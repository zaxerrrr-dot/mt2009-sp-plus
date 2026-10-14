# -*- coding: utf-8 -*-
# MT2009_PLUS_COPIED_MAPS_V1 - the copied maps get their parent's terrain in their own folder. GF's copied maps (Zaklety
# Las (SZC) 404 metin2_map_boss_crack_dawnmist, Zaklety Las 353 metin2_map_dawnmist_dungeon_01) shipped only setting.txt
# and a mapproperty.txt with ParentMapName "metin2_map_boss_awaken_dawnmist". Our exe (GameLib/MapBase.h
# GetMapDataDirectory) then reads "<parent>\Setting.txt" without the "maps/" its pack names carry - "LoadSetting(
# metin2_map_boss_awaken_dawnmist\Setting.txt) Failed", no terrain, no environment (the owner, 14 October 2026) - and
# even found, the parent's Setting.txt would give the parent's BasePosition. So each copied map gets every file of the
# parent's folder (sectors, environment) except setting.txt / mapproperty.txt under its own name, keeps its own
# setting.txt (its own base) and a mapproperty.txt without ParentMapName.
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 .../ycopymaps/build_ycopymaps.py <OUT pack dir>
#
# clientY.sh: after yfinal, before the verify loop. Idempotent (a second run finds nothing to do).
import json
import os
import sys
import zlib

sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
TEXT = ('.txt', '.msa', '.msm', '.mse', '.mss', '.msenv', '.sub', '.prb', '.prd', '.pre', '.prt', '.py', '.ifl', '.pra')
PARENT = 'metin2_map_boss_awaken_dawnmist'
COPIES = (('ycrack_maps', 'metin2_map_boss_crack_dawnmist'), ('yzaklety_maps', 'metin2_map_dawnmist_dungeon_01'))
PROPERTY = b'ScriptType MapProperty\r\n\r\nMapType "Outdoor"\r\n'


def main():
    import m2pack
    import packlib
    out = sys.argv[1]
    rd = packlib.rd
    # the parent's folder, from whichever OUT pack holds it
    parent, ppack = {}, None
    pp = 'maps/%s/' % PARENT
    for p in sorted(f[:-6] for f in os.listdir(out) if f.endswith('.index')):
        ents = m2pack.read_index(os.path.join(out, p + '.index'))[2]
        mine = [e for e in ents if e['name'].startswith(pp)]
        if mine:
            dat = rd(os.path.join(out, p + '.data'))
            for e in mine:
                parent[e['name'][len(pp):]] = m2pack.read_entry(dat, e)
            ppack = p
    if 'setting.txt' not in parent or '000000/height.raw' not in parent:
        raise SystemExit('the parent %s is in no OUT pack' % PARENT)
    report = {'parent_pack': ppack, 'parent_files': len(parent)}
    for pack, name in COPIES:
        ip, dp = os.path.join(out, pack + '.index'), os.path.join(out, pack + '.data')
        f, v, ents = m2pack.read_index(ip)
        dat = rd(dp)
        have = dict((e['name'], m2pack.read_entry(dat, e)) for e in ents)
        mp = 'maps/%s/' % name
        rep, add = {}, {}
        if have.get(mp + 'mapproperty.txt') != PROPERTY:
            rep[mp + 'mapproperty.txt'] = PROPERTY
        for rel, b in parent.items():
            if rel in ('setting.txt', 'mapproperty.txt'):
                continue
            n = mp + rel
            if n not in have:
                add[n] = (b, 2 if n.endswith(TEXT) else 1)
            elif have[n] != b:
                rep[n] = b
        if not rep and not add:
            report[pack] = 'unchanged'
            continue
        ti, td = ip + '.ycm', dp + '.ycm'
        packlib.repack_add_typed(ip, dp, rep, add, ti, td, ents[-1]['raw'])
        os.replace(ti, ip)
        os.replace(td, dp)
        f, v, nw = m2pack.read_index(ip)
        nd = rd(dp)
        got = {}
        for e in nw:
            assert zlib.crc32(nd[e['pos']:e['pos'] + e['size']]) & 0xffffffff == e['dcrc'], (pack, e['name'])
            got[e['name']] = m2pack.read_entry(nd, e)
        for n, b in list(rep.items()) + [(k, b) for k, (b, c) in add.items()]:
            assert got[n] == b, (pack, n)
        assert b'ParentMapName' not in got[mp + 'mapproperty.txt'] and mp + 'setting.txt' in got, pack
        report[pack] = dict(added=len(add), replaced=len(rep), entries=len(nw), data_mb=round(len(nd) / 1e6, 2))
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
