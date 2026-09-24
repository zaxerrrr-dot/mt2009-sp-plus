#!/usr/bin/env python3
"""apply_dscommand.py <engine game/src dir> -- Linux/VPS twin of
Apply-DsCommandPatch.ps1 (same replacements, same marker). The client
activates the alchemy deck with "/dragon_soul activate <deck>" (and takes it
off with "/dragon_soul deactivate"); the command was registered for
GM_IMPLEMENTOR, so a player got "Ta komenda nie istnieje". It is a player's
command now; its two testing aids (open the refine / change window anywhere)
stay a GM's. Applied once, each file edited in place (cmd.cpp mixes CRLF and
LF lines, so no line ending is touched); a file without the expected code
stops with an error, changing nothing."""
import os
import re
import sys

MARK = "MT2009_PLUS_DS_PLAYER_CMD_V1"

CMD_RE = re.compile(r'(\{ "dragon_soul",[^\r\n]*?)GM_IMPLEMENTOR \},')
CMD_NEW = r'\1GM_PLAYER }, // ' + MARK + ': the client activates the deck with it'

GUARD = "\t\t\tif (ch->GetGMLevel() < GM_IMPLEMENTOR) // " + MARK + ": a GM's testing aid\n\t\t\t\tbreak;\n"
GM_OLD = [
    "\t\t\t// reach NPC 20001 (operator's explicit request, 17 September 2026).\n"
    "\t\t\tch->DragonSoul_RefineWindow_Open(NULL);\n",
    "\tcase 'c':\n\t\t{\n\t\t\tch->DragonSoul_RefineWindow_ChangeAttr_Open(NULL);\n",
]
GM_NEW = [
    "\t\t\t// reach NPC 20001 (operator's explicit request, 17 September 2026).\n"
    + GUARD + "\t\t\tch->DragonSoul_RefineWindow_Open(NULL);\n",
    "\tcase 'c':\n\t\t{\n" + GUARD + "\t\t\tch->DragonSoul_RefineWindow_ChangeAttr_Open(NULL);\n",
]


def crlf(text, s):
    return s.replace("\n", "\r\n") if "\r\n" in text else s


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    cmd_path = os.path.join(sys.argv[1], "cmd.cpp")
    gm_path = os.path.join(sys.argv[1], "cmd_gm.cpp")
    cmd = open(cmd_path, "rb").read().decode("latin-1")
    gm = open(gm_path, "rb").read().decode("latin-1")
    if MARK in cmd and MARK in gm:
        print("dscommand: already applied")
        return
    if MARK not in cmd and len(CMD_RE.findall(cmd)) != 1:
        sys.exit("dscommand: expected code not found in " + cmd_path)
    if MARK not in gm:
        for old in GM_OLD:
            if gm.count(crlf(gm, old)) != 1:
                sys.exit("dscommand: expected code not found in " + gm_path)
    if MARK not in cmd:
        cmd = CMD_RE.sub(CMD_NEW, cmd, count=1)
        open(cmd_path, "wb").write(cmd.encode("latin-1"))
    if MARK not in gm:
        for old, new in zip(GM_OLD, GM_NEW):
            gm = gm.replace(crlf(gm, old), crlf(gm, new), 1)
        open(gm_path, "wb").write(gm.encode("latin-1"))
    print("dscommand: applied")


if __name__ == "__main__":
    main()
