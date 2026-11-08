#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_ycrack2.py [--owsap DIR] [--gf DIR]          (host python3; no LZO needed)

MT2009_PLUS_YOHARA_CRACK2_V1: everything the server needs for the three remaining Time Rift dungeons - Grota Wygnańców
2 (SZC) (405), Twierdza Czerwonego Smoka (SZC) (406), Strażnica Nemere (SZC) (407) (ycrack2_data.py) - GENERATED
here, never edited by hand:

  linux-port/docker/game/yohara_crack2/
    map/<folder>/                        Setting.txt (Owsap's = GF's: MapSize, the official BasePosition), Town.txt
                                         (our entry cell), server_attr (= the PB twin's - the same terrain: GF's crack
                                         folders name the PB maps' parents, the grotto's own 000000/attr.atr is the
                                         PB grotto's, byte for byte)
    data/dungeon/<sub>/*.txt             Owsap's crack_*_dungeon spawns (the files the PB twin's quest reads; the
                                         temple's stones and Beran's group are the quest's, as in the PB grotto)
    group.yohara_crack2.txt              Owsap's "crack_*" groups the spawn files and the quests name (4201-4212,
                                         6021-6031, 6071-6082 - free in our group.txt)
    group_group.yohara_crack2.txt        Owsap's "crack_*" groups of groups (4201-4207, 6021-6023)
    spawned.txt                          every vnum each map shows (the client builder ycrack2 reads it)
  linux-port/docker/game/quest/beran_szc.quest, razador_szc.quest, nemere_szc.quest
                                         the PB twins' quests (beran_pb, razador_pb, nemere_pb) with the SZC vnums,
                                         map, base, ticket and the way back of Statua Szczeliny Czasu - as Owsap's
                                         crack quests are its awaken ones; Beran's keys as the wikis (see KEYS_*)
  linux-port/docker/mariadb/playerbot/
    yohara_crack2.sql                    world.mob_proto (INSERT IGNORE) - the SZC monsters, bosses, Metins, NPCs
    yohara_crack2_zywioly.sql            their elements (after zywioly_moby.sql)
    yohara_items_crack2.sql              world.item_proto (INSERT IGNORE) - Kręty Klucz (SZC) and the quests' items
  tools/yohara_crack2/ycrack2_client.json  the client's rows (client-2.0.30/tools/ycrack2)
  client-patches/client-2.0.30/root/icon/item/<icon>.tga   the GF icons our packs lack

No drop file, no chest: the pl-wiki - "W tej lokacji potwory nie dają dropu ... ale w zamian dają więcej
Doświadczenia" - the engine drops nothing on 405-407 (server-patches/szczelina, MT2009_PLUS_YOHARA_CRACK2_V1) but
the mob_proto's own yang (Beran-Setaou (SZC): 20 000 000, tr-wiki). Every position the quests and spawn files use is
checked against the walk grid of GF's terrain.
"""
import argparse
import csv
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
for _d in ('yohara_maps', 'yohara_items', 'yohara_iluzja', 'yohara_pb'):
    sys.path.insert(0, os.path.join(REPO, 'tools', _d))
import ycrack2_data as D  # noqa: E402
from gen_ymaps_sql import COLS, row_of, npc_row  # noqa: E402
import gen_yitems as Y  # noqa: E402
import gen_yiluzja as YI  # noqa: E402  (client_grid, the PB grotto's quest points)
import gen_ypb as YP  # noqa: E402  (the PB fortress' / watchtower's quest points)

M = 'MT2009_PLUS_YOHARA_CRACK2_V1'
GAME = os.path.join(REPO, 'linux-port', 'docker', 'game')
OUT = os.path.join(GAME, 'yohara_crack2')
QUESTS = os.path.join(GAME, 'quest')
PB = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot')
SQL_OUT = os.path.join(PB, 'yohara_crack2.sql')
ZYW_OUT = os.path.join(PB, 'yohara_crack2_zywioly.sql')
ITEMS_OUT = os.path.join(PB, 'yohara_items_crack2.sql')
JSON_OUT = os.path.join(HERE, 'ycrack2_client.json')
ICON_OUT = os.path.join(REPO, 'client-patches', 'client-2.0.30', 'root', 'icon', 'item')
PB_JSON = [os.path.join(REPO, 'tools', 'yohara_pb', 'ypb_client.json'),
           os.path.join(REPO, 'tools', 'yohara_iluzja', 'yiluzja_client.json')]
EARLIER_JSON = YI.EARLIER_JSON + [YI.JSON_OUT, os.path.join(REPO, 'tools', 'yohara_crack', 'ycrack_client.json')]

# -- the spawn files: Owsap's crack_*_dungeon file -> ours (the names the PB twin's quest reads) ------------------
REGEN = {
    405: ['npc.txt', 'regen.txt', 'boss.txt'],
    406: ['fd_a.txt', 'fd_b.txt', 'fd_c.txt', 'fd_d.txt', 'fd_e.txt', 'fd_f.txt', 'fd_fild_boss.txt'],
    407: ['sd_%d.txt' % i for i in range(1, 11)],
}
# what the quests spawn themselves (left out of the files): the temple's stones (Owsap's group of groups 8120) and
# Beran-Setaou (SZC) with his guard (group 4212 - the quest needs his VID), as beran_pb
SKIP = {('r', 8120), ('ga', 4212)}
QUEST_GROUPS = {405: [4212, 4208, 4209, 4210]}    # beran_szc: d.spawn_group (Beran; a troop where a Metin falls)
# every position the quests use: the PB twins' (the same local cells; = the PB quests' cfg())
QUEST_POINTS = {405: YI.QUEST_POINTS[398], 406: YP.QUEST_POINTS[369], 407: YP.QUEST_POINTS[370]}
QUEST_SPAWNED = {
    405: [20510, 8120, 8121, 8122, 8123, 4400, 4207, 4208, 4209, 4210],
    406: [20511, 20512, 20513, 20514, 20515, 4229, 4401, 8124],
    407: [20516, 20517, 4249, 8125, 20518, 4402],
}
SUMMONS = {405: [4200, 4206], 406: [4227], 407: [4247]}   # mob_proto "summon" of the bosses / captains / generals


def owsap_groups(a, fn):
    t = open(os.path.join(a.owsap, 'share/locale/uk', fn), encoding='latin-1').read().replace('\r', '')
    out = {}
    for m in re.finditer(r'Group\s+(\S+)\s*\{(.*?)\}', t, re.S):
        b = m.group(2)
        v = re.search(r'Vnum\s+(\d+)', b)
        if not v:
            continue
        v = int(v.group(1))
        if fn == 'group.txt':
            lead = re.search(r'Leader\s+"?[^"\n]*"?\s+(\d+)', b)
            mem = [int(x) for x in re.findall(r'\n\s*\d+\s+"?[^"\n]*?"?\s+(\d+)\s*(?=\n|$)', b)]
            out[v] = (m.group(1), [int(lead.group(1))] + mem)
        else:
            out[v] = (m.group(1), [int(x) for x in re.findall(r'\n\s*\d+\s+(\d+)\s+\d+\s*(?=\n|$)', b)])
    return out


def norm_setting(t):
    return re.sub(r'BasePosition[^\r\n]*', '', t.replace('\r\n', '\n')).strip()


# ------------------------------------------------------------------------------------------------ the maps
def gen_maps(a, report):
    shutil.rmtree(os.path.join(OUT, 'map'), ignore_errors=True)       # README.md (by hand) stays
    shutil.rmtree(os.path.join(OUT, 'data'), ignore_errors=True)
    groups = owsap_groups(a, 'group.txt')
    ggroups = owsap_groups(a, 'group_group.txt')
    used_g, used_gg = set(), set()
    spawned = {}
    for m in D.MAPS:
        idx = m['index']
        dst = os.path.join(OUT, 'map', m['folder'])
        os.makedirs(dst)
        st = open(os.path.join(a.owsap, 'share/locale/uk/map', m['folder'], 'Setting.txt'), encoding='latin-1').read()
        assert re.search(r'MapSize\s+%d\s+%d' % m['size'], st) and re.search(r'BasePosition\s+%d\s+%d' % m['base'], st)
        gfst = open(os.path.join(a.gf, m['folder'], 'setting.txt'), encoding='latin-1').read()
        assert re.search(r'MapSize\s+%d\s+%d' % m['size'], gfst) and \
            re.search(r'BasePosition\s+%d\s+%d' % m['base'], gfst), m['folder']
        prop = open(os.path.join(a.gf, m['folder'], 'mapproperty.txt'), encoding='latin-1').read()
        assert 'ParentMapName "%s"' % m['gf_parent'] in prop, (m['folder'], prop)
        # the PB twin: the same Setting.txt but the base, the same terrain (its server_attr)
        pbdir = os.path.join(GAME, m['pb_dir'], 'map', m['pb_folder'])
        pbst = open(os.path.join(pbdir, 'Setting.txt'), encoding='latin-1', newline='').read()
        assert norm_setting(pbst) == norm_setting(st), m['folder']
        assert open(os.path.join(a.gf, m['pb_folder'], 'mapproperty.txt'), encoding='latin-1').read() == prop
        if m['own_attr']:
            for sec in sorted(os.listdir(os.path.join(a.gf, m['own_attr']))):
                if re.match(r'^\d{6}$', sec):
                    assert open(os.path.join(a.gf, m['own_attr'], sec, 'attr.atr'), 'rb').read() == \
                        open(os.path.join(a.gf, m['pb_folder'], sec, 'attr.atr'), 'rb').read(), sec
        open(os.path.join(dst, 'Setting.txt'), 'w', newline='').write(st.replace('\r\n', '\n').replace('\n', '\r\n'))
        open(os.path.join(dst, 'Town.txt'), 'w', newline='').write('%d\t%d\r\n' % m['town'])
        shutil.copyfile(os.path.join(pbdir, 'server_attr'), os.path.join(dst, 'server_attr'))
        head = open(os.path.join(dst, 'server_attr'), 'rb').read(8).hex()
        assert head == m['attr_head'], (m['folder'], head)
        W, H, g, LW, LH, walk, own = YI.client_grid(a.gf, dict(src=m['gf_parent'], size=m['size'],
                                                                 own_attr=m['own_attr']))
        blocked = []
        for k, pts in QUEST_POINTS[idx].items():
            for x, y in pts:
                assert 0 <= x < LW and 0 <= y < LH, (idx, k, x, y)
                if not walk[y * LW + x]:
                    blocked.append('%s %d,%d' % (k, x, y))
        report.append('%d %s: server_attr = %s (%s), quest points %d, blocked: %s' % (
            idx, m['folder'], m['pb_folder'], m['gf_parent'] + (' + own ' + ','.join(own) if own else ''),
            sum(len(v) for v in QUEST_POINTS[idx].values()), blocked or 'none'))
        # the spawn files
        d2 = os.path.join(OUT, 'data', 'dungeon', m['sub'])
        os.makedirs(d2)
        n = b = 0
        vs = set(QUEST_SPAWNED[idx]) | set(SUMMONS[idx])
        for g_ in QUEST_GROUPS.get(idx, []):
            used_g.add(g_)
            vs |= set(groups[g_][1])
        for fn in REGEN[idx]:
            out = []
            for l in open(os.path.join(a.owsap, 'share/data/dungeon', m['owsap'], fn), encoding='latin-1') \
                    .read().replace('\r', '').split('\n'):
                t = l.split('\t')
                if len(t) < 11 or not t[1].strip().isdigit():
                    continue
                v = int(t[-1])
                if (t[0], v) in SKIP:
                    continue
                if t[0] == 'r':
                    assert v in ggroups, (fn, l)
                    used_gg.add(v)
                    for g_ in ggroups[v][1]:
                        used_g.add(g_)
                        vs |= set(groups[g_][1])
                elif t[0] in ('g', 'ga'):
                    assert v in groups, (fn, l)
                    used_g.add(v)
                    vs |= set(groups[v][1])
                elif t[0] == 'm':
                    assert v in D.MOBS or v in D.NPCS, (fn, l)
                    vs.add(v)
                else:
                    raise SystemExit('%s: %s' % (fn, l))
                t[7] = t[7].replace('ss', 's')          # Owsap's "3600ss"
                x, y = int(t[1]), int(t[2])
                assert 0 <= x < LW and 0 <= y < LH, (fn, l)
                n += 1
                b += 0 if walk[y * LW + x] else 1
                out.append('\t'.join(t))
            assert out, fn
            open(os.path.join(d2, fn), 'w', newline='').write(YI.crlf_text(out))
        report.append('data/dungeon/%s: %d files, %d spawn points, %d on a blocked centre (the engine finds a free '
                      'cell around)' % (m['sub'], len(REGEN[idx]), n, b))
        assert vs <= set(D.MOBS) | set(D.NPCS), sorted(vs - set(D.MOBS) - set(D.NPCS))
        spawned[idx] = vs
    # the groups: Owsap's crack ones, every member ours
    L = ['// %s: the spawn groups of the Time Rift dungeons Grota Wygnancow 2 (SZC), Twierdza Czerwonego' % M,
         '// Smoka (SZC), Straznica Nemere (SZC) - Owsap v6.2.6\'s "crack_*" (= the official ones).',
         '// GENERATED by tools/yohara_crack2/gen_ycrack2.py - do not edit.']
    for v in sorted(used_g):
        name, mobs = groups[v]
        for mob in mobs:
            assert mob in D.MOBS, (v, mob)
        L += ['Group\tMT2009_ycr2_%s' % name, '{', '\tLeader\t"%s"\t%d' % (YI.ascii_pl(D.MOBS[mobs[0]][0]), mobs[0]),
              '\tVnum\t%d' % v]
        L += ['\t%d\t"%s"\t%d' % (i, YI.ascii_pl(D.MOBS[mob][0]), mob) for i, mob in enumerate(mobs[1:], 1)]
        L += ['}', '']
    open(os.path.join(OUT, 'group.yohara_crack2.txt'), 'w', newline='\n').write('\n'.join(L))
    L = ['// %s: the groups of groups of the Time Rift dungeons - Owsap v6.2.6\'s "crack_*".' % M,
         '// GENERATED by tools/yohara_crack2/gen_ycrack2.py - do not edit.']
    for v in sorted(used_gg):
        name, gs = ggroups[v]
        L += ['Group\tMT2009_ycr2_%s' % name, '{', '\tVnum\t%d' % v]
        for i, gv in enumerate(gs, 1):
            assert gv in used_g, (v, gv)
            L.append('\t%d\t%d\t1' % (i, gv))
        L += ['}', '']
    open(os.path.join(OUT, 'group_group.yohara_crack2.txt'), 'w', newline='\n').write('\n'.join(L))
    report.append('groups %d (%s), groups of groups %d (%s)' % (len(used_g), ranges(used_g), len(used_gg),
                                                                ranges(used_gg)))
    lines = ['# %s: every vnum each map shows (the spawn files with their groups unfolded + the quests\' spawns +' % M,
             '# the summons) - the client builder (client-patches/client-2.0.30/tools/ycrack2) reads it.',
             '# GENERATED by tools/yohara_crack2/gen_ycrack2.py.']
    for idx in sorted(spawned):
        lines += ['%d %d' % (idx, v) for v in sorted(spawned[idx])]
    open(os.path.join(OUT, 'spawned.txt'), 'w', newline='\n').write('\n'.join(lines) + '\n')
    allv = set().union(*spawned.values())
    assert allv == set(D.MOBS) | set(D.NPCS), (sorted(set(D.MOBS) | set(D.NPCS) - allv), sorted(allv - set(D.MOBS)))
    return used_g, used_gg


def ranges(vs):
    vs = sorted(vs)
    out, s = [], vs[0]
    for p, c in zip(vs, vs[1:] + [None]):
        if c != p + 1:
            out.append('%d' % s if s == p else '%d-%d' % (s, p))
            s = c
    return ', '.join(out)


# ------------------------------------------------------------------------------------------------ mob_proto
SQL_HEAD = """-- %(m)s: the three remaining Time Rift dungeons (the owner, 21 October 2026) - Grota Wygnancow 2 (SZC) (405,
-- Beran-Setaou (SZC)), Twierdza Czerwonego Smoka (SZC) (406, Razador (SZC)), Straznica Nemere (SZC) (407, Nemere
-- (SZC)). GENERATED by tools/yohara_crack2/gen_ycrack2.py - do not edit, rerun it. Every start (apply.sh, after
-- yohara_crack.sql), idempotent: INSERT IGNORE - a row the operator changed is kept. Every vnum was free in our world
-- (21 October 2026). %(n)d rows: %(mobs)d monsters, bosses and stones, %(npcs)d NPCs. Monsters: Owsap v6.2.6
-- db/mob_proto.txt (the official "TR:" rows - more experience than the PB ones, the pl-wiki's "daja wiecej
-- Doswiadczenia"; level, HP, EXP, damage and defence = the owner's sheet of 20 October, checked) in our r40250 columns
-- (tools/yohara_maps/gen_ymaps_sql.row_of); the tr-wiki over Owsap: Beran-Setaou (SZC) drops 20 000 000 Yang - nothing
-- else drops on 405-407 (server-patches/szczelina). Names "SZC: ..." as the sheet (= the official ones). NPCs on our NPC
-- numbers (gen_ymaps_sql.npc_row; Smocza Brama, Owsap's DOOR, an NPC as the PB one). The elements:
-- yohara_crack2_zywioly.sql (after zywioly_moby.sql).
SET NAMES utf8mb4;

"""

ZHEAD = """-- %s: the elements of the three remaining Time Rift dungeons (setRaceFlag bits 11-16: 2048 lightning,
-- 4096 fire, 8192 ice) as the pl-wiki ("Zywiol": the grotto lightning, the fortress fire, the watchtower ice; Owsap's
-- AttElec / AttFire / AttIce 90 agree). GENERATED by tools/yohara_crack2/gen_ycrack2.py. apply.sh runs it AFTER
-- zywioly_moby.sql, which clears bits 11-16 of every mob it does not list: idempotent.
SET NAMES utf8mb4;""" % M


def gen_mobs(a, report):
    en = {}
    for line in open(os.path.join(a.owsap, 'db', 'mob_names.txt'), encoding='latin-1'):
        p = line.rstrip('\r\n').split('\t')
        if len(p) >= 2 and p[0].isdigit():
            en[int(p[0])] = p[1]
    rows = {}
    for r in csv.DictReader(open(os.path.join(a.owsap, 'db', 'mob_proto.txt'), encoding='latin-1'), delimiter='\t'):
        if r['Vnum'].isdigit():
            rows[int(r['Vnum'])] = r
    lines = []
    for v in sorted(D.MOBS):
        pl, elem, _p = D.MOBS[v]
        assert len(pl.encode('cp1250')) <= 24, pl
        r = dict(rows[v])
        assert r['Type'] in ('MONSTER', 'STONE'), (v, r['Type'])
        for e, col in D.OWSAP_ATT.items():
            assert (r[col] == '90') == (elem == e), (v, col, r[col])
        assert r['MinGold'] == '0' and r['MaxGold'] == '0', v
        r.update(D.OVERRIDE.get(v, {}))
        lines.append(row_of(r, en[v][:24], pl))
    for v in sorted(D.NPCS):
        en_n, pl = D.NPCS[v]
        assert len(pl.encode('cp1250')) <= 24, pl
        assert en[v] == en_n, (v, en[v])
        assert rows[v]['Type'] in ('NPC', 'DOOR'), (v, rows[v]['Type'])
        lines.append(npc_row(v, en_n[:24], pl, rows[v]['Folder']))
    assert len(set(t[0] for t in lines)) == len(lines)
    for t in lines:
        assert len(t) == len(COLS), (t[0], len(t))
    with open(SQL_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write(SQL_HEAD % dict(m=M, n=len(lines), mobs=len(D.MOBS), npcs=len(D.NPCS)))
        f.write('INSERT IGNORE INTO world.mob_proto (%s) VALUES\n' % ','.join('`%s`' % c for c in COLS))
        f.write(',\n'.join('(%s)' % ','.join(str(x) for x in t) for t in lines) + ';\n')
    by = {}
    for v, (pl, elem, _p) in D.MOBS.items():
        if elem:
            by.setdefault(elem, []).append(v)
    L = [ZHEAD]
    for elem in sorted(by):
        L.append('-- %s: %s' % (D.ELEMENT_NAME[elem], ','.join(str(v) for v in sorted(by[elem]))))
        L.append('UPDATE world.mob_proto SET setRaceFlag = ((setRaceFlag + 0) & ~%d) | %d WHERE vnum IN (%s);'
                 % (D.ELEMENT_BITS, elem, ','.join(str(v) for v in sorted(by[elem]))))
    none = sorted(v for v, (pl, elem, _p) in D.MOBS.items() if not elem)
    L.append('-- no element (the Metins and the pillar - the wiki gives a Metin none): %s' % ','.join(map(str, none)))
    L.append('UPDATE world.mob_proto SET setRaceFlag = (setRaceFlag + 0) & ~%d WHERE vnum IN (%s) AND '
             '(setRaceFlag + 0) & %d <> 0;' % (D.ELEMENT_BITS, ','.join(map(str, none)), D.ELEMENT_BITS))
    with open(ZYW_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')
    report.append('mob_proto rows: %d (monsters/Metins %d, NPCs %d); elements: %s' % (
        len(lines), len(D.MOBS), len(D.NPCS), ', '.join('%s %d' % (D.ELEMENT_NAME[e], len(v)) for e, v in
                                                       sorted(by.items()))))
    return lines


# ------------------------------------------------------------------------------------------------ the items
ITEM_KEYS = ('vnum', 'name', 'locale_name', 'type', 'subtype', 'stack', 'weight', 'size', 'antiflag', 'flag',
             'wearflag', 'gold', 'shop_buy_price', 'refined_vnum', 'refine_set', 'magic_pct', 'specular', 'socket_pct',
             'limittype0', 'limitvalue0', 'limittype1', 'limitvalue1', 'applytype0', 'applyvalue0', 'applytype1',
             'applyvalue1', 'applytype2', 'applyvalue2', 'value0', 'value1', 'value2', 'value3', 'value4', 'value5')


def gen_items(a, report):
    pb, pbdesc = {}, {}
    for p in PB_JSON:
        d = json.load(open(p, encoding='utf-8'))
        for i in d['items']:
            pb[i['vnum']] = i
            pbdesc[i['vnum']] = d['itemdesc'][str(i['vnum'])].split('\t', 2)[2]
    gf_list = {}
    for r in Y.read_tsv(os.path.join(a.gf, 'shared/common/item_list.txt')):
        if len(r) >= 3 and r[0].strip().isdigit():
            gf_list[int(r[0])] = r[2].strip()
    proto = {}
    rows = Y.read_tsv(os.path.join(a.owsap, 'db/item_proto.txt'))
    for r in rows[1:]:
        if r and r[0].isdigit():
            proto[int(r[0])] = dict(zip(rows[0], r))
    earlier = set()
    for p in EARLIER_JSON:
        earlier |= set(i['vnum'] for i in json.load(open(p, encoding='utf-8'))['items'])
    items = []
    for v, twin in sorted(D.ITEMS.items()):
        assert v not in earlier and v in proto, v
        assert proto[v]['Type'] == proto[twin]['Type'], (v, twin)      # Owsap: the TR item = its RX twin
        i = dict(pb[twin])
        assert i['locale_name'].endswith(' (PB)'), i['locale_name']
        i.update(vnum=v, src=v, status=Y.ST, addon_type=0, list_type='ETC', model='',
                 locale_name=i['locale_name'][:-5] + ' (SZC)', name=i['name'][:-5] + ' (SZC)')
        assert len(i['locale_name'].encode('cp1250')) <= 24, i['locale_name']
        desc = D.ITEM_TEXT.get(v) or pbdesc[twin].replace('(PB)', '(SZC)')
        assert 'PB' not in desc, (v, desc)
        i['desc'] = desc
        icon = gf_list.get(v)
        assert icon, v
        i['icon'] = 'icon/item/' + os.path.basename(icon)
        i['icon_src'] = icon
        items.append(i)
    L = ['-- %s: Kręty Klucz (SZC) and the quest items of Twierdza Czerwonego Smoka (SZC) / Straznica Nemere' % M,
         '-- (SZC). GENERATED by tools/yohara_crack2/gen_ycrack2.py - do not edit, rerun it. Every start (apply.sh, after',
         '-- yohara_items_crack.sql), idempotent: INSERT IGNORE. Source: Owsap v6.2.6 db/item_proto.txt (the official',
         '-- vnums 31160, 31167-31171 - the "TR:" twins of the PB items 31180, 31187-31191), each row as its PB twin\'s',
         '-- (yohara_items_pb.sql / yohara_items_iluzja.sql) with "(SZC)"; every vnum free in our world (21 October 2026).',
         'SET NAMES utf8mb4;',
         'INSERT IGNORE INTO world.item_proto (%s) VALUES' % ','.join('`%s`' % c for c in Y.COLS),
         ',\n'.join(Y.sqlrow(i) for i in items) + ';']
    with open(ITEMS_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L).replace('Kręty', 'Krety') + '\n')
    added = 0
    for i in items:
        dst = os.path.join(ICON_OUT, os.path.basename(i['icon']))
        src = os.path.join(a.gf, i['icon_src'].replace('\\', '/'))
        assert os.path.isfile(src), src
        if not os.path.exists(dst):
            shutil.copyfile(src, dst)
            added += 1
    report.append('items %d (%s), icons copied %d' % (len(items), ', '.join(i['locale_name'] for i in items), added))
    return items


def write_client(mob_lines, items):
    out = {'cols': list(COLS), 'rows': [list(t) for t in mob_lines],
           'elements': dict((str(v), e) for v, (pl, e, _p) in D.MOBS.items()),
           'atlas': ['%s\t%d\t%d\t%d\t%d' % (m['folder'], m['base'][0], m['base'][1], m['size'][0], m['size'][1])
                     for m in D.MAPS],
           'items': [dict((k, i[k]) for k in ITEM_KEYS) for i in items],
           'item_list': dict((str(i['vnum']), '%d\t%s\t%s' % (i['vnum'], i['list_type'], i['icon'])) for i in items),
           'itemdesc': dict((str(i['vnum']), '%d\t%s\t%s' % (i['vnum'], i['locale_name'], Y.client_desc(i)))
                            for i in items)}
    with open(JSON_OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=0)
        f.write('\n')


# ------------------------------------------------------------------------------------------------ the quests
QHEAD = {
    'beran_szc': """-- %(m)s: Grota Wygnańców 2 (SZC) i Świątynia Smoka (SZC) - loch Szczeliny Czasu z Beranem-Setaou (SZC)
-- (405, metin2_map_boss_crack_skipia - teren Groty Wygnańców 2 (PB) w miejscu z Owsapa; pl-wiki "Grota Wygnańców 2
-- (SZC)", "Świątynia Smoka (SZC)", "Beran-Setaou (SZC)", "Generał Yonghan (SZC)", "Kapitan Yonghan (SZC-110)",
-- "Kręty Klucz (SZC)", "Duch Sura (SZC)"; tr-wiki "ZC: General Yonghan (110)", "ZC: Beran-Setaou"). Wejście: Statua
-- Szczeliny Czasu na Płaskowyżu Iluzji (quest szczelina_czasu). Przebieg jak Grota Wygnańców 2 (PB) (quest beran_pb -
-- Owsap: crack_skipia_dungeon.quest = awaken_skipia_dungeon.quest z wierszami "TR:"):
--   * w grocie: gdzie padnie Kapitan Yonghan (SZC) (4207 / 4208), pojawia się Generał Yonghan (SZC) (4209 / 4210);
--     Kręty Klucz (SZC) (31160) zostawia tylko Generał po Kapitanie (SZC-110) - 4210 (wiki, tr-wiki, arkusz
--     właściciela; Owsap daje klucz z każdego);
--   * Duch Sura (SZC) (20510): gracz sam albo przywódca, cała grupa przy nim, każdy ma 3 Kręte Klucze (SZC) - Świątynia Smoka (SZC);
--   * Beran-Setaou (SZC) (4400, błyskawica, 122 poz.; przywołuje Wojowników Setaou (SZC)) i cztery Metiny (8120-8123) -
--     dopóki stoi którykolwiek, smoka nie da się zranić; po śmierci 20 000 000 Yang (tr-wiki).
-- Potwory nie dają dropu, ale dają więcej PD (wiki) - silnik nie upuszcza niczego na mapie 405 poza Yangami Berana
-- (server-patches/szczelina). 60 minut od wejścia; po zwycięstwie (minuta) lub po czasie wszyscy wracają na Płaskowyż
-- Iluzji (obok Statuy Szczeliny Czasu). Zegarek Kieszonkowy znika przy pierwszym wejściu do nowej wyprawy. Panel lochów:
-- beran_szc. Boty nie wchodzą same - wyprawy botów
-- (MT2009_PLUS_BOT_YDG_V1) przez beran_szc_dgrun / beran_szc_dgrun_next.
-- GENERATED by tools/yohara_crack2/gen_ycrack2.py from beran_pb.quest - do not edit, rerun it.
-- cp1250; żaden napis nie kończy się polską literą (qc).
""",
    'razador_szc': """-- %(m)s: Twierdza Czerwonego Smoka (SZC) - loch Szczeliny Czasu z Razadorem (SZC) (406,
-- metin2_map_boss_crack_flame - teren naszej 351 w miejscu z Owsapa; pl-wiki "Twierdza Czerwonego Smoka (SZC)",
-- "Razador (SZC)"; tr-wiki "Zaman Catlagi Kirmizi Ejderha Kalesi"). Wejście: Statua Szczeliny Czasu na Płaskowyżu
-- Iluzji (quest szczelina_czasu). Przebieg jak Twierdza Czerwonego Smoka (PB) (quest razador_pb - Owsap:
-- crack_flame_dungeon.quest = awaken_flame_dungeon.quest z wierszami "TR:"): Gardziel Am-heha (SZC) (20511) wyznacza
-- sześć zadań w losowej kolejności (2× wszystkie potwory; Złota Zębatka (SZC) (31167) na Stelę Isfet (SZC) (20513);
-- Ignator (SZC) (4229); siedem Stel Isfet Kamieniami Maat (SZC) (31168) w ukrytej kolejności; Metin Purgatorium (SZC)
-- (8124)), potem Razador (SZC) (4401, ogień, 130 poz.; przywołuje Ognistych Generałów Żaru (SZC), maks. 3).
-- Potwory nie dają dropu, ale dają więcej PD (wiki) - silnik nie upuszcza niczego na mapie 406 (server-patches/
-- szczelina). 60 minut od wejścia; po zwycięstwie (minuta) lub po czasie wszyscy wracają na Płaskowyż Iluzji (obok
-- Statuy Szczeliny Czasu). Zegarek Kieszonkowy znika przy pierwszym wejściu do nowej wyprawy. Panel lochów:
-- razador_szc. Boty nie wchodzą same - wyprawy botów
-- (MT2009_PLUS_BOT_YDG_V1) przez razador_szc_dgrun / razador_szc_dgrun_next.
-- GENERATED by tools/yohara_crack2/gen_ycrack2.py from razador_pb.quest - do not edit, rerun it.
-- cp1250; żaden napis nie kończy się polską literą (qc).
""",
    'nemere_szc': """-- %(m)s: Strażnica Nemere (SZC) - loch Szczeliny Czasu z Nemere (SZC) (407,
-- metin2_map_boss_crack_snow - teren naszej 352 w miejscu z Owsapa; pl-wiki "Strażnica Nemere (SZC)", "Nemere (SZC)";
-- tr-wiki "Zaman Catlagi Nemere Gozlemevi" - dziesięć pięter). Wejście: Statua Szczeliny Czasu na Płaskowyżu Iluzji
-- (quest szczelina_czasu) - w grupie Ninja i Szaman. Przebieg jak Strażnica Nemere (PB) (quest nemere_pb - Owsap:
-- crack_snow_dungeon.quest = awaken_snow_dungeon.quest z wierszami "TR:"): Lodowy Lew (SZC) (20516); 2: Mroźny Klucz
-- (SZC) (31169, tylko Szaman); 4: druga fala i Szel (SZC) (4249); 5: Arktyczne Kostki (SZC) (20517) Gwiazdami Północy
-- (SZC) (31170); 6: Metin Chłodu (SZC) (8125) - rani go tylko Szaman; 7: cztery Szele - trzy sobowtóry; 8: Klucz Lod.
-- Kwiatu (SZC) (31171, wypada, gdy zabija Ninja); 9: Kolumna Smoka Północy (SZC) (20518) - rani ją tylko Ninja albo
-- Szaman (server-patches/szczelina); 10: Nemere (SZC) (4402, lód, 130 poz.; przywołuje Mroźnych Generałów (SZC)).
-- Potwory nie dają dropu, ale dają więcej PD (wiki) - silnik nie upuszcza niczego na mapie 407. 60 minut od wejścia; po
-- zwycięstwie (minuta) lub po czasie wszyscy wracają na Płaskowyż Iluzji (obok Statuy Szczeliny Czasu). Zegarek
-- Kieszonkowy znika przy pierwszym wejściu do nowej wyprawy. Panel lochów: nemere_szc. Boty nie wchodzą same - wyprawy botów
-- (MT2009_PLUS_BOT_YDG_V1) przez nemere_szc_dgrun / nemere_szc_dgrun_next.
-- GENERATED by tools/yohara_crack2/gen_ycrack2.py from nemere_pb.quest - do not edit, rerun it.
-- cp1250; żaden napis nie kończy się polską literą (qc).
""",
}

# Beran's keys (beran_pb: every Captain / General Yonghan (PB) leaves one - Owsap). The wikis and the sheet for the SZC
# grotto: the General appears where a Captain fell, and only the one after Kapitan Yonghan (SZC-110) has the key
KEYS_PB = '''		-- the keys: every Captain / General Yonghan (SZC) leaves one (Owsap)
		when 4207.kill or 4208.kill or 4209.kill or 4210.kill with beran_szc.inside() and d.getf("level") == 0 begin
			game.drop_item(beran_szc.cfg().key, 1)
		end
'''
KEYS_SZC = '''		-- %s (the keys): the pl-wiki "Generał Yonghan (SZC)" / "Kapitan Yonghan (SZC-110)", the tr-wiki
		-- "ZC: General Yonghan (110)" and the owner's sheet - a General Yonghan (SZC) appears where a Captain fell
		-- (SZC-116 4207 -> 4209, SZC-110 4208 -> 4210); only 4210 leaves a Kręty Klucz (SZC) (Owsap: every Yonghan)
		when 4207.kill with beran_szc.inside() and d.getf("level") == 0 begin
			d.spawn_mob(4209, pc.get_local_x(), pc.get_local_y())
		end

		when 4208.kill with beran_szc.inside() and d.getf("level") == 0 begin
			d.spawn_mob(4210, pc.get_local_x(), pc.get_local_y())
		end

		when 4210.kill with beran_szc.inside() and d.getf("level") == 0 begin
			game.drop_item(beran_szc.cfg().key, 1)
		end
''' % M
# MT2009_PLUS_YOHARA_SZC_SOLO_V1 (the owner, 8 November 2026: players enter the Time Rift alone): beran_pb's
# "only in a party" gate at Duch Sura goes; a lone player opens the temple portal himself (the bots' runs keep their
# parties of 2+)
SOLO_PB = '''			if not pc.is_gm() and not party.is_party() then
				say("Do Świątyni Smoka wchodzi się tylko w grupie.")
				npc.unlock()
				return
			end
'''
NOTICE_NODROP = 'd.notice("Potwory Szczeliny Czasu nie dają dropu, ale dają więcej PD.")'


def gen_quests(report):
    for m in D.MAPS:
        src = open(os.path.join(QUESTS, m['pb_quest'] + '.quest'), 'rb').read().decode('cp1250')
        assert '\r' not in src
        body = src[src.index('quest %s begin' % m['pb_quest']):]
        t = body.replace(m['pb_quest'], m['quest'])
        # the map, its instances, the base and the purge area (the PB base y 1971200 -> 1817600)
        t, k = re.subn(r'map = %d, base_x = (\d+), base_y = 19712,' % m['pb_index'],
                       lambda x: 'map = %d, base_x = %s, base_y = 18176,' % (m['index'], x.group(1)), t)
        assert k == 1, m['quest']
        t, k = re.subn(r'idx >= %d \* 10000 and idx < %d \* 10000' % (m['pb_index'], m['pb_index'] + 1),
                       'idx >= %d * 10000 and idx < %d * 10000' % (m['index'], m['index'] + 1), t)
        assert k == 1, m['quest']

        def area(x):
            v = [int(s) for s in x.group(1).split(',')]
            return 'area = {%d, %d, %d, %d}' % (v[0], v[1] - D.BASE_SHIFT, v[2], v[3] - D.BASE_SHIFT)
        t, k = re.subn(r'area = \{([0-9, ]+)\}', area, t)
        assert k == (0 if m['index'] == 405 else 1), (m['quest'], k)
        # the vnums (monsters, bosses, Metins, NPCs, groups, items, the ticket)
        seen = set()

        def vnum(x):
            v = int(x.group(0))
            seen.add(v)
            return str(D.PB_TO_SZC[v])
        t = re.sub(r'(?<![0-9.])(%s)(?![0-9])' % '|'.join(str(v) for v in sorted(D.PB_TO_SZC, reverse=True)), vnum, t)
        assert D.PB_TO_SZC[31146] == D.TICKET and 31146 in seen
        # the names and the way back: Statua Szczeliny Czasu's quest flags
        t = t.replace('"przebudzeni_bossowie"', '"szczelina_czasu"')
        t = t.replace('(PB)', '(SZC)')
        t = t.replace('Książki Przebudzenia', 'Zegarka Kieszonkowego')
        assert 'przebudzeni' not in t.lower() and 'Książk' not in t, m['quest']
        # the init notice: no drop, more experience (as jotun_szc)
        t, k = re.subn(r'(\n(\t+)d\.notice\("[^"\n]*: masz 60 minut[^"\n]*"\)\n)',
                       lambda x: x.group(1) + x.group(2) + NOTICE_NODROP + '\n', t)
        assert k == 1, m['quest']
        if m['quest'] == 'beran_szc':
            assert t.count(KEYS_PB) == 1, 'beran_pb keys block changed - update KEYS_PB'
            t = t.replace(KEYS_PB, KEYS_SZC)
            assert t.count(SOLO_PB) == 1, 'beran_pb party gate changed - update SOLO_PB'
            t = t.replace(SOLO_PB, '')
        for bad in ('Metin2', 'Gameforge', 'oficjaln'):
            assert bad.lower() not in t.lower(), (m['quest'], bad)
        left = re.findall(r'\bPB\b', t)
        assert not left, (m['quest'], left)
        out = QHEAD[m['quest']] % dict(m=M) + t
        open(os.path.join(QUESTS, m['quest'] + '.quest'), 'wb').write(out.encode('cp1250'))
        report.append('quest %s from %s: %d vnums mapped (%s)' % (m['quest'], m['pb_quest'], len(seen),
                                                                 ranges(sorted(seen))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--owsap', default='/opt/metin2/cache/owsap/Server/Server')
    ap.add_argument('--gf', default='/opt/metin2/cache/gf/Gameforge_26.1.11/_client')
    a = ap.parse_args()
    report = []
    os.makedirs(OUT, exist_ok=True)
    gen_maps(a, report)
    mob_lines = gen_mobs(a, report)
    items = gen_items(a, report)
    write_client(mob_lines, items)
    gen_quests(report)
    print('\n'.join(report))


if __name__ == '__main__':
    main()
