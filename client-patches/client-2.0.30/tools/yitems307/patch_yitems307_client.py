# MT2009_PLUS_DROP307_V1 - the client's gamedata/item_proto (dbdata pack) carries the same flags, antiflags and stacks
# linux-port/docker/mariadb/playerbot/drop307.sql writes into world.item_proto (the owner's list of 3 November 2026,
# Yohara 3.x section C). The client asks the flags itself - whether a line stacks and splits, whether it may go to a
# trade, a stall, the merchant, the safebox - so without this the old client still refuses what the server takes.
#
#   39002 / 72003 Pierscien Doswiadczenia: STACKABLE on, IRREMOVABLE off, ANTI_STACK / ANTI_SELL / ANTI_GIVE / ANTI_MYSHOP off.
#   70005 Pierscien Doswiadczenia, 70043 Rekawica Zlodzieja: IRREMOVABLE kept (owner 3 Nov), ANTI_SELL / ANTI_GIVE / ANTI_MYSHOP off.
#   72005 Rekawica Zlodzieja: IRREMOVABLE kept (owner 3 Nov).
#   39006 Peleryna Mestwa: ANTI_STACK / ANTI_SELL / ANTI_GIVE / ANTI_MYSHOP off.
#   50516-50523 Ksiegi Riposty: STACKABLE on, stack 200.
#   49990 Lodowa Runa Aury: ANTI_SAFEBOX off.
#   39015 Kamien Kowala / 39016 Magiczny Metal (the tradeable twins): STACKABLE on, stack 200, ANTI_STACK / ANTI_SELL /
#   ANTI_GIVE / ANTI_MYSHOP off (their itemdesc already says "Przedmiot ten jest zdatny do handlu").
#
# Run on a plain copy of gamedata/item_proto, in the m2pack-lzo image for the proto's MCOZ (clientY.sh's data step,
# with the other item_proto patches):
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/yitems307/patch_yitems307_client.py <item_proto> [<out item_proto>]
# Without an out path the file is rewritten in place. Idempotent: a second run changes nothing. Then the panel's
# database editor base: python3 -m m2clientpack.make_base <client>/pack <version>.
#
# The client item record (184 bytes; offsets as in tools/digirasta/patch_digirasta_stack.py): stack 78 (uint32),
# antiflags 82 (uint32), flags 86 (uint32).
import os
import struct
import sys

sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
ITEM_KEY = (173217, 72619434, 408587239, 27973291)
RECORD = 184

FLAG_STACKABLE = 4
FLAG_IRREMOVABLE = 256
ANTI_SELL = 1 << 8
ANTI_GIVE = 1 << 13
ANTI_STACK = 1 << 15
ANTI_MYSHOP = 1 << 16
ANTI_SAFEBOX = 1 << 17
TRADE = ANTI_SELL | ANTI_GIVE | ANTI_MYSHOP

# vnum: (flags on, flags off, antiflags off, stack or None) - the same rows as drop307.sql
RULES = {
    39002: (FLAG_STACKABLE, FLAG_IRREMOVABLE, TRADE | ANTI_STACK, None),
    72003: (FLAG_STACKABLE, FLAG_IRREMOVABLE, TRADE | ANTI_STACK, None),
    70005: (FLAG_IRREMOVABLE, 0, TRADE, None),	# MT2009_PLUS_IRREMOVABLE_KEEP_V1: stays irremovable
    70043: (FLAG_IRREMOVABLE, 0, TRADE, None),
    72005: (FLAG_IRREMOVABLE, 0, 0, None),
    39006: (0, 0, TRADE | ANTI_STACK, None),
    49990: (0, 0, ANTI_SAFEBOX, None),
    39015: (FLAG_STACKABLE, 0, TRADE | ANTI_STACK, 200),
    39016: (FLAG_STACKABLE, 0, TRADE | ANTI_STACK, 200),
}
for _v in range(50516, 50524):
    RULES[_v] = (FLAG_STACKABLE, 0, 0, 200)


def fix(r):
    vnum = struct.unpack_from('<I', r, 0)[0]
    on, off, anti_off, stack = RULES[vnum]
    r = bytearray(r)
    stk, anti, flags = struct.unpack_from('<III', r, 78)
    struct.pack_into('<III', r, 78, stk if stack is None else stack, anti & ~anti_off, (flags | on) & ~off)
    return bytes(r)


def item_proto(b):
    import m2pack
    assert b[:4] == b'MIPX'
    ver, stride, cnt, size = struct.unpack_from('<IIII', b, 4)
    assert stride == RECORD, stride
    raw = m2pack.mcoz_decode(b[20:], ITEM_KEY)
    recs = [raw[i * RECORD:(i + 1) * RECORD] for i in range(cnt)]
    changed, seen = 0, set()
    for i, r in enumerate(recs):
        vnum = struct.unpack_from('<I', r, 0)[0]
        if vnum in RULES:
            seen.add(vnum)
            nr = fix(r)
            if nr != r:
                recs[i] = nr
                changed += 1
    missing = sorted(set(RULES) - seen)
    assert not missing, 'records missing from the client item_proto: %s' % missing
    if not changed:
        return b, 0
    blob = m2pack.mcoz_encode(b''.join(recs), ITEM_KEY)
    return b'MIPX' + struct.pack('<IIII', ver, stride, cnt, len(blob)) + blob, changed


def main():
    if len(sys.argv) not in (2, 3):
        sys.exit('usage: patch_yitems307_client.py <item_proto> [<out item_proto>]')
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) == 3 else src
    b = open(src, 'rb').read()
    nb, changed = item_proto(b)
    if nb != b or dst != src:
        d = os.path.dirname(dst)
        if d:
            os.makedirs(d, exist_ok=True)
        open(dst, 'wb').write(nb)
    print('item_proto: %d record(s) changed (drop 3.0.7: rings, gloves, capes, riposte books, ice aura rune, '
          'tradeable smith materials) -> %s' % (changed, dst))


if __name__ == '__main__':
    main()
