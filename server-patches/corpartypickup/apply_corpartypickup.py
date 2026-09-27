#!/usr/bin/env python3
"""apply_corpartypickup.py <engine game/src dir> -- Linux/VPS twin of
Apply-CorPartyPickupPatch.ps1 (same edit, same marker). A bot may not pick a
Cor Draconis up (CHARACTER::PickupItem), so the companion, which collects its
owner's drop through the party branch of PickupItem, walked to the owner's
Cor, was refused and gave up ("Towarzysz nie podnosi Corow", 27 September).
A bot now may pick up a Cor that is owned by a real player of its own party:
the party branch hands it straight to that player. Every other Cor stays
refused. Applied once; a file without the expected code stops with an error,
changing nothing."""
import os
import sys

MARK = "MT2009_PLUS_COR_PARTY_PICKUP_V1"
OLD = '\tif (item->GetVnum() == 50255 &&\n\t\tGetDesc() &&\n\t\tGetDesc()->IsBot())\n\t{\n\t\tsys_log(0, "[DS_COR_DROP] pickup blocked: bot pid=%u name=%s tried to pick up Cor Draconis id=%u",\n\t\t\tGetPlayerID(), GetName(), item->GetID());\n\t\treturn false;\n\t}\n'
NEW = '\t//\n\t// MT2009_PLUS_COR_PARTY_PICKUP_V1: except a Cor that is a real player\'s of\n\t// the bot\'s own party - the companion collecting its owner\'s drop, a bot\n\t// invited into a player\'s party. The party branch below hands such an\n\t// item straight to its owner, so the bot never holds it ("Towarzysz nie\n\t// podnosi Corow", 27 September). Only an owned Cor: an ownerless one would\n\t// go to whichever member the party branch finds last, a bot as likely.\n\tif (item->GetVnum() == 50255 &&\n\t\tGetDesc() &&\n\t\tGetDesc()->IsBot())\n\t{\n\t\tLPCHARACTER corOwner = NULL;\n\t\tif (!item->IsOwnership(this) && GetParty() &&\n\t\t\t!IS_SET(item->GetAntiFlag(), ITEM_ANTIFLAG_GIVE | ITEM_ANTIFLAG_DROP))\n\t\t{\n\t\t\tNPartyPickupDistribute::FFindOwnership findOwner(item);\n\t\t\tGetParty()->ForEachOnlineMember(findOwner);\n\t\t\tcorOwner = findOwner.owner;\n\t\t}\n\t\tif (!corOwner || corOwner == this || !corOwner->GetDesc() || corOwner->GetDesc()->IsBot())\n\t\t{\n\t\t\tsys_log(0, "[DS_COR_DROP] pickup blocked: bot pid=%u name=%s tried to pick up Cor Draconis id=%u",\n\t\t\t\tGetPlayerID(), GetName(), item->GetID());\n\t\t\treturn false;\n\t\t}\n\t\tsys_log(0, "[DS_COR_DROP] party pickup: bot pid=%u name=%s picks up Cor Draconis id=%u for %s",\n\t\t\tGetPlayerID(), GetName(), item->GetID(), corOwner->GetName());\n\t}\n'


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: apply_corpartypickup.py <game/src dir>")
    path = os.path.join(sys.argv[1], "char_item.cpp")
    raw = open(path, "rb").read()
    if MARK.encode() in raw:
        print("corpartypickup: already applied")
        return
    crlf = b"\r\n" in raw
    text = raw.decode("latin-1").replace("\r\n", "\n")
    if text.count(OLD) != 1:
        sys.exit("corpartypickup: the expected Cor Draconis pickup block is not in char_item.cpp - nothing changed")
    text = text.replace(OLD, NEW)
    if crlf:
        text = text.replace("\n", "\r\n")
    open(path, "wb").write(text.encode("latin-1"))
    print("corpartypickup: applied")


if __name__ == "__main__":
    main()
