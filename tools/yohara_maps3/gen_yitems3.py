#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_yitems3.py [--owsap DIR] [--gf DIR]

MT2009_PLUS_YOHARA_MAPS3_V1: the items of the third batch of Yohara places (ymaps3_data.py) - every item the pl-wiki
(the TR wiki where the Polish page is empty) lists as a drop of their monsters, bosses and Metins, the dungeons'
keys and rewards and the chests' contents, that our world did not have; the official vnums and numbers of Owsap
v6.2.6 (Server/Server/db/item_proto.txt), the Polish names and descriptions of its Polish client (= the official
translation), the icons of the GF 26.1.11 client - the method of tools/yohara_items/gen_yitems.py.
An item whose system we lack is an inert, tradeable material (the owner's rule of 13 October) - its row says what
it waits for. The wiki gives no odds: the percents are ours, official-like (rare; the test server's 500% drop
event is not compensated for).

Writes (all GENERATED - edit this file, run it again):
  linux-port/docker/mariadb/playerbot/yohara_items3.sql                 world.item_proto (INSERT IGNORE)
  linux-port/docker/game/yohara_maps3/mob_drop_item.yohara_maps3.txt    the monsters', bosses', Metins' drops
  linux-port/docker/game/yohara_maps3/special_item_group.yohara_maps3.txt the chests' contents
  tools/yohara_maps3/yohara_items3.json                                 the client's records, item_list, itemdesc
  client-patches/client-2.0.30/root/icon/item/<icon>.tga                the GF icons our packs lack

Example: python3 tools/yohara_maps3/gen_yitems3.py
"""
import argparse
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, 'tools', 'yohara_items'))
import gen_yitems as Y  # noqa: E402  (the engine's numbers, the row writer)
import ymaps3_data as D  # noqa: E402

SQL_OUT = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot', 'yohara_items3.sql')
DROP_OUT = os.path.join(REPO, 'linux-port', 'docker', 'game', 'yohara_maps3', 'mob_drop_item.yohara_maps3.txt')
SIG_OUT = os.path.join(REPO, 'linux-port', 'docker', 'game', 'yohara_maps3', 'special_item_group.yohara_maps3.txt')
JSON_OUT = os.path.join(HERE, 'yohara_items3.json')
ICON_OUT = os.path.join(REPO, 'client-patches', 'client-2.0.30', 'root', 'icon', 'item')
ITEMS1_JSON = os.path.join(REPO, 'tools', 'yohara_items', 'yohara_items.json')
# icons our client packs already have, byte for byte the GF ones (client 2.0.61 packs icon, newpet, wiki_nowe -
# checked 14 October 2026): not added again
HAVE_ICONS = set(('30300.tga', '30616.tga', '30617.tga', '30618.tga', '31270.tga', '50527.tga', '55001.tga'))

ST = Y.ST
TYPES = dict(Y.TYPES, ITEM_TREASURE_BOX=20, ITEM_TREASURE_KEY=21, ITEM_PET=37, ITEM_RESOURCE=14)
SUBTYPES = dict(Y.SUBTYPES, USE_CHANGE_ATTRIBUTE2=0)


def need(s):
    return 'needs: ' + s


ITEMS = []
# the second batch's items (MT2009_PLUS_YOHARA_ITEMS2_V1, tools/yohara_items/yohara_items2.json on claude/yohara-3):
# ours already when this batch is merged - named, never added again (an add() of one is skipped)
MAPS2_ITEMS = {50641: 'Ruda Jadeitu Slonca', 50642: 'Ruda Jadeitu Nocy', 50643: 'Ruda Jadeitu Dymu', 50644: 'Ruda Jadeitu Mgly', 50663: 'Jadeit Dymu', 31228: 'Luska Argosa', 31233: 'Kamien Wezowy', 31234: 'Kamien Wezowy+', 31257: 'Wzor Wezowy', 31258: 'Jedwab Wezowy', 70428: 'Pyl Wezowy', 31236: 'Biala Smocza Luska', 31237: 'Kamien Duchowy Pln. W.', 31242: 'Kamien Broni Pln. Wiatru', 31243: 'Kamien Broni Pln. W+', 31244: 'Kamien Rekawic Pln. W.', 31259: 'Kowadlo Pln. Wiatru', 31263: 'Kamien Szlif. Pln. W.', 31239: 'Polyskujaca Biala Perla', 31240: 'Polyskujaca Nieb. Perla', 31241: 'Polyskujaca Krwawa Perla', 31238: 'Polyskujaca Muszla', 95735: 'Piorunowe Ziolo', 95736: 'Kwiat Polnocnego Wiatru', 50737: 'Ziemne Pnacze', 50739: 'Pusty Eliksir Mocy', 50740: 'Pusty Eliksir Odp.', 83065: 'Losowa Skrzynia Skarbow', 83066: 'Los. Klucz do Skrz. Sk.', 83067: 'Skrzynia z Bransoletka', 83054: 'Idealny Klucz', 70410: 'Zamarzniety Klucz', 50527: 'Mikstura Talentu', 50336: 'Ksiega Misji (W.Pln.W.)', 72740: 'Licencja Najemnika', 49991: 'Ognista Runa Aury (10)', 49992: 'Ognista Runa Aury (50)', 49993: 'Ognista Runa Aury (100)', 70401: 'Sztandar Czaszki', 55003: 'Ksiega Mlodego Zwierza', 55050: 'Jazda (Zwinne Kopyta)', 55051: 'Jazda Konna (PD)', 55052: 'Jazda (Gwalt. Wichura)', 55053: 'Jazda (Bezszelest. Chod)', 55054: 'Jazda (Niesmiertelnosc)', 55055: 'Jazda (Brak Odrzutu)', 55056: 'Jazda Konna (losowo)', 55057: 'Jazda Konna (Wojownik)', 55058: 'Jazda Konna (Ninja)', 55059: 'Jazda Konna (Sura)', 55060: 'Jazda Konna (Szaman)', 55061: 'Jazda Konna (Likan)', 55062: 'Jazda (umiej. konne)', 55063: 'Jazda (W. SungMa. SILA)', 55064: 'Jazda (W. SungMa. WIT)', 55065: 'Jazda (W. SungMa. ODP)', 55066: 'Jazda (W. SungMa. INT)', 55067: 'Jazda Konna (Precyzja)'}


def add(vnum, src=None, name=None, status=ST, **over):
    if vnum in MAPS2_ITEMS:
        return
    ITEMS.append(dict(vnum=vnum, src=src or vnum, name=name, status=status, over=over))


INERT = dict(type='ITEM_MATERIAL', subtype='MATERIAL_LEATHER', wear='NONE', refined=0, refine_set=0)
QUEST = dict(type='ITEM_QUEST', subtype='QUEST_NONE')

# -- Zejscie / Glebie Polnocnego Wiatru ------------------------------------------------------------------------
NW = 'the Northwind crafting (the white dragon\'s weapons and armour, Kowal Skor 20828) - none here yet'
for v in (31235, 31236, 31237, 31242, 31243, 31244, 31259, 31263):
    add(v, status=need(NW))
for v in (31239, 31240, 31241):                                   # Polyskujace Perly
    add(v, status=need(NW + '; Polyskujaca Muszla gives them'))
for v in (30616, 30617, 30618):                                   # Dwutlenek Tytanu, Agat, Kamien Ksiezycowy
    add(v, status=need('the mined stones\' crafting (Yohara jewellery) - none here yet'))
add(31238)                                                        # Polyskujaca Muszla - chest (the pearls)
add(50663, status=need(Y.JADE))                                   # Jadeit Dymu
ELIXIR = 'the Sung Ma elixirs (Eliksir Woli SungMa, herbalism) - none here yet'
add(50739, status=need(ELIXIR))
add(50740, status=need(ELIXIR))
add(95735, src=50735, status=need(Y.HERBS + '; 50735 is our Korzen Weza, so 95735'))   # Piorunowe Ziolo
add(50527, status=need('Mikstura Talentu (the 9th skills\' talent) - none here yet'), **INERT)
add(70401, status=need('Sztandar Czaszki (the guild\'s Alastor) - none here yet'))
add(70410)                                                        # Zamarzniety Klucz - Glebie (quest ymaps3_glebie)
add(70411, name='B. Smocza Skrz. (lekka)')                        # wiki's names (Owsap's PL: slaby/silny)
add(70412, name='B. Smocza Skrz. (ciężka)')
add(72740, status=need('the mercenaries (Licencja Najemnika) - none here yet'), **INERT)
add(55001, status=need('the official pets (Odzywka) - none here yet'), **INERT)
AURA = 'the aura costume (Ognista Runa Aury) - none here yet'
add(49992, status=need(AURA), **INERT)
add(49993, status=need(AURA), **INERT)
HORSE = 'the horse skills 285-311 (Jazda ...) - none here yet'
for v in range(55050, 55068):
    if v != 55061:                                                # 55061 Jazda Konna (Likan) - no Lycan here
        add(v, status=need(HORSE), **INERT)
# the treasure boxes and their keys (ITEM_TREASURE_BOX / _KEY - char_item.cpp opens a box with the key of the same
# value0): Skrzynia z Bransoletka and the Id. Skrzynie (4) with Idealny Klucz, Plat. Skrzynia Skarbow (5) with its key
for v in (83051, 83052, 83053):                                   # Id. Skrzynie (Idealny Klucz 83054 - batch 2)
    add(v)
# -- Swiatynia Wezy ----------------------------------------------------------------------------------------------
SERPENT = 'the serpent weapons and armour (Zbroje / Bronie Wezowe, the crafting at Statua Wezy) - none here yet'
for v in (31233, 31234, 31257, 31258, 31262):
    add(v, status=need(SERPENT))
for v in (376, 396, 1226, 2246, 3266, 5216, 6166, 7346, 21326, 21346, 21366, 21386, 21406):    # "(wykon.)"
    add(v, status=need(SERPENT))
add(70428, **QUEST)                                               # Pyl Wezowy: +1 min in the temple (quest)
for v in (70422, 70423, 70424, 70425, 70426, 70427):              # Klucz Wezowy, Odlamki Weza, Klucz do Wiezienia
    add(v, **QUEST)
add(70429)                                                        # Skarb Wezy - chest
add(70430, **QUEST)                                               # Wejscie Do Swiatyni Wezy: today's entries again
add(28047, status=need(Y.GLOVES + ' (a Sung Ma stone; our engine has no METIN_SUNGMA)'), **INERT)
# -- Tajemnicza Instancja ---------------------------------------------------------------------------------------
add(31261)                                                        # Tajemniczy Kamien - Tajemniczy Oltarz (quest)
add(31270)                                                        # Esencja Talizmanu - Tajemniczy Oltarz (quest)
add(81560, name='Tajemniczy Talizman+0', status=need('its random bonus table (Owsap\'s apply_random 28) and the '
                                                      'refine to +1..; a level-120 talisman without bonus here'),
    refined=0, refine_set=0)
GUILD = 'the guild buildings\' "+" materials - none here yet'
for v in (90015, 90016, 90017):
    add(v, status=need(GUILD), **INERT)
# -- Krolestwo Zywiolow ------------------------------------------------------------------------------------------
SETFX = 'the set effects (Kowale Zestawu 20475-20479 in the port) - none here yet'
for v in list(range(39085, 39109)) + [39110, 39111, 39112]:
    add(v, status=need(SETFX))
add(39113, **QUEST)                                               # Medal Sily Natury: 10 min on the plateau (quest)
# MT2009_PLUS_YOHARA_REALM_V2 (fix 3.0 #13b): Pierscien Sily Natury does not stack (pl-wiki item page: Laczenie - Nie;
# trade with an NPC only, no storehouse / mail, as GF's antiflags already are)
add(39114, nostack=True, **QUEST)                                 # Pierscien Sily Natury: to the plateau (quest)
add(39116, name='Pierścień Siły Natury (100%)', **QUEST)
# MT2009_PLUS_YOHARA_REALM_V2 (fix 3.0 #13b): the rings' descriptions say how the plateau is reached here (the chance,
# where they work, where they drop) - the official text alone left the owner looking for the way in
DESC = {
    39114: 'Użyj pierścienia w Królestwie Żywiołów (na jednym z dziewięciu obszarów), by zyskać szansę (10%) '
           'teleportowania się na Płaskowyż Siły Natury. Pierścień znika przy każdym użyciu. Wypada ze wszystkich '
           'potworów i Metinów Królestwa Żywiołów (wejście: portal i Staruszek w Porcie Nowego Kontynentu).',
    39116: 'Użyj pierścienia w Królestwie Żywiołów (na jednym z dziewięciu obszarów), by zawsze teleportować się '
           'na Płaskowyż Siły Natury. Pierścień znika po użyciu.',
}

# items we have (official vnums or ours - see the notes): their names in the drop file
EXISTING = {
    250: 'Demoniczne Ostrze', 3150: 'Zlodziej Dusz', 190: 'Lwi Miecz', 180: 'Zatruty Miecz', 7150: 'Ekstazyjny Wachlarz',
    5120: 'Bambusowy Dzwon', 1130: 'Skrzydla Demona Chakr.', 2180: 'Luk Niebieskiego Smoka', 170: 'Miecz Zadlo',
    1120: 'Noz Siamese', 2170: 'Stalowy Luk Kruka', 50662: 'Jadeit Nocy', 50661: 'Jadeit Slonca', 50664: 'Jadeit Mgly',
    95734: 'Mrozny Korzonek', 31246: 'Wzor Rekawicy', 31247: 'Czerwona Runa SungMa', 31248: 'Liliowa Runa SungMa',
    31249: 'Niebieska Runa SungMa', 31250: 'Zielona Runa SungMa', 31251: 'Utwardzacz Skory', 31252: 'Utwardzacz Skory+',
    50529: 'Skrzynia Ksiag (9.skill)', 70050: 'Symbol Krola Przepowiedni', 50124: 'Sprochniala Skrzynia',
    39078: 'Szary Lsniacy Odlamek', 39079: 'Zielony Lsniacy Odlamek', 39080: 'Zolty Lsniacy Odlamek',
    39081: 'Swiety Fragment (120)', 27992: 'Biala Perla', 27993: 'Niebieska Perla', 27994: 'Krwawa Perla',
    72353: 'Topaz Woli', 50513: 'Kamien Duchowy', 90006: 'Kamien Duszy', 28046: 'Kamien Demonow+0',
    71015: 'Pierscien Doswiadczenia', 72006: 'Rekawica Zlodzieja (3 h)', 70434: 'Zwoj Skarbu (Stopien A)',
    81000: 'Talizman Woli SILA+0', 81300: 'Talizman Woli WIT+0', 81250: 'Talizman Woli ODP+0', 81550: 'Talizman Woli INT+0',
    31216: 'Plyta z Surowego Metalu', 31218: 'Plyta ze Stali Kuzniczej', 31224: 'Plyta ze Stali Ozdobnej',
    31217: 'Rog Trolla', 95601: 'Stabilne Sznury', 72354: 'Przenosna Zyla Jadeitu', 50325: 'Ksiega Precyzji',
    50300: 'Ksiega Umiejetnosci', 70014: 'Pigulka Krwi', 50528: 'Szkatulka Yohara', 39068: 'Zdobna Skrz. z Odlamkiem',
    95926: 'Kamyki', 27007: 'Czerwona Mikstura (XXL)', 27008: 'Niebieska Mikstura (XXL)', 70037: 'Ksiega Zapomnienia',
    50525: 'Kamien Duchowy+', 50043: 'Klucz Nimfy Wodnej', 76029: 'Zielona Smocza Fasola', 70408: 'Tajemniczy Bilet',
    50338: 'Charyzma Nowicjusza', 50341: 'Inspiracja Nowicjusza', 50569: 'Trzesienie (9.skill)',
    50570: 'Swiatlo Gwiazd (9.skill)', 50571: 'Strzal Wichury (9.skill)', 50572: 'Piekielny Cios (9.skill)',
    50573: 'Fala Smierci (9.skill)', 50574: 'Meteor (9.skill)', 50575: 'Tarcza Eteru (9.skill)',
    50323: 'Skrzynia Ksiag: Riposta', 50324: 'Skrzynia Ksiag: Dopalacz', 71019: 'Blogoslawienstwo Magii',
    71018: 'Blogoslawienstwo Zycia', 71020: 'Blogoslawienstwo Smoka', 71083: 'Ksiega Obrobki Kamienia',
    39004: 'Kula Blogoslawienstwa', 71130: 'Przepustka', 71085: 'Wzmocnienie Przedmiotu', 71084: 'Zaczarowanie Przedmiotu',
    71001: 'Zwoj Egzorcyzmu', 71025: 'Kamien Kowala', 100700: 'Smoczy Plomien (B)', 85003: 'Szarfa Wladcy (zacna)',
    25040: 'Zwoj Blogoslawienstwa', 72058: 'Pakiet Kamieni Duszy', 71004: 'Medal Smoka', 71017: 'Medal Szczescia',
    71101: 'Mikstura Pospiechu', 71068: 'Pioro Ptaka Milosci', 70043: 'Rekawica Zlodzieja', 71008: 'Rybie Wnetrznosci',
    71044: 'Dlon Krytyka', 31226: 'Skazony Rdzen', 31227: 'Kiel Argosa', 70024: 'Marmur Blogoslawienstwa',
    50037: 'Heksagonalna Szkatulka', 50249: 'Skrzynia Triumfu', 50007: 'Srebrna Szkatulka', 50006: 'Zlota Szkatulka',
    50009: 'Srebrny Klucz', 50008: 'Zloty Klucz', 27990: 'Kawalek Kamienia', 70048: 'Peleryna Maskujaca',
    30006: 'Zab Orka', 30047: 'Ksiega Klatw', 30015: 'Pamiatka Po Demonie', 30050: 'Lodowa Kulka',
    30165: 'Konar Zelkova', 30166: 'Certyfikat Tugyisa', 30168: 'Notatka Przywodcy', 30251: 'Klejnot Zawisci',
    30252: 'Klejnot Madrosci', 30053: 'Niedzwiedzia Skora', 30031: 'Ornament', 30194: 'Orkowa Maczuga',
    30195: 'Piasek Kwarcowy', 30061: 'Zabie Udka', 30058: 'Worek Z Pajeczymi Jajami', 30010: 'Zolc Niedzwiedzia',
    27987: 'Malz', 'gold': 'Yang',
    # MT2009_PLUS_YOHARA_ITEMS4_V1 (tools/yohara_maps4/gen_yitems4.py, yohara_items4.sql)
    72339: 'Kamien Metin z Yohara', 95737: 'Przeb. Ksiega Zwierza',
}
EXISTING.update(MAPS2_ITEMS)
# items of the second batch this one gives their use: Pyl Wezowy (70428) adds a minute in Swiatynia Wezy (quest
# swiatynia_wezy) - the second batch made it an inert material (it had no temple); a quest-use item here (Owsap:
# USE_SPECIAL, a quest use). The server: an idempotent UPDATE; the client: patch_ymaps3_client.item_proto ('retype').
RETYPE = {70428: dict(type=18, subtype=0, flag_or=1024,
                      desc='70428\tPył Wężowy\tUżyj go w Świątyni Węży, aby przedłużyć czas wyprawy o minutę '
                           '(najwyżej do 60 minut).')}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--owsap', default='/opt/metin2/cache/owsap')
    ap.add_argument('--gf', default='/opt/metin2/cache/gf/Gameforge_26.1.11/_client')
    a = ap.parse_args()
    rows = Y.read_tsv(os.path.join(a.owsap, 'Server/Server/db/item_proto.txt'))
    head = rows[0]
    proto = dict((int(r[0]), dict(zip(head, r))) for r in rows[1:] if r and r[0].isdigit())
    desc = {}
    for r in Y.read_tsv(os.path.join(a.owsap, 'Client/Client/pack/locale/locale/pl/itemdesc.txt')):
        if len(r) >= 2 and r[0].strip().isdigit():
            desc[int(r[0])] = (r[1].strip(), r[2].strip() if len(r) > 2 else '')
    gf_list = {}
    for r in Y.read_tsv(os.path.join(a.gf, 'shared/common/item_list.txt')):
        if len(r) >= 3 and r[0].strip().isdigit():
            gf_list[int(r[0])] = r[2].strip()
    items1 = set(i['vnum'] for i in json.load(open(ITEMS1_JSON, encoding='utf-8'))['items'])
    items = []
    for it in ITEMS:
        assert it['vnum'] not in items1, it['vnum']
        o = proto[it['src']]
        ov = it['over']
        pl, text = desc.get(it['src'], ('', ''))
        name = it['name'] or pl
        assert name and len(name.encode('cp1250')) <= 32, (it['vnum'], name)
        typ = TYPES[ov.get('type', o['Type'])]
        sub = SUBTYPES.get(ov.get('subtype', o['SubType']), 0) if ov.get('subtype', o['SubType']) not in (
            'UNK23_1', 'UNK23_2', 'UNK17_1') else 0
        if typ == 23 and o['SubType'] not in ('UNK23_1', '0'):
            raise SystemExit('%d: giftbox subtype %s' % (it['vnum'], o['SubType']))
        anti = Y.flags(o['AntiFlags'], Y.ANTI, 'antiflag')
        if it['status'] != ST:
            anti &= ~Y.ANTI_TRADE
        flag = Y.flags(o['Flags'], Y.FLAGS, 'flag')
        if ov.get('nostack'):
            flag &= ~Y.FLAGS['ITEM_STACKABLE']
        if typ == 18:
            flag |= Y.FLAGS['ITEM_QUEST_USE']
        wear = Y.flags(ov.get('wear', o['WearFlags']), Y.WEAR, 'wearflag')
        refined = ov.get('refined', int(o['RefinedVnum']))
        refine_set = ov.get('refine_set', int(o['RefineSet']))
        lim = []
        for k in (0, 1):
            t = o['LimitType%d' % k]
            lim.append((Y.LIMITS.get(t, 0) if t != 'NEWWORLD_LEVEL' else 0, int(o['LimitValue%d' % k])
                        if t != 'NEWWORLD_LEVEL' else 0))
        for i in range(3):
            t = o['ApplyType%d' % i]
            if t not in ('A_NONE', 'APPLY_NONE', 'A_RANDOM', 'APPLY_RANDOM'):
                raise SystemExit('%d: apply %s not mapped' % (it['vnum'], t))
        values = [int(o['Value%d' % i]) for i in range(6)]
        if typ == 5:                                    # an inert material keeps no values
            values = [0] * 6
        stackable = bool(flag & Y.FLAGS['ITEM_STACKABLE'])
        icon = gf_list.get(it['src'])
        assert icon, it['vnum']
        icon_file = os.path.basename(icon)
        if it['vnum'] != it['src']:
            icon_file = '%d.tga' % it['vnum']
        items.append(dict(
            vnum=it['vnum'], src=it['src'], status=it['status'], name=Y.ascii_name(name), locale_name=name,
            type=typ, subtype=sub, stack=200 if stackable else 1, weight=0, size=int(o['Size']), antiflag=anti,
            flag=flag, wearflag=wear, gold=int(o['ShopBuyPrice']), shop_buy_price=int(o['ShopSellPrice']),
            refined_vnum=refined, refine_set=refine_set, magic_pct=int(o['AlterToMagicItemPercent']),
            specular=int(o['Specular']), socket_pct=int(o['GainSocketPercent']), addon_type=0,
            limittype0=lim[0][0], limitvalue0=lim[0][1], limittype1=lim[1][0], limitvalue1=lim[1][1],
            applytype0=0, applyvalue0=0, applytype1=0, applyvalue1=0, applytype2=0, applyvalue2=0,
            **dict(('value%d' % i, values[i]) for i in range(6)),
            icon='icon/item/' + icon_file, icon_src=icon, desc=DESC.get(it['vnum'], text),
            list_type='ARMOR' if typ == 2 else 'ETC'))
    byv = dict((i['vnum'], i) for i in items)
    assert len(byv) == len(items)
    write_sql(items)
    write_json(items)
    copy_icons(items, a.gf)
    write_sig(byv)
    write_drops(byv)
    print('items %d (%d work, %d need a system)' % (len(items), sum(1 for i in items if i['status'] == ST),
                                                    sum(1 for i in items if i['status'] != ST)))
    for i in items:
        if i['status'] != ST:
            print('  %d %s: %s' % (i['vnum'], i['name'], i['status']))


def write_sql(items):
    L = ['-- MT2009_PLUS_YOHARA_MAPS3_V1: the items of the third batch of Yohara places (Zejscie/Glebie Polnocnego Wiatru,',
         '-- Swiatynia Wezy, Tajemnicza Instancja, Krolestwo Zywiolow) that our world did not have - drops, the dungeons\'',
         '-- keys and rewards, the chests. GENERATED by tools/yohara_maps3/gen_yitems3.py - do not edit, rerun it. Every',
         '-- start (apply.sh), idempotent: INSERT IGNORE. Source: Owsap v6.2.6 db/item_proto.txt (the official vnums and',
         '-- numbers), the Polish names of its Polish client; every vnum free in our world (a throwaway world after the',
         '-- whole apply.sh, 14 October 2026); Piorunowe Ziolo is 95735 (our 50735 is Korzen Weza). An item whose system',
         '-- we do not have is an inert, tradeable material and does nothing yet - its row says what it waits for:']
    for i in items:
        if i['status'] != ST:
            L.append('--   %d %s - %s' % (i['vnum'], i['name'], i['status'][len('needs: '):]))
    L.append('SET NAMES utf8mb4;')
    L.append('INSERT IGNORE INTO world.item_proto (%s) VALUES' % ','.join('`%s`' % c for c in Y.COLS))
    L.append(',\n'.join(Y.sqlrow(i) for i in items) + ';')
    for v, r in sorted(RETYPE.items()):
        L.append('UPDATE world.item_proto SET type=%d, subtype=%d, flag=flag|%d WHERE vnum=%d AND (type<>%d OR '
                 'flag&%d=0);' % (r['type'], r['subtype'], r['flag_or'], v, r['type'], r['flag_or']))
    for i in items:                     # a non-stacking item of an earlier start (INSERT IGNORE keeps the old row)
        if i['stack'] == 1 and not i['flag'] & Y.FLAGS['ITEM_STACKABLE'] and i['vnum'] in NOSTACK_UPDATE:
            L.append('UPDATE world.item_proto SET flag=flag&~%d, stack=1 WHERE vnum=%d AND (flag&%d<>0 OR stack<>1);'
                     % (Y.FLAGS['ITEM_STACKABLE'], i['vnum'], Y.FLAGS['ITEM_STACKABLE']))
    with open(SQL_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')


NOSTACK_UPDATE = (39114,)


def write_json(items):
    keys = ('vnum', 'name', 'locale_name', 'type', 'subtype', 'stack', 'weight', 'size', 'antiflag', 'flag',
            'wearflag', 'gold', 'shop_buy_price', 'refined_vnum', 'refine_set', 'magic_pct', 'specular', 'socket_pct',
            'limittype0', 'limitvalue0', 'limittype1', 'limitvalue1', 'applytype0', 'applyvalue0', 'applytype1',
            'applyvalue1', 'applytype2', 'applyvalue2', 'value0', 'value1', 'value2', 'value3', 'value4', 'value5')
    out = {'items': [dict((k, i[k]) for k in keys) for i in items],
           'item_list': dict((str(i['vnum']), '%d\t%s\t%s' % (i['vnum'], i['list_type'], i['icon'])) for i in items),
           'itemdesc': dict((str(i['vnum']), '%d\t%s\t%s' % (i['vnum'], i['locale_name'], Y.client_desc(i)))
                            for i in items),
           # Tajemniczy Bilet (70408, MT2009_PLUS_YOHARA_ITEMS1_V1) works now: Tajemniczy Oltarz on Namgan
           'itemdesc_replace': dict([('70408', '70408\tTajemniczy Bilet\tPokaż go Tajemniczemu Ołtarzowi w Namgan, '
                                                  'aby wejść do Tajemniczej Instancji.')] +
                                    [(str(v), r['desc']) for v, r in RETYPE.items()]),
           'retype': dict((str(v), dict(type=r['type'], subtype=r['subtype'], flag_or=r['flag_or']))
                          for v, r in RETYPE.items())}
    with open(JSON_OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=0)
        f.write('\n')


def copy_icons(items, gf):
    os.makedirs(ICON_OUT, exist_ok=True)
    for i in items:
        if os.path.basename(i['icon']) in HAVE_ICONS:
            continue
        dst = os.path.join(ICON_OUT, os.path.basename(i['icon']))
        src = os.path.join(gf, i['icon_src'].replace('\\', '/'))
        assert os.path.isfile(src), src
        if not os.path.exists(dst):
            shutil.copyfile(src, dst)


def nm(byv, v, c=1):
    n = byv[v]['name'] if v in byv else EXISTING[v]
    return n + (' x%d' % c if c > 1 else '')


# MT2009_PLUS_YOHARA_SETS_V1: the serpent and Dark Dragon weapons and the dragon armours +0 of B. Smocza Skrz. (ciezka)
# (pl-wiki), linux-port/docker/mariadb/playerbot/yohara_sets.sql (tools/ysets/gen_ysets.py) - the Lycan's left out
YSETS_GEAR = [(v, 1, 5) for v in (5200, 7330, 1210, 2230, 360, 380, 3250, 5170, 7310, 1190, 2210, 320, 340, 3230,
                                  21230, 21250, 21270, 21210)]
EXISTING.update({5200: 'Dzwon Wezowy+0', 7330: 'Wachlarz Wezowy+0', 1210: 'Sztylet Wezowy+0', 2230: 'Luk Wezowy+0',
                 360: 'Miecz Wezowy+0', 380: 'Ostrze Wezowe+0', 3250: 'Wielki Miecz Wezowy+0',
                 5170: 'Dzwon Smoka Mroku+0', 7310: 'Wachlarz Smoka Mroku+0', 1190: 'Sztylet Smoka Mroku+0',
                 2210: 'Luk Smoka Mroku+0', 320: 'Miecz Smoka Mroku+0', 340: 'Brzeszczot Smoka Mrok+0',
                 3230: 'Ostrze Smoka Mroku+0', 21230: 'Zbroja Smoka Wiatru+0', 21250: 'Zbroja Smoka Magii+0',
                 21270: 'Zbroja Boskiego Smoka+0', 21210: 'Zbroja Smoka Mroku+0'})


# -- the chests (special_item_group): one thing an opening, by weight; what our world lacks is left out ------------
def chests(byv):
    g = []
    serp = [(v, 1, 10) for v in (376, 396, 1226, 2246, 3266, 5216, 6166, 7346)]
    light = [(30617, 1, 20), (31235, 1, 20), (31236, 1, 20), (71019, 1, 20), (71018, 1, 20), (31242, 10, 30),
             (31243, 10, 20), (28046, 1, 20), (31237, 1, 20), (30618, 1, 20), (31244, 1, 20), (31263, 1, 20),
             (95926, 200, 30), (71083, 1, 15), (50325, 1, 15), (39004, 1, 15), (72740, 1, 10), (50527, 1, 10),
             (71130, 1, 15), (72353, 1, 30), (71085, 1, 15), (71084, 1, 15), (71001, 1, 15), (39081, 1, 10),
             (31239, 1, 15), (31240, 1, 15), (31241, 1, 15), (31238, 1, 15), (55001, 1, 10)] + serp
    g.append((70411, 'B. Smocza Skrz. (lekka) - left out: Losowa Skrzynka, Szklo Handlu, Male Blogoslawienstwo, '
                     'Torba Emocji, Kamien Mocy Demonow (no system)', light))
    heavy = [(30617, 1, 20), (31235, 1, 20), (31236, 1, 20), (71019, 6, 15), (71020, 6, 15), (71018, 6, 15),
             (30616, 1, 20), (50663, 1, 15), (50662, 1, 15), (31242, 15, 30), (31243, 15, 20), (28046, 1, 20),
             (31237, 1, 20), (71025, 1, 15), (30618, 1, 20), (31244, 7, 20), (31263, 5, 20), (95926, 200, 30),
             (39004, 1, 15), (50325, 1, 15), (72740, 1, 10), (50527, 1, 10), (55001, 1, 10), (49993, 1, 5),
             (31239, 1, 15), (31240, 1, 15), (31241, 1, 15), (31238, 1, 15), (71130, 1, 15), (72353, 6, 30),
             (100700, 1, 5), (39081, 1, 10), (71085, 1, 15), (71084, 1, 15)] + serp + YSETS_GEAR
    g.append((70412, 'B. Smocza Skrz. (ciezka) - left out: the Lycan\'s Szpon Wezowy / Pazur Smoka Mroku / Zbroja Smoka '
                     'Nieba, Biale Jajo Smoka (pet), Dumny Smok Pln. Wiatru (mount), Szklo Handlu, Male '
                     'Blogoslawienstwo, Osobisty Sklepik Premium', heavy))
    treasure = [(50662, 1, 20), (31258, 2, 20), (21346, 1, 10), (28046, 1, 20), (28047, 1, 10), (31233, 10, 20),
                (31234, 10, 15), (95926, 200, 30), (71083, 1, 15), (50325, 1, 15), (39004, 1, 15), (72740, 1, 10),
                (50527, 1, 10), (21406, 1, 10), (55001, 1, 10), (72058, 1, 15), (21326, 1, 10), (31216, 3, 20),
                (31218, 3, 20), (31224, 3, 20), (31262, 5, 20), (31239, 1, 15), (31241, 1, 15), (31238, 1, 15),
                (31240, 1, 15), (72354, 1, 10), (71130, 1, 15), (31217, 3, 20), (100700, 1, 5), (85003, 1, 2),
                (39081, 1, 10), (72353, 6, 30), (31257, 5, 20), (21386, 1, 10), (71084, 1, 15), (21366, 1, 10),
                (25040, 1, 15), (71001, 1, 15), (71085, 1, 15)]
    g.append((70429, 'Skarb Wezy - left out: Losowa Skrzynka, Osobisty Sklepik Premium, Szklo Handlu, Male '
                     'Blogoslawienstwo, Torba Emocji (no system)', treasure))
    perfect = [(31226, 1, 10), (31227, 1, 10), (31216, 1, 10), (31217, 1, 10), (50664, 1, 10), (50662, 1, 10),
               (50661, 1, 10), (25040, 1, 10), (70024, 1, 10), (71004, 1, 10), (71015, 1, 10), (70043, 1, 10),
               (71017, 1, 10), (71008, 1, 10), (71068, 1, 10), (31238, 1, 10), (71018, 1, 10), (71019, 1, 10),
               (72339, 1, 10)]
    g.append((83053, 'Id. Skrzynia Kolczykow (Idealny Klucz) - left out: the jade earrings, Luska Argosa', perfect))
    g.append((83052, 'Id. Skrzynia Naszyjniku (Idealny Klucz) - left out: the jade necklaces, Luska Argosa', perfect))
    tal = [(81000, 1, 10), (81300, 1, 10), (81250, 1, 10), (81550, 1, 10), (72353, 1, 20), (71044, 1, 10),
           (71004, 1, 10), (71015, 1, 10), (70043, 1, 10), (71017, 1, 10), (71008, 1, 10), (71068, 1, 10),
           (31238, 1, 10), (71018, 1, 10), (71019, 1, 10)]
    g.append((83051, 'Id. Skrzynia Talizmanu (Idealny Klucz)', tal))
    out = []
    for vnum, title, rows in g:
        rr = []
        for r in rows:
            v, c, w = r[:3]
            if v != 'gold':
                assert v in byv or v in EXISTING, (vnum, v)
            rr.append((v, c, w, (EXISTING['gold'] + ' %d' % c) if v == 'gold' else nm(byv, v, c)))
        out.append((vnum, title, rr))
    return out


def write_sig(byv):
    L = ['# MT2009_PLUS_YOHARA_MAPS3_V1: the chests of the third batch of Yohara places - their contents as on their',
         '# pl-wiki pages (B. Smocza Skrz., Skarb Wezy, Polyskujaca Muszla, the treasure boxes), one thing an opening, by',
         '# weight (ours: the wiki gives no odds). GENERATED by tools/yohara_maps3/gen_yitems3.py - do not edit.',
         '# Appended to special_item_group.txt by the Dockerfile (share: Yohara - the third batch).', '']
    for vnum, title, rows in chests(byv):
        L.append('Group\tMT2009_yitems3_%d' % vnum)
        L.append('{')
        L.append('\tVnum\t%d -- %s' % (vnum, title))
        for k, (v, c, w, n) in enumerate(rows, 1):
            L.append('\t%d\t%s\t%d\t%d -- %s' % (k, v, c, w, n))
        L.append('}')
        L.append('')
    with open(SIG_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L))


# -- the drops (mob_drop_item, Type drop: vnum, count, percent) ----------------------------------------------------
# Official-like rarity: an ordinary monster's material 0.1-0.4 %, a chest or a rare stone 0.02-0.1 %, a Talizman Woli
# 0.05 %; a boss's things 2-30 %, a Metin's 5-50 % (the test server's 500% event multiplies these; not compensated).
WEAP = lambda vs, p=0.1: [(v, 1, p) for v in vs]  # noqa: E731
RUNES = [(31246, 1, 0.15), (31247, 1, 0.08), (31248, 1, 0.08), (31249, 1, 0.08), (31250, 1, 0.08)]
LEATHER = [(31251, 1, 0.15), (31252, 1, 0.08)]
NW_BASE = [(31238, 1, 0.1), (50662, 1, 0.1), (50663, 1, 0.1), (31244, 1, 0.15), (95734, 1, 0.5),
           (50739, 1, 0.15), (50740, 1, 0.15), (50529, 1, 0.03), (83067, 1, 0.03), (83054, 1, 0.03),
           (70050, 1, 0.1), (50124, 1, 0.1)]
LUCENT = [(39078, 1, 0.04), (39079, 1, 0.04), (39080, 1, 0.04), (39081, 1, 0.02)]
WILL = [(v, 1, 0.05) for v in (81000, 81300, 81250, 81550)]
YOH_UPG = [(72353, 1, 0.4), (31216, 1, 0.25), (31218, 1, 0.25), (31224, 1, 0.25), (31217, 1, 0.25)]
TREASURE_BOX = [(83065, 1, 0.03), (83066, 1, 0.03)]
SERP_MAT = [(31257, 1, 0.15), (31258, 1, 0.15), (70428, 1, 0.3)]
PERFECT = [(83053, 1, 0.03), (83052, 1, 0.03), (83051, 1, 0.03), (83054, 1, 0.03), (83067, 1, 0.03)]
SET1 = [(v, 1, 0.05) for v in (39085, 39086, 39087, 39091, 39092, 39093, 39097, 39098, 39099)]
SET2 = [(v, 1, 3) for v in (39088, 39089, 39090, 39094, 39095, 39096, 39100, 39101, 39102)] + \
       [(v, 1, 1) for v in (39103, 39104, 39105, 39106, 39107, 39108)]
PROJECT = [(39110, 1, 0.05), (39111, 1, 0.05), (39112, 1, 0.05)]
NATURE = [(39114, 1, 0.1), (39113, 1, 0.1)]


def drops():
    d = []
    w_sold = WEAP((250, 3150, 190, 180))
    d.append((6792, 'Zolnierz Schron. Pln. W. (lod, blyskawice)', w_sold + NW_BASE + RUNES + LEATHER))
    d.append((6793, 'Zadziora Schron. Pln. W. (lod, blyskawice)', WEAP((7150, 250, 5120, 190)) + NW_BASE + RUNES +
              LEATHER + [(31241, 1, 0.1), (31242, 1, 0.15)] + LUCENT))
    d.append((6794, 'Wojownik Schron. Pln. W. (lod, blyskawice)', WEAP((7150, 250, 3150, 5120, 190, 1130)) + NW_BASE +
              RUNES + LEATHER + [(31241, 1, 0.1), (31242, 1, 0.15), (31259, 1, 0.1)] + LUCENT))
    d.append((6795, 'Czarownik Sch. Pln. W. (lod, blyskawice)', WEAP((2180,)) + NW_BASE +
              [(27992, 1, 0.1), (27993, 1, 0.1), (27994, 1, 0.1)]))
    d.append((6796, 'General Schron. Pln. W. (lod, blyskawice)', WEAP((7150, 250, 3150, 5120, 190, 1130, 180)) +
              [(31239, 1, 0.2), (31240, 1, 0.2), (31241, 1, 0.2), (31259, 1, 0.2), (31244, 1, 0.2), (55001, 1, 0.1),
               (95734, 1, 0.3), (50739, 1, 0.15), (50740, 1, 0.15)]))
    d.append((6797, 'Wodz Wojenny Schronienia (lod, blyskawice)',
              WEAP((7150, 1120, 250, 2180, 170, 3150), 5) +
              [(30617, 1, 8), (31236, 1, 8), (30616, 1, 8), (31242, 1, 10), (31243, 1, 8),
               (31237, 1, 8), (31263, 1, 8), (30618, 1, 8), (49992, 1, 3), (49993, 1, 1), (31239, 1, 8),
               (31240, 1, 8), (31241, 1, 8), (39081, 1, 5), (72353, 1, 15), (72740, 1, 3), (50513, 1, 15),
               (90006, 1, 10), (28046, 1, 10), (50527, 1, 5), (71015, 1, 10), (95735, 1, 10), (72006, 1, 10),
               (50529, 1, 5), (83067, 1, 5), (70401, 1, 3), (70434, 1, 3), (95737, 1, 2)] +
              [(v, 1, 1) for v in range(55050, 55068) if v != 55061]))
    # Glebie: Alastor (TR wiki: Kamien Duchowy), the eggs (TR: Dumny Smok Pln. Wiatru - a mount, none here)
    d.append((6790, 'Alastor (slaby)', [(50513, 1, 30), (90006, 1, 20)]))
    d.append((6791, 'Alastor (silny)', [(50513, 2, 40), (90006, 1, 30)]))
    # 1. poziom Swiatyni Wezy
    d7 = WILL + YOH_UPG + [(95601, 1, 0.3)] + SERP_MAT + [(31238, 1, 0.1)] + LUCENT + [(72354, 1, 0.04),
                                                                                         (50527, 1, 0.02)] + \
        TREASURE_BOX
    for v, n in ((6748, 'Kappa Lowca'), (6747, 'Kappa Czarodziej'), (6746, 'Kappa Zolnierz (lvl-123)')):
        d.append((v, n, d7))
    d.append((6745, 'Kappa Robotnik', WILL + YOH_UPG + [(72354, 1, 0.04)] + TREASURE_BOX))
    d.append((6744, 'Kappa Zolnierz (lvl-124)', [(v, 1, 1) for v in (81000, 81300, 81250, 81550)] +
              [(72353, 1, 5), (31216, 1, 4), (31218, 1, 4), (31224, 1, 4), (31217, 1, 4), (31257, 1, 5),
               (31258, 1, 5), (50527, 1, 2), (72354, 1, 2), (83065, 1, 2), (83066, 1, 2)]))
    d.append((6749, 'Potezny Kappa', [(250, 1, 5), (190, 1, 5), (39078, 1, 5), (39079, 1, 5), (39080, 1, 5),
                                      (31247, 1, 5), (31249, 1, 5), (31248, 1, 5), (31250, 1, 5), (50527, 1, 3),
                                      (50663, 1, 5), (50662, 3, 5), (31258, 1, 8), (31216, 1, 8), (70428, 5, 10),
                                      (31257, 1, 8)] + [(v, 1, 2) for v in (81000, 81300, 81250, 81550)] +
              [(83065, 1, 3), (83066, 1, 3), (83053, 1, 2), (83052, 1, 2), (83051, 1, 2), (28046, 1, 5),
               (71025, 1, 5), (95926, 50, 10), (50325, 1, 5), (50300, 1, 10), (31238, 1, 5), (70014, 1, 10),
               (50529, 1, 3), (50528, 1, 5), (39068, 1, 3)]))
    d.append((8076, 'Metin Wezowy Przestrzeni', [(27007, 5, 50), (27008, 5, 50)] +
              [(v, 1, 1) for v in (50573, 50574, 50575, 50569, 50572, 50571, 50570)] +
              [(50341, 1, 5), (70037, 1, 5), (28046, 1, 5), (50513, 1, 20), (50525, 1, 3), (50300, 1, 20),
               (70014, 1, 20), (50043, 1, 3), (31238, 1, 5), (31258, 1, 5), (55001, 1, 3), (76029, 1, 5),
               (70428, 1, 10), (50663, 1, 5), (83053, 1, 2), (83052, 1, 2), (70408, 1, 3)]))
    # Swiatynia Wezy (the dungeon): TR wiki - the mighty warriors drop Pyl Wezowy, Nethis Kamien Duchowy; the keys
    # and the shards are the quest's (swiatynia_wezy.quest)
    d.append((6755, 'Potezny Wojownik Wezowy (lod)', [(70428, 1, 30)]))
    d.append((6765, 'Potezny Wojownik Wezowy (ziemia)', [(70428, 1, 30)]))
    d.append((6756, 'Krolowa Wezy Nethis', [(50513, 2, 50), (90006, 1, 30)]))
    # Tajemnicza Instancja
    d12 = WEAP((7150, 1120, 250, 2180, 3150, 5120, 1130, 190, 2170, 180), 0.05) + [(39078, 1, 0.04)] + WILL + \
        [(31216, 1, 0.25), (31218, 1, 0.25), (31224, 1, 0.25), (50527, 1, 0.02), (31217, 1, 0.25),
         (31238, 1, 0.1), (31261, 1, 8), (72353, 1, 0.4), (90015, 1, 0.05), (90016, 1, 0.05), (90017, 1, 0.05)] + \
        PERFECT + [(39068, 1, 0.03)]
    for v in (6860, 6861, 6862, 6863, 6865, 6866, 6867, 6868):
        d.append((v, D.MOBS[v][0].translate(str.maketrans('ąćęłńóśźżŁ', 'acelnoszzL')) +
                  (' (mrok)' if v < 6865 else ' (lod)'), d12))
    for v in (6864, 6869):
        d.append((v, 'Mistrz Miecza Kao' + (' (mrok)' if v < 6865 else ' (lod)'), [(31261, 1, 12)] + d12))
    for v in (6870, 6871):
        d.append((v, 'Tajemniczy Mnich' + (' (lod)' if v == 6870 else ' (mrok)'),
                  [(90006, 1, 20), (28046, 1, 10), (70408, 1, 10), (70434, 1, 5), (31261, 5, 30), (95737, 1, 2)]))
    # Krolestwo Zywiolow: the areas' monsters (D16), the Metins (D15), the plateau's lords (D17)
    d16 = [(27007, 5, 2)] + SET1 + NATURE + PROJECT
    for v in (3980, 3981, 3982, 3983, 3984, 3985, 3986, 3987, 3988, 3989, 3990, 3991, 4006):
        d.append((v, D.MOBS[v][0].translate(str.maketrans('ąćęłńóśźżŻŁŚ', 'acelnoszzZLS')), d16))
    d15 = [(39110, 1, 5), (39111, 1, 5), (39112, 1, 5)] + [(v, 1, 3) for v in (39097, 39091, 39085, 39098, 39092,
                                                                              39086, 39099, 39093, 39087)] + \
        [(50513, 1, 30), (39114, 1, 10), (39113, 1, 10)]
    for v in (4000, 4001, 4002, 4003, 4004, 4005):
        d.append((v, D.MOBS[v][0].translate(str.maketrans('ąćęłńóśźżŻŁŚ', 'acelnoszzZLS')), d15))
    d17 = [(27007, 5, 5)] + SET2 + [(50338, 1, 3), (50341, 1, 3), (39110, 1, 2), (39111, 1, 2), (39112, 1, 2)]
    for v in (3992, 3993, 3994, 3995, 3996, 3997):
        d.append((v, D.MOBS[v][0].translate(str.maketrans('ąćęłńóśźżŻŁŚ', 'acelnoszzZLS')), d17))
    return d


KEY_BOSSES = [(6797, 'Wodz Wojenny Schronienia (lod, blyskawice)')]


def write_drops(byv):
    L = ['// MT2009_PLUS_YOHARA_MAPS3_V1: drops of the third batch of Yohara places - the pl-wiki lists of each monster,',
         '// boss and Metin (the TR wiki where the Polish page has none) with the items yohara_items3.sql adds.',
         '// GENERATED by tools/yohara_maps3/gen_yitems3.py - do not edit. Owsap gives these monsters no drop. The',
         '// percents are ours, official-like - the second batch\'s scale (mob_drop_item.yohara_maps2.txt): a monster -',
         '// a Talizman Woli 0.05 each, Topaz Woli 0.4, a plate / Rog Trolla 0.25, the herb 0.5, a material 0.15, a',
         '// rare thing 0.03-0.1, Tajemniczy Kamien 8 (200 a Tajemniczy Talizman); a boss (hourly) 1-25; Zamarzniety',
         '// Klucz: exactly one a kill of Wodz Wojenny Schronienia (a "limit" group at 100 - the owner, 14 October);',
         '// a Metin\'s 1-50. Left out: Odlamki 39070-39077 (with the Seon-Hae event, as tools/yohara_items), the',
         '// Lycan\'s claws (Kolczasty / Jastrzebi Szpon), Mnisi Len and Odlamek Miecza Kao (no',
         '// vnum anywhere), Dumny Smok Pln. Wiatru (a mount), the eggs\' and Glebie\'s other drops (none on the wiki).', '']
    sys.path.insert(0, os.path.join(REPO, 'tools', 'yskill9'))
    import talent  # noqa: E402  (MT2009_PLUS_SKILL9_TALENT_V1: Mikstura Talentu's rows)
    for v, n, rows in talent.with_talent(drops()):
        assert v in D.MOBS, v
        L.append('Group\tMT2009_ymaps3_%d' % v)
        L.append('{')
        L.append('\tMob\t%d\t-- %s' % (v, n))
        L.append('\tType\tdrop')
        seen = set()
        k = 0
        for r in rows:
            iv, c, p = r[:3]
            if iv in seen:
                continue
            seen.add(iv)
            assert iv in byv or iv in EXISTING, (v, iv)
            k += 1
            L.append('\t%d\t%d\t%d\t%s\t-- %s' % (k, iv, c, '%g' % p, nm(byv, iv, c)))
        L.append('}')
        L.append('')
    # Zamarzniety Klucz (70410): exactly one from every Wodz Wojenny Schronienia (the owner, 14 October 2026) - a
    # "limit" group (item_manager: pct x 10000 against 1..1000000 - 100 is every kill, no level fade and no drop
    # event multiplies it), apart from the "drop" group above
    for v, n in KEY_BOSSES:
        L += ['Group\tMT2009_ymaps3_%d_klucz' % v, '{', '\tMob\t%d\t-- %s' % (v, n), '\tType\tlimit',
              '\tlevel_limit\t1', '\t1\t70410\t1\t100\t-- Zamarzniety Klucz (always one)', '}', '']
    with open(DROP_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L))


if __name__ == '__main__':
    main()
