#!/usr/bin/env python3
"""gen_edits.py [<game/src>] - writes edits.json of server-patches/sesja (MT2009_PLUS_FARM_SESSION_V1, README.md)
from the code below; the developer's tool (the apply scripts read edits.json only). With a game/src dir it also checks
that every edit's code is there exactly once (or its marker is). Applied LAST (after pety). The logic is the overlay's
dr_farm_session.cpp / dr_farm_session.h (Digi Rasta's p-sesja-farmienia, its marker DR_FARM_SESSION_V1 kept: every
insertion is under #ifdef DR_FARM_SESSION_V1, the define this patch adds to CommonDefines.h)."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
M = 'MT2009_PLUS_FARM_SESSION_V1'
E = []


def add(f, tag, old, new):
    E.append(dict(file=f, marker='%s (%s)' % (M, tag), old=old, new=new))


def ifdef(tag, what, body, indent=''):
    """An insertion: '#ifdef DR_FARM_SESSION_V1 // <marker>: <what>', the body, '#endif'."""
    return ('#ifdef DR_FARM_SESSION_V1 // %s (%s): %s\n' % (M, tag, what)) + body + '#endif\n'


INC = '#\tinclude "dr_farm_session.h"\n'

# --- CommonDefines.h: the define (the package's DR_FARM_DEBUG stays out: a test build adds it by hand)
add('../../common/CommonDefines.h', 'define',
    '#define ENABLE_CHANGELOOK_SYSTEM\n',
    '#define ENABLE_CHANGELOOK_SYSTEM\n'
    '// ' + M + ' (define): Sesja farmienia (server-patches/sesja) - Digi Rasta\'s p-sesja-farmienia, its own define:\n'
    '// dr_farm_session.cpp / .h (the overlay) and the hooks of the patch are under it. //#define DR_FARM_DEBUG: a test\n'
    '// build only (every line to the client in the syslog, /sesja start 60).\n'
    '#define DR_FARM_SESSION_V1\n')

# --- the includes
for f in ('char.cpp', 'input_login.cpp', 'main.cpp', 'cmd_general.cpp', 'char_item.cpp'):
    add(f, 'include',
        '#include "char_manager.h"\n',
        '#include "char_manager.h"\n' + ifdef('include', 'the farm session (dr_farm_session.h)', INC))
add('char_battle.cpp', 'include',
    '#include "playerbot_manager.h"\n',
    '#include "playerbot_manager.h"\n' + ifdef('include', 'the kills, the exp and the drop of the farm session', INC))
add('item.cpp', 'include',
    '#include "../../common/CommonDefines.h"\n',
    '#include "../../common/CommonDefines.h"\n' + ifdef('include', 'the owner of a kill\'s item may count it', INC))

# --- main.cpp: the tables at the core's start
add('main.cpp', 'start',
    '\tOXEvent_manager.Initialize();\n',
    '\tOXEvent_manager.Initialize();\n'
    + ifdef('start', 'the tables player.dr_farm_* (dr_farm_session.cpp, CREATE TABLE IF NOT EXISTS)',
            '\tDrFarmInit();\n'))

# --- cmd.cpp / cmd_general.cpp: /sesja
add('cmd.cpp', 'declare',
    'ACMD(do_towarzysz);\n',
    'ACMD(do_towarzysz);\n' + ifdef('declare', '/sesja, the farm session (dr_farm_session.cpp)', 'ACMD(do_sesja);\n'))
add('cmd.cpp', 'table',
    '\t{ "towarzysz",\tdo_towarzysz,\t0,\t\t\tPOS_DEAD,\tGM_PLAYER\t},\n',
    '\t{ "towarzysz",\tdo_towarzysz,\t0,\t\t\tPOS_DEAD,\tGM_PLAYER\t},\n'
    + ifdef('table', '/sesja', '\t{ "sesja",\tdo_sesja,\t0,\t\t\tPOS_DEAD,\tGM_PLAYER\t},\n'))
add('cmd_general.cpp', 'command',
    '// "Towarzysz", the player\'s own companion (playerbot_sidekick.h): the\n',
    ifdef('command', '"/sesja start <sec>|pauza|wznow|koniec|stan|pelne|historia|stat" - the Y window sends these, a\n'
          '// player may type them too (dr_farm_session.cpp answers with FarmInfo and the rest)',
          'ACMD(do_sesja)\n'
          '{\n'
          '\tif (!ch || !ch->GetDesc())\n'
          '\t\treturn;\n'
          '\tDrFarmCommand(ch, argument);\n'
          '}\n') + '\n'
    '// "Towarzysz", the player\'s own companion (playerbot_sidekick.h): the\n')

# --- input_login.cpp: the open session at the entry (humans only; DrFarmIsHuman also leaves out registered bots)
add('input_login.cpp', 'enter',
    '\t\tch->playerData->SendSpecialFlagsToClient(ch);\n\n',
    '\t\tch->playerData->SendSpecialFlagsToClient(ch);\n\n'
    + ifdef('enter', 'the open farm session of the player is read (dr_farm_session.cpp), humans only',
            '\tif (!d->IsBot())\n\t\tDrFarmOnEnterGame(ch);\n') + '\n')

# --- char.cpp: the logout, a change of channel or core
add('char.cpp', 'logout',
    '\t\tCatchKingOnDisconnect(this);\n\t}\n',
    '\t\tCatchKingOnDisconnect(this);\n\t}\n'
    + ifdef('logout', 'the farm session stops counting and is written (a logout, a change of channel or of core)',
            '\tDrFarmOnDisconnect(this);\n'))

# --- item.cpp: the owner of a kill's item may count it at its pick-up
add('item.cpp', 'owner',
    '\tm_dwOwnershipPID = ch->GetPlayerID();\n',
    '\tm_dwOwnershipPID = ch->GetPlayerID();\n'
    + ifdef('owner', 'the owner may count a kill\'s item at its pick-up (dr_farm_session.h)',
            '\tif (g_iDrFarmActive)\n\t\tDrFarmTagOwner(m_dwVID, m_dwOwnershipPID);\n'))

# --- char_battle.cpp: RewardGold's yang on the ground (the boss split and the plain one)
add('char_battle.cpp', 'ground yang boss',
    '\t\t\t\titem->AddToGround(GetMapIndex(), pos);\n\t\t\t\titem->StartDestroyEvent();\n\n\t\t\t\tiTotalGold += iGold; // Total gold\n',
    '\t\t\t\titem->AddToGround(GetMapIndex(), pos);\n'
    + ifdef('ground yang boss', 'a boss\'s yang counts at its pick-up (dr_farm_session.h)',
            '\t\t\t\tif (g_iDrFarmActive)\n\t\t\t\t\tDrFarmTagGroundYang(item, this, pkAttacker);\n')
    + '\t\t\t\titem->StartDestroyEvent();\n\n\t\t\t\tiTotalGold += iGold; // Total gold\n')
add('char_battle.cpp', 'ground yang',
    '\t\t\t\t\tpos.y = GetY() + (number(-7, 7) * 20);\n\n\t\t\t\t\titem->AddToGround(GetMapIndex(), pos);\n\t\t\t\t\titem->StartDestroyEvent();\n',
    '\t\t\t\t\tpos.y = GetY() + (number(-7, 7) * 20);\n\n\t\t\t\t\titem->AddToGround(GetMapIndex(), pos);\n'
    + ifdef('ground yang', 'yang on the ground counts at its pick-up (dr_farm_session.h)',
            '\t\t\t\t\tif (g_iDrFarmActive)\n\t\t\t\t\t\tDrFarmTagGroundYang(item, this, pkAttacker);\n')
    + '\t\t\t\t\titem->StartDestroyEvent();\n')

# --- char_battle.cpp: Reward - the kill (after KillLog) and the scope of the kill's rewards
add('char_battle.cpp', 'kill',
    '\t\tCHARACTER_MANAGER::instance().KillLog(GetRaceNum());\n',
    '\t\tCHARACTER_MANAGER::instance().KillLog(GetRaceNum());\n'
    + ifdef('kill', 'the kill for the farm sessions of the killer (its owner\'s for a companion), its party and those\n'
            '// who hurt the victim, every rank; what the rewards below give for it (a card, a rank fruit, a rune: on the ground\n'
            '// under the killer\'s name, or straight into a bag) is its drop (dr_farm_session.h)',
            '\t\tif (g_iDrFarmActive)\n'
            '\t\t{\n'
            '\t\t\tstd::vector<LPCHARACTER> hurt;\n'
            '\t\t\tfor (TDamageMap::iterator it = m_map_kDamage.begin(); it != m_map_kDamage.end(); ++it)\n'
            '\t\t\t{\n'
            '\t\t\t\tLPCHARACTER attacker = CHARACTER_MANAGER::instance().Find(it->first);\n'
            '\t\t\t\tif (attacker)\n'
            '\t\t\t\t\thurt.push_back(attacker);\n'
            '\t\t\t}\n'
            '\t\t\tDrFarmOnKill(this, pkQuestKiller, hurt);\n'
            '\t\t}\n'
            '\t\tDrFarmKillScope drFarmKillRewards(this, pkQuestKiller);\n'))

# --- char_battle.cpp: the scope of the drop (RewardGold's GiveGold, AutoGiveItem) and the tags of the drop
add('char_battle.cpp', 'drop scope',
    '\t\tsys_log(0, "Drop money : Attacker %s", pkAttacker->GetName());\n\tRewardGold(pkAttacker);\n',
    '\t\tsys_log(0, "Drop money : Attacker %s", pkAttacker->GetName());\n'
    + ifdef('drop scope', 'the yang RewardGold gives (GiveGold) and what the drop below puts straight into a bag\n'
            '// (AutoGiveItem) count for this kill (dr_farm_session.h)',
            '\tDrFarmKillScope drFarmKillDrop(this, pkAttacker);\n')
    + '\tRewardGold(pkAttacker);\n')
add('char_battle.cpp', 'drop',
    '\tif (ITEM_MANAGER::instance().CreateDropItem(this, pkAttacker, s_vec_item) || bAwakeningDrop || bTalismanDrop)\n\t{\n',
    '\tif (ITEM_MANAGER::instance().CreateDropItem(this, pkAttacker, s_vec_item) || bAwakeningDrop || bTalismanDrop)\n\t{\n'
    + ifdef('drop', 'the kill\'s items (the awakening stone and the talisman too) count at their pick-up',
            '\t\tif (g_iDrFarmActive)\n\t\t\tDrFarmTagDrops(this, pkAttacker, s_vec_item);\n'))

# --- char_battle.cpp: GiveExp (ENABLE_NEWEXP_CALCULATION, the one this engine builds)
add('char_battle.cpp', 'exp',
    '\tto->PointChange(POINT_EXP, iExp, true);\n\tfrom->CreateFly(FLY_EXP, to);\n\t// MT2009_PLUS_NEW_PET_V1 (exp given)',
    '\tto->PointChange(POINT_EXP, iExp, true);\n'
    + ifdef('exp', 'the experience for a human\'s farm session (dr_farm_session.h)',
            '\tif (g_iDrFarmActive)\n\t\tDrFarmOnExp(to, iExp);\n')
    + '\tfrom->CreateFly(FLY_EXP, to);\n\t// MT2009_PLUS_NEW_PET_V1 (exp given)')

# --- char_item.cpp: GiveGold (the party's shares, the own share, alone)
add('char_item.cpp', 'party yang',
    '\t\t\t\t\tch->ChangeGold(iMoney);\n',
    '\t\t\t\t\tch->ChangeGold(iMoney);\n'
    + ifdef('party yang', 'a member\'s share of a kill\'s yang',
            '\t\t\t\t\tif (g_iDrFarmActive)\n\t\t\t\t\t\tDrFarmOnYang(ch, iMoney);\n'))
add('char_item.cpp', 'own yang',
    '\t\tChangeGold(dwMyAmount);\n',
    '\t\tChangeGold(dwMyAmount);\n'
    + ifdef('own yang', 'the own share of a kill\'s yang',
            '\t\tif (g_iDrFarmActive)\n\t\t\tDrFarmOnYang(this, dwMyAmount);\n'))
add('char_item.cpp', 'yang',
    '\t\tChangeGold(iAmount);\n\n\t\tif (iAmount > 1000)\n',
    '\t\tChangeGold(iAmount);\n'
    + ifdef('yang', 'a kill\'s yang',
            '\t\tif (g_iDrFarmActive)\n\t\t\tDrFarmOnYang(this, iAmount);\n')
    + '\n\t\tif (iAmount > 1000)\n')

# --- char_item.cpp: PickupItem - read before the item moves (AutoStackItem may destroy it), counted where it lands
add('char_item.cpp', 'pickup',
    '\tif (item->IsOwnership(this))\n\t{\n\t\t// MT2009_PLUS_GAYA_CURRENCY_V1 (pickup)',
    ifdef('pickup', 'a kill\'s item counts for the bag it lands in, read before it moves (dr_farm_session.h)',
          '\tconst TDrFarmPick drFarmPick = DrFarmPickBegin(item);\n')
    + '\tif (item->IsOwnership(this))\n\t{\n\t\t// MT2009_PLUS_GAYA_CURRENCY_V1 (pickup)')
add('char_item.cpp', 'pickup yang',
    '\t\t\tAddPlayerStat(PLAYER_STATS_GOLD_FLAG, item->GetCount());\n\t\t\tGiveGold(item->GetCount());\n',
    '\t\t\tAddPlayerStat(PLAYER_STATS_GOLD_FLAG, item->GetCount());\n'
    + ifdef('pickup yang', 'a kill\'s yang from the ground, for whoever GiveGold pays',
            '\t\t\tDrFarmKillScope drFarmPickYang(drFarmPick);\n')
    + '\t\t\tGiveGold(item->GetCount());\n')
add('char_item.cpp', 'pickup stacked',
    '\t\t\tauto finalItem = AutoStackItem(item);\n\t\t\tif (finalItem)\n\t\t\t{\n',
    '\t\t\tauto finalItem = AutoStackItem(item);\n\t\t\tif (finalItem)\n\t\t\t{\n'
    + ifdef('pickup stacked', 'the own bag', '\t\t\t\tif (drFarmPick.tagged)\n\t\t\t\t\tDrFarmPickDone(drFarmPick, this);\n'))
add('char_item.cpp', 'pickup add',
    '\t\t\titem->AddToCharacter(this, TItemPos(bEkwWindow, iEmptyCell)); // MT2009_PLUS_EKWIPUNEK_V1 (pickup add)\n',
    '\t\t\titem->AddToCharacter(this, TItemPos(bEkwWindow, iEmptyCell)); // MT2009_PLUS_EKWIPUNEK_V1 (pickup add)\n'
    + ifdef('pickup add', 'the own bag', '\t\t\tif (drFarmPick.tagged)\n\t\t\t\tDrFarmPickDone(drFarmPick, this);\n'))
add('char_item.cpp', 'party stacked',
    '\t\tauto finalItem = owner->AutoStackItem(item);\n\t\tif (finalItem)\n\t\t{\n',
    '\t\tauto finalItem = owner->AutoStackItem(item);\n\t\tif (finalItem)\n\t\t{\n'
    + ifdef('party stacked', 'the owner\'s bag', '\t\t\tif (drFarmPick.tagged)\n\t\t\t\tDrFarmPickDone(drFarmPick, owner);\n'))
add('char_item.cpp', 'party add',
    '\t\titem->AddToCharacter(owner, TItemPos(bEkwWindow, iEmptyCell)); // MT2009_PLUS_EKWIPUNEK_V1 (party add)\n',
    '\t\titem->AddToCharacter(owner, TItemPos(bEkwWindow, iEmptyCell)); // MT2009_PLUS_EKWIPUNEK_V1 (party add)\n'
    + ifdef('party add', 'the owner\'s bag', '\t\tif (drFarmPick.tagged)\n\t\t\tDrFarmPickDone(drFarmPick, owner);\n'))

# --- char_item.cpp: AutoGiveItem (both): what a kill hands straight into the bag (inside a DrFarmKillScope only)
add('char_item.cpp', 'give',
    '\t\titem->AddToCharacter(this, TItemPos(bEkwWindow, cell));\n',
    '\t\titem->AddToCharacter(this, TItemPos(bEkwWindow, cell));\n'
    + ifdef('give', 'a kill\'s item handed straight into the bag',
            '\t\tif (g_iDrFarmActive)\n\t\t\tDrFarmOnAutoGive(this, item->GetVnum(), item->GetCount());\n'))
add('char_item.cpp', 'give vnum found',
    '\tif (foundItem)\n\t{\n\t\tif (bMsg)\n\t\t\tChatPacketRecieveItem(this, foundItem, original_count);\n',
    '\tif (foundItem)\n\t{\n'
    + ifdef('give vnum found', 'a kill\'s item', '\t\tif (g_iDrFarmActive)\n\t\t\tDrFarmOnAutoGive(this, dwItemVnum, original_count);\n')
    + '\t\tif (bMsg)\n\t\t\tChatPacketRecieveItem(this, foundItem, original_count);\n')
add('char_item.cpp', 'give vnum stacked',
    '\t\tauto finalItem = AutoStackItem(item); // @fixme316\n\t\tif (finalItem)\n\t\t{\n',
    '\t\tauto finalItem = AutoStackItem(item); // @fixme316\n\t\tif (finalItem)\n\t\t{\n'
    + ifdef('give vnum stacked', 'a kill\'s item', '\t\t\tif (g_iDrFarmActive)\n\t\t\t\tDrFarmOnAutoGive(this, dwItemVnum, original_count);\n'))
add('char_item.cpp', 'give vnum blend',
    '\t\t\t\t\t\tinv_item->SetCount(inv_item->GetCount() + item->GetCount());\n\t\t\t\t\t\treturn inv_item;\n',
    '\t\t\t\t\t\tinv_item->SetCount(inv_item->GetCount() + item->GetCount());\n'
    + ifdef('give vnum blend', 'a kill\'s item', '\t\t\t\t\t\tif (g_iDrFarmActive)\n\t\t\t\t\t\t\tDrFarmOnAutoGive(this, dwItemVnum, original_count);\n')
    + '\t\t\t\t\t\treturn inv_item;\n')
add('char_item.cpp', 'give vnum add',
    '\t\titem->AddToCharacter(this, TItemPos(bEkwWindow, iEmptyCell));\n\t\tLogManager::instance().ItemLog(this, item, "SYSTEM", item->GetName());\n',
    '\t\titem->AddToCharacter(this, TItemPos(bEkwWindow, iEmptyCell));\n'
    + ifdef('give vnum add', 'a kill\'s item', '\t\tif (g_iDrFarmActive)\n\t\t\tDrFarmOnAutoGive(this, dwItemVnum, original_count);\n')
    + '\t\tLogManager::instance().ItemLog(this, item, "SYSTEM", item->GetName());\n')


def main():
    with open(os.path.join(HERE, 'edits.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(E, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print('edits.json: %d edits' % len(E))
    if len(sys.argv) > 1:
        bad = 0
        for e in E:
            text = open(os.path.join(sys.argv[1], e['file']), 'rb').read().decode('latin-1').replace('\r\n', '\n')
            if e['marker'] in text:
                print('  there:  %s %s' % (e['file'], e['marker']))
            elif text.count(e['old']) != 1:
                print('  MISSING (%d): %s %s' % (text.count(e['old']), e['file'], e['marker']))
                bad += 1
            else:
                print('  ok:     %s %s' % (e['file'], e['marker']))
        sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
