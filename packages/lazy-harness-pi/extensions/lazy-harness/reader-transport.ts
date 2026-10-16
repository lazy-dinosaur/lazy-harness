export type ReaderLaunchIdentity = { agent: string; task: string; model: string };
export type ReaderDelivery = { runId: string; sessionFile: string; text: string };

/** Runtime-specific admission/binding, never an alternate ledger or join authority. */
export interface ReaderTransport {
  guidance?(root: string): string;
  prepare(root: string, name: string, args: Record<string, unknown>): ReaderLaunchIdentity | undefined;
  admit(toolCallId: string): void;
  receive(event: any): ReaderDelivery;
  childModelMatches(task: string, context: any): boolean;
  isTerminalCall(name: string, args: Record<string, unknown>): boolean;
  normalizeRead(toolCallId: string, args: Record<string, unknown>): Record<string, unknown>;
  readResultError(event: any): string | undefined;
  sessionHeader?(entries: unknown[]): { type: "session"; id: string } | undefined;
  dispose(): void;
}
