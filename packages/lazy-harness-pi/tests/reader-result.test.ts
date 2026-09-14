import { expect, test } from "bun:test";
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import lazyHarnessPi from "../extensions/lazy-harness/index";
import { parseReaderResultPacket } from "../extensions/lazy-harness/reader-result";

const host = resolve(import.meta.dir, "../../..");
const revision = execFileSync("git", ["rev-parse", "HEAD"], { cwd: host, encoding: "utf8" }).trim();
const hash = (text: string) => createHash("sha256").update(text).digest("hex").slice(0, 16);
const packet = (root: string, quoted = true, status = "complete") => {
  const value = (s: string) => quoted ? `\`${s}\`` : s;
  return `Fan-out result\nLAZY_HARNESS_READER_RESULT: ${status}\n\nroot: ${value(root)}\nrevision: ${value(revision)}\nevidenceEpoch: ${value("1")}\nfacts: delivery matters\n`;
};

for (const quoted of [false, true]) for (const status of ["complete", "incomplete", "conflict"]) {
  test(`result parser: ${quoted ? "quoted native" : "bare scripted"} ${status}`, () => {
    expect(parseReaderResultPacket(packet("/root", quoted, status))).toEqual({ root: "/root", revision, evidenceEpoch: "1", status });
  });
}
const malformed = [
  ["duplicate root", (s: string) => s + "root: `/root`\n"],
  ["conflicting root", (s: string) => s + "root: `/other`\n"],
  ["duplicate revision", (s: string) => s + `revision: ${revision}\n`],
  ["duplicate epoch", (s: string) => s + "evidenceEpoch: 1\n"],
  ["duplicate status", (s: string) => s + "LAZY_HARNESS_READER_RESULT: complete\n"],
  ["conflicting status", (s: string) => s + "LAZY_HARNESS_READER_RESULT: conflict\n"],
  ["unknown status", (s: string) => s.replace(": complete", ": completed")],
  ["quoted status", (s: string) => s.replace(": complete", ": `complete`")],
  ["missing status", (s: string) => s.replace("LAZY_HARNESS_READER_RESULT: complete", "")],
  ...["root", "revision", "evidenceEpoch"].flatMap((field) => [
    [`missing ${field}`, (s: string) => s.replace(new RegExp(`^${field}:.*$`, "m"), "")],
    [`unmatched ${field}`, (s: string) => s.replace(new RegExp(`^${field}: \\x60`, "m"), `${field}: `)],
    [`double delimiters ${field}`, (s: string) => s.replace(new RegExp(`^${field}: (.*)$`, "m"), `${field}: \`$1\``)],
    [`indented duplicate ${field}`, (s: string) => s + `  ${field}: bad\n`],
  ]),
] as [string, (s: string) => string][];
for (const [name, change] of malformed) test(`result parser rejects ${name}`, () => expect(parseReaderResultPacket(change(packet("/root")))).toBeUndefined());

async function fixture(sync: boolean) {
  const root = join(mkdtempSync(join(tmpdir(), "reader-result-")), "host");
  execFileSync("git", ["clone", "--quiet", "--shared", "--no-checkout", host, root]);
  mkdirSync(join(root, ".lazy-harness/bin"), { recursive: true });
  mkdirSync(join(root, ".lazy-harness/spec"), { recursive: true });
  writeFileSync(join(root, ".lazy-harness/bin/lazy"), "#!/bin/sh\n");
  writeFileSync(join(root, ".lazy-harness/spec/fact.md"), "fact");
  writeFileSync(join(root, ".lazy-harness/spec/second.md"), "second");
  const handlers = new Map<string, Function>();
  const tools = new Map<string, any>();
  lazyHarnessPi({ on: (name: string, handler: Function) => handlers.set(name, handler), registerCommand() {}, registerTool: (tool: any) => tools.set(tool.name, tool), exec: async () => ({ stdout: "", stderr: "", exitCode: 0 }) } as any);
  const ctx = { cwd: root, mode: "json", hasUI: false, sessionManager: { getCwd: () => root, getSessionId: () => root }, ui: { notify() {} } };
  await handlers.get("before_agent_start")!({ prompt: "fixture", systemPrompt: "base" }, ctx);
  const launch = { toolCallId: "launch", toolName: "subagent", input: { agent: "lazy-harness.record-reader", async: !sync, context: "fresh", acceptance: false, output: false, artifacts: false, model: "fixture/reader", cwd: root, agentContract: { version: 1 }, task: `root: ${root}\nrevision: ${revision}\nmodel: fixture/reader\nevidenceEpoch: 1\nmaxReadCalls: 2\nmaxRequestedLines: 400\nmaxLinesPerRead: 200\ntask: objective` } };
  expect(await handlers.get("tool_call")!(launch, ctx)).toBeUndefined();
  const sessionFile = join(root, "child.jsonl");
  const ledger = { root, revision, model: "fixture/reader", evidenceEpoch: 1, taskDigest: hash("objective"), sessionId: "child", terminal: true, maxReadCalls: 2, maxRequestedLines: 400, maxLinesPerRead: 200, readCalls: 2, requestedLines: 400, maxObservedReadLimit: 200, failedToolCalls: 0, recordHashes: { ".lazy-harness/spec/fact.md": hash("fact"), ".lazy-harness/spec/second.md": hash("second") } };
  const save = (data: any = ledger, header = "child") => writeFileSync(sessionFile, [{ type: "session", id: header }, { type: "custom", customType: "lazy-harness-reader-ledger-v1", data }].map((row) => JSON.stringify(row)).join("\n"));
  save();
  const result = { agent: "lazy-harness.record-reader", exitCode: 0, sessionFile };
  const receipt = { ...launch, isError: false, content: [{ type: "text", text: packet(root) }], details: { runId: "owned", mode: "single", results: [result] } };
  const notification = { role: "custom", customType: "subagent-notify", content: `Background task completed: **lazy-harness.record-reader**\n${packet(root)}`, details: { completions: [{ runId: "owned", agent: "lazy-harness.record-reader", sessionFile }] } };
  const deliver = async () => {
    await handlers.get("tool_result")!(sync ? receipt : { ...launch, details: { runId: "owned", asyncId: "owned" }, content: [{ type: "text", text: "launched" }] }, ctx);
    if (!sync) await handlers.get("context")!({ messages: [notification] }, ctx);
  };
  const params = { revision, evidenceEpoch: 1, status: "complete", resultMarker: "LAZY_HARNESS_READER_RESULT: complete" };
  const close = (overrides = {}) => tools.get("lazy_reader_join").execute("join", { ...params, ...overrides }, undefined, undefined, ctx);
  const changeText = (change: (s: string) => string) => { receipt.content[0].text = change(receipt.content[0].text); notification.content = change(notification.content); };
  return { root, ctx, handlers, launch, receipt, notification, ledger, save, deliver, close, changeText };
}
for (const sync of [true, false]) {
  const mode = sync ? "sync" : "async";
  test(`${mode} quoted delivered packet joins the full ledger, not asserted subset`, async () => {
    const f = await fixture(sync); await f.deliver();
    expect((await f.close({ recordPaths: [".lazy-harness/spec/fact.md"] })).details).toMatchObject({ joined: true, recordCount: 2, recordPaths: [".lazy-harness/spec/fact.md", ".lazy-harness/spec/second.md"] });
  });
  for (const status of ["incomplete", "conflict"]) test(`${mode} cannot relabel actual ${status} complete or cache it`, async () => {
    const f = await fixture(sync); f.changeText((s) => s.replace(": complete", `: ${status}`)); await f.deliver();
    expect((await f.close()).details).toMatchObject({ joined: false, fallbackAllowed: true, status });
    await expect(f.close()).rejects.toThrow("terminal fallback");
    const next = await f.handlers.get("before_agent_start")!({ prompt: "next", systemPrompt: "base" }, f.ctx);
    expect(JSON.stringify(next)).not.toContain("reused-work-unit");
  });
  for (const [name, change] of malformed) test(`${mode} rejects malformed packet: ${name}`, async () => { const f = await fixture(sync); f.changeText(change); await f.deliver(); await expect(f.close()).rejects.toThrow("bounded direct Parent fallback"); });
  for (const field of ["root", "revision", "evidenceEpoch"]) test(`${mode} rejects quoted wrong ${field}`, async () => {
    const f = await fixture(sync); f.changeText((s) => s.replace(new RegExp(`^${field}:.*$`, "m"), `${field}: \`wrong\``)); await f.deliver(); await expect(f.close()).rejects.toThrow("identity/status");
  });
  const ledgerCases: [string, Record<string, any>][] = [
    ["wrong root", { root: "/other" }], ["wrong revision", { revision: "wrong" }], ["wrong epoch", { evidenceEpoch: 0 }], ["wrong model", { model: "wrong" }], ["wrong task", { taskDigest: "wrong" }], ["wrong session", { sessionId: "other" }], ["nonterminal", { terminal: false }], ["absent ledger", {}],
    ["failed read", { failedToolCalls: 1 }], ["zero reads", { readCalls: 0 }], ["zero lines", { requestedLines: 0 }], ["zero observed", { maxObservedReadLimit: 0 }], ["impossible lines", { readCalls: 1 }], ["observed over cap", { maxObservedReadLimit: 201 }], ["raised calls", { maxReadCalls: 8 }], ["raised lines", { maxRequestedLines: 1600 }], ["raised per read", { maxLinesPerRead: 201 }], ["over calls", { readCalls: 3 }], ["over lines", { requestedLines: 401 }], ["noninteger", { readCalls: 1.5 }], ["negative", { failedToolCalls: -1 }], ["no paths", { recordHashes: {} }], ["outside path", { recordHashes: { "source.txt": hash("fact") } }],
  ];
  for (const [name, delta] of ledgerCases) test(`${mode} rejects ledger ${name}`, async () => {
    const f = await fixture(sync); f.save(name === "absent ledger" ? {} : { ...f.ledger, ...delta }); await f.deliver(); await expect(f.close()).rejects.toThrow("bounded direct Parent fallback");
  });
  for (const [name, params] of [["wrong run", { runId: "wrong" }], ["wrong epoch", { evidenceEpoch: 0 }], ["false counter", { readCalls: 0 }], ["unread", { recordPaths: [".lazy-harness/spec/unread.md"] }], ["duplicate paths", { recordPaths: [".lazy-harness/spec/fact.md", ".lazy-harness/spec/fact.md"] }]] as const) test(`${mode} rejects asserted ${name}`, async () => { const f = await fixture(sync); await f.deliver(); await expect(f.close(params)).rejects.toThrow("bounded direct Parent fallback"); });
  test(`${mode} rejects hash drift on omitted path`, async () => { const f = await fixture(sync); await f.deliver(); writeFileSync(join(f.root, ".lazy-harness/spec/second.md"), "changed"); await expect(f.close({ recordPaths: [".lazy-harness/spec/fact.md"] })).rejects.toThrow("changed"); });
  test(`${mode} stale steer cannot revive packet`, async () => { const f = await fixture(sync); await f.handlers.get("input")!({ text: "steer", source: "user", streamingBehavior: "steer" }, f.ctx); await f.deliver(); await expect(f.close()).rejects.toThrow(); });
}
for (const kind of ["missing-content", "wrong-agent", "multiple-results", "failed-exit", "missing-session", "missing-run", "conflicting-run", "wrong-call", "wrong-mode"]) test(`sync native binding rejects ${kind}`, async () => {
  const f = await fixture(true); const r: any = f.receipt;
  if (kind === "missing-content") { r.details.results[0].finalOutput = r.content[0].text; r.content = []; }
  if (kind === "wrong-agent") r.details.results[0].agent = "other";
  if (kind === "multiple-results") r.details.results.push(r.details.results[0]);
  if (kind === "failed-exit") r.details.results[0].exitCode = 1;
  if (kind === "missing-session") delete r.details.results[0].sessionFile;
  if (kind === "missing-run") delete r.details.runId;
  if (kind === "conflicting-run") r.details.asyncId = "other";
  if (kind === "wrong-call") r.toolCallId = "other";
  if (kind === "wrong-mode") r.details.mode = "parallel";
  await f.deliver(); await expect(f.close()).rejects.toThrow();
});
for (const kind of ["wrong-run", "wrong-agent", "duplicate-owned", "missing-session", "status-only", "missing-content"]) test(`async native binding rejects ${kind}`, async () => {
  const f = await fixture(false); const n: any = f.notification;
  if (kind === "wrong-run") n.details.completions[0].runId = "other";
  if (kind === "wrong-agent") n.details.completions[0].agent = "other";
  if (kind === "duplicate-owned") n.details.completions.push(n.details.completions[0]);
  if (kind === "missing-session") delete n.details.completions[0].sessionFile;
  if (kind === "status-only") n.customType = "subagent-status";
  if (kind === "missing-content") { n.details.finalOutput = n.content; n.content = ""; }
  await f.deliver(); await expect(f.close()).rejects.toThrow("notification");
});
