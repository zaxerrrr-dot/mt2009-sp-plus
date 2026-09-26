#!/usr/bin/env python3
"""Write the title and notes of a GitHub Release for one CHANGELOG.md version.

    python3 .github/scripts/github_release.py 2.6.0 OUT_DIR
    python3 .github/scripts/github_release.py 2.0.17 OUT_DIR --client

Writes OUT_DIR/title.txt and OUT_DIR/notes.md from the same section the
Discord post uses (discord_release.py), so the release page, the Discord
announcement and the panels all say the same thing. Exits non-zero when the
changelog has no section for the version.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from discord_release import read, section  # noqa: E402

REPO = os.environ.get("GITHUB_REPOSITORY", "zaxerrrr-dot/mt2009-sp-plus")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    client = "--client" in sys.argv
    if len(args) != 2:
        sys.exit(__doc__)
    version, out = args
    found = section(read("CHANGELOG.md"), version, client)
    if not found:
        sys.exit("CHANGELOG.md has no section for %s%s" % ("Klient " if client else "", version))
    rest, body = found
    # "— 2026-09-24 — Title" after the version: the date goes, a title stays.
    parts = [p.strip() for p in re.split(r"\s+[—–-]\s+", rest.strip(" —–-")) if p.strip()]
    parts = [p for p in parts if not re.fullmatch(r"\d{4}-\d\d-\d\d", p)]
    label = ("MT2009 PLUS — klient %s" if client else "MT2009 PLUS %s") % version
    title = label + (" — " + " — ".join(parts) if parts else "")
    kind = "client" if client else "server"
    notes = (body + "\n\n---\n\n"
             "Aktualizacja instaluje się sama: launcher (Windows) albo "
             "`sh linux-port/tools/update.sh` (VPS). Plik "
             "`metin2-%s-update-%s.zip` poniżej to ta sama paczka, do pobrania "
             "ręcznie. Pełna historia zmian: "
             "[CHANGELOG.md](https://github.com/%s/blob/main/CHANGELOG.md).\n"
             % (kind, version, REPO))
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "title.txt"), "w", encoding="utf-8") as f:
        f.write(title)
    with open(os.path.join(out, "notes.md"), "w", encoding="utf-8") as f:
        f.write(notes)
    print(title)


if __name__ == "__main__":
    main()
