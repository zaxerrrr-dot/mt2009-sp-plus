#!/usr/bin/env python3
"""yohara_bot_cohort.py - picks, raises and equips the night's bot cohorts
(MT2009_PLUS_BOT_YOHARA_COHORT_V1, playerbot_yohara_bots.h) on the test server.

The owner, 21 October 2026 (night): "Kohorty na noc: 100 botow Zaklety Las
(super EQ, rozne klasy), 100 botow lvl 110 na SZC Zaklety Las (rozne klasy),
2 x 50 botow: Wezowe Pole i Kraina Gigantow."

    yohara_bot_cohort.py <outdir> [--zaklety 100] [--szc 100] [--snakefield 50] [--giantland 50]
                                  [--db-container mt2009plustest-db] [--channel 1]
    yohara_bot_cohort.py <outdir> --hydra 32 [--db-container ...] [--channel 1]
    yohara_bot_cohort.py <outdir> --hydra-pairs 16 [--db-container ...] [--channel 1]
    yohara_bot_cohort.py <outdir> --hydra-end
    yohara_bot_cohort.py <outdir> --yohara 100 [--db-container ...] [--channel 1]
    yohara_bot_cohort.py <outdir> --yohara800 800 [--channels 1] [--active 800] [--pid-base 6001] [--cor-vnum 51510]

MT2009_PLUS_BOT_YOHARA800_V1: --yohara800 N makes N NEW bot identities for the Yohara maps (tools/yohara_bot_cohort_800.py:
made as the seed makes a bot, PIDs 6001.., names from the nickname pool; level 120, Champion 1-30 over the nine Sung Ma
maps, G0 gear and some better, no bonuses, the bonus / alchemy bag; purpose 'yohara800') and touches no registry bot.

MT2009_PLUS_BOT_YOHARA_MAPS_V1: --yohara N makes the Yohara maps' cohort (tools/yohara_bot_cohort_sungma.py: the Hydra's
Champions first, then the pool; level 120, a Champion level and the Sung Ma Will of one of the nine Sung Ma maps
of the bots, the Hydra's gear, Sung Ma gloves where the points cannot carry the map; its own backup tables) and
touches no other cohort.

MT2009_PLUS_BOT_CHAMPION_V1: --hydra-end writes, and touches nothing else (no database read):
  hydra_end.sql            the Hydra's test over (the owner, 22 October): every Hydra member's row gets
                           champion = 1 (a won run, no Champion level: the statue's errand ahead) or 3 (nothing to
                           go there for); the cores read it within a minute - no new ship, the members on the pier
                           (and the ones at home, sent there) walk to Posag Wojownika (20433) and become Champions
                           (playerbot_yohara_bots.h, ManagePlayerBotYoharaChampion), then go home as ordinary bots.
                           Safe with the game running. (The same switch live: event flag m2_bot_hydra_end 1.)
  hydra_champion_status.sql  the errand's progress: champion 1 pending, 2 a Champion, 3 done without it, and the
                           characters' conqueror_level.
  hydra_dissolve_ended.sql the cohort's rows into common.playerbot_yohara_cohort_ended (the backup, as the other
                           cohorts') and out of the cohort table, with their open handover requests; the bots keep
                           level, gear and Champion level. Run it when the status shows no 1 left.

MT2009_PLUS_BOT_HYDRA_COHORT_V1: --hydra N makes the Hydra's cohort instead (tools/yohara_bot_cohort_hydra.py:
four fixed parties of eight, level 120 and a quarter of its experience, the Hydra's gear and kit) and touches
no other cohort. MT2009_PLUS_BOT_HYDRA_PAIRS_V1: --hydra-pairs N re-plans the Hydra's cohort as N pairs (a Ninja
and another class of one kingdom), keeps the members that fit, releases the rest (cohort_release.sql, also the
head of cohort_apply.sql: back as they were before the first apply) and picks replacements. Either way a member of another cohort - active, or set aside in
common.playerbot_yohara_cohort_paused - is never picked.

Reads the world's database (read-only, `docker exec <db-container> mariadb`)
and writes to <outdir>:

  pick.tsv             the members: pid, name, class, path, sex, kingdom, level
                       before/after, purpose, the gear's level, an estimate of
                       their max HP with the new gear;
  cohort_apply.sql     the change (idempotent, see below) - run it with the game
                       stopped (the db core caches characters and would write
                       its copy back);
  cohort_dissolve.sql  the cohorts gone: the table's rows and their handover
                       rows; the bots keep their levels and gear and go back to
                       the population (safe while the game runs: the cores
                       read the table every minute);
  cohort_restore.sql   dissolve + every member's level, experience, stats,
                       skills, gold, channel and replaced equipment back from
                       the backup taken by the first apply (game stopped).

Who: existing bot identities of the registry (playerbot_* accounts, seed state
complete/adopted, the account's first character), with a skill path chosen;
never a guild's leader, a companion, a shouter, one of the 27 Legends (tier
3-4), a farmer at work, a takeover, a retirement pick or an Arezzo cohort's
member; moved to --channel (1) if it was on another. Not under --min-raise (70). Their identity (name, class, kingdom, guild) stays.
No new characters: the registry (4500 identities on the test world) is the
seed's (generate_seed.py) and holds enough bots of every class and kingdom;
the Time Rift's cohort takes the highest levels (110-119 as they are, the
rest raised to 110), the forest's the next ones (100-109 as they are, the
rest raised to 100-105), so a level jump is as small as the registry allows.
Wezowe Pole / Kraina Gigantow take bots already in their bands (66-76 /
66-78), levels unchanged. Each cohort: the eight class-and-path pairs in equal
shares, both sexes and the three kingdoms in turn.

What (a member raised to its level): experience 0, the stats of a bot of that
level (three at 90, the class's fourth with the rest: INT for a Warrior or a
Ninja, STR for a Sura or a Shaman), the hit and spell points the levels roll
on average, the sub-skill points; every member: its path's six skills to
Master (the forest M5-M9, the Time Rift M8-M10 and now and then G1-G2,
Wezowe Pole / Kraina M1-M4 - a learned skill is never lowered), 20 000 000
gold at least (the belt is bought where it stands), and its equipment:
armour, helmet, boots, bracelet, weapon, necklace, earrings and shield +9 -
the highest of what the bots of its class and path wear (the world's own
items) that its level can wear - with five bonuses each at their top value
(against Demons for the forest and the Time Rift - the En-Tai are DEVIL -,
against Animals for Wezowe Pole / Kraina; max HP, critical, piercing, attack
speed, HP regeneration...), the weapon's and the armour's three spirit
stones, the element talisman of its map (Wind - ATT_TEMPLE - for the forest
and the Time Rift, Earth for Wezowe Pole / Kraina; the highest plus its level
can wear, at most +150), and seven alchemy stones (Legendary / Ancient,
highest step, the bonuses the world's stones of that kind carry; the Jade
with max HP and max HP %); arrows for an archer that has none; the Time
Rift's members 30 Zegarek Kieszonkowy in the bag.

Idempotent: the members go into common.playerbot_yohara_cohort first (the
cores' table); a character changes only while its applied_at is NULL, and
its backup (player.playerbot_yohara_cohort_bak_player / _bak_item) is taken
only once; the gear rows are deleted and put back each time. Run it again with
bigger numbers to add members.
"""
import sys, os, subprocess, argparse, collections, random

ap = argparse.ArgumentParser()
ap.add_argument('outdir')
ap.add_argument('--zaklety', type=int, default=100)
ap.add_argument('--szc', type=int, default=100)
ap.add_argument('--snakefield', type=int, default=50)
ap.add_argument('--giantland', type=int, default=50)
ap.add_argument('--db-container', default='mt2009plustest-db')
ap.add_argument('--channel', type=int, default=1)
ap.add_argument('--min-raise', type=int, default=70, help='the lowest level raised to the forest / the Time Rift')
ap.add_argument('--hydra', type=int, default=0, help='the Hydra\'s cohort of this many (four parties of eight: 32) - '
                'MT2009_PLUS_BOT_HYDRA_COHORT_V1, tools/yohara_bot_cohort_hydra.py')
ap.add_argument('--hydra-end', action='store_true', help='the Hydra\'s test over: the statue\'s errand and the '
                'backup/dissolve SQL - MT2009_PLUS_BOT_CHAMPION_V1')
ap.add_argument('--yohara', type=int, default=0, help='the Yohara maps\' cohort of this many (100): the Hydra\'s '
                'Champions first, level 120, a Champion level and the Sung Ma Will of one of the nine Sung Ma maps, the '
                'Hydra\'s gear - MT2009_PLUS_BOT_YOHARA_MAPS_V1, tools/yohara_bot_cohort_sungma.py')
ap.add_argument('--hydra-pairs', type=int, default=0, help='the Hydra\'s cohort as this many pairs (a Ninja and '
                'another class of one kingdom; 16) - MT2009_PLUS_BOT_HYDRA_PAIRS_V1, tools/yohara_bot_cohort_hydra.py')
# MT2009_PLUS_BOT_YOHARA800_V1: the 800 new Yohara bots (tools/yohara_bot_cohort_800.py)
ap.add_argument('--yohara800', type=int, default=0, help='this many NEW bot identities for the Yohara maps (800): level '
                '120, Champion 1-30, G0 gear (some better), no bonuses, the bonus/alchemy bag - MT2009_PLUS_BOT_YOHARA800_V1, '
                'tools/yohara_bot_cohort_800.py')
ap.add_argument('--channels', default='1', help='--yohara800: the channels the members go to in turn ("1" or "1,2")')
ap.add_argument('--active', type=int, default=-1, help='--yohara800: this many work at once, the rest rest until '
                'cohort_activate.sql (-1: all)')
ap.add_argument('--pid-base', type=int, default=6001, help='--yohara800: the first PID (6001: past the seed, under the '
                'companions\' 8000)')
ap.add_argument('--cor-vnum', type=int, default=51510, help='--yohara800: the legendary Cor Draconis (51510 or 50259)')
ap.add_argument('--better-pct', type=float, default=22.0, help='--yohara800: per cent of the bots better than G0 at least')
ap.add_argument('--seed', type=int, default=800, help='--yohara800: the random seed (the same seed, the same plan)')
a = ap.parse_args()
if a.hydra_pairs > 0:	# MT2009_PLUS_BOT_HYDRA_PAIRS_V1
    a.hydra = 2 * a.hydra_pairs
os.makedirs(a.outdir, exist_ok=True)

# MT2009_PLUS_BOT_CHAMPION_V1: the Hydra's end - three SQL files, nothing read or changed here.
if a.hydra_end:
    COLS = ("ALTER TABLE common.playerbot_yohara_cohort ADD COLUMN IF NOT EXISTS champion TINYINT UNSIGNED NOT NULL DEFAULT 0, "
            "ADD COLUMN IF NOT EXISTS champion_at DATETIME NULL;")
    E = ['-- MT2009_PLUS_BOT_CHAMPION_V1: the Hydra\'s test over - the statue\'s errand. Safe with the game running.',
         'SET NAMES latin1;',
         COLS,
         "UPDATE common.playerbot_yohara_cohort c LEFT JOIN player.player p ON p.id = c.pid\n"
         "   SET c.champion = IF(IFNULL(p.conqueror_level, 0) > 0, 2, IF(c.wins >= 1, 1, 3)),\n"
         "       c.champion_at = IF(IFNULL(p.conqueror_level, 0) > 0 OR c.wins < 1, NOW(), NULL)\n"
         " WHERE c.purpose = 'hydra' AND c.champion = 0;",
         "SELECT c.champion, COUNT(*) AS members, SUM(c.wins) AS wins FROM common.playerbot_yohara_cohort c "
         "WHERE c.purpose = 'hydra' GROUP BY c.champion;"]
    open(os.path.join(a.outdir, 'hydra_end.sql'), 'w').write('\n'.join(E) + '\n')
    open(os.path.join(a.outdir, 'hydra_champion_status.sql'), 'w').write('\n'.join([
        '-- MT2009_PLUS_BOT_CHAMPION_V1: the statue\'s errand (champion 1 pending, 2 a Champion, 3 done without it).',
        'SET NAMES latin1;',
        "SELECT c.champion, COUNT(*) AS members, SUM(p.conqueror_level > 0) AS champions FROM common.playerbot_yohara_cohort c "
        "LEFT JOIN player.player p ON p.id = c.pid WHERE c.purpose = 'hydra' GROUP BY c.champion;",
        "SELECT c.pid, p.name, p.level, c.wins, c.champion, c.champion_at, p.conqueror_level, c.last_map, h.target_map AS handover_to, "
        "h.state AS handover_state FROM common.playerbot_yohara_cohort c LEFT JOIN player.player p ON p.id = c.pid "
        "LEFT JOIN common.playerbot_core_handover h ON h.pid = c.pid WHERE c.purpose = 'hydra' ORDER BY c.champion, c.party, c.pid;",
    ]) + '\n')
    open(os.path.join(a.outdir, 'hydra_dissolve_ended.sql'), 'w').write('\n'.join([
        '-- MT2009_PLUS_BOT_CHAMPION_V1: the Hydra\'s cohort dissolved, its rows kept in common.playerbot_yohara_cohort_ended',
        '-- (as the other cohorts\'). The bots keep level, gear and Champion level. Safe with the game running.',
        'SET NAMES latin1;',
        'USE common;',
        COLS,
        'CREATE TABLE IF NOT EXISTS common.playerbot_yohara_cohort_ended LIKE common.playerbot_yohara_cohort;',
        COLS.replace('playerbot_yohara_cohort ', 'playerbot_yohara_cohort_ended '),
        'START TRANSACTION;',
        'REPLACE INTO common.playerbot_yohara_cohort_ended (pid, purpose, channel, rest_until, created_at, level_start, '
        'exp_start, sent, arrived, deaths, runs, rest_outs, exp_gained, last_map, last_seen, applied_at, party, wins, '
        'champion, champion_at)\n'
        '  SELECT pid, purpose, channel, rest_until, created_at, level_start, exp_start, sent, arrived, deaths, runs, '
        'rest_outs, exp_gained, last_map, last_seen, applied_at, party, wins, champion, champion_at\n'
        "    FROM common.playerbot_yohara_cohort WHERE purpose = 'hydra';",
        "DELETE h FROM common.playerbot_core_handover h JOIN common.playerbot_yohara_cohort c ON c.pid = h.pid "
        "WHERE h.state = 1 AND c.purpose = 'hydra';",
        "DELETE FROM common.playerbot_yohara_cohort WHERE purpose = 'hydra';",
        'COMMIT;',
        "SELECT purpose, COUNT(*) AS rows_ended, SUM(champion = 2) AS champions FROM common.playerbot_yohara_cohort_ended "
        "GROUP BY purpose;",
    ]) + '\n')
    print('wrote hydra_end.sql, hydra_champion_status.sql, hydra_dissolve_ended.sql to', a.outdir)
    sys.exit(0)


def q(sql, fatal=True):
    r = subprocess.run(['docker', 'exec', '-i', a.db_container, 'sh', '-c',
                        'mariadb -uroot -p"$MARIADB_ROOT_PASSWORD" -N -B --default-character-set=latin1'],
                       input=sql.encode('latin-1'), capture_output=True)
    if r.returncode:
        if fatal:
            sys.exit(r.stderr.decode(errors='replace'))
        return None
    return [l.split('\t') for l in r.stdout.decode('latin-1').splitlines() if l]


def pidset(sql):
    rows = q(sql, fatal=False)
    return set(int(r[0]) for r in rows or [] if r and r[0].isdigit())


# MT2009_PLUS_BOT_YOHARA800_V1: the 800 new identities - their own tool, no registry bot touched.
if a.yohara800 > 0:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import yohara_bot_cohort_800
    yohara_bot_cohort_800.run(a, q, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.exit(0)

PURPOSES = ('zaklety', 'szc', 'snakefield', 'giantland')
WANT = {'zaklety': a.zaklety, 'szc': a.szc, 'snakefield': a.snakefield, 'giantland': a.giantland}

# ---------------------------------------------------------------- who
excluded = set()
excluded |= pidset('SELECT sidekick_pid FROM player.playerbot_sidekick;')
excluded |= pidset('SELECT pid FROM player.playerbot_shouter;')
excluded |= pidset('SELECT pid FROM player.playerbot_legend WHERE tier >= 3;')	# the 27 Legends
excluded |= pidset('SELECT farmer_pid FROM player.playerbot_farmer_link WHERE active = 1;')	# a farmer at its work
excluded |= pidset('SELECT pid FROM common.playerbot_takeover;')
excluded |= pidset('SELECT pid FROM common.playerbot_retire_pick;')
excluded |= pidset('SELECT pid FROM player.arezzo_dungeon_cohort;')
excluded |= pidset('SELECT pid FROM player.arezzo_test_cohort;')
# MT2009_PLUS_BOT_HYDRA_COHORT_V1: the cohorts set aside (the forest's and the Time Rift's of 22 October)
# and the Hydra's are no one else's pick.
paused = pidset('SELECT pid FROM common.playerbot_yohara_cohort_paused;')
hydra_rows = pidset("SELECT pid FROM common.playerbot_yohara_cohort WHERE purpose = 'hydra';")

rows = q("""
SELECT p.id, p.name, p.job, pi.empire, p.level, p.skill_group, p.random_hp, p.st, p.ht, p.dx, p.iq,
       IFNULL(HEX(p.skill_level), ''), (g.master IS NOT NULL), IFNULL(ca.channel, 0), (pin.pid IS NOT NULL)
  FROM common.playerbot_seed_state l
  JOIN player.player p ON p.id = l.pid
  JOIN account.account ac ON ac.id = p.account_id
  JOIN player.player_index pi ON pi.id = ac.id
  LEFT JOIN player.guild g ON g.master = p.id
  LEFT JOIN common.playerbot_channel_assignment ca ON ca.pid = p.id
  LEFT JOIN player.playerbot_channel_pin pin ON pin.pid = p.id
 WHERE l.state IN ('complete', 'adopted') AND LEFT(ac.login, 10) = 'playerbot_'
   AND pi.empire IN (1, 2, 3) AND pi.pid1 = p.id
 ORDER BY p.id;
""")
bots = {}
for r in rows:
    pid = int(r[0])
    bots[pid] = dict(pid=pid, name=r[1], job=int(r[2]), cls=int(r[2]) % 4, female=int(r[2]) >= 4, emp=int(r[3]),
                     old=int(r[4]), grp=int(r[5]), rhp=int(r[6]), st=int(r[7]), ht=int(r[8]), dx=int(r[9]),
                     iq=int(r[10]), skills=r[11], master=int(r[12]), chan=int(r[13]), pinned=int(r[14]))

# MT2009_PLUS_BOT_HYDRA_COHORT_V1: the Hydra's cohort - its own tool, nothing else touched.
if a.hydra > 0:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import yohara_bot_cohort_hydra
    cohort_pids = pidset('SELECT pid FROM common.playerbot_yohara_cohort;') | paused
    yohara_bot_cohort_hydra.run(a, q, bots, excluded, cohort_pids,
                                lambda b: not b['master'] and b['grp'] in (1, 2))
    sys.exit(0)
# MT2009_PLUS_BOT_YOHARA_MAPS_V1: the Yohara maps' cohort - its own tool, nothing else touched.
if a.yohara > 0:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import yohara_bot_cohort_sungma
    cohort_pids = pidset('SELECT pid FROM common.playerbot_yohara_cohort;') | paused
    yohara_bot_cohort_sungma.run(a, q, bots, excluded, cohort_pids,
                                 lambda b: not b['master'] and b['grp'] in (1, 2),
                                 os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.exit(0)
excluded |= paused | hydra_rows

# Members an earlier run made keep their place (and their purpose).
earlier = {}
for r in q('SELECT pid, purpose FROM common.playerbot_yohara_cohort;', fatal=False) or []:
    if r[0].isdigit() and r[1] in PURPOSES:
        earlier[int(r[0])] = r[1]


def usable(b):
    # (a pin keeps a bot that kept a shop on the first channel - the shops' - so it is no bar)
    return b['pid'] not in excluded and not b['master'] and b['grp'] in (1, 2)


picks = {p: [] for p in PURPOSES}
used = set()
for pid, purpose in earlier.items():
    if pid in bots:
        picks[purpose].append(bots[pid])
        used.add(pid)


def pick(purpose, pool):
    """Equal shares of the eight class/path pairs, kingdoms and sexes in turn, the pool's order kept."""
    rank = {b['pid']: i for i, b in enumerate(pool)}
    need = WANT[purpose] - len(picks[purpose])
    if need <= 0:
        return
    pairs = [(c, g) for c in range(4) for g in (1, 2)]
    have = collections.Counter((b['cls'], b['grp']) for b in picks[purpose])
    buckets = {pr: collections.defaultdict(list) for pr in pairs}
    for b in pool:
        if b['pid'] in used or not usable(b):
            continue
        buckets[(b['cls'], b['grp'])][(b['emp'], b['female'])].append(b)
    quota = {pr: max(0, (WANT[purpose] + 7) // 8 - have[pr]) for pr in pairs}
    took = 0
    rounds = 0
    while took < need and rounds < 4000:
        rounds += 1
        progress = False
        for pr in pairs:
            if took >= need:
                break
            if quota[pr] <= 0:
                continue
            # the best of the pool's order, a kingdom and sex this pair already has two more of
            # than its fewest giving way (a level is worth more than the balance, but not all of it)
            mine = [b for b in picks[purpose] if (b['cls'], b['grp']) == pr]
            cnt = collections.Counter((b['emp'], b['female']) for b in mine)
            for k in buckets[pr]:
                lst = buckets[pr][k]
                while lst and lst[0]['pid'] in used:
                    lst.pop(0)
            live = [k for k in buckets[pr] if buckets[pr][k]]
            low = min([cnt[k] for k in live] or [0])
            keys = sorted(live, key=lambda k: (cnt[k] > low + 1, rank[buckets[pr][k][0]['pid']]))
            for k in keys:
                lst = buckets[pr][k]
                if lst:
                    b = lst.pop(0)
                    picks[purpose].append(b)
                    used.add(b['pid'])
                    quota[pr] -= 1
                    took += 1
                    progress = True
                    break
        if not progress:
            # a pair ran dry: its share goes to the others
            open_pairs = [pr for pr in pairs if any(buckets[pr][k] for k in buckets[pr])]
            if not open_pairs:
                break
            for pr in open_pairs:
                quota[pr] += 1
    if took < need:
        print('WARNING: %s - only %d of %d more members found' % (purpose, took, need))


by_level = sorted(bots.values(), key=lambda b: (-b['old'], b['pid']))
# Never from under --min-raise: a class/path pair short of such bots gives its share to the others.
pick('szc', [b for b in by_level if a.min_raise <= b['old'] <= 119])
pick('zaklety', [b for b in by_level if a.min_raise <= b['old'] <= 109])
mid = lambda lo, hi, c: sorted([b for b in bots.values() if lo <= b['old'] <= hi], key=lambda b: (abs(b['old'] - c), b['pid']))
pick('snakefield', mid(66, 76, 71))
pick('giantland', mid(66, 78, 72))


def target_level(purpose, b):
    if purpose == 'szc':
        return max(b['old'], 110)
    if purpose == 'zaklety':
        return b['old'] if b['old'] >= 100 else 100 + b['pid'] % 6
    return b['old']


# ---------------------------------------------------------------- items
proto = {}
for r in q('SELECT vnum, type, subtype, limittype0, limitvalue0, limittype1, limitvalue1, size, locale_name FROM player.item_proto;'):
    v = int(r[0])
    lv = 0
    if r[3] == '1':
        lv = int(r[4])
    elif r[5] == '1':
        lv = int(r[6])
    proto[v] = dict(type=int(r[1]), sub=int(r[2]), lv=lv, size=int(r[7]), name=r[8])

GEAR_POS = (0, 1, 2, 3, 4, 5, 6, 10)
fam = collections.defaultdict(collections.Counter)	# (cls, grp, pos) -> family -> bots wearing it
for r in q("""
SELECT p.job % 4, p.skill_group, i.pos, i.vnum, COUNT(*)
  FROM player.player p JOIN account.account ac ON ac.id = p.account_id
  JOIN player.item i ON i.owner_id = p.id AND i.window = 'EQUIPMENT' AND i.pos IN (0,1,2,3,4,5,6,10)
 WHERE LEFT(ac.login, 10) = 'playerbot_' AND p.level >= 50 AND p.skill_group IN (1, 2)
 GROUP BY 1, 2, 3, 4;
"""):
    cls, grp, pos, vnum, n = int(r[0]), int(r[1]), int(r[2]), int(r[3]), int(r[4])
    f = vnum - vnum % 10
    if f + 9 in proto and proto[f + 9]['lv'] > 0:
        # the weapon by path (a bow, a dagger...), the rest by class
        fam[(cls, grp if pos == 4 else 0, pos)][f] += n


def gear_for(cls, grp, pos, level):
    key = (cls, grp if pos == 4 else 0, pos)
    fams = [(proto[f + 9]['lv'], n, f) for f, n in fam[key].items() if n >= 2 and proto[f + 9]['lv'] <= level]
    if not fams:
        return None
    fams.sort(reverse=True)
    return fams[0][2] + 9


# The engine keeps an item's bonus types as POINT_* numbers (playerbot_engine_compat.h).
MAX_HP, ST, HT, DX, IQ = 6, 12, 13, 14, 15
ATT_SPEED, MOV_SPEED, HP_REGEN, POISON, STUN = 17, 19, 32, 37, 38
CRIT, PEN, ANIMAL, ORC, MILGYO, DEVIL = 40, 41, 44, 45, 46, 48
STEAL_HP, BLOCK, DODGE, RES_MAGIC, REFLECT, POISON_REDUCE, IMMUNE_STUN, ATT_GRADE = 63, 67, 68, 77, 79, 81, 88, 95


def bonuses(pos, cls, grp, purpose):
    race = DEVIL if purpose in ('zaklety', 'szc') else ANIMAL
    other = MILGYO if race == DEVIL else ORC
    stat = IQ if (cls == 3 or (cls == 2 and grp == 2)) else (DX if (cls == 1 and grp == 2) else ST)
    return {
        0: [(MAX_HP, 2000), (STEAL_HP, 10), (ATT_GRADE, 50), (RES_MAGIC, 15), (REFLECT, 10)],
        1: [(ATT_SPEED, 8), (HP_REGEN, 30), (race, 20), (POISON, 8), (RES_MAGIC, 15)],
        2: [(MAX_HP, 2000), (MOV_SPEED, 20), (CRIT, 10), (ATT_SPEED, 8), (DODGE, 15)],
        3: [(MAX_HP, 2000), (PEN, 10), (race, 20), (STEAL_HP, 10), (RES_MAGIC, 15)],
        4: [(race, 20), (CRIT, 10), (PEN, 10), (stat, 12), (HT, 12)],
        5: [(MAX_HP, 2000), (CRIT, 10), (PEN, 10), (HP_REGEN, 30), (STUN, 8)],
        6: [(race, 20), (MOV_SPEED, 20), (other, 20), (ANIMAL if race != ANIMAL else MILGYO, 20), (POISON_REDUCE, 5)],
        10: [(HT, 12), (BLOCK, 15), (race, 20), (IMMUNE_STUN, 1), (REFLECT, 10)],
    }[pos]


# Spirit stones (the ones the bots' own sets carry, playerbot_gear / tools/arezzo_test_cohort.py).
WEAPON_SOCKETS = (28437, 28430, 28431)
ARMOUR_SOCKETS = (28441, 28441, 28439)
TALISMAN = {'zaklety': 94750, 'szc': 94750, 'snakefield': 95000, 'giantland': 95000}	# Wind (ATT_TEMPLE), Earth


def talisman_for(purpose, level):
    base = TALISMAN[purpose]
    best = None
    for plus in range(0, 151):
        p = proto.get(base + plus)
        if p and p['lv'] <= level:
            best = base + plus
    return best


# Alchemy: each kind's best stone the world's bots wear (at most Legendary - grade 4 -, three of
# a vnum at least: the highest grade, step and strength), with the bonuses those stones carry (the
# basic pair most often seen, the three additional ones most often seen - the Jade's max HP / max
# HP % / life steal first).
ds_rows = collections.defaultdict(list)
for r in q("""SELECT vnum, attrtype0, attrvalue0, attrtype1, attrvalue1, attrtype3, attrvalue3, attrtype4, attrvalue4,
              attrtype5, attrvalue5 FROM player.item WHERE vnum BETWEEN 110000 AND 179999 AND attrtype0 > 0;"""):
    ds_rows[int(r[0])].append([int(x) for x in r[1:]])


def ds_stone(t):
    vs = [v for v, rs in ds_rows.items() if v // 10000 == t and (v // 1000) % 10 <= 4 and len(rs) >= 3 and v in proto]
    if not vs:
        return None
    v = max(vs)
    rs = ds_rows[v]
    basic = collections.Counter(tuple(x[0:4]) for x in rs).most_common(1)[0][0]
    add = collections.Counter()
    for x in rs:
        for k in (4, 6, 8):
            if x[k] > 0:
                add[(x[k], x[k + 1])] += 1
    chosen = []
    if t == 13:
        for want in (MAX_HP, 119, STEAL_HP):
            c = [kv for kv in add if kv[0] == want]
            if c:
                chosen.append(max(c, key=lambda kv: (add[kv], kv[1])))
    for kv, _ in add.most_common():
        if len(chosen) >= 3:
            break
        if kv[0] not in [c[0] for c in chosen]:
            chosen.append(kv)
    attrs = [(basic[0], basic[1]), (basic[2], basic[3]), (0, 0)] + chosen[:3]
    return v, attrs


ARROW = 8001

# ---------------------------------------------------------------- skills
SKILLS = {(0, 1): range(1, 7), (0, 2): range(16, 22), (1, 1): range(31, 37), (1, 2): range(46, 52),
          (2, 1): range(61, 67), (2, 2): range(76, 82), (3, 1): range(91, 97), (3, 2): range(106, 112)}


def skills_for(b, purpose):
    blob = bytearray.fromhex(b['skills']) if b['skills'] else bytearray()
    if len(blob) < 1590:
        blob += bytearray(1590 - len(blob))
    rng = random.Random(b['pid'] * 7919 + len(purpose))
    vn = list(SKILLS[(b['cls'], b['grp'])])
    learned = [v for v in vn if blob[v * 6 + 1] > 0] or vn
    for v in learned:
        if purpose == 'szc':
            target = 30 + rng.randint(0, 1) if rng.random() < 0.2 else rng.randint(27, 29)
        elif purpose == 'zaklety':
            target = rng.randint(24, 28)
        else:
            target = rng.randint(20, 23)
        if blob[v * 6 + 1] < target:
            blob[v * 6] = 2 if target >= 30 else 1
            blob[v * 6 + 1] = target
    return blob.hex().upper()


# ---------------------------------------------------------------- stats
BASE_HP = {0: 600, 1: 650, 2: 650, 3: 700}


def stats_for(cls, level):
    total = min(16 + 3 * (level - 1), 360)
    rest = max(3, total - 270)
    if cls in (0, 1):
        return 90, 90, 90, rest	# st, ht, dx, iq
    return rest, 90, 90, 90


members = []
for purpose in PURPOSES:
    for b in picks[purpose]:
        m = dict(b)
        m['purpose'] = purpose
        m['lvl'] = target_level(purpose, b)
        members.append(m)

# ---------------------------------------------------------------- SQL
pids = sorted(m['pid'] for m in members)
plist = ','.join(str(x) for x in pids)
EQ_POS = '0,1,2,3,4,5,6,10,25,32,33,34,35,36,37,38'
S = []
S.append('-- MT2009_PLUS_BOT_YOHARA_COHORT_V1: the night\'s cohorts (tools/yohara_bot_cohort.py). Game stopped.')
S.append('-- %s' % ', '.join('%s %d' % (p, sum(1 for m in members if m['purpose'] == p)) for p in PURPOSES))
S.append('SET NAMES latin1;')
S.append("""CREATE TABLE IF NOT EXISTS common.playerbot_yohara_cohort (
  pid INT UNSIGNED NOT NULL PRIMARY KEY, purpose VARCHAR(16) NOT NULL, channel TINYINT UNSIGNED NOT NULL DEFAULT 1,
  rest_until DATETIME NULL, created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  level_start TINYINT UNSIGNED NOT NULL DEFAULT 0, exp_start INT UNSIGNED NOT NULL DEFAULT 0,
  sent INT UNSIGNED NOT NULL DEFAULT 0, arrived INT UNSIGNED NOT NULL DEFAULT 0, deaths INT UNSIGNED NOT NULL DEFAULT 0,
  runs INT UNSIGNED NOT NULL DEFAULT 0, rest_outs INT UNSIGNED NOT NULL DEFAULT 0, exp_gained BIGINT UNSIGNED NOT NULL DEFAULT 0,
  last_map INT NOT NULL DEFAULT 0, last_seen DATETIME NULL, applied_at DATETIME NULL, KEY purpose (purpose)) ENGINE=InnoDB;""")
S.append('ALTER TABLE common.playerbot_yohara_cohort ADD COLUMN IF NOT EXISTS applied_at DATETIME NULL;')
S.append("""CREATE TABLE IF NOT EXISTS player.playerbot_yohara_cohort_bak_player (
  id INT UNSIGNED NOT NULL PRIMARY KEY, level TINYINT UNSIGNED NOT NULL, exp INT UNSIGNED NOT NULL, level_step TINYINT NOT NULL,
  st SMALLINT NOT NULL, ht SMALLINT NOT NULL, dx SMALLINT NOT NULL, iq SMALLINT NOT NULL, stat_point SMALLINT NOT NULL,
  skill_point SMALLINT NOT NULL, sub_skill_point SMALLINT NOT NULL, random_hp SMALLINT NOT NULL, random_sp SMALLINT NOT NULL,
  gold BIGINT NOT NULL, skill_level BLOB NULL, channel_old TINYINT UNSIGNED NULL, saved_at DATETIME NOT NULL) ENGINE=InnoDB;""")
# MT2009_PLUS_EXP_UNSIGNED_V1: player.player.exp is INT UNSIGNED (the level-120 bar is 2.5 bn); a backup table
# made before as INT would clamp a saved exp at 2 147 483 647.
S.append('ALTER TABLE player.playerbot_yohara_cohort_bak_player MODIFY exp INT UNSIGNED NOT NULL;')
S.append('CREATE TABLE IF NOT EXISTS player.playerbot_yohara_cohort_bak_item LIKE player.item;')
S.append('START TRANSACTION;')
S.append('INSERT IGNORE INTO common.playerbot_yohara_cohort (pid, purpose, channel, level_start, created_at) VALUES')
S.append(',\n'.join("  (%d, '%s', %d, %d, NOW())" % (m['pid'], m['purpose'], a.channel, m['lvl']) for m in members) + ';')
S.append('-- the backups, once a member (applied_at still NULL, not backed up yet)')
S.append("""INSERT IGNORE INTO player.playerbot_yohara_cohort_bak_player
SELECT p.id, p.level, p.exp, p.level_step, p.st, p.ht, p.dx, p.iq, p.stat_point, p.skill_point, p.sub_skill_point,
       p.random_hp, p.random_sp, p.gold, p.skill_level, ca.channel, NOW()
  FROM player.player p JOIN common.playerbot_yohara_cohort c ON c.pid = p.id AND c.applied_at IS NULL
  LEFT JOIN common.playerbot_channel_assignment ca ON ca.pid = p.id;""")
S.append("""INSERT IGNORE INTO player.playerbot_yohara_cohort_bak_item
SELECT i.* FROM player.item i JOIN common.playerbot_yohara_cohort c ON c.pid = i.owner_id AND c.applied_at IS NULL
 WHERE ((i.window = 'EQUIPMENT' AND i.pos IN (%s, 9)) OR (i.window = 'INVENTORY' AND i.vnum = 31147))
   AND i.owner_id NOT IN (SELECT DISTINCT owner_id FROM player.playerbot_yohara_cohort_bak_item);""" % EQ_POS)
S.append('-- the characters (only while applied_at is NULL; level last - MariaDB assigns left to right)')
pick_rows = []
for m in sorted(members, key=lambda x: x['pid']):
    L = m['lvl']
    st, ht, dx, iq = stats_for(m['cls'], L)
    blob = skills_for(m, m['purpose'])
    S.append("""UPDATE player.player p JOIN common.playerbot_yohara_cohort c ON c.pid = p.id AND c.applied_at IS NULL
   SET p.stat_point = IF(p.level < %(L)d, 0, GREATEST(p.stat_point, LEAST(3 * (p.level - 1), 344) - (p.st + p.ht + p.dx + p.iq - 16))),
       p.st = IF(p.level < %(L)d, %(st)d, p.st), p.ht = IF(p.level < %(L)d, %(ht)d, p.ht),
       p.dx = IF(p.level < %(L)d, %(dx)d, p.dx), p.iq = IF(p.level < %(L)d, %(iq)d, p.iq),
       p.sub_skill_point = p.sub_skill_point + GREATEST(0, %(L)d - GREATEST(p.level, 8)),
       p.random_hp = GREATEST(p.random_hp, 40 * (%(L)d - 1)), p.random_sp = GREATEST(p.random_sp, 20 * (%(L)d - 1)),
       p.gold = GREATEST(p.gold, 20000000), p.skill_level = UNHEX('%(blob)s'),
       p.exp = IF(p.level < %(L)d, 0, p.exp), p.level_step = IF(p.level < %(L)d, 0, p.level_step),
       p.level = GREATEST(p.level, %(L)d)
 WHERE p.id = %(pid)d;""" % dict(L=L, st=st, ht=ht, dx=dx, iq=iq, blob=blob, pid=m['pid']))
S.append("""INSERT INTO common.playerbot_channel_assignment (pid, channel, ready_at) SELECT c.pid, %d, NOW()
  FROM common.playerbot_yohara_cohort c WHERE c.applied_at IS NULL
ON DUPLICATE KEY UPDATE channel = VALUES(channel), requested_channel = 0, request_reason = '', request_at = NULL, ready_at = NOW();""" % a.channel)
S.append("UPDATE common.playerbot_yohara_cohort c JOIN player.player p ON p.id = c.pid SET c.applied_at = NOW(), "
         "c.level_start = p.level, c.exp_start = p.exp WHERE c.applied_at IS NULL;")
S.append('-- the equipment (put back every run)')
S.append("DELETE FROM player.item WHERE window = 'EQUIPMENT' AND pos IN (%s) AND owner_id IN (%s);" % (EQ_POS, plist))
ins = []
for m in sorted(members, key=lambda x: x['pid']):
    L, cls, grp, purpose = m['lvl'], m['cls'], m['grp'], m['purpose']
    hp_items = 0
    ht_items = 0
    gear_lv = []
    for pos in GEAR_POS:
        v = gear_for(cls, grp, pos, L)
        if v is None:
            print('WARNING: no gear for pid %d class %d path %d pos %d level %d' % (m['pid'], cls, grp, pos, L))
            continue
        gear_lv.append(proto[v]['lv'])
        sock = WEAPON_SOCKETS if pos == 4 else (ARMOUR_SOCKETS if pos == 0 else (0, 0, 0))
        at = bonuses(pos, cls, grp, purpose)
        hp_items += sum(val for t, val in at if t == MAX_HP)
        ht_items += sum(val for t, val in at if t == HT)
        at = at + [(0, 0)] * (7 - len(at))
        ins.append("  (%d, 'EQUIPMENT', %d, 1, %d, %d, %d, %d, %s)" % (
            m['pid'], pos, v, sock[0], sock[1], sock[2], ', '.join('%d, %d' % t for t in at)))
    tal = talisman_for(purpose, L)
    if tal:
        ins.append("  (%d, 'EQUIPMENT', 25, 1, %d, 0, 0, 0, %s)" % (m['pid'], tal, ', '.join(['0, 0'] * 7)))
    ds_hp = 0
    ds_pct = 0
    ds_ht = 0
    for t in range(11, 18):
        st_ = ds_stone(t)
        if not st_:
            continue
        v, at = st_
        for ty, val in at:
            if ty == MAX_HP:
                ds_hp += val
            elif ty == 119:
                ds_pct += val
            elif ty == HT:
                ds_ht += val
        at = at + [(0, 0)] * (7 - len(at))
        ins.append("  (%d, 'EQUIPMENT', %d, 1, %d, 86400, 0, 0, %s)" % (
            m['pid'], 32 + t - 11, v, ', '.join('%d, %d' % x for x in at)))
    st, ht, dx, iq = stats_for(cls, L) if m['old'] < L else (m['st'], m['ht'], m['dx'], m['iq'])
    rhp = max(m['rhp'], 40 * (L - 1))
    hp = BASE_HP[cls] + rhp + (ht + ht_items + ds_ht) * 40 + hp_items + ds_hp
    hp += min(3500, hp * ds_pct // 100)
    m['est_hp'] = hp
    m['gear_lv'] = max(gear_lv) if gear_lv else 0
    m['talisman'] = tal or 0
S.append('INSERT INTO player.item (owner_id, window, pos, count, vnum, socket0, socket1, socket2, '
         'attrtype0, attrvalue0, attrtype1, attrvalue1, attrtype2, attrvalue2, attrtype3, attrvalue3, '
         'attrtype4, attrvalue4, attrtype5, attrvalue5, attrtype6, attrvalue6) VALUES\n' + ',\n'.join(ins) + ';')
archers = [m['pid'] for m in members if m['cls'] == 1 and m['grp'] == 2]
for pid in archers:
    S.append("INSERT INTO player.item (owner_id, window, pos, count, vnum) SELECT %d, 'EQUIPMENT', 9, 1000, %d FROM DUAL "
             "WHERE NOT EXISTS (SELECT 1 FROM player.item WHERE owner_id = %d AND window = 'EQUIPMENT' AND pos = 9);" % (pid, ARROW, pid))
szc = [m['pid'] for m in members if m['purpose'] == 'szc']
if szc:
    S.append('-- the Time Rift: 30 Zegarek Kieszonkowy (31147) in the first free cell of the bag\'s four pages (none free:')
    S.append('-- the bot pays the watch\'s 25 000 at each run - ChargePlayerBotYoharaSzcWatch)')
    S.append("DELETE FROM player.item WHERE window = 'INVENTORY' AND vnum = 31147 AND owner_id IN (%s);" % ','.join(map(str, szc)))
    for pid in szc:
        S.append("""INSERT INTO player.item (owner_id, window, pos, count, vnum)
WITH RECURSIVE n(pos) AS (SELECT 0 UNION ALL SELECT pos + 1 FROM n WHERE pos < 179)
SELECT %(pid)d, 'INVENTORY', MIN(n.pos), 30, 31147 FROM n
 WHERE NOT EXISTS (SELECT 1 FROM player.item i JOIN player.item_proto ip ON ip.vnum = i.vnum
                    WHERE i.owner_id = %(pid)d AND i.window = 'INVENTORY' AND n.pos >= i.pos
                      AND n.pos < i.pos + 5 * GREATEST(ip.size, 1) AND (n.pos - i.pos) %% 5 = 0)
HAVING MIN(n.pos) IS NOT NULL;""" % dict(pid=pid))
S.append('COMMIT;')
S.append("SELECT c.purpose, COUNT(*) AS members, MIN(p.level) AS lv_min, MAX(p.level) AS lv_max, SUM(c.applied_at IS NOT NULL) AS applied "
         "FROM common.playerbot_yohara_cohort c JOIN player.player p ON p.id = c.pid GROUP BY c.purpose;")
S.append("SELECT COUNT(DISTINCT owner_id) AS szc_with_watches FROM player.item WHERE window = 'INVENTORY' AND vnum = 31147 "
         "AND owner_id IN (SELECT pid FROM common.playerbot_yohara_cohort WHERE purpose = 'szc');")
S.append("SELECT COUNT(*) AS gear_rows FROM player.item WHERE window = 'EQUIPMENT' AND pos IN (%s) AND owner_id IN (%s);" % (EQ_POS, plist))
open(os.path.join(a.outdir, 'cohort_apply.sql'), 'w', encoding='latin-1').write('\n'.join(S) + '\n')

D = ['-- MT2009_PLUS_BOT_YOHARA_COHORT_V1: the cohorts dissolved (the bots keep their level and gear).',
     '-- Safe with the game running: the cores read the table every minute; residents finish their stay as',
     '-- ordinary bots and come home through the handover.',
     'USE common;',
     'DELETE h FROM common.playerbot_core_handover h JOIN common.playerbot_yohara_cohort c ON c.pid = h.pid WHERE h.state = 1;',
     'DELETE FROM common.playerbot_yohara_cohort;']
open(os.path.join(a.outdir, 'cohort_dissolve.sql'), 'w').write('\n'.join(D) + '\n')

R = ['-- MT2009_PLUS_BOT_YOHARA_COHORT_V1: every member back as it was before the first apply. Game stopped.',
     'SET NAMES latin1;',
     'USE player;',
     'START TRANSACTION;',
     """UPDATE player.player p JOIN player.playerbot_yohara_cohort_bak_player b ON b.id = p.id
   SET p.exp = b.exp, p.level_step = b.level_step, p.st = b.st, p.ht = b.ht, p.dx = b.dx, p.iq = b.iq,
       p.stat_point = b.stat_point, p.skill_point = b.skill_point, p.sub_skill_point = b.sub_skill_point,
       p.random_hp = b.random_hp, p.random_sp = b.random_sp, p.gold = b.gold, p.skill_level = b.skill_level,
       p.level = b.level;""",
     """UPDATE common.playerbot_channel_assignment ca JOIN player.playerbot_yohara_cohort_bak_player b ON b.id = ca.pid
   SET ca.channel = b.channel_old WHERE b.channel_old IS NOT NULL;""",
     """DELETE i FROM player.item i JOIN player.playerbot_yohara_cohort_bak_player b ON b.id = i.owner_id
 WHERE (i.window = 'EQUIPMENT' AND i.pos IN (%s, 9)) OR (i.window = 'INVENTORY' AND i.vnum = 31147);""" % EQ_POS,
     'INSERT IGNORE INTO player.item SELECT * FROM player.playerbot_yohara_cohort_bak_item;',
     'DELETE FROM common.playerbot_core_handover WHERE pid IN (SELECT id FROM player.playerbot_yohara_cohort_bak_player);',
     'DELETE FROM common.playerbot_yohara_cohort;',
     'COMMIT;',
     '-- then, when nothing more is needed from them:',
     '-- DROP TABLE player.playerbot_yohara_cohort_bak_player, player.playerbot_yohara_cohort_bak_item;']
open(os.path.join(a.outdir, 'cohort_restore.sql'), 'w').write('\n'.join(R) + '\n')

CLS = ('wojownik', 'ninja', 'sura', 'szaman')
SHORT = ('W', 'N', 'S', 'Sz')
with open(os.path.join(a.outdir, 'pick.tsv'), 'w', encoding='latin-1') as f:
    f.write('pid\tname\tpurpose\tclass\tpath\tsex\tempire\tlevel_before\tlevel_after\tgear_level\ttalisman\test_max_hp\n')
    for m in sorted(members, key=lambda x: (PURPOSES.index(x['purpose']), x['cls'], x['grp'], x['emp'], x['pid'])):
        f.write('%d\t%s\t%s\t%s\t%d\t%s\t%d\t%d\t%d\t%d\t%d\t%d\n' % (
            m['pid'], m['name'], m['purpose'], CLS[m['cls']], m['grp'], 'k' if m['female'] else 'm', m['emp'],
            m['old'], m['lvl'], m['gear_lv'], m['talisman'], m['est_hp']))
open(os.path.join(a.outdir, 'pids.txt'), 'w').write(' '.join(map(str, pids)) + '\n')
for p in PURPOSES:
    ms = [m for m in members if m['purpose'] == p]
    if not ms:
        continue
    print('%-10s %3d  class/path %s  kingdoms %s  sex m/k %d/%d  level before %d-%d after %d-%d  raised %d  est HP %d-%d' % (
        p, len(ms), dict(sorted(collections.Counter('%s%d' % (SHORT[m['cls']], m['grp']) for m in ms).items())),
        dict(sorted(collections.Counter(m['emp'] for m in ms).items())),
        sum(1 for m in ms if not m['female']), sum(1 for m in ms if m['female']),
        min(m['old'] for m in ms), max(m['old'] for m in ms), min(m['lvl'] for m in ms), max(m['lvl'] for m in ms),
        sum(1 for m in ms if m['lvl'] > m['old']), min(m['est_hp'] for m in ms), max(m['est_hp'] for m in ms)))
