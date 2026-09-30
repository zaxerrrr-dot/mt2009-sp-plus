# Client 2.0.31: root pack with the repo's uidungeoninfo.py (teleport question fix).
import os, sys
sys.path.insert(0, '/opt/metin2/cache/tcm/tz'); sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
import m2pack, packlib
BASE = '/opt/metin2/cache/tcm/c30/pack'; OUT = '/opt/metin2/cache/arezzo-work/client/fix1/out/pack'
SRC = '/opt/metin2/git/mt2009-sp-plus/client-patches/client-2.0.30/root/'
f, v, ents = m2pack.read_index(BASE + '/root.index'); d = packlib.rd(BASE + '/root.data')
names = [e['name'] for e in ents]
rep = {}
for n in ('uidungeoninfo.py', 'playerbot_status_tail.py'):
    k = [x for x in names if x.endswith(n)]; assert len(k) == 1, k
    new = open(SRC + n, 'rb').read()
    old = m2pack.read_entry(d, [e for e in ents if e['name'] == k[0]][0])
    print(k[0], len(old), '->', len(new), 'same' if old == new else 'changed')
    if old != new: rep[k[0]] = new
r = packlib.repack_add_typed(BASE + '/root.index', BASE + '/root.data', rep, {}, OUT + '/root.index', OUT + '/root.data')
f2, v2, e2 = m2pack.read_index(OUT + '/root.index'); d2 = packlib.rd(OUT + '/root.data')
for e in e2:
    b = m2pack.read_entry(d2, e)
    exp = rep.get(e['name'])
    if exp is None: exp = m2pack.read_entry(d, [x for x in ents if x['name'] == e['name']][0])
    assert b == exp, e['name']
print('root', len(e2), 'entries, read back OK')
