# -*- coding: utf-8 -*-
# MT2009_PLUS_KAWUCO_V1 - Kawuco's look (20413, the boots NPC of Przyladek Smoczego Ognia): the client's
# gamedata/npclist.txt draws him as the race japanese_pirate_2 ("20413 japanese_pirate_2" and the race line
# "0 japanese_pirate_2 japanese_pirate" are in it already), whose model reads
#   d:/ymir work/monster2/japanese_pirate/japanese_pirate_2.msm  (the pirate's .gr2 with its own skin) and
#   d:/ymir work/monster2/japanese_pirate/japanese_pirate_2.dds  (that skin, DXT1)
# with the motions of the folder (Pirat 5001/5004 and Zodiac's 2736 already use japanese_pirate's model and motions -
# in the base client's monster2 pack, which has no listing on vps1). This puts the two files of the GF 26.1.11 client
# into a new pack, kawuco_mobs, and its Index line; if the base pack has them too, one shadows the other with the
# same race (the stage_zodiak.py rule). Run on the same OUT as the other builders, before yfinal (clientY.sh):
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/kawuco/build_kawuco_pack.py $C/azbase $C/out/pack \
#     > $C/kawuco.json
# The name over his head is gamedata/mob_proto's (patch_kawuco_client.py, in the data step). --check measures only.
# Idempotent: a second run gives "in out".
import json
import os
import sys

sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
GF = '/opt/metin2/cache/gf/Gameforge_26.1.11/_client/d_/'
NEW_PACK = 'kawuco_mobs'
FOLDER = 'd:/ymir work/monster2/japanese_pirate/'
FILES = ('japanese_pirate_2.msm', 'japanese_pirate_2.dds')
TEXT = ('.txt', '.msa', '.msm', '.mse', '.mss', '.msenv', '.sub', '.prb', '.prd', '.pre', '.prt', '.py', '.ifl', '.pra')


def ctype(name):
    return 2 if name.endswith(TEXT) else 1


def new_pack_files():
    out = {}
    for n in FILES:
        k = FOLDER + n
        out[k] = open(GF + k[len('d:/'):], 'rb').read()
    msm = out[FOLDER + 'japanese_pirate_2.msm'].decode('latin-1').lower()
    assert 'japanese_pirate_2.dds' in msm and 'japanese_pirate.gr2' in msm, 'GF japanese_pirate_2.msm changed'
    assert out[FOLDER + 'japanese_pirate_2.dds'][:4] == b'DDS ', 'not a dds'
    return out


def main():
    import m2pack
    import packlib
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    check = '--check' in sys.argv
    base, out = args[:2]
    rd = packlib.rd
    report = {}
    src = out if os.path.exists(os.path.join(out, 'gamedata.index')) else base
    f, v, gents = m2pack.read_index(os.path.join(src, 'gamedata.index'))
    gdat = rd(os.path.join(src, 'gamedata.data'))
    npcl = m2pack.read_entry(gdat, [e for e in gents if e['name'] == 'gamedata/npclist.txt'][0]).decode('cp1250')
    rows = set(tuple(l.split()) for l in npcl.replace('\r', '').split('\n') if l.strip())
    for want in (('20413', 'japanese_pirate_2'), ('0', 'japanese_pirate_2', 'japanese_pirate')):
        if want not in rows:
            raise SystemExit('kawuco: gamedata/npclist.txt has no line %s' % ' '.join(want))
    report['npclist'] = 'has 20413 japanese_pirate_2'

    np = NEW_PACK
    files = new_pack_files()
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
            tmp_i, tmp_d = os.path.join(out, np + '.index.kw'), os.path.join(out, np + '.data.kw')
            packlib.repack_add_typed(None, None, {}, dict((k, (b, ctype(k))) for k, b in files.items()), tmp_i, tmp_d,
                                     gents[-1]['raw'])
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
