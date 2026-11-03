# -*- coding: utf-8 -*-
# MT2009_PLUS_ZODIAC_MERCHANT_V1 - the Kupiec Zodiaku (NPC 20451, shop 41, floor 40 of the Swiatynia Zodiaku) as the
# pl-wiki lists him (the owner, 3 November 2026), the client's side of linux-port/docker/mariadb/playerbot/zodiak_kupiec.sql:
#
#   item_proto (dbdata pack, gamedata/item_proto) - the "gold" the shop's line price is made of (count x gold), so the
#                 client's own records show the same values as the server's: 33032 Pryzmat Ozywienia (Q) 14 500 -> 15 000
#                 (x200 = 3 000 000 Yang), 72329 Pergamin Sfer 100 000 -> 1 000 000, 39068 Zdobna Skrz. z Odlamkiem
#                 0 -> 1 000 000 (each changed only from the old value - another value is left alone);
#   itemdesc.txt (dbdata pack, locale/pl/itemdesc.txt) - Pergamin Sfer 72329 / 72327 (handel): the pl-wiki's text
#                 "Naladuj 30 Animosfer, aby otrzymac wstep do Swiatyni Zodiaku." instead of the package's
#                 "Zaladuj swoje Animosfery o 30 zyc, ...".
#
# Run after patch_zodiak_client.py (it adds these records / lines), on plain copies, in the m2pack-lzo image (MCOZ):
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/zodiak/patch_zodiak_kupiec_client.py <item_proto> <itemdesc.txt>
# Idempotent: a second run changes nothing.
import os
import struct
import sys

sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
ITEM_KEY = (173217, 72619434, 408587239, 27973291)
RECORD = 184
GOLD_OFF = 98   # int64 gold, int64 shop_buy_price (patch_zodiak_client.item_record)

# vnum: (old gold, new gold)
GOLD = {33032: (14500, 15000), 72329: (100000, 1000000), 39068: (0, 1000000)}

DESC = {
    '72329': u'72329\tPergamin Sfer\tNaładuj 30 Animosfer, aby otrzymać wstęp do Świątyni Zodiaku.',
    '72327': u'72327\tPergamin Sfer (handel)\tNaładuj 30 Animosfer, aby otrzymać wstęp do Świątyni Zodiaku. '
             u'Przedmiot zdatny do handlu.',
}


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
        if vnum not in GOLD:
            continue
        seen.add(vnum)
        old, new = GOLD[vnum]
        gold = struct.unpack_from('<q', r, GOLD_OFF)[0]
        if gold == old:
            r = bytearray(r)
            struct.pack_into('<q', r, GOLD_OFF, new)
            recs[i] = bytes(r)
            changed += 1
        elif gold != new:
            print('item_proto: %d has gold %d (not %d / %d) - left alone' % (vnum, gold, old, new))
    missing = sorted(set(GOLD) - seen)
    assert not missing, 'records missing from the client item_proto: %s' % missing
    if not changed:
        return b, 0
    blob = m2pack.mcoz_encode(b''.join(recs), ITEM_KEY)
    return b'MIPX' + struct.pack('<IIII', ver, stride, cnt, len(blob)) + blob, changed


def itemdesc(b):
    text = b.decode('cp1250')
    nl = '\r\n' if '\r\n' in text else '\n'
    lines = text.split(nl)
    changed, seen = 0, set()
    for i, l in enumerate(lines):
        k = l.split('\t')[0].strip()
        if k in DESC:
            seen.add(k)
            if l.rstrip('\r') != DESC[k]:
                lines[i] = DESC[k]
                changed += 1
    missing = sorted(set(DESC) - seen)
    assert not missing, 'itemdesc.txt lines missing: %s' % missing
    return nl.join(lines).encode('cp1250'), changed


def main():
    if len(sys.argv) != 3:
        sys.exit('usage: patch_zodiak_kupiec_client.py <item_proto> <itemdesc.txt>')
    for path, fn, what in ((sys.argv[1], item_proto, 'item_proto'), (sys.argv[2], itemdesc, 'itemdesc.txt')):
        b = open(path, 'rb').read()
        nb, n = fn(b)
        if nb != b:
            open(path, 'wb').write(nb)
        print('%s: %d changed (Kupiec Zodiaku) -> %s' % (what, n, path))


if __name__ == '__main__':
    main()
