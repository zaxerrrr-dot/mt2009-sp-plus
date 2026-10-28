#!/usr/bin/env python3
"""gen_edits.py - writes edits.json of server-patches/czepiec (MT2009_PLUS_SERPENT_HOOD_V1, README.md) from the code
below and the random bonus table of tools/czepiec/czepiec_items.json (tools/czepiec/gen_czepiec.py); the developer's
tool (the apply scripts read edits.json only). Applied after server-patches/ysets (it changes ysets' functions in
item.cpp). Every anchor is checked against a patched engine tree when one is given:

  python3 gen_edits.py [<engine game/src dir to check the anchors against>]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
M = 'MT2009_PLUS_SERPENT_HOOD_V1'


def hood():
    d = json.load(open(os.path.join(REPO, 'tools', 'czepiec', 'czepiec_items.json'), encoding='utf-8'))
    return d['hood']


def table(h):
    L = ['static const SMt2009YSetsOption s_aYSetsHood[] = {']
    for o in h['line']:
        rows = o['rows'] + [o['rows'][-1]] * (5 - len(o['rows']))
        L.append('\t{ %d, %d, { %s } },' % (o['point'], len(o['rows']), ', '.join(
            '{ %s }' % ', '.join(str(v) for v in r) for r in rows)))
    L.append('};')
    return '\n'.join(L)


def edits():
    h = hood()
    assert h['levels'] == 16 and 1 <= len(h['line']) <= 15
    fam_old = 'bool Mt2009YSetsRandomFamily(DWORD dwVnum, int& iKind, int& iLevel)\n{\n'
    fam_new = (
        '// ' + M + ' (tables): Wezowy Czepiec (12880-12895, tools/czepiec) - one random line of the wiki\'s\n'
        '// "1. Bonus" (Wola SungMa x4, Precyzja, Odp. na Magie, Odp. na atak potworow, Blok, Unik strzaly), the line\'s\n'
        '// byte in yextra bits 8-15 like a serpent piece\'s first line (bonus + 1 | row << 4): rolled when the helmet is\n'
        '// made, carried by a refine (Mt2009YSetsCopy, the same kind), in the points at its refine level. Its main bonus\n'
        '// (Mag./krotkodys. atak) is item_proto\'s apply; bonuses 1-5 and 6/7 are any helmet\'s.\n'
        + table(h) + '\n'
        'enum { YSETS_HOOD_KIND = 2, YSETS_HOOD_BASE = %d, YSETS_HOOD_LEVELS = %d };\n'
        'static const int s_iYSetsHoodCount = (int) (sizeof(s_aYSetsHood) / sizeof(s_aYSetsHood[0]));\n\n'
        % (h['base'], h['levels'])
        + fam_old +
        '\tif (dwVnum >= YSETS_HOOD_BASE && dwVnum < YSETS_HOOD_BASE + YSETS_HOOD_LEVELS) // ' + M + ' (family)\n'
        '\t{\n'
        '\t\tiKind = YSETS_HOOD_KIND;\n'
        '\t\tiLevel = dwVnum - YSETS_HOOD_BASE;\n'
        '\t\treturn true;\n'
        '\t}\n')
    roll_old = ('static void Mt2009YSetsRoll(LPITEM item, int iKind)\n{\n'
                '\tDWORD dwExtra = item->GetYExtra() & 0xFF;\n')
    roll_new = roll_old + (
        '\tif (iKind == YSETS_HOOD_KIND) // ' + M + ' (roll): the hood\'s one line\n'
        '\t{\n'
        '\t\tconst int iOpt = number(0, s_iYSetsHoodCount - 1);\n'
        '\t\tconst int iRow = number(0, s_aYSetsHood[iOpt].bRows - 1);\n'
        '\t\titem->SetYExtra(dwExtra | ((DWORD) ((iOpt + 1) | (iRow << 4)) << 8));\n'
        '\t\treturn;\n'
        '\t}\n')
    pts_old = ('\tif (!owner || !item->GetYExtra() || !Mt2009YSetsRandomFamily(item->GetVnum(), iKind, iLevel))\n'
               '\t\treturn;\n')
    pts_new = pts_old + (
        '\tif (iKind == YSETS_HOOD_KIND) // ' + M + ' (points): the hood\'s one line at its refine level\n'
        '\t{\n'
        '\t\tconst BYTE b = (item->GetYExtra() >> 8) & 0xFF;\n'
        '\t\tconst int iOpt = (b & 0x0F) - 1;\n'
        '\t\tconst int iRow = b >> 4;\n'
        '\t\tif (iOpt >= 0 && iOpt < s_iYSetsHoodCount && iRow < s_aYSetsHood[iOpt].bRows)\n'
        '\t\t{\n'
        '\t\t\tconst int iValue = s_aYSetsHood[iOpt].asValue[iRow][iLevel];\n'
        '\t\t\towner->PointChange(s_aYSetsHood[iOpt].bPoint, bAdd ? iValue : -iValue);\n'
        '\t\t}\n'
        '\t\treturn;\n'
        '\t}\n')
    return [
        dict(file='item.cpp', marker=M + ' (tables)', old=fam_old, new=fam_new),
        dict(file='item.cpp', marker=M + ' (roll)', old=roll_old, new=roll_new),
        dict(file='item.cpp', marker=M + ' (points)', old=pts_old, new=pts_new),
    ]


def main():
    E = edits()
    for e in E:
        assert e['marker'] in e['new'] and e['marker'] not in e['old'], e['marker']
        e['new'].encode('latin-1')
    if len(sys.argv) > 1:
        texts = {}
        for e in E:
            if e['file'] not in texts:
                texts[e['file']] = open(os.path.join(sys.argv[1], e['file']), 'rb').read().decode('latin-1').replace('\r\n', '\n')
            t = texts[e['file']]
            if e['marker'] in t:
                print('%s: already there' % e['marker'])
            elif t.count(e['old']) != 1:
                sys.exit('%s: the anchor is in %s %d times' % (e['marker'], e['file'], t.count(e['old'])))
            else:
                print('%s: anchor ok' % e['marker'])
    with open(os.path.join(HERE, 'edits.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(E, f, indent=1)
        f.write('\n')
    print('edits.json: %d edit(s)' % len(E))


if __name__ == '__main__':
    main()
