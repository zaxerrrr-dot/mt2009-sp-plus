#!/usr/bin/env python3
"""apply_mobattack.py <engine game/src dir> -- MT2009_PLUS_MOB_ATTACK_V1.

How hard monsters hit, a percent of the damage they deal (the owner,
3 November 2026, from the server configurator's EASY / SAPPHIRE profiles:
"obrazenia od potworow 80%"): the event flag m2_mob_attack, 10..300, 100 or 0
the game as it was made - the twin of server-patches/mobhp's m2_mob_hp.
CHARACTER::Damage scales the damage once, at its very start, whenever the one
who deals it is a monster (not a pet, not a Metin stone, never a player or a
bot): skills, ordinary hits, arrows and poison alike, players, bots and
anything else a monster hits. The players' and the bots' own damage is never
touched. The flag is live on every core (CQuestManager::SetEventFlag): the
migrator writes it from .env's M2_MONSTER_ATTACK when that changed
(apply.sh), the advanced panel's "Konfiguracja serwera" and the web_admin
queue's MOB_ATTACK switch it at once.

Applied once; a file without the expected code stops with an error, changing
nothing. Anchors the mobhp patch's flag hook in questmanager.cpp, so it
goes after server-patches/mobhp (already part of the engine tree).

MT2009_PLUS_PC_ATTACK_V1 (the owner, 3 November 2026, the EMERALD server
configuration: "+10% obrazen zadawanych przez gracza"): the other way round,
the event flag m2_pc_attack, 10..300, 100 or 0 the game as it was made - a
percent of the damage a player (and a bot, who plays like one) deals to
monsters, bosses and Metin stones. Scaled once in CHARACTER::Damage right
after the monsters' scale, whenever the one who deals it is a player
character and the one hit a monster or a Metin stone: the wiki's server buff names no PvP, so
the damage between players never changes. Live on every core the same way:
the migrator writes it from .env's M2_PLAYER_ATTACK when that changed, the
advanced panel and the web_admin queue's PC_ATTACK switch it at once."""
import os
import sys

MARK = "MT2009_PLUS_MOB_ATTACK_V1"
PC_MARK = "MT2009_PLUS_PC_ATTACK_V1"
HELPERS = (
    "// " + MARK + " (server-patches/mobattack): how hard monsters hit, a percent\n"
    "// of their damage - the event flag m2_mob_attack (10..300; 0 or 100 = the game\n"
    "// as it was made). Set on every core by CQuestManager::SetEventFlag.\n"
    "static int s_iM2MobAttackPercent = 100;\n"
    "\n"
    "void M2ApplyMobAttackPercent(int value)\n"
    "{\n"
    "\tconst int pct = value <= 0 ? 100 : (value < 10 ? 10 : (value > 300 ? 300 : value));\n"
    "\tif (pct != s_iM2MobAttackPercent)\n"
    "\t\tsys_log(0, \"MOB_ATTACK: %d%% -> %d%% of the damage monsters deal\", s_iM2MobAttackPercent, pct);\n"
    "\ts_iM2MobAttackPercent = pct;\n"
    "}\n"
    "\n"
)
DAMAGE_HEAD = ("bool CHARACTER::Damage(LPCHARACTER pAttacker, int dam, EDamageType type, DWORD dwUsedSkill, "
               "bool IsPenetrate) // returns true if dead\n{\n")
MOB_SCALE = (
    "\t// " + MARK + " (scale): a monster's hit, once, before anything else reads it.\n"
    "\tif (s_iM2MobAttackPercent != 100 && dam > 0 && pAttacker && pAttacker != this\n"
    "\t\t&& pAttacker->IsMonster() && !pAttacker->IsPet() && !pAttacker->IsPC())\n"
    "\t{\n"
    "\t\tlong long scaled = (long long)dam * s_iM2MobAttackPercent / 100;\n"
    "\t\tif (scaled < 1)\n"
    "\t\t\tscaled = 1;\n"
    "\t\tif (scaled > 2147483647LL)\n"
    "\t\t\tscaled = 2147483647LL;\n"
    "\t\tdam = (int)scaled;\n"
    "\t}\n\n")
MOB_HELPER_END = "\ts_iM2MobAttackPercent = pct;\n}\n\n"
EDITS = [
    ("char_battle.cpp",
     DAMAGE_HEAD,
     HELPERS + DAMAGE_HEAD + MOB_SCALE),
    ("questmanager.cpp",
     "extern void M2ApplyMobHpPercent(int value);\n",
     "extern void M2ApplyMobHpPercent(int value);\n"
     "// " + MARK + " (declare): char_battle.cpp, server-patches/mobattack.\n"
     "extern void M2ApplyMobAttackPercent(int value);\n"),
    ("questmanager.cpp",
     "\t\tif (name == \"m2_mob_hp\")\n\t\t\t::M2ApplyMobHpPercent(value);\n",
     "\t\tif (name == \"m2_mob_hp\")\n\t\t\t::M2ApplyMobHpPercent(value);\n"
     "\t\t// " + MARK + " (flag): how hard monsters hit, live on every core.\n"
     "\t\tif (name == \"m2_mob_attack\")\n"
     "\t\t\t::M2ApplyMobAttackPercent(value);\n"),
    # MT2009_PLUS_PC_ATTACK_V1: the players' damage to monsters, after the monsters' own.
    ("char_battle.cpp",
     MOB_HELPER_END,
     MOB_HELPER_END +
     "// " + PC_MARK + " (server-patches/mobattack): how hard players hit monsters,\n"
     "// bosses and Metin stones, a percent of their damage - the event flag\n"
     "// m2_pc_attack (10..300; 0 or 100 = the game as it was made). Never PvP.\n"
     "static int s_iM2PcAttackPercent = 100;\n"
     "\n"
     "void M2ApplyPcAttackPercent(int value)\n"
     "{\n"
     "\tconst int pct = value <= 0 ? 100 : (value < 10 ? 10 : (value > 300 ? 300 : value));\n"
     "\tif (pct != s_iM2PcAttackPercent)\n"
     "\t\tsys_log(0, \"PC_ATTACK: %d%% -> %d%% of the damage players deal to monsters\", s_iM2PcAttackPercent, pct);\n"
     "\ts_iM2PcAttackPercent = pct;\n"
     "}\n"
     "\n"),
    ("char_battle.cpp",
     MOB_SCALE,
     MOB_SCALE +
     "\t// " + PC_MARK + " (scale): a player's (or a bot's) hit on a monster, a boss or a Metin, once.\n"
     "\tif (s_iM2PcAttackPercent != 100 && dam > 0 && pAttacker && pAttacker != this\n"
     "\t\t&& pAttacker->IsPC() && !IsPC() && (IsMonster() || IsStone()))\n"
     "\t{\n"
     "\t\tlong long scaled = (long long)dam * s_iM2PcAttackPercent / 100;\n"
     "\t\tif (scaled < 1)\n"
     "\t\t\tscaled = 1;\n"
     "\t\tif (scaled > 2147483647LL)\n"
     "\t\t\tscaled = 2147483647LL;\n"
     "\t\tdam = (int)scaled;\n"
     "\t}\n\n"),
    ("questmanager.cpp",
     "extern void M2ApplyMobAttackPercent(int value);\n",
     "extern void M2ApplyMobAttackPercent(int value);\n"
     "// " + PC_MARK + " (declare): char_battle.cpp, server-patches/mobattack.\n"
     "extern void M2ApplyPcAttackPercent(int value);\n"),
    ("questmanager.cpp",
     "\t\tif (name == \"m2_mob_attack\")\n\t\t\t::M2ApplyMobAttackPercent(value);\n",
     "\t\tif (name == \"m2_mob_attack\")\n\t\t\t::M2ApplyMobAttackPercent(value);\n"
     "\t\t// " + PC_MARK + " (flag): how hard players hit monsters, live on every core.\n"
     "\t\tif (name == \"m2_pc_attack\")\n"
     "\t\t\t::M2ApplyPcAttackPercent(value);\n"),
]


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    files = {}
    for name, old, new in EDITS:
        path = os.path.join(sys.argv[1], name)
        if path not in files:
            files[path] = open(path, "rb").read().decode("latin-1")
    for name, old, new in EDITS:
        path = os.path.join(sys.argv[1], name)
        text = files[path]
        # The edit's own marked lines (an anchor may carry an earlier edit's).
        marked = [l for l in new.split("\n") if (MARK in l or PC_MARK in l) and l not in old.split("\n")]
        if marked and marked[0] in text.replace("\r\n", "\n"):
            continue
        crlf = "\r\n" in text
        o, n = (old.replace("\n", "\r\n"), new.replace("\n", "\r\n")) if crlf else (old, new)
        if text.count(o) != 1:
            sys.exit("mobattack: expected code not found in " + path + " -- nothing changed")
        files[path] = text.replace(o, n, 1)
    for path, text in files.items():
        before = open(path, "rb").read().decode("latin-1")
        if text != before:
            open(path, "wb").write(text.encode("latin-1"))
            print("mobattack: %s applied" % os.path.basename(path))
        else:
            print("mobattack: %s already applied" % os.path.basename(path))


if __name__ == "__main__":
    main()
