export type ReaderStatusInspectionContext = {
  root: string;
  runId: string;
  evidenceEpoch: number;
  currentEpoch: number;
  pending: boolean;
};

const READER_STATUS_ARG_KEYS = new Set(["action", "id", "includeProgress", "view", "lines"]);

/** Pure public predicate; runtime-owned state is supplied by the caller. */
export function permitsOwnedReaderStatusInspection(root: string, name: string, args: Record<string, unknown>, context: ReaderStatusInspectionContext): boolean {
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
