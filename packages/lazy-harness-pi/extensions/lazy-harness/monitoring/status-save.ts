import { join } from 'node:path'

/** Explicit save only; plain status preserves its existing JSON notification. No model access. */
export async function notifyMonitoringStatus(args: string, ui: { notify: (message: string, level: 'info' | 'warning') => void }, root: string, setting: false | string | undefined, status: () => unknown) {
  const value = args.trim()
  if (value && value !== 'status' && !/^status\s+--save$/.test(value)) { ui.notify('Usage: /monitoring status [--save]', 'info'); return }
  const json = JSON.stringify(status(), null, 2)
  ui.notify(json, 'info')
  if (value !== 'status' && /^status\s+--save$/.test(value)) {
    try {
      const { observeDirectory, writePrivate } = await import('../../../../../.lazy-harness/scripts/monitoring-private-state.ts')
      const path = join(observeDirectory(root, setting), 'status-latest.json')
      await writePrivate(path, json + '\n', true)
      ui.notify('Monitoring status saved: ' + path, 'info')
    } catch { ui.notify('Monitoring status save failed: unsafe or unavailable external state path', 'warning') }
  }
}
