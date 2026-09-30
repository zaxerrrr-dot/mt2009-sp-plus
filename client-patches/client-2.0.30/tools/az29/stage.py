# Repo staging copy: client-patches/client-2.0.30 (text + protos + generated files + tooling + manifest).
# The asset packs themselves stay in client/out/pack (manifest.json lists every entry and its source).
import os, sys, json, shutil, hashlib
HERE = os.path.dirname(os.path.abspath(__file__))
ST = sys.argv[1] if len(sys.argv) > 1 else '/opt/metin2/cache/arezzo-work/client/repo/client-patches/client-2.0.30'
OUTX = sys.argv[2] if len(sys.argv) > 2 else '/opt/metin2/cache/arezzo-work/client/out/extract'
GEN = '/opt/metin2/cache/arezzo-work/client/gen'
os.makedirs(ST, exist_ok=True)
def cp(src, rel):
    d = os.path.join(ST, rel); os.makedirs(os.path.dirname(d), exist_ok=True); shutil.copyfile(src, d)
for rel in ('gamedata/gamedata/atlasinfo.txt', 'gamedata/gamedata/npclist.txt', 'gamedata/gamedata/item_list.txt',
            'gamedata/gamedata/mob_proto', 'gamedata/gamedata/item_proto', 'locale/locale/pl/itemdesc.txt', 'root/localeinfo.py'):
    cp(os.path.join(OUTX, rel), rel)
for dp, dn, fn in os.walk(GEN):
    for f in fn:
        p = os.path.join(dp, f); cp(p, 'gen/' + os.path.relpath(p, GEN))
fin = json.load(open(HERE + '/final.json'))['add']
man = {}
for pack, m in sorted(fin.items()):
    man[pack] = {}
    for k, src in sorted(m.items()):
        b = open(src, 'rb').read()
        s = src.replace('/opt/metin2/cache/arezzo/cpack/files/', 'AREZZO:').replace('/opt/metin2/cache/gf/Gameforge_26.1.11/_client/', 'GF:').replace(GEN + '/', 'GEN:')
        man[pack][k] = dict(src=s, size=len(b), sha1=hashlib.sha1(b).hexdigest())
json.dump(man, open(ST + '/manifest.json', 'w'), indent=1, sort_keys=True)
T = ST + '/tools/az29'
os.makedirs(T + '/gr2', exist_ok=True)
for f in ('common.py', 'gfres.py', 'plan.py', 'gen.py', 'dxt.py', 'patch_gamedata.py', 'packlib.py', 'build_az.py', 'verify_az.py', 'stage.py', 'rebuild.sh', 'extract_out.py'):
    if os.path.exists(os.path.join(HERE, f)): shutil.copyfile(os.path.join(HERE, f), os.path.join(T, f))
for f in ('gr2dec.c', 'oodle1.c', 'oodle1.h', 'dllapi.h', 'debug.h', 'LICENSE-opengr2.txt'):
    shutil.copyfile(os.path.join(HERE, 'gr2', f), os.path.join(T, 'gr2', f))
shutil.copyfile('/opt/metin2/cache/arezzo-work/client/out/pack/Index', ST + '/Index')
print('staged', ST, sum(len(v) for v in man.values()), 'manifest entries')
