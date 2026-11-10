#!/usr/bin/env python3
"""MT2009 PLUS - Yohara: builds / updates the Yohara update mirror (MT2009_PLUS_YOHARA_MIRROR_V1).

The mirror is served by the mt2009plus-wiki nginx on vps1 (location /aktualizacje/, the folder
/opt/metin2/dist/aktualizacje) at http://141.94.100.53/aktualizacje/yohara/ and is read ONLY by
MT2009-Yohara-Patcher.exe. It has nothing in common with the 2.x mirror (update-manifest-mt2009.json,
client-files.json, /patcher/patchlist.json): other folder, other file names, other format.

Layout (<out> = /opt/metin2/dist/aktualizacje/yohara):
  channels.json                 {"marker", "schema", "default": "test", "channels": {"test": {...}, "stable": {...}}}
  <channel>/manifest.json       version, client version, every client file (path, size, sha256, keep),
                                files to delete, the patcher (version, size, sha256)
  <channel>/manifest-poprzedni.json   the list before the last publish (its files stay in the store)
  files/<aa>/<sha256>           the files, by content (aa = first two hex digits); raw like the 2.x
                                mirror (packs are compressed already); a file is never rewritten
  news.json                     news of the patcher window
  MT2009-Yohara-Patcher.exe(.sha256)  the patcher, for players to download

Sources (--zrodlo, in order, a later one wins for the same path):
  FOLDER[=PREFIX]               a whole client folder (or a folder placed under PREFIX, e.g. pack)
  FILE=PATH                     one file at PATH
  ZIP[=PREFIX]                  a zip (test patch): its single top folder is stripped
--zrodlo-link does the same as --zrodlo for a folder whose files never change in place (e.g. the
assembled native client): the store gets hard links instead of copies (no extra disk space).

Example (test client 3.0.23 = native 3.0.15 + the 3.0.23 build of all Yohara packs + exe 1.3.3):
  python3 tools/make_mirror.py --kanal test --wersja 3.0.23 --wersja-klienta 1.3.3 \\
    --zrodlo-link /opt/metin2/cache/webclient/work/inputs/native-3.0.15 \\
    --zrodlo /opt/metin2/cache/cY/out/pack=pack \\
    --zrodlo /opt/metin2/cache/yohara/exe-out24/metin2client.exe=metin2client.exe \\
    --zrodlo /opt/metin2/dist/aktualizacje/test-plus/klient-test-yohara-3.0.23-latka.zip \\
    --sprawdz /opt/metin2/cache/yohara/base-3023/pack.sha256=pack \\
    --patcher /opt/metin2/dist/aktualizacje/yohara/MT2009-Yohara-Patcher.exe --wersja-patchera 1.0.0
"""
import argparse
import datetime
import re
import fnmatch
import hashlib
import json
import os
import shutil
import sys
import tempfile
import zipfile

MARKER = 'MT2009_PLUS_YOHARA_MIRROR_V1'
SCHEMA = 1
PRODUCT = 'MT2009 PLUS Yohara'
STAMP = 'YOHARA_VERSION'
DEFAULT_OUT = '/opt/metin2/dist/aktualizacje/yohara'
DEFAULT_CACHE = '/opt/metin2/cache/yohara-mirror-hashes.json'

# never published: the player's own files, logs, the patchers and their state, 2.x update lists,
# the test patch instructions
SKIP = [
    '*.cfg', 'channel.inf', 'UserData/*', 'screenshot/*', 'mark/*', 'log/*', 'logs/*', '*.log', '*.log.1',
    'syserr.txt', 'syserr*.txt', '*.bak', '*.tmp', '*.dmp', '*.old', '*.part',
    '.webclient-assembly.json', 'Thumbs.db', 'desktop.ini',
    'MT2009-Patcher.exe', 'MT2009-Patcher.exe.config', 'MT2009-Aktualizator.*', 'update-manifest-mt2009.json',
    'client-files.json', 'MT2009-Yohara-Patcher.exe', 'MT2009-Yohara-Patcher.exe.config',
    'MT2009-Yohara-Patcher.exe.sha256', '.yohara-patcher/*', STAMP,
    'LATKA-*', '*-INSTRUKCJA.txt',
]
# the player's own copy wins (the database editor's files from the server panel)
KEEP = ['pack/dbdata.index', 'pack/dbdata.data']


class Source(argparse.Action):
    """--zrodlo / --zrodlo-link into one list, in command line order."""

    def __call__(self, parser, namespace, values, option_string=None):
        items = list(getattr(namespace, self.dest) or [])
        items.append(('link' if option_string == '--zrodlo-link' else 'copy', values))
        setattr(namespace, self.dest, items)


def log(*a):
    print(*a, flush=True)


def die(msg):
    print('BLAD: ' + msg, file=sys.stderr, flush=True)
    sys.exit(1)


def match(path, patterns):
    low = path.lower()
    base = low.rsplit('/', 1)[-1]
    for p in patterns:
        p = p.lower()
        if fnmatch.fnmatchcase(low, p) or ('/' not in p and fnmatch.fnmatchcase(base, p)):
            return True
    return False


def safe(path):
    if not path or path.startswith('/') or ':' in path or '\\' in path:
        return False
    return all(part not in ('', '.', '..') and not part.endswith(('.', ' ')) for part in path.split('/'))


class HashCache:
    """sha256 of source files by (path, size, mtime_ns, inode) - repeated publishes skip re-reading
    the unchanged 3 GB client."""

    def __init__(self, path):
        self.path = path
        self.data = {}
        self.dirty = False
        if path and os.path.exists(path):
            try:
                with open(path) as f:
                    self.data = json.load(f)
            except Exception:
                self.data = {}

    def sha(self, path):
        st = os.stat(path)
        key = '%s|%d|%d|%d' % (os.path.abspath(path), st.st_size, st.st_mtime_ns, st.st_ino)
        if key in self.data:
            return self.data[key]
        value = sha256_file(path)
        self.data[key] = value
        self.dirty = True
        return value

    def save(self):
        if self.path and self.dirty:
            tmp = self.path + '.tmp'
            with open(tmp, 'w') as f:
                json.dump(self.data, f)
            os.replace(tmp, self.path)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def zip_entries(path, prefix):
    with zipfile.ZipFile(path) as z:
        names = [i for i in z.infolist() if not i.is_dir()]
    tops = {n.filename.split('/', 1)[0] for n in names}
    strip = ''
    if len(tops) == 1 and all('/' in n.filename for n in names):
        strip = tops.pop() + '/'
    out = []
    for info in names:
        rel = info.filename[len(strip):] if info.filename.startswith(strip) else info.filename
        rel = rel.replace('\\', '/')
        out.append(((prefix + '/' + rel) if prefix else rel, info))
    return out


def collect(args):
    """path -> source dict, in source order (a later source wins)."""
    files = {}
    for kind, spec in args.sources:
        link = kind == 'link'
        src, _, target = spec.partition('=')
        src = os.path.abspath(src)
        target = target.strip('/').replace('\\', '/')
        if os.path.isdir(src):
            n = 0
            for dirpath, dirnames, filenames in os.walk(src):
                dirnames.sort()
                for name in sorted(filenames):
                    full = os.path.join(dirpath, name)
                    rel = os.path.relpath(full, src).replace(os.sep, '/')
                    rel = (target + '/' + rel) if target else rel
                    files[rel] = {'type': 'file', 'src': full, 'link': link, 'from': spec}
                    n += 1
            log('  zrodlo %-60s %5d plikow%s' % (src + ('=' + target if target else ''), n, ' (twarde linki)' if link else ''))
        elif os.path.isfile(src) and src.lower().endswith('.zip'):
            entries = zip_entries(src, target)
            for rel, info in entries:
                files[rel] = {'type': 'zip', 'src': src, 'member': info.filename, 'size': info.file_size, 'from': spec}
            log('  zrodlo %-60s %5d plikow (zip)' % (src, len(entries)))
        elif os.path.isfile(src):
            if not target:
                die('plik bez sciezki docelowej: %s (uzyj PLIK=sciezka)' % spec)
            files[target] = {'type': 'file', 'src': src, 'link': link, 'from': spec}
            log('  zrodlo %-60s -> %s' % (src, target))
        else:
            die('nie ma zrodla: ' + src)
    return files


def store_path(out, sha):
    return os.path.join(out, 'files', sha[:2], sha)


def put_store(out, sha, size, writer, stats, dry):
    """writer(tmp_path) creates the file; the store file is only ever added, never rewritten."""
    dst = store_path(out, sha)
    if os.path.exists(dst):
        if os.path.getsize(dst) != size:
            die('plik w magazynie ma zly rozmiar: %s' % dst)
        return
    stats['nowe'] += 1
    stats['nowe_bajty'] += size
    if dry:
        return
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.nowy-', dir=os.path.dirname(dst))
    os.close(fd)
    os.unlink(tmp)
    try:
        writer(tmp)
        if sha256_file(tmp) != sha:
            die('suma pliku w magazynie sie nie zgadza (zrodlo zmienilo sie w trakcie?): ' + sha)
        if os.stat(tmp).st_nlink == 1:
            # a copy of our own: read-only (a hard link keeps its source's mode)
            os.chmod(tmp, 0o444)
        os.replace(tmp, dst)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def write_json(path, data, dry):
    if dry:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write('\n')
    os.chmod(tmp, 0o644)
    os.replace(tmp, path)


def load_json(path):
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--wyjscie', default=DEFAULT_OUT, help='folder mirrora (domyslnie %(default)s)')
    ap.add_argument('--kanal', required=True, help='kanal: test albo stable (male litery, cyfry, - _)')
    ap.add_argument('--wersja', required=True, help='wersja klienta Yohara, np. 3.0.23 (YOHARA_VERSION)')
    ap.add_argument('--wersja-klienta', default='', help='wersja exe (constinfo), np. 1.3.3')
    ap.add_argument('--zrodlo', dest='sources', action=Source, default=[], help='FOLDER[=PREFIKS] | PLIK=SCIEZKA | ZIP[=PREFIKS]')
    ap.add_argument('--zrodlo-link', dest='sources', action=Source, default=[], help='jak --zrodlo, ale twarde linki (folder, ktory sie nie zmienia)')
    ap.add_argument('--sprawdz', action='append', default=[], help='PLIK_SHA256[=PREFIKS]: sumy (sha256sum), ktore musza sie zgadzac')
    ap.add_argument('--patcher', help='MT2009-Yohara-Patcher.exe do samoaktualizacji (i do pobrania dla graczy)')
    ap.add_argument('--wersja-patchera', default='1.0.0')
    ap.add_argument('--usun', action='append', default=[], help='plik do usuniecia u graczy (sciezka w kliencie)')
    ap.add_argument('--zachowaj', action='append', default=[], help='wzorzec "keep" (domyslnie pack/dbdata.*)')
    ap.add_argument('--bez-zachowania', action='store_true', help='bez domyslnych "keep"')
    ap.add_argument('--pomin', action='append', default=[], help='dodatkowy wzorzec plikow, ktorych nie publikowac')
    ap.add_argument('--domyslny', action='store_true', help='ustaw ten kanal jako domyslny (patcher bez ustawionego kanalu)')
    ap.add_argument('--aktualnosci', help='news.json (lista NewsItem) zamiast wygenerowanego')
    ap.add_argument('--bez-sprzatania', action='store_true', help='nie usuwaj z magazynu plikow, ktorych nie ma na zadnej liscie')
    ap.add_argument('--cache', default=DEFAULT_CACHE, help='pamiec sum plikow zrodlowych (domyslnie %(default)s)')
    ap.add_argument('--proba', action='store_true', help='tylko pokaz, co by sie stalo')
    a = ap.parse_args()

    if not re.match(r'^[a-z0-9][a-z0-9_-]{0,31}$', a.kanal):
        die('zla nazwa kanalu: ' + a.kanal)
    if not re.match(r'^[0-9A-Za-z.+_-]{1,40}$', a.wersja):
        die('zla wersja: ' + a.wersja)
    if not a.sources:
        die('brak --zrodlo')
    out = os.path.abspath(a.wyjscie)
    skip = SKIP + a.pomin
    keep = ([] if a.bez_zachowania else KEEP) + a.zachowaj

    log('Mirror Yohary: %s, kanal %s, wersja %s%s' % (out, a.kanal, a.wersja, ' (PROBA)' if a.proba else ''))
    files = collect(a)
    cache = HashCache(a.cache)

    # final list
    entries = {}
    skipped = []
    for rel in sorted(files, key=str.lower):
        src = files[rel]
        if match(rel, skip):
            skipped.append(rel)
            continue
        if not safe(rel):
            die('niebezpieczna sciezka: ' + rel)
        entries[rel] = src
    lower = {}
    for rel in entries:
        if rel.lower() in lower:
            die('ta sama sciezka dwa razy (wielkosc liter): %s / %s' % (lower[rel.lower()], rel))
        lower[rel.lower()] = rel
    if not any(p in lower for p in ('pack/hydra_map.index', 'pack/balathor_map.index', 'pack/seoganland_map.index')):
        die('to nie wyglada na klienta Yohara (brak paczek hydra_map / balathor_map / seoganland_map)')
    if 'metin2client.exe' not in lower:
        die('brak metin2client.exe')
    log('  plikow klienta: %d, pominietych: %d (%s)' % (len(entries), len(skipped), ', '.join(skipped[:12]) + (' ...' if len(skipped) > 12 else '')))

    # hashes + store
    stats = {'nowe': 0, 'nowe_bajty': 0, 'linki': 0}
    listed = []
    zips = {}
    total = 0
    for rel, src in entries.items():
        if src['type'] == 'file':
            sha = cache.sha(src['src'])
            size = os.path.getsize(src['src'])
            path = src['src']
            if src['link']:
                def writer(tmp, path=path):
                    try:
                        os.link(path, tmp)
                        stats['linki'] += 1
                    except OSError:
                        shutil.copyfile(path, tmp)
            else:
                def writer(tmp, path=path):
                    shutil.copyfile(path, tmp)
        else:
            z = zips.get(src['src']) or zips.setdefault(src['src'], zipfile.ZipFile(src['src']))
            h = hashlib.sha256()
            with z.open(src['member']) as f:
                for block in iter(lambda: f.read(1 << 20), b''):
                    h.update(block)
            sha = h.hexdigest()
            size = src['size']

            def writer(tmp, z=z, member=src['member']):
                with z.open(member) as f, open(tmp, 'wb') as g:
                    shutil.copyfileobj(f, g, 1 << 20)
        put_store(out, sha, size, writer, stats, a.proba)
        listed.append({'path': rel, 'size': size, 'sha256': sha, 'keep': bool(match(rel, keep))})
        total += size
    cache.save()

    # YOHARA_VERSION (the folder marker the patchers look for)
    stamp = (a.wersja + '\r\n').encode('ascii')
    stamp_sha = hashlib.sha256(stamp).hexdigest()

    def stamp_writer(tmp):
        with open(tmp, 'wb') as f:
            f.write(stamp)
    put_store(out, stamp_sha, len(stamp), stamp_writer, stats, a.proba)
    listed.append({'path': STAMP, 'size': len(stamp), 'sha256': stamp_sha, 'keep': False})
    listed.sort(key=lambda e: e['path'].lower())

    # checks against the build's own sums
    final = {e['path']: e['sha256'] for e in listed}
    for spec in a.sprawdz:
        sums, _, prefix = spec.partition('=')
        bad = 0
        n = 0
        with open(sums) as f:
            for line in f:
                parts = line.strip().split(None, 1)
                if len(parts) != 2:
                    continue
                sha, name = parts[0].lower(), parts[1].lstrip('*').strip()
                rel = (prefix.strip('/') + '/' + name) if prefix else name
                n += 1
                if final.get(rel) != sha:
                    bad += 1
                    log('  NIEZGODNE z %s: %s (mirror %s, sumy %s)' % (os.path.basename(sums), rel, (final.get(rel) or 'brak')[:12], sha[:12]))
        if bad:
            die('%d z %d plikow niezgodnych z %s - nic nie opublikowano' % (bad, n, sums))
        log('  sprawdzone z %s: %d plikow zgodnych' % (sums, n))

    delete = []
    for path in a.usun:
        path = path.replace('\\', '/').strip('/')
        if not safe(path) or path.lower() in {e['path'].lower() for e in listed}:
            die('zly plik do usuniecia: ' + path)
        delete.append(path)

    patcher = None
    if a.patcher:
        psha = sha256_file(a.patcher)
        psize = os.path.getsize(a.patcher)
        with open(a.patcher, 'rb') as f:
            if f.read(2) != b'MZ':
                die('--patcher to nie jest plik exe')

        def pwriter(tmp, path=a.patcher):
            shutil.copyfile(path, tmp)
        put_store(out, psha, psize, pwriter, stats, a.proba)
        patcher = {'version': a.wersja_patchera, 'size': psize, 'sha256': psha}
        pub = os.path.join(out, 'MT2009-Yohara-Patcher.exe')
        if not a.proba and not (os.path.exists(pub) and os.path.samefile(pub, a.patcher)):
            shutil.copyfile(a.patcher, pub + '.tmp')
            os.chmod(pub + '.tmp', 0o644)
            os.replace(pub + '.tmp', pub)
        if not a.proba:
            with open(pub + '.sha256.tmp', 'w') as f:
                f.write('%s  MT2009-Yohara-Patcher.exe\n' % psha)
            os.replace(pub + '.sha256.tmp', pub + '.sha256')
    else:
        old = load_json(os.path.join(out, a.kanal, 'manifest.json'))
        if old and old.get('patcher'):
            patcher = old['patcher']
            log('  patcher bez zmian: %s %s' % (patcher.get('version'), patcher.get('sha256', '')[:12]))

    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    manifest = {
        'marker': MARKER,
        'schema': SCHEMA,
        'product': PRODUCT,
        'channel': a.kanal,
        'version': a.wersja,
        'clientVersion': a.wersja_klienta,
        'published': now,
        'totalSize': total + len(stamp),
        'files': listed,
        'delete': delete,
        'patcher': patcher,
    }
    mdir = os.path.join(out, a.kanal)
    mpath = os.path.join(mdir, 'manifest.json')
    old = load_json(mpath)
    if old and not a.proba:
        if [f for f in old.get('files', [])] != listed or old.get('version') != a.wersja or old.get('patcher') != patcher:
            write_json(os.path.join(mdir, 'manifest-poprzedni.json'), old, False)
    if old and old.get('files') == listed and old.get('version') == a.wersja and old.get('patcher') == patcher and old.get('delete', []) == delete:
        manifest['published'] = old.get('published', now)
        log('  lista bez zmian (wersja %s)' % a.wersja)
    write_json(mpath, manifest, a.proba)

    channels = load_json(os.path.join(out, 'channels.json')) or {'marker': MARKER, 'schema': SCHEMA, 'default': a.kanal, 'channels': {}}
    channels['marker'] = MARKER
    channels['schema'] = SCHEMA
    channels.setdefault('channels', {})[a.kanal] = {'manifest': a.kanal + '/manifest.json', 'version': a.wersja, 'published': manifest['published']}
    if a.domyslny or not channels.get('default') or channels['default'] not in channels['channels']:
        channels['default'] = a.kanal
    write_json(os.path.join(out, 'channels.json'), channels, a.proba)

    # news.json (own news of the Yohara patcher; never the 2.x news)
    if a.aktualnosci:
        news = load_json(a.aktualnosci)
        if not isinstance(news, list):
            die('--aktualnosci: to nie jest lista')
    else:
        news = []
        for name in sorted(channels['channels'], key=lambda c: (c != channels['default'], c)):
            info = channels['channels'][name]
            day = (info.get('published') or now)[:10]
            news.append({
                'newsType': 2,
                'topic': 'Klient Yohara %s (%s)' % (info.get('version'), name),
                'creator': '.'.join(reversed(day.split('-'))),
                'threadUrl': '',
                'date': day,
                'message': 'Aktualna wersja klienta Yohara na kanale %s.' % name,
                'avatarLink': '',
            })
    write_json(os.path.join(out, 'news.json'), news, a.proba)

    # clean the store: keep what any channel's current or previous list (or patcher) needs
    removed = 0
    if not a.bez_sprzatania and not a.proba:
        needed = set()
        for name in channels['channels']:
            for fn in ('manifest.json', 'manifest-poprzedni.json'):
                m = load_json(os.path.join(out, name, fn))
                if not m:
                    continue
                needed.update(e['sha256'] for e in m.get('files', []))
                if m.get('patcher'):
                    needed.add(m['patcher']['sha256'])
        root = os.path.join(out, 'files')
        for sub in sorted(os.listdir(root)) if os.path.isdir(root) else []:
            d = os.path.join(root, sub)
            for name in os.listdir(d):
                if name not in needed:
                    os.unlink(os.path.join(d, name))
                    removed += 1
            if not os.listdir(d):
                os.rmdir(d)

    for z in zips.values():
        z.close()
    log('Gotowe: wersja %s, kanal %s%s: %d plikow, %.1f MB; w magazynie nowych %d (%.1f MB, twardych linkow %d), usunietych starych %d'
        % (a.wersja, a.kanal, ' (domyslny)' if channels['default'] == a.kanal else '', len(listed), (total + len(stamp)) / 1048576.0,
           stats['nowe'], stats['nowe_bajty'] / 1048576.0, stats['linki'], removed))
    log('  lista: %s' % mpath)


if __name__ == '__main__':
    main()
