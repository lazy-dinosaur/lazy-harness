import { existsSync, lstatSync, mkdirSync, readFileSync, realpathSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";

export const OMP_READER_NAME = "lazy-harness.record-reader";
export const OMP_READER_CONTEXT = "Read-only canonical record loading; the assignment supplies the full identity and budget.";
const OWNER = "<!-- lazy-harness:omp-record-reader:v1 -->";
const ROLE = "LAZY_HARNESS_ROLE: record-reader/reader-join-v1";
const canonicalPrompt = new URL("../agents/record-reader.md", import.meta.url);

/** Adapt frontmatter only: the Reader policy body has one package-owned source. */
export function ompReaderDefinition(model: string): string {
  if (!/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_./-]+$/.test(model)) {
    throw new Error("Reader requires an explicit provider/model id (no alias, thinking suffix, or fallback list)");
  }
  const source = readFileSync(canonicalPrompt, "utf8");
  const frontmatter = source.match(/^---\r?\n[\s\S]*?\r?\n---\r?\n/);
  if (!frontmatter) throw new Error("canonical Reader frontmatter missing");
  const body = source.slice(frontmatter[0].length).trim();
  if (!body.startsWith(ROLE)) throw new Error("canonical Reader role marker missing");
  const output = JSON.stringify({ type: "object", properties: { packet: { type: "string" } }, required: ["packet"], additionalProperties: false });
  const encoding = "OMP transport encoding: read has only a path field. Use '.lazy-harness/...:raw:N-M', never offset/limit. Its charged limit includes up to 1 leading and 3 trailing context lines; reserve those inside maxLinesPerRead (e.g. 1-47 charges 50). The runtime verifies returned line coverage before delivering content. Return the exact result packet described below using the exposed native yield schema: yield({data:{packet: TEXT}}) on OMP 18, or yield({result:{data:{packet: TEXT}}}) when the schema exposes result. Never send both shapes or use a text-only final turn. These encoding rules replace only the Pi tool-call and final-response syntax; all canonical Reader boundaries remain unchanged.";
  return ["---", `name: ${OMP_READER_NAME}`, "description: Dedicated read-only canonical Lazy-Harness record loader", 'tools: ["read", "grep", "bash"]', "spawns: []", `model: ${JSON.stringify(model)}`, "thinkingLevel: low", "readSummarize: false", "autoloadSkills: []", "blocking: true", `output: ${output}`, "---", "", OWNER, "", encoding, "", body, ""].join("\n");
}

export type OmpReaderActivation = {
  root: string;
  path: string;
  action: "create" | "unchanged";
  applied: boolean;
};

/** Explicit, create-only project activation; never edits global config or a user's agent. */
export function activateOmpReader(target: string, model: string, apply = false): OmpReaderActivation {
  const root = realpathSync(resolve(target));
  if (!existsSync(join(root, ".lazy-harness/bin/lazy"))) throw new Error("target is not an initialized lazy-harness root");
  const content = ompReaderDefinition(model);
  const directories = [join(root, ".omp"), join(root, ".omp/agents")];
  for (const directory of directories) {
    // lstat also sees broken links; existsSync alone would miss them.
    try {
      if (!lstatSync(directory).isDirectory()) throw new Error(`refusing non-directory or symlink: ${directory}`);
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code !== "ENOENT") throw error;
    }
  }
  const path = join(directories[1], `${OMP_READER_NAME}.md`);
  let existing: string | undefined;
  try {
    if (!lstatSync(path).isFile()) throw new Error(`refusing non-regular agent: ${path}`);
    existing = readFileSync(path, "utf8");
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code !== "ENOENT") throw error;
  }
  if (existing !== undefined && existing !== content) throw new Error(`existing Reader definition differs; explicit reconciliation required: ${path}`);
  const action = existing === undefined ? "create" : "unchanged";
  if (apply && action === "create") {
    mkdirSync(directories[1], { recursive: true });
    writeFileSync(path, content, { encoding: "utf8", flag: "wx" });
  }
  return { root, path, action, applied: apply };
}
