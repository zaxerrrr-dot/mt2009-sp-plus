# -*- coding: utf-8 -*-
# MT2009_PLUS_HALLOWEEN_V1 (Autor: Owsap - the event, event_halloween_hair) - the Yohara (3.x) client build's part of
# the Halloween event, in the shape of the other Yohara steps (../ishop5, ../mlodzi): one call on the chain's
# BASE / OUT that
#   * builds the pack "halloween" (Jack Pumpkin's model, build_halloween_pack.py next to this file) and lists it in
#     OUT's Index;
#   * patches the existing packs "gamedata" (gamedata/item_list.txt: a line per vnum of halloween_client.json
#     "items_present" the file lacks) and "dbdata" (locale/pl/itemdesc.txt: the twelve descriptions of
#     halloween_client.json) - a pack already in OUT (an earlier step changed it) is the one patched, so the earlier
#     steps' lines stay.
# The 2.x chain (client237.sh) runs patch_halloween_client.py on the data dir and build_halloween_pack.py instead.
# BUILD ORDER - it shares gamedata and dbdata: after every other Yohara step that writes them (after ../ishop5).
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/halloween/build_yhalloween_packs.py <BASE pack dir> <OUT pack dir> [--check]
#
# clientY.sh: after the ishop5 line,
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/halloween/build_yhalloween_packs.py $C/azbase \
#     $C/out/pack > $C/halloween.json
# then verify_yhalloween.py on OUT. Every entry written is read back. Idempotent: a second run gives "unchanged".
import io
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
    import build_halloween_pack as bp
    import patch_halloween_client as pc
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if len(args) != 2:
        raise SystemExit('usage: build_yhalloween_packs.py <BASE pack dir> <OUT pack dir> [--check]')
    check = '--check' in sys.argv
    rd = packlib.rd
    base, out = args
    report = {}

    # the pack "halloween" and its Index line - build_halloween_pack.py's own run, its report kept
    saved, real = sys.argv, sys.stdout
    sys.argv = [bp.__file__, base, out] + (['--check'] if check else [])
    sys.stdout = io.StringIO()
    try:
        bp.main()
        report['halloween_pack'] = json.loads(sys.stdout.getvalue())
    finally:
        sys.argv, sys.stdout = saved, real

    def src_of(pack):
        return out if os.path.exists(os.path.join(out, pack + '.index')) else base

    def write(pack, src, rep, ents, dat):
        tmp_i, tmp_d = os.path.join(out, pack + '.index.yhw'), os.path.join(out, pack + '.data.yhw')
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

    jobs = {'gamedata': [('gamedata/item_list.txt', pc.item_list)],
            'dbdata': [('locale/pl/itemdesc.txt', pc.itemdesc)]}
    for pack, files in sorted(jobs.items()):
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
