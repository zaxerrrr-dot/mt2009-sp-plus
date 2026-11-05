# -*- coding: utf-8 -*-
# MT2009_PLUS_LANG_V1 - the client's languages in the client build: a new pack "lang" with locale/<code>/ of every
# language of client-patches/lang/<code>/language.cfg, generated from the FINAL Polish client data of the build.
#
# What a language folder gets (all complete: every Polish key / vnum / row, so a client never shows Polish under
# another codepage; the lookup chain is langlib.Resolver - the language's tables, English, folded Polish):
#   locale_game.txt, locale_interface.txt          (localeinfo.py / uiscriptlocale.py load them over the Polish ones)
#   item_names.txt, mob_names.txt, itemdesc.txt,  (exe LoadLocaleData: locale/<language>/...; SkillDesc.txt is NOT
#   skilldesc.txt, pet_skill.txt                    optional there - a language without it stops the client)
#   guildbuildinglist.txt and the description files (empiredesc_*, jobdesc_*, rules, event descriptions)
#   mt2009_texts.txt                                the hard-coded Polish strings of the root python -> the language
#                                                   (mt2009lang.py: the UI text sink, playerbot_lang.T)
#   language.cfg                                    NAME / NATIVE / CODEPAGE (the exe-src21 reads CODEPAGE)
# and locale/common/mt2009_languages.txt: the list the language choice shows (code, codepage, "works on a 1250-only
# exe", the name in ASCII and in every codepage of the list).
# Every text is written in the language's codepage (language.cfg CODEPAGE: 1250 pl/cz/hu/ro, 1252 en/de/es/fr/it/pt,
# 1253 gr, 1254 tr, 1256 ae).
# The pack "locale" loses its old locale/en/* (the upstream's partial English of client 2.0.26): "lang" has them now.
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/lang/build_lang_packs.py <BASE pack dir> <OUT pack dir> \
#     [--check] [--report <json>] [--missing <dir>] [--dump <catalog json>]
#
# clientY.sh: LAST pack step (it reads the final locale/pl, item_proto, mob_proto and root python of the build):
#   S_lang_packs() { docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/lang/build_lang_packs.py \
#     $C/azbase $C/out/pack --lang-dir /opt/metin2/git/wt-yohara/client-patches/lang --report $C/lang_report.json; }
#   step lang_packs $C/lang.json S_lang_packs
# and lang/verify_lang.py <BASE> <OUT> in the verify loop. Every entry written is read back. Idempotent.
import json
import os
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, '/opt/metin2/cache/c36')
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
import langlib as L  # noqa: E402

PACK = 'lang'
ROOT_PACK = 'root'  # read: the python strings of the root pack (clientY's step cache keys on this name)
ZIP_LIMIT = 29 * 1024 * 1024
ITEM_KEY = (173217, 72619434, 408587239, 27973291)
MOB_KEY = (4813894, 18955, 552631, 6822045)
ITEM_RECORD = 184
MOB_RECORD = 256
LIST_FILE = 'locale/common/mt2009_languages.txt'


# ---------------------------------------------------------------- packs


class Packs(object):
    """every entry of BASE and OUT (OUT's pack wins over BASE's of the same name; "lang" itself left out)"""

    def __init__(self, base, out):
        import m2pack
        self.m2pack = m2pack
        self.where = {}
        self.dirs = {}
        for d in (base, out):
            if not d or not os.path.isdir(d):
                continue
            for f in sorted(os.listdir(d)):
                if f.endswith('.index') and f[:-6] != PACK:
                    self.dirs[f[:-6]] = d
        self._data = {}
        for p in sorted(self.dirs):
            try:
                ents = m2pack.read_index(os.path.join(self.dirs[p], p + '.index'))[2]
            except Exception:
                continue
            for e in ents:
                self.where.setdefault(e['name'], []).append((p, e))

    def data(self, p):
        if p not in self._data:
            self._data[p] = open(os.path.join(self.dirs[p], p + '.data'), 'rb').read()
        return self._data[p]

    def get(self, name, prefer=None):
        hits = self.where.get(name)
        if not hits:
            return None
        if prefer:
            for p, e in hits:
                if p == prefer:
                    return self.m2pack.read_entry(self.data(p), e)
        p, e = hits[0]
        return self.m2pack.read_entry(self.data(p), e)


def cstr(b):
    return b.split(b'\0')[0].decode(L.SOURCE_CP, 'replace')


def proto_names(packs):
    import m2pack
    items, mobs = {}, {}
    b = packs.get('gamedata/item_proto', prefer='dbdata')
    if b is not None:
        assert b[:4] == b'MIPX'
        ver, stride, cnt, size = struct.unpack_from('<IIII', b, 4)
        raw = m2pack.mcoz_decode(b[20:], ITEM_KEY)
        for i in range(cnt):
            r = raw[i * stride:(i + 1) * stride]
            items[struct.unpack_from('<I', r, 0)[0]] = cstr(r[41:74])
    b = packs.get('gamedata/mob_proto', prefer='gamedata')
    if b is not None:
        magic, cnt, esize = struct.unpack_from('<4sII', b, 0)
        raw = m2pack.mcoz_decode(b[12:12 + esize], MOB_KEY)
        for i in range(cnt):
            r = raw[i * MOB_RECORD:(i + 1) * MOB_RECORD]
            mobs[struct.unpack_from('<I', r, 0)[0]] = cstr(r[29:54])
    return items, mobs


def root_python(packs):
    out = {}
    for name in sorted(packs.where):
        if name.endswith('.py') and not name.startswith('d:') and not name.startswith('locale/common/'):
            if name.startswith('locale/') and not name.startswith('locale/pl/'):
                continue
            b = packs.get(name)
            if b is not None:
                out[name] = b
    return out


def wordlists(cat, en_store):
    plw = set()
    for d in ('lgame', 'lintf', 'idesc', 'item', 'skill'):
        for k, t in cat.by_domain(d):
            plw.update(L.words(t))
    enw = set()
    for v in list(en_store.tm.values()) + [t for s, t in en_store.keyed.values()]:
        enw.update(L.words(v))
    return plw, enw


def make_catalog(packs, extra_en_words=()):
    items, mobs = proto_names(packs)
    get = packs.get
    py = root_python(packs)
    # a first catalog without the python (its words tell Polish strings from English ones)
    cat0 = L.build_catalog(get, items, mobs, {})
    en = L.Store('en')
    plw, enw = wordlists(cat0, en)
    enw.update(extra_en_words)
    L.set_wordlists(plw, enw)
    return L.build_catalog(get, items, mobs, py)


# ---------------------------------------------------------------- generation

NL = '\r\n'


def gen_language(code, cfg, cat, res):
    cp = cfg['CODEPAGE']
    enc = lambda s: L.encode(s, cp)  # noqa: E731
    files = {}

    def t(domain, key, pl):
        return res.get(domain, key, pl)

    # locale_game / locale_interface: every line of the Polish file, the value translated
    for name, dom in (('locale_game.txt', 'lgame'), ('locale_interface.txt', 'lintf')):
        b = cat.files.get(name)
        if b is None:
            continue
        lines = []
        seen = set()
        for cols in L.tsv_lines(b):
            if len(cols) < 2 or not cols[0].strip() or cols[0].startswith('#'):
                continue
            k = cols[0]
            v = cols[1]
            if (dom, k) in cat.entries and k not in seen:
                v = t(dom, k, cat.entries[(dom, k)])
                seen.add(k)
            elif (dom, k) in cat.entries:
                v = t(dom, k, cat.entries[(dom, k)])
            lines.append('\t'.join([k, v] + cols[2:]))
        files[name] = enc(NL.join(lines) + NL)
    # the offline shop (English source in locale/common): the other languages get their own file
    b = cat.files.get('locale_game_ikashop.txt')
    if b is not None and code != 'en':
        lines = []
        for cols in L.tsv_lines(b):
            if len(cols) < 2 or not cols[0].strip() or cols[0].startswith('#'):
                continue
            v = cols[1]
            if ('ikash', cols[0]) in cat.entries:
                v = t('ikash', cols[0], v)
            lines.append('\t'.join([cols[0], v] + cols[2:]))
        files['locale_game_ikashop.txt'] = enc(NL.join(lines) + NL)
    # names
    rows = ['VNUM\tLOCALE_NAME']
    for v in sorted(cat.items):
        pl = cat.items[v]
        rows.append('%d\t%s' % (v, t('item', str(v), pl) if ('item', str(v)) in cat.entries else pl))
    # itemdesc rows of vnums item_proto lacks (the exe adds some of them itself, e.g. 100101 "Smocze Cegi+")
    b = cat.files.get('itemdesc.txt')
    if b is not None:
        for cols in L.tsv_lines(b):
            if len(cols) >= 2 and cols[0].strip().isdigit() and int(cols[0]) not in cat.items and L.has_text(cols[1]) \
                    and not L.garbled(cols[1]):
                rows.append('%s\t%s' % (cols[0].strip(), t('item', cols[0].strip(), cols[1])))
    files['item_names.txt'] = enc(NL.join(rows) + NL)
    rows = ['VNUM\tLOCALE_NAME']
    for v in sorted(cat.mobs):
        pl = cat.mobs[v]
        rows.append('%d\t%s' % (v, t('mob', str(v), pl) if ('mob', str(v)) in cat.entries else pl))
    files['mob_names.txt'] = enc(NL.join(rows) + NL)
    # itemdesc: vnum, name, description, summary
    b = cat.files.get('itemdesc.txt')
    if b is not None:
        rows = []
        for cols in L.tsv_lines(b):
            if len(cols) < 2 or not cols[0].strip().isdigit():
                continue
            v = cols[0].strip()
            c = list(cols)
            if ('item', v) in cat.entries:
                c[1] = t('item', v, cat.items[int(v)])
            elif L.has_text(c[1]):
                c[1] = t('item', v, c[1])
            if len(c) > 2 and ('idesc', v) in cat.entries:
                c[2] = t('idesc', v, c[2])
            if len(c) > 3 and ('isumm', v) in cat.entries:
                c[3] = t('isumm', v, c[3])
            rows.append('\t'.join(c))
        files['itemdesc.txt'] = enc(NL.join(rows) + NL)
    # skilldesc / pet_skill / guildbuildinglist: their text cells
    for name, dom, keycol in (('skilldesc.txt', 'skill', None), ('pet_skill.txt', 'pet', None),
                              ('guildbuildinglist.txt', 'gbld', 3)):
        b = cat.files.get(name)
        if b is None:
            continue
        rows = []
        for cols in L.tsv_lines(b):
            if not any(x.strip() for x in cols):
                continue
            c = list(cols)
            if c[0].strip().isdigit():
                for i in range(len(c)):
                    key = c[0].strip() if keycol is not None else '%s:%d' % (c[0].strip(), i)
                    if keycol is not None and i != keycol:
                        continue
                    if (dom, key) in cat.entries:
                        c[i] = t(dom, key, c[i])
            rows.append('\t'.join(c))
        files[name] = enc(NL.join(rows) + NL)
    # whole description files
    for name in L.DESC_FILES:
        if ('file', name) in cat.entries:
            txt = t('file', name, cat.entries[('file', name)])
            files[name] = enc(txt.replace('\r\n', '\n').replace('\n', NL))
    # the root python's strings: Polish (cp1250) -> the language; every literal that has a translation
    pyrows = {}
    for d, k in cat.order:
        if d != 'py':
            continue
        pl = cat.entries[(d, k)]
        tr = res.get('py', k, pl)
        if tr != pl:
            pyrows[pl] = tr
    for pl in sorted(cat.py_all):
        if pl in pyrows:
            continue
        tr = res.get('py', None, pl, count=False)
        if tr != pl and tr != L.fold(pl):
            pyrows[pl] = tr
    lines = []
    for pl in sorted(pyrows):
        tr = pyrows[pl]
        if cp == 1250 and tr == L.fold(pl):
            continue  # Polish letters show under 1250 - the original reads better than the folded one
        lines.append(L.esc(pl).encode(L.SOURCE_CP, 'replace') + b'\t' + enc(L.esc(tr)))
    files['mt2009_texts.txt'] = b'\r\n'.join(lines) + b'\r\n'
    files['language.cfg'] = enc('NAME\t%s%sNATIVE\t%s%sCODEPAGE\t%d%s' % (cfg['NAME'], NL, cfg['NATIVE'], NL, cp, NL))
    return dict(('locale/%s/%s' % (code, n), b) for n, b in files.items())


def cp1250_safe(files, cp, cat):
    """True when every text of the language reads the same under the 1250 codepage (an exe without the per-language
    codepage of exe-src21 can show it). Not counted: the Polish keys of mt2009_texts.txt (compared as cp1250 bytes,
    never shown) and the garbled names of unused item / monster rows."""
    if cp == 1250:
        return True
    bad_names = set(str(v) for v, t in list(cat.items.items()) + list(cat.mobs.items()) if L.garbled(t))
    for n, b in files.items():
        lines = b.split(b'\r\n')
        if n.endswith('/mt2009_texts.txt'):
            lines = [l.split(b'\t', 1)[1] if b'\t' in l else b'' for l in lines]
        elif n.endswith(('/item_names.txt', '/mob_names.txt', '/itemdesc.txt')):
            lines = [l for l in lines if l.split(b'\t', 1)[0].decode('ascii', 'replace') not in bad_names]
        for l in lines:
            try:
                if l.decode('cp%d' % cp) != l.decode('cp1250'):
                    return False
            except UnicodeDecodeError:
                return False
    return True


def language_list(langs, safe):
    cps = sorted(set([1250] + [cfg['CODEPAGE'] for c, cfg in langs]))
    rows = ['# code\tcodepage\tworks_on_1250_exe\tname_ascii\t' + '\t'.join('name_cp%d' % c for c in cps)]
    rows.append('#CODEPAGES\t' + '\t'.join(str(c) for c in cps))
    out = [r.encode('ascii') for r in rows]
    entries = [('pl', {'CODEPAGE': 1250, 'NATIVE': u'Polski', 'NAME': 'Polish'})] + langs
    for code, cfg in entries:
        native = cfg['NATIVE']
        cells = [code.encode('ascii'), str(cfg['CODEPAGE']).encode('ascii'),
                 b'1' if code == 'pl' or safe.get(code) else b'0', L.fold(native).encode('ascii', 'replace')]
        for c in cps:
            try:
                cells.append(native.encode('cp%d' % c))
            except UnicodeEncodeError:
                cells.append(L.fold(native).encode('ascii', 'replace'))
        out.append(b'\t'.join(cells))
    return b'\r\n'.join(out) + b'\r\n'


def coverage(res, cat):
    """per domain: entries, own (the language's tables), en (English fallback), fallback (folded Polish) + percent"""
    rep = {}
    for dom, st in sorted(res.stats.items()):
        total = sum(st.values())
        own = sum(v for k, v in st.items() if not k.startswith('en-') and k != 'fallback')
        en = sum(v for k, v in st.items() if k.startswith('en-'))
        rep[dom] = dict(entries=total, own=own, english=en, fallback=st.get('fallback', 0),
                        own_pct=round(100.0 * own / total, 1) if total else 100.0, detail=st)
    tot = sum(r['entries'] for r in rep.values())
    own = sum(r['own'] for r in rep.values())
    rep['_all'] = dict(entries=tot, own=own, own_pct=round(100.0 * own / tot, 1) if tot else 100.0)
    return rep


# ---------------------------------------------------------------- pack writing


def _m2pack_c36():
    """/opt/metin2/cache/c36/m2pack.py - the one with repack2 (removal); the tz one on the path has no repack2"""
    import importlib.util
    spec = importlib.util.spec_from_file_location('m2pack_c36', '/opt/metin2/cache/c36/m2pack.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_pack(base, out, files, report, check):
    import m2pack
    import packlib
    rd = packlib.rd
    # 1) the old locale/en/* leave the "locale" pack
    src = out if os.path.exists(os.path.join(out, 'locale.index')) else base
    f, v, ents = m2pack.read_index(os.path.join(src, 'locale.index'))
    drop = sorted(e['name'] for e in ents if e['name'].startswith('locale/en/') or e['name'] in files)
    if drop:
        report['locale_removed'] = drop
        if not check:
            ti, td = os.path.join(out, 'locale.index.lang'), os.path.join(out, 'locale.data.lang')
            _m2pack_c36().repack2(os.path.join(src, 'locale.index'), os.path.join(src, 'locale.data'), ti, td, remove=drop)
            os.replace(ti, os.path.join(out, 'locale.index'))
            os.replace(td, os.path.join(out, 'locale.data'))
            f2, v2, nw = m2pack.read_index(os.path.join(out, 'locale.index'))
            nd = rd(os.path.join(out, 'locale.data'))
            od = rd(os.path.join(src, 'locale.data')) if src != out else None
            names = [e['name'] for e in nw]
            assert not set(drop) & set(names)
            assert len(names) == len(ents) - len(drop), 'locale'
            for e in nw:
                assert zlib.crc32(nd[e['pos']:e['pos'] + e['size']]) & 0xffffffff == e['dcrc'], ('locale', e['name'])
                m2pack.read_entry(nd, e)
    # 2) the "lang" pack
    have = None
    if os.path.exists(os.path.join(out, PACK + '.index')):
        f, v, ents = m2pack.read_index(os.path.join(out, PACK + '.index'))
        dat = rd(os.path.join(out, PACK + '.data'))
        have = dict((e['name'], m2pack.read_entry(dat, e)) for e in ents)
    if os.path.exists(os.path.join(base, PACK + '.index')) and base != out:
        raise SystemExit('%s is in BASE - drop it from BASE' % PACK)
    if have == files:
        report[PACK] = 'unchanged'
    elif check:
        report[PACK] = dict(files=len(files), raw_mb=round(sum(len(b) for b in files.values()) / 1e6, 2))
    else:
        tmpl = None
        for d in (out, base):
            for p in sorted(os.listdir(d)):
                if p.endswith('.index') and p != PACK + '.index':
                    try:
                        tmpl = m2pack.read_index(os.path.join(d, p))[2][-1]['raw']
                        break
                    except Exception:
                        continue
            if tmpl:
                break
        add = dict((k, (b, 2)) for k, b in files.items())
        ti, td = os.path.join(out, PACK + '.index.lang'), os.path.join(out, PACK + '.data.lang')
        packlib.repack_add_typed(None, None, {}, add, ti, td, tmpl)
        os.replace(ti, os.path.join(out, PACK + '.index'))
        os.replace(td, os.path.join(out, PACK + '.data'))
        f, v, nw = m2pack.read_index(os.path.join(out, PACK + '.index'))
        nd = rd(os.path.join(out, PACK + '.data'))
        got = {}
        for e in nw:
            assert zlib.crc32(nd[e['pos']:e['pos'] + e['size']]) & 0xffffffff == e['dcrc'], (PACK, e['name'])
            assert e['fcrc'] == zlib.crc32(e['name'].encode('cp1252')) & 0xffffffff, (PACK, e['name'])
            got[e['name']] = m2pack.read_entry(nd, e)
        assert got == files, PACK
        report[PACK] = dict(entries=len(nw), data_mb=round(len(nd) / 1e6, 2), under_zip_limit=len(nd) < ZIP_LIMIT)
        assert report[PACK]['under_zip_limit'], report[PACK]
    # 3) Index: the new pack at the end
    if not check:
        ix_path = os.path.join(out, 'Index') if os.path.exists(os.path.join(out, 'Index')) else os.path.join(base, 'Index')
        ix = rd(ix_path)
        lines = [l.strip() for l in ix.replace(b'\r\n', b'\n').split(b'\n')]
        if PACK.encode() not in lines:
            nl = b'\r\n' if b'\r\n' in ix else b'\n'
            ix = ix.rstrip(b'\r\n') + nl + b'*' + nl + PACK.encode() + nl
        if ix != rd(ix_path) or ix_path != os.path.join(out, 'Index'):
            open(os.path.join(out, 'Index'), 'wb').write(ix)
            report['Index'] = 'written'


def main():
    args = [a for a in sys.argv[1:]]
    opts = {}
    pos = []
    i = 0
    while i < len(args):
        a = args[i]
        if a in ('--report', '--missing', '--dump', '--only', '--files', '--lang-dir'):
            opts[a] = args[i + 1]
            i += 2
            continue
        if a.startswith('--'):
            opts[a] = True
        else:
            pos.append(a)
        i += 1
    if len(pos) != 2:
        raise SystemExit('usage: build_lang_packs.py <BASE pack dir> <OUT pack dir> [--check] [--report json] '
                         '[--missing dir] [--dump catalog.json] [--only code,code] [--files dir] [--lang-dir dir]')
    base, out = pos
    check = '--check' in opts
    if '--lang-dir' in opts:
        # the tables of the build's checkout (clientY.sh names it, so its step cache sees a change of a table)
        L.LANG_DIR = os.path.abspath(opts['--lang-dir'])
    packs = Packs(base, out)
    cat = make_catalog(packs)
    if '--dump' in opts:
        json.dump(dict(entries=[[d, k, cat.entries[(d, k)]] for d, k in cat.order], py_all=sorted(cat.py_all)),
                  open(opts['--dump'], 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    langs = L.languages()
    if '--only' in opts:
        only = opts['--only'].split(',')
        langs = [x for x in langs if x[0] in only]
    en = L.Store('en')
    files, report, safe = {}, {'languages': {}}, {}
    for code, cfg in langs:
        res = L.Resolver(code, en=en)
        lf = gen_language(code, cfg, cat, res)
        safe[code] = cp1250_safe(lf, cfg['CODEPAGE'], cat)
        files.update(lf)
        report['languages'][code] = dict(codepage=cfg['CODEPAGE'], works_on_1250_exe=safe[code],
                                         coverage=coverage(res, cat), refused=len(res.refused),
                                         refused_sample=[list(x) for x in res.refused[:20]])
        if '--missing' in opts:
            d = os.path.join(opts['--missing'], code)
            if not os.path.isdir(d):
                os.makedirs(d)
            seen = set()
            rows = []
            for dom, key, pl, en_t in res.not_own:
                if dom in ('item', 'mob'):
                    b, suf = L.split_refine(pl)
                    if suf:
                        pl = b.strip()
                        en_t = L.split_refine(en_t)[0].strip() if en_t else en_t
                # one row per text that differs only in its numbers (the numeric templates fill the others)
                k = (dom if dom in ('file',) else '', L.num_key(pl))
                if k in seen:
                    continue
                seen.add(k)
                rows.append(['%s%05d' % (code, len(rows) + 1), dom, key or '', pl, en_t or ''])
            L.write_rows(os.path.join(d, 'missing.tsv'), rows,
                         'id\tdomain\tkey\tPolish text\tEnglish (the current fallback, empty: none) - no %s text yet' % code)
            L.write_rows(os.path.join(d, 'refused.tsv'), [list(x) for x in res.refused])
    files[LIST_FILE] = language_list(langs, safe)
    if '--files' in opts:
        for n, b in files.items():
            p = os.path.join(opts['--files'], n)
            if not os.path.isdir(os.path.dirname(p)):
                os.makedirs(os.path.dirname(p))
            open(p, 'wb').write(b)
    write_pack(base, out, files, report, check)
    if '--report' in opts:
        json.dump(report, open(opts['--report'], 'w'), indent=1, ensure_ascii=False)
    short = dict((c, dict(all=r['coverage']['_all']['own_pct'], works_on_1250_exe=r['works_on_1250_exe'],
                          refused=r['refused']))
                 for c, r in report['languages'].items())
    print(json.dumps(dict(languages=short, **dict((k, v) for k, v in report.items() if k != 'languages')),
                     indent=1, ensure_ascii=False))


if __name__ == '__main__':
    main()
