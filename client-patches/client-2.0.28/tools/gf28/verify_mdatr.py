# MT2009 client 2.0.28: every map object's collision / walkable-height data (.mdatr) must be in the packs.
# Exe 2.0.25 (no source; disassembly around the "BuildingFile"/"DungeonBlockFile"/".mdatr" strings): the property
# loader stores  NoExtension(BuildingFile or DungeonBlockFile) + ".mdatr"  as the object's attribute file; the
# CAttributeData it names holds the collision shapes (buildings you cannot walk through) and the height meshes
# (bridges / floors you walk ON). The property file itself never names the .mdatr, so a missing one is silent:
# the model is drawn but has no collision and no height.
# Run in docker (m2pack-lzo) after build. Checks 351/352/Ochao/Treasure Island (our maps pack) + entrances
# 61/62 (GF areadata), and every .gr2 in the GF-import packs that has an .mdatr next to it in GF.
import sys, os, struct, collections
sys.path.insert(0, '/opt/metin2/cache/tcm/tz'); sys.path.insert(0, '/opt/metin2/cache/tcm/gf28')
import m2pack, gfres
C = sys.argv[1] if len(sys.argv) > 1 else '/opt/metin2/cache/tcm/c28/pack'
PACK = {}
for p in sorted(f[:-6] for f in os.listdir(C) if f.endswith('.index')):
    if p == 'root': continue
    f, v, ents = m2pack.read_index(C + '/%s.index' % p); d = open(C + '/%s.data' % p, 'rb').read()
    for e in ents: PACK.setdefault(e['name'], (p, d, e))
BASE = gfres.load_ours('/opt/metin2/cache/tcm/gf28/ourpacks_pre.txt')
def raw(k): p, d, e = PACK[k]; return m2pack.read_entry(d, e)
def has(k): return k in PACK or k in BASE
def txt(k):
    if k in PACK: return raw(k).decode('latin1')
    return open(gfres.GF[k], 'rb').read().decode('latin1') if k in gfres.GF else ''

DIMS = {0: 2, 1: 3, 2: 1, 3: 2, 4: 3, 5: 3}   # plane, box, sphere, cylinder, aabb, obb
def mdatr_info(b):
    """(collisions, heights) of an AttributeData blob ("AttributeData\\0", DWORD collisions, DWORD heights, ...)"""
    assert b[:14] == b'AttributeData\0', 'bad header'
    nc, nh = struct.unpack_from('<II', b, 14); o = 22
    for i in range(nc):                           # DWORD type, char name[32], pos[3], dims[by type], quat[4]
        t = struct.unpack_from('<I', b, o)[0]; o += 4 + 32 + 12 + 4 * DIMS[t] + 16
    for i in range(nh):
        n = struct.unpack_from('<I', b, o + 32)[0]; o += 36 + 12 * n   # char name[32], DWORD n, vec3[n]
    assert o == len(b), 'size %d != %d' % (o, len(b))
    return nc, nh

PROP = {}
for k in PACK:
    if k.startswith('property/'):
        l = raw(k).replace(b'\r', b'').split(b'\n')
        if l and l[0].strip() == b'YPRT' and len(l) > 1: PROP.setdefault(int(l[1].strip()), k)
def crcs_ours(m):
    s = set()
    for k in PACK:
        if k.startswith('maps/%s/' % m) and k.endswith('/areadata.txt'):
            t = txt(k).replace('\r', '').split('\n')
            s |= {int(t[i + 2].split('#')[0]) for i, l in enumerate(t) if l.startswith('Start Object')}
    return s
def crcs_gf(m):
    s = set()
    for dp, dn, fn in os.walk(os.path.join(gfres.G, m)):
        for f in fn:
            if f.lower() == 'areadata.txt':
                t = open(os.path.join(dp, f), 'rb').read().decode('latin1').replace('\r', '').split('\n')
                s |= {int(t[i + 2].split('#')[0]) for i, l in enumerate(t) if l.startswith('Start Object')}
    return s
bad = 0; checked = set()
def check(k, src):
    """-> problem string or None"""
    global bad
    checked.add(k)
    if k not in gfres.GF: return None            # GF has none either: the official object has no collision/height
    if not has(k): bad += 1; return 'MISSING'
    if k in PACK:
        b = raw(k)
        if b != open(gfres.GF[k], 'rb').read(): bad += 1; return 'DIFFERS from GF'
        try: nc, nh = mdatr_info(b)
        except Exception as e: bad += 1; return 'MALFORMED %s' % e
        return 'ok %s (%d collision, %d height)' % (PACK[k][0], nc, nh)
    return 'ok (base listing)'

MAPS = [('351 metin2_map_n_flame_dungeon_01', crcs_ours('metin2_map_n_flame_dungeon_01')),
        ('352 metin2_map_n_snow_dungeon_01', crcs_ours('metin2_map_n_snow_dungeon_01')),
        ('Ochao metin2_map_mt_th_dungeon_01', crcs_ours('metin2_map_mt_th_dungeon_01')),
        ('419 metin2_map_treasure_hunt', crcs_ours('metin2_map_treasure_hunt')),
        ('62 metin2_map_n_flame_01 (GF areadata)', crcs_gf('metin2_map_n_flame_01')),
        ('61 map_n_snowm_01 (GF areadata)', crcs_gf('map_n_snowm_01'))]
for name, crcs in MAPS:
    rows = []; noprop = []; ngf = 0
    for c in sorted(crcs):
        if c not in PROP: noprop.append(c); continue
        model = gfres.prop_attr_model(txt(PROP[c]))
        if not model: continue
        k = gfres.mdatr_of(model)
        r = check(k, model)
        if r is None: continue
        ngf += 1; rows.append('   %-70s %s' % (k, r))
    nbad = sum('ok' not in r for r in rows)
    print('== %s: %d objects (%d without our property), %d with an official .mdatr, problems: %d' % (name, len(crcs), len(noprop), ngf, nbad))
    for r in rows: print(r)
# every .gr2 of the GF-import packs that has an official .mdatr next to it (dungeon blocks, NPC gates...)
rows = []
for k, (p, d, e) in sorted(PACK.items()):
    if k.endswith('.gr2') and (p.startswith('gf_') or p in ('goblin', 'ochao', 'maps')):
        a = gfres.mdatr_of(k)
        if a in gfres.GF and a not in checked:
            r = check(a, k); rows.append('   %-70s %s' % (a, r))
print('== other .gr2 in gf_*/goblin/ochao with an official .mdatr: %d, problems: %d' % (len(rows), sum('ok' not in r for r in rows)))
for r in rows: print(r)
print('RESULT: %d .mdatr problems' % bad)
sys.exit(1 if bad else 0)
