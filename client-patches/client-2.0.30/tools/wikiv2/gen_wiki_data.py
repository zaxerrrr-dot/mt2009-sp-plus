# -*- coding: utf-8 -*-
"""MT2009_PLUS_WIKI_V2_DATA - the in-game wiki's data (client root uiwiki.py / the exe's "wikipedia" module) generated
from OUR server's own tables, so the wiki can be rebuilt every release.

Run on vps1 (host python3; needs docker for the test DB and the running test game container):

    python3 client-patches/client-2.0.30/tools/wikiv2/gen_wiki_data.py            # write the four files
    python3 client-patches/client-2.0.30/tools/wikiv2/gen_wiki_data.py --check    # build again, compare, exit 1 on a diff
  options: --share DIR      the game's locale dir (default: docker cp mt2009plustest-game:/opt/metin2/share/locale/poland
                            into a temp dir, removed afterwards)
           --out DIR        default: client-patches/client-2.0.30/wikiv2/locale/common/wiki (next to this tools dir)
           --item-rate N    the mob item rate (%) the chances are computed at (default 100 = the BASE chance; the test
                            server's own event flag mob_item is printed for reference)

Sources (all what the RUNNING test server loads):
  * world DB (test stack, docker exec mt2009plustest-db): item_proto, mob_proto, refine_proto, shop + shop_item,
    shop_special(+_proto), crafting_proto, quest_reward_proto; player.quest dwPID 0 event flags (rare drop switches,
    m2_alchemy_off, m2_sash_off, no_drop_metin_stone, mob_item).
  * the game container's share/locale/poland: mob_drop_item.txt, drop_item_group.txt, special_item_group.txt,
    etc_drop_item.txt, common_drop_item.txt, cube.txt, group.txt, group_group.txt, drop_wiki.txt, dungeon_info.txt,
    map/index + map/<dir>/{regen,boss,stone,npc}.txt, quest/libs/crafting/crafting_data.lua, quest/object (which NPC
    opens which crafting window).
  * the game's CONFIG (channel1/game1): MOONLIGHT_CHEST_PERMILLE, MOONLIGHT_CHEST_STONE_PERMILLE,
    DRAGON_COIN_STONE_PERMILLE, DRAGON_COIN_BOSS_PERMILLE, BLESSING_SCROLL_STONE_PERMILLE.

WHAT A CHANCE MEANS (MD / CC lines, hundred-millionths: 100000000 = 100%):
  MD - per kill, for a killer AT THE MONSTER'S OWN LEVEL, at the mob item rate --item-rate (default 100%: the base
       chance), no premium, thief gloves, events or party. A port of ITEM_MANAGER::GetDropWikiRows (item_manager.cpp,
       MT2009_PLUS_DROP_WIKI_V1/V2) as the test tree has it: drop_item_group + mob_drop_item "drop" rows (pct * delta /
       100 / 4 000 000, a special group "sNNN" by its weights), the "kill" pool (40000*delta/kill_drop/4 000 000, then
       one entry by weight), the "limit" rows (pct per million), etc_drop_item for the proto's drop_item, a Metin's
       spirit stone (aStoneDrop, grade portions, 16 kinds), and the world's extras (skill book 50300 from a Metin,
       Blessing Scroll 25040 from a Metin lv 15-99, Moonlight chest 50011, Kupon SM 80014 (a Sung Ma field boss x2),
       Cor Draconis 50255 (Metin 20%, boss 80%, per-mob rules), Delikatne Sukno 80019 for bosses (count by the
       mob's level), rank fruit 80050-80054 30%, element talismans from bosses 5% / Metins 2%), plus drop_wiki.txt's
       quest/engine drops. One item = one row: several draws merge as 1-(1-a)(1-b), counts min..max.
  CC - per opening: GetDropWikiChests / DropWikiAddChestGroup - one entry by weight, each entry at its own percent
       for a Type Pct group, a "Pick N" group by 20000 fixed xorshift trials, groups inside groups by their share.
  The common drop (common_drop_item.txt) goes by the KILLER's level and the monster's rank, not by monster: it is an
  SRC note per item (level range + chance range per kill at the base rate).

Item filter for EQ: a chain is listed when its +0 has a name and any item of the chain has a source (drop, chest,
recipe/crafting, shop, quest reward, refine from an obtainable item, drop_wiki.txt) - unused/GM test items are left out.
The output is sorted and deterministic; text is CP1250.
"""
import argparse
import collections
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_C30 = os.path.normpath(os.path.join(HERE, '..', '..'))
DEFAULT_OUT = os.path.join(REPO_C30, 'wikiv2', 'locale', 'common', 'wiki')
GAME = 'mt2009plustest-game'
DB = 'mt2009plustest-db'

# ----------------------------------------------------------------------------------------------- server constants
RANGE = 4000000.0
MOB_RANK_BOSS = 4
CHAR_TYPE_MONSTER, CHAR_TYPE_NPC, CHAR_TYPE_STONE = 0, 1, 2
SIG_NORMAL, SIG_PCT, SIG_QUEST, SIG_SPECIAL = 0, 1, 2, 3
MOB_GROUP = 7          # CSpecialItemGroup::MOB_GROUP - every give-type below it is no item
MAX_DEPTH = 4          # PLAYERBOT_MOB_PREVIEW_MAX_DEPTH
MAX_ROWS = 400         # MT2009_PLUS_DROP_WIKI_MAX_ROWS
TANAKA, TANAKA_EAR = 5001, 30202
METIN_STONES = [28030, 28031, 28032, 28033, 28034, 28035, 28036, 28037, 28038, 28039, 28040, 28041, 28042, 28043,
                28044, 28045]   # MT2009_PLUS_ANTI_RESIST_MAGIC is defined
STONE_DROP = {  # aStoneDrop: mob -> (pct, (+0..+4))
    8005: (60, (30, 30, 30, 9, 1)), 8006: (60, (28, 29, 31, 11, 1)), 8007: (60, (24, 29, 32, 13, 2)),
    8008: (60, (22, 28, 33, 15, 2)), 8009: (60, (21, 27, 33, 17, 2)), 8010: (60, (18, 26, 34, 20, 2)),
    8011: (60, (14, 26, 35, 22, 3)), 8012: (60, (10, 26, 37, 24, 3)), 8013: (60, (2, 26, 40, 29, 3)),
    8014: (60, (0, 26, 41, 30, 3)),
}
STONE_LEVEL_MAX = 4
# Mt2009PlusRareMobRuleForRace(race, -1): race -> (corCount, corChance, sashChance); map-bound rules are not taken
RARE_RULES = {9701: (0, 0, 0), 9702: (0, 0, 0), 9684: (0, 0, 0), 9682: (5, 15, 15)}
CHAMPION_BOSSES = {6691, 6698, 6699, 6705, 6706, 6716, 6717, 6723, 6724, 6730, 6731, 6789, 6797}
MISSION_NO_DROP = {6692}
BLESS_MIN, BLESS_MAX = 15, 99
SASH_CLOTH = 80019
# playerbot_rank_points.h
FRUITS = [(80050, 53), (80051, 74), (80052, 99), (80053, 109), (80054, 1000)]
FRUIT_GRAPES = {3090, 3091, 3190, 3191, 3290, 3291, 3390, 3391, 3490, 3491, 3590, 3591, 3595, 3596, 3690, 3691, 3790,
                3791, 3890, 3891, 3911, 3912, 3913, 8051, 8052, 8053, 8054, 8055, 8056}
FRUIT_PINEAPPLES = {6407, 6408, 6192, 8059, 8061}
FRUIT_PERCENT = 30
# server race flag bits (common/length.h; the DB's setRaceFlag+0 is the same bitmask)
RF_ATT_ELEC, RF_ATT_FIRE, RF_ATT_ICE, RF_ATT_TEMPLE, RF_ATT_EARTH, RF_ATT_DARK = 1 << 11, 1 << 12, 1 << 13, 1 << 14, 1 << 15, 1 << 16
TALISMANS = [(RF_ATT_FIRE, 94000), (RF_ATT_ELEC, 94250), (RF_ATT_ICE, 94500), (RF_ATT_TEMPLE, 94750),
             (RF_ATT_EARTH, 95000), (RF_ATT_DARK, 95250)]
# aiPercentByDeltaLev(_ForBoss)[15] (killer at the mob's own level) = 100 in both tables
DELTA_SAME_LEVEL = 100

# item types (common/item_length.h)
IT_WEAPON, IT_ARMOR, IT_USE, IT_COSTUME, IT_RING, IT_BELT, IT_PET = 1, 2, 3, 28, 33, 34, 37
IT_GIFTBOX = 23
WEARABLE_TYPES = (IT_WEAPON, IT_ARMOR, IT_COSTUME, IT_RING, IT_BELT)
WEAPON_ARROW, WEAPON_QUIVER = 6, 9
ARMOR_SUB_CAT = {0: 1, 1: 2, 2: 3, 3: 5, 4: 7, 5: 6, 6: 4, 7: 9, 8: 10}   # body, head, shield, wrist, foots, neck, ear, pendant, glove
COSTUME_CAT = {4: 0, 0: 1, 1: 2, 3: 3, 2: 5, 5: 7}                      # weapon skin, body, hair, sash, mount, aura
ANTI_WARRIOR, ANTI_ASSASSIN, ANTI_SURA, ANTI_SHAMAN = 1 << 2, 1 << 3, 1 << 4, 1 << 5
LIMIT_LEVEL = 1

# event chests: the special_item_group parts of these event files (linux-port/docker/game/special_item_group.<x>.txt)
EVENT_GROUP_FILES = ('catchking', 'flower', 'yutnori', 'rumi', 'halloween', 'goblin', 'fishpuzzle')

# Polish map names: the old drop wiki's (uidropwiki.py MAP_NAMES), then the Monster Cards' (monstercard_data.py
# MAPY), the dungeon panel's (dungeon_info.txt), then these.
MAP_NAMES_EXTRA = {
    114: u'Pole Bitwy', 64: u'Dolina Seungryong', 67: u'Las Duchów Lungsam', 367: u'Obrona Statku',
    368: u'Port (Obrona Statku)', 373: u'Dongan', 374: u'Opuszczona Twierdza', 376: u'Seoganland', 377: u'Namgan',
    378: u'Królestwo Żywiołów I', 379: u'Królestwo Żywiołów II', 380: u'Królestwo Żywiołów III',
    381: u'Płaskowyż Sił Natury', 385: u'Przełęcz Yilad', 386: u'Wieża Sung Mahi (wejście)', 387: u'Wieża Sung Mahi',
    388: u'Wąwóz Północnego Wiatru', 389: u'Rozpadlina Dusz', 390: u'Świątynia Węży (1. poziom)',
    391: u'Świątynia Węży', 393: u'Schronienie Północnego Wiatru', 394: u'Zejście Północnego Wiatru',
    395: u'Głębie Północnego Wiatru', 396: u'Loch Anglar', 397: u'Labirynt Iluzji', 420: u'Leże Białego Smoka',
    200: u'Budowa Gildii', 250: u'Studio',
    118: u'Pole Bitwy - Ogniste Wzgórze 1', 119: u'Pole Bitwy - Ogniste Wzgórze 2', 120: u'Pole Bitwy - Ogniste Wzgórze 3',
    121: u'Pole Bitwy - Śnieg', 122: u'Pole Bitwy - Śnieżna Przełęcz 1', 123: u'Pole Bitwy - Śnieżna Przełęcz 2',
    124: u'Pole Bitwy - Śnieżna Przełęcz 3', 125: u'Pole Bitwy - Pustynia', 126: u'Pole Bitwy - Pustynne Wzgórze 1',
    127: u'Pole Bitwy - Pustynne Wzgórze 2', 128: u'Pole Bitwy - Pustynne Wzgórze 3',
}

# crafting NPC labels (menu order = this order, then every other crafting NPC by vnum)
NPC_LABELS = [
    (20016, u'Kowal - wytwarzanie'), (20001, u'Alchemik - rudy i kamienie'), (20017, u'Pasy, runy, wody'),
    (20022, u'Eliksiry i rosy'), (20018, u'Zioła, soki, szaty aury'), (9009, u'Wędki i soki'),
    (20008, u'Kucharz'), (20090, u'Półdemon - wytwarzanie'), (20041, u'Wytwarzanie'), (20364, u'Wytwarzanie'),
    (20349, u'Przedmioty dla konia'), (11001, u'Strzały'), (11003, u'Strzały'), (11005, u'Strzały'),
    (20402, u'Czarna stal'), (60003, u'Szarfy (Delikatne Sukno)'), (20011, u'Owoce rangi'),
    (20383, u'Ekwipunek i kamienie'), (20413, u'Ekwipunek ognia i mroku'), (20378, u'Pancerze'),
    (20812, u'Pancerze'), (20421, u'Hełmy smoków'), (20473, u'Broń Smoka'), (20474, u'Zbroje i hełmy Smoka'),
    (20433, u'Odłamki zestawów'), (20475, u'Projekty zestawów'), (20476, u'Projekty zestawów'),
    (20477, u'Projekty zestawów'), (20478, u'Projekty zestawów'), (20479, u'Projekty zestawów'),
    (20807, u'Ekwipunek wężowy'), (20823, u'Jadeit, rękawice, kamienie mocy'), (20470, u'Kamienie przebudzenia'),
    (20850, u'Talizmany'), (20438, u'Wymiany Zodiaku'),
] + [(v, u'Przetapianie (budynek gildii)') for v in range(20060, 20073)] + [
]

BANNED = ('metin2', 'gameforge', 'oficjaln', 'tieru')


# ----------------------------------------------------------------------------------------------- input helpers
def sh(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, **kw).stdout


def sql(query):
    """rows of a query against the test DB (utf8mb4 text, tab-separated)"""
    out = subprocess.run(
        ['docker', 'exec', '-e', 'Q=' + query, DB, 'sh', '-c',
         'mariadb -uroot -p"$MARIADB_ROOT_PASSWORD" --default-character-set=utf8mb4 -B -N -e "$Q"'],
        check=True, capture_output=True).stdout
    return [line.split('\t') for line in out.decode('utf-8', 'replace').split('\n') if line]


def ival(s, default=0):
    try:
        return int(float(s))
    except (TypeError, ValueError):
        return default


def str_to_number(s):
    """the server's str_to_number for an integer: leading digits (a non-number is 0)"""
    m = re.match(r'\s*([-+]?\d+)', s or '')
    return int(m.group(1)) if m else 0


def read_text(path):
    with open(path, 'rb') as f:
        return f.read().decode('cp1250', 'replace')


_TOKEN = re.compile(r'"([^"]*)"|(\S+)')


def text_nodes(path):
    """CTextFileLoader-like: [(name, {lowerkey: [tokens...] (first occurrence)})] for every 'Group name { ... }'"""
    nodes = []
    cur = None
    name = None
    depth = 0
    for raw in read_text(path).replace('\r', '').split('\n'):
        toks = [a if a else b for a, b in _TOKEN.findall(raw)]   # "a quoted name" is one token
        if not toks:
            continue
        if toks[0].startswith('#') or toks[0].startswith('//'):
            continue
        if toks[0].lower() == 'group' and depth == 0:
            name = toks[1] if len(toks) > 1 else ''
            cur = None
            if '{' in toks[2:]:
                cur = collections.OrderedDict()
                depth = 1
            continue
        if toks[0] == '{':
            if depth == 0:
                cur = collections.OrderedDict()
            depth += 1
            continue
        if toks[0] == '}':
            depth -= 1
            if depth == 0 and cur is not None:
                nodes.append((name, cur))
                cur = None
            continue
        if cur is not None and depth == 1:
            key = toks[0].lower()
            vals = toks[1:]
            if '--' in vals:
                vals = vals[:vals.index('--')]
            vals = [v for v in vals if not v.startswith('--')] if vals and any(v.startswith('--') for v in vals) else vals
            if key not in cur:
                cur[key] = vals
    return nodes


# ----------------------------------------------------------------------------------------------- the generator
class Gen(object):
    def __init__(self, share, item_rate, data_root=None):
        self.share = share
        self.data_root = data_root
        self.item_rate = item_rate
        self.warn = []

    # ---------------------------------------------------------------- loading
    def load(self):
        self.load_db()
        self.load_config()
        self.load_tables()
        self.load_places()

    def load_db(self):
        self.items = {}
        for r in sql('SELECT vnum, locale_name, type, subtype, antiflag, refined_vnum, refine_set, gold, flag, '
                     'limittype0, limitvalue0, limittype1, limitvalue1, value0, value1, value2, value3, value4, value5 '
                     'FROM world.item_proto ORDER BY vnum'):
            v = int(r[0])
            self.items[v] = dict(vnum=v, name=r[1], type=ival(r[2]), sub=ival(r[3]), anti=ival(r[4]),
                                 refined=ival(r[5]), rset=ival(r[6]), gold=ival(r[7]), flag=ival(r[8]),
                                 limits=[(ival(r[9]), ival(r[10])), (ival(r[11]), ival(r[12]))],
                                 values=[ival(x) for x in r[13:19]])
        self.mobs = {}
        for r in sql('SELECT vnum, locale_name, `rank`, type, level, max_hp, exp, damage_min, damage_max, def, gold_min, '
                     'gold_max, setRaceFlag+0, setImmuneFlag+0, ai_flag+0, drop_item, resist_sword, resist_twohand, '
                     'resist_dagger, resist_bell, resist_fan, resist_bow, resist_fire, resist_elect, resist_magic, '
                     'resist_wind, resist_poison FROM world.mob_proto ORDER BY vnum'):
            v = int(r[0])
            self.mobs[v] = dict(vnum=v, name=r[1], rank=ival(r[2]), type=ival(r[3]), level=ival(r[4]), hp=ival(r[5]),
                                exp=ival(r[6]), dmin=ival(r[7]), dmax=ival(r[8]), dfn=ival(r[9]), gmin=ival(r[10]),
                                gmax=ival(r[11]), race=ival(r[12]), immune=ival(r[13]), ai=ival(r[14]),
                                drop_item=ival(r[15]), resists=[ival(x) for x in r[16:27]])
        self.refine = {}
        for r in sql('SELECT id, cost, prob, vnum0, count0, vnum1, count1, vnum2, count2, vnum3, count3, vnum4, count4 '
                     'FROM world.refine_proto'):
            mats = []
            for i in range(5):
                vn, c = ival(r[3 + 2 * i]), ival(r[4 + 2 * i])
                if vn and c > 0:
                    mats.append((vn, c))
            self.refine[int(r[0])] = (ival(r[1]), ival(r[2]), mats)
        self.shops = []   # (npc, item, count)
        for r in sql('SELECT shop.npc_vnum, shop_item.item_vnum, shop_item.count FROM world.shop JOIN world.shop_item '
                     'ON shop.vnum = shop_item.shop_vnum'):
            self.shops.append((ival(r[0]), ival(r[1]), ival(r[2])))
        self.special_shops = []   # (npc, item, count, price_type, price)
        try:
            for r in sql('SELECT s.vnum, p.item_vnum, p.count, p.price_type, p.price FROM world.shop_special s JOIN '
                         'world.shop_special_proto p ON p.vnum = s.item_vnum'):
                self.special_shops.append((ival(r[0]), ival(r[1]), ival(r[2]), r[3], ival(r[4])))
        except subprocess.CalledProcessError:
            self.warn.append('shop_special not read')
        self.crafting = {}
        for r in sql('SELECT vnum, item_vnum, count, price, chance, recipe FROM world.crafting_proto'):
            mats = []
            parts = [p for p in r[5].split(',') if p.strip()]
            for i in range(0, len(parts) - 1, 2):
                vn, c = ival(parts[i]), ival(parts[i + 1])
                if vn and c > 0:
                    mats.append((vn, c))
            self.crafting[int(r[0])] = (ival(r[1]), ival(r[2]), ival(r[3]), ival(r[4]), mats)
        self.quest_rewards = []   # (quest, vnum, count)
        for r in sql('SELECT quest_name, items, warrior_items, assassin_items, sura_items, shaman_items '
                     'FROM world.quest_reward_proto'):
            for col in r[1:6]:
                parts = [p for p in col.split(',') if p.strip()]
                for i in range(0, len(parts) - 1, 2):
                    if ival(parts[i]):
                        self.quest_rewards.append((r[0], ival(parts[i]), ival(parts[i + 1])))
        self.itemshop = set()
        try:
            for r in sql('SELECT DISTINCT vnum FROM itemshop3.shop WHERE available IS NULL OR available <> 0'):
                self.itemshop.add(ival(r[0]))
        except subprocess.CalledProcessError:
            self.warn.append('itemshop3.shop not read')
        self.flags = {}
        for r in sql('SELECT szName, lValue FROM player.quest WHERE dwPID = 0'):
            self.flags[r[0]] = ival(r[1])

    def flag(self, name):
        return self.flags.get(name, 0)

    def load_config(self):
        self.cfg = {}
        try:
            text = sh(['docker', 'exec', GAME, 'cat', '/opt/metin2/var/channel1/game1/CONFIG']).decode('latin-1')
        except subprocess.CalledProcessError:
            text = ''
            self.warn.append('CONFIG not read - permilles 0')
        for line in text.split('\n'):
            if ':' in line:
                k, v = line.split(':', 1)
                self.cfg[k.strip().upper()] = v.strip()
        c = lambda k: ival(self.cfg.get(k, '0'))
        self.moon = c('MOONLIGHT_CHEST_PERMILLE')
        self.moon_stone = c('MOONLIGHT_CHEST_STONE_PERMILLE')
        self.coin_stone = c('DRAGON_COIN_STONE_PERMILLE')
        self.coin_boss = c('DRAGON_COIN_BOSS_PERMILLE')
        self.bless_stone = c('BLESSING_SCROLL_STONE_PERMILLE')

    def p(self, *parts):
        return os.path.join(self.share, *parts)

    def load_tables(self):
        # special_item_group.txt (first group of a vnum wins: map emplace)
        self.groups = {}       # vnum -> dict(type, pick, items[(vnum,count,prob,special)])
        self.quest_groups = {}
        for name, node in text_nodes(self.p('special_item_group.txt')):
            if 'vnum' not in node or not node['vnum']:
                continue
            gv = str_to_number(node['vnum'][0])
            typ = SIG_NORMAL
            st = node.get('type', [''])[0].lower() if node.get('type') else ''
            if st == 'pct':
                typ = SIG_PCT
            elif st == 'quest':
                typ = SIG_QUEST
            elif st == 'special':
                typ = SIG_SPECIAL
            if st == 'attr':
                continue
            pick = 0
            if 'pick' in node and node['pick']:
                pick = max(0, str_to_number(node['pick'][0])) if typ == SIG_NORMAL else 0
            items = []
            k = 1
            while str(k) in node:
                t = node[str(k)]
                k += 1
                if len(t) < 3:
                    break
                nm = t[0]
                special = False
                if nm in ('exp', 'mob', 'slow', 'drain_hp', 'poison', 'bleeding', 'group', 'gold'):
                    vn = {'gold': 1, 'exp': 2, 'mob': 3, 'slow': 4, 'drain_hp': 5, 'poison': 6, 'group': 7,
                          'bleeding': 8}[nm]
                elif nm.startswith('s'):
                    special = True
                    vn = str_to_number(nm[1:])
                else:
                    vn = str_to_number(nm)
                cnt = str_to_number(t[1])
                prob = str_to_number(t[2])
                if not prob:
                    continue
                items.append((vn, cnt, prob, special))
            g = dict(vnum=gv, type=typ, pick=pick, items=items)
            target = self.quest_groups if typ == SIG_QUEST else self.groups
            if gv not in target:
                target[gv] = g
        # drop_item_group.txt then mob_drop_item.txt
        self.dropgroup = collections.OrderedDict()   # mob -> [(vnum, pct, count, special, builtin)]
        self.killgroup = {}    # mob -> (kill_drop, [(vnum, count, partpct)])
        self.limitgroup = {}   # mob -> (level_limit, [(vnum, pct, count)])
        if os.path.exists(self.p('drop_item_group.txt')):
            for name, node in text_nodes(self.p('drop_item_group.txt')):
                if 'vnum' not in node or 'mob' not in node:
                    continue
                mob = str_to_number(node['mob'][0])
                rows = self.dropgroup.setdefault(mob, [])
                k = 1
                while str(k) in node:
                    t = node[str(k)]
                    k += 1
                    vn = str_to_number(t[0])
                    pct = int(10000.0 * float(t[1])) if len(t) > 1 else 0
                    cnt = str_to_number(t[2]) if len(t) > 2 else 1
                    rows.append((vn, pct, cnt, False, False))
        for name, node in text_nodes(self.p('mob_drop_item.txt')):
            if 'type' not in node or 'mob' not in node:
                continue
            typ = node['type'][0].lower() if node['type'] else ''
            mob = str_to_number(node['mob'][0])
            if typ == 'kill':
                kd = str_to_number(node.get('kill_drop', ['0'])[0])
            else:
                kd = 1
            if kd == 0:
                continue
            rows = []
            k = 1
            while str(k) in node:
                rows.append(node[str(k)])
                k += 1
            if typ == 'kill':
                its = []
                for t in rows:
                    its.append((str_to_number(t[0]), str_to_number(t[1]), str_to_number(t[2])))
                if mob not in self.killgroup:
                    self.killgroup[mob] = (kd, its)
            elif typ == 'drop':
                lst = self.dropgroup.setdefault(mob, [])
                builtin = not name.startswith('MT2009_panel_')
                for t in rows:
                    special = t[0].startswith('s')
                    vn = str_to_number(t[0][1:] if special else t[0])
                    lst.append((vn, int(10000.0 * float(t[2])), str_to_number(t[1]), special, builtin))
            elif typ == 'limit':
                its = []
                for t in rows:
                    its.append((str_to_number(t[0]), int(10000.0 * float(t[2])), str_to_number(t[1])))
                if mob not in self.limitgroup:
                    self.limitgroup[mob] = (str_to_number(node.get('level_limit', ['0'])[0]), its)
        # etc_drop_item.txt: vnum -> pct*10000 (last line wins)
        self.etc = {}
        for line in read_text(self.p('etc_drop_item.txt')).replace('\r', '').split('\n'):
            if '\t' not in line:
                continue
            name, prob = line.rsplit('\t', 1)
            try:
                fp = float(prob)
            except ValueError:
                continue
            if not name or fp == 0.0:
                continue
            self.etc[str_to_number(name)] = int(fp * 10000.0)
        # mob groups for the regens
        self.mobgroup = {}
        for name, node in text_nodes(self.p('group.txt')):
            if 'vnum' not in node:
                continue
            gv = str_to_number(node['vnum'][0])
            members = []
            if 'leader' in node and len(node['leader']) >= 2:
                members.append(str_to_number(node['leader'][1]))
            k = 1
            while str(k) in node:
                t = node[str(k)]
                k += 1
                if len(t) >= 2:
                    members.append(str_to_number(t[1]))
            self.mobgroup.setdefault(gv, members)
        self.groupgroup = {}
        for name, node in text_nodes(self.p('group_group.txt')):
            if 'vnum' not in node:
                continue
            gv = str_to_number(node['vnum'][0])
            gl = []
            k = 1
            while str(k) in node:
                t = node[str(k)]
                k += 1
                if t:
                    gl.append(str_to_number(t[0]))
            self.groupgroup.setdefault(gv, gl)

    # ---------------------------------------------------------------- places, dungeons, drop_wiki.txt
    def load_places(self):
        self.map_index = {}
        for line in read_text(self.p('map', 'index')).split('\n'):
            t = line.split()
            if len(t) >= 2 and t[0].isdigit():
                self.map_index.setdefault(int(t[0]), t[1])
        self.places = collections.defaultdict(dict)   # mob -> {map: kind}
        self.npc_pos = collections.defaultdict(list)  # npc -> [(map, x, y)]
        self.dungeon_name = {}
        self.dungeon_drops = []
        for line in read_text(self.p('dungeon_info.txt')).split('\n'):
            t = line.split()
            if len(t) >= 19 and t[0] == 'dungeon':
                m = ival(t[2])
                if m <= 0:
                    continue
                self.dungeon_name[m] = t[17].replace('_', ' ')
                if ival(t[12]):
                    self.add_place(ival(t[12]), m, 2)
        self.file_drops = []
        self.exchanges = []
        for line in read_text(self.p('drop_wiki.txt')).split('\n'):
            t = line.split()
            if not t or t[0].startswith('#'):
                continue
            if t[0] == 'place' and len(t) >= 3:
                m = ival(t[1])
                if m <= 0:
                    continue
                if len(t) >= 4:
                    self.dungeon_name.setdefault(m, t[3].replace('_', ' '))
                rng = re.match(r'^(\d+)(?:-(\d+))?$', t[2])
                if rng:
                    a = int(rng.group(1))
                    b = int(rng.group(2) or a)
                    for race in range(a, b + 1):
                        self.add_place(race, m, 1)
                else:
                    self.read_regen_path(t[2], m)
            elif t[0] == 'drop' and len(t) >= 6:
                self.file_drops.append((ival(t[1]), ival(t[2]), ival(t[3]), ival(t[4]), float(t[5]) / 100.0))
            elif t[0] == 'exchange' and len(t) >= 5:
                self.exchanges.append((ival(t[1]), ival(t[2]), ival(t[3]), t[4]))
        for m in sorted(self.map_index):
            d = self.p('map', self.map_index[m])
            dungeon = m in self.dungeon_name
            for f in ('regen.txt', 'boss.txt', 'stone.txt'):
                self.read_regen(os.path.join(d, f), m, 1 if dungeon else 0)
            for f in ('npc.txt', 'regen.txt'):
                self.read_npcs(os.path.join(d, f), m)

    def is_monster(self, race):
        mob = self.mobs.get(race)
        return mob is not None and mob['type'] in (CHAR_TYPE_MONSTER, CHAR_TYPE_STONE)

    def add_place(self, race, m, kind):
        if not self.is_monster(race):
            return
        pl = self.places[race]
        if m in pl:
            pl[m] = max(pl[m], kind)
        elif len(pl) < 12:
            pl[m] = kind

    def read_regen(self, path, m, kind):
        if not os.path.isfile(path):
            return
        for line in read_text(path).split('\n'):
            w = line.split()
            if len(w) < 11 or w[0].startswith('//'):
                continue
            typ = w[0][0]
            vn = str_to_number(w[10])
            if not vn:
                continue
            if typ in 'ms':
                self.add_place(vn, m, kind)
            elif typ == 'g':
                for mem in self.mobgroup.get(vn, []):
                    self.add_place(mem, m, kind)
            elif typ == 'r':
                for gv in self.groupgroup.get(vn, []):
                    for mem in self.mobgroup.get(gv, []):
                        self.add_place(mem, m, kind)

    def read_regen_path(self, rel, m):
        """a drop_wiki.txt regen path (relative to the cores' dir, which holds share's data/): a dir (its .txt two
        levels down), a file, or the start of file names in a dir"""
        base = os.path.normpath(os.path.join(self.data_root or '', rel[5:] if rel.startswith('data/') else rel))
        if self.data_root and os.path.isdir(base):
            for dp, dn, fn in sorted(os.walk(base)):
                if dp[len(base):].count(os.sep) > 2:
                    continue
                for f in sorted(fn):
                    if f.endswith('.txt'):
                        self.read_regen(os.path.join(dp, f), m, 1)
            return
        if self.data_root and os.path.isfile(base):
            self.read_regen(base, m, 1)
            return
        parent, prefix = os.path.split(base)
        if self.data_root and os.path.isdir(parent):
            hit = [f for f in sorted(os.listdir(parent)) if f.startswith(prefix)]
            for f in hit:
                self.read_regen(os.path.join(parent, f), m, 1)
            if hit:
                return
        self.warn.append('drop_wiki place path not found: %s' % rel)

    def read_npcs(self, path, m):
        if not os.path.isfile(path):
            return
        for line in read_text(path).split('\n'):
            w = line.split()
            if len(w) < 11 or w[0] != 'm':
                continue
            vn = str_to_number(w[10])
            mob = self.mobs.get(vn)
            if not mob or mob['type'] == CHAR_TYPE_MONSTER or mob['type'] == CHAR_TYPE_STONE:
                continue
            pos = (m, ival(w[1]), ival(w[2]))
            if pos not in self.npc_pos[vn]:
                self.npc_pos[vn].append(pos)

    # ---------------------------------------------------------------- drops (GetDropWikiRows port)
    @staticmethod
    def add(rows, items, vnum, count, chance):
        if vnum <= MOB_GROUP or count <= 0 or chance <= 0.0:
            return
        if vnum not in items:
            return
        chance = min(chance, 1.0)
        r = rows.get(vnum)
        if r:
            r[2] = 1.0 - (1.0 - r[2]) * (1.0 - chance)
            r[0] = min(r[0], count)
            r[1] = max(r[1], count)
            return
        if len(rows) < MAX_ROWS:
            rows[vnum] = [count, count, chance]

    def add_special_group(self, rows, gv, chance, depth):
        if depth > MAX_DEPTH or chance <= 0.0:
            return
        g = self.groups.get(gv)
        if not g or not g['items']:
            return
        total = float(sum(x[2] for x in g['items']))
        if total <= 0:
            return
        for vn, cnt, prob, special in g['items']:
            share = prob / total
            if special:
                self.add_special_group(rows, vn, chance * share, depth + 1)
            else:
                self.add(rows, self.items, vn, cnt, chance * share)

    def rare_off(self, kind, stone):
        names = {'sm': ('m2_sm_boss_off', 'm2_sm_metin_off'), 'sash': ('m2_sash_boss_off', 'm2_sash_metin_off'),
                 'cor': ('m2_cor_boss_off', 'm2_cor_metin_off')}
        return self.flag(names[kind][1 if stone else 0]) != 0

    def rare_kind(self, vnum):
        if 80014 <= vnum <= 80018:
            return 'sm'
        if vnum == 50252 or 50255 <= vnum <= 50260:
            return 'cor'
        if vnum == SASH_CLOTH:
            return 'sash'
        it = self.items.get(vnum)
        if it and it['type'] == IT_COSTUME and it['sub'] == 3:
            return 'sash'
        return None

    def mob_rows(self, race):
        rows = collections.OrderedDict()
        mob = self.mobs.get(race)
        if not mob:
            return rows
        stone = mob['type'] == CHAR_TYPE_STONE
        if mob['type'] != CHAR_TYPE_MONSTER and not stone:
            return rows
        if race in (6091, 6191) or race in MISSION_NO_DROP:
            return rows
        if race == TANAKA:
            self.add(rows, self.items, TANAKA_EAR, 1, 1.0)
            return rows
        level = mob['level']
        boss = mob['rank'] >= MOB_RANK_BOSS
        delta = DELTA_SAME_LEVEL * self.item_rate // 100
        for vn, pct, cnt, special, builtin in self.dropgroup.get(race, []):
            if not special and builtin and (stone or boss):
                k = self.rare_kind(vn)
                if k and self.rare_off(k, stone):
                    continue
            chance = float(pct) * delta / 100.0 / RANGE
            if special:
                self.add_special_group(rows, vn, chance, 0)
            else:
                self.add(rows, self.items, vn, cnt, chance)
        kg = self.killgroup.get(race)
        if kg and kg[1] and kg[0] > 0:
            pool = float((40000 * delta) // kg[0]) / RANGE
            total = float(sum(x[2] for x in kg[1]))
            if total > 0:
                for vn, cnt, part in kg[1]:
                    self.add(rows, self.items, vn, cnt, pool * part / total)
        lg = self.limitgroup.get(race)
        if lg:
            for vn, pct, cnt in lg[1]:
                self.add(rows, self.items, vn, cnt, pct / 1000000.0)
        if mob['drop_item'] and mob['drop_item'] in self.etc:
            self.add(rows, self.items, mob['drop_item'], 1, float(self.etc[mob['drop_item']]) * delta / 100.0 / RANGE)
        if stone and not self.flag('no_drop_metin_stone') and race in STONE_DROP:
            pct, grades = STONE_DROP[race]
            drop = float(pct) * delta * 400.0 / RANGE
            left = 100
            for grade in range(STONE_LEVEL_MAX + 1):
                portion = left
                if grade < STONE_LEVEL_MAX:
                    portion = min(max(0, grades[grade]), left)
                    left -= portion
                if portion <= 0:
                    continue
                for st in METIN_STONES:
                    self.add(rows, self.items, st + 100 * grade, 1, drop / len(METIN_STONES) * portion / 100.0)
        # rank fruit (RankPointsWikiFruitRace)
        if stone or boss:
            fruit = None
            if race in FRUIT_GRAPES:
                fruit = 80052
            elif race in FRUIT_PINEAPPLES:
                fruit = 80054
            else:
                fruit = FRUITS[-1][0]
                for fv, top in FRUITS:
                    if level <= top:
                        fruit = fv
                        break
            self.add(rows, self.items, fruit, 1, FRUIT_PERCENT / 100.0)
            if fruit in rows:
                rows[fruit][1] = max(rows[fruit][1], 2)
        dungeon_mob = 6001 <= race <= 6199 or race in (8057, 8058)
        if not dungeon_mob:
            if stone:
                self.add(rows, self.items, 50300, 1, 1.0)
                if self.bless_stone > 0 and BLESS_MIN <= level <= BLESS_MAX:
                    self.add(rows, self.items, 25040, 1, self.bless_stone / 1000.0)
            cp = self.moon_stone if stone else self.moon
            if cp > 0:
                self.add(rows, self.items, 50011, 1, cp / 1000.0)
            coin = self.coin_stone if stone else (self.coin_boss * (2 if race in CHAMPION_BOSSES else 1) if boss else 0)
            if coin > 0 and not self.rare_off('sm', stone):
                self.add(rows, self.items, 80014, 1, coin / 1000.0)
            rule = RARE_RULES.get(race)
            if self.flag('m2_alchemy_off') == 0 and not self.rare_off('cor', stone):
                cor = 20 if stone else (80 if boss else 0)
                if rule:
                    cor = rule[1]
                if cor > 0:
                    self.add(rows, self.items, 50255, rule[0] if rule and rule[0] > 1 else 1, cor / 100.0)
            if boss and self.flag('m2_sash_off') == 0 and not self.rare_off('sash', stone):
                sash = 15 if stone else 80
                if rule:
                    sash = rule[2]
                if sash > 0:
                    cloth = 2 if level < 50 else (5 if level < 75 else 10)
                    self.add(rows, self.items, SASH_CLOTH, cloth, sash / 100.0)
            if self.moon <= 0 and self.moon_stone <= 0:
                rows.pop(50011, None)
        if stone or boss:
            for flag, tv in TALISMANS:
                if mob['race'] & flag:
                    self.add(rows, self.items, tv, 1, 0.02 if stone else 0.05)
        return rows

    # ---------------------------------------------------------------- chests (GetDropWikiChests port)
    def add_chest_group(self, rows, g, chance, depth):
        if not g or not g['items'] or depth > MAX_DEPTH or chance <= 0.0:
            return
        items = g['items']
        pct = g['type'] == SIG_PCT
        total = float(sum(x[2] for x in items))
        if not pct and total <= 0:
            return
        if not pct and g['pick'] > 0:
            n = len(items)
            hits = [0.0] * n
            seed = (2463534242 ^ g['vnum']) & 0xFFFFFFFF
            trials = 20000
            base_w = [max(0, x[2]) for x in items]
            for _ in range(trials):
                w = list(base_w)
                left = sum(w)
                k = 0
                while k < g['pick'] and left > 0:
                    seed ^= (seed << 13) & 0xFFFFFFFF
                    seed ^= seed >> 17
                    seed ^= (seed << 5) & 0xFFFFFFFF
                    r = seed % left + 1
                    i = 0
                    while i + 1 < n:
                        if r <= w[i]:
                            break
                        r -= w[i]
                        i += 1
                    hits[i] += 1.0
                    left -= w[i]
                    w[i] = 0
                    k += 1
            for i, (vn, cnt, prob, special) in enumerate(items):
                share = hits[i] / trials
                if share <= 0:
                    continue
                if special:
                    self.add_chest_group(rows, self.groups.get(vn), chance * share, depth + 1)
                else:
                    self.add(rows, self.items, vn, cnt, chance * share)
            return
        for vn, cnt, prob, special in items:
            share = prob / 100.0 if pct else prob / total
            if special:
                self.add_chest_group(rows, self.groups.get(vn), chance * share, depth + 1)
            else:
                self.add(rows, self.items, vn, cnt, chance * share)

    # ---------------------------------------------------------------- crafting
    def load_crafting(self):
        """recipes: [(npcs tuple, kind, result, count, gold, percent, mats str)]"""
        recipes = []
        # cube.txt (Cube_load: '#' lines skipped, tokens by whitespace)
        cur = None
        for line in read_text(self.p('cube.txt')).replace('\r', '').split('\n'):
            if line.startswith('#'):
                continue
            t = line.split()
            if not t:
                continue
            v1 = str_to_number(t[1]) if len(t) > 1 else 0
            v2 = str_to_number(t[2]) if len(t) > 2 else 0
            if t[0] == 'section':
                cur = dict(npc=[], item=[], reward=[], percent=0, gold=0, gaya=0)
            elif cur is None:
                continue
            elif t[0] == 'npc':
                cur['npc'].append(v1)
            elif t[0] == 'item':
                cur['item'].append((v1, v2))
            elif t[0] == 'reward':
                cur['reward'].append((v1, v2))
            elif t[0] == 'percent':
                cur['percent'] = v1
            elif t[0] == 'gold':
                cur['gold'] = v1
            elif t[0] == 'gaya':
                cur['gaya'] = v1
            elif t[0] == 'end':
                c = cur
                cur = None
                if not c['reward'] or not c['npc'] or not c['item']:
                    continue
                rv, rc = c['reward'][0]
                mats = [(v, n) for v, n in c['item'] if v and n > 0]
                if rv not in self.items or not mats:
                    continue
                recipes.append((tuple(c['npc']), 0, rv, rc, c['gold'], c['percent'],
                                ','.join('%d:%d' % m for m in mats)))
        # crafting windows (crafting_proto + crafting_data.lua + the quests that open them)
        lua = read_text(self.p('quest', 'libs', 'crafting', 'crafting_data.lua'))
        lua = re.sub(r'--\[\[.*?\]\]', '', lua, flags=re.S)
        lua = re.sub(r'--[^\n]*', '', lua)
        consts = dict((m.group(1), int(m.group(2))) for m in re.finditer(r'^\s*([A-Z_][A-Z0-9_]*)\s*=\s*(\d+)\s*$', lua, re.M))
        windows = {}
        body = lua[lua.find('crafting_data = {'):]
        for m in re.finditer(r'\[\s*([A-Z_0-9]+)\s*\]\s*=\s*\{([^}]*)\}', body):
            key = m.group(1)
            wid = consts.get(key, ival(key, -1))
            windows[wid] = [int(x) for x in re.findall(r'\d+', m.group(2))]
        win_npcs = collections.defaultdict(set)
        objdir = self.p('quest', 'object')
        if os.path.isdir(objdir):
            for npc in os.listdir(objdir):
                if not npc.isdigit():
                    continue
                chat = os.path.join(objdir, npc, 'chat')
                if not os.path.isdir(chat):
                    continue
                for f in os.listdir(chat):
                    if not f.endswith('.script'):
                        continue
                    text = read_text(os.path.join(chat, f))
                    for m in re.finditer(r'crafting\s*\.\s*open\s*\(\s*([^)]*?)\s*\)', text):
                        arg = m.group(1).replace(' ', '')
                        if arg.startswith('npc.get_vnum('):
                            wid = int(npc)
                        elif arg.isdigit():
                            wid = int(arg)
                        else:
                            wid = consts.get(arg, -1)
                        if wid in windows:
                            win_npcs[wid].add(int(npc))
        for wid in sorted(windows):
            npcs = tuple(sorted(win_npcs.get(wid, ())))
            if not npcs:
                continue
            for rid in windows[wid]:
                r = self.crafting.get(rid)
                if not r:
                    continue
                res, cnt, price, chance, mats = r
                if res not in self.items or not mats:
                    continue
                recipes.append((npcs, 0, res, cnt, price, chance, ','.join('%d:%d' % m for m in mats)))
        # drop_wiki.txt exchanges (kind 1); a material "a-b:n" is n of any one of a..b
        for npc, res, cnt, mats in self.exchanges:
            if res in self.items:
                recipes.append(((npc,), 1, res, cnt, 0, 100, mats))
        return sorted(set(recipes))

    # ---------------------------------------------------------------- build everything
    def build(self):
        items = self.items
        # --- mob drops
        self.md = {}
        for race in sorted(self.mobs):
            rows = self.mob_rows(race)
            if rows:
                self.md[race] = rows
        for mob, it, cmin, cmax, ch in self.file_drops:
            if it not in items or mob not in self.mobs:
                continue
            rows = self.md.setdefault(mob, collections.OrderedDict())
            r = rows.get(it)
            ch = min(1.0, ch)
            if r:
                r[2] = 1.0 - (1.0 - r[2]) * (1.0 - ch)
                r[0] = min(r[0], cmin)
                r[1] = max(r[1], cmax)
            else:
                rows[it] = [cmin, cmax, ch]
        # --- chests
        self.cc = {}
        for gv in sorted(self.groups):
            g = self.groups[gv]
            if g['type'] == SIG_SPECIAL or gv not in items or not g['items']:
                continue
            rows = collections.OrderedDict()
            self.add_chest_group(rows, g, 1.0, 0)
            if rows:
                self.cc[gv] = rows
        # --- crafting
        self.recipes = self.load_crafting()
        # --- refine steps / chains
        self.rs = {}
        for v in sorted(items):
            it = items[v]
            if not it['refined'] or not it['rset'] or it['refined'] == v or it['refined'] not in items:
                continue
            rf = self.refine.get(it['rset'])
            if not rf:
                continue
            self.rs[v] = (it['refined'], rf[0], rf[1], rf[2])
        # a chain is one item's +0..+N: a step into an item of another base name (a +9 that the smith turns into the
        # next weapon's +0) is a refine step (RS) but starts a new chain
        nxt = dict((v, s[0]) for v, s in self.rs.items() if base_name(items[v]['name']) == base_name(items[s[0]]['name']))
        has_prev = set(nxt.values())
        self.chains = []
        self.chain_of = {}
        for v in sorted(nxt):
            if v in has_prev:
                continue
            chain = [v]
            seen = {v}
            while chain[-1] in nxt and nxt[chain[-1]] not in seen:
                chain.append(nxt[chain[-1]])
                seen.add(chain[-1])
            self.chains.append(chain)
            for x in chain:
                self.chain_of.setdefault(x, chain)
        # --- obtainable items
        src = set()
        for rows in self.md.values():
            src.update(rows)
        for rows in self.cc.values():
            src.update(rows)
        for r in self.recipes:
            src.add(r[2])
        for npc, it, cnt in self.shops:
            if npc in self.mobs:    # the npc_vnum 0 shops are GM / beta-test shops
                src.add(it)
        for s in self.special_shops:
            if s[0] in self.mobs:
                src.add(s[1])
        for q in self.quest_rewards:
            src.add(q[1])
        src.update(self.itemshop)
        self.common = self.common_drop()
        src.update(self.common)
        changed = True
        while changed:
            changed = False
            for v, s in self.rs.items():
                if v in src and s[0] not in src:
                    src.add(s[0])
                    changed = True
        self.obtainable = src

    def common_drop(self):
        """item -> [(rank, lvStart, lvEnd, chance at the base delta)]"""
        out = collections.defaultdict(list)
        for line in read_text(self.p('common_drop_item.txt')).replace('\r', '').split('\n'):
            if not line:
                continue
            f = line.split('\t')
            for rank in range(4):
                c = f[rank * 6: rank * 6 + 6]
                if len(c) < 6:
                    break
                vn = str_to_number(c[4])
                if vn <= 1 or vn not in self.items:
                    continue
                lv0, lv1 = str_to_number(c[1]), str_to_number(c[2])
                if lv0 == 0:
                    continue
                try:
                    pct = int(float(c[3]) * 10000.0)
                except ValueError:
                    continue
                out[vn].append((rank, lv0, lv1, pct * self.item_rate / 100.0 / RANGE))
        return out

    # ---------------------------------------------------------------- output
    def eq_cat(self, it):
        t, s = it['type'], it['sub']
        if t == IT_WEAPON:
            return 11 if s in (WEAPON_ARROW, WEAPON_QUIVER) else 0
        if t == IT_ARMOR:
            return ARMOR_SUB_CAT.get(s)
        if t == IT_BELT:
            return 8
        if t == IT_RING:
            return 11
        return None

    @staticmethod
    def jobmask(it):
        a = it['anti']
        m = 0
        if not a & ANTI_WARRIOR:
            m |= 1
        if not a & ANTI_ASSASSIN:
            m |= 2
        if not a & ANTI_SURA:
            m |= 4
        if not a & ANTI_SHAMAN:
            m |= 8
        return m

    @staticmethod
    def level(it):
        for t, v in it['limits']:
            if t == LIMIT_LEVEL:
                return v
        return 0

    @staticmethod
    def chance(x):
        if x <= 0:
            return 0
        if x >= 1.0:
            return 100000000
        return max(1, int(x * 100000000.0 + 0.5))

    def map_names(self):
        names = {}
        uid = os.path.join(REPO_C30, 'root', 'uidropwiki.py')
        mcd = os.path.join(REPO_C30, 'root', 'monstercard_data.py')
        try:
            ns = {}
            text = read_text(uid)
            blk = text[text.index('MAP_NAMES = {'):]
            blk = blk[:blk.index('}') + 1]
            exec(blk.encode('latin-1').decode('unicode_escape').encode('latin-1').decode('cp1250'), ns)
            names.update(ns['MAP_NAMES'])
        except Exception as e:
            self.warn.append('uidropwiki map names: %s' % e)
        try:
            ns = {}
            text = read_text(mcd)
            blk = text[text.index('MAPY = {'):]
            blk = blk[:blk.index('}') + 1]
            exec(blk.encode('latin-1').decode('unicode_escape').encode('latin-1').decode('cp1250'), ns)
            for k, v in ns['MAPY'].items():
                names.setdefault(k, v[1])
        except Exception as e:
            self.warn.append('monstercard map names: %s' % e)
        for k, v in self.dungeon_name.items():
            names.setdefault(k, v)
        for k, v in MAP_NAMES_EXTRA.items():
            names.setdefault(k, v)
        return names

    def write(self):
        L = collections.defaultdict(list)    # file -> lines
        items = self.items
        hdr = '# MT2009_PLUS_WIKI_V2_DATA - GENERATED by tools/wikiv2/gen_wiki_data.py from the server tables; do not edit\n'
        # ---------------- items.txt
        roots = {}
        for v in sorted(items):
            it = items[v]
            cat = self.eq_cat(it)
            if cat is None:
                continue
            chain = self.chain_of.get(v, [v])
            root = chain[0]
            if root in roots:
                continue
            r = items[root]
            if not r['name'] or not r['name'].strip() or self.eq_cat(r) is None:
                continue
            if not any(x in self.obtainable for x in chain):
                continue
            roots[root] = (self.eq_cat(r), self.jobmask(r), self.level(r))
        for root, (cat, jm, lv) in sorted(roots.items(), key=lambda x: (x[1][0], x[1][2], x[0])):
            L['items'].append('EQ\t%d\t%d\t%d\t%d' % (cat, jm, lv, root))
        for chain in sorted(self.chains):
            L['items'].append('CH\t' + '\t'.join(str(x) for x in chain))
        for v in sorted(self.rs):
            to, cost, prob, mats = self.rs[v]
            L['items'].append('RS\t%d\t%d\t%d\t%d\t%s' % (v, to, cost, prob, ','.join('%d:%d' % m for m in mats) or '-'))
        co = []
        for v in sorted(items):
            it = items[v]
            cat = None
            preview = 0
            if it['type'] == IT_COSTUME:
                cat = COSTUME_CAT.get(it['sub'], 8)
                if cat == 5:
                    preview = it['values'][1]
            elif it['type'] == IT_PET and it['sub'] == 12:
                cat = 6
                preview = it['values'][0]
            if cat is None or not it['name'].strip() or junk_name(it['name']):
                continue
            co.append((cat, v, preview))
        for cat, v, pv in sorted(co):
            L['items'].append('CO\t%d\t%d\t%d' % (cat, v, pv))
        shop_rows = set()
        for npc, it, cnt in self.shops:
            if it not in items or npc not in self.mobs:
                continue
            i = items[it]
            if i['flag'] & (1 << 4):    # ITEM_FLAG_COUNT_PER_1GOLD
                price = cnt if not i['gold'] else cnt // i['gold']
            else:
                price = i['gold'] * cnt
            shop_rows.add((npc, it, price, cnt))
        for npc, it, cnt, ptype, price in self.special_shops:
            if it in items and ptype.upper() == 'GOLD' and npc in self.mobs:
                shop_rows.add((npc, it, price, cnt))
        for r in sorted(shop_rows):
            L['items'].append('SHOP\t%d\t%d\t%d\t%d' % r)
        src = set()
        for q, vn, cnt in self.quest_rewards:
            if vn in items:
                src.add((vn, u'Nagroda za zadanie (%d szt.)' % cnt))
        for npc, it, cnt, ptype, price in self.special_shops:
            if it in items and not (ptype.upper() == 'GOLD' and npc in self.mobs):
                src.add((it, u'Sklep specjalny (%s %d)' % (u'yang' if ptype.upper() == 'GOLD' else ptype.lower(), price)))
        for vn in self.itemshop:
            if vn in items:
                src.add((vn, u'Sklep przedmiotów (ItemShop)'))
        for vn, lst in self.common.items():
            lv0 = min(x[1] for x in lst)
            lv1 = max(x[2] for x in lst)
            cmin = min(x[3] for x in lst) * 100
            cmax = max(x[3] for x in lst) * 100
            rng = fmt_pct(cmin) if fmt_pct(cmin) == fmt_pct(cmax) else u'%s-%s' % (fmt_pct(cmin), fmt_pct(cmax))
            src.add((vn, u'Wspólny drop z potworów dla postaci poz. %d-%d: %s%% za zabójstwo (zależnie od rangi potwora)'
                     % (lv0, lv1, rng)))
        for vn, text in sorted(src):
            L['items'].append('SRC\t%d\t%s' % (vn, text))
        # ---------------- mobs.txt
        names = self.map_names()
        used_maps = set()
        for race, pl in self.places.items():
            used_maps.update(pl)
        for m in sorted(set(self.map_index) | used_maps):
            nm = names.get(m) or ('Mapa %d' % m)
            L['mobs'].append('MAP\t%d\t%s' % (m, nm))
        self.map_name = names
        cats = self.mob_categories(names)
        mob_seen = set()
        cid = 0
        for group, label, mobs in cats:
            L['mobs'].append('MCAT\t%d\t%d\t%s' % (cid, group, label))
            for race in mobs:
                L['mobs'].append('MC\t%d\t%d' % (cid, race))
                mob_seen.add(race)
            cid += 1
        for race in sorted(self.md):
            rows = self.md[race]
            for it, (cmin, cmax, ch) in sorted(rows.items(), key=lambda x: (-x[1][2], x[0])):
                L['md'].append('MD\t%d\t%d\t%d\t%d\t%d' % (race, it, cmin, cmax, self.chance(ch)))
            mob_seen.add(race)
        for race in sorted(self.places):
            for m, kind in sorted(self.places[race].items()):
                L['mp'].append('MP\t%d\t%d\t%d' % (race, m, kind))
            mob_seen.add(race)
        # ---------------- chests.txt
        chest_cats, chest_lines = self.chest_categories()
        for c, label in chest_cats:
            L['chests'].append('CCAT\t%d\t%s' % (c, label))
        for c, chest, frm in chest_lines:
            L['chests'].append('CL\t%d\t%d\t%d' % (c, chest, frm))
            if frm:
                mob_seen.add(frm)
        listed = set(l[1] for l in chest_lines)
        for chest in sorted(self.cc):
            if chest not in listed:
                continue
            for it, (cmin, cmax, ch) in sorted(self.cc[chest].items(), key=lambda x: (-x[1][2], x[0])):
                L['chests'].append('CC\t%d\t%d\t%d\t%d\t%d' % (chest, it, cmin, cmax, self.chance(ch)))
        for race in sorted(mob_seen):
            mob = self.mobs.get(race)
            if not mob:
                continue
            rf = mob['race']
            elements = [1 if rf & f else 0 for f in (RF_ATT_ELEC, RF_ATT_FIRE, RF_ATT_ICE, RF_ATT_TEMPLE, RF_ATT_EARTH, RF_ATT_DARK)]
            L['ms'].append('MS\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%s\t%s' % (
                race, mob['level'], mob['rank'], mob['type'], mob['hp'], mob['exp'], mob['dmin'], mob['dmax'],
                mob['dfn'], mob['gmin'], mob['gmax'], rf, mob['immune'], mob['ai'],
                ','.join(str(x) for x in mob['resists']), ','.join(str(x) for x in elements)))
        # ---------------- crafting.txt
        npcs = set()
        for r in self.recipes:
            npcs.update(r[0])
        order = [n for n, lab in NPC_LABELS if n in npcs]
        order += sorted(n for n in npcs if n not in order)
        labels = dict(NPC_LABELS)
        for n in order:
            L['crafting'].append('NPC\t%d\t%s' % (n, labels.get(n, u'-')))
        for n in order:
            per_map = collections.Counter()
            for m, x, y in sorted(self.npc_pos.get(n, [])):
                per_map[m] += 1
                if per_map[m] > 4:
                    continue
                L['crafting'].append('LOC\t%d\t%d\t%d\t%d' % (n, m, x, y))
        for npcs_, kind, res, cnt, gold, pct, mats in self.recipes:
            L['crafting'].append('CUBE\t%s\t%d\t%d\t%d\t%d\t%d\t%s' % (','.join(str(x) for x in npcs_), kind, res, cnt,
                                                                      gold, pct, mats or '-'))
        files = {
            'items.txt': hdr + '# EQ cat jobmask level v0 | CH v0..vN | RS from to cost prob mats | CO cat vnum preview | '
                         'SHOP npc item price count | SRC item text\n' + '\n'.join(L['items']) + '\n',
            'mobs.txt': hdr + '# chance: per kill, killer at the mob level, base item rate %d%%, 100000000 = 100%%\n'
                        '# MAP idx name | MCAT id group label | MC id mob | MS mob level rank type hp exp dmgMin dmgMax def '
                        'goldMin goldMax raceFlag immuneFlag aiFlag resists(sword,twohand,dagger,bell,fan,bow,fire,elect,'
                        'magic,wind,poison) elements(elec,fire,ice,wind,earth,dark: 1 = attacks with it, race flags) | '
                        'MD mob item cmin cmax chance | MP mob map kind\n' % self.item_rate
                        + '\n'.join(L['mobs'] + L['ms'] + L['md'] + L['mp']) + '\n',
            'chests.txt': hdr + '# chance: per opening, 100000000 = 100% | CCAT id label | CL cat chest fromMob | '
                                'CC chest item cmin cmax chance\n' + '\n'.join(L['chests']) + '\n',
            'crafting.txt': hdr + '# NPC npc label | LOC npc map x y (regen/npc.txt cx cy: map-local metres = world units '
                                  '/ 100, as the minimap / Lokalizator NPC) | CUBE npcs kind(0 recipe, 1 exchange) result '
                                  'count gold percent mats (v:c; "a-b:c" = c of any one of a..b)\n'
                            + '\n'.join(L['crafting']) + '\n',
        }
        data = {}
        for name, text in files.items():
            low = text.lower()
            for b in BANNED:
                if b in low:
                    # an item/mob name can not contain these; only a label could - fail loudly
                    for line in text.split('\n'):
                        if b in line.lower() and not line.startswith('#'):
                            raise SystemExit('banned word %r in %s: %s' % (b, name, line[:120]))
            data[name] = text.encode('cp1250', 'replace')
        self.counts = dict(
            EQ=sum(1 for l in L['items'] if l.startswith('EQ\t')), CH=len(self.chains), RS=len(self.rs),
            CO=collections.Counter(l.split('\t')[1] for l in L['items'] if l.startswith('CO\t')),
            SHOP=sum(1 for l in L['items'] if l.startswith('SHOP\t')), SRC=sum(1 for l in L['items'] if l.startswith('SRC\t')),
            MAP=sum(1 for l in L['mobs'] if l.startswith('MAP\t')), MCAT=cid,
            MC=sum(1 for l in L['mobs'] if l.startswith('MC\t')), MS=len(L['ms']), MD=len(L['md']),
            MD_mobs=len(self.md), MP=len(L['mp']), CCAT=len(chest_cats), CL=len(chest_lines),
            CC=sum(len(self.cc[c]) for c in listed), NPC=len(order),
            LOC=sum(1 for l in L['crafting'] if l.startswith('LOC\t')), CUBE=len(self.recipes))
        return data

    def mob_categories(self, names):
        """[(group, label, [mobs])]: Metins and bosses by level band, monsters by map"""
        def lvl(r):
            return self.mobs[r]['level']
        # a monster is listed when it lives somewhere or has drop rows of its own (every monster gets the world's
        # extras - Moonlight chest... - so md alone says nothing)
        own = set(self.dropgroup) | set(self.killgroup) | set(self.limitgroup) | set(m for m, *_ in self.file_drops)
        own |= set(r for r, mob in self.mobs.items() if mob['drop_item'] in self.etc)
        live = set(self.places) | (own & set(self.md))
        stones = sorted((r for r in live if self.mobs.get(r) and self.mobs[r]['type'] == CHAR_TYPE_STONE), key=lambda r: (lvl(r), r))
        bosses = sorted((r for r in live if self.mobs.get(r) and self.mobs[r]['type'] == CHAR_TYPE_MONSTER and
                         self.mobs[r]['rank'] >= MOB_RANK_BOSS), key=lambda r: (lvl(r), r))
        out = []
        bands = [(1, 39), (40, 59), (60, 74), (75, 89), (90, 99), (100, 109), (110, 255)]

        def by_band(group, word, mobs):
            for a, b in bands:
                sel = [r for r in mobs if a <= lvl(r) <= b]
                label = u'%s poz. %d-%d' % (word, a, b) if b < 255 else u'%s poz. %d+' % (word, a)
                for i in range(0, len(sel), 60):
                    part = sel[i:i + 60]
                    out.append((group, label + (u' (%d)' % (i // 60 + 1) if len(sel) > 60 else u''), part))
        by_band(0, u'Metiny', stones)
        by_band(1, u'Bossowie', bosses)
        # monsters: by the map they live on (lowest map index of a regular map first, a dungeon second)
        permap = collections.defaultdict(list)
        unplaced = []
        for r in sorted(live):
            mob = self.mobs.get(r)
            if not mob or mob['type'] != CHAR_TYPE_MONSTER or mob['rank'] >= MOB_RANK_BOSS:
                continue
            pl = self.places.get(r)
            if not pl:
                unplaced.append(r)
                continue
            for m in pl:
                permap[m].append(r)
        # maps of one name (the three kingdoms' copies) are one category
        byname = collections.OrderedDict()
        for m in sorted(permap):
            nm = names.get(m) or ('Mapa %d' % m)
            byname.setdefault(nm, set()).update(permap[m])
        def namekey(nm):
            mobs = sorted(lvl(r) for r in byname[nm])
            return (mobs[len(mobs) // 2], nm)
        for nm in sorted(byname, key=namekey):
            mobs = sorted(byname[nm], key=lambda r: (lvl(r), r))
            for i in range(0, len(mobs), 60):
                out.append((2, nm + (u' (%d)' % (i // 60 + 1) if len(mobs) > 60 else u''), mobs[i:i + 60]))
        unplaced.sort(key=lambda r: (lvl(r), r))
        for i in range(0, len(unplaced), 60):
            out.append((2, u'Inne potwory' + (u' (%d)' % (i // 60 + 1) if len(unplaced) > 60 else u''), unplaced[i:i + 60]))
        return out

    def chest_categories(self):
        """CCAT list and CL lines: boss / dungeon / Metin / event / other chests"""
        event_vnums = set()
        gdir = os.path.join(REPO_C30, '..', '..', 'linux-port', 'docker', 'game')
        for part in EVENT_GROUP_FILES:
            f = os.path.join(gdir, 'special_item_group.%s.txt' % part)
            if os.path.isfile(f):
                for name, node in text_nodes(f):
                    if node.get('vnum'):
                        event_vnums.add(str_to_number(node['vnum'][0]))
        cor_vnums = set()
        f = os.path.join(gdir, 'special_item_group.cors.txt')
        if os.path.isfile(f):
            for name, node in text_nodes(f):
                if node.get('vnum'):
                    cor_vnums.add(str_to_number(node['vnum'][0]))
        best = {}   # chest -> (prio, chance, mob)
        dungeon_maps = set(self.dungeon_name)
        for race, rows in self.md.items():
            mob = self.mobs[race]
            for it, (cmin, cmax, ch) in rows.items():
                if it not in self.cc:
                    continue
                prio = 2 if mob['rank'] >= MOB_RANK_BOSS else (1 if mob['type'] == CHAR_TYPE_STONE else 0)
                key = (prio, ch, -race)
                if it not in best or key > best[it][0]:
                    best[it] = (key, race)
        cats = [(0, u'Skrzynie bossów'), (1, u'Skrzynie lochów'), (2, u'Skrzynie z Metinów'), (3, u'Skrzynie z wydarzeń'),
                (4, u'Cor Draconis i Smocze Skrzynie'), (5, u'Pozostałe skrzynie')]
        lines = []
        for chest in sorted(self.cc):
            frm = best.get(chest, (None, 0))[1]
            if self.items[chest]['type'] in WEARABLE_TYPES:
                continue        # a group number that only shares its number with a weapon / armour: no chest
            if chest in event_vnums:
                c = 3
            elif chest in cor_vnums or self.items[chest]['name'].startswith('Cor '):
                c = 4
            elif frm:
                mob = self.mobs[frm]
                in_dungeon = any(m in dungeon_maps or k > 0 for m, k in self.places.get(frm, {}).items())
                if mob['type'] == CHAR_TYPE_STONE:
                    c = 2
                elif in_dungeon or (6001 <= frm <= 6199):
                    c = 1
                elif mob['rank'] >= MOB_RANK_BOSS:
                    c = 0
                else:
                    c = 5
            else:
                c = 5
            lines.append((c, chest, frm))
        lines.sort(key=lambda x: (x[0], x[1]))
        # keep the menu sane: split a big category into parts of 80
        out_cats = []
        out_lines = []
        cid = 0
        for c, label in cats:
            sel = [l for l in lines if l[0] == c]
            if not sel:
                continue
            for i in range(0, len(sel), 80):
                out_cats.append((cid, label + (u' (%d)' % (i // 80 + 1) if len(sel) > 80 else u'')))
                for _, chest, frm in sel[i:i + 80]:
                    out_lines.append((cid, chest, frm))
                cid += 1
        return out_cats, out_lines


def base_name(name):
    """an item name without its "+N" """
    return re.sub(r'\s*\+\s*\d+\s*$', '', name or '').strip().lower()


def junk_name(name):
    n = (name or '').lower()
    return any(w in n for w in ('test', '[gm]', 'unused', 'nieuzywan', 'nieużywan')) or n.strip() in ('', '-', '?')


def fmt_pct(x):
    if x >= 1:
        s = '%.2f' % x
    elif x >= 0.01:
        s = '%.3f' % x
    else:
        s = '%.5f' % x
    s = s.rstrip('0').rstrip('.') if '.' in s else s
    return s.replace('.', ',')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--share')
    ap.add_argument('--out', default=DEFAULT_OUT)
    ap.add_argument('--item-rate', type=int, default=100)
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--data-root', help='with --share: the dir holding dungeon/ (the cores\' data/)')
    a = ap.parse_args()
    tmp = None
    share = a.share
    if not share:
        tmp = tempfile.mkdtemp(prefix='wikigen-')
        subprocess.run(['docker', 'cp', GAME + ':/opt/metin2/share/locale/poland', tmp], check=True)
        share = os.path.join(tmp, 'poland')
        # drop_wiki.txt regen paths ("data/dungeon/...") are relative to the cores' dir = share's data/
        os.makedirs(os.path.join(tmp, 'data'))
        subprocess.run(['docker', 'cp', GAME + ':/opt/metin2/share/data/dungeon', os.path.join(tmp, 'data', 'dungeon')],
                       check=True)
    try:
        g = Gen(share, a.item_rate, os.path.join(tmp, 'data') if tmp else a.data_root)
        g.load()
        g.build()
        data = g.write()
        print('test server event flag mob_item = %s (the chances use %d%%)' % (g.flags.get('mob_item', 'unset'), a.item_rate))
        print('CONFIG permille: moonlight %d / stone %d, kupon stone %d / boss %d, blessing stone %d' % (
            g.moon, g.moon_stone, g.coin_stone, g.coin_boss, g.bless_stone))
        for k in ('EQ', 'CH', 'RS', 'CO', 'SHOP', 'SRC', 'MAP', 'MCAT', 'MC', 'MS', 'MD', 'MD_mobs', 'MP', 'CCAT', 'CL',
                  'CC', 'NPC', 'LOC', 'CUBE'):
            v = g.counts[k]
            if isinstance(v, collections.Counter):
                v = ', '.join('cat %s: %d' % (c, n) for c, n in sorted(v.items(), key=lambda x: int(x[0])))
            print('%-8s %s' % (k, v))
        for w in g.warn:
            print('WARN', w)
        rc = 0
        if not a.check:
            os.makedirs(a.out, exist_ok=True)
        for name, b in sorted(data.items()):
            path = os.path.join(a.out, name)
            old = open(path, 'rb').read() if os.path.exists(path) else None
            if a.check:
                state = 'same' if old == b else 'DIFFERENT'
                if old != b:
                    rc = 1
            else:
                if old != b:
                    with open(path, 'wb') as f:
                        f.write(b)
                state = 'unchanged' if old == b else 'written'
            print('%-14s %8d bytes  %s' % (name, len(b), state))
        return rc
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    sys.exit(main())
