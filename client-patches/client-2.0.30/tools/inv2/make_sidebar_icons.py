# MT2009_PLUS_INVENTORY_V2_V2 - two inventory side bar icons (uiinventory.py SidebarWindow, the owner's 3.0.6 tests):
#   root/mt2009_ui/sidebar/offlineshop_01/02/03.tga    "Sklep" (the own offline shop): a bundle - the Tobolek's
#                                                      item icon (icon/item/50200.tga, the private shop bundle)
#   root/mt2009_ui/sidebar/chestpreview_01/02/03.tga   "Podglad skrzyn": a wooden chest (icon/item/38050.tga)
# 32x32 BGRA, normal / over / down, the octagon frame of the side bar's first icons (client-2.0.28 trash_0N.tga), its
# inside filled with that icon's own brown and the item icon over it. Plain Python 3, no PIL (the TGA helpers of
# tools/tpbookmarks/make_icons.py):
#   python3 make_sidebar_icons.py <frame dir: trash_0N.tga> <icon/item dir> <client root dir>
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'tpbookmarks'))
import make_icons as tp  # noqa: E402

ICONS = (('offlineshop', '50200.tga'), ('chestpreview', '38050.tga'))
GAINS = (1.0, 1.2, 0.8)		# normal / over / down
SIZE, OFF = 24, 4			# the item icon scaled to 24 x 24 at (4, 4)
BG = (40, 30, 21)			# trash_01.tga's inside


def inside(x, y):
	dx, dy = abs(x - 15.5), abs(y - 15.5)
	return dx <= 11.5 and dy <= 11.5 and dx + dy <= 17


def make(frame, icon, gain):
	out = []
	for y in range(32):
		line = []
		for x in range(32):
			if not inside(x, y):
				line.append(frame[y][x])
				continue
			c = list(BG)
			if OFF <= x < OFF + SIZE and OFF <= y < OFF + SIZE:
				r, g, b, a = icon[y - OFF][x - OFF]
				c = [c[0] * (1 - a) + r * a, c[1] * (1 - a) + g * a, c[2] * (1 - a) + b * a]
			line.append(tuple(min(255, max(0, int(round(v * gain)))) for v in c) + (255,))
		out.append(line)
	return out


def main():
	frames_dir, icon_dir, root = sys.argv[1:4]
	frames = [tp.read_tga(os.path.join(frames_dir, 'trash_%02d.tga' % (i + 1)))[2] for i in range(3)]
	out_dir = os.path.join(root, 'mt2009_ui', 'sidebar')
	for name, src in ICONS:
		w, h, rows = tp.read_tga(os.path.join(icon_dir, src))
		icon = tp.scaled(rows, SIZE)
		# scaled() gives alpha 0..1
		for i, gain in enumerate(GAINS):
			tp.write_tga(os.path.join(out_dir, '%s_%02d.tga' % (name, i + 1)), make(frames[i], icon, gain))
			print('%s_%02d.tga' % (name, i + 1))


if __name__ == '__main__':
	main()
