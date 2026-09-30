# MT2009 client 2.0.30 - Arezzo phases 5-8 packs. Base = the CURRENT /opt/metin2/cache/tcm/c30/pack (read only; phase 1
# and the dungeon panel are in it), output = /opt/metin2/cache/arezzo-work/client/out58/pack (changed packs + Index).
# Run: python3 plan58.py && python3 gen58.py   (host)
#      docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 /opt/metin2/cache/arezzo-work/client/az58/build58.py [BASE] [OUT]
import os, sys, json, zlib, shutil, struct
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz'); sys.path.insert(0, HERE)
import m2pack, packlib, patch_gamedata58 as pg
BASE = sys.argv[1] if len(sys.argv) > 1 else '/opt/metin2/cache/tcm/c30/pack'
OUT = sys.argv[2] if len(sys.argv) > 2 else '/opt/metin2/cache/arezzo-work/client/out58/pack'
NEW_PACKS = ['az_maps2', 'az_maps3', 'az_mobs2', 'az_mobs3', 'az_mobs4']
TEXT = ('.txt', '.msa', '.msm', '.mse', '.mss', '.msenv', '.sub', '.prb', '.prd', '.pre', '.prt', '.py', '.ifl', '.pra')
def ctype(name): return 2 if name.endswith(TEXT) else 1
rd = packlib.rd
fin = json.load(open(HERE + '/final58.json'))['add']
shutil.rmtree(OUT, ignore_errors=True); os.makedirs(OUT)

# every name in every base pack: an added name must be new to the whole client we know
allnames = {}
for p in sorted(f[:-6] for f in os.listdir(BASE) if f.endswith('.index')):
    for e in m2pack.read_index(BASE + '/%s.index' % p)[2]: allnames.setdefault(e['name'], p)
def entry(pack, name):
    f, v, ents = m2pack.read_index(BASE + '/%s.index' % pack); d = rd(BASE + '/%s.data' % pack)
    return [m2pack.read_entry(d, e) for e in ents if e['name'] == name][0]

report = {}; expect = {}
def build(pack, add_items, rep_items):
    idx, dat = BASE + '/%s.index' % pack, BASE + '/%s.data' % pack
    exists = os.path.exists(idx)
    have = {}
    if exists:
        f, v, ents = m2pack.read_index(idx); data = rd(dat); have = dict((e['name'], e) for e in ents); tmpl = ents[-1]['raw']
    else:
        f, v, ents = m2pack.read_index(BASE + '/az_mobs.index'); tmpl = ents[-1]['raw']; data = b''
    rep, add = {}, {}
    for k, b in rep_items.items():
        assert k in have, (pack, 'replace of a missing entry', k)
        if m2pack.read_entry(data, have[k]) != b: rep[k] = b
    for k, b in add_items.items():
        if k in have:
            if m2pack.read_entry(data, have[k]) != b: rep[k] = b      # a re-run on a pack that already has it
        else:
            assert k not in allnames, (pack, k, 'already in pack', allnames.get(k))
            add[k] = (b, ctype(k))
    if not rep and not add:
        report[pack] = 'unchanged'; return
    r = packlib.repack_add_typed(idx if exists else None, dat if exists else None, rep, add,
                                 OUT + '/%s.index' % pack, OUT + '/%s.data' % pack, tmpl)
    report[pack] = dict(old=r[0], added=r[1], replaced=r[2])
    expect[pack] = dict(list(rep.items()) + [(k, b) for k, (b, c) in add.items()])

for pack in sorted(fin):
    build(pack, dict((k, rd(p)) for k, p in fin[pack].items()), {})

# gamedata: atlasinfo, npclist, item_list, mob_proto, item_proto
MOB_KEY = (4813894, 18955, 552631, 6822045); ITEM_KEY = (173217, 72619434, 408587239, 27973291)
def mob_proto(b):
    assert b[:4] == b'MMPT'; cnt = struct.unpack_from('<I', b, 4)[0]; raw = m2pack.mcoz_decode(b[12:], MOB_KEY)
    recs = pg.mob_rows([raw[i * 256:(i + 1) * 256] for i in range(cnt)])
    new = b'MMPT' + struct.pack('<II', len(recs), 0) + b''
    blob = m2pack.mcoz_encode(b''.join(recs), MOB_KEY)
    out = b'MMPT' + struct.pack('<II', len(recs), len(blob)) + blob
    # unchanged rows -> keep the original bytes (idempotent re-run)
    return b if m2pack.mcoz_decode(b[12:], MOB_KEY) == b''.join(recs) else out
def item_proto(b):
    assert b[:4] == b'MIPX'; ver, stride, cnt, size = struct.unpack_from('<IIII', b, 4); raw = m2pack.mcoz_decode(b[20:], ITEM_KEY)
    recs = pg.item_rows([raw[i * 184:(i + 1) * 184] for i in range(cnt)])
    if raw == b''.join(recs): return b
    blob = m2pack.mcoz_encode(b''.join(recs), ITEM_KEY)
    return b'MIPX' + struct.pack('<IIII', ver, stride, len(recs), len(blob)) + blob
gd = {}
for name, fn in (('gamedata/atlasinfo.txt', pg.atlasinfo), ('gamedata/npclist.txt', pg.npclist), ('gamedata/item_list.txt', pg.item_list),
                 ('gamedata/mob_proto', mob_proto), ('gamedata/item_proto', item_proto)):
    gd[name] = fn(entry('gamedata', name))
build('gamedata', {}, gd)
build('locale', {}, {'locale/pl/itemdesc.txt': pg.itemdesc(entry('locale', 'locale/pl/itemdesc.txt'))})
build('root', {}, {'localeinfo.py': pg.localeinfo(entry('root', 'localeinfo.py'))})

# Index: the new packs at the end
ix = rd(BASE + '/Index')
for p in NEW_PACKS:
    if (b'\n' + p.encode() + b'\n') not in ix and os.path.exists(OUT + '/%s.index' % p):
        ix = ix.rstrip(b'\n') + b'\n*\n' + p.encode() + b'\n'
if ix != rd(BASE + '/Index'):
    open(OUT + '/Index', 'wb').write(ix); report['Index'] = 'updated'

# verification: every entry of every output pack read back; old entries unchanged
for pack, exp in expect.items():
    f, v, nw = m2pack.read_index(OUT + '/%s.index' % pack); nd = rd(OUT + '/%s.data' % pack)
    names = [e['name'] for e in nw]; assert len(set(names)) == len(names), pack
    got = {}
    for e in nw:
        assert zlib.crc32(nd[e['pos']:e['pos'] + e['size']]) & 0xffffffff == e['dcrc'], (pack, e['name'])
        assert e['fcrc'] == zlib.crc32(e['name'].encode('cp1252')) & 0xffffffff, (pack, e['name'])
        got[e['name']] = m2pack.read_entry(nd, e)
    bad = [k for k, b in exp.items() if got.get(k) != b]; assert not bad, (pack, bad[:5])
    if os.path.exists(BASE + '/%s.index' % pack):
        f, v, old = m2pack.read_index(BASE + '/%s.index' % pack); od = rd(BASE + '/%s.data' % pack)
        ch = [e['name'] for e in old if e['name'] not in exp and m2pack.read_entry(od, e) != got[e['name']]]
        assert not ch, (pack, ch[:5])
        assert set(e['name'] for e in old) <= set(got), pack
    report[pack]['verified_entries'] = len(nw)
    report[pack]['data_mb'] = round(os.path.getsize(OUT + '/%s.data' % pack) / 1e6, 2)
# the protos read back
GD = OUT if os.path.exists(OUT + '/gamedata.index') else BASE
f, v, ents = m2pack.read_index(GD + '/gamedata.index'); d = rd(GD + '/gamedata.data')
g = dict((e['name'], m2pack.read_entry(d, e)) for e in ents)
b = g['gamedata/mob_proto']; raw = m2pack.mcoz_decode(b[12:], MOB_KEY)
mobs = dict((struct.unpack_from('<I', raw, i)[0], raw[i:i + 256]) for i in range(0, len(raw), 256))
for m in pg.ALLOC['mobs']:
    r = mobs[m['vnum']]; assert r[29:54].split(b'\0')[0].decode('cp1250') == m['name'], m['vnum']
    if 'level' in m: assert r[57] == m['level'], m['vnum']
b = g['gamedata/item_proto']; raw = m2pack.mcoz_decode(b[20:], ITEM_KEY)
items = dict((struct.unpack_from('<I', raw, i)[0], raw[i:i + 184]) for i in range(0, len(raw), 184))
for it in pg.ALLOC['items']: assert items[it['vnum']][41:74].split(b'\0')[0].decode('cp1250') == it['name']
report['protos'] = dict(mob_rows=len(mobs), item_rows=len(items))
json.dump(report, open(HERE + '/build_report.json', 'w'), indent=1)
print(json.dumps(report, indent=1))
