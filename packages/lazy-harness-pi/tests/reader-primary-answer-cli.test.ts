import { test, expect } from "bun:test";
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, cpSync, symlinkSync, existsSync, realpathSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { execFileSync, spawn } from "node:child_process";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";

const currentHost = resolve(import.meta.dir, "../../..");
const installedPi = dirname(dirname(realpathSync(fileURLToPath(import.meta.resolve("@earendil-works/pi-coding-agent")))));
const jsonLines = (file: string): any[] => existsSync(file) ? readFileSync(file, "utf8").split("\n").filter(Boolean).map((line) => JSON.parse(line)) : [];

// One real CLI Parent -> native detached runner -> SDK Reader -> native notify ->
// actual host lazy_reader_join. No captured handlers or child factory injection.
test.each(["A", "B"].flatMap((arm) => ["json", "text"].flatMap((mode) => ["capture", "placement"].map((advisory) => [arm, mode, advisory]))))("%s real production hook: %s %s", async (arm, mode, advisory) => {
  const upstream = process.env[arm === "A" ? "LAZY_READER_NATIVE_SYNC" : "LAZY_READER_NATIVE_ASYNC"];
  if (!upstream) throw new Error("Supply read-only native package paths via LAZY_READER_NATIVE_SYNC/ASYNC");
  const host = currentHost;
  const scenario = "complete";
  const evidenceLimit = Date.now() + 70000;
  const sandbox = mkdtempSync(join(tmpdir(), "reader-native-launcher-"));
  const root = join(sandbox, "project");
  const agentDir = join(sandbox, "agent");
  const tracePath = join(sandbox, "trace.jsonl");
  const runtimeDir = join(sandbox, "native-runs");
  let child: ReturnType<typeof spawn> | undefined;
  let stdout = "", stderr = "";
  let timeout: ReturnType<typeof setTimeout> | undefined;
  try {
    execFileSync("git", ["clone", "--quiet", "--shared", "--no-checkout", host, root]);
    mkdirSync(join(root, ".lazy-harness/bin"), { recursive: true });
    mkdirSync(join(root, ".lazy-harness/spec"), { recursive: true });
    mkdirSync(join(root, ".pi"));
    cpSync(join(host, ".lazy-harness/hooks/lifecycle"), join(root, ".lazy-harness/hooks/lifecycle"), { recursive: true });
    const hookPath = ".lazy-harness/hooks/lifecycle/on-response-completed.sh";
    expect(readFileSync(join(root, hookPath))).toEqual(readFileSync(join(host, hookPath)));
    for (const helper of ["check-analysis-discovery-capture.sh", "check-project-rule-placement.sh"]) expect(readFileSync(join(root, ".lazy-harness/hooks/lifecycle/helpers", helper))).toEqual(readFileSync(join(host, ".lazy-harness/hooks/lifecycle/helpers", helper)));
    mkdirSync(agentDir);
    mkdirSync(join(sandbox, "home"));
    writeFileSync(join(root, ".lazy-harness/bin/lazy"), "#!/bin/sh\nprintf 'native-fact: .lazy-harness/spec/fact.md\\n'\n", { mode: 0o755 });
    writeFileSync(join(root, ".lazy-harness/spec/fact.md"), "canonical fact: delivery matters\n");
    writeFileSync(join(root, ".lazy-harness/spec/second.md"), "canonical second fact: never drop successful reads\n");
    writeFileSync(join(root, ".lazy-harness/spec/unread.md"), "not read by Reader\n");
    writeFileSync(join(root, "source.txt"), "Parent must consume the Reader packet before answering.\n");
    const revision = execFileSync("git", ["rev-parse", "HEAD"], { cwd: root, encoding: "utf8" }).trim();
    const provider = join(agentDir, "offline-provider.ts");
    cpSync(join(import.meta.dir, "fixtures/native-reader-provider.ts"), provider);
    // Test-only explicit registration: foreground does not discover ambient providers.
    // The production Reader body/tools and actual host ledger extension are unchanged.
    mkdirSync(join(root, ".pi/agents"));
    const definition = readFileSync(join(host, "packages/lazy-harness-pi/agents/record-reader.md"), "utf8");
    const fixtureDefinition = definition.replace("subagentOnlyExtensions: ../extensions/lazy-harness/index.ts", `subagentOnlyExtensions: ${join(host, "packages/lazy-harness-pi/extensions/lazy-harness/index.ts")}, ${provider}`);
    expect(fixtureDefinition.split("---").slice(2)).toEqual(definition.split("---").slice(2));
    writeFileSync(join(root, ".pi/agents/record-reader.md"), fixtureDefinition);
    writeFileSync(join(sandbox, "fixture-overlay.json"), JSON.stringify({ arm, originalDefinitionSha256: createHash("sha256").update(definition).digest("hex"), fixtureDefinitionSha256: createHash("sha256").update(fixtureDefinition).digest("hex"), providerSha256: createHash("sha256").update(readFileSync(provider)).digest("hex"), change: "Only child extension list; host ledger extension plus offline provider" }, null, 2));
    // Resolve only the already installed peer packages, without installing anything.
    symlinkSync(realpathSync(join(host, "node_modules")), join(agentDir, "node_modules"));
    writeFileSync(join(agentDir, "settings.json"), JSON.stringify({ extensions: [provider], compaction: { enabled: false }, retry: { enabled: false }, quietStartup: true }));
    writeFileSync(join(root, ".pi/settings.json"), JSON.stringify({ packages: [upstream, join(host, "packages/lazy-harness-pi")] }));
    writeFileSync(join(agentDir, "auth.json"), "{}");
    writeFileSync(tracePath, "");
    const env = {
      PATH: process.env.PATH!, HOME: join(sandbox, "home"), XDG_CONFIG_HOME: join(sandbox, "home/.config"),
      PI_CODING_AGENT_DIR: agentDir, PI_OFFLINE: "1", PI_SUBAGENTS_TEMP_ROOT: runtimeDir,
      PI_SUBAGENTS_PI_CODING_AGENT_PACKAGE_ROOT: installedPi,
      NATIVE_READER_ROOT: root, NATIVE_READER_TRACE: tracePath, NATIVE_READER_REVISION: revision, NATIVE_READER_ARM: arm, NATIVE_READER_SCENARIO: scenario, NATIVE_READER_ADVISORY: advisory, LAZY_PI_AGENT_END_TRACE: "1",
      NODE_OPTIONS: `--import=${join(import.meta.dir, "fixtures/native-reader-network-guard.mjs")}`,
      NO_COLOR: "1", TERM: "dumb",
    };
    // Explicit extension order places the passive observer before the unmodified
    // native agent_end handler. Child discovery still uses only temp settings.
    child = spawn("node", [join(installedPi, "dist/cli.js"), "--offline", "--approve", "--print", "--mode", mode, "--model", "offline-native-reader/scripted", "--thinking", "off", "--no-skills", "--no-context-files", "--no-prompt-templates", "--no-themes", "--extension", provider, "--extension", join(upstream, "index.ts"), "--system-prompt", "OFFLINE_NATIVE_PARENT: inspect source independently, then consume Reader content and join before answering.", "Inspect the delivery rule and answer after joining the Reader."], { cwd: root, env, detached: true, stdio: ["ignore", "pipe", "pipe"] });
    child.stdout!.on("data", (data) => { stdout += data; });
    child.stderr!.on("data", (data) => { stderr += data; });
    const exit = await Promise.race([
      new Promise<number | null>((resolveExit, reject) => { child!.on("error", reject); child!.on("close", resolveExit); }),
      new Promise<never>((_, reject) => { timeout = setTimeout(() => reject(new Error("Native Parent exceeded 60s deadline")), 60000); }),
    ]);
    clearTimeout(timeout);
    const parentExitAt = Date.now();
    // If Parent exits prematurely, let the already-launched Reader finish only
    // for failure evidence. This cannot resume Parent or fabricate delivery.
    const evidenceDeadline = Math.min(Date.now() + 15000, evidenceLimit);
    while (!jsonLines(tracePath).some((row) => row.event === "reader-agent-end") && Date.now() < evidenceDeadline) await new Promise((resolve) => setTimeout(resolve, 50));
    const trace = jsonLines(tracePath);
    expect(trace.filter((row) => row.event === "network-denied")).toEqual([]);
    expect(exit).toBe(0);
    const launch = trace.find((row) => row.event === "parent-tool-result" && row.result.toolName === "subagent")?.result;
    expect(launch).toBeDefined();
    expect(launch.isError).toBe(false);
    const ownedId = launch.details.asyncId ?? launch.details.runId;
    expect(typeof ownedId).toBe("string");
    const readerComplete = trace.find((row) => row.event === "reader-delayed-completion");
    if (arm === "A") expect(trace.filter((row) => row.event === "parent-notification")).toEqual([]);
    const readerEnd = trace.find((row) => row.event === "reader-agent-end");
    expect(readerEnd).toBeDefined();
    // Regression: the native index-backed drain must not treat a just-spawned,
    // not-yet-indexed runner as no work and let the actual Parent CLI exit.
    expect(parentExitAt, "Parent CLI exited before its owned native Reader ended").toBeGreaterThanOrEqual(readerEnd.at);
    expect(trace.filter((row) => row.event === "script-error")).toEqual([]);
    expect(readerComplete).toBeDefined();
    const independentRead = trace.find((row) => row.event === "parent-tool-result" && row.result.toolName === "read");
    const childStart = trace.find((row) => row.event === "reader-start");
    let completion: any;
    if (arm === "A") {
      expect(independentRead.at).toBeGreaterThanOrEqual(readerEnd.at);
      expect(childStart.pid).toBe(child.pid);
      expect(JSON.stringify(launch.content)).toContain("facts: canonical fact: delivery matters");
      expect(launch.details.mode).toBe("single");
      expect(launch.details.results).toHaveLength(1);
      completion = launch.details.results[0];
    } else {
      expect(independentRead.at).toBeLessThan(readerEnd.at);
      expect(childStart.pid).not.toBe(child.pid);
      const parentEnd = trace.find((row) => row.event === "parent-agent-end" && row.last.includes("Independent source inspection finished."));
      expect(parentEnd.hasUI).toBe(false);
      expect(readerComplete.at - parentEnd.at).toBeGreaterThanOrEqual(300);
      const notification = trace.find((row) => row.event === "parent-notification")?.message;
      expect(notification?.content).toContain("facts: canonical fact: delivery matters");
      completion = notification.details.completions.find((item: any) => item.runId === ownedId);
    }
    expect(completion.agent).toBe("lazy-harness.record-reader");
    expect(completion.sessionFile).toBe(childStart.sessionFile);
    const ledger = jsonLines(completion.sessionFile).filter((entry) => entry.type === "custom" && entry.customType === "lazy-harness-reader-ledger-v1").at(-1)?.data;
    expect(ledger).toMatchObject({ root, revision, evidenceEpoch: 1, terminal: true, readCalls: 2, requestedLines: 400, maxObservedReadLimit: 200, failedToolCalls: scenario === "failed-read" ? 1 : 0 });
    const expectedPaths = scenario === "failed-read" ? [".lazy-harness/spec/fact.md"] : [".lazy-harness/spec/fact.md", ".lazy-harness/spec/second.md"];
    expect(Object.keys(ledger.recordHashes)).toEqual(expectedPaths);
    const joined = trace.find((row) => row.event === "parent-tool-result" && row.result.toolName === "lazy_reader_join")?.result;
    expect(joined?.isError).toBe(scenario !== "complete");
    if (scenario === "complete") {
      expect(joined.details).toMatchObject({ joined: true, runId: ownedId, readCalls: ledger.readCalls, requestedLines: ledger.requestedLines, failedToolCalls: ledger.failedToolCalls, recordPaths: expectedPaths, recordCount: 2 });
      expect(joined.input).not.toHaveProperty("runId");
      expect(joined.input).not.toHaveProperty("readCalls");
      expect(joined.input).not.toHaveProperty("requestedLines");
      // Parent reports only the first path, but all successful Reader hashes join.
      expect(joined.input.recordPaths).toEqual([".lazy-harness/spec/fact.md"]);
    } else {
      const reasons: Record<string, string> = { "wrong-run-id": "run id does not match", "stale-epoch": "evidence epoch is stale", "false-counter": "self-report does not match", "unread-path": "outside runtime-owned successful reads", "changed-hash": "missing, changed, or unreadable", "failed-read": "failed-tool budget" };
      expect(JSON.stringify(joined.content)).toContain(reasons[scenario]);
      expect(JSON.stringify(joined.content)).toContain("bounded direct Parent fallback enabled");
      expect(joined.details?.joined).not.toBe(true);
    }
    const guard = join(host, "packages/lazy-harness-pi/extensions/lazy-harness/index.ts");
    expect(readFileSync(join(host, "packages/lazy-harness-pi/agents/record-reader.md"), "utf8")).toContain("subagentOnlyExtensions: ../extensions/lazy-harness/index.ts");
    const guardId = `sha256:${createHash("sha256").update(guard).digest("hex").slice(0, 16)}`;
    const resolvedExtensions = arm === "A" ? completion.launchResolvedExtensions : launch.details.launchResolvedExtensions;
    expect(resolvedExtensions.configured).toContain(guardId);
    expect(resolvedExtensions.effective).toContain(guardId);
    const providerId = `sha256:${createHash("sha256").update(provider).digest("hex").slice(0, 16)}`;
    expect(resolvedExtensions.configured).toContain(providerId);
    expect(resolvedExtensions.effective).toContain(providerId);
    writeFileSync(join(sandbox, "effective-extensions.json"), JSON.stringify(resolvedExtensions, null, 2));
    expect(trace.filter((row) => row.event === "parent-model")).toHaveLength(arm === "A" ? 4 : 5);
    expect(trace.filter((row) => row.event === "reader-model")).toHaveLength(8);
    const final = trace.filter((row) => row.event === "parent-agent-end").at(-1);
    const finalText = scenario === "complete" ? "Substantive answer: delivery matters." : "Rejected unsafe Reader join; bounded Parent fallback is required.";
    expect(final.last).toContain(finalText);
    expect(stdout).toContain(finalText);
    for (const claim of ["CLAIM-1", "CLAIM-2", "CLAIM-3", "CLAIM-4"]) { expect(stdout).toContain(claim); expect(final.last).toContain(claim); }
    // Upstream capture is typed, non-steering metadata, not a keyword STOP.
    // Read the actual native session delivery after the CLI exits; no mock sends.
    const parentEntries = jsonLines(final.sessionFile);
    const capture = parentEntries.filter((entry) => entry.type === "custom" && entry.customType === "lazy-harness-capture").at(-1);
    expect(capture?.data).toMatchObject({ root, epoch: 1, status: "unverified", semanticStatus: "llm-judgement-not-verified", approvalStatus: "not-evaluated" });
    expect(parentEntries.filter((entry) => entry.type === "custom_message" && entry.customType === "lazy-harness-capture")).toEqual([]);
    expect(stderr).toContain("Capture evidence: unverified");
    expect(stderr).toContain("Semantic relevance and approval are not runtime-verified");
    expect(stderr).toContain("primary stdout preserved");
    expect(stderr).not.toContain("Analysis discovery capture gate");
    if (advisory === "placement") {
      expect(stderr).toContain("Project rule placement gate");
      expect(stderr).toContain("primary stdout preserved");
    }
    expect(stdout).not.toContain("Partial replacement");
    expect(trace.filter((row) => row.event === "unwanted-advisory-continuation")).toEqual([]);
    expect(trace.filter((row) => row.event.endsWith("tool-result") && ["write", "edit", "multiedit"].includes(row.result.toolName))).toEqual([]);
    expect(readFileSync(join(root, ".lazy-harness/spec/fact.md"), "utf8")).toBe("canonical fact: delivery matters\n");
    expect(readFileSync(join(root, ".lazy-harness/spec/second.md"), "utf8")).toBe("canonical second fact: never drop successful reads\n");
    expect(existsSync(join(root, ".lazy-harness/knowledge/candidates.jsonl"))).toBe(false);
    if (scenario !== "complete") expect(final.last).not.toContain("Substantive answer:");
    writeFileSync(join(sandbox, "verification.json"), JSON.stringify({ arm, scenario, passed: true, ownedId, ledger, joined, launchToExitMs: parentExitAt - trace.find((row) => row.event === "process").at }, null, 2));
  } catch (error) {
    const trace = jsonLines(tracePath);
    const childSession = trace.find((row) => row.event === "reader-start")?.sessionFile;
    const ledgers = childSession ? jsonLines(childSession).filter((entry) => entry.type === "custom" && entry.customType === "lazy-harness-reader-ledger-v1") : [];
    const lifecycle = trace.filter((row) => ["parent-agent-end", "reader-start", "reader-delayed-completion", "reader-agent-end", "script-error", "network-denied"].includes(row.event));
    console.error(`Native integration failure (sandbox preserved): ${sandbox}\nSTDERR:\n${stderr}\nLIFECYCLE:\n${lifecycle.map((row) => JSON.stringify(row)).join("\n")}\nACTUAL CHILD LEDGER ENTRIES:\n${JSON.stringify(ledgers)}\nSTDOUT (tail):\n${stdout.slice(-2000)}`);
    throw error;
  } finally {
    clearTimeout(timeout);
    // The native runner is detached: aborting only the CLI would leak it on a
    // timeout. The inherited preload records every Node PID in this sandbox.
    const pids = new Set<number>(jsonLines(tracePath).filter((row) => row.event === "process").map((row) => row.pid));
    if (child?.pid) pids.add(child.pid);
    for (const pid of pids) {
      // Never signal a PID reused by an unrelated process after the CLI exits.
      const environ = `/proc/${pid}/environ`;
      if (!existsSync(environ) || !readFileSync(environ, "utf8").split("\0").includes(`NATIVE_READER_TRACE=${tracePath}`)) continue;
      for (const target of [-pid, pid]) {
        try { process.kill(target, "SIGKILL"); } catch (error) { if ((error as NodeJS.ErrnoException).code !== "ESRCH") throw error; }
      }
    }
    if (child && child.exitCode === null && child.signalCode === null) await new Promise<void>((done) => child!.once("close", () => done()));
    writeFileSync(join(sandbox, "parent-stdout.jsonl"), stdout);
    writeFileSync(join(sandbox, "parent-stderr.log"), stderr);
    console.log(`Preserved ${arm} evidence: ${sandbox}`);
  }
}, 75000);
