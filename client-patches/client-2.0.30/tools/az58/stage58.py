# Repo staging copy: client-patches/client-2.0.30, phases 5-8 on top of phase 1 (the text/proto files are the
# latest - they carry phase 1 too), generated files in gen58/, tooling in tools/az58, manifest58.json.
import os, sys, json, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
ST = sys.argv[1] if len(sys.argv) > 1 else '/opt/metin2/cache/arezzo-work/client/repo/client-patches/client-2.0.30'
OUTX = '/opt/metin2/cache/arezzo-work/client/out58/extract'
GEN = '/opt/metin2/cache/arezzo-work/client/gen58'
import hashlib
def cp(src, rel):
    d = os.path.join(ST, rel); os.makedirs(os.path.dirname(d), exist_ok=True); shutil.copyfile(src, d)
for rel in ('gamedata/gamedata/atlasinfo.txt', 'gamedata/gamedata/npclist.txt', 'gamedata/gamedata/item_list.txt',
            'gamedata/gamedata/mob_proto', 'gamedata/gamedata/item_proto', 'locale/locale/pl/itemdesc.txt', 'root/localeinfo.py'):
    cp(os.path.join(OUTX, rel), rel)
for dp, dn, fn in os.walk(GEN):
    for f in fn:
        p = os.path.join(dp, f); cp(p, 'gen58/' + os.path.relpath(p, GEN))
fin = json.load(open(HERE + '/final58.json'))['add']
man = {}
for pack, m in sorted(fin.items()):
    man[pack] = {}
    for k, src in sorted(m.items()):
        b = open(src, 'rb').read()
        s = src.replace('/opt/metin2/cache/arezzo/cpack/files/', 'AREZZO:').replace('/opt/metin2/cache/gf/Gameforge_26.1.11/_client/', 'GF:').replace(GEN + '/', 'GEN:')
        man[pack][k] = dict(src=s, size=len(b), sha1=hashlib.sha1(b).hexdigest())
json.dump(man, open(ST + '/manifest58.json', 'w'), indent=1, sort_keys=True)
T = ST + '/tools/az58'
os.makedirs(T, exist_ok=True)
for f in ('common58.py', 'plan58.py', 'gen58.py', 'patch_gamedata.py', 'patch_gamedata58.py', 'build58.py', 'verify58.py',
          'extract58.py', 'stage58.py', 'rebuild58.sh', 'gfres.py', 'dxt.py', 'packlib.py', '../c30list.py'):
    shutil.copyfile(os.path.join(HERE, f), os.path.join(T, os.path.basename(f)))
shutil.copyfile('/opt/metin2/cache/arezzo-work/client/out58/pack/Index', ST + '/Index')
print('staged', ST, sum(len(v) for v in man.values()), 'manifest58 entries')
