# -*- coding: utf-8 -*-
# MT2009_PLUS_REMOTE_CALL_V1 - Enasir (Dozorca / Handlarz) in the client build (server-patches/remotecall/README.md;
# the button, tooltip and questions are root python - uiremotecall.py, the side bar's button pictures
# root/mt2009_ui/sidebar/enasir_0x.tga):
#   1) the existing packs "gamedata" (gamedata/item_list.txt, gamedata/mob_proto) and "dbdata" (gamedata/item_proto,
#      locale/pl/itemdesc.txt): patch_remotecall_client.py - 72368-72371 and Enasir (20874); gamedata/npclist.txt
#      must have GF's "20874 peddler_call" row (it has - checked);
#   2) a new pack "remotecall" (new names only) from the unpacked GF 26.1.11 client - the same bytes as the owner's
#      package (compared file by file on 5 November 2026: model, motions, effects, button, icons all identical):
#      - icon/item/72368.tga, 72369.tga (the "(h)" items use them too);
#      - Enasir: gf28/gfres.closure of d:/ymir work/npc2/peddler_call/peddler_call.msm + motlist.txt (model, mount,
#        textures, SPAWN / WAIT motions, their effects peddler_call_spawn_01/02.mse and the textures those name) and
#        SEEDS (the spawn effect's sound sound/effect/npc2/peddler_call_spawn_01.mss + its .wav) minus every name our
#        packs (BASE, OUT, the base-pack listing tcm/gf28/ourpacks_pre.txt) have;
#      a name of the icons that another pack has with OTHER content stops the build;
#   3) its line at the end of pack/Index.
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/remotecall/build_remotecall_packs.py <BASE pack dir> <OUT pack dir> [--check]
#
# clientY.sh - it rewrites gamedata/dbdata (item_proto, item_list, itemdesc, mob_proto): after every other step that
# writes them (after S_energia_pack), before the npclist / verify loop:
#   S_remotecall_packs() { docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/remotecall/build_remotecall_packs.py \
#     $C/azbase $C/out/pack; }; step remotecall_packs $C/remotecall.json S_remotecall_packs
# then remotecall/verify_remotecall.py <OUT> in the verify loop. Every entry written is read back. Idempotent: a second
# run gives "unchanged".
import json
import os
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, '/opt/metin2/cache/tcm/gf28')
sys.path.insert(0, HERE)
PACK = 'remotecall'
ZIP_LIMIT = 29 * 1024 * 1024
OURS_PRE = '/opt/metin2/cache/tcm/gf28/ourpacks_pre.txt'
TEXT = ('.txt', '.sub', '.mse', '.msm', '.msa', '.mss')
# more GF files: the spawn effect's sound (the exe reads sound/<effect path>.mss next to an effect)
SEEDS = [
    'sound/effect/npc2/peddler_call_spawn_01.mss',
]


def ctype(name):
    return 2 if name.endswith(TEXT) else 1


def norm(p):
    p = p.replace('\\', '/').strip().lower()
    return 'd:/' + p[3:] if p.startswith('d_/') else p


def gf_bytes(key):
    import gfres
    src = gfres.GF.get(key)
    if src is None:
        raise SystemExit('%s: %s is not in the GF client' % (PACK, key))
    return open(src, 'rb').read()


def sub_image(key, b):
    """the picture a .sub names (exe CGraphicSubImage: version 2.0 next to the .sub, else d:/ymir work/ui/)"""
    kv = {}
    for l in b.decode('latin1').replace('\r', '').split('\n'):
        t = l.split(None, 1)
        if len(t) == 2:
            kv[t[0].lower()] = t[1].strip().strip('"')
    img = norm(kv.get('image', ''))
    assert kv.get('title', '').lower() == 'subimage' and img, key
    if kv.get('version') == '2.0':
        return key.rsplit('/', 1)[0] + '/' + img
    return 'd:/ymir work/ui/' + img


def our_names(base, out):
    """name -> (dir, pack, entry) of every pack of BASE / OUT but ours (OUT's wins - it is what the build has)"""
    import m2pack
    where = {}
    for d in (out, base):
        if not d or not os.path.isdir(d):
            continue
        for p in sorted(f[:-6] for f in os.listdir(d) if f.endswith('.index')):
            if p == PACK:
                continue
            for e in m2pack.read_index(os.path.join(d, p + '.index'))[2]:
                where.setdefault(e['name'].lower(), (d, p, e))
    return where


def pre_names():
    import gfres
    return gfres.load_ours(OURS_PRE) if os.path.exists(OURS_PRE) else set()


def plan(base, out):
    """the pack's entries {name: bytes} and a report (kept names, unresolved)"""
    import gfres
    import m2pack
    import packlib
    import patch_remotecall_client as pc
    where = our_names(base, out)
    pre = pre_names()
    ours = set(where) | pre
    _cache = {}

    def content_of(name):
        d, p, e = where[name]
        if (d, p) not in _cache:
            _cache[(d, p)] = packlib.rd(os.path.join(d, p + '.data'))
        return m2pack.read_entry(_cache[(d, p)], e)

    # the explicit files: the two GF icons (the "(h)" items use them too)
    want = {}
    for icon in sorted(set(it['icon'] for it in pc.items())):
        k = 'icon/item/%d.tga' % icon
        want[k] = gf_bytes(k)
    files, kept, listed = {}, {}, []
    for k, b in sorted(want.items()):
        if k in where:
            if content_of(k) != b:
                raise SystemExit('%s: %s is in %s/%s with other content - replace it there or drop it here'
                                 % (PACK, k, where[k][0], where[k][1]))
            kept[k] = where[k][1]
        elif k in pre:
            listed.append(k)
        else:
            files[k] = b
    # Enasir: gfres closure of his .msm, motlist.txt (SPAWN / WAIT and their effects) and SEEDS, new names only
    seeds = ['d:/ymir work/npc2/peddler_call/peddler_call.msm', 'd:/ymir work/npc2/peddler_call/motlist.txt'] + SEEDS
    got, unresolved, ours_hit = gfres.closure(seeds, ours)
    for s in seeds:
        if s not in got and s not in ours:
            raise SystemExit('%s: %s is in no pack and not in the GF client' % (PACK, s))
    model_files = 0
    for k, src in sorted(got.items()):
        if k in ours or k in files or k in kept:
            continue
        files[k] = open(src, 'rb').read()
        model_files += 1
    for k in files:
        assert k == k.lower() and '\\' not in k, k
    rep = dict(kept_same_content=kept, in_base_listing=listed, model_files=model_files,
               already_ours=sorted(ours_hit), unresolved=sorted(unresolved), gr2_undecodable=sorted(gfres.GR2_FAIL))
    return files, rep


def main():
    import m2pack
    import packlib
    import patch_remotecall_client as pc
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    check = '--check' in sys.argv
    if len(args) != 2:
        raise SystemExit('usage: build_remotecall_packs.py <BASE pack dir> <OUT pack dir> [--check]')
    rd = packlib.rd
    base, out = args
    report = {}

    def src_of(pack):
        return out if os.path.exists(os.path.join(out, pack + '.index')) else base

    def readback(pack, rep, add, ents, dat):
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
        return dict(entries=len(nw), data_mb=round(len(nd) / 1e6, 2), under_zip_limit=len(nd) < ZIP_LIMIT)

    # 1) gamedata and dbdata
    jobs = {}
    for n, p in pc.PACK_OF.items():
        jobs.setdefault(p, []).append(n)
    for pack, names in sorted(jobs.items()):
        src = src_of(pack)
        f, v, ents = m2pack.read_index(os.path.join(src, pack + '.index'))
        dat = rd(os.path.join(src, pack + '.data'))
        have = dict((e['name'], e) for e in ents)
        rep = {}
        for n in sorted(names):
            if n not in have:
                raise SystemExit('%s: %s is not in the pack' % (pack, n))
            b = m2pack.read_entry(dat, have[n])
            nb, changed = pc.JOBS[n](b)
            if nb != b:
                rep[n] = nb
                report.setdefault('changed', {})[n] = changed
        if not rep:
            report[pack] = 'unchanged'
        elif check:
            report[pack] = dict(replace=sorted(rep))
        else:
            ti, td = os.path.join(out, pack + '.index.remotecall'), os.path.join(out, pack + '.data.remotecall')
            r = packlib.repack_add_typed(os.path.join(src, pack + '.index'), os.path.join(src, pack + '.data'), rep, {},
                                         ti, td, ents[-1]['raw'])
            os.replace(ti, os.path.join(out, pack + '.index'))
            os.replace(td, os.path.join(out, pack + '.data'))
            report[pack] = readback(pack, rep, {}, ents, dat)
            report[pack].update(replaced=r[2], replaced_names=sorted(rep))
            assert report[pack]['under_zip_limit'], report[pack]

    # Enasir's npclist row (GF's, in the repo's gamedata) - checked, not written
    src = src_of('gamedata')
    f, v, ents = m2pack.read_index(os.path.join(src, 'gamedata.index'))
    gd = dict((e['name'], e) for e in ents)
    if 'gamedata/npclist.txt' not in gd or not pc.npclist_ok(
            m2pack.read_entry(rd(os.path.join(src, 'gamedata.data')), gd['gamedata/npclist.txt'])):
        raise SystemExit('gamedata/npclist.txt has no "%s" row' % pc.NPCLIST_ROW.replace('\t', ' '))
    report['npclist'] = 'has 20874 peddler_call'

    # 2) the new pack
    files, info = plan(base, out)
    report['plan'] = info
    have = None
    if os.path.exists(os.path.join(out, PACK + '.index')):
        f, v, ents = m2pack.read_index(os.path.join(out, PACK + '.index'))
        dat = rd(os.path.join(out, PACK + '.data'))
        have = dict((e['name'], m2pack.read_entry(dat, e)) for e in ents)
    if os.path.exists(os.path.join(base, PACK + '.index')) and base != out:
        raise SystemExit('%s is in BASE - drop it from BASE' % PACK)
    if have == files:
        report[PACK] = 'unchanged'
    elif check:
        size = sum(len(m2pack.encode_entry(b, ctype(k))) for k, b in files.items())
        report[PACK] = dict(files=len(files), data_mb=round(size / 1e6, 2))
    else:
        tmpl_ix = [os.path.join(d, p) for d in (base, out) for p in (['az_mobs.index'] + sorted(os.listdir(d)))
                   if p.endswith('.index') and p != PACK + '.index' and os.path.exists(os.path.join(d, p))]
        tmpl = m2pack.read_index(tmpl_ix[0])[2][-1]['raw']
        add = dict((k, (b, ctype(k))) for k, b in files.items())
        ti, td = os.path.join(out, PACK + '.index.remotecall'), os.path.join(out, PACK + '.data.remotecall')
        packlib.repack_add_typed(None, None, {}, add, ti, td, tmpl)
        os.replace(ti, os.path.join(out, PACK + '.index'))
        os.replace(td, os.path.join(out, PACK + '.data'))
        report[PACK] = readback(PACK, {}, add, [], b'')
        report[PACK]['files'] = len(files)
        assert report[PACK]['under_zip_limit'], report[PACK]

    # 3) Index: the new pack at the end
    if not check:
        ix_path = os.path.join(out, 'Index') if os.path.exists(os.path.join(out, 'Index')) else os.path.join(base, 'Index')
        ix = rd(ix_path)
        lines = [l.strip() for l in ix.replace(b'\r\n', b'\n').split(b'\n')]
        if PACK.encode() not in lines:
            nl = b'\r\n' if b'\r\n' in ix else b'\n'
            ix = ix.rstrip(b'\r\n') + nl + b'*' + nl + PACK.encode() + nl
        if ix != rd(ix_path) or ix_path != os.path.join(out, 'Index'):
            open(os.path.join(out, 'Index'), 'wb').write(ix)
            report['Index'] = 'written'
    print(json.dumps(report, indent=1, ensure_ascii=False))


if __name__ == '__main__':
    main()
