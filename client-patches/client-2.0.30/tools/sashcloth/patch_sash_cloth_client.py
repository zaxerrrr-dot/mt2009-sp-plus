# MT2009_PLUS_SASH_CLOTH_V1 - "Delikatne Sukno" (80019) in the client's data: the item the
# server's linux-port/docker/mariadb/playerbot/apply.sh adds to world.item_proto - keep them equal.
#
#   80019  Delikatne Sukno   ITEM_MATERIAL, stack 200 (flag 4), antiflag 0, buy 5000 / sell 1000
#
# Metins and bosses drop it in place of the +0 sash (server-patches/raremobrules); ten of
# them and 80 000 yang make the plain sash (85001) in Uriel's "Wytwarzanie" window
# (crafting window 111, game/quest/acce_costume_uriel.quest).
#
# The client already has its icon (icon/item/80019.tga in the icon pack, from Arezzo) and its
# itemdesc.txt line ("Delikatne Sukno / Z tego materialu mozna utkac szarfe."), but no
# item_proto record and no item_list.txt line - without them the item shows no name or icon.
# A new item_proto record (a copy of 30228's with every value cleared, as tools/monstercard)
# and a line in item_list.txt. Idempotent: a second run changes nothing; a record or line
# that is there is rewritten only when it differs.
#
# From client 2.0.52 item_proto lives in the "dbdata" pack (gamedata/item_proto), item_list.txt
# in gamedata. Run on plain copies of the two files, in the m2pack-lzo image for the proto's MCOZ:
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/sashcloth/patch_sash_cloth_client.py \
#     <item_proto> <item_list.txt> [<out dir>]
# Without an out dir the files are rewritten in place. Then the next client's dbdata base for
# the panel's database editor: python3 -m m2clientpack.make_base <client>/pack <version>
# (linux-port/docker/seban-panel, see /opt/metin2/cache/klient-do-zbudowania.md).
import os
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'monstercard'))
import patch_monstercard_client as base  # noqa: E402  (the record layout, MCOZ and the line writer)

# (vnum, name, Polish name, type, subtype, stack, antiflag, flag, buy, sell) - = apply.sh.
ITEMS = (
    (80019, u'Fine Cloth', u'Delikatne Sukno', 5, 0, 200, 0, 4, 5000, 1000),
)
ICON = u'icon/item/80019.tga'


def record(template, vnum, name, pl, typ, sub, stack, anti, flag, buy, sell):
    r = bytearray(base.card_record(template, vnum, name, pl, typ, sub, anti))
    struct.pack_into('<II', r, 78, stack, anti)
    struct.pack_into('<I', r, 86, flag)
    struct.pack_into('<qq', r, 98, buy, sell)
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
    for item in ITEMS:
        r = record(recs[base.TEMPLATE], *item)
        if recs.get(item[0]) != r:
            recs[item[0]] = r
            changed += 1
    if not changed:
        return b, 0
    out = b''.join(recs[v] for v in sorted(recs))
    blob = m2pack.mcoz_encode(out, base.ITEM_KEY)
    return b'MIPX' + struct.pack('<IIII', ver, stride, len(recs), len(blob)) + blob, changed


def main():
    if len(sys.argv) not in (3, 4):
        raise SystemExit('usage: patch_sash_cloth_client.py <item_proto> <item_list.txt> [<out dir>]')
    proto_path, list_path = sys.argv[1:3]
    out_dir = sys.argv[3] if len(sys.argv) == 4 else None
    results = []
    with open(proto_path, 'rb') as f:
        results.append((proto_path, item_proto(f.read())))
    with open(list_path, 'rb') as f:
        results.append((list_path, base.set_rows(f.read(), [u'%d\tETC\t%s' % (i[0], ICON) for i in ITEMS])))
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
