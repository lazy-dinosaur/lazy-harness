import { expect, test } from "bun:test";
import { execFileSync, spawn } from "node:child_process";
import { cpSync, existsSync, mkdirSync, mkdtempSync, readFileSync, symlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { basename, join, resolve } from "node:path";
import { activateOmpReader } from "../omp/reader-definition.ts";

const native = process.env.LAZY_OMP_NATIVE_TEST === "1" ? test : test.skip;
for (const queueMode of ["steer", "follow_up", "new_session", "ask"] as const) native(`native RPC ${queueMode} respects its grounding boundary`, async () => {
  const source = resolve(import.meta.dir, "../../..");
  const sandbox = mkdtempSync(join(tmpdir(), "lh-omp-steer-"));
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
  const events: any[] = [];
  let stderr = "";
  let pending = "";
  let steerSent = false;
  let ended = false;
  let restarted = false;
  const child = spawn(process.env.LAZY_OMP_BINARY || "omp", ["--cwd", root, "--mode", "rpc", "--model", "offline-omp-reader/parent", "--thinking", "low", "--no-skills", "--no-rules", "--no-lsp", "--no-pty", "--extension", join(import.meta.dir, "fixtures/omp-native-reader-provider.ts")], {
    env: { ...process.env, HOME: home, PI_CODING_AGENT_DIR: agent, OMP_PROFILE: "", LAZY_OMP_PROBE_LOG: trace, LAZY_OMP_READER_ROOT: root, LAZY_OMP_READER_REVISION: revision, LAZY_OMP_READER_CASE: "bounded", LAZY_OMP_STEER_PROBE: ["steer", "follow_up"].includes(queueMode) ? "1" : "", LAZY_OMP_QUEUE_MODE: queueMode, LAZY_OMP_STEER_GATE_USED: "" },
    stdio: ["pipe", "pipe", "pipe"],
  });
  const send = (command: unknown) => child.stdin.write(JSON.stringify(command) + "\n");
  await new Promise<void>((resolveRun, reject) => {
    const timer = setTimeout(() => { child.kill("SIGKILL"); reject(new Error(`native steer timeout: ${sandbox}`)); }, 90000);
    child.on("error", error => { clearTimeout(timer); reject(error); });
    child.stderr.setEncoding("utf8");
    child.stdout.setEncoding("utf8");
    child.stderr.on("data", chunk => {
      stderr += chunk;
      if (!steerSent && stderr.includes("OMP_STEER_READER_READY")) {
        steerSent = true;
        send({ id: "steer", type: queueMode, message: queueMode === "steer" ? "Stop the previous objective. New scope: do not use the old Reader packet or write until fresh grounding." : "Continue the same approved objective using unchanged grounding; write the follow-up result." });
      }
    });
    child.stdout.on("data", chunk => {
      pending += chunk;
      let newline: number;
      while ((newline = pending.indexOf("\n")) >= 0) {
        const line = pending.slice(0, newline); pending = pending.slice(newline + 1);
        let event: any;
        try { event = JSON.parse(line); } catch { continue; }
        events.push(event);
        if (event.type === "ready") send({ id: "prompt", type: "prompt", message: "Offline native steer regression" });
        if (queueMode === "ask" && event.type === "extension_ui_request" && event.method === "select") {
          send({ type: "extension_ui_response", id: event.id, value: "Continue" });
        }
        if (event.type === "response" && event.id === "steer" && event.success === true) child.kill("SIGUSR2");
        if (event.type === "response" && event.id === "reset" && event.success === true) {
          send({ id: "second-prompt", type: "prompt", message: "SECOND_SESSION_BOUNDARY_PROBE" });
        }
        if (event.type === "agent_end") {
          if (queueMode === "new_session" && !restarted) {
            restarted = true;
            send({ id: "reset", type: "new_session" });
          } else { ended = true; child.kill("SIGTERM"); }
        }
      }
    });
    child.on("exit", () => { clearTimeout(timer); resolveRun(); });
  });
  writeFileSync(join(sandbox, "rpc.json"), JSON.stringify({ events, stderr, steerSent, ended }));
  expect(ended, `native evidence: ${sandbox}`).toBe(true);
  if (queueMode !== "ask") expect(events.some(event => event.type === "response" && event.id === (queueMode === "new_session" ? "reset" : "steer") && event.success === true)).toBe(true);
  const rows = readFileSync(trace, "utf8").trim().split("\n").map(line => JSON.parse(line));
  const parentRows = rows.filter(row => row.model === "parent");
  if (queueMode === "ask") {
    expect(events.some(event => event.type === "extension_ui_request" && event.method === "select")).toBe(false);
    const answer = parentRows.find(row => row.turn === 1)?.messages.find((m: any) => m.role === "toolResult" && m.toolName === "ask");
    expect(answer?.isError).toBe(true);
    expect(JSON.stringify(answer?.content)).toContain("Tool ask not found");
    expect(existsSync(join(root, "native-ask-approved.txt"))).toBe(false);
    return;
  }
  if (queueMode === "new_session") {
    expect(existsSync(join(root, "native-stale-session.txt")), `new session must not inherit write permission: ${sandbox}`).toBe(false);
    expect(rows.filter(row => row.model === "reader" && row.turn === 0)).toHaveLength(2);
    expect(readFileSync(join(root, "native-session-recovered.txt"), "utf8")).toBe("fresh session grounded");
    return;
  }
  if (queueMode === "follow_up") {
    expect(events.some(event => event.type === "message_start" && event.message?.steering === true)).toBe(false);
    expect(rows.filter(row => row.model === "reader" && row.turn === 0)).toHaveLength(1);
    const joins = parentRows.flatMap(row => row.output).filter((part: any) => part.name === "lazy_reader_join");
    expect(joins).toHaveLength(1);
    // OMP 18 starts a fresh runtime turn for follow_up. A new bookkeeping epoch
    // is allowed only with unchanged work-unit evidence reuse (no new Reader).
    const laterMarkers = parentRows.at(-1)?.messages.flatMap((m: any) => Array.isArray(m.content) ? m.content : [])
      .filter((p: any) => p.type === "text" && p.text.includes("lazy-harness read-debt:") && p.text.includes("evidence-epoch=2")) ?? [];
    for (const marker of laterMarkers) expect(marker.text).toContain("status=reused-work-unit");
    expect(readFileSync(join(root, "native-follow-up.txt"), "utf8")).toBe("reused grounding");
    return;
  }
  expect(events.some(event => event.type === "message_start" && event.message?.role === "user" && event.message.steering === true), `native evidence: ${sandbox}`).toBe(true);
  expect(JSON.stringify(parentRows.find(row => row.turn === 1)?.messages), `native epoch must advance: ${sandbox}`).toContain("evidence-epoch=2");
  const afterJoin = parentRows.find(row => row.turn === 2);
  const joinResult = afterJoin?.messages.find((m: any) => m.role === "toolResult" && m.toolName === "lazy_reader_join");
  expect(joinResult?.isError, `late Reader must fail: ${sandbox}`).toBe(true);
  expect(existsSync(join(root, "native-joined.txt")), `stale write must not occur: ${sandbox}`).toBe(false);
  const recovery = parentRows.find(row => row.turn === 5)?.messages.find((m: any) => m.role === "toolResult" && m.toolCallId === "parent-4");
  expect(recovery?.details, `fresh epoch must recover: ${sandbox}`).toMatchObject({ joined: true, evidenceEpoch: 2 });
  expect(readFileSync(join(root, "native-recovered.txt"), "utf8")).toBe("fresh epoch joined");
}, 100000);
