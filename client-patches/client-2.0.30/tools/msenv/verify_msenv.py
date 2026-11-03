# -*- coding: utf-8 -*-
# MT2009_PLUS_MAP_ENVIRONMENT_V1 - every map the client can load has an environment exe 2.0.25 loads (msenvlib.py has
# the exe's path; a map without one floods syserr with "CMapOutdoor::RenderBeforeLensFlare mc_pEnvironmentData is NULL"
# every frame and has no sky, fog or lights). On the whole pack set (OUT over BASE, pack/Index order, first pack wins):
#   for every atlasinfo row and every maps/<x>/setting.txt of our packs (a copied map: its ParentMapName folder's):
#     setting.txt is in our packs (else: the base client's map - counted, not checkable on vps1, its packs are not here)
#     -> the environment the exe picks (the map folder's copy, else d:/ymir work/environment/<name>) is in a listed
#     pack of ours, CTextFileLoader loads it (every group closed, no key without a value inside a group), its Group Fog
#     has NearDistance/FarDistance and no GF "foglevel"; the textures it names (skybox faces, cloud, main flare) are in
#     our packs (else a note: the base client may have them);
#   the pack "ymsenv" (build_msenv_pack.py) holds exactly what the builder computes, its entries read back, and
#   pack/Index lists it; the night environments root's game.py / constinfo.py register (a note when none of our packs
#   has one: background.RegisterEnvironmentData only logs and the day environment stays).
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/msenv/verify_msenv.py \
#     <OUT pack dir> [<BASE pack dir>]
# Output ends with "FAIL (n):" as the other verifiers; exit 1 on a failure.
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
import msenvlib as L  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith('--')]
OUT = args[0]
BASE = args[1] if len(args) > 1 else '/opt/metin2/cache/cY/azbase'
if not os.path.exists(os.path.join(BASE, 'Index')) and not os.path.exists(os.path.join(OUT, 'Index')):
    raise SystemExit('no pack/Index in %s or %s' % (OUT, BASE))
fails, notes = [], []

view = L.View(OUT, BASE)
maps = L.map_folders(view)
n_ok = n_base = n_local = 0
for name in sorted(maps):
    r = L.resolve(view, name)
    if r['state'] == 'base':
        n_base += 1
        continue
    if r['state'] != 'ok':
        fails.append('%s: copied map, its parent folder %s has no Setting.txt' % (name, r['dir']))
        continue
    b = view.get(r['path'])
    if b is None:
        fails.append('%s: environment %s (setting.txt "%s") is in no pack of ours - mc_pEnvironmentData NULL'
                     % (name, r['path'], r['env']))
        continue
    fatal, fog, tree = L.check_env(b)
    if fatal:
        fails.append('%s: %s (%s): %s - mc_pEnvironmentData NULL' % (name, r['path'], view.pack_of(r['path']),
                                                                     '; '.join(fatal)))
        continue
    for f in fog:
        fails.append('%s: %s: %s' % (name, r['path'], f))
    for t in L.env_textures(tree):
        if not view.has(t):
            notes.append('%s: %s names %s - in no pack of ours (the base client may have it)' % (name, r['path'], t))
    n_ok += 1
    n_local += r['local']

# the pack this tool writes: exactly what the builder computes without it
need = L.needed(L.View(OUT, BASE, skip=(L.PACK,)))
ip, dp = os.path.join(OUT, L.PACK + '.index'), os.path.join(OUT, L.PACK + '.data')
got = {}
if os.path.exists(ip):
    f, v, ents = m2pack.read_index(ip)
    dat = packlib.rd(dp)
    for e in ents:
        if zlib.crc32(dat[e['pos']:e['pos'] + e['size']]) & 0xffffffff != e['dcrc']:
            fails.append('%s: %s data crc' % (L.PACK, e['name']))
            continue
        got[e['name']] = m2pack.read_entry(dat, e)
    if L.PACK not in view.packs:
        fails.append('pack/Index: no %s line' % L.PACK)
    for n, (b, m, e) in sorted(need.items()):
        if got.get(n) != b:
            fails.append('%s: %s (%s) %s' % (L.PACK, n, m, 'missing' if n not in got else 'not env/%s' % e.lower()))
        elif view.pack_of(n) != L.PACK:
            fails.append('%s: %s is read from %s' % (L.PACK, n, view.pack_of(n)))
    for n in sorted(set(got) - set(need)):
        notes.append('%s: %s no longer needed' % (L.PACK, n))
elif need:
    fails.append('%s.index not in OUT; needed for %s' % (L.PACK, ', '.join(m for b, m, e in need.values())))

# the night environments of root (game.py __SetNightMode, constinfo.ENVIRONMENT_NIGHT)
night = set()
for py in ('game.py', 'constinfo.py'):
    b = view.get(py) or b''
    for m in re.findall(rb'"([a-z0-9_]+)"\s*:\s*"([a-z0-9_]+_night)"', b):
        night.add(L.ENVROOT + m[1].decode() + '.msenv')
    for m in re.findall(rb'"(d:/ymir work/environment/[^"%]+\.msenv)"', b, re.I):
        night.add(L.norm(m.decode()))
    if b'environment/%s.msenv' in b:
        night.add(L.ENVROOT + 'moonlight04.msenv')
for n in sorted(night):
    if not view.has(n):
        notes.append('night environment %s: in no pack of ours (the base client may have it)' % n)
    elif L.check_env(view.get(n))[0]:
        fails.append('night environment %s: %s' % (n, L.check_env(view.get(n))[0]))

print('msenv: %d maps (%d atlas rows), %d with a loadable environment of ours (%d in their folder), %d the base '
      'client\'s (setting.txt in no pack here); %s: %d file(s) for %s; %d base-client packs not on this host'
      % (len(maps), sum(1 for v in maps.values() if v == 'atlas'), n_ok, n_local, n_base, L.PACK, len(got),
         ', '.join(sorted(set(m for b, m, e in need.values()))) or '-', len(view.missing)))
for n in notes:
    print('  note: ' + n)
print('FAIL (%d):' % len(fails))
for f in fails:
    print('  ' + f)
sys.exit(1 if fails else 0)
