/** OMP 18 may prepend one v1 title row. It is metadata, never session identity. */
export function ompSessionHeader(entries: unknown[]): { type: "session"; id: string } | undefined {
  const isRecord = (value: unknown): value is Record<string, unknown> => Boolean(value && typeof value === "object" && !Array.isArray(value));
  const first = entries[0];
  const header = isRecord(first) && first.type === "title" && first.v === 1 ? entries[1] : first;
  if (!isRecord(header) || header.type !== "session" || typeof header.id !== "string" || !header.id
    || entries.filter(entry => isRecord(entry) && entry.type === "session").length !== 1) return undefined;
  return { type: "session", id: header.id };
}
