import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

// Isolated test dependency graph only: never upgrade the production SDK or global Pi.
const cwd = fileURLToPath(new URL('../tests/runtime/fabric/', import.meta.url));
const result = spawnSync('bun', ['--no-env-file', 'install', '--frozen-lockfile', '--ignore-scripts'], { cwd, stdio: 'inherit' });
process.exit(result.status ?? 1);
