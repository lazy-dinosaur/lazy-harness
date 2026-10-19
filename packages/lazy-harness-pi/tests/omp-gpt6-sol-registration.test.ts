import { expect, test } from "bun:test";
import { spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, realpathSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import registerExtension, { gpt6SolRegistration, registerGpt6Sol } from "./fixtures/omp-gpt6-sol-registration";

function nativeHandlers() {
  let calls = 0;
  return {
    oauth: { name: "OpenAI Codex", login: () => { calls++; }, refreshToken: () => { calls++; } },
    calls: () => calls,
  };
}

test("GPT-6 Sol medium registration retains native handlers without invoking them", () => {
  const native = nativeHandlers();
  const registrations: { provider: string; definition: ReturnType<typeof gpt6SolRegistration> }[] = [];
  registerGpt6Sol({ registerProvider: (provider, definition) => registrations.push({ provider, definition }) }, native.oauth);
  expect(registrations).toHaveLength(1);
  const { provider, definition } = registrations[0];
  expect(provider).toBe("openai-codex");
  expect(definition.api).toBe("openai-codex-responses");
  expect(definition.baseUrl).toBe("https://chatgpt.com/backend-api");
  expect(definition.models).toEqual([{
    id: "gpt-6-sol", name: "GPT-6 Sol", reasoning: true,
    thinking: { mode: "effort", efforts: ["medium"], defaultLevel: "medium" },
    input: ["text", "image"], contextWindow: 272000, maxTokens: 128000,
    cost: { input: 2, output: 10, cacheRead: 0.2, cacheWrite: 2.5 },
  }]);
  expect(definition.oauth.login).toBe(native.oauth.login);
  expect(definition.oauth.refreshToken).toBe(native.oauth.refreshToken);
  expect(definition).not.toHaveProperty("apiKey");
  expect(definition).not.toHaveProperty("auth");
  expect(native.calls()).toBe(0);
});

test("missing native OAuth handlers fail before provider registration", () => {
  for (const invalid of [null, {}, { name: "x", login() {} }, { name: " ", login() {}, refreshToken() {} }]) {
    let registrations = 0;
    expect(() => registerGpt6Sol({ registerProvider: () => { registrations++; } }, invalid)).toThrow("Native Codex OAuth handlers unavailable");
    expect(registrations).toBe(0);
  }
});

test("each registration has independent model configuration", () => {
  const native = nativeHandlers();
  const first = gpt6SolRegistration(native.oauth);
  first.models[0].id = "changed";
  first.models[0].thinking.efforts.push("high");
  const next = gpt6SolRegistration(native.oauth);
  expect(next.models[0].id).toBe("gpt-6-sol");
  expect(next.models[0].thinking.efforts).toEqual(["medium"]);
});

test("extension requires an explicit absolute native package root", async () => {
  let registrations = 0;
  for (const path of ["", "relative/path"]) {
    await expect(registerExtension({ registerProvider: () => { registrations++; } }, path)).rejects.toThrow("absolute installed OMP package path");
  }
  expect(registrations).toBe(0);
});

const native = process.env.LAZY_OMP_NATIVE_TEST === "1" ? test : test.skip;
native("installed OMP registers the repository fixture offline without authentication or inference", () => {
  const binary = Bun.which(process.env.LAZY_OMP_BINARY || "omp");
  if (!binary) throw new Error("Installed OMP binary required; missing runner is not a passing test");
  const packageRoot = dirname(dirname(realpathSync(binary)));
  const sandbox = mkdtempSync(join(tmpdir(), "lh-omp-gpt6-regression-"));
  const home = join(sandbox, "home");
  const agent = join(sandbox, "agent");
  mkdirSync(home);
  mkdirSync(agent);
  const fixture = resolve(import.meta.dir, "fixtures/omp-gpt6-sol-registration.ts");
  const code = `
    import { writeFileSync } from "node:fs";
    let networkCalls = 0;
    globalThis.fetch = () => { networkCalls++; throw new Error("Network disabled in offline regression"); };
    globalThis.WebSocket = class { constructor() { networkCalls++; throw new Error("Network disabled in offline regression"); } };
    const { discoverAuthStorage } = await import(${JSON.stringify(join(packageRoot, "src/sdk.ts"))});
    const { ModelRegistry } = await import(${JSON.stringify(join(packageRoot, "src/config/model-registry.ts"))});
    const { default: register, gpt6SolRegistration } = await import(${JSON.stringify(fixture)});
    const auth = await discoverAuthStorage();
    try {
      const registry = new ModelRegistry(auth);
      await register({ registerProvider: registry.registerProvider.bind(registry) });
      const model = registry.getAll().find(m => m.provider === "openai-codex" && m.id === "gpt-6-sol");
      const authenticated = registry.getAvailable().some(m => m.provider === "openai-codex" && m.id === "gpt-6-sol");
      const config = gpt6SolRegistration({ name: "native", login() {}, refreshToken() {} });
      const { oauth, ...plain } = config;
      // A unique ID prevents a newly bundled GPT-6 model from masking ignored config.
      const probeId = "gpt-6-sol-config-probe";
      writeFileSync("plain-models.json", JSON.stringify({providers: {"openai-codex": {...plain, models: plain.models.map(m => ({...m, id: probeId})), auth:"oauth"}}}));
      const configured = new ModelRegistry(auth, ${JSON.stringify(join(sandbox, "plain-models.json"))});
      const plainConfigModel = configured.getAll().find(m => m.provider === "openai-codex" && m.id === probeId);
      const plainConfigAvailable = configured.getAvailable().some(m => m.provider === "openai-codex" && m.id === probeId);
      console.log(JSON.stringify({ model, authenticated, networkCalls, plainConfigError: configured.getError()?.message, plainConfigModel, plainConfigAvailable }));
    } finally { auth.close(); }
  `;
  const result = spawnSync(process.execPath, ["-e", code], {
    cwd: sandbox,
    env: { PATH: process.env.PATH ?? "", HOME: home, PI_CODING_AGENT_DIR: agent, OMP_PROFILE: "", LAZY_OMP_MODULE_ROOT: packageRoot },
    encoding: "utf8", timeout: 30000, maxBuffer: 1024 * 1024,
  });
  expect(result.error, `native evidence: ${sandbox}`).toBeUndefined();
  expect(result.status, result.stderr).toBe(0);
  const report = JSON.parse(result.stdout.trim());
  expect(report.model.id).toBe("gpt-6-sol");
  expect(report.model.provider).toBe("openai-codex");
  expect(report.model.api).toBe("openai-codex-responses");
  expect(report.model.baseUrl).toBe("https://chatgpt.com/backend-api");
  expect(report.model.thinking).toEqual({mode: "effort", efforts: ["medium"], defaultLevel: "medium"});
  expect(report.model.contextWindow).toBe(272000);
  expect(report.model.maxTokens).toBe(128000);
  expect(report.authenticated).toBe(false);
  expect(report.networkCalls).toBe(0);
  expect(report.plainConfigAvailable).toBe(false);
  if (report.plainConfigError !== undefined) {
    // Older OMP rejects direct OAuth config; unexpected errors still fail.
    expect(report.plainConfigError).toContain('"apiKey" is required');
    expect(report.plainConfigModel).toBeUndefined();
  } else {
    // Newer OMP accepts it, but must actually load the config and require auth.
    expect(report.plainConfigModel).toMatchObject({
      id: "gpt-6-sol-config-probe", provider: "openai-codex",
      api: "openai-codex-responses", contextWindow: 272000, maxTokens: 128000,
      thinking: { mode: "effort", efforts: ["medium"], defaultLevel: "medium" },
    });
  }
}, 45000);
