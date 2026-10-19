import { expect, test } from "bun:test";
import { execFileSync, spawnSync } from "node:child_process";
import { cpSync, existsSync, mkdirSync, mkdtempSync, readFileSync, symlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { basename, join, resolve } from "node:path";
import { activateOmpReader } from "../omp/reader-definition.ts";

const native = process.env.LAZY_OMP_NATIVE_TEST === "1" ? test : test.skip;
for (const readCase of ["bounded", "legacy-limit", "over-cap"]) native(`real OMP Reader ${readCase}: native task, read ledger, content, join and write guard`, () => {
  const source = resolve(import.meta.dir, "../../..");
  const sandbox = mkdtempSync(join(tmpdir(), "lh-omp-reader-native-"));
  const root = join(sandbox, "host");
  const home = join(sandbox, "home");
  const agent = join(sandbox, "agent");
  mkdirSync(home); mkdirSync(agent);
  execFileSync("git", ["clone", "--quiet", "--shared", "--no-checkout", source, root]);
  cpSync(join(source, ".lazy-harness"), join(root, ".lazy-harness"), { recursive: true, filter: path => !["logs", "state", "tmp", "evidence", "generated", "__pycache__", "node_modules", ".cache"].includes(basename(path)) });
  symlinkSync(join(source, "node_modules"), join(root, "node_modules"), "dir");
  activateOmpReader(root, "offline-omp-reader/reader", true);
  const revision = execFileSync("git", ["rev-parse", "HEAD"], { cwd: root, encoding: "utf8" }).trim();
  const trace = join(sandbox, "trace.jsonl");
  const args = ["--cwd", root, "--print", "--model", "offline-omp-reader/parent", "--thinking", "low", "--max-time", "90", "--no-skills", "--no-rules", "--no-lsp", "--no-pty", "--extension", join(import.meta.dir, "fixtures/omp-native-reader-provider.ts"), "Offline native Reader regression"];
  const result = spawnSync(process.env.LAZY_OMP_BINARY || "omp", args, { env: { ...process.env, HOME: home, PI_CODING_AGENT_DIR: agent, OMP_PROFILE: "", LAZY_OMP_PROBE_LOG: trace, LAZY_OMP_READER_ROOT: root, LAZY_OMP_READER_REVISION: revision, LAZY_OMP_READER_CASE: readCase }, encoding: "utf8", timeout: 110000, maxBuffer: 16 * 1024 * 1024 });
  writeFileSync(join(sandbox, "result.json"), JSON.stringify({ status: result.status, error: String(result.error ?? ""), stdout: result.stdout, stderr: result.stderr }));
  expect(result.status, `native evidence: ${sandbox}`).toBe(0);
  const rows = readFileSync(trace, "utf8").trim().split("\n").map(row => JSON.parse(row));
  const yieldCall = rows.find(row => row.event === "tool_call" && row.toolName === "yield");
  expect(yieldCall, `native terminal call: ${sandbox}`).toBeDefined();
  const directYield = Object.keys(yieldCall.input).join() === "data";
  expect(Object.keys(yieldCall.input)).toEqual([directYield ? "data" : "result"]);
  // OMP 18 terminates on yield itself; older OMP emits one scripted epilogue.
  expect(rows.filter(row => row.model === "reader").map(row => row.turn), `native evidence: ${sandbox}`).toEqual(directYield ? [0, 1, 2, 3, 4, 5, 6] : [0, 1, 2, 3, 4, 5, 6, 7]);
  const afterRead = rows.find(row => row.model === "reader" && row.turn === 6);
  const readResult = afterRead.messages.find((message: any) => message.role === "toolResult" && message.toolName === "read");
  expect(rows.filter(row => row.model === "parent")).toHaveLength(4);
  const afterJoin = rows.find(row => row.model === "parent" && row.turn === 2);
  const joinResult = afterJoin.messages.find((message: any) => message.role === "toolResult" && message.toolName === "lazy_reader_join");
  if (readCase === "bounded") {
    const lines = readResult.details.displayContent.lineNumbers;
    // 16 adds trailing context; 18 returns the exact raw selector. Charge the safe 50-line ceiling in both.
    expect([47, 50]).toContain(lines.length);
    expect(lines).toEqual(Array.from({ length: lines.length }, (_, i) => i + 1));
    expect(readResult.isError).toBe(false);
    expect(joinResult.details).toMatchObject({ joined: true, readCalls: 1, requestedLines: 50, maxObservedReadLimit: 50, failedToolCalls: 0 });
    expect(readFileSync(join(root, "native-joined.txt"), "utf8")).toBe("native Reader joined");
    expect(result.stdout).toContain("OMP_NATIVE_READER_JOINED");
  } else {
    expect(readResult.isError).toBe(true);
    expect(JSON.stringify(readResult.content)).toContain("Reader boundary");
    expect(joinResult.isError).toBe(true);
    expect(existsSync(join(root, "native-joined.txt"))).toBe(false);
    expect(result.stdout).toContain("OMP_NATIVE_READER_REJECTED");
  }
}, 120000);
