# -*- coding: utf-8 -*-
# MT2009_PLUS_COSTUME_SET_V2 - the client build's part for the costume sets' items (patch_zestawy_client.py):
#   * the existing packs "gamedata" (gamedata/item_list.txt) and "dbdata" (gamedata/item_proto, locale/pl/itemdesc.txt)
#     get the 6 items of tools/zestawy/zestawy_items.json (the method of ../ygloves/build_ygloves_packs.py);
#   * a new pack "gf_zestawy" (its line at the end of pack/Index, the method of ../gfore/build_gfore_pack.py) carries
#     Szarfa Serca (unikat.)'s model from the unpacked GF 26.1.11 client: acce_valentine_2020_4.gr2 and the one texture
#     it names, acce_valentine_2020_1.dds (gfres.gr2_textures).
# The icons (root/icon/item/70607, 71188, 71199, 71202, 72713, 86064.tga) and root/costume_set_bonus.py travel in
# client-2.0.30/root like every root change.
# BUILD ORDER - gamedata and dbdata are shared: after every other step that patches them, on the same OUT:
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/zestawy/build_zestawy_packs.py <BASE pack dir> <OUT pack dir> [--check]
#
# clientY.sh: after the ygloves line (and before the verify loop),
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/zestawy/build_zestawy_packs.py $C/azbase $C/out/pack \
#     > $C/zestawy.json
# Every entry written is read back. Idempotent: a second run gives "unchanged".
import json
import os
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, HERE)
ZIP_LIMIT = 29 * 1024 * 1024
PACK = 'gf_zestawy'
GF_DIR = '/opt/metin2/cache/gf/Gameforge_26.1.11/_client/d_/ymir work/item/wing'
IN_PACK = 'd:/ymir work/item/wing/'
FILES = ('acce_valentine_2020_4.gr2', 'acce_valentine_2020_1.dds')


def main():
    import m2pack
    import packlib
    import patch_zestawy_client as pc
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    check = '--check' in sys.argv
    base, out = args[:2]
    rd = packlib.rd
    report = {}

    def src_of(pack):
        return out if os.path.exists(os.path.join(out, pack + '.index')) else base

    # --- gamedata / dbdata: the items' rows
    def write(pack, src, rep, ents, dat):
        tmp_i, tmp_d = os.path.join(out, pack + '.index.zst'), os.path.join(out, pack + '.data.zst')
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

    # --- gf_zestawy: the sash's model
    items = dict((IN_PACK + f, rd(os.path.join(GF_DIR, f))) for f in FILES)
    for where in (out, base):
        if os.path.exists(os.path.join(where, PACK + '.index')):
            f, v, ents = m2pack.read_index(os.path.join(where, PACK + '.index'))
            dat = rd(os.path.join(where, PACK + '.data'))
            if dict((e['name'], m2pack.read_entry(dat, e)) for e in ents) != items:
                raise SystemExit('%s in %s has other content - remove it and run again' % (PACK, where))
            report[PACK] = 'unchanged (%s)' % where
            break
    else:
        others = {}
        for p in sorted(f[:-6] for f in os.listdir(base) if f.endswith('.index')):
            if p == PACK:
                continue
            for e in m2pack.read_index(os.path.join(base, p + '.index'))[2]:
                others.setdefault(e['name'], p)
        clash = dict((k, others[k]) for k in items if k in others)
        if clash:
            raise SystemExit('names already in other packs: %s' % clash)
        if check:
            report[PACK] = dict(files=len(items), raw_mb=round(sum(map(len, items.values())) / 1e6, 2))
        else:
            tmpl = m2pack.read_index(os.path.join(base, 'gf_mobs.index'))[2][-1]['raw']
            ti, td = os.path.join(out, PACK + '.index.tmp'), os.path.join(out, PACK + '.data.tmp')
            packlib.repack_add_typed(None, None, {}, dict((k, (b, 1)) for k, b in items.items()), ti, td, tmpl)
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
