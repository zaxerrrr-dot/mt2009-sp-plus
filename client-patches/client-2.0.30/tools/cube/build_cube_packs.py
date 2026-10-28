# -*- coding: utf-8 -*-
# MT2009_PLUS_CUBE_RENEWAL_V1 - the client build's part for the global crafting window (root/uicuberenewal.py,
# root/uiscript/cuberenewalwindow.py, GF's d:/ymir work/ui/making_001.dds and d:/ymir work/ui/game/cube/*.sub, see
# cube_files.py): no new pack. build57.py already puts client-2.0.30/root and client-2.0.30/atlas/d_ into the "root"
# pack, so on the Yohara chain this step finds them there and reports "unchanged"; on a build without them (an older
# build57, another branch) it adds the missing entries to the root pack and replaces a different one. Every entry
# written is read back, the other entries stay byte for byte.
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/cube/build_cube_packs.py <BASE pack dir> <OUT pack dir> [--check]
#
# clientY.sh: after build57.py (it writes OUT's root pack) - e.g. after the kamienie line:
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/cube/build_cube_packs.py $C/azbase \
#     $C/out/pack > $C/cube.json
# and cube/verify_cube_packs.py in the verify loop. Idempotent: a second run gives "unchanged".
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
    import cube_files
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    check = '--check' in sys.argv
    base, out = args[:2]
    rd = packlib.rd
    pack = 'root'
    src = out if os.path.exists(os.path.join(out, pack + '.index')) else base
    f, v, ents = m2pack.read_index(os.path.join(src, pack + '.index'))
    dat = rd(os.path.join(src, pack + '.data'))
    have = dict((e['name'], e) for e in ents)
    rep, new = {}, {}
    for name, (path, ctype) in sorted(cube_files.entries().items()):
        b = cube_files.read(path)
        if name not in have:
            new[name] = (b, ctype)
        elif m2pack.read_entry(dat, have[name]) != b:
            rep[name] = b
    report = {}
    if not rep and not new:
        report[pack] = 'unchanged'
    elif check:
        report[pack] = dict(replace=sorted(rep), add=sorted(new))
    else:
        tmp_i, tmp_d = os.path.join(out, pack + '.index.cube'), os.path.join(out, pack + '.data.cube')
        r = packlib.repack_add_typed(os.path.join(src, pack + '.index'), os.path.join(src, pack + '.data'), rep, new,
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
        for n, b in list(rep.items()) + [(k, b) for k, (b, c) in new.items()]:
            assert got[n] == b, (pack, n)
        for e in ents:
            if e['name'] not in rep:
                assert got[e['name']] == m2pack.read_entry(dat, e), (pack, e['name'])
        report[pack] = dict(old=r[0], added=r[1], replaced=r[2], entries=len(nw), data_mb=round(len(nd) / 1e6, 2),
                            under_zip_limit=len(nd) < ZIP_LIMIT, replaced_names=sorted(rep), added_names=sorted(new))
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
