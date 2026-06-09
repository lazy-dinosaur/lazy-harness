#!/usr/bin/env bun
import { copyFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { homedir } from "node:os";

interface AntigravityServerEntry {
  command?: string;
  args?: string[];
  env?: Record<string, string>;
  cwd?: string;
  serverUrl?: string;
  url?: string;
  httpUrl?: string;
  headers?: Record<string, string>;
  authProviderType?: string;
  oauth?: Record<string, unknown>;
  disabled?: boolean;
  disabledTools?: string[];
  [key: string]: unknown;
}

interface PiServerEntry {
  command?: string;
  args?: string[];
  env?: Record<string, string>;
  cwd?: string;
  url?: string;
  headers?: Record<string, string>;
  auth?: "oauth" | "bearer" | false;
  bearerToken?: string;
  bearerTokenEnv?: string;
  oauth?: Record<string, unknown> | false;
  lifecycle?: "keep-alive" | "lazy" | "eager";
  exposeResources?: boolean;
  directTools?: boolean | string[];
  excludeTools?: string[];
  debug?: boolean;
  [key: string]: unknown;
}

interface McpConfig {
  mcpServers: Record<string, PiServerEntry>;
  imports?: string[];
  settings?: Record<string, unknown>;
  [key: string]: unknown;
}

interface Options {
  sources: string[];
  target: string;
  apply: boolean;
  overwrite: boolean;
  includeDisabled: boolean;
  prefix: string;
  googleCredentialsMode: "env" | "skip";
  workspace?: string;
}

interface ConvertedServer {
  sourceName: string;
  targetName: string;
  entry?: PiServerEntry;
  skipped?: string;
  warnings: string[];
  authBridge?: string;
}

const SECRET_KEY_RE = /(token|secret|password|authorization|bearer|credential|key)/i;

// Deliberately not read/copied: Antigravity OAuth token stores such as
// ~/.gemini/antigravity/mcp_oauth_tokens.json. Pi should use its own OAuth
// store, or the google_credentials bearerTokenEnv bridge below.

function expandHome(path: string): string {
  if (path === "~") return homedir();
  if (path.startsWith("~/")) return join(homedir(), path.slice(2));
  return path;
}

function defaultSources(workspace?: string): string[] {
  const home = homedir();
  const paths = [
    join(home, ".gemini", "config", "mcp_config.json"),
    join(home, ".gemini", "antigravity", "mcp_config.json"),
  ];
  if (workspace) {
    paths.push(join(workspace, ".agents", "mcp_config.json"));
    paths.push(join(workspace, "_agents", "mcp_config.json"));
  }
  return paths;
}

function stripJsonc(text: string): string {
  let out = "";
  let inString = false;
  let quote = "";
  let escaped = false;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    const next = text[i + 1];
    if (inString) {
      out += ch;
      if (escaped) {
        escaped = false;
      } else if (ch === "\\") {
        escaped = true;
      } else if (ch === quote) {
        inString = false;
      }
      continue;
    }
    if (ch === '"' || ch === "'") {
      inString = true;
      quote = ch;
      out += ch;
      continue;
    }
    if (ch === "/" && next === "/") {
      while (i < text.length && text[i] !== "\n") i++;
      out += "\n";
      continue;
    }
    if (ch === "/" && next === "*") {
      i += 2;
      while (i < text.length && !(text[i] === "*" && text[i + 1] === "/")) i++;
      i++;
      continue;
    }
    out += ch;
  }
  return out.replace(/,\s*([}\]])/g, "$1");
}

function parseJsoncFile(path: string): Record<string, unknown> {
  if (!existsSync(path)) return {};
  const raw = readFileSync(path, "utf8").replace(/^\uFEFF/, "");
  if (!raw.trim()) return {};
  return JSON.parse(stripJsonc(raw));
}

function readAntigravityServers(path: string): Record<string, AntigravityServerEntry> {
  const parsed = parseJsoncFile(path);
  const servers = parsed.mcpServers;
  if (!servers || typeof servers !== "object" || Array.isArray(servers)) return {};
  return servers as Record<string, AntigravityServerEntry>;
}

function readPiConfig(path: string): McpConfig {
  if (!existsSync(path)) return { mcpServers: {}, imports: ["claude-code"] };
  const parsed = JSON.parse(readFileSync(path, "utf8"));
  if (!parsed.mcpServers || typeof parsed.mcpServers !== "object" || Array.isArray(parsed.mcpServers)) {
    parsed.mcpServers = {};
  }
  return parsed as McpConfig;
}

function envNameForGoogleCredentials(serverName: string): string {
  return `ANTIGRAVITY_MCP_${serverName.replace(/[^A-Za-z0-9]+/g, "_").replace(/^_+|_+$/g, "").toUpperCase()}_ACCESS_TOKEN`;
}

function copyKnownBooleans(source: AntigravityServerEntry, target: PiServerEntry) {
  for (const key of ["exposeResources", "directTools", "debug"] as const) {
    if (typeof source[key] === "boolean") target[key] = source[key] as boolean;
  }
  if (Array.isArray(source.directTools)) target.directTools = source.directTools as string[];
}

function convertServer(name: string, source: AntigravityServerEntry, options: Options): ConvertedServer {
  const targetName = `${options.prefix}${name}`;
  const warnings: string[] = [];
  if (source.disabled && !options.includeDisabled) {
    return { sourceName: name, targetName, skipped: "disabled", warnings };
  }

  const target: PiServerEntry = {};
  if (source.command) target.command = source.command;
  if (Array.isArray(source.args)) target.args = source.args;
  if (source.env && typeof source.env === "object" && !Array.isArray(source.env)) target.env = source.env;
  if (typeof source.cwd === "string") target.cwd = source.cwd;

  const url = source.serverUrl || source.url || source.httpUrl;
  if (typeof url === "string" && url.trim()) target.url = url;
  if (source.headers && typeof source.headers === "object" && !Array.isArray(source.headers)) target.headers = source.headers;
  if (Array.isArray(source.disabledTools)) target.excludeTools = source.disabledTools;
  copyKnownBooleans(source, target);

  let authBridge: string | undefined;
  if (source.authProviderType === "google_credentials") {
    if (options.googleCredentialsMode === "skip") {
      warnings.push("authProviderType=google_credentials skipped; use --google-credentials=env to emit bearerTokenEnv bridge");
    } else {
      const envName = envNameForGoogleCredentials(targetName);
      target.auth = "bearer";
      target.bearerTokenEnv = envName;
      authBridge = `export ${envName}=\"$(gcloud auth application-default print-access-token)\"`;
      warnings.push("google_credentials converted to Pi bearerTokenEnv bridge; refresh/export the env var before running Pi");
    }
  } else if (source.authProviderType && source.authProviderType !== "none") {
    warnings.push(`unsupported authProviderType=${source.authProviderType}; copied transport fields only`);
  }

  if (source.oauth && typeof source.oauth === "object" && !Array.isArray(source.oauth)) {
    target.auth = "oauth";
    const oauth: Record<string, unknown> = {};
    for (const key of ["clientId", "clientSecret", "scope", "redirectUri", "clientName", "clientUri", "grantType"] as const) {
      if (source.oauth[key] !== undefined) oauth[key] = source.oauth[key];
    }
    target.oauth = oauth;
  } else if (target.url && !target.auth && !target.headers) {
    // Pi adapter auto-detects OAuth for remote MCP when auth is unset.
  }

  if (!target.command && !target.url) {
    return { sourceName: name, targetName, skipped: "missing command/serverUrl/url/httpUrl", warnings };
  }
  return { sourceName: name, targetName, entry: target, warnings, authBridge };
}

function redactValue(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(redactValue);
  if (value && typeof value === "object") {
    const out: Record<string, unknown> = {};
    for (const [key, child] of Object.entries(value as Record<string, unknown>)) {
      out[key] = SECRET_KEY_RE.test(key) ? "<redacted>" : redactValue(child);
    }
    return out;
  }
  if (typeof value === "string" && (value.length > 100 || SECRET_KEY_RE.test(value))) return "<redacted>";
  return value;
}

function parseArgs(argv: string[]): Options {
  const options: Options = {
    sources: [],
    target: join(homedir(), ".pi", "agent", "mcp.json"),
    apply: false,
    overwrite: false,
    includeDisabled: false,
    prefix: "",
    googleCredentialsMode: "env",
  };
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === "--source") options.sources.push(resolve(expandHome(argv[++i] || "")));
    else if (arg === "--target") options.target = resolve(expandHome(argv[++i] || ""));
    else if (arg === "--workspace") options.workspace = resolve(expandHome(argv[++i] || ""));
    else if (arg === "--prefix") options.prefix = argv[++i] || "";
    else if (arg === "--apply") options.apply = true;
    else if (arg === "--dry-run") options.apply = false;
    else if (arg === "--overwrite") options.overwrite = true;
    else if (arg === "--include-disabled") options.includeDisabled = true;
    else if (arg === "--google-credentials") {
      const value = argv[++i];
      if (value !== "env" && value !== "skip") throw new Error("--google-credentials must be env or skip");
      options.googleCredentialsMode = value;
    } else if (arg === "--help" || arg === "-h") {
      printHelp();
      process.exit(0);
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }
  if (!options.sources.length) options.sources = defaultSources(options.workspace).map((p) => resolve(p));
  return options;
}

function printHelp() {
  console.log(`Usage: bun packages/lazy-harness-pi/scripts/import-antigravity-mcp.ts [options]\n\n` +
`Imports Antigravity MCP config into Pi MCP adapter config without copying Antigravity token stores.\n\n` +
`Options:\n` +
`  --source <path>              Antigravity mcp_config.json path. Repeatable.\n` +
`  --workspace <path>           Also read <workspace>/.agents/mcp_config.json and _agents/mcp_config.json.\n` +
`  --target <path>              Pi mcp.json target. Default: ~/.pi/agent/mcp.json\n` +
`  --apply                      Write merged target. Default is dry-run.\n` +
`  --dry-run                    Print redacted summary only.\n` +
`  --overwrite                  Replace existing Pi servers with the same name. Default skips conflicts.\n` +
`  --prefix <prefix>            Prefix imported server names. Useful to avoid conflicts.\n` +
`  --include-disabled           Import Antigravity disabled servers. Default skips disabled.\n` +
`  --google-credentials env     Convert google_credentials to bearerTokenEnv bridge. Default.\n` +
`  --google-credentials skip    Skip google_credentials auth bridge conversion.\n`);
}

function main() {
  const options = parseArgs(process.argv.slice(2));
  const sourceReports: Array<{ path: string; exists: boolean; serverCount: number }> = [];
  const converted: ConvertedServer[] = [];
  for (const sourcePath of options.sources) {
    const exists = existsSync(sourcePath);
    const servers = exists ? readAntigravityServers(sourcePath) : {};
    sourceReports.push({ path: sourcePath, exists, serverCount: Object.keys(servers).length });
    for (const [name, entry] of Object.entries(servers)) {
      converted.push(convertServer(name, entry, options));
    }
  }

  const target = readPiConfig(options.target);
  const targetServers = target.mcpServers || {};
  const imported: string[] = [];
  const skipped: Array<{ name: string; targetName: string; reason: string }> = [];
  const warnings: Array<{ name: string; warning: string }> = [];
  const authBridgeExports: string[] = [];

  for (const result of converted) {
    for (const warning of result.warnings) warnings.push({ name: result.targetName, warning });
    if (result.authBridge) authBridgeExports.push(result.authBridge);
    if (result.skipped || !result.entry) {
      skipped.push({ name: result.sourceName, targetName: result.targetName, reason: result.skipped || "conversion failed" });
      continue;
    }
    if (targetServers[result.targetName] && !options.overwrite) {
      skipped.push({ name: result.sourceName, targetName: result.targetName, reason: "target exists; use --overwrite or --prefix" });
      continue;
    }
    targetServers[result.targetName] = result.entry;
    imported.push(result.targetName);
  }

  target.mcpServers = targetServers;
  if (!Array.isArray(target.imports)) target.imports = [];
  if (!target.imports.includes("claude-code")) target.imports.push("claude-code");

  let backupPath: string | undefined;
  if (options.apply) {
    mkdirSync(dirname(options.target), { recursive: true });
    if (existsSync(options.target)) {
      const stamp = new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z");
      backupPath = `${options.target}.bak-antigravity-${stamp}`;
      copyFileSync(options.target, backupPath);
    }
    writeFileSync(options.target, JSON.stringify(target, null, 2) + "\n");
  }

  const summary = {
    mode: options.apply ? "apply" : "dry-run",
    target: options.target,
    backupPath,
    sources: sourceReports,
    imported,
    skipped,
    warnings,
    authBridgeExports,
    finalServerCount: Object.keys(target.mcpServers).length,
    redactedImportedPreview: Object.fromEntries(imported.map((name) => [name, redactValue(target.mcpServers[name])])),
  };
  console.log(JSON.stringify(summary, null, 2));
}

try {
  main();
} catch (error) {
  console.error(error instanceof Error ? error.message : String(error));
  process.exit(1);
}
