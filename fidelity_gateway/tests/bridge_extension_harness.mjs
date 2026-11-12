// Runs the REAL Fidelity Bridge extension -- its background (background-core.js),
// and through it the BridgeClient, command handler, order log and toasts, all
// from the submodule -- in Node, against a live engine BridgeServer. Driven
// by fidelity_gateway/tests/test_bridge_extension.py.
//
// Only the browser and Fidelity are faked. The browser is the extension's
// own test fake (tests/helpers/fakes.js) with one Fidelity tab. Fidelity
// echoes every request back, and keeps just enough state to be useful:
// a preview mints a confirmation number, an order placed with one is
// remembered, and the order list shows every remembered order FILLED at
// its limit. Everything the extension decides -- the handshake, the address
// policy, the endpoint and header gates, the sealing, what it reports back
// -- is the extension's own code.
//
//   node bridge_extension_harness.mjs <extension root> <host> <port>
//   env FIDELITY_BRIDGE_API_KEY   the key (never on the command line)
//   env BRIDGE_TEST_SETTINGS      JSON overrides for the extension settings
//   env BRIDGE_TEST_CALLS         JSON list of {method, args}: the algorithm
//                                 editor's calls, made once connected
//
// Prints one JSON line per status change, {"status": {"state", "detail"}};
// one per toast window opened, {"toast": {...}}; one per badge,
// {"badge": {"text", "title"}}; one per call made, {"call": {...}}; and
// one whenever the versions the popup would show change, {"versions": {...}}.

import { join } from "node:path";
import { pathToFileURL } from "node:url";

const [, , extensionRoot, host, port] = process.argv;
const load = (...parts) => import(pathToFileURL(join(extensionRoot, ...parts)).href);

const { createBackground } = await load("src", "lib", "background-core.js");
const { EXTENSION_ID, fakeChrome } = await load("tests", "helpers", "fakes.js");

const settings = {
  schemaVersion: 1,
  apiKey: process.env.FIDELITY_BRIDGE_API_KEY,
  engineHost: host,
  enginePort: Number(port),
  allowedAddresses: [host],
  blockedAddresses: [],
  allowPreview: false,
  allowPlace: false,
  showToasts: false,
  ...JSON.parse(process.env.BRIDGE_TEST_SETTINGS || "{}"),
};

const chrome = fakeChrome({
  stored: { settings },
  tabs: [{ id: 1, url: "https://digital.fidelity.com/ftgw/digital/traderplus", active: true }],
});

// A navigation finishes a tick later, as a real load does.
const update = chrome.tabs.update.bind(chrome.tabs);
chrome.tabs.update = async (id, props) => {
  const tab = await update(id, props);
  setTimeout(() => chrome.tabs.onUpdated.fire(id, { status: "complete", url: tab?.url }, tab), 0);
  return tab;
};

// Fidelity, as far as the test can tell.
const placed = new Map();
let previews = 0;
function optionReply(path, query) {
  if (path.endsWith("/key-statistics/v1")) {
    return {
      underlyingsymbol: query.underlying,
      iv30percentile: 56,
      hv30percentile: 100,
      callVolume: 40000,
      putVolume: 30000,
      avgCallVolume: 150000,
      avgPutVolume: 150000,
      callOpenInterest: 1000000,
      putOpenInterest: 650000,
    };
  }
  if (path.endsWith("/option-expirations/v1")) {
    return {
      expirations: [
        { date: "2099-11-13", optionPeriodicity: "W" },
        { date: "2099-11-20", optionPeriodicity: "M" },
      ],
    };
  }
  const callsAndPuts = [];
  String(query.settlementTypes ?? "")
    .split(",")
    .filter(Boolean)
    .forEach((settlement, n) => {
      for (const [strike, delta] of [[54, 0.75], [56, 0.5], [58, 0.25]]) {
        callsAndPuts.push({
          expirationData: { date: settlement.split("|")[0], daysToExpiration: 1 + 6 * n },
          strike,
          callImpliedVolatility: 0.8,
          putImpliedVolatility: 0.9,
          callDelta: delta,
          putDelta: delta - 1,
          callGamma: 0.04,
          putGamma: 0.04,
          callOpenInterest: 1000,
          putOpenInterest: 400,
          callIntrinsicValue: Math.max(0, 56 - strike),
          putIntrinsicValue: Math.max(0, strike - 56),
        });
      }
    });
  return { underlyingSymbol: query.symbol, callsAndPuts, asked: query };
}

chrome.scripting.executeScript = async ({ func, args }) => {
  // The extension's `get`: market data, by the page's own GET.
  if (func?.name === "fidelityGetInPage") {
    const [getPath, query] = args;
    return [
      {
        result: {
          status: 200,
          url: `https://digital.fidelity.com${getPath}?${new URLSearchParams(query)}`,
          body: JSON.stringify(optionReply(getPath, query)),
        },
      },
    ];
  }
  const [path, body, headers] = args;
  const reply = { path, body, headers };
  if (path.endsWith("/previewSrvc")) {
    previews += 1;
    reply.preview = { orderConfirmDetail: { confNum: `IOP${String(previews).padStart(5, "0")}` } };
  } else if (path.endsWith("/placeOrder") && body?.orderDetails?.confNum) {
    placed.set(String(body.orderDetails.confNum), body.orderDetails);
  } else if (path.endsWith("/transactions/pending")) {
    reply.data = {
      orders: [...placed].map(([confNum, ticket]) => ({
        orderNum: confNum,
        acctNum: ticket.acctNum,
        symbol: ticket.symbol,
        status: `Filled at $${ticket.limitPrice}`,
        cancelableInd: false,
        amountDetail: {
          qty: Number(ticket.qty),
          qtyExec: Number(ticket.qty),
          qtyRemaining: 0,
          avgExecPrice: Number(ticket.limitPrice),
        },
      })),
    };
  }
  return [{ result: { status: 200, url: `https://digital.fidelity.com${path}`, body: JSON.stringify(reply) } }];
};

// Report what the test waits on: every badge and every toast window,
// and -- watched below -- every change of the connection's state.
let background = null;
const setTitle = chrome.action.setTitle.bind(chrome.action);
chrome.action.setTitle = async (details) => {
  console.log(JSON.stringify({ badge: { text: chrome.action.badge.text, title: details.title } }));
  return setTitle(details);
};
const createWindow = chrome.windows.create.bind(chrome.windows);
chrome.windows.create = async (props) => {
  console.log(JSON.stringify({ toast: props }));
  return createWindow(props);
};

background = createBackground({ chrome, WebSocketImpl: WebSocket, version: "interop" });

// The algorithm editor's calls, as its page makes them: a message from
// one of the extension's own pages, answered by the background.
const page = { id: EXTENSION_ID, url: `chrome-extension://${EXTENSION_ID}/src/ui/algorithm.html` };
const ask = (message) =>
  new Promise((resolve) => {
    const [keepOpen] = chrome.runtime.onMessage.fire(message, page, resolve);
    if (!keepOpen) resolve(undefined);
  });
const calls = JSON.parse(process.env.BRIDGE_TEST_CALLS || "[]");
let lastStatus = "";
let lastVersions = "";
const watcher = setInterval(async () => {
  const versions = JSON.stringify({ versions: background.statusSnapshot().versions });
  if (versions !== lastVersions) {
    lastVersions = versions;
    console.log(versions);
  }
  const status = background.client?.status;
  const line = JSON.stringify({ status });
  if (!status || line === lastStatus) return;
  lastStatus = line;
  console.log(line);
  if (status.state === "ready" && calls.length) {
    for (const { method, args } of calls.splice(0)) {
      console.log(JSON.stringify({ call: { method, answer: await ask({ type: "engineCall", method, args }) } }));
    }
  }
}, 10);

// What a real page would have shown the extension by now: its own
// requests, carrying each backend's auth headers. The extension replays
// them to the engine once it connects.
chrome.webRequest.onSendHeaders.fire({
  url: "https://digital.fidelity.com/ftgw/digital/trade-equity/getquote",
  requestHeaders: [
    { name: "x-csrf-token", value: "T-from-the-extension" },
    { name: "appid", value: "AP145890" },
    { name: "appname", value: "Trader Dashboard" },
  ],
});
chrome.webRequest.onSendHeaders.fire({
  url: "https://digital.fidelity.com/ftgw/digital/activityapi/api/v1/transactions/pending",
  requestHeaders: [
    { name: "appid", value: "AP182052" },
    { name: "appname", value: "Trader Plus Web" },
  ],
});

// Never outlive the test that started it.
setTimeout(() => {
  clearInterval(watcher);
  background.client?.stop();
  process.exit(0);
}, 60_000);
