'use strict';
// MT2009_PLUS_WEBCLIENT_SERVICE_V1: the bridge's configuration, written at every
// start from the environment the game itself runs with - nothing to edit by hand.
//
//   * the page's server list (serverInfo.py of the web client) names 127.0.0.1:11000
//     for the login and 13000 + 10 * (channel - 1) for the channels - always; the
//     bridge maps those names onto THIS stack's game container (auth 11000, the
//     channels from M2_GAME_PORT_BASE), so one site serves every installation;
//   * after the character select the game hands the client over to a core by the
//     address it announces (M2_PUBLIC_ADDRESS, or 127.0.0.1/localhost on a local
//     install) and the core's own port: every port of M2_GAME_CONTAINER_PORT_RANGE
//     is reachable under those names;
//   * nothing else: the bridge is never an open relay;
//   * allowed pages: the stack's own (http(s)://<public address>:<M2_WEBCLIENT_PORT>,
//     127.0.0.1 / localhost on that port), M2_WEBCLIENT_PUBLIC_URL, M2_WEBCLIENT_ORIGINS,
//     and any page served by this very address (allowSameHostOrigin: the Origin must
//     name exactly the host:port the WebSocket was sent to - a domain the owner points
//     at the server works without a setting, a page of another site never does).
const env = process.env;
const HOST_RE = /^[A-Za-z0-9.-]{1,253}$/;

function fail(message) {
  process.stderr.write(`webclient: ${message}\n`);
  process.exit(2);
}

function port(value, name) {
  const n = Number(value);
  if (!Number.isInteger(n) || n < 1 || n > 65535) fail(`${name} is not a port: ${JSON.stringify(value)}`);
  return n;
}

function range(value, name) {
  const m = /^\s*(\d{1,5})\s*(?:-\s*(\d{1,5}))?\s*$/.exec(String(value || ''));
  if (!m) fail(`${name} is not a port range: ${JSON.stringify(value)}`);
  const lo = port(m[1], name);
  const hi = port(m[2] || m[1], name);
  if (hi < lo || hi - lo > 200) fail(`${name}: bad range ${lo}-${hi}`);
  return [lo, hi];
}

/// scheme://host[:port] of a URL, or null.
function originOf(text) {
  try {
    const u = new URL(String(text).trim());
    if ((u.protocol !== 'http:' && u.protocol !== 'https:') || !u.hostname || u.username) return null;
    return `${u.protocol}//${u.host}`;
  } catch {
    return null;
  }
}

const gameHost = env.YWC_GAME_HOST || 'game';
const authPort = port(env.YWC_GAME_AUTH_PORT || '11000', 'YWC_GAME_AUTH_PORT');
const [lo, hi] = range(env.M2_GAME_CONTAINER_PORT_RANGE || '13000-13003', 'M2_GAME_CONTAINER_PORT_RANGE');
const base = port(env.M2_GAME_PORT_BASE || String(lo), 'M2_GAME_PORT_BASE');
const publicPort = port(env.M2_WEBCLIENT_PORT || '7792', 'M2_WEBCLIENT_PORT');
const publicAddress = String(env.M2_PUBLIC_ADDRESS || '').trim().toLowerCase();
if (publicAddress && !HOST_RE.test(publicAddress)) fail(`M2_PUBLIC_ADDRESS is not a host name: ${JSON.stringify(publicAddress)}`);

const local = ['127.0.0.1', 'localhost'];
const names = [...new Set([...local, ...(publicAddress ? [publicAddress] : [])])];
const aliasesFor = (host) => names.filter((n) => n !== host.toLowerCase());

// The page's built-in names first, by the port it dials; then every core port.
const targets = {};
targets.auth = { host: gameHost, port: authPort, matchPort: 11000, aliases: aliasesFor(gameHost) };
for (let p = lo; p <= hi; p++) {
  if (p === authPort) continue;
  targets[`game-${p}`] = { host: gameHost, port: p, aliases: aliasesFor(gameHost) };
}
if (base !== 13000) {
  // The page asks for 127.0.0.1:13000+k; this stack's channel k listens on base+k.
  for (let p = base; p <= hi; p++) {
    targets[`page-${13000 + p - base}`] = { host: gameHost, port: p, matchPort: 13000 + p - base, aliases: local.slice() };
  }
}

const origins = new Set();
for (const host of names) {
  origins.add(`http://${host}:${publicPort}`);
  origins.add(`https://${host}:${publicPort}`);
}
for (const item of [env.M2_WEBCLIENT_PUBLIC_URL || '', ...String(env.M2_WEBCLIENT_ORIGINS || '').split(/[\s,]+/)]) {
  if (!item.trim()) continue;
  const o = originOf(item);
  if (!o) fail(`not an origin (http(s)://host[:port]): ${JSON.stringify(item)}`);
  origins.add(o);
}

process.stdout.write(`${JSON.stringify({
  listenHost: '127.0.0.1',
  listenPort: port(env.YWC_BRIDGE_PORT || '11497', 'YWC_BRIDGE_PORT'),
  defaultTarget: null,
  allowedOrigins: [...origins],
  allowSameHostOrigin: true,
  targets,
  maxConnections: 500,
  // Per address: nginx in front limits it (a NAT or Docker Desktop's gateway can
  // put many players behind one address, so the bridge itself does not).
  maxConnectionsPerAddress: 0,
  maxNewPerMinutePerAddress: 0,
  maxPayloadBytes: 262144,
  heartbeatMs: 30000,
  tcpConnectTimeoutMs: 5000,
  trustProxy: true,
}, null, 2)}\n`);
