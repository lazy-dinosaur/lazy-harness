import { appendFileSync } from "node:fs";
import harness from "../../omp/index.ts";
import { OMP_READER_CONTEXT } from "../../omp/reader-definition.ts";
import { nativeFixtureStream } from "./omp-native-stream.ts";

// No external model traffic. Real native task/discovery/session/tools/ledger/join.
export default function fixture(api: any) {
  api.on("tool_call", (event: any) => appendFileSync(process.env.LAZY_OMP_PROBE_LOG!, JSON.stringify({ event: "tool_call", toolName: event.toolName, input: event.input }) + "\n"));
  for (const eventName of ["before_agent_start", "input", "message_start"]) api.on(eventName, (event: any, ctx: any) => {
    if (eventName === "message_start" && event.message?.role !== "user") return;
    appendFileSync(process.env.LAZY_OMP_PROBE_LOG!, JSON.stringify({ event: eventName, sessionId: ctx.sessionManager.getSessionId(), prompt: event.prompt, text: event.text, source: event.source, streamingBehavior: event.streamingBehavior, steering: event.message?.steering }) + "\n");
  });
  harness(api);
  api.registerProvider("offline-omp-reader", {
    api: "offline-omp-reader-api", apiKey: "offline-placeholder", baseUrl: "http://invalid.invalid",
    models: ["parent", "reader"].map(id => ({ id, name: id, reasoning: true, input: ["text"], cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 }, contextWindow: 100000, maxTokens: 2000 })),
    streamSimple(model: any, context: any) {
      const root = process.env.LAZY_OMP_READER_ROOT!;
      const revision = process.env.LAZY_OMP_READER_REVISION!;
      const readCase = process.env.LAZY_OMP_READER_CASE || "bounded";
      const turn = context.messages.filter((message: any) => message.role === "assistant").length;
      const taskText = context.messages.filter((m: any) => m.role === "user").map((m: any) => typeof m.content === "string" ? m.content : m.content.filter((p: any) => p.type === "text").map((p: any) => p.text).join("\n")).join("\n");
      const childEpoch = taskText.match(/^evidenceEpoch: ([0-9]+)$/m)?.[1] || "1";
      const envelope = `root: ${root}\nrevision: ${revision}\nmodel: offline-omp-reader/reader\nevidenceEpoch: 1\nmaxReadCalls: 2\nmaxRequestedLines: 100\nmaxLinesPerRead: 50\ntask: Inspect the package contract`;
      const tool = (name: string, args: any) => {
        if (name === "task") {
          const schema = JSON.stringify(context.tools?.find((t: any) => t.name === "task")?.parameters ?? {});
          const field = schema.includes('"assignment":') ? "assignment" : schema.includes('"task":') ? "task" : undefined;
          if (!field) throw new Error("Native task instruction schema is unavailable");
          args = { ...args, tasks: args.tasks.map(({ assignment, ...rest }: any) => ({ ...rest, ...(field === "task" ? { agent: "lazy-harness.record-reader" } : {}), [field]: assignment })) };
          if (field === "task") delete args.agent;
        }
        if (name === "yield") {
          const schema = JSON.stringify(context.tools?.find((t: any) => t.name === "yield")?.parameters ?? {});
          if (!schema.includes('"result":')) {
            if (!schema.includes('"data":')) throw new Error("Native yield data schema is unavailable");
            args = args.result;
          }
        }
        return { type: "toolCall", id: `${model.id}-${turn}`, name, arguments: args };
      };
      const text = (value: string) => ({ type: "text", text: value });
      const steps = model.id === "reader" ? [
        tool("bash", { command: ".lazy-harness/bin/lazy map --overview --complete --format=md" }),
        tool("bash", { command: "pwd" }),
        tool("bash", { command: "git rev-parse --show-toplevel" }),
        tool("bash", { command: "git rev-parse HEAD" }),
        tool("bash", { command: ".lazy-harness/bin/lazy map .lazy-harness/spec/platform/pi-agent-package.md --format=md --limit=8" }),
        tool("read", readCase === "legacy-limit" ? { path: ".lazy-harness/spec/platform/pi-agent-package.md", limit: 50 } : { path: `.lazy-harness/spec/platform/pi-agent-package.md:raw:1-${readCase === "over-cap" ? 50 : 47}` }),
        tool("yield", { result: { data: { packet: `LAZY_HARNESS_READER_RESULT: complete\nroot: ${root}\nrevision: ${revision}\nevidenceEpoch: ${childEpoch}\nrecordsRead: .lazy-harness/spec/platform/pi-agent-package.md lines 1-50` } } }),
        text("Reader result submitted."),
      ] : process.env.LAZY_OMP_QUEUE_MODE === "ask" ? [
        tool("ask", { questions: [{ id: "native-choice", question: "Continue this isolated native test?", options: [{ label: "Continue" }, { label: "Stop" }] }] }),
        tool("task", { agent: "lazy-harness.record-reader", context: OMP_READER_CONTEXT, tasks: [{ assignment: envelope }] }),
        tool("lazy_reader_join", { revision, evidenceEpoch: 1, status: "complete", resultMarker: "LAZY_HARNESS_READER_RESULT: complete" }),
        tool("write", { path: "native-ask-approved.txt", content: "native ask answered" }),
        text("OMP_NATIVE_ASK_COMPLETE"),
      ] : process.env.LAZY_OMP_QUEUE_MODE === "new_session" && taskText.includes("SECOND_SESSION_BOUNDARY_PROBE") ? [
        tool("write", { path: "native-stale-session.txt", content: "must not inherit grounding" }),
        tool("task", { agent: "lazy-harness.record-reader", context: OMP_READER_CONTEXT, tasks: [{ assignment: envelope.replace("evidenceEpoch: 1", "evidenceEpoch: 3") }] }),
        tool("lazy_reader_join", { revision, evidenceEpoch: 3, status: "complete", resultMarker: "LAZY_HARNESS_READER_RESULT: complete" }),
        tool("write", { path: "native-session-recovered.txt", content: "fresh session grounded" }),
        text("OMP_NATIVE_SESSION_RECOVERED"),
      ] : process.env.LAZY_OMP_STEER_PROBE === "1" && process.env.LAZY_OMP_QUEUE_MODE !== "follow_up" ? [
        tool("task", { agent: "lazy-harness.record-reader", context: OMP_READER_CONTEXT, tasks: [{ assignment: envelope }] }),
        tool("lazy_reader_join", { revision, evidenceEpoch: 1, status: "complete", resultMarker: "LAZY_HARNESS_READER_RESULT: complete" }),
        tool("write", { path: "native-joined.txt", content: "must be blocked after steer" }),
        tool("task", { agent: "lazy-harness.record-reader", context: OMP_READER_CONTEXT, tasks: [{ assignment: envelope.replace("evidenceEpoch: 1", "evidenceEpoch: 2") }] }),
        tool("lazy_reader_join", { revision, evidenceEpoch: 2, status: "complete", resultMarker: "LAZY_HARNESS_READER_RESULT: complete" }),
        tool("write", { path: "native-recovered.txt", content: "fresh epoch joined" }),
        text("OMP_NATIVE_STEER_RECOVERED"),
      ] : [
        tool("task", { agent: "lazy-harness.record-reader", context: OMP_READER_CONTEXT, tasks: [{ assignment: envelope }] }),
        tool("lazy_reader_join", { revision, evidenceEpoch: 1, status: "complete", resultMarker: "LAZY_HARNESS_READER_RESULT: complete" }),
        tool("write", { path: "native-joined.txt", content: "native Reader joined" }),
        text(readCase === "bounded" ? "OMP_NATIVE_READER_JOINED" : "OMP_NATIVE_READER_REJECTED"),
        ...(process.env.LAZY_OMP_QUEUE_MODE === "follow_up" ? [
          tool("write", { path: "native-follow-up.txt", content: "reused grounding" }),
          text("OMP_NATIVE_FOLLOW_UP_REUSED"),
        ] : []),
      ];
      const askUnavailable = model.id === "parent" && process.env.LAZY_OMP_QUEUE_MODE === "ask" && context.messages.some((m: any) => m.role === "toolResult" && m.toolName === "ask" && m.isError);
      const content = [askUnavailable ? text("OMP_NATIVE_ASK_UNAVAILABLE") : steps[turn] || text("UNEXPECTED_NATIVE_READER_TURN")];
      appendFileSync(process.env.LAZY_OMP_PROBE_LOG!, JSON.stringify({ model: model.id, turn, messages: context.messages, output: content }) + "\n");
      let released: Promise<void> = Promise.resolve();
      if (process.env.LAZY_OMP_STEER_PROBE === "1" && process.env.LAZY_OMP_STEER_GATE_USED !== "1" && model.id === "reader" && turn === 0) {
        process.env.LAZY_OMP_STEER_GATE_USED = "1";
        released = new Promise<void>(resolve => process.once("SIGUSR2", () => resolve()));
        console.error("OMP_STEER_READER_READY");
      }
      const stopReason = content[0].type === "toolCall" ? "toolUse" : "stop";
      const message = { role: "assistant", content, api: model.api, provider: model.provider, model: model.id, usage: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, totalTokens: 0, cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, total: 0 } }, stopReason, timestamp: Date.now() };
      return nativeFixtureStream(message, released);
    },
  });
}
