#!/usr/bin/env python3
"""apply_metindrops.py <engine game/src dir> -- Linux/VPS twin of
Apply-MetinDropsPatch.ps1 (same replacements, same marker).
- A Metin stone drops the +0 sash at 15% (a boss keeps 80%): the engine ranks
  the Metins as bosses, so every Metin gave a sash at 80% (operator, 1 October
  2026: "Szarfa z metinow 15%").
- A Metin stone drops Cor Draconis at 20% (it was 50%; a boss keeps 80%, a
  bot's kill keeps its own 5%): "Cor draconis z metinow to 20%".
- The command flood guard: the client's own polls (autohunt_target,
  autohunt_loot, gmpanel_check_gm, kalendarz, ingame_event) no longer count,
  and a player has 10 commands per half second instead of 5 - his stat
  clicks, the sidekick's window and "lochy open" were being dropped behind the
  polls ("Zwolnic limit komend").
Needs botsashdrop and raretoggle applied first. Applied once; a file without
the expected code stops with an error, changing nothing."""
import os
import sys

MARK = "MT2009_PLUS_METIN_DROPS_V1"
EDITS = [
    ("item_manager.cpp",
     "\t\tconst int szarfaChance = 80;\n",
     "\t\t// " + MARK + " (server-patches/metindrops): a Metin 15%, a boss 80%.\n"
     "\t\tconst int szarfaChance = pkChr->IsStone() ? 15 : 80;\n"),
    ("item_manager.cpp",
     "\t\t\tcorChance = 50;\n"
     "\t\t\tcorKind = \"stone\";\n",
     "\t\t\t// " + MARK + " (server-patches/metindrops): a Metin 20% (it was 50).\n"
     "\t\t\tcorChance = 20;\n"
     "\t\t\tcorKind = \"stone\";\n"),
    ("cmd.cpp",
     "\tif (ch && !PulseManager::Instance().IncreaseCount(ch->GetPlayerID(), ePulse::CommandRequest, std::chrono::milliseconds(500), 5))\n",
     "\t// " + MARK + " (server-patches/metindrops): the client's own polls do not\n"
     "\t// count, and a player has 10 commands a half second (it was 5).\n"
     "\tstatic const char* const s_apszUnthrottled[] = { \"autohunt_target\", \"autohunt_loot\", \"gmpanel_check_gm\", \"kalendarz\", \"ingame_event\", NULL };\n"
     "\tbool bUnthrottled = false;\n"
     "\tfor (int i = 0; s_apszUnthrottled[i] && !bUnthrottled; ++i)\n"
     "\t{\n"
     "\t\tconst size_t n = strlen(s_apszUnthrottled[i]);\n"
     "\t\tbUnthrottled = !strncmp(argument, s_apszUnthrottled[i], n) && (argument[n] == ' ' || argument[n] == '\\0');\n"
     "\t}\n"
     "\tif (ch && !bUnthrottled && !PulseManager::Instance().IncreaseCount(ch->GetPlayerID(), ePulse::CommandRequest, std::chrono::milliseconds(500), 10))\n"),
]


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    files = {}
    for name, old, new in EDITS:
        path = os.path.join(sys.argv[1], name)
        if path not in files:
            files[path] = open(path, "rb").read().decode("latin-1")
    for name, old, new in EDITS:
        path = os.path.join(sys.argv[1], name)
        text = files[path]
        # The marker comment line is enough: a later patch (raremobrules) rewrites
        # the line under it, and the edit is still in place.
        if new.split("\n")[0] in text:
            continue
        crlf = "\r\n" in text
        o, n = (old.replace("\n", "\r\n"), new.replace("\n", "\r\n")) if crlf else (old, new)
        if text.count(o) != 1:
            sys.exit("metindrops: expected code not found in " + path + " -- nothing changed")
        files[path] = text.replace(o, n, 1)
    for path, text in files.items():
        before = open(path, "rb").read().decode("latin-1")
        if text != before:
            open(path, "wb").write(text.encode("latin-1"))
            print("metindrops: %s applied" % os.path.basename(path))
        else:
            print("metindrops: %s already applied" % os.path.basename(path))


if __name__ == "__main__":
    main()
