#!/usr/bin/env python3
"""gen_addeq.py - MT2009_PLUS_ADDEQ_V1 (Druga strona ekwipunku, server-patches/addeq/README.md): the unlock items of
the "Official Additional Equipment Page" package (its 2. Server/item_proto.txt, item_names.txt; the vnums and flags of
the GF 26.1.11 client), with our Polish names. Writes

  tools/addeq/addeq.json                              - the items, item_list / itemdesc lines and the skill 200's
                                                        client rows (client-patches/client-2.0.30/tools/addeq reads it)
  linux-port/docker/mariadb/playerbot/addeq.sql       - world.item_proto (apply.sh, idempotent: INSERT IGNORE)

The skill 200 "Zmiana strony ekwipunku" needs no skill_proto row: the engine takes it before any proto lookup
(CHARACTER::UseSkill -> Mt2009AddeqUseSkill), it cannot be levelled (DISABLE_BY_POINT_UP on the client's row) and the
unlock item sets its level. Run again after a change; a second run writes the same bytes."""
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..'))
SQL = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot', 'addeq.sql')
JSON = os.path.join(HERE, 'addeq.json')

ITEM_USE, USE_SPECIAL = 3, 10
ANTI_DROP, ANTI_GIVE, ANTI_PKDROP, ANTI_MYSHOP, ANTI_SAFEBOX = 1 << 7, 1 << 13, 1 << 14, 1 << 16, 1 << 17
FLAG_STACKABLE, FLAG_CONFIRM_WHEN_USE = 1 << 2, 1 << 9

DESC = (u'Odblokowuje drugą stronę ekwipunku: dwa zestawy przedmiotów (zbroja, hełm, buty, '
        u'bransoleta, broń, naszyjnik, kolczyki, strzały, tarcza, talizman, rękawice) zmieniane jednym '
        u'kliknięciem - zakładki I / II w oknie ekwipunku albo umiejętność '
        u'„Zmiana strony ekwipunku” (umiejętności pomocnicze). Bonusy daje tylko założona '
        u'strona; pierścienie, kostiumy i pas są wspólne. Raz na postać.')

ITEMS = [
    # vnum, English name (the package's item_names.txt), Polish name, stack, antiflag, flag, last sentence
    (38306, 'Extra Equipment Page', u'Strona ekwipunku II', 1,
     ANTI_DROP | ANTI_GIVE | ANTI_PKDROP | ANTI_MYSHOP | ANTI_SAFEBOX, FLAG_CONFIRM_WHEN_USE,
     u' Nie można nim handlować.'),
    (76055, 'Extra Equip. Page (t)', u'Strona ekwipunku II (wymienna)', 200,
     ANTI_PKDROP, FLAG_STACKABLE | FLAG_CONFIRM_WHEN_USE,
     u' Można nim handlować.'),
]

ICON = 'icon/item/38306.tga'

SKILL_VNUM = 200
SKILL_NAME = u'Zmiana strony ekwipunku'
SKILL_DESC = (u'Przełącza między pierwszą i drugą stroną ekwipunku. Bonusy daje tylko '
              u'założona strona. Odblokowuje ją przedmiot Strona ekwipunku II.')


def items():
    out = []
    for vnum, name, pl, stack, anti, flag, _tail in ITEMS:
        assert len(pl.encode('cp1250')) <= 32 and len(name) <= 32, vnum
        out.append(dict(vnum=vnum, name=name, locale_name=pl, type=ITEM_USE, subtype=USE_SPECIAL, stack=stack,
                        weight=0, size=1, antiflag=anti, flag=flag, wearflag=0, gold=0, shop_buy_price=0,
                        refined_vnum=0, refine_set=0, magic_pct=0, specular=0, socket_pct=0, addon_type=0,
                        limittype0=0, limitvalue0=0, limittype1=0, limitvalue1=0,
                        applytype0=0, applyvalue0=0, applytype1=0, applyvalue1=0, applytype2=0, applyvalue2=0,
                        value0=0, value1=0, value2=0, value3=0, value4=0, value5=0))
    return out


def skilldesc_line():
    # the columns of the client's locale/pl/skilldesc.txt (28, as Kombinacja 122 / Precyzja 246): vnum, job, name x3,
    # description, ..., flags (10), ..., icon (12); the rest empty (CP1250, CRLF in the pack)
    col = [str(SKILL_VNUM), u'SUPPORT', SKILL_NAME, u'', u'', SKILL_DESC, u'', u'', u'', u'', u'CANNOT_LEVEL_UP', u'',
           u'change_equipment', u' ']
    col += [u''] * (28 - len(col))
    return u'\t'.join(col)


def skilltable_line():
    # the client's gamedata/skilltable.txt (27 columns, as COMBO 122): type 0, max level 1, no cost, no motion
    col = [str(SKILL_VNUM), u'ADDITIONAL_PAGE', u'0', u'1', u'1', u'0', u'NONE', u'', u'', u'', u'', u'', u'', u'',
           u'DISABLE_BY_POINT_UP', u'NONE', u'NONE', u'', u'', u'NONE', u'0', u'0', u'NORMAL', u'0', u'1', u'0', u'0']
    assert len(col) == 27
    return u'\t'.join(col)


def sql_text(its):
    cols = ['vnum', 'name', 'locale_name', 'type', 'subtype', 'stack', 'weight', 'size', 'antiflag', 'flag', 'wearflag',
            'immuneflag', 'gold', 'shop_buy_price', 'refined_vnum', 'refine_set', 'magic_pct', 'specular', 'socket_pct',
            'addon_type', 'limittype0', 'limitvalue0', 'limittype1', 'limitvalue1', 'applytype0', 'applyvalue0',
            'applytype1', 'applyvalue1', 'applytype2', 'applyvalue2', 'value0', 'value1', 'value2', 'value3', 'value4',
            'value5', 'socket0', 'socket1', 'socket2', 'socket3', 'socket4', 'socket5']
    rows = []
    for w in its:
        vals = []
        for c in cols:
            if c == 'name':
                vals.append("'%s'" % w['name'].replace("'", "''"))
            elif c == 'locale_name':
                vals.append("_cp1250 X'%s'" % w['locale_name'].encode('cp1250').hex().upper())
            elif c == 'immuneflag':
                vals.append("''")
            elif c.startswith('socket') and c != 'socket_pct':
                vals.append('-1')
            else:
                vals.append(str(w[c]))
        rows.append('(' + ','.join(vals) + ')')
    return ('-- MT2009_PLUS_ADDEQ_V1: Druga strona ekwipunku (server-patches/addeq) - the unlock items of the "Official\n'
            '-- Additional Equipment Page" package: 38306 Strona ekwipunku II (bound) and 76055 its tradeable twin. GENERATED by\n'
            '-- tools/addeq/gen_addeq.py - do not edit, rerun it. Every start (apply.sh), idempotent: INSERT IGNORE - a row the\n'
            '-- operator changed (the Seban panel) is kept. ITEM_USE / USE_SPECIAL, asks before use; the engine unlocks the\n'
            '-- page (playerbot_addeq.cpp Mt2009AddeqUseItem). No skill_proto row: the skill 200 is the engine\'s own.\n'
            'SET NAMES utf8mb4;\n'
            'INSERT IGNORE INTO world.item_proto (' + ','.join('`%s`' % c for c in cols) + ') VALUES\n' +
            ',\n'.join(rows) + ';\n')


def main():
    its = items()
    d = dict(items=its,
             item_list=dict((str(v[0]), u'%d\tETC\t%s' % (v[0], ICON)) for v in ITEMS),
             itemdesc=dict((str(v[0]), u'%d\t%s\t%s' % (v[0], v[2], DESC + v[6])) for v in ITEMS),
             skilldesc=skilldesc_line(), skilltable=skilltable_line())
    with io.open(JSON, 'w', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(d, indent=1, ensure_ascii=False, sort_keys=True) + u'\n')
    with io.open(SQL, 'w', encoding='ascii', newline='\n') as f:
        f.write(sql_text(its))
    print('addeq: %d items -> %s, %s' % (len(its), os.path.relpath(JSON, REPO), os.path.relpath(SQL, REPO)))


if __name__ == '__main__':
    main()
