"""Writes base/<client version>/ from a released client's pack folder - run
once per client release (the server package then carries ~0.6 MB):

    python3 -m m2clientpack.make_base <client>/pack 2.0.52

base.json  the client version, per pack the release's index (SHA-256, size)
           and the length of its .data; per patched file its pack and hash.
<pack>.index, files/<name>: the release's index and the files the overlay
patches (FILES), taken out of the packs.
"""
import json
import os
import sys

from . import eterpack, overlay

FILES = (
    ('gamedata', 'gamedata/item_proto'),
    ('gamedata', 'gamedata/skilltable.txt'),
    ('locale', 'locale/pl/itemdesc.txt'),
    ('locale', 'locale/pl/skilldesc.txt'),
)


def make_base(pack_dir, version, root=overlay.BASE_ROOT):
    out = os.path.join(root, version)
    os.makedirs(os.path.join(out, 'files'), exist_ok=True)
    meta = {'client': version, 'packs': {}, 'files': {}}
    for pack in sorted(set(p for p, _ in FILES)):
        with open(os.path.join(pack_dir, pack + '.index'), 'rb') as f:
            index_blob = f.read()
        data_size = os.path.getsize(os.path.join(pack_dir, pack + '.data'))
        _, entries = eterpack.read_index_bytes(index_blob)
        end = max(e.pos + e.real for e in entries)
        if end > data_size:
            raise SystemExit('%s.data is shorter than its index says' % pack)
        meta['packs'][pack] = {'indexSha256': overlay.sha256(index_blob), 'indexSize': len(index_blob),
                               'dataSize': data_size, 'entries': len(entries)}
        with open(os.path.join(out, pack + '.index'), 'wb') as f:
            f.write(index_blob)
        by_name = dict((e.name, e) for e in entries)
        with open(os.path.join(pack_dir, pack + '.data'), 'rb') as f:
            for p, name in FILES:
                if p != pack:
                    continue
                e = by_name[name]
                f.seek(e.pos)
                data = eterpack.decode_entry(f.read(e.size), e.ctype)
                path = os.path.join(out, 'files', *name.split('/'))
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'wb') as g:
                    g.write(data)
                meta['files'][name] = {'pack': pack, 'size': len(data), 'sha256': overlay.sha256(data)}
    with open(os.path.join(out, 'base.json'), 'w', encoding='utf-8') as f:
        json.dump(meta, f, indent=1, sort_keys=True)
    return out


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    print(make_base(sys.argv[1], sys.argv[2]))
