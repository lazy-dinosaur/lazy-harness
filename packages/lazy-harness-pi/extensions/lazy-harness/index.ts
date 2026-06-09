import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { existsSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const EXTENSION_NAME = "lazy-harness";
const MAX_RECENT_TOOL_CALLS = 80;
const DEFAULT_TIMEOUT_MS = Number(process.env.LAZY_HARNESS_PI_HOOK_TIMEOUT_MS || 15000);

type JsonObject = Record<string, unknown>;

type RecentToolCall = {
  name: string;
  args: JsonObject;
  toolCallId?: string;
  is_error?: boolean;
  result_preview?: unknown;
};

const recentToolCalls: RecentToolCall[] = [];
let activePacket: { root: string; sessionId: string; messageId: string } | undefined;

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

function rememberToolCall(call: RecentToolCall): void {
  recentToolCalls.push(call);
  while (recentToolCalls.length > MAX_RECENT_TOOL_CALLS) recentToolCalls.shift();
}

async function runLazyCommand(pi: ExtensionAPI, ctx: any, args: string, lazyArgs: string[]): Promise<void> {
  const root = findLazyRoot(ctx.cwd);
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
  const root = findLazyRoot(ctx.cwd);
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
    const root = findLazyRoot(ctx.cwd);
    if (!root) return undefined;

    const sessionId = `pi:${stableHash(ctx.cwd)}`;
    const messageId = `pi:${stableHash(`${Date.now()}:${event.prompt || ""}`)}`;
    activePacket = { root, sessionId, messageId };

    const payload: JsonObject = {
      event: "message.received",
      source: EXTENSION_NAME,
      session_id: sessionId,
      message_id: messageId,
      working_dir: root,
      last_user_message: String(event.prompt || ""),
      recent_tool_calls: recentToolCalls.slice(-40),
    };

    const script = join(root, ".lazy-harness", "hooks", "lifecycle", "on-message-received.sh");
    const hook = existsSync(script) ? runHook(script, payload, root) : { stdout: "", stderr: "", status: 0 };
    const body = hookInjectBody(hook.stdout) ?? [
      "REMINDER. Harness-first search/read debt before response.",
      "- Pi lazy-harness package loaded; inspect real .lazy-harness records/source/tests before host-specific claims or mutation.",
      "- Mutation remains guarded by the generic search/read evidence guard.",
    ].join("\n");

    if (String(event.systemPrompt || "").includes(body)) return undefined;
    return { systemPrompt: `${event.systemPrompt || ""}\n\n${body}` };
  });

  pi.on("tool_call", async (event: any, ctx: any) => {
    const root = findLazyRoot(ctx.cwd);
    if (!root) return undefined;

    const packet = activePacket && activePacket.root === root
      ? activePacket
      : { root, sessionId: `pi:${stableHash(ctx.cwd)}`, messageId: `pi:${stableHash("no-active-packet")}` };

    const payload: JsonObject = {
      event: "tool.execute.before",
      source: EXTENSION_NAME,
      session_id: packet.sessionId,
      message_id: packet.messageId,
      working_dir: root,
      tool: normalizePiTool(event.toolName, event.input || {}),
      recent_tool_calls: recentToolCalls.slice(-40),
    };

    const script = join(root, ".lazy-harness", "hooks", "lifecycle", "on-tool-execute-before.sh");
    if (!existsSync(script)) return undefined;
    const hook = runHook(script, payload, root);
    const reason = denyReason(hook.stdout, hook.stderr);
    if (reason) return { block: true, reason };
    return undefined;
  });

  pi.on("tool_result", async (event: any) => {
    rememberToolCall({
      ...normalizePiTool(event.toolName, event.input || {}),
      toolCallId: String(event.toolCallId || ""),
      is_error: Boolean(event.isError),
      result_preview: previewContent(event.content),
    });
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
