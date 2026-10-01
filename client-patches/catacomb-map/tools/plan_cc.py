# MT2009 client 2.0.36 - the Devil's Catacomb (server map 216 metin2_map_devilcatacomb; the client finds it by
# position in atlasinfo as metin2_map_devilsCatacomb -> maps/metin2_map_devilscatacomb, already in pack maps).
# Plan: every file the map and its monsters need that the client (BASE packs + pre-import base listing) lacks,
# as the full reference closure from GF 26.1.11 + generated files -> final_cc.json {add: {pack: {key: src}}}.
# Run: docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 plan_cc.py [BASE]
import os, sys, re, json, struct, subprocess, tempfile, collections, shutil
H = '/opt/metin2/cache/c36-catacomb'
sys.path.insert(0, '/opt/metin2/cache/tcm/tz'); sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
import m2pack, gfres, dxt
BASE = sys.argv[1] if len(sys.argv) > 1 else '/opt/metin2/cache/c35/pack'
G = gfres.G
MAP = 'metin2_map_devilscatacomb'
ENVKEY = 'd:/ymir work/environment/map_devilscatacomb.msenv'
# the dungeon's races (client npclist names, GF folders): floors 1-7 mobs, bosses, statues, gates, Guardian, peddler
RACES = ['monster2/zombie_diseased_kid', 'monster2/zombie_diseased_dog', 'monster2/zombie_diseased_infector',
         'monster2/zombie_diseased_sword', 'monster2/zombie_diseased_spear', 'monster2/zombie_diseased_bow',
         'monster2/zombie_diseased_boss', 'monster2/zombie_soldier_scythe', 'monster2/zombie_soldier_bow',
         'monster2/zombie_soldier_spear', 'monster2/zombie_magician', 'monster2/zombie_bigboss', 'monster2/zombie_ghost',
         'monster2/zombie_general', 'monster2/zombie_king', 'monster2/zombie_god', 'monster2/zombie_bigboss2',
         'npc2/zombie_key_stone', 'npc2/zombie_god_stone', 'npc2/zombie_security_stone', 'npc2/zombie_warp_stone',
         'npc2/zombie_ghost_door', 'npc/jinno_patrol_spear', 'npc/peddler']
NEWPACK = 'catacomb_map'
GEN = H + '/gen'
GR2_64 = b'\xe5\x9b\x49\x5e'
norm = gfres.norm

# ---- base packs (lazy content) ----
PACK = {}
for p in sorted(f[:-6] for f in os.listdir(BASE) if f.endswith('.index')):
    for e in m2pack.read_index(BASE + '/%s.index' % p)[2]: PACK.setdefault(e['name'], (p, e))
def pack_content(k):
    p, e = PACK[k]
    with open(BASE + '/%s.data' % p, 'rb') as f:
        f.seek(e['pos']); blob = f.read(e['size'])
    e2 = dict(e); e2['pos'] = 0
    return m2pack.read_entry(blob, e2)
PRE = gfres.load_ours('/opt/metin2/cache/tcm/gf28/ourpacks_pre.txt')

# ---- generated files ----
shutil.rmtree(GEN, ignore_errors=True)
GENF = {}
def gen(key, data):
    p = os.path.join(GEN, key.replace('d:/', 'd_/', 1)); os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'wb').write(data); GENF[key] = p; return p
def crlf(s): return s.replace('\r\n', '\n').replace('\n', '\r\n')
# 1. environment (setting.txt: Environment map_devilsCatacomb.msenv -> d:/ymir work/environment/): GF's has
#    "foglevel 5"; exe 2.0.25 needs Enable/NearDistance/FarDistance - the same conversion as Razador's flame
#    dungeon (gf_razador: foglevel 5 -> 1000 / 30000), GF's fog colour kept.
genv = open(G + '/d_/ymir work/environment/map_devilscatacomb.msenv', 'rb').read().decode('latin1').replace('\r', '')
m = re.search(r'Group Fog\s*\{[^}]*\}', genv); assert m and 'foglevel' in m.group(0)
col = re.search(r'Color\s+([^\n]+)', m.group(0)).group(1).strip()
fog = 'Group Fog\n{\n    Enable        1\n    NearDistance  1000.000000\n    FarDistance   30000.000000\n    Color         %s\n}' % col
gen(ENVKEY, crlf(genv[:m.start()] + fog + genv[m.end():]).encode('latin1'))
# 2. big-map atlas from the GF minimap tiles (the minimap info is hidden in the Catacomb by uiminimap's
#    CANNOT_SEE_INFO_MAP_DICT, the atlas is there for completeness, as for 208)
st = open(G + '/%s/setting.txt' % MAP, 'rb').read().decode('latin1')
mw, mh = map(int, re.search(r'MapSize\s+(\d+)\s+(\d+)', st).groups())
W, Hh, big = dxt.stitch(G + '/' + MAP, mw, mh)
side = 512 if max(mw, mh) >= 4 else 256
p = gen('d:/ymir work/ui/%s_atlas.dds' % MAP, b'')
dxt.write_dxt1(p, side, side, dxt.downscale(W, Hh, big, side, side))
gen('d:/ymir work/ui/atlas/%s/atlas.sub' % MAP, crlf('title subImage\nversion 1.0\nimage "%s_atlas.dds"\nleft 0\ntop 0\nright %d\nbottom %d\n' % (MAP, side, side)).encode())

# ---- sources: GF map folder, the race folders (+ their sounds), the generated files ----
SRC = {}
for dp, dn, fn in os.walk(G + '/' + MAP):
    for f in fn:
        k = norm('maps/%s/%s' % (MAP, os.path.relpath(os.path.join(dp, f), G + '/' + MAP)))
        if k.endswith('.msenv'): continue
        SRC[k] = os.path.join(dp, f)
seeds = list(SRC) + list(GENF)
for r in RACES:
    hit = [k for k in gfres.GF if k.startswith('d:/ymir work/%s/' % r)]; assert hit, r; seeds += hit
    seeds += [k for k in gfres.GF if k.startswith('sound/%s/' % r)]
SRC.update(GENF)
# fallback: the Arezzo client's unpacked files (the source of maps 360-366) for what GF ships only encrypted
AZ = '/opt/metin2/cache/arezzo/cpack/files/ymir work/'
AZHIT = set()
def src_of(k):
    s = SRC.get(k) or gfres.GF.get(k)
    if not s and k.startswith('d:/ymir work/'):
        p = AZ + k[len('d:/ymir work/'):]
        if os.path.isfile(p): AZHIT.add(k); s = p
        else:
            d, f = os.path.split(p)
            if os.path.isdir(d):
                for x in os.listdir(d):
                    if x.lower() == f: AZHIT.add(k); s = os.path.join(d, x); break
    return s

# ---- property objects of the map ----
def prop_index(files):
    idx = {}
    for k, get in files:
        l = get().replace(b'\r', b'').split(b'\n')
        if l and l[0].strip() == b'YPRT' and len(l) > 1:
            try: idx.setdefault(int(l[1].strip()), k)
            except ValueError: pass
    return idx
OURPROP = prop_index([(k, (lambda k=k: pack_content(k))) for k in PACK if PACK[k][0] == 'property'])
GFPROP = prop_index([(k, (lambda v=v: open(v, 'rb').read())) for k, v in gfres.GF.items() if k.startswith('property/')])
crcs = collections.Counter()
for k, v in SRC.items():
    if k.endswith('/areadata.txt'):
        t = open(v, 'rb').read().decode('latin1').replace('\r', '').split('\n')
        crcs.update(int(t[i + 2].strip().split('#')[0]) for i, l in enumerate(t) if l.startswith('Start Object'))
functional = lambda b: sorted(l.strip() for l in b.replace(b'\r', b'').split(b'\n')[2:] if l.strip() and not l.lower().startswith(b'propertyname'))
props = {}; propdiff = {}; propmissing = {}
for c in sorted(crcs):
    if c in OURPROP:
        k = OURPROP[c]
        if c in GFPROP and functional(pack_content(k)) != functional(open(gfres.GF[GFPROP[c]], 'rb').read()):
            propdiff[c] = (k, GFPROP[c])   # ours is kept (the property pack is read as it is)
        props[c] = ('ours', k)
    elif c not in GFPROP:
        propmissing[c] = crcs[c]; continue
    else:
        k = GFPROP[c]; assert k not in PACK, k
        props[c] = ('new', k)
    seeds.append(props[c][1])

# ---- closure ----
TAGS = (2000, 20002, 17749)
def spt_refs(k, b):
    d = k.rsplit('/', 1)[0] + '/'; out = set()
    for tag in TAGS:
        for m in re.finditer(re.escape(struct.pack('<I', tag)), b):
            i = m.end(); n = struct.unpack('<i', b[i:i + 4])[0] if i + 4 <= len(b) else 0
            if 1 <= n <= 300:
                s = b[i + 4:i + 4 + n]
                if re.search(rb'[A-Za-z]', s) and all(c >= 32 for c in s):
                    base = re.split(r'[\\/]', s.decode('latin1'))[-1]
                    out.add((d + (base.rsplit('.', 1)[0] if '.' in base else base) + '.dds').lower())
    return out
RE_ABS = re.compile(rb'[A-Za-z]:[\\/][\x20-\x7e]{3,220}?\.(?:dds|tga|jpg|png|bmp|mde|mse|gr2|msa|msf|mss|wav|mp3|spt)(?![A-Za-z0-9])', re.I)
RE_YW = re.compile(rb'ymir work[\\/][\x20-\x7e]{3,220}?\.(?:dds|tga|jpg|png|bmp|mde|mse|gr2|msa|msf|mss|wav|mp3|spt)(?![A-Za-z0-9])', re.I)
def bin_refs(b):
    out = set()
    for s in RE_ABS.findall(b) + RE_YW.findall(b):
        s = norm(s.decode('latin1'))
        if 'ymir work/' in s: out.add('d:/ymir work/' + s.split('ymir work/', 1)[1])
    return out
gr2fail = {}; bad64 = set()
def refs(k, b, src):
    out = set()
    if k.endswith('.spt'): return spt_refs(k, b)
    if k.endswith('.gr2'):
        if b[:4] == GR2_64: bad64.add(k)
        fn = tempfile.mktemp(suffix='.gr2'); open(fn, 'wb').write(b)
        r = subprocess.run([gfres.GR2DEC, fn], capture_output=True)
        if r.returncode == 0:
            out |= gfres.gr2_textures(k, fn)
        else:
            gr2fail[k] = r.stderr.decode('latin1').strip()[:120]
            dd = os.path.dirname(src) if src else None       # BitKnit: every texture beside the model
            if dd and os.path.isdir(dd):
                for f in os.listdir(dd):
                    if f.lower().endswith(('.dds', '.tga')): out.add(norm(k.rsplit('/', 1)[0] + '/' + f))
        os.unlink(fn); return out
    if k.endswith(gfres.TEXT_EXT) or k.endswith('.mde'):
        fn = tempfile.mktemp(); open(fn, 'wb').write(b)
        out |= gfres.refs_of(k, fn); os.unlink(fn)
        out |= bin_refs(b)
    if k.startswith('property/'):
        out = set(r for r in out if not r.startswith('property/'))   # propertyname "x.mse"/"x.gr2" is a label
        m = gfres.prop_attr_model(b.decode('latin1'))
        if m: out.add(gfres.mdatr_of(m))
    s = gfres.sound_of(k)
    if s and (s in gfres.GF or s in SRC or s in PACK): out.add(s)
    return out
DROP = {'maps/%s/map_devilscatacomb.msenv' % MAP}
seen = set(DROP); todo = list(seeds); add = {}; unresolved = {}; parent = {}; ours_hit = set(); pre_hit = set()
while todo:
    k = todo.pop()
    if k in seen or k.endswith('.psd'): continue
    seen.add(k)
    if k in PACK:
        ours_hit.add(k); src = None; b = pack_content(k)
    elif k in PRE:
        pre_hit.add(k); continue
    else:
        src = src_of(k)
        if not src:
            unresolved[k] = parent.get(k, 'seed'); continue
        add[k] = src; b = open(src, 'rb').read()
    for r in refs(k, b, src):
        if r not in seen: parent.setdefault(r, k); todo.append(r)
# .mdatr is optional for objects whose model has none (the exe then uses no extra collision)
opt = {k: v for k, v in unresolved.items() if k.endswith('.mdatr')}
def dest(k):
    if k.startswith('property/'): return 'property'
    return NEWPACK
final = collections.defaultdict(dict)
for k, s in add.items(): final[dest(k)][k] = s
rep = dict(propdiff={str(c): v for c, v in propdiff.items()}, propmissing={str(c): n for c, n in propmissing.items()}, crcs={str(c): [n, props[c][0], props[c][1]] for c, n in crcs.items()},
           packs={p: dict(files=len(v), mb=round(sum(os.path.getsize(s) for s in v.values()) / 1e6, 2)) for p, v in final.items()},
           generated=sorted(GENF), arezzo=sorted(AZHIT), ours_followed=len(ours_hit), pre_trusted=sorted(pre_hit),
           unresolved=unresolved, bad64=sorted(bad64), gr2fail=gr2fail)
json.dump(dict(add=final, report=rep, parent={k: parent.get(k) for k in add}), open(H + '/final_cc.json', 'w'), indent=1, sort_keys=True)
for p, v in sorted(rep['packs'].items()): print('%-9s %4d files %6.2f MB' % (p, v['files'], v['mb']))
print('crcs', rep['crcs']); print('generated', len(GENF), 'ours followed', len(ours_hit), 'pre trusted', sorted(pre_hit))
print('arezzo', sorted(AZHIT)); print('propdiff', propdiff, 'propmissing', propmissing); print('UNRESOLVED', json.dumps(unresolved, indent=1)); print('64-bit gr2', sorted(bad64)); print('gr2 fail', gr2fail)
