#!/usr/bin/env python3
"""apply_stonestill.py <engine game/src dir> -- Linux/VPS twin of
Apply-StoneStillPatch.ps1 (same replacements, same marker). A Metin stone
that was sent walking (CHARACTER::Goto, char.cpp) went into the move state
and from it into the battle state it has no AI for: "Stone must not use
battle state" hundreds of times a minute. Goto refuses a stone (and says
once who it was fighting and who synced it), and a stone in the battle state
goes back to idle (StateBattle, char_state.cpp).
Applied once; a file without the expected code stops with an error."""
import os
import sys

MARK = 'MT2009_PLUS_STONE_STILL_V1'
EDITS = [
    ("char.cpp", 'bool CHARACTER::Goto(long x, long y)\n{\n\tif (GetX() == x && GetY() == y)\n\t\treturn false;\n',
     'bool CHARACTER::Goto(long x, long y)\n{\n\t// MT2009_PLUS_STONE_STILL_V1 (server-patches/stonestill): a Metin stone\n\t// never walks. One that was sent here went into the move state and from\n\t// it into the battle state it has no AI for ("Stone must not use battle\n\t// state", hundreds a minute). Refused, and said once a stone with who it\n\t// was fighting and who synced it, to find the caller.\n\tif (IsStone())\n\t{\n\t\tstatic DWORD s_dwStoneGotoLogged = 0;\n\t\tif (s_dwStoneGotoLogged != GetVID())\n\t\t{\n\t\t\ts_dwStoneGotoLogged = GetVID();\n\t\t\tsys_err("stone goto refused (name %s vnum %u map %ld pos %ld,%ld to %ld,%ld victim %s sync_owner %s)",\n\t\t\t\t\tGetName(), GetRaceNum(), GetMapIndex(), GetX(), GetY(), x, y,\n\t\t\t\t\tGetVictim() ? GetVictim()->GetName() : "-", m_pkChrSyncOwner ? m_pkChrSyncOwner->GetName() : "-");\n\t\t}\n\t\treturn false;\n\t}\n\n\tif (GetX() == x && GetY() == y)\n\t\treturn false;\n'),
    ("char_state.cpp", '\tif (IsStone())\n\t{\n\t\tsys_err("Stone must not use battle state (name %s)", GetName());\n\t\treturn;\n\t}\n',
     '\tif (IsStone())\n\t{\n\t\t// MT2009_PLUS_STONE_STILL_V1: back to the stone\'s own idle state, once,\n\t\t// instead of this line every pass for as long as the stone stood.\n\t\tsys_err("Stone must not use battle state (name %s), back to idle", GetName());\n\t\tGotoState(m_stateIdle);\n\t\tm_dwStateDuration = 1;\n\t\treturn;\n\t}\n'),
]


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    for name, old, new in EDITS:
        path = os.path.join(sys.argv[1], name)
        text = open(path, "rb").read().decode("latin-1")
        if MARK in text:
            print("stonestill: %s already applied" % name)
            continue
        if "\r\n" in text:
            old, new = old.replace("\n", "\r\n"), new.replace("\n", "\r\n")
        if text.count(old) != 1:
            sys.exit("stonestill: expected code not found in " + path)
        open(path, "wb").write(text.replace(old, new, 1).encode("latin-1"))
        print("stonestill: %s applied" % name)


if __name__ == "__main__":
    main()
