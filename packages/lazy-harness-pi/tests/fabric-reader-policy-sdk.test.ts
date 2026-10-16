import { expect, test } from "bun:test";
import { execFileSync } from "node:child_process";
import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { createEventBus, createExtensionRuntime, ExtensionRunner, ModelRegistry, ModelRuntime, SessionManager } from "@earendil-works/pi-coding-agent";
import { loadExtensionFromFactory } from "../../../node_modules/@earendil-works/pi-coding-agent/dist/core/extensions/loader.js";
import lazyHarnessPi from "../extensions/lazy-harness/index.ts";
import { fabricReaderPrompt } from "../extensions/lazy-harness/fabric-reader.ts";

const host = resolve(import.meta.dir, "../../..");

test("real SDK replaces Parent context/skills and enforces the dedicated Reader turn policy without network", async () => {
  const temp = mkdtempSync(join(tmpdir(), "reader-sdk-policy-"));
  const root = join(temp, "host");
  const previous = process.env.PI_FABRIC_LINEAGE;
  const runId = "sdk-reader-contract";
  const ledgers: any[] = [];
  const errors: any[] = [];
  let aborted = 0;
  try {
    execFileSync("git", ["clone", "--quiet", "--shared", "--no-checkout", host, root]);
    mkdirSync(join(root, ".lazy-harness/bin"), { recursive: true });
    writeFileSync(join(root, ".lazy-harness/bin/lazy"), "#!/bin/sh\n");
    const revision = execFileSync("git", ["rev-parse", "HEAD"], { cwd: root, encoding: "utf8" }).trim();
    process.env.PI_FABRIC_LINEAGE = JSON.stringify({ version: 1, worker: true, runId });
    const runtime = createExtensionRuntime();
    const extension = await loadExtensionFromFactory(lazyHarnessPi, root, createEventBus(), runtime);
    const models = await ModelRuntime.create({ authPath: join(temp, "auth.json"), modelsPath: null, modelsStorePath: join(temp, "models.json"), refreshOnCreate: false, allowModelNetwork: false });
    const session = SessionManager.inMemory(root);
    const runner = new ExtensionRunner([extension], runtime, root, session, new ModelRegistry(models));
    runner.onError(error => errors.push(error));
    runner.bindCore({
      sendMessage() {}, sendUserMessage() {},
      appendEntry(kind: string, data: unknown) { if (kind === "lazy-harness-reader-ledger-v1") ledgers.push(structuredClone(data)); },
      setSessionName() {}, getSessionName: () => undefined, setLabel() {},
      getActiveTools: () => ["read", "grep", "bash", "fabric_exec"], getAllTools: () => [], setActiveTools() {}, refreshTools: async () => {}, getCommands: () => [],
      setModel: async () => false, getThinkingLevel: () => "low", setThinkingLevel() {},
    } as any, {
      getModel: () => ({ provider: "fixture", id: "reader" }), getScopedModels: () => [],
      isIdle: () => false, isProjectTrusted: () => true, getSignal: () => undefined,
      abort: () => { aborted += 1; }, hasPendingMessages: () => false, shutdown() {},
      getContextUsage: () => undefined, compact() {}, getSystemPrompt: () => "PARENT_SYSTEM_SECRET",
    } as any);
    const task = `root: ${root}\nrevision: ${revision}\nmodel: fixture/reader:low\nevidenceEpoch: 1\nmaxReadCalls: 2\nmaxRequestedLines: 400\nmaxLinesPerRead: 200\ntask: inspect canonical records`;
    const result = await runner.emitBeforeAgentStart(task, undefined, `PARENT_SYSTEM_SECRET\n${fabricReaderPrompt()}`, {
      cwd: root, contextFiles: [{ path: "AGENTS.md", content: "PARENT_PROJECT_SECRET" }],
      skills: [{ name: "parent-skill", description: "PARENT_SKILL_SECRET" } as any],
      appendSystemPrompt: "PARENT_APPEND_SECRET",
    });
    expect(result?.systemPrompt).toContain(fabricReaderPrompt());
    expect(result?.systemPrompt).not.toContain("PARENT_");
    expect(ledgers.at(-1).readerPolicy).toMatchObject({ inheritProjectContext: false, inheritSkills: false, context: "fresh", systemPromptMode: "replace", maxTurns: 12, graceTurns: 2 });
    for (let turn = 1; turn <= 14; turn++) {
      await runner.emitMessageEnd({ type: "message_end", message: {
        role: "assistant", content: turn === 14 ? [{ type: "toolCall", id: "last-call", name: "read", arguments: {} }] : [{ type: "text", text: "continue" }],
        api: "openai-responses", provider: "fixture", model: "reader", usage: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, totalTokens: 0, cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, total: 0 } }, stopReason: turn === 14 ? "toolUse" : "stop", timestamp: turn,
      } as any });
      if (turn === 12) {
        const context = await runner.emitContext([]);
        expect(JSON.stringify(context)).toContain("Reader turn budget reached");
      }
    }
    expect(aborted).toBe(1);
    expect(ledgers.at(-1).readerPolicy).toMatchObject({ turnCount: 14, wrapUpRequested: true, turnBudgetExceeded: true });
    const denied = await runner.emitToolCall({ type: "tool_call", toolName: "read", toolCallId: "after-hard-limit", input: { path: ".lazy-harness/spec/fact.md", offset: 1, limit: 1 } });
    expect(denied?.block).toBe(true);
    expect(errors).toEqual([]);
  } finally {
    if (previous === undefined) delete process.env.PI_FABRIC_LINEAGE; else process.env.PI_FABRIC_LINEAGE = previous;
    rmSync(temp, { recursive: true, force: true });
  }
});
