# -*- coding: utf-8 -*-
# MT2009_PLUS_CAPE301_V1 - the client build's part for Przyladek Smoczego Ognia (map 301, Metin2_map_CapeDragonHead):
#   1) the new packs cape_map (the map folder, its textureset, terrain textures, msenv, atlas), cape_obj (the map
#      objects' models, trees, effects) and cape_mobs (the races of map 301 our packs lack: the bosses 3090/3091/
#      3290/3291/3590, the Cape NPCs 20378/20380-20383 incl. 9009's sailor, ...), staged by stage_cape301.py under
#      <staging>/add/<pack>/<in-pack path> ("d_/" = "d:/"), listed in cape301_manifest.json;
#   2) the existing pack "property": ships_brokenbody00.prb replaced by GF's (ours names the developer's path
#      d:/project/metin2/data/..., same CRC 1092342088) - old entries otherwise unchanged;
#   3) their lines at the end of pack/Index.
# No gamedata row changes: atlasinfo.txt ("Metin2_map_CapeDragonHead 1024000 1664000 6 6"), npclist.txt and
# mob_proto of client 2.0.64 already have the map and all 55 vnums it spawns; locale_game.txt has MAP_CAPE.
# For the builder of the next client: run it after the build's own packs, on the same OUT (a property pack already
# in OUT - the build changed it - is the one patched):
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/cape301/build_cape301_packs.py \
#     <BASE pack dir> <OUT pack dir> <staging dir>
#   ... build_cape301_packs.py <BASE> - <staging> --check      # measure only, writes nothing
#
# client61.sh-style builds: after the razgate line,
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/cape301/build_cape301_packs.py $C/azbase $C/out/pack \
#     /opt/metin2/cache/yohara/cape301-staging > $C/cape.json
# then verify_cape301.py on a pack dir holding the result (OUT; the BASE listing comes from c58.lst).
# Every entry written is read back; an added name must be new to the whole BASE (when a newer BASE has gained some
# of the staged names, stage again: ../atlantis/dump_base.py <BASE> /opt/metin2/cache/yohara/cape301-work, then
# stage_cape301.py). Idempotent: a BASE that has it all gives "unchanged"/"in base".
import json
import os
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
TEXT = ('.txt', '.msa', '.msm', '.mse', '.mss', '.msenv', '.sub', '.prb', '.prd', '.pre', '.prt', '.py', '.ifl', '.pra')
ZIP_LIMIT = 29 * 1024 * 1024
NEW_PACKS = ('cape_map', 'cape_obj', 'cape_mobs')
OLD_PACKS = ('property',)


def ctype(name):
    return 2 if name.endswith(TEXT) else 1


def main():
    import m2pack
    import packlib
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    check = '--check' in sys.argv
    base, out, staging = args[:3]
    man = json.load(open(os.path.join(HERE, 'cape301_manifest.json'), encoding='utf-8'))
    rd = packlib.rd
    allnames = {}
    for p in sorted(f[:-6] for f in os.listdir(base) if f.endswith('.index')):
        for e in m2pack.read_index(os.path.join(base, p + '.index'))[2]:
            allnames.setdefault(e['name'], p)
    tmpl = m2pack.read_index(os.path.join(base, 'az_mobs.index'))[2][-1]['raw']
    replace_ok = set(man.get('replace', []))

    def staged(pack, k):
        return rd(os.path.join(staging, 'add', pack, k.replace('d:/', 'd_/', 1)))

    def src_of(pack):
        if not check and os.path.exists(os.path.join(out, pack + '.index')):
            return out
        return base

    report = {}

    def write(pack, src, rep, add, ents, dat):
        tmp_i, tmp_d = os.path.join(out, pack + '.index.cape'), os.path.join(out, pack + '.data.cape')
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
        assert report[pack]['under_zip_limit'], (pack, report[pack])

    # 2) property: new names added, the listed ones replaced when they differ
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
                assert k in replace_ok, (pack, k, 'would replace an entry not listed in "replace"')
                if m2pack.read_entry(dat, have[k]) != b:
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

    # 3) Index: the new packs at the end (after the build's own lines)
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
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
