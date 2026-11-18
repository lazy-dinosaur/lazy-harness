import { constants, closeSync, existsSync, fstatSync, fsyncSync, linkSync, lstatSync, mkdirSync, openSync, readFileSync, realpathSync, renameSync, unlinkSync, writeFileSync } from 'node:fs'
import { randomUUID } from 'node:crypto'
import { homedir } from 'node:os'
import { basename, join, resolve } from 'node:path'
import { parseMonitoringAttachConfig, type MonitoringAttachConfig } from './config.ts'
import { admitCatalog } from './catalog.ts'
import { resolveMonitoring } from './global.ts'
import { manageGlobalMonitoring } from './global-manage.ts'

export const CONFIG_PATH = '.lazy-harness/monitoring-attach.json'
export const DEFAULT_DOCUMENTS = [
  { id: 'ssot:monitoring-records-ownership', path: '.lazy-harness/ssot/monitoring-records-ownership.md' },
  { id: 'adr:0062-monitoring-core-own-repository', path: '.lazy-harness/decisions/0062-monitoring-core-own-repository.md' },
]
export type ManageDeps = { print?: (text: string) => void; settingsFile?: string }
const json = (value: unknown) => JSON.stringify(value, null, 2) + '\n'
const usage = 'Usage: lazy monitoring enable [--doc PATH]... [--no-default-docs] [--calls N] [--usd X] [--read-format F] [--force] [--dry-run] | disable [--dry-run] | config'

/** Settings metadata only: never load an SDK, auth storage, provider or model registry. */
export function detectReadFormat(settingsFile = join(process.env.PI_CODING_AGENT_DIR || join(homedir(), '.pi/agent'), 'settings.json')): MonitoringAttachConfig['readFormat'] {
  try {
    const packages = JSON.parse(readFileSync(settingsFile, 'utf8')).packages
    if (Array.isArray(packages) && packages.some(entry => {
      const source = typeof entry === 'string' ? entry : entry?.source
      return typeof source === 'string' && /(?:^npm:|[/\\])pi-hashline-edit-pro(?:@[^/\\]+)?\/?$/.test(source)
    })) return 'pi-hashline-edit-pro-v1'
  } catch { /* Unknown settings are not evidence of a hashline installation. */ }
  return 'pi-read-text-v1'
}

function options(args: string[]) {
  const command = args.shift()
  if (!['enable', 'disable', 'config'].includes(command ?? '')) throw Error(usage)
  const o = { command, docs: [] as string[], defaults: true, calls: 100, usd: 0.05, format: undefined as string | undefined, force: false, dryRun: false }
  while (args.length) {
    const key = args.shift()!
    if (key === '--dry-run' && command !== 'config') o.dryRun = true
    else if (command !== 'enable') throw Error(usage)
    else if (key === '--force') o.force = true
    else if (key === '--no-default-docs') o.defaults = false
    else if (['--doc', '--calls', '--usd', '--read-format'].includes(key)) {
      const value = args.shift()
      if (!value || value.startsWith('--')) throw Error('Missing option value. ' + usage)
      if (key === '--doc') o.docs.push(value)
      if (key === '--read-format') o.format = value
      if (key === '--calls') { if (!/^\d+$/.test(value)) throw Error('calls must be a nonnegative safe integer'); o.calls = Number(value) }
      if (key === '--usd') { if (!/^(?:\d+(?:\.\d*)?|\.\d+)$/.test(value)) throw Error('usd must be a finite nonnegative number'); o.usd = Number(value) }
    } else throw Error(usage)
  }
  return o
}

/** Refuse directory/file symlinks, nonregular files and unbounded config reads. */
function current(root: string): string | undefined {
  const dir = join(root, '.lazy-harness'), file = join(root, CONFIG_PATH)
  try { if (!lstatSync(dir).isDirectory() || lstatSync(dir).isSymbolicLink()) throw Error('Unsafe monitoring config directory') }
  catch (e: any) { if (e.code === 'ENOENT') return; throw e }
  let fd: number | undefined
  try {
    const stat = lstatSync(file)
    if (!stat.isFile() || stat.isSymbolicLink() || stat.size > 65536) throw Error('Unsafe or oversized monitoring config')
    fd = openSync(file, constants.O_RDONLY | constants.O_NOFOLLOW)
    const opened = fstatSync(fd)
    if (opened.dev !== stat.dev || opened.ino !== stat.ino) throw Error('Monitoring config changed; retry')
    return readFileSync(fd, 'utf8')
  } catch (e: any) { if (e.code === 'ENOENT') return; throw e }
  finally { if (fd !== undefined) closeSync(fd) }
}
function diff(old: string | undefined, next: string) {
  const lines = (s: string, prefix: string) => s.trimEnd().split('\n').map(line => prefix + line).join('\n')
  return `--- ${old === undefined ? '/dev/null' : CONFIG_PATH}\n+++ ${CONFIG_PATH}\n@@ whole file @@\n${old === undefined ? '' : lines(old, '-') + '\n'}${lines(next, '+')}`
}
function atomicWrite(root: string, next: string, old: string | undefined, force: boolean) {
  mkdirSync(join(root, '.lazy-harness'), { recursive: true })
  if (current(root) !== old) throw Error('Monitoring config changed; retry')
  const file = join(root, CONFIG_PATH), temp = join(root, '.lazy-harness', `.monitoring-attach-${randomUUID()}.tmp`)
  let fd: number | undefined
  try {
    fd = openSync(temp, constants.O_WRONLY | constants.O_CREAT | constants.O_EXCL | constants.O_NOFOLLOW, 0o644)
    writeFileSync(fd, next); fsyncSync(fd); closeSync(fd); fd = undefined
    if (current(root) !== old) throw Error('Monitoring config changed; retry')
    // link is an atomic no-clobber publication; rename is only allowed by explicit --force.
    if (force) renameSync(temp, file)
    else linkSync(temp, file)
  } finally {
    if (fd !== undefined) closeSync(fd)
    if (existsSync(temp)) unlinkSync(temp)
  }
}

/** Shared offline CLI/Pi controls. Global mode never mutates a project file. */
export function manageMonitoring(root: string, args: string[], deps: ManageDeps = {}) {
  const emit = deps.print ?? console.log
  root = realpathSync(resolve(root))
  if (args.includes('--global')) return manageGlobalMonitoring(root, args, detectReadFormat(deps.settingsFile), emit)
  const o = options([...args])
  const old = o.command === 'config' ? undefined : current(root)
  if (o.command === 'config') {
    try {
      const effective = resolveMonitoring(root), { config } = effective
      emit(json({ ...config, ...effective }).trimEnd())
      if (effective.reason.startsWith('invalid_')) throw Error('Invalid monitoring config')
      admitCatalog(root, config)
      emit(effective.reason === 'config_absent' ? 'Validation: OK (absent; effective off)' : 'Validation: OK')
    } catch { emit('Validation: FAILED (invalid config or catalog; effective monitoring unavailable)'); throw Error('Monitoring config validation failed') }
    return
  }
  if (o.command === 'disable') {
    if (old === undefined) emit('Monitoring already disabled (config absent).')
    else {
      emit(`${CONFIG_PATH}:\n${old}`)
      if (!o.dryRun) {
        if (current(root) !== old) throw Error('Monitoring config changed; retry')
        unlinkSync(join(root, CONFIG_PATH))
      }
      emit(`${o.dryRun ? 'Would remove' : 'Removed'} ${CONFIG_PATH}; no other files changed.`)
    }
    emit('Next: /reload in Pi. Running monitoring is unchanged until reload.')
    return
  }
  const catalog = o.defaults ? DEFAULT_DOCUMENTS.filter(d => {
    if (existsSync(join(root, d.path))) return true
    emit('Skipped missing default doc: ' + d.path); return false
  }).map(d => ({ ...d })) : []
  for (const path of o.docs) {
    // Keep caller bytes/path intact so the real parser/admission rejects traversal and absolute paths.
    const layer = path.split('/')[1], name = basename(path).replace(/\.(md|xml)$/, '').toLowerCase()
    if (!catalog.some(d => d.path === path)) catalog.push({ id: `${layer === 'decisions' ? 'adr' : layer}:${name}`, path })
  }
  const config = parseMonitoringAttachConfig({ references: { stage: 'observe' }, catalog, readFormat: o.format ?? detectReadFormat(deps.settingsFile), budget: { maxCalls: o.calls, maxConcurrent: 1, maxQueued: 2, maxReservedTokens: 1000000, maxReservedUsd: o.usd } })
  admitCatalog(root, config)
  const next = json(config)
  emit(diff(old, next))
  if (old !== undefined && !o.force) throw Error('Config exists; refusing overwrite. Review the diff, then use --force.')
  if (!o.dryRun) atomicWrite(root, next, old, o.force)
  emit(`${o.dryRun ? 'Would enable' : 'Enabled'} monitoring observe: ${catalog.length} docs, maxCalls ${o.calls}, maxReservedUsd ${o.usd}. No model calls made.`)
  // Deliberately uncertain: do not open auth.json or read secret values just to suppress a hint.
  emit('Next: /login openrouter if no stored OpenRouter credential (not checked); then /reload in Pi; then /monitoring status.')
}

/** Slash global controls explicitly add/remove only the current root; custom flags remain CLI-only. */
export function handleMonitoringControl(args: string, root: string, ui: { notify: (text: string, level: 'info' | 'warning') => void }, run = manageMonitoring): boolean {
  const value = args.trim()
  if (!/^(enable|disable)(?:\s|$)/.test(value)) return false
  const global = /^(enable|disable)\s+--global$/.exec(value)
  const commandArgs = global ? [global[1], '--global', '--project', root] : [value]
  try { run(root, commandArgs, { print: text => ui.notify(text, 'info') }) }
  catch (error) { ui.notify(error instanceof Error ? error.message : 'Monitoring config change failed', 'warning') }
  return true
}
