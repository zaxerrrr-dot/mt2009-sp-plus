#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_skrzynie_ucznia.py

MT2009_PLUS_SKRZYNIE_UCZNIA_WIKI_V1: the level chests of a new character - Skrzynia Ucznia I-III, Eksperta I-III,
Mistrza I-III and Arcymistrza (1, 10, 20 ... 90) - with the contents of the pl-wiki pages (the owner, 23 October 2026:
"tutaj masz pierwsze trzy - wsadz dokladnie takie same itemy", then the chain the wiki links up to level 90). Until now
the chain was r40250's (an old package's special_item_group.txt, special_item_group.starter.txt since the 2.0 port) -
no MT2009 change of its own (the CHANGELOG only added the missing 70-90 groups "as on the 1.x servers").

The items are the wiki's; the vnums are the official ones of the chests (Owsap's special_item_group.txt: the gift
series 76000-76042 "(present)" - not tradeable, as the wiki says of every chest item) where our world has them, else
our exact equivalents:
  * "Mikstura Ataku +10" = 71014 (+10 attack speed; the official 76017 is the +15 one), "Mikstura Ataku +20" = 76018
    (+20; our client called it "+15" and 76017 "+10" - both get the official Polish names here);
  * "Maska Uczuc" (15 dni) = 71033 (the official 38059 is the same 15-day mask);
  * "Pierscien Teleportacji" = 70058 (the official 76042 is the same ring), "Smocza Skrzynia" = 51639 (11x Cor
    Draconis, special_item_group.cors.txt; the official 76039 is the same chest);
  * "Kula Blogoslawienstwa" = 76015 (our "Marmur Blogoslawienstwa", the gift marble);
  * the class weapon +0 of Skrzynia Ucznia I stays as it was (10 Miecz, 1000 Sztylet, 7000 Wachlarz - the wiki: "Bron
    +0 na Lv. 1 (zalezna od klasy postaci)"); it does not clash with Bronie dla Mlodych Bohaterow (a letter of its own
    at 1, 10 ... 70, MT2009_PLUS_MLODZI_BOHATEROWIE_V1) - the chests hold no other weapon.
NOT here - "Torba Emocji" (Skrzynia Mistrza II, the official 38060): a random 12-hour emotion of the newer emotion
system (USE_EMOTION_PACK and its animations), which this engine and client have not got.

New items (our rows cloned, the official numbers and Polish names; GENERATED rows, tools/skrzynie_ucznia/
our_rows.tsv is the source - the generator never reads a database):
  76009 Zwoj Boga Smokow (71032), 76016 Zwoj Blogoslawienstwa (25040), 76026 Zwoj Egzorcyzmu (71001), 76034 Rada
  Pustelnika (71094), 76035 Zycie Boga Smokow (71027), 76036 Atak Boga Smokow (71028, +20% as officially), 76037
  Rekawica Zlodzieja and 76038 Medal Szczescia (71016 / 71017, 7 days as officially) - the gift series' rights
  (no trade / drop / shop / storage); 56001 Bilet Podrozniczy (5 uses, from level 10 - quest starter_chest takes the
  owner to the 1st or 2nd village of their kingdom) and 38103 Przekaska Appaloosa (7 more days to the Appaloosa
  56000 - quest starter_chest).

Writes (all GENERATED - edit this file, run it again):
  linux-port/docker/game/special_item_group.starter.txt     the chain's groups (the file's part above the boss
                                                            caskets; the rest of the file is kept as it is)
  linux-port/docker/mariadb/playerbot/skrzynie_ucznia.sql   world.item_proto: the new rows + the two names (apply.sh)
  tools/skrzynie_ucznia/skrzynie_items.json                 the client's records, item_list and itemdesc rows, the
                                                            Appaloosa mob (client-patches/client-2.0.30/tools/skrzynie)
  client-patches/client-2.0.30/root/icon/item/{56000,51639}.tga   the GF icons our packs have not got
  --md FILE                                                 the Polish table (before -> after) for the owner

Example: python3 tools/skrzynie_ucznia/gen_skrzynie_ucznia.py [--md /opt/metin2/cache/yohara/skrzynie-ucznia.md]
"""
import argparse
import io
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
M = 'MT2009_PLUS_SKRZYNIE_UCZNIA_WIKI_V1'
SIG = os.path.join(REPO, 'linux-port', 'docker', 'game', 'special_item_group.starter.txt')
SQL_OUT = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot', 'skrzynie_ucznia.sql')
JSON_OUT = os.path.join(HERE, 'skrzynie_items.json')
ROWS = os.path.join(HERE, 'our_rows.tsv')
ICON_OUT = os.path.join(REPO, 'client-patches', 'client-2.0.30', 'root', 'icon', 'item')
GF = '/opt/metin2/cache/gf/Gameforge_26.1.11/_client'
SIG_END = '# Two boss caskets the package has no group for'

# vnum -> the wiki's Polish name (the table and the group lines' comments)
NAMES = {
    10: 'Miecz+0', 1000: 'Sztylet+0', 7000: 'Wachlarz+0',
    27051: 'Czerwona Mikstura (M)', 27052: 'Niebieska Mikstura (M)', 27053: 'Zielona Mikstura (M)',
    27054: 'Fioletowa Mikstura (M)', 71153: u'Mikstura Mądrości', 71155: u'Mikstura Mądrości (3h)',
    76012: u'Mikstura Szybkości', 71014: 'Mikstura Ataku +10', 76017: u'Mikstura Ataku +15',
    76018: 'Mikstura Ataku +20', 76021: u'Eliksir Słońca (M)', 76022: u'Eliksir Słońca (Ś)',
    76004: u'Eliksir Księżyca (M)', 76005: u'Eliksir Księżyca (Ś)', 56000: u'Appaloos (pieczęć, 7 dni)',
    56001: u'Bilet Podróżniczy', 76006: 'Wykrywacz Kamieni Metin', 76007: u'Peleryna Męstwa (B)',
    71033: u'Maska Uczuć (15 dni)', 38103: u'Przekąska Appaloosa (7 dni)', 76011: u'Księga Lidera',
    76016: u'Zwój Błogosławieństwa', 76026: u'Zwój Egzorcyzmu', 76023: 'Zielony Czar', 76024: u'Zielona Siła',
    70058: u'Pierścień Teleportacji', 76003: u'Mikstura Pośpiechu', 76019: 'Przepustka', 76036: u'Atak Boga Smoków',
    76035: u'Życie Boga Smoków', 76037: u'Rękawica Złodzieja (7 dni)', 76038: u'Medal Szczęścia (7 dni)',
    76000: 'Wino z Kwiatu Brzoskwini', 76009: u'Zwój Boga Smoków', 76001: u'Zwój Powrotu Statusu',
    76013: 'Wzmocnienie Przedmiotu(n)', 76014: 'Zaczarowanie Przedmiotu(n)', 76034: 'Rada Pustelnika',
    76020: 'Eliksir Poszukiwacza', 51639: 'Smocza Skrzynia', 76002: u'Zasuszona Głowa', 76010: u'Krwisty Kamień',
    76015: u'Kula Błogosławieństwa', 76008: 'Medal Smoka',
    50187: 'Skrzynia Ucznia I', 50212: 'Skrzynia Ucznia I', 50213: 'Skrzynia Ucznia I',
    50188: 'Skrzynia Ucznia II', 50189: 'Skrzynia Ucznia III', 50190: 'Skrzynia Eksperta I',
    50191: 'Skrzynia Eksperta II', 50192: 'Skrzynia Eksperta III', 50193: 'Skrzynia Mistrza I',
    50194: 'Skrzynia Mistrza II', 50195: 'Skrzynia Mistrza III', 50196: 'Skrzynia Arcymistrza',
}

# (group name, chest vnum, level, wiki page, [(vnum, count)]) - the wiki pages' order (action=raw, 23 October 2026)
POTIONS_M = [(27051, 20), (27052, 10), (27053, 10), (27054, 10), (71155, 1)]
CHAIN = [
    ('lv1(sura_warrior)', 50187, 1, 'Skrzynia Ucznia I', POTIONS_M + [(10, 1), (50188, 1)]),
    ('lv1(assassin)', 50212, 1, 'Skrzynia Ucznia I', POTIONS_M + [(1000, 1), (50188, 1)]),
    ('lv1(shaman)', 50213, 1, 'Skrzynia Ucznia I', POTIONS_M + [(7000, 1), (50188, 1)]),
    ('lv10', 50188, 10, 'Skrzynia Ucznia II',
     [(76012, 5), (71014, 5), (76021, 1), (71153, 3), (56000, 1), (56001, 1), (50189, 1)]),
    ('lv20', 50189, 20, 'Skrzynia Ucznia III',
     [(76004, 1), (76006, 1), (76012, 5), (71014, 5), (76007, 20), (71033, 1), (71153, 3), (56001, 1), (38103, 1),
      (50190, 1)]),
    ('lv30', 50190, 30, 'Skrzynia Eksperta I',
     [(76011, 1), (76012, 5), (76016, 5), (71014, 5), (76007, 20), (56001, 1), (50191, 1)]),
    ('lv40', 50191, 40, 'Skrzynia Eksperta II',
     [(76011, 1), (76012, 5), (76018, 5), (71155, 1), (76016, 5), (76026, 3), (76023, 3), (76024, 3), (50192, 1)]),
    ('lv50', 50192, 50, 'Skrzynia Eksperta III',
     [(70058, 1), (76003, 5), (76007, 20), (76018, 5), (76019, 5), (76026, 5), (76036, 5), (76035, 5), (76037, 1),
      (76038, 1), (50193, 1)]),
    ('lv60', 50193, 60, 'Skrzynia Mistrza I',
     [(76000, 10), (76003, 5), (76009, 3), (76018, 5), (76026, 5), (76036, 5), (76035, 5), (76037, 1), (76038, 1),
      (76012, 5), (50194, 1)]),
    ('lv70', 50194, 70, 'Skrzynia Mistrza II',
     [(76001, 1), (76003, 5), (76013, 5), (76014, 5), (76018, 5), (76026, 5), (76034, 5), (76036, 5), (76035, 5),
      (76037, 1), (76038, 1), (76012, 5), (50195, 1)]),
    ('lv80', 50195, 80, 'Skrzynia Mistrza III',
     [(76003, 5), (76005, 1), (76018, 5), (76020, 5), (76013, 5), (76014, 5), (76026, 5), (76034, 5), (76036, 5),
      (76035, 5), (76037, 1), (76038, 1), (76012, 5), (51639, 1), (50196, 1)]),
    ('lv90', 50196, 90, 'Skrzynia Arcymistrza',
     [(76002, 3), (76010, 3), (76015, 2), (76022, 1), (76036, 5), (76013, 5), (76014, 10), (76035, 5), (76019, 5),
      (51639, 1)]),
]
# what the wiki lists and we cannot give: chest vnum -> [text]
MISSING = {50194: ['Torba Emocji (38060) - losowa emocja na 12 h; silnik i klient nie maja tego systemu emocji']}

# the rights of the gift series (our 76xxx rows): no trade (GIVE), no drop, no shop, no storage
ANTI_GIFT = 131072 | 65536 | 8192 | 128            # 204928, stackable
ANTI_GIFT_SINGLE = ANTI_GIFT | 32768               # 237696, one per slot

# new rows: vnum -> (our source row, ascii name, Polish name, overrides)
NEW = {
    76009: (71032, 'Zwoj Boga Smokow (gift)', u'Zwój Boga Smoków', dict(antiflag=ANTI_GIFT)),
    76016: (25040, 'Zwoj Blogoslawienstwa (gift)', u'Zwój Błogosławieństwa',
            dict(antiflag=ANTI_GIFT, flag=8196, gold=0, shop_buy_price=0)),
    76026: (71001, 'Zwoj Egzorcyzmu (gift)', u'Zwój Egzorcyzmu', dict(antiflag=ANTI_GIFT)),
    76034: (71094, 'Rada Pustelnika (gift)', u'Rada Pustelnika', dict(antiflag=ANTI_GIFT)),
    76035: (71027, 'Zycie Boga Smokow (gift)', u'Życie Boga Smoków', dict(antiflag=ANTI_GIFT)),
    76036: (71028, 'Atak Boga Smokow (gift)', u'Atak Boga Smoków', dict(antiflag=ANTI_GIFT, value2=20)),
    76037: (71016, 'Rekawica Zlodzieja (gift)', u'Rękawica Złodzieja', dict(antiflag=ANTI_GIFT, value3=604800)),
    76038: (71017, 'Medal Szczescia (gift)', u'Medal Szczęścia', dict(antiflag=ANTI_GIFT, value3=604800)),
    56001: (38100, 'Village Travel Ticket', u'Bilet Podróżniczy',
            dict(antiflag=ANTI_GIFT_SINGLE, stack=1, limittype0=1, limitvalue0=10, value0=5)),
    38103: (38100, 'Appaloosa Snack (7 days)', u'Przekąska Appaloosa', dict(antiflag=ANTI_GIFT_SINGLE, stack=1)),
}
# our rows renamed to the official Polish names (the guard: the old name)
RENAME = {76017: (u'Mikstura Ataku +10', u'Mikstura Ataku +15'), 76018: (u'Mikstura Ataku +15', u'Mikstura Ataku +20')}
# the client: item_list rows (the official client's icons) and itemdesc rows (the official Polish client's texts)
ITEM_LIST = {
    76009: 'icon/item/76009.tga', 76016: 'icon/item/76016.tga', 76026: 'icon/item/71001.tga',
    76034: 'icon/item/71094.tga', 76035: 'icon/item/71027.tga', 76036: 'icon/item/71028.tga',
    76037: 'icon/item/70043.tga', 76038: 'icon/item/71017.tga', 56001: 'icon/item/22000.tga',
    38103: 'icon/item/50709.tga', 56000: 'icon/item/56000.tga', 71033: 'icon/item/71011.tga',
    51639: 'icon/item/51639.tga',
}
DESC = {
    76009: u'Zwiększa szansę na ulepszenie przedmiotu o 10% i przedmiot nie ulega zniszczeniu, gdy ulepszenie '
           u'zawiedzie. W przypadku niepowodzenia jakość przedmiotu jest redukowana o 1 poziom. Niezdatny do handlu.',
    76016: u'Usuwa ryzyko zniszczenia przedmiotu podczas jego ulepszania. Jeżeli ulepszanie się nie powiedzie, to '
           u'jakość przedmiotu jest redukowana o 1 poziom. Przedmiot niezdatny do handlu.',
    76026: u'Uwalnia cię od klątwy złego ducha, jeśli nauka się nie powiedzie. Za pomocą tego zwoju możesz '
           u'przeczytać w ciągu jednego dnia kolejny dokument umiejętności. Niezdatny do handlu.',
    76034: u'Podnosi szansę na pomyślne przeczytanie następnej Księgi Umiejętności (lub Kamienia Duchowego). '
           u'Niezdatna do handlu.',
    76035: u'Zwiększa maksymalną ilość PŻ o 20% na 30 minut. Niezdatne do handlu.',
    76036: u'Zwiększa twoją siłę ataku o 20% na 30 minut. Niezdatny do handlu.',
    76037: u'Zwiększają o 50% twoją szansę na zdobycie przedmiotów. Po aktywowaniu nie można już zdezaktywować ich '
           u'działania. Czas trwania: 7 dni. Niezdatne do handlu.',
    76038: u'Podwaja szansę na zdobycie Yang. Czas trwania: 7 dni. Niezdatny do handlu.',
    56001: u'Zwój teleportuje cię tam i z powrotem między dwoma wioskami twojego królestwa. Można go użyć 5 razy i '
           u'jest dostępny od poziomu 10.',
    38103: u'Przedłuża życie twojego Appaloosa o 7 dni.',
    56000: u'Pieczęć ta przywołuje twojego łagodnego kucyka Appaloosa. Obdarza swoich jeźdźców +10 szybkością '
           u'ruchu.',
    76017: u'Zwiększa twoją szybkość ataku o 15% na okres 30 minut. Niezdatna do handlu.',
    76018: u'Zwiększa twoją szybkość ataku o 20% na okres 30 minut. Niezdatna do handlu.',
}
CLIENT_PROTO = sorted(NEW) + [56000, 76017, 76018]     # records the client gets (56000 had none)
MOB = dict(vnum=20253, template=20030, name='Appaloosa')   # the Appaloosa's race: the client had no mob record
ICONS = (56000, 51639)
COLS = ['vnum', 'name', 'locale_name', 'type', 'subtype', 'stack', 'weight', 'size', 'antiflag', 'flag', 'wearflag',
        'immuneflag', 'gold', 'shop_buy_price', 'refined_vnum', 'refine_set', 'magic_pct', 'specular', 'socket_pct',
        'addon_type', 'limittype0', 'limitvalue0', 'limittype1', 'limitvalue1', 'applytype0', 'applyvalue0',
        'applytype1', 'applyvalue1', 'applytype2', 'applyvalue2', 'value0', 'value1', 'value2', 'value3', 'value4',
        'value5', 'socket0', 'socket1', 'socket2', 'socket3', 'socket4', 'socket5']


def ascii(text):
    """a Polish text without its diacritics (the share files' comments are plain ascii)"""
    import unicodedata
    text = text.replace(u'ł', 'l').replace(u'Ł', 'L').replace(u'„', '"').replace(u'”', '"')
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')


def read_rows():
    rows = {}
    with io.open(ROWS, encoding='utf-8') as f:
        lines = [l.rstrip('\n') for l in f if not l.startswith('#')]
    head = lines[0].split('\t')
    for l in lines[1:]:
        c = dict(zip(head, l.split('\t')))
        r = {}
        for k in COLS:
            if k == 'name':
                r[k] = c['name_hex']
            elif k in ('locale_name', 'immuneflag'):
                r[k] = c[k]
            else:
                r[k] = int(c[k])
        rows[r['vnum']] = r
    return rows


def new_rows(our):
    out = {}
    for v, (src, name, pl, over) in sorted(NEW.items()):
        r = dict(our[src])
        r.update(vnum=v, name=name, locale_name=pl)
        r.update(over)
        assert len(name.encode('ascii')) < 32 and len(pl.encode('cp1250')) < 25, v
        out[v] = r
    return out


def sql_value(k, v):
    if k == 'locale_name':
        return "_cp1250 X'%s'" % v.encode('cp1250').hex().upper()
    if isinstance(v, int):
        return str(v)
    return "'" + v.replace('\\', '\\\\').replace("'", "''") + "'"


def write_sql(rows):
    L = ['-- %s: the new items of the level chests Skrzynia Ucznia I .. Skrzynia Arcymistrza (the pl-wiki chain,' % M,
         '-- the owner 23 October 2026). GENERATED by tools/skrzynie_ucznia/gen_skrzynie_ucznia.py from our_rows.tsv -',
         '-- do not edit, rerun it. apply.sh, every start; idempotent: our own row (the same vnum and name) is written',
         '-- again, a row of that vnum with another name (the operator made the item his own) stays (INSERT IGNORE).',
         'SET NAMES utf8mb4;']
    for v in sorted(rows):
        r = rows[v]
        L.append("DELETE FROM world.item_proto WHERE vnum = %d AND name = '%s';" % (v, r['name']))
    L.append('INSERT IGNORE INTO world.item_proto (%s) VALUES' % ','.join('`%s`' % c for c in COLS))
    vals = []
    for v in sorted(rows):
        r = rows[v]
        vals.append('(' + ','.join(sql_value(c, r[c]) for c in COLS) + ')')
    L.append(',\n'.join(vals) + ';')
    L.append('-- the official Polish names of the two gift attack potions (76017 gives +15, 76018 +20; the client said')
    L.append('-- "+10" and "+15"); only while the row still has the old name')
    for v, (old, new) in sorted(RENAME.items()):
        L.append("UPDATE world.item_proto SET locale_name = _cp1250 X'%s' WHERE vnum = %d AND locale_name = "
                 "_cp1250 X'%s';" % (new.encode('cp1250').hex().upper(), v, old.encode('cp1250').hex().upper()))
    data = '\n'.join(L) + '\n'
    with io.open(SQL_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write(data)


def sig_text():
    L = ['# The level chests of a new character - Skrzynia Ucznia I (every new character: quest starter_chest; a bot',
         '# from the playerbot seed) and the nine that come out of one another, each opened from its level (item_proto',
         '# limitvalue0) - with the contents of the pl-wiki pages (%s, the owner 23 October 2026;' % M,
         '# GENERATED by tools/skrzynie_ucznia/gen_skrzynie_ucznia.py - edit it, not these groups). Type Pct: every line',
         '# with its 100% - the whole list. Not given (the engine has no such item): Torba Emocji (Skrzynia Mistrza II).']
    for gname, vnum, level, page, items in CHAIN:
        L.append('# %s (Lv. %d)' % (page, level))
        L.append('Group\t%s' % gname)
        L.append('{')
        L.append('\tVnum\t%d' % vnum)
        L.append('\tType\tPct')
        for i, (v, n) in enumerate(items, 1):
            L.append('\t%d\t%d\t%d\t100\t-- %s' % (i, v, n, ascii(NAMES[v])))
        L.append('}')
    return '\n'.join(L) + '\n'


def write_sig():
    with io.open(SIG, encoding='utf-8', newline='') as f:
        text = f.read()
    at = text.index(SIG_END)
    nl = '\r\n' if '\r\n' in text[:at] else '\n'
    new = sig_text().replace('\n', nl) + text[at:]
    if new != text:
        with io.open(SIG, 'w', encoding='utf-8', newline='') as f:
            f.write(new)


def write_json(our, rows):
    items = []
    for v in CLIENT_PROTO:
        r = dict(rows.get(v) or our[v])
        if v in RENAME:
            r['locale_name'] = RENAME[v][1]
        if v not in rows:            # our existing row: the client's name is plain ascii as well
            r['name'] = {56000: 'Appaloosa', 76017: 'Potion of Attack +15 (gift)',
                         76018: 'Potion of Attack +20 (gift)'}[v]
        items.append(dict((k, r[k]) for k in COLS if k not in ('immuneflag', 'addon_type') and
                          not re.match(r'socket\d', k)))
    names = dict((v, rows[v]['locale_name']) for v in rows)
    names.update((v, RENAME[v][1]) for v in RENAME)
    names[56000] = u'Appaloosa'
    d = dict(marker=M, items=items,
             item_list=dict((str(v), '%d\tETC\t%s' % (v, p)) for v, p in sorted(ITEM_LIST.items())),
             itemdesc=dict((str(v), u'%d\t%s\t%s' % (v, names[v], DESC[v])) for v in sorted(DESC)),
             mob=MOB)
    with io.open(JSON_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(d, ensure_ascii=False, indent=1, sort_keys=True) + '\n')


def copy_icons():
    for v in ICONS:
        src = os.path.join(GF, 'icon', 'item', '%d.tga' % v)
        dst = os.path.join(ICON_OUT, '%d.tga' % v)
        if os.path.exists(src):
            if not os.path.exists(dst) or open(src, 'rb').read() != open(dst, 'rb').read():
                shutil.copyfile(src, dst)
        elif not os.path.exists(dst):
            raise SystemExit('no GF icon %s and none in the repo' % src)


def old_chain():
    """the groups the file had before this generator (git: the parent of the first generated version)"""
    import subprocess
    try:
        text = subprocess.check_output(['git', '-C', REPO, 'show', 'claude/yohara-3:linux-port/docker/game/'
                                        'special_item_group.starter.txt']).decode('utf-8')
    except Exception:
        return {}
    groups, cur = {}, None
    for l in text.splitlines():
        m = re.match(r'\s*Vnum\s+(\d+)', l)
        if m:
            cur = int(m.group(1))
            groups[cur] = []
            continue
        m = re.match(r'\s*\d+\s+(\d+)\s+(\d+)\s+\d+', l)
        if m and cur is not None:
            groups[cur].append((int(m.group(1)), int(m.group(2))))
        if l.startswith('}'):
            cur = None
    return groups


OLD_NAMES = {76008: 'Medal Smoka', 76017: u'Mikstura Ataku „+10” (daje +15)', 76018: u'Mikstura Ataku „+15” (daje +20)',
             76015: u'Marmur Błogosławieństwa'}


def fmt(items, names):
    return ', '.join('%s x%d (%d)' % (names.get(v, NAMES.get(v, str(v))), n, v) if n > 1 else
                     '%s (%d)' % (names.get(v, NAMES.get(v, str(v))), v) for v, n in items)


def write_md(path):
    old = old_chain()
    L = [u'# Skrzynie Ucznia / Eksperta / Mistrza / Arcymistrza — zawartość wg wiki',
         u'',
         u'Znacznik: `%s`. Gałąź `claude/y-skrzynie`. Polecenie właściciela z 23.10.2026: zawartość jak na '
         u'pl-wiki (Skrzynia Ucznia I–III, Eksperta I–III, Mistrza I–III, Arcymistrza).' % M,
         u'Źródło danych: `tools/skrzynie_ucznia/gen_skrzynie_ucznia.py` → `special_item_group.starter.txt`, '
         u'`skrzynie_ucznia.sql` (nowe przedmioty), klient: `client-2.0.30/tools/skrzynie`.',
         u'Wcześniej łańcuch był z paczki r40250 (bez własnej zmiany MT2009). Liczba w nawiasie = vnum.',
         u'',
         u'| skrzynia (vnum) | poziom | przed | po (wiki) |',
         u'|---|---|---|---|']
    seen = set()
    for gname, vnum, level, page, items in CHAIN:
        label = page + (' (%s)' % gname.split('(')[1].rstrip(')').replace('_', '/') if '(' in gname else '')
        before = fmt(old.get(vnum, []), OLD_NAMES)
        after = fmt(items, {})
        miss = MISSING.get(vnum)
        if miss:
            after += u'. **Brak:** ' + '; '.join(miss)
        L.append(u'| %s (%d) | %d | %s | %s |' % (label, vnum, level, before or u'—', after))
        seen.add(vnum)
    L += [u'',
          u'## Jak się je dostaje',
          u'',
          u'- Skrzynia Ucznia I: każda nowa postać gracza przy pierwszym logowaniu (quest `starter_chest`, wg klasy: '
          u'50187 wojownik/sura, 50212 ninja, 50213 szaman), bot — z seeda. Wyłącznik: `M2_STARTER_CHEST`.',
          u'- Każda następna wypada z poprzedniej; otwiera się od poziomu z tabeli (item_proto, bez zmian).',
          u'',
          u'## Nowe przedmioty (serwer + klient)',
          u'',
          u'| vnum | nazwa | wzór (nasz wiersz) | uwagi |',
          u'|---|---|---|---|']
    notes = {76036: u'+20% ataku (jak we wzorcowych danych; 71028 daje 15)', 76037: u'7 dni', 76038: u'7 dni',
             56001: u'5 użyć, od 10 poz.; wybór: 1. lub 2. wioska swojego królestwa (quest starter_chest)',
             38103: u'+7 dni do Appaloosa (56000) — noszonego albo w plecaku (quest starter_chest)'}
    for v, (src, name, pl, over) in sorted(NEW.items()):
        L.append(u'| %d | %s | %d | %s |' % (v, pl, src, notes.get(v, u'niehandlowalny (seria prezentowa 76xxx)')))
    L += [u'',
          u'Klient dostaje też: rekord 56000 Appaloosa (serwer go miał, klient nie — pieczęć była bez nazwy i ikony), '
          u'moba 20253 Appaloosa (model `pony/horse_normal02` już jest), wiersz item_list 71033 (Maska Uczuć bez ikony), '
          u'ikony 56000 i 51639 (Smocza Skrzynia nie miała ikony), nazwy 76017 „Mikstura Ataku +15” i 76018 '
          u'„Mikstura Ataku +20” (było „+10”/„+15”, a dają 15/20).',
          u'',
          u'## Zamienniki (zamiast vnumów ze wzorcowych danych, ten sam przedmiot)',
          u'',
          u'- Mikstura Ataku +10 → 71014 (wzorcowa 76017 to +15), Maska Uczuć 15 dni → 71033 (wzorcowa 38059), '
          u'Pierścień Teleportacji → 70058 (wzorcowy 76042), Smocza Skrzynia → 51639 (wzorcowa 76039, '
          u'11× Cor Draconis), Kula Błogosławieństwa → 76015 (u nas „Marmur Błogosławieństwa”).',
          u'',
          u'## Brakuje',
          u'',
          u'- **Torba Emocji** (Skrzynia Mistrza II): losowa emocja na 12 h z nowszego systemu emocji — nie mamy go '
          u'ani w silniku, ani w kliencie (animacje). Pominięta.',
          u'',
          u'## Bronie dla Młodych Bohaterów',
          u'',
          u'Bez konfliktu: skrzynie dają tylko broń +0 z Skrzyni Ucznia I (jak na wiki); bronie Młodych Bohaterów '
          u'przychodzą osobnym listem (1, 10 … 70).']
    with io.open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--md')
    a = ap.parse_args()
    our = read_rows()
    rows = new_rows(our)
    for gname, vnum, level, page, items in CHAIN:
        assert len(items) == len(set(v for v, n in items)), gname
        for v, n in items:
            assert v in NAMES, (gname, v)
    write_sql(rows)
    write_sig()
    write_json(our, rows)
    copy_icons()
    if a.md:
        write_md(a.md)
    print('chests %d, new items %d, client records %d' % (len(CHAIN), len(rows), len(CLIENT_PROTO)))


if __name__ == '__main__':
    main()
