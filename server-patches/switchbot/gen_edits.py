#!/usr/bin/env python3
"""gen_edits.py [<engine game/src dir>] -- writes edits.json of the Bonus Switcher (Ameria's switchbot,
MT2009_PLUS_SWITCHBOT_V1, README.md). With a game/src dir, also checks that every edit's old code is there
exactly once (or its marker already is) and says what a revert would do.

Two kinds of entries:
  * an edit ("marker", "old", "new"): skipped when its marker is in the file, else "old" must be there once;
  * a revert ("revert": true, "old", "new"): takes out a line of the old bonus switcher (MT2009_PLUS_BONUS_SWITCH_V1,
    server-patches/bonusswitch - removed) when it is there (once), nothing when it is not (a fresh engine)."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
M = "MT2009_PLUS_SWITCHBOT_V1"

E = []


def edit(file, tag, old, new):
	E.append({"file": file, "marker": "%s (%s)" % (M, tag), "old": old, "new": new})


def revert(file, tag, old, new=""):
	E.append({"file": file, "revert": True, "marker": "%s (%s)" % (M, tag), "old": old, "new": new})


# ---------------------------------------------------------------- the old bonus switcher out (MT2009_PLUS_BONUS_SWITCH_V1)
revert("cmd.cpp", "old declare out",
	"// MT2009_PLUS_BONUS_SWITCH_V1 (declare) (Autor: Vekirion)\nACMD(do_bonus_switch);\n")
revert("cmd.cpp", "old table out",
	"\t// MT2009_PLUS_BONUS_SWITCH_V1 (table) (Autor: Vekirion)\n\t{ \"bonus_switch\",\tdo_bonus_switch,\t0,\t\tPOS_DEAD,\tGM_PLAYER\t},\n")
revert("cmd_general.cpp", "old command out",
	"// MT2009_PLUS_BONUS_SWITCH_V1 (command) (Autor: Vekirion): the bonus switcher window's\n"
	"// \"/bonus_switch info <cell> | items | start <cell> <speed> <need> <costume bonuses> <apply>:<min> ... | once <cell> | stop [cell]\"\n"
	"// (playerbot_bonus_switch.h).\n"
	"ACMD(do_bonus_switch)\n{\n\tif (!ch || !ch->GetDesc())\n\t\treturn;\n"
	"\tvoid BonusSwitchCommand(LPCHARACTER ch, const char* argument);\n\tBonusSwitchCommand(ch, argument);\n}\n\n")

# ---------------------------------------------------------------- common/length.h
L = "../../common/length.h"
edit(L, "values", "enum EWindows\n{\n",
	"// " + M + " (values): Ameria's switchbot (common/length.h SwitchbotValues) - five slots, five alternatives of\n"
	"// five bonuses each (playerbot_switchbot.cpp; the client's exe the same, client-patches/exe Server/common/length.h).\n"
	"enum SwitchbotValues\n{\n"
	"\tSWITCHBOT_SLOT_COUNT = 5,\n"
	"\tSWITCHBOT_ALTERNATIVE_COUNT = 5,\n"
	"\tSWITCHBOT_ATTR_COUNT = 5,\t// Ameria's MAX_NORM_ATTR_NUM: the five normal bonuses\n"
	"};\n\n"
	"enum EWindows\n{\n")
edit(L, "window", "\tCHEST_INVENTORY,\n\tWINDOW_TYPE_MAX,\n",
	"\tCHEST_INVENTORY,\n"
	"\t// " + M + " (window): the switchbot's slots, 16 - after every old window (the client's exe the same); no item is\n"
	"\t// ever kept here (the slot's item stays in the bag, locked), so player.item.window is not touched\n"
	"\tSWITCHBOT,\n"
	"\tWINDOW_TYPE_MAX,\n")

# ---------------------------------------------------------------- packet.h
P = "packet.h"
edit(P, "cg header", "\tHEADER_CG_FLOWER_EVENT\t\t\t= 187,\n",
	"\tHEADER_CG_FLOWER_EVENT\t\t\t= 187,\n"
	"\t// " + M + " (cg header): Ameria's switchbot - start / stop a slot (playerbot_switchbot.cpp)\n"
	"\tHEADER_CG_SWITCHBOT\t\t\t\t= 170,\n")
edit(P, "gc header", "\tHEADER_GC_FLOWER_EVENT\t\t\t\t\t= 187,\n",
	"\tHEADER_GC_FLOWER_EVENT\t\t\t\t\t= 187,\n"
	"\t// " + M + " (gc header): Ameria's switchbot - only to a client that sent \"/switchbot hello\"\n"
	"\tHEADER_GC_SWITCHBOT\t\t\t\t\t\t= 171,\n")
edit(P, "gg header", "\tHEADER_GG_DUNGEON_NEW_JUMP = 37,\n};",
	"\tHEADER_GG_DUNGEON_NEW_JUMP = 37,\n\n"
	"\t// " + M + " (gg header): a running switchbot follows its player to another core (Ameria's)\n"
	"\tHEADER_GG_SWITCHBOT = 39,\n};")
edit(P, "structs", "} TPacketCGFlowerEvent;\t\t// 4 B\n\n#pragma pack()\n#endif",
	"} TPacketCGFlowerEvent;\t\t// 4 B\n\n"
	"// " + M + " (structs): Ameria's switchbot (new_switchbot.h, common/tables.h, packet.h), fixed-size fields here -\n"
	"// the client's exe has the same (client-patches/exe UserInterface/Packet.h, static_assert of the sizes).\n"
	"struct TSwitchbotAttributeAlternativeTable\n{\n"
	"\tTPlayerItemAttribute attributes[SWITCHBOT_ATTR_COUNT];\n\n"
	"\tbool IsConfigured() const\n\t{\n"
	"\t\tfor (const auto& it : attributes)\n\t\t{\n\t\t\tif (it.bType && it.sValue)\n\t\t\t{\n\t\t\t\treturn true;\n\t\t\t}\n\t\t}\n\n"
	"\t\treturn false;\n\t}\n};\t// 15 B\n\n"
	"struct TSwitchbotTable\n{\n"
	"\tDWORD player_id;\n"
	"\tbool active[SWITCHBOT_SLOT_COUNT];\n"
	"\tbool finished[SWITCHBOT_SLOT_COUNT];\n"
	"\tDWORD items[SWITCHBOT_SLOT_COUNT];\n"
	"\tTSwitchbotAttributeAlternativeTable alternatives[SWITCHBOT_SLOT_COUNT][SWITCHBOT_ALTERNATIVE_COUNT];\n\n"
	"\tTSwitchbotTable() : player_id(0)\n\t{\n"
	"\t\tmemset(&items, 0, sizeof(items));\n"
	"\t\tmemset(&alternatives, 0, sizeof(alternatives));\n"
	"\t\tmemset(&active, false, sizeof(active));\n"
	"\t\tmemset(&finished, false, sizeof(finished));\n"
	"\t}\n};\t// 409 B\n\n"
	"struct TSwitchbotAttributeInfo\n{\n"
	"\tBYTE attribute_set;\n\tint apply_num;\n\tint max_value;\n};\t// 9 B\n\n"
	"struct TPacketGGSwitchbot\n{\n\tBYTE bHeader;\n\tWORD wPort;\n\tTSwitchbotTable table;\n};\n\n"
	"enum ECGSwitchbotSubheader\n{\n\tSUBHEADER_CG_SWITCHBOT_START,\n\tSUBHEADER_CG_SWITCHBOT_STOP,\n};\n\n"
	"struct TPacketCGSwitchbot\n{\n\tBYTE header;\n\tWORD size;\n\tBYTE subheader;\n\tBYTE slot;\n};\t// 5 B; START: + 5 alternatives\n\n"
	"enum EGCSwitchbotSubheader\n{\n\tSUBHEADER_GC_SWITCHBOT_UPDATE,\n\tSUBHEADER_GC_SWITCHBOT_UPDATE_ITEM,\n"
	"\tSUBHEADER_GC_SWITCHBOT_SEND_ATTRIBUTE_INFORMATION,\n};\n\n"
	"struct TPacketGCSwitchbot\n{\n\tBYTE header;\n\tWORD size;\n\tBYTE subheader;\n\tBYTE slot;\n};\t// 5 B\n\n"
	"struct TSwitchbotUpdateItem\n{\n"
	"\tBYTE\tslot;\n\tDWORD\tvnum;\n\tDWORD\tcount;\n"
	"\tint\t\talSockets[ITEM_SOCKET_MAX_NUM];\n"
	"\tTPlayerItemAttribute aAttr[ITEM_ATTRIBUTE_MAX_NUM];\n"
	"\tWORD\tCellInven;\n};\t// 44 B\n\n"
	"static_assert(sizeof(TSwitchbotAttributeAlternativeTable) == 15, \"switchbot alternative\");\n"
	"static_assert(sizeof(TSwitchbotTable) == 409, \"switchbot table\");\n"
	"static_assert(sizeof(TSwitchbotAttributeInfo) == 9, \"switchbot attribute info\");\n"
	"static_assert(sizeof(TPacketCGSwitchbot) == 5 && sizeof(TPacketGCSwitchbot) == 5, \"switchbot packets\");\n"
	"static_assert(sizeof(TSwitchbotUpdateItem) == 44, \"switchbot update item\");\n\n"
	"#pragma pack()\n#endif")

# ---------------------------------------------------------------- packet_info.cpp
edit("packet_info.cpp", "cg size",
	"\tSet(HEADER_CG_MINI_GAME_RUMI, sizeof(TPacketCGMiniGameRumi), \"MiniGameRumi\", true);\n",
	"\tSet(HEADER_CG_MINI_GAME_RUMI, sizeof(TPacketCGMiniGameRumi), \"MiniGameRumi\", true);\n"
	"\t// " + M + " (cg size): Ameria's switchbot, 5 bytes + what the handler reads, with the sequence byte\n"
	"\tSet(HEADER_CG_SWITCHBOT, sizeof(TPacketCGSwitchbot), \"Switchbot\", true);\n")
edit("packet_info.cpp", "gg size",
	"\tSet(HEADER_GG_DUNGEON_NEW_JUMP, sizeof(TPacketGGDungeonNewJump), \"DungeonNewJump\", false);\n",
	"\tSet(HEADER_GG_DUNGEON_NEW_JUMP, sizeof(TPacketGGDungeonNewJump), \"DungeonNewJump\", false);\n"
	"\t// " + M + " (gg size)\n"
	"\tSet(HEADER_GG_SWITCHBOT, sizeof(TPacketGGSwitchbot), \"Switchbot\", false);\n")

# ---------------------------------------------------------------- input_main.cpp
I = "input_main.cpp"
edit(I, "packet",
	"\t\tcase HEADER_CG_MINI_GAME_RUMI:\n\t\t\t{\n\t\t\t\tvoid RumiPacket(LPCHARACTER ch, const char* data);\n"
	"\t\t\t\tRumiPacket(ch, c_pData);\n\t\t\t}\n\t\t\tbreak;\n",
	"\t\tcase HEADER_CG_MINI_GAME_RUMI:\n\t\t\t{\n\t\t\t\tvoid RumiPacket(LPCHARACTER ch, const char* data);\n"
	"\t\t\t\tRumiPacket(ch, c_pData);\n\t\t\t}\n\t\t\tbreak;\n\n"
	"\t\t// " + M + " (packet): Ameria's switchbot - start / stop a slot (playerbot_switchbot.cpp)\n"
	"\t\tcase HEADER_CG_SWITCHBOT:\n\t\t\t{\n"
	"\t\t\t\tint Mt2009SwitchbotPacket(LPCHARACTER ch, const char* data, size_t uiBytes);\n"
	"\t\t\t\tif ((iExtraLen = Mt2009SwitchbotPacket(ch, c_pData, m_iBufferLeft)) < 0)\n\t\t\t\t\treturn -1;\n"
	"\t\t\t}\n\t\t\tbreak;\n")
edit(I, "move",
	"\tstruct command_item_move * pinfo = (struct command_item_move *) data;\n\n\tif (ch)\n"
	"\t\tch->MoveItem(pinfo->Cell, pinfo->CellTo, pinfo->count);\n",
	"\tstruct command_item_move * pinfo = (struct command_item_move *) data;\n\n"
	"\t// " + M + " (move): into / out of a switchbot slot (Ameria's MoveItem, IsSwitchbotPosition)\n"
	"\tbool Mt2009SwitchbotItemMove(LPCHARACTER ch, const TItemPos& Cell, const TItemPos& DestCell);\n"
	"\tif (ch && Mt2009SwitchbotItemMove(ch, pinfo->Cell, pinfo->CellTo))\n\t\treturn;\n\n"
	"\tif (ch)\n"
	"\t\tch->MoveItem(pinfo->Cell, pinfo->CellTo, pinfo->count);\n")
edit(I, "use",
	"void CInputMain::ItemUse(LPCHARACTER ch, const char * data)\n{\n"
	"\tch->UseItem(((struct command_item_use *) data)->Cell);\n}\n",
	"void CInputMain::ItemUse(LPCHARACTER ch, const char * data)\n{\n"
	"\t// " + M + " (use): a switchbot slot's item taken out (Ameria's UseItem)\n"
	"\tbool Mt2009SwitchbotItemUse(LPCHARACTER ch, const TItemPos& Cell);\n"
	"\tif (Mt2009SwitchbotItemUse(ch, ((struct command_item_use *) data)->Cell))\n\t\treturn;\n\n"
	"\tch->UseItem(((struct command_item_use *) data)->Cell);\n}\n")

# ---------------------------------------------------------------- input_p2p.cpp
edit("input_p2p.cpp", "p2p",
	"\t\tcase HEADER_GG_DUNGEON_NEW_JUMP:\n\t\t\tquest::Mt2009PlusDungeonNewJumpRecv(c_pData);\n\t\t\tbreak;\n",
	"\t\tcase HEADER_GG_DUNGEON_NEW_JUMP:\n\t\t\tquest::Mt2009PlusDungeonNewJumpRecv(c_pData);\n\t\t\tbreak;\n\n"
	"\t\t// " + M + " (p2p): a running switchbot of a player coming to this core (Ameria's)\n"
	"\t\tcase HEADER_GG_SWITCHBOT:\n\t\t\t{\n"
	"\t\t\t\tvoid Mt2009SwitchbotP2P(const char* c_pData);\n"
	"\t\t\t\tMt2009SwitchbotP2P(c_pData);\n\t\t\t}\n\t\t\tbreak;\n")

# ---------------------------------------------------------------- char.cpp
C = "char.cpp"
edit(C, "warp", "\tp.wPort\t= wPort;\n\n\tGetDesc()->Packet(p);\n",
	"\tp.wPort\t= wPort;\n\n"
	"\t// " + M + " (warp): Ameria's - the switchbot pauses, to another core it goes along (playerbot_switchbot.cpp)\n"
	"\t{\n\t\tvoid Mt2009SwitchbotWarp(LPCHARACTER ch, WORD wPort);\n\t\tMt2009SwitchbotWarp(this, p.wPort);\n\t}\n\n"
	"\tGetDesc()->Packet(p);\n")
edit(C, "channel", "\tp.wPort\t= newPort;\n\tGetDesc()->Packet(p);\n",
	"\tp.wPort\t= newPort;\n"
	"\t// " + M + " (channel): Ameria's, as at a warp\n"
	"\t{\n\t\tvoid Mt2009SwitchbotWarp(LPCHARACTER ch, WORD wPort);\n\t\tMt2009SwitchbotWarp(this, p.wPort);\n\t}\n"
	"\tGetDesc()->Packet(p);\n")
edit(C, "logout", "\tMessengerManager::instance().Logout(GetName());\n",
	"\tMessengerManager::instance().Logout(GetName());\n\n"
	"\t// " + M + " (logout): Ameria's ItemSaveSwitchbot; a real logout (no warp) stops the slots\n"
	"\t{\n\t\tvoid Mt2009SwitchbotDisconnect(LPCHARACTER ch);\n\t\tMt2009SwitchbotDisconnect(this);\n\t}\n")

# ---------------------------------------------------------------- char_item.cpp
CI = "char_item.cpp"
edit(CI, "equip",
	"bool CHARACTER::CanEquipNow(const LPITEM item, const TItemPos& srcCell, const TItemPos& destCell) /*const*/\n{\n",
	"bool CHARACTER::CanEquipNow(const LPITEM item, const TItemPos& srcCell, const TItemPos& destCell) /*const*/\n{\n"
	"\t// " + M + " (equip): Ameria's - an item in a switchbot slot (locked) is not put on\n"
	"\t{\n\t\tbool Mt2009SwitchbotRefuseEquip(LPCHARACTER ch, LPITEM item);\n"
	"\t\tif (Mt2009SwitchbotRefuseEquip(this, item))\n\t\t\treturn false;\n\t}\n\n")
edit(CI, "swap",
	"\t    sys_log(0, \"[WARNING][WARNING][HACK USER!] : %s %d %d\", m_stName.c_str(), bCell, bDestCell);\n"
	"\t    return false;\n\t}\n\n"
	"\tif (!IsEmptyItemGrid(TItemPos (INVENTORY, item1->GetCell()), item2->GetSize(), item1->GetCell()))\n",
	"\t    sys_log(0, \"[WARNING][WARNING][HACK USER!] : %s %d %d\", m_stName.c_str(), bCell, bDestCell);\n"
	"\t    return false;\n\t}\n\n"
	"\t// " + M + " (swap): Ameria's - no swap of a locked item (a switchbot slot's)\n"
	"\tif (item1->isLocked() || item2->isLocked())\n\t\treturn false;\n\n"
	"\tif (!IsEmptyItemGrid(TItemPos (INVENTORY, item1->GetCell()), item2->GetSize(), item1->GetCell()))\n")

# ---------------------------------------------------------------- cmd.cpp
edit("cmd.cpp", "declare",
	"ACMD(do_ekwipunek);\t// MT2009_PLUS_EKWIPUNEK_V1 (declare): Dodatkowy ekwipunek, root/uiekwipunek.py (playerbot_ekwipunek.cpp)\n",
	"ACMD(do_ekwipunek);\t// MT2009_PLUS_EKWIPUNEK_V1 (declare): Dodatkowy ekwipunek, root/uiekwipunek.py (playerbot_ekwipunek.cpp)\n"
	"ACMD(do_switchbot);\t// " + M + " (declare): \"/switchbot hello\", root/uiswitchbot.py (playerbot_switchbot.cpp)\n")
edit("cmd.cpp", "table",
	"\t{ \"ekwipunek\",\tdo_ekwipunek,\t0,\t\t\tPOS_DEAD,\tGM_PLAYER\t},\t// MT2009_PLUS_EKWIPUNEK_V1 (table)\n",
	"\t{ \"ekwipunek\",\tdo_ekwipunek,\t0,\t\t\tPOS_DEAD,\tGM_PLAYER\t},\t// MT2009_PLUS_EKWIPUNEK_V1 (table)\n"
	"\t{ \"switchbot\",\tdo_switchbot,\t0,\t\t\tPOS_DEAD,\tGM_PLAYER\t},\t// " + M + " (table)\n")


def main():
	out = os.path.join(HERE, "edits.json")
	with open(out, "w", encoding="utf-8", newline="\n") as f:
		json.dump(E, f, indent=1, ensure_ascii=False)
		f.write("\n")
	print("switchbot: %d entries -> %s" % (len(E), out))
	if len(sys.argv) > 1:
		src = sys.argv[1]
		bad = 0
		for e in E:
			text = open(os.path.join(src, e["file"]), "rb").read().decode("latin-1").replace("\r\n", "\n")
			n = text.count(e["old"])
			if e.get("revert"):
				print("  %-28s %s: %s" % (e["file"], e["marker"], "reverts" if n == 1 else ("nothing to revert" if n == 0 else "AMBIGUOUS")))
				bad += n > 1
			elif e["marker"] in text:
				print("  %-28s %s: already there" % (e["file"], e["marker"]))
			elif n != 1:
				print("  %-28s %s: OLD CODE FOUND %d TIMES" % (e["file"], e["marker"], n))
				bad += 1
		sys.exit(1 if bad else 0)


if __name__ == "__main__":
	main()
