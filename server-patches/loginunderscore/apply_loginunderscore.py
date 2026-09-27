#!/usr/bin/env python3
"""apply_loginunderscore.py <engine game/src dir> -- Linux/VPS twin of
Apply-LoginUnderscorePatch.ps1 (same edit, same marker). The auth core took
letters and digits only (FN_IS_VALID_LOGIN_STRING), and every bot's account is
playerbot_NNN, so a bot taken over from the advanced panel ("Przejmij bota",
27 September) answered its right password with "wrong login". An underscore is
now a login's letter too. Applied once; a file without the expected code stops
with an error, changing nothing."""
import os
import sys

MARK = "MT2009_PLUS_LOGIN_UNDERSCORE_V1"
OLD = "\t\tif (isdigit(*tmp) || isalpha(*tmp))\n\t\t\tcontinue;\n\n#ifdef ENABLE_ACCOUNT_W_SPECIALCHARS\n"
NEW = ("\t\tif (isdigit(*tmp) || isalpha(*tmp))\n\t\t\tcontinue;\n\n"
       "\t\t// MT2009_PLUS_LOGIN_UNDERSCORE_V1 (server-patches/loginunderscore): a\n"
       "\t\t// bot's account is playerbot_NNN, and the advanced panel hands it to a\n"
       "\t\t// person for a while (\"Przejmij bota\").\n"
       "\t\tif (*tmp == '_')\n\t\t\tcontinue;\n\n"
       "#ifdef ENABLE_ACCOUNT_W_SPECIALCHARS\n")


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: apply_loginunderscore.py <game/src dir>")
    path = os.path.join(sys.argv[1], "input_auth.cpp")
    raw = open(path, "rb").read()
    if MARK.encode() in raw:
        print("loginunderscore: already applied")
        return
    crlf = b"\r\n" in raw
    text = raw.decode("latin-1").replace("\r\n", "\n")
    if text.count(OLD) != 1:
        sys.exit("loginunderscore: the expected login check is not in input_auth.cpp - nothing changed")
    text = text.replace(OLD, NEW)
    if crlf:
        text = text.replace("\n", "\r\n")
    open(path, "wb").write(text.encode("latin-1"))
    print("loginunderscore: applied")


if __name__ == "__main__":
    main()
