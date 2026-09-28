M = 'd:/ymir work/monster/'; M2 = 'd:/ymir work/monster2/'; N = 'd:/ymir work/npc/'; N2 = 'd:/ymir work/npc2/'
def mapseeds(m, ts, env):
    return ['maps/%s/' % m, 'textureset/%s' % ts, 'd:/ymir work/environment/%s' % env]
GROUPS = {
 'ochao': mapseeds('metin2_map_mt_th_dungeon_01', 'metin2_mtthunder_dungeon.txt', 'dark.msenv') + [
    M2+'lemures_soldier/', M2+'lemures_soldier2/', M2+'lemures_magic/', M2+'lemures_officer/', M2+'lemures_general/',
    M2+'lemures_boss/', M2+'lemures_boss2/', M2+'trent_officer/', N+'redguild_guard_m/', N+'warp/',
    'sound/monster2/lemures_soldier/', 'sound/monster2/lemures_soldier2/', 'sound/monster2/lemures_magic/',
    'sound/monster2/lemures_officer/', 'sound/monster2/lemures_general/', 'sound/monster2/lemures_boss/',
    'sound/monster2/lemures_boss2/', 'sound/monster2/trent_officer/', 'd:/ymir work/ui/metin2_map_mt_th_dungeon_01.dds'],
 'razador': mapseeds('metin2_map_n_flame_dungeon_01', 'metin2_map_n_flame_dungeon_01.txt', 'metin2_map_n_flame_dungeon_01.msenv') + [
    M2+'fire_ghost/', M2+'fire_tiger_boss/', M2+'fire_man/', M2+'fire_knight/', M2+'fire_king/',
    M2+'firegolem_soldier/', M2+'firegolem_magician/', M2+'firegolem_general/', M2+'firegolem_boss/', M2+'yamachun_boss/',
    M+'metinstone_02/', N2+'flame_dungeon_npc/', N2+'flame_bridge_block_chain/', N2+'flame_door_npc/',
    'd:/ymir work/ui/metin2_map_n_flame_dungeon_01.dds'],
 'nemere': mapseeds('metin2_map_n_snow_dungeon_01', 'metin2_map_n_snow_dungeon_01.txt', 'metin2_map_n_snow_dungeon_01.msenv') + [
    M+'ice_snow_monster/', M+'ice_snow_insect/', M+'ice_snow_man/', M+'ice_snow_giant_man/', M+'ice_snow_golem/',
    M2+'icegolem_soldier/', M2+'icegolem_magician/', M2+'icegolem_general/', M2+'icegolem_boss/', M2+'hanma_boss/',
    N2+'ice_lionstone/', N2+'ice_keybox/', N2+'ice_stonepillar/', 'd:/ymir work/ui/metin2_map_n_snow_dungeon_01.dds'],
 'treasure': mapseeds('metin2_map_treasure_hunt', 'metin2_map_treasure_hunt.txt', 'metin2_map_treasure_hunt.msenv') + [
    N2+'treasure_hunt_goblin/', N2+'treasure_hunt_box/', 'd:/ymir work/zone/treasure_hunt/'],
 'misc': [M2+'gnoll_general/', M2+'cyclops_officer/', M2+'triton_soldier/', M2+'redthief_bow/', M2+'redthief2_soldier2/',
    'icon/item/50260.tga', 'd:/ymir work/effect/gm/top1.mse', 'd:/ymir work/effect/etc/fall/waterwheel_small.mse',
    'd:/ymir work/npc_mount/summer_2023_hoverboard/', 'd:/ymir work/npc_mount/summer_2026_drakkar/',
    'd:/ymir work/effect/pet/pet_fenfire_01.mse', 'd:/ymir work/effect/pet/pet_fenfire_02.mse',
    'd:/ymir work/effect/jin_han/work/efect_duel_jin_han_sender.mse', 'd:/ymir work/effect/pet/pet_pve_fire_01.mse'],
}
