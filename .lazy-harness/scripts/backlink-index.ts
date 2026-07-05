#!/usr/bin/env bun
/**
 * backlink-index.ts — derive the backlink index from forward links (W2, memory-device plan).
 *
 * Backlinks are DERIVED data (never hand-stored): computed from
 *   (a) in-file `.lazy-harness/...md` references across canonical + planning/plans/knowledge docs
 *       (fenced code blocks stripped), and
 *   (b) graph.jsonl rows that mention a record path (any schema generation; row ids listed
 *       as graph evidence).
 *
 * Output: `.lazy-harness/generated/backlink-index.json` — rebuildable, non-canonical, cue-only.
 * Surface: `lazy map <record>` drill-down renders a "referenced by" line from this index.
 * Fallback protocol (works with stale/absent index): `grep -rl <record-path> .lazy-harness/`.
 *
 * Contract: ADR memory-device storage discipline; W2 of memory-device-implementation-plan.
 */
import { existsSync, mkdirSync, readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs'
import path from 'node:path'

const DOC_DIRS = ['domain', 'spec', 'behavior', 'tests', 'decisions', 'ssot', 'planning', 'plans', 'knowledge']
const LINK_RE = /\.lazy-harness\/[A-Za-z0-9_\-./]+?\.md/g

function findHarnessRoot(start: string): string | null {
  let cur = path.resolve(start)
  while (true) {
    if (existsSync(path.join(cur, '.lazy-harness'))) return cur
    const parent = path.dirname(cur)
    if (parent === cur) return null
    cur = parent
  }
}

function listMarkdown(dir: string): string[] {
  const out: string[] = []
  if (!existsSync(dir)) return out
  const walk = (d: string) => {
    for (const entry of readdirSync(d)) {
      const p = path.join(d, entry)
      const st = statSync(p)
      if (st.isDirectory()) walk(p)
      else if (entry.endsWith('.md') && entry !== 'README.md') out.push(p)
    }
  }
  walk(dir)
  return out
}

function stripFences(text: string): string {
  return text.replace(/```[\s\S]*?```/g, '')
}

export interface BacklinkIndexResult {
  outPath: string
  docCount: number
  targetCount: number
}

/**
 * Compute and write generated/backlink-index.json for the given harness root.
 * Exported so record-index rebuild paths (record-map/record-index) can keep the
 * derived backlink index fresh automatically (memory-device small-automation #1).
 */
export function refreshBacklinkIndex(root: string): BacklinkIndexResult {
  const lh = path.join(root, '.lazy-harness')
  const rel = (p: string) => path.relative(root, p)

  const docs = DOC_DIRS.flatMap((d) => listMarkdown(path.join(lh, d)))
  const docSet = new Set(docs.map(rel))

  const referencedBy = new Map<string, Set<string>>()
  for (const doc of docs) {
    const from = rel(doc)
    const body = stripFences(readFileSync(doc, 'utf8'))
    for (const m of body.matchAll(LINK_RE)) {
      const target = m[0]
      if (target === from || !docSet.has(target)) continue
      if (!referencedBy.has(target)) referencedBy.set(target, new Set())
      referencedBy.get(target)!.add(from)
    }
  }

  // graph.jsonl mentions (all schema generations: scan every string field for record paths)
  const graphRefs = new Map<string, Set<string>>()
  const graphPath = path.join(lh, 'knowledge', 'graph.jsonl')
  if (existsSync(graphPath)) {
    for (const line of readFileSync(graphPath, 'utf8').split(/\r?\n/)) {
      if (!line.trim()) continue
      try {
        const row = JSON.parse(line) as Record<string, unknown>
        const id = typeof row.id === 'string' ? row.id : null
        if (!id) continue
        for (const value of Object.values(row)) {
          if (typeof value !== 'string') continue
          for (const m of value.matchAll(LINK_RE)) {
            const target = m[0].replace(/^\.lazy-harness/, '.lazy-harness')
            if (!docSet.has(target)) continue
            if (!graphRefs.has(target)) graphRefs.set(target, new Set())
            graphRefs.get(target)!.add(id)
          }
        }
      } catch {
        /* graph-hygiene owns invalid rows */
      }
    }
  }

  const entries: Record<string, { referencedBy: string[]; graphRefIds: string[] }> = {}
  const targets = new Set([...referencedBy.keys(), ...graphRefs.keys()])
  for (const target of [...targets].sort()) {
    entries[target] = {
      referencedBy: [...(referencedBy.get(target) ?? [])].sort(),
      graphRefIds: [...(graphRefs.get(target) ?? [])].sort(),
    }
  }

  const result = {
    schemaVersion: '1.0',
    mode: 'backlink-index',
    derived: true,
    note: 'Rebuildable derived index (backlinks are computed from forward links + graph.jsonl mentions; never hand-maintained). Cue-only; fallback: grep -rl <record-path> .lazy-harness/',
    generatedAt: new Date().toISOString(),
    docCount: docs.length,
    targetCount: targets.size,
    entries,
  }

  const outDir = path.join(lh, 'generated')
  mkdirSync(outDir, { recursive: true })
  const outPath = path.join(outDir, 'backlink-index.json')
  writeFileSync(outPath, `${JSON.stringify(result, null, 2)}\n`)
  return { outPath: rel(outPath), docCount: docs.length, targetCount: targets.size }
}

function main(): number {
  const argRoot = process.argv.find((a) => a.startsWith('--root='))?.slice('--root='.length)
  const root = findHarnessRoot(argRoot ? path.resolve(argRoot) : process.cwd())
  if (!root) {
    console.error('backlink-index: no .lazy-harness root found')
    return 1
  }
  const res = refreshBacklinkIndex(root)
  console.log(`backlink-index: wrote ${res.outPath} (docs=${res.docCount}, targets=${res.targetCount})`)
  return 0
}

if (import.meta.main) process.exit(main())
