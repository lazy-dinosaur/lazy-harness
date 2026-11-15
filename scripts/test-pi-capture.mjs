import { execFileSync, spawnSync } from 'node:child_process';

const supplied = process.argv.slice(2);
const captureOnly = supplied[0] === '--capture-only';
const options = captureOnly ? supplied.slice(1) : supplied;
// The aggregate passes only the shared, explicitly translated test-name filter.
for (let i = 0; i < options.length; i += 2) {
  if (options[i] !== '--test-name-pattern' || !options[i + 1]) throw new Error('Unsupported Node capture test options');
}
const supportsTransform = execFileSync(process.execPath, ['--help'], { encoding: 'utf8' }).includes('--experimental-transform-types');
const flags = supportsTransform ? ['--experimental-transform-types'] : [];
const capture = spawnSync(process.execPath, [...flags, '--test', ...options, 'tests/lazy-harness/pi-capture-evidence.test.ts'], { stdio: 'inherit', env: process.env });
if (capture.status !== 0) process.exit(capture.status ?? 1);
if (!captureOnly) {
  const monitoring = spawnSync('bun', ['run', 'test:monitoring-attach'], { stdio: 'inherit', env: process.env });
  if (monitoring.status !== 0) process.exit(monitoring.status ?? 1);
}
