# Extract the changed text/proto entries of out/pack (gamedata, locale, root) to out/extract for staging.
import sys, os
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
import m2pack
O = '/opt/metin2/cache/arezzo-work/client/out/pack'; X = '/opt/metin2/cache/arezzo-work/client/out/extract'
want = {'gamedata': ['gamedata/atlasinfo.txt', 'gamedata/npclist.txt', 'gamedata/item_list.txt', 'gamedata/mob_proto', 'gamedata/item_proto'],
        'locale': ['locale/pl/itemdesc.txt'], 'root': ['localeinfo.py']}
for p, names in want.items():
    f, v, ents = m2pack.read_index(O + '/%s.index' % p); d = open(O + '/%s.data' % p, 'rb').read()
    for e in ents:
        if e['name'] in names:
            dst = os.path.join(X, p, e['name']); os.makedirs(os.path.dirname(dst), exist_ok=True)
            open(dst, 'wb').write(m2pack.read_entry(d, e))
print('extracted')
