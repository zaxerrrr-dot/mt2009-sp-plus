# -*- coding: utf-8 -*-
# MT2009_PLUS_LANG_V1 - our own translations into the language tables: a batch (id, domain, key, Polish, English
# reference - build_lang_packs.py --missing) and its translation (id <tab> text) go to client-patches/lang/<code>/
# tm.tsv (Polish text -> translation) and, for whole description files, keyed.tsv (domain file, key = file name).
# A translation with other %-placeholders / tags than its Polish text, or with a forbidden name, is refused (listed).
#   python3 merge_translations.py <code> <batch.tsv> <translation.tsv> [<batch> <translation> ...]
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import langlib as L  # noqa: E402

HEAD_TM = 'OUR translations (merge_translations.py; edit freely - they win over tm_orig.tsv)\nPolish text\ttranslation'
HEAD_KEYED = 'OUR per-key translations (edit freely - they win over keyed_orig.tsv)\ndomain\tkey\tPolish text\ttranslation'


def main():
    code = sys.argv[1]
    pairs = sys.argv[2:]
    assert pairs and len(pairs) % 2 == 0, 'usage: merge_translations.py <code> <batch> <translation> ...'
    d = os.path.join(L.LANG_DIR, code)
    tm_path, keyed_path = os.path.join(d, 'tm.tsv'), os.path.join(d, 'keyed.tsv')
    tm = dict((r[0], r[1]) for r in L.read_rows(tm_path) if len(r) >= 2)
    keyed = dict(((r[0], r[1]), (r[2], r[3])) for r in L.read_rows(keyed_path) if len(r) >= 4)
    added = refused = same = missing = 0
    bad = []
    for bi in range(0, len(pairs), 2):
        batch = dict((r[0], r) for r in L.read_rows(pairs[bi]) if len(r) >= 4)
        got = {}
        for r in L.read_rows(pairs[bi + 1]):
            if len(r) >= 2:
                got[r[0].strip()] = r[1]
        for i, r in batch.items():
            dom, key, pl = r[1], r[2], r[3]
            t = got.get(i)
            if t is None or t.strip() == '':
                missing += 1
                continue
            if dom != 'file':
                t = t.strip('\r')
            if not L.same_placeholders(pl, t) or L.FORBIDDEN.search(t):
                refused += 1
                bad.append((i, pl, t))
                continue
            if t == pl and code != 'pl':
                same += 1  # left as it was (not text / a name) - kept, it is a decision too
            if dom == 'file':
                keyed[(dom, key)] = (pl, t)
            else:
                tm[L.norm_key(pl)] = t
            added += 1
    L.write_rows(tm_path, sorted([k, v] for k, v in tm.items()), HEAD_TM)
    L.write_rows(keyed_path, [[k[0], k[1], v[0], v[1]] for k, v in sorted(keyed.items())], HEAD_KEYED)
    print('%s: merged %d (unchanged text %d), refused %d, missing %d; tm %d, keyed %d'
          % (code, added, same, refused, missing, len(tm), len(keyed)))
    for b in bad[:30]:
        print('  REFUSED', b[0], repr(b[1])[:80], '->', repr(b[2])[:80])


if __name__ == '__main__':
    main()
