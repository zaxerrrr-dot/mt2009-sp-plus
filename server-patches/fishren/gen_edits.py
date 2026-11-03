#!/usr/bin/env python3
"""gen_edits.py [<game/src dir>] -- writes edits.json (MT2009_PLUS_FISHING_RENEWAL_V1, README.md) and, given a game/src
dir (an engine tree with every earlier patch applied - the test tree), checks that each edit's code is there exactly
once (or its marker already is). The logic is linux-port/overlays/playerbot/src/game/src/fish_renewal.cpp; these are
only its hooks, each with its own marker. Applied after enginefixes (MT2009_PLUS_FISHING_FREE_V1 in CHARACTER::fishing)
and fishpuzzle (cmd.cpp), e.g. last."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
M = 'MT2009_PLUS_FISHING_RENEWAL_V1'


def E(file, tag, old, new):
    return {'file': file, 'marker': '%s (%s)' % (M, tag), 'old': old, 'new': new}


EDITS = [
    # the fishing key / a move while a renewal cast runs: the rod pulled out (fish_renewal.cpp), not the old take
    E('char.cpp', 'pull',
      'void CHARACTER::fishing()\n{\n\tif (m_pkFishingEvent || m_pkPreFishingEvent)\n\t{\n',
      'void CHARACTER::fishing()\n{\n'
      '\t// %s (pull): a renewal cast (the new fishing window, fish_renewal.cpp) ends here - the old take never sees it\n'
      '\t{\n\t\tbool Mt2009FishRenPull(LPCHARACTER ch);\n\t\tif (m_pkPreFishingEvent && Mt2009FishRenPull(this))\n\t\t\treturn;\n\t}\n\n'
      '\tif (m_pkFishingEvent || m_pkPreFishingEvent)\n\t{\n' % M),
    # the cast: a client that said "/fishren hello" gets the renewal's cast, any other (old root, bots) the old one
    E('char.cpp', 'cast',
      '\tm_pkPreFishingEvent = fishing::CreatePreFishingEvent(this);\n}\n',
      '\t// %s (cast): the new fishing window\'s cast for a client that has it (fish_renewal.cpp); NULL - the bar minigame\n'
      '\t{\n\t\tLPEVENT Mt2009FishRenCast(LPCHARACTER ch);\n\t\tm_pkPreFishingEvent = Mt2009FishRenCast(this);\n\t}\n'
      '\tif (!m_pkPreFishingEvent)\n'
      '\t\tm_pkPreFishingEvent = fishing::CreatePreFishingEvent(this);\n}\n' % M),
    # the command
    E('cmd.cpp', 'command declare',
      'struct command_info cmd_info[] =\n',
      '// %s (command declare): "/fishren hello|end <token> <hits>" - fish_renewal.cpp\n'
      'void Mt2009FishRenCommand(LPCHARACTER ch, const char* argument);\n'
      'ACMD(do_fishren)\n{\n\tMt2009FishRenCommand(ch, argument);\n}\n\n'
      'struct command_info cmd_info[] =\n' % M),
    E('cmd.cpp', 'command table',
      '\t{ "yitem",\tdo_yitem,\t0,\t\t\tPOS_DEAD,\tGM_PLAYER\t}, // MT2009_PLUS_YOHARA_SETS_V2 (command table)\n',
      '\t{ "yitem",\tdo_yitem,\t0,\t\t\tPOS_DEAD,\tGM_PLAYER\t}, // MT2009_PLUS_YOHARA_SETS_V2 (command table)\n'
      '\t{ "fishren",\tdo_fishren,\t0,\t\t\tPOS_DEAD,\tGM_PLAYER\t}, // %s (command table)\n' % M),
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
