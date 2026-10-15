# -*- coding: utf-8 -*-
# MT2009_PLUS_BERAN_CHEST_V1 - Skrzynia Berana-Setaou (54700, the official vnum; the owner, 15 October 2026; pl-wiki
# 17.3: Beran-Setaou gives 8-10, each opens 2 times), in the client's data - the client had no such item:
#
#   item_proto    a record (a copy of the Zelazna Szkatulka's, 50120, a giftbox) with the server's row of apply.sh:
#                 giftbox (23), stack 1, ANTI_STACK (32768), not STACKABLE - the openings are counted in the chest's
#                 socket 0 (ShipDefense_ChestKeep), so the client must not merge two chests;
#   item_list.txt "54700 ETC icon/item/54700.tga" - the GF 26.1.11 icon, a new file of the root pack
#                 (client-patches/client-2.0.30/root/icon/item/54700.tga; build57.py adds every file there);
#   itemdesc.txt  its line (the pl-wiki's text and "Mozna ja otworzyc 2 razy").
#
# Idempotent: a record or line that is there is rewritten only when it differs. From client 2.0.52 item_proto and
# itemdesc.txt live in the "dbdata" pack, item_list.txt in gamedata. Run on plain copies, in the m2pack-lzo image:
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/beran/patch_beran_chest_client.py \
#     <item_proto> <item_list.txt> <itemdesc.txt> [<out dir>]
# Without an out dir the files are rewritten in place. Then the next client's dbdata base for the panel's database
# editor (python3 -m m2clientpack.make_base <client>/pack <version>, linux-port/docker/seban-panel).
import os
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'monstercard'))
import patch_monstercard_client as base  # noqa: E402  (record layout, MCOZ key, the line writer)

TEMPLATE = 50120    # Zelazna Szkatulka, giftbox
VNUM = 54700
NAME, PL = u'Beran-Setaou Chest', u'Skrzynia Berana-Setaou'
ICON = u'icon/item/54700.tga'
DESC = (u'Ta skrzynia została wydobyta z Groty Wygnańców. Znajduje się w niej prawdziwy królewski skarb. '
        u'Można ją otworzyć 2 razy - za każdym razem coś daje.')


def record(template):
    r = bytearray(template)
    struct.pack_into('<II', r, 0, VNUM, 0)
    r[8:41] = base.fixed(NAME, 33)
    r[41:74] = base.fixed(PL, 33)
    struct.pack_into('<BBBB', r, 74, 23, 0, 0, 1)                    # giftbox, weight 0, size 1
    struct.pack_into('<IIIII', r, 78, 1, 32768, 0, 0, 0)            # stack 1, ANTI_STACK, no flags, wear, immune
    r[98:base.RECORD] = b'\0' * (base.RECORD - 98)                   # no price, limit, apply, value, socket, refine
    return bytes(r)


def item_proto(b):
    import m2pack
    assert b[:4] == b'MIPX'
    ver, stride, cnt, size = struct.unpack_from('<IIII', b, 4)
    assert stride == base.RECORD, stride
    raw = m2pack.mcoz_decode(b[20:], base.ITEM_KEY)
    recs = dict((struct.unpack_from('<I', raw, i * base.RECORD)[0], raw[i * base.RECORD:(i + 1) * base.RECORD])
                for i in range(cnt))
    r = record(recs[TEMPLATE])
    if recs.get(VNUM) == r:
        return b, 0
    recs[VNUM] = r
    out = b''.join(recs[v] for v in sorted(recs))
    blob = m2pack.mcoz_encode(out, base.ITEM_KEY)
    return b'MIPX' + struct.pack('<IIII', ver, stride, len(recs), len(blob)) + blob, 1


def main():
    if len(sys.argv) not in (4, 5):
        raise SystemExit('usage: patch_beran_chest_client.py <item_proto> <item_list.txt> <itemdesc.txt> [<out dir>]')
    proto_path, list_path, desc_path = sys.argv[1:4]
    out_dir = sys.argv[4] if len(sys.argv) == 5 else None
    results = []
    with open(proto_path, 'rb') as f:
        results.append((proto_path, item_proto(f.read())))
    with open(list_path, 'rb') as f:
        results.append((list_path, base.set_rows(f.read(), [u'%d\tETC\t%s' % (VNUM, ICON)])))
    with open(desc_path, 'rb') as f:
        results.append((desc_path, base.set_rows(f.read(), [u'%d\t%s\t%s' % (VNUM, PL, DESC)])))
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
