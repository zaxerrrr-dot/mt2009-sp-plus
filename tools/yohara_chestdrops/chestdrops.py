#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""chestdrops.py [CHEST ...]

MT2009_PLUS_CHEST_DROPS_V1: the contents and chances of the Yohara 3.0 chests (and of Skrzynia Razadora / Nemere)
from the owner's sheet of 15 October 2026 (chest_drops_2026-10-15_v2.tsv, a copy of cache/yohara/
metin2alerts_drop_2026-10-15_v2.csv: community data, estimated chances of ONE opening). The chest generators
(tools/yohara_items, yohara_maps3, yohara_maps4, yohara_dung4, yohara_pb, yohara_iluzja, yohara_zaklety) take their
groups from table(); the hand-made groups (game/shipdefense: 54705, 72058; game/special_item_group.dungeons.txt:
50270, 50271 - the sheet's 54702 / 54703) were written from it too, verify_chestdrops.py keeps them all equal.

Each sheet row: the official vnum -> ours. The same vnum when our world has it (world.item_proto, checked by
verify_chestdrops.py --db), else SUBST (our number of the same item) or SKIP (a system we lack - left out). The
chances of the rows left are scaled to weights summing to SCALE (one opening = one row by weight, a normal special
group: CSpecialItemGroup::GetOneIndex), so a weight / 1000 is the percent. Exact duplicates (the same item, the same
count) are one row with their chances summed; the same item with other counts stays separate rows. FIXED keeps a
row at the owner's own chance (Skrzynia Hydry: Magiczny Kamien 4%, 13 October), the rest scaled to what is left.

Example: python3 tools/yohara_chestdrops/chestdrops.py 54705     (prints the group's rows and what is left out)
"""
import os
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
SHEET = os.path.join(HERE, 'chest_drops_2026-10-15_v2.tsv')
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
    76044: (55009, 'our Skrzynia Ksiag Peta'),
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
    55412: 'no such pet',
    9999998: 'a group gives no champion EXP',
    27213: 'not in our world',
    27214: 'not in our world',
    27215: 'not in our world',
    27216: 'not in our world',
    31230: 'not in our world',
    31231: 'not in our world',
    31232: 'not in our world',
    39067: 'not in our world',
    72350: 'not in our world',
    50514: 'not in our world',
    50515: 'not in our world',
    30601: 'not in our world',
    30605: 'not in our world',
    30607: 'not in our world',
    30609: 'not in our world',
    30614: 'not in our world',
    30615: 'not in our world',
    30619: 'not in our world',
    30625: 'not in our world',
    30628: 'not in our world',
    55004: 'not in our world',
    55005: 'not in our world',
    28045: 'the engine draws no such stone',
    28145: 'the engine draws no such stone',
    28245: 'the engine draws no such stone',
    28345: 'the engine draws no such stone',
}
for _v in (6045, 6046, 6047, 6073, 6074, 6093, 6130, 6150, 21073, 21074, 21075, 21076, 21077, 21090, 21093, 21290,
           50524, 50568, 50576, 28012, 28112, 28212, 28312, 28412):     # 280x2: Kamien Duszy Likanow
    SKIP[_v] = _LYCAN

# our chest -> {our vnum: the owner's own weight of SCALE}
FIXED = {54705: {25042: 4000}}      # Skrzynia Hydry: Magiczny Kamien exactly 4% (the owner, 13 October 2026)


def ascii_pl(s):
    s = s.replace('ł', 'l').replace('Ł', 'L')
    s = unicodedata.normalize('NFKD', s)
    return ''.join(c for c in s if not unicodedata.combining(c))


def sheet():
    """our chest -> [(official chest, item name, count, chance, official vnum, time)] in the sheet's order"""
    out = {}
    for line in open(SHEET, encoding='utf-8'):
        t = line.rstrip('\n').split('\t')
        if len(t) != 7 or not t[0].isdigit():
            continue
        c = int(t[0])
        out.setdefault(OUR_CHEST.get(c, c), []).append((c, t[2], int(t[3]), float(t[4]), int(t[5]), t[6]))
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
        if key in at:                           # the same item and count twice: one row, the chances summed
            rows[at[key]][2] += chance
            continue
        at[key] = len(rows)
        rows.append([str(o), count, chance, nm])
    fixed = FIXED.get(chest, {})
    free = SCALE - sum(fixed.values())
    total = sum(r[2] for r in rows if not (r[1] == 1 and r[0] in map(str, fixed)))
    out = []
    for vn, count, chance, nm in rows:
        if count == 1 and vn in map(str, fixed):
            w = fixed[int(vn)]
        else:
            w = max(1, int(round(chance * free / total)))
        out.append((vn, count, w, nm))
    assert all(int(v) in [int(r[0]) for r in out if r[1] == 1] for v in fixed), (chest, 'a fixed row is missing')
    return out, skipped


def comment(chest):
    """the comment lines before a chest's group: the source and the sheet's rows left out"""
    rows, skipped = table(chest)
    L = ['# MT2009_PLUS_CHEST_DROPS_V1: %d - %d rows from the owner\'s sheet of 15 October 2026 (tools/yohara_chestdrops),'
         % (chest, len(rows)), '# weights of %d (/ 1000 = %%), one row an opening.' % SCALE]
    if chest in FIXED:
        L.append('# The owner\'s own chance kept: ' + ', '.join('vnum %d weight %d' % kv for kv in sorted(FIXED[chest].items())) +
                 ' (the rest scaled to what is left).')
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
