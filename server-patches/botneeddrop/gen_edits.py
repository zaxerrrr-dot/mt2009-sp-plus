#!/usr/bin/env python3
"""gen_edits.py -- writes edits.json of server-patches/botneeddrop (MT2009_PLUS_BOT_NEED_DROP_V1). Each edit: the file, a
marker that says it is in, the exact code it replaces (found exactly once by apply_botneeddrop.py) and the new code."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
F = "item_manager.cpp"
edits = []

# 1. the hooks' declarations (defined in the playerbot overlay, playerbot_petmat.h)
edits.append({
    "file": F,
    "marker": "MT2009_PLUS_BOT_NEED_DROP_V1 (helper)",
    "old": "bool ITEM_MANAGER::GetDropPct(LPCHARACTER pkChr, LPCHARACTER pkKiller, OUT int& iDeltaPercent, OUT int& iRandRange)\n{\n",
    "new": "// MT2009_PLUS_BOT_NEED_DROP_V1 (helper) (server-patches/botneeddrop; the owner, 7 November 2026: \"od teraz boty moga\n"
           "// otrzymywac potrzebne przedmioty na kazdym lvl. Czyli nie maja capa na drop -15%\"): a bot's kill drops an item the bot\n"
           "// needs (the playerbot overlay's kinds - a growth pet keeper's missing evolution material, playerbot_petmat.h) at the\n"
           "// chance of a kill at its own level: the level fade of GetDropPct (PERCENT_LVDELTA / _BOSS) is lifted for that row\n"
           "// alone. Every other row, and every person's kill, rolls exactly as before (one roll a row, as before). Event flag\n"
           "// m2_bot_petmat_drop_off 1 (or m2_bot_petmat_off 1): off.\n"
           "bool Mt2009PlusBotNeedDropKiller(LPCHARACTER pkKiller);\n"
           "bool Mt2009PlusBotNeedsDropItem(LPCHARACTER pkKiller, DWORD dwVnum);\n"
           "void Mt2009PlusBotNeedDropNote(LPCHARACTER pkKiller, DWORD dwVnum, bool bBypassed);\n\n"
           "bool ITEM_MANAGER::GetDropPct(LPCHARACTER pkChr, LPCHARACTER pkKiller, OUT int& iDeltaPercent, OUT int& iRandRange)\n{\n",
})

# 2. the unfaded percent of a needing bot's kill
edits.append({
    "file": F,
    "marker": "MT2009_PLUS_BOT_NEED_DROP_V1 (pct)",
    "old": "\tif (!GetDropPct(pkChr, pkKiller, iDeltaPercent, iRandRange))\n\t\treturn false;\n\n\t// MT2009_PLUS_HORSE40_V1 (drop)",
    "new": "\tif (!GetDropPct(pkChr, pkKiller, iDeltaPercent, iRandRange))\n\t\treturn false;\n\n"
           "\t// MT2009_PLUS_BOT_NEED_DROP_V1 (pct): a bot with a needed item - the percent of a kill at its own level (GetDropPct\n"
           "\t// with the monster's level raised to the bot's: no fade, every bonus as it is), for the needed rows below.\n"
           "\tint iBotNeedPercent = iDeltaPercent;\n"
           "\tconst bool bBotNeedDrop = Mt2009PlusBotNeedDropKiller(pkKiller);\n"
           "\tif (bBotNeedDrop && pkChr->GetLevel() < pkKiller->GetLevel())\n"
           "\t{\n"
           "\t\tint iNeedRandRange = iRandRange;\n"
           "\t\tif (!GetDropPct(pkKiller, pkChr->GetRaceNum(), pkChr->GetMobRank(), pkKiller->GetLevel(), pkChr->IsStone(),\n"
           "\t\t\t\tiBotNeedPercent, iNeedRandRange) || iBotNeedPercent < iDeltaPercent)\n"
           "\t\t\tiBotNeedPercent = iDeltaPercent;\n"
           "\t}\n\n"
           "\t// MT2009_PLUS_HORSE40_V1 (drop)",
})

# 3. the drop groups (mob_drop_item "drop")
edits.append({
    "file": F,
    "marker": "MT2009_PLUS_BOT_NEED_DROP_V1 (drop group)",
    "old": "\t\t\t\tauto info = v[i];\n\t\t\t\tint iPercent = (v[i].dwPct * iDeltaPercent) / 100;\n\n\t\t\t\tif (iPercent >= number(1, iRandRange))\n\t\t\t\t{\n",
    "new": "\t\t\t\tauto info = v[i];\n\t\t\t\tint iPercent = (v[i].dwPct * iDeltaPercent) / 100;\n"
           "\t\t\t\t// MT2009_PLUS_BOT_NEED_DROP_V1 (drop group): one roll a row as before; a needed row of a bot also at the\n"
           "\t\t\t\t// unfaded percent (a special group's content is not known before the roll: as before)\n"
           "\t\t\t\tconst int iNeedRoll = number(1, iRandRange);\n"
           "\t\t\t\tconst bool bNeedBypass = iPercent < iNeedRoll && bBotNeedDrop && iBotNeedPercent > iDeltaPercent &&\n"
           "\t\t\t\t\t\t!info.bSpecialGroup && (long long)v[i].dwPct * iBotNeedPercent / 100 >= (long long)iNeedRoll &&\n"
           "\t\t\t\t\t\tMt2009PlusBotNeedsDropItem(pkKiller, info.dwVnum);\n\n"
           "\t\t\t\tif (iPercent >= iNeedRoll || bNeedBypass)\n\t\t\t\t{\n",
})
edits.append({
    "file": F,
    "marker": "MT2009_PLUS_BOT_NEED_DROP_V1 (drop group note)",
    "old": "\t\t\t\t\titem = CreateItem(itemVnum, itemCount, 0, true, iRarePct, false, iAddRarePct);\n",
    "new": "\t\t\t\t\titem = CreateItem(itemVnum, itemCount, 0, true, iRarePct, false, iAddRarePct);\n"
           "\t\t\t\t\t// MT2009_PLUS_BOT_NEED_DROP_V1 (drop group note): the bots' census\n"
           "\t\t\t\t\tif (item && bBotNeedDrop)\n"
           "\t\t\t\t\t\tMt2009PlusBotNeedDropNote(pkKiller, itemVnum, bNeedBypass);\n",
})

# 4. the kill groups (mob_drop_item "kill")
edits.append({
    "file": F,
    "marker": "MT2009_PLUS_BOT_NEED_DROP_V1 (kill group)",
    "old": "\t\t\t\tint iPercent = 40000 * iDeltaPercent / pGroup->GetKillPerDrop();\n"
           "\t\t\t\tif (iPercent >= number(1, iRandRange))\n"
           "\t\t\t\t{\n"
           "\t\t\t\t\tconst CMobItemGroup::SMobItemGroupInfo& info = pGroup->GetOne();\n"
           "\t\t\t\t\tint iRarePct = info.iRarePct;\n\n"
           "\t\t\t\t\tTItemTable* table = GetTable(info.dwItemVnum);\n"
           "\t\t\t\t\tSetDropRarePct(pkChr, iRarePct, table);\n"
           "\t\t\t\t\titem = CreateItem(info.dwItemVnum, info.iCount, 0, true, iRarePct, false, iAddRarePct);\n\n"
           "\t\t\t\t\tif (item) vec_item.emplace_back(item);\n"
           "\t\t\t\t}\n",
    "new": "\t\t\t\tint iPercent = 40000 * iDeltaPercent / pGroup->GetKillPerDrop();\n"
           "\t\t\t\t// MT2009_PLUS_BOT_NEED_DROP_V1 (kill group): one roll as before; a needing bot's roll that only the\n"
           "\t\t\t\t// unfaded percent clears gives the pick only when it is a needed item (so a needed item comes at the\n"
           "\t\t\t\t// full chance, the rest of the pool at the faded one)\n"
           "\t\t\t\tconst int iNeedRoll = number(1, iRandRange);\n"
           "\t\t\t\tconst bool bNeedRoll = iPercent < iNeedRoll && bBotNeedDrop && iBotNeedPercent > iDeltaPercent &&\n"
           "\t\t\t\t\t\t40000LL * iBotNeedPercent / pGroup->GetKillPerDrop() >= (long long)iNeedRoll;\n"
           "\t\t\t\tif (iPercent >= iNeedRoll || bNeedRoll)\n"
           "\t\t\t\t{\n"
           "\t\t\t\t\tconst CMobItemGroup::SMobItemGroupInfo& info = pGroup->GetOne();\n"
           "\t\t\t\t\tif (!bNeedRoll || Mt2009PlusBotNeedsDropItem(pkKiller, info.dwItemVnum))\n"
           "\t\t\t\t\t{\n"
           "\t\t\t\t\t\tint iRarePct = info.iRarePct;\n\n"
           "\t\t\t\t\t\tTItemTable* table = GetTable(info.dwItemVnum);\n"
           "\t\t\t\t\t\tSetDropRarePct(pkChr, iRarePct, table);\n"
           "\t\t\t\t\t\titem = CreateItem(info.dwItemVnum, info.iCount, 0, true, iRarePct, false, iAddRarePct);\n"
           "\t\t\t\t\t\tif (item && bBotNeedDrop)\n"
           "\t\t\t\t\t\t\tMt2009PlusBotNeedDropNote(pkKiller, info.dwItemVnum, bNeedRoll);\n\n"
           "\t\t\t\t\t\tif (item) vec_item.emplace_back(item);\n"
           "\t\t\t\t\t}\n"
           "\t\t\t\t}\n",
})

# 5. the proto's etc drop (mob_proto drop_item / etc_drop_item.txt)
edits.append({
    "file": F,
    "marker": "MT2009_PLUS_BOT_NEED_DROP_V1 (etc drop)",
    "old": "\t\t\tint iPercent = (it->second * iDeltaPercent) / 100;\n\n"
           "\t\t\tif (iPercent >= number(1, iRandRange))\n"
           "\t\t\t{\n"
           "\t\t\t\titem = CreateItem(pkChr->GetMobDropItemVnum(), 1, 0, true);\n",
    "new": "\t\t\tint iPercent = (it->second * iDeltaPercent) / 100;\n"
           "\t\t\t// MT2009_PLUS_BOT_NEED_DROP_V1 (etc drop): one roll as before; a needed etc drop of a bot unfaded\n"
           "\t\t\tconst int iNeedRoll = number(1, iRandRange);\n"
           "\t\t\tconst bool bNeedBypass = iPercent < iNeedRoll && bBotNeedDrop && iBotNeedPercent > iDeltaPercent &&\n"
           "\t\t\t\t\t(long long)it->second * iBotNeedPercent / 100 >= (long long)iNeedRoll &&\n"
           "\t\t\t\t\tMt2009PlusBotNeedsDropItem(pkKiller, pkChr->GetMobDropItemVnum());\n\n"
           "\t\t\tif (iPercent >= iNeedRoll || bNeedBypass)\n"
           "\t\t\t{\n"
           "\t\t\t\titem = CreateItem(pkChr->GetMobDropItemVnum(), 1, 0, true);\n"
           "\t\t\t\tif (item && bBotNeedDrop)\n"
           "\t\t\t\t\tMt2009PlusBotNeedDropNote(pkKiller, pkChr->GetMobDropItemVnum(), bNeedBypass);\n",
})

with open(os.path.join(HERE, "edits.json"), "w") as f:
    json.dump(edits, f, indent=1)
print("botneeddrop: %d edits written" % len(edits))
