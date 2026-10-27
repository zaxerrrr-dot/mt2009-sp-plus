"""yohara_bot_cohort_800.py - the 800 new Yohara bots (MT2009_PLUS_BOT_YOHARA800_V1), the part of
tools/yohara_bot_cohort.py that `--yohara800 N` runs instead of the night's cohorts:

    yohara_bot_cohort.py <outdir> --yohara800 800 [--channels 1] [--active 800] [--pid-base 6001] [--cor-vnum 51510]
                                  [--better-pct 22] [--db-container mt2009plustest-db]

The owner, 27 October 2026: "Stworz 800 botow na 1 lvl - 30lvl championa. Rozne profesje, rozne eq, wszystkie skile
minimum na G1, rozdale punkty statystyk, EQ z G0, niektore postacie lepsze eq niz g0, daj im po 200kk na start, aby
mialy na potki itd, zresp je w dongan, daj im tez po 2000 SM aby mogly kupic sobie kostiumy, mounty itd. 21 lvl konia.
... Nie bonuj EQ, daj im po 400 wzmocnien przedmiotow i po 800 zaczarowan przedmiotow ... Daj im rowniez cor draconis
legenedarne 400 sztuk ... Daj im rowniez po 400 zielonych smoczych fasol" (cache/yohara/boty-800-brief.md).

Who: NEW bot identities - the 4500 of the registry (the seed's, PID 4-4503) and their population stay as they are.
Each one is made the way the seed makes a bot (linux-port/docker/mariadb/playerbot/playerbots_seed.sql) and the
companions' new identities do (playerbot_sidekick.h, MakePlayerBotSidekickIdentity): the ledger row
(common.playerbot_seed_state, version 1, pending until the rest is written, then complete), a non-login account
(playerbot_<pid-3>, password '!', status BLOCK, social id '9' + the number padded to 12), the character, its
player_index row with the kingdom - so the cores' registry (LoadRegisteredBots) takes it as any bot. The PIDs are
--pid-base.. (6001-6800: past the seed's 4503, under the companions' 8000-8999 and the people's 9001+; the tool and the
SQL check that nothing holds them). The names are the nickname pool's (playerbot_names.sql - the kingdom's own share,
in the pool's order, a name nobody wears; the Legends' never) with their common.playerbot_name_history row (the seed
name "y8<pid>", the pool's version), so that file's next run sees settled bots and renames none.

The eight class/path pairs in equal shares, both sexes in turn, the kingdoms in turn; level 120 with the stats of 120
(90 each), the hit/spell points the levels roll on average, the sub-skill points of 120, the path's six skills at G1
(30) - a third of them higher (G2-G10, now and then P) -, Precyzja (246) P (every bot's anyway, PrecisionSkillBonus),
combo 2, leadership 1, riding 21 and the horse call; horse level 21 (hp 35, stamina 120 - the population's own numbers
of a level-21 horse); 200 000 000 gold; account cash 2000 (SM); saved standing in Dongan (373) by the merchants
(the arrival / safe point 1102450, 506850 - where a revived Sung Ma bot stands up and Dongan's errand trades).

The Champion: a level 1-30 by the nine Sung Ma maps' shares of the 100's tool (yohara_bot_cohort_sungma.MAPS:
Twierdza 10, Dongan 14, Seoganland 12, Namgan 12, Yilad 12, Wawoz 12, Rozpadlina 10, Schronienie 10, Zejscie 8), in
the range the dispatcher lands on that map: an offline member goes to the highest map whose Champion floor + 2 its
level reached (PickPlayerBotSungmaMapByBand, PLAYERBOT_SUNGMA_STEP_UP_LEVELS) - Twierdza 1-4, Dongan 5-7, Seoganland
8-9, Namgan 10-13, Yilad 14-16, Wawoz 17-19, Rozpadlina 20-23, Schronienie 24-27, Zejscie 28-30. The Will of the map
(sungma_table.txt, Sila / Witalnosc / Odpornosc - what staying on it asks): the items' (the glove's at the bottom of
its plus's range - the core rolls it at the first load; the jade's and the Will talisman's as written) and the points
of the level (3 a level past the first) to the stat short most - Sila, Odpornosc, Witalnosc, then Inteligencja; the
rest unspent (conqueror_point - the core spends it toward the next map).

The gear - no bonuses (attrtype0-4 zero, no spirit stones, no Sung Ma stones; the owner: "Nie bonuj EQ" - they add
them with the 71085 / 71084 of their bag). The jade's and the Will talisman's own lines (the 6th / 7th slot: the Will
of the jade always, its Precyzja 80%; the talisman's Will always, its element 80% - what such an item has the moment
it is made, server-patches/obreczjadeitu2 / talizmanwoli) are written, since a loaded item does not roll them:

  G0 (the plan's package, cache/yohara/plan-boty-yohara.md 6.1): Rekawice Mocy +3, Obrecz / Kolia / Klipsy Jadeitu +3
     and a Talizman Woli +3 (the kinds the map's Will needs most), the armour of 90 +9, the helmet of 80 +9, the
     weapon of 90 +9 (the class's and the path's kind), Buty Qilina +9, Tarcza Tytanow +9;
  G1: the Sung Ma pieces +6, the helmet of 100 (Smokow) +0..+5, the weapon of Smoka Mroku (96) +9;
  G2: the Sung Ma pieces +9, the Hydra's gear (the Zodiac weapon and armour +9, the helmet of 100 +9, Ogniste Buty +9,
     Pas Dusz +9, Szarfa Wladcy Absolutnego +3) - without its bonuses and its alchemy.
  A bot gets the lowest tier that carries its map (G0 does to Rozpadlina, Schronienie and Zejscie ask G1); then more
  bots are lifted at random to --better-pct of the cohort (better than G0 - G1, a third of them G2). The Sung Ma
  pieces are account-bound like the G0 package (player.item_account_bound, why 'yohara800'). No alchemy is worn.
  An archer: 200 Srebrna Strzala on and 200 in the bag.

The bag (INVENTORY, cells 0..; a new character's bag is empty; MT2009's stacks are 200): 400 Wzmocnienie Przedmiotu
(71085, 2 x 200), 800 Zaczarowanie Przedmiotu (71084, 4 x 200), 400 Cor Draconis (legendarne) (--cor-vnum, 51510 -
special_item_group.cors.txt opens it as 50259: one Legendary Najnizszy stone of the seven; 2 x 200), 400 Zielona
Smocza Fasola (100300, 2 x 200), 200 red potions (27003), a caster's 200 blue (27006). 71084 / 71085 carry
ANTI_SELL / GIVE / MYSHOP / DROP, the Cor ANTI_SELL / DROP: none of them can be sold or traded away; the beans can
(antiflag 0). Bots never use the extra inventory windows (dodatkowy-ekwipunek.md): all of it is in the bag.

The cohort: common.playerbot_yohara_cohort rows, purpose 'yohara800' (the cores read it as the Sung Ma maps' purpose -
playerbot_yohara_bots.h ParsePlayerBotYoharaPurpose, MT2009_PLUS_BOT_YOHARA800_V1), the channel of --channels in
turn, applied at once; past --active the rows rest (rest_until 2099) - the cores hold them offline - until
cohort_activate.sql. The cohort's members are never loaded on their home core: its dispatcher hands them over to
game3, PLAYERBOT_COHORT_DISPATCH a pass; each lands on its map's arrival.

Writes (nothing is changed by the tool itself - it only reads the database):
  cohort_apply.sql       the identities, their gear and bag, the cohort's rows. Game stopped (the db core caches
                         characters; the registry is read at a core's start). Idempotent: a PID whose ledger row is
                         complete is left alone; one half made by an interrupted run is cleared and made again; a
                         PID, login, social id or name held by anybody else stops the file before its first write.
  cohort_activate.sql    the resting rows to work (all; or edit its LIMIT). Safe with the game running.
  cohort_dissolve.sql    the rows into common.playerbot_yohara800_ended, out of the cohort (the bots stay registry
                         bots of the population - level 120 Champions on game1 when the slider reaches them). Safe
                         with the game running.
  cohort_remove.sql      every trace of the 800 identities (their characters, items, quests, accounts, ledger and
                         name rows, cohort rows, bot tables), by the tool's ledger common.playerbot_yohara800. Game
                         stopped.
  cohort_status.sql      the counts by map, tier, channel, online.
  pick.tsv, pids.txt, plan.txt (the distribution, the env the cores need, the memory and CPU estimate).
"""
import os, re, sys, random, collections

import yohara_bot_cohort_hydra as H
import yohara_bot_cohort_sungma as SM

PURPOSE = 'yohara800'
LEVEL = 120
GOLD = 200000000
CASH = 2000
HORSE_LEVEL, HORSE_HP, HORSE_STAMINA = 21, 35, 120
DONGAN = (373, 1102450, 506850)          # the arrival / safe point by Dongan's merchants (playerbot_yohara_sungma.h)
SIDEKICK_PID_FLOOR = 8000                # MakePlayerBotSidekickIdentity's gap 8000-8999
SEED_TOP = 4503                          # the seed's registry: PID 4-4503
NAME_POOL_VERSION_RE = re.compile(r"SET @playerbot_pool_version = '([^']+)';")

# the cores' Sung Ma table (PLAYERBOT_SUNGMA_MAPS bChampionMin) and the dispatcher's step up
CHAMPION_FLOOR = {374: 1, 373: 3, 376: 6, 377: 8, 385: 12, 388: 15, 389: 18, 393: 22, 394: 26}
STEP_UP = 2

# the bag (vnum, count) - stacks of 200
ADD, CHANGE, BEAN = 71085, 71084, 100300
POT_RED, POT_BLUE = 27003, 27006
STACK = 200

# POINT_* of the Sung Ma lines (czempion / obreczjadeitu2 / talizmanwoli): Sila, Witalnosc, Odpornosc, Inteligencja
P_STR, P_HP, P_MOVE, P_IMMUNE, P_HIT = 184, 185, 186, 187, 197
WILL_POINT = (P_STR, P_HP, P_MOVE, P_IMMUNE)
ELEMENTS = (178, 179, 180, 181, 182, 183)
# jade families by kind (Dym Sila, Noc Witalnosc, Mgla Odpornosc, Slonce Inteligencja) - bracelet, necklace, earrings
JADE_BASE = {
    'bracelet': {0: 14610, 1: 14600, 2: 14580, 3: 14590},
    'necklace': {0: 16610, 1: 16600, 2: 16580, 3: 16590},
    'earrings': {0: 17600, 1: 17590, 2: 17570, 3: 17580},
}
JADE_POS = {'bracelet': 3, 'necklace': 5, 'earrings': 6}
WILL_TALISMAN_BASE = {0: 81000, 1: 81300, 2: 81250, 3: 81550}   # SILA, WIT, ODP, INT
GLOVE_BASE = 23000                                               # Rekawice Mocy (Sila)
# playerbot_yohara_gear.cpp's tables, +0..+9
GLOVE_WILL = ((3, 7), (5, 11), (9, 17), (14, 22), (19, 28), (24, 34), (29, 40), (34, 46), (39, 52), (58, 63))
JADE_PRECISION = ((1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 8), (8, 10), (9, 11), (10, 14))
JADE_WILL = ((1, 2), (3, 4), (5, 6), (7, 8), (9, 10), (11, 12), (13, 14), (15, 17), (18, 20), (21, 24))
JADE_EAR_WILL = ((1, 2), (2, 4), (3, 6), (5, 8), (7, 10), (9, 12), (13, 14), (15, 17), (18, 20), (21, 24))
# server-patches/talizmanwoli/README.md: the Will line (common / rare 10%), the element line (80%; common / rare)
TAL_WILL = ((1, 1, 3, 5, 7, 9, 11, 14, 17, 21), (2, 3, 4, 6, 8, 10, 12, 16, 19, 24))
TAL_ELEMENT = ((1, 2, 3, 4, 5, 6, 7, 8, 9, 15), (2, 3, 4, 5, 6, 7, 8, 9, 10, 17))

TIER_PLUS = (3, 6, 9)
TIER_NAME = ('G0', 'G1', 'G2')
# weapons (cls, grp): G0 the 90-level +9, G1 Smoka Mroku (96) +9, G2 the Zodiac +9 (the Hydra's)
WEAPON = {
    0: {(0, 1): 279, (0, 2): 3189, (1, 1): 4049, (1, 2): 2169, (2, 1): 289, (2, 2): 289, (3, 1): 7199, (3, 2): 5339},
    1: {(0, 1): 329, (0, 2): 3239, (1, 1): 1199, (1, 2): 2219, (2, 1): 349, (2, 2): 349, (3, 1): 7319, (3, 2): 5179},
    2: {(0, 1): 319, (0, 2): 3229, (1, 1): 1189, (1, 2): 2209, (2, 1): 309, (2, 2): 309, (3, 1): 7309, (3, 2): 5169},
}
ARMOUR90 = {0: 12019, 1: 12029, 2: 12039, 3: 12049}
HELMET80 = {0: 12289, 1: 12409, 2: 12549, 3: 12689}
HELMET100 = {0: 12690, 1: 12700, 2: 12710, 3: 12720}             # + plus
SHOES_QILIN = 15419
# EQUIPMENT positions this tool writes (common/length.h: body, head, foots, wrist, weapon, neck, ear, arrow, shield,
# sash, belt, pendant / talisman, glove)
EQ_POS = (0, 1, 2, 3, 4, 5, 6, 9, 10, 22, 23, 25, 26)
# the skills besides the path's: leadership, combo, riding (the horse's level), the horse call, Precyzja
EXTRA_SKILLS = ((121, 0, 1), (122, 0, 2), (130, 1, HORSE_LEVEL), (131, 0, 10), (246, 3, 40))
BOT_MB = 1.7          # a bot on a core (plan-boty-yohara.md 1.6)
BOT_CPU_PCT = 0.15    # a Sung Ma resident's share of one CPU on game3 (test, 27 October: ch1 game3 8.4% over 2 h with ~60)
GRIDS_MB = sum(SM.GRID_MB.values())


def landing_ranges():
    """map -> (lo, hi): the Champion levels the dispatcher sends to it (floor + STEP_UP .. the next one's - 1)."""
    maps = [m[0] for m in SM.MAPS]
    out = {}
    for i, m in enumerate(maps):
        lo = 1 if i == 0 else CHAMPION_FLOOR[m] + STEP_UP
        hi = 30 if i == len(maps) - 1 else CHAMPION_FLOOR[maps[i + 1]] + STEP_UP - 1
        out[m] = (lo, hi)
    return out


def sql_str(s):
    return "'" + s.replace('\\', '\\\\').replace("'", "''") + "'"


# ------------------------------------------------------------------------------------------------ the names
def name_pool(repo):
    """The nickname pool as playerbot_names.sql deals it: kingdom -> names in order (the priority names first, the
    Legends' never), and the pool's version."""
    path = os.path.join(repo, 'linux-port', 'docker', 'mariadb', 'playerbot', 'playerbot_names.sql')
    text = open(path, encoding='latin-1').read()
    version = NAME_POOL_VERSION_RE.search(text).group(1)
    pool = [(int(n), int(e), nm) for n, e, nm in re.findall(r"^\s*\((\d+),(\d),'([^']*)'\)", text, re.M)]
    prio = re.findall(r"^\s*\((\d+),'([^']*)'\)", text.split('CREATE TEMPORARY TABLE playerbot_name_priority', 1)[1]
                      .split('DELETE np FROM', 1)[0], re.M)
    legend = re.search(r"name REGEXP '([^']+)'", text).group(1)
    legend_re = re.compile(legend, re.I)
    prio_l = set(nm.lower() for _, nm in prio)
    pool = [(n + 1000, e, nm) for n, e, nm in pool if nm.lower() not in prio_l]
    pool += [(int(k), (2, 1, 3)[(int(k) - 1) % 3], nm) for k, nm in prio]
    out = collections.defaultdict(list)
    for n, e, nm in sorted(pool):
        if not legend_re.match(nm):
            out[e].append(nm)
    return out, version


def valid_name(nm):
    return 3 <= len(nm) <= 16 and re.match(r'^[A-Za-z0-9]+$', nm) is not None


# ------------------------------------------------------------------------------------------------ the Will
def item_will(tier, kinds, rng):
    """The Sung Ma pieces of a tier for the kinds chosen: [(slot, vnum, will kind, will, attrs [(type, value)])]."""
    plus = TIER_PLUS[tier]
    out = []
    for piece in ('bracelet', 'necklace', 'earrings'):
        k = kinds[piece]
        rngw = (JADE_EAR_WILL if piece == 'earrings' else JADE_WILL)[plus]
        will = rng.randint(*rngw)
        attrs = []
        if rng.random() < 0.8:
            attrs.append((P_HIT, rng.randint(*JADE_PRECISION[plus])))
        attrs.append((WILL_POINT[k], will))
        out.append((JADE_POS[piece], JADE_BASE[piece][k] + plus, k, will, attrs))
    k = kinds['talisman']
    rare = 1 if rng.random() < 0.1 else 0
    will = TAL_WILL[rare][plus]
    attrs = [(WILL_POINT[k], will)]
    if rng.random() < 0.8:
        attrs.append((rng.choice(ELEMENTS), TAL_ELEMENT[1 if rng.random() < 0.1 else 0][plus]))
    out.append((25, WILL_TALISMAN_BASE[k] + plus, k, will, attrs))
    return out


def plan_will(req, champion, tier, rng):
    """Kinds, items and points of a bot of this Champion level and tier for a map of these requirements (str, hp,
    move, immune). Returns None when the map's Sila / Witalnosc / Odpornosc are out of reach."""
    plus = TIER_PLUS[tier]
    glove = GLOVE_WILL[plus][0]                     # the bottom of the plus's range: the core rolls it
    have = [glove, 0, 0, 0]
    # each piece's kind: the stat short most (Sila, Witalnosc, Odpornosc), then Inteligencja; the pieces with the
    # most Will first (the planner's estimate: the bottom of each range)
    est = [('bracelet', JADE_WILL[plus][0]), ('necklace', JADE_WILL[plus][0]), ('earrings', JADE_EAR_WILL[plus][0]),
           ('talisman', TAL_WILL[0][plus])]
    kinds = {}
    for piece, w in sorted(est, key=lambda x: -x[1]):
        deficit = [req[k] - have[k] for k in range(4)]
        k = max((0, 1, 2), key=lambda k: (deficit[k], -k))
        if deficit[k] <= 0:
            k = 3 if deficit[3] > 0 else max((0, 1, 2), key=lambda k: (deficit[k], -k))
        kinds[piece] = k
        have[k] += w
    pieces = item_will(tier, kinds, rng)
    have = [glove, 0, 0, 0]
    for _, _, k, will, _ in pieces:
        have[k] += will
    pts = 3 * (champion - 1)
    spend = [0, 0, 0, 0]
    left = pts
    for k in (0, 2, 1, 3):
        n = min(left, max(0, req[k] - have[k]), 90)
        spend[k] = n
        left -= n
    if any(have[k] + spend[k] < req[k] for k in (0, 1, 2)):
        return None
    return dict(kinds=kinds, pieces=pieces, glove=(GLOVE_BASE + plus, glove), spend=spend, left=left,
                will=[have[k] + spend[k] for k in range(4)])


# ------------------------------------------------------------------------------------------------ the character
def skill_blob(cls, grp, level):
    blob = bytearray(1590)
    for v in H.SKILLS[(cls, grp)]:
        blob[v * 6] = 3 if level >= 40 else (2 if level >= 30 else (1 if level >= 20 else 0))
        blob[v * 6 + 1] = level
    for v, master, lv in EXTRA_SKILLS:
        blob[v * 6] = master
        blob[v * 6 + 1] = lv
    return blob.hex().upper()


def path_skill_level(rng):
    r = rng.random()
    if r < 0.65:
        return 30                       # G1
    if r < 0.95:
        return rng.randint(31, 39)      # G2-G10
    return 40                           # P


def gear_rows(b, ctx):
    """The EQUIPMENT rows (pos, vnum, count, sockets, attrs) of a member - no bonuses."""
    cls, grp, tier = b['cls'], b['grp'], b['tier']
    wv = WEAPON[tier][(cls, grp)]
    rows = []
    if tier == 2:
        rows += [(0, H.ARMOUR[cls], 1, (0, 0, 0), []), (1, H.HELMET[cls], 1, (0, 0, 0), []),
                 (2, H.SHOES, 1, (0, 0, 0), []), (23, H.BELT, 1, (0, 0, 0), []),
                 (22, H.SASH, 1, (25, wv, 0), [])]
    else:
        helmet = HELMET80[cls] if tier == 0 else HELMET100[cls] + b['helmet_plus']
        rows += [(0, ARMOUR90[cls], 1, (0, 0, 0), []), (1, helmet, 1, (0, 0, 0), []),
                 (2, SHOES_QILIN, 1, (0, 0, 0), [])]
    rows += [(4, wv, 1, (0, 0, 0), []), (10, H.SHIELD, 1, (0, 0, 0), [])]
    w = b['will']
    rows.append((26, w['glove'][0], 1, (0, 0, 0), []))
    for pos, vnum, _, _, attrs in w['pieces']:
        rows.append((pos, vnum, 1, (0, 0, 0), attrs))
    if cls == 1 and grp == 2:
        rows.append((9, H.ARROW, STACK, (0, 0, 0), []))
    for r in rows:
        if r[1] not in ctx['proto']:
            sys.exit('item %d is not in item_proto' % r[1])
    return rows


def bag_rows(b, cor):
    kit = [(ADD, 400), (CHANGE, 800), (cor, 400), (BEAN, 400), (POT_RED, STACK)]
    if H.caster(b['cls'], b['grp']):
        kit.append((POT_BLUE, STACK))
    if b['cls'] == 1 and b['grp'] == 2:
        kit.append((H.ARROW, STACK))
    rows = []
    pos = 0
    for vnum, total in kit:
        while total > 0:
            n = min(STACK, total)
            rows.append((pos, vnum, n))
            pos += 1
            total -= n
    return rows


def attrs7(lst):
    """attrtype0..6 / attrvalue0..6: the first five (the bonuses) empty, the item's own lines in the 6th / 7th."""
    lst = [(0, 0)] * 5 + list(lst) + [(0, 0)] * (2 - len(lst))
    return ', '.join('%d, %d' % t for t in lst[:7])


# ------------------------------------------------------------------------------------------------ run
def run(a, q, repo):
    want = a.yohara800
    rng = random.Random(a.seed)
    base = a.pid_base
    top = base + want - 1
    channels = [int(x) for x in str(a.channels).split(',') if x.strip()]
    active = want if a.active < 0 else min(a.active, want)
    cor = a.cor_vnum
    if want < 1 or not channels:
        sys.exit('yohara800: nothing to make')

    # ------------------------------------------------ the PID range: ours or nobody's
    if base <= SEED_TOP or top >= SIDEKICK_PID_FLOOR:
        sys.exit('yohara800: PIDs %d-%d must lie between the seed (%d) and the companions (%d)' % (base, top, SEED_TOP,
                                                                                            SIDEKICK_PID_FLOOR))
    ledger = {}
    for r in q('SELECT pid, login, name FROM common.playerbot_yohara800;', fatal=False) or []:
        if r and r[0].isdigit():
            ledger[int(r[0])] = (r[1], r[2])
    auto = int(q("SELECT AUTO_INCREMENT FROM information_schema.TABLES WHERE TABLE_SCHEMA='player' AND TABLE_NAME='player';")[0][0])
    first_person = q('SELECT MIN(p.id) FROM player.player p LEFT JOIN common.playerbot_seed_state l ON l.pid = p.id '
                     'WHERE l.pid IS NULL;')[0][0]
    first_person = int(first_person) if first_person not in ('NULL', '') else 0
    if auto <= top or (first_person and first_person <= top and first_person not in ledger):
        sys.exit('yohara800: the people\'s characters start at %s (next %d) - no room for %d-%d' % (first_person, auto, base, top))
    held = collections.Counter()
    for sql, what in (('SELECT id FROM player.player WHERE id BETWEEN %d AND %d;', 'character'),
                      ('SELECT pid FROM common.playerbot_seed_state WHERE pid BETWEEN %d AND %d;', 'ledger'),
                      ('SELECT pid1 FROM player.player_index WHERE pid1 BETWEEN %d AND %d;', 'index')):
        for r in q(sql % (base, top)):
            if int(r[0]) not in ledger:
                held[what] += 1
    logins = set(r[0] for r in q("SELECT login FROM account.account WHERE login LIKE 'playerbot\\_%%';"))
    socials = set(r[0] for r in q("SELECT social_id FROM account.account WHERE social_id LIKE '9%%';"))
    for pid in range(base, top + 1):
        if pid in ledger:
            continue
        if 'playerbot_%03d' % (pid - 3) in logins:
            held['login'] += 1
        if '9%012d' % (pid - 3) in socials:
            held['social_id'] += 1
    if held:
        sys.exit('yohara800: PIDs %d-%d are not free: %s' % (base, top, dict(held)))

    # ------------------------------------------------ the names
    pool, pool_version = name_pool(repo)
    worn = set(r[0].lower() for r in q('SELECT name FROM player.player;'))
    worn |= set(r[0].lower() for r in q('SELECT human_name FROM common.playerbot_name_history UNION '
                                       'SELECT seed_name FROM common.playerbot_name_history;'))
    mine = set(nm.lower() for _, nm in ledger.values())
    free = {e: [nm for nm in pool[e] if valid_name(nm) and (nm.lower() not in worn or nm.lower() in mine)] for e in (1, 2, 3)}

    # ------------------------------------------------ who: the pairs, the sexes, the kingdoms
    pairs = [(c, g) for c in range(4) for g in (1, 2)]
    members = []
    for i in range(want):
        cls, grp = pairs[i % 8]
        k = i // 8
        female = k % 2 == 1
        emp = (1, 2, 3)[(k // 2 + i) % 3]
        pid = base + i
        members.append(dict(pid=pid, cls=cls, grp=grp, female=female, emp=emp, job=cls + (4 if female else 0)))
    used = set()
    for b in members:
        if b['pid'] in ledger:
            b['name'] = ledger[b['pid']][1]
            used.add(b['name'].lower())
    for b in members:
        if 'name' in b:
            continue
        lst = free[b['emp']]
        while lst and lst[0].lower() in used:
            lst.pop(0)
        if not lst:
            sys.exit('yohara800: the name pool of kingdom %d ran out' % b['emp'])
        b['name'] = lst.pop(0)
        used.add(b['name'].lower())

    # ------------------------------------------------ the maps and the Champion levels
    shares = [m[4] for m in SM.MAPS]
    count = [int(round(want * s / 100.0)) for s in shares]
    while sum(count) > want:
        count[count.index(max(count))] -= 1
    while sum(count) < want:
        count[shares.index(max(shares))] += 1
    slots = []
    left = list(count)
    while any(left):
        for i in range(len(SM.MAPS)):
            if left[i]:
                slots.append(i)
                left[i] -= 1
    order = list(members)
    rng.shuffle(order)                  # the classes mixed on every map
    ranges = landing_ranges()
    req = SM.requirements(repo)
    for b, slot in zip(order, slots):
        mp = SM.MAPS[slot][0]
        lo, hi = ranges[mp]
        b['map'] = mp
        b['map_name'] = SM.MAPS[slot][1]
        b['champion'] = rng.randint(lo, hi)
        b['skill'] = path_skill_level(rng)
        b['helmet_plus'] = rng.randint(0, 5)
        b['rng'] = random.Random(a.seed * 100003 + b['pid'])
        for tier in (0, 1, 2):
            w = plan_will(req[mp], b['champion'], tier, random.Random(a.seed * 100003 + b['pid']))
            if w:
                b['need_tier'] = tier
                break
        else:
            sys.exit('yohara800: pid %d Champion %d cannot carry map %d even at G2' % (b['pid'], b['champion'], mp))
    # better than G0: the ones that need it, and more at random up to --better-pct (a third G2)
    target = int(round(want * a.better_pct / 100.0))
    better = [b for b in members if b['need_tier'] > 0]
    rest = [b for b in members if b['need_tier'] == 0]
    rng.shuffle(rest)
    extra = rest[:max(0, target - len(better))]
    for b in members:
        b['tier'] = b['need_tier']
    for b in better + extra:
        b['tier'] = max(b['need_tier'], 2 if rng.random() < 1.0 / 3 else 1)
    for b in members:
        b['will'] = plan_will(req[b['map']], b['champion'], b['tier'], random.Random(a.seed * 100003 + b['pid']))
    # the channels in turn, the active ones a mix (the shuffled order)
    for i, b in enumerate(order):
        b['channel'] = channels[i % len(channels)]
        b['active'] = i < active

    ctx = H.gear_context(q)
    for v in (ADD, CHANGE, cor, BEAN, POT_RED, POT_BLUE, H.ARROW):
        if v not in ctx['proto']:
            sys.exit('item %d is not in item_proto' % v)
    for b in members:
        b['gear'] = gear_rows(b, ctx)
        b['bag'] = bag_rows(b, cor)

    write_sql(a, members, pool_version, cor)
    write_reports(a, members, req, q)


def write_sql(a, members, pool_version, cor):
    pids = sorted(b['pid'] for b in members)
    out = a.outdir
    S = []
    S.append('-- MT2009_PLUS_BOT_YOHARA800_V1: the 800 new Yohara bots (tools/yohara_bot_cohort.py --yohara800). GAME STOPPED.')
    S.append('-- %d identities, PIDs %d-%d, purpose %s, channels %s, active %d.' % (
        len(members), pids[0], pids[-1], PURPOSE, a.channels, sum(1 for b in members if b['active'])))
    S.append('SET NAMES latin1;')
    S.append('USE player;')
    S.append("""CREATE TABLE IF NOT EXISTS common.playerbot_yohara_cohort (
  pid INT UNSIGNED NOT NULL PRIMARY KEY, purpose VARCHAR(16) NOT NULL, channel TINYINT UNSIGNED NOT NULL DEFAULT 1,
  rest_until DATETIME NULL, created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  level_start TINYINT UNSIGNED NOT NULL DEFAULT 0, exp_start INT UNSIGNED NOT NULL DEFAULT 0,
  sent INT UNSIGNED NOT NULL DEFAULT 0, arrived INT UNSIGNED NOT NULL DEFAULT 0, deaths INT UNSIGNED NOT NULL DEFAULT 0,
  runs INT UNSIGNED NOT NULL DEFAULT 0, rest_outs INT UNSIGNED NOT NULL DEFAULT 0, exp_gained BIGINT UNSIGNED NOT NULL DEFAULT 0,
  last_map INT NOT NULL DEFAULT 0, last_seen DATETIME NULL, applied_at DATETIME NULL, KEY purpose (purpose)) ENGINE=InnoDB;""")
    S.append('ALTER TABLE common.playerbot_yohara_cohort ADD COLUMN IF NOT EXISTS applied_at DATETIME NULL, '
             'ADD COLUMN IF NOT EXISTS party TINYINT UNSIGNED NOT NULL DEFAULT 0, ADD COLUMN IF NOT EXISTS wins INT UNSIGNED NOT NULL DEFAULT 0, '
             'ADD COLUMN IF NOT EXISTS champion TINYINT UNSIGNED NOT NULL DEFAULT 0, ADD COLUMN IF NOT EXISTS champion_at DATETIME NULL;')
    S.append("""CREATE TABLE IF NOT EXISTS common.playerbot_yohara800 (
  pid INT UNSIGNED NOT NULL PRIMARY KEY, login VARCHAR(16) NOT NULL, name VARCHAR(24) NOT NULL, job TINYINT UNSIGNED NOT NULL,
  skill_group TINYINT UNSIGNED NOT NULL, empire TINYINT UNSIGNED NOT NULL, champion TINYINT UNSIGNED NOT NULL,
  map INT NOT NULL, tier TINYINT UNSIGNED NOT NULL, channel TINYINT UNSIGNED NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, UNIQUE KEY login (login)) ENGINE=InnoDB DEFAULT CHARSET=latin1;""")
    S.append("""CREATE TABLE IF NOT EXISTS player.item_account_bound (
  id INT UNSIGNED NOT NULL PRIMARY KEY, pid INT UNSIGNED NOT NULL DEFAULT 0, vnum INT UNSIGNED NOT NULL DEFAULT 0,
  why VARCHAR(24) NOT NULL DEFAULT '', bound_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, KEY pid (pid))
  ENGINE=InnoDB DEFAULT CHARSET=latin1;""")
    # ---------------- the spec
    S.append('DROP TEMPORARY TABLE IF EXISTS y8_spec;')
    S.append("""CREATE TEMPORARY TABLE y8_spec (
  pid INT UNSIGNED NOT NULL PRIMARY KEY, login VARCHAR(16) NOT NULL, social_id VARCHAR(13) NOT NULL, name VARCHAR(24) NOT NULL,
  seed_name VARCHAR(24) NOT NULL, job TINYINT UNSIGNED NOT NULL, skill_group TINYINT UNSIGNED NOT NULL,
  empire TINYINT UNSIGNED NOT NULL, x INT NOT NULL, y INT NOT NULL, hp INT NOT NULL, mp INT NOT NULL,
  random_hp SMALLINT NOT NULL, random_sp SMALLINT NOT NULL, champion TINYINT UNSIGNED NOT NULL, cpoint SMALLINT NOT NULL,
  s0 SMALLINT NOT NULL, s1 SMALLINT NOT NULL, s2 SMALLINT NOT NULL, s3 SMALLINT NOT NULL, skills VARCHAR(3180) NOT NULL,
  map INT NOT NULL, tier TINYINT UNSIGNED NOT NULL, channel TINYINT UNSIGNED NOT NULL, active TINYINT UNSIGNED NOT NULL,
  UNIQUE KEY login (login), UNIQUE KEY name (name)) ENGINE=InnoDB DEFAULT CHARSET=latin1;""")
    rows = []
    for b in sorted(members, key=lambda b: b['pid']):
        r = b['rng']
        rhp, rsp = 40 * (LEVEL - 1), 20 * (LEVEL - 1)
        hp = H_BASE[b['cls']] + rhp + 90 * 40
        mp = rsp + 90 * 20
        w = b['will']
        rows.append("  (%d, '%s', '%s', %s, 'y8%d', %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, '%s', %d, %d, %d, %d)" % (
            b['pid'], 'playerbot_%03d' % (b['pid'] - 3), '9%012d' % (b['pid'] - 3), sql_str(b['name']), b['pid'], b['job'],
            b['grp'], b['emp'], DONGAN[1] + r.randint(-300, 300), DONGAN[2] + r.randint(-300, 300), hp, mp, rhp, rsp,
            b['champion'], w['left'], w['spend'][0], w['spend'][1], w['spend'][2], w['spend'][3],
            skill_blob(b['cls'], b['grp'], b['skill']), b['map'], b['tier'], b['channel'], 1 if b['active'] else 0))
    for i in range(0, len(rows), 200):
        S.append('INSERT INTO y8_spec VALUES\n' + ',\n'.join(rows[i:i + 200]) + ';')
    S.append('DROP TEMPORARY TABLE IF EXISTS y8_item;')
    S.append("""CREATE TEMPORARY TABLE y8_item (
  owner_id INT UNSIGNED NOT NULL, window VARCHAR(16) NOT NULL, pos SMALLINT UNSIGNED NOT NULL, count INT UNSIGNED NOT NULL,
  vnum INT UNSIGNED NOT NULL, socket0 INT UNSIGNED NOT NULL, socket1 INT UNSIGNED NOT NULL, socket2 INT UNSIGNED NOT NULL,
  attrtype0 TINYINT UNSIGNED NOT NULL, attrvalue0 SMALLINT NOT NULL, attrtype1 TINYINT UNSIGNED NOT NULL, attrvalue1 SMALLINT NOT NULL,
  attrtype2 TINYINT UNSIGNED NOT NULL, attrvalue2 SMALLINT NOT NULL, attrtype3 TINYINT UNSIGNED NOT NULL, attrvalue3 SMALLINT NOT NULL,
  attrtype4 TINYINT UNSIGNED NOT NULL, attrvalue4 SMALLINT NOT NULL, attrtype5 TINYINT UNSIGNED NOT NULL, attrvalue5 SMALLINT NOT NULL,
  attrtype6 TINYINT UNSIGNED NOT NULL, attrvalue6 SMALLINT NOT NULL, PRIMARY KEY (owner_id, window, pos)) ENGINE=InnoDB;""")
    irows = []
    for b in sorted(members, key=lambda b: b['pid']):
        for pos, vnum, count, sock, attrs in b['gear']:
            irows.append("  (%d, 'EQUIPMENT', %d, %d, %d, %d, %d, %d, %s)" % (b['pid'], pos, count, vnum, sock[0], sock[1],
                                                                            sock[2], attrs7(attrs)))
        for pos, vnum, count in b['bag']:
            irows.append("  (%d, 'INVENTORY', %d, %d, %d, 0, 0, 0, %s)" % (b['pid'], pos, count, vnum, attrs7([])))
    for i in range(0, len(irows), 1000):
        S.append('INSERT INTO y8_item VALUES\n' + ',\n'.join(irows[i:i + 1000]) + ';')
    # ---------------- the guards: anybody else's PID, login, social id, index or name stops the file here
    S.append("""DELIMITER //
BEGIN NOT ATOMIC
    DECLARE v INT DEFAULT 0;
    SELECT COUNT(*) INTO v FROM y8_spec s LEFT JOIN common.playerbot_yohara800 l ON l.pid = s.pid
     WHERE l.pid IS NULL AND (EXISTS (SELECT 1 FROM player.player p WHERE p.id = s.pid)
        OR EXISTS (SELECT 1 FROM common.playerbot_seed_state z WHERE z.pid = s.pid)
        OR EXISTS (SELECT 1 FROM account.account a WHERE a.login = s.login OR a.social_id = s.social_id)
        OR EXISTS (SELECT 1 FROM player.player_index i WHERE s.pid IN (i.pid1, i.pid2, i.pid3, i.pid4)));
    IF v <> 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'yohara800: a PID, login, social id or index of the range is somebody else''s';
    END IF;
    SELECT COUNT(*) INTO v FROM y8_spec s JOIN player.player p ON p.name = s.name AND p.id <> s.pid;
    IF v <> 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'yohara800: a name is worn by another character - run the tool again';
    END IF;
    SELECT COUNT(*) INTO v FROM y8_spec s JOIN common.playerbot_name_history h ON (h.human_name = s.name OR h.seed_name = s.name)
     AND h.pid <> s.pid;
    IF v <> 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'yohara800: a name is in the nickname ledger of another bot - run the tool again';
    END IF;
    SELECT COUNT(*) INTO v FROM information_schema.TABLES
     WHERE TABLE_SCHEMA = 'player' AND TABLE_NAME = 'player' AND AUTO_INCREMENT <= (SELECT MAX(pid) FROM y8_spec);
    IF v <> 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'yohara800: the people''s character ids have reached the range';
    END IF;
END//
DELIMITER ;""")
    # ---------------- what to make: no complete ledger row yet; a half made one of ours is cleared first
    S.append('DROP TEMPORARY TABLE IF EXISTS y8_todo;')
    S.append("""CREATE TEMPORARY TABLE y8_todo ENGINE=InnoDB AS
SELECT s.pid, s.login FROM y8_spec s LEFT JOIN common.playerbot_seed_state z ON z.pid = s.pid AND z.state = 'complete'
 WHERE z.pid IS NULL;""")
    S.append("SELECT CONCAT('yohara800: making ', COUNT(*), ' identities (', (SELECT COUNT(*) FROM y8_spec) - COUNT(*), "
             "' made before, left alone)') AS note FROM y8_todo;")
    for t in ("DELETE i FROM player.item i JOIN y8_todo t ON t.pid = i.owner_id WHERE i.window NOT IN ('SAFEBOX', 'MALL');",
              "DELETE b FROM player.item_account_bound b JOIN y8_todo t ON t.pid = b.pid;",
              "DELETE q FROM player.quest q JOIN y8_todo t ON t.pid = q.dwPID;",
              "DELETE x FROM player.player_index x JOIN y8_todo t ON t.pid = x.pid1;",
              "DELETE p FROM player.player p JOIN y8_todo t ON t.pid = p.id;",
              "DELETE a FROM account.account a JOIN y8_todo t ON t.login = a.login WHERE a.password = '!' AND a.status = 'BLOCK';",
              "DELETE h FROM common.playerbot_name_history h JOIN y8_todo t ON t.pid = h.pid;",
              "DELETE c FROM common.playerbot_channel_assignment c JOIN y8_todo t ON t.pid = c.pid;",
              "DELETE c FROM common.playerbot_yohara_cohort c JOIN y8_todo t ON t.pid = c.pid;",
              "DELETE z FROM common.playerbot_seed_state z JOIN y8_todo t ON t.pid = z.pid;"):
        S.append(t)
    S.append("""REPLACE INTO common.playerbot_yohara800 (pid, login, name, job, skill_group, empire, champion, map, tier, channel)
SELECT s.pid, s.login, s.name, s.job, s.skill_group, s.empire, s.champion, s.map, s.tier, s.channel FROM y8_spec s JOIN y8_todo t ON t.pid = s.pid;""")
    S.append("INSERT INTO common.playerbot_seed_state (pid, seed_version, state) SELECT pid, 1, 'pending' FROM y8_todo;")
    S.append('START TRANSACTION;')
    S.append("""INSERT INTO account.account (login, password, social_id, email, create_time, status, availDt, last_play, cash)
SELECT s.login, '!', s.social_id, '', UTC_TIMESTAMP(), 'BLOCK', UTC_TIMESTAMP(), UTC_TIMESTAMP(), %d
  FROM y8_spec s JOIN y8_todo t ON t.pid = s.pid;""" % CASH)
    S.append("""INSERT INTO player.player
  (id, account_id, name, job, voice, dir, x, y, z, map_index, exit_x, exit_y, exit_map_index, hp, mp, stamina, random_hp, random_sp,
   playtime, level, level_step, st, ht, dx, iq, exp, gold, stat_point, skill_point, skill_group, skill_level, sub_skill_point,
   horse_hp, horse_stamina, horse_level, horse_hp_droptime, horse_riding, horse_skill_point, last_play,
   conqueror_level, conqueror_level_step, conqueror_exp, conqueror_point, sungma_str, sungma_hp, sungma_move, sungma_immune)
SELECT s.pid, a.id, s.name, s.job, 0, 0, s.x, s.y, 0, %(map)d, s.x, s.y, %(map)d, s.hp, s.mp, 800, s.random_hp, s.random_sp,
       0, %(L)d, 0, 90, 90, 90, 90, 0, %(G)d, 0, 0, s.skill_group, UNHEX(s.skills), %(sub)d,
       %(hhp)d, %(hst)d, %(hl)d, UNIX_TIMESTAMP(), 0, 0, NOW(),
       s.champion, 0, 0, s.cpoint, s.s0, s.s1, s.s2, s.s3
  FROM y8_spec s JOIN y8_todo t ON t.pid = s.pid JOIN account.account a ON a.login = s.login;""" % dict(
        map=DONGAN[0], L=LEVEL, G=GOLD, sub=LEVEL - 8, hhp=HORSE_HP, hst=HORSE_STAMINA, hl=HORSE_LEVEL))
    S.append("""INSERT INTO player.player_index (id, pid1, pid2, pid3, pid4, empire)
SELECT a.id, s.pid, 0, 0, 0, s.empire FROM y8_spec s JOIN y8_todo t ON t.pid = s.pid JOIN account.account a ON a.login = s.login;""")
    S.append('-- the seed\'s login rewards marked (no starter chest or weapon at the first login), the G0 package given')
    S.append("""INSERT INTO player.quest (dwPID, szName, szState, lValue)
SELECT t.pid, f.n, f.s, 1 FROM y8_todo t CROSS JOIN (SELECT 'give_basic_weapon' n, 'basic_weapon' s UNION ALL SELECT 'starter_chest', 'given'
  UNION ALL SELECT 'mt2009_g0', 'given') AS f WHERE 1
ON DUPLICATE KEY UPDATE lValue = GREATEST(lValue, VALUES(lValue));""")
    S.append("""INSERT INTO player.item (owner_id, window, pos, count, vnum, socket0, socket1, socket2, attrtype0, attrvalue0,
  attrtype1, attrvalue1, attrtype2, attrvalue2, attrtype3, attrvalue3, attrtype4, attrvalue4, attrtype5, attrvalue5, attrtype6, attrvalue6)
SELECT i.owner_id, i.window, i.pos, i.count, i.vnum, i.socket0, i.socket1, i.socket2, i.attrtype0, i.attrvalue0, i.attrtype1,
       i.attrvalue1, i.attrtype2, i.attrvalue2, i.attrtype3, i.attrvalue3, i.attrtype4, i.attrvalue4, i.attrtype5, i.attrvalue5,
       i.attrtype6, i.attrvalue6
  FROM y8_item i JOIN y8_todo t ON t.pid = i.owner_id ORDER BY i.owner_id, i.window, i.pos;""")
    S.append('-- the Sung Ma pieces bound to the account, as the G0 package (playerbot_yohara_g0.cpp)')
    S.append("""INSERT IGNORE INTO player.item_account_bound (id, pid, vnum, why)
SELECT i.id, i.owner_id, i.vnum, 'yohara800' FROM player.item i JOIN y8_todo t ON t.pid = i.owner_id
 WHERE i.window = 'EQUIPMENT' AND ((i.vnum BETWEEN 23000 AND 23039) OR (i.vnum BETWEEN 14580 AND 14619)
    OR (i.vnum BETWEEN 16580 AND 16619) OR (i.vnum BETWEEN 17570 AND 17609) OR i.vnum DIV 10 IN (8100, 8125, 8130, 8155));""")
    S.append("""INSERT INTO common.playerbot_channel_assignment (pid, channel, ready_at)
SELECT s.pid, s.channel, NOW() FROM y8_spec s JOIN y8_todo t ON t.pid = s.pid
ON DUPLICATE KEY UPDATE channel = VALUES(channel), requested_channel = 0, request_reason = '', request_at = NULL, ready_at = NOW();""")
    S.append("""INSERT IGNORE INTO common.playerbot_yohara_cohort (pid, purpose, channel, level_start, created_at, last_map, applied_at, rest_until)
SELECT s.pid, '%s', s.channel, %d, NOW(), s.map, NOW(), IF(s.active, NULL, '2099-01-01 00:00:00')
  FROM y8_spec s JOIN y8_todo t ON t.pid = s.pid;""" % (PURPOSE, LEVEL))
    S.append('COMMIT;')
    S.append("""INSERT INTO common.playerbot_name_history (pid, seed_name, human_name, pool_version, renamed_at)
SELECT s.pid, s.seed_name, s.name, %s, NOW() FROM y8_spec s JOIN y8_todo t ON t.pid = s.pid
ON DUPLICATE KEY UPDATE seed_name = VALUES(seed_name), human_name = VALUES(human_name), pool_version = VALUES(pool_version);""" % sql_str(pool_version))
    S.append("""UPDATE common.playerbot_seed_state z JOIN y8_todo t ON t.pid = z.pid
   JOIN player.player p ON p.id = z.pid JOIN account.account a ON a.id = p.account_id AND a.login = t.login
   JOIN player.player_index x ON x.id = a.id AND x.pid1 = z.pid
   SET z.state = 'complete' WHERE z.state = 'pending';""")
    S.append('DROP TEMPORARY TABLE IF EXISTS y8_todo;')
    S.append('DROP TEMPORARY TABLE IF EXISTS y8_item;')
    S.append('DROP TEMPORARY TABLE IF EXISTS y8_spec;')
    S.append(STATUS)
    open(os.path.join(out, 'cohort_apply.sql'), 'w', encoding='latin-1').write('\n'.join(S) + '\n')

    open(os.path.join(out, 'cohort_status.sql'), 'w').write('SET NAMES latin1;\nUSE common;\n' + STATUS + '\n' + STATUS_LIVE + '\n')
    open(os.path.join(out, 'cohort_activate.sql'), 'w').write('\n'.join([
        '-- MT2009_PLUS_BOT_YOHARA800_V1: the resting rows to work - the cores read the table every minute and the',
        '-- dispatcher sends them (PLAYERBOT_COHORT_DISPATCH a pass). Safe with the game running. A stage: put a LIMIT',
        '-- (e.g. "ORDER BY pid LIMIT 200") on the UPDATE.',
        'SET NAMES latin1;',
        'USE common;',
        "UPDATE common.playerbot_yohara_cohort SET rest_until = NULL WHERE purpose = '%s' AND rest_until > NOW() + INTERVAL 1 YEAR;" % PURPOSE,
        "SELECT channel, COUNT(*) AS members, SUM(IFNULL(rest_until > NOW(), 0)) AS resting FROM common.playerbot_yohara_cohort "
        "WHERE purpose = '%s' GROUP BY channel;" % PURPOSE]) + '\n')
    open(os.path.join(out, 'cohort_dissolve.sql'), 'w').write('\n'.join([
        '-- MT2009_PLUS_BOT_YOHARA800_V1: the 800\'s cohort dissolved - its rows kept in common.playerbot_yohara800_ended.',
        '-- The bots stay registry bots (level 120 Champions of the population: game1 may load them when its slider reaches',
        '-- them). Safe with the game running. cohort_remove.sql takes the identities away altogether (game stopped).',
        'SET NAMES latin1;',
        'USE common;',
        'CREATE TABLE IF NOT EXISTS common.playerbot_yohara800_ended LIKE common.playerbot_yohara_cohort;',
        'START TRANSACTION;',
        'REPLACE INTO common.playerbot_yohara800_ended (pid, purpose, channel, rest_until, created_at, level_start, exp_start, '
        'sent, arrived, deaths, runs, rest_outs, exp_gained, last_map, last_seen, applied_at, party, wins, champion, champion_at)\n'
        '  SELECT pid, purpose, channel, rest_until, created_at, level_start, exp_start, sent, arrived, deaths, runs, rest_outs, '
        "exp_gained, last_map, last_seen, applied_at, party, wins, champion, champion_at FROM common.playerbot_yohara_cohort WHERE purpose = '%s';" % PURPOSE,
        "DELETE h FROM common.playerbot_core_handover h JOIN common.playerbot_yohara_cohort c ON c.pid = h.pid "
        "WHERE h.state = 1 AND c.purpose = '%s';" % PURPOSE,
        "DELETE FROM common.playerbot_yohara_cohort WHERE purpose = '%s';" % PURPOSE,
        'COMMIT;']) + '\n')
    # the removal: every table of player / common / account with the bot's pid, by the ledger
    R = ['-- MT2009_PLUS_BOT_YOHARA800_V1: the 800 identities taken away altogether (their characters, items, quests,',
         '-- affects, accounts, ledger, nickname and channel rows, cohort and handover rows, and every row of the bot',
         '-- tables keyed by their pid). By the ledger common.playerbot_yohara800 only. GAME STOPPED.',
         'SET NAMES latin1;',
         'USE player;',
         'DROP TEMPORARY TABLE IF EXISTS y8_gone;',
         'CREATE TEMPORARY TABLE y8_gone ENGINE=InnoDB AS SELECT l.pid, l.login, a.id AS account_id FROM common.playerbot_yohara800 l '
         'LEFT JOIN account.account a ON a.login = l.login;',
         "SELECT CONCAT('yohara800: removing ', COUNT(*), ' identities') AS note FROM y8_gone;",
         "DELETE i FROM player.item i JOIN y8_gone g ON g.pid = i.owner_id WHERE i.window NOT IN ('SAFEBOX', 'MALL');",
         "DELETE i FROM player.item i JOIN y8_gone g ON g.account_id = i.owner_id WHERE i.window IN ('SAFEBOX', 'MALL');",
         'DELETE x FROM player.item_account_bound x JOIN y8_gone g ON g.pid = x.pid;',
         'DELETE x FROM player.quest x JOIN y8_gone g ON g.pid = x.dwPID;',
         'DELETE x FROM player.affect x JOIN y8_gone g ON g.pid = x.dwPID;',
         'DELETE x FROM player.player_index x JOIN y8_gone g ON g.account_id = x.id;',
         'DELETE x FROM player.player x JOIN y8_gone g ON g.pid = x.id;',
         "DELETE x FROM account.account x JOIN y8_gone g ON g.account_id = x.id WHERE x.password = '!' AND x.status = 'BLOCK';",
         'DELETE x FROM common.playerbot_name_history x JOIN y8_gone g ON g.pid = x.pid;',
         'DELETE x FROM common.playerbot_seed_state x JOIN y8_gone g ON g.pid = x.pid;',
         'DELETE x FROM common.playerbot_channel_assignment x JOIN y8_gone g ON g.pid = x.pid;',
         'DELETE x FROM common.playerbot_core_handover x JOIN y8_gone g ON g.pid = x.pid;',
         'DELETE x FROM common.playerbot_yohara_cohort x JOIN y8_gone g ON g.pid = x.pid;',
         '-- the bot tables (playerbot_*, web_seban_*, guild_member, quest-like tables) keyed by pid, whatever exists',
         'DELIMITER //',
         'BEGIN NOT ATOMIC',
         '    DECLARE done INT DEFAULT 0;',
         '    DECLARE s VARCHAR(64); DECLARE t VARCHAR(64); DECLARE c VARCHAR(64);',
         '    DECLARE cur CURSOR FOR SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME FROM information_schema.COLUMNS',
         "        WHERE TABLE_SCHEMA IN ('player', 'common') AND COLUMN_NAME IN ('pid', 'dwPID', 'player_id', 'sidekick_pid', 'farmer_pid')",
         "          AND TABLE_NAME NOT IN ('item', 'quest', 'affect', 'player', 'player_index', 'playerbot_yohara800')",
         "          AND (TABLE_NAME LIKE 'playerbot\\_%' OR TABLE_NAME LIKE 'web\\_seban\\_%' OR TABLE_NAME IN ('guild_member',",
         "               'weekly_rank_score', 'weekly_rank_title', 'mt2009_rank_points', 'battlepass_progress', 'player_special_flag',",
         "               'switchbot', 'wheel_spin', 'worldboss_damage', 'worldboss_points', 'worldboss_reward', 'messenger_block_list'));",
         '    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;',
         '    OPEN cur;',
         '    l: LOOP',
         '        FETCH cur INTO s, t, c;',
         '        IF done THEN LEAVE l; END IF;',
         "        SET @y8q = CONCAT('DELETE x FROM `', s, '`.`', t, '` x JOIN y8_gone g ON g.pid = x.`', c, '`');",
         '        PREPARE y8s FROM @y8q; EXECUTE y8s; DEALLOCATE PREPARE y8s;',
         '    END LOOP;',
         '    CLOSE cur;',
         'END//',
         'DELIMITER ;',
         'DELETE x FROM common.playerbot_yohara800 x JOIN y8_gone g ON g.pid = x.pid;',
         'DROP TEMPORARY TABLE IF EXISTS y8_gone;',
         "SELECT COUNT(*) AS left_characters FROM player.player WHERE id BETWEEN %d AND %d;" % (pids[0], pids[-1])]
    open(os.path.join(out, 'cohort_remove.sql'), 'w').write('\n'.join(R) + '\n')
    open(os.path.join(out, 'pids.txt'), 'w').write(' '.join(map(str, pids)) + '\n')


H_BASE = {0: 600, 1: 650, 2: 650, 3: 700}     # the class's base hit points (the night tool's estimate)

STATUS = """SELECT y.map, y.tier, COUNT(*) AS bots, MIN(p.conqueror_level) AS champ_min, MAX(p.conqueror_level) AS champ_max,
       SUM(c.pid IS NOT NULL) AS in_cohort, SUM(IFNULL(c.rest_until > NOW(), 0)) AS resting, MIN(p.level) AS lv_min,
       MIN(p.gold) AS gold_min
  FROM common.playerbot_yohara800 y JOIN player.player p ON p.id = y.pid
  LEFT JOIN common.playerbot_yohara_cohort c ON c.pid = y.pid AND c.purpose = '%(P)s'
 GROUP BY y.map, y.tier ORDER BY y.map, y.tier;
SELECT COUNT(*) AS identities, SUM(z.state = 'complete') AS ledger_complete, SUM(ca.channel = 1) AS ch1, SUM(ca.channel = 2) AS ch2,
       SUM(a.cash) AS cash, SUM(p.horse_level = 21) AS horse21
  FROM common.playerbot_yohara800 y JOIN player.player p ON p.id = y.pid JOIN account.account a ON a.id = p.account_id
  LEFT JOIN common.playerbot_seed_state z ON z.pid = y.pid LEFT JOIN common.playerbot_channel_assignment ca ON ca.pid = y.pid;
SELECT i.window, i.vnum, COUNT(DISTINCT i.owner_id) AS bots, SUM(i.count) AS items, MAX(i.count) AS max_stack,
       SUM(i.attrtype0 + i.attrtype1 + i.attrtype2 + i.attrtype3 + i.attrtype4 > 0) AS with_bonuses
  FROM player.item i JOIN common.playerbot_yohara800 y ON y.pid = i.owner_id
 WHERE i.window = 'INVENTORY' OR i.attrtype0 + i.attrtype1 + i.attrtype2 + i.attrtype3 + i.attrtype4 > 0
 GROUP BY i.window, i.vnum ORDER BY i.window, i.vnum;""" % dict(P=PURPOSE)

STATUS_LIVE = """SELECT IFNULL(h.target_map, c.last_map) AS map, COUNT(*) AS members,
       COALESCE(SUM(h.state = 2 AND h.updated_at > NOW() - INTERVAL 180 SECOND), 0) AS on_core3,
       COALESCE(SUM(h.state = 1), 0) AS on_way, SUM(IFNULL(c.rest_until > NOW(), 0)) AS resting,
       SUM(c.deaths) AS deaths, SUM(c.exp_gained) AS exp_gained
  FROM common.playerbot_yohara_cohort c LEFT JOIN common.playerbot_core_handover h ON h.pid = c.pid
 WHERE c.purpose = '%(P)s' GROUP BY 1 ORDER BY 1;""" % dict(P=PURPOSE)


def write_reports(a, members, req, q):
    out = a.outdir
    with open(os.path.join(out, 'pick.tsv'), 'w', encoding='latin-1') as f:
        f.write('pid\tname\tempire\tclass\tpath\tsex\tchannel\tactive\tmap\tmap_name\tchampion\ttier\tpath_skill\t'
                'req_str_hp_move_int\tpoints_str_hp_move_int\tpoints_left\twill_str_hp_move_int_min\tglove\tjade_kinds\ttalisman\tweapon\n')
        KN = 'SHMI'
        for b in sorted(members, key=lambda b: ([m[0] for m in SM.MAPS].index(b['map']), b['champion'], b['pid'])):
            w = b['will']
            wv = [g for g in b['gear'] if g[0] == 4][0][1]
            f.write('%d\t%s\t%d\t%s\t%d\t%s\t%d\t%d\t%d\t%s\t%d\t%s\t%d\t%s\t%s\t%d\t%s\t%d\t%s\t%d\t%d\n' % (
                b['pid'], b['name'], b['emp'], H.CLS[b['cls']], b['grp'], 'k' if b['female'] else 'm', b['channel'],
                1 if b['active'] else 0, b['map'], b['map_name'], b['champion'], TIER_NAME[b['tier']], b['skill'],
                '/'.join(map(str, req[b['map']])), '/'.join(map(str, w['spend'])), w['left'], '/'.join(map(str, w['will'])),
                w['glove'][0], ''.join(KN[w['kinds'][p]] for p in ('bracelet', 'necklace', 'earrings')),
                [p for p in w['pieces'] if p[0] == 25][0][1], wv))
    # the distribution, the env, the memory and the CPU
    existing = collections.Counter()
    for r in q("SELECT channel, COUNT(*) FROM common.playerbot_yohara_cohort WHERE purpose <> '%s' AND purpose = 'yohara' "
               "GROUP BY channel;" % PURPOSE, fatal=False) or []:
        existing[int(r[0])] = int(r[1])
    P = ['MT2009_PLUS_BOT_YOHARA800_V1 - %d new Yohara bots, PIDs %d-%d, channels %s, active at once %d' % (
        len(members), min(b['pid'] for b in members), max(b['pid'] for b in members), a.channels,
        sum(1 for b in members if b['active'])),
         '%-32s %6s %9s %5s %5s %5s %s' % ('map', 'bots', 'champion', 'G0', 'G1', 'G2', 'classes')]
    for m in SM.MAPS:
        ms = [b for b in members if b['map'] == m[0]]
        tiers = collections.Counter(b['tier'] for b in ms)
        P.append('%-32s %6d %9s %5d %5d %5d %s' % ('%d %s' % (m[0], m[1]), len(ms),
                 '%d-%d' % (min(b['champion'] for b in ms), max(b['champion'] for b in ms)) if ms else '-',
                 tiers[0], tiers[1], tiers[2],
                 dict(sorted(collections.Counter('%s%d' % (H.CLS[b['cls']], b['grp']) for b in ms).items()))))
    tiers = collections.Counter(b['tier'] for b in members)
    P.append('tiers: G0 %d, G1 %d, G2 %d (better than G0: %d = %.1f%%; G0 cannot carry it: %d)' % (
        tiers[0], tiers[1], tiers[2], tiers[1] + tiers[2], 100.0 * (tiers[1] + tiers[2]) / len(members),
        sum(1 for b in members if b['need_tier'] > 0)))
    P.append('class/path %s' % dict(sorted(collections.Counter('%s%d' % (H.CLS[b['cls']], b['grp']) for b in members).items())))
    P.append('kingdoms %s, sex m/k %d/%d' % (dict(sorted(collections.Counter(b['emp'] for b in members).items())),
             sum(1 for b in members if not b['female']), sum(1 for b in members if b['female'])))
    P.append('path skills: G1 %d, G2-G10 %d, P %d' % (sum(1 for b in members if b['skill'] == 30),
             sum(1 for b in members if 31 <= b['skill'] <= 39), sum(1 for b in members if b['skill'] == 40)))
    P.append('')
    for ch in sorted(set(b['channel'] for b in members)):
        act = [b for b in members if b['channel'] == ch and b['active']]
        allc = [b for b in members if b['channel'] == ch]
        tot = len(act) + existing[ch]
        per_map = collections.Counter(b['map'] for b in act)
        mx = max(per_map.values()) if per_map else 0
        P.append('channel %d: %d of the 800 (%d active) + %d of "yohara" = %d on its game3 at once at most' % (
            ch, len(allc), len(act), existing[ch], tot))
        P.append('  env: PLAYERBOT_SUNGMA_MAX >= %d (clamp 1000 with MT2009_PLUS_BOT_YOHARA800_V1, 600 before), '
                 'PLAYERBOT_SUNGMA_MAP_MAX >= %d (the busiest map %d of the 800 + the 100\'s; clamp 300)' % (
                     tot + 20, mx + 40, mx))
        P.append('  memory of that game3 (32-bit, 4 GB): ~0.33 GB + the nine grids %d MB + %d bots x %.1f MB = ~%.2f GB' % (
            GRIDS_MB, tot, BOT_MB, 0.33 + (GRIDS_MB + tot * BOT_MB) / 1024.0))
        P.append('  CPU of that game3 (one thread): ~%.0f%% of a core (%.2f%% a Sung Ma resident, measured)' % (
            tot * BOT_CPU_PCT, BOT_CPU_PCT))
    open(os.path.join(out, 'plan.txt'), 'w').write('\n'.join(P) + '\n')
    print('\n'.join(P))
