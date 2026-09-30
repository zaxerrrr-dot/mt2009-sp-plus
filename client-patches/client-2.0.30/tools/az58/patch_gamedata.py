# -*- coding: utf-8 -*-
# Idempotent patches of the CURRENT client text/proto files (MT2009 client 2.0.30, Arezzo phase 1),
# all from data/allocation.json. Each function: bytes in -> bytes out; a second run changes nothing.
import struct, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
ALLOC = json.load(open('/opt/metin2/cache/arezzo-work/data/allocation.json'))
MARK = 'MT2009_PLUS_AREZZO_V1'
# client mob_proto (256 B, checked on 3101/3190/2092/20394/8009 against world.mob_proto):
MOB_OFF = {'rank': (55, 'B'), 'level': (57, 'B'), 'gold_min': (59, 'I'), 'gold_max': (63, 'I'), 'exp': (67, 'I'),
           'max_hp': (71, 'I'), 'regen_cycle': (75, 'B'), 'regen_percent': (76, 'B'), 'def': (77, 'H'),
           'ai_flag': (79, 'I'), 'st': (91, 'B'), 'dx': (92, 'B'), 'ht': (93, 'B'), 'iq': (94, 'B'),
           'damage_min': (95, 'I'), 'damage_max': (99, 'I'), 'attack_speed': (103, 'h'), 'move_speed': (105, 'h'),
           'aggressive_hp_pct': (107, 'B'), 'aggressive_sight': (108, 'H'), 'attack_range': (110, 'H')}
AI = ['AGGR', 'NOMOVE', 'COWARD', 'NOATTSHINSU', 'NOATTCHUNJO', 'NOATTJINNO', 'ATTMOB', 'BERSERK', 'STONESKIN', 'GODSPEED',
      'DEATHBLOW', 'REVIVE', 'IGNORE_LAST_ATTACK', 'NO_WANDER', 'SEE_OTHER_NPC', 'RETURN_LASTATTACK_POS', 'LOOSE_AGGRO_ON_DISTANCE']
def ai_mask(s): return sum(1 << AI.index(x.strip()) for x in s.split(',') if x.strip())
def setstr(rec, off, size, s):
    b = s.encode('cp1250'); assert len(b) < size, s
    return rec[:off] + b + b'\0' * (size - len(b)) + rec[off + size:]

def mob_rows(recs):
    """recs: list of 256-byte records -> new list (sorted by vnum) with the allocation's mobs"""
    byv = {struct.unpack_from('<I', r, 0)[0]: r for r in recs}
    for m in ALLOC['mobs']:
        r = bytearray(byv[m['src']]); struct.pack_into('<I', r, 0, m['vnum'])
        r = bytearray(setstr(bytes(r), 29, 25, m['name']))
        for k, (o, f) in MOB_OFF.items():
            if k in m:
                v = ai_mask(m[k]) if k == 'ai_flag' else m[k]
                struct.pack_into('<' + f, r, o, int(v))
        for k, mul in m.get('scale', {}).items():
            o, f = MOB_OFF[k]; v = struct.unpack_from('<' + f, r, o)[0]
            struct.pack_into('<' + f, r, o, int(round(v * mul)))
        byv[m['vnum']] = bytes(r)
    return [byv[v] for v in sorted(byv)]
def item_rows(recs):
    byv = {struct.unpack_from('<I', r, 0)[0]: r for r in recs}
    for it in ALLOC['items']:
        r = struct.pack('<II', it['vnum'], 0) + byv[it['src']][8:]
        r = setstr(r, 8, 33, it['name']); r = setstr(r, 41, 33, it['name'])
        byv[it['vnum']] = r
    return [byv[v] for v in sorted(byv)]

def _lines(b): return b.decode('cp1250').split('\r\n')
def _join(ls): return '\r\n'.join(ls).encode('cp1250')
def _append(b, rows, key):
    """add rows whose key (first tab field) is missing; keep a final CRLF"""
    ls = _lines(b); have = set(l.split('\t')[0].strip() for l in ls)
    tail = ls[-1] == ''
    if tail: ls.pop()
    for r in rows:
        if key(r) not in have: ls.append(r); have.add(key(r))
    if tail: ls.append('')
    return _join(ls)
def atlasinfo(b):
    rows = ['%s\t%d\t%d\t%d\t%d' % (m['name'], m['base'][0], m['base'][1], m['size'][0], m['size'][1]) for m in ALLOC['maps'].values()]
    return _append(b, rows, lambda r: r.split('\t')[0])
def npclist(b):
    """vnum<TAB>folder for every allocation mob; an existing line of such a vnum is rewritten (the client's
    npclist lists official GF NPCs the server never spawns, e.g. 20430 "ten")"""
    want = dict((str(m['vnum']), '%d\t%s' % (m['vnum'], (m.get('client_folder') or m['folder']))) for m in ALLOC['mobs'])
    ls = _lines(b); seen = set(); out = []
    for l in ls:
        k = l.split('\t')[0].strip()
        if k in want:
            if k in seen: continue
            seen.add(k); out.append(want[k]); continue
        out.append(l)
    return _append(_join(out), [want[k] for k in want], lambda r: r.split('\t')[0])
ICON = {30765: 'icon/item/30327.tga', 30773: 'icon/item/50270.tga'}   # 30329.tga is not in our icon pack
def item_list(b):
    rows = []
    for it in ALLOC['items']:
        if it['src'] in (50270, 50271): rows.append('%d\tETC\t%s\td:/ymir work/item/etc/boss_box.gr2' % (it['vnum'], ICON[it['vnum']]))
        else: rows.append('%d\tETC\t%s' % (it['vnum'], ICON[it['vnum']]))
    return _append(b, rows, lambda r: r.split('\t')[0])
def itemdesc(b):
    rows = ['%d\t%s\t%s' % (it['vnum'], it['name'], it['desc']) for it in ALLOC['items']]
    return _append(b, rows, lambda r: r.split('\t')[0])
def _esc(s):
    return ''.join(ch if ord(ch) < 128 else '\\x%02x' % ch.encode('cp1250')[0] for ch in s)
def localeinfo(b):
    t = b.decode('utf-8')
    if MARK in t: return b
    anchor = '\t"metin2_map_n_snow_dungeon_01" : "Lodowa Kraina",\r\n'
    assert t.count(anchor) == 1, 'localeinfo anchor'
    add = '\t# %s (client): Arezzo maps 360/362/363 on the minimap\r\n' % MARK
    for m in ALLOC['maps'].values(): add += '\t"%s" : "%s",\r\n' % (m['name'], _esc(m['pl']))
    return t.replace(anchor, anchor + add).encode('utf-8')
