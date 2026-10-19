import { appendFileSync } from "node:fs";
import harness from "../../omp/index.ts";
import { nativeFixtureStream } from "./omp-native-stream.ts";

// Scripted provider only. Events, tools, guards, and output are the real OMP runtime.
export default function offlineOmp(api: any) {
  const log = (data: unknown) => appendFileSync(process.env.LAZY_OMP_PROBE_LOG!, JSON.stringify(data) + "\n");
  harness(api);
  api.on("before_agent_start", (_event: unknown, ctx: any) => log({ event: "start", mode: ctx.mode ?? null }));
  let calls = 0;
  api.registerProvider("offline-omp-probe", {
    api: "offline-omp-probe-api", apiKey: "offline-placeholder", baseUrl: "http://invalid.invalid",
    models: [{ id: "scripted", name: "Offline OMP", reasoning: false, input: ["text"], cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 }, contextWindow: 100000, maxTokens: 2000 }],
    streamSimple(model: any, context: any) {
      const turn = calls++;
      log({ event: "model", turn, messages: context.messages });
      const content: any[] = turn === 0
        ? [{ type: "toolCall", id: "unguarded-write", name: "write", arguments: { path: "must-not-exist.txt", content: "unguarded" } }]
        : [{ type: "text", text: turn === 1 ? "OMP_OFFLINE_PRIMARY_ANSWER" : "OMP_OFFLINE_ADVISORY_ONLY" }];
      const stopReason = turn === 0 ? "toolUse" : "stop";
      const message: any = { role: "assistant", content, api: model.api, provider: model.provider, model: model.id, usage: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, totalTokens: 0, cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, total: 0 } }, stopReason, timestamp: Date.now() };
      return nativeFixtureStream(message);
    },
  });
}
