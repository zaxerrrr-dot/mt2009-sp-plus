#!/usr/bin/env python3
"""MT2009_PLUS_ITEMSHOP_V3_V6: the pictures of the round-3 lines (images.json, written by gen_global_catalog.py).

  fetch_global_images.py [<saved page dir>]

- a set chest: its pl-wiki picture (the chest page's "image", 242 x 242 as the big servers' detail picture) into
  app/shop3/images/chests/<id>.png and a 98 x 98 copy <id>_98.png for the cards; a chest of the model (no pl-wiki chest
  for its set) gets the picture of the chest the owner saved (the one .png of 242 px in <saved page dir>);
- an item without a picture in app/itemshop/img/item (the folder the second shop's images/item points to): the
  pl-wiki's icon of its name ("Plik:<name>.png", the Kostiumy pages' icons) - an icon the wiki lacks is left to
  tools/itemshop3/gen_shop_icons.py (the client's icons).
Needs Pillow (e.g. docker run --rm -v /opt/metin2:/opt/metin2 python:3.12-slim sh -c "pip install -q pillow && python3 ...").
Files already there are kept.
"""
import io
import json
import os
import sys
import time
import urllib.parse
import urllib.request

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
APP = os.path.join(REPO, 'linux-port', 'docker', 'itemshop', 'app')
CHESTS = os.path.join(APP, 'shop3', 'images', 'chests')
ITEMS = os.path.join(APP, 'itemshop', 'img', 'item')
API = 'https://pl-wiki.metin2.gameforge.com/api.php'
UA = {'User-Agent': 'Mozilla/5.0 (MT2009 shop pictures)'}


def wiki_file(name):
	"""The bytes of a pl-wiki file (None when it has none)."""
	q = urllib.parse.urlencode({'action': 'query', 'titles': 'Plik:' + name, 'prop': 'imageinfo', 'iiprop': 'url', 'format': 'json'})
	d = json.load(urllib.request.urlopen(urllib.request.Request(API + '?' + q, headers=UA), timeout=30))
	for p in d.get('query', {}).get('pages', {}).values():
		ii = p.get('imageinfo')
		if ii:
			time.sleep(0.1)
			return urllib.request.urlopen(urllib.request.Request(ii[0]['url'], headers=UA), timeout=30).read()
	return None


def save_chest(img, cid):
	"""<cid>.png (242 px) and <cid>_98.png; cid 'model' = the picture of every chest of the model."""
	img = img.convert('RGBA')
	if img.size != (242, 242):
		img.thumbnail((242, 242), Image.LANCZOS)
		canvas = Image.new('RGBA', (242, 242), (0, 0, 0, 0))
		canvas.paste(img, ((242 - img.width) // 2, (242 - img.height) // 2))
		img = canvas
	img.save(os.path.join(CHESTS, '%s.png' % cid), optimize=True)
	img.resize((98, 98), Image.LANCZOS).save(os.path.join(CHESTS, '%s_98.png' % cid), optimize=True)


def main():
	saved = sys.argv[1] if len(sys.argv) > 1 else '/opt/metin2/cache/yohara/ishop-global'
	model = None
	for root, dirs, files in os.walk(saved):
		for f in sorted(files):
			if f.endswith('.png'):
				im = Image.open(os.path.join(root, f))
				if im.size == (242, 242):
					model = im.copy()
	x = json.load(open(os.path.join(HERE, 'images.json'), encoding='utf-8'))
	os.makedirs(CHESTS, exist_ok=True)
	done = kept = 0
	if model is not None and not os.path.exists(os.path.join(CHESTS, 'model.png')):
		save_chest(model, 'model')
	for c in x['chests']:
		if c['model']:
			continue
		if os.path.exists(os.path.join(CHESTS, '%d.png' % c['id'])):
			kept += 1
			continue
		blob = wiki_file(c['wiki_file'])
		if blob:
			save_chest(Image.open(io.BytesIO(blob)), c['id'])
		else:
			print('chest %d: no picture' % c['id'])
			continue
		done += 1
	missing = []
	for v in x['items']:
		out = os.path.join(ITEMS, '%d.png' % v)
		if os.path.exists(out):
			continue
		blob = wiki_file(x['item_names'][str(v)] + '.png')
		if not blob:
			missing.append(v)
			continue
		Image.open(io.BytesIO(blob)).convert('RGBA').save(out, optimize=True)
		done += 1
	print('chests and icons made %d, kept %d, icons without a wiki picture (gen_shop_icons.py): %s' % (done, kept, ' '.join(map(str, missing))))


if __name__ == '__main__':
	main()
