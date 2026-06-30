import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { existsSync, readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const EXTENSION_NAME = "lazy-harness";
const MAX_RECENT_TOOL_CALLS = 80;
const DEFAULT_TIMEOUT_MS = Number(process.env.LAZY_HARNESS_PI_HOOK_TIMEOUT_MS || 15000);

type JsonObject = Record<string, unknown>;

type RecentToolCall = {
  name: string;
  args: JsonObject;
  args_preview?: string;
  edit_target?: string;
  toolCallId?: string;
  is_error?: boolean;
  result_preview?: unknown;
};

const recentToolCallsByRoot = new Map<string, RecentToolCall[]>();
const activePacketsByRoot = new Map<string, { root: string; sessionId: string; messageId: string }>();
const lastAdvisoryByRoot = new Map<string, { hash: string; count: number; chainCount: number }>();
const MAX_ADVISORY_CONTINUATIONS = 2;
const MAX_ADVISORY_CHAIN_CONTINUATIONS = 1;
// Jcode-parity mid-turn re-grounding state (see the "context" handler).
const pendingRegroundByRoot = new Map<string, boolean>();
const regroundBodyByRoot = new Map<string, string>();
const FILE_OP_TOOLS = new Set(["read", "edit", "write", "grep", "find", "ls"]);

function stableHash(value: unknown): string {
  return createHash("sha256").update(String(value ?? "")).digest("hex").slice(0, 16);
}

function findLazyRoot(cwd: string): string | undefined {
  let current = resolve(cwd || process.cwd());
  while (true) {
    if (existsSync(join(current, ".lazy-harness", "bin", "lazy"))) return current;
    const parent = dirname(current);
    if (parent === current) return undefined;
    current = parent;
  }
}

function resolveInvocationCwd(event: any, ctx: any): string {
  const sessionCwd = ctx?.sessionManager?.getCwd?.();
  return String(sessionCwd || event?.cwd || event?.workingDirectory || ctx?.cwd || process.cwd());
}

function findLazyRootForInvocation(event: any, ctx: any): string | undefined {
  return findLazyRoot(resolveInvocationCwd(event, ctx));
}

function runHook(scriptPath: string, payload: JsonObject, root: string): { stdout: string; stderr: string; status: number | null; error?: string } {
  const completed = spawnSync("bash", [scriptPath], {
    cwd: root,
    input: JSON.stringify(payload),
    encoding: "utf8",
    timeout: DEFAULT_TIMEOUT_MS,
    env: {
      ...process.env,
      LAZY_HOST_ROOT: root,
      LAZY_HARNESS_INVOKER: "pi-extension",
    },
  });
  return {
    stdout: completed.stdout || "",
    stderr: completed.stderr || "",
    status: completed.status,
    error: completed.error ? String(completed.error) : undefined,
  };
}

function parseJsonMaybe(text: string): JsonObject | undefined {
  const trimmed = text.trim();
  if (!trimmed) return undefined;
  try {
    const parsed = JSON.parse(trimmed);
    return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed as JsonObject : undefined;
  } catch {
    return undefined;
  }
}

function hookInjectBody(stdout: string): string | undefined {
  const parsed = parseJsonMaybe(stdout);
  const inject = parsed?.inject;
  if (inject && typeof inject === "object" && !Array.isArray(inject)) {
    const body = (inject as JsonObject).body;
    if (typeof body === "string" && body.trim()) return body;
  }
  return undefined;
}

function denyReason(stdout: string, stderr: string): string | undefined {
  const trimmed = stdout.trim();
  if (!trimmed) return undefined;
  const parsed = parseJsonMaybe(trimmed);
  if (parsed?.action === "deny" && typeof parsed.reason === "string" && parsed.reason.trim()) {
    return parsed.reason.trim();
  }
  return trimmed || stderr.trim() || undefined;
}

function previewContent(content: unknown): unknown {
  if (typeof content === "string") return content.slice(0, 1000);
  if (Array.isArray(content)) return content.slice(0, 3);
  if (content && typeof content === "object") {
    try {
      return JSON.parse(JSON.stringify(content)).slice?.(0, 3) ?? content;
    } catch {
      return String(content).slice(0, 1000);
    }
  }
  return content;
}

// jcode-shape payload parity: on-response-completed helpers (17 of them) read a
// string `args_preview` per tool call and the agent's `assistant_response` prose
// to decide gate satisfaction. The Pi/OMP events expose `args` objects and
// `event.messages`, so we project them into the shape the canonical helpers expect.
function argsPreview(args: JsonObject): string {
  const parts: string[] = [];
  for (const k of ["file_path", "path", "filePath", "command", "cmd", "text", "pattern", "old_string", "new_string"]) {
    const v = (args as Record<string, unknown>)[k];
    if (typeof v === "string") parts.push(v);
  }
  let blob = parts.join(" ");
  if (!blob) {
    try { blob = JSON.stringify(args); } catch { blob = String(args); }
  }
  return blob.slice(0, 2000);
}

// Edit-target-only path extraction for the 5d-3 gates: the file(s) actually
// written/edited, NOT every path quoted in the args body (which made records that
// merely mention `src/foo.tsx` false-fire the gate). Clean tools carry
// file_path/path; patch tools (`_edit`) embed the target in `[PATH#TAG]` headers.
function editTargetPaths(args: JsonObject): string {
  const targets: string[] = [];
  for (const k of ["file_path", "path", "filePath"]) {
    const v = (args as Record<string, unknown>)[k];
    if (typeof v === "string" && v.trim()) targets.push(v.trim());
  }
  for (const k of ["input", "patch"]) {
    const v = (args as Record<string, unknown>)[k];
    if (typeof v === "string") {
      for (const m of v.matchAll(/\[([^\]\s#]+)#[0-9A-Fa-f]{4}\]/g)) targets.push(m[1]);
    }
  }
  return [...new Set(targets)].join(" ");
}

function messageText(message: unknown): string {
  const content = (message as { content?: unknown } | undefined)?.content;
  if (typeof content === "string") return content;
  if (Array.isArray(content)) {
    return content
      .map((part: any) => (part && typeof part.text === "string" ? part.text : ""))
      .filter(Boolean)
      .join("\n");
  }
  return "";
}

function lastMessageTextByRole(messages: unknown, role: string): string {
  if (!Array.isArray(messages)) return "";
  for (let i = messages.length - 1; i >= 0; i--) {
    if ((messages[i] as { role?: string } | undefined)?.role === role) return messageText(messages[i]);
  }
  return "";
}

// OMP/Pi expose a native interactive `ask` selector (loadMode "discoverable"), which tool
// discovery mode hides once the session has many tools (>40). Keep it active so harness
// option gates (AGENTS §2.3) render as native selectable choices instead of plain A/B/C
// text. Add-only, interactive-only (the `ask` tool only exists when the session has a UI),
// fail-open so a runtime without these APIs simply falls back to text option gates.
async function ensureAskToolActive(pi: ExtensionAPI): Promise<void> {
  try {
    const p = pi as any;
    if (typeof p.getAllTools !== "function" || typeof p.getActiveTools !== "function" || typeof p.setActiveTools !== "function") return;
    const allNames = (p.getAllTools() as any[]).map((t) => (typeof t === "string" ? t : t?.name)).filter(Boolean);
    if (!allNames.includes("ask")) return; // non-interactive session: no native ask selector to surface
    const active = (p.getActiveTools() as string[]) ?? [];
    if (active.includes("ask")) return;
    await p.setActiveTools([...active, "ask"]);
  } catch {
    /* unsupported runtime / non-interactive: option gates fall back to text */
  }
}

function systemPromptIncludesBody(systemPrompt: unknown, body: string): boolean {
  if (Array.isArray(systemPrompt)) {
    return systemPrompt.some((part) => typeof part === "string" && part.includes(body));
  }
  return String(systemPrompt || "").includes(body);
}

function appendSystemPromptBody(systemPrompt: unknown, body: string): string | string[] {
  if (Array.isArray(systemPrompt)) {
    const parts = systemPrompt.filter((part): part is string => typeof part === "string");
    return [...parts, body];
  }
  const current = String(systemPrompt || "").trimEnd();
  return current ? `${current}\n\n${body}` : body;
}


function normalizePiTool(toolName: unknown, input: unknown): { name: string; args: JsonObject } {
  const rawName = String(toolName || "");
  const args = (input && typeof input === "object" ? input : {}) as JsonObject;
  const lower = rawName.toLowerCase();
  if (["cmd", "command", "shell", "terminal"].includes(lower)) {
    const command = typeof args.command === "string"
      ? args.command
      : typeof args.cmd === "string"
        ? args.cmd
        : typeof args.text === "string"
          ? args.text
          : "";
    return { name: "bash", args: { ...args, command } };
  }
  return { name: rawName, args };
}

function recentToolCallsForRoot(root: string): RecentToolCall[] {
  let calls = recentToolCallsByRoot.get(root);
  if (!calls) {
    calls = [];
    recentToolCallsByRoot.set(root, calls);
  }
  return calls;
}

function rememberToolCall(root: string, call: RecentToolCall): void {
  const calls = recentToolCallsForRoot(root);
  calls.push(call);
  while (calls.length > MAX_RECENT_TOOL_CALLS) calls.shift();
}

function findLazyRootFromEvent(event: any, ctx: any): string | undefined {
  return findLazyRootForInvocation(event, ctx);
}

async function runLazyCommand(pi: ExtensionAPI, ctx: any, args: string, lazyArgs: string[]): Promise<void> {
  const root = findLazyRootForInvocation(undefined, ctx);
  if (!root) {
    ctx.ui?.notify?.("lazy-harness: .lazy-harness/bin/lazy not found from current cwd", "warning");
    return;
  }
  const lazy = join(root, ".lazy-harness", "bin", "lazy");
  const extra = args.trim() ? args.trim().split(/\s+/) : [];
  const result = await pi.exec(lazy, [...lazyArgs, ...extra], { cwd: root, timeout: 120000, signal: ctx.signal });
  const stdout = String((result as any).stdout ?? "");
  const stderr = String((result as any).stderr ?? "");
  const code = (result as any).exitCode ?? (result as any).code ?? 0;
  const body = [stdout.trim(), stderr.trim()].filter(Boolean).join("\n").slice(0, 1600) || `lazy ${lazyArgs.join(" ")} completed`;
  ctx.ui?.notify?.(`lazy-harness ${lazyArgs.join(" ")} exit=${code}\n${body}`, code ? "warning" : "info");
}

async function runPackageScript(pi: ExtensionAPI, ctx: any, args: string, scriptRelativeToExtension: string): Promise<void> {
  const root = findLazyRootForInvocation(undefined, ctx);
  if (!root) {
    ctx.ui?.notify?.("lazy-harness: .lazy-harness/bin/lazy not found from current cwd", "warning");
    return;
  }
  const scriptPath = fileURLToPath(new URL(scriptRelativeToExtension, import.meta.url));
  const extra = args.trim() ? args.trim().split(/\s+/) : [];
  const result = await pi.exec("bun", [scriptPath, ...extra], { cwd: root, timeout: 120000, signal: ctx.signal });
  const stdout = String((result as any).stdout ?? "");
  const stderr = String((result as any).stderr ?? "");
  const code = (result as any).exitCode ?? (result as any).code ?? 0;
  const body = [stdout.trim(), stderr.trim()].filter(Boolean).join("\n").slice(0, 2000) || `${scriptPath} completed`;
  ctx.ui?.notify?.(`lazy-harness package script exit=${code}\n${body}`, code ? "warning" : "info");
}

export default function lazyHarnessPi(pi: ExtensionAPI) {
  pi.on("before_agent_start", async (event: any, ctx: any) => {
    const cwd = resolveInvocationCwd(event, ctx);
    const root = findLazyRoot(cwd);
    if (!root) return undefined;

    const sessionId = `pi:${stableHash(cwd)}`;
    const messageId = `pi:${stableHash(`${Date.now()}:${event.prompt || ""}`)}`;
    activePacketsByRoot.set(root, { root, sessionId, messageId });
    pendingRegroundByRoot.delete(root); // fresh turn: clear mid-turn re-grounding state
    regroundBodyByRoot.delete(root);
    await ensureAskToolActive(pi); // keep OMP's native `ask` selector available for §2.3 option gates

    const payload: JsonObject = {
      event: "message.received",
      source: EXTENSION_NAME,
      session_id: sessionId,
      message_id: messageId,
      working_dir: root,
      last_user_message: String(event.prompt || ""),
      recent_tool_calls: recentToolCallsForRoot(root).slice(-40),
    };

    const script = join(root, ".lazy-harness", "hooks", "lifecycle", "on-message-received.sh");
    const hook = existsSync(script) ? runHook(script, payload, root) : { stdout: "", stderr: "", status: 0 };
    const body = hookInjectBody(hook.stdout) ?? [
      "REMINDER. Harness-first search/read debt before response.",
      "- Pi lazy-harness package loaded; inspect real .lazy-harness records/source/tests before host-specific claims or mutation.",
      "- Mutation remains guarded by the generic search/read evidence guard.",
    ].join("\n");

    // jcode load_harness_dir parity: force-load the FULL .lazy-harness/AGENTS.md grammar into the
    // system prompt every session (OMP/Pi otherwise only load a compact pointer). Deduped by the
    // grammar title marker so it lands once and persists; fail-open to reminder-only on any error.
    let inject = body;
    const agentsPath = join(root, ".lazy-harness", "AGENTS.md");
    if (existsSync(agentsPath) && !systemPromptIncludesBody(event.systemPrompt, "Lazy-Harness AI")) {
      try {
        const grammar = readFileSync(agentsPath, "utf8").trim();
        if (grammar) inject = `${grammar}\n\n${body}`;
      } catch { /* fail-open: reminder only */ }
    }

    if (systemPromptIncludesBody(event.systemPrompt, inject)) return undefined;
    return { systemPrompt: appendSystemPromptBody(event.systemPrompt, inject) };
  });

  pi.on("tool_call", async (event: any, ctx: any) => {
    const cwd = resolveInvocationCwd(event, ctx);
    const root = findLazyRoot(cwd);
    if (!root) return undefined;

    const packet = activePacketsByRoot.get(root)
      ? activePacketsByRoot.get(root)!
      : { root, sessionId: `pi:${stableHash(cwd)}`, messageId: `pi:${stableHash("no-active-packet")}` };

    const payload: JsonObject = {
      event: "tool.execute.before",
      source: EXTENSION_NAME,
      session_id: packet.sessionId,
      message_id: packet.messageId,
      working_dir: root,
      tool: normalizePiTool(event.toolName, event.input || {}),
      recent_tool_calls: recentToolCallsForRoot(root).slice(-40),
    };

    const script = join(root, ".lazy-harness", "hooks", "lifecycle", "on-tool-execute-before.sh");
    if (!existsSync(script)) return undefined;
    const hook = runHook(script, payload, root);
    const reason = denyReason(hook.stdout, hook.stderr);
    if (reason) return { block: true, reason };
    return undefined;
  });

  pi.on("tool_result", async (event: any, ctx: any) => {
    const root = findLazyRootFromEvent(event, ctx);
    if (!root) return undefined;
    const normalized = normalizePiTool(event.toolName, event.input || {});
    rememberToolCall(root, {
      ...normalized,
      args_preview: argsPreview(normalized.args),
      edit_target: editTargetPaths(normalized.args),
      toolCallId: String(event.toolCallId || ""),
      is_error: Boolean(event.isError),
      result_preview: previewContent(event.content),
    });
    // Jcode parity: after the agent reads/searches/edits files, mark the next LLM
    // call for harness-grammar re-grounding (handled by the "context" handler).
    if (FILE_OP_TOOLS.has(normalized.name.toLowerCase()) && !event.isError) {
      pendingRegroundByRoot.set(root, true);
    }
    return undefined;
  });

  // "context" fires before each LLM call and can modify the messages sent to the model.
  // Jcode natively re-injected relevant AGENTS/.jcode instructions after file operations
  // ("read and follow them for the next steps"). Pi/OMP load AGENTS.md only once at session
  // start, so we replicate that mid-turn re-grounding here: one inject per new file-op batch,
  // body computed once per turn via on-context.sh. If the hook cannot produce a real body,
  // fail open silently; do NOT inject a generic fallback reminder, because it can loop without
  // surfacing the relevant records that make the reminder actionable.
  pi.on("context", async (event: any, ctx: any) => {
    try {
      const root = findLazyRoot(resolveInvocationCwd(event, ctx));
      if (!root) return undefined;
      if (!pendingRegroundByRoot.get(root)) return undefined;
      pendingRegroundByRoot.delete(root);

      let body = regroundBodyByRoot.get(root);
      if (body === undefined) {
        const script = join(root, ".lazy-harness", "hooks", "lifecycle", "on-context.sh");
        if (!existsSync(script)) return undefined;
        const payload: JsonObject = { event: "context", source: EXTENSION_NAME, working_dir: root, recent_tool_calls: recentToolCallsForRoot(root).slice(-40) };
        const hook = runHook(script, payload, root);
        body = hookInjectBody(hook.stdout);
        if (!body) return undefined;
        regroundBodyByRoot.set(root, body);
      }

      const messages = Array.isArray(event.messages) ? event.messages : [];
      const reminder = { role: "user", content: `<system-reminder>\n${body}\n</system-reminder>`, timestamp: Date.now() };
      return { messages: [...messages, reminder] };
    } catch {
      return undefined;
    }
  });

  pi.on("agent_end", async (event: any, ctx: any) => {
    const cwd = resolveInvocationCwd(event, ctx);
    const root = findLazyRoot(cwd);
    if (!root) return undefined;

    const packet = activePacketsByRoot.get(root)
      ? activePacketsByRoot.get(root)!
      : { root, sessionId: `pi:${stableHash(cwd)}`, messageId: `pi:${stableHash("no-active-packet")}` };

    const messages = Array.isArray(event.messages) ? event.messages : [];
    const payload: JsonObject = {
      event: "response.completed",
      source: EXTENSION_NAME,
      session_id: packet.sessionId,
      message_id: packet.messageId,
      working_dir: root,
      recent_tool_calls: recentToolCallsForRoot(root).slice(-40),
      // jcode-shape parity: on-response-completed helpers walk the assistant response
      // prose and last user message (e.g. discovery-capture satisfaction #2).
      assistant_response: lastMessageTextByRole(messages, "assistant"),
      last_user_message: lastMessageTextByRole(messages, "user"),
    };

    const script = join(root, ".lazy-harness", "hooks", "lifecycle", "on-response-completed.sh");
    if (!existsSync(script)) return undefined;
    const hook = runHook(script, payload, root);
    const body = hookInjectBody(hook.stdout);
    if (!body) {
      lastAdvisoryByRoot.delete(root); // gate resolved → reset continuation counter
      return undefined;
    }
    // Drive a continuation so the agent addresses the gate (Jcode response.completed M11 parity).
    // Loop-safe on two axes: the SAME unresolved advisory drives at most
    // MAX_ADVISORY_CONTINUATIONS turns, and an alternating sequence of different
    // STOP advisories drives at most MAX_ADVISORY_CHAIN_CONTINUATIONS follow-up
    // turns before degrading to non-steering display. This prevents capture-gate
    // and rule-placement helpers from ping-ponging indefinitely.
    const advisoryHash = stableHash(body);
    const prevAdvisory = lastAdvisoryByRoot.get(root);
    const advisoryCount = prevAdvisory && prevAdvisory.hash === advisoryHash ? prevAdvisory.count + 1 : 1;
    const advisoryChainCount = prevAdvisory ? prevAdvisory.chainCount + 1 : 1;
    lastAdvisoryByRoot.set(root, { hash: advisoryHash, count: advisoryCount, chainCount: advisoryChainCount });
    if (advisoryCount <= MAX_ADVISORY_CONTINUATIONS && advisoryChainCount <= MAX_ADVISORY_CHAIN_CONTINUATIONS && typeof (pi as any).sendUserMessage === "function") {
      (pi as any).sendUserMessage(body, { deliverAs: "followUp" });
    } else if (typeof (pi as any).sendMessage === "function") {
      (pi as any).sendMessage({ content: body, display: true });
    }
    return undefined;
  });

  pi.registerCommand("lazy-map", {
    description: "Run lazy map from the current project root. Usage: /lazy-map --overview --format=md --limit=20",
    handler: async (args: string, ctx: any) => runLazyCommand(pi, ctx, args || "--overview --format=md --limit=20", ["map"]),
  });

  pi.registerCommand("lazy-doctor", {
    description: "Run lazy doctor from the current project root.",
    handler: async (args: string, ctx: any) => runLazyCommand(pi, ctx, args, ["doctor"]),
  });

  pi.registerCommand("lazy-test", {
    description: "Run lazy test from the current project root.",
    handler: async (args: string, ctx: any) => runLazyCommand(pi, ctx, args, ["test"]),
  });

  pi.registerCommand("lazy-sync", {
    description: "Run lazy sync from the current project root.",
    handler: async (args: string, ctx: any) => runLazyCommand(pi, ctx, args, ["sync"]),
  });

  pi.registerCommand("lazy-update", {
    description: "Run lazy update from the current project root.",
    handler: async (args: string, ctx: any) => runLazyCommand(pi, ctx, args, ["update"]),
  });

  pi.registerCommand("lazy-import-antigravity-mcp", {
    description: "Import Antigravity MCP config into Pi MCP adapter config. Defaults to dry-run; pass --apply to write ~/.pi/agent/mcp.json.",
    handler: async (args: string, ctx: any) => runPackageScript(pi, ctx, args || "--dry-run", "../../scripts/import-antigravity-mcp.ts"),
  });
}
