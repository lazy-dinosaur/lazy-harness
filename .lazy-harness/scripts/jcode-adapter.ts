#!/usr/bin/env bun

import { spawnSync } from 'node:child_process';
import {
  existsSync,
  mkdirSync,
  readFileSync,
  realpathSync,
  renameSync,
  rmSync,
  statSync,
  writeFileSync,
} from 'node:fs';
import { createHash, randomUUID } from 'node:crypto';
import { basename, dirname, isAbsolute, join, parse, relative, resolve, sep } from 'node:path';
import { isTrustedRoot } from './jcode-trust';
type HookName =
  | 'before-model'
  | 'turn-start'
  | 'pre-tool'
  | 'post-tool'
  | 'turn-end'
  | 'session-start'
  | 'session-end';

type RecentToolCall = {
  name: string;
  args_preview: string;
  edit_target?: string;
  status: 'ok';
  timestamp: string;
};

type PendingToolCall = {
  id: string;
  name: string;
  evidencePath?: string;
  editTarget?: string;
  startedAt: number;
  epoch: number;
};

type AdapterState = {
  schemaVersion: 'jcode-adapter-state/v1';
  root: string;
  sessionHash: string;
  epoch: number;
  pending: PendingToolCall[];
  recent: RecentToolCall[];
};

const MAX_RECENT = 40;
const MAX_PENDING = 40;
const PREVIEW_LIMIT = 768;
const PENDING_MAX_AGE_MS = 60_000;
const LOCK_STALE_MS = 30_000;
const MAX_INJECT_BYTES = 24_000;
function usage(exitCode = 0): never {
  const out = exitCode === 0 ? console.log : console.error;
  out('Usage: lazy jcode hook <before-model|turn-start|pre-tool|post-tool|turn-end|session-start|session-end>');
  process.exit(exitCode);
  throw new Error('unreachable');
}

function bounded(value: unknown, limit = PREVIEW_LIMIT): string {
  const text = String(value ?? '').trim();
  return text.length <= limit ? text : `${text.slice(0, limit)}…`;
}

function parsePayload(): Record<string, unknown> {
  const raw = process.env.JCODE_HOOK_PAYLOAD ?? '';
  if (!raw.trim()) return {};
  try {
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === 'object' && !Array.isArray(parsed)
      ? (parsed as Record<string, unknown>)
      : {};
  } catch {
    return {};
  }
}

function findLazyRoot(start: string | undefined): string | undefined {
  if (!start) return undefined;
  let current = resolve(start);
  const filesystemRoot = parse(current).root;
  for (;;) {
    if (existsSync(join(current, '.lazy-harness', 'bin', 'lazy'))) return realpathSync(current);
    if (current === filesystemRoot) return undefined;
    current = dirname(current);
  }
}

function activeRoot(payload: Record<string, unknown>): string | undefined {
  const candidates = [
    process.env.JCODE_HOOK_CWD,
    typeof payload.cwd === 'string' ? payload.cwd : undefined,
  ];
  for (const candidate of candidates) {
    const root = findLazyRoot(candidate);
    if (root && isTrustedRoot(root)) return root;
  }
  return undefined;
}

function sessionId(payload: Record<string, unknown>): string {
  return bounded(process.env.JCODE_HOOK_SESSION_ID ?? payload.session_id ?? '', 256);
}

function hash(value: string): string {
  return createHash('sha256').update(value).digest('hex').slice(0, 20);
}

function statePath(root: string, session: string): string {
  const explicit = process.env.LAZY_RUNTIME_ROOT?.trim();
  let runtimeRoot: string;
  if (explicit) {
    runtimeRoot = resolve(explicit);
  } else {
    const gitDir = spawnSync('git', ['-C', root, 'rev-parse', '--absolute-git-dir'], {
      encoding: 'utf8',
      timeout: 5000,
    }).stdout.trim();
    const base = gitDir ? resolve(gitDir) : join(root, '.lazy-harness', '.gitless');
    const sessionKey = session.trim() ? `session-${hash(session)}` : 'default';
    runtimeRoot = join(base, 'lazy-harness', 'runtime', sessionKey);
  }
  return join(runtimeRoot, 'state', 'jcode-adapter.json');
}

function emptyState(root: string, session: string, epoch = 0): AdapterState {
  return {
    schemaVersion: 'jcode-adapter-state/v1',
    root,
    sessionHash: hash(session),
    epoch,
    pending: [],
    recent: [],
  };
}

function loadState(path: string, root: string, session: string): AdapterState {
  try {
    const parsed = JSON.parse(readFileSync(path, 'utf8')) as Partial<AdapterState>;
    if (
      parsed.schemaVersion === 'jcode-adapter-state/v1' &&
      parsed.root === root &&
      parsed.sessionHash === hash(session)
    ) {
      return {
        ...emptyState(root, session),
        ...parsed,
        pending: Array.isArray(parsed.pending) ? parsed.pending.slice(-MAX_PENDING) : [],
        recent: Array.isArray(parsed.recent) ? parsed.recent.slice(-MAX_RECENT) : [],
      };
    }
  } catch {
    // Corrupt or absent runtime state is recreated; canonical project data is untouched.
  }
  return emptyState(root, session);
}

function saveState(path: string, state: AdapterState): void {
  mkdirSync(dirname(path), { recursive: true, mode: 0o700 });
  const tmp = `${path}.${process.pid}.${Date.now()}.tmp`;
  writeFileSync(tmp, `${JSON.stringify(state)}\n`, { mode: 0o600 });
  renameSync(tmp, path);
}

function sleep(milliseconds: number): void {
  const buffer = new SharedArrayBuffer(4);
  Atomics.wait(new Int32Array(buffer), 0, 0, milliseconds);
}

type LockOwner = { id: string; pid: number; startedAt: number };

function readLockOwner(lock: string): LockOwner | undefined {
  try {
    const owner = JSON.parse(readFileSync(join(lock, 'owner.json'), 'utf8')) as Partial<LockOwner>;
    return typeof owner.id === 'string' &&
      typeof owner.pid === 'number' &&
      typeof owner.startedAt === 'number'
      ? (owner as LockOwner)
      : undefined;
  } catch {
    return undefined;
  }
}

function processIsAlive(pid: number): boolean {
  try {
    process.kill(pid, 0);
    return true;
  } catch {
    return false;
  }
}

function lockIsStale(lock: string, owner = readLockOwner(lock)): boolean {
  try {
    const age = Date.now() - (owner?.startedAt ?? statSync(lock).mtimeMs);
    return age > LOCK_STALE_MS && (!owner || !processIsAlive(owner.pid));
  } catch {
    return false;
  }
}

function recoverStaleLock(lock: string): boolean {
  const observed = readLockOwner(lock);
  if (!lockIsStale(lock, observed)) return false;
  const quarantine = `${lock}.stale-${randomUUID()}`;
  try {
    renameSync(lock, quarantine);
  } catch {
    return false;
  }
  const movedOwner = readLockOwner(quarantine);
  const sameOwner = observed ? movedOwner?.id === observed.id : !movedOwner;
  if (!sameOwner || !lockIsStale(quarantine, movedOwner)) {
    try {
      if (!existsSync(lock)) renameSync(quarantine, lock);
    } catch {
      // Preserve the quarantined lock rather than deleting an unverified owner.
    }
    return false;
  }
  rmSync(quarantine, { recursive: true, force: true });
  return true;
}

function tryAcquireLock(lock: string, owner: LockOwner): boolean {
  const candidate = `${lock}.candidate-${owner.id}`;
  try {
    mkdirSync(candidate);
    writeFileSync(join(candidate, 'owner.json'), `${JSON.stringify(owner)}\n`, { mode: 0o600 });
    renameSync(candidate, lock);
    return true;
  } catch {
    rmSync(candidate, { recursive: true, force: true });
    return false;
  }
}

function withOwnedLock<T>(path: string, operation: () => T): T | undefined {
  const lock = `${path}.lock`;
  mkdirSync(dirname(path), { recursive: true, mode: 0o700 });
  const owner: LockOwner = { id: randomUUID(), pid: process.pid, startedAt: Date.now() };
  let acquired = false;
  for (let attempt = 0; attempt < 50; attempt += 1) {
    if (tryAcquireLock(lock, owner)) {
      acquired = true;
      break;
    }
    recoverStaleLock(lock);
    sleep(10);
  }
  if (!acquired) return undefined;
  try {
    return operation();
  } finally {
    try {
      const current = readLockOwner(lock);
      if (current?.id === owner.id) rmSync(lock, { recursive: true, force: true });
    } catch {
      // Never remove a lock whose ownership cannot be verified.
    }
  }
}

function withState<T>(
  path: string,
  root: string,
  session: string,
  update: (state: AdapterState) => T,
): T | undefined {
  return withOwnedLock(path, () => {
    const state = loadState(path, root, session);
    const result = update(state);
    saveState(path, state);
    return result;
  });
}

function readStdin(): string {
  try {
    return readFileSync(0, 'utf8');
  } catch {
    return '';
  }
}

function parseToolInput(raw: string): Record<string, unknown> {
  try {
    const parsed = JSON.parse(raw || '{}');
    return parsed && typeof parsed === 'object' && !Array.isArray(parsed)
      ? (parsed as Record<string, unknown>)
      : {};
  } catch {
    return {};
  }
}

function firstString(input: Record<string, unknown>, keys: string[]): string | undefined {
  for (const key of keys) {
    if (typeof input[key] === 'string' && input[key].trim()) return bounded(input[key]);
  }
  return undefined;
}

function canonicalCandidatePath(root: string, candidate: string): string | undefined {
  const absolute = resolve(root, candidate);
  let probe = absolute;
  const suffix: string[] = [];
  while (!existsSync(probe)) {
    const parent = dirname(probe);
    if (parent === probe) return undefined;
    suffix.unshift(basename(probe));
    probe = parent;
  }
  try {
    return resolve(realpathSync(probe), ...suffix);
  } catch {
    return undefined;
  }
}

function rootContainedPath(root: string, input: Record<string, unknown>): string | undefined {
  const candidate = firstString(input, ['file_path', 'path', 'filePath']);
  if (!candidate || /[\u0000-\u001f\u007f]/.test(candidate) || /^[A-Za-z][A-Za-z0-9+.-]*:/.test(candidate)) {
    return undefined;
  }
  const canonical = canonicalCandidatePath(root, candidate);
  if (!canonical) return undefined;
  const fromRoot = relative(root, canonical);
  if (isAbsolute(fromRoot) || fromRoot === '..' || fromRoot.startsWith(`..${sep}`)) return undefined;
  return bounded(canonical);
}

function hookEnvPayload(
  event: string,
  root: string,
  session: string,
  extra: Record<string, unknown> = {},
): Record<string, unknown> {
  return {
    event,
    session_id: session,
    working_dir: root,
    cwd: root,
    ...extra,
  };
}

function runCanonical(root: string, relativeScript: string, payload: unknown) {
  return spawnSync(join(root, relativeScript), {
    cwd: root,
    env: { ...process.env, LAZY_HOST_ROOT: root },
    input: JSON.stringify(payload),
    encoding: 'utf8',
    timeout: 15_000,
  });
}

function denyReason(stdout: string): string | undefined {
  const text = stdout.trim();
  if (!text) return undefined;
  try {
    const parsed = JSON.parse(text) as { action?: string; reason?: unknown };
    if (parsed.action === 'deny' && typeof parsed.reason === 'string') {
      return bounded(parsed.reason, 2000);
    }
  } catch {
    // Legacy/plain deny output is still a canonical deny signal when non-empty.
  }
  return bounded(text, 2000);
}

function normalizedInjection(stdout: string): string | undefined {
  if (!stdout.trim() || Buffer.byteLength(stdout, 'utf8') > MAX_INJECT_BYTES * 2) return undefined;
  try {
    const parsed = JSON.parse(stdout) as {
      action?: unknown;
      inject?: { body?: unknown; format?: unknown };
    };
    if (parsed.action !== 'allow' || typeof parsed.inject?.body !== 'string') return undefined;
    const body = bounded(parsed.inject.body, MAX_INJECT_BYTES).trim();
    if (!body) return undefined;
    return JSON.stringify({
      action: 'allow',
      inject: { body, format: 'system_reminder' },
    });
  } catch {
    return undefined;
  }
}

function beforeModel(root: string, session: string, path: string): void {
  const state = loadState(path, root, session);
  const hasToolEvidence = state.recent.length > 0;
  const payload = hookEnvPayload('model.request.before', root, session, {
    request_kind: hasToolEvidence ? 'post_tool' : 'initial',
    recent_tool_calls: state.recent,
    message: hasToolEvidence ? '' : '[jcode before_model static transport]',
  });
  const result = runCanonical(
    root,
    hasToolEvidence
      ? '.lazy-harness/hooks/lifecycle/on-context.sh'
      : '.lazy-harness/hooks/lifecycle/on-message-received.sh',
    payload,
  );
  const injection = normalizedInjection(result.stdout ?? '');
  if (injection) console.log(injection);
}

function turnStart(root: string, session: string, path: string): void {
  withState(path, root, session, (state) => {
    state.epoch += 1;
    state.pending = [];
    state.recent = [];
  });
  runCanonical(
    root,
    '.lazy-harness/hooks/lifecycle/on-message-received.sh',
    hookEnvPayload('message.received', root, session, {
      message: '[jcode turn_start static transport]',
    }),
  );
}

function preTool(root: string, session: string, path: string): void {
  const raw = readStdin();
  const args = parseToolInput(raw);
  const name = bounded(process.env.JCODE_HOOK_TOOL_NAME ?? 'unknown-tool', 128);
  const pendingId = randomUUID();
  const state =
    withState(path, root, session, (current) => {
      current.pending.push({
        id: pendingId,
        name,
        evidencePath: rootContainedPath(root, args),
        editTarget: rootContainedPath(root, args),
        startedAt: Date.now(),
        epoch: current.epoch,
      });
      current.pending = current.pending.slice(-MAX_PENDING);
      return structuredClone(current);
    }) ?? emptyState(root, session);

  const payload = hookEnvPayload('tool.execute.before', root, session, {
    tool: { name, args },
    recent_tool_calls: state.recent,
  });
  const result = runCanonical(
    root,
    '.lazy-harness/hooks/lifecycle/on-tool-execute-before.sh',
    payload,
  );
  const reason = denyReason(result.stdout ?? '');
  if (reason) {
    try {
      withState(path, root, session, (current) => {
        current.pending = current.pending.filter((call) => call.id !== pendingId);
      });
    } catch {
      // A confirmed canonical deny must survive cleanup/state failures.
    }
    console.error(reason);
    process.exit(2);
    return;
  }
  process.exit(0);
}

function postTool(root: string, session: string, path: string): void {
  const name = bounded(process.env.JCODE_HOOK_TOOL_NAME ?? 'unknown-tool', 128);
  const status = bounded(process.env.JCODE_HOOK_STATUS ?? '', 32).toLowerCase();
  withState(path, root, session, (state) => {
    const now = Date.now();
    state.pending = state.pending.filter((call) => now - call.startedAt <= PENDING_MAX_AGE_MS);
    const matches = state.pending
      .map((call, index) => ({ call, index }))
      .filter(({ call }) => call.name === name && call.epoch === state.epoch);
    // Jcode exposes no stable call id in post_tool. Ambiguous same-tool calls are
    // all discarded rather than retained indefinitely or accepted as false proof.
    if (matches.length !== 1) {
      if (matches.length > 1) {
        const ids = new Set(matches.map(({ call }) => call.id));
        state.pending = state.pending.filter((call) => !ids.has(call.id));
      }
      return;
    }
    const [{ call, index }] = matches;
    state.pending.splice(index, 1);
    if (status !== 'ok') return;
    state.recent.push({
      name: call.name,
      args_preview: call.evidencePath ?? '',
      ...(call.editTarget ? { edit_target: call.editTarget } : {}),
      status: 'ok',
      timestamp: new Date().toISOString(),
    });
    state.recent = state.recent.slice(-MAX_RECENT);
  });
}

function turnEnd(root: string, session: string, path: string): void {
  const state = loadState(path, root, session);
  runCanonical(
    root,
    '.lazy-harness/hooks/lifecycle/on-response-completed.sh',
    hookEnvPayload('response.completed', root, session, {
      assistant_response: bounded(process.env.JCODE_HOOK_LAST_ASSISTANT_TEXT ?? '', 4000),
      last_user_message: '',
      recent_tool_calls: state.recent,
    }),
  );
  withState(path, root, session, (current) => {
    current.pending = [];
    current.recent = [];
  });
}

function main(): void {
  const [rawHook] = process.argv.slice(2) as [string | undefined];
  const supported = new Set<HookName>([
    'before-model',
    'turn-start',
    'pre-tool',
    'post-tool',
    'turn-end',
    'session-start',
    'session-end',
  ]);
  if (!rawHook || !supported.has(rawHook as HookName)) usage(2);
  const hook = rawHook as HookName;

  const payload = parsePayload();
  const root = activeRoot(payload);
  if (!root) return;
  const session = sessionId(payload);
  const path = statePath(root, session);

  try {
    switch (hook) {
      case 'before-model':
        beforeModel(root, session, path);
        break;
      case 'session-start':
        withState(path, root, session, () => undefined);
        break;
      case 'session-end':
        withOwnedLock(path, () => rmSync(path, { force: true }));
        break;
      case 'turn-start':
        turnStart(root, session, path);
        break;
      case 'pre-tool':
        preTool(root, session, path);
        break;
      case 'post-tool':
        postTool(root, session, path);
        break;
      case 'turn-end':
        turnEnd(root, session, path);
        break;
    }
  } catch {
    // Jcode hook contract is fail-open except for an explicit canonical deny.
    process.exit(0);
  }
}

main();
