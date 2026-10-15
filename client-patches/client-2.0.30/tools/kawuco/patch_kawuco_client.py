# -*- coding: utf-8 -*-
# MT2009_PLUS_KAWUCO_V1 - Kawuco (20413), the boots NPC of Przyladek Smoczego Ognia, in the client's gamedata/mob_proto.
#
# The server has his row since this change (linux-port/docker/mariadb/playerbot/kawuco.sql) and spawns him at 662,1224;
# the client's mob_proto already has a 20413 record (an NPC, from the base client) but under another name ("Ji Jin"),
# and the name over his head and in the target window is the client's. This writes "Kawuco" into the record's name
# (offset 4, 25 bytes) and locale name (offset 29, 25 bytes) of the 256-byte record; nothing else changes. His look
# is gamedata/npclist.txt's "20413 japanese_pirate_2" (already in the client) with the model build_kawuco_pack.py adds.
# A client mob_proto without 20413 stops the run (the record would have to be built - not done here).
#
# Idempotent: a second run changes nothing. Run on a plain copy of the "gamedata" pack's gamedata/mob_proto (never on
# a cache's data itself), in the m2pack-lzo image for the MCOZ:
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/kawuco/patch_kawuco_client.py <mob_proto> [<out mob_proto>]
# Without an out path the file is rewritten in place.
import struct
import sys

sys.path.insert(0, '/opt/metin2/cache/cli')

MOB_KEY = (4813894, 18955, 552631, 6822045)
MOB_RECORD = 256
MOB_NAME = 4
MOB_LOCALE_NAME = 29
NAME_LEN = 25
VNUM = 20413
NAME = b'Kawuco'


def patch(b):
    import m2pack
    magic, cnt, esize = struct.unpack_from('<4sII', b, 0)
    assert magic == b'MMPT', magic
    raw = bytearray(m2pack.mcoz_decode(b[12:12 + esize], MOB_KEY))
    assert len(raw) == cnt * MOB_RECORD, (len(raw), cnt)
    want = NAME + b'\0' * (NAME_LEN - len(NAME))
    changed = 0
    seen = False
    for i in range(cnt):
        off = i * MOB_RECORD
        if struct.unpack_from('<I', raw, off)[0] != VNUM:
            continue
        seen = True
        for at in (MOB_NAME, MOB_LOCALE_NAME):
            old = bytes(raw[off + at:off + at + NAME_LEN])
            if old.split(b'\0')[0] != NAME:
                print('%d: name %r -> %r' % (VNUM, old.split(b'\0')[0], NAME))
                raw[off + at:off + at + NAME_LEN] = want
                changed += 1
    if not seen:
        raise SystemExit('not in the client mob_proto: %d' % VNUM)
    print('mob_proto: %d name field(s) of %d changed' % (changed, VNUM))
    if not changed:
        return b, 0
    blob = m2pack.mcoz_encode(bytes(raw), MOB_KEY)
    return struct.pack('<4sII', b'MMPT', cnt, len(blob)) + blob, changed


def main():
    if len(sys.argv) not in (2, 3):
        raise SystemExit('usage: patch_kawuco_client.py <mob_proto> [<out mob_proto>]')
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) == 3 else src
    with open(src, 'rb') as f:
        data, changed = patch(f.read())
    if changed or dst != src:
        with open(dst, 'wb') as f:
            f.write(data)


if __name__ == '__main__':
    main()
