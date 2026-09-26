#!/usr/bin/env python3
"""apply_mountdeath.py <engine game/src dir> -- Linux/VPS twin of
Apply-MountDeathPatch.ps1 (same replacement, same marker). A player who died
riding a mount seal (WEAR_COSTUME_MOUNT) got off it, but the seal stayed in
its slot and could not be ridden again until it was taken off and put back
on. Now CHARACTER::Dead (char_battle.cpp) takes the seal off into the bag of
every player, bots too (a bot puts it back on from the bag); with a full
bag it stays where it is.
Applied once; a file without the expected code stops with an error."""
import os
import sys

MARK = 'MT2009_PLUS_MOUNT_DEATH_UNEQUIP_V1'
OLD = '\t\t\tUpdatePacket();\n\t\t}\n\n\t}\n#endif\n\n\tif (!pkKiller && m_dwKillerPID)\n'
NEW = ('\t\t\tUpdatePacket();\n\t\t}\n\n\t}\n#endif\n\n'
       '\t// MT2009_PLUS_MOUNT_DEATH_UNEQUIP_V1 (server-patches/mountdeath): a player\'s\n'
       '\t// mount seal comes off into the bag at death - left in its slot it could\n'
       '\t// not be ridden again until taken off and put back on. A full bag keeps\n'
       '\t// it where it is. A bot puts it back on from the bag (WearPlayerBotBoughtLook).\n'
       '\tif (IsPC())\n'
       '\t{\n'
       '\t\t// Moved as UnequipItem moves it, without CanUnequipNow: the killing\n'
       '\t\t// blow stuns first (Stun), and a stunned character may unequip nothing.\n'
       '\t\tLPITEM mountSeal = GetWear(WEAR_COSTUME_MOUNT);\n'
       '\t\tconst int sealCell = mountSeal ? GetEmptyInventoryEx(mountSeal) : -1;\n'
       '\t\tif (mountSeal && sealCell >= 0)\n'
       '\t\t{\n'
       '\t\t\tmountSeal->RemoveFromCharacter();\n'
       '\t\t\tmountSeal->AddToCharacter(this, TItemPos(mountSeal->GetWindowInventoryEx(), sealCell));\n'
       '\t\t}\n'
       '\t}\n\n'
       '\tif (!pkKiller && m_dwKillerPID)\n')


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    path = os.path.join(sys.argv[1], "char_battle.cpp")
    text = open(path, "rb").read().decode("latin-1")
    if MARK in text:
        print("mountdeath: already applied")
        return
    old, new = OLD, NEW
    if "\r\n" in text:
        old, new = old.replace("\n", "\r\n"), new.replace("\n", "\r\n")
    if text.count(old) != 1:
        sys.exit("mountdeath: expected code not found in " + path)
    open(path, "wb").write(text.replace(old, new, 1).encode("latin-1"))
    print("mountdeath: applied")


if __name__ == "__main__":
    main()
