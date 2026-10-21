# -*- coding: utf-8 -*-
# MT2009_PLUS_RIPOSTY_V1 (client data) - Riposty i Dopalacze (skills 221-228 / 236-243, server-patches/riposty/README.md)
# in the client's two skill files of the "dbdata" pack:
#   locale/pl/skilldesc.txt  - job "PASSIVE" (the exe: an active-type skill, icons d:/ymir work/ui/skill/passive/
#                              <icon>_01..03.sub - build_yriposty_packs.py adds them), the names (Owsap's pl client =
#                              GF's), a description, the PASSIVE flag (never used, never on the quickslot bar), no motion;
#                              the tooltip itself is root/riposty.py's (the wiki's values) - the affect line stays GF's.
#   gamedata/skilltable.txt  - the client's copy of skill_proto (riposty_skill.sql): type 6, 24*k / 16*k.
# Both CP1250 with CRLF; the rows are replaced if there, appended if not - a second run changes nothing.
#
#   python3 patch_yriposty_client.py <skilldesc.txt> [<skilltable.txt>]         (files rewritten in place if changed)
# build_yriposty_packs.py calls skilldesc() / skilltable() on the pack's entries.
import sys

# (attack skill's name, its genitive, icon stem (GF's ui/skill/passive/p_<stem> / pp_<stem>), Owsap's skill name)
SKILLS = [
    (u'Wir Miecza', u'Wiru Miecza', u'palbang', 'PALBANG'),
    (u'Zasadzka', u'Zasadzki', u'amseup', 'AMSEOP'),
    (u'Uderzenie Palcem', u'Uderzenia Palcem', u'swaeryeong', 'SWAERYUNG'),
    (u'Strzelający Smok', u'Strzelającego Smoka', u'yongpa', 'YONGBI'),
    (u'Duchowe Uderzenie', u'Duchowego Uderzenia', u'gigongcham', 'GIGONGCHAM'),
    (u'Ognista Strzała', u'Ognistej Strzały', u'hwajo', 'HWAJO'),
    (u'Mroczne Uderzenie', u'Mrocznego Uderzenia', u'maryeong', 'MARYUNG'),
    (u'Przywołanie Błyskawicy', u'Przywołania Błyskawicy', u'byeorak', 'BYEURAK'),
]
RIPOSTE_FIRST, BOOST_FIRST = 221, 236
VNUMS = [RIPOSTE_FIRST + i for i in range(8)] + [BOOST_FIRST + i for i in range(8)]
ICONS = ['p_' + s[2] for s in SKILLS] + ['pp_' + s[2] for s in SKILLS]


def desc_lines():
    out = []
    for i, (name, gen, stem, _k) in enumerate(SKILLS):
        n = u'Riposta: ' + name
        col = [str(RIPOSTE_FIRST + i), u'PASSIVE', n, n, n,
               u'Zmniejsza obrażenia otrzymywane od umiejętności %s. Umiejętność pasywna - można znać tylko '
               u'jedną ripostę.' % name,
               u'Odporność na ' + name, u'', u'', u'', u'PASSIVE', u'', u'p_' + stem, u'', u'', u'', u'',
               u'Obrona przed umiejętnością %s +%%.1f%%%%' % name, u'24*k', u'']
        out.append(col)
    for i, (name, gen, stem, _k) in enumerate(SKILLS):
        n = u'Dopalacz: ' + name
        col = [str(BOOST_FIRST + i), u'PASSIVE', n, n, n,
               u'Zwiększa obrażenia zadawane umiejętnością %s. Umiejętność pasywna.' % name,
               u'Ulepszenie: ' + name, u'', u'', u'', u'PASSIVE', u'', u'pp_' + stem, u'', u'', u'', u'',
               u'Dopalacz +%.1f%%', u'16*k', u'']
        out.append(col)
    lines = []
    for col in out:
        col += [u''] * (28 - len(col))
        assert len(col) == 28, col[0]
        lines.append(u'\t'.join(col))
    return lines


def table_lines():
    lines = []
    for i, (_n, _g, _s, k) in enumerate(SKILLS):
        for first, pre, poly in ((RIPOSTE_FIRST, u'ANTI_', u'24*k'), (BOOST_FIRST, u'HELP_', u'16*k')):
            col = [str(first + i), pre + k, u'6', u'1', u'1', u'0', u'NONE', poly, u'', u'', u'', u'', poly, u'',
                   u'', u'NONE', u'NONE', u'', u'', u'NONE', u'0', u'0', u'NORMAL', u'1', u'1', u'1000', u'0']
            assert len(col) == 27
            lines.append(u'\t'.join(col))
    lines.sort(key=lambda l: int(l.split(u'\t', 1)[0]))
    return lines


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
    return _replace_rows(b, desc_lines())


def skilltable(b):
    return _replace_rows(b, table_lines())


def main():
    if len(sys.argv) < 2:
        raise SystemExit('usage: patch_yriposty_client.py <skilldesc.txt> [<skilltable.txt>]')
    for path, fn in zip(sys.argv[1:3], (skilldesc, skilltable)):
        b = open(path, 'rb').read()
        nb, changed = fn(b)
        if changed:
            open(path, 'wb').write(nb)
        print('%s: %s' % (path, 'patched' if changed else 'unchanged'))


if __name__ == '__main__':
    main()
