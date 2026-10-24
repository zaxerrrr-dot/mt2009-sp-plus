#!/usr/bin/env python3
"""MT2009_PLUS_ITEMSHOP_V3_V2 - the item pictures of the web shops (app/itemshop/img/item/<vnum>.png, also the
second shop's images/item) that are missing, made from the client's own icons.

The old shop's picture folder had 2717 files while the catalogue (itemshop.ishop_items) names 2513 icons, 1701 of
them without a file - both shops showed a broken picture there (the owner's screenshot of 24.10.2026: "Buffi").
For every vnum given, this takes the icon of the client's item_list.txt (icon/item/....tga) out of the client packs
and writes it as PNG; files already there are kept.

  gen_shop_icons.py <client pack dir> <item_list.txt> <out dir> [<loose client dir>] < vnums.txt

An icon the packs lack is looked up as a plain file under <loose client dir> (the unpacked GF client,
/opt/metin2/cache/gf/Gameforge_26.1.11/_client - e.g. the weapon skins 40108.. have no icon in our packs).

vnums.txt: one vnum per line - the catalogue's icons, e.g.
  docker exec -i <db> mariadb ... -N -e "SELECT DISTINCT vnum_icon FROM itemshop.ishop_items" > vnums.txt
Runs in the m2pack-lzo image (the pack readers m2pack/packlib, python-lzo); the TGA -> PNG step is plain Python.
Example (vps1, the Yohara client):
  docker run --rm -i -v /opt/metin2:/opt/metin2 m2pack-lzo python3 tools/itemshop3/gen_shop_icons.py \\
      /opt/metin2/cache/cY/pack /opt/metin2/cache/cY/data/item_list.txt \\
      linux-port/docker/itemshop/app/itemshop/img/item < vnums.txt
"""
import os
import struct
import sys
import zlib

for p in ('/opt/metin2/cache/c36', '/opt/metin2/cache/tcm/tz', '/opt/metin2/cache/arezzo-work/client/az58'):
	if os.path.isdir(p):
		sys.path.insert(0, p)


def tga_to_rgba(data):
	"""(width, height, RGBA rows top-down) of a true-colour TGA (types 2 and 10, 24/32 bit)."""
	id_len, cmap_type, img_type = data[0], data[1], data[2]
	w, h = struct.unpack_from('<HH', data, 12)
	bpp, desc = data[16], data[17]
	if cmap_type or img_type not in (2, 10) or bpp not in (24, 32):
		raise ValueError('tga type %d / %d bpp' % (img_type, bpp))
	cmap_len = struct.unpack_from('<H', data, 5)[0] * ((data[7] + 7) // 8)
	pos = 18 + id_len + cmap_len
	n = bpp // 8
	px = bytearray()
	if img_type == 2:
		px = data[pos:pos + w * h * n]
	else:
		while len(px) < w * h * n:
			c = data[pos]
			pos += 1
			cnt = (c & 0x7f) + 1
			if c & 0x80:
				px += data[pos:pos + n] * cnt
				pos += n
			else:
				px += data[pos:pos + n * cnt]
				pos += n * cnt
	rows = []
	for y in range(h):
		row = bytearray()
		for x in range(w):
			i = (y * w + x) * n
			b, g, r = px[i], px[i + 1], px[i + 2]
			a = px[i + 3] if n == 4 else 255
			row += bytes((r, g, b, a))
		rows.append(bytes(row))
	if not desc & 0x20:		# origin bottom-left
		rows.reverse()
	return w, h, rows


def png(w, h, rows):
	def chunk(tag, body):
		return struct.pack('>I', len(body)) + tag + body + struct.pack('>I', zlib.crc32(tag + body) & 0xffffffff)
	raw = b''.join(b'\x00' + r for r in rows)
	return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0))
		+ chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))


def main():
	if len(sys.argv) not in (4, 5):
		sys.exit(__doc__)
	pack_dir, item_list, out_dir = sys.argv[1:4]
	loose_dir = sys.argv[4] if len(sys.argv) == 5 else None
	import m2pack
	import packlib
	icon_of = {}
	for line in open(item_list, encoding='cp1250', errors='replace'):
		f = line.rstrip('\r\n').split('\t')
		if len(f) >= 3 and f[0].strip().isdigit():
			icon_of[int(f[0])] = f[2].strip().replace('\\', '/').lower()
	entries = {}
	for name in sorted(os.listdir(pack_dir)):
		if not name.endswith('.index'):
			continue
		p = os.path.join(pack_dir, name[:-6])
		try:
			ents = m2pack.read_index(p + '.index')[2]
		except Exception:
			continue
		for e in ents:
			if e['name'].startswith('icon/'):
				entries.setdefault(e['name'], (p, e))	# the first pack in name order, as listed
	data_cache = {}
	made = kept = 0
	missing = []
	for line in sys.stdin:
		line = line.strip()
		if not line.isdigit():
			continue
		vnum_text, vnum = line, int(line)
		out = os.path.join(out_dir, '%s.png' % vnum_text)
		if os.path.exists(out):
			kept += 1
			continue
		icon = icon_of.get(vnum)
		loose = os.path.join(loose_dir, icon) if (icon and loose_dir) else None
		if icon and icon in entries:
			p, e = entries[icon]
			if p not in data_cache:
				data_cache[p] = packlib.rd(p + '.data')
			blob = m2pack.read_entry(data_cache[p], e)
		elif loose and os.path.isfile(loose):
			blob = open(loose, 'rb').read()
		else:
			missing.append(vnum_text)
			continue
		try:
			w, h, rows = tga_to_rgba(blob)
		except Exception as ex:
			missing.append('%s(%s)' % (vnum_text, ex))
			continue
		with open(out, 'wb') as f:
			f.write(png(w, h, rows))
		made += 1
	print('made %d, kept %d, without a client icon %d: %s' % (made, kept, len(missing), ' '.join(missing[:60])))


if __name__ == '__main__':
	main()
