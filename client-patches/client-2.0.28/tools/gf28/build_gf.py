# MT2009 client 2.0.28: official Gameforge assets (Gameforge_26.1.11 client) into our packs.
# Idempotent: base = the current /opt/metin2/cache/tcm/c28/pack, output = gf28/out/pack.
# Run (host): python3 plan.py && python3 gen.py   (GF closure -> final.json)
#       then: docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 /opt/metin2/cache/tcm/gf28/build_gf.py
import os, sys, json, zlib, shutil
sys.path.insert(0, '/opt/metin2/cache/tcm/tz'); sys.path.insert(0, '/opt/metin2/cache/tcm/gf28')
import m2pack, packlib
HERE = '/opt/metin2/cache/tcm/gf28'
C28 = '/opt/metin2/cache/tcm/c28/pack'
OUT = HERE + '/out/pack'
GF = '/opt/metin2/cache/gf/Gameforge_26.1.11/_client'
NEW_PACKS = ['gf_razador', 'gf_nemere', 'gf_misc']
TEXT = ('.txt', '.msa', '.msm', '.mse', '.mss', '.msenv', '.sub', '.prb', '.prd', '.pre', '.prt', '.py', '.ifl', '.pra')
def ctype(name): return 2 if name.endswith(TEXT) else 1
rd = packlib.rd

fin = json.load(open(HERE + '/final.json'))
ADD, REP = fin['add'], fin['replace']
shutil.rmtree(HERE + '/out', ignore_errors=True); os.makedirs(OUT)

# npclist: the real models are in now -> the official names instead of patch_npclist.py's stand-ins
VNUMS = [6001, 6002, 6003, 6004, 6005, 6006, 6007, 6008, 6009, 6051, 6091, 6101, 6102, 6103, 6104, 6105, 6106,
         6107, 6108, 6109, 6151, 6191, 8057, 8058, 20385, 20386, 20387, 20388, 20397, 20398, 20399]
gfnpc = {}
for l in open(GF + '/shared/common/npclist.txt', 'rb').read().replace(b'\r', b'').split(b'\n'):
    t = l.split(b'\t')
    if len(t) >= 2 and t[0].isdigit() and int(t[0]) in VNUMS and int(t[0]) not in gfnpc:
        gfnpc[int(t[0])] = t[1].strip()
assert sorted(gfnpc) == sorted(VNUMS), set(VNUMS) - set(gfnpc)
def restore_npclist(b):
    lines = b.split(b'\r\n'); seen = set(); out = []
    for l in lines:
        t = l.split(b'\t')
        if len(t) >= 2 and t[0].isdigit() and int(t[0]) in gfnpc:
            v = int(t[0])
            if v in seen: continue
            seen.add(v); l = b'%d\t%s\t' % (v, gfnpc[v])
        out.append(l)
    tail = out.pop() if out and out[-1] == b'' else None
    for v in sorted(set(gfnpc) - seen): out.append(b'%d\t%s\t' % (v, gfnpc[v]))
    if tail is not None: out.append(tail)
    return b'\r\n'.join(out)

report = {}
def build(pack, add_src, rep_src, extra_rep=None, extra_add=None):
    idx, dat = C28 + '/%s.index' % pack, C28 + '/%s.data' % pack
    exists = os.path.exists(idx)
    have = {}
    if exists:
        f, v, ents = m2pack.read_index(idx); data = rd(dat)
        have = dict((e['name'], e) for e in ents)
        tmpl = ents[-1]['raw']
    else:
        f, v, ents = m2pack.read_index(C28 + '/goblin.index'); tmpl = ents[-1]['raw']; data = b''
    rep, add = {}, {}
    items = [(k, rd(p)) for k, p in add_src.items()] + [(k, rd(p)) for k, p in rep_src.items()]
    items += list((extra_add or {}).items()) + list((extra_rep or {}).items())
    for k, b in items:
        if k in have:
            if m2pack.read_entry(data, have[k]) != b: rep[k] = b
        else:
            add[k] = (b, ctype(k))
    if not rep and not add:
        report[pack] = 'unchanged'; return None
    r = packlib.repack_add_typed(idx if exists else None, dat if exists else None, rep, add,
                                 OUT + '/%s.index' % pack, OUT + '/%s.data' % pack, tmpl)
    report[pack] = dict(old=r[0], added=r[1], replaced=r[2])
    return dict(list(rep.items()) + [(k, b) for k, (b, c) in add.items()])

expect = {}
for pack in sorted(set(ADD) | set(REP)):
    e = build(pack, ADD.get(pack, {}), REP.get(pack, {}))
    if e is not None: expect[pack] = e
# icon: 50260 (Cor Draconis, rough) - item_list names 50255.tga, a code path asks for 50260.tga
f, v, ents = m2pack.read_index(C28 + '/icon.index'); d = rd(C28 + '/icon.data')
ico = [m2pack.read_entry(d, e) for e in ents if e['name'] == 'icon/item/50255.tga'][0]
e = build('icon', {}, {}, extra_add={'icon/item/50260.tga': ico})
if e is not None: expect['icon'] = e
# gamedata: npclist
f, v, ents = m2pack.read_index(C28 + '/gamedata.index'); d = rd(C28 + '/gamedata.data')
npl = [m2pack.read_entry(d, e) for e in ents if e['name'] == 'gamedata/npclist.txt'][0]
new = restore_npclist(npl); assert restore_npclist(new) == new
open(HERE + '/npclist.new.txt', 'wb').write(new)
e = build('gamedata', {}, {}, extra_rep={'gamedata/npclist.txt': new})
if e is not None: expect['gamedata'] = e
# Index
ix = rd(C28 + '/Index')
for p in NEW_PACKS:
    if (b'\n' + p.encode() + b'\n') not in ix:
        ix = ix.rstrip(b'\n') + b'\n*\n' + p.encode() + b'\n'
if ix != rd(C28 + '/Index'):
    open(OUT + '/Index', 'wb').write(ix); report['Index'] = 'updated'

# verification: every entry of every output pack read back
for pack, exp in expect.items():
    f, v, nw = m2pack.read_index(OUT + '/%s.index' % pack); nd = rd(OUT + '/%s.data' % pack)
    names = [e['name'] for e in nw]; assert len(set(names)) == len(names), pack
    got = {}
    for e in nw:
        assert zlib.crc32(nd[e['pos']:e['pos'] + e['size']]) & 0xffffffff == e['dcrc'], (pack, e['name'])
        assert e['fcrc'] == zlib.crc32(e['name'].encode('cp1252')) & 0xffffffff, (pack, e['name'])
        got[e['name']] = m2pack.read_entry(nd, e)
    bad = [k for k, b in exp.items() if got.get(k) != b]
    assert not bad, (pack, bad[:5])
    changed_old = []
    if os.path.exists(C28 + '/%s.index' % pack):
        f, v, old = m2pack.read_index(C28 + '/%s.index' % pack); od = rd(C28 + '/%s.data' % pack)
        for e in old:
            if e['name'] not in exp and m2pack.read_entry(od, e) != got[e['name']]: changed_old.append(e['name'])
        assert not changed_old, (pack, changed_old[:5])
    report[pack]['verified_entries'] = len(nw)
    report[pack]['data_mb'] = round(os.path.getsize(OUT + '/%s.data' % pack) / 1e6, 2)
json.dump(report, open(HERE + '/build_report.json', 'w'), indent=1)
print(json.dumps(report, indent=1))
