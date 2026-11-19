import type { ExtensionAPI } from '@earendil-works/pi-coding-agent';
import { createAssistantMessageEventStream } from '@earendil-works/pi-ai';

export default function projectMoveFixture(pi: ExtensionAPI) {
  if (process.env.MOVE_FIXTURE_CANCEL === '1') pi.on('session_before_switch', () => ({ cancel: true }));
  pi.registerProvider('offline-project-move', {
    api: 'offline-project-move-api', apiKey: 'offline-placeholder', baseUrl: 'http://invalid.invalid',
    models: [{ id: 'scripted', name: 'Project move fixture', reasoning: false, input: ['text'], cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 }, contextWindow: 65536, maxTokens: 500 }],
    streamSimple(model, context) {
      const stream = createAssistantMessageEventStream();
      const request = context.messages.findLast(message => message.role === 'user' && /move through the tool|inspect workspace/.test(JSON.stringify(message.content)));
      const completed = context.messages.some(message => message.role === 'toolResult' && message.toolCallId === 'project-move-tool');
      const move = !completed && request?.role === 'user' && JSON.stringify(request.content).includes('move through the tool');
      const hasHistory = JSON.stringify(context.messages).includes('original conversation marker');
      const systems = context.messages.filter(message => message.role === 'system');
      const rules = JSON.stringify(systems.at(-1)) || context.systemPrompt || '';
      const target = rules.includes('TARGET_RULE_MARKER') && !rules.includes('SOURCE_RULE_MARKER');
      const stopReason = move ? 'toolUse' : 'stop';
      const message = {
        role: 'assistant' as const,
        content: move
          ? [{ type: 'toolCall' as const, id: 'project-move-tool', name: 'lazy_move_project', arguments: { targetPath: process.env.MOVE_FIXTURE_TARGET, prompt: 'inspect workspace' } }]
          : [{ type: 'text' as const, text: `MOVE_PROOF history=${hasHistory} targetRules=${target}` }],
        api: model.api, provider: model.provider, model: model.id, stopReason: stopReason as 'toolUse' | 'stop', timestamp: Date.now(),
        usage: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, totalTokens: 0, cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, total: 0 } },
      };
      stream.push({ type: 'done', reason: stopReason, message });
      stream.end();
      return stream;
    },
  });
}
