# -*- coding: utf-8 -*-
# MT2009_PLUS_ARROWS_GLOBAL_V1 - the ammunition as on the global server (the owner, 5 November 2026; the pl-wiki's
# category Przedmioty/Amunicja) in the client's data: the same rows linux-port/docker/mariadb/playerbot/
# strzaly_global.sql and apply.sh (Kolczan 8010) write into world.item_proto - keep the two equal.
#
#   item_proto (dbdata gamedata/item_proto):
#     8000-8005  the six arrows: values 0 / magic / 0 / attack / 0 / 0 (the wiki's 3/1, 10/2, 15/3, 17/4, 20/5, 25/4,
#                no fade - the old 40-100 / 500-1300 / 1250-2250 are gone), levels 0/10/30/40/45/50; the Wooden
#                Arrow's price 5 (COUNT_PER_1GOLD: 5 a Yang - the wiki's 100 for 20 Yang)
#     8010       Kolczan (the ItemShop's, 14 days): values 0 / 4 / 0 / 25 / 0 / 0 (the wiki's 25 / 4, no fade)
#     8011/8012  Kolczan for 1 day / 7 days (General Store, 100 000 / 550 000 Yang): copies of 8010 with their own
#                LIMIT_REAL_TIME (86 400 / 604 800 s) and price
#     30395      Plonaca Strzala (Balathor's Hwacha arrow; was Ognista Strzala)
#   item_list.txt (gamedata): 8011 / 8012 with 8010's icon (an arrow has no model)
#   itemdesc.txt (dbdata locale/pl): 8010-8012 and 30395
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/strzaly/patch_strzaly_client.py <item_proto> <item_list.txt> <itemdesc.txt> [<out dir>]
# Without an out dir the three files are rewritten in place. Idempotent: a second run changes nothing.
# The client item record (184 bytes, offsets as in tools/quiver): vnum 0, name 8 (33), locale name 41 (33), type 74,
# subtype 75, stack 78, antiflags 82, flags 86, wear 90, buy 98 (int64), sell 106 (int64), limits 114 (2 x 5),
# applies 124 (3 x 5), values 139 (6 x 4), refined vnum 175, refine set 179.
import os
import struct
import sys

sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
ITEM_KEY = (173217, 72619434, 408587239, 27973291)
RECORD = 184

# vnum: (level, magic attack, attack) - the wiki
ARROWS = {8000: (0, 1, 3), 8001: (10, 2, 10), 8002: (30, 3, 15), 8003: (40, 4, 17), 8004: (45, 5, 20),
          8005: (50, 4, 25)}
WOODEN_PRICE = 5
QUIVER = 8010
QUIVER_VALUES = (0, 4, 0, 25, 0, 0)
# vnum: (seconds, price, how long in the description)
NEW_QUIVERS = {8011: (86400, 100000, u'1 dzień'), 8012: (604800, 550000, u'7 dni')}
ICON = u'icon/item/08010.tga'
QUIVER_NAME = u'Kołczan'
FLAMING = 30395
FLAMING_NAME = u'Płonąca Strzała'
FLAMING_DESC = (u'Przeciągnij jedną z tych strzał na Hwachę w Krypcie Balathora, aby ją naładować. Służy do zniszczenia '
                u'tarczy Zamrożonego Jaja Smoka. Strzały dają Pradawne Kryształy Lodu.')


def quiver_desc(how_long):
    return (u'Kołczan pełen strzał, które nigdy się nie kończą. Załóż go w miejsce strzał: łuk ninja strzela bez '
            u'zużywania strzał, a obrażenia nie maleją wraz z odległością. Działa %s od zakupu.' % how_long)


DESCS = {QUIVER: (QUIVER_NAME, quiver_desc(u'14 dni')), FLAMING: (FLAMING_NAME, FLAMING_DESC)}
for _v, (_s, _p, _h) in NEW_QUIVERS.items():
    DESCS[_v] = (QUIVER_NAME, quiver_desc(_h))
ALL = sorted(set(ARROWS) | {QUIVER, FLAMING} | set(NEW_QUIVERS))


def fixed(text, size):
    b = text.encode('cp1250')
    assert len(b) < size, text
    return b + b'\0' * (size - len(b))


def want(vnum, r):
    """The record of vnum as the patch leaves it (r: its record, or 8010's for a new quiver)."""
    r = bytearray(r)
    if vnum in ARROWS:
        level, magic, attack = ARROWS[vnum]
        struct.pack_into('<BiBi', r, 114, 1, level, 0, 0)
        struct.pack_into('<BiBiBi', r, 124, 0, 0, 0, 0, 0, 0)
        struct.pack_into('<6i', r, 139, 0, magic, 0, attack, 0, 0)
        if vnum == 8000:
            struct.pack_into('<qq', r, 98, WOODEN_PRICE, WOODEN_PRICE)
    elif vnum == QUIVER or vnum in NEW_QUIVERS:
        struct.pack_into('<I', r, 0, vnum)
        struct.pack_into('<6i', r, 139, *QUIVER_VALUES)
        if vnum in NEW_QUIVERS:
            secs, price, _ = NEW_QUIVERS[vnum]
            lt1, lv1 = struct.unpack_from('<Bi', r, 119)
            struct.pack_into('<BiBi', r, 114, 7, secs, lt1, lv1)
            struct.pack_into('<qq', r, 98, price, price)
    elif vnum == FLAMING:
        r[41:74] = fixed(FLAMING_NAME, 33)
    return bytes(r)


def records(b):
    import m2pack
    assert b[:4] == b'MIPX'
    ver, stride, cnt, size = struct.unpack_from('<IIII', b, 4)
    assert stride == RECORD, stride
    raw = m2pack.mcoz_decode(b[20:], ITEM_KEY)
    return ver, stride, dict((struct.unpack_from('<I', raw, i * RECORD)[0], raw[i * RECORD:(i + 1) * RECORD])
                             for i in range(cnt))


def item_proto(b):
    import m2pack
    ver, stride, recs = records(b)
    missing = [v for v in sorted(set(ARROWS) | {QUIVER, FLAMING}) if v not in recs]
    assert not missing, 'records missing from the client item_proto: %s (tools/quiver, tools/balathor first)' % missing
    changed = 0
    for v in ALL:
        old = recs.get(v)
        new = want(v, old if old is not None else recs[QUIVER])
        if new != old:
            recs[v] = new
            changed += 1
    if not changed:
        return b, 0
    blob = m2pack.mcoz_encode(b''.join(recs[v] for v in sorted(recs)), ITEM_KEY)
    return b'MIPX' + struct.pack('<IIII', ver, stride, len(recs), len(blob)) + blob, changed


def set_rows(b, rows):
    """Each row replaces the lines whose first column is its key, or is appended (before a trailing empty line)."""
    text = b.decode('cp1250')
    nl = '\r\n' if '\r\n' in text else '\n'
    lines = text.split(nl)
    changed = 0
    for row in rows:
        key = row.split('\t')[0]
        hits = [i for i, l in enumerate(lines) if l.split('\t')[0].strip() == key]
        if hits:
            if all(lines[i] == row for i in hits):
                continue
            for i in hits:
                lines[i] = row
        else:
            tail = lines and lines[-1] == ''
            if tail:
                lines.pop()
            lines.append(row)
            if tail:
                lines.append('')
        changed += 1
    if not changed:
        return b, 0
    return nl.join(lines).encode('cp1250'), changed


def list_rows():
    return [u'%d\tWEAPON\t%s' % (v, ICON) for v in sorted(NEW_QUIVERS)]


def desc_rows():
    return [u'%d\t%s\t%s' % (v, DESCS[v][0], DESCS[v][1]) for v in sorted(DESCS)]


def item_list(b):
    return set_rows(b, list_rows())


def itemdesc(b):
    return set_rows(b, desc_rows())


JOBS = {'gamedata/item_proto': item_proto, 'gamedata/item_list.txt': item_list, 'locale/pl/itemdesc.txt': itemdesc}


def main():
    if len(sys.argv) not in (4, 5):
        sys.exit('usage: patch_strzaly_client.py <item_proto> <item_list.txt> <itemdesc.txt> [<out dir>]')
    out_dir = sys.argv[4] if len(sys.argv) == 5 else None
    for path, fn in zip(sys.argv[1:4], (item_proto, item_list, itemdesc)):
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
