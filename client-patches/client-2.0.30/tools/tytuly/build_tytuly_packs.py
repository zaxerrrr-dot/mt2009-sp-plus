# -*- coding: utf-8 -*-
# MT2009_PLUS_TITLES_V1 - the client build's part of Tytuly (the owner's package "Official Title System Renewal", rebuilt;
# server-patches/tytuly): the three certificates 57000-57002 (patch_tytuly_client.py) in the existing packs "gamedata"
# (gamedata/item_list.txt) and "dbdata" (gamedata/item_proto, locale/pl/itemdesc.txt), and a new pack "tytuly" with
# everything of files/ (make_tytuly_files.py): the title window's pictures (GF 26.1.11's d:/ymir work/ui/titlesystem_001.dds
# and the package's 18 window .sub), the plates and the animated banners (d:/ymir work/ui/game/title/..., the resources
# titles/title_1000..1005.sub and the banner frames sprites_1000..1002), the over-head effects (d:/ymir work/effect/etc/
# title/: the package's 10 .mse with their textures, GF's crown01), the portrait button (char_face.dds cut out of GF's
# windows.dds and its .sub) and the certificates' icons (files/d_/ymir work/... is packed as d:/...; a name some pack
# of BASE / OUT has stops the build) + its Index line at the end. The window itself is root python
# (root/uicharactertitle.py, uiscript/charactertitlewindow.py) and the exe (Mt2009Titles.cpp).
# BUILD ORDER - it shares gamedata and dbdata: after every other Yohara step that writes them (e.g. right after
# ../skillcolor), on the same OUT (a pack already in OUT - an earlier step changed it - is the one patched):
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/tytuly/build_tytuly_packs.py <BASE pack dir> <OUT pack dir> [--check]
#
# clientY.sh: after the skillcolor_packs line,
#   S_tytuly_packs() { docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/tytuly/build_tytuly_packs.py \
#     $C/azbase $C/out/pack; }; step tytuly_packs $C/tytuly.json S_tytuly_packs
# then verify_tytuly.py on OUT. Every entry written is read back. Idempotent: a second run gives "unchanged".
import json
import os
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, HERE)
ZIP_LIMIT = 29 * 1024 * 1024
ICON_PACK = 'tytuly'


def pack_files():
	"""files/ as the pack's entries: files/d_/ymir work/... -> d:/ymir work/..., the rest by its path (icon/item/...)."""
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
	import patch_tytuly_client as pc
	args = [a for a in sys.argv[1:] if not a.startswith('--')]
	check = '--check' in sys.argv
	rd = packlib.rd
	base, out = args[:2]
	report = {}

	def src_of(pack):
		return out if os.path.exists(os.path.join(out, pack + '.index')) else base

	def write(pack, src, rep, ents, dat):
		tmp_i, tmp_d = os.path.join(out, pack + '.index.spk'), os.path.join(out, pack + '.data.spk')
		r = packlib.repack_add_typed(os.path.join(src, pack + '.index'), os.path.join(src, pack + '.data'), rep, {},
			tmp_i, tmp_d, ents[-1]['raw'])
		os.replace(tmp_i, os.path.join(out, pack + '.index'))
		os.replace(tmp_d, os.path.join(out, pack + '.data'))
		f, v, nw = m2pack.read_index(os.path.join(out, pack + '.index'))
		nd = rd(os.path.join(out, pack + '.data'))
		names = [e['name'] for e in nw]
		assert len(set(names)) == len(names), pack
		got = {}
		for e in nw:
			assert zlib.crc32(nd[e['pos']:e['pos'] + e['size']]) & 0xffffffff == e['dcrc'], (pack, e['name'])
			assert e['fcrc'] == zlib.crc32(e['name'].encode('cp1252')) & 0xffffffff, (pack, e['name'])
			got[e['name']] = m2pack.read_entry(nd, e)
		for n, b in rep.items():
			assert got[n] == b, (pack, n)
		for e in ents:
			if e['name'] not in rep:
				assert got[e['name']] == m2pack.read_entry(dat, e), (pack, e['name'])
		return dict(old=r[0], added=r[1], replaced=r[2], entries=len(nw), data_mb=round(len(nd) / 1e6, 2),
			under_zip_limit=len(nd) < ZIP_LIMIT)

	jobs = {'gamedata': ['gamedata/item_list.txt'], 'dbdata': ['gamedata/item_proto', 'locale/pl/itemdesc.txt']}
	for pack, files in sorted(jobs.items()):
		src = src_of(pack)
		f, v, ents = m2pack.read_index(os.path.join(src, pack + '.index'))
		dat = rd(os.path.join(src, pack + '.data'))
		have = dict((e['name'], e) for e in ents)
		rep = {}
		for n in files:
			b = m2pack.read_entry(dat, have[n])
			nb, changed = pc.JOBS[n](b)
			if nb != b:
				rep[n] = nb
				report.setdefault('changed', {})[n] = changed
		if not rep:
			report[pack] = 'unchanged'
		elif check:
			report[pack] = dict(replace=sorted(rep))
		else:
			report[pack] = write(pack, src, rep, ents, dat)
			report[pack]['replaced_names'] = sorted(rep)
			assert report[pack]['under_zip_limit'], report[pack]
	# the pictures, effects and icons: pack "tytuly" (new names only) + its Index line at the end
	icons = pack_files()
	want = set(i[3] for i in pc.items())
	assert want <= set(icons), (sorted(want), sorted(icons))
	for d in (base, out):
		for p in sorted(f[:-6] for f in os.listdir(d) if f.endswith('.index')):
			if p == ICON_PACK:
				continue
			for e in m2pack.read_index(os.path.join(d, p + '.index'))[2]:
				if e['name'] in icons:
					raise SystemExit('%s: %s is in %s/%s already' % (ICON_PACK, e['name'], d, p))
	have = None
	if os.path.exists(os.path.join(out, ICON_PACK + '.index')):
		f, v, ents = m2pack.read_index(os.path.join(out, ICON_PACK + '.index'))
		dat = rd(os.path.join(out, ICON_PACK + '.data'))
		have = dict((e['name'], m2pack.read_entry(dat, e)) for e in ents)
	if have == icons:
		report[ICON_PACK] = 'unchanged'
	elif check:
		report[ICON_PACK] = dict(files=len(icons))
	else:
		tmpl = m2pack.read_index(os.path.join(base, 'az_mobs.index'))[2][-1]['raw']
		ti, td = os.path.join(out, ICON_PACK + '.index.spk'), os.path.join(out, ICON_PACK + '.data.spk')
		packlib.repack_add_typed(None, None, {}, dict((k, (b, 1)) for k, b in icons.items()), ti, td, tmpl)
		os.replace(ti, os.path.join(out, ICON_PACK + '.index'))
		os.replace(td, os.path.join(out, ICON_PACK + '.data'))
		f, v, ents = m2pack.read_index(os.path.join(out, ICON_PACK + '.index'))
		dat = rd(os.path.join(out, ICON_PACK + '.data'))
		got = {}
		for e in ents:
			assert zlib.crc32(dat[e['pos']:e['pos'] + e['size']]) & 0xffffffff == e['dcrc'], e['name']
			assert e['fcrc'] == zlib.crc32(e['name'].encode('cp1252')) & 0xffffffff, e['name']
			got[e['name']] = m2pack.read_entry(dat, e)
		assert got == icons, 'read-back differs'
		report[ICON_PACK] = dict(entries=len(ents), data_kb=round(len(dat) / 1e3, 1))
	if not check:
		ix_path = os.path.join(out, 'Index') if os.path.exists(os.path.join(out, 'Index')) else os.path.join(base, 'Index')
		ix = rd(ix_path)
		lines = [l.strip() for l in ix.replace(b'\r\n', b'\n').split(b'\n')]
		if ICON_PACK.encode() not in lines:
			nl = b'\r\n' if b'\r\n' in ix else b'\n'
			ix = ix.rstrip(b'\r\n') + nl + b'*' + nl + ICON_PACK.encode() + nl
		if ix != rd(ix_path) or ix_path != os.path.join(out, 'Index'):
			open(os.path.join(out, 'Index'), 'wb').write(ix)
			report['Index'] = 'written'
	print(json.dumps(report, indent=1))


if __name__ == '__main__':
	main()
