# MT2009_PLUS_QUIVER_V1: Kolczan (8010), the ItemShop's quiver (100 SM, 14
# days), in the client - the same row linux-port/docker/mariadb/playerbot/
# apply.sh writes into the world, so the tooltip shows what the server does.
# Idempotent: a second run changes nothing.
#
#   item_proto    8010, a copy of the Silver Arrow (8005): type WEAPON /
#                 subtype ARROW (the arrow slot, wear 512 - the 2.0.x client
#                 knows no WEAPON_QUIVER), stack 1, ninja only, no drop / sell /
#                 trade / stall / PK drop (antiflag 123316), flag 0, no price,
#                 limit 0 LIMIT_REAL_TIME 1 209 600 s (14 days - the tooltip
#                 counts down socket0), no level floor, values 0/0/100/25/1300/
#                 2250 (the silver arrow's fade and bonus);
#   item_list.txt "8010 WEAPON icon/item/08010.tga" (an arrow has no model);
#   itemdesc.txt  the name and the Polish description.
#
# The icon, icon/item/08010.tga (32x32 RGBA, next to this script), is a new
# entry of the icon pack - GF 26.1.11 has no quiver icon; it was drawn for this
# item. The web shop's copy: linux-port/docker/itemshop/app/itemshop/img/item/
# 08010.png.
#
# Run on the current files (plain copies out of the gamedata and locale packs),
# in the m2pack-lzo image for the proto's MCOZ:
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/quiver/patch_quiver_client.py \
#     <item_proto> <item_list.txt> <itemdesc.txt> [<out dir>]
# Without an out dir the three files are rewritten in place.
#
# The client item record (184 bytes, TItemTable_r156; offsets as in
# tools/digirasta/patch_digirasta_client.py): vnum 0, name 8 (33), locale name
# 41 (33), type 74, subtype 75, stack 78, antiflags 82, flags 86, wear 90,
# immune 94, buy 98 (int64), sell 106 (int64), limits 114 (2 x 5), applies 124
# (3 x 5), values 139 (6 x 4), sockets 163, refined vnum 175, refine set 179.
import os
import struct
import sys

sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
ITEM_KEY = (173217, 72619434, 408587239, 27973291)
RECORD = 184

QUIVER_VNUM = 8010
TEMPLATE = 8005  # Srebrna Strzala
NAME = u'Kołczan'
DESC = (u'Kołczan pełen strzał, które nigdy się nie kończą. Załóż go w miejsce strzał: '
        u'łuk ninja strzela bez zużywania strzał (obrażenia jak ze Srebrnej Strzały). '
        u'Działa 14 dni od zakupu.')
ICON = 'icon/item/08010.tga'

ANTIFLAG = 123316   # 52 (ninja only) | drop | sell | give | PK drop | stack | stall
LIMIT_REAL_TIME = 7
DAYS14 = 14 * 86400
VALUES = (0, 0, 100, 25, 1300, 2250)


def fixed(text, size):
    b = text.encode('cp1250')
    assert len(b) < size, text
    return b + b'\0' * (size - len(b))


def set_quiver(r):
    struct.pack_into('<II', r, 0, QUIVER_VNUM, 0)
    r[8:41] = fixed(u'Quiver', 33)
    r[41:74] = fixed(NAME, 33)
    struct.pack_into('<BB', r, 74, 1, 6)
    struct.pack_into('<IIII', r, 78, 1, ANTIFLAG, 0, 512)
    struct.pack_into('<qq', r, 98, 0, 0)
    struct.pack_into('<BiBi', r, 114, LIMIT_REAL_TIME, DAYS14, 0, 0)
    struct.pack_into('<BiBiBi', r, 124, 0, 0, 0, 0, 0, 0)
    struct.pack_into('<6i', r, 139, *VALUES)
    struct.pack_into('<IH', r, 175, 0, 0)


def item_proto(b):
    import m2pack
    assert b[:4] == b'MIPX'
    ver, stride, cnt, size = struct.unpack_from('<IIII', b, 4)
    assert stride == RECORD, stride
    raw = m2pack.mcoz_decode(b[20:], ITEM_KEY)
    recs = dict((struct.unpack_from('<I', raw, i * RECORD)[0], raw[i * RECORD:(i + 1) * RECORD]) for i in range(cnt))
    r = bytearray(recs.get(QUIVER_VNUM, recs[TEMPLATE]))
    set_quiver(r)
    if recs.get(QUIVER_VNUM) == bytes(r):
        return b, 0
    recs[QUIVER_VNUM] = bytes(r)
    out = b''.join(recs[v] for v in sorted(recs))
    blob = m2pack.mcoz_encode(out, ITEM_KEY)
    return b'MIPX' + struct.pack('<IIII', ver, stride, len(recs), len(blob)) + blob, 1


def set_row(b, row):
    """The line whose first column is the row's replaced by it, or the row
    appended (before a trailing empty line)."""
    text = b.decode('cp1250')
    nl = '\r\n' if '\r\n' in text else '\n'
    lines = text.split(nl)
    key = row.split('\t')[0]
    hits = [i for i, l in enumerate(lines) if l.split('\t')[0].strip() == key]
    if hits:
        if all(lines[i] == row for i in hits):
            return b, 0
        for i in hits:
            lines[i] = row
    else:
        tail = lines and lines[-1] == ''
        if tail:
            lines.pop()
        lines.append(row)
        if tail:
            lines.append('')
    return nl.join(lines).encode('cp1250'), 1


def item_list_rows(b):
    return set_row(b, '%d\tWEAPON\t%s' % (QUIVER_VNUM, ICON))


def itemdesc_rows(b):
    return set_row(b, u'%d\t%s\t%s' % (QUIVER_VNUM, NAME, DESC))


def main():
    if len(sys.argv) not in (4, 5):
        sys.exit('usage: patch_quiver_client.py <item_proto> <item_list.txt> <itemdesc.txt> [<out dir>]')
    proto_p, list_p, desc_p = sys.argv[1:4]
    out_dir = sys.argv[4] if len(sys.argv) == 5 else None
    for path, fn in ((proto_p, item_proto), (list_p, item_list_rows), (desc_p, itemdesc_rows)):
        b = open(path, 'rb').read()
        nb, changed = fn(b)
        dst = os.path.join(out_dir, os.path.basename(path)) if out_dir else path
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        if nb != b or out_dir:
            open(dst, 'wb').write(nb)
        print('%s: %d changed -> %s' % (os.path.basename(path), changed, dst))


if __name__ == '__main__':
    main()
