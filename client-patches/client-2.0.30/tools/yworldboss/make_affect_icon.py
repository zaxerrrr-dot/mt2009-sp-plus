# -*- coding: utf-8 -*-
# MT2009_PLUS_WORLDBOSS_V1 - the affect icon of Boss Swiata's two buffs (the server's affects 720 - drop, 721 -
# "Pokonaj Bossa Swiata" attack; root/uiaffectbar.py): the pl-wiki's 32x32 "Boss Swiata Ikona.png" (copy in
# /opt/metin2/cache/yohara/wiki/worldboss/) as an uncompressed 32-bit TGA (bottom-up, BGRA) like the other
# root/mt2009_ui/affect/*.tga. Pure python (zlib + the PNG filters), no PIL.
#
#   python3 make_affect_icon.py [<png>] [<tga>]
import os
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else '/opt/metin2/cache/yohara/wiki/worldboss/Boss_Świata_Ikona.png'
DST = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, '..', '..', 'root', 'mt2009_ui', 'affect', 'worldboss.tga')


def png_rgba(path):
    b = open(path, 'rb').read()
    assert b[:8] == b'\x89PNG\r\n\x1a\n'
    i, idat, w = 8, b'', None
    while i < len(b):
        n, t = struct.unpack('>I4s', b[i:i + 8])
        d = b[i + 8:i + 8 + n]
        if t == b'IHDR':
            w, h, depth, ctype, comp, filt, inter = struct.unpack('>IIBBBBB', d)
            assert depth == 8 and ctype == 6 and inter == 0, (depth, ctype, inter)
        elif t == b'IDAT':
            idat += d
        i += 12 + n
    raw = zlib.decompress(idat)
    bpp, stride = 4, w * 4
    rows, prev, p = [], bytearray(stride), 0
    for y in range(h):
        f = raw[p]
        line = bytearray(raw[p + 1:p + 1 + stride])
        p += 1 + stride
        for x in range(stride):
            a = line[x - bpp] if x >= bpp else 0
            up = prev[x]
            c = prev[x - bpp] if x >= bpp else 0
            if f == 1:
                line[x] = (line[x] + a) & 255
            elif f == 2:
                line[x] = (line[x] + up) & 255
            elif f == 3:
                line[x] = (line[x] + ((a + up) >> 1)) & 255
            elif f == 4:
                pa, pb, pc = abs(up - c), abs(a - c), abs(a + up - 2 * c)
                pr = a if pa <= pb and pa <= pc else (up if pb <= pc else c)
                line[x] = (line[x] + pr) & 255
        rows.append(bytes(line))
        prev = line
    return w, h, rows


def main():
    w, h, rows = png_rgba(SRC)
    out = bytearray(struct.pack('<BBBHHBHHHHBB', 0, 0, 2, 0, 0, 0, 0, 0, w, h, 32, 8))
    for row in reversed(rows):
        for x in range(w):
            r, g, b_, a = row[x * 4:x * 4 + 4]
            out += bytes((b_, g, r, a))
    os.makedirs(os.path.dirname(os.path.abspath(DST)), exist_ok=True)
    open(DST, 'wb').write(bytes(out))
    print('%s: %dx%d, %d bytes' % (DST, w, h, len(out)))


if __name__ == '__main__':
    main()
