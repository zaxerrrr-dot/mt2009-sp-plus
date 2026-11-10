#!/usr/bin/env python3
"""apply_mountdeath.py <engine game/src dir> -- Linux/VPS twin of
Apply-MountDeathPatch.ps1 (same replacements, same markers).

MT2009_PLUS_MOUNT_DEATH_KEEP_SEAL_V2 (players, 10 November 2026: "podczas
smierci pieczec wierzchowca wychodzi ze slotu i automatycznie traci sie bonus
zestawu ... trzeba wlozyc pieczec ponownie"): death only takes the rider off
the seal's mount. The seal stays in WEAR_COSTUME_MOUNT, so the costume set
that counts it keeps its bonus, and after the revive the mount stands beside
its rider again (Ctrl+G rides it, as after any getting off).

  char_battle.cpp  CHARACTER::Dead - the seal branch of the stop-riding block
                   drops AFFECT_MOUNT with AFFECT_MOUNT_BONUS (as CMountActor::
                   Unmount does) and no longer calls UnEquipSpecialRideUniqueItem
                   for the seal (that took it off whenever the dying character
                   was not stunned); an old unique ride item (UNIQUE1/2) still
                   comes off as before. V1 (MT2009_PLUS_MOUNT_DEATH_UNEQUIP_V1,
                   the seal moved into the bag at death - from before
                   mountquickswap made Ctrl+G call a missing mount first) is
                   taken out of an already patched file.
  char.cpp         CHARACTER::ReviveInvisible (every revive: here, in town, the
                   lairs) - a player back on his feet with a worn seal and no
                   mount out calls it (CheckMount, as the login does; not on
                   the OX map or an arena, not while riding).

Applied once; a file without the expected code stops with an error and
nothing is written."""
import os
import sys

MARK = 'MT2009_PLUS_MOUNT_DEATH_KEEP_SEAL_V2'
MARK_V1 = 'MT2009_PLUS_MOUNT_DEATH_UNEQUIP_V1'

# ---- V1 (taken out) ---------------------------------------------------------
V1_OLD = '\t\t\tUpdatePacket();\n\t\t}\n\n\t}\n#endif\n\n\tif (!pkKiller && m_dwKillerPID)\n'
V1_NEW = ('\t\t\tUpdatePacket();\n\t\t}\n\n\t}\n#endif\n\n'
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

# ---- V2: char_battle.cpp, CHARACTER::Dead -----------------------------------
DEAD_OLD = ('\t\telse if (GetMountVnum())\n'
            '\t\t{\n'
            '\t\t\tRemoveAffect(AFFECT_MOUNT_BONUS);\n'
            '\t\t\tm_dwMountVnum = 0;\n'
            '\t\t\tUnEquipSpecialRideUniqueItem();\n'
            '\n'
            '\t\t\tUpdatePacket();\n'
            '\t\t}\n')
DEAD_NEW = ('\t\telse if (GetMountVnum())\n'
            '\t\t{\n'
            '\t\t\t// MT2009_PLUS_MOUNT_DEATH_KEEP_SEAL_V2 (server-patches/mountdeath): death only\n'
            '\t\t\t// takes the rider off. The mount seal stays worn - taken off, it took the\n'
            '\t\t\t// costume set bonus with it - and after the revive its mount is called\n'
            '\t\t\t// again (ReviveInvisible -> CheckMount); Ctrl+G rides it. AFFECT_MOUNT goes\n'
            '\t\t\t// with the bonus, as in CMountActor::Unmount. An old unique ride item\n'
            '\t\t\t// (UNIQUE1/2) still comes off as before.\n'
            '\t\t\tRemoveAffect(AFFECT_MOUNT);\n'
            '\t\t\tRemoveAffect(AFFECT_MOUNT_BONUS);\n'
            '\t\t\tm_dwMountVnum = 0;\n'
            '\t\t\tLPITEM rideUnique1 = GetWear(WEAR_UNIQUE1);\n'
            '\t\t\tLPITEM rideUnique2 = GetWear(WEAR_UNIQUE2);\n'
            '\t\t\tif ((rideUnique1 && rideUnique1->GetSpecialGroup() == UNIQUE_GROUP_SPECIAL_RIDE) ||\n'
            '\t\t\t\t(rideUnique2 && rideUnique2->GetSpecialGroup() == UNIQUE_GROUP_SPECIAL_RIDE))\n'
            '\t\t\t\tUnEquipSpecialRideUniqueItem();\n'
            '\n'
            '\t\t\tUpdatePacket();\n'
            '\t\t}\n')

# ---- V2: char.cpp, CHARACTER::ReviveInvisible -------------------------------
REVIVE_OLD = ('void CHARACTER::ReviveInvisible(int iDur)\n'
              '{\n'
              '\tAddAffect(AFFECT_REVIVE_INVISIBLE, POINT_NONE, 0, AFF_REVIVE_INVISIBLE, iDur, 0, true);\n'
              '}\n')
REVIVE_NEW = ('void CHARACTER::ReviveInvisible(int iDur)\n'
              '{\n'
              '\tAddAffect(AFFECT_REVIVE_INVISIBLE, POINT_NONE, 0, AFF_REVIVE_INVISIBLE, iDur, 0, true);\n'
              '#ifdef ENABLE_MOUNT_COSTUME_SYSTEM\n'
              '\t// MT2009_PLUS_MOUNT_DEATH_KEEP_SEAL_V2 (revive), server-patches/mountdeath: the seal\n'
              '\t// stayed worn through the death, its mount went away with the dying rider\n'
              '\t// (CMountActor::Update) - it comes out again as at the login (input_login.cpp,\n'
              '\t// CheckMount: only when none is out). Not at the login itself (its phase is\n'
              '\t// not PHASE_GAME yet, the login calls CheckMount later), not before a warp\n'
              '\t// (the town restart: the next login calls it), not while riding, not on the\n'
              '\t// OX map (113) or an arena - the login\'s own rules.\n'
              '\tif (IsPC() && !IsDead() && !GetMountVnum() && !IsHorseRiding() && GetWear(WEAR_COSTUME_MOUNT) &&\n'
              '\t\tGetDesc() && GetDesc()->IsPhase(PHASE_GAME) && !IsWarping() && GetMapIndex() != 113 &&\n'
              '\t\t!CArenaManager::instance().IsArenaMap(GetMapIndex()))\n'
              '\t\tCheckMount();\n'
              '#endif\n'
              '}\n')


def read(path):
    return open(path, "rb").read().decode("latin-1")


def crlf(text, s):
    return s.replace("\n", "\r\n") if "\r\n" in text else s


def replace_once(text, old, new, what):
    old, new = crlf(text, old), crlf(text, new)
    if text.count(old) != 1:
        sys.exit("mountdeath: expected code not found (%s)" % what)
    return text.replace(old, new, 1)


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    battle = os.path.join(sys.argv[1], "char_battle.cpp")
    char = os.path.join(sys.argv[1], "char.cpp")
    tb, tc = read(battle), read(char)
    if MARK in tb and MARK in tc:
        print("mountdeath: already applied")
        return
    nb, nc = tb, tc
    if MARK not in nb:
        if MARK_V1 in nb:
            nb = replace_once(nb, V1_NEW, V1_OLD, "V1 block, char_battle.cpp")
        nb = replace_once(nb, DEAD_OLD, DEAD_NEW, "CHARACTER::Dead, char_battle.cpp")
    if MARK not in nc:
        nc = replace_once(nc, REVIVE_OLD, REVIVE_NEW, "CHARACTER::ReviveInvisible, char.cpp")
    # both checked before anything is written
    if nb != tb:
        open(battle, "wb").write(nb.encode("latin-1"))
    if nc != tc:
        open(char, "wb").write(nc.encode("latin-1"))
    print("mountdeath: applied (V2)")


if __name__ == "__main__":
    main()
