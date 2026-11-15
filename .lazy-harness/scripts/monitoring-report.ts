import { spawnSync } from 'node:child_process'
import { hostname, homedir, platform, arch } from 'node:os'
import { join, resolve } from 'node:path'
import { projectConfig, projectObserve, projectStatus, privacy, summarize } from './monitoring-report-data.ts'
import { observeDirectory, assertOutsideGit, readMetadata, writePrivate } from './monitoring-private-state.ts'

export type Runner = (command: string, args: string[], cwd: string) => { ok: boolean; stdout: string }
const run: Runner = (command, args, cwd) => {
  const r = spawnSync(command, args, { cwd, encoding: 'utf8', timeout: 15000, maxBuffer: 1024 * 1024, stdio: ['ignore', 'pipe', 'pipe'] })
  return { ok: !r.error && r.status === 0, stdout: r.stdout || '' }
}
export type Options = { lines: number; out?: string; issue: boolean; repo: string; dryRun: boolean }
export function parseArgs(args: string[]): Options {
  if (args.shift() !== 'report') throw Error('Usage: lazy monitoring report [--lines N] [--out FILE] [--issue] [--repo OWNER/NAME] [--dry-run]')
  const o: Options = { lines: 20, issue: false, repo: 'lazy-dinosaur/lazy-harness', dryRun: false }
  while (args.length) {
    const key = args.shift()!
    if (key === '--issue') o.issue = true
    else if (key === '--dry-run') o.dryRun = true
    else if (['--lines', '--out', '--repo'].includes(key)) {
      const value = args.shift()
      if (!value || value.startsWith('--')) throw Error('missing option value')
      if (key === '--lines') { if (!/^\d+$/.test(value) || +value < 1 || +value > 1000) throw Error('lines must be 1..1000'); o.lines = +value }
      if (key === '--out') o.out = value
      if (key === '--repo') o.repo = value
    } else throw Error('unknown report option')
  }
  if (!/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(o.repo)) throw Error('repo must be OWNER/NAME')
  return o
}
const json = (v: unknown) => '```json\n' + JSON.stringify(v, null, 2) + '\n```'
export async function collectReport(root: string, lines = 20, options: { runner?: Runner; now?: number; home?: string; host?: string; os?: string } = {}) {
  root = resolve(root)
  if (!Number.isSafeInteger(lines) || lines < 1 || lines > 1000) throw Error('lines must be 1..1000')
  const exec = options.runner ?? run, now = options.now ?? Date.now(), home = options.home ?? homedir()
  const command = (cmd: string, args: string[]) => { const r = exec(cmd, args, root); return r.ok ? r.stdout.trim() : 'unavailable' }
  const configFile = await readMetadata(join(root, '.lazy-harness/monitoring-attach.json'), 65536)
  // Only this path and explicit observe state files are read; never auth, environment or sessions.
  let raw: any = {}, config: unknown = null, configNote = 'absent (default off)'
  if (configFile) {
    configNote = 'present'
    try { raw = JSON.parse(configFile.text); config = projectConfig(raw) } catch { configNote = 'present, invalid JSON (omitted)' }
  }
  const setting = typeof raw?.observeLog === 'string' ? raw.observeLog : undefined
  const state = observeDirectory(root, setting)
  await assertOutsideGit(join(state, 'status-latest.json'))
  const status = await readMetadata(join(state, 'status-latest.json'), 65536)
  let statusText = 'No saved snapshot. Run /monitoring status --save in Pi.'
  if (status) {
    try { statusText = `Snapshot age: ${Math.max(0, Math.floor((now - status.mtimeMs) / 1000))} seconds (saved file mtime; not live status).\n\n` + json(projectStatus(JSON.parse(status.text))) }
    catch { statusText = 'Invalid saved status JSON (omitted).' }
  }
  const candidates: unknown[] = [], notes: string[] = []
  for (const offset of [1, 0]) {
    const date = new Date(now - offset * 86400000).toISOString().slice(0, 10)
    const file = await readMetadata(join(state, date + '.jsonl'))
    if (!file) continue
    for (const line of file.text.trim().split('\n').slice(-lines)) {
      if (!line) continue
      try { candidates.push(JSON.parse(line)) } catch { notes.push('Malformed observe row omitted.') }
    }
  }
  const rows = candidates.slice(-lines).map(projectObserve).filter((r): r is NonNullable<typeof r> => r !== null)
  const summary = summarize(rows), table = ['| Dimension | Value | Count |', '| --- | --- | ---: |']
  const cell = (s: string) => s.replace(/\|/g, '\\|').replace(/[\r\n]/g, ' ')
  for (const key of ['outcome', 'mode', 'errorClass'] as const) for (const [value, count] of summary[key]) table.push(`| ${key} | ${cell(value)} | ${count} |`)
  const host = options.host ?? hostname(), date = new Date(now).toISOString().slice(0, 10)
  const head = command('git', ['rev-parse', 'HEAD'])
  const dirty = command('git', ['status', '--porcelain', '--untracked-files=normal'])
  const submodule = command('git', ['submodule', 'status', 'vendor/lazy-harness-monitoring'])
  const report = [`# Monitoring report`, '', `Host: ${host}`, `Date (UTC): ${date}`, `OS/arch: ${options.os ?? platform() + '/' + arch()}`, `lazy-harness HEAD: ${head}`, `Dirty: ${dirty === 'unavailable' ? 'unknown' : Boolean(dirty)}`, '', '## Versions / pinned module', '', json({ bun: command('bun', ['--version']), node: command('node', ['--version']), pi: command('pi', ['--version']), submodule }), '', '## Host-local config (allowlist only)', '', configNote, ...(config ? [json(config)] : []), '', '## Saved status (allowlist only)', '', statusText, '', `## Recent observe rows (today/yesterday UTC, last ${lines} lines, v1 allowlist only)`, '', json(rows), ...new Set(notes), '', `## Summary (${rows.length} projected rows; sample only, not lifetime totals)`, '', ...table, '', `Total model calls: ${summary.calls}`, `Reported USD: ${summary.usd ?? 'unknown'} (${summary.usdMissing} rows without reported cost)`, `Latency p50 / p95 (nearest-rank ms): ${summary.p50 ?? 'unknown'} / ${summary.p95 ?? 'unknown'}`, '', 'Offline collection only. No model calls. No conversation or record bodies collected.', 'Review metadata before sharing; hostnames and catalog ids/paths may identify your project.', ''].join('\n')
  return { report: privacy(report, home), title: privacy(`monitoring report: ${host} ${date}`, home) }
}
export function issueCommand(repo: string, title: string, report: string, label: boolean) {
  return ['issue', 'create', '--repo', repo, '--title', title, '--body', report, ...(label ? ['--label', 'monitoring-report'] : [])]
}
export async function monitoringReport(args: string[], deps: { root?: string; runner?: Runner; print?: (s: string) => void; now?: number; home?: string; host?: string; os?: string } = {}) {
  const o = parseArgs([...args]), root = deps.root ?? process.env.LAZY_HOST_ROOT ?? process.cwd(), exec = deps.runner ?? run, emit = deps.print ?? console.log
  const out = o.out ? resolve(process.env.LAZY_INVOCATION_CWD || process.cwd(), o.out) : undefined
  if (out) await assertOutsideGit(out)
  const collected = await collectReport(root, o.lines, deps)
  const target = privacy(`GitHub target: ${o.repo}`, deps.home ?? homedir())
  // Print the exact report and target BEFORE even a read-only GitHub lookup.
  emit(collected.report)
  if (o.issue) emit(target)
  if (out && !o.dryRun) { await writePrivate(out, collected.report); emit('Saved: ' + privacy(out, deps.home ?? homedir())) }
  if (out && o.dryRun) emit('Would save: ' + privacy(out, deps.home ?? homedir()))
  if (!o.issue) return
  if (o.dryRun) {
    emit('Dry run; no gh execution. Command argv (body is the exact report printed above):')
    emit(JSON.stringify(['gh', ...issueCommand(o.repo, collected.title, '<report printed above>', false)]))
    emit('At submission: add --label monitoring-report only if gh label list confirms it exists; otherwise omit.')
    return
  }
  const labels = exec('gh', ['label', 'list', '--repo', o.repo, '--search', 'monitoring-report', '--json', 'name', '--limit', '100'], root)
  let hasLabel = false
  try { hasLabel = labels.ok && JSON.parse(labels.stdout).some((l: any) => l.name === 'monitoring-report') } catch { /* missing label is not fatal */ }
  const result = exec('gh', issueCommand(o.repo, collected.title, collected.report, hasLabel), root)
  if (!result.ok) throw Error('gh issue create failed (details omitted for privacy); check gh auth status separately')
  emit(privacy(result.stdout.trim(), deps.home ?? homedir()))
}
if (import.meta.main) monitoringReport(process.argv.slice(2)).catch(() => { console.error('monitoring report failed: invalid options, unsafe path/input, credential pattern, or command failure. No sensitive details printed.'); process.exitCode = 1 })
