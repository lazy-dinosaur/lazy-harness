import { test } from 'bun:test';
import { runFabricScenario } from './fixtures/fabric-cli-runner.ts';

test('actual Fabric untrusted child cannot supply the declared guard/ledger or join', async () => {
  await runFabricScenario({ order: 'source-first', mode: 'json', advisory: 'capture', trusted: false });
}, 115000);
