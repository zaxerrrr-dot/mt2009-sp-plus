# -*- coding: utf-8 -*-
# MT2009_PLUS_ZODIAC_V1 - Swiatynia Zodiaku (map 358, metin2_12zi_stage) in the client's data, from
# zodiak_client.json (the client part of the package nowy-system 0.35.0, "Autor: Digi Rasta", dane/zodiak.json;
# the same rows the server's 96_zodiak.sql writes). APPEND ONLY: a record or a line our client already has is never
# changed - a key that exists with other content is a collision and stops the run before anything is written.
#
#   item_proto    166 records (the Zodiac weapons/armours +0..+9, Insygnia 33001-33024, Pryzmaty 33025/33032,
#                 Skarby 33026-33028, Pudla 33029/33030, Kwiat 33031, Zlota Skrzynia 33033, 72327-72329), each on
#                 the record of the first item of the same type/subtype (the package's rekord_klienta offsets);
#                 Korony 45314-45317 are ours already (left alone);
#   mob_proto     201 records (2600-2937, NPC 20438-20464) on 101 (monsters, stones) or 9012 (NPC) (the package's
#                 rekord_moba offsets); the element bits 11-16 of the race flag as tools/zywioly/zywioly_moby.json
#                 (the server's zywioly_moby.sql takes them off every mob it does not list), RACE_FLAG_CZ kept;
#   item_list.txt / itemdesc.txt   the rows of the new vnums (300-309, 1180-1189, 3220-3229 have our rows already:
#                 the same model, our icon icon/item/0xxxx.tga - kept);
#   npclist.txt   the race aliases ("0 <race> <dir>") before the first vnum line, the vnum lines at the end;
#   atlasinfo.txt "metin2_12zi_stage 307200 1408000 6 6";
#   locale_game.txt (38) / locale_interface.txt (1)   the strings of ui12zi.py, uitarget.py, uiinventory.py,
#                 uiaffectbar.py, game.py (cp1250).
# Idempotent: a second run changes nothing.
#
# Packs: item_proto, itemdesc.txt - "dbdata" (gamedata/item_proto, locale/pl/itemdesc.txt); item_list.txt, mob_proto,
# npclist.txt, atlasinfo.txt - "gamedata" (gamedata/...); locale_game.txt, locale_interface.txt - "locale"
# (locale/pl/...). Run on plain copies, in the m2pack-lzo image (MCOZ):
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/zodiak/patch_zodiak_client.py \
#     <item_proto> <item_list.txt> <itemdesc.txt> <mob_proto> [<out dir>] \
#     [--npclist <f>] [--atlasinfo <f>] [--locale-game <f>] [--locale-interface <f>] [--check]
# Any positional file may be "-". --check: report only (collisions, counts), write nothing.
# build_zodiak_packs.py calls the same functions on the gamedata/dbdata/locale packs.
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
DATA = json.load(open(os.path.join(HERE, 'zodiak_client.json'), encoding='utf-8'))
MARK = 'MT2009_PLUS_ZODIAC_V1'

ITEM_KEY = (173217, 72619434, 408587239, 27973291)
ITEM_RECORD = 184
MOB_KEY = (4813894, 18955, 552631, 6822045)
MOB_RECORD = 256
ELEMENT_OFF, ELEMENT_MASK = 83, 0x1F800
_ZYW = os.path.join(HERE, '..', '..', '..', '..', 'tools', 'zywioly', 'zywioly_moby.json')
ELEMENTS = json.load(open(_ZYW)) if os.path.exists(_ZYW) else {}
MOB_SIZE = {'': 0, 'NONE': 0, 'SMALL': 1, 'MEDIUM': 2, 'BIG': 3}
EXISTING = set(DATA['istnieja'])
NEW_ITEMS = [w for w in DATA['przedmioty'] if w['vnum'] not in EXISTING]
NEW_ITEM_VNUMS = set(w['vnum'] for w in NEW_ITEMS)
NEW_MOB_VNUMS = set(m['vnum'] for m in DATA['moby'])


class Collision(Exception):
    pass


def fixed(text, size):
    b = text.encode('cp1250')
    assert len(b) < size, text
    return b + b'\0' * (size - len(b))


STD_APPLY = {7: 17, 1: 6, 37: 77, 74: 124}


def item_record(w, tmpl):
    r = bytearray(tmpl)
    struct.pack_into('<II', r, 0, w['vnum'], 0)
    r[8:41] = fixed(w['name'], 33)
    r[41:74] = fixed(w['locale_name'], 33)
    struct.pack_into('<BBBB', r, 74, w['type'], w['subtype'], w['weight'], w['size'])
    struct.pack_into('<IIII', r, 78, w['stack'], w['antiflag'], w['flag'], w['wearflag'])
    struct.pack_into('<qq', r, 98, w['gold'], w['shop_buy_price'])
    struct.pack_into('<BiBi', r, 114, w['limittype0'], w['limitvalue0'], w['limittype1'], w['limitvalue1'])
    # MT2009_PLUS_ZODIAC_WEAPON_BONUS_V1: the package's standard APPLY numbers -> our POINT numbers, as zodiak.sql
    # gives the server (7 attack speed -> 17, 1 max HP -> 6, 37 magic resistance -> 77, 74 average damage
    # resistance -> 124); the weapons' average/skill damage is addon_type, not in the client's record
    if w['type'] in (1, 2) and (w['applytype0'], w['applytype1'], w['applytype2']) in ((7, 0, 0), (74, 37, 1)):
        w = dict(w, **dict(('applytype%d' % j, STD_APPLY.get(w['applytype%d' % j], w['applytype%d' % j]))
                           for j in range(3)))
    struct.pack_into('<BiBiBi', r, 124, w['applytype0'], w['applyvalue0'], w['applytype1'], w['applyvalue1'],
                     w['applytype2'], w['applyvalue2'])
    struct.pack_into('<6i', r, 139, *(w['value%d' % j] for j in range(6)))
    struct.pack_into('<IHBBB', r, 175, w['refined_vnum'], w['refine_set'], w['magic_pct'], w['specular'], w['socket_pct'])
    return bytes(r)


def mob_record(w, tmpl):
    r = bytearray(tmpl)
    struct.pack_into('<I', r, 0, w['vnum'])
    r[4:29] = fixed(w['name'][:24], 25)
    r[29:54] = fixed(w['locale_name'], 25)
    struct.pack_into('<5B', r, 54, w['type'], w['rank'], w['battle_type'], w['level'], MOB_SIZE.get(w['size'], 0))
    struct.pack_into('<4I', r, 59, w['gold_min'], w['gold_max'], w['exp'], w['max_hp'])
    struct.pack_into('<BBH', r, 75, w['regen_cycle'], w['regen_percent'], w['def'])
    race = (w['rasa_bity'] & ~ELEMENT_MASK) | ELEMENTS.get(str(w['vnum']), 0)
    struct.pack_into('<3I', r, 79, w['ai_bity'], race, w['odpornosc_bity'])
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


def _add_records(recs, want, what):
    """append-only: a vnum already there must hold exactly our record (a second run), else it is a collision"""
    changed = 0
    clash = []
    for v, r in sorted(want.items()):
        if v in recs:
            if recs[v] != r:
                clash.append(v)
            continue
        recs[v] = r
        changed += 1
    if clash:
        raise Collision('%s: %d vnum(s) already in the client with other content: %s' % (what, len(clash), clash[:20]))
    return changed


def item_proto(b):
    import m2pack
    assert b[:4] == b'MIPX'
    ver, stride, cnt, size = struct.unpack_from('<IIII', b, 4)
    assert stride == ITEM_RECORD, stride
    raw = m2pack.mcoz_decode(b[20:], ITEM_KEY)
    recs = dict((struct.unpack_from('<I', raw, i * ITEM_RECORD)[0], raw[i * ITEM_RECORD:(i + 1) * ITEM_RECORD]) for i in range(cnt))
    tmpl = {}
    for v in sorted(recs):
        if v not in NEW_ITEM_VNUMS:
            tmpl.setdefault((recs[v][74], recs[v][75]), v)
    want = {}
    for w in NEW_ITEMS:
        t = tmpl.get((w['type'], w['subtype'])) or tmpl.get((w['type'], 0))
        if t is None:
            raise SystemExit('item_proto: no template of type %d/%d for %d' % (w['type'], w['subtype'], w['vnum']))
        want[w['vnum']] = item_record(w, recs[t])
    changed = _add_records(recs, want, 'item_proto')
    if not changed:
        return b, 0
    out = b''.join(recs[v] for v in sorted(recs))
    blob = m2pack.mcoz_encode(out, ITEM_KEY)
    return b'MIPX' + struct.pack('<IIII', ver, stride, len(recs), len(blob)) + blob, changed


def mob_proto(b):
    import m2pack
    magic, cnt, esize = struct.unpack_from('<4sII', b, 0)
    assert magic == b'MMPT', magic
    raw = m2pack.mcoz_decode(b[12:12 + esize], MOB_KEY)
    assert len(raw) == cnt * MOB_RECORD, (len(raw), cnt)
    recs = dict((struct.unpack_from('<I', raw, i * MOB_RECORD)[0], raw[i * MOB_RECORD:(i + 1) * MOB_RECORD]) for i in range(cnt))
    want = dict((m['vnum'], mob_record(m, recs[9012] if m['type'] not in (0, 2) else recs[101])) for m in DATA['moby'])
    changed = _add_records(recs, want, 'mob_proto')
    if not changed:
        return b, 0
    out = b''.join(recs[v] for v in sorted(recs))
    blob = m2pack.mcoz_encode(out, MOB_KEY)
    return struct.pack('<4sII', b'MMPT', len(recs), len(blob)) + blob, changed


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


def _key(l):
    return l.split('\t')[0].strip()


def add_rows(b, rows, what, key=_key, same=lambda a, b: a == b):
    """append the rows whose key is missing; a key that is there with another line is a collision"""
    lines, nl, tail = _split(b)
    have = {}
    for l in lines:
        have.setdefault(key(l), l)
    clash = [key(r) for r in rows if key(r) in have and not same(have[key(r)], r)]
    if clash:
        raise Collision('%s: %d key(s) already there with other content: %s' % (what, len(clash), clash[:20]))
    new = [r for r in rows if key(r) not in have]
    return _join(lines + new, nl, tail), len(new)


def _desc_same(a, b):
    # an existing description of the same item name is fine (only the name column is checked)
    return a.split('\t')[:2] == b.split('\t')[:2]


def _list_same(a, b):
    # 300-309, 1180-1189, 3220-3229 are in our item_list already (dead vnums of the old client: the same type and
    # model, the icon icon/item/0xxxx.tga our icon pack has) - ours stays; only another type or model is a collision
    pa, pb = [x.strip().lower() for x in a.split('\t')], [x.strip().lower() for x in b.split('\t')]
    return pa[1:2] == pb[1:2] and (pa + [''] * 4)[3] == (pb + [''] * 4)[3]


# MT2009_PLUS_ZODIAC_WEAPON_MODELS_V1 (the owner, 9 October: wrong icons and models of Ostrze, Glewia, Sztylet and
# Miecz Zodiaku): the old client's own files of these names are other weapons, so the rows of these vnums point at
# GF's icons (icon/item/300.tga, 1180.tga, 3220.tga) and at the models staged under new names (stage_zodiak.py);
# our old rows of 300-309, 1180-1189, 3220-3229 are replaced.
MODEL_RENAME = {'d:/ymir work/item/weapon/00300.gr2': 'd:/ymir work/item/weapon/zodiak_00300.gr2',
                'd:/ymir work/item/weapon/01180.gr2': 'd:/ymir work/item/weapon/zodiak_01180.gr2',
                'd:/ymir work/item/weapon/03220.gr2': 'd:/ymir work/item/weapon/zodiak_03220.gr2'}


def _renamed(row):
    p = row.split('\t')
    if len(p) > 3 and p[3].strip().lower() in MODEL_RENAME:
        p[3] = MODEL_RENAME[p[3].strip().lower()]
        return '\t'.join(p)
    return None


def item_list(b):
    rows = [DATA['item_list'][str(v)] for v in sorted(NEW_ITEM_VNUMS) if str(v) in DATA['item_list']]
    fixed = dict((_key(r), _renamed(r)) for r in rows if _renamed(r))
    lines, nl, tail = _split(b)
    lines = [fixed.pop(_key(l)) if _key(l) in fixed else l for l in lines]
    b2 = _join(lines, nl, tail)
    rows = [_renamed(r) or r for r in rows]
    return add_rows(b2, rows, 'item_list.txt', same=_list_same)


def itemdesc(b):
    return add_rows(b, [DATA['itemdesc'][str(v)] for v in sorted(NEW_ITEM_VNUMS) if str(v) in DATA['itemdesc']],
                    'itemdesc.txt', same=_desc_same)


def _npc_key(l):
    p = l.split('\t')
    v = p[0].strip()
    return ('0', p[1].strip().lower()) if v == '0' and len(p) > 1 else (v, '')


def npclist(b):
    lines, nl, tail = _split(b)
    have = {}
    for l in lines:
        have.setdefault(_npc_key(l), l)
    rows = DATA['npclist']
    clash = [r for r in rows if _npc_key(r) in have and have[_npc_key(r)].split('\t') != r.split('\t')]
    # an alias line of another folder for the same race is a collision; a vnum line too
    if clash:
        raise Collision('npclist.txt: %d line(s) already there with other content: %s' % (len(clash), clash[:10]))
    alias = [r for r in rows if r.split('\t')[0] == '0' and _npc_key(r) not in have]
    vnums = [r for r in rows if r.split('\t')[0] != '0' and _npc_key(r) not in have]
    if alias:
        first = next(i for i, l in enumerate(lines) if _key(l).isdigit() and _key(l) != '0')
        lines[first:first] = alias
    return _join(lines + vnums, nl, tail), len(alias) + len(vnums)


def atlasinfo(b):
    return add_rows(b, DATA['atlas'], 'atlasinfo.txt')


def locale_game(b):
    return add_rows(b, list(DATA['napisy'].get('locale_game.txt', {}).values()), 'locale_game.txt')


def locale_interface(b):
    return add_rows(b, list(DATA['napisy'].get('locale_interface.txt', {}).values()), 'locale_interface.txt')


def main():
    args = sys.argv[1:]
    check = '--check' in args
    if check:
        args.remove('--check')
    extra = {}
    for opt in ('--npclist', '--atlasinfo', '--locale-game', '--locale-interface'):
        if opt in args:
            i = args.index(opt)
            extra[opt] = args[i + 1]
            del args[i:i + 2]
    if len(args) not in (4, 5):
        raise SystemExit('usage: patch_zodiak_client.py <item_proto> <item_list.txt> <itemdesc.txt> <mob_proto> [<out dir>]'
                         ' [--npclist <f>] [--atlasinfo <f>] [--locale-game <f>] [--locale-interface <f>] [--check]')
    out_dir = args[4] if len(args) == 5 else None
    jobs = [(args[0], item_proto), (args[1], item_list), (args[2], itemdesc), (args[3], mob_proto)]
    for opt, fn in (('--npclist', npclist), ('--atlasinfo', atlasinfo), ('--locale-game', locale_game),
                    ('--locale-interface', locale_interface)):
        if opt in extra:
            jobs.append((extra[opt], fn))
    results = []
    for path, fn in jobs:          # everything first: a collision anywhere writes nothing
        if path == '-':
            continue
        with open(path, 'rb') as f:
            results.append((path,) + fn(f.read()))
    for path, data, changed in results:
        target = os.path.join(out_dir, os.path.basename(path)) if out_dir else path
        if not check and (out_dir or changed):
            if out_dir and not os.path.isdir(out_dir):
                os.makedirs(out_dir)
            with open(target, 'wb') as f:
                f.write(data)
        print('%s: %d added%s%s' % (os.path.basename(path), changed, ' (check)' if check else '',
                                    '' if check or target == path else ' -> ' + target))


if __name__ == '__main__':
    try:
        main()
    except Collision as e:
        raise SystemExit('ZODIAK COLLISION - nothing written: %s' % e)
