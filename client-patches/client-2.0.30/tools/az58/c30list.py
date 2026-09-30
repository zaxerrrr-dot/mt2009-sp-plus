import sys, os
sys.path.insert(0, '/opt/metin2/cache/tcm/tz'); sys.path.insert(0, '/opt/metin2/cache/tcm/gf28')
import m2pack, packlib
B = '/opt/metin2/cache/tcm/c30/pack'; O = '/opt/metin2/cache/arezzo-work/client/c30x'
for f in sorted(os.listdir(B)):
    if not f.endswith('.index'): continue
    p = f[:-6]
    fh, v, ents = m2pack.read_index(B + '/' + f)
    open(O + '/%s.lst' % p, 'w').write(''.join(e['name'] + '\n' for e in ents))
    if p in ('property', 'gamedata', 'locale', 'root'):
        d = packlib.rd(B + '/%s.data' % p)
        for e in ents:
            dst = os.path.join(O, p, e['name'].replace('d:/', 'd_/'))
            os.makedirs(os.path.dirname(dst), exist_ok=True); open(dst, 'wb').write(m2pack.read_entry(d, e))
    print(p, len(ents))
