"""MT2009_PLUS_DBDATA_AUTO_V1: the client's dbdata pack for MT2009-Patcher,
without the panel login.

Until now an operator downloaded "Pobierz aktualne pliki klienta (zip)" and
every player unpacked it by hand (dbeditor/clientdata.py). Now the panel
also publishes the same pack under a public path the patcher asks at every
start (client-patches/patcher, N2_Patcher/Core/DbDataSync.cs):

  GET /klient/dbdata/manifest.json
      {"format": "MT2009_PLUS_DBDATA_AUTO_V1",
       "client_version_base": "2.0.57",           the client base (m2clientpack/base/<v>)
       "stamp": "2.0.57" | "2.0.57-<12 hex>",     what the game sends as "DbDataStamp"
       "edited": false | true,                    the editor changes something the client shows
       "files": [{"name": "pack/dbdata.index", "size": .., "sha256": "<HEX>", "url": "<stamp>/dbdata.index"},
                 {"name": "pack/dbdata.data",  ...}],
       "base": {"index_sha256": .., "data_sha256": ..},   the release's own pack of that base
                                                  (a newer client still carrying it may take the server's pack)
       "stamp_file": "<dbdata_stamp.txt, CRLF>"}  written by the patcher next to metin2client.exe
  GET /klient/dbdata/<stamp>/dbdata.index | dbdata.data
      the pack files of that stamp (404 for any other stamp/name).

The URLs are relative to the manifest, so the same paths work behind a
gate that forwards only /klient/dbdata/ (the supporters' server: README).

Nothing here is secret: the pack is what the zip hands to every player
anyway (item/skill names, bonuses, descriptions of the client), and the
stamp is what the game sends to every client at login. No settings, no
panel name, no history, no address. Only GET; a name is never a path.

The pack is the one of the stamp the game reports (<spool>/dbdata_stamp.txt,
kept current by clientdata.py). Untouched by the editor ("base"): the
release's pack straight from m2clientpack/base/<v>/ - a player whose pack
already is that one downloads nothing (the patcher compares SHA-256).
Edited: built once per stamp (dbsource.build_dbdata, a second or two) and
kept in <spool>/dbeditor/autodbdata/<stamp>/ for both gunicorn workers;
one build at a time (flock), the last KEEP builds stay. A build that
comes out with another stamp (the database changed since the spool's
stamp was made) is the truth: its stamp is written to the spool for the
game cores too.

Requests are counted per address (RATE_* per minute and worker): a
manifest is a few hundred bytes, a pack a few MB at most.

DBDATA_AUTO=0 in the panel's environment switches the public paths off.
"""
import fcntl
import json
import os
import re
import shutil
import threading
import time
from pathlib import Path

from flask import Response, abort, jsonify, request, send_file

FORMAT = "MT2009_PLUS_DBDATA_AUTO_V1"
PREFIX = "/klient/dbdata"
FILE_NAMES = ("dbdata.index", "dbdata.data")
STAMP_RE = re.compile(r"^[0-9A-Za-z._-]{1,64}$")
CACHE_DIR = "autodbdata"
KEEP = 3
# the same spool stamp is built again at most this often per worker when its
# build came out with another stamp and the spool did not follow (not writable)
BUILD_RETRY_SECONDS = 30
RATE_MANIFEST = 60
RATE_FILES = 30
RATE_WINDOW = 60.0


def enabled():
    return os.environ.get("DBDATA_AUTO", "1").strip().lower() not in ("0", "false", "no", "off", "nie")


class RateLimit(object):
    """At most `limit` hits per `window` seconds per key (an address)."""

    def __init__(self, limit, window=RATE_WINDOW):
        self.limit, self.window = limit, window
        self.hits = {}
        self.lock = threading.Lock()

    def allow(self, key, now=None):
        now = time.time() if now is None else now
        with self.lock:
            if len(self.hits) > 5000:  # forget the idle ones
                for k in [k for k, v in self.hits.items() if not v or v[-1] < now - self.window]:
                    del self.hits[k]
            times = [t for t in self.hits.get(key, []) if t > now - self.window]
            if len(times) >= self.limit:
                self.hits[key] = times
                return False
            times.append(now)
            self.hits[key] = times
            return True


def _sha_file(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


class Publisher(object):
    """The current pack: {stamp, base, edited, files: {name: (path, size, sha256)}}.

    current_stamp() -> the spool's stamp (or None); refresh() -> a fresh one
    (written to the spool); build() -> (base, index, data, changed, summary);
    save_stamp(value) -> the spool's copy for the game cores."""

    def __init__(self, cache_root, current_stamp, refresh, build, save_stamp, latest_base):
        self.root = Path(cache_root)
        self.current_stamp = current_stamp
        self.refresh = refresh
        self.build = build
        self.save_stamp = save_stamp
        self.latest_base = latest_base
        # {spool stamp: (time, stamp built for it)} when the two differed and the
        # spool could not be brought along (BUILD_RETRY_SECONDS)
        self.unmatched = {}
        self.lock = threading.Lock()

    # -- the cache ---------------------------------------------------------
    def _cached(self, stamp):
        folder = self.root / stamp
        meta_path = folder / "meta.json"
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        files = {}
        for name in FILE_NAMES:
            entry = (meta.get("files") or {}).get(name) or {}
            path = folder / name
            try:
                if path.stat().st_size != int(entry.get("size", -1)):
                    return None
            except (OSError, TypeError, ValueError):
                return None
            files[name] = (path, int(entry["size"]), str(entry.get("sha256", "")).upper())
        return {"stamp": stamp, "base": meta.get("base"), "edited": True, "files": files,
                "built": meta.get("built")}

    def _store(self, stamp, base_version, index, data):
        import hashlib
        self.root.mkdir(parents=True, exist_ok=True)
        tmp = self.root / (".%s.%d.tmp" % (stamp, os.getpid()))
        shutil.rmtree(tmp, ignore_errors=True)
        tmp.mkdir()
        meta = {"format": FORMAT, "stamp": stamp, "base": base_version, "built": int(time.time()), "files": {}}
        for name, blob in zip(FILE_NAMES, (index, data)):
            (tmp / name).write_bytes(blob)
            meta["files"][name] = {"size": len(blob), "sha256": hashlib.sha256(blob).hexdigest().upper()}
        (tmp / "meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
        final = self.root / stamp
        if final.exists():  # the other worker was quicker: the same stamp, the same contents
            shutil.rmtree(tmp, ignore_errors=True)
        else:
            os.rename(tmp, final)
        self._prune(stamp)

    def _prune(self, keep_stamp):
        try:
            folders = [p for p in self.root.iterdir() if p.is_dir() and not p.name.startswith(".")]
        except OSError:
            return
        folders.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        kept = 0
        for p in folders:
            if p.name == keep_stamp or kept < KEEP - 1:
                kept += p.name != keep_stamp
                continue
            shutil.rmtree(p, ignore_errors=True)

    def _base_entry(self, base):
        pack = base.meta.get("pack") or {}
        files = {}
        for name, ext in zip(FILE_NAMES, ("index", "data")):
            path = Path(base.path) / name
            files[name] = (path, int(pack.get(ext + "Size") or path.stat().st_size),
                           str(pack.get(ext + "Sha256") or _sha_file(path)).upper())
        return {"stamp": base.version, "base": base.version, "edited": False, "files": files, "built": None}

    # -- the current pack --------------------------------------------------
    def current(self):
        entry = self._current()
        try:
            pack = self.latest_base().meta.get("pack") or {}
            if entry.get("base") == self.latest_base().version:
                entry["base_pack"] = {"index_sha256": str(pack.get("indexSha256", "")).upper(),
                                      "data_sha256": str(pack.get("dataSha256", "")).upper()}
        except Exception:
            pass
        return entry

    def _current(self):
        base = self.latest_base()
        stamp = self.current_stamp()
        if not stamp or not STAMP_RE.match(stamp) or stamp.split("-", 1)[0] != base.version:
            stamp = self.refresh() or None  # missing, or made for another client base
        if not stamp or not STAMP_RE.match(stamp):
            raise RuntimeError("no dbdata stamp")
        if stamp == base.version:
            return self._base_entry(base)
        hit = self._cached(stamp)
        if hit:
            return hit
        with self.lock:
            hit = self._cached(stamp)
            if hit:
                return hit
            seen = self.unmatched.get(stamp)
            if seen and time.time() - seen[0] < BUILD_RETRY_SECONDS:
                hit = self._cached(seen[1])
                if hit:
                    return hit
            self.root.mkdir(parents=True, exist_ok=True)
            with open(self.root / ".build.lock", "a+") as lock:
                fcntl.flock(lock, fcntl.LOCK_EX)
                try:
                    hit = self._cached(stamp)
                    if hit:
                        return hit
                    built_base, index, data, changed, summary = self.build()
                    built = summary.get("stamp") or stamp
                    if not changed or built == built_base.version:
                        self.save_stamp(built_base.version)
                        return self._base_entry(built_base)
                    if not self._cached(built):
                        self._store(built, built_base.version, index, data)
                    if built != stamp:
                        self.save_stamp(built)
                        self.unmatched = {stamp: (time.time(), built)}
                finally:
                    fcntl.flock(lock, fcntl.LOCK_UN)
            hit = self._cached(built)
            if not hit:
                raise RuntimeError("dbdata build not stored")
            return hit

    def file_path(self, stamp, name):
        """The path of a pack file of `stamp` (None: no such file here)."""
        if name not in FILE_NAMES or not STAMP_RE.match(stamp or ""):
            return None
        try:
            base = self.latest_base()
        except Exception:
            return None
        if stamp == base.version:
            path = Path(base.path) / name
            return path if path.is_file() else None
        hit = self._cached(stamp)
        return hit["files"][name][0] if hit else None


def manifest(entry, stamp_text):
    """The manifest's JSON object of a Publisher.current() entry."""
    files = []
    sizes = {}
    for name in FILE_NAMES:
        _path, size, sha = entry["files"][name]
        sizes[name] = size
        files.append({"name": "pack/" + name, "size": size, "sha256": sha,
                      "url": "%s/%s" % (entry["stamp"], name)})
    return {"format": FORMAT, "client_version_base": entry["base"], "stamp": entry["stamp"],
            "edited": bool(entry["edited"]), "built": entry.get("built"), "files": files,
            # the release's own pack of that client base: a client newer than the
            # base whose pack still is this one may take the server's pack
            "base": entry.get("base_pack") or {},
            "stamp_file": stamp_text(entry["stamp"], sizes["dbdata.index"], sizes["dbdata.data"])}


def install(app, publisher, stamp_text):
    """The public routes on the app itself (no /db prefix, no login)."""
    manifest_limit = RateLimit(RATE_MANIFEST)
    file_limit = RateLimit(RATE_FILES)

    def client_key():
        # behind a gate (nginx in front of the panel: the supporters' server)
        # every request comes from the gate's own private address - then the
        # address it forwards counts. Only for limiting: nothing else trusts it.
        remote = request.remote_addr or "?"
        try:
            import ipaddress
            local = ipaddress.ip_address(remote)
            behind = local.is_private or local.is_loopback
        except ValueError:
            behind = False
        if behind:
            forwarded = (request.headers.get("X-Real-IP") or
                         (request.headers.get("X-Forwarded-For") or "").split(",")[-1]).strip()
            if forwarded:
                return forwarded[:64]
        return remote

    def manifest_view():
        if not enabled():
            abort(404)
        if not manifest_limit.allow(client_key()):
            return Response("Za dużo zapytań - spróbuj za minutę.\n", status=429, mimetype="text/plain",
                            headers={"Retry-After": "60"})
        try:
            entry = publisher.current()
        except Exception:
            # no detail out: the panel's log has it
            app.logger.exception("dbdata manifest")
            return Response('{"error": "unavailable"}\n', status=503, mimetype="application/json",
                            headers={"Cache-Control": "no-store", "Retry-After": "60"})
        response = jsonify(manifest(entry, stamp_text))
        response.headers["Cache-Control"] = "no-store"
        return response

    def file_view(stamp, name):
        if not enabled():
            abort(404)
        if not file_limit.allow(client_key()):
            return Response("Za dużo zapytań - spróbuj za minutę.\n", status=429, mimetype="text/plain",
                            headers={"Retry-After": "60"})
        path = publisher.file_path(stamp, name)
        if path is None:
            abort(404)
        response = send_file(str(path), mimetype="application/octet-stream", as_attachment=False,
                             conditional=True, max_age=0)
        response.headers["Cache-Control"] = "no-cache"
        return response

    app.add_url_rule(PREFIX + "/manifest.json", "dbdata_auto_manifest", manifest_view, methods=["GET"])
    app.add_url_rule(PREFIX + "/<stamp>/<name>", "dbdata_auto_file", file_view, methods=["GET"])
