import type { ModelRuntime } from '@earendil-works/pi-coding-agent'
import { bindModelBackend, exposeModelBackend, type MonitoringModelBackend, type MonitoringModelLimits } from '../../../../../vendor/lazy-harness-monitoring/composition.ts'
import { assertModel, assertOpenRouterJevOnly } from '../../../../../vendor/lazy-harness-monitoring/hosts/pi/src/eval/compaction-transport.ts'

export { assertOpenRouterJevOnly }
export const JEV_MODEL = 'openrouter/typesafe/jev-1.14'
export type ClassifierModel = Parameters<ModelRuntime['classify']>[0]
export type ClassifierRuntime = Pick<ModelRuntime, 'classify'>
/** A bounded native backend, NOT the monitoring eval transport. Only the module router owns dispatch. */
export function createPiModelBinding(runtime: ClassifierRuntime, model: ClassifierModel, limits: MonitoringModelLimits) {
  assertModel(model)
  let stopped = false
  const estimate: MonitoringModelBackend['estimate'] = request => {
    if (request.kind !== 'native-classifier') throw Error('native classifier required')
    const maxInputTokens = Buffer.byteLength(JSON.stringify(request.body), 'utf8') + 4096
    if (maxInputTokens > model.contextWindow) throw Error('classifier context bound')
    return { maxInputTokens, maxEstimatedUsd: Math.ceil(maxInputTokens * model.cost.input / 1e6 * 1e9) / 1e9 }
  }
  const backend: MonitoringModelBackend = {
    version: '1', provider: 'openrouter', model: 'typesafe/jev-1.14', kind: 'native-classifier', roles: ['judge'],
    parametersSchema: { type: 'object', additionalProperties: false, properties: {} }, ceilings: limits, estimate,
    async invoke(request, context) {
      if (stopped) throw Error('classifier stopped after uncertain outcome')
      assertModel(model)
      context.signal.throwIfAborted()
      const bound = estimate(request, context.profile)
      if (bound.maxInputTokens > context.reservation.maxInputTokens || bound.maxEstimatedUsd > context.reservation.maxEstimatedUsd) throw Error('missing model reservation')
      try {
        // Empty env overrides environment credentials: ModelRuntime resolves the stored OpenRouter credential.
        const value = await runtime.classify(model, request.body as unknown as Parameters<ModelRuntime['classify']>[1], {
          signal: context.signal, maxRetries: 0, timeoutMs: context.profile.limits.timeoutMs,
          env: { OPENROUTER_API_KEY: '' },
        })
        if (context.signal.aborted || value.stopReason !== 'stop' || value.provider !== model.provider || value.model !== model.id || value.api !== model.api) throw Error('invalid classifier completion')
        return { value }
      } catch { stopped = true; throw Error('classifier outcome uncertain; no retry') }
    },
  }
  // Router reserves calls/tokens/USD before invoke and performs native request generation + decoding.
  // It retains raw capacity through settlement; budgets are lifetime, not reset per opportunity.
  return { modelConfig: { modelConfigVersion: 1, profiles: [{ id: 'jev', backend: 'pi-jev', backendVersion: '1', provider: 'openrouter', model: 'typesafe/jev-1.14', role: 'judge', parameters: {}, referenceThreshold: 0.5 }], defaultJudgeProfile: 'jev' }, modelHost: {
    backends: { 'pi-jev': bindModelBackend(exposeModelBackend(backend)) }, maxProfiles: 1, maxTotalConcurrent: limits.maxConcurrent,
  } }
}
