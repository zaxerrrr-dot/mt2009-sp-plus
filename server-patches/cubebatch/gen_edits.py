#!/usr/bin/env python3
"""gen_edits.py [game/src] -- writes edits.json of server-patches/cubebatch (MT2009_PLUS_CUBE_BATCH_V1) and checks every
anchor is found exactly once in the given engine tree (default: the test tree, already patched by every other server
patch).

Discord, 9 November 2026: "nie przerabia sokow wody po 200 szt. Loga (wylogowuje / rozlacza)". The crafting window
(client root/uicuberenewal.py, MT2009_PLUS_CUBE_RENEWAL_V1) made N attempts by sending "/cube make" N times in one frame
(200 for a full stack of Sok z Kwiatu Brzoskwini + Kwiat Ognisty -> Woda Sim at Yu-Hwan / Huahn-So). interpret_command
lets 10 commands through per 500 ms (ENABLE_ANTI_CMD_FLOOD) - the rest were dropped, so only 5-14 attempts ran - and
CInputMain::Analyze closes the connection at 300 packets in one second (hack_log "FLOOD_HEADER_3", HEADER_CG_CHAT):
one 200 batch plus a second click, or the window's own "/cube del" / "/cube add" / "/cube pick", and the player was out.

The fix: "/cube make <n>" (a number, 1-200) is one command for n attempts - Cube_make_batch (cube.cpp):
  * a plain recipe (one reward, no set / copy_attr / fail_keep): n is cut to what the window's materials, the Yang and
    the Gaya allow; the n rolls are made, the materials taken at once (one update per stack), the Yang and Gaya at once,
    the chance-raising item one piece per boosted attempt (as Cube_make_window), the results given as full stacks
    (200 a piece; a blend item or an unstackable one each attempt alone - a blend's value is rolled per item); one
    "CubeBatch <ok> <tried> <vnum> <count>" back, two cube log rows (the successes with their count, the failures);
  * any other recipe: Cube_make_window n times inside the same command, stopping when an attempt took nothing.
"/cube make" (no argument: one attempt) and "/cube make all" (a word: until the first failure, the old loop) stay."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else "/opt/metin2/mt2009plustest/linux-port/docker/game/src/server/game/src"
M = "MT2009_PLUS_CUBE_BATCH_V1"

edits = []


def edit(file, tag, old, new):
    edits.append({"file": file, "marker": "%s (%s)" % (M, tag), "old": old, "new": new})


# 1. the declaration
edit("cube.h", "decl",
     "bool Cube_make_window (LPCHARACTER ch);\n",
     "bool Cube_make_window (LPCHARACTER ch);\n"
     "// MT2009_PLUS_CUBE_BATCH_V1 (decl): \"/cube make <n>\" - n attempts in one command (server-patches/cubebatch)\n"
     "int Cube_make_batch (LPCHARACTER ch, int iTimes);\n")

# 2. the batch itself, after Cube_make
edit("cube.cpp", "batch",
     "\treturn false;\n}\n\nvoid Cube_show_list (LPCHARACTER ch)\n",
     "\treturn false;\n}\n\n"
     "// MT2009_PLUS_CUBE_BATCH_V1 (batch): \"/cube make <n>\" (server-patches/cubebatch, Discord 9 November 2026: 200 juices\n"
     "// at once logged the player out). The crafting window sent \"/cube make\" n times in one frame - 10 commands per 500 ms\n"
     "// pass (cmd.cpp, ENABLE_ANTI_CMD_FLOOD) and 300 packets in a second close the connection (input_main.cpp,\n"
     "// FLOOD_HEADER_3). Now one command: a plain recipe's n attempts are rolled together, the materials, Yang and Gaya taken\n"
     "// at once and the results given as full stacks; any other recipe runs Cube_make_window n times. The client gets one\n"
     "// \"CubeBatch <ok> <tried> <vnum> <count>\" at the end (root/uicuberenewal.py).\n"
     "static const int MT2009_CUBE_BATCH_MAX = 200;\n"
     "\n"
     "static int Mt2009CubeBatchHave (LPITEM* items, DWORD dwVnum)\n"
     "{\n"
     "\tint iCount = 0;\n"
     "\tfor (int i = 0; i < CUBE_MAX_NUM; ++i)\n"
     "\t\tif (items[i] && items[i]->GetVnum() == dwVnum)\n"
     "\t\t\tiCount += (int)items[i]->GetCount();\n"
     "\treturn iCount;\n"
     "}\n"
     "\n"
     "int Cube_make_batch (LPCHARACTER ch, int iTimes)\n"
     "{\n"
     "\tif (NULL == ch)\n"
     "\t\treturn 0;\n"
     "\tiTimes = MINMAX(1, iTimes, MT2009_CUBE_BATCH_MAX);\n"
     "\tLPCHARACTER npc = ch->IsCubeOpen() ? ch->GetQuestNPC() : NULL;\n"
     "\tLPITEM* items = ch->GetCubeItem();\n"
     "\tCUBE_DATA* pCube = npc ? Mt2009CubeFindPicked(ch, items, npc->GetRaceNum()) : NULL;\n"
     "\tconst bool bPlain = pCube && !pCube->set_value && !pCube->copy_attr && !pCube->fail_keep && pCube->reward.size() == 1\n"
     "\t\t&& !pCube->item.empty() && pCube->gold >= 0 && pCube->percent > 0;\n"
     "\tif (!bPlain)\n"
     "\t{\n"
     "\t\t// one attempt after another, as before, but in this one command; an attempt that took nothing ends it (the reason\n"
     "\t\t// was said by Cube_make)\n"
     "\t\tint iOk = 0, iDone = 0;\n"
     "\t\tDWORD dwVnum = 0;\n"
     "\t\tint iCount = 0;\n"
     "\t\tfor (; iDone < iTimes; ++iDone)\n"
     "\t\t{\n"
     "\t\t\tconst int iWeightBefore = Mt2009CubeWindowWeight(ch->GetCubeItem());\n"
     "\t\t\tconst bool bOk = Cube_make_window(ch);\n"
     "\t\t\tif (!bOk && Mt2009CubeWindowWeight(ch->GetCubeItem()) == iWeightBefore)\n"
     "\t\t\t\tbreak;\n"
     "\t\t\tif (bOk)\n"
     "\t\t\t{\n"
     "\t\t\t\t++iOk;\n"
     "\t\t\t\tif (pCube && pCube->reward.size() == 1)\n"
     "\t\t\t\t{\n"
     "\t\t\t\t\tdwVnum = pCube->reward[0].vnum;\n"
     "\t\t\t\t\tiCount += pCube->reward[0].count;\n"
     "\t\t\t\t}\n"
     "\t\t\t}\n"
     "\t\t\tif (!pCube || pCube->set_value || pCube->copy_attr || pCube->fail_keep)\n"
     "\t\t\t{\n"
     "\t\t\t\t++iDone;\n"
     "\t\t\t\tbreak; // a set / copied / kept piece is one item - never again on the window's next stack\n"
     "\t\t\t}\n"
     "\t\t}\n"
     "\t\tch->ChatPacket(CHAT_TYPE_COMMAND, \"CubeBatch %d %d %u %d\", iOk, iDone, dwVnum, iCount);\n"
     "\t\treturn iOk;\n"
     "\t}\n"
     "\n"
     "\t// how many attempts the window's materials, the Yang and the Gaya pay for\n"
     "\tstd::map<DWORD, int> mapNeed;\n"
     "\tfor (size_t i = 0; i < pCube->item.size(); ++i)\n"
     "\t\tif (pCube->item[i].count > 0)\n"
     "\t\t\tmapNeed[pCube->item[i].vnum] += pCube->item[i].count;\n"
     "\tint iTimesOk = iTimes;\n"
     "\tfor (std::map<DWORD, int>::const_iterator it = mapNeed.begin(); it != mapNeed.end(); ++it)\n"
     "\t\tiTimesOk = MIN(iTimesOk, Mt2009CubeBatchHave(items, it->first) / it->second);\n"
     "\tif (pCube->gold > 0 && ch->GetGold() / pCube->gold < (YANG)iTimesOk)\n"
     "\t\tiTimesOk = (int)(ch->GetGold() / pCube->gold);\n"
     "\tif (pCube->gaya > 0 && ch->GetGaya() / pCube->gaya < iTimesOk)\n"
     "\t\tiTimesOk = ch->GetGaya() / pCube->gaya;\n"
     "\tif (iTimesOk <= 0)\n"
     "\t{\n"
     "\t\tconst bool bOk = Cube_make_window(ch); // not even one: its own refusal (\"Not enough Yang\", the Gaya ...)\n"
     "\t\tch->ChatPacket(CHAT_TYPE_COMMAND, \"CubeBatch %d %d %u %d\", bOk ? 1 : 0, bOk ? 1 : 0, pCube->reward[0].vnum,\n"
     "\t\t\tbOk ? pCube->reward[0].count : 0);\n"
     "\t\treturn bOk ? 1 : 0;\n"
     "\t}\n"
     "\n"
     "\t// the chance-raising item: its bonus on as many attempts as it has pieces (one piece an attempt, Cube_make_window)\n"
     "\tint iBonus = 0;\n"
     "\tLPITEM pImprove = Mt2009CubeImproveItem(ch, pCube, npc->GetRaceNum(), &iBonus);\n"
     "\tif (pImprove && (iBonus <= 0 || pCube->percent >= 100))\n"
     "\t\tpImprove = NULL;\n"
     "\tconst DWORD dwImproveId = pImprove ? pImprove->GetID() : 0;\n"
     "\tconst int iBoosted = pImprove ? MIN(iTimesOk, (int)pImprove->GetCount()) : 0;\n"
     "\tint iOk = 0;\n"
     "\tfor (int i = 0; i < iTimesOk; ++i)\n"
     "\t\tif (number(1, 100) <= (i < iBoosted ? MIN(100, pCube->percent + iBonus) : pCube->percent))\n"
     "\t\t\t++iOk;\n"
     "\n"
     "\t// everything taken at once: one update per stack\n"
     "\tfor (std::map<DWORD, int>::const_iterator it = mapNeed.begin(); it != mapNeed.end(); ++it)\n"
     "\t\tFN_remove_material(items, it->first, it->second * iTimesOk);\n"
     "\tif (pCube->gaya > 0)\n"
     "\t\tch->ChangeGaya(-pCube->gaya * iTimesOk, \"CUBE\");\n"
     "\tif (pCube->gold > 0)\n"
     "\t\tch->ChangeGold(-(pCube->gold * (YANG)iTimesOk));\n"
     "\tif (iBoosted > 0)\n"
     "\t{\n"
     "\t\tLPITEM pUsed = ch->FindItemByID(dwImproveId);\n"
     "\t\tif (pUsed)\n"
     "\t\t\tpUsed->SetCount(pUsed->GetCount() - MIN((ITEM_COUNT)iBoosted, pUsed->GetCount()));\n"
     "\t\tch->ChatPacket(CHAT_TYPE_INFO, \"Szansa podwy\\277szona o %d%% (zu\\277yto %d przedm.).\", iBonus, iBoosted);\n"
     "\t}\n"
     "\n"
     "\t// the results: full stacks; a blend item (its value rolled per item) or an unstackable one each attempt alone\n"
     "\tconst CUBE_VALUE& rReward = pCube->reward[0];\n"
     "\tconst TItemTable* pTable = ITEM_MANAGER::instance().GetTable(rReward.vnum);\n"
     "\tconst bool bStack = pTable && (pTable->dwFlags & ITEM_FLAG_STACKABLE) && pTable->bType != ITEM_BLEND;\n"
     "\tconst long long llTotal = (long long)rReward.count * iOk;\n"
     "\tDWORD dwFirstId = 0;\n"
     "\tif (bStack)\n"
     "\t{\n"
     "\t\tfor (long long llLeft = llTotal; llLeft > 0; )\n"
     "\t\t{\n"
     "\t\t\tconst ITEM_COUNT iChunk = (ITEM_COUNT)MIN(llLeft, (long long)ITEM_MAX_COUNT);\n"
     "\t\t\tLPITEM pNew = ch->AutoGiveItem(rReward.vnum, iChunk);\n"
     "\t\t\tif (pNew && !dwFirstId)\n"
     "\t\t\t\tdwFirstId = pNew->GetID();\n"
     "\t\t\tllLeft -= iChunk;\n"
     "\t\t}\n"
     "\t}\n"
     "\telse\n"
     "\t{\n"
     "\t\tfor (int i = 0; i < iOk; ++i)\n"
     "\t\t{\n"
     "\t\t\tLPITEM pNew = ch->AutoGiveItem(rReward.vnum, rReward.count);\n"
     "\t\t\tif (pNew && !dwFirstId)\n"
     "\t\t\t\tdwFirstId = pNew->GetID();\n"
     "\t\t}\n"
     "\t}\n"
     "\n"
     "\tif (iOk > 0)\n"
     "\t\tLogManager::instance().CubeLog(ch->GetPlayerID(), ch->GetX(), ch->GetY(), rReward.vnum, dwFirstId, (int)llTotal, true);\n"
     "\tif (iOk < iTimesOk) // the window says \"Udane proby: ok z n\"\n"
     "\t\tLogManager::instance().CubeLog(ch->GetPlayerID(), ch->GetX(), ch->GetY(), rReward.vnum, 0, 0, false);\n"
     "\tsys_log(0, \"CUBE BATCH %s: npc %u reward %u x%d - %d of %d attempts (asked %d)\", ch->GetName(),\n"
     "\t\t(unsigned int)npc->GetRaceNum(), rReward.vnum, rReward.count, iOk, iTimesOk, iTimes);\n"
     "\tch->ChatPacket(CHAT_TYPE_COMMAND, \"CubeBatch %d %d %u %d\", iOk, iTimesOk, rReward.vnum, (int)llTotal);\n"
     "\treturn iOk;\n"
     "}\n\n"
     "void Cube_show_list (LPCHARACTER ch)\n")

# 3. the command: a number is the batch; a word keeps the old "until the first failure" loop
edit("cmd_general.cpp", "make",
     "\t\tcase 'm':\t// make (Cube_make_window: with the window's chance-raising item)\n"
     "\t\t\tif (0 != arg2[0])\n"
     "\t\t\t{\n"
     "\t\t\t\twhile (true == Cube_make_window(ch))\n"
     "\t\t\t\t\tsys_log(1, \"cube make success\");\n"
     "\t\t\t}\n"
     "\t\t\telse\n"
     "\t\t\t\tCube_make_window(ch);\n"
     "\t\t\tbreak;\n",
     "\t\tcase 'm':\t// make (Cube_make_window: with the window's chance-raising item)\n"
     "\t\t\tif (0 != arg2[0] && isdigit(*arg2)) // MT2009_PLUS_CUBE_BATCH_V1 (make): \"/cube make <n>\" - n attempts in one command\n"
     "\t\t\t\tCube_make_batch(ch, atoi(arg2));\n"
     "\t\t\telse if (0 != arg2[0])\n"
     "\t\t\t{\n"
     "\t\t\t\twhile (true == Cube_make_window(ch))\n"
     "\t\t\t\t\tsys_log(1, \"cube make success\");\n"
     "\t\t\t}\n"
     "\t\t\telse\n"
     "\t\t\t\tCube_make_window(ch);\n"
     "\t\t\tbreak;\n")

for e in edits:
    text = open(os.path.join(SRC, e["file"]), "rb").read().decode("latin-1").replace("\r\n", "\n")
    if e["marker"] in text:
        print("%s: already there" % e["marker"])
        continue
    n = text.count(e["old"])
    if n != 1:
        sys.exit("%s: anchor found %d times in %s" % (e["marker"], n, e["file"]))
json.dump(edits, open(os.path.join(HERE, "edits.json"), "w"), indent=1, ensure_ascii=True)
print("edits.json: %d edit(s)" % len(edits))
