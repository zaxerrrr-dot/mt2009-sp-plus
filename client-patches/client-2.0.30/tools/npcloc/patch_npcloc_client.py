# -*- coding: utf-8 -*-
# MT2009_PLUS_NPC_LOCATION_HELPER_V1 (client data) - Lokalizator NPC (Autor: Best Studio): the three items of the
# server's linux-port/docker/mariadb/playerbot/npc_location_helper.sql (the ONLY source - this file reads it):
#   79667 Lokalizator NPC, 79668 Kamien Teleportacji+, 79669 Kamien Teleportacji
#
#   gamedata/item_proto (dbdata)    a full record each (../yohara/patch_yohara_client.py yitem_record over
#                                   Przepustka 71095, every field of the SQL row)
#   gamedata/item_list.txt          "<vnum>\tETC\ticon/item/<icon>.tga" (the icons in client-2.0.30/root/icon/item)
#   locale/pl/itemdesc.txt (dbdata) "<vnum>\t<Polish name>\t<description>" (cp1250)
# A vnum the client has with another record is replaced. Idempotent: a second run changes nothing.
# build_npcloc_packs.py calls these functions on the packs; by hand, on plain copies, in the m2pack-lzo image:
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/npcloc/patch_npcloc_client.py <file> ... [--check]   (by its name)
import io
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, os.path.join(HERE, '..', 'yohara'))
sys.path.insert(0, os.path.join(HERE, '..', 'monstercard'))
import patch_monstercard_client as base  # noqa: E402
import patch_yohara_client as py  # noqa: E402

REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
SQL = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot', 'npc_location_helper.sql')
TEMPLATE = 71095    # Przepustka: a plain stackable item
VNUMS = (79667, 79668, 79669)
ICON = {79667: '79667', 79668: '79669', 79669: '79669'}
DESC = {
    79667: u'Użyty raz, na stałe włącza tej postaci Lokalizator NPC: duża mapa pokazuje NPC '
           u'każdej mapy, strzałkę pod postacią i potwory z ich łupem. | Na mapie świata '
           u'przełącz widok przyciskiem w pasku tytułu.',
    79669: u'Teleportuje do NPC wybranego w Lokalizatorze NPC. | Ta sama mapa: 1 kamień, ten sam region: 2, '
           u'inna mapa: 3.',
    79668: u'Teleportuje do NPC wybranego w Lokalizatorze NPC. | Ta sama mapa: 1 kamień, ten sam region: 2, '
           u'inna mapa: 3. | Można nim handlować.',
}


def sql_items():
    """the INSERT's rows as {column: value}; _cp1250 X'..' decoded, numbers as int"""
    text = io.open(SQL, encoding='utf-8').read()
    m = re.search(r'INSERT IGNORE INTO world\.item_proto \(([^)]*)\) VALUES\s*(.*?);\s*$', text, re.S | re.M)
    cols = [c.strip().strip('`') for c in m.group(1).split(',')]
    out = []
    for row in re.findall(r'^\((.*)\)[,;]?\s*$', m.group(2), re.M):
        vals = []
        for tok in re.findall(r"_cp1250 X'[0-9A-Fa-f]*'|'[^']*'|-?\d+", row):
            if tok.startswith('_cp1250'):
                vals.append(bytes.fromhex(tok[10:-1]).decode('cp1250'))
            elif tok.startswith("'"):
                vals.append(tok[1:-1])
            else:
                vals.append(int(tok))
        assert len(vals) == len(cols), (row, len(vals), len(cols))
        out.append(dict(zip(cols, vals)))
    assert sorted(w['vnum'] for w in out) == list(VNUMS), [w['vnum'] for w in out]
    return out


def records(b):
    import m2pack
    assert b[:4] == b'MIPX'
    ver, stride, cnt, size = struct.unpack_from('<IIII', b, 4)
    assert stride == base.RECORD, stride
    raw = m2pack.mcoz_decode(b[20:], base.ITEM_KEY)
    return ver, dict((struct.unpack_from('<I', raw, i * base.RECORD)[0], raw[i * base.RECORD:(i + 1) * base.RECORD])
                     for i in range(cnt))


def want_records(recs):
    return dict((w['vnum'], py.yitem_record(recs[TEMPLATE], w)) for w in sql_items())


def item_proto(b):
    import m2pack
    ver, recs = records(b)
    changed = 0
    for v, r in want_records(recs).items():
        if recs.get(v) != r:
            recs[v] = r
            changed += 1
    if not changed:
        return b, 0
    out = b''.join(recs[v] for v in sorted(recs))
    blob = m2pack.mcoz_encode(out, base.ITEM_KEY)
    return b'MIPX' + struct.pack('<IIII', ver, base.RECORD, len(recs), len(blob)) + blob, changed


def list_rows():
    return ['%d\tETC\ticon/item/%s.tga' % (v, ICON[v]) for v in VNUMS]


def desc_rows():
    names = dict((w['vnum'], w['locale_name']) for w in sql_items())
    return [u'%d\t%s\t%s' % (v, names[v], DESC[v]) for v in VNUMS]


def item_list(b):
    return base.set_rows(b, list_rows())


def itemdesc(b):
    return base.set_rows(b, desc_rows())


# in-pack name -> function
JOBS = {'gamedata/item_list.txt': item_list, 'gamedata/item_proto': item_proto, 'locale/pl/itemdesc.txt': itemdesc}
BY_FILE = dict((os.path.basename(k), f) for k, f in JOBS.items())


def main():
    args = [a for a in sys.argv[1:] if a != '--check']
    check = '--check' in sys.argv
    if not args:
        raise SystemExit('usage: patch_npcloc_client.py <item_list.txt|item_proto|itemdesc.txt> ... [--check]')
    for path in args:
        fn = BY_FILE[os.path.basename(path)]
        b = open(path, 'rb').read()
        nb, n = fn(b)
        if n and not check:
            open(path, 'wb').write(nb)
        print('%s: %d new/changed%s' % (os.path.basename(path), n, ' (check only)' if check else ''))


if __name__ == '__main__':
    main()
