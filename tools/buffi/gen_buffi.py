#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_buffi.py [--ameria DIR]

MT2009_PLUS_BUFFI_V1: the data of Buffi, the support shaman of Ameria Project (server-patches/buffi/README.md;
the owner, 21 October 2026: "W zamian za towarzysza dodaj system buffi z Amerii"). Ameria's vnums, flags, limits and
numbers (serverfiles home share/conf/item_proto.txt, mysql player.sql skill_proto 164-167 and ishop_data, the quest
__buffi__), Polish names and texts (Ameria's "pl" locale is English):

  61025 Buffi (7 dni)            the seal, 7 days real time, bound (Ameria's starter chest; here V1's starter gift of
                                 a new character - MT2009_PLUS_BUFFI_V3: no source any more, the gift of level 55 is
                                 61026 + 61030, quest buffi)
  61026 Buffi                    the seal, for good, tradeable (Ameria's ItemShop: 750)
  61030 Zwoj Imienia Buffi       the name: Szybkosc and Zwiekszenie Ataku, +10% against bosses for 7 days (ItemShop 50)
  61031 Kamien Duchowy Buffi     G1 -> P of a buffi skill (quest buffi); MT2009_PLUS_BUFFI_V2: drops from Metins
                                 and bosses from Zaklety Las up (tools/ymoby_arkusz/gen_buffi_stone.py)
  61035-61038 the books          M1 -> G1 of Blogoslawienstwo / Pomoc Smoka / Szybkosc / Zwiekszenie Ataku Buffi
                                 (the engine's book reading). MT2009_PLUS_BUFFI_V2: withdrawn - no source any more
                                 (the owner: M1 -> G1 with the shaman's own skill books in the Buffi window); the rows
                                 stay so that a book still owned does not vanish, and it still reads
  skill_proto 164-167            Ameria's rows - the engine's book and soul stone paths want them; the buffs
                                 themselves are computed by playerbot_buffi.cpp with the same polys
  mob_proto 65000                the shaman - an NPC (a copy of the pet 34001's row); the clients see a female shaman
                                 (playerbot_buffi.cpp, BuffiInsertLook)

MT2009_PLUS_BUFFI_V3 (the owner's list of 22 October 2026): weaker buffs - the value (not the time) of every buff
M1-M10 -50%, G1-G4 -35%, G5-G10 -25%, P -18%. The server applies it where the value is made (playerbot_buffi.cpp,
GradeFactor - the skill_proto rows below are not read for it and stay Ameria's); the client's tooltip polys here get
the same factor (CLIENT_FACTOR, by the real skill level "sl" the tooltip passes). Buffi from level 55: the seals' text.

Every vnum was free in our world (21 October 2026). The engine's numbers: tools/yohara_items/gen_yitems.py.

Writes (all GENERATED - edit this file, run it again):
  linux-port/docker/mariadb/playerbot/buffi.sql             items, skills, the mob, the name table, the ItemShop offers
  tools/buffi/buffi.json                                    the client's records, item_list, itemdesc and
                                                            (MT2009_PLUS_BUFFI_V2) the skills' skilldesc / skilltable
                                                            lines (164-167: names, icons, the tooltip's polys)
  client-patches/client-2.0.30/root/icon/item/<icon>.tga    Ameria's icons

Example: python3 tools/buffi/gen_buffi.py
"""
import argparse
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, 'tools', 'yohara_items'))
import gen_yitems as Y  # noqa: E402  (the engine's numbers, the row writer)

SQL_OUT = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot', 'buffi.sql')
JSON_OUT = os.path.join(HERE, 'buffi.json')
ICON_OUT = os.path.join(REPO, 'client-patches', 'client-2.0.30', 'root', 'icon', 'item')

ITEM_USE, USE_SPECIAL, ITEM_SKILLBOOK, ITEM_QUEST = 3, 10, 17, 18
STACKABLE = 4
LIMIT_REAL_TIME = 7
SEAL_ANTI = ('ANTI_STACK', 'ANTI_SELL', 'ANTI_PKDROP', 'ANTI_DROP', 'ANTI_GIVE', 'ANTI_MYSHOP')   # Ameria's 61025
MOB, MOB_TEMPLATE = 65000, 34001
BOOK_ICON = 'buffi_book.tga'    # Ameria's 50322.tga - our 50322 is Rola Transformacyjna, so a name of its own

SKILLS = (  # vnum, szName, Polish, point, poly, sp, duration, flag, point2, poly2, duration2
    (164, 'BUFFI_HOSIN', u'Błogosławieństwo', 'RESIST_NORMAL', '(226*0.2+5)*(2*k+0.5)/(k+1.5)', '40+160*k', '3600', 'HOSIN',
     'NONE', '', ''),
    (165, 'BUFFI_GICHEON', u'Pomoc Smoka', 'CRITICAL', '(226*0.2+5)*(2*k+0.5)/(k+1.5)', '40+160*k', '3600', 'GICHEON',
     'NONE', '', ''),
    (166, 'BUFFI_KWAESOK', u'Szybkość', 'MOV_SPEED', '5 + 35*k', '60+100*k', '3600', 'KWAESOK',
     'CASTING_SPEED', '3+33*k', '60+100*k'),
    (167, 'BUFFI_JEUNGRYEOK', u'Zwiększenie Ataku', 'ATT_GRADE', '5+(226*0.2 +15)*k', '60+150*k', '3600', 'JEUNGRYEOK',
     'NONE', '', ''),
)
NAMED_ONLY = (166, 167)

BUFFI_TEXT = (u'Przywołuje Buffi - szamankę, która chodzi za tobą i co 3 sekundy rzuca na ciebie brakujące '
              u'wzmocnienie: Błogosławieństwo i Pomoc Smoka, a gdy ma imię (Zwój Imienia Buffi) także Szybkość '
              u'i Zwiększenie Ataku. Użyj ponownie, aby ją odwołać. Okno Buffi: klawisz P. '
              u'Buffi dostępna od 55 poziomu postaci.')  # MT2009_PLUS_BUFFI_V3: from level 55


def base(vnum, src, locale_name, typ, subtype, desc, icon, **over):
    i = dict(vnum=vnum, src=src, status=Y.ST, name=Y.ascii_name(locale_name), locale_name=locale_name, type=typ,
             subtype=subtype, stack=1, weight=0, size=1, antiflag=0, flag=0, wearflag=0, gold=0, shop_buy_price=0,
             refined_vnum=0, refine_set=0, magic_pct=0, specular=0, socket_pct=0, addon_type=0, limittype0=0,
             limitvalue0=0, limittype1=0, limitvalue1=0, applytype0=0, applyvalue0=0, applytype1=0, applyvalue1=0,
             applytype2=0, applyvalue2=0, value0=0, value1=0, value2=0, value3=0, value4=0, value5=0, desc=desc,
             icon='icon/item/%s' % icon, list_type='ETC')
    i.update(over)
    return i


def items():
    anti = sum(Y.ANTI[a] for a in SEAL_ANTI)
    out = [
        base(61025, 61025, u'Buffi (7 dni)', ITEM_USE, USE_SPECIAL, BUFFI_TEXT + u' Ważna 7 dni.', '61025.tga',
             antiflag=anti, limittype0=LIMIT_REAL_TIME, limitvalue0=7 * 24 * 3600),
        base(61026, 61026, u'Buffi', ITEM_USE, USE_SPECIAL, BUFFI_TEXT, '61026.tga'),
        base(61030, 61030, u'Zwój Imienia Buffi', ITEM_USE, USE_SPECIAL,
             u'Nadaje imię przywołanej Buffi (imię zostaje przy jej pieczęci). Buffi z imieniem rzuca też Szybkość '
             u'i Zwiększenie Ataku, a ty dostajesz +10% silny przeciwko bossom na 7 dni. Nowe imię - dopiero gdy '
             u'ten bonus minie.', '61030.tga'),
        base(61031, 61031, u'Kamień Duchowy Buffi', ITEM_QUEST, 0,
             u'Trenuje umiejętność Buffi od stopnia G1 do P, jak Kamień Duchowy zwykłe umiejętności (punkty rangi, '
             u'następna próba po 12 godzinach, Zwój Egzorcyzmu od razu). Wypada z Metinów i bossów od Zaklętego '
             u'Lasu wzwyż.', '61031.tga', stack=200, flag=STACKABLE),
    ]
    for n, (vnum, sname, pl, *_rest) in enumerate(SKILLS):
        extra = u' Działa, gdy Buffi ma imię.' if vnum in NAMED_ONLY else u''
        # MT2009_PLUS_BUFFI_V2: withdrawn (no source); one still owned reads as before
        out.append(base(61035 + n, 61035 + n, u'Księga Buffi: %s' % pl, ITEM_SKILLBOOK, 0,
                        u'Księga wycofana - nie można jej już zdobyć. Uczy umiejętności Buffi "%s" od stopnia M1 '
                        u'do G1.%s Teraz do G1 służą zwykłe Księgi Umiejętności szamana przeciągnięte w oknie Buffi '
                        u'(klawisz P) na jej umiejętność.' % (pl, extra), BOOK_ICON,
                        stack=200, flag=STACKABLE, value0=vnum))
    return out


def write_sql(its):
    L = ['-- MT2009_PLUS_BUFFI_V1: Buffi, the support shaman of Ameria Project (server-patches/buffi/README.md; the owner,',
         '-- 21 October 2026). GENERATED by tools/buffi/gen_buffi.py - do not edit, rerun it. Every start (apply.sh), idempotent:',
         '-- INSERT IGNORE - a row the operator changed is kept. Ameria\'s vnums and numbers; each vnum was free here.',
         'SET NAMES utf8mb4;',
         '-- the seals, the name scroll, the soul stone and the four books',
         'INSERT IGNORE INTO world.item_proto (%s) VALUES' % ','.join('`%s`' % c for c in Y.COLS),
         ',\n'.join(Y.sqlrow(i) for i in its) + ';',
         '-- the skills 164-167 (Ameria\'s skill_proto rows; the buffs come from playerbot_buffi.cpp with these polys)',
         'INSERT IGNORE INTO world.skill_proto (dwVnum, szName, bType, bLevelStep, bMaxLevel, bLevelLimit, szPointOn, '
         'szPointPoly, szSPCostPoly, szDurationPoly, szDurationSPCostPoly, szCooldownPoly, szMasterBonusPoly, '
         'szAttackGradePoly, setFlag, setAffectFlag, szPointOn2, szPointPoly2, szDurationPoly2, setAffectFlag2, szPointOn3, '
         'szPointPoly3, szDurationPoly3, setAffectFlag3, szGrandMasterAddSPCostPoly, prerequisiteSkillVnum, '
         'prerequisiteSkillLevel, eSkillType, iMaxHit, szSplashAroundDamageAdjustPoly, dwTargetRange, dwSplashRange) VALUES']
    rows = []
    for vnum, sname, pl, point, poly, sp, dur, flag, point2, poly2, dur2 in SKILLS:
        master = poly.replace('226*0.2+5', '226*0.3+5')     # Ameria's szMasterBonusPoly (0.3 where the point has 0.2)
        rows.append("  (%d, '%s', 4, 1, 40, 20, '%s', '%s', '%s', '%s', '', '10', '%s', '', '', '%s', '%s', '%s', '%s', "
                    "'NONE', 'NONE', '', '', 'NONE', '%s', 0, 0, 'NORMAL', 1, '1', 1000, 0)"
                    % (vnum, sname, point, poly, sp, dur, master, flag, point2, poly2, dur2, sp))
    L.append(',\n'.join(rows) + ';')
    L += ['-- the shaman: an NPC with no AI of its own (a pet\'s row, 34001, under its own vnum and name)',
          'DROP TEMPORARY TABLE IF EXISTS world.mt2009_buffi_mob;',
          'CREATE TEMPORARY TABLE world.mt2009_buffi_mob AS SELECT * FROM world.mob_proto WHERE vnum = %d;' % MOB_TEMPLATE,
          "UPDATE world.mt2009_buffi_mob SET vnum = %d, name = 'buffi', locale_name = 'Buffi', type = 1, `rank` = 0, level = 1, "
          "folder = 'phoenix1', on_click = 0, move_speed = 200, attack_speed = 100, empire = 0;" % MOB,
          'INSERT IGNORE INTO world.mob_proto SELECT * FROM world.mt2009_buffi_mob;',
          # MT2009_PLUS_BUFFI_V1 (folder): the server reads the walk timing from data/monster/<folder>/motlist.txt - there
          # is no 'buffi' folder, so the pet's (the client draws a shaman anyway)
          "UPDATE world.mob_proto SET folder = 'phoenix1' WHERE vnum = %d AND folder = 'buffi';" % MOB,
          'DROP TEMPORARY TABLE IF EXISTS world.mt2009_buffi_mob;',
          '-- a buffi\'s name, a name per seal (Ameria: share/buffi_name/<item id>; the core makes it too)',
          'CREATE TABLE IF NOT EXISTS player.mt2009_buffi_name (item_id INT UNSIGNED NOT NULL PRIMARY KEY, '
          'owner_pid INT UNSIGNED NOT NULL DEFAULT 0, name VARCHAR(24) NOT NULL DEFAULT \'\', named_at DATETIME NOT NULL) '
          'ENGINE=InnoDB;']
    with open(SQL_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')


ITEMSHOP_OUT = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot', 'buffi_itemshop.sql')
OFFERS = (  # id, vnum, price (Ameria's ishop_data, COINS), text
    (1061026, 61026, 750, u'Buffi na zawsze: szamanka chodzi za tobą i rzuca Błogosławieństwo i Pomoc Smoka (z imieniem '
                          u'także Szybkość i Zwiększenie Ataku). Klawisz P.'),
    (1061030, 61030, 50, u'Imię dla Buffi: odblokowuje Szybkość i Zwiększenie Ataku, +10% silny przeciwko bossom na 7 dni.'),
)


def write_itemshop(its):
    names = dict((i['vnum'], i['locale_name']) for i in its)
    L = ['-- MT2009_PLUS_BUFFI_V1: the ItemShop\'s Buffi offers (category 3 "Kon i pomoc"; Ameria\'s prices in its coins).',
         '-- GENERATED by tools/buffi/gen_buffi.py. Once: an offer of the vnum already there (the operator\'s price) stays;',
         '-- a removed one comes back on the next start.',
         'SET NAMES utf8mb4;']
    for oid, vnum, price, text in OFFERS:
        L.append("INSERT IGNORE INTO itemshop.ishop_items (id, category, name_item, `desc`, price, currency, vnum, count, "
                 "socket0, socket1, socket2, vnum_icon, date_added)\nSELECT %d, 3, '%s', '%s', %d, 'cash', %d, 1, 0, 0, 0, "
                 "'%d', NOW() FROM DUAL WHERE EXISTS (SELECT 1 FROM world.item_proto WHERE vnum = %d) AND NOT EXISTS "
                 "(SELECT 1 FROM itemshop.ishop_items WHERE vnum = %d);"
                 % (oid, names[vnum], text, price, vnum, vnum, vnum, vnum))
    with open(ITEMSHOP_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')


# MT2009_PLUS_BUFFI_V3 (weaker): the server's GradeFactor (playerbot_buffi.cpp) as a client poly - the tooltip
# (uitooltip.py AppendSkillLevelDescriptionNew) evaluates skilldesc's polys with "sl" = the real skill level and the
# skilltable's point poly overwrites the first one (PythonSkill.cpp OVERWRITE_SKILLPROTO_POLY): M1-M10 0.5, G1-G4 0.65,
# G5-G10 0.75, P 0.82. The texts are "%.0f" - the client floors, as the server's (long) does.
CLIENT_FACTOR = '(0.5*(isgraden+isgradem)+isgradeg*(0.65+0.1*min(1,max(0,sl-33)))+0.82*isgradep)'


def client_poly(poly):
    return '(%s)*%s' % (poly, CLIENT_FACTOR) if poly else poly


def factor(level):
    """The server's GradeFactor (a check of CLIENT_FACTOR)."""
    return 0.82 if level >= 40 else 0.75 if level >= 34 else 0.65 if level >= 30 else 0.5


# MT2009_PLUS_BUFFI_V2: the client's skill data of the buffi skills (locale/pl/skilldesc.txt and
# gamedata/skilltable.txt of the dbdata pack - names, the shaman's icons and motions, the tooltip's polys with
# Ameria's iq 226 as playerbot_buffi.cpp casts them). 28 / 27 columns as the client's shaman lines 94/96/110/111.
SKILLDESC = (  # vnum, names, description, affect texts and polys
    (164, u'Błogosławieństwo Buffi', u'Buffi otacza cię kręgiem ochronnym. Trenuj: zwykłe Księgi Umiejętności '
          u'szamana w oknie Buffi (do G1), Kamień Duchowy Buffi (do P).', u'Odporność na fizyczne obrażenia',
     u'', 'hosin', '4', [u'Odporność Na Ataki Fizyczne %.0f%%', u'(226*0.2+5)*(2*k+0.5)/(k+1.5)']),
    (165, u'Pomoc Smoka Buffi', u'Buffi zwiększa twoją szansę na cios krytyczny. Trenuj: zwykłe Księgi '
          u'Umiejętności szamana w oknie Buffi (do G1), Kamień Duchowy Buffi (do P).',
     u'Zwiększa szansę na krytyczne uderzenie', u'', 'gicheon', '6',
     [u'Szansa na cios krytyczny: +%.0f%%', u'(226*0.2+5)*(2*k+0.5)/(k+1.5)']),
    (166, u'Szybkość Buffi', u'Buffi przyspiesza twój ruch. Wymaga imienia Buffi. Trenuj: zwykłe Księgi '
          u'Umiejętności szamana w oknie Buffi (do G1), Kamień Duchowy Buffi (do P).', u'Zwiększa Szybkość Ruchu',
     u'Zmniejsza się Czas Ładowania Umiejętności', 'kwaesok', '20',
     [u'Szybkość Ruchu +%.0f%%', u'5 + 35*k', u'', u'Czas Ładowania -%.0f%%', u'3+33*k']),
    (167, u'Zwiększenie Ataku Buffi', u'Buffi wzmacnia twój atak. Wymaga imienia Buffi. Trenuj: zwykłe Księgi '
          u'Umiejętności szamana w oknie Buffi (do G1), Kamień Duchowy Buffi (do P).', u'Zwiększa Siłę Ataku', u'',
     'jeungryeok', '21', [u'Siła Ataku: +%.0f', u'5+(226*0.2+15)*k']),
)


def skilldesc_lines():
    out = {}
    for vnum, name, desc, aff1, aff2, icon, motion, polys in SKILLDESC:
        # MT2009_PLUS_BUFFI_V3: every affect's min poly (text, min, max) times the grade's factor
        polys = [client_poly(p) if n % 3 == 1 else p for n, p in enumerate(polys)]
        cols = [str(vnum), 'SHAMAN', name, name, name, desc, aff1, aff2, u'', u'', u'', u'', icon, motion, '4', u'',
                u''] + polys
        cols += [u''] * (28 - len(cols))
        assert len(cols) == 28, vnum
        out[str(vnum)] = u'\t'.join(cols)
    return out


def skilltable_lines():
    # the client's own shaman rows (94/96/110/111) with the buffi's vnum, name and polys
    out = {}
    for vnum, sname, pl, point, poly, sp, dur, flag, point2, poly2, dur2 in SKILLS:
        # MT2009_PLUS_BUFFI_V3: the point polys times the grade's factor (this one overwrites the tooltip's first)
        cp, cp2 = client_poly(poly), client_poly(poly2)
        # (and the time the server gives - 3600 s, Ameria's szDurationPoly - in place of the shaman's 60+100*k)
        cols = [str(vnum), sname, '4', '1', '1', '0', point, cp, sp, dur, '', '2', cp, '', '', flag,
                point2 or 'NONE', cp2, dur2, 'NONE', '0', '0', 'NORMAL', '1', '1', '1000', '0']
        assert len(cols) == 27, vnum
        out[str(vnum)] = '\t'.join(cols)
    return out


def write_json(its):
    keys = ('vnum', 'name', 'locale_name', 'type', 'subtype', 'stack', 'weight', 'size', 'antiflag', 'flag',
            'wearflag', 'gold', 'shop_buy_price', 'refined_vnum', 'refine_set', 'magic_pct', 'specular', 'socket_pct',
            'limittype0', 'limitvalue0', 'limittype1', 'limitvalue1', 'applytype0', 'applyvalue0', 'applytype1',
            'applyvalue1', 'applytype2', 'applyvalue2', 'value0', 'value1', 'value2', 'value3', 'value4', 'value5')
    out = {'items': [dict((k, i[k]) for k in keys) for i in its],
           'item_list': dict((str(i['vnum']), '%d\t%s\t%s' % (i['vnum'], i['list_type'], i['icon'])) for i in its),
           'itemdesc': dict((str(i['vnum']), '%d\t%s\t%s' % (i['vnum'], i['locale_name'], Y.client_desc(i)))
                            for i in its),
           'skilldesc': skilldesc_lines(),
           'skilltable': skilltable_lines()}
    with open(JSON_OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=0)
        f.write('\n')


def copy_icons(ameria):
    src = os.path.join(ameria, 'tools', 'FoxFSArchiver', 'source', 'icon', 'item')
    os.makedirs(ICON_OUT, exist_ok=True)
    for dst, name in (('61025.tga', '61025.tga'), ('61026.tga', '61026.tga'), ('61030.tga', '61030.tga'),
                      ('61031.tga', '61031.tga'), (BOOK_ICON, '50322.tga')):
        s = os.path.join(src, name)
        assert os.path.isfile(s), s
        shutil.copyfile(s, os.path.join(ICON_OUT, dst))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ameria', default='/opt/metin2/ameria/ameria-prj-2025')
    a = ap.parse_args()
    its = items()
    for i in its:
        for bad in ('Metin2', 'Gameforge', 'oficjaln'):
            assert bad.lower() not in (i['locale_name'] + i['desc']).lower(), i['vnum']
    write_sql(its)
    write_itemshop(its)
    write_json(its)
    copy_icons(a.ameria)
    print('items %d, skills %d, mob %d, offers %d' % (len(its), len(SKILLS), MOB, len(OFFERS)))


if __name__ == '__main__':
    main()
