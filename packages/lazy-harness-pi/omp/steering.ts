import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";

/** Consume structured native steering; OMP 18 may prepare a new turn first. */
export function onOmpNativeSteer(api: ExtensionAPI, listener: (text: string, ctx: ExtensionContext, preparedTurn?: boolean) => Promise<void>): void {
  let preparedSession: string | undefined;
  api.on("before_agent_start", (_event, ctx) => { preparedSession = ctx.sessionManager.getSessionId(); });
  api.on("message_start", async (event: any, ctx) => {
    const message = event.message;
    if (message?.role !== "user") return;
    const preparedTurn = preparedSession !== undefined && preparedSession === ctx.sessionManager.getSessionId();
    preparedSession = undefined;
    if (message.steering !== true || message.attribution === "agent") return;
    const text = typeof message.content === "string" ? message.content
      : Array.isArray(message.content) ? message.content.filter((part: any) => part?.type === "text" && typeof part.text === "string").map((part: any) => part.text).join("\n") : "";
    if (text.trim()) await listener(text, ctx, preparedTurn);
  });
}
