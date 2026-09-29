import os, sys, zlib
sys.path.insert(0, '/w'); sys.path.insert(0, '/s')
import m2pack, packlib
C28 = '/c28'; OUT = '/s/out'
os.makedirs(OUT, exist_ok=True)
rd = packlib.rd
f, v, ents = m2pack.read_index(C28 + '/root.index'); data = rd(C28 + '/root.data')
have = dict((e['name'], m2pack.read_entry(data, e)) for e in ents)
rep = {}; add = {}
for dp, dn, fn in os.walk('/t/w27'):
    for fl in fn:
        if fl.endswith('.pyc'): continue
        p = os.path.join(dp, fl); n = os.path.relpath(p, '/t/w27').replace(os.sep, '/'); b = rd(p)
        if n in have:
            if have[n] != b: rep[n] = b
        else: add[n] = (b, 1 if n.endswith('.tga') else 2)
tmpl = [e for e in ents if e['name'] == 'uiscript/mt2009battlepass.py'][0]['raw']
print('root', packlib.repack_add_typed(C28 + '/root.index', C28 + '/root.data', rep, add, OUT + '/root.index', OUT + '/root.data', tmpl), sorted(rep), sorted(add))
f, v, nw = m2pack.read_index(OUT + '/root.index'); nd = rd(OUT + '/root.data')
exp = dict(list(rep.items()) + [(k, b) for k, (b, c) in add.items()])
for e in nw:
    assert zlib.crc32(nd[e['pos']:e['pos'] + e['size']]) & 0xffffffff == e['dcrc']
got = dict((e['name'], m2pack.read_entry(nd, e)) for e in nw)
assert all(got[k] == b for k, b in exp.items())
print('verify ok', len(ents), '->', len(nw))
