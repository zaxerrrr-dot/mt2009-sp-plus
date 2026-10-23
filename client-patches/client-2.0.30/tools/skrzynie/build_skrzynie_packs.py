# -*- coding: utf-8 -*-
# MT2009_PLUS_SKRZYNIE_UCZNIA_WIKI_V1 - the client build's part for the level chests' items (patch_skrzynie_client.py):
# the existing packs "gamedata" (gamedata/item_list.txt, gamedata/mob_proto) and "dbdata" (gamedata/item_proto,
# locale/pl/itemdesc.txt). No new pack: every icon is in the client already or travels in client-2.0.30/root
# (56000.tga, 51639.tga), the Appaloosa's model (pony/horse_normal02) is in the client.
# BUILD ORDER - it shares gamedata and dbdata: after every other Yohara step that writes them (after ../mlodzi), on
# the same OUT (a pack already in OUT - an earlier step changed it - is the one patched):
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/skrzynie/build_skrzynie_packs.py <BASE pack dir> <OUT pack dir> [--check]
#
# clientY.sh: after the mlodzi line,
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/skrzynie/build_skrzynie_packs.py $C/azbase \
#     $C/out/pack > $C/skrzynie.json
# Every entry written is read back. Idempotent: a second run gives "unchanged". --verify OUT: only checks that OUT
# has every record / line (exit 1 if not).
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
    import patch_skrzynie_client as pc
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    check = '--check' in sys.argv
    rd = packlib.rd
    if '--verify' in sys.argv:
        out = args[0]
        bad = []
        for pack, n in (('gamedata', 'gamedata/item_list.txt'), ('gamedata', 'gamedata/mob_proto'),
                        ('dbdata', 'gamedata/item_proto'), ('dbdata', 'locale/pl/itemdesc.txt')):
            ents = dict((e['name'], e) for e in m2pack.read_index(os.path.join(out, pack + '.index'))[2])
            b = m2pack.read_entry(rd(os.path.join(out, pack + '.data')), ents[n])
            if pc.JOBS[n](b)[1]:
                bad.append(n)
        print(json.dumps(dict(verify='bad' if bad else 'ok', missing=bad)))
        sys.exit(1 if bad else 0)
    base, out = args[:2]
    report = {}

    def src_of(pack):
        return out if os.path.exists(os.path.join(out, pack + '.index')) else base

    def write(pack, src, rep, ents, dat):
        tmp_i, tmp_d = os.path.join(out, pack + '.index.sk1'), os.path.join(out, pack + '.data.sk1')
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
            assert e['fcrc'] == zlib.crc32(e['name'].encode('cp1252')) & 0xffffffff, (pack, e['name'])
            got[e['name']] = m2pack.read_entry(nd, e)
        for n, b in rep.items():
            assert got[n] == b, (pack, n)
        for e in ents:
            if e['name'] not in rep:
                assert got[e['name']] == m2pack.read_entry(dat, e), (pack, e['name'])
        return dict(old=r[0], added=r[1], replaced=r[2], entries=len(nw), data_mb=round(len(nd) / 1e6, 2),
                    under_zip_limit=len(nd) < ZIP_LIMIT)

    jobs = {'gamedata': ['gamedata/item_list.txt', 'gamedata/mob_proto'],
            'dbdata': ['gamedata/item_proto', 'locale/pl/itemdesc.txt']}
    for pack, files in sorted(jobs.items()):
        src = src_of(pack)
        f, v, ents = m2pack.read_index(os.path.join(src, pack + '.index'))
        dat = rd(os.path.join(src, pack + '.data'))
        have = dict((e['name'], e) for e in ents)
        rep = {}
        for n in files:
            b = m2pack.read_entry(dat, have[n])
            nb, changed = pc.JOBS[n](b)
            if nb != b:
                rep[n] = nb
                report.setdefault('changed', {})[n] = changed
        if not rep:
            report[pack] = 'unchanged'
        elif check:
            report[pack] = dict(replace=sorted(rep))
        else:
            report[pack] = write(pack, src, rep, ents, dat)
            report[pack]['replaced_names'] = sorted(rep)
            assert report[pack]['under_zip_limit'], report[pack]
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
