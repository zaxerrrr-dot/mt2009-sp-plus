# MT2009_PLUS_SEONHAE_V1: Seon-Hae's shards and additives in the client's
# gamedata/item_proto, gamedata/item_list.txt and locale/pl/itemdesc.txt, from
# seonhae_items.json (the server rows are apply.sh's). Idempotent: an item
# already in a file is left alone, a second run changes nothing.
#
# Run on the current files (plain copies, as client-patches/client-2.0.30 keeps
# them), in the m2pack-lzo image for the proto's MCOZ:
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/seonhae/patch_seonhae_client.py \
#     <item_proto> <item_list.txt> <itemdesc.txt> [<out dir>]
# Without an out dir the three files are rewritten in place.
#
# The client item record (184 bytes, TItemTable_r156, checked against
# world.item_proto on 8101/25040/30000/71051): vnum 0, vnum range 4, name 8
# (33), locale name 41 (33), type 74, subtype 75, weight 76, size 77, stack
# 78, antiflags 82, flags 86, wear 90, immune 94, buy 98 (int64), sell 106
# (int64), limits 114 (2 x 5), applies 124 (3 x 5), values 139 (6 x 4),
# sockets 163 (3 x 4), refined vnum 175, refine set 179, magic % 181,
# specular 182, socket % 183.
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
ITEM_KEY = (173217, 72619434, 408587239, 27973291)
RECORD = 184
DATA = json.load(open(os.path.join(HERE, 'seonhae_items.json'), encoding='utf-8'))


def setstr(rec, off, size, s):
    b = s.encode('cp1250')
    assert len(b) < size, s
    rec[off:off + size] = b + b'\0' * (size - len(b))


def item_proto(b):
    import m2pack
    assert b[:4] == b'MIPX'
    ver, stride, cnt, size = struct.unpack_from('<IIII', b, 4)
    assert stride == RECORD, stride
    raw = m2pack.mcoz_decode(b[20:], ITEM_KEY)
    recs = [raw[i * RECORD:(i + 1) * RECORD] for i in range(cnt)]
    byv = dict((struct.unpack_from('<I', r, 0)[0], r) for r in recs)
    added = 0
    for it in DATA['items']:
        if it['vnum'] in byv:
            continue
        r = bytearray(byv[it['src']])
        struct.pack_into('<II', r, 0, it['vnum'], 0)
        setstr(r, 8, 33, it['name'])
        setstr(r, 41, 33, it['name'])
        struct.pack_into('<I', r, 82, it['antiflag'])
        struct.pack_into('<I', r, 86, it['flag'])
        struct.pack_into('<qq', r, 98, 0, 0)
        struct.pack_into('<i', r, 143, it['value1'])
        byv[it['vnum']] = bytes(r)
        added += 1
    if not added:
        return b, 0
    out = b''.join(byv[v] for v in sorted(byv))
    blob = m2pack.mcoz_encode(out, ITEM_KEY)
    return b'MIPX' + struct.pack('<IIII', ver, stride, len(byv), len(blob)) + blob, added


def append_rows(b, rows):
    text = b.decode('cp1250')
    nl = '\r\n' if '\r\n' in text else '\n'
    lines = text.split(nl)
    tail = lines and lines[-1] == ''
    if tail:
        lines.pop()
    have = set(l.split('\t')[0].strip() for l in lines)
    added = 0
    for r in rows:
        if r.split('\t')[0] not in have:
            lines.append(r)
            have.add(r.split('\t')[0])
            added += 1
    if tail:
        lines.append('')
    return nl.join(lines).encode('cp1250'), added


def main():
    if len(sys.argv) not in (4, 5):
        sys.exit(__doc__ or 'usage: patch_seonhae_client.py <item_proto> <item_list.txt> <itemdesc.txt> [<out dir>]')
    proto_p, list_p, desc_p = sys.argv[1:4]
    out_dir = sys.argv[4] if len(sys.argv) == 5 else None
    jobs = [
        (proto_p, lambda b: item_proto(b)),
        (list_p, lambda b: append_rows(b, ['%d\tETC\t%s' % (it['vnum'], it['icon']) for it in DATA['items']])),
        (desc_p, lambda b: append_rows(b, ['%d\t%s\t%s' % (it['vnum'], it['name'], it['desc']) for it in DATA['items']])),
    ]
    for path, fn in jobs:
        b = open(path, 'rb').read()
        nb, added = fn(b)
        dst = os.path.join(out_dir, os.path.basename(path)) if out_dir else path
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        if nb != b or out_dir:
            open(dst, 'wb').write(nb)
        print('%s: %d added -> %s' % (os.path.basename(path), added, dst))


if __name__ == '__main__':
    main()
