# -*- coding: utf-8 -*-
# MT2009_PLUS_LANG_V1 - the client's languages: the shared library of the language tools (python 3).
#
# The Polish client is the source. Every other language is generated at build time from the FINAL Polish client data
# (after every other builder step) and the translation tables in client-patches/lang/<code>/:
#   language.cfg   NAME / NATIVE / CODEPAGE / ORDER of the language (one "KEY<tab>value" per line);
#   keyed*.tsv     domain <tab> key <tab> Polish text at translation time <tab> translation (per vnum / locale key);
#   tm*.tsv        Polish text <tab> translation (translation memory: any domain, any key with that exact text).
#   *_orig.tsv are the imported originals (import_originals.py: Owsap's per-language client data, the upstream
#   release's English layer) - regenerated, never edited; every other table (keyed.tsv, tm.tsv, tm_*.tsv) is ours
#   and wins over them.
# A table line starting with "#" is a comment. Inside a cell "\t", "\n" and "\\" are escapes. Files are UTF-8.
#
# Domains (catalog of the Polish client):
#   item  <vnum>            item name (item_proto locale name; "+N" refine suffixes are translated by their base name)
#   mob   <vnum>            monster / NPC name (mob_proto locale name)
#   idesc <vnum>            itemdesc.txt description (column 3) - summary (column 4) is domain isumm
#   isumm <vnum>
#   skill <vnum>:<col>      skilldesc.txt text cells
#   pet   <vnum>:<col>      pet_skill.txt text cells
#   gbld  <vnum>            guildbuildinglist.txt building name
#   lgame <KEY>             locale_game.txt
#   lintf <KEY>             locale_interface.txt
#   ikash <KEY>             locale/common/locale_game_ikashop.txt (the offline shop; its source text is ENGLISH)
#   file  <name>            a whole description file (empiredesc_a.txt, jobdesc_*.txt, event descriptions, rules.txt)
#   py    <module>:<line>   a Polish string literal of the root python (the UI sink of mt2009lang.py translates it)
#
# Lookup of one entry for a language: keyed (same Polish text, or a similar one - then counted "stale") -> tm (exact,
# then whitespace/case-folded) -> for names "<base>+N": the base name -> the same for English -> the Polish text with
# its diacritics folded to ASCII. A translation whose %-placeholders / {n} / [ENTER] / |cff..|r tags differ from the
# Polish text's is refused (it would break the client's formatting) and counted.
import codecs
import difflib
import io
import os
import re
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
LANG_DIR = os.path.join(REPO, 'client-patches', 'lang')
SOURCE = 'pl'
SOURCE_CP = 'cp1250'

# ---------------------------------------------------------------- tables


def unesc(s):
    out, i = [], 0
    while i < len(s):
        c = s[i]
        if c == '\\' and i + 1 < len(s):
            n = s[i + 1]
            out.append({'t': '\t', 'n': '\n', 'r': '\r', '\\': '\\'}.get(n, '\\' + n))
            i += 2
        else:
            out.append(c)
            i += 1
    return ''.join(out)


def esc(s):
    return s.replace('\\', '\\\\').replace('\t', '\\t').replace('\r', '\\r').replace('\n', '\\n')


def read_rows(path):
    rows = []
    if not os.path.exists(path):
        return rows
    with io.open(path, encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n').rstrip('\r')
            if not line or line.startswith('#'):
                continue
            rows.append([unesc(c) for c in line.split('\t')])
    return rows


def write_rows(path, rows, header=None):
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with io.open(path, 'w', encoding='utf-8', newline='\n') as f:
        if header:
            for h in header.split('\n'):
                f.write('# ' + h + '\n')
        for r in rows:
            f.write('\t'.join(esc(c) for c in r) + '\n')


def read_cfg(path):
    cfg = {}
    if os.path.exists(path):
        with io.open(path, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                k, _, v = line.partition('\t')
                if not _:
                    k, _, v = line.partition(' ')
                cfg[k.strip().upper()] = v.strip()
    return cfg


def languages(lang_dir=None):
    """[(code, cfg)] of every client-patches/lang/<code>/language.cfg, by ORDER then code"""
    lang_dir = lang_dir or LANG_DIR
    out = []
    if not os.path.isdir(lang_dir):
        return out
    for code in sorted(os.listdir(lang_dir)):
        p = os.path.join(lang_dir, code, 'language.cfg')
        if code == SOURCE or not os.path.exists(p):
            continue
        assert re.match(r'^[a-z]{2,3}$', code), code
        cfg = read_cfg(p)
        cfg.setdefault('NAME', code)
        cfg.setdefault('NATIVE', cfg['NAME'])
        cfg['CODEPAGE'] = int(cfg.get('CODEPAGE', '1252'))
        cfg['ORDER'] = int(cfg.get('ORDER', '99'))
        out.append((code, cfg))
    out.sort(key=lambda x: (x[1]['ORDER'], x[0]))
    return out


# ---------------------------------------------------------------- text helpers

_PL_FOLD = {u'ą': u'a', u'ć': u'c', u'ę': u'e', u'ł': u'l', u'ń': u'n', u'ó': u'o', u'ś': u's', u'ź': u'z', u'ż': u'z',
            u'Ą': u'A', u'Ć': u'C', u'Ę': u'E', u'Ł': u'L', u'Ń': u'N', u'Ó': u'O', u'Ś': u'S', u'Ź': u'Z', u'Ż': u'Z',
            u'„': u'"', u'”': u'"', u'“': u'"', u'–': u'-', u'—': u'-', u'…': u'...', u'’': u"'", u'‘': u"'",
            u'ı': u'i', u'İ': u'I', u'ş': u's', u'Ş': u'S', u'ğ': u'g', u'Ğ': u'G', u'ß': u'ss', u'đ': u'd'}


def fold(s):
    """ASCII-ish text: Polish letters without diacritics (the last fallback, readable under any codepage)"""
    s = u''.join(_PL_FOLD.get(c, c) for c in s)
    s = unicodedata.normalize('NFKD', s)
    return u''.join(c for c in s if not unicodedata.combining(c))


_CP_ALIAS = {1250: {u'ș': u'ş', u'Ș': u'Ş', u'ț': u'ţ', u'Ț': u'Ţ'}}


def encode(s, cp):
    """text in the language's codepage; a character the codepage lacks is folded, then '?'"""
    enc = 'cp%d' % cp
    alias = _CP_ALIAS.get(cp)
    if alias:
        s = u''.join(alias.get(c, c) for c in s)
    try:
        return s.encode(enc)
    except UnicodeEncodeError:
        out = []
        for c in s:
            try:
                out.append(c.encode(enc))
            except UnicodeEncodeError:
                f = fold(c)
                try:
                    out.append(f.encode(enc))
                except UnicodeEncodeError:
                    out.append(b'?')
        return b''.join(out)


def norm_key(s):
    return re.sub(r'\s+', ' ', s).strip()


def norm_loose(s):
    return re.sub(r'[\W_]+', '', s.lower(), flags=re.UNICODE)


def similar(a, b, limit=0.75):
    a, b = norm_loose(a), norm_loose(b)
    if a == b:
        return True
    if not a or not b:
        return False
    return difflib.SequenceMatcher(None, a, b).ratio() >= limit


_PH = re.compile(r'%(?:\([A-Za-z_0-9]+\))?[-+#0]*(?:\d+|\*)?(?:\.\d+)?[sdifxXcurgeEGo%]|\{\d*\}|\[ENTER\]|\|c[0-9a-fA-F]{8}|\|[rhH]|\[(?:DELAY|TAB|ENTER)[^\]]*\]|\[[A-Z]\]')


def placeholders(s):
    return sorted(m.group(0).lower() if m.group(0).startswith('|c') else m.group(0) for m in _PH.finditer(s)
                  if m.group(0) != '%%')


def same_placeholders(pl, tr):
    a, b = placeholders(pl), placeholders(tr)
    if a == b:
        return True
    # [ENTER] line wrapping may differ in a whole translated file / long description
    a2 = [x for x in a if x != '[ENTER]']
    b2 = [x for x in b if x != '[ENTER]']
    return a2 == b2


_NUM = re.compile(r'(?<![%.\w])\d+(?:[.,]\d+)?')


def numbers(s):
    """the numbers of a text (not those of a %-placeholder or of a word like M1 / x2)"""
    return _NUM.findall(s)


def num_key(s):
    return _NUM.sub('#', norm_key(s))


_REFINE = re.compile(r'^(.*?)(\s*\+\s*\d+)$')


def split_refine(name):
    m = _REFINE.match(name)
    if m and m.group(1).strip():
        return m.group(1), m.group(2)
    return name, ''


# never in a translation (the owner's rule for player-facing text in any language); the project's own domain metin2sp.pl
# is not the game's name. A Polish source with one of them gets a translation without it (or none).
FORBIDDEN = re.compile(r'metin\w{0,3}\s*2(?![0-9]|sp)|gameforge|oficjaln|official|offiziell|ufficial|oficial|officiel|\bresm[iî]\b|tieru|'
                       r'ameria|metin2alerts|επίσημ|رسمي', re.I)

# ---------------------------------------------------------------- translation store


class Store(object):
    """one language's tables"""

    def __init__(self, code, lang_dir=None):
        self.code = code
        self.dir = os.path.join(lang_dir or LANG_DIR, code)
        self.cfg = read_cfg(os.path.join(self.dir, 'language.cfg'))
        self.keyed = {}
        self.tm = {}
        self.tm_loose = {}
        # *_orig.tsv (imported originals, regenerated by import_originals.py) first, our own tables over them
        names = sorted(os.listdir(self.dir)) if os.path.isdir(self.dir) else []
        names = [n for n in names if n.endswith('.tsv')]
        names.sort(key=lambda n: (0 if n.endswith('_orig.tsv') else 1, n))
        for name in names:
            if name.startswith('keyed'):
                for r in read_rows(os.path.join(self.dir, name)):
                    if len(r) >= 4 and r[3] != '':
                        self.keyed[(r[0], r[1])] = (r[2], r[3])
            elif name.startswith('tm'):
                for r in read_rows(os.path.join(self.dir, name)):
                    if len(r) >= 2 and r[1] != '':
                        self.tm[norm_key(r[0])] = r[1]
        for k, v in self.tm.items():
            self.tm_loose.setdefault(k.lower(), v)
        # numeric templates: a text that differs only in its numbers ("Restores 600 HP." / "Restores 230 HP.") reuses
        # a translation whose numbers are the Polish ones in the same order
        self.tm_num = {}
        for k, v in sorted(self.tm.items()):
            nk = numbers(k)
            # not for ordinals / units glued to a number ("1st", "2nd", "3x") - they change with the number
            if nk and numbers(v) == nk and not re.search(r'\d[^\W\d_]', v, re.UNICODE):
                self.tm_num.setdefault(num_key(k), _NUM.split(v))

    def candidates(self, domain, key, pl):
        """(text, how) of every table hit, best first: keyed (same / similar Polish), tm (exact, folded case),
        for a "<base>+N" name its base"""
        k = self.keyed.get((domain, key))
        if k is not None:
            src, tr = k
            if src == pl:
                yield tr, 'keyed'
            else:
                limit = 0.6 if domain in ('file', 'idesc', 'isumm') else 0.75
                if similar(src, pl, limit):
                    yield tr, 'stale'
        nk = norm_key(pl)
        t = self.tm.get(nk)
        if t is not None:
            yield t, 'tm'
        t = self.tm_loose.get(nk.lower())
        if t is not None and nk.lower() != nk:
            yield t, 'tm'
        if domain in ('item', 'mob'):
            base, suf = split_refine(pl)
            if suf:
                for t, how in self.candidates(domain, None, base):
                    yield t + suf.replace(' ', ''), 'base'
        nums = numbers(nk)
        if nums:
            parts = self.tm_num.get(num_key(nk))
            if parts is not None and len(parts) == len(nums) + 1:
                out = [parts[0]]
                for n, lit in zip(nums, parts[1:]):
                    out.append(n)
                    out.append(lit)
                yield ''.join(out), 'num'

    def lookup(self, domain, key, pl):
        for t, how in self.candidates(domain, key, pl):
            return t, how
        return None, None


class Resolver(object):
    """the lookup chain of a language: its own tables -> English -> folded Polish"""

    def __init__(self, code, lang_dir=None, en=None):
        self.code = code
        self.own = Store(code, lang_dir)
        self.en = None if code == 'en' else (en or Store('en', lang_dir))
        self.stats = {}
        self.refused = []
        self.missing = []
        self.not_own = []

    def _count(self, domain, how):
        d = self.stats.setdefault(domain, {})
        d[how] = d.get(how, 0) + 1

    def get(self, domain, key, pl, count=True):
        if pl.strip() == '' or not re.search(r'[^\W\d_]', pl, re.UNICODE):
            return pl
        own_hit = False
        result = None
        for store, tag in ((self.own, ''), (self.en, 'en-')):
            if store is None:
                continue
            for t, how in store.candidates(domain, key, pl):
                if not same_placeholders(pl, t) or FORBIDDEN.search(t):
                    if count:
                        self.refused.append((store.code, domain, key, pl, t))
                    continue
                if count:
                    self._count(domain, tag + how)
                own_hit = not tag
                result = t
                break
            if result is not None:
                break
        if count and not own_hit:
            self.not_own.append((domain, key, pl, result))
        if result is not None:
            return result
        if count:
            self._count(domain, 'fallback')
            self.missing.append((domain, key, pl))
        return fold(pl)


# ---------------------------------------------------------------- the Polish catalog


def dec(b):
    return b.decode(SOURCE_CP, 'replace')


def tsv_lines(b):
    """rows of a client tab file (CRLF / LF), keeping empty columns"""
    t = dec(b)
    return [l.split('\t') for l in t.replace('\r\n', '\n').replace('\r', '\n').split('\n')]


def has_text(s):
    return bool(re.search(r'[^\W\d_]{2}', s, re.UNICODE))


SKILL_TEXT_COLS = (2, 3, 4, 5, 6, 7, 8, 9)


def skill_text_col(col, cell):
    """skilldesc.txt: the names / descriptions (2-9) and the affect texts after the flags (a format string with
    letters, no formula)"""
    if col in SKILL_TEXT_COLS:
        return has_text(cell)
    if col < 15 or not has_text(cell):
        return False
    if re.search(r'[*()]|\b(?:k|lv|iq|str|dex|con|SkillPoint|MinATK|MaxATK|sl|min|max|floor)\b', cell):
        return False
    return True


PET_TEXT_COLS = (1, 4)

# description files read whole (the client wraps them with [ENTER])
DESC_FILES = ('empiredesc_a.txt', 'empiredesc_b.txt', 'empiredesc_c.txt', 'jobdesc_warrior.txt',
              'jobdesc_assassin.txt', 'jobdesc_sura.txt', 'jobdesc_shaman.txt', 'jobdesc_wolfman.txt', 'rules.txt',
              'fish_event_desc.txt', 'catchking_event_desc.txt', 'yutnori_event_desc.txt', 'mini_game_okey_desc.txt')


def locale_kv(b):
    """KEY -> (value, rest columns) of locale_game / locale_interface (first one of a key wins, as the client's
    dict - no: the LAST one wins there; keep the last)"""
    out = {}
    order = []
    for cols in tsv_lines(b):
        if len(cols) < 2 or not cols[0].strip() or cols[0].startswith('#'):
            continue
        k = cols[0]
        if k not in out:
            order.append(k)
        out[k] = cols
    return out, order


class Catalog(object):
    """the Polish client's texts: entries[(domain, key)] = Polish text; files = the source bytes"""

    def __init__(self):
        self.entries = {}
        self.order = []
        self.files = {}
        self.items = {}
        self.mobs = {}

    def add(self, domain, key, text):
        if (domain, key) not in self.entries:
            self.order.append((domain, key))
        self.entries[(domain, key)] = text

    def by_domain(self, domain):
        return [(k, self.entries[(d, k)]) for d, k in self.order if d == domain]


def build_catalog(get, items=None, mobs=None, py_files=None):
    """get(name) -> bytes or None for a pack file name (locale/pl/...); items / mobs: {vnum: Polish name};
    py_files: {module name: bytes} of the root python"""
    cat = Catalog()
    cat.items = dict(items or {})
    cat.mobs = dict(mobs or {})
    for v in sorted(cat.items):
        if cat.items[v].strip() and not garbled(cat.items[v]):
            cat.add('item', str(v), cat.items[v])
    for v in sorted(cat.mobs):
        if cat.mobs[v].strip() and not garbled(cat.mobs[v]):
            cat.add('mob', str(v), cat.mobs[v])
    b = get('locale/pl/itemdesc.txt')
    if b is not None:
        cat.files['itemdesc.txt'] = b
        for cols in tsv_lines(b):
            if len(cols) >= 3 and cols[0].strip().isdigit():
                if has_text(cols[2]):
                    cat.add('idesc', cols[0].strip(), cols[2])
                if len(cols) >= 4 and has_text(cols[3]):
                    cat.add('isumm', cols[0].strip(), cols[3])
    b = get('locale/pl/skilldesc.txt')
    if b is not None:
        cat.files['skilldesc.txt'] = b
        for cols in tsv_lines(b):
            if len(cols) > 2 and cols[0].strip().isdigit():
                for i, c in enumerate(cols):
                    if skill_text_col(i, c):
                        cat.add('skill', '%s:%d' % (cols[0].strip(), i), c)
    b = get('locale/pl/pet_skill.txt')
    if b is not None:
        cat.files['pet_skill.txt'] = b
        for cols in tsv_lines(b):
            if len(cols) > 4 and cols[0].strip().isdigit():
                for i in PET_TEXT_COLS:
                    if has_text(cols[i]):
                        cat.add('pet', '%s:%d' % (cols[0].strip(), i), cols[i])
    b = get('locale/pl/guildbuildinglist.txt')
    if b is not None:
        cat.files['guildbuildinglist.txt'] = b
        for cols in tsv_lines(b):
            if len(cols) > 3 and cols[0].strip().isdigit() and has_text(cols[3]):
                cat.add('gbld', cols[0].strip(), cols[3])
    for name, dom in (('locale_game.txt', 'lgame'), ('locale_interface.txt', 'lintf')):
        b = get('locale/pl/' + name)
        if b is None:
            continue
        cat.files[name] = b
        kv, order = locale_kv(b)
        for k in order:
            v = kv[k][1]
            if has_text(v):
                cat.add(dom, k, v)
    # the offline shop's texts: English in locale/common (every client), translated for the other languages
    b = get('locale/common/locale_game_ikashop.txt')
    if b is not None:
        cat.files['locale_game_ikashop.txt'] = b
        kv, order = locale_kv(b)
        for k in order:
            v = kv[k][1]
            if has_text(v):
                cat.add('ikash', k, v)
    for name in DESC_FILES:
        b = get('locale/pl/' + name)
        if b is not None:
            cat.files[name] = b
            cat.add('file', name, dec(b).replace('\r\n', '\n'))
    for mod in sorted(py_files or {}):
        for line, text in py_strings(py_files[mod]):
            cat.add('py', '%s:%d' % (mod, line), text)
    cat.py_all = set()
    for mod in sorted(py_files or {}):
        for line, text in py_strings(py_files[mod], every=True):
            cat.py_all.add(text)
    return cat


# ---------------------------------------------------------------- root python string literals

_STR = re.compile(r'''(?P<pre>\b[uUbBrR]{0,2})(?P<q>"""|\'\'\'|"|')''')


def _literals(src):
    """(line, prefix, body) of every string literal of a python 2 source (comments skipped)"""
    i, n, line = 0, len(src), 1
    while i < n:
        c = src[i]
        if c == '\n':
            line += 1
            i += 1
            continue
        if c == '#':
            j = src.find('\n', i)
            i = n if j < 0 else j
            continue
        if c in '"\'':
            pre = ''
            k = i - 1
            while k >= 0 and src[k] in 'uUbBrR' and i - k <= 2:
                pre = src[k] + pre
                k -= 1
            if k >= 0 and (src[k].isalnum() or src[k] == '_'):
                pre = ''
            q = src[i:i + 3] if src[i:i + 3] in ('"""', "'''") else c
            j = i + len(q)
            start_line = line
            raw = 'r' in pre.lower()
            while j < n:
                if src[j] == '\\' and not (raw and False):
                    j += 2
                    continue
                if src.startswith(q, j):
                    break
                if src[j] == '\n':
                    line += 1
                    if len(q) == 1:
                        break
                j += 1
            body = src[i + len(q):j]
            yield start_line, pre, body, len(q) == 3, i - len(pre), j + len(q)
            i = j + len(q)
            continue
        i += 1


def _decode_body(pre, body):
    """the bytes of a py2 str literal -> text (cp1250, as the client's strings are)"""
    if 'r' in pre.lower():
        b = body.encode('latin-1', 'replace')
    else:
        try:
            b = codecs.escape_decode(body.encode('latin-1', 'backslashreplace'))[0]
        except Exception:
            return None
    if 'u' in pre.lower():
        try:
            return b.decode('unicode_escape')
        except Exception:
            return None
    return b.decode(SOURCE_CP, 'replace')


_PL_LETTERS = set(u'ąćęłńśźżĄĆĘŁŃŚŹŻ')
PL_WORDS = set()
EN_WORDS = set()


def set_wordlists(pl_words, en_words):
    PL_WORDS.clear()
    PL_WORDS.update(pl_words)
    EN_WORDS.clear()
    EN_WORDS.update(en_words)


def words(s):
    return re.findall(r'[^\W\d_]+', s.lower(), re.UNICODE)


_MOJIBAKE = set(u'ĹŔ´˛°Ľ»ˇÁĆÇČÉĚÍÎĐŇÔŐÖ×ŘŮÚŰÜÝŢßŕáâăäĺçčéěíîďđňôőö÷řůúűüýţ˙¸¨ŞŻ®±')


_SYMBOLS = set(u'»±¸°˛´˝·¤¦§¨©«¬®¯²³µ¶¹º¼½¾¿×÷ˇ˘˙¡¢¥')


def garbled(s, polish=True):
    """Korean text read in a European codepage (the client's untranslated leftovers, unused rows); polish=False for
    a text of another language (its own accented letters are fine there)"""
    if '??' in s or sum(1 for c in s if c in _SYMBOLS) >= 2:
        return True
    if not polish:
        return False
    return sum(1 for c in s if c in _MOJIBAKE and c not in _PL_LETTERS and c not in u'óÓéáüöäí') >= 2


def looks_polish(s):
    if not has_text(s):
        return False
    if garbled(s):
        return False
    if re.match(r'^[a-z0-9_./\\:%-]+$', s) and ' ' not in s:
        return False  # identifiers, paths, keys
    if re.match(r'^[A-Z0-9_]+$', s):
        return False
    if re.search(r'(^|/)[\w\-]+\.(py|txt|tga|dds|sub|jpg|png|mse|msm|gr2|wav|mp3|cfg|json|sql)$', s, re.I):
        return False
    if s.startswith(('d:/', 'D:/', 'locale/', 'uiscript/', 'icon/', 'http')):
        return False
    if any(c in _PL_LETTERS for c in s):
        return True
    ws = words(s)
    if not ws:
        return False
    pl = sum(1 for w in ws if (w in PL_WORDS or _pl_shape(w)) and w not in EN_WORDS)
    return pl >= 1 and pl * 2 >= len([w for w in ws if len(w) > 2]) * 0.5


_PL_ENDINGS = ('ych', 'ego', 'emu', 'ami', 'ach', 'ów', 'ość', 'osc', 'ać', 'ić', 'nia', 'nie', 'cie', 'ię', 'ją',
               'ą', 'ę', 'wy', 'ny', 'na', 'ne', 'ki', 'ka', 'ko', 'aj', 'ij', 'uj', 'ym', 'im', 'om')
_PL_CLUSTERS = ('cz', 'sz', 'rz', 'dz', 'ż', 'ł', 'ś', 'ć', 'ń', 'ź', 'ą', 'ę', 'prz', 'trz', 'wsz', 'zn', 'ws', 'wz')


def _pl_shape(w):
    """a word that looks Polish (letter clusters / endings English does not have) - for strings without diacritics"""
    if len(w) < 4 or not w.isalpha():
        return False
    return any(c in w for c in _PL_CLUSTERS) and w.endswith(_PL_ENDINGS)


def py_strings(b, every=False):
    """(line, text) of the Polish display strings of a module (docstrings left out); every=True: every string
    literal with letters (the build emits any of them that has a translation)"""
    src = b.decode('latin-1')
    out = []
    # adjacent literals ("a" "b", over lines inside brackets) are one string, as python joins them
    merged = []
    for line, pre, body, triple, start, end in _literals(src):
        t = None if triple else _decode_body(pre, body)
        if merged and merged[-1][3] is not None and t is not None and re.match(r'^[\s\\]*$', src[merged[-1][2]:start]):
            l0, t0, e0, _ = merged[-1]
            merged[-1] = (l0, t0 + t, end, t)
            continue
        merged.append((line, t, end, t))
    for line, t, end, last in merged:
        if t is None or len(t) < 2 or len(t) > 1200 or not has_text(t):
            continue
        if every or looks_polish(t):
            out.append((line, t))
    return out


T_PAIR = re.compile(r'''\bT\(\s*(?P<pp>[uU]?)(?P<pq>['"])(?P<pl>(?:\\.|(?!(?P=pq)).)*)(?P=pq)\s*,\s*(?P<ep>[uU]?)(?P<eq>['"])(?P<en>(?:\\.|(?!(?P=eq)).)*)(?P=eq)\s*\)''', re.S)


def t_pairs(b):
    """(pl, en) of every T('pl', 'en') literal pair of a module (playerbot_lang.T)"""
    src = b.decode('latin-1')
    out = []
    for m in T_PAIR.finditer(src):
        pl = _decode_body(m.group('pp'), m.group('pl'))
        en = _decode_body(m.group('ep'), m.group('en'))
        if pl and en:
            out.append((pl, en))
    return out
