# MT2009_PLUS_DIGI_STACK_V1 (Autor: Digi Rasta, nowy-system v0.23 - his
# 20_stakowanie.sql and klient.py STACK_*): the client's item_proto gets the
# stacks the server's apply.sh writes, so the bag shows and splits them the way
# the server keeps them:
#
#   * every soul stone (type 10), every gift box (type 23) and the caskets and
#     chests of STACK_VNUMS: STACKABLE flag (4), no ANTI_STACK (1 << 15),
#     stack 200;
#   * Odlamek Smoczego Kamienia (30270): no 24 h real-time limit (limit type 7).
#
# Keep STACK_TYPES / STACK_VNUMS / UNTIMED_VNUMS equal to the
# MT2009_PLUS_DIGI_STACK_V1 block of linux-port/docker/mariadb/playerbot/apply.sh.
# Idempotent: a second run changes nothing.
#
# Run on a plain copy of gamedata/item_proto, in the m2pack-lzo image (MCOZ):
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/digirasta/patch_digirasta_stack.py \
#     <item_proto> [<out dir>]
# Without an out dir the file is rewritten in place.
#
# The client item record (184 bytes; offsets as in patch_digirasta_client.py):
# type 74, stack 78, antiflags 82, flags 86, limits 114 (2 x (BYTE type, int value)).
import os
import struct
import sys

sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
ITEM_KEY = (173217, 72619434, 408587239, 27973291)
RECORD = 184

STACK = 200
FLAG_STACKABLE = 4
ANTIFLAG_STACK = 1 << 15
STACK_TYPES = (10, 23)   # ITEM_METIN (soul stones), ITEM_GIFTBOX (boxes, caskets, Cors)
STACK_VNUMS = (30118, 50006, 50007, 50011, 50012, 50013, 50033, 50034, 50037,
               50070, 50071, 50072, 50073, 50074, 50075, 50076, 50077, 50078, 50079,
               50080, 50081, 50082, 50090, 50097, 50098,
               50109, 50110, 50111, 50112, 50113, 50114, 50115, 50120, 50218,
               70009, 70619, 30670,
               30300, 38054, 38056, 38057, 50130, 50132, 50133, 50134, 50135, 50136, 50137,
               # MT2009_PLUS_STACK_CHESTS_COUPONS_V1: the Kupony SM (80014-80018) and
               # the Grotto's chests (50120-50122, 50124 - gift boxes, here as well)
               80014, 80015, 80016, 80017, 80018, 50121, 50122, 50124)
UNTIMED_VNUMS = (30270,)  # Odlamek Smoczego Kamienia: no 24 h limit
LIMIT_REAL_TIME = 7


def patch_record(vnum, r):
    if r[74] in STACK_TYPES or vnum in STACK_VNUMS:
        stack, anti, flag = struct.unpack_from('<III', r, 78)
        struct.pack_into('<III', r, 78, STACK, anti & ~ANTIFLAG_STACK, flag | FLAG_STACKABLE)
    if vnum in UNTIMED_VNUMS:
        for slot in (114, 119):
            if r[slot] == LIMIT_REAL_TIME:
                struct.pack_into('<Bi', r, slot, 0, 0)


def item_proto(b):
    import m2pack
    assert b[:4] == b'MIPX'
    ver, stride, cnt, size = struct.unpack_from('<IIII', b, 4)
    assert stride == RECORD, stride
    raw = m2pack.mcoz_decode(b[20:], ITEM_KEY)
    assert len(raw) >= cnt * RECORD, (len(raw), cnt)
    recs = [bytearray(raw[i * RECORD:(i + 1) * RECORD]) for i in range(cnt)]
    changed = 0
    for r in recs:
        before = bytes(r)
        patch_record(struct.unpack_from('<I', r, 0)[0], r)
        changed += bytes(r) != before
    if not changed:
        return b, 0
    blob = m2pack.mcoz_encode(b''.join(bytes(r) for r in recs), ITEM_KEY)
    return b'MIPX' + struct.pack('<IIII', ver, stride, cnt, len(blob)) + blob, changed


def main():
    if len(sys.argv) not in (2, 3):
        sys.exit('usage: patch_digirasta_stack.py <item_proto> [<out dir>]')
    path = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) == 3 else None
    b = open(path, 'rb').read()
    nb, changed = item_proto(b)
    dst = os.path.join(out_dir, os.path.basename(path)) if out_dir else path
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    if nb != b or out_dir:
        open(dst, 'wb').write(nb)
    print('%s: %d record(s) changed -> %s' % (os.path.basename(path), changed, dst))


if __name__ == '__main__':
    main()
