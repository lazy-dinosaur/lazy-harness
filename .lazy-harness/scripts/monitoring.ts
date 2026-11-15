import { existsSync, readFileSync } from 'node:fs'
import { resolve, join } from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

/** Report remains independent of source/vendor availability. Synced hosts use their recorded source. */
export async function monitoring(args: string[], root = process.env.LAZY_HOST_ROOT || process.cwd()) {
  if (args[0] === 'report') {
    const { monitoringReport } = await import('./monitoring-report.ts')
    return monitoringReport(args, { root })
  }
  const localSource = fileURLToPath(new URL('../..', import.meta.url))
  const modulePath = 'packages/lazy-harness-pi/extensions/lazy-harness/monitoring/manage.ts'
  let source = localSource
  if (!existsSync(join(source, modulePath))) {
    try { source = JSON.parse(readFileSync(join(root, '.lazy-harness/state/synced-from-commit'), 'utf8')).sourceRoot } catch { /* clear repair hint below */ }
  }
  if (typeof source !== 'string' || !existsSync(join(source, modulePath))) throw Error('Monitoring config helper unavailable. Run lazy update / lazy pi install from the source checkout.')
  const { manageMonitoring } = await import(pathToFileURL(resolve(source, modulePath)).href)
  manageMonitoring(root, args)
}
if (import.meta.main) monitoring(process.argv.slice(2)).catch(error => { console.error(error instanceof Error ? error.message : 'Monitoring command failed'); process.exitCode = 1 })
