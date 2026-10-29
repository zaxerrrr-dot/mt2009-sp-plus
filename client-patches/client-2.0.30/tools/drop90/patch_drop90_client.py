# MT2009_PLUS_DROP90_V1 - the client's gamedata/item_proto (dbdata pack) carries the same antiflags and
# prices apply.sh writes into world.item_proto (the owner, 29 October 2026). The client asks the antiflags
# itself before it sends a line to a stall, a trade or the merchant, so without this the old client still
# refuses what the server takes now.
#
#   39006 Peleryna Mestwa (the level-90 maps' drop), 70005 / 39002 Pierscien Doswiadczenia, 70043 Rekawica
#   Zlodzieja: ANTI_SELL, ANTI_GIVE and ANTI_MYSHOP (256 | 8192 | 65536) off.
#   The level-66 body armours (11290-11299, 11490-11499, 11690-11699, 11890-11899): ANTI_SELL (256) off at
#   +4..+9, buy = sell = 140 000, 150 000, 170 000, 195 000, 220 000, 255 000, 310 000, 380 000, 475 000,
#   600 000 for +0..+9 (were the level-61 ladder 120 000 .. 515 000).
#
# Run on the current file (a plain copy of gamedata/item_proto out of the dbdata pack), in the m2pack-lzo
# image for the proto's MCOZ:
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/drop90/patch_drop90_client.py <item_proto> [<out item_proto>]
# Without an out path the file is rewritten in place. Idempotent: a second run changes nothing. Then the
# panel's database editor base: python3 -m m2clientpack.make_base <client>/pack <version>.
#
# Record layout as tools/pogromca/patch_pogromca_client.py (184 bytes): antiflags 82 (uint32), buy 98 and
# sell 106 (int64; buy = world gold, sell = world shop_buy_price).
import os
import struct
import sys

sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
ITEM_KEY = (173217, 72619434, 408587239, 27973291)
RECORD = 184

TRADE_BITS = (1 << 8) | (1 << 13) | (1 << 16)   # ANTI_SELL | ANTI_GIVE | ANTI_MYSHOP
ANTI_SELL = 1 << 8
TRADE_VNUMS = (39006, 70005, 39002, 70043)
ARMOUR_FIRST = (11290, 11490, 11690, 11890)
PRICE = (140000, 150000, 170000, 195000, 220000, 255000, 310000, 380000, 475000, 600000)


def fix(r):
    vnum = struct.unpack_from('<I', r, 0)[0]
    r = bytearray(r)
    anti = struct.unpack_from('<I', r, 82)[0]
    if vnum in TRADE_VNUMS:
        struct.pack_into('<I', r, 82, anti & ~TRADE_BITS)
    elif any(first <= vnum <= first + 9 for first in ARMOUR_FIRST):
        plus = vnum % 10
        if plus >= 4:
            struct.pack_into('<I', r, 82, anti & ~ANTI_SELL)
        struct.pack_into('<qq', r, 98, PRICE[plus], PRICE[plus])
    return bytes(r)


def item_proto(b):
    import m2pack
    assert b[:4] == b'MIPX'
    ver, stride, cnt, size = struct.unpack_from('<IIII', b, 4)
    assert stride == RECORD, stride
    raw = m2pack.mcoz_decode(b[20:], ITEM_KEY)
    recs = [raw[i * RECORD:(i + 1) * RECORD] for i in range(cnt)]
    changed, seen = 0, 0
    for i, r in enumerate(recs):
        vnum = struct.unpack_from('<I', r, 0)[0]
        if vnum in TRADE_VNUMS or any(first <= vnum <= first + 9 for first in ARMOUR_FIRST):
            seen += 1
            nr = fix(r)
            if nr != r:
                recs[i] = nr
                changed += 1
    assert seen == len(TRADE_VNUMS) + 10 * len(ARMOUR_FIRST), 'expected 44 records, found %d' % seen
    if not changed:
        return b, 0
    blob = m2pack.mcoz_encode(b''.join(recs), ITEM_KEY)
    return b'MIPX' + struct.pack('<IIII', ver, stride, cnt, len(blob)) + blob, changed


def main():
    if len(sys.argv) not in (2, 3):
        sys.exit('usage: patch_drop90_client.py <item_proto> [<out item_proto>]')
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) == 3 else src
    b = open(src, 'rb').read()
    nb, changed = item_proto(b)
    if nb != b or dst != src:
        d = os.path.dirname(dst)
        if d:
            os.makedirs(d, exist_ok=True)
        open(dst, 'wb').write(nb)
    print('item_proto: %d record(s) changed (drop 90: capes, rings, gloves, level-66 armours) -> %s' % (changed, dst))


if __name__ == '__main__':
    main()
