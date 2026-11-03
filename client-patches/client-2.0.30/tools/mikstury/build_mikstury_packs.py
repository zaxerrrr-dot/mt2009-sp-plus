# -*- coding: utf-8 -*-
# MT2009_PLUS_BIOLOG_ELIKSIR_V1 / MT2009_PLUS_MIKSTURY_WYCOFANE_V1 - the client build's part (patch_mikstury_client.py):
# the 6 itemdesc lines of the existing pack "dbdata" (locale/pl/itemdesc.txt). No new pack, no icon.
# BUILD ORDER - it shares dbdata: after every other Yohara step that writes it (e.g. right after ../spirala), on the same
# OUT (a pack already in OUT - an earlier step changed it - is the one patched):
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/mikstury/build_mikstury_packs.py <BASE pack dir> <OUT pack dir> [--check]
#
# clientY.sh: after the spirala line,
#   S_mikstury() { docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/mikstury/build_mikstury_packs.py $C/azbase \
#     $C/out/pack; }; step mikstury $C/mikstury.json S_mikstury
# and mikstury/verify_mikstury.py in the verify loop. Every entry written is read back. Idempotent: a second run gives
# "unchanged".
import json
import os
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, HERE)
ZIP_LIMIT = 29 * 1024 * 1024


def main():
	import m2pack
	import packlib
	import patch_mikstury_client as pc
	args = [a for a in sys.argv[1:] if not a.startswith('--')]
	check = '--check' in sys.argv
	rd = packlib.rd
	base, out = args[:2]
	report = {}

	def src_of(pack):
		return out if os.path.exists(os.path.join(out, pack + '.index')) else base

	def write(pack, src, rep, ents, dat):
		tmp_i, tmp_d = os.path.join(out, pack + '.index.mik'), os.path.join(out, pack + '.data.mik')
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

	jobs = {'dbdata': sorted(pc.JOBS)}
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
	print(json.dumps(report, indent=1))


if __name__ == '__main__':
	main()
