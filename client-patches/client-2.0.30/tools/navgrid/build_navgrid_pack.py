# -*- coding: utf-8 -*-
# MT2009_PLUS_NAVGRID_V1 - the client pack "navgrid" (maps/<map>/navgrid.bin of every map) from the cache of
# build_navgrid.py (its manifest.json), plus the Index line. Auto Lowy navigation based on Path-Finder V1.0 by
# @coanitoa97 (tutorial by Kolen).
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/navgrid/build_navgrid_pack.py <BASE pack dir> <OUT pack dir> \
#     [--cache /opt/metin2/cache/navgrid-cache] [--check]
#
# BASE: the client's packs so far (Index is read from OUT if an earlier step wrote one there, else from BASE); OUT: where
# navgrid.index / navgrid.data and the Index go. Every name is new (no other pack has a navgrid.bin), so the place in
# Index does not matter; the line goes at the end. Idempotent: the same grids give "unchanged" and the pack's files are
# not rewritten - a release whose maps did not change carries no navgrid delta. Entries are LZO (type 1, no XTEA).
# Every entry written is read back. --check measures only.
import json
import os
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import navgrid_lib as nl

PACK = 'navgrid'
AFTER = b'PACK'
CTYPE = 1
DEFAULT_CACHE = '/opt/metin2/cache/navgrid-cache'


def key(m):
    return 'maps/%s/navgrid.bin' % m.lower()


def main():
    m2pack = nl.pack_modules()
    import packlib
    argv = sys.argv[1:]
    cache = DEFAULT_CACHE
    if '--cache' in argv:
        i = argv.index('--cache')
        cache = argv[i + 1]
        del argv[i:i + 2]
    check = '--check' in argv
    args = [a for a in argv if not a.startswith('--')]
    base, out = args[:2]
    man = json.load(open(os.path.join(cache, 'manifest.json')))['maps']
    if not man:
        raise SystemExit('navgrid: the cache has no grids (run build_navgrid.py first)')
    want = {}
    for m, v in sorted(man.items()):
        b = open(os.path.join(cache, v['file']), 'rb').read()
        h = nl.parse_grid(b)[0]
        if h['stamp'] != v['stamp']:
            raise SystemExit('navgrid: %s - the cached file is not the manifest\'s (stamp)' % m)
        want[key(m)] = (b, CTYPE)
    raw = dict((k, b) for k, (b, c) in want.items())
    report = {}

    others = {}
    for d in (base, out):
        for p in sorted(f[:-6] for f in os.listdir(d) if f.endswith('.index')):
            if p == PACK:
                continue
            for e in m2pack.read_index(os.path.join(d, p + '.index'))[2]:
                if e['name'] in want:
                    others.setdefault(p, set()).add(e['name'])
    if others:
        raise SystemExit('navgrid: names of the pack in other packs: %s' % dict((p, sorted(n)[:5]) for p, n in others.items()))

    built = False
    if os.path.exists(os.path.join(out, PACK + '.index')):
        f, v, ents = m2pack.read_index(os.path.join(out, PACK + '.index'))
        dat = packlib.rd(os.path.join(out, PACK + '.data'))
        if (dict((e['name'], m2pack.read_entry(dat, e)) for e in ents) == raw and
                all(e['ctype'] == CTYPE for e in ents)):
            report[PACK] = dict(state='unchanged', entries=len(ents), data_kb=round(len(dat) / 1e3, 1))
            built = True
    if not built:
        if check:
            size = sum(len(m2pack.encode_entry(b, c)) for b, c in want.values())
            report[PACK] = dict(files=len(want), data_kb=round(size / 1e3, 1))
        else:
            tmpl = m2pack.read_index(os.path.join(base, 'gf_mobs.index'))[2][-1]['raw']
            ti, td = os.path.join(out, PACK + '.index.tmp'), os.path.join(out, PACK + '.data.tmp')
            packlib.repack_add_typed(None, None, {}, want, ti, td, tmpl)
            os.replace(ti, os.path.join(out, PACK + '.index'))
            os.replace(td, os.path.join(out, PACK + '.data'))
            f, v, ents = m2pack.read_index(os.path.join(out, PACK + '.index'))
            dat = packlib.rd(os.path.join(out, PACK + '.data'))
            got = {}
            for e in ents:
                assert zlib.crc32(dat[e['pos']:e['pos'] + e['size']]) & 0xffffffff == e['dcrc'], e['name']
                assert e['fcrc'] == zlib.crc32(e['name'].encode('cp1252')) & 0xffffffff, e['name']
                assert e['ctype'] == CTYPE, e['name']
                got[e['name']] = m2pack.read_entry(dat, e)
            assert got == raw, 'read-back differs'
            report[PACK] = dict(state='written', entries=len(ents), data_kb=round(len(dat) / 1e3, 1),
                                raw_kb=round(sum(len(b) for b in raw.values()) / 1e3, 1))

    if not check:
        ix_path = os.path.join(out, 'Index') if os.path.exists(os.path.join(out, 'Index')) else os.path.join(base, 'Index')
        ix = packlib.rd(ix_path)
        nl_ = b'\r\n' if b'\r\n' in ix else b'\n'
        lines = ix.replace(b'\r\n', b'\n').split(b'\n')
        stripped = [l.strip() for l in lines]
        if stripped[0] != AFTER:
            raise SystemExit('Index: the first line is not PACK')
        if PACK.encode() in stripped:
            new = ix
        else:
            tail = []
            while lines and not lines[-1].strip():
                tail.append(lines.pop())
            lines += [b'*', PACK.encode()] + tail
            new = nl_.join(lines)
        if new != ix or ix_path != os.path.join(out, 'Index'):
            open(os.path.join(out, 'Index'), 'wb').write(new)
            report['Index'] = 'written'
        else:
            report['Index'] = 'unchanged'
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
