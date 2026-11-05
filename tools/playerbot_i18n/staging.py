#!/usr/bin/env python3
"""Hand the bots' untranslated chat lines to translators and take them back.

    staging.py export [lang ...]     write the untranslated lines per language to
                                     /opt/metin2/cache/i18n-staging/bots/<lang>/<lang>_NNN.tsv
                                     (~300 lines each) and RULES.md beside them
    staging.py import [lang ...]     validate the filled staging files and merge the good
                                     rows into linux-port/docker/game/playerbot_i18n/chat_<lang>.tsv;
                                     every rejected row is listed in <lang>/IMPORT_REPORT.txt
    staging.py status [lang ...]     what is translated / still missing per language

Staging TSV (UTF-8, one row per line, TAB-separated, 4 columns):
    id <TAB> Polish source <TAB> English reference <TAB> target (empty until translated)
The id is the first 10 hex digits of sha1(Polish source). A translator fills
column 4 only and changes nothing else. "-" in column 4 = not text (a code word).

Only the import writes the real files. A row is rejected when its id or Polish
column does not match the catalog, the target is empty, a slot ($NAME, {n})
is missing / added / changed, the target holds a TAB, a forbidden name or a
letter the language's code page has not got, or it is much longer than the
Polish (over 200 bytes and over 1.6 times the Polish).
"""
import hashlib, os, re, sys, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.normpath(os.path.join(HERE, '..', '..', 'linux-port/docker/game/playerbot_i18n'))
STAGE = '/opt/metin2/cache/i18n-staging/bots'
CHUNK = 300
SLOT = re.compile(r'\$[A-Z][A-Z0-9_]*|\{[1-9][0-9]*\}')
# lang -> (Windows code page, English name)
LANGS = {
    'en': (1252, 'English'), 'de': (1252, 'German'), 'tr': (1254, 'Turkish'), 'ro': (1250, 'Romanian'),
    'es': (1252, 'Spanish'), 'it': (1252, 'Italian'), 'fr': (1252, 'French'), 'pt': (1252, 'Portuguese'),
    'cz': (1250, 'Czech'), 'hu': (1250, 'Hungarian'), 'gr': (1253, 'Greek'), 'uk': (1251, 'Ukrainian'),
    'ae': (1256, 'Arabic'),
}
FORBIDDEN = re.compile(
    r'metin ?2|gameforge|tieru|ameria|metin2alerts|\bofficial|oficjaln|offiziell|officiel|ufficial|\boficial|'
    r'resmi sunucu|resmî|oficiáln|hivatalos|επίσημ|офіційн|официальн|رسمي', re.I)
CP_FIX = {0x219: 0x15F, 0x218: 0x15E, 0x21B: 0x163, 0x21A: 0x162, 0x2019: 39, 0x2018: 39, 0x201C: 34,
          0x201D: 34, 0x201E: 34, 0x2013: 45, 0x2014: 45, 0x2026: 46, 0xA0: 32}
HEADER = ("# The bots' chat in %s (playerbot_i18n.h): Polish template<TAB>translation.\n"
          "# Keys: catalog_pl.tsv (tools/playerbot_i18n/extract_pl.py); check with tools/playerbot_i18n/check_catalog.py %s.\n"
          "# \"-\" = not text. Slots $NAME / {n} as in the Polish. Merged by tools/playerbot_i18n/staging.py import.\n"
          "#@codepage\t%d\n")


def rid(pl):
    return hashlib.sha1(pl.encode('utf-8')).hexdigest()[:10]


def load_pairs(path):
    out = {}
    if os.path.exists(path):
        for line in open(path, encoding='utf-8'):
            line = line.rstrip('\r\n')
            if not line or line.startswith('#') or '\t' not in line:
                continue
            a, b = line.split('\t')[:2]
            out.setdefault(a, b)
    return out


def catalog():
    keys = []
    for line in open(os.path.join(DIR, 'catalog_pl.tsv'), encoding='utf-8'):
        if line.startswith('#') or '\t' not in line:
            continue
        keys.append(line.split('\t')[0])
    return keys


def langs_of(args):
    return args or [l for l in LANGS if l not in ('uk', 'ae')]


def check_row(lang, pl, tr):
    """The reason a translation is refused, or None."""
    if not tr.strip():
        return 'empty target'
    if tr == '-':
        return None
    if '\t' in tr or '\n' in tr:
        return 'TAB or newline in target'
    a, b = sorted(SLOT.findall(pl)), sorted(SLOT.findall(tr))
    if set(b) - set(a):
        return 'slot not in the Polish: %s' % ', '.join(sorted(set(b) - set(a)))
    if set(a) - set(b):
        return 'slot missing: %s' % ', '.join(sorted(set(a) - set(b)))
    m = FORBIDDEN.search(tr)
    if m and not FORBIDDEN.search(pl):
        return 'forbidden name: %s' % m.group(0)
    page = LANGS.get(lang, (1252, ''))[0]
    t = tr.translate(CP_FIX)
    try:
        enc = t.encode('cp%d' % page)
    except UnicodeEncodeError as e:
        return 'letter not in code page %d: %r' % (page, t[e.start:e.end])
    limit = max(200, int(len(pl.encode('utf-8')) * 1.6))
    if len(enc) > limit:
        return 'too long (%d bytes, max %d)' % (len(enc), limit)
    if re.search(r'\\x[0-9a-fA-F]', tr):
        return 'escape sequence in target'
    return None


def export(langs):
    keys = catalog()
    en = load_pairs(os.path.join(DIR, 'chat_en.tsv'))
    os.makedirs(STAGE, exist_ok=True)
    with open(os.path.join(STAGE, 'RULES.md'), 'w', encoding='utf-8') as fp:
        fp.write(open(os.path.join(HERE, 'TRANSLATOR_RULES.md'), encoding='utf-8').read())
    for lang in langs:
        have = load_pairs(os.path.join(DIR, 'chat_%s.tsv' % lang))
        todo = []
        for k in keys:
            if k in have:
                continue
            ref = en.get(k, '')
            # A code word English marks "-" is no text in any language.
            if lang != 'en' and ref == '-':
                continue
            todo.append((rid(k), k, ref))
        d = os.path.join(STAGE, lang)
        os.makedirs(d, exist_ok=True)
        for f in os.listdir(d):
            if f.startswith(lang + '_') and f.endswith('.tsv'):
                os.remove(os.path.join(d, f))
        for n in range(0, len(todo), CHUNK):
            with open(os.path.join(d, '%s_%03d.tsv' % (lang, n // CHUNK + 1)), 'w', encoding='utf-8', newline='\n') as fp:
                for r in todo[n:n + CHUNK]:
                    fp.write('%s\t%s\t%s\t\n' % r)
        print('%s: %d lines to translate in %d files -> %s' % (lang, len(todo), (len(todo) + CHUNK - 1) // CHUNK, d))


def import_(langs):
    keys = catalog()
    byid = {rid(k): k for k in keys}
    for lang in langs:
        d = os.path.join(STAGE, lang)
        if not os.path.isdir(d):
            print('%s: no staging dir' % lang)
            continue
        path = os.path.join(DIR, 'chat_%s.tsv' % lang)
        have = load_pairs(path)
        good, bad = 0, []
        for f in sorted(os.listdir(d)):
            if not (f.startswith(lang + '_') and f.endswith('.tsv')):
                continue
            for no, line in enumerate(open(os.path.join(d, f), encoding='utf-8'), 1):
                line = line.rstrip('\r\n')
                if not line.strip():
                    continue
                cols = line.split('\t')
                where = '%s:%d' % (f, no)
                if len(cols) != 4:
                    bad.append((where, 'expected 4 TAB-separated columns, got %d' % len(cols), line))
                    continue
                i, pl, ref, tr = cols
                if byid.get(i) != pl:
                    bad.append((where, 'id / Polish column changed or unknown', line))
                    continue
                tr = unicodedata.normalize('NFC', tr.strip())
                if not tr:
                    continue   # not translated yet: not an error, not merged
                why = check_row(lang, pl, tr)
                if why:
                    bad.append((where, why, line))
                    continue
                have[pl] = tr
                good += 1
        page, name = LANGS.get(lang, (1252, lang))
        with open(path, 'w', encoding='utf-8', newline='\n') as fp:
            fp.write(HEADER % (name, lang, page))
            for k in keys:
                if k in have:
                    fp.write('%s\t%s\n' % (k, have[k]))
        with open(os.path.join(d, 'IMPORT_REPORT.txt'), 'w', encoding='utf-8') as fp:
            fp.write('%s: %d rows merged, %d rejected\n' % (lang, good, len(bad)))
            for where, why, line in bad:
                fp.write('%s\t%s\t%s\n' % (where, why, line))
        print('%s: %d rows merged, %d rejected (see %s)' % (lang, good, len(bad), os.path.join(d, 'IMPORT_REPORT.txt')))


def status(langs):
    keys = catalog()
    en = load_pairs(os.path.join(DIR, 'chat_en.tsv'))
    text = [k for k in keys if en.get(k, 'x') != '-']
    for lang in langs:
        have = load_pairs(os.path.join(DIR, 'chat_%s.tsv' % lang))
        done = sum(1 for k in text if have.get(k, '-') != '-')
        bad = sum(1 for k, v in have.items() if check_row(lang, k, v))
        print('%s: %d/%d text lines translated (%.1f%%), %d missing, %d failing the checks' % (
            lang, done, len(text), 100.0 * done / max(1, len(text)), len(text) - done, bad))


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ('export', 'import', 'status'):
        print(__doc__)
        sys.exit(1)
    langs = langs_of(sys.argv[2:])
    {'export': export, 'import': import_, 'status': status}[sys.argv[1]](langs)


if __name__ == '__main__':
    main()
