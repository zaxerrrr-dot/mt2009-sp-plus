# -*- coding: utf-8 -*-
# MT2009_PLUS_SMH_TOWER_V3 - the client build's part for Wieza Sung Mahi's window, floor board and defeat popup
# (root/uiwiezasm.py, root/uiscript/sungmaheetowerenter.py and root/uiscript/sungmaheetowerinformationboard.py travel in
# client-2.0.30/root like every root change). This puts GF 26.1.11's images those name into a new pack, "wieza":
#   d:/ymir work/ui/smhtower_01.dds                         the tower's UI atlas (every sungmahee_tower/*.sub names it)
#   d:/ymir work/ui/game/sungmahee_tower/*.sub              17 parts: floor buttons, clear icons, the board, the gauge,
#                                                           the exit X, the list's division line, the blessing line
#   d:/ymir work/ui/game/sungmahee_tower/wieza_buff.sub, wieza_debuff.sub    the blessing / curse icons: GF's
#                                                           skill/common/affect/sungmahee_tower_buff.sub / _debuff.sub
#                                                           with their image renamed to the one below
#   d:/ymir work/ui/game/sungmahee_tower/wieza_affect.dds   GF's d:/ymir work/ui/newskillcommon.dds (256x768) under a
#                                                           new name: our zodiak_maps pack carries an older
#                                                           newskillcommon.dds (256x352) that comes first in the Index,
#                                                           and GF's icons sit at y 384-416 - outside it
# (wieza_files.json: names, sizes and sha256 of GF's files; the bytes are read from the GF client at build time.)
# A name another listed pack already has (BASE or OUT) is left out when the bytes are the same, and refused when they
# differ. The pack's Index line goes LAST ("*" + "wieza"): the exe keeps the first pack that registers a name, so a
# file the players' base install has (etc / gf_official, packs this tree does not hold) stays its own - this pack only
# fills the gaps (its own wieza_* names are new).
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/wieza/build_wieza_packs.py <BASE pack dir> <OUT pack dir> [--check]
#
# clientY.sh: after the kamienie line (any place after the Index writers works - the line goes last),
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/wieza/build_wieza_packs.py $C/azbase \
#     $C/out/pack > $C/wieza.json
# then wieza/verify_wieza.py in the verify loop. Every entry written is read back. Idempotent: a second run gives
# "unchanged" and the Index line is not added twice. --check measures only.
import hashlib
import json
import os
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')

PACK = 'wieza'
GF = '/opt/metin2/cache/gf/Gameforge_26.1.11/_client/d_/'
MANIFEST = os.path.join(HERE, 'wieza_files.json')
TEXT = ('.txt', '.msa', '.msm', '.mse', '.mss', '.msenv', '.sub', '.prb', '.prd', '.pre', '.prt', '.py', '.ifl', '.pra')


def ctype(name):
    return 2 if name.endswith(TEXT) else 1


def manifest():
    return json.load(open(MANIFEST))['files']


# the affect icons under our own names (see above): {our name: (GF's name, the image line to put in)}
AFFECT_DDS = 'd:/ymir work/ui/game/sungmahee_tower/wieza_affect.dds'
GF_AFFECT_DDS = 'd:/ymir work/ui/newskillcommon.dds'
GEN_SUBS = {'d:/ymir work/ui/game/sungmahee_tower/wieza_buff.sub': 'd:/ymir work/ui/skill/common/affect/sungmahee_tower_buff.sub',
            'd:/ymir work/ui/game/sungmahee_tower/wieza_debuff.sub': 'd:/ymir work/ui/skill/common/affect/sungmahee_tower_debuff.sub'}


def gf_raw():
    """{name: bytes} - GF's files, checked against wieza_files.json"""
    out = {}
    for name, w in sorted(manifest().items()):
        path = GF + name[len('d:/'):]
        if not os.path.isfile(path):
            raise SystemExit('%s: not in the GF client (%s)' % (name, path))
        b = open(path, 'rb').read()
        if len(b) != w['size'] or hashlib.sha256(b).hexdigest() != w['sha256']:
            raise SystemExit('%s: the GF client\'s file differs from wieza_files.json' % name)
        out[name] = b
    for name, b in out.items():
        if name.endswith('.dds'):
            assert b[:4] == b'DDS ', name
        if name.endswith('.sub'):
            assert b'subImage' in b, name
    return out


def gf_files():
    """{name: bytes} - what the pack carries: GF's UI files, the affect image and its two .sub under our names"""
    raw = gf_raw()
    out = dict((n, b) for n, b in raw.items() if n != GF_AFFECT_DDS and n not in GEN_SUBS.values())
    out[AFFECT_DDS] = raw[GF_AFFECT_DDS]
    for ours, theirs in GEN_SUBS.items():
        b = raw[theirs]
        assert b'image "newskillcommon.dds"' in b, theirs
        out[ours] = b.replace(b'image "newskillcommon.dds"', b'image "game/sungmahee_tower/wieza_affect.dds"')
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


def main():
    import m2pack
    import packlib
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    check = '--check' in sys.argv
    base, out = args[:2]
    rd = packlib.rd
    report = {}
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
        ti, td = os.path.join(out, PACK + '.index.wz'), os.path.join(out, PACK + '.data.wz')
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

    # Index: "*" + "wieza" at the end (only when the pack exists)
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
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
