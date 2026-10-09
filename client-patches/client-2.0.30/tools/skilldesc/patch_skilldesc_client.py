# -*- coding: utf-8 -*-
# MT2009_PLUS_NS_SKILL_HINTS_V1 - "Wzmacnia: Sila (++), Witalnosc (+)..." at the end of the description of the 45
# class skills (warrior, ninja, sura, shaman) in the client's locale/pl/skilldesc.txt (Autor: Digi Rasta, nowy-system
# 0.30.1, his klient.py patch_skilldesc and dane/wzmacnia_umiejetnosci.tsv - here as wzmacnia_umiejetnosci.tsv, the
# same 45 lines: vnum<TAB>text; his card SYSTEMY/umiejetnosci-wzmocnienia.md: the stats read from the skill_proto
# formulas and the server's code - atk holds the class stat, ar is Dexterity for magic too).
#
# Only the description column (the 6th) changes: "<description>.|Wzmacnia: ..." - the "|" makes the skill tooltip
# (root uitooltip.py SplitDescription) start the hint on a line of its own (his version ran it on in the same line).
# A description that already carries a hint (his " Wzmacnia:" or ours "|Wzmacnia:") gets it replaced, so a second
# run changes nothing and an edit of the .tsv reaches the file. Client only; the server is unchanged.
#
# From client 2.0.52 skilldesc.txt lives in the "dbdata" pack (locale/pl/skilldesc.txt). Run on a plain copy, in the
# m2pack-lzo image (or any Python 2.7 / 3):
#   python3 <repo>/client-patches/client-2.0.30/tools/skilldesc/patch_skilldesc_client.py <skilldesc.txt> [<out dir>]
# Without an out dir the file is rewritten in place (only when something changed).
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TSV = os.path.join(HERE, 'wzmacnia_umiejetnosci.tsv')
MARK = u'Wzmacnia:'
COLUMN = 5          # 0 vnum, 1 job, 2-4 names, 5 description
EXPECTED = 45


def hints():
    out = {}
    with io.open(TSV, encoding='utf-8') as f:
        for line in f:
            line = line.rstrip(u'\r\n')
            if line.strip():
                vnum, text = line.split(u'\t', 1)
                assert text.startswith(MARK), line
                out[vnum.strip()] = text.strip()
    if len(out) != EXPECTED:
        raise SystemExit('%s: %d skills, %d expected' % (TSV, len(out), EXPECTED))
    return out


def patch(data):
    text = data.decode('cp1250')
    nl = u'\r\n' if u'\r\n' in text else u'\n'
    lines = text.split(nl)
    want = hints()
    seen = set()
    changed = 0
    for i, line in enumerate(lines):
        cols = line.split(u'\t')
        key = cols[0].strip()
        if key not in want or len(cols) <= COLUMN:
            continue
        seen.add(key)
        base = cols[COLUMN]
        for sep in (u'|' + MARK, u' ' + MARK):
            if sep in base:
                base = base.split(sep)[0]
        base = base.rstrip()
        if base and base[-1] not in u'.!?':
            base += u'.'
        cols[COLUMN] = (base + u'|' + want[key]) if base else want[key]
        new = u'\t'.join(cols)
        if new != line:
            lines[i] = new
            changed += 1
    missing = sorted(set(want) - seen, key=int)
    if missing:
        raise SystemExit('skilldesc.txt: no line for skill(s) %s' % ', '.join(missing))
    return nl.join(lines).encode('cp1250'), changed


def main():
    if len(sys.argv) not in (2, 3):
        raise SystemExit('usage: patch_skilldesc_client.py <skilldesc.txt> [<out dir>]')
    path = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) == 3 else None
    with open(path, 'rb') as f:
        data, changed = patch(f.read())
    target = os.path.join(out_dir, os.path.basename(path)) if out_dir else path
    if out_dir or changed:
        if out_dir and not os.path.isdir(out_dir):
            os.makedirs(out_dir)
        with open(target, 'wb') as f:
            f.write(data)
    print('%s: %d change(s)%s' % (os.path.basename(path), changed, '' if target == path else ' -> ' + target))


if __name__ == '__main__':
    main()
