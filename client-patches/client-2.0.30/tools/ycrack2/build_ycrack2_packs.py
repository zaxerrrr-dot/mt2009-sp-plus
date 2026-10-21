# -*- coding: utf-8 -*-
# MT2009_PLUS_YOHARA_CRACK2_V1 - the client build's part for the three other Time Rift dungeons: Grota Wygnancow 2
# (SZC) (405, metin2_map_boss_crack_skipia), Twierdza Czerwonego Smoka (SZC) (406, metin2_map_boss_crack_flame),
# Straznica Nemere (SZC) (407, metin2_map_boss_crack_snow):
#   1) the new pack ycrack2_maps - each map a FULL folder (MT2009_PLUS_COPIED_MAPS_V1, ../ycopymaps: our exe cannot
#      load GF's copied maps - it reads ParentMapName without "maps/"): every file of its terrain's folder as the
#      packs already hold it (the grotto: ../yiluzja's metin2_map_boss_awaken_skipia, GF's Grota Wygnancow 2 with the
#      temple open - GF's crack_skipia sector 000000 is the same file; the fortress / watchtower: the base client's
#      metin2_map_n_flame_dungeon_01 / metin2_map_n_snow_dungeon_01 = Razador's / Nemere's), the terrain's
#      setting.txt with the official BasePosition, a mapproperty.txt without ParentMapName, and the PB twin's
#      atlas.sub (the same picture) where the twin has one; ycrack2_mobs... - the races our packs lack (staged by
#      stage_ycrack2.py under <staging>/add/<pack>/<in-pack path>, "d_/" = "d:/");
#   2) their lines at the end of pack/Index;
#   3) the existing packs "gamedata" and "dbdata" (patch_ycrack2_client.py): gamedata/mob_proto - the 49 rows of
#      yohara_crack2.sql with their element; gamedata/atlasinfo.txt - the three maps' rows (the official bases,
#      overlapping no map of our atlasinfo); gamedata/item_list.txt, gamedata/item_proto (dbdata) and
#      locale/pl/itemdesc.txt (dbdata) - the 6 items of yohara_items_crack2.sql (tools/yohara_crack2/ycrack2_client.json).
# The maps' names on the minimap (localeinfo.py MINIMAP_ZONE_NAME_DICT) and the items' icons (root/icon/item) travel in
# client-2.0.30/root like every root change.
# BUILD ORDER - they share pack/Index, gamedata and dbdata, and the grotto's terrain is ../yiluzja's: the build's own
# packs, then ../cape301 ... ../ypb, ../yiluzja, ../ycrack and then this one, all on the same OUT (before ../yfinal,
# which sets every monster's element bits from the server's *_zywioly.sql files):
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/ycrack2/build_ycrack2_packs.py <BASE pack dir> <OUT pack dir> <staging dir> \
#     [--data <dir>]
#   ... build_ycrack2_packs.py <BASE> <OUT> <staging> --check      # measure only, writes nothing
#
# clientY.sh: after the ycrack line,
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/ycrack2/build_ycrack2_packs.py $C/azbase $C/out/pack \
#     /opt/metin2/cache/yohara/ycrack2-staging > $C/ycrack2.json
# then verify_ycrack2.py on OUT. Every entry written is read back; an added name must be new to BASE and to the packs
# already in OUT. Idempotent: a second run gives "in out"/"unchanged".
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
PROPERTY = b'ScriptType MapProperty\r\n\r\nMapType "Outdoor"\r\n'     # = ../ycopymaps' (no ParentMapName)
MAPS_PACK = 'ycrack2_maps'


def ctype(name):
    return 2 if name.endswith(TEXT) else 1


def map_files(man, read_name):
    """{in-pack name: bytes} of ycrack2_maps - each map's folder from its terrain's files in the packs"""
    out = {}
    for idx, M in sorted(man['maps'].items()):
        tp, mp = 'maps/%s/' % M['terrain'], 'maps/%s/' % M['folder']
        names = read_name('prefix', tp)
        st = names.get(tp + 'setting.txt')
        if st is None or tp + '000000/attr.atr' not in names:
            raise SystemExit('map %s: its terrain %s is in no pack of BASE/OUT' % (idx, M['terrain']))
        s = st.decode('latin1')
        size = re.search(r'MapSize\s+(\d+)\s+(\d+)', s)
        assert size and [int(size.group(1)), int(size.group(2))] == M['size'], (idx, s[:120])
        s2, k = re.subn(r'(BasePosition[ \t]+)\d+([ \t]+)\d+', lambda x: '%s%d%s%d' % (
            x.group(1), M['base'][0], x.group(2), M['base'][1]), s)
        assert k == 1, idx
        for rel, b in names.items():
            r = rel[len(tp):]
            if r in ('setting.txt', 'mapproperty.txt'):
                continue
            out[mp + r] = b
        out[mp + 'setting.txt'] = s2.encode('latin1')
        out[mp + 'mapproperty.txt'] = PROPERTY
        sub = read_name('one', 'd:/ymir work/ui/atlas/%s/atlas.sub' % M['pb'])
        if sub is not None:
            out['d:/ymir work/ui/atlas/%s/atlas.sub' % M['folder']] = sub
    return out


def main():
    import m2pack
    import packlib
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    check = '--check' in sys.argv
    data_from = sys.argv[sys.argv.index('--data') + 1] if '--data' in sys.argv else None
    if data_from:
        args.remove(data_from)
    base, out, staging = args[:3]
    import patch_ycrack2_client as pc
    man = json.load(open(os.path.join(HERE, 'ycrack2_manifest.json'), encoding='utf-8'))
    new_packs = man['new_packs']
    rd = packlib.rd
    allnames = {}
    where = {}                                   # name -> (dir, pack) - OUT first (the chain's newer copy)
    for d in (out, base):
        if not os.path.isdir(d):
            continue
        for p in sorted(f[:-6] for f in os.listdir(d) if f.endswith('.index')):
            if p in new_packs:
                continue
            for e in m2pack.read_index(os.path.join(d, p + '.index'))[2]:
                allnames.setdefault(e['name'], p)
                where.setdefault(e['name'], (d, p))
    tmpl = m2pack.read_index(os.path.join(base, 'az_mobs.index'))[2][-1]['raw']
    cache = {}

    def entry(name):
        d, p = where[name]
        if (d, p) not in cache:
            cache[(d, p)] = (dict((e['name'], e) for e in m2pack.read_index(os.path.join(d, p + '.index'))[2]),
                             rd(os.path.join(d, p + '.data')))
        ents, dat = cache[(d, p)]
        return m2pack.read_entry(dat, ents[name])

    def read_name(kind, key):
        if kind == 'one':
            return entry(key) if key in where else None
        return dict((n, entry(n)) for n in sorted(where) if n.startswith(key))

    def staged(pack, k):
        return rd(os.path.join(staging, 'add', pack, k.replace('d:/', 'd_/', 1)))

    def src_of(pack):
        if os.path.exists(os.path.join(out, pack + '.index')):
            return out
        return base

    report = {}

    def write(pack, src, rep, add, ents, dat):
        tmp_i, tmp_d = os.path.join(out, pack + '.index.ycr2'), os.path.join(out, pack + '.data.ycr2')
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
        if pack == MAPS_PACK:
            items = map_files(man, read_name)
        else:
            items = dict((e['name'], staged(pack, e['name'])) for e in man['packs'].get(pack, []))
        keys = sorted(items)
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

    # 2) Index: the new packs at the end (after the build's own lines and the earlier builders')
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
    # 3) gamedata / dbdata (patch_ycrack2_client.py): mob_proto, atlasinfo, npclist rows (append only); the items
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
