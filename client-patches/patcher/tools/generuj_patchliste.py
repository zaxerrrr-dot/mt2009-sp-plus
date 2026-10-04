#!/usr/bin/env python3
"""MT2009 PLUS Patcher - builds the patch server tree (patchlist.json + files/).

The patcher (MT2009-Patcher.exe, N2Play Patcher format) downloads
<Patchlist> = a JSON array, one object per client file:

    {"name": "pack\\\\root.data",   path in the client folder, "\\" separators
     "size": 4124928,              bytes; 0 = the entry is ignored by the patcher
     "md5": "5D41402ABC4B2A76...", MD5 of the file, 32 hex digits, UPPER case
                                   (the patcher compares the text exactly)
     "uid": "5d41402abc4b2a76...", the file is downloaded from <Clientdata> + uid
     "delete": 0}                  1 = delete this file in the client folder
     ("keep": 1)                   only when missing; the player's copy is never
                                   compared (default for pack/dbdata.*, --zachowaj)

A client file that is missing or has another MD5 is downloaded. Files are
stored content-addressed (files/<md5 lower case>): publishing a new version
never changes a file a player may be downloading; patchlist.json is replaced
last, in one rename.

Sources are applied in order, a later source replaces the same path:

    python3 generuj_patchliste.py --wyjscie /opt/metin2/dist/patcher \\
        --zrodlo /opt/metin2/dist/klient/klient-test-2.0.28-pelny.zip \\
        --zrodlo '/opt/metin2/cache/relout/metin2-client-update-2.0.28.zip::metin2client.exe,Dolacz.*' \\
        --patcher /opt/metin2/dist/patcher-app

A source is a .zip or a folder; "::" adds a comma separated list of paths /
glob patterns to take from it (default: everything). Player files are never
published (coop*.cfg, *.cfg, UserData/, screenshot/, mark/, logs, ...).

CLIENT_VERSION: the release zips carry one at their root, and the patcher
writes it into the client folder - that is how the server launcher learns that
the patcher brought the client up to date. It is published from the last
source that has one (whatever the "::" patterns), as "<version>\\r\\n";
--client-version overrides it, --bez-client-version leaves it out.
"""
import argparse
import datetime
import fnmatch
import hashlib
import io
import json
import os
import re
import shutil
import sys
import tempfile
import zipfile

# Never published: the player's own files and runtime leftovers. Matched on
# the path with "/" separators, case-insensitive.
NEVER = [
    '*.cfg',                # coop.cfg, coop2.cfg, metin2.cfg, game1.cfg, config.cfg ...
    'userdata/*', 'screenshot/*', 'screenshots/*', 'mark/*',
    '*.log', 'syserr.txt', 'log.txt', 'errorlog.txt', '*.dmp', 'crash*',
    'mt2009-aktualizator.tmp/*', 'mt2009-aktualizator.log',
    '*.bak', '*.tmp', 'thumbs.db', 'desktop.ini',
    'client_version',       # published on its own (see read_client_version)
]
CHUNK = 1 << 20
# MT2009_PLUS_DB_EDITOR_V1: the player's own copy wins ("keep": 1 - the
# patcher downloads it only when missing, never "repairs" it): pack/dbdata.*
# holds the database editor's files, which the player unpacks from the zip of
# his server's panel. --zachowaj adds patterns, --bez-zachowania drops these.
KEEP = ['pack/dbdata.*']


def is_never(path):
    p = path.lower()
    return any(fnmatch.fnmatchcase(p, pat) for pat in NEVER)


def parse_source(text):
    if '::' in text:
        path, pats = text.split('::', 1)
        return path, [p.strip().replace('\\', '/') for p in pats.split(',') if p.strip()]
    return text, None


def wanted(path, patterns):
    if patterns is None:
        return True
    p = path.lower()
    return any(fnmatch.fnmatchcase(p, pat.lower()) for pat in patterns)


def iter_source(path, patterns):
    """(relative path with "/", opener) for every file of a zip or folder."""
    if os.path.isdir(path):
        for base, dirs, files in os.walk(path):
            dirs.sort()
            for name in sorted(files):
                full = os.path.join(base, name)
                rel = os.path.relpath(full, path).replace(os.sep, '/')
                if wanted(rel, patterns):
                    yield rel, (lambda f=full: open(f, 'rb'))
    elif zipfile.is_zipfile(path):
        zf = zipfile.ZipFile(path)
        for info in zf.infolist():
            if info.is_dir():
                continue
            rel = info.filename.replace('\\', '/')
            if wanted(rel, patterns):
                yield rel, (lambda i=info: zf.open(i))
    else:
        sys.exit('Nie znaleziono źródła (zip albo folder): %s' % path)


def read_client_version(path):
    """The version in the root CLIENT_VERSION of a zip or folder, or None."""
    data = None
    if os.path.isdir(path):
        for name in os.listdir(path):
            full = os.path.join(path, name)
            if name.lower() == 'client_version' and os.path.isfile(full):
                with open(full, 'rb') as f:
                    data = f.read(256)
                break
    elif zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as zf:
            for info in zf.infolist():
                if not info.is_dir() and info.filename.replace('\\', '/').lower() == 'client_version':
                    with zf.open(info) as f:
                        data = f.read(256)
                    break
    if data is None:
        return None
    text = data.decode('utf-8-sig', 'replace').strip()
    if not re.match(r'^[0-9A-Za-z._-]{1,32}$', text):
        sys.exit('CLIENT_VERSION w %s nie jest wersją: %r' % (path, text))
    return text


def check_rel(rel):
    parts = rel.split('/')
    if not rel or rel.startswith('/') or ':' in rel or any(p in ('', '.', '..') for p in parts):
        sys.exit('Niedozwolona ścieżka w źródle: %r' % rel)


def store(opener, files_dir):
    """Copies the file into files/<md5>, returns (md5 upper, size)."""
    md5 = hashlib.md5()
    size = 0
    fd, tmp = tempfile.mkstemp(dir=files_dir, prefix='.nowy-')
    try:
        with os.fdopen(fd, 'wb') as out, opener() as src:
            while True:
                block = src.read(CHUNK)
                if not block:
                    break
                md5.update(block)
                size += len(block)
                out.write(block)
        digest = md5.hexdigest()
        target = os.path.join(files_dir, digest)
        if os.path.exists(target) and os.path.getsize(target) == size:
            os.unlink(tmp)
        else:
            os.chmod(tmp, 0o644)
            os.replace(tmp, target)
        return digest.upper(), size
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def write_json(path, data):
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write('\n')
    os.chmod(tmp, 0o644)
    os.replace(tmp, path)


def main():
    ap = argparse.ArgumentParser(description='Buduje listę plików patchera MT2009 PLUS (patchlist.json + files/).',
                                 formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument('--zrodlo', action='append', required=True, metavar='ZIP_LUB_FOLDER[::wzorce]',
                    help='źródło plików klienta; można podać kilka (późniejsze nadpisują wcześniejsze)')
    ap.add_argument('--patcher', metavar='FOLDER',
                    help='folder z MT2009-Patcher.exe (+ .exe.config) - dołącza patcher do listy (samoaktualizacja)')
    ap.add_argument('--usun', action='append', default=[], metavar='ŚCIEŻKA',
                    help='plik klienta do usunięcia u graczy (wpis "delete")')
    ap.add_argument('--zachowaj', action='append', default=[], metavar='WZORZEC',
                    help='plik gracza: pobierany tylko gdy go brak (wpis "keep"); domyślnie też ' + ', '.join(KEEP))
    ap.add_argument('--bez-zachowania', action='store_true', help='bez domyślnej listy "keep" (%s)' % ', '.join(KEEP))
    ap.add_argument('--pomin', action='append', default=[], metavar='WZORZEC',
                    help='nie publikuj tych plików wcale (ścieżka klienta, wzorzec glob)')
    ap.add_argument('--client-version', metavar='WERSJA',
                    help='wersja w publikowanym CLIENT_VERSION (domyślnie: z CLIENT_VERSION ostatniego źródła, które go ma)')
    ap.add_argument('--bez-client-version', action='store_true',
                    help='nie publikuj CLIENT_VERSION')
    ap.add_argument('--wyjscie', default='/opt/metin2/dist/patcher', help='drzewo serwera (domyślnie %(default)s)')
    ap.add_argument('--bez-sprzatania', action='store_true', help='nie usuwaj starych plików z files/')
    args = ap.parse_args()
    keep = ([] if args.bez_zachowania else list(KEEP)) + [k.replace('\\', '/') for k in args.zachowaj]
    omit = [k.replace('\\', '/').lower() for k in args.pomin]

    out = os.path.abspath(args.wyjscie)
    files_dir = os.path.join(out, 'files')
    os.makedirs(files_dir, exist_ok=True)
    os.chmod(out, 0o755)
    os.chmod(files_dir, 0o755)

    chosen = {}   # lower-case path -> (path, opener, source)
    sources = [parse_source(s) for s in args.zrodlo]
    if args.patcher:
        pats = ['MT2009-Patcher.exe', 'MT2009-Patcher.exe.config']
        if not os.path.isfile(os.path.join(args.patcher, 'MT2009-Patcher.exe')):
            sys.exit('Brak MT2009-Patcher.exe w %s' % args.patcher)
        sources.append((args.patcher, pats))
    skipped = []
    client_version = None
    client_version_from = None
    for path, patterns in sources:
        found = read_client_version(path)
        if found:
            client_version, client_version_from = found, path
        count = 0
        for rel, opener in iter_source(path, patterns):
            check_rel(rel)
            if rel.lower() == 'client_version':
                continue    # read by read_client_version, published below
            if is_never(rel) or any(fnmatch.fnmatchcase(rel.lower(), pat) for pat in omit):
                skipped.append(rel)
                continue
            chosen[rel.lower()] = (rel, opener, path)
            count += 1
        if count == 0:
            sys.exit('Źródło %s nie dało żadnego pliku (sprawdź wzorce po "::")' % path)
        print('%-70s %4d plików' % (os.path.basename(path) + ('' if patterns is None else ' :: ' + ','.join(patterns)), count))

    items = []
    total = 0
    for key in sorted(chosen):
        rel, opener, src = chosen[key]
        md5, size = store(opener, files_dir)
        if size == 0:
            print('UWAGA: pusty plik %s pominięty (patcher ignoruje wpisy o rozmiarze 0)' % rel)
            continue
        item = {'name': rel.replace('/', '\\'), 'size': size, 'md5': md5, 'uid': md5.lower(), 'delete': 0}
        if any(fnmatch.fnmatchcase(rel.lower(), pat.lower()) for pat in keep):
            item['keep'] = 1
            print('keep (tylko gdy brak): %s' % rel)
        items.append(item)
        total += size
    if args.client_version:
        client_version, client_version_from = args.client_version.strip(), '--client-version'
    if args.bez_client_version:
        client_version = None
    if client_version:
        print('CLIENT_VERSION %s (z %s)' % (client_version, client_version_from))
        data = (client_version + '\r\n').encode('ascii')
        md5, size = store(lambda: io.BytesIO(data), files_dir)
        items.append({'name': 'CLIENT_VERSION', 'size': size, 'md5': md5, 'uid': md5.lower(), 'delete': 0})
    else:
        print('UWAGA: bez CLIENT_VERSION - launcher serwera rozpozna klienta z patchera tylko po sumach z client-files.json')
    for rel in args.usun:
        rel = rel.replace('\\', '/')
        check_rel(rel)
        if rel.lower() in chosen:
            sys.exit('%s jest jednocześnie w źródłach i w --usun' % rel)
        # size must be > 0, otherwise the patcher skips the entry entirely
        items.append({'name': rel.replace('/', '\\'), 'size': 1, 'md5': '', 'uid': '', 'delete': 1})

    listing = os.path.join(out, 'patchlist.json')
    previous = os.path.join(out, 'patchlist-poprzednia.json')
    old_items = []
    if os.path.exists(listing):
        try:
            with open(listing, encoding='utf-8') as f:
                old_items = json.load(f)
        except ValueError:
            old_items = []
        shutil.copyfile(listing, previous)
        os.chmod(previous, 0o644)
    write_json(listing, items)
    write_json(os.path.join(out, 'patchlist-info.json'), {
        'wygenerowano': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'zrodla': [p + ('' if pats is None else '::' + ','.join(pats)) for p, pats in sources],
        'client_version': client_version,
        'plikow': len(items),
        'bajtow': total,
    })

    removed = 0
    if not args.bez_sprzatania:
        keep = {i['uid'] for i in items} | {i.get('uid') for i in old_items if isinstance(i, dict)}
        for name in os.listdir(files_dir):
            if name not in keep:
                os.unlink(os.path.join(files_dir, name))
                removed += 1
    print('Zapisano %s: %d wpisów, %.1f MB; usunięto starych plików: %d' % (listing, len(items), total / 1048576, removed))
    if skipped:
        print('Pominięte pliki gracza: %s' % ', '.join(sorted(set(skipped))[:20]))


if __name__ == '__main__':
    main()
