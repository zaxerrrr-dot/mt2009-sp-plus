"""yohara_bot_cohort_sungma.py - the Yohara maps' cohort (MT2009_PLUS_BOT_YOHARA_MAPS_V1), the part of
tools/yohara_bot_cohort.py that `--yohara N` runs instead of the night's cohorts:

    yohara_bot_cohort.py <outdir> --yohara 100 [--db-container mt2009plustest-db] [--channel 1]

The owner, 22 October 2026: "Przygotuj 100 botow z takim EQ jak do Hydry i wpusc je na mapy Yohary, krok po kroku
bedziemy testowac nawigacje, zabijanie potworow, exp, ich logike. Naucz je, jak sie po nich poruszac, jakie sa
mapy, na jakich poziomach Czempiona maja byc na jakich mapach, jakie statystyki musza miec na kazda mape. Uwaga:
wszystkie boty domyslnie maja miec maksymalny poziom Precyzji. Ten system ich nie dotyczy."

Who: first the bots the Hydra made Champions (common.playerbot_yohara_cohort_ended: purpose 'hydra', champion 2 -
30 on the test world of 22 October), then the pool's highest levels (the night tool's exclusions; a member of
another cohort - active or paused -, or a bot whose backup a dissolved cohort left, is never picked), the eight
class/path pairs in turn and in each the kingdom with the fewest members. Members an earlier run made stay.

The maps (playerbot_yohara_sungma.h, PLAYERBOT_SUNGMA_MAPS): every member gets a map of the nine Sung Ma maps of
the bots, the classes mixed on each (SHARES of 100: Twierdza 10, Dongan 14, Seoganland 12, Namgan 12, Yilad 12,
Wawoz 12, Rozpadlina 10, Schronienie 10, Zejscie 8), a Champion level of that map's cohort range (its band's floor
to the next map's floor less one - so the cores' pick, the highest map whose floor its level reached and whose Will
it has, lands it there) and the Will of the map:

  * the Sung Ma points of its level (3 a level past the first) - Sila, Witalnosc, Odpornosc to the map's, then
    Inteligencja to the map's; what is left stays unspent (conqueror_point) and the core spends it at once toward
    the next map (SpendPlayerBotSungmaPoints - its own test);
  * where the points cannot carry the map (every map past the Twierdza at the cohort's levels): Sung Ma gloves on
    the empty glove slot (26 - the Hydra's gear has none): Rekawice Mocy at the lowest plus whose Will (its range's
    bottom: +4 19 ... +8 39, +9 58) covers the map's Sila, three Kamien Demonow +4 (Witalnosc, Odpornosc,
    Inteligencja +15 each, the stone's socket number apply*10000 + 4000 + 100 + 15); the Twierdza's level-1 bots
    Zwinne Rekawice +0 (Odpornosc 3-7). The glove's own Will is rolled by the core at the first load
    (Mt2009GloveLoad) within its plus's range.

  Inteligencja falls short on the top maps (its penalty halves only the poison / fire / bleeding of the bot's
  blows); Precyzja is none of a bot's business (the cores: every bot P, no miss).

What else: the Hydra's character (tools/yohara_bot_cohort_hydra.py: level 120 and 25% of its experience, the stats
of 120, the path's skills at P, 30 000 000 gold at least) and its gear (gear_inserts: the Zodiac weapon and armour
+9, the 100-level helmet, Tarcza Tytanow, the jewels, Pas Dusz, Ogniste Buty, the sash, the Ice talisman, the
Mythic alchemy, an archer's arrows); a stack of red potions (27003) and a caster's blue (27006) in the bag (the
cores keep the belt full on the map). Champion experience 0, its level step 0.

Idempotent: the rows first (common.playerbot_yohara_cohort, purpose 'yohara'), the character, the Champion level and
the Will changed only while applied_at is NULL, the backup (player.playerbot_yohara_sungma_bak_player /
_bak_item - its own, with the Champion columns, so the Hydra's backup of the same bots stays the Hydra's) taken
once, the gear put back on each run. Writes cohort_apply.sql (game stopped), cohort_dissolve.sql (the rows into
common.playerbot_yohara_sungma_ended - the Hydra's rows of the same bots stay in _cohort_ended, one row a pid; safe
with the game running), cohort_restore.sql (game stopped), pick.tsv, pids.txt and plan.txt (the distribution and
the memory estimate).
"""
import os, sys, collections

import yohara_bot_cohort_hydra as H

# map, name, the cohort's Champion range (the band's floor .. the next map's floor - 1), its share of 100
MAPS = [
    (374, 'Opuszczona Twierdza', 1, 2, 10),
    (373, 'Dongan', 3, 5, 14),
    (376, 'Seoganland', 6, 7, 12),
    (377, 'Namgan', 8, 11, 12),
    (385, 'Przelecz Yilad', 12, 14, 12),
    (388, 'Wawoz Polnocnego Wiatru', 15, 17, 12),
    (389, 'Rozpadlina Dusz', 18, 21, 10),
    (393, 'Schronienie Polnocnego Wiatru', 22, 25, 10),
    (394, 'Zejscie Polnocnego Wiatru', 26, 30, 8),
]
MAP_FILE = {374: 'metin2_map_empirecastle', 373: 'metin2_map_eastplain_01', 376: 'metin2_map_eastplain_02',
            377: 'metin2_map_eastplain_03', 385: 'metin2_map_snakevalley', 388: 'metin2_map_icecrystalcave',
            389: 'metin2_map_whitdragonvalley', 393: 'metin2_map_whitedragoncave_01', 394: 'metin2_map_whitedragoncave_02'}
# the grid of each map on the Yohara core (playerbot_navigation.h: 17 B a 50-unit cell), MB
GRID_MB = {374: 18, 373: 89, 376: 80, 377: 36, 385: 80, 388: 89, 389: 40, 393: 160, 394: 40}
BOT_MB = 1.7
PURPOSE = 'yohara'

GLOVE_STR, GLOVE_MOVE = 23000, 23010      # Rekawice Mocy, Zwinne Rekawice +0 (+k = +k)
GLOVE_MIN = (3, 5, 9, 14, 19, 24, 29, 34, 39, 58)   # the bottom of each plus's Will (playerbot_yohara_gear.cpp)
STONE = {1: 185, 2: 186, 3: 187}          # Witalnosc, Odpornosc, Inteligencja: POINT_SUNGMA_HP / MOVE / IMMUNE
STONE_WILL = 15                           # Kamien Demonow +4
POT_RED, POT_BLUE = 27003, 27006
EQ_POS = H.EQ_POS + ',26'
KIT_VNUMS = '%d,%d' % (POT_RED, POT_BLUE)


def requirements(repo):
    """sungma_table.txt (the cores read it): map name -> (str, hp, move, immune)."""
    req = {}
    path = os.path.join(repo, 'linux-port', 'docker', 'game', 'champion', 'sungma_table.txt')
    for l in open(path, errors='replace'):
        p = l.split()
        if len(p) >= 5 and not p[0].startswith('#'):
            req[p[0]] = tuple(int(x) for x in p[1:5])
    return {m: req[MAP_FILE[m]] for m in MAP_FILE}


def plan_will(req, level):
    """The Will a member of this level gets for a map of these requirements: (points str/hp/move/immune, left, glove
    (vnum, plus) or None, stones [(point, value)])."""
    s, h, mv, i = req
    pts = 3 * (level - 1)
    glove = None
    stones = []
    have = [0, 0, 0, 0]
    if pts < s + h + mv:
        if s > 0:
            plus = next((k for k in range(10) if GLOVE_MIN[k] >= s), 9)
            glove = (GLOVE_STR + plus, plus)
            have[0] = GLOVE_MIN[plus]
            for idx, need in ((1, h), (2, mv), (3, i)):
                if need > 0:
                    stones.append((STONE[idx], STONE_WILL))
                    have[idx] += STONE_WILL
        elif mv > 0:
            glove = (GLOVE_MOVE, 0)
            have[2] = GLOVE_MIN[0]
    spend = [0, 0, 0, 0]
    left = pts
    for idx, need in ((0, s), (2, mv), (1, h), (3, i)):
        n = min(left, max(0, need - have[idx]), 90)
        spend[idx] = n
        left -= n
    short = [idx for idx, need in enumerate((s, h, mv)) if have[idx] + spend[idx] < need]
    if short:
        sys.exit('yohara cohort: level %d cannot carry %s (short of %s)' % (level, req, short))
    return spend, left, glove, stones, have


def run(a, q, bots, excluded, cohort_pids, usable, repo):
    want = a.yohara
    # ------------------------------------------------------------ who
    earlier = set(int(r[0]) for r in q("SELECT pid FROM common.playerbot_yohara_cohort WHERE purpose = '%s';" % PURPOSE,
                                         fatal=False) or [] if r and r[0].isdigit())
    champions = set(int(r[0]) for r in q("SELECT pid FROM common.playerbot_yohara_cohort_ended "
                                         "WHERE purpose = 'hydra' AND champion = 2;", fatal=False) or [] if r and r[0].isdigit())
    stale = set(int(r[0]) for r in q('SELECT id FROM player.playerbot_yohara_cohort_bak_player;', fatal=False) or []
                if r and r[0].isdigit())
    taken = set(cohort_pids) - earlier          # another cohort's (active or paused)
    members = [bots[p] for p in sorted(earlier) if p in bots]
    have = set(b['pid'] for b in members)
    hydra_kept = 0
    for p in sorted(champions, key=lambda p: (-bots[p]['old'], p) if p in bots else (0, p)):
        if len(members) >= want:
            break
        b = bots.get(p)
        if not b or p in have or p in taken or p in excluded or not usable(b):
            continue
        members.append(b)
        have.add(p)
        hydra_kept += 1
    # the pool: the highest levels, the class/path pairs in turn, the kingdom with the fewest
    pool = collections.defaultdict(list)
    for b in sorted(bots.values(), key=lambda b: (-b['old'], b['pid'])):
        p = b['pid']
        if p in have or p in taken or p in excluded or (p in stale and p not in champions) or not usable(b):
            continue
        pool[(b['cls'], b['grp'])].append(b)
    pairs = [(c, g) for c in range(4) for g in (1, 2)]
    turn = 0
    while len(members) < want and any(pool[pr] for pr in pairs):
        pr = pairs[turn % len(pairs)]
        turn += 1
        if not pool[pr]:
            continue
        cnt = collections.Counter(b['emp'] for b in members)
        lst = pool[pr]
        best = min(range(min(len(lst), 12)), key=lambda k: (cnt[lst[k]['emp']], k))
        members.append(lst.pop(best))
    if len(members) < want:
        print('WARNING: yohara - only %d of %d members found' % (len(members), want))

    # ------------------------------------------------------------ the maps
    shares = [m[4] for m in MAPS]
    count = [int(round(want * s / 100.0)) for s in shares]
    while sum(count) > len(members):
        count[count.index(max(count))] -= 1
    while sum(count) < len(members):
        count[shares.index(max(shares))] += 1
    slots = []
    left = list(count)
    while any(left):
        for i in range(len(MAPS)):
            if left[i]:
                slots.append(i)
                left[i] -= 1
    req = requirements(repo)
    order = sorted(members, key=lambda b: (b['cls'], b['grp'], b['emp'], b['pid']))
    plan = {}
    for b, slot in zip(order, slots):
        mapidx, name, lo, hi, _ = MAPS[slot]
        level = lo + b['pid'] % (hi - lo + 1)
        spend, left_pts, glove, stones, items = plan_will(req[mapidx], level)
        plan[b['pid']] = dict(map=mapidx, name=name, level=level, spend=spend, left=left_pts, glove=glove, stones=stones,
                              items=items, req=req[mapidx])

    # ------------------------------------------------------------ SQL
    ctx = H.gear_context(q)
    for v in (GLOVE_STR, GLOVE_STR + 9, GLOVE_MOVE, POT_RED, POT_BLUE):
        if v not in ctx['proto']:
            sys.exit('item %d is not in item_proto' % v)
    pids = sorted(plan)
    plist = ','.join(str(x) for x in pids) or '0'
    S = []
    S.append('-- MT2009_PLUS_BOT_YOHARA_MAPS_V1: the Yohara maps\' cohort (tools/yohara_bot_cohort.py --yohara). Game stopped.')
    S.append('-- %d members (%d Hydra Champions), maps %s' % (len(plan), hydra_kept,
             dict(collections.Counter(p['map'] for p in plan.values()))))
    S.append('SET NAMES latin1;')
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
    # (exp unsigned as player.exp - a 120's bar passes 2^31)
    S.append("""CREATE TABLE IF NOT EXISTS player.playerbot_yohara_sungma_bak_player (
  id INT UNSIGNED NOT NULL PRIMARY KEY, level TINYINT UNSIGNED NOT NULL, exp INT UNSIGNED NOT NULL, level_step TINYINT NOT NULL,
  st SMALLINT NOT NULL, ht SMALLINT NOT NULL, dx SMALLINT NOT NULL, iq SMALLINT NOT NULL, stat_point SMALLINT NOT NULL,
  skill_point SMALLINT NOT NULL, sub_skill_point SMALLINT NOT NULL, random_hp SMALLINT NOT NULL, random_sp SMALLINT NOT NULL,
  gold BIGINT NOT NULL, skill_level BLOB NULL, conqueror_level TINYINT UNSIGNED NOT NULL, conqueror_level_step TINYINT UNSIGNED NOT NULL,
  conqueror_exp INT UNSIGNED NOT NULL, conqueror_point SMALLINT NOT NULL, sungma_str SMALLINT NOT NULL, sungma_hp SMALLINT NOT NULL,
  sungma_move SMALLINT NOT NULL, sungma_immune SMALLINT NOT NULL, channel_old TINYINT UNSIGNED NULL, saved_at DATETIME NOT NULL) ENGINE=InnoDB;""")
    S.append('CREATE TABLE IF NOT EXISTS player.playerbot_yohara_sungma_bak_item LIKE player.item;')
    S.append('START TRANSACTION;')
    if plan:
        S.append('INSERT IGNORE INTO common.playerbot_yohara_cohort (pid, purpose, channel, level_start, created_at, last_map) VALUES')
        S.append(',\n'.join("  (%d, '%s', %d, %d, NOW(), %d)" % (p, PURPOSE, a.channel, H.LEVEL, plan[p]['map']) for p in pids) + ';')
    S.append('-- the backups, once a member (applied_at still NULL, not backed up yet)')
    S.append("""INSERT IGNORE INTO player.playerbot_yohara_sungma_bak_player
SELECT p.id, p.level, p.exp, p.level_step, p.st, p.ht, p.dx, p.iq, p.stat_point, p.skill_point, p.sub_skill_point,
       p.random_hp, p.random_sp, p.gold, p.skill_level, p.conqueror_level, p.conqueror_level_step, p.conqueror_exp,
       p.conqueror_point, p.sungma_str, p.sungma_hp, p.sungma_move, p.sungma_immune, ca.channel, NOW()
  FROM player.player p JOIN common.playerbot_yohara_cohort c ON c.pid = p.id AND c.applied_at IS NULL AND c.purpose = '%s'
  LEFT JOIN common.playerbot_channel_assignment ca ON ca.pid = p.id;""" % PURPOSE)
    S.append("""INSERT IGNORE INTO player.playerbot_yohara_sungma_bak_item
SELECT i.* FROM player.item i JOIN common.playerbot_yohara_cohort c ON c.pid = i.owner_id AND c.applied_at IS NULL AND c.purpose = '%s'
 WHERE ((i.window = 'EQUIPMENT' AND i.pos IN (%s)) OR (i.window = 'INVENTORY' AND i.vnum IN (%s)))
   AND i.owner_id NOT IN (SELECT DISTINCT owner_id FROM player.playerbot_yohara_sungma_bak_item);""" % (PURPOSE, EQ_POS, KIT_VNUMS))
    S.append('-- the characters (only while applied_at is NULL; level last - MariaDB assigns left to right) and their Champion')
    L, G, E = H.LEVEL, H.GOLD, H.EXP
    for p in pids:
        b = bots[p]
        pl = plan[p]
        S.append("""UPDATE player.player p JOIN common.playerbot_yohara_cohort c ON c.pid = p.id AND c.applied_at IS NULL
   SET p.stat_point = IF(p.level < %(L)d, 0, GREATEST(p.stat_point, LEAST(3 * (p.level - 1), 344) - (p.st + p.ht + p.dx + p.iq - 16))),
       p.st = IF(p.level < %(L)d, 90, p.st), p.ht = IF(p.level < %(L)d, 90, p.ht),
       p.dx = IF(p.level < %(L)d, 90, p.dx), p.iq = IF(p.level < %(L)d, 90, p.iq),
       p.sub_skill_point = p.sub_skill_point + GREATEST(0, %(L)d - GREATEST(p.level, 8)),
       p.random_hp = GREATEST(p.random_hp, 40 * (%(L)d - 1)), p.random_sp = GREATEST(p.random_sp, 20 * (%(L)d - 1)),
       p.gold = GREATEST(p.gold, %(G)d), p.skill_level = UNHEX('%(blob)s'),
       p.exp = GREATEST(IF(p.level < %(L)d, 0, p.exp), %(E)d), p.level_step = IF(p.level < %(L)d, 0, p.level_step),
       p.conqueror_level = %(cl)d, p.conqueror_level_step = 0, p.conqueror_exp = 0, p.conqueror_point = %(cp)d,
       p.sungma_str = %(s0)d, p.sungma_hp = %(s1)d, p.sungma_move = %(s2)d, p.sungma_immune = %(s3)d,
       p.level = GREATEST(p.level, %(L)d)
 WHERE p.id = %(pid)d;""" % dict(L=L, G=G, E=E, blob=H.skills_for(b), pid=p, cl=pl['level'], cp=pl['left'],
                                 s0=pl['spend'][0], s1=pl['spend'][1], s2=pl['spend'][2], s3=pl['spend'][3]))
    S.append("""INSERT INTO common.playerbot_channel_assignment (pid, channel, ready_at) SELECT c.pid, %d, NOW()
  FROM common.playerbot_yohara_cohort c WHERE c.applied_at IS NULL AND c.purpose = '%s'
ON DUPLICATE KEY UPDATE channel = VALUES(channel), requested_channel = 0, request_reason = '', request_at = NULL, ready_at = NOW();""" % (a.channel, PURPOSE))
    S.append("UPDATE common.playerbot_yohara_cohort c JOIN player.player p ON p.id = c.pid SET c.applied_at = NOW(), "
             "c.level_start = p.level, c.exp_start = p.exp WHERE c.applied_at IS NULL AND c.purpose = '%s';" % PURPOSE)
    S.append('-- the equipment (the Hydra\'s, and the Sung Ma gloves where the points cannot carry the map) and the potions (every run)')
    S.append("DELETE FROM player.item WHERE window = 'EQUIPMENT' AND pos IN (%s) AND owner_id IN (%s);" % (EQ_POS, plist))
    S.append("DELETE FROM player.item WHERE window = 'INVENTORY' AND vnum IN (%s) AND owner_id IN (%s);" % (KIT_VNUMS, plist))
    ins = []
    rows = []
    for p in pids:
        b = dict(bots[p])
        g, wv = H.gear_inserts(ctx, b)
        ins.extend(g)
        pl = plan[p]
        if pl['glove']:
            sock = [pt * 10000 + 4 * 1000 + 100 + val for pt, val in pl['stones']] + [0, 0, 0]
            ins.append("  (%d, 'EQUIPMENT', 26, 1, %d, %d, %d, %d, %s)" % (p, pl['glove'][0], sock[0], sock[1], sock[2], H.attrs7([])))
        rows.append((b, wv))
    S.append('INSERT INTO player.item (owner_id, window, pos, count, vnum, socket0, socket1, socket2, '
             'attrtype0, attrvalue0, attrtype1, attrvalue1, attrtype2, attrvalue2, attrtype3, attrvalue3, '
             'attrtype4, attrvalue4, attrtype5, attrvalue5, attrtype6, attrvalue6) VALUES\n' + ',\n'.join(ins) + ';')
    S.append('-- the bag: 200 red potions, a caster\'s 200 blue - each in the first free cell of the bag\'s four pages')
    cell = """INSERT INTO player.item (owner_id, window, pos, count, vnum, socket0, socket1, socket2)
WITH RECURSIVE n(pos) AS (SELECT 0 UNION ALL SELECT pos + 1 FROM n WHERE pos < 179)
SELECT %(pid)d, 'INVENTORY', MIN(n.pos), %(count)d, %(vnum)d, 0, 0, 0 FROM n
 WHERE NOT EXISTS (SELECT 1 FROM player.item i JOIN player.item_proto ip ON ip.vnum = i.vnum
                    WHERE i.owner_id = %(pid)d AND i.window = 'INVENTORY' AND n.pos >= i.pos
                      AND n.pos < i.pos + 5 * GREATEST(ip.size, 1) AND (n.pos - i.pos) %% 5 = 0)
HAVING MIN(n.pos) IS NOT NULL;"""
    for b, wv in rows:
        S.append(cell % dict(pid=b['pid'], count=200, vnum=POT_RED))
        if H.caster(b['cls'], b['grp']):
            S.append(cell % dict(pid=b['pid'], count=200, vnum=POT_BLUE))
    S.append('COMMIT;')
    S.append("SELECT c.last_map AS map, COUNT(*) AS members, MIN(p.conqueror_level) AS champion_min, MAX(p.conqueror_level) AS champion_max, "
             "MIN(p.level) AS lv_min, SUM(c.applied_at IS NOT NULL) AS applied FROM common.playerbot_yohara_cohort c "
             "JOIN player.player p ON p.id = c.pid WHERE c.purpose = '%s' GROUP BY c.last_map;" % PURPOSE)
    S.append("SELECT COUNT(*) AS gear_rows, SUM(pos = 26) AS gloves FROM player.item WHERE window = 'EQUIPMENT' AND pos IN (%s) "
             "AND owner_id IN (%s);" % (EQ_POS, plist))
    open(os.path.join(a.outdir, 'cohort_apply.sql'), 'w', encoding='latin-1').write('\n'.join(S) + '\n')

    D = ['-- MT2009_PLUS_BOT_YOHARA_MAPS_V1: the Yohara maps\' cohort dissolved - its rows kept in',
         '-- common.playerbot_yohara_sungma_ended (its own: common.playerbot_yohara_cohort_ended keeps the Hydra\'s rows of the',
         '-- same bots - one row a pid); the bots keep level, gear, Champion level and Will',
         '-- and stay bot Champions of the population (the Sung Ma maps by PLAYERBOT_SUNGMA_MAX). Safe with the game running.',
         'SET NAMES latin1;',
         'USE common;',
         'CREATE TABLE IF NOT EXISTS common.playerbot_yohara_sungma_ended LIKE common.playerbot_yohara_cohort;',
         'ALTER TABLE common.playerbot_yohara_sungma_ended ADD COLUMN IF NOT EXISTS party TINYINT UNSIGNED NOT NULL DEFAULT 0, '
         'ADD COLUMN IF NOT EXISTS wins INT UNSIGNED NOT NULL DEFAULT 0, ADD COLUMN IF NOT EXISTS champion TINYINT UNSIGNED NOT NULL DEFAULT 0, '
         'ADD COLUMN IF NOT EXISTS champion_at DATETIME NULL;',
         'START TRANSACTION;',
         'REPLACE INTO common.playerbot_yohara_sungma_ended (pid, purpose, channel, rest_until, created_at, level_start, exp_start, '
         'sent, arrived, deaths, runs, rest_outs, exp_gained, last_map, last_seen, applied_at, party, wins, champion, champion_at)\n'
         '  SELECT pid, purpose, channel, rest_until, created_at, level_start, exp_start, sent, arrived, deaths, runs, rest_outs, '
         "exp_gained, last_map, last_seen, applied_at, party, wins, champion, champion_at FROM common.playerbot_yohara_cohort WHERE purpose = '%s';" % PURPOSE,
         "DELETE h FROM common.playerbot_core_handover h JOIN common.playerbot_yohara_cohort c ON c.pid = h.pid "
         "WHERE h.state = 1 AND c.purpose = '%s';" % PURPOSE,
         "DELETE FROM common.playerbot_yohara_cohort WHERE purpose = '%s';" % PURPOSE,
         'COMMIT;']
    open(os.path.join(a.outdir, 'cohort_dissolve.sql'), 'w').write('\n'.join(D) + '\n')

    R = ['-- MT2009_PLUS_BOT_YOHARA_MAPS_V1: the Yohara maps\' members back as they were before the first apply (level, stats,',
         '-- skills, gold, channel, Champion level and Will, the gear and the potions replaced). Game stopped.',
         'SET NAMES latin1;',
         'USE player;',
         'START TRANSACTION;',
         """UPDATE player.player p JOIN player.playerbot_yohara_sungma_bak_player b ON b.id = p.id
   SET p.exp = b.exp, p.level_step = b.level_step, p.st = b.st, p.ht = b.ht, p.dx = b.dx, p.iq = b.iq,
       p.stat_point = b.stat_point, p.skill_point = b.skill_point, p.sub_skill_point = b.sub_skill_point,
       p.random_hp = b.random_hp, p.random_sp = b.random_sp, p.gold = b.gold, p.skill_level = b.skill_level,
       p.conqueror_level = b.conqueror_level, p.conqueror_level_step = b.conqueror_level_step, p.conqueror_exp = b.conqueror_exp,
       p.conqueror_point = b.conqueror_point, p.sungma_str = b.sungma_str, p.sungma_hp = b.sungma_hp,
       p.sungma_move = b.sungma_move, p.sungma_immune = b.sungma_immune, p.level = b.level
 WHERE p.id IN (%s);""" % plist,
         """UPDATE common.playerbot_channel_assignment ca JOIN player.playerbot_yohara_sungma_bak_player b ON b.id = ca.pid
   SET ca.channel = b.channel_old WHERE b.channel_old IS NOT NULL AND ca.pid IN (%s);""" % plist,
         """DELETE FROM player.item WHERE owner_id IN (%s)
   AND ((window = 'EQUIPMENT' AND pos IN (%s)) OR (window = 'INVENTORY' AND vnum IN (%s)));""" % (plist, EQ_POS, KIT_VNUMS),
         'INSERT IGNORE INTO player.item SELECT * FROM player.playerbot_yohara_sungma_bak_item WHERE owner_id IN (%s);' % plist,
         'DELETE FROM common.playerbot_core_handover WHERE pid IN (%s);' % plist,
         "DELETE FROM common.playerbot_yohara_cohort WHERE purpose = '%s';" % PURPOSE,
         'DELETE FROM player.playerbot_yohara_sungma_bak_player WHERE id IN (%s);' % plist,
         'DELETE FROM player.playerbot_yohara_sungma_bak_item WHERE owner_id IN (%s);' % plist,
         'COMMIT;']
    open(os.path.join(a.outdir, 'cohort_restore.sql'), 'w').write('\n'.join(R) + '\n')

    with open(os.path.join(a.outdir, 'pick.tsv'), 'w', encoding='latin-1') as f:
        f.write('pid\tname\tempire\tclass\tpath\tlevel_before\thydra_champion\tmap\tmap_name\tchampion\treq_str_hp_move_int\t'
                'points_str_hp_move_int\tpoints_left\tglove\tstones\twill_str_hp_move_int_min\n')
        for p in sorted(plan, key=lambda p: (plan[p]['map'] != 374, [m[0] for m in MAPS].index(plan[p]['map']), p)):
            b, pl = bots[p], plan[p]
            will = [pl['items'][k] + pl['spend'][k] for k in range(4)]
            f.write('%d\t%s\t%d\t%s\t%d\t%d\t%d\t%d\t%s\t%d\t%s\t%s\t%d\t%s\t%s\t%s\n' % (
                p, b['name'], b['emp'], H.CLS[b['cls']], b['grp'], b['old'], 1 if p in champions else 0, pl['map'], pl['name'],
                pl['level'], '/'.join(map(str, pl['req'])), '/'.join(map(str, pl['spend'])), pl['left'],
                ('%d(+%d)' % pl['glove']) if pl['glove'] else '-', ','.join('%d+%d' % s for s in pl['stones']) or '-',
                '/'.join(map(str, will))))
    open(os.path.join(a.outdir, 'pids.txt'), 'w').write(' '.join(map(str, pids)) + '\n')
    # the distribution and the memory of the Yohara core
    P = ['MT2009_PLUS_BOT_YOHARA_MAPS_V1 - the Yohara maps\' cohort: %d members (%d Hydra Champions kept)' % (len(plan), hydra_kept),
         '%-32s %7s %9s %10s %8s %s' % ('map', 'members', 'champion', 'grid MB', 'bots MB', 'classes')]
    tot_grid = 0
    for m in MAPS:
        ms = [p for p in plan if plan[p]['map'] == m[0]]
        tot_grid += GRID_MB[m[0]]
        P.append('%-32s %7d %9s %10d %8.0f %s' % ('%d %s' % (m[0], m[1]), len(ms), '%d-%d' % (m[2], m[3]), GRID_MB[m[0]],
                 len(ms) * BOT_MB, dict(sorted(collections.Counter('%s%d' % (H.CLS[bots[p]['cls']], bots[p]['grp']) for p in ms).items()))))
    P.append('kingdoms %s' % dict(sorted(collections.Counter(bots[p]['emp'] for p in plan).items())))
    P.append('the Yohara core (game3), each channel with the cohort: ~0.33 GB today + the grids %d MB + %d bots x %.1f MB = ~%.2f GB '
             '(+ Zaklety/SZC/the pier ~150 MB when those run) of the 32-bit core\'s 4 GB; game1: the members held there '
             '(not loaded) cost it nothing.' % (tot_grid, len(plan), BOT_MB, 0.33 + (tot_grid + len(plan) * BOT_MB) / 1024.0))
    open(os.path.join(a.outdir, 'plan.txt'), 'w').write('\n'.join(P) + '\n')
    print('\n'.join(P))
