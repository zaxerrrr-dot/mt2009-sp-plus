# -*- coding: utf-8 -*-
# MT2009_PLUS_AUTOHUNT_TEST_V1 - checks the pack build_autohunt_test_packs.py wrote (on the OUT of the whole Yohara chain):
#   autohunttest.index / .data hold exactly the package's 3 names (autohunt_test_files.json: size, sha256, entry type),
#   every entry's crc and read-back; pack/Index lists "autohunttest" once; the effect names its mesh, the mesh its
#   texture, all three in the pack. With the players' base pack dir (default: the exe smoke client's packs, which hold the
#   base install's etc) it also checks that every image the TEST window names (root uiscript/autohunttest*.py,
#   uiautohunt_test.py) is in a listed pack, and reports whether etc already has the circle with the same bytes.
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/autohunt_test/verify_autohunt_test.py \
#     <OUT pack dir> [<base install pack dir>]
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
BASE_INSTALL = args[1] if len(args) > 1 else '/opt/metin2/cache/exebuild/smoke/client/pack'
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

# the base install: the window's images and the same circle in etc
etc_same = None
images = 0
if os.path.isdir(BASE_INSTALL):
    where = {}
    for f in os.listdir(BASE_INSTALL):
        if f.endswith('.index'):
            for e in m2pack.read_index(os.path.join(BASE_INSTALL, f))[2]:
                where[e['name']] = f[:-6]
    if os.path.exists(os.path.join(BASE_INSTALL, 'etc.index')):
        ents, dat = pack_entries(BASE_INSTALL, 'etc')
        etc = dict((e['name'], e) for e in ents)
        etc_same = all(n in etc and m2pack.read_entry(dat, etc[n]) == b for n, b in got.items()) if got else False
    names = set()
    sources = [os.path.join(ROOT, 'uiautohunt_test.py')] + [os.path.join(ROOT, 'uiscript', f) for f in
                                                             ('autohunttestwindow.py', 'autohunttestoptionwindow.py', 'autohunttestrangewindow.py')]
    for path in sources:
        text = open(path, 'rb').read().decode('latin-1')
        consts = dict(re.findall(r'^([A-Z_]+)\s*=\s*"([^"]+/)"', text, re.M))
        for prefix, rest in re.findall(r'(?:([A-Z_]+)\s*\+\s*)?["\']([^"\']+\.(?:sub|tga|dds))["\']', text):
            if prefix and prefix not in consts:
                continue	# SMALL + "1.sub": below
            full = (consts[prefix] + rest) if prefix else rest
            if '/' not in full and 'ROOT' in consts:
                full = consts['ROOT'] + full	# a bare name handed to a helper that adds ROOT (_TextBar)
            if full.startswith('d:/'):
                names.add(full.lower())
        # the images named with a counter ("..._0" + "1.sub")
        for prefix in re.findall(r'^SMALL\s*=\s*"([^"]+)"', text, re.M):
            for n in '123':
                names.add((prefix + n + '.sub').lower())
    for n in sorted(names):
        if n.endswith('_0.sub') and 'public/small_button' in n:
            continue
        images += 1
        if n not in where:
            fails.append('%s: named by the window, in no pack of %s' % (n, BASE_INSTALL))
else:
    print('(no base install pack dir %s - the window\'s images not checked)' % BASE_INSTALL)

print('autohunttest: %d files, %d window image(s) found, base etc has the circle with the same bytes: %s, %d problem(s)'
      % (len(got), images, etc_same, len(fails)))
for f in fails:
    print('  ' + f)
sys.exit(1 if fails else 0)
