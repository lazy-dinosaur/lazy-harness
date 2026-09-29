import { execFile } from "node:child_process";
import { dirname, isAbsolute, relative, resolve as resolvePath } from "node:path";
import { homedir } from "node:os";
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
    name: "rule_dispute", label: "Rule dispute",
    description: "When a [harness-rule-check] violation is not true after you re-checked it, record why in one line (receipt_id from the check). Fix it instead when it is true.",
    parameters: Type.Object({ receipt_id: Type.String(), reason: Type.String() }),
    async execute(_id, params, _signal, _update, ctx) { return out(await ruleCli("dispute", params, ctx.cwd)); },
  });
  pi.registerTool({
    name: "rule_list", label: "Rule list",
    description: "List active rules (harness base h-* and project p-*). Use before changing or deleting a rule.",
    parameters: Type.Object({}),
    async execute(_id, _params, _signal, _update, ctx) { return out(await ruleCli("list", {}, ctx.cwd)); },
  });

  // Harness base rule h-1 (code check, block): general tools must not read or search outside the project folder.
  // "Outside" = sibling projects / ancestors of the project root (the case seen in real use: find .. over other
  // projects' AGENTS.md). System paths (/usr, /tmp, ...) are not project knowledge and are left alone.
  const outsideProject = (cwd: string, p: string): boolean => {
    const abs = resolvePath(cwd, p.startsWith("~/") ? homedir() + p.slice(1) : p);
    const rel = relative(cwd, abs);
    if (!rel || (!rel.startsWith("..") && !isAbsolute(rel))) return false;
    const parent = dirname(cwd);
    const relParent = relative(parent, abs);
    return !relParent.startsWith("..") && !isAbsolute(relParent);
  };
  const BASH_OUT = /(?:^|[\s;&|(])(?:cd|find|ls|grep|rg|cat|head|tail|tree|fd)\s+(?:-\S+\s+)*(\.\.(?:\/[^\s;&|)]*)?|~\/[^\s;&|)]+|\/home\/[^\s;&|)]+)/g;
  pi.on("tool_call", async (event, ctx) => {
    const input = (event as { input?: Record<string, unknown> }).input ?? {};
    const paths: string[] = [];
    for (const k of ["path", "file_path", "cwd", "directory"]) if (typeof input[k] === "string") paths.push(input[k] as string);
    if (typeof input.command === "string") for (const m of (input.command as string).matchAll(BASH_OUT)) paths.push(m[1]);
    const bad = paths.find((p) => outsideProject(ctx.cwd, p));
    if (!bad) return;
    return { block: true, reason: `[h-1] 프로젝트 폴더 밖(${bad})은 일반 도구로 읽거나 뒤지지 않는다. 다른 프로젝트·팀 문서는 사용자가 원할 때 소화 전용 도구로만 가져온다.` };
  });

  // LHV2_INJECT=none only for baseline experiments (judgment without injection); default injects (sys placement)
  const INJECT = (process.env.LHV2_INJECT ?? "sys").toLowerCase();
  let delivered = new Set<string>();
  let guideText = "";
  let prompt = "";
  let windowText = "";
  let windowAliases: string[] = [];
  let ruleText = "";
  let ruleIds: string[] = [];
  const sessionTag = Math.random().toString(36).slice(2, 10);
  let turnNo = 0;
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
    if (Array.isArray(result.aliases)) windowAliases = result.aliases as string[];
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

  // 1. turn start (schema-delta '주입 위치 — 규칙은 시스템 안내, 지식은 턴 시작 메시지'; inj-01):
  //    harness guide (top) + project rule block go into a system prompt section (stable -> cache kept);
  //    the knowledge window goes in once per user turn as a message (never re-attached per request).
  pi.on("before_agent_start", async (event, ctx) => {
    prompt = event.prompt ?? "";
    checkedThisRun = false;
    turnNo += 1;
    delivered = new Set<string>();
    if (INJECT === "none") return;
    const block = await ruleCli("block", {}, ctx.cwd);
    ruleText = typeof block.text === "string" ? block.text : "";
    guideText = typeof block.guide === "string" ? block.guide : "";
    ruleIds = Array.isArray(block.ids) ? block.ids as string[] : [];
    const opts = (event as { systemPromptOptions?: { sections?: Record<string, string> } }).systemPromptOptions;
    if (opts) opts.sections = { ...(opts.sections ?? {}), "lazy-harness-rules": [guideText, ruleText].filter((t) => t && t.trim()).join("\n\n") };
    windowText = "";
    windowAliases = [];
    if (prompt.trim().length >= 4) {
      subjects = new Set(recentSubjects(ctx));
      await build(ctx, prompt, [...subjects].map((s) => s.split("/").pop() ?? s));
    }
    for (const a of windowAliases) delivered.add(a);
    void ruleCli("inject", { turn_ref: `${sessionTag}#${turnNo}`, rule_ids: ruleIds, aliases: windowAliases,
      tokens: Math.floor((guideText.length + ruleText.length + windowText.length) / 2) }, ctx.cwd);
    if (!windowText.trim()) return;
    return { message: { customType: "harness-context", content: windowText, display: false } };
  });

  // 2. subject shift (any tool, not a tool list): only knowledge lines not yet delivered this turn, as one message
  pi.on("turn_end", async (_event, ctx) => {
    if (!prompt || refreshing || INJECT === "none") return;
    const now = recentSubjects(ctx);
    const fresh = now.filter((s) => !subjects.has(s));
    if (fresh.length === 0) return;
    for (const s of fresh) subjects.add(s);
    const names = fresh.map((s) => s.split("/").pop() ?? s);
    refreshing = build(ctx, `${prompt.slice(0, 600)}\n작업 대상: ${fresh.join(", ")}`, names).then(() => {
      const lines = windowText.split("\n").filter((line) => {
        const m = /^- (?:⚠ 충돌 후보 )?\[([^\[\]\s]+-\d+)\]/.exec(line);
        return m && !delivered.has(m[1]);
      });
      if (!lines.length) return;
      for (const l of lines) { const m = /\[([^\[\]\s]+-\d+)\]/.exec(l); if (m) delivered.add(m[1]); }
      // async refresh: the session may be gone by now (closed window, headless exit) -> drop the supplement
      try {
        pi.sendMessage({ customType: "harness-context", display: false,
          content: `[knowledge-window 보충] 작업 대상이 바뀌어 추가로 관련된 지식:\n${lines.join("\n")}` }, { deliverAs: "steer" });
      } catch { /* stale session */ }
    }).catch(() => undefined).finally(() => { refreshing = undefined; });
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
    // rule judgment evidence: code-collected facts of this turn (files touched, commands run, diff)
    const files = new Set<string>(), commands: string[] = [];
    for (const m of msgs.slice(start)) {
      if (m.role !== "assistant" || !Array.isArray(m.content)) continue;
      for (const c of m.content as { type?: string; name?: string; arguments?: Record<string, unknown> }[]) {
        if (c?.type !== "toolCall") continue;
        const a = c.arguments ?? {};
        if (typeof a.path === "string" && /edit|write/i.test(c.name ?? "")) files.add(a.path);
        if (typeof a.command === "string") commands.push(a.command);
      }
    }
    const diff = files.size ? await new Promise<string>((resolve) => execFile("git", ["diff", "--no-color", "--", ...files],
      { cwd: ctx.cwd, timeout: 15000, maxBuffer: 2 * 1024 * 1024 }, (_e, stdout) => resolve(String(stdout ?? "").slice(0, 20000)))) : "";
    const lastAnswer = [...turn].reverse().find((t) => t.role === "assistant")?.text ?? "";
    const [result, judged] = await Promise.all([
      invoke("audit", { transcript: turn, work_unit_id: workUnit(ctx) }, ctx.cwd),
      ruleCli("judge", { turn_ref: `${sessionTag}#${turnNo}`, evidence: { user: prompt, answer: lastAnswer, files: [...files], commands, diff } }, ctx.cwd),
    ]);
    const missing = Array.isArray(result.missing) ? result.missing as { text?: string; kind?: string }[] : [];
    const entries: { type: "custom_message"; customType: string; display: boolean; content: string }[] = [];
    if (typeof judged.alert === "string" && judged.alert) {
      const receipts = (judged.receipts ?? {}) as Record<string, string>;
      entries.push({ type: "custom_message", customType: "harness-rule-check", display: true,
        content: judged.alert + "\nreceipt_id: " + Object.entries(receipts).map(([k, v]) => `${k}=${v}`).join(", ") });
    }
    if (missing.length) {
      entries.push({ type: "custom_message", customType: "harness-record-check", display: true,
        content: "[harness-record-check] 이번 턴에서 기록되지 않은 지식으로 보이는 문장이 있다. 같은 내용은 한 사실로 합쳐 knowledge_record 로 기록하거나(원문 인용), "
          + "지식이 아니면(진행 안내·확정 안 된 제안·질문·자기 행동 설명) 건너뛰어라. 괄호 안은 권장 kind. 사용자에게 답할 필요는 없다.\n"
          + missing.slice(0, 12).map((m) => `- (${RECORD_KIND[m.kind ?? ""] ?? "fact"}) ${m.text ?? ""}`).join("\n") });
    }
    if (!entries.length) return;
    return { entries, continue: true };
  });
}
