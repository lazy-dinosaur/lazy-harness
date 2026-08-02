#!/usr/bin/env bun

import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import {
  accessSync,
  constants,
  copyFileSync,
  existsSync,
  lstatSync,
  mkdirSync,
  readFileSync,
  readlinkSync,
  realpathSync,
  renameSync,
  rmSync,
  symlinkSync,
  writeFileSync,
} from 'node:fs';
import { homedir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import {
  canonicalRoot,
  isTrustedRoot,
  jcodeHome,
  loadTrustRegistry,
  relativeJcodeHome,
  trustRegistryPath,
  updateTrustedRoot,
  writeTrustRegistry,
} from './jcode-trust';
import {
  inspectLocalPromptTransport,
  updateLocalPromptTransport,
  type LocalPromptTransportResult,
} from './jcode-local-config';
type Format = 'md' | 'json';
type Action =
  | 'install'
  | 'remove'
  | 'doctor'
  | 'smoke'
  | 'trust'
  | 'untrust'
  | 'trusted-roots'
  | 'launcher-status'
  | 'promote-launcher'
  | 'rollback-launcher';
type Options = {
  action: Action;
  config?: string;
  target?: string;
  launcher?: string;
  adapterLazy?: string;
  dryRun: boolean;
  format: Format;
};

const HOOKS = {
  before_model: 'before-model',
  turn_followup: 'turn-followup',
  turn_start: 'turn-start',
  pre_tool: 'pre-tool',
  post_tool: 'post-tool',
  turn_end: 'turn-end',
  session_start: 'session-start',
  session_end: 'session-end',
} as const;

type HookKey = keyof typeof HOOKS;

function usage(exitCode = 0): never {
  const out = exitCode === 0 ? console.log : console.error;
  out(`Usage: lazy jcode <command> [options]

Commands:
  install [--target=DIR] [--adapter-lazy=PATH] [--dry-run] [--format=md|json] [--config=PATH]
  remove  [--target=DIR] [--dry-run] [--format=md|json] [--config=PATH]
  doctor  [--target=DIR] [--adapter-lazy=PATH] [--format=md|json] [--config=PATH]
  smoke   [--dry-run] [--format=md|json]
  trust   [--target=DIR] [--dry-run] [--format=md|json]
  untrust [--target=DIR] [--dry-run] [--format=md|json]
  trusted-roots [--format=md|json]
  launcher-status [--launcher=PATH] [--format=md|json]
  promote-launcher [--launcher=PATH] [--dry-run] [--format=md|json]
  rollback-launcher [--launcher=PATH] [--dry-run] [--format=md|json]

Managed hooks execute project lifecycle scripts only for canonical roots in the
user-owned trusted-roots registry; all other projects silently no-op.`);
  process.exit(exitCode);
  throw new Error('unreachable');
}

function optionValue(argv: string[], index: number, flag: string): [string, number] {
  const current = argv[index];
  const prefix = `${flag}=`;
  if (current.startsWith(prefix)) return [current.slice(prefix.length), index];
  const next = argv[index + 1];
  if (!next || next.startsWith('-')) usage(2);
  return [next, index + 1];
}

function parseOptions(argv: string[]): Options {
  const action = argv[0] as Action | undefined;
  const actions: Action[] = [
    'install',
    'remove',
    'doctor',
    'smoke',
    'trust',
    'untrust',
    'trusted-roots',
    'launcher-status',
    'promote-launcher',
    'rollback-launcher',
  ];
  if (!action || !actions.includes(action)) usage(2);
  const options: Options = { action, dryRun: false, format: 'md' };
  for (let index = 1; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === '--dry-run') {
      options.dryRun = true;
    } else if (arg === '--format' || arg.startsWith('--format=')) {
      const [raw, consumed] = optionValue(argv, index, '--format');
      if (raw !== 'md' && raw !== 'json') usage(2);
      options.format = raw;
      index = consumed;
    } else if (arg === '--config' || arg.startsWith('--config=')) {
      const [raw, consumed] = optionValue(argv, index, '--config');
      options.config = resolve(raw);
      index = consumed;
    } else if (arg === '--target' || arg.startsWith('--target=')) {
      const [raw, consumed] = optionValue(argv, index, '--target');
      options.target = resolve(raw);
      index = consumed;
    } else if (arg === '--launcher' || arg.startsWith('--launcher=')) {
      const [raw, consumed] = optionValue(argv, index, '--launcher');
      options.launcher = resolve(raw);
      index = consumed;
    } else if (arg === '--adapter-lazy' || arg.startsWith('--adapter-lazy=')) {
      const [raw, consumed] = optionValue(argv, index, '--adapter-lazy');
      options.adapterLazy = resolve(raw);
      index = consumed;
    } else if (arg === '-h' || arg === '--help' || arg === 'help') {
      usage(0);
    } else {
      usage(2);
    }
  }
  return options;
}

function defaultConfigPath(): string {
  return join(dirname(trustRegistryPath()), 'config.toml');
}

function defaultTarget(): string {
  return resolve(process.env.LAZY_INVOCATION_CWD?.trim() || process.cwd());
}

function sourceLazyPath(): string {
  return resolve(import.meta.dir, '..', 'bin', 'lazy');
}

function selectedLazyPath(options: Options): string {
  const path = options.adapterLazy ?? sourceLazyPath();
  if (!existsSync(path)) throw new Error(`Jcode adapter lazy entrypoint does not exist: ${path}`);
  return path;
}

function tomlString(value: string): string {
  return JSON.stringify(value);
}

function shellQuote(value: string): string {
  return `'${value.replace(/'/g, `'"'"'`)}'`;
}

function managedCommands(lazyPath = sourceLazyPath()): Record<HookKey, string> {
  return Object.fromEntries(
    Object.entries(HOOKS).map(([key, event]) => [key, `${shellQuote(lazyPath)} jcode hook ${event}`]),
  ) as Record<HookKey, string>;
}

function managedLine(key: HookKey, command: string): string {
  return `${key} = ${tomlString(command)}`;
}

const MANAGED_TABLE_MARKER = '# lazy-harness managed hooks table';

function tableName(line: string): string | undefined {
  const match = line.match(/^\s*\[\s*(?:"([^"]+)"|'([^']+)'|([A-Za-z0-9_-]+))\s*\]\s*(?:#.*)?$/);
  return match?.[1] ?? match?.[2] ?? match?.[3];
}

function sectionBounds(lines: string[], section: string): { start: number; end: number } | undefined {
  const start = lines.findIndex((line) => tableName(line) === section);
  if (start < 0) return undefined;
  let end = lines.length;
  for (let index = start + 1; index < lines.length; index += 1) {
    if (/^\s*\[\[?/.test(lines[index])) {
      end = index;
      break;
    }
  }
  return { start, end };
}

function assignment(line: string): { key: string; value: string } | undefined {
  const match = line.match(
    /^\s*(?:"([^"]+)"|'([^']+)'|([A-Za-z0-9_-]+))\s*=\s*("(?:\\.|[^"\\])*"|'[^']*')\s*(?:#.*)?$/,
  );
  if (!match) return undefined;
  const key = match[1] ?? match[2] ?? match[3];
  const token = match[4];
  try {
    return { key, value: token.startsWith('"') ? JSON.parse(token) : token.slice(1, -1) };
  } catch {
    return undefined;
  }
}

function existingHookLines(lines: string[]): Map<HookKey, { index: number; line: string; value: string }> {
  const bounds = sectionBounds(lines, 'hooks');
  const found = new Map<HookKey, { index: number; line: string; value: string }>();
  if (!bounds) return found;
  for (let index = bounds.start + 1; index < bounds.end; index += 1) {
    const parsed = assignment(lines[index]);
    const key = parsed?.key as HookKey | undefined;
    if (key && key in HOOKS) found.set(key, { index, line: lines[index], value: parsed.value });
  }
  return found;
}

function tomlIsValid(content: string): { ok: boolean; error?: string } {
  const check = spawnSync(
    'python3',
    ['-c', 'import sys, tomllib; tomllib.loads(sys.stdin.read())'],
    { input: content, encoding: 'utf8', timeout: 5000 },
  );
  return check.status === 0
    ? { ok: true }
    : { ok: false, error: check.stderr.trim() || check.error?.message || 'invalid TOML' };
}

function classifyHooks(lines: string[], commands: Record<HookKey, string>) {
  const existing = existingHookLines(lines);
  const matching: HookKey[] = [];
  const missing: HookKey[] = [];
  const conflicts: Array<{ key: HookKey; line: string }> = [];
  for (const key of Object.keys(HOOKS) as HookKey[]) {
    const current = existing.get(key);
    if (!current) missing.push(key);
    else if (current.value === commands[key]) matching.push(key);
    else conflicts.push({ key, line: current.line.trim() });
  }
  return { existing, matching, missing, conflicts };
}

const MANAGED_TABLE_SEPARATOR_MARKER = '# lazy-harness managed hooks table; separator-added';

function splitToml(original: string): { eol: string; lines: string[] } {
  const eol = original.includes('\r\n') ? '\r\n' : '\n';
  return { eol, lines: original ? original.split(eol) : [] };
}

function installText(original: string, commands: Record<HookKey, string>) {
  const { eol, lines } = splitToml(original);
  const classification = classifyHooks(lines, commands);
  if (classification.conflicts.length > 0) return { text: original, changed: false, ...classification };
  if (classification.missing.length === 0) return { text: original, changed: false, ...classification };

  let bounds = sectionBounds(lines, 'hooks');
  if (!bounds) {
    const separatorAdded = lines.length > 0 && Boolean(lines[lines.length - 1].trim());
    if (separatorAdded) lines.push('');
    lines.push(separatorAdded ? MANAGED_TABLE_SEPARATOR_MARKER : MANAGED_TABLE_MARKER, '[hooks]');
    bounds = { start: lines.length - 1, end: lines.length };
  }
  const additions = classification.missing.map((key) => managedLine(key, commands[key]));
  lines.splice(bounds.end, 0, ...additions);
  return {
    text: lines.join(eol),
    changed: true,
    ...classification,
  };
}

function removeText(original: string, commands: Record<HookKey, string>) {
  const { eol, lines } = splitToml(original);
  const classification = classifyHooks(lines, commands);
  const indexes = [...classification.existing.entries()]
    .filter(([key, value]) => value.value === commands[key])
    .map(([, value]) => value.index)
    .sort((a, b) => b - a);
  for (const index of indexes) lines.splice(index, 1);

  const bounds = sectionBounds(lines, 'hooks');
  const marker = bounds ? lines[bounds.start - 1] : undefined;
  if (bounds && (marker === MANAGED_TABLE_MARKER || marker === MANAGED_TABLE_SEPARATOR_MARKER)) {
    const body = lines.slice(bounds.start + 1, bounds.end);
    if (body.every((line) => !line.trim())) {
      const removeSeparator = marker === MANAGED_TABLE_SEPARATOR_MARKER && lines[bounds.start - 2] === '';
      const start = bounds.start - (removeSeparator ? 2 : 1);
      lines.splice(start, bounds.end - start);
    } else {
      lines.splice(bounds.start - 1, 1);
    }
  }

  return {
    text: lines.join(eol),
    changed: indexes.length > 0,
    removed: indexes.length,
    ...classification,
  };
}

function backupPath(config: string): string {
  return `${config}.lazy-harness-backup-${new Date().toISOString().replace(/[:.]/g, '-')}`;
}

function atomicWrite(path: string, content: string): void {
  mkdirSync(dirname(path), { recursive: true });
  const tmp = `${path}.${process.pid}.tmp`;
  writeFileSync(tmp, content, { mode: 0o600 });
  renameSync(tmp, path);
}

function emit(value: Record<string, unknown>, format: Format): void {
  if (format === 'json') {
    console.log(JSON.stringify(value, null, 2));
    return;
  }
  console.log(`# ${String(value.title ?? 'Jcode adapter')}\n`);
  for (const [key, raw] of Object.entries(value)) {
    if (key === 'title') continue;
    if (Array.isArray(raw)) {
      console.log(`- ${key}:`);
      for (const item of raw) console.log(`  - ${typeof item === 'string' ? item : JSON.stringify(item)}`);
    } else {
      console.log(`- ${key}: ${String(raw)}`);
    }
  }
}

function readConfig(path: string): string {
  return existsSync(path) ? readFileSync(path, 'utf8') : '';
}

function targetRoot(options: Options): string {
  const root = canonicalRoot(options.target ?? defaultTarget());
  if (!existsSync(join(root, '.lazy-harness', 'bin', 'lazy'))) {
    throw new Error(`Not a lazy-harness root: ${root}`);
  }
  return root;
}

function emitFailure(title: string, details: Record<string, unknown>, format: Format, exitCode = 2): void {
  emit({ title, ok: false, ...details }, format);
  process.exitCode = exitCode;
}

function installOrRemove(options: Options): void {
  const config = options.config ?? defaultConfigPath();
  const original = readConfig(config);
  const originalValidation = tomlIsValid(original);
  if (!originalValidation.ok) {
    emitFailure('Jcode adapter TOML error', { config, error: originalValidation.error }, options.format);
    return;
  }

  let root: string | undefined;
  if (options.action === 'install' || options.target) {
    try {
      root = targetRoot(options);
    } catch (error) {
      emitFailure('Jcode adapter trust error', { error: String(error) }, options.format);
      return;
    }
  }

  let commands: Record<HookKey, string>;
  try {
    commands = managedCommands(selectedLazyPath(options));
  } catch (error) {
    emitFailure('Jcode adapter source error', { error: String(error) }, options.format);
    return;
  }
  const result = options.action === 'install' ? installText(original, commands) : removeText(original, commands);
  if (result.conflicts.length > 0 && options.action === 'install') {
    emitFailure(
      'Jcode adapter conflict',
      {
        config,
        conflicts: result.conflicts.map((conflict) => `${conflict.key}: ${conflict.line}`),
        next: 'Preserve the existing hook and choose an explicit composition policy before installing.',
      },
      options.format,
    );
    return;
  }

  const resultValidation = tomlIsValid(result.text);
  if (!resultValidation.ok) {
    emitFailure(
      'Jcode adapter TOML conflict',
      { config, error: resultValidation.error, next: 'No changes were written.' },
      options.format,
    );
    return;
  }

  let localTransport: LocalPromptTransportResult | undefined;
  if (root) {
    localTransport = updateLocalPromptTransport(root, options.action === 'install', options.dryRun);
    if (!localTransport.ok) {
      emitFailure(
        'Jcode local prompt transport error',
        {
          root,
          config: localTransport.config,
          error: localTransport.error ?? 'local prompt transport update failed',
          next: 'No global Jcode hook changes were written.',
        },
        options.format,
      );
      return;
    }
  }

  let backup: string | undefined;
  let trustChanged = false;
  const configExisted = existsSync(config);
  if (!options.dryRun) {
    let globalApplied = false;
    try {
      if (result.changed) {
        if (configExisted) {
          backup = backupPath(config);
          copyFileSync(config, backup);
        }
        atomicWrite(config, result.text);
        globalApplied = true;
      }
      if (root && options.action === 'install') {
        const update = updateTrustedRoot(root, true);
        trustChanged = update.changed;
        if (trustChanged) writeTrustRegistry(update.registry);
      }
    } catch (error) {
      try {
        if (globalApplied) {
          if (configExisted) atomicWrite(config, original);
          else rmSync(config, { force: true });
        }
        if (root && localTransport?.changed) {
          updateLocalPromptTransport(root, options.action !== 'install');
        }
      } catch {
        // Doctor reports any residual drift after best-effort rollback.
      }
      emitFailure(
        'Jcode adapter transaction error',
        { config, root: root ?? 'unchanged', error: String(error) },
        options.format,
      );
      return;
    }
  } else if (root && options.action === 'install') {
    trustChanged = !isTrustedRoot(root);
  }

  emit(
    {
      title: options.action === 'install' ? 'Jcode adapter install' : 'Jcode adapter remove',
      ok: true,
      config,
      changed: result.changed,
      dryRun: options.dryRun,
      backup: backup ?? 'none',
      trustedRoot: root ?? 'unchanged',
      trustChanged,
      localPromptConfig: localTransport?.config ?? 'unchanged',
      localPromptChanged: localTransport?.changed ?? false,
      localPromptActive: localTransport?.active ?? false,
      localPromptManaged: localTransport?.managed ?? false,
      localPromptIgnored: localTransport?.ignored ?? false,
      localPromptBackup: localTransport?.backup ?? 'none',
      managedHooks: Object.keys(HOOKS),
    },
    options.format,
  );
}

function trustCommand(options: Options): void {
  let root: string;
  try {
    root = targetRoot(options);
  } catch (error) {
    emitFailure('Jcode trusted root error', { error: String(error) }, options.format);
    return;
  }
  const trust = options.action === 'trust';
  const localTransport = updateLocalPromptTransport(root, trust, options.dryRun);
  if (!localTransport.ok) {
    emitFailure(
      'Jcode local prompt transport error',
      {
        root,
        config: localTransport.config,
        error: localTransport.error ?? 'local prompt transport update failed',
      },
      options.format,
    );
    return;
  }
  const update = updateTrustedRoot(root, trust);
  if (update.changed && !options.dryRun) {
    try {
      writeTrustRegistry(update.registry);
    } catch (error) {
      if (localTransport.changed) updateLocalPromptTransport(root, !trust);
      emitFailure(
        'Jcode trust transaction error',
        { root, registry: trustRegistryPath(), error: String(error) },
        options.format,
      );
      return;
    }
  }
  emit(
    {
      title: trust ? 'Jcode root trust' : 'Jcode root untrust',
      ok: true,
      root,
      changed: update.changed,
      dryRun: options.dryRun,
      registry: trustRegistryPath(),
      localPromptConfig: localTransport.config,
      localPromptChanged: localTransport.changed,
      localPromptActive: localTransport.active,
      localPromptManaged: localTransport.managed,
      localPromptIgnored: localTransport.ignored,
      localPromptBackup: localTransport.backup ?? 'none',
    },
    options.format,
  );
}

function trustedRoots(options: Options): void {
  const registry = loadTrustRegistry();
  emit(
    {
      title: 'Jcode trusted roots',
      ok: true,
      registry: trustRegistryPath(),
      roots: registry.roots,
    },
    options.format,
  );
}

type LauncherRollbackState = {
  schemaVersion: 'lazy-jcode-launcher-rollback/v1';
  launcher: string;
  channel: string;
  prior: { kind: 'missing' } | { kind: 'symlink'; target: string };
  promotedAt: string;
};

function pathExistsIncludingBrokenSymlink(path: string): boolean {
  try {
    lstatSync(path);
    return true;
  } catch {
    return false;
  }
}

function launcherPaths(options: Options) {
  const channel = join(jcodeHome(), 'builds', 'lazy-patched', 'jcode');
  const launcher = options.launcher ?? join(homedir(), '.local', 'bin', 'jcode');
  const rollback = join(jcodeHome(), 'builds', 'lazy-patched', 'launcher-rollback.json');
  return { channel, launcher, rollback };
}

function sha256(path: string): string {
  return createHash('sha256').update(readFileSync(path)).digest('hex');
}

function validateLazyPatchedCandidate(channel: string): Record<string, unknown> {
  if (!pathExistsIncludingBrokenSymlink(channel) || !lstatSync(channel).isSymbolicLink()) {
    throw new Error(`lazy-patched channel is not a symlink: ${channel}`);
  }
  const candidate = realpathSync(channel);
  accessSync(candidate, constants.X_OK);
  const candidateDir = dirname(candidate);
  const complete = join(candidateDir, '.complete');
  const provenancePath = join(candidateDir, 'provenance.json');
  if (!existsSync(complete) || !existsSync(provenancePath)) {
    throw new Error(`lazy-patched candidate is incomplete: ${candidateDir}`);
  }
  const provenance = JSON.parse(readFileSync(provenancePath, 'utf8')) as {
    schema?: number;
    binary_sha256?: string;
    version_json?: { git_hash?: string; version?: string };
  };
  if (provenance.schema !== 1 || !provenance.binary_sha256 || !provenance.version_json?.git_hash) {
    throw new Error(`invalid lazy-patched provenance: ${provenancePath}`);
  }
  const binarySha256 = sha256(candidate);
  if (binarySha256 !== provenance.binary_sha256) {
    throw new Error(`lazy-patched binary digest mismatch: ${candidate}`);
  }
  const versionResult = spawnSync(candidate, ['version', '--json'], { encoding: 'utf8', timeout: 10_000 });
  if (versionResult.status !== 0) {
    throw new Error(`lazy-patched version check failed: ${versionResult.stderr.trim()}`);
  }
  const version = JSON.parse(versionResult.stdout) as { git_hash?: string; version?: string };
  if (version.git_hash !== provenance.version_json.git_hash) {
    throw new Error(`lazy-patched version/provenance mismatch: ${version.git_hash ?? 'unknown'}`);
  }
  return { candidate, complete, provenance: provenancePath, binarySha256, version };
}

function capturePriorLauncher(launcher: string): LauncherRollbackState['prior'] {
  if (!pathExistsIncludingBrokenSymlink(launcher)) return { kind: 'missing' };
  const stat = lstatSync(launcher);
  if (!stat.isSymbolicLink()) {
    throw new Error(`normal launcher is not a symlink; refusing replacement: ${launcher}`);
  }
  return { kind: 'symlink', target: readlinkSync(launcher) };
}

function launcherMatchesPrior(launcher: string, prior: LauncherRollbackState['prior']): boolean {
  if (prior.kind === 'missing') return !pathExistsIncludingBrokenSymlink(launcher);
  return (
    pathExistsIncludingBrokenSymlink(launcher) &&
    lstatSync(launcher).isSymbolicLink() &&
    readlinkSync(launcher) === prior.target
  );
}

function atomicSymlink(target: string, path: string): void {
  mkdirSync(dirname(path), { recursive: true });
  const tmp = `${path}.${process.pid}.tmp`;
  rmSync(tmp, { force: true });
  symlinkSync(target, tmp);
  renameSync(tmp, path);
}

function writeRollbackState(path: string, state: LauncherRollbackState): void {
  mkdirSync(dirname(path), { recursive: true });
  const tmp = `${path}.${process.pid}.tmp`;
  writeFileSync(tmp, `${JSON.stringify(state, null, 2)}\n`, { mode: 0o600 });
  renameSync(tmp, path);
}

function readRollbackState(path: string): LauncherRollbackState | undefined {
  if (!existsSync(path)) return undefined;
  const parsed = JSON.parse(readFileSync(path, 'utf8')) as Partial<LauncherRollbackState>;
  if (
    parsed.schemaVersion !== 'lazy-jcode-launcher-rollback/v1' ||
    typeof parsed.launcher !== 'string' ||
    typeof parsed.channel !== 'string' ||
    !parsed.prior ||
    (parsed.prior.kind !== 'missing' && (parsed.prior.kind !== 'symlink' || typeof parsed.prior.target !== 'string'))
  ) {
    throw new Error(`invalid launcher rollback state: ${path}`);
  }
  return parsed as LauncherRollbackState;
}

function launcherStatus(options: Options): void {
  const paths = launcherPaths(options);
  let candidate: Record<string, unknown> | undefined;
  let candidateError: string | undefined;
  try {
    candidate = validateLazyPatchedCandidate(paths.channel);
  } catch (error) {
    candidateError = String(error);
  }
  const launcherKind = pathExistsIncludingBrokenSymlink(paths.launcher)
    ? lstatSync(paths.launcher).isSymbolicLink()
      ? 'symlink'
      : 'other'
    : 'missing';
  const launcherTarget = launcherKind === 'symlink' ? readlinkSync(paths.launcher) : undefined;
  let promoted = false;
  try {
    promoted = launcherKind === 'symlink' && realpathSync(paths.launcher) === realpathSync(paths.channel);
  } catch {
    promoted = false;
  }
  emit(
    {
      title: 'Jcode lazy-patched launcher status',
      ok: candidate !== undefined,
      ...paths,
      launcherKind,
      launcherTarget: launcherTarget ?? 'none',
      promoted,
      rollbackAvailable: existsSync(paths.rollback),
      candidate: candidate ?? 'invalid',
      candidateError: candidateError ?? 'none',
    },
    options.format,
  );
  if (!candidate) process.exitCode = 1;
}

function promoteLauncher(options: Options): void {
  const paths = launcherPaths(options);
  let candidate: Record<string, unknown>;
  try {
    candidate = validateLazyPatchedCandidate(paths.channel);
  } catch (error) {
    emitFailure('Jcode launcher promotion error', { ...paths, error: String(error) }, options.format);
    return;
  }
  let alreadyPromoted = false;
  try {
    alreadyPromoted = pathExistsIncludingBrokenSymlink(paths.launcher) && realpathSync(paths.launcher) === realpathSync(paths.channel);
  } catch {
    alreadyPromoted = false;
  }
  if (alreadyPromoted) {
    if (!existsSync(paths.rollback)) {
      emitFailure(
        'Jcode launcher promotion conflict',
        { ...paths, error: 'launcher already targets lazy-patched channel but no rollback state exists' },
        options.format,
      );
      return;
    }
    emit(
      {
        title: 'Jcode launcher promotion',
        ok: true,
        changed: false,
        dryRun: options.dryRun,
        ...paths,
        rollbackAvailable: existsSync(paths.rollback),
        candidate,
      },
      options.format,
    );
    return;
  }
  if (existsSync(paths.rollback)) {
    try {
      const stale = readRollbackState(paths.rollback);
      if (!stale || stale.launcher !== paths.launcher || stale.channel !== paths.channel || !launcherMatchesPrior(paths.launcher, stale.prior)) {
        throw new Error('rollback state already exists while launcher is not in its recorded prior state');
      }
      if (!options.dryRun) rmSync(paths.rollback, { force: true });
    } catch (error) {
      emitFailure('Jcode launcher promotion conflict', { ...paths, error: String(error) }, options.format);
      return;
    }
  }
  let prior: LauncherRollbackState['prior'];
  try {
    prior = capturePriorLauncher(paths.launcher);
  } catch (error) {
    emitFailure('Jcode launcher promotion error', { ...paths, error: String(error) }, options.format);
    return;
  }
  const state: LauncherRollbackState = {
    schemaVersion: 'lazy-jcode-launcher-rollback/v1',
    launcher: paths.launcher,
    channel: paths.channel,
    prior,
    promotedAt: new Date().toISOString(),
  };
  if (!options.dryRun) {
    try {
      writeRollbackState(paths.rollback, state);
      atomicSymlink(paths.channel, paths.launcher);
      if (realpathSync(paths.launcher) !== realpathSync(paths.channel)) throw new Error('launcher verification failed');
      const verifiedCandidate = validateLazyPatchedCandidate(paths.channel);
      if (verifiedCandidate.candidate !== candidate.candidate) throw new Error('lazy-patched channel changed during promotion');
    } catch (error) {
      try {
        if (prior.kind === 'symlink') atomicSymlink(prior.target, paths.launcher);
        else rmSync(paths.launcher, { force: true });
        rmSync(paths.rollback, { force: true });
      } catch {
        // Status/doctor will expose residual drift.
      }
      emitFailure('Jcode launcher promotion error', { ...paths, error: String(error) }, options.format);
      return;
    }
  }
  emit(
    {
      title: 'Jcode launcher promotion',
      ok: true,
      changed: true,
      dryRun: options.dryRun,
      ...paths,
      prior,
      candidate,
    },
    options.format,
  );
}

function rollbackLauncher(options: Options): void {
  const paths = launcherPaths(options);
  let state: LauncherRollbackState | undefined;
  try {
    state = readRollbackState(paths.rollback);
  } catch (error) {
    emitFailure('Jcode launcher rollback error', { ...paths, error: String(error) }, options.format);
    return;
  }
  if (!state) {
    emitFailure('Jcode launcher rollback error', { ...paths, error: 'no rollback state exists' }, options.format);
    return;
  }
  if (state.launcher !== paths.launcher || state.channel !== paths.channel) {
    emitFailure('Jcode launcher rollback error', { ...paths, error: 'rollback state path mismatch' }, options.format);
    return;
  }
  let currentlyPromoted = false;
  try {
    currentlyPromoted = realpathSync(paths.launcher) === realpathSync(paths.channel);
  } catch {
    currentlyPromoted = false;
  }
  if (!currentlyPromoted) {
    const priorAlreadyRestored = launcherMatchesPrior(paths.launcher, state.prior);
    if (priorAlreadyRestored) {
      if (!options.dryRun) rmSync(paths.rollback, { force: true });
      emit(
        {
          title: 'Jcode launcher rollback',
          ok: true,
          changed: false,
          dryRun: options.dryRun,
          ...paths,
          restored: state.prior,
          recoveredStaleState: true,
        },
        options.format,
      );
      return;
    }
    emitFailure(
      'Jcode launcher rollback conflict',
      { ...paths, error: 'launcher no longer targets the recorded lazy-patched channel' },
      options.format,
    );
    return;
  }
  if (!options.dryRun) {
    try {
      if (state.prior.kind === 'symlink') atomicSymlink(state.prior.target, paths.launcher);
      else rmSync(paths.launcher, { force: true });
      rmSync(paths.rollback, { force: true });
    } catch (error) {
      emitFailure('Jcode launcher rollback error', { ...paths, error: String(error) }, options.format);
      return;
    }
  }
  emit(
    {
      title: 'Jcode launcher rollback',
      ok: true,
      changed: true,
      dryRun: options.dryRun,
      ...paths,
      restored: state.prior,
    },
    options.format,
  );
}

function jcodeVersion(): { available: boolean; version?: string; error?: string } {
  const result = spawnSync('jcode', ['version', '--json'], { encoding: 'utf8', timeout: 10_000 });
  if (result.error || result.status !== 0) {
    return { available: false, error: result.error?.message ?? result.stderr.trim() ?? 'jcode unavailable' };
  }
  try {
    const parsed = JSON.parse(result.stdout) as { version?: string };
    return { available: true, version: parsed.version ?? result.stdout.trim() };
  } catch {
    return { available: true, version: result.stdout.trim() };
  }
}

function doctor(options: Options): void {
  const config = options.config ?? defaultConfigPath();
  const original = readConfig(config);
  const validation = tomlIsValid(original);
  let commands: Record<HookKey, string>;
  try {
    commands = managedCommands(selectedLazyPath(options));
  } catch (error) {
    emitFailure('Jcode adapter source error', { error: String(error) }, options.format);
    return;
  }
  const classification = classifyHooks(original ? original.replace(/\n$/, '').split('\n') : [], commands);
  const version = jcodeVersion();
  let root: string | undefined;
  try {
    root = targetRoot(options);
  } catch {
    root = undefined;
  }
  const trusted = root ? isTrustedRoot(root) : false;
  const localTransport = root ? inspectLocalPromptTransport(root) : undefined;
  const ok =
    version.available &&
    validation.ok &&
    trusted &&
    localTransport?.ok === true &&
    localTransport.active &&
    localTransport.ignored &&
    classification.conflicts.length === 0 &&
    classification.missing.length === 0;
  emit(
    {
      title: 'Jcode adapter doctor',
      ok,
      jcodeAvailable: version.available,
      version: version.version ?? 'unknown',
      config,
      configExists: existsSync(config),
      tomlValid: validation.ok,
      tomlError: validation.error ?? 'none',
      targetRoot: root ?? 'not-a-lazy-root',
      targetTrusted: trusted,
      localPromptConfig: localTransport?.config ?? 'not-a-lazy-root',
      localPromptTomlValid: localTransport?.ok ?? false,
      localPromptActive: localTransport?.active ?? false,
      localPromptManaged: localTransport?.managed ?? false,
      localPromptIgnored: localTransport?.ignored ?? false,
      projectAgentsSuppressed: localTransport?.active ?? false,
      trustRegistry: trustRegistryPath(),
      matchingHooks: classification.matching,
      missingHooks: classification.missing,
      conflicts: classification.conflicts.map((conflict) => `${conflict.key}: ${conflict.line}`),
      knownGaps: [
        'before_model context transport installed; live provider prompt proof pending',
        'bounded turn_followup transport installed; live continuation proof pending',
        'native ask transport installed; live local/remote picker proof pending',
      ],
    },
    options.format,
  );
  if (!ok) process.exitCode = 1;
}

function smoke(options: Options): void {
  const version = jcodeVersion();
  const adapter = resolve(import.meta.dir, 'jcode-adapter.ts');
  const tempCwd = process.env.TMPDIR ?? '/tmp';
  const hook = spawnSync('bun', [adapter, 'session-start'], {
    cwd: tempCwd,
    env: {
      ...process.env,
      JCODE_HOOK_CWD: tempCwd,
      JCODE_HOOK_SESSION_ID: 'lazy-jcode-smoke',
      JCODE_HOOK_PAYLOAD: JSON.stringify({ event: 'session_start', cwd: tempCwd }),
    },
    encoding: 'utf8',
    timeout: 10_000,
  });
  const hookNoop = hook.status === 0 && !hook.stdout.trim() && !hook.stderr.trim();
  const ok = version.available && hookNoop;
  emit(
    {
      title: 'Jcode adapter smoke',
      ok,
      dryRun: options.dryRun,
      jcodeAvailable: version.available,
      version: version.version ?? 'unknown',
      nonLazyHookNoop: hookNoop,
      adapter,
    },
    options.format,
  );
  if (!ok) process.exitCode = 1;
}

function main(): void {
  const argv = process.argv.slice(2);
  if (argv.length === 0 || argv[0] === 'help' || argv[0] === '-h' || argv[0] === '--help') usage(0);
  const options = parseOptions(argv);
  const relativeHome = relativeJcodeHome();
  if (relativeHome) {
    emitFailure(
      'Jcode home error',
      { error: `JCODE_HOME must be absolute: ${relativeHome}`, next: 'No changes were written.' },
      options.format,
    );
    return;
  }
  if (options.action === 'install' || options.action === 'remove') installOrRemove(options);
  else if (options.action === 'doctor') doctor(options);
  else if (options.action === 'trust' || options.action === 'untrust') trustCommand(options);
  else if (options.action === 'trusted-roots') trustedRoots(options);
  else if (options.action === 'launcher-status') launcherStatus(options);
  else if (options.action === 'promote-launcher') promoteLauncher(options);
  else if (options.action === 'rollback-launcher') rollbackLauncher(options);
  else smoke(options);
}

main();
