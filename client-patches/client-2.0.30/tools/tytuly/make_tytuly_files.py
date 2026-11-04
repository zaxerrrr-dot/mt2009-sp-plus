# -*- coding: utf-8 -*-
# MT2009_PLUS_TITLES_V1 - the developer's tool that made files/ of tools/tytuly (kept for the record; the builder reads
# files/ only). Sources: the owner's package "Official Title System Renewal" (02. Client: the title pictures, banners,
# effects, icons, the window's .sub) and GF 26.1.11 (d:/ymir work/ui/titlesystem_001.dds - the window's atlas the
# package's .sub name; crown01.mse/.dds - the crown of "Ostatni Ocalaly"; the portrait button cut out of windows.dds).
#   python3 make_tytuly_files.py <package "02. Client" dir> <GF _client dir>
# Taken: the window's 18 .sub, the plates (title_0x_*_left/middle/right.tga) and banners (title_0x_banner_*.dds), the
# resources title_1000..1005.sub (the plates the catalogue uses) and the banners' frames sprites_1000..1002, every
# effect of effect/etc/title (10 .mse + their textures), the certificate icons 57000-57002 (V2: + the rank medals,
# RANK_MSE). Not taken: the package's
# title_0000 / 2000-2003 / 3000-3006 .sub (the exe takes an effect title's file from the server's catalogue) and its
# char_face_*.sub on Windows.dds (the players' install may have another windows.dds): the portrait button's three
# pictures and the pencil are cut out of GF's windows.dds (DXT5 blocks, x 284-432, y 848-940) into
# d:/ymir work/ui/game/title/char_face.dds, their .sub with the coordinates moved by that corner.
import os
import shutil
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'files')
CUT_X, CUT_Y, CUT_W, CUT_H = 284, 848, 148, 92
# (name, GF left, top, right, bottom) of the package's char_face_*.sub
FACE = (
	('char_face_button_default', 286, 851, 330, 895),
	('char_face_button_over', 335, 896, 379, 940),
	('char_face_button_down', 385, 896, 429, 940),
	('char_face_write_default', 338, 850, 353, 865),
	('char_face_write_over', 359, 850, 374, 865),
)


# MT2009_PLUS_TITLES_V2: a still picture over the head (crown01.mse's particle: one at a time, billboard, alpha blend)
RANK_MSE = (
	'BoundingSphereRadius   100.000000\r\nBoundingSpherePosition 0.000000 0.000000 0.000000\r\n\r\n'
	'Group Particle\r\n{\r\n'
	'    StartTime           0.000000\r\n'
	'    List TimeEventPosition\r\n    {\r\n        0.000000 "MOVING_TYPE_DIRECT" 0.000000 0.000000 0.000000\r\n    }\r\n'
	'    Group EmitterProperty\r\n    {\r\n'
	'        MaxEmissionCount        1\r\n'
	'        CycleLength             1.000000\r\n        CycleLoopEnable         1\r\n        LoopCount               0\r\n'
	'        EmitterShape            0\r\n        EmitterAdvancedType     0\r\n        EmitterEmitFromEdgeFlag  0\r\n'
	'        EmittingDirection       0.000000 0.000000 0.000000\r\n'
	'        List TimeEventEmittingSize\r\n        {\r\n            0.000000 0.000000\r\n        }\r\n'
	'        List TimeEventEmittingAngularVelocity\r\n        {\r\n            0.000000 0.000000\r\n        }\r\n'
	'        List TimeEventEmittingDirectionX\r\n        {\r\n            0.000000 0.000000\r\n        }\r\n'
	'        List TimeEventEmittingDirectionY\r\n        {\r\n            0.000000 0.000000\r\n        }\r\n'
	'        List TimeEventEmittingDirectionZ\r\n        {\r\n            0.000000 0.000000\r\n        }\r\n'
	'        List TimeEventEmittingVelocity\r\n        {\r\n            0.000000 0.000000\r\n        }\r\n'
	'        List TimeEventEmissionCountPerSecond\r\n        {\r\n            0.000000 20.000000\r\n        }\r\n'
	'        List TimeEventLifeTime\r\n        {\r\n            0.000000 3600.000000\r\n        }\r\n'
	'        List TimeEventSizeX\r\n        {\r\n            0.000000 64.000000\r\n        }\r\n'
	'        List TimeEventSizeY\r\n        {\r\n            0.000000 64.000000\r\n        }\r\n'
	'    }\r\n'
	'    Group ParticleProperty\r\n    {\r\n'
	'        SrcBlendType                 5\r\n        DestBlendType                6\r\n        ColorOperationType           4\r\n'
	'        BillboardType                1\r\n        RotationType                 0\r\n        RotationSpeed                0.000000\r\n'
	'        RotationRandomStartingBegin  0\r\n        RotationRandomStartingEnd    0\r\n'
	'        AttachEnable                 1\r\n        StretchEnable                0\r\n'
	'        TexAniType                   0\r\n        TexAniDelay                  0.029000\r\n        TexAniRandomStartFrameEnable 0\r\n'
	'        List TimeEventGravity\r\n        {\r\n            0.000000 0.000000\r\n        }\r\n'
	'        List TimeEventAirResistance\r\n        {\r\n            0.000000 0.000000\r\n        }\r\n'
	'        List TimeEventScaleX\r\n        {\r\n            0.000000 0.600000\r\n        }\r\n'
	'        List TimeEventScaleY\r\n        {\r\n            0.000000 0.600000\r\n        }\r\n'
	'        List TimeEventColorRed\r\n        {\r\n            0.000000 1.000000\r\n        }\r\n'
	'        List TimeEventColorGreen\r\n        {\r\n            0.000000 1.000000\r\n        }\r\n'
	'        List TimeEventColorBlue\r\n        {\r\n            0.000000 1.000000\r\n        }\r\n'
	'        List TimeEventAlpha\r\n        {\r\n            0.000000 1.000000\r\n            1.000000 1.000000\r\n        }\r\n'
	'        List TimeEventRotation\r\n        {\r\n            0.000000 0.000000\r\n        }\r\n'
	'        List TextureFiles\r\n        {\r\n            "%s"\r\n        }\r\n'
	'    }\r\n}\r\n')


def copy(src, dst):
	os.makedirs(os.path.dirname(dst), exist_ok=True)
	shutil.copyfile(src, dst)


def cut_dxt5(src, x0, y0, w, h):
	b = open(src, 'rb').read()
	assert b[:4] == b'DDS ' and b[84:88] == b'DXT5', src
	height, width = struct.unpack_from('<II', b, 12)
	assert x0 % 4 == 0 and y0 % 4 == 0 and w % 4 == 0 and h % 4 == 0 and x0 + w <= width and y0 + h <= height
	row = (width // 4) * 16
	out = bytearray()
	for by in range(y0 // 4, (y0 + h) // 4):
		start = 128 + by * row + (x0 // 4) * 16
		out += b[start:start + (w // 4) * 16]
	hdr = bytearray(b[:128])
	struct.pack_into('<II', hdr, 12, h, w)
	struct.pack_into('<I', hdr, 20, len(out))			# linear size
	flags = struct.unpack_from('<I', hdr, 8)[0] & ~0x20000	# no DDSD_MIPMAPCOUNT
	struct.pack_into('<I', hdr, 8, flags)
	struct.pack_into('<I', hdr, 28, 0)					# mip map count
	caps = struct.unpack_from('<I', hdr, 108)[0] & ~(0x400000 | 0x8)
	struct.pack_into('<I', hdr, 108, caps)
	return bytes(hdr) + bytes(out)


def main():
	pkg, gf = sys.argv[1:3]
	if os.path.isdir(OUT):
		shutil.rmtree(OUT)
	ui = os.path.join(pkg, 'd', 'ymir work', 'ui', 'game', 'title')
	dst_ui = os.path.join(OUT, 'd_', 'ymir work', 'ui', 'game', 'title')
	for f in sorted(os.listdir(os.path.join(ui, 'window'))):
		copy(os.path.join(ui, 'window', f), os.path.join(dst_ui, 'window', f.lower()))
	for f in sorted(os.listdir(ui)):
		if os.path.isfile(os.path.join(ui, f)):
			copy(os.path.join(ui, f), os.path.join(dst_ui, f.lower()))
	for res in range(1000, 1006):
		f = 'title_%04d.sub' % res
		copy(os.path.join(ui, 'titles', f), os.path.join(dst_ui, 'titles', f))
	for res in (1000, 1001, 1002):
		d = os.path.join(ui, 'titles', 'sprites_%04d' % res)
		for f in sorted(os.listdir(d)):
			copy(os.path.join(d, f), os.path.join(dst_ui, 'titles', 'sprites_%04d' % res, f.lower()))
	fx = os.path.join(pkg, 'd', 'ymir work', 'effect', 'etc', 'title')
	dst_fx = os.path.join(OUT, 'd_', 'ymir work', 'effect', 'etc', 'title')
	for f in sorted(os.listdir(fx)):
		copy(os.path.join(fx, f), os.path.join(dst_fx, f.lower()))
	for f in ('crown01.mse', 'crown01.dds'):
		copy(os.path.join(gf, 'd_', 'ymir work', 'effect', 'battleroyale', f), os.path.join(dst_fx, f))
	# MT2009_PLUS_TITLES_V2: the weekly ranking's titles 2-4 look as on the wiki (en "Titles": the Combat Zone's medals
	# - GF's title_2001..2003.sub, IMAGE effect/etc/ranking_battle/ranker_1..3.tga over the head). The exe draws an
	# effect title, not an image one: title_rank_<n>.mse shows GF's medal as one still billboard over the head (crown01's
	# particle, no movement, always fully visible, an hour's life), the medal picture next to it.
	for n in (1, 2, 3):
		copy(os.path.join(gf, 'd_', 'ymir work', 'effect', 'etc', 'ranking_battle', 'ranker_%d.tga' % n),
			os.path.join(dst_fx, 'ranker_%d.tga' % n))
		open(os.path.join(dst_fx, 'title_rank_%d.mse' % n), 'w', newline='').write(RANK_MSE % ('ranker_%d.tga' % n))
	copy(os.path.join(gf, 'd_', 'ymir work', 'ui', 'titlesystem_001.dds'), os.path.join(OUT, 'd_', 'ymir work', 'ui', 'titlesystem_001.dds'))
	dds = cut_dxt5(os.path.join(gf, 'd_', 'ymir work', 'ui', 'windows.dds'), CUT_X, CUT_Y, CUT_W, CUT_H)
	open(os.path.join(dst_ui, 'char_face.dds'), 'wb').write(dds)
	for name, l, t, r, b in FACE:
		sub = 'title subImage\r\nversion 1.0\r\nimage "game/title/char_face.dds"\r\nleft %d\r\ntop %d\r\nright %d\r\nbottom %d\r\n' % (
			l - CUT_X, t - CUT_Y, r - CUT_X, b - CUT_Y)
		open(os.path.join(dst_ui, name + '.sub'), 'w', newline='').write(sub)
	for vnum in (57000, 57001, 57002):
		copy(os.path.join(pkg, 'icon', 'icon', 'item', '%d.tga' % vnum), os.path.join(OUT, 'icon', 'item', '%d.tga' % vnum))
	n = sum(len(fn) for dp, dn, fn in os.walk(OUT))
	print('files/: %d files' % n)


if __name__ == '__main__':
	main()
