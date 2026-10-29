# -*- coding: utf-8 -*-
# MT2009_PLUS_INVENTORY_V2_V1 - the pictures of the official v2 inventory (the package "offical_inventory_v2",
# Autor: dracaryS) for the pack "inv2_ui" (build_inv2_packs.py). Run once by hand (plain python3, no PIL); the result is
# kept in client-patches/client-2.0.30/inv2/d_ (d_/ = d:/) and the pack builder reads only that folder:
#
#   d:/ymir work/ui/new_inventory/equip_bg_sub.png       the package's, as it is (the ring frames + the four round buttons)
#   d:/ymir work/ui/new_inventory/equip_pagebtn_bg.png   the package's (the frame under a page tab)
#   d:/ymir work/ui/new_inventory/btn_[0-3]_[0-2].png    the package's round buttons (Alchemia, Magazyn, Sklep, Kostiumy)
#   d:/ymir work/ui/new_inventory/equip_bg_mt2009.png    the package's equip_bg_0.png with the pet icon of the bottom right
#                                                        frame wiped (no pet slot here): the inside of the sub picture's
#                                                        empty ring frame is copied over it - that frame holds our small
#                                                        buttons (horse bag, chest preview; uiscript/inventoryequipwindow.py)
#
#   python3 make_inv2_images.py <package dir>/Binary/etc/ymir\ work/ui/new_inventory [--check]
import os
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, '..', '..', 'inv2', 'd_', 'ymir work', 'ui', 'new_inventory'))
COPY = ['equip_bg_sub.png', 'equip_pagebtn_bg.png'] + ['btn_%d_%d.png' % (a, b) for a in range(4) for b in range(3)]
# the bottom right frame's inside in equip_bg_0.png (157 x 138) and where it is taken from in equip_bg_sub.png
DST = (119, 103, 28, 29)		# x, y, w, h
SRC = (8, 8)					# the first ring frame's inside


def load(path):
	b = open(path, 'rb').read()
	assert b[:8] == b'\x89PNG\r\n\x1a\n', path
	i, idat = 8, b''
	while i < len(b):
		n, t = struct.unpack('>I4s', b[i:i + 8])
		d = b[i + 8:i + 8 + n]
		i += 12 + n
		if t == b'IHDR':
			w, h, bd, ct, _, _, il = struct.unpack('>IIBBBBB', d)
			assert bd == 8 and ct in (2, 6) and il == 0, (path, bd, ct, il)
		elif t == b'IDAT':
			idat += d
	bpp = 3 if ct == 2 else 4
	raw = zlib.decompress(idat)
	stride = w * bpp
	rows, prev, o = [], bytearray(stride), 0
	for _ in range(h):
		f = raw[o]
		o += 1
		cur = bytearray(raw[o:o + stride])
		o += stride
		for x in range(stride):
			a = cur[x - bpp] if x >= bpp else 0
			c = prev[x - bpp] if x >= bpp else 0
			up = prev[x]
			if f == 1:
				cur[x] = (cur[x] + a) & 255
			elif f == 2:
				cur[x] = (cur[x] + up) & 255
			elif f == 3:
				cur[x] = (cur[x] + ((a + up) >> 1)) & 255
			elif f == 4:
				p = a + up - c
				pa, pb, pc = abs(p - a), abs(p - up), abs(p - c)
				cur[x] = (cur[x] + (a if pa <= pb and pa <= pc else (up if pb <= pc else c))) & 255
		rows.append(cur)
		prev = cur
	return w, h, ct, bpp, rows


def save(w, h, ct, rows):
	def chunk(t, d):
		return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
	raw = b''.join(b'\x00' + bytes(r) for r in rows)
	return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, ct, 0, 0, 0))
		+ chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))


def build(src):
	out = {}
	for n in COPY:
		out[n] = open(os.path.join(src, n), 'rb').read()
	w, h, ct, bpp, rows = load(os.path.join(src, 'equip_bg_0.png'))
	assert (w, h) == (157, 138), (w, h)
	sw, sh, sct, sbpp, srows = load(os.path.join(src, 'equip_bg_sub.png'))
	assert (sw, sh) == (157, 82) and sbpp == bpp, (sw, sh)
	x0, y0, dw, dh = DST
	for dy in range(dh):
		for dx in range(dw):
			s = srows[SRC[1] + dy]
			rows[y0 + dy][(x0 + dx) * bpp:(x0 + dx + 1) * bpp] = s[(SRC[0] + dx) * bpp:(SRC[0] + dx + 1) * bpp]
	out['equip_bg_mt2009.png'] = save(w, h, ct, rows)
	assert load_bytes_ok(out['equip_bg_mt2009.png'])
	return out


def load_bytes_ok(b):
	import tempfile
	fd, p = tempfile.mkstemp(suffix='.png')
	os.write(fd, b)
	os.close(fd)
	try:
		return load(p)[:2] == (157, 138)
	finally:
		os.remove(p)


def main():
	args = [a for a in sys.argv[1:] if not a.startswith('--')]
	files = build(args[0])
	if '--check' in sys.argv:
		bad = [n for n, b in sorted(files.items()) if not os.path.isfile(os.path.join(OUT, n))
			or open(os.path.join(OUT, n), 'rb').read() != b]
		print('\n'.join(bad) if bad else 'inv2 images: OK (%d)' % len(files))
		sys.exit(1 if bad else 0)
	if not os.path.isdir(OUT):
		os.makedirs(OUT)
	for n, b in sorted(files.items()):
		open(os.path.join(OUT, n), 'wb').write(b)
	print('%d files -> %s' % (len(files), OUT))


if __name__ == '__main__':
	main()
