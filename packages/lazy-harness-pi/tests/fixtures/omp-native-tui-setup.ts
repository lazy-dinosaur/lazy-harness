// Prepare an isolated real-TUI fixture; run the printed command with a PTY.
import { execFileSync } from "node:child_process";
import { cpSync, mkdirSync, mkdtempSync, symlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { basename, join, resolve } from "node:path";
import { activateOmpReader } from "../../omp/reader-definition.ts";

const source = resolve(import.meta.dir, "../../../..");
const sandbox = mkdtempSync(join(tmpdir(), "lh-omp-tui-"));
const root = join(sandbox, "host");
const home = join(sandbox, "home");
const agent = join(sandbox, "agent");
mkdirSync(home); mkdirSync(agent);
// Only the fixture's disposable agent directory; avoid unrelated onboarding.
writeFileSync(join(agent, "config.yml"), "setupVersion: 1\n");
execFileSync("git", ["clone", "--quiet", "--shared", "--no-checkout", source, root]);
cpSync(join(source, ".lazy-harness"), join(root, ".lazy-harness"), { recursive: true, filter: path => !["logs", "state", "tmp", "evidence", "generated", "__pycache__", "node_modules", ".cache"].includes(basename(path)) });
symlinkSync(join(source, "node_modules"), join(root, "node_modules"), "dir");
activateOmpReader(root, "offline-omp-reader/reader", true);
const revision = execFileSync("git", ["rev-parse", "HEAD"], { cwd: root, encoding: "utf8" }).trim();
const quote = (value: string) => "'" + value.replaceAll("'", "'\\''") + "'";
const args = ["env", `HOME=${home}`, `PI_CODING_AGENT_DIR=${agent}`, "OMP_PROFILE=", `LAZY_OMP_PROBE_LOG=${join(sandbox, "trace.jsonl")}`, `LAZY_OMP_READER_ROOT=${root}`, `LAZY_OMP_READER_REVISION=${revision}`, "LAZY_OMP_QUEUE_MODE=ask", "LAZY_OMP_STEER_PROBE=", "omp", "--cwd", root, "--model", "offline-omp-reader/parent", "--thinking", "low", "--no-skills", "--no-rules", "--no-lsp", "--no-pty", "--extension", join(import.meta.dir, "omp-native-reader-provider.ts"), "Offline native interactive ask probe"];
console.log(JSON.stringify({ sandbox, command: args.map(quote).join(" ") }));
