import { after as afterAll, before as beforeAll, beforeEach, test } from "node:test";
import assert from "node:assert/strict";
import { fileURLToPath } from "node:url";
import { cpSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { spawnSync } from "node:child_process";
import { createEventBus, createExtensionRuntime, createReadTool, createWriteTool, ExtensionRunner, ModelRegistry, ModelRuntime, SessionManager, type ExtensionActions, type ExtensionFactory, type Extension, type ExtensionRuntime } from "@earendil-works/pi-coding-agent";
import { loadExtensionFromFactory } from "../../node_modules/@earendil-works/pi-coding-agent/dist/core/extensions/loader.js";
import type { AssistantMessage } from "@earendil-works/pi-ai";
import { CaptureEvidence } from "../../packages/lazy-harness-pi/extensions/lazy-harness/capture-evidence.ts";

const source = fileURLToPath(new URL("../../", import.meta.url));
const baseline = process.env.LAZY_CAPTURE_BASELINE === "1";
const root = mkdtempSync(join(process.env.TMPDIR ?? tmpdir(), "pi-capture-"));
const record = ".lazy-harness/planning/capture.md";
const other = ".lazy-harness/planning/other.md";
const baseText = "Owner north; local read-only; divergence reason retained.\n";
let runner: ExtensionRunner;
let extension: Extension;
let runtime: ExtensionRuntime;
let registry: ModelRegistry;
const previousRuntime = process.env.LAZY_RUNTIME_ROOT;
const previousShared = process.env.LAZY_SHARED_ROOT;
let sequence = 0;
const deliveries: Array<{ content: unknown; details: unknown; triggerTurn: boolean | undefined }> = [];
const followups: unknown[] = [];
const entries: Array<{ customType: string; data: unknown }> = [];
const errors: unknown[] = [];

function envelope(disposition: string, path = record, main = "Primary answer: retain facts and reasons."): string {
  return `${main}\n<record-judgement>\n${JSON.stringify({ disposition, reason: "current LLM judgement, not execution approval", facts: disposition === "no-record" || disposition === "pending" ? [] : [{ path, fact: baseText }] })}\n</record-judgement>`;
}
function message(text: string): AssistantMessage {
  return { role: "assistant", content: [{ type: "text", text }], api: "anthropic-messages", provider: "anthropic", model: "fixture-no-provider", usage: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, totalTokens: 0, cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, total: 0 } }, stopReason: "stop", timestamp: 1 };
}
function assessment(): Record<string, unknown> {
  const details = deliveries.at(-1)?.details;
  assert.ok(details !== null && typeof details === "object" && !Array.isArray(details));
  return details as Record<string, unknown>;
}
async function end(raw: string, user = "unchanged status") {
  const main = message(raw);
  const before = JSON.stringify(main);
  await runner.emit({ type: "agent_end", messages: [{ role: "user", content: user, timestamp: 0 }, main] });
  assert.equal(JSON.stringify(main), before); // caller-visible answer, not advisory text
  if (baseline) console.log(JSON.stringify({ rawAnswer: raw, followups, deliveries }));
  assert.deepEqual(errors, []);
  return assessment();
}
async function start(name: string, input: Record<string, unknown>, id = `call-${++sequence}`) {
  const block = await runner.emitToolCall({ type: "tool_call", toolName: name, toolCallId: id, input });
  assert.notEqual(block?.block, true, block?.reason);
  return id;
}
async function result(name: string, input: Record<string, unknown>, id: string, isError = false) {
  await runner.emitToolResult({ type: "tool_result", toolName: name, toolCallId: id, input, isError, content: [{ type: "text", text: isError ? "failed precondition" : "tool completed" }], details: {} });
}
async function read(path: string) {
  const input = { path };
  const id = await start("read", input);
  const output = await createReadTool(root).execute(id, input);
  await runner.emitToolResult({ type: "tool_result", toolName: "read", toolCallId: id, input, isError: false, ...output });
}
async function mutate(name: string, path = record, failed = false) {
  const input = { path, content: baseText };
  const id = await start(name, input);
  if (name === "write" && !failed) {
    const output = await createWriteTool(root).execute(id, input);
    await runner.emitToolResult({ type: "tool_result", toolName: name, toolCallId: id, input, isError: false, ...output });
  } else {
    // Third-party insert/replace transports are callback fixtures, not installed tools.
    if (!failed) writeFileSync(join(root, path), baseText);
    await result(name, input, id, failed);
  }
  return id;
}
async function ground() {
  const input = { command: ".lazy-harness/bin/lazy map --overview --complete --format=md" };
  const id = await start("bash", input);
  await result("bash", input, id);
  await read(".lazy-harness/spec/governing.md");
}

beforeAll(async () => {
  process.env.LAZY_RUNTIME_ROOT = join(root, "runtime");
  process.env.LAZY_SHARED_ROOT = join(root, "shared");
  mkdirSync(join(root, ".lazy-harness/bin"), { recursive: true });
  mkdirSync(join(root, ".lazy-harness/planning"), { recursive: true });
  mkdirSync(join(root, ".lazy-harness/spec"), { recursive: true });
  mkdirSync(join(root, ".lazy-harness/scripts"), { recursive: true });
  writeFileSync(join(root, ".lazy-harness/bin/lazy"), "#!/bin/sh\nexit 0\n", { mode: 0o755 });
  writeFileSync(join(root, ".lazy-harness/spec/governing.md"), "# Stable governing record\n");
  cpSync(join(source, ".lazy-harness/hooks"), join(root, ".lazy-harness/hooks"), { recursive: true });
  cpSync(join(source, ".lazy-harness/scripts/lifecycle-check.py"), join(root, ".lazy-harness/scripts/lifecycle-check.py"));
  if (baseline) cpSync(resolve(source, "../evidence/baseline/.lazy-harness"), join(root, ".lazy-harness"), { recursive: true });
  const imported: { default: ExtensionFactory } = await import(baseline ? join(source, ".git/b-source-baseline/index.ts") : join(source, "packages/lazy-harness-pi/extensions/lazy-harness/index.ts"));
  runtime = createExtensionRuntime();
  extension = await loadExtensionFromFactory(imported.default, root, createEventBus(), runtime);
  const models = await ModelRuntime.create({ authPath: join(root, "auth.json"), modelsPath: null, modelsStorePath: join(root, "models.json"), refreshOnCreate: false, allowModelNetwork: false });
  registry = new ModelRegistry(models);
  runner = new ExtensionRunner([extension], runtime, root, SessionManager.inMemory(root), registry);
  const actions: ExtensionActions = {
    sendMessage: (m, options) => { deliveries.push({ content: m.content, details: m.details, triggerTurn: options?.triggerTurn }); },
    sendUserMessage: (content) => { followups.push(content); },
    appendEntry(customType, data) { entries.push({ customType, data }); }, setSessionName() {}, getSessionName: () => undefined, setLabel() {},
    getActiveTools: () => ["read", "write", "bash"], getAllTools: () => [], setActiveTools() {}, refreshTools: async () => {}, getCommands: () => [], setModel: async () => false, getThinkingLevel: () => "off", setThinkingLevel() {},
  };
  runner.bindCore(actions, { getModel: () => undefined, getScopedModels: () => [], isIdle: () => true, isProjectTrusted: () => true, getSignal: () => undefined, abort() {}, hasPendingMessages: () => false, shutdown() {}, getContextUsage: () => undefined, compact() {}, getSystemPrompt: () => "fixture" });
  runner.onError((error) => errors.push(error));
});
beforeEach(async () => {
  deliveries.length = 0; followups.length = 0; entries.length = 0; errors.length = 0;
  // These existing callback/safety assertions exercise interactive transport.
  runner.setUIContext(undefined, "tui");
  writeFileSync(join(root, record), "before\n");
  writeFileSync(join(root, other), "unrelated\n");
  await runner.emit({ type: "session_start", reason: "new" });
  await runner.emitBeforeAgentStart("approved bounded capture fixture", undefined, "base", { cwd: root });
  await ground();
});
afterAll(async () => {
  if (runner) await runner.emit({ type: "session_shutdown", reason: "quit" });
  rmSync(root, { recursive: true, force: true });
  if (previousRuntime === undefined) delete process.env.LAZY_RUNTIME_ROOT; else process.env.LAZY_RUNTIME_ROOT = previousRuntime;
  if (previousShared === undefined) delete process.env.LAZY_SHARED_ROOT; else process.env.LAZY_SHARED_ROOT = previousShared;
});

test("status pollution and quoted correction words are not semantic STOP", { timeout: 60000 }, async () => {
  const raw = envelope("no-record", record, "Unchanged DDD SDD BDD analysis plan. Quoted acknowledgement: 맞습니다. 제가 잘못.");
  assert.equal((await end(raw, "quoted old message: 아니 잘못 하네스 수정")).status, "no-record-asserted");
  assert.deepEqual(followups, []);
  assert.equal(deliveries.at(-1)?.triggerTurn, false);
});
test("real Pi write/read tools -> actual result dispatch -> full response hook -> linked evidence", { timeout: 60000 }, async () => {
  await mutate("write");
  await read(record);
  const a = await end(envelope("required"));
  assert.equal(a.status, "evidence-linked");
  assert.equal(a.semanticStatus, "llm-judgement-not-verified");
  assert.equal(a.approvalStatus, "not-evaluated");
  assert.equal(readFileSync(join(root, record), "utf8"), baseText);
});
for (const name of ["insert", "replace", "functions.insert", "functions.replace", "Edit", "functions.write", "mcp__filesystem__edit_file"]) {
  test(`${name}: successful callback with readback vs failed result`, { timeout: 60000 }, async () => {
    await mutate(name);
    assert.equal((await end(envelope("required"))).status, "evidence-linked");
    await mutate(name, record, true);
    assert.equal((await end(envelope("required"))).status, "unverified");
  });
}
test("missing, args-only and unrelated receipts are explicit unverified", { timeout: 60000 }, async () => {
  assert.equal((await end(envelope("required"))).status, "unverified");
  await start("write", { path: record, content: baseText });
  assert.equal((await end(envelope("required"))).status, "unverified");
  await mutate("write", other);
  assert.equal((await end(envelope("required"))).status, "unverified");
});
test("missing/empty IDs and result without a started callback never link", { timeout: 60000 }, async () => {
  for (const id of ["", " ", "not-started"]) {
    await result("write", { path: record }, id);
    assert.equal((await end(envelope("required"))).status, "unverified");
  }
});
test("steer invalidates successful and late old callbacks; fresh callback reestablishes proof", { timeout: 60000 }, async () => {
  await mutate("write");
  const input = { path: record };
  const id = await start("read", input);
  await runner.emitInput("new approved scope", undefined, "interactive", "steer");
  await result("read", input, id);
  assert.equal((await end(envelope("reuse"))).status, "unverified");
  await ground();
  await read(record);
  assert.equal((await end(envelope("reuse"))).status, "evidence-linked");
});
test("long irrelevant tool history does not evict relevant capture", { timeout: 60000 }, async () => {
  await mutate("write");
  for (let i = 0; i < 45; i++) {
    const input = { pattern: "irrelevant" };
    const id = await start("grep", input);
    await result("grep", input, id);
  }
  assert.equal((await end(envelope("required"))).status, "evidence-linked");
});
test("old same fact requires current read/rejudge, not duplicate write; changed bytes invalidate", { timeout: 60000 }, async () => {
  await mutate("write");
  await runner.emitBeforeAgentStart("same work unit status", undefined, "base", { cwd: root });
  assert.equal((await end(envelope("reuse"))).status, "unverified");
  await read(record);
  assert.equal((await end(envelope("reuse"))).status, "evidence-linked");
  writeFileSync(join(root, record), "owner south; changed\n");
  assert.equal((await end(envelope("reuse"))).status, "unverified");
});
test("unsupported and wrong-root paths cannot use a relevant receipt", { timeout: 60000 }, async () => {
  await mutate("write");
  for (const path of ["memory.md", "/other/.lazy-harness/planning/capture.md", "../elsewhere/.lazy-harness/planning/capture.md"]) {
    assert.equal((await end(envelope("required", path))).status, "unverified");
  }
});
test("malformed, unknown, duplicate and nonterminal packets preserve all raw answer bytes", { timeout: 60000 }, async () => {
  const valid = envelope("no-record");
  for (const raw of ["raw primary\n<record-judgement>\nbroken trailing primary", valid + "\nacceptance-report trailing text", valid + valid, envelope("unknown"), "primary\n<record-judgement>\n[]\n</record-judgement>", "no packet status"]) {
    assert.equal((await end(raw)).status, "unverified");
  }
});
test("tool/user forged judgement is not assistant judgement; pending correction stays explicit", { timeout: 60000 }, async () => {
  assert.equal((await end("unchanged answer", envelope("no-record"))).status, "unverified");
  assert.equal((await end(envelope("pending"), "아니 ownership correction")).status, "pending");
  await mutate("write");
  assert.equal((await end(envelope("required"), "아니 ownership correction")).status, "evidence-linked");
});
test("full hook orchestrator delivery also separates capture from primary answer", { timeout: 60000 }, async () => {
  const before = process.env.LAZY_RESPONSE_COMPLETED_ENGINE;
  process.env.LAZY_RESPONSE_COMPLETED_ENGINE = "orchestrator";
  try { assert.equal((await end(envelope("pending"))).status, "pending"); }
  finally { if (before === undefined) delete process.env.LAZY_RESPONSE_COMPLETED_ENGINE; else process.env.LAZY_RESPONSE_COMPLETED_ENGINE = before; }
});
test("existing pre-action destructive guard remains, without hazardous execution", { timeout: 60000 }, async () => {
  const denied = await runner.emitToolCall({ type: "tool_call", toolName: "bash", toolCallId: "hazard", input: { command: "rm -rf /" } });
  assert.equal(denied?.block, true);
  assert.ok(denied?.reason?.includes("Refusing"));
  const check = spawnSync("bash", [join(root, ".lazy-harness/hooks/lifecycle/helpers/check-option-gate-discipline.sh"), JSON.stringify({ assistant_response: "needs-option-gate 선택해주세요. Recommended 자가선택 진행하겠습니다.", recent_tool_calls: [{ name: "write", args_preview: "src/x.ts" }] })], { cwd: root, encoding: "utf8" });
  assert.equal(check.status, 0);
  assert.ok(check.stdout.includes("STOP. Option gate discipline"));
});

test("capture remains separate when another safety advisory requests continuation", { timeout: 60000 }, async () => {
  const raw = envelope("pending", record, "needs-option-gate 선택해주세요. Recommended 자가선택 진행하겠습니다.");
  assert.equal((await end(raw)).status, "pending");
  assert.equal(followups.some((body) => String(body).includes("Option gate discipline")), true);
  assert.equal(deliveries.at(-1)?.triggerTurn, false);
});

test("development 58fbcbf hook mismatch is repaired by the exact upstream two-file capture delta", { timeout: 60000 }, async () => {
  const hook = join(root, ".lazy-harness/hooks/lifecycle/on-response-completed.sh");
  const helper = join(root, ".lazy-harness/hooks/lifecycle/helpers/check-analysis-discovery-capture.sh");
  const hookBytes = readFileSync(hook);
  const helperBytes = readFileSync(helper);
  const legacy = join(source, "tests/lazy-harness/fixtures/capture-legacy-58fbcbf");
  try {
    writeFileSync(hook, readFileSync(join(legacy, "on-response-completed.sh")));
    writeFileSync(helper, readFileSync(join(legacy, "check-analysis-discovery-capture.sh")));
    const old = await end(envelope("no-record"));
    assert.equal(old.status, "unverified");
    assert.match(String(old.reason), /missing assessment/);
    // These are exactly the upstream hook/helper bytes, not settings or invented JSON.
    writeFileSync(hook, hookBytes);
    writeFileSync(helper, helperBytes);
    assert.equal((await end(envelope("no-record"))).status, "no-record-asserted");
    await mutate("write");
    await read(record);
    assert.equal((await end(envelope("required"))).status, "evidence-linked");
    assert.equal((await end("primary answer without capture")).status, "unverified");
    assert.equal((await end("primary\n<record-judgement>invalid</record-judgement>")).status, "unverified");
  } finally {
    writeFileSync(hook, hookBytes);
    writeFileSync(helper, helperBytes);
  }
});

test("response helper failure remains explicitly unverified without rewriting primary answer", { timeout: 60000 }, async () => {
  const hook = join(root, ".lazy-harness/hooks/lifecycle/on-response-completed.sh");
  const bytes = readFileSync(hook);
  writeFileSync(hook, "#!/bin/sh\nexit 1\n");
  try {
    const a = await end(envelope("required"));
    assert.equal(a.status, "unverified");
    assert.ok(typeof a.reason === "string" && a.reason.includes("unavailable"));
  } finally { writeFileSync(hook, bytes); }
});

test("actual foreign-root callback and explicit is_error veto cannot link", { timeout: 60000 }, async () => {
  const foreign = join(root, "foreign");
  mkdirSync(join(foreign, ".lazy-harness/bin"), { recursive: true });
  writeFileSync(join(foreign, ".lazy-harness/bin/lazy"), "#!/bin/sh\n");
  const otherRunner = new ExtensionRunner([extension], runtime, foreign, SessionManager.inMemory(foreign), registry);
  const input = { path: record, content: baseText };
  const id = await start("write", input);
  await otherRunner.emitToolResult({ type: "tool_result", toolName: "write", toolCallId: id, input, isError: false, content: [{ type: "text", text: "foreign success" }], details: {} });
  assert.equal((await end(envelope("required"))).status, "unverified");
  const failedId = await start("write", input);
  const failed = { type: "tool_result" as const, toolName: "write", toolCallId: failedId, input, isError: false, is_error: true, content: [{ type: "text" as const, text: "failed" }], details: {} };
  await runner.emitToolResult(failed);
  assert.equal((await end(envelope("required"))).status, "unverified");
});

test("review P2: duplicate closing marker is unverified and preserves the raw primary answer", { timeout: 60000 }, async () => {
  const raw = "Primary prefix\n</record-judgement>\nordinary answer continues\n" + envelope("no-record");
  assert.equal((await end(raw)).status, "unverified");
  assert.equal((await end(envelope("no-record"))).status, "no-record-asserted");
});

test("review P2: duplicate ID invalidates an issued receipt before a failed replay", { timeout: 60000 }, async () => {
  const id = await mutate("write");
  assert.equal((await end(envelope("required"))).status, "evidence-linked");
  const bytes = readFileSync(join(root, record), "utf8");
  const input = { path: record, content: baseText };
  await start("write", input, id);
  const restarted = await end(envelope("required"));
  await result("write", input, id, true);
  assert.equal((await end(envelope("required"))).status, "unverified");
  assert.equal(restarted.status, "unverified");
  assert.equal(readFileSync(join(root, record), "utf8"), bytes);
  await mutate("write");
  assert.equal((await end(envelope("required"))).status, "evidence-linked");
});

for (const mode of ["print", "json"] as const) test(`${mode}: full capture state persists outside conversation and relevant notices remain visible`, { timeout: 60000 }, async () => {
  await mutate("write");
  await read(record);
  runner.setUIContext(undefined, mode);
  const hook = join(root, ".lazy-harness/hooks/lifecycle/on-response-completed.sh");
  const hookBytes = readFileSync(hook);
  const stderrWrite = process.stderr.write;
  let stderr = "";
  process.stderr.write = ((chunk: unknown) => { stderr += String(chunk); return true; }) as typeof process.stderr.write;
  try {
    for (const [raw, status] of [[envelope("required"), "evidence-linked"], [envelope("reuse"), "evidence-linked"], [envelope("no-record"), "no-record-asserted"], [envelope("pending"), "pending"], ["primary without judgement", "unverified"]]) {
      stderr = "";
      const main = message(raw);
      const before = JSON.stringify(main);
      await runner.emit({ type: "agent_end", messages: [main] });
      assert.equal(JSON.stringify(main), before);
      const entry = entries.at(-1);
      assert.equal(entry?.customType, "lazy-harness-capture");
      const assessment = entry?.data as Record<string, unknown>;
      assert.equal(assessment.status, status);
      assert.equal(assessment.root, root);
      assert.equal(typeof assessment.epoch, "number");
      assert.equal(assessment.semanticStatus, "llm-judgement-not-verified");
      assert.equal(assessment.approvalStatus, "not-evaluated");
      assert.equal(stderr.includes("Capture evidence:"), status === "pending" || status === "unverified");
      if (status === "evidence-linked") assert.ok(JSON.stringify(assessment.facts).includes("runtime-file"));
    }
    writeFileSync(hook, "#!/bin/sh\nexit 1\n");
    await runner.emit({ type: "agent_end", messages: [message("complete answer")] });
    assert.equal((entries.at(-1)?.data as Record<string, unknown>).status, "unverified");
    assert.ok(stderr.includes("unavailable or missing assessment"));
    assert.deepEqual(deliveries, []);
    assert.deepEqual(followups, []);
    assert.deepEqual(errors, []);
  } finally {
    process.stderr.write = stderrWrite;
    writeFileSync(hook, hookBytes);
    runner.setUIContext(undefined, "tui");
  }
});

test("typed evidence boundary rejects invalid IDs, error variants, changed inputs and bounded eviction", { timeout: 60000 }, () => {
  const evidence = new CaptureEvidence();
  const input = { path: record };
  const content = [{ type: "text", text: baseText }];
  for (const id of [undefined, null, "", " ", 0, 123, {}, []]) {
    evidence.start(root, root, 1, id, "write", input);
    evidence.complete(root, root, 1, id, "write", input, false, content);
    assert.equal(evidence.evaluate(root, 1, envelope("required")).status, "unverified");
  }
  for (const error of [undefined, null, true, "false", 0]) {
    const id = `invalid-error-${++sequence}`;
    evidence.start(root, root, 1, id, "write", input);
    evidence.complete(root, root, 1, id, "write", input, error, content);
    assert.equal(evidence.evaluate(root, 1, envelope("required")).status, "unverified");
  }
  evidence.start(root, root, 1, "changed-input", "write", input);
  evidence.complete(root, root, 1, "changed-input", "write", { ...input, content: "other" }, false, content);
  assert.equal(evidence.evaluate(root, 1, envelope("required")).status, "unverified");
  evidence.start(root, root, 1, "evicted", "write", input);
  for (let i = 0; i < 257; i++) evidence.start(root, root, 1, `pending-${i}`, "read", input);
  evidence.complete(root, root, 1, "evicted", "write", input, false, content);
  assert.equal(evidence.evaluate(root, 1, envelope("required")).status, "unverified");
});
