# -*- coding: utf-8 -*-
# MT2009_PLUS_FISHING_GLOBAL_V1 - the client build's part for fishing as on the global server: no new pack; the
# existing packs "gamedata" (gamedata/item_list.txt) and "dbdata" (gamedata/item_proto, locale/pl/itemdesc.txt) get the
# items of yohara_lowienie.sql (tools/yohara_lowienie/yohara_lowienie.json, patch_ylowienie_client.py): the new items,
# the rods Wedka+1..+20, the grilled fish of the wiki, Kula Rybaka. The icons (root/icon/item/27591, 27621-27625,
# 27797, 27824-27827, 27854-27857, 27884-27887, 55004, 55005 .tga - GF 26.1.11; 27625 = GF 83032) travel in
# client-2.0.30/root like every root change; the affect bar's icons of the golden tuna's bonus (742) and Mokre Szaty
# (743) are root/uiaffectbar.py, Wedka Weglowa's tooltip root/uitooltip.py. No cube line: the crafting window's
# recipes come from the server (cube.lowienie.txt, root/uicuberenewal.py); the golden tuna's dialog is the server's
# quest (lowienie/fishing.lua) - no client string.
# BUILD ORDER - they share gamedata and dbdata: after the other Yohara steps that write them (e.g. right after
# ../mikstury), on the same OUT (a pack already in OUT - an earlier step changed it - is the one patched):
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/ylowienie/build_ylowienie_packs.py <BASE pack dir> <OUT pack dir> [--check]
#
# clientY.sh: after the mikstury line,
#   S_ylowienie() { docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/ylowienie/build_ylowienie_packs.py \
#     $C/azbase $C/out/pack; }; step ylowienie $C/ylowienie.json S_ylowienie
# then verify_ylowienie.py on OUT. Every entry written is read back. Idempotent: a second run gives "unchanged".
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
    import patch_ylowienie_client as pc
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    check = '--check' in sys.argv
    base, out = args[:2]
    rd = packlib.rd
    report = {}

    def src_of(pack):
        return out if os.path.exists(os.path.join(out, pack + '.index')) else base

    def write(pack, src, rep, ents, dat):
        tmp_i, tmp_d = os.path.join(out, pack + '.index.yl'), os.path.join(out, pack + '.data.yl')
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
