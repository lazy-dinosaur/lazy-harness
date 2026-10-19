import { readFileSync, realpathSync, statSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { ompSessionHeader } from "../omp/session-header.ts";

const tokenFields = ["input", "output", "cacheRead", "cacheWrite", "totalTokens"] as const;
type TokenTotals = Record<typeof tokenFields[number], number>;
type SessionRole = "parent" | "reader";
type JsonObject = Record<string, unknown>;

function object(value: unknown, label: string): JsonObject {
  if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error(`${label}: expected object`);
  return value as JsonObject;
}
function parseObject(text: string, label: string): JsonObject {
  let value: unknown;
  try { value = JSON.parse(text); } catch { throw new Error(`${label}: invalid JSON`); }
  return object(value, label);
}
function nonempty(value: unknown, label: string): string {
  if (typeof value !== "string" || !value.trim()) throw new Error(`${label}: expected nonempty string`);
  return value;
}
function emptyTotals(): TokenTotals {
  return { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, totalTokens: 0 };
}
function addTotals(target: TokenTotals, source: TokenTotals): void {
  for (const field of tokenFields) {
    const sum = target[field] + source[field];
    if (!Number.isSafeInteger(sum)) throw new Error(`usage.${field}: unsafe aggregate`);
    target[field] = sum;
  }
}
function decodeUsage(value: unknown, label: string): TokenTotals {
  const usage = object(value, `${label}: missing or invalid usage`);
  const result = emptyTotals();
  for (const field of tokenFields) {
    const count = usage[field];
    if (typeof count !== "number" || !Number.isSafeInteger(count) || count < 0) throw new Error(`${label}: invalid usage.${field}`);
    result[field] = count;
  }
  return result;
}

/** Read-only accounting of explicitly supplied files, not a task-success or billing verdict. */
export function collectRuntimeUsage(input: unknown, baseDir = process.cwd()) {
  const manifest = object(input, "manifest");
  if (manifest.runtime !== "pi" && manifest.runtime !== "omp") throw new Error("manifest.runtime must be pi or omp");
  if (manifest.measurement !== "offline" && manifest.measurement !== "live") throw new Error("manifest.measurement must be offline or live");
  if (!Array.isArray(manifest.sessions) || !manifest.sessions.length) throw new Error("manifest.sessions must be nonempty");
  const sessions = manifest.sessions.map((value, index) => {
    const entry = object(value, `sessions[${index}]`);
    if (entry.role !== "parent" && entry.role !== "reader") throw new Error(`sessions[${index}]: invalid role`);
    return { role: entry.role as SessionRole, path: nonempty(entry.path, `sessions[${index}].path`) };
  });
  if (sessions.filter(entry => entry.role === "parent").length !== 1) throw new Error("exactly one Parent session is required");

  const paths = new Set<string>();
  const sessionIds = new Set<string>();
  const messageIds = new Set<string>();
  const identities = new Set<string>();
  const totals = emptyTotals();
  const byRole = { parent: emptyTotals(), reader: emptyTotals() };
  let messages = 0;
  let nonSuccessfulStops = 0;
  let knownEstimatedCost = 0;
  let missingCostMessages = 0;
  const files = sessions.map(entry => {
    const path = realpathSync(resolve(baseDir, entry.path));
    if (paths.has(path)) throw new Error(`duplicate session path: ${path}`);
    paths.add(path);
    if (!statSync(path).isFile()) throw new Error(`not a regular session file: ${path}`);
    const rows = readFileSync(path, "utf8").split(/\r?\n/).filter(line => line.trim()).map((line, i) => parseObject(line, `${path}:${i + 1}`));
    const header = manifest.runtime === "omp" ? ompSessionHeader(rows) : rows[0];
    if (header?.type !== "session" || rows.filter(row => row.type === "session").length !== 1) throw new Error(`${path}: one leading session header required`);
    const sessionId = nonempty(header.id, `${path}: session id`);
    if (sessionIds.has(sessionId)) throw new Error(`duplicate session id: ${sessionId}`);
    sessionIds.add(sessionId);
    const fileTotals = emptyTotals();
    let assistantMessages = 0;
    for (const row of rows) {
      if (row.type !== "message") continue;
      const message = object(row.message, `${path}: message`);
      if (message.role !== "assistant") continue;
      const id = nonempty(row.id, `${path}: assistant entry id`);
      // Reject copied/replayed entries rather than silently counting them twice.
      if (messageIds.has(id)) throw new Error(`duplicate assistant entry id: ${id}`);
      messageIds.add(id);
      const provider = nonempty(message.provider, `${path}: provider`);
      const model = nonempty(message.model, `${path}: model`);
      identities.add(`${provider}/${model}`);
      const usage = decodeUsage(message.usage, `${path}:${id}`);
      addTotals(fileTotals, usage);
      const rawUsage = object(message.usage, `${path}:${id}: usage`);
      if (rawUsage.cost === undefined) {
        missingCostMessages++;
      } else {
        const cost = object(rawUsage.cost, `${path}:${id}: cost`).total;
        if (cost === undefined) missingCostMessages++;
        else {
          if (typeof cost !== "number" || !Number.isFinite(cost) || cost < 0) throw new Error(`${path}:${id}: invalid estimated cost`);
          knownEstimatedCost += cost;
          if (!Number.isFinite(knownEstimatedCost)) throw new Error("unsafe aggregate estimated cost");
        }
      }
      assistantMessages++;
      if (message.stopReason === "error" || message.stopReason === "aborted") nonSuccessfulStops++;
    }
    messages += assistantMessages;
    addTotals(totals, fileTotals);
    addTotals(byRole[entry.role], fileTotals);
    return { role: entry.role, path, sessionId, assistantMessages, totals: fileTotals };
  });
  return {
    schemaVersion: "runtime-session-usage/v1",
    runtime: manifest.runtime,
    declaredMeasurement: manifest.measurement,
    coverage: "explicit-session-inventory-only",
    inventoryCompletenessVerified: false,
    providerRequestCount: null,
    unloggedRetryUsage: "unknown",
    taskSuccess: "not-evaluated",
    identities: [...identities].sort(),
    assistantMessages: messages,
    nonSuccessfulStops,
    totals,
    byRole,
    runtimeEstimatedCost: { knownSubtotal: knownEstimatedCost, missingCostMessages, completeEstimate: missingCostMessages ? null : knownEstimatedCost },
    files,
    limitations: [
      "The caller must prove all Parent/Reader/attempt files are included; this reader does not discover omitted work.",
      "Assistant entries are not a verified count of provider requests or retries. Logged error/aborted usage is included.",
      "Runtime totalTokens is retained independently; cache fields are not added to it again.",
      "Runtime estimated cost is not a billing receipt; offline zero usage is not efficiency evidence.",
    ],
  };
}

if (import.meta.main) {
  try {
    if (process.argv.length !== 3) throw new Error("Usage: bun collect-runtime-usage.ts <manifest.json>");
    const manifestPath = resolve(process.argv[2]);
    console.log(JSON.stringify(collectRuntimeUsage(parseObject(readFileSync(manifestPath, "utf8"), manifestPath), dirname(manifestPath)), null, 2));
  } catch (error) {
    console.error(error instanceof Error ? error.message : String(error));
    process.exitCode = 1;
  }
}
