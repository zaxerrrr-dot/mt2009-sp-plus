#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_ymaps3_maps.py [--owsap DIR] [--gf DIR]     (in the m2pack-lzo image: server_attr is LZO)

MT2009_PLUS_YOHARA_MAPS3_V1: the server's map folders of the third batch of Yohara places (ymaps3_data.MAPS) and
their spawn groups, under linux-port/docker/game/yohara_maps3/:

  map/<folder>/Setting.txt, Town.txt   Owsap v6.2.6's (= the GF 26.1.11 client's MapSize / BasePosition)
  map/<folder>/server_attr             made from the GF client's attr.atr (tools/gf28/srvattr.py; equal to Owsap's
                                       in every cell of all nine maps - checked 14 October 2026)
  map/<folder>/npc.txt                 every NPC and portal of GF's shared/common/map/<map>_point.txt (the official
                                       places), Owsap's where GF has none (the elemental realm: Owsap's npc.txt, our
                                       portal vnums)
  map/<folder>/regen/boss/stone.txt    Owsap's where it has them (Tajemnicza Instancja, Krolestwo Zywiolow); Zejscie
                                       and the 1st temple level have none in any source: our spawn points on the
                                       walkable cells, each a group of the monster GF's map_mob_list.txt shows
                                       nearest (the official "where it lives" points), the bosses / Metins as the
                                       TR wiki says (Wodz Wojenny on Ameria's two points, Kappa Zolnierz (124) every
                                       hour and Potezny Kappa every 2 hours anywhere, Metin Wezowy Przestrzeni)
  group.yohara_maps3.txt
                                       Owsap's groups of the instance and the realm (6829-6838, 6156-6161) and ours
                                       for Zejscie (9160-9164) and the 1st temple level (9180-9189)
Glebie (395) and Swiatynia Wezy (391) are dungeons: no spawn file, the quests spawn everything.

Example: docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \\
           /opt/metin2/git/<tree>/tools/yohara_maps3/gen_ymaps3_maps.py
"""
import argparse
import os
import random
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, 'client-patches', 'client-2.0.28', 'tools', 'gf28'))
import ymaps3_data as D  # noqa: E402
import srvattr as sa  # noqa: E402

OUT = os.path.join(REPO, 'linux-port', 'docker', 'game', 'yohara_maps3')

# -- our groups (Zejscie, the 1st temple level): vnum -> (name, [leader, members...]) -------------------------------
GROUPS = {
    9160: ('Zejscie_Zolnierz', [6792, 6792, 6792, 6793]),
    9161: ('Zejscie_Zadziora', [6793, 6793, 6792, 6792]),
    9162: ('Zejscie_Wojownik', [6794, 6794, 6792, 6792]),
    9163: ('Zejscie_Czarownik', [6795, 6795, 6793, 6792]),
    9164: ('Zejscie_General', [6796, 6794, 6795, 6792]),
    9180: ('Swiatynia1_Kappa_Robotnik', [6745, 6745, 6745, 6746]),
    9181: ('Swiatynia1_Kappa_Zolnierz', [6746, 6746, 6745, 6745]),
    9182: ('Swiatynia1_Kappa_Czarodziej', [6747, 6746, 6746]),
    9183: ('Swiatynia1_Kappa_Lowca', [6748, 6745, 6745]),
    9184: ('Swiatynia1_Skazony_mrok', [6758, 6758, 6758, 6759]),
    9185: ('Swiatynia1_Skazony_ziemia', [6875, 6875, 6875, 6876]),
    9186: ('Swiatynia1_Skazony_Wojownik_mrok', [6760, 6760, 6758]),
    9187: ('Swiatynia1_Skazony_Wojownik_ziemia', [6877, 6877, 6875]),
    9188: ('Swiatynia1_Skazony_Mnich_mrok', [6761, 6762, 6758]),
    9189: ('Swiatynia1_Skazony_Mnich_ziemia', [6878, 6879, 6875]),
}
# the group a hinted monster's spawn point takes (GF map_mob_list.txt: the mob -> its group)
HINT_GROUP = {6792: 9160, 6793: 9161, 6794: 9162, 6795: 9163, 6796: 9164,
              6745: 9180, 6746: 9181, 6747: 9182, 6748: 9183,
              6758: 9184, 6759: 9184, 6760: 9186, 6761: 9188, 6762: 9188}
# the wiki lists the (ziemia) Skazeni on the 1st level too (GF's list only the (mrok) ones): every second point of a
# (mrok) group takes its (ziemia) twin
EARTH_TWIN = {9184: 9185, 9186: 9187, 9188: 9189}
OWSAP_GROUPS = list(range(6829, 6839)) + list(range(6156, 6162))
OTHER_MAPS_MOBS = {6758, 6759, 6760, 6761, 6762, 6875, 6876, 6877, 6878, 6879}   # Przelecz Yilad's (maps2)

# spawn density: one group per this many walkable cells (1 cell = 1 m) - Owsap's Tajemnicza Instancja has one per
# ~300, Dongan one per ~600; the corridors of Zejscie are tight
DENSITY = {394: 450, 390: 650}
# Zejscie's "Tajna Komnata" (10222 leads there): Upiorny Straznik's room, no monsters
QUIET = {394: [(350, 600, 425, 675)]}
KEEP_CLEAR = 14      # metres from Town, an NPC or a portal
SPACING = 16         # metres between two spawn points


def read_tsv_points(path):
    out = []
    for l in open(path, encoding='latin-1'):
        t = l.replace('\r', '').split('\t')
        if len(t) >= 4 and t[0].strip().isdigit():
            out.append((int(t[1]) // 100, int(t[2]) // 100, int(t[3])))
    return out


def mob_hints(gf, index):
    h = []
    for l in open(os.path.join(gf, 'shared/common/map/map_mob_list.txt'), encoding='latin-1'):
        t = l.replace('\r', '').rstrip('\n').split('\t')
        if len(t) >= 2 and t[0].strip() == str(index):
            for p in t[2:]:
                p = p.strip().replace('.', ',')
                if ',' in p:
                    x, y = p.split(',')[:2]
                    h.append((int(x), int(y), int(t[1])))
    return h


def walk_grid(gf, m):
    W, H, g = sa.grid_from_client(os.path.join(gf, m['folder']), m['size'][0], m['size'][1])
    LW, LH = W // 2, H // 2
    walk = bytearray(LW * LH)
    for y in range(LH):
        row = 2 * y * W
        for x in range(LW):
            walk[y * LW + x] = 0 if g[row + 2 * x] & 1 else 1
    return W, H, g, LW, LH, walk


def open_area(walk, LW, LH, x, y, r=3):
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            xx, yy = x + dx, y + dy
            if not (0 <= xx < LW and 0 <= yy < LH) or not walk[yy * LW + xx]:
                return False
    return True


def spawn_points(walk, LW, LH, avoid, n, seed, quiet=()):
    rnd = random.Random(seed)
    cells = [(x, y) for y in range(0, LH, 2) for x in range(0, LW, 2) if open_area(walk, LW, LH, x, y)]
    rnd.shuffle(cells)
    pts = []
    for x, y in cells:
        if any((x - a) ** 2 + (y - b) ** 2 < KEEP_CLEAR ** 2 for a, b in avoid):
            continue
        if any(x0 <= x <= x1 and y0 <= y <= y1 for x0, y0, x1, y1 in quiet):
            continue
        if any((x - a) ** 2 + (y - b) ** 2 < SPACING ** 2 for a, b in pts):
            continue
        pts.append((x, y))
        if len(pts) >= n:
            break
    return sorted(pts, key=lambda p: (p[1], p[0]))


def line(t, x, y, sx, sy, time, pct, cnt, vnum, z=0, d=0):
    return '%s\t%d\t%d\t%d\t%d\t%d\t%d\t%s\t%d\t%d\t%d' % (t, x, y, sx, sy, z, d, time, pct, cnt, vnum)


def crlf_text(lines, head=None):
    out = ([head] if head else []) + lines
    return '\r\n'.join(out) + '\r\n'


def owsap_file(owsap, folder, name):
    p = os.path.join(owsap, 'map', folder, name)
    if not os.path.exists(p):
        return None
    return [l for l in open(p, encoding='latin-1').read().replace('\r', '').split('\n')
            if l.strip() and not l.startswith('//')]


def renumber(lines):
    out = []
    for l in lines:
        t = l.split('\t')
        v = int(t[-1])
        t[-1] = str(D.PORTAL_RENUMBER.get(v, v))
        out.append('\t'.join(t))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--owsap', default='/opt/metin2/cache/owsap/Server/Server/share/locale/uk')
    ap.add_argument('--gf', default='/opt/metin2/cache/gf/Gameforge_26.1.11/_client')
    a = ap.parse_args()
    report = []
    for m in D.MAPS:
        folder, idx = m['folder'], m['index']
        dst = os.path.join(OUT, 'map', folder)
        shutil.rmtree(dst, ignore_errors=True)
        os.makedirs(dst)
        st = open(os.path.join(a.owsap, 'map', folder, 'Setting.txt'), encoding='latin-1').read()
        assert re.search(r'MapSize\s+%d\s+%d' % m['size'], st) and re.search(r'BasePosition\s+%d\s+%d' % m['base'],
                                                                               st), folder
        open(os.path.join(dst, 'Setting.txt'), 'w', newline='').write(st.replace('\r\n', '\n').replace('\n', '\r\n'))
        town = open(os.path.join(a.owsap, 'map', folder, 'Town.txt'), encoding='latin-1').read().split()
        open(os.path.join(dst, 'Town.txt'), 'w', newline='').write('%s\t%s\r\n' % (town[0], town[1]))
        W, H, g, LW, LH, walk = walk_grid(a.gf, m)
        sa.write_server(os.path.join(dst, 'server_attr'), W, H, g)
        tx, ty = int(town[0]), int(town[1])
        # npc.txt: GF's points (official), else Owsap's npc.txt
        npc = []
        pf = os.path.join(a.gf, 'shared/common/map/%s_point.txt' % folder)
        if os.path.exists(pf) and not folder.startswith('metin2_map_elemental'):
            for x, y, v in read_tsv_points(pf):
                if v == 20491:      # the guild's Alastor statue (guild dungeon) - no guild Alastor here
                    continue
                if v == 3973:       # Glebie's hall portal: the quest spawns it in each instance
                    continue
                assert v in D.NPCS or v in D.PORTALS, (folder, v)
                npc.append(line('m', x, y, 0, 0, '1m', 100, 1, v, d=1))
        else:
            npc = renumber(owsap_file(a.owsap, folder, 'npc.txt') or [])
        for l in npc:
            v = int(l.split('\t')[-1])
            assert v in D.NPCS or v in D.PORTALS, (folder, v)
        avoid = [(tx, ty)] + [(int(l.split('\t')[1]), int(l.split('\t')[2])) for l in npc]
        files = {'npc.txt': npc}
        if idx in DENSITY:
            hints = mob_hints(a.gf, idx)
            n = sum(walk) // DENSITY[idx]
            pts = spawn_points(walk, LW, LH, avoid, n, seed=idx, quiet=QUIET.get(idx, ()))
            regen = []
            k = 0
            for x, y in pts:
                cand = [(hx, hy, hv) for hx, hy, hv in hints if hv in HINT_GROUP]
                hx, hy, hv = min(cand, key=lambda c: (c[0] - x) ** 2 + (c[1] - y) ** 2)
                grp = HINT_GROUP[hv]
                if grp in EARTH_TWIN:
                    k += 1
                    if k % 2 == 0:
                        grp = EARTH_TWIN[grp]
                regen.append(line('g', x, y, 6, 6, '60s', 100, 1, grp))
            files['regen.txt'] = regen
            if idx == 394:
                # Wodz Wojenny Schronienia (lod, blyskawice): Ameria's two points of the map, every hour
                files['boss.txt'] = [line('m', 354, 148, 10, 10, '3600s', 100, 1, 6797, d=1),
                                     line('m', 475, 58, 10, 10, '3600s', 100, 1, 6797, d=1)]
                files['stone.txt'] = []
            else:
                # TR wiki "Yilan Tapinagi (Giris Kat)": Kappa Zolnierz (124) every hour, Potezny Kappa every 2 hours,
                # anywhere on the map - over the map's walkable middle, wide ranges; Metin Wezowy Przestrzeni (GF's
                # point 400,600 and two in the upper part) every hour
                files['boss.txt'] = [line('m', 400, 400, 250, 250, '3600s', 100, 1, 6744, d=1),
                                     line('m', 400, 400, 250, 250, '7200s', 100, 1, 6749, d=1)]
                files['stone.txt'] = [line('m', 400, 600, 10, 10, '3600s', 100, 1, 8076),
                                      line('m', 420, 100, 10, 10, '3600s', 100, 1, 8076),
                                      line('m', 320, 190, 10, 10, '3600s', 100, 1, 8076)]
        elif m['kind'] == 'map':
            for f in ('regen.txt', 'boss.txt', 'stone.txt'):
                ls = owsap_file(a.owsap, folder, f)
                files[f] = renumber(ls) if ls else []
            if idx == 396:
                # Tajemniczy Mnich: TR wiki - every 6 hours somewhere on the map (Owsap: 3 points, 2 hours)
                files['boss.txt'] = [re.sub(r'\t7200s\t', '\t21600s\t', l) for l in files['boss.txt']]
        for f, ls in files.items():
            for l in ls:
                t = l.split('\t')
                x, y = int(t[1]), int(t[2])
                assert 0 <= x < LW and 0 <= y < LH, (folder, l)
            open(os.path.join(dst, f), 'w', newline='').write(crlf_text(ls))
        # a spawn point on a blocked cell (centre) is worth knowing
        blocked = []
        for f, ls in files.items():
            for l in ls:
                t = l.split('\t')
                x, y = int(t[1]), int(t[2])
                if not walk[y * LW + x]:
                    blocked.append('%s %s' % (f, l.replace('\t', ' ')))
        report.append('%d %s: %s; blocked centres %d %s' % (
            idx, folder, ', '.join('%s %d' % (f, len(ls)) for f, ls in sorted(files.items())), len(blocked),
            blocked[:3]))
    write_groups(a.owsap)
    print('\n'.join(report))


def blocks(path):
    text = open(path, encoding='latin-1').read().replace('\r', '')
    out = {}
    for name, body in re.findall(r'Group\s+(\S+)\s*\{(.*?)\n\}', text, re.S):
        v = re.search(r'Vnum\s+(\d+)', body)
        if v:
            out[int(v.group(1))] = (name, body)
    return out


def ascii_pl(s):
    return s.translate(str.maketrans('ąćęłńóśźżĄĆĘŁŃÓŚŹŻ', 'acelnoszzACELNOSZZ'))


def mob_name(v):
    if v in D.MOBS:
        return ascii_pl(D.MOBS[v][0])
    return {6758: 'Skazony Zolnierz', 6759: 'Skazony Zadziora', 6760: 'Skazony Wojownik', 6761: 'Skazony Mnich',
            6762: 'Skazony General', 6875: 'Skazony Zolnierz', 6876: 'Skazony Zadziora', 6877: 'Skazony Wojownik',
            6878: 'Skazony Mnich', 6879: 'Skazony General'}[v]


def write_groups(owsap):
    g = blocks(os.path.join(owsap, 'group.txt'))
    L = ['// MT2009_PLUS_YOHARA_MAPS3_V1: the spawn groups of the third batch of Yohara places (tools/yohara_maps3/',
         '// gen_ymaps3_maps.py; GENERATED). Owsap v6.2.6: Tajemnicza Instancja 6829-6838, Krolestwo Zywiolow',
         '// 6156-6161; ours: Zejscie Polnocnego Wiatru 9160-9164, 1. poziom Swiatyni Wezy 9180-9189 (6758-6762 /',
         '// 6875-6879 are Przelecz Yilad\'s monsters, rows of maps2).']
    for v in OWSAP_GROUPS:
        name, body = g[v]
        L += ['Group\tMT2009_ymaps3_%s' % name, '{', '\tVnum\t%d' % v]
        for l in body.split('\n'):
            t = l.split()
            if not t or t[0] == 'Vnum':
                continue
            mob = int(t[-1])
            assert mob in D.MOBS, (v, mob)
            L.append('\t%s\t"%s"\t%d' % (t[0], mob_name(mob), mob))
        L += ['}', '']
    for v, (name, mobs) in sorted(GROUPS.items()):
        L += ['Group\tMT2009_ymaps3_%s' % name, '{', '\tVnum\t%d' % v]
        for i, mob in enumerate(mobs):
            assert mob in D.MOBS or mob in OTHER_MAPS_MOBS, (v, mob)
            L.append('\t%s\t"%s"\t%d' % ('Leader' if i == 0 else str(i), mob_name(mob), mob))
        L += ['}', '']
    open(os.path.join(OUT, 'group.yohara_maps3.txt'), 'w', newline='\n').write('\n'.join(L))


if __name__ == '__main__':
    main()
