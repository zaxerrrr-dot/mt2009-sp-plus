# -*- coding: utf-8 -*-
# MT2009_PLUS_HELM100_V1 - the client build's part for the level-100 helmets and Straznik Smokow Jaharr:
#   1) a new pack "yhelm100": Jaharr's race model d:/ymir work/npc/old_magic_m/ (old_magic_m.gr2, old_magic_m2.msm with
#      its skin old_magic_m2.dds - npclist 20421 old_magic_M2 -> folder old_magic_M - and the wait/walk/run/dead
#      motions) from the GF 26.1.11 client, the 17 files gf28/gfres.closure gives for the folder (its
#      old_magic_m.dds reference is the base model's default skin, GF has no such file either; the race swaps it for
#      old_magic_m2.dds); a name already in BASE or OUT is not added again (the base client's npc packs have no
#      listing - when they hold the folder, the pack only repeats it);
#   2) its line at the end of pack/Index;
#   3) the existing packs "gamedata" (gamedata/item_list.txt, gamedata/mob_proto, gamedata/npclist.txt) and "dbdata"
#      (gamedata/item_proto, locale/pl/itemdesc.txt): the 84 items, Jaharr's mob row and his npclist rows
#      (patch_yhelm100_client.py; tools/yhelm100/yhelm100_items.json). The item icons (root/icon/item) travel in
#      client-2.0.30/root like every root change.
# BUILD ORDER - it shares pack/Index, gamedata and dbdata: after every other Yohara step (after ../ygloves, before
# ../yfinal), on the same OUT (a pack already in OUT - an earlier step changed it - is the one patched):
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/yhelm100/build_yhelm100_packs.py <BASE pack dir> <OUT pack dir> [--check]
#
# clientY.sh: after the ygloves line,
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/yhelm100/build_yhelm100_packs.py $C/azbase \
#     $C/out/pack > $C/yhelm100.json
# then verify_yhelm100.py on OUT. Every entry written is read back. Idempotent: a second run gives "in out" /
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
GF = '/opt/metin2/cache/gf/Gameforge_26.1.11/_client'
PACK = 'yhelm100'
MODEL_DIR = 'd:/ymir work/npc/old_magic_m/'
MODEL_FILES = ('dead.gr2', 'dead.msa', 'motlist.txt', 'old_magic_m.gr2', 'old_magic_m.msm', 'old_magic_m1.dds',
               'old_magic_m1.msm', 'old_magic_m2.dds', 'old_magic_m2.msm', 'run.gr2', 'run.msa', 'wait.gr2',
               'wait.msa', 'wait1.gr2', 'wait1.msa', 'walk.gr2', 'walk.msa')
TEXT = ('.txt', '.msa', '.msm')
GR2_64 = b'\xe5\x9b\x49\x5e'


def ctype(name):
    return 2 if name.endswith(TEXT) else 1


def model_files():
    out = {}
    for f in MODEL_FILES:
        k = MODEL_DIR + f
        src = os.path.join(GF, k.replace('d:/', 'd_/', 1))
        b = open(src, 'rb').read()
        assert not (f.endswith('.gr2') and b[:4] == GR2_64), ('64-bit GR2', k)
        out[k] = b
    return out


def main():
    import m2pack
    import packlib
    import patch_yhelm100_client as pc
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    check = '--check' in sys.argv
    base, out = args[:2]
    rd = packlib.rd
    report = {}
    allnames = {}
    for d in (base, out):
        for p in sorted(f[:-6] for f in os.listdir(d) if f.endswith('.index')):
            if p == PACK:
                continue
            for e in m2pack.read_index(os.path.join(d, p + '.index'))[2]:
                allnames.setdefault(e['name'], p)
    tmpl = m2pack.read_index(os.path.join(base, 'az_mobs.index'))[2][-1]['raw']

    def src_of(pack):
        return out if os.path.exists(os.path.join(out, pack + '.index')) else base

    def write(pack, src, rep, add, ents, dat):
        tmp_i, tmp_d = os.path.join(out, pack + '.index.yh1'), os.path.join(out, pack + '.data.yh1')
        exists = src is not None
        r = packlib.repack_add_typed(os.path.join(src, pack + '.index') if exists else None,
                                     os.path.join(src, pack + '.data') if exists else None, rep, add, tmp_i, tmp_d,
                                     ents[-1]['raw'] if ents else tmpl)
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
        for n, b in list(rep.items()) + [(k, b) for k, (b, c) in add.items()]:
            assert got[n] == b, (pack, n)
        for e in ents:
            if e['name'] not in rep:
                assert got[e['name']] == m2pack.read_entry(dat, e), (pack, e['name'])
        return dict(old=r[0], added=r[1], replaced=r[2], entries=len(nw), data_mb=round(len(nd) / 1e6, 2),
                    under_zip_limit=len(nd) < ZIP_LIMIT)

    # 1) the model pack (only the names no other pack has)
    items = dict((k, b) for k, b in model_files().items() if k not in allnames)
    report['model_already_in'] = sorted(set(allnames[k] for k in model_files() if k in allnames))
    done = [d for d in (base, out) if os.path.exists(os.path.join(d, PACK + '.index'))]
    if done:
        f, v, ents = m2pack.read_index(os.path.join(done[0], PACK + '.index'))
        dat = rd(os.path.join(done[0], PACK + '.data'))
        have = dict((e['name'], m2pack.read_entry(dat, e)) for e in ents)
        if have == items:
            report[PACK] = 'in base' if done[0] == base else 'in out'
            items = None
        elif done[0] == out and not check:
            os.remove(os.path.join(out, PACK + '.index'))
            os.remove(os.path.join(out, PACK + '.data'))
        else:
            raise SystemExit('%s is in BASE with other content - drop it from BASE' % PACK)
    if items is not None:
        if not items:
            report[PACK] = 'not needed (every file is in another pack)'
        elif check:
            report[PACK] = dict(files=len(items), raw_mb=round(sum(len(b) for b in items.values()) / 1e6, 2))
        else:
            report[PACK] = write(PACK, None, {}, dict((k, (b, ctype(k))) for k, b in items.items()), [], b'')
            assert report[PACK]['under_zip_limit'], report[PACK]

    # 2) Index: the new pack at the end
    if not check and (os.path.exists(os.path.join(out, PACK + '.index')) or
                      os.path.exists(os.path.join(base, PACK + '.index'))):
        ix_path = os.path.join(out, 'Index') if os.path.exists(os.path.join(out, 'Index')) else os.path.join(base, 'Index')
        ix = rd(ix_path)
        lines = [l.strip() for l in ix.replace(b'\r\n', b'\n').split(b'\n')]
        if PACK.encode() not in lines:
            ix = ix.rstrip(b'\r\n') + b'\n*\n' + PACK.encode() + b'\n'
        if ix != rd(ix_path) or ix_path != os.path.join(out, 'Index'):
            open(os.path.join(out, 'Index'), 'wb').write(ix)
            report['Index'] = 'written'

    # 3) gamedata / dbdata
    jobs = {'gamedata': [('gamedata/item_list.txt', pc.item_list), ('gamedata/mob_proto', pc.mob_proto),
                         ('gamedata/npclist.txt', pc.npclist)],
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
            report[pack] = write(pack, src, rep, {}, ents, dat)
            report[pack]['replaced_names'] = sorted(rep)
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
