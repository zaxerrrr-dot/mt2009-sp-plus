'use strict';

class ConfigError extends Error {
  constructor(message) {
    super(message);
    this.name = 'ConfigError';
  }
}

const DEFAULTS = {
  listenHost: '127.0.0.1',
  listenPort: 9000,
  defaultTarget: null,
  maxConnections: 200,
  // Sessions one player address may hold at once; 0 = no limit. Off by
  // default: behind a proxy that does not pass the player's address (e.g.
  // Cloudflare without real_ip in nginx) every player looks the same.
  maxConnectionsPerAddress: 0,
  // Take the player's address from X-Forwarded-For - only ever from a peer on
  // this machine (nginx), never from anyone else.
  trustProxy: true,
  // 0 = never close a quiet session: a player standing still (AFK) sends
  // nothing and must not be thrown out. Dead peers are found by the
  // heartbeat instead.
  idleTimeoutMs: 0,
  // Every heartbeatMs the bridge pings each browser; a browser that has not
  // answered the previous ping is gone and its session is closed. The pings
  // are also traffic, so proxies that drop quiet WebSockets (Cloudflare
  // after ~100 s) keep the connection. 0 = off.
  heartbeatMs: 30000,
  tcpConnectTimeoutMs: 5000,
  highWaterMarkBytes: 1024 * 1024,
  allowedOrigins: null,
  // Started by index.js (the service), an empty allowedOrigins is refused
  // unless this is true - any web page could otherwise use the bridge.
  allowAnyOrigin: false,
  // Also accept a page whose Origin names exactly the host[:port] the request
  // was sent to (the Host header nginx passes on as $http_host): the page and
  // the bridge share one origin, whatever name or address the player used.
  // A page on any other site still has its own Origin and is refused.
  allowSameHostOrigin: false,
  // Largest WebSocket message from a browser. The game client sends packets
  // of at most a few kB; 8 MB (the ws default here before) let one peer park
  // megabytes in memory per message.
  maxPayloadBytes: 256 * 1024,
  // New sessions one player address may open per minute; 0 = no limit.
  // A reload opens 2-3 (server status probes + auth + game).
  maxNewPerMinutePerAddress: 0,
};

/// A TCP port a target may use: an integer 1..65535.
function isPort(value) {
  return Number.isInteger(value) && value > 0 && value <= 65535;
}

// listenPort additionally allows 0, which asks the OS to assign an
// ephemeral port (standard net.Server behavior, used by tests).
/// A port to listen on: 0..65535 (0 = any free port, used by the tests).
function isListenPort(value) {
  return Number.isInteger(value) && value >= 0 && value <= 65535;
}

/// The configuration with defaults filled in; throws ConfigError on a missing target, a bad port or a bad origin list.
function loadConfig(raw) {
  if (raw === null || typeof raw !== 'object') {
    throw new ConfigError('config must be an object');
  }

  const cfg = { ...DEFAULTS, ...raw };
  const targets = cfg.targets ?? {};
  const names = Object.keys(targets);

  if (names.length === 0) {
    throw new ConfigError('config.targets must declare at least one target');
  }

  for (const name of names) {
    const target = targets[name];
    if (target === null || typeof target !== 'object') {
      throw new ConfigError(`target "${name}" must be an object`);
    }
    if (typeof target.host !== 'string' || target.host.length === 0) {
      throw new ConfigError(`target "${name}" is missing a host`);
    }
    if (!isPort(target.port)) {
      throw new ConfigError(`target "${name}" has an invalid port: ${target.port}`);
    }
    if (target.matchPort !== undefined && !isPort(target.matchPort)) {
      throw new ConfigError(`target "${name}" has an invalid matchPort: ${target.matchPort}`);
    }
  }

  if (!Number.isInteger(cfg.maxConnectionsPerAddress) || cfg.maxConnectionsPerAddress < 0) {
    throw new ConfigError(`invalid maxConnectionsPerAddress: ${cfg.maxConnectionsPerAddress}`);
  }

  for (const key of ['maxPayloadBytes', 'maxNewPerMinutePerAddress']) {
    if (!Number.isInteger(cfg[key]) || cfg[key] < 0) {
      throw new ConfigError(`invalid ${key}: ${cfg[key]}`);
    }
  }

  if (!isListenPort(cfg.listenPort)) {
    throw new ConfigError(`invalid listenPort: ${cfg.listenPort}`);
  }
  if (cfg.defaultTarget !== null && !names.includes(cfg.defaultTarget)) {
    throw new ConfigError(`defaultTarget "${cfg.defaultTarget}" is not a declared target`);
  }

  if (cfg.allowedOrigins !== null && cfg.allowedOrigins !== undefined) {
    if (
      !Array.isArray(cfg.allowedOrigins) ||
      cfg.allowedOrigins.some((origin) => typeof origin !== 'string' || origin.length === 0)
    ) {
      throw new ConfigError('allowedOrigins must be null or an array of non-empty strings');
    }
  }

  return cfg;
}

module.exports = { loadConfig, ConfigError, DEFAULTS };
