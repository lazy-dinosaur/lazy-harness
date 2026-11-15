import { test } from 'bun:test';
import { runFabricScenario } from './fixtures/fabric-cli-runner.ts';

// Current Pi transport: real Fabric processes, not old native A/B packages.
for (const order of ['wait-first', 'source-first'] as const) {
  for (const mode of ['json', 'text'] as const) {
    for (const advisory of ['capture', 'placement'] as const) {
      test(`Fabric ${order} ${mode} ${advisory}: full ledger join and primary answer`, async () => {
        await runFabricScenario({ order, mode, advisory, trusted: true });
      }, 115000);
    }
  }
}
