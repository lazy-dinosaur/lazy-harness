export type OutputMode = "tui" | "rpc" | "json" | "print";

/** OMP 16.2.2 has no ctx.mode. Only explicit CLI output flags are evidence;
 * SDK/embedded/implicit modes stay unknown. Never equate !hasUI with print.
 */
export function explicitOmpOutputMode(args: readonly string[]): OutputMode | undefined {
  let mode: string | undefined;
  let print = false;
  // Value-taking flags preceding a value that happens to look like an output
  // flag must not turn that value into a capability (e.g. --system-prompt -p).
  const valued = new Set([
    "--model", "--smol", "--slow", "--plan", "--provider", "--api-key",
    "--system-prompt", "--append-system-prompt", "--profile", "--alias", "--cwd",
    "--config", "--session-dir", "--provider-session-id", "--fork", "--models", "--tools", "--thinking",
    "--hook", "--extension", "-e", "--skills", "--export", "--max-time",
    "--approval-mode", "--plugin-dir",
  ]);
  for (let index = 0; index < args.length; index++) {
    const arg = args[index];
    if (arg === "--") break;
    if (arg === "--mode") mode = args[++index] ?? "unknown";
    else if (arg.startsWith("--mode=")) mode = arg.slice("--mode=".length);
    else if (arg === "--print" || arg === "-p") print = true;
    else if (valued.has(arg)) index++;
  }
  // RPC wins over -p. Unknown modes must not acquire headless authority.
  if (mode === "rpc" || mode === "rpc-ui") return "rpc";
  if (mode === "json") return "json";
  if (mode !== undefined && mode !== "text") return undefined;
  return print ? "print" : undefined;
}
