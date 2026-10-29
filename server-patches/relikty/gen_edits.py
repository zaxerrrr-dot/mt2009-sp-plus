#!/usr/bin/env python3
"""gen_edits.py [<game/src>] - writes edits.json of server-patches/relikty (MT2009_PLUS_RELIC_V1, README.md) from the
code below; the developer's tool (the apply scripts read edits.json only). With a game/src dir it also checks that
every edit's code is there exactly once (or its marker is). Applied last (after dmgprint / autohuntreach); its anchors are addeq's
(V2) store lines (char.h, char_item.cpp, char.cpp, item.cpp, cmd.cpp) and bonusy67's damage / cooldown lines."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
M = 'MT2009_PLUS_RELIC_V1'
E = []


def add(f, tag, old, new):
    E.append(dict(file=f, marker='%s (%s)' % (M, tag), old=old, new=new))


def mk(tag):
    return '%s (%s)' % (M, tag)


# ---- char.h: the relic cells, their slots, the methods
add('char.h', 'cells',
    "// @fixme199 BEGIN\nstruct PlayerSlotT {\n",
    "// %s: Bonus Reliktu - the two relic pages (I, II), hidden cells after the second equipment page's\n"
    "// store (window INVENTORY, cells 436-437 in the DB, after\n"
    "// the four equipment pages' blocks 308-435 of MT2009_PLUS_ADDEQ_V2); never a packet, never a client's cell - playerbot_relikty.cpp\n"
    "enum EMt2009Relic\n"
    "{\n"
    "\tMT2009_RELIC_SLOT_START = MT2009_ADDEQ_SLOT_END,\n"
    "\tMT2009_RELIC_PAGE_NUM = 2,\n"
    "\tMT2009_RELIC_SLOT_END = MT2009_RELIC_SLOT_START + MT2009_RELIC_PAGE_NUM,\n"
    "};\n\n"
    "// @fixme199 BEGIN\nstruct PlayerSlotT {\n" % mk('cells'))

add('char.h', 'slots',
    "\tstd::array<LPITEM,MT2009_ADDEQ_SLOT_END - MT2009_ADDEQ_SLOT_START> pAddeqItems{};",
    "\tstd::array<LPITEM,MT2009_RELIC_PAGE_NUM> pRelicItems{};\t// %s: the relics of the pages I / II\n"
    "\tstd::array<LPITEM,MT2009_ADDEQ_SLOT_END - MT2009_ADDEQ_SLOT_START> pAddeqItems{};" % mk('slots'))

add('char.h', 'methods',
    "Mt2009AddeqSwitch(int iPage);\n",
    "Mt2009AddeqSwitch(int iPage);\n"
    "\t\t// %s: Bonus Reliktu's relic pages, playerbot_relikty.cpp\n"
    "\t\tstatic bool\t\tMt2009RelicIsCell(WORD wCell) { return wCell >= MT2009_RELIC_SLOT_START && wCell < MT2009_RELIC_SLOT_END; }\n"
    "\t\tLPITEM\t\t\tMt2009RelicGetItem(int iPage) const;\n"
    "\t\tvoid\t\t\tMt2009RelicSetItem(WORD wCell, LPITEM pItem);\n"
    "\t\tvoid\t\t\tMt2009RelicFlushItems();\n"
    "\t\tvoid\t\t\tMt2009RelicClearItems();\n" % mk('methods'))

# ---- char_item.cpp: SetItem, ClearItem, UseItemEx
add('char_item.cpp', 'set',
    "\t// MT2009_PLUS_ADDEQ_V1 (set): a cell of the inactive equipment page's store - no packet, the client never sees it\n",
    "\t// %s: a relic page's cell - no packet, the client never sees it\n"
    "\tif (window_type == INVENTORY && Mt2009RelicIsCell(wCell))\n"
    "\t{\n"
    "\t\tMt2009RelicSetItem(wCell, pItem);\n"
    "\t\treturn;\n"
    "\t}\n\n"
    "\t// MT2009_PLUS_ADDEQ_V1 (set): a cell of the inactive equipment page's store - no packet, the client never sees it\n"
    % mk('set'))

add('char_item.cpp', 'clear',
    "\tMt2009AddeqClearItems(); // MT2009_PLUS_ADDEQ_V1 (clear): the inactive equipment page\n",
    "\tMt2009AddeqClearItems(); // MT2009_PLUS_ADDEQ_V1 (clear): the inactive equipment page\n"
    "\tMt2009RelicClearItems(); // %s: the relic pages\n" % mk('clear'))

add('char_item.cpp', 'use',
    "\tint iLimitRealtimeStartFirstUseFlagIndex = -1;\n",
    "\t// %s: a Relikt Duszy (30272-30276) goes into the relic window (playerbot_relikty.cpp)\n"
    "\t{\n"
    "\t\tint Mt2009RelicUseItem(LPCHARACTER ch, LPITEM item);\n"
    "\t\tconst int iRelicUse = Mt2009RelicUseItem(this, item);\n"
    "\t\tif (iRelicUse >= 0)\n"
    "\t\t\treturn iRelicUse != 0;\n"
    "\t}\n"
    "\tint iLimitRealtimeStartFirstUseFlagIndex = -1;\n" % mk('use'))

# ---- input_db.cpp: a second row on a relic cell goes to the bag (as addeq V2's store cells)
add('input_db.cpp', 'load',
    "\t\tif ((p->window == INVENTORY && CHARACTER::Mt2009AddeqIsCell(p->pos) && ch->Mt2009AddeqGetCellItem(p->pos)) ||\n",
    "\t\t// %s: a relic page's cell already taken - the item to the bag\n"
    "\t\tif ((p->window == INVENTORY && CHARACTER::Mt2009RelicIsCell(p->pos) &&\n"
    "\t\t\t\tch->Mt2009RelicGetItem(p->pos - MT2009_RELIC_SLOT_START)) ||\n"
    "\t\t\t\t(p->window == INVENTORY && CHARACTER::Mt2009AddeqIsCell(p->pos) && ch->Mt2009AddeqGetCellItem(p->pos)) ||\n" % mk('load'))

# ---- char.cpp: the flush before a warp, the mount
add('char.cpp', 'flush',
    "\tMt2009AddeqFlushItems(); // MT2009_PLUS_ADDEQ_V1 (flush): the inactive equipment page (before a warp)\n",
    "\tMt2009AddeqFlushItems(); // MT2009_PLUS_ADDEQ_V1 (flush): the inactive equipment page (before a warp)\n"
    "\tMt2009RelicFlushItems(); // %s: the relic pages (their time run so far first)\n" % mk('flush'))

add('char.cpp', 'mount',
    "void CHARACTER::MountVnum(DWORD vnum)\n{\n\tif (m_dwMountVnum == vnum)\n\t\treturn;\n",
    "void CHARACTER::MountVnum(DWORD vnum)\n{\n\tif (m_dwMountVnum == vnum)\n\t\treturn;\n\n"
    "\tif (IsPC()) // %s: the relic's lines of mounting / dismounting (playerbot_relikty.cpp)\n"
    "\t{\n"
    "\t\tvoid Mt2009RelicOnMount(LPCHARACTER ch, bool bMount);\n"
    "\t\tif (!m_dwMountVnum && vnum)\n"
    "\t\t\tMt2009RelicOnMount(this, true);\n"
    "\t\telse if (m_dwMountVnum && !vnum)\n"
    "\t\t\tMt2009RelicOnMount(this, false);\n"
    "\t}\n" % mk('mount'))

# ---- item.cpp: an item leaving a relic cell, no update packet of one
add('item.cpp', 'remove',
    "\t\t\t// MT2009_PLUS_ADDEQ_V1 (remove): an item of the inactive equipment page's store leaves the store\n",
    "\t\t\t// %s: a relic leaves its page\n"
    "\t\t\telse if (m_bWindow == INVENTORY && CHARACTER::Mt2009RelicIsCell(m_wCell))\n"
    "\t\t\t\tpOwner->SetItem(TItemPos(INVENTORY, m_wCell), NULL);\n"
    "\t\t\t// MT2009_PLUS_ADDEQ_V1 (remove): an item of the inactive equipment page's store leaves the store\n"
    % mk('remove'))

add('item.cpp', 'update',
    "\t// MT2009_PLUS_ADDEQ_V1 (update): the inactive equipment page's store is never sent\n",
    "\t// %s: a relic page's item is never sent (\"relikt_state\" tells the client)\n"
    "\tif (GetWindow() == INVENTORY && CHARACTER::Mt2009RelicIsCell(m_wCell))\n"
    "\t\treturn;\n\n"
    "\t// MT2009_PLUS_ADDEQ_V1 (update): the inactive equipment page's store is never sent\n" % mk('update'))

# ---- char_battle.cpp: the blows, the death
add('char_battle.cpp', 'damage',
    "\t\tdam = Bonus67Damage(this, pAttacker, (int) type, dam);\n\t}\n",
    "\t\tdam = Bonus67Damage(this, pAttacker, (int) type, dam);\n\t}\n\n"
    "\tif (pAttacker) // %s: the relic lines a blow starts (playerbot_relikty.cpp)\n"
    "\t{\n"
    "\t\tint Mt2009RelicOnDamage(LPCHARACTER pkVictim, LPCHARACTER pkAttacker, int iType, int iDam);\n"
    "\t\tdam = Mt2009RelicOnDamage(this, pAttacker, (int) type, dam);\n"
    "\t}\n" % mk('damage'))

add('char_battle.cpp', 'no death',
    "\tif (GetHP() <= 0)\n\t{\n\t\tStun();\n",
    "\tif (GetHP() <= 0 && IsPC()) // %s: \"Unikniecie smierci\" - 30%% HP back instead of the death\n"
    "\t{\n"
    "\t\tbool Mt2009RelicNoDeath(LPCHARACTER ch, LPCHARACTER pkAttacker);\n"
    "\t\tif (Mt2009RelicNoDeath(this, pAttacker))\n"
    "\t\t\treturn false;\n"
    "\t}\n\n"
    "\tif (GetHP() <= 0)\n\t{\n\t\tStun();\n" % mk('no death'))

# ---- char_skill.cpp: every cooldown reset
add('char_skill.cpp', 'skill reset',
    "\t\tm_SkillUseInfo[dwVnum].dwNextSkillUsableTime = Bonus67SkillCooldown(this, dwVnum, m_SkillUseInfo[dwVnum].dwNextSkillUsableTime);\n\t}\n",
    "\t\tm_SkillUseInfo[dwVnum].dwNextSkillUsableTime = Bonus67SkillCooldown(this, dwVnum, m_SkillUseInfo[dwVnum].dwNextSkillUsableTime);\n\t}\n\n"
    "\tif (false == m_bDisableCooltime) // %s: \"Reset umiejetnosci\" - every skill's cooldown over\n"
    "\t{\n"
    "\t\tbool Mt2009RelicSkillReset(LPCHARACTER ch, unsigned int dwVnum);\n"
    "\t\tvoid Mt2009RelicCooltimeEnd(LPCHARACTER ch, int iSkill);\n"
    "\t\tif (Mt2009RelicSkillReset(this, dwVnum))\n"
    "\t\t{\n"
    "\t\t\tfor (std::map<int, TSkillUseInfo>::iterator itRelic = m_SkillUseInfo.begin(); itRelic != m_SkillUseInfo.end(); ++itRelic)\n"
    "\t\t\t{\n"
    "\t\t\t\titRelic->second.dwNextSkillUsableTime = 0;\n"
    "\t\t\t\tMt2009RelicCooltimeEnd(this, itRelic->first);\n"
    "\t\t\t}\n"
    "\t\t}\n"
    "\t}\n" % mk('skill reset'))

# ---- item_manager.cpp: a boss's drop chance
add('item_manager.cpp', 'drop',
    "\t//iDeltaPercent = iDeltaPercent * (100 + MIN(item_drop_bonus, 225)) / 100;\n",
    "\t// %s: \"Drop z bossow\" - a boss killed: +x%% of the killer's active relic (every kill)\n"
    "\t{\n"
    "\t\tint Mt2009RelicBossDropBonus(LPCHARACTER pkKiller, unsigned char bMobRank, bool bStone);\n"
    "\t\tconst int relic_drop = Mt2009RelicBossDropBonus(pkKiller, bMobRank, IsStone);\n"
    "\t\tif (relic_drop > 0)\n"
    "\t\t\tAddToBonusItemDrop(item_drop_bonus, relic_drop);\n"
    "\t}\n"
    "\t//iDeltaPercent = iDeltaPercent * (100 + MIN(item_drop_bonus, 225)) / 100;\n" % mk('drop'))

# ---- cmd.cpp: /relikt
add('cmd.cpp', 'declare',
    "ACMD(do_addeq);\t// MT2009_PLUS_ADDEQ_V1 (declare): Druga strona ekwipunku, root/uiaddeq.py (playerbot_addeq.cpp)\n",
    "ACMD(do_addeq);\t// MT2009_PLUS_ADDEQ_V1 (declare): Druga strona ekwipunku, root/uiaddeq.py (playerbot_addeq.cpp)\n"
    "ACMD(do_relikt);\t// %s: Bonus Reliktu, root/uirelikt.py (playerbot_relikty.cpp)\n" % mk('declare'))

add('cmd.cpp', 'table',
    "\t{ \"addeq\",\tdo_addeq,\t0,\t\t\tPOS_DEAD,\tGM_PLAYER\t},\t// MT2009_PLUS_ADDEQ_V1 (table)\n",
    "\t{ \"addeq\",\tdo_addeq,\t0,\t\t\tPOS_DEAD,\tGM_PLAYER\t},\t// MT2009_PLUS_ADDEQ_V1 (table)\n"
    "\t{ \"relikt\",\tdo_relikt,\t0,\t\t\tPOS_DEAD,\tGM_PLAYER\t},\t// %s\n" % mk('table'))

for e in E:
    assert e['marker'] in e['new'], e['marker']
json.dump(E, open(os.path.join(HERE, 'edits.json'), 'w'), indent=1)
print('relikty: %d edits' % len(E))
if len(sys.argv) > 1:
    bad = 0
    for e in E:
        t = open(os.path.join(sys.argv[1], e['file']), encoding='latin-1').read().replace('\r\n', '\n')
        if e['marker'] not in t and t.count(e['old']) != 1:
            print('%s: %s - the code is there %d times' % (e['file'], e['marker'], t.count(e['old'])))
            bad += 1
    print('check: %s' % ('OK' if not bad else '%d problem(s)' % bad))
    sys.exit(1 if bad else 0)
