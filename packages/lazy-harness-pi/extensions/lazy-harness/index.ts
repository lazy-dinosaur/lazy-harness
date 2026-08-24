import { SessionManager, type ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, realpathSync, renameSync, writeFileSync } from "node:fs";
import { dirname, isAbsolute, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const EXTENSION_NAME = "lazy-harness";
const EXTENSION_RUNTIME_MARKER = "lh-pi-read-debt-steering-20260701";
const MAX_RECENT_TOOL_CALLS = 80;
const DEFAULT_TIMEOUT_MS = Number(process.env.LAZY_HARNESS_PI_HOOK_TIMEOUT_MS || 15000);
const AGENT_END_TRACE_ENV = "LAZY_PI_AGENT_END_TRACE";
const AGENT_END_TRACE_NAME = "pi-agent-end-trace.jsonl";
const MAX_AGENT_END_TRACE_MESSAGE_SHAPES = 40;
const MAX_AGENT_END_TRACE_CONTENT_KINDS = 12;
const MAX_AGENT_END_TRACE_TOOL_NAMES = 40;
const MAX_AGENT_END_TRACE_ROWS = 50;
const MAX_AGENT_END_TRACE_METADATA_CHARS = 128;
const RECORD_READER_ROLE_MARKER = "LAZY_HARNESS_ROLE: record-reader/v2";
const RECORD_READER_PROFILE = "record-reader/v2";

type JsonObject = Record<string, unknown>;
type ReadDebtStatus = "armed" | "reused-work-unit" | "not-armed-synthetic" | "not-armed-hook-empty" | "not-armed-hook-timeout" | "not-armed-hook-error";
type HookResult = { stdout: string; stderr: string; status: number | null; signal?: string | null; error?: string };
type LazyAgentRole = "record-reader";
type ActivePacket = { root: string; sessionId: string; messageId: string; readDebtStatus: ReadDebtStatus; readDebtDetail?: string; role?: LazyAgentRole };

type RecentToolCall = {
  name: string;
  args: JsonObject;
  args_preview?: string;
  edit_target?: string;
  toolCallId?: string;
  evidence_epoch?: number;
  is_error?: boolean;
  result_preview?: unknown;
};

type WorkUnitEvidence = {
  mapped: boolean;
  recordHashes: Map<string, string>;
};

const recentToolCallsByRoot = new Map<string, RecentToolCall[]>();
const workUnitEvidenceByRoot = new Map<string, WorkUnitEvidence>();
const activePacketsByRoot = new Map<string, ActivePacket>();
const lastAdvisoryByRoot = new Map<string, { hash: string; count: number; chainCount: number; body: string }>();
const lastInputByRoot = new Map<string, { text: string; streamingBehavior?: string; source?: string; at: number }>();
// Every normal turn and non-extension mid-turn steer advances a root-scoped
// evidence epoch. Tool calls retain their start epoch, and completed calls retain
// their completion epoch, so agent_end can project only the current turn while
// late results from an older turn/steer cannot repopulate current evidence.
const evidenceEpochByRoot = new Map<string, number>();
const toolCallEpochsByRoot = new Map<string, Map<string, number>>();
const MAX_ADVISORY_CONTINUATIONS = 2;
const MAX_ADVISORY_CHAIN_CONTINUATIONS = 1;
// Runtime-neutral mid-turn re-grounding state (see the "context" handler).
const pendingRegroundByRoot = new Map<string, boolean>();
const regroundBodyByRoot = new Map<string, string>();
const REGROUND_MUTATION_TOOLS = new Set(["edit", "write", "multiedit", "patch", "apply_patch"]);
const MUTATION_TOOL_NAMES = new Set(["edit", "write", "multiedit", "patch", "apply_patch"]);
const READ_ONLY_SHELL_RE = /^\s*(?:cd\s+[^;&|]+\s*(?:&&|;)\s*)?(?:(?:\.lazy-harness\/bin\/lazy|lazy)\s+map|pwd|ls|tree|cat|grep|rg|find|git\s+(?:status|diff|show|log|rev-parse))\b/is;
const ACTION_NAME_RE = /(?:^|[_:.\-])(write|edit|patch|apply_patch|create|update|delete|remove|send|merge|push|upload|click|type|fill|press|select|drag|drop|navigate|run|close|open|schedule)(?:$|[_:.\-])/i;

function stableHash(value: unknown): string {
  return createHash("sha256").update(String(value ?? "")).digest("hex").slice(0, 16);
}

const RECORD_EVIDENCE_PATH_RE = /\.lazy-harness\/(?:domain|spec|behavior|tests|decisions|ssot|planning|plans)\/[A-Za-z0-9_./-]+\.(?:md|xml|json)/g;
const RECORD_EVIDENCE_TOOLS = new Set(["read", "read_symbol", "read_enclosing", "module_report"]);

function hashFile(path: string): string | undefined {
  try {
    return stableHash(readFileSync(path, "utf8"));
  } catch {
    return undefined;
  }
}

function workUnitEvidenceValid(root: string): boolean {
  const evidence = workUnitEvidenceByRoot.get(root);
  if (!evidence?.mapped || evidence.recordHashes.size === 0) return false;
  for (const [relativePath, expectedHash] of evidence.recordHashes) {
    if (hashFile(join(root, relativePath)) !== expectedHash) return false;
  }
  return true;
}

function observeEvidenceCall(root: string, evidence: WorkUnitEvidence, name: string, args: JsonObject): void {
  const normalizedName = name.toLowerCase();
  const blob = JSON.stringify(args ?? {});
  if (/(?:\.lazy-harness\/bin\/lazy|\blazy)\s+map\s+--overview\b/.test(blob)) evidence.mapped = true;
  const leafName = normalizedName.split(/[.:]/).pop() ?? normalizedName;
  if (RECORD_EVIDENCE_TOOLS.has(leafName)) {
    for (const relativePath of blob.match(RECORD_EVIDENCE_PATH_RE) ?? []) {
      const digest = hashFile(join(root, relativePath));
      if (digest) evidence.recordHashes.set(relativePath, digest);
    }
  }
  const nested = (args.tool_calls ?? args.toolCalls ?? args.tool_uses) as unknown;
  if (!Array.isArray(nested)) return;
  for (const item of nested) {
    if (!item || typeof item !== "object") continue;
    const call = item as Record<string, unknown>;
    const nestedName = String(call.recipient_name ?? call.tool ?? call.name ?? call.toolName ?? "");
    const nestedArgs = (call.parameters ?? call.input ?? call.args ?? {}) as JsonObject;
    observeEvidenceCall(root, evidence, nestedName, nestedArgs);
  }
}

function observeWorkUnitEvidence(root: string, name: string, args: JsonObject): void {
  const evidence = workUnitEvidenceByRoot.get(root) ?? { mapped: false, recordHashes: new Map<string, string>() };
  observeEvidenceCall(root, evidence, name, args);
  workUnitEvidenceByRoot.set(root, evidence);
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

function runHook(scriptPath: string, payload: JsonObject, root: string): HookResult {
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
    signal: completed.signal,
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

// Canonical lifecycle payload: on-response-completed helpers read a
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

function utf8ByteLength(value: string): number {
  return new TextEncoder().encode(value).byteLength;
}

function boundedTraceMetadata(value: unknown, maxChars = MAX_AGENT_END_TRACE_METADATA_CHARS): string {
  return String(value ?? "").slice(0, maxChars);
}

function traceContentShape(content: unknown): { contentPartCount: number; contentKinds: string[]; contentKindsTruncated: boolean } {
  const parts = Array.isArray(content) ? content : content == null ? [] : [content];
  const contentKinds = parts.slice(0, MAX_AGENT_END_TRACE_CONTENT_KINDS).map((part) => {
    if (typeof part === "string") return "string";
    if (part && typeof part === "object" && typeof (part as { type?: unknown }).type === "string") {
      return boundedTraceMetadata((part as { type: string }).type, 64);
    }
    return part == null ? "none" : typeof part;
  });
  return {
    contentPartCount: parts.length,
    contentKinds,
    contentKindsTruncated: parts.length > MAX_AGENT_END_TRACE_CONTENT_KINDS,
  };
}

function traceMessageShapes(messages: unknown): Array<{ role: string; contentPartCount: number; contentKinds: string[]; contentKindsTruncated: boolean }> {
  if (!Array.isArray(messages)) return [];
  return messages.slice(-MAX_AGENT_END_TRACE_MESSAGE_SHAPES).map((message) => {
    const item = message && typeof message === "object" ? message as { role?: unknown; content?: unknown } : {};
    return {
      role: boundedTraceMetadata(typeof item.role === "string" ? item.role : "unknown", 64),
      ...traceContentShape(item.content),
    };
  });
}

function traceTextFingerprint(value: string): { present: boolean; bytes: number; hash: string | null } {
  return {
    present: value.length > 0,
    bytes: utf8ByteLength(value),
    hash: value.length > 0 ? stableHash(value) : null,
  };
}

function agentEndTracePath(root: string, payload: JsonObject): string | undefined {
  const explicitRuntimeRoot = String(process.env.LAZY_RUNTIME_ROOT || "").trim();
  if (explicitRuntimeRoot) return join(resolve(explicitRuntimeRoot), "logs", AGENT_END_TRACE_NAME);

  const helper = join(root, ".lazy-harness", "hooks", "lifecycle", "helpers", "runtime_paths.py");
  if (!existsSync(helper)) return undefined;
  const runtimePayload = JSON.stringify({ session_id: payload.session_id });
  const completed = spawnSync(process.env.PYTHON_BIN || "python3", [helper, "log-path", runtimePayload, AGENT_END_TRACE_NAME], {
    cwd: root,
    encoding: "utf8",
    timeout: DEFAULT_TIMEOUT_MS,
    env: { ...process.env, LAZY_HOST_ROOT: root },
  });
  if (completed.status !== 0) return undefined;
  const resolvedPath = String(completed.stdout || "").trim();
  return resolvedPath ? resolve(resolvedPath) : undefined;
}

function writeBoundedAgentEndTrace(tracePath: string, row: Record<string, unknown>): void {
  const existingLines = existsSync(tracePath)
    ? readFileSync(tracePath, "utf8").split(/\r?\n/).filter(Boolean)
    : [];
  const retained = existingLines.slice(-(MAX_AGENT_END_TRACE_ROWS - 1));
  retained.push(JSON.stringify(row));
  const tempPath = `${tracePath}.tmp-${process.pid}-${Date.now()}`;
  writeFileSync(tempPath, `${retained.join("\n")}\n`, { encoding: "utf8", flag: "w", mode: 0o600 });
  renameSync(tempPath, tracePath);
}

function writeAgentEndTrace(
  root: string,
  payload: JsonObject,
  messages: unknown,
  recentToolCalls: RecentToolCall[],
  hook: HookResult,
  advisoryBody: string | undefined,
): void {
  if (process.env[AGENT_END_TRACE_ENV] !== "1") return;
  try {
    const tracePath = agentEndTracePath(root, payload);
    if (!tracePath) return;
    const messageList = Array.isArray(messages) ? messages : [];
    const assistantResponse = String(payload.assistant_response || "");
    const lastUserMessage = String(payload.last_user_message || "");
    const row = {
      schemaVersion: "pi-agent-end-trace/v1",
      timestamp: new Date().toISOString(),
      event: "pi.agent_end.response.completed",
      rootHash: stableHash(root),
      sessionHash: stableHash(payload.session_id),
      messageCount: messageList.length,
      messageShapesTruncated: messageList.length > MAX_AGENT_END_TRACE_MESSAGE_SHAPES,
      messageShapes: traceMessageShapes(messageList),
      assistantResponse: traceTextFingerprint(assistantResponse),
      lastUserMessage: traceTextFingerprint(lastUserMessage),
      recentToolNames: recentToolCalls
        .slice(-MAX_AGENT_END_TRACE_TOOL_NAMES)
        .map((call) => boundedTraceMetadata(call.name || "unknown")),
      hook: {
        status: hook.status,
        signal: hook.signal ? boundedTraceMetadata(hook.signal, 32) : null,
        error: Boolean(hook.error),
        stdout: traceTextFingerprint(hook.stdout || ""),
        stderr: traceTextFingerprint(hook.stderr || ""),
      },
      advisory: traceTextFingerprint(advisoryBody || ""),
    };
    mkdirSync(dirname(tracePath), { recursive: true, mode: 0o700 });
    writeBoundedAgentEndTrace(tracePath, row);
  } catch {
    // Diagnostics are opt-in and fail-open; tracing must never alter agent behavior.
  }
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

function lazyAgentRole(systemPrompt: unknown): LazyAgentRole | undefined {
  return systemPromptIncludesBody(systemPrompt, RECORD_READER_ROLE_MARKER) ? "record-reader" : undefined;
}

function recordReaderReminder(root: string): string {
  return [
    `Lazy-Harness role profile: ${RECORD_READER_PROFILE}`,
    `Root: ${root}`,
    "Use the package-owned Record Reader system prompt as the complete role contract.",
    "Require one explicit Work Packet mode: candidate-map proposes non-authoritative coverage; claim-evidence loads one Parent-approved evidence bundle.",
    "The Parent alone owns complete overview discovery, candidate-map approval, fixed-point reopening, semantic authority, and all read debt.",
    "Run identity probes as three separate shell calls: pwd, git rev-parse --show-toplevel, then git rev-parse HEAD; compound commands are blocked.",
    "The execution transport must disable native supervisor/intercom coordination for this role; never call contact_supervisor.",
    "Runtime tool-call soft and hard limits must both equal the packet tool budget, including one reserved final structured_output call; output uses a separate 6000 soft target and 12000 hard cap.",
    "New runs use compact admission v2: the model echoes one contractDigest and normalized F/I/N/V/R/Q/B references; deterministic admission binds the full Parent envelope, one record/range table, one coverage authority, soft-target warnings, hard-cap overflow, and success closure; finish with Pi Subagents' runtime-owned structured_output tool.",
    "Do not run an overview, read product/framework source, mutate files, invoke subagents, or claim that a packet proves global completeness.",
  ].join("\n");
}

function recordReaderShellAllowed(root: string, args: JsonObject): boolean {
  const command = shellCommand(args).trim();
  if (!command || /[;&|><`$()]/.test(command)) return false;
  const concreteMap = command.match(/^\.lazy-harness\/bin\/lazy\s+map\s+([A-Za-z0-9_./:#-]+)\s+--format=md\s+--limit=8$/i);
  if (concreteMap) {
    const node = concreteMap[1];
    if (!node.startsWith("-") && !node.startsWith("/") && !node.split("/").includes("..")) return true;
  }
  const contentHash = command.match(/^git\s+hash-object\s+--\s+(.+)$/i);
  if (contentHash && recordReaderCanonicalPath(root, contentHash[1], true)) return true;
  return /^(?:pwd|git\s+rev-parse\s+(?:HEAD|--show-toplevel))$/i.test(command);
}

function recordReaderCanonicalPath(root: string, raw: string, requireBody: boolean): string | undefined {
  if (!raw.trim()) return undefined;
  let absolute: string;
  try {
    absolute = realpathSync(resolve(root, raw));
  } catch {
    return undefined;
  }
  const rel = relative(root, absolute).replace(/\\/g, "/");
  if (rel.startsWith("../") || rel === "..") return undefined;
  const canonical = /^\.lazy-harness\/(?:domain|spec|behavior|tests|decisions|ssot|planning|plans)(?:\/[A-Za-z0-9_./-]+)?$/;
  if (!canonical.test(rel)) return undefined;
  if (requireBody && !/\.(?:md|xml|json)$/.test(rel)) return undefined;
  return rel;
}

function recordReaderRecordPathAllowed(root: string, args: JsonObject): boolean {
  const raw = String(args.path || args.file_path || args.filePath || "");
  return recordReaderCanonicalPath(root, raw, true) !== undefined;
}

function recordReaderGrepAllowed(root: string, args: JsonObject): boolean {
  const raw = String(args.path || "");
  if (!recordReaderCanonicalPath(root, raw, false)) return false;
  const pattern = String(args.pattern || "");
  if (!pattern.trim() || pattern.length > 240 || /[\r\n]/.test(pattern)) return false;
  const context = Number(args.context ?? 0);
  const limit = Number(args.limit ?? 100);
  if (!Number.isFinite(context) || context < 0 || context > 3) return false;
  if (!Number.isFinite(limit) || limit < 1 || limit > 100) return false;
  const glob = String(args.glob || "").trim();
  if (glob && !/^(?:\*\*\/)?\*\.(?:md|xml|json)$/.test(glob)) return false;
  return true;
}

function recordReaderStructuredOutputAllowed(): boolean {
  const capturePath = String(process.env.PI_SUBAGENT_STRUCTURED_OUTPUT_CAPTURE || "").trim();
  const schemaPath = String(process.env.PI_SUBAGENT_STRUCTURED_OUTPUT_SCHEMA || "").trim();
  return isAbsolute(capturePath) && isAbsolute(schemaPath) && existsSync(schemaPath);
}

function recordReaderToolDenial(root: string, name: string, args: JsonObject): string | undefined {
  const lower = name.toLowerCase();
  if (lower === "structured_output" && recordReaderStructuredOutputAllowed()) return undefined;
  if (lower === "read" && recordReaderRecordPathAllowed(root, args)) return undefined;
  if (lower === "grep" && recordReaderGrepAllowed(root, args)) return undefined;
  if (lower === "bash" && recordReaderShellAllowed(root, args)) return undefined;
  return [
    "[lazy-harness record-reader scope] tool blocked by the records-only role profile.",
    `Root: ${root}`,
    `Tool: ${name}`,
    "Allowed: Pi Subagents' internal `structured_output` protocol tool only while its absolute schema/capture runtime paths are active, exact concrete-node `.lazy-harness/bin/lazy map <node> --format=md --limit=8`, root/revision probes, exact canonical-record `git hash-object`, bounded grep inside one canonical record layer, and direct canonical record-body reads under domain/spec/behavior/tests/decisions/ssot/planning/plans.",
    "Blocked: complete overview, source reads, mutation, general shell search, root-wide grep, file output, subagents, and external tools.",
    "Return `invalid-packet`, `needs-remap`, `overflow`, or another explicit non-success status instead of expanding scope.",
  ].join("\n");
}
function shellCommand(args: JsonObject): string {
  return String(args.command || args.cmd || args.text || "");
}

function isReadOnlyShell(args: JsonObject): boolean {
  const command = shellCommand(args);
  if (!command.trim()) return false;
  if (/\b(rm|mv|cp|mkdir|touch|tee|python3?\s+-|node\s+-|bun\s+(?:run|x|test)|npm|pnpm|yarn|gh\s+(?:pr\s+(?:create|edit|merge)|issue\s+create))\b/i.test(command)) return false;
  return READ_ONLY_SHELL_RE.test(command);
}

function isActionTool(name: string, args: JsonObject): boolean {
  const lower = name.toLowerCase();
  if (["read", "grep", "find", "ls"].includes(lower)) return false;
  if (lower === "batch" && Array.isArray((args as Record<string, unknown>).tool_calls)) {
    return ((args as Record<string, unknown>).tool_calls as unknown[]).some((call) => {
      const c = (call && typeof call === "object" ? call : {}) as Record<string, unknown>;
      const nestedName = String(c.tool || c.name || c.toolName || "");
      const nestedArgs = (c.parameters && typeof c.parameters === "object" ? c.parameters : c.input && typeof c.input === "object" ? c.input : {}) as JsonObject;
      return isActionTool(nestedName, nestedArgs);
    });
  }
  if (MUTATION_TOOL_NAMES.has(lower)) return true;
  if (lower === "bash") return !isReadOnlyShell(args);
  if (ACTION_NAME_RE.test(name)) return true;
  if (lower.startsWith("mcp__")) return true;
  return false;
}

function readDebtLabel(status: ReadDebtStatus): string {
  if (status === "armed" || status === "reused-work-unit") return status;
  if (status === "not-armed-synthetic") return "not-armed(synthetic-turn)";
  if (status === "not-armed-hook-timeout") return "not-armed(hook-timeout)";
  if (status === "not-armed-hook-error") return "not-armed(hook-error)";
  return "not-armed(hook-empty)";
}

function readDebtArmed(status: ReadDebtStatus): boolean {
  return status === "armed" || status === "reused-work-unit";
}

function firstLine(value: string, max = 120): string {
  return value.trim().split(/\r?\n/)[0]?.replace(/\s+/g, " ").slice(0, max) || "";
}

function hookErrorDetail(hook: HookResult, hookBody?: string): string | undefined {
  if (hook.error) {
    if (hook.error.includes("ETIMEDOUT")) return `timeout>${DEFAULT_TIMEOUT_MS}ms`;
    return hook.error.replace(/\s+/g, " ").slice(0, 120);
  }
  if (hook.signal) return `signal=${hook.signal}`;
  if (hook.status !== null && hook.status !== 0) return `exit=${hook.status}${hook.stderr.trim() ? ` stderr=${firstLine(hook.stderr, 100)}` : ""}`;
  if (!hookBody && hook.stderr.trim()) return `stderr=${firstLine(hook.stderr, 120)}`;
  if (!hookBody && hook.stdout.trim()) return `unparseable-stdout=${firstLine(hook.stdout, 120)}`;
  if (!hookBody) return "empty-output";
  return undefined;
}

function classifyReadDebtStatus(prompt: string, hook: HookResult, hookBody: string | undefined): ReadDebtStatus {
  if (hookBody) return "armed";
  if (!prompt.trim()) return "not-armed-synthetic";
  if (hook.error?.includes("ETIMEDOUT")) return "not-armed-hook-timeout";
  if (hook.error || (hook.status !== null && hook.status !== 0)) return "not-armed-hook-error";
  return "not-armed-hook-empty";
}

function steeringReminder(root: string, status: ReadDebtStatus, detail?: string): string {
  const statusLabel = readDebtLabel(status);
  const synthetic = status === "not-armed-synthetic";
  return [
    synthetic
      ? "REMINDER. Synthetic/steering turn; read-debt was not armed."
      : `REMINDER. Work-unit grounding hook was not armed (${statusLabel}).`,
    `Root: ${root}`,
    detail ? `Hook detail: ${detail}` : undefined,
    "Do not make host-specific claims or mutations from memory.",
    "If project detail is needed, run `.lazy-harness/bin/lazy map --overview --complete --format=md`, drill into a concrete feature id / record path / graph id / source path / test path copied from the map, and read real records/source/tests before proceeding.",
    "Action tools remain guarded until a human turn arms read-debt or sufficient map/read evidence exists.",
  ].filter(Boolean).join("\n");
}

function armStatusMessage(root: string, status: ReadDebtStatus, detail?: string): string {
  const detailSuffix = detail ? ` hook=${detail.replace(/\s+/g, "_").slice(0, 80)}` : "";
  const phase = readDebtArmed(status) ? "phase=armed" : "phase=debug";
  return `lazy-harness read-debt: ${EXTENSION_RUNTIME_MARKER} root=${root} status=${readDebtLabel(status)} ${phase}${detailSuffix} tool-guard=ready`;
}

function readDebtNotArmedReason(root: string, name: string, status: ReadDebtStatus, detail?: string): string {
  return [
    "[lazy-harness read-debt not armed] action blocked before map/read evidence.",
    "",
    `Runtime marker: ${EXTENSION_RUNTIME_MARKER}`,
    `Root: ${root}`,
    `Tool: ${name}`,
    `Status: ${readDebtLabel(status)}`,
    detail ? `Hook detail: ${detail}` : undefined,
    "",
    "This means the turn-start read-debt reminder did not arm, so lazy-harness cannot prove map/read evidence exists for this action yet.",
    "Recovery for the agent:",
    "  1. Stop the blocked action; do not retry the same mutation immediately.",
    "  2. Run: `.lazy-harness/bin/lazy map --overview --complete --format=md`.",
    "  3. Pick a concrete feature id, record path, graph id, source path, or test path from that map output; never invent a query string.",
    "  4. Run: `.lazy-harness/bin/lazy map <copied-node> --format=md --limit=8`.",
    "  5. Read the governing record(s) and linked source/tests, then state the evidence and retry only if the action is still needed.",
    "  6. If Status is hook-timeout/hook-error/hook-empty, report the visible `lazy-harness read-debt` marker and hook detail; after code/package update, restart/reload Pi/OMP if the marker still says `lazy-harness armed` or `read-debt=NOT-ARMED`.",
  ].filter(Boolean).join("\n");
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

function currentEvidenceEpoch(root: string): number {
  return evidenceEpochByRoot.get(root) ?? 0;
}

function toolCallKey(event: any): string {
  const toolCallId = String(event?.toolCallId || "").trim();
  if (toolCallId) return toolCallId;
  let input = "";
  try { input = JSON.stringify(event?.input || {}); } catch { input = String(event?.input || ""); }
  return `anonymous:${stableHash(`${String(event?.toolName || "")}\n${input}`)}`;
}

function markToolCallStarted(root: string, event: any): void {
  let epochs = toolCallEpochsByRoot.get(root);
  if (!epochs) {
    epochs = new Map<string, number>();
    toolCallEpochsByRoot.set(root, epochs);
  }
  epochs.set(toolCallKey(event), currentEvidenceEpoch(root));
  while (epochs.size > MAX_RECENT_TOOL_CALLS * 2) {
    const oldest = epochs.keys().next().value as string | undefined;
    if (!oldest) break;
    epochs.delete(oldest);
  }
}

function toolResultBelongsToCurrentEvidenceEpoch(root: string, event: any): boolean {
  const epochs = toolCallEpochsByRoot.get(root);
  const key = toolCallKey(event);
  const startedEpoch = epochs?.get(key);
  epochs?.delete(key);
  // Older runtimes/tests may omit tool_call events. Preserve their pre-turn
  // behavior only at epoch zero; after any turn/steer boundary, accept results
  // only when the corresponding call started in the current evidence epoch.
  if (startedEpoch === undefined) return currentEvidenceEpoch(root) === 0;
  return startedEpoch === currentEvidenceEpoch(root);
}

function advanceEvidenceEpoch(root: string): number {
  const nextEpoch = currentEvidenceEpoch(root) + 1;
  evidenceEpochByRoot.set(root, nextEpoch);
  return nextEpoch;
}

function rearmEvidenceAfterSteer(root: string): number {
  const nextEpoch = advanceEvidenceEpoch(root);
  recentToolCallsByRoot.set(root, []);
  return nextEpoch;
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

function resolveTargetPath(ctx: any, targetPath: string): string {
  const raw = String(targetPath || "").trim();
  if (!raw) throw new Error("targetPath is required");
  return resolve(resolveInvocationCwd(undefined, ctx), raw.replace(/^~(?=\/|$)/, process.env.HOME || "~"));
}

async function switchToProjectSession(ctx: any, target: string, prompt?: string): Promise<string> {
  if (!existsSync(join(target, ".lazy-harness", "bin", "lazy"))) {
    throw new Error(`target is not a lazy-harness project: ${target}`);
  }
  if (typeof ctx.switchSession !== "function") {
    throw new Error("Pi command context does not expose switchSession; use /lazy-move from an interactive command context");
  }
  const session = SessionManager.create(target);
  const sessionFile = session.getSessionFile();
  if (!sessionFile) throw new Error(`failed to create persisted session for ${target}`);
  await ctx.switchSession(sessionFile, {
    withSession: async (nextCtx: any) => {
      nextCtx.ui?.notify?.(`lazy-harness moved to ${target}`, "info");
      if (prompt && typeof nextCtx.sendUserMessage === "function") {
        await nextCtx.sendUserMessage(prompt);
      }
    },
  });
  return sessionFile;
}

async function createWorktree(pi: ExtensionAPI, ctx: any, root: string, target: string, branch?: string, baseRef?: string): Promise<string> {
  const args = ["worktree", "add"];
  if (branch && branch.trim()) args.push("-b", branch.trim());
  args.push(target);
  if (baseRef && baseRef.trim()) args.push(baseRef.trim());
  const result = await pi.exec("git", args, { cwd: root, timeout: 120000, signal: ctx.signal });
  const stdout = String((result as any).stdout ?? "").trim();
  const stderr = String((result as any).stderr ?? "").trim();
  const code = (result as any).exitCode ?? (result as any).code ?? 0;
  if (code) throw new Error(`git ${args.join(" ")} failed exit=${code}\n${[stdout, stderr].filter(Boolean).join("\n")}`);
  return [stdout, stderr].filter(Boolean).join("\n");
}

export default function lazyHarnessPi(pi: ExtensionAPI) {
  pi.on("input", async (event: any, ctx: any) => {
    const root = findLazyRootForInvocation(event, ctx);
    if (!root) return undefined;
    lastInputByRoot.set(root, {
      text: String(event.text || ""),
      streamingBehavior: typeof event.streamingBehavior === "string" ? event.streamingBehavior : undefined,
      source: typeof event.source === "string" ? event.source : undefined,
      at: Date.now(),
    });
    // Pi's default Enter steers mid-turn, which skips before_agent_start entirely.
    // before_agent_start entirely — the new instruction would silently inherit the
    // previous topic's read-debt evidence and lose the §2.1 record-search push.
    // Organic fix (ADR 0041/0048/0051): a real mid-turn steer starts a fresh
    // work unit, writes one compact first-grounding packet, and clears cached
    // fingerprints. It does not schedule a second context reminder.
    if (event.streamingBehavior === "steer" && event.source !== "extension") {
      const steerText = String(event.text || "");
      if (steerText.trim()) {
        const role = activePacketsByRoot.get(root)?.role;
        const sessionId = `pi:${stableHash(root)}`;
        const messageId = `pi:${stableHash(`${Date.now()}:${steerText}`)}`;
        if (role) {
          const readDebtStatus: ReadDebtStatus = "armed";
          activePacketsByRoot.set(root, { root, sessionId, messageId, readDebtStatus, role });
          const body = recordReaderReminder(root);
          return {
            action: "transform" as const,
            text: `${steerText}\n\n<system-reminder>\n${body}\n</system-reminder>`,
          };
        }
        rearmEvidenceAfterSteer(root); // invalidate Parent evidence for the previous instruction
        workUnitEvidenceByRoot.delete(root); // explicit steer starts a fresh work unit for the Parent
        pendingRegroundByRoot.delete(root);
        regroundBodyByRoot.delete(root);
        const payload: JsonObject = {
          event: "message.received", source: EXTENSION_NAME, session_id: sessionId,
          message_id: messageId, working_dir: root, last_user_message: steerText, recent_tool_calls: [],
        };
        const script = join(root, ".lazy-harness", "hooks", "lifecycle", "on-message-received.sh");
        const hook: HookResult = existsSync(script)
          ? runHook(script, payload, root)
          : { stdout: "", stderr: "", status: 127, error: "hook-missing:on-message-received.sh" };
        const hookBody = hookInjectBody(hook.stdout);
        const readDebtStatus = classifyReadDebtStatus(steerText, hook, hookBody);
        const readDebtDetail = readDebtArmed(readDebtStatus) ? undefined : hookErrorDetail(hook, hookBody);
        activePacketsByRoot.set(root, { root, sessionId, messageId, readDebtStatus, readDebtDetail });
        const body = hookBody ?? steeringReminder(root, readDebtStatus, readDebtDetail);
        return {
          action: "transform" as const,
          text: `${steerText}\n\n<system-reminder>\n${body}\n</system-reminder>`,
        };
      }
    }
    return undefined;
  });

  pi.on("before_agent_start", async (event: any, ctx: any) => {
    const cwd = resolveInvocationCwd(event, ctx);
    const root = findLazyRoot(cwd);
    if (!root) return undefined;

    const role = lazyAgentRole(event.systemPrompt);
    if (role) {
      const sessionId = `pi:${stableHash(cwd)}`;
      const messageId = `pi:${stableHash(`${Date.now()}:${event.prompt || ""}`)}`;
      // Reader children must not establish, invalidate, or satisfy Parent
      // work-unit evidence, even in a sequential same-process fake runtime.
      const readDebtStatus: ReadDebtStatus = "armed";
      activePacketsByRoot.set(root, { root, sessionId, messageId, readDebtStatus, role });
      const profile = RECORD_READER_PROFILE;
      const inject = recordReaderReminder(root);
      const message = { customType: EXTENSION_NAME, content: `${armStatusMessage(root, readDebtStatus)} profile=${profile}`, display: true };
      if (systemPromptIncludesBody(event.systemPrompt, inject)) return { message };
      return { message, systemPrompt: appendSystemPromptBody(event.systemPrompt, inject) };
    }

    const sessionId = `pi:${stableHash(cwd)}`;
    const messageId = `pi:${stableHash(`${Date.now()}:${event.prompt || ""}`)}`;
    advanceEvidenceEpoch(root); // fresh turn boundary: exclude prior-turn calls from agent_end
    pendingRegroundByRoot.delete(root); // fresh turn: clear mid-turn re-grounding state
    regroundBodyByRoot.delete(root);
    // A queued lazy-harness follow-up starts a new runtime turn too. Keep the
    // advisory cap for that synthetic turn, but reset it when a real user prompt
    // differs from the last advisory body so the next human request can get one
    // fresh follow-up if it hits a new gate.
    const prevAdvisory = lastAdvisoryByRoot.get(root);
    if (prevAdvisory && String(event.prompt || "") !== prevAdvisory.body) {
      lastAdvisoryByRoot.delete(root);
    }
    await ensureAskToolActive(pi); // keep OMP's native `ask` selector available for §2.3 option gates
    const promptText = String(event.prompt || "");
    // Reuse validated map/record fingerprints for the current work unit. A new
    // Pi/OMP session or explicit steer starts a new work unit; changed/deleted
    // governing records invalidate reuse without replaying their bodies.
    if (workUnitEvidenceValid(root)) {
      const readDebtStatus: ReadDebtStatus = "reused-work-unit";
      activePacketsByRoot.set(root, { root, sessionId, messageId, readDebtStatus });
      return { message: { customType: EXTENSION_NAME, content: armStatusMessage(root, readDebtStatus), display: true } };
    }
    workUnitEvidenceByRoot.delete(root);

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
    const hook: HookResult = existsSync(script)
      ? runHook(script, payload, root)
      : { stdout: "", stderr: "", status: 127, error: "hook-missing:on-message-received.sh" };
    const hookBody = hookInjectBody(hook.stdout);
    const readDebtStatus = classifyReadDebtStatus(promptText, hook, hookBody);
    const readDebtDetail = readDebtArmed(readDebtStatus) ? undefined : hookErrorDetail(hook, hookBody);
    activePacketsByRoot.set(root, { root, sessionId, messageId, readDebtStatus, readDebtDetail });
    const body = hookBody ?? steeringReminder(root, readDebtStatus, readDebtDetail);

    // Force-load the FULL .lazy-harness/AGENTS.md grammar into the
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

    const message = { customType: EXTENSION_NAME, content: armStatusMessage(root, readDebtStatus, readDebtDetail), display: true };
    if (systemPromptIncludesBody(event.systemPrompt, inject)) return { message };
    return { message, systemPrompt: appendSystemPromptBody(event.systemPrompt, inject) };
  });

  pi.on("tool_call", async (event: any, ctx: any) => {
    const cwd = resolveInvocationCwd(event, ctx);
    const root = findLazyRoot(cwd);
    if (!root) return undefined;

    const packet = activePacketsByRoot.get(root)
      ? activePacketsByRoot.get(root)!
      : { root, sessionId: `pi:${stableHash(cwd)}`, messageId: `pi:${stableHash("no-active-packet")}`, readDebtStatus: "not-armed-hook-empty" as ReadDebtStatus };

    const normalized = normalizePiTool(event.toolName, event.input || {});
    if (packet.role) {
      const reason = recordReaderToolDenial(root, normalized.name, normalized.args);
      if (reason) return { block: true, reason };
      return undefined;
    }
    if (!readDebtArmed(packet.readDebtStatus) && isActionTool(normalized.name, normalized.args)) {
      return { block: true, reason: readDebtNotArmedReason(root, normalized.name, packet.readDebtStatus, packet.readDebtDetail) };
    }

    const payload: JsonObject = {
      event: "tool.execute.before",
      source: EXTENSION_NAME,
      session_id: packet.sessionId,
      message_id: packet.messageId,
      working_dir: root,
      tool: normalized,
      recent_tool_calls: recentToolCallsForRoot(root).slice(-40),
    };

    const script = join(root, ".lazy-harness", "hooks", "lifecycle", "on-tool-execute-before.sh");
    if (existsSync(script)) {
      const hook = runHook(script, payload, root);
      const reason = denyReason(hook.stdout, hook.stderr);
      if (reason) return { block: true, reason };
    }
    markToolCallStarted(root, event);
    return undefined;
  });

  pi.on("tool_result", async (event: any, ctx: any) => {
    const root = findLazyRootFromEvent(event, ctx);
    if (!root) return undefined;
    if (activePacketsByRoot.get(root)?.role) return undefined;
    if (!toolResultBelongsToCurrentEvidenceEpoch(root, event)) return undefined;
    const normalized = normalizePiTool(event.toolName, event.input || {});
    if (!event.isError) observeWorkUnitEvidence(root, normalized.name, normalized.args);
    rememberToolCall(root, {
      ...normalized,
      args_preview: argsPreview(normalized.args),
      edit_target: editTargetPaths(normalized.args),
      toolCallId: String(event.toolCallId || ""),
      evidence_epoch: currentEvidenceEpoch(root),
      is_error: Boolean(event.isError),
      result_preview: previewContent(event.content),
    });
    // Re-ground only after the first successful mutation, never after reads/searches.
    // The hook is pointer-only and cannot replay maps, records, or policy catalogs.
    if (REGROUND_MUTATION_TOOLS.has(normalized.name.toLowerCase()) && !event.isError && !regroundBodyByRoot.has(root)) {
      pendingRegroundByRoot.set(root, true);
    }
    return undefined;
  });

  // "context" fires before each LLM call and can modify the messages sent to the model.
  // Work-unit grounding is already cached. After the first successful mutation,
  // inject one pointer-only continuation reminder; reads/searches never schedule it.
  // Failed hooks keep pending for a retry, while a valid body suppresses later
  // same-turn mutation retriggers.
  pi.on("context", async (event: any, ctx: any) => {
    try {
      const root = findLazyRoot(resolveInvocationCwd(event, ctx));
      if (!root) return undefined;
      if (activePacketsByRoot.get(root)?.role) return undefined;
      if (!pendingRegroundByRoot.get(root)) return undefined;
      let body = regroundBodyByRoot.get(root);
      if (body === undefined) {
        const script = join(root, ".lazy-harness", "hooks", "lifecycle", "on-context.sh");
        if (!existsSync(script)) return undefined;
        const payload: JsonObject = { event: "context", source: EXTENSION_NAME, working_dir: root, recent_tool_calls: recentToolCallsForRoot(root).slice(-40) };
        const hook = runHook(script, payload, root);
        if (hook.status !== 0 || hook.signal || hook.error) return undefined;
        body = hookInjectBody(hook.stdout);
        if (!body) return undefined;
        regroundBodyByRoot.set(root, body);
      }
      pendingRegroundByRoot.delete(root);

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
      : { root, sessionId: `pi:${stableHash(cwd)}`, messageId: `pi:${stableHash("no-active-packet")}`, readDebtStatus: "not-armed-hook-empty" as ReadDebtStatus };
    if (packet.role) return undefined;
    const messages = Array.isArray(event.messages) ? event.messages : [];
    const currentEpoch = currentEvidenceEpoch(root);
    const recentToolCalls = recentToolCallsForRoot(root)
      .filter((call) => call.evidence_epoch === currentEpoch)
      .slice(-40);
    const assistantResponse = lastMessageTextByRole(messages, "assistant");
    const lastUserMessage = lastMessageTextByRole(messages, "user");
    const payload: JsonObject = {
      event: "response.completed",
      source: EXTENSION_NAME,
      session_id: packet.sessionId,
      message_id: packet.messageId,
      working_dir: root,
      recent_tool_calls: recentToolCalls,
      // Canonical response-completed helpers walk the assistant response
      // prose and last user message (e.g. discovery-capture satisfaction #2).
      assistant_response: assistantResponse,
      last_user_message: lastUserMessage,
    };

    const script = join(root, ".lazy-harness", "hooks", "lifecycle", "on-response-completed.sh");
    if (!existsSync(script)) {
      writeAgentEndTrace(root, payload, messages, recentToolCalls, { stdout: "", stderr: "", status: 127, error: "hook-missing" }, undefined);
      return undefined;
    }
    const hook = runHook(script, payload, root);
    const body = hookInjectBody(hook.stdout);
    writeAgentEndTrace(root, payload, messages, recentToolCalls, hook, body);
    if (!body) {
      lastAdvisoryByRoot.delete(root); // gate resolved → reset continuation counter
      return undefined;
    }
    // Drive a continuation so the agent addresses the response-completed advisory.
    // Loop-safe on two axes: the SAME unresolved advisory drives at most
    // MAX_ADVISORY_CONTINUATIONS turns, and an alternating sequence of different
    // STOP advisories drives at most MAX_ADVISORY_CHAIN_CONTINUATIONS follow-up
    // turns before degrading to non-steering display. This prevents capture-gate
    // and rule-placement helpers from ping-ponging indefinitely.
    const advisoryHash = stableHash(body);
    const prevAdvisory = lastAdvisoryByRoot.get(root);
    const advisoryCount = prevAdvisory && prevAdvisory.hash === advisoryHash ? prevAdvisory.count + 1 : 1;
    const advisoryChainCount = prevAdvisory && prevAdvisory.hash !== advisoryHash ? prevAdvisory.chainCount + 1 : 1;
    lastAdvisoryByRoot.set(root, { hash: advisoryHash, count: advisoryCount, chainCount: advisoryChainCount, body });
    if (advisoryCount <= MAX_ADVISORY_CONTINUATIONS && advisoryChainCount <= MAX_ADVISORY_CHAIN_CONTINUATIONS && typeof (pi as any).sendUserMessage === "function") {
      (pi as any).sendUserMessage(body, { deliverAs: "followUp" });
    } else {
      ctx.ui?.notify?.(`lazy-harness advisory suppressed after follow-up cap\n${body}`.slice(0, 1800), "warning");
    }
    return undefined;
  });

  pi.registerCommand("lazy-move", {
    description: "Move Pi to another lazy-harness project/session. Usage: /lazy-move /path/to/project [--prompt text]",
    handler: async (args: string, ctx: any) => {
      const [targetArg, ...rest] = String(args || "").trim().split(/\s+/).filter(Boolean);
      const target = resolveTargetPath(ctx, targetArg || "");
      const promptIndex = rest.indexOf("--prompt");
      const prompt = promptIndex >= 0 ? rest.slice(promptIndex + 1).join(" ") : undefined;
      await switchToProjectSession(ctx, target, prompt);
    },
  });

  // Fail-open: older Pi/OMP runtimes (and the self-test smoke stub) may not expose
  // registerTool; the /lazy-move command remains the fallback surface.
  if (typeof (pi as any).registerTool === "function") pi.registerTool({
    name: "lazy_move_project",
    label: "Lazy Move Project",
    description: "Create an optional git worktree and switch Pi to another lazy-harness project/session when supported. Use when the user asks to move/switch to another repo/worktree.",
    promptSnippet: "Create a worktree if requested, then switch Pi to the target lazy-harness project when the runtime exposes switchSession.",
    promptGuidelines: [
      "Use lazy_move_project when the user asks to move/switch to another lazy-harness project or to create a worktree and continue there.",
      "lazy_move_project should only be used with an explicit targetPath/worktreePath from the user or from read project evidence; do not invent paths.",
    ],
    parameters: Type.Object({
      targetPath: Type.Optional(Type.String({ description: "Existing lazy-harness project path to move to. Required unless worktreePath is supplied." })),
      createWorktree: Type.Optional(Type.Boolean({ description: "Whether to create a git worktree before moving." })),
      worktreePath: Type.Optional(Type.String({ description: "Path for a new git worktree. Used as targetPath when createWorktree is true." })),
      branch: Type.Optional(Type.String({ description: "Optional new branch name for git worktree add -b." })),
      baseRef: Type.Optional(Type.String({ description: "Optional base ref for git worktree add." })),
      prompt: Type.Optional(Type.String({ description: "Optional prompt to send after switching session." })),
      autoSwitch: Type.Optional(Type.Boolean({ description: "Switch to the target project after preparation when ctx.switchSession is available. Defaults to true." })),
    }),
    async execute(_toolCallId: string, params: any, signal: AbortSignal | undefined, _onUpdate: any, ctx: any) {
      const root = findLazyRootForInvocation(undefined, ctx);
      if (!root) throw new Error("lazy-harness root not found from current cwd");
      const target = resolveTargetPath(ctx, params.createWorktree ? params.worktreePath : params.targetPath);
      let worktreeOutput = "";
      if (params.createWorktree) {
        worktreeOutput = await createWorktree(pi, { ...ctx, signal }, root, target, params.branch, params.baseRef);
      }
      if (!existsSync(join(target, ".lazy-harness", "bin", "lazy"))) {
        throw new Error(`target is not a lazy-harness project after preparation: ${target}`);
      }
      const autoSwitch = params.autoSwitch !== false;
      let switchedSessionFile = "";
      if (autoSwitch) {
        if (typeof ctx.switchSession === "function") {
          switchedSessionFile = await switchToProjectSession(ctx, target, params.prompt);
        } else {
          const promptSuffix = params.prompt ? ` --prompt ${String(params.prompt).replace(/\s+/g, " ")}` : "";
          return {
            content: [{
              type: "text",
              text: [
                `Prepared ${target}, but this tool context cannot switch sessions directly (ctx.switchSession unavailable).`,
                `Run /lazy-move ${target}${promptSuffix} from an interactive command context to switch.`,
                worktreeOutput,
              ].filter(Boolean).join("\n"),
            }],
            details: { targetPath: target, autoSwitch, switched: false, worktreeOutput },
          };
        }
      }
      const message = autoSwitch
        ? `Prepared ${target} and switched session${switchedSessionFile ? ` (${switchedSessionFile})` : ""}.`
        : `Prepared ${target}. Run /lazy-move ${target} to switch.`;
      return {
        content: [{ type: "text", text: [message, worktreeOutput].filter(Boolean).join("\n") }],
        details: { targetPath: target, autoSwitch, switched: Boolean(switchedSessionFile), switchedSessionFile, worktreeOutput },
      };
    },
  });
  // (registerTool guard ends here)

  pi.registerCommand("lazy-map", {
    description: "Run lazy map from the current project root. Usage: /lazy-map --overview --format=md --limit=20",
    handler: async (args: string, ctx: any) => runLazyCommand(pi, ctx, args || "--overview --format=md --limit=20", ["map"]),
  });

  pi.registerCommand("lazy-doctor", {
    description: "Run lazy doctor from the current project root.",
    handler: async (args: string, ctx: any) => runLazyCommand(pi, ctx, args, ["doctor"]),
  });

  pi.registerCommand("lazy-check", {
    description: "Run fast changed-file lazy validation from the current project root.",
    handler: async (args: string, ctx: any) => runLazyCommand(pi, ctx, args, ["check"]),
  });

  pi.registerCommand("lazy-validate", {
    description: "Run bounded lazy validation. Defaults to the fast plan; pass --plan standard once after final mutation.",
    handler: async (args: string, ctx: any) => runLazyCommand(pi, ctx, args || "--plan fast", ["validate"]),
  });

  pi.registerCommand("lazy-test", {
    description: "Run a fresh full lazy regression test. Prefer /lazy-check while editing and /lazy-validate --plan standard at the final boundary.",
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
