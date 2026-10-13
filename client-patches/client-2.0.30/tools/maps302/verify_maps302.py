# -*- coding: utf-8 -*-
# MT2009_PLUS_YOHARA_MAPS302_V1 - checks the packs build_maps302_packs.py wrote: everything maps 302, 303 and 304 name
# resolves to a name of the client (the OUT packs + the BASE listing c58.lst + the base client's pre-import listing):
#   each map folder (setting.txt with its size/base/ViewRadius, mapproperty.txt, the msenv copy; every sector's
#   areadata/areaproperty/areaambiencedata/attr.atr/height.raw/tile.raw/water.wtr/minimap.dds/shadowmap.*), the
#   textureset and its textures, the msenv (fog as exe 2.0.25 reads it) and its skybox, the atlas, every object of
#   every sector (areadata CRC -> a property of pack property -> its model/effect/tree and, for a Building, the
#   .mdatr), every race of the maps (npclist -> .msm) and every name the staged text files give; the new packs
#   under the 29 MB limit and in Index; with --locale, locale_game.txt's map names.
# Run in the m2pack-lzo image:
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/maps302/verify_maps302.py \
#     <OUT pack dir> [<work dir with c58.lst>] [<npclist.txt>]
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, os.path.join(HERE, '..', 'az58'))
import m2pack  # noqa: E402
import packlib  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith('--')]
OUT = args[0]
WORK = args[1] if len(args) > 1 else '/opt/metin2/cache/yohara/cape301-work'
NPCLIST = args[2] if len(args) > 2 else '/opt/metin2/cache/c61/chk/gamedata/npclist.txt'
PRE_LST = '/opt/metin2/cache/tcm/gf28/ourpacks_pre.txt'
ZIP_LIMIT = 29 * 1024 * 1024
MAN = json.load(open(os.path.join(HERE, 'maps302_manifest.json'), encoding='utf-8'))
MAPS = [(302, 'metin2_map_dawnmistwood', (7, 4), (1177600, 1664000)),
        (303, 'metin2_map_bayblacksand', (3, 6), (1049600, 1510400)),
        (304, 'metin2_map_mt_thunder', (4, 6), (1126400, 1510400))]
RACE_DIRS = ('guild', 'npc', 'npc2', 'npc_pet', 'npc_mount', 'monster', 'monster2')
# GF's own broken references (the official client has the same): reported, not failed
KNOWN = {'d:/ymir work/zone/b/obj/512.jpg', 'd:/ymir work/zone/\xb0\xf8\xbf\xeb/hay_01.gr2',
         # the Red Chief bosses' (3591, 3596) attack motions name the other folder's or misspelt files, and
         # ray_blue1.mse (Triton boss 3491) a mesh in no client: those motions/that effect do not play, as in GF's
         'd:/ymir work/monster2/redthief2_boss2/special_attack.gr2',
         'd:/ymir work/monster2/redthief2_boss2/special_attack1.gr2',
         'd:/ymir work/monster2/redthief2_boss2/specil_attack.gr2',
         'd:/ymir work/monster2/redthief2_boss2/specil_attack1.gr2',
         'd:/ymir work/effect/monster2/mash_ray1.mde'}


def norm(p):
    p = p.replace('\\', '/').strip().lower()
    while '//' in p:
        p = p.replace('//', '/')
    return p


fail = []
notes = []
CONTENT = {}
for p in sorted(f[:-6] for f in os.listdir(OUT) if f.endswith('.index')):
    f, v, ents = m2pack.read_index(os.path.join(OUT, p + '.index'))
    d = packlib.rd(os.path.join(OUT, p + '.data'))
    if p in MAN['new_packs'] and len(d) >= ZIP_LIMIT:
        fail.append('pack %s: data %d bytes, over the 29 MB limit' % (p, len(d)))
    for e in ents:
        CONTENT.setdefault(e['name'], m2pack.read_entry(d, e))
NAMES = set(CONTENT)
for l in open(os.path.join(WORK, 'c58.lst'), encoding='utf-8', errors='replace'):
    t = l.rstrip('\n').split(' ', 1)
    if len(t) == 2:
        NAMES.add(norm(t[1]))
for l in open(PRE_LST, encoding='utf-8', errors='replace'):
    t = l.rstrip('\n').split(' ', 3)
    if len(t) == 4:
        NAMES.add(norm(t[3]))
ix = [l.strip() for l in open(os.path.join(OUT, 'Index'), 'rb').read().decode('latin1').replace('\r', '').split('\n')]
for p in MAN['new_packs']:
    if p not in ix:
        fail.append('pack %s is not in Index' % p)
    if not os.path.exists(os.path.join(OUT, p + '.index')):
        fail.append('pack %s is not in OUT' % p)
for e in [e for p in MAN['packs'].values() for e in p]:
    if e['name'] not in CONTENT:
        fail.append('staged %s is in no pack of OUT' % e['name'])


def need(k, why):
    if k not in NAMES:
        known = k in KNOWN or ':/' in k[3:]          # a developer's path inside a GF file (horse_stop.msa)
        (notes if known else fail).append('%s  (%s)' % (k, why))
        return False
    return True


def text(k):
    return CONTENT[k].decode('latin1') if k in CONTENT else None


props = {}
for k, b in CONTENT.items():
    if k.startswith('property/'):
        l = b.replace(b'\r', b'').split(b'\n')
        if l and l[0].strip() == b'YPRT':
            props[int(l[1].strip())] = k
nobj = 0
nomdatr = set()      # GF ships no .mdatr for them either: no client collision (the server's server_attr still blocks)
for idx, MAP, size, basepos in MAPS:
    mp = 'maps/%s/' % MAP
    # 1) the map folder
    for k in ('setting.txt', 'mapproperty.txt'):
        need(mp + k, 'map %d' % idx)
    st = text(mp + 'setting.txt') or ''
    w, h = [int(x) for x in re.search(r'MapSize\s+(\d+)\s+(\d+)', st).groups()]
    assert (w, h) == size and re.search(r'BasePosition\s+%d\s+%d' % basepos, st), st
    vr = int(re.search(r'ViewRadius\s+(\d+)', st).group(1))
    if vr != 128:
        fail.append('%s setting.txt ViewRadius %d (ours: 128)' % (MAP, vr))
    SECT = ('areadata.txt', 'areaproperty.txt', 'areaambiencedata.txt', 'attr.atr', 'height.raw', 'tile.raw',
            'water.wtr', 'minimap.dds', 'shadowmap.dds', 'shadowmap.raw')
    for x in range(w):
        for y in range(h):
            for f in SECT:
                need('%s%03d%03d/%s' % (mp, x, y, f), 'sector')
    # 2) textureset
    ts = norm(re.search(r'TextureSet\s+(\S+)', st, re.I).group(1))
    need(ts, mp + 'setting.txt')
    for t in re.findall(r'"([^"]+\.dds)"', text(ts) or '', re.I):
        need(norm(t), ts)
    # 3) msenv
    env = norm(re.search(r'Environment\s+(\S+)', st, re.I).group(1))
    for k in (mp + env, 'd:/ymir work/environment/' + env):
        if need(k, mp + 'setting.txt') and k in CONTENT:
            et = text(k)
            if not (re.search(r'(?im)^\s*NearDistance', et) and re.search(r'(?im)^\s*FarDistance', et)) \
                    or re.search(r'(?im)^\s*foglevel', et):
                fail.append('%s: fog not as exe 2.0.25 reads it' % k)
            for t in re.findall(r'"([^"]+\.dds)"', et, re.I):
                need(norm(t), k)
    # 4) atlas
    sub = 'd:/ymir work/ui/atlas/%s/atlas.sub' % MAP
    if need(sub, 'atlas'):
        img = re.search(r'image\s+"([^"]+)"', text(sub) or '').group(1)
        need('d:/ymir work/ui/' + norm(img), sub)
    # 5) the objects
    for x in range(w):
        for y in range(h):
            a = text('%s%03d%03d/areadata.txt' % (mp, x, y)) or ''
            bodies = re.findall(r'Start Object\d+\r?\n(.*?)End Object', a, re.S)
            cnt = re.search(r'ObjectCount\s+(\d+)', a)
            assert cnt is None or int(cnt.group(1)) == len(bodies), (MAP, x, y)
            for body in bodies:
                nobj += 1
                crc = int(body.replace('\r', '').split('\n')[1].strip().split('#')[0])
                if crc not in props:
                    fail.append('%s: object CRC %d of sector %03d%03d: no property in pack property' % (MAP, crc, x, y))
                    continue
                pt = text(props[crc])
                kv = dict((l.split(None, 1)[0].lower(), l.split(None, 1)[1].strip().strip('"'))
                          for l in pt.replace('\r', '').split('\n') if len(l.split(None, 1)) == 2)
                for key in ('buildingfile', 'dungeonblockfile', 'effectfile', 'treefile', 'ambiencefile'):
                    if key in kv:
                        m = norm(kv[key])
                        need(m, props[crc])
                        if key in ('buildingfile', 'dungeonblockfile'):
                            i = m.rfind('.')
                            md = (m[:i] if i > m.rfind('/') else m) + '.mdatr'
                            if md not in NAMES:
                                nomdatr.add(m)

# 6) the races, and everything the staged text files name
npc, alias = {}, {}
for l in open(NPCLIST, encoding='latin1'):
    t = l.split()
    if len(t) >= 3 and t[0] == '0':
        alias[t[1].lower()] = t[2].lower()
    elif len(t) >= 2 and t[0].isdigit():
        npc[int(t[0])] = t[1].lower()
for v in sorted(int(x) for x in MAN['races']):
    if v not in npc:
        fail.append('race %d: no npclist row' % v)
        continue
    name = npc[v]
    folder = alias.get(name, name)
    cands = ['d:/ymir work/%s/%s/%s.msm' % (d, folder, name) for d in RACE_DIRS]
    if not any(c in NAMES for c in cands):
        notes.append('race %d %s: no .msm in our listing - the base client (npc/monster packs, no listing) must have it'
                     % (v, name))
RE_Q = re.compile(r'"([^"\r\n]+\.(?:gr2|dds|tga|mse|msa|msm|mss|wav|mp3|txt|msenv|mde|spt|mdatr))"', re.I)
staged = set(e['name'] for p in MAN['packs'].values() for e in p)
for k in staged:
    if not k.endswith(('.msm', '.msa', '.mse', '.mss', '.prb', '.prd', '.pre', '.prt', '.msenv')) or k.startswith('property/'):
        continue
    t = CONTENT[k].decode('latin1')
    d = k.rsplit('/', 1)[0] + '/'
    for r in RE_Q.findall(t):
        r = norm(r)
        if not (r.startswith('d:/') or r.startswith(('sound/', 'textureset/', 'property/'))):
            r = 'd:/' + r if r.startswith('ymir work/') else d + r
        need(r, k)

# 7) the map names (MT2009_PLUS_OCHAO_GAUTAMA_V1), when the locale pack is in OUT
if '--locale' in sys.argv:
    want = {'MAP_DAWN': 'Zbocze Gautama', 'MAP_DAWNMISTWOOD': 'Zbocze Gautama', 'MAP_BAY': 'Nefrytowa Zatoka',
            'MAP_BAYBLACKSAND': 'Nefrytowa Zatoka', 'MAP_THUNDER': 'Gromiste G\xf3ry', 'MAP_MT_THUNDER': 'Gromiste G\xf3ry'}
    for f in ('locale/pl/locale_game.txt', 'locale/pl/locale_game_marty.txt'):
        if f not in CONTENT:
            fail.append('%s not in OUT' % f)
            continue
        rows = dict(l.split('\t', 1) for l in CONTENT[f].decode('cp1250').replace('\r', '').split('\n') if '\t' in l)
        for k, v in want.items():
            if rows.get(k, '').strip() != v:
                fail.append('%s %s = %r (want %r)' % (f, k, rows.get(k), v))

print('objects checked: %d, properties in pack: %d, names known: %d' % (nobj, len(props), len(NAMES)))
print('Building/DungeonBlock models without .mdatr (none in GF either): %d' % len(nomdatr))
print('notes (%d):' % len(set(notes)))
for n in sorted(set(notes)):
    print('  ' + n)
print('FAIL (%d):' % len(set(fail)))
for f in sorted(set(fail)):
    print('  ' + f)
sys.exit(1 if fail else 0)
