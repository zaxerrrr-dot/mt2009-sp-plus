#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_ygloves.py [--owsap DIR] [--gf DIR] [--world-dump FILE] [--length-h FILE]

MT2009_PLUS_GLOVES_V1: Rekawice Sung Ma (the owner, 14 October 2026, cache/yohara/decyzje.md "14.10 ok. 8:10":
"Rekawice Sung Ma - dodac"), as the pl-wiki gives them ("Rekawice", "Rekawice Mocy" .. "Ochronne Rekawice", "Kamien
Demonow", "Kamien Mocy") with the official vnums and numbers of Owsap v6.2.6 (Server/Server/db/item_proto.txt,
refine_proto of db/data/player.sql), the Polish names and descriptions of its Polish client and the icons of the GF
26.1.11 client - the method of tools/yohara_items/gen_yitems.py:

  23000-23009 Rekawice Mocy+0..+9       level 105 gloves (ITEM_ARMOR / ARMOR_GLOVE, the glove slot WEAR_GLOVE 26 -
  23010-23019 Zwinne Rekawice+0..+9     ENABLE_GLOVE_SYSTEM, server-patches/rekawice); 3 empty sockets (socket_pct 3)
  23020-23029 Pancerne Rekawice+0..+9   for Kamienie Demonow; no item_proto apply: the glove's Sung Ma Will (Mocy SILA,
  23030-23039 Ochronne Rekawice+0..+9   Zwinne ODP, Pancerne WIT, Ochronne INT; the wiki's ranges 3-7 .. 58-63) is its
                                        base attribute (MT2009_PLUS_GLOVE_BASE_V1: the item's yextra, not a bonus slot -
                                        the 6th and 7th are the 6/7 system's), rolled by the engine when one is made,
                                        carried by a refine;
                                        refined at the blacksmith with Owsap's refine rows 800-808 (= the wiki: 10..200
                                        Utwardzacz Skory, from +5 Utwardzacz Skory+, +6 Biala Perla, +7 Kamien
                                        Ksiezycowy, +8 Niebieska Perla, +9 Krwawa Perla; 250 000 .. 650 000 Yang) - ours
                                        22720-22728; made by Mistrz Chi in Dongan (quest rekawice);
  28046/28146/28246/28346/28446 Kamien Demonow+0..+4       Sung Ma stones (ITEM_METIN / METIN_SUNGMA 2, value0 = the
  28047/28147/28247/28347/28447 Kamien Mocy Demonow+0..+4  stone's level, value5 1 / 2 - Mocy: a chance of a double
                                        Will): put into a glove's socket they give one random Sung Ma Will 1/3/6/9/15
                                        (pl-wiki "Kamien Mocy"; server-patches/rekawice). 28046 and 28047 were inert
                                        materials (yohara_items.sql / yohara_items3.sql): UPDATEd to stones here.

and world.item_attr for the glove's five bonuses (the engine reads item_attr.glove with ENABLE_GLOVE_SYSTEM): the
`apply` ENUM grows to POINT_HIT_PCT (197, Precyzja - server-patches/precyzja; the db core's "apply+0" is the point),
the gloves' set (Owsap's glove column, the bonuses our table has) and a POINT_HIT_PCT row for gloves only.

Writes (all GENERATED - edit this file, run it again):
  linux-port/docker/mariadb/playerbot/yohara_gloves.sql      world.item_proto / refine_proto / item_attr (idempotent)
  tools/ygloves/ygloves_items.json                           the client's records, item_list and itemdesc rows
                                                             (client-patches/client-2.0.30/tools/ygloves)
  client-patches/client-2.0.30/root/icon/item/<icon>.tga     the GF glove icons (the stones' are in our icon pack)

Example: python3 tools/ygloves/gen_ygloves.py
"""
import argparse
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, 'tools', 'yohara_items'))
import gen_yitems as Y  # noqa: E402  (the engine's numbers, the row writer)

SQL_OUT = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot', 'yohara_gloves.sql')
JSON_OUT = os.path.join(HERE, 'ygloves_items.json')
ICON_OUT = os.path.join(REPO, 'client-patches', 'client-2.0.30', 'root', 'icon', 'item')

ST = Y.ST
REFINE_ID0 = 22720          # ours (Owsap's 800-808 are other rows here; 22701-22709 the jade bracelets)
ARMOR, GLOVE, METIN, METIN_SUNGMA = 2, 8, 10, 2
WEARABLE_GLOVE = Y.WEAR['WEAR_GLOVE']        # 8192 = 1 << 13
assert WEARABLE_GLOVE == 8192
GLOVES = [(23000, 'Rękawice Mocy'), (23010, 'Zwinne Rękawice'), (23020, 'Pancerne Rękawice'),
          (23030, 'Ochronne Rękawice')]
STONES = [(28046, 'Kamień Demonów', 1), (28047, 'Kamień Mocy Demonów', 2)]

# world.item_attr: the points after the base dump's last enum value (161, POINT_MAGIC_ATT) up to Precyzja; the names
# of 162-192 are common/length.h's (read from --length-h when given, else this list), 193-197 server-patches/precyzja's
POINT_HIT_PCT = 197
NEW_POINTS = {193: 'POINT_SUNGMA_PER_STR', 194: 'POINT_SUNGMA_PER_HP', 195: 'POINT_SUNGMA_PER_MOVE',
              196: 'POINT_SUNGMA_PER_IMMUNE', 197: 'POINT_HIT_PCT'}
# Owsap's item_attr glove column, as our table names them; BLEEDING_REDUCE / BLEEDING_PCT / RESIST_MOUNT_FALL: not in
# our item_attr (no rows) - left out
GLOVE_ATTRS = ['POINT_MAX_SP', 'POINT_HT', 'POINT_IQ', 'POINT_ST', 'POINT_DX', 'POINT_POISON_PCT', 'POINT_STUN_PCT',
               'POINT_SLOW_PCT', 'POINT_STEAL_HP', 'POINT_STEAL_SP', 'POINT_REFLECT_MELEE', 'POINT_POISON_REDUCE',
               'POINT_RESIST_HUMAN']
HIT_PCT_ROW = dict(prob=18, lv=(2, 4, 6, 8, 12), glove=5)      # Owsap's HIT_PCT row


def point_names(length_h):
    s = open(length_h, encoding='latin-1').read()
    i = s.index('enum EPointTypes')
    body = s[i:s.index('};', i)]
    body = re.sub(r'//[^\n]*', '', body)
    body = re.sub(r'/\*.*?\*/', '', body, flags=re.S)
    body = '\n'.join(ln for ln in body.split('\n') if not ln.strip().startswith('#'))
    out, v = {}, -1
    for tok in body[body.index('{') + 1:].split(','):
        t = tok.strip()
        if not t:
            continue
        m = re.match(r'(\w+)\s*(=\s*(\w+))?', t)
        if m.group(3):
            x = m.group(3)
            v = int(x) if x.isdigit() else dict((b, a) for a, b in out.items())[x]
        else:
            v += 1
        out.setdefault(v, m.group(1))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--owsap', default='/opt/metin2/cache/owsap')
    ap.add_argument('--gf', default='/opt/metin2/cache/gf/Gameforge_26.1.11/_client')
    ap.add_argument('--world-dump', default='/opt/metin2/mt2009plustest/linux-port/docker/mariadb/initdb.d/dumps/world.sql')
    ap.add_argument('--length-h', default='/opt/metin2/mt2009plustest/linux-port/docker/game/src/server/common/length.h')
    a = ap.parse_args()
    rows = Y.read_tsv(os.path.join(a.owsap, 'Server/Server/db/item_proto.txt'))
    head = rows[0]
    proto = dict((int(r[0]), dict(zip(head, r))) for r in rows[1:] if r and r[0].isdigit())
    desc = {}
    for r in Y.read_tsv(os.path.join(a.owsap, 'Client/Client/pack/locale/locale/pl/itemdesc.txt')):
        if len(r) >= 2 and r[0].strip().isdigit():
            desc[int(r[0])] = (r[1].strip(), r[2].strip() if len(r) > 2 else '')
    refine = {}
    with open(os.path.join(a.owsap, 'Server/Server/db/data/player.sql'), encoding='latin-1') as f:
        for m in re.finditer(r'INSERT INTO `refine_proto` VALUES \(([^)]*)\);', f.read()):
            p = [int(x) for x in m.group(1).split(',')]
            refine[p[0]] = p
    items, refines, icons = [], [], {}

    def base(vnum, o, name, text, **kw):
        flag = Y.flags(o['Flags'], Y.FLAGS, 'flag')
        d = dict(vnum=vnum, src=vnum, status=ST, name=Y.ascii_name(name), locale_name=name,
                 type=0, subtype=0, stack=200 if flag & Y.FLAGS['ITEM_STACKABLE'] else 1, weight=0, size=int(o['Size']),
                 antiflag=Y.flags(o['AntiFlags'], Y.ANTI, 'antiflag'), flag=flag, wearflag=WEARABLE_GLOVE,
                 gold=int(o['ShopBuyPrice']), shop_buy_price=int(o['ShopSellPrice']), refined_vnum=0, refine_set=0,
                 magic_pct=int(o['AlterToMagicItemPercent']), specular=int(o['Specular']),
                 socket_pct=int(o['GainSocketPercent']), addon_type=0,
                 limittype0=Y.LIMITS[o['LimitType0']], limitvalue0=int(o['LimitValue0']),
                 limittype1=Y.LIMITS[o['LimitType1']], limitvalue1=int(o['LimitValue1']),
                 applytype0=0, applyvalue0=0, applytype1=0, applyvalue1=0, applytype2=0, applyvalue2=0,
                 desc=text, **dict(('value%d' % i, int(o['Value%d' % i])) for i in range(6)))
        d.update(kw)
        assert len(d['locale_name'].encode('cp1250')) <= 32, d['locale_name']
        return d

    for k, (g0, kind) in enumerate(GLOVES):
        for lv in range(10):
            v = g0 + lv
            o = proto[v]
            assert o['Type'] == 'ITEM_ARMOR' and o['SubType'] == 'ARMOR_GLOVE' and o['WearFlags'] == 'WEAR_GLOVE', v
            assert o['ApplyType0'] == 'APPLY_RANDOM' and int(o['ApplyValue0']) == k + 1, v
            assert o['LimitType0'] == 'LEVEL' and int(o['LimitValue0']) == 105 and int(o['GainSocketPercent']) == 3, v
            pl, text = desc[v]
            assert pl == '%s+%d' % (kind, lv), (v, pl)
            rs = 0
            if lv < 9:
                assert int(o['RefinedVnum']) == v + 1 and int(o['RefineSet']) == 800 + lv, (v, o['RefineSet'])
                rs = REFINE_ID0 + lv
            items.append(base(v, o, pl, text, type=ARMOR, subtype=GLOVE, refined_vnum=v + 1 if lv < 9 else 0,
                              refine_set=rs, icon='icon/item/%d.tga' % g0, list_type='ARMOR'))
            icons['%d.tga' % g0] = '%d.tga' % g0
    for lv in range(9):
        r = refine[800 + lv]
        # id, vnum0, count0, vnum1, count1, vnum2, count2, vnum3, count3, vnum4, count4, cost, src, result, prob
        refines.append(dict(id=REFINE_ID0 + lv, mats=[(r[1], r[2]), (r[3], r[4]), (r[5], r[6]), (r[7], r[8]),
                                                         (r[9], r[10])], cost=r[11], prob=r[14], src=800 + lv))
    for s0, kind, power in STONES:
        for lv in range(5):
            v = s0 + 100 * lv
            o = proto[v]
            assert o['Type'] == 'ITEM_METIN' and o['SubType'] == 'METIN_SUNGMA' and int(o['Value5']) == power, v
            _pl, text = desc[v]                 # Owsap's 28146 is "Kamien Mocy Demonow+1" - the name is ours
            items.append(base(v, o, '%s+%d' % (kind, lv), text, type=METIN, subtype=METIN_SUNGMA, refined_vnum=0,
                              refine_set=0, value0=lv, value1=0, value2=0, value3=0, value4=0, value5=power,
                              icon='icon/item/%d.tga' % s0, list_type='ETC'))
    byv = dict((i['vnum'], i) for i in items)
    assert len(byv) == len(items) == 50
    write_sql(items, refines, attr_names(a))
    write_json(items)
    copy_icons(icons, a.gf)
    print('items %d (gloves 40, stones 10), refine rows %d (%d-%d)' % (len(items), len(refines), refines[0]['id'],
                                                                         refines[-1]['id']))


def attr_names(a):
    """The world dump's item_attr enum (the count it starts from) and the names of 1..197 the ALTER appends."""
    s = open(a.world_dump, encoding='latin-1').read()
    i = s.index('CREATE TABLE `item_attr` (')
    m = re.search(r"`apply` enum\((.*?)\) ", s[i:i + 20000], re.S)
    base = re.findall(r"'([^']*)'", m.group(1))
    pts = point_names(a.length_h) if os.path.isfile(a.length_h) else {}
    names = {}
    for k in range(1, POINT_HIT_PCT + 1):
        if k <= len(base):
            names[k] = base[k - 1]
        else:
            names[k] = NEW_POINTS.get(k) or pts.get(k) or 'POINT_ENUM_%d' % k
    assert names[12] == 'POINT_ST' and names[161] == 'POINT_MAGIC_ATT' and len(set(names.values())) == len(names)
    for n in GLOVE_ATTRS:
        assert n in base, n
    return names


def write_sql(items, refines, names):
    gloves = [i for i in items if i['type'] == ARMOR]
    stones = [i for i in items if i['type'] == METIN]
    L = ['-- MT2009_PLUS_GLOVES_V1: Rekawice Sung Ma (23000-23039), Kamienie Demonow / Mocy Demonow +0..+4 (28046-28447)',
         '-- and item_attr for the glove slot - the owner, 14 October 2026. GENERATED by tools/ygloves/gen_ygloves.py - do',
         '-- not edit, rerun it. Every start (apply.sh, after the Yohara item files), idempotent. Source: Owsap v6.2.6',
         '-- db/item_proto.txt (the official vnums and numbers), refine_proto 800-808 (db/data/player.sql) as ours %d-%d,'
         % (refines[0]['id'], refines[-1]['id']),
         '-- the Polish names of its Polish client. The gloves have no item_proto apply: their Sung Ma Will is their base',
         '-- attribute (item_yextra; server-patches/rekawice); the stones (ITEM_METIN / METIN_SUNGMA 2, value0 = level,',
         '-- value5 1 Demonow / 2 Mocy Demonow) give a random Will in a glove\'s socket (server-patches/rekawice).',
         'SET NAMES utf8mb4;',
         'INSERT IGNORE INTO world.item_proto (%s) VALUES' % ','.join('`%s`' % c for c in Y.COLS),
         ',\n'.join(Y.sqlrow(i) for i in items) + ';',
         'INSERT IGNORE INTO world.refine_proto (id,vnum0,count0,vnum1,count1,vnum2,count2,vnum3,count3,vnum4,count4,'
         'cost,src_vnum,result_vnum,prob) VALUES',
         ',\n'.join('(%d,%s,%d,0,0,%d)' % (r['id'], ','.join('%d,%d' % m for m in r['mats']), r['cost'], r['prob'])
                    for r in refines) + ';',
         '-- 28046 (yohara_items.sql) and 28047 (yohara_items3.sql) were inert materials: now the Sung Ma stones',
         '-- (only while they are still those rows - a row the operator made a stone himself is kept)']
    for i in stones:
        if i['vnum'] in (28046, 28047):
            L.append("UPDATE world.item_proto SET type=%d, subtype=%d, wearflag=%d, value0=%d, value5=%d, "
                     "refined_vnum=0, refine_set=0 WHERE vnum=%d AND type<>%d;"
                     % (METIN, METIN_SUNGMA, WEARABLE_GLOVE, i['value0'], i['value5'], i['vnum'], METIN))
    assert len(gloves) == 40
    enum_tail = ','.join("'%s'" % names[k] for k in range(162, POINT_HIT_PCT + 1))
    union = ' UNION ALL '.join("SELECT %d AS i, '%s' AS n" % (k, names[k]) for k in range(1, POINT_HIT_PCT + 1))
    L += ['-- world.item_attr `apply`: the ENUM is the POINT_* number (the db core reads apply+0). It grows to %d' % POINT_HIT_PCT,
          '-- (POINT_HIT_PCT, Precyzja) - only when POINT_HIT_PCT is not there yet and the column is still the POINT_* enum;',
          '-- the values it has stay as they are, the missing ones are appended in point order (162..%d: %s ..).'
          % (POINT_HIT_PCT, enum_tail[:60]),
          "SET @m2g_type := (SELECT COLUMN_TYPE FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = 'world' "
          "AND TABLE_NAME = 'item_attr' AND COLUMN_NAME = 'apply');",
          "SET @m2g_count := IF(@m2g_type LIKE 'enum(%''POINT_ST''%', "
          "(LENGTH(@m2g_type) - LENGTH(REPLACE(@m2g_type, ''',''', ''))) / 3 + 1, 0);",
          "SET @m2g_tail := (SELECT GROUP_CONCAT(CONCAT('''', t.n, '''') ORDER BY t.i SEPARATOR ',') FROM (%s) t "
          "WHERE t.i > @m2g_count);" % union,
          "SET @m2g_sql := IF(@m2g_count > 0 AND @m2g_count < %d AND @m2g_type NOT LIKE '%%''POINT_HIT_PCT''%%' "
          "AND @m2g_tail IS NOT NULL, CONCAT('ALTER TABLE world.item_attr MODIFY `apply` ', LEFT(@m2g_type, "
          "LENGTH(@m2g_type) - 1), ',', @m2g_tail, ') NOT NULL DEFAULT ''POINT_MAX_HP'''), 'DO 0');" % POINT_HIT_PCT,
          'PREPARE m2g_stmt FROM @m2g_sql;',
          'EXECUTE m2g_stmt;',
          'DEALLOCATE PREPARE m2g_stmt;',
          '-- the gloves\' five bonuses (Owsap\'s item_attr.glove, the bonuses our table has; Krwawienie / Odpornosc na',
          '-- upadek it has no rows for) - written once: only while no bonus has a glove level yet (a later hand edit stays)',
          'SET @m2g_gloves := (SELECT COALESCE(SUM(glove), 0) FROM world.item_attr);',
          'UPDATE world.item_attr SET glove = 5 WHERE @m2g_gloves = 0 AND apply IN (%s);'
          % ','.join("'%s'" % n for n in GLOVE_ATTRS),
          '-- Precyzja (POINT_HIT_PCT): a glove bonus only (Owsap\'s HIT_PCT row)',
          "INSERT INTO world.item_attr (apply,prob,lv1,lv2,lv3,lv4,lv5,weapon,body,wrist,foots,neck,head,shield,ear,"
          "costume_body,costume_hair,costume_weapon,pendant,glove) SELECT 'POINT_HIT_PCT',%d,%s,0,0,0,0,0,0,0,0,0,0,0,"
          "0,%d FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM world.item_attr WHERE apply = 'POINT_HIT_PCT') AND "
          "(SELECT COLUMN_TYPE FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = 'world' AND TABLE_NAME = "
          "'item_attr' AND COLUMN_NAME = 'apply') LIKE '%%''POINT_HIT_PCT''%%';"
          % (HIT_PCT_ROW['prob'], ','.join(str(x) for x in HIT_PCT_ROW['lv']), HIT_PCT_ROW['glove'])]
    with open(SQL_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')


def write_json(items):
    keys = ('vnum', 'name', 'locale_name', 'type', 'subtype', 'stack', 'weight', 'size', 'antiflag', 'flag',
            'wearflag', 'gold', 'shop_buy_price', 'refined_vnum', 'refine_set', 'magic_pct', 'specular', 'socket_pct',
            'limittype0', 'limitvalue0', 'limittype1', 'limitvalue1', 'applytype0', 'applyvalue0', 'applytype1',
            'applyvalue1', 'applytype2', 'applyvalue2', 'value0', 'value1', 'value2', 'value3', 'value4', 'value5')
    out = {'items': [dict((k, i[k]) for k in keys) for i in items],
           'item_list': dict((str(i['vnum']), '%d\t%s\t%s' % (i['vnum'], i['list_type'], i['icon'])) for i in items),
           'itemdesc': dict((str(i['vnum']), '%d\t%s\t%s' % (i['vnum'], i['locale_name'], Y.client_desc(i)))
                            for i in items)}
    with open(JSON_OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=0)
        f.write('\n')


def copy_icons(icons, gf):
    os.makedirs(ICON_OUT, exist_ok=True)
    for dst, src in sorted(icons.items()):
        s = os.path.join(gf, 'icon', 'item', src)
        assert os.path.isfile(s), s
        shutil.copyfile(s, os.path.join(ICON_OUT, dst))


if __name__ == '__main__':
    main()
