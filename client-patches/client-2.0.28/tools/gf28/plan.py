# Builds plan.json: which GF files go into which pack (MT2009 client 2.0.28 GF import).
import os, re, json, sys, gfres
from seeds import M, M2, N, N2
S = '/opt/metin2/cache/tcm/gf28'
OURPROP = S + '/ourprop_pre'   # extracted c28 property pack
ours = gfres.load_ours(S + '/ourpacks_pre.txt')
G = gfres.G

def prop_index(root):
    idx = {}
    for dp, dn, fn in os.walk(root):
        for f in fn:
            p = os.path.join(dp, f)
            l = open(p, 'rb').read().replace(b'\r', b'').split(b'\n')
            if l and l[0].strip() == b'YPRT' and len(l) > 1:
                idx.setdefault(int(l[1].strip()), p)
    return idx
GFPROP = prop_index(G + '/property'); OUR_PROP = prop_index(OURPROP)

def map_crcs(m):
    crcs = set()
    for dp, dn, fn in os.walk(os.path.join(G, m)):
        for f in fn:
            if f.lower() == 'areadata.txt':
                t = open(os.path.join(dp, f), 'rb').read().decode('latin1').replace('\r', '').split('\n')
                for i, l in enumerate(t):
                    if l.startswith('Start Object'):
                        crcs.add(int(t[i + 2].strip().split('#')[0]))
    return crcs

def prop_refs(m):
    """seeds = files referenced by the map's objects (our property file if we have it, else GF's);
    newprops = GF property files our property pack lacks."""
    seeds = set(); newprops = {}
    for c in map_crcs(m):
        p = OUR_PROP.get(c) or GFPROP.get(c)
        if c not in OUR_PROP:
            k = gfres.norm('property/' + os.path.relpath(GFPROP[c], G + '/property'))
            newprops[k] = GFPROP[c]
        for l in open(p, 'rb').read().decode('latin1').replace('\r', '').split('\n'):
            t = l.split(None, 1)
            if len(t) == 2 and t[0].lower().endswith('file'):
                v = t[1].strip().strip('"')
                if v: seeds.add(gfres.norm(v))
    return seeds, newprops

def mapseeds(m, ts, env):
    return ['maps/%s/' % m, 'textureset/%s' % ts]   # env is converted separately

GROUPS = [
 ('ochao', 'metin2_map_mt_th_dungeon_01', mapseeds('metin2_map_mt_th_dungeon_01', 'metin2_mtthunder_dungeon.txt', 'dark.msenv') + [
    M2+'lemures_soldier/', M2+'lemures_soldier2/', M2+'lemures_magic/', M2+'lemures_officer/', M2+'lemures_general/',
    M2+'lemures_boss/', M2+'lemures_boss2/', M2+'trent_officer/', N+'redguild_guard_m/', N+'warp/',
    'sound/monster2/lemures_soldier/', 'sound/monster2/lemures_soldier2/', 'sound/monster2/lemures_magic/',
    'sound/monster2/lemures_officer/', 'sound/monster2/lemures_general/', 'sound/monster2/lemures_boss/',
    'sound/monster2/lemures_boss2/', 'sound/monster2/trent_officer/', 'sound/npc/redguild_guard_m/',
    'd:/ymir work/ui/metin2_map_mt_th_dungeon_01.dds', 'd:/ymir work/ui/atlas_resize/metin2_map_mt_th_dungeon_01_atlas.dds']),
 ('gf_razador', 'metin2_map_n_flame_dungeon_01', mapseeds('metin2_map_n_flame_dungeon_01', 'metin2_map_n_flame_dungeon_01.txt', '') + [
    M2+'fire_ghost/', M2+'fire_tiger_boss/', M2+'fire_man/', M2+'fire_knight/', M2+'fire_king/',
    M2+'firegolem_soldier/', M2+'firegolem_magician/', M2+'firegolem_general/', M2+'firegolem_boss/', M2+'yamachun_boss/',
    M+'metinstone_02/', N2+'flame_dungeon_npc/', N2+'flame_bridge_block_chain/', N2+'flame_door_npc/',
    'sound/monster2/fire_ghost/', 'sound/monster2/fire_tiger_boss/', 'sound/monster2/fire_man/', 'sound/monster2/fire_knight/',
    'sound/monster2/fire_king/', 'sound/monster2/firegolem_soldier/', 'sound/monster2/firegolem_magician/',
    'sound/monster2/firegolem_general/', 'sound/monster2/firegolem_boss/', 'sound/monster2/yamachun_boss/',
    'sound/monster/metinstone_02/', 'sound/npc2/flame_dungeon_npc/', 'sound/npc2/flame_bridge_block_chain/', 'sound/npc2/flame_door_npc/',
    'd:/ymir work/ui/metin2_map_n_flame_dungeon_01.dds', 'd:/ymir work/ui/atlas_resize/metin2_map_n_flame_dungeon_01_atlas.dds']),
 ('gf_nemere', 'metin2_map_n_snow_dungeon_01', mapseeds('metin2_map_n_snow_dungeon_01', 'metin2_map_n_snow_dungeon_01.txt', '') + [
    M+'ice_snow_monster/', M+'ice_snow_insect/', M+'ice_snow_man/', M+'ice_snow_giant_man/', M+'ice_snow_golem/',
    M2+'icegolem_soldier/', M2+'icegolem_magician/', M2+'icegolem_general/', M2+'icegolem_boss/', M2+'hanma_boss/',
    N2+'ice_lionstone/', N2+'ice_keybox/', N2+'ice_stonepillar/',
    'sound/monster/ice_snow_monster/', 'sound/monster/ice_snow_insect/', 'sound/monster/ice_snow_man/',
    'sound/monster/ice_snow_giant_man/', 'sound/monster/ice_snow_golem/', 'sound/monster2/icegolem_soldier/',
    'sound/monster2/icegolem_magician/', 'sound/monster2/icegolem_general/', 'sound/monster2/icegolem_boss/',
    'sound/monster2/hanma_boss/', 'sound/npc2/ice_lionstone/', 'sound/npc2/ice_keybox/', 'sound/npc2/ice_stonepillar/']),
 ('goblin', 'metin2_map_treasure_hunt', mapseeds('metin2_map_treasure_hunt', 'metin2_map_treasure_hunt.txt', '') + [
    N2+'treasure_hunt_goblin/', N2+'treasure_hunt_box/', 'd:/ymir work/zone/treasure_hunt/',
    'sound/npc2/treasure_hunt_goblin/', 'sound/npc2/treasure_hunt_box/']),
 ('gf_misc', None, [M2+'gnoll_general/', M2+'cyclops_officer/', M2+'triton_soldier/', M2+'redthief_bow/', M2+'redthief2_soldier2/',
    'sound/monster2/gnoll_general/', 'sound/monster2/cyclops_officer/', 'sound/monster2/triton_soldier/',
    'sound/monster2/redthief_bow/', 'sound/monster2/redthief2_soldier2/',
    'd:/ymir work/effect/pet/pet_pve_fire_01.mse']),
]
plan = {}      # pack -> {key: src}
where = {}     # key -> pack (first owner)
report = {}
newprops = {}
for pack, mapname, sd in GROUPS:
    sd = list(sd)
    if mapname:
        ps, npr = prop_refs(mapname); sd += sorted(ps); newprops.update(npr)
    files, unres, oh = gfres.closure(sd, ours)
    unres = {u for u in unres if not u.endswith('.msenv')}
    plan.setdefault(pack, {})
    for k, src in sorted(files.items()):
        if k in ours or k in where: continue
        dest = 'maps' if k.startswith('maps/') else pack
        if k.startswith('textureset/') and pack == 'goblin': dest = 'goblin'
        where[k] = dest; plan.setdefault(dest, {})[k] = src
    report[pack] = dict(unresolved=sorted(unres), n=len(files), already=len(oh))
# GF textureset of the Treasure Island replaces our stand-in (goblin pack already has the name)
plan['goblin_replace'] = {'textureset/metin2_map_treasure_hunt.txt': G + '/textureset/metin2_map_treasure_hunt.txt'}
plan['property'] = newprops
json.dump(dict(plan=plan, report=report), open('plan.json', 'w'), indent=1, sort_keys=True)
for p, f in plan.items():
    print('%-15s %5d files %6.1f MB' % (p, len(f), sum(os.path.getsize(v) for v in f.values()) / 1e6))
for p, r in report.items(): print(p, r['n'], 'already', r['already'], 'UNRES', r['unresolved'])
