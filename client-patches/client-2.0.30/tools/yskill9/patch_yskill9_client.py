# -*- coding: utf-8 -*-
# MT2009_PLUS_SKILL9_V1 (client data) - the 9th skills of Yohara (176-182) in the client's two skill files of the
# "dbdata" pack:
#   locale/pl/skilldesc.txt  - names (normal / M / G), description, the tooltip's lines, flags, weapons, icon and the
#                              motion (9 = the first group's slot 9, 24 = the second group's: the exe's
#                              PythonPlayerSettingsModule.cpp registers the motions there). The texts are the pl
#                              client's (Owsap's GF locale/pl/skilldesc.txt, the pl wiki's), the tooltip formulas are
#                              the server's (tools/yskill9/yskill9_data.py: atk -> minatk/maxatk, mwep ->
#                              minmwep/maxmwep, number(a,b) -> a/b) - GF's own lines have unbalanced brackets.
#                              No "Bonus precyzji" line: our engine has no precision (the server keeps no HIT_PCT).
#   gamedata/skilltable.txt  - the client's copy of skill_proto (SP cost, cooldown, target range ...), the server's
#                              rows (yskill9_data.py) in its 27 columns.
# Both CP1250 with CRLF; rows of 176-182 are replaced if there, appended if not - a second run changes nothing.
#
#   python3 patch_yskill9_client.py <skilldesc.txt> [<skilltable.txt>]         (files rewritten in place if changed)
# build_yskill9_packs.py calls skilldesc() / skilltable() on the pack's entries.
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', '..', 'tools', 'yskill9'))
from yskill9_data import COLS, ROWS  # noqa: E402

LV = u'Siła ataku +%.0f-%.0f'
MLV = u'Magiczna siła ataku +%.0f-%.0f'
# vnum: (job, name, name M, name G, description, conditions (4), flags, weapons, icon, motion, lines [(label, f1, f2)])
DESC = [
    (176, u'WARRIOR', u'Trzęsienie', u'Silne Trzęsienie', u'Potężne Trzęsienie',
     u'Powoduje potężnym ciosem trzęsienie ziemi.|Wzmacnia: Siła (++), Zręczność (+), poziom postaci.',
     (u'Atak z dystansu', u'Efekt frontalny w jednej linii', u'', u''),
     u'ATTACK_SKILL|NEED_TARGET|WEAPON_LIMITATION|IGNORE_BLOCK|CANNOT_LEVEL_UP', u'SWORD|TWO_HANDED', u'finish', 9,
     [(LV, u'3*minatk+(0.9*minatk+1+str*5+dex*3+lv)*k', u'3*maxatk+(0.9*maxatk+1000+str*5+dex*3+lv)*k')]),
    (177, u'ASSASSIN', u'Światło Gwiazd', u'Silne Światło Gwiazd', u'Potężne Światło Gwiazd',
     u'Rzuca w przeciwników wypełnione światłem gwiazdy.|Wzmacnia: Zręczność (++), poziom postaci.',
     (u'Atak z dystansu', u'Obszar efektu w pobliżu celu', u'', u''),
     u'ATTACK_SKILL|NEED_TARGET|WEAPON_LIMITATION|IGNORE_BLOCK|CANNOT_LEVEL_UP', u'DAGGER|DOUBLE_SWORD|SWORD',
     u'ilgwangpyo', 9,
     [(LV, u'minatk+(1.7*minatk+1+dex*6+lv*5)*k', u'maxatk+(1.7*maxatk+1000+dex*6+lv*5)*k')]),
    (178, u'ASSASSIN', u'Strzał Wichury', u'Silny Strzał Wichury', u'Potężny Strzał Wichury',
     u'Strzał, który wyrządza wielkie obrażenia.|Wzmacnia: Zręczność (++).',
     (u'Atak z dystansu', u'Efekt frontalny w jednej linii', u'', u''),
     u'ATTACK_SKILL|NEED_TARGET|WEAPON_LIMITATION|IGNORE_BLOCK|CANNOT_LEVEL_UP', u'BOW', u'pungloepo', 24,
     [(LV, u'1.9*minatk+(2.6*minatk+1)*k', u'1.9*maxatk+(2.6*maxatk+1000)*k')]),
    (179, u'SURA', u'Piekielny Cios', u'Silny Piekielny Cios', u'Potężny Piekielny Cios',
     u'Przywołuje demoniczne moce do olbrzymiego pchnięcia mieczem.|Wzmacnia: Siła (++).',
     (u'Atak obszarowy walki wręcz', u'', u'', u''),
     u'ATTACK_SKILL|WEAPON_LIMITATION|MELEE_ATTACK|NEED_TARGET|IGNORE_BLOCK|CANNOT_LEVEL_UP', u'SWORD', u'geomaggwi', 9,
     [(LV, u'1.9*minatk+(2.6*minatk+1)*k', u'1.9*maxatk+(2.6*maxatk+1000)*k')]),
    (180, u'SURA', u'Fala Śmierci', u'Silna Fala Śmierci', u'Potężna Fala Śmierci',
     u'Przywołuje na przeciwnika żądne zemsty demony.|Wzmacnia: Inteligencja (++), Zręczność (+), Witalność (+), poziom postaci.',
     (u'Atak z dystansu', u'Obszar efektu w pobliżu celu', u'', u''),
     u'ATTACK_SKILL|NEED_TARGET|IGNORE_BLOCK|CANNOT_LEVEL_UP', u'', u'mabeobaggwi', 24,
     [(MLV, u'120+6*lv+(5*con+5*dex+30*iq+1+9*minmwep)*ar*k', u'120+6*lv+(5*con+5*dex+30*iq+1+9*maxmwep)*ar*k')]),
    (181, u'SHAMAN', u'Meteor', u'Silny Meteor', u'Potężny Meteor',
     u'Przyzywa meteor z nieba.|Wzmacnia: Inteligencja (++), Zręczność (+), Witalność (+), poziom postaci.',
     (u'Atak z dystansu', u'Obszar efektu w pobliżu celu', u'Trwałe obrażenia od ognia', u''),
     u'ATTACK_SKILL|NEED_TARGET|IGNORE_BLOCK|CANNOT_LEVEL_UP', u'', u'meteo', 9,
     [(MLV, u'120+6*lv+(5*con+5*dex+30*iq+1+9*minmwep)*ar*k', u'120+6*lv+(5*con+5*dex+30*iq+1+9*maxmwep)*ar*k'),
      (u'Szansa na podpalenie celu: %.0f%%', u'20*k', u'')]),
    (182, u'SHAMAN', u'Tarcza Eteru', u'Silna Tarcza Eteru', u'Potężna Tarcza Eteru',
     u'Co 12 sekund może osłonić członków grupy przed obrażeniami.|Wzmacnia: tylko poziom umiejętności.',
     (u'Możliwość użycia na członkach grupy w pobliżu', u'Powstrzymuje obrażenia', u'', u''),
     u'STANDING_SKILL|CAN_USE_FOR_ME|NEED_TARGET|ONLY_FOR_ALLIANCE|CANNOT_LEVEL_UP', u'', u'cheonun', 24,
     [(u'Szansa na ochronę co 12 s: %.0f%%', u'0.4*k+(18*k)', u''),
      (u'Czas trwania ochrony: %.0f s', u'4*k', u''),
      (u'Czas działania: %.0f s', u'50+(8*k)', u'')]),
]
VNUMS = [d[0] for d in DESC]
assert VNUMS == [r[0] for r in ROWS], (VNUMS, [r[0] for r in ROWS])


def desc_line(d):
    vnum, job, n0, n1, n2, text, cond, flags, weap, icon, motion, lines = d
    col = [str(vnum), job, n0, n1, n2, text] + list(cond) + [flags, weap, icon, str(motion), u'4', u'', u'']
    # the tooltip's lines: label, min[, max] - then the next at +3
    for label, f1, f2 in lines:
        col += [label, f1, f2]
    col += [u''] * (28 - len(col))
    assert len(col) == 28, (vnum, len(col))
    return u'\t'.join(col)


def table_line(r):
    c = dict(zip(COLS, r))
    order = ('dwVnum', 'szName', 'bType', 'bLevelStep', 'bMaxLevel', 'bLevelLimit', 'szPointOn', 'szPointPoly',
             'szSPCostPoly', 'szDurationPoly', 'szDurationSPCostPoly', 'szCooldownPoly', 'szMasterBonusPoly',
             'szAttackGradePoly', 'setFlag', 'setAffectFlag', 'szPointOn2', 'szPointPoly2', 'szDurationPoly2',
             'setAffectFlag2', 'prerequisiteSkillVnum', 'prerequisiteSkillLevel', 'eSkillType', 'iMaxHit',
             'szSplashAroundDamageAdjustPoly', 'dwTargetRange', 'dwSplashRange')
    col = [str(c[k]) for k in order]
    assert len(col) == 27
    return u'\t'.join(col)


def _replace_rows(b, lines):
    text = b.decode('cp1250')
    crlf = u'\r\n' in text
    rows = text.replace(u'\r\n', u'\n').split(u'\n')
    end = rows and rows[-1] == u''
    if end:
        rows = rows[:-1]
    want = dict((l.split(u'\t', 1)[0], l) for l in lines)
    out, done = [], set()
    for r in rows:
        v = r.split(u'\t', 1)[0]
        if v in want:
            if v not in done:
                out.append(want[v])
                done.add(v)
            continue
        out.append(r)
    for l in lines:
        v = l.split(u'\t', 1)[0]
        if v not in done:
            out.append(l)
    nl = u'\r\n' if crlf or not rows else u'\n'
    nb = (nl.join(out) + nl).encode('cp1250')
    return nb, nb != b


def skilldesc(b):
    return _replace_rows(b, [desc_line(d) for d in DESC])


def skilltable(b):
    return _replace_rows(b, [table_line(r) for r in ROWS])


def main():
    if len(sys.argv) < 2:
        raise SystemExit('usage: patch_yskill9_client.py <skilldesc.txt> [<skilltable.txt>]')
    for path, fn in zip(sys.argv[1:3], (skilldesc, skilltable)):
        b = open(path, 'rb').read()
        nb, changed = fn(b)
        if changed:
            open(path, 'wb').write(nb)
        print('%s: %s' % (path, 'patched' if changed else 'unchanged'))


if __name__ == '__main__':
    main()
