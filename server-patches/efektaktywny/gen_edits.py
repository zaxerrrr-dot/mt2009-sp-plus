#!/usr/bin/env python3
"""gen_edits.py [<game/src dir>] -- writes edits.json (MT2009_PLUS_EFFECT_ACTIVE_QUIET_V1, README.md) and, given a
game/src dir (an engine tree with every earlier patch applied - the test tree), checks that each edit's code is there
exactly once (or its marker already is). Autohunt (and a player clicking fast) used Grzaniec 50216 / Znak Straznika
72328 again and again while the affect ran: every refusal wrote "Ten efekt jest juz aktywny." into the chat. The
refusal stays; the line comes at most once a minute a character."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
M = 'MT2009_PLUS_EFFECT_ACTIVE_QUIET_V1'


def quiet(tag, indent, text):
    t = '\t' * indent
    return ('%s// %s (%s): the refusal\'s line at most once a minute a character (autohunt tried it every few seconds)\n'
            '%s{\n'
            '%s\tstatic std::map<DWORD, DWORD> s_mapLastLine;\n'
            '%s\tDWORD& rdwLast = s_mapLastLine[GetPlayerID()];\n'
            '%s\tconst DWORD dwNow = get_dword_time();\n'
            '%s\tif (!rdwLast || dwNow - rdwLast >= 60000)\n'
            '%s\t{\n'
            '%s\t\trdwLast = dwNow;\n'
            '%s\t\tChatPacket(CHAT_TYPE_INFO, LC_TEXT("%s"));\n'
            '%s\t}\n'
            '%s}\n') % ((t, M, tag) + (t,) * 7 + (t, text) + (t, t))


def E(file, tag, indent, text):
    return {'file': file, 'marker': '%s (%s)' % (M, tag),
            'old': '\t' * indent + 'ChatPacket(CHAT_TYPE_INFO, LC_TEXT("%s"));\n' % text,
            'new': quiet(tag, indent, text)}


EDITS = [
    # case ITEM_NOG_POCKET (Grzaniec 50216) while AFFECT_NOG_ABILITY runs
    E('char_item.cpp', 'nog', 10, 'This effect is already activated.'),
    # case 72328 (Znak Straznika, ENABLE_12ZI) while AFFECT_CZ_UNLIMIT_ENTER runs
    E('char_item.cpp', 'cz', 9, 'The effect is already active.'),
]


def main():
    json.dump(EDITS, open(os.path.join(HERE, 'edits.json'), 'w'), indent=1)
    if len(sys.argv) > 1:
        bad = 0
        for e in EDITS:
            text = open(os.path.join(sys.argv[1], e['file']), 'rb').read().decode('latin-1').replace('\r\n', '\n')
            if e['marker'] not in text and text.count(e['old']) != 1:
                print('NOT FOUND once: %s' % e['marker'])
                bad += 1
        print('%d edit(s), %d not found' % (len(EDITS), bad))
        sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
