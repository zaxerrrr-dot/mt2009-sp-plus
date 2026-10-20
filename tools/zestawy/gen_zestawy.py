#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_zestawy.py [--xlsx FILE]

MT2009_PLUS_COSTUME_SET_V2: the costume sets as on the Polish global server (the owner, 20 October 2026: "system
zestawow ... musi byc dokladnie tak samo jak na globalu polskim, czyli rozne stopnie bonusow i rozne bonusy dla danego
zestawu. Jesli jakichs przedmiotow brakuje, np. Amulet Nazara, to dodaj, z bonusami z wiki"). Source: the owner's
sheet Metin2_Zestawy_kostiumow.xlsx (metin2alerts.com/pl/wiki/costumes, read 16.10.2026) - 48 sets, every part with
its alternatives, the bonuses of each grade (2..6 parts worn; a grade's bonuses are the whole grade, not added to the
lower ones). --xlsx FILE reads the sheet again into tools/zestawy/zestawy_wiki.json (needs openpyxl - the venv
/opt/metin2/cache/xlsxenv); without it the JSON is the source.

Writes (all GENERATED - edit this file or the JSON, run it again):
  linux-port/docker/game/costume_sets.txt              the "#Z" block (the sets, parts, grades) - the V1 reader skips
                                                       "#" lines; the V1 lines (bots, the Arezzo sets) stay as they are
  client-patches/client-2.0.30/root/costume_set_bonus.py   the client's copy (affect bar 545, item tooltips)
  linux-port/docker/mariadb/playerbot/zestawy_items.sql    the set items the server lacked (world.item_proto)
  linux-port/docker/game/special_item_group.unique_attr.txt   their bonuses (attr groups) - the generated block
  tools/zestawy/zestawy_items.json                     the client's records, item_list and itemdesc rows
                                                       (client-patches/client-2.0.30/tools/zestawy)
  client-patches/client-2.0.30/root/icon/item/<vnum>.tga   the GF icons of the added items

Example: python3 tools/zestawy/gen_zestawy.py
"""
import io
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
MARK = 'MT2009_PLUS_COSTUME_SET_V2'
WIKI_JSON = os.path.join(HERE, 'zestawy_wiki.json')
ITEMS_JSON = os.path.join(HERE, 'zestawy_items.json')
SETS_TXT = os.path.join(REPO, 'linux-port', 'docker', 'game', 'costume_sets.txt')
UNIQUE_ATTR = os.path.join(REPO, 'linux-port', 'docker', 'game', 'special_item_group.unique_attr.txt')
SQL_OUT = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot', 'zestawy_items.sql')
PY_OUT = os.path.join(REPO, 'client-patches', 'client-2.0.30', 'root', 'costume_set_bonus.py')
ICON_OUT = os.path.join(REPO, 'client-patches', 'client-2.0.30', 'root', 'icon', 'item')
GF = '/opt/metin2/cache/gf/Gameforge_26.1.11/_client'

# The sheet's vnum -> ours: the official 41980/41981/45722 are our Death Ruler costume and helmet
# (item_proto.mt2009plus.sql); the Smocza Rycerka+ pair and the helmet live at 940180/940181/945722 here.
ALIAS = {41980: 940180, 41981: 940181, 45722: 945722}
# The claws of the Lycan (no such class here): the sheet's weapon skins 40156, 40198, 40205, 40226 do not exist.
NO_CLASS = {40156, 40198, 40205, 40226}

# The sheet's bonus id (the official apply number) -> our point; DROP: the drop chance (GetDropPct, no point).
# Experience is POINT_RAMADAN_CANDY_BONUS_EXP - additive and without the 100% cap of POINT_MALL_EXPBONUS (sets
# give up to +150%; MT2009_PLUS_NS_SPECIAL_EXP_V1); the element powers are the talismans' POINT_ENCHANT_*.
POINTS = {
    7: 'POINT_ATT_SPEED', 8: 'POINT_MOV_SPEED', 9: 'POINT_CASTING_SPEED', 10: 'POINT_HP_REGEN',
    13: 'POINT_STUN_PCT', 15: 'POINT_CRITICAL_PCT', 16: 'POINT_PENETRATE_PCT', 23: 'POINT_STEAL_HP',
    35: 'POINT_RESIST_FIRE', 53: 'POINT_ATT_GRADE_BONUS', 55: 'POINT_MAGIC_ATT_GRADE_BONUS',
    63: 'POINT_ATTBONUS_MONSTER', 66: 'POINT_RAMADAN_CANDY_BONUS_EXP', 67: 'DROP', 71: 'POINT_SKILL_DAMAGE_BONUS',
    72: 'POINT_NORMAL_HIT_DAMAGE_BONUS', 86: 'POINT_MELEE_MAGIC_ATT_BONUS_PER', 87: 'POINT_RESIST_ICE',
    99: 'POINT_ENCHANT_ELECT', 100: 'POINT_ENCHANT_FIRE', 101: 'POINT_ENCHANT_ICE', 102: 'POINT_ENCHANT_WIND',
    103: 'POINT_ENCHANT_EARTH', 104: 'POINT_ENCHANT_DARK', 151: 'POINT_ATTBONUS_BOSS', 214: 'POINT_ATTBONUS_STONE',
}
PART_LABEL = {u'Zbroja': u'Kostium', u'Fryzura': u'Fryzura', u'Broń': u'Nakładka na broń', u'Zwierzak': u'Zwierzak',
              u'Wierzchowiec': u'Wierzchowiec', u'Pierścień / amulet': u'Pierścień / amulet', u'Akcesorium': u'Szarfa'}

# The set items the server lacked (20 October 2026) - each as an item we have (the template: its flags, wear slot,
# limit), with the pl-wiki's bonuses (special_item_group attr groups; a line is POINT number, value: 127 experience
# (additive), 17 attack speed, 21 casting speed, 93 attack %, 53 strong vs monsters, 119/120 max HP/SP %,
# 131 magic attack %, 132 magic/melee attack %, 121 skill damage, 149 strong vs Metin stones).
# limit: LIMIT_REAL_TIME (7) and seconds; 0 = the engine's 7 days (as Lizak Potegi).
SPECIAL_GROUP = 10051          # item -> attr group (the base file's 10050 holds the older rings; < 30000)
NEW_ITEMS = [
    dict(vnum=71202, name=u'Amulet Nazara', template=71136, limit=0, attr_group=100010,
         attrs=[(127, 50), (17, 20), (21, 20), (93, 30), (53, 10)],
         desc=u'Amulet chroniący przed złym spojrzeniem. Daje: +50% PD, +20% szybkości ataku, +20% szybkości zaklęć, '
              u'+30% obrażeń, +10% siły w walce z potworami. Czas upływa także, gdy go nie nosisz.',
         wiki=u'pl-wiki "Amulet Nazara": +50% PD, +20% szybkości ataku, +20% szybkości zaklęć, +30% obrażeń, '
              u'+10% siły w walce z potworami; czas trwania nie podany (tu 7 dni jak Lizak Potęgi)'),
    dict(vnum=71188, name=u'Lizak Magii', template=71136, limit=0, attr_group=100011,
         attrs=[(127, 50), (17, 20), (21, 20), (131, 30), (119, 10), (120, 10)],
         desc=u'Lizak o tajemniczym składzie, pełen magii. Daje: +50% PD, +20% szybkości ataku, +20% szybkości '
              u'zaklęć, +30% obrażeń magicznych, +10% maks. PŻ, +10% maks. PE. Działa 7 dni.',
         wiki=u'pl-wiki "Lizak Magii": +50% PD, +20% szybkości ataku i zaklęć, +30% obrażeń magicznych, +10% maks. '
              u'PŻ/PE, 7 dni'),
    dict(vnum=71199, name=u'Czekoladowy Amulet', template=71136, limit=0, attr_group=100012,
         attrs=[(127, 50), (17, 20), (21, 20), (53, 10), (119, 10), (120, 10)],
         desc=u'Słodki amulet na walentynki. Daje: +50% PD, +20% szybkości ataku, +20% szybkości zaklęć, +10% siły '
              u'w walce z potworami, +10% maks. PŻ, +10% maks. PE. Czas upływa także, gdy go nie nosisz.',
         wiki=u'pl-wiki "Czekoladowy Amulet": 50% PD, +20 szybkości ataku i zaklęć, +10% siły w walce z potworami, '
              u'+10% maks. PŻ/PE'),
    dict(vnum=70607, name=u'Mistrzowski Emblemat', template=71136, limit=21600, attr_group=100013,
         attrs=[(127, 50), (17, 20), (21, 20), (132, 35), (119, 10), (120, 10)],
         desc=u'Emblemat mistrzów piłki nożnej. Na 6 godzin daje: +50% PD, +20% szybkości ataku, +20% szybkości '
              u'zaklęć, +35% ataku magicznego i w zwarciu, +10% maks. PŻ, +10% maks. PE.',
         wiki=u'pl-wiki "Mistrzowski emblemat": +50% PD, +10% szansy na drop, +20% szybkości ataku i zaklęć, +35% '
              u'ataku magicznego i w zwarciu, +10% maks. PŻ/PE, 6 godzin (szansy na drop tu brak - przedmiot nie ma '
              u'takiego punktu)'),
    dict(vnum=72713, name=u'Błogosławieństwo Mocy', template=71136, limit=0, attr_group=100014,
         attrs=[(127, 50), (17, 5), (21, 20), (149, 10), (121, 40)],
         desc=u'Amulet z Koła Strażników. Daje: +50% PD, +5% szybkości ataku, +20% szybkości zaklęć, +10% siły '
              u'w walce z kamieniami Metin, +40% obrażeń umiejętności. Czas upływa także, gdy go nie nosisz.',
         wiki=u'pl-wiki "Błogosławieństwo Mocy": +50% PD, +5% szybkości ataku, +20% szybkości zaklęć, +10% siły '
              u'w walce z kamieniami Metin, +40% obrażeń od umiejętności'),
    dict(vnum=86064, name=u'Szarfa Serca (unikat.)', template=85024, limit=None, attr_group=0, attrs=[],
         desc=u'Szarfa walentynkowa w kształcie skrzydeł serca. Pochłania 11-25% bonusów broni lub zbroi '
              u'(łączenie u Theowahdana).',
         wiki=u'pl-wiki "Szarfa Serca (unikat.)": pochłania 11-25% bonusów (szarfa unikatowa, stopień 4)',
         model=u'd:/ymir work/item/wing/acce_valentine_2020_4.gr2',
         # the client's item_proto has no sash records (the exe makes 85001-85104 itself, client-patches/exe
         # GameLib/ItemManager.cpp) - this one is Lizak Potegi's record made a grade 4 sash as the exe makes them:
         # ITEM_COSTUME / COSTUME_ACCE, apply 0 = APPLY_ACCEDRAIN_RATE 20 (the tooltip), value0 4, specular 100
         client=dict(type=28, subtype=3, stack=1, antiflag=49280, flag=0, wearflag=0, limit=(0, 0),
                     applies=[(97, 20), (0, 0), (0, 0)], values=[4, 0, 0, 0, 0, 0], specular=100)),
]


def ascii_name(s):
    tr = {ord(a): b for a, b in zip(u'ąćęłńóśźżĄĆĘŁŃÓŚŹŻ', u'acelnoszzACELNOSZZ')}
    return s.translate(tr)


def read_xlsx(path):
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=False)
    out = {}
    for ws in wb.worksheets:
        rows = [list(r) for r in ws.iter_rows(values_only=True) if any(c is not None for c in r)]
        out[ws.title] = dict(notes=[r[0] for r in rows[:3]], header=rows[3], rows=rows[4:])
    with io.open(WIKI_JSON, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=0)
        f.write(u'\n')


def load_sets():
    d = json.load(io.open(WIKI_JSON, encoding='utf-8'))
    sets = []
    for i, r in enumerate(d['Zestawy']['rows']):
        sets.append(dict(id=i + 1, name=r[0], key=r[1], count=r[2], parts=[], grades={}))
    by_key = dict((s['key'], s) for s in sets)
    for r in d['Przedmioty']['rows']:
        s = by_key[r[1]]
        if r[3] in NO_CLASS:
            continue
        if not s['parts'] or s['parts'][-1]['slot'] != r[2]:
            assert all(p['slot'] != r[2] for p in s['parts']), (r[1], r[2])
            s['parts'].append(dict(slot=r[2], vnums=[], names=[]))
        v = ALIAS.get(r[3], r[3])
        if v not in s['parts'][-1]['vnums']:
            s['parts'][-1]['vnums'].append(v)
            s['parts'][-1]['names'].append(r[4])
    for r in d['Bonusy']['rows']:
        s = by_key[r[1]]
        s['grades'].setdefault(int(r[2]), []).append(dict(text=r[3], value=int(r[4]), unit=r[5], point=POINTS[r[6]]))
    for s in sets:
        assert len(s['parts']) == s['count'], (s['key'], len(s['parts']), s['count'])
        assert max(s['grades']) == s['count'] and min(s['grades']) == 2, s['key']
    return sets


def write_sets_txt(sets):
    raw = io.open(SETS_TXT, encoding='utf-8', newline='').read()
    nl = '\r\n' if '\r\n' in raw else '\n'
    lines = [l for l in raw.replace('\r\n', '\n').split('\n') if not l.startswith('#Z')]   # the block before
    block = [u'#Z# %s: the costume sets as on the Polish global server (tools/zestawy/gen_zestawy.py, the' % MARK,
             u'#Z# owner\'s sheet of 20 October 2026) - "#Z<TAB>S<TAB>id<TAB>name" a set, "#Z<TAB>P<TAB>id<TAB>vnums" one part',
             u'#Z# (its alternatives), "#Z<TAB>B<TAB>id<TAB>parts<TAB>POINT_*|DROP<TAB>value" one bonus of the grade of that',
             u'#Z# many parts (server-patches/zestawy). A V1 line below whose vnums no #Z set has keeps +800 HP / +15 attack.']
    for s in sets:
        block.append(u'#Z\tS\t%d\t%s' % (s['id'], ascii_name(s['name'])))
        for p in s['parts']:
            block.append(u'#Z\tP\t%d\t%s' % (s['id'], ','.join(str(v) for v in p['vnums'])))
        for g in sorted(s['grades']):
            for b in s['grades'][g]:
                block.append(u'#Z\tB\t%d\t%d\t%s\t%d' % (s['id'], g, b['point'], b['value']))
    # after the file's own header (the leading comment lines), before the V1 lines
    at = 0
    while at < len(lines) and lines[at].startswith('#'):
        at += 1
    lines = lines[:at] + block + lines[at:]
    io.open(SETS_TXT, 'w', encoding='utf-8', newline='').write(nl.join(lines))


def pystr(s):
    """a Python 2 byte-string literal of s in cp1250 (the client's root files are latin-1 source with escapes)"""
    out = []
    for c in s.encode('cp1250'):
        ch = chr(c)
        if ch in '\\"':
            out.append('\\' + ch)
        elif 32 <= c < 127:
            out.append(ch)
        else:
            out.append('\\x%02x' % c)
    return '"' + ''.join(out) + '"'


def write_client_py(sets):
    L = ['# -*- coding: latin-1 -*-',
         '# MT2009_PLUS_COSTUME_SET_V2: the costume sets as on the Polish global server - GENERATED by',
         '# tools/zestawy/gen_zestawy.py (the owner\'s sheet, 20 October 2026), do not edit by hand. The server: the "#Z"',
         '# lines of costume_sets.txt (server-patches/zestawy). Affect 545\'s entry without a point has the value',
         '# set * 10 + parts worn; ids from LEGACY_BASE are the old two-part sets of costume_sets.txt (+800 HP, +15 attack).',
         '# SETS[id] = (name, ((part, (vnums)), ...), {parts: (bonus lines of that grade)})',
         '',
         'LEGACY_BASE = 100',
         'LEGACY_LINES = (%s, %s)' % (pystr(u'+800 PŻ'), pystr(u'+15 wartości ataku')),
         '',
         'SETS = {']
    for s in sets:
        parts = ', '.join('(%s, (%s,))' % (pystr(PART_LABEL[p['slot']]), ','.join(str(v) for v in p['vnums']))
                          for p in s['parts'])
        grades = ', '.join('%d: (%s,)' % (g, ', '.join(pystr(b['text']) for b in s['grades'][g]))
                           for g in sorted(s['grades']))
        L.append('\t%d: (%s, (%s), {%s}),\t# %s' % (s['id'], pystr(s['name']), parts, grades, s['key']))
    L.append('}')
    L += ['',
          'VNUM_SETS = {}',
          'for _id, (_name, _parts, _grades) in SETS.items():',
          '\tfor _label, _vnums in _parts:',
          '\t\tfor _v in _vnums:',
          '\t\t\tVNUM_SETS.setdefault(_v, []).append(_id)',
          '',
          '',
          'def GradeLines(setId, parts):',
          '\t"""the bonus lines of a set\'s grade for that many parts (the highest grade not above it)"""',
          '\tif setId >= LEGACY_BASE:',
          '\t\treturn LEGACY_LINES if parts >= 2 else ()',
          '\tif not SETS.has_key(setId):',
          '\t\treturn ()',
          '\tgrades = SETS[setId][2]',
          '\tfor g in xrange(parts, 1, -1):',
          '\t\tif grades.has_key(g):',
          '\t\t\treturn grades[g]',
          '\treturn ()',
          '',
          '',
          'def AffectDescription(value):',
          '\t"""the affect bar\'s tooltip of affect 545 (uiaffectbar.py): lines split by ;"""',
          '\tvalue = int(value)',
          '\tsetId, parts = value // 10, value % 10',
          '\tif setId >= LEGACY_BASE or not SETS.has_key(setId):',
          '\t\tlines = [%s, %s %% parts]' % (pystr(u'Bonus zestawu kostiumów'), pystr(u'Założone części zestawu: %d/2')),
          '\telse:',
          '\t\tname, partList, grades = SETS[setId]',
          '\t\tlines = [%s + name, %s %% (parts, len(partList))]' % (pystr(u'Zestaw: '), pystr(u'Założone części zestawu: %d/%d')),
          '\tlines += list(GradeLines(setId, parts))',
          '\treturn ";".join(lines)',
          '']
    io.open(PY_OUT, 'w', encoding='latin-1', newline='\n').write('\n'.join(L))


def write_items(sets):
    # the server: one temporary copy of the template per item, renamed (INSERT IGNORE - a row there stays)
    L = ['-- %s: the costume sets\' items the server lacked (the owner, 20 October 2026: "Jesli jakichs przedmiotow' % MARK,
         '-- brakuje, np. Amulet Nazara, to dodaj, z bonusami z wiki"). GENERATED by tools/zestawy/gen_zestawy.py - do not',
         '-- edit, rerun it. Every start (apply.sh), idempotent (INSERT IGNORE). Each is a copy of an item we have (the',
         '-- template: flags, wear slot, limit) under its official vnum (free here, 20 October 2026); the rings\' and',
         '-- amulets\' bonuses are attr groups of special_item_group.unique_attr.txt (special group %d), as the older' % SPECIAL_GROUP,
         '-- rings\' (MT2009_PLUS_UNIQUE_RING_BONUS_V1). Bonuses from the pl-wiki:']
    for it in NEW_ITEMS:
        L.append('--   %d %s (template %d) - %s' % (it['vnum'], ascii_name(it['name']), it['template'], ascii_name(it['wiki'])))
    L.append('SET NAMES utf8mb4;')
    for it in NEW_ITEMS:
        L.append('DROP TEMPORARY TABLE IF EXISTS world.mt2009_zestawy_tmp;')
        L.append('CREATE TEMPORARY TABLE world.mt2009_zestawy_tmp AS SELECT * FROM world.item_proto WHERE vnum = %d;' % it['template'])
        sets_ = "vnum = %d, name = '%s', locale_name = _cp1250 X'%s'" % (
            it['vnum'], ascii_name(it['name']).replace("'", "''"), it['name'].encode('cp1250').hex().upper())
        if it['limit'] is not None:
            sets_ += ', limittype0 = 7, limitvalue0 = %d' % it['limit']
        L.append('UPDATE world.mt2009_zestawy_tmp SET %s;' % sets_)
        L.append('INSERT IGNORE INTO world.item_proto SELECT * FROM world.mt2009_zestawy_tmp;')
    L.append('DROP TEMPORARY TABLE IF EXISTS world.mt2009_zestawy_tmp;')
    io.open(SQL_OUT, 'w', encoding='utf-8', newline='\n').write('\n'.join(L) + '\n')

    # the bonuses: the generated block of special_item_group.unique_attr.txt
    raw = io.open(UNIQUE_ATTR, encoding='utf-8', newline='').read()
    nl = '\r\n' if '\r\n' in raw else '\n'
    text = raw.replace('\r\n', '\n')
    begin, end = u'# BEGIN %s (tools/zestawy/gen_zestawy.py - generated, do not edit)\n' % MARK, u'# END %s\n' % MARK
    if begin in text:
        a = text.index(begin)
        text = text[:a] + text[text.index(end, a) + len(end):]
    if not text.endswith('\n'):
        text += '\n'
    B = [begin, u'Group\tMT2009_zestawy_special\n{\n\tVnum\t%d\n\ttype\tspecial\n' % SPECIAL_GROUP]
    n = 0
    for it in NEW_ITEMS:
        if it['attr_group']:
            n += 1
            B.append(u'\t%d\t%d\t%d\t1\t-- %s\n' % (n, it['vnum'], it['attr_group'], ascii_name(it['name'])))
    B.append(u'}\n')
    for it in NEW_ITEMS:
        if not it['attr_group']:
            continue
        B.append(u'Group\tMT2009_%s\n{\n\tVnum\t%d\n\ttype\tattr\n' % (ascii_name(it['name']).lower().replace(' ', '_'), it['attr_group']))
        for i, (p, v) in enumerate(it['attrs']):
            B.append(u'\t%d\t%d\t%d\n' % (i + 1, p, v))
        B.append(u'}\n')
    B.append(end)
    text += ''.join(B)
    io.open(UNIQUE_ATTR, 'w', encoding='utf-8', newline='').write(text.replace('\n', nl))

    # the client: records over the template's, item_list and itemdesc rows; the GF icons
    items, item_list, itemdesc = [], {}, {}
    for it in NEW_ITEMS:
        items.append(dict(vnum=it['vnum'], template=71136, name=ascii_name(it['name']), locale_name=it['name'],
                          limit=it['limit'], client=it.get('client')))
        if it.get('model'):
            item_list[str(it['vnum'])] = u'%d\tWING\ticon/item/%d.tga\t%s' % (it['vnum'], it['vnum'], it['model'])
        else:
            item_list[str(it['vnum'])] = u'%d\tETC\ticon/item/%d.tga' % (it['vnum'], it['vnum'])
        itemdesc[str(it['vnum'])] = u'%d\t%s\t%s' % (it['vnum'], it['name'], it['desc'])
        src = os.path.join(GF, 'icon', 'item', '%d.tga' % it['vnum'])
        if os.path.exists(src):
            shutil.copyfile(src, os.path.join(ICON_OUT, '%d.tga' % it['vnum']))
        else:
            print('no GF icon for %d' % it['vnum'])
    with io.open(ITEMS_JSON, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(dict(items=items, item_list=item_list, itemdesc=itemdesc), f, ensure_ascii=False, indent=1)
        f.write(u'\n')


def main():
    if '--xlsx' in sys.argv:
        read_xlsx(sys.argv[sys.argv.index('--xlsx') + 1])
    sets = load_sets()
    write_sets_txt(sets)
    write_client_py(sets)
    write_items(sets)
    print('%d sets, %d parts, %d bonus lines; %d new items' % (
        len(sets), sum(len(s['parts']) for s in sets), sum(len(b) for s in sets for b in s['grades'].values()),
        len(NEW_ITEMS)))


if __name__ == '__main__':
    main()
