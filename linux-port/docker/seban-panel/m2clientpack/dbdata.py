"""The client's "dbdata" pack (from client 2.0.52): the files the database
editor's changes reach - gamedata/item_proto, gamedata/skilltable.txt,
locale/pl/itemdesc.txt, locale/pl/skilldesc.txt - moved out of the gamedata
and locale packs into pack/dbdata.index + pack/dbdata.data, listed in
pack/Index (/opt/metin2/cache/c54/split_dbdata.py). No other pack has these
names, so the exe finds them only here.

The panel builds a whole new dbdata pack from the release's files (base/
<client version>/) patched with the edits, and hands it out as a zip the
player unpacks into his client folder himself. Nothing downloads anything
automatically: a client with several servers (localhost, COOP 1, COOP 2)
carries the data of the server whose zip was unpacked last.

base/<version>/: base.json (client version, per file its size, hash and
compression type), dbdata.index + dbdata.data (the release's own pack, the
"original files" download) and files/<name> (its contents).
"""
import hashlib
import io
import json
import os
import time
import zipfile

from . import eterpack

PACK = 'dbdata'
# MT2009_PLUS_ITEM_EXTRA_APPLY_V1: files the pack may carry that an older
# release's pack does not have yet ({name: compression type}). build() adds
# one only when the edits produce it (dbsource.py: the extra bonus lines,
# read by the client's uitooltip.py; a client without that code never opens
# it). From the next client release on its base has the file itself.
OPTIONAL_FILES = {'gamedata/item_extra_apply.txt': 2}
BASE_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'base')


def sha256(data):
    return hashlib.sha256(data).hexdigest().upper()


class Base(object):
    def __init__(self, path):
        self.path = path
        with open(os.path.join(path, 'base.json'), encoding='utf-8') as f:
            self.meta = json.load(f)
        self.version = self.meta['client']

    def names(self):
        return sorted(self.meta['files'])

    def ctype(self, name):
        return int(self.meta['files'][name]['ctype'])

    def file(self, name):
        with open(os.path.join(self.path, 'files', *name.split('/')), 'rb') as f:
            data = f.read()
        if sha256(data) != self.meta['files'][name]['sha256']:
            # e.g. a checkout that turned the line ends round (base/.gitattributes)
            raise ValueError('base %s/%s differs from base.json' % (self.version, name))
        return data

    def original(self):
        """(index bytes, data bytes) of the release's own dbdata pack."""
        out = []
        for ext in ('index', 'data'):
            with open(os.path.join(self.path, '%s.%s' % (PACK, ext)), 'rb') as f:
                data = f.read()
            if sha256(data) != self.meta['pack'][ext + 'Sha256']:
                raise ValueError('base %s/%s.%s differs from base.json' % (self.version, PACK, ext))
            out.append(data)
        return tuple(out)


def latest_base(root=BASE_ROOT):
    """The newest base/<version>/ (numeric compare)."""
    versions = [v for v in (os.listdir(root) if os.path.isdir(root) else [])
                if os.path.isfile(os.path.join(root, v, 'base.json'))]
    if not versions:
        raise FileNotFoundError('no client base in %s' % root)
    versions.sort(key=lambda v: [int(p) if p.isdigit() else 0 for p in v.split('.')])
    return Base(os.path.join(root, versions[-1]))


def build(base, files):
    """(index bytes, data bytes, changed names) of the dbdata pack: the
    release's files with `files` ({name: bytes}) in their place. With
    nothing changed it is the release's pack, byte for byte."""
    contents = dict((n, base.file(n)) for n in base.names())
    changed = sorted(n for n, data in files.items() if contents.get(n) != data)
    unknown = [n for n in changed if n not in contents and n not in OPTIONAL_FILES]
    if unknown:
        raise ValueError('not in the dbdata pack of client %s: %s' % (base.version, ', '.join(unknown)))
    if not changed:
        index, data = base.original()
        return index, data, []
    ctypes = dict((n, base.ctype(n)) for n in base.names())
    for n in changed:
        contents[n] = files[n]
        ctypes.setdefault(n, OPTIONAL_FILES.get(n, 2))
    names = sorted(contents)
    index, data = eterpack.write_pack([(n, contents[n], ctypes[n]) for n in names])
    verify(index, data, contents)
    return index, data, changed


def verify(index, data, contents):
    """The pack read back as the client reads it: every name once, each
    decoding to exactly its contents."""
    _ver, entries = eterpack.read_index_bytes(index)
    names = [e.name for e in entries]
    if sorted(names) != sorted(contents) or len(set(names)) != len(names):
        raise AssertionError('dbdata: names %s' % names)
    for e in entries:
        if e.fcrc != eterpack.name_crc(e.name) or eterpack.read_entry(data, e) != contents[e.name]:
            raise AssertionError('dbdata: %s reads back differently' % e.name)


README = u"""Pliki klienta z edytora bazy danych - serwer: {server}
=================================================================

Co to jest: nazwy, poziomy, bonusy przedmiotów i opisy umiejętności tak, jak
ustawiono je w edytorze bazy danych tego serwera (panel Seban).
{what}
Jak zainstalować:
1. Zamknij grę.
2. Rozpakuj ten zip do folderu klienta (tam, gdzie jest metin2client.exe).
   Pliki trafią do pack\\dbdata.index i pack\\dbdata.data - zgódź się na
   nadpisanie.
3. Uruchom grę.

Działa z klientem {version} (i nowszym, dopóki nie zmieni się w nim paczka
dbdata). Starszy klient tej paczki nie zna - najpierw go zaktualizuj.

Możesz wysłać ten zip znajomemu, który gra na tym serwerze (COOP). Masz w
kliencie kilka serwerów? Klient pokazuje dane z ostatnio rozpakowanego zipa -
grając na innym serwerze rozpakuj jego zip albo "oryginalne pliki".

Zbudowano: {built}
"""


def make_zip(base, index, data, server, changed, original=False):
    """(file name, zip bytes): pack/dbdata.index, pack/dbdata.data and
    CZYTAJ_MNIE.txt."""
    stamp = time.strftime('%Y-%m-%d_%H%M')
    safe = ''.join(ch if ch.isalnum() or ch in '-_.' else '-' for ch in (server or 'serwer'))[:40].strip('-') or 'serwer'
    what = (u'\nTo są ORYGINALNE pliki klienta %s - bez zmian z edytora.\n' % base.version if original else
            (u'\nZmienione pliki: %s.\n' % ', '.join(changed) if changed else
             u'\nTen serwer nie zmienia jeszcze niczego, co widzi klient.\n'))
    text = README.format(server=server or '?', version=base.version, what=what,
                         built=time.strftime('%d.%m.%Y %H:%M')).replace(u'\n', u'\r\n')
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('pack/%s.index' % PACK, index)
        z.writestr('pack/%s.data' % PACK, data)
        z.writestr('CZYTAJ_MNIE.txt', text.encode('utf-8-sig'))
    label = 'oryginal' if original else safe
    return 'dbdata-%s-klient-%s-%s.zip' % (label, base.version, stamp), buf.getvalue()
