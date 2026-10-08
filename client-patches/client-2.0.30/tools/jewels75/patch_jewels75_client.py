# -*- coding: utf-8 -*-
# MT2009_PLUS_JEWELS75_V1 - the Gameforge jewellery of Rubin, Szmaragd and Szafir at level 75 in
# the client's data (the owner, 8 October 2026: "na 75 lvl chcialbym dodac nowa bizuterie:
# Rubinowa, Szmaragdowa i Szafirowa ... normalnie sa na 85, ale ja chce zeby byly na 75").
#
# The client already had the records (item_proto 14500/14540/14560 bracelets, 16500/16540/16560
# necklaces, 17500/17540/17560 earrings, +0..+9) and the icons (icon pack: icon/item/<+0>.tga; with
# no item_list.txt line the exe falls back to icon/item/<vnum>.tga, then <vnum - vnum % 10>.tga -
# GameLib/ItemManager.cpp - so they showed already). This script:
#   item_proto    the nine families: level limit 75 (Gameforge: Rubin 85, Szmaragd 95, Szafir
#                 100), the earrings' regeneration as Gameforge's today (Szmaragdowe: SP
#                 regeneration, Szafirowe: HP regeneration, 4/5/6/8/10/12/15/18/22/28 % - the
#                 old record had 1..15), the refine chain on their own Blacksmith recipes
#                 7320-7328 (the Granat family 14520/16520/17520 too, at Gameforge's level
#                 90) - all as linux-port/docker/mariadb/playerbot/apply.sh
#                 (MT2009_PLUS_JEWELS75_V1) writes world.item_proto;
#   item_list.txt one line per piece (ARMOR, icon/item/<+0 vnum>.tga, as Gameforge's
#                 item_list) for the nine families and for the Granat family (14520/16520/
#                 17520) - explicit rather than the exe's fallback.
#   and the gems Rubin/Granat/Szmaragd/Szafir (50635-50638) stackable (flag 4) as the other
#   przetopy and as world.item_proto.
# Every other field (names, bonuses, prices) stays. Idempotent: a second run changes nothing.
#
# From client 2.0.52 item_proto lives in the "dbdata" pack (gamedata/item_proto), item_list.txt
# in "gamedata" (gamedata/item_list.txt). Run on plain copies, in the m2pack-lzo image:
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/jewels75/patch_jewels75_client.py \
#     <item_proto> <item_list.txt> [<out dir>]
# Either file may be "-" to leave it alone. Without an out dir the files are rewritten in place.
# Then the next client's dbdata base for the panel's database editor:
#   python3 -m m2clientpack.make_base <client>/pack <version>
import os
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'monstercard'))
sys.path.insert(0, '/opt/metin2/cache/cli')
import patch_monstercard_client as base  # noqa: E402  (the record layout and MCOZ keys)

LEVEL = 75
LIMIT_LEVEL = 1
REFINE_FIRST = 7320          # refine_proto 7320 + n: the step +n -> +n+1 (apply.sh)
# The +0 vnums of the nine families that move to level 75.
FAMILIES = (
    14500, 14540, 14560,     # Rubinowa / Szmaragdowa / Szafirowa Bransoleta
    16500, 16540, 16560,     # Rubinowy / Szmaragdowy / Szafirowy Naszyjnik
    17500, 17540, 17560,     # Rubinowe / Szmaragdowe / Szafirowe Kolczyki
)
GRANAT = (14520, 16520, 17520)   # Gameforge's level 90 kept; the refine chain and item_list lines
REGEN = (4, 5, 6, 8, 10, 12, 15, 18, 22, 28)
GEMS = (50635, 50636, 50637, 50638)   # Rubin, Granat, Szmaragd, Szafir: stackable like the przetopy
ITEM_FLAG_STACKABLE = 4
# The earrings' second bonus (apply slot 1): the type it must already be, the new values.
EARRING_REGEN = {
    17540: (33, REGEN),      # Szmaragdowe Kolczyki: SP regeneration
    17560: (32, REGEN),      # Szafirowe Kolczyki: HP regeneration
}


def item_proto(b):
    import m2pack
    assert b[:4] == b'MIPX'
    ver, stride, cnt, size = struct.unpack_from('<IIII', b, 4)
    assert stride == base.RECORD, stride
    raw = bytearray(m2pack.mcoz_decode(b[20:], base.ITEM_KEY))
    want = dict((first + n, (first, n)) for first in FAMILIES + GRANAT for n in range(10))
    changed = seen = 0
    for i in range(cnt):
        off = i * base.RECORD
        vnum = struct.unpack_from('<I', raw, off)[0]
        if vnum not in want:
            continue
        seen += 1
        first, n = want[vnum]
        r = bytearray(raw[off:off + base.RECORD])
        before = bytes(r)
        if r[74] != 2 or r[75] not in (3, 5, 6):
            raise SystemExit('item_proto: %d is not a bracelet, necklace or earring (%d/%d)' % (vnum, r[74], r[75]))
        if first not in GRANAT:
            struct.pack_into('<Bi', r, 114, LIMIT_LEVEL, LEVEL)                   # limit 0
        if first in EARRING_REGEN:
            kind, values = EARRING_REGEN[first]
            if r[129] != kind:
                raise SystemExit('item_proto: %d has bonus %d where %d was expected' % (vnum, r[129], kind))
            struct.pack_into('<i', r, 130, values[n])                             # apply 1 value
        struct.pack_into('<IH', r, 175, vnum + 1 if n < 9 else 0, REFINE_FIRST + n if n < 9 else 0)
        if bytes(r) != before:
            raw[off:off + base.RECORD] = r
            changed += 1
    if seen != len(want):
        raise SystemExit('item_proto: %d of the %d jewellery records found' % (seen, len(want)))
    gems = 0
    for i in range(cnt):
        off = i * base.RECORD
        vnum = struct.unpack_from('<I', raw, off)[0]
        if vnum in GEMS:
            gems += 1
            flags = struct.unpack_from('<I', raw, off + 86)[0]
            if not flags & ITEM_FLAG_STACKABLE:
                struct.pack_into('<I', raw, off + 86, flags | ITEM_FLAG_STACKABLE)
                changed += 1
    if gems != len(GEMS):
        raise SystemExit('item_proto: %d of the %d gem records found' % (gems, len(GEMS)))
    if not changed:
        return b, 0
    blob = m2pack.mcoz_encode(bytes(raw), base.ITEM_KEY)
    return b'MIPX' + struct.pack('<IIII', ver, stride, cnt, len(blob)) + blob, changed


def item_list(b):
    """Every line whose first column is one of ours becomes ours (or ours is appended);
    keeps the file's line ends."""
    rows = ['%d\tARMOR\ticon/item/%d.tga' % (first + n, first)
            for first in sorted(FAMILIES + GRANAT) for n in range(10)]
    text = b.decode('cp1250')
    nl = '\r\n' if '\r\n' in text else '\n'
    lines = text.split(nl)
    tail = lines and lines[-1] == ''
    if tail:
        lines.pop()
    want = dict((r.split('\t')[0], r) for r in rows)
    seen = set()
    changed = 0
    for i, line in enumerate(lines):
        k = line.split('\t')[0].strip()
        if k in want:
            seen.add(k)
            if line.rstrip('\t ') != want[k]:
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
    if len(sys.argv) not in (3, 4):
        raise SystemExit('usage: patch_jewels75_client.py <item_proto> <item_list.txt> [<out dir>]')
    out_dir = sys.argv[3] if len(sys.argv) == 4 else None
    for path, fn in ((sys.argv[1], item_proto), (sys.argv[2], item_list)):
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
