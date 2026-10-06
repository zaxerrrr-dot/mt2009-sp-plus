# -*- coding: utf-8 -*-
# MT2009_PLUS_RANK_POINTS_V1 - the rank fruits (Punkty Rangi) in the client's data: the five
# items the server's linux-port/docker/mariadb/playerbot/apply.sh adds to world.item_proto -
# keep them equal.
#
#   80050  Jablko     ITEM_USE / USE_SPECIAL, stack 200 (flag 4), antiflag 0, value0 50,  buy 25 000 / sell 1 000
#   80051  Gruszka    ITEM_USE / USE_SPECIAL, stack 200,                     value0 50,  buy 50 000 / sell 2 000
#   80052  Winogrono  ITEM_USE / USE_SPECIAL, stack 200,                     value0 100, buy 125 000 / sell 5 000
#   80053  Arbuz      ITEM_USE / USE_SPECIAL, stack 200,                     value0 100, buy 250 000 / sell 10 000
#   80054  Ananas     ITEM_USE / USE_SPECIAL, stack 200,                     value0 100, buy 500 000 / sell 20 000
#
# Arezzo's vnums, type and names (Arezzo calls 80052 "Winogron"); the icons are Arezzo's
# icon/item/fruit_2, _1, _7, _6, _5.tga (RLE in Arezzo's pack, written out uncompressed) as new
# entries of the root pack: client-patches/client-2.0.30/root/icon/item/80050-80054.tga.
# Metins and bosses drop them (server-patches/rankpoints, playerbot_rank_points.h); eaten in
# its range of points a fruit raises the character's Punkty Rangi.
#
# A new item_proto record each (a copy of 30228's with every value cleared, as tools/monstercard),
# a line in item_list.txt and a line in itemdesc.txt. Idempotent: a second run changes nothing;
# a record or line that is there is rewritten only when it differs.
#
# From client 2.0.52 item_proto and itemdesc.txt live in the "dbdata" pack (gamedata/item_proto,
# locale/pl/itemdesc.txt), item_list.txt in gamedata. Run on plain copies of the three files, in
# the m2pack-lzo image for the proto's MCOZ:
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/rankfruit/patch_rank_fruit_client.py \
#     <item_proto> <item_list.txt> <itemdesc.txt> [<out dir>]
# Without an out dir the files are rewritten in place. Then the next client's dbdata base for the
# panel's database editor: python3 -m m2clientpack.make_base <client>/pack <version>
# (linux-port/docker/seban-panel, see /opt/metin2/cache/klient-do-zbudowania.md).
import os
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'monstercard'))
import patch_monstercard_client as base  # noqa: E402  (the record layout, MCOZ and the line writer)

# (vnum, name, Polish name, points, buy, sell, description) - = apply.sh.
ITEMS = (
    (80050, u'Apple', u'Jabłko', 50, 25000, 1000,
     u'Owoc rangi: +50 Punktów Rangi. Działa od 0 do 20 000 punktów. Pierwsza ranga (Waleczny) od 21 000. Komenda /ranga.'),
    (80051, u'Pear', u'Gruszka', 50, 50000, 2000,
     u'Owoc rangi: +50 Punktów Rangi. Działa od 20 000 do 40 000 punktów. Komenda /ranga.'),
    (80052, u'Grapes', u'Winogrono', 100, 125000, 5000,
     u'Owoc rangi: +100 Punktów Rangi. Działa od 40 000 do 80 000 punktów. Komenda /ranga.'),
    (80053, u'Watermelon', u'Arbuz', 100, 250000, 10000,
     u'Owoc rangi: +100 Punktów Rangi. Działa od 80 000 do 120 000 punktów. Komenda /ranga.'),
    (80054, u'Pineapple', u'Ananas', 100, 500000, 20000,
     u'Owoc rangi: +100 Punktów Rangi. Działa od 120 000 do 200 000 punktów (maksimum). Komenda /ranga.'),
)
TYPE, SUBTYPE = 3, 10   # ITEM_USE / USE_SPECIAL, as Arezzo's


def record(template, vnum, name, pl, points, buy, sell):
    r = bytearray(base.card_record(template, vnum, name, pl, TYPE, SUBTYPE, 0))
    struct.pack_into('<qq', r, 98, buy, sell)
    struct.pack_into('<i', r, 139, points)      # value0
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
    for vnum, name, pl, points, buy, sell, _desc in ITEMS:
        r = record(recs[base.TEMPLATE], vnum, name, pl, points, buy, sell)
        if recs.get(vnum) != r:
            recs[vnum] = r
            changed += 1
    if not changed:
        return b, 0
    out = b''.join(recs[v] for v in sorted(recs))
    blob = m2pack.mcoz_encode(out, base.ITEM_KEY)
    return b'MIPX' + struct.pack('<IIII', ver, stride, len(recs), len(blob)) + blob, changed


def main():
    if len(sys.argv) not in (4, 5):
        raise SystemExit('usage: patch_rank_fruit_client.py <item_proto> <item_list.txt> <itemdesc.txt> [<out dir>]')
    proto_path, list_path, desc_path = sys.argv[1:4]
    out_dir = sys.argv[4] if len(sys.argv) == 5 else None
    results = []
    with open(proto_path, 'rb') as f:
        results.append((proto_path, item_proto(f.read())))
    with open(list_path, 'rb') as f:
        results.append((list_path, base.set_rows(f.read(), [u'%d\tETC\ticon/item/%d.tga' % (i[0], i[0]) for i in ITEMS])))
    with open(desc_path, 'rb') as f:
        results.append((desc_path, base.set_rows(f.read(), [u'%d\t%s\t%s' % (i[0], i[2], i[6]) for i in ITEMS])))
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
