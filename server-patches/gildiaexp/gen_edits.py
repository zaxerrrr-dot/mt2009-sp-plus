#!/usr/bin/env python3
"""gen_edits.py -- writes edits.json of server-patches/gildiaexp (README.md): MT2009_PLUS_GUILD_OFFER_CHAMPION_V1
(guild.cpp CGuild::OfferExp, input_main.cpp GUILD_SUBHEADER_CG_OFFER): a character with a Champion Level (>= 1) may
not offer experience to the guild (the owner, 6 November 2026, after the wiki). Anchors: the engine after czempion
and pdbonus (the deploy list puts gildiaexp just before logtrim)."""
import json
import os

E = []

MSG = "[Gildia] Na Poziomie Czempiona nie mozna oddawac doswiadczenia gildii."


def edit(file, marker, old, new):
    E.append({"file": file, "marker": marker, "old": old, "new": new})


# ---------------------------------------------------------------- guild.cpp
edit("guild.cpp", "MT2009_PLUS_GUILD_OFFER_CHAMPION_V1 (refuse)",
     '\tif (ch->FindAffect(AFFECT_EXP_BLOCK))\n\t\treturn false;\n\n'
     '\tif (ch->GetExp() < (DWORD) amount)\n',
     '\tif (ch->FindAffect(AFFECT_EXP_BLOCK))\n\t\treturn false;\n\n'
     '\t// MT2009_PLUS_GUILD_OFFER_CHAMPION_V1 (refuse): no offering at a Champion Level (the owner, 6 November 2026,\n'
     '\t// as the wiki has it). A Champion\'s bar is the champion one (POINT_CONQUEROR_EXP); the ordinary bar of\n'
     '\t// level 120 is hidden and refills to next_exp - 1 from every kill, so offering it gave the guild free\n'
     '\t// experience (vps3, 6 November: 1 132 221 700 in 33 s, nothing gone from the visible bar). A bot is refused\n'
     '\t// without a line (playerbot_guild.h does not ask).\n'
     '\tif (ch->GetConquerorLevel() >= 1)\n'
     '\t{\n'
     '\t\tif (ch->GetDesc() && !ch->GetDesc()->IsBot())\n'
     '\t\t\tch->ChatPacket(CHAT_TYPE_INFO, "' + MSG + '");\n'
     '\t\treturn false;\n'
     '\t}\n\n'
     '\tif (ch->GetExp() < (DWORD) amount)\n')

# ---------------------------------------------------------------- input_main.cpp
edit("input_main.cpp", "MT2009_PLUS_GUILD_OFFER_CHAMPION_V1 (no second line)",
     '\t\t\t\t\telse\n\t\t\t\t\t{\n'
     '\t\t\t\t\t\tch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("[Guild] Experience usage has failed."));\n',
     '\t\t\t\t\telse if (ch->GetConquerorLevel() < 1) // MT2009_PLUS_GUILD_OFFER_CHAMPION_V1 (no second line): OfferExp said why\n'
     '\t\t\t\t\t{\n'
     '\t\t\t\t\t\tch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("[Guild] Experience usage has failed."));\n')

json.dump(E, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "edits.json"), "w"), indent=2)
print("gildiaexp: %d edit(s) written" % len(E))
