'use strict';
// MT2009_PLUS_WEBCLIENT_SERVICE_V1: brings the web client's site in the volume (/site)
// to the release this image is pinned to (site-release.json, from the repository -
// every server update brings the pin of its client patch).
//
//   1. the index (rel/<build>/index.sha256) from the first source that has it; its
//      SHA-256 has to be the pin's, so the update server cannot change what is
//      installed, only deliver it;
//   2. every file of the index that the volume lacks (or holds with other bytes) is
//      downloaded to a .tmp, checked against its SHA-256 and renamed into place:
//      corpus chunks first (content-addressed, shared by all releases - a client
//      patch brings only the new ones), the engine next, the page last, so a player
//      who is in the game during an update keeps a consistent site;
//   3. chunks neither this release nor the previous one uses are removed.
//
// Sources: M2_WEBCLIENT_SOURCE (space/comma separated base URLs) after the local
// directory /websrc when it holds the release (M2_WEBCLIENT_SOURCE_DIR - an offline
// copy, or the publishing machine itself). Exit 0 = the site is the pinned release.
const fs = require('node:fs');
const fsp = require('node:fs/promises');
const path = require('node:path');
const crypto = require('node:crypto');
const { pipeline } = require('node:stream/promises');
const { Readable } = require('node:stream');

const SITE = process.env.YWC_SITE || '/site';
const PIN = process.env.YWC_PIN || path.join(__dirname, "..", "site-release.json");
const LOCAL = process.env.YWC_LOCAL_SOURCE || '/websrc';
const STATE = path.join(SITE, '.ywc');
const PARALLEL = 6;
const log = (msg) => process.stdout.write(`webclient: ${msg}\n`);

function sha256File(file) {
  return new Promise((resolve, reject) => {
    const h = crypto.createHash('sha256');
    fs.createReadStream(file).on('error', reject).on('data', (d) => h.update(d)).on('end', () => resolve(h.digest('hex')));
  });
}

function sources(build) {
  const list = [];
  if (fs.existsSync(path.join(LOCAL, 'rel', build, 'index.sha256'))) list.push(LOCAL);
  for (const s of String(process.env.M2_WEBCLIENT_SOURCE || '').split(/[\s,]+/)) {
    if (/^https?:\/\/[^\s]+$/.test(s)) list.push(s.endsWith('/') ? s : `${s}/`);
  }
  return list;
}

/// Writes source/rel into `dest` (a .tmp path); throws on a network or HTTP error.
async function fetchTo(source, rel, dest) {
  if (!/^https?:/.test(source)) {
    await fsp.copyFile(path.join(source, rel), dest);
    return;
  }
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 15 * 60 * 1000);
  try {
    const res = await fetch(source + rel.split('/').map(encodeURIComponent).join('/'), { signal: ctrl.signal, redirect: 'follow' });
    if (!res.ok) throw new Error(`HTTP ${res.status} for ${rel}`);
    await pipeline(Readable.fromWeb(res.body), fs.createWriteStream(dest));
  } finally {
    clearTimeout(timer);
  }
}

/// One file into place: downloaded, checked, renamed. Tries every source.
async function getFile(srcs, from, to, sha, size) {
  const tmp = `${to}.tmp`;
  await fsp.mkdir(path.dirname(to), { recursive: true });
  const errors = [];
  for (const s of srcs) {
    try {
      await fetchTo(s, from, tmp);
      const st = await fsp.stat(tmp);
      if (size !== null && st.size !== size) throw new Error(`${from}: ${st.size} bytes, the index says ${size}`);
      if ((await sha256File(tmp)) !== sha) throw new Error(`${from}: SHA-256 differs from the index`);
      await fsp.rename(tmp, to);
      return;
    } catch (err) {
      errors.push(`${s}: ${err.message}`);
      await fsp.rm(tmp, { force: true });
    }
  }
  throw new Error(`${from} - ${errors.join('; ') || 'no source'}`);
}

function readJson(file) {
  try { return JSON.parse(fs.readFileSync(file, 'utf8')); } catch { return null; }
}

function parseIndex(text) {
  const out = [];
  for (const line of text.split('\n')) {
    if (!line.trim()) continue;
    const m = /^([0-9a-f]{64}) (\d+) ((?:corpus\/)?[A-Za-z0-9._-]+)$/.exec(line);
    if (!m || m[3].includes('..') || m[3].startsWith('.')) throw new Error(`bad index line: ${line.slice(0, 120)}`);
    out.push({ sha: m[1], size: Number(m[2]), rel: m[3] });
  }
  return out;
}

const isChunk = (rel) => /^corpus\/[0-9a-f]{32}\.bin(\.gz)?$/.test(rel);
const isPage = (rel) => /^client\.html(\.gz)?$/.test(rel);

async function main() {
  const pin = readJson(PIN);
  if (!pin || !/^\d+$/.test(String(pin.build)) || !/^[0-9a-f]{64}$/.test(String(pin.index_sha256))) {
    throw new Error(`no valid pin in ${PIN}`);
  }
  const build = String(pin.build);
  await fsp.mkdir(STATE, { recursive: true });
  const installed = readJson(path.join(STATE, 'installed.json'));
  if (installed && installed.build === build && installed.index_sha256 === pin.index_sha256
      && fs.existsSync(path.join(STATE, 'index.sha256')) && process.env.YWC_VERIFY !== '1') {
    const entries = parseIndex(fs.readFileSync(path.join(STATE, 'index.sha256'), 'utf8'));
    const missing = entries.filter((e) => { try { return fs.statSync(path.join(SITE, e.rel)).size !== e.size; } catch { return true; } });
    if (!missing.length) {
      log(`site is client ${pin.client} (build ${build}), ${entries.length} files - nothing to do`);
      return;
    }
    log(`${missing.length} files of the installed site are missing or damaged - repairing`);
  }

  const srcs = sources(build);
  if (!srcs.length) throw new Error('no source: set M2_WEBCLIENT_SOURCE (or M2_WEBCLIENT_SOURCE_DIR)');
  const indexRel = String(pin.index || `rel/${build}/index.sha256`);
  const indexTmp = path.join(STATE, 'index.new');
  await getFile(srcs, indexRel, indexTmp, pin.index_sha256, null);
  const entries = parseIndex(await fsp.readFile(indexTmp, 'utf8'));
  log(`client ${pin.client} build ${build}: ${entries.length} files, ${(pin.bytes / 1e9).toFixed(2)} GB, from ${srcs.join(' ')}`);

  // What was verified before (installed or a previous run) is not hashed again.
  const known = new Set();
  for (const f of ['index.sha256', 'partial.sha256']) {
    try { for (const e of parseIndex(fs.readFileSync(path.join(STATE, f), 'utf8'))) known.add(`${e.sha} ${e.size} ${e.rel}`); } catch { /* none */ }
  }
  const todo = [];
  for (const e of entries) {
    let ok = false;
    try { ok = fs.statSync(path.join(SITE, e.rel)).size === e.size && known.has(`${e.sha} ${e.size} ${e.rel}`); } catch { ok = false; }
    if (!ok) todo.push(e);
  }
  const total = todo.reduce((a, e) => a + e.size, 0);
  let doneBytes = 0;
  let doneFiles = 0;
  const partial = fs.createWriteStream(path.join(STATE, 'partial.sha256'), { flags: 'a' });
  const progress = () => fs.writeFileSync(path.join(STATE, 'progress.json'), JSON.stringify({
    client: pin.client, build, files: todo.length, done: doneFiles, bytes: total, done_bytes: doneBytes, at: Date.now(),
  }));
  progress();
  log(`${todo.length} files to fetch (${(total / 1e9).toFixed(2)} GB)`);

  const run = async (group) => {
    let next = 0;
    let lastReport = Date.now();
    const worker = async () => {
      while (next < group.length) {
        const e = group[next++];
        const from = isChunk(e.rel) ? e.rel : `rel/${build}/${e.rel}`;
        await getFile(srcs, from, path.join(SITE, e.rel), e.sha, e.size);
        partial.write(`${e.sha} ${e.size} ${e.rel}\n`);
        doneBytes += e.size;
        doneFiles += 1;
        if (Date.now() - lastReport > 5000) {
          lastReport = Date.now();
          progress();
          log(`${doneFiles}/${todo.length} files, ${(doneBytes / 1e9).toFixed(2)}/${(total / 1e9).toFixed(2)} GB`);
        }
      }
    };
    await Promise.all(Array.from({ length: Math.min(PARALLEL, group.length) }, worker));
  };
  await run(todo.filter((e) => isChunk(e.rel)));
  await run(todo.filter((e) => !isChunk(e.rel) && !isPage(e.rel)));
  await run(todo.filter((e) => isPage(e.rel)));
  await new Promise((r) => partial.end(r));
  progress();

  // Keep the previous release's chunks (players still on the old page), drop older ones
  // and every other file that is in no index.
  const keep = new Set(entries.map((e) => e.rel));
  try { for (const e of parseIndex(fs.readFileSync(path.join(STATE, 'index.sha256'), 'utf8'))) if (isChunk(e.rel)) keep.add(e.rel); } catch { /* first install */ }
  let removed = 0;
  for (const dir of ['', 'corpus']) {
    let names = [];
    try { names = fs.readdirSync(path.join(SITE, dir)); } catch { continue; }
    for (const name of names) {
      const rel = dir ? `${dir}/${name}` : name;
      if (name.startsWith('.') || rel === 'corpus') continue;
      if (!keep.has(rel) && fs.statSync(path.join(SITE, rel)).isFile()) { fs.rmSync(path.join(SITE, rel)); removed += 1; }
    }
  }
  if (fs.existsSync(path.join(STATE, 'index.sha256'))) fs.renameSync(path.join(STATE, 'index.sha256'), path.join(STATE, 'previous.sha256'));
  fs.renameSync(indexTmp, path.join(STATE, 'index.sha256'));
  fs.rmSync(path.join(STATE, 'partial.sha256'), { force: true });
  fs.writeFileSync(path.join(STATE, 'installed.json'), JSON.stringify({ client: pin.client, build, index_sha256: pin.index_sha256, at: new Date().toISOString() }));
  log(`site is client ${pin.client} (build ${build}); fetched ${doneFiles} files, removed ${removed} unused`);
}

main().catch((err) => {
  log(`not updated: ${err.message}`);
  process.exit(1);
});
