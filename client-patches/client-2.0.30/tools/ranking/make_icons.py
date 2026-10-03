# MT2009_PLUS_WEEKLY_RANKING_V1: the inventory sidebar's "Ranking" icon,
# root/mt2009_ui/sidebar/ranking_01/02/03.tga (normal/over/down), 32x32 BGRA,
# and the window's images, root/mt2009_ui/ranking/ (copied from the Arezzo
# files' weekly rank window, "d:/ymir work/ui/new_weekly_rank/"). The icon's
# frame is the dungeon button's (mt2009_ui/sidebar/dungeon_0N.tga), the middle
# the crown of Arezzo's image-example-005.png over a golden glow. Plain Python 3,
# no PIL (tools/tpbookmarks/make_icons.py for the TGA helpers):
#   python3 make_icons.py <arezzo new_weekly_rank dir> <client root dir>
import math
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'tpbookmarks'))
import make_icons as tp  # noqa: E402  (tools/tpbookmarks/make_icons.py)
import pngread  # noqa: E402

COPY = {
    'box-1.png': 'row_1.png', 'box-2.png': 'row_2.png', 'box-3.png': 'row_3.png', 'box-4.png': 'row_4.png',
    'title_box-1.png': 'title_1.png', 'title_box-2.png': 'title_2.png', 'title_box-3.png': 'title_3.png',
    'title_box-4.png': 'title_4.png',
    'image-example-005.png': 'crown_1.png', 'image-example-006.png': 'crown_2.png',
    'image-example-007.png': 'crown_3.png',
    'header_big_new.png': 'header_big.png', 'header_small_new.png': 'header_small.png',
    'button_new1.tga': 'cat_0.tga', 'button_new2.tga': 'cat_2.tga', 'button_new3.tga': 'cat_1.tga',
}


def crown(src):
    w, h, rows = pngread.read_png(os.path.join(src, 'image-example-005.png'))
    # the crown, without the coin beside it
    return [[rows[y][x] for x in range(2, 19)] for y in range(2, 21)]


def make(frame, art, gain):
    C = 15.5
    R_IN = 10.2
    R_OUT = 11.2
    aw, ah = len(art[0]), len(art)
    ox, oy = int(round(C - aw / 2.0 + 0.5)), int(round(C - ah / 2.0 + 0.5))
    out = []
    for y in range(32):
        line = []
        for x in range(32):
            d = math.hypot(x - C, y - C)
            fr = frame[y][x]
            if d >= R_OUT:
                line.append(fr)
                continue
            t = max(0.0, 1.0 - d / R_IN)
            bg = [60 + 90 * t, 40 + 70 * t, 10 + 20 * t]
            if ox <= x < ox + aw and oy <= y < oy + ah:
                r, g, b, a = art[y - oy][x - ox]
                a = a / 255.0
                bg = [bg[0] * (1 - a) + r * a, bg[1] * (1 - a) + g * a, bg[2] * (1 - a) + b * a]
            bg = [min(255, max(0, int(round(c * gain)))) for c in bg]
            if d > R_IN:
                k = (d - R_IN) / (R_OUT - R_IN)
                bg = [int(round(bg[i] * (1 - k) + fr[i] * k)) for i in range(3)]
            line.append((bg[0], bg[1], bg[2], 255))
        out.append(line)
    return out


if __name__ == '__main__':
    src, root = sys.argv[1], sys.argv[2]
    side = os.path.join(root, 'mt2009_ui', 'sidebar')
    frames = [tp.read_tga(os.path.join(side, 'dungeon_%02d.tga' % i))[2] for i in (1, 2, 3)]
    art = crown(src)
    for i, gain in enumerate((1.0, 1.2, 0.8)):
        tp.write_tga(os.path.join(side, 'ranking_%02d.tga' % (i + 1)), make(frames[i], art, gain))
    dst = os.path.join(root, 'mt2009_ui', 'ranking')
    if not os.path.isdir(dst):
        os.makedirs(dst)
    for a, b in sorted(COPY.items()):
        shutil.copyfile(os.path.join(src, a), os.path.join(dst, b))
