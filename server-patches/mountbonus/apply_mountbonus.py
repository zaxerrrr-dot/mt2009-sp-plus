#!/usr/bin/env python3
"""apply_mountbonus.py <engine game/src dir> -- Linux/VPS twin of
Apply-MountBonusPatch.ps1 (same replacement, same marker). CMountActor::Mount
(MountSystem.cpp) cleared the old AFFECT_MOUNT_BONUS only through Unmount(),
which does nothing once GetMountVnum() is 0 - so a rider who lost the saddle
by dying or warping kept the seal's bonuses, and every later ride stacked
another set (MALL_EXPBONUS to its cap, "MALL_BONUS exceeded over 100"). The
bonuses are removed before every mount now. Applied once; a file without
the expected code stops with an error, changing nothing. Only the block
changes, in its own line ending."""
import os
import sys

MARK = 'MT2009_PLUS_MOUNT_BONUS_ONCE_V1'
OLD = '\tUnmount();\n\n\tm_pkOwner->AddAffect(AFFECT_MOUNT, POINT_MOUNT, m_dwVnum, AFF_NONE, lDuration, 0, true);\n'
NEW = "\tUnmount();\n\t// MT2009_PLUS_MOUNT_BONUS_ONCE_V1 (server-patches/mountbonus): Unmount() above clears\n\t// the seal's bonuses only while GetMountVnum() is set, and a rider who\n\t// lost the saddle another way (death, a warp) kept them: the next Mount\n\t// added a second set, and the next a third - +30% experience a ride on\n\t// a Snow Tiger until MALL_EXPBONUS hit its cap. Cleared every time.\n\tm_pkOwner->RemoveAffect(AFFECT_MOUNT_BONUS);\n\n\tm_pkOwner->AddAffect(AFFECT_MOUNT, POINT_MOUNT, m_dwVnum, AFF_NONE, lDuration, 0, true);\n"


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    path = os.path.join(sys.argv[1], "MountSystem.cpp")
    text = open(path, "rb").read().decode("latin-1")
    if MARK in text:
        print("mountbonus: already applied")
        return
    for old, new in ((OLD.replace("\n", "\r\n"), NEW.replace("\n", "\r\n")), (OLD, NEW)):
        if text.count(old) == 1:
            text = text.replace(old, new, 1)
            break
    else:
        sys.exit("mountbonus: expected code not found in " + path)
    open(path, "wb").write(text.encode("latin-1"))
    print("mountbonus: applied")


if __name__ == "__main__":
    main()
