import { afterEach, test, expect } from 'bun:test'
import { cpSync, existsSync, lstatSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, realpathSync, rmSync, symlinkSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { dirname, join, resolve } from 'node:path'
import { spawnSync } from 'node:child_process'
import { manageMonitoring, detectReadFormat, handleMonitoringControl, CONFIG_PATH, DEFAULT_DOCUMENTS } from '../extensions/lazy-harness/monitoring/manage.ts'
import { readMonitoringAttachConfig } from '../extensions/lazy-harness/monitoring/config.ts'
import { admitCatalog } from '../extensions/lazy-harness/monitoring/catalog.ts'
import { installOptionalMonitoring } from '../extensions/lazy-harness/monitoring/load.ts'
import { installMonitoringPhase1 } from '../extensions/lazy-harness/monitoring/index.ts'

const source = resolve(import.meta.dir, '../../..'), roots: string[] = []
const env = { ...process.env }; delete env.PI_FABRIC_LINEAGE; delete env.LAZY_HOST_ROOT
function fixture(defaults = true) {
  const root = mkdtempSync(join(tmpdir(), 'lh-enable-')); roots.push(root)
  const put = (path: string, text: string) => { mkdirSync(dirname(join(root, path)), { recursive: true }); writeFileSync(join(root, path), text) }
  if (defaults) for (const d of DEFAULT_DOCUMENTS) put(d.path, '# Offline fixture\n')
  const settingsFile = join(root, 'settings.json'); put('settings.json', '{"packages":[]}')
  const messages: string[] = [], run = (...args: string[]) => manageMonitoring(root, args, { settingsFile, print: text => messages.push(text) })
  return { root, put, run, settingsFile, messages, file: join(root, CONFIG_PATH) }
}
afterEach(() => { for (const root of roots.splice(0)) rmSync(root, { recursive: true, force: true }) })

test('defaults write only config and are accepted by the real parser and catalog', () => {
  const f = fixture(); f.run('enable')
  const config = readMonitoringAttachConfig(f.root)
  expect(config.references.stage).toBe('observe'); expect(config.catalog).toEqual(DEFAULT_DOCUMENTS)
  expect(config.budget).toMatchObject({ maxCalls: 100, maxConcurrent: 1, maxQueued: 2, maxReservedTokens: 1000000, maxReservedUsd: 0.05 })
  expect(config.readFormat).toBe('pi-read-text-v1'); expect(admitCatalog(f.root, config).documents).toHaveLength(2)
  expect(lstatSync(f.file).mode & 0o777).toBe(0o644)
  expect(readdirSync(join(f.root, '.lazy-harness')).sort()).toEqual(['decisions', 'monitoring-attach.json', 'ssot'])
  expect(f.messages.join('\n')).toContain('/login openrouter'); expect(f.messages.join('\n')).toContain('/reload')
})
test('real host default records fit admission without modifying or activating this checkout', () => {
  const f = fixture(false)
  for (const d of DEFAULT_DOCUMENTS) f.put(d.path, readFileSync(join(source, d.path), 'utf8'))
  f.run('enable'); expect(admitCatalog(f.root, readMonitoringAttachConfig(f.root)).documents).toHaveLength(2)
})
test('missing default records skip with messages; no-default-docs and custom doc derive ids', () => {
  const f = fixture(false); f.run('enable')
  expect(f.messages.filter(s => s.startsWith('Skipped missing'))).toHaveLength(2)
  expect(readMonitoringAttachConfig(f.root).catalog).toEqual([])
  f.put('.lazy-harness/spec/demo.xml', '<record/>')
  f.run('enable', '--force', '--no-default-docs', '--doc', '.lazy-harness/spec/demo.xml', '--calls', '3', '--usd', '0.01', '--read-format', 'unknown')
  expect(readMonitoringAttachConfig(f.root)).toMatchObject({ catalog: [{ id: 'spec:demo', path: '.lazy-harness/spec/demo.xml' }], readFormat: 'unknown', budget: { maxCalls: 3, maxReservedUsd: 0.01 } })
})
test('overwrite refusal prints diff; force succeeds; dry-run never changes files', () => {
  const f = fixture(); f.run('enable', '--dry-run'); expect(existsSync(f.file)).toBe(false)
  f.run('enable'); const before = readFileSync(f.file, 'utf8')
  expect(() => f.run('enable', '--calls', '4')).toThrow('refusing overwrite')
  expect(f.messages.at(-1)).toContain('--- ' + CONFIG_PATH); expect(f.messages.at(-1)).toContain('+    "maxCalls": 4')
  expect(readFileSync(f.file, 'utf8')).toBe(before)
  f.run('enable', '--force', '--calls', '4', '--dry-run'); expect(readFileSync(f.file, 'utf8')).toBe(before)
  f.run('enable', '--force', '--calls', '4'); expect(readMonitoringAttachConfig(f.root).budget.maxCalls).toBe(4)
})
test('disable shows config, removes only config, preserves logs/records, is idempotent and supports dry-run', () => {
  const f = fixture(); f.run('enable'); f.put('.lazy-harness/keep.txt', 'keep')
  f.run('disable', '--dry-run'); expect(existsSync(f.file)).toBe(true)
  f.run('disable'); expect(existsSync(f.file)).toBe(false)
  expect(f.messages.join('\n')).toContain('"stage": "observe"')
  expect(readFileSync(join(f.root, '.lazy-harness/keep.txt'), 'utf8')).toBe('keep')
  expect(existsSync(join(f.root, DEFAULT_DOCUMENTS[0].path))).toBe(true)
  f.run('disable'); expect(f.messages.join('\n')).toContain('already disabled')
})
for (const path of ['/tmp/out.md', '../out.md', '.lazy-harness/ssot/../../out.md', '.lazy-harness/logs/out.md', '.lazy-harness/ssot/out.txt']) test('refuse path ' + path, () => {
  const f = fixture(); expect(() => f.run('enable', '--doc', path)).toThrow(); expect(existsSync(f.file)).toBe(false)
})
test('refuse oversized per-doc/aggregate catalogs, symlink files/directories, invalid UTF-8 and too many docs', () => {
  const f = fixture(false), a = '.lazy-harness/ssot/a.md', b = '.lazy-harness/spec/b.md'
  f.put(a, 'x'.repeat(8193)); expect(() => f.run('enable', '--doc', a)).toThrow('8192')
  f.put(a, 'x'.repeat(7000)); f.put(b, 'x'.repeat(7000)); expect(() => f.run('enable', '--doc', a, '--doc', b)).toThrow('material budget')
  f.put(b, 'small'); rmSync(join(f.root, a)); symlinkSync(join(f.root, b), join(f.root, a))
  expect(() => f.run('enable', '--doc', a)).toThrow('unavailable')
  rmSync(join(f.root, a)); rmSync(join(f.root, '.lazy-harness/ssot'), { recursive: true }); symlinkSync(join(f.root, '.lazy-harness/spec'), join(f.root, '.lazy-harness/ssot'))
  expect(() => f.run('enable', '--doc', '.lazy-harness/ssot/b.md')).toThrow('unavailable')
  writeFileSync(join(f.root, b), Buffer.from([0xff])); expect(() => f.run('enable', '--doc', b)).toThrow('unavailable')
  rmSync(join(f.root, '.lazy-harness/ssot')); const docs: string[] = []
  for (let i = 0; i < 17; i++) { const p = `.lazy-harness/ssot/d${i}.md`; f.put(p, 'small'); docs.push('--doc', p) }
  expect(() => f.run('enable', ...docs)).toThrow('bounded catalog'); expect(existsSync(f.file)).toBe(false)
})
test('unsafe config symlinks refuse enable/force/disable and leave targets untouched', () => {
  const f = fixture(); f.put('target', '{}'); symlinkSync(join(f.root, 'target'), f.file)
  for (const args of [['enable'], ['enable', '--force'], ['disable']]) expect(() => f.run(...args)).toThrow('Unsafe')
  expect(readFileSync(join(f.root, 'target'), 'utf8')).toBe('{}')
  rmSync(f.file); rmSync(join(f.root, '.lazy-harness'), { recursive: true }); mkdirSync(join(f.root, 'other')); symlinkSync(join(f.root, 'other'), join(f.root, '.lazy-harness'))
  expect(() => f.run('enable')).toThrow('Unsafe'); expect(readdirSync(join(f.root, 'other'))).toEqual([])
})
test('read format detection: npm versioned, object/local package, absent, malformed and lookalike settings', () => {
  const f = fixture(false)
  for (const entry of ['npm:pi-hashline-edit-pro', 'npm:pi-hashline-edit-pro@1.2.3', { source: '/tmp/pi-hashline-edit-pro', extensions: [] }]) {
    f.put('settings.json', JSON.stringify({ packages: [entry] })); expect(detectReadFormat(f.settingsFile)).toBe('pi-hashline-edit-pro-v1')
  }
  f.run('enable'); expect(readMonitoringAttachConfig(f.root).readFormat).toBe('pi-hashline-edit-pro-v1')
  for (const content of ['{}', '{', '{"packages":["npm:not-pi-hashline-edit-pro","npm:pi-hashline-edit-pro-extra"]}']) {
    f.put('settings.json', content); expect(detectReadFormat(f.settingsFile)).toBe('pi-read-text-v1')
  }
  expect(detectReadFormat(join(f.root, 'missing'))).toBe('pi-read-text-v1')
})
test('config prints effective off/parsed defaults and validation failures without writing', () => {
  const f = fixture(), previous = process.env.XDG_CONFIG_HOME
  process.env.XDG_CONFIG_HOME = join(realpathSync(f.root), 'xdg-config')
  try {
    f.run('config'); expect(f.messages.join('\n')).toContain('absent; effective off'); expect(existsSync(f.file)).toBe(false)
    f.run('enable'); f.run('config'); expect(f.messages.at(-1)).toBe('Validation: OK')
    f.put(CONFIG_PATH, '{'); expect(() => f.run('config')).toThrow('validation failed')
    f.put(CONFIG_PATH, '{"references":{"stage":"observe"},"catalog":[{"id":"ssot:missing","path":".lazy-harness/ssot/missing.md"}]}')
    expect(() => f.run('config')).toThrow('validation failed')
  } finally {
    if (previous === undefined) delete process.env.XDG_CONFIG_HOME
    else process.env.XDG_CONFIG_HOME = previous
  }
})
for (const args of [['enable', '--calls', '-1'], ['enable', '--calls', '1.5'], ['enable', '--calls', '9007199254740992'], ['enable', '--usd', 'NaN'], ['enable', '--usd', '-1'], ['enable', '--read-format', 'bad'], ['enable', '--doc'], ['enable', '--oops'], ['disable', '--force'], ['config', '--dry-run']]) test('invalid args ' + args.join(' '), () => {
  const f = fixture(); expect(() => f.run(...args)).toThrow(); expect(existsSync(f.file)).toBe(false)
})
test('Pi controls delegate to shared implementation; no reload/session/model APIs', async () => {
  const f = fixture(), calls: unknown[] = [], messages: string[] = [], ui = { notify: (s: string) => messages.push(s) }
  expect(handleMonitoringControl('enable', f.root, ui, (root, args, deps) => { calls.push([root, args]); manageMonitoring(root, args, { ...deps, settingsFile: f.settingsFile }) })).toBe(true)
  expect(calls).toEqual([[f.root, ['enable']]]); expect(existsSync(f.file)).toBe(true)
  handleMonitoringControl('disable', f.root, ui); expect(existsSync(f.file)).toBe(false)
  expect(handleMonitoringControl('status --save', f.root, ui)).toBe(false)
  expect(messages.join('\n')).toContain('/reload')
  let loads = 0, handler: any
  const pi: any = { registerCommand(_name: string, spec: any) { handler = spec.handler }, on() { throw Error('off must not register hooks') } }
  installOptionalMonitoring(pi, f.root, async () => { loads++; throw Error('no module calls') })
  const ctx: any = { ui, reload() { throw Error('must not reload') }, modelRegistry: new Proxy({}, { get() { throw Error('no models') } }) }
  await handler('enable', ctx); expect(existsSync(f.file)).toBe(true); expect(loads).toBe(0)
  await handler('disable', ctx); expect(existsSync(f.file)).toBe(false)
  f.run('enable'); installMonitoringPhase1({ registerCommand(_n: string, spec: any) { handler = spec.handler }, on() {} } as any, f.root)
  await handler('disable', ctx); expect(existsSync(f.file)).toBe(false)
})
test('CLI dispatcher targets temp host and synced-host helper uses recorded source without cwd changes', () => {
  const f = fixture()
  const invoke = (...args: string[]) => spawnSync('bash', [join(source, '.lazy-harness/bin/lazy'), 'monitoring', ...args], { cwd: f.root, env: { ...env, LAZY_HOST_ROOT: f.root, PI_CODING_AGENT_DIR: f.root }, encoding: 'utf8' })
  expect(invoke('enable', '--dry-run').status).toBe(0); expect(existsSync(f.file)).toBe(false)
  expect(invoke('enable').status).toBe(0); expect(readMonitoringAttachConfig(f.root).references.stage).toBe('observe')
  expect(invoke('enable').status).toBe(1); expect(invoke('config').stdout).toContain('Validation: OK')
  expect(invoke('disable').status).toBe(0); expect(existsSync(f.file)).toBe(false)
  f.put('.lazy-harness/state/synced-from-commit', JSON.stringify({ sourceRoot: source }))
  mkdirSync(join(f.root, '.lazy-harness/scripts'), { recursive: true }); cpSync(join(source, '.lazy-harness/scripts/monitoring.ts'), join(f.root, '.lazy-harness/scripts/monitoring.ts'))
  const synced = spawnSync('bun', [join(f.root, '.lazy-harness/scripts/monitoring.ts'), 'enable'], { cwd: f.root, env, encoding: 'utf8' })
  expect(synced.status).toBe(0); expect(readMonitoringAttachConfig(f.root).references.stage).toBe('observe')
})
