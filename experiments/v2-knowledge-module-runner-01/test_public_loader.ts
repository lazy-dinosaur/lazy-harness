// Synthetic loader seam, NOT Pi/SDK integration or extension attachment.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath, pathToFileURL } from "node:url";
import { join } from "node:path";

const root = process.argv[2];
assert(root);
const extension = join(root, "pi-extension/knowledge.ts");
const source = readFileSync(extension, "utf8");
const calls: { file: string; args: string[]; options: unknown; input?: string }[] = [];
const tools = new Map<string, any>();
const hooks = new Map<string, any>();
const execFile = (file: string, args: string[], options: unknown, callback: any) => {
  const call = { file, args, options, input: undefined as string | undefined };
  calls.push(call);
  queueMicrotask(() => callback(null, '{"items":[],"ok":true}'));
  return { stdin: { end: (input: string) => { call.input = input; } } };
};
// Schema builder is a passive fixture, not an SDK provider or authentication shim.
const Type = new Proxy({}, { get: () => (...args: unknown[]) => ({ args }) });
const js = new Bun.Transpiler({ loader: "ts", target: "bun" }).transformSync(source);
const body = js
  .replace(/^import .*;?\n/gm, "")
  .replace(/import\.meta\.url/g, JSON.stringify(pathToFileURL(extension).href))
  .replace(/export default function/, "return function");
const attach = new Function("execFile", "fileURLToPath", "Type", body)(execFile, fileURLToPath, Type);
assert.equal(calls.length, 0, "module import must not invoke Python");
attach({ on: (name: string, fn: any) => hooks.set(name, fn),
  registerTool: (tool: any) => tools.set(tool.name, tool),
  sendMessage: () => { throw new Error("unexpected notification"); }, appendEntry: () => {} });
assert.equal(calls.length, 0, "registration alone must remain inactive");
assert(tools.has("knowledge_review"));
assert(hooks.has("session_start"));
const cwd = join(root, "unrelated-caller-root");
await tools.get("knowledge_review").execute("fixture", { action: "list", host_id: "fixture-host" }, undefined, undefined, { cwd });
assert.equal(calls.length, 1);
assert.equal(calls[0].file, "/usr/bin/python3");
assert.deepEqual(calls[0].args, [join(root, "knowledge_cli.py"), "review"]);
assert.equal((calls[0].options as any).cwd, cwd);
assert.equal(JSON.parse(calls[0].input!).host_id, "fixture-host");
assert.equal(JSON.parse(calls[0].input!).action, "list");
console.log("PASS public loader: 1 synthetic callback; no SDK, Python, network or lifecycle execution");
