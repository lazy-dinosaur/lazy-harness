import { spawnSync } from 'node:child_process';
import {
  copyFileSync,
  existsSync,
  mkdirSync,
  readFileSync,
  renameSync,
  rmSync,
  writeFileSync,
} from 'node:fs';
import { dirname, isAbsolute, join, resolve } from 'node:path';

const FILE_MARKER = '# lazy-harness managed local Jcode transport file';
const TABLE_MARKER = '# lazy-harness managed prompt transport table';
const TABLE_SEPARATOR_MARKER = '# lazy-harness managed prompt transport table; separator-added';
const KEY_MARKER = '# lazy-harness managed prompt transport key';
const EXCLUDE_MARKER = '# lazy-harness managed local Jcode config';
const EXCLUDE_ENTRY = '.jcode/config.local.toml';

export type LocalPromptTransportResult = {
  ok: boolean;
  root: string;
  config: string;
  changed: boolean;
  dryRun: boolean;
  active: boolean;
  managed: boolean;
  ignored: boolean;
  backup?: string;
  error?: string;
};

type TextPlan = {
  text: string;
  changed: boolean;
  active: boolean;
  managed: boolean;
  removeFile: boolean;
  error?: string;
};

function splitToml(original: string): { eol: string; lines: string[] } {
  const eol = original.includes('\r\n') ? '\r\n' : '\n';
  return { eol, lines: original ? original.split(eol) : [] };
}

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

function booleanAssignment(line: string): { key: string; value: boolean } | undefined {
  const match = line.match(
    /^\s*(?:"([^"]+)"|'([^']+)'|([A-Za-z0-9_-]+))\s*=\s*(true|false)\s*(?:#.*)?$/,
  );
  if (!match) return undefined;
  return { key: match[1] ?? match[2] ?? match[3], value: match[4] === 'true' };
}

function promptKey(lines: string[]): { index: number; value: boolean; managed: boolean } | undefined {
  const bounds = sectionBounds(lines, 'prompt');
  if (!bounds) return undefined;
  for (let index = bounds.start + 1; index < bounds.end; index += 1) {
    const parsed = booleanAssignment(lines[index]);
    if (parsed?.key === 'ignore_project_agents') {
      return { index, value: parsed.value, managed: lines[index - 1] === KEY_MARKER };
    }
  }
  return undefined;
}

function installText(original: string): TextPlan {
  const { eol, lines } = splitToml(original);
  const existing = promptKey(lines);
  if (existing) {
    if (!existing.value) {
      return {
        text: original,
        changed: false,
        active: false,
        managed: existing.managed,
        removeFile: false,
        error: 'Existing [prompt] ignore_project_agents = false is user-owned and was not changed.',
      };
    }
    return {
      text: original,
      changed: false,
      active: true,
      managed: existing.managed,
      removeFile: false,
    };
  }

  let bounds = sectionBounds(lines, 'prompt');
  if (!bounds) {
    if (lines.length === 0) lines.push(FILE_MARKER);
    const separatorAdded = lines.length > 0 && Boolean(lines[lines.length - 1].trim());
    if (separatorAdded) lines.push('');
    lines.push(separatorAdded ? TABLE_SEPARATOR_MARKER : TABLE_MARKER, '[prompt]');
    bounds = { start: lines.length - 1, end: lines.length };
  }
  lines.splice(bounds.end, 0, KEY_MARKER, 'ignore_project_agents = true');
  return {
    text: lines.join(eol),
    changed: true,
    active: true,
    managed: true,
    removeFile: false,
  };
}

function removeText(original: string): TextPlan {
  const { eol, lines } = splitToml(original);
  const existing = promptKey(lines);
  if (!existing?.managed) {
    return {
      text: original,
      changed: false,
      active: Boolean(existing?.value),
      managed: false,
      removeFile: false,
    };
  }

  lines.splice(existing.index - 1, 2);
  const bounds = sectionBounds(lines, 'prompt');
  const tableMarker = bounds ? lines[bounds.start - 1] : undefined;
  if (bounds && (tableMarker === TABLE_MARKER || tableMarker === TABLE_SEPARATOR_MARKER)) {
    const body = lines.slice(bounds.start + 1, bounds.end);
    if (body.every((line) => !line.trim())) {
      const separator = tableMarker === TABLE_SEPARATOR_MARKER && lines[bounds.start - 2] === '' ? 1 : 0;
      const start = bounds.start - 1 - separator;
      lines.splice(start, bounds.end - start);
    } else {
      lines.splice(bounds.start - 1, 1);
    }
  }
  const fileMarker = lines.indexOf(FILE_MARKER);
  if (fileMarker >= 0) lines.splice(fileMarker, 1);
  const text = lines.join(eol);
  return {
    text,
    changed: true,
    active: false,
    managed: false,
    removeFile: !text.trim(),
  };
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

function atomicWrite(path: string, content: string): void {
  mkdirSync(dirname(path), { recursive: true });
  const temporary = `${path}.${process.pid}.tmp`;
  writeFileSync(temporary, content, { mode: 0o600 });
  renameSync(temporary, path);
}

function gitExcludePath(root: string): string | undefined {
  const result = spawnSync('git', ['-C', root, 'rev-parse', '--git-path', 'info/exclude'], {
    encoding: 'utf8',
    timeout: 5000,
  });
  if (result.status !== 0 || !result.stdout.trim()) return undefined;
  const path = result.stdout.trim();
  return isAbsolute(path) ? path : resolve(root, path);
}

function backupPath(root: string): string | undefined {
  const result = spawnSync(
    'git',
    [
      '-C',
      root,
      'rev-parse',
      '--git-path',
      `lazy-harness-backups/jcode-config.local-${new Date().toISOString().replace(/[:.]/g, '-')}.toml`,
    ],
    { encoding: 'utf8', timeout: 5000 },
  );
  if (result.status !== 0 || !result.stdout.trim()) return undefined;
  const path = result.stdout.trim();
  return isAbsolute(path) ? path : resolve(root, path);
}

function isIgnored(root: string): boolean {
  const result = spawnSync('git', ['-C', root, 'check-ignore', '-q', EXCLUDE_ENTRY], {
    encoding: 'utf8',
    timeout: 5000,
  });
  return result.status === 0;
}

type IgnorePlan = {
  ok: boolean;
  changed: boolean;
  path?: string;
  original?: string;
  text?: string;
  error?: string;
};

function planIgnore(root: string, enable: boolean): IgnorePlan {
  if (enable && isIgnored(root)) return { ok: true, changed: false };
  const exclude = gitExcludePath(root);
  if (!exclude) {
    return enable
      ? { ok: false, changed: false, error: 'Target root is not a Git worktree; private local Jcode config cannot be guaranteed.' }
      : { ok: true, changed: false };
  }
  const original = existsSync(exclude) ? readFileSync(exclude, 'utf8') : '';
  if (enable) {
    const separator = original && !original.endsWith('\n') ? '\n' : '';
    return {
      ok: true,
      changed: true,
      path: exclude,
      original,
      text: `${original}${separator}${EXCLUDE_MARKER}\n${EXCLUDE_ENTRY}\n`,
    };
  }
  const managed = `${EXCLUDE_MARKER}\n${EXCLUDE_ENTRY}\n`;
  if (!original.includes(managed)) return { ok: true, changed: false };
  return { ok: true, changed: true, path: exclude, original, text: original.replace(managed, '') };
}

export function localPromptConfigPath(root: string): string {
  return join(root, '.jcode', 'config.local.toml');
}

export function inspectLocalPromptTransport(root: string): LocalPromptTransportResult {
  const config = localPromptConfigPath(root);
  const original = existsSync(config) ? readFileSync(config, 'utf8') : '';
  const validation = tomlIsValid(original);
  const existing = promptKey(splitToml(original).lines);
  return {
    ok: validation.ok,
    root,
    config,
    changed: false,
    dryRun: false,
    active: Boolean(existing?.value),
    managed: Boolean(existing?.managed),
    ignored: isIgnored(root),
    ...(!validation.ok ? { error: validation.error } : {}),
  };
}

export function updateLocalPromptTransport(
  root: string,
  enable: boolean,
  dryRun = false,
): LocalPromptTransportResult {
  const config = localPromptConfigPath(root);
  const configExisted = existsSync(config);
  const original = configExisted ? readFileSync(config, 'utf8') : '';
  const originalValidation = tomlIsValid(original);
  if (!originalValidation.ok) {
    return {
      ok: false,
      root,
      config,
      changed: false,
      dryRun,
      active: false,
      managed: false,
      ignored: isIgnored(root),
      error: originalValidation.error,
    };
  }

  const plan = enable ? installText(original) : removeText(original);
  if (plan.error) {
    return { ok: false, root, config, changed: false, dryRun, active: plan.active, managed: plan.managed, ignored: isIgnored(root), error: plan.error };
  }
  const plannedValidation = tomlIsValid(plan.text);
  if (!plannedValidation.ok) {
    return { ok: false, root, config, changed: false, dryRun, active: plan.active, managed: plan.managed, ignored: isIgnored(root), error: plannedValidation.error };
  }

  const ignore = planIgnore(root, enable);
  if (!ignore.ok) {
    return { ok: false, root, config, changed: false, dryRun, active: plan.active, managed: plan.managed, ignored: false, error: ignore.error };
  }

  let backup: string | undefined;
  if (plan.changed && configExisted && !dryRun) {
    try {
      backup = backupPath(root);
      if (!backup) {
        return { ok: false, root, config, changed: false, dryRun, active: plan.active, managed: plan.managed, ignored: isIgnored(root), error: 'Could not resolve a private Git metadata backup path.' };
      }
      mkdirSync(dirname(backup), { recursive: true });
      copyFileSync(config, backup);
    } catch (error) {
      return {
        ok: false,
        root,
        config,
        changed: false,
        dryRun,
        active: Boolean(promptKey(splitToml(original).lines)?.value),
        managed: Boolean(promptKey(splitToml(original).lines)?.managed),
        ignored: isIgnored(root),
        error: `Could not create a private local-config backup: ${String(error)}`,
      };
    }
  }

  if (!dryRun) {
    let configApplied = false;
    let ignoreApplied = false;
    try {
      if (plan.changed) {
        if (plan.removeFile) rmSync(config, { force: true });
        else atomicWrite(config, plan.text);
        configApplied = true;
      }
      if (ignore.changed && ignore.path !== undefined && ignore.text !== undefined) {
        atomicWrite(ignore.path, ignore.text);
        ignoreApplied = true;
      }
    } catch (error) {
      try {
        if (ignoreApplied && ignore.path !== undefined && ignore.original !== undefined) {
          atomicWrite(ignore.path, ignore.original);
        }
        if (configApplied) {
          if (configExisted) atomicWrite(config, original);
          else rmSync(config, { force: true });
        }
      } catch {
        // Best-effort rollback; the caller receives a hard failure and doctor exposes drift.
      }
      return {
        ok: false,
        root,
        config,
        changed: false,
        dryRun,
        active: Boolean(promptKey(splitToml(original).lines)?.value),
        managed: Boolean(promptKey(splitToml(original).lines)?.managed),
        ignored: isIgnored(root),
        error: `Local prompt transport transaction failed: ${String(error)}`,
      };
    }
  }

  return {
    ok: true,
    root,
    config,
    changed: plan.changed || ignore.changed,
    dryRun,
    active: enable ? true : plan.active,
    managed: enable ? plan.managed : false,
    ignored: enable ? true : isIgnored(root),
    ...(backup ? { backup } : {}),
  };
}
