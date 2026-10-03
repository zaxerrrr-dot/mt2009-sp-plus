# Digi Rasta's systems (nowy-system v0.16, "Autor: Digi Rasta") in the client:
# the same rows linux-port/docker/mariadb/playerbot/apply.sh writes into the
# world, so the tooltip shows what the server does. Idempotent: a second run
# changes nothing.
#
#   MT2009_PLUS_AWAKENING_V1   the seven awakened weapon families +0..+9 (210,
#                              220, 1160, 2190, 3170, 5150, 7170): levels 90..105,
#                              strong vs people -15..-50%, vs monsters +2..+15%,
#                              attack 98% of the base weapon's +9, three sockets,
#                              refine chain 7100+n; Kamien Przebudzenia (30670) -
#                              a new record (a copy of 30228, stack 200), its
#                              item_list.txt line and its itemdesc.txt line;
#   MT2009_PLUS_SOULSTONE9_V1  the soul stones +5..+9 (28530+k, 28g00+k): type
#                              METIN, the kind's bonus and wear flag, the kind in
#                              value5 (17+k);
#   MT2009_PLUS_HORSE30_V1     the level-30 horse (race 20119) is "Czarny Rumak"
#                              in mob_proto;
#   MT2009_PLUS_HEAVEN_OIL_V1  (Autor: Digi Rasta, nowy-system v0.17 / 0.17.2)
#                              Olejek Niebios (71056) a plain material as the
#                              server makes it (type 5/0, stack 200, flag 4, no
#                              values - his OLEJEK_NIEBIOS) and its itemdesc.txt
#                              line rewritten (the old one promised a better
#                              refine chance); and his item_list fixes: 7170
#                              (Wachlarz Lezac. Smoka+0) takes its family's icon
#                              07180.tga instead of the 8 Trigrams' 07170.tga
#                              (icon column only), and 22030 (Zwoj Teleportu)
#                              gets the row it lacks (icon of 22000).
#
# His klient.py carried the same tables (FAMILIES, STONES, MOB_NAZWY); keep
# them equal to apply.sh.
#
# Run on the current files (plain copies out of the gamedata and locale packs),
# in the m2pack-lzo image for the protos' MCOZ:
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/digirasta/patch_digirasta_client.py \
#     <item_proto> <item_list.txt> <itemdesc.txt> <mob_proto> [<out dir>]
# Without an out dir the four files are rewritten in place. 30670 is a new
# item_proto record and a new line in two text files - no new pack entry.
#
# The client item record (184 bytes, TItemTable_r156; offsets as in
# tools/seonhae/patch_seonhae_client.py): vnum 0, name 8 (33), locale name 41
# (33), type 74, subtype 75, stack 78, antiflags 82, flags 86, wear 90, immune
# 94, buy 98 (int64), sell 106 (int64), limits 114 (2 x 5), applies 124 (3 x 5),
# values 139 (6 x 4), sockets 163, refined vnum 175, refine set 179, magic %
# 181, specular 182, socket % 183. The mob record (256 bytes, MMPT): the
# locale name at 29 (25).
import os
import struct
import sys

sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
ITEM_KEY = (173217, 72619434, 408587239, 27973291)
MOB_KEY = (4813894, 18955, 552631, 6822045)
RECORD = 184
MOB_RECORD = 256

STONE_VNUM = 30670
STONE_TEMPLATE = 30228  # Kamien Dusz Beran-Setaou: record and icon
STONE_NAME = u'Kamień Przebudzenia'
STONE_DESC = (u'Rzadki kamień z bossów. U Kowala przemienia broń 75. poziomu +9 '
              u'w broń przebudzoną +0, zachowując bonusy i kamienie '
              u'(koszt: 200 000 000 Yang).')

LEVELS = (90, 92, 93, 95, 97, 98, 100, 102, 103, 105)
SPECULAR = (0, 0, 0, 0, 30, 40, 50, 65, 80, 100)
HUMAN = (-15, -19, -23, -27, -31, -35, -39, -43, -47, -50)   # apply 43, negative: no PvP weapon
MONSTER = (2, 3, 5, 6, 8, 9, 11, 12, 14, 15)                  # apply 53
CURVE = (0, 0.04, 0.056, 0.088, 0.132, 0.2, 0.296, 0.444, 0.668, 1)
PRICE = 12474000
# base +0, subtype, antiflag, attack speed, magic min/max, attack min/max, V9
FAMILIES = (
    (210, 0, 32, 26, 0, 0, 232, 271, 181),      # Smiercionosne Ostrze
    (220, 0, 44, 26, 160, 205, 221, 246, 192),  # Ksiezycowy Miecz
    (1160, 1, 52, 26, 0, 0, 216, 224, 264),     # Noz Strumienia
    (2190, 2, 52, 26, 0, 0, 274, 372, 322),     # Upiorna Kusza
    (3170, 3, 56, 30, 0, 0, 260, 290, 230),     # Zabojca Zolt. Smoka
    (5150, 4, 28, 26, 203, 213, 207, 242, 223), # Hibiskusowy Dzwon
    (7170, 5, 28, 15, 208, 229, 192, 222, 171), # Wachlarz Lezac. Smoka
)
# Soul stones +5..+9: (apply, wear, values +5..+9) of kind k = 0..13.
STONES = (
    (41, 16, (9, 10, 11, 13, 15)),          # Penetracji
    (40, 16, (9, 10, 11, 13, 15)),          # Smierci
    (21, 16, (28, 31, 34, 37, 40)),         # Powtorki
    (54, 16, (27, 29, 31, 33, 35)),         # Wojownika
    (55, 16, (27, 29, 31, 33, 35)),         # Ninja
    (56, 16, (27, 29, 31, 33, 35)),         # Sury
    (57, 16, (27, 29, 31, 33, 35)),         # Szamana
    (53, 16, (10, 12, 15, 17, 20)),         # Potwora
    (67, 1, (10, 11, 12, 13, 15)),          # Uchylenia
    (68, 1, (10, 11, 12, 13, 15)),          # Uniku
    (8, 1, (700, 850, 1000, 1250, 1500)),   # Magii
    (6, 1, (1200, 1600, 2000, 2500, 3000)), # Witalnosci
    (96, 1, (40, 55, 70, 85, 100)),         # Obrony
    (19, 1, (32, 34, 36, 38, 40)),          # Przyspieszenia
)
MOB_NAMES = ((20119, u'Czarny Rumak'),)

# MT2009_PLUS_HEAVEN_OIL_V1 (Autor: Digi Rasta, v0.17): = 71056 in apply.sh and
# HEAVEN_OIL_BOSS_DROPS in playerbot_awakening.h (the three bosses below).
OIL_VNUM = 71056
OIL_NAME = u'Olejek Niebios'
OIL_DESC = (u'Składnik ulepszania Kamieni Duszy u Kowala (od +4): potrzeba 1, 1, 2, 2, 3 sztuk '
            u'na kolejne stopnie, obok Magicznego Pyłu. Wypada z Silnej Lodowej Wiedźmy '
            u'(Grota Wygnańców), Beran-Setaou (Leże Smoka) i Królowej Dżungli (Starożytna Dżungla).')
# His item_list fixes (v0.17.2, IKONY_POPRAWKI / IKONY_DODATKOWE): vnum -> icon.
ICON_FIXES = {7170: 'icon/item/07180.tga'}   # Wachlarz Lezac. Smoka+0: its family's icon, not the 8 Trigrams'
ICON_ROWS = ['22030\tETC\ticon/item/22000.tga']  # Zwoj Teleportu: the mod has no item_list row


def fixed(text, size):
    b = text.encode('cp1250')
    assert len(b) < size, text
    return b + b'\0' * (size - len(b))


def set_weapon(r, vnum, n, sub, anti, speed, mmin, mmax, amin, amax, v9, last):
    struct.pack_into('<BB', r, 74, 1, sub)
    struct.pack_into('<IIII', r, 82, anti, 1, 16, 0)
    struct.pack_into('<qq', r, 98, PRICE, PRICE)
    struct.pack_into('<BiBi', r, 114, 1, LEVELS[n], 0, 0)
    struct.pack_into('<BiBiBi', r, 124, 17, speed, 43, HUMAN[n], 53, MONSTER[n])
    struct.pack_into('<6i', r, 139, 0, mmin, mmax, amin, amax, int(round(v9 * CURVE[n])))
    struct.pack_into('<IH', r, 175, 0 if last else vnum + 1, 0 if last else 7100 + n)
    struct.pack_into('<BBB', r, 181, 0, SPECULAR[n], 3)


def item_proto(b):
    import m2pack
    assert b[:4] == b'MIPX'
    ver, stride, cnt, size = struct.unpack_from('<IIII', b, 4)
    assert stride == RECORD, stride
    raw = m2pack.mcoz_decode(b[20:], ITEM_KEY)
    recs = dict((struct.unpack_from('<I', raw, i * RECORD)[0], raw[i * RECORD:(i + 1) * RECORD]) for i in range(cnt))
    changed = 0
    for base, sub, anti, speed, mmin, mmax, amin, amax, v9 in FAMILIES:
        for n in range(10):
            r = bytearray(recs[base + n])
            set_weapon(r, base + n, n, sub, anti, speed, mmin, mmax, amin, amax, v9, n == 9)
            if bytes(r) != recs[base + n]:
                recs[base + n] = bytes(r)
                changed += 1
    for k, (ap, wear, vals) in enumerate(STONES):
        for i, val in enumerate(vals):
            g = 5 + i
            vnum = 28030 + g * 100 + k if g == 5 else 28000 + g * 100 + k
            r = bytearray(recs[vnum])
            struct.pack_into('<BB', r, 74, 10, 0)
            struct.pack_into('<I', r, 90, wear)
            struct.pack_into('<BiBi', r, 124, ap, val, 0, 0)
            struct.pack_into('<i', r, 139, 0)
            struct.pack_into('<i', r, 159, 17 + k)
            struct.pack_into('<IH', r, 175, 0, 0)
            if bytes(r) != recs[vnum]:
                recs[vnum] = bytes(r)
                changed += 1
    # MT2009_PLUS_HEAVEN_OIL_V1: Olejek Niebios as the server's 66_olejek row.
    if OIL_VNUM in recs:
        r = bytearray(recs[OIL_VNUM])
        struct.pack_into('<BB', r, 74, 5, 0)
        struct.pack_into('<IIIII', r, 78, 200, 0, 4, 0, 0)
        struct.pack_into('<6i', r, 139, 0, 0, 0, 0, 0, 0)
        if bytes(r) != recs[OIL_VNUM]:
            recs[OIL_VNUM] = bytes(r)
            changed += 1
    if STONE_VNUM not in recs:
        r = bytearray(recs[STONE_TEMPLATE])
        struct.pack_into('<II', r, 0, STONE_VNUM, 0)
        r[8:41] = fixed(u'Awakening Stone', 33)
        r[41:74] = fixed(STONE_NAME, 33)
        struct.pack_into('<I', r, 78, 200)
        struct.pack_into('<I', r, 86, struct.unpack_from('<I', r, 86)[0] | 4)
        recs[STONE_VNUM] = bytes(r)
        changed += 1
    if not changed:
        return b, 0
    out = b''.join(recs[v] for v in sorted(recs))
    blob = m2pack.mcoz_encode(out, ITEM_KEY)
    return b'MIPX' + struct.pack('<IIII', ver, stride, len(recs), len(blob)) + blob, changed


def mob_proto(b):
    import m2pack
    assert b[:4] == b'MMPT'
    cnt, size = struct.unpack_from('<II', b, 4)
    raw = bytearray(m2pack.mcoz_decode(b[12:], MOB_KEY))
    assert len(raw) == cnt * MOB_RECORD, (len(raw), cnt)
    changed = 0
    for i in range(cnt):
        vnum = struct.unpack_from('<I', raw, i * MOB_RECORD)[0]
        for v, name in MOB_NAMES:
            if vnum == v:
                off = i * MOB_RECORD + 29
                want = fixed(name, 25)
                if bytes(raw[off:off + 25]) != want:
                    raw[off:off + 25] = want
                    changed += 1
    if not changed:
        return b, 0
    blob = m2pack.mcoz_encode(bytes(raw), MOB_KEY)
    return b'MMPT' + struct.pack('<II', cnt, len(blob)) + blob, changed


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


def set_rows(b, rows):
    """Every line whose first column is a row's replaced by that row (or the row
    appended): the itemdesc lines whose text we change on purpose."""
    text = b.decode('cp1250')
    nl = '\r\n' if '\r\n' in text else '\n'
    lines = text.split(nl)
    changed = 0
    for r in rows:
        key = r.split('\t')[0]
        hit = False
        for i, l in enumerate(lines):
            if l.split('\t')[0].strip() == key:
                hit = True
                if l != r:
                    lines[i] = r
                    changed += 1
        if not hit:
            nb, added = append_rows(nl.join(lines).encode('cp1250'), [r])
            lines = nb.decode('cp1250').split(nl)
            changed += added
    return nl.join(lines).encode('cp1250'), changed


def fix_icons(b):
    """MT2009_PLUS_HEAVEN_OIL_V1 (Autor: Digi Rasta, v0.17.2): ICON_FIXES - the
    icon column (the third) of those rows only."""
    text = b.decode('cp1250')
    nl = '\r\n' if '\r\n' in text else '\n'
    lines = text.split(nl)
    changed = 0
    for i, l in enumerate(lines):
        p = l.split('\t')
        if len(p) > 2 and p[0].strip().isdigit() and int(p[0]) in ICON_FIXES and p[2].strip() != ICON_FIXES[int(p[0])]:
            p[2] = ICON_FIXES[int(p[0])]
            lines[i] = '\t'.join(p)
            changed += 1
    return nl.join(lines).encode('cp1250'), changed


def item_list_rows(b):
    text = b.decode('cp1250')
    icon = 'icon/item/30228.tga'
    for l in text.splitlines():
        if l.startswith('%d\t' % STONE_TEMPLATE):
            icon = l.split('\t')[2].strip()
    b, added = append_rows(b, ['%d\tETC\t%s' % (STONE_VNUM, icon)] + ICON_ROWS)
    b, fixed_n = fix_icons(b)
    return b, added + fixed_n


def itemdesc_rows(b):
    b, added = append_rows(b, [u'%d\t%s\t%s' % (STONE_VNUM, STONE_NAME, STONE_DESC)])
    b, set_n = set_rows(b, [u'%d\t%s\t%s' % (OIL_VNUM, OIL_NAME, OIL_DESC)])
    return b, added + set_n


def main():
    if len(sys.argv) not in (5, 6):
        sys.exit('usage: patch_digirasta_client.py <item_proto> <item_list.txt> <itemdesc.txt> <mob_proto> [<out dir>]')
    proto_p, list_p, desc_p, mob_p = sys.argv[1:5]
    out_dir = sys.argv[5] if len(sys.argv) == 6 else None
    jobs = [
        (proto_p, item_proto),
        (list_p, item_list_rows),
        (desc_p, itemdesc_rows),
        (mob_p, mob_proto),
    ]
    for path, fn in jobs:
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
