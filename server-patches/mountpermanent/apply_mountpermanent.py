#!/usr/bin/env python3
"""apply_mountpermanent.py <engine game/src dir> -- Linux/VPS twin of
Apply-MountPermanentPatch.ps1 (same replacement, same marker). A mount seal
without a real-time limit in its proto (the blue and the war mounts,
71115-71128) never gets an expiry in socket0, and MountItem_GetRemainingSeconds
(MountSystem.cpp) took socket0 == 0 for "expired": "Ta pieczec wierzchowca juz
wygasla" on a new seal. Such a seal rides with no end now. Applied once; a
file without the expected code stops with an error, changing nothing. Only
the block changes, in its own line ending."""
import os
import sys

MARK = 'MT2009_PLUS_MOUNT_PERMANENT_V1'
OLD = '\tDWORD dwExpireAt = mountItem->GetSocket(0);\n\tDWORD dwNow = (DWORD)time(0);\n'
NEW = '\t// MT2009_PLUS_MOUNT_PERMANENT_V1 (server-patches/mountpermanent): a seal whose\n\t// proto has no real-time limit (the blue and the war mounts, 71115-71128)\n\t// never gets an expiry in socket0. It is a permanent seal, not an expired\n\t// one: "Ta pieczec wierzchowca juz wygasla" on a brand new Dzik Wojenny.\n\tbool bTimedSeal = false;\n\tfor (int i = 0; i < ITEM_LIMIT_MAX_NUM; ++i)\n\t{\n\t\tBYTE bLimit = mountItem->GetProto()->aLimits[i].bType;\n\t\tif (LIMIT_REAL_TIME == bLimit || LIMIT_REAL_TIME_START_FIRST_USE == bLimit)\n\t\t\tbTimedSeal = true;\n\t}\n\tif (!bTimedSeal)\n\t{\n\t\t*pDurationOut = INFINITE_AFFECT_DURATION;\n\t\treturn true;\n\t}\n\n\tDWORD dwExpireAt = mountItem->GetSocket(0);\n\tDWORD dwNow = (DWORD)time(0);\n'


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    path = os.path.join(sys.argv[1], "MountSystem.cpp")
    text = open(path, "rb").read().decode("latin-1")
    if MARK in text:
        print("mountpermanent: already applied")
        return
    for old, new in ((OLD.replace("\n", "\r\n"), NEW.replace("\n", "\r\n")), (OLD, NEW)):
        if text.count(old) == 1:
            text = text.replace(old, new, 1)
            break
    else:
        sys.exit("mountpermanent: expected code not found in " + path)
    open(path, "wb").write(text.encode("latin-1"))
    print("mountpermanent: applied")


if __name__ == "__main__":
    main()
