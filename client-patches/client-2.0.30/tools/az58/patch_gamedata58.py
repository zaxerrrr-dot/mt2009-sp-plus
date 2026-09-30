# -*- coding: utf-8 -*-
# Phases 5-8 on top of az29/patch_gamedata.py (same functions, all from data/allocation.json, idempotent):
# the new items' icons, the nested Plechito races' alias lines in npclist ("0 <race> <dir>/<race>"),
# and the new maps' minimap names beside phase 1's in localeinfo.py.
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import patch_gamedata as pg
from patch_gamedata import ALLOC, MARK, mob_rows, item_rows, atlasinfo, itemdesc, _lines, _join, _append, _esc
pg.ICON.update({30766: 'icon/item/30327.tga', 30767: 'icon/item/30327.tga', 30768: 'icon/item/30327.tga',
                30774: 'icon/item/50270.tga', 30775: 'icon/item/50270.tga', 30776: 'icon/item/50271.tga'})
item_list = pg.item_list
PLAN = json.load(open(HERE + '/plan58.json'))
ALIASES = PLAN['aliases']            # race -> dir as the Arezzo npclist has it (backslashes made /)
def npclist(b):
    b = pg.npclist(b)
    ls = _lines(b); have = {}
    for i, l in enumerate(ls):
        t = l.split('\t')
        if len(t) >= 3 and t[0].strip() == '0': have[t[1].strip().lower()] = i
    rows = []
    for race, d in sorted(ALIASES.items()):
        row = '0\t%s\t%s' % (race, d)
        if race in have:
            ls[have[race]] = row
        else:
            rows.append(row)
    tail = ls[-1] == ''
    if tail: ls.pop()
    # alias lines go before the vnum lines that use them (the exe reads the file top-down)
    first = next(i for i, l in enumerate(ls) if l.split('\t')[0].strip().isdigit() and l.split('\t')[0].strip() != '0')
    ls[first:first] = rows
    if tail: ls.append('')
    return _join(ls)
def localeinfo(b):
    t = b.decode('utf-8')
    anchor = '\t# %s (client): Arezzo maps 360/362/363 on the minimap\r\n' % MARK
    assert t.count(anchor) == 1, 'localeinfo: phase-1 block'
    i = t.index(anchor) + len(anchor)
    j = t.index('}', i)
    block = t[i:j]; add = ''
    for mid, m in sorted(ALLOC['maps'].items()):
        line = '\t"%s" : "%s",\r\n' % (m['name'], _esc(m['pl']))
        if ('"%s" :' % m['name']) not in block: add += line
    return (t[:j] + add + t[j:]).encode('utf-8')
