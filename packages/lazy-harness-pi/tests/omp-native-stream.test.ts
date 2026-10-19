import { expect, test } from "bun:test";
import { nativeFixtureStream } from "./fixtures/omp-native-stream.ts";

for (const tool of [false, true]) test(`native fixture emits a complete ${tool ? "tool" : "text"} lifecycle`, async () => {
  const block = tool ? { type: "toolCall", id: "one", name: "read", arguments: { path: "record.md" } } : { type: "text", text: "answer" };
  const message = { role: "assistant", content: [block], stopReason: tool ? "toolUse" : "stop" };
  const stream = nativeFixtureStream(message);
  const events: any[] = [];
  for await (const event of stream) events.push(event);
  const prefix = tool ? "toolcall" : "text";
  expect(events.map(e => e.type)).toEqual(["start", `${prefix}_start`, `${prefix}_delta`, `${prefix}_end`, "done"]);
  expect(events[0].partial.content).toEqual([]);
  expect(events[1].partial.content[0]).toEqual(tool ? { ...block, arguments: {} } : { ...block, text: "" });
  expect(events[2].delta).toBe(tool ? JSON.stringify(block.arguments) : block.text);
  expect(events[3].contentIndex).toBe(0);
  expect(events[4].message).toBe(message);
  expect(await stream.result()).toBe(message);
  expect(message.content).toEqual([block]);
});

test("native fixture preserves the steering release barrier for events and result", async () => {
  let release!: () => void;
  const held = new Promise<void>(resolve => { release = resolve; });
  const message = { content: [{ type: "text", text: "released" }], stopReason: "stop" };
  const stream = nativeFixtureStream(message, held);
  const iterator = stream[Symbol.asyncIterator]();
  let eventReady = false;
  let resultReady = false;
  const next = iterator.next().then(value => { eventReady = true; return value; });
  const result = stream.result().then(value => { resultReady = true; return value; });
  await Promise.resolve();
  expect(eventReady).toBe(false);
  expect(resultReady).toBe(false);
  release();
  expect((await next).value?.type).toBe("start");
  expect(await result).toBe(message);
  await iterator.return(undefined as never);
});
