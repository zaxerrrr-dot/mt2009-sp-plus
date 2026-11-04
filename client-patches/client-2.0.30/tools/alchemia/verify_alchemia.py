# -*- coding: utf-8 -*-
# MT2009_PLUS_ALCHEMY_WIKI_NAMES_V1 - checks what build_alchemia_pack.py wrote (on the OUT of the whole Yohara chain):
#   locale/pl/locale_game.txt has every DS_APPLY_ line of alchemia_names.py once, with its exact text, and is not
#   shorter than the BASE's (other steps patch it too); every name formats with a value; every <POINT>
#   is a point the root code knows (player.POINT_<POINT> in the exe's module list below, or DS_FALLBACK_POINTS of
#   root localeinfo_point.py); the root code that reads them is there (localeinfo_point.GetDragonSoulApplyString,
#   uitooltip.py's ITEM_TYPE_DS branch calls it).
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/alchemia/verify_alchemia.py \
#     <OUT pack dir> [<BASE pack dir>]
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/c36')
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, HERE)
import m2pack  # noqa: E402
import packlib  # noqa: E402
import alchemia_names as an  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith('--')]
OUT = args[0]
BASE = args[1] if len(args) > 1 else '/opt/metin2/cache/c55/pack'
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', 'root'))
NAME = 'locale/pl/locale_game.txt'
fails = []


def entry(d, name):
    f, v, ents = m2pack.read_index(os.path.join(d, 'locale.index'))
    have = dict((e['name'], e) for e in ents)
    return m2pack.read_entry(packlib.rd(os.path.join(d, 'locale.data')), have[name])


def strip(data):
    return b''.join(l for l in data.splitlines(True) if not l.startswith(an.PREFIX.encode('ascii')))


got = entry(OUT if os.path.exists(os.path.join(OUT, 'locale.index')) else BASE, NAME)
base = entry(BASE, NAME)
have = an.parse(got)
count = sum(1 for l in got.split(b'\n') if l.startswith(an.PREFIX.encode('ascii')))
if count != len(an.NAMES):
    fails.append('%d DS_APPLY_ lines, want %d' % (count, len(an.NAMES)))
for key, text in an.NAMES:
    if have.get(key) != text:
        fails.append('%s%s: %r, want %r' % (an.PREFIX, key, have.get(key), text))
    try:
        s = text % ('2.400' if '%s' in text else 6)
    except (TypeError, ValueError) as e:
        fails.append('%s: does not format (%s)' % (key, e))
        continue
    if any(w in s.lower() for w in an.FORBIDDEN):
        fails.append('%s: forbidden word' % key)
# the rest of the file: other steps (balathor, maps302, zodiak) patch it too, so only its size is checked - not less
# than the base's without the DS_APPLY_ lines
if len(strip(got)) < len(strip(base)):
    fails.append('%s: shorter than the base (lines lost?)' % NAME)

lp = open(os.path.join(ROOT, 'localeinfo_point.py'), 'rb').read().decode('cp1250')
tt = open(os.path.join(ROOT, 'uitooltip.py'), 'rb').read().decode('cp1250')
if 'def GetDragonSoulApplyString' not in lp:
    fails.append('root/localeinfo_point.py: no GetDragonSoulApplyString')
m = re.search(r'DS_FALLBACK_POINTS = \{(.*?)\}', lp, re.S)
fallback = set(re.findall(r'"([A-Z_]+)"', m.group(1))) if m else set()
# the POINT_ names the client's player module has (PythonPlayerModule.cpp of our exe source and the repo's exe patch),
# when they are here
SRCS = ('/opt/metin2/cache/client-build/Source/Source Client/UserInterface/PythonPlayerModule.cpp',
        os.path.normpath(os.path.join(HERE, '..', '..', '..', 'exe', 'UserInterface', 'PythonPlayerModule.cpp')))
module = None
for SRC in SRCS:
    if os.path.exists(SRC):
        module = (module or set()) | set(re.findall(r'"POINT_([A-Z0-9_]+)"', open(SRC, 'rb').read().decode('latin-1')))
for key, text in an.NAMES:
    p = key[6:] if key.startswith('BASIC_') else key
    if p in fallback or module is None:
        continue
    if p not in module:
        fails.append('%s: POINT_%s neither in the player module nor in DS_FALLBACK_POINTS' % (key, p))
if not re.search(r'ITEM_TYPE_DS == itemType:.*?dragonSoul\s*=\s*True', tt, re.S):
    fails.append('root/uitooltip.py: the ITEM_TYPE_DS branch does not ask for the alchemy names')
print('alchemia: %d dragon stone bonus names checked%s, %d problem(s)'
      % (len(an.NAMES), '' if module is not None else ' (player module source not here - points not checked)', len(fails)))
for f in fails:
    print('  ' + f)
sys.exit(1 if fails else 0)
