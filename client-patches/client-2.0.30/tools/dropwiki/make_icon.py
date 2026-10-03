# MT2009_PLUS_DROP_WIKI_V1: the inventory sidebar's "Drop wiki" icon,
# root/mt2009_ui/sidebar/dropwiki_01/02/03.tga (normal/over/down), 32x32 BGRA:
# the dungeon button's frame (as tools/ranking/make_icons.py) with the
# Moonlight Treasure Box (icon/item/50011.tga of the GF client) in the middle.
# Needs Pillow for the box's downscale:
#   python3 make_icon.py <icon/item/50011.tga> <client root dir>
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'ranking'))
sys.path.insert(0, os.path.join(HERE, '..', 'tpbookmarks'))
import make_icons as tp  # noqa: E402  (tools/tpbookmarks/make_icons.py)
from PIL import Image  # noqa: E402

RANKING = os.path.join(HERE, '..', 'ranking', 'make_icons.py')
ns = {'__name__': 'ranking_make', '__file__': RANKING}
exec(open(RANKING).read(), ns)

if __name__ == '__main__':
    box, root = sys.argv[1], sys.argv[2]
    im = Image.open(box).convert('RGBA').resize((20, 20), Image.LANCZOS)
    art = [[im.getpixel((x, y)) for x in range(20)] for y in range(20)]
    side = os.path.join(root, 'mt2009_ui', 'sidebar')
    frames = [tp.read_tga(os.path.join(side, 'dungeon_%02d.tga' % i))[2] for i in (1, 2, 3)]
    for i, gain in enumerate((1.0, 1.2, 0.8)):
        tp.write_tga(os.path.join(side, 'dropwiki_%02d.tga' % (i + 1)), ns['make'](frames[i], art, gain))
