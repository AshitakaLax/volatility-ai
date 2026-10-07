// Runs the REAL Fidelity Bridge extension code -- its BridgeClient and its
// command handler, from the submodule -- in Node, against a live engine
// BridgeServer. Driven by fidelity_gateway/tests/test_bridge_extension.py.
//
// Only the browser is faked: one Fidelity tab, and an executeScript that
// answers like Fidelity would, echoing what it was sent. Everything the
// extension decides -- the handshake, the address policy, the endpoint
// and header gates, the sealing -- is the extension's own code.
//
//   node bridge_extension_harness.mjs <extension root> <host> <port>
//   env FIDELITY_BRIDGE_API_KEY   the key (never on the command line)
//   env BRIDGE_TEST_SETTINGS      JSON overrides for the extension settings
//
// Prints one JSON line per status change: {"status": {"state", "detail"}}.

import { join } from "node:path";
import { pathToFileURL } from "node:url";

const [, , extensionRoot, host, port] = process.argv;
const lib = (name) => import(pathToFileURL(join(extensionRoot, "src", "lib", name)).href);

const { BridgeClient } = await lib("bridge-client.js");
const { createCommandHandler } = await lib("commands.js");
const { permissionsFrom } = await lib("endpoints.js");

const overrides = JSON.parse(process.env.BRIDGE_TEST_SETTINGS || "{}");
const settings = {
  schemaVersion: 1,
  apiKey: process.env.FIDELITY_BRIDGE_API_KEY,
  engineHost: host,
  enginePort: Number(port),
  allowedAddresses: [host],
  blockedAddresses: [],
  allowPreview: false,
  allowPlace: false,
  ...overrides,
};

const tab = { id: 1, url: "https://digital.fidelity.com/ftgw/digital/traderplus", active: true };

const handleCommand = createCommandHandler({
  tabs: {
    query: async () => [tab],
    update: async (id, props) => {
      tab.url = props.url;
      return tab;
    },
  },
  scripting: {
    // Fidelity, as far as the test can tell: echo the request back.
    executeScript: async ({ args: [path, body, headers] }) => [
      {
        result: {
          status: 200,
          url: `https://digital.fidelity.com${path}`,
          body: JSON.stringify({ path, body, headers }),
        },
      },
    ],
  },
  getSettings: () => settings,
  // Resolves a tick later, as a real load does: after the navigation
  // the command handler starts once it is listening.
  waitForTabComplete: (id) => new Promise((resolve) => setTimeout(() => resolve({ id, url: tab.url }), 0)),
  version: "interop",
});

const client = new BridgeClient({
  settings,
  WebSocketImpl: WebSocket,
  handleCommand,
  clientInfo: { version: "interop" },
  onStatus: (status) => console.log(JSON.stringify({ status })),
  onReady: () => {
    // What the extension announces on connecting (background-core.js
    // does the same), then what a real page would have shown it by now.
    client.sendEvent("permissions", permissionsFrom(settings));
    client.sendEvent("tab", { url: tab.url });
    client.sendEvent("request", {
      url: "https://digital.fidelity.com/ftgw/digital/trade-equity/getquote",
      headers: { "x-csrf-token": "T-from-the-extension", appid: "AP145890", appname: "Trader Dashboard" },
    });
    client.sendEvent("request", {
      url: "https://digital.fidelity.com/ftgw/digital/activityapi/api/v1/transactions/pending",
      headers: { appid: "AP182052", appname: "Trader Plus Web" },
    });
  },
});

client.start();
// Never outlive the test that started it.
setTimeout(() => {
  client.stop();
  process.exit(0);
}, 60_000);
