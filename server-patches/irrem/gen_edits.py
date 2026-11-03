#!/usr/bin/env python3
"""gen_edits.py [<game/src dir>] -- writes edits.json (MT2009_PLUS_IRREMOVABLE_DELETE_V1, README.md) and, given a game/src
dir (an engine tree with every earlier patch applied - the test tree), checks that each edit's code is there exactly
once (or its marker already is). The logic is linux-port/overlays/playerbot/src/game/src/irremovable_delete.cpp; these
are only its hooks, each with its own marker. Applied after switchbot (input_main.cpp ItemUse / ItemMove) and fishren
(cmd.cpp), e.g. last."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
M = 'MT2009_PLUS_IRREMOVABLE_DELETE_V1'


def E(file, tag, old, new):
    return {'file': file, 'marker': '%s (%s)' % (M, tag), 'old': old, 'new': new}


EDITS = [
    # the player's own packets: the question may only come out of them (not from quests, mounts, bots...)
    E('input_main.cpp', 'use scope',
      '\tch->UseItem(((struct command_item_use *) data)->Cell);\n}\n',
      '\t// %s (use scope): a refused take-off of a worn irremovable item in this use asks whether to destroy it\n'
      '\tvoid Mt2009IrremScope(LPCHARACTER ch);\n'
      '\tMt2009IrremScope(ch);\n'
      '\tch->UseItem(((struct command_item_use *) data)->Cell);\n'
      '\tMt2009IrremScope(NULL);\n}\n' % M),
    E('input_main.cpp', 'move scope',
      '\tif (ch)\n\t\tch->MoveItem(pinfo->Cell, pinfo->CellTo, pinfo->count);\n}\n',
      '\t// %s (move scope): a refused take-off of a worn irremovable item in this move asks whether to destroy it\n'
      '\tvoid Mt2009IrremScope(LPCHARACTER ch);\n'
      '\tif (ch)\n\t{\n'
      '\t\tMt2009IrremScope(ch);\n'
      '\t\tch->MoveItem(pinfo->Cell, pinfo->CellTo, pinfo->count);\n'
      '\t\tMt2009IrremScope(NULL);\n\t}\n}\n' % M),
    # MoveItem's early test (a worn irremovable item dragged out of the equipment never reaches CanUnequipNow)
    E('char_item.cpp', 'move',
      '\tif (INVENTORY == Cell.window_type && Cell.cell >= INVENTORY_MAX_NUM && IS_SET(item->GetFlag(), ITEM_FLAG_IRREMOVABLE))\n'
      '\t{\n'
      '\t\tif (bDSMoveTrace) sys_err("[DS_EQUIP_MOVE_TRACE] return false at ITEM_FLAG_IRREMOVABLE horse-page check");\n'
      '\t\treturn false;\n\t}\n',
      '\tif (INVENTORY == Cell.window_type && Cell.cell >= INVENTORY_MAX_NUM && IS_SET(item->GetFlag(), ITEM_FLAG_IRREMOVABLE))\n'
      '\t{\n'
      '\t\tif (bDSMoveTrace) sys_err("[DS_EQUIP_MOVE_TRACE] return false at ITEM_FLAG_IRREMOVABLE horse-page check");\n'
      '\t\t// %s (move): the worn one dragged out - ask whether to destroy it (irremovable_delete.cpp)\n'
      '\t\t{ void Mt2009IrremAsk(LPCHARACTER ch, LPITEM item); Mt2009IrremAsk(this, item); }\n'
      '\t\treturn false;\n\t}\n' % M),
    # every other take-off (UnequipItem of a use, SwapItem of a move onto its slot, MoveItem's equipment branch)
    E('char_item.cpp', 'unequip',
      '\tif (IS_SET(item->GetFlag(), ITEM_FLAG_IRREMOVABLE))\n\t\treturn false;\n',
      '\tif (IS_SET(item->GetFlag(), ITEM_FLAG_IRREMOVABLE))\n\t{\n'
      '\t\t// %s (unequip): within the player\'s own use / move only - ask whether to destroy it\n'
      '\t\t{ void Mt2009IrremAsk(LPCHARACTER ch, LPITEM item); Mt2009IrremAsk(this, item); }\n'
      '\t\treturn false;\n\t}\n' % M),
    # the command
    E('cmd.cpp', 'command declare',
      'struct command_info cmd_info[] =\n',
      '// %s (command declare): "/irrem usun <token>" | "/irrem anuluj" - irremovable_delete.cpp\n'
      'void Mt2009IrremCommand(LPCHARACTER ch, const char* argument);\n'
      'ACMD(do_irrem)\n{\n\tMt2009IrremCommand(ch, argument);\n}\n\n'
      'struct command_info cmd_info[] =\n' % M),
    E('cmd.cpp', 'command table',
      '\t{ "yitem",\tdo_yitem,\t0,\t\t\tPOS_DEAD,\tGM_PLAYER\t}, // MT2009_PLUS_YOHARA_SETS_V2 (command table)\n',
      '\t{ "yitem",\tdo_yitem,\t0,\t\t\tPOS_DEAD,\tGM_PLAYER\t}, // MT2009_PLUS_YOHARA_SETS_V2 (command table)\n'
      '\t{ "irrem",\tdo_irrem,\t0,\t\t\tPOS_DEAD,\tGM_PLAYER\t}, // %s (command table)\n' % M),
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
