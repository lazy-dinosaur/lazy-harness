import { afterEach, expect, test } from "bun:test";
import { execFileSync } from "node:child_process";
import { copyFileSync, mkdtempSync, readFileSync, rmSync, symlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { collectRuntimeUsage } from "./collect-runtime-usage.ts";

const roots: string[] = [];
afterEach(() => { for (const root of roots.splice(0)) rmSync(root, { recursive: true, force: true }); });
const usage = { input: 10, output: 2, cacheRead: 5, cacheWrite: 3, totalTokens: 20, cost: { total: 0.1 } };
function assistant(id: string, supplied: any = usage, stopReason = "stop") {
  return { type: "message", id, message: { role: "assistant", provider: "example", model: "model", content: "private answer", usage: supplied, stopReason } };
}
function fixture() {
  const root = mkdtempSync(join(tmpdir(), "runtime-usage-")); roots.push(root);
  const parent = join(root, "parent.jsonl");
  const reader = join(root, "reader.jsonl");
  const save = (path: string, id: string, rows: any[]) => writeFileSync(path, [{ type: "session", id }, ...rows].map(row => JSON.stringify(row)).join("\n") + "\n");
  save(parent, "parent-session", [assistant("p1"), { type: "message", id: "user", message: { role: "user", content: "prompt" } }]);
  save(reader, "reader-session", [assistant("r1"), assistant("r2", usage, "error")]);
  const manifest = { runtime: "pi", measurement: "offline", sessions: [{ role: "parent", path: parent }, { role: "reader", path: reader }] };
  return { root, parent, reader, save, manifest };
}

test.each(["pi", "omp"])("%s includes Parent, Reader and logged error usage without recounting caches", runtime => {
  const f = fixture();
  const report = collectRuntimeUsage({ ...f.manifest, runtime });
  expect(report.totals).toEqual({ input: 30, output: 6, cacheRead: 15, cacheWrite: 9, totalTokens: 60 });
  expect(report.byRole.parent.totalTokens).toBe(20);
  expect(report.byRole.reader.totalTokens).toBe(40);
  expect(report.assistantMessages).toBe(3);
  expect(report.nonSuccessfulStops).toBe(1);
  expect(report.runtimeEstimatedCost.completeEstimate).toBeCloseTo(0.3);
  expect(report.providerRequestCount).toBeNull();
  expect(report.unloggedRetryUsage).toBe("unknown");
  expect(report.inventoryCompletenessVerified).toBe(false);
  expect(report.taskSuccess).toBe("not-evaluated");
  expect(JSON.stringify(report)).not.toContain("private answer");
});

test("OMP title metadata preserves totals without changing Pi header admission", () => {
  const f = fixture();
  const before = collectRuntimeUsage({ ...f.manifest, runtime: "omp" });
  for (const path of [f.parent, f.reader]) writeFileSync(path, JSON.stringify({ type: "title", v: 1, title: "private title" }) + "\n" + readFileSync(path, "utf8"));
  expect(collectRuntimeUsage({ ...f.manifest, runtime: "omp" })).toEqual(before);
  expect(() => collectRuntimeUsage(f.manifest)).toThrow("leading session header");
});

test("OMP rejects duplicate, displaced and malformed session preludes", () => {
  const f = fixture();
  const session = { type: "session", id: "parent-session" };
  for (const rows of [
    [{ type: "title", v: 2 }, session],
    [{ type: "title", v: 1 }, { type: "title", v: 1 }, session],
    [{ type: "custom" }, session],
    [{ type: "title", v: 1 }, session, session],
  ]) {
    writeFileSync(f.parent, [...rows, assistant("p1")].map(row => JSON.stringify(row)).join("\n"));
    expect(() => collectRuntimeUsage({ ...f.manifest, runtime: "omp" })).toThrow("leading session header");
  }
});

test("retains runtime-reported total independently of component arithmetic", () => {
  const f = fixture();
  f.save(f.parent, "parent-session", [assistant("p1", { ...usage, totalTokens: 99 })]);
  expect(collectRuntimeUsage(f.manifest).totals.totalTokens).toBe(139);
});

test("missing estimated cost is unknown, not free", () => {
  const f = fixture();
  f.save(f.parent, "parent-session", [assistant("p1", { ...usage, cost: undefined })]);
  expect(collectRuntimeUsage(f.manifest).runtimeEstimatedCost).toEqual({ knownSubtotal: 0.2, missingCostMessages: 1, completeEstimate: null });
});

test.each([undefined, null, -1, 1.5, "10", Number.MAX_SAFE_INTEGER + 1])("rejects invalid input token field %s", input => {
  const f = fixture();
  f.save(f.parent, "parent-session", [assistant("p1", { ...usage, input })]);
  expect(() => collectRuntimeUsage(f.manifest)).toThrow("invalid usage.input");
});

test("rejects missing usage rather than silently dropping a model response", () => {
  const f = fixture();
  const row = assistant("p1"); delete row.message.usage;
  f.save(f.parent, "parent-session", [row]);
  expect(() => collectRuntimeUsage(f.manifest)).toThrow("missing or invalid usage");
});

test("rejects duplicate files through a symlink", () => {
  const f = fixture(); const alias = join(f.root, "alias.jsonl"); symlinkSync(f.parent, alias);
  f.manifest.sessions[1].path = alias;
  expect(() => collectRuntimeUsage(f.manifest)).toThrow("duplicate session path");
});

test("rejects copied sessions with different paths", () => {
  const f = fixture(); copyFileSync(f.parent, f.reader);
  expect(() => collectRuntimeUsage(f.manifest)).toThrow("duplicate session id");
});

test("rejects duplicate assistant IDs across files", () => {
  const f = fixture(); f.save(f.reader, "reader-session", [assistant("p1")]);
  expect(() => collectRuntimeUsage(f.manifest)).toThrow("duplicate assistant entry id");
});

test("rejects malformed JSON and trace-like files without a session header", () => {
  const f = fixture(); writeFileSync(f.reader, "{truncated\n");
  expect(() => collectRuntimeUsage(f.manifest)).toThrow("invalid JSON");
  writeFileSync(f.reader, JSON.stringify(assistant("r1")));
  expect(() => collectRuntimeUsage(f.manifest)).toThrow("session header required");
});

test("rejects unsafe aggregate and malformed cost", () => {
  const f = fixture();
  f.save(f.reader, "reader-session", [assistant("r1", { ...usage, input: Number.MAX_SAFE_INTEGER })]);
  expect(() => collectRuntimeUsage(f.manifest)).toThrow("unsafe aggregate");
  f.save(f.reader, "reader-session", [assistant("r1", { ...usage, cost: { total: -1 } })]);
  expect(() => collectRuntimeUsage(f.manifest)).toThrow("invalid estimated cost");
});

test("requires one Parent and valid manifest metadata", () => {
  const f = fixture();
  expect(() => collectRuntimeUsage({ ...f.manifest, runtime: "invented" })).toThrow("runtime");
  expect(() => collectRuntimeUsage({ ...f.manifest, measurement: "measured-maybe" })).toThrow("measurement");
  expect(() => collectRuntimeUsage({ ...f.manifest, sessions: [] })).toThrow("nonempty");
  expect(() => collectRuntimeUsage({ ...f.manifest, sessions: [f.manifest.sessions[1]] })).toThrow("one Parent");
});

test("CLI resolves relative paths from the manifest and leaves inputs unchanged", () => {
  const f = fixture();
  const manifest = join(f.root, "manifest.json");
  writeFileSync(manifest, JSON.stringify({ ...f.manifest, sessions: [{ role: "parent", path: "parent.jsonl" }, { role: "reader", path: "reader.jsonl" }] }));
  const before = readFileSync(f.parent, "utf8");
  const output = execFileSync("bun", [join(import.meta.dir, "collect-runtime-usage.ts"), manifest], { encoding: "utf8" });
  expect(JSON.parse(output).totals.totalTokens).toBe(60);
  expect(readFileSync(f.parent, "utf8")).toBe(before);
});
