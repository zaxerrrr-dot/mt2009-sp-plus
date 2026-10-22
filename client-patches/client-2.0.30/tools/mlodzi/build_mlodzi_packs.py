# -*- coding: utf-8 -*-
# MT2009_PLUS_MLODZI_BOHATEROWIE_V1 - the client build's part for Bronie dla Mlodych Bohaterow (21900-21975):
#   1) a new pack "mlodzi": the 6 weapon models d:/ymir work/item/weapon/21900..21905.gr2 (every tier uses the tier-1
#      model of its kind, tools/mlodzi/mlodzi_items.json "models") from the GF 26.1.11 client and every texture they
#      name (gf28/gfres.gr2_textures: weapon_beginner_01.dds, weapon_choegogeup01_06.dds); a 64-bit GR2 stops the run;
#      a name already in BASE or OUT is not added again (a model there with other content is a collision and stops
#      the run - the item_list lines would show the other model; a texture there is the client's own and is kept);
#   2) its line at the end of pack/Index;
#   3) the existing packs "gamedata" (gamedata/item_list.txt) and "dbdata" (gamedata/item_proto,
#      locale/pl/itemdesc.txt): the 48 weapons (patch_mlodzi_client.py). The 6 icons (root/icon/item/2190K.tga)
#      travel in client-2.0.30/root like every root change.
# Weapons need nothing else in the client: gamedata/item_scale.txt is the sashes' table only (ACCE), the weapon
# model is item_list's 4th column.
# BUILD ORDER - it shares pack/Index, gamedata and dbdata: after every other Yohara step that writes them (after
# ../yhelm100), on the same OUT (a pack already in OUT - an earlier step changed it - is the one patched):
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/mlodzi/build_mlodzi_packs.py <BASE pack dir> <OUT pack dir> [--check]
#
# clientY.sh: after the yhelm100 line,
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/mlodzi/build_mlodzi_packs.py $C/azbase \
#     $C/out/pack > $C/mlodzi.json
# then verify_mlodzi.py on OUT. Every entry written is read back. Idempotent: a second run gives "in out" /
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
GF28 = '/opt/metin2/cache/tcm/gf28'
PACK = 'mlodzi'
TEXT = ('.txt', '.msa', '.msm')
GR2_64 = b'\xe5\x9b\x49\x5e'


def ctype(name):
    return 2 if name.endswith(TEXT) else 1


def gf_path(key):
    return os.path.join(GF, key.replace('d:/', 'd_/', 1))


def model_files():
    """{in-pack name: bytes} of the 6 models, {in-pack name: bytes} of their textures"""
    sys.path.insert(0, GF28)
    import gfres
    import patch_mlodzi_client as pc
    models, textures = {}, {}
    for k in pc.items_json()['models']:
        b = open(gf_path(k), 'rb').read()
        assert b[:4] != GR2_64, ('64-bit GR2', k)
        models[k] = b
        names = gfres.gr2_textures(k, gf_path(k))
        assert k not in gfres.GR2_FAIL, (k, gfres.GR2_FAIL.get(k))
        assert names, ('no texture named', k)
        for t in sorted(names):
            assert t in gfres.GF, ('texture not in the GF client', k, t)
            textures[t] = open(gfres.GF[t], 'rb').read()
    return models, textures


def main():
    import m2pack
    import packlib
    import patch_mlodzi_client as pc
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
        tmp_i, tmp_d = os.path.join(out, pack + '.index.ml1'), os.path.join(out, pack + '.data.ml1')
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

    # 1) the model pack (only the names no other pack has; a model there with other content is a collision)
    models, textures = model_files()
    clash = []
    for k, b in sorted(models.items()):
        if k in allnames:
            d = src_of(allnames[k])
            f, v, ents = m2pack.read_index(os.path.join(d, allnames[k] + '.index'))
            dat = rd(os.path.join(d, allnames[k] + '.data'))
            if [m2pack.read_entry(dat, e) for e in ents if e['name'] == k] != [b]:
                clash.append('%s (pack %s)' % (k, allnames[k]))
    if clash:
        raise SystemExit('model name(s) already in the client with other content: %s' % ', '.join(clash))
    allfiles = dict(models)
    allfiles.update(textures)
    items = dict((k, b) for k, b in allfiles.items() if k not in allnames)
    report['already_in'] = dict((k, allnames[k]) for k in sorted(allfiles) if k in allnames)
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
            report[pack] = write(pack, src, rep, {}, ents, dat)
            report[pack]['replaced_names'] = sorted(rep)
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
