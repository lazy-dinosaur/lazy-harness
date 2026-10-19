#!/usr/bin/env bun
import { activateOmpReader } from "../omp/reader-definition.ts";

const usage = "Usage: bun scripts/activate-omp-reader.ts --target ROOT --model PROVIDER/MODEL [--apply]\nDefault is preview-only. Restart OMP after activation. Native Reader support remains Experimental.";
const args = process.argv.slice(2);
if (args.includes("--help")) {
  console.log(usage);
} else {
  try {
    let target: string | undefined;
    let model: string | undefined;
    let apply = false;
    for (let i = 0; i < args.length; i++) {
      const flag = args[i];
      const equal = flag.indexOf("=");
      const name = equal < 0 ? flag : flag.slice(0, equal);
      if (flag === "--apply" && !apply) { apply = true; continue; }
      const value = equal < 0 ? args[i + 1] : flag.slice(equal + 1);
      if (name === "--target" && !target && value && !value.startsWith("--")) { target = value; if (equal < 0) i++; }
      else if (name === "--model" && !model && value && !value.startsWith("--")) { model = value; if (equal < 0) i++; }
      else throw new Error(`Unknown, repeated, or incomplete argument: ${flag}`);
    }
    if (!target || !model) throw new Error(usage);
    console.log(JSON.stringify(activateOmpReader(target, model, apply), null, 2));
  } catch (error) {
    console.error(String(error));
    process.exitCode = 1;
  }
}
