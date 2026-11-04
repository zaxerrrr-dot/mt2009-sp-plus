#!/usr/bin/env python3
"""gen_edits.py [<game/src dir>] -- writes edits.json (MT2009_PLUS_FISHING_GLOBAL_V1, README.md) and, given a game/src
dir (an engine tree with every earlier patch applied - the test tree), checks that each edit's code is there exactly
once (or its marker already is). The logic is linux-port/overlays/playerbot/src/game/src/fish_global.cpp; these are
its hooks and the rod upgrade's global rule, each with its own marker. After chestsash (char_item.cpp's boss chest
line), konie (item_manager.cpp's Mt2009KonieDrop line) and fishpuzzle / fishren - e.g. last."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
M = 'MT2009_PLUS_FISHING_GLOBAL_V1'


def E(file, tag, old, new):
    return {'file': file, 'marker': '%s (%s)' % (M, tag), 'old': old, 'new': new}


EDITS = [
    # fish_global.cpp's function at file scope (a block-scope declaration inside namespace fishing would name
    # fishing::Mt2009FishMindOrTuna)
    E('fishing.cpp', 'decl',
      '#include "unique_item.h"\n#endif\n',
      '#include "unique_item.h"\n#endif\n\n'
      '// %s (decl): Rybie Wnetrznosci (premium or worn) or the golden tuna\'s bonus - fish_global.cpp\n'
      'bool Mt2009FishMindOrTuna(LPCHARACTER ch);\n' % M),
    # the bite chance's +10: also a worn Rybie Wnetrznosci (71008 / 72013-72015) and the golden tuna's bonus
    E('fishing.cpp', 'chance',
      '\t\tif (ch->GetPremiumRemainSeconds(PREMIUM_FISH_MIND) > 0)\n\t\t\tchance += 10;\n',
      '\t\t// %s (chance): Rybie Wnetrznosci - the premium or the worn item - or the golden tuna\'s bonus\n'
      '\t\tif (::Mt2009FishMindOrTuna(ch))\n\t\t\tchance += 10;\n' % M),
    # a rod with no next step (Wedka+20, Wedka Weglowa - its socket 0 holds its end time) is never upgraded
    E('fishing.cpp', 'refinable',
      '\t\treturn (rod->GetSocket(0) == rod->GetValue(2));\n',
      '\t\t// %s (refinable): only a rod with a next step (not +20 nor Wedka Weglowa)\n'
      '\t\treturn rod->GetRefinedVnum() > 0 && rod->GetSocket(0) == rod->GetValue(2);\n' % M),
    # a failed upgrade: the rod stays with 10% of its points less (the pl-wiki "Wedka", since 15.7; Owsap
    # __REFINE_FISHINGROD_RENEWAL__) - before, a new rod of value4 with no points
    E('fishing.cpp', 'rod fail',
      '\t\t\tLPITEM pkNewItem = ITEM_MANAGER::instance().CreateItem(rod->GetValue(4), 1);\n',
      '\t\t\t// %s (rod fail): the rod stays, 10%% of its points less (the global rule)\n'
      '\t\t\t{\n'
      '\t\t\t\tconst long lPoints = rod->GetSocket(0);\n'
      '\t\t\t\tconst long lLose = MAX(1L, lPoints / 10);\n'
      '\t\t\t\trod->SetSocket(0, MAX(0L, lPoints - lLose), true, "SOCKET_FISHING");\n'
      '\t\t\t\tLogManager::instance().ItemLog(ch, rod, "REFINE FISH_ROD FAIL", rod->GetName());\n'
      '\t\t\t\treturn 0;\n'
      '\t\t\t}\n'
      '\t\t\tLPITEM pkNewItem = ITEM_MANAGER::instance().CreateItem(rod->GetValue(4), 1);\n' % M),
    # the Rybak takes every rod into his dialog (quest rybak_wedki): the free upgrade, no refine window
    E('char_item.cpp', 'fisher take',
      '\t\tcase fishing::FISHER_MOB:\n\t\t{\n\t\t\tif (fishing::RefinableRod(item))\n\t\t\t{\n'
      '\t\t\t\tfrom->SetRefineNPC(this);\n\t\t\t\tfrom->RefineInformation(item->GetCell(), REFINE_TYPE_FISHER);\n'
      '\t\t\t}\n\t\t\telse {\n',
      '\t\tcase fishing::FISHER_MOB:\n\t\t{\n'
      '\t\t\t// %s (fisher take): no refine window - the rod goes to the Rybak\'s dialog (quest rybak_wedki), which\n'
      '\t\t\t// upgrades it for free (__fish_real_refine_rod -> fishing::RealRefineRod)\n'
      '\t\t\t{\n' % M),
    # Skrzynia Nimfy Wodnej is no boss chest: no sash roll on opening it (as the Gold / Silver Caskets)
    E('char_item.cpp', 'chest sash',
      'dwBoxVnum != 50012 && dwBoxVnum != 50013 &&\n',
      'dwBoxVnum != 50012 && dwBoxVnum != 50013 &&\n'
      '\t\t\t\t\t\t\t\tdwBoxVnum != 27625 /* %s (chest sash): Skrzynia Nimfy Wodnej */ &&\n' % M),
    # Skrzynia Nimfy Wodnej from every monster of level 70 or more (fish_global.cpp)
    E('item_manager.cpp', 'nimfa drop',
      '\t{ void Mt2009KonieDrop(LPCHARACTER, LPCHARACTER, std::vector<LPITEM>&); Mt2009KonieDrop(pkChr, pkKiller, vec_item); }\n',
      '\t{ void Mt2009KonieDrop(LPCHARACTER, LPCHARACTER, std::vector<LPITEM>&); Mt2009KonieDrop(pkChr, pkKiller, vec_item); }\n'
      '\t// %s (nimfa drop): Skrzynia Nimfy Wodnej from every monster of level 70+ (fish_global.cpp)\n'
      '\t{ void Mt2009FishNimfaDrop(LPCHARACTER, LPCHARACTER, int, int, std::vector<LPITEM>&); '
      'Mt2009FishNimfaDrop(pkChr, pkKiller, iDeltaPercent, iRandRange, vec_item); }\n' % M),
]


def main():
    json.dump(EDITS, open(os.path.join(HERE, 'edits.json'), 'w'), indent=1)
    print('edits.json: %d edit(s)' % len(EDITS))
    if len(sys.argv) > 1:
        bad = 0
        for e in EDITS:
            text = open(os.path.join(sys.argv[1], e['file']), 'rb').read().decode('latin-1').replace('\r\n', '\n')
            if e['marker'] in text:
                print('  %s: already applied' % e['marker'])
            elif text.count(e['old']) != 1:
                print('  %s: code found %d time(s) in %s' % (e['marker'], text.count(e['old']), e['file']))
                bad += 1
            else:
                print('  %s: ok' % e['marker'])
        sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
