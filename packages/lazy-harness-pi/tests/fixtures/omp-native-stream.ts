// Scripted native fixtures must emit the same lifecycle as a streaming provider.
// A terminal-only stream does not establish a turn in newer OMP agent loops.
export function nativeFixtureStream(message: any, released: Promise<void> = Promise.resolve()) {
  return {
    async *[Symbol.asyncIterator]() {
      await released;
      yield { type: "start", partial: { ...message, content: [] } };
      for (let contentIndex = 0; contentIndex < message.content.length; contentIndex++) {
        const block = message.content[contentIndex];
        const prefix = message.content.slice(0, contentIndex);
        if (block.type === "toolCall") {
          yield { type: "toolcall_start", contentIndex, partial: { ...message, content: [...prefix, { ...block, arguments: {} }] } };
          yield { type: "toolcall_delta", contentIndex, delta: JSON.stringify(block.arguments), partial: message };
          yield { type: "toolcall_end", contentIndex, toolCall: block, partial: message };
        } else if (block.type === "text") {
          yield { type: "text_start", contentIndex, partial: { ...message, content: [...prefix, { ...block, text: "" }] } };
          yield { type: "text_delta", contentIndex, delta: block.text, partial: message };
          yield { type: "text_end", contentIndex, content: block.text, partial: message };
        } else {
          throw new Error(`Unsupported native fixture block: ${block.type}`);
        }
      }
      yield { type: "done", reason: message.stopReason, message };
    },
    result: async () => { await released; return message; },
  };
}
