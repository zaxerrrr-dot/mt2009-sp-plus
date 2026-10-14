#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_ydung4_maps.py [--owsap DIR] [--gf DIR]     (in the m2pack-lzo image: server_attr is LZO)

MT2009_PLUS_YOHARA_DUNG4_V1: the server's map folders of Jaskinie Gnolli (382-384) and Wieza Sung Mahi (386 the hall,
387 the tower) - ydung4_data.MAPS - and their spawn groups, under linux-port/docker/game/yohara_dung4/:

  map/<folder>/Setting.txt, Town.txt   Owsap v6.2.6's (= the GF 26.1.11 client's MapSize / BasePosition); the tower's
                                       BasePosition is ours (998400 614400 - GF's is our Komnata Wiedzy's, ydung4_data)
  map/<folder>/server_attr             made from the GF client's attr.atr (tools/gf28/srvattr.py)
  map/<folder>/npc.txt                 every NPC and portal of GF's shared/common/map/<map>_point.txt (the official
                                       places: the caves' exits and stage portals, the maze's GOTO portals; the hall's
                                       portal, exit and merchant - its mailbox 30308 left out: no mail here)
  map/<folder>/regen.txt               the caves: Owsap's 245-255 spawn points of each level, each a group of ours of
                                       the monsters the pl-wiki lists for that level (Owsap's groups put the 2nd
                                       level's Ahtrins and the 3rd level's Szpieg / Wiedzmin / Komendant nowhere)
  map/<folder>/boss.txt                the caves' bosses on Owsap's two points - every hour (level 1), 2 hours
                                       (level 2), 3 hours (level 3): the TR wiki ("Gnoll Magarasi 1./2./3. Kat")
  group.yohara_dung4.txt               ours: the caves 9230-9244, the tower's waves 9250-9267
  spawned.txt                          every vnum each map spawns (+ the quests') - the client builder reads it
The tower (387) is a dungeon: no spawn file, the quest wieza_sung_mahi spawns everything.

Example: docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \\
           /opt/metin2/git/<tree>/tools/yohara_dung4/gen_ydung4_maps.py
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
import ydung4_data as D  # noqa: E402
import srvattr as sa  # noqa: E402

OUT = os.path.join(REPO, 'linux-port', 'docker', 'game', 'yohara_dung4')

# -- our groups: vnum -> (name, [leader, members...]) ---------------------------------------------------------------
GROUPS = {
    # Jaskinie Gnolli 1: Gnoll Wojownik / Zwiadowca / Czarodziej / Marszalek
    9230: ('Gnolle1_Wojownik', [6800, 6800, 6800]),
    9231: ('Gnolle1_Zwiadowca', [6801, 6800, 6800]),
    9232: ('Gnolle1_Czarodziej', [6802, 6802, 6800, 6800]),
    9233: ('Gnolle1_Marszalek', [6803, 6802, 6801, 6800]),
    # Jaskinie Gnolli 2: Gnoll Zolnierz / Szpieg / Mag / Komendant, Ahtrin Wojownik / Zwiadowca / Czarodziej /
    # Komendant (lvl-124)
    9234: ('Gnolle2_Zolnierz', [6806, 6806, 6806]),
    9235: ('Gnolle2_Szpieg', [6807, 6806, 6806]),
    9236: ('Gnolle2_Mag', [6808, 6807, 6806]),
    9237: ('Gnolle2_Komendant', [6809, 6808, 6806, 6806]),
    9238: ('Gnolle2_Ahtrin_Wojownik', [6810, 6810, 6811]),
    9239: ('Gnolle2_Ahtrin_Czarodziej', [6812, 6811, 6810]),
    9240: ('Gnolle2_Ahtrin_Komendant', [6813, 6812, 6811, 6810]),
    # Jaskinie Gnolli 3: Ahtrin Szpieg / Wojownik / Wiedzmin / Komendant (lvl-127)
    9241: ('Gnolle3_Ahtrin_Wojownik', [6810, 6810, 6816]),
    9242: ('Gnolle3_Ahtrin_Szpieg', [6816, 6816, 6810]),
    9243: ('Gnolle3_Ahtrin_Wiedzmin', [6817, 6817, 6816]),
    9244: ('Gnolle3_Ahtrin_Komendant', [6818, 6817, 6816, 6810]),
}
# Wieza Sung Mahi: a wave of an element (wolves, bruisers, a berserker, a warlock) and a heavy wave (the butcher with
# his escort) - three groups an element, 9250 + 3 * element (0 fire .. 5 dark) + 0/1/2
for _k, (_first, _el, _n) in enumerate(D.TOWER_ELEMENTS):
    GROUPS[9250 + 3 * _k] = ('Wieza_%s_Fala' % _n, [_first + 2, _first, _first, _first + 1, _first + 1])
    GROUPS[9251 + 3 * _k] = ('Wieza_%s_Magowie' % _n, [_first + 3, _first + 3, _first, _first + 1])
    GROUPS[9252 + 3 * _k] = ('Wieza_%s_Rzeznik' % _n, [_first + 4, _first + 2, _first + 1, _first])
# the Demon Stone's archers, woken (wieza_sung_mahi: the stone was hit - aggressive in their place)
GROUPS[9268] = ('Wieza_Lucznik', [7595])
# the level of each cave's groups (Owsap's points keep their level's groups); the share of each (weights)
LEVEL_GROUPS = {382: [(9230, 4), (9231, 3), (9232, 2), (9233, 1)],
                383: [(9234, 3), (9235, 2), (9236, 2), (9237, 1), (9238, 3), (9239, 2), (9240, 1)],
                384: [(9241, 3), (9242, 3), (9243, 2), (9244, 1)]}
# the bosses: TR wiki - level 1 every hour, level 2 every 2 hours, level 3 every 3 hours; Owsap's two points
BOSS_RESPAWN = {382: '3600s', 383: '7200s', 384: '10800s'}
# what the quests spawn - every vnum the client must draw, by map
QUEST_SPAWNED = {
    387: sorted(set(v for v, m in D.MOBS.items() if m[2] == 'wieza')) + [4020, 4021],
    376: [4019],          # Seoganland: the hall's entrance (the late step "Yohara dung4: links")
}


def read_tsv_points(path):
    out = []
    for l in open(path, encoding='latin-1'):
        t = l.replace('\r', '').split('\t')
        if len(t) >= 4 and t[0].strip().isdigit():
            out.append((int(t[1]) // 100, int(t[2]) // 100, int(t[3])))
    return out


def walk_grid(gf, m):
    W, H, g = sa.grid_from_client(os.path.join(gf, m['folder']), m['size'][0], m['size'][1])
    LW, LH = W // 2, H // 2
    walk = bytearray(LW * LH)
    for y in range(LH):
        row = 2 * y * W
        for x in range(LW):
            walk[y * LW + x] = 0 if g[row + 2 * x] & 1 else 1
    return W, H, g, LW, LH, walk


def line(t, x, y, sx, sy, time, pct, cnt, vnum, z=0, d=0):
    return '%s\t%d\t%d\t%d\t%d\t%d\t%d\t%s\t%d\t%d\t%d' % (t, x, y, sx, sy, z, d, time, pct, cnt, vnum)


def crlf_text(lines):
    return '\r\n'.join(lines) + '\r\n'


def owsap_lines(owsap, folder, name):
    p = os.path.join(owsap, 'map', folder, name)
    if not os.path.exists(p):
        return []
    return [l for l in open(p, encoding='latin-1').read().replace('\r', '').split('\n')
            if l.strip() and not l.startswith('//')]


def pick(rnd, weights):
    tot = sum(w for g, w in weights)
    r = rnd.randrange(tot)
    for g, w in weights:
        if r < w:
            return g
        r -= w
    raise AssertionError


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--owsap', default='/opt/metin2/cache/owsap/Server/Server/share/locale/uk')
    ap.add_argument('--gf', default='/opt/metin2/cache/gf/Gameforge_26.1.11/_client')
    a = ap.parse_args()
    report = []
    shutil.rmtree(os.path.join(OUT, 'map'), ignore_errors=True)
    for m in D.MAPS:
        folder, idx = m['folder'], m['index']
        dst = os.path.join(OUT, 'map', folder)
        os.makedirs(dst)
        st = open(os.path.join(a.owsap, 'map', folder, 'Setting.txt'), encoding='latin-1').read()
        gf_base = m.get('gf_base', m['base'])
        assert re.search(r'MapSize\s+%d\s+%d' % m['size'], st) and \
            re.search(r'BasePosition\s+%d\s+%d' % gf_base, st), folder
        if gf_base != m['base']:
            st, n = re.subn(r'BasePosition\s+%d\s+%d' % gf_base, 'BasePosition\t%d\t%d' % m['base'], st)
            assert n == 1, folder
        open(os.path.join(dst, 'Setting.txt'), 'w', newline='').write(st.replace('\r\n', '\n').replace('\n', '\r\n'))
        town = open(os.path.join(a.owsap, 'map', folder, 'Town.txt'), encoding='latin-1').read().split()
        open(os.path.join(dst, 'Town.txt'), 'w', newline='').write('%s\t%s\r\n' % (town[0], town[1]))
        W, H, g, LW, LH, walk = walk_grid(a.gf, m)
        sa.write_server(os.path.join(dst, 'server_attr'), W, H, g)
        files = {}
        pf = os.path.join(a.gf, 'shared/common/map/%s_point.txt' % folder)
        npc = []
        if os.path.exists(pf):
            for x, y, v in read_tsv_points(pf):
                if v == 30308:          # Skrzynka Pocztowa - no mail system here
                    continue
                assert v in D.NPCS or v in D.PORTALS or v in D.MAZE_PORTALS, (folder, v)
                npc.append(line('m', x, y, 0, 0, '1m', 100, 1, v, d=1))
        if npc:
            files['npc.txt'] = npc
        if idx in LEVEL_GROUPS:
            rnd = random.Random(idx)
            regen = []
            for l in owsap_lines(a.owsap, folder, 'regen.txt'):
                t = l.split('\t')
                assert t[0] == 'r' and t[7] == '120s', l
                x, y = int(t[1]), int(t[2])
                regen.append(line('g', x, y, int(t[3]), int(t[4]), '120s', 100, 1, pick(rnd, LEVEL_GROUPS[idx])))
            files['regen.txt'] = regen
            boss = []
            for l in owsap_lines(a.owsap, folder, 'boss.txt'):
                t = l.split('\t')
                v = int(t[-1])
                assert v in D.MOBS and t[0] == 'm', l
                boss.append(line('m', int(t[1]), int(t[2]), 5, 5, BOSS_RESPAWN[idx], 100, 1, v, d=1))
            assert len(boss) == 2, folder
            files['boss.txt'] = boss
            files['stone.txt'] = []
        for f, ls in files.items():
            for l in ls:
                t = l.split('\t')
                x, y = int(t[1]), int(t[2])
                assert 0 <= x < LW and 0 <= y < LH, (folder, l)
            open(os.path.join(dst, f), 'w', newline='').write(crlf_text(ls) if ls else '')
        blocked = []
        for f, ls in files.items():
            for l in ls:
                t = l.split('\t')
                if not walk[int(t[2]) * LW + int(t[1])]:
                    blocked.append('%s %s' % (f, l.replace('\t', ' ')))
        report.append('%d %s: %s; blocked centres %d %s' % (
            idx, folder, ', '.join('%s %d' % (f, len(ls)) for f, ls in sorted(files.items())), len(blocked),
            blocked[:3]))
    write_groups()
    write_spawned()
    print('\n'.join(report))


def ascii_pl(s):
    return s.translate(str.maketrans('ąćęłńóśźżĄĆĘŁŃÓŚŹŻ', 'acelnoszzACELNOSZZ'))


def write_groups():
    L = ['// MT2009_PLUS_YOHARA_DUNG4_V1: the spawn groups of Jaskinie Gnolli and Wieza Sung Mahi (tools/yohara_dung4/',
         '// gen_ydung4_maps.py; GENERATED). The caves 9230-9244 (each level\'s monsters as the pl-wiki lists them),',
         '// the tower\'s waves 9250-9267 (three an element: 0 ogien, 1 lod, 2 blyskawice, 3 wiatr, 4 ziemia, 5 mrok).']
    for v, (name, mobs) in sorted(GROUPS.items()):
        L += ['Group\tMT2009_ydung4_%s' % name, '{', '\tVnum\t%d' % v]
        for i, mob in enumerate(mobs):
            assert mob in D.MOBS, (v, mob)
            L.append('\t%s\t"%s"\t%d' % ('Leader' if i == 0 else str(i), ascii_pl(D.MOBS[mob][0]), mob))
        L += ['}', '']
    open(os.path.join(OUT, 'group.yohara_dung4.txt'), 'w', newline='\n').write('\n'.join(L))


def write_spawned():
    lines = ['# MT2009_PLUS_YOHARA_DUNG4_V1: every vnum each map of Jaskinie Gnolli / Wieza Sung Mahi spawns (npc/regen/',
             '# boss, groups unfolded, + the quests\' spawns) - client-patches/client-2.0.30/tools/ydung4 reads it.',
             '# GENERATED by tools/yohara_dung4/gen_ydung4_maps.py.']
    gm = dict((v, list(m)) for v, (n, m) in GROUPS.items())
    for m in D.MAPS:
        vs = set(QUEST_SPAWNED.get(m['index'], []))
        for f in ('npc.txt', 'regen.txt', 'boss.txt', 'stone.txt'):
            p = os.path.join(OUT, 'map', m['folder'], f)
            if not os.path.exists(p):
                continue
            for l in open(p, encoding='latin-1'):
                t = l.split()
                if len(t) >= 11:
                    v = int(t[-1])
                    vs |= set(gm[v]) if t[0] == 'g' else {v}
        lines += ['%d %d' % (m['index'], v) for v in sorted(vs)]
    lines += ['%d %d' % (i, v) for i in sorted(QUEST_SPAWNED) if i not in [m['index'] for m in D.MAPS]
              for v in QUEST_SPAWNED[i]]
    open(os.path.join(OUT, 'spawned.txt'), 'w', newline='\n').write('\n'.join(lines) + '\n')


if __name__ == '__main__':
    main()
