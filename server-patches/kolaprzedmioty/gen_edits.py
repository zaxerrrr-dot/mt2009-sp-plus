#!/usr/bin/env python3
"""gen_edits.py - writes edits.json of server-patches/kolaprzedmioty (MT2009_PLUS_KOLA_ITEMS_V1) from the code below;
the developer's tool (the apply scripts read edits.json only). Every anchor is checked against a patched engine tree
when one is given:

  python3 gen_edits.py [<engine game/src dir to check the anchors against>]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
M = 'MT2009_PLUS_KOLA_ITEMS_V1'
RITUAL_STONE = 25046        # tools/kola_items/gen_kola_items.py (the global 25042 is our Magiczny Kamien)


def cstr(s):
    """a Polish text as a C string literal of cp1250 bytes (the sources are latin-1; the client reads cp1250)"""
    out = []
    for b in s.encode('cp1250'):
        if b == 0x22 or b == 0x5c:
            out.append('\\' + chr(b))
        elif 0x20 <= b < 0x7f:
            out.append(chr(b))
        else:
            out.append('\\%03o' % b)
    return '"' + ''.join(out) + '"'


RITUAL_TEXT = cstr(u'Kamień Rytualny działa tylko na przedmioty powyżej 80. poziomu.')

REFINE_ITEM_OLD = '\tif (pkItem->GetSubType() == USE_TUNING)\n\t{\n\t\tif (pkItem->GetValue(0) == UP_TO_3TH_LEVEL_SCROLL)\n'
REFINE_ITEM_NEW = ('\tif (pkItem->GetSubType() == USE_TUNING)\n\t{\n'
                   '\t\t// ' + M + ' (ritual stone): Kamien Rytualny (%d, the wheels\' prize) - the Magic Stone\'s\n'
                   '\t\t// protection (value0 1: no loss, no downgrade) with +15%% (value1), only on an item above level 80\n'
                   '\t\t// (as on the global server)\n'
                   '\t\tif (pkItem->GetVnum() == %d && (!pkTarget || pkTarget->GetLevelLimit() <= 80))\n'
                   '\t\t{\n'
                   '\t\t\tChatPacket(CHAT_TYPE_INFO, %s);\n'
                   '\t\t\treturn false;\n'
                   '\t\t}\n'
                   '\t\tif (pkItem->GetValue(0) == UP_TO_3TH_LEVEL_SCROLL)\n') % (RITUAL_STONE, RITUAL_STONE, RITUAL_TEXT)

SCROLL_OLD = ('\tif (pkItemScroll->GetVnum() == item->GetVnum())\n\t\treturn false;\n\n'
              '\tDWORD result_vnum = item->GetRefinedVnum();\n\tDWORD result_fail_vnum = item->GetRefineFromVnum();\n')
SCROLL_NEW = ('\tif (pkItemScroll->GetVnum() == item->GetVnum())\n\t\treturn false;\n\n'
              '\t// ' + M + ' (ritual stone roll): the level rule again at the roll\n'
              '\tif (pkItemScroll->GetVnum() == %d && item->GetLevelLimit() <= 80)\n'
              '\t{\n'
              '\t\tChatPacket(CHAT_TYPE_INFO, %s);\n'
              '\t\treturn false;\n'
              '\t}\n\n'
              '\tDWORD result_vnum = item->GetRefinedVnum();\n\tDWORD result_fail_vnum = item->GetRefineFromVnum();\n'
              ) % (RITUAL_STONE, RITUAL_TEXT)

EDITS = [
    {'file': 'char_item.cpp', 'marker': M + ' (ritual stone)', 'old': REFINE_ITEM_OLD, 'new': REFINE_ITEM_NEW},
    {'file': 'char_item.cpp', 'marker': M + ' (ritual stone roll)', 'old': SCROLL_OLD, 'new': SCROLL_NEW},
]


def main():
    for e in EDITS:
        assert e['marker'] in e['new'] and e['marker'] not in e['old'], e['marker']
    if len(sys.argv) > 1:
        for e in EDITS:
            t = open(os.path.join(sys.argv[1], e['file']), 'rb').read().decode('latin-1').replace('\r\n', '\n')
            if e['marker'] not in t and t.count(e['old']) != 1:
                sys.exit('anchor of %s found %d times' % (e['marker'], t.count(e['old'])))
    with open(os.path.join(HERE, 'edits.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(EDITS, f, indent=1)
        f.write('\n')
    print('edits.json: %d edits' % len(EDITS))


if __name__ == '__main__':
    main()
