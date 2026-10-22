"""yohara_bot_cohort_hydra.py - the Hydra's cohort (MT2009_PLUS_BOT_HYDRA_COHORT_V1), the part of
tools/yohara_bot_cohort.py that `--hydra N` runs instead of the night's cohorts:

    yohara_bot_cohort.py <outdir> --hydra 32 [--db-container mt2009plustest-db] [--channel 1]

The owner, 22 October 2026: "Przygotuj cztery party po 8 postaci. Lvl 120 + 25% expa. Daj im super EQ pod
Hydre. Najwiecej Hydr na globalu robia ninje lucznicy na polimorfii w Dzikiego Sluge, Orka albo Trujacego
Pajaka ... Reszta postaci w duzych 7-8 osobowych partiach ... Mozesz im dac tez mikstury lodu z Yohary."

Who: N existing bots (the night tool's exclusions, and every member of a cohort - active or paused - left
alone), in fixed parties of eight, a party of one kingdom (the engine's rule for a party):

    party 1  N2 x6, Sh2, W1                  the global way: Archer Ninjas on a polymorph
    party 2  N2 x5, Sh2, W1, S1
    party 3  W1, W2, N1, N2, S1, S2, Sh1, Sh2 mixed
    party 4  W1, W2, N1, N2, S1, S2, Sh1, Sh2 mixed

(N2 = Archer Ninja, Sh2 = the healing Shaman with Cure; a fifth party and on: the mixed one.) Parties 1-3 take
the kingdoms 1, 2, 3, the fourth the kingdom with the most of its template left. Each slot: the highest level
of its kingdom, class and path; none - the class's other path.

What: level 120 and 25% of the level's experience (exp_table[120] 2 500 000 000 -> 625 000 000), the
stats of 120 (90 each), the hit/spell points the levels roll on average, the path's six skills at P (40) and the
Archer Ninjas' Polymorph (129) at P - a marble then lasts 35 minutes, the ship's whole voyage; 30 000 000 gold at
least; the gear +9 with five strong bonuses each (our items for the owner's list - see GEAR below), the sash
(Szarfa Wladcy Absolutnego +3, 25% of the bot's own Zodiac weapon and its bonuses), Pas Dusz +9, the Ice
talisman (Talizman Lodu, the highest plus the level wears, at most +150), the seven Mythic stones at their
highest step and +6 with the bonuses of dragon_soul_table.txt at that weight (x1.6), 200 Srebrna Strzala for an
archer; in the bag three Marmur Polimorfii (70104, socket 0: Dziki Sluga 502 / Ork 601 / Trujacy Pajak 2002 by
the pid) for an Archer Ninja and ten of each ice elixir (Eliksir Mroznej Mocy 50831 - Sila Lodu, Eliksir Odp. na
Lod 50837) at their best (20%, 10 minutes). The cores keep the marbles, the elixirs and the arrows up on the pier
(RestockPlayerBotYoharaHydra).

Idempotent like the night tool: the rows first (common.playerbot_yohara_cohort, purpose 'hydra', party 1-4),
the character changed only while applied_at is NULL, the backup taken once (the same backup tables), the gear and
the kit put back on each run. Writes cohort_apply.sql, cohort_dissolve.sql and cohort_restore.sql for the Hydra's
members only, pick.tsv and pids.txt.

MT2009_PLUS_BOT_HYDRA_PAIRS_V1 - the owner, 22 October 2026: "Zmniejsz party do dwoch osob i puszczaj
wszystkie party naraz. Party = jeden ninja + inna postac." `--hydra-pairs N` (16) re-plans the cohort as N
pairs, each one kingdom's Ninja (an Archer Ninja first - the polymorph) and one of another class (a healing
Shaman or a Warrior first, the classes mixed). The kingdoms' numbers of pairs keep the most of the members there
are (then the evenest split); a member that fits no pair is released - cohort_release.sql, and the head of
cohort_apply.sql, puts it back as it was before its first apply (the backup tables, as cohort_restore.sql does)
and drops its rows - and the pairs short of a Ninja or a partner take the pool's best of their kingdom (the same
exclusions; a bot with a backup left by a dissolved cohort is no pick either), raised and equipped as above.
Writes cohort_release.sql and released.tsv too.
"""
import os, sys, math, collections, itertools

CLS = ('W', 'N', 'S', 'Sh')
TEMPLATES = [
    ['N2'] * 6 + ['Sh2', 'W1'],
    ['N2'] * 5 + ['Sh2', 'W1', 'S1'],
    ['W1', 'W2', 'N1', 'N2', 'S1', 'S2', 'Sh1', 'Sh2'],
    ['W1', 'W2', 'N1', 'N2', 'S1', 'S2', 'Sh1', 'Sh2'],
]
LEVEL = 120
EXP = 625000000          # 25% of exp_table[120] (constants.cpp: 2 500 000 000)
GOLD = 30000000

# The engine keeps an item's bonus types as POINT_* numbers (playerbot_engine_compat.h; common/length.h).
MAX_HP, MAX_SP, ST, HT, DX, IQ = 6, 8, 12, 13, 14, 15
ATT_SPEED, MOV_SPEED, HP_REGEN, SP_REGEN, POISON, STUN = 17, 19, 32, 33, 37, 38
CRIT, PEN, HUMAN, ANIMAL, ORC, MILGYO, UNDEAD, DEVIL, MONSTER = 40, 41, 43, 44, 45, 46, 47, 48, 53
RES_WARRIOR, RES_ASSASSIN, RES_SURA = 59, 60, 61
STEAL_HP, BLOCK, DODGE, RES_MAGIC, REFLECT, POISON_REDUCE, IMMUNE_STUN = 63, 67, 68, 77, 79, 81, 88
ATT_GRADE, MAGIC_ATT_GRADE = 95, 97
MAX_HP_PCT, MAX_SP_PCT, SKILL_DMG, AVG_DMG, SKILL_DEF, AVG_DEF = 119, 120, 121, 122, 123, 124
RES_ICE, RES_CRIT, STONE, BOSS = 133, 136, 149, 150
ENCHANT_ICE = 180

# GEAR: the owner's list (global names) on our item_proto (+9 vnums; the class by antiflag):
#   weapon      Zodiac +9 - Luk Zodiaku 2209 (N2), Sztylet Zodiaku 1189 (N1), Ostrze Zodiaku 309 (Sura),
#               a Warrior's two-handed Glewia Zodiaku 3229 or Miecz Zodiaku 319, a Shaman's Dzwon Zodiaku 5169
#               or Wachlarz Zodiaku 7309 (the kind the bots of that class and path wear most)
#   armour      no "Ambush/Boss" armour in our data - Zodiac +9: Zbroja 19299 (W), Ubranie 19499 (N),
#               Zbroja Plytowa 19699 (S), Szata 19899 (Sh) - with attack value and strong vs monsters
#   helmet      the 100-level helmets +9: Stalowy Helm Smokow 12699 (W), Smoczy Kaptur 12709 (N), Pancerny Helm
#               Smokow 12719 (S), Smoczy Kapelusz 12729 (Sh) - attack speed and skill defence
#   shield      Tarcza Tytanow +9 13149;   earrings  Szmaragdowe Kolczyki +9 17549
#   necklace    Naszyj. z Niebianskich Lez +9 16209;   bracelet  Bransol. z Niebianskich Lez +9 14209 (boss)
#   belt        Pas Dusz +9 18089;   shoes  Ogniste Buty +9 15449
#   sash        Szarfa Wladcy Absolutnego +3 85014 (socket 0 the absorption 25%, socket 1 the weapon absorbed)
#   talisman    Talizman Lodu (94500 + plus)
#   alchemy     Mythic, the highest step, +6: x5460 for the seven kinds (115460 ... 175460)
ARMOUR = {0: 19299, 1: 19499, 2: 19699, 3: 19899}
HELMET = {0: 12699, 1: 12709, 2: 12719, 3: 12729}
WEAPON_BY_SUBTYPE = {(0, 3): 3229, (0, 0): 319, (1, 1): 1189, (1, 2): 2209, (2, 0): 309, (3, 4): 5169, (3, 5): 7309}
SHIELD, EARRINGS, NECKLACE, BRACELET, BELT, SHOES, SASH = 13149, 17549, 16209, 14209, 18089, 15449, 85014
ICE_TALISMAN = 94500
ARROW = 8005                     # Srebrna Strzala (50)
MARBLE = 70104
POLY_MOBS = (502, 601, 2002)     # Dziki Sluga, Ork, Trujacy Pajak (the cores' PLAYERBOT_HYDRA_POLY_MOBS[pid % 3])
ELIXIRS = ((50831, ENCHANT_ICE), (50837, RES_ICE))
WEAPON_SOCKETS = (28437, 28430, 28431)
ARMOUR_SOCKETS = (28441, 28441, 28439)
SKILLS = {(0, 1): range(1, 7), (0, 2): range(16, 22), (1, 1): range(31, 37), (1, 2): range(46, 52),
          (2, 1): range(61, 67), (2, 2): range(76, 82), (3, 1): range(91, 97), (3, 2): range(106, 112)}
POLYMORPH_SKILL = 129
EQ_POS = '0,1,2,3,4,5,6,9,10,22,23,25,32,33,34,35,36,37,38'
KIT_VNUMS = '%d,%d,%d' % (MARBLE, ELIXIRS[0][0], ELIXIRS[1][0])

# The seven stones at Myth / highest step / +6 (dragon_soul_table.txt WeightTables GRADE_MYTH STEP_HIGHEST 160):
# each value ceil(base * 1.6 - 0.01), as DragonSoul.cpp puts them; the two basic ones, an empty third (the table
# has two), and three of the additional ones (the useful ones for a PvM bot).
def _w(v):
    return int(math.ceil(v * 1.6 - 0.01))

DS = {
    11: [(IQ, _w(8)), (MILGYO, _w(9)), (0, 0), (SKILL_DMG, _w(10)), (MAGIC_ATT_GRADE, _w(10)), (SKILL_DEF, _w(10))],
    12: [(ST, _w(8)), (DEVIL, _w(9)), (0, 0), (AVG_DMG, _w(10)), (ATT_GRADE, _w(200)), (AVG_DEF, _w(10))],
    13: [(MAX_SP, _w(500)), (ANIMAL, _w(9)), (0, 0), (MAX_HP, _w(2000)), (MAX_HP_PCT, _w(12)), (STEAL_HP, _w(6))],
    14: [(DX, _w(8)), (ORC, _w(9)), (0, 0), (RES_WARRIOR, _w(10)), (RES_ASSASSIN, _w(10)), (RES_SURA, _w(10))],
    15: [(MAX_HP, _w(1000)), (HUMAN, _w(6)), (0, 0), (MAX_SP, _w(1500)), (SP_REGEN, _w(10)), (MAX_SP_PCT, _w(20))],
    16: [(HT, _w(8)), (UNDEAD, _w(9)), (0, 0), (BLOCK, _w(8)), (DODGE, _w(8)), (RES_CRIT, _w(8))],
    17: [(MONSTER, _w(6)), (STONE, _w(6)), (0, 0), (CRIT, _w(5)), (PEN, _w(5)), (ATT_GRADE, _w(100))],
}


def caster(cls, grp):
    return cls == 3 or (cls == 2 and grp == 2)


def bonuses(pos, cls, grp):
    stat = IQ if caster(cls, grp) else (DX if (cls == 1 and grp == 2) else ST)
    if pos == 4:
        if caster(cls, grp):
            return [(SKILL_DMG, 30), (AVG_DMG, 10), (stat, 12), (CRIT, 10), (PEN, 10)]
        return [(AVG_DMG, 50), (SKILL_DMG, 10), (CRIT, 10), (PEN, 10), (stat, 12)]
    return {
        0: [(MAX_HP, 2000), (ATT_GRADE, 50), (MONSTER, 10), (STEAL_HP, 10), (RES_ICE, 15)],
        1: [(ATT_SPEED, 8), (HP_REGEN, 30), (SKILL_DEF, 10), (RES_MAGIC, 15), (POISON, 8)],
        2: [(MAX_HP, 2000), (MOV_SPEED, 20), (CRIT, 10), (ATT_SPEED, 8), (DODGE, 15)],
        3: [(MAX_HP, 2000), (BOSS, 15), (PEN, 10), (STEAL_HP, 10), (RES_ICE, 15)],
        5: [(MAX_HP, 2000), (BOSS, 15), (CRIT, 10), (HP_REGEN, 30), (STUN, 8)],
        6: [(MOV_SPEED, 20), (MONSTER, 10), (RES_ICE, 15), (POISON_REDUCE, 5), (DODGE, 15)],
        10: [(HT, 12), (BLOCK, 15), (MONSTER, 10), (IMMUNE_STUN, 1), (REFLECT, 10)],
    }[pos]


def attrs7(lst):
    lst = list(lst) + [(0, 0)] * (7 - len(lst))
    return ', '.join('%d, %d' % t for t in lst[:7])


# MT2009_PLUS_BOT_HYDRA_PAIRS_V1: a pair's partner, the owner's "healer Shaman or Warrior" first (a kept member's
# rank; the replacements take these in turn, the classes mixed), then the rest.
PARTNER_KEEP = {'Sh2': 0, 'W1': 1, 'W2': 1, 'S1': 2, 'S2': 2, 'Sh1': 3}
PARTNER_TURN = ['Sh2', 'W1', 'Sh2', 'W2', 'S1', 'Sh2', 'W1', 'S2']


def slot_of(b):
    return '%s%d' % (CLS[b['cls']], b['grp'])


def plan_pairs(npairs, earlier, bots, pool):
    """earlier: pid -> party of the Hydra's rows; pool: (emp, cls, grp) -> free bots, highest level first.
    Returns the members (with 'party') and the released pids."""
    cur = {e: {'N': [], 'O': []} for e in (1, 2, 3)}
    gone = [pid for pid in earlier if pid not in bots]
    for pid in sorted(earlier):
        b = bots.get(pid)
        if not b:
            continue
        cur[b['emp']]['N' if b['cls'] == 1 else 'O'].append(b)
    # a kept Ninja: an Archer first; a kept partner: the owner's classes first
    for e in cur:
        cur[e]['N'].sort(key=lambda b: (b['grp'] != 2, -b['old'], b['pid']))
        cur[e]['O'].sort(key=lambda b: (PARTNER_KEEP.get(slot_of(b), 9), -b['old'], b['pid']))
    pool_n = {e: len(pool[(e, 1, 2)]) + len(pool[(e, 1, 1)]) for e in (1, 2, 3)}
    pool_o = {e: sum(len(pool[(e, c, g)]) for c in (0, 2, 3) for g in (1, 2)) for e in (1, 2, 3)}
    best = None
    for p1 in range(npairs + 1):
        for p2 in range(npairs + 1 - p1):
            ps = {1: p1, 2: p2, 3: npairs - p1 - p2}
            if any(max(0, ps[e] - len(cur[e]['N'])) > pool_n[e] or max(0, ps[e] - len(cur[e]['O'])) > pool_o[e]
                   for e in ps):
                continue
            kept = sum(min(ps[e], len(cur[e]['N'])) + min(ps[e], len(cur[e]['O'])) for e in ps)
            archers = sum(sum(1 for b in cur[e]['N'][:ps[e]] if b['grp'] == 2) for e in ps)
            key = (kept, -(max(ps.values()) - min(ps.values())), archers, ps[1], ps[2])
            if best is None or key > best[0]:
                best = (key, ps)
    if best is None:
        sys.exit('hydra pairs: %d pairs of one kingdom cannot be made from the pool' % npairs)
    ps = best[1]
    members, released = [], list(gone)
    party = 0
    turn = collections.Counter()
    for e in (1, 2, 3):
        ninjas = cur[e]['N'][:ps[e]]
        others = cur[e]['O'][:ps[e]]
        released += [b['pid'] for b in cur[e]['N'][ps[e]:] + cur[e]['O'][ps[e]:]]
        while len(ninjas) < ps[e]:
            lst = pool[(e, 1, 2)] or pool[(e, 1, 1)]
            ninjas.append(lst.pop(0))
        while len(others) < ps[e]:
            got = None
            for k in range(len(PARTNER_TURN)):
                slot = PARTNER_TURN[(turn[e] + k) % len(PARTNER_TURN)]
                lst = pool[(e, CLS.index(slot[:-1]), int(slot[-1]))]
                if lst:
                    got = lst.pop(0)
                    turn[e] += k + 1
                    break
            if got is None:
                for c, g in itertools.product((3, 0, 2), (2, 1)):
                    if pool[(e, c, g)]:
                        got = pool[(e, c, g)].pop(0)
                        break
            others.append(got)
        # an Archer with the healer first, the Warriors next
        others.sort(key=lambda b: (PARTNER_KEEP.get(slot_of(b), 9), b['pid']))
        for n, o in zip(ninjas, others):
            party += 1
            for b in (n, o):
                m = dict(b)
                m['party'] = party
                members.append(m)
    print('hydra pairs: kingdoms %s, kept %d of %d, released %d, new %d' % (
        ps, best[0][0], len(earlier), len(released), len(members) - best[0][0]))
    return members, sorted(released)


def release_sql(pids, plist_of):
    """MT2009_PLUS_BOT_HYDRA_PAIRS_V1: the released members back as they were before their first apply (the backup
    tables, as cohort_restore.sql) and out of the cohort. Game stopped. A member without a backup row only leaves."""
    if not pids:
        return ['-- MT2009_PLUS_BOT_HYDRA_PAIRS_V1: nobody released.']
    pl = plist_of(pids)
    return ['-- MT2009_PLUS_BOT_HYDRA_PAIRS_V1: the members no pair keeps (%d), back as before their first apply.' % len(pids),
            'USE player;',
            'START TRANSACTION;',
            """UPDATE player.player p JOIN player.playerbot_yohara_cohort_bak_player b ON b.id = p.id
   SET p.exp = b.exp, p.level_step = b.level_step, p.st = b.st, p.ht = b.ht, p.dx = b.dx, p.iq = b.iq,
       p.stat_point = b.stat_point, p.skill_point = b.skill_point, p.sub_skill_point = b.sub_skill_point,
       p.random_hp = b.random_hp, p.random_sp = b.random_sp, p.gold = b.gold, p.skill_level = b.skill_level,
       p.level = b.level
 WHERE p.id IN (%s);""" % pl,
            """UPDATE common.playerbot_channel_assignment ca JOIN player.playerbot_yohara_cohort_bak_player b ON b.id = ca.pid
   SET ca.channel = b.channel_old, ca.requested_channel = 0, ca.request_reason = '', ca.request_at = NULL, ca.ready_at = NOW()
 WHERE b.channel_old IS NOT NULL AND ca.pid IN (%s);""" % pl,
            """DELETE i FROM player.item i JOIN player.playerbot_yohara_cohort_bak_player b ON b.id = i.owner_id
 WHERE i.owner_id IN (%s)
   AND ((i.window = 'EQUIPMENT' AND i.pos IN (%s)) OR (i.window = 'INVENTORY' AND i.vnum IN (%s)));""" % (pl, EQ_POS, KIT_VNUMS),
            'INSERT IGNORE INTO player.item SELECT * FROM player.playerbot_yohara_cohort_bak_item WHERE owner_id IN (%s);' % pl,
            'DELETE FROM common.playerbot_core_handover WHERE pid IN (%s);' % pl,
            "DELETE FROM common.playerbot_yohara_cohort WHERE purpose = 'hydra' AND pid IN (%s);" % pl,
            'DELETE FROM player.playerbot_yohara_cohort_bak_player WHERE id IN (%s);' % pl,
            'DELETE FROM player.playerbot_yohara_cohort_bak_item WHERE owner_id IN (%s);' % pl,
            'COMMIT;']


def run(a, q, bots, excluded, cohort_pids, usable):
    # ------------------------------------------------------------ who
    earlier = {}
    for r in q("SELECT pid, IFNULL(party, 0) FROM common.playerbot_yohara_cohort WHERE purpose = 'hydra';", fatal=False) or []:
        if r[0].isdigit():
            earlier[int(r[0])] = int(r[1] or 0)
    if not earlier:
        # an older table: no party column yet
        for r in q("SELECT pid FROM common.playerbot_yohara_cohort WHERE purpose = 'hydra';", fatal=False) or []:
            if r[0].isdigit():
                earlier[int(r[0])] = 0
    taken = set(cohort_pids) - set(earlier)
    if getattr(a, 'hydra_pairs', 0) > 0:
        # MT2009_PLUS_BOT_HYDRA_PAIRS_V1: a bot a dissolved cohort left with its backup (its level and gear of then
        # still in the backup tables) is no pick - a later restore would take it back to that night.
        stale = set(int(r[0]) for r in q('SELECT id FROM player.playerbot_yohara_cohort_bak_player;', fatal=False) or []
                    if r and r[0].isdigit())
        taken |= stale - set(earlier)
    parties = {}
    for pid, party in earlier.items():
        if pid in bots:
            parties.setdefault(party, []).append(bots[pid])
    want = a.hydra
    nparty = max(1, (want + 7) // 8)
    pool = collections.defaultdict(list)    # (emp, cls, grp) -> bots, highest level first
    for b in sorted(bots.values(), key=lambda b: (-b['old'], b['pid'])):
        if b['pid'] in taken or b['pid'] in earlier or not usable(b) or b['pid'] in excluded:
            continue
        pool[(b['emp'], b['cls'], b['grp'])].append(b)
    used_emp = []
    members = []
    released = []
    pairs = getattr(a, 'hydra_pairs', 0)
    if pairs > 0:	# MT2009_PLUS_BOT_HYDRA_PAIRS_V1
        members, released = plan_pairs(pairs, earlier, bots, pool)
        nparty = 0
    for p in range(1, nparty + 1):
        tpl = TEMPLATES[p - 1] if p <= len(TEMPLATES) else TEMPLATES[-1]
        tpl = tpl[:max(0, min(8, want - 8 * (p - 1)))]
        have = parties.get(p, [])
        if have:
            emp = have[0]['emp']
        elif p <= 3 and p not in used_emp and len(used_emp) < 3:
            emp = [e for e in (1, 2, 3) if e not in used_emp][0]
        else:
            # the kingdom with the most of the template left (its slots' levels summed)
            def score(e):
                s = 0
                for slot in tpl:
                    cls = CLS.index(slot[:-1]); grp = int(slot[-1])
                    lst = pool[(e, cls, grp)] or pool[(e, cls, 3 - grp)]
                    s += lst[0]['old'] if lst else -200
                return s
            emp = max((1, 2, 3), key=score)
        used_emp.append(emp)
        got = list(have)
        need = list(tpl)
        for b in got:
            key = '%s%d' % (CLS[b['cls']], b['grp'])
            if key in need:
                need.remove(key)
        for slot in need[:max(0, len(tpl) - len(got))]:
            cls = CLS.index(slot[:-1]); grp = int(slot[-1])
            lst = pool[(emp, cls, grp)] or pool[(emp, cls, 3 - grp)]
            if not lst:
                print('WARNING: hydra party %d kingdom %d - no %s left' % (p, emp, slot))
                continue
            got.append(lst.pop(0))
        for b in got:
            m = dict(b)
            m['party'] = p
            members.append(m)
    if len(members) < want:
        print('WARNING: hydra - only %d of %d members found' % (len(members), want))

    # ------------------------------------------------------------ items
    proto = {}
    for r in q('SELECT vnum, type, subtype, limittype0, limitvalue0, limittype1, limitvalue1, size FROM player.item_proto;'):
        v = int(r[0]); lv = 0
        if r[3] == '1':
            lv = int(r[4])
        elif r[5] == '1':
            lv = int(r[6])
        proto[v] = dict(type=int(r[1]), sub=int(r[2]), lv=lv, size=int(r[7]))
    for v in list(ARMOUR.values()) + list(HELMET.values()) + list(WEAPON_BY_SUBTYPE.values()) + \
            [SHIELD, EARRINGS, NECKLACE, BRACELET, BELT, SHOES, SASH, ARROW, MARBLE, ELIXIRS[0][0], ELIXIRS[1][0]] + \
            [t * 10000 + 5460 for t in DS]:
        if v not in proto:
            sys.exit('item %d is not in item_proto' % v)
    # the weapon kind the bots of a class and path wear most (a Warrior's two-handed or one-handed, a
    # Shaman's bell or fan)
    kind = collections.defaultdict(collections.Counter)
    for r in q("""SELECT p.job % 4, p.skill_group, ip.subtype, COUNT(*) FROM player.player p
                   JOIN account.account ac ON ac.id = p.account_id
                   JOIN player.item i ON i.owner_id = p.id AND i.window = 'EQUIPMENT' AND i.pos = 4
                   JOIN player.item_proto ip ON ip.vnum = i.vnum
                  WHERE LEFT(ac.login, 10) = 'playerbot_' AND p.level >= 50 AND p.skill_group IN (1, 2) GROUP BY 1, 2, 3;"""):
        kind[(int(r[0]), int(r[1]))][int(r[2])] += int(r[3])

    def weapon(cls, grp):
        subs = [s for (c, s) in WEAPON_BY_SUBTYPE if c == cls]
        if len(subs) == 1:
            return WEAPON_BY_SUBTYPE[(cls, subs[0])]
        if cls == 1:
            return WEAPON_BY_SUBTYPE[(1, 2 if grp == 2 else 1)]
        best = max(subs, key=lambda s: (kind[(cls, grp)][s], -s))
        return WEAPON_BY_SUBTYPE[(cls, best)]

    tal = None
    for plus in range(0, 151):
        p = proto.get(ICE_TALISMAN + plus)
        if p and p['lv'] <= LEVEL:
            tal = ICE_TALISMAN + plus

    def skills_for(b):
        blob = bytearray.fromhex(b['skills']) if b['skills'] else bytearray()
        if len(blob) < 1590:
            blob += bytearray(1590 - len(blob))
        for v in SKILLS[(b['cls'], b['grp'])]:
            blob[v * 6] = 3
            blob[v * 6 + 1] = 40
        if b['cls'] == 1 and b['grp'] == 2:
            blob[POLYMORPH_SKILL * 6] = 3
            blob[POLYMORPH_SKILL * 6 + 1] = 40
        return blob.hex().upper()

    # ------------------------------------------------------------ SQL
    pids = sorted(m['pid'] for m in members)
    plist = ','.join(str(x) for x in pids) or '0'
    S = []
    S.append('-- MT2009_PLUS_BOT_HYDRA_COHORT_V1: the Hydra\'s cohort (tools/yohara_bot_cohort.py --hydra). Game stopped.')
    S.append('-- %d members, parties %s' % (len(members), dict(collections.Counter(m['party'] for m in members))))
    S.append('SET NAMES latin1;')
    S.append("""CREATE TABLE IF NOT EXISTS common.playerbot_yohara_cohort (
  pid INT UNSIGNED NOT NULL PRIMARY KEY, purpose VARCHAR(16) NOT NULL, channel TINYINT UNSIGNED NOT NULL DEFAULT 1,
  rest_until DATETIME NULL, created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  level_start TINYINT UNSIGNED NOT NULL DEFAULT 0, exp_start INT UNSIGNED NOT NULL DEFAULT 0,
  sent INT UNSIGNED NOT NULL DEFAULT 0, arrived INT UNSIGNED NOT NULL DEFAULT 0, deaths INT UNSIGNED NOT NULL DEFAULT 0,
  runs INT UNSIGNED NOT NULL DEFAULT 0, rest_outs INT UNSIGNED NOT NULL DEFAULT 0, exp_gained BIGINT UNSIGNED NOT NULL DEFAULT 0,
  last_map INT NOT NULL DEFAULT 0, last_seen DATETIME NULL, applied_at DATETIME NULL, KEY purpose (purpose)) ENGINE=InnoDB;""")
    S.append('ALTER TABLE common.playerbot_yohara_cohort ADD COLUMN IF NOT EXISTS applied_at DATETIME NULL, '
             'ADD COLUMN IF NOT EXISTS party TINYINT UNSIGNED NOT NULL DEFAULT 0, ADD COLUMN IF NOT EXISTS wins INT UNSIGNED NOT NULL DEFAULT 0;')
    S.append("""CREATE TABLE IF NOT EXISTS player.playerbot_yohara_cohort_bak_player (
  id INT UNSIGNED NOT NULL PRIMARY KEY, level TINYINT UNSIGNED NOT NULL, exp INT UNSIGNED NOT NULL, level_step TINYINT NOT NULL,
  st SMALLINT NOT NULL, ht SMALLINT NOT NULL, dx SMALLINT NOT NULL, iq SMALLINT NOT NULL, stat_point SMALLINT NOT NULL,
  skill_point SMALLINT NOT NULL, sub_skill_point SMALLINT NOT NULL, random_hp SMALLINT NOT NULL, random_sp SMALLINT NOT NULL,
  gold BIGINT NOT NULL, skill_level BLOB NULL, channel_old TINYINT UNSIGNED NULL, saved_at DATETIME NOT NULL) ENGINE=InnoDB;""")
    # MT2009_PLUS_EXP_UNSIGNED_V1: player.player.exp is INT UNSIGNED (the level-120 bar is 2.5 bn); a backup table
    # made before as INT would clamp a saved exp at 2 147 483 647.
    S.append('ALTER TABLE player.playerbot_yohara_cohort_bak_player MODIFY exp INT UNSIGNED NOT NULL;')
    S.append('CREATE TABLE IF NOT EXISTS player.playerbot_yohara_cohort_bak_item LIKE player.item;')
    rel = release_sql(released, plist_of=lambda xs: ','.join(str(x) for x in xs))
    if released:
        S.extend(rel)
    S.append('START TRANSACTION;')
    if members:
        S.append('INSERT IGNORE INTO common.playerbot_yohara_cohort (pid, purpose, channel, level_start, created_at, party) VALUES')
        S.append(',\n'.join("  (%d, 'hydra', %d, %d, NOW(), %d)" % (m['pid'], a.channel, LEVEL, m['party']) for m in members) + ';')
        S.append("UPDATE common.playerbot_yohara_cohort SET party = CASE pid %s END WHERE purpose = 'hydra' AND pid IN (%s);" % (
            ' '.join('WHEN %d THEN %d' % (m['pid'], m['party']) for m in members), plist))
    S.append('-- the backups, once a member (applied_at still NULL, not backed up yet)')
    S.append("""INSERT IGNORE INTO player.playerbot_yohara_cohort_bak_player
SELECT p.id, p.level, p.exp, p.level_step, p.st, p.ht, p.dx, p.iq, p.stat_point, p.skill_point, p.sub_skill_point,
       p.random_hp, p.random_sp, p.gold, p.skill_level, ca.channel, NOW()
  FROM player.player p JOIN common.playerbot_yohara_cohort c ON c.pid = p.id AND c.applied_at IS NULL AND c.purpose = 'hydra'
  LEFT JOIN common.playerbot_channel_assignment ca ON ca.pid = p.id;""")
    S.append("""INSERT IGNORE INTO player.playerbot_yohara_cohort_bak_item
SELECT i.* FROM player.item i JOIN common.playerbot_yohara_cohort c ON c.pid = i.owner_id AND c.applied_at IS NULL AND c.purpose = 'hydra'
 WHERE ((i.window = 'EQUIPMENT' AND i.pos IN (%s)) OR (i.window = 'INVENTORY' AND i.vnum IN (%s)))
   AND i.owner_id NOT IN (SELECT DISTINCT owner_id FROM player.playerbot_yohara_cohort_bak_item);""" % (EQ_POS, KIT_VNUMS))
    S.append('-- the characters (only while applied_at is NULL; level last - MariaDB assigns left to right)')
    for m in sorted(members, key=lambda x: x['pid']):
        S.append("""UPDATE player.player p JOIN common.playerbot_yohara_cohort c ON c.pid = p.id AND c.applied_at IS NULL
   SET p.stat_point = IF(p.level < %(L)d, 0, GREATEST(p.stat_point, LEAST(3 * (p.level - 1), 344) - (p.st + p.ht + p.dx + p.iq - 16))),
       p.st = IF(p.level < %(L)d, 90, p.st), p.ht = IF(p.level < %(L)d, 90, p.ht),
       p.dx = IF(p.level < %(L)d, 90, p.dx), p.iq = IF(p.level < %(L)d, 90, p.iq),
       p.sub_skill_point = p.sub_skill_point + GREATEST(0, %(L)d - GREATEST(p.level, 8)),
       p.random_hp = GREATEST(p.random_hp, 40 * (%(L)d - 1)), p.random_sp = GREATEST(p.random_sp, 20 * (%(L)d - 1)),
       p.gold = GREATEST(p.gold, %(G)d), p.skill_level = UNHEX('%(blob)s'),
       p.exp = GREATEST(IF(p.level < %(L)d, 0, p.exp), %(E)d), p.level_step = IF(p.level < %(L)d, 0, p.level_step),
       p.level = GREATEST(p.level, %(L)d)
 WHERE p.id = %(pid)d;""" % dict(L=LEVEL, G=GOLD, E=EXP, blob=skills_for(m), pid=m['pid']))
    S.append("""INSERT INTO common.playerbot_channel_assignment (pid, channel, ready_at) SELECT c.pid, %d, NOW()
  FROM common.playerbot_yohara_cohort c WHERE c.applied_at IS NULL AND c.purpose = 'hydra'
ON DUPLICATE KEY UPDATE channel = VALUES(channel), requested_channel = 0, request_reason = '', request_at = NULL, ready_at = NOW();""" % a.channel)
    S.append("UPDATE common.playerbot_yohara_cohort c JOIN player.player p ON p.id = c.pid SET c.applied_at = NOW(), "
             "c.level_start = p.level, c.exp_start = p.exp WHERE c.applied_at IS NULL AND c.purpose = 'hydra';")
    S.append('-- the equipment and the kit (put back every run)')
    S.append("DELETE FROM player.item WHERE window = 'EQUIPMENT' AND pos IN (%s) AND owner_id IN (%s);" % (EQ_POS, plist))
    S.append("DELETE FROM player.item WHERE window = 'INVENTORY' AND vnum IN (%s) AND owner_id IN (%s);" % (KIT_VNUMS, plist))
    ins = []
    rows = []
    for m in sorted(members, key=lambda x: x['pid']):
        cls, grp, pid = m['cls'], m['grp'], m['pid']
        wv = weapon(cls, grp)
        wat = bonuses(4, cls, grp)
        gear = [(0, ARMOUR[cls], ARMOUR_SOCKETS, bonuses(0, cls, grp)), (1, HELMET[cls], (0, 0, 0), bonuses(1, cls, grp)),
                (2, SHOES, (0, 0, 0), bonuses(2, cls, grp)), (3, BRACELET, (0, 0, 0), bonuses(3, cls, grp)),
                (4, wv, WEAPON_SOCKETS, wat), (5, NECKLACE, (0, 0, 0), bonuses(5, cls, grp)),
                (6, EARRINGS, (0, 0, 0), bonuses(6, cls, grp)), (10, SHIELD, (0, 0, 0), bonuses(10, cls, grp)),
                (22, SASH, (25, wv, 0), wat), (23, BELT, (0, 0, 0), [])]
        if tal:
            gear.append((25, tal, (0, 0, 0), []))
        for pos, v, sock, at in gear:
            ins.append("  (%d, 'EQUIPMENT', %d, 1, %d, %d, %d, %d, %s)" % (pid, pos, v, sock[0], sock[1], sock[2], attrs7(at)))
        for t, at in sorted(DS.items()):
            ins.append("  (%d, 'EQUIPMENT', %d, 1, %d, 86400, 0, 0, %s)" % (pid, 32 + t - 11, t * 10000 + 5460, attrs7(at)))
        if cls == 1 and grp == 2:
            ins.append("  (%d, 'EQUIPMENT', 9, 200, %d, 0, 0, 0, %s)" % (pid, ARROW, attrs7([])))
        rows.append((m, wv))
    S.append('INSERT INTO player.item (owner_id, window, pos, count, vnum, socket0, socket1, socket2, '
             'attrtype0, attrvalue0, attrtype1, attrvalue1, attrtype2, attrvalue2, attrtype3, attrvalue3, '
             'attrtype4, attrvalue4, attrtype5, attrvalue5, attrtype6, attrvalue6) VALUES\n' + ',\n'.join(ins) + ';')
    S.append('-- the bag: an Archer Ninja\'s three marbles, everyone\'s two ice elixirs - each in the first free cell of the')
    S.append('-- bag\'s four pages (none free: the core gives them on the pier, RestockPlayerBotYoharaHydra)')
    cell = """INSERT INTO player.item (owner_id, window, pos, count, vnum, socket0, socket1, socket2)
WITH RECURSIVE n(pos) AS (SELECT 0 UNION ALL SELECT pos + 1 FROM n WHERE pos < 179)
SELECT %(pid)d, 'INVENTORY', MIN(n.pos), %(count)d, %(vnum)d, %(s0)d, %(s1)d, %(s2)d FROM n
 WHERE NOT EXISTS (SELECT 1 FROM player.item i JOIN player.item_proto ip ON ip.vnum = i.vnum
                    WHERE i.owner_id = %(pid)d AND i.window = 'INVENTORY' AND n.pos >= i.pos
                      AND n.pos < i.pos + 5 * GREATEST(ip.size, 1) AND (n.pos - i.pos) %% 5 = 0)
HAVING MIN(n.pos) IS NOT NULL;"""
    for m, wv in rows:
        if m['cls'] == 1 and m['grp'] == 2:
            for _ in range(3):
                S.append(cell % dict(pid=m['pid'], count=1, vnum=MARBLE, s0=POLY_MOBS[m['pid'] % 3], s1=0, s2=0))
        for v, point in ELIXIRS:
            S.append(cell % dict(pid=m['pid'], count=10, vnum=v, s0=point, s1=20, s2=600))
    S.append('COMMIT;')
    S.append("SELECT c.party, COUNT(*) AS members, MIN(p.level) AS lv_min, MAX(p.level) AS lv_max, MIN(p.exp) AS exp_min, "
             "SUM(c.applied_at IS NOT NULL) AS applied FROM common.playerbot_yohara_cohort c JOIN player.player p ON p.id = c.pid "
             "WHERE c.purpose = 'hydra' GROUP BY c.party;")
    S.append("SELECT COUNT(*) AS gear_rows FROM player.item WHERE window = 'EQUIPMENT' AND pos IN (%s) AND owner_id IN (%s);" % (EQ_POS, plist))
    S.append("SELECT vnum, COUNT(DISTINCT owner_id) AS bots, SUM(count) AS items FROM player.item WHERE window = 'INVENTORY' "
             "AND vnum IN (%s) AND owner_id IN (%s) GROUP BY vnum;" % (KIT_VNUMS, plist))
    open(os.path.join(a.outdir, 'cohort_apply.sql'), 'w', encoding='latin-1').write('\n'.join(S) + '\n')

    D = ['-- MT2009_PLUS_BOT_HYDRA_COHORT_V1: the Hydra\'s cohort dissolved (the bots keep their level and gear).',
         '-- Safe with the game running: the cores read the table every minute; residents finish their stay as',
         '-- ordinary bots and come home through the handover.',
         'USE common;',
         "DELETE h FROM common.playerbot_core_handover h JOIN common.playerbot_yohara_cohort c ON c.pid = h.pid "
         "WHERE h.state = 1 AND c.purpose = 'hydra';",
         "DELETE FROM common.playerbot_yohara_cohort WHERE purpose = 'hydra';"]
    open(os.path.join(a.outdir, 'cohort_dissolve.sql'), 'w').write('\n'.join(D) + '\n')

    R = ['-- MT2009_PLUS_BOT_HYDRA_COHORT_V1: the Hydra\'s members back as they were before the first apply. Game stopped.',
         'SET NAMES latin1;',
         'USE player;',
         'START TRANSACTION;',
         """UPDATE player.player p JOIN player.playerbot_yohara_cohort_bak_player b ON b.id = p.id
   SET p.exp = b.exp, p.level_step = b.level_step, p.st = b.st, p.ht = b.ht, p.dx = b.dx, p.iq = b.iq,
       p.stat_point = b.stat_point, p.skill_point = b.skill_point, p.sub_skill_point = b.sub_skill_point,
       p.random_hp = b.random_hp, p.random_sp = b.random_sp, p.gold = b.gold, p.skill_level = b.skill_level,
       p.level = b.level
 WHERE p.id IN (%s);""" % plist,
         """UPDATE common.playerbot_channel_assignment ca JOIN player.playerbot_yohara_cohort_bak_player b ON b.id = ca.pid
   SET ca.channel = b.channel_old WHERE b.channel_old IS NOT NULL AND ca.pid IN (%s);""" % plist,
         """DELETE FROM player.item WHERE owner_id IN (%s)
   AND ((window = 'EQUIPMENT' AND pos IN (%s)) OR (window = 'INVENTORY' AND vnum IN (%s)));""" % (plist, EQ_POS, KIT_VNUMS),
         'INSERT IGNORE INTO player.item SELECT * FROM player.playerbot_yohara_cohort_bak_item WHERE owner_id IN (%s);' % plist,
         'DELETE FROM common.playerbot_core_handover WHERE pid IN (%s);' % plist,
         "DELETE FROM common.playerbot_yohara_cohort WHERE purpose = 'hydra';",
         'DELETE FROM player.playerbot_yohara_cohort_bak_player WHERE id IN (%s);' % plist,
         'DELETE FROM player.playerbot_yohara_cohort_bak_item WHERE owner_id IN (%s);' % plist,
         'COMMIT;']
    open(os.path.join(a.outdir, 'cohort_restore.sql'), 'w').write('\n'.join(R) + '\n')
    # MT2009_PLUS_BOT_HYDRA_PAIRS_V1: the release alone (cohort_apply.sql begins with it too).
    if getattr(a, 'hydra_pairs', 0) > 0:
        open(os.path.join(a.outdir, 'cohort_release.sql'), 'w').write(
            '\n'.join(['SET NAMES latin1;'] + rel) + '\n')
        with open(os.path.join(a.outdir, 'released.tsv'), 'w', encoding='latin-1') as f:
            f.write('pid\tname\tparty_before\tempire\tclass\tpath\n')
            for pid in released:
                b = bots.get(pid)
                if b:
                    f.write('%d\t%s\t%d\t%d\t%s\t%d\n' % (pid, b['name'], earlier.get(pid, 0), b['emp'], CLS[b['cls']], b['grp']))
                else:
                    f.write('%d\t?\t%d\t0\t?\t0\n' % (pid, earlier.get(pid, 0)))

    with open(os.path.join(a.outdir, 'pick.tsv'), 'w', encoding='latin-1') as f:
        f.write('pid\tname\tparty\tempire\tclass\tpath\tlevel_before\tlevel_after\tweapon\tpolymorph_mob\n')
        for m, wv in sorted(rows, key=lambda x: (x[0]['party'], x[0]['cls'], x[0]['grp'], x[0]['pid'])):
            poly = POLY_MOBS[m['pid'] % 3] if (m['cls'] == 1 and m['grp'] == 2) else 0
            f.write('%d\t%s\t%d\t%d\t%s\t%d\t%d\t%d\t%d\t%d\n' % (m['pid'], m['name'], m['party'], m['emp'], CLS[m['cls']],
                    m['grp'], m['old'], max(m['old'], LEVEL), wv, poly))
    open(os.path.join(a.outdir, 'pids.txt'), 'w').write(' '.join(map(str, pids)) + '\n')
    for p in sorted(set(m['party'] for m in members)):
        ms = [m for m in members if m['party'] == p]
        print('hydra party %d  kingdom %s  %d members  %s  level before %d-%d  talisman %s' % (
            p, sorted(set(m['emp'] for m in ms)), len(ms),
            dict(sorted(collections.Counter('%s%d' % (CLS[m['cls']], m['grp']) for m in ms).items())),
            min(m['old'] for m in ms), max(m['old'] for m in ms), tal))
