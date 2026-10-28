# -*- coding: utf-8 -*-
# MT2009_PLUS_COMMUNITY_V1 - the Community window's graphics (root/uicommunity.py; the package "Community System
# (Messenger Renewal)", Autor: Best Studio - its 02. Client/d_ files, which are the GF 26.1.11 client's bytes):
#   d:/ymir work/ui/messengers_01.dds                       the window's atlas (DXT, 275 024 B)
#   d:/ymir work/ui/game/windows/community_*.sub (70)       its pieces, CRLF as in GF; community_config_subtopic_title_bg
#                                                           points at our windows_yohara.dds (GF's windows.dds, root pack)
# They are in client-patches/client-2.0.30/community/d_ (d_/ = d:/) and go into a new pack, community_ui, with its
# Index line; no other pack may have one of the names. The window also uses mt2009_ui/checkbox/*.tga (root pack).
# Run on the same OUT as the other builders, before yfinal (clientY.sh):
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/community/build_community_packs.py $C/azbase \
#     $C/out/pack > $C/community.json
# then verify_community.py on OUT. --check measures only. Idempotent: a second run gives "in out".
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
SRC = os.path.normpath(os.path.join(HERE, '..', '..', 'community'))
NEW_PACK = 'community_ui'
TEXT = ('.txt', '.msa', '.msm', '.mse', '.mss', '.msenv', '.sub', '.prb', '.prd', '.pre', '.prt', '.py', '.ifl', '.pra')


def ctype(name):
	return 2 if name.endswith(TEXT) else 1


def new_pack_files():
	out = {}
	for dp, dn, fn in os.walk(os.path.join(SRC, 'd_')):
		for f in fn:
			rel = os.path.relpath(os.path.join(dp, f), SRC).replace(os.sep, '/')
			name = 'd:' + rel[2:]
			assert name == name.lower(), name
			out[name] = open(os.path.join(dp, f), 'rb').read()
	subs = [n for n in out if n.endswith('.sub')]
	assert len(subs) == 70 and 'd:/ymir work/ui/messengers_01.dds' in out, (len(subs), sorted(out)[:3])
	assert out['d:/ymir work/ui/messengers_01.dds'][:4] == b'DDS ', 'not a dds'
	for n in subs:
		b = out[n]
		assert b.startswith(b'title subImage\r\n') and b'\r\nimage "' in b, n
	return out


def main():
	import m2pack
	import packlib
	args = [a for a in sys.argv[1:] if not a.startswith('--')]
	check = '--check' in sys.argv
	base, out = args[:2]
	rd = packlib.rd
	report = {}

	np = NEW_PACK
	files = new_pack_files()
	done = [d for d in (out, base) if os.path.exists(os.path.join(d, np + '.index'))]
	have_new = None
	if done:
		f, v, e2 = m2pack.read_index(os.path.join(done[0], np + '.index'))
		d2 = rd(os.path.join(done[0], np + '.data'))
		have_new = dict((e['name'], m2pack.read_entry(d2, e)) for e in e2)
	if have_new == files:
		report[np] = 'in out' if done[0] == out else 'in base'
	else:
		if done and done[0] == base and not os.path.exists(os.path.join(out, np + '.index')):
			report[np + '_base'] = 'BASE has another community_ui - replaced in OUT'
		for d in (base, out):
			for fn in sorted(os.listdir(d)):
				if fn.endswith('.index') and fn[:-6] != np:
					for e in m2pack.read_index(os.path.join(d, fn))[2]:
						assert e['name'] not in files, (np, e['name'], fn)
		if check:
			report[np] = dict(add=len(files))
		else:
			src = out if os.path.exists(os.path.join(out, 'root.index')) else base
			tmpl = m2pack.read_index(os.path.join(src, 'root.index'))[2][-1]['raw']
			tmp_i, tmp_d = os.path.join(out, np + '.index.cm'), os.path.join(out, np + '.data.cm')
			packlib.repack_add_typed(None, None, {}, dict((k, (b, ctype(k))) for k, b in files.items()), tmp_i, tmp_d, tmpl)
			os.replace(tmp_i, os.path.join(out, np + '.index'))
			os.replace(tmp_d, os.path.join(out, np + '.data'))
			f, v, nw = m2pack.read_index(os.path.join(out, np + '.index'))
			nd = rd(os.path.join(out, np + '.data'))
			got = dict((e['name'], m2pack.read_entry(nd, e)) for e in nw)
			assert got == files, np
			report[np] = dict(added=len(got), data_mb=round(len(nd) / 1e6, 2))
	if not check:
		ix_path = os.path.join(out, 'Index') if os.path.exists(os.path.join(out, 'Index')) else os.path.join(base, 'Index')
		ix = rd(ix_path)
		lines = [l.strip() for l in ix.replace(b'\r\n', b'\n').split(b'\n')]
		if np.encode() not in lines:
			ix = ix.rstrip(b'\r\n') + b'\n*\n' + np.encode() + b'\n'
		if ix != rd(ix_path) or ix_path != os.path.join(out, 'Index'):
			open(os.path.join(out, 'Index'), 'wb').write(ix)
			report['Index'] = 'written'
	print(json.dumps(report, indent=1))


if __name__ == '__main__':
	main()
