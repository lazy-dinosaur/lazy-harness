export type ReaderResultStatus = "complete" | "incomplete" | "conflict";
export type ReaderResultPacket = {
  status: ReaderResultStatus;
  root: string;
  revision: string;
  evidenceEpoch: string;
};

// Result prose may quote identity values once. Launch tasks have a separate,
// strict parser: do not use this normalization to admit launch identities.
export function parseReaderResultPacket(text: string): ReaderResultPacket | undefined {
  const fields = new Map<string, string>();
  const names = ["LAZY_HARNESS_READER_RESULT", "root", "revision", "evidenceEpoch"];
  for (const line of text.split(/\r?\n/)) {
    const candidate = line.match(/^[ \t]*(LAZY_HARNESS_READER_RESULT|root|revision|evidenceEpoch)\b/i);
    if (!candidate) continue;
    const name = names.find((name) => name.toLowerCase() === candidate[1].toLowerCase())!;
    const match = line.match(new RegExp(`^${name}:[ \\t]*(.*?)[ \\t]*$`));
    if (!match || fields.has(name)) return undefined;
    let value = match[1];
    if (name !== "LAZY_HARNESS_READER_RESULT" && value.includes("`")) {
      if (!/^`[^`]+`$/.test(value)) return undefined;
      value = value.slice(1, -1);
    }
    if (!value) return undefined;
    fields.set(name, value);
  }
  if (fields.size !== names.length) return undefined;
  const status = fields.get("LAZY_HARNESS_READER_RESULT");
  if (status !== "complete" && status !== "incomplete" && status !== "conflict") return undefined;
  return { status, root: fields.get("root")!, revision: fields.get("revision")!, evidenceEpoch: fields.get("evidenceEpoch")! };
}
