#!/usr/bin/env python3
"""gen_edits.py [<game/src>] -- writes edits.json of server-patches/kolekcjoner (README.md,
MT2009_PLUS_KOLEKCJONER_NAJEMNIKOW_V1: Kolekcjoner Najemnikow, the mercenaries' unlock); with a game/src dir it also
checks that each edit's code is there exactly once (or its marker already is). Applied after najemnicy (its command's
lines in cmd.cpp are the anchors)."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
M = 'MT2009_PLUS_KOLEKCJONER_NAJEMNIKOW_V1'
EDITS = []


def edit(file, tag, old, new):
    EDITS.append(dict(file=file, marker='%s (%s)' % (M, tag), old=old, new=new))


# the command, after the mercenaries' one
edit('cmd.cpp', 'command declare',
     'ACMD(do_najemnicy)\n{\n\tPlayerBotNajemnicyCommand(ch, argument);\n}\n',
     'ACMD(do_najemnicy)\n{\n\tPlayerBotNajemnicyCommand(ch, argument);\n}\n'
     '// ' + M + ' (command declare): "/kolekcja_najemnikow" - Kolekcjoner Najemnikow, the mercenaries\' unlock (the\n'
     '// client\'s window, the Najemnicy letter): open, lista, oddaj <task> <item> [all]; GM: przeladuj, ukoncz, wyczysc\n'
     '// (playerbot_kolekcjoner_najemnikow.cpp)\n'
     'void KolekcjonerNajemnikowCommand(LPCHARACTER ch, const char* argument);\n'
     'ACMD(do_kolekcja_najemnikow)\n'
     '{\n'
     '\tKolekcjonerNajemnikowCommand(ch, argument);\n'
     '}\n')

edit('cmd.cpp', 'command table',
     '\t{ "najemnicy",\tdo_najemnicy,\t0,\tPOS_DEAD,\tGM_PLAYER\t}, // MT2009_PLUS_NAJEMNICY_V1 (command table): the GM\'s part '
     'checks GM_HIGH_WIZARD itself\n',
     '\t{ "najemnicy",\tdo_najemnicy,\t0,\tPOS_DEAD,\tGM_PLAYER\t}, // MT2009_PLUS_NAJEMNICY_V1 (command table): the GM\'s part '
     'checks GM_HIGH_WIZARD itself\n'
     '\t{ "kolekcja_najemnikow",\tdo_kolekcja_najemnikow,\t0,\tPOS_DEAD,\tGM_PLAYER\t}, // ' + M + ' (command table): '
     'the GM\'s part checks GM_HIGH_WIZARD itself\n')

# the permanent bonuses: every recompute, after the worn items and sets, before the horse's minima and the battle points
# (so +100 attack value goes through POINT_ATT_GRADE_BONUS into ComputeBattlePoints)
edit('char.cpp', 'compute',
     '\t// MT2009_PLUS_HORSE40_V1 (compute): the Sung Ma minima of a horse of 31+ and the constant horse skills while\n',
     '\t// ' + M + ' (compute): the completed Kolekcjoner Najemnikow tasks\' permanent bonuses - added at every\n'
     '\t// recompute, never an affect, so nothing expires or can be removed (playerbot_kolekcjoner_najemnikow.cpp)\n'
     '\tif (IsPC())\n'
     '\t{\n'
     '\t\tvoid KolekcjonerNajemnikowComputePoints(LPCHARACTER ch);\n'
     '\t\tKolekcjonerNajemnikowComputePoints(this);\n'
     '\t}\n'
     '\n'
     '\t// MT2009_PLUS_HORSE40_V1 (compute): the Sung Ma minima of a horse of 31+ and the constant horse skills while\n')


def main():
    with open(os.path.join(HERE, 'edits.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(EDITS, f, indent=1, ensure_ascii=False)
        f.write('\n')
    if len(sys.argv) > 1:
        bad = 0
        for e in EDITS:
            text = open(os.path.join(sys.argv[1], e['file']), 'rb').read().decode('latin-1').replace('\r\n', '\n')
            if e['marker'] in text:
                print('%s: %s already there' % (e['file'], e['marker']))
            elif text.count(e['old']) != 1:
                print('%s: %s - anchor found %d times' % (e['file'], e['marker'], text.count(e['old'])))
                bad += 1
        print('edits %d, bad anchors %d' % (len(EDITS), bad))
        sys.exit(1 if bad else 0)
    print('edits %d' % len(EDITS))


if __name__ == '__main__':
    main()
