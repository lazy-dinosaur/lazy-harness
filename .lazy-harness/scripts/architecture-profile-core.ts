import { createHash } from 'node:crypto'
import {
  closeSync,
  existsSync,
  mkdirSync,
  openSync,
  readFileSync,
  renameSync,
  rmSync,
  writeFileSync,
} from 'node:fs'
import { basename, dirname, isAbsolute, join, resolve, sep } from 'node:path'

export const ARCHITECTURE_CATALOG_PATH =
  '.lazy-harness/ssot/architecture-profile-catalog.json'
export const HOST_ARCHITECTURE_MAP_PATH =
  '.lazy-harness/project/architecture-map.json'

const STABLE_ID = /^[a-z][a-z0-9-]*(?:[.:][a-z0-9][a-z0-9-]*)*$/
const SEMVER = /^[0-9]+\.[0-9]+\.[0-9]+$/
const VALUE_REF = /^(runtime|organization|operational)\/([a-z][a-z0-9-]*)@([0-9]+\.[0-9]+\.[0-9]+)$/
const VALUE_ID = /^(runtime|organization|operational)\/([a-z][a-z0-9-]*)$/
const ROOT_REF = /^\.lazy-harness\/(?:domain|spec|behavior|tests|decisions|ssot|rules|project|planning|evidence|framework\/operational-adrs)\/.+$/
const SEMANTIC_OWNER_REF = /^\.lazy-harness\/(?:domain|spec|behavior|tests|decisions|ssot|rules|framework\/operational-adrs)\/.+$/

export type ArchitectureAxis = 'runtime' | 'organization' | 'operational'
export type RelationType =
  | 'requires'
  | 'compatibleWith'
  | 'conflictsWith'
  | 'strengthens'
export type ScopeKind = 'host' | 'unit' | 'entrypoint' | 'responsibility'

export interface ArchitectureFinding {
  severity: 'error' | 'warning'
  code: string
  message: string
  path?: string
}

export interface ProfileValue {
  id: string
  version: string
  axis: ArchitectureAxis
  status: 'active' | 'deprecated'
  summary: string
  constraintRefs: string[]
}

export interface ProfileAliasParameter {
  name: string
  scopeKinds: ScopeKind[]
}

export interface ProfileAliasBinding {
  axis: ArchitectureAxis
  valueRef: string
  scopeParameter: string
  condition?: string
  semanticOwnerRefs: string[]
}

export interface ProfileAlias {
  id: string
  version: string
  status: 'active' | 'deprecated'
  parameters: ProfileAliasParameter[]
  bindings: ProfileAliasBinding[]
  assumptions: string[]
  omissions: string[]
  activationEvidence: string[]
  exitTriggers: string[]
  constraintRefs: string[]
}

export interface ProfileRelation {
  id: string
  type: RelationType
  from: string
  to: string
  scopeRule: 'same' | 'overlap' | 'explicit-cross-scope'
  decisionRef: string
}

export interface ArchitectureProfileCatalog {
  schemaVersion: 'architecture-profile-catalog/v1'
  catalogId: string
  catalogVersion: string
  principleRefs: string[]
  projectBaseDimensions: {
    unitTopology: string[]
    packageTopology: string[]
    deploymentTopology: string[]
    ownershipTopology: string[]
  }
  values: ProfileValue[]
  aliases: ProfileAlias[]
  relations: ProfileRelation[]
  semanticOwnerRefs: string[]
}

export interface ArchitectureScope {
  id: string
  kind: ScopeKind
  parentId: string | null
  selectors: Array<{
    kind: 'path' | 'package' | 'process' | 'service' | 'deployment'
    value: string
  }>
  ownerRefs: string[]
}

export interface ArchitectureBinding {
  id: string
  axis: ArchitectureAxis
  valueRef: string
  scopeId: string
  condition?: string
  evidenceRefs: string[]
  semanticOwnerRefs: string[]
  aliasInstanceId?: string
  reviewTrigger: string
}

export interface ArchitectureAliasInstance {
  id: string
  aliasRef: string
  parameters: Record<string, string>
  materializedBindingIds: string[]
}

export interface ArchitectureCompositionDecision {
  id: string
  leftBindingId: string
  rightBindingId: string
  scopeId: string
  outcome: 'accepted-compatible' | 'accepted-with-waiver'
  decisionRef: string
}

export interface HostArchitectureMap {
  schemaVersion: 'host-architecture-map/v1'
  mapVersion: number
  hostId: string
  catalogRef: { id: string; version: string }
  status: 'candidate' | 'confirmed'
  confirmation?: { reference: string; confirmedAt: string }
  principleRefs: string[]
  projectBase: {
    unitTopology: string
    packageTopology: string
    deploymentTopology: string
    ownershipTopology: string
    edges: Array<{
      fromScopeId: string
      toScopeId: string
      relation: 'depends-on' | 'owns' | 'deploys-with' | 'publishes-to'
    }>
    evidenceRefs: string[]
  }
  scopes: ArchitectureScope[]
  bindings: ArchitectureBinding[]
  aliasInstances: ArchitectureAliasInstance[]
  compositionDecisions: ArchitectureCompositionDecision[]
  waiverRefs: string[]
  evidenceAdapterRefs: string[]
  policyRefs: string[]
  capabilityRefs: string[]
  reviewTriggers: string[]
}

export interface ArchitectureValidationResult {
  ok: boolean
  findings: ArchitectureFinding[]
}

export interface ArchitectureInspectResult {
  ok: boolean
  mode: 'architecture.inspect'
  schemaVersion: 'architecture-inspect/v1'
  root: string
  catalogPath: string
  mapPath: string
  catalog: {
    id?: string
    version?: string
    valueCount: number
    aliasCount: number
    relationCount: number
    digest?: string
  }
  hostMap: {
    exists: boolean
    status: 'missing' | 'candidate' | 'confirmed' | 'invalid'
    hostId?: string
    mapVersion?: number
    digest?: string
  }
  findings: ArchitectureFinding[]
  writes: []
  notice: string
}

export interface ArchitecturePlanResult {
  ok: boolean
  mode: 'architecture.plan'
  schemaVersion: 'architecture-plan/v1'
  root: string
  proposalPath: string
  catalogPath: string
  mapPath: string
  baselineDigest: string
  proposalDigest: string
  catalogDigest: string
  planDigest: string
  catalogRef?: { id: string; version: string }
  normalizedMap?: HostArchitectureMap
  findings: ArchitectureFinding[]
  unresolved: ArchitectureFinding[]
  writes: Array<{
    path: string
    action: 'create' | 'replace'
    requiresConfirmation: true
  }>
}

export interface ArchitectureApplyResult {
  ok: true
  mode: 'architecture.apply'
  schemaVersion: 'architecture-apply/v1'
  root: string
  planDigest: string
  baselineDigest: string
  mapPath: string
  mapDigest: string
  status: 'confirmed'
  confirmationRef: string
  writes: Array<{ path: string; action: 'written' }>
}

export class ArchitectureContractError extends Error {
  readonly exitCode: number
  readonly findings: ArchitectureFinding[]

  constructor(message: string, findings: ArchitectureFinding[] = [], exitCode = 2) {
    super(message)
    this.name = 'ArchitectureContractError'
    this.exitCode = exitCode
    this.findings = findings
  }
}

function isObject(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value)
}

function stringArray(value: unknown): string[] {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === 'string')
    : []
}

function unique(values: string[]): boolean {
  return new Set(values).size === values.length
}

function stableValue(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(stableValue)
  if (!isObject(value)) return value
  return Object.fromEntries(
    Object.keys(value)
      .sort()
      .map((key) => [key, stableValue(value[key])]),
  )
}

export function stableJson(value: unknown): string {
  return JSON.stringify(stableValue(value))
}

export function architectureDigest(value: unknown): string {
  return createHash('sha256').update(stableJson(value)).digest('hex')
}

function readJson(path: string): unknown {
  try {
    return JSON.parse(readFileSync(path, 'utf8'))
  } catch (error) {
    const detail = error instanceof Error ? error.message : String(error)
    throw new ArchitectureContractError(`Cannot read JSON ${path}: ${detail}`, [], 1)
  }
}

function addFinding(
  findings: ArchitectureFinding[],
  code: string,
  message: string,
  path?: string,
  severity: ArchitectureFinding['severity'] = 'error',
): void {
  findings.push({ severity, code, message, ...(path ? { path } : {}) })
}

function validateAllowedKeys(
  findings: ArchitectureFinding[],
  value: Record<string, unknown>,
  allowed: string[],
  path: string,
 ): void {
  const allowedSet = new Set(allowed)
  for (const key of Object.keys(value)) {
    if (!allowedSet.has(key)) {
      addFinding(
        findings,
        'unknown-property',
        `${path || 'object'} contains unsupported property ${key}`,
        path ? `${path}.${key}` : key,
      )
    }
  }
}

function validateStableId(
  findings: ArchitectureFinding[],
  value: unknown,
  path: string,
): value is string {
  if (typeof value !== 'string' || !STABLE_ID.test(value)) {
    addFinding(findings, 'invalid-id', `${path} must be a stable lowercase ID`, path)
    return false
  }
  return true
}

function validateSemver(
  findings: ArchitectureFinding[],
  value: unknown,
  path: string,
): value is string {
  if (typeof value !== 'string' || !SEMVER.test(value)) {
    addFinding(findings, 'invalid-version', `${path} must be semantic x.y.z`, path)
    return false
  }
  return true
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
  const direct = resolve(root, ref)
  return direct.startsWith(`${harnessRoot}${sep}`)
}

function referenceExists(root: string, ref: string): boolean {
  if (!isRootBoundReference(root, ref)) return false
  const direct = resolve(root, ref)
  if (existsSync(direct)) return true
  const fallback = sourceFallbackForOperationalRef(root, ref)
  return Boolean(fallback && existsSync(fallback))
}

function validateReferences(
  root: string,
  findings: ArchitectureFinding[],
  refs: unknown,
  path: string,
  minItems = 0,
): string[] {
  const values = stringArray(refs)
  if (!Array.isArray(refs) || values.length !== refs.length || values.length < minItems) {
    addFinding(
      findings,
      'invalid-reference-list',
      `${path} must contain at least ${minItems} root-bound reference(s)`,
      path,
    )
    return values
  }
  if (!unique(values)) {
    addFinding(findings, 'duplicate-reference', `${path} contains duplicate refs`, path)
  }
  for (const [index, ref] of values.entries()) {
    if (!isRootBoundReference(root, ref)) {
      addFinding(
        findings,
        'non-root-bound-reference',
        `${path}[${index}] is not a root-bound architecture reference`,
        `${path}[${index}]`,
      )
    } else if (!referenceExists(root, ref)) {
      addFinding(
        findings,
        'missing-reference',
        `${path}[${index}] does not resolve in this host: ${ref}`,
        `${path}[${index}]`,
      )
    }
  }
  return values
}

function validateSemanticOwnerReferences(
  root: string,
  findings: ArchitectureFinding[],
  refs: unknown,
  path: string,
  minItems = 1,
 ): string[] {
  const values = validateReferences(root, findings, refs, path, minItems)
  for (const [index, ref] of values.entries()) {
    if (!SEMANTIC_OWNER_REF.test(ref)) {
      addFinding(
        findings,
        'invalid-semantic-owner',
        `${path}[${index}] must reference DDD, SDD, BDD, TDD, ADR, SSOT, rulebook, or operational ADR truth`,
        `${path}[${index}]`,
      )
    }
  }
  return values
}

function exactStrings(actual: unknown, expected: string[]): boolean {
  return Array.isArray(actual)
    && actual.length === expected.length
    && actual.every((item, index) => item === expected[index])
}

function validateCatalogObject(
  root: string,
  raw: unknown,
): { catalog?: ArchitectureProfileCatalog; findings: ArchitectureFinding[] } {
  const findings: ArchitectureFinding[] = []
  if (!isObject(raw)) {
    addFinding(findings, 'invalid-catalog', 'Catalog must be an object')
    return { findings }
  }
  validateAllowedKeys(
    findings,
    raw,
    [
      'schemaVersion',
      'catalogId',
      'catalogVersion',
      'principleRefs',
      'projectBaseDimensions',
      'values',
      'aliases',
      'relations',
      'semanticOwnerRefs',
    ],
    'catalog',
  )
  if (raw.schemaVersion !== 'architecture-profile-catalog/v1') {
    addFinding(findings, 'invalid-schema-version', 'Catalog schemaVersion must be architecture-profile-catalog/v1')
  }
  validateStableId(findings, raw.catalogId, 'catalogId')
  validateSemver(findings, raw.catalogVersion, 'catalogVersion')
  const expectedPrinciples = [
    'ARCH-L1-01',
    'ARCH-L1-02',
    'ARCH-L1-03',
    'ARCH-L1-04',
    'ARCH-L1-05',
    'ARCH-L1-06',
  ]
  if (!exactStrings(raw.principleRefs, expectedPrinciples)) {
    addFinding(findings, 'invalid-principles', 'Catalog must reference all six Layer 1 principles in order', 'principleRefs')
  }

  const base = raw.projectBaseDimensions
  const expectedBase: Record<string, string[]> = {
    unitTopology: ['single-unit', 'multi-unit'],
    packageTopology: ['single-package', 'multi-package'],
    deploymentTopology: ['single-deployment', 'multi-deployment', 'hybrid'],
    ownershipTopology: ['single-owner', 'multi-owner'],
  }
  if (!isObject(base)) {
    addFinding(findings, 'invalid-project-base', 'projectBaseDimensions must be an object', 'projectBaseDimensions')
  } else {
    validateAllowedKeys(
      findings,
      base,
      ['unitTopology', 'packageTopology', 'deploymentTopology', 'ownershipTopology'],
      'projectBaseDimensions',
    )
    for (const [key, expected] of Object.entries(expectedBase)) {
      if (!exactStrings(base[key], expected)) {
        addFinding(
          findings,
          'invalid-project-base-values',
          `projectBaseDimensions.${key} does not match the approved catalog`,
          `projectBaseDimensions.${key}`,
        )
      }
    }
  }

  const values = Array.isArray(raw.values) ? raw.values : []
  if (!Array.isArray(raw.values) || values.length < 18) {
    addFinding(findings, 'missing-profile-values', 'Catalog must contain the 18 approved normalized values', 'values')
  }
  const valueRefs = new Set<string>()
  const parsedValues: ProfileValue[] = []
  for (const [index, value] of values.entries()) {
    const path = `values[${index}]`
    if (!isObject(value)) {
      addFinding(findings, 'invalid-profile-value', `${path} must be an object`, path)
      continue
    }
    validateAllowedKeys(
      findings,
      value,
      ['id', 'version', 'axis', 'status', 'summary', 'constraintRefs'],
      path,
    )
    const id = typeof value.id === 'string' ? value.id : ''
    const version = typeof value.version === 'string' ? value.version : ''
    const axis = value.axis
    const idMatch = id.match(VALUE_ID)
    if (!idMatch) addFinding(findings, 'invalid-value-id', `${path}.id is invalid`, `${path}.id`)
    validateSemver(findings, version, `${path}.version`)
    if (!['runtime', 'organization', 'operational'].includes(String(axis))) {
      addFinding(findings, 'invalid-axis', `${path}.axis is invalid`, `${path}.axis`)
    }
    if (idMatch && axis !== idMatch[1]) {
      addFinding(findings, 'axis-id-mismatch', `${path}.axis does not match its id prefix`, `${path}.axis`)
    }
    if (!['active', 'deprecated'].includes(String(value.status))) {
      addFinding(findings, 'invalid-value-status', `${path}.status is invalid`, `${path}.status`)
    }
    if (typeof value.summary !== 'string' || !value.summary.trim()) {
      addFinding(findings, 'missing-value-summary', `${path}.summary is required`, `${path}.summary`)
    }
    const constraintRefs = validateReferences(root, findings, value.constraintRefs, `${path}.constraintRefs`, 1)
    const ref = `${id}@${version}`
    if (valueRefs.has(ref)) {
      addFinding(findings, 'duplicate-value-ref', `Duplicate catalog value ${ref}`, path)
    }
    valueRefs.add(ref)
    parsedValues.push({
      id,
      version,
      axis: axis as ArchitectureAxis,
      status: value.status as ProfileValue['status'],
      summary: String(value.summary || ''),
      constraintRefs,
    })
  }

  const aliases = Array.isArray(raw.aliases) ? raw.aliases : []
  if (!Array.isArray(raw.aliases)) {
    addFinding(findings, 'invalid-aliases', 'aliases must be an array', 'aliases')
  }
  const aliasRefs = new Set<string>()
  const parsedAliases: ProfileAlias[] = []
  for (const [index, alias] of aliases.entries()) {
    const path = `aliases[${index}]`
    if (!isObject(alias)) {
      addFinding(findings, 'invalid-alias', `${path} must be an object`, path)
      continue
    }
    validateAllowedKeys(
      findings,
      alias,
      [
        'id',
        'version',
        'status',
        'parameters',
        'bindings',
        'assumptions',
        'omissions',
        'activationEvidence',
        'exitTriggers',
        'constraintRefs',
      ],
      path,
    )
    const id = typeof alias.id === 'string' ? alias.id : ''
    const version = typeof alias.version === 'string' ? alias.version : ''
    validateStableId(findings, id, `${path}.id`)
    validateSemver(findings, version, `${path}.version`)
    const aliasRef = `${id}@${version}`
    if (aliasRefs.has(aliasRef)) {
      addFinding(findings, 'duplicate-alias-ref', `Duplicate alias ${aliasRef}`, path)
    }
    aliasRefs.add(aliasRef)
    if (!['active', 'deprecated'].includes(String(alias.status))) {
      addFinding(findings, 'invalid-alias-status', `${path}.status is invalid`, `${path}.status`)
    }
    const parametersRaw = Array.isArray(alias.parameters) ? alias.parameters : []
    const parameters: ProfileAliasParameter[] = []
    const parameterNames = new Set<string>()
    if (!parametersRaw.length) {
      addFinding(findings, 'missing-alias-parameters', `${path}.parameters cannot be empty`, `${path}.parameters`)
    }
    for (const [parameterIndex, parameter] of parametersRaw.entries()) {
      const parameterPath = `${path}.parameters[${parameterIndex}]`
      if (!isObject(parameter)) {
        addFinding(findings, 'invalid-alias-parameter', `${parameterPath} must be an object`, parameterPath)
        continue
      }
      validateAllowedKeys(findings, parameter, ['name', 'scopeKinds'], parameterPath)
      const name = typeof parameter.name === 'string' ? parameter.name : ''
      const scopeKinds = stringArray(parameter.scopeKinds) as ScopeKind[]
      if (!/^[a-z][a-zA-Z0-9]*$/.test(name)) {
        addFinding(findings, 'invalid-parameter-name', `${parameterPath}.name is invalid`, `${parameterPath}.name`)
      }
      if (parameterNames.has(name)) {
        addFinding(findings, 'duplicate-parameter', `${path} repeats parameter ${name}`, parameterPath)
      }
      parameterNames.add(name)
      if (!scopeKinds.length || scopeKinds.some((kind) => !['host', 'unit', 'entrypoint', 'responsibility'].includes(kind))) {
        addFinding(findings, 'invalid-parameter-scope', `${parameterPath}.scopeKinds is invalid`, `${parameterPath}.scopeKinds`)
      }
      parameters.push({ name, scopeKinds })
    }
    const bindingsRaw = Array.isArray(alias.bindings) ? alias.bindings : []
    const bindings: ProfileAliasBinding[] = []
    if (!bindingsRaw.length) {
      addFinding(findings, 'missing-alias-bindings', `${path}.bindings cannot be empty`, `${path}.bindings`)
    }
    for (const [bindingIndex, binding] of bindingsRaw.entries()) {
      const bindingPath = `${path}.bindings[${bindingIndex}]`
      if (!isObject(binding)) {
        addFinding(findings, 'invalid-alias-binding', `${bindingPath} must be an object`, bindingPath)
        continue
      }
      validateAllowedKeys(
        findings,
        binding,
        ['axis', 'valueRef', 'scopeParameter', 'condition', 'semanticOwnerRefs'],
        bindingPath,
      )
      const axis = String(binding.axis) as ArchitectureAxis
      const valueRef = String(binding.valueRef || '')
      const scopeParameter = String(binding.scopeParameter || '')
      if (!['runtime', 'organization', 'operational'].includes(axis)) {
        addFinding(findings, 'invalid-axis', `${bindingPath}.axis is invalid`, `${bindingPath}.axis`)
      }
      if (!valueRefs.has(valueRef)) {
        addFinding(findings, 'unknown-value-ref', `${bindingPath}.valueRef is not in the catalog`, `${bindingPath}.valueRef`)
      }
      if (VALUE_REF.exec(valueRef)?.[1] !== axis) {
        addFinding(findings, 'axis-value-mismatch', `${bindingPath}.axis does not match valueRef`, bindingPath)
      }
      if (!parameterNames.has(scopeParameter)) {
        addFinding(findings, 'unknown-scope-parameter', `${bindingPath}.scopeParameter is undeclared`, `${bindingPath}.scopeParameter`)
      }
      if (axis === 'operational' && (typeof binding.condition !== 'string' || !binding.condition.trim())) {
        addFinding(findings, 'missing-operational-condition', `${bindingPath}.condition is required`, `${bindingPath}.condition`)
      }
      const semanticOwnerRefs = validateSemanticOwnerReferences(
        root,
        findings,
        binding.semanticOwnerRefs,
        `${bindingPath}.semanticOwnerRefs`,
      )
      bindings.push({
        axis,
        valueRef,
        scopeParameter,
        ...(typeof binding.condition === 'string' ? { condition: binding.condition } : {}),
        semanticOwnerRefs,
      })
    }
    const constraintRefs = validateReferences(root, findings, alias.constraintRefs, `${path}.constraintRefs`, 1)
    const stringListFields = ['assumptions', 'omissions', 'activationEvidence', 'exitTriggers'] as const
    const stringLists: Record<string, string[]> = {}
    for (const field of stringListFields) {
      const list = stringArray(alias[field])
      if (!Array.isArray(alias[field]) || list.length !== alias[field].length || (field === 'exitTriggers' && !list.length)) {
        addFinding(findings, 'invalid-alias-list', `${path}.${field} is invalid`, `${path}.${field}`)
      }
      stringLists[field] = list
    }
    parsedAliases.push({
      id,
      version,
      status: alias.status as ProfileAlias['status'],
      parameters,
      bindings,
      assumptions: stringLists.assumptions,
      omissions: stringLists.omissions,
      activationEvidence: stringLists.activationEvidence,
      exitTriggers: stringLists.exitTriggers,
      constraintRefs,
    })
  }

  const relations = Array.isArray(raw.relations) ? raw.relations : []
  if (!Array.isArray(raw.relations)) {
    addFinding(findings, 'invalid-relations', 'relations must be an array', 'relations')
  }
  const relationIds = new Set<string>()
  const relationKeys = new Set<string>()
  const directed = new Map<string, string[]>()
  const parsedRelations: ProfileRelation[] = []
  for (const [index, relation] of relations.entries()) {
    const path = `relations[${index}]`
    if (!isObject(relation)) {
      addFinding(findings, 'invalid-relation', `${path} must be an object`, path)
      continue
    }
    validateAllowedKeys(
      findings,
      relation,
      ['id', 'type', 'from', 'to', 'scopeRule', 'decisionRef'],
      path,
    )
    const id = String(relation.id || '')
    const type = String(relation.type || '') as RelationType
    const from = String(relation.from || '')
    const to = String(relation.to || '')
    const scopeRule = String(relation.scopeRule || '') as ProfileRelation['scopeRule']
    validateStableId(findings, id, `${path}.id`)
    if (relationIds.has(id)) addFinding(findings, 'duplicate-relation-id', `Duplicate relation ${id}`, path)
    relationIds.add(id)
    if (!['requires', 'compatibleWith', 'conflictsWith', 'strengthens'].includes(type)) {
      addFinding(findings, 'invalid-relation-type', `${path}.type is invalid`, `${path}.type`)
    }
    if (!valueRefs.has(from) || !valueRefs.has(to)) {
      addFinding(findings, 'unknown-relation-value', `${path} references an unknown value`, path)
    }
    if (from === to) addFinding(findings, 'self-relation', `${path} cannot relate a value to itself`, path)
    if (!['same', 'overlap', 'explicit-cross-scope'].includes(scopeRule)) {
      addFinding(findings, 'invalid-scope-rule', `${path}.scopeRule is invalid`, `${path}.scopeRule`)
    }
    validateSemanticOwnerReferences(root, findings, [relation.decisionRef], `${path}.decisionRef`, 1)
    const symmetric = ['compatibleWith', 'conflictsWith'].includes(type)
    const endpoints = symmetric ? [from, to].sort() : [from, to]
    const relationKey = `${type}:${endpoints.join('->')}:${scopeRule}`
    if (relationKeys.has(relationKey)) {
      addFinding(findings, 'duplicate-relation', `${path} duplicates another relation`, path)
    }
    relationKeys.add(relationKey)
    if (['requires', 'strengthens'].includes(type)) {
      directed.set(from, [...(directed.get(from) || []), to])
    }
    parsedRelations.push({
      id,
      type,
      from,
      to,
      scopeRule,
      decisionRef: String(relation.decisionRef || ''),
    })
  }

  const visiting = new Set<string>()
  const visited = new Set<string>()
  const visit = (node: string): boolean => {
    if (visiting.has(node)) return true
    if (visited.has(node)) return false
    visiting.add(node)
    for (const next of directed.get(node) || []) {
      if (visit(next)) return true
    }
    visiting.delete(node)
    visited.add(node)
    return false
  }
  for (const node of directed.keys()) {
    if (visit(node)) {
      addFinding(findings, 'relation-cycle', 'requires/strengthens relations must be acyclic', 'relations')
      break
    }
  }

  const semanticOwnerRefs = validateSemanticOwnerReferences(
    root,
    findings,
    raw.semanticOwnerRefs,
    'semanticOwnerRefs',
    1,
  )
  const catalog: ArchitectureProfileCatalog = {
    schemaVersion: 'architecture-profile-catalog/v1',
    catalogId: String(raw.catalogId || ''),
    catalogVersion: String(raw.catalogVersion || ''),
    principleRefs: stringArray(raw.principleRefs),
    projectBaseDimensions: {
      unitTopology: stringArray(isObject(base) ? base.unitTopology : []),
      packageTopology: stringArray(isObject(base) ? base.packageTopology : []),
      deploymentTopology: stringArray(isObject(base) ? base.deploymentTopology : []),
      ownershipTopology: stringArray(isObject(base) ? base.ownershipTopology : []),
    },
    values: parsedValues,
    aliases: parsedAliases,
    relations: parsedRelations,
    semanticOwnerRefs,
  }
  return { catalog, findings }
}

export function loadArchitectureCatalog(root: string): {
  catalog?: ArchitectureProfileCatalog
  findings: ArchitectureFinding[]
} {
  const path = join(root, ARCHITECTURE_CATALOG_PATH)
  if (!existsSync(path)) {
    return {
      findings: [{
        severity: 'error',
        code: 'catalog-missing',
        message: `Architecture profile catalog is missing: ${ARCHITECTURE_CATALOG_PATH}`,
        path: ARCHITECTURE_CATALOG_PATH,
      }],
    }
  }
  return validateCatalogObject(root, readJson(path))
}

function parseHostMap(raw: unknown): HostArchitectureMap | undefined {
  return isObject(raw) ? raw as unknown as HostArchitectureMap : undefined
}

function aliasRefParts(ref: string): { id: string; version: string } | null {
  const index = ref.lastIndexOf('@')
  if (index <= 0) return null
  const id = ref.slice(0, index)
  const version = ref.slice(index + 1)
  return STABLE_ID.test(id) && SEMVER.test(version) ? { id, version } : null
}

function materializedBindingId(instanceId: string, index: number): string {
  const suffix = instanceId.startsWith('alias:')
    ? instanceId.slice('alias:'.length)
    : instanceId.replace(/[.:]/g, '-')
  return `binding:alias:${suffix}:${index + 1}`
}

export function materializeAliases(
  rawMap: HostArchitectureMap,
  catalog: ArchitectureProfileCatalog,
): { map: HostArchitectureMap; findings: ArchitectureFinding[] } {
  const findings: ArchitectureFinding[] = []
  const explicitBindings = Array.isArray(rawMap.bindings)
    ? rawMap.bindings.filter((binding) => !binding.aliasInstanceId)
    : []
  const materialized: ArchitectureBinding[] = []
  const scopes = new Map((rawMap.scopes || []).map((scope) => [scope.id, scope]))
  const aliases = new Map(catalog.aliases.map((alias) => [`${alias.id}@${alias.version}`, alias]))

  for (const [instanceIndex, instance] of (rawMap.aliasInstances || []).entries()) {
    const path = `aliasInstances[${instanceIndex}]`
    if (!isObject(instance)) {
      addFinding(findings, 'invalid-alias-instance', `${path} must be an object`, path)
      continue
    }
    validateStableId(findings, instance.id, `${path}.id`)
    const parsedRef = aliasRefParts(instance.aliasRef)
    const alias = parsedRef ? aliases.get(`${parsedRef.id}@${parsedRef.version}`) : undefined
    if (!alias) {
      addFinding(findings, 'unknown-alias', `${path}.aliasRef is not active in the catalog`, `${path}.aliasRef`)
      continue
    }
    if (alias.status !== 'active') {
      addFinding(findings, 'deprecated-alias', `${path}.aliasRef is deprecated`, `${path}.aliasRef`)
    }
    const parameterKeys = Object.keys(instance.parameters || {}).sort()
    const expectedKeys = alias.parameters.map((parameter) => parameter.name).sort()
    if (stableJson(parameterKeys) !== stableJson(expectedKeys)) {
      addFinding(findings, 'alias-parameter-mismatch', `${path}.parameters must match the alias exactly`, `${path}.parameters`)
      continue
    }
    const expectedBindingIds = alias.bindings.map((_, index) => materializedBindingId(instance.id, index))
    if (stableJson(instance.materializedBindingIds) !== stableJson(expectedBindingIds)) {
      addFinding(
        findings,
        'alias-binding-id-mismatch',
        `${path}.materializedBindingIds must be deterministic: ${expectedBindingIds.join(', ')}`,
        `${path}.materializedBindingIds`,
      )
      continue
    }
    alias.parameters.forEach((parameter) => {
      const scopeId = instance.parameters[parameter.name]
      const scope = scopes.get(scopeId)
      if (!scope) {
        addFinding(findings, 'unknown-alias-scope', `${path} parameter ${parameter.name} references unknown scope ${scopeId}`, path)
      } else if (!parameter.scopeKinds.includes(scope.kind)) {
        addFinding(
          findings,
          'alias-scope-kind-mismatch',
          `${path} parameter ${parameter.name} requires ${parameter.scopeKinds.join('/')} scope`,
          path,
        )
      }
    })
    if (findings.some((finding) => finding.path === path && finding.severity === 'error')) {
      continue
    }
    alias.bindings.forEach((template, index) => {
      materialized.push({
        id: expectedBindingIds[index],
        axis: template.axis,
        valueRef: template.valueRef,
        scopeId: instance.parameters[template.scopeParameter],
        ...(template.condition ? { condition: template.condition } : {}),
        evidenceRefs: [...alias.constraintRefs],
        semanticOwnerRefs: [...template.semanticOwnerRefs],
        aliasInstanceId: instance.id,
        reviewTrigger: `alias ${instance.aliasRef} changes or reaches an exit trigger`,
      })
    })
  }

  return {
    map: {
      ...rawMap,
      bindings: [...explicitBindings, ...materialized],
    },
    findings,
  }
}

function scopeAncestors(scopes: Map<string, ArchitectureScope>, scopeId: string): string[] {
  const result: string[] = []
  const seen = new Set<string>()
  let current: string | null | undefined = scopeId
  while (current) {
    result.push(current)
    if (seen.has(current)) break
    seen.add(current)
    current = scopes.get(current)?.parentId
  }
  return result
}

function scopesOverlap(
  scopes: Map<string, ArchitectureScope>,
  left: string,
  right: string,
): boolean {
  if (left === right) return true
  const leftAncestors = new Set(scopeAncestors(scopes, left))
  const rightAncestors = new Set(scopeAncestors(scopes, right))
  return leftAncestors.has(right) || rightAncestors.has(left)
}

function relationApplies(
  relation: ProfileRelation,
  scopes: Map<string, ArchitectureScope>,
  explicitScopePairs: Set<string>,
  leftScope: string,
  rightScope: string,
 ): boolean {
  if (relation.scopeRule === 'same') return leftScope === rightScope
  if (relation.scopeRule === 'overlap') return scopesOverlap(scopes, leftScope, rightScope)
  return explicitScopePairs.has(pairKey(leftScope, rightScope))
}

function pairKey(left: string, right: string): string {
  return [left, right].sort().join('|')
}

function normalizeHostMap(map: HostArchitectureMap): HostArchitectureMap {
  const sortById = <T extends { id: string }>(values: T[]): T[] =>
    [...values].sort((left, right) => left.id.localeCompare(right.id))
  return {
    ...map,
    principleRefs: [...map.principleRefs].sort(),
    projectBase: {
      ...map.projectBase,
      edges: [...map.projectBase.edges].sort((left, right) =>
        stableJson(left).localeCompare(stableJson(right))),
      evidenceRefs: [...map.projectBase.evidenceRefs].sort(),
    },
    scopes: sortById(map.scopes).map((scope) => ({
      ...scope,
      selectors: [...scope.selectors].sort((left, right) =>
        stableJson(left).localeCompare(stableJson(right))),
      ownerRefs: [...scope.ownerRefs].sort(),
    })),
    bindings: sortById(map.bindings).map((binding) => ({
      ...binding,
      evidenceRefs: [...binding.evidenceRefs].sort(),
      semanticOwnerRefs: [...binding.semanticOwnerRefs].sort(),
    })),
    aliasInstances: sortById(map.aliasInstances).map((instance) => ({
      ...instance,
      parameters: Object.fromEntries(Object.entries(instance.parameters).sort()),
      materializedBindingIds: [...instance.materializedBindingIds],
    })),
    compositionDecisions: sortById(map.compositionDecisions),
    waiverRefs: [...map.waiverRefs].sort(),
    evidenceAdapterRefs: [...map.evidenceAdapterRefs].sort(),
    policyRefs: [...map.policyRefs].sort(),
    capabilityRefs: [...map.capabilityRefs].sort(),
    reviewTriggers: [...map.reviewTriggers].sort(),
  }
}

function validateHostMapObject(
  root: string,
  rawMap: HostArchitectureMap,
  catalog: ArchitectureProfileCatalog,
  canonical: boolean,
): ArchitectureValidationResult {
  const findings: ArchitectureFinding[] = []
  validateAllowedKeys(
    findings,
    rawMap as unknown as Record<string, unknown>,
    [
      'schemaVersion',
      'mapVersion',
      'hostId',
      'catalogRef',
      'status',
      'confirmation',
      'principleRefs',
      'projectBase',
      'scopes',
      'bindings',
      'aliasInstances',
      'compositionDecisions',
      'waiverRefs',
      'evidenceAdapterRefs',
      'policyRefs',
      'capabilityRefs',
      'reviewTriggers',
    ],
    'hostMap',
  )
  if (rawMap.schemaVersion !== 'host-architecture-map/v1') {
    addFinding(findings, 'invalid-schema-version', 'Host map schemaVersion must be host-architecture-map/v1')
  }
  if (!Number.isInteger(rawMap.mapVersion) || rawMap.mapVersion < 1) {
    addFinding(findings, 'invalid-map-version', 'mapVersion must be a positive integer', 'mapVersion')
  }
  validateStableId(findings, rawMap.hostId, 'hostId')
  if (!isObject(rawMap.catalogRef)
    || rawMap.catalogRef.id !== catalog.catalogId
    || rawMap.catalogRef.version !== catalog.catalogVersion) {
    addFinding(findings, 'catalog-ref-mismatch', 'Host map catalogRef must match the active catalog', 'catalogRef')
  } else {
    validateAllowedKeys(findings, rawMap.catalogRef, ['id', 'version'], 'catalogRef')
  }
  if (!['candidate', 'confirmed'].includes(rawMap.status)) {
    addFinding(findings, 'invalid-map-status', 'Host map status must be candidate or confirmed', 'status')
  }
  if (canonical && rawMap.status !== 'confirmed') {
    addFinding(findings, 'canonical-map-not-confirmed', 'Canonical host map must have status=confirmed', 'status')
  }
  if (rawMap.status === 'confirmed') {
    if (!isObject(rawMap.confirmation)
      || typeof rawMap.confirmation.reference !== 'string'
      || !rawMap.confirmation.reference.trim()
      || typeof rawMap.confirmation.confirmedAt !== 'string'
      || Number.isNaN(Date.parse(rawMap.confirmation.confirmedAt))) {
      addFinding(findings, 'missing-confirmation', 'Confirmed map requires confirmation reference and timestamp', 'confirmation')
    } else {
      validateAllowedKeys(
        findings,
        rawMap.confirmation,
        ['reference', 'confirmedAt'],
        'confirmation',
      )
    }
  }
  if (!exactStrings(rawMap.principleRefs, [...catalog.principleRefs].sort())
    && stableJson([...rawMap.principleRefs].sort()) !== stableJson([...catalog.principleRefs].sort())) {
    addFinding(findings, 'principle-ref-mismatch', 'Host map must inherit all six catalog principles', 'principleRefs')
  }

  const base = rawMap.projectBase
  if (!isObject(base)) {
    addFinding(findings, 'missing-project-base', 'Host map requires one projectBase object', 'projectBase')
  } else {
    validateAllowedKeys(
      findings,
      base,
      [
        'unitTopology',
        'packageTopology',
        'deploymentTopology',
        'ownershipTopology',
        'edges',
        'evidenceRefs',
      ],
      'projectBase',
    )
    const dimensions: Array<[
      keyof ArchitectureProfileCatalog['projectBaseDimensions'],
      unknown,
    ]> = [
      ['unitTopology', base.unitTopology],
      ['packageTopology', base.packageTopology],
      ['deploymentTopology', base.deploymentTopology],
      ['ownershipTopology', base.ownershipTopology],
    ]
    for (const [key, value] of dimensions) {
      if (!catalog.projectBaseDimensions[key].includes(String(value))) {
        addFinding(findings, 'invalid-project-base-value', `projectBase.${key} is not catalogued`, `projectBase.${key}`)
      }
    }
    validateReferences(root, findings, base.evidenceRefs, 'projectBase.evidenceRefs', 1)
  }

  const scopesRaw = Array.isArray(rawMap.scopes) ? rawMap.scopes : []
  if (!Array.isArray(rawMap.scopes) || !scopesRaw.length) {
    addFinding(findings, 'missing-scopes', 'Host map requires scopes', 'scopes')
  }
  const scopes = new Map<string, ArchitectureScope>()
  for (const [index, scope] of scopesRaw.entries()) {
    const path = `scopes[${index}]`
    if (!isObject(scope)) {
      addFinding(findings, 'invalid-scope', `${path} must be an object`, path)
      continue
    }
    validateAllowedKeys(
      findings,
      scope,
      ['id', 'kind', 'parentId', 'selectors', 'ownerRefs'],
      path,
    )
    const id = String(scope.id || '')
    validateStableId(findings, id, `${path}.id`)
    if (scopes.has(id)) addFinding(findings, 'duplicate-scope-id', `Duplicate scope ${id}`, path)
    const kind = String(scope.kind) as ScopeKind
    if (!['host', 'unit', 'entrypoint', 'responsibility'].includes(kind)) {
      addFinding(findings, 'invalid-scope-kind', `${path}.kind is invalid`, `${path}.kind`)
    }
    const parentId = scope.parentId === null ? null : String(scope.parentId || '')
    if (parentId !== null) validateStableId(findings, parentId, `${path}.parentId`)
    const selectors = Array.isArray(scope.selectors)
      ? scope.selectors.filter(isObject).map((selector) => ({
        kind: String(selector.kind) as ArchitectureScope['selectors'][number]['kind'],
        value: String(selector.value || ''),
      }))
      : []
    if (!Array.isArray(scope.selectors) || selectors.length !== scope.selectors.length) {
      addFinding(findings, 'invalid-selectors', `${path}.selectors must be an array`, `${path}.selectors`)
    }
    for (const [selectorIndex, selector] of selectors.entries()) {
      const selectorPath = `${path}.selectors[${selectorIndex}]`
      const rawSelector = Array.isArray(scope.selectors)
        ? scope.selectors[selectorIndex]
        : undefined
      if (isObject(rawSelector)) {
        validateAllowedKeys(findings, rawSelector, ['kind', 'value'], selectorPath)
      }
      if (!['path', 'package', 'process', 'service', 'deployment'].includes(selector.kind)
        || !selector.value.trim()) {
        addFinding(findings, 'invalid-selector', `${selectorPath} is invalid`, selectorPath)
      }
      if (selector.kind === 'path'
        && (selector.value.startsWith('/') || selector.value.split('/').includes('..'))) {
        addFinding(findings, 'unsafe-path-selector', `${selectorPath} must be relative and root-bound`, selectorPath)
      }
    }
    const ownerRefs = validateSemanticOwnerReferences(
      root,
      findings,
      scope.ownerRefs,
      `${path}.ownerRefs`,
      1,
    )
    scopes.set(id, { id, kind, parentId, selectors, ownerRefs })
  }
  const hostScopes = [...scopes.values()].filter((scope) => scope.kind === 'host')
  if (hostScopes.length !== 1 || hostScopes[0]?.parentId !== null) {
    addFinding(findings, 'invalid-host-scope', 'Host map requires exactly one parentless host scope', 'scopes')
  }
  for (const scope of scopes.values()) {
    if (scope.kind !== 'host' && (!scope.parentId || !scopes.has(scope.parentId))) {
      addFinding(findings, 'unknown-parent-scope', `Scope ${scope.id} has an unknown parent`, `scopes.${scope.id}`)
    }
    const ancestors = scopeAncestors(scopes, scope.id)
    if (new Set(ancestors).size !== ancestors.length) {
      addFinding(findings, 'scope-cycle', `Scope ${scope.id} participates in a parent cycle`, `scopes.${scope.id}`)
    }
  }

  const edgeKeys = new Set<string>()
  const explicitScopePairs = new Set<string>()
  for (const [index, edge] of (base?.edges || []).entries()) {
    const path = `projectBase.edges[${index}]`
    if (!isObject(edge)) {
      addFinding(findings, 'invalid-project-edge', `${path} must be an object`, path)
      continue
    }
    validateAllowedKeys(
      findings,
      edge,
      ['fromScopeId', 'toScopeId', 'relation'],
      path,
    )
    const from = String(edge.fromScopeId || '')
    const to = String(edge.toScopeId || '')
    const relation = String(edge.relation || '')
    if (!scopes.has(from) || !scopes.has(to) || from === to) {
      addFinding(findings, 'invalid-project-edge-scope', `${path} has invalid endpoints`, path)
    }
    if (!['depends-on', 'owns', 'deploys-with', 'publishes-to'].includes(relation)) {
      addFinding(findings, 'invalid-project-edge-relation', `${path}.relation is invalid`, `${path}.relation`)
    }
    const key = `${from}|${relation}|${to}`
    if (edgeKeys.has(key)) addFinding(findings, 'duplicate-project-edge', `${path} duplicates another edge`, path)
    edgeKeys.add(key)
    explicitScopePairs.add(pairKey(from, to))
  }

  const valueByRef = new Map(catalog.values.map((value) => [`${value.id}@${value.version}`, value]))
  const bindingsRaw = Array.isArray(rawMap.bindings) ? rawMap.bindings : []
  if (!Array.isArray(rawMap.bindings)) {
    addFinding(findings, 'invalid-bindings', 'bindings must be an array', 'bindings')
  }
  const bindings = new Map<string, ArchitectureBinding>()
  for (const [index, binding] of bindingsRaw.entries()) {
    const path = `bindings[${index}]`
    if (!isObject(binding)) {
      addFinding(findings, 'invalid-binding', `${path} must be an object`, path)
      continue
    }
    validateAllowedKeys(
      findings,
      binding,
      [
        'id',
        'axis',
        'valueRef',
        'scopeId',
        'condition',
        'evidenceRefs',
        'semanticOwnerRefs',
        'aliasInstanceId',
        'reviewTrigger',
      ],
      path,
    )
    const id = String(binding.id || '')
    const axis = String(binding.axis || '') as ArchitectureAxis
    const valueRef = String(binding.valueRef || '')
    const scopeId = String(binding.scopeId || '')
    validateStableId(findings, id, `${path}.id`)
    if (bindings.has(id)) addFinding(findings, 'duplicate-binding-id', `Duplicate binding ${id}`, path)
    if (!['runtime', 'organization', 'operational'].includes(axis)) {
      addFinding(findings, 'invalid-binding-axis', `${path}.axis is invalid`, `${path}.axis`)
    }
    const value = valueByRef.get(valueRef)
    if (!value) {
      addFinding(findings, 'unknown-binding-value', `${path}.valueRef is not in the active catalog`, `${path}.valueRef`)
    } else if (value.axis !== axis) {
      addFinding(findings, 'binding-axis-mismatch', `${path}.axis does not match its value`, path)
    }
    const scope = scopes.get(scopeId)
    if (!scope) {
      addFinding(findings, 'unknown-binding-scope', `${path}.scopeId does not resolve`, `${path}.scopeId`)
    } else if (axis === 'runtime' && scope.kind !== 'entrypoint') {
      addFinding(findings, 'runtime-scope-kind', `${path} runtime binding requires an entrypoint scope`, path)
    } else if (axis === 'organization' && !['unit', 'responsibility'].includes(scope.kind)) {
      addFinding(findings, 'organization-scope-kind', `${path} organization binding requires a unit or responsibility scope`, path)
    }
    if (axis === 'operational'
      && (typeof binding.condition !== 'string' || !binding.condition.trim())) {
      addFinding(findings, 'missing-operational-condition', `${path}.condition is required`, `${path}.condition`)
    }
    const evidenceRefs = validateReferences(root, findings, binding.evidenceRefs, `${path}.evidenceRefs`, 1)
    const semanticOwnerRefs = validateSemanticOwnerReferences(
      root,
      findings,
      binding.semanticOwnerRefs,
      `${path}.semanticOwnerRefs`,
      1,
    )
    if (typeof binding.reviewTrigger !== 'string' || !binding.reviewTrigger.trim()) {
      addFinding(findings, 'missing-review-trigger', `${path}.reviewTrigger is required`, `${path}.reviewTrigger`)
    }
    bindings.set(id, {
      id,
      axis,
      valueRef,
      scopeId,
      ...(typeof binding.condition === 'string' ? { condition: binding.condition } : {}),
      evidenceRefs,
      semanticOwnerRefs,
      ...(typeof binding.aliasInstanceId === 'string'
        ? { aliasInstanceId: binding.aliasInstanceId }
        : {}),
      reviewTrigger: String(binding.reviewTrigger || ''),
    })
  }

  for (const scope of scopes.values()) {
    const scopedBindings = [...bindings.values()].filter((binding) => binding.scopeId === scope.id)
    if (scope.kind === 'entrypoint') {
      const runtimeCount = scopedBindings.filter((binding) => binding.axis === 'runtime').length
      if (runtimeCount !== 1) {
        addFinding(
          findings,
          'runtime-cardinality',
          `Entrypoint ${scope.id} requires exactly one runtime binding; found ${runtimeCount}`,
          `scopes.${scope.id}`,
        )
      }
    }
    const organizationCount = scopedBindings.filter((binding) => binding.axis === 'organization').length
    if (scope.kind === 'responsibility' && organizationCount !== 1) {
      addFinding(
        findings,
        'organization-cardinality',
        `Responsibility ${scope.id} requires exactly one organization binding; found ${organizationCount}`,
        `scopes.${scope.id}`,
      )
    } else if (organizationCount > 1) {
      addFinding(
        findings,
        'organization-cardinality',
        `Scope ${scope.id} has more than one primary organization binding`,
        `scopes.${scope.id}`,
      )
    }
  }

  const aliasInstances = Array.isArray(rawMap.aliasInstances) ? rawMap.aliasInstances : []
  const aliasInstanceIds = new Set<string>()
  for (const [index, instance] of aliasInstances.entries()) {
    const path = `aliasInstances[${index}]`
    if (!isObject(instance)) {
      addFinding(findings, 'invalid-alias-instance', `${path} must be an object`, path)
      continue
    }
    validateAllowedKeys(
      findings,
      instance,
      ['id', 'aliasRef', 'parameters', 'materializedBindingIds'],
      path,
    )
    const id = String(instance.id || '')
    validateStableId(findings, id, `${path}.id`)
    if (aliasInstanceIds.has(id)) addFinding(findings, 'duplicate-alias-instance', `Duplicate alias instance ${id}`, path)
    aliasInstanceIds.add(id)
    for (const bindingId of stringArray(instance.materializedBindingIds)) {
      const binding = bindings.get(bindingId)
      if (!binding || binding.aliasInstanceId !== id) {
        addFinding(findings, 'missing-materialized-binding', `${path} does not resolve binding ${bindingId}`, path)
      }
    }
  }

  const decisionsRaw = Array.isArray(rawMap.compositionDecisions)
    ? rawMap.compositionDecisions
    : []
  const decisionsByPair = new Map<string, ArchitectureCompositionDecision>()
  for (const [index, decision] of decisionsRaw.entries()) {
    const path = `compositionDecisions[${index}]`
    if (!isObject(decision)) {
      addFinding(findings, 'invalid-composition-decision', `${path} must be an object`, path)
      continue
    }
    validateAllowedKeys(
      findings,
      decision,
      [
        'id',
        'leftBindingId',
        'rightBindingId',
        'scopeId',
        'outcome',
        'decisionRef',
      ],
      path,
    )
    const id = String(decision.id || '')
    const leftBindingId = String(decision.leftBindingId || '')
    const rightBindingId = String(decision.rightBindingId || '')
    const scopeId = String(decision.scopeId || '')
    validateStableId(findings, id, `${path}.id`)
    if (!bindings.has(leftBindingId) || !bindings.has(rightBindingId)
      || leftBindingId === rightBindingId) {
      addFinding(findings, 'invalid-decision-bindings', `${path} references invalid bindings`, path)
    }
    if (!scopes.has(scopeId)) {
      addFinding(findings, 'invalid-decision-scope', `${path}.scopeId is unknown`, `${path}.scopeId`)
    }
    if (!['accepted-compatible', 'accepted-with-waiver'].includes(String(decision.outcome))) {
      addFinding(findings, 'invalid-decision-outcome', `${path}.outcome is invalid`, `${path}.outcome`)
    }
    validateSemanticOwnerReferences(root, findings, [decision.decisionRef], `${path}.decisionRef`, 1)
    const key = pairKey(leftBindingId, rightBindingId)
    if (decisionsByPair.has(key)) {
      addFinding(findings, 'duplicate-composition-decision', `${path} duplicates a binding pair`, path)
    }
    decisionsByPair.set(key, {
      id,
      leftBindingId,
      rightBindingId,
      scopeId,
      outcome: decision.outcome as ArchitectureCompositionDecision['outcome'],
      decisionRef: String(decision.decisionRef || ''),
    })
  }

  const activeBindings = [...bindings.values()]
  for (const relation of catalog.relations) {
    const fromBindings = activeBindings.filter((binding) => binding.valueRef === relation.from)
    const toBindings = activeBindings.filter((binding) => binding.valueRef === relation.to)
    if (relation.type === 'requires' || relation.type === 'strengthens') {
      for (const fromBinding of fromBindings) {
        const matches = toBindings.filter((toBinding) =>
          relationApplies(
            relation,
            scopes,
            explicitScopePairs,
            fromBinding.scopeId,
            toBinding.scopeId,
          ))
        if (!matches.length) {
          addFinding(
            findings,
            relation.type === 'requires' ? 'missing-required-binding' : 'missing-strengthened-binding',
            `${fromBinding.valueRef} ${relation.type} ${relation.to} in ${relation.scopeRule} scope`,
            `bindings.${fromBinding.id}`,
          )
        }
      }
    }
    if (relation.type === 'conflictsWith') {
      for (const left of fromBindings) {
        for (const right of toBindings) {
          if (relationApplies(
            relation,
            scopes,
            explicitScopePairs,
            left.scopeId,
            right.scopeId,
          )) {
            addFinding(
              findings,
              'conflicting-bindings',
              `${left.valueRef} conflicts with ${right.valueRef} in overlapping scope`,
              `bindings.${left.id}`,
            )
          }
        }
      }
    }
  }

  for (let leftIndex = 0; leftIndex < activeBindings.length; leftIndex += 1) {
    for (let rightIndex = leftIndex + 1; rightIndex < activeBindings.length; rightIndex += 1) {
      const left = activeBindings[leftIndex]
      const right = activeBindings[rightIndex]
      if (left.axis !== right.axis || left.valueRef === right.valueRef) continue
      if (!scopesOverlap(scopes, left.scopeId, right.scopeId)) continue
      const known = catalog.relations.some((relation) => {
        const direct = relation.from === left.valueRef && relation.to === right.valueRef
        const reverse = relation.from === right.valueRef && relation.to === left.valueRef
        if (direct) {
          return relationApplies(
            relation,
            scopes,
            explicitScopePairs,
            left.scopeId,
            right.scopeId,
          )
        }
        if (reverse) {
          return relationApplies(
            relation,
            scopes,
            explicitScopePairs,
            right.scopeId,
            left.scopeId,
          )
        }
        return false
      })
      if (!known && !decisionsByPair.has(pairKey(left.id, right.id))) {
        addFinding(
          findings,
          'unknown-composition',
          `Undocumented overlapping composition ${left.valueRef} + ${right.valueRef} requires a decision ref`,
          `bindings.${left.id}`,
        )
      }
    }
  }

  for (const [field, refs] of [
    ['waiverRefs', rawMap.waiverRefs],
    ['evidenceAdapterRefs', rawMap.evidenceAdapterRefs],
    ['policyRefs', rawMap.policyRefs],
    ['capabilityRefs', rawMap.capabilityRefs],
  ] as const) {
    validateReferences(root, findings, refs, field, 0)
  }
  if (!Array.isArray(rawMap.reviewTriggers)
    || !rawMap.reviewTriggers.length
    || rawMap.reviewTriggers.some((value) => typeof value !== 'string' || !value.trim())) {
    addFinding(findings, 'invalid-review-triggers', 'reviewTriggers must contain non-empty strings', 'reviewTriggers')
  }

  return {
    ok: !findings.some((finding) => finding.severity === 'error'),
    findings,
  }
}

export function loadHostArchitectureMap(root: string): HostArchitectureMap | null {
  const path = join(root, HOST_ARCHITECTURE_MAP_PATH)
  if (!existsSync(path)) return null
  const raw = parseHostMap(readJson(path))
  if (!raw) {
    throw new ArchitectureContractError('Host architecture map must be a JSON object')
  }
  return raw
}

function proposalFromPath(path: string): HostArchitectureMap {
  const raw = parseHostMap(readJson(path))
  if (!raw) throw new ArchitectureContractError('Architecture proposal must be a JSON object')
  return raw
}

export function inspectArchitecture(root: string): ArchitectureInspectResult {
  const catalogResult = loadArchitectureCatalog(root)
  const findings = [...catalogResult.findings]
  const catalog = catalogResult.catalog
  let hostMap: ArchitectureInspectResult['hostMap'] = {
    exists: false,
    status: 'missing',
  }
  const mapPath = join(root, HOST_ARCHITECTURE_MAP_PATH)
  if (existsSync(mapPath)) {
    try {
      const rawMap = loadHostArchitectureMap(root)
      if (rawMap && catalog) {
        const materialized = materializeAliases(rawMap, catalog)
        const normalized = normalizeHostMap(materialized.map)
        const validation = validateHostMapObject(root, normalized, catalog, true)
        findings.push(...materialized.findings, ...validation.findings)
        hostMap = {
          exists: true,
          status: validation.ok ? 'confirmed' : 'invalid',
          hostId: normalized.hostId,
          mapVersion: normalized.mapVersion,
          digest: architectureDigest(normalized),
        }
      } else {
        hostMap = { exists: true, status: 'invalid' }
      }
    } catch (error) {
      addFinding(
        findings,
        'host-map-read-failed',
        error instanceof Error ? error.message : String(error),
        HOST_ARCHITECTURE_MAP_PATH,
      )
      hostMap = { exists: true, status: 'invalid' }
    }
  }
  return {
    ok: !findings.some((finding) => finding.severity === 'error'),
    mode: 'architecture.inspect',
    schemaVersion: 'architecture-inspect/v1',
    root,
    catalogPath: ARCHITECTURE_CATALOG_PATH,
    mapPath: HOST_ARCHITECTURE_MAP_PATH,
    catalog: {
      id: catalog?.catalogId,
      version: catalog?.catalogVersion,
      valueCount: catalog?.values.length || 0,
      aliasCount: catalog?.aliases.length || 0,
      relationCount: catalog?.relations.length || 0,
      ...(catalog ? { digest: architectureDigest(catalog) } : {}),
    },
    hostMap,
    findings,
    writes: [],
    notice: hostMap.exists
      ? 'Inspect reports confirmed host architecture truth and validation only.'
      : 'No confirmed host map exists; architecture remains unclassified, not simple-direct.',
  }
}

export function buildArchitecturePlan(
  root: string,
  proposalFile: string,
): ArchitecturePlanResult {
  const proposalPath = isAbsolute(proposalFile)
    ? resolve(proposalFile)
    : resolve(root, proposalFile)
  const catalogResult = loadArchitectureCatalog(root)
  const findings = [...catalogResult.findings]
  const catalog = catalogResult.catalog
  const baseline = loadHostArchitectureMap(root)
  const baselineDigest = architectureDigest(baseline ? normalizeHostMap(baseline) : null)
  const catalogDigest = architectureDigest(catalog || null)
  let normalizedMap: HostArchitectureMap | undefined

  if (catalog) {
    const rawProposal = proposalFromPath(proposalPath)
    const materialized = materializeAliases(rawProposal, catalog)
    findings.push(...materialized.findings)
    normalizedMap = normalizeHostMap(materialized.map)
    const validation = validateHostMapObject(root, normalizedMap, catalog, false)
    findings.push(...validation.findings)
    if (baseline) {
      const currentMaterialized = materializeAliases(baseline, catalog)
      findings.push(...currentMaterialized.findings)
      const currentValidation = validateHostMapObject(
        root,
        normalizeHostMap(currentMaterialized.map),
        catalog,
        true,
      )
      findings.push(...currentValidation.findings.map((finding) => ({
        ...finding,
        path: finding.path ? `baseline.${finding.path}` : 'baseline',
      })))
      if (normalizedMap.mapVersion !== baseline.mapVersion + 1) {
        addFinding(
          findings,
          'map-version-stale',
          `Proposal mapVersion must be ${baseline.mapVersion + 1} for the current baseline`,
          'mapVersion',
        )
      }
    } else if (normalizedMap.mapVersion !== 1) {
      addFinding(findings, 'initial-map-version', 'Initial host map must use mapVersion=1', 'mapVersion')
    }
  }

  const proposalDigest = architectureDigest(normalizedMap || null)
  const planDigest = architectureDigest({
    schemaVersion: 'architecture-plan/v1',
    catalogRef: catalog
      ? { id: catalog.catalogId, version: catalog.catalogVersion }
      : null,
    catalogDigest,
    baselineDigest,
    proposalDigest,
  })
  const errors = findings.filter((finding) => finding.severity === 'error')
  return {
    ok: errors.length === 0,
    mode: 'architecture.plan',
    schemaVersion: 'architecture-plan/v1',
    root,
    proposalPath,
    catalogPath: ARCHITECTURE_CATALOG_PATH,
    mapPath: HOST_ARCHITECTURE_MAP_PATH,
    baselineDigest,
    proposalDigest,
    catalogDigest,
    planDigest,
    ...(catalog ? { catalogRef: { id: catalog.catalogId, version: catalog.catalogVersion } } : {}),
    ...(normalizedMap ? { normalizedMap } : {}),
    findings,
    unresolved: findings.filter((finding) =>
      ['unknown-composition', 'conflicting-bindings'].includes(finding.code)),
    writes: errors.length
      ? []
      : [{
        path: HOST_ARCHITECTURE_MAP_PATH,
        action: baseline ? 'replace' : 'create',
        requiresConfirmation: true,
      }],
  }
}

function atomicWrite(path: string, content: string): void {
  mkdirSync(dirname(path), { recursive: true })
  const tempPath = `${path}.tmp-${process.pid}-${Date.now()}`
  try {
    writeFileSync(tempPath, content, { encoding: 'utf8', mode: 0o600 })
    renameSync(tempPath, path)
  } catch (error) {
    rmSync(tempPath, { force: true })
    throw error
  }
}

export function applyArchitecturePlan(
  root: string,
  proposalFile: string,
  confirmedPlanDigest: string,
  confirmationRef: string,
): ArchitectureApplyResult {
  if (!confirmedPlanDigest || !/^[a-f0-9]{64}$/.test(confirmedPlanDigest)) {
    throw new ArchitectureContractError(
      'apply requires --confirm <64-character plan digest>; bare confirmation is rejected',
    )
  }
  if (!confirmationRef.trim()) {
    throw new ArchitectureContractError('apply requires --confirmation-ref <reference>')
  }
  const plan = buildArchitecturePlan(root, proposalFile)
  if (!plan.ok || !plan.normalizedMap) {
    throw new ArchitectureContractError(
      'Architecture plan has unresolved validation errors',
      plan.findings,
    )
  }
  if (plan.planDigest !== confirmedPlanDigest) {
    throw new ArchitectureContractError(
      `Plan digest mismatch or stale baseline: expected ${plan.planDigest}`,
      plan.findings,
    )
  }
  const confirmedMap: HostArchitectureMap = normalizeHostMap({
    ...plan.normalizedMap,
    status: 'confirmed',
    confirmation: {
      reference: confirmationRef,
      confirmedAt: new Date().toISOString(),
    },
  })
  const catalogResult = loadArchitectureCatalog(root)
  if (!catalogResult.catalog) {
    throw new ArchitectureContractError('Architecture catalog is unavailable', catalogResult.findings)
  }
  const validation = validateHostMapObject(root, confirmedMap, catalogResult.catalog, true)
  if (!validation.ok) {
    throw new ArchitectureContractError('Confirmed host map failed final validation', validation.findings)
  }
  const mapPath = join(root, HOST_ARCHITECTURE_MAP_PATH)
  const lockPath = `${mapPath}.lock`
  mkdirSync(dirname(mapPath), { recursive: true })
  let lockFd: number
  try {
    lockFd = openSync(lockPath, 'wx', 0o600)
  } catch (error) {
    const code = isObject(error) ? error.code : undefined
    throw new ArchitectureContractError(
      code === 'EEXIST'
        ? 'Host Architecture Map writer is locked by another apply'
        : `Cannot acquire Host Architecture Map writer lock: ${error instanceof Error ? error.message : String(error)}`,
      [],
      code === 'EEXIST' ? 2 : 1,
    )
  }
  try {
    const latestCatalogResult = loadArchitectureCatalog(root)
    const latestCatalogDigest = architectureDigest(latestCatalogResult.catalog || null)
    if (
      !latestCatalogResult.catalog
      || latestCatalogResult.findings.some((finding) => finding.severity === 'error')
      || latestCatalogDigest !== plan.catalogDigest
    ) {
      throw new ArchitectureContractError(
        'Plan digest mismatch or stale catalog: catalog changed before atomic write',
        latestCatalogResult.findings,
      )
    }
    const latestBaseline = loadHostArchitectureMap(root)
    const latestBaselineDigest = architectureDigest(
      latestBaseline ? normalizeHostMap(latestBaseline) : null,
    )
    if (latestBaselineDigest !== plan.baselineDigest) {
      throw new ArchitectureContractError(
        'Plan digest mismatch or stale baseline: Host Architecture Map changed before atomic write',
      )
    }
    atomicWrite(mapPath, JSON.stringify(confirmedMap, null, 2) + '\n')
  } finally {
    closeSync(lockFd)
    rmSync(lockPath, { force: true })
  }
  return {
    ok: true,
    mode: 'architecture.apply',
    schemaVersion: 'architecture-apply/v1',
    root,
    planDigest: plan.planDigest,
    baselineDigest: plan.baselineDigest,
    mapPath: HOST_ARCHITECTURE_MAP_PATH,
    mapDigest: architectureDigest(confirmedMap),
    status: 'confirmed',
    confirmationRef,
    writes: [{ path: HOST_ARCHITECTURE_MAP_PATH, action: 'written' }],
  }
}
