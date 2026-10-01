# MT2009 client 2.0.36 - the Devil's Catacomb: NEW pack catacomb_map (+ Index line at the end) from final_cc.json.
# Every entry is read back (dcrc, fcrc, content); no existing pack is touched (a new name already in a pack aborts).
# Run: docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 /opt/metin2/cache/c36-catacomb/tools/build_cc.py [BASE] [OUT]
import os, sys, json, zlib, shutil
H = '/opt/metin2/cache/c36-catacomb'
sys.path.insert(0, '/opt/metin2/cache/tcm/tz'); sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
import m2pack, packlib
BASE = sys.argv[1] if len(sys.argv) > 1 else '/opt/metin2/cache/c35/pack'
OUT = sys.argv[2] if len(sys.argv) > 2 else H + '/pack'
NEW = 'catacomb_map'
TEXT = ('.txt', '.msa', '.msm', '.mse', '.mss', '.msenv', '.sub', '.prb', '.prd', '.pre', '.prt', '.py', '.ifl', '.pra')
def ctype(n): return 2 if n.endswith(TEXT) else 1
fin = json.load(open(H + '/final_cc.json'))
assert set(fin['add']) == {NEW}, set(fin['add'])
allnames = {}
for p in sorted(f[:-6] for f in os.listdir(BASE) if f.endswith('.index')):
    for e in m2pack.read_index(BASE + '/%s.index' % p)[2]: allnames.setdefault(e['name'], p)
add = {}
for k, src in fin['add'][NEW].items():
    assert k not in allnames, (k, allnames[k]); add[k] = (packlib.rd(src), ctype(k))
shutil.rmtree(OUT, ignore_errors=True); os.makedirs(OUT)
tmpl = m2pack.read_index(BASE + '/az_fix1.index')[2][-1]['raw']
packlib.repack_add_typed(None, None, {}, add, OUT + '/%s.index' % NEW, OUT + '/%s.data' % NEW, tmpl)
ix = packlib.rd(BASE + '/Index')
assert b'\n' + NEW.encode() + b'\n' not in ix + b'\n'
open(OUT + '/Index', 'wb').write(ix.rstrip(b'\n') + b'\n*\n' + NEW.encode() + b'\n')
f, v, ents = m2pack.read_index(OUT + '/%s.index' % NEW); d = packlib.rd(OUT + '/%s.data' % NEW)
names = [e['name'] for e in ents]; assert len(set(names)) == len(names) == len(add)
for e in ents:
    assert zlib.crc32(d[e['pos']:e['pos'] + e['size']]) & 0xffffffff == e['dcrc'], e['name']
    assert e['fcrc'] == zlib.crc32(e['name'].encode('cp1252')) & 0xffffffff, e['name']
    assert m2pack.read_entry(d, e) == add[e['name']][0], e['name']
print(json.dumps(dict(pack=NEW, entries=len(ents), data_mb=round(len(d) / 1e6, 2)), indent=1))
