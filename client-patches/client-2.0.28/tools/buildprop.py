# pack/property 2.0.28: the owner's client property pack + Treasure Island and Temple of Ochao objects
import os, sys, zlib, shutil
sys.path.insert(0, '/w'); sys.path.insert(0, '/s')
import m2pack, packlib
SRC = '/s/stage/property/property'
add = {}
for dp, dn, fn in os.walk(SRC):
    for f in fn:
        p = os.path.join(dp, f)
        name = ('property/' + os.path.relpath(p, SRC).replace(os.sep, '/')).lower()
        add[name] = (open(p, 'rb').read(), 2)
f, v, ents = m2pack.read_index('/s/prop/property.index')
tmpl = [e for e in ents if e['name'].endswith('.prb')][0]['raw']
r = packlib.repack_add_typed('/s/prop/property.index', '/s/prop/property.data', {}, add, '/s/out/pack/property.index', '/s/out/pack/property.data', tmpl)
print('property pack: %d entries, +%d new, %d replaced' % r)
# verify
f, v, new = m2pack.read_index('/s/out/pack/property.index'); nd = open('/s/out/pack/property.data', 'rb').read()
od = open('/s/prop/property.data', 'rb').read()
nb = dict((e['name'], e) for e in new)
assert len(nb) == len(new) == len(ents) + len(add)
for e in new:
    assert zlib.crc32(nd[e['pos']:e['pos'] + e['size']]) & 0xffffffff == e['dcrc']
    assert e['fcrc'] == zlib.crc32(e['name'].encode('cp1252')) & 0xffffffff
changed = [e['name'] for e in ents if m2pack.read_entry(od, e) != m2pack.read_entry(nd, nb[e['name']])]
bad = [n for n, (b, c) in add.items() if m2pack.read_entry(nd, nb[n]) != b]
crcs = {}
for e in new:
    raw = m2pack.read_entry(nd, e); l = raw.split(b'\n')
    if l[0].strip() == b'YPRT': crcs.setdefault(l[1].strip(), []).append(e['name'])
dup = dict((k, v) for k, v in crcs.items() if len(v) > 1)
print('old entries changed: %d, new entries mismatched: %d, total %d, property CRCs %d, duplicate CRCs %d %s' % (len(changed), len(bad), len(new), len(crcs), len(dup), list(dup.items())[:5]))
