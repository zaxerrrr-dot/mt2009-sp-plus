# 2.0.28 round 3: root re-sync from w27 + dungeon npclist fallbacks, on top of the c28 packs.
import os, sys, zlib, subprocess, shutil
sys.path.insert(0, '/w'); sys.path.insert(0, '/s')
import m2pack, packlib
C28 = '/c28'; OUT = '/s/out3'
os.makedirs(OUT, exist_ok=True)
rd = packlib.rd
# root
f, v, ents = m2pack.read_index(C28 + '/root.index'); data = rd(C28 + '/root.data')
have = dict((e['name'], m2pack.read_entry(data, e)) for e in ents)
rep = {}; add = {}
for dp, dn, fn in os.walk('/t/w27'):
    for fl in fn:
        p = os.path.join(dp, fl); n = os.path.relpath(p, '/t/w27').replace(os.sep, '/'); b = rd(p)
        if n in have:
            if have[n] != b: rep[n] = b
        else: add[n] = (b, 1 if n.endswith('.tga') else 2)
tmpl = [e for e in ents if e['name'] == 'uiscript/mt2009battlepass.py'][0]['raw']
print('root', packlib.repack_add_typed(C28 + '/root.index', C28 + '/root.data', rep, add, OUT + '/root.index', OUT + '/root.data', tmpl), sorted(rep), len(add))
# gamedata npclist
f, v, gents = m2pack.read_index(C28 + '/gamedata.index'); gdata = rd(C28 + '/gamedata.data')
npl = [m2pack.read_entry(gdata, e) for e in gents if e['name'] == 'gamedata/npclist.txt'][0]
open('/s/tmp_npc_in.txt', 'wb').write(npl)
subprocess.check_call([sys.executable, '/t/dungeons_client/tools/patch_npclist.py', '/s/tmp_npc_in.txt', '/s/tmp_npc_out.txt'])
subprocess.check_call([sys.executable, '/t/dungeons_client/tools/patch_npclist.py', '/s/tmp_npc_out.txt', '/s/tmp_npc_out2.txt'])
new = rd('/s/tmp_npc_out.txt'); assert new == rd('/s/tmp_npc_out2.txt'), 'not idempotent'
print('gamedata', packlib.repack_add_typed(C28 + '/gamedata.index', C28 + '/gamedata.data', {'gamedata/npclist.txt': new}, {}, OUT + '/gamedata.index', OUT + '/gamedata.data'))
# verify
for pack, exp in (('root', dict(list(rep.items()) + [(k, b) for k, (b, c) in add.items()])), ('gamedata', {'gamedata/npclist.txt': new})):
    f, v, old = m2pack.read_index(C28 + '/%s.index' % pack); od = rd(C28 + '/%s.data' % pack)
    f, v, nw = m2pack.read_index(OUT + '/%s.index' % pack); nd = rd(OUT + '/%s.data' % pack)
    nb = dict((e['name'], e) for e in nw); assert len(nb) == len(nw)
    for e in nw:
        assert zlib.crc32(nd[e['pos']:e['pos'] + e['size']]) & 0xffffffff == e['dcrc']
        assert e['fcrc'] == zlib.crc32(e['name'].encode('cp1252')) & 0xffffffff
    got = dict((e['name'], m2pack.read_entry(nd, e)) for e in nw)
    assert all(got[k] == b for k, b in exp.items())
    changed = [e['name'] for e in old if m2pack.read_entry(od, e) != got[e['name']]]
    print('verify', pack, len(old), '->', len(nw), 'changed old:', changed)
