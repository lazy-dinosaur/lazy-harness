import {
  existsSync,
  mkdirSync,
  readFileSync,
  realpathSync,
  renameSync,
  writeFileSync,
} from 'node:fs';
import { homedir } from 'node:os';
import { dirname, isAbsolute, join, resolve } from 'node:path';

export type TrustRegistry = {
  schemaVersion: 'lazy-jcode-trusted-roots/v1';
  roots: string[];
};

export function jcodeHome(): string {
  const configured = process.env.JCODE_HOME?.trim();
  // Runtime hooks must never resolve a relative user-home path from an untrusted cwd.
  return configured && isAbsolute(configured) ? resolve(configured) : join(homedir(), '.jcode');
}

export function relativeJcodeHome(): string | undefined {
  const configured = process.env.JCODE_HOME?.trim();
  return configured && !isAbsolute(configured) ? configured : undefined;
}

export function trustRegistryPath(): string {
  return join(jcodeHome(), 'lazy-harness-trusted-roots.json');
}

export function canonicalRoot(path: string): string {
  const absolute = resolve(path);
  return existsSync(absolute) ? realpathSync(absolute) : absolute;
}

export function loadTrustRegistry(path = trustRegistryPath()): TrustRegistry {
  try {
    const parsed = JSON.parse(readFileSync(path, 'utf8')) as Partial<TrustRegistry>;
    if (parsed.schemaVersion === 'lazy-jcode-trusted-roots/v1' && Array.isArray(parsed.roots)) {
      return {
        schemaVersion: 'lazy-jcode-trusted-roots/v1',
        roots: [...new Set(parsed.roots.filter((root): root is string => typeof root === 'string').map(canonicalRoot))].sort(),
      };
    }
  } catch {
    // Missing or invalid registry is an empty trust set, never trust-all.
  }
  return { schemaVersion: 'lazy-jcode-trusted-roots/v1', roots: [] };
}

export function isTrustedRoot(root: string, path = trustRegistryPath()): boolean {
  return loadTrustRegistry(path).roots.includes(canonicalRoot(root));
}

export function writeTrustRegistry(registry: TrustRegistry, path = trustRegistryPath()): void {
  const normalized: TrustRegistry = {
    schemaVersion: 'lazy-jcode-trusted-roots/v1',
    roots: [...new Set(registry.roots.map(canonicalRoot))].sort(),
  };
  mkdirSync(dirname(path), { recursive: true });
  const tmp = `${path}.${process.pid}.tmp`;
  writeFileSync(tmp, `${JSON.stringify(normalized, null, 2)}\n`, { mode: 0o600 });
  renameSync(tmp, path);
}

export function updateTrustedRoot(
  root: string,
  trust: boolean,
  path = trustRegistryPath(),
): { changed: boolean; registry: TrustRegistry; root: string } {
  const canonical = canonicalRoot(root);
  const registry = loadTrustRegistry(path);
  const before = registry.roots.includes(canonical);
  if (trust && !before) registry.roots.push(canonical);
  if (!trust && before) registry.roots = registry.roots.filter((item) => item !== canonical);
  registry.roots.sort();
  return { changed: before !== trust, registry, root: canonical };
}
