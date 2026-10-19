import { expect, test } from "bun:test";
import { explicitOmpOutputMode } from "../omp/output-mode.ts";

for (const [args, expected] of [
  [[], undefined], [["-p"], "print"], [["--print"], "print"],
  [["--mode", "text", "-p"], "print"], [["--mode=json"], "json"],
  [["--mode", "rpc", "-p"], "rpc"], [["--print", "--mode=rpc-ui"], "rpc"],
  [["--mode=acp", "--print"], undefined], [["--mode=unknown", "-p"], undefined],
  [["--", "--print"], undefined], [["--system-prompt", "-p"], undefined],
  [["--append-system-prompt=--print"], undefined], [["--extension", "--print"], undefined],
  [["--resume", "--print"], "print"], [["-r", "--print"], "print"],
  [["--model", "scripted", "--print", "prompt containing --mode=rpc"], "print"],
  [["--mode"], undefined], [["--mode=json", "--mode", "rpc"], "rpc"],
] as const) {
  test(`OMP explicit output capability ${JSON.stringify(args)}`, () => {
    expect(explicitOmpOutputMode(args)).toBe(expected);
  });
}

test("OMP manifest selects the thin adapter, Pi retains its existing entry", async () => {
  const manifest = await Bun.file(new URL("../package.json", import.meta.url)).json();
  expect(manifest.omp.extensions).toEqual(["./omp/index.ts"]);
  expect(manifest.pi.extensions).toEqual(["./extensions"]);
});
