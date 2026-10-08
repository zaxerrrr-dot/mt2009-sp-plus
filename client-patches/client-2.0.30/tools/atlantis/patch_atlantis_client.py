# -*- coding: utf-8 -*-
# MT2009_PLUS_ATLANTYDA_V1 - Ruiny Atlantydy (map 158) in the client's data, from atlantis.json (the same file
# the server's rows in apply.sh are written from):
#
#   item_proto    30919 Bilet do Atlantydy, 30920 Klucz Atlantydy (copies of 30767 Pieczec Ruin's record),
#                 30921 Skrzynia Atlantydy (a copy of 30775 Skrzynia Skorpiona's) - names, stack 200, flag
#                 STACKABLE; the ticket's antiflag 90496 (not tradeable), as the server's rows;
#   item_list.txt their icons (icon/item/sum2022_*.tga, pack at_maps); the chest with boss_box.gr2 as 30775;
#   itemdesc.txt  one line each;
#   mob_proto     4550-4559, 8729-8731, 9460-9462: a copy of the record of a mob of the same kind (9697 monster,
#                 9695 boss, 9694 king, 9696 stone, 20424 NPC) with the vnum, the name, the rank, the level and the
#                 numbers of atlantis.json (offsets of az29's patch_gamedata.py, type 54 / rank 55 / level 57);
#   npclist.txt   (optional, --npclist) the races' alias lines "0 <race> plechito_summer2022/<dir>" before the
#                 first vnum line, and "<vnum> <race>";
#   atlasinfo.txt (optional, --atlasinfo) "plechito_summer2022_dungeon 3814400 2252800 3 3".
# Idempotent: a second run changes nothing. Any of the four positional files may be "-" to leave it alone.
#
# item_proto and itemdesc.txt live in the "dbdata" pack (gamedata/item_proto, locale/pl/itemdesc.txt),
# item_list.txt, mob_proto, npclist.txt and atlasinfo.txt in "gamedata" (gamedata/...). Run on plain copies,
# in the m2pack-lzo image (MCOZ):
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/atlantis/patch_atlantis_client.py \
#     <item_proto> <item_list.txt> <itemdesc.txt> <mob_proto> [<out dir>] [--npclist <f>] [--atlasinfo <f>]
# build_atlantis_packs.py calls the same functions on the gamedata/dbdata packs (npclist and atlasinfo too).
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
DATA = json.load(open(os.path.join(HERE, 'atlantis.json'), encoding='utf-8'))
MARK = 'MT2009_PLUS_ATLANTYDA_V1'

ITEM_KEY = (173217, 72619434, 408587239, 27973291)
ITEM_RECORD = 184
MOB_KEY = (4813894, 18955, 552631, 6822045)
MOB_RECORD = 256
ELEMENT_OFF, ELEMENT_MASK = 83, 0x1F800
ELEMENTS = json.load(open(os.path.join(HERE, '..', '..', '..', '..', 'tools', 'zywioly', 'zywioly_moby.json')))
ITEM_TEMPLATE = {30919: 30767, 30920: 30767, 30921: 30775}
# stack, antiflag, flag (= the server's rows in apply.sh): the ticket is bound (DROP|SELL|GIVE|PKDROP|MYSHOP)
ITEM_FLAGS = {30919: (200, 90496, 4), 30920: (200, 0, 4), 30921: (200, 0, 4)}
CHEST_MODEL = 'd:/ymir work/item/etc/boss_box.gr2'
RACE_DIR = {'plechi_summ2022_stone1a': 'plechi_summ2022_stone1', 'plechi_summ2022_stone1b': 'plechi_summ2022_stone1'}
# client mob_proto offsets (az29 patch_gamedata.py, checked on 3101/3190/2092/20394/8009; type/rank/battle/level/size
# 54-58 checked on 9697/9694/9696/20424 of client 2.0.58)
MOB_OFF = {'type': (54, 'B'), 'rank': (55, 'B'), 'level': (57, 'B'), 'gold_min': (59, 'I'), 'gold_max': (63, 'I'),
           'exp': (67, 'I'), 'hp': (71, 'I'), 'regen_cycle': (75, 'B'), 'regen_percent': (76, 'B'), 'def': (77, 'H'),
           'ai': (79, 'I'), 'st': (91, 'B'), 'dx': (92, 'B'), 'ht': (93, 'B'), 'iq': (94, 'B'), 'dmin': (95, 'I'),
           'dmax': (99, 'I'), 'attack_speed': (103, 'h'), 'move_speed': (105, 'h'), 'range': (110, 'H')}
AI = ['AGGR', 'NOMOVE', 'COWARD', 'NOATTSHINSU', 'NOATTCHUNJO', 'NOATTJINNO', 'ATTMOB', 'BERSERK', 'STONESKIN', 'GODSPEED',
      'DEATHBLOW', 'REVIVE', 'IGNORE_LAST_ATTACK', 'NO_WANDER', 'SEE_OTHER_NPC', 'RETURN_LASTATTACK_POS', 'LOOSE_AGGRO_ON_DISTANCE']


def mob_template(m):
    if m['type'] == 2:
        return 9696
    if m['type'] == 1:
        return 20424
    if m.get('rank', 0) >= 5:
        return 9694
    if m.get('rank', 0) == 4:
        return 9695
    return 9697


def fixed(text, size):
    b = text.encode('cp1250')
    assert len(b) < size, text
    return b + b'\0' * (size - len(b))


def ai_mask(s):
    return sum(1 << AI.index(x.strip()) for x in s.split(',') if x.strip())


def mob_record(tmpl, m):
    r = bytearray(tmpl)
    struct.pack_into('<I', r, 0, m['vnum'])
    r[4:29] = fixed(m['en'][:24], 25)
    r[29:54] = fixed(m['name'], 25)
    vals = {}
    for k in ('type', 'rank', 'level', 'hp', 'def', 'exp', 'st', 'dx', 'ht', 'iq', 'dmin', 'dmax', 'attack_speed', 'move_speed', 'range'):
        if k in m:
            vals[k] = m[k]
    if 'gold' in m:
        vals['gold_min'], vals['gold_max'] = m['gold']
    if 'regen' in m:
        vals['regen_cycle'], vals['regen_percent'] = m['regen']
    if 'ai' in m:
        vals['ai'] = ai_mask(m['ai'])
    if 'groups' in m:        # a stone: the groups it calls are its attack/move speed
        vals['attack_speed'], vals['move_speed'] = m['groups']
    for k, v in vals.items():
        o, f = MOB_OFF[k]
        struct.pack_into('<' + f, r, o, int(v))
    # MT2009_PLUS_ATLANTYDA_V1 (8 October): the element bits (race flag offset 83, bits 11-16) as the server's
    # zywioly_moby.sql - tools/zywioly/zywioly_moby.json, whole dungeon lightning, stones too; set here, since
    # the zywioly client patch may run before these rows exist.
    rf = struct.unpack_from('<I', r, ELEMENT_OFF)[0] & ~ELEMENT_MASK
    struct.pack_into('<I', r, ELEMENT_OFF, rf | ELEMENTS.get(str(m['vnum']), 0))
    return bytes(r)


def mob_proto(b):
    import m2pack
    magic, cnt, esize = struct.unpack_from('<4sII', b, 0)
    assert magic == b'MMPT', magic
    raw = m2pack.mcoz_decode(b[12:12 + esize], MOB_KEY)
    assert len(raw) == cnt * MOB_RECORD, (len(raw), cnt)
    recs = dict((struct.unpack_from('<I', raw, i * MOB_RECORD)[0], raw[i * MOB_RECORD:(i + 1) * MOB_RECORD]) for i in range(cnt))
    changed = 0
    for m in DATA['mobs']:
        r = mob_record(recs[mob_template(m)], m)
        if recs.get(m['vnum']) != r:
            recs[m['vnum']] = r
            changed += 1
    if not changed:
        return b, 0
    out = b''.join(recs[v] for v in sorted(recs))
    blob = m2pack.mcoz_encode(out, MOB_KEY)
    return struct.pack('<4sII', b'MMPT', len(recs), len(blob)) + blob, changed


def item_proto(b):
    import m2pack
    assert b[:4] == b'MIPX'
    ver, stride, cnt, size = struct.unpack_from('<IIII', b, 4)
    assert stride == ITEM_RECORD, stride
    raw = m2pack.mcoz_decode(b[20:], ITEM_KEY)
    recs = dict((struct.unpack_from('<I', raw, i * ITEM_RECORD)[0], raw[i * ITEM_RECORD:(i + 1) * ITEM_RECORD]) for i in range(cnt))
    changed = 0
    for it in DATA['items']:
        r = bytearray(recs[ITEM_TEMPLATE[it['vnum']]])
        struct.pack_into('<II', r, 0, it['vnum'], 0)
        r[8:41] = fixed(it['en'], 33)
        r[41:74] = fixed(it['name'], 33)
        struct.pack_into('<III', r, 78, *ITEM_FLAGS[it['vnum']])
        r = bytes(r)
        if recs.get(it['vnum']) != r:
            recs[it['vnum']] = r
            changed += 1
    if not changed:
        return b, 0
    out = b''.join(recs[v] for v in sorted(recs))
    blob = m2pack.mcoz_encode(out, ITEM_KEY)
    return b'MIPX' + struct.pack('<IIII', ver, stride, len(recs), len(blob)) + blob, changed


def _split(b):
    text = b.decode('cp1250')
    nl = '\r\n' if '\r\n' in text else '\n'
    lines = text.split(nl)
    tail = bool(lines) and lines[-1] == ''
    if tail:
        lines.pop()
    return lines, nl, tail


def _join(lines, nl, tail):
    return (nl.join(lines + ([''] if tail else []))).encode('cp1250')


def set_rows(b, rows, key=lambda l: l.split('\t')[0].strip()):
    """Every line whose key is a row's becomes that row (a second one of the key goes), the rest are appended."""
    lines, nl, tail = _split(b)
    want = dict((key(r), r) for r in rows)
    seen = set()
    out = []
    changed = 0
    for l in lines:
        k = key(l)
        if k in want:
            if k in seen:
                changed += 1
                continue
            seen.add(k)
            if l != want[k]:
                changed += 1
            out.append(want[k])
            continue
        out.append(l)
    for r in rows:
        if key(r) not in seen:
            out.append(r)
            seen.add(key(r))
            changed += 1
    return _join(out, nl, tail), changed


def item_list_rows():
    rows = []
    for it in DATA['items']:
        if it['vnum'] == 30921:
            rows.append('%d\tETC\t%s\t%s' % (it['vnum'], it['icon'], CHEST_MODEL))
        else:
            rows.append('%d\tETC\t%s' % (it['vnum'], it['icon']))
    return rows


def itemdesc_rows():
    return ['%d\t%s\t%s' % (it['vnum'], it['name'], it['desc']) for it in DATA['items']]


def npclist(b):
    """the alias lines before the first vnum line (the exe reads the file top-down), then the vnum lines"""
    lines, nl, tail = _split(b)
    aliases = {}
    for m in DATA['mobs']:
        aliases[m['race']] = 'plechito_summer2022/' + RACE_DIR.get(m['race'], m['race'])
    want_vnum = dict((str(m['vnum']), '%d\t%s' % (m['vnum'], m['race'])) for m in DATA['mobs'])
    out = []
    changed = 0
    seen_alias = set()
    seen_vnum = set()
    for l in lines:
        t = l.split('\t')
        k0 = t[0].strip()
        if k0 == '0' and len(t) >= 3 and t[1].strip().lower() in aliases:
            race = t[1].strip().lower()
            row = '0\t%s\t%s' % (race, aliases[race])
            if race in seen_alias:
                changed += 1
                continue
            seen_alias.add(race)
            changed += row != l
            out.append(row)
            continue
        if k0 in want_vnum:
            if k0 in seen_vnum:
                changed += 1
                continue
            seen_vnum.add(k0)
            changed += want_vnum[k0] != l
            out.append(want_vnum[k0])
            continue
        out.append(l)
    new_alias = ['0\t%s\t%s' % (r, d) for r, d in sorted(aliases.items()) if r not in seen_alias]
    if new_alias:
        first = next(i for i, l in enumerate(out) if l.split('\t')[0].strip().isdigit() and l.split('\t')[0].strip() != '0')
        out[first:first] = new_alias
        changed += len(new_alias)
    for v, row in sorted(want_vnum.items(), key=lambda x: int(x[0])):
        if v not in seen_vnum:
            out.append(row)
            changed += 1
    return _join(out, nl, tail), changed


def atlasinfo(b):
    m = DATA['map']
    row = '%s\t%d\t%d\t%d\t%d' % (m['folder'], m['base'][0], m['base'][1], m['size'][0], m['size'][1])
    return set_rows(b, [row])


def main():
    args = sys.argv[1:]
    extra = {}
    for opt in ('--npclist', '--atlasinfo'):
        if opt in args:
            i = args.index(opt)
            extra[opt] = args[i + 1]
            del args[i:i + 2]
    if len(args) not in (4, 5):
        raise SystemExit('usage: patch_atlantis_client.py <item_proto> <item_list.txt> <itemdesc.txt> <mob_proto> [<out dir>]'
                         ' [--npclist <f>] [--atlasinfo <f>]')
    out_dir = args[4] if len(args) == 5 else None
    jobs = [(args[0], item_proto), (args[1], lambda b: set_rows(b, item_list_rows())),
            (args[2], lambda b: set_rows(b, itemdesc_rows())), (args[3], mob_proto)]
    if '--npclist' in extra:
        jobs.append((extra['--npclist'], npclist))
    if '--atlasinfo' in extra:
        jobs.append((extra['--atlasinfo'], atlasinfo))
    for path, fn in jobs:
        if path == '-':
            continue
        with open(path, 'rb') as f:
            data, changed = fn(f.read())
        target = os.path.join(out_dir, os.path.basename(path)) if out_dir else path
        if out_dir or changed:
            if out_dir and not os.path.isdir(out_dir):
                os.makedirs(out_dir)
            with open(target, 'wb') as f:
                f.write(data)
        print('%s: %d change(s)%s' % (os.path.basename(path), changed, '' if target == path else ' -> ' + target))


if __name__ == '__main__':
    main()
