import { expect, test } from "bun:test";
import { cpSync, existsSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { basename, join, resolve } from "node:path";
import { spawnSync } from "node:child_process";

const native = process.env.LAZY_OMP_NATIVE_TEST === "1" ? test : test.skip;
const source = resolve(import.meta.dir, "../../..");
for (const mode of ["print", "json"] as const) native(`native OMP ${mode}: real grounding deny, primary answer, no advisory model call`, () => {
  const sandbox = mkdtempSync(join(tmpdir(), "lh-omp-regression-"));
  const host = join(sandbox, "host");
  const home = join(sandbox, "home");
  const agent = join(sandbox, "agent");
  for (const path of [host, home, agent]) mkdirSync(path);
  cpSync(join(source, ".lazy-harness"), join(host, ".lazy-harness"), {
    recursive: true,
    filter: (path) => !["logs", "state", "tmp", "evidence", "generated", "__pycache__", "node_modules", ".cache"].includes(basename(path)),
  });
  expect(spawnSync("git", ["init", "--quiet", host]).status).toBe(0);
  const trace = join(sandbox, "trace.jsonl");
  const args = ["--cwd", host, "--print", ...(mode === "json" ? ["--mode", "json"] : []), "--model", "offline-omp-probe/scripted", "--max-time", "30", "--no-session", "--no-skills", "--no-rules", "--no-lsp", "--no-pty", "--extension", join(import.meta.dir, "fixtures/omp-native-provider.ts"), "Offline lifecycle regression"];
  const result = spawnSync(process.env.LAZY_OMP_BINARY || "omp", args, {
    env: { ...process.env, HOME: home, PI_CODING_AGENT_DIR: agent, OMP_PROFILE: "", LAZY_OMP_PROBE_LOG: trace },
    encoding: "utf8", timeout: 45000, maxBuffer: 4 * 1024 * 1024,
  });
  writeFileSync(join(sandbox, "result.json"), JSON.stringify({ status: result.status, error: String(result.error ?? ""), stdout: result.stdout, stderr: result.stderr }));
  expect(result.status, `native OMP evidence: ${sandbox}`).toBe(0);
  const rows = readFileSync(trace, "utf8").trim().split("\n").map((row) => JSON.parse(row));
  const calls = rows.filter((row) => row.event === "model");
  expect(calls).toHaveLength(2);
  expect(JSON.stringify(calls[0])).toContain("status=armed");
  expect(JSON.stringify(calls[1])).toContain("search-debt gate");
  expect(existsSync(join(host, "must-not-exist.txt"))).toBe(false);
  expect(result.stdout).toContain("OMP_OFFLINE_PRIMARY_ANSWER");
  expect(result.stdout).not.toContain("OMP_OFFLINE_ADVISORY_ONLY");
  expect(result.stderr).toContain("post-response advisory; primary stdout preserved");
}, 60000);
