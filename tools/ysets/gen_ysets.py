#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_ysets.py [--owsap DIR] [--gf DIR] [--wiki DIR]

MT2009_PLUS_YOHARA_SETS_V1: the Yohara gear and the equipment set effects (the owner, 14 October 2026 morning,
cache/yohara/decyzje.md: "Bronie/zbroje Mrocznego Smoka i wezy: TAK, razem z systemem zestawow - wytwarzanie,
kowale zestawow, bonusy zestawow, wszystko wg wiki").

  * the serpent weapons and armours (Bronie / Zbroje Wezowe, level 120, +0..+15): crafted at Statua Wezy (20807)
    from their "(wykon.)" piece (pl-wiki "Miecz Wezowy" ... "Wytwarzanie"), refined with Kamien Broni Pln. Wiatru /
    Kamien Wezowy (pl-wiki refine tables = Owsap refine_proto 720-749), three random base bonuses each (the pl-wiki
    templates BronieWezoweWartosci / ZbrojeWezoweWartosci: the bonus of each line and its value at every level);
  * the Dark Dragon weapons and the dragon armours (Bronie Smoka Mroku, Zbroje Smoka ..., level 96, +0..+15) of
    B. Smocza Skrz. (ciezka) (Glebie Polnocnego Wiatru), refined as the wiki says (Owsap refine_proto 551-585 - the
    awakening materials Plotno ... Wspanialy Kamien Chaosu, added here as materials);
  * the set effects (pl-wiki "Zestaw Ekwipunku", de-wiki "Set-Effekt", Owsap set_item_table.txt / cube.txt): the
    five set blacksmiths 20475-20479 in Port Nowego Kontynentu put a set (Swiety, Okazaly, Rycerski, Ksiazecy,
    Majestatyczny) on a weapon, armour or helmet of level 75+ refined to +7 or more; Statua Wojownika (20433) refines
    the set shards. Two or three worn pieces of the same set give its bonus.

The Lycan's pieces (Szpon / Pazur, Niebianski Plaszcz Wezowy, Zbroja Smoka Nieba) are left out: no Lycan here.

Writes (all GENERATED - edit this file, run it again):
  linux-port/docker/mariadb/playerbot/yohara_sets.sql   world.item_proto / refine_proto / mob_proto, player.item_yextra
  linux-port/docker/game/ysets/cube.ysets.txt           Statua Wezy, Statua Wojownika, the five set blacksmiths
  tools/ysets/yohara_sets.json                          the client's records (items, item_list, itemdesc, mobs)
  tools/ysets/ysets_random.json                         the random base bonuses (server-patches/ysets/gen_edits.py)
  client-patches/client-2.0.30/root/ysets_data.py       the same for the client's tooltip, the sets' names/bonuses

Example: python3 tools/ysets/gen_ysets.py
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, 'tools', 'yohara_items'))
import gen_yitems as Y  # noqa: E402  (the row writer, the engine's flag numbers)

SQL_OUT = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot', 'yohara_sets.sql')
CUBE_OUT = os.path.join(REPO, 'linux-port', 'docker', 'game', 'ysets', 'cube.ysets.txt')
JSON_OUT = os.path.join(HERE, 'yohara_sets.json')
RANDOM_OUT = os.path.join(HERE, 'ysets_random.json')
PY_OUT = os.path.join(REPO, 'client-patches', 'client-2.0.30', 'root', 'ysets_data.py')

M = 'MT2009_PLUS_YOHARA_SETS_V1'

# -- our engine's numbers -----------------------------------------------------------------------------------------
# applies are POINT_* numbers here (common/length.h; CItem::ModifyPoints -> PointChange(apply type))
P = dict(MAX_HP=6, ATT_SPEED=17, MOV_SPEED=19, CASTING_SPEED=21, HP_REGEN=32, STUN_PCT=38, SLOW_PCT=39,
         ATTBONUS_HUMAN=43, ATTBONUS_ANIMAL=44, ATTBONUS_ORC=45, ATTBONUS_MILGYO=46, ATTBONUS_UNDEAD=47,
         ATTBONUS_DEVIL=48, ATTBONUS_INSECT=49, ATTBONUS_DESERT=52, ATTBONUS_MONSTER=53, STEAL_HP=63, STEAL_SP=64,
         RESIST_MAGIC=77, POISON_REDUCE=81, EXP_DOUBLE_BONUS=83, MALL_EXPBONUS=116, SKILL_DAMAGE_BONUS=121,
         NORMAL_HIT_DAMAGE_BONUS=122, SKILL_DEFEND_BONUS=123, NORMAL_HIT_DEFEND_BONUS=124, MELEE_MAGIC_ATT_BONUS_PER=132,
         ATTBONUS_STONE=149, SUNGMA_STR=184, SUNGMA_HP=185, SUNGMA_MOVE=186, SUNGMA_IMMUNE=187)
TYPES = {'ITEM_WEAPON': 1, 'ITEM_ARMOR': 2, 'ITEM_MATERIAL': 5}
SUBTYPES = {'WEAPON_SWORD': 0, 'WEAPON_DAGGER': 1, 'WEAPON_BOW': 2, 'WEAPON_TWO_HANDED': 3, 'WEAPON_BELL': 4,
            'WEAPON_FAN': 5, 'ARMOR_BODY': 0, 'ARMOR_HEAD': 1, 'MATERIAL_LEATHER': 0}
ANTI = {'ANTI_FEMALE': 1, 'ANTI_MALE': 2, 'ANTI_MUSA': 4, 'ANTI_ASSASSIN': 8, 'ANTI_SURA': 16, 'ANTI_MUDANG': 32,
        'ANTI_WOLFMAN': 262144}
FLAGS = {'ITEM_TUNABLE': 1, 'ITEM_STACKABLE': 4}
WEAR = {'WEAR_BODY': 1, 'WEAR_HEAD': 2, 'WEAR_WEAPON': 16}
APPLY_NAMES = {'APPLY_ATT_SPEED': P['ATT_SPEED'], 'APPLY_SKILL_DAMAGE_BONUS': P['SKILL_DAMAGE_BONUS'],
               'APPLY_NORMAL_HIT_DEFEND_BONUS': P['NORMAL_HIT_DEFEND_BONUS'], 'APPLY_RESIST_MAGIC': P['RESIST_MAGIC'],
               'APPLY_MAX_HP': P['MAX_HP'], 'APPLY_NORMAL_HIT_DAMAGE_BONUS': P['NORMAL_HIT_DAMAGE_BONUS'],
               'APPLY_SKILL_DEFEND_BONUS': P['SKILL_DEFEND_BONUS']}

# -- the gear: (family base vnum, kind) ----------------------------------------------------------------------------
# kind: serpent weapon / serpent armour (random base bonuses) / dark dragon weapon / dragon armour (fixed ones)
SERPENT_WEAPONS = (360, 380, 1210, 2230, 3250, 5200, 7330)      # 6150 Szpon Wezowy: the Lycan's
SERPENT_ARMOURS = (21310, 21330, 21350, 21370)                  # 21390 Nieb. Plaszcz Wezowy: the Lycan's
DARK_WEAPONS = (320, 340, 1190, 2210, 3230, 5170, 7310)         # 6130 Pazur Smoka Mroku: the Lycan's
DRAGON_ARMOURS = (21210, 21230, 21250, 21270)                   # 21290 Zbroja Smoka Nieba: the Lycan's
FAMILIES = ([(b, 'sw') for b in SERPENT_WEAPONS] + [(b, 'sa') for b in SERPENT_ARMOURS] +
            [(b, 'dw') for b in DARK_WEAPONS] + [(b, 'da') for b in DRAGON_ARMOURS])
# the crafting pieces ("wykon.", tools/yohara_maps3 added them) -> the +0 piece; Statua Wezy (Owsap cube 20807 =
# pl-wiki "Miecz Wezowy" ... "Wytwarzanie": 10 Wzor Wezowy, 5 Kowadlo Pln. Wiatru / Jedwab Wezowy, 10 Jadeit Nocy,
# 5 Kamien Szlif. Pln. W. / Politura Wezowa, 10 000 000 Yang, 50%; the 100 Gaya: no Gaya here)
CRAFT = {376: 360, 396: 380, 1226: 1210, 2246: 2230, 3266: 3250, 5216: 5200, 7346: 7330,
         21326: 21310, 21346: 21330, 21366: 21350, 21386: 21370}
# awakening materials the dark dragon / dragon refine needs (Owsap refine_proto 551-585 = the pl-wiki refine tables)
AWAKENING = tuple(range(31122, 31139))
REFINE_SRC = {'sw': 720, 'sa': 735, 'dw': 571, 'da': 551}
REFINE_ID0 = 22600          # our refine_proto ids (22536 the highest one on 14 October 2026)

# -- the set effects ------------------------------------------------------------------------------------------------
# (value, the item name's prefix in the client, the bonus name, smith vnum, smith name, chance %, shard count,
#  shards (weapon, armour, helmet), Kamien Ksiezycowy needed, bonuses {pieces: [(point, value)]})
SETS = (
    (1, u'Święty', u'Święty Efekt Zestawu', 20475, u'Święty Kowal Zestawu', 50, 10, (39100, 39094, 39088), False,
     {2: [(P['MAX_HP'], 500), (P['MALL_EXPBONUS'], 5)], 3: [(P['MAX_HP'], 1500), (P['MALL_EXPBONUS'], 15)]}),
    (2, u'Okazały', u'Okazały Efekt Zestawu', 20476, u'Okazały Kowal Zestawu', 40, 30, (39101, 39095, 39089), False,
     {2: [(P['MAX_HP'], 500), (P['MOV_SPEED'], 3)], 3: [(P['MAX_HP'], 1500), (P['MOV_SPEED'], 7)]}),
    (3, u'Rycerski', u'Rycerski Efekt Zestawu', 20477, u'Rycerski Kowal Zestawu', 30, 50, (39102, 39096, 39090), False,
     {2: [(P['MAX_HP'], 500), (P['ATTBONUS_MONSTER'], 1)], 3: [(P['MAX_HP'], 1500), (P['ATTBONUS_MONSTER'], 5)]}),
    (4, u'Książęcy', u'Książęcy Efekt Zestawu', 20478, u'Książęcy Kowal Zestawu', 20, 30, (39105, 39104, 39103), False,
     {3: [(P['MAX_HP'], 2500), (P['MELEE_MAGIC_ATT_BONUS_PER'], 10), (P['MOV_SPEED'], 5)]}),
    (5, u'Majest.', u'Majestatyczny Efekt Zestawu', 20479, u'Majest. Kowal Zestawu', 15, 30, (39108, 39107, 39106), True,
     {3: [(P['MAX_HP'], 3500), (P['MELEE_MAGIC_ATT_BONUS_PER'], 15), (P['MOV_SPEED'], 7)]}),
)
SET_PROJECTS = (39112, 39111, 39110)          # Projekt Zestawu Broni, Zbroi, Helmu
SET_PARTS = (1, 2, 3)                         # set_part: 1 weapon, 2 armour, 3 helmet (server-patches/ysets)
SET_GOLD = 100000000                          # de-wiki / Owsap: 100 000 000 Yang (+ 500 Gaya: no Gaya here)
MOONSTONE = 30618                             # Kamien Ksiezycowy (the majestic set)
# Statua Wojownika: shard II from 200 shards I (500k / 1 mln / 3 mln), princely/majestic II from 10 of the one
# below (5 mln), 70% (pl-wiki "Zestaw Ekwipunku" - Uszlachetnianie = Owsap cube 20433)
SHARD_REFINE = [(39097, 39100, 200, 500000), (39091, 39094, 200, 500000), (39085, 39088, 200, 500000),
                (39098, 39101, 200, 1000000), (39092, 39095, 200, 1000000), (39086, 39089, 200, 1000000),
                (39099, 39102, 200, 3000000), (39093, 39096, 200, 3000000), (39087, 39090, 200, 3000000),
                (39102, 39105, 10, 5000000), (39096, 39104, 10, 5000000), (39090, 39103, 10, 5000000),
                (39105, 39108, 10, 5000000), (39104, 39107, 10, 5000000), (39103, 39106, 10, 5000000)]

# -- the random base bonuses of the serpent gear ---------------------------------------------------------------------
# pl-wiki templates "BronieWezoweWartosci" / "ZbrojeWezoweWartosci": three lines, each one bonus of its list with one
# of the value rows ("Wer." V1..V5) the wiki lists for every level +0..+15. Bonus names (wiki) -> our points; the
# ones our engine has no point for are left out (WIKI_SKIP).
WIKI_POINTS = {
    u'Średnie Obrażenia': 'NORMAL_HIT_DAMAGE_BONUS', u'Siła w walce z półludźmi': 'ATTBONUS_HUMAN',
    u'Siła w walce z diabłami': 'ATTBONUS_DEVIL', u'Silny przeciwko Zwierzętom': 'ATTBONUS_ANIMAL',
    u'Silny przeciwko Nieumarłym': 'ATTBONUS_UNDEAD', u'Silny przeciwko Orkom': 'ATTBONUS_ORC',
    u'Silny przeciwko Mistykom': 'ATTBONUS_MILGYO', u'Wola SungMa (SIŁA)': 'SUNGMA_STR',
    u'Wola SungMa (ODP)': 'SUNGMA_MOVE', u'Wola SungMa (WIT)': 'SUNGMA_HP', u'Wola SungMa (INT)': 'SUNGMA_IMMUNE',
    u'Szybkość Ataku': 'ATT_SPEED', u'Silny przeciwko Potworom': 'ATTBONUS_MONSTER',
    u'Silny przeciwko Insektom': 'ATTBONUS_INSECT', u'Obrażenia Umiejętności': 'SKILL_DAMAGE_BONUS',
    u'Siła w walce z kamieniami Metin': 'ATTBONUS_STONE', u'Siła w walce z potworami pustyni': 'ATTBONUS_DESERT',
    u'Szybkość Zaklęcia': 'CASTING_SPEED', u'Szansa na Bonus DOŚ': 'EXP_DOUBLE_BONUS',
    u'Szansa na kradzież PE': 'STEAL_SP', u'Szansa na Spowolnienie': 'SLOW_PCT', u'Szansa na Omdlenie': 'STUN_PCT',
    u'Max PŻ': 'MAX_HP', u'Odporność na Obrażenia': 'NORMAL_HIT_DEFEND_BONUS',
    u'Odporność na Obrażenia Umiejętności': 'SKILL_DEFEND_BONUS', u'Szansa na odzyskanie PŻ': 'HP_REGEN',
    u'Odporność na Trucizny': 'POISON_REDUCE', u'Odp. na Magię': 'RESIST_MAGIC', u'Odporność na Magię': 'RESIST_MAGIC',
    u'Szybkość Ruchu': 'MOV_SPEED', u'% obrażeń będzie dodanych do PŻ': 'STEAL_HP',
    u'% obrażeń będzie dodanych do PE': 'STEAL_SP'}
# no point for these here: Zodiac monsters (ATTBONUS_CZ), Precyzja, bleeding (the Lycan's), fall resistance as a %,
# resistance to monsters
WIKI_SKIP = (u'Siła w walce z potworami Zodiaku', u'Precyzja', u'Odporność na Atak Krwawienia',
             u'Odporność na Upadek', u'Odp. na atak potworów', u'Odporność na atak potworów')
# the wiki's evident typos (a value lower than the level below it): (template, bonus, row, level) -> value
WIKI_FIX = {('w', u'Szybkość Ataku', 2, 7): 20}


def parse_template(text, kind):
    """[(line 1..3, [(wiki name, [[16 values] per row]])])]"""
    out = []
    parts = re.split(r'===\s*(\d)\.\s*[^=]*===', text)
    for k in range(1, len(parts), 2):
        line = int(parts[k])
        rows = []
        for row in re.split(r'\n\|-(?:[ \t]+align="center")?[ \t]*(?=\n)', parts[k + 1])[1:]:
            m = re.search(r"'''\[\[([^\]|]+)(?:\|([^\]]*))?\]\]\s*:?\s*'''|\{\{ti\|([^}|]+)\}\}", row)
            if not m:
                continue
            name = (m.group(3) or m.group(2) or m.group(1)).strip()
            rest = row[m.end():].replace('||', '\n|')
            vals = []
            for ln in rest.split('\n'):
                if not ln.startswith('|'):
                    continue
                c = ln.rsplit('|', 1)[1].strip()
                if not c or 'V' in c or not re.match(r'^[-+0-9%<br>\s]+$', c):
                    continue
                vals.append([int(x.replace('%', '').replace('+', '').strip()) for x in c.split('<br>') if x.strip()])
            vals = vals[:16]
            assert len(vals) == 16, (kind, name, len(vals), vals)
            nrow = max(len(v) for v in vals)
            table = []
            for r in range(nrow):
                # a level the wiki gives fewer rows (all rows equal there) repeats its last one
                table.append([v[r] if r < len(v) else v[-1] for v in vals])
            for (t, n, r, lv), fix in WIKI_FIX.items():
                if t == kind and n == name:
                    table[r][lv] = fix
            rows.append((name, table))
        out.append((line, rows))
    return out


def random_groups(wiki):
    groups = {}
    for kind, fn in (('w', 'Szablon:BronieWężoweWartości.raw'), ('a', 'Szablon:ZbrojeWężoweWartości.raw')):
        lines = parse_template(open(os.path.join(wiki, fn), encoding='utf-8').read(), kind)
        assert [l for l, _r in lines] == [1, 2, 3], (kind, [l for l, _r in lines])
        g = []
        for line, rows in lines:
            opts = []
            for name, table in rows:
                if name in WIKI_SKIP:
                    continue
                assert name in WIKI_POINTS, (kind, line, name)
                for r in table:
                    for lv in range(1, 16):
                        assert r[lv] >= r[lv - 1], (kind, name, r)
                opts.append(dict(name=name, point=P[WIKI_POINTS[name]], rows=table))
            assert 0 < len(opts) <= 15 and all(len(o['rows']) <= 15 for o in opts), (kind, line)
            g.append(opts)
        groups[kind] = g
    return groups


# -- reading the sources -------------------------------------------------------------------------------------------
def read_tsv(path, enc='cp1250'):
    with open(path, 'rb') as f:
        return [l.decode(enc, 'replace').rstrip('\r\n').split('\t') for l in f]


def flags(s, table):
    v = 0
    for t in (x.strip() for x in s.split('|')):
        if t in ('NONE', '', '0'):
            continue
        if t not in table:
            raise SystemExit('unknown flag %s' % t)
        v |= table[t]
    return v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--owsap', default='/opt/metin2/cache/owsap')
    ap.add_argument('--gf', default='/opt/metin2/cache/gf/Gameforge_26.1.11/_client')
    ap.add_argument('--wiki', default='/opt/metin2/cache/yohara/wiki/sets')
    a = ap.parse_args()
    rows = read_tsv(os.path.join(a.owsap, 'Server/Server/db/item_proto.txt'))
    head = rows[0]
    proto = dict((int(r[0]), dict(zip(head, r))) for r in rows[1:] if r and r[0].isdigit())
    desc = {}
    for r in read_tsv(os.path.join(a.owsap, 'Client/Client/pack/locale/locale/pl/itemdesc.txt')):
        if len(r) >= 2 and r[0].strip().isdigit():
            desc[int(r[0])] = (r[1].strip(), r[2].strip() if len(r) > 2 else '')
    gf_list = {}
    for r in read_tsv(os.path.join(a.gf, 'shared/common/item_list.txt')):
        if len(r) >= 3 and r[0].strip().isdigit():
            gf_list[int(r[0])] = [x.strip() for x in r[1:]]
    refine = {}
    with open(os.path.join(a.owsap, 'Server/Server/db/data/player.sql'), encoding='latin-1') as f:
        for m in re.finditer(r'INSERT INTO `refine_proto` VALUES \(([^)]*)\);', f.read()):
            p = [int(x) for x in m.group(1).split(',')]
            refine[p[0]] = p

    # refine_proto: Owsap's 15 rows of each kind under our ids
    refines, rid_of = [], {}
    for kind, src in sorted(REFINE_SRC.items(), key=lambda x: x[1]):
        for lv in range(15):
            r = refine[src + lv]
            rid = REFINE_ID0 + len(refines)
            rid_of[(kind, lv)] = rid
            mats = [(r[1 + 2 * i], r[2 + 2 * i]) for i in range(5) if r[1 + 2 * i]]
            refines.append(dict(id=rid, mats=mats, cost=r[11], prob=r[14], src=src + lv))

    items = []
    for base, kind in FAMILIES:
        for lv in range(16):
            v = base + lv
            o = proto[v]
            pl, text = desc[v]
            assert pl.endswith('+%d' % lv) and len(pl.encode('cp1250')) <= 24, (v, pl)
            typ, sub = TYPES[o['Type']], SUBTYPES[o['SubType']]
            applies = []
            for i in range(3):
                t, val = o['ApplyType%d' % i], int(o['ApplyValue%d' % i])
                if t in ('APPLY_NONE', 'APPLY_RANDOM'):
                    applies.append((0, 0))     # APPLY_RANDOM: the item's own lines (server-patches/ysets)
                else:
                    applies.append((APPLY_NAMES[t], val))
            if kind in ('sw', 'sa'):
                assert all(o['ApplyType%d' % i] == 'APPLY_RANDOM' for i in range(3)), v
            values = [int(o['Value%d' % i]) for i in range(6)]
            if typ == 2:
                values[3] = base            # the body's shape: the family's own msm group (tools/ysets, client)
            gl = gf_list[v]
            items.append(dict(
                vnum=v, family=base, kind=kind, level=lv, name=Y.ascii_name(pl), locale_name=pl,
                type=typ, subtype=sub, stack=1, weight=0, size=int(o['Size']),
                antiflag=flags(o['AntiFlags'], ANTI), flag=flags(o['Flags'], FLAGS),
                wearflag=flags(o['WearFlags'], WEAR), gold=int(o['ShopBuyPrice']),
                shop_buy_price=int(o['ShopSellPrice']), refined_vnum=v + 1 if lv < 15 else 0,
                refine_set=rid_of[(kind, lv)] if lv < 15 else 0, magic_pct=int(o['AlterToMagicItemPercent']),
                specular=int(o['Specular']), socket_pct=int(o['GainSocketPercent']), addon_type=0,
                limittype0=1, limitvalue0=int(o['LimitValue0']), limittype1=0, limitvalue1=0,
                applytype0=applies[0][0], applyvalue0=applies[0][1], applytype1=applies[1][0],
                applyvalue1=applies[1][1], applytype2=applies[2][0], applyvalue2=applies[2][1],
                **dict(('value%d' % i, values[i]) for i in range(6)),
                icon=gl[1], model=gl[2] if len(gl) > 2 else '', list_type=gl[0], desc=text))
            assert o['LimitType0'] == 'LEVEL' and o['LimitType1'] == 'LIMIT_NONE', v
            assert int(o['RefinedVnum']) == (v + 1 if lv < 15 else 0), v
    for v in AWAKENING:
        o = proto[v]
        pl, text = desc[v]
        items.append(dict(
            vnum=v, family=0, kind='mat', level=0, name=Y.ascii_name(pl), locale_name=pl, type=5, subtype=0,
            stack=200, weight=0, size=1, antiflag=0, flag=FLAGS['ITEM_STACKABLE'], wearflag=0,
            gold=int(o['ShopBuyPrice']), shop_buy_price=int(o['ShopSellPrice']), refined_vnum=0, refine_set=0,
            magic_pct=0, specular=0, socket_pct=0, addon_type=0, limittype0=0, limitvalue0=0, limittype1=0,
            limitvalue1=0, applytype0=0, applyvalue0=0, applytype1=0, applyvalue1=0, applytype2=0, applyvalue2=0,
            value0=0, value1=0, value2=0, value3=0, value4=0, value5=0,
            icon=gf_list[v][1], model='', list_type='ETC',
            desc=text + ' (Przebudzenie bossów - nie ma go jeszcze na serwerze.)'))
    byv = dict((i['vnum'], i) for i in items)
    assert len(byv) == len(items)

    groups = random_groups(a.wiki)
    write_sql(items, refines)
    write_cube()
    write_json(items, groups)
    write_random(groups)
    write_py(groups)
    print('items %d (%s), refine rows %d, cube recipes %d' % (
        len(items), ', '.join('%s %d' % (k, sum(1 for i in items if i['kind'] == k))
                              for k in ('sw', 'sa', 'dw', 'da', 'mat')),
        len(refines), len(CRAFT) + 2 + len(SHARD_REFINE) + 3 * len(SETS)))
    for kind, g in sorted(groups.items()):
        print('random %s: %s' % (kind, ' | '.join(', '.join('%s(%d)' % (o['name'], len(o['rows'])) for o in l)
                                                  for l in g)))


COLS = Y.COLS


def write_sql(items, refines):
    L = ['-- %s: the Yohara gear and the set effects (the owner, 14 October 2026). GENERATED by' % M,
         '-- tools/ysets/gen_ysets.py - do not edit, rerun it. Every start (apply.sh), idempotent (INSERT IGNORE / IF NOT',
         '-- EXISTS). Source: Owsap v6.2.6 db/item_proto.txt + refine_proto (the official vnums and numbers; = the pl-wiki',
         '-- pages of every piece), the Polish names of its Polish client; every vnum free in our world (14 October 2026).',
         '--   serpent weapons 360/380/1210/2230/3250/5200/7330 +0..+15, level 120 - three random base bonuses each',
         '--     (server-patches/ysets: player.item_yextra), refine 10..80x Kamien Broni Pln. Wiatru(+) ... (Owsap 720-734)',
         '--   serpent armours 21310/21330/21350/21370 +0..+15, level 120 - the same, Kamien Wezowy(+) (Owsap 735-749)',
         '--   dark dragon weapons 320/340/1190/2210/3230/5170/7310 +0..+15, level 96 (Owsap 571-585)',
         '--   dragon armours 21210/21230/21250/21270 +0..+15, level 96 (Owsap 551-565)',
         '--   31122-31138 the awakening materials of the last two refines (Plotno ... Wspanialy Kamien Chaosu): no',
         '--     awakened boss here yet - they wait for one (their description says so)',
         '-- The armours\' value3 is the family\'s own body shape (the client\'s msm group, tools/ysets).',
         '-- refine_proto %d-%d. The Lycan\'s pieces are left out (no Lycan).' % (refines[0]['id'], refines[-1]['id']),
         'SET NAMES utf8mb4;',
         'INSERT IGNORE INTO world.item_proto (%s) VALUES' % ','.join('`%s`' % c for c in COLS),
         ',\n'.join(Y.sqlrow(i) for i in items) + ';',
         'INSERT IGNORE INTO world.refine_proto (id,vnum0,count0,vnum1,count1,vnum2,count2,vnum3,count3,vnum4,count4,'
         'cost,src_vnum,result_vnum,prob) VALUES']
    rr = []
    for r in refines:
        m = r['mats'] + [(0, 0)] * (5 - len(r['mats']))
        rr.append('(%d,%s,%d,0,0,%d)' % (r['id'], ','.join('%d,%d' % x for x in m), r['cost'], r['prob']))
    L.append(',\n'.join(rr) + ';')
    # the set blacksmiths: copies of Statua Wojownika's row (shipdefense.sql 20433, an NPC), the blacksmith's look
    # (client npclist 20475-20479 -> "blacksmith"); Owsap mob_proto 20475-20479 are NPCs of level 1 alike
    L.append('-- the five set blacksmiths of Port Nowego Kontynentu (Owsap 20475-20479, pl-wiki names)')
    L.append('INSERT IGNORE INTO world.mob_proto (vnum,name,locale_name,rank,type,battle_type,level,size,ai_flag,'
             'mount_capacity,setRaceFlag,setImmuneFlag,empire,folder,on_click,st,dx,ht,iq,damage_min,damage_max,'
             'max_hp,regen_cycle,regen_percent,gold_min,gold_max,exp,def,attack_speed,move_speed,aggressive_hp_pct,'
             'aggressive_sight,attack_range,drop_item,resurrection_vnum,enchant_curse,enchant_slow,enchant_poison,'
             'enchant_stun,enchant_critical,enchant_penetrate,enchant_fire,enchant_root,resist_sword,resist_twohand,'
             'resist_dagger,resist_bell,resist_fan,resist_bow,resist_fire,resist_elect,resist_magic,resist_wind,'
             'resist_poison,dam_multiply,summon,drain_sp,mob_color,polymorph_item,skill_level0,skill_vnum0,'
             'skill_level1,skill_vnum1,skill_level2,skill_vnum2,skill_level3,skill_vnum3,skill_level4,skill_vnum4,'
             'sp_berserk,sp_stoneskin,sp_godspeed,sp_deathblow,sp_revive) VALUES')
    mobs = []
    for sv, _pre, _bn, npc, nm, *_r in SETS:
        mobs.append("(%d,'Set Blacksmith',_cp1250 X'%s',2,1,0,1,'NONE','NOMOVE',0,'','STUN,SLOW,TERROR',0,'',2,0,0,0,0,"
                    "0,0,120,3,1,0,0,10,4,100,100,0,2000,150,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.0,0,0,0,0,0,"
                    "0,0,0,0,0,0,0,0,0,0,0,0,0,0)" % (npc, nm.encode('cp1250').hex().upper()))
    L.append(',\n'.join(mobs) + ';')
    # the items' own data the engine keeps beside player.item (server-patches/ysets): the set (bits 0-3) and the three
    # random base bonuses of a serpent piece (bits 8-31, a byte each: bonus 1-15 | row << 4)
    L.append('-- the set and the random base bonuses of an item (server-patches/ysets, by item id; a row of an item that')
    L.append('-- no longer exists does nothing)')
    L.append('CREATE TABLE IF NOT EXISTS player.item_yextra (id INT UNSIGNED NOT NULL PRIMARY KEY, '
             'yextra INT UNSIGNED NOT NULL DEFAULT 0) ENGINE=InnoDB;')
    with open(SQL_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')


def write_cube():
    L = ['# %s: GENERATED by tools/ysets/gen_ysets.py - do not edit. Appended to the share\'s cube.txt by the' % M,
         '# Dockerfile (quest ysets opens each window). Sources: Owsap cube.txt (npc 20807, 20433, 20475-20479) = the',
         '# pl-wiki ("Miecz Wezowy" ... "Wytwarzanie", "Zestaw Ekwipunku") / de-wiki ("Set-Effekt"); their Gaya cost',
         '# ("gem") is left out - no Gaya here.', '']
    L.append('# -- Statua Wezy (20807): the serpent weapons and armours from their "(wykon.)" piece')
    for piece, result in sorted(CRAFT.items()):
        armour = result >= 20000
        L += ['section', 'npc\t20807', 'item\t%d\t1' % piece, 'item\t31257\t10',
              'item\t%d\t5' % (31258 if armour else 31259), 'item\t50662\t10',
              'item\t%d\t5' % (31262 if armour else 31263), 'reward\t%d\t1' % result, 'gold\t10000000',
              'percent\t50', 'end', '']
    L.append('# -- Statua Wezy: Pyl Wezowy from 30 Wzor Wezowy or 30 Jedwab Wezowy')
    for v in (31257, 31258):
        L += ['section', 'npc\t20807', 'item\t%d\t30' % v, 'reward\t70428\t1', 'gold\t50000', 'percent\t100', 'end', '']
    L.append('# -- Statua Wojownika (20433): the set shards II, 70%')
    for src, dst, n, gold in SHARD_REFINE:
        L += ['section', 'npc\t20433', 'item\t%d\t%d' % (src, n), 'reward\t%d\t1' % dst, 'gold\t%d' % gold,
              'percent\t70', 'end', '']
    L.append('# -- the set blacksmiths (20475-20479): a set on a weapon / armour / helmet of level 75+ at +7 or more')
    L.append('#    (set_value / set_part: server-patches/ysets cube.cpp - the piece itself is the cube\'s other item, kept')
    L.append('#    on failure; the reward line is what the result list shows, nothing is given). 100 000 000 Yang.')
    for sv, _pre, bn, npc, nm, pct, shards, shard_v, moon, _b in SETS:
        for part, shard, proj in zip(SET_PARTS, shard_v, SET_PROJECTS):
            L += ['section', 'npc\t%d' % npc, 'item\t%d\t%d' % (shard, shards), 'item\t%d\t1' % proj]
            if moon:
                L.append('item\t%d\t1' % MOONSTONE)
            L += ['reward\t%d\t1' % proj, 'gold\t%d' % SET_GOLD, 'percent\t%d' % pct, 'set_value\t%d' % sv,
                  'set_part\t%d' % part, 'end', '']
    os.makedirs(os.path.dirname(CUBE_OUT), exist_ok=True)
    with open(CUBE_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L))


def write_json(items, groups):
    keys = ('vnum', 'name', 'locale_name', 'type', 'subtype', 'stack', 'weight', 'size', 'antiflag', 'flag',
            'wearflag', 'gold', 'shop_buy_price', 'refined_vnum', 'refine_set', 'magic_pct', 'specular', 'socket_pct',
            'limittype0', 'limitvalue0', 'limittype1', 'limitvalue1', 'applytype0', 'applyvalue0', 'applytype1',
            'applyvalue1', 'applytype2', 'applyvalue2', 'value0', 'value1', 'value2', 'value3', 'value4', 'value5')
    il = {}
    for i in items:
        line = '%d\t%s\t%s' % (i['vnum'], i['list_type'], i['icon'])
        if i['model']:
            line += '\t' + i['model']
        il[str(i['vnum'])] = line
    out = {'items': [dict((k, i[k]) for k in keys) for i in items],
           'families': dict((str(b), k) for b, k in FAMILIES),
           'item_list': il,
           'itemdesc': dict((str(i['vnum']), '%d\t%s\t%s' % (i['vnum'], i['locale_name'], i['desc'].replace('\t', ' ')))
                            for i in items),
           'mobs': dict((str(npc), dict(name=nm, folder='blacksmith', x=x, y=y))
                        for (sv, _p, _b, npc, nm, *_r), (x, y) in zip(SETS, ((258, 568), (257, 569), (256, 570),
                                                                             (255, 571), (254, 572)))),
           # the materials the yohara_items* batches added "without a use yet" that have one now: their client
           # description loses "(Na razie bez zastosowania ...)" (tools/ysets client patch)
           'now_used': sorted(set([31233, 31234, 31235, 31236, 31237, 31239, 31240, 31241, 31242, 31243, 31257, 31258,
                                   31259, 31262, 31263, 30616, 30617, 30618, 50662, 50663] + list(CRAFT) +
                                  list(range(39085, 39109)) + [39110, 39111, 39112]))}
    with open(JSON_OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=0)
        f.write('\n')


def write_random(groups):
    fam = dict([(b, 'w') for b in SERPENT_WEAPONS] + [(b, 'a') for b in SERPENT_ARMOURS])
    out = {'families': dict((str(b), k) for b, k in fam.items()),
           'groups': dict((k, [[dict(point=o['point'], name=o['name'], rows=o['rows']) for o in line] for line in g])
                          for k, g in groups.items()),
           'sets': [dict(value=s[0], prefix=s[1], name=s[2], smith=s[3], bonuses=dict((str(n), b) for n, b in s[9].items()))
                    for s in SETS]}
    with open(RANDOM_OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=0)
        f.write('\n')


def write_py(groups):
    """the client's copy (Python 2, cp1250 source like every root file): the families, the random bonus tables, the
    sets' names and bonuses"""
    fam = dict([(b, 'w') for b in SERPENT_WEAPONS] + [(b, 'a') for b in SERPENT_ARMOURS])
    L = ['# -*- coding: cp1250 -*-',
         '# %s: GENERATED by tools/ysets/gen_ysets.py - do not edit. The serpent gear\'s random base' % M,
         '# bonuses (pl-wiki BronieWezoweWartosci / ZbrojeWezoweWartosci) and the set effects (pl-wiki "Zestaw',
         '# Ekwipunku"); the server\'s copy: server-patches/ysets. uitooltip.py / ysets.py read it.',
         '',
         '# family base vnum -> "w" (weapon) / "a" (armour); a piece is base + its refine level (0..15)',
         'RANDOM_FAMILIES = {%s}' % ', '.join('%d: "%s"' % (b, k) for b, k in sorted(fam.items())),
         '',
         '# kind -> [line 1, 2, 3] -> [(point, ((+0..+15) per row))] - a line\'s byte: bonus index + 1 | row << 4',
         'RANDOM_GROUPS = {']
    for k in sorted(groups):
        L.append('\t"%s": (' % k)
        for line in groups[k]:
            L.append('\t\t(')
            for o in line:
                L.append('\t\t\t(%d, (%s)),' % (o['point'], ', '.join('(%s)' % ', '.join(str(x) for x in r)
                                                                     for r in o['rows'])))
            L.append('\t\t),')
        L.append('\t),')
    L.append('}')
    L.append('')
    L.append('# set value -> (prefix of the item\'s name, the effect\'s name, {pieces: ((point, value), ...)})')
    L.append('SETS = {')
    for s in SETS:
        L.append('\t%d: ("%s", "%s", {%s}),' % (
            s[0], s[1].encode('cp1250').decode('latin-1'), s[2].encode('cp1250').decode('latin-1'),
            ', '.join('%d: (%s)' % (n, ''.join('(%d, %d), ' % pv for pv in b)) for n, b in sorted(s[9].items()))))
    L.append('}')
    L.append('')
    with open(PY_OUT, 'wb') as f:
        f.write('\n'.join(L).encode('latin-1'))


if __name__ == '__main__':
    main()
