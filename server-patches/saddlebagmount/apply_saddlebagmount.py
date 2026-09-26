#!/usr/bin/env python3
"""apply_saddlebagmount.py <engine game/src dir> -- Linux/VPS twin of
Apply-SaddlebagMountPatch.ps1 (same replacement, same marker). The horse
saddlebags (the fifth bag page, CHARACTER::CanUseHorseInventory in char.cpp)
opened only with the horse out or ridden; now riding a mount seal opens them
too. Owning a horse (horse level 1 or more) is still the condition.
Applied once; a file without the expected code stops with an error."""
import os
import sys

MARK = 'MT2009_PLUS_SADDLEBAG_MOUNT_V1'
OLD = '\treturn GetHorseLevel() > 0 && (GetHorse() || IsHorseRiding());\n'
NEW = ('\t// MT2009_PLUS_SADDLEBAG_MOUNT_V1 (server-patches/saddlebagmount): the\n'
       '\t// saddlebags open on a mount seal too (IsRiding: the horse or a mount).\n'
       '\treturn GetHorseLevel() > 0 && (GetHorse() || IsRiding());\n')


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    path = os.path.join(sys.argv[1], "char.cpp")
    text = open(path, "rb").read().decode("latin-1")
    if MARK in text:
        print("saddlebagmount: already applied")
        return
    old, new = OLD, NEW
    if "\r\n" in text:
        old, new = old.replace("\n", "\r\n"), new.replace("\n", "\r\n")
    if text.count(old) != 1:
        sys.exit("saddlebagmount: expected code not found in " + path)
    open(path, "wb").write(text.replace(old, new, 1).encode("latin-1"))
    print("saddlebagmount: applied")


if __name__ == "__main__":
    main()
