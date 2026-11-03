# -*- coding: utf-8 -*-
# MT2009_PLUS_FISHING_RENEWAL_V1 - the client build's part of the new fishing minigame: a new pack "fishren" with
# everything of files/ - GF 26.1.11's d:/ymir work/ui/fishing_01.dds and the 15 d:/ymir work/ui/game/fishing/**.sub on
# it (the window, the circle, the counter, the timer, the fish's 4 frames, the wave's 4 frames, "Hit", "Miss"; the same
# pictures github.com/amun3808/metin2-fishing-renewal ships; files/d_/... is packed as d:/...; the players' install has
# none of them - a name some pack of BASE / OUT has stops the build) + its Index line at the end. The window itself is
# root python (root/uifishingrenewal.py, root/uiscript/fishingrenewalwindow.py) and goes with the root pack. No
# gamedata / dbdata change, so the place in clientY.sh is free; e.g. right after fishpuzzle (or the spirala line):
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/fishren/build_fishren_pack.py <BASE pack dir> <OUT pack dir> [--check]
#
# clientY.sh:
#   S_fishren() { docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/fishren/build_fishren_pack.py \
#     $C/azbase $C/out/pack; }; step fishren $C/fishren.json S_fishren
# and fishren/verify_fishren.py in the verify loop. Every entry written is read back. Idempotent: a second run gives
# "unchanged".
import json
import os
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
PACK = 'fishren'


def pack_files():
	"""files/ as the pack's entries: files/d_/ymir work/... -> d:/ymir work/..."""
	root = os.path.join(HERE, 'files')
	got = {}
	for dp, dn, fn in os.walk(root):
		for f in fn:
			rel = os.path.relpath(os.path.join(dp, f), root).replace(os.sep, '/')
			if rel.startswith('d_/'):
				rel = 'd:/' + rel[3:]
			got[rel.lower()] = open(os.path.join(dp, f), 'rb').read()
	return got


def main():
	import m2pack
	import packlib
	args = [a for a in sys.argv[1:] if not a.startswith('--')]
	check = '--check' in sys.argv
	rd = packlib.rd
	base, out = args[:2]
	report = {}
	files = pack_files()
	for d in (base, out):
		for p in sorted(f[:-6] for f in os.listdir(d) if f.endswith('.index')):
			if p == PACK:
				continue
			for e in m2pack.read_index(os.path.join(d, p + '.index'))[2]:
				if e['name'] in files:
					raise SystemExit('%s: %s is in %s/%s already' % (PACK, e['name'], d, p))
	have = None
	if os.path.exists(os.path.join(out, PACK + '.index')):
		f, v, ents = m2pack.read_index(os.path.join(out, PACK + '.index'))
		dat = rd(os.path.join(out, PACK + '.data'))
		have = dict((e['name'], m2pack.read_entry(dat, e)) for e in ents)
	if have == files:
		report[PACK] = 'unchanged'
	elif check:
		report[PACK] = dict(files=len(files))
	else:
		tmpl = m2pack.read_index(os.path.join(base, 'az_mobs.index'))[2][-1]['raw']
		ti, td = os.path.join(out, PACK + '.index.spk'), os.path.join(out, PACK + '.data.spk')
		packlib.repack_add_typed(None, None, {}, dict((k, (b, 1)) for k, b in files.items()), ti, td, tmpl)
		os.replace(ti, os.path.join(out, PACK + '.index'))
		os.replace(td, os.path.join(out, PACK + '.data'))
		f, v, ents = m2pack.read_index(os.path.join(out, PACK + '.index'))
		dat = rd(os.path.join(out, PACK + '.data'))
		got = {}
		for e in ents:
			assert zlib.crc32(dat[e['pos']:e['pos'] + e['size']]) & 0xffffffff == e['dcrc'], e['name']
			assert e['fcrc'] == zlib.crc32(e['name'].encode('cp1252')) & 0xffffffff, e['name']
			got[e['name']] = m2pack.read_entry(dat, e)
		assert got == files, 'read-back differs'
		report[PACK] = dict(entries=len(ents), data_kb=round(len(dat) / 1e3, 1))
	if not check:
		ix_path = os.path.join(out, 'Index') if os.path.exists(os.path.join(out, 'Index')) else os.path.join(base, 'Index')
		ix = rd(ix_path)
		lines = [l.strip() for l in ix.replace(b'\r\n', b'\n').split(b'\n')]
		if PACK.encode() not in lines:
			nl = b'\r\n' if b'\r\n' in ix else b'\n'
			ix = ix.rstrip(b'\r\n') + nl + b'*' + nl + PACK.encode() + nl
		if ix != rd(ix_path) or ix_path != os.path.join(out, 'Index'):
			open(os.path.join(out, 'Index'), 'wb').write(ix)
			report['Index'] = 'written'
	print(json.dumps(report, indent=1))


if __name__ == '__main__':
	main()
