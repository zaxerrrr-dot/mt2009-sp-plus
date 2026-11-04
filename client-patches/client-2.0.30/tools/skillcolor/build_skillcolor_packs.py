# -*- coding: utf-8 -*-
# MT2009_PLUS_SKILL_COLOR_V1 - the client build's part of Kolor umiejetnosci (root uiskillcolor.py, skillcolorpick.py,
# uiscript/skillcolorwindow.py; exe ENABLE_MT2009_SKILL_COLOR; server-patches/skillcolor/README.md):
#   1) a new pack "skillcolor" with the window's two pictures:
#      - d:/ymir work/ui/skillcolor/color_picker.tga - the colour picker, 180 x 120, painted here from root
#        skillcolorpick.ColorAt (the very function the window reads a click with - the colour under the mouse is
#        computed, never read off the screen), a plain 32-bit TGA;
#      - d:/ymir work/ui/skillcolor/color_picker_dot.tga - the mark of the chosen point, the owner's package's 12 x 12
#        color_picker_dot (a PNG named .tga there; src/ has it as a real 32-bit TGA, the same pixels).
#      The package's other pictures (its window backgrounds, the skill window's per-slot buttons, the pet / mailbox /
#      private shop UI that came in its folder) are not used: the window is our board, the button a standard one.
#   2) its line at the end of pack/Index.
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/skillcolor/build_skillcolor_packs.py <BASE pack dir> <OUT pack dir> [--check]
#
# clientY.sh: a pack builder without gamedata / dbdata, after the azbase copy, next to the other 3.x UI packs (after
# quickslot2):
#   S_skillcolor_packs() { docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/skillcolor/build_skillcolor_packs.py \
#     $C/azbase $C/out/pack; }; step skillcolor_packs $C/skillcolor.json S_skillcolor_packs
# then skillcolor/verify_skillcolor.py in the verify loop. A name some other pack of BASE / OUT has stops the build.
# Every entry written is read back. Idempotent.
import json
import os
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', 'root'))
sys.path.insert(0, ROOT)
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
import skillcolorpick as P  # noqa: E402

PACK = 'skillcolor'
SRC = os.path.join(HERE, 'src')
PREFIX = 'd:/ymir work/ui/skillcolor/'
PICKER = PREFIX + 'color_picker.tga'
DOT = PREFIX + 'color_picker_dot.tga'
ZIP_LIMIT = 29 * 1024 * 1024


def ctype(name):
    return 2 if name.endswith(('.txt', '.sub')) else 1


def tga(width, height, pixels):
    """an uncompressed 32-bit TGA, the first row on top; pixels: rows of (r, g, b, a)"""
    out = bytearray(struct.pack('<BBBHHBHHHHBB', 0, 0, 2, 0, 0, 0, 0, 0, width, height, 32, 0x28))
    for row in pixels:
        assert len(row) == width
        for r, g, b, a in row:
            out += bytes((b, g, r, a))
    return bytes(out)


def tga_info(b):
    """(width, height, bits, top-left origin) of an uncompressed true-colour TGA"""
    assert len(b) > 18 and b[2] == 2, 'not an uncompressed true-colour TGA'
    w, h, bits, desc = b[12] | (b[13] << 8), b[14] | (b[15] << 8), b[16], b[17]
    assert len(b) >= 18 + b[0] + w * h * bits // 8, 'short TGA'
    return w, h, bits, bool(desc & 0x20)


def tga_pixel(b, x, y):
    """(r, g, b, a) of a 32-bit TGA at (x, y) from the top"""
    w, h, bits, top = tga_info(b)
    row = y if top else h - 1 - y
    o = 18 + b[0] + (row * w + x) * 4
    return (b[o + 2], b[o + 1], b[o], b[o + 3])


def picker():
    return tga(P.PICKER_WIDTH, P.PICKER_HEIGHT,
               [[P.ColorAt(x, y) + (255,) for x in range(P.PICKER_WIDTH)] for y in range(P.PICKER_HEIGHT)])


def files():
    """the new pack's entries: name -> bytes"""
    dot = open(os.path.join(SRC, 'color_picker_dot.tga'), 'rb').read()
    assert tga_info(dot)[:3] == (12, 12, 32), tga_info(dot)
    pick = picker()
    assert tga_info(pick) == (P.PICKER_WIDTH, P.PICKER_HEIGHT, 32, True)
    return {PICKER: pick, DOT: dot}


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
        tmp_i, tmp_d = os.path.join(out, pack + '.index.sc'), os.path.join(out, pack + '.data.sc')
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
