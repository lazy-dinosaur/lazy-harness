import { test, expect } from 'bun:test'
import { cpSync, chmodSync, existsSync, mkdtempSync, mkdirSync, readFileSync, rmSync, symlinkSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join, resolve } from 'node:path'
import { spawnSync } from 'node:child_process'
import { installOptionalMonitoring } from '../extensions/lazy-harness/monitoring/load.ts'

const root = resolve(import.meta.dir, '../../..')
const env = { ...process.env }; delete env.PI_FABRIC_LINEAGE
function harness() {
  const events = new Map<string, Function[]>(), commands = new Map<string, any>(), notices: string[] = []
  const pi: any = { on(name: string, fn: Function) { events.set(name, [...(events.get(name) ?? []), fn]) }, registerCommand(name: string, spec: any) { commands.set(name, spec) }, registerTool() {}, registerMessageRenderer() {}, registerFlag() {} }
  const ctx: any = { ui: { notify(text: string) { notices.push(text) } } }
  return { pi, events, commands, notices, ctx, async emit(name: string) { for (const fn of [...(events.get(name) ?? [])]) await fn({ type: name }, ctx) } }
}

for (const vendor of ['absent', 'empty', 'missing-dependency']) for (const stage of ['absent', 'off', 'observe']) {
  test(`extension stays loadable: vendor ${vendor}, stage ${stage}`, async () => {
    const dir = mkdtempSync(join(tmpdir(), 'lh-load-')), oldCwd = process.cwd()
    try {
      const ext = join(dir, 'packages/lazy-harness-pi/extensions')
      cpSync(join(root, 'packages/lazy-harness-pi/extensions'), ext, { recursive: true })
      symlinkSync(join(root, 'node_modules'), join(dir, 'node_modules'), 'dir')
      if (vendor !== 'absent') mkdirSync(join(dir, 'vendor/lazy-harness-monitoring'), { recursive: true })
      if (vendor === 'missing-dependency') writeFileSync(join(dir, 'vendor/lazy-harness-monitoring/composition.ts'), "import 'missing-monitoring-dependency-offline-fixture'\n")
      mkdirSync(join(dir, '.lazy-harness'), { recursive: true })
      if (stage !== 'absent') writeFileSync(join(dir, '.lazy-harness/monitoring-attach.json'), JSON.stringify({ references: { stage } }))
      const extension = await import(join(ext, 'lazy-harness/index.ts'))
      const h = harness()
      process.chdir(dir)
      extension.default(h.pi)
      process.chdir(oldCwd)
      // Core hooks register even though no vendor code or dependencies can be imported.
      for (const name of ['tool_call', 'tool_result', 'before_agent_start', 'agent_end']) expect(h.events.has(name)).toBe(true)
      if (stage === 'observe') {
        // Only the optional bootstrap callback: don't execute unrelated host hooks in this unit fixture.
        await h.events.get('session_start')![0]({ type: 'session_start' }, h.ctx)
        await h.events.get('session_start')![0]({ type: 'session_start' }, h.ctx)
        expect(h.notices).toHaveLength(1)
        expect(h.notices[0]).toContain('monitoring_module_unavailable')
        await h.commands.get('monitoring').handler('status', h.ctx)
        const status = JSON.parse(h.notices.at(-1)!)
        expect(status.reason).toBe('monitoring_module_unavailable')
        expect(status.attached).toBe(false)
        expect(status.installHint).toContain('bun install --frozen-lockfile')
      } else { expect(h.commands.has('monitoring')).toBe(false); expect(h.notices).toHaveLength(0) }
    } finally { process.chdir(oldCwd); rmSync(dir, { recursive: true, force: true }) }
  })
}
test('off never invokes even an injected loader; observe replays initiating event and forwards later events', async () => {
  const dir = mkdtempSync(join(tmpdir(), 'lh-loader-'))
  try {
    let loads = 0, starts = 0, inputs = 0
    const load = async () => { loads++; return { installMonitoringPhase1(pi: any) {
      pi.on('session_start', () => { starts++ }); pi.on('input', () => { inputs++ })
      pi.registerCommand('monitoring', { handler: async (_args: string, ctx: any) => ctx.ui.notify('healthy') })
    } } }
    const off = harness(); installOptionalMonitoring(off.pi, dir, load); expect(loads).toBe(0); expect(off.events.size).toBe(0)
    mkdirSync(join(dir, '.lazy-harness')); writeFileSync(join(dir, '.lazy-harness/monitoring-attach.json'), '{"references":{"stage":"observe"}}')
    const h = harness(); installOptionalMonitoring(h.pi, dir, load)
    await h.emit('session_start'); await h.emit('input'); await h.emit('session_start')
    await h.commands.get('monitoring').handler('status', h.ctx)
    expect([loads, starts, inputs]).toEqual([1, 2, 1]); expect(h.notices).toEqual(['healthy'])
  } finally { rmSync(dir, { recursive: true, force: true }) }
})
test('source preparation is ordered, repeatable and fails clearly without network', () => {
  const dir = mkdtempSync(join(tmpdir(), 'lh-prep-')), bin = join(dir, 'bin'), log = join(dir, 'commands')
  try {
    mkdirSync(bin); mkdirSync(join(dir, 'vendor/lazy-harness-monitoring'), { recursive: true })
    writeFileSync(join(dir, 'vendor/lazy-harness-monitoring/package.json'), '{}')
    for (const name of ['git', 'bun']) {
      const path = join(bin, name)
      writeFileSync(path, `#!/bin/bash\nprintf '%s\\n' "${name}:$PWD:$*" >> "$PREP_LOG"\nif [[ "$PREP_FAIL" == "${name}" ]]; then exit 1; fi\n`)
      chmodSync(path, 0o755)
    }
    const options = { cwd: dir, env: { ...env, PATH: `${bin}:${process.env.PATH}`, PREP_LOG: log, PREP_FAIL: '' }, encoding: 'utf8' as const }
    const args = [join(root, '.lazy-harness/scripts/install-source-deps.sh'), dir]
    expect(spawnSync('bash', args, options).status).toBe(0)
    expect(spawnSync('bash', args, options).status).toBe(0)
    const lines = readFileSync(log, 'utf8').trim().split('\n')
    expect(lines).toHaveLength(6)
    expect(lines[0]).toContain('submodule update --init --recursive vendor/lazy-harness-monitoring')
    expect(lines[1]).toBe(`bun:${dir}:install --frozen-lockfile`)
    expect(lines[2]).toBe(`bun:${dir}/vendor/lazy-harness-monitoring:install --frozen-lockfile`)
    expect(lines.slice(0, 3)).toEqual(lines.slice(3))
    const failed = spawnSync('bash', args, { ...options, env: { ...options.env, PREP_FAIL: 'git' } })
    expect(failed.status).toBe(1); expect(failed.stderr).toContain('monitoring submodule initialization')
    expect(failed.stderr).toContain('retry lazy pi install')
  } finally { rmSync(dir, { recursive: true, force: true }) }
})
test('source preparation dry-run is offline and does not create a missing source', () => {
  const dir = mkdtempSync(join(tmpdir(), 'lh-install-')), source = join(dir, 'not-cloned')
  try {
    const r = spawnSync('bash', [join(root, '.lazy-harness/scripts/install-source-deps.sh'), source, '--dry-run'], { env, encoding: 'utf8' })
    expect(r.status).toBe(0); expect(r.stdout).toContain('submodule update --init --recursive vendor/lazy-harness-monitoring')
    expect(r.stdout.match(/bun install --frozen-lockfile/g)).toHaveLength(2); expect(existsSync(source)).toBe(false)
    for (const scope of ['--global', '--local']) {
      const p = spawnSync('bun', [join(root, '.lazy-harness/scripts/pi-package.ts'), 'install', scope, '--dry-run', '--format=json'], { cwd: root, env, encoding: 'utf8' })
      expect(p.status).toBe(0)
      const result = JSON.parse(p.stdout)
      expect(result.preparation.stdout).toContain('submodule update --init --recursive')
      expect(result.result.command[1]).toBe('install')
    }
  } finally { rmSync(dir, { recursive: true, force: true }) }
})
