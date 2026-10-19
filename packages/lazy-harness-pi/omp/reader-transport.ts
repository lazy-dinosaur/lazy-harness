import { lstatSync, readFileSync } from "node:fs";
import { isAbsolute, join } from "node:path";
import type { ReaderDelivery, ReaderLaunchIdentity, ReaderTransport } from "../extensions/lazy-harness/reader-transport.ts";
import { OMP_READER_CONTEXT, OMP_READER_NAME, ompReaderDefinition } from "./reader-definition.ts";
import { ompSessionHeader } from "./session-header.ts";

type Binding = { runId?: string; sessionFile?: string; terminal?: boolean; error?: string };
const CHANNEL = "task:subagent:lifecycle";

/** OMP single blocking task transport (16/18 wire shapes). Lifecycle is identity, not delivery. */
export class OmpReaderTransport implements ReaderTransport {
  private bindings = new Map<string, Binding>();
  private reads = new Map<string, { start: number; end: number }>();
  private unsubscribe?: () => void;
  constructor(private api: any) {
    if (typeof api.events?.on === "function") this.unsubscribe = api.events.on(CHANNEL, (event: any) => {
      const binding = this.bindings.get(event?.parentToolCallId);
      if (!binding) return;
      if (event.agent !== OMP_READER_NAME || event.index !== 0 || event.detached === true
        || typeof event.id !== "string" || !event.id || typeof event.sessionFile !== "string" || !isAbsolute(event.sessionFile)) {
        binding.error = "invalid native Reader lifecycle identity";
        return;
      }
      if (event.status === "started") {
        if (binding.runId) { binding.error = "duplicate native Reader start"; return; }
        binding.runId = event.id;
        binding.sessionFile = event.sessionFile;
      } else if (event.id !== binding.runId || event.sessionFile !== binding.sessionFile || binding.terminal) {
        binding.error = "conflicting native Reader terminal identity";
      } else if (event.status !== "completed") {
        binding.error = "native Reader failed or aborted";
      } else binding.terminal = true;
    });
  }
  guidance(root: string): string {
    try {
      const text = readFileSync(join(root, ".omp/agents", `${OMP_READER_NAME}.md`), "utf8");
      const encoded = text.match(/^model: ("[^\n]+")$/m)?.[1];
      const model = encoded ? JSON.parse(encoded) : undefined;
      this.prepare(root, "task", { agent: OMP_READER_NAME, assignment: `model: ${model}` });
      return `OMP native Reader is registered for ${model} (low). Use task with context:${JSON.stringify(OMP_READER_CONTEXT)} and exactly one tasks item containing the exact root/revision/model/evidenceEpoch/budget/task envelope. Follow the exposed native schema: on OMP 18 put agent:'${OMP_READER_NAME}' and task:<envelope> in that item; on older OMP use top-level agent:'${OMP_READER_NAME}' and item assignment:<envelope>. Never supply both instruction fields or conflicting agent selectors. Flat task/assignment is also accepted when the runtime exposes that schema. This transport is blocking/fresh; do not pass Pi flags, role/isolation overrides, other shared context or multiple tasks. After visible result content, call lazy_reader_join with the current revision/epoch and actual marker. Lifecycle status alone is not content. Native task may persist runtime session/result artifacts; this is not Pi artifacts:false or async parity.`;
    } catch {
      return "OMP native Reader is unavailable or its project definition differs. Use bounded direct map/read fallback; do not claim Reader parity or invent Pi launch flags.";
    }
  }
  prepare(root: string, name: string, args: Record<string, unknown>): ReaderLaunchIdentity | undefined {
    const batch = Array.isArray(args.tasks) ? args.tasks : [];
    const namesReader = args.agent === OMP_READER_NAME || batch.some(item => item && typeof item === "object" && item.agent === OMP_READER_NAME);
    if (name !== "task" || !namesReader) return undefined;
    if (args.agent !== undefined && args.agent !== OMP_READER_NAME) throw new Error("Reader agent selectors conflict");
    if (typeof this.api.events?.on !== "function") throw new Error("native Reader lifecycle channel unavailable");
    let item: Record<string, unknown> = args;
    if (Array.isArray(args.tasks)) {
      const candidate = args.tasks.length === 1 ? args.tasks[0] : undefined;
      if (args.context !== OMP_READER_CONTEXT || Object.keys(args).some(key => !["agent", "context", "tasks"].includes(key))
        || !candidate || typeof candidate !== "object" || Array.isArray(candidate)
        || Object.keys(candidate).some(key => !["id", "name", "description", "agent", "assignment", "task"].includes(key))
        || (candidate.agent !== undefined && candidate.agent !== OMP_READER_NAME)
        || (Object.prototype.hasOwnProperty.call(candidate, "task") && candidate.agent !== OMP_READER_NAME)) {
        throw new Error("Reader batch transport requires exactly one task and the fixed shared context, without overrides");
      }
      item = candidate as Record<string, unknown>;
    } else if (Object.keys(args).some(key => !["agent", "assignment", "task", "id", "description"].includes(key))) {
      throw new Error("Reader requires one task without role/context/isolation overrides");
    }
    const hasAssignment = Object.prototype.hasOwnProperty.call(item, "assignment");
    const hasTask = Object.prototype.hasOwnProperty.call(item, "task");
    if (hasAssignment === hasTask) throw new Error("Reader requires exactly one instruction field: task or assignment");
    const assignment = hasTask ? item.task : item.assignment;
    if (typeof assignment !== "string") throw new Error("Reader assignment missing");
    const models = [...assignment.matchAll(/^model:[ \t]*(.+)$/gm)];
    if (models.length !== 1) throw new Error("Reader assignment requires one explicit model field");
    const model = models[0][1].trim();
    const path = join(root, ".omp/agents", `${OMP_READER_NAME}.md`);
    for (const dir of [join(root, ".omp"), join(root, ".omp/agents")]) {
      if (!lstatSync(dir).isDirectory()) throw new Error("Reader directory must not be a symlink");
    }
    if (!lstatSync(path).isFile() || readFileSync(path, "utf8") !== ompReaderDefinition(model)) {
      throw new Error("project Reader definition does not match the package contract/model; activate and restart OMP");
    }
    return { agent: OMP_READER_NAME, task: assignment, model };
  }
  admit(toolCallId: string): void {
    if (!toolCallId || this.bindings.has(toolCallId)) throw new Error("native Reader call identity missing or reused");
    this.bindings.set(toolCallId, {});
  }
  receive(event: any): ReaderDelivery {
    const binding = this.bindings.get(event.toolCallId);
    if (!binding || binding.error || !binding.terminal || !binding.runId || !binding.sessionFile) {
      throw new Error(binding?.error || "native Reader lacks bound terminal lifecycle/session evidence");
    }
    const results = event.details?.results;
    const result = Array.isArray(results) && results.length === 1 ? results[0] : undefined;
    if (event.isError || event.is_error || !result || result.id !== binding.runId || result.agent !== OMP_READER_NAME
      || result.exitCode !== 0 || result.error || result.aborted || result.truncated) {
      throw new Error("native Reader result lacks one successful untruncated owned result");
    }
    const text = Array.isArray(event.content) ? event.content.filter((part: any) => part?.type === "text" && typeof part.text === "string").map((part: any) => part.text).join("\n") : "";
    // Never use details.output, outputPath, or a transcript as Parent content.
    const outputs = [...text.matchAll(/<output>\n([\s\S]*?)\n<\/output>/g)];
    if (outputs.length !== 1) throw new Error("native Reader requires one visible yielded output");
    let yielded: Record<string, unknown>;
    try { yielded = JSON.parse(outputs[0][1]); }
    catch { throw new Error("native Reader visible output is malformed JSON"); }
    if (!yielded || typeof yielded !== "object" || Object.keys(yielded).join() !== "packet" || typeof yielded.packet !== "string") {
      throw new Error("native Reader visible output is not a packet envelope");
    }
    return { runId: binding.runId, sessionFile: binding.sessionFile, text: yielded.packet };
  }
  sessionHeader(entries: unknown[]): { type: "session"; id: string } | undefined {
    return ompSessionHeader(entries);
  }
  isTerminalCall(name: string, args: Record<string, unknown>): boolean {
    if (name !== "yield") return false;
    const key = Object.keys(args).join();
    const result = (key === "result" ? args.result : key === "data" ? args : undefined) as Record<string, unknown> | undefined;
    const data = result?.data as Record<string, unknown> | undefined;
    return Boolean(result && Object.keys(result).join() === "data" && data && Object.keys(data).join() === "packet" && typeof data.packet === "string");
  }
  normalizeRead(toolCallId: string, args: Record<string, unknown>): Record<string, unknown> {
    // OMP 16.2.2's real read schema is path-only. Legacy limit is ignored.
    // Explicit raw N-M selections add one leading and three trailing lines.
    const match = typeof args.path === "string" ? args.path.match(/^(\.lazy-harness\/[A-Za-z0-9_./-]+\.(?:md|xml|json)):raw:([1-9]\d*)-([1-9]\d*)$/) : undefined;
    if (!match || Object.keys(args).some(key => key !== "path")) throw new Error("native Reader read requires path '.lazy-harness/...:raw:N-M'; legacy offset/limit and open/multiple ranges are forbidden");
    const start = Number(match[2]); const end = Number(match[3]);
    if (!Number.isSafeInteger(start) || !Number.isSafeInteger(end) || end < start || end > Number.MAX_SAFE_INTEGER - 3) throw new Error("invalid native Reader line range");
    const expandedStart = start > 1 ? start - 1 : start;
    const expandedEnd = end + 3;
    this.reads.set(toolCallId, { start: expandedStart, end: expandedEnd });
    return { path: match[1], offset: expandedStart, limit: expandedEnd - expandedStart + 1 };
  }
  readResultError(event: any): string | undefined {
    if (event.toolName !== "read") return undefined;
    const range = this.reads.get(String(event.toolCallId || ""));
    this.reads.delete(String(event.toolCallId || ""));
    if (event.isError || event.is_error) return undefined;
    const lines = event.details?.displayContent?.lineNumbers;
    if (!range || !Array.isArray(lines) || lines.length === 0
      || lines.some((line: unknown, index: number) => !Number.isInteger(line) || Number(line) < range.start || Number(line) > range.end || (index > 0 && Number(line) <= lines[index - 1]))
      || lines.length > range.end - range.start + 1) return "native Reader returned unverifiable or out-of-budget line coverage";
    return undefined;
  }
  childModelMatches(task: string, context: any): boolean {
    const requested = task.match(/^model:[ \t]*(.+)$/m)?.[1]?.trim();
    return Boolean(requested && requested === `${context.model?.provider}/${context.model?.id}` && this.api.getThinkingLevel?.() === "low");
  }
  dispose(): void { this.unsubscribe?.(); this.bindings.clear(); this.reads.clear(); }
}
