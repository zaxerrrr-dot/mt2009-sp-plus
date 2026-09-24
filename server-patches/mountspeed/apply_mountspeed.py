#!/usr/bin/env python3
"""apply_mountspeed.py <engine game/src dir> -- Linux/VPS twin of
Apply-MountSpeedPatch.ps1 (same replacement, same marker). The movement
check (CCharacterPlayerData::GetAllowedMovementDistance, char_player.cpp)
allows a rider one fixed distance, calibrated for a combat horse's run
(vnum 20104, 740.67). Magma Manni (53201-53203) was given its own motion's
share of it, which ended its rubber-banding; every other costume mount
still ran on the combat horse's ceiling, and 98 of the 246 run faster (up
to 1159: Manni/Manu, Cerber 959) and were pulled back. The same correction
now covers every costume mount (a mount race worn in WEAR_COSTUME_MOUNT),
and only ever widens the ceiling - a mount slower than the combat horse
keeps the ceiling it had. Applied once; a file without the expected code
stops with an error, changing nothing. CRLF/LF is kept."""
import os
import sys

MARK = "MT2009_PLUS_MOUNT_SPEED_V1"

OLD = ("\t\tif (mountVnum == 53201 || mountVnum == 53202 || mountVnum == 53203)\n"
       "\t\t{\n"
       "\t\t\tconstexpr float kCombatHorseMotionSpeed = 740.67f;\n"
       "\t\t\tconst float mountMotionMultiplier = ch->GetMoveMotionSpeed() / kCombatHorseMotionSpeed;\n"
       "\n"
       "\t\t\tbaseDistance = static_cast<DWORD>(baseDistance * mountMotionMultiplier);\n"
       "\t\t}\n")
NEW = ("\t\t// " + MARK + " (server-patches/mountspeed): every costume mount,\n"
       "\t\t// not Magma Manni alone - 98 of the 246 run faster than the combat\n"
       "\t\t// horse the ceiling is set for, and each was pulled back like Manni\n"
       "\t\t// was. Widened only: a slower mount keeps the ceiling it had.\n"
       "\t\tif (mountVnum != 0 && ch->GetWear(WEAR_COSTUME_MOUNT))\n"
       "\t\t{\n"
       "\t\t\tconstexpr float kCombatHorseMotionSpeed = 740.67f;\n"
       "\t\t\tconst float mountMotionMultiplier = ch->GetMoveMotionSpeed() / kCombatHorseMotionSpeed;\n"
       "\n"
       "\t\t\tif (mountMotionMultiplier > 1.0f)\n"
       "\t\t\t\tbaseDistance = static_cast<DWORD>(baseDistance * mountMotionMultiplier);\n"
       "\t\t}\n")


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    path = os.path.join(sys.argv[1], "char_player.cpp")
    raw = open(path, "rb").read().decode("latin-1")
    crlf = "\r\n" in raw
    text = raw.replace("\r\n", "\n")
    if MARK in text:
        print("mountspeed: already applied")
        return
    if text.count(OLD) != 1:
        sys.exit("mountspeed: expected code not found in " + path)
    text = text.replace(OLD, NEW, 1)
    if crlf:
        text = text.replace("\n", "\r\n")
    open(path, "wb").write(text.encode("latin-1"))
    print("mountspeed: applied")


if __name__ == "__main__":
    main()
