# Builds plan.json: which GF files go into which pack (MT2009 client 2.0.28 GF import).
import os, re, json, sys, gfres
from seeds import M, M2, N, N2
S = '/opt/metin2/cache/tcm/gf28'
OURPROP = S + '/ourprop_pre'   # extracted c28 property pack
ours = gfres.load_ours(S + '/ourpacks_pre.txt')
G = gfres.G
G_ALL = gfres.GF

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
        text = open(p, 'rb').read().decode('latin1')
        for l in text.replace('\r', '').split('\n'):
            t = l.split(None, 1)
            if len(t) == 2 and t[0].lower().endswith('file'):
                v = t[1].strip().strip('"')
                if v: seeds.add(gfres.norm(v))
        # collision + walkable height: the exe loads NoExtension(model).mdatr, the property never names it
        model = gfres.prop_attr_model(text)
        if model and gfres.mdatr_of(model) in G_ALL: seeds.add(gfres.mdatr_of(model))
    return seeds, newprops

def mapseeds(m, ts, env):
    return ['maps/%s/' % m, 'textureset/%s' % ts]   # env is converted separately

GOBLIN_MOBS = ('gnoll_soldier gnoll_bow gnoll_soldier2 gnoll_magic gnoll_general cyclops_soldier cyclops_soldier2 cyclops_magic '
    'cyclops_officer cyclops_general manticore_soldier manticore_soldier2 manticore_magic manticore_officer manticore_general '
    'lemures_soldier lemures_soldier2 lemures_magic lemures_officer lemures_general triton_soldier triton_soldier2 triton_magic '
    'triton_officer triton_general redthief_bow redthief_soldier2 redthief_magic redthief_officer redthief_general redthief2_bow '
    'redthief2_soldier2 redthief2_magic redthief2_officer redthief2_general crustacean_soldier crustacean_bow crustacean_soldier2 '
    'crustacean_officer crustacean_general giant_soldier giant_soldier2 giant_magic giant_officer giant_general ogre_soldier '
    'ogre_bow ogre_officer ogre_magic ogre_general').split()
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
 # Treasure Island waves (playerbot_goblin.h MOB_POOL 3001-3805): every race's model, motions, sounds
 ('gf_mobs', None, [M2 + n + '/' for n in GOBLIN_MOBS] + ['sound/monster2/%s/' % n for n in GOBLIN_MOBS]),
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
# Entrance maps (base-client maps, not imported): the textures their objects' .gr2 models name, so the
# dungeon gates / props there are never drawn untextured, and their .mdatr (collision / walkable height) so
# bridges are walked ON and buildings block (base-client copies, if any, are identical names).
ENTRANCES = (('gf_razador', 'metin2_map_n_flame_01'), ('gf_nemere', 'map_n_snowm_01'))
for pack, m in ENTRANCES:
    ps, npr = prop_refs(m)
    tex = set()
    for k in ps:
        if k.endswith('.gr2') and k in G_ALL: tex |= gfres.refs_of(k, G_ALL[k])
        if k.endswith('.mdatr'): tex.add(k)   # collision/height of the gate, bridges, towers (item 27)
    files, unres, oh = gfres.closure(sorted(tex), ours)
    for k, src in sorted(files.items()):
        if k in ours or k in where: continue
        where[k] = pack; plan[pack][k] = src
    report[pack + '@' + m] = dict(unresolved=sorted(unres), n=len(files), already=len(oh))
# GF textureset of the Treasure Island replaces our stand-in (goblin pack already has the name)
plan['goblin_replace'] = {'textureset/metin2_map_treasure_hunt.txt': G + '/textureset/metin2_map_treasure_hunt.txt'}
plan['property'] = newprops
json.dump(dict(plan=plan, report=report), open('plan.json', 'w'), indent=1, sort_keys=True)
for p, f in plan.items():
    print('%-15s %5d files %6.1f MB' % (p, len(f), sum(os.path.getsize(v) for v in f.values()) / 1e6))
for p, r in report.items(): print(p, r['n'], 'already', r['already'], 'UNRES', r['unresolved'])
