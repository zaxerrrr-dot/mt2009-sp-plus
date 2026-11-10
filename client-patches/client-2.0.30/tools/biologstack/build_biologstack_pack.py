# -*- coding: utf-8 -*-
# MT2009_PLUS_BIOLOG_NO_CARRY_CAP_V1 (client side) - the client's gamedata/item_proto (pack "dbdata") gets the stack
# flags and sizes linux-port/docker/mariadb/playerbot/apply.sh gives world.item_proto (70c97ceb, the owner, 10 November
# 2026: "mozesz dropic wszystkie przedmioty do biologa bez limitu"): every Biologist herb, specimen and key item is
# STACKABLE with a stack of at least 200 - the herbs 50701-50706, the specimens 30006 30015 30047 30050 30165-30168
# 30251 30252 31230-31232 and the keys 30220-30228. The package left the keys unstackable (flag 0) in the client too,
# so the client refused to put a second key on the first even though the server stacks them.
# The same rule as the SQL: flags |= STACKABLE, stack = max(stack, 200); antiflags untouched (none of these rows has
# ANTI_STACK); a record already right stays byte for byte.
#
# BUILD ORDER: after every other item_proto writer (runy_packs), before descsync_pack / lang_packs:
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/biologstack/build_biologstack_pack.py <BASE pack dir> <OUT pack dir> [--check]
# clientY.sh:
#   S_biologstack_pack() { docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     $T/biologstack/build_biologstack_pack.py $C/azbase $C/out/pack; }; step biologstack_pack $C/biologstack.json S_biologstack_pack
# Reads dbdata from OUT when an earlier step wrote it there, else from BASE; writes OUT/dbdata.*. Idempotent: a second
# run gives "unchanged". Then the panel's database editor base: python3 -m m2clientpack.make_base <out pack> <version>.
#
# The client item record (184 bytes; offsets as in tools/ystack307): stack 78 (uint32), antiflags 82, flags 86.
import json
import os
import struct
import sys
import zlib

sys.path.insert(0, '/opt/metin2/cache/c36')
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
NAME = 'gamedata/item_proto'
ITEM_KEY = (173217, 72619434, 408587239, 27973291)
RECORD = 184
FLAG_STACKABLE = 4
STACK = 200
VNUMS = sorted(set(list(range(50701, 50707)) + list(range(30220, 30229)) + list(range(30165, 30169)) +
                   list(range(31230, 31233)) + [30006, 30015, 30047, 30050, 30251, 30252]))


def patch(b):
	import m2pack
	assert b[:4] == b'MIPX'
	ver, stride, cnt, size = struct.unpack_from('<IIII', b, 4)
	assert stride == RECORD, stride
	raw = m2pack.mcoz_decode(b[20:], ITEM_KEY)
	recs = [raw[i * RECORD:(i + 1) * RECORD] for i in range(cnt)]
	changed, seen = [], set()
	for i, r in enumerate(recs):
		vnum = struct.unpack_from('<I', r, 0)[0]
		if vnum not in VNUMS:
			continue
		seen.add(vnum)
		stk, anti, flags = struct.unpack_from('<III', r, 78)
		nr = bytearray(r)
		struct.pack_into('<III', nr, 78, max(stk, STACK), anti, flags | FLAG_STACKABLE)
		if bytes(nr) != r:
			recs[i] = bytes(nr)
			changed.append(vnum)
	missing = sorted(set(VNUMS) - seen)
	assert not missing, 'records missing from the client item_proto: %s' % missing
	if not changed:
		return b, changed
	blob = m2pack.mcoz_encode(b''.join(recs), ITEM_KEY)
	return b'MIPX' + struct.pack('<IIII', ver, stride, len(recs), len(blob)) + blob, changed


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
	report = {'changed_vnums': changed}
	if nb == b:
		report['dbdata'] = 'unchanged'
	elif check:
		report['dbdata'] = dict(replace=[NAME])
	else:
		os.makedirs(out, exist_ok=True)
		ti, td = os.path.join(out, 'dbdata.index.biologstack'), os.path.join(out, 'dbdata.data.biologstack')
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
				assert patch(got)[1] == [], 'not idempotent'
			else:
				assert got == m2pack.read_entry(dat, have[e['name']]), e['name']
		report['dbdata'] = dict(old=r[0], replaced=r[2], entries=len(nw), replaced_names=[NAME])
	print(json.dumps(report, indent=1))


if __name__ == '__main__':
	main()
