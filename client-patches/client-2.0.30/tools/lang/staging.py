# -*- coding: utf-8 -*-
# MT2009_PLUS_LANG_V1 - the translators' staging area (docs/i18n-handoff-client.md):
#
#   export: every text of the client build that a language has no own translation for, as small TSV chunks
#     docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/lang/staging.py \
#       export <BASE pack dir> <OUT pack dir> /opt/metin2/cache/i18n-staging/client [--lang de,tr] [--chunk 300]
#     -> <staging>/<lang>/<lang>_NNN.tsv   id <TAB> Polish source <TAB> English reference (may be empty) <TAB> (empty target)
#        <staging>/<lang>/_manifest.tsv     id <TAB> domain <TAB> key <TAB> Polish source  (for the import, do not edit)
#        <staging>/<lang>/_glossary.tsv     Polish <TAB> official <lang> text (Owsap originals; read-only help)
#     A text that differs from another only in its numbers is exported once (the build's numeric templates fill the rest).
#
#   import: the filled chunks (4th column = translation) into client-patches/lang/<lang>/tm.tsv / keyed.tsv
#     python3 <repo>/client-patches/client-2.0.30/tools/lang/staging.py import /opt/metin2/cache/i18n-staging/client \
#       [--lang de,tr] [--dry-run]
#     A row is REFUSED (listed in <staging>/<lang>/_import_report.tsv, nothing written for it) when its %-placeholders /
#     {n} / [ENTER] / |c..|r tags differ from the Polish ones, its numbers differ (count or order), it has a forbidden name
#     (Metin2, Gameforge, official ... - langlib.FORBIDDEN), it has a character the language's codepage cannot show,
#     a TAB / raw newline, or it is empty. Rows with an empty target are skipped (still untranslated).
# The import runs on the host (python3, no packs needed); the export needs the m2pack-lzo image (it reads the packs).
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import langlib as L  # noqa: E402


def _opts(argv):
    pos, opts = [], {}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ('--lang', '--chunk', '--lang-dir'):
            opts[a] = argv[i + 1]
            i += 2
            continue
        if a.startswith('--'):
            opts[a] = True
        else:
            pos.append(a)
        i += 1
    if '--lang-dir' in opts:
        L.LANG_DIR = os.path.abspath(opts['--lang-dir'])
    return pos, opts


def export(base, out, staging, langs, chunk):
    import build_lang_packs as B
    packs = B.Packs(base, out)
    cat = B.make_catalog(packs)
    en = L.Store('en')
    for code, cfg in L.languages():
        if langs and code not in langs:
            continue
        res = L.Resolver(code, en=en)
        B.gen_language(code, cfg, cat, res)
        seen, rows = set(), []
        for dom, key, pl, en_t in res.not_own:
            if dom in ('item', 'mob'):
                b, suf = L.split_refine(pl)
                if suf:
                    pl = b.strip()
                    en_t = L.split_refine(en_t)[0].strip() if en_t else en_t
            k = (dom if dom == 'file' else '', L.num_key(pl))
            if k in seen:
                continue
            seen.add(k)
            rows.append(('%s%05d' % (code, len(rows) + 1), dom, key or '', pl, en_t or ''))
        d = os.path.join(staging, code)
        if not os.path.isdir(d):
            os.makedirs(d)
        for f in os.listdir(d):
            if f.endswith('.tsv'):
                os.remove(os.path.join(d, f))
        L.write_rows(os.path.join(d, '_manifest.tsv'), [list(r[:4]) for r in rows],
                     'id\tdomain\tkey\tPolish source - DO NOT EDIT (staging.py import reads it)')
        for i in range(0, len(rows), chunk):
            part = rows[i:i + chunk]
            L.write_rows(os.path.join(d, '%s_%03d.tsv' % (code, i // chunk + 1)),
                         [[r[0], r[3], r[4], ''] for r in part],
                         'id\tPolish source\tEnglish reference (may be empty)\t%s translation (fill this column)' % code)
        st = L.Store(code)
        L.write_rows(os.path.join(d, '_glossary.tsv'),
                     sorted([k, v] for k, v in st_orig_tm(code).items()),
                     'official %s game terms (Owsap originals) - Polish\t%s; read-only help for the translators' % (code, code))
        print('%s: %d texts to translate, %d chunks, %d chars' % (code, len(rows), (len(rows) + chunk - 1) // chunk,
                                                                  sum(len(r[3]) for r in rows)))


def st_orig_tm(code):
    tm = {}
    for r in L.read_rows(os.path.join(L.LANG_DIR, code, 'tm_orig.tsv')):
        if len(r) >= 2 and len(r[0]) <= 80:
            tm[r[0]] = r[1]
    return tm


def check_row(pl, tr, cp, dom):
    if not tr.strip():
        return 'empty'
    if '\t' in tr or ('\n' in tr and '\n' not in pl):
        return 'tab or newline'
    if not L.same_placeholders(pl, tr):
        return 'placeholders %s -> %s' % (L.placeholders(pl), L.placeholders(tr))
    if L.numbers(pl) != L.numbers(tr) and dom not in ('file', 'idesc', 'isumm'):
        # numbers may move in long texts; short ones keep them (numeric templates)
        if sorted(L.numbers(pl)) != sorted(L.numbers(tr)):
            return 'numbers %s -> %s' % (L.numbers(pl), L.numbers(tr))
    m = L.FORBIDDEN.search(tr)
    if m:
        return 'forbidden name %r' % m.group(0)
    try:
        s = u''.join(L._CP_ALIAS.get(cp, {}).get(c, c) for c in tr)
        s.encode('cp%d' % cp)
    except UnicodeEncodeError as e:
        return 'not in codepage %d: %r' % (cp, tr[e.start:e.end])
    return None


def do_import(staging, langs, dry):
    from merge_translations import HEAD_TM, HEAD_KEYED
    total = 0
    for code, cfg in L.languages():
        if langs and code not in langs:
            continue
        d = os.path.join(staging, code)
        man_p = os.path.join(d, '_manifest.tsv')
        if not os.path.exists(man_p):
            continue
        man = dict((r[0], r) for r in L.read_rows(man_p) if len(r) >= 4)
        tm_p = os.path.join(L.LANG_DIR, code, 'tm.tsv')
        keyed_p = os.path.join(L.LANG_DIR, code, 'keyed.tsv')
        tm = dict((r[0], r[1]) for r in L.read_rows(tm_p) if len(r) >= 2)
        keyed = dict(((r[0], r[1]), (r[2], r[3])) for r in L.read_rows(keyed_p) if len(r) >= 4)
        ok, refused, empty, unknown = 0, [], 0, 0
        for f in sorted(os.listdir(d)):
            if not f.endswith('.tsv') or f.startswith('_'):
                continue
            for r in L.read_rows(os.path.join(d, f)):
                if not r or not r[0].strip():
                    continue
                rid = r[0].strip()
                tr = r[3] if len(r) >= 4 else ''
                if not tr.strip():
                    empty += 1
                    continue
                if rid not in man:
                    unknown += 1
                    refused.append([f, rid, 'unknown id', '', tr])
                    continue
                _, dom, key, pl = man[rid][:4]
                why = check_row(pl, tr, cfg['CODEPAGE'], dom)
                if why:
                    refused.append([f, rid, why, pl, tr])
                    continue
                if dom == 'file':
                    keyed[(dom, key)] = (pl, tr)
                else:
                    tm[L.norm_key(pl)] = tr
                ok += 1
        if not dry:
            L.write_rows(tm_p, sorted([k, v] for k, v in tm.items()), HEAD_TM)
            L.write_rows(keyed_p, [[k[0], k[1], v[0], v[1]] for k, v in sorted(keyed.items())], HEAD_KEYED)
        L.write_rows(os.path.join(d, '_import_report.tsv'), refused, 'chunk\tid\twhy refused\tPolish\ttranslation')
        total += ok
        print('%s: imported %d, refused %d, still empty %d%s' % (code, ok, len(refused), empty,
                                                               ' (dry run - nothing written)' if dry else ''))
    return total


def main():
    pos, opts = _opts(sys.argv[1:])
    langs = set(opts['--lang'].split(',')) if '--lang' in opts else set()
    if pos and pos[0] == 'export' and len(pos) == 4:
        export(pos[1], pos[2], pos[3], langs, int(opts.get('--chunk', 300)))
    elif pos and pos[0] == 'import' and len(pos) == 2:
        do_import(pos[1], langs, '--dry-run' in opts)
    else:
        raise SystemExit(__doc__ if __doc__ else 'usage: staging.py export <BASE> <OUT> <staging> | import <staging>')


if __name__ == '__main__':
    main()
