# -*- coding: utf-8 -*-
# MT2009_PLUS_SHIP_DEFENSE_V1 (client data) - Obrona Statku (Hydra) items the client did not have (13 October 2026):
#
#   31107  Deska Naprawcza        quest item (18), stack 200, ANTI_MYSHOP|ANTI_SAFEBOX, LIMIT_REAL_TIME 300 s
#   54705  Skrzynia Hydry         giftbox (23), ANTI_STACK - opens 3 times (chest_uses)
#   72058  Pakiet Kamieni Duszy   giftbox (23), stack 200 - one spirit stone as a Metin's
#
# The rows = linux-port/docker/mariadb/playerbot/shipdefense.sql (world.item_proto) - keep them equal. Each record
# is a copy of the Zelazna Szkatulka's (50120, a giftbox) with every server column written over it and the rest
# (prices, applies, sockets) cleared. Icons: GF 26.1.11 icon/item/31107.tga and 54705.tga, new entries of the root
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
# Without an out dir the files are rewritten in place. Then the next client's dbdata base for the panel's
# database editor: python3 -m m2clientpack.make_base <client>/pack <version> (linux-port/docker/seban-panel) -
# the panel builds its dbdata zips from the newest base, so until then they lack these three items.
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
)
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
        results.append((list_path, base.set_rows(f.read(), [u'%d\tETC\t%s' % (i[0], i[10]) for i in ITEMS])))
    with open(desc_path, 'rb') as f:
        rows = [u'%d\t%s\t%s' % (i[0], i[2], i[11]) for i in ITEMS] + [u'%d\t%s\t%s' % d for d in DESC_ONLY]
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
