#!/usr/bin/env python3
"""MT2009_PLUS_ITEMSHOP_V3_V3 - the item descriptions of the client (locale itemdesc.txt, the text of the item's
tooltip in the game) for the second ItemShop (linux-port/docker/itemshop/app/shop3).

Since V3 the shop sells the in-game shop's lines (common.itemshop_items); a description comes from the web
catalogue (itemshop.ishop_items `desc`) where it has the vnum, else from here - the same words the in-game
window shows in the item's tooltip.

  gen_client_desc.py <itemdesc.txt>
      writes linux-port/docker/itemshop/app/shop3/include/db/client_itemdesc.json ({vnum: text}); the file is
      cp1250 (vnum, name, description[, a second line]), the client's colour codes (|cffRRGGBB ... |r) are dropped
      and [ENTER] becomes a new line.
Example (vps1, the Yohara client): gen_client_desc.py /opt/metin2/cache/cY/data/itemdesc.txt
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..'))
OUT = os.path.join(REPO, 'linux-port', 'docker', 'itemshop', 'app', 'shop3', 'include', 'db', 'client_itemdesc.json')


def clean(text):
	text = re.sub(r'\|c[0-9a-fA-F]{8}', '', text).replace('|r', '').replace('|R', '')
	text = text.replace('[ENTER]', '\n')
	lines = [re.sub(r'\s+', ' ', l).strip() for l in text.split('\n')]
	return '\n'.join(l for l in lines if l)


def main():
	if len(sys.argv) != 2:
		sys.exit(__doc__)
	out = {}
	for line in open(sys.argv[1], encoding='cp1250', errors='replace'):
		f = line.rstrip('\r\n').split('\t')
		if len(f) < 3 or not f[0].strip().isdigit():
			continue
		text = clean('\n'.join(x for x in f[2:4] if x.strip()))
		if text:
			out[f[0].strip()] = text
	with open(OUT, 'w', encoding='utf-8', newline='\n') as fp:
		json.dump(out, fp, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
	print('wrote %s (%d descriptions)' % (OUT, len(out)))


if __name__ == '__main__':
	main()
