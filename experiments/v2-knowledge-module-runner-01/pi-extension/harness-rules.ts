import { execFile } from "node:child_process";
import { Type } from "@earendil-works/pi-ai";
import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";

// Harness rule layer (fixed, not per-project) for the knowledge module — schema-delta
// '하네스 규칙 층 1차 설계' and '지식 창 구성'. Not tied to any specific tool:
//  1. turn start: build the knowledge window for the user's request (Jev selects what is needed)
//  2. when the work subject (paths named in any tool call) shifts: rebuild the window in the background
//  3. every model request: attach the window to the request only (never stored in the transcript),
//     dropping lines whose [alias] is already present elsewhere in the current context
//  4. answer end: Jev looks for decisions/constraints of this turn that were not recorded; if any, one continuation.
const CLI = "/home/lazydino/dev/lazy-harness.v2/experiments/v2-knowledge-module-runner-01/knowledge_cli.py";
const WORK_UNIT = "knowledge-work-unit";
const PATH_RE = /(?:[\w.-]+\/)+[\w.-]+\.[A-Za-z0-9]{1,6}|\b[\w-]+\.(?:ts|tsx|js|py|md|sql|json|go|rs|ya?ml|toml|sh|css|html)\b/g;
const ALIAS_RE = /\[([^\[\]\s]+-\d+)\]/g;
// capture_audit sentence kinds -> knowledge_record kinds (the check must not suggest names record rejects)
const RECORD_KIND: Record<string, string> = { rule: "constraint", behavior: "fact", decision: "decision", code_role: "fact",
  test_guard: "fact", term: "term" };

type Msg = { role?: string; content?: unknown; customType?: string };

const RULE_CLI = "/home/lazydino/dev/lazy-harness.v2/experiments/v2-knowledge-module-runner-01/rule_cli.py";
const lits = (values: string[]) => Type.Union(values.map((v) => Type.Literal(v)));
const ruleFields = {
  when: Type.String({ description: "조건. 항상이면 '항상'" }),
  must: Type.String({ description: "해야 할 것. 금지는 '~하지 않는다'" }),
  level: lits(["must", "should"]),
  unless: Type.Optional(Type.String()), why: Type.Optional(Type.String()), ref: Type.Optional(Type.String()),
  code_check: Type.Optional(Type.Object({ type: lits(["command_succeeded_after_edit", "path_outside_project"]), command: Type.Optional(Type.String()) })),
};

export default function (pi: ExtensionAPI) {
  // Rule tools (rule module; not the knowledge pipeline). The agent turns the user's instruction into a rule.
  const ruleCli = (command: string, input: object, cwd: string): Promise<Record<string, unknown>> =>
    new Promise((resolve) => {
      const child = execFile("/usr/bin/python3", [RULE_CLI, command], { cwd, timeout: 180000, maxBuffer: 4 * 1024 * 1024 }, (error, stdout) => {
        try { resolve(JSON.parse(stdout.trim()) as Record<string, unknown>); }
        catch { resolve({ ok: false, error: error?.name ?? "InvalidResponse" }); }
      });
      child.stdin?.end(JSON.stringify(input));
    });
  const out = (r: Record<string, unknown>) => ({ content: [{ type: "text" as const, text: JSON.stringify(r) }], details: r });
  pi.registerTool({
    name: "rule_create", label: "Rule create",
    description: "When the user states how the agent must work from now on (e.g. '앞으로 코드 고치면 테스트 돌려'), turn it into ONE project rule. " +
      "when/must/level (must = '무조건/반드시', should = '가능하면'); unless/why only if the user said them; ref = knowledge area name when the rule means 'follow that convention'. " +
      "quote = the user's words verbatim (not a question). If the user's intent is unclear, ask first. If the result has needs_user, show the flags in plain words, " +
      "propose a fix, and call again with confirm_quote only if the user still wants it. Report the created rule in one line.",
    parameters: Type.Object({ rule: Type.Object(ruleFields), quote: Type.String(), confirm_quote: Type.Optional(Type.String()) }),
    async execute(_id, params, _signal, _update, ctx) { return out(await ruleCli("create", params, ctx.cwd)); },
  });
  pi.registerTool({
    name: "rule_update", label: "Rule update",
    description: "Change a project rule (p-*) the user asked to change. changes = only the changed fields (null clears unless/why/ref). quote = the user's words. Harness base rules (h-*) cannot be changed.",
    parameters: Type.Object({ id: Type.String(), changes: Type.Object(Object.fromEntries(Object.entries(ruleFields).map(([k, v]) => [k, Type.Optional(v)]))), quote: Type.String() }),
    async execute(_id, params, _signal, _update, ctx) { return out(await ruleCli("update", params, ctx.cwd)); },
  });
  pi.registerTool({
    name: "rule_delete", label: "Rule delete",
    description: "Delete a project rule (p-*) the user asked to remove. quote = the user's words. History is kept.",
    parameters: Type.Object({ id: Type.String(), quote: Type.String() }),
    async execute(_id, params, _signal, _update, ctx) { return out(await ruleCli("delete", params, ctx.cwd)); },
  });
  pi.registerTool({
    name: "rule_list", label: "Rule list",
    description: "List active rules (harness base h-* and project p-*). Use before changing or deleting a rule.",
    parameters: Type.Object({}),
    async execute(_id, _params, _signal, _update, ctx) { return out(await ruleCli("list", {}, ctx.cwd)); },
  });

  let prompt = "";
  let windowText = "";
  let subjects = new Set<string>();
  let refreshing: Promise<void> | undefined;
  let checkedThisRun = false;

  const invoke = (command: string, input: object, cwd: string, timeout = 180000): Promise<Record<string, unknown>> =>
    new Promise((resolve) => {
      const child = execFile("/usr/bin/python3", [CLI, command], { cwd, timeout, maxBuffer: 8 * 1024 * 1024 }, (error, stdout) => {
        try { resolve(JSON.parse(stdout.trim()) as Record<string, unknown>); }
        catch { resolve({ ok: false, error: error?.name ?? "InvalidResponse" }); }
      });
      child.stdin?.end(JSON.stringify(input));
    });

  const textOf = (content: unknown): string => typeof content === "string" ? content
    : Array.isArray(content) ? content.filter((c: { type?: string }) => c?.type === "text").map((c: { text?: string }) => c.text ?? "").join("\n") : "";
  const argsOf = (content: unknown): string => Array.isArray(content)
    ? content.filter((c: { type?: string }) => c?.type === "toolCall").map((c: { arguments?: unknown }) => JSON.stringify(c.arguments ?? {})).join("\n") : "";

  const build = async (ctx: ExtensionContext, question: string, queries: string[]) => {
    const result = await invoke("window", { question, queries: queries.slice(0, 7) }, ctx.cwd);
    if (typeof result.text === "string") windowText = result.text;
  };

  const recentSubjects = (ctx: ExtensionContext): string[] => {
    const found: string[] = [];
    const branch = ctx.sessionManager.getBranch();
    for (const entry of branch.slice(-12)) {
      if (entry.type !== "message") continue;
      const msg = (entry as { message?: Msg }).message;
      if (msg?.role !== "assistant") continue;
      for (const m of argsOf(msg.content).matchAll(PATH_RE)) found.push(m[0]);
    }
    return [...new Set(found)];
  };

  const workUnit = (ctx: ExtensionContext): string | undefined => {
    let id: string | undefined;
    for (const entry of ctx.sessionManager.getBranch()) {
      if (entry.type === "custom" && entry.customType === WORK_UNIT) id = (entry.data as { work_unit_id?: string })?.work_unit_id ?? id;
    }
    return id;
  };

  // 1. turn start
  pi.on("before_agent_start", async (event, ctx) => {
    prompt = event.prompt ?? "";
    checkedThisRun = false;
    if (prompt.trim().length < 4) return;
    subjects = new Set(recentSubjects(ctx));
    await build(ctx, prompt, [...subjects].map((s) => s.split("/").pop() ?? s));
  });

  // 2. subject shift (any tool, not a tool list)
  pi.on("turn_end", async (_event, ctx) => {
    if (!prompt || refreshing) return;
    const now = recentSubjects(ctx);
    const fresh = now.filter((s) => !subjects.has(s));
    if (fresh.length === 0) return;
    for (const s of fresh) subjects.add(s);
    const names = fresh.map((s) => s.split("/").pop() ?? s);
    refreshing = build(ctx, `${prompt.slice(0, 600)}\n작업 대상: ${fresh.join(", ")}`, names).finally(() => { refreshing = undefined; });
  });

  // 3. every model request: attach the window to this request only
  pi.on("context", async (event) => {
    if (!windowText) return;
    const messages = event.messages as Msg[];
    const present = new Set<string>();
    for (const m of messages) for (const a of textOf(m.content).matchAll(ALIAS_RE)) present.add(a[1]);
    const lines = windowText.split("\n").filter((line) => {
      const a = /^- (?:⚠ 충돌 후보 )?\[([^\[\]\s]+-\d+)\]/.exec(line);
      return !a || !present.has(a[1]);
    });
    if (!lines.some((l) => /^- (?:⚠ 충돌 후보 )?\[/.test(l))) return;
    const block = { type: "text" as const, text: lines.join("\n") };
    const out = messages.slice();
    const last = out[out.length - 1];
    if (last && (last.role === "user" || last.role === "toolResult" || last.role === "custom")) {
      const content = typeof last.content === "string" ? [{ type: "text" as const, text: last.content }] : Array.isArray(last.content) ? last.content : [];
      out[out.length - 1] = { ...last, content: [...content, block] };
    } else {
      out.push({ role: "custom", customType: "knowledge-window", content: [block], display: false, timestamp: Date.now() } as Msg);
    }
    return { messages: out as typeof event.messages };
  });

  // 4. answer end: unrecorded knowledge of this turn -> one continuation
  pi.on("agent_before_settle", async (event, ctx) => {
    if (checkedThisRun || !prompt) return;
    checkedThisRun = true;
    const turn: { role: string; text: string }[] = [];
    const msgs = event.context.contextMessages as Msg[];
    let start = 0;
    for (let i = msgs.length - 1; i >= 0; i--) if (msgs[i].role === "user") { start = i; break; }
    for (const m of msgs.slice(start)) {
      if (m.role !== "user" && m.role !== "assistant") continue;
      const text = textOf(m.content).trim();
      if (text) turn.push({ role: m.role, text });
    }
    if (!turn.some((t) => t.role === "assistant")) return;
    const result = await invoke("audit", { transcript: turn, work_unit_id: workUnit(ctx) }, ctx.cwd);
    const missing = Array.isArray(result.missing) ? result.missing as { text?: string; kind?: string }[] : [];
    if (missing.length === 0) return;
    return {
      entries: [{ type: "custom_message", customType: "harness-record-check", display: true,
        content: "[harness-record-check] 이번 턴에서 기록되지 않은 지식으로 보이는 문장이 있다. 같은 내용은 한 사실로 합쳐 knowledge_record 로 기록하거나(원문 인용), "
          + "지식이 아니면(진행 안내·확정 안 된 제안·질문·자기 행동 설명) 건너뛰어라. 괄호 안은 권장 kind. 사용자에게 답할 필요는 없다.\n"
          + missing.slice(0, 12).map((m) => `- (${RECORD_KIND[m.kind ?? ""] ?? "fact"}) ${m.text ?? ""}`).join("\n") }],
      continue: true,
    };
  });
}
