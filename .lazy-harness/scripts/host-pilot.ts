#!/usr/bin/env bun
/**
 * N2 host-pilot harness
 *
 * For each input commit (or commit range) on the host project, replay the N1
 * Layer Impact Gate as if those changes had just landed, and write a
 * machine-readable + human-readable record so the operator can label each
 * case as true-positive / false-positive / false-negative.
 *
 * Output format per commit:
 *   {
 *     sha, subject, author, date,
 *     changedFiles: [{ path, changeKind }],
 *     gate: <full LayerImpactResult JSON>,
 *     summary: {
 *       missingLayers,
 *       candidateCountByLayer,
 *       resolverVersion
 *     },
 *     label: null                       // operator fills this in afterwards
 *   }
 *
 * Recall  = (# commits where gate flagged ≥1 truly-relevant record) / (# commits with any truly-relevant record)
 * Precision = (# commits whose top-3 candidates included ≥1 truly-relevant record) / (# commits gate returned ≥1 candidate)
 *
 * Usage:
 *   bun .lazy-harness/scripts/host-pilot.ts --shas <sha1>,<sha2>,...
 *   bun .lazy-harness/scripts/host-pilot.ts --range origin/dev-ian~10..origin/dev-ian
 *   bun .lazy-harness/scripts/host-pilot.ts --range origin/dev-ian~10..origin/dev-ian --max 5
 *
 * Exit 0 unless usage error.
 */

import { execFileSync } from 'node:child_process'
import { existsSync, mkdirSync, writeFileSync } from 'node:fs'
import path from 'node:path'
import { runLayerImpactGate } from './layer-impact-gate'

type ChangeKind = 'added' | 'modified' | 'deleted' | 'renamed'

interface ChangedFile {
  path: string
  changeKind: ChangeKind
}

interface CommitMeta {
  sha: string
  subject: string
  author: string
  date: string
}

function gitShow(args: string[]): string {
  return execFileSync('git', args, { encoding: 'utf8' }).trim()
}

function listCommits(opts: { shas?: string[]; range?: string; max?: number }): string[] {
  if (opts.shas && opts.shas.length > 0) {
    return opts.shas
  }
  if (opts.range) {
    const out = gitShow(['rev-list', '--no-merges', opts.range])
    const all = out.split('\n').filter(Boolean)
    return opts.max ? all.slice(0, opts.max) : all
  }
  throw new Error('host-pilot: provide --shas or --range')
}

function getCommitMeta(sha: string): CommitMeta {
  const fmt = '%H%x09%s%x09%an%x09%aI'
  const line = gitShow(['log', '-1', '--format=' + fmt, sha])
  const [fullSha, subject, author, date] = line.split('\t')
  return { sha: fullSha, subject, author, date }
}

function getChangedFiles(sha: string): ChangedFile[] {
  // --name-status returns one line per file: e.g. "M\tpath", "A\tpath",
  // "D\tpath", "R100\told\tnew". We only need the destination path.
  const out = gitShow(['show', '--no-renames', '--name-status', '--format=', sha])
  const files: ChangedFile[] = []
  for (const line of out.split('\n').filter(Boolean)) {
    const parts = line.split('\t')
    if (parts.length < 2) continue
    const status = parts[0]
    const dest = parts[parts.length - 1]
    let changeKind: ChangeKind = 'modified'
    if (status.startsWith('A')) changeKind = 'added'
    else if (status.startsWith('D')) changeKind = 'deleted'
    else if (status.startsWith('R')) changeKind = 'renamed'
    else if (status.startsWith('M')) changeKind = 'modified'
    files.push({ path: dest, changeKind })
  }
  return files
}

interface CliOptions {
  shas: string[]
  range: string | null
  max: number | null
  outPath: string
  verbose: boolean
}

function parseCli(argv: string[]): CliOptions {
  const opts: CliOptions = {
    shas: [],
    range: null,
    max: null,
    outPath: '.lazy-harness/retrospective/host-pilot-N2.jsonl',
    verbose: false
  }
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i]
    if (a === '--shas' && argv[i + 1]) opts.shas = argv[++i].split(',').filter(Boolean)
    else if (a === '--range' && argv[i + 1]) opts.range = argv[++i]
    else if (a === '--max' && argv[i + 1]) opts.max = Number(argv[++i])
    else if (a === '--out' && argv[i + 1]) opts.outPath = argv[++i]
    else if (a === '--verbose' || a === '-v') opts.verbose = true
  }
  return opts
}

function main(): void {
  const opts = parseCli(process.argv.slice(2))
  const shas = listCommits({ shas: opts.shas, range: opts.range ?? undefined, max: opts.max ?? undefined })
  if (shas.length === 0) {
    console.error('host-pilot: no commits selected')
    process.exit(1)
  }
  const dir = path.dirname(opts.outPath)
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true })
  const records: any[] = []
  for (const sha of shas) {
    const meta = getCommitMeta(sha)
    const files = getChangedFiles(sha)
    if (files.length === 0) {
      if (opts.verbose) console.error(`[skip] ${sha.slice(0, 8)} ${meta.subject} (no files)`)
      continue
    }
    const result = runLayerImpactGate({
      files: files.map((f) => ({ path: f.path, changeKind: f.changeKind })),
      from: null,
      to: null,
      source: 'manual',
      appendValidation: false,
      format: 'json',
      strict: false,
      noResolver: false
    })
    const candidateCountByLayer: Record<string, number> = {}
    for (const [layer, entry] of Object.entries(result.layerImpact)) {
      candidateCountByLayer[layer] = (entry as any).candidateRecords.length
    }
    const record = {
      sha: meta.sha,
      subject: meta.subject,
      author: meta.author,
      date: meta.date,
      changedFiles: files,
      gate: result,
      summary: {
        missingLayers: result.missingLayers,
        candidateCountByLayer,
        resolverVersion: result.resolverVersion,
        productionFileCount: files.filter((f) => /^src\//.test(f.path) && !/\.(test|spec)\./.test(f.path)).length,
        testFileCount: files.filter((f) => /\.(test|spec)\./.test(f.path)).length,
        recordFileCount: files.filter((f) => f.path.startsWith('.lazy-harness/')).length
      },
      label: null
    }
    records.push(record)
    console.error(
      `[ok] ${sha.slice(0, 8)} ${meta.subject.slice(0, 60)} ` +
        `→ missingLayers=${JSON.stringify(result.missingLayers)} ` +
        `candidates=${JSON.stringify(candidateCountByLayer)}`
    )
  }
  // Write JSONL
  const jsonl = records.map((r) => JSON.stringify(r)).join('\n') + '\n'
  writeFileSync(opts.outPath, jsonl, 'utf8')
  // Print summary table
  console.log('')
  console.log('=== host-pilot summary ===')
  console.log(`commits scanned : ${records.length}`)
  console.log(`output          : ${opts.outPath}`)
  console.log('')
  console.log('Per-commit top hits (sha · missingLayers · top candidateRecord):')
  for (const r of records) {
    const top: string[] = []
    for (const [layer, entry] of Object.entries(r.gate.layerImpact)) {
      const cands = (entry as any).candidateRecords as Array<{ recordPath: string; score: number | null }>
      if (cands.length > 0) {
        top.push(`${layer}:${cands[0].recordPath}(${cands[0].score})`)
      }
    }
    console.log(`  ${r.sha.slice(0, 8)}  ${JSON.stringify(r.summary.missingLayers)}  ${top.slice(0, 2).join(' | ')}`)
  }
  console.log('')
  console.log('Next: open the JSONL, fill `label` for each entry with one of:')
  console.log('  true-positive   — gate output matched what should have been updated')
  console.log('  false-positive  — gate flagged something that didn\'t actually need updating')
  console.log('  false-negative  — gate missed a record that should have been flagged')
  console.log('  mixed           — partial credit (record per layer in label.byLayer)')
  console.log('  n/a             — no truly-relevant records (gate output ignored)')
}

main()
