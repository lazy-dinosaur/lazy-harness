import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import lazyHarness from "../extensions/lazy-harness/index.ts";
import { explicitOmpOutputMode } from "./output-mode.ts";
import { OmpReaderTransport } from "./reader-transport.ts";
import { onOmpNativeSteer } from "./steering.ts";

type OmpExtensionAPI = ExtensionAPI & { on(event: "session_switch", listener: () => void): void };

/** OMP-only entrypoint: common policy/guards remain owned by the shared core. */
export default function lazyHarnessOmp(api: OmpExtensionAPI) {
  lazyHarness(api, {
    outputMode: explicitOmpOutputMode(process.argv.slice(2)),
    readerTransport: new OmpReaderTransport(api),
    onNativeSteer: listener => onOmpNativeSteer(api, listener),
    onNativeSessionSwitch: listener => api.on("session_switch", listener),
  });
}
