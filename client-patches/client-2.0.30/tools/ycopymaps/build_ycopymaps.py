# -*- coding: utf-8 -*-
# MT2009_PLUS_COPIED_MAPS_V1 - the copied maps get their parent's terrain in their own folder. GF's copied maps (Zaklety
# Las (SZC) 404 metin2_map_boss_crack_dawnmist, Zaklety Las 353 metin2_map_dawnmist_dungeon_01) shipped only setting.txt
# and a mapproperty.txt with ParentMapName "metin2_map_boss_awaken_dawnmist". Our exe (GameLib/MapBase.h
# GetMapDataDirectory) then reads "<parent>\Setting.txt" without the "maps/" its pack names carry - "LoadSetting(
# metin2_map_boss_awaken_dawnmist\Setting.txt) Failed", no terrain, no environment (the owner, 14 October 2026) - and
# even found, the parent's Setting.txt would give the parent's BasePosition. So each copied map gets every file of the
# parent's folder (sectors, environment) except setting.txt / mapproperty.txt under its own name, keeps its own
# setting.txt (its own base) and a mapproperty.txt without ParentMapName.
# 3.0.7 (MT2009_PLUS_MAP_ENVIRONMENT_V1, a Yohara 3.0.6 player's syserr of 3 November 2026 - "CMapOutdoor::
# RenderBeforeLensFlare mc_pEnvironmentData is NULL" every frame): ../ypb's 369 Twierdza Czerwonego Smoka (PB)
# metin2_map_boss_awaken_flame and 370 Straznica Nemere (PB) metin2_map_boss_awaken_snow are copied maps the same way
# (ParentMapName "metin2_map_n_flame_dungeon_01" / "metin2_map_n_snow_dungeon_01", our 351/352): LoadSetting failed
# there too - no terrain, and with no Environment read the exe asks for d:/ymir work/environment/me.msenv / ow.msenv (the
# map name's last 2 characters), which nothing has, so the map never had an environment. They get their parent's folder
# like the two above; their parents are in the base client's pack "maps" (c55), so the parent is looked up in the whole
# pack set: pack/Index order, a pack from OUT if it is there, else from BASE (the first listed pack holding a name wins,
# as in the exe). A parent's navgrid.bin is never copied (../navgrid makes the copy's own).
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 .../ycopymaps/build_ycopymaps.py <OUT pack dir> \
#     [<BASE pack dir>]       (BASE default: /opt/metin2/cache/cY/azbase)
#
# clientY.sh: after yfinal, before the verify loop. Idempotent (a second run finds nothing to do).
import json
import os
import sys
import zlib

sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
TEXT = ('.txt', '.msa', '.msm', '.mse', '.mss', '.msenv', '.sub', '.prb', '.prd', '.pre', '.prt', '.py', '.ifl', '.pra')
# (the copy's pack, the copy, its ParentMapName)
COPIES = (('ycrack_maps', 'metin2_map_boss_crack_dawnmist', 'metin2_map_boss_awaken_dawnmist'),
          ('yzaklety_maps', 'metin2_map_dawnmist_dungeon_01', 'metin2_map_boss_awaken_dawnmist'),
          ('ypb_maps', 'metin2_map_boss_awaken_flame', 'metin2_map_n_flame_dungeon_01'),
          ('ypb_maps', 'metin2_map_boss_awaken_snow', 'metin2_map_n_snow_dungeon_01'))
SKIP = ('setting.txt', 'mapproperty.txt', 'navgrid.bin')
PROPERTY = b'ScriptType MapProperty\r\n\r\nMapType "Outdoor"\r\n'


def pack_set(out, base):
    """[(pack, dir)] in pack/Index order (OUT's Index if there, else BASE's): a pack from OUT if it is there, else BASE"""
    dirs = [d for d in (out, base) if d and os.path.isdir(d)]
    ix = next(os.path.join(d, 'Index') for d in dirs if os.path.exists(os.path.join(d, 'Index')))
    lines = [l.strip() for l in open(ix, 'rb').read().decode('latin-1').replace('\r', '').split('\n')]
    res = []
    for p in [lines[i + 1] for i in range(1, len(lines) - 1, 2) if lines[i + 1]]:
        d = next((d for d in dirs if os.path.exists(os.path.join(d, p + '.index'))), None)
        if d:
            res.append((p, d))
    return res


def parent_files(m2pack, rd, packs, parent):
    """{relative name: bytes} of maps/<parent>/ (first listed pack wins per name), the packs it came from"""
    pp = 'maps/%s/' % parent
    files, src = {}, set()
    for p, d in packs:
        mine = [e for e in m2pack.read_index(os.path.join(d, p + '.index'))[2]
                if e['name'].startswith(pp) and e['name'][len(pp):] not in files]
        if mine:
            dat = rd(os.path.join(d, p + '.data'))
            for e in mine:
                files[e['name'][len(pp):]] = m2pack.read_entry(dat, e)
            src.add(p)
    if 'setting.txt' not in files or '000000/height.raw' not in files:
        raise SystemExit('the parent %s is in no listed pack of OUT/BASE' % parent)
    return files, sorted(src)


def main():
    import m2pack
    import packlib
    out = sys.argv[1]
    base = sys.argv[2] if len(sys.argv) > 2 else '/opt/metin2/cache/cY/azbase'
    rd = packlib.rd
    packs = pack_set(out, base)
    parents = {}
    report = {}
    for pack, name, par in COPIES:
        if par not in parents:
            parents[par] = parent_files(m2pack, rd, packs, par)
            report['parent ' + par] = dict(packs=parents[par][1], files=len(parents[par][0]))
    for pack, name, par in COPIES:
        parent = parents[par][0]
        ip, dp = os.path.join(out, pack + '.index'), os.path.join(out, pack + '.data')
        f, v, ents = m2pack.read_index(ip)
        dat = rd(dp)
        have = dict((e['name'], m2pack.read_entry(dat, e)) for e in ents)
        mp = 'maps/%s/' % name
        rep, add = {}, {}
        if have.get(mp + 'mapproperty.txt') != PROPERTY:
            rep[mp + 'mapproperty.txt'] = PROPERTY
        for rel, b in parent.items():
            if rel in SKIP:
                continue
            n = mp + rel
            if n not in have:
                add[n] = (b, 2 if n.endswith(TEXT) else 1)
            elif have[n] != b:
                rep[n] = b
        if not rep and not add:
            report[name] = 'unchanged'
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
        report[name] = dict(pack=pack, added=len(add), replaced=len(rep), entries=len(nw),
                            data_mb=round(len(nd) / 1e6, 2))
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
