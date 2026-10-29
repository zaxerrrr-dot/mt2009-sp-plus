# -*- coding: utf-8 -*-
# MT2009_PLUS_AUTOHUNT_TEST_V1 - checks the pack build_autohunt_test_packs.py wrote (on the OUT of the whole Yohara chain):
#   autohunttest.index / .data hold exactly the package's names (autohunt_test_files.json: size, sha256, entry type -
#   the circle's 3 and the TEST window's 20 .sub + its atlas), every entry's crc and read-back; pack/Index lists
#   "autohunttest" once; the effect names its mesh, the mesh its texture, all three in the pack. Then, on the players'
#   install (klient-test-2.37 + yohara-3.0.1 zips + OUT, tools/uicheck/check_ui_assets.py - NOT the exe smoke client,
#   whose etc pack is not the players'), every picture the TEST window opens (root uiscript/autohunttest*.py,
#   uiautohunt_test.py) and the image every .sub of the pack cuts.
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/autohunt_test/verify_autohunt_test.py \
#     <OUT pack dir>
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
import build_autohunt_test_packs as B  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith('--')]
OUT = args[0]
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', 'root'))
fails = []


def pack_entries(d, p):
    f, v, ents = m2pack.read_index(os.path.join(d, p + '.index'))
    return ents, packlib.rd(os.path.join(d, p + '.data'))


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
if packs.count(B.PACK.encode()) != 1:
    fails.append('pack/Index: %s listed %d times' % (B.PACK, packs.count(B.PACK.encode())))

eff = got.get(B.EFFECT, b'')
for mesh in set(re.findall(rb'MeshFileName\s+"([^"]+)"', eff)):
    name = B.EFFECT.rsplit('/', 1)[0] + '/' + mesh.decode('latin-1').lower()
    if name not in got:
        fails.append('%s: names %s, not in the pack' % (B.EFFECT, name))
for tex in set(re.findall(rb'[A-Za-z]:\\[^\x00]+?\.dds', got.get(B.MESH, b''), re.I)):
    name = 'd:/' + tex.decode('latin-1').replace('\\', '/').lower()[3:]
    if name not in got:
        fails.append('%s: names %s, not in the pack' % (B.MESH, name))

# the players' install (klient-test-2.37 + yohara-3.0.1 zips + OUT; tools/uicheck): every picture the TEST window opens
# - and the image each of its .sub cuts - is in a pack the client lists (3.0.4 counted the exe smoke client's etc,
# which is not the players' etc, and Alt+H died on auto_system_edit_line.sub)
sys.path.insert(0, os.path.join(HERE, '..', 'uicheck'))
import check_ui_assets as U  # noqa: E402
probs, inst, images = U.feature_problems(OUT, ['uiautohunt_test.py', 'uiscript/autohunttestwindow.py',
                                              'uiscript/autohunttestoptionwindow.py',
                                              'uiscript/autohunttestrangewindow.py'],
                                         names=[n for n in m if n.endswith('.sub')], root=ROOT)
fails += probs
for n in sorted(m):
    w = inst.where(n)
    if not w or w[0] != B.PACK:
        fails.append('%s: the install opens it from %s, not %s' % (n, w, B.PACK))
etc_same = None
print('autohunttest: %d files, %d window picture(s) checked against the players\' install, %d problem(s)'
      % (len(got), images, len(fails)))
for f in fails:
    print('  ' + f)
sys.exit(1 if fails else 0)
