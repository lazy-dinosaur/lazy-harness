import { createHash } from "node:crypto";
import { readFileSync, realpathSync } from "node:fs";
import { fileURLToPath } from "node:url";

const source = new URL("../../agents/record-reader.md", import.meta.url);
const guard = new URL("./index.ts", import.meta.url);
export const FABRIC_READER_DEFAULT_MODEL = "openai/gpt-6-luna:low";
const fields = ["name", "package", "description", "systemPromptMode", "inheritProjectContext", "inheritSkills", "defaultContext", "acceptanceRole", "tools", "subagentOnlyExtensions", "output", "turnBudget"];

export type FabricReaderDefinition = {
  body: string;
  guardPath: string;
  tools: string[];
  turnBudget: { maxTurns: number; graceTurns: number };
  contractHash: string;
};
export type FabricReaderPolicyState = {
  contractHash: string;
  guardPath: string;
  systemPromptMode: "replace";
  inheritProjectContext: false;
  inheritSkills: false;
  context: "fresh";
  acceptanceRole: "read-only";
  output: false;
  maxTurns: number;
  graceTurns: number;
  turnCount: number;
  wrapUpRequested: boolean;
  turnBudgetExceeded: boolean;
};

/** Parse the existing role definition; unknown or changed semantics fail, never silently disappear. */
export function parseFabricReaderDefinition(text: string): FabricReaderDefinition {
  const match = text.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n([\s\S]*)$/);
  if (!match) throw new Error("Reader definition frontmatter missing");
  const values: Record<string, string> = {};
  for (const line of match[1].split(/\r?\n/)) {
    const entry = line.match(/^([A-Za-z]+):[ \t]*(.+)$/);
    if (!entry || !fields.includes(entry[1]) || Object.hasOwn(values, entry[1])) throw new Error("Reader definition contains unsupported or duplicate frontmatter");
    values[entry[1]] = entry[2];
  }
  if (fields.some(key => !values[key])) throw new Error("Reader definition frontmatter is incomplete");
  const fixed: Record<string, string> = {
    name: "record-reader", package: "lazy-harness", systemPromptMode: "replace",
    inheritProjectContext: "false", inheritSkills: "false", defaultContext: "fresh",
    acceptanceRole: "read-only", output: "false",
  };
  if (Object.entries(fixed).some(([key, value]) => values[key] !== value)) throw new Error("Reader definition no longer matches the supported dedicated role");
  const tools = values.tools.split(",").map(value => value.trim());
  if (JSON.stringify(tools) !== JSON.stringify(["read", "grep", "bash"])) throw new Error("Reader tools must preserve the canonical read-only ceiling");
  const guardPath = realpathSync(fileURLToPath(new URL(values.subagentOnlyExtensions, source)));
  if (guardPath !== realpathSync(fileURLToPath(guard))) throw new Error("Reader guard extension differs from the canonical child guard");
  const budget = JSON.parse(values.turnBudget);
  if (!budget || Object.keys(budget).sort().join() !== "graceTurns,maxTurns"
    || !Number.isSafeInteger(budget.maxTurns) || budget.maxTurns < 1
    || !Number.isSafeInteger(budget.graceTurns) || budget.graceTurns < 0) throw new Error("Reader turnBudget is invalid");
  const body = match[2].trim();
  if (!body.startsWith("LAZY_HARNESS_ROLE: record-reader/reader-join-v1\n")) throw new Error("Reader role prompt missing");
  const contractHash = createHash("sha256").update(JSON.stringify({ values, body })).digest("hex");
  return { body, guardPath, tools, turnBudget: budget, contractHash };
}

export function fabricReaderDefinition(): FabricReaderDefinition {
  return parseFabricReaderDefinition(readFileSync(source, "utf8"));
}

/** Map replace/no-project/no-skills explicitly, not merely by dropping YAML. */
export function applyFabricReaderPrompt(event: any, guardModule: string): FabricReaderPolicyState {
  const definition = fabricReaderDefinition();
  if (realpathSync(fileURLToPath(guardModule)) !== definition.guardPath) throw new Error("Fabric Reader child guard did not load from its declared extension");
  const prompt = fabricReaderSystemPrompt(definition);
  if (event.systemPromptOptions) {
    Object.assign(event.systemPromptOptions, {
      customPrompt: prompt, forceSystemPrompt: prompt, contextFiles: [], skills: [],
      sections: {}, appendSystemPrompt: "", promptGuidelines: [], toolGuidelines: {}, toolSnippets: {},
      selectedTools: [...definition.tools, "fabric_exec"],
    });
  }
  return {
    contractHash: definition.contractHash, guardPath: definition.guardPath,
    systemPromptMode: "replace", inheritProjectContext: false, inheritSkills: false,
    context: "fresh", acceptanceRole: "read-only", output: false,
    ...definition.turnBudget, turnCount: 0, wrapUpRequested: false, turnBudgetExceeded: false,
  };
}

export function fabricReaderSystemPrompt(definition = fabricReaderDefinition()): string {
  return `${definition.body}\n\nFabric transport encoding only: use fabric_exec with pi.read/pi.grep/pi.bash. Do not call agents, other extensions, native executors or nested delegation. This changes tool syntax, not the Reader policy above.`;
}

export function advanceFabricReaderTurn(state: FabricReaderPolicyState, message: any): boolean {
  if (message?.role !== "assistant") return false;
  state.turnCount += 1;
  if (state.turnCount >= state.maxTurns) state.wrapUpRequested = true;
  const wantsTools = Array.isArray(message.content) && message.content.some((part: any) => part?.type === "toolCall");
  // Two grace responses may finish normally; no further tool cycle beyond the hard ceiling.
  if (state.turnCount > state.maxTurns + state.graceTurns
    || (state.turnCount >= state.maxTurns + state.graceTurns && wantsTools)) state.turnBudgetExceeded = true;
  return state.turnBudgetExceeded;
}

export const FABRIC_READER_WRAP_UP = "Reader turn budget reached: finish within the remaining grace turns. Return the existing complete/incomplete/conflict packet honestly; do not conceal missing evidence or start unrelated work.";

export function validateFabricReaderPolicy(state: FabricReaderPolicyState | undefined, contractHash: string, guardPath: string): boolean {
  const expected = fabricReaderDefinition();
  return Boolean(state && state.contractHash === contractHash && state.guardPath === guardPath
    && state.maxTurns === expected.turnBudget.maxTurns && state.graceTurns === expected.turnBudget.graceTurns
    && state.systemPromptMode === "replace" && state.inheritProjectContext === false && state.inheritSkills === false
    && state.context === "fresh" && state.acceptanceRole === "read-only" && state.output === false
    && Number.isSafeInteger(state.turnCount) && state.turnCount >= 1
    && state.turnCount <= state.maxTurns + state.graceTurns && state.turnBudgetExceeded === false);
}
