# MT2009_PLUS_MONSTER_CARDS_V1 - Karty Potworow (Autor: Digi Rasta, nowy-system v0.25.2,
# his klient.py KARTY_POTWOROW) in the client's data: the four items the server's
# linux-port/docker/mariadb/playerbot/apply.sh adds to world.item_proto - keep them equal.
#
#   50283  Karta Potwora                 ITEM_USE / USE_SPECIAL, stack 200, no drop/give/shop
#   50284  Karta Potwora (handlowalna)   ITEM_USE / USE_SPECIAL, stack 200, tradable
#   72322  Karta Nowego Poczatku         material, stack 200 (a mission reset past the free one)
#   72323  Karta Nowego Ukladu           material, stack 200 (new mission targets)
#
# A new item_proto record each (a copy of 30228's with every value cleared), a
# line in item_list.txt (icon/item/<vnum>.tga - the icons are new entries of the
# root pack: client-patches/client-2.0.30/root/icon/item, from the official
# client) and a line in itemdesc.txt. Idempotent: a second run changes nothing;
# a record or line that is there is rewritten only when it differs.
#
# From client 2.0.52 item_proto and itemdesc.txt live in the "dbdata" pack
# (gamedata/item_proto, locale/pl/itemdesc.txt), item_list.txt in gamedata.
# Run on plain copies of the three files, in the m2pack-lzo image for the
# proto's MCOZ:
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/monstercard/patch_monstercard_client.py \
#     <item_proto> <item_list.txt> <itemdesc.txt> [<out dir>]
# Without an out dir the files are rewritten in place. Then the next client's
# dbdata base for the panel's database editor: python3 -m m2clientpack.make_base
# <client>/pack <version> (linux-port/docker/seban-panel, see
# /opt/metin2/cache/klient-do-zbudowania.md).
#
# The client item record (184 bytes; offsets as in tools/digirasta): vnum 0,
# name 8 (33), locale name 41 (33), type 74, subtype 75, stack 78, antiflags 82,
# flags 86, wear 90, immune 94, buy 98 (int64), sell 106 (int64), limits 114,
# applies 124, values 139, sockets 163, refined vnum 175, refine set 179, magic %
# 181, specular 182, socket % 183.
import os
import struct
import sys

sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
ITEM_KEY = (173217, 72619434, 408587239, 27973291)
RECORD = 184
TEMPLATE = 30228

# (vnum, name, Polish name, type, subtype, antiflag, description) - = apply.sh.
CARDS = (
    (50283, u'Monster Card', u'Karta Potwora', 3, 10, 73856,
     u'Po użyciu dodaje kartę potwora do kolekcji (Karty Potworów w menu pod Esc). Nie można nią handlować.'),
    (50284, u'Monster Card (Tradable)', u'Karta Potwora (handlowalna)', 3, 10, 0,
     u'Po użyciu dodaje kartę potwora do kolekcji (Karty Potworów w menu pod Esc). Można nią handlować.'),
    (72322, u'New Start Card', u'Karta Nowego Początku', 5, 0, 0,
     u'Pozwala zresetować misję Kart Potworów ponad darmowy reset (raz na 24 godziny).'),
    (72323, u'New Order Card', u'Karta Nowego Układu', 5, 0, 0,
     u'Pozwala wylosować nowe cele misji Kart Potworów.'),
)


def fixed(text, size):
    b = text.encode('cp1250')
    assert len(b) < size, text
    return b + b'\0' * (size - len(b))


def card_record(template, vnum, name, pl, typ, sub, anti):
    r = bytearray(template)
    struct.pack_into('<II', r, 0, vnum, 0)
    r[8:41] = fixed(name, 33)
    r[41:74] = fixed(pl, 33)
    struct.pack_into('<BB', r, 74, typ, sub)
    struct.pack_into('<IIIII', r, 78, 200, anti, 4, 0, 0)   # stack, antiflags, flags (stackable), wear, immune
    r[98:RECORD] = b'\0' * (RECORD - 98)                    # no price, limit, apply, value, socket, refine
    return bytes(r)


def item_proto(b):
    import m2pack
    assert b[:4] == b'MIPX'
    ver, stride, cnt, size = struct.unpack_from('<IIII', b, 4)
    assert stride == RECORD, stride
    raw = m2pack.mcoz_decode(b[20:], ITEM_KEY)
    recs = dict((struct.unpack_from('<I', raw, i * RECORD)[0], raw[i * RECORD:(i + 1) * RECORD]) for i in range(cnt))
    changed = 0
    for vnum, name, pl, typ, sub, anti, _desc in CARDS:
        r = card_record(recs[TEMPLATE], vnum, name, pl, typ, sub, anti)
        if recs.get(vnum) != r:
            recs[vnum] = r
            changed += 1
    if not changed:
        return b, 0
    out = b''.join(recs[v] for v in sorted(recs))
    blob = m2pack.mcoz_encode(out, ITEM_KEY)
    return b'MIPX' + struct.pack('<IIII', ver, stride, len(recs), len(blob)) + blob, changed


def set_rows(b, rows):
    """Every line whose first column is a row's vnum becomes that row (or the
    row is appended); keeps the file's line ends."""
    text = b.decode('cp1250')
    nl = '\r\n' if '\r\n' in text else '\n'
    lines = text.split(nl)
    tail = lines and lines[-1] == ''
    if tail:
        lines.pop()
    changed = 0
    for row in rows:
        key = row.split('\t')[0]
        hits = [i for i, l in enumerate(lines) if l.split('\t')[0].strip() == key]
        if hits:
            for i in hits:
                if lines[i] != row:
                    lines[i] = row
                    changed += 1
        else:
            lines.append(row)
            changed += 1
    if tail:
        lines.append('')
    return nl.join(lines).encode('cp1250'), changed


def main():
    if len(sys.argv) not in (4, 5):
        raise SystemExit('usage: patch_monstercard_client.py <item_proto> <item_list.txt> <itemdesc.txt> [<out dir>]')
    proto_path, list_path, desc_path = sys.argv[1:4]
    out_dir = sys.argv[4] if len(sys.argv) == 5 else None
    results = []
    with open(proto_path, 'rb') as f:
        results.append((proto_path, item_proto(f.read())))
    with open(list_path, 'rb') as f:
        results.append((list_path, set_rows(f.read(), [u'%d\tETC\ticon/item/%d.tga' % (c[0], c[0]) for c in CARDS])))
    with open(desc_path, 'rb') as f:
        results.append((desc_path, set_rows(f.read(), [u'%d\t%s\t%s' % (c[0], c[2], c[6]) for c in CARDS])))
    for path, (data, changed) in results:
        target = os.path.join(out_dir, os.path.basename(path)) if out_dir else path
        if out_dir or changed:
            if out_dir and not os.path.isdir(out_dir):
                os.makedirs(out_dir)
            with open(target, 'wb') as f:
                f.write(data)
        print('%s: %d change(s)%s' % (os.path.basename(path), changed, '' if target == path else ' -> ' + target))


if __name__ == '__main__':
    main()
