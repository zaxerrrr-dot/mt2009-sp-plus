#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MT2009_PLUS_GLOBAL_PROTO_V1 - the fixed item bonuses (item_proto applytype0..2 / applyvalue0..2) of
M2_BONUS_MODE=global (the owner's list of 15 October 2026, item 19: "Bambusowe Buty+9 - u nas szybkosc ruchu +25% i
maks. wytrzymalosc +800, na globalu ruch 15 i odpornosc na ogien 10"; in global mode the items that give element
resistances etc. on the global server - boots, helmets, shields, jewellery... - have the global fixed bonuses, the
mt2009 mode stays as it is).

Source of the global values: Owsap's official item_proto (Server/Server/db/item_proto.txt = the GF data; the same
source as the dragon soul table and the monsters' elements of global mode). Every vnum both item_protos have is
compared; an item takes the global applies only when it is the SAME item - the owner (20 October 2026): "tak,
wszystko jak global" (everything the global data gives as a fixed bonus):
  * armour, weapons, soul stones, pets, costumes and mounts, unique items: the same type (and subtype), the same
    level limit, the same refine step (+N) in the name (or the same Korean name);
  * potions and grilled fish (our type 36, the effect in the applies) against the global USE_ABILITY_UP (the effect
    in value0 = APPLY_* number, value2 = amount): the same duration (value1 = our value0);
  * every global apply maps by NAME onto our POINT_* numbers (item_proto's applytype is a POINT_* number here,
    playerbot_engine_compat.h); APPLY_RANDOM (a random bonus made on the item) and APPLY_MOUNT (a mount's race) are
    no fixed bonuses and are left out; another name this engine has not got skips the item;
  * at most three applies, at least one (an item the global data gives none - its effect lives elsewhere, or a
    vnum that is no item there - keeps ours);
  * NOT: the Wolfman (Lykan) items (claws, Lycan stones, Lycan hairstyles - no Wolfman here, the owner 20 October),
    the sashes (our sashes keep their absorption in value0/sockets), our reworks (another level limit - listed
    in the report as "rework", not changed).
Only the six apply columns change; names, limits, values, sockets stay ours.

Output:
  linux-port/docker/mariadb/playerbot/item_proto_global.sql  world.item_proto_apply_global (the global applies and
                                                            the guard columns: type, subtype, limitvalue0); apply.sh
                                                            switches world.item_proto with it every start
  tools/protoglobal/item_proto_global.json                  {vnum: {glob: [[type, value] x 3], mt2009: ...}} for
                                                            the client build
                                                            (client-patches/client-2.0.30/tools/protoglobal)
  --report FILE                                             every differing vnum and the verdict (TSV)
Usage (ours.tsv = the world's item_proto, e.g. of the test server):
  docker exec -i mt2009plustest-db sh -c 'mariadb -uroot -p"$MARIADB_ROOT_PASSWORD" -N -B -e "SELECT vnum,
      HEX(name), locale_name, type, subtype, limittype0, limitvalue0, limittype1, limitvalue1, applytype0,
      applyvalue0, applytype1, applyvalue1, applytype2, applyvalue2 FROM world.item_proto ORDER BY vnum"' > ours.tsv
  python3 tools/protoglobal/gen_item_proto_global.py --ours ours.tsv [--report FILE]
The vnums are the world's of the generation; apply.sh's guard (type, subtype, level) keeps a vnum that became
another item out.
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
PB = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot')
SQL_OUT = os.path.join(PB, 'item_proto_global.sql')
JSON_OUT = os.path.join(HERE, 'item_proto_global.json')
LENGTH_H = os.path.join(REPO, 'linux-port', 'docker', 'game', 'src', 'server', 'common', 'length.h')
LENGTH_H_TEST = '/opt/metin2/mt2009plustest/linux-port/docker/game/src/server/common/length.h'
OWSAP = '/opt/metin2/cache/owsap/Server/Server/db'

TYPES = ['ITEM_NONE', 'ITEM_WEAPON', 'ITEM_ARMOR', 'ITEM_USE', 'ITEM_AUTOUSE', 'ITEM_MATERIAL', 'ITEM_SPECIAL',
         'ITEM_TOOL', 'ITEM_LOTTERY', 'ITEM_ELK', 'ITEM_METIN', 'ITEM_CONTAINER', 'ITEM_FISH', 'ITEM_ROD',
         'ITEM_RESOURCE', 'ITEM_CAMPFIRE', 'ITEM_UNIQUE', 'ITEM_SKILLBOOK', 'ITEM_QUEST', 'ITEM_POLYMORPH',
         'ITEM_TREASURE_BOX', 'ITEM_TREASURE_KEY', 'ITEM_SKILLFORGET', 'ITEM_GIFTBOX', 'ITEM_PICK', 'ITEM_HAIR',
         'ITEM_TOTEM', 'ITEM_BLEND', 'ITEM_COSTUME', 'ITEM_DS', 'ITEM_SPECIAL_DS', 'ITEM_EXTRACT',
         'ITEM_SECONDARY_COIN', 'ITEM_RING', 'ITEM_BELT', 'ITEM_HERB_KNIFE', 'ITEM_POTION', 'ITEM_PET']
CATEGORY = {'ITEM_ARMOR': 'armour', 'ITEM_WEAPON': 'weapon', 'ITEM_METIN': 'stone', 'ITEM_PET': 'pet',
            'ITEM_COSTUME': 'costume', 'ITEM_UNIQUE': 'unique', 'ITEM_POTION': 'food', 'ITEM_BELT': 'belt'}
OWSAP_LENGTH_H = '/opt/metin2/cache/owsap/Srcs/Srcs/Server/common/length.h'
SUBTYPES = {
    'ITEM_ARMOR': ['ARMOR_BODY', 'ARMOR_HEAD', 'ARMOR_SHIELD', 'ARMOR_WRIST', 'ARMOR_FOOTS', 'ARMOR_NECK', 'ARMOR_EAR',
                   'ARMOR_PENDANT', 'ARMOR_GLOVE'],
    'ITEM_WEAPON': ['WEAPON_SWORD', 'WEAPON_DAGGER', 'WEAPON_BOW', 'WEAPON_TWO_HANDED', 'WEAPON_BELL', 'WEAPON_FAN',
                    'WEAPON_ARROW', 'WEAPON_MOUNT_SPEAR', 'WEAPON_CLAW', 'WEAPON_QUIVER'],
    'ITEM_COSTUME': ['COSTUME_BODY', 'COSTUME_HAIR', 'COSTUME_MOUNT', 'COSTUME_ACCE', 'COSTUME_WEAPON', 'COSTUME_AURA'],
}
LIMITS = ['LIMIT_NONE', 'LIMIT_LEVEL', 'LIMIT_STR', 'LIMIT_DEX', 'LIMIT_INT', 'LIMIT_CON', 'LIMIT_PCBANG',
          'LIMIT_REAL_TIME', 'LIMIT_REAL_TIME_START_FIRST_USE', 'LIMIT_TIMER_BASED_ON_WEAR']
# APPLY_<x> whose POINT_* has another name (playerbot_engine_compat.h)
ALIAS = {'CON': 'HT', 'INT': 'IQ', 'STR': 'ST', 'DEX': 'DX', 'CAST_SPEED': 'CASTING_SPEED',
         'KILL_HP_RECOVER': 'KILL_HP_RECOVERY', 'ANTI_CRITICAL_PCT': 'RESIST_CRITICAL',
         'ANTI_PENETRATE_PCT': 'RESIST_PENETRATE', 'MAGIC_ATTBONUS_PER': 'MAGIC_ATT_BONUS_PER',
         'MELEE_MAGIC_ATTBONUS_PER': 'MELEE_MAGIC_ATT_BONUS_PER'}


def point_numbers():
    path = LENGTH_H if os.path.exists(LENGTH_H) else LENGTH_H_TEST
    src = open(path, encoding='latin-1').read()
    body = src[src.index('enum EPointTypes'):]
    body = body[body.index('{') + 1:body.index('};')]
    pts, n = {}, 0
    for line in body.split('\n'):
        m = re.match(r'(POINT_\w+)\s*(=\s*(\d+))?\s*,?', line.split('//')[0].strip())
        if not m:
            continue
        if m.group(3):
            n = int(m.group(3))
        pts[m.group(1)] = n
        n += 1
    # the numbers item_proto, the client and the points packet agree on
    assert (pts['POINT_MOV_SPEED'], pts['POINT_MAX_STAMINA'], pts['POINT_RESIST_FIRE'], pts['POINT_ACCEDRAIN_RATE'],
            pts['POINT_ENCHANT_ELECT'], pts['POINT_SUNGMA_STR']) == (19, 10, 75, 177, 178, 184), path
    return pts


def owsap_apply_names():
    """Owsap's EApplyTypes: number -> APPLY_* name (a potion's value0 is one)."""
    src = open(OWSAP_LENGTH_H, 'rb').read().decode('latin-1').replace('\r', '')
    body = src[src.index('enum EApplyTypes'):]
    body = body[body.index('{') + 1:body.index('};')]
    names, n = {}, 0
    for line in body.split('\n'):
        m = re.match(r'(APPLY_\w+)\s*(=\s*(\d+))?', line.split('//')[0].strip())
        if m:
            if m.group(3):
                n = int(m.group(3))
            names[n] = m.group(1)
            n += 1
    assert names[8] == 'APPLY_MOV_SPEED' and names[63] == 'APPLY_ATTBONUS_MONSTER', 'Owsap EApplyTypes changed'
    return names


def apply_number(pts, name):
    if name == 'APPLY_NONE':
        return 0
    key = name[len('APPLY_'):]
    return pts.get('POINT_' + ALIAS.get(key, key))


def read_ours(path):
    ours = {}
    for line in open(path, encoding='utf-8', errors='replace'):
        f = line.rstrip('\n').split('\t')
        if len(f) < 15 or not f[0].isdigit():
            continue
        ours[int(f[0])] = dict(
            kname=bytes.fromhex(f[1]).rstrip(), pl=f[2], type=int(f[3]), sub=int(f[4]), lim=(int(f[5]), int(f[6])),
            app=[(int(f[9]), int(f[10])), (int(f[11]), int(f[12])), (int(f[13]), int(f[14]))],
            val=[int(x) for x in f[15:18]] + [0] * (3 - len(f[15:18])))
    return ours


def read_owsap():
    en = {}
    for line in open(os.path.join(OWSAP, 'item_names.txt'), 'rb'):
        f = line.rstrip(b'\r\n').split(b'\t')
        if len(f) >= 2 and f[0].isdigit():
            en[int(f[0])] = f[1].decode('latin-1').strip()
    rows = {}
    lines = open(os.path.join(OWSAP, 'item_proto.txt'), 'rb').read().replace(b'\r\n', b'\n').split(b'\n')
    hdr = lines[0].decode().split('\t')
    for line in lines[1:]:
        if not line.strip():
            continue
        f = line.split(b'\t')
        d = dict(zip(hdr, [x.decode('latin-1').strip() for x in f]))
        d['kname'] = f[1].rstrip()
        if '~' in d['Vnum']:
            a, b = map(int, d['Vnum'].split('~'))
            vnums = range(a, b + 1)
        else:
            vnums = [int(d['Vnum'])]
        for v in vnums:
            rows[v] = d
    return rows, en


def step(name):
    m = re.search(r'\+(\d+)\s*$', name or '')
    return m.group(1) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ours', required=True)
    ap.add_argument('--report')
    a = ap.parse_args()
    pts = point_numbers()
    pname = dict((v, k[len('POINT_'):]) for k, v in pts.items())
    ours = read_ours(a.ours)
    ows, en = read_owsap()

    def fmt(apps):
        return ' '.join('%s:%d' % (pname.get(t, t), v) for t, v in apps if t) or '-'

    owsap_apply = owsap_apply_names()
    chosen, report = {}, []
    for v in sorted(set(ours) & set(ows)):
        o, w = ours[v], ows[v]
        mine = [x for x in o['app'] if x[0]]
        otype = TYPES[o['type']] if 0 <= o['type'] < len(TYPES) else str(o['type'])
        wtype = w['Type']
        glob_, unmapped, dropped, slots = [], [], [], []
        wolfman = False
        if otype == 'ITEM_POTION' and wtype == 'ITEM_USE' and w['SubType'] == 'USE_ABILITY_UP':
            # our potions and grilled fish (type 36) carry the effect in the applies, the global ones in
            # value0 (APPLY_* number), value1 (seconds), value2 (amount)
            t = owsap_apply.get(int(w['Value0'] or 0), 'APPLY_NONE')
            if t != 'APPLY_NONE':
                n = apply_number(pts, t)
                if n is None:
                    unmapped.append(t)
                else:
                    glob_.append((n, int(w['Value2'] or 0)))
                    slots.append(0)
        else:
            for i in range(4):
                t, val = w.get('ApplyType%d' % i, 'APPLY_NONE'), int(w.get('ApplyValue%d' % i, '0') or 0)
                if t == 'APPLY_NONE':
                    continue
                if 'WOLFMAN' in t or 'CLAW' in t:
                    wolfman = True
                    continue
                if t in ('APPLY_RANDOM', 'APPLY_MOUNT'):
                    dropped.append(t)   # a random bonus made on the item / the mount's race - not a fixed bonus
                    continue
                n = apply_number(pts, t)
                if n is None:
                    unmapped.append(t)
                else:
                    glob_.append((n, val))
                    slots.append(i)   # the global slot: a mount's slot 0 (APPLY_MOUNT) stays empty as ours
        wolfman = wolfman and not glob_ and not unmapped   # a Lycan stone; a bracelet's extra Lycan line is dropped
        if not unmapped and not wolfman and sorted(mine) == sorted(glob_):
            continue
        wsub_s = w['SubType']
        subs = SUBTYPES.get(wtype)
        wsub = subs.index(wsub_s) if subs and wsub_s in subs else (int(wsub_s) if wsub_s.isdigit() else -1)
        lt = w['LimitType0'] if w['LimitType0'].startswith('LIMIT_') else 'LIMIT_' + w['LimitType0']
        wlim = (LIMITS.index(lt) if lt in LIMITS else -1, int(w['LimitValue0']))
        same_type = otype == wtype or (otype == 'ITEM_POTION' and wtype == 'ITEM_USE')
        level_diff = (o['lim'][0] == 1 or wlim[0] == 1) and wlim != o['lim']
        cat = CATEGORY.get(otype, otype)
        if wolfman or (wtype == 'ITEM_WEAPON' and wsub_s == 'WEAPON_CLAW'):
            cat, why = 'wolfman', 'skip: Wolfman (Lykan) item - no Wolfman here'
        elif wtype == 'ITEM_NONE':
            why = 'skip: not an item in the global data (ITEM_NONE)'
        elif not same_type:
            why = 'skip: another item in the global data (ours %s, global %s %s)' % (otype, wtype, wsub_s)
        elif subs and otype != 'ITEM_PET' and wsub != o['sub']:
            why = 'skip: subtype differs (ours %d, global %s)' % (o['sub'], wsub_s)
        elif otype == 'ITEM_COSTUME' and wsub_s == 'COSTUME_ACCE':
            why = 'skip: sash - our sashes keep their absorption in value0/sockets, ACCEDRAIN_RATE is no bonus here'
        elif level_diff:
            cat, why = 'rework', 'not changed: our rework - level limit differs (ours %d/%d, global %d/%d)' % (
                o['lim'] + wlim)
        elif not (o['kname'] == w['kname'] or step(o['pl']) == step(en.get(v))):
            why = 'skip: name/refine step differs'
        elif otype == 'ITEM_POTION' and int(w['Value1'] or 0) != o['val'][0]:
            why = 'skip: another potion/food (duration %d s, global %s s)' % (o['val'][0], w['Value1'])
        elif unmapped:
            why = 'skip: global apply %s not in this engine' % ','.join(sorted(set(unmapped)))
        elif not glob_:
            why = 'skip: the global item has no fixed bonus (its effect lives elsewhere) - ours kept'
        elif len(glob_) > 3:
            why = 'skip: four global applies'
        elif sorted(mine) == sorted(glob_):
            continue
        else:
            why = 'APPLIED'
            app = [(0, 0)] * 3
            for slot, x in zip(slots, glob_):
                if slot < 3:
                    app[slot] = x
            for slot, x in zip(slots, glob_):
                if slot >= 3:   # a mount's third bonus (slot 3 there; ours has three slots): the free one
                    app[app.index((0, 0))] = x
            chosen[v] = dict(type=o['type'], sub=o['sub'], lim=o['lim'][1], app=app,
                             mine=o['app'], cat=cat)
        report.append((v, o['pl'], en.get(v, ''), otype, o['sub'], '%d/%d' % o['lim'], cat, why, fmt(mine),
                       fmt(glob_) + (' +' + ','.join(unmapped + dropped) if unmapped or dropped else '')))

    with open(SQL_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('-- MT2009_PLUS_GLOBAL_PROTO_V1: the fixed item bonuses of M2_BONUS_MODE=global (made by\n'
                '-- tools/protoglobal/gen_item_proto_global.py from Owsap\'s official item_proto - do not edit by hand).\n'
                '-- %d items (the same item in both: type, subtype, level, refine step).\n'
                '-- Only the table of the global values; apply.sh switches world.item_proto with it (global: writes these\n'
                '-- applies and keeps the mt2009 ones in world.item_proto_apply_mt2009; mt2009: puts those back).\n'
                % len(chosen))
        f.write('CREATE TABLE IF NOT EXISTS world.item_proto_apply_global (vnum INT UNSIGNED NOT NULL PRIMARY KEY,\n'
                '  type TINYINT NOT NULL, subtype TINYINT NOT NULL, limitvalue0 INT NOT NULL,\n'
                '  applytype0 TINYINT UNSIGNED NOT NULL, applyvalue0 INT NOT NULL,\n'
                '  applytype1 TINYINT UNSIGNED NOT NULL, applyvalue1 INT NOT NULL,\n'
                '  applytype2 TINYINT UNSIGNED NOT NULL, applyvalue2 INT NOT NULL) ENGINE=InnoDB;\n'
                'START TRANSACTION;\nDELETE FROM world.item_proto_apply_global;\n')
        rows = ['(%d,%d,%d,%d,%s)' % (v, c['type'], c['sub'], c['lim'], ','.join('%d,%d' % x for x in c['app']))
                for v, c in sorted(chosen.items())]
        for i in range(0, len(rows), 50):
            f.write('INSERT INTO world.item_proto_apply_global VALUES\n' + ',\n'.join(rows[i:i + 50]) + ';\n')
        f.write('COMMIT;\n')
    with open(JSON_OUT, 'w', encoding='utf-8') as f:
        f.write('{\n' + ',\n'.join('"%d": %s' % (v, json.dumps(dict(glob=[list(x) for x in c['app']],
                                                                      mt2009=[list(x) for x in c['mine']]),
                                                                 sort_keys=True))
                                    for v, c in sorted(chosen.items())) + '\n}\n')
    if a.report:
        with open(a.report, 'w', encoding='utf-8') as f:
            f.write('vnum\tour_name\tglobal_name\ttype\tsubtype\tour_limit\tcategory\tverdict\tour_applies\t'
                    'global_applies\n')
            for r in report:
                f.write('\t'.join(str(x) for x in r) + '\n')
    import collections
    cats = collections.Counter(c['cat'] for c in chosen.values())
    print('differing: %d, applied: %d (%s) -> %s, %s' % (len(report), len(chosen),
          ', '.join('%s %d' % kv for kv in sorted(cats.items())), SQL_OUT, JSON_OUT))


if __name__ == '__main__':
    sys.exit(main())
