# MT2009_PLUS_WEEKLY_RANKING_V1: a plain-Python reader of 8-bit RGBA PNGs
# (no PIL), for make_icons.py.
import struct
import zlib


def read_png(path):
    b = open(path, 'rb').read()
    assert b[:8] == b'\x89PNG\r\n\x1a\n', path
    w, h, depth, ctype = struct.unpack('>IIBB', b[16:26])
    assert depth == 8 and ctype == 6, (path, depth, ctype)
    i = 8
    idat = b''
    while i < len(b):
        n = struct.unpack('>I', b[i:i + 4])[0]
        if b[i + 4:i + 8] == b'IDAT':
            idat += b[i + 8:i + 8 + n]
        i += 12 + n
    raw = zlib.decompress(idat)
    stride = w * 4
    rows = []
    prev = bytearray(stride)
    p = 0
    for _ in range(h):
        f = raw[p]
        line = bytearray(raw[p + 1:p + 1 + stride])
        p += 1 + stride
        for x in range(stride):
            a = line[x - 4] if x >= 4 else 0
            up = prev[x]
            c = prev[x - 4] if x >= 4 else 0
            if f == 1:
                line[x] = (line[x] + a) & 255
            elif f == 2:
                line[x] = (line[x] + up) & 255
            elif f == 3:
                line[x] = (line[x] + (a + up) // 2) & 255
            elif f == 4:
                pa, pb, pc = abs(up - c), abs(a - c), abs(a + up - 2 * c)
                pr = a if pa <= pb and pa <= pc else (up if pb <= pc else c)
                line[x] = (line[x] + pr) & 255
        rows.append([tuple(line[x:x + 4]) for x in range(0, stride, 4)])
        prev = line
    return w, h, rows
