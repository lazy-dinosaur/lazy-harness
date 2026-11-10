import { createPiInputPortGenerations } from '@lazy-harness/monitoring-host-pi';
import { REFERENCES_MODULE_ID, createReferencesRegistration } from '@lazy-harness/monitoring-module-references';
import { validateRequiredInputPorts, type InputPortContext, type InputPortScope } from '@lazy-harness/monitoring-core/host';
import { ApprovedBudgetGate, MonitoringModuleRuntime, type RuntimeOptions } from '@lazy-harness/monitoring-core/engine/monitoring-engine-runtime.ts';
import type { MonitoringRunStage } from '@lazy-harness/monitoring-core';
import type { CaptureValidation } from '../capture-evidence.ts';
import { createHarnessReadRecordPort, type ReadRecordCatalog } from './read-record-port.ts';

export interface HarnessReferencesBindings {
  catalog: ReadRecordCatalog;
  context(): Omit<InputPortContext, 'scope'> | undefined;
  captureIdentity(): Readonly<{ root: string; epoch: number }> | undefined;
}
/** Inactive composition seam, NOT a Pi extension entry. Construction installs no
 * listeners. Only an explicit future caller may attach extension(pi), feed fresh
 * CaptureEvidence.evaluate receipts, or submit selected triggers to the runtime.
 * No model, catalog discovery, Fabric, input classifier or report transport here. */
export function createHarnessReferences(options: Readonly<{
  bindings: HarnessReferencesBindings;
  stage?: MonitoringRunStage;
  report?: RuntimeOptions['report'];
}>) {
  if (!options?.bindings || typeof options.bindings.catalog?.resolve !== 'function' ||
      typeof options.bindings.context !== 'function' || typeof options.bindings.captureIdentity !== 'function') {
    throw Error('Monitoring references require catalog, context and capture identity bindings');
  }
  const bindings = options.bindings, generations = createPiInputPortGenerations();
  const context = (): InputPortContext | undefined => {
    const scope = generations.current(), source = bindings.context();
    return scope && source ? { ...source, scope } : undefined;
  };
  const reads = createHarnessReadRecordPort({ context, captureIdentity: bindings.captureIdentity });
  const registration = createReferencesRegistration({ stage: options.stage ?? 'observe', readRecords: {
    port: reads.port,
    request(trigger, signal) {
      const c = context();
      if (!c) throw Error('Monitoring references generation is unavailable');
      return { protocolVersion: 1, scope: c.scope, sourceEventId: trigger.eventId,
        cursor: c.completeThroughCursor, sourceRevision: c.sourceRevision, grantRevision: c.grantRevision,
        documents: trigger.evidence.filter(e => e.kind === 'knowledge').map(e => ({ documentId: e.id, documentVersion: e.version })), signal };
    },
  } });
  const inputPorts = { [REFERENCES_MODULE_ID]: { 'already-read': { adapter: 'session.read-records', protocolVersion: 1 as const, port: reads.port } } };
  validateRequiredInputPorts(registration.moduleId, registration.declaration.needs, inputPorts);
  const runtime = new MonitoringModuleRuntime({ modules: [registration], handlers: registration.handlers,
    budget: new ApprovedBudgetGate(), report: options.report, maxActive: 1, maxQueued: 0, maxWork: 32 });
  return Object.freeze({ registration, inputPorts, runtime, reads, generations,
    extension: generations.extension,
    ingestCapture(capture: CaptureValidation, cursor: number, capturedScope: InputPortScope) {
      return reads.ingestCapture(capture, cursor, bindings.catalog, capturedScope);
    },
    close() { runtime.dispose(); reads.close(); generations.close(); },
  });
}
