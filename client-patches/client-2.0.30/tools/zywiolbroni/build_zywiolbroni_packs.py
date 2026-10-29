# -*- coding: utf-8 -*-
# MT2009_PLUS_WEAPON_ELEMENT_V1 - the client build's part for Zaczarowanie Żywiołu Broni (server-patches/zywiolbroni):
#   1) a new pack "zywiolbroni" with what the GF 26.1.11 client has and ours does not:
#      - the weapon element effects d:/ymir work/pc/common/effect/sword/element01_electric .. element06_dark (+ _f, _b,
#        _s, _w: the exe's sword/two-handed, fan, bell, bow, dagger, claw parts - welemfx.py registers them) with the
#        textures they name (gf28/gfres.closure: effect/hit/blow_*, effect/monster2/*);
#      - the Zwój Zmiany window's buttons: d:/ymir work/ui/welem/long_button_01/02/03/disable.sub and
#        number_input_area.sub - GF's ui/event/*.sub of those names (the same rectangles) over
#        d:/ymir work/ui/welem_event_001.dds = GF's ui/event_001.dds; their own names, so the minigames pack's
#        ui/event/*.sub and any older event_001.dds stay as they are (uiscript/weaponelementchange.py names these);
#      a name our packs (BASE, OUT, gf28/ourpacks_pre.txt) have already is left out - ours is kept;
#      - Stróż Medali 20650's GF model, the folder d:/ymir work/npc/scholar_brown_m (MODEL_DIR);
#   2) its line at the end of pack/Index;
#   3) the existing packs "gamedata" (gamedata/item_list.txt, gamedata/mob_proto) and "dbdata" (gamedata/item_proto,
#      locale/pl/itemdesc.txt) - patch_zywiolbroni_client.py: the scrolls 56002-56009 and Stróż Medali 20650.
# The scrolls' icons (root/icon/item/56002-56009.tga, GF = the package's), root/welem.py, root/uiweaponelement.py,
# root/welemfx.py and the two uiscript files travel in client-2.0.30/root like every root change.
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/zywiolbroni/build_zywiolbroni_packs.py <BASE pack dir> <OUT pack dir> [--check]
#
# clientY.sh: after the czepiec line (it patches gamedata and dbdata too; on the same OUT a pack already there - an
# earlier step changed it - is the one patched):
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/zywiolbroni/build_zywiolbroni_packs.py $C/azbase \
#     $C/out/pack > $C/zywiolbroni.json
# then zywiolbroni/verify_zywiolbroni.py in the verify loop. Every entry written is read back. Idempotent.
import json
import os
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, '/opt/metin2/cache/tcm/gf28')
sys.path.insert(0, HERE)
PACK = 'zywiolbroni'
GF_UI = '/opt/metin2/cache/gf/Gameforge_26.1.11/_client/d_/ymir work/ui'
OURS_PRE = '/opt/metin2/cache/tcm/gf28/ourpacks_pre.txt'
ELEMENTS = ('01_electric', '02_fire', '03_ice', '04_wind', '05_daeji', '06_dark')
PARTS = ('', '_f', '_b', '_s', '_w')
EFFECTS = ['d:/ymir work/pc/common/effect/sword/element%s%s.mse' % (e, p) for e in ELEMENTS for p in PARTS]
# Stróż Medali 20650's model (npclist: scholar_brown_M1 -> the folder scholar_brown_M): the base packs npc/npc2 are not
# on the VPS, so whether our client has it cannot be proved - the GF race folder goes in (msm, gr2 with the motions of
# its motlist, dds; gfres.closure of the folder), minus what our packs provably have
MODEL_DIR = 'd:/ymir work/npc/scholar_brown_m/'
MODEL = [MODEL_DIR + n for n in ('scholar_brown_m.msm', 'scholar_brown_m1.msm', 'scholar_brown_m.gr2', 'motlist.txt',
                                 'wait.msa', 'wait.gr2', 'walk.msa', 'walk.gr2', 'run.msa', 'run.gr2', 'dead.msa',
                                 'dead.gr2', 'scholar_brown_m1.dds')]
UI_SUBS = ('long_button_01', 'long_button_02', 'long_button_03', 'long_button_disable', 'number_input_area')
UI_DIR = 'd:/ymir work/ui/welem/'
UI_DDS = 'd:/ymir work/ui/welem_event_001.dds'
TEXT = ('.txt', '.sub', '.mse', '.msm', '.msa')
ZIP_LIMIT = 29 * 1024 * 1024


def ctype(name):
    return 2 if name.endswith(TEXT) else 1


def ui_files():
    """the change window's buttons: GF's .sub rectangles over our own copy of event_001.dds"""
    out = {}
    for n in UI_SUBS:
        src = open(os.path.join(GF_UI, 'event', n + '.sub'), 'rb').read()
        assert b'"event_001.dds"' in src, n
        out[UI_DIR + n + '.sub'] = src.replace(b'"event_001.dds"', b'"welem_event_001.dds"')
    dds = open(os.path.join(GF_UI, 'event_001.dds'), 'rb').read()
    assert dds[:4] == b'DDS ', 'event_001.dds'
    out[UI_DDS] = dds
    return out


def effect_files(ours):
    """the effects and their closure in the GF client; (files, kept ours)"""
    import gfres
    files, unresolved, ours_hit = gfres.closure(EFFECTS + [MODEL_DIR], ours)
    assert not unresolved, unresolved
    for k in EFFECTS + MODEL:
        assert k in files, k
    got = {}
    for k, src in files.items():
        if k in ours:
            continue
        got[k] = open(src, 'rb').read()
    return got, sorted(ours_hit)


def our_names(base, out):
    import m2pack
    where = {}
    for d in (base, out):
        if not os.path.isdir(d):
            continue
        for p in sorted(f[:-6] for f in os.listdir(d) if f.endswith('.index')):
            if p == PACK:
                continue
            for e in m2pack.read_index(os.path.join(d, p + '.index'))[2]:
                where.setdefault(e['name'].lower(), (d, p, e))
    return where


def files(base, out):
    """the new pack's entries (name -> bytes) and the names left to our packs"""
    import gfres
    where = our_names(base, out)
    ours = set(where) | (gfres.load_ours(OURS_PRE) if os.path.exists(OURS_PRE) else set())
    eff, kept = effect_files(ours)
    allf = dict(eff)
    for k, b in ui_files().items():
        if k in ours:
            kept.append(k)
            continue
        allf[k] = b
    for k in allf:
        assert k == k.lower(), k
    return allf, sorted(set(kept))


def main():
    import m2pack
    import packlib
    import patch_zywiolbroni_client as pc
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    check = '--check' in sys.argv
    base, out = args[:2]
    rd = packlib.rd
    tmpl_ix = [os.path.join(d, p) for d in (base, out) if os.path.isdir(d)
               for p in (['az_mobs.index'] + sorted(os.listdir(d))) if p.endswith('.index') and
               os.path.exists(os.path.join(d, p)) and p != PACK + '.index']
    tmpl = m2pack.read_index(tmpl_ix[0])[2][-1]['raw']          # an entry header of the packs (az_mobs, as addeq)

    def src_of(pack):
        return out if os.path.exists(os.path.join(out, pack + '.index')) else base

    report = {}

    def write(pack, src, rep, add, ents, dat):
        tmp_i, tmp_d = os.path.join(out, pack + '.index.zb'), os.path.join(out, pack + '.data.zb')
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
    items, kept = files(base, out)
    done = [d for d in (base, out) if os.path.exists(os.path.join(d, PACK + '.index'))]
    skip = False
    if done:
        f, v, ents = m2pack.read_index(os.path.join(done[0], PACK + '.index'))
        dat = rd(os.path.join(done[0], PACK + '.data'))
        have = dict((e['name'], m2pack.read_entry(dat, e)) for e in ents)
        if have == items:
            report[PACK] = 'in base' if done[0] == base else 'in out'
            skip = True
        elif done[0] == out and not check:
            os.remove(os.path.join(out, PACK + '.index'))
            os.remove(os.path.join(out, PACK + '.data'))
        else:
            raise SystemExit('%s is in BASE with other content - drop it from BASE' % PACK)
    if not skip:
        if check:
            size = sum(len(m2pack.encode_entry(b, ctype(k))) for k, b in items.items())
            report[PACK] = dict(files=len(items), kept_ours=kept, data_mb=round(size / 1e6, 2))
        else:
            report[PACK] = write(PACK, None, {}, dict((k, (b, ctype(k))) for k, b in items.items()), [], b'')
            report[PACK]['kept_ours'] = kept
            assert report[PACK]['under_zip_limit'], report[PACK]

    # 2) Index: the new pack at the end
    if not check:
        ix_path = os.path.join(out, 'Index') if os.path.exists(os.path.join(out, 'Index')) else os.path.join(base, 'Index')
        ix = rd(ix_path)
        lines = [l.strip() for l in ix.replace(b'\r\n', b'\n').split(b'\n')]
        if PACK.encode() not in lines and (os.path.exists(os.path.join(out, PACK + '.index')) or
                                           os.path.exists(os.path.join(base, PACK + '.index'))):
            ix = ix.rstrip(b'\r\n') + b'\n*\n' + PACK.encode() + b'\n'
        if ix != rd(ix_path) or ix_path != os.path.join(out, 'Index'):
            open(os.path.join(out, 'Index'), 'wb').write(ix)
            report['Index'] = 'written'

    # 3) gamedata and dbdata: the scrolls and Stróż Medali
    jobs = {'gamedata': [('gamedata/item_list.txt', pc.item_list), ('gamedata/mob_proto', pc.mob_proto)],
            'dbdata': [('gamedata/item_proto', pc.item_proto), ('locale/pl/itemdesc.txt', pc.itemdesc)]}
    for pack, jfiles in sorted(jobs.items()):
        src = src_of(pack)
        f, v, ents = m2pack.read_index(os.path.join(src, pack + '.index'))
        dat = rd(os.path.join(src, pack + '.data'))
        have = dict((e['name'], e) for e in ents)
        rep = {}
        for n, fn in jfiles:
            if n not in have:
                raise SystemExit('%s: %s is not in the pack' % (pack, n))
            b = m2pack.read_entry(dat, have[n])
            nb, changed = fn(b)
            if nb != b:
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
