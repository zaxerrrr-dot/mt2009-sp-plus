#!/usr/bin/env python3
"""gen_edits.py <base server dir> <edited server dir> - writes edits.json of server-patches/wideattr
(MT2009_PLUS_WIDE_ATTR_V1, README.md) - the developer's tool; the apply scripts read edits.json only.

<base> is the engine tree (game/src, common, db/src) with the overlay and every server-patch of the deploy list applied
(this patch is the LAST one); <edited> is the same tree with the two-byte bonus type done by hand. Every engine file of
FILES that differs becomes edits: each changed block of lines with as little unchanged context as keeps its old text
unique in the file. The edits are then replayed on <base> exactly as apply_wideattr.py does - each must apply (none
already there), the result must equal <edited>, and a second run must change nothing - or nothing is written.
The overlay's own files (linux-port/overlays/playerbot) are edited in place, not here."""
import difflib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
M = 'MT2009_PLUS_WIDE_ATTR_V1'
# paths as the apply script sees them: relative to game/src
FILES = [
    '../../common/length.h', '../../common/tables.h',
    'affect.h', 'packet.h', 'char.h', 'char.cpp', 'char_affect.cpp', 'char_item.cpp', 'char_skill.cpp', 'skill.h',
    'item.h', 'item.cpp', 'item_attribute.cpp', 'item_manager.cpp', 'constants.h', 'constants.cpp', 'battle.h',
    'DragonSoul.cpp', 'dragon_soul_table.h', 'dragon_soul_table.cpp', 'dungeon.h', 'dungeon.cpp', 'log.h', 'log.cpp',
    'cmd_gm.cpp', 'questlua_affect.cpp', 'questlua_dungeon.cpp', 'questlua_item.cpp', 'questlua_party.cpp',
    'questlua_pc.cpp',
]


def read(path):
    raw = open(path, 'rb').read().decode('latin-1')
    return raw.replace('\r\n', '\n')


def apply_one(text, e):
    """the apply scripts' rule: already there -> same text; old exactly once -> replaced; else None"""
    if e['new'] in text:
        return text, False
    if text.count(e['old']) != 1:
        return None, False
    return text.replace(e['old'], e['new']), True


def hunks(a, b):
    al, bl = a.split('\n'), b.split('\n')
    ops = [op for op in difflib.SequenceMatcher(None, al, bl, autojunk=False).get_opcodes() if op[0] != 'equal']
    merged = []
    for op in ops:  # blocks closer than 3 lines are one edit
        if merged and op[1] - merged[-1][2] < 3:
            merged[-1] = ('replace', merged[-1][1], op[2], merged[-1][3], op[4])
        else:
            merged.append(op)
    return al, bl, merged


def make_edits(name, a, b):
    al, bl, merged = hunks(a, b)
    out = []
    for n, (_, i1, i2, j1, j2) in enumerate(merged):
        before = after = 0
        while True:
            lo, hi = i1 - before, i2 + after
            if lo < 0 or hi > len(al):
                sys.exit('wideattr gen: %s - no unique context for block %d' % (name, n))
            old = '\n'.join(al[lo:hi]) + ('\n' if hi < len(al) else '')
            new = '\n'.join(al[lo:i1] + bl[j1:j2] + al[i2:hi]) + ('\n' if hi < len(al) else '')
            if old.strip() and a.count(old) == 1 and new not in a:
                break
            if before <= after:
                before += 1
            else:
                after += 1
        out.append(dict(file=name, marker='%s (%s #%d)' % (M, os.path.basename(name), n + 1), old=old, new=new))
    return out


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    base, edited = sys.argv[1], sys.argv[2]
    edits = []
    for f in FILES:
        pa = os.path.normpath(os.path.join(base, 'game/src', f))
        pb = os.path.normpath(os.path.join(edited, 'game/src', f))
        a, b = read(pa), read(pb)
        if a == b:
            sys.exit('wideattr gen: %s did not change - take it off FILES' % f)
        edits += make_edits(f, a, b)
    # replay as the apply script does
    texts = {}
    for e in edits:
        if e['file'] not in texts:
            texts[e['file']] = read(os.path.normpath(os.path.join(base, 'game/src', e['file'])))
        t, done = apply_one(texts[e['file']], e)
        if t is None or not done:
            sys.exit('wideattr gen: replay failed at %s' % e['marker'])
        texts[e['file']] = t
    for f, t in texts.items():
        if t != read(os.path.normpath(os.path.join(edited, 'game/src', f))):
            sys.exit('wideattr gen: replay of %s differs from the edited tree' % f)
        for e in edits:
            if e['file'] == f and apply_one(t, e) != (t, False):
                sys.exit('wideattr gen: %s is not idempotent' % e['marker'])
    json.dump(edits, open(os.path.join(HERE, 'edits.json'), 'w'), indent=1)
    print('wideattr gen: %d edits in %d files' % (len(edits), len(texts)))


if __name__ == '__main__':
    main()
