#!/usr/bin/env python3
"""gen_edits.py [<engine game/src dir>] -- writes edits.json of Druga strona ekwipunku (the "Official Additional
Equipment Page" package on our engine, MT2009_PLUS_ADDEQ_V1, README.md). With a game/src dir (a tree with every patch
of yohara-deploy.sh up to balathor), also checks that every edit's old code is there exactly once (or its marker
already is).

The logic is linux-port/overlays/playerbot/src/game/src/playerbot_addeq.cpp; these are its hooks only. No common/ or
db/ file is changed: the store's cells are named in char.h, the DB keeps them as window INVENTORY."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
M = "MT2009_PLUS_ADDEQ_V1"

E = []


def edit(file, tag, old, new):
	E.append({"file": file, "marker": "%s (%s)" % (M, tag), "old": old, "new": new})


# ---------------------------------------------------------------- char.h
edit("char.h", "cells",
	"// @fixme199 BEGIN\nstruct PlayerSlotT {\n",
	"// " + M + " (cells): Druga strona ekwipunku - the inactive page's store, one cell per wear cell after the belt's\n"
	"// inventory (window INVENTORY, cells 308-339 in the DB); never a packet, never a client's cell (INVENTORY_AND_EQUIP_SLOT_MAX\n"
	"// stays the limit of TItemPos and GetItem) - playerbot_addeq.cpp\n"
	"enum EMt2009Addeq\n{\n"
	"\tMT2009_ADDEQ_SLOT_START = BELT_INVENTORY_SLOT_END,\n"
	"\tMT2009_ADDEQ_SLOT_END = MT2009_ADDEQ_SLOT_START + WEAR_MAX_NUM,\n"
	"};\n\n"
	"// @fixme199 BEGIN\nstruct PlayerSlotT {\n")
edit("char.h", "slots",
	"\tbool bSpecialStorageClient{false};\n",
	"\tbool bSpecialStorageClient{false};\n"
	"\tstd::array<LPITEM,WEAR_MAX_NUM> pAddeqItems{};\t// " + M + " (slots): the inactive equipment page, by wear cell\n")
edit("char.h", "methods",
	"\t\tvoid\t\t\tMt2009SpecialClearItems();\n",
	"\t\tvoid\t\t\tMt2009SpecialClearItems();\n"
	"\t\t// " + M + " (methods): Druga strona ekwipunku, playerbot_addeq.cpp\n"
	"\t\tstatic bool\t\tMt2009AddeqIsCell(WORD wCell) { return wCell >= MT2009_ADDEQ_SLOT_START && wCell < MT2009_ADDEQ_SLOT_END; }\n"
	"\t\tLPITEM\t\t\tMt2009AddeqGetItem(BYTE bWear) const;\n"
	"\t\tvoid\t\t\tMt2009AddeqSetItem(WORD wCell, LPITEM pItem);\n"
	"\t\tvoid\t\t\tMt2009AddeqFlushItems();\n"
	"\t\tvoid\t\t\tMt2009AddeqClearItems();\n"
	"\t\tbool\t\t\tMt2009AddeqSwitch(int iPage);\n")

# ---------------------------------------------------------------- char_item.cpp
edit("char_item.cpp", "set",
	"\tswitch(window_type)\n\t{\n\tcase INVENTORY:\n\tcase EQUIPMENT:\n\t\t{\n"
	"\t\t\tif (wCell >= INVENTORY_AND_EQUIP_SLOT_MAX)\n\t\t\t{\n"
	"\t\t\t\tsys_err(\"CHARACTER::SetItem: invalid item cell %d\", wCell);\n",
	"\t// " + M + " (set): a cell of the inactive equipment page's store - no packet, the client never sees it\n"
	"\tif (window_type == INVENTORY && Mt2009AddeqIsCell(wCell))\n\t{\n"
	"\t\tMt2009AddeqSetItem(wCell, pItem);\n\t\treturn;\n\t}\n\n"
	"\tswitch(window_type)\n\t{\n\tcase INVENTORY:\n\tcase EQUIPMENT:\n\t\t{\n"
	"\t\t\tif (wCell >= INVENTORY_AND_EQUIP_SLOT_MAX)\n\t\t\t{\n"
	"\t\t\t\tsys_err(\"CHARACTER::SetItem: invalid item cell %d\", wCell);\n")
edit("char_item.cpp", "clear",
	"\tMt2009SpecialClearItems(); // MT2009_PLUS_EKWIPUNEK_V1 (clear): the category storages\n",
	"\tMt2009SpecialClearItems(); // MT2009_PLUS_EKWIPUNEK_V1 (clear): the category storages\n"
	"\tMt2009AddeqClearItems(); // " + M + " (clear): the inactive equipment page\n")
edit("char_item.cpp", "use",
	"\tint iLimitRealtimeStartFirstUseFlagIndex = -1;\n",
	"\t// " + M + " (use): Strona ekwipunku II 38306 / 76055 unlocks the second equipment page (playerbot_addeq.cpp)\n"
	"\t{\n"
	"\t\tint Mt2009AddeqUseItem(LPCHARACTER ch, LPITEM item);\n"
	"\t\tconst int iAddeqUse = Mt2009AddeqUseItem(this, item);\n"
	"\t\tif (iAddeqUse >= 0)\n"
	"\t\t\treturn iAddeqUse != 0;\n"
	"\t}\n"
	"\tint iLimitRealtimeStartFirstUseFlagIndex = -1;\n")

# ---------------------------------------------------------------- char.cpp
edit("char.cpp", "flush",
	"\tfor (int i = 0; i < INVENTORY_AND_EQUIP_SLOT_MAX; ++i)\n"
	"\t\tif ((item = GetInventoryItem(i)))\n"
	"\t\t\tITEM_MANAGER::instance().FlushDelayedSave(item);\n}\n",
	"\tfor (int i = 0; i < INVENTORY_AND_EQUIP_SLOT_MAX; ++i)\n"
	"\t\tif ((item = GetInventoryItem(i)))\n"
	"\t\t\tITEM_MANAGER::instance().FlushDelayedSave(item);\n"
	"\tMt2009AddeqFlushItems(); // " + M + " (flush): the inactive equipment page (before a warp)\n}\n")

# ---------------------------------------------------------------- item.cpp
edit("item.cpp", "remove",
	"\t\t\telse\n\t\t\t{\n\t\t\t\tTItemPos cell(INVENTORY, m_wCell);\n",
	"\t\t\t// " + M + " (remove): an item of the inactive equipment page's store leaves the store\n"
	"\t\t\telse if (m_bWindow == INVENTORY && CHARACTER::Mt2009AddeqIsCell(m_wCell))\n"
	"\t\t\t\tpOwner->SetItem(TItemPos(INVENTORY, m_wCell), NULL);\n"
	"\t\t\telse\n\t\t\t{\n\t\t\t\tTItemPos cell(INVENTORY, m_wCell);\n")
edit("item.cpp", "update",
	"\tif (IsChangingAttr())\n\t\treturn;\n\n\tTPacketGCItemUpdate pack;\n",
	"\tif (IsChangingAttr())\n\t\treturn;\n\n"
	"\t// " + M + " (update): the inactive equipment page's store is never sent\n"
	"\tif (GetWindow() == INVENTORY && CHARACTER::Mt2009AddeqIsCell(m_wCell))\n\t\treturn;\n\n"
	"\tTPacketGCItemUpdate pack;\n")

# ---------------------------------------------------------------- char_skill.cpp
edit("char_skill.cpp", "skill",
	"bool CHARACTER::UseSkill(DWORD dwVnum, LPCHARACTER pkVictim, bool bUseGrandMaster)\n{\n",
	"bool CHARACTER::UseSkill(DWORD dwVnum, LPCHARACTER pkVictim, bool bUseGrandMaster)\n{\n"
	"\t// " + M + " (skill): the support skill 200 \"Zmiana strony ekwipunku\" switches the page (playerbot_addeq.cpp)\n"
	"\t{\n"
	"\t\tbool Mt2009AddeqUseSkill(LPCHARACTER ch, DWORD dwVnum, bool& bResult);\n"
	"\t\tbool bAddeqResult = false;\n"
	"\t\tif (Mt2009AddeqUseSkill(this, dwVnum, bAddeqResult))\n"
	"\t\t\treturn bAddeqResult;\n"
	"\t}\n")
edit("char_skill.cpp", "reset",
	"\tvec.emplace_back(SKILL_PRECISION, m_pSkillLevels[SKILL_PRECISION]);\n",
	"\tvec.emplace_back(SKILL_PRECISION, m_pSkillLevels[SKILL_PRECISION]);\n"
	"\t// " + M + " (reset): the second equipment page's switch (200) is kept - the item unlocked it, not points\n"
	"\tvec.emplace_back(200, m_pSkillLevels[200]);\n")

# ---------------------------------------------------------------- cmd.cpp
edit("cmd.cpp", "declare",
	"ACMD(do_switchbot);\t// MT2009_PLUS_SWITCHBOT_V1 (declare): \"/switchbot hello\", root/uiswitchbot.py (playerbot_switchbot.cpp)\n",
	"ACMD(do_switchbot);\t// MT2009_PLUS_SWITCHBOT_V1 (declare): \"/switchbot hello\", root/uiswitchbot.py (playerbot_switchbot.cpp)\n"
	"ACMD(do_addeq);\t// " + M + " (declare): Druga strona ekwipunku, root/uiaddeq.py (playerbot_addeq.cpp)\n")
edit("cmd.cpp", "table",
	"\t{ \"switchbot\",\tdo_switchbot,\t0,\t\t\tPOS_DEAD,\tGM_PLAYER\t},\t// MT2009_PLUS_SWITCHBOT_V1 (table)\n",
	"\t{ \"switchbot\",\tdo_switchbot,\t0,\t\t\tPOS_DEAD,\tGM_PLAYER\t},\t// MT2009_PLUS_SWITCHBOT_V1 (table)\n"
	"\t{ \"addeq\",\tdo_addeq,\t0,\t\t\tPOS_DEAD,\tGM_PLAYER\t},\t// " + M + " (table)\n")


def main():
	out = os.path.join(HERE, "edits.json")
	with open(out, "w", encoding="utf-8", newline="\n") as f:
		json.dump(E, f, indent=1, ensure_ascii=False)
		f.write("\n")
	print("addeq: %d edits -> %s" % (len(E), out))
	if len(sys.argv) > 1:
		src = sys.argv[1]
		bad = 0
		texts = {}
		for e in E:
			if e["file"] not in texts:
				texts[e["file"]] = open(os.path.join(src, e["file"]), "rb").read().decode("latin-1").replace("\r\n", "\n")
			text = texts[e["file"]]
			n = text.count(e["old"])
			if e["marker"] in text:
				print("  %-16s %s: already there" % (e["file"], e["marker"]))
			elif n != 1:
				print("  %-16s %s: OLD CODE FOUND %d TIMES" % (e["file"], e["marker"], n))
				bad += 1
			else:
				texts[e["file"]] = text.replace(e["old"], e["new"])
				print("  %-16s %s: ok" % (e["file"], e["marker"]))
		sys.exit(1 if bad else 0)


if __name__ == "__main__":
	main()
