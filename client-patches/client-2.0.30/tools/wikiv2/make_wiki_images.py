# -*- coding: utf-8 -*-
# MT2009_PLUS_WIKI_V1 - the wiki's pictures for the client pack "wikiv2" (build_wikiv2_pack.py), made once from the
# owner's Valiant2 wiki package (WikiSystem/2_Client_Pack/patch2/ui) - the output is committed under
# client-patches/client-2.0.30/wikiv2/d_/ymir work/ui/game/wiki/, so the client build does not need the package:
#   - every picture of patch2/ui/game/wiki (+ render/preview_back.tga, pattern/winfo*.png) as it is;
#   - the category banners (category/*.png, 722x105) in Polish: the English caption is found (bright, grey letters
#     left of the art), painted over (OpenCV inpaint) and the Polish one drawn in its place (Roboto Medium, white);
#   - the inventory side bar's button (32x32 tga, normal / over / down) from side_inv/wikipedia*.png ->
#     client-2.0.30/root/mt2009_ui/sidebar/wiki_0{1,2,3}.tga (root pack, as the bar's other icons).
#
#   docker run --rm -v /opt/metin2:/opt/metin2 python:3.12-slim sh -c \
#     "pip install -q pillow opencv-python-headless font-roboto && python3 \
#      /opt/metin2/git/wt-y-wiki/client-patches/client-2.0.30/tools/wikiv2/make_wiki_images.py \
#      /opt/metin2/cache/yohara/wiki-valiant2/WikiSystem/2_Client_Pack/patch2/ui"
import os
import shutil
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..'))
OUT = os.path.join(REPO, 'wikiv2', 'd_', 'ymir work', 'ui', 'game', 'wiki')
SIDEBAR = os.path.join(REPO, 'root', 'mt2009_ui', 'sidebar')

TITLES = {
	'acce_costumes.png': u'KOSTIUMY SZARF',
	'acce_system.png': u'SZARFY',
	'alchemy_system.png': u'ALCHEMIA SMOCZA',
	'aura.png': u'AURY',
	'body_costumes.png': u'KOSTIUMY',
	'bosses.png': u'BOSSOWIE',
	'chests.png': u'SKRZYNIE',
	'crafting.png': u'WYTWARZANIE',
	'equipments.png': u'EKWIPUNEK',
	'hair_styles.png': u'FRYZURY',
	'metin_stones.png': u'KAMIENIE METIN',
	'monsters.png': u'POTWORY',
	'mounts.png': u'WIERZCHOWCE',
	'pets.png': u'ZWIERZAKI',
	'weapon_skins.png': u'KOSTIUMY BRONI',
	'wikipedia.png': u'ENCYKLOPEDIA',
}


def font_path():
	import font_roboto
	return os.path.join(os.path.dirname(font_roboto.__file__), 'files', 'Roboto-Medium.ttf')


def caption_box(img):
	"""(mask, (x0, y0, x1, y1), letter height) of the English caption: bright grey letter-sized blobs, the widest
	horizontal cluster of them."""
	a = np.asarray(img).astype(np.int32)
	mx, mn = a.max(axis=2), a.min(axis=2)
	bright = ((mn > 150) & (mx - mn < 45)).astype(np.uint8)
	n, lab, stats, cent = cv2.connectedComponentsWithStats(bright, 8)
	letters = []
	for i in range(1, n):
		x, y, w, h, area = stats[i]
		if 10 <= h <= 48 and w <= 70 and area >= 12 and 8 <= cent[i][1] <= 97:
			letters.append((x, y, w, h, i))
	if not letters:
		return None
	letters.sort()
	clusters, cur = [], [letters[0]]
	for l in letters[1:]:
		px = max(c[0] + c[2] for c in cur)
		if l[0] - px <= 34:
			cur.append(l)
		else:
			clusters.append(cur)
			cur = [l]
	clusters.append(cur)
	# the caption starts in the left half (the art - keys, items - is on the right)
	left = [c for c in clusters if min(x[0] for x in c) < img.size[0] * 0.5] or clusters
	best = max(left, key=lambda c: (len(c), max(x[0] + x[2] for x in c) - min(x[0] for x in c)))
	x0 = min(c[0] for c in best); y0 = min(c[1] for c in best)
	x1 = max(c[0] + c[2] for c in best); y1 = max(c[1] + c[3] for c in best)
	mask = np.zeros(bright.shape, np.uint8)
	for c in best:
		mask[lab == c[4]] = 255
	heights = sorted(c[3] for c in best)
	return mask, (x0, y0, x1, y1), heights[len(heights) // 2]


def banner(src, dst, title, font):
	img = Image.open(src).convert('RGB')
	found = caption_box(img)
	if not found:
		raise SystemExit('%s: no caption found' % src)
	mask, (x0, y0, x1, y1), letter = found
	mask = cv2.dilate(mask, np.ones((5, 5), np.uint8), iterations=2)
	bgr = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)
	clean = cv2.inpaint(bgr, mask, 9, cv2.INPAINT_TELEA)
	out = Image.fromarray(cv2.cvtColor(clean, cv2.COLOR_BGR2RGB))
	d = ImageDraw.Draw(out)
	cx = (x0 + x1) / 2.0
	cy = (y0 + y1) / 2.0
	# one line, the old capital height (two-line captions: one line a little smaller), never wider than the old
	# caption's room
	size = int(max(22, min(40, letter * 1.32 if (y1 - y0) < letter * 1.6 else letter * 1.2)))
	room = max(x1 - x0, 300)
	while size > 14:
		f = ImageFont.truetype(font, size)
		bb = d.textbbox((0, 0), title, font=f)
		if bb[2] - bb[0] <= room:
			break
		size -= 1
	f = ImageFont.truetype(font, size)
	bb = d.textbbox((0, 0), title, font=f)
	tx = cx - (bb[2] - bb[0]) / 2.0 - bb[0]
	ty = cy - (bb[3] - bb[1]) / 2.0 - bb[1]
	d.text((tx + 1, ty + 2), title, font=f, fill=(0, 0, 0))
	d.text((tx, ty), title, font=f, fill=(245, 245, 245))
	out.save(dst)
	return (x0, y0, x1, y1), size


def sidebar(src_dir):
	os.makedirs(SIDEBAR, exist_ok=True)
	for n, name in enumerate(('wikipedia.png', 'wikipedia1.png', 'wikipedia2.png'), 1):
		im = Image.open(os.path.join(src_dir, 'game', 'side_inv', name)).convert('RGBA')
		canvas = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
		canvas.paste(im, ((32 - im.size[0]) // 2, (32 - im.size[1]) // 2), im)
		canvas.save(os.path.join(SIDEBAR, 'wiki_%02d.tga' % n))


def main():
	src = sys.argv[1]
	font = font_path()
	if os.path.isdir(OUT):
		shutil.rmtree(OUT)
	shutil.copytree(os.path.join(src, 'game', 'wiki'), OUT)
	shutil.copy(os.path.join(src, 'game', 'render', 'preview_back.tga'), os.path.join(OUT, 'preview_back.tga'))
	for n in (1, 2, 3):
		shutil.copy(os.path.join(src, 'pattern', 'winfo%d.png' % n), os.path.join(OUT, 'winfo%d.png' % n))
	for name, title in sorted(TITLES.items()):
		path = os.path.join(OUT, 'category', name)
		box, size = banner(path, path, title, font)
		print('%-20s %-18s caption %s -> %d px' % (name, title.encode('ascii', 'replace').decode(), box, size))
	sidebar(src)
	n = sum(len(f) for _, _, f in os.walk(OUT))
	print('%d files in %s' % (n, OUT))


if __name__ == '__main__':
	main()
