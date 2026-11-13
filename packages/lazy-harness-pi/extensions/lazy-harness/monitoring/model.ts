import { bindModelBackend, exposeModelBackend, type MonitoringModelBackend, type MonitoringModelLimits } from '../../../../../vendor/lazy-harness-monitoring/composition.ts'
// Local structural boundary: the running Pi supplies the registry, not the host's installed SDK.
export type ClassifierModel = { provider: string; id: string; api: string; type: string; baseUrl: string; contextWindow: number; cost: { input: number; output: number; cacheRead: number; cacheWrite: number; tiers?: readonly unknown[] } }
export type ClassifierRuntime = { classify(model: ClassifierModel, body: unknown, options: { signal: AbortSignal; maxRetries: number; timeoutMs: number; env: Record<string, string> }): Promise<{ stopReason: string; provider: string; model: string; api: string; [key: string]: unknown }> }
export type ClassifierRegistry = ClassifierRuntime & { getModelOfType(type: 'classifier', provider: string, id: string): ClassifierModel | undefined }
export function classifierFromContext(ctx: { modelRegistry?: unknown }) {
  const registry = ctx.modelRegistry as Partial<ClassifierRegistry> | undefined
  if (typeof registry?.getModelOfType !== 'function' || typeof registry.classify !== 'function') throw Error('Pi context classifier registry unavailable')
  const model = registry.getModelOfType('classifier', 'openrouter', 'typesafe/jev-1.14')
  if (!model) throw Error('pinned Jev classifier unavailable')
  assertModel(model)
  return { runtime: registry as ClassifierRegistry, model }
}
export function assertOpenRouterJevOnly(model: Pick<ClassifierModel, 'provider' | 'id'>) {
  if (model.provider === 'openrouter' && !/^typesafe\/jev-\d+\.\d+$/.test(model.id)) throw Error('OpenRouter is used only for pinned TypeSafe Jev models')
}
function assertModel(model: ClassifierModel) {
  assertOpenRouterJevOnly(model)
  if (`${model.provider}/${model.id}` !== JEV_MODEL || model.api !== 'typesafe-system-one' || model.type !== 'classifier' || model.baseUrl !== 'https://openrouter.ai/api/v1') throw Error('exact classifier/API/endpoint required')
  if (!Number.isFinite(model.cost.input) || model.cost.input <= 0 || model.cost.output !== 0 || model.cost.cacheRead !== 0 || model.cost.cacheWrite !== 0 || model.cost.tiers?.length) throw Error('unsupported classifier pricing')
}
/** Bounded failure class from a provider/transport message: category + optional HTTP status, never the raw text. */
export function classifierErrorKind(message?: string) {
  if (!message) return 'none'
  const code = message.match(/\b([45]\d\d)\b/)?.[1]
  const kind = /unauthori|forbidden|api.?key|credential|auth/i.test(message) ? 'auth' : /time.?out|timed out|deadline/i.test(message) ? 'timeout' : /rate|quota|too many/i.test(message) ? 'rate' : /too large|too long|context|length|payload|exceed/i.test(message) ? 'size' : /abort|cancel/i.test(message) ? 'aborted' : /network|fetch|econn|socket|dns/i.test(message) ? 'network' : 'other'
  return code ? `${kind}_${code}` : kind
}
export const JEV_MODEL = 'openrouter/typesafe/jev-1.14'
/** A bounded native backend, NOT the monitoring eval transport. Only the module router owns dispatch. */
export function createPiModelBinding(runtime: ClassifierRuntime, model: ClassifierModel, limits: MonitoringModelLimits, observe?: (request: any, value: any, latencyMs: number, error: boolean, failure?: string) => void, scopeGeneration: () => number = () => 0) {
  assertModel(model)
  let stopped = false
  // This owner survives scope pipeline replacement. Reservations never refund, even on cancellation.
  const usage = { calls: 0, tokens: 0, usd: 0, active: 0, reportedTokens: 0, reportedUsd: 0, errors: 0, lastFailure: null as string | null }
  const remaining = () => ({ calls: Math.max(0, limits.maxCalls - usage.calls), tokens: Math.max(0, limits.maxReservedTokens - usage.tokens), usd: Math.max(0, limits.maxReservedUsd - usage.usd) })
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
      const tokens = bound.maxInputTokens + context.profile.limits.maxOutputTokens
      if (usage.calls >= limits.maxCalls || usage.tokens + tokens > limits.maxReservedTokens || usage.usd + bound.maxEstimatedUsd > limits.maxReservedUsd || usage.active >= limits.maxConcurrent) throw Error('session model budget unavailable')
      usage.calls++; usage.tokens += tokens; usage.usd += bound.maxEstimatedUsd; usage.active++
      const started = performance.now(), generation = scopeGeneration()
      let failure: string | undefined
      const notify = (value: any, error: boolean) => { try { observe?.(request, value, performance.now() - started, error, failure) } catch { /* advisory only */ } }
      try {
        // Empty env overrides environment credentials: Pi's registry resolves stored OpenRouter auth.
        const value = await runtime.classify(model, request.body, {
          signal: context.signal, maxRetries: 0, timeoutMs: context.profile.limits.timeoutMs,
          env: { OPENROUTER_API_KEY: '' },
        })
        if (context.signal.aborted) { failure = 'aborted'; throw Error('aborted') }
        if (value.stopReason !== 'stop') { failure = 'stop_' + String(value.stopReason) + '_' + classifierErrorKind(typeof value.errorMessage === 'string' ? value.errorMessage : undefined); throw Error('classifier stop') }
        if (value.provider !== model.provider || value.model !== model.id || value.api !== model.api) { failure = 'field_mismatch'; throw Error('invalid classifier completion') }
        const u = value.usage as any
        if (Number.isFinite(u?.totalTokens) && u.totalTokens >= 0) usage.reportedTokens += u.totalTokens
        if (Number.isFinite(u?.cost?.total) && u.cost.total >= 0) usage.reportedUsd += u.cost.total
        notify(value, false)
        return { value }
      } catch (e) { failure ??= 'threw_' + classifierErrorKind(e instanceof Error ? e.message : String(e)); usage.errors++; usage.lastFailure = failure; if (scopeGeneration() === generation) stopped = true; notify(undefined, true); throw Error('classifier outcome uncertain; no retry') }
      finally { usage.active-- }
    },
  }
  // Router reserves calls/tokens/USD before invoke and performs native request generation + decoding.
  // It retains raw capacity through settlement; budgets are lifetime, not reset per opportunity.
  return { usage, remaining, get stopped() { return stopped }, modelConfig: { modelConfigVersion: 1, profiles: [{ id: 'jev', backend: 'pi-jev', backendVersion: '1', provider: 'openrouter', model: 'typesafe/jev-1.14', role: 'judge', parameters: {}, referenceThreshold: 0.5 }], defaultJudgeProfile: 'jev' }, modelHost: {
    backends: { 'pi-jev': bindModelBackend(exposeModelBackend(backend)) }, maxProfiles: 1, maxTotalConcurrent: limits.maxConcurrent,
  } }
}
