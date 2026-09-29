# Staging copy of the GF import in client-patches/client-2.0.28 (<pack>/<entry name>, "d:" -> "d_")
import os, json, shutil
ST = '/opt/metin2/git/mt2009-sp-plus/client-patches/client-2.0.28'
HERE = '/opt/metin2/cache/tcm/gf28'
fin = json.load(open(HERE + '/final.json'))
n = 0
def put(pack, key, src):
    global n
    dst = os.path.join(ST, pack, key.replace('d:/', 'd_/', 1))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(src, dst); n += 1
for part in ('add', 'replace'):
    for pack, m in fin[part].items():
        for k, src in m.items(): put(pack, k, src)
put('gamedata', 'gamedata/npclist.txt', HERE + '/npclist.new.txt')
put('icon', 'icon/item/50260.tga', HERE + '/icon_50255.tga')
shutil.copyfile('/opt/metin2/cache/tcm/c28/pack/Index', ST + '/Index')
os.makedirs(ST + '/tools/gf28', exist_ok=True)
for f in ('gfres.py', 'seeds.py', 'stage.py', 'verify_gr2tex.py', 'plan.py', 'gen.py', 'build_gf.py', 'verify_all.py', 'verify_refs.py', 'make_zips.py', 'rebuild.sh', 'attr/srvattr.py', 'attr/check_fix.py', 'attr/gen_nemere.py'):
    if os.path.exists(os.path.join(HERE, f)): shutil.copyfile(os.path.join(HERE, f), os.path.join(ST, 'tools/gf28', os.path.basename(f)))
os.makedirs(ST + '/tools/gf28/gr2', exist_ok=True)
for f in ('gr2dec.c', 'oodle1.c', 'oodle1.h', 'dllapi.h', 'debug.h', 'LICENSE-opengr2.txt'):
    shutil.copyfile(os.path.join(HERE, 'gr2', f), os.path.join(ST, 'tools/gf28/gr2', f))
print('staged', n, 'files')
