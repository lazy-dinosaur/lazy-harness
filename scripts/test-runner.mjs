import { readdirSync, realpathSync, statSync } from 'node:fs';
import { join, relative, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { spawnSync } from 'node:child_process';
import { tmpdir } from 'node:os';

const nodeOnly = 'tests/lazy-harness/pi-capture-evidence.test.ts';
function collect(directory, output) {
  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    if (['node_modules', '.git', 'vendor'].includes(entry.name)) continue;
    const path = join(directory, entry.name);
    if (entry.isDirectory()) collect(path, output);
    else if (entry.isFile() && entry.name.endsWith('.test.ts')) output.push(path);
  }
}

export function planTestRuns(argv, cwd = process.cwd()) {
  const args = argv[0] === '--' ? argv.slice(1) : argv;
  const targets = [], bunOptions = [], nodeOptions = [], bunOnlyOptions = [];
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    const pattern = arg.startsWith('--test-name-pattern=') ? arg.slice('--test-name-pattern='.length) : undefined;
    if (arg === '-t' || arg === '--test-name-pattern' || pattern !== undefined) {
      const value = pattern ?? args[++i];
      if (!value) throw new Error('A test-name pattern value is required');
      bunOptions.push('-t', value); nodeOptions.push('--test-name-pattern', value);
    } else if (arg === '--timeout' || arg.startsWith('--timeout=')) {
      const value = arg === '--timeout' ? args[++i] : arg.slice('--timeout='.length);
      if (!value) throw new Error('A timeout value is required');
      bunOnlyOptions.push('--timeout', value);
    } else if (arg.startsWith('-')) {
      throw new Error(`Unsupported aggregate option: ${arg}; use an explicit engine command instead`);
    } else targets.push(arg);
  }
  const paths = [];
  if (!targets.length) {
    collect(join(cwd, 'tests/lazy-harness'), paths);
    collect(join(cwd, 'packages/lazy-harness-pi/tests'), paths);
  } else for (const target of targets) {
    const path = resolve(cwd, target.replaceAll('\\', '/'));
    const key = relative(cwd, path).replaceAll('\\', '/');
    if (key === '..' || key.startsWith('../')) throw new Error('Test targets must remain inside the repository');
    if (statSync(path).isDirectory()) collect(path, paths);
    else paths.push(path);
  }
  const normalized = [...new Set(paths.map(path => relative(cwd, path).replaceAll('\\', '/')))].sort();
  const needsNode = normalized.includes(nodeOnly);
  if (needsNode && bunOnlyOptions.length) throw new Error('Bun-only options are unsupported for the Node lane; invoke each engine explicitly');
  const bunTargets = normalized.filter(path => path !== nodeOnly);
  if (!normalized.length) throw new Error('No owned test files found');
  return {
    bun: bunTargets.length ? ['test', ...bunOptions, ...bunOnlyOptions, ...bunTargets] : undefined,
    node: needsNode ? ['scripts/test-pi-capture.mjs', '--capture-only', ...nodeOptions] : undefined,
  };
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  try {
    const plan = planTestRuns(process.argv.slice(2));
    const env = { ...process.env, TMPDIR: realpathSync(tmpdir()) };
    for (const [command, args] of [['bun', plan.bun], [process.execPath, plan.node]]) {
      if (!args) continue;
      const result = spawnSync(command, args, { stdio: 'inherit', env });
      if (result.status !== 0) process.exit(result.status ?? 1);
    }
    console.log('1 passed');
  } catch (error) { console.error(error instanceof Error ? error.message : String(error)); process.exit(1); }
}
