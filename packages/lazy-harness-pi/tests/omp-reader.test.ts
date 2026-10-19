import { afterEach, expect, test } from "bun:test";
import { execFileSync } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, symlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { EventEmitter } from "node:events";
import lazyHarness from "../extensions/lazy-harness/index.ts";
import { activateOmpReader, ompReaderDefinition, OMP_READER_NAME } from "../omp/reader-definition.ts";
import { OmpReaderTransport } from "../omp/reader-transport.ts";

const roots: string[] = [];
afterEach(() => { for (const root of roots.splice(0)) rmSync(root, { recursive: true, force: true }); });
function host() {
  const dir = mkdtempSync(join(tmpdir(), "omp-reader-")); roots.push(dir);
  const root = join(dir, "host");
  execFileSync("git", ["clone", "--quiet", "--shared", "--no-checkout", resolve(import.meta.dir, "../../.."), root]);
  mkdirSync(join(root, ".lazy-harness/bin"), { recursive: true });
  mkdirSync(join(root, ".lazy-harness/spec"), { recursive: true });
  writeFileSync(join(root, ".lazy-harness/bin/lazy"), "#!/bin/sh\n");
  writeFileSync(join(root, ".lazy-harness/spec/fact.md"), "fact");
  return root;
}

test("registration is explicit, preview-only, idempotent and uses the canonical body", () => {
  const root = host();
  const preview = activateOmpReader(root, "fixture/reader");
  expect(preview).toMatchObject({ action: "create", applied: false });
  expect(existsSync(join(root, ".omp"))).toBe(false);
  activateOmpReader(root, "fixture/reader", true);
  expect(activateOmpReader(root, "fixture/reader", true).action).toBe("unchanged");
  const canonical = readFileSync(new URL("../agents/record-reader.md", import.meta.url), "utf8").split("LAZY_HARNESS_ROLE:")[1].trim();
  const activated = readFileSync(preview.path, "utf8");
  expect(activated).toContain("yield({data:{packet: TEXT}}) on OMP 18");
  expect(activated).toContain("yield({result:{data:{packet: TEXT}}}) when the schema exposes result");
  expect(readFileSync(preview.path, "utf8").split("LAZY_HARNESS_ROLE:")[1].trim()).toBe(canonical);
  expect(() => activateOmpReader(root, "fixture/other", true)).toThrow("reconciliation");
});
for (const model of ["inherit", "provider/model:low", "p/m\nblocking: false", "p/m,other/model"]) {
  test(`reject model ${JSON.stringify(model)}`, () => expect(() => ompReaderDefinition(model)).toThrow());
}
for (const link of [".omp", ".omp/agents", ".omp/agents/lazy-harness.record-reader.md"]) {
  test(`reject symlink ${link}`, () => {
    const root = host();
    if (link !== ".omp") mkdirSync(join(root, ".omp/agents"), { recursive: true });
    if (link === ".omp/agents") rmSync(join(root, link), { recursive: true });
    symlinkSync(join(root, "missing"), join(root, link));
    expect(() => activateOmpReader(root, "fixture/reader", true)).toThrow();
  });
}

async function fixture() {
  const root = host();
  const revision = execFileSync("git", ["rev-parse", "HEAD"], { cwd: root, encoding: "utf8" }).trim();
  activateOmpReader(root, "fixture/reader", true);
  const bus = new EventEmitter();
  function instance(id: string) {
    const handlers = new Map<string, Function>();
    const tools = new Map<string, any>();
    const entries: any[] = [{ type: "session", id }];
    const api = { on: (name: string, fn: Function) => handlers.set(name, fn), events: { on: (channel: string, fn: any) => { bus.on(channel, fn); return () => { bus.off(channel, fn); }; } }, getThinkingLevel: () => "low", registerCommand() {}, registerTool: (tool: any) => tools.set(tool.name, tool), appendEntry: (customType: string, data: unknown) => entries.push({ type: "custom", customType, data: structuredClone(data) }), exec: async () => ({ stdout: "", stderr: "", exitCode: 0 }) };
    const transport = new OmpReaderTransport(api);
    lazyHarness(api as any, { readerTransport: transport });
    const ctx = { cwd: root, mode: "json", hasUI: false, model: { provider: "fixture", id: "reader" }, sessionManager: { getCwd: () => root, getSessionId: () => id }, ui: { notify() {} } };
    return { ctx, entries, tools, transport, call: (name: string, event: any) => handlers.get(name)!(event, ctx) };
  }
  const parent = instance("parent");
  const child = instance("child-session");
  await parent.call("before_agent_start", { prompt: "fixture", systemPrompt: "base" });
  const task = `root: ${root}\nrevision: ${revision}\nmodel: fixture/reader\nevidenceEpoch: 1\nmaxReadCalls: 2\nmaxRequestedLines: 100\nmaxLinesPerRead: 50\ntask: objective`;
  const launch = { toolName: "task", toolCallId: "launch", input: { agent: OMP_READER_NAME, assignment: task } };
  const sessionFile = join(root, "child.jsonl");
  const lifecycle = { agent: OMP_READER_NAME, id: "native-run", parentToolCallId: "launch", index: 0, sessionFile };
  const emit = (status: string, overrides = {}) => bus.emit("task:subagent:lifecycle", { ...lifecycle, status, ...overrides });
  const packet = `LAZY_HARNESS_READER_RESULT: complete\nroot: ${root}\nrevision: ${revision}\nevidenceEpoch: 1`;
  const result = { ...launch, content: [{ type: "text", text: `<output>\n${JSON.stringify({ packet })}\n</output>` }], details: { results: [{ id: "native-run", agent: OMP_READER_NAME, exitCode: 0, truncated: false }] } };
  async function read() {
    await child.call("before_agent_start", { prompt: `Task: ${task}`, systemPrompt: "LAZY_HARNESS_ROLE: record-reader/reader-join-v1" });
    const read = { toolName: "read", toolCallId: "read", input: { path: ".lazy-harness/spec/fact.md:raw:1-47" } };
    expect(await child.call("tool_call", read)).toBeUndefined();
    await child.call("tool_result", { ...read, content: [{ type: "text", text: "fact" }], details: { displayContent: { lineNumbers: [1] } } });
    await child.call("agent_end", { messages: [] });
    writeFileSync(sessionFile, child.entries.map(entry => JSON.stringify(entry)).join("\n"));
  }
  const close = () => parent.tools.get("lazy_reader_join").execute("join", { status: "complete", revision, evidenceEpoch: 1, resultMarker: "LAZY_HARNESS_READER_RESULT: complete" }, undefined, undefined, parent.ctx);
  return { root, parent, child, task, launch, emit, result, read, close };
}

test("native task and legacy assignment normalize identically and reject ambiguous/overridden instructions", async () => {
  const f = await fixture();
  const context = "Read-only canonical record loading; the assignment supplies the full identity and budget.";
  for (const field of ["task", "assignment"]) {
    for (const input of [
      { agent: OMP_READER_NAME, [field]: f.task },
      { agent: OMP_READER_NAME, context, tasks: [{ agent: OMP_READER_NAME, [field]: f.task }] },
      { context, tasks: [{ agent: OMP_READER_NAME, [field]: f.task }] },
    ]) expect(f.parent.transport.prepare(f.root, "task", input)).toEqual({ agent: OMP_READER_NAME, task: f.task, model: "fixture/reader" });
  }
  for (const item of [
    { task: f.task, assignment: f.task },
    { task: f.task, assignment: undefined },
    { task: 17 }, {},
    { task: f.task, model: "other/model" },
    { task: f.task, role: "writer" },
  ]) {
    expect(() => f.parent.transport.prepare(f.root, "task", { agent: OMP_READER_NAME, ...item })).toThrow();
    expect(() => f.parent.transport.prepare(f.root, "task", { agent: OMP_READER_NAME, context, tasks: [{ agent: OMP_READER_NAME, ...item }] })).toThrow();
  }
  for (const input of [
    { agent: OMP_READER_NAME, context, tasks: [{ task: f.task }] },
    { agent: OMP_READER_NAME, context, tasks: [{ agent: "task", task: f.task }] },
    { agent: "writer", context, tasks: [{ agent: OMP_READER_NAME, task: f.task }] },
    { context, tasks: [{ agent: OMP_READER_NAME, task: f.task }, { agent: "writer", task: f.task }] },
  ]) expect(() => f.parent.transport.prepare(f.root, "task", input)).toThrow();
});

for (const shape of ["legacy", "native18"]) test(`native ${shape} lifecycle + visible content + actual child hook ledger join through shared core`, async () => {
  const f = await fixture();
  const launch = shape === "legacy" ? f.launch : { ...f.launch, input: {
    context: "Read-only canonical record loading; the assignment supplies the full identity and budget.",
    tasks: [{ agent: OMP_READER_NAME, task: f.task }],
  } };
  expect(await f.parent.call("tool_call", launch)).toBeUndefined();
  f.emit("started"); await f.read();
  if (shape === "native18") {
    const path = join(f.root, "child.jsonl");
    writeFileSync(path, JSON.stringify({ type: "title", v: 1, title: "Reader" }) + "\n" + readFileSync(path, "utf8"));
  }
  f.emit("completed");
  await f.parent.call("tool_result", { ...f.result, input: launch.input });
  expect((await f.close()).details).toMatchObject({ joined: true, recordCount: 1 });
});

test("native session title prelude never substitutes for or obscures session identity", () => {
  const transport = new OmpReaderTransport({} as any);
  const header = { type: "session", id: "child" };
  const title = { type: "title", v: 1, title: "Reader" };
  expect(transport.sessionHeader([header])).toEqual(header);
  expect(transport.sessionHeader([title, header])).toEqual(header);
  for (const entries of [[], [title], [{ ...title, v: 2 }, header], [title, title, header], [header, header], [{ type: "custom" }, header], [{ type: "session", id: "" }]]) {
    expect(transport.sessionHeader(entries)).toBeUndefined();
  }
});

test("native yield aliases accept only a single terminal packet envelope", () => {
  const transport = new OmpReaderTransport({ events: { on() {} } } as any);
  const data = { packet: "LAZY_HARNESS_READER_RESULT: complete" };
  expect(transport.isTerminalCall("yield", { data })).toBe(true);
  expect(transport.isTerminalCall("yield", { result: { data } })).toBe(true);
  for (const args of [{}, { data, result: { data } }, { data, type: ["incremental"] }, { error: "failed" }, { data: { ...data, extra: true } }, { result: { data, error: "failed" } }]) {
    expect(transport.isTerminalCall("yield", args)).toBe(false);
  }
});
for (const mutation of ["missing-start", "wrong-id", "missing-content", "failed", "truncated", "stale", "wrong-model", "duplicate-start"]) {
  test(`native Reader rejects ${mutation}`, async () => {
    const f = await fixture();
    expect(await f.parent.call("tool_call", f.launch)).toBeUndefined();
    if (mutation !== "missing-start") f.emit("started");
    if (mutation === "duplicate-start") f.emit("started");
    if (mutation === "wrong-model") {
      f.child.ctx.model.id = "other";
      await f.child.call("before_agent_start", { prompt: f.task, systemPrompt: "LAZY_HARNESS_ROLE: record-reader/reader-join-v1" });
      expect((await f.child.call("tool_call", { toolName: "read", toolCallId: "read", input: { path: ".lazy-harness/spec/fact.md", limit: 50 } })).block).toBe(true);
    } else await f.read();
    f.emit(mutation === "failed" ? "failed" : "completed", mutation === "wrong-id" ? { id: "foreign" } : {});
    if (mutation === "missing-content") f.result.content = [];
    if (mutation === "truncated") f.result.details.results[0].truncated = true;
    if (mutation === "stale") await f.parent.call("before_agent_start", { prompt: "new work", systemPrompt: "base" });
    await f.parent.call("tool_result", f.result);
    await expect(f.close()).rejects.toThrow();
  });
}
for (const extra of [{ role: "writer" }, { context: "history" }, { tasks: [] }, { isolated: true }, { async: false }]) {
  test(`native Reader rejects launch overrides ${JSON.stringify(extra)}`, async () => {
    const f = await fixture();
    expect((await f.parent.call("tool_call", { ...f.launch, input: { ...f.launch.input, ...extra } })).block).toBe(true);
  });
}

test("native read return overrun is hidden and charged as a failed call", async () => {
  const f = await fixture();
  await f.child.call("before_agent_start", { prompt: f.task, systemPrompt: "LAZY_HARNESS_ROLE: record-reader/reader-join-v1" });
  const read = { toolName: "read", toolCallId: "range", input: { path: ".lazy-harness/spec/fact.md:raw:1-47" } };
  expect(await f.child.call("tool_call", read)).toBeUndefined();
  const result = await f.child.call("tool_result", { ...read, content: [{ type: "text", text: "out-of-budget content" }], details: { displayContent: { lineNumbers: [1, 300] } } });
  expect(result.isError).toBe(true);
  expect(JSON.stringify(result)).not.toContain("out-of-budget content");
  expect(f.child.entries.at(-1).data).toMatchObject({ failedToolCalls: 1, requestedLines: 50, recordHashes: {} });
});

test("native range accounting includes context and rejects unknown selectors", () => {
  const t = new OmpReaderTransport({});
  expect(t.normalizeRead("range", { path: ".lazy-harness/spec/fact.md:raw:2-47" })).toEqual({ path: ".lazy-harness/spec/fact.md", offset: 1, limit: 50 });
  for (const path of [".lazy-harness/spec/fact.md", ".lazy-harness/spec/fact.md:raw:1-", ".lazy-harness/spec/fact.md:raw:1-20,40-50", ".lazy-harness/spec/fact.md:raw:10-1"]) {
    expect(() => t.normalizeRead("bad", { path })).toThrow();
  }
  expect(() => t.normalizeRead("legacy", { path: ".lazy-harness/spec/fact.md", limit: 50 })).toThrow();
});

test("activation CLI supports space/equals forms and remains preview-only by default", () => {
  const root = host();
  const script = resolve(import.meta.dir, "../scripts/activate-omp-reader.ts");
  const preview = JSON.parse(execFileSync("bun", [script, "--target", root, "--model=fixture/reader"], { encoding: "utf8" }));
  expect(preview.applied).toBe(false);
  expect(existsSync(preview.path)).toBe(false);
  const applied = JSON.parse(execFileSync("bun", [script, `--target=${root}`, "--model", "fixture/reader", "--apply"], { encoding: "utf8" }));
  expect(applied.applied).toBe(true);
  expect(existsSync(applied.path)).toBe(true);
});
