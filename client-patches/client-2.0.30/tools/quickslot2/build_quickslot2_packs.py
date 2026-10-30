# -*- coding: utf-8 -*-
# MT2009_PLUS_QUICKSLOT_IMPROVE_V1 - the client build's part of the expanded quick slot bar (root uitaskbar.py,
# quickslotstate.py, uiscript/expandedquickslot.py; exe ENABLE_QUICKSLOT_IMPROVE):
#   1) a new pack "quickslot2" with the 15 d:/ymir work/ui/game/taskbar/expanded_quickslot_*.sub of the package
#      (src/, = GF 26.1.11's) and their picture. The players' base pack "etc" has none of them (3.0.6 aborted at game
#      start: "Failed to load image ... expanded_quickslot_bg_top.sub" - the port had checked the exe smoke client's etc).
#      The package's .sub cut their rectangles from "TaskBar.tga" (version 1.0: d:/ymir work/ui/taskbar.tga). The
#      players' etc has its own ui/taskbar.tga for the normal task bar, which we keep: the pack carries the package's
#      512x256 picture as d:/ymir work/ui/game/taskbar/expanded_quickslot_taskbar.tga and its .sub name that file
#      (only their "image" line differs from the package), so no picture of the players' task bar is replaced;
#   2) its line at the end of pack/Index.
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/quickslot2/build_quickslot2_packs.py <BASE pack dir> <OUT pack dir> [--check]
#
# clientY.sh: a pack builder without gamedata / dbdata, after the azbase copy, next to the other 3.x UI packs:
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/quickslot2/build_quickslot2_packs.py $C/azbase $C/out/pack \
#     > $C/quickslot2.json
# then quickslot2/verify_quickslot2.py in the verify loop. A name some other pack of BASE / OUT has stops the build.
# Every entry written is read back. Idempotent.
import json
import os
import re
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
PACK = 'quickslot2'
SRC = os.path.join(HERE, 'src')
PREFIX = 'd:/ymir work/ui/game/taskbar/'
TGA = PREFIX + 'expanded_quickslot_taskbar.tga'
SUB_IMAGE = b'game/taskbar/expanded_quickslot_taskbar.tga'     # version 1.0: "d:/ymir work/ui/" + image
SUBS = ['expanded_quickslot_%s.sub' % s for s in (
    'bg_top', 'bg_middle', 'bg_bottom', 'list_line', 'number_box', 'slot',
    'switch_button_default', 'switch_button_over', 'switch_button_down',
    'show_button_default', 'show_button_over', 'show_button_down',
    'hide_button_default', 'hide_button_over', 'hide_button_down')]
ZIP_LIMIT = 29 * 1024 * 1024


def ctype(name):
    return 2 if name.endswith(('.txt', '.sub')) else 1


def tga_size(b):
    assert len(b) > 18 and b[2] in (2, 10), 'not a true-colour TGA'
    return (b[12] | (b[13] << 8), b[14] | (b[15] << 8))


def sub_fields(b):
    t = dict((k.lower(), v) for k, v in re.findall(rb'(?m)^\s*(\w+)\s+"?([^"\r\n]*)"?\s*$', b))
    return t


def files():
    """the new pack's entries: name -> bytes"""
    tga = open(os.path.join(SRC, 'taskbar.tga'), 'rb').read()
    w, h = tga_size(tga)
    assert (w, h) == (512, 256), (w, h)
    out = {TGA: tga}
    for n in SUBS:
        b = open(os.path.join(SRC, n), 'rb').read()
        f = sub_fields(b)
        assert f.get(b'title', b'').lower() == b'subimage' and f.get(b'version') == b'1.0', n
        assert f[b'image'].lower() == b'taskbar.tga', (n, f[b'image'])
        box = [int(f[k]) for k in (b'left', b'top', b'right', b'bottom')]
        assert 0 <= box[0] < box[2] <= w and 0 <= box[1] < box[3] <= h, (n, box)
        nb, k = re.subn(rb'(?im)^(\s*image\s+)"[^"]*"', lambda m: m.group(1) + b'"' + SUB_IMAGE + b'"', b)
        assert k == 1, n
        out[PREFIX + n] = nb
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
    items = files()
    for k in sorted(items):
        assert k == k.lower(), k
        if k in where:
            raise SystemExit('%s: %s is in %s/%s already' % (PACK, k, where[k][0], where[k][1]))
    report = {}

    def write(pack, add):
        tmp_i, tmp_d = os.path.join(out, pack + '.index.qs'), os.path.join(out, pack + '.data.qs')
        r = packlib.repack_add_typed(None, None, {}, add, tmp_i, tmp_d, tmpl)
        os.replace(tmp_i, os.path.join(out, pack + '.index'))
        os.replace(tmp_d, os.path.join(out, pack + '.data'))
        f, v, nw = m2pack.read_index(os.path.join(out, pack + '.index'))
        nd = rd(os.path.join(out, pack + '.data'))
        got = {}
        for e in nw:
            assert zlib.crc32(nd[e['pos']:e['pos'] + e['size']]) & 0xffffffff == e['dcrc'], (pack, e['name'])
            assert e['fcrc'] == zlib.crc32(e['name'].encode('cp1252')) & 0xffffffff, (pack, e['name'])
            got[e['name']] = m2pack.read_entry(nd, e)
        assert sorted(got) == sorted(add), pack
        for n, (b, c) in add.items():
            assert got[n] == b, (pack, n)
        return dict(old=r[0], added=r[1], replaced=r[2], entries=len(nw), data_mb=round(len(nd) / 1e6, 3),
                    under_zip_limit=len(nd) < ZIP_LIMIT)

    done = [d for d in (base, out) if os.path.exists(os.path.join(d, PACK + '.index'))]
    skip = False
    if done:
        f, v, ents = m2pack.read_index(os.path.join(done[0], PACK + '.index'))
        dat = rd(os.path.join(done[0], PACK + '.data'))
        if dict((e['name'], m2pack.read_entry(dat, e)) for e in ents) == items:
            report[PACK] = 'in base' if done[0] == base else 'in out'
            skip = True
        elif done[0] == out and not check:
            os.remove(os.path.join(out, PACK + '.index'))
            os.remove(os.path.join(out, PACK + '.data'))
        else:
            raise SystemExit('%s is in BASE with other content - drop it from BASE' % PACK)
    if not skip:
        if check:
            report[PACK] = dict(files=len(items), data_mb=round(sum(len(m2pack.encode_entry(b, ctype(k)))
                                                                     for k, b in items.items()) / 1e6, 3))
        else:
            report[PACK] = write(PACK, dict((k, (b, ctype(k))) for k, b in items.items()))
            assert report[PACK]['under_zip_limit'], report[PACK]

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

    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
