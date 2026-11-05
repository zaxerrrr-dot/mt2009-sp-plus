# -*- coding: utf-8 -*-
# MT2009_PLUS_KOLA_V1 - checks the F12 "Kolo Losu" window's data against the wheels of the shop
# (linux-port/docker/itemshop/app/itemshop/kola/kola.json), so a wheel added there (246 Kolo Plomieni Nocy,
# 5 Nov 2026) is not left with the previous wheel's name and background in the game:
#   the repo: root/koladata.py (make_kola_ui.py) has every wheel of the rotation with its name (CP1250), its
#   background and the 16 idle field pictures per tier of kola.json; every picture it names is in
#   root/mt2009_ui/kola/;
#   with <OUT pack dir>: the built root pack (OUT, else BASE) carries this koladata.py and every picture it names,
#   byte for byte as the repo.
#   python3 verify_kola_ui.py                       (repo only)
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/kola/verify_kola_ui.py \
#     <OUT pack dir> [<BASE pack dir>]
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
ROOT = os.path.join(REPO, 'client-patches', 'client-2.0.30', 'root')
KOLA = os.path.join(REPO, 'linux-port', 'docker', 'itemshop', 'app', 'itemshop', 'kola', 'kola.json')

args = [a for a in sys.argv[1:] if not a.startswith('--')]
OUT = args[0] if args else None
BASE = args[1] if len(args) > 1 else '/opt/metin2/cache/cY/azbase'
fails = []

cfg = json.load(open(KOLA, 'rb'))
src = open(os.path.join(ROOT, 'koladata.py'), 'rb').read()
data = {}
exec(compile(src.decode('latin-1'), 'koladata.py', 'exec'), data)
UI = data['UI']
wheels = data['WHEELS']
order = cfg['rotation']['order']
if sorted(wheels) != sorted(order):
    fails.append('koladata.py wheels %s, the rotation %s - run make_kola_ui.py' % (sorted(wheels), sorted(order)))
named = set()
for wid in order:
    w = wheels.get(wid)
    want = cfg['wheels'][str(wid)]
    if not w:
        continue
    if w['name'].encode('latin-1').decode('cp1250') != want['name']:
        fails.append('wheel %d: name %r, kola.json %r' % (wid, w['name'], want['name']))
    if w['bg'] != UI + 'bg_%d.jpg' % wid:
        fails.append('wheel %d: background %s' % (wid, w['bg']))
    named.add(w['bg'])
    if sorted(w['fields']) != sorted(int(t) for t in want['fields']):
        fails.append('wheel %d: tiers %s, kola.json %s' % (wid, sorted(w['fields']), sorted(want['fields'])))
    for t, pics in want['fields'].items():
        got = list(w['fields'].get(int(t), ()))
        exp = [UI + 'f/' + n[2:14] + '.png' for n in pics]
        if got != exp:
            fails.append('wheel %d tier %s: field pictures differ from kola.json' % (wid, t))
        named.update(got)
for p in sorted(named):
    if not os.path.isfile(os.path.join(ROOT, p)):
        fails.append('root/%s: missing' % p)

packed = 0
if OUT:
    sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
    sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
    import m2pack  # noqa: E402
    import packlib  # noqa: E402
    idx = None
    for d in (OUT, BASE):
        if os.path.exists(os.path.join(d, 'root.index')):
            f, v, ents = m2pack.read_index(os.path.join(d, 'root.index'))
            dat = packlib.rd(os.path.join(d, 'root.data'))
            idx = dict((e['name'], e) for e in ents)
            break
    if idx is None:
        fails.append('root.index: in neither %s nor %s' % (OUT, BASE))
    else:
        for name in ['koladata.py'] + sorted(named):
            e = idx.get(name)
            if e is None:
                fails.append('root pack: %s missing' % name)
                continue
            got = m2pack.read_entry(dat, e)
            mine = open(os.path.join(ROOT, name), 'rb').read()
            if name.endswith('.py'):
                got, mine = got.replace(b'\r\n', b'\n'), mine.replace(b'\r\n', b'\n')
            if got != mine:
                fails.append('root pack: %s is not the repo\'s' % name)
            packed += 1

print('kola ui: %d wheels, %d pictures named, %d root pack files checked, %d problem(s)'
      % (len(order), len(named), packed, len(fails)))
for f in fails:
    print('  ' + f)
sys.exit(1 if fails else 0)
