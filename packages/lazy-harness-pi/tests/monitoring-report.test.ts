import { test, expect } from 'bun:test'
import { mkdirSync, mkdtempSync, readFileSync, rmSync, statSync, symlinkSync, writeFileSync, realpathSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { projectConfig, projectObserve, projectStatus, privacy, summarize } from '../../../.lazy-harness/scripts/monitoring-report-data.ts'
import { assertOutsideGit, observeDirectory, writePrivate } from '../../../.lazy-harness/scripts/monitoring-private-state.ts'
import { collectReport, monitoringReport, parseArgs, type Runner } from '../../../.lazy-harness/scripts/monitoring-report.ts'
import { notifyMonitoringStatus } from '../extensions/lazy-harness/monitoring/status-save.ts'
import { installOptionalMonitoring } from '../extensions/lazy-harness/monitoring/load.ts'

const row = { schema: 'lazy-harness-observe/v1', time: '2026-11-14T12:00:00.000Z', outcome: 'judged', decisionMode: 'skip', modelCalls: 1, reportedUsd: .001, latencyMs: 100, selectedDocuments: [{ id: 'synthetic', version: 'abc', body: 'NEVER INCLUDE' }], compaction: { kept: 1, withinBudget: true, body: 'NEVER INCLUDE' }, budgetRemaining: { calls: 0, usd: 0, tokens: 0, body: 'NEVER INCLUDE' }, conversation: 'NEVER INCLUDE' }
const fixture = () => realpathSync(mkdtempSync(join(tmpdir(), 'lh-report-')))
const fake: Runner = (cmd, args) => ({ ok: cmd !== 'pi', stdout: cmd === 'git' ? args[0] === 'rev-parse' ? '983796570cb5b30ddc181d1ad5c7458fc657c9d9' : args[0] === 'status' ? '' : ' 659cdc782bef43fd77a79bbc5e77a16ad61d22ab vendor/lazy-harness-monitoring' : cmd === 'bun' ? '1.3.14' : 'v24.0.0' })
test('v1 nested allowlist drops extras and unknown schemas; status also reprojects', () => {
  expect(JSON.stringify(projectObserve(row))).not.toContain('NEVER INCLUDE')
  expect(projectObserve({ ...row, schema: 'future' })).toBeNull()
  expect(JSON.stringify(projectStatus({ conversation: 'NEVER INCLUDE', budget: { used: { calls: 1, prompt: 'NEVER INCLUDE' } }, lastOutcomes: [row] }))).not.toContain('NEVER INCLUDE')
})
test('config projection exposes only permitted fields and numeric budget', () => {
  expect(projectConfig({ references: { stage: 'observe', secret: 'NO' }, catalog: [{ id: 'x', path: '.lazy-harness/spec/x.md', body: 'NO' }], readFormat: 'unknown', observeLog: '/private', apiKey: 'NO', budget: { maxCalls: 2, maxReservedUsd: .01, timeoutMs: 'secret', other: 9 } })).toEqual({ stage: 'observe', catalog: [{ id: 'x', path: '.lazy-harness/spec/x.md' }], readFormat: 'unknown', budget: { maxCalls: 2, maxReservedUsd: .01 } })
})
test('redacts home paths, strips terminal controls and refuses credential patterns without echoing', () => {
  expect(privacy('/Users/synthetic/repo /Users/synthetic/a\u001b', '/Users/synthetic')).toBe('~/repo ~/a')
  for (const credential of ['sk-test', 'ghp_test', 'Bearer test', 'api_key=test', '-----BEGIN RSA PRIVATE KEY-----', '-----BEGIN PRIVATE KEY-----', 'github_pat_test']) expect(() => privacy(credential, '/Users/synthetic')).toThrow('credential pattern')
})
test('private output refuses normal/linked/nested Git worktrees and symlinks', async () => {
  const dir = fixture()
  try {
    for (const linked of [false, true]) {
      const repo = join(dir, String(linked)); mkdirSync(repo)
      if (linked) writeFileSync(join(repo, '.git'), 'gitdir: /synthetic')
      else mkdirSync(join(repo, '.git'))
      await expect(writePrivate(join(repo, 'new/report.md'), 'safe')).rejects.toThrow('Git')
    }
    symlinkSync(dir, join(dir, 'link'))
    await expect(assertOutsideGit(join(dir, 'link/out.md'))).rejects.toThrow('symlink')
    await writePrivate(join(dir, 'state/out.md'), 'safe')
    expect(statSync(join(dir, 'state/out.md')).mode & 0o777).toBe(0o600)
  } finally { rmSync(dir, { recursive: true, force: true }) }
})
test('status report preserves readiness booleans but drops unknown fields', () => {
  const s = projectStatus({ attached: true, paused: false, rebuilding: true, ready: false, body: 'NEVER INCLUDE' })
  expect(s).toMatchObject({ attached: true, paused: false, rebuilding: true, ready: false })
  expect(s).not.toHaveProperty('body')
})
test('plain status unchanged; explicit --save writes same JSON 0600 in 0700 external directory; errors advisory', async () => {
  const dir = fixture(), notices: string[] = [], ui = { notify: (s: string) => { notices.push(s) } }, status = { attached: false, stage: 'observe', reason: 'synthetic' }
  try {
    await notifyMonitoringStatus('status', ui, join(dir, 'project'), join(dir, 'state'), () => status)
    expect(notices).toEqual([JSON.stringify(status, null, 2)])
    await notifyMonitoringStatus('status --save', ui, join(dir, 'project'), join(dir, 'state'), () => status)
    const state = observeDirectory(join(dir, 'project'), join(dir, 'state')), path = join(state, 'status-latest.json')
    expect(JSON.parse(readFileSync(path, 'utf8'))).toEqual(status)
    expect(statSync(path).mode & 0o777).toBe(0o600)
    expect(statSync(state).mode & 0o777).toBe(0o700)
    expect(notices.at(-1)).toContain(path)
    mkdirSync(join(dir, 'project')); mkdirSync(join(dir, 'project/.git'))
    await notifyMonitoringStatus('status --save', ui, join(dir, 'project'), join(dir, 'project/state'), () => status)
    expect(notices.at(-1)).toContain('save failed')
  } finally { rmSync(dir, { recursive: true, force: true }) }
})
test('unavailable bootstrap status --save works without loading vendor or model', async () => {
  const dir = fixture(), commands = new Map<string, any>(), notices: string[] = []
  try {
    mkdirSync(join(dir, '.lazy-harness'))
    writeFileSync(join(dir, '.lazy-harness/monitoring-attach.json'), JSON.stringify({ references: { stage: 'observe' }, observeLog: join(dir, 'state') }))
    installOptionalMonitoring({ registerCommand: (n: string, s: any) => commands.set(n, s), on() {} } as any, dir, async () => { throw Error('must not load for status') })
    await commands.get('monitoring').handler('status --save', { ui: { notify: (s: string) => notices.push(s) } })
    const saved = join(observeDirectory(dir, join(dir, 'state')), 'status-latest.json')
    expect(JSON.parse(readFileSync(saved, 'utf8')).reason).toBe('awaiting_session_start')
  } finally { rmSync(dir, { recursive: true, force: true }) }
})
test('synthetic collector uses today/yesterday, bounded tail, stale snapshot and no gh in dry-run', async () => {
  const dir = fixture(), root = join(dir, 'project'), stateBase = join(dir, 'state'), printed: string[] = [], commands: string[] = []
  try {
    mkdirSync(join(root, '.lazy-harness'), { recursive: true })
    writeFileSync(join(root, '.lazy-harness/monitoring-attach.json'), JSON.stringify({ references: { stage: 'observe' }, catalog: [], observeLog: stateBase }))
    const state = observeDirectory(root, stateBase); mkdirSync(state, { recursive: true })
    writeFileSync(join(state, '2026-11-13.jsonl'), JSON.stringify({ ...row, outcome: 'skipped', modelCalls: 0 }) + '\n')
    writeFileSync(join(state, '2026-11-14.jsonl'), JSON.stringify(row) + '\n')
    writeFileSync(join(state, '2026-11-12.jsonl'), JSON.stringify({ ...row, outcome: 'failed' }) + '\n')
    writeFileSync(join(state, 'status-latest.json'), JSON.stringify({ stage: 'observe', attached: true, body: 'NEVER INCLUDE', log: { path: '/Users/synthetic/state/file' } }))
    const runner: Runner = (cmd, args, cwd) => { commands.push(cmd); if (cmd === 'gh') throw Error('no gh permitted'); return fake(cmd, args, cwd) }
    await monitoringReport(['report', '--issue', '--dry-run', '--lines', '2'], { root, runner, print: s => printed.push(s), now: Date.parse('2026-11-14T12:00:00Z'), home: '/Users/synthetic', host: 'synthetic-mac', os: 'darwin/arm64' })
    const result = printed.join('\n')
    expect(commands).not.toContain('gh'); expect(result).toContain('GitHub target: lazy-dinosaur/lazy-harness')
    expect(result).toContain('"issue","create"'); expect(result).toContain('Snapshot age:'); expect(result).toContain('~/state/file')
    expect(result).toContain('Summary (2 projected rows'); expect(result).not.toContain('NEVER INCLUDE'); expect(result).toContain('unavailable')
    const one = await collectReport(root, 1, { runner, now: Date.parse('2026-11-14T12:00:00Z') })
    expect(one.report).toContain('Summary (1 projected rows')
    // The optional synthetic sample is written only outside Git, never committed.
    if (process.env.LH_SYNTHETIC_REPORT_OUT) await writePrivate(process.env.LH_SYNTHETIC_REPORT_OUT, printed[0])
  } finally { rmSync(dir, { recursive: true, force: true }) }
})
test('summary nearest-rank percentiles and reported cost unknowns', () => {
  const s = summarize([{ outcome: 'judged', decisionMode: 'skip', modelCalls: 1, reportedUsd: .1, latencyMs: 10 }, { outcome: 'skipped', modelCalls: 0, reportedUsd: null, latencyMs: 100 }])
  expect([s.calls, s.usd, s.usdMissing, s.p50, s.p95]).toEqual([1, .1, 1, 10, 100])
})
test('strict CLI validation', () => {
  for (const a of [['report', '--lines', '-1'], ['report', '--lines', '0'], ['report', '--lines', '1001'], ['report', '--repo', 'bad'], ['report', '--out'], ['oops'], ['report', '--unknown']]) expect(() => parseArgs(a)).toThrow()
})
