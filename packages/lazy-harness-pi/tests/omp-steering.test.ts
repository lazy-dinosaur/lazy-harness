import { expect, test } from "bun:test";
import { onOmpNativeSteer } from "../omp/steering.ts";

test("native steer bridge uses runtime metadata, not words or normal messages", async () => {
  let handler: any;
  const calls: string[] = [];
  onOmpNativeSteer({ on: (name: string, fn: any) => { expect(["before_agent_start", "message_start"]).toContain(name); if (name === "message_start") handler = fn; } } as any, async text => { calls.push(text); });
  for (const message of [
    { role: "user", content: "stop, steer, new objective" },
    { role: "user", steering: "true", content: "text" },
    { role: "assistant", steering: true, content: "text" },
    { role: "user", steering: true, attribution: "agent", content: "text" },
    { role: "user", steering: true, content: "   " },
  ]) await handler({ message }, {});
  expect(calls).toEqual([]);
  await handler({ message: { role: "user", steering: true, attribution: "user", content: [{ type: "text", text: "new objective" }] } }, {});
  expect(calls).toEqual(["new objective"]);
});

test("prepared native boundaries are consumed once and bound to their session", async () => {
  const handlers = new Map<string, any>();
  const prepared: boolean[] = [];
  onOmpNativeSteer({ on: (name: string, fn: any) => handlers.set(name, fn) } as any, async (_text, _ctx, value) => { prepared.push(value === true); });
  const ctx = (id: string) => ({ sessionManager: { getSessionId: () => id } });
  const steer = { message: { role: "user", steering: true, content: "new objective" } };
  await handlers.get("before_agent_start")({}, ctx("one"));
  await handlers.get("message_start")(steer, ctx("one"));
  await handlers.get("message_start")(steer, ctx("one"));
  expect(prepared).toEqual([true, false]);
  await handlers.get("before_agent_start")({}, ctx("one"));
  await handlers.get("message_start")({ message: { role: "user", content: "normal follow-up" } }, ctx("one"));
  await handlers.get("message_start")(steer, ctx("one"));
  await handlers.get("before_agent_start")({}, ctx("one"));
  await handlers.get("message_start")(steer, ctx("two"));
  expect(prepared).toEqual([true, false, false, false]);
});
