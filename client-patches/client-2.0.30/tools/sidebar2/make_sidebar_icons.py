# MT2009_PLUS_SIDEBAR_WINDOWS_V1 - three inventory side bar icons (uiinventory.py SidebarWindow, the owner's list of
# 10 November 2026), made as tools/inv2/make_sidebar_icons.py makes "Podglad skrzyn": the octagon frame of the side
# bar's first icons (client-2.0.28 trash_0N.tga), its inside filled with that icon's brown and a picture the client
# already has over it, scaled to 24 x 24:
#   root/mt2009_ui/sidebar/najemnicy_01/02/03.tga    "Najemnicy": the warrior's face (icon/face/warrior_m.tga - the
#                                                    Kolekcjoner Najemnikow window's Najemnicy tab shows these faces)
#   root/mt2009_ui/sidebar/monstercard_01/02/03.tga  "Karty potworow": the Zlote Pudelko Kart Potwora
#                                                    (root/icon/item/83037.tga)
#   root/mt2009_ui/sidebar/relikt_01/02/03.tga       "Relikty": the Relikt Duszy (root/icon/item/30272.tga)
# Plain Python 3, no PIL:
#   python3 make_sidebar_icons.py <frame dir: trash_0N.tga> <dir with icon/face/warrior_m.tga> <client root dir>
# e.g. client-2.0.28/root/mt2009_ui/sidebar /opt/metin2/cache/gf/Gameforge_26.1.11/_client client-2.0.30/root
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'inv2'))
sys.path.insert(0, os.path.join(HERE, '..', 'tpbookmarks'))
import make_icons as tp  # noqa: E402  (tools/tpbookmarks/make_icons.py)
import make_sidebar_icons as inv2  # noqa: E402  (tools/inv2/make_sidebar_icons.py)

# (name, source: 'face' = the face dir, 'root' = the client root, path)
ICONS = (
	('najemnicy', 'face', 'icon/face/warrior_m.tga'),
	('monstercard', 'root', 'icon/item/83037.tga'),
	('relikt', 'root', 'icon/item/30272.tga'),
)


def main():
	frames_dir, face_dir, root = sys.argv[1:4]
	frames = [tp.read_tga(os.path.join(frames_dir, 'trash_%02d.tga' % (i + 1)))[2] for i in range(3)]
	out_dir = os.path.join(root, 'mt2009_ui', 'sidebar')
	for name, where, src in ICONS:
		w, h, rows = tp.read_tga(os.path.join(face_dir if where == 'face' else root, src))
		icon = tp.scaled(rows, inv2.SIZE)
		for i, gain in enumerate(inv2.GAINS):
			tp.write_tga(os.path.join(out_dir, '%s_%02d.tga' % (name, i + 1)), inv2.make(frames[i], icon, gain))
			print('%s_%02d.tga' % (name, i + 1))


if __name__ == '__main__':
	main()
