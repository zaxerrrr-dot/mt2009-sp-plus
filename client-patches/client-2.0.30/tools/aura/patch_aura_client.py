# -*- coding: utf-8 -*-
# MT2009_PLUS_AURA_V1 (client data) - Szata Aury's items in the client (15 October 2026; server-patches/aura):
#
#   49101-49106  Zwyczajna .. Promienista Szata Aury  ITEM_COSTUME / COSTUME_AURA (28/5), specular 100; the official
#                                                     49001-49006 are our Death Ruler skins - icons GF 49001-49006
#   49990        Lodowa Runa Aury                     material, stack 9999 (1 exp; MT2009_PLUS_AURA_RUNE_STACK_V1,
#                                                     10 November 2026 - was 200)
#   49994/49995  Ognista Runa Aury (250) / (500)      material, stack 200 - the icon of 49991 (as GF's item_list)
#   89999        Swiadectwo Aury+                     ITEM_USE / USE_SPECIAL (3/10), stack 200, APPLICABLE (dragged onto
#                                                     an outfit)
#   49991-49993  Ognista Runa Aury (10/50/100) of tools/yohara: value0 = exp, the description without "Na razie bez
#                zastosowania" (the system is here now)
#
# The rows = linux-port/docker/mariadb/playerbot/szata_aury.sql (tools/aura/gen_aura_sql.py) - keep them equal. Each new
# record is a copy of the Zelazna Szkatulka's (50120) with the server columns written over it and the rest cleared (the
# tools/transmutacja way). Icons: client-patches/client-2.0.30/root/icon/item/ (build57.py adds every file there).
# Idempotent. item_proto and itemdesc.txt are in the "dbdata" pack, item_list.txt in "gamedata"; run on plain copies,
# after tools/yohara/patch_yohara_client.py (it writes 49991-49993):
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/aura/patch_aura_client.py \
#     <item_proto> <item_list.txt> <itemdesc.txt> [<out dir>]
# then the next dbdata base for the panel's editor.
import os
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'monstercard'))
import patch_monstercard_client as base  # noqa: E402  (record layout, MCOZ key, the line writer)

TEMPLATE = 50120   # Zelazna Szkatulka

ANTI_DROP, ANTI_GIVE, ANTI_PKDROP, ANTI_STACK, ANTI_MYSHOP, ANTI_SAFEBOX = 1 << 7, 1 << 13, 1 << 14, 1 << 15, 1 << 16, 1 << 17
FLAG_STACKABLE, FLAG_LOG, FLAG_APPLICABLE = 1 << 2, 1 << 13, 1 << 14
AURA_ANTI = ANTI_DROP | ANTI_GIVE | ANTI_PKDROP | ANTI_STACK | ANTI_MYSHOP

D_AURA = u'Możesz przenosić parametry z biżuterii (bransolety, naszyjnika, kolczyków) i tarczy na szatę aury z pewnym stopniem absorpcji - u Theowahdana. Za pomocą run aury możesz ulepszać szatę aury.'
D_RUNE = u'Materiał do ulepszania szaty aury. Udaj się do Theowahdana, aby ulepszyć swoją szatę aury.'

# vnum, name, Polish name, type, subtype, stack, antiflag, flag, value0, specular, icon, description
ITEMS = (
    (49101, u'Ordinary Aura Outfit', u'Zwyczajna Szata Aury', 28, 5, 1, AURA_ANTI, FLAG_LOG, 0, 100, u'icon/item/49101.tga',
     D_AURA + u' Można ją ulepszać do poziomu 49 i rozwijać od poziomu 49.'),
    (49102, u'Simple Aura Outfit', u'Prosta Szata Aury', 28, 5, 1, AURA_ANTI, FLAG_LOG, 0, 100, u'icon/item/49102.tga',
     D_AURA + u' Od poziomu 99 można ją rozwijać.'),
    (49103, u'Noble Aura Outfit', u'Szlachetna Szata Aury', 28, 5, 1, AURA_ANTI, FLAG_LOG, 0, 100, u'icon/item/49103.tga',
     D_AURA + u' Od poziomu 149 można ją rozwijać.'),
    (49104, u'Sparkling Aura Outfit', u'Błyszcząca Szata Aury', 28, 5, 1, AURA_ANTI, FLAG_LOG, 0, 100, u'icon/item/49104.tga',
     D_AURA + u' Od poziomu 199 można ją rozwijać.'),
    (49105, u'Magnificent Aura Outfit', u'Wytworna Szata Aury', 28, 5, 1, AURA_ANTI, FLAG_LOG, 0, 100, u'icon/item/49105.tga',
     D_AURA + u' Od poziomu 249 można ją rozwijać.'),
    (49106, u'Radiant Aura Outfit', u'Promienista Szata Aury', 28, 5, 1, ANTI_PKDROP | ANTI_STACK, FLAG_LOG, 0, 100,
     u'icon/item/49106.tga', u'Możesz przenosić parametry z biżuterii (bransolety, naszyjnika, kolczyków) i tarczy na szatę aury z pewnym stopniem absorpcji - u Theowahdana. Najwyższy poziom: 250 (25% absorpcji). Można nią handlować.'),
    (49990, u'Aura Ice Rune', u'Lodowa Runa Aury', 5, 0, 9999, ANTI_DROP | ANTI_GIVE | ANTI_PKDROP | ANTI_MYSHOP | ANTI_SAFEBOX,
     FLAG_STACKABLE, 1, 0, u'icon/item/49990.tga', D_RUNE + u' Daje 1 punkt doświadczenia szaty. Wypada z potworów.'),
    (49994, u'Aura Fire Rune (250)', u'Ognista Runa Aury (250)', 5, 0, 200, ANTI_DROP | ANTI_PKDROP, FLAG_STACKABLE, 250, 0,
     u'icon/item/49991.tga', D_RUNE + u' Daje 250 punktów doświadczenia szaty.'),
    (49995, u'Aura Fire Rune (500)', u'Ognista Runa Aury (500)', 5, 0, 200, ANTI_DROP | ANTI_PKDROP, FLAG_STACKABLE, 500, 0,
     u'icon/item/49991.tga', D_RUNE + u' Daje 500 punktów doświadczenia szaty.'),
    (89999, u'Aura Certificate+', u'Świadectwo Aury+', 3, 10, 200, ANTI_DROP | ANTI_GIVE | ANTI_PKDROP | ANTI_MYSHOP,
     FLAG_STACKABLE | FLAG_APPLICABLE, 0, 0, u'icon/item/89999.tga',
     u'Za pomocą tego przedmiotu możesz usunąć wszystkie zarejestrowane wartości szaty aury. Przeciągnij na szatę aury w ekwipunku (nie założoną) - poziom szaty zostaje.'),
)
# the Ognista Runy of tools/yohara (their records and item_list lines stay; value0 and the description change)
OLD_RUNES = (
    (49991, u'Ognista Runa Aury (10)', 10),
    (49992, u'Ognista Runa Aury (50)', 50),
    (49993, u'Ognista Runa Aury (100)', 100),
)


def record(template, it):
    vnum, name, pl, typ, sub, stack, anti, flag, value0, spec = it[:10]
    r = bytearray(template)
    struct.pack_into('<II', r, 0, vnum, 0)
    r[8:41] = base.fixed(name, 33)
    r[41:74] = base.fixed(pl, 33)
    struct.pack_into('<BBBB', r, 74, typ, sub, 0, 1)                 # weight 0, size 1
    struct.pack_into('<IIIII', r, 78, stack, anti, flag, 0, 0)       # stack, antiflags, flags, wear, immune
    r[98:base.RECORD] = b'\0' * (base.RECORD - 98)                   # no price, apply, socket, refine
    struct.pack_into('<i', r, 139, value0)
    struct.pack_into('<B', r, 182, spec)
    return bytes(r)


def item_proto(b):
    import m2pack
    assert b[:4] == b'MIPX'
    ver, stride, cnt, size = struct.unpack_from('<IIII', b, 4)
    assert stride == base.RECORD, stride
    raw = m2pack.mcoz_decode(b[20:], base.ITEM_KEY)
    recs = dict((struct.unpack_from('<I', raw, i * base.RECORD)[0], raw[i * base.RECORD:(i + 1) * base.RECORD])
                for i in range(cnt))
    changed = 0
    for it in ITEMS:
        r = record(recs[TEMPLATE], it)
        if recs.get(it[0]) != r:
            recs[it[0]] = r
            changed += 1
    for vnum, pl, exp in OLD_RUNES:
        if vnum not in recs:
            continue
        r = bytearray(recs[vnum])
        struct.pack_into('<i', r, 139, exp)
        if bytes(r) != recs[vnum]:
            recs[vnum] = bytes(r)
            changed += 1
    if not changed:
        return b, 0
    out = b''.join(recs[v] for v in sorted(recs))
    blob = m2pack.mcoz_encode(out, base.ITEM_KEY)
    return b'MIPX' + struct.pack('<IIII', ver, stride, len(recs), len(blob)) + blob, changed


def desc_rows():
    rows = [u'%d\t%s\t%s' % (i[0], i[2], i[11]) for i in ITEMS]
    rows += [u'%d\t%s\t%s Daje %d punktów doświadczenia szaty.' % (v, pl, D_RUNE, exp) for v, pl, exp in OLD_RUNES]
    return rows


def main():
    if len(sys.argv) not in (4, 5):
        raise SystemExit('usage: patch_aura_client.py <item_proto> <item_list.txt> <itemdesc.txt> [<out dir>]')
    proto_path, list_path, desc_path = sys.argv[1:4]
    out_dir = sys.argv[4] if len(sys.argv) == 5 else None
    results = []
    with open(proto_path, 'rb') as f:
        results.append((proto_path, item_proto(f.read())))
    with open(list_path, 'rb') as f:
        results.append((list_path, base.set_rows(f.read(), [u'%d\tETC\t%s' % (i[0], i[10]) for i in ITEMS])))
    with open(desc_path, 'rb') as f:
        results.append((desc_path, base.set_rows(f.read(), desc_rows())))
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
