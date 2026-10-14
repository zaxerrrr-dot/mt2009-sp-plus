# -*- coding: utf-8 -*-
# MT2009_PLUS_CHANGE_LOOK_V1 (client data) - Transmutacja's items the client did not have (14 October 2026):
#
#   72325  Anulacja Transmutacji            ITEM_USE/USE_SPECIAL (3/10), stack 200, flag STACKABLE|APPLICABLE (dragged onto an item)
#   72326  Bilet Transmutacji               3/10, stack 200 (into the window instead of 50 mln Yang)
#   72341  Bilet Transmutacji (handlowy)    3/10, stack 200, only ANTI_DROP (tradeable); the icon of 72326 (as GF's item_list)
#   72343  Anulacja Polimorfii Wierzchowca  3/10, stack 200, STACKABLE|APPLICABLE
#   72344  Bilet Polimorfii Wierzchowca     3/10, stack 200 (into the mount window instead of 30 mln Yang)
#
# The rows = linux-port/docker/mariadb/playerbot/transmutacja.sql (world.item_proto) - keep them equal. Each record is a
# copy of the Zelazna Szkatulka's (50120) with the server columns written over it and the rest cleared (the
# tools/yohara way). Icons: GF 26.1.11 icon/item/72325.tga, 72326.tga, 72343.tga, 72344.tga - new entries of the root
# pack (client-patches/client-2.0.30/root/icon/item/, build57.py adds every file there).
# Idempotent. item_proto and itemdesc.txt are in the "dbdata" pack, item_list.txt in "gamedata"; run on plain copies:
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/transmutacja/patch_transmutacja_client.py \
#     <item_proto> <item_list.txt> <itemdesc.txt> [<out dir>]
# (in clientY.sh after tools/yohara/patch_yohara_client.py), then the next dbdata base for the panel's editor.
import os
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'monstercard'))
import patch_monstercard_client as base  # noqa: E402  (record layout, MCOZ key, the line writer)

TEMPLATE = 50120   # Zelazna Szkatulka

# vnum, name, Polish name, type, subtype, stack, antiflag, flag, (limittype0, limitvalue0), value0, icon, description
ITEMS = (
    (72325, u'Transmutation Reversal', u'Anulacja Transmutacji', 3, 10, 200, 90240, 16388, (0, 0), 0,
     u'icon/item/72325.tga', u'Przeciągnij na przedmiot z transmutacją (w ekwipunku, nie założony), aby przywrócić mu jego własny wygląd.'),
    (72326, u'Transmutation Ticket', u'Bilet Transmutacji', 3, 10, 200, 90240, 4, (0, 0), 0,
     u'icon/item/72326.tga', u'Włóż do okna transmutacji u Teowadena zamiast 50 000 000 Yang.'),
    (72341, u'Transmutation Ticket (t)', u'Bilet Transmutacji (handlowy)', 3, 10, 200, 128, 4, (0, 0), 0,
     u'icon/item/72326.tga', u'Włóż do okna transmutacji u Teowadena zamiast 50 000 000 Yang. Można nim handlować.'),
    (72343, u'Mount Transformation Reversal', u'Anulacja Polimorfii Wierzchowca', 3, 10, 200, 90240, 16388, (0, 0), 0,
     u'icon/item/72343.tga', u'Przeciągnij na wierzchowca z polimorfią (w ekwipunku), aby przywrócić mu jego własny wygląd.'),
    (72344, u'Mount Transformation Ticket', u'Bilet Polimorfii Wierzchowca', 3, 10, 200, 73856, 4, (0, 0), 0,
     u'icon/item/72344.tga', u'Włóż do okna polimorfii wierzchowca u Teowadena zamiast 30 000 000 Yang.'),
)


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
        raise SystemExit('usage: patch_transmutacja_client.py <item_proto> <item_list.txt> <itemdesc.txt> [<out dir>]')
    proto_path, list_path, desc_path = sys.argv[1:4]
    out_dir = sys.argv[4] if len(sys.argv) == 5 else None
    results = []
    with open(proto_path, 'rb') as f:
        results.append((proto_path, item_proto(f.read())))
    with open(list_path, 'rb') as f:
        results.append((list_path, base.set_rows(f.read(), [u'%d\tETC\t%s' % (i[0], i[10]) for i in ITEMS])))
    with open(desc_path, 'rb') as f:
        results.append((desc_path, base.set_rows(f.read(), [u'%d\t%s\t%s' % (i[0], i[2], i[11]) for i in ITEMS])))
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
