import { expect, test } from "bun:test";
import { execFileSync } from "node:child_process";
import { cpSync, mkdirSync, mkdtempSync, rmSync, symlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";

test("OMP entry registers offline without a Pi runtime dependency", () => {
  const sandbox = mkdtempSync(join(tmpdir(), "omp-only-loader-"));
  try {
    const source = resolve(import.meta.dir, "..");
    cpSync(join(source, "extensions"), join(sandbox, "extensions"), { recursive: true });
    cpSync(join(source, "omp"), join(sandbox, "omp"), { recursive: true });
    mkdirSync(join(sandbox, "node_modules"));
    // Supply only the runtime's schema dependency, never the Pi SDK or credentials.
    const typebox = dirname(Bun.resolveSync("typebox/package.json", source));
    symlinkSync(typebox, join(sandbox, "node_modules/typebox"), "dir");
    writeFileSync(join(sandbox, "package.json"), '{"type":"module"}');
    const probe = `
      globalThis.fetch = () => { throw new Error("network forbidden"); };
      const {default: extension} = await import("./omp/index.ts");
      const tools = [], commands = [], events = [];
      extension({on(name) {events.push(name)}, events:{on() {return () => {}}},
        registerTool(tool) {tools.push(tool.name)}, registerCommand(name) {commands.push(name)}});
      console.log(JSON.stringify({tools, commands, events}));
    `;
    const result = JSON.parse(execFileSync(process.execPath, ["-e", probe], {
      cwd: sandbox, encoding: "utf8", timeout: 15000,
      env: { PATH: process.env.PATH ?? "", HOME: sandbox, PI_CODING_AGENT_DIR: join(sandbox, "agent") },
    }));
    expect(result.tools).toContain("lazy_reader_join");
    expect(result.commands).toContain("lazy-move");
    expect(result.events).toContain("session_switch");
    expect(result.events).toContain("message_start");
  } finally { rmSync(sandbox, { recursive: true, force: true }); }
});
