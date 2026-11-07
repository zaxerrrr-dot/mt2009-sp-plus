#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_yzaklety.py [--owsap DIR] [--gf DIR]          (host python3; no LZO needed)

MT2009_PLUS_YOHARA_ZAKLETY_V1: everything the server needs for Zaklęty Las (353) and Erebu (yzaklety_data.py) -
GENERATED here, never edited by hand:

  linux-port/docker/game/yohara_zaklety/
    map/metin2_map_dawnmist_dungeon_01/  Setting.txt (Owsap's = GF's: MapSize 3 4, BasePosition 768000 1408000),
                                         Town.txt (Owsap's entry cell), server_attr (= Zaklęty Las (PB)'s, the same
                                         terrain - GF's attr.atr cell for cell, checked by verify_attr in the m2pack-lzo
                                         image), regen.txt / boss.txt / stone.txt (Owsap's points and groups), npc.txt
                                         (the forest's guards and the Teleporter at the wiki's cells)
    data/monster/<folder>/               Owsap's motions of the forest's races (trent_soldier, trent_magic,
                                         trent_general, trent_boss, trent_boss2, thunder_boss): the server times moves
                                         and attacks by them; every run.msa carries its Accumulation
    group.yohara_zaklety.txt             Owsap's groups 6311-6318 (the En-Tai, Władca En-Tai's guard) and 6330-6333
                                         (Metin Lasu's: the wiki's "Silny" En-Tai)
    mob_drop_item.yohara_zaklety.txt     the pl-wiki's drop lists, our odds (official-like; the test server's drop
                                         event is not compensated for)
    special_item_group.yohara_zaklety.txt  Skrzynia Jotuna Thryma (50266), Skrzynia Bagjanamu (54701) - the owner's
                                         sheet (tools/yohara_chestdrops), one thing an opening by weight
    spawned.txt                          every vnum the map shows (the client builder yzaklety reads it)
  linux-port/docker/mariadb/playerbot/
    yohara_zaklety.sql                   world.mob_proto (INSERT IGNORE) - the forest's monsters, bosses, Metins, NPCs
    yohara_zaklety_zywioly.sql           their elements (after zywioly_moby.sql)
    yohara_items_zaklety.sql             world.item_proto (INSERT IGNORE) - Kamień Driad, the missions' items, the chests
  tools/yohara_zaklety/yzaklety_client.json  the client's rows (client-2.0.30/tools/yzaklety)
  client-patches/client-2.0.30/root/icon/item/<icon>.tga   the GF icons our packs lack

Every position the quests and the spawn files use is checked against the terrain (GF's attr.atr).
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
sys.path.insert(0, os.path.join(REPO, 'tools', 'yohara_chestdrops'))
import chestdrops as CD  # noqa: E402  (MT2009_PLUS_CHEST_DROPS_V1: the chests' rows)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, 'tools', 'yohara_maps'))
sys.path.insert(0, os.path.join(REPO, 'tools', 'yohara_items'))
sys.path.insert(0, os.path.join(REPO, 'tools', 'yohara_iluzja'))
sys.path.insert(0, os.path.join(REPO, 'tools', 'yohara_crack'))
import yzaklety_data as D  # noqa: E402
from gen_ymaps_sql import COLS, row_of, npc_row  # noqa: E402
import gen_yitems as Y  # noqa: E402
import gen_yiluzja as YI  # noqa: E402  (client_grid, ascii_pl, crlf_text)
import gen_ycrack as YC  # noqa: E402  (the earlier client rows)

M = 'MT2009_PLUS_YOHARA_ZAKLETY_V1'
OUT = os.path.join(REPO, 'linux-port', 'docker', 'game', 'yohara_zaklety')
ILUZJA = os.path.join(REPO, 'linux-port', 'docker', 'game', 'yohara_iluzja')
PB = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot')
SQL_OUT = os.path.join(PB, 'yohara_zaklety.sql')
ZYW_OUT = os.path.join(PB, 'yohara_zaklety_zywioly.sql')
ITEMS_OUT = os.path.join(PB, 'yohara_items_zaklety.sql')
JSON_OUT = os.path.join(HERE, 'yzaklety_client.json')
ICON_OUT = os.path.join(REPO, 'client-patches', 'client-2.0.30', 'root', 'icon', 'item')
EARLIER_JSON = YC.EARLIER_JSON + [YC.JSON_OUT]
OUR_ATLAS = '/opt/metin2/cache/cY/chk/gamedata/atlasinfo.txt'

REGEN = ['regen.txt', 'boss.txt', 'stone.txt']
MOTIONS = ['trent_soldier', 'trent_magic', 'trent_general', 'trent_boss', 'trent_boss2', 'thunder_boss']
# every position the quests use (linux-port/docker/game/quest/zaklety_las.quest, erebu.quest,
# temple_of_the_ochao.quest, starozytna_dzungla.quest's way out is the temple's)
QUEST_POINTS = dict(entry=[D.MAP['town']], erebu=[D.EREBU_ENTRY, D.EREBU_BOSS], leader_side=[D.LEADER_SIDE],
                    sovereign=[(587, 97)])
QUEST_SPAWNED = [6408, 6192]
SUMMONS = [6404, 6409, 6401, 6410]      # Władca / Bagjanamu, Jotun Thrym, Niszczyciel, Silny Niszczyciel


def owsap_groups(a, want):
    t = open(os.path.join(a.owsap, 'share/locale/uk/group.txt'), encoding='latin-1').read().replace('\r', '')
    out = {}
    for m in re.finditer(r'Group\s+(\S+)\s*\{(.*?)\}', t, re.S):
        b = m.group(2)
        v = re.search(r'Vnum\s+(\d+)', b)
        if v and int(v.group(1)) in want:
            lead = re.search(r'Leader\s+"?[^"\n]*"?\s+(\d+)', b)
            mem = [int(x) for x in re.findall(r'\n\s*\d+\s+"?[^"\n]*?"?\s+(\d+)\s*(?=\n|$)', b)]
            out[int(v.group(1))] = (m.group(1), [int(lead.group(1))] + mem)
    assert sorted(out) == sorted(want), sorted(out)
    return out


def atlas_overlaps(base, size):
    x0, y0 = base
    x1, y1 = x0 + size[0] * 25600, y0 + size[1] * 25600
    bad = []
    for l in open(OUR_ATLAS, encoding='latin-1'):
        t = l.split()
        if len(t) < 5 or not t[1].isdigit():
            continue
        a0, b0 = int(t[1]), int(t[2])
        a1, b1 = a0 + int(t[3]) * 25600, b0 + int(t[4]) * 25600
        if a0 < x1 and x0 < a1 and b0 < y1 and y0 < b1:
            bad.append(t[0])
    return bad


def gen_map(a, report):
    m = D.MAP
    for sub in ('map', 'data'):
        shutil.rmtree(os.path.join(OUT, sub), ignore_errors=True)       # README.md (by hand) stays
    dst = os.path.join(OUT, 'map', m['folder'])
    os.makedirs(dst)
    osrc = os.path.join(a.owsap, 'share/locale/uk/map', m['owsap'])
    st = open(os.path.join(osrc, 'Setting.txt'), encoding='latin-1').read()
    assert re.search(r'MapSize\s+%d\s+%d' % m['size'], st) and re.search(r'BasePosition\s+%d\s+%d' % m['base'], st)
    gfst = open(os.path.join(a.gf, m['folder'], 'setting.txt'), encoding='latin-1').read()
    assert re.search(r'MapSize\s+%d\s+%d' % m['size'], gfst) and re.search(r'BasePosition\s+%d\s+%d' % m['base'], gfst)
    town = open(os.path.join(osrc, 'Town.txt'), encoding='latin-1').read().split()
    assert (int(town[0]), int(town[1])) == m['town'], town
    # the PB forest's Setting.txt differs in BasePosition only
    pbst = open(os.path.join(ILUZJA, 'map', m['pb_folder'], 'Setting.txt'), encoding='latin-1', newline='').read()
    assert re.sub(r'BasePosition[^\r\n]*', '', pbst) == re.sub(r'BasePosition[^\r\n]*', '',
                                                             st.replace('\r\n', '\n').replace('\n', '\r\n'))
    bad = [f for f in atlas_overlaps(m['base'], m['size']) if f != m['folder']]     # its own row once added
    assert not bad, ('the base overlaps', bad)
    open(os.path.join(dst, 'Setting.txt'), 'w', newline='').write(st.replace('\r\n', '\n').replace('\n', '\r\n'))
    open(os.path.join(dst, 'Town.txt'), 'w', newline='').write('%d\t%d\r\n' % m['town'])
    shutil.copyfile(os.path.join(ILUZJA, 'map', m['pb_folder'], 'server_attr'), os.path.join(dst, 'server_attr'))
    W, H, g, LW, LH, walk, own = YI.client_grid(a.gf, dict(m, own_attr=None))
    pts = dict(QUEST_POINTS)
    pts['npc'] = [(x, y) for v, x, y, d in D.NPC_CELLS]
    blocked = []
    for k, ps in pts.items():
        for x, y in ps:
            assert 0 <= x < LW and 0 <= y < LH, (k, x, y)
            if not walk[y * LW + x]:
                blocked.append('%s %d,%d' % (k, x, y))
    assert not blocked, blocked
    cx, cy = D.EREBU_CORNER
    assert D.EREBU_ENTRY[0] < cx and D.EREBU_ENTRY[1] > cy and not (m['town'][0] < cx and m['town'][1] > cy)
    report.append('%d %s: base %d %d (no atlasinfo overlap), server_attr = %s\'s (terrain %s), %d quest/npc points '
                  'walkable' % (m['index'], m['folder'], m['base'][0], m['base'][1], m['pb_folder'], m['src'],
                                sum(len(v) for v in pts.values())))
    # npc.txt: the wiki's cells
    open(os.path.join(dst, 'npc.txt'), 'w', newline='').write(YI.crlf_text(
        ['m\t%d\t%d\t0\t0\t0\t%d\t1m\t100\t1\t%d' % (x, y, d, v) for v, x, y, d in D.NPC_CELLS]))
    # regen / boss / stone: Owsap's
    groups = set(D.GROUPS_OWSAP)
    n = b = 0
    for fn in REGEN:
        out = []
        for l in open(os.path.join(osrc, fn), encoding='latin-1').read().replace('\r', '').split('\n'):
            t = l.split('\t')
            if len(t) < 11 or not t[1].strip().isdigit():
                continue
            v = int(t[-1])
            if t[0] == 'g':
                assert v in groups, (fn, l)
            elif t[0] == 'm':
                assert v in D.MOBS, (fn, l)
            else:
                raise SystemExit('%s: %s' % (fn, l))
            x, y = int(t[1]), int(t[2])
            assert 0 <= x < LW and 0 <= y < LH, (fn, l)
            n += 1
            b += 0 if walk[y * LW + x] else 1
            out.append('\t'.join(t))
        assert out, fn
        open(os.path.join(dst, fn), 'w', newline='').write(YI.crlf_text(out))
    report.append('regen/boss/stone: %d spawn points (Owsap\'s), %d on a blocked centre (the engine finds a free cell)'
                  % (n, b))
    # the motions
    mot = os.path.join(OUT, 'data', 'monster')
    for f in MOTIONS:
        s = os.path.join(a.owsap, 'share/data/monster', f)
        assert os.path.isfile(os.path.join(s, 'motlist.txt')), f
        acc = re.search(r'^Accumulation\s+[-0-9.]+\s+-[0-9]', open(os.path.join(s, 'run.msa'), encoding='latin-1')
                        .read(), re.M)
        assert acc, ('run.msa without Accumulation', f)
        shutil.copytree(s, os.path.join(mot, f))
    report.append('data/monster: %s (Owsap\'s motions, run.msa with Accumulation)' % ', '.join(MOTIONS))
    return groups


def write_groups(a):
    og = owsap_groups(a, D.GROUPS_OWSAP)
    L = ['// %s: the spawn groups of Zaklety Las (353) - Owsap\'s 6311-6318 (the En-Tai of the forest, Wladca' % M,
         '// En-Tai\'s guard) and 6330-6333 (Metin Lasu\'s: the pl-wiki\'s "Silny" En-Tai). Owsap\'s numbers - none of',
         '// them existed here. GENERATED by tools/yohara_zaklety/gen_yzaklety.py - do not edit.']
    gm = {}
    allg = [(v, og[v]) for v in sorted(og)] + [(v, D.GROUPS_STRONG[v]) for v in sorted(D.GROUPS_STRONG)]
    for v, (name, mobs) in allg:
        gm[v] = set(mobs)
        L += ['Group\tMT2009_yzl_%s' % name.replace('-', '_'), '{',
              '\tLeader\t"%s"\t%d' % (YI.ascii_pl(D.MOBS[mobs[0]][0]), mobs[0]), '\tVnum\t%d' % v]
        for i, mob in enumerate(mobs[1:], 1):
            assert mob in D.MOBS, (v, mob)
            L.append('\t%d\t"%s"\t%d' % (i, YI.ascii_pl(D.MOBS[mob][0]), mob))
        L += ['}', '']
    open(os.path.join(OUT, 'group.yohara_zaklety.txt'), 'w', newline='\n').write('\n'.join(L))
    return gm


def write_spawned(gm, report):
    m = D.MAP
    dst = os.path.join(OUT, 'map', m['folder'])
    vs = set(QUEST_SPAWNED) | set(SUMMONS)
    for fn in REGEN + ['npc.txt']:
        for l in open(os.path.join(dst, fn), encoding='latin-1'):
            t = l.split()
            v = int(t[-1])
            vs |= gm[v] if t[0] == 'g' else {v}
    # the Metins' groups (their rows' attack/move speed: 8059 6311-6314, 8061 6330-6333)
    for g in list(range(6311, 6315)) + list(range(6330, 6334)):
        vs |= gm[g]
    known = set(D.MOBS) | set(D.NPCS) | {D.TELEPORTER}
    assert vs <= known, sorted(vs - known)
    assert set(D.MOBS) - vs == set(), sorted(set(D.MOBS) - vs)
    lines = ['# %s: every vnum the map shows (the spawn files with their groups unfolded, the Metins\' groups,' % M,
             '# the quests\' bosses, the summons) - the client builder (client-patches/client-2.0.30/tools/yzaklety)',
             '# reads it. GENERATED by tools/yohara_zaklety/gen_yzaklety.py.']
    lines += ['%d %d' % (m['index'], v) for v in sorted(vs)]
    open(os.path.join(OUT, 'spawned.txt'), 'w', newline='\n').write('\n'.join(lines) + '\n')
    report.append('spawned: %d vnums' % len(vs))


# ------------------------------------------------------------------------------------------------ mob_proto
SQL_HEAD = """-- %(m)s: Zaklety Las (353, metin2_map_dawnmist_dungeon_01) and Erebu (Jotun Thrym) - the open forest past the
-- Temple of Ochao (the owner, 14 October 2026: it replaces the Arezzo forest).
-- GENERATED by tools/yohara_zaklety/gen_yzaklety.py - do not edit, rerun it. Every start (apply.sh), idempotent:
-- INSERT IGNORE - a row the operator changed is kept. Every vnum was free in our world (14 October 2026).
-- %(n)d rows: %(mobs)d monsters, bosses and stones (Owsap v6.2.6 db/mob_proto.txt, the official vnums, in our r40250
-- columns - tools/yohara_maps/gen_ymaps_sql.row_of; the Polish names of the pl-wiki; the pl-wiki over Owsap:
-- Jotun Thrym summons Uzdrowiciele Ochao (the experience Owsap's = the owner's sheet of 20 October); the tr-wiki: Jotun Thrym drops 10-27 million
-- Yang) and %(npcs)d NPCs (Strazniki Lasu - our 20160-20162, the official 20409-20411 are Orc Valley's archers here;
-- Przywodca Straz. Lasu - the official 20412). The elements: yohara_zaklety_zywioly.sql (after zywioly_moby.sql).
SET NAMES utf8mb4;

"""

ZHEAD = """-- %s: the elements of Zaklety Las (353) and Erebu - the pl-wiki's "Zywiol" of each monster: the En-Tai and
-- Uzdrowiciel Ochao wind, Wladca En-Tai and Bagjanamu ice, Jotun Thrym earth (setRaceFlag bits 11-16), the Metins none.
-- GENERATED by tools/yohara_zaklety/gen_yzaklety.py. apply.sh runs it AFTER zywioly_moby.sql, which clears bits 11-16
-- of every mob it does not list: idempotent.
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
        pl, elem = D.MOBS[v]
        assert len(pl.encode('cp1250')) <= 24, pl
        r = dict(rows[v])
        assert r['Type'] in ('MONSTER', 'STONE'), (v, r['Type'])
        assert r['MinGold'] == '0' and r['MaxGold'] == '0', v
        r.update(D.OVERRIDE.get(v, {}))
        lines.append(row_of(r, en[v][:24], pl))
    for v in sorted(D.NPCS):
        en_n, pl, race = D.NPCS[v]
        assert len(pl.encode('cp1250')) <= 24, pl
        lines.append(npc_row(v, en_n[:24], pl, ''))
    assert len(set(t[0] for t in lines)) == len(lines)
    for t in lines:
        assert len(t) == len(COLS), (t[0], len(t))
    with open(SQL_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write(SQL_HEAD % dict(m=M, n=len(lines), mobs=len(D.MOBS), npcs=len(D.NPCS)))
        f.write('INSERT IGNORE INTO world.mob_proto (%s) VALUES\n' % ','.join('`%s`' % c for c in COLS))
        f.write(',\n'.join('(%s)' % ','.join(str(x) for x in t) for t in lines) + ';\n')
    L = [ZHEAD]
    for elem, nm in ((D.WIND, 'wiatr'), (D.ICE, 'lod'), (D.EARTH, 'ziemia')):
        vs = sorted(v for v, (pl, e) in D.MOBS.items() if e == elem)
        L += ['-- %s: %s' % (nm, ','.join(map(str, vs))),
              'UPDATE world.mob_proto SET setRaceFlag = ((setRaceFlag + 0) & ~%d) | %d WHERE vnum IN (%s);'
              % (D.ELEMENT_BITS, elem, ','.join(map(str, vs)))]
    none = sorted(v for v, (pl, e) in D.MOBS.items() if not e)
    L += ['-- no element (the Metins): %s' % ','.join(map(str, none)),
          'UPDATE world.mob_proto SET setRaceFlag = (setRaceFlag + 0) & ~%d WHERE vnum IN (%s) AND '
          '(setRaceFlag + 0) & %d <> 0;' % (D.ELEMENT_BITS, ','.join(map(str, none)), D.ELEMENT_BITS)]
    with open(ZYW_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')
    report.append('mob_proto rows: %d (monsters/Metins %d, NPCs %d)' % (len(lines), len(D.MOBS), len(D.NPCS)))
    return lines


# ------------------------------------------------------------------------------------------------ the items
ITEM_TEXT = {
    D.DRYAD: 'W tym tajemniczym zielonkawym kamieniu jest zamknięta dusza driady, drzewnego duszka. Driada zna '
             'zaklęte słowa, które otwierają wstęp do Erebu - Przywódca Straży Lasu wpuszcza grupę, której każdy '
             'członek go ma (znika przy wejściu).',
    D.TIMBER: 'Szlachetne Drewno od Władcy En-Tai. Zanieś je Badaczowi Lasu.',
    D.DEW: 'Rosa En-Tai od Niszczycieli En-Tai. Zanieś pięć Zwiadowcy Lasu.',
    D.SPIRIT: 'Duch Ziemi od Strażnika Świątyni. Zanieś go Strażnikowi Lasu w Zaklętym Lesie.',
    D.EMERALD: 'Drzewny Szmaragd od Władcy En-Tai. Zanieś go Badaczowi Lasu - da ci Kamień Driad.',
    D.AIDKIT: 'Apteczka strażników Zaklętego Lasu.',
    D.CHEST_JOTUN: 'Skrzynia Jotuna Thryma z Erebu - jej ciężka kłódka wróży cenną zawartość.',
    D.CHEST_BAGJANAMU: 'Ta skrzynia została wydobyta z Erebu. Znajduje się w niej prawdziwy królewski skarb.',
}


def gen_items(a, report):
    rows = Y.read_tsv(os.path.join(a.owsap, 'db/item_proto.txt'))
    head = rows[0]
    proto = dict((int(r[0]), dict(zip(head, r))) for r in rows[1:] if r and r[0].isdigit())
    desc = {}
    for r in Y.read_tsv(os.path.join(os.path.dirname(os.path.dirname(a.owsap)),
                                     'Client/Client/pack/locale/locale/pl/itemdesc.txt')):
        if len(r) >= 2 and r[0].strip().isdigit():
            desc[int(r[0])] = (r[1].strip(), r[2].strip() if len(r) > 2 else '')
    gf_list = {}
    for r in Y.read_tsv(os.path.join(a.gf, 'shared/common/item_list.txt')):
        if len(r) >= 3 and r[0].strip().isdigit():
            gf_list[int(r[0])] = r[2].strip()
    earlier = set()
    for p in EARLIER_JSON:
        earlier |= set(i['vnum'] for i in json.load(open(p, encoding='utf-8'))['items'])
    items = []
    for v in D.ITEMS:
        assert v not in earlier, v
        o = proto[v]
        name = desc[v][0]
        assert name and len(name.encode('cp1250')) <= 24, (v, name)
        anti = Y.flags(o['AntiFlags'].replace('ANTI_MAIL', 'NONE'), Y.ANTI, 'antiflag')
        flag = Y.flags(o['Flags'], Y.FLAGS, 'flag')
        if v in (D.CHEST_JOTUN, D.CHEST_BAGJANAMU):
            # a chest opened as one (Owsap's 54701 is a gacha box, opened three times - our engine has none)
            typ, sub, anti = 23, 0, 0
            flag |= Y.FLAGS['ITEM_STACKABLE']
        else:
            typ, sub = 18, 0            # the quests' items (Owsap: Kamień Driad a material) - as Kamień Driad (PB)
            flag |= Y.FLAGS['ITEM_QUEST_USE']
        if v == D.DRYAD:
            # the pl-wiki: NPC trade yes, players / shop / drop / storage / mail no, stacking yes
            anti |= Y.ANTI['ANTI_DROP']
        icon = gf_list.get(v)
        assert icon, v
        items.append(dict(
            vnum=v, src=v, status=Y.ST, name=Y.ascii_name(name), locale_name=name, type=typ, subtype=sub,
            stack=200 if flag & Y.FLAGS['ITEM_STACKABLE'] else 1, weight=0, size=int(o['Size']), antiflag=anti,
            flag=flag, wearflag=0, gold=0, shop_buy_price=int(o['ShopSellPrice']),
            refined_vnum=0, refine_set=0, magic_pct=0, specular=0, socket_pct=0, addon_type=0,
            limittype0=0, limitvalue0=0, limittype1=0, limitvalue1=0,
            applytype0=0, applyvalue0=0, applytype1=0, applyvalue1=0, applytype2=0, applyvalue2=0,
            value0=0, value1=0, value2=0, value3=0, value4=0, value5=0,
            icon='icon/item/' + os.path.basename(icon), icon_src=icon, desc=ITEM_TEXT[v], list_type='ETC', model=''))
    L = ['-- %s: Kamien Driad (Erebu\'s pass), the items of the seven missions of Zaklety Las and the two chests' % M,
         '-- of Erebu. GENERATED by tools/yohara_zaklety/gen_yzaklety.py - do not edit, rerun it. Every start (apply.sh),',
         '-- idempotent: INSERT IGNORE. Source: Owsap v6.2.6 db/item_proto.txt (the official vnums), the Polish names of its',
         '-- Polish client, the pl-wiki\'s trade rules of Kamien Driad; the chests a chest opened once (Owsap\'s Skrzynia',
         '-- Bagjanamu is a gacha box). Every vnum free in our world (14 October 2026).',
         'SET NAMES utf8mb4;',
         'INSERT IGNORE INTO world.item_proto (%s) VALUES' % ','.join('`%s`' % c for c in Y.COLS),
         ',\n'.join(Y.sqlrow(i) for i in items) + ';']
    with open(ITEMS_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')
    os.makedirs(ICON_OUT, exist_ok=True)
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


# -- items we have, by the pl-wiki's name (checked on the test server's world.item_proto, 14 October 2026) ----------
HAVE = {
    # MT2009_PLUS_RIPOSTY_FORGET_V1: the Podreczniki (yohara_items.sql, server-patches/riposty)
    50514: 'Podrecznik: Dopalacz', 50515: 'Podrecznik: Riposta',
    27002: 'Czerwona Mikstura(S)', 27003: 'Czerwona Mikstura(D)', 27005: 'Niebieska Mikstura(S)',
    27006: 'Niebieska Mikstura(D)', 27102: 'Zielona Mikstura(D)', 27105: 'Fioletowa Mikstura(D)',
    50721: 'Kwiat Brzoskwini', 50722: 'Pokrzywa', 50723: 'Kwiat Kaki', 50724: 'Korzen Gango', 50725: 'Bez',
    50726: 'Grzyb Tue', 50727: 'Roza Alpejska', 50728: 'Morwa',
    30606: 'Srebrne Plyty', 30608: 'Stalowe Plyty', 95601: 'Stabilne Sznury', 95602: 'Wzor Kroju',
    95603: 'Ciezkie Pasy', 30616: 'Dwutlenek Tytanu', 30610: 'Mithril', 30192: 'Mleczny Sok', 30617: 'Agat',
    30618: 'Kamien Ksiezycowy', 30507: 'Brazowy Zacisk', 30504: 'Srebrny Zacisk', 30501: 'Zlota Sprzaczka',
    30502: 'Rubinowa Ozdoba', 30508: 'Szafirowa Ozdoba', 30500: 'Rubinowy Ozdobny Noz',
    30503: 'Ametystowy Ozdobny Noz', 30506: 'Szafirowy Ozdobny Noz', 30509: 'Niebieska Smocza Stal',
    30512: 'Czerwona Smocza Stal', 30515: 'Purpurowa Smocza Stal', 30516: 'Antyczny Naramiennik',
    30517: 'Zloty Material', 30519: 'Zloty Hak', 30520: 'Zlota Spinka', 30522: 'Ogniwa Lancucha',
    30602: 'Niebieski Barwnik', 30603: 'Czerwony Barwnik', 30604: 'Szary Barwnik',
    30623: 'Ksiega Prawdy', 30624: 'Dusza Prawdy', 30627: 'Owoc Bogow', 30629: 'Eliksir Bogow',
    30227: 'Kamien Liderow', 50513: 'Kamien Duchowy', 50525: 'Kamien Duchowy+', 50300: 'Ksiega Umiejetnosci',
    25040: 'Zwoj Blogoslawienstwa', 25100: 'Zwoj Kamienia Duszy', 27992: 'Biala Perla', 27993: 'Niebieska Perla',
    27994: 'Krwawa Perla', 70012: 'Lza Bogini', 70014: 'Pigulka Krwi', 70031: 'Broszura Szermierki',
    70037: 'Ksiega Zapomnienia', 70038: 'Peleryna Mestwa', 39002: 'Pierscien Doswiadczenia (1 h)',
    72006: 'Rekawica Zlodzieja (3 h)', 71095: 'Przepustka', 50007: 'Srebrna Szkatulka', 50121: 'Zelazne Pudelko',
    39075: 'Fioletowy Odlamek', 39076: 'Czerwony Odlamek', 39077: 'Teczowy Odlamek', 39080: 'Zolty Lsniacy Odlamek',
    14220: 'Opaska Krysztalu Duszy', 16060: 'Zloty Naszyjnik', 12400: 'Pajeczy Kaptur', 12540: 'Magiczny Helm',
    15200: 'Buty Feniksa', 15370: 'Buty Euforii', 15430: 'Buty Zimorodka',
    5070: 'Zloty Robaczy Dzwon', 5100: 'Dzwon Nieba I Ziemi', 7140: 'Wachlarz Zbawienia', 7150: 'Ekstazyjny Wachlarz',
    2130: 'Boski Luk Moreli', 2140: 'Olbrz. Luk Zolt. Smoka', 3090: 'Lodowa Iglica', 3140: 'Magnetyczne Ostrze',
    140: 'Miecz Bojowy', 150: 'Miecz Szponu Ducha', 180: 'Zatruty Miecz', 1100: 'Smoczy Noz',
    1106: 'Smoczy Noz+6', 155: 'Miecz Szponu Ducha+5', 2147: 'Olbrz. Luk Zolt. Smoka+7', 11897: 'Czarna Szata+7',
    11496: 'Ubranie Czarn. Wiatru+6', 11295: 'Zbroja Z Czarnej Stali+5', 11695: 'Zbr. Plyt. Czar. Magii+5',
    20000: 'Pancerz Diabel. Rogu', 20250: 'Szata Smoczego Jezdzca', 20500: 'Pancerz Kosciplytowy',
    20750: 'Zlote Ubranie', 13060: 'Sokola Tarcza', 13080: 'Tarcza Tygrysa', 13100: 'Lwia Tarcza',
    13120: 'Tarcza Smoka', 13140: 'Tarcza Tytanow', 13160: 'Tarcza Trzech Wladcow',
    18000: 'Pas Lniany', 18010: 'Pas Skorzany', 18020: 'Pas Przepychu', 18030: 'Pas Madrosci', 18080: 'Pas Dusz',
    # MT2009_PLUS_ARMOR105_V1 (22 October 2026): the level-105 armours' materials (tools/zbroje105)
    30601: 'Plan Zbroi', 30605: 'Zlote Plyty', 30607: 'Miedziane Plyty', 30609: 'Brazowe Plyty',
    30614: 'Czarny Barwnik', 30615: 'Bialy Barwnik', 30619: 'Barwnik zloty metalik',
}
# MT2009_PLUS_ARMOR105_V1 (the owner, 22 October 2026): the level-105 armours' materials the pl-wiki's lists give these
# monsters and the owner's monster sheet does not (its rows - the En-Tai 6401 / 6403 / 6406 / 6407 - are
# tools/ymoby_arkusz's, game/yohara_arkusz): the chances of the owner's package p-gf-po-3.0.1 (as the monster's other
# materials: an En-Tai 0.5, Bagjanamu 15, Jotun Thrym 20)
ARMOR105 = {
    6402: [(30609, 1, 0.5)],
    6408: [(30601, 1, 15), (30605, 1, 15), (30607, 1, 15), (30609, 1, 15), (30615, 1, 15)],
    6192: [(30601, 1, 20), (30609, 1, 20), (30615, 1, 20), (30619, 1, 20)],
}


# -- the chests: one thing an opening, by weight -----------------------------------------------------------------
def chests():
    # MT2009_PLUS_CHEST_DROPS_V1: the rows and their chances - the owner's sheet of 15 October 2026
    # (tools/yohara_chestdrops: the official vnums mapped to ours, what we lack left out and the rest renormalised)
    return [(vnum, title, CD.table(vnum)[0]) for vnum, title in (
        (D.CHEST_JOTUN, 'Skrzynia Jotuna Thryma - Jotun Thrym (Erebu)'),
        (D.CHEST_BAGJANAMU, 'Skrzynia Bagjanamu - Bagjanamu (Erebu)'))]


# -- the drops (mob_drop_item, Type drop: vnum, count, percent): the pl-wiki's list of each monster, boss and Metin;
#    the odds ours, official-like; the bosses' chests always ("9-11" / "8-10" -> 10 / 9). The test server's drop
#    event is not compensated for. Apteczka / Rosa En-Tai / Szlachetne Drewno / Drzewny Szmaragd are the quest's. -----
# MT2009_PLUS_RIPOSTY_FORGET_V1 (owner, 21 October 2026: "Podreczniki z Metina Lasu i Niszczyciela En-Tai z wiki"): the
# wiki's Podrecznik: Riposta (50515) from Metin Lasu and Niszczyciel En-Tai, Podrecznik: Dopalacz (50514) from Niszczyciel
# En-Tai (Metin Lasu's page has no Dopalacz). The wiki and the owner's sheet give no chances: tools/ymoby_arkusz's
# default for an "other" item - a normal monster 0.2, a Metin 4.
PODRECZNIKI_ENTAI = [(50515, 1, 0.2), (50514, 1, 0.2)]
PODRECZNIKI_METIN = [(50515, 1, 4)]


def drops():
    herbs8 = [(50725, 8, 20), (50726, 8, 20), (50721, 8, 20), (50724, 8, 20), (50728, 8, 20), (50722, 1, 20)]
    return [
        (6401, 'Wojownik En-Tai', [(30606, 1, 0.5), (95601, 1, 0.5)]),
        (6402, 'Bojownik En-Tai', [(5100, 1, 0.3), (7150, 1, 0.3), (5070, 1, 0.3), (16060, 1, 0.3), (30606, 1, 0.5),
                                   (50722, 1, 1), (50007, 1, 0.5)]),
        (6403, 'Druid En-Tai', [(2130, 1, 0.3), (3090, 1, 0.3), (12400, 1, 0.3), (15200, 1, 0.3), (30507, 1, 0.5),
                                (30502, 1, 0.5), (30604, 1, 0.5), (30606, 1, 0.5), (30608, 1, 0.5), (50725, 1, 1),
                                (50728, 1, 1), (50121, 1, 0.5)]),
        (6404, 'Uzdrowiciel En-Tai', [(12540, 1, 0.3), (30606, 1, 0.5), (30604, 1, 0.5), (95601, 1, 0.5),
                                      (50723, 1, 1), (25100, 1, 0.5), (50121, 1, 0.5)]),
        (6406, 'Niszczyciel En-Tai', [(95603, 1, 0.5), (30616, 1, 0.5), (30610, 1, 0.5), (30192, 1, 0.5),
                                      (95601, 1, 0.5), (30606, 1, 0.5), (30608, 1, 0.5), (50728, 1, 1),
                                      (50121, 1, 0.5)] + PODRECZNIKI_ENTAI),
        (6414, 'Silny Niszczyciel En-Tai', [(50724, 1, 2), (50728, 1, 2)]),
        (6407, 'Wladca En-Tai', [(14220, 1, 5), (27003, 10, 40), (27105, 10, 380), (27006, 10, 40), (27102, 10, 380)] +
         herbs8 + [(39076, 1, 10), (39075, 1, 10), (39077, 1, 5), (50513, 1, 15), (50300, 1, 10)]),
        (6408, 'Bagjanamu', [(D.CHEST_BAGJANAMU, 10, 100), (27102, 10, 40), (30227, 1, 20), (30520, 1, 15),
                             (30503, 1, 15), (50725, 3, 25), (50726, 3, 25), (50724, 3, 25), (50721, 3, 25),
                             (50723, 3, 25), (50728, 3, 25), (50722, 3, 25), (50727, 3, 25), (50513, 1, 20)]),
        (6192, 'Jotun Thrym', [(D.CHEST_JOTUN, 9, 100), (27003, 10, 40), (27006, 10, 40), (27102, 10, 40),
                               (30227, 1, 20), (50726, 3, 30), (50724, 3, 30), (30192, 2, 30), (30610, 2, 30),
                               (30617, 1, 20), (39075, 1, 15), (39077, 1, 10), (39080, 1, 15)]),
        (8059, 'Metin Drzewnych Stworzen', [(7150, 1, 5), (50513, 1, 10), (30606, 1, 15), (95601, 1, 15)]),
        (8061, 'Metin Lasu', [(1106, 1, 2), (155, 1, 2), (2147, 1, 2), (11897, 1, 2), (11496, 1, 2), (11295, 1, 2),
                              (11695, 1, 2), (27003, 30, 20), (27002, 50, 20), (27006, 20, 20), (27005, 30, 20),
                              (30516, 1, 5), (30512, 1, 5), (30522, 1, 5), (30506, 1, 5), (50513, 1, 15),
                              (50525, 1, 5), (70037, 1, 3), (70012, 1, 3), (70038, 20, 10), (39002, 1, 3),
                              (70014, 1, 3), (72006, 1, 3), (25040, 1, 5)] + PODRECZNIKI_METIN),
    ]


def nm(byv, v, c=1):
    n = byv[v]['name'] if v in byv else HAVE[v]
    return n + (' x%d' % c if c > 1 else '')


def write_drops(byv):
    L = ['// %s: drops of Zaklety Las (353) and Erebu - the pl-wiki\'s lists ("Wojownik En-Tai" ... "Jotun' % M,
         '// Thrym", "Metin Lasu"). GENERATED by tools/yohara_zaklety/gen_yzaklety.py - do not edit. The percents are ours,',
         '// official-like. Left out what our world has not (Szpon Gryfa, Stalowy / Zelazny Szpon, Ksiega Misji (Ksiaze 2),',
         '// Zwoj Skarbu (B), Zielona Smocza Fasola, Peleryna Maskujaca, Ksiega Dzielnego / Dzikiego Zwierza, Opatrunek); the',
         '// level-105 armours\' plates, Plan Zbroi and dyes since MT2009_PLUS_ARMOR105_V1 (22 October 2026). Apteczka,',
         '// Rosa En-Tai, Szlachetne Drewno and Drzewny Szmaragd are the quest\'s (zaklety_las).', '']
    for v, n, rows in drops():
        assert v in D.MOBS, v
        rows = rows + ARMOR105.get(v, [])
        L += ['Group\tMT2009_yzl_%d' % v, '{', '\tMob\t%d\t-- %s' % (v, n), '\tType\tdrop']
        for k, (iv, c, p) in enumerate(rows, 1):
            assert iv in byv or iv in HAVE, (v, iv)
            L.append('\t%d\t%d\t%d\t%s\t-- %s' % (k, iv, c, '%g' % p, nm(byv, iv, c)))
        L += ['}', '']
    with open(os.path.join(OUT, 'mob_drop_item.yohara_zaklety.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L))


def write_sig(byv):
    L = ['# %s: the chests of Erebu - Skrzynia Jotuna Thryma (50266) and Skrzynia Bagjanamu (54701), their' % M,
         '# contents as on their pl-wiki pages, one thing an opening, by weight (the owner\'s sheet of 15 October 2026).',
         '# GENERATED by tools/yohara_zaklety/gen_yzaklety.py - do not edit. Appended to special_item_group.txt by the',
         '# Dockerfile.', '']
    for vnum, title, rows in chests():
        assert vnum in byv
        L += CD.comment(vnum)
        L += ['Group\tMT2009_yzl_%d' % vnum, '{', '\tVnum\t%d -- %s' % (vnum, title)]
        for k, (v, c, w, n) in enumerate(rows, 1):
            L.append('\t%d\t%s\t%d\t%d -- %s' % (k, v, c, w, n))
        L += ['}', '']
    with open(os.path.join(OUT, 'special_item_group.yohara_zaklety.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L))


def write_client(mob_lines, items):
    keys = ('vnum', 'name', 'locale_name', 'type', 'subtype', 'stack', 'weight', 'size', 'antiflag', 'flag',
            'wearflag', 'gold', 'shop_buy_price', 'refined_vnum', 'refine_set', 'magic_pct', 'specular', 'socket_pct',
            'limittype0', 'limitvalue0', 'limittype1', 'limitvalue1', 'applytype0', 'applyvalue0', 'applytype1',
            'applyvalue1', 'applytype2', 'applyvalue2', 'value0', 'value1', 'value2', 'value3', 'value4', 'value5')
    m = D.MAP
    out = {'cols': list(COLS), 'rows': [list(t) for t in mob_lines],
           'elements': dict((str(v), e) for v, (pl, e) in D.MOBS.items()),
           'atlas': ['%s\t%d\t%d\t%d\t%d' % (m['folder'], m['base'][0], m['base'][1], m['size'][0], m['size'][1])],
           'npclist_add': dict((str(v), r) for v, r in D.NPC_RACE.items()),
           'items': [dict((k, i[k]) for k in keys) for i in items],
           'item_list': dict((str(i['vnum']), '%d\t%s\t%s' % (i['vnum'], i['list_type'], i['icon'])) for i in items),
           'itemdesc': dict((str(i['vnum']), '%d\t%s\t%s' % (i['vnum'], i['locale_name'], Y.client_desc(i)))
                            for i in items)}
    with open(JSON_OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=0)
        f.write('\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--owsap', default='/opt/metin2/cache/owsap/Server/Server')
    ap.add_argument('--gf', default='/opt/metin2/cache/gf/Gameforge_26.1.11/_client')
    a = ap.parse_args()
    report = []
    gen_map(a, report)
    gm = write_groups(a)
    write_spawned(gm, report)
    mob_lines = gen_mobs(a, report)
    items = gen_items(a, report)
    byv = dict((i['vnum'], i) for i in items)
    write_drops(byv)
    write_sig(byv)
    write_client(mob_lines, items)
    report.append('drops: %d groups; chests: %d' % (len(drops()), len(chests())))
    print('\n'.join(report))


if __name__ == '__main__':
    main()
