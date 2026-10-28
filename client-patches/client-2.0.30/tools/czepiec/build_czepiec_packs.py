# -*- coding: utf-8 -*-
# MT2009_PLUS_SERPENT_HOOD_V1 - the client build's part for Wężowy Czepiec (12880-12895) and its materials (31264-31269):
# no new pack (helmets are not drawn on the character - no model goes with the hood); the existing packs "gamedata"
# (gamedata/item_list.txt) and "dbdata" (gamedata/item_proto, locale/pl/itemdesc.txt) get the 22 items of
# yohara_czepiec.sql (tools/czepiec/czepiec_items.json, patch_czepiec_client.py). The icons (root/icon/item/12880.tga,
# 31264-31269.tga, GF 26.1.11) and the random second bonus's table (root/ysets_hood.py, read by root/ysets.py) travel in
# client-2.0.30/root like every root change.
# BUILD ORDER - it shares gamedata and dbdata: after every other step that patches them (after ../kamienie), on the
# same OUT (a pack already in OUT - an earlier step changed it - is the one patched):
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/czepiec/build_czepiec_packs.py <BASE pack dir> <OUT pack dir> [--check]
#
# clientY.sh: after the kamienie line,
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/czepiec/build_czepiec_packs.py $C/azbase \
#     $C/out/pack > $C/czepiec.json
# then czepiec/verify_czepiec.py in the verify loop. Every entry written is read back. Idempotent: a second run gives
# "unchanged".
import json
import os
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, HERE)
ZIP_LIMIT = 29 * 1024 * 1024


def main():
    import m2pack
    import packlib
    import patch_czepiec_client as pc
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    check = '--check' in sys.argv
    base, out = args[:2]
    rd = packlib.rd
    report = {}

    def src_of(pack):
        return out if os.path.exists(os.path.join(out, pack + '.index')) else base

    def write(pack, src, rep, ents, dat):
        tmp_i, tmp_d = os.path.join(out, pack + '.index.cz'), os.path.join(out, pack + '.data.cz')
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
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
