'use strict';

const { WebSocketServer } = require('ws');
const { createTargetResolver, UnknownTargetError } = require('./target-resolver.js');
const { createBridge } = require('./bridge.js');
const { CLOSE_CODES } = require('./close-codes.js');

/// The player's address: the socket peer - or, when the peer is this machine
/// (nginx in front) and `trustProxy` is on, the last address in
/// X-Forwarded-For, the one nginx appended. From any other peer the header is
/// ignored: anyone can send it.
function clientAddress(req, config) {
  const peer = (req.socket && req.socket.remoteAddress) || '';
  const loopback = peer === '127.0.0.1' || peer === '::1' || peer === '::ffff:127.0.0.1';
  if (loopback && config.trustProxy) {
    const forwarded = String(req.headers['x-forwarded-for'] || '')
      .split(',').map((s) => s.trim()).filter(Boolean);
    if (forwarded.length) return forwarded[forwarded.length - 1];
  }
  return peer;
}

/// True when `origin` (scheme://host[:port] of the page) names the same
/// host[:port] as the request's Host header - the page was served by the same
/// address the WebSocket goes to. Only http(s) origins; "null" never matches.
function sameHostOrigin(origin, hostHeader) {
  if (typeof origin !== 'string' || typeof hostHeader !== 'string' || !hostHeader) return false;
  try {
    const page = new URL(origin);
    if (page.protocol !== 'http:' && page.protocol !== 'https:') return false;
    if (page.pathname !== '/' || page.search || page.username) return false;
    const asked = new URL(`${page.protocol}//${hostHeader}`);
    return page.host === asked.host && asked.pathname === '/' && !asked.username;
  } catch {
    return false;
  }
}

/// The WebSocket server: checks the Origin, the connection limits (all and per address) and the target (allowlist) of every request, then bridges it; returns { listen, close, activeCount }.
function createProxyServer(config, { logger = () => {} } = {}) {
  const resolver = createTargetResolver(config);
  const sessions = new Set();
  const perAddress = new Map();   // player address -> open sessions
  const recent = new Map();       // player address -> { start, count } (new sessions this minute)

  /// True when `address` may open one more session this minute (and counts it).
  function admitRate(address) {
    const limit = config.maxNewPerMinutePerAddress;
    if (!(limit > 0)) return true;
    const now = Date.now();
    if (recent.size > 50000) {                       // forget finished windows
      for (const [key, w] of recent) if (now - w.start >= 60000) recent.delete(key);
    }
    let w = recent.get(address);
    if (!w || now - w.start >= 60000) {
      w = { start: now, count: 0 };
      recent.set(address, w);
    }
    w.count += 1;
    return w.count <= limit;
  }

  const wss = new WebSocketServer({
    host: config.listenHost,
    port: config.listenPort,
    // The game stream is already encrypted; compressing it wastes CPU
    // and adds latency to every packet.
    perMessageDeflate: false,
    maxPayload: config.maxPayloadBytes,
    // Loopback binding is not an origin boundary: WebSockets are exempt
    // from same-origin policy, so any page the operator's browser visits
    // could otherwise open a connection here. Reject before the connection
    // is ever accepted (and before any target resolution or TCP dial).
    verifyClient(info) {
      const origins = config.allowedOrigins;
      const listed = Array.isArray(origins) && origins.length > 0;
      if (!listed && !config.allowSameHostOrigin) return true;
      if (listed && origins.includes(info.origin)) return true;
      return config.allowSameHostOrigin === true && sameHostOrigin(info.origin, info.req && info.req.headers.host);
    },
  });

  // Permanent handler so a post-listen server-level error is logged instead
  // of crashing the process. Registered before the temporary listen()
  // listener below so the server is never left without error handling.
  wss.on('error', (err) => {
    logger('server_error', { message: err.message });
  });

  wss.on('connection', (ws, req) => {
    const address = clientAddress(req, config);
    if (sessions.size >= config.maxConnections) {
      logger('connection_rejected', { reason: 'limit', active: sessions.size, address });
      ws.close(CLOSE_CODES.CONNECTION_LIMIT, 'too many connections');
      return;
    }
    if (!admitRate(address)) {
      logger('connection_rejected', { reason: 'rate_per_address', address });
      ws.close(CLOSE_CODES.CONNECTION_LIMIT, 'too many new connections from this address');
      return;
    }
    // one address must not take every slot; off when 0
    if (config.maxConnectionsPerAddress > 0 &&
        (perAddress.get(address) || 0) >= config.maxConnectionsPerAddress) {
      logger('connection_rejected', { reason: 'limit_per_address', address });
      ws.close(CLOSE_CODES.CONNECTION_LIMIT, 'too many connections from this address');
      return;
    }

    let target;
    try {
      // `/to/<host>:<port>` (our client) or `?target=<name>` - see target-resolver.js
      target = resolver.resolveRequest(req.url);
    } catch (err) {
      if (err instanceof UnknownTargetError) {
        logger('connection_rejected', { reason: 'unknown_target', requested: err.requested, address });
        ws.close(CLOSE_CODES.UNKNOWN_TARGET, 'unknown target');
        return;
      }
      // An unexpected error here must not crash the whole proxy for what
      // should be a single bad connection — log it and close just this
      // websocket instead of rethrowing inside the EventEmitter callback.
      logger('connection_error', { message: err.message });
      ws.close(1011, 'internal error');
      return;
    }

    const bridge = createBridge({ ws, target, config, logger });
    const session = { ws, bridge };
    sessions.add(session);
    perAddress.set(address, (perAddress.get(address) || 0) + 1);

    let idleTimer;
    /// Restarts the idle timer of a session - any traffic either way keeps it
    /// alive. Only when `idleTimeoutMs` > 0 (off by default).
    const resetIdle = () => {
      if (!(config.idleTimeoutMs > 0)) return;
      clearTimeout(idleTimer);
      idleTimer = setTimeout(() => {
        logger('idle_timeout', { target: target.name });
        bridge.close(CLOSE_CODES.IDLE_TIMEOUT, 'idle timeout');
      }, config.idleTimeoutMs);
    };

    resetIdle();
    ws.on('message', resetIdle);
    bridge.socket.on('data', resetIdle);

    // Heartbeat: a ping every heartbeatMs; no pong since the last one means
    // the browser is gone (closed laptop, lost network) - drop the session.
    let answered = true;
    ws.on('pong', () => { answered = true; });
    const heartbeat = config.heartbeatMs > 0 ? setInterval(() => {
      if (!answered) {
        logger('heartbeat_timeout', { target: target.name });
        ws.terminate();
        return;
      }
      answered = false;
      try { ws.ping(); } catch (e) { /* closing already */ }
    }, config.heartbeatMs) : null;

    ws.on('close', () => {
      clearTimeout(idleTimer);
      clearInterval(heartbeat);
      sessions.delete(session);
      const left = (perAddress.get(address) || 1) - 1;
      if (left > 0) perAddress.set(address, left); else perAddress.delete(address);
      logger('session_closed', { target: target.name, active: sessions.size, address });
    });

    logger('session_opened', { target: target.name, active: sessions.size, address });
  });

  return {
    listen() {
      return new Promise((resolve, reject) => {
        // Temporary listener used only to settle the initial bind. Removed
        // as soon as listen() settles (success or failure) so it doesn't
        // linger and swallow the first real post-listen server error.
        /// Rejects the initial listen() when binding fails.
        const onListenError = (err) => {
          wss.removeListener('listening', onListening);
          reject(err);
        };
        /// Resolves the initial listen() with the bound port.
        const onListening = () => {
          wss.removeListener('error', onListenError);
          resolve({ port: wss.address().port });
        };

        if (wss.address()) {
          resolve({ port: wss.address().port });
          return;
        }
        wss.once('error', onListenError);
        wss.once('listening', onListening);
      });
    },
    close() {
      return new Promise((resolve) => {
        for (const session of sessions) session.bridge.close();
        sessions.clear();
        wss.close(resolve);
      });
    },
    activeCount() {
      return sessions.size;
    },
  };
}

module.exports = { sameHostOrigin, createProxyServer, clientAddress };
