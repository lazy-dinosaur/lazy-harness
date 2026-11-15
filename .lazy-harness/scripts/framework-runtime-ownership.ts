import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs'
import path from 'node:path'
import { shouldIncludeManifestPath } from './manifest-path-matcher.ts'

export type RuntimeScope = 'framework' | 'host'
interface ManifestItem { path: string; kind: 'file' | 'directory'; glob?: string[]; exclude?: string[] }
const roots = ['scripts', 'hooks', 'bin', 'manifests', 'schemas', 'fixtures']
const suffixes = new Set(['.md', '.ts', '.tsx', '.js', '.py', '.sh', '.json', '.jsonl', '.xml', '.toml', '.yaml', '.yml', '.txt'])
function record(value: unknown): value is Record<string, unknown> { return value !== null && typeof value === 'object' && !Array.isArray(value) }
function stringList(value: unknown): value is string[] { return Array.isArray(value) && value.every(item => typeof item === 'string') }
export function managedRuntimeItems(raw: unknown): ManifestItem[] {
  if (!record(raw) || !record(raw.categories) || !record(raw.categories.A) || !Array.isArray(raw.categories.A.items) || !raw.categories.A.items.length) throw new Error('Missing Category A runtime ownership manifest')
  return raw.categories.A.items.map((item: unknown) => {
    if (!record(item) || typeof item.path !== 'string' || !item.path || path.posix.isAbsolute(item.path) || item.path.split('/').includes('..') || !['file', 'directory'].includes(String(item.kind))) throw new Error('Invalid Category A ownership item')
    if ((item.glob !== undefined && !stringList(item.glob)) || (item.exclude !== undefined && !stringList(item.exclude))) throw new Error('Invalid Category A ownership patterns')
    return { path: item.path, kind: item.kind === 'file' ? 'file' : 'directory', glob: item.glob as string[] | undefined, exclude: item.exclude as string[] | undefined }
  })
}
export function isManagedRuntimePath(relative: string, items: ManifestItem[]): boolean {
  return items.some(item => {
    const prefix = item.path.replace(/\/$/, '')
    if (item.kind === 'file') return relative === prefix
    return relative.startsWith(prefix + '/') && shouldIncludeManifestPath(relative.slice(prefix.length + 1), item.glob, item.exclude)
  })
}
export function collectRuntimePaths(lazyRoot: string, scope: RuntimeScope): string[] {
  const items = scope === 'host' ? managedRuntimeItems(JSON.parse(readFileSync(path.join(lazyRoot, 'manifests/init-categories.json'), 'utf8'))) : []
  const files: string[] = []
  const walk = (directory: string): void => {
    if (!existsSync(directory)) return
    for (const entry of readdirSync(directory, { withFileTypes: true })) {
      if (entry.name === '__pycache__') continue
      const full = path.join(directory, entry.name)
      if (entry.isDirectory()) { walk(full); continue }
      let file = entry.isFile()
      if (entry.isSymbolicLink()) {
        try { file = statSync(full).isFile() }
        catch (error) { if (!record(error) || error.code !== 'ENOENT') throw error }
      }
      if (!file || !suffixes.has(path.extname(entry.name))) continue
      const relative = path.relative(lazyRoot, full).split(path.sep).join('/')
      if (scope === 'framework' || isManagedRuntimePath(relative, items)) files.push(relative)
    }
  }
  for (const root of roots) walk(path.join(lazyRoot, root))
  return files.sort()
}
if (import.meta.main) {
  const args = process.argv.slice(2)
  const rootAt = args.indexOf('--root')
  const scopeAt = args.indexOf('--scope')
  const root = rootAt >= 0 ? args[rootAt + 1] : undefined
  const scope = scopeAt >= 0 ? args[scopeAt + 1] : undefined
  if (!root || (scope !== 'host' && scope !== 'framework') || args.length !== 4) throw new Error('Use --root <harness-root> --scope framework|host')
  console.log(JSON.stringify({ schemaVersion: 1, scope, paths: collectRuntimePaths(path.resolve(root), scope) }))
}
