import { existsSync, readFileSync } from 'node:fs'
import { basename, isAbsolute, join, resolve, sep } from 'node:path'

const STABLE_ID = /^[a-z][a-z0-9-]*(?:[.:][a-z0-9][a-z0-9-]*)*$/
const VALUE_REF = /^(?:runtime|organization|operational)\/[a-z][a-z0-9-]*@[0-9]+\.[0-9]+\.[0-9]+$/
const ROOT_REF = /^\.lazy-harness\/(?:domain|spec|behavior|tests|decisions|ssot|rules|project|planning|evidence|framework\/operational-adrs)\/.+$/
const SEMANTIC_OWNER_REF = /^\.lazy-harness\/(?:domain|spec|behavior|tests|decisions|ssot|rules|framework\/operational-adrs)\/.+$/
const FORBIDDEN_FIELDS = new Set([
  'confidence',
  'intent',
  'risk',
  'requiredRead',
  'optionalRead',
  'gate',
  'nextAction',
  'candidateMeaning',
])

export interface ProjectProfileArchitectureCandidate {
  id: string
  status: 'candidate'
  sourceQuestionGroup: 'system-design'
  summary: string
  proposedBindings: Array<{
    axis: 'project-base' | 'runtime' | 'organization' | 'operational'
    valueRef: string
    scopeRef: string
    alias?: { id: string; version: string }
  }>
  evidence: Array<{ kind: string; path?: string; summary: string }>
  semanticOwnerRefs: string[]
  requiresConfirmation: true
}

export interface ProjectProfileArchitecturePromotionDelegation {
  kind: 'host-architecture-map'
  handler: 'lazy architecture plan'
  candidateId: string
  requiresConfirmation: true
  semanticOwnerRefs: string[]
  nextStep: string
}

function isObject(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value)
}

function sourceFallbackForOperationalRef(root: string, ref: string): string | null {
  const prefix = '.lazy-harness/framework/operational-adrs/'
  if (!ref.startsWith(prefix)) return null
  return join(root, '.lazy-harness', 'decisions', basename(ref))
}

function isRootBoundReference(root: string, ref: string): boolean {
  if (!ROOT_REF.test(ref) || ref.includes('\\')) return false
  const segments = ref.split('/')
  if (segments.some((segment) => !segment || segment === '.' || segment === '..')) {
    return false
  }
  const harnessRoot = resolve(root, '.lazy-harness')
  return resolve(root, ref).startsWith(`${harnessRoot}${sep}`)
}

function referenceExists(root: string, ref: string): boolean {
  if (!isRootBoundReference(root, ref)) return false
  if (existsSync(resolve(root, ref))) return true
  const fallback = sourceFallbackForOperationalRef(root, ref)
  return Boolean(fallback && existsSync(fallback))
}

function assertNoForbiddenFields(value: unknown, path = 'architectureCandidates'): void {
  if (Array.isArray(value)) {
    value.forEach((item, index) => assertNoForbiddenFields(item, `${path}[${index}]`))
    return
  }
  if (!isObject(value)) return
  for (const [key, child] of Object.entries(value)) {
    if (FORBIDDEN_FIELDS.has(key)) {
      throw new Error(`${path}.${key} is a forbidden semantic-authority field`)
    }
    assertNoForbiddenFields(child, `${path}.${key}`)
  }
}

function assertAllowedKeys(
  value: Record<string, unknown>,
  allowed: string[],
  path: string,
 ): void {
  const allowedSet = new Set(allowed)
  for (const key of Object.keys(value)) {
    if (!allowedSet.has(key)) {
      throw new Error(`${path}.${key} is not supported by the architecture candidate contract`)
    }
  }
}

function readCandidateFile(root: string, candidateFile: string): unknown {
  const path = isAbsolute(candidateFile)
    ? candidateFile
    : resolve(root, candidateFile)
  let raw: unknown
  try {
    raw = JSON.parse(readFileSync(path, 'utf8'))
  } catch (error) {
    const detail = error instanceof Error ? error.message : String(error)
    throw new Error(`Cannot read architecture candidate file ${path}: ${detail}`)
  }
  return raw
}

function validateCandidate(
  root: string,
  raw: unknown,
  index: number,
): ProjectProfileArchitectureCandidate {
  const path = `architectureCandidates[${index}]`
  if (!isObject(raw)) throw new Error(`${path} must be an object`)
  assertAllowedKeys(
    raw,
    [
      'id',
      'status',
      'sourceQuestionGroup',
      'summary',
      'proposedBindings',
      'evidence',
      'semanticOwnerRefs',
      'requiresConfirmation',
    ],
    path,
  )
  if (typeof raw.id !== 'string' || !STABLE_ID.test(raw.id)) {
    throw new Error(`${path}.id must be a stable lowercase ID`)
  }
  if (raw.status !== 'candidate') throw new Error(`${path}.status must be candidate`)
  if (raw.sourceQuestionGroup !== 'system-design') {
    throw new Error(`${path}.sourceQuestionGroup must be system-design`)
  }
  if (typeof raw.summary !== 'string' || !raw.summary.trim()) {
    throw new Error(`${path}.summary is required`)
  }
  if (raw.requiresConfirmation !== true) {
    throw new Error(`${path}.requiresConfirmation must be true`)
  }

  if (!Array.isArray(raw.proposedBindings) || !raw.proposedBindings.length) {
    throw new Error(`${path}.proposedBindings must be a non-empty array`)
  }
  const proposedBindings = raw.proposedBindings.map((binding, bindingIndex) => {
    const bindingPath = `${path}.proposedBindings[${bindingIndex}]`
    if (!isObject(binding)) throw new Error(`${bindingPath} must be an object`)
    assertAllowedKeys(
      binding,
      ['axis', 'valueRef', 'scopeRef', 'alias'],
      bindingPath,
    )
    const axis = String(binding.axis)
    if (!['project-base', 'runtime', 'organization', 'operational'].includes(axis)) {
      throw new Error(`${bindingPath}.axis is invalid`)
    }
    const valueRef = String(binding.valueRef || '')
    if (axis !== 'project-base' && !VALUE_REF.test(valueRef)) {
      throw new Error(`${bindingPath}.valueRef is invalid`)
    }
    if (axis === 'project-base'
      && !/^project-base\/[a-z][a-z0-9-]*\/[a-z][a-z0-9-]*$/.test(valueRef)) {
      throw new Error(`${bindingPath}.valueRef is invalid`)
    }
    const scopeRef = String(binding.scopeRef || '')
    if (!STABLE_ID.test(scopeRef)) throw new Error(`${bindingPath}.scopeRef is invalid`)
    let alias: { id: string; version: string } | undefined
    if (binding.alias !== undefined) {
      if (!isObject(binding.alias)) {
        throw new Error(`${bindingPath}.alias is invalid`)
      }
      assertAllowedKeys(binding.alias, ['id', 'version'], `${bindingPath}.alias`)
      if (typeof binding.alias.id !== 'string'
        || !STABLE_ID.test(binding.alias.id)
        || typeof binding.alias.version !== 'string'
        || !/^[0-9]+\.[0-9]+\.[0-9]+$/.test(binding.alias.version)) {
        throw new Error(`${bindingPath}.alias is invalid`)
      }
      alias = { id: binding.alias.id, version: binding.alias.version }
    }
    return {
      axis: axis as ProjectProfileArchitectureCandidate['proposedBindings'][number]['axis'],
      valueRef,
      scopeRef,
      ...(alias ? { alias } : {}),
    }
  })

  if (!Array.isArray(raw.evidence) || !raw.evidence.length) {
    throw new Error(`${path}.evidence must be a non-empty array`)
  }
  const evidence = raw.evidence.map((item, evidenceIndex) => {
    const evidencePath = `${path}.evidence[${evidenceIndex}]`
    if (!isObject(item)
      || typeof item.kind !== 'string'
      || !item.kind.trim()
      || typeof item.summary !== 'string'
      || !item.summary.trim()) {
      throw new Error(`${evidencePath} is invalid`)
    }
    assertAllowedKeys(item, ['kind', 'path', 'summary'], evidencePath)
    if (item.path !== undefined) {
      if (typeof item.path !== 'string' || !referenceExists(root, item.path)) {
        throw new Error(`${evidencePath}.path must resolve to a root-bound record`)
      }
    }
    return {
      kind: item.kind,
      ...(typeof item.path === 'string' ? { path: item.path } : {}),
      summary: item.summary,
    }
  })

  if (!Array.isArray(raw.semanticOwnerRefs) || !raw.semanticOwnerRefs.length) {
    throw new Error(`${path}.semanticOwnerRefs must be a non-empty array`)
  }
  const semanticOwnerRefs = raw.semanticOwnerRefs.map((ref, refIndex) => {
    if (typeof ref !== 'string'
      || !SEMANTIC_OWNER_REF.test(ref)
      || !referenceExists(root, ref)) {
      throw new Error(
        `${path}.semanticOwnerRefs[${refIndex}] must resolve to DDD, SDD, BDD, TDD, ADR, SSOT, rulebook, or operational ADR truth`,
      )
    }
    return ref
  })

  return {
    id: raw.id,
    status: 'candidate',
    sourceQuestionGroup: 'system-design',
    summary: raw.summary,
    proposedBindings,
    evidence,
    semanticOwnerRefs,
    requiresConfirmation: true,
  }
}

export function loadProjectProfileArchitectureCandidates(
  root: string,
  candidateFile?: string,
): ProjectProfileArchitectureCandidate[] {
  if (!candidateFile) return []
  const raw = readCandidateFile(root, candidateFile)
  if (!isObject(raw)
    || raw.schemaVersion !== 'project-profile-architecture-candidates/v1'
    || !Array.isArray(raw.candidates)) {
    throw new Error(
      'Architecture candidate file must use project-profile-architecture-candidates/v1',
    )
  }
  assertAllowedKeys(raw, ['schemaVersion', 'candidates'], 'architectureCandidateFile')
  assertNoForbiddenFields(raw)
  const candidates = raw.candidates.map((candidate, index) =>
    validateCandidate(root, candidate, index))
  const ids = candidates.map((candidate) => candidate.id)
  if (new Set(ids).size !== ids.length) {
    throw new Error('Architecture candidate IDs must be unique')
  }
  return candidates
}

export function buildArchitecturePromotionDelegation(
  candidateId: string,
  semanticOwnerRefs: string[],
): ProjectProfileArchitecturePromotionDelegation {
  return {
    kind: 'host-architecture-map',
    handler: 'lazy architecture plan',
    candidateId,
    requiresConfirmation: true,
    semanticOwnerRefs: [...semanticOwnerRefs],
    nextStep: 'Create an explicit host-map proposal, run lazy architecture plan, then apply only with the exact confirmed plan digest.',
  }
}
