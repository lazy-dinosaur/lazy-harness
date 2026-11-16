import type { ExtensionAPI } from '@earendil-works/pi-coding-agent';
import { createAssistantMessageEventStream, getCurrentSystemPrompt, type AssistantMessage } from '@earendil-works/pi-ai';
import { appendFileSync } from 'node:fs';

const object = (value: unknown): Record<string, unknown> => value !== null && typeof value === 'object' ? value as Record<string, unknown> : {};
export default function (pi: ExtensionAPI) {
  const root = process.env.FABRIC_READER_TEST_ROOT ?? '';
  const trace = process.env.FABRIC_READER_TEST_TRACE ?? '';
  const revision = process.env.FABRIC_READER_TEST_REVISION ?? '';
  const log = (event: string, data: Record<string, unknown> = {}) => appendFileSync(trace, JSON.stringify({ event, at: Date.now(), pid: process.pid, ...data }) + '\n');
  let request: Record<string, unknown> | undefined;
  let handle: string | undefined;
  let joined = false;
  let calls = 0;
  let reader = false;
  pi.on('before_agent_start', (event, ctx) => {
    reader = event.systemPrompt.includes('LAZY_HARNESS_ROLE: record-reader/reader-join-v1');
    log(reader ? 'reader-start' : 'parent-start', { sessionFile: ctx.sessionManager.getSessionFile(), sessionId: ctx.sessionManager.getSessionId(), lineage: process.env.PI_FABRIC_LINEAGE });
  });
  pi.on('agent_end', (event, ctx) => log(reader ? 'reader-end' : 'parent-end', { messages: event.messages, sessionFile: ctx.sessionManager.getSessionFile() }));
  pi.on('tool_result', (event) => {
    log(reader ? 'reader-tool' : 'parent-tool', { result: event });
    const details = object(event.details);
    if (event.toolName === 'lazy_reader_request') request = object(details.request);
    if (event.toolName === 'agents.spawn') { const result = object(details.result); if (typeof result.id === 'string') handle = result.id; }
    if (event.toolName === 'lazy_reader_join') joined = details.joined === true;
  });
  pi.registerProvider('offline-fabric-reader', {
    api: 'offline-fabric-reader-api', apiKey: 'offline-placeholder', baseUrl: 'http://invalid.invalid',
    models: [{ id: 'scripted', name: 'Offline Fabric fixture', reasoning: true, input: ['text'], cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 }, contextWindow: 100000, maxTokens: 2000 }],
    streamSimple(model, context) {
      const stream = createAssistantMessageEventStream();
      void (async () => {
        const system = typeof getCurrentSystemPrompt === 'function' ? getCurrentSystemPrompt(context.messages) : String(Reflect.get(context, 'systemPrompt') ?? '');
        const isReader = system.includes('LAZY_HARNESS_ROLE: record-reader/reader-join-v1');
        const turn = calls++;
        log(isReader ? 'reader-model' : 'parent-model', { turn });
        const tool = (name: string, args: Extract<AssistantMessage['content'][number], { type: 'toolCall' }>['arguments']): AssistantMessage['content'] => [{ type: 'toolCall', id: `${isReader ? 'reader' : 'parent'}-${turn}`, name, arguments: args }];
        let content: AssistantMessage['content'];
        if (isReader) {
          const commands = ['.lazy-harness/bin/lazy map --overview --complete --format=md', 'pwd', 'git rev-parse --show-toplevel', 'git rev-parse HEAD', '.lazy-harness/bin/lazy map fixture-fact --format=md --limit=8'];
          if (turn < commands.length) content = tool('fabric_exec', { code: `return await pi.bash({cmd:${JSON.stringify(commands[turn])}})` });
          else if (turn < 7) content = tool('fabric_exec', { code: `return await pi.read({path:${JSON.stringify('.lazy-harness/spec/' + (turn === 5 ? 'fact.md' : 'second.md'))},limit:200})` });
          else if (turn === 7) {
            await new Promise(resolve => setTimeout(resolve, 300));
            content = [{ type: 'text', text: `LAZY_HARNESS_READER_RESULT: complete\nroot: ${root}\nrevision: ${revision}\nevidenceEpoch: 1\nfacts: canonical fact: delivery matters\nrecordsRead: .lazy-harness/spec/fact.md\nconflicts: none\nmissing: none\nparentFollowUp: join before answering` }];
          } else throw new Error('Unexpected Reader continuation');
        } else if (turn === 0) content = tool('lazy_reader_request', { task: `root: ${root}\nrevision: ${revision}\nmodel: offline-fabric-reader/scripted:low\nevidenceEpoch: 1\nmaxReadCalls: 6\nmaxRequestedLines: 1200\nmaxLinesPerRead: 200\ntask: inspect canonical delivery records` });
        else if (turn === 1) {
          if (!request) throw new Error('No runtime-prepared request');
          content = tool('fabric_exec', { code: `return await agents.spawn(${JSON.stringify(request)})`, resultFormat: 'json' });
        } else if (turn === 2 || turn === 3) {
          const wait = (turn === 2) === (process.env.FABRIC_READER_TEST_ORDER === 'wait-first');
          if (wait) {
            if (!handle) throw new Error('No actual Fabric spawn proxy observed');
            content = tool('fabric_exec', { code: `return await agents.wait({id:${JSON.stringify(handle)}})`, resultFormat: 'json' });
          } else content = tool('read', { path: 'source.txt', limit: 10 });
        } else if (turn === 4) {
          if (!JSON.stringify(context.messages).includes('facts: canonical fact: delivery matters')) throw new Error('Reader content not delivered to Parent');
          content = tool('lazy_reader_join', { status: 'complete', resultMarker: 'LAZY_HARNESS_READER_RESULT: complete', revision, evidenceEpoch: 1, recordPaths: ['.lazy-harness/spec/fact.md'] });
        } else if (turn === 5) {
          if (process.env.FABRIC_READER_TEST_TRUST === 'false') {
            if (joined) throw new Error('Untrusted child unexpectedly joined');
            content = [{ type: 'text', text: 'Rejected unsafe Reader join; bounded Parent fallback is required.' }];
          } else {
            if (!joined) throw new Error('Cannot answer without actual full-ledger join');
            const contextText = process.env.FABRIC_READER_TEST_ADVISORY === 'placement' ? 'The project-specific ownership rule must be stored in .lazy-harness.' : 'Analysis across SDD, BDD and TDD.';
            content = [{ type: 'text', text: `Substantive answer: delivery matters. ${contextText}\nCLAIM-1: runtime owns root identity.\nCLAIM-2: Reader content reaches Parent before join.\nCLAIM-3: all successful ledger hashes remain protected.\nCLAIM-4: absent archival guarantee is not invented.` }];
          }
        } else { log('unwanted-continuation'); content = [{ type: 'text', text: 'Partial replacement' }]; }
        const stopReason = content.some(part => part.type === 'toolCall') ? 'toolUse' : 'stop';
        const message: AssistantMessage = { role: 'assistant', content, api: model.api, provider: model.provider, model: model.id, usage: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, totalTokens: 0, cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, total: 0 } }, stopReason, timestamp: Date.now() };
        stream.push({ type: 'start', partial: message }); stream.push({ type: 'done', reason: stopReason, message }); stream.end();
      })().catch(error => {
        log('script-error', { error: String(error) });
        const failed: AssistantMessage = { role: 'assistant', content: [], api: model.api, provider: model.provider, model: model.id, usage: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, totalTokens: 0, cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, total: 0 } }, stopReason: 'error', errorMessage: String(error), timestamp: Date.now() };
        stream.push({ type: 'error', reason: 'error', error: failed });
        stream.end();
      });
      return stream;
    },
  });
}
