#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_relikty.py [--gf DIR] [--png-python PY]

MT2009_PLUS_RELIC_V1: Bonus Reliktu (the owner, 29 October 2026: "Add relics according to the wiki" - pl-wiki "Bonus
Reliktu", "Relikt Duszy", "Odłamek Reliktu", "Dusza Miecza / Ochrony / Ozdoby / Światła", "Pakiet Dusz", the
missions "Uratuj Handlarza Bronią / Handlarza Zbrojami / Alchemika / Uriela / Chaegiraba" and their repeatable
ones). Base package: "Official Passive Attr System" (Best Studio, github.com/ybeststudio) - its item vnums
(= the GF 26.1.11 client's, shared/common/item_list.txt, with GF's icons), its window (passive_attr) and its idea of
two relic pages; the rules and the sixteen bonuses are the wiki's. This file is the single source of:

  linux-port/docker/mariadb/playerbot/relikty.sql              world.item_proto (INSERT IGNORE), apply.sh step
  linux-port/docker/game/special_item_group.relikty.txt        Pakiet Dusz (30263, Type Pct: one of each soul)
  linux-port/docker/game/quest/relikt_*.quest                   the five missions (cp1250), Dongan (373)
  linux-port/overlays/playerbot/src/game/src/playerbot_relikty_table.h   the bonus table of the server
  client-patches/client-2.0.30/root/relikt_data.py              the bonus table of the client (tooltip, window)
  tools/relikty/relikty_items.json                              the client's item records, item_list, itemdesc
                                                                (client-patches/client-2.0.30/tools/relikty)
  client-patches/client-2.0.30/root/icon/item/<vnum>.tga        GF's icons
  linux-port/docker/itemshop/app/itemshop/img/item/<vnum>.png   the V3 shop's pictures (needs PIL: --png-python)

All GENERATED - edit this file and run it again:  python3 tools/relikty/gen_relikty.py
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, 'tools', 'yohara_items'))
import gen_yitems as Y  # noqa: E402  (the item row writer)

M = 'MT2009_PLUS_RELIC_V1'
SQL_OUT = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot', 'relikty.sql')
SIG_OUT = os.path.join(REPO, 'linux-port', 'docker', 'game', 'special_item_group.relikty.txt')
QUEST_DIR = os.path.join(REPO, 'linux-port', 'docker', 'game', 'quest')
H_OUT = os.path.join(REPO, 'linux-port', 'overlays', 'playerbot', 'src', 'game', 'src', 'playerbot_relikty_table.h')
CLIENT_ROOT = os.path.join(REPO, 'client-patches', 'client-2.0.30', 'root')
PY_OUT = os.path.join(CLIENT_ROOT, 'relikt_data.py')
ICON_OUT = os.path.join(CLIENT_ROOT, 'icon', 'item')
JSON_OUT = os.path.join(HERE, 'relikty_items.json')
PNG_OUT = os.path.join(REPO, 'linux-port', 'docker', 'itemshop', 'app', 'itemshop', 'img', 'item')

MATERIAL, QUEST, GIFTBOX = 5, 18, 23
STACKABLE = Y.FLAGS['ITEM_STACKABLE']
# a shard: storage yes, NPC / player / shop / drop no (pl-wiki "Odłamek Reliktu")
SHARD_ANTI = Y.ANTI['ANTI_DROP'] | Y.ANTI['ANTI_SELL'] | Y.ANTI['ANTI_GIVE'] | Y.ANTI['ANTI_MYSHOP']

# --- the items (vnums of the package = GF 26.1.11) -------------------------------------------------------------
SOUL_DESC = 'Może dodać lub przedłużyć bonus reliktu. Razem z pozostałymi duszami służy do dodawania bonusów i ' \
            'doładowania Reliktu Duszy (okno Bonusu Reliktu).'
SOULS = [  # (vnum, name, the window's place) - the window's order: up (sword), down (light), left (armour), right (ornament)
    (30255, 'Dusza Miecza'),
    (30258, 'Dusza Światła'),
    (30256, 'Dusza Ochrony'),
    (30257, 'Dusza Ozdoby'),
]
PACK = 30263
PACK_NAME = 'Pakiet Dusz'
# pl-wiki "Pakiet Dusz" (revision 125810, read 30 October 2026): "Opis" word for word and "Inne": "Zawartość pakietu:
# Dusza Miecza, Dusza Ochrony, Dusza Ozdoby, Dusza Światła" - four items, no count, no chance (the box gives them all:
# Type Pct, 100 each), "Duży pakiet"; only the Item-Shop for 100 SM (no metin / monster / chest source).
PACK_DESC = 'Ten praktyczny pakiet zawiera mnóstwo dusz, dzięki którym możesz doładować swoje relikty duszy i ' \
            'korzystać z potężnych bonusów reliktu. Zawartość pakietu: Dusza Miecza, Dusza Ochrony, Dusza Ozdoby, ' \
            'Dusza Światła.'
PACK_ICON = 'icon/item/27999.tga'   # the base client's chest icon of Pakiet Kamieni Duszy (72058): GF has none for it
PACK_PER_SOUL = 1                   # the wiki lists each soul once and gives no count - one of each
JOBS = ['Wojownika', 'Ninja', 'Sura', 'Szamana', 'Likana']      # JOB_WARRIOR, ASSASSIN, SURA, SHAMAN, WOLFMAN
SHARD_JOBS = ['Wojownika', 'Ninja', 'Sury', 'Szamana', 'Likana']
RELIC0, SHARD0 = 30272, 30280
RELIC_DESC = 'Może dodać bonus reliktu. Równocześnie może mieć do 4 bonusów. Bonusów nie można zmieniać. Umieść ' \
             'go w oknie Bonusu Reliktu (prawy klik) - po pierwszej aktywacji wyjęcie go niszczy.'
SHARD_DESC = 'Służy do wytworzenia Reliktu Duszy u Biologa Chaegiraba w Dongan.'


def item(vnum, name, desc, **kw):
    d = dict(vnum=vnum, src=vnum, status=Y.ST, name=Y.ascii_name(name), locale_name=name, type=MATERIAL, subtype=0,
             stack=200, weight=0, size=1, antiflag=0, flag=STACKABLE, wearflag=0, gold=1000, shop_buy_price=50,
             refined_vnum=0, refine_set=0, magic_pct=0, specular=0, socket_pct=0, addon_type=0, limittype0=0,
             limitvalue0=0, limittype1=0, limitvalue1=0, applytype0=0, applyvalue0=0, applytype1=0, applyvalue1=0,
             applytype2=0, applyvalue2=0, value0=0, value1=0, value2=0, value3=0, value4=0, value5=0, desc=desc,
             icon='icon/item/%d.tga' % vnum, list_type='ETC')
    d.update(kw)
    assert len(d['locale_name'].encode('cp1250')) <= 24, d['locale_name']
    return d


def items():
    out = [item(v, n, SOUL_DESC) for v, n in SOULS]
    out.append(item(PACK, PACK_NAME, PACK_DESC, type=GIFTBOX, icon=PACK_ICON, gold=10000, shop_buy_price=0))
    for j, n in enumerate(JOBS):
        out.append(item(RELIC0 + j, 'Relikt Duszy %s' % n, RELIC_DESC, type=QUEST, stack=1, flag=0, gold=50000,
                        shop_buy_price=1000))
    for j, n in enumerate(SHARD_JOBS):
        nm = 'Odłamek Reliktu %s' % n
        if len(nm.encode('cp1250')) > 24:
            nm = 'Odł. Reliktu %s' % n
        out.append(item(SHARD0 + j, nm, SHARD_DESC, type=QUEST, antiflag=SHARD_ANTI, gold=0, shop_buy_price=0))
    return out


# --- the bonuses (pl-wiki "Bonus Reliktu", "Możliwe Bonusy") ---------------------------------------------------
# id = the relic's attribute type (the relic's own numbers - a relic is never worn, its attributes are read by
# playerbot_relikty.cpp only; the client names them from relikt_data.py). value = x of the wiki: seconds (S),
# a chance % (C) or the size % (P). point = what the effect adds while it lasts (our POINT_* numbers).
POINT_SUNGMA_STR, POINT_SUNGMA_HP, POINT_SUNGMA_MOVE, POINT_SUNGMA_IMMUNE = 184, 185, 186, 187
POINT_MOV_SPEED, POINT_ATTBONUS_STONE, POINT_ATT_BONUS, POINT_DEF_BONUS = 19, 'POINT_ATTBONUS_STONE', 93, 94
SM = [1, 2, 3, 4, 5, 6, 7, 8, 10]
PCT9 = [1, 2, 3, 4, 5, 6, 7, 9, 15]
TEN = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
ATTACKED = 'Aktywuje się, gdy zostaniesz zaatakowany'
BONUSES = [
    # id, short name, the line ("%d" = x), trigger, values, kind, cooldown s, effect s, point, size
    (1, 'Wola SungMa (WIT)', 'Zwiększa wolę SungMa (WIT) w walce o 15 na %d sek.', ATTACKED, SM, 'S', 120, 0,
     POINT_SUNGMA_HP, 15),
    (2, 'Wola SungMa (SIŁA)', 'Zwiększa wolę SungMa (SIŁA) w walce o 15 na %d sek.', ATTACKED, SM, 'S', 120, 0,
     POINT_SUNGMA_STR, 15),
    (3, 'Wola SungMa (ODP)', 'Zwiększa wolę SungMa (ODP) w walce o 15 na %d sek.', ATTACKED, SM, 'S', 120, 0,
     POINT_SUNGMA_MOVE, 15),
    (4, 'Wola SungMa (INT)', 'Zwiększa wolę SungMa (INT) w walce o 15 na %d sek.', ATTACKED, SM, 'S', 120, 0,
     POINT_SUNGMA_IMMUNE, 15),
    (5, 'Automatyczne zbieranie', 'Posiadasz %d%% szansy, że przez 30 sek. zbierzesz automatycznie przedmioty '
     'w pobliżu', ATTACKED, PCT9, 'C', 300, 30, 0, 0),
    (6, 'Eliksir słońca', 'Podczas walki otrzymasz efekt eliksiru słońca', 'Aktywuje się, gdy nie masz pełnych PŻ',
     [100], 'N', 300, 0, 0, 0),
    (7, 'Eliksir księżyca', 'Podczas walki otrzymasz efekt eliksiru księżyca', 'Aktywuje się, gdy nie masz pełnych PE',
     [100], 'N', 300, 0, 0, 0),
    (8, 'Reset umiejętności', 'Z szansą %d%% resetuje czas odnowienia twoich umiejętności',
     'Aktywuje się, gdy użyjesz umiejętności', PCT9, 'C', 120, 0, 0, 0),
    (9, 'Atak na Metiny', 'Obrażenia zadawane Kamieniom Metin +%d%% na 5 sek.',
     'Aktywuje się, gdy zaatakujesz Kamień Metin', TEN, 'P', 120, 5, POINT_ATTBONUS_STONE, 0),
    (10, 'Obrona przy Metinach', 'Twoja obrona wzrasta o %d%% na 5 sek.', 'Aktywuje się, gdy zaatakujesz Kamień Metin',
     TEN, 'P', 120, 5, POINT_DEF_BONUS, 0),
    (11, 'Atak z wierzchowca', 'Obrażenia zwiększają się o %d%% na 10 sek.', 'Aktywuje się przy dosiadaniu wierzchowca',
     [1, 2, 3, 4, 5], 'P', 120, 10, POINT_ATT_BONUS, 0),
    (12, 'Prędkość po zsiadaniu', 'Prędkość ruchu wzrasta o %d%% na 10 sek.',
     'Aktywuje się przy zsiadaniu z wierzchowca', SM, 'P', 120, 10, POINT_MOV_SPEED, 0),
    (13, 'Drop z bossów', 'Szansa na wypadnięcie przedmiotu z bossa +%d%%', 'Działa przy każdym zabiciu bossa',
     SM, 'P', 0, 0, 0, 0),
    (14, 'Uniknięcie śmierci', '%d%% szansy na uniknięcie śmierci i odnowienie 30%% PŻ',
     'Aktywuje się, gdy zginiesz - anuluje śmierć', [5, 7, 11, 15, 20, 30, 50], 'C', 600, 0, 0, 0),
    (15, 'Peleryna męstwa', '%d%% szansy, że wszystkie potwory wokół zaatakują cię (peleryna męstwa)',
     'Aktywuje się podczas ataku na potwora', TEN, 'C', 180, 0, 0, 0),
    (16, 'Deptanie', '%d%% szansy na deptanie przeciwników przez 20 sek.',
     'Aktywuje się podczas ataku z wierzchowca', TEN, 'C', 120, 20, 0, 0),
]
KIND = {'S': 0, 'C': 1, 'P': 2, 'N': 3}     # value = seconds / chance / size / none (fixed)


def weights(n):
    # the lower values are the common ones (as the 6th/7th bonus lines): 100, 70, 49, ... a level
    return [max(1, int(round(100 * 0.7 ** i))) for i in range(n)]


def c_str(s):
    out = ''
    for ch in s:
        b = ch.encode('cp1250')
        out += ch if b[0] < 0x80 and ch not in '"\\' else ''.join('\\x%02x' % x for x in b) if b[0] >= 0x80 else '\\' + ch
    # a hex escape followed by a hex digit would swallow it
    import re
    return re.sub(r'(\\x[0-9a-f]{2})(?=[0-9a-fA-F])', r'\1""', out)


def write_header():
    L = ['// %s: GENERATED by tools/relikty/gen_relikty.py - do not edit, rerun it. The sixteen bonuses of the' % M,
         '// pl-wiki "Bonus Reliktu" (playerbot_relikty.cpp; the client\'s copy: root/relikt_data.py). x of the wiki is',
         '// the value of a level: seconds (KIND_SECONDS), a chance (KIND_CHANCE), a size in % (KIND_SIZE) or nothing',
         '// (KIND_NONE: 100). A new bonus takes a level by its weight (the lower ones are the common ones).',
         '#ifndef MT2009_PLUS_PLAYERBOT_RELIKTY_TABLE_H',
         '#define MT2009_PLUS_PLAYERBOT_RELIKTY_TABLE_H',
         '',
         'namespace relic_table',
         '{',
         '\tenum EKind { KIND_SECONDS = 0, KIND_CHANCE = 1, KIND_SIZE = 2, KIND_NONE = 3 };',
         '\tenum { BONUS_NUM = %d, LEVEL_MAX = 10 };' % len(BONUSES),
         '\tstruct TBonus',
         '\t{',
         '\t\tunsigned char bId;',
         '\t\tunsigned char bKind;',
         '\t\tint iCooldown;\t\t// seconds; 0 = every time',
         '\t\tint iEffect;\t\t// seconds the effect lasts (KIND_SECONDS: the value is it)',
         '\t\tunsigned char bPoint;\t// the point the effect adds (0: none)',
         '\t\tint iSize;\t\t// a fixed size of that point (Sung Ma: 15); 0 = the value',
         '\t\tint iLevels;',
         '\t\tshort asValue[LEVEL_MAX];',
         '\t\tshort asWeight[LEVEL_MAX];',
         '\t\tconst char* szName;\t// cp1250',
         '\t};',
         '\tstatic const TBonus s_aBonus[BONUS_NUM] =',
         '\t{']
    for b in BONUSES:
        bid, name, _line, _trig, vals, kind, cd, eff, point, size = b
        assert len(vals) <= 10
        v = vals + [0] * (10 - len(vals))
        w = weights(len(vals)) + [0] * (10 - len(vals))
        L.append('\t\t{ %d, %d, %d, %d, %s, %d, %d, { %s }, { %s }, "%s" },' % (
            bid, KIND[kind], cd, eff, point, size, len(vals), ', '.join(map(str, v)), ', '.join(map(str, w)),
            c_str(name)))
    L += ['\t};', '}', '', '#endif', '']
    with open(H_OUT, 'w', encoding='ascii', newline='\n') as f:
        f.write('\n'.join(L))


def py_str(s):
    return repr(s.encode('cp1250'))[1:]   # a Python 2 byte string literal ('...')


def write_client_py():
    L = ['# %s: GENERATED by tools/relikty/gen_relikty.py - do not edit. The bonuses of a Relikt Duszy (pl-wiki' % M,
         '# "Bonus Reliktu") - the server\'s copy: playerbot_relikty_table.h. A relic\'s attribute type is the id, its',
         '# value the x of the line. Texts cp1250.',
         '',
         'RELIC_FIRST = %d' % RELIC0,
         'RELIC_LAST = %d' % (RELIC0 + len(JOBS) - 1),
         'SHARD_FIRST = %d' % SHARD0,
         'PACK = %d' % PACK,
         '# the window\'s soul slots: up, down, left, right',
         'SOULS = (%s)' % ', '.join(str(v) for v, _n in SOULS),
         'MAX_BONUS = 4',
         '',
         '# id: (name, line with %d, trigger, cooldown s, values)',
         'BONUS = {']
    for b in BONUSES:
        bid, name, line, trig, vals, kind, cd, eff, point, size = b
        L.append('\t%d: (%s, %s, %s, %d, (%s,)),' % (bid, py_str(name), py_str(line), py_str(trig), cd,
                                                     ', '.join(map(str, vals))))
    L += ['}', '']
    with open(PY_OUT, 'wb') as f:
        f.write('\n'.join(L).encode('ascii'))


def write_sql(its):
    L = ['-- %s: Bonus Reliktu (the owner, 29 October 2026; pl-wiki "Bonus Reliktu") - GENERATED by' % M,
         '-- tools/relikty/gen_relikty.py, do not edit, rerun it. Every start (apply.sh, after yohara_czepiec.sql),',
         '-- idempotent: INSERT IGNORE - a row the operator changed is kept. The vnums of the package "Official Passive',
         '-- Attr System" (Best Studio) = the GF 26.1.11 client (shared/common/item_list.txt), free in world.item_proto:',
         '--   30255 Dusza Miecza, 30256 Dusza Ochrony, 30257 Dusza Ozdoby, 30258 Dusza Światła (ITEM_MATERIAL, stack 200,',
         '--     tradeable: missions of Dongan, ItemShop V3 39 SM, Pakiet Dusz);',
         '--   30263 Pakiet Dusz (ITEM_GIFTBOX: special_item_group.relikty.txt - one of each soul; ItemShop V3 100 SM);',
         '--   30272-30276 Relikt Duszy Wojownika / Ninja / Sura / Szamana / Likana (ITEM_QUEST, one a class, tradeable;',
         '--     sockets: 0 time left, 1 its time (1-12 h, rolled once), 2 flags; attributes: up to 4 relic bonuses);',
         '--   30280-30284 Odłamek Reliktu (ITEM_QUEST, stack 200, storage only; Chaegirab makes a relic of it).',
         '-- The system: playerbot_relikty.cpp, server-patches/relikty; the missions: quest/relikt_*.quest.',
         'SET NAMES utf8mb4;',
         'INSERT IGNORE INTO world.item_proto (%s) VALUES' % ','.join('`%s`' % c for c in Y.COLS),
         ',\n'.join(Y.sqlrow(i) for i in its) + ';']
    with open(SQL_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')


def write_sig():
    L = ['# %s: GENERATED by tools/relikty/gen_relikty.py - do not edit. Pakiet Dusz (30263, pl-wiki "Pakiet' % M,
         '# Dusz", "Zawartość pakietu": Dusza Miecza, Dusza Ochrony, Dusza Ozdoby, Dusza Światła - no count, no chance).',
         '# Type Pct: every line rolls its percent -',
         '# 100 each, so the box gives all four. Appended to special_item_group.txt by the Dockerfile (once, after any',
         '# group of the same vnum is cut out).'.replace('ś', 's').replace('Ś', 'S'),
         'Group\tmt2009_relikty_pakiet_dusz',
         '{',
         '\tVnum\t%d -- %s' % (PACK, Y.ascii_name(PACK_NAME)),
         '\tType\tPct']
    for i, (v, n) in enumerate(SOULS):
        L.append('\t%d\t%d\t%d\t100 -- %s' % (i + 1, v, PACK_PER_SOUL, Y.ascii_name(n)))
    L += ['}', '']
    L[2] = L[2].replace('Ś', 'S').replace('ś', 's')
    with open(SIG_OUT, 'w', encoding='ascii', newline='\n') as f:
        f.write('\n'.join(Y.ascii_name(x) for x in L))


def write_json(its):
    keys = ('vnum', 'name', 'locale_name', 'type', 'subtype', 'stack', 'weight', 'size', 'antiflag', 'flag',
            'wearflag', 'gold', 'shop_buy_price', 'refined_vnum', 'refine_set', 'magic_pct', 'specular', 'socket_pct',
            'limittype0', 'limitvalue0', 'limittype1', 'limitvalue1', 'applytype0', 'applyvalue0', 'applytype1',
            'applyvalue1', 'applytype2', 'applyvalue2', 'value0', 'value1', 'value2', 'value3', 'value4', 'value5')
    out = {'items': [dict((k, i[k]) for k in keys) for i in its],
           'item_list': dict((str(i['vnum']), '%d\t%s\t%s' % (i['vnum'], i['list_type'], i['icon'])) for i in its),
           'itemdesc': dict((str(i['vnum']), '%d\t%s\t%s' % (i['vnum'], i['locale_name'], Y.client_desc(i)))
                            for i in its),
           'bonuses': [dict(id=b[0], name=b[1], values=b[4], cooldown=b[6]) for b in BONUSES]}
    with open(JSON_OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=0)
        f.write('\n')


def check_gf_list(gf):
    rows = {}
    with open(os.path.join(gf, 'shared', 'common', 'item_list.txt'), 'rb') as f:
        for raw in f:
            t = raw.decode('cp1250', 'replace').rstrip('\r\n').split('\t')
            if len(t) >= 3 and t[0].strip().isdigit():
                rows[int(t[0])] = (t[1].strip(), t[2].strip())
    for v in [s[0] for s in SOULS] + list(range(RELIC0, RELIC0 + 5)) + list(range(SHARD0, SHARD0 + 5)):
        assert rows.get(v) == ('ETC', 'icon/item/%d.tga' % v), (v, rows.get(v))


def icon_vnums():
    return [s[0] for s in SOULS] + list(range(RELIC0, RELIC0 + 5)) + list(range(SHARD0, SHARD0 + 5))


def copy_icons(gf):
    os.makedirs(ICON_OUT, exist_ok=True)
    for v in icon_vnums():
        s = os.path.join(gf, 'icon', 'item', '%d.tga' % v)
        assert os.path.isfile(s), s
        shutil.copyfile(s, os.path.join(ICON_OUT, '%d.tga' % v))


def write_pngs(gf, py):
    """the V3 shop's pictures of the souls and the package (PIL in another interpreter - optional). The folder's
    30255-30258 / 30263 were pictures of other items (an old list's fireworks and letters) - ours replace them."""
    if not py:
        return 'skipped (no --png-python)'
    jobs = [(os.path.join(gf, 'icon', 'item', '%d.tga' % v), os.path.join(PNG_OUT, '%05d.png' % v)) for v, _n in SOULS]
    code = ('import sys\nfrom PIL import Image\nfor s, d in zip(sys.argv[1::2], sys.argv[2::2]):\n'
            '\tImage.open(s).convert("RGBA").save(d)\n')
    args = []
    for s, d in jobs:
        args += [s, d]
    subprocess.check_call([py, '-c', code] + args)
    # Pakiet Dusz: the picture of its icon's chest (Pakiet Kamieni Duszy's 27999)
    shutil.copyfile(os.path.join(PNG_OUT, '27999.png'), os.path.join(PNG_OUT, '%05d.png' % PACK))
    return '%d png' % (len(jobs) + 1)


# --- the missions (pl-wiki; Dongan = map 373) -----------------------------------------------------------------
DONGAN = 373
METIN_SWIADOMOSC = 8067
YOHARA_MAPS = (373, 374, 376, 377, 378, 379, 380, 381, 382, 383, 384, 385, 386, 387, 388, 389, 390, 391, 393, 394,
               395, 396)
LEK_PCT = 35          # a Metin Świadomość gives the medicine (the wiki: "aż do momentu, gdy otrzymasz Lekarstwo")
FRAG_ONE_IN = 8       # a monster of Yohara: a soul fragment while the repeatable mission collects them
ASH_ONE_IN = 6        # a monster of Dongan: an ash (Popiół) while Chaegirab's mission collects them
REPEAT_PCT = 60       # the repeatable missions: "wytworzenie może się nie udać" (the Biologist's 60%)
DAY = 86400
READY = 'pc.get_level() >= 120 and pc.get_map_index() == %d' % DONGAN

# quest, npc, the soul (0 = Chaegirab's shard), the NPC's name in the texts, the mission names, the next quest
MISSIONS = [
    ('relikt_bron', 9001, 30255, 'Handlarz Bronią', 'Uratuj Handlarza Bronią', 'Dusza Miecza (powtarzalna)',
     'fragmentów duszy miecza', 'relikt_zbroja', None),
    ('relikt_zbroja', 9002, 30256, 'Handlarz Zbrojami', 'Uratuj Handlarza Zbrojami', 'Dusza Ochrony (powtarzalna)',
     'fragmentów duszy ochrony', 'relikt_alchemik', 'relikt_bron'),
    ('relikt_alchemik', 20001, 30258, 'Alchemik', 'Uratuj Alchemika', 'Dusza Światła (powtarzalna)',
     'fragmentów duszy światła', 'relikt_uriel', 'relikt_zbroja'),
    ('relikt_uriel', 20011, 30257, 'Uriel', 'Uratuj Uriela', 'Dusza Ozdoby (powtarzalna)',
     'fragmentów duszy ozdoby', 'relikt_chaegirab', 'relikt_alchemik'),
    ('relikt_chaegirab', 20810, 0, 'Chaegirab', 'Uratuj Chaegiraba', 'Relikt Duszy (powtarzalna)',
     'popiołów', None, 'relikt_uriel'),
]


def lua_s(s):
    assert '"' not in s
    if s and ord(s[-1]) >= 0x80:
        s += ' '    # qc: a string must not end with a Polish letter
    return '"%s"' % s


def quest_text(q, npc, soul, who, first, daily, frags, nxt, prev):
    chae = soul == 0
    reward = 'pc.give_item2(%d + pc.get_job(), 1)' % SHARD0 if chae else 'pc.give_item2(%d, 1)' % soul
    reward_vnum = '%d + pc.get_job()' % SHARD0 if chae else str(soul)
    head = [
        '-- %s: "%s" and "%s" - pl-wiki "Bonus Reliktu" (the owner, 29 October 2026). GENERATED by' % (M, first, daily),
        '-- tools/relikty/gen_relikty.py - do not edit, rerun it. cp1250; no string ends with a Polish letter (qc).',
        '-- %s in Dongan (%d, NPC %d), from level 120.' % (Y.ascii_name(who), DONGAN, npc),
        '--   First: Metin Swiadomosc (%d) on Dongan until the medicine (%d%% a Metin) - the wiki\'s mission Metin is' % (
            METIN_SWIADOMOSC, LEK_PCT),
        '--   this world\'s Metin Swiadomosc of the map%s; reward %s (100%%).' % (
            ', then 10 ashes of the monsters of Dongan (1 in %d)' % ASH_ONE_IN if chae else '',
            'the class\'s Odlamek Reliktu (%d+job)' % SHARD0 if chae else 'the soul %d' % soul),
        '--   Then every 24 h: %s' % (
            '10 ashes of the monsters of Dongan, %d%% a shard (the wiki: "wytworzenie moze sie nie udac").' % REPEAT_PCT
            if chae else '10 soul fragments of the monsters of Yohara (1 in %d), handed in; 24 h later %d%% the soul.'
            % (FRAG_ONE_IN, REPEAT_PCT)),
    ]
    if prev:
        head.append('-- Opened by %s (set_quest_state "run").' % prev)
    if nxt:
        head.append('-- Opens %s.' % nxt)
    T = []

    def w(line=''):
        # qc: a string must not end with a Polish letter - a space after it
        T.append(re.sub(r'"([^"]*[^\x00-\x7f])"', r'"\1 "', line))

    w('quest %s begin' % q)
    w('\tstate start begin')
    w('\t\tfunction on_yohara()')
    w('\t\t\tlocal idx = pc.get_map_index()')
    w('\t\t\tif idx >= 10000 then')
    w('\t\t\t\tidx = math.floor(idx / 10000)')
    w('\t\t\tend')
    w('\t\t\treturn table_is_in({ %s }, idx)' % ', '.join(map(str, YOHARA_MAPS)))
    w('\t\tend')
    w('')
    w('\t\tfunction ready()')
    w('\t\t\treturn pc.get_level() >= 120 and pc.get_map_index() == %d' % DONGAN)
    w('\t\tend')
    w('')
    w('\t\tfunction wait_text(left)')
    w('\t\t\tlocal h = math.floor(left / 3600)')
    w('\t\t\tlocal m = math.floor(math.mod(left, 3600) / 60)')
    w('\t\t\treturn string.format("%d godz. %d min", h, m)')
    w('\t\tend')
    w('')
    if prev is None:
        w('\t\twhen login or levelup with pc.get_level() >= 120 begin')
        w('\t\t\tset_state(information)')
        w('\t\tend')
    else:
        w('\t\t-- opened by %s' % prev)
    w('\tend')
    w('')
    # information: the letter to the NPC - "run" when the previous mission opened it (set_quest_state)
    w('\tstate %s begin' % ('information' if prev is None else 'run'))
    w('\t\twhen letter begin')
    w('\t\t\tlocal v = find_npc_by_vnum(%d)' % npc)
    w('\t\t\tif v ~= 0 and pc.get_map_index() == %d then' % DONGAN)
    w('\t\t\t\ttarget.vid("__TARGET__", v, mob_name(%d))' % npc)
    w('\t\t\tend')
    w('\t\t\tsend_letter(%s)' % lua_s(first))
    w('\t\tend')
    w('')
    w('\t\twhen button or info begin')
    w('\t\t\tsay_title(%s)' % lua_s(first))
    w('\t\t\tsay(%s)' % lua_s('%s w Dongan potrzebuje pomocy.' % who))
    w('\t\t\tsay("Porozmawiaj z nim (od poziomu 120).")')
    w('\t\tend')
    w('')
    w('\t\twhen __TARGET__.target.click or %d.chat.%s with %s begin' % (npc, lua_s(first), READY))
    w('\t\t\ttarget.delete("__TARGET__")')
    w('\t\t\tsay_title(mob_name(%d)..":")' % npc)
    w('\t\t\tsay("Ledwo trzymam się na nogach... Energia")')
    w('\t\t\tsay("Metinu Świadomość zatruła mnie i potrzebuję")')
    w('\t\t\tsay("lekarstwa. Pokonuj Metiny Świadomość w Dongan,")')
    w('\t\t\tsay("aż znajdziesz przy którymś z nich Lekarstwo.")')
    w('\t\t\tsay_reward("Nagroda:")')
    w('\t\t\tsay_item_vnum(%s)' % reward_vnum)
    w('\t\t\tpc.setqf("lek", 0)')
    w('\t\t\tset_state(medicine)')
    w('\t\tend')
    w('\tend')
    w('')
    # medicine
    w('\tstate medicine begin')
    w('\t\twhen letter begin')
    w('\t\t\tsend_letter(%s)' % lua_s(first))
    w('\t\tend')
    w('')
    w('\t\twhen button or info begin')
    w('\t\t\tsay_title(%s)' % lua_s(first))
    w('\t\t\tsay("Pokonuj Metiny Świadomość w Dongan, aż zdobędziesz")')
    w('\t\t\tsay(%s)' % lua_s('Lekarstwo. Zanieś je: %s.' % who))
    w('\t\tend')
    w('')
    w('\t\twhen kill with npc.get_race() == %d and pc.get_map_index() == %d begin' % (METIN_SWIADOMOSC, DONGAN))
    w('\t\t\tif number(1, 100) <= %d then' % LEK_PCT)
    w('\t\t\t\tpc.setqf("lek", 1)')
    w('\t\t\t\tsyschat("Znalazłeś Lekarstwo. Wróć do: %s.")' % who)
    w('\t\t\t\tset_state(medicine_back)')
    w('\t\t\tend')
    w('\t\tend')
    w('\tend')
    w('')
    w('\tstate medicine_back begin')
    w('\t\twhen letter begin')
    w('\t\t\tlocal v = find_npc_by_vnum(%d)' % npc)
    w('\t\t\tif v ~= 0 and pc.get_map_index() == %d then' % DONGAN)
    w('\t\t\t\ttarget.vid("__TARGET__", v, mob_name(%d))' % npc)
    w('\t\t\tend')
    w('\t\t\tsend_letter(%s)' % lua_s(first))
    w('\t\tend')
    w('')
    w('\t\twhen button or info begin')
    w('\t\t\tsay_title(%s)' % lua_s(first))
    w('\t\t\tsay(%s)' % lua_s('Masz Lekarstwo. Zanieś je: %s (Dongan).' % who))
    w('\t\tend')
    w('')
    w('\t\twhen __TARGET__.target.click or %d.chat."Lekarstwo" with pc.get_map_index() == %d begin' % (npc, DONGAN))
    w('\t\t\ttarget.delete("__TARGET__")')
    w('\t\t\tsay_title(mob_name(%d)..":")' % npc)
    if chae:
        w('\t\t\tsay("Dziękuję, już mi lepiej. Do uszlachetnienia")')
        w('\t\t\tsay("odłamka potrzebuję jeszcze 10 popiołów. Zbierz je")')
        w('\t\t\tsay("z potworów w Dongan.")')
        w('\t\t\tpc.setqf("ash", 0)')
        w('\t\t\tset_state(ashes)')
        w('\t\tend')
        w('\tend')
        w('')
        w('\tstate ashes begin')
        w('\t\twhen letter begin')
        w('\t\t\tsend_letter(%s)' % lua_s(first))
        w('\t\tend')
        w('')
        w('\t\twhen button or info begin')
        w('\t\t\tsay_title(%s)' % lua_s(first))
        w('\t\t\tsay("Zbierz 10 popiołów z potworów w Dongan.")')
        w('\t\t\tsay_reward(string.format("Zebrane: %d / 10", pc.getqf("ash")))')
        w('\t\tend')
        w('')
        w('\t\twhen kill with not npc.is_pc() and pc.get_map_index() == %d begin' % DONGAN)
        w('\t\t\tlocal r = npc.get_race()')
        w('\t\t\tif r >= 8000 and r < 9000 then')
        w('\t\t\t\treturn')
        w('\t\t\tend')
        w('\t\t\tif pc.getqf("ash") < 10 and number(1, %d) == 1 then' % ASH_ONE_IN)
        w('\t\t\t\tpc.setqf("ash", pc.getqf("ash") + 1)')
        w('\t\t\t\tsyschat(string.format("Popiół: %d / 10", pc.getqf("ash")))')
        w('\t\t\tend')
        w('\t\tend')
        w('')
        w('\t\twhen %d.chat."Popioły" with pc.getqf("ash") >= 10 begin' % npc)
        w('\t\t\tsay_title(mob_name(%d)..":")' % npc)
    w('\t\t\tsay("Dziękuję za pomoc. Weź to w nagrodę.")')
    w('\t\t\tsay_item_vnum(%s)' % reward_vnum)
    w('\t\t\t%s' % reward)
    w('\t\t\tpc.setqf("last", 0)')
    w('\t\t\tpc.setqf("count", 0)')
    if nxt:
        w('\t\t\tset_quest_state("%s", "run")' % nxt)
    w('\t\t\tclear_letter()')
    w('\t\t\tset_state(daily)')
    w('\t\tend')
    w('\tend')
    w('')
    # daily: start
    w('\tstate daily begin')
    w('\t\twhen %d.chat.%s with %s begin' % (npc, lua_s(daily), READY))
    w('\t\t\tsay_title(mob_name(%d)..":")' % npc)
    w('\t\t\tlocal left = pc.getqf("last") + %d - get_time()' % DAY)
    w('\t\t\tif left > 0 then')
    w('\t\t\t\tsay("Wróć do mnie później. Następna próba za:")')
    w('\t\t\t\tsay_reward(%s.wait_text(left))' % q)
    w('\t\t\t\treturn')
    w('\t\t\tend')
    if chae:
        w('\t\t\tsay("Przynieś mi 10 popiołów z potworów w Dongan,")')
        w('\t\t\tsay("a spróbuję wytworzyć Odłamek Reliktu.")')
        w('\t\t\tsay("Nie zawsze się to udaje.")')
    else:
        w('\t\t\tsay(%s)' % lua_s('Przynieś mi 10 %s.' % frags))
        w('\t\t\tsay("Znajdziesz je u potworów na nowym kontynencie.")')
        w('\t\t\tsay("Zbadam je przez dobę - wytworzenie duszy")')
        w('\t\t\tsay("może się nie udać.")')
    w('\t\t\tpc.setqf("count", 0)')
    w('\t\t\tset_state(daily_collect)')
    w('\t\tend')
    w('\tend')
    w('')
    # daily: collect
    w('\tstate daily_collect begin')
    w('\t\twhen letter begin')
    w('\t\t\tsend_letter(%s)' % lua_s(daily))
    w('\t\tend')
    w('')
    w('\t\twhen button or info begin')
    w('\t\t\tsay_title(%s)' % lua_s(daily))
    w('\t\t\tsay(%s)' % lua_s('Zbierz 10 %s.' % frags))
    w('\t\t\tsay_reward(string.format("Zebrane: %d / 10", pc.getqf("count")))')
    w('\t\tend')
    w('')
    if chae:
        w('\t\twhen kill with not npc.is_pc() and pc.get_map_index() == %d begin' % DONGAN)
        one_in = ASH_ONE_IN
        drop_word = 'Popiół'
    else:
        w('\t\twhen kill with not npc.is_pc() begin')
        one_in = FRAG_ONE_IN
        drop_word = 'Fragment duszy'
    w('\t\t\tlocal r = npc.get_race()')
    if not chae:
        w('\t\t\tif not %s.on_yohara() then' % q)
        w('\t\t\t\treturn')
        w('\t\t\tend')
    w('\t\t\tif r >= 8000 and r < 9000 then')
    w('\t\t\t\treturn')
    w('\t\t\tend')
    w('\t\t\tif pc.getqf("count") < 10 and number(1, %d) == 1 then' % one_in)
    w('\t\t\t\tpc.setqf("count", pc.getqf("count") + 1)')
    w('\t\t\t\tsyschat(string.format("%s: %%d / 10", pc.getqf("count")))' % drop_word)
    w('\t\t\tend')
    w('\t\tend')
    w('')
    hand = 'Oddaj popioły' if chae else 'Oddaj fragmenty duszy'
    w('\t\twhen %d.chat.%s with pc.getqf("count") >= 10 begin' % (npc, lua_s(hand)))
    w('\t\t\tsay_title(mob_name(%d)..":")' % npc)
    w('\t\t\tpc.setqf("count", 0)')
    if chae:
        w('\t\t\tpc.setqf("last", get_time())')
        w('\t\t\tset_state(daily)')
        w('\t\t\tif number(1, 100) > %d then' % REPEAT_PCT)
        w('\t\t\t\tsay("Niestety, tym razem się nie udało. Spróbuj")')
        w('\t\t\t\tsay("ponownie jutro.")')
        w('\t\t\t\treturn')
        w('\t\t\tend')
        w('\t\t\tsay("Udało się! Oto Odłamek Reliktu twojej klasy.")')
        w('\t\t\tsay_item_vnum(%s)' % reward_vnum)
        w('\t\t\t%s' % reward)
        w('\t\tend')
        w('\tend')
    else:
        w('\t\t\tpc.setqf("given", get_time())')
        w('\t\t\tsay("Dobrze, zbadam je. Wróć po wynik za dobę.")')
        w('\t\t\tset_state(daily_wait)')
        w('\t\tend')
        w('\tend')
        w('')
        w('\tstate daily_wait begin')
        w('\t\twhen letter begin')
        w('\t\t\tsend_letter(%s)' % lua_s(daily))
        # MT2009_PLUS_SPIRALA_CZASU_V2: the research's clock in the letter (as the Biologist's) - Spirala Czasu
        # sets it again (q.set_clock_of) the moment it cuts the wait
        w('\t\t\tlocal left = pc.getqf("given") + %d - get_time()' % DAY)
        w('\t\t\tif left > 0 then')
        w('\t\t\t\tq.set_clock("Pozostało", left)')
        w('\t\t\tend')
        w('\t\tend')
        w('')
        w('\t\twhen button or info begin')
        w('\t\t\tsay_title(%s)' % lua_s(daily))
        w('\t\t\tlocal left = pc.getqf("given") + %d - get_time()' % DAY)
        w('\t\t\tif left > 0 then')
        w('\t\t\t\tsay("Wynik badań będzie gotowy za:")')
        w('\t\t\t\tsay_reward(%s.wait_text(left))' % q)
        w('\t\t\telse')
        w('\t\t\t\tsay(%s)' % lua_s('Wynik badań jest gotowy. Wróć: %s.' % who))
        w('\t\t\tend')
        w('\t\tend')
        w('')
        w('\t\twhen %d.chat."Wynik badań" with pc.get_map_index() == %d begin'
          % (npc, DONGAN))
        w('\t\t\tsay_title(mob_name(%d)..":")' % npc)
        w('\t\t\tlocal left = pc.getqf("given") + %d - get_time()' % DAY)
        w('\t\t\tif left > 0 then')
        w('\t\t\t\tsay("Jeszcze nie skończyłem. Wróć za:")')
        w('\t\t\t\tsay_reward(%s.wait_text(left))' % q)
        w('\t\t\t\treturn')
        w('\t\t\tend')
        w('\t\t\tpc.setqf("last", get_time() - %d)' % DAY)
        w('\t\t\tset_state(daily)')
        w('\t\t\tif number(1, 100) > %d then' % REPEAT_PCT)
        w('\t\t\t\tsay("Niestety, z tych fragmentów nie udało się")')
        w('\t\t\t\tsay("wytworzyć duszy. Spróbuj ponownie.")')
        w('\t\t\t\treturn')
        w('\t\t\tend')
        w('\t\t\tsay("Udało się! Weź tę duszę.")')
        w('\t\t\tsay_item_vnum(%s)' % reward_vnum)
        w('\t\t\t%s' % reward)
        w('\t\tend')
        w('\tend')
    w('end')
    text = '\n'.join(head + T) + '\n'
    # qc: no string ends with a Polish letter (the lexer of qc eats the closing quote after a byte >= 0x80)
    for line in text.split('\n'):
        if line.startswith('--'):
            continue
        i = 0
        while True:
            a = line.find('"', i)
            if a < 0:
                break
            b = line.find('"', a + 1)
            assert b > a, (q, line)
            s = line[a + 1:b]
            assert not s or ord(s[-1]) < 0x80, (q, line)
            i = b + 1
    return text


def craft_quest_text():
    """relikt_uszlachetnianie: Chaegirab (Dongan, 20810) makes a Relikt Duszy of a shard of the class, any time
    (pl-wiki "Bonus Reliktu": "zamieniamy na Relikt Duszy korzystajac z okienka uszlachetnienia")."""
    q, npc = "relikt_uszlachetnianie", 20810
    T = []

    def w(line=''):
        T.append(re.sub(r'"([^"]*[^\x00-\x7f])"', r'"\1 "', line))

    w('-- %s: Chaegirab (Dongan, 20810) makes the class\'s Relikt Duszy (%d+job) of its Odlamek Reliktu' % (M, RELIC0))
    w('-- (%d+job), at any time, 100%% - pl-wiki "Bonus Reliktu" ("okienko uszlachetnienia"). GENERATED by' % SHARD0)
    w('-- tools/relikty/gen_relikty.py - do not edit, rerun it. cp1250.')
    w('quest %s begin' % q)
    w('\tstate start begin')
    w('\t\tfunction craft()')
    w('\t\t\tlocal shard = %d + pc.get_job()' % SHARD0)
    w('\t\t\tsay_title(mob_name(%d)..":")' % npc)
    w('\t\t\tif pc.count_item(shard) < 1 then')
    w('\t\t\t\tsay("Nie masz przy sobie Odłamka Reliktu swojej klasy.")')
    w('\t\t\t\treturn')
    w('\t\t\tend')
    w('\t\t\tsay("Z tego odłamka mogę uszlachetnić Relikt Duszy")')
    w('\t\t\tsay("dla twojej klasy. Uda się na pewno.")')
    w('\t\t\tsay_item_vnum(%d + pc.get_job())' % RELIC0)
    w('\t\t\tif select("Uszlachetnij", "Anuluj") ~= 1 then')
    w('\t\t\t\treturn')
    w('\t\t\tend')
    w('\t\t\tif pc.count_item(shard) < 1 then')
    w('\t\t\t\treturn')
    w('\t\t\tend')
    w('\t\t\tpc.remove_item(shard, 1)')
    w('\t\t\tpc.give_item2(%d + pc.get_job(), 1)' % RELIC0)
    w('\t\t\tsay_title(mob_name(%d)..":")' % npc)
    w('\t\t\tsay("Gotowe. Umieść Relikt w oknie Bonusu Reliktu")')
    w('\t\t\tsay("(prawy klik na relikt) i dodaj mu bonusy duszami.")')
    w('\t\tend')
    w('')
    w('\t\twhen %d.chat."Uszlachetnij Odłamek Reliktu" with pc.count_item(%d + pc.get_job()) > 0 begin' % (npc, SHARD0))
    w('\t\t\t%s.craft()' % q)
    w('\t\tend')
    w('\tend')
    w('end')
    return '\n'.join(T) + '\n'

def write_quests():
    out = []
    for m in MISSIONS:
        t = quest_text(*m)
        for bad in ('Metin2', 'Gameforge', 'oficjaln'):
            assert bad.lower() not in t.lower(), (m[0], bad)
        p = os.path.join(QUEST_DIR, m[0] + '.quest')
        with open(p, 'wb') as f:
            f.write(t.encode('cp1250'))
        out.append(m[0])
    t = craft_quest_text()
    with open(os.path.join(QUEST_DIR, 'relikt_uszlachetnianie.quest'), 'wb') as f:
        f.write(t.encode('cp1250'))
    out.append('relikt_uszlachetnianie')
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--gf', default='/opt/metin2/cache/gf/Gameforge_26.1.11/_client')
    ap.add_argument('--png-python', default='')
    a = ap.parse_args()
    check_gf_list(a.gf)
    its = items()
    write_sql(its)
    write_sig()
    write_json(its)
    write_header()
    write_client_py()
    qs = write_quests()
    copy_icons(a.gf)
    png = write_pngs(a.gf, a.png_python)
    print('items %d, bonuses %d, quests %s, icons %d, shop pictures: %s'
          % (len(its), len(BONUSES), ' '.join(qs), len(icon_vnums()), png))


if __name__ == '__main__':
    main()
