# -*- coding: utf-8 -*-
# MT2009_PLUS_RZNM_GLOBAL_LEVEL_V1 - Razador's and Nemere's monsters at their official levels in the client.
#
# The server's world.mob_proto has them on Owsap v6.2.6's (= the official) numbers again (apply.sh,
# MT2009_PLUS_RZNM_GLOBAL_LEVEL_V1), but the client's gamedata/mob_proto still carries the levels of
# the lowered dungeons (2.0.28's dungeons_client patch_protos: 6001 56 ... Razador 68, Nemere 95), and
# the target window shows the client's level. This sets the level byte (offset 57 of the 256-byte
# record: type 54, rank 55, battle type 56, level 57) of the 25 monsters to the server's; nothing else
# in the record changes (the client draws no HP or damage of its own).
#
# Idempotent: a second run changes nothing. Run on a plain copy of the "gamedata" pack's
# gamedata/mob_proto (never on a cache's data itself), in the m2pack-lzo image for the MCOZ:
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/rznm/patch_rznm_client.py <mob_proto> [<out mob_proto>]
# Without an out path the file is rewritten in place.
import struct
import sys

sys.path.insert(0, '/opt/metin2/cache/cli')

MOB_KEY = (4813894, 18955, 552631, 6822045)
MOB_RECORD = 256
MOB_LEVEL = 57

# vnum -> level: Owsap v6.2.6 db/mob_proto.txt (= the server's apply.sh)
LEVELS = {
    6001: 97, 6002: 99, 6003: 100, 6004: 100, 6005: 103, 6006: 103, 6007: 105, 6008: 105, 6009: 107,
    6051: 107, 6091: 108,
    6101: 97, 6102: 99, 6103: 100, 6104: 100, 6105: 103, 6106: 103, 6107: 105, 6108: 105, 6109: 107,
    6151: 107, 6191: 108,
    8057: 100, 8058: 100, 20399: 100,
}


def patch(b):
    import m2pack
    magic, cnt, esize = struct.unpack_from('<4sII', b, 0)
    assert magic == b'MMPT', magic
    raw = bytearray(m2pack.mcoz_decode(b[12:12 + esize], MOB_KEY))
    assert len(raw) == cnt * MOB_RECORD, (len(raw), cnt)
    seen = set()
    changed = 0
    for i in range(cnt):
        off = i * MOB_RECORD
        vnum = struct.unpack_from('<I', raw, off)[0]
        if vnum not in LEVELS:
            continue
        seen.add(vnum)
        if raw[off + MOB_LEVEL] != LEVELS[vnum]:
            print('%d: level %d -> %d' % (vnum, raw[off + MOB_LEVEL], LEVELS[vnum]))
            raw[off + MOB_LEVEL] = LEVELS[vnum]
            changed += 1
    missing = sorted(set(LEVELS) - seen)
    if missing:
        raise SystemExit('not in the client mob_proto: %s' % missing)
    print('mob_proto: %d of the %d monsters changed' % (changed, len(LEVELS)))
    if not changed:
        return b, 0
    blob = m2pack.mcoz_encode(bytes(raw), MOB_KEY)
    return struct.pack('<4sII', b'MMPT', cnt, len(blob)) + blob, changed


def main():
    if len(sys.argv) not in (2, 3):
        raise SystemExit('usage: patch_rznm_client.py <mob_proto> [<out mob_proto>]')
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) == 3 else src
    with open(src, 'rb') as f:
        data, changed = patch(f.read())
    if changed or dst != src:
        with open(dst, 'wb') as f:
            f.write(data)


if __name__ == '__main__':
    main()
