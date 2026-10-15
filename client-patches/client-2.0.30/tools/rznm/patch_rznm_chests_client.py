# -*- coding: utf-8 -*-
# MT2009_PLUS_RZNM_BOSS_DROP_V1 - Skrzynia Razadora (50270) and Skrzynia Nemere (50271) open 3 times (the owner,
# 15 October; pl-wiki 17.3), in the client's data:
#
#   item_proto    the two records ANTI_STACK (antiflag | 32768) and no longer STACKABLE (flag & ~4) - the server's
#                 apply.sh writes the same into world.item_proto; the openings are counted in the chest's socket 0
#                 (ShipDefense_ChestKeep, the Skrzynia Hydry's way), so the client must not merge two chests;
#   itemdesc.txt  their lines say so ("Można ją otworzyć 3 razy").
#
# Record layout (184 bytes): stack 78, antiflag 82, flag 86 (<I each). Idempotent: a second run changes nothing.
# From client 2.0.52 both files live in the "dbdata" pack (gamedata/item_proto, locale/pl/itemdesc.txt). Run on
# plain copies, in the m2pack-lzo image for the MCOZ:
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/rznm/patch_rznm_chests_client.py <item_proto> <itemdesc.txt> [<out dir>]
# Without an out dir the files are rewritten in place. Either file may be "-" to leave it alone.
import os
import struct
import sys

sys.path.insert(0, '/opt/metin2/cache/cli')

ITEM_KEY = (173217, 72619434, 408587239, 27973291)
RECORD = 184
ANTI_STACK = 32768
STACKABLE = 4
CHESTS = (50270, 50271)
DESC = {
    50270: u'50270\tSkrzynia Razadora\tTa skrzynia została wydobyta z Czyśćca Ognia, legowiska Razadora. '
           u'Znajduje się w niej prawdziwy królewski skarb. Można ją otworzyć 3 razy - za każdym razem coś daje.',
    50271: u'50271\tSkrzynia Nemere\tTa skrzynia została wydobyta z Lodowej Krainy, legowiska Nemere. '
           u'Znajduje się w niej prawdziwy królewski skarb. Można ją otworzyć 3 razy - za każdym razem coś daje.',
}


def item_proto(b):
    import m2pack
    assert b[:4] == b'MIPX'
    ver, stride, cnt, size = struct.unpack_from('<IIII', b, 4)
    assert stride == RECORD, stride
    raw = bytearray(m2pack.mcoz_decode(b[20:], ITEM_KEY))
    assert len(raw) == cnt * RECORD, (len(raw), cnt)
    seen = set()
    changed = 0
    for i in range(cnt):
        off = i * RECORD
        vnum = struct.unpack_from('<I', raw, off)[0]
        if vnum not in CHESTS:
            continue
        seen.add(vnum)
        anti, flag = struct.unpack_from('<II', raw, off + 82)
        new = (anti | ANTI_STACK, flag & ~STACKABLE)
        if new != (anti, flag):
            struct.pack_into('<II', raw, off + 82, *new)
            print('%d: antiflag %d -> %d, flag %d -> %d' % (vnum, anti, new[0], flag, new[1]))
            changed += 1
    if seen != set(CHESTS):
        raise SystemExit('item_proto: not in the client: %s' % sorted(set(CHESTS) - seen))
    if not changed:
        return b, 0
    blob = m2pack.mcoz_encode(bytes(raw), ITEM_KEY)
    return b'MIPX' + struct.pack('<IIII', ver, stride, cnt, len(blob)) + blob, changed


def itemdesc(b):
    text = b.decode('cp1250')
    nl = '\r\n' if '\r\n' in text else '\n'
    lines = text.split(nl)
    changed = 0
    seen = set()
    for i, l in enumerate(lines):
        k = l.split('\t')[0].strip()
        if k.isdigit() and int(k) in DESC:
            seen.add(int(k))
            if l != DESC[int(k)]:
                lines[i] = DESC[int(k)]
                changed += 1
    for v in CHESTS:
        if v not in seen:
            if lines and lines[-1] == '':
                lines.insert(len(lines) - 1, DESC[v])
            else:
                lines.append(DESC[v])
            changed += 1
    print('itemdesc.txt: %d lines changed' % changed)
    return nl.join(lines).encode('cp1250'), changed


def main():
    if len(sys.argv) not in (3, 4):
        raise SystemExit('usage: patch_rznm_chests_client.py <item_proto> <itemdesc.txt> [<out dir>]')
    out_dir = sys.argv[3] if len(sys.argv) == 4 else None
    for path, fn in ((sys.argv[1], item_proto), (sys.argv[2], itemdesc)):
        if path == '-':
            continue
        with open(path, 'rb') as f:
            data, changed = fn(f.read())
        target = os.path.join(out_dir, os.path.basename(path)) if out_dir else path
        if out_dir or changed:
            if out_dir and not os.path.isdir(out_dir):
                os.makedirs(out_dir)
            with open(target, 'wb') as f:
                f.write(data)


if __name__ == '__main__':
    main()
