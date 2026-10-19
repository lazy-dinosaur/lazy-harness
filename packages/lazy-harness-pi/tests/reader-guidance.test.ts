import { expect, test } from "bun:test";
import { execFileSync } from "node:child_process";
import { mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import lazyHarnessPi from "../extensions/lazy-harness/index.ts";
import { ompReaderDefinition } from "../omp/reader-definition.ts";

const host = resolve(import.meta.dir, "../../..");
const prompt = readFileSync(new URL("../agents/record-reader.md", import.meta.url), "utf8");
const body = prompt.replace(/^---\r?\n[\s\S]*?\r?\n---\r?\n/, "").trim();

test("Reader guidance separates body allowance, task coverage, path identity and stopping causes", () => {
  for (const clause of [
    "count record-body reads, not overview, drill, identity-probe or discovery calls",
    "Use the discovered root-relative `.lazy-harness/...` record path verbatim",
    "Keep the absolute `root` identity in the launch/result unchanged",
    "not every page of every selected record or every layer",
    "Do not return incomplete merely because overview and identity probes finished",
    "An unperformed next step alone is not a stopping cause",
    "Do not retry after a failed/denied read",
    "plain, unindented top-level result lines",
  ]) expect(body).toContain(clause);
  // This checks instruction preservation, not a live model's compliance.
  expect(prompt).toContain('turnBudget: {"maxTurns":12,"graceTurns":2}');
  expect(body).toContain("`failedToolCalls` is zero");
});

test("OMP generator carries the exact shared guidance without losing native encoding", () => {
  const generated = ompReaderDefinition("openai-codex/gpt-6-luna");
  expect(generated.endsWith(body + "\n")).toBe(true);
  expect(generated).toContain(".lazy-harness/...:raw:N-M");
  expect(generated).toContain("yield({data:{packet: TEXT}})");
});

test("nested-host Reader probes do not consume body allowance; relative paths work and original-root paths stay denied", async () => {
  const temp = mkdtempSync(join(tmpdir(), "reader-guidance-"));
  try {
    const root = join(temp, "isolated", "nested", "host");
    mkdirSync(join(temp, "isolated", "nested"), { recursive: true });
    execFileSync("git", ["clone", "--quiet", "--shared", "--no-checkout", host, root]);
    mkdirSync(join(root, ".lazy-harness/bin"), { recursive: true });
    mkdirSync(join(root, ".lazy-harness/spec"), { recursive: true });
    writeFileSync(join(root, ".lazy-harness/bin/lazy"), "#!/bin/sh\n");
    writeFileSync(join(root, ".lazy-harness/spec/fact.md"), "canonical fact\n");
    const revision = execFileSync("git", ["rev-parse", "HEAD"], { cwd: root, encoding: "utf8" }).trim();
    const handlers = new Map<string, Function>();
    const ledgers: any[] = [];
    lazyHarnessPi({
      on: (name: string, handler: Function) => handlers.set(name, handler), registerCommand() {}, registerTool() {},
      appendEntry: (kind: string, data: unknown) => { if (kind === "lazy-harness-reader-ledger-v1") ledgers.push(structuredClone(data)); },
      exec: async () => ({ stdout: "", stderr: "", exitCode: 0 }),
    } as any);
    const ctx = { cwd: root, mode: "json", sessionManager: { getCwd: () => root, getSessionId: () => "child" } };
    await handlers.get("before_agent_start")!({ systemPrompt: body, prompt: `root: ${root}\nrevision: ${revision}\nmodel: fixture/reader\nevidenceEpoch: 1\nmaxReadCalls: 4\nmaxRequestedLines: 600\nmaxLinesPerRead: 150\ntask: inspect canonical facts` }, ctx);
    let serial = 0;
    for (const command of [".lazy-harness/bin/lazy map --overview --complete --format=md", "pwd", "git rev-parse --show-toplevel", "git rev-parse HEAD"]) {
      const event = { toolName: "bash", toolCallId: `probe-${serial++}`, input: { command } };
      expect(await handlers.get("tool_call")!(event, ctx)).toBeUndefined();
      await handlers.get("tool_result")!({ ...event, isError: false }, ctx);
    }
    expect(ledgers.at(-1)).toMatchObject({ readCalls: 0, requestedLines: 0, failedToolCalls: 0 });
    const read = { toolName: "read", toolCallId: "relative", input: { path: ".lazy-harness/spec/fact.md", offset: 1, limit: 150 } };
    expect(await handlers.get("tool_call")!(read, ctx)).toBeUndefined();
    await handlers.get("tool_result")!({ ...read, isError: false }, ctx);
    expect(ledgers.at(-1)).toMatchObject({ readCalls: 1, requestedLines: 150, failedToolCalls: 0 });
    expect(Object.keys(ledgers.at(-1).recordHashes)).toEqual([".lazy-harness/spec/fact.md"]);
    const denied = await handlers.get("tool_call")!({ toolName: "read", toolCallId: "wrong-root", input: { path: join(host, ".lazy-harness/spec/platform/search-read-debt-contract.md"), offset: 1, limit: 150 } }, ctx);
    expect(denied.block).toBe(true);
    expect(ledgers.at(-1)).toMatchObject({ readCalls: 1, requestedLines: 150, failedToolCalls: 1 });
  } finally { rmSync(temp, { recursive: true, force: true }); }
});
