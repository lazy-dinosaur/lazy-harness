import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { createAssistantMessageEventStream } from "@earendil-works/pi-ai";
import { appendFileSync, existsSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

// This file is copied into the isolated agent configuration. No runtime methods,
// tool implementations, event handlers, notifications, or ledgers are replaced.
export default function offlineProvider(pi: ExtensionAPI) {
  const root = process.env.NATIVE_READER_ROOT!;
  const trace = process.env.NATIVE_READER_TRACE!;
  const revision = process.env.NATIVE_READER_REVISION!;
  const scenario = process.env.NATIVE_READER_SCENARIO ?? "complete";
  const advisory = process.env.NATIVE_READER_ADVISORY;
  const primaryAnswer = advisory === "capture"
    ? "Substantive answer: delivery matters. Analysis across SDD, BDD and TDD.\nCLAIM-1: the host owns runtime-root resolution.\nCLAIM-2: native Reader content must reach Parent before joining.\nCLAIM-3: all successful ledger hashes remain protected.\nCLAIM-4: a 30-day archival guarantee is absent."
    : "Substantive answer: delivery matters. The project-specific ownership rule must be stored in .lazy-harness.\nCLAIM-1: the host owns runtime-root resolution.\nCLAIM-2: native Reader content must reach Parent before joining.\nCLAIM-3: all successful ledger hashes remain protected.\nCLAIM-4: a 30-day archival guarantee is absent.";
  const gate = join(root, "parent-independent-ended");
  const log = (event: string, data: Record<string, unknown> = {}) => appendFileSync(trace, `${JSON.stringify({ event, at: Date.now(), pid: process.pid, ...data })}\n`);
  let reader = false;
  let calls = 0;
  pi.on("before_agent_start", (event, ctx) => {
    reader = event.systemPrompt.includes("LAZY_HARNESS_ROLE: record-reader/reader-join-v1");
    log(reader ? "reader-start" : "parent-start", { sessionFile: ctx.sessionManager.getSessionFile(), ...(reader ? { prompt: event.prompt } : {}) });
  });
  pi.on("agent_end", (event, ctx) => {
    const last = JSON.stringify(event.messages.at(-1));
    const asyncRoot = join(process.env.PI_SUBAGENTS_TEMP_ROOT!, "async-subagent-runs");
    const statuses = !reader && existsSync(asyncRoot) ? readdirSync(asyncRoot).filter((name) => !name.startsWith(".")).map((name) => {
      const path = join(asyncRoot, name, "status.json");
      return existsSync(path) ? JSON.parse(readFileSync(path, "utf8")) : null;
    }) : [];
    const index = join(asyncRoot, ".active-runs");
    log(reader ? "reader-agent-end" : "parent-agent-end", { last, hasUI: ctx.hasUI, sessionFile: ctx.sessionManager.getSessionFile(), statuses, activeIndex: existsSync(index) ? readdirSync(index) : [] });
    // Registered ahead of the actual native drain. Merely release the scripted
    // model: the native handler must still wait for and deliver the real child.
    if (!reader && last.includes("Independent source inspection finished.")) writeFileSync(gate, "ended");
  });
  pi.on("tool_result", (event) => { log(reader ? "reader-tool-result" : "parent-tool-result", { result: event }); });
  pi.on("context", (event) => {
    if (!reader) for (const message of event.messages) {
      if (message.role === "custom" && message.customType === "subagent-notify") log("parent-notification", { message });
    }
  });
  pi.registerProvider("offline-native-reader", {
    api: "offline-native-reader-api",
    apiKey: "offline-placeholder-not-a-credential",
    baseUrl: "http://invalid.invalid",
    models: [{ id: "scripted", name: "Offline native Reader script", reasoning: false, input: ["text"], cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 }, contextWindow: 100000, maxTokens: 2000 }],
    streamSimple(model, context) {
      const stream = createAssistantMessageEventStream();
      void (async () => {
        const isReader = context.systemPrompt?.includes("LAZY_HARNESS_ROLE: record-reader/reader-join-v1");
        const turn = calls++;
        log(isReader ? "reader-model" : "parent-model", { turn });
        const tool = (name: string, args: Record<string, unknown>) => [{ type: "toolCall", id: `${isReader ? "reader" : "parent"}-${turn}`, name, arguments: args }];
        const text = (value: string) => [{ type: "text", text: value }];
        let content: any[];
        if (isReader) {
          const commands = [".lazy-harness/bin/lazy map --overview --complete --format=md", "pwd", "git rev-parse --show-toplevel", "git rev-parse HEAD", ".lazy-harness/bin/lazy map native-fact --format=md --limit=8"];
          if (turn < commands.length) content = tool("bash", { command: commands[turn], timeout: 120 });
          else if (turn === commands.length) content = tool("read", { path: ".lazy-harness/spec/fact.md", limit: 200 });
          else if (turn === commands.length + 1) content = tool("read", { path: `.lazy-harness/spec/${scenario === "failed-read" ? "missing" : "second"}.md`, limit: 200 });
          else {
            if (turn !== 7) throw new Error("Unexpected Reader continuation");
            const read = context.messages.find((message: any) => message.role === "toolResult" && message.toolName === "read") as any;
            if (!read || read.isError || !JSON.stringify(read.content).includes("canonical fact: delivery matters")) throw new Error(`Real Reader read failed: ${JSON.stringify(context.messages.filter((message) => message.role === "toolResult"))}`);
            const deadline = Date.now() + 15000;
            while (process.env.NATIVE_READER_ARM !== "A" && !existsSync(gate)) {
              if (Date.now() > deadline) throw new Error("Parent independent agent_end never arrived");
              await new Promise((resolve) => setTimeout(resolve, 25));
            }
            await new Promise((resolve) => setTimeout(resolve, 300));
            log("reader-delayed-completion");
            content = text(`LAZY_HARNESS_READER_RESULT: complete\nroot: \`${root}\`\nrevision: \`${revision}\`\nevidenceEpoch: \`1\`\nbudget: readCalls: 0 (deliberately untrusted self-report)\nrecordsRead: .lazy-harness/spec/fact.md lines 1-1\napplicablePolicies: native completion delivery\nfacts: canonical fact: delivery matters\nconflicts: none\nmissing: none\nparentFollowUp: join before answering`);
          }
        } else if (turn === 0) {
          content = tool("subagent", { agent: "lazy-harness.record-reader", model: "offline-native-reader/scripted", cwd: root, async: process.env.NATIVE_READER_ARM !== "A", context: "fresh", acceptance: false, artifacts: false, output: false, agentContract: { version: 1 }, task: `root: ${root}\nrevision: ${revision}\nmodel: offline-native-reader/scripted\nevidenceEpoch: 1\nmaxReadCalls: 6\nmaxRequestedLines: 1200\nmaxLinesPerRead: 200\ntask: inspect the canonical delivery rule` });
        } else if (turn === 1) {
          content = tool("read", { path: "source.txt", limit: 10 });
        } else if (turn === 2 && process.env.NATIVE_READER_ARM !== "A") {
          content = text("Independent source inspection finished.");
        } else if (turn === (process.env.NATIVE_READER_ARM === "A" ? 2 : 3)) {
          if (!JSON.stringify(context.messages).includes("facts: canonical fact: delivery matters")) throw new Error("Native handler resumed Parent without Reader content");
          if (scenario === "changed-hash") writeFileSync(join(root, ".lazy-harness/spec/second.md"), "changed after real Reader completion\n");
          content = tool("lazy_reader_join", { status: "complete", resultMarker: "LAZY_HARNESS_READER_RESULT: complete", revision, evidenceEpoch: scenario === "stale-epoch" ? 0 : 1,
            recordPaths: [scenario === "unread-path" ? ".lazy-harness/spec/unread.md" : ".lazy-harness/spec/fact.md"],
            ...(scenario === "wrong-run-id" ? { runId: "forged-run-id" } : {}),
            ...(scenario === "false-counter" ? { readCalls: 0 } : {}) });
        } else if (turn === (process.env.NATIVE_READER_ARM === "A" ? 3 : 4)) {
          const joined = context.messages.find((message: any) => message.role === "toolResult" && message.toolName === "lazy_reader_join") as any;
          if (!joined || Boolean(joined.isError) !== (scenario !== "complete")) throw new Error(`Unexpected native Parent join outcome: ${JSON.stringify(joined)}`);
          content = text(scenario === "complete" ? primaryAnswer : "Rejected unsafe Reader join; bounded Parent fallback is required.");
        } else {
          // The pre-repair production hook would request this partial replacement.
          // Make that failure visible at the real CLI endpoint, not a send-count stub.
          log("unwanted-advisory-continuation");
          content = text("Partial replacement: only a capture/placement candidate remains.");
        }
        const stopReason = content[0].type === "toolCall" ? "toolUse" : "stop";
        const message: any = { role: "assistant", content, api: model.api, provider: model.provider, model: model.id, usage: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, totalTokens: 0, cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, total: 0 } }, stopReason, timestamp: Date.now() };
        stream.push({ type: "done", reason: stopReason, message });
        stream.end();
      })().catch((error) => {
        log("script-error", { error: String(error) });
        const message: any = { role: "assistant", content: [], api: model.api, provider: model.provider, model: model.id, usage: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, totalTokens: 0, cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, total: 0 } }, stopReason: "error", errorMessage: String(error), timestamp: Date.now() };
        stream.push({ type: "error", reason: "error", error: message });
        stream.end();
      });
      return stream;
    },
  });
}
