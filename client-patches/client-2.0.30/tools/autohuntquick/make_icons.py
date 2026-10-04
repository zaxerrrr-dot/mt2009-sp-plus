# MT2009_PLUS_AUTOHUNT_QUICK_V1: the inventory sidebar's quick start/stop of
# Auto Lowy, root/mt2009_ui/sidebar/autohuntgo_0N.tga (stopped: a green badge
# with a play arrow) and autohuntstop_0N.tga (hunting: a red badge with a
# square), N = 1/2/3 normal/over/down, 32x32 BGRA. The icon is the Auto Lowy
# button's own (client-2.0.28 root/mt2009_ui/sidebar/autohunt_0N.tga) with the
# badge in its lower right corner. Plain Python 3, no PIL
# (tools/tpbookmarks/make_icons.py for the TGA helpers):
#   python3 make_icons.py <dir with autohunt_0N.tga> <client root dir>
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'tpbookmarks'))
import make_icons as tp  # noqa: E402

CX, CY = 23.5, 23.5
R_BADGE = 6.6
R_RIM = 7.8

COLORS = {
    'go': ((40, 150, 50), (110, 220, 110)),
    'stop': ((160, 30, 25), (235, 90, 70)),
}


def inside_play(x, y):
    # A triangle pointing right, its middle a bit right of the badge's.
    px, py = x + 0.5 - CX, y + 0.5 - CY
    return -2.2 <= px <= 3.4 and abs(py) <= (3.4 - px) * 3.2 / 5.6


def inside_square(x, y):
    px, py = x + 0.5 - CX, y + 0.5 - CY
    return abs(px) <= 2.6 and abs(py) <= 2.6


def make(frame, kind, gain):
    dark, light = COLORS[kind]
    glyph = inside_play if kind == 'go' else inside_square
    out = []
    for y in range(32):
        line = []
        for x in range(32):
            fr = frame[y][x]
            d = math.hypot(x + 0.5 - CX, y + 0.5 - CY)
            if d >= R_RIM + 0.5:
                line.append(fr)
                continue
            if d > R_BADGE:
                # A dark rim, blended into the icon at its outer edge.
                k = max(0.0, min(1.0, R_RIM + 0.5 - d))
                rim = (20, 14, 8)
                line.append(tuple(int(round(rim[i] * k + fr[i] * (1 - k))) for i in range(3)) + (max(fr[3], int(255 * k)),))
                continue
            t = max(0.0, 1.0 - d / R_BADGE)
            col = [dark[i] + (light[i] - dark[i]) * t for i in range(3)]
            if glyph(x, y):
                col = [245, 245, 235]
            col = [min(255, max(0, int(round(c * gain)))) for c in col]
            line.append((col[0], col[1], col[2], 255))
        out.append(line)
    return out


if __name__ == '__main__':
    src, root = sys.argv[1], sys.argv[2]
    side = os.path.join(root, 'mt2009_ui', 'sidebar')
    for i, gain in enumerate((1.0, 1.15, 0.8)):
        frame = tp.read_tga(os.path.join(src, 'autohunt_%02d.tga' % (i + 1)))[2]
        for kind in ('go', 'stop'):
            tp.write_tga(os.path.join(side, 'autohunt%s_%02d.tga' % (kind, i + 1)), make(frame, kind, gain))
