# -*- coding: utf-8 -*-
# MT2009_PLUS_ELEMENTS_V1 - Elements and talismans (Zywioly i talizmany) in the client's data.
# Autor: Digi Rasta (nowy-system 0.28.0, SYSTEMY/zywioly-talizmany.md; his klient.py
# patch_talizmany / ustaw_zywiol), ported into MT2009 PLUS with the owner's rules of 7 October 2026.
#
#   item_proto    the talismans +0..+200 of the six elements (94000-94200 Ognia, 94250 Blyskawicy,
#                 94500 Lodu, 94750 Wiatru, 95000 Ziemi, 95250 Mroku) and Kwiat Zywiolu (95500) -
#                 equal to the server's linux-port/docker/mariadb/playerbot/zywioly_talizmany.sql
#                 (both from tools/zywioly/zywioly_dane.py); a talisman is armour subtype 7
#                 (ARMOR_PENDANT, WEARABLE_PENDANT) built on 16120's record, the flower on 30031's;
#   item_list.txt one line each (the icons: root/icon/item/<+0 vnum>.tga, 95500.tga);
#   itemdesc.txt  one line each;
#   mob_proto     the monsters' elements, dwRaceFlag bits 11-16 (offset 83 of the 256-byte record)
#                 = tools/zywioly/zywioly_moby.json (the server's zywioly_moby.sql, same generator):
#                 set on the mapped mobs, cleared on every other one - the target's element icon
#                 (ENABLE_ELEMENTAL_TARGET, root/uitarget.py) shows what the server applies.
# Idempotent: a second run changes nothing; a record or line that is there is rewritten only when
# it differs. Any of the four files may be given as "-" to leave it alone.
#
# From client 2.0.52 item_proto and itemdesc.txt live in the "dbdata" pack (gamedata/item_proto,
# locale/pl/itemdesc.txt), item_list.txt and mob_proto in "gamedata" (gamedata/...). Run on plain
# copies (never on /opt/metin2/cache/c57/data itself), in the m2pack-lzo image for the MCOZ:
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/zywioly/patch_zywioly_client.py \
#     <item_proto> <item_list.txt> <itemdesc.txt> <mob_proto> [<out dir>]
# Without an out dir the files are rewritten in place. Then the next client's dbdata base for the
# panel's database editor: python3 -m m2clientpack.make_base <client>/pack <version>
# (linux-port/docker/seban-panel, see /opt/metin2/cache/klient-do-zbudowania.md).
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'tools', 'zywioly'))
sys.path.insert(0, os.path.join(HERE, '..', 'monstercard'))
sys.path.insert(0, '/opt/metin2/cache/cli')
import zywioly_dane as d  # noqa: E402
from patch_monstercard_client import ITEM_KEY, RECORD, fixed  # noqa: E402

MOB_KEY = (4813894, 18955, 552631, 6822045)
MOB_RECORD = 256
MOB_RACE_FLAG = 83
ELEMENT_MASK = 0x1F800
TALISMAN_TEMPLATE = 16120   # Perlowy Naszyjnik+0 (armour record layout)
FLOWER_TEMPLATE = 30031     # Ornament (material)
MOBS_JSON = os.path.join(REPO, 'tools', 'zywioly', 'zywioly_moby.json')


def talisman_records(recs):
    out = {}
    for vnum, nr, n, nazwa, ascii_, punkt, opis, ikona in d.talizmany():
        r = bytearray(recs[TALISMAN_TEMPLATE])
        struct.pack_into('<II', r, 0, vnum, 0)
        r[8:41] = fixed(ascii_, 33)
        r[41:74] = fixed(nazwa, 33)
        struct.pack_into('<BBBB', r, 74, d.ITEM_ARMOR, d.ARMOR_PENDANT, 0, 1)      # type, subtype, weight, size
        struct.pack_into('<IIIII', r, 78, 1, 0, 0, d.WEARABLE_PENDANT, 0)          # stack, anti, flags, wear, immune
        struct.pack_into('<qq', r, 98, d.TALIZMAN_CENA, d.TALIZMAN_CENA)
        struct.pack_into('<BiBi', r, 114, d.LIMIT_LEVEL, d.poziom_gracza(n), 0, 0)
        struct.pack_into('<BiBiBi', r, 124, punkt, n, 0, 0, 0, 0)
        struct.pack_into('<6i', r, 139, 0, 0, 0, 0, 0, 0)
        struct.pack_into('<3i', r, 163, 0, 0, 0)
        struct.pack_into('<IHBBB', r, 175, vnum + 1 if n < d.MAKS else 0, d.refine_set(nr, n), 0, 0, 0)
        out[vnum] = bytes(r)
    r = bytearray(recs[FLOWER_TEMPLATE])
    struct.pack_into('<II', r, 0, d.KWIAT, 0)
    r[8:41] = fixed(u'Kwiat Zywiolu', 33)
    r[41:74] = fixed(d.KWIAT_NAZWA, 33)
    struct.pack_into('<BB', r, 74, d.ITEM_MATERIAL, 0)
    struct.pack_into('<IIIII', r, 78, d.STACK, 0, d.ITEM_FLAG_STACKABLE, 0, 0)
    struct.pack_into('<qq', r, 98, d.KWIAT_CENA, d.KWIAT_SKUP)
    out[d.KWIAT] = bytes(r)
    return out


def item_proto(b):
    import m2pack
    assert b[:4] == b'MIPX'
    ver, stride, cnt, size = struct.unpack_from('<IIII', b, 4)
    assert stride == RECORD, stride
    raw = m2pack.mcoz_decode(b[20:], ITEM_KEY)
    recs = dict((struct.unpack_from('<I', raw, i * RECORD)[0], raw[i * RECORD:(i + 1) * RECORD]) for i in range(cnt))
    ours = d.vnumy()
    changed = 0
    for vnum, r in talisman_records(recs).items():
        if recs.get(vnum) != r:
            recs[vnum] = r
            changed += 1
    stray = [v for v in recs if 94000 <= v <= 95500 and v not in ours]
    if stray:
        raise SystemExit('item_proto: vnums of the talismans\' range that are not ours: %s' % stray[:10])
    if not changed:
        return b, 0
    out = b''.join(recs[v] for v in sorted(recs))
    blob = m2pack.mcoz_encode(out, ITEM_KEY)
    return b'MIPX' + struct.pack('<IIII', ver, stride, len(recs), len(blob)) + blob, changed


def mob_proto(b):
    import m2pack
    magic, cnt, esize = struct.unpack_from('<4sII', b, 0)
    assert magic == b'MMPT', magic
    raw = bytearray(m2pack.mcoz_decode(b[12:12 + esize], MOB_KEY))
    assert len(raw) == cnt * MOB_RECORD, (len(raw), cnt)
    want = dict((int(k), v) for k, v in json.load(open(MOBS_JSON)).items())
    changed = seen = 0
    for i in range(cnt):
        off = i * MOB_RECORD
        vnum = struct.unpack_from('<I', raw, off)[0]
        old = struct.unpack_from('<I', raw, off + MOB_RACE_FLAG)[0]
        new = (old & ~ELEMENT_MASK) | want.get(vnum, 0)
        seen += vnum in want
        if new != old:
            struct.pack_into('<I', raw, off + MOB_RACE_FLAG, new)
            changed += 1
    print('mob_proto: %d of the %d mapped monsters are in the client' % (seen, len(want)))
    if not changed:
        return b, 0
    blob = m2pack.mcoz_encode(bytes(raw), MOB_KEY)
    return struct.pack('<4sII', b'MMPT', cnt, len(blob)) + blob, changed


def set_rows(b, rows):
    """Every line whose first column is a row's key becomes that row (or the row is appended);
    keeps the file's line ends."""
    text = b.decode('cp1250')
    nl = '\r\n' if '\r\n' in text else '\n'
    lines = text.split(nl)
    tail = lines and lines[-1] == ''
    if tail:
        lines.pop()
    want = dict((r.split('\t')[0], r) for r in rows)
    seen = set()
    changed = 0
    for i, l in enumerate(lines):
        k = l.split('\t')[0].strip()
        if k in want:
            seen.add(k)
            if l != want[k]:
                lines[i] = want[k]
                changed += 1
    for r in rows:
        k = r.split('\t')[0]
        if k not in seen:
            lines.append(r)
            seen.add(k)
            changed += 1
    if tail:
        lines.append('')
    return nl.join(lines).encode('cp1250'), changed


def main():
    if len(sys.argv) not in (5, 6):
        raise SystemExit('usage: patch_zywioly_client.py <item_proto> <item_list.txt> <itemdesc.txt> <mob_proto> [<out dir>]')
    proto_path, list_path, desc_path, mob_path = sys.argv[1:5]
    out_dir = sys.argv[5] if len(sys.argv) == 6 else None
    tal = d.talizmany()
    list_rows = [u'%d\tARMOR\t%s' % (t[0], t[7]) for t in tal] + [u'%d\tETC\t%s' % (d.KWIAT, d.IKONA.format(d.KWIAT))]
    desc_rows = [u'%d\t%s\t%s' % (t[0], t[3], t[6]) for t in tal] + [u'%d\t%s\t%s' % (d.KWIAT, d.KWIAT_NAZWA, d.KWIAT_OPIS)]
    jobs = ((proto_path, item_proto), (list_path, lambda b: set_rows(b, list_rows)),
            (desc_path, lambda b: set_rows(b, desc_rows)), (mob_path, mob_proto))
    for path, fn in jobs:
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
        print('%s: %d change(s)%s' % (os.path.basename(path), changed, '' if target == path else ' -> ' + target))


if __name__ == '__main__':
    main()
