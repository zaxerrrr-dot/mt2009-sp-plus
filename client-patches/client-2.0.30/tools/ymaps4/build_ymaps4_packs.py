# -*- coding: utf-8 -*-
# MT2009_PLUS_YOHARA_MAPS4_V1 - the client build's part for Rozpadlina Dusz (389) and the owner's items of 14 October
# (MT2009_PLUS_YOHARA_ITEMS4_V1):
#   1) the new packs of ymaps4_manifest.json "new_packs" - rozpadlina_map (the map folder, its textureset, terrain
#      textures, msenv, atlas), ymaps4_obj (the map objects' models) and ymaps4_mobs (the races our packs lack) - staged
#      by stage_ymaps4.py under <staging>/add/<pack>/<in-pack path> ("d_/" = "d:/");
#   2) the existing pack "property": the map's object properties added (none of ours replaced);
#   3) their lines at the end of pack/Index;
#   4) the existing packs "gamedata" and "dbdata" (patch_ymaps4_client.py): gamedata/mob_proto - the 20 rows of
#      yohara_maps4.sql with their elements (the stand-in portals 10145/10146 out); gamedata/atlasinfo.txt - the map's
#      row; gamedata/item_list.txt, gamedata/item_proto (dbdata) and locale/pl/itemdesc.txt (dbdata) - the 44 items of
#      yohara_items4.sql (tools/yohara_maps4/yohara_items4.json).
# The map's name on the minimap (localeinfo.py MINIMAP_ZONE_NAME_DICT) and the items' icons (root/icon/item) travel in
# client-2.0.30/root like every root change.
# BUILD ORDER - they share pack/Index, property, gamedata and dbdata: the build's own packs, then ../cape301,
# ../maps302, ../shipdefense, ../port368, ../ymaps, ../ymaps2, ../ymaps3 and then this one, all on the same OUT (a
# pack already in OUT - an earlier step changed it - is the one patched):
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/ymaps4/build_ymaps4_packs.py \
#     <BASE pack dir> <OUT pack dir> <staging dir> [--data <dir>]
#   ... build_ymaps4_packs.py <BASE> <OUT> <staging> --check      # measure only, writes nothing
#
# clientY.sh: after the ymaps3 line,
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/ymaps4/build_ymaps4_packs.py $C/azbase $C/out/pack \
#     /opt/metin2/cache/yohara/ymaps4-staging > $C/ymaps4.json
# then verify_ymaps4.py on OUT (ymaps4/verify_ymaps4.py in the verify loop). --data: a directory with the build's
# patched copies (flat: mob_proto, atlasinfo.txt, npclist.txt, item_list.txt, item_proto, itemdesc.txt) to start from
# instead of the packs' entries. Every entry written is read back; an added name must be new to BASE and to the packs
# already in OUT (stage again when a newer BASE has gained some). Idempotent: a second run gives "in out"/"unchanged".
import json
import os
import re
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, HERE)
TEXT = ('.txt', '.msa', '.msm', '.mse', '.mss', '.msenv', '.sub', '.prb', '.prd', '.pre', '.prt', '.py', '.ifl', '.pra')
ZIP_LIMIT = 29 * 1024 * 1024
def ctype(name):
    return 2 if name.endswith(TEXT) else 1


def main():
    import m2pack
    import packlib
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    check = '--check' in sys.argv
    data_from = sys.argv[sys.argv.index('--data') + 1] if '--data' in sys.argv else None
    if data_from:
        args.remove(data_from)
    base, out, staging = args[:3]
    import patch_ymaps4_client as pc
    man = json.load(open(os.path.join(HERE, 'ymaps4_manifest.json'), encoding='utf-8'))
    new_packs = man['new_packs']
    rd = packlib.rd
    allnames = {}
    for d in (base, out):
        if not os.path.isdir(d):
            continue
        for p in sorted(f[:-6] for f in os.listdir(d) if f.endswith('.index')):
            if p in new_packs:
                continue
            for e in m2pack.read_index(os.path.join(d, p + '.index'))[2]:
                allnames.setdefault(e['name'], p)
    tmpl = m2pack.read_index(os.path.join(base, 'az_mobs.index'))[2][-1]['raw']
    replace_ok = set(man.get('replace', []))

    def staged(pack, k):
        return rd(os.path.join(staging, 'add', pack, k.replace('d:/', 'd_/', 1)))

    def src_of(pack):
        if os.path.exists(os.path.join(out, pack + '.index')):
            return out
        return base

    report = {}

    def write(pack, src, rep, add, ents, dat):
        tmp_i, tmp_d = os.path.join(out, pack + '.index.ym2'), os.path.join(out, pack + '.data.ym2')
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

    # 1) the new packs
    for pack in new_packs:
        keys = [e['name'] for e in man['packs'].get(pack, [])]
        items = dict((k, staged(pack, k)) for k in keys)
        done = [d for d in (base, out) if os.path.exists(os.path.join(d, pack + '.index'))]
        if done:
            f, v, ents = m2pack.read_index(os.path.join(done[0], pack + '.index'))
            dat = rd(os.path.join(done[0], pack + '.data'))
            have = dict((e['name'], m2pack.read_entry(dat, e)) for e in ents)
            if have != items:
                if done[0] == out and not check:
                    os.remove(os.path.join(out, pack + '.index'))
                    os.remove(os.path.join(out, pack + '.data'))
                else:
                    raise SystemExit('%s is in BASE with other content - stage again or drop it from BASE' % pack)
            else:
                report[pack] = 'in base' if done[0] == base else 'in out'
                continue
        for k in keys:
            assert k == k.lower() and k not in allnames, (pack, k, allnames.get(k))
        if check:
            size = sum(len(m2pack.encode_entry(b, ctype(k))) for k, b in items.items())
            report[pack] = dict(files=len(items), raw_mb=round(sum(len(b) for b in items.values()) / 1e6, 2),
                                data_mb=round(size / 1e6, 2), under_zip_limit=size < ZIP_LIMIT)
            continue
        report[pack] = write(pack, None, {}, dict((k, (b, ctype(k))) for k, b in items.items()), [], b'')
        assert report[pack]['under_zip_limit'], (pack, report[pack])

    # 2) property: new names added, the listed ones replaced when they differ
    for pack in ('property',):
        src = src_of(pack)
        f, v, ents = m2pack.read_index(os.path.join(src, pack + '.index'))
        dat = rd(os.path.join(src, pack + '.data'))
        have = dict((e['name'], e) for e in ents)
        rep, add = {}, {}
        for e in man['packs'].get(pack, []):
            k = e['name']
            b = staged(pack, k)
            if k in have:
                if m2pack.read_entry(dat, have[k]) != b:
                    assert k in replace_ok, (pack, k, 'would replace an entry not listed in "replace"')
                    rep[k] = b
            else:
                assert k == k.lower() and k not in allnames, (pack, k, allnames.get(k))
                add[k] = (b, ctype(k))
        if not rep and not add:
            report[pack] = 'unchanged'
        elif check:
            report[pack] = dict(add=len(add), replace=sorted(rep))
        else:
            report[pack] = write(pack, src, rep, add, ents, dat)
            report[pack]['replaced_names'] = sorted(rep)

    # 3) Index: the new packs at the end (after the build's own lines and cape301's)
    if not check:
        ix_path = os.path.join(out, 'Index') if os.path.exists(os.path.join(out, 'Index')) else os.path.join(base, 'Index')
        ix = rd(ix_path)
        lines = [l.strip() for l in ix.replace(b'\r\n', b'\n').split(b'\n')]
        for pack in new_packs:
            if pack.encode() not in lines and (os.path.exists(os.path.join(out, pack + '.index')) or
                                               os.path.exists(os.path.join(base, pack + '.index'))):
                ix = ix.rstrip(b'\r\n') + b'\n*\n' + pack.encode() + b'\n'
        if ix != rd(ix_path) or ix_path != os.path.join(out, 'Index'):
            open(os.path.join(out, 'Index'), 'wb').write(ix)
            report['Index'] = 'written'
    # 4) gamedata / dbdata (patch_ymaps4_client.py): mob_proto, atlasinfo, npclist rows (append only); the items
    jobs = {'gamedata': [('gamedata/mob_proto', pc.mob_proto), ('gamedata/atlasinfo.txt', pc.atlasinfo),
                         ('gamedata/npclist.txt', pc.npclist), ('gamedata/item_list.txt', pc.item_list)],
            'dbdata': [('gamedata/item_proto', pc.item_proto), ('locale/pl/itemdesc.txt', pc.itemdesc)]}
    for pack, files in jobs.items():
        src = src_of(pack)
        f, v, ents = m2pack.read_index(os.path.join(src, pack + '.index'))
        dat = rd(os.path.join(src, pack + '.data'))
        have = dict((e['name'], e) for e in ents)
        rep = {}
        for n, fn in files:
            b = m2pack.read_entry(dat, have[n])
            if data_from:
                for cand in (os.path.join(data_from, os.path.basename(n)), os.path.join(data_from, n)):
                    if os.path.exists(cand):
                        b = rd(cand)
                        break
            nb, changed = fn(b)
            if nb != m2pack.read_entry(dat, have[n]):
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
