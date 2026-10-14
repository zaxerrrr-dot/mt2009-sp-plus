#!/usr/bin/env python3
"""gen_edits.py [<game/src>] - writes edits.json of server-patches/obreczjadeitu2 (MT2009_PLUS_JADE_BRACELET_V2,
README.md) from the code below; the developer's tool (the apply scripts read edits.json only). With a game/src dir it
also checks the anchors. Applied after server-patches/obreczjadeitu (V1: its calls are replaced), precyzja
(POINT_HIT_PCT) and rekawice; the logic is the overlay's playerbot_yohara_gear.cpp (Mt2009JadeBracelet*V2*)."""
import json
import os
import sys

M = 'MT2009_PLUS_JADE_BRACELET_V2'
J = 'MT2009_PLUS_JADE_JEWELLERY_V1'
V1 = 'MT2009_PLUS_JADE_BRACELET_V1'

EDITS = [
    # V2: two lines (Precyzja, the Will of the jade) with the wiki's ranges in place of V1's one Will line
    dict(file='item_manager.cpp', marker=M + ' (new)',
         old='\t\tMt2009JadeBraceletCreate(item); // ' + V1 + ' (new): an Obrecz Jadeitu\'s Will line\n',
         new='\t\t{ // ' + M + ' (new): an Obrecz Jadeitu\'s two base lines (playerbot_yohara_gear.cpp; V1\'s one line no more)\n'
             '\t\t\tvoid Mt2009JadeBraceletV2Create(LPITEM);\n'
             '\t\t\tMt2009JadeBraceletV2Create(item);\n'
             '\t\t}\n'),
    dict(file='item_attribute.cpp', marker=M + ' (refine)',
         old='\tMt2009JadeBraceletRefine(this, pItem); // ' + V1 + ' (refine)\n',
         new='\t{ // ' + M + ' (refine): both lines carried to the new level (V1\'s Will line too)\n'
             '\t\tvoid Mt2009JadeBraceletV2Refine(LPITEM, LPITEM);\n'
             '\t\tMt2009JadeBraceletV2Refine(this, pItem);\n'
             '\t}\n'
             '\t(void) Mt2009JadeBraceletRefine; // ' + V1 + ' (refine): replaced by V2\n'),
    # the jade in the Diamond's sockets (the engine's accessory sockets) adds to the lines
    dict(file='item.cpp', marker=M + ' (socket points)',
         old='\tMt2009YSetsItemPoints(this, m_pOwner, bAdd); // MT2009_PLUS_YOHARA_SETS_V1 (points): a serpent piece\'s random base bonuses\n',
         new='\tMt2009YSetsItemPoints(this, m_pOwner, bAdd); // MT2009_PLUS_YOHARA_SETS_V1 (points): a serpent piece\'s random base bonuses\n'
             '\t{ // ' + M + ' (socket points): the jade in an Obrecz Jadeitu\'s sockets adds to its lines\n'
             '\t\tvoid Mt2009JadeBraceletSocketPoints(LPITEM, LPCHARACTER, bool);\n'
             '\t\tMt2009JadeBraceletSocketPoints(this, m_pOwner, bAdd);\n'
             '\t}\n'),
    dict(file='item.cpp', marker=M + ' (jewel)',
         old='\t\t{ 50639, 14570, 16570, 17570 },\n\t};\n',
         new='\t\t{ 50639, 14570, 16570, 17570 },\n'
             '\t\t// ' + M + ' (jewel): Jadeit Mgly / Slonca / Nocy / Dymu into their Obrecz Jadeitu only (pl-wiki\n'
             '\t\t// "Jadeit Mgly": into a pocket a Diamond made, at most 3; the jewellery of jade has no necklace or earrings here)\n'
             '\t\t{ 50664, 14580, 0, 0 },\n'
             '\t\t{ 50661, 14590, 0, 0 },\n'
             '\t\t{ 50662, 14600, 0, 0 },\n'
             '\t\t{ 50663, 14610, 0, 0 },\n'
             '\t};\n'),
    # MT2009_PLUS_JADE_JEWELLERY_V1 (the owner, 14 October: the necklaces and earrings of jade, pl-wiki "Kolia Jadeitu
    # ...", "Klipsy Jadeitu ..."): the same two lines and sockets - V1's type switch (its guards against the 6/7
    # changers, V2's create / refine / socket points all ask it) knows them; the ranges of each kind are the overlay's
    dict(file='item_attribute.cpp', marker=J + ' (types)',
         old='\t\tcase 14610: bWillType = POINT_SUNGMA_STR; return true;\n',
         new='\t\tcase 14610: bWillType = POINT_SUNGMA_STR; return true;\n'
             '\t\t// ' + J + ' (types): Kolia Jadeitu 16580-16619 and Klipsy Jadeitu 17570-17609 - the same Wills\n'
             '\t\tcase 16580: case 17570: bWillType = POINT_SUNGMA_MOVE; return true;\n'
             '\t\tcase 16590: case 17580: bWillType = POINT_SUNGMA_IMMUNE; return true;\n'
             '\t\tcase 16600: case 17590: bWillType = POINT_SUNGMA_HP; return true;\n'
             '\t\tcase 16610: case 17600: bWillType = POINT_SUNGMA_STR; return true;\n'),
    # the jade into its necklace / earrings too (Owsap's table); Turmalin's earrings row (17570, no such item here) is
    # Klipsy Jadeitu Mgly - out, as in Owsap's (the first row of a vnum decides)
    dict(file='item.cpp', marker=J + ' (turmalin)',
         old='\t\t{ 50639, 14570, 16570, 17570 },\n',
         new='\t\t{ 50639, 14570, 16570, 0 }, // ' + J + ' (turmalin): 17570 is Klipsy Jadeitu Mgly\n'),
    dict(file='item.cpp', marker=J + ' (jewel)',
         old='\t\t{ 50664, 14580, 0, 0 },\n\t\t{ 50661, 14590, 0, 0 },\n\t\t{ 50662, 14600, 0, 0 },\n'
             '\t\t{ 50663, 14610, 0, 0 },\n',
         new='\t\t// ' + J + ' (jewel): and into their Kolia / Klipsy Jadeitu\n'
             '\t\t{ 50664, 14580, 16580, 17570 },\n\t\t{ 50661, 14590, 16590, 17580 },\n'
             '\t\t{ 50662, 14600, 16600, 17590 },\n\t\t{ 50663, 14610, 16610, 17600 },\n'),
]


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    for e in EDITS:
        assert e['marker'] in e['new'], e['marker']
    assert len(set(e['marker'] for e in EDITS)) == len(EDITS)
    if len(sys.argv) > 1:
        for e in EDITS:
            text = open(os.path.join(sys.argv[1], e['file']), 'rb').read().decode('latin-1')
            n = text.count(e['old']) + text.count(e['old'].replace('\n', '\r\n'))
            assert e['marker'] in text or n == 1, (e['marker'], n)
        print('anchors ok')
    with open(os.path.join(here, 'edits.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(EDITS, f, ensure_ascii=False, indent=1)
        f.write('\n')


if __name__ == '__main__':
    main()
