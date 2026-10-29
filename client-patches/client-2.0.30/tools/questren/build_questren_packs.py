# -*- coding: utf-8 -*-
# MT2009_PLUS_QUEST_RENEWAL_V1 - the client build's part of the renewed quest window (QUEST_RENEWAL 1.0.0.6, (C) 2019
# Owsap Productions; server: server-patches/questren, root: questrenewal.py, uicharacter.py, interfacemodule.py,
# game.py, uiscript/characterwindow.py - they travel in client-2.0.30/root like every root change):
#   1) a new pack "questren": the window's pictures d:/ymir work/ui/quest_re/*.tga (the package's = GF 26.1.11's, kept in
#      this directory, quest_re/): the category bar, its arrows, the 8 category marks, the unread dot, the separator;
#   2) its line at the end of pack/Index.
# The board's frame (d:/ymir work/ui/pattern/border_a_*.tga) is the client's already (pack "minigames"); verify checks it.
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/questren/build_questren_packs.py <BASE pack dir> <OUT pack dir> [--check]
#
# clientY.sh: a pack builder without gamedata / dbdata, so anywhere after the azbase copy; next to the other 3.x UI packs:
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/questren/build_questren_packs.py $C/azbase $C/out/pack \
#     > $C/questren.json
# then questren/verify_questren.py in the verify loop. A name the client has already (BASE, OUT) with the same bytes is
# left out of the new pack ("shared"); with other bytes the build stops. Every entry written is read back. Idempotent.
import json
import os
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
PACK = 'questren'
SRC = os.path.join(HERE, 'quest_re')
PREFIX = 'd:/ymir work/ui/quest_re/'
IMAGES = ('quest_tab_01.tga', 'quest_down.tga', 'quest_up.tga', 'quest_new.tga', 'quest_list_line_01.tga',
          'tabcolor_1_main.tga', 'tabcolor_2_sub.tga', 'tabcolor_3_levelup.tga', 'tabcolor_4_event.tga',
          'tabcolor_5_collection.tga', 'tabcolor_6_system.tga', 'tabcolor_7_scroll.tga', 'tabcolor_8_daily.tga')
# the root's images (questrenewal.py) with their sizes - verify_questren.py checks them
SIZES = {'quest_tab_01.tga': (222, 17), 'quest_down.tga': (14, 13), 'quest_up.tga': (14, 13), 'quest_new.tga': (7, 7),
         'quest_list_line_01.tga': (216, 5)}
TEXT = ('.txt', '.sub')
ZIP_LIMIT = 29 * 1024 * 1024


def ctype(name):
    return 2 if name.endswith(TEXT) else 1


def tga_size(b):
    """(width, height) of an uncompressed / RLE true-colour TGA"""
    assert len(b) > 18 and b[2] in (2, 10), 'not a true-colour TGA'
    return (b[12] | (b[13] << 8), b[14] | (b[15] << 8))


def files():
    """the new pack's entries: name -> bytes"""
    out = {}
    for n in IMAGES:
        b = open(os.path.join(SRC, n), 'rb').read()
        w, h = tga_size(b)
        if n in SIZES:
            assert (w, h) == SIZES[n], (n, w, h)
        elif n.startswith('tabcolor_'):
            assert (w, h) == (15, 5), (n, w, h)
        out[PREFIX + n] = b
    return out


def main():
    import m2pack
    import packlib
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    check = '--check' in sys.argv
    base, out = args[:2]
    rd = packlib.rd
    where = {}
    for d in (base, out):
        if not os.path.isdir(d):
            continue
        for p in sorted(f[:-6] for f in os.listdir(d) if f.endswith('.index')):
            if p == PACK:
                continue
            for e in m2pack.read_index(os.path.join(d, p + '.index'))[2]:
                where.setdefault(e['name'], (d, p, e))
    tmpl = m2pack.read_index(os.path.join(base, 'az_mobs.index'))[2][-1]['raw']
    datcache = {}

    def entry_bytes(d, p, e):
        if (d, p) not in datcache:
            datcache[(d, p)] = rd(os.path.join(d, p + '.data'))
        return m2pack.read_entry(datcache[(d, p)], e)

    report = {}

    def write(pack, add):
        tmp_i, tmp_d = os.path.join(out, pack + '.index.qr'), os.path.join(out, pack + '.data.qr')
        r = packlib.repack_add_typed(None, None, {}, add, tmp_i, tmp_d, tmpl)
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
        for n, (b, c) in add.items():
            assert got[n] == b, (pack, n)
        assert sorted(got) == sorted(add), pack
        return dict(old=r[0], added=r[1], replaced=r[2], entries=len(nw), data_mb=round(len(nd) / 1e6, 3),
                    under_zip_limit=len(nd) < ZIP_LIMIT)

    # 1) the new pack
    items, shared = {}, []
    for k, b in sorted(files().items()):
        if k in where:
            if entry_bytes(*where[k]) != b:
                raise SystemExit('%s: %s is in %s/%s with other bytes' % (PACK, k, where[k][0], where[k][1]))
            shared.append(k)
            continue
        assert k == k.lower(), k
        items[k] = b
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
        if not items:
            report[PACK] = dict(files=0, shared=len(shared), note='every picture is in the client already')
        elif check:
            size = sum(len(m2pack.encode_entry(b, ctype(k))) for k, b in items.items())
            report[PACK] = dict(files=len(items), shared=len(shared), data_mb=round(size / 1e6, 3))
        else:
            report[PACK] = write(PACK, dict((k, (b, ctype(k))) for k, b in items.items()))
            report[PACK]['shared'] = shared
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

    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
