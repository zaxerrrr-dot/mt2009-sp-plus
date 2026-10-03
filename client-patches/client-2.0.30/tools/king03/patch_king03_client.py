# MT2009_PLUS_WARRIOR_KING03_V1: two ItemShop cosmetics from the owner's
# packages (3 October: "Dodaj ta zbroje i bron jako kostium i nakladke. Zbroja
# to warrior king03. Dodaj standardowo do itemshopa"), in the client - the same
# rows linux-port/docker/mariadb/playerbot/apply.sh writes into the world, so
# the tooltip shows what the server does. Idempotent: a second run changes
# nothing.
#
#   41986  Zbroja Krola Wojownikow+  costume body (COSTUME 28 / BODY 0), a
#          copy of Wiking Swiatla+ (41982): 30 days LIMIT_REAL_TIME, no drop /
#          PK drop / stack, specular 100; MALE WARRIOR ONLY - antiflag 49337 =
#          the template's 49281 (female | drop | PK drop | stack) + assassin
#          8 + sura 16 + shaman 32. The package has no female model (its
#          README: the female MSM wants pc2/warrior/warrior_lord.GR2 with a
#          warrior_king03.dds that was never shipped). Shape 41986 (value3)
#          only in gamedata/warrior_m.msm: the package's male warrior_lord
#          mesh as warrior_king03.gr2 (+ _lod_01..03), its source skin
#          warrior_king01.dds (the base pc_1 file the mesh names) swapped for
#          the new warrior_king03.dds (1024x1024 DXT3).
#   40233  Swiety Miecz Bogow+  weapon skin (COSTUME 28 / WEAPON 4), a copy of
#          Miecz Smoka Polnocy+ (40227): one-handed sword (value3 0), warrior /
#          ninja / sura (antiflag 49312, as every sword skin), 30 days. Model
#          d:/ymir work/item/weapon/costume/40233.gr2 (the package's 07300.gr2
#          - renamed: GF has its own, different 07300.gr2), texture
#          d:/ymir work/item/weapon/bamboomt2_0005.dds (the path the gr2 names).
#
# Rows: gamedata/gf_official_costumes.txt (two lines - the client's legacy
# item_proto has none of the 40xxx/41xxx ItemShop cosmetics; the exe's
# CItemManager::LoadItemTable reads them from this 24-column table after the
# proto, GameLib/ItemManager.cpp), item_list.txt (two lines: icon, and the
# weapon's model), itemdesc.txt (two lines: the description), and
# gamedata/warrior_m.msm (one ShapeData group, ShapeDataCount + 1).
# New pack entries (no row here): assets/ next to this script - icon/item/
# 41986.tga and 40233.tga (icon pack), and the d_/ymir work/... files as
# d:/ymir work/... (see /opt/metin2/cache/c53-staging/README.txt).
#
# Run on the current files (plain copies out of the gamedata and locale packs);
# plain Python 3, no image needed:
#   python3 \
#     <repo>/client-patches/client-2.0.30/tools/king03/patch_king03_client.py \
#     <gf_official_costumes.txt> <item_list.txt> <itemdesc.txt> <warrior_m.msm> [<out dir>]
# Without an out dir the four files are rewritten in place.
#
# gf_official_costumes.txt columns (tab, cp1250, LF): 0 vnum, 1 name (the exe
# keeps 24 bytes), 2 subtype, 3 size, 4 antiflags, 5 flags, 6-9 two limits,
# 10-15 three applies, 16-21 values 0-5, 22 specular, 23 the vnum again. The
# type is always ITEM_COSTUME (28).
import os
import sys

BODY_VNUM = 41986
BODY_TEMPLATE = 41982          # Wiking Swiatla+ (m), 30 days, ItemShop
BODY_NAME = u'Zbroja Króla Wojowników+'
BODY_DESC = (u'Królewska zbroja wojownika. Kostium tylko dla wojownika '
             u'(postać męska). Działa 30 dni od zakupu.')
BODY_ANTIFLAG = 49281 | 8 | 16 | 32   # 49337: male warrior only
BODY_SHAPE = 41986
BODY_ICON = 'icon/item/41986.tga'

WEAPON_VNUM = 40233
WEAPON_TEMPLATE = 40227        # Miecz Smoka Polnocy+, sword skin, 30 days
WEAPON_NAME = u'Święty Miecz Bogów+'
WEAPON_DESC = (u'Nakładka na broń jednoręczną (miecz) - wojownik, ninja, sura. '
               u'Działa 30 dni od zakupu.')
WEAPON_ICON = 'icon/item/40233.tga'
WEAPON_MODEL = 'd:/ymir work/item/weapon/costume/40233.gr2'

MSM_GROUP = (
    '\tGroup ShapeData%d\n'
    '\t{\n'
    '\t\tShapeIndex\t\t\t%d\n'
    '\t\tSpecialPath\t\t\t"d:/ymir Work/pc/warrior/"\n'
    '\t\tModel\t\t\t\t"warrior_king03.gr2"\n'
    '\t\tSourceSkin\t\t\t"warrior_king01.dds"\n'
    '\t\tTargetSkin\t\t\t"warrior_king03.dds"\n'
    '\t}\n')


def set_row(b, row):
    """The line whose first column is the row's replaced by it, or the row
    appended (before a trailing empty line)."""
    text = b.decode('cp1250')
    nl = '\r\n' if '\r\n' in text else '\n'
    lines = text.split(nl)
    key = row.split('\t')[0]
    hits = [i for i, l in enumerate(lines) if l.split('\t')[0].strip() == key]
    if hits:
        if all(lines[i] == row for i in hits):
            return b, 0
        for i in hits:
            lines[i] = row
    else:
        tail = lines and lines[-1] == ''
        if tail:
            lines.pop()
        lines.append(row)
        if tail:
            lines.append('')
    return nl.join(lines).encode('cp1250'), 1


def set_rows(b, rows):
    n = 0
    for row in rows:
        b, c = set_row(b, row)
        n += c
    return b, n


def costume_rows(b):
    """Two lines of gf_official_costumes.txt, each built from its template's
    line (so a rerun gives the same text)."""
    rows = dict((l.split('\t')[0], l.split('\t')) for l in b.decode('cp1250').replace('\r\n', '\n').split('\n')
                if l and not l.startswith('#'))
    body = list(rows[str(BODY_TEMPLATE)])
    assert len(body) == 24 and body[2] == '0', body
    body[0] = body[23] = str(BODY_VNUM)
    body[1] = BODY_NAME
    body[4] = str(BODY_ANTIFLAG)
    body[19] = str(BODY_SHAPE)
    weapon = list(rows[str(WEAPON_TEMPLATE)])
    assert len(weapon) == 24 and weapon[2] == '4' and weapon[19] == '0', weapon   # COSTUME_WEAPON, sword
    weapon[0] = weapon[23] = str(WEAPON_VNUM)
    weapon[1] = WEAPON_NAME
    for name in (BODY_NAME, WEAPON_NAME):
        assert len(name.encode('cp1250')) <= 24, name
    return set_rows(b, ['\t'.join(body), '\t'.join(weapon)])


def item_list_rows(b):
    return set_rows(b, ['%d\tARMOR\t%s' % (BODY_VNUM, BODY_ICON),
                        '%d\tWEAPON\t%s\t%s' % (WEAPON_VNUM, WEAPON_ICON, WEAPON_MODEL)])


def itemdesc_rows(b):
    return set_rows(b, [u'%d\t%s\t%s' % (BODY_VNUM, BODY_NAME, BODY_DESC),
                        u'%d\t%s\t%s' % (WEAPON_VNUM, WEAPON_NAME, WEAPON_DESC)])


def msm_rows(b):
    """gamedata/warrior_m.msm: shape BODY_SHAPE as the last group of the
    ShapeData block, ShapeDataCount + 1. The file mixes CRLF and LF; only the
    count line and the inserted lines change."""
    text = b.decode('cp1250')
    if ('ShapeIndex\t\t\t%d\n' % BODY_SHAPE) in text.replace('\r\n', '\n'):
        return b, 0
    lines = text.splitlines(True)
    start = next(i for i, l in enumerate(lines) if l.strip() == 'Group ShapeData')
    end = next(i for i in range(start + 1, len(lines)) if lines[i].rstrip('\r\n') == '}')
    cnt_i = next(i for i in range(start, end) if lines[i].strip().startswith('ShapeDataCount'))
    cnt = int(lines[cnt_i].split()[1])
    groups = sum(1 for i in range(start + 1, end) if lines[i].strip().startswith('Group ShapeData'))
    assert groups == cnt, (groups, cnt)
    lines[cnt_i] = lines[cnt_i].replace(str(cnt), str(cnt + 1), 1)
    lines[end:end] = ['\n', MSM_GROUP % (cnt, BODY_SHAPE)]
    return ''.join(lines).encode('cp1250'), 1


def main():
    if len(sys.argv) not in (5, 6):
        sys.exit('usage: patch_king03_client.py <gf_official_costumes.txt> <item_list.txt> <itemdesc.txt> '
                 '<warrior_m.msm> [<out dir>]')
    out_dir = sys.argv[5] if len(sys.argv) == 6 else None
    for path, fn in zip(sys.argv[1:5], (costume_rows, item_list_rows, itemdesc_rows, msm_rows)):
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
