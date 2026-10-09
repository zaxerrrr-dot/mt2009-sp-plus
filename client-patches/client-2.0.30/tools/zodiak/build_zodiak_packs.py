# -*- coding: utf-8 -*-
# MT2009_PLUS_ZODIAC_V1 - the client build's part for Swiatynia Zodiaku (map 358, metin2_12zi_stage; package
# nowy-system 0.35.0, "Autor: Digi Rasta"):
#   1) the new packs zodiak_maps (the temple's objects, effects, environments, terrain, textureset, UI pictures,
#      item icons, the atlas), zodiak_mobs and zodiak_mobs2 (the Zodiac races 2600-2937 / NPC 20438-20464 with their
#      sounds and effects, split by race; the Zodiac weapons' models and the armour shape 25), staged by stage_zodiak.py under
#      <staging>/add/<pack>/<in-pack path> ("d_/" = "d:/"), listed in zodiak_manifest.json - the package's pack
#      "nowy_system_zodiak" split in three (each under the 29 MB zip limit) and completed from GF;
#   2) the map folder into the existing pack "maps" and the used map objects' properties into "property" (the exe
#      loads map objects only from pack/property) - old entries unchanged;
#   3) their lines at the end of pack/Index;
#   4) the rows (patch_zodiak_client.py, append only): gamedata - npclist.txt (aliases + vnums), atlasinfo.txt,
#      item_list.txt, mob_proto; dbdata - gamedata/item_proto, locale/pl/itemdesc.txt; locale -
#      locale/pl/locale_game.txt, locale/pl/locale_interface.txt.
# The root scripts (ui12zi.py, uiscript/bead.py, 12floorinfo.py, 12zirewardwindow.py and the hooks in game.py,
# interfacemodule.py, ...) travel in client-2.0.30/root like every root change (build57.py's root step).
# For the builder of the next client: run it after the build's own packs, build_azcostume_packs.py and
# build_atlantis_packs.py, on the same OUT (a maps/property/gamedata/dbdata/locale pack already in OUT - the build
# changed it - is the one patched):
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/zodiak/build_zodiak_packs.py \
#     <BASE pack dir> <OUT pack dir> <staging dir> [--data <dir>]
#   ... build_zodiak_packs.py <BASE> - <staging> --check      # measure only, writes nothing
#
# --data: a directory with the build's patched copies (flat: item_list.txt, item_proto, itemdesc.txt, mob_proto,
# as client59.sh's c59/data) to start from instead of the pack's entry. Every entry written is read back; an added
# name must be new to the whole BASE. Idempotent: a BASE that has it all gives "unchanged"/"in base".
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
NEW_PACKS = ('zodiak_maps', 'zodiak_mobs', 'zodiak_mobs2')
OLD_PACKS = ('maps', 'property')


def ctype(name):
    return 2 if name.endswith(TEXT) else 1


def main():
    import m2pack
    import packlib
    import patch_zodiak_client as pc
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    check = '--check' in sys.argv
    data_from = sys.argv[sys.argv.index('--data') + 1] if '--data' in sys.argv else None
    if data_from:
        args.remove(data_from)
    base, out, staging = args[:3]
    man = json.load(open(os.path.join(HERE, 'zodiak_manifest.json'), encoding='utf-8'))
    rd = packlib.rd
    allnames = {}
    for p in sorted(f[:-6] for f in os.listdir(base) if f.endswith('.index')):
        for e in m2pack.read_index(os.path.join(base, p + '.index'))[2]:
            allnames.setdefault(e['name'], p)
    tmpl = m2pack.read_index(os.path.join(base, 'az_mobs.index'))[2][-1]['raw']

    def staged(pack, k):
        return rd(os.path.join(staging, 'add', pack, k.replace('d:/', 'd_/', 1)))

    def src_of(pack):
        if not check and os.path.exists(os.path.join(out, pack + '.index')):
            return out
        return base

    report = {}
    expect = {}

    def write(pack, src, rep, add, ents, dat):
        tmp_i, tmp_d = os.path.join(out, pack + '.index.zd'), os.path.join(out, pack + '.data.zd')
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
    for pack in NEW_PACKS:
        keys = [e['name'] for e in man['packs'].get(pack, [])]
        items = dict((k, staged(pack, k)) for k in keys)
        if os.path.exists(os.path.join(base, pack + '.index')):
            f, v, ents = m2pack.read_index(os.path.join(base, pack + '.index'))
            dat = rd(os.path.join(base, pack + '.data'))
            have = dict((e['name'], m2pack.read_entry(dat, e)) for e in ents)
            if have != items:
                raise SystemExit('%s is in BASE with other content - stage again or drop it from BASE' % pack)
            report[pack] = 'in base'
            continue
        for k in keys:
            assert k == k.lower() and k not in allnames, (pack, k, allnames.get(k))
        if check:
            size = sum(len(m2pack.encode_entry(b, ctype(k))) for k, b in items.items())
            report[pack] = dict(files=len(items), raw_mb=round(sum(len(b) for b in items.values()) / 1e6, 2),
                                data_mb=round(size / 1e6, 2), under_zip_limit=size < ZIP_LIMIT)
            continue
        report[pack] = write(pack, None, {}, dict((k, (b, ctype(k))) for k, b in items.items()), [], b'')

    # 2) maps and property: new names added, ours replaced when they differ
    for pack in OLD_PACKS:
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
                    rep[k] = b
            else:
                assert k == k.lower() and k not in allnames, (pack, k, allnames.get(k))
                add[k] = (b, ctype(k))
        if not rep and not add:
            report[pack] = 'unchanged'
        elif check:
            report[pack] = dict(add=len(add), replace=len(rep),
                                add_mb=round(sum(len(m2pack.encode_entry(b, c)) for b, c in add.values()) / 1e6, 2))
        else:
            report[pack] = write(pack, src, rep, add, ents, dat)

    # 3) Index: the new packs at the end (after the build's own and the costume packs' lines)
    if not check:
        ix_path = os.path.join(out, 'Index') if os.path.exists(os.path.join(out, 'Index')) else os.path.join(base, 'Index')
        ix = rd(ix_path)
        lines = [l.strip() for l in ix.replace(b'\r\n', b'\n').split(b'\n')]
        for pack in NEW_PACKS:
            if pack.encode() not in lines and (os.path.exists(os.path.join(out, pack + '.index')) or
                                               os.path.exists(os.path.join(base, pack + '.index'))):
                ix = ix.rstrip(b'\r\n') + b'\n*\n' + pack.encode() + b'\n'
        if ix != rd(ix_path) or ix_path != os.path.join(out, 'Index'):
            open(os.path.join(out, 'Index'), 'wb').write(ix)
            report['Index'] = 'written'

    # 4) the rows
    jobs = {'gamedata': [('gamedata/npclist.txt', pc.npclist), ('gamedata/atlasinfo.txt', pc.atlasinfo),
                         ('gamedata/item_list.txt', pc.item_list), ('gamedata/mob_proto', pc.mob_proto)],
            'dbdata': [('gamedata/item_proto', pc.item_proto), ('locale/pl/itemdesc.txt', pc.itemdesc)],
            'locale': [('locale/pl/locale_game.txt', pc.locale_game),
                       ('locale/pl/locale_interface.txt', pc.locale_interface)]}
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
