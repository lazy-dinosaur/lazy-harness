#!/usr/bin/env bun
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

export type RecordReaderMode = "candidate-map" | "claim-evidence";

type JsonObject = Record<string, unknown>;
type JsonSchema = Record<string, unknown>;

export interface RecordReaderAdmissionContract {
  schemaVersion: "record-reader-admission/v1";
  mode: RecordReaderMode;
  identity: Record<string, string>;
  objective: string;
  concreteNodes: string[];
  allowedLayers: string[];
  governingRecordsReadByParent: string[];
  riskConstraints: string[];
  explicitExclusionIds: string[];
  budget: {
    outputCharacters: number;
    records: number;
    toolCalls: number;
    questions?: number;
    claims?: number;
    seedNodes?: number;
    dependencyEdges?: number;
    proposedBundles?: number;
  };
  objectiveFacetIds?: string[];
  inventoryEntryIds?: string[];
  approvedQuestionIds?: string[];
  assignedFacetIds?: string[];
  approvedSeedNodes?: string[];
  terminalDependencyIds?: string[];
  sharedEvidenceOwners?: string[];
}

interface CompactDescriptionEntry { id: string; description: string; }
interface CompactNodeEntry { id: string; node: string; }
interface CompactVerificationEntry { id: string; target: string; }

export interface CompactRecordReaderAdmissionContract {
  schemaVersion: "record-reader-admission/v2";
  mode: RecordReaderMode;
  contractDigest: string;
  identity: Record<string, string>;
  objective: string;
  facets: CompactDescriptionEntry[];
  inventoryEntries: CompactDescriptionEntry[];
  nodes: CompactNodeEntry[];
  verificationCandidates: CompactVerificationEntry[];
  allowedLayers: string[];
  governingRecordsReadByParent: string[];
  riskConstraints: string[];
  explicitExclusionIds: string[];
  budget: {
    targetOutputCharacters: number;
    hardOutputCharacters: number;
    records: number;
    toolCalls: number;
    questions?: number;
    claims?: number;
    seedNodes?: number;
    dependencyEdges?: number;
    proposedBundles?: number;
  };
  approvedQuestionIds?: string[];
  assignedFacetIds?: string[];
  approvedSeedNodeIds?: string[];
  terminalDependencyIds?: string[];
  sharedEvidenceOwnerIds?: string[];
}

export type AnyRecordReaderAdmissionContract = RecordReaderAdmissionContract | CompactRecordReaderAdmissionContract;

export interface RecordReaderAdmissionReceipt {
  schemaVersion: "record-reader-admission-receipt/v1" | "record-reader-admission-receipt/v2";
  valid: boolean;
  success: boolean;
  reportedStatus?: string;
  admittedStatus: string;
  outputCharacters: number;
  outputCharacterBudget: number;
  outputCharacterTarget?: number;
  outputCharacterHardLimit?: number;
  overTarget?: boolean;
  outputMeasurement: "compact-json-unicode-code-points/v1";
  violations: string[];
  warnings?: string[];
}

const COMMON_STATUSES = ["stale-root-or-epoch", "invalid-packet", "incomplete", "overflow"];
const CANDIDATE_STATUSES = ["proposal-ready", ...COMMON_STATUSES];
const CLAIM_STATUSES = ["complete", "needs-remap", "conflict", "blocked-by-dependency", ...COMMON_STATUSES];
const ROLE_CEILINGS = {
  "candidate-map": { outputCharacters: 6_000, records: 6, toolCalls: 14, questions: 6, seedNodes: 12, dependencyEdges: 8, proposedBundles: 3 },
  "claim-evidence": { outputCharacters: 8_000, records: 8, toolCalls: 14, claims: 6 },
} as const;
const REQUIRED_IDENTITY_KEYS = [
  "packetVersion",
  "mode",
  "modelRoute",
  "workUnitId",
  "packetId",
  "parentPacketId",
  "root",
  "revision",
  "canonicalSnapshotId",
  "overviewFingerprint",
  "parentEvidenceEpoch",
] as const;
const CLAIM_IDENTITY_KEYS = ["candidateMapId", "evidenceBundleId"] as const;
const ALLOWED_LAYERS = ["domain", "spec", "behavior", "tests", "decisions", "ssot", "planning", "plans"] as const;
const MAX_CANDIDATE_COVERAGE_INPUTS = 32;
const MAX_CLAIM_REFERENCES = 16;
const COMPACT_TARGET_MAX = 6_000;
const COMPACT_HARD_MAX = 12_000;
const COMPACT_TEXT_MAX = 600;
const COMPACT_DETAIL_MAX = 300;
const COMPACT_RISK_MAX = 300;
const COMPACT_ID_PATTERNS = {
  facet: "^F[1-9][0-9]*$",
  inventory: "^I[1-9][0-9]*$",
  node: "^N[1-9][0-9]*$",
  verification: "^V[1-9][0-9]*$",
  record: "^R[1-9][0-9]*$",
  question: "^Q[1-9][0-9]*$",
  claim: "^C[1-9][0-9]*$",
  bundle: "^B[1-9][0-9]*$",
  dependency: "^D[1-9][0-9]*$",
} as const;

function isObject(value: unknown): value is JsonObject {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function stringArray(value: unknown): string[] {
  return Array.isArray(value) && value.every((entry) => typeof entry === "string") ? value : [];
}

function objectArray(value: unknown): JsonObject[] {
  return Array.isArray(value) && value.every(isObject) ? value : [];
}

function unique(values: string[]): string[] {
  return [...new Set(values)];
}

function nonEmptyStringSchema(extra: JsonObject = {}): JsonSchema {
  return { type: "string", minLength: 1, ...extra };
}

function stringArraySchema(maxItems = 64, minItems = 0): JsonSchema {
  return { type: "array", items: nonEmptyStringSchema(), minItems, maxItems, uniqueItems: true };
}

function provenanceSchema(): JsonSchema {
  return {
    type: "object",
    properties: {
      path: nonEmptyStringSchema(),
      contentHash: nonEmptyStringSchema({ pattern: "^[0-9a-f]{40,64}$" }),
      ranges: { type: "array", items: nonEmptyStringSchema(), minItems: 1, maxItems: 12 },
    },
    required: ["path", "contentHash", "ranges"],
    additionalProperties: false,
  };
}

function newEvidenceQuestionSchema(): JsonSchema {
  return {
    type: "object",
    properties: {
      questionId: nonEmptyStringSchema(),
      question: nonEmptyStringSchema(),
      reason: nonEmptyStringSchema(),
      cueOrigins: stringArraySchema(32, 1),
      provenance: { type: "array", items: provenanceSchema(), minItems: 1, maxItems: 4 },
    },
    required: ["questionId", "question", "reason", "cueOrigins", "provenance"],
    additionalProperties: false,
  };
}

function commonProperties(contract: RecordReaderAdmissionContract): Record<string, JsonSchema> {
  const identity = Object.fromEntries(Object.entries(contract.identity).map(([key, value]) => [
    key,
    { type: "string", const: value },
  ]));
  return {
    ...identity,
    status: { type: "string", enum: contract.mode === "candidate-map" ? CANDIDATE_STATUSES : CLAIM_STATUSES },
    statusJustification: nonEmptyStringSchema(),
    recordsRead: {
      type: "array",
      items: provenanceSchema(),
      maxItems: contract.budget.records,
    },
    consideredNodes: stringArraySchema(64),
    notRead: {
      type: "array",
      items: {
        type: "object",
        properties: { node: nonEmptyStringSchema(), reason: nonEmptyStringSchema() },
        required: ["node", "reason"],
        additionalProperties: false,
      },
      maxItems: 64,
    },
    parentMustRead: { type: "array", items: nonEmptyStringSchema(), maxItems: 4, uniqueItems: true },
    implementationVerificationNeeded: stringArraySchema(64),
    overflow: {
      anyOf: [
        { type: "null" },
        {
          type: "object",
          properties: { reason: nonEmptyStringSchema(), limit: { type: "string" } },
          required: ["reason"],
          additionalProperties: false,
        },
      ],
    },
  };
}

function candidateProperties(contract: RecordReaderAdmissionContract): Record<string, JsonSchema> {
  const questionLimit = contract.budget.questions!;
  const seedLimit = contract.budget.seedNodes!;
  const dependencyLimit = contract.budget.dependencyEdges!;
  const bundleLimit = contract.budget.proposedBundles!;
  return {
    evidenceQuestions: {
      type: "array",
      minItems: 0,
      maxItems: questionLimit,
      items: {
        type: "object",
        properties: {
          questionId: nonEmptyStringSchema(),
          state: { type: "string", const: "unverified" },
          question: nonEmptyStringSchema(),
          facets: stringArraySchema(32),
          inventoryEntries: stringArraySchema(32),
          cueOrigins: stringArraySchema(32, 1),
          provenance: { type: "array", items: provenanceSchema(), minItems: 1, maxItems: 4 },
          seedNodes: stringArraySchema(seedLimit, 1),
          allowedLayers: stringArraySchema(8, 1),
          overlapKeys: stringArraySchema(16),
          risks: stringArraySchema(16),
          implementationVerificationNeeded: stringArraySchema(32),
        },
        required: ["questionId", "state", "question", "facets", "inventoryEntries", "cueOrigins", "provenance", "seedNodes", "allowedLayers", "overlapKeys", "risks", "implementationVerificationNeeded"],
        additionalProperties: false,
      },
    },
    coverageDispositions: {
      type: "array",
      items: {
        type: "object",
        properties: {
          inputId: nonEmptyStringSchema(),
          disposition: { type: "string", enum: ["assigned", "unmapped", "excluded"] },
          questionIds: stringArraySchema(8),
          reason: nonEmptyStringSchema(),
        },
        required: ["inputId", "disposition", "questionIds", "reason"],
        additionalProperties: false,
      },
      maxItems: MAX_CANDIDATE_COVERAGE_INPUTS,
    },
    unmappedFacets: {
      type: "array",
      items: {
        type: "object",
        properties: { inputId: nonEmptyStringSchema(), reason: nonEmptyStringSchema() },
        required: ["inputId", "reason"],
        additionalProperties: false,
      },
      maxItems: MAX_CANDIDATE_COVERAGE_INPUTS,
    },
    rejectedNodes: {
      type: "array",
      items: {
        type: "object",
        properties: { node: nonEmptyStringSchema(), reason: nonEmptyStringSchema() },
        required: ["node", "reason"],
        additionalProperties: false,
      },
      maxItems: 32,
    },
    overlapGroups: {
      type: "array",
      items: {
        type: "object",
        properties: { groupId: nonEmptyStringSchema(), questionIds: stringArraySchema(16), reason: nonEmptyStringSchema() },
        required: ["groupId", "questionIds", "reason"],
        additionalProperties: false,
      },
      maxItems: 16,
    },
    cycles: stringArraySchema(16),
    proposedBundles: {
      type: "array",
      maxItems: bundleLimit,
      items: {
        type: "object",
        properties: {
          bundleId: nonEmptyStringSchema(),
          questionIds: stringArraySchema(16, 1),
          seedNodes: stringArraySchema(seedLimit, 1),
          allowedLayers: stringArraySchema(8, 1),
          dependencies: stringArraySchema(dependencyLimit),
          sharedEvidenceOwners: stringArraySchema(16),
          reason: nonEmptyStringSchema(),
        },
        required: ["bundleId", "questionIds", "seedNodes", "allowedLayers", "dependencies", "sharedEvidenceOwners", "reason"],
        additionalProperties: false,
      },
    },
    dependencies: stringArraySchema(dependencyLimit),
    proposedExclusions: stringArraySchema(32),
    gaps: stringArraySchema(32),
    routingRecommendation: { type: "string", enum: ["parent-direct", "single-reader", "parallel-candidate"] },
  };
}

function claimProperties(contract: RecordReaderAdmissionContract): Record<string, JsonSchema> {
  return {
    approvedQuestionIds: stringArraySchema(MAX_CLAIM_REFERENCES, 1),
    assignedFacets: stringArraySchema(MAX_CLAIM_REFERENCES, 1),
    dependencies: stringArraySchema(32),
    sharedEvidenceOwner: nonEmptyStringSchema(),
    claims: {
      type: "array",
      maxItems: contract.budget.claims!,
      items: {
        type: "object",
        properties: {
          claimId: nonEmptyStringSchema(),
          questionIds: stringArraySchema(MAX_CLAIM_REFERENCES, 1),
          facets: stringArraySchema(MAX_CLAIM_REFERENCES, 1),
          text: nonEmptyStringSchema(),
          provenance: { type: "array", items: provenanceSchema(), minItems: 1, maxItems: 4 },
        },
        required: ["claimId", "questionIds", "facets", "text", "provenance"],
        additionalProperties: false,
      },
    },
    conflictsSupersession: stringArraySchema(32),
    sharedEvidenceUsed: stringArraySchema(32),
    gaps: stringArraySchema(32),
    newEvidenceQuestions: { type: "array", items: newEvidenceQuestionSchema(), maxItems: 32 },
    overlapObserved: stringArraySchema(32),
    dependencyChanges: stringArraySchema(32),
  };
}

function buildLegacyOutputSchema(contract: RecordReaderAdmissionContract): JsonSchema {
  assertLegacyContract(contract);
  const properties = {
    ...commonProperties(contract),
    ...(contract.mode === "candidate-map" ? candidateProperties(contract) : claimProperties(contract)),
  };
  const commonRequired = [
    ...Object.keys(contract.identity),
    "status",
    "statusJustification",
    "recordsRead",
    "consideredNodes",
    "notRead",
    "parentMustRead",
    "implementationVerificationNeeded",
    "overflow",
  ];
  const modeRequired = contract.mode === "candidate-map"
    ? ["evidenceQuestions", "coverageDispositions", "unmappedFacets", "rejectedNodes", "overlapGroups", "cycles", "proposedBundles", "dependencies", "proposedExclusions", "gaps", "routingRecommendation"]
    : ["approvedQuestionIds", "assignedFacets", "dependencies", "sharedEvidenceOwner", "claims", "conflictsSupersession", "sharedEvidenceUsed", "gaps", "newEvidenceQuestions", "overlapObserved", "dependencyChanges"];
  return { type: "object", properties, required: [...commonRequired, ...modeRequired], additionalProperties: false };
}

function requireContractIds(label: string, value: unknown, allowEmpty = false, maxItems = 64): string[] {
  if (!Array.isArray(value) || (!allowEmpty && value.length === 0)) throw new Error(`contract.${label} must be ${allowEmpty ? "an" : "a non-empty"} array`);
  if (value.length > maxItems) throw new Error(`contract.${label} exceeds ${maxItems} items`);
  if (value.some((entry) => typeof entry !== "string" || !entry)) throw new Error(`contract.${label} must contain non-empty strings`);
  const ids = value as string[];
  if (unique(ids).length !== ids.length) throw new Error(`contract.${label} must contain unique values`);
  return ids;
}

function assertLegacyContract(contract: RecordReaderAdmissionContract): void {
  if (!isObject(contract) || contract.schemaVersion !== "record-reader-admission/v1") throw new Error("contract.schemaVersion must be record-reader-admission/v1");
  if (contract.mode !== "candidate-map" && contract.mode !== "claim-evidence") throw new Error("contract.mode must be candidate-map or claim-evidence");
  if (!isObject(contract.identity) || Object.keys(contract.identity).length === 0) throw new Error("contract.identity must be a non-empty object");
  for (const key of REQUIRED_IDENTITY_KEYS) {
    if (typeof contract.identity[key] !== "string" || !contract.identity[key]) throw new Error(`contract.identity.${key} must be a non-empty string`);
  }
  for (const [key, value] of Object.entries(contract.identity)) {
    if (!key || typeof value !== "string" || !value) throw new Error(`contract.identity.${key} must be a non-empty string`);
  }
  if (contract.identity.packetVersion !== "record-reader/v2") throw new Error("contract.identity.packetVersion must be record-reader/v2");
  if (contract.identity.mode !== contract.mode) throw new Error("contract.identity.mode must equal contract.mode");
  if (contract.mode === "claim-evidence") {
    for (const key of CLAIM_IDENTITY_KEYS) if (typeof contract.identity[key] !== "string" || !contract.identity[key]) throw new Error(`contract.identity.${key} must be a non-empty string`);
  }
  if (typeof contract.objective !== "string" || !contract.objective.trim() || [...contract.objective].length > 2_000) throw new Error("contract.objective must be a non-empty string of at most 2000 characters");
  requireContractIds("concreteNodes", contract.concreteNodes, false, 32);
  const allowedLayers = requireContractIds("allowedLayers", contract.allowedLayers, false, ALLOWED_LAYERS.length);
  for (const layer of allowedLayers) if (!(ALLOWED_LAYERS as readonly string[]).includes(layer)) throw new Error(`contract.allowedLayers contains unsupported layer ${layer}`);
  requireContractIds("governingRecordsReadByParent", contract.governingRecordsReadByParent, false, 32);
  requireContractIds("riskConstraints", contract.riskConstraints, true, 32);
  const exclusions = requireContractIds("explicitExclusionIds", contract.explicitExclusionIds, true, 64);
  if (!isObject(contract.budget)) throw new Error("contract.budget must be an object");

  const limits: ReadonlyArray<readonly [keyof RecordReaderAdmissionContract["budget"], number]> = contract.mode === "candidate-map"
    ? [["outputCharacters", ROLE_CEILINGS["candidate-map"].outputCharacters], ["records", ROLE_CEILINGS["candidate-map"].records], ["toolCalls", ROLE_CEILINGS["candidate-map"].toolCalls], ["questions", ROLE_CEILINGS["candidate-map"].questions], ["seedNodes", ROLE_CEILINGS["candidate-map"].seedNodes], ["dependencyEdges", ROLE_CEILINGS["candidate-map"].dependencyEdges], ["proposedBundles", ROLE_CEILINGS["candidate-map"].proposedBundles]]
    : [["outputCharacters", ROLE_CEILINGS["claim-evidence"].outputCharacters], ["records", ROLE_CEILINGS["claim-evidence"].records], ["toolCalls", ROLE_CEILINGS["claim-evidence"].toolCalls], ["claims", ROLE_CEILINGS["claim-evidence"].claims]];
  for (const [key, ceiling] of limits) {
    const value = contract.budget[key];
    if (!Number.isInteger(value) || Number(value) < 1) throw new Error(`contract.budget.${key} must be a positive integer`);
    if (Number(value) > ceiling) throw new Error(`contract.budget.${key} exceeds ${contract.mode} role ceiling ${ceiling}`);
  }

  if (contract.mode === "candidate-map") {
    const facets = requireContractIds("objectiveFacetIds", contract.objectiveFacetIds, false, 32);
    const inventory = requireContractIds("inventoryEntryIds", contract.inventoryEntryIds, false, 32);
    const allInputs = [...facets, ...inventory];
    if (allInputs.length > MAX_CANDIDATE_COVERAGE_INPUTS) throw new Error(`candidate coverage inputs exceed ${MAX_CANDIDATE_COVERAGE_INPUTS} total items`);
    if (unique(allInputs).length !== allInputs.length) throw new Error("candidate coverage input ids must be unique across objectiveFacetIds and inventoryEntryIds");
    for (const id of exclusions) if (!allInputs.includes(id)) throw new Error(`contract.explicitExclusionIds contains unknown coverage input ${id}`);
  } else {
    const questions = requireContractIds("approvedQuestionIds", contract.approvedQuestionIds, false, MAX_CLAIM_REFERENCES);
    const facets = requireContractIds("assignedFacetIds", contract.assignedFacetIds, false, MAX_CLAIM_REFERENCES);
    requireContractIds("approvedSeedNodes", contract.approvedSeedNodes, false, 12);
    requireContractIds("terminalDependencyIds", contract.terminalDependencyIds, true, 8);
    requireContractIds("sharedEvidenceOwners", contract.sharedEvidenceOwners, false, 16);
    for (const id of exclusions) if (questions.includes(id) || facets.includes(id)) throw new Error(`contract.explicitExclusionIds overlaps approved claim input ${id}`);
  }
}

function statusOf(output: JsonObject): string | undefined {
  return typeof output.status === "string" ? output.status : undefined;
}

function serializedCharacterCount(value: unknown): number {
  const serialized = JSON.stringify(value);
  return typeof serialized === "string" ? [...serialized].length : 0;
}

function validateSchemaValue(schema: JsonSchema, value: unknown, path: string, violations: string[]): void {
  const anyOf = Array.isArray(schema.anyOf) ? schema.anyOf.filter(isObject) : [];
  if (anyOf.length > 0) {
    const matched = anyOf.some((branch) => {
      const branchViolations: string[] = [];
      validateSchemaValue(branch, value, path, branchViolations);
      return branchViolations.length === 0;
    });
    if (!matched) violations.push(`${path} does not match any allowed schema branch`);
    return;
  }

  if ("const" in schema && !Object.is(value, schema.const)) violations.push(`${path} must equal its contract constant`);
  if (Array.isArray(schema.enum) && !schema.enum.some((entry) => Object.is(entry, value))) violations.push(`${path} is not an allowed enum value`);

  const type = schema.type;
  if (type === "null") {
    if (value !== null) violations.push(`${path} must be null`);
    return;
  }
  if (type === "string") {
    if (typeof value !== "string") { violations.push(`${path} must be a string`); return; }
    if (typeof schema.minLength === "number" && [...value].length < schema.minLength) violations.push(`${path} is shorter than ${schema.minLength}`);
    if (typeof schema.maxLength === "number" && [...value].length > schema.maxLength) violations.push(`${path} is longer than ${schema.maxLength}`);
    if (typeof schema.pattern === "string" && !new RegExp(schema.pattern).test(value)) violations.push(`${path} does not match ${schema.pattern}`);
    return;
  }
  if (type === "integer") {
    if (!Number.isInteger(value)) { violations.push(`${path} must be an integer`); return; }
    if (typeof schema.minimum === "number" && Number(value) < schema.minimum) violations.push(`${path} is less than ${schema.minimum}`);
    if (typeof schema.maximum === "number" && Number(value) > schema.maximum) violations.push(`${path} is greater than ${schema.maximum}`);
    return;
  }
  if (type === "boolean") {
    if (typeof value !== "boolean") violations.push(`${path} must be a boolean`);
    return;
  }
  if (type === "array") {
    if (!Array.isArray(value)) { violations.push(`${path} must be an array`); return; }
    if (typeof schema.minItems === "number" && value.length < schema.minItems) violations.push(`${path} has fewer than ${schema.minItems} items`);
    if (typeof schema.maxItems === "number" && value.length > schema.maxItems) violations.push(`${path} has more than ${schema.maxItems} items`);
    if (schema.uniqueItems === true) {
      const encoded = value.map((entry) => JSON.stringify(entry));
      if (new Set(encoded).size !== encoded.length) violations.push(`${path} must contain unique items`);
    }
    if (isObject(schema.items)) value.forEach((entry, index) => validateSchemaValue(schema.items as JsonSchema, entry, `${path}[${index}]`, violations));
    return;
  }
  if (type === "object") {
    if (!isObject(value)) { violations.push(`${path} must be an object`); return; }
    const properties = isObject(schema.properties) ? schema.properties : {};
    const required = stringArray(schema.required);
    for (const key of required) if (!(key in value)) violations.push(`${path}.${key} is required`);
    if (schema.additionalProperties === false) {
      for (const key of Object.keys(value)) if (!(key in properties)) violations.push(`${path}.${key} is not allowed`);
    }
    for (const [key, childSchema] of Object.entries(properties)) {
      if (key in value && isObject(childSchema)) validateSchemaValue(childSchema, value[key], `${path}.${key}`, violations);
    }
  }
}

function verifyCommon(contract: RecordReaderAdmissionContract, output: JsonObject, violations: string[]): void {
  for (const [key, expected] of Object.entries(contract.identity)) {
    if (output[key] !== expected) violations.push(`identity mismatch: ${key}`);
  }
  const records = objectArray(output.recordsRead);
  if (records.length > contract.budget.records) violations.push(`recordsRead exceeds ${contract.budget.records}`);
  const recordPathList = records.map((record) => typeof record.path === "string" ? record.path : "").filter(Boolean);
  if (unique(recordPathList).length !== recordPathList.length) violations.push("recordsRead contains duplicate paths");
  const recordPaths = new Set(recordPathList);
  const parentMustRead = stringArray(output.parentMustRead);
  const successStatus = statusOf(output) === "proposal-ready" || statusOf(output) === "complete";
  if (successStatus && (parentMustRead.length < 2 || parentMustRead.length > 4)) violations.push("successful packets require 2-4 parentMustRead paths");
  if (!successStatus && parentMustRead.length > 4) violations.push("parentMustRead cannot exceed 4 paths");
  for (const path of parentMustRead) if (!recordPaths.has(path)) violations.push(`parentMustRead path was not directly read: ${path}`);
  const trackedNodes = new Set([
    ...stringArray(output.consideredNodes),
    ...objectArray(output.notRead).map((row) => typeof row.node === "string" ? row.node : "").filter(Boolean),
  ]);
  for (const node of contract.concreteNodes) if (!trackedNodes.has(node)) violations.push(`supplied concrete node was not tracked: ${node}`);
  if (output.overflow !== null && !isObject(output.overflow)) violations.push("overflow must be null or an object");
}

function verifyProvenanceBackedByRecords(output: JsonObject, owners: JsonObject[], label: string, violations: string[]): void {
  const observed = new Map<string, Set<string>>();
  for (const record of objectArray(output.recordsRead)) {
    const key = `${String(record.path)}\u0000${String(record.contentHash)}`;
    observed.set(key, new Set(stringArray(record.ranges)));
  }
  for (const owner of owners) {
    for (const provenance of objectArray(owner.provenance)) {
      const key = `${String(provenance.path)}\u0000${String(provenance.contentHash)}`;
      const observedRanges = observed.get(key);
      if (!observedRanges) {
        violations.push(`${label} provenance is not backed by recordsRead: ${String(provenance.path)}`);
        continue;
      }
      for (const range of stringArray(provenance.ranges)) if (!observedRanges.has(range)) violations.push(`${label} provenance range was not directly read: ${String(provenance.path)}#${range}`);
    }
  }
}

function verifyCandidate(contract: RecordReaderAdmissionContract, output: JsonObject, violations: string[]): void {
  const facets = contract.objectiveFacetIds!;
  const inventory = contract.inventoryEntryIds!;
  const expectedInputs = [...facets, ...inventory];
  const explicitExclusions = new Set(contract.explicitExclusionIds!);
  const questions = objectArray(output.evidenceQuestions);
  const questionIds = questions.map((question) => typeof question.questionId === "string" ? question.questionId : "").filter(Boolean);
  const questionById = new Map(questionIds.map((id, index) => [id, questions[index]]));
  const seedNodes = new Set<string>();
  const dependencyEdges = new Set(stringArray(output.dependencies));
  verifyProvenanceBackedByRecords(output, questions, "evidence question", violations);

  for (const question of questions) {
    const questionFacets = stringArray(question.facets);
    const questionInventory = stringArray(question.inventoryEntries);
    if (questionFacets.length + questionInventory.length === 0) violations.push(`evidence question ${String(question.questionId)} has no Parent input origin`);
    for (const id of questionFacets) if (!facets.includes(id)) violations.push(`evidence question references unknown facet: ${id}`);
    for (const id of questionInventory) if (!inventory.includes(id)) violations.push(`evidence question references unknown inventory entry: ${id}`);
    for (const id of [...questionFacets, ...questionInventory]) if (explicitExclusions.has(id)) violations.push(`Parent-excluded input appears in evidence question: ${id}`);
    for (const layer of stringArray(question.allowedLayers)) if (!contract.allowedLayers.includes(layer)) violations.push(`evidence question uses disallowed layer: ${layer}`);
    for (const node of stringArray(question.seedNodes)) seedNodes.add(node);
  }

  const dispositions = objectArray(output.coverageDispositions);
  const dispositionIds = dispositions.map((row) => typeof row.inputId === "string" ? row.inputId : "").filter(Boolean);
  for (const id of expectedInputs) {
    const count = dispositionIds.filter((candidate) => candidate === id).length;
    if (count !== 1) violations.push(`coverage disposition count for ${id} is ${count}, expected 1`);
  }
  for (const id of dispositionIds) if (!expectedInputs.includes(id)) violations.push(`unexpected coverage disposition: ${id}`);

  const unmappedRows = objectArray(output.unmappedFacets);
  const unmappedIds = unmappedRows.map((row) => typeof row.inputId === "string" ? row.inputId : "").filter(Boolean);
  for (const row of dispositions) {
    const inputId = typeof row.inputId === "string" ? row.inputId : "";
    const disposition = typeof row.disposition === "string" ? row.disposition : "";
    const refs = stringArray(row.questionIds);
    if (disposition === "assigned" && refs.length === 0) violations.push(`assigned coverage lacks questionIds: ${inputId}`);
    if (disposition !== "assigned" && refs.length > 0) violations.push(`${disposition} coverage cannot reference questionIds: ${inputId}`);
    if (explicitExclusions.has(inputId) && disposition !== "excluded") violations.push(`Parent exclusion was not preserved exactly: ${inputId}`);
    if (disposition === "excluded" && !explicitExclusions.has(inputId)) violations.push(`coverage exclusion was not Parent-authored: ${inputId}`);
    if (disposition === "unmapped" && unmappedIds.filter((id) => id === inputId).length !== 1) violations.push(`unmapped coverage lacks one matching unmappedFacets row: ${inputId}`);
    for (const ref of refs) {
      const question = questionById.get(ref);
      if (!question) { violations.push(`coverage references unknown questionId: ${ref}`); continue; }
      const declaredOrigins = [...stringArray(question.facets), ...stringArray(question.inventoryEntries)];
      if (!declaredOrigins.includes(inputId)) violations.push(`question ${ref} does not declare assigned input ${inputId}`);
    }
  }
  for (const id of unmappedIds) {
    if (!expectedInputs.includes(id)) violations.push(`unmappedFacets contains unknown input: ${id}`);
    if (!dispositions.some((row) => row.inputId === id && row.disposition === "unmapped")) violations.push(`unmappedFacets lacks matching unmapped disposition: ${id}`);
  }

  const bundles = objectArray(output.proposedBundles);
  const bundledQuestions = new Set<string>();
  for (const bundle of bundles) {
    for (const id of stringArray(bundle.questionIds)) {
      if (!questionById.has(id)) violations.push(`proposed bundle references unknown questionId: ${id}`);
      else bundledQuestions.add(id);
    }
    for (const layer of stringArray(bundle.allowedLayers)) if (!contract.allowedLayers.includes(layer)) violations.push(`proposed bundle uses disallowed layer: ${layer}`);
    for (const node of stringArray(bundle.seedNodes)) seedNodes.add(node);
    for (const edge of stringArray(bundle.dependencies)) dependencyEdges.add(edge);
  }
  if (seedNodes.size > contract.budget.seedNodes!) violations.push(`unique seed nodes ${seedNodes.size} exceed ${contract.budget.seedNodes}`);
  if (dependencyEdges.size > contract.budget.dependencyEdges!) violations.push(`unique dependency edges ${dependencyEdges.size} exceed ${contract.budget.dependencyEdges}`);

  const status = statusOf(output);
  if (status === "proposal-ready") {
    if (questions.length === 0) violations.push("proposal-ready requires at least one evidence question");
    if (bundles.length === 0) violations.push("proposal-ready requires at least one proposed bundle");
    if (objectArray(output.recordsRead).length === 0) violations.push("proposal-ready requires direct record evidence");
    if (unmappedRows.length > 0) violations.push("proposal-ready cannot contain unmappedFacets");
    if (stringArray(output.gaps).length > 0) violations.push("proposal-ready cannot contain gaps");
    if (output.overflow !== null) violations.push("proposal-ready cannot contain overflow");
    if (dispositions.some((row) => row.disposition === "unmapped")) violations.push("proposal-ready cannot contain unmapped coverage dispositions");
    for (const id of questionIds) if (!bundledQuestions.has(id)) violations.push(`proposal-ready question is not assigned to a proposed bundle: ${id}`);
  }
}

function verifyClaim(contract: RecordReaderAdmissionContract, output: JsonObject, violations: string[]): void {
  const claims = objectArray(output.claims);
  const expectedQuestions = contract.approvedQuestionIds!;
  const expectedFacets = contract.assignedFacetIds!;
  const echoedQuestions = stringArray(output.approvedQuestionIds);
  const echoedFacets = stringArray(output.assignedFacets);
  for (const id of expectedQuestions) if (!echoedQuestions.includes(id)) violations.push(`approvedQuestionIds missing ${id}`);
  for (const id of echoedQuestions) if (!expectedQuestions.includes(id)) violations.push(`approvedQuestionIds contains unexpected ${id}`);
  for (const id of expectedFacets) if (!echoedFacets.includes(id)) violations.push(`assignedFacets missing ${id}`);
  for (const id of echoedFacets) if (!expectedFacets.includes(id)) violations.push(`assignedFacets contains unexpected ${id}`);
  const newQuestions = objectArray(output.newEvidenceQuestions);
  verifyProvenanceBackedByRecords(output, [...claims, ...newQuestions], "claim/new question", violations);
  const trackedNodes = new Set([
    ...stringArray(output.consideredNodes),
    ...objectArray(output.notRead).map((row) => typeof row.node === "string" ? row.node : "").filter(Boolean),
  ]);
  for (const node of contract.approvedSeedNodes!) if (!trackedNodes.has(node)) violations.push(`approved claim seed was not tracked: ${node}`);
  const echoedDependencies = stringArray(output.dependencies);
  for (const id of contract.terminalDependencyIds!) if (!echoedDependencies.includes(id)) violations.push(`dependencies missing Parent-accepted terminal dependency ${id}`);
  for (const id of echoedDependencies) if (!contract.terminalDependencyIds!.includes(id)) violations.push(`dependencies contains unapproved dependency ${id}`);
  if (!contract.sharedEvidenceOwners!.includes(String(output.sharedEvidenceOwner))) violations.push(`sharedEvidenceOwner is not Parent-approved: ${String(output.sharedEvidenceOwner)}`);

  const coveredQuestions = new Set<string>();
  const coveredFacets = new Set<string>();
  for (const claim of claims) {
    for (const id of stringArray(claim.questionIds)) {
      if (!expectedQuestions.includes(id)) violations.push(`claim references unapproved question ${id}`);
      else coveredQuestions.add(id);
    }
    for (const id of stringArray(claim.facets)) {
      if (!expectedFacets.includes(id)) violations.push(`claim references unassigned facet ${id}`);
      else coveredFacets.add(id);
    }
  }

  const status = statusOf(output);
  if (status === "complete") {
    if (claims.length === 0) violations.push("complete requires at least one evidence claim");
    if (objectArray(output.recordsRead).length === 0) violations.push("complete requires direct record evidence");
    if (stringArray(output.gaps).length > 0) violations.push("complete cannot contain gaps");
    if (objectArray(output.newEvidenceQuestions).length > 0) violations.push("complete cannot contain newEvidenceQuestions");
    for (const field of ["overlapObserved", "dependencyChanges"] as const) {
      if (stringArray(output[field]).length > 0) violations.push(`complete cannot contain ${field}`);
    }
    for (const id of expectedQuestions) if (!coveredQuestions.has(id)) violations.push(`complete claims do not cover approved question ${id}`);
    for (const id of expectedFacets) if (!coveredFacets.has(id)) violations.push(`complete claims do not cover assigned facet ${id}`);
    if (output.overflow !== null) violations.push("complete cannot contain overflow");
  }
}

function admitLegacyOutput(contract: RecordReaderAdmissionContract, value: unknown): RecordReaderAdmissionReceipt {
  assertLegacyContract(contract);
  const violations: string[] = [];
  const outputCharacters = serializedCharacterCount(value);
  validateSchemaValue(buildLegacyOutputSchema(contract), value, "$", violations);
  if (!isObject(value)) {
    const uniqueViolations = unique(violations);
    return {
      schemaVersion: "record-reader-admission-receipt/v1",
      valid: false,
      success: false,
      admittedStatus: "invalid-packet",
      outputCharacters,
      outputCharacterBudget: contract.budget.outputCharacters,
      outputMeasurement: "compact-json-unicode-code-points/v1",
      violations: uniqueViolations,
    };
  }

  if (outputCharacters > contract.budget.outputCharacters) violations.push(`output characters ${outputCharacters} exceed ${contract.budget.outputCharacters}`);
  verifyCommon(contract, value, violations);
  if (contract.mode === "candidate-map") verifyCandidate(contract, value, violations);
  else verifyClaim(contract, value, violations);

  const reportedStatus = statusOf(value);
  const validStatuses = contract.mode === "candidate-map" ? CANDIDATE_STATUSES : CLAIM_STATUSES;
  if (!reportedStatus || !validStatuses.includes(reportedStatus)) violations.push(`invalid status for ${contract.mode}: ${String(reportedStatus)}`);
  const uniqueViolations = unique(violations);
  const valid = uniqueViolations.length === 0;
  const success = valid && (reportedStatus === "proposal-ready" || reportedStatus === "complete");
  return {
    schemaVersion: "record-reader-admission-receipt/v1",
    valid,
    success,
    reportedStatus,
    admittedStatus: valid ? reportedStatus! : "invalid-packet",
    outputCharacters,
    outputCharacterBudget: contract.budget.outputCharacters,
    outputMeasurement: "compact-json-unicode-code-points/v1",
    violations: uniqueViolations,
  };
}

function isCompactContract(value: unknown): value is CompactRecordReaderAdmissionContract {
  return isObject(value) && value.schemaVersion === "record-reader-admission/v2";
}

function canonicalJson(value: unknown): string {
  if (value === null || typeof value === "string" || typeof value === "number" || typeof value === "boolean") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`;
  if (isObject(value)) {
    return `{${Object.keys(value).sort((left, right) => left.localeCompare(right)).map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`).join(",")}}`;
  }
  throw new Error(`Unsupported contract value in canonical JSON: ${typeof value}`);
}

export function computeRecordReaderContractDigest(contract: unknown): string {
  if (!isObject(contract)) throw new Error("compact contract must be an object");
  const { contractDigest: _ignoredDigest, ...digestInput } = contract;
  void _ignoredDigest;
  return `sha256:${createHash("sha256").update(canonicalJson(digestInput)).digest("hex")}`;
}

function assertExactKeys(label: string, value: JsonObject, allowed: string[], required: string[] = allowed): void {
  for (const key of required) if (!(key in value)) throw new Error(`${label}.${key} is required`);
  for (const key of Object.keys(value)) if (!allowed.includes(key)) throw new Error(`${label}.${key} is not allowed`);
}
interface CompactCatalogOptions {
  label: string;
  value: unknown;
  idPattern: string;
  valueKey: "description" | "node" | "target";
  maxItems: number;
  allowEmpty?: boolean;
}

function compactCatalog(options: CompactCatalogOptions): Map<string, string> {
  const { label, value, idPattern, valueKey, maxItems, allowEmpty = false } = options;
  if (!Array.isArray(value) || (!allowEmpty && value.length === 0) || value.length > maxItems) {
    throw new Error(`contract.${label} must contain ${allowEmpty ? "0" : "1"}-${maxItems} entries`);
  }
  const result = new Map<string, string>();
  const pattern = new RegExp(idPattern);
  for (const [index, entry] of value.entries()) {
    if (!isObject(entry)) throw new Error(`contract.${label}[${index}] must be an object`);
    assertExactKeys(`contract.${label}[${index}]`, entry, ["id", valueKey]);
    const id = entry.id;
    const text = entry[valueKey];
    if (typeof id !== "string" || !pattern.test(id)) throw new Error(`contract.${label}[${index}].id is invalid`);
    if (typeof text !== "string" || !text.trim() || [...text].length > 2_000) throw new Error(`contract.${label}[${index}].${valueKey} is invalid`);
    if (result.has(id)) throw new Error(`contract.${label} contains duplicate id ${id}`);
    result.set(id, text);
  }
  return result;
}

function compactBudgetValue(
  contract: CompactRecordReaderAdmissionContract,
  key: keyof CompactRecordReaderAdmissionContract["budget"],
  ceiling: number,
 ): number {
  const value = contract.budget[key];
  if (!Number.isInteger(value) || Number(value) < 1) throw new Error(`contract.budget.${key} must be a positive integer`);
  if (Number(value) > ceiling) throw new Error(`contract.budget.${key} exceeds compact role ceiling ${ceiling}`);
  return Number(value);
}

function assertCompactContract(contract: CompactRecordReaderAdmissionContract): void {
  if (!isObject(contract) || contract.schemaVersion !== "record-reader-admission/v2") throw new Error("contract.schemaVersion must be record-reader-admission/v2");
  if (contract.mode !== "candidate-map" && contract.mode !== "claim-evidence") throw new Error("contract.mode must be candidate-map or claim-evidence");
  const commonContractKeys = ["schemaVersion", "mode", "contractDigest", "identity", "objective", "facets", "inventoryEntries", "nodes", "verificationCandidates", "allowedLayers", "governingRecordsReadByParent", "riskConstraints", "explicitExclusionIds", "budget"];
  const claimContractKeys = ["approvedQuestionIds", "assignedFacetIds", "approvedSeedNodeIds", "terminalDependencyIds", "sharedEvidenceOwnerIds"];
  const topKeys = [...commonContractKeys, ...(contract.mode === "claim-evidence" ? claimContractKeys : [])];
  assertExactKeys("contract", contract as unknown as JsonObject, topKeys);
  if (!isObject(contract.identity)) throw new Error("contract.identity must be an object");
  if (!isObject(contract.budget)) throw new Error("contract.budget must be an object");
  const identityKeys = [...REQUIRED_IDENTITY_KEYS, ...(contract.mode === "claim-evidence" ? CLAIM_IDENTITY_KEYS : [])];
  assertExactKeys("contract.identity", contract.identity, identityKeys);
  const commonBudgetKeys = ["targetOutputCharacters", "hardOutputCharacters", "records", "toolCalls"];
  const modeBudgetKeys = contract.mode === "candidate-map" ? ["questions", "seedNodes", "dependencyEdges", "proposedBundles"] : ["claims"];
  assertExactKeys("contract.budget", contract.budget as unknown as JsonObject, [...commonBudgetKeys, ...modeBudgetKeys]);
  for (const key of REQUIRED_IDENTITY_KEYS) if (typeof contract.identity[key] !== "string" || !contract.identity[key]) throw new Error(`contract.identity.${key} must be a non-empty string`);
  for (const [key, value] of Object.entries(contract.identity)) if (!key || typeof value !== "string" || !value) throw new Error(`contract.identity.${key} must be a non-empty string`);
  if (contract.identity.packetVersion !== "record-reader/v2" || contract.identity.mode !== contract.mode) throw new Error("contract identity packetVersion/mode mismatch");
  if (contract.mode === "claim-evidence") for (const key of CLAIM_IDENTITY_KEYS) if (!contract.identity[key]) throw new Error(`contract.identity.${key} is required`);
  if (typeof contract.contractDigest !== "string" || !/^sha256:[0-9a-f]{64}$/.test(contract.contractDigest)) throw new Error("contract.contractDigest must be sha256:<64 hex>");
  const expectedDigest = computeRecordReaderContractDigest(contract);
  if (contract.contractDigest !== expectedDigest) throw new Error(`contract.contractDigest mismatch; expected ${expectedDigest}`);
  if (typeof contract.objective !== "string" || !contract.objective.trim() || [...contract.objective].length > 4_000) throw new Error("contract.objective must be 1-4000 characters");

  const facets = compactCatalog({ label: "facets", value: contract.facets, idPattern: COMPACT_ID_PATTERNS.facet, valueKey: "description", maxItems: 32, allowEmpty: contract.mode === "claim-evidence" });
  const inventory = compactCatalog({ label: "inventoryEntries", value: contract.inventoryEntries, idPattern: COMPACT_ID_PATTERNS.inventory, valueKey: "description", maxItems: 32, allowEmpty: contract.mode === "claim-evidence" });
  const nodes = compactCatalog({ label: "nodes", value: contract.nodes, idPattern: COMPACT_ID_PATTERNS.node, valueKey: "node", maxItems: 32 });
  const verification = compactCatalog({ label: "verificationCandidates", value: contract.verificationCandidates, idPattern: COMPACT_ID_PATTERNS.verification, valueKey: "target", maxItems: 32, allowEmpty: true });
  const allInputs = [...facets.keys(), ...inventory.keys()];
  if (allInputs.length > MAX_CANDIDATE_COVERAGE_INPUTS || unique(allInputs).length !== allInputs.length) throw new Error("compact facet/inventory ids must be unique and total <= 32");
  const exclusions = requireContractIds("explicitExclusionIds", contract.explicitExclusionIds, true, 32);
  for (const id of exclusions) if (!allInputs.includes(id)) throw new Error(`contract.explicitExclusionIds contains unknown input ${id}`);
  const allowedLayers = requireContractIds("allowedLayers", contract.allowedLayers, false, ALLOWED_LAYERS.length);
  for (const layer of allowedLayers) if (!(ALLOWED_LAYERS as readonly string[]).includes(layer)) throw new Error(`unsupported allowed layer ${layer}`);
  requireContractIds("governingRecordsReadByParent", contract.governingRecordsReadByParent, false, 32);
  requireContractIds("riskConstraints", contract.riskConstraints, true, 32);
  const target = compactBudgetValue(contract, "targetOutputCharacters", COMPACT_TARGET_MAX);
  const hard = compactBudgetValue(contract, "hardOutputCharacters", COMPACT_HARD_MAX);
  if (target > hard) throw new Error("targetOutputCharacters must be <= hardOutputCharacters");
  compactBudgetValue(contract, "toolCalls", 14);
  const recordBudget = compactBudgetValue(contract, "records", contract.mode === "candidate-map" ? 6 : 8);
  if (recordBudget < 2) throw new Error("compact budget.records must be at least 2 so success can satisfy parentRead");

  if (contract.mode === "candidate-map") {
    if (facets.size === 0 || inventory.size === 0) throw new Error("candidate compact contract requires facets and inventoryEntries");
    compactBudgetValue(contract, "questions", 6);
    compactBudgetValue(contract, "seedNodes", 12);
    compactBudgetValue(contract, "dependencyEdges", 8);
    compactBudgetValue(contract, "proposedBundles", 3);
  } else {
    compactBudgetValue(contract, "claims", 6);
    const questions = requireContractIds("approvedQuestionIds", contract.approvedQuestionIds, false, MAX_CLAIM_REFERENCES);
    if (questions.some((id) => !new RegExp(COMPACT_ID_PATTERNS.question).test(id))) throw new Error("approvedQuestionIds must use Q<number>");
    const assigned = requireContractIds("assignedFacetIds", contract.assignedFacetIds, false, MAX_CLAIM_REFERENCES);
    for (const id of assigned) if (!facets.has(id)) throw new Error(`assignedFacetIds contains unknown ${id}`);
    const seeds = requireContractIds("approvedSeedNodeIds", contract.approvedSeedNodeIds, false, 12);
    for (const id of seeds) if (!nodes.has(id)) throw new Error(`approvedSeedNodeIds contains unknown ${id}`);
    const dependencies = requireContractIds("terminalDependencyIds", contract.terminalDependencyIds, true, 8);
    if (dependencies.some((id) => !new RegExp(COMPACT_ID_PATTERNS.dependency).test(id))) throw new Error("terminalDependencyIds must use D<number>");
    requireContractIds("sharedEvidenceOwnerIds", contract.sharedEvidenceOwnerIds, false, 16);
    for (const id of exclusions) if (questions.includes(id) || assigned.includes(id)) throw new Error(`explicit exclusion overlaps approved claim input ${id}`);
  }
  void verification;
}

function boundedStringSchema(maxLength = COMPACT_DETAIL_MAX): JsonSchema {
  return nonEmptyStringSchema({ maxLength });
}

function compactRefSchema(pattern: string, values?: string[]): JsonSchema {
  const schema: JsonSchema = nonEmptyStringSchema({ pattern });
  if (values && values.length > 0) schema.enum = values;
  return schema;
}

function compactRefArraySchema(pattern: string, maxItems: number, minItems = 0, values?: string[]): JsonSchema {
  return { type: "array", items: compactRefSchema(pattern, values), minItems, maxItems, uniqueItems: true };
}

function compactEvidenceSchema(): JsonSchema {
  return {
    type: "object",
    properties: {
      recordId: compactRefSchema(COMPACT_ID_PATTERNS.record),
      rangeIndexes: { type: "array", items: { type: "integer", minimum: 0, maximum: 11 }, minItems: 1, maxItems: 12, uniqueItems: true },
    },
    required: ["recordId", "rangeIndexes"],
    additionalProperties: false,
  };
}

function compactOverflowSchema(): JsonSchema {
  return {
    anyOf: [
      { type: "null" },
      {
        type: "object",
        properties: { reason: boundedStringSchema(COMPACT_DETAIL_MAX), limit: boundedStringSchema(80) },
        required: ["reason"],
        additionalProperties: false,
      },
    ],
  };
}

function compactCommonProperties(contract: CompactRecordReaderAdmissionContract): Record<string, JsonSchema> {
  const nodeIds = contract.nodes.map((entry) => entry.id);
  const verificationIds = contract.verificationCandidates.map((entry) => entry.id);
  return {
    contractDigest: { type: "string", const: contract.contractDigest },
    status: { type: "string", enum: contract.mode === "candidate-map" ? CANDIDATE_STATUSES : CLAIM_STATUSES },
    statusJustification: boundedStringSchema(COMPACT_TEXT_MAX),
    records: {
      type: "array",
      maxItems: contract.budget.records,
      items: {
        type: "object",
        properties: {
          id: compactRefSchema(COMPACT_ID_PATTERNS.record),
          path: boundedStringSchema(512),
          contentHash: nonEmptyStringSchema({ pattern: "^(?:[0-9a-f]{40}|[0-9a-f]{64})$" }),
          ranges: { type: "array", items: boundedStringSchema(COMPACT_DETAIL_MAX), minItems: 1, maxItems: 12, uniqueItems: true },
        },
        required: ["id", "path", "contentHash", "ranges"],
        additionalProperties: false,
      },
    },
    nodes: {
      type: "object",
      properties: {
        considered: compactRefArraySchema(COMPACT_ID_PATTERNS.node, nodeIds.length, 0, nodeIds),
        notRead: {
          type: "array",
          maxItems: nodeIds.length,
          items: {
            type: "object",
            properties: {
              id: compactRefSchema(COMPACT_ID_PATTERNS.node, nodeIds),
              reasonCode: { type: "string", enum: ["budget", "parent-owned", "excluded", "duplicate", "other"] },
              detail: { type: "string", maxLength: COMPACT_DETAIL_MAX },
            },
            required: ["id", "reasonCode"],
            additionalProperties: false,
          },
        },
        rejected: {
          type: "array",
          maxItems: nodeIds.length,
          items: {
            type: "object",
            properties: { id: compactRefSchema(COMPACT_ID_PATTERNS.node, nodeIds), reason: boundedStringSchema(COMPACT_DETAIL_MAX) },
            required: ["id", "reason"],
            additionalProperties: false,
          },
        },
      },
      required: ["considered", "notRead", "rejected"],
      additionalProperties: false,
    },
    parentRead: compactRefArraySchema(COMPACT_ID_PATTERNS.record, 4),
    verification: compactRefArraySchema(COMPACT_ID_PATTERNS.verification, verificationIds.length, 0, verificationIds),
    overflow: compactOverflowSchema(),
  };
}

function compactQuestionSchema(contract: CompactRecordReaderAdmissionContract): JsonSchema {
  const nodeIds = contract.nodes.map((entry) => entry.id);
  const verificationIds = contract.verificationCandidates.map((entry) => entry.id);
  return {
    type: "object",
    properties: {
      id: compactRefSchema(COMPACT_ID_PATTERNS.question),
      text: boundedStringSchema(COMPACT_TEXT_MAX),
      evidence: { type: "array", items: compactEvidenceSchema(), minItems: 1, maxItems: 8 },
      seeds: compactRefArraySchema(COMPACT_ID_PATTERNS.node, contract.budget.seedNodes ?? 12, 1, nodeIds),
      risks: { type: "array", items: boundedStringSchema(COMPACT_RISK_MAX), maxItems: 4, uniqueItems: true },
      verification: compactRefArraySchema(COMPACT_ID_PATTERNS.verification, verificationIds.length, 0, verificationIds),
    },
    required: ["id", "text", "evidence", "seeds", "risks", "verification"],
    additionalProperties: false,
  };
}

function compactCoverageSchema(contract: CompactRecordReaderAdmissionContract): JsonSchema {
  const properties: Record<string, JsonSchema> = {};
  const exclusions = new Set(contract.explicitExclusionIds);
  for (const id of [...contract.facets.map((entry) => entry.id), ...contract.inventoryEntries.map((entry) => entry.id)]) {
    properties[id] = exclusions.has(id)
      ? { type: "string", const: "excluded" }
      : {
          anyOf: [
            compactRefArraySchema(COMPACT_ID_PATTERNS.question, 8, 1),
            {
              type: "object",
              properties: { unmapped: boundedStringSchema(COMPACT_DETAIL_MAX) },
              required: ["unmapped"],
              additionalProperties: false,
            },
          ],
        };
  }
  return { type: "object", properties, required: Object.keys(properties), additionalProperties: false };
}

function compactDependencySchema(): JsonSchema {
  return {
    type: "object",
    properties: {
      id: compactRefSchema(COMPACT_ID_PATTERNS.dependency),
      from: compactRefSchema(COMPACT_ID_PATTERNS.question),
      to: compactRefSchema(COMPACT_ID_PATTERNS.question),
      reason: boundedStringSchema(COMPACT_DETAIL_MAX),
    },
    required: ["id", "from", "to", "reason"],
    additionalProperties: false,
  };
}

function compactCandidateProperties(contract: CompactRecordReaderAdmissionContract): Record<string, JsonSchema> {
  const nodeIds = contract.nodes.map((entry) => entry.id);
  const inputIds = [...contract.facets.map((entry) => entry.id), ...contract.inventoryEntries.map((entry) => entry.id)];
  return {
    questions: { type: "array", items: compactQuestionSchema(contract), maxItems: contract.budget.questions },
    coverage: compactCoverageSchema(contract),
    overlap: {
      type: "array",
      maxItems: 16,
      items: {
        type: "object",
        properties: { questions: compactRefArraySchema(COMPACT_ID_PATTERNS.question, 16, 1), reason: boundedStringSchema(COMPACT_DETAIL_MAX) },
        required: ["questions", "reason"],
        additionalProperties: false,
      },
    },
    cycles: {
      type: "array",
      maxItems: 16,
      items: {
        type: "object",
        properties: { questions: compactRefArraySchema(COMPACT_ID_PATTERNS.question, 16, 1), reason: boundedStringSchema(COMPACT_DETAIL_MAX) },
        required: ["questions", "reason"],
        additionalProperties: false,
      },
    },
    dependencies: { type: "array", items: compactDependencySchema(), maxItems: contract.budget.dependencyEdges },
    bundles: {
      type: "array",
      maxItems: contract.budget.proposedBundles,
      items: {
        type: "object",
        properties: {
          id: compactRefSchema(COMPACT_ID_PATTERNS.bundle),
          questions: compactRefArraySchema(COMPACT_ID_PATTERNS.question, 16, 1),
          seeds: compactRefArraySchema(COMPACT_ID_PATTERNS.node, contract.budget.seedNodes ?? 12, 1, nodeIds),
          dependencies: compactRefArraySchema(COMPACT_ID_PATTERNS.dependency, contract.budget.dependencyEdges ?? 8),
          owner: boundedStringSchema(80),
          reason: boundedStringSchema(COMPACT_DETAIL_MAX),
        },
        required: ["id", "questions", "seeds", "dependencies", "owner", "reason"],
        additionalProperties: false,
      },
    },
    proposedExclusions: { type: "array", items: { type: "string", enum: inputIds }, maxItems: inputIds.length, uniqueItems: true },
    gaps: { type: "array", items: boundedStringSchema(COMPACT_DETAIL_MAX), maxItems: 32, uniqueItems: true },
    routing: { type: "string", enum: ["parent-direct", "single-reader", "parallel-candidate"] },
  };
}

function compactClaimProperties(contract: CompactRecordReaderAdmissionContract): Record<string, JsonSchema> {
  const questionIds = contract.approvedQuestionIds ?? [];
  const facetIds = contract.assignedFacetIds ?? [];
  const nodeIds = contract.nodes.map((entry) => entry.id);
  const verificationIds = contract.verificationCandidates.map((entry) => entry.id);
  const owners = contract.sharedEvidenceOwnerIds ?? [];
  const dependencyIds = contract.terminalDependencyIds ?? [];
  return {
    sharedEvidenceOwner: { type: "string", enum: owners },
    claims: {
      type: "array",
      maxItems: contract.budget.claims,
      items: {
        type: "object",
        properties: {
          id: compactRefSchema(COMPACT_ID_PATTERNS.claim),
          questions: compactRefArraySchema(COMPACT_ID_PATTERNS.question, questionIds.length, 1, questionIds),
          facets: compactRefArraySchema(COMPACT_ID_PATTERNS.facet, facetIds.length, 1, facetIds),
          text: boundedStringSchema(COMPACT_TEXT_MAX),
          evidence: { type: "array", items: compactEvidenceSchema(), minItems: 1, maxItems: 8 },
          risks: { type: "array", items: boundedStringSchema(COMPACT_RISK_MAX), maxItems: 4, uniqueItems: true },
          verification: compactRefArraySchema(COMPACT_ID_PATTERNS.verification, verificationIds.length, 0, verificationIds),
        },
        required: ["id", "questions", "facets", "text", "evidence", "risks", "verification"],
        additionalProperties: false,
      },
    },
    conflicts: { type: "array", items: boundedStringSchema(COMPACT_DETAIL_MAX), maxItems: 32, uniqueItems: true },
    blockingConflicts: { type: "array", items: boundedStringSchema(COMPACT_DETAIL_MAX), maxItems: 32, uniqueItems: true },
    sharedEvidenceUsed: compactRefArraySchema(COMPACT_ID_PATTERNS.record, contract.budget.records),
    gaps: { type: "array", items: boundedStringSchema(COMPACT_DETAIL_MAX), maxItems: 32, uniqueItems: true },
    newQuestions: {
      type: "array",
      maxItems: 16,
      items: {
        type: "object",
        properties: {
          id: nonEmptyStringSchema({ pattern: "^NQ[1-9][0-9]*$" }),
          text: boundedStringSchema(COMPACT_TEXT_MAX),
          reason: boundedStringSchema(COMPACT_DETAIL_MAX),
          evidence: { type: "array", items: compactEvidenceSchema(), minItems: 1, maxItems: 8 },
          seeds: compactRefArraySchema(COMPACT_ID_PATTERNS.node, nodeIds.length, 1, nodeIds),
          verification: compactRefArraySchema(COMPACT_ID_PATTERNS.verification, verificationIds.length, 0, verificationIds),
        },
        required: ["id", "text", "reason", "evidence", "seeds", "verification"],
        additionalProperties: false,
      },
    },
    overlapObserved: { type: "array", items: boundedStringSchema(COMPACT_DETAIL_MAX), maxItems: 32, uniqueItems: true },
    dependencyChanges: { type: "array", items: boundedStringSchema(COMPACT_DETAIL_MAX), maxItems: 32, uniqueItems: true },
    blockedDependencies: compactRefArraySchema(COMPACT_ID_PATTERNS.dependency, dependencyIds.length, 0, dependencyIds),
  };
}

function buildCompactOutputSchema(contract: CompactRecordReaderAdmissionContract): JsonSchema {
  assertCompactContract(contract);
  const properties = {
    ...compactCommonProperties(contract),
    ...(contract.mode === "candidate-map" ? compactCandidateProperties(contract) : compactClaimProperties(contract)),
  };
  const commonRequired = ["contractDigest", "status", "statusJustification", "records", "nodes", "parentRead", "verification", "overflow"];
  const modeRequired = contract.mode === "candidate-map"
    ? ["questions", "coverage", "overlap", "cycles", "dependencies", "bundles", "proposedExclusions", "gaps", "routing"]
    : ["sharedEvidenceOwner", "claims", "conflicts", "blockingConflicts", "sharedEvidenceUsed", "gaps", "newQuestions", "overlapObserved", "dependencyChanges", "blockedDependencies"];
  return { type: "object", properties, required: [...commonRequired, ...modeRequired], additionalProperties: false };
}

function compactRecordIndex(output: JsonObject, violations: string[]): Map<string, JsonObject> {
  const result = new Map<string, JsonObject>();
  const paths = new Set<string>();
  for (const record of objectArray(output.records)) {
    const id = typeof record.id === "string" ? record.id : "";
    const path = typeof record.path === "string" ? record.path : "";
    if (result.has(id)) violations.push(`records contains duplicate id ${id}`);
    else result.set(id, record);
    if (paths.has(path)) violations.push(`records contains duplicate path ${path}`);
    paths.add(path);
  }
  return result;
}

function compactCanonicalRecordLayer(path: string): string | undefined {
  if (!path || path.includes("\\") || path.includes("\0")) return undefined;
  const segments = path.split("/");
  if (segments.some((segment) => !segment || segment === "." || segment === "..")) return undefined;
  if (segments[0] !== ".lazy-harness" || segments.length < 3 || !/\.(?:md|xml|json|jsonl)$/.test(segments.at(-1) ?? "")) return undefined;
  const layer = segments[1];
  return (ALLOWED_LAYERS as readonly string[]).includes(layer) ? layer : undefined;
}

function verifyCompactEvidence(
  owners: JsonObject[],
  recordIndex: Map<string, JsonObject>,
  label: string,
  violations: string[],
 ): void {
  for (const owner of owners) {
    for (const evidence of objectArray(owner.evidence)) {
      const recordId = typeof evidence.recordId === "string" ? evidence.recordId : "";
      const record = recordIndex.get(recordId);
      if (!record) { violations.push(`${label} references unknown record ${recordId}`); continue; }
      const rangeCount = stringArray(record.ranges).length;
      for (const index of Array.isArray(evidence.rangeIndexes) ? evidence.rangeIndexes : []) {
        if (!Number.isInteger(index) || Number(index) < 0 || Number(index) >= rangeCount) violations.push(`${label} range index ${String(index)} is invalid for ${recordId}`);
      }
    }
  }
}

function verifyCompactCommon(
  contract: CompactRecordReaderAdmissionContract,
  output: JsonObject,
  violations: string[],
 ): Map<string, JsonObject> {
  if (output.contractDigest !== contract.contractDigest) violations.push("contractDigest mismatch");
  const records = objectArray(output.records);
  if (records.length > contract.budget.records) violations.push(`records exceeds ${contract.budget.records}`);
  const recordIndex = compactRecordIndex(output, violations);
  for (const record of records) {
    const path = typeof record.path === "string" ? record.path : "";
    const layer = compactCanonicalRecordLayer(path);
    if (!layer || !contract.allowedLayers.includes(layer)) violations.push(`record path is outside allowed canonical layers: ${path}`);
  }
  const success = statusOf(output) === "proposal-ready" || statusOf(output) === "complete";
  const parentRead = stringArray(output.parentRead);
  if (success && (parentRead.length < 2 || parentRead.length > 4)) violations.push("successful compact packet requires 2-4 parentRead ids");
  for (const id of parentRead) if (!recordIndex.has(id)) violations.push(`parentRead references unknown record ${id}`);
  const verificationIds = new Set(contract.verificationCandidates.map((entry) => entry.id));
  for (const id of stringArray(output.verification)) if (!verificationIds.has(id)) violations.push(`verification references unknown id ${id}`);

  const nodeIds = contract.nodes.map((entry) => entry.id);
  const nodes = isObject(output.nodes) ? output.nodes : {};
  const considered = stringArray(nodes.considered);
  for (const id of nodeIds) if (!considered.includes(id)) violations.push(`node ${id} was not considered`);
  for (const id of considered) if (!nodeIds.includes(id)) violations.push(`unknown considered node ${id}`);
  const notReadRows = objectArray(nodes.notRead);
  const rejectedRows = objectArray(nodes.rejected);
  const notReadIds = notReadRows.map((row) => String(row.id));
  const rejectedIds = rejectedRows.map((row) => String(row.id));
  if (unique(notReadIds).length !== notReadIds.length) violations.push("nodes.notRead contains duplicate ids");
  if (unique(rejectedIds).length !== rejectedIds.length) violations.push("nodes.rejected contains duplicate ids");
  for (const id of notReadIds) if (rejectedIds.includes(id)) violations.push(`node ${id} cannot be both notRead and rejected`);
  for (const row of [...notReadRows, ...rejectedRows]) {
    if (typeof row.id !== "string" || !nodeIds.includes(row.id)) violations.push(`node detail references unknown id ${String(row.id)}`);
  }
  const readPaths = new Set(records.map((record) => String(record.path)));
  for (const entry of contract.nodes) {
    const wasRead = readPaths.has(entry.node);
    if (wasRead && (notReadIds.includes(entry.id) || rejectedIds.includes(entry.id))) violations.push(`read node ${entry.id} cannot be notRead/rejected`);
    if (!wasRead && !notReadIds.includes(entry.id) && !rejectedIds.includes(entry.id)) violations.push(`node ${entry.id} has no read/notRead/rejected closure`);
  }
  const status = statusOf(output);
  if (output.overflow !== null && status !== "overflow") violations.push("non-null overflow requires overflow status");
  if (status === "overflow" && output.overflow === null) violations.push("overflow status requires overflow detail");
  return recordIndex;
}

function verifyCompactCandidate(
  contract: CompactRecordReaderAdmissionContract,
  output: JsonObject,
  recordIndex: Map<string, JsonObject>,
  violations: string[],
 ): void {
  const questions = objectArray(output.questions);
  const questionIds = questions.map((question) => typeof question.id === "string" ? question.id : "").filter(Boolean);
  if (unique(questionIds).length !== questionIds.length) violations.push("questions contains duplicate ids");
  const questionSet = new Set(questionIds);
  verifyCompactEvidence(questions, recordIndex, "question evidence", violations);
  const topVerification = new Set(stringArray(output.verification));
  const uniqueSeeds = new Set<string>();
  for (const question of questions) {
    for (const id of stringArray(question.verification)) if (!topVerification.has(id)) violations.push(`question ${String(question.id)} verification ${id} is absent from top-level verification`);
    for (const id of stringArray(question.seeds)) uniqueSeeds.add(id);
  }

  const coverage = isObject(output.coverage) ? output.coverage : {};
  const allInputIds = [...contract.facets.map((entry) => entry.id), ...contract.inventoryEntries.map((entry) => entry.id)];
  const excluded = new Set(contract.explicitExclusionIds);
  const coveredQuestions = new Set<string>();
  let hasUnmapped = false;
  for (const id of allInputIds) {
    const value = coverage[id];
    if (excluded.has(id)) {
      if (value !== "excluded") violations.push(`Parent exclusion was not preserved for ${id}`);
      continue;
    }
    if (Array.isArray(value)) {
      for (const questionId of value) {
        if (typeof questionId !== "string" || !questionSet.has(questionId)) violations.push(`coverage ${id} references unknown question ${String(questionId)}`);
        else coveredQuestions.add(questionId);
      }
    } else if (isObject(value) && typeof value.unmapped === "string") hasUnmapped = true;
    else violations.push(`coverage ${id} has invalid disposition`);
  }
  for (const id of questionIds) if (!coveredQuestions.has(id)) violations.push(`question ${id} has no coverage input`);

  const dependencyRows = objectArray(output.dependencies);
  const dependencyIds = dependencyRows.map((row) => typeof row.id === "string" ? row.id : "").filter(Boolean);
  if (unique(dependencyIds).length !== dependencyIds.length) violations.push("dependencies contains duplicate ids");
  const dependencyById = new Map<string, JsonObject>();
  for (const row of dependencyRows) {
    const id = String(row.id);
    dependencyById.set(id, row);
    if (!questionSet.has(String(row.from)) || !questionSet.has(String(row.to))) violations.push(`dependency ${id} references unknown question`);
    if (row.from === row.to) violations.push(`dependency ${id} cannot self-reference`);
  }
  const overlapRows = objectArray(output.overlap);
  const cycleRows = objectArray(output.cycles);
  for (const row of [...overlapRows, ...cycleRows]) {
    for (const id of stringArray(row.questions)) if (!questionSet.has(id)) violations.push(`overlap/cycle references unknown question ${id}`);
  }

  const bundles = objectArray(output.bundles);
  const questionOwners = new Map<string, JsonObject[]>();
  const bundleIds = new Set<string>();
  const dependencyOwners = new Map<string, JsonObject[]>();
  for (const bundle of bundles) {
    const id = String(bundle.id);
    if (bundleIds.has(id)) violations.push(`bundles contains duplicate id ${id}`);
    bundleIds.add(id);
    const bundleQuestions = stringArray(bundle.questions);
    for (const questionId of bundleQuestions) {
      if (!questionSet.has(questionId)) violations.push(`bundle ${id} references unknown question ${questionId}`);
      else {
        const owners = questionOwners.get(questionId) ?? [];
        owners.push(bundle);
        questionOwners.set(questionId, owners);
      }
    }
    for (const seedId of stringArray(bundle.seeds)) uniqueSeeds.add(seedId);
    for (const dependencyId of stringArray(bundle.dependencies)) {
      if (!dependencyById.has(dependencyId)) violations.push(`bundle ${id} references unknown dependency ${dependencyId}`);
      const owners = dependencyOwners.get(dependencyId) ?? [];
      owners.push(bundle);
      dependencyOwners.set(dependencyId, owners);
    }
  }
  if (uniqueSeeds.size > Number(contract.budget.seedNodes)) violations.push(`unique seed ids ${uniqueSeeds.size} exceed ${contract.budget.seedNodes}`);

  const status = statusOf(output);
  if (status === "proposal-ready") {
    if (questions.length === 0 || objectArray(output.records).length === 0 || bundles.length === 0) violations.push("proposal-ready requires questions, records, and bundles");
    if (hasUnmapped) violations.push("proposal-ready cannot contain unmapped coverage");
    if (stringArray(output.gaps).length > 0 || output.overflow !== null) violations.push("proposal-ready cannot contain gaps or overflow");
    for (const id of questionIds) if ((questionOwners.get(id) ?? []).length !== 1) violations.push(`proposal-ready question ${id} must belong to exactly one bundle`);
    for (const [label, rows] of [["overlap", overlapRows], ["cycle", cycleRows]] as const) {
      for (const row of rows) {
        const ids = stringArray(row.questions);
        const owners = bundles.filter((bundle) => ids.every((id) => stringArray(bundle.questions).includes(id)));
        if (owners.length !== 1) violations.push(`proposal-ready ${label} group must have exactly one co-located owning bundle`);
      }
    }
    for (const [id, dependency] of dependencyById) {
      const owners = dependencyOwners.get(id) ?? [];
      if (owners.length !== 1) violations.push(`proposal-ready dependency ${id} must have exactly one owning bundle`);
      for (const bundle of owners) {
        const ids = stringArray(bundle.questions);
        if (!ids.includes(String(dependency.from)) || !ids.includes(String(dependency.to))) violations.push(`bundle ${String(bundle.id)} does not contain both endpoints of dependency ${id}`);
      }
    }
  }
}

function verifyCompactClaim(
  contract: CompactRecordReaderAdmissionContract,
  output: JsonObject,
  recordIndex: Map<string, JsonObject>,
  violations: string[],
 ): void {
  const claims = objectArray(output.claims);
  const newQuestions = objectArray(output.newQuestions);
  verifyCompactEvidence([...claims, ...newQuestions], recordIndex, "claim/new-question evidence", violations);
  const topVerification = new Set(stringArray(output.verification));
  for (const owner of [...claims, ...newQuestions]) {
    for (const id of stringArray(owner.verification)) if (!topVerification.has(id)) violations.push(`claim/new-question verification ${id} is absent from top-level verification`);
  }
  const newQuestionIds = newQuestions.map((question) => String(question.id));
  if (unique(newQuestionIds).length !== newQuestionIds.length) violations.push("newQuestions contains duplicate ids");
  const approvedQuestions = contract.approvedQuestionIds ?? [];
  const assignedFacets = contract.assignedFacetIds ?? [];
  const coveredQuestions = new Set<string>();
  const coveredFacets = new Set<string>();
  const claimIds = new Set<string>();
  for (const claim of claims) {
    const id = String(claim.id);
    if (claimIds.has(id)) violations.push(`claims contains duplicate id ${id}`);
    claimIds.add(id);
    for (const questionId of stringArray(claim.questions)) {
      if (!approvedQuestions.includes(questionId)) violations.push(`claim ${id} references unapproved question ${questionId}`);
      else coveredQuestions.add(questionId);
    }
    for (const facetId of stringArray(claim.facets)) {
      if (!assignedFacets.includes(facetId)) violations.push(`claim ${id} references unassigned facet ${facetId}`);
      else coveredFacets.add(facetId);
    }
  }
  if (!(contract.sharedEvidenceOwnerIds ?? []).includes(String(output.sharedEvidenceOwner))) violations.push("sharedEvidenceOwner is not Parent-approved");
  for (const id of stringArray(output.sharedEvidenceUsed)) if (!recordIndex.has(id)) violations.push(`sharedEvidenceUsed references unknown record ${id}`);

  const status = statusOf(output);
  const hasRemap = newQuestions.length > 0 || stringArray(output.overlapObserved).length > 0 || stringArray(output.dependencyChanges).length > 0;
  const hasConflict = stringArray(output.blockingConflicts).length > 0;
  const blockedDependencyIds = stringArray(output.blockedDependencies);
  const hasBlockedDependency = blockedDependencyIds.length > 0;
  for (const id of blockedDependencyIds) if (!(contract.terminalDependencyIds ?? []).includes(id)) violations.push(`blockedDependencies references unapproved dependency ${id}`);
  if (hasRemap && status !== "needs-remap") violations.push("new question/overlap/dependency change requires needs-remap status");
  if (status === "needs-remap" && !hasRemap) violations.push("needs-remap status requires a remap trigger");
  if (!hasRemap && hasConflict && status !== "conflict") violations.push("blocking conflict requires conflict status");
  if (status === "conflict" && !hasConflict) violations.push("conflict status requires blockingConflicts");
  if (!hasRemap && !hasConflict && hasBlockedDependency && status !== "blocked-by-dependency") violations.push("blocked dependency requires blocked-by-dependency status");
  if (status === "blocked-by-dependency" && !hasBlockedDependency) violations.push("blocked-by-dependency status requires blockedDependencies");
  if (status === "complete") {
    if (claims.length === 0 || objectArray(output.records).length === 0) violations.push("complete requires claims and records");
    for (const id of approvedQuestions) if (!coveredQuestions.has(id)) violations.push(`complete does not cover question ${id}`);
    for (const id of assignedFacets) if (!coveredFacets.has(id)) violations.push(`complete does not cover facet ${id}`);
    if (hasConflict || stringArray(output.gaps).length > 0 || hasRemap || hasBlockedDependency || output.overflow !== null) violations.push("complete contains a conflict, gap, remap trigger, blocked dependency, or overflow");
  }
}

function admitCompactOutput(
  contract: CompactRecordReaderAdmissionContract,
  value: unknown,
 ): RecordReaderAdmissionReceipt {
  assertCompactContract(contract);
  const violations: string[] = [];
  const warnings: string[] = [];
  const outputCharacters = serializedCharacterCount(value);
  validateSchemaValue(buildCompactOutputSchema(contract), value, "$", violations);
  if (!isObject(value)) {
    return {
      schemaVersion: "record-reader-admission-receipt/v2",
      valid: false,
      success: false,
      admittedStatus: "invalid-packet",
      outputCharacters,
      outputCharacterBudget: contract.budget.hardOutputCharacters,
      outputCharacterTarget: contract.budget.targetOutputCharacters,
      outputCharacterHardLimit: contract.budget.hardOutputCharacters,
      overTarget: outputCharacters > contract.budget.targetOutputCharacters,
      outputMeasurement: "compact-json-unicode-code-points/v1",
      violations: unique(violations),
      warnings,
    };
  }
  if (outputCharacters > contract.budget.hardOutputCharacters) violations.push(`output characters ${outputCharacters} exceed hard limit ${contract.budget.hardOutputCharacters}`);
  else if (outputCharacters > contract.budget.targetOutputCharacters) warnings.push(`output characters ${outputCharacters} exceed soft target ${contract.budget.targetOutputCharacters}`);
  const recordIndex = verifyCompactCommon(contract, value, violations);
  if (contract.mode === "candidate-map") verifyCompactCandidate(contract, value, recordIndex, violations);
  else verifyCompactClaim(contract, value, recordIndex, violations);
  const reportedStatus = statusOf(value);
  const statuses = contract.mode === "candidate-map" ? CANDIDATE_STATUSES : CLAIM_STATUSES;
  if (!reportedStatus || !statuses.includes(reportedStatus)) violations.push(`invalid status for ${contract.mode}: ${String(reportedStatus)}`);
  const uniqueViolations = unique(violations);
  const valid = uniqueViolations.length === 0;
  const success = valid && (reportedStatus === "proposal-ready" || reportedStatus === "complete");
  return {
    schemaVersion: "record-reader-admission-receipt/v2",
    valid,
    success,
    reportedStatus,
    admittedStatus: valid && reportedStatus ? reportedStatus : "invalid-packet",
    outputCharacters,
    outputCharacterBudget: contract.budget.hardOutputCharacters,
    outputCharacterTarget: contract.budget.targetOutputCharacters,
    outputCharacterHardLimit: contract.budget.hardOutputCharacters,
    overTarget: outputCharacters > contract.budget.targetOutputCharacters,
    outputMeasurement: "compact-json-unicode-code-points/v1",
    violations: uniqueViolations,
    warnings,
  };
}

export function assertContract(contract: AnyRecordReaderAdmissionContract): void {
  if (isCompactContract(contract)) assertCompactContract(contract);
  else assertLegacyContract(contract);
}

export function buildRecordReaderOutputSchema(contract: AnyRecordReaderAdmissionContract): JsonSchema {
  return isCompactContract(contract) ? buildCompactOutputSchema(contract) : buildLegacyOutputSchema(contract);
}

export function admitRecordReaderOutput(
  contract: AnyRecordReaderAdmissionContract,
  value: unknown,
 ): RecordReaderAdmissionReceipt {
  return isCompactContract(contract) ? admitCompactOutput(contract, value) : admitLegacyOutput(contract, value);
}

interface CliOptions {
  command?: "digest" | "schema" | "validate";
  contract?: string;
  output?: string;
}

function parseArgs(argv: string[]): CliOptions {
  const options: CliOptions = {};
  for (let index = 0; index < argv.length; index++) {
    const arg = argv[index];
    if (arg === "digest" || arg === "schema" || arg === "validate") options.command = arg;
    else if (arg === "--contract") options.contract = resolve(argv[++index] ?? "");
    else if (arg === "--output") options.output = resolve(argv[++index] ?? "");
    else if (arg === "--help" || arg === "-h") {
      console.log("Usage: record-reader-admission.ts digest --contract <compact-contract.json>\n       record-reader-admission.ts schema --contract <contract.json>\n       record-reader-admission.ts validate --contract <contract.json> --output <output.json>");
      process.exit(0);
    } else throw new Error(`Unknown argument: ${arg}`);
  }
  return options;
}

function readJson(path: string): unknown {
  try {
    return JSON.parse(readFileSync(path, "utf8"));
  } catch (error) {
    throw new Error(`Invalid JSON in ${path}: ${error instanceof Error ? error.message : String(error)}`, { cause: error });
  }
}

function main(): void {
  const options = parseArgs(process.argv.slice(2));
  if (!options.command || !options.contract) throw new Error("command and --contract are required");
  const contract = readJson(options.contract) as AnyRecordReaderAdmissionContract;
  if (options.command === "digest") {
    console.log(computeRecordReaderContractDigest(contract));
    return;
  }
  if (options.command === "schema") {
    console.log(JSON.stringify(buildRecordReaderOutputSchema(contract), null, 2));
    return;
  }
  if (!options.output) throw new Error("validate requires --output");
  const receipt = admitRecordReaderOutput(contract, readJson(options.output));
  console.log(JSON.stringify(receipt, null, 2));
  if (!receipt.valid) process.exitCode = 1;
}

if (import.meta.main) {
  try {
    main();
  } catch (error) {
    console.error(error instanceof Error ? error.message : String(error));
    process.exitCode = 2;
  }
}
