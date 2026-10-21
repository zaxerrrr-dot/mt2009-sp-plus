# -*- coding: utf-8 -*-
# MT2009_PLUS_WORLDBOSS_V1 - the client build's part for Boss Swiata (the server: playerbot_worldboss.h,
# linux-port/docker/mariadb/playerbot/worldboss.sql):
#   1) a new pack "yworldboss": the six world bosses' GF models (d:/ymir work/monster2/w_*) with what they name and our
#      client lacks - staged by stage_yworldboss.py under <staging>/add/yworldboss/<in-pack path> ("d_/" = "d:/");
#   2) its line at the end of pack/Index;
#   3) the existing packs "gamedata" and "dbdata" (patch_yworldboss_client.py): gamedata/mob_proto - the 36 rows
#      4420-4479 with their element; gamedata/npclist.txt - only rows missing (client 2.0.61 has all 36);
#      gamedata/item_list.txt, gamedata/item_proto (dbdata), locale/pl/itemdesc.txt (dbdata) - Skrzynka Tajemnic 38015,
#      Kupon SM (20) 80031, Kupon SM (10) 80032.
# The window (root/uiworldboss.py, root/uiscript/worldboss*.py), its graphics (atlas/d_/ymir work/ui/worldboss.dds,
# ui/minigame/world_boss/*.sub), the buffs' icon (root/mt2009_ui/affect/worldboss.tga) and Skrzynka Tajemnic's icon
# (root/icon/item/38015.tga) travel in the root pack like every root change.
# BUILD ORDER - it shares pack/Index, gamedata and dbdata with the other builders: after the ymeley line (any place
# after build57.py's data step works; the patches are append-only and idempotent), all on the same OUT:
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/yworldboss/build_yworldboss_packs.py \
#     <BASE pack dir> <OUT pack dir> [<staging dir>] [--data <dir>] [--check]
#
# --data: a directory with gamedata/dbdata files that win over the packs' (as ../ymeley). --check measures only.
# Every entry written is read back; an added name must be new to BASE and to the packs already in OUT. Idempotent: a
# second run gives "in out"/"unchanged".
import json
import os
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, HERE)
TEXT = ('.txt', '.msa', '.msm', '.mse', '.mss', '.msenv', '.sub', '.prb', '.prd', '.pre', '.prt', '.py', '.ifl', '.pra')
ZIP_LIMIT = 29 * 1024 * 1024
STAGING = '/opt/metin2/cache/yohara/yworldboss-staging'


def ctype(name):
    return 2 if name.endswith(TEXT) else 1


def main():
    import m2pack
    import packlib
    import patch_yworldboss_client as pc
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    check = '--check' in sys.argv
    data_from = sys.argv[sys.argv.index('--data') + 1] if '--data' in sys.argv else None
    if data_from:
        args.remove(data_from)
    base, out = args[:2]
    staging = args[2] if len(args) > 2 else STAGING
    man = json.load(open(os.path.join(HERE, 'yworldboss_manifest.json'), encoding='utf-8'))
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

    def src_of(pack):
        if os.path.exists(os.path.join(out, pack + '.index')):
            return out
        return base

    report = {}

    def write(pack, src, rep, add, ents, dat):
        tmp_i, tmp_d = os.path.join(out, pack + '.index.ywb'), os.path.join(out, pack + '.data.ywb')
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

    # 1) the new pack
    for pack in new_packs:
        keys = [e['name'] for e in man['packs'][pack]]
        items = dict((k, rd(os.path.join(staging, 'add', pack, k.replace('d:/', 'd_/', 1)))) for k in keys)
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

    # 2) Index: the new pack at the end
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

    # 3) gamedata / dbdata (patch_yworldboss_client.py)
    jobs = {'gamedata': [('gamedata/mob_proto', pc.mob_proto), ('gamedata/npclist.txt', pc.npclist),
                         ('gamedata/item_list.txt', pc.item_list)],
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
