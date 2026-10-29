#!/usr/bin/env python3
"""gen_edits.py [<game/src dir>] -- writes edits.json (MT2009_PLUS_WEAPON_ELEMENT_V1, README.md) and, given a game/src
dir (an engine tree with every earlier patch applied - the test tree), checks that each edit's code is there exactly
once (or its marker already is). The logic is linux-port/overlays/playerbot/src/game/src/weapon_element.cpp; these
are only its hooks, each with its own marker. Applied after superstone / questren (the last ones)."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
M = 'MT2009_PLUS_WEAPON_ELEMENT_V1'


def E(file, tag, old, new):
    return {'file': file, 'marker': '%s (%s)' % (M, tag), 'old': old, 'new': new}


EDITS = [
    # the data: read when a weapon / sash is loaded
    E('item_manager.cpp', 'create',
      '\tMt2009YSetsCreate(item, bIsNewItem, bSkipSave); // MT2009_PLUS_YOHARA_SETS_V1 (create): its set / random bonuses\n',
      '\tMt2009YSetsCreate(item, bIsNewItem, bSkipSave); // MT2009_PLUS_YOHARA_SETS_V1 (create): its set / random bonuses\n'
      '\t{ void Mt2009WElemCreate(LPITEM, bool); Mt2009WElemCreate(item, bIsNewItem); } // %s (create): its weapon element\n' % M),
    # a refine / a sash's absorption keeps it
    E('item_attribute.cpp', 'copy',
      '\tMt2009YSetsCopy(this, pItem); // MT2009_PLUS_YOHARA_SETS_V1 (copy): the set and the random bonuses\n',
      '\tMt2009YSetsCopy(this, pItem); // MT2009_PLUS_YOHARA_SETS_V1 (copy): the set and the random bonuses\n'
      '\t{ void Mt2009WElemCopy(LPITEM, LPITEM); Mt2009WElemCopy(this, pItem); } // %s (copy): the weapon element\n' % M),
    # the points: the power of the element (a sash: its share and the attack's)
    E('item.cpp', 'points',
      "\tMt2009YSetsItemPoints(this, m_pOwner, bAdd); // MT2009_PLUS_YOHARA_SETS_V1 (points): a serpent piece's random base bonuses\n",
      "\tMt2009YSetsItemPoints(this, m_pOwner, bAdd); // MT2009_PLUS_YOHARA_SETS_V1 (points): a serpent piece's random base bonuses\n"
      "\t{ void Mt2009WElemItemPoints(LPITEM, LPCHARACTER, bool); Mt2009WElemItemPoints(this, m_pOwner, bAdd); } // %s (points)\n" % M),
    # the client's copy when an item comes into the bag
    E('item.cpp', 'add',
      '\tif ((window_type == INVENTORY || window_type == EQUIPMENT) && GetYExtra()) // MT2009_PLUS_YOHARA_SETS_V2 (add)\n'
      '\t\tMt2009YSetsNotify(ch, 1, pos, GetYExtra());\n',
      '\tif ((window_type == INVENTORY || window_type == EQUIPMENT) && GetYExtra()) // MT2009_PLUS_YOHARA_SETS_V2 (add)\n'
      '\t\tMt2009YSetsNotify(ch, 1, pos, GetYExtra());\n'
      '\tif (window_type == INVENTORY || window_type == EQUIPMENT) // %s (add): the weapon element (WELEM)\n'
      '\t{ void Mt2009WElemNotifyItem(LPCHARACTER, int, int, LPITEM, bool); Mt2009WElemNotifyItem(ch, 1, pos, this, false); }\n' % M),
    # the attack value - added as the weapon's value5 (melee and bow)
    E('battle.cpp', 'melee',
      '\t\tiAtk += pWeapon->GetValue(5) * 2;\n\n\t\tif (pkVictim->IsNPC())\n',
      '\t\tiAtk += pWeapon->GetValue(5) * 2;\n'
      '\t\t{ int Mt2009WElemAttack(LPITEM); iAtk += Mt2009WElemAttack(pWeapon) * 2; } // %s (melee): the enchant\'s Wartosc Ataku\n'
      '\n\t\tif (pkVictim->IsNPC())\n' % M),
    E('battle.cpp', 'bow',
      '\tiAtk += pkBow->GetValue(5) * 2;\n',
      '\tiAtk += pkBow->GetValue(5) * 2;\n'
      '\t{ int Mt2009WElemAttack(LPITEM); iAtk += Mt2009WElemAttack(pkBow) * 2; } // %s (bow): the enchant\'s Wartosc Ataku\n' % M),
    # a scroll dragged onto a weapon opens the window (nothing is used yet)
    E('char_item.cpp', 'use',
      '\t\tconst int iAddeqUse = Mt2009AddeqUseItem(this, item);\n\t\tif (iAddeqUse >= 0)\n\t\t\treturn iAddeqUse != 0;\n\t}\n',
      '\t\tconst int iAddeqUse = Mt2009AddeqUseItem(this, item);\n\t\tif (iAddeqUse >= 0)\n\t\t\treturn iAddeqUse != 0;\n\t}\n'
      '\t// %s (use): Zwoje Zywiolow / Klatwy / Zmiany 56002-56009 dragged onto a weapon (weapon_element.cpp)\n'
      '\t{\n\t\tint Mt2009WElemUseItem(LPCHARACTER ch, LPITEM item, TItemPos DestCell);\n'
      '\t\tconst int iWElemUse = Mt2009WElemUseItem(this, item, DestCell);\n\t\tif (iWElemUse >= 0)\n'
      '\t\t\treturn iWElemUse != 0;\n\t}\n' % M),
    # a cell of the inventory / equipment changed
    E('char_item.cpp', 'notify',
      '\t\t\tMt2009YSetsNotify(this, 1, wCell, pItem ? pItem->GetYExtra() : 0);\n\t}\n',
      '\t\t\tMt2009YSetsNotify(this, 1, wCell, pItem ? pItem->GetYExtra() : 0);\n'
      '\t\tif (window_type == INVENTORY || window_type == EQUIPMENT) // %s (notify): the weapon element (WELEM)\n'
      '\t\t{ void Mt2009WElemCellNotify(LPCHARACTER, int, LPITEM, LPITEM); Mt2009WElemCellNotify(this, wCell, pItem, pYSetsOld); }\n'
      '\t}\n' % M),
    # entergame
    E('input_login.cpp', 'enter',
      '\tMt2009YSetsSendAll(ch); // MT2009_PLUS_YOHARA_SETS_V1 (enter): the tooltip\'s set / random bonuses\n',
      '\tMt2009YSetsSendAll(ch); // MT2009_PLUS_YOHARA_SETS_V1 (enter): the tooltip\'s set / random bonuses\n'
      '\t{ void Mt2009WElemSendAll(LPCHARACTER); Mt2009WElemSendAll(ch); } // %s (enter): the weapon elements (WELEM)\n' % M),
    # the storehouse
    E('safebox.cpp', 'safebox add',
      '\t\tMt2009YSetsNotify(m_pkChrOwner, 3, dwPos, pkItem->GetYExtra());\n',
      '\t\tMt2009YSetsNotify(m_pkChrOwner, 3, dwPos, pkItem->GetYExtra());\n'
      '\tif (m_bWindowMode == SAFEBOX) // %s (safebox add)\n'
      '\t{ void Mt2009WElemNotifyItem(LPCHARACTER, int, int, LPITEM, bool); Mt2009WElemNotifyItem(m_pkChrOwner, 3, dwPos, pkItem, false); }\n' % M),
    E('safebox.cpp', 'safebox remove',
      '\t\tMt2009YSetsNotify(m_pkChrOwner, 3, dwPos, 0);\n',
      '\t\tMt2009YSetsNotify(m_pkChrOwner, 3, dwPos, 0);\n'
      '\tif (m_bWindowMode == SAFEBOX) // %s (safebox remove)\n'
      '\t{ void Mt2009WElemNotifyItem(LPCHARACTER, int, int, LPITEM, bool); Mt2009WElemNotifyItem(m_pkChrOwner, 3, dwPos, pkItem, true); }\n' % M),
    # the trade
    E('exchange.cpp', 'start',
      '\texchange_packet(this, EXCHANGE_SUBHEADER_GC_START, 0, victim->GetVID(), NPOS, 0);\n',
      '\texchange_packet(this, EXCHANGE_SUBHEADER_GC_START, 0, victim->GetVID(), NPOS, 0);\n'
      '\t{ void Mt2009WElemExchangeStart(LPCHARACTER, LPCHARACTER); Mt2009WElemExchangeStart(this, victim); } // %s (start)\n' % M),
    E('exchange.cpp', 'add',
      '\t\tsys_log(0, "EXCHANGE AddItem success %s pos(%d, %d) %d", item->GetName(), item_pos.window_type, item_pos.cell, display_pos);\n',
      '\t\t{ void Mt2009WElemExchangeAdd(LPCHARACTER, LPCHARACTER, int, LPITEM); // %s (add): both sides hear the element\n'
      '\t\t\tMt2009WElemExchangeAdd(m_pOwner, GetCompany()->GetOwner(), display_pos, item); }\n'
      '\t\tsys_log(0, "EXCHANGE AddItem success %%s pos(%%d, %%d) %%d", item->GetName(), item_pos.window_type, item_pos.cell, display_pos);\n' % M),
    # Straznik Medali's shop: the config's prices, the guild level
    E('shop.cpp', 'buy',
      '\t\tdwPrice /= 2;\n\t}\n',
      '\t\tdwPrice /= 2;\n\t}\n'
      '\t// %s (buy): Straznik Medali\'s scrolls - weapon_element.txt\'s price (no empire mark-up), the wiki\'s guild level\n'
      '\t{\n\t\tbool Mt2009WElemShopPrice(DWORD, int, YANG&);\n\t\tbool Mt2009WElemShopCanBuy(LPCHARACTER, DWORD);\n'
      '\t\tif (!m_pkPC && Mt2009WElemShopPrice(r_item.vnum, r_item.count, dwPrice) && !Mt2009WElemShopCanBuy(ch, r_item.vnum))\n'
      '\t\t\treturn SHOP_SUBHEADER_GC_OK; // nothing bought, nothing sent (the reason is in the chat)\n\t}\n' % M),
    E('shop.cpp', 'list',
      '\t\tpack2.items[i].price = price;\n',
      '\t\t{ bool Mt2009WElemShopPrice(DWORD, int, YANG&); if (!m_pkPC) Mt2009WElemShopPrice(item.vnum, item.count, price); } // %s (list)\n'
      '\t\tpack2.items[i].price = price;\n' % M),
    # the commands
    E('cmd.cpp', 'command declare',
      'ACMD(do_yitem)\n{\n\tMt2009YSetsResend(ch);\n}\n',
      'ACMD(do_yitem)\n{\n\tMt2009YSetsResend(ch);\n}\n'
      '// %s (command declare): "/welem ok|change <element>|close" (the window), "/welem_sync" (WELEM again),\n'
      '// "/welem_reload" (GM: weapon_element.txt again) - weapon_element.cpp\n'
      'void Mt2009WElemCommand(LPCHARACTER ch, const char* argument);\nvoid Mt2009WElemResend(LPCHARACTER ch);\n'
      'void Mt2009WElemReload(LPCHARACTER ch);\n'
      'ACMD(do_welem)\n{\n\tMt2009WElemCommand(ch, argument);\n}\n'
      'ACMD(do_welem_sync)\n{\n\tMt2009WElemResend(ch);\n}\n'
      'ACMD(do_welem_reload)\n{\n\tMt2009WElemReload(ch);\n}\n' % M),
    E('cmd.cpp', 'command table',
      '\t{ "yitem",\tdo_yitem,\t0,\t\t\tPOS_DEAD,\tGM_PLAYER\t}, // MT2009_PLUS_YOHARA_SETS_V2 (command table)\n',
      '\t{ "yitem",\tdo_yitem,\t0,\t\t\tPOS_DEAD,\tGM_PLAYER\t}, // MT2009_PLUS_YOHARA_SETS_V2 (command table)\n'
      '\t{ "welem",\tdo_welem,\t0,\t\t\tPOS_DEAD,\tGM_PLAYER\t}, // %s (command table)\n'
      '\t{ "welem_sync",\tdo_welem_sync,\t0,\t\tPOS_DEAD,\tGM_PLAYER\t},\n'
      '\t{ "welem_reload",\tdo_welem_reload,\t0,\t\tPOS_DEAD,\tGM_HIGH_WIZARD\t},\n' % M),
    # the effect the others see
    E('char.cpp', 'update',
      '\t{ void Mt2009AuraOnUpdatePacket(LPCHARACTER); Mt2009AuraOnUpdatePacket(this); }\n#endif\n',
      '\t{ void Mt2009AuraOnUpdatePacket(LPCHARACTER); Mt2009AuraOnUpdatePacket(this); }\n#endif\n'
      '\t{ void Mt2009WElemOnUpdatePacket(LPCHARACTER); Mt2009WElemOnUpdatePacket(this); } // %s (update): the weapon element effect\n' % M),
    E('char.cpp', 'insert',
      '\t\tMt2009AuraOnInsert(this, ch);\n\t}\n#endif\n',
      '\t\tMt2009AuraOnInsert(this, ch);\n\t}\n#endif\n'
      '\t// %s (insert): a character with the weapon element effect coming into a player\'s view ("WELEMFX")\n'
      '\tif (IsPC() && ch && ch->IsPC() && !d->IsBot())\n'
      '\t{\n\t\tvoid Mt2009WElemOnInsert(LPCHARACTER, LPCHARACTER);\n\t\tMt2009WElemOnInsert(this, ch);\n\t}\n' % M),
    # a sash cleaned of its absorbed weapon loses the element too
    E('char.cpp', 'detach',
      '\tpkTarget->SetSocket(ACCE_ABSORBED_SOCKET, 0);\n\tfor (int i = 0; i < ITEM_ATTRIBUTE_MAX_NUM; ++i)\n\t\tpkTarget->SetForceAttribute(i, 0, 0);\n',
      '\tpkTarget->SetSocket(ACCE_ABSORBED_SOCKET, 0);\n\tfor (int i = 0; i < ITEM_ATTRIBUTE_MAX_NUM; ++i)\n\t\tpkTarget->SetForceAttribute(i, 0, 0);\n'
      '\t{ void Mt2009WElemClear(LPITEM); Mt2009WElemClear(pkTarget); } // %s (detach): the absorbed weapon\'s element\n' % M),
]


def main():
    with open(os.path.join(HERE, 'edits.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(EDITS, f, indent=1)
        f.write('\n')
    print('zywiolbroni: %d edits written' % len(EDITS))
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
        print('zywiolbroni: anchors %s' % ('OK' if not bad else '%d BAD' % bad))
        sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
