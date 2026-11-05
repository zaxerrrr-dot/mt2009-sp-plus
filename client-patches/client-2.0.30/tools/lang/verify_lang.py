# -*- coding: utf-8 -*-
# MT2009_PLUS_LANG_V1 - checks the pack "lang" of a client build (build_lang_packs.py) against the build's Polish data:
#   - every language of locale/common/mt2009_languages.txt has all its files (skilldesc.txt above all - the exe stops
#     without it) and a language.cfg with its CODEPAGE;
#   - locale_game / locale_interface: every Polish key is there, with the same %-placeholders / tags as the Polish
#     value (a wrong one breaks the client's formatting or raises in python);
#   - item_names / mob_names: every vnum of item_proto / mob_proto;
#   - mt2009_texts.txt: both columns, the same placeholders;
#   - no forbidden name (Metin2, Gameforge, "official" ...) a Polish text does not have itself;
#   - the "locale" pack has no locale/en/* any more (the old partial English).
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/lang/verify_lang.py \
#     <OUT pack dir> <BASE pack dir>
# clientY.sh verify loop: lang/verify_lang.py with A="$C/azbase" (the loop passes $C/out/pack first).
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import langlib as L  # noqa: E402
import build_lang_packs as B  # noqa: E402

NEED = ('locale_game.txt', 'locale_interface.txt', 'item_names.txt', 'mob_names.txt', 'itemdesc.txt', 'skilldesc.txt',
        'mt2009_texts.txt', 'language.cfg')


def main():
    import m2pack
    out, base = sys.argv[1:3]
    idx = os.path.join(out, B.PACK + '.index')
    if not os.path.exists(idx):
        raise SystemExit('no %s pack in %s' % (B.PACK, out))
    f, v, ents = m2pack.read_index(idx)
    dat = open(os.path.join(out, B.PACK + '.data'), 'rb').read()
    files = dict((e['name'], m2pack.read_entry(dat, e)) for e in ents)
    packs = B.Packs(base, out)
    problems = []
    if any(n.startswith('locale/en/') for n in packs.where if any(p == 'locale' for p, e in packs.where[n])):
        problems.append('the "locale" pack still has locale/en/*')
    lst = files.get(B.LIST_FILE)
    if not lst:
        raise SystemExit('no ' + B.LIST_FILE)
    codes = []
    for line in lst.decode('latin-1').replace('\r', '').split('\n'):
        if line and not line.startswith('#'):
            c = line.split('\t')
            codes.append((c[0], int(c[1])))
    items, mobs = B.proto_names(packs)
    pl_game = L.locale_kv(packs.get('locale/pl/locale_game.txt'))[0]
    pl_intf = L.locale_kv(packs.get('locale/pl/locale_interface.txt'))[0]
    report = {}
    for code, cp in codes:
        if code == 'pl':
            continue
        enc = 'cp%d' % cp
        bad = []
        for n in NEED:
            if 'locale/%s/%s' % (code, n) not in files:
                bad.append('missing ' + n)
        cfg = files.get('locale/%s/language.cfg' % code, b'').decode(enc, 'replace')
        if 'CODEPAGE\t%d' % cp not in cfg:
            bad.append('language.cfg has no CODEPAGE %d' % cp)

        def text(n):
            return files.get('locale/%s/%s' % (code, n), b'').decode(enc, 'replace')

        for n, src in (('locale_game.txt', pl_game), ('locale_interface.txt', pl_intf)):
            got = L.locale_kv(files.get('locale/%s/%s' % (code, n), b''))[0]
            got = dict((k, [x.encode('cp1250', 'replace').decode(enc, 'replace') for x in c]) for k, c in got.items())
            for k, c in src.items():
                if k not in got:
                    bad.append('%s: no key %s' % (n, k))
                elif not L.same_placeholders(c[1], got[k][1]):
                    bad.append('%s %s: placeholders %r -> %r' % (n, k, c[1], got[k][1]))
        for n, src in (('item_names.txt', items), ('mob_names.txt', mobs)):
            have = set()
            for line in text(n).split('\r\n'):
                c = line.split('\t')
                if c and c[0].isdigit():
                    have.add(int(c[0]))
            miss = [v for v in src if v not in have]
            if miss:
                bad.append('%s: %d vnums missing (%s)' % (n, len(miss), miss[:5]))
        for line in files.get('locale/%s/mt2009_texts.txt' % code, b'').split(b'\r\n'):
            if not line:
                continue
            if b'\t' not in line:
                bad.append('mt2009_texts.txt: a line without a tab')
                continue
            a, b = line.split(b'\t', 1)
            a = L.unesc(a.decode('cp1250', 'replace'))
            b = L.unesc(b.decode(enc, 'replace'))
            if not L.same_placeholders(a, b):
                bad.append('mt2009_texts.txt: placeholders %r -> %r' % (a[:60], b[:60]))
        for n in NEED + L.DESC_FILES:
            t = text(n)
            if not t or n == 'mt2009_texts.txt':
                continue
            for line in t.split('\r\n'):
                if L.FORBIDDEN.search(line):
                    pl_has = any(L.FORBIDDEN.search(x) for x in (pl_game.get(line.split('\t')[0], ['', ''])[1],))
                    if not pl_has and 'metin2sp' not in line.lower():
                        bad.append('%s: forbidden name in %r' % (n, line[:80]))
                        break
        report[code] = bad[:20] + (['... %d more' % (len(bad) - 20)] if len(bad) > 20 else [])
        problems.extend('%s: %s' % (code, b) for b in bad)
    for code, bad in sorted(report.items()):
        print('%s: %s' % (code, 'ok' if not bad else '; '.join(bad[:5])))
    if problems:
        raise SystemExit('verify_lang: %d problem(s)' % len(problems))
    print('verify_lang: %d languages ok' % (len(codes) - 1))


if __name__ == '__main__':
    main()
