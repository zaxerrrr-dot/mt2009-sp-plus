#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_ymaps4.py [--attr FILE] [--ameria DIR]

MT2009_PLUS_YOHARA_MAPS4_V1: Rozpadlina Dusz (389, metin2_map_whitdragonvalley, 3x3 at 128000 1510400 - Owsap's
index; the owner, 14 October 2026, cache/yohara/decyzje.md "14.10 rano": "Rozpadlina Dusz: TAK, z danymi Amerii
(metin2_map_whitdragonvalley: boss/stone/npc), zastepuje tymczasowy portal Wawoz<->Schronienie"). The pl-wiki
"Rozpadlina Dusz" for everything: Wola SungMa 35/25/35/40 (sungma_table.txt has it), the monsters (Duch, Golem,
Opetany Mrozny Jelen, Opetany Snieżny Leopard, Yeti Pln. Wiatru - lod 6777-6781 / blyskawice 6889-6893), the bosses
(Wielka Stopa, Wodz Wojenny Pln. Wiatru - lod 6782/6783, blyskawice 6894/6895), Metin Shiho / Metin Gumar, the NPCs
(Lowca Glow (Roz.Pln.W.) 20846, General Kohan 20808, Straznik Rozpad. Dusz 20806) and the teleports - Wawoz and
Schronienie Polnocnego Wiatru: the official route Wawoz -> Rozpadlina -> Schronienie in place of the second batch's
stand-in portals 10145/10146 (gone).

  terrain       server_attr from the GF 26.1.11 client's attr.atr (tools/gf28 srvattr.py; --attr, made once in the
                m2pack-lzo image) - every spawn centre is checked on the same attr.atr (no lzo needed here);
  bosses        Ameria's 8 spots (its boss.txt; serverfiles/home.tar.gz, Ameria keeps its own "Wawoz" on this
                terrain), every hour, the wiki's four bosses over them;
  Metins        Ameria's 33 spots in three rings (10 s - a farm): two of each ring, every 30 min (as Przelecz Yilad,
                the owner 14 October); a ring's Metin by GF's nearest position (Shiho 8066 / Gumar 8077);
  NPCs          Ameria's npc.txt (= Owsap's = GF's metin2_map_whitdragonvalley_point.txt) - 20806, 20808, 20846 and
                the portal 10143 to Wawoz (Owsap's target 247 15392);
  monsters      ours as on Wawoz (tools/yohara_maps/gen_ymaps2.py): groups of four over all the reachable terrain,
                Seoganland's density of Owsap's groups, the element of a group by GF's nearest position of a lod /
                blyskawice monster (map_mob_list.txt 389);
  links         Wawoz (388): 10142 "Rozpadlina Dusz" at GF's point 235,267 -> here, by Straznik Rozpad. Dusz;
                10143 -> Wawoz 247,288 (Owsap's). Schronienie (393): 10201 "Wyjdz" at GF's point 19,640 -> here, by
                General Kohan; Kohan (quest yohara_mapy4) -> Schronienie's Town (80,640) - the wiki: "Umozliwia
                wejscie do Schronienia" (its pass and missions we do not have: none asked).

Writes (GENERATED - edit this file, run it again):
  linux-port/docker/game/yohara_maps4/map/metin2_map_whitdragonvalley/{Setting,Town,regen,boss,stone,npc}.txt
                                                                                    (+ server_attr from --attr)
  linux-port/docker/game/yohara_maps4/{group,group_group,mob_drop_item}.yohara_maps4.txt
  linux-port/docker/game/yohara_maps4/links.yohara_maps4.txt   the lines the Dockerfile step adds to 388 / 393
  linux-port/docker/game/yohara_maps4/spawned.txt, gen_report.txt
  linux-port/docker/mariadb/playerbot/yohara_maps4.sql, yohara_maps4_zywioly.sql
  tools/yohara_maps4/ymaps4_mobs.json                          the client's rows (client-2.0.30/tools/ymaps4)

  docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 tools/yohara_maps4/gen_ymaps4.py --attr-only OUT
  python3 tools/yohara_maps4/gen_ymaps4.py --attr OUT/metin2_map_whitdragonvalley.server_attr
"""
import argparse
import collections
import csv
import json
import os
import random
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, 'tools', 'yohara_maps'))
sys.path.insert(0, os.path.join(REPO, 'tools', 'yohara_items'))
import gen_ymaps2 as m2  # noqa: E402  (the second batch: terrain grid, spawn lines, Wawoz's spawn method)
import gen_ymaps_sql as m1  # noqa: E402  (row writers and columns)

GF = m2.GF
OWSAP = m2.OWSAP
OUT = os.path.join(REPO, 'linux-port', 'docker', 'game', 'yohara_maps4')
SQL_OUT = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot', 'yohara_maps4.sql')
ZYW_OUT = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot', 'yohara_maps4_zywioly.sql')
JSON_OUT = os.path.join(HERE, 'ymaps4_mobs.json')
DEF_AMERIA = '/tmp/claude-0/-root/9f475014-d1bc-4cf4-a3e1-da3c380fc52c/scratchpad/ymaps4/home/srv1/share/locale/germany/map'

M = dict(index=389, folder='metin2_map_whitdragonvalley', name='Rozpadlina Dusz', size=(3, 3), base=(128000, 1510400))
WAWOZ = dict(index=388, folder='metin2_map_icecrystalcave', size=(5, 4), base=(0, 1510400))
SHELTER = dict(index=393, folder='metin2_map_whitedragoncave_01', size=(6, 6), base=(998400, 1203200),
               town=(80, 640))

ELEC, ICE = 2048, 8192
ELEMENT_BITS = 2048 | 4096 | 8192 | 16384 | 32768 | 65536
# the monsters: the official Polish names (Owsap's Polish client; 6889 is in no Polish data - the wiki's name)
MOBS = collections.OrderedDict()
for _base, _el in ((6777, ICE), (6889, ELEC)):
    for _k, _n in enumerate(('Opętany Mroźny Jeleń', 'Opętany Śnieżny Leopard', 'Yeti Płn. Wiatru',
                             'Duch Płn. Wiatru', 'Golem Płn. Wiatru', 'Wielka Stopa', 'Wódz Wojenny Płn. Wiatru')):
        MOBS[_base + _k] = (_n, _el)
EL_NAME = {ICE: 'lod', ELEC: 'blyskawice'}
NPCS = collections.OrderedDict([(20806, 'Strażnik Rozpad. Dusz'), (20808, 'Generał Kohan'),
                                (20846, 'Łowca Głów (Roz.Płn.W.)')])
# portals: vnum -> (name, Polish name) - WARP (3), "<name> x y" (global / 100); the official Polish names
PORTALS = collections.OrderedDict([
    (10142, None),                                              # Wawoz 235,267 -> here (filled in main)
    (10143, ('Northwind_C 247 15392', 'WąwózPłnW. 247 15392')),  # here 575,705 -> Wawoz 247,288 (Owsap)
    (10201, None),                                              # Schronienie 19,640 -> here, by Kohan
])

# groups (ours - Owsap has none of these monsters): four a group as the second batch's Wawoz (9170-9175)
GROUPS = collections.OrderedDict([
    (9190, ('Rozpadlina_lod_01', [6777, 6777, 6778, 6778])),
    (9191, ('Rozpadlina_lod_02', [6779, 6779, 6780, 6778])),
    (9192, ('Rozpadlina_lod_03', [6781, 6780, 6779, 6777])),
    (9193, ('Rozpadlina_blysk_01', [6889, 6889, 6890, 6890])),
    (9194, ('Rozpadlina_blysk_02', [6891, 6891, 6892, 6890])),
    (9195, ('Rozpadlina_blysk_03', [6893, 6892, 6891, 6889])),
])
GGROUPS = collections.OrderedDict([
    (4042, ('rozpadlina_lod', [9190, 9191, 9192])),
    (4043, ('rozpadlina_blysk', [9193, 9194, 9195])),
])

# -- the drops (the pl-wiki pages of each monster; percents ours, the second batch's official-like scale - a monster:
#    a Talizman Woli 0.05 each, Topaz Woli 0.4, a plate / Rog Trolla 0.25, the herb 0.5, a material 0.15, a rare
#    thing 0.03-0.1; a boss (hourly): weapons +5 2 / +6 0.5, materials 3-10, Topaz Woli x2 25. Nothing compensates
#    the test server's drop event.) Left out as in the batches before: the Odlamki 39070-39077 (the Seon-Hae event
#    drops them by level), Kamien Demonow +4 (we have +0 only: +0 as the second batch), the Eliksiry W. SungMa
#    27213-27216 and Przeb. Ksiega Zwierza (not in our world).
WILL = [(81000, 1, 0.05), (81300, 1, 0.05), (81250, 1, 0.05), (81550, 1, 0.05)]
TOPAZ = (72353, 1, 0.4)
RANDOM_CHEST = [(83065, 1, 0.1), (83066, 1, 0.1)]
HERB = {ICE: (95734, 1, 0.5), ELEC: (95735, 1, 0.5)}         # Mrozny Korzonek / Piorunowe Ziolo
BOSS_RUNES = [(31247, 1, 4), (31248, 1, 4), (31249, 1, 4), (31250, 1, 4)]
WEAPONS = {'Miecz Zadlo': 170, 'Demoniczne Ostrze': 250, 'Noz Siamese': 1120}


def monster_drop(el):
    # Duch / Golem / Jelen / Leopard / Yeti Pln. Wiatru - one list on the wiki (the herb by the element)
    return [(39078, 1, 0.05)] + WILL + [(31233, 1, 0.25), (31234, 1, 0.08), (27987, 1, 0.4), (49991, 1, 0.15),
                                       (31216, 1, 0.25), (31217, 1, 0.25), TOPAZ, (31251, 1, 0.15),
                                       (31252, 1, 0.05), (31257, 1, 0.15), HERB[el], (50739, 1, 0.25),
                                       (50740, 1, 0.25), (50529, 1, 0.03), (39068, 1, 0.05)] + RANDOM_CHEST


def boss_drop(el, war):
    # Wielka Stopa / Wodz Wojenny Pln. Wiatru: Miecz Zadlo, Demoniczne Ostrze, Noz Siamese and the rest of the wiki's
    r = [(WEAPONS[n] + 5, 1, 2, '%s+5' % n) for n in ('Miecz Zadlo', 'Demoniczne Ostrze', 'Noz Siamese')] + \
        [(WEAPONS[n] + 6, 1, 0.5, '%s+6' % n) for n in ('Miecz Zadlo', 'Demoniczne Ostrze', 'Noz Siamese')] + \
        [(39081, 1, 3), (31258, 1, 5), (31257, 1, 8), (31238, 1, 8), (49991, 3, 10, 'Ognista Runa Aury (10) x3'),
         (31217, 2, 8, 'Rog Trolla x2'), (72353, 2, 25, 'Topaz Woli x2'), (31251, 1, 4), (31252, 1, 2),
         (31246, 1, 4)] + BOSS_RUNES + \
        [(31245, 1, 4), (72740, 1, 2), (50527, 1, 3), (25040, 1, 5), (72006, 1, 5), (39002, 1, 5),
         HERB[el][:2] + (10,), (50300, 1, 10), (50325, 1, 3), (95926, 50, 10, 'Kamyki x50'), (50528, 1, 8),
         (28046, 1, 2), (50338, 1, 3), (50339, 1, 1.5), (50340, 1, 0.75), (50663, 1, 3), (70014, 1, 10),
         (70048, 1, 8), (50529, 1, 3), (70038, 20, 10, 'Peleryna Mestwa x20'), (83065, 1, 5), (83066, 1, 5)]
    if war:
        # Zwoj Skarbu (A); Kowadlo Pln. Wiatru - both Wodze (lod: "Ulepszacze", blyskawice: "Inne")
        r += [(70434, 1, 2), (31259, 1, 3)]
    return r


def drops():
    d = []
    for v, (n, el) in MOBS.items():
        k = (v - 6777) if v < 6889 else (v - 6889)
        name = '%s (%s)' % (m2.ascii_pl(n), EL_NAME[el])
        if k < 5:
            d.append((v, name, monster_drop(el)))
        else:
            d.append((v, name, boss_drop(el, k == 6)))
    return d


def item_names():
    """vnum -> our name (the items the second batch's drops name; their files)."""
    sys.path.insert(0, os.path.join(REPO, 'tools', 'yohara_items'))
    import gen_yitems2 as y2  # noqa: E402
    names = dict(y2.EXISTING)
    for f in (os.path.join(REPO, 'tools', 'yohara_items', 'yohara_items2.json'),
              os.path.join(REPO, 'tools', 'yohara_items', 'yohara_items.json')):
        if os.path.exists(f):
            for i in json.load(open(f, encoding='utf-8'))['items']:
                names.setdefault(i['vnum'], i['name'])
    return names


def write_drops(rep):
    names = item_names()
    L = ['// MT2009_PLUS_YOHARA_MAPS4_V1: drops of Rozpadlina Dusz (389) - the pl-wiki lists of each monster and boss',
         '// with the items we have (the second batch\'s, tools/yohara_items). GENERATED by tools/yohara_maps4/gen_ymaps4.py',
         '// - do not edit. Owsap gives these monsters no drop. Official-like percents (the second batch\'s scale, the',
         '// owner 14 October: nothing raised for the test server\'s drop event). Left out: the Odlamki 39070-39077 (the',
         '// Seon-Hae event), Eliksir: W. SungMa x4 and Przeb. Ksiega Zwierza (not in our world), Kamien Demonow +4 (+0',
         '// here). The Metins (Shiho 8066, Gumar 8077) keep the second batch\'s groups.', '']
    for v, n, rows in drops():
        L += ['Group\tMT2009_ymaps4_%d' % v, '{', '\tMob\t%d\t-- %s' % (v, n), '\tType\tdrop']
        seen = set()
        k = 0
        for r in rows:
            iv, c, p = r[:3]
            assert iv not in seen, (v, iv)
            seen.add(iv)
            nm = r[3] if len(r) > 3 else names[iv] + (' x%d' % c if c > 1 else '')
            k += 1
            L.append('\t%d\t%d\t%d\t%g\t-- %s' % (k, iv, c, p, nm))
        L += ['}', '']
    open(os.path.join(OUT, 'mob_drop_item.yohara_maps4.txt'), 'w', encoding='utf-8', newline='\n').write('\n'.join(L))
    rep('drops: %d groups' % len(drops()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--attr', help='the server_attr made by --attr-only')
    ap.add_argument('--attr-only', help='write <dir>/metin2_map_whitdragonvalley.server_attr and stop (python-lzo)')
    ap.add_argument('--ameria', default=DEF_AMERIA, help="Ameria's share/locale/germany/map")
    a = ap.parse_args()
    if a.attr_only:
        sys.path.insert(0, os.path.join(REPO, 'client-patches', 'client-2.0.28', 'tools', 'gf28'))
        import srvattr  # noqa: E402
        W, H, g = srvattr.grid_from_client(os.path.join(GF, M['folder']), *M['size'])
        srvattr.write_server(os.path.join(a.attr_only, M['folder'] + '.server_attr'), W, H, g)
        return
    rep = m2.Report()
    rng = random.Random(14102026)
    g = m2.Grid(M['folder'], M['size'])
    h = m2.gf_hints()[M['index']]
    am = os.path.join(a.ameria, M['folder'])
    rep('389 Rozpadlina Dusz (%s)' % M['folder'])

    # NPCs and the portal back to Wawoz: Ameria's npc.txt (= Owsap's, GF's points)
    npc = []
    pts_npc = {}
    for t in m2.read_lines(os.path.join(am, 'npc.txt')):
        v = int(t[10])
        assert v in NPCS or v == 10143, t
        x, y = m2.check_free(g, int(t[1]), int(t[2]), 'NPC %d' % v, rep)
        pts_npc[v] = (x, y)
        npc.append(m2.spawn_line('m', x, y, 0, '10s' if v == 10143 else '1m', v, direction=int(t[6])))
    assert sorted(pts_npc) == [10143, 20806, 20808, 20846], pts_npc
    # where people come in: from Wawoz (10142) by Straznik Rozpad. Dusz - the map's Town (Owsap's 31,220 is blocked
    # on GF's terrain); from Schronienie (10201) by General Kohan
    town = m2.check_free(g, 550, 690, 'arrival from Wawoz (Town)', rep)
    by_kohan = m2.check_free(g, 150, 100, 'arrival from Schronienie', rep)
    reach = g.reach([town])
    for nm, p in [('town', town), ('by Kohan', by_kohan)] + [(str(v), p) for v, p in pts_npc.items()]:
        assert reach[p[1] * g.W + p[0]], nm
    for v, p in pts_npc.items():
        assert (p[0] - town[0]) ** 2 + (p[1] - town[1]) ** 2 >= 15 ** 2 or v != 10143, v
    avoid = [town, by_kohan] + list(pts_npc.values())

    # the regular monsters (Wawoz's method)
    seog = m2.Grid(m2.MAPS[376]['folder'], m2.MAPS[376]['size'])
    seog_lines = sum(1 for l in open(os.path.join(REPO, 'linux-port', 'docker', 'game', 'yohara_maps2', 'map',
                                                  m2.MAPS[376]['folder'], 'regen.txt')) if l.startswith('r'))
    seog_density = seog_lines / float(sum(seog.reach([(713, 565)])))
    target = int(round(seog_density * sum(reach)))
    pts, d = m2.poisson(g, reach, rng, target, avoid)
    ice_h = [p for v in range(6777, 6782) for p in h.get(v, [])]
    el_h = [p for v in range(6889, 6894) for p in h.get(v, [])]

    def nearest(p, hs):
        return min((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 for q in hs)
    regen = []
    n_ice = 0
    for x, y in sorted(pts, key=lambda p: (p[1], p[0])):
        ice = nearest((x, y), ice_h) <= nearest((x, y), el_h)
        n_ice += ice
        regen.append(m2.spawn_line('r', x, y, 10, '10s', 4042 if ice else 4043))
    rep('  regen: %d group lines (target %d = Seoganland\'s density %.6f x %d reachable m2; %.1f m apart), %d lod / %d '
        'blyskawice by the nearest GF position of each kind' % (len(regen), target, seog_density, sum(reach), d,
                                                               n_ice, len(regen) - n_ice))
    # bosses: Ameria's 8 spots, every hour - the wiki's four, two each
    order = [6782, 6895, 6894, 6783, 6782, 6895, 6894, 6783]
    boss = []
    for j, t in enumerate(m2.read_lines(os.path.join(am, 'boss.txt'))):
        x, y = m2.check_free(g, int(t[1]), int(t[2]), 'boss', rep)
        boss.append(m2.spawn_line('m', x, y, 10, '3600s', order[j], direction=1))
    assert len(boss) == 8, len(boss)
    rep('  bosses: %d on Ameria\'s spots (Wielka Stopa / Wodz Wojenny Pln. Wiatru, lod and blyskawice), 1 h' % len(boss))
    # Metins: Ameria's rings, two spots each, 30 min; the Metin by GF's nearest position of 8066 / 8077
    rings = collections.defaultdict(list)
    for t in m2.read_lines(os.path.join(am, 'stone.txt')):
        x, y = int(t[1]), int(t[2])
        rings['east' if x > 500 else 'north' if y < 250 else 'middle'].append((x, y))
    met_h = [(p, 8066) for p in h.get(8066, [])] + [(p, 8077) for p in h.get(8077, [])]
    stone = []
    for ring, rp in sorted(rings.items()):
        far = max(rp, key=lambda p: (p[0] - rp[0][0]) ** 2 + (p[1] - rp[0][1]) ** 2)
        for x, y in (rp[0], far):
            x, y = m2.check_free(g, x, y, 'Metin', rep)
            v = min(met_h, key=lambda q: (q[0][0] - x) ** 2 + (q[0][1] - y) ** 2)[1]
            stone.append(m2.spawn_line('m', x, y, 10, '1800s', v))
    rep('  Metins: %d (of Ameria\'s %d spots in %s rings: two a ring), 30 min: %s' % (
        len(stone), sum(len(p) for p in rings.values()), len(rings),
        ', '.join('%s %d' % (n, sum(1 for l in stone if l.endswith('\t%d' % v))) for n, v in (('Shiho', 8066),
                                                                                               ('Gumar', 8077)))))
    files = collections.OrderedDict([('regen.txt', regen), ('boss.txt', boss), ('stone.txt', stone), ('npc.txt', npc)])
    bad = sum(1 for ls in files.values() for l in ls if not g.free(int(l.split('\t')[1]), int(l.split('\t')[2])))
    rep('389 %s: %d spawn centre(s) on blocked ground' % (M['folder'], bad))
    assert bad == 0

    # the links: Wawoz's 10142 and Schronienie's 10201 at GF's points; the targets
    gw = m2.Grid(WAWOZ['folder'], WAWOZ['size'])
    gs = m2.Grid(SHELTER['folder'], SHELTER['size'])
    w142 = m2.check_free(gw, 235, 267, 'Wawoz portal 10142', rep)
    w_arr = m2.check_free(gw, 247, 288, 'Wawoz arrival from 10143', rep)
    assert gw.reach([(1106, 893)])[w_arr[1] * gw.W + w_arr[0]]
    s201 = m2.check_free(gs, 19, 640, 'Schronienie portal 10201', rep)
    assert gs.reach([SHELTER['town']])[s201[1] * gs.W + s201[0]]
    bx, by = M['base'][0] // 100, M['base'][1] // 100
    PORTALS[10142] = ('SoulGorge %d %d' % (bx + town[0], by + town[1]),
                      'RozpadlinaD. %d %d' % (bx + town[0], by + town[1]))
    PORTALS[10201] = ('Leave %d %d' % (bx + by_kohan[0], by + by_kohan[1]),
                      'Wyjdź %d %d' % (bx + by_kohan[0], by + by_kohan[1]))
    assert PORTALS[10143][0].split()[1:] == [str(WAWOZ['base'][0] // 100 + w_arr[0]),
                                             str(WAWOZ['base'][1] // 100 + w_arr[1])]
    links = ['388\t' + m2.spawn_line('m', w142[0], w142[1], 0, '10s', 10142),
             '393\t' + m2.spawn_line('m', s201[0], s201[1], 0, '10s', 10201)]
    rep('links: Wawoz 10142 at %d,%d -> %s; Schronienie 10201 at %d,%d -> %s; Kohan -> Schronienie %d,%d' % (
        w142[0], w142[1], PORTALS[10142][0], s201[0], s201[1], PORTALS[10201][0],
        SHELTER['base'][0] // 100 + SHELTER['town'][0], SHELTER['base'][1] // 100 + SHELTER['town'][1]))
    rep('quest yohara_mapy4: Kohan %s, by Kohan %d,%d, town %d,%d' % (pts_npc[20808], by_kohan[0], by_kohan[1],
                                                                      town[0], town[1]))

    # write
    d_ = os.path.join(OUT, 'map', M['folder'])
    if os.path.isdir(d_):
        shutil.rmtree(d_)
    os.makedirs(d_)
    st = open(os.path.join(GF, M['folder'], 'setting.txt'), encoding='latin-1').read().replace('\r\n', '\n')
    assert re.search(r'MapSize\s+%d\s+%d' % M['size'], st) and re.search(r'BasePosition\s+%d\s+%d' % M['base'], st)
    keep = [l.strip() for l in st.split('\n') if l.split() and l.split()[0] in (
        'ScriptType', 'CellScale', 'HeightScale', 'ViewRadius', 'MapSize', 'BasePosition', 'TextureSet', 'Environment')]
    setting = []
    for l in keep:
        setting.append(re.sub(r'^ViewRadius\s+\d+', 'ViewRadius\t128', l))
        if l.split()[0] in ('ScriptType', 'HeightScale', 'ViewRadius'):
            setting.append('')
    open(os.path.join(d_, 'Setting.txt'), 'w', newline='\n').write('\n'.join(setting) + '\n')
    open(os.path.join(d_, 'Town.txt'), 'w', newline='\n').write('%d %d\n' % town)
    for name, lines in files.items():
        open(os.path.join(d_, name), 'w', newline='\n').write('\n'.join(lines) + ('\n' if lines else ''))
    if a.attr:
        shutil.copyfile(a.attr, os.path.join(d_, 'server_attr'))
    open(os.path.join(OUT, 'links.yohara_maps4.txt'), 'w', newline='\n').write('\n'.join(links) + '\n')
    # groups
    L = ['// MT2009_PLUS_YOHARA_MAPS4_V1: Rozpadlina Dusz (389) - ours, four a group (Owsap has no group of these',
         '// monsters; tools/yohara_maps4/gen_ymaps4.py, GENERATED)']
    for v, (name, mobs) in GROUPS.items():
        L += ['Group\tMT2009_ymaps4_%s' % name, '{', '\tVnum\t%d' % v]
        for k, mob in enumerate(mobs):
            L.append('\t%s\t"%s"\t%d' % ('Leader' if k == 0 else str(k), m2.ascii_pl(MOBS[mob][0]), mob))
        L += ['}', '']
    open(os.path.join(OUT, 'group.yohara_maps4.txt'), 'w', newline='\n').write('\n'.join(L))
    L = ['// MT2009_PLUS_YOHARA_MAPS4_V1: Rozpadlina Dusz (389) - the "r" lines of its regen.txt: 4042 lod, 4043',
         '// blyskawice (tools/yohara_maps4/gen_ymaps4.py, GENERATED)']
    for v, (name, mem) in GGROUPS.items():
        L += ['Group\tMT2009_ymaps4_%s' % name, '{', '\tVnum\t%d' % v]
        for k, gv in enumerate(mem, 1):
            L.append('\t%d\t%d\t1' % (k, gv))
        L += ['}', '']
    open(os.path.join(OUT, 'group_group.yohara_maps4.txt'), 'w', newline='\n').write('\n'.join(L))
    write_drops(rep)
    # spawned (the client builder reads it)
    vs = set()
    for name, lines in files.items():
        for l in lines:
            t = l.split('\t')
            v = int(t[10])
            if t[0] == 'r':
                for gv in GGROUPS[v][1]:
                    vs.update(GROUPS[gv][1])
            else:
                vs.add(v)
    out = ['# MT2009_PLUS_YOHARA_MAPS4_V1: every vnum each map spawns (GENERATED by tools/yohara_maps4/gen_ymaps4.py;',
           '# the client builder client-patches/client-2.0.30/tools/ymaps4 reads it): <map index> <vnum>']
    out += ['389 %d' % v for v in sorted(vs)] + ['388 10142', '393 10201']
    open(os.path.join(OUT, 'spawned.txt'), 'w', newline='\n').write('\n'.join(out) + '\n')
    assert vs == set(MOBS) | set(NPCS) | {10143, 8066, 8077}, sorted(vs ^ (set(MOBS) | set(NPCS) | {10143, 8066, 8077}))
    write_sql(rep)
    open(os.path.join(OUT, 'gen_report.txt'), 'w', newline='\n').write('\n'.join(rep.lines) + '\n')


def write_sql(rep):
    en = {}
    for line in open(os.path.join(OWSAP, 'db/mob_names.txt'), encoding='latin-1'):
        p = line.rstrip('\r\n').split('\t')
        if len(p) >= 2 and p[0].isdigit():
            en[int(p[0])] = p[1]
    rows = {}
    for r in csv.DictReader(open(os.path.join(OWSAP, 'db/mob_proto.txt'), encoding='latin-1'), delimiter='\t'):
        if r['Vnum'].isdigit():
            rows[int(r['Vnum'])] = r
    lines = []
    for v, (n, el) in MOBS.items():
        assert len(n) <= 24, n
        r = rows[v]
        assert r['Type'] == 'MONSTER', v
        lines.append(m1.row_of(r, en.get(v) or m2.ascii_pl(n), n))
    for v, n in NPCS.items():
        assert len(n) <= 24, n
        lines.append(m1.npc_row(v, en.get(v) or m2.ascii_pl(n), n, rows[v]['Folder'] if v in rows else ''))
    for v, (name, pl) in PORTALS.items():
        assert len(name) <= 24 and len(pl) <= 24, (v, name, pl)
        t = list(m1.warp_row(v, name))
        t[2] = m1.q(pl)
        lines.append(tuple(t))
    for t in lines:
        assert len(t) == len(m1.COLS), t[0]
    with open(SQL_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write(SQL_HEADER % dict(n=len(lines), mobs=len(MOBS), npcs=len(NPCS), portals=len(PORTALS)))
        f.write('INSERT IGNORE INTO world.mob_proto (%s) VALUES\n' % ','.join('`%s`' % c for c in m1.COLS))
        f.write(',\n'.join('(%s)' % ','.join(str(x) for x in t) for t in lines) + ';\n')
        f.write(SQL_TAIL)
    L = [ZHEAD]
    for el in (ELEC, ICE):
        vs = [v for v, (n, e) in MOBS.items() if e == el]
        L.append('-- %s: %s' % (EL_NAME[el], ','.join(str(v) for v in vs)))
        L.append('UPDATE world.mob_proto SET setRaceFlag = ((setRaceFlag + 0) & ~%d) | %d WHERE vnum IN (%s);'
                 % (ELEMENT_BITS, el, ','.join(str(v) for v in vs)))
    with open(ZYW_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')
    with open(JSON_OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(dict(cols=list(m1.COLS), rows=[list(t) for t in lines],
                       elements=dict((str(v), e) for v, (n, e) in MOBS.items()),
                       remove=[10145, 10146]), f, ensure_ascii=False, indent=0)
        f.write('\n')
    rep('yohara_maps4.sql: %d rows (%d monsters/bosses, %d NPCs, %d portals)' % (len(lines), len(MOBS), len(NPCS),
                                                                              len(PORTALS)))


SQL_HEADER = """-- MT2009_PLUS_YOHARA_MAPS4_V1: Rozpadlina Dusz (389, metin2_map_whitdragonvalley) - its monsters, bosses, NPCs and
-- portals. GENERATED by tools/yohara_maps4/gen_ymaps4.py - do not edit, rerun it. Every start (apply.sh, after the
-- third batch), idempotent: INSERT IGNORE - a row the operator changed is kept. Every vnum was free in our world
-- (14 October 2026, the test server). %(n)d rows: %(mobs)d monsters and bosses, %(npcs)d NPCs, %(portals)d portals.
-- Monsters: Owsap v6.2.6 db/mob_proto.txt (the official vnums: lod 6777-6783, blyskawice 6889-6895) in our r40250
-- columns as tools/yohara_maps does it (levels 123-127, HP, damage, defence as they are; exp 0 - champion exp from
-- sungma_mob_exp.txt), the official Polish names (Owsap's Polish client; 6889 the wiki's), drop_item 0 (the drops:
-- game/yohara_maps4/mob_drop_item.yohara_maps4.txt); the elements: yohara_maps4_zywioly.sql. NPCs on our NPC
-- numbers (no quests but General Kohan's way into Schronienie: quest yohara_mapy4). Portals (WARP, "<name> x y",
-- global / 100): 10142 Wawoz -> here, 10143 here -> Wawoz (Owsap's), 10201 Schronienie -> here (official names).
-- At the end: the second batch's stand-in portals 10145/10146 (Wawoz <-> Schronienie, no map spawns them now) go.
SET NAMES utf8mb4;

"""
SQL_TAIL = """DELETE FROM world.mob_proto WHERE (vnum = 10145 AND name LIKE 'SchronPlnW %%') OR (vnum = 10146 AND name LIKE 'WawozPlnW %%');
""".replace('%%', '%')

ZHEAD = """-- MT2009_PLUS_YOHARA_MAPS4_V1: the elements of Rozpadlina Dusz's monsters (setRaceFlag bits 11-16: 2048 lightning,
-- 8192 ice) as on the pl-wiki ("Zywiol"; Owsap's AttElec / AttIce agree). GENERATED by tools/yohara_maps4/
-- gen_ymaps4.py. apply.sh runs it AFTER zywioly_moby.sql, which clears bits 11-16 of every mob it does not list:
-- idempotent, the end state is these bits on every start.
SET NAMES utf8mb4;"""

if __name__ == '__main__':
    main()
