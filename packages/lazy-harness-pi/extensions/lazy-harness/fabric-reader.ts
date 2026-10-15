import { createHash } from "node:crypto";
import { mkdirSync, readFileSync, renameSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fabricReaderDefinition, FABRIC_READER_DEFAULT_MODEL } from "./fabric-reader-policy.ts";

export const FABRIC_READER_NAME = "lazy-harness.record-reader";
const PROXY_KIND = "pi-fabric.tool-result-proxy.v1";
const hash = (text: string) => createHash("sha256").update(text).digest("hex").slice(0, 16);
const field = (task: string, name: string) => task.match(new RegExp(`^${name}:[ \\t]*(.+)$`, "m"))?.[1]?.trim();

/** Canonical body remains shared with OMP; no pi-subagents loader is involved. */
export function fabricReaderPrompt(): string {
  return fabricReaderDefinition().body;
}

export function fabricReaderRequest(root: string, task: string, model: string): Record<string, unknown> {
  const definition = fabricReaderDefinition();
  const match = model.match(/^([A-Za-z0-9_.-]+\/[A-Za-z0-9_./-]+):low$/);
  if (!match || field(task, "model") !== model) throw new Error("Fabric Reader requires an explicit provider/model:low matching the task");
  return {
    name: FABRIC_READER_NAME, task, cwd: root, model: match[1], thinking: "low",
    runner: "pi", transport: "process", seed: "task", extensions: true, recursive: false,
    tools: [...definition.tools], readOnly: true, shell: "unconfined",
    systemPrompt: fabricReaderPrompt(),
  };
}

/** Runtime scratch only. The path comes from Fabric's host-issued run id, never model prose. */
export function fabricReaderLedgerPath(root: string, runId: string): string {
  if (!/^[A-Za-z0-9_-]{1,128}$/.test(runId)) throw new Error("invalid Fabric Reader run identity");
  return join(tmpdir(), "lazy-harness-fabric-reader", hash(root), `${runId}.jsonl`);
}

export function fabricReaderLineage(): { runId: string } | undefined {
  try {
    const lineage = JSON.parse(process.env.PI_FABRIC_LINEAGE || "null");
    if (lineage?.version === 1 && lineage.worker === true && typeof lineage.runId === "string") {
      fabricReaderLedgerPath("", lineage.runId); // validate host identity before any filesystem operation
      return lineage;
    }
  } catch { /* ordinary Parent or malformed lineage: no Fabric ledger */ }
  return undefined;
}

/** Pi Fabric one-shot workers use --no-session; mirror the actual hook-owned meter, not child claims. */
export function persistFabricReaderLedger(ledger: Record<string, unknown>): void {
  const lineage = fabricReaderLineage();
  if (!lineage) return;
  const path = fabricReaderLedgerPath(String(ledger.root), lineage.runId);
  mkdirSync(dirname(path), { recursive: true, mode: 0o700 });
  const rows = [
    { type: "session", id: ledger.sessionId },
    { type: "custom", customType: "lazy-harness-reader-ledger-v1", data: { ...ledger, fabricRunId: lineage.runId } },
  ];
  const temporary = `${path}.${process.pid}.tmp`;
  writeFileSync(temporary, rows.map(row => JSON.stringify(row)).join("\n") + "\n", { mode: 0o600 });
  renameSync(temporary, path);
}

export function fabricReaderModelMatches(task: string, context: any, thinking: unknown): boolean {
  return field(task, "model") === `${context.model?.provider}/${context.model?.id}:low` && thinking === "low";
}

/** Consume only Fabric's native result proxy plus its matching visible JSON content. */
export function fabricReaderProxyResult(event: any): Record<string, any> {
  if (event.isError || event.is_error || event.details?.kind !== PROXY_KIND || event.details?.ref !== event.toolName) {
    throw new Error("Fabric Reader result lacks a successful native proxy");
  }
  const result = event.details.result;
  const text = Array.isArray(event.content) ? event.content.filter((part: any) => part?.type === "text").map((part: any) => part.text).join("\n") : "";
  let visible: unknown;
  try { visible = JSON.parse(text); } catch { throw new Error("Fabric Reader result content is missing or truncated"); }
  if (!result || typeof result !== "object" || JSON.stringify(visible) !== JSON.stringify(result)) {
    throw new Error("Fabric Reader visible content differs from its native result");
  }
  return result;
}

export function validateFabricReaderSpawn(root: string, task: string, model: string, event: any): string {
  const expected = fabricReaderRequest(root, task, model);
  const args = event.input || {};
  if (Object.keys(args).length !== Object.keys(expected).length || Object.entries(expected).some(([key, value]) => JSON.stringify(args[key]) !== JSON.stringify(value))) {
    throw new Error("Fabric Reader launch options differ from the prepared read-only fresh request");
  }
  const result = fabricReaderProxyResult(event);
  fabricReaderLedgerPath(root, result.id);
  if (result.name !== FABRIC_READER_NAME || result.runner !== "pi" || result.cwd !== root
    || result.model !== expected.model || result.thinking !== "low"
    || !["running", "starting", "pending", "completed"].includes(result.status)) {
    throw new Error("Fabric Reader handle model, cwd, runner or status mismatch");
  }
  return result.id;
}

export const FABRIC_READER_GUIDANCE = `Pi Reader uses Pi Fabric, not pi-subagents. Its current default envelope model is ${FABRIC_READER_DEFAULT_MODEL}; do not use the obsolete openai-codex route unless separately approved. Call lazy_reader_request with the exact identity/budget/task envelope; pass its details.request unchanged to agents.spawn inside fabric_exec and return the handle immediately. Continue Parent source/test work in parallel, then use agents.wait({id: handle.id}) only at the join point and return the full result. The existing Reader body AND all supported frontmatter are mapped: replace prompt, no inherited project context/skills, fresh seed, read-only tools, declared child guard, and soft/grace turn budget. Missing/mismatched child policy stamps cannot join. Only a matching content-bearing result delivered to Parent is evidence; status/automatic completion alone is not. Omit old Agent Contract/acceptance/output/artifacts/toolBudget call flags. Fabric owns native runtime artifacts; output:false forbids model-authored output files, not runtime scratch. Direct bounded map/read remains the unavailable/non-complete fallback. Do not install or invoke pi-subagents.`;
