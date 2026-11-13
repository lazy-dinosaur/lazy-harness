import { existsSync, readFileSync } from 'node:fs'
import { join } from 'node:path'
import type { MonitoringModelLimits } from '../../../../../vendor/lazy-harness-monitoring/composition.ts'
export type MonitoringAttachConfig = { references: { stage: 'off' | 'observe' }; catalog: Array<{ id: string; path: string }>; readFormat: 'unknown' | 'pi-read-text-v1' | 'pi-hashline-edit-pro-v1'; budget: MonitoringModelLimits }
const budget: MonitoringModelLimits = { maxCalls: 0, maxConcurrent: 1, maxQueued: 0, timeoutMs: 10000, maxInputBytes: 65536, maxOutputBytes: 65536, maxOutputTokens: 1, maxReservedTokens: 0, maxReservedUsd: 0 }
/** No config is written by installation. Unknown keys/stages fail closed, never activate a second module. */
export function readMonitoringAttachConfig(root: string): MonitoringAttachConfig {
  const path = join(root, '.lazy-harness', 'monitoring-attach.json')
  return parseMonitoringAttachConfig(existsSync(path) ? JSON.parse(readFileSync(path, 'utf8')) : {})
}
export function parseMonitoringAttachConfig(raw: unknown): MonitoringAttachConfig {
  const object = (x: unknown): x is Record<string, any> => !!x && typeof x === 'object' && !Array.isArray(x)
  if (!object(raw) || Object.keys(raw).some(k => !['references', 'catalog', 'readFormat', 'budget'].includes(k))) throw Error('invalid monitoring attach config')
  if (raw.references !== undefined && (!object(raw.references) || Object.keys(raw.references).some(k => k !== 'stage'))) throw Error('invalid references config')
  const stage = raw.references?.stage ?? 'off'
  if (!['off', 'observe'].includes(stage)) throw Error('phase 1 supports only off/observe references')
  const catalog = raw.catalog ?? []
  if (!Array.isArray(catalog) || catalog.length > 16 || catalog.some(d => !object(d) || Object.keys(d).some(k => !['id', 'path'].includes(k)) || typeof d.id !== 'string' || !/^[a-z][a-z0-9:._/-]{0,119}$/.test(d.id) || typeof d.path !== 'string' || !/^\.lazy-harness\/(domain|spec|behavior|tests|decisions|ssot|planning)\/.+\.(md|xml)$/.test(d.path) || d.path.split('/').includes('..')) || new Set(catalog.map(d => d.id)).size !== catalog.length || new Set(catalog.map(d => d.path)).size !== catalog.length) throw Error('explicit bounded catalog required')
  const readFormat = raw.readFormat ?? 'unknown'
  if (!['unknown', 'pi-read-text-v1', 'pi-hashline-edit-pro-v1'].includes(readFormat)) throw Error('invalid read format')
  if (raw.budget !== undefined && (!object(raw.budget) || Object.keys(raw.budget).some(k => !(k in budget)))) throw Error('invalid model budget')
  const limits = { ...budget, ...raw.budget }
  for (const [key, value] of Object.entries(limits)) if (typeof value !== 'number' || !Number.isFinite(value) || value < 0 || key !== 'maxReservedUsd' && !Number.isSafeInteger(value)) throw Error('invalid model budget')
  return { references: { stage }, catalog: catalog.map(d => ({ ...d })), readFormat, budget: limits }
}
