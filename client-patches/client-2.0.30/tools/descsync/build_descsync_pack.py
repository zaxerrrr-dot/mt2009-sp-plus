# -*- coding: utf-8 -*-
# MT2009_PLUS_DESC_SYNC_V1 - item descriptions corrected in the repo's Polish source (client-2.0.30/locale/locale/pl/
# itemdesc.txt) after the client data the Yohara build starts from (cache/c55/data) was made: the rows of SYNC are
# copied from the repo into the build's locale/pl/itemdesc.txt (pack "dbdata"). 30368-30370 lost "Oficjalny" (a570ba0d)
# - without this the build kept the old text and tools/lang (keyed by the Polish text) fell back to it in every
# language (verify_lang: forbidden name). A row is replaced only when the build has it; the rest stays byte for byte.
# BUILD ORDER: after every other dbdata writer (now runy_packs), before lang_packs:
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/descsync/build_descsync_pack.py <BASE pack dir> <OUT pack dir> [--check]
# clientY.sh:
#   S_descsync_pack() { docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/descsync/build_descsync_pack.py \
#     $C/azbase $C/out/pack; }; step descsync_pack $C/descsync.json S_descsync_pack
# Idempotent: a second run gives "unchanged".
import json
import os
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
SRC = os.path.join(REPO, 'client-patches', 'client-2.0.30', 'locale', 'locale', 'pl', 'itemdesc.txt')
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
NAME = 'locale/pl/itemdesc.txt'
# MT2009_PLUS_SEONHAE_DESC_V1 (8 November 2026, Discord: "w opisie fioletowy odlamek od 75, a przy bonusowaniu zielony"):
# the shards whose level range held the Lucent shards' levels - 39075 said 75-89, but a level-75 item (Miecz Zalu)
# takes the Zielony Lsniacy (39079) as the pl-wiki table, playerbot_seonhae.h and uiseonhae.py have it; likewise 30
# (Szary Lsniacy), 96 weapons/armours/helmets and 105 (Zolty Lsniacy) - 39071 31-39, 39075 76-89, 39076 and 39077
# 106-119 now say so.
SYNC = ('30368', '30369', '30370', '39071', '39075', '39076', '39077')


def rows_of(b):
	out = {}
	for line in b.split(b'\n'):
		k = line.split(b'\t', 1)[0].strip()
		if k:
			out[k.decode('latin-1')] = line.rstrip(b'\r')
	return out


def patch(b):
	want = rows_of(open(SRC, 'rb').read())
	lines = b.split(b'\n')
	changed = []
	for i, line in enumerate(lines):
		k = line.split(b'\t', 1)[0].strip().decode('latin-1')
		if k in SYNC and k in want:
			cr = b'\r' if line.endswith(b'\r') else b''
			if line.rstrip(b'\r') != want[k]:
				lines[i] = want[k] + cr
				changed.append(k)
	return b'\n'.join(lines), changed


def main():
	import m2pack
	import packlib
	args = [a for a in sys.argv[1:] if not a.startswith('--')]
	check = '--check' in sys.argv
	base, out = args[:2]
	src = out if os.path.exists(os.path.join(out, 'dbdata.index')) else base
	f, v, ents = m2pack.read_index(os.path.join(src, 'dbdata.index'))
	dat = packlib.rd(os.path.join(src, 'dbdata.data'))
	have = dict((e['name'], e) for e in ents)
	b = m2pack.read_entry(dat, have[NAME])
	nb, changed = patch(b)
	report = {'changed_rows': changed}
	if nb == b:
		report['dbdata'] = 'unchanged'
	elif check:
		report['dbdata'] = dict(replace=[NAME])
	else:
		ti, td = os.path.join(out, 'dbdata.index.descsync'), os.path.join(out, 'dbdata.data.descsync')
		r = packlib.repack_add_typed(os.path.join(src, 'dbdata.index'), os.path.join(src, 'dbdata.data'), {NAME: nb}, {},
			ti, td, ents[-1]['raw'])
		os.replace(ti, os.path.join(out, 'dbdata.index'))
		os.replace(td, os.path.join(out, 'dbdata.data'))
		f, v, nw = m2pack.read_index(os.path.join(out, 'dbdata.index'))
		nd = packlib.rd(os.path.join(out, 'dbdata.data'))
		assert len(set(e['name'] for e in nw)) == len(nw)
		for e in nw:
			assert zlib.crc32(nd[e['pos']:e['pos'] + e['size']]) & 0xffffffff == e['dcrc'], e['name']
			got = m2pack.read_entry(nd, e)
			if e['name'] == NAME:
				assert got == nb
			else:
				assert got == m2pack.read_entry(dat, have[e['name']]), e['name']
		report['dbdata'] = dict(old=r[0], replaced=r[2], entries=len(nw), replaced_names=[NAME])
	print(json.dumps(report, indent=1))


if __name__ == '__main__':
	main()
