# Minimal DDS DXT1 decode/encode (pure python) for the big-map atlas images.
import struct
def _c565(v):
    r = (v >> 11) & 31; g = (v >> 5) & 63; b = v & 31
    return ((r << 3) | (r >> 2), (g << 2) | (g >> 4), (b << 3) | (b >> 2))
def read_dds(path):
    b = open(path, 'rb').read()
    assert b[:4] == b'DDS '
    h, w = struct.unpack_from('<II', b, 12); four = b[84:88]; bits = struct.unpack_from('<I', b, 88)[0]
    px = [[(0, 0, 0)] * w for _ in range(h)]
    o = 128
    if four == b'DXT1':
        for by in range(0, h, 4):
            for bx in range(0, w, 4):
                c0, c1, idx = struct.unpack_from('<HHI', b, o); o += 8
                a, bb = _c565(c0), _c565(c1)
                if c0 > c1: pal = [a, bb, tuple((2 * x + y) // 3 for x, y in zip(a, bb)), tuple((x + 2 * y) // 3 for x, y in zip(a, bb))]
                else: pal = [a, bb, tuple((x + y) // 2 for x, y in zip(a, bb)), (0, 0, 0)]
                for i in range(16):
                    y, x = by + i // 4, bx + i % 4
                    if y < h and x < w: px[y][x] = pal[(idx >> (2 * i)) & 3]
    elif four == b'\0\0\0\0' and bits == 32:
        for y in range(h):
            for x in range(w):
                B, G, R, A = b[o:o + 4]; o += 4; px[y][x] = (R, G, B)
    else:
        raise ValueError('unsupported dds %r %d' % (four, bits))
    return w, h, px
def _p565(c):
    r, g, b = c
    return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)
def write_dxt1(path, w, h, px):
    out = bytearray(b'DDS ')
    hdr = struct.pack('<7I', 124, 0x1 | 0x2 | 0x4 | 0x1000 | 0x80000, h, w, w * h // 2, 0, 0) + b'\0' * 44
    hdr += struct.pack('<2I4s5I', 32, 0x4, b'DXT1', 0, 0, 0, 0, 0) + struct.pack('<5I', 0x1000, 0, 0, 0, 0)
    out += hdr; assert len(out) == 128
    for by in range(0, h, 4):
        for bx in range(0, w, 4):
            blk = [px[by + i // 4][bx + i % 4] for i in range(16)]
            lum = [r * 3 + g * 6 + b for r, g, b in blk]
            hi = blk[lum.index(max(lum))]; lo = blk[lum.index(min(lum))]
            c0, c1 = _p565(hi), _p565(lo)
            if c0 < c1: c0, c1 = c1, c0; hi, lo = lo, hi
            if c0 == c1:
                out += struct.pack('<HHI', c0, c1, 0); continue
            a, bb = _c565(c0), _c565(c1)
            pal = [a, bb, tuple((2 * x + y) // 3 for x, y in zip(a, bb)), tuple((x + 2 * y) // 3 for x, y in zip(a, bb))]
            idx = 0
            for i, p in enumerate(blk):
                best = min(range(4), key=lambda j: sum((p[k] - pal[j][k]) ** 2 for k in range(3)))
                idx |= best << (2 * i)
            out += struct.pack('<HHI', c0, c1, idx)
    open(path, 'wb').write(bytes(out))
def downscale(w, h, px, nw, nh):
    fx, fy = w // nw, h // nh
    res = []
    for y in range(nh):
        row = []
        for x in range(nw):
            s = [0, 0, 0]
            for yy in range(y * fy, y * fy + fy):
                r = px[yy]
                for xx in range(x * fx, x * fx + fx):
                    p = r[xx]; s[0] += p[0]; s[1] += p[1]; s[2] += p[2]
            n = fx * fy; row.append((s[0] // n, s[1] // n, s[2] // n))
        res.append(row)
    return res
def stitch(mapdir, mw, mh, sub='minimap.dds'):
    import os
    W = H = None; big = None
    for cy in range(mh):
        for cx in range(mw):
            w, h, px = read_dds(os.path.join(mapdir, '%03d%03d' % (cx, cy), sub))
            if big is None: W, H = w * mw, h * mh; big = [[(0, 0, 0)] * W for _ in range(H)]
            for y in range(h): big[cy * h + y][cx * w:cx * w + w] = px[y]
    return W, H, big
