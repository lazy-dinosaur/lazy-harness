import { createHash } from "node:crypto";
import { closeSync, constants, fstatSync, openSync, readSync, realpathSync } from "node:fs";
import { isAbsolute, relative, resolve } from "node:path";

const OPEN = "\n<record-judgement>\n";
const CLOSE = "\n</record-judgement>";
const MAX_PACKET_BYTES = 8192;
const MAX_RECORD_BYTES = 1024 * 1024;
const MAX_TARGETS = 128;
const MAX_STARTED_CALLS = 256;
const WRITE_NAMES = new Set(["write", "edit", "insert", "replace", "multiedit", "write_file", "edit_file"]);
const READ_NAMES = new Set(["read", "read_file", "read_text_file"]);
const RECORD_PATH = /^\.lazy-harness\/(?:(?:domain|spec|behavior|tests|decisions|ssot|planning|plans)\/.+\.(?:md|xml|json|jsonl)|knowledge\/(?:candidates|graph-drafts|corrections)\.jsonl)$/;

type JsonObject = Record<string, unknown>;
type Disposition = "required" | "reuse" | "no-record" | "pending";
type Fact = { path: string; fact: string };
type Judgement = { disposition: Disposition; reason: string; facts: Fact[] };
type Snapshot = { path: string; sha256: string; bytes: number };
type Started = { name: string; path: string; epoch: number; inputHash: string };
type Receipt = Snapshot & Started & { toolCallId: string; is_error: false; readback: "runtime-file" };
export type CaptureValidation = {
  schemaVersion: "1.0";
  root: string;
  epoch: number;
  status: "unverified" | "pending" | "no-record-asserted" | "evidence-linked";
  reason: string;
  semanticStatus: "llm-judgement-not-verified";
  approvalStatus: "not-evaluated";
  judgement?: Judgement;
  facts: Array<Fact & { status: "unverified" | "evidence-linked"; receipt?: Receipt }>;
};

export const CAPTURE_GUIDANCE = [
  "Capture judgement: you own semantic necessity, fact relevance, reasons, ownership and current approval.",
  "Capture newly confirmed durable facts before completion in one existing primary .lazy-harness record where suitable; add other narratives only for independent deltas.",
  "User corrections that change facts, reasons, constraints or ownership require durable capture too. Preserve the correction and its reason; capture success never renews stale execution approval (ADR 0038).",
  "Do not rewrite unchanged status or ask for approval again merely to satisfy capture. Reuse needs a successful current read of the relevant record and your current judgement; stale evidence is not success.",
  "For a capture decision, append a terminal envelope to your ordinary complete answer: ",
  '<record-judgement>\n{"disposition":"required|reuse|no-record|pending","reason":"your reason","facts":[{"path":".lazy-harness/planning/example.md","fact":"relevant fact, reason and ownership"}]}\n</record-judgement>',
  "Put each marker on its own line, JSON between them, and nothing after the closing marker. Use one actual disposition, not the alternatives string. no-record uses empty facts. No seven-layer ceremony is required.",
  "Do not invent toolCallIds, hashes, root, session or runtime fields: the adapter attaches actual structural evidence. Missing/malformed judgement stays unverified, never no-record. Pending capture is not completion or permission for action.",
].join("\n");

function object(value: unknown): value is JsonObject {
  return !!value && typeof value === "object" && !Array.isArray(value);
}
function nonempty(value: unknown): value is string {
  return typeof value === "string" && value.trim().length > 0;
}
function leaf(name: string): string {
  return name.toLowerCase().split(/[.:]|__/).at(-1) ?? "";
}
function parseJudgement(raw: string): Judgement | undefined {
  if (raw.split(OPEN).length !== 2 || raw.split(CLOSE).length !== 2 || !raw.endsWith(CLOSE)) return undefined;
  const packet = raw.slice(raw.indexOf(OPEN) + OPEN.length, -CLOSE.length);
  if (Buffer.byteLength(packet) > MAX_PACKET_BYTES) return undefined;
  try {
    const value: unknown = JSON.parse(packet);
    if (!object(value) || Object.keys(value).some((key) => !["disposition", "reason", "facts"].includes(key))) return undefined;
    const { disposition, reason, facts } = value;
    if (disposition !== "required" && disposition !== "reuse" && disposition !== "no-record" && disposition !== "pending") return undefined;
    if (!nonempty(reason) || !Array.isArray(facts) || facts.length > 20) return undefined;
    const parsed: Fact[] = [];
    for (const fact of facts) {
      if (!object(fact) || Object.keys(fact).some((key) => !["path", "fact"].includes(key)) || !nonempty(fact.path) || !nonempty(fact.fact)) return undefined;
      parsed.push({ path: fact.path, fact: fact.fact });
    }
    if (disposition === "no-record" ? parsed.length !== 0 : disposition !== "pending" && parsed.length === 0) return undefined;
    return { disposition, reason, facts: parsed };
  } catch { return undefined; }
}

/** One active root/work unit per extension instance. No journal or restored receipts.
 * Only 128 latest record targets and 256 pending calls survive tool-history projection.
 * Session/steer/work-unit invalidation clears them; eviction requires a fresh read.
 */
export class CaptureEvidence {
  private root = "";
  private started = new Map<string, Started>();
  private receipts = new Map<string, { write?: Receipt; read?: Receipt }>();
  private seenIds = new Set<string>();

  reset(root: string): void {
    this.root = root;
    this.started.clear();
    this.receipts.clear();
    this.seenIds.clear();
  }

  private target(root: string, cwd: string, input: unknown): string | undefined {
    if (!object(input)) return undefined;
    const paths = [input.path, input.file_path, input.filePath].filter(nonempty);
    if (paths.length !== 1) return undefined;
    const path = relative(root, resolve(cwd, paths[0]));
    if (!RECORD_PATH.test(path) || isAbsolute(path) || path.split(/[\\/]/).includes("..")) return undefined;
    return path;
  }

  private snapshot(root: string, path: string): Snapshot | undefined {
    let fd: number | undefined;
    try {
      const actual = realpathSync(resolve(root, path));
      const inside = relative(realpathSync(root), actual);
      if (isAbsolute(inside) || inside.split(/[\\/]/).includes("..") || !RECORD_PATH.test(inside)) return undefined;
      fd = openSync(actual, constants.O_RDONLY | constants.O_NOFOLLOW);
      const before = fstatSync(fd);
      if (!before.isFile() || before.size > MAX_RECORD_BYTES) return undefined;
      const buffer = Buffer.alloc(MAX_RECORD_BYTES + 1);
      let size = 0;
      while (size < buffer.length) {
        const count = readSync(fd, buffer, size, buffer.length - size, null);
        if (count === 0) break;
        size += count;
      }
      const after = fstatSync(fd);
      if (size > MAX_RECORD_BYTES || before.size !== after.size || before.mtimeMs !== after.mtimeMs || realpathSync(resolve(root, path)) !== actual) return undefined;
      return { path, sha256: createHash("sha256").update(buffer.subarray(0, size)).digest("hex"), bytes: size };
    } catch { return undefined; }
    finally { if (fd !== undefined) closeSync(fd); }
  }

  start(root: string, cwd: string, epoch: number, id: unknown, name: string, input: unknown): void {
    if (this.root !== root) this.reset(root);
    if (!nonempty(id)) return;
    // Duplicate IDs invalidate issued proof too, even if the recent-ID set evicted
    // the ID while its relevant receipt survived unrelated tool history.
    let duplicate = this.seenIds.has(id);
    for (const [path, receipts] of this.receipts) {
      if (receipts.write?.toolCallId === id) { delete receipts.write; duplicate = true; }
      if (receipts.read?.toolCallId === id) { delete receipts.read; duplicate = true; }
      if (!receipts.write && !receipts.read) this.receipts.delete(path);
    }
    if (duplicate) { this.started.delete(id); return; }
    this.seenIds.add(id);
    if (this.seenIds.size > MAX_STARTED_CALLS) this.seenIds.delete(this.seenIds.values().next().value!);
    const path = this.target(root, cwd, input);
    const tool = leaf(name);
    if (!path || (!WRITE_NAMES.has(tool) && !READ_NAMES.has(tool))) return;
    const inputHash = createHash("sha256").update(JSON.stringify(input)).digest("hex");
    this.started.set(id, { path, name: tool, epoch, inputHash });
    if (this.started.size > MAX_STARTED_CALLS) this.started.delete(this.started.keys().next().value!);
  }

  complete(root: string, cwd: string, epoch: number, id: unknown, name: string, input: unknown, isError: unknown, content: unknown): void {
    if (root !== this.root || !nonempty(id)) return;
    const call = this.started.get(id);
    this.started.delete(id);
    const path = this.target(root, cwd, input);
    if (!call || call.epoch !== epoch || call.path !== path || call.name !== leaf(name) || call.inputHash !== createHash("sha256").update(JSON.stringify(input)).digest("hex")) return;
    const prior = this.receipts.get(call.path);
    this.receipts.delete(call.path);
    if (isError !== false || !Array.isArray(content) || !content.some((part) => object(part) && part.type === "text" && nonempty(part.text))) return;
    const snapshot = this.snapshot(root, call.path);
    if (!snapshot) return;
    const receipt: Receipt = { ...call, ...snapshot, toolCallId: id, is_error: false, readback: "runtime-file" };
    this.receipts.set(call.path, WRITE_NAMES.has(call.name) ? { write: receipt } : {
      read: receipt,
      write: prior?.write?.sha256 === snapshot.sha256 ? prior.write : undefined,
    });
    if (this.receipts.size > MAX_TARGETS) this.receipts.delete(this.receipts.keys().next().value!);
  }

  evaluate(root: string, epoch: number, raw: string): CaptureValidation {
    const result: CaptureValidation = { schemaVersion: "1.0", root, epoch, status: "unverified", reason: "judgement-absent-or-malformed", semanticStatus: "llm-judgement-not-verified", approvalStatus: "not-evaluated", facts: [] };
    const judgement = parseJudgement(raw);
    if (!judgement) return result;
    result.judgement = judgement;
    result.reason = judgement.reason;
    if (judgement.disposition === "no-record") { result.status = "no-record-asserted"; return result; }
    if (judgement.disposition === "pending") { result.status = "pending"; return result; }
    result.facts = judgement.facts.map((fact) => {
      const path = this.target(root, root, { path: fact.path });
      const stored = root === this.root && path ? this.receipts.get(path) : undefined;
      const receipt = judgement.disposition === "reuse" ? stored?.read : stored?.write;
      const current = path ? this.snapshot(root, path) : undefined;
      const names = judgement.disposition === "reuse" ? READ_NAMES : WRITE_NAMES;
      if (!receipt || receipt.epoch !== epoch || !names.has(receipt.name) || !current || receipt.sha256 !== current.sha256) return { ...fact, status: "unverified" };
      return { ...fact, status: "evidence-linked", receipt };
    });
    result.status = result.facts.every((fact) => fact.status === "evidence-linked") ? "evidence-linked" : "unverified";
    if (result.status === "unverified") result.reason = "capture-unverified: missing successful current relevant tool/readback; read and rejudge or complete required capture";
    return result;
  }
}
