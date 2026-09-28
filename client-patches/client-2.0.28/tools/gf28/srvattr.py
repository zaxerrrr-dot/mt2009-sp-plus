# server_attr <-> client attr.atr tools (MT2009 2.0.28)
import struct, os, sys, lzo
SEC = 128  # server cells per sectree (6400/50)
def read_server(path):
    b = open(path, 'rb').read(); w, h = struct.unpack_from('<2i', b, 0); o = 8; secs = []
    for i in range(w * h):
        n = struct.unpack_from('<i', b, o)[0]; o += 4
        raw = lzo.decompress(b[o:o + n], False, SEC * SEC * 4); o += n
        secs.append(struct.unpack('<%dI' % (SEC * SEC), raw))
    assert o == len(b)
    return w, h, secs
def grid_from_server(w, h, secs):
    W, H = w * SEC, h * SEC; g = bytearray(W * H)
    for sy in range(h):
        for sx in range(w):
            s = secs[sy * w + sx]
            for y in range(SEC):
                row = (sy * SEC + y) * W + sx * SEC
                for x in range(SEC):
                    g[row + x] = s[y * SEC + x] & 0xff
    return W, H, g
def grid_from_client(mapdir, mw, mh, flip=False):
    # client: sector XXXYYY, attr.atr 256x256 cells of 100 units -> server 2x2 cells of 50
    W, H = mw * 512, mh * 512; g = bytearray(W * H)
    for cy in range(mh):
        for cx in range(mw):
            p = os.path.join(mapdir, '%03d%03d' % (cx, cy), 'attr.atr')
            b = open(p, 'rb').read(); mg, aw, ah = struct.unpack_from('<3H', b, 0); assert (aw, ah) == (256, 256), p
            d = b[6:]
            for y in range(256):
                yy = 255 - y if flip else y
                for x in range(256):
                    v = d[yy * 256 + x]
                    if v:
                        gx = cx * 512 + x * 2; gy = cy * 512 + y * 2
                        for dy in (0, 1):
                            o = (gy + dy) * W + gx
                            g[o] = v; g[o + 1] = v
    return W, H, g
def write_server(path, W, H, g):
    w, h = W // SEC, H // SEC; out = bytearray(struct.pack('<2i', w, h))
    for sy in range(h):
        for sx in range(w):
            vals = []
            for y in range(SEC):
                row = (sy * SEC + y) * W + sx * SEC
                vals.extend(g[row:row + SEC])
            raw = struct.pack('<%dI' % (SEC * SEC), *vals)
            c = lzo.compress(raw, 1, False)
            out += struct.pack('<i', len(c)) + c
    open(path, 'wb').write(bytes(out))
