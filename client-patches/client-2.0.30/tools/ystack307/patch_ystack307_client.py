# MT2009_PLUS_STACK307_V1 - the client's gamedata/item_proto (dbdata pack) carries the same flags, stacks and limits
# linux-port/docker/mariadb/playerbot/stack307.sql writes into world.item_proto (a player's report on Yohara 3.0.7,
# 3 November 2026: "brak stackowania"). The client asks the flag itself whether a line stacks and splits, and shows a
# limit's timer from the proto.
#
#   50338-50343 Charyzma / Inspiracja Nowicjusza / Adepta / Eksperta: STACKABLE on, ANTI_STACK off, stack 200
#     (the wiki: "Laczenie: tak").
#   (withdrawn 3 Nov: 70434 Zwoj Skarbu (Stopien A) stays unchanged)
#   was: 70434 Zwoj Skarbu (Stopien A): STACKABLE on, ANTI_STACK off, stack 200 and no limit (the package's LIMIT_REAL_TIME
#     259200 - each piece's own end time, so no two ever stacked; this server has no Swiatynia Enigma yet).
#
# Run on a plain copy of gamedata/item_proto, in the m2pack-lzo image for the proto's MCOZ (clientY.sh's data step,
# after yitems307):
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/ystack307/patch_ystack307_client.py <item_proto> [<out item_proto>]
# Without an out path the file is rewritten in place. Idempotent: a second run changes nothing. Then the panel's
# database editor base: python3 -m m2clientpack.make_base <client>/pack <version>.
#
# The client item record (184 bytes; offsets as in tools/yitems307 and tools/yohara): stack 78 (uint32), antiflags 82
# (uint32), flags 86 (uint32), limits 114 (uint8 type, int32 value) x 2.
import os
import struct
import sys

sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
ITEM_KEY = (173217, 72619434, 408587239, 27973291)
RECORD = 184

FLAG_STACKABLE = 4
ANTI_STACK = 1 << 15
STACK = 200

# vnum: drop the limit 0 too - the same rows as stack307.sql
RULES = dict((v, False) for v in range(50338, 50344))
# 70434 Zwoj Skarbu stays as the wiki has it (no stacking, 3 days) - the owner, 3 November 2026; its drop is off instead.


def want(r):
    """The record as the patch leaves it."""
    vnum = struct.unpack_from('<I', r, 0)[0]
    r = bytearray(r)
    stk, anti, flags = struct.unpack_from('<III', r, 78)
    struct.pack_into('<III', r, 78, STACK, anti & ~ANTI_STACK, flags | FLAG_STACKABLE)
    if RULES[vnum]:
        struct.pack_into('<Bi', r, 114, 0, 0)
    return bytes(r)


def records(b):
    import m2pack
    assert b[:4] == b'MIPX'
    ver, stride, cnt, size = struct.unpack_from('<IIII', b, 4)
    assert stride == RECORD, stride
    raw = m2pack.mcoz_decode(b[20:], ITEM_KEY)
    return ver, stride, [raw[i * RECORD:(i + 1) * RECORD] for i in range(cnt)]


def item_proto(b):
    import m2pack
    ver, stride, recs = records(b)
    changed, seen = 0, set()
    for i, r in enumerate(recs):
        vnum = struct.unpack_from('<I', r, 0)[0]
        if vnum in RULES:
            seen.add(vnum)
            nr = want(r)
            if nr != r:
                recs[i] = nr
                changed += 1
    missing = sorted(set(RULES) - seen)
    assert not missing, 'records missing from the client item_proto: %s' % missing
    if not changed:
        return b, 0
    blob = m2pack.mcoz_encode(b''.join(recs), ITEM_KEY)
    return b'MIPX' + struct.pack('<IIII', ver, stride, len(recs), len(blob)) + blob, changed


def main():
    if len(sys.argv) not in (2, 3):
        sys.exit('usage: patch_ystack307_client.py <item_proto> [<out item_proto>]')
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) == 3 else src
    b = open(src, 'rb').read()
    nb, changed = item_proto(b)
    if nb != b or dst != src:
        d = os.path.dirname(dst)
        if d:
            os.makedirs(d, exist_ok=True)
        open(dst, 'wb').write(nb)
    print('item_proto: %d record(s) changed (stack 3.0.7: Charyzma / Inspiracja, Zwoj Skarbu (Stopien A)) -> %s'
          % (changed, dst))


if __name__ == '__main__':
    main()
