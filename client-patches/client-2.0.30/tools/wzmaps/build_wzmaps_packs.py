# -*- coding: utf-8 -*-
# MT2009_PLUS_MAPS_WZ_V1 - the client build's part for Wezowe Pole (80) and Kraina Gigantow (70):
#   1) the new packs of wzmaps_manifest.json "new_packs" - wzmaps_map (the two map folders under their new names, the
#      textureset, terrain textures, msenv, atlases), wzmaps_obj (the map objects' models) and wzmaps_mobs (the Giants',
#      ogres' and golems' races) - staged by stage_wzmaps.py under <staging>/add/<pack>/<in-pack path> ("d_/" = "d:/");
#   2) the existing pack "property": the maps' object properties added (none of ours replaced);
#   3) their lines at the end of pack/Index;
#   4) the existing pack "gamedata" (patch_wzmaps_client.py): gamedata/mob_proto - the level byte of 1401-1403 /
#      1601-1603 (the pl-wiki's); gamedata/atlasinfo.txt - the maps' rows in place of the base client's
#      metin2_map_WL_01 / metin2_map_nusluck01 rows.
# The maps' names on the minimap (localeinfo.py MINIMAP_ZONE_NAME_DICT) and the GM panel's teleports travel in
# client-2.0.30/root like every root change.
# BUILD ORDER - it shares pack/Index, property and gamedata with the other builders, all on the same OUT (a pack
# already in OUT - an earlier step changed it - is the one patched). The 2.x line (MT2009_PLUS_MAPS_WZ_V1 taken over on
# 26 October 2026; its staging /opt/metin2/cache/wzmaps-2x-staging, made by stage_wzmaps.py with the 2.x defaults):
# in /opt/metin2/cache/client237.sh (and the 2.x build scripts after it) after the zaklety237 line and before the
# global mode's line,
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/wzmaps/build_wzmaps_packs.py $C/azbase $C/out/pack \
#     /opt/metin2/cache/wzmaps-2x-staging > $C/wzmaps.json
#   echo VERIFY wzmaps; docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/wzmaps/verify_wzmaps.py \
#     $C/out/pack /opt/metin2/cache/yohara/cape301-work /opt/metin2/cache/c67/chk/gamedata/npclist.txt | tail -2
#
#   ... build_wzmaps_packs.py <BASE> <OUT> <staging> --check      # measure only, writes nothing
#
# The Yohara line (clientY.sh): after the ygloves line, before ../yfinal, with /opt/metin2/cache/yohara/wzmaps-staging.
# then verify_wzmaps.py on OUT (wzmaps/verify_wzmaps.py in the verify loop). --data: a directory with the build's
# patched copies (flat: mob_proto, atlasinfo.txt) to start from instead of the packs' entries. Every entry written is
# read back; an added name must be new to BASE and to the packs already in OUT (stage again when a newer BASE has
# gained some). Idempotent: a second run gives "in out"/"unchanged".
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
    import patch_wzmaps_client as pc
    man = json.load(open(os.path.join(HERE, 'wzmaps_manifest.json'), encoding='utf-8'))
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
    _packcache = {}

    def existing_entry(pack, name):
        for d in (out, base):
            ip = os.path.join(d, pack + '.index')
            if not os.path.exists(ip):
                continue
            if (d, pack) not in _packcache:
                ents = m2pack.read_index(ip)[2]
                _packcache[(d, pack)] = (dict((e['name'], e) for e in ents), rd(os.path.join(d, pack + '.data')))
            idx, dat = _packcache[(d, pack)]
            if name in idx:
                return m2pack.read_entry(dat, idx[name])
        return None
    replace_ok = set(man.get('replace', []))

    def staged(pack, k):
        return rd(os.path.join(staging, 'add', pack, k.replace('d:/', 'd_/', 1)))

    def src_of(pack):
        if os.path.exists(os.path.join(out, pack + '.index')):
            return out
        return base

    report = {}

    def write(pack, src, rep, add, ents, dat):
        tmp_i, tmp_d = os.path.join(out, pack + '.index.wz2'), os.path.join(out, pack + '.data.wz2')
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
        # A file another new pack of this build already carries with the same bytes (e.g. the golem sounds,
        # in ymeley_mobs too) is left out here; a different file under the same name still stops the build.
        shared = []
        for k in list(keys):
            if k in allnames:
                other = existing_entry(allnames[k], k)
                if other is not None and other == items[k]:
                    shared.append(k)
                    del items[k]
        keys = [k for k in keys if k in items]
        if shared:
            report.setdefault('shared_left_out', {})[pack] = len(shared)
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
    # 4) gamedata (patch_wzmaps_client.py): mob_proto levels, atlasinfo rows
    jobs = {'gamedata': [('gamedata/mob_proto', pc.mob_proto), ('gamedata/atlasinfo.txt', pc.atlasinfo)]}
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
