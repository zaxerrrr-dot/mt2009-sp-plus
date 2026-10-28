#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_npcloc_data.py <DUMP dir>            (in the m2pack-lzo image: it decodes server_attr with python-lzo)
   gen_npcloc_data.py --ref <PACKAGE dir>   (once: the package's tables -> tools/npcloc/npcloc_ref.json)

MT2009_PLUS_NPC_LOCATION_HELPER_V1 - Lokalizator NPC (the improved map; Autor: Best Studio). The data of the system
made from OUR world, not shipped from the package: the package describes another server's maps.

    sh tools/npcloc/dump_npcloc_inputs.sh /tmp/npcloc-dump
    docker run --rm -v /opt/metin2:/opt/metin2 -v /tmp/npcloc-dump:/tmp/npcloc-dump m2pack-lzo \
        python3 <repo>/tools/npcloc/gen_npcloc_data.py /tmp/npcloc-dump

Reads the dump (dump_npcloc_inputs.sh: the test server's map/index, each map's npc/regen/boss/stone/Setting/
server_attr, group.txt, group_group.txt, mob_drop_item.txt, world.mob_proto, the item vnums, the shop NPCs, the
client's atlasinfo.txt) and npcloc_ref.json (from the package: the role icon of each NPC vnum it knows, the vnums it
hides, its map rows - category, levels, empire, tickets). Writes (GENERATED - rerun, do not edit):

  linux-port/docker/game/npc_location_helper/npc_location_helper.txt + <map_dir>_point.txt
        (the image puts them in /opt/metin2/share/locale/poland/npc_location_helper/; npc_location_helper.cpp checks
        a teleport against them)
  client-patches/client-2.0.30/npcloc/locale/common/map/npc_location_helper/{npc_location_helper.txt,
        map_mob_list.txt, mob_drop_item.txt, event_npc_list.txt} and .../locale/common/map/<map_dir>_point.txt
        (tools/npcloc/build_npcloc_packs.py puts them in the locale pack)

map_dir is the CLIENT's map name (atlasinfo.txt, matched by the map's BasePosition): the client loads the atlas and
the point file by it (e.g. our map_n_threeway is the client's map_a2). Maps: every indexed map players walk on with
spawns or NPCs; left out: event/war/GM maps, the instance-only dungeons (no own spawns or the package hides them),
maps the client has no atlas for (EXCLUDE below). Every map is open (show_atlas 1): the package's map fragments are the
owner's decision. No tickets and no yang (warp_need_* 0): our dungeons keep their own entry rules. Point files: the
'm' lines of npc.txt whose mob is an NPC (type 1) or a portal (type 3), x/y in local cm; an NPC point is checked on the
map's server_attr (an open cell within MAX_SNAP_M metres, else the point is left out).
"""
import collections
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..'))
REF = os.path.join(HERE, 'npcloc_ref.json')
SRV_OUT = os.path.join(REPO, 'linux-port', 'docker', 'game', 'npc_location_helper')
CLI_OUT = os.path.join(REPO, 'client-patches', 'client-2.0.30', 'npcloc', 'locale', 'common', 'map')
MAX_SNAP_M = 5          # an NPC point needs an open server_attr cell within 5 m
MAX_MOB_POS = 5
MAX_DROPS = 40
BLOCK = 0x01 | 0x80     # ATTR_BLOCK | ATTR_OBJECT (SECTREE_MANAGER::IsMovablePosition)
WATER = 0x02

# map index -> why it is left out (besides the rules in Map())
EXCLUDE = {
    81: 'wedding map', 103: 'guild war arena', 105: 'guild war arena', 110: 'guild war arena (owner\'s 20/side map)',
    111: 'guild war arena', 112: 'duel map', 113: 'OX event', 181: 'empire war', 182: 'empire war', 183: 'empire war',
    200: 'GM guild build map', 250: 'studio', 419: 'treasure hunt event (no Setting.txt)',
    114: 'Sungzi castle war', 118: 'Sungzi castle war', 119: 'Sungzi castle war', 120: 'Sungzi castle war',
    121: 'Sungzi castle war', 122: 'Sungzi castle war', 123: 'Sungzi castle war', 124: 'Sungzi castle war',
    125: 'Sungzi castle war', 126: 'Sungzi castle war', 127: 'Sungzi castle war', 128: 'Sungzi castle war',
    100: 'no client atlas, no spawns', 101: 'no client atlas, no spawns',
    358: 'Zodiac temple floors (instances of the Zodiac quests)',
}
# our maps the package does not know: category (1 kingdom, 2 neutral, 3 dragon land, 5 dungeon, 6 Yohara, 7 Yohara
# dungeon), min level (our quests' gates where there is one)
OWN = {
    70: (2, 1), 80: (2, 1), 360: (2, 1), 361: (2, 1), 209: (3, 90), 368: (3, 90), 397: (4, 110),
}
# min champion level: only the Tajemnicza Instancja asks for one (yohara_mapy3.quest)
MIN_C_LEVEL = {396: 1}
NAME_ROLE = (('teleport', 6), ('kowal', 7), ('rybak', 8), ('g\u00f3rnik', 9), ('alchemi', 10), ('stajen', 14),
             ('wej\u015bcie', 15), ('brama', 15))
# NPC vnums kept off the list: decoration / quest props
HIDE = {20375}


def rd_lines(path):
    if not os.path.exists(path):
        return []
    return open(path, 'rb').read().decode('cp1250', 'replace').replace('\r', '').split('\n')


def toks(line):
    line = line.split('//')[0].split('--')[0]
    return line.split()


def make_ref(pkg):
    cli = os.path.join(pkg, '02. Client', 'locale', 'common', 'map')
    roles = collections.defaultdict(collections.Counter)
    for f in sorted(os.listdir(cli)):
        if not f.endswith('_point.txt'):
            continue
        for l in rd_lines(os.path.join(cli, f)):
            t = l.split()
            if len(t) < 6 or l.startswith('#'):
                continue
            try:
                roles[int(t[3])][(int(t[4]), int(t[5]))] += 1
            except ValueError:
                pass
    role, hidden = {}, []
    for v, c in sorted(roles.items()):
        on = [(n, r) for (e, r), n in c.items() if e]
        if on:
            role[str(v)] = sorted(on, reverse=True)[0][1]
        else:
            hidden.append(v)
    rows = {}
    hf = os.path.join(pkg, '03. Server', 'share', 'locale', 'xx', 'common', 'map', 'npc_location_helper',
                      'npc_location_helper.txt')
    grp = False
    for l in rd_lines(hf):
        s = l.strip()
        if s.startswith('Group') and 'MapInfo' in s:
            grp = True
            continue
        if grp and s.startswith('}'):
            break
        p = [x.strip() for x in l.split('\t') if x.strip()]
        if not grp or len(p) < 13 or not p[0].isdigit():
            continue
        rows[p[0]] = dict(dir=p[2], category=int(p[3]), min_level=int(p[4]), min_c_level=int(p[5]),
                          rec_min=int(p[6]), rec_max=int(p[7]), empire=int(p[8]), show_atlas=int(p[9]),
                          show_npc_list=int(p[10]), warp_item=p[12])
    json.dump(dict(note='MT2009_PLUS_NPC_LOCATION_HELPER_V1: from the Best Studio package (gen_npcloc_data.py --ref)',
                   role=role, hidden=hidden, maps=rows), open(REF, 'w'), indent=1, sort_keys=True)
    print('ref: %d roles, %d hidden vnums, %d map rows -> %s' % (len(role), len(hidden), len(rows), REF))


class Attr(object):
    """server_attr: int32 width/height in sectors, then per sector an lzo1x block of 128x128 uint32 (50 cm cells)."""

    def __init__(self, path):
        import lzo
        self.lzo = lzo
        self.d = open(path, 'rb').read()
        self.w, self.h = struct.unpack_from('<ii', self.d, 0)
        self.off, o = [], 8
        for _ in range(self.w * self.h):
            (n,) = struct.unpack_from('<I', self.d, o)
            self.off.append((o + 4, n))
            o += 4 + n
        self.cache = {}

    def cell(self, cx, cy):
        sx, sy = cx // 128, cy // 128
        if cx < 0 or cy < 0 or sx >= self.w or sy >= self.h:
            return BLOCK
        k = sy * self.w + sx
        if k not in self.cache:
            o, n = self.off[k]
            self.cache[k] = struct.unpack('<16384I', self.lzo.decompress(self.d[o:o + n], False, 128 * 128 * 4))
        return self.cache[k][(cy % 128) * 128 + cx % 128] & 0xff

    def open_near(self, x_cm, y_cm, r_m):
        """the nearest open cell (non-block, preferably dry) within r_m metres; None when there is none"""
        cx, cy = x_cm // 50, y_cm // 50
        best = None
        r = r_m * 2
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                a = self.cell(cx + dx, cy + dy)
                if a & BLOCK:
                    continue
                d = dx * dx + dy * dy + (10000 if a & WATER else 0)
                if d <= r * r + (10000 if a & WATER else 0) and (best is None or d < best[0]):
                    best = (d, dx, dy)
        return best


def main(dump):
    ref = json.load(open(REF))
    mob = {}
    for l in open(os.path.join(dump, 'mob_proto.tsv'), encoding='latin-1'):
        p = l.rstrip('\n').split('\t')
        try:
            name = bytes.fromhex(p[5]).decode('cp1250', 'replace')
        except ValueError:
            name = ''
        mob[int(p[0])] = dict(rank=int(p[1]), type=int(p[2]), level=int(p[3]), name=name)
    items = set(int(x) for x in open(os.path.join(dump, 'item_vnums.txt')) if x.strip().isdigit())
    shops = {}
    for l in open(os.path.join(dump, 'shop_npcs.tsv'), encoding='latin-1'):
        p = l.rstrip('\n').split('\t')
        v = int(p[0])
        if v:
            n, eq = int(p[2]), int(p[3]) if p[3] not in ('NULL', '') else 0
            a = shops.setdefault(v, [0, 0])
            a[0] += n
            a[1] += eq
    atlas = {}
    for l in rd_lines(os.path.join(dump, 'atlasinfo.txt')):
        p = l.split()
        if len(p) >= 5:
            atlas.setdefault((int(p[1]), int(p[2])), p[0])

    # groups: group.txt Vnum -> members, group_group.txt Vnum -> groups
    def groups(path, member_last):
        out, cur, lead = {}, None, []
        for l in rd_lines(path):
            t = toks(l)
            if not t:
                continue
            if t[0] == 'Group':
                cur, lead = None, []
            elif t[0].lower() == 'vnum' and len(t) > 1:
                cur = out.setdefault(int(t[1]), [])
                cur.extend(lead)
            elif t[0].lower() == 'leader':
                try:
                    (cur if cur is not None else lead).append(int(t[-1]))
                except ValueError:
                    pass
            elif cur is not None and t[0].isdigit() and len(t) >= 2:
                try:
                    cur.append(int(t[-1] if member_last else t[1]))
                except ValueError:
                    pass
        return out
    grp = groups(os.path.join(dump, 'group.txt'), True)
    ggrp = groups(os.path.join(dump, 'group_group.txt'), False)

    drops = collections.defaultdict(list)
    cur = None
    for l in rd_lines(os.path.join(dump, 'mob_drop_item.txt')):
        t = toks(l)
        if not t:
            continue
        if t[0] == 'Group':
            cur = None
        elif t[0].lower() == 'mob' and len(t) > 1:
            cur = int(t[1])
        elif cur is not None and t[0].isdigit() and len(t) >= 2 and t[1].isdigit():
            v = int(t[1])
            if v in items and v not in drops[cur]:
                drops[cur].append(v)

    def role_of(v):
        if str(v) in ref['role']:
            return ref['role'][str(v)]
        m = mob.get(v, {})
        if m.get('type') == 3:
            return 1
        if v == 9005:
            return 4
        nm = m.get('name', '').lower()
        for k, r in NAME_ROLE:
            if k in nm:
                return r
        if v in shops:
            n, eq = shops[v]
            return 2 if n and eq * 2 >= n else 3
        return 19

    maps, points, mobs_by_map, report = [], {}, {}, collections.Counter()
    excluded = []
    for l in rd_lines(os.path.join(dump, 'map', 'index')):
        p = l.split()
        if len(p) < 2 or not p[0].isdigit():
            continue
        idx, sdir = int(p[0]), p[1]
        md = os.path.join(dump, 'map', sdir)
        if idx in EXCLUDE:
            excluded.append((idx, sdir, EXCLUDE[idx]))
            continue
        setting = [toks(x) for x in rd_lines(os.path.join(md, 'Setting.txt'))]
        base = [x for x in setting if x and x[0] == 'BasePosition']
        if not base:
            excluded.append((idx, sdir, 'no Setting.txt'))
            continue
        cdir = atlas.get((int(base[0][1]), int(base[0][2])))
        if not cdir:
            excluded.append((idx, sdir, 'the client has no atlas for it (not in atlasinfo.txt)'))
            continue
        pr = ref['maps'].get(str(idx))
        if pr and pr['dir'].lower() not in (sdir.lower(), cdir.lower()):
            pr = None
        if pr is None:
            same = [r for r in ref['maps'].values() if r['dir'].lower() in (sdir.lower(), cdir.lower())]
            pr = same[0] if same else None
        if pr and pr['show_atlas'] == 0:
            excluded.append((idx, sdir, 'instance / boss room the package hides (show_atlas 0)'))
            continue
        # spawns
        spawn = collections.OrderedDict()
        for f in ('regen.txt', 'boss.txt', 'stone.txt'):
            for l2 in rd_lines(os.path.join(md, f)):
                t = toks(l2)
                if len(t) < 11 or t[0] not in ('m', 'g', 'r'):
                    continue
                try:
                    x, y, v = int(t[1]), int(t[2]), int(t[10])
                except ValueError:
                    continue
                vs = [v] if t[0] == 'm' else grp.get(v, []) if t[0] == 'g' else \
                    [m for g in ggrp.get(v, []) for m in grp.get(g, [])]
                for mv in vs:
                    m = mob.get(mv)
                    if not m or m['type'] not in (0, 2):
                        continue
                    pos = spawn.setdefault(mv, [])
                    if len(pos) < MAX_MOB_POS and all(abs(a - x) + abs(b - y) > 40 for a, b in pos):
                        pos.append((x, y))
        npcs = []
        attr = None
        if os.path.exists(os.path.join(md, 'server_attr')):
            attr = Attr(os.path.join(md, 'server_attr'))
        for l2 in rd_lines(os.path.join(md, 'npc.txt')):
            t = toks(l2)
            if len(t) < 11 or t[0] != 'm':
                continue
            try:
                x, y, v = int(t[1]), int(t[2]), int(t[10])
            except ValueError:
                continue
            m = mob.get(v)
            if not m or m['type'] not in (1, 3):
                continue
            if any(n[2] == v and abs(n[0] - x * 100) <= 500 and abs(n[1] - y * 100) <= 500 for n in npcs):
                report['dup'] += 1
                continue
            hidden = v in ref['hidden'] or v in HIDE or not m['name'].strip() or m['name'].startswith('#')
            xc, yc = x * 100, y * 100
            if attr is not None:
                b = attr.open_near(xc, yc, MAX_SNAP_M)
                if b is None:
                    report['no_open_cell'] += 1
                    continue
                if b[1] or b[2]:
                    report['near_open_cell'] += 1
            npcs.append((xc, yc, v, 0 if hidden else 1, role_of(v)))
        if not spawn and len(npcs) <= 1:
            excluded.append((idx, sdir, 'no own spawns and at most one NPC (instance-only dungeon)'))
            continue
        lv = sorted(mob[v]['level'] for v in spawn if mob[v]['type'] == 0)
        if pr:
            cat, minl, rmin, rmax, emp = pr['category'], pr['min_level'], pr['rec_min'], pr['rec_max'], pr['empire']
            if pr['warp_item'] not in ('0', ''):
                report['ticket:%d %s %s' % (idx, cdir, pr['warp_item'])] += 1
            if pr['show_atlas'] == 2:
                report['fragment:%d %s' % (idx, cdir)] += 1
            if pr['min_c_level'] > 0 or rmax == 0:   # the package's band is champion levels / open; ours: plain
                rmin, rmax = (lv[len(lv) // 10], lv[(len(lv) * 9) // 10]) if lv else (0, 0)
        else:
            cat, minl = OWN.get(idx, (2, 1))
            rmin, rmax = (lv[len(lv) // 10], lv[(len(lv) * 9) // 10]) if lv else (0, 0)
            emp = 0
        show_npc = 1 if any(n[3] for n in npcs) else 0
        maps.append([idx, cdir, cdir, cat, minl, MIN_C_LEVEL.get(idx, 0), rmin, rmax, emp, 1, show_npc, 0, '0'])
        points[cdir] = npcs
        mobs_by_map[idx] = sorted(spawn.items(), key=lambda kv: (mob[kv[0]]['level'], kv[0]))
        report['npc_points'] += len(npcs)
        report['npc_enabled'] += sum(1 for n in npcs if n[3])

    def w(path, lines):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, 'wb').write(('\r\n'.join(lines) + '\r\n').encode('cp1250'))

    head = ['# MT2009_PLUS_NPC_LOCATION_HELPER_V1 - GENERATED by tools/npcloc/gen_npcloc_data.py from our world; do not edit',
            'Group\tMapInfo', '{',
            '\t#map_index\tmap_name\tmap_dir\tcategory\tmin_level\tmin_c_level\trecommended_level_min\t'
            'recommended_level_max\tempire\tshow_atlas\tshow_npc_list\twarp_need_yang\twarp_need_item']
    info = head + ['\t' + '\t'.join(str(c) for c in r) for r in maps] + ['}']
    pts = {}
    for cdir, npcs in points.items():
        pts[cdir] = ['#index\tx\ty\tnpc_vnum\tenable_helper\ticon'] + \
            ['%d\t%d\t%d\t%d\t%d\t%d' % ((i,) + n) for i, n in enumerate(npcs)]
    for out in (SRV_OUT, CLI_OUT):
        hdir = out if out == SRV_OUT else os.path.join(out, 'npc_location_helper')
        if os.path.isdir(hdir):
            for f in os.listdir(hdir):
                if f.endswith('.txt'):
                    os.remove(os.path.join(hdir, f))
        w(os.path.join(hdir, 'npc_location_helper.txt'), info)
    if os.path.isdir(CLI_OUT):
        for f in os.listdir(CLI_OUT):
            if f.endswith('_point.txt'):
                os.remove(os.path.join(CLI_OUT, f))
    for cdir, lines in pts.items():
        w(os.path.join(SRV_OUT, cdir + '_point.txt'), lines)
        w(os.path.join(CLI_OUT, cdir + '_point.txt'), lines)
    mm = ['## MT2009_PLUS_NPC_LOCATION_HELPER_V1 - GENERATED: the monsters of each map (regen/boss/stone), sorted by level',
          '#map_index\tmob_vnum\tspawn_pos']
    shown = set()
    for idx in sorted(mobs_by_map):
        for v, pos in mobs_by_map[idx]:
            mm.append('%d\t%d\t%s' % (idx, v, '\t'.join('%d,%d' % p for p in pos)))
            shown.add(v)
    w(os.path.join(CLI_OUT, 'npc_location_helper', 'map_mob_list.txt'), mm)
    dl = ['## MT2009_PLUS_NPC_LOCATION_HELPER_V1 - GENERATED: what each listed monster can drop (mob_drop_item.txt)']
    for v in sorted(shown):
        if not drops.get(v):
            continue
        dl += ['Group\tmob_%d' % v, '{', '\tMob\t%d' % v]
        dl += ['\t%d\t%d' % (i + 1, it) for i, it in enumerate(drops[v][:MAX_DROPS])]
        dl.append('}')
        report['mobs_with_drops'] += 1
        report['drop_lines'] += min(len(drops[v]), MAX_DROPS)
    w(os.path.join(CLI_OUT, 'npc_location_helper', 'mob_drop_item.txt'), dl)
    w(os.path.join(CLI_OUT, 'npc_location_helper', 'event_npc_list.txt'),
      ['## MT2009_PLUS_NPC_LOCATION_HELPER_V1 - the NPCs an event spawns (none listed)',
       '#map_index\tx\ty\tvnum\tevent_flag'])
    report['maps'] = len(maps)
    report['mobs_listed'] = len(shown)
    print(json.dumps(dict(report=dict(sorted(report.items())), excluded=excluded,
                          maps=[(r[0], r[1], 'cat%d' % r[3], 'lv%d' % r[4], '%d-%d' % (r[6], r[7]), 'emp%d' % r[8],
                                 len(points[r[1]])) for r in maps]), indent=1, ensure_ascii=True))


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--ref':
        make_ref(sys.argv[2])
    elif len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        sys.exit(__doc__)
