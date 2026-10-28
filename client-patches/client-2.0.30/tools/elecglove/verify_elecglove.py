# -*- coding: utf-8 -*-
# MT2009_PLUS_ELEC_GLOVE_V1 - checks the pack build_elecglove_pack.py wrote (on the OUT of the whole Yohara chain):
#   elecglove.index / elecglove.data hold exactly the manifest's names (elecglove_files.json: size, sha256, entry type),
#   every entry's crc and read-back; pack/Index lists "elecglove"; 6th7th_attributes_blow.mse does not loop; every
#   texture it names (its own folder's 3-6.dds, effect/monster2/impact3.dds and smoke_dust.dds) is in this pack or in a
#   listed pack; the exe overlay registers that file for EFFECT_ELEC_ATTACK_HIT.
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/elecglove/verify_elecglove.py \
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
import build_elecglove_pack as B  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith('--')]
OUT = args[0]
BASE = args[1] if len(args) > 1 else '/opt/metin2/cache/cY/azbase'
EXE_SETTINGS = os.path.normpath(os.path.join(HERE, '..', '..', '..', 'exe', 'UserInterface',
                                             'PythonPlayerSettingsModule.cpp'))
fails = []
WHERE = {}
for _d in (BASE, OUT):
    for _f in os.listdir(_d):
        if _f.endswith('.index') and _f[:-6] != B.PACK:
            for e in m2pack.read_index(os.path.join(_d, _f))[2]:
                WHERE[e['name']] = _f[:-6]

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

eff = got.get(B.EFFECT, b'')
if not re.search(rb'CycleLoopEnable\s+0', eff) or re.search(rb'CycleLoopEnable\s+1', eff):
    fails.append('%s: loops or is missing' % B.EFFECT)
refs = set()
for r in re.findall(rb'"([^"]+\.(?:dds|tga|mse|mde|msf))"', eff, re.I):
    r = r.decode('latin-1').replace('\\', '/').lower()
    if '/' not in r:
        r = B.EFFECT.rsplit('/', 1)[0] + '/' + r
    refs.add(r)
outside = {}
for r in sorted(refs):
    if r in got:
        continue
    if r in WHERE:
        outside[r] = WHERE[r]
    else:
        fails.append('%s: named by the effect, in no listed pack' % r)

src = open(EXE_SETTINGS, 'rb').read() if os.path.exists(EXE_SETTINGS) else b''
if not re.search(rb'EFFECT_ELEC_ATTACK_HIT,\s*"",\s*"' + re.escape(B.EFFECT.encode()) + rb'"', src):
    fails.append('client-patches/exe PythonPlayerSettingsModule.cpp: EFFECT_ELEC_ATTACK_HIT does not load %s' % B.EFFECT)

print('elecglove: %d files, %d textures (%d in other packs: %s), %d problem(s)'
      % (len(got), len(refs), len(outside), ', '.join('%s=%s' % (os.path.basename(k), p) for k, p in sorted(outside.items())),
         len(fails)))
for f in fails:
    print('  ' + f)
sys.exit(1 if fails else 0)
