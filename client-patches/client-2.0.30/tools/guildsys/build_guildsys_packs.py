# -*- coding: utf-8 -*-
# MT2009_PLUS_GUILDSYS_V1 - the client build's part of the guild system update (server-patches/guildsys/README.md; on
# Guild Systems compiled by Nazox). No new pack; existing packs get:
#   gamedata  gamedata/item_list.txt          the four books' lines (patch_guildsys_client.py)
#   dbdata    gamedata/item_proto, locale/pl/itemdesc.txt   their records / descriptions (from the server's SQL),
#             locale/pl/skilldesc.txt, gamedata/skilltable.txt   Balathor's guild skills 158-160
#   root      d:/ymir work/ui/guildsys_common.dds (GF 26.1.11's newskillcommon.dds, 256x768 - ours of that name is
#             another, smaller atlas) and its six squares: the skill window's icons
#             d:/ymir work/ui/skill/common/guild/guildsys_{burza,wola,nieugietosc}.sub and the affect bar's
#             d:/ymir work/ui/skill/common/affect/guildsys_{burza,wola,nieugietosc}.sub (client-2.0.30/guildsys/d_,
#             GF's white_dragon_{bless,resolution,firmness} squares under our names: the full install's etc pack has
#             GF's own names pointing at newskillcommon.dds, which our zodiak_maps pack replaces with a 256x352 one)
# The python (root/uiguild.py, playersettingmodule.py, uiaffectbar.py) travels in client-2.0.30/root like every root
# change (build57.py).
# BUILD ORDER - shares gamedata / dbdata / root: after every other step that patches them (after ../npcloc), on the
# same OUT (a pack already in OUT - an earlier step changed it - is the one patched):
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/guildsys/build_guildsys_packs.py <BASE pack dir> <OUT pack dir> [--check]
#
# clientY.sh: after the npcloc line,
#   # MT2009_PLUS_GUILDSYS_V1: guild system - books in gamedata/dbdata, Balathor's guild skills in dbdata, icons in root
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/guildsys/build_guildsys_packs.py $C/azbase \
#     $C/out/pack > $C/guildsys.json
# and guildsys/verify_guildsys.py in the verify loop. Every entry written is read back. Idempotent: a second run gives
# "unchanged". A name already in the full install's base pack "etc" (--etc=<dir with etc.index>, default
# /opt/metin2/cache/exebuild/smoke/client/pack, when there) is refused: it would shadow the install's file.
import json
import os
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, HERE)
ZIP_LIMIT = 29 * 1024 * 1024
DATA = os.path.normpath(os.path.join(HERE, '..', '..', 'guildsys'))
TEXT = ('.txt', '.sub', '.mse')
ETC_DEFAULT = '/opt/metin2/cache/exebuild/smoke/client/pack'


def etc_dir():
    for a in sys.argv[1:]:
        if a.startswith('--etc='):
            return a[6:]
    return ETC_DEFAULT


def etc_names():
    """the names of the full install's base pack etc (None when that pack is not here)"""
    import m2pack
    p = os.path.join(etc_dir(), 'etc.index')
    if not os.path.exists(p):
        return None
    return set(e['name'] for e in m2pack.read_index(p)[2])


def added_files():
    """pack -> {in-pack name: bytes} of the files this step adds (names lower-case as the packs keep them)"""
    out = {'root': {}}
    for dp, dn, fn in os.walk(DATA):
        for f in fn:
            path = os.path.join(dp, f)
            rel = os.path.relpath(path, DATA).replace(os.sep, '/')
            if rel.startswith('d_/'):
                out['root'][('d:' + rel[2:]).lower()] = open(path, 'rb').read()
    return out


def main():
    import m2pack
    import packlib
    import patch_guildsys_client as pc
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    check = '--check' in sys.argv
    base, out = args[:2]
    rd = packlib.rd
    report = {}

    def src_of(pack):
        return out if os.path.exists(os.path.join(out, pack + '.index')) else base

    def write(pack, src, rep, add, ents, dat):
        tmp_i, tmp_d = os.path.join(out, pack + '.index.gs'), os.path.join(out, pack + '.data.gs')
        r = packlib.repack_add_typed(os.path.join(src, pack + '.index'), os.path.join(src, pack + '.data'), rep, add,
                                     tmp_i, tmp_d, ents[-1]['raw'])
        os.replace(tmp_i, os.path.join(out, pack + '.index'))
        os.replace(tmp_d, os.path.join(out, pack + '.data'))
        f, v, nw = m2pack.read_index(os.path.join(out, pack + '.index'))
        nd = rd(os.path.join(out, pack + '.data'))
        names = [e['name'] for e in nw]
        assert len(set(names)) == len(names), pack
        got = {}
        for e in nw:
            assert zlib.crc32(nd[e['pos']:e['pos'] + e['size']]) & 0xffffffff == e['dcrc'], (pack, e['name'])
            got[e['name']] = m2pack.read_entry(nd, e)
        for n, b in list(rep.items()) + [(k, b) for k, (b, c) in add.items()]:
            assert got[n] == b, (pack, n)
        for e in ents:
            if e['name'] not in rep:
                assert got[e['name']] == m2pack.read_entry(dat, e), (pack, e['name'])
        return dict(old=r[0], added=r[1], replaced=r[2], entries=len(nw), data_mb=round(len(nd) / 1e6, 2),
                    under_zip_limit=len(nd) < ZIP_LIMIT)

    # every name this step adds must be new to every pack but the one it goes to
    files = added_files()
    elsewhere = {}
    for d in (base, out):
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if f.endswith('.index'):
                for e in m2pack.read_index(os.path.join(d, f))[2]:
                    elsewhere.setdefault(e['name'], set()).add(f[:-6])
    for pack, fs in files.items():
        clash = sorted(n for n in fs if elsewhere.get(n, set()) - {pack})
        assert not clash, (pack, clash[:5])
    etc = etc_names()
    if etc is not None:
        clash = sorted(n for fs in files.values() for n in fs if n in etc)
        assert not clash, ('in the base pack etc', clash[:5])
    report['etc_pack_checked'] = etc is not None

    jobs = {'gamedata': [('gamedata/item_list.txt', pc.item_list)],
            'dbdata': [('gamedata/item_proto', pc.item_proto), ('locale/pl/itemdesc.txt', pc.itemdesc),
                       ('locale/pl/skilldesc.txt', pc.skilldesc), ('gamedata/skilltable.txt', pc.skilltable)],
            'root': []}
    for pack, patches in jobs.items():
        src = src_of(pack)
        f, v, ents = m2pack.read_index(os.path.join(src, pack + '.index'))
        dat = rd(os.path.join(src, pack + '.data'))
        have = dict((e['name'], e) for e in ents)
        rep, add = {}, {}
        for n, fn in patches:
            if n not in have:
                raise SystemExit('%s: %s is not in the pack' % (pack, n))
            b = m2pack.read_entry(dat, have[n])
            nb, changed = fn(b)
            if nb != b:
                rep[n] = nb
        for n, b in sorted(files.get(pack, {}).items()):
            if n in have:
                if m2pack.read_entry(dat, have[n]) != b:
                    rep[n] = b
            else:
                add[n] = (b, 2 if n.endswith(TEXT) else 1)
        if not rep and not add:
            report[pack] = 'unchanged'
        elif check:
            report[pack] = dict(replace=sorted(rep), add=len(add))
        else:
            report[pack] = write(pack, src, rep, add, ents, dat)
            report[pack]['replaced_names'] = sorted(rep)
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
