#!/usr/bin/env python3
"""gen_balathor_sql.py <mob_proto.txt> <out.sql> -- MT2009_PLUS_BALATHOR_V1: linux-port/docker/mariadb/playerbot/balathor.sql
from the package's mob_proto.txt rows (mods-incoming/balathor/server/mob_proto.txt, author dracaryS; 72 columns: the
r40250 order with ScalePct after Level) in our world.mob_proto columns (tools/yohara_maps/gen_ymaps_sql.py), the Polish
names of the pl-wiki ("Krypta Balathora"), the elements (setRaceFlag bits, as yohara_maps3_zywioly.sql) and the items
the lair needs: Ognista Strzala 30395 (the package's 30345 is our Ezoteryczne Drewno) and the two chests 83075/83076."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'yohara_maps'))
from gen_ymaps_sql import RANK, TYPE, BATTLE, AI, RACE, IMMUNE, COLS, q, flags, num  # noqa: E402

# 24 characters at most (the client's name field). 8635/8636 (Biale Jajo Smoka) and 20815 (Upiorny Straznik) are the
# Yohara line's already (yohara_maps3.sql, the same models) - not written here.
NAMES = {
    6896: ('Balathor', 'Balathor'),
    6897: ('Balathor (Hidden)', 'Balathor'),
    6898: ('Spectral Warrior', 'Upiorny Wojownik'),
    6899: ('Spectral Archer', 'Upiorny Łucznik'),
    6900: ('Spectral Echo', 'Upiorne Echo'),
    20491: ('Cursed Stone Tablet', 'Zakazana Tablica'),
    20492: ("Balathor's Treasure", 'Skarb Balathora'),
    20493: ('Hwacha', 'Hwacha'),
    20494: ('Solid Ice Wall', 'Masywna Lodowa Ściana'),
    20495: ('Frozen Dragon Egg', 'Zamrożone Jajo Smoka'),
    20496: ('Frozen Dragon Egg', 'Zamrożone Jajo Smoka'),
    20497: ('Flaming Dragon Egg', 'Ogniste Jajo Smoka'),
    20498: ('Ancient Ice Crystal', 'Pradawny Kryształ Lodu'),
    20499: ('Hwacha (Transformed)', 'Hwacha'),
    20507: ('Eternal Ice Crystal', 'Wieczny Kryształ Lodu'),
    20868: ('Dragonsoul Albira', 'Smocza Dusza Albira'),
    20869: ('Dragonsoul Albira', 'Smocza Dusza Albira'),
}
# pl-wiki: Balathor and his ghost warriors / archers ice, the Echo fire (setRaceFlag bit 13 = 8192 ice, 12 = 4096 fire)
ICE = (6896, 6897, 6898, 6899)
FIRE = (6900,)
# package column -> index (0-based) of its 72 columns
P = dict(vnum=0, rank=2, type=3, battle=4, level=5, ai=8, race=10, immune=11, folder=13, onclick=14, st=15, dx=16,
         ht=17, iq=18, dmin=19, dmax=20, hp=21, regen_cycle=22, regen_pct=23, gmin=24, gmax=25, exp=26, defe=27,
         aspd=28, mspd=29, aggr_hp=30, sight=31, arange=32, drop=33, resur=34)
ENCHANT0, RESIST0, DAM_MULT = 35, 41, 52


def row_of(r, en, pl):
    g = lambda k: r[P[k]]  # noqa: E731
    enchants = [num(r[ENCHANT0 + i]) for i in range(6)]
    resists = [num(r[RESIST0 + i]) for i in range(11)]
    rest = [num(x) for x in r[DAM_MULT + 1:DAM_MULT + 20]]   # summon, drain_sp, mob_color, polymorph, 5 skills x2, 5 sp
    t = (int(g('vnum')), q(en[:24]), q(pl), RANK[g('rank')], TYPE[g('type')], BATTLE[g('battle')], num(g('level')),
         "'NONE'", q(flags(g('ai'), AI)), 0, q(flags(g('race'), RACE)), q(flags(g('immune'), IMMUNE)), 0,
         q(g('folder')), num(g('onclick')), num(g('st')), num(g('dx')), num(g('ht')), num(g('iq')), num(g('dmin')),
         num(g('dmax')), num(g('hp')), num(g('regen_cycle')), num(g('regen_pct')), num(g('gmin')), num(g('gmax')),
         num(g('exp')), num(g('defe')), num(g('aspd')), num(g('mspd')), num(g('aggr_hp')), num(g('sight')),
         num(g('arange')), 0, num(g('resur'))) + tuple(enchants) + (0, 0) + tuple(resists) + \
        ('%.1f' % float(r[DAM_MULT] or 0),) + tuple(rest)
    assert len(t) == len(COLS), (t[0], len(t), len(COLS))
    return t


ITEM_COLS = ('vnum', 'name', 'locale_name', 'type', 'subtype', 'stack', 'weight', 'size', 'antiflag', 'flag',
             'wearflag', 'immuneflag', 'gold', 'shop_buy_price', 'refined_vnum', 'refine_set', 'magic_pct', 'specular',
             'socket_pct', 'addon_type', 'limittype0', 'limitvalue0', 'limittype1', 'limitvalue1', 'applytype0',
             'applyvalue0', 'applytype1', 'applyvalue1', 'applytype2', 'applyvalue2', 'value0', 'value1', 'value2',
             'value3', 'value4', 'value5', 'socket0', 'socket1', 'socket2', 'socket3', 'socket4', 'socket5')
# (vnum, name, Polish name, type, subtype, stack, antiflag, flag, value0) - the rest 0, sockets -1.
# 30395: ITEM_QUEST, stackable, ANTI_DROP|SELL|GIVE|PKDROP|MYSHOP (90496) as the package's 30345;
# 83075/83076: ITEM_GIFTBOX as our Yohara chests (70412: flag 8196, value0 2), opened by special_item_group.
ITEMS = (
    (30395, 'Fire Arrow', 'Ognista Strzała', 18, 0, 200, 90496, 4, 0),
    (83075, 'Frozen Chest Balathor', 'Mroźna Skrz. Balathora', 23, 0, 200, 0, 8196, 2),
    (83076, 'Frozen Chest Balathor+', 'Mroźna Skrz. Balathora+', 23, 0, 200, 0, 8196, 2),
)


def item_row(v, en, pl, typ, sub, stack, anti, flag, value0):
    hexname = pl.encode('cp1250').hex().upper()
    t = (v, q(en), "_cp1250 X'%s'" % hexname, typ, sub, stack, 0, 1, anti, flag, 0, "''") + (0,) * 18 + \
        (value0, 0, 0, 0, 0, 0) + (-1,) * 6
    assert len(t) == len(ITEM_COLS) and len(en) <= 24 and len(pl.encode('cp1250')) <= 24, v
    return t


HEADER = """-- MT2009_PLUS_BALATHOR_V1: Krypta Balathora (author of the module: dracaryS) - its monsters, NPCs and stones, the
-- Fire Arrow and the two chests. GENERATED by tools/balathor/gen_balathor_sql.py - do not edit, rerun it. Every start
-- (apply.sh, after the elements' files: zywioly_moby.sql clears bits 11-16 of every mob it does not list), idempotent:
-- INSERT IGNORE and guarded UPDATEs. Every vnum free in our world (the test world, 28 October 2026); 8635/8636 and
-- 20815 are yohara_maps3.sql's already. Monsters: the package's mob_proto.txt in our columns (its DRAGON race and
-- NORECOVERY flag are not ours and are dropped); names: the pl-wiki "Krypta Balathora".
SET NAMES utf8mb4;
"""


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    rows = {}
    for line in open(sys.argv[1], encoding='utf-8'):
        p = line.rstrip('\r\n').split('\t')
        if p and p[0].isdigit() and int(p[0]) in NAMES:
            assert len(p) == 72, (p[0], len(p))
            rows[int(p[0])] = p
    missing = sorted(set(NAMES) - set(rows))
    if missing:
        sys.exit('not in the package mob_proto: %s' % missing)
    mob_lines = ['(%s)' % ','.join(str(x) for x in row_of(rows[v], *NAMES[v])) for v in sorted(rows)]
    item_lines = ['(%s)' % ','.join(str(x) for x in item_row(*it)) for it in ITEMS]
    with open(sys.argv[2], 'w', encoding='utf-8', newline='\n') as f:
        f.write(HEADER)
        f.write('INSERT IGNORE INTO world.mob_proto (%s) VALUES\n' % ','.join('`%s`' % c for c in COLS))
        f.write(',\n'.join(mob_lines) + ';\n')
        f.write('-- lod: %s\n' % ','.join(map(str, ICE)))
        f.write('UPDATE world.mob_proto SET setRaceFlag = ((setRaceFlag + 0) & ~129024) | 8192 WHERE vnum IN (%s);\n'
                % ','.join(map(str, ICE)))
        f.write('-- ogien: %s\n' % ','.join(map(str, FIRE)))
        f.write('UPDATE world.mob_proto SET setRaceFlag = ((setRaceFlag + 0) & ~129024) | 4096 WHERE vnum IN (%s);\n'
                % ','.join(map(str, FIRE)))
        f.write('INSERT IGNORE INTO world.item_proto (%s) VALUES\n' % ','.join('`%s`' % c for c in ITEM_COLS))
        f.write(',\n'.join(item_lines) + ';\n')
    print('%s: %d monsters/NPCs, %d items' % (sys.argv[2], len(mob_lines), len(item_lines)))


if __name__ == '__main__':
    main()
