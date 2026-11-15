import type { ChildProcess } from 'node:child_process';

/** Attach immediately after spawn; ownership is the live ChildProcess handle, never a saved PID/PGID. */
export function observeOwnedChild(child: ChildProcess, options: { termMs?: number; killMs?: number } = {}) {
  const termMs = options.termMs ?? 1500;
  const killMs = options.killMs ?? 2000;
  let closed = false;
  let spawnError: Error | undefined;
  let code: number | null = null;
  const close = new Promise<void>(resolve => {
    child.once('error', (error: Error) => { spawnError = error; });
    child.once('close', (exitCode: number | null) => { code = exitCode; closed = true; resolve(); });
  });
  const live = () => !closed && child.pid !== undefined && child.exitCode === null && child.signalCode === null;
  async function within(milliseconds: number): Promise<boolean> {
    if (closed) return true;
    if (!Number.isFinite(milliseconds) || milliseconds <= 0) throw new Error('Owned child deadlines must be positive and finite');
    let timer: ReturnType<typeof setTimeout> | undefined;
    try {
      return await Promise.race([close.then(() => true), new Promise<boolean>(resolve => { timer = setTimeout(() => resolve(false), milliseconds); })]);
    } finally { clearTimeout(timer); }
  }
  let settlement: Promise<NodeJS.Signals[]> | undefined;
  return {
    get closed() { return closed; },
    async waitForClose(milliseconds: number): Promise<number | null> {
      if (!await within(milliseconds)) throw new Error('Owned child exceeded its deadline');
      if (spawnError) throw spawnError;
      return code;
    },
    settle(): Promise<NodeJS.Signals[]> {
      settlement ??= (async () => {
        const signals: NodeJS.Signals[] = [];
        if (closed) return signals;
        if (live() && child.kill('SIGTERM')) signals.push('SIGTERM');
        if (await within(termMs)) return signals;
        // child.killed does not mean exited: a TERM-ignoring owned handle can still need KILL.
        if (live() && child.kill('SIGKILL')) signals.push('SIGKILL');
        if (!await within(killMs)) throw new Error('Owned child did not physically close; fixture must be preserved');
        return signals;
      })();
      return settlement;
    },
  };
}
