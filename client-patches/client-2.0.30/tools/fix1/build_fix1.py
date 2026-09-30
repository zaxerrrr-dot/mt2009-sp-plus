# Client 2.0.31: new pack az_fix1 with the files from fix1/closure.json (add) on top of BASE; Index gets it at the end.
import os, sys, json, shutil
sys.path.insert(0, '/opt/metin2/cache/tcm/tz'); sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
import m2pack, packlib
BASE = sys.argv[1] if len(sys.argv) > 1 else '/opt/metin2/cache/tcm/c30/pack'
OUT = sys.argv[2] if len(sys.argv) > 2 else '/opt/metin2/cache/arezzo-work/client/fix1/out/pack'
H = '/opt/metin2/cache/arezzo-work/client/fix1'
TEXT = ('.txt', '.msa', '.msm', '.mse', '.mss', '.msenv', '.sub', '.prb', '.prd', '.pre', '.prt', '.py', '.ifl', '.pra')
add = json.load(open(H + '/closure.json'))['add']
shutil.rmtree(OUT, ignore_errors=True); os.makedirs(OUT)
allnames = set()
for p in sorted(f[:-6] for f in os.listdir(BASE) if f.endswith('.index')):
    for e in m2pack.read_index(BASE + '/%s.index' % p)[2]: allnames.add(e['name'])
items = {}
for k, src in sorted(add.items()):
    assert k not in allnames, k
    items[k] = (open(src, 'rb').read(), 2 if k.endswith(TEXT) else 1)
tmpl = m2pack.read_index(BASE + '/az_mobs.index')[2][-1]['raw']
r = packlib.repack_add_typed(None, None, {}, items, OUT + '/az_fix1.index', OUT + '/az_fix1.data', tmpl)
ix = packlib.rd(BASE + '/Index')
if b'\naz_fix1\n' not in ix + b'\n':
    ix = ix.rstrip(b'\n') + b'\n*\naz_fix1\n'
open(OUT + '/Index', 'wb').write(ix)
# read back
f, v, ents = m2pack.read_index(OUT + '/az_fix1.index'); d = packlib.rd(OUT + '/az_fix1.data')
assert len(ents) == len(items)
for e in ents:
    assert m2pack.read_entry(d, e) == items[e['name']][0], e['name']
print('az_fix1', len(ents), 'entries', os.path.getsize(OUT + '/az_fix1.data'), 'bytes; read back OK')
