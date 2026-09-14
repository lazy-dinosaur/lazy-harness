// Loaded by NODE_OPTIONS in both the real CLI and its detached native runner.
import { appendFileSync } from "node:fs";
import net from "node:net";
import { syncBuiltinESMExports } from "node:module";
const trace = process.env.NATIVE_READER_TRACE;
appendFileSync(trace, JSON.stringify({ event: "process", pid: process.pid, at: Date.now() }) + "\n");
function denied(kind) {
  appendFileSync(trace, JSON.stringify({ event: "network-denied", kind, pid: process.pid }) + "\n");
  throw new Error(`Offline native Reader test forbids ${kind}`);
}
globalThis.fetch = async () => denied("fetch");
const connect = net.Socket.prototype.connect;
net.Socket.prototype.connect = function (...args) {
  // Native local control channels may use Unix sockets, never TCP.
  const options = Array.isArray(args[0]) ? args[0][0] : args[0];
  if ((typeof options === "object" && typeof options?.path === "string") ||
      (typeof options === "string" && !/^\d+$/.test(options))) return connect.apply(this, args);
  return denied("TCP connect");
};
syncBuiltinESMExports();
