#!/usr/bin/env python3
"""apply_petstaysondeath.py <engine game/src dir> -- Linux/VPS twin of
Apply-PetStaysOnDeathPatch.ps1 (same edit, same marker). CPetActor::Update
unsummoned the pet the moment its owner died; now the pet waits by the body
and follows again once the owner stands up ("po zginieciu pet jest
odwolywany, ma zostawac", 27 September). Applied once; a file without the
expected code stops with an error, changing nothing."""
import os
import sys

MARK = "MT2009_PLUS_PET_STAYS_ON_DEATH_V1"
OLD = '\tif (m_pkOwner->IsDead() || (IsSummoned() && m_pkChar->IsDead())\n\t\t|| NULL == ITEM_MANAGER::instance().FindByVID(this->GetSummonItemVID())\n\t\t|| ITEM_MANAGER::instance().FindByVID(this->GetSummonItemVID())->GetOwner() != this->GetOwner()\n\t\t)\n\t{\n\t\tthis->Unsummon();\n\t\treturn true;\n\t}\n'
NEW = '\t// MT2009_PLUS_PET_STAYS_ON_DEATH_V1 (server-patches/petstaysondeath): the\n\t// owner\'s death no longer sends the pet away - it waits by the body and\n\t// follows again once the owner is back on its feet ("po zginieciu pet jest\n\t// odwolywany, ma zostawac", 27 September).\n\tif ((IsSummoned() && m_pkChar->IsDead())\n\t\t|| NULL == ITEM_MANAGER::instance().FindByVID(this->GetSummonItemVID())\n\t\t|| ITEM_MANAGER::instance().FindByVID(this->GetSummonItemVID())->GetOwner() != this->GetOwner()\n\t\t)\n\t{\n\t\tthis->Unsummon();\n\t\treturn true;\n\t}\n\n\tif (m_pkOwner->IsDead())\n\t\treturn true;\n'


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: apply_petstaysondeath.py <game/src dir>")
    path = os.path.join(sys.argv[1], "PetSystem.cpp")
    raw = open(path, "rb").read()
    if MARK.encode() in raw:
        print("petstaysondeath: already applied")
        return
    crlf = b"\r\n" in raw
    text = raw.decode("latin-1").replace("\r\n", "\n")
    if text.count(OLD) != 1:
        sys.exit("petstaysondeath: the expected unsummon block is not in PetSystem.cpp - nothing changed")
    text = text.replace(OLD, NEW)
    if crlf:
        text = text.replace("\n", "\r\n")
    open(path, "wb").write(text.encode("latin-1"))
    print("petstaysondeath: applied")


if __name__ == "__main__":
    main()
