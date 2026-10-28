# -*- coding: utf-8 -*-
# MT2009_PLUS_GUILDSYS_V1 (client data) - the guild system update (server-patches/guildsys/README.md; on Guild Systems
# compiled by Nazox). Everything is read from / written like the server's linux-port/docker/mariadb/playerbot/
# guildsys.sql (the ONLY source of the items and the skills' numbers - change both together):
#   gamedata/item_proto (dbdata)       a full record each of 50344-50347 (../yohara/patch_yohara_client.py
#                                      yitem_record over Przepustka 71095, every field of the SQL row)
#   gamedata/item_list.txt (gamedata)  "<vnum>\tETC\ticon/item/<icon>.tga" - icons the client has (icon pack)
#   locale/pl/itemdesc.txt (dbdata)    "<vnum>\t<Polish name>\t<description>" (cp1250)
#   locale/pl/skilldesc.txt (dbdata)   the rows 158-160: Burza / Wola / Nieugietosc Balathora (GUILD, icons
#                                      common/guild/guildsys_*.sub of build_guildsys_packs.py, the tooltip's lines)
#   gamedata/skilltable.txt (dbdata)   the rows 158-160 = the SQL's skill_proto rows (max level 10, SP, time, cool-down)
# A vnum the client has with another record / line is replaced. Idempotent: a second run changes nothing.
# build_guildsys_packs.py calls these functions on the packs; by hand, on plain copies, in the m2pack-lzo image:
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/guildsys/patch_guildsys_client.py <file> ... [--check]   (by its name)
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
SQL = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot', 'guildsys.sql')
TEMPLATE = 71095    # Przepustka: a plain stackable item
VNUMS = (50344, 50345, 50346, 50347)
SKILLS = (158, 159, 160)
# icons the client has already (icon pack): blue / red / brown books, the forget book's own
ICON = {50344: 'book_45', 50345: 'book_46', 50346: 'book_44', 50347: '70037'}
DESC = {
    50344: u'Uczy gildię umiejętności Burza Balathora (+1 poziom, najwyżej 10). | Odporność na omdlenie '
           u'i spowolnienie. | Czyta tylko lider gildii.',
    50345: u'Uczy gildię umiejętności Wola Balathora (+1 poziom, najwyżej 10). | Odporność na ogłuszenie, '
           u'kajdany i zamrożenie. | Czyta tylko lider gildii.',
    50346: u'Uczy gildię umiejętności Nieugiętość Balathora (+1 poziom, najwyżej 10). | Odporność na odrzucenie '
           u'i powalenie. | Czyta tylko lider gildii.',
    50347: u'Zwraca gildii wszystkie punkty rozdane na jej umiejętności (bez umiejętności Balathora). | Czyta '
           u'tylko lider gildii.',
}

# skilldesc rows (28 columns): vnum, job, name, name M, name G, description, conditions (4), flags, weapons, icon,
# motion, motion step, -, -, then the tooltip's lines (label, formula, formula 2) - as the guild skills 152-157 have
# (motion 101-103: the guild skills' own; ONLY_FOR_GUILD_WAR: the exe lets every guild skill work in the Balathor
# lair too - client-patches/exe PythonPlayerSkill.cpp, MT2009_PLUS_GUILDSYS_V1).
TIME = (u'Czas działania: %.0f s', u'300+429*k', u'')
SKILL_DESC = [
    (158, u'Burza Balathora', u'Daje członkom gildii obok odporność na omdlenie i spowolnienie.', 'guildsys_burza', 101,
     [(u'Odporność na omdlenie i spowolnienie: %.0f%%', u'k*100', u''), TIME]),
    (159, u'Wola Balathora', u'Daje członkom gildii obok odporność na ogłuszenie, kajdany i zamrożenie.',
     'guildsys_wola', 102,
     [(u'Odporność na ogłuszenie, kajdany i zamrożenie: %.0f%%', u'k*100', u''), TIME]),
    (160, u'Nieugiętość Balathora', u'Daje członkom gildii obok odporność na odrzucenie i powalenie.',
     'guildsys_nieugietosc', 103,
     [(u'Odporność na odrzucenie i powalenie: %.0f%%', u'k*100', u''), TIME]),
]
COND = (u'Tylko z Księgi (Krypta Balathora)', u'Wojna gildii i Krypta Balathora', u'', u'')
SKILL_COLS = ('dwVnum', 'szName', 'bType', 'bLevelStep', 'bMaxLevel', 'bLevelLimit', 'szPointOn', 'szPointPoly',
              'szSPCostPoly', 'szDurationPoly', 'szDurationSPCostPoly', 'szCooldownPoly', 'szMasterBonusPoly',
              'szAttackGradePoly', 'setFlag', 'setAffectFlag', 'szPointOn2', 'szPointPoly2', 'szDurationPoly2',
              'setAffectFlag2', 'prerequisiteSkillVnum', 'prerequisiteSkillLevel', 'eSkillType', 'iMaxHit',
              'szSplashAroundDamageAdjustPoly', 'dwTargetRange', 'dwSplashRange')


def _sql():
    return io.open(SQL, encoding='utf-8').read()


def _values(row):
    vals = []
    for tok in re.findall(r"_cp1250 X'[0-9A-Fa-f]*'|'[^']*'|-?\d+", row):
        if tok.startswith('_cp1250'):
            vals.append(bytes.fromhex(tok[10:-1]).decode('cp1250'))
        elif tok.startswith("'"):
            vals.append(tok[1:-1])
        else:
            vals.append(int(tok))
    return vals


def sql_items():
    """the item_proto INSERT's rows as {column: value}"""
    m = re.search(r'INSERT IGNORE INTO world\.item_proto \(([^)]*)\) VALUES\s*(.*?);\s*$', _sql(), re.S | re.M)
    cols = [c.strip().strip('`') for c in m.group(1).split(',')]
    out = []
    for row in re.findall(r'^\((.*)\)[,;]?\s*$', m.group(2), re.M):
        vals = _values(row)
        assert len(vals) == len(cols), (row, len(vals), len(cols))
        out.append(dict(zip(cols, vals)))
    assert sorted(w['vnum'] for w in out) == list(VNUMS), [w['vnum'] for w in out]
    return out


def sql_skills():
    """the skill_proto INSERT's rows as {column: value}"""
    m = re.search(r'INSERT INTO world\.skill_proto \(([^)]*)\) VALUES\s*(.*?)\s*ON DUPLICATE KEY', _sql(), re.S)
    cols = [c.strip() for c in m.group(1).split(',')]
    out = []
    for row in re.findall(r'^\s*\((.*)\)[,]?\s*$', m.group(2), re.M):
        vals = _values(row)
        assert len(vals) == len(cols), (row, len(vals), len(cols))
        out.append(dict(zip(cols, vals)))
    assert sorted(w['dwVnum'] for w in out) == list(SKILLS), [w['dwVnum'] for w in out]
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


def skilldesc_rows():
    out = []
    for vnum, name, text, icon, motion, lines in SKILL_DESC:
        col = [str(vnum), u'GUILD', name, u'', u'', text] + list(COND) + [u'ONLY_FOR_GUILD_WAR', u'', icon,
                                                                          str(motion), u'1', u'', u' ']
        for label, f1, f2 in lines:
            col += [label, f1, f2]
        col += [u''] * (28 - len(col))
        assert len(col) == 28, (vnum, len(col))
        out.append(u'\t'.join(col))
    return out


def skilltable_rows():
    out = []
    for w in sorted(sql_skills(), key=lambda w: w['dwVnum']):
        col = [str(w[k]) for k in SKILL_COLS]
        assert len(col) == 27
        out.append(u'\t'.join(col))
    return out


def item_list(b):
    return base.set_rows(b, list_rows())


def itemdesc(b):
    return base.set_rows(b, desc_rows())


def skilldesc(b):
    return base.set_rows(b, skilldesc_rows())


def skilltable(b):
    return base.set_rows(b, skilltable_rows())


# in-pack name -> function
JOBS = {'gamedata/item_list.txt': item_list, 'gamedata/item_proto': item_proto, 'locale/pl/itemdesc.txt': itemdesc,
        'locale/pl/skilldesc.txt': skilldesc, 'gamedata/skilltable.txt': skilltable}
BY_FILE = dict((os.path.basename(k), f) for k, f in JOBS.items())


def main():
    args = [a for a in sys.argv[1:] if a != '--check']
    check = '--check' in sys.argv
    if not args:
        raise SystemExit('usage: patch_guildsys_client.py <item_list.txt|item_proto|itemdesc.txt|skilldesc.txt|'
                         'skilltable.txt> ... [--check]')
    for path in args:
        fn = BY_FILE[os.path.basename(path)]
        b = open(path, 'rb').read()
        nb, n = fn(b)
        if n and not check:
            open(path, 'wb').write(nb)
        print('%s: %d new/changed%s' % (os.path.basename(path), n, ' (check only)' if check else ''))


if __name__ == '__main__':
    main()
