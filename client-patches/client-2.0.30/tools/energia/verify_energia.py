# -*- coding: utf-8 -*-
# MT2009_PLUS_ENERGY_V1 - checks the client part of System Energii (Krysztal Energii 51002, server-patches/energia) on
# the OUT of the whole Yohara chain:
#   energia.index / energia.data hold exactly the manifest's four pictures (energia_files.json: size, sha256, entry
#   type), every entry's crc and read-back; pack/Index lists "energia";
#   the energy bar's scripts (locale/pl/ui/energybar.py, uiscript/energybar.py - OUT or BASE) name only pictures this
#   pack has;
#   the root pack (OUT, else BASE) has the bar always on (interfacemodule.py), its tooltip and the once-a-second colour
#   (uitaskbar.py) and the crystal's tooltip line (uitooltip.py) - each with the marker.
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/energia/verify_energia.py \
#     <OUT pack dir> [<BASE pack dir>]
import hashlib
import os
import re
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, HERE)
import m2pack  # noqa: E402
import packlib  # noqa: E402
import build_energia_pack as B  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith('--')]
OUT = args[0]
BASE = args[1] if len(args) > 1 else '/opt/metin2/cache/cY/azbase'
MARK = b'MT2009_PLUS_ENERGY_V1'
fails = []


def entries(pack):
    """{name: bytes} of pack from OUT, else BASE (None: in neither)"""
    for d in (OUT, BASE):
        if os.path.exists(os.path.join(d, pack + '.index')):
            f, v, ents = m2pack.read_index(os.path.join(d, pack + '.index'))
            dat = packlib.rd(os.path.join(d, pack + '.data'))
            return dict((e['name'], e) for e in ents), dat
    return None, None


m = B.manifest()
got = {}
if not os.path.exists(os.path.join(OUT, B.PACK + '.index')):
    fails.append('%s.index: not in OUT' % B.PACK)
else:
    f, v, ents = m2pack.read_index(os.path.join(OUT, B.PACK + '.index'))
    dat = packlib.rd(os.path.join(OUT, B.PACK + '.data'))
    for e in ents:
        if zlib.crc32(dat[e['pos']:e['pos'] + e['size']]) & 0xffffffff != e['dcrc']:
            fails.append('%s: data crc' % e['name'])
            continue
        b = m2pack.read_entry(dat, e)
        got[e['name']] = b
        w = m.get(e['name'])
        if w is None:
            fails.append('%s: not in the manifest' % e['name'])
        elif len(b) != w['size'] or hashlib.sha256(b).hexdigest() != w['sha256']:
            fails.append('%s: not the manifest\'s bytes' % e['name'])
        elif e['ctype'] != w['ctype']:
            fails.append('%s: entry type %d, the manifest %d' % (e['name'], e['ctype'], w['ctype']))
    fails += ['%s: missing' % n for n in sorted(set(m) - set(got))]

ix = open(os.path.join(OUT, 'Index'), 'rb').read() if os.path.exists(os.path.join(OUT, 'Index')) else b''
packs = [l.strip() for l in ix.replace(b'\r\n', b'\n').split(b'\n')]
if not packs or packs[0] != b'PACK' or B.PACK.encode() not in packs:
    fails.append('pack/Index: no %s line' % B.PACK)

# the bar's scripts name only this pack's pictures
scripts = 0
for pack, name in (('locale', 'locale/pl/ui/energybar.py'), ('root', 'uiscript/energybar.py')):
    idx, dat = entries(pack)
    if idx is None or name not in idx:
        fails.append('%s: not in pack %s' % (name, pack))
        continue
    scripts += 1
    src = m2pack.read_entry(dat, idx[name])
    pics = set(p.decode('latin-1').replace('\\', '/').lower() for p in re.findall(rb'"([^"]+\.tga)"', src, re.I))
    if not pics:
        fails.append('%s: names no picture' % name)
    for p in sorted(pics):
        if p not in m:
            fails.append('%s: names %s, not in pack %s' % (name, p, B.PACK))

# the root's code
idx, dat = entries('root')
want = {
    'interfacemodule.py': [MARK + rb'[^\n]*\n[^\n]*\n\t\tif True:\n\t\t\twndEnergyBar = uiTaskBar\.EnergyBar\(\)'],
    'uitaskbar.py': [rb'bonusy ekwipunku \+%d%%', rb'mt2009EnergyNext', rb'player\.ENERGY_END_TIME'],
    'uitooltip.py': [rb'"POINT_ENERGY", 128\)', rb'Bonusy ekwipunku \+%d%%'],
}
for name, pats in sorted(want.items()):
    if idx is None or name not in idx:
        fails.append('root: %s missing' % name)
        continue
    src = m2pack.read_entry(dat, idx[name]).replace(b'\r\n', b'\n')
    if MARK not in src:
        fails.append('root %s: no %s' % (name, MARK.decode()))
    for p in pats:
        if not re.search(p, src):
            fails.append('root %s: no %r' % (name, p))

print('energia: %d pictures, %d bar scripts, root %d files checked, %d problem(s)'
      % (len(got), scripts, len(want), len(fails)))
for f in fails:
    print('  ' + f)
sys.exit(1 if fails else 0)
