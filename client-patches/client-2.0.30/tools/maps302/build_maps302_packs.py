# -*- coding: utf-8 -*-
# MT2009_PLUS_YOHARA_MAPS302_V1 - the client build's part for Zbocze Gautama (302, metin2_map_dawnmistwood), Nefrytowa
# Zatoka (303, metin2_map_BayBlackSand) and Gromiste Gory (304, metin2_map_Mt_Thunder):
#   1) the new packs of maps302_manifest.json "new_packs" - one per map (gautama_map, zatoka_map, gromiste_map: the
#      map folder, its textureset, terrain textures, msenv, atlas), yohara_obj (the map objects' models, trees,
#      effects) and yohara_mobs (the races of the three maps our packs lack) - staged by stage_maps302.py under
#      <staging>/add/<pack>/<in-pack path> ("d_/" = "d:/");
#   2) the existing pack "property": the entries listed in "replace" (bone_whale_tail00.prb with the model's real
#      path) - old entries otherwise unchanged;
#   3) their lines at the end of pack/Index;
#   4) MT2009_PLUS_OCHAO_GAUTAMA_V1 - the existing pack "locale": MAP_DAWN / MAP_DAWNMISTWOOD of
#      locale/pl/locale_game.txt and locale_game_marty.txt become "Zbocze Gautama" (they said "Klif Gautama").
# No gamedata row changes: atlasinfo.txt, npclist.txt and mob_proto of client 2.0.64 already have the three maps and
# every vnum they spawn.
# Run it AFTER ../cape301/build_cape301_packs.py, on the same OUT: the names cape301 adds are left to its packs (the
# staging counts them as ours), and a property pack already in OUT is the one patched:
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/maps302/build_maps302_packs.py \
#     <BASE pack dir> <OUT pack dir> <staging dir>
#   ... build_maps302_packs.py <BASE> <OUT> <staging> --check      # measure only, writes nothing
#
# client61.sh-style builds: after the cape301 line,
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/maps302/build_maps302_packs.py $C/azbase $C/out/pack \
#     /opt/metin2/cache/yohara/maps302-staging > $C/maps302.json
# then verify_maps302.py on OUT. Every entry written is read back; an added name must be new to BASE and to the
# packs already in OUT (stage again when a newer BASE has gained some: ../atlantis/dump_base.py <BASE>
# /opt/metin2/cache/yohara/cape301-work, then stage_maps302.py). Idempotent: a second run gives "in out"/"unchanged".
import json
import os
import re
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
TEXT = ('.txt', '.msa', '.msm', '.mse', '.mss', '.msenv', '.sub', '.prb', '.prd', '.pre', '.prt', '.py', '.ifl', '.pra')
ZIP_LIMIT = 29 * 1024 * 1024
# MT2009_PLUS_OCHAO_GAUTAMA_V1: the owner's name for map 302 (13 Oct 2026) - the client called it "Klif Gautama"
# (MAP_DAWN / MAP_DAWNMISTWOOD of locale_game.txt and locale_game_marty.txt, pack "locale"); every other row stays.
LOCALE_NAMES = {b'MAP_DAWN': u'Zbocze Gautama', b'MAP_DAWNMISTWOOD': u'Zbocze Gautama'}
LOCALE_FILES = ('locale/pl/locale_game.txt', 'locale/pl/locale_game_marty.txt')


def locale_rename(b):
    for key, val in LOCALE_NAMES.items():
        b, n = re.subn(rb'(?m)^(' + key + rb'\t)[^\r\n]*', lambda m: m.group(1) + val.encode('cp1250'), b)
        assert n == 1, (key, n)
    return b


def ctype(name):
    return 2 if name.endswith(TEXT) else 1


def main():
    import m2pack
    import packlib
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    check = '--check' in sys.argv
    base, out, staging = args[:3]
    man = json.load(open(os.path.join(HERE, 'maps302_manifest.json'), encoding='utf-8'))
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
        tmp_i, tmp_d = os.path.join(out, pack + '.index.m302'), os.path.join(out, pack + '.data.m302')
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

    # 2b) locale (MT2009_PLUS_OCHAO_GAUTAMA_V1): the map names of locale_game(_marty).txt
    for pack in ('locale',):
        src = src_of(pack)
        f, v, ents = m2pack.read_index(os.path.join(src, pack + '.index'))
        dat = rd(os.path.join(src, pack + '.data'))
        have = dict((e['name'], e) for e in ents)
        rep = {}
        for k in LOCALE_FILES:
            old = m2pack.read_entry(dat, have[k])
            new = locale_rename(old)
            if new != old:
                rep[k] = new
        if not rep:
            report[pack] = 'unchanged'
        elif check:
            report[pack] = dict(replace=sorted(rep))
        else:
            report[pack] = write(pack, src, rep, {}, ents, dat)
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
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
