# -*- coding: utf-8 -*-
# MT2009_PLUS_BALATHOR_V1 (Autor: dracaryS) - the client build's part for Krypta Balathora (420, the guild lair):
#   1) the new packs of balathor_manifest.json "new_packs" - balathor_map (the map folder metin2_map_balathor, its
#      textureset, terrain textures and msenv), balathor_obj (the lair's object models), balathor_mobs (the races of
#      the 20 vnums our packs lack, the egg / ice / Hwacha effects the exe names) - staged by stage_balathor.py under
#      <staging>/add/<pack>/<in-pack path> ("d_/" = "d:/");
#   2) the existing pack "property": the lair's 7 object properties (property/guild_whitedragon/...);
#   3) their lines at the end of pack/Index;
#   4) the existing packs "gamedata" (atlasinfo row, npclist rows if missing, mob_proto rows, item_list line),
#      "dbdata" (item_proto records and itemdesc lines of Ognista Strzala 30395 and the chests 83075 / 83076) and "locale" (locale/pl/locale_game.txt:
#      the boss window's strings; locale/common/camera/guild_white_dragonlair/*.txt: the six cinema scripts the server
#      runs - client-2.0.30/balathor/locale/...) - patch_balathor_client.py.
# The python (root/uiguildwhitedragon.py, root/uiscript/guildwhitedragonlairwindow.py, the hooks in game.py /
# interfacemodule.py, the minimap name in localeinfo.py) and the icons (root/icon/item/30395.tga, 83075.tga, 83076.tga,
# guild_whitedragon_boss.tga, guild_whitedragon_egg.tga) travel in client-2.0.30/root like every root change. The boss
# window's pictures (the package's whole d:/ymir work/ui/game/guild_white_dragon_lair/, the atlases ui/spacebar_01.dds /
# spacebar_effect.dds its .sub cut, ui/whitedragon_damage_01.dds) and the named effects go in balathor_mobs
# (balathor_manifest.json "ui"): 3.0.4 took the exe smoke client's etc pack for the players' and shipped none of them -
# exception.Abort when the boss window opened at the cinema (MT2009_PLUS_BALATHOR_UI_V2).
# BUILD ORDER - it shares pack/Index, property, gamedata, dbdata and locale with the other builders: after ../spider3,
# before ../kawuco / ../yfinal, all on the same OUT (a pack already in OUT - an earlier step changed it - is the one
# patched). It needs linux-port/docker/mariadb/playerbot/balathor.sql (the server's rows the client rows are made of).
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/balathor/build_balathor_packs.py <BASE pack dir> <OUT pack dir> \
#     <staging dir> [--check]
#
# clientY.sh: after the spider3 lines,
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/balathor/stage_balathor.py \
#     /opt/metin2/cache/yohara/balathor-staging
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/balathor/build_balathor_packs.py $C/azbase \
#     $C/out/pack /opt/metin2/cache/yohara/balathor-staging > $C/balathor.json
# then balathor/verify_balathor_packs.py on OUT (in the verify loop). Every entry written is read back; an added name
# must be new to BASE and to the packs already in OUT. Idempotent: a second run gives "in out" / "unchanged".
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
LOCALE_DATA = os.path.normpath(os.path.join(HERE, '..', '..', 'balathor'))


def ctype(name):
    return 2 if name.endswith(TEXT) else 1


def locale_files():
    """in-pack name -> bytes of client-2.0.30/balathor/locale/... (the cinema scripts)"""
    out = {}
    for dp, dn, fn in os.walk(LOCALE_DATA):
        for f in fn:
            p = os.path.join(dp, f)
            out[os.path.relpath(p, LOCALE_DATA).replace(os.sep, '/').lower()] = open(p, 'rb').read()
    assert len(out) == 6 and all(k.startswith('locale/common/camera/guild_white_dragonlair/') for k in out), sorted(out)
    return out


def main():
    import m2pack
    import packlib
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    check = '--check' in sys.argv
    if len(args) != 3:
        raise SystemExit('usage: build_balathor_packs.py <BASE pack dir> <OUT pack dir> <staging dir> [--check]')
    base, out, staging = args
    import patch_balathor_client as pc
    man = json.load(open(os.path.join(HERE, 'balathor_manifest.json'), encoding='utf-8'))
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

    def staged(pack, k):
        return rd(os.path.join(staging, 'add', pack, k.replace('d:/', 'd_/', 1)))

    def src_of(pack):
        return out if os.path.exists(os.path.join(out, pack + '.index')) else base

    report = {}

    def write(pack, src, rep, add, ents, dat):
        tmp_i, tmp_d = os.path.join(out, pack + '.index.bal'), os.path.join(out, pack + '.data.bal')
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
        # a file another pack of this build already carries with the same bytes is left out here; a different file
        # under the same name stops the build
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

    # 2) property: the new names added (an existing name with other bytes stops the build)
    for pack in ('property',):
        src = src_of(pack)
        f, v, ents = m2pack.read_index(os.path.join(src, pack + '.index'))
        dat = rd(os.path.join(src, pack + '.data'))
        have = dict((e['name'], e) for e in ents)
        add = {}
        for e in man['packs'].get(pack, []):
            k = e['name']
            b = staged(pack, k)
            if k in have:
                assert m2pack.read_entry(dat, have[k]) == b, (pack, k, 'already there with other content')
            else:
                assert k == k.lower() and k not in allnames, (pack, k, allnames.get(k))
                add[k] = (b, ctype(k))
        if not add:
            report[pack] = 'unchanged'
        elif check:
            report[pack] = dict(add=len(add))
        else:
            report[pack] = write(pack, src, {}, add, ents, dat)

    # 3) Index: the new packs at the end
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

    # 4) gamedata / dbdata / locale (patch_balathor_client.py) and the cinema scripts
    cams = locale_files()
    for n in cams:
        assert allnames.get(n, 'locale') == 'locale', (n, allnames.get(n))
    jobs = {'gamedata': [('gamedata/atlasinfo.txt', pc.atlasinfo), ('gamedata/npclist.txt', pc.npclist),
                         ('gamedata/mob_proto', pc.mob_proto), ('gamedata/item_list.txt', pc.item_list)],
            'dbdata': [('gamedata/item_proto', pc.item_proto), ('locale/pl/itemdesc.txt', pc.itemdesc)],
            'locale': [('locale/pl/locale_game.txt', pc.locale_game)]}
    for pack, files in jobs.items():
        src = src_of(pack)
        f, v, ents = m2pack.read_index(os.path.join(src, pack + '.index'))
        dat = rd(os.path.join(src, pack + '.data'))
        have = dict((e['name'], e) for e in ents)
        rep, add = {}, {}
        for n, fn in files:
            b = m2pack.read_entry(dat, have[n])
            nb, changed = fn(b)
            if nb != b:
                rep[n] = nb
        if pack == 'locale':
            for n, b in sorted(cams.items()):
                if n in have:
                    if m2pack.read_entry(dat, have[n]) != b:
                        rep[n] = b
                else:
                    add[n] = (b, ctype(n))
        if not rep and not add:
            report[pack] = 'unchanged'
        elif check:
            report[pack] = dict(replace=sorted(rep), add=sorted(add))
        else:
            report[pack] = write(pack, src, rep, add, ents, dat)
            report[pack]['replaced_names'] = sorted(rep)

    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
