#!/usr/bin/env python3
"""apply_corstack.py <engine game/src dir> -- Linux/VPS twin of
Apply-CorStackPatch.ps1 (same replacements, same marker). Cor Draconis boxes
(50252-50260, 51501-51632, 76040) stack in CHARACTER::MoveItem
(char_item.cpp) - merging onto the same vnum and splitting a count off - even
where the server proto still carries ANTI_STACK or no STACKABLE flag. The
change Codex made on the test server (custom-patches/cor_stack_move.patch),
brought into the release. Applied once; a file without the expected code
stops with an error, changing nothing. Only the blocks change, in the file's
own line ending."""
import os
import sys

MARK = 'IsStackableCorDraconisVnum'
PAIRS = [('enum {ITEM_BROKEN_METIN_VNUM = 28960};\n\n', 'enum {ITEM_BROKEN_METIN_VNUM = 28960};\n\n// MT2009 Plus: Cor Draconis items from the newer client data must remain\n// stackable even when the legacy server proto still carries ANTI_STACK.\nstatic bool IsStackableCorDraconisVnum(DWORD vnum)\n{\n\tswitch (vnum)\n\t{\n\t\tcase 50252: case 50255: case 50256: case 50257: case 50258: case 50259: case 50260:\n\t\tcase 51501: case 51502: case 51503: case 51504: case 51505: case 51506: case 51507: case 51508: case 51509: case 51510:\n\t\tcase 51541: case 51548: case 51549: case 51562: case 51569: case 51576: case 51583: case 51590: case 51597:\n\t\tcase 51604: case 51611: case 51618: case 51625: case 51632: case 76040:\n\t\t\treturn true;\n\t}\n\treturn false;\n}\n\n'), ('\tconst bool bDSMoveTrace = bDSMoveTraceSrc || item->IsDragonSoul() || item->GetType() == ITEM_SPECIAL_DS;\n', '\tconst bool bDSMoveTrace = bDSMoveTraceSrc || item->IsDragonSoul() || item->GetType() == ITEM_SPECIAL_DS;\n\tconst bool bForceCorStack = IsStackableCorDraconisVnum(item->GetVnum());\n'), ('\t\tif ((item2 = GetItem(DestCell)) && item != item2 && item2->IsStackable() &&\n\t\t\t\t!IS_SET(item2->GetAntiFlag(), ITEM_ANTIFLAG_STACK) &&\n', '\t\tif ((item2 = GetItem(DestCell)) && item != item2 && (item2->IsStackable() || bForceCorStack) &&\n\t\t\t\t(!IS_SET(item2->GetAntiFlag(), ITEM_ANTIFLAG_STACK) || bForceCorStack) &&\n'), ('\t\tif (count == 0 || count >= item->GetCount() || !item->IsStackable() || IS_SET(item->GetAntiFlag(), ITEM_ANTIFLAG_STACK))\n', '\t\tif (count == 0 || count >= item->GetCount() ||\n\t\t\t\t(!item->IsStackable() && !bForceCorStack) ||\n\t\t\t\t(IS_SET(item->GetAntiFlag(), ITEM_ANTIFLAG_STACK) && !bForceCorStack))\n')]


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    path = os.path.join(sys.argv[1], "char_item.cpp")
    text = open(path, "rb").read().decode("latin-1")
    if MARK in text:
        print("corstack: already applied")
        return
    crlf = "\r\n" in text
    for old, new in PAIRS:
        if crlf:
            old, new = old.replace("\n", "\r\n"), new.replace("\n", "\r\n")
        if text.count(old) != 1:
            sys.exit("corstack: expected code not found in " + path)
        text = text.replace(old, new, 1)
    open(path, "wb").write(text.encode("latin-1"))
    print("corstack: applied")


if __name__ == "__main__":
    main()
