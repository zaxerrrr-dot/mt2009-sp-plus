# MT2009_PLUS_NO_AWAKENING_V1 (client data; the owner, 15 October 2026, Yohara 3.0): the Ritual of Awakening and
# the awakened weapons are gone (server: linux-port/docker/mariadb/playerbot/noawaken.sql, playerbot_awakening.h).
# What tools/digirasta/patch_digirasta_client.py (MT2009_PLUS_AWAKENING_V1) wrote into the client is put back:
#
#   item_proto    the seven families 210, 220, 1160, 2190, 3170, 5150, 7170 +0..+9 get the official records again -
#                 every field the awakening set (type/subtype, flags, prices, level limits, applies, values,
#                 refine chain, magic %, specular, socket %) from tools/noawaken/noawaken_client.json, which
#                 tools/noawaken/gen_noawaken.py writes from the same rows as the server's noawaken.sql
#                 (item_proto.mt2009plus.sql - the world before 3 October). Names are not touched.
#   itemdesc.txt  Kamien Przebudzenia (30670) stays for the pieces players hold, its line says it has no use any more.
#
# The players' awakened pieces are the level-87 weapons now (server-side vnum move); those records are the
# client's own, nothing changes for them. Idempotent: a record or line that is there is rewritten only when it
# differs. Run on plain copies of the files (dbdata pack: gamedata/item_proto, locale/pl/itemdesc.txt), in the
# m2pack-lzo image for the proto's MCOZ, AFTER tools/digirasta (if a chain still runs it) and anything else that
# writes these records:
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/noawaken/patch_noawaken_client.py \
#     <item_proto> <itemdesc.txt> [<out dir>]
# Without an out dir the files are rewritten in place.
#
# The client item record (184 bytes, TItemTable_r156; offsets as in tools/digirasta/patch_digirasta_client.py):
# type 74, subtype 75, stack 78, antiflags 82, flags 86, wear 90, immune 94, buy 98 (int64), sell 106 (int64),
# limits 114 (2 x 5), applies 124 (3 x 5), values 139 (6 x 4), refined vnum 175, refine set 179, magic % 181,
# specular 182, socket % 183.
import json
import os
import struct
import sys

sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
ITEM_KEY = (173217, 72619434, 408587239, 27973291)
RECORD = 184

DATA_PATH = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'tools',
                                          'noawaken', 'noawaken_client.json'))
with open(DATA_PATH, encoding='utf-8') as _f:
    DATA = json.load(_f)

STONE_VNUM = DATA['stone_vnum']
STONE_NAME = u'Kamień Przebudzenia'
STONE_DESC = (u'Wycofany przedmiot: Rytuału Przebudzenia już nie ma, a kamień nie ma żadnego zastosowania. '
              u'Możesz go wyrzucić.')


def set_record(r, f):
    struct.pack_into('<BB', r, 74, f['type'], f['subtype'])
    struct.pack_into('<I', r, 78, f['stack'])
    struct.pack_into('<IIII', r, 82, f['antiflag'], f['flag'], f['wearflag'], 0)
    struct.pack_into('<qq', r, 98, f['gold'], f['shop_buy_price'])
    struct.pack_into('<BiBi', r, 114, f['limittype0'], f['limitvalue0'], f['limittype1'], f['limitvalue1'])
    struct.pack_into('<BiBiBi', r, 124, f['applytype0'], f['applyvalue0'], f['applytype1'], f['applyvalue1'],
                     f['applytype2'], f['applyvalue2'])
    struct.pack_into('<6i', r, 139, *[f['value%d' % i] for i in range(6)])
    struct.pack_into('<IH', r, 175, f['refined_vnum'], f['refine_set'])
    struct.pack_into('<BBB', r, 181, f['magic_pct'], f['specular'], f['socket_pct'])


def item_proto(b):
    import m2pack
    assert b[:4] == b'MIPX'
    ver, stride, cnt, size = struct.unpack_from('<IIII', b, 4)
    assert stride == RECORD, stride
    raw = m2pack.mcoz_decode(b[20:], ITEM_KEY)
    recs = dict((struct.unpack_from('<I', raw, i * RECORD)[0], raw[i * RECORD:(i + 1) * RECORD]) for i in range(cnt))
    changed = 0
    for vnum, f in sorted(DATA['records'].items(), key=lambda kv: int(kv[0])):
        vnum = int(vnum)
        assert f['immuneflag'] == '', (vnum, f['immuneflag'])
        r = bytearray(recs[vnum])
        set_record(r, f)
        if bytes(r) != recs[vnum]:
            recs[vnum] = bytes(r)
            changed += 1
    if not changed:
        return b, 0
    out = b''.join(recs[v] for v in sorted(recs))
    blob = m2pack.mcoz_encode(out, ITEM_KEY)
    return b'MIPX' + struct.pack('<IIII', ver, stride, len(recs), len(blob)) + blob, changed


def itemdesc_rows(b):
    """The stone's line replaced (or appended when the file has none)."""
    text = b.decode('cp1250')
    nl = '\r\n' if '\r\n' in text else '\n'
    lines = text.split(nl)
    row = u'%d\t%s\t%s' % (STONE_VNUM, STONE_NAME, STONE_DESC)
    changed, hit = 0, False
    for i, l in enumerate(lines):
        if l.split('\t')[0].strip() == str(STONE_VNUM):
            hit = True
            if l != row:
                lines[i] = row
                changed += 1
    if not hit:
        tail = lines and lines[-1] == ''
        if tail:
            lines.pop()
        lines.append(row)
        if tail:
            lines.append('')
        changed += 1
    return nl.join(lines).encode('cp1250'), changed


def main():
    if len(sys.argv) not in (3, 4):
        sys.exit('usage: patch_noawaken_client.py <item_proto> <itemdesc.txt> [<out dir>]')
    proto_p, desc_p = sys.argv[1:3]
    out_dir = sys.argv[3] if len(sys.argv) == 4 else None
    for path, fn in ((proto_p, item_proto), (desc_p, itemdesc_rows)):
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
