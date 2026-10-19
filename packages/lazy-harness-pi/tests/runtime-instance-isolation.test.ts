import { afterEach, expect, test } from "bun:test";
import { execFileSync } from "node:child_process";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import lazyHarness from "../extensions/lazy-harness/index.ts";

const roots: string[] = [];
afterEach(() => { for (const root of roots.splice(0)) rmSync(root, { recursive: true, force: true }); });
function host() {
  const directory = mkdtempSync(join(tmpdir(), "lh-instance-")); roots.push(directory);
  const root = join(directory, "host");
  execFileSync("git", ["clone", "--quiet", "--shared", "--no-checkout", resolve(import.meta.dir, "../../.."), root]);
  mkdirSync(join(root, ".lazy-harness/bin"), { recursive: true });
  writeFileSync(join(root, ".lazy-harness/bin/lazy"), "#!/bin/sh\n");
  return root;
}
function instance(root: string, id: string) {
  const handlers = new Map<string, Function>();
  const entries: any[] = [];
  lazyHarness({ on: (name: string, fn: Function) => handlers.set(name, fn), registerTool() {}, registerCommand() {}, appendEntry: (customType: string, data: unknown) => entries.push({ customType, data }), exec: async () => ({ stdout: "", stderr: "", exitCode: 0 }) } as any);
  const ctx = { cwd: root, mode: "json", hasUI: false, sessionManager: { getCwd: () => root, getSessionId: () => id }, ui: { notify() {} } };
  return { entries, call: (name: string, event: any) => handlers.get(name)!(event, ctx) };
}

test("same-root extension instances own independent evidence epochs", async () => {
  const root = host();
  const parent = instance(root, "parent");
  const sibling = instance(root, "sibling");
  const event = { prompt: "fixture", systemPrompt: "base" };
  expect((await parent.call("before_agent_start", event)).message.content).toContain("evidence-epoch=1");
  expect((await sibling.call("before_agent_start", event)).message.content).toContain("evidence-epoch=1");
  expect((await parent.call("before_agent_start", event)).message.content).toContain("evidence-epoch=2");
});

test("same-root Reader role and read meter cannot leak into its Parent", async () => {
  const root = host();
  const revision = execFileSync("git", ["rev-parse", "HEAD"], { cwd: root, encoding: "utf8" }).trim();
  const parent = instance(root, "parent");
  const child = instance(root, "child");
  await parent.call("before_agent_start", { prompt: "fixture", systemPrompt: "base" });
  await child.call("before_agent_start", { systemPrompt: ["LAZY_HARNESS_ROLE: record-reader/reader-join-v1"], prompt: `root: ${root}\nrevision: ${revision}\nmodel: fixture/reader\nevidenceEpoch: 1\nmaxReadCalls: 2\nmaxRequestedLines: 100\nmaxLinesPerRead: 50\ntask: read fact` });
  expect(child.entries.length).toBeGreaterThan(0);
  const parentResult = await parent.call("tool_call", { toolCallId: "source", toolName: "read", input: { path: "source.ts", limit: 20 } });
  expect(parentResult).toBeUndefined();
  const childResult = await child.call("tool_call", { toolCallId: "source-denied", toolName: "read", input: { path: "source.ts", limit: 20 } });
  expect(childResult?.block).toBe(true);
  expect(childResult?.reason).toContain("Reader boundary");
});

test("custom-trigger Reader start without prompt fails closed instead of throwing", async () => {
  const root = host();
  const child = instance(root, "custom-child");
  await child.call("before_agent_start", { messageType: "custom", message: { content: "custom" }, systemPrompt: "LAZY_HARNESS_ROLE: record-reader/reader-join-v1" });
  const denied = await child.call("tool_call", { toolCallId: "no-envelope", toolName: "read", input: { path: ".lazy-harness/spec/fact.md", limit: 20 } });
  expect(denied?.block).toBe(true);
  expect(denied?.reason).toContain("missing runtime-owned launch budget/identity");
});
