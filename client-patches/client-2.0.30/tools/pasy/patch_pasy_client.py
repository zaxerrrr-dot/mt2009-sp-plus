# MT2009_PLUS_BELTS_V1 - the belt system (Pasy) in the client's item_proto. Autor: Digi Rasta
# (nowy-system v0.27.0, SYSTEMY/pasy.md; his klient.py PASY_KLIENT), ported into MT2009 PLUS.
#
# The client's item_proto had the first four belt families 18000-18039 (Lniany, Skorzany,
# Przepychu, Madrosci) as armour (type 2 / subtype 9, a wear flag) with no belt grade
# (value0 0), Lniany and Skorzany at level 55 and with no bonus: the tooltip showed the
# wrong level and bonus, and the belt window (ENABLE_NEW_EQUIPMENT_SYSTEM) opened no slot,
# whatever the refine. The forty records get the server's values (world.item_proto, checked
# on the test server 7 October): type ITEM_BELT (34/0), no wear flag, the level limit, the
# bonus and the belt grade in value0. 18040-18089 were right already. Names, icons, refine
# chains, prices and the stack field stay as they are. Idempotent: a second run changes
# nothing.
#
# From client 2.0.52 item_proto lives in the "dbdata" pack (gamedata/item_proto). Run on a
# plain copy, in the m2pack-lzo image for the proto's MCOZ:
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/pasy/patch_pasy_client.py <item_proto> [<out dir>]
# Without an out dir the file is rewritten in place. Then the next client's dbdata base for
# the panel's database editor: python3 -m m2clientpack.make_base <client>/pack <version>
# (linux-port/docker/seban-panel, see /opt/metin2/cache/klient-do-zbudowania.md).
import os
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'monstercard'))
import patch_monstercard_client as base  # noqa: E402  (the record layout and MCOZ keys)

ITEM_BELT = 34
LIMIT_LEVEL = 1
# (first vnum, level, bonus (apply type), bonus +0..+9, belt grade +0..+9) = world.item_proto.
FAMILIES = (
    (18000, 50, 6, (50, 50, 60, 70, 80, 90, 100, 200, 300, 500), (0, 1, 1, 1, 1, 2, 2, 3, 3, 4)),   # Lniany: max HP
    (18010, 70, 8, (10, 10, 20, 30, 40, 50, 60, 80, 100, 200), (0, 1, 1, 1, 1, 2, 2, 3, 3, 4)),     # Skorzany: max SP
    (18020, 85, 84, (1, 1, 1, 2, 2, 2, 3, 3, 4, 5), (0, 1, 1, 2, 2, 3, 3, 4, 4, 5)),                # Przepychu: yang drop
    (18030, 97, 83, (1, 1, 1, 2, 2, 2, 3, 3, 4, 5), (0, 1, 1, 2, 2, 3, 3, 4, 4, 5)),                # Madrosci: exp
)
BELTS = dict((first + i, (level, bonus, values[i], grades[i]))
             for first, level, bonus, values, grades in FAMILIES for i in range(10))


def item_proto(b):
    import m2pack
    assert b[:4] == b'MIPX'
    ver, stride, cnt, size = struct.unpack_from('<IIII', b, 4)
    assert stride == base.RECORD, stride
    raw = bytearray(m2pack.mcoz_decode(b[20:], base.ITEM_KEY))
    changed = 0
    seen = 0
    for i in range(cnt):
        off = i * base.RECORD
        vnum = struct.unpack_from('<I', raw, off)[0]
        if vnum not in BELTS:
            continue
        seen += 1
        level, bonus, value, grade = BELTS[vnum]
        r = bytearray(raw[off:off + base.RECORD])
        before = bytes(r)
        struct.pack_into('<BB', r, 74, ITEM_BELT, 0)                          # type, subtype
        struct.pack_into('<I', r, 90, 0)                                      # wear flag
        struct.pack_into('<BiBi', r, 114, LIMIT_LEVEL, level, 0, 0)      # limits
        struct.pack_into('<BiBiBi', r, 124, bonus, value, 0, 0, 0, 0)         # applies
        struct.pack_into('<i', r, 139, grade)                                 # value0 = belt grade
        if bytes(r) != before:
            raw[off:off + base.RECORD] = r
            changed += 1
    if seen != len(BELTS):
        raise SystemExit('item_proto: %d of the %d belt records found' % (seen, len(BELTS)))
    if not changed:
        return b, 0
    blob = m2pack.mcoz_encode(bytes(raw), base.ITEM_KEY)
    return b'MIPX' + struct.pack('<IIII', ver, stride, cnt, len(blob)) + blob, changed


def main():
    if len(sys.argv) not in (2, 3):
        raise SystemExit('usage: patch_pasy_client.py <item_proto> [<out dir>]')
    path = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) == 3 else None
    with open(path, 'rb') as f:
        data, changed = item_proto(f.read())
    target = os.path.join(out_dir, os.path.basename(path)) if out_dir else path
    if out_dir or changed:
        if out_dir and not os.path.isdir(out_dir):
            os.makedirs(out_dir)
        with open(target, 'wb') as f:
            f.write(data)
    print('%s: %d change(s)%s' % (os.path.basename(path), changed, '' if target == path else ' -> ' + target))


if __name__ == '__main__':
    main()
