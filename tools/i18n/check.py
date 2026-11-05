#!/usr/bin/env python3
"""Checks of the web pages' language files (MT2009_PLUS_WEB_I18N_V1):

  - a translation must not name the game's publisher, the game by its brand,
    "official", or Ameria / metin2alerts (the file name
    Metin2Distribute.exe and the project's address metin2sp.pl are no names)
  - every {N} of the text is in its translation
  - a translation that is still Polish (Polish letters, not a name)

    python3 tools/i18n/check.py            # report
    python3 tools/i18n/check.py --strict   # exit 1 on a forbidden word or a placeholder
"""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from catalog import APP_DIRS  # noqa: E402

BRAND = re.compile(r"metin\s*2|gameforge|\bt[i]eru\b|\bameria\b|metin2alerts", re.I)
# "official" in each language; some of these words also mean "officer" / "picture" (names are skipped)
OFFICIAL = re.compile(r"\bofficial|oficjal|offiziell|\bofficiel|ufficial|\boficial|\bresm[iî]\b|hivatalos|oficiáln|επίσημ", re.I)
ALLOWED = re.compile(r"Metin2Distribute\.exe|metin2sp\.pl|/opt/metin2\S*|metin2_\w+|m2", re.I)
PH = re.compile(r"\{\d+\}")
PL = re.compile(r"[ąćęłńśźżĄĆĘŁŃŚŹŻ]")


def main(strict):
    bad = 0
    for app, d in APP_DIRS.items():
        for path in sorted(glob.glob(os.path.join(d, "*.json")) + glob.glob(os.path.join(d, "*", "*.json"))):
            lang = os.path.basename(path)[:-5] if os.path.dirname(path) == d else os.path.basename(os.path.dirname(path))
            try:
                data = json.load(open(path, encoding="utf-8"))
            except ValueError as e:
                print("BROKEN", path, e)
                bad += 1
                continue
            forbidden, holders, polish = [], [], []
            for key in ("exact", "patterns", "names"):
                for src, val in (data.get(key) or {}).items():
                    if not isinstance(val, str):
                        continue
                    clean = ALLOWED.sub("", val)
                    if BRAND.search(clean) or (key != "names" and OFFICIAL.search(clean)):
                        forbidden.append((src, val))
                    if sorted(PH.findall(src)) != sorted(PH.findall(val)):
                        holders.append((src, val))
                    if lang != "pl" and key != "names" and PL.search(val) and val == src and len(val) > 12:
                        polish.append(src)
            if forbidden or holders or polish:
                print("%s %s: forbidden %d, placeholders %d, still Polish %d" % (
                    app, os.path.relpath(path, d), len(forbidden), len(holders), len(polish)))
                for s, v in forbidden[:5]:
                    print("   FORBIDDEN", repr(s[:80]), "->", repr(v[:120]))
                for s, v in holders[:3]:
                    print("   PLACEHOLDER", repr(s[:80]), "->", repr(v[:80]))
            bad += len(forbidden) + len(holders)
    if strict and bad:
        sys.exit(1)


if __name__ == "__main__":
    main("--strict" in sys.argv)
