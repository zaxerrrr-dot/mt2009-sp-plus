#!/usr/bin/env python3
"""apply_corautostack.py <engine game/src dir> -- Linux/VPS twin of
Apply-CorAutoStackPatch.ps1 (same replacements, same marker). A Cor Draconis
picked up off the ground or given (CHARACTER::AutoStackItem and
AutoStackItemProto, char_item.cpp) joins the stack already in the bag even
where the proto carries ANTI_STACK or no STACKABLE flag - as a drag already
does (server-patches/corstack, which this needs: IsStackableCorDraconisVnum).
Applied once; a file without the expected code stops with an error."""
import os
import sys

MARK = 'MT2009_PLUS_COR_AUTOSTACK_V1'
PAIRS = [('\tif (p->dwFlags & ITEM_FLAG_STACKABLE && p->bType != ITEM_BLEND)\n',
          '\t// MT2009_PLUS_COR_AUTOSTACK_V1 (server-patches/corautostack): a Cor Draconis\n\t// joins the stack its owner carries whatever the proto says, as a drag does\n\t// (IsStackableCorDraconisVnum, server-patches/corstack).\n\tif (((p->dwFlags & ITEM_FLAG_STACKABLE) || IsStackableCorDraconisVnum(dwItemVnum)) && p->bType != ITEM_BLEND)\n'),
         ('\tif (item->IsStackable() && !IS_SET(item->GetAntiFlag(), ITEM_ANTIFLAG_STACK))\n\t{\n\t\tauto bCount = item->GetCount();\n',
          '\t// MT2009_PLUS_COR_AUTOSTACK_V1: a Cor Draconis picked up or given joins the\n\t// stack already in the bag, even where the proto has ANTI_STACK or lacks\n\t// STACKABLE - the pickup put every Cor in a stack of its own.\n\tif ((item->IsStackable() && !IS_SET(item->GetAntiFlag(), ITEM_ANTIFLAG_STACK)) ||\n\t\t\tIsStackableCorDraconisVnum(item->GetVnum()))\n\t{\n\t\tauto bCount = item->GetCount();\n')]


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    path = os.path.join(sys.argv[1], "char_item.cpp")
    text = open(path, "rb").read().decode("latin-1")
    if MARK in text:
        print("corautostack: already applied")
        return
    if 'IsStackableCorDraconisVnum' not in text:
        sys.exit("corautostack: needs server-patches/corstack first")
    crlf = "\r\n" in text
    for old, new in PAIRS:
        if crlf:
            old, new = old.replace("\n", "\r\n"), new.replace("\n", "\r\n")
        if text.count(old) != 1:
            sys.exit("corautostack: expected code not found in " + path)
        text = text.replace(old, new, 1)
    open(path, "wb").write(text.encode("latin-1"))
    print("corautostack: applied")


if __name__ == "__main__":
    main()
