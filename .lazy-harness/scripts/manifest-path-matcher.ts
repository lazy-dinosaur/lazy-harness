/** Shared Category A manifest glob semantics for sync and installed-host audits. */
export function matchManifestGlob(name: string, glob: string): boolean {
  const re = new RegExp(
    '^' +
      glob
        .replace(/\./g, '\\.')
        .replace(/\*\*/g, '___DOUBLESTAR___')
        .replace(/\*/g, '[^/]*')
        .replace(/___DOUBLESTAR___/g, '.*') +
      '$'
  )
  return re.test(name)
}

export function shouldIncludeManifestPath(relPath: string, glob?: string[], exclude?: string[]): boolean {
  if (exclude) {
    for (const pattern of exclude) {
      if (matchManifestGlob(relPath, pattern) || relPath.startsWith(pattern.replace(/\/$/, ''))) return false
    }
  }
  if (!glob || glob.length === 0) return true
  return glob.some((pattern) => matchManifestGlob(relPath, pattern))
}
