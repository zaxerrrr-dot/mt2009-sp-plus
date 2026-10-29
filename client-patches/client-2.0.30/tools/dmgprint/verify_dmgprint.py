# -*- coding: utf-8 -*-
# MT2009_PLUS_DAMAGE_PRINT_V1 - checks the pack build_dmgprint_pack.py wrote (on the OUT of the whole Yohara chain):
#   dmgprint.index / dmgprint.data hold exactly the manifest's names (dmgprint_files.json: size, sha256, entry type),
#   every entry's crc and read-back; pack/Index lists "dmgprint"; no other listed pack carries a damagevalue2/ name;
#   every texture the ten registered .mse files name is in the pack; the exe overlay registers those ten files from
#   damagevalue2/ (PythonPlayerSettingsModule.cpp) and builds the digit names from the same folder (InstanceBaseEffect.cpp).
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/dmgprint/verify_dmgprint.py \
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
import build_dmgprint_pack as B  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith('--')]
OUT = args[0]
BASE = args[1] if len(args) > 1 else '/opt/metin2/cache/cY/azbase'
EXE = os.path.normpath(os.path.join(HERE, '..', '..', '..', 'exe', 'UserInterface'))
fails = []

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

for _d in (BASE, OUT):
    if not os.path.isdir(_d):
        continue
    for _f in sorted(os.listdir(_d)):
        if _f.endswith('.index') and _f[:-6] != B.PACK:
            for e in m2pack.read_index(os.path.join(_d, _f))[2]:
                if e['name'].startswith(B.FOLDER):
                    fails.append('%s also in %s' % (e['name'], _f[:-6]))

for f in B.EFFECTS:
    b = got.get(B.FOLDER + f, b'')
    if not b:
        continue
    for t in B.mse_textures(b, B.FOLDER + f):
        if t not in got:
            fails.append('%s names %s - not in the pack' % (f, t))

settings = open(os.path.join(EXE, 'PythonPlayerSettingsModule.cpp'), 'rb').read()
for f in B.EFFECTS:
    if (B.FOLDER + f).encode() not in settings:
        fails.append('exe PythonPlayerSettingsModule.cpp: %s not registered' % f)
effect = open(os.path.join(EXE, 'InstanceBaseEffect.cpp'), 'rb').read()
if B.FOLDER.encode() not in effect:
    fails.append('exe InstanceBaseEffect.cpp: the digits are not read from %s' % B.FOLDER)

print('dmgprint: %d files (%d effects, %d digits), %d problem(s)' % (len(got), len(B.EFFECTS), len(B.DIGITS), len(fails)))
for f in fails:
    print('  ' + f)
sys.exit(1 if fails else 0)
