# -*- coding: utf-8 -*-
# MT2009_PLUS_FIRE_GHOST_V1 - checks the pack build_fireghost_pack.py wrote (on the OUT of the whole Yohara chain):
#   fireghost.index / fireghost.data hold exactly the package's 38 names (fireghost_files.json: size, sha256, entry
#   type), every entry's crc and read-back; pack/Index has "fireghost" as its first pack (ahead of monster2, etc and
#   gf_razador, which carry the same names); no .msa / .msm of the set names the looping fire_ghost_body.mse and no
#   .msm attaches an effect for good (AttachingDataType 2); fire_ghost_body_gf.mse does not loop; the files the set
#   names outside itself (redburn.dds, fire_ghost_fireball.msf) are in a listed pack - "redburn_1 copy.dds" is in
#   the players' base install (etc / gf_official, packs this tree does not hold), named by gf_razador's own
#   fire_ghost_body.mse already; the set's files other than the 12 .msa are byte for byte gf_razador's, the new
#   effect fire_ghost_body_gf.mse is gf_razador's fire_ghost_body.mse.
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/fireghost/verify_fireghost.py \
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
import build_fireghost_pack as B  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith('--')]
OUT = args[0]
BASE = args[1] if len(args) > 1 else '/opt/metin2/cache/cY/azbase'
BASE_INSTALL = {'d:/ymir work/pc/assassin/effect/redburn_1 copy.dds'}
GF_BODY = 'd:/ymir work/effect/monster2/fire_ghost_body.mse'
fails = []
WHERE = {}
for _d in (BASE, OUT):          # OUT last: a pack there is the one the client gets
    for _f in os.listdir(_d):
        if _f.endswith('.index') and _f[:-6] != B.PACK:
            for e in m2pack.read_index(os.path.join(_d, _f))[2]:
                WHERE[e['name']] = (_d, _f[:-6])


def pack_entries(d, p):
    f, v, ents = m2pack.read_index(os.path.join(d, p + '.index'))
    dat = packlib.rd(os.path.join(d, p + '.data'))
    return ents, dat


m = B.manifest()
got = {}
if not os.path.exists(os.path.join(OUT, B.PACK + '.index')):
    fails.append('%s.index: not in OUT' % B.PACK)
else:
    ents, dat = pack_entries(OUT, B.PACK)
    for e in ents:
        if zlib.crc32(dat[e['pos']:e['pos'] + e['size']]) & 0xffffffff != e['dcrc']:
            fails.append('%s: data crc' % e['name'])
            continue
        b = m2pack.read_entry(dat, e)
        got[e['name']] = b
        w = m.get(e['name'])
        if w is None:
            fails.append('%s: not in the package' % e['name'])
        elif len(b) != w['size'] or hashlib.sha256(b).hexdigest() != w['sha256']:
            fails.append('%s: not the package\'s bytes' % e['name'])
        elif e['ctype'] != w['ctype']:
            fails.append('%s: entry type %d, the package %d' % (e['name'], e['ctype'], w['ctype']))
    fails += ['%s: missing' % n for n in sorted(set(m) - set(got))]

ix = open(os.path.join(OUT, 'Index'), 'rb').read() if os.path.exists(os.path.join(OUT, 'Index')) else b''
packs = [l.strip() for l in ix.replace(b'\r\n', b'\n').split(b'\n')]
if packs[:3] != [b'PACK', b'*', B.PACK.encode()]:
    fails.append('pack/Index: %s is not the first pack' % B.PACK)

for n, b in got.items():
    if n.endswith(('.msa', '.msm')) and B.OLD_EFFECT in b.lower():
        fails.append('%s: names the looping fire_ghost_body.mse' % n)
    if n.endswith('.msm') and re.search(rb'AttachingDataType\s+2', b):
        fails.append('%s: attaches an effect for good' % n)
eff = got.get(B.NEW_EFFECT, b'')
if not re.search(rb'CycleLoopEnable\s+0', eff) or re.search(rb'CycleLoopEnable\s+1', eff):
    fails.append('%s: loops' % B.NEW_EFFECT)
msa_new = [n for n, b in got.items() if n.endswith('.msa') and b'fire_ghost_body_gf.mse' in b]

# outside references
refs = set()
for n, b in got.items():
    for r in re.findall(rb'"([^"]+\.(?:dds|mse|msf|gr2|tga))"', b, re.I):
        r = r.decode('latin-1').replace('\\', '/').lower()
        if '/' not in r:
            r = n.rsplit('/', 1)[0] + '/' + r
        refs.add(r)
for r in sorted(refs):
    if r not in got and r not in WHERE and r not in BASE_INSTALL:
        fails.append('%s: named by the set, in no listed pack' % r)

# the rest is GF's (gf_razador) byte for byte
same = 0
if 'd:/ymir work/monster2/fire_ghost/fire_ghost.msm' in WHERE:
    d, p = WHERE['d:/ymir work/monster2/fire_ghost/fire_ghost.msm']
    ents, dat = pack_entries(d, p)
    gf = dict((e['name'], e) for e in ents)
    for n, b in got.items():
        if n.endswith('.msa'):
            continue
        g = GF_BODY if n == B.NEW_EFFECT else n
        if g not in gf or m2pack.read_entry(dat, gf[g]) != b:
            fails.append('%s: not %s\'s bytes' % (n, p))
        else:
            same += 1
print('fireghost: %d files, %d .msa on the 1 s effect, %d equal to GF\'s, %d outside refs, %d problem(s)'
      % (len(got), len(msa_new), same, len(refs - set(got)), len(fails)))
for f in fails:
    print('  ' + f)
sys.exit(1 if fails else 0)
