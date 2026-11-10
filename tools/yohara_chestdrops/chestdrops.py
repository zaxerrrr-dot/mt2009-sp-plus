#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""chestdrops.py [CHEST ...]

MT2009_PLUS_CHEST_DROPS_V1: the contents and chances of the Yohara 3.0 chests (and of Skrzynia Razadora / Nemere)
from the owner's sheet of 15 October 2026 (chest_drops_2026-10-15_v2.tsv, a copy of cache/yohara/
metin2alerts_drop_2026-10-15_v2.csv: community data, estimated chances of ONE opening). The chest generators
(tools/yohara_items, yohara_maps3, yohara_maps4, yohara_dung4, yohara_pb, yohara_iluzja, yohara_zaklety) take their
groups from table(); the hand-made groups (game/shipdefense: 54705, 72058; game/special_item_group.dungeons.txt:
50270, 50271 - the sheet's 54702 / 54703 - and 54700, Skrzynia Berana-Setaou) were written from it too, verify_chestdrops.py keeps them all equal.

Each sheet row: the official vnum -> ours. The same vnum when our world has it (world.item_proto, checked by
verify_chestdrops.py --db), else SUBST (our number of the same item) or SKIP (a system we lack - left out). The
chances of the rows left are scaled to weights summing to SCALE (one opening = one row by weight, a normal special
group: CSpecialItemGroup::GetOneIndex), so a weight / 1000 is the percent. Exact duplicates (the same item, the same
count) are one row with their chances summed; the same item with other counts stays separate rows. FIXED keeps a
row at the owner's own chance (Skrzynia Hydry: Magiczny Kamien 4%, 13 October), the rest scaled to what is left.
EXTRA adds rows the sheet lacks at a chance of their own (Skrzynia Berana-Setaou 54700: the pl-wiki's items without a
rate, MT2009_PLUS_BERAN_CHEST_V1), the sheet's rows scaled to what is left.

MT2009_PLUS_CHEST_DROPS_V2: the owner's sheet of 20 October 2026 (all ~370 chests, read 16 October; its 31 chests of
the first sheet are the same) adds chest_drops_2026-10-20_add.tsv - only our chests that had no group at all: Skrzynia
Triumfu (50249, a row of Losowa Skrzynia Skarbow 83065; group from tools/yohara_items/gen_yitems2.py) and the Zodiac
Temple's Skarb Aureolin / Skarb Aventurin / Gwiezdny Skarb (33026-33028; game/zodiak/special_item_group.zodiak.txt).

Example: python3 tools/yohara_chestdrops/chestdrops.py 54705     (prints the group's rows and what is left out)
"""
import os
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
SHEET = os.path.join(HERE, 'chest_drops_2026-10-15_v2.tsv')
# MT2009_PLUS_CHEST_DROPS_V2: the chests the first sheet lacks (the owner's sheet of 20 October 2026)
SHEETS = (SHEET, os.path.join(HERE, 'chest_drops_2026-10-20_add.tsv'))
SHEET_DATE = {SHEET: '15 October 2026', SHEETS[1]: '20 October 2026'}
SOURCE = {}                                     # our chest -> the sheet's date (filled by sheet())
SCALE = 100000

# the sheet's chest -> our chest (the official Razador / Nemere chests are 50270 / 50271 here, the dungeons' quests)
OUR_CHEST = {54702: 50270, 54703: 50271}

# the official vnum (with its time limit when it matters) -> our vnum of the same item: (ours, a note for the row)
SUBST = {
    50926: (95926, 'ours 95926 (50926 is a recipe here)'),
    72301: (25040, ''),
    72310: (71001, ''),
    39001: (25042, ''),
    (76038, '30m'): (72023, ''),
    (76037, '30m'): (72006, ''),
    (76037, '2h'): (70043, ''),
    (76037, '3h'): (70043, 'the 2 h one - none of 3 h here'),
    30600: (95602, ''),
    30611: (95603, ''),
    30612: (95601, ''),
    76044: (55009, 'ours 55009'),
    9999999: ('exp', ''),
    1: ('gold', ''),
}

# the official vnum -> why it is left out (no such item / system in our world)
_LYCAN = 'the Lycan\'s (no such class here)'
SKIP = {
    55400: 'no system',
    38060: 'no system',
    72051: 'no system',
    72052: 'no system',
    60004: 'no system',
    60005: 'no system',
    72355: 'no system',
    72356: 'no system',
    72351: 'not in our world',
    9999998: 'a group gives no champion EXP',
    27213: 'not in our world',
    27214: 'not in our world',
    27215: 'not in our world',
    27216: 'not in our world',
    # 31230 / 31231 / 31232 (Oczyszczony Rdzen, Krysztal Metin, Mroczna Paproc) are ours since
    # MT2009_PLUS_BIOLOGIST_YOHARA_V1 (tools/ybiolog, 29 October 2026) - back in Plat. Skrzynia Skarbow
    39067: 'not in our world',
    72350: 'not in our world',
    # 50514 / 50515 (Podreczniki: Dopalacz / Riposta) are ours since MT2009_PLUS_RIPOSTY_V1 (tools/yohara_items)
    # MT2009_PLUS_ARMOR105_V1 (22 October 2026): the level-105 armours' materials 30601, 30605, 30607, 30609, 30614,
    # 30615, 30619, 30625, 30628 are ours (tools/zbroje105) - back in the chests
    # MT2009_PLUS_GROWTH_PET_V1 (4 November 2026): Biale Jajo Smoka (55412) and the Ksiegi Dzikiego / Dzielnego
    # Zwierza (55004 / 55005) are ours (mariadb/playerbot/pety.sql) - back in B. Smocza Skrz. (ciezka), Skrzynia
    # Razadora / Nemere / Jotuna Thryma / Bagjanamu. Losowa Skrzynka (55400, Skrzynka na Zwierzaka) stays out.
}
# MT2009_PLUS_CHEST_DROPS_V2: the Zodiac treasures' rows we lack (as Zlota Skrzynia Zodiaku 33033 leaves them out)
for _v in (86001, 86011, 86021, 86031, 86041, 86051):              # Szarfa Zi/Yin/Chen/Wu/Shen/Xu (prosta)
    SKIP[_v] = 'not in our world'
for _v in (9600, 9830, 10060, 10290, 10520, 10750):                # Talizman Ognia/Lodu/Ziemi/Mroku/Wiatru/Blyskawicy+0
    SKIP[_v] = 'not in our world'
for _v in (6045, 6046, 6047, 6073, 6074, 6093, 6130, 6150, 21073, 21074, 21075, 21076, 21077, 21090, 21093, 21290,
           50524, 50568, 50576, 28012, 28112, 28212, 28312, 28412,      # 280x2: Kamien Duszy Likanow
           6120, 21200):                                                # Szpon / Pancerz Zodiaku (V2, as 33033)
    SKIP[_v] = _LYCAN
# MT2009_PLUS_NO_ROTTEN_CHEST_V1: Sprochniala Skrzynia out of every drop and chest (the owner, 15 October 2026, fix 7)
SKIP[50124] = 'no Sprochniala Skrzynia in any drop - owner 15.10'
# MT2009_PLUS_NO_TRZECH_WLADCOW_V1: Tarcza Trzech Wladcow out of every drop and chest (the owner, 10 November 2026)
for _v in range(13160, 13170):
    SKIP[_v] = 'no Tarcza Trzech Wladcow in any drop - owner 10.11'

# MT2009_PLUS_ANTI_RESIST_MAGIC_V1 (tools/antimagic, 28 October 2026): Kamien Antymagii is ours now. The sheet has two
# rows of each grade, both "Kamien Antymagii+N" with the armour stone's vnum (28045 + 100*N - the official weapon and
# armour stones share the name); the second of them is the weapon stone 28044 + 100*N (Kamien Duszy Antymagii).
TWIN = dict((28045 + 100 * g, 28044 + 100 * g) for g in range(10))

# our chest -> {our vnum: the owner's own weight of SCALE}
FIXED = {54705: {25042: 4000}}      # Skrzynia Hydry: Magiczny Kamien exactly 4% (the owner, 13 October 2026)

# MT2009_PLUS_BERAN_CHEST_V1: our chest -> rows the sheet lacks, at a chance of their own: (our vnum, count, chance of one
# opening, name). Skrzynia Berana-Setaou (54700, the owner 15 October 2026): the pl-wiki's "Zawartosc" items with no
# rate in the sheet, each at the sheet's rare rows' 0.74627% (Wzmocnienie Przedmiotu's); the sheet's rows are scaled
# down to what is left. The boots +4 as Beran-Setaou drops them (pl-wiki: "max ulepszone +4").
_BERAN_RARE = 0.0074627
_WIKI = 'wiki, no rate - owner 15.10'
EXTRA = {54700: [
    (15374, 1, _BERAN_RARE, 'Buty Euforii+4 - ' + _WIKI),
    (15414, 1, _BERAN_RARE, 'Buty Qilina+4 - ' + _WIKI),
    (15434, 1, _BERAN_RARE, 'Buty Zimorodka+4 - ' + _WIKI),
    (15394, 1, _BERAN_RARE, 'Kozaki Glorii+4 - ' + _WIKI),
    (27003, 100, _BERAN_RARE, 'Czerwona Mikstura(D) x100 - ' + _WIKI),
    (27002, 100, _BERAN_RARE, 'Czerwona Mikstura(S) x100 - ' + _WIKI),
    (27002, 200, _BERAN_RARE, 'Czerwona Mikstura(S) x200 - ' + _WIKI),
    (27006, 100, _BERAN_RARE, 'Niebieska Mikstura(D) x100 - ' + _WIKI),
    (27005, 100, _BERAN_RARE, 'Niebieska Mikstura(S) x100 - ' + _WIKI),
    (27005, 200, _BERAN_RARE, 'Niebieska Mikstura(S) x200 - ' + _WIKI),
    (71083, 1, _BERAN_RARE, 'Ksiega Obrobki Kamienia - ' + _WIKI),
    (71123, 1, _BERAN_RARE, 'Smocza Luska - ' + _WIKI),
    (71129, 1, _BERAN_RARE, 'Smoczy Szpon - ' + _WIKI),
]}
EXTRA_NOTE = {54700: ('MT2009_PLUS_BERAN_CHEST_V1', 'the pl-wiki\'s list, no rate - the owner, 15 October 2026')}

# MT2009_PLUS_BRAKI_WIKI_V1 (the owner, 5 November 2026: "Dodaj zgodnie z Wiki Global"): Skrzynia Jotuna Thryma (50266) -
# the pl-wiki's "Skrzynia Jotuna Thryma", "Srebrne Plyty" and "Stalowe Plyty" list both plates, the sheet has neither;
# each at the sheet's dye / pearl rows' 1.961% (the wiki gives no rate), the sheet's rows scaled to what is left.
EXTRA.setdefault(50266, []).extend([(30606, 1, 0.01961, 'Srebrne Plyty - wiki, no rate - owner 5.11'),
                                    (30608, 1, 0.01961, 'Stalowe Plyty - wiki, no rate - owner 5.11')])
EXTRA_NOTE[50266] = ('MT2009_PLUS_BRAKI_WIKI_V1', 'the pl-wiki\'s plates, no rate - the owner, 5 November 2026')

# MT2009_PLUS_MIKSTURY_V1 (the owner, 4 November 2026, M3): Zlote Ziolo (50741, the golden elixirs' herb) rarely from the
# Yohara bosses' chests - the four of Jaskinie Gnolli / Wieza Sung Mahi (Gnoll Kapitan, Ahtrin Kapitan, Ahtrin Wielki
# Mistrz); 1% an opening (the wiki gives no rate; the Water Nymph chest's ~1%), the sheet's rows scaled to what is left.
GOLDEN_HERB_CHESTS = (31253, 31254, 31255, 31256)
for _c in GOLDEN_HERB_CHESTS:
    EXTRA.setdefault(_c, []).append((50741, 1, 0.01, 'Zlote Ziolo - owner 4.11, 1%'))
    EXTRA_NOTE[_c] = ('MT2009_PLUS_MIKSTURY_V1', 'Zlote Ziolo for the golden elixirs - the owner, 4 November 2026')


def ascii_pl(s):
    s = s.replace('ł', 'l').replace('Ł', 'L')
    s = unicodedata.normalize('NFKD', s)
    return ''.join(c for c in s if not unicodedata.combining(c))


def sheet():
    """our chest -> [(official chest, item name, count, chance, official vnum, time)] in the sheet's order"""
    out = {}
    for path in SHEETS:
        part = {}
        for line in open(path, encoding='utf-8'):
            t = line.rstrip('\n').split('\t')
            if len(t) != 7 or not t[0].isdigit():
                continue
            c = int(t[0])
            part.setdefault(OUR_CHEST.get(c, c), []).append((c, t[2], int(t[3]), float(t[4]), int(t[5]), t[6]))
        assert not set(part) & set(out), (path, 'a chest of an earlier sheet', sorted(set(part) & set(out)))
        out.update(part)
        SOURCE.update((c, SHEET_DATE[path]) for c in part)
    return out


def ours(v, time):
    """the official vnum -> (our vnum or 'exp' / 'gold', note) or (None, why left out)"""
    if (v, time) in SUBST:
        return SUBST[(v, time)]
    if v in SUBST:
        return SUBST[v]
    if v in SKIP:
        return None, SKIP[v]
    return v, ''


def table(chest):
    """(rows, skipped): rows [(vnum string, count, weight, name)], weights summing to SCALE; skipped [(name, count,
    chance, why)] - the sheet's rows left out"""
    rows, skipped, at = [], [], {}
    for _, name, count, chance, v, time in sheet()[chest]:
        o, note = ours(v, time)
        nm = ascii_pl(name) + (' x%d' % count if count > 1 else '')
        nm += ' (%s)' % time if time and '(%s)' % time not in nm else ''
        if o is None:
            skipped.append((ascii_pl(name), count, chance, note))
            continue
        if o in ('gold', 'exp'):
            nm = '%s %d' % ('Yang' if o == 'gold' else 'EXP', count)
        if note:
            nm += ' - ' + note
        key = (str(o), count)
        if o in TWIN:
            nm = nm.replace('Kamien Antymagii', 'Bialy Kamien Antymagii')
        if key in at and o in TWIN and (str(TWIN[o]), count) not in at:
            o = TWIN[o]                         # MT2009_PLUS_ANTI_RESIST_MAGIC_V1: the second row is the weapon stone
            nm = nm.replace('Bialy Kamien Antymagii', 'Kamien Duszy Antymagii') + ' - ours %d (the weapon stone)' % o
            key = (str(o), count)
        if key in at:                           # the same item and count twice: one row, the chances summed
            rows[at[key]][2] += chance
            continue
        at[key] = len(rows)
        rows.append([str(o), count, chance, nm])
    fixed = FIXED.get(chest, {})
    extra = [(str(v), c, max(1, int(round(p * SCALE))), nm) for v, c, p, nm in EXTRA.get(chest, [])]
    assert not set((v, c) for v, c, _, _ in extra) & set(at), (chest, 'an extra row is in the sheet')
    free = SCALE - sum(fixed.values()) - sum(w for _, _, w, _ in extra)
    total = sum(r[2] for r in rows if not (r[1] == 1 and r[0] in map(str, fixed)))
    out = []
    for vn, count, chance, nm in rows:
        if count == 1 and vn in map(str, fixed):
            w = fixed[int(vn)]
        else:
            w = max(1, int(round(chance * free / total)))
        out.append((vn, count, w, nm))
    out += extra
    assert all(int(v) in [int(r[0]) for r in out if r[1] == 1] for v in fixed), (chest, 'a fixed row is missing')
    return out, skipped


def comment(chest):
    """the comment lines before a chest's group: the source and the sheet's rows left out"""
    rows, skipped = table(chest)
    L = ['# MT2009_PLUS_CHEST_DROPS_V1: %d - %d rows from the owner\'s sheet of %s (tools/yohara_chestdrops),'
         % (chest, len(rows) - len(EXTRA.get(chest, [])), SOURCE[chest]),
         '# weights of %d (/ 1000 = %%), one row an opening.' % SCALE]
    if chest in FIXED:
        L.append('# The owner\'s own chance kept: ' + ', '.join('vnum %d weight %d' % kv for kv in sorted(FIXED[chest].items())) +
                 ' (the rest scaled to what is left).')
    if chest in EXTRA:
        marker, why = EXTRA_NOTE[chest]
        L.append('# Not in the sheet, added at a chance of their own (%s): %d rows, %.3f%% each'
                 % (marker, len(EXTRA[chest]), EXTRA[chest][0][2] * 100))
        L.append('#   (%s); the sheet\'s rows scaled to what is left.' % why)
    if skipped:
        s = '# Left out (renormalised): ' + '; '.join('%s%s %.3f%% - %s' % (n, ' x%d' % c if c > 1 else '', p * 100, w)
                                                     for n, c, p, w in skipped)
        while len(s) > 118:                     # wrapped like the files' other comments
            k = s.rfind('; ', 0, 118)
            k = k if k > 0 else s.rfind(' ', 0, 118)
            L.append(s[:k + 1].rstrip())
            s = '#   ' + s[k + 1:].lstrip()
        L.append(s)
    return L


def group_lines(chest):
    """the numbered rows of the group, tab-separated as the generators write them"""
    rows, _ = table(chest)
    return ['\t%d\t%s\t%d\t%d -- %s' % (k, v, c, w, nm) for k, (v, c, w, nm) in enumerate(rows, 1)]


def main():
    chests = [int(a) for a in sys.argv[1:]] or sorted(sheet())
    for c in chests:
        print('\n'.join(comment(c)))
        print('\n'.join(group_lines(c)))
        print()


if __name__ == '__main__':
    main()
