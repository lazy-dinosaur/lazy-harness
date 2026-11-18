import { constants, closeSync, fstatSync, lstatSync, openSync, readFileSync, realpathSync, readdirSync } from 'node:fs'
import { homedir } from 'node:os'
import { isAbsolute, join, basename, dirname, resolve } from 'node:path'
import { parseMonitoringAttachConfig, type MonitoringAttachConfig } from './config.ts'
import { captureRecord, admitCatalog } from './catalog.ts'

export const GLOBAL_SCHEMA = 'lazy-harness-monitoring-global/v1'
export type GlobalConfig = { schema: typeof GLOBAL_SCHEMA; defaults: { stage: 'off' | 'observe'; readFormat: MonitoringAttachConfig['readFormat']; budget: MonitoringAttachConfig['budget']; observeLog?: false | string }; projects: string[]; all?: boolean }
export function globalConfigPath() { return join(process.env.XDG_CONFIG_HOME || join(process.env.HOME || homedir(), '.config'), 'lazy-harness/monitoring.json') }
/** Private config IO: bounded regular files, no symlink component, stable open identity. */
export function configText(file: string): string | undefined {
  let fd: number | undefined
  try {
    let cursor = resolve(file)
    while (true) { const s = lstatSync(cursor); if (s.isSymbolicLink()) throw Error('Unsafe monitoring config path'); const parent = dirname(cursor); if (parent === cursor) break; cursor = parent }
    const before = lstatSync(file)
    if (!before.isFile() || before.size > 65536) throw Error('Unsafe or oversized monitoring config')
    fd = openSync(file, constants.O_RDONLY | constants.O_NOFOLLOW)
    const opened = fstatSync(fd)
    if (opened.dev !== before.dev || opened.ino !== before.ino) throw Error('Monitoring config changed')
    const bytes = readFileSync(fd), after = fstatSync(fd), current = lstatSync(file)
    if (bytes.length > 65536 || !Buffer.from(bytes.toString('utf8')).equals(bytes) || ['dev', 'ino', 'size', 'mtimeMs', 'ctimeMs'].some(k => (opened as any)[k] !== (after as any)[k] || (after as any)[k] !== (current as any)[k])) throw Error('Monitoring config changed')
    return bytes.toString('utf8')
  } catch (e: any) { if (e.code === 'ENOENT') return; throw e }
  finally { if (fd !== undefined) closeSync(fd) }
}
export function parseGlobalConfig(raw: unknown): GlobalConfig {
  const object = (v: unknown): v is Record<string, any> => !!v && typeof v === 'object' && !Array.isArray(v)
  if (!object(raw) || Object.keys(raw).some(k => !['schema', 'defaults', 'projects', 'all'].includes(k)) || raw.schema !== GLOBAL_SCHEMA || !object(raw.defaults) || Object.keys(raw.defaults).some(k => !['stage', 'readFormat', 'budget', 'observeLog'].includes(k)) || !['off', 'observe'].includes(raw.defaults.stage) || !['unknown', 'pi-read-text-v1', 'pi-hashline-edit-pro-v1'].includes(raw.defaults.readFormat) || !object(raw.defaults.budget) || !Array.isArray(raw.projects) || raw.projects.some(p => typeof p !== 'string' || !isAbsolute(p)) || new Set(raw.projects).size !== raw.projects.length || (raw.all !== undefined && typeof raw.all !== 'boolean')) throw Error('Invalid global monitoring config')
  const budgetKeys = Object.keys(parseMonitoringAttachConfig({}).budget)
  if (Object.keys(raw.defaults.budget).some(k => !budgetKeys.includes(k))) throw Error('Invalid global monitoring budget')
  const config = parseMonitoringAttachConfig({ references: { stage: raw.defaults.stage }, readFormat: raw.defaults.readFormat, budget: raw.defaults.budget, observeLog: raw.defaults.observeLog })
  return { schema: GLOBAL_SCHEMA, defaults: { stage: config.references.stage, readFormat: config.readFormat, budget: config.budget, ...(config.observeLog === undefined ? {} : { observeLog: config.observeLog }) }, projects: [...raw.projects], ...(raw.all === undefined ? {} : { all: raw.all }) }
}
/** Only direct project-owned Markdown files. Admission remains the existing byte/path authority. */
export function automaticCatalog(root: string) {
  const candidates: Array<{ id: string; path: string; bytes: number; digest: boolean }> = []
  for (const layer of ['ssot', 'decisions']) {
    const dir = `.lazy-harness/${layer}`
    let names: string[]
    try { names = readdirSync(join(root, dir)) } catch { continue }
    for (const name of names) {
      if (!name.endsWith('.md')) continue
      const path = `${dir}/${name}`, bytes = captureRecord(root, path)
      if (!bytes?.length) continue
      const id = `${layer === 'ssot' ? 'ssot' : 'adr'}:${basename(name, '.md')}`
      try { parseMonitoringAttachConfig({ catalog: [{ id, path }] }) } catch { continue }
      candidates.push({ id, path, bytes: bytes.length, digest: /^## Rule digest\r?$/m.test(bytes.toString('utf8')) })
    }
  }
  candidates.sort((a, b) => Number(b.digest) - Number(a.digest) || a.bytes - b.bytes || (a.path < b.path ? -1 : a.path > b.path ? 1 : 0))
  const selected: typeof candidates = []; let total = 0
  for (const d of candidates) if (selected.length < 16 && total + d.bytes <= 12288) { selected.push(d); total += d.bytes }
  return selected
}
export type EffectiveMonitoring = { config: MonitoringAttachConfig; configSource: 'project' | 'global' | 'off'; reason: string; allowlistMember: boolean; all: boolean; catalog: Array<{ id: string; path: string; bytes: number }> }
/** All failures are content-free and off; project presence wins, even when invalid. No vendor runtime. */
export function resolveMonitoring(root: string): EffectiveMonitoring {
  const off = parseMonitoringAttachConfig({})
  let source: EffectiveMonitoring['configSource'] = 'off', member = false, all = false
  const result = (config = off, reason = 'not_allowlisted', catalog: EffectiveMonitoring['catalog'] = []): EffectiveMonitoring => ({ config, configSource: source, reason, allowlistMember: member, all, catalog })
  try {
    root = realpathSync(root)
    const projectFile = join(root, '.lazy-harness/monitoring-attach.json')
    try { lstatSync(projectFile); source = 'project' } catch (e: any) { if (e.code !== 'ENOENT') { source = 'project'; throw e } }
    const project = configText(projectFile)
    if (project !== undefined) {
      source = 'project'
      const config = parseMonitoringAttachConfig(JSON.parse(project))
      // Membership is diagnostic only here; invalid global input cannot override the project.
      try {
        const text = configText(globalConfigPath())
        if (text !== undefined) {
          const global = parseGlobalConfig(JSON.parse(text))
          member = global.projects.some(p => { try { return realpathSync(p) === root } catch { return false } }); all = global.all === true
        }
      } catch { /* Project authority is independent of global validity. */ }
      return result(config, config.references.stage === 'off' ? 'project_disabled' : 'project_config', config.catalog.map(d => ({ ...d, bytes: captureRecord(root, d.path)?.length ?? 0 })))
    }
    const text = configText(globalConfigPath())
    if (text === undefined) return result(off, 'config_absent')
    const global = parseGlobalConfig(JSON.parse(text))
    member = global.projects.some(p => { try { return realpathSync(p) === root } catch { return false } }); all = global.all === true
    if (!member && !all) return result()
    source = 'global'
    if (global.defaults.stage === 'off') return result(off, 'global_disabled')
    const catalog = automaticCatalog(root)
    if (!catalog.length) return result(off, 'no_catalog_documents')
    const config = parseMonitoringAttachConfig({ references: { stage: global.defaults.stage }, readFormat: global.defaults.readFormat, budget: global.defaults.budget, observeLog: global.defaults.observeLog, catalog: catalog.map(({ id, path }) => ({ id, path })) })
    admitCatalog(root, config)
    return result(config, 'global_allowlisted', catalog)
  } catch { return result(off, source === 'project' ? 'invalid_monitoring_config' : 'invalid_global_monitoring_config') }
}
