# -*- coding: utf-8 -*-
# MT2009_PLUS_ATLANTYDA_V1 - what stage_atlantis.py needs of the client it builds on: the names of every entry of
# every pack ("<pack> <name>" a line, <work>/c58.lst) and the property pack's files (<work>/x/property/...), to
# leave out what our client has and to find property CRC clashes. Run in the m2pack-lzo image:
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/atlantis/dump_base.py \
#     [<BASE pack dir, default /opt/metin2/cache/c58/pack>] [<work dir, default /opt/metin2/cache/atlantis-work>]
import os
import shutil
import sys

sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
import m2pack  # noqa: E402
import packlib  # noqa: E402

P = sys.argv[1] if len(sys.argv) > 1 else '/opt/metin2/cache/c58/pack'
O = sys.argv[2] if len(sys.argv) > 2 else '/opt/metin2/cache/atlantis-work'
shutil.rmtree(os.path.join(O, 'x', 'property'), ignore_errors=True)
os.makedirs(O, exist_ok=True)
n = 0
with open(os.path.join(O, 'c58.lst'), 'w', encoding='utf-8') as lst:
    for p in sorted(f[:-6] for f in os.listdir(P) if f.endswith('.index')):
        f, v, ents = m2pack.read_index(os.path.join(P, p + '.index'))
        for e in ents:
            lst.write('%s %s\n' % (p, e['name']))
            n += 1
        if p == 'property':
            d = packlib.rd(os.path.join(P, p + '.data'))
            for e in ents:
                t = os.path.join(O, 'x', 'property', e['name'].replace('d:/', 'd_/'))
                os.makedirs(os.path.dirname(t), exist_ok=True)
                open(t, 'wb').write(m2pack.read_entry(d, e))
print('%d entries listed from %s' % (n, P))
