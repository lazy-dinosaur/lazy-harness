import { afterEach, beforeEach, expect, test } from 'bun:test'
import { existsSync, lstatSync, mkdirSync, mkdtempSync, readFileSync, realpathSync, rmSync, symlinkSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { dirname, join, resolve } from 'node:path'
import { spawnSync } from 'node:child_process'
import { automaticCatalog, globalConfigPath, GLOBAL_SCHEMA, parseGlobalConfig, resolveMonitoring } from '../extensions/lazy-harness/monitoring/global.ts'
import { manageMonitoring, handleMonitoringControl } from '../extensions/lazy-harness/monitoring/manage.ts'
import { parseMonitoringAttachConfig } from '../extensions/lazy-harness/monitoring/config.ts'
import { installOptionalMonitoring } from '../extensions/lazy-harness/monitoring/load.ts'
import { installMonitoringPhase1 } from '../extensions/lazy-harness/monitoring/index.ts'

let temp: string, root: string, saved: NodeJS.ProcessEnv, messages: string[]
beforeEach(() => {
  saved = { ...process.env }; temp = realpathSync(mkdtempSync(join(tmpdir(), 'lh-global-'))); root = join(temp, 'project'); mkdirSync(root)
  process.env.HOME = temp; process.env.XDG_CONFIG_HOME = join(temp, 'config'); process.env.PI_CODING_AGENT_DIR = join(temp, 'pi'); messages = []
})
afterEach(() => { process.env = saved; rmSync(temp, { recursive: true, force: true }) })
function put(path: string, content = '# Fixture\n') { const file = join(root, path); mkdirSync(dirname(file), { recursive: true }); writeFileSync(file, content) }
function run(...args: string[]) { manageMonitoring(root, args, { print: t => messages.push(t) }) }
function globalRaw() { return { schema: GLOBAL_SCHEMA, defaults: { stage: 'observe', readFormat: 'pi-read-text-v1', budget: {} }, projects: [root] } }
function save(raw: unknown) { mkdirSync(dirname(globalConfigPath()), { recursive: true }); writeFileSync(globalConfigPath(), JSON.stringify(raw)) }
function fakePi() {
  const hooks = new Map<string, Function[]>(), commands = new Map<string, any>()
  return { hooks, commands, on(name: string, fn: Function) { hooks.set(name, [...hooks.get(name) ?? [], fn]) }, registerCommand(name: string, spec: any) { commands.set(name, spec) } }
}

test('strict global parser: schema, unknown keys at every level, types, stages and budgets', () => {
  expect(parseGlobalConfig(globalRaw()).defaults.budget.maxCalls).toBe(0)
  const raw = globalRaw()
  for (const bad of [null, [], {}, { ...raw, extra: true }, { ...raw, schema: 'v2' }, { ...raw, all: 1 }, { ...raw, projects: ['relative'] }, { ...raw, projects: [root, root] }, { ...raw, projects: [{ path: root }] }, { ...raw, defaults: { ...raw.defaults, catalog: [] } }, { ...raw, defaults: { ...raw.defaults, stage: 'active' } }, { ...raw, defaults: { ...raw.defaults, readFormat: null } }, { ...raw, defaults: { ...raw.defaults, budget: { extra: 1 } } }, { ...raw, defaults: { ...raw.defaults, budget: { maxCalls: -1 } } }, { ...raw, defaults: { ...raw.defaults, observeLog: true } }]) expect(() => parseGlobalConfig(bad)).toThrow()
})
test('project > global > off, realpath allowlist and symlinked cwd', () => {
  put('.lazy-harness/ssot/identity.md'); expect(resolveMonitoring(root).configSource).toBe('off')
  save({ ...globalRaw(), projects: [] }); expect(resolveMonitoring(root).reason).toBe('not_allowlisted')
  const alias = join(temp, 'alias'); symlinkSync(root, alias); save({ ...globalRaw(), projects: [alias] })
  expect(resolveMonitoring(alias)).toMatchObject({ configSource: 'global', allowlistMember: true, config: { references: { stage: 'observe' } } })
  put('.lazy-harness/monitoring-attach.json', '{"references":{"stage":"off"}}')
  expect(resolveMonitoring(root)).toMatchObject({ configSource: 'project', reason: 'project_disabled', allowlistMember: true, config: { references: { stage: 'off' } } })
  put('.lazy-harness/monitoring-attach.json', '{bad')
  expect(resolveMonitoring(root)).toMatchObject({ configSource: 'project', reason: 'invalid_monitoring_config', config: { references: { stage: 'off' } } })
})
test('automatic catalog sorts digest, bytes, path; refuses symlinks, oversize, invalid UTF-8 and other dirs', () => {
  put('.lazy-harness/ssot/b.md', '## Rule digest\nb'); put('.lazy-harness/ssot/a.md', '## Rule digest\na')
  put('.lazy-harness/decisions/small.md', 'a'); put('.lazy-harness/ssot/large.md', 'x'.repeat(8193))
  put('.lazy-harness/spec/not-selected.md'); put('.lazy-harness/ssot/empty.md', '')
  writeFileSync(join(root, '.lazy-harness/ssot/invalid.md'), Buffer.from([255]))
  symlinkSync(join(root, '.lazy-harness/ssot/a.md'), join(root, '.lazy-harness/ssot/link.md'))
  expect(automaticCatalog(root).map(d => d.id)).toEqual(['ssot:a', 'ssot:b', 'adr:small'])
  const other = join(temp, 'other'); mkdirSync(other); writeFileSync(join(other, 'escape.md'), 'secret'); rmSync(join(root, '.lazy-harness/decisions'), { recursive: true }); symlinkSync(other, join(root, '.lazy-harness/decisions'))
  expect(automaticCatalog(root).map(d => d.id)).toEqual(['ssot:a', 'ssot:b'])
})
test('automatic catalog caps count at 16 and bytes at 12288 inclusive', () => {
  for (let i = 0; i < 20; i++) put(`.lazy-harness/ssot/doc-${i}.md`, 'x'.repeat(768))
  const docs = automaticCatalog(root); expect(docs).toHaveLength(16); expect(docs.reduce((n, d) => n + d.bytes, 0)).toBe(12288)
  rmSync(join(root, '.lazy-harness'), { recursive: true }); put('.lazy-harness/ssot/a.md', 'x'.repeat(8192)); put('.lazy-harness/ssot/b.md', 'x'.repeat(4096)); put('.lazy-harness/ssot/c.md', 'x'.repeat(8192))
  expect(automaticCatalog(root).reduce((n, d) => n + d.bytes, 0)).toBe(12288)
})
test('empty/invalid global stays off: zero imports, registry lookups or classifier calls; notice and status', async () => {
  for (const raw of [globalRaw(), { ...globalRaw(), extra: true }]) {
    save(raw); const pi = fakePi(); let imports = 0, calls = 0
    installOptionalMonitoring(pi as any, root, async () => { imports++; throw Error('must not import') })
    const ctx = { ui: { notify: (t: string) => messages.push(t) }, modelRegistry: { classify() { calls++; throw Error('must not call') }, getModelOfType() { calls++; throw Error('must not look up') } } }
    for (const fn of pi.hooks.get('session_start') ?? []) await fn({}, ctx)
    await pi.commands.get('monitoring').handler('status', ctx)
    expect(imports).toBe(0); expect(calls).toBe(0)
    expect(messages.join('\n')).toContain('Monitoring off:')
    const status = JSON.parse(messages.at(-1)!); expect(status.ready).toBe(false); expect(status.stage).toBe('off'); expect(status.reason).toBe('extra' in raw ? 'invalid_global_monitoring_config' : 'no_catalog_documents')
  }
})
test('CLI private permissions, defaults-only, allowlist add/remove, dry-run and force; never project writes', () => {
  put('.lazy-harness/ssot/identity.md')
  run('enable', '--global', '--dry-run'); expect(existsSync(globalConfigPath())).toBe(false)
  run('enable', '--global'); expect(resolveMonitoring(root).configSource).toBe('off')
  expect(messages.join('\n')).toContain('conversation excerpts'); expect(lstatSync(globalConfigPath()).mode & 0o777).toBe(0o600); expect(lstatSync(dirname(globalConfigPath())).mode & 0o777).toBe(0o700)
  run('enable', '--global', '--project'); expect(resolveMonitoring(root).configSource).toBe('global')
  const before = readFileSync(globalConfigPath(), 'utf8')
  expect(() => run('enable', '--global', '--calls', '2')).toThrow('refusing overwrite')
  run('enable', '--global', '--calls', '2', '--force', '--dry-run'); expect(readFileSync(globalConfigPath(), 'utf8')).toBe(before)
  run('enable', '--global', '--calls', '2', '--force'); expect(resolveMonitoring(root).config.budget.maxCalls).toBe(2)
  run('config'); expect(messages.join('\n')).toContain('global_allowlisted'); expect(messages.join('\n')).toContain('"bytes"')
  run('disable', '--global', '--project', root, '--dry-run'); expect(resolveMonitoring(root).allowlistMember).toBe(true)
  run('disable', '--global', '--project', root); expect(resolveMonitoring(root).reason).toBe('not_allowlisted')
  expect(existsSync(join(root, '.lazy-harness/monitoring-attach.json'))).toBe(false)
  run('disable', '--global', '--dry-run'); expect(existsSync(globalConfigPath())).toBe(true)
  run('disable', '--global'); expect(existsSync(globalConfigPath())).toBe(false)
})
test('all:true only with explicit paired flags; project removal cannot misleadingly disable all', () => {
  expect(() => run('enable', '--global', '--all')).toThrow('requires'); expect(() => run('enable', '--global', '--i-understand')).toThrow('requires')
  expect(existsSync(globalConfigPath())).toBe(false); put('.lazy-harness/ssot/identity.md')
  run('enable', '--global', '--all', '--i-understand'); expect(resolveMonitoring(root)).toMatchObject({ all: true, allowlistMember: false, configSource: 'global' })
  expect(() => run('disable', '--global', '--project', root)).toThrow('Cannot exclude')
})
test('CLI canonicalizes project aliases, rejects unsafe config paths, and validates numeric overrides', () => {
  const alias = join(temp, 'alias'); symlinkSync(root, alias)
  run('enable', '--global', '--project', alias); expect(JSON.parse(readFileSync(globalConfigPath(), 'utf8')).projects).toEqual([root])
  for (const args of [['--calls', '-1'], ['--calls', '1.2'], ['--usd', 'Infinity'], ['--read-format', 'bad'], ['--doc', 'foo']]) expect(() => run('enable', '--global', '--force', ...args)).toThrow()
  rmSync(globalConfigPath()); symlinkSync(join(temp, 'missing'), globalConfigPath())
  expect(() => run('enable', '--global')).toThrow('Unsafe'); expect(resolveMonitoring(root).config.references.stage).toBe('off')
})
test('Pi global controls current root only, notify reload; status source global/project/off without classifier', async () => {
  put('.lazy-harness/ssot/identity.md'); const ui = { notify: (t: string) => messages.push(t) }
  expect(handleMonitoringControl('enable --global', root, ui)).toBe(true); expect(resolveMonitoring(root).allowlistMember).toBe(true); expect(messages.join('\n')).toContain('/reload')
  const pi = fakePi(); installMonitoringPhase1(pi as any, root)
  await pi.commands.get('monitoring').handler('status', { ui }); expect(JSON.parse(messages.at(-1)!).configSource).toBe('global')
  handleMonitoringControl('disable --global', root, ui); const off = fakePi(); installOptionalMonitoring(off as any, root)
  await off.commands.get('monitoring').handler('status', { ui }); expect(JSON.parse(messages.at(-1)!).configSource).toBe('off')
  put('.lazy-harness/monitoring-attach.json', JSON.stringify(parseMonitoringAttachConfig({ references: { stage: 'observe' }, observeLog: false })))
  const project = fakePi(); installMonitoringPhase1(project as any, root); await project.commands.get('monitoring').handler('status', { ui }); expect(JSON.parse(messages.at(-1)!).configSource).toBe('project')
})
test('HOME fallback, invalid global cannot override project, unsafe project presence fails closed', () => {
  delete process.env.XDG_CONFIG_HOME
  expect(globalConfigPath()).toBe(join(temp, '.config/lazy-harness/monitoring.json'))
  save({ ...globalRaw(), extra: true }); put('.lazy-harness/ssot/identity.md')
  put('.lazy-harness/monitoring-attach.json', '{"references":{"stage":"observe"},"catalog":[]}')
  expect(resolveMonitoring(root)).toMatchObject({ configSource: 'project', reason: 'project_config', config: { references: { stage: 'observe' }, catalog: [] } })
  rmSync(join(root, '.lazy-harness/monitoring-attach.json')); symlinkSync(join(temp, 'missing'), join(root, '.lazy-harness/monitoring-attach.json'))
  expect(resolveMonitoring(root)).toMatchObject({ configSource: 'project', reason: 'invalid_monitoring_config', config: { references: { stage: 'off' } } })
})
test('oversized global and symlink directory refuse; off defaults do not select catalog', () => {
  save(globalRaw()); writeFileSync(globalConfigPath(), 'x'.repeat(65537))
  expect(resolveMonitoring(root).reason).toBe('invalid_global_monitoring_config')
  save({ ...globalRaw(), defaults: { ...globalRaw().defaults, stage: 'off' } })
  expect(resolveMonitoring(root)).toMatchObject({ configSource: 'global', reason: 'global_disabled', catalog: [] })
  rmSync(dirname(globalConfigPath()), { recursive: true }); const target = join(temp, 'target'); mkdirSync(target); symlinkSync(target, dirname(globalConfigPath()))
  expect(() => run('enable', '--global')).toThrow('Unsafe'); expect(existsSync(join(target, 'monitoring.json'))).toBe(false)
})

test('whole global disable displays and removes malformed config without schema admission', () => {
  save({ unknown: true }); run('disable', '--global', '--dry-run'); expect(existsSync(globalConfigPath())).toBe(true)
  writeFileSync(globalConfigPath(), '{broken'); run('disable', '--global')
  expect(messages.join('\n')).toContain('{broken'); expect(existsSync(globalConfigPath())).toBe(false)
})

test('real offline dispatcher handles global flags with temp HOME/XDG and no project mutation', () => {
  const source = resolve(import.meta.dir, '../../..'), env = { ...process.env, LAZY_HOST_ROOT: root }; delete env.PI_FABRIC_LINEAGE
  const child = spawnSync('bun', [join(source, '.lazy-harness/scripts/monitoring.ts'), 'enable', '--global', '--project', root], { cwd: root, env, encoding: 'utf8' })
  expect(child.status).toBe(0); expect(child.stdout).toContain('No model calls made'); expect(existsSync(join(root, '.lazy-harness/monitoring-attach.json'))).toBe(false)
})
