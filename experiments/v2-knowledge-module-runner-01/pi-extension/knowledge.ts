import { execFile } from "node:child_process";
import { Type } from "@earendil-works/pi-ai";
import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";

const CLI = "/home/lazydino/dev/lazy-harness.v2/experiments/v2-knowledge-module-runner-01/knowledge_cli.py";
const ENTRY = "knowledge-work-unit";
const lits = (values: string[]) => Type.Union(values.map((v) => Type.Literal(v)));
// Must match runner.py FACT_KINDS / EVIDENCE_SOURCES / EVIDENCE_REF_TYPES (and the DB check).
const ref = Type.Object({
  type: lits(["code_test", "official_doc", "user_utterance", "observed_output", "ai_inference"]),
  locator: Type.String(), quote: Type.String() });
const fact = Type.Object({
  operation: lits(["add", "update", "deprecate"]),
  kind: lits(["fact", "decision", "rationale", "rejected", "constraint", "procedure", "term", "question"]),
  subject: Type.String(), fact: Type.String(),
  evidence_source: lits(["user_confirmed", "user_tentative", "official_doc", "code_test", "observed_output", "ai_inference"]),
  reason: Type.String(), why: Type.Optional(Type.String()),
  evidence_refs: Type.Array(ref), keywords: Type.Optional(Type.Array(Type.String())),
  target_ref: Type.Optional(Type.String({ description: "update/deprecate: the fragment token exactly as shown when you read it, e.g. knowledge-module-16@2" })),
});

export default function (pi: ExtensionAPI) {
  let workUnitId: string | undefined;
  // Tool calls in a single model turn may be parallel; serialize access to this session's ID.
  let tail: Promise<unknown> = Promise.resolve();
  const serialized = <T>(fn: () => Promise<T>): Promise<T> => {
    const next = tail.then(fn, fn);
    tail = next.catch(() => undefined);
    return next;
  };
  const restore = (ctx: ExtensionContext) => {
    workUnitId = undefined;
    for (const entry of ctx.sessionManager.getBranch()) {
      if (entry.type === "custom" && entry.customType === ENTRY) {
        const data = entry.data as { work_unit_id?: string } | undefined;
        if (data?.work_unit_id) workUnitId = data.work_unit_id;
      }
    }
  };
  // Guide, not enforcement (digestion module owns it): tell the worker when human review is pending.
  // Blocking/gating the agent belongs to the behavior (rule) module.
  let announced = -1;
  const announceReview = (ctx: ExtensionContext) => {
    void invoke("review", { action: "list" }, ctx.cwd).then((result) => {
      const items = Array.isArray(result.items) ? result.items as { fact?: string; why_waiting?: string[] }[] : null;
      if (!items) return;
      const count = items.length;
      if (count > 0 && count > announced) {
        // The lookup is async: the session may already be closed (headless -p exit, window closed). Drop the
        // notice then; it is re-announced on the next session_start.
        try { pi.sendMessage({
          customType: "knowledge-review", display: true, details: { pending: count },
          content: `[knowledge-review] 사용자 확인을 기다리는 지식 ${count}개. knowledge_review 로 사용자에게 물어볼 수 있어(결정은 사용자가 한다).\n` +
            items.map((i) => `- ${i.fact ?? ""} (${(i.why_waiting ?? []).join(", ")})`).join("\n"),
        }, { deliverAs: "nextTurn" }); } catch { return; }
      }
      announced = count;
    }).catch(() => undefined);
  };
  pi.on("session_start", async (_event, ctx) => { restore(ctx); announceReview(ctx); });
  pi.on("agent_end", async (_event, ctx) => announceReview(ctx));
  pi.on("session_tree", async (_event, ctx) => restore(ctx));

  type Command = "record" | "complete" | "status" | "search" | "more" | "brief" | "fix_plan" | "fix_submit" | "audit" | "review";
  const LONG = new Set<Command>(["search", "more", "brief", "fix_plan", "fix_submit", "audit"]);
  // user/assistant text of the current branch (tool results and thinking excluded), newest last
  const transcript = (ctx: ExtensionContext, limit: number) => {
    const out: { role: string; text: string }[] = [];
    for (const entry of ctx.sessionManager.getBranch()) {
      if (entry.type !== "message") continue;
      const msg = (entry as { message?: { role?: string; content?: unknown } }).message;
      if (!msg || (msg.role !== "user" && msg.role !== "assistant")) continue;
      const parts = typeof msg.content === "string" ? [msg.content]
        : Array.isArray(msg.content) ? msg.content.filter((c: { type?: string }) => c?.type === "text").map((c: { text?: string }) => c.text ?? "") : [];
      const text = parts.join("\n").trim();
      if (text) out.push({ role: msg.role, text });
    }
    return out.slice(-limit);
  };
  const invoke = (command: Command, input: object, cwd: string): Promise<Record<string, unknown>> =>
    new Promise((resolve) => {
      const child = execFile("/usr/bin/python3", [CLI, command],
        { cwd, timeout: command === "brief" ? 420000 : LONG.has(command) ? 180000 : 15000, maxBuffer: 8 * 1024 * 1024 }, (error, stdout) => {
          try {
            resolve(JSON.parse(stdout.trim()) as Record<string, unknown>);
          } catch {
            resolve({ ok: false, error: error?.name ?? "InvalidResponse" });
          }
        });
      child.stdin?.end(JSON.stringify(input));
    });
  const output = (result: Record<string, unknown>) => ({
    content: [{ type: "text" as const, text: JSON.stringify(result) }], details: result,
  });

  pi.registerTool({
    name: "knowledge_record", label: "Knowledge record",
    description: "Register proposed judgements; resident poller reviews them. One fact = one claim; subject appears verbatim in fact. Knowledge you read is listed as [alias@revision]: to change or retire that knowledge use operation update/deprecate with target_ref = that token (add is only for knowledge that is not there yet). Records are applied as written; the only question back is a contradiction with an earlier record of this work: when the result lists contradictions, show them to the user and ask which is right, then append the fix. decision/constraint need two distinct evidence refs, decision needs why. user_confirmed requires a non-question confirmed user utterance. Quote original words verbatim; correct lint errors and retry.",
    parameters: Type.Object({ facts: Type.Array(fact), partition_key: Type.String(), host_id: Type.Optional(Type.String()) }),
    async execute(_id, params, _signal, _update, ctx) {
      return serialized(async () => {
        const result = await invoke("record", { ...params, work_unit_id: workUnitId, cwd: ctx.cwd, check_contradictions: true }, ctx.cwd);
        if (typeof result.work_unit_id === "string" && !workUnitId) {
          workUnitId = result.work_unit_id;
          pi.appendEntry(ENTRY, { work_unit_id: workUnitId });
        }
        return output(result);
      });
    },
  });
  pi.registerTool({
    name: "knowledge_review", label: "Knowledge review",
    description: "Handle recorded facts that the checker could not decide (fact level; other facts of the same record are digested normally). action=list returns items {entry_id, fact_index, fact, why_waiting}. Show each item to the user in plain words with why it waits and ask: approve (absorb as user-confirmed), revise, or reject. Then call action=resolve with entry_id, fact_index, decision approve|reject and user_quote = the user's non-question answer verbatim. For revise: resolve with reject, then knowledge_record the corrected fact. Never decide for the user. Items of kind contradiction are canonical facts that contradict each other after digestion: show both, ask which is right, write the fix as a normal record (update/deprecate the wrong one), then resolve the item with the user's answer.",
    parameters: Type.Object({ action: Type.Union([Type.Literal("list"), Type.Literal("resolve")]),
      entry_id: Type.Optional(Type.String()), fact_index: Type.Optional(Type.Number()),
      decision: Type.Optional(Type.Union([Type.Literal("approve"), Type.Literal("reject")])),
      user_quote: Type.Optional(Type.String()), locator: Type.Optional(Type.String()), host_id: Type.Optional(Type.String()) }),
    async execute(_id, params, _signal, _update, ctx) {
      return serialized(async () => output(await invoke("review", params, ctx.cwd)));
    },
  });
  pi.registerTool({
    name: "knowledge_complete", label: "Knowledge complete",
    description: "Signal completion only after the user explicitly confirms this work unit. user_quote must quote that non-question confirmation verbatim; poller handles absorption.",
    parameters: Type.Object({ user_quote: Type.String(), locator: Type.Optional(Type.String()) }),
    async execute(_id, params, _signal, _update, ctx) {
      return serialized(async () => output(workUnitId
        ? await invoke("complete", { ...params, work_unit_id: workUnitId }, ctx.cwd)
        : { ok: false, error: "NoWorkUnit" }));
    },
  });
  pi.registerTool({
    name: "knowledge_search", label: "Knowledge search",
    description: "Get the project knowledge you need for your task — nothing missing, nothing more. Call it before changing something and whenever you need knowledge while working (and when the user asks to see it). question = what you are about to work on and what you need; queries = 3-6 queries you wrote in the language the stored knowledge uses (this project: Korean), keeping original identifiers; the question is also searched. Returns only the relevant fragments in four views — prior decisions/reasons, current implementation, what must be kept, other — each line '[alias] text'. Pass change (one line describing your planned change) to get fragments it would conflict with marked '⚠ 충돌 후보'. The '더 있음' index lists how many more fragments the touched domains/groups hold; fetch them with knowledge_more when your need grows — and when you are about to change something or write a layer note, fetch the rest of the topic domain(s) with knowledge_more so nothing is missed. For a layer view (DDD/SDD/BDD/TDD/ADR/SSOT) pass layer=domain|spec|behavior|tests|decisions|ssot and follow the guide at the end; write that note in your reply, never as a file.",
    parameters: Type.Object({ question: Type.String(), queries: Type.Array(Type.String()), host_id: Type.Optional(Type.String()),
      layer: Type.Optional(Type.Union(["domain", "spec", "behavior", "tests", "decisions", "ssot"].map((l) => Type.Literal(l)))),
      change: Type.Optional(Type.String()) }),
    async execute(_id, params, _signal, _update, ctx) {
      return serialized(async () => output(await invoke("search", params, ctx.cwd)));
    },
  });
  let briefSeq = 0;
  pi.registerTool({
    name: "knowledge_brief", label: "Knowledge brief",
    description: "Start this before you change something (and at the start of a work unit). Runs in the background: a cheap sub-agent reads a wide collection of the project knowledge about your target and returns only a brief in four views — prior decisions/reasons, current implementation, what must be kept, conflict candidates — each line with its [alias]. The call returns immediately with a brief_id; keep reading the source code meanwhile. The brief arrives later as a 'knowledge-brief' message. question = what you are about to do and on what; queries = 3-6 queries in the language the stored knowledge uses (this project: Korean), keeping original identifiers; change = one line describing your planned change (optional, marks conflicts). Knowledge is the intent, code is the reality: compare both and ask the user when they disagree.",
    parameters: Type.Object({ question: Type.String(), queries: Type.Array(Type.String()), change: Type.Optional(Type.String()), host_id: Type.Optional(Type.String()) }),
    async execute(_id, params, _signal, _update, ctx) {
      const briefId = `brief-${Date.now().toString(36)}-${++briefSeq}`;
      // Not serialized with the other knowledge tools: it must not block them while the sub-agent runs.
      void invoke("brief", params, ctx.cwd).then((result) => {
        const ok = typeof result.brief === "string";
        // async sub-agent: the session may already be closed; a lost brief is harmless (the worker can ask again)
        try { pi.sendMessage({
          customType: "knowledge-brief", display: true, details: { brief_id: briefId, ...result, brief: undefined },
          content: ok ? `[knowledge-brief ${briefId}] ${params.question}\n\n${result.brief as string}`
                      : `[knowledge-brief ${briefId}] failed: ${JSON.stringify(result)}`,
        }, { triggerTurn: true, deliverAs: "steer" }); } catch { /* stale session */ }
      }).catch(() => undefined);
      return output({ ok: true, brief_id: briefId, status: "started",
        notice: "The brief arrives later as a 'knowledge-brief' message. Read the relevant source code now." });
    },
  });
  pi.registerTool({
    name: "knowledge_more", label: "Knowledge more",
    description: "Fetch the rest of a domain or group listed in a knowledge_search '더 있음' index (fragments not yet returned in that search), in the same four views. Give search_id and exactly one of domain or group. Use it when your need grows beyond what the search returned (for example a layer note that needs the whole topic domain).",
    parameters: Type.Object({ search_id: Type.String(), domain: Type.Optional(Type.String()), group: Type.Optional(Type.String()) }),
    async execute(_id, params, _signal, _update, ctx) {
      return serialized(async () => output(await invoke("more", params, ctx.cwd)));
    },
  });
  pi.registerTool({
    name: "knowledge_fix_plan", label: "Knowledge fix plan",
    description: "After the user confirms a change, list stored fragments that now hold the old content. change: {type: rename|semantic, subject, old, new, instruction, user_quote (verbatim non-question confirmation), forms_quote? (verbatim user confirmation of the exact new wording, when user_quote does not contain change.new)}; plus 3-6 queries. Returns plan_id, items (rename items carry proposed_text) and needs_confirmation when the exact new wording is not user-confirmed yet: ask the user, then call again with forms_quote.",
    parameters: Type.Object({
      change: Type.Object({ type: Type.String(), subject: Type.String(), old: Type.String(), new: Type.String(),
        instruction: Type.String(), user_quote: Type.String(), forms_quote: Type.Optional(Type.String()) }),
      queries: Type.Array(Type.String()), host_id: Type.Optional(Type.String()),
    }),
    async execute(_id, params, _signal, _update, ctx) {
      return serialized(async () => output(await invoke("fix_plan", params, ctx.cwd)));
    },
  });
  pi.registerTool({
    name: "knowledge_fix_submit", label: "Knowledge fix submit",
    description: "Answer EVERY item of a fix plan exactly once: {alias, action: update|deprecate|keep, text (update: full corrected fragment, change only the old part), why (deprecate: why it is no longer valid — needs the user's confirmation in the plan; keep: why it still holds)}. Rejected or still-old rewrites come back in retry; fix those and submit them again. deprecate is held for now.",
    parameters: Type.Object({
      plan_id: Type.String(), partition_key: Type.String(),
      answers: Type.Array(Type.Object({ alias: Type.String(), action: Type.String(), text: Type.Optional(Type.String()), why: Type.Optional(Type.String()) })),
    }),
    async execute(_id, params, _signal, _update, ctx) {
      return serialized(async () => {
        const result = await invoke("fix_submit", { ...params, work_unit_id: workUnitId, cwd: ctx.cwd }, ctx.cwd);
        const rec = result.recorded as Record<string, unknown> | null | undefined;
        if (rec && typeof rec.work_unit_id === "string" && !workUnitId) {
          workUnitId = rec.work_unit_id;
          pi.appendEntry(ENTRY, { work_unit_id: workUnitId });
        }
        return output(result);
      });
    },
  });
  pi.registerTool({
    name: "knowledge_audit", label: "Knowledge audit",
    description: "Before knowledge_complete: Jev checks this session's conversation (plus optional code_summary lines) against the facts already recorded in this work unit and returns sentences that look like durable knowledge but are not recorded yet. Answer EVERY missing item: record it with knowledge_record (quote original words verbatim). Skip only non-knowledge (greeting, bare agreement, progress, verification report, question, unconfirmed proposal); never skip as 'already recorded' — digestion removes duplicates.",
    parameters: Type.Object({ code_summary: Type.Optional(Type.String()), max_messages: Type.Optional(Type.Number()) }),
    async execute(_id, params, _signal, _update, ctx) {
      return serialized(async () => {
        const t: { role: string; text: string }[] = transcript(ctx, Math.min(Math.max(params.max_messages ?? 80, 1), 400));
        if (params.code_summary) t.push({ role: "code", text: params.code_summary });
        return output(await invoke("audit", { transcript: t, work_unit_id: workUnitId }, ctx.cwd));
      });
    },
  });
  pi.registerTool({
    name: "knowledge_status", label: "Knowledge status",
    description: "Read this session's work unit, ledger states, baseline and absorbed aliases; no review or absorption is performed.",
    parameters: Type.Object({}),
    async execute(_id, _params, _signal, _update, ctx) {
      return serialized(async () => output(workUnitId
        ? await invoke("status", { work_unit_id: workUnitId }, ctx.cwd)
        : { ok: false, error: "NoWorkUnit" }));
    },
  });
}
