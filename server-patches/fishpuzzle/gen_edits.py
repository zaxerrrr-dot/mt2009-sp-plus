#!/usr/bin/env python3
"""gen_edits.py [<game/src dir>] -- writes edits.json (MT2009_PLUS_FISH_PUZZLE_V1, README.md) and, given a game/src
dir (an engine tree with every earlier patch applied - the test tree), checks that each edit's code is there exactly
once (or its marker already is). The logic is linux-port/overlays/playerbot/src/game/src/fish_puzzle.cpp; these are
only its hooks, each with its own marker. Applied after relikty (the use hook sits under its block), e.g. last."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
M = 'MT2009_PLUS_FISH_PUZZLE_V1'


def E(file, tag, old, new):
    return {'file': file, 'marker': '%s (%s)' % (M, tag), 'old': old, 'new': new}


EDITS = [
    # a fish caught (the fishing game won) during the event may bring a puzzle box
    E('fishing.cpp', 'catch',
      '\t\tquest::CQuestManager::instance().Fishing(ch->GetPlayerID(), FISHING_QUEST_STATE_SUCCESS);\n'
      '\t\tFishingSuccess(ch);\n',
      '\t\tquest::CQuestManager::instance().Fishing(ch->GetPlayerID(), FISHING_QUEST_STATE_SUCCESS);\n'
      '\t\tFishingSuccess(ch);\n'
      '\t\t// %s (catch): Event Rybacki - Puzzle - a Pudlo wedkarskich puzzli now and then (fish_puzzle.cpp)\n'
      '\t\t{ void Mt2009FishPuzzleOnCatch(LPCHARACTER); Mt2009FishPuzzleOnCatch(ch); }\n' % M),
    # a puzzle box used from the inventory opens the window
    E('char_item.cpp', 'use',
      '\t\tconst int iRelicUse = Mt2009RelicUseItem(this, item);\n\t\tif (iRelicUse >= 0)\n\t\t\treturn iRelicUse != 0;\n\t}\n',
      '\t\tconst int iRelicUse = Mt2009RelicUseItem(this, item);\n\t\tif (iRelicUse >= 0)\n\t\t\treturn iRelicUse != 0;\n\t}\n'
      '\t// %s (use): Pudlo wedkarskich puzzli 25106 / 25107 opens the puzzle window (fish_puzzle.cpp)\n'
      '\t{\n\t\tint Mt2009FishPuzzleUseItem(LPCHARACTER ch, LPITEM item);\n'
      '\t\tconst int iFishPuzzleUse = Mt2009FishPuzzleUseItem(this, item);\n\t\tif (iFishPuzzleUse >= 0)\n'
      '\t\t\treturn iFishPuzzleUse != 0;\n\t}\n' % M),
    # the command
    E('cmd.cpp', 'command declare',
      'struct command_info cmd_info[] =\n',
      '// %s (command declare): "/fishpuzzle open|box <1|2>|place <cell>|discard" - fish_puzzle.cpp\n'
      'void Mt2009FishPuzzleCommand(LPCHARACTER ch, const char* argument);\n'
      'ACMD(do_fishpuzzle)\n{\n\tMt2009FishPuzzleCommand(ch, argument);\n}\n\n'
      'struct command_info cmd_info[] =\n' % M),
    E('cmd.cpp', 'command table',
      '\t{ "yitem",\tdo_yitem,\t0,\t\t\tPOS_DEAD,\tGM_PLAYER\t}, // MT2009_PLUS_YOHARA_SETS_V2 (command table)\n',
      '\t{ "yitem",\tdo_yitem,\t0,\t\t\tPOS_DEAD,\tGM_PLAYER\t}, // MT2009_PLUS_YOHARA_SETS_V2 (command table)\n'
      '\t{ "fishpuzzle",\tdo_fishpuzzle,\t0,\t\tPOS_DEAD,\tGM_PLAYER\t}, // %s (command table)\n' % M),
]


def main():
    with open(os.path.join(HERE, 'edits.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(EDITS, f, indent=1)
        f.write('\n')
    print('fishpuzzle: %d edits written' % len(EDITS))
    if len(sys.argv) > 1:
        bad = 0
        for e in EDITS:
            text = open(os.path.join(sys.argv[1], e['file']), 'rb').read().decode('latin-1').replace('\r\n', '\n')
            if e['marker'] in text:
                continue
            n = text.count(e['old'])
            if n != 1:
                bad += 1
                print('  %s %s: the code is there %d time(s)' % (e['file'], e['marker'], n))
        print('fishpuzzle: anchors %s' % ('OK' if not bad else '%d BAD' % bad))
        sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
