# -*- coding: utf-8 -*-
# MT2009_PLUS_YOHARA_FINAL_V1 - the LAST builder of the Yohara client chain (yfinal_data.py says what and why):
#   gamedata/atlasinfo.txt  the base client's dead rows under the Yohara maps out (0 overlaps in the whole file);
#   gamedata/mob_proto      every monster's element bits = the server's (zywioly_moby.sql + the *_zywioly.sql files);
#   gamedata/npclist.txt    the tree Metins (8126/8127/8136/8137) on the race mt2009_metin_tree;
#   yfinal_mobs (new pack)  metinstone_east_02..05.dds under monster2 (Metin Szacunku's white model) and the tree
#                           Metin's race (GF's metinstone_16 under its own name), from the GF client; its Index line.
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
TEXT = ('.txt', '.msa', '.msm', '.mse', '.mss', '.msenv', '.sub', '.prb', '.prd', '.pre', '.prt', '.py', '.ifl', '.pra')


def ctype(name):
    return 2 if name.endswith(TEXT) else 1


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
    for n, fn in (('gamedata/atlasinfo.txt', yd.atlasinfo), ('gamedata/mob_proto', yd.mob_proto),
                  ('gamedata/npclist.txt', yd.npclist)):
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

    # the new pack (every name new to BASE and OUT), then its Index line
    np = yd.NEW_PACK
    files = yd.new_pack_files()
    done = [d for d in (base, out) if os.path.exists(os.path.join(d, np + '.index'))]
    have_new = None
    if done:
        f, v, e2 = m2pack.read_index(os.path.join(done[0], np + '.index'))
        d2 = rd(os.path.join(done[0], np + '.data'))
        have_new = dict((e['name'], m2pack.read_entry(d2, e)) for e in e2)
    if have_new == files:
        report[np] = 'in base' if done[0] == base else 'in out'
    else:
        if done and done[0] == base:
            raise SystemExit('%s is in BASE with other content' % np)
        for d in (base, out):
            for fn in sorted(os.listdir(d)):
                if fn.endswith('.index') and fn[:-6] != np:
                    for e in m2pack.read_index(os.path.join(d, fn))[2]:
                        assert e['name'] not in files, (np, e['name'], fn)
        if check:
            report[np] = dict(add=sorted(files))
        else:
            tmp_i, tmp_d = os.path.join(out, np + '.index.yf'), os.path.join(out, np + '.data.yf')
            packlib.repack_add_typed(None, None, {}, dict((k, (b, ctype(k))) for k, b in files.items()), tmp_i, tmp_d,
                                     ents[-1]['raw'])
            os.replace(tmp_i, os.path.join(out, np + '.index'))
            os.replace(tmp_d, os.path.join(out, np + '.data'))
            f, v, nw = m2pack.read_index(os.path.join(out, np + '.index'))
            nd = rd(os.path.join(out, np + '.data'))
            got = dict((e['name'], m2pack.read_entry(nd, e)) for e in nw)
            assert got == files, np
            report[np] = dict(added=len(got), data_mb=round(len(nd) / 1e6, 2))
    if not check:
        ix_path = os.path.join(out, 'Index') if os.path.exists(os.path.join(out, 'Index')) else os.path.join(base, 'Index')
        ix = rd(ix_path)
        lines = [l.strip() for l in ix.replace(b'\r\n', b'\n').split(b'\n')]
        if np.encode() not in lines:
            ix = ix.rstrip(b'\r\n') + b'\n*\n' + np.encode() + b'\n'
        if ix != rd(ix_path) or ix_path != os.path.join(out, 'Index'):
            open(os.path.join(out, 'Index'), 'wb').write(ix)
            report['Index'] = 'written'
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
