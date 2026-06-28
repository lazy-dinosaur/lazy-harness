// Shared test-file matcher for the 5d-3 gates (tdd-cross-verify.ts + affected-test-runner.ts).
//
// Single source of "does this source file have a matching test?" so both gates agree
// and a layout fix lands in one place. See tests/tdd-cross-verify-forcegate-loop.md.
//
// Robust against common project conventions that the old co-located-only matcher
// missed (which caused false-positive 5d-3 STOPs even when tests existed and passed):
//   - test dir: co-located, `__tests__/`, `tests/`, `__test__/`
//   - name case: PascalCase source ↔ kebab-case / snake_case test (separator-insensitive)
//   - infixes: `Foo.tsx` matches `foo.contract.test.tsx`, `foo.unit.spec.ts`, etc.
import { existsSync, readdirSync } from 'node:fs';
import path from 'node:path';

export const TEST_FILE_RE = /\.(test|spec)\.(ts|tsx|js|jsx)$/;

export function normalizePath(file: string): string {
  return file.replace(/\\/g, '/').replace(/^\.\//, '');
}

export function uniqueFiles(files: string[]): string[] {
  return [...new Set(files.map(normalizePath))];
}

export function isTestFile(file: string): boolean {
  return TEST_FILE_RE.test(path.basename(file));
}

// Collapse separators + case so PascalCase/kebab-case/snake_case stems compare equal.
function normalizeStem(stem: string): string {
  return stem.replace(/[-_.\s]/g, '').toLowerCase();
}


// Deterministic co-located suggestion paths (used for the option-A suggestedPath and
// crossRef.candidates in both gates). Kept co-located so suggestions stay conventional.
export function candidateTestPaths(file: string): string[] {
  const parsed = path.parse(file);
  const dir = parsed.dir;
  const ext = parsed.ext;
  const base = parsed.name;
  return [
    path.join(dir, `${base}.test${ext}`),
    path.join(dir, `${base}.spec${ext}`),
    path.join(dir, '__tests__', `${base}.test${ext}`),
    path.join(dir, '__tests__', `${base}.spec${ext}`),
  ].map(normalizePath);
}

// Return existing test files that cover `file`. A test matches when, in any candidate
// test dir, a `*.test|spec.*` file's base (suffix stripped) has a leading dot-delimited
// segment-prefix whose normalized form equals the source stem — so infixes like
// `.contract` are allowed while unrelated files (`OtherView.test.tsx`) are not matched.
export function matchingTests(file: string): string[] {
  if (isTestFile(file)) return [file];
  const parsed = path.parse(file);
  const stemNorm = normalizeStem(parsed.name);
  if (!stemNorm) return [];
  const results: string[] = [];
  const baseDir = parsed.dir || '.';
  const dirs = [baseDir, path.join(baseDir, '__tests__'), path.join(baseDir, 'tests'), path.join(baseDir, '__test__')];
  for (const dir of dirs) {
    if (!existsSync(dir)) continue;
    let entries: string[];
    try {
      entries = readdirSync(dir);
    } catch {
      continue;
    }
    for (const entry of entries) {
      if (!TEST_FILE_RE.test(entry)) continue;
      const testBase = entry.replace(TEST_FILE_RE, '');
      const segments = testBase.split('.');
      for (let k = 1; k <= segments.length; k += 1) {
        if (normalizeStem(segments.slice(0, k).join('')) === stemNorm) {
          results.push(normalizePath(path.join(dir, entry)));
          break;
        }
      }
    }
  }
  return uniqueFiles(results);
}
