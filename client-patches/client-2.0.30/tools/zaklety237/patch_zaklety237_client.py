# -*- coding: utf-8 -*-
# MT2009_PLUS_237_ZAKLETY_LAS_V1 (client data, 2.x) - Zaklety Las (353) in the 2.x client's data. The rows of the Yohara
# branch's ../yzaklety/patch_yzaklety_client.py (MT2009_PLUS_YOHARA_ZAKLETY_V1), self-contained here: the 2.x tree has
# neither ../shipdefense nor ../yohara, so their record writers are below, and the rows come from zaklety237_client.json
# (a copy of the Yohara branch's tools/yohara_zaklety/yzaklety_client.json = yohara_zaklety.sql / yohara_items_zaklety.sql
# / yohara_zaklety_zywioly.sql - keep them equal to the server's rows):
#
#   gamedata/mob_proto      the 20 rows (the forest's monsters, bosses, Metins and guards) on the record of 101
#                           (monsters, stones) or 9012 (NPC), each with its element - race flag bits 11-16 (offset 83)
#   gamedata/atlasinfo.txt  the map's row (the official base 768000 1408000, 3x4) - and the Arezzo forest's row
#                           (natural_map, 362) out: no 2.x server hosts it any more (Zaklety Las replaces it)
#   gamedata/npclist.txt    the forest's guards 20160-20162 on the official races redguild_guard_M / _M_2 / _M_3
#   gamedata/item_list.txt, gamedata/item_proto (dbdata), locale/pl/itemdesc.txt (dbdata)
#                           the 8 items (Kamien Driad, the missions' items, Skrzynia Jotuna Thryma / Bagjanamu): a full
#                           record each over the Zelazna Szkatulka's (50120), its item_list line (the GF icons:
#                           client-2.0.30/root/icon/item) and its itemdesc line
# APPEND ONLY for mob_proto/atlasinfo/npclist (the natural_map row aside): a vnum/map already there with other content
# (the element bits aside) is a collision and stops the run. Idempotent: a second run changes nothing.
# By hand, on plain copies, in the m2pack-lzo image (MCOZ):
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/zaklety237/patch_zaklety237_client.py <file> ...   (by its name)
import io
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, os.path.join(HERE, '..', 'monstercard'))
import patch_monstercard_client as base  # noqa: E402  (item record layout, MCOZ key, the line writer)

JSON = os.path.join(HERE, 'zaklety237_client.json')
ATLAS = ['metin2_map_dawnmist_dungeon_01\t768000\t1408000\t3\t4']   # = the server's Setting.txt
ATLAS_GONE = ['natural_map']        # the Arezzo forest (362): no server hosts it
ROWS = 20
ITEMS = 8
# Przywodca Straz. Lasu: a GF row of 20412 may have come with the client's GF import - the server's row wins
REPLACE_OK = {20412}
RACE_FLAG = 83                 # the record's dwRaceFlag (= ../zywioly/patch_zywioly_client.py)
ELEMENT_MASK = 0x1F800         # bits 11-16
ITEM_TEMPLATE = 50120          # Zelazna Szkatulka, giftbox

# the mob record (= the Yohara branch's ../shipdefense/patch_shipdefense_client.py, the zodiak layout)
MOB_KEY = (4813894, 18955, 552631, 6822045)
MOB_RECORD = 256
AI = ['AGGR', 'NOMOVE', 'COWARD', 'NOATTSHINSU', 'NOATTCHUNJO', 'NOATTJINNO', 'ATTMOB', 'BERSERK', 'STONESKIN', 'GODSPEED',
      'DEATHBLOW', 'REVIVE', 'IGNORE_LAST_ATTACK', 'NO_WANDER', 'SEE_OTHER_NPC', 'RETURN_LASTATTACK_POS', 'LOOSE_AGGRO_ON_DISTANCE']
RACE = ['ANIMAL', 'UNDEAD', 'DEVIL', 'HUMAN', 'ORC', 'MILGYO', 'INSECT', 'FIRE', 'ICE', 'DESERT', 'TREE',
        'ATT_ELEC', 'ATT_FIRE', 'ATT_ICE', 'ATT_WIND', 'ATT_EARTH', 'ATT_DARK']
IMMUNE = ['STUN', 'SLOW', 'FALL', 'CURSE', 'POISON', 'TERROR', 'REFLECT']
SIZE = {'': 0, 'NONE': 0, 'SMALL': 1, 'MEDIUM': 2, 'BIG': 3}


class Collision(Exception):
    pass


def data():
    with io.open(JSON, encoding='utf-8') as f:
        return json.load(f)


def _val(v):
    if isinstance(v, str) and len(v) >= 2 and v[0] == "'" and v[-1] == "'":
        return v[1:-1].replace("\\'", "'")
    return v


def mobs():
    d = data()
    out = [dict(zip(d['cols'], [_val(v) for v in r])) for r in d['rows']]
    assert len(out) == ROWS, len(out)
    return out


def fixed(text, size):
    b = text.encode('cp1250')
    assert len(b) < size, text
    return b + b'\0' * (size - len(b))


def bits(s, names):
    return sum(1 << names.index(x.strip()) for x in s.split(',') if x.strip())


def mob_record(w, tmpl):
    r = bytearray(tmpl)
    struct.pack_into('<I', r, 0, w['vnum'])
    r[4:29] = fixed(w['name'][:24], 25)
    r[29:54] = fixed(w['locale_name'], 25)
    struct.pack_into('<5B', r, 54, w['type'], w['rank'], w['battle_type'], w['level'], SIZE[w['size']])
    struct.pack_into('<4I', r, 59, w['gold_min'], w['gold_max'], w['exp'], w['max_hp'])
    struct.pack_into('<BBH', r, 75, w['regen_cycle'], w['regen_percent'], w['def'])
    struct.pack_into('<3I', r, 79, bits(w['ai_flag'], AI), bits(w['setRaceFlag'], RACE), bits(w['setImmuneFlag'], IMMUNE))
    struct.pack_into('<4B', r, 91, w['st'], w['dx'], w['ht'], w['iq'])
    struct.pack_into('<2I', r, 95, w['damage_min'], w['damage_max'])
    struct.pack_into('<2h', r, 103, w['attack_speed'], w['move_speed'])
    struct.pack_into('<BHH', r, 107, w['aggressive_hp_pct'], w['aggressive_sight'], w['attack_range'])
    struct.pack_into('<6b', r, 112, w['enchant_curse'], w['enchant_slow'], w['enchant_poison'], w['enchant_stun'],
                     w['enchant_critical'], w['enchant_penetrate'])
    struct.pack_into('<11b', r, 118, w['resist_sword'], w['resist_twohand'], w['resist_dagger'], w['resist_bell'],
                     w['resist_fan'], w['resist_bow'], w['resist_fire'], w['resist_elect'], w['resist_magic'],
                     w['resist_wind'], w['resist_poison'])
    struct.pack_into('<2I', r, 129, w['resurrection_vnum'], w['drop_item'])
    struct.pack_into('<3B', r, 137, w['mount_capacity'], w['on_click'], w['empire'])
    r[140:204] = fixed(w['folder'], 64)
    return bytes(r)


def with_element(r, element):
    r = bytearray(r)
    old = struct.unpack_from('<I', r, RACE_FLAG)[0]
    struct.pack_into('<I', r, RACE_FLAG, (old & ~ELEMENT_MASK) | (element & ELEMENT_MASK))
    return bytes(r)


def mob_proto(b):
    import m2pack
    magic, cnt, esize = struct.unpack_from('<4sII', b, 0)
    assert magic == b'MMPT', magic
    raw = m2pack.mcoz_decode(b[12:12 + esize], MOB_KEY)
    assert len(raw) == cnt * MOB_RECORD, (len(raw), cnt)
    R = MOB_RECORD
    recs = dict((struct.unpack_from('<I', raw, i * R)[0], raw[i * R:(i + 1) * R]) for i in range(cnt))
    elem = dict((int(k), v) for k, v in data()['elements'].items())
    want = dict((w['vnum'], with_element(mob_record(w, recs[101] if w['type'] in (0, 2) else recs[9012]),
                                         elem.get(w['vnum'], 0))) for w in mobs())
    clash = [v for v, r in sorted(want.items()) if v in recs and v not in REPLACE_OK and
             with_element(recs[v], 0) != with_element(r, 0)]
    if clash:
        raise Collision('mob_proto: %d vnum(s) already in the client with other content: %s' % (len(clash), clash))
    new = dict((v, r) for v, r in want.items() if recs.get(v) != r)
    if not new:
        return b, 0
    recs.update(new)
    out = b''.join(recs[v] for v in sorted(recs))
    blob = m2pack.mcoz_encode(out, MOB_KEY)
    return struct.pack('<4sII', b'MMPT', len(recs), len(blob)) + blob, len(new)


def _append_rows(b, rows, key):
    text = b.decode('cp1250')
    nl = '\r\n' if '\r\n' in text else '\n'
    lines = text.split(nl)
    tail = bool(lines) and lines[-1] == ''
    if tail:
        lines.pop()
    have = dict((key(l), l) for l in lines if l.strip() and not l.lstrip().startswith(('#', '//')))
    new = []
    for row in rows:
        k = key(row)
        if k in have:
            if have[k].split() != row.split():
                raise Collision('%r already there as %r' % (k, have[k]))
            continue
        new.append(row)
    if not new:
        return b, 0
    return (nl.join(lines + new + ([''] if tail else []))).encode('cp1250'), len(new)


def atlasinfo(b):
    nb, n = _append_rows(b, ATLAS, lambda l: l.split('\t')[0].strip().lower())
    text = nb.decode('cp1250')
    nl = '\r\n' if '\r\n' in text else '\n'
    lines = text.split(nl)
    keep = [l for l in lines if not (l.split() and l.split()[0].lower() in ATLAS_GONE)]
    if len(keep) == len(lines):
        return nb, n
    return nl.join(keep).encode('cp1250'), n + len(lines) - len(keep)


# MT2009_PLUS_237_TREE_METIN_V1: Metin Drzewnych Stworzen (8059) and Metin Lasu (8061) are GF's race metinstone_16, but
# the 2.x base client has a monster/metinstone/metinstone_16.msm of its own in its "monster" pack, and the exe takes a
# name from the pack registered first - the base one: a grey stone with a red glow (owner's in-game test, 22 October)
# instead of the green Metin wrapped in vines. As the Yohara line's yfinal step does it: GF's metinstone_16.msm/.dds
# under a name no client has (RACE_TREE, written into zaklety_mobs by build_zaklety237_packs.py) and the two vnums'
# npclist lines pointed at it, with its race line (source folder metinstone).
RACE_TREE = 'mt2009_metin_tree'
TREE_VNUMS = (8059, 8061)
TREE_DIR = 'd:/ymir work/monster/metinstone/'


def tree_files(msm16, dds16):
    """{in-pack name: bytes} of the tree Metin's own race from GF's metinstone_16.msm / .dds."""
    msm = msm16.decode('latin-1')
    assert msm.count('"metinstone_16.dds"') == 1, 'GF metinstone_16.msm changed'
    return {TREE_DIR + RACE_TREE + '.msm': msm.replace('"metinstone_16.dds"', '"%s.dds"' % RACE_TREE).encode('latin-1'),
            TREE_DIR + RACE_TREE + '.dds': dds16}


def _tree_rows(b):
    text = b.decode('cp1250')
    nl = '\r\n' if '\r\n' in text else '\n'
    lines = text.split(nl)
    tail = bool(lines) and lines[-1] == ''
    if tail:
        lines.pop()
    want = dict(('%d' % v, '%d\t%s' % (v, RACE_TREE)) for v in TREE_VNUMS)
    changed, seen = 0, set()
    for i, l in enumerate(lines):
        t = l.split('\t')
        k = t[0].strip()
        if k in want:
            seen.add(k)
            if l != want[k]:
                lines[i] = want[k]
                changed += 1
        elif k == '0' and len(t) > 1 and t[1].strip() == RACE_TREE:
            seen.add(RACE_TREE)
    if RACE_TREE not in seen:
        last0 = max([i for i, l in enumerate(lines) if l.split('\t')[0].strip() == '0'] or [-1])
        lines.insert(last0 + 1, '0\t%s\tmetinstone' % RACE_TREE)
        changed += 1
    for k in sorted(set(want) - seen):
        lines.append(want[k])
        changed += 1
    if not changed:
        return b, 0
    return nl.join(lines + ([''] if tail else [])).encode('cp1250'), changed


def npclist(b):
    rows = ['%s\t%s' % (k, v) for k, v in sorted(data().get('npclist_add', {}).items())]
    b, n = _append_rows(b, rows, lambda l: l.split()[0] if l.split() else '')
    b, m = _tree_rows(b)
    return b, n + m


def item_record(template, w):
    r = bytearray(template)
    struct.pack_into('<II', r, 0, w['vnum'], 0)
    r[8:41] = base.fixed(w['name'], 33)
    r[41:74] = base.fixed(w['locale_name'], 33)
    struct.pack_into('<BBBB', r, 74, w['type'], w['subtype'], w['weight'], w['size'])
    struct.pack_into('<IIIII', r, 78, w['stack'], w['antiflag'], w['flag'], w['wearflag'], 0)
    struct.pack_into('<qq', r, 98, w['gold'], w['shop_buy_price'])
    struct.pack_into('<BiBi', r, 114, w['limittype0'], w['limitvalue0'], w['limittype1'], w['limitvalue1'])
    struct.pack_into('<BiBiBi', r, 124, w['applytype0'], w['applyvalue0'], w['applytype1'], w['applyvalue1'],
                     w['applytype2'], w['applyvalue2'])
    struct.pack_into('<6i', r, 139, *(w['value%d' % j] for j in range(6)))
    struct.pack_into('<3i', r, 163, 0, 0, 0)
    struct.pack_into('<IHBBB', r, 175, w['refined_vnum'], w['refine_set'], w['magic_pct'], w['specular'],
                     w['socket_pct'])
    return bytes(r)


def item_proto(b):
    import m2pack
    assert b[:4] == b'MIPX'
    ver, stride, cnt, size = struct.unpack_from('<IIII', b, 4)
    assert stride == base.RECORD, stride
    raw = m2pack.mcoz_decode(b[20:], base.ITEM_KEY)
    recs = dict((struct.unpack_from('<I', raw, i * base.RECORD)[0], raw[i * base.RECORD:(i + 1) * base.RECORD])
                for i in range(cnt))
    items = data()['items']
    assert len(items) == ITEMS, len(items)
    changed = 0
    for w in items:
        r = item_record(recs[ITEM_TEMPLATE], w)
        if recs.get(w['vnum']) != r:
            recs[w['vnum']] = r
            changed += 1
    if not changed:
        return b, 0
    out = b''.join(recs[v] for v in sorted(recs))
    blob = m2pack.mcoz_encode(out, base.ITEM_KEY)
    return b'MIPX' + struct.pack('<IIII', ver, stride, len(recs), len(blob)) + blob, changed


def item_list(b):
    d = data()
    return base.set_rows(b, [d['item_list'][k] for k in sorted(d['item_list'], key=int)])


def itemdesc(b):
    d = data()
    return base.set_rows(b, [d['itemdesc'][k] for k in sorted(d['itemdesc'], key=int)])


# in-pack name -> function
JOBS = {'gamedata/mob_proto': mob_proto, 'gamedata/atlasinfo.txt': atlasinfo, 'gamedata/npclist.txt': npclist,
        'gamedata/item_list.txt': item_list, 'gamedata/item_proto': item_proto, 'locale/pl/itemdesc.txt': itemdesc}
BY_FILE = dict((os.path.basename(k), f) for k, f in JOBS.items())


def main():
    args = [a for a in sys.argv[1:] if a != '--check']
    check = '--check' in sys.argv
    if not args:
        raise SystemExit('usage: patch_zaklety237_client.py <mob_proto|atlasinfo.txt|npclist.txt|item_list.txt|item_proto|'
                         'itemdesc.txt> ... [--check]')
    for path in args:
        fn = BY_FILE[os.path.basename(path)]
        b = open(path, 'rb').read()
        nb, n = fn(b)
        if n and not check:
            open(path, 'wb').write(nb)
        print('%s: %d new/changed%s' % (os.path.basename(path), n, ' (check only)' if check else ''))


if __name__ == '__main__':
    main()
