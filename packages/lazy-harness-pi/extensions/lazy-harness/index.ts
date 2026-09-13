import { SessionManager, type AgentToolResult, type ExtensionAPI, type ExtensionContext } from "@earendil-works/pi-coding-agent";
import { parseReaderResultPacket, type ReaderResultStatus } from "./reader-result.ts";
import { Type } from "typebox";
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, renameSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { CAPTURE_GUIDANCE, CaptureEvidence } from "./capture-evidence.ts";

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
const RECORD_READER_AGENT = "lazy-harness.record-reader";
const RECORD_READER_ROLE_MARKER = "LAZY_HARNESS_ROLE: record-reader/reader-join-v1";
const RECORD_READER_RESULT_PREFIX = "LAZY_HARNESS_READER_RESULT:";
const MAX_READER_READ_CALLS = 8;
const MAX_READER_REQUESTED_LINES = 1600;
const RECORD_READER_PATH_RE = /^\.lazy-harness\/(?:domain|spec|behavior|tests|decisions|ssot|planning|plans)\/[A-Za-z0-9_./-]+\.(?:md|xml|json)$/;

type JsonObject = Record<string, unknown>;
type TextToolResult = { content: { type: "text"; text: string }[]; details: JsonObject };
type ReadDebtStatus = "armed" | "reused-work-unit" | "not-armed-synthetic" | "not-armed-hook-empty" | "not-armed-hook-timeout" | "not-armed-hook-error";
type HookResult = { stdout: string; stderr: string; status: number | null; signal?: string | null; error?: string };
type MoveProjectDetails = {
  targetPath: string;
  autoSwitch: boolean;
  switched: boolean;
  switchedSessionFile?: string;
  worktreeOutput: string;
};

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

type ReaderRunState = {
  evidenceEpoch: number;
  launchToolCallId: string;
  runId?: string;
  ledgerSessionFile?: string;
  completed: boolean;
  contentReceived: boolean;
  resultStatus?: ReaderResultStatus;
  packetError?: string;
  joined: boolean;
  fallbackAllowed: boolean;
  revision: string;
  model: string;
  maxReadCalls: number;
  maxRequestedLines: number;
  maxLinesPerRead: number;
  taskDigest: string;
  failureReason?: string;
};

const recentToolCallsByRoot = new Map<string, RecentToolCall[]>();
const workUnitEvidenceByRoot = new Map<string, WorkUnitEvidence>();
const readerRunByRoot = new Map<string, ReaderRunState>();
const readerRuntimeRoots = new Set<string>();
const READER_LEDGER_ENTRY = "lazy-harness-reader-ledger-v1";
type ReaderLedger = {
  root: string; revision: string; evidenceEpoch: number; model: string; taskDigest: string; sessionId: string;
  maxReadCalls: number; maxRequestedLines: number; maxLinesPerRead: number;
  readCalls: number; requestedLines: number; maxObservedReadLimit: number; failedToolCalls: number;
  recordHashes: Record<string, string>; terminal: boolean;
};
type ReaderMeter = { ledger: ReaderLedger; pending: Map<string, string | undefined>; settled: Set<string> };
const readerMeters = new Map<string, ReaderMeter>();
const activePacketsByRoot = new Map<string, { root: string; sessionId: string; messageId: string; readDebtStatus: ReadDebtStatus; readDebtDetail?: string }>();
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
const READ_ONLY_SHELL_RE = /^\s*(?:cd\s+[^;&|]+\s*(?:&&|;)\s*)?(?:(?:\.lazy-harness\/bin\/lazy|lazy)\s+map|pwd|ls|cat|grep|rg|git\s+(?:status|rev-parse))\b/is;
const ACTION_NAME_RE = /(?:^|[_:.\-])(write|edit|patch|apply_patch|create|update|delete|remove|send|merge|push|upload|click|type|fill|press|select|drag|drop|navigate|run|close|open|schedule)(?:$|[_:.\-])/i;
const READER_STATUS_ARG_KEYS = new Set(["action", "id", "includeProgress", "view", "lines"]);

function stableHash(value: unknown): string {
  return createHash("sha256").update(String(value ?? "")).digest("hex").slice(0, 16);
}

function currentRevision(root: string): string | undefined {
  const result = spawnSync("git", ["rev-parse", "HEAD"], { cwd: root, encoding: "utf8", timeout: 5000 });
  return result.status === 0 ? String(result.stdout || "").trim() || undefined : undefined;
}

function isRecordReaderAgent(args: JsonObject): boolean {
  return String(args.agent || "") === RECORD_READER_AGENT;
}

function readerTaskField(task: string, name: string): string | undefined {
  return task.match(new RegExp(`^${name}:\\s*(.+)$`, "mi"))?.[1]?.trim();
}

function readerLaunchValidationError(root: string, args: JsonObject): string | undefined {
  if (!isRecordReaderAgent(args)) return undefined;
  if (Object.prototype.hasOwnProperty.call(args, "action")) return "dedicated Reader launch must omit action; management operations are not launches";
  const existing = readerRunByRoot.get(root);
  if (existing?.evidenceEpoch === currentEvidenceEpoch(root)) return "only one dedicated Reader launch is allowed per evidence epoch";
  if (args.async !== true && args.async !== false) return "dedicated Reader must explicitly select async:true or async:false";
  if (args.context !== "fresh") return "dedicated Reader must use fresh context";
  if (args.acceptance !== false) return "dedicated Reader must set acceptance:false";
  if (args.output !== false) return "dedicated Reader must set output:false";
  if (args.artifacts !== false) return "dedicated Reader must set artifacts:false";
  if (args.toolBudget !== undefined) return "dedicated Reader must omit toolBudget: it counts all tools, not body reads; use maxReadCalls/maxRequestedLines/maxLinesPerRead in the task";
  const model = String(args.model || "").trim();
  if (!model) return "dedicated Reader model must be explicit";
  const contract = args.agentContract && typeof args.agentContract === "object" ? args.agentContract as JsonObject : {};
  if (contract.version !== 1) return "dedicated Reader must use agentContract.version=1";
  const cwd = String(args.cwd || root);
  if (resolve(cwd) !== resolve(root)) return `dedicated Reader cwd must equal the active lazy root: ${root}`;
  const task = String(args.task || "");
  if (readerTaskField(task, "model") !== model) return "Reader task model does not match the explicit launch model";
  const revision = currentRevision(root);
  if (!revision || readerTaskField(task, "root") !== root) return "Reader task root does not match the active lazy root";
  if (readerTaskField(task, "revision") !== revision) return "Reader task revision does not match the active root HEAD";
  if (Number(readerTaskField(task, "evidenceEpoch")) !== currentEvidenceEpoch(root)) return "Reader task evidenceEpoch does not match the active turn";
  if (!readerTaskField(task, "task")) return "Reader task must include a non-empty task field";
  const maxReadCalls = Number(readerTaskField(task, "maxReadCalls"));
  const maxRequestedLines = Number(readerTaskField(task, "maxRequestedLines"));
  const maxLinesPerRead = Number(readerTaskField(task, "maxLinesPerRead"));
  if (!Number.isInteger(maxReadCalls) || maxReadCalls <= 0 || maxReadCalls > MAX_READER_READ_CALLS) return `Reader maxReadCalls must be 1..${MAX_READER_READ_CALLS}`;
  if (!Number.isInteger(maxRequestedLines) || maxRequestedLines <= 0 || maxRequestedLines > MAX_READER_REQUESTED_LINES) return `Reader maxRequestedLines must be 1..${MAX_READER_REQUESTED_LINES}`;
  const expectedPerRead = Math.floor(maxRequestedLines / maxReadCalls);
  if (!Number.isInteger(maxLinesPerRead) || maxLinesPerRead !== expectedPerRead || maxLinesPerRead <= 0) return `Reader maxLinesPerRead must equal floor(maxRequestedLines/maxReadCalls)=${expectedPerRead}`;
  return undefined;
}

function readerLaunchState(root: string, args: JsonObject, launchToolCallId: string): ReaderRunState {
  const task = String(args.task || "");
  const revision = currentRevision(root);
  if (!revision) throw new Error("cannot resolve Reader launch revision");
  return {
    evidenceEpoch: currentEvidenceEpoch(root),
    launchToolCallId,
    completed: false,
    contentReceived: false,
    joined: false,
    fallbackAllowed: false,
    revision,
    model: String(args.model),
    maxReadCalls: Number(readerTaskField(task, "maxReadCalls")),
    maxRequestedLines: Number(readerTaskField(task, "maxRequestedLines")),
    maxLinesPerRead: Number(readerTaskField(task, "maxLinesPerRead")),
    taskDigest: stableHash(readerTaskField(task, "task")),
  };
}

// Native async notification is the delivery boundary; a legacy wait receipt is
// neither required nor sufficient. One launch per epoch disambiguates packets.
function observeReaderPacket(root: string, messages: unknown): void {
  const run = readerRunByRoot.get(root);
  if (!run?.runId || run.fallbackAllowed || run.evidenceEpoch !== currentEvidenceEpoch(root) || !Array.isArray(messages)) return;
  for (const message of messages) {
    if (message?.role !== "custom" || message.customType !== "subagent-notify" || typeof message.content !== "string") continue;
    const identities = message.details?.completions;
    if (!Array.isArray(identities)) continue;
    const owned = identities.filter((item: any) => item?.runId === run.runId);
    if (owned.length !== 1 || owned[0].agent !== RECORD_READER_AGENT || typeof owned[0].sessionFile !== "string" || !owned[0].sessionFile) continue;
    const text = message.content;
    if (!text.startsWith(`Background task completed: **${RECORD_READER_AGENT}**`)) continue;
    receiveReaderResult(root, run, text, owned[0].sessionFile);
  }
}

function receiveReaderResult(root: string, run: ReaderRunState, text: string, sessionFile: string): void {
  const packet = parseReaderResultPacket(text);
  if (!packet || packet.root !== root || packet.revision !== run.revision || packet.evidenceEpoch !== String(run.evidenceEpoch)) {
    run.packetError = "Reader result packet has malformed, duplicate, missing, or mismatched identity/status";
    return;
  }
  if (run.contentReceived && (run.ledgerSessionFile !== sessionFile || run.resultStatus !== packet.status)) {
    run.packetError = "Reader result delivery conflicts with the observed session/status";
    return;
  }
  run.ledgerSessionFile = sessionFile;
  run.resultStatus = packet.status;
  run.contentReceived = true;
  run.completed = true;
}

function readerFallbackError(root: string, message: string): Error {
  const run = readerRunByRoot.get(root);
  if (run) {
    run.joined = false;
    run.fallbackAllowed = true;
    run.failureReason = message;
  }
  workUnitEvidenceByRoot.delete(root);
  return new Error(`${message}; bounded direct Parent fallback enabled`);
}

function startReaderMeter(root: string, task: string, sessionId: string): ReaderMeter | undefined {
  const maxReadCalls = Number(readerTaskField(task, "maxReadCalls"));
  const maxRequestedLines = Number(readerTaskField(task, "maxRequestedLines"));
  const maxLinesPerRead = Number(readerTaskField(task, "maxLinesPerRead"));
  const evidenceEpoch = Number(readerTaskField(task, "evidenceEpoch"));
  const revision = readerTaskField(task, "revision");
  const model = readerTaskField(task, "model");
  const objective = readerTaskField(task, "task");
  if (readerTaskField(task, "root") !== root || !revision || revision !== currentRevision(root) || !model || !objective || !sessionId
    || !Number.isInteger(evidenceEpoch) || evidenceEpoch < 0
    || !Number.isInteger(maxReadCalls) || maxReadCalls < 1 || maxReadCalls > MAX_READER_READ_CALLS
    || !Number.isInteger(maxRequestedLines) || maxRequestedLines < 1 || maxRequestedLines > MAX_READER_REQUESTED_LINES
    || maxLinesPerRead < 1 || maxLinesPerRead !== Math.floor(maxRequestedLines / maxReadCalls)) return undefined;
  return { ledger: { root, revision, evidenceEpoch, model, taskDigest: stableHash(objective), sessionId,
    maxReadCalls, maxRequestedLines, maxLinesPerRead, readCalls: 0, requestedLines: 0,
    maxObservedReadLimit: 0, failedToolCalls: 0, recordHashes: {}, terminal: false }, pending: new Map(), settled: new Set() };
}

function persistReaderMeter(pi: ExtensionAPI, meter: ReaderMeter): boolean {
  try {
    pi.appendEntry(READER_LEDGER_ENTRY, { ...meter.ledger, recordHashes: { ...meter.ledger.recordHashes } });
    return true;
  } catch {
    meter.ledger.failedToolCalls += 1;
    return false;
  }
}

function readDeliveredReaderLedger(root: string, run: ReaderRunState): ReaderLedger {
  try {
    if (!run.ledgerSessionFile) throw new Error("missing session identity");
    const entries = readFileSync(run.ledgerSessionFile, "utf8").split("\n").filter(Boolean).map((line) => JSON.parse(line));
    const header = entries[0];
    const ledger = entries.filter((entry) => entry.type === "custom" && entry.customType === READER_LEDGER_ENTRY).at(-1)?.data as ReaderLedger | undefined;
    if (!ledger || header?.type !== "session" || header.id !== ledger.sessionId || ledger.terminal !== true
      || !ledger.recordHashes || typeof ledger.recordHashes !== "object" || Array.isArray(ledger.recordHashes)
      || ledger.root !== root || ledger.revision !== run.revision || ledger.evidenceEpoch !== run.evidenceEpoch
      || ledger.model !== run.model || ledger.taskDigest !== run.taskDigest) throw new Error("mismatched or nonterminal ledger");
    return ledger;
  } catch {
    throw readerFallbackError(root, "runtime-owned Reader ledger is unavailable, stale, or mismatched");
  }
}

function canonicalReaderRecordPath(root: string, input: string): string | undefined {
  const normalized = String(input || "").replace(/\\/g, "/");
  const parts = normalized.split("/");
  if (!RECORD_READER_PATH_RE.test(normalized) || parts.some((part) => !part || part === "." || part === "..")) return undefined;
  const layer = parts[1];
  const allowedLayers = new Set(["domain", "spec", "behavior", "tests", "decisions", "ssot", "planning", "plans"]);
  if (parts[0] !== ".lazy-harness" || !layer || !allowedLayers.has(layer)) return undefined;
  const absolute = resolve(root, normalized);
  const layerRoot = resolve(root, ".lazy-harness", layer);
  return absolute.startsWith(`${layerRoot}/`) ? normalized : undefined;
}

function parseReaderRunId(event: any): string | undefined {
  const details = event?.details;
  const runId = details?.runId;
  const asyncId = details?.asyncId;
  if (runId !== undefined && asyncId !== undefined && runId !== asyncId) return undefined;
  const id = runId ?? asyncId;
  return typeof id === "string" && /^[A-Za-z0-9_-]{1,128}$/.test(id) ? id : undefined;
}

// SDK mode is a typed output capability. hasUI alone would conflate RPC with
// headless output on older adapters; unknown runtimes retain their prior flow.
function preservesHeadlessPrimaryAnswer(ctx: Pick<ExtensionContext, "mode">): boolean {
  return ctx.mode === "print" || ctx.mode === "json";
}

function printModeAdvisory(body: string): void {
  process.stderr.write(`[lazy-harness post-response advisory; primary stdout preserved]\n${body.trim()}\n`);
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

// Preserve the input runtime's prompt shape: Pi uses strings, OMP uses blocks.
function appendSystemPromptBody(systemPrompt: string, body: string): string;
function appendSystemPromptBody(systemPrompt: string[], body: string): string[];
function appendSystemPromptBody(systemPrompt: unknown, body: string): string | string[] {
  if (Array.isArray(systemPrompt)) {
    const parts = systemPrompt.filter((part): part is string => typeof part === "string");
    return [...parts, body];
  }
  const current = String(systemPrompt || "").trimEnd();
  return current ? `${current}\n\n${body}` : body;
}


function shellCommand(args: JsonObject): string {
  return String(args.command || args.cmd || args.text || "");
}

function isReadOnlyShell(args: JsonObject): boolean {
  const command = shellCommand(args).trim();
  if (!command) return false;
  let body = command;
  if (/^cd\s+/i.test(command)) {
    const match = command.match(/^cd\s+(.+?)\s*&&\s*(.+)$/is);
    if (!match || /[<>&|;$()`\n]/.test(match[1] || "")) return false;
    body = match[2] || "";
  }
  const normalizedFlags = body.replace(/\\(.)/gs, "$1").replace(/["']/g, "");
  if (/[;&<>]|\|\||\$|`|\n/.test(body) || /(?:^|\s)--pre(?:=|\s)/i.test(normalizedFlags)) return false;
  if (/\b(rm|mv|cp|mkdir|touch|tee|python3?\s+-|node\s+-|bun\s+(?:run|x|test)|npm|pnpm|yarn|gh\s+(?:pr\s+(?:create|edit|merge)|issue\s+create))\b/i.test(body)) return false;
  const [first, ...filters] = body.split("|").map((part) => part.trim());
  if (!first || !READ_ONLY_SHELL_RE.test(first)) return false;
  return filters.every((part) => /^(?:head|tail|wc)(?:\s|$)/i.test(part));
}

function isReaderAllowedShell(args: JsonObject): boolean {
  const command = shellCommand(args).trim();
  if (command === ".lazy-harness/bin/lazy map --overview --complete --format=md") return true;
  if (command === "pwd" || command === "git rev-parse --show-toplevel" || command === "git rev-parse HEAD") return true;
  return /^\.lazy-harness\/bin\/lazy map [A-Za-z0-9_./:#-]+ --format=md --limit=8$/.test(command);
}

function readerToolPath(root: string, input: string): string {
  const path = input.replace(/\\/g, "/");
  const prefix = `${resolve(root).replace(/\\/g, "/")}/`;
  return path.startsWith(prefix) ? path.slice(prefix.length) : path;
}

function isReaderRuntimeToolAllowed(root: string, name: string, args: JsonObject): boolean {
  const leaf = name.toLowerCase().split(/[.:]/).pop() || name.toLowerCase();
  if (leaf === "read") {
    const path = readerToolPath(root, String(args.path || args.file_path || ""));
    return Boolean(canonicalReaderRecordPath(root, path));
  }
  if (leaf === "grep") {
    const rawPaths = Array.isArray(args.paths) ? args.paths : [args.path];
    const paths = rawPaths.filter((path) => typeof path === "string" && path.length > 0).map(String);
    return paths.length > 0 && paths.every((path) => {
      const normalized = readerToolPath(root, path).replace(/\/$/, "");
      return /^\.lazy-harness\/(?:domain|spec|behavior|tests|decisions|ssot|planning|plans)(?:\/|$)/.test(normalized)
        && !normalized.split("/").some((part) => part === "." || part === "..");
    });
  }
  if (["bash", "cmd", "command", "shell", "terminal"].includes(leaf)) return isReaderAllowedShell(args);
  return false;
}

type ReaderStatusInspectionContext = {
  root: string;
  runId: string;
  evidenceEpoch: number;
  currentEpoch: number;
  pending: boolean;
};

export function permitsOwnedReaderStatusInspection(root: string, name: string, args: JsonObject, context: ReaderStatusInspectionContext): boolean {
  if (name.toLowerCase() !== "subagent" || String(args.action || "") !== "status") return false;
  if (Object.keys(args).some((key) => !READER_STATUS_ARG_KEYS.has(key))) return false;
  if (args.includeProgress !== undefined && typeof args.includeProgress !== "boolean") return false;
  if (args.view !== undefined && args.view !== "transcript") return false;
  if (args.lines !== undefined && (!Number.isInteger(args.lines) || Number(args.lines) <= 0 || Number(args.lines) > 500)) return false;
  return Boolean(
    context.pending === true
    && Number.isInteger(context.evidenceEpoch) && context.evidenceEpoch >= 0
    && Number.isInteger(context.currentEpoch) && context.currentEpoch >= 0
    && context.root === root
    && context.runId
    && String(args.id || "") === context.runId
    && context.evidenceEpoch === context.currentEpoch
  );
}

function readerStatusInspectionContext(root: string): ReaderStatusInspectionContext {
  const run = readerRunByRoot.get(root);
  return {
    root,
    runId: run?.runId || "",
    evidenceEpoch: run?.evidenceEpoch ?? -1,
    currentEpoch: currentEvidenceEpoch(root),
    pending: Boolean(run?.runId && !run.joined && !run.fallbackAllowed),
  };
}

function isOwnedReaderStatusInspection(root: string, name: string, args: JsonObject): boolean {
  return permitsOwnedReaderStatusInspection(root, name, args, readerStatusInspectionContext(root));
}

function isActionTool(name: string, args: JsonObject, ownedReaderStatus = false): boolean {
  const lower = name.toLowerCase();
  const leaf = lower.split(/[.:]/).pop() || lower;
  if (lower === "subagent" && (String(args.action || "") === "list" || isRecordReaderAgent(args) || ownedReaderStatus)) return false;
  if (lower === "subagent_wait" || lower === "lazy_reader_join") return false;
  if (["read", "grep", "find", "ls"].includes(leaf)) return false;
  if (["batch", "multi_tool_use.parallel"].includes(lower)) {
    const nested = (args.tool_calls ?? args.toolCalls ?? args.tool_uses) as unknown;
    if (!Array.isArray(nested)) return false;
    return nested.some((call) => {
      const c = (call && typeof call === "object" ? call : {}) as Record<string, unknown>;
      const nestedName = String(c.recipient_name || c.tool || c.name || c.toolName || "");
      const nestedArgs = (
        c.parameters && typeof c.parameters === "object" ? c.parameters
          : c.input && typeof c.input === "object" ? c.input
            : c.args && typeof c.args === "object" ? c.args : {}
      ) as JsonObject;
      return isActionTool(nestedName, nestedArgs);
    });
  }
  if (MUTATION_TOOL_NAMES.has(lower)) return true;
  if (["bash", "cmd", "command", "shell", "terminal"].includes(leaf)) return !isReadOnlyShell(args);
  if (lower === "subagent" || lower === "swarm") return true;
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
    "If project detail is needed, prefer one dedicated `lazy-harness.record-reader` plus content join while Parent inspects source/tests; use direct map/read only when Reader is unavailable or non-complete.",
    "Action tools remain guarded until a human turn arms read-debt or sufficient map/read evidence exists.",
  ].filter(Boolean).join("\n");
}

function armStatusMessage(root: string, status: ReadDebtStatus, detail?: string): string {
  const detailSuffix = detail ? ` hook=${detail.replace(/\s+/g, "_").slice(0, 80)}` : "";
  const phase = readDebtArmed(status) ? "phase=armed" : "phase=debug";
  const revision = currentRevision(root) ?? "unknown";
  return `lazy-harness read-debt: ${EXTENSION_RUNTIME_MARKER} root=${root} revision=${revision} evidence-epoch=${currentEvidenceEpoch(root)} status=${readDebtLabel(status)} ${phase}${detailSuffix} tool-guard=ready`;
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
  readerRunByRoot.delete(root);
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
  const captureEvidence = new CaptureEvidence();
  const clearCapture = () => captureEvidence.reset("");
  pi.on("session_start", clearCapture);
  pi.on("session_shutdown", clearCapture);
  pi.on("input", async (event: any, ctx: any) => {
    const root = findLazyRootForInvocation(event, ctx);
    if (!root) return undefined;
    if (readerRuntimeRoots.has(root)) return undefined;
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
        rearmEvidenceAfterSteer(root); // invalidate all evidence collected for the previous instruction
        captureEvidence.reset(root);
        workUnitEvidenceByRoot.delete(root); // explicit steer starts a fresh work unit
        pendingRegroundByRoot.delete(root);
        regroundBodyByRoot.delete(root);
        const sessionId = `pi:${stableHash(root)}`;
        const messageId = `pi:${stableHash(`${Date.now()}:${steerText}`)}`;
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

  pi.on("before_agent_start", async (event, ctx) => {
    const cwd = resolveInvocationCwd(event, ctx);
    const root = findLazyRoot(cwd);
    if (!root) return undefined;
    if (systemPromptIncludesBody(event.systemPrompt, RECORD_READER_ROLE_MARKER)) {
      readerRuntimeRoots.add(root);
      const sessionId = String(ctx?.sessionManager?.getSessionId?.() || "");
      if (!readerMeters.has(root)) {
        // Native child launch wraps the caller task as `Task: ${attemptTask}`.
        // Unwrap only that transport prefix before parsing identity/objective.
        const task = event.prompt.startsWith("Task: ") ? event.prompt.slice(6) : event.prompt;
        const meter = startReaderMeter(root, task, sessionId);
        if (meter) { readerMeters.set(root, meter); persistReaderMeter(pi, meter); }
      }
      return undefined;
    }
    readerRuntimeRoots.delete(root);

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
      return {
        message: { customType: EXTENSION_NAME, content: armStatusMessage(root, readDebtStatus), display: true },
        systemPrompt: systemPromptIncludesBody(event.systemPrompt, CAPTURE_GUIDANCE) ? event.systemPrompt : appendSystemPromptBody(event.systemPrompt, CAPTURE_GUIDANCE),
      };
    }
    workUnitEvidenceByRoot.delete(root);
    captureEvidence.reset(root);
    readerRunByRoot.delete(root);

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
    let inject = `${body}\n\n${CAPTURE_GUIDANCE}`;
    const agentsPath = join(root, ".lazy-harness", "AGENTS.md");
    if (existsSync(agentsPath) && !systemPromptIncludesBody(event.systemPrompt, "Lazy-Harness AI")) {
      try {
        const grammar = readFileSync(agentsPath, "utf8").trim();
        if (grammar) inject = `${grammar}\n\n${inject}`;
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
    if (readerRuntimeRoots.has(root)) {
      const normalized = normalizePiTool(event.toolName, event.input || {});
      const meter = readerMeters.get(root);
      const id = String(event.toolCallId || "");
      if (!meter || meter.ledger.sessionId !== ctx?.sessionManager?.getSessionId?.()) return { block: true, reason: "[lazy-harness Reader boundary] missing runtime-owned launch budget/identity" };
      const ledger = meter.ledger;
      const leaf = normalized.name.toLowerCase().split(/[.:]/).pop();
      let allowed = isReaderRuntimeToolAllowed(root, normalized.name, normalized.args) && !ledger.terminal && Boolean(id) && !meter.pending.has(id) && !meter.settled.has(id);
      let path: string | undefined;
      if (leaf === "read") {
        const limit = Number(normalized.args.limit);
        allowed = allowed && Number.isInteger(limit) && limit > 0 && limit <= ledger.maxLinesPerRead
          && ledger.readCalls < ledger.maxReadCalls && ledger.requestedLines + limit <= ledger.maxRequestedLines;
        if (allowed) {
          ledger.readCalls += 1;
          ledger.requestedLines += limit;
          ledger.maxObservedReadLimit = Math.max(ledger.maxObservedReadLimit, limit);
          path = readerToolPath(root, String(normalized.args.path || normalized.args.file_path || ""));
        }
      }
      if (allowed) meter.pending.set(id, path);
      else { ledger.failedToolCalls += 1; meter.settled.add(id); }
      if (!persistReaderMeter(pi, meter)) return { block: true, reason: "[lazy-harness Reader boundary] runtime ledger persistence failed; return incomplete" };
      return allowed ? undefined : { block: true, reason: "[lazy-harness Reader boundary] canonical lane or launch read budget exceeded; return incomplete without retry" };
    }

    const packet = activePacketsByRoot.get(root)
      ? activePacketsByRoot.get(root)!
      : { root, sessionId: `pi:${stableHash(cwd)}`, messageId: `pi:${stableHash("no-active-packet")}`, readDebtStatus: "not-armed-hook-empty" as ReadDebtStatus };

    const normalized = normalizePiTool(event.toolName, event.input || {});
    const readerLaunchError = readerLaunchValidationError(root, normalized.args);
    if (readerLaunchError) return { block: true, reason: `[lazy-harness Reader launch] ${readerLaunchError}` };
    const activeReader = readerRunByRoot.get(root);
    const ownedReaderStatus = isOwnedReaderStatusInspection(root, normalized.name, normalized.args);
    if (activeReader && activeReader.evidenceEpoch === currentEvidenceEpoch(root) && !activeReader.joined && !activeReader.fallbackAllowed && isActionTool(normalized.name, normalized.args, ownedReaderStatus)) {
      return { block: true, reason: "[lazy-harness Reader join pending] wait for the content-bearing Reader packet, then call lazy_reader_join before action." };
    }
    if (!readDebtArmed(packet.readDebtStatus) && isActionTool(normalized.name, normalized.args, ownedReaderStatus)) {
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
      ...(normalized.name.toLowerCase() === "subagent" && String(normalized.args.action || "") === "status"
        ? { reader_status_inspection: readerStatusInspectionContext(root) }
        : {}),
    };

    const script = join(root, ".lazy-harness", "hooks", "lifecycle", "on-tool-execute-before.sh");
    if (existsSync(script)) {
      const hook = runHook(script, payload, root);
      const reason = denyReason(hook.stdout, hook.stderr);
      if (reason) return { block: true, reason };
    }
    if (isRecordReaderAgent(normalized.args)) {
      readerRunByRoot.set(root, readerLaunchState(root, normalized.args, String(event.toolCallId || "")));
      workUnitEvidenceByRoot.delete(root);
    }
    // Status is coordination-only. Its result may contain transcript text, so do
    // not admit it to evidence epochs, recent-call caches, or record fingerprints.
    if (ownedReaderStatus) return undefined;
    markToolCallStarted(root, event);
    captureEvidence.start(root, cwd, currentEvidenceEpoch(root), event.toolCallId, normalized.name, normalized.args);
    return undefined;
  });

  pi.on("tool_result", async (event: any, ctx: any) => {
    const root = findLazyRootFromEvent(event, ctx);
    if (!root) return undefined;
    if (readerRuntimeRoots.has(root)) {
      const meter = readerMeters.get(root);
      const id = String(event.toolCallId || "");
      if (!meter || !meter.pending.has(id)) return undefined;
      const path = meter.pending.get(id);
      meter.pending.delete(id);
      meter.settled.add(id);
      if (event.isError) meter.ledger.failedToolCalls += 1;
      else if (path) {
        const digest = hashFile(join(root, path));
        if (digest) meter.ledger.recordHashes[path] = digest;
        else meter.ledger.failedToolCalls += 1;
      }
      persistReaderMeter(pi, meter);
      return undefined;
    }
    const normalized = normalizePiTool(event.toolName, event.input || {});
    captureEvidence.complete(root, resolveInvocationCwd(event, ctx), currentEvidenceEpoch(root), event.toolCallId, normalized.name, normalized.args,
      event.is_error === true ? true : event.isError, event.content);
    if (!toolResultBelongsToCurrentEvidenceEpoch(root, event)) return undefined;
    const activeReader = readerRunByRoot.get(root);
    const normalizedName = normalized.name.toLowerCase();
    if (normalizedName === "subagent" && isRecordReaderAgent(normalized.args)) {
      if (event.isError) {
        readerFallbackError(root, "dedicated Reader launch failed");
      } else if (activeReader && activeReader.launchToolCallId === String(event.toolCallId || "")) {
        const runId = parseReaderRunId(event);
        if (runId) {
          activeReader.runId = runId;
          if (normalized.args.async === false) {
            const results = event.details?.results;
            const result = Array.isArray(results) && results.length === 1 ? results[0] : undefined;
            if (event.details?.mode !== "single" || result?.agent !== RECORD_READER_AGENT || result.exitCode !== 0 || result.error
              || typeof result.sessionFile !== "string" || !result.sessionFile) {
              activeReader.packetError = "synchronous Reader result lacks successful runtime run/session identity";
            } else {
              // Only actual Parent tool content is delivery. details.finalOutput
              // and session-file prose must never substitute for missing content.
              const text = Array.isArray(event.content) ? event.content.filter((part: any) => part?.type === "text" && typeof part.text === "string").map((part: any) => part.text).join("\n") : "";
              receiveReaderResult(root, activeReader, text, result.sessionFile);
            }
          }
        } else readerFallbackError(root, "dedicated Reader launch result did not expose a run id");
      }
    } else if (normalizedName === "subagent_wait" && activeReader && String(normalized.args.id || "") === String(activeReader.runId || "")) {
      let completionBlob = "";
      try { completionBlob = JSON.stringify({ content: event.content, details: event.details }); } catch { completionBlob = String(event.content || ""); }
      activeReader.completed = !event.isError && /(?:\"state\":\"complete\"|Outcome:\s*1\s+complete)/i.test(completionBlob);
      if (!activeReader.completed) readerFallbackError(root, "dedicated Reader wait did not complete successfully");
    }
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
      if (readerRuntimeRoots.has(root)) return undefined;
      observeReaderPacket(root, event.messages);
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
    if (readerRuntimeRoots.has(root)) {
      const meter = readerMeters.get(root);
      if (meter) {
        // SDK schema/unknown-tool failures can bypass both extension tool hooks.
        // Reconcile the actual turn results before sealing, never model prose.
        for (const message of Array.isArray(event.messages) ? event.messages : []) {
          const id = String(message?.toolCallId || "");
          if (message?.role === "toolResult" && message.isError && id && !meter.settled.has(id)) {
            meter.ledger.failedToolCalls += 1;
            meter.pending.delete(id);
            meter.settled.add(id);
          }
        }
        meter.ledger.terminal = meter.pending.size === 0;
        persistReaderMeter(pi, meter);
      }
      return undefined;
    }
    const packet = activePacketsByRoot.get(root)
      ? activePacketsByRoot.get(root)!
      : { root, sessionId: `pi:${stableHash(cwd)}`, messageId: `pi:${stableHash("no-active-packet")}`, readDebtStatus: "not-armed-hook-empty" as ReadDebtStatus };

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
      // Never edit the caller-visible answer, even for valid/malformed envelopes.
      // Capture evidence is independent of the lossy last-40 diagnostic projection.
      capture_validation: captureEvidence.evaluate(root, currentEpoch, assistantResponse),
      assistant_response: assistantResponse,
      last_user_message: lastUserMessage,
    };

    const script = join(root, ".lazy-harness", "hooks", "lifecycle", "on-response-completed.sh");
    const hook: HookResult = existsSync(script)
      ? runHook(script, payload, root)
      : { stdout: "", stderr: "", status: 127, error: "hook-missing" };
    const body = hookInjectBody(hook.stdout);
    const capture = parseJsonMaybe(hook.stdout)?.capture;
    const assessment: JsonObject = hook.status === 0 && capture && typeof capture === "object" && !Array.isArray(capture)
      ? capture as JsonObject
      : { schemaVersion: "1.0", root, epoch: currentEpoch, status: "unverified", reason: "capture response hook unavailable or missing assessment", semanticStatus: "llm-judgement-not-verified", approvalStatus: "not-evaluated", facts: [] };
    const captureNotice = `Capture evidence: ${String(assessment.status)} — ${String(assessment.reason)}. Semantic relevance and approval are not runtime-verified.`;
    const captureNeedsAttention = assessment.status === "unverified" || assessment.status === "pending";
    if (preservesHeadlessPrimaryAnswer(ctx)) {
      // Plain custom entries are runtime state, not conversation messages. Even
      // triggerTurn:false custom messages hide Pi's last-assistant text output.
      pi.appendEntry("lazy-harness-capture", assessment);
      if (captureNeedsAttention) printModeAdvisory(captureNotice);
    } else if (typeof pi.sendMessage === "function") {
      pi.sendMessage({
        customType: "lazy-harness-capture",
        content: captureNotice,
        display: captureNeedsAttention,
        details: assessment,
      }, { triggerTurn: false });
    }
    writeAgentEndTrace(root, payload, messages, recentToolCalls, hook, body);
    if (!body) {
      lastAdvisoryByRoot.delete(root); // gate resolved → reset continuation counter
      return undefined;
    }
    if (preservesHeadlessPrimaryAnswer(ctx)) {
      // This response.completed hook is advisory metadata, not Reader content,
      // a user steer, or a tool action block. Do not schedule a replacement
      // assistant answer in either headless output format. Native drain remains
      // owned by the native extension, including on pending/waiting turns.
      printModeAdvisory(body);
      lastAdvisoryByRoot.delete(root);
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

  // Explicit Reader join barrier. Process completion alone never marks joined;
  // the Parent calls this only after consuming the content-bearing Reader packet.
  if (typeof (pi as any).registerTool === "function") pi.registerTool({
    name: "lazy_reader_join",
    label: "Lazy Reader Join",
    description: "Close a dedicated lazy-harness.record-reader join after its result content reaches the Parent, or explicitly enter bounded fallback for a non-complete result.",
    promptSnippet: "Join the dedicated Reader result before planning, mutation, or host-specific completion.",
    promptGuidelines: [
      "Call only after the Reader result content is present in Parent context; subagent_wait completion alone is insufficient.",
      "Use status=complete only for an exact matching complete packet within cumulative budgets. Non-complete status enables bounded direct fallback.",
      "Omit runId and numeric accounting fields to use adapter-owned launch identity and actual child ledger. Never copy a child session/execution UUID or trust self-reported counters; explicit mismatches reject the join.",
    ],
    parameters: Type.Object({
      runId: Type.Optional(Type.String({ description: "Defaults to the adapter-owned active Reader run. Explicit mismatches are rejected; never use a child execution/session id." })),
      status: Type.Union([Type.Literal("complete"), Type.Literal("incomplete"), Type.Literal("conflict"), Type.Literal("failed")]),
      resultMarker: Type.Optional(Type.String({ description: "Exact LAZY_HARNESS_READER_RESULT marker observed in the content packet." })),
      revision: Type.String({ description: "Reader packet Git revision." }),
      evidenceEpoch: Type.Number({ description: "Reader packet evidence epoch from the turn-start marker." }),
      readCalls: Type.Optional(Type.Number({ description: "Defaults to runtime-owned admitted body-read count." })),
      requestedLines: Type.Optional(Type.Number({ description: "Defaults to runtime-owned charged lines, including failed reads." })),
      maxReadCalls: Type.Optional(Type.Number({ description: "Defaults to launch read-call ceiling." })),
      maxRequestedLines: Type.Optional(Type.Number({ description: "Defaults to launch requested-line ceiling." })),
      maxLinesPerRead: Type.Optional(Type.Number({ description: "Defaults to launch per-read line ceiling." })),
      maxObservedReadLimit: Type.Optional(Type.Number({ description: "Defaults to largest admitted read limit." })),
      failedToolCalls: Type.Optional(Type.Number({ description: "Defaults to runtime-owned failure count; complete requires zero." })),
      recordPaths: Type.Optional(Type.Array(Type.String(), { maxItems: 16, description: "Normally omit: all successful runtime-ledger paths are joined automatically. Legacy reported subsets are accepted; unread or duplicate paths are rejected." })),
    }),
    async execute(_toolCallId: string, params: any, _signal: AbortSignal | undefined, _onUpdate: any, ctx: any): Promise<TextToolResult> {
      const root = findLazyRootForInvocation(undefined, ctx);
      if (!root) throw new Error("lazy-harness root not found from current cwd");
      const run = readerRunByRoot.get(root);
      if (!run) throw new Error("no dedicated Reader launch is active for this root");
      if (run.joined) throw new Error("dedicated Reader run is already joined");
      if (run.fallbackAllowed) throw new Error(`dedicated Reader run entered terminal fallback: ${run.failureReason || "non-complete result"}`);
      if (run.evidenceEpoch !== currentEvidenceEpoch(root) || Number(params.evidenceEpoch) !== run.evidenceEpoch) {
        throw readerFallbackError(root, "Reader evidence epoch is stale");
      }
      if (!run.runId || (params.runId !== undefined && String(params.runId) !== run.runId)) throw readerFallbackError(root, "Reader run id does not match the active launch");
      const revision = currentRevision(root);
      if (!revision || revision !== run.revision || String(params.revision) !== run.revision) throw readerFallbackError(root, "Reader revision does not match the launch and active root HEAD");
      if (run.packetError) throw readerFallbackError(root, run.packetError);
      const status = run.resultStatus && run.resultStatus !== "complete" ? run.resultStatus : String(params.status || "");
      if (status !== "complete") {
        run.failureReason = `Reader result is ${status}`;
        run.fallbackAllowed = true;
        run.joined = false;
        workUnitEvidenceByRoot.delete(root);
        return {
          content: [{ type: "text", text: `Reader result is ${status}; dedicated join remains incomplete and bounded Parent fallback is enabled.` }],
          details: { joined: false, fallbackAllowed: true, status, runId: run.runId, revision, evidenceEpoch: run.evidenceEpoch },
        };
      }
      if (!run.contentReceived) throw readerFallbackError(root, "content-bearing Reader completion notification has not been observed");
      if (String(params.resultMarker || "") !== `${RECORD_READER_RESULT_PREFIX} complete`) {
        throw readerFallbackError(root, "content-bearing complete Reader marker was not supplied");
      }
      const ledger = readDeliveredReaderLedger(root, run);
      const fields = ["readCalls", "requestedLines", "maxReadCalls", "maxRequestedLines", "maxLinesPerRead", "maxObservedReadLimit", "failedToolCalls"] as const;
      if (fields.some((field) => params[field] !== undefined && params[field] !== ledger[field])) throw readerFallbackError(root, "Reader self-report does not match runtime-owned accounting");
      const budgetValues = fields.map((field) => ledger[field]);
      if (budgetValues.some((value) => !Number.isInteger(value) || value < 0)) throw readerFallbackError(root, "Reader budget fields must be non-negative integers");
      const [readCalls, requestedLines, maxReadCalls, maxRequestedLines, maxLinesPerRead, maxObservedReadLimit, failedToolCalls] = budgetValues;
      if (readCalls <= 0 || requestedLines <= 0 || maxObservedReadLimit <= 0) throw readerFallbackError(root, "complete Reader ledger requires positive read counters");
      if (maxObservedReadLimit > requestedLines || requestedLines > readCalls * maxLinesPerRead) throw readerFallbackError(root, "Reader complete packet has an internally impossible read ledger");
      if (
        maxReadCalls !== run.maxReadCalls
        || maxRequestedLines !== run.maxRequestedLines
        || maxLinesPerRead !== run.maxLinesPerRead
        || maxLinesPerRead !== Math.floor(maxRequestedLines / maxReadCalls)
        || maxReadCalls > MAX_READER_READ_CALLS
        || maxRequestedLines > MAX_READER_REQUESTED_LINES
      ) {
        throw readerFallbackError(root, "Reader packet budget ceilings do not match the launch envelope");
      }
      if (readCalls > maxReadCalls || requestedLines > maxRequestedLines || maxObservedReadLimit > maxLinesPerRead || failedToolCalls !== 0) {
        throw readerFallbackError(root, "Reader complete packet violates cumulative read or failed-tool budget");
      }
      const recordPaths = Object.keys(ledger.recordHashes);
      if (params.recordPaths !== undefined) {
        const reportedPaths = params.recordPaths;
        if (!Array.isArray(reportedPaths) || reportedPaths.length > 16 || reportedPaths.some((path: unknown) => typeof path !== "string")) {
          throw readerFallbackError(root, "Reader reported paths must be a bounded string array");
        }
        if (new Set(reportedPaths).size !== reportedPaths.length) throw readerFallbackError(root, "Reader reported paths contain duplicates");
        if (reportedPaths.some((path: string) => !Object.prototype.hasOwnProperty.call(ledger.recordHashes, path))) {
          throw readerFallbackError(root, "Reader reported path is outside runtime-owned successful reads");
        }
      }
      if (recordPaths.length === 0) throw readerFallbackError(root, "complete Reader join requires at least one canonical record path");
      if (recordPaths.length > readCalls) throw readerFallbackError(root, "Reader complete packet reports more record paths than read calls");
      if (new Set(recordPaths).size !== recordPaths.length) throw readerFallbackError(root, "complete Reader join contains duplicate record paths");
      const recordHashes = new Map<string, string>();
      for (const rawPath of recordPaths) {
        const path = canonicalReaderRecordPath(root, rawPath);
        if (!path) throw readerFallbackError(root, `Reader record path is outside the canonical record lane: ${rawPath}`);
        const digest = hashFile(join(root, path));
        if (!digest || digest !== ledger.recordHashes[path]) throw readerFallbackError(root, `Reader record path is missing, changed, or unreadable: ${path}`);
        recordHashes.set(path, digest);
      }
      workUnitEvidenceByRoot.set(root, { mapped: true, recordHashes });
      run.joined = true;
      run.fallbackAllowed = false;
      return {
        content: [{ type: "text", text: `Reader join complete for ${run.runId}; ${recordHashes.size} canonical record fingerprint(s) cached.` }],
        details: { joined: true, fallbackAllowed: false, status, runId: run.runId, revision, evidenceEpoch: run.evidenceEpoch, model: run.model, taskDigest: run.taskDigest, recordCount: recordHashes.size, recordPaths: [...recordHashes.keys()], readCalls, requestedLines, maxReadCalls, maxRequestedLines, maxLinesPerRead, maxObservedReadLimit, failedToolCalls },
      };
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
    async execute(_toolCallId: string, params: any, signal: AbortSignal | undefined, _onUpdate: any, ctx: any): Promise<AgentToolResult<MoveProjectDetails>> {
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
