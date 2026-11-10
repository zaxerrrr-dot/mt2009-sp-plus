#!/usr/bin/env python3
"""gen_ymaps_sql.py <Owsap mob_proto.txt> <Owsap mob_names.txt> <out .sql>

MT2009_PLUS_YOHARA_MAPS1_V1: the world.mob_proto rows of the first two Yohara maps - Opuszczona Twierdza (374,
metin2_map_empirecastle) and Dongan (373, metin2_map_eastplain_01); plan cache/yohara/plan-mapy-yohary.md. Owsap
v6.2.6's numbers (the official vnums, levels 119-125 and HP as they are - balance: see the notes in the output) in
our r40250 columns, the Polish names of the pl-wiki. Writes linux-port/docker/mariadb/playerbot/yohara_maps.sql.

Example: python3 tools/yohara_maps/gen_ymaps_sql.py /opt/metin2/cache/owsap/Server/Server/db/mob_proto.txt \
         /opt/metin2/cache/owsap/Server/Server/db/mob_names.txt linux-port/docker/mariadb/playerbot/yohara_maps.sql
"""
import csv
import sys

# vnum -> Polish name (pl-wiki: Opuszczona Twierdza, Dongan, the monsters' and NPCs' pages). The element in
# brackets follows Owsap's Att* column (6686-6692 dark, 6693-6699 ice, 6700-6706/6710 dark, 6711-6717 fire).
NAMES = {
    # Opuszczona Twierdza
    6686: 'Jin Bing (mrok)', 6687: 'Żołnierz Ki (mrok)', 6688: 'Żołnierz Mao (mrok)', 6689: 'Żołnierz Gong (mrok)',
    6690: 'Mag Frontowy (mrok)', 6691: 'Kao (mrok)', 6692: 'Król Bao (misja)',
    6693: 'Jin Bing (lód)', 6694: 'Żołnierz Ki (lód)', 6695: 'Żołnierz Mao (lód)', 6696: 'Żołnierz Gong (lód)',
    6697: 'Mag Frontowy (lód)', 6698: 'Kao (lód)', 6699: 'Król Bao',
    # Dongan
    6700: 'Piekielny Pies (mrok)', 6701: 'Troll Żołnierz (mrok)', 6702: 'Troll Wojownik (mrok)',
    6703: 'Troll Strzelec (mrok)', 6704: 'Troll Szamanka (mrok)', 6705: 'Natanan (mrok)', 6706: 'Argos (mrok)',
    6710: 'Dręczony Duch',
    6711: 'Piekielny Pies (ogień)', 6712: 'Troll Żołnierz (ogień)', 6713: 'Troll Wojownik (ogień)',
    6714: 'Troll Strzelec (ogień)', 6715: 'Troll Szamanka (ogień)', 6716: 'Natanan (ogień)', 6717: 'Argos (ogień)',
    # Metins
    8067: 'Metin Świadomość', 8625: 'Posterunek Trolli',
    # NPCs (no quests yet - they stand where the official ones stand)
    20799: 'Kwiaty', 20800: 'Ranny', 20802: 'Wartownik z Yohara', 20803: 'Strażnik z Yohara',
    20809: 'Konfucjusz', 20810: 'Chaegirab', 20811: 'Kim Rim', 20812: 'Admirał Angmur', 20823: 'Mistrz Chi',
    20830: 'Oddelegowany Komendant', 20831: 'Komandor z Yohara', 20833: 'Skażone Kwiaty', 20834: 'Relikwiarz',
    20836: 'Halabardnik', 20849: 'Taehwarang', 60003: 'Theowahdan',
}
# Owsap's 10107 "DongGwang 10629 4767" (Twierdza's gate -> Dongan) is our Lodowa Grota portal: 10144 (a "warp" race
# in npclist, free in our world.mob_proto and in Owsap's) carries it. Destination = Owsap's (Dongan 133, 415).
WARPS = {10144: 'Dongan 10629 4767'}

RANK = {'PAWN': 0, 'S_PAWN': 1, 'KNIGHT': 2, 'S_KNIGHT': 3, 'BOSS': 4, 'KING': 5}
TYPE = {'MONSTER': 0, 'NPC': 1, 'STONE': 2, 'WARP': 3}
BATTLE = {'MELEE': 0, 'RANGE': 1, 'MAGIC': 2, 'SPECIAL': 3, 'POWER': 4, 'TANKER': 5, 'SUPER_POWER': 6,
          'SUPER_TANKER': 7}
AI = ('AGGR', 'NOMOVE', 'COWARD', 'NOATTSHINSU', 'NOATTCHUNJO', 'NOATTJINNO', 'ATTMOB', 'BERSERK', 'STONESKIN',
      'GODSPEED', 'DEATHBLOW', 'REVIVE', 'IGNORE_LAST_ATTACK', 'NO_WANDER', 'SEE_OTHER_NPC', 'RETURN_LASTATTACK_POS',
      'LOOSE_AGGRO_ON_DISTANCE')
RACE = ('ANIMAL', 'UNDEAD', 'DEVIL', 'HUMAN', 'ORC', 'MILGYO', 'INSECT', 'FIRE', 'ICE', 'DESERT', 'TREE')
IMMUNE = ('STUN', 'SLOW', 'FALL', 'CURSE', 'POISON', 'TERROR', 'REFLECT')
COLS = ('vnum', 'name', 'locale_name', 'rank', 'type', 'battle_type', 'level', 'size', 'ai_flag', 'mount_capacity',
        'setRaceFlag', 'setImmuneFlag', 'empire', 'folder', 'on_click', 'st', 'dx', 'ht', 'iq', 'damage_min',
        'damage_max', 'max_hp', 'regen_cycle', 'regen_percent', 'gold_min', 'gold_max', 'exp', 'def', 'attack_speed',
        'move_speed', 'aggressive_hp_pct', 'aggressive_sight', 'attack_range', 'drop_item', 'resurrection_vnum',
        'enchant_curse', 'enchant_slow', 'enchant_poison', 'enchant_stun', 'enchant_critical', 'enchant_penetrate',
        'enchant_fire', 'enchant_root', 'resist_sword', 'resist_twohand', 'resist_dagger', 'resist_bell', 'resist_fan',
        'resist_bow', 'resist_fire', 'resist_elect', 'resist_magic', 'resist_wind', 'resist_poison', 'dam_multiply',
        'summon', 'drain_sp', 'mob_color', 'polymorph_item', 'skill_level0', 'skill_vnum0', 'skill_level1',
        'skill_vnum1', 'skill_level2', 'skill_vnum2', 'skill_level3', 'skill_vnum3', 'skill_level4', 'skill_vnum4',
        'sp_berserk', 'sp_stoneskin', 'sp_godspeed', 'sp_deathblow', 'sp_revive')


def q(s):
    return "'" + s.replace('\\', '\\\\').replace("'", "\\'") + "'"


def flags(v, allowed):
    return ','.join(f for f in v.split(',') if f.strip() in allowed)


def race_sql(races):
    """MT2009_PLUS_YOHARA_RASY_V1: the UPDATEs setting the races (setRaceFlag bits 0-10, RACE) of {vnum: 'ORC,DEVIL'} -
    the elements (bits 11-16) kept; for a generator's elements' file (every start, after its INSERT IGNORE)."""
    by = {}
    for v, f in races.items():
        names = [x.strip() for x in f.split(',') if x.strip()]
        assert all(x in RACE for x in names), (v, f)
        by.setdefault(sum(1 << RACE.index(x) for x in names), []).append(v)
    L = []
    for bits in sorted(by):
        vs = ','.join(map(str, sorted(by[bits])))
        L += ['-- race %s: %s' % (','.join(x for i, x in enumerate(RACE) if bits >> i & 1) or 'none', vs),
              'UPDATE world.mob_proto SET setRaceFlag = ((setRaceFlag + 0) & ~%d) | %d WHERE vnum IN (%s) AND '
              '(setRaceFlag + 0) & %d <> %d;' % ((1 << len(RACE)) - 1, bits, vs, (1 << len(RACE)) - 1, bits)]
    return L


def num(v):
    return int(float(v or 0))


def row_of(r, en, pl):
    g = lambda k: r[k]  # noqa: E731
    return (int(g('Vnum')), q(en[:24]), q(pl), RANK[g('Rank')], TYPE[g('Type')], BATTLE[g('BattleType')],
            num(g('Level')), "'NONE'", q(flags(g('AiFlags'), AI)), 0, q(flags(g('RaceFlags'), RACE)),
            q(flags(g('ImmuneFlags'), IMMUNE)), 0, q(g('Folder')), num(g('OnClick')), num(g('St')), num(g('Dx')),
            num(g('Ht')), num(g('Iq')), num(g('MinDamage')), num(g('MaxDamage')), num(g('MaxHp')),
            num(g('RegenCycle')), num(g('RegenPercent')), num(g('MinGold')), num(g('MaxGold')), num(g('Exp')),
            num(g('Def')), num(g('AttackSpeed')), num(g('MoveSpeed')), num(g('AggressiveHpPct')),
            num(g('AggressiveSight')), num(g('AttackRange')), 0, num(g('ResurrectionVnum')), num(g('EnchantCurse')),
            num(g('EnchantSlow')), num(g('EnchantPoison')), num(g('EnchantStun')), num(g('EnchantCritical')),
            num(g('EnchantPenetrate')), 0, 0, num(g('ResistSword')), num(g('ResistTwoHanded')), num(g('ResistDagger')),
            num(g('ResistBell')), num(g('ResistFan')), num(g('ResistBow')), num(g('ResistFire')),
            num(g('ResistElect')), num(g('ResistMagic')), num(g('ResistWind')), num(g('ResistPoison')),
            '%.1f' % float(g('DamMultiply') or 0), num(g('SummonVnum')), num(g('DrainSp')), num(g('MobColor')),
            num(g('PolymorphItem')), num(g('SkillLevel0')), num(g('SkillVnum0')), num(g('SkillLevel1')),
            num(g('SkillVnum1')), num(g('SkillLevel2')), num(g('SkillVnum2')), num(g('SkillLevel3')),
            num(g('SkillVnum3')), num(g('SkillLevel4')), num(g('SkillVnum4')), num(g('SpBerserk')),
            num(g('SpStoneSkin')), num(g('SpGodSpeed')), num(g('SpDeathBlow')), num(g('SpRevive')))


def npc_row(vnum, en, pl, folder):
    # Owsap's NPC rows 20799-20834 lack a column (MaxHp sits under MaxDamage): every NPC takes our own NPCs'
    # numbers instead (20016 Kowal: rank 5, level 1, 120 HP, on_click 2), Owsap's folder only
    return (vnum, q(en[:24]), q(pl), 5, 1, 0, 1, "'NONE'", "'NOMOVE'", 0, "''", "'STUN,SLOW,CURSE,TERROR'", 0, q(folder),
            2, 0, 0, 0, 0, 0, 0, 120, 3, 1, 0, 0, 10, 4, 100, 100, 0, 2000, 175) + (0,) * 21 + ('0.0',) + (0,) * 19


def warp_row(vnum, name):
    # our own warp portals' numbers (10101 Nefr.Zatoka): type WARP 3, battle 3, level 70
    return (vnum, q(name), q(name), 0, 3, 3, 70, "'NONE'", "'NOMOVE'", 0, "''", "'STUN,SLOW,CURSE,TERROR'", 0, "''",
            0, 0, 0, 0, 0, 0, 0, 3954, 3, 1, 0, 0, 562, 79, 100, 100, 0, 2000, 150) + (0,) * 21 + ('0.0',) + (0,) * 19


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    proto, names_path, out = sys.argv[1:]
    en = {}
    for line in open(names_path, encoding='latin-1'):
        p = line.rstrip('\r\n').split('\t')
        if len(p) >= 2 and p[0].isdigit():
            en[int(p[0])] = p[1]
    rd = csv.DictReader(open(proto, encoding='latin-1'), delimiter='\t')
    rows = {}
    for r in rd:
        if r['Vnum'].isdigit() and int(r['Vnum']) in NAMES:
            rows[int(r['Vnum'])] = r
    missing = sorted(set(NAMES) - set(rows))
    if missing:
        sys.exit('not in Owsap mob_proto: %s' % missing)
    for v, n in NAMES.items():
        assert len(n) <= 24, n
    lines = []
    for v in sorted(rows):
        if rows[v]['Type'] == 'NPC':
            t = npc_row(v, en.get(v, NAMES[v]), NAMES[v], rows[v]['Folder'])
        else:
            t = row_of(rows[v], en.get(v, NAMES[v]), NAMES[v])
        assert len(t) == len(COLS), (v, len(t))
        lines.append('(%s)' % ','.join(str(x) for x in t))
    for v, n in sorted(WARPS.items()):
        t = warp_row(v, n)
        assert len(t) == len(COLS), (v, len(t))
        lines.append('(%s)' % ','.join(str(x) for x in t))
    with open(out, 'w', encoding='utf-8', newline='\n') as f:
        f.write(HEADER)
        f.write('INSERT IGNORE INTO world.mob_proto (%s) VALUES\n' % ','.join('`%s`' % c for c in COLS))
        f.write(',\n'.join(lines) + ';\n')


HEADER = """-- MT2009_PLUS_YOHARA_MAPS1_V1: Opuszczona Twierdza (374, metin2_map_empirecastle) and Dongan (373,
-- metin2_map_eastplain_01) - the first maps of Yohara (cache/yohara/plan-mapy-yohary.md). GENERATED by
-- tools/yohara_maps/gen_ymaps_sql.py - do not edit, rerun it. Every start (apply.sh), idempotent: INSERT IGNORE - a
-- row the operator changed is kept. Every vnum checked free in our world.mob_proto (13 October 2026).
-- Source: Owsap v6.2.6 db/mob_proto.txt (the official vnums), recomputed into our r40250 columns:
--  * rank/type/battle_type as numbers; ai/race/immune flags only with our names (Owsap's UNK_IMMUNE_FLAG7 and the
--    outpost's OUTPOST dropped - the Troll Outpost 8625 is a plain Metin here);
--  * ScalePct, SungMa*, SungMaExp (sungma_mob_exp.txt has it), Resist{Fist,Claw,Bleeding,Dark,Ice,Earth}, Att*,
--    HitRange dropped; drop_item 0 (the drops: mob_drop_item.yohara_maps.txt).
--  * the element (wiki "(mrok)/(lod)/(ogien)") is not set here: zywioly_moby.sql (MT2009_PLUS_ELEMENTS_V1, run
--    after this file) gives it - rule h of gen_zywioly_moby.py (the owner, 13 October: as in the official game).
-- Balance (GUESS, to test): Owsap's levels 119-125, HP, damage (x4.0) and defence as they are; exp 0 as official -
-- experience only as champion experience on a Sung Ma map (sungma_mob_exp.txt). Our 301-304 bosses and Metins
-- carry half of Owsap's HP - halve max_hp here too if Yohara proves too slow.
-- A Metin's attack_speed/move_speed are the groups it calls (8067: 6194/6196, 8625: 6145/6151 - group.txt,
-- share step "Yohara: Opuszczona Twierdza, Dongan").
-- 10144: the portal at Twierdza's gate to Dongan (Owsap's 10107 "DongGwang"; our 10107 is Lodowa Grota).
SET NAMES utf8mb4;

"""

if __name__ == '__main__':
    main()
