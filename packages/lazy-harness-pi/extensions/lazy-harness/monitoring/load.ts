import type { ExtensionAPI } from '@earendil-works/pi-coding-agent'
import { readMonitoringAttachConfig } from './config.ts'

export const MONITORING_INSTALL_HINT = 'From the lazy-harness source checkout run: git submodule update --init --recursive vendor/lazy-harness-monitoring; bun install --frozen-lockfile; (cd vendor/lazy-harness-monitoring && bun install --frozen-lockfile). Then lazy pi install and /reload.'
type Module = typeof import('./index.ts')
type Loader = () => Promise<Pick<Module, 'installMonitoringPhase1'>>
/** No runtime vendor imports on the off path. Import failures are advisory, never a hook denial. */
export function installOptionalMonitoring(pi: ExtensionAPI, root: string, load: Loader = () => import('./index.ts')) {
  let config: ReturnType<typeof readMonitoringAttachConfig>
  try { config = readMonitoringAttachConfig(root) } catch { return }
  if (config.references.stage !== 'observe') return
  let reason = 'awaiting_session_start', notified = false
  let command: { handler: (args: string, ctx: any) => unknown } | undefined
  pi.registerCommand('monitoring', { description: 'Read-only monitoring status (no model calls)', handler: async (args, ctx) => {
    if (command) { await command.handler(args, ctx); return }
    if (args.trim() && args.trim() !== 'status') { ctx.ui.notify('Usage: /monitoring status', 'info'); return }
    ctx.ui.notify(JSON.stringify({ attached: false, stage: 'off', reason, installHint: MONITORING_INSTALL_HINT }, null, 2), 'info')
  } })
  let started = false
  const starts: Array<(event: any, ctx: any) => unknown> = []
  pi.on('session_start', async (event, ctx) => {
    if (started) {
      try { for (const start of starts) await start(event, ctx) } catch { /* advisory only */ }
      return
    }
    started = true
    // Preserve the real initiating event: the module registers synchronously after import,
    // but Pi already took its session_start handler snapshot. All later events use Pi normally.
    const scoped = new Proxy(pi, { get(target, key) {
      if (key === 'on') return (name: string, handler: any) => {
        if (name === 'session_start') { starts.push(handler); return }
        return (target.on as any)(name, handler)
      }
      if (key === 'registerCommand') return (name: string, spec: any) => {
        if (name === 'monitoring') command = spec
        else target.registerCommand(name, spec)
      }
      const value = Reflect.get(target, key)
      return typeof value === 'function' ? value.bind(target) : value
    } })
    try {
      let module: Pick<Module, 'installMonitoringPhase1'>
      try { module = await load() } catch { reason = 'monitoring_module_unavailable'; return }
      module.installMonitoringPhase1(scoped, root)
      for (const start of starts) await start(event, ctx)
      // The bootstrap itself forwards subsequent starts; never mutate Pi's current handler list.
      reason = 'attached'
    } catch { command = undefined; reason = 'monitoring_start_failed' }
    finally {
      if (reason !== 'attached' && !notified) {
        notified = true
        try { ctx.ui.notify(`Monitoring off: ${reason}. ${MONITORING_INSTALL_HINT}`, 'warning') } catch { /* UI is optional; never block */ }
      }
    }
  })
}
