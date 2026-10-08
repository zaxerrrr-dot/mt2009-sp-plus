# -*- coding: utf-8 -*-
# MT2009_PLUS_NS_WIKI_ITEMS_V1 - the new client pack "wiki_nowe": the icons and the weapons' models of the wiki
# families and materials (Autor: Digi Rasta, nowy-system 0.33.0; the records are patch_wikinowe_client.py's):
#   icon/item/00500 01500 02500 03500 05500 07500 95601 95602 95603.tga - his 9 icons made from the wiki's
#       pictures (client-patches/client-2.0.30/wikinowe/icon/item; the Cyjanitowe weapons, Stabilne Sznury, Wzor
#       Kroju, Ciezkie Pasy have no official icon);
#   icon/item/14570 15440 15450 16570 30602 30603 30604 30610 30616 30617 30618 30623 30624 30626 30627 30629
#       50639.tga - the official icons, from the unpacked Gameforge 26.1.11 client (our icon pack has none of them);
#   d:/ymir work/item/weapon/00500 01500 02500 03500 05500 07500.gr2 and weapon_jin.dds (their texture) - the
#       Cyjanitowe weapons' models from the same client (32-bit GR2, the exe reads them).
# A name some other pack already carries is left out (the exe takes a name from the first pack that registers it,
# and ours comes last in Index, so the base client's copy would win anyway). The pack's line goes at the end of
# pack/Index. Every entry written is read back.
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/wikinowe/build_wikinowe_pack.py <BASE pack dir> <OUT pack dir> [--check]
#
# BASE: the client's packs so far (Index, the names of every other pack); OUT: where wiki_nowe.index / .data and the
# Index go (an Index already in OUT - written by an earlier step - is the one extended). --check measures only.
# Idempotent: a BASE or OUT that has wiki_nowe with the same content gives "unchanged".
import json
import os
import sys
import zlib

sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')

PACK = 'wiki_nowe'
HERE = os.path.dirname(os.path.abspath(__file__))
OURS = os.path.normpath(os.path.join(HERE, '..', '..', 'wikinowe'))
GF = '/opt/metin2/cache/gf/Gameforge_26.1.11/_client'
OUR_ICONS = ('00500', '01500', '02500', '03500', '05500', '07500', '95601', '95602', '95603')
GF_ICONS = ('14570', '15440', '15450', '16570', '30602', '30603', '30604', '30610', '30616', '30617', '30618',
            '30623', '30624', '30626', '30627', '30629', '50639')
GF_MODELS = ('00500.gr2', '01500.gr2', '02500.gr2', '03500.gr2', '05500.gr2', '07500.gr2', 'weapon_jin.dds')
GR2_64 = b'\xe5\x9b\x49\x5e'
TEXT = ('.txt', '.msa', '.msm')


def ctype(name):
    return 2 if name.endswith(TEXT) else 1


def sources():
    src = {}
    for v in OUR_ICONS:
        src['icon/item/%s.tga' % v] = os.path.join(OURS, 'icon', 'item', v + '.tga')
    for v in GF_ICONS:
        src['icon/item/%s.tga' % v] = os.path.join(GF, 'icon', 'item', v + '.tga')
    for f in GF_MODELS:
        src['d:/ymir work/item/weapon/' + f] = os.path.join(GF, 'd_', 'ymir work', 'item', 'weapon', f)
    return src


def main():
    import m2pack
    import packlib
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    check = '--check' in sys.argv
    base, out = args[:2]
    rd = packlib.rd
    others = {}
    for where in (base, out):
        if where == '-' or not os.path.isdir(where):
            continue
        for p in sorted(f[:-6] for f in os.listdir(where) if f.endswith('.index')):
            if p == PACK:
                continue
            for e in m2pack.read_index(os.path.join(where, p + '.index'))[2]:
                others.setdefault(e['name'], p)
    report = {}
    src = sources()
    skipped = dict((k, others[k]) for k in sorted(src) if k in others)
    items = dict((k, rd(s)) for k, s in src.items() if k not in skipped)
    if skipped:
        report['left_out'] = skipped
    bad64 = sorted(k for k, b in items.items() if k.endswith('.gr2') and b[:4] == GR2_64)
    if bad64:
        raise SystemExit('64-bit GR2: %s' % bad64)

    for where in (out, base):
        if where != '-' and os.path.exists(os.path.join(where, PACK + '.index')):
            f, v, ents = m2pack.read_index(os.path.join(where, PACK + '.index'))
            dat = rd(os.path.join(where, PACK + '.data'))
            if dict((e['name'], m2pack.read_entry(dat, e)) for e in ents) != items:
                raise SystemExit('%s in %s has other content - remove it and run again' % (PACK, where))
            report[PACK] = 'unchanged (%s)' % where
            break
    else:
        if check:
            size = sum(len(m2pack.encode_entry(b, ctype(k))) for k, b in items.items())
            report[PACK] = dict(files=len(items), raw_mb=round(sum(map(len, items.values())) / 1e6, 2),
                                data_mb=round(size / 1e6, 2))
        else:
            tmpl = m2pack.read_index(os.path.join(base, 'gf_mobs.index'))[2][-1]['raw']
            ti, td = os.path.join(out, PACK + '.index.tmp'), os.path.join(out, PACK + '.data.tmp')
            packlib.repack_add_typed(None, None, {}, dict((k, (b, ctype(k))) for k, b in items.items()), ti, td, tmpl)
            os.replace(ti, os.path.join(out, PACK + '.index'))
            os.replace(td, os.path.join(out, PACK + '.data'))
            f, v, ents = m2pack.read_index(os.path.join(out, PACK + '.index'))
            dat = rd(os.path.join(out, PACK + '.data'))
            got = {}
            for e in ents:
                assert zlib.crc32(dat[e['pos']:e['pos'] + e['size']]) & 0xffffffff == e['dcrc'], e['name']
                assert e['fcrc'] == zlib.crc32(e['name'].encode('cp1252')) & 0xffffffff, e['name']
                got[e['name']] = m2pack.read_entry(dat, e)
            assert got == items, 'read-back differs'
            report[PACK] = dict(entries=len(ents), data_mb=round(len(dat) / 1e6, 2))

    if not check:
        ix_path = os.path.join(out, 'Index') if os.path.exists(os.path.join(out, 'Index')) else os.path.join(base, 'Index')
        ix = rd(ix_path)
        lines = [l.strip() for l in ix.replace(b'\r\n', b'\n').split(b'\n')]
        new = ix if PACK.encode() in lines else ix.rstrip(b'\r\n') + b'\n*\n' + PACK.encode() + b'\n'
        if new != ix or ix_path != os.path.join(out, 'Index'):
            open(os.path.join(out, 'Index'), 'wb').write(new)
            report['Index'] = 'written'
        else:
            report['Index'] = 'unchanged'
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
