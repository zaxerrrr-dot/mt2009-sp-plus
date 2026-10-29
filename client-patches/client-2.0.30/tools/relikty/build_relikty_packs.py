# -*- coding: utf-8 -*-
# MT2009_PLUS_RELIC_V1 - the client build's part for Bonus Reliktu (root/uirelikt.py, root/uiscript/reliktwindow.py,
# root/relikt_data.py and the icons root/icon/item/302xx.tga travel in client-2.0.30/root like every root change):
#   1. the existing packs "gamedata" (gamedata/item_list.txt) and "dbdata" (gamedata/item_proto, locale/pl/itemdesc.txt)
#      get the 15 items of relikty.sql (tools/relikty/relikty_items.json, patch_relikty_client.py) - as ../czepiec;
#   2. a new pack "relikty" with GF 26.1.11's images of the relic window (the package "Official Passive Attr System",
#      Best Studio, uses them too):
#        d:/ymir work/ui/passive_01.dds                    the window's atlas (every passive_attr/*.sub names it)
#        d:/ymir work/ui/game/passive_attr/*.sub            the background, the page buttons I (up) / II (down)
#      (relikty_files.json: names, sizes and sha256 of GF's files; the bytes are read from the GF client at build time).
#      A name another listed pack already has (BASE or OUT) is left out when the bytes are the same, and refused when
#      they differ. The pack's Index line goes LAST ("*" + "relikty"), as ../wieza.
# BUILD ORDER - it shares gamedata and dbdata: after every other step that patches them (after ../ybiolog), on the same
# OUT (a pack already in OUT - an earlier step changed it - is the one patched):
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/relikty/build_relikty_packs.py <BASE pack dir> <OUT pack dir> [--check]
#
# clientY.sh: after the ybiolog line,
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/relikty/build_relikty_packs.py $C/azbase \
#     $C/out/pack > $C/relikty.json
# then relikty/verify_relikty.py in the verify loop. Every entry written is read back. Idempotent: a second run gives
# "unchanged" and the Index line is not added twice.
import hashlib
import json
import os
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, HERE)
ZIP_LIMIT = 29 * 1024 * 1024

PACK = 'relikty'
GF = '/opt/metin2/cache/gf/Gameforge_26.1.11/_client/d_/'
MANIFEST = os.path.join(HERE, 'relikty_files.json')
TEXT = ('.txt', '.msa', '.msm', '.mse', '.mss', '.msenv', '.sub', '.prb', '.prd', '.pre', '.prt', '.py', '.ifl', '.pra')


def ctype(name):
    return 2 if name.endswith(TEXT) else 1


def gf_files():
    """{name: bytes} - GF's files, checked against relikty_files.json"""
    out = {}
    for name, w in sorted(json.load(open(MANIFEST))['files'].items()):
        path = GF + name[len('d:/'):]
        if not os.path.isfile(path):
            raise SystemExit('%s: not in the GF client (%s)' % (name, path))
        b = open(path, 'rb').read()
        if len(b) != w['size'] or hashlib.sha256(b).hexdigest() != w['sha256']:
            raise SystemExit('%s: the GF client\'s file differs from relikty_files.json' % name)
        if name.endswith('.dds'):
            assert b[:4] == b'DDS ', name
        if name.endswith('.sub'):
            assert b'subImage' in b, name
        out[name] = b
    return out


def others(base, out):
    """{name: (dir, pack)} of every listed pack but ours - OUT last (a pack there is the one the client gets)"""
    import m2pack
    where = {}
    for d in (base, out):
        for fn in sorted(os.listdir(d)):
            if fn.endswith('.index') and fn[:-6] != PACK:
                for e in m2pack.read_index(os.path.join(d, fn))[2]:
                    where[e['name']] = (d, fn[:-6])
    return where


def wanted(base, out, report):
    """GF's files minus the ones another listed pack already has with the same bytes"""
    import m2pack
    import packlib
    files = gf_files()
    where = others(base, out)
    cache = {}
    keep = {}
    for name, b in sorted(files.items()):
        if name not in where:
            keep[name] = b
            continue
        d, p = where[name]
        if (d, p) not in cache:
            f, v, ents = m2pack.read_index(os.path.join(d, p + '.index'))
            cache[(d, p)] = (dict((e['name'], e) for e in ents), packlib.rd(os.path.join(d, p + '.data')))
        ents, dat = cache[(d, p)]
        if m2pack.read_entry(dat, ents[name]) != b:
            raise SystemExit('%s: pack %s has other bytes than GF\'s - it would shadow ours' % (name, p))
        report.setdefault('already_in', {})[name] = p
    return keep


def data_packs(base, out, check, report):
    """1. gamedata / dbdata (the method of ../czepiec/build_czepiec_packs.py)"""
    import m2pack
    import packlib
    import patch_relikty_client as pc
    rd = packlib.rd

    def src_of(pack):
        return out if os.path.exists(os.path.join(out, pack + '.index')) else base

    def write(pack, src, rep, ents, dat):
        tmp_i, tmp_d = os.path.join(out, pack + '.index.rl'), os.path.join(out, pack + '.data.rl')
        r = packlib.repack_add_typed(os.path.join(src, pack + '.index'), os.path.join(src, pack + '.data'), rep, {},
                                     tmp_i, tmp_d, ents[-1]['raw'])
        os.replace(tmp_i, os.path.join(out, pack + '.index'))
        os.replace(tmp_d, os.path.join(out, pack + '.data'))
        f, v, nw = m2pack.read_index(os.path.join(out, pack + '.index'))
        nd = rd(os.path.join(out, pack + '.data'))
        names = [e['name'] for e in nw]
        assert len(set(names)) == len(names), pack
        got = {}
        for e in nw:
            assert zlib.crc32(nd[e['pos']:e['pos'] + e['size']]) & 0xffffffff == e['dcrc'], (pack, e['name'])
            got[e['name']] = m2pack.read_entry(nd, e)
        for n, b in rep.items():
            assert got[n] == b, (pack, n)
        for e in ents:
            if e['name'] not in rep:
                assert got[e['name']] == m2pack.read_entry(dat, e), (pack, e['name'])
        return dict(old=r[0], added=r[1], replaced=r[2], entries=len(nw), data_mb=round(len(nd) / 1e6, 2),
                    under_zip_limit=len(nd) < ZIP_LIMIT)

    jobs = {'gamedata': [('gamedata/item_list.txt', pc.item_list)],
            'dbdata': [('gamedata/item_proto', pc.item_proto), ('locale/pl/itemdesc.txt', pc.itemdesc)]}
    for pack, files in jobs.items():
        src = src_of(pack)
        f, v, ents = m2pack.read_index(os.path.join(src, pack + '.index'))
        dat = rd(os.path.join(src, pack + '.data'))
        have = dict((e['name'], e) for e in ents)
        rep = {}
        for n, fn in files:
            b = m2pack.read_entry(dat, have[n])
            nb, changed = fn(b)
            if nb != b:
                rep[n] = nb
        if not rep:
            report[pack] = 'unchanged'
        elif check:
            report[pack] = dict(replace=sorted(rep))
        else:
            report[pack] = write(pack, src, rep, ents, dat)
            report[pack]['replaced_names'] = sorted(rep)


def ui_pack(base, out, check, report):
    """2. the pack "relikty" (the method of ../wieza/build_wieza_packs.py)"""
    import m2pack
    import packlib
    rd = packlib.rd
    files = wanted(base, out, report)
    have = None
    if os.path.exists(os.path.join(out, PACK + '.index')):
        f, v, ents = m2pack.read_index(os.path.join(out, PACK + '.index'))
        dat = rd(os.path.join(out, PACK + '.data'))
        have = dict((e['name'], m2pack.read_entry(dat, e)) for e in ents)
    if have == files:
        report[PACK] = 'unchanged'
    elif not files:
        report[PACK] = 'nothing to add - every file is in a listed pack'
    elif check:
        report[PACK] = dict(add=sorted(files), data_kb=round(sum(len(b) for b in files.values()) / 1e3, 1))
    else:
        tmpl = m2pack.read_index(os.path.join(base, 'gamedata.index'))[2][-1]['raw']
        ti, td = os.path.join(out, PACK + '.index.rl'), os.path.join(out, PACK + '.data.rl')
        packlib.repack_add_typed(None, None, {}, dict((k, (b, ctype(k))) for k, b in files.items()), ti, td, tmpl)
        os.replace(ti, os.path.join(out, PACK + '.index'))
        os.replace(td, os.path.join(out, PACK + '.data'))
        f, v, ents = m2pack.read_index(os.path.join(out, PACK + '.index'))
        dat = rd(os.path.join(out, PACK + '.data'))
        got = {}
        for e in ents:
            assert zlib.crc32(dat[e['pos']:e['pos'] + e['size']]) & 0xffffffff == e['dcrc'], e['name']
            assert e['ctype'] == ctype(e['name']), e['name']
            got[e['name']] = m2pack.read_entry(dat, e)
        assert got == files, 'read-back differs'
        report[PACK] = dict(entries=len(ents), data_kb=round(len(dat) / 1e3, 1))

    # Index: "*" + "relikty" at the end (only when the pack exists)
    if not check and os.path.exists(os.path.join(out, PACK + '.index')):
        ix_path = os.path.join(out, 'Index') if os.path.exists(os.path.join(out, 'Index')) else os.path.join(base, 'Index')
        ix = rd(ix_path)
        lines = [l.strip() for l in ix.replace(b'\r\n', b'\n').split(b'\n')]
        new = ix
        if PACK.encode() not in lines:
            nl = b'\r\n' if b'\r\n' in ix else b'\n'
            new = ix.rstrip(b'\r\n') + nl + b'*' + nl + PACK.encode() + nl
        if new != ix or ix_path != os.path.join(out, 'Index'):
            open(os.path.join(out, 'Index'), 'wb').write(new)
            report['Index'] = 'written'
        else:
            report['Index'] = 'unchanged'


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    check = '--check' in sys.argv
    base, out = args[:2]
    report = {}
    data_packs(base, out, check, report)
    ui_pack(base, out, check, report)
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
