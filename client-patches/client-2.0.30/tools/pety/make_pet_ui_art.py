#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MT2009_PLUS_PET_WINDOW_LAYOUT_V2 - the pet window's buttons and tabs with room for their text.

The official 26.1.11 art draws a big emblem in the middle of the three mode buttons (normal / champion / potential,
106 x 20) and of the three page tabs (tab_1..3.tga, 352 x 48): a text set on them ends up over the emblem. This makes,
from the same GF pictures,

  root/mt2009_ui/pet/{normal,conqueror,potential}_bt_{default,over,down}.tga
      the emblem moved to the button's left end, the middle cleared (plain columns of the same button) for the text;
  root/mt2009_ui/pet/tab_1.tga .. tab_3.tga
      the three plates without their emblem (plain columns of the same plate), for the text the window sets.

The result is committed (the client build only packs it with the rest of root). Needs Pillow:

    python3 make_pet_ui_art.py [<GF client dir>]      (default /opt/metin2/cache/gf/Gameforge_26.1.11/_client)
"""
import os
import re
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, '..', '..', 'root', 'mt2009_ui', 'pet'))
GF = sys.argv[1] if len(sys.argv) > 1 else '/opt/metin2/cache/gf/Gameforge_26.1.11/_client'
UI = os.path.join(GF, 'd_', 'ymir work', 'ui')

# the emblem's columns in the 106 x 20 buttons, where it goes (x) and the plain columns that fill its old place
EMBLEM = {'normal': (40, 66), 'conqueror': (40, 66), 'potential': (37, 69)}
EMBLEM_X = 4
TAB_PLATE_X = (13, 107, 201)	# the plates' left edge in tab_N.tga (the Tab_Button_0N positions)
TAB_PLATE_Y = (8, 39)
TAB_EMBLEM = (17, 61)		# the emblem's columns in a plate (from its left edge)
TAB_PLAIN = (8, 17)		# plain columns between the left rivets and the emblem


def sub(path):
    """the picture a GF .sub names, cropped"""
    t = open(path).read()
    g = lambda k: int(re.search(k + r'\s+(-?\d+)', t).group(1))
    img = re.search(r'image\s+"([^"]+)"', t).group(1)
    sheet = Image.open(os.path.join(UI, img)).convert('RGBA')
    return sheet.crop((g('left'), g('top'), g('right'), g('bottom')))


def fill_columns(im, x0, x1, src_cols, y0=0, y1=None):
    """columns x0..x1-1 (rows y0..y1-1) from src_cols, back and forth, so no seam repeats"""
    y1 = im.height if y1 is None else y1
    seq = list(src_cols) + list(reversed(src_cols))
    for i, x in enumerate(range(x0, x1)):
        sx = seq[i % len(seq)]
        im.paste(im.crop((sx, y0, sx + 1, y1)), (x, y0))


def button(kind, state):
    im = sub(os.path.join(UI, 'pet', 'conqueror', '%s_bt_%s.sub' % (kind, state)))
    e0, e1 = EMBLEM[kind]
    emblem = im.crop((e0, 0, e1, im.height))
    w = e1 - e0
    # the plain right part of the button (no emblem, no end cap) fills the middle and the emblem's new place
    plain = range(e1 + 8, im.width - 6)
    fill_columns(im, EMBLEM_X, e1 + 2, plain)
    # the emblem's own columns hold the button's top / bottom edge: take only its middle rows over the plain bar
    im.alpha_composite(emblem.crop((0, 2, w, im.height - 2)), (EMBLEM_X, 2))
    return im


def tab(n):
    im = Image.open(os.path.join(UI, 'pet', 'res', 'tab_%d.tga' % n)).convert('RGBA')
    for px in TAB_PLATE_X:
        fill_columns(im, px + TAB_EMBLEM[0], px + TAB_EMBLEM[1], range(px + TAB_PLAIN[0], px + TAB_PLAIN[1]),
                     TAB_PLATE_Y[0], TAB_PLATE_Y[1])
    return im


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    names = []
    for kind in ('normal', 'conqueror', 'potential'):
        for state in ('default', 'over', 'down'):
            name = '%s_bt_%s.tga' % (kind, state)
            button(kind, state).save(os.path.join(OUT, name))
            names.append(name)
    for n in (1, 2, 3):
        name = 'tab_%d.tga' % n
        tab(n).save(os.path.join(OUT, name))
        names.append(name)
    print('%d pictures in %s' % (len(names), OUT))


if __name__ == '__main__':
    main()
