import { constants, chmodSync, closeSync, fsyncSync, linkSync, lstatSync, mkdirSync, openSync, realpathSync, renameSync, unlinkSync, writeFileSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { randomUUID } from 'node:crypto'
import { configText, globalConfigPath, GLOBAL_SCHEMA, parseGlobalConfig } from './global.ts'
import { parseMonitoringAttachConfig, type MonitoringAttachConfig } from './config.ts'

const usage = 'Global usage: enable --global [--project [PATH]] [--calls N] [--usd X] [--read-format F] [--all --i-understand] [--dry-run] [--force] | disable --global [--project [PATH]] [--dry-run]'
export function manageGlobalMonitoring(root: string, args: string[], readFormat: MonitoringAttachConfig['readFormat'], emit: (text: string) => void) {
  const [command, ...flags] = args
  if (!['enable', 'disable'].includes(command)) throw Error(usage)
  let project: string | undefined, all = false, consent = false, force = false, dry = false
  const overrides: { calls?: number; usd?: number; format?: string } = {}
  for (let i = 0; i < flags.length; i++) {
    const key = flags[i]
    if (key === '--global') continue
    if (key === '--dry-run') { dry = true; continue }
    if (key === '--project') { project = flags[i + 1] && !flags[i + 1].startsWith('--') ? flags[++i] : root; continue }
    if (command === 'disable') throw Error(usage)
    if (key === '--all') all = true
    else if (key === '--i-understand') consent = true
    else if (key === '--force') force = true
    else if (['--calls', '--usd', '--read-format'].includes(key)) {
      const value = flags[++i]
      if (!value || value.startsWith('--')) throw Error(usage)
      if (key === '--read-format') overrides.format = value
      if (key === '--calls') { if (!/^\d+$/.test(value)) throw Error('calls must be a nonnegative safe integer'); overrides.calls = Number(value) }
      if (key === '--usd') { if (!/^(?:\d+(?:\.\d*)?|\.\d+)$/.test(value)) throw Error('usd must be a finite nonnegative number'); overrides.usd = Number(value) }
    } else throw Error(usage)
  }
  if (all !== consent) throw Error('all:true requires --all --i-understand together')
  if (all && project !== undefined) throw Error('Choose --all or --project, not both')
  const file = globalConfigPath(), old = configText(file)
  // Whole-file disable must remain available even for malformed JSON/schema.
  const previous = old === undefined || command === 'disable' && project === undefined ? undefined : parseGlobalConfig(JSON.parse(old))
  if (project !== undefined) project = realpathSync(resolve(project))
  const sameProject = (p: string) => { try { return realpathSync(p) === project } catch { return p === project } }
  if (command === 'disable') {
    if (old === undefined) { emit('Global monitoring already disabled (config absent).'); return }
    emit(`${file}:\n${old}`)
    if (project === undefined) {
      if (!dry) { if (configText(file) !== old) throw Error('Monitoring config changed; retry'); unlinkSync(file) }
      emit(`${dry ? 'Would remove' : 'Removed'} ${file}; no project files changed. Next: /reload in Pi.`)
      return
    }
    if (previous!.all) throw Error('Cannot exclude a project while all:true; disable the global file first.')
    previous!.projects = previous!.projects.filter(p => !sameProject(p))
  }
  const base = previous?.defaults
  const defaults = parseMonitoringAttachConfig({ references: { stage: command === 'enable' ? 'observe' : base!.stage }, readFormat: overrides.format ?? base?.readFormat ?? readFormat, observeLog: base?.observeLog, budget: { ...(base?.budget ?? { maxCalls: 100, maxConcurrent: 1, maxQueued: 2, maxReservedTokens: 1000000, maxReservedUsd: 0.05 }), ...(overrides.calls === undefined ? {} : { maxCalls: overrides.calls }), ...(overrides.usd === undefined ? {} : { maxReservedUsd: overrides.usd }) } })
  const nextConfig = parseGlobalConfig({ schema: GLOBAL_SCHEMA, defaults: { stage: defaults.references.stage, readFormat: defaults.readFormat, budget: defaults.budget, ...(defaults.observeLog === undefined ? {} : { observeLog: defaults.observeLog }) }, projects: previous?.projects ?? [], ...(previous?.all || all ? { all: true } : {}) })
  if (command === 'enable' && project !== undefined && !nextConfig.projects.some(sameProject)) nextConfig.projects.push(project)
  nextConfig.projects.sort()
  const next = JSON.stringify(nextConfig, null, 2) + '\n'
  if (command === 'enable' && old === undefined) emit('Consent: conversation excerpts of allowlisted projects are sent to OpenRouter Jev during judgement. Budgets are per session; totals scale with open sessions.')
  emit(`--- ${old === undefined ? '/dev/null' : file}\n+++ ${file}\n${old === undefined ? '' : old.trimEnd().split('\n').map(l => '-' + l).join('\n') + '\n'}${next.trimEnd().split('\n').map(l => '+' + l).join('\n')}`)
  // Allowlist-only edits are additive/removal controls; replacing defaults or all requires force.
  const changedDefaults = previous && (JSON.stringify(previous.defaults) !== JSON.stringify(nextConfig.defaults) || previous.all !== nextConfig.all)
  if (command === 'enable' && previous && (project === undefined || changedDefaults) && !force) throw Error('Config exists; refusing overwrite. Review the diff, then use --force.')
  if (!dry) publish(file, old, next)
  emit(`${dry ? 'Would update' : 'Updated'} global monitoring: ${nextConfig.projects.length} allowlisted projects, all=${nextConfig.all === true}. No project files changed. No model calls made.`)
  emit('Next: /login openrouter if needed; /reload in Pi; /monitoring status.')
}
function publish(file: string, old: string | undefined, next: string) {
  const dir = dirname(file)
  // Check existing ancestors before mkdir: configText returns absent early for a missing leaf.
  let parent = dir
  while (true) {
    try { if (lstatSync(parent).isSymbolicLink() || !lstatSync(parent).isDirectory()) throw Error('Unsafe global config directory') }
    catch (e: any) { if (e.code !== 'ENOENT') throw e }
    const up = dirname(parent); if (up === parent) break; parent = up
  }
  mkdirSync(dir, { recursive: true, mode: 0o700 }); chmodSync(dir, 0o700)
  if (configText(file) !== old) throw Error('Monitoring config changed; retry')
  const temp = join(dir, `.monitoring-${randomUUID()}.tmp`)
  let fd: number | undefined
  try {
    fd = openSync(temp, constants.O_WRONLY | constants.O_CREAT | constants.O_EXCL | constants.O_NOFOLLOW, 0o600)
    writeFileSync(fd, next); fsyncSync(fd); closeSync(fd); fd = undefined
    if (configText(file) !== old) throw Error('Monitoring config changed; retry')
    if (old === undefined) linkSync(temp, file); else renameSync(temp, file)
  } finally { if (fd !== undefined) closeSync(fd); try { unlinkSync(temp) } catch (e: any) { if (e.code !== 'ENOENT') throw e } }
}
