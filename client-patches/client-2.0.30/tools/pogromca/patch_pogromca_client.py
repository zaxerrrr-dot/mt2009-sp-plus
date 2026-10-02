# MT2009_PLUS_POGROMCA_V1: Pogromca Nieb. Smoka +0..+9 (3180-3189) in the
# client's gamedata/item_proto, the same rows apply.sh writes into
# world.item_proto (the package left both as an empty skeleton: level 0, no
# attack, no bonus, so the tooltip showed nothing). Filled like Seon-Pyeong's
# other level-80 weapons (Miecz Trytona 270-279): level, attack speed /
# strong against devils / strong against humans, attack 273-321 plus the
# refine bonus, prices, ANTI_SELL, socket % 3, refine chain 502-510 and
# +9 -> Ostrze Slonca (3190) by 610. Idempotent: a second run changes nothing.
#
# Run on the current file (a plain copy of gamedata/item_proto out of the
# gamedata pack), in the m2pack-lzo image for the proto's MCOZ:
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/pogromca/patch_pogromca_client.py \
#     <item_proto> [<out item_proto>]
# Without an out path the file is rewritten in place.
#
# The client item record (184 bytes, TItemTable_r156; offsets as in
# tools/seonhae/patch_seonhae_client.py): antiflags 82, buy 98 (int64), sell
# 106 (int64), limits 114 (2 x 5), applies 124 (3 x 5), values 139 (6 x 4),
# refined vnum 175, refine set 179, magic % 181, specular 182, socket % 183.
# buy = world gold, sell = world shop_buy_price (checked on 270 and 2160).
import os
import struct
import sys

sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
ITEM_KEY = (173217, 72619434, 408587239, 27973291)
RECORD = 184

LEVEL = (80, 80, 82, 82, 84, 84, 86, 86, 88, 90)
ATT_SPEED = (15, 15, 16, 17, 18, 20, 22, 24, 27, 30)
DEVIL = (2, 3, 4, 5, 6, 7, 8, 9, 10, 12)
HUMAN = (2, 3, 4, 5, 6, 7, 8, 9, 10, 12)
BONUS = (0, 3, 7, 11, 15, 20, 25, 31, 41, 55)
PRICE = (360000, 395000, 435000, 500000, 600000, 750000, 975000, 1320000, 1845000, 2770000)
ANTI_SELL = 1 << 8


def fill(r, plus):
    r = bytearray(r)
    struct.pack_into('<I', r, 82, struct.unpack_from('<I', r, 82)[0] | ANTI_SELL)
    struct.pack_into('<qq', r, 98, PRICE[plus], PRICE[plus])
    struct.pack_into('<BiBi', r, 114, 1, LEVEL[plus], 0, 0)
    struct.pack_into('<BiBiBi', r, 124, 17, ATT_SPEED[plus], 48, DEVIL[plus], 43, HUMAN[plus])
    struct.pack_into('<6i', r, 139, 0, 0, 0, 273, 321, BONUS[plus])
    struct.pack_into('<IH', r, 175, 3190 if plus == 9 else 3181 + plus, 610 if plus == 9 else 502 + plus)
    r[183] = 3
    return bytes(r)


def item_proto(b):
    import m2pack
    assert b[:4] == b'MIPX'
    ver, stride, cnt, size = struct.unpack_from('<IIII', b, 4)
    assert stride == RECORD, stride
    raw = m2pack.mcoz_decode(b[20:], ITEM_KEY)
    recs = [raw[i * RECORD:(i + 1) * RECORD] for i in range(cnt)]
    changed = 0
    for i, r in enumerate(recs):
        vnum = struct.unpack_from('<I', r, 0)[0]
        if 3180 <= vnum <= 3189:
            nr = fill(r, vnum - 3180)
            if nr != r:
                recs[i] = nr
                changed += 1
    if not changed:
        return b, 0
    blob = m2pack.mcoz_encode(b''.join(recs), ITEM_KEY)
    return b'MIPX' + struct.pack('<IIII', ver, stride, cnt, len(blob)) + blob, changed


def main():
    if len(sys.argv) not in (2, 3):
        sys.exit('usage: patch_pogromca_client.py <item_proto> [<out item_proto>]')
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) == 3 else src
    b = open(src, 'rb').read()
    nb, changed = item_proto(b)
    if nb != b or dst != src:
        d = os.path.dirname(dst)
        if d:
            os.makedirs(d, exist_ok=True)
        open(dst, 'wb').write(nb)
    print('item_proto: %d Pogromca rows filled -> %s' % (changed, dst))


if __name__ == '__main__':
    main()
