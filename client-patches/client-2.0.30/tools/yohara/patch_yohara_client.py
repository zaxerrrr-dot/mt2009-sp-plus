# -*- coding: utf-8 -*-
# MT2009_PLUS_SHIP_DEFENSE_V1 (client data) - Obrona Statku (Hydra) items the client did not have (13 October 2026):
#
#   31107  Deska Naprawcza        quest item (18), stack 200, ANTI_MYSHOP|ANTI_SAFEBOX, LIMIT_REAL_TIME 300 s
#   54705  Skrzynia Hydry         giftbox (23), ANTI_STACK - opens 3 times (chest_uses)
#   72058  Pakiet Kamieni Duszy   giftbox (23), stack 200 - one spirit stone as a Metin's
#   70303  Pierscien Hydry        quest item (18), level 90 - three teleports to Port Nowego Kontynentu (368, quest
#                                 port_yohary; MT2009_PLUS_YOHARA_PORT_V1, the owner 13 October evening)
#
# The rows = linux-port/docker/mariadb/playerbot/shipdefense.sql (world.item_proto) - keep them equal. Each record
# is a copy of the Zelazna Szkatulka's (50120, a giftbox) with every server column written over it and the rest
# (prices, applies, sockets) cleared. Icons: GF 26.1.11 icon/item/31107.tga, 54705.tga and 70303.tga, new entries of the root
# pack (client-patches/client-2.0.30/root/icon/item/, build57.py adds every file there); 72058 uses the official
# icon/item/27999.tga (Sakiewka Kamieni Dusz's), already in the icon pack.
#
# Idempotent: a record or line that is there is rewritten only when it differs.
# From client 2.0.52 item_proto and itemdesc.txt live in the "dbdata" pack (gamedata/item_proto,
# locale/pl/itemdesc.txt), item_list.txt in gamedata. Run on plain copies of the three files, in the m2pack-lzo
# image for the proto's MCOZ:
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/yohara/patch_yohara_client.py \
#     <item_proto> <item_list.txt> <itemdesc.txt> [<out dir>]
# Without an out dir the files are rewritten in place.
#
# MT2009_PLUS_YOHARA_ITEMS1_V1: also the 106 Yohara items of Opuszczona Twierdza / Dongan (tools/yohara_items/
# yohara_items.json - made by tools/yohara_items/gen_yitems.py with linux-port/docker/mariadb/playerbot/yohara_items.sql,
# so the client's records are the server's rows): a full record each (every server column written over a template -
# Talizman Ognia+0's 94000 for the Talizmany Woli, Zelazna Szkatulka's 50120 for the rest), its item_list line (the GF
# icons: client-patches/client-2.0.30/root/icon/item, build57.py adds every file there) and its itemdesc line.
# Also the Polish name of the items in its 'renamed' (27007/27008 "(XXL)"; the client has no itemdesc line for
# them). Then the next client's dbdata base for the panel's
# database editor: python3 -m m2clientpack.make_base <client>/pack <version> (linux-port/docker/seban-panel) -
# the panel builds its dbdata zips from the newest base, so until then they lack these three items.
import io
import json
import os
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'monstercard'))
import patch_monstercard_client as base  # noqa: E402  (record layout, MCOZ key, the line writer)

TEMPLATE = 50120   # Zelazna Szkatulka, giftbox

# vnum: (name, Polish name, type, subtype, stack, antiflag, flag, (limittype0, limitvalue0), value0, icon, description)
ITEMS = (
    (31107, u'Repair Wood', u'Deska Naprawcza', 18, 0, 200, 196608, 4, (7, 300), 20437, u'icon/item/31107.tga',
     u'Przeciągnij ją na maszt statku, aby go naprawić. Ważna 5 minut.'),
    (54705, u'Hydra Chest', u'Skrzynia Hydry', 23, 0, 200, 32768, 0, (0, 0), 0, u'icon/item/54705.tga',
     u'Skarb pokonanej Hydry. Można ją otworzyć 3 razy - za każdym razem daje jeden przedmiot.'),
    (72058, u'Soul Stone Package', u'Pakiet Kamieni Duszy', 23, 0, 200, 0, 4, (0, 0), 0, u'icon/item/27999.tga',
     u'Po otwarciu daje jeden losowy Kamień Duszy (od +0 do +4).'),
    # MT2009_PLUS_YOHARA_PORT_V1: value0 = 3 uses (quest port_yohary), level 90, ANTI_SELL|GIVE|DROP|STACK|MYSHOP|SAFEBOX
    (70303, u'Hydra Ring', u'Pierścień Hydry', 18, 0, 1, 237952, 0, (1, 90), 3, u'icon/item/70303.tga',
     u'Ten pierścień upuściła Hydra, konając. Zaprowadzi cię na nowy kontynent: 3 teleporty do Portu Nowego Kontynentu.'),
    # MT2009_PLUS_CHAMPION_V1: Nowa Wola (czempion.sql, quest czempion_nowa_wola) - quest-use items, GF icons
    (72068, u'New Will (STR)', u'Nowa Wola (Siła Sung Ma)', 18, 0, 200, 106880, 8192, (0, 0), 0, u'icon/item/72068.tga',
     u'Zwraca punkty Czempiona rozdane w Siłę Sung Ma.'),
    (72069, u'New Will (VIT)', u'Nowa Wola (Witalność Sung Ma)', 18, 0, 200, 106880, 8192, (0, 0), 0, u'icon/item/72069.tga',
     u'Zwraca punkty Czempiona rozdane w Witalność Sung Ma.'),
    (72070, u'New Will (RES)', u'Nowa Wola (Odporność Sung Ma)', 18, 0, 200, 106880, 8192, (0, 0), 0, u'icon/item/72070.tga',
     u'Zwraca punkty Czempiona rozdane w Odporność Sung Ma.'),
    (72071, u'New Will (INT)', u'Nowa Wola (Inteligencja Sung Ma)', 18, 0, 200, 106880, 8192, (0, 0), 0, u'icon/item/72071.tga',
     u'Zwraca punkty Czempiona rozdane w Inteligencję Sung Ma.'),
)
YITEMS_PATH = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'tools',
                                           'yohara_items', 'yohara_items.json'))
with io.open(YITEMS_PATH, encoding='utf-8') as _f:
    YITEMS = json.load(_f)
YITEM_TEMPLATE = {2: 94000}    # by type: Talizman Ognia+0 for the talismans, else TEMPLATE


def yitem_record(template, w):
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


# vnum: (Polish name, description) of an item the client has - only its itemdesc line is set.
# (the Magic Stone 25042 keeps its own text - the owner, 13 October; the stray refine-bonus lines under it
# were uitooltip.py's, MT2009_PLUS_REFINE_TOOLTIP_V1)
DESC_ONLY = ()


def record(template, it):
    vnum, name, pl, typ, sub, stack, anti, flag, limit, value0 = it[:10]
    r = bytearray(template)
    struct.pack_into('<II', r, 0, vnum, 0)
    r[8:41] = base.fixed(name, 33)
    r[41:74] = base.fixed(pl, 33)
    struct.pack_into('<BBBB', r, 74, typ, sub, 0, 1)                 # weight 0, size 1
    struct.pack_into('<IIIII', r, 78, stack, anti, flag, 0, 0)       # stack, antiflags, flags, wear, immune
    r[98:base.RECORD] = b'\0' * (base.RECORD - 98)                   # no price, apply, socket, refine
    struct.pack_into('<BiBi', r, 114, limit[0], limit[1], 0, 0)
    struct.pack_into('<i', r, 139, value0)
    return bytes(r)


def item_proto(b):
    import m2pack
    assert b[:4] == b'MIPX'
    ver, stride, cnt, size = struct.unpack_from('<IIII', b, 4)
    assert stride == base.RECORD, stride
    raw = m2pack.mcoz_decode(b[20:], base.ITEM_KEY)
    recs = dict((struct.unpack_from('<I', raw, i * base.RECORD)[0], raw[i * base.RECORD:(i + 1) * base.RECORD])
                for i in range(cnt))
    changed = 0
    for it in ITEMS:
        r = record(recs[TEMPLATE], it)
        if recs.get(it[0]) != r:
            recs[it[0]] = r
            changed += 1
    for w in YITEMS['items']:
        r = yitem_record(recs[YITEM_TEMPLATE.get(w['type'], TEMPLATE)], w)
        if recs.get(w['vnum']) != r:
            recs[w['vnum']] = r
            changed += 1
    # the official names of items the client has (27007/27008 "(XXL)", the owner 13 October): only the Polish name
    for k, pl in sorted(YITEMS.get('renamed', {}).items()):
        v = int(k)
        r = bytearray(recs[v])
        r[41:74] = base.fixed(pl, 33)
        if recs[v] != bytes(r):
            recs[v] = bytes(r)
            changed += 1
    if not changed:
        return b, 0
    out = b''.join(recs[v] for v in sorted(recs))
    blob = m2pack.mcoz_encode(out, base.ITEM_KEY)
    return b'MIPX' + struct.pack('<IIII', ver, stride, len(recs), len(blob)) + blob, changed


def main():
    if len(sys.argv) not in (4, 5):
        raise SystemExit('usage: patch_yohara_client.py <item_proto> <item_list.txt> <itemdesc.txt> [<out dir>]')
    proto_path, list_path, desc_path = sys.argv[1:4]
    out_dir = sys.argv[4] if len(sys.argv) == 5 else None
    results = []
    with open(proto_path, 'rb') as f:
        results.append((proto_path, item_proto(f.read())))
    with open(list_path, 'rb') as f:
        results.append((list_path, base.set_rows(f.read(), [u'%d\tETC\t%s' % (i[0], i[10]) for i in ITEMS] +
                                                 [YITEMS['item_list'][k] for k in sorted(YITEMS['item_list'], key=int)])))
    with open(desc_path, 'rb') as f:
        rows = [u'%d\t%s\t%s' % (i[0], i[2], i[11]) for i in ITEMS] + [u'%d\t%s\t%s' % d for d in DESC_ONLY] + \
            [YITEMS['itemdesc'][k] for k in sorted(YITEMS['itemdesc'], key=int)]
        results.append((desc_path, base.set_rows(f.read(), rows)))
    for path, (data, changed) in results:
        target = os.path.join(out_dir, os.path.basename(path)) if out_dir else path
        if out_dir or changed:
            if out_dir and not os.path.isdir(out_dir):
                os.makedirs(out_dir)
            with open(target, 'wb') as f:
                f.write(data)
        print('%s: %d change(s)%s' % (os.path.basename(path), changed, '' if target == path else ' -> ' + target))


if __name__ == '__main__':
    main()
