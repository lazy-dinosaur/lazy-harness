import { dirname, isAbsolute, resolve } from "node:path";
import { pathToFileURL } from "node:url";

/** Benchmark-only metadata snapshot from Pi's selected GPT-6 Sol definition.
 * Cost tiers are deliberately not claimed equivalent; this is not a live runner.
 * Native OAuth handlers are retained, never called or replaced with dummy keys.
 */
export function gpt6SolRegistration(nativeOAuth: unknown) {
  if (!nativeOAuth || typeof nativeOAuth !== "object") throw new Error("Native Codex OAuth handlers unavailable");
  const native = nativeOAuth as Record<string, unknown>;
  if (typeof native.name !== "string" || !native.name.trim()
      || typeof native.login !== "function" || typeof native.refreshToken !== "function") {
    throw new Error("Native Codex OAuth handlers unavailable");
  }
  return {
    api: "openai-codex-responses" as const,
    baseUrl: "https://chatgpt.com/backend-api",
    models: [{
      id: "gpt-6-sol", name: "GPT-6 Sol", reasoning: true,
      thinking: { mode: "effort" as const, efforts: ["medium"], defaultLevel: "medium" },
      input: ["text", "image"], contextWindow: 272000, maxTokens: 128000,
      cost: { input: 2, output: 10, cacheRead: 0.2, cacheWrite: 2.5 },
    }],
    oauth: { name: native.name, login: native.login, refreshToken: native.refreshToken },
  };
}

type Registration = ReturnType<typeof gpt6SolRegistration>;
export interface BenchmarkRegistrationAPI {
  registerProvider(provider: string, definition: Registration): void;
}

export function registerGpt6Sol(api: BenchmarkRegistrationAPI, nativeOAuth: unknown): void {
  api.registerProvider("openai-codex", gpt6SolRegistration(nativeOAuth));
}

/** Explicit installed-package root; no global installation/configuration changes.
 * This native internal import is intentionally OMP-version-specific and tested.
 */
export default async function registerBenchmarkModel(
  api: BenchmarkRegistrationAPI,
  packageRoot = process.env.LAZY_OMP_MODULE_ROOT ?? "",
): Promise<void> {
  if (!isAbsolute(packageRoot)) throw new Error("LAZY_OMP_MODULE_ROOT must be an absolute installed OMP package path");
  const oauthEntry = Bun.resolveSync("@oh-my-pi/pi-ai/oauth", packageRoot);
  const registryPath = resolve(dirname(oauthEntry), "../registry.ts");
  const { getProviderDefinition } = await import(pathToFileURL(registryPath).href);
  registerGpt6Sol(api, getProviderDefinition("openai-codex"));
}
