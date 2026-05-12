import path from 'node:path';

export function splitIdentifierWords(value: string): string[] {
  return value
    .replace(/([a-z0-9])([A-Z])/g, '$1 $2')
    .replace(/[_\-./]+/g, ' ')
    .split(/\s+/)
    .map((word) => word.trim())
    .filter(Boolean)
    .map((word) => word.toLowerCase());
}

export function compactSignature(value: string): string {
  return value.replace(/\s+/g, ' ').trim();
}

export function unique<T>(items: T[]): T[] {
  return [...new Set(items)];
}

export function isTypescriptFile(filePath: string): boolean {
  return /\.(ts|tsx)$/.test(filePath) && !/\.(test|spec)\.(ts|tsx)$/.test(filePath);
}

export function normalizePath(filePath: string): string {
  return path.relative(process.cwd(), path.resolve(filePath)).replaceAll('\\', '/');
}
