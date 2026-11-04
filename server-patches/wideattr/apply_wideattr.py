#!/usr/bin/env python3
"""apply_wideattr.py <engine game/src dir> -- Linux/VPS twin of Apply-WideattrPatch.ps1: the edits of edits.json
(README.md, MT2009_PLUS_WIDE_ATTR_V1 - an item's bonus type, an item_proto apply and an affect's point are two bytes).
Applied LAST, after every other server-patch of the list (its anchors are their lines). An edit whose new code is
already there is skipped; one whose old code is not found exactly once stops everything before a file is written."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def lines_in_order(text, new):
    # a later patch of the list (bonusy67c) puts its points between the lines of an edit's new code (length.h #1: above
    # the comment, before POINT_WIDE_END) - the edit is there when the old code is gone and each of its new lines stands,
    # in order (a second run over a patched tree: the package build, a later deploy)
    # (a code line's trailing comment may be renumbered by it - POINT_WIDE_END's "// 256" is "// 319" after bonusy67c -
    # so a line with code before its "//" is looked for by that code)
    pos = 0
    for line in new.split("\n"):
        if not line.strip():
            continue
        code = line.split("//", 1)[0].rstrip()
        if code.strip():
            line = code
        i = text.find(line, pos)
        if i < 0:
            return False
        pos = i + len(line)
    return True


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: apply_wideattr.py <game/src dir>")
    edits = json.load(open(os.path.join(HERE, "edits.json")))
    texts, crlf = {}, {}
    for e in edits:
        if e["file"] not in texts:
            raw = open(os.path.join(sys.argv[1], e["file"]), "rb").read()
            crlf[e["file"]] = b"\r\n" in raw
            texts[e["file"]] = raw.decode("latin-1").replace("\r\n", "\n")
    applied = 0
    for e in edits:
        text = texts[e["file"]]
        if e["new"] in text or (e["old"] not in text and lines_in_order(text, e["new"])):
            continue
        if text.count(e["old"]) != 1:
            sys.exit("wideattr: %s - the expected code of %s is not in the file; nothing changed" % (e["file"], e["marker"]))
        texts[e["file"]] = text.replace(e["old"], e["new"])
        applied += 1
    for name, text in texts.items():
        if crlf[name]:
            text = text.replace("\n", "\r\n")
        path = os.path.join(sys.argv[1], name)
        if open(path, "rb").read() != text.encode("latin-1"):
            open(path, "wb").write(text.encode("latin-1"))
    print("wideattr: %d edit(s) applied" % applied)


if __name__ == "__main__":
    main()
