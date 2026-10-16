import { expect, test } from "bun:test";
import { execFileSync } from "node:child_process";
import { mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import lazyHarnessPi from "../extensions/lazy-harness/index.ts";
import { FABRIC_READER_DEFAULT_MODEL, fabricReaderDefinition, applyFabricReaderPrompt, advanceFabricReaderTurn, parseFabricReaderDefinition, validateFabricReaderPolicy } from "../extensions/lazy-harness/fabric-reader-policy.ts";
import { fabricReaderLedgerPath, fabricReaderPrompt, fabricReaderRequest } from "../extensions/lazy-harness/fabric-reader.ts";

const host = resolve(import.meta.dir, "../../..");
const revision = execFileSync("git", ["rev-parse", "HEAD"], { cwd: host, encoding: "utf8" }).trim();
const proxy = (toolName: string, input: any, result: any, content = JSON.stringify(result)) => ({
  toolName, toolCallId: `fabric-${toolName}`, parentToolCallId: `outer-${toolName}`, input, isError: false,
  content: [{ type: "text", text: content }],
  details: { kind: "pi-fabric.tool-result-proxy.v1", ref: toolName, result },
});
const adapter = (thinking = "low") => {
  const handlers = new Map<string, Function>();
  const tools = new Map<string, any>();
  lazyHarnessPi({
    on: (name: string, handler: Function) => handlers.set(name, handler),
    registerCommand() {}, registerTool: (tool: any) => tools.set(tool.name, tool),
    appendEntry() {}, getThinkingLevel: () => thinking,
    exec: async () => ({ stdout: "", stderr: "", exitCode: 0 }),
  } as any);
  return { handlers, tools };
};

async function fixture() {
  const temp = mkdtempSync(join(tmpdir(), "fabric-reader-"));
  const root = join(temp, "host");
  execFileSync("git", ["clone", "--quiet", "--shared", "--no-checkout", host, root]);
  mkdirSync(join(root, ".lazy-harness/bin"), { recursive: true });
  mkdirSync(join(root, ".lazy-harness/spec"), { recursive: true });
  writeFileSync(join(root, ".lazy-harness/bin/lazy"), "#!/bin/sh\n");
  writeFileSync(join(root, ".lazy-harness/spec/fact.md"), "fact\n");
  const { handlers, tools } = adapter();
  const ctx = { cwd: root, mode: "json", hasUI: false, sessionManager: { getCwd: () => root, getSessionId: () => "parent" }, ui: { notify() {} } };
  await handlers.get("before_agent_start")!({ prompt: "fixture", systemPrompt: "base" }, ctx);
  const task = `root: ${root}\nrevision: ${revision}\nmodel: fixture/reader:low\nevidenceEpoch: 1\nmaxReadCalls: 2\nmaxRequestedLines: 400\nmaxLinesPerRead: 200\ntask: objective`;
  const prepared = await tools.get("lazy_reader_request").execute("request", { task }, undefined, undefined, ctx);
  const request = prepared.details.request;
  const id = `reader-${temp.split("/").at(-1)}`;
  const handle = { id, name: "lazy-harness.record-reader", runner: "pi", cwd: root, model: "fixture/reader", thinking: "low", status: "running" };
  const resultPacket = (epoch = 1, status = "complete") => `LAZY_HARNESS_READER_RESULT: ${status}\nroot: ${root}\nrevision: ${revision}\nevidenceEpoch: ${epoch}\nfacts: canonical fact\n`;
  const spawn = (patch: any = {}, resultPatch: any = {}) => handlers.get("tool_result")!(proxy("agents.spawn", { ...request, ...patch }, { ...handle, ...resultPatch }), ctx);
  const wait = async (patch: any = {}, content?: string, deliver = true) => {
    const result = { ...handle, status: "completed", text: resultPacket(), ...patch };
    const response = await handlers.get("tool_result")!(proxy("agents.wait", { id }, result, content ?? JSON.stringify(result)), ctx);
    if (!response?.isError && deliver) {
      const outer = await handlers.get("tool_result")!({ toolName: "fabric_exec", toolCallId: "outer-agents.wait", input: {}, content: [{ type: "text", text: "guest returned only a summary" }] }, ctx);
      // The adapter, not model-authored return code, guarantees packet visibility.
      if (outer?.content) expect(outer.content.at(-1).text).toBe(result.text);
    }
    return response;
  };
  const params = { status: "complete", resultMarker: "LAZY_HARNESS_READER_RESULT: complete", revision, evidenceEpoch: 1 };
  const joinReader = (patch: any = {}) => tools.get("lazy_reader_join").execute("join", { ...params, ...patch }, undefined, undefined, ctx);
  const child = async (options: { thinking?: string; failed?: boolean; overCap?: boolean; turns?: number } = {}) => {
    const previous = process.env.PI_FABRIC_LINEAGE;
    process.env.PI_FABRIC_LINEAGE = JSON.stringify({ version: 1, worker: true, runId: id });
    try {
      const childAdapter = adapter(options.thinking ?? "low");
      let aborts = 0;
      const childCtx = { ...ctx, abort: () => { aborts += 1; }, model: { provider: "fixture", id: "reader" }, sessionManager: { getCwd: () => root, getSessionId: () => "child" } };
      const start = await childAdapter.handlers.get("before_agent_start")!({ prompt: task, systemPrompt: fabricReaderPrompt() }, childCtx);
      expect(start.systemPrompt).toContain("Fabric transport encoding only");
      const outer = { toolName: "fabric_exec", toolCallId: "outer", input: { code: "return await pi.read(...)" } };
      const outerAdmission = await childAdapter.handlers.get("tool_call")!(outer, childCtx);
      if (options.thinking && options.thinking !== "low") { expect(outerAdmission.block).toBe(true); return; }
      expect(outerAdmission).toBeUndefined();
      const read = { toolName: "read", toolCallId: "body-read", input: { path: ".lazy-harness/spec/fact.md", offset: 1, limit: options.overCap ? 201 : 200 } };
      const admission = await childAdapter.handlers.get("tool_call")!(read, childCtx);
      if (options.thinking && options.thinking !== "low") { expect(admission.block).toBe(true); return; }
      if (options.overCap) expect(admission.block).toBe(true);
      else {
        expect(admission).toBeUndefined();
        await childAdapter.handlers.get("tool_result")!({ ...read, isError: Boolean(options.failed) }, childCtx);
      }
      for (let turn = 1; turn <= (options.turns ?? 1); turn++) {
        const content = options.turns === 14 && turn === 14 ? [{ type: "toolCall", name: "read" }] : [{ type: "text", text: resultPacket() }];
        await childAdapter.handlers.get("message_end")!({ message: { role: "assistant", content } }, childCtx);
        if (turn === 12) {
          const wrapped = await childAdapter.handlers.get("context")!({ messages: [] }, childCtx);
          expect(wrapped.messages.at(-1).content).toContain("Reader turn budget reached");
        }
      }
      if (options.turns === 14) expect(aborts).toBe(1);
      await childAdapter.handlers.get("agent_end")!({ messages: [] }, childCtx);
    } finally {
      if (previous === undefined) delete process.env.PI_FABRIC_LINEAGE; else process.env.PI_FABRIC_LINEAGE = previous;
    }
  };

  const close = () => { rmSync(temp, { recursive: true, force: true }); rmSync(fabricReaderLedgerPath(root, id), { force: true }); };
  return { root, task, ctx, handlers, tools, request, id, spawn, wait, child, joinReader, close, resultPacket };
}

test("runtime hook hard-aborts an exhausted Reader and complete prose cannot bypass its policy ledger", async () => {
  const f = await fixture();
  try {
    await f.spawn(); await f.child({ turns: 14 }); await f.wait();
    await expect(f.joinReader()).rejects.toThrow("readerPolicy");
  } finally { f.close(); }
});

test("Reader may finish honestly within its two soft-budget grace responses", async () => {
  const f = await fixture();
  try {
    await f.spawn(); await f.child({ turns: 13 }); await f.wait();
    expect((await f.joinReader()).details.joined).toBe(true);
  } finally { f.close(); }
});

test("missing child policy/guard stamp cannot pass the dedicated Reader join", async () => {
  const f = await fixture();
  try {
    await f.spawn(); await f.child();
    const path = fabricReaderLedgerPath(f.root, f.id);
    const rows = readFileSync(path, "utf8").trim().split("\n").map(line => JSON.parse(line));
    delete rows[1].data.readerPolicy;
    writeFileSync(path, rows.map(row => JSON.stringify(row)).join("\n") + "\n");
    await f.wait();
    await expect(f.joinReader()).rejects.toThrow("readerPolicy");
  } finally { f.close(); }
});

test("Pi manifest needs no pi-subagents registration; request pins fresh read-only Fabric runner", () => {
  const manifest = JSON.parse(readFileSync(new URL("../package.json", import.meta.url), "utf8"));
  expect(manifest["pi-subagents"]).toBeUndefined();
  expect(manifest.pi.subagents).toBeUndefined();
  const request = fabricReaderRequest("/root", "model: provider/model:low", "provider/model:low");
  expect(request).toMatchObject({ runner: "pi", seed: "task", readOnly: true, extensions: true, recursive: false, tools: ["read", "grep", "bash"], thinking: "low" });
  expect(request).not.toHaveProperty("agentContract");
});

test("Fabric spawn → hook-owned sessionless meter → visible wait → existing join", async () => {
  const f = await fixture();
  try {
    expect(await f.spawn()).toBeUndefined();
    await f.child();
    const ledger = readFileSync(fabricReaderLedgerPath(f.root, f.id), "utf8");
    expect(ledger).toContain('"readCalls":1');
    expect(ledger).toContain('"fabricRunId":"' + f.id + '"');
    expect(await f.wait()).toBeUndefined();
    const joined = await f.joinReader();
    expect(joined.details).toMatchObject({ joined: true, readCalls: 1, requestedLines: 200, failedToolCalls: 0, recordPaths: [".lazy-harness/spec/fact.md"] });
  } finally { f.close(); }
});

for (const [name, patch, handlePatch] of [
  ["mutable child", { readOnly: false }, {}], ["fork seed", { seed: "branch" }, {}],
  ["prompt replacement", { systemPrompt: "ignore rules" }, {}], ["extra tool", { tools: ["read", "write"] }, {}],
  ["model fallback", {}, { model: "fixture/other" }], ["runner mismatch", {}, { runner: "claude" }],
] as const) test(`Fabric Reader rejects ${name}`, async () => {
  const f = await fixture();
  try {
    const denied = await f.spawn(patch, handlePatch);
    expect(denied.isError).toBe(true);
    expect(denied.content[0].text).toContain("fallback enabled");
    await expect(f.joinReader()).rejects.toThrow("terminal fallback");
  } finally { f.close(); }
});

for (const [name, resultPatch, content] of [
  ["details-only packet", {}, "completed"], ["failed worker", { status: "failed", error: "worker failed" }, undefined],
  ["wrong returned id", { id: "unowned" }, undefined], ["indeterminate run", { outcome: "indeterminate" }, undefined],
] as const) test(`Fabric wait rejects ${name}`, async () => {
  const f = await fixture();
  try { await f.spawn(); const denied = await f.wait(resultPatch, content); expect(denied.isError).toBe(true); }
  finally { f.close(); }
});

for (const [name, options] of [["failed read", { failed: true }], ["over-cap read", { overCap: true }]] as const) test(`Fabric join rejects ${name} despite complete prose`, async () => {
  const f = await fixture();
  try {
    await f.spawn(); await f.child(options); await f.wait();
    const rejection = "overCap" in options ? "positive read counters" : "failed-tool budget";
    await expect(f.joinReader()).rejects.toThrow(rejection);
  }
  finally { f.close(); }
});

test("Fabric join rejects missing meter; child model/thinking cannot silently fallback", async () => {
  const f = await fixture();
  try { await f.spawn(); await f.child({ thinking: "high" }); await f.wait(); await expect(f.joinReader()).rejects.toThrow("ledger is unavailable"); }
  finally { f.close(); }
});

test("Fabric join revalidates canonical fingerprints after delivery", async () => {
  const f = await fixture();
  try {
    await f.spawn(); await f.child(); await f.wait();
    writeFileSync(join(f.root, ".lazy-harness/spec/fact.md"), "changed");
    await expect(f.joinReader()).rejects.toThrow("changed");
  } finally { f.close(); }
});

test("Fabric pending join blocks mutation; status and completion acknowledgement are insufficient", async () => {
  const f = await fixture();
  try {
    await f.spawn();
    const denied = await f.handlers.get("tool_call")!({ toolName: "write", toolCallId: "write", input: { path: "product.ts", content: "bad" } }, f.ctx);
    expect(denied.reason).toContain("join pending");
    await f.handlers.get("tool_result")!(proxy("agents.status", { id: f.id }, { id: f.id, status: "completed" }), f.ctx);
    await expect(f.joinReader()).rejects.toThrow("content-bearing");
  } finally { f.close(); }
});

test("Fabric launch infrastructure failure explicitly enables direct fallback without a run id", async () => {
  const f = await fixture();
  try { expect((await f.joinReader({ status: "failed" })).details).toMatchObject({ joined: false, fallbackAllowed: true }); }
  finally { f.close(); }
});

test("Fabric stale post-steer result cannot repopulate the active work unit", async () => {
  const f = await fixture();
  try {
    await f.spawn(); await f.child();
    await f.handlers.get("input")!({ text: "new constraint", streamingBehavior: "steer", source: "interactive" }, f.ctx);
    await f.wait();
    await expect(f.joinReader()).rejects.toThrow("no dedicated Reader launch");
  } finally { f.close(); }
});


test("nested wait alone cannot join before its actual Parent-visible outer result", async () => {
  const f = await fixture();
  try {
    await f.spawn(); await f.child(); await f.wait({}, undefined, false);
    await expect(f.joinReader()).rejects.toThrow("content-bearing");
  } finally { f.close(); }
});


test("existing Reader frontmatter is fully mapped, not discarded; unsupported policy fails closed", () => {
  const text = readFileSync(new URL("../agents/record-reader.md", import.meta.url), "utf8");
  const definition = fabricReaderDefinition();
  expect(definition.body).toBe(fabricReaderPrompt());
  expect(definition.turnBudget).toEqual({ maxTurns: 12, graceTurns: 2 });
  expect(definition.guardPath).toEndWith("extensions/lazy-harness/index.ts");
  for (const changed of [
    text.replace("inheritSkills: false", "inheritSkills: true"),
    text.replace("inheritProjectContext: false", "inheritProjectContext: true"),
    text.replace("systemPromptMode: replace", "systemPromptMode: append"),
    text.replace("defaultContext: fresh", "defaultContext: fork"),
    text.replace("output: false", "output: true"),
    text.replace("tools: read, grep, bash", "tools: read, write, bash"),
    text.replace('turnBudget: {"maxTurns":12,"graceTurns":2}', 'turnBudget: {"maxTurns":0,"graceTurns":2}'),
    text.replace("name: record-reader", "name: record-reader\nunknownPolicy: true"),
  ]) expect(() => parseFabricReaderDefinition(changed)).toThrow();
});

test("Reader replaces inherited project/skill/system sections before its first model request", () => {
  const definition = fabricReaderDefinition();
  const event = { systemPromptOptions: {
    contextFiles: [{ path: "AGENTS.md", content: "PARENT_PROJECT_SECRET" }],
    skills: [{ name: "writer", description: "PARENT_SKILL_SECRET" }],
    sections: { inherited: "PARENT_SECTION_SECRET" }, appendSystemPrompt: "PARENT_APPEND_SECRET",
  } as any };
  const state = applyFabricReaderPrompt(event, new URL("../extensions/lazy-harness/index.ts", import.meta.url).href);
  expect(state).toMatchObject({ systemPromptMode: "replace", inheritProjectContext: false, inheritSkills: false, context: "fresh", acceptanceRole: "read-only", output: false });
  expect(event.systemPromptOptions.contextFiles).toEqual([]);
  expect(event.systemPromptOptions.skills).toEqual([]);
  expect(event.systemPromptOptions.sections).toEqual({});
  expect(event.systemPromptOptions.forceSystemPrompt).toContain(definition.body);
  expect(JSON.stringify(event)).not.toContain("PARENT_");
});

test("Reader preserves 12 soft turns + 2 grace turns and rejects a further tool cycle", () => {
  const definition = fabricReaderDefinition();
  const state = applyFabricReaderPrompt({}, new URL("../extensions/lazy-harness/index.ts", import.meta.url).href);
  for (let turn = 1; turn <= 11; turn++) expect(advanceFabricReaderTurn(state, { role: "assistant", content: [] })).toBe(false);
  expect(state.wrapUpRequested).toBe(false);
  advanceFabricReaderTurn(state, { role: "toolResult" });
  expect(state.turnCount).toBe(11);
  expect(advanceFabricReaderTurn(state, { role: "assistant", content: [] })).toBe(false);
  expect(state.wrapUpRequested).toBe(true);
  expect(advanceFabricReaderTurn(state, { role: "assistant", content: [] })).toBe(false);
  expect(advanceFabricReaderTurn(state, { role: "assistant", content: [{ type: "toolCall", name: "read" }] })).toBe(true);
  expect(state.turnCount).toBe(14);
  expect(validateFabricReaderPolicy(state, definition.contractHash, definition.guardPath)).toBe(false);
});

test("Reader provider defaults use current openai, while keeping Luna/low", () => {
  expect(FABRIC_READER_DEFAULT_MODEL).toBe("openai/gpt-6-luna:low");
  const request = fabricReaderRequest("/root", `model: ${FABRIC_READER_DEFAULT_MODEL}`, FABRIC_READER_DEFAULT_MODEL);
  expect(request).toMatchObject({ model: "openai/gpt-6-luna", thinking: "low", seed: "task", recursive: false });
  for (const path of [join(host, ".lazy-harness/AGENTS.md"), join(host, "packages/lazy-harness-pi/prompts/lazy-harness.md"), join(host, "packages/lazy-harness-pi/README.md")]) {
    const guidance = readFileSync(path, "utf8");
    expect(guidance).toContain(`model: ${FABRIC_READER_DEFAULT_MODEL}`);
    expect(guidance).not.toContain("model: openai-codex/gpt-6-luna:low");
  }
});

test("Parent source work remains admitted while the asynchronous Reader is pending", async () => {
  const f = await fixture();
  try {
    await f.spawn();
    expect(await f.handlers.get("tool_call")!({ toolName: "read", toolCallId: "parent-source", input: { path: "src/product.ts", offset: 1, limit: 20 } }, f.ctx)).toBeUndefined();
    const mutation = await f.handlers.get("tool_call")!({ toolName: "write", toolCallId: "parent-mutation", input: { path: "src/product.ts", content: "blocked" } }, f.ctx);
    expect(mutation.reason).toContain("join pending");
    await f.child(); await f.wait();
    expect((await f.joinReader()).details.joined).toBe(true);
  } finally { f.close(); }
});


test("synthetic continuation preserves pending Reader epoch and join barrier until actual content joins", async () => {
  const f = await fixture();
  try {
    await f.spawn();
    const continuation = await f.handlers.get("before_agent_start")!({ prompt: "", systemPrompt: "base" }, f.ctx);
    expect(continuation.message.content).toContain("evidence-epoch=1");
    const mutation = await f.handlers.get("tool_call")!({ toolName: "write", toolCallId: "resume-before-join", input: { path: "src/product.ts", content: "blocked" } }, f.ctx);
    expect(mutation.reason).toContain("join pending");
    await f.child(); await f.wait();
    expect((await f.joinReader()).details.joined).toBe(true);
    const reused = await f.handlers.get("before_agent_start")!({ prompt: "", systemPrompt: "base" }, f.ctx);
    expect(reused.message.content).toContain("reused-work-unit");
    expect(reused.message.content).toContain("evidence-epoch=1");
  } finally { f.close(); }
});

test("real non-extension steer still invalidates a pending Reader instead of rebinding its epoch", async () => {
  const f = await fixture();
  try {
    await f.spawn();
    await f.handlers.get("input")!({ text: "new work unit", streamingBehavior: "steer", source: "interactive" }, f.ctx);
    await expect(f.joinReader()).rejects.toThrow();
  } finally { f.close(); }
});
