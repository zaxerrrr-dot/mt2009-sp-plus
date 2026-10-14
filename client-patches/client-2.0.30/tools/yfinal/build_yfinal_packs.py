# -*- coding: utf-8 -*-
# MT2009_PLUS_YOHARA_FINAL_V1 - the LAST builder of the Yohara client chain (yfinal_data.py says what and why):
#   gamedata/atlasinfo.txt  the base client's dead rows under the Yohara maps out (0 overlaps in the whole file);
#   gamedata/mob_proto      every monster's element bits = the server's (zywioly_moby.sql + the *_zywioly.sql files).
# Runs on the same OUT after every other builder (it patches the gamedata pack an earlier step left in OUT, else
# BASE's) - clientY.sh, after the yskill9 line (and after any builder added later):
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/yfinal/build_yfinal_packs.py $C/azbase $C/out/pack \
#     > $C/yfinal.json
# then yfinal/verify_yfinal.py in the verify loop. --check measures only. Idempotent: a second run gives "unchanged".
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
    import yfinal_data as yd
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    check = '--check' in sys.argv
    base, out = args[:2]
    rd = packlib.rd
    pack = 'gamedata'
    src = out if os.path.exists(os.path.join(out, pack + '.index')) else base
    f, v, ents = m2pack.read_index(os.path.join(src, pack + '.index'))
    dat = rd(os.path.join(src, pack + '.data'))
    have = dict((e['name'], e) for e in ents)
    report = {}
    rep = {}
    for n, fn in (('gamedata/atlasinfo.txt', yd.atlasinfo), ('gamedata/mob_proto', yd.mob_proto)):
        b = m2pack.read_entry(dat, have[n])
        nb, changed = fn(b)
        report[n] = changed
        if nb != b:
            rep[n] = nb
    bad = yd.overlaps((rep.get('gamedata/atlasinfo.txt') or m2pack.read_entry(dat, have['gamedata/atlasinfo.txt']))
                      .decode('cp1250'))
    if bad:
        raise SystemExit('yfinal: atlasinfo rows still overlap: %s' % bad)
    if not rep:
        report[pack] = 'unchanged'
    elif check:
        report[pack] = dict(replace=sorted(rep))
    else:
        tmp_i, tmp_d = os.path.join(out, pack + '.index.yf'), os.path.join(out, pack + '.data.yf')
        r = packlib.repack_add_typed(os.path.join(src, pack + '.index'), os.path.join(src, pack + '.data'), rep, {},
                                     tmp_i, tmp_d, ents[-1]['raw'])
        os.replace(tmp_i, os.path.join(out, pack + '.index'))
        os.replace(tmp_d, os.path.join(out, pack + '.data'))
        f, v, nw = m2pack.read_index(os.path.join(out, pack + '.index'))
        nd = rd(os.path.join(out, pack + '.data'))
        names = [e['name'] for e in nw]
        assert len(set(names)) == len(names), pack
        for e in nw:
            assert zlib.crc32(nd[e['pos']:e['pos'] + e['size']]) & 0xffffffff == e['dcrc'], (pack, e['name'])
            got = m2pack.read_entry(nd, e)
            assert got == (rep[e['name']] if e['name'] in rep else m2pack.read_entry(dat, have[e['name']])), e['name']
        report[pack] = dict(old=r[0], added=r[1], replaced=r[2], entries=len(nw), data_mb=round(len(nd) / 1e6, 2),
                            under_zip_limit=len(nd) < ZIP_LIMIT, replaced_names=sorted(rep))
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
