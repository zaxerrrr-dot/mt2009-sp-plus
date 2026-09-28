# Generated/converted files for the GF import (MT2009 2.0.28) -> gen/ + final.json
import os, re, json, shutil, gfres
G = gfres.G; W = G + '/d_/ymir work'
GEN = '/opt/metin2/cache/tcm/gf28/gen'
shutil.rmtree(GEN, ignore_errors=True)
pl = json.load(open('plan.json'))['plan']
add = {p: dict(v) for p, v in pl.items() if p not in ('goblin_replace',)}
replace = {'goblin': dict(pl['goblin_replace']), 'ochao': {}, 'maps': {}}
def gen(key, data):
    p = os.path.join(GEN, key.replace('d:/', 'd_/', 1)); os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'wb').write(data); return p
def crlf(s): return s.replace('\r\n', '\n').replace('\n', '\r\n')

# 1. msenv: the 2.0.25 exe reads Fog Enable/NearDistance/FarDistance, not GF's "foglevel"
FOG = {'dark.msenv': (1000, 20000), 'metin2_map_n_flame_dungeon_01.msenv': (1000, 30000),
       'metin2_map_n_snow_dungeon_01.msenv': (1000, 30000), 'metin2_map_treasure_hunt.msenv': (5000, 60000)}
def conv_msenv(name):
    t = open(os.path.join(W, 'environment', name), 'rb').read().decode('latin1').replace('\r', '')
    near, far = FOG[name]
    t2, n = re.subn(r'(?im)^([ \t]*)foglevel[ \t]+\d+[ \t]*$',
                    lambda m: '%sEnable        1\n%sNearDistance  %.6f\n%sFarDistance   %.6f' % (m.group(1), m.group(1), near, m.group(1), far), t)
    assert n == 1, name
    return crlf(t2).encode('latin1')
envs = {'dark.msenv': ('ochao', 'metin2_map_mt_th_dungeon_01'),
        'metin2_map_n_flame_dungeon_01.msenv': ('gf_razador', 'metin2_map_n_flame_dungeon_01'),
        'metin2_map_n_snow_dungeon_01.msenv': ('gf_nemere', 'metin2_map_n_snow_dungeon_01'),
        'metin2_map_treasure_hunt.msenv': ('goblin', 'metin2_map_treasure_hunt')}
for name, (pack, m) in envs.items():
    b = conv_msenv(name)
    k1 = 'd:/ymir work/environment/' + name; k2 = 'maps/%s/%s' % (m, name)
    if pack == 'goblin':   # both names already exist in goblin/maps
        replace['goblin'][k1] = gen(k1, b); replace['maps'][k2] = gen(k2, b)
    else:
        add[pack][k1] = gen(k1, b); add['maps'][k2] = gen(k2, b)
    # skybox / flare / cloud textures the environment names
    ours = gfres.load_ours('/opt/metin2/cache/tcm/gf28/ourpacks_pre.txt')
    files, unres, oh = gfres.closure(sorted(gfres.refs_of(k1, os.path.join(W, 'environment', name))), ours)
    assigned = set(k for v in add.values() for k in v)
    for k, src in files.items():
        if k not in ours and k not in assigned: add[pack][k] = src
    assert not unres, (name, unres)

# 2. big-map atlas (exe: d:/ymir work/ui/atlas/<map>/atlas.sub, image relative to d:/ymir work/ui/)
for m, pack in (('metin2_map_mt_th_dungeon_01', 'ochao'), ('metin2_map_n_flame_dungeon_01', 'gf_razador')):
    img = 'atlas_resize/%s_atlas.dds' % m
    assert 'd:/ymir work/ui/' + img in add[pack] or 'd:/ymir work/ui/' + img in gfres.GF
    k = 'd:/ymir work/ui/atlas/%s/atlas.sub' % m
    add[pack][k] = gen(k, crlf('title subImage\nversion 1.0\nimage "%s"\nleft 0\ntop 0\nright 352\nbottom 352\n' % img).encode())

# 3. Top1 badge: GF has no effect/gm/top1.mse; the Battle Royale leader crown (effect/battleroyale/crown01.mse) is the equivalent
t = open(W + '/effect/battleroyale/crown01.mse', 'rb').read().decode('latin1').replace('\r', '')
t = t.replace('"crown01.dds"', '"top1.dds"')
t = t.replace('0.000000 "MOVING_TYPE_DIRECT" 0.000000 0.000000 110.150993', '0.000000 "MOVING_TYPE_DIRECT" 0.000000 0.000000 240.000000')
t = t.replace('BoundingSpherePosition 0.000000 0.000000 120.000000', 'BoundingSpherePosition 0.000000 0.000000 240.000000')
assert '240.000000' in t and 'top1.dds' in t
add['gf_misc']['d:/ymir work/effect/gm/top1.mse'] = gen('d:/ymir work/effect/gm/top1.mse', crlf(t).encode('latin1'))
add['gf_misc']['d:/ymir work/effect/gm/top1.dds'] = W + '/effect/battleroyale/crown01.dds'

# 4. mounts: the motlist names wait1/wait2.msa (probability 0) that no client ships -> copies of wait.msa
for m in ('summer_2023_hoverboard', 'summer_2026_drakkar'):
    for w in ('wait1', 'wait2'):
        add['gf_misc']['d:/ymir work/npc_mount/%s/%s.msa' % (m, w)] = W + '/npc_mount/%s/wait.msa' % m

# 5. Razador: GF lacks effect/monster2/yellowred1_great.mse (his body glow) -> copy of yellowred1.mse
add['gf_razador']['d:/ymir work/effect/monster2/yellowred1_great.mse'] = W + '/effect/monster2/yellowred1.mse'
#    flame_bridge_block_chain/front_dead.msa points at a developer path (D:/scm/...)
k = 'd:/ymir work/npc2/flame_bridge_block_chain/front_dead.msa'
t = open(W + '/npc2/flame_bridge_block_chain/front_dead.msa', 'rb').read().decode('latin1')
t2 = t.replace('"D:/scm/metin2/main/Data/npc2/flame_bridge_block_chain/front_dead.GR2"', '"D:/Ymir Work/npc2/flame_bridge_block_chain/front_dead.GR2"')
assert t2 != t
add['gf_razador'][k] = gen(k, t2.encode('latin1'))

# 6. Ochao: official text files that differ from the Version 16.2 package's (EnableHitProcess, RUN motion)
for k in ('d:/ymir work/npc/redguild_guard_m/motlist.txt', 'd:/ymir work/monster2/trent_officer/normal_attack.msa',
          'd:/ymir work/monster2/trent_officer/normal_attack1.msa'):
    replace['ochao'][k] = gfres.GF[k]
#    maps: 3 areadata.txt of the temple differ by 10 units from the official ones
for s in ('000002', '001000', '001001'):
    k = 'maps/metin2_map_mt_th_dungeon_01/%s/areadata.txt' % s
    replace['maps'][k] = gfres.GF[k]

for p in add: assert all(os.path.exists(v) for v in add[p].values()), p
json.dump(dict(add=add, replace=replace), open('final.json', 'w'), indent=1, sort_keys=True)
for p in sorted(set(add) | set(replace)):
    print('%-12s add %4d (%5.1f MB)  replace %d' % (p, len(add.get(p, {})), sum(os.path.getsize(v) for v in add.get(p, {}).values()) / 1e6, len(replace.get(p, {}))))
