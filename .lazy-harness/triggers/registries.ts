import { existsSync, readFileSync } from 'node:fs';
import { splitIdentifierWords } from './common';

export function readKnownTerms(filePath: string): Set<string> {
  if (!existsSync(filePath)) return new Set();
  const xml = readFileSync(filePath, 'utf8');
  const terms = new Set<string>();
  const attributePattern = /\b(?:name|term|canonical|acronym|fullName)=["']([^"']+)["']/gi;
  for (const match of xml.matchAll(attributePattern)) {
    addKnownTermVariants(terms, match[1]);
  }

  const patterns = [
    /<canonical>([^<]+)<\/canonical>/gi,
    /<name>([^<]+)<\/name>/gi,
    /<term>([^<]+)<\/term>/gi,
    /<acronym>([^<]+)<\/acronym>/gi,
    /<fullName>([^<]+)<\/fullName>/gi,
  ];
  for (const pattern of patterns) {
    for (const match of xml.matchAll(pattern)) {
      addKnownTermVariants(terms, match[1]);
    }
  }
  return terms;
}

function addKnownTermVariants(terms: Set<string>, rawValue: string | undefined): void {
  const value = rawValue?.trim();
  if (!value) return;
  terms.add(value.toLowerCase());
  const compact = value.replace(/[^A-Za-z0-9]/g, '');
  if (compact) terms.add(compact.toLowerCase());
  const words = splitIdentifierWords(value);
  if (words.length > 0) terms.add(words.map((word) => word.charAt(0).toUpperCase() + word.slice(1)).join('').toLowerCase());
}
