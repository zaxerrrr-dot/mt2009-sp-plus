#!/usr/bin/env python3
"""gen_edits.py [<game/src>] - writes edits.json of server-patches/jadeit67 (MT2009_PLUS_JADE_BONUS67_V1, README.md)
from the code below; the developer's tool (the apply scripts read edits.json only). With a game/src dir it also checks
that every edit applies there. Applied after server-patches/obreczjadeitu2 (its MT2009_PLUS_JADE_BASE_V1 blocks are the
anchors).

Each edit has "olds": the code it looks for, in order - the first found exactly once is replaced by "new" (an edit
already there - its marker - is skipped; none found stops everything before a file is written)."""
import json
import os
import sys

M = 'MT2009_PLUS_JADE_BONUS67_V1'
V1 = 'MT2009_PLUS_JADE_BRACELET_V1'
B = 'MT2009_PLUS_JADE_BASE_V1'


def edit(tag):
    guard = ('\tif (Mt2009JadeBraceletType(GetVnum(), bWillTalismanType)) // %s (%s): its Will line\n'
             '\t\treturn false;\n') % (V1, tag)
    base = ('\t{ // %s (%s): the jade\'s base lines are no bonus any more - an old piece\'s leave its 6th/7th slots\n'
            % (B, tag))
    # The comment names V1's marker on purpose: V1's apply skips an edit whose marker is in the file, and
    # JADE_BASE_V1 had replaced V1's guard together with that marker - so every later run of the chain on the same tree
    # (yohara-deploy.sh, Apply-MT2009PlusEngine.ps1) put the guard back above JADE_BASE_V1's block and the jade refused
    # 71051 / 71052 / 72351 / Seon-Hae again.
    note = ('\t// %s (%s): Obrecz / Kolia / Klipsy Jadeitu take the 6th and 7th bonus (the owner, 8 Nov 2026 "napraw";\n'
            '\t// their Precyzja and Will are the base attribute, never touched here) - %s (%s)\'s guard stays out\n'
            % (M, tag, V1, tag))
    return dict(file='item_attribute.cpp', marker='%s (%s)' % (M, tag), olds=[guard + base, base], new=note + base)


EDITS = [edit(tag) for tag in ('change rare', 'change rare 2', 'add rare', 'add rare 2')]


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    for e in EDITS:
        assert e['marker'] in e['new'], e['marker']
        assert V1 + ' (' + e['marker'].split(' (', 1)[1] in e['new']
    assert len(set(e['marker'] for e in EDITS)) == len(EDITS)
    if len(sys.argv) > 1:
        for e in EDITS:
            text = open(os.path.join(sys.argv[1], e['file']), 'rb').read().decode('latin-1').replace('\r\n', '\n')
            assert e['marker'] in text or any(text.count(o) == 1 for o in e['olds']), e['marker']
        print('anchors ok')
    with open(os.path.join(here, 'edits.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(EDITS, f, ensure_ascii=False, indent=1)
        f.write('\n')


if __name__ == '__main__':
    main()
