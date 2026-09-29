// Offline check of the h-1 path test used by harness-rules.ts (kept in sync by copy; run with node).
import { dirname, isAbsolute, relative, resolve as resolvePath } from "node:path";
import { homedir } from "node:os";
const outsideProject = (cwd, p) => {
  const abs = resolvePath(cwd, p.startsWith("~/") ? homedir() + p.slice(1) : p);
  const rel = relative(cwd, abs);
  if (!rel || (!rel.startsWith("..") && !isAbsolute(rel))) return false;
  const parent = dirname(cwd);
  const relParent = relative(parent, abs);
  return !relParent.startsWith("..") && !isAbsolute(relParent);
};
const BASH_OUT = /(?:^|[\s;&|(])(?:cd|find|ls|grep|rg|cat|head|tail|tree|fd)\s+(?:-\S+\s+)*(\.\.(?:\/[^\s;&|)]*)?|~\/[^\s;&|)]+|\/home\/[^\s;&|)]+)/g;
const cwd = "/home/lazydino/dev/lazy-harness.v2";
const bashPaths = (c) => [...c.matchAll(BASH_OUT)].map((m) => m[1]);
const cases = [
  ["src/a.ts", false], ["./x/../y", false], ["/home/lazydino/dev/lazy-harness.v2/README.md", false],
  ["../medivance/AGENTS.md", true], ["..", true], ["/home/lazydino/dev/other/x", true], ["~/dev/other", true],
  ["/tmp/x", false], ["/usr/bin/python3", false],
];
let fail = 0;
for (const [p, want] of cases) if (outsideProject(cwd, p) !== want) { fail++; console.log("path FAIL", p); }
const bash = [["find .. -name AGENTS.md", true], ["git status --short; rg -n foo src", false], ["cd ../lazy-harness && ls", true],
  ["/usr/bin/python3 -m pytest -q", false], ["cat /home/lazydino/dev/other/AGENTS.md", true]];
for (const [c, want] of bash) if (bashPaths(c).some((p) => outsideProject(cwd, p)) !== want) { fail++; console.log("bash FAIL", c); }
console.log(fail ? `FAILED ${fail}` : `outside-check ok ${cases.length + bash.length}`);
process.exit(fail ? 1 : 0);
