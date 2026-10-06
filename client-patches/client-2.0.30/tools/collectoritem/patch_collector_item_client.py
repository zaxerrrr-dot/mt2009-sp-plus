# MT2009_PLUS_COLLECTOR_ITEM_V1 - "Kolekcjoner" (70115) in the client's data: the item the
# server's linux-port/docker/mariadb/playerbot/apply.sh adds to world.item_proto - keep them equal.
#
#   70115  Kolekcjoner   ITEM_QUEST, stack 1, antiflag 106880 (DROP|SELL|GIVE|STACK|MYSHOP)
#
# Sold in the ItemShop (1000 SM, "Wyposazenie", index 16); its use opens the collector's
# storage anywhere (game/quest/kolekcjoner_item.quest -> "/kolekcjoner przedmiot",
# playerbot_collector.cpp); the window is root/uicollector.py, opened by the server's
# "COLL begin" as at the storekeeper.
#
# A new item_proto record (a copy of 30228's with every value cleared), a line in
# item_list.txt (the icon of Bilet Do Magazynu, icon/item/70010.tga - already in the
# icon pack, nothing new to pack) and a line in itemdesc.txt. Idempotent: a second run
# changes nothing; a record or line that is there is rewritten only when it differs.
#
# As tools/monstercard: from client 2.0.52 item_proto and itemdesc.txt live in the
# "dbdata" pack (gamedata/item_proto, locale/pl/itemdesc.txt), item_list.txt in gamedata.
# Run on plain copies of the three files, in the m2pack-lzo image for the proto's MCOZ:
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/collectoritem/patch_collector_item_client.py \
#     <item_proto> <item_list.txt> <itemdesc.txt> [<out dir>]
# Without an out dir the files are rewritten in place. Then the next client's dbdata
# base for the panel's database editor: python3 -m m2clientpack.make_base <client>/pack
# <version> (linux-port/docker/seban-panel, see /opt/metin2/cache/klient-do-zbudowania.md).
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'monstercard'))
import patch_monstercard_client as base  # noqa: E402  (the record layout, MCOZ and the line writer)

# (vnum, name, Polish name, type, subtype, stack, antiflag, flag, description) - = apply.sh.
ITEMS = (
    (70115, u'Collector', u'Kolekcjoner', 18, 0, 1, 106880, 0,
     u'Otwiera okno Kolekcjonera z dowolnego miejsca.'),
)
ICON = u'icon/item/70010.tga'


def record(template, vnum, name, pl, typ, sub, stack, anti, flag):
    import struct
    r = bytearray(base.card_record(template, vnum, name, pl, typ, sub, anti))
    struct.pack_into('<II', r, 78, stack, anti)
    struct.pack_into('<I', r, 86, flag)
    return bytes(r)


def item_proto(b):
    import struct
    import m2pack
    assert b[:4] == b'MIPX'
    ver, stride, cnt, size = struct.unpack_from('<IIII', b, 4)
    assert stride == base.RECORD, stride
    raw = m2pack.mcoz_decode(b[20:], base.ITEM_KEY)
    recs = dict((struct.unpack_from('<I', raw, i * base.RECORD)[0], raw[i * base.RECORD:(i + 1) * base.RECORD])
                for i in range(cnt))
    changed = 0
    for vnum, name, pl, typ, sub, stack, anti, flag, _desc in ITEMS:
        r = record(recs[base.TEMPLATE], vnum, name, pl, typ, sub, stack, anti, flag)
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
        raise SystemExit('usage: patch_collector_item_client.py <item_proto> <item_list.txt> <itemdesc.txt> [<out dir>]')
    proto_path, list_path, desc_path = sys.argv[1:4]
    out_dir = sys.argv[4] if len(sys.argv) == 5 else None
    results = []
    with open(proto_path, 'rb') as f:
        results.append((proto_path, item_proto(f.read())))
    with open(list_path, 'rb') as f:
        results.append((list_path, base.set_rows(f.read(), [u'%d\tETC\t%s' % (i[0], ICON) for i in ITEMS])))
    with open(desc_path, 'rb') as f:
        results.append((desc_path, base.set_rows(f.read(), [u'%d\t%s\t%s' % (i[0], i[2], i[8]) for i in ITEMS])))
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
