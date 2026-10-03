# MT2009_PLUS_TP_BOOKMARKS_V1: the inventory sidebar's "Zapisane pozycje" icon,
# root/mt2009_ui/sidebar/teleport_01/02/03.tga (normal/over/down), 32x32 BGRA.
# The frame is the dungeon button's (mt2009_ui/sidebar/dungeon_0N.tga), the
# middle a scroll (icon/item/22000.tga, the Zwoj Powrotu's icon) over a blue
# glow. Plain Python 3, no PIL:
#   python3 make_icons.py <dungeon_01.tga> <dungeon_02.tga> <dungeon_03.tga> <22000.tga> <out dir>
import math, os, struct, sys

def read_tga(path):
    b = open(path, 'rb').read()
    idlen, itype = b[0], b[2]
    w, h = struct.unpack('<HH', b[12:16]); bpp = b[16]; desc = b[17]
    n = bpp // 8; off = 18 + idlen; px = []
    if itype == 2:
        px = [tuple(b[off + i * n: off + i * n + n]) for i in range(w * h)]
    elif itype == 10:
        while len(px) < w * h:
            c = b[off]; off += 1; cnt = (c & 0x7f) + 1
            if c & 0x80:
                p = tuple(b[off:off + n]); off += n; px.extend([p] * cnt)
            else:
                for _ in range(cnt):
                    px.append(tuple(b[off:off + n])); off += n
    else:
        raise ValueError('tga type %d' % itype)
    rows = [px[r * w:(r + 1) * w] for r in range(h)]
    if not (desc & 0x20):
        rows = rows[::-1]
    return w, h, [[(p[2], p[1], p[0], p[3] if n == 4 else 255) for p in r] for r in rows]

def write_tga(path, rows):
    h = len(rows); w = len(rows[0])
    # top-left origin (descriptor 0x28), as the other sidebar icons
    out = bytearray(struct.pack('<BBBHHBHHHHBB', 0, 0, 2, 0, 0, 0, 0, 0, w, h, 32, 0x28))
    for r in rows:
        for (R, G, B, A) in r:
            out += bytes((B, G, R, A))
    open(path, 'wb').write(bytes(out))

def scaled(rows, size):
    w = len(rows[0]); h = len(rows); out = []
    for y in range(size):
        line = []
        for x in range(size):
            x0, x1 = x * w / size, (x + 1) * w / size
            y0, y1 = y * h / size, (y + 1) * h / size
            acc = [0.0] * 4; tot = 0.0
            for sy in range(int(y0), int(math.ceil(y1))):
                for sx in range(int(x0), int(math.ceil(x1))):
                    wt = (min(x1, sx + 1) - max(x0, sx)) * (min(y1, sy + 1) - max(y0, sy))
                    R, G, B, A = rows[sy][sx]
                    a = A / 255.0
                    acc[0] += R * a * wt; acc[1] += G * a * wt; acc[2] += B * a * wt; acc[3] += a * wt; tot += wt
            a = acc[3]
            line.append((acc[0] / a, acc[1] / a, acc[2] / a, a / tot) if a > 0 else (0, 0, 0, 0))
        out.append(line)
    return out

def make(frame, scroll, gain):
    C = 15.5; R_IN = 10.2; R_OUT = 11.2; S = 20; O = 6
    out = []
    for y in range(32):
        line = []
        for x in range(32):
            d = math.hypot(x - C, y - C)
            fr = frame[y][x]
            if d >= R_OUT:
                line.append(fr); continue
            t = max(0.0, 1.0 - d / R_IN)
            bg = [18 + 40 * t, 40 + 80 * t, 70 + 110 * t]
            if O <= x < O + S and O <= y < O + S:
                r, g, b, a = scroll[y - O][x - O]
                bg = [bg[0] * (1 - a) + r * a, bg[1] * (1 - a) + g * a, bg[2] * (1 - a) + b * a]
            bg = [min(255, max(0, int(round(c * gain)))) for c in bg]
            if d > R_IN:
                k = (d - R_IN) / (R_OUT - R_IN)
                bg = [int(round(bg[i] * (1 - k) + fr[i] * k)) for i in range(3)]
            line.append((bg[0], bg[1], bg[2], 255))
        out.append(line)
    return out

if __name__ == '__main__':
    frames = [read_tga(p)[2] for p in sys.argv[1:4]]
    scroll = scaled(read_tga(sys.argv[4])[2], 20)
    outdir = sys.argv[5]
    for i, gain in enumerate((1.0, 1.2, 0.8)):
        write_tga(os.path.join(outdir, 'teleport_%02d.tga' % (i + 1)), make(frames[i], scroll, gain))
