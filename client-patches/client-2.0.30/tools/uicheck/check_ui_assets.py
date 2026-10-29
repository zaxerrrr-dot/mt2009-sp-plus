# -*- coding: utf-8 -*-
# MT2009_PLUS_UICHECK_V1 - checks that every picture the client's python names is in the packs a PLAYER has.
#
# The player's install is a base client (etc, item, icon, ... - no listing of its base packs on the VPS) plus the
# test-plus layers: klient-test-2.37.zip, klient-test-yohara-3.0.1.zip and the packs of the build being tested
# (default /opt/metin2/cache/cY/out/pack = 3.0.4). A layer's <pack>.index replaces the lower layer's; the top layer's
# pack/Index says which packs the client opens. Only the .index files are read from the zips (and a .data only for
# the .sub files and the root .py, straight from the zip into memory - nothing is extracted to disk).
#
# The smoke-test client's "etc" pack is NOT the players' etc (it has the white dragon UI, the players' has not) and is
# never used. A name counts as being in the players' base packs only when the base client's own python names it
# (/opt/metin2/cache/tcm/ours/root, the root before our patches: the base client opened those windows, so their
# pictures are in its etc) - reported as "base".
#
# What is read: every .py of the top layer's root pack, overlaid with the repo's client-2.0.30/root (the files the next
# build packs). From each: string literals and "+"-chains of them (module constants such as ROOT_PATH = "d:/ymir
# work/..." and other modules' constants, e.g. uiScriptLocale.X, are resolved; str(i) / "%d" % i become a wildcard)
# that end in .sub/.tga/.dds/.png/.jpg/.bmp/.mse. A bare file name ("auto_system_text_bar_01.sub", passed to a helper
# that adds the folder) is tried with every folder constant of its file. Each found .sub is read and its "image"
# target checked too.
#
#   docker run --rm -v /opt/metin2:/opt/metin2 -v /tmp:/tmp m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/uicheck/check_ui_assets.py [--top <pack dir>] [--layer <zip|dir>]...
#     [--root <repo root dir>] [--changed-only] [--json <out.json>] [--files a.py,b.py]
#
# Exit code 0 always (it is a report); "MISSING" lines are the names a player has in none of his packs.
import fnmatch
import io
import json
import os
import re
import struct
import sys
import tokenize
import warnings
import zipfile
import zlib

warnings.simplefilter('ignore', DeprecationWarning)

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/c36')
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
import m2pack  # noqa: E402

DIST = '/opt/metin2/dist/aktualizacje/test-plus'
DEFAULT_LAYERS = [os.path.join(DIST, 'klient-test-2.37.zip'), os.path.join(DIST, 'klient-test-yohara-3.0.1.zip')]
DEFAULT_TOP = '/opt/metin2/cache/cY/out/pack'
DEFAULT_ROOT = os.path.normpath(os.path.join(HERE, '..', '..', 'root'))
BASE_ROOT = '/opt/metin2/cache/tcm/ours/root'
PREV_LAYER = os.path.join(DIST, 'klient-test-yohara-3.0.1.zip')        # "changed since" = differs from this root
IMG_EXT = ('.sub', '.tga', '.dds', '.png', '.jpg', '.bmp', '.mse')
WILD = '\x01'
_GC = {}


# ---------------------------------------------------------------- packs
def _index_from_bytes(blob):
    raw = m2pack.mcoz_decode(blob, m2pack.IDX_KEY)
    four, ver, cnt = struct.unpack_from('<4sII', raw, 0)
    ents = []
    for i in range(cnt):
        o = 12 + i * m2pack.ENTRY
        name = raw[o + 4:o + 165].split(b'\0')[0].decode('cp1252')
        fcrc, real, size, dcrc, pos = struct.unpack_from('<IiiIi', raw, o + 168)
        ents.append(dict(name=name, size=size, pos=pos, ctype=raw[o + 188]))
    return ents


class Layer(object):
    """a zip of a client (members pack/<x>.index) or a pack dir"""

    def __init__(self, path):
        self.path = path
        self.zip = zipfile.ZipFile(path) if path.endswith('.zip') else None
        if self.zip:
            self.members = dict((n.split('/', 1)[1].lower(), n) for n in self.zip.namelist()
                                if n.lower().startswith('pack/') and '/' in n)
        else:
            self.members = dict((n.lower(), n) for n in os.listdir(path))
        self._data = {}

    def has(self, member):
        return member.lower() in self.members

    def read(self, member):
        m = self.members[member.lower()]
        if self.zip:
            return self.zip.read(m)
        return open(os.path.join(self.path, m), 'rb').read()

    def data(self, pack):
        if pack not in self._data:
            self._data = {pack: self.read(pack + '.data')}      # one .data in memory at a time
        return self._data[pack]


class Install(object):
    """the packs a player opens: per pack name the topmost layer that has its .index"""

    def __init__(self, layers):
        self.layers = [Layer(p) for p in layers]           # bottom .. top
        top = next(l for l in reversed(self.layers) if l.has('Index'))
        ix = top.read('Index').replace(b'\r', b'').split(b'\n')
        self.index_packs = [l.strip().decode('latin1').lower() for l in ix
                            if l.strip() and l.strip() not in (b'*', b'PACK')]
        self.pack_layer = {}
        self.names = {}                                    # name -> (pack, layer, entry)
        self.unlisted = []                                 # Index packs no layer has (the base client's)
        for p in self.index_packs:
            lay = next((l for l in reversed(self.layers) if l.has(p + '.index')), None)
            if lay is None:
                self.unlisted.append(p)
                continue
            self.pack_layer[p] = lay
            for e in _index_from_bytes(lay.read(p + '.index')):
                self.names.setdefault(e['name'].lower(), (p, lay, e))     # the first registered pack wins

    def where(self, name):
        t = self.names.get(name)
        return t and (t[0], os.path.basename(t[1].path))

    def read(self, name):
        p, lay, e = self.names[name]
        return m2pack.read_entry(lay.data(p), e)


def root_pack_files(layer, pack='root'):
    """{name: bytes} of the .py in a layer's root pack"""
    ents = _index_from_bytes(layer.read(pack + '.index'))
    dat = layer.read(pack + '.data')
    return dict((e['name'].lower(), m2pack.read_entry(dat, e)) for e in ents if e['name'].lower().endswith('.py'))


def repo_root_files(root):
    out = {}
    for dp, dn, fn in os.walk(root):
        for f in fn:
            if f.lower().endswith('.py'):
                ap = os.path.join(dp, f)
                out[os.path.relpath(ap, root).replace(os.sep, '/').lower()] = open(ap, 'rb').read()
    return out


# ---------------------------------------------------------------- python -> picture names
def norm(s):
    s = s.replace('\\', '/').lower()
    while '//' in s:
        s = s.replace('//', '/')
    if s.startswith('d:ymir'):
        s = 'd:/' + s[2:]
    return s


def _str_value(tok):
    s = tok
    i = 0
    while i < len(s) and s[i] in 'rRuUbB':
        i += 1
    prefix, body = s[:i].lower(), s[i:]
    q = body[:3] if body[:3] in ('"""', "'''") else body[0]
    body = body[len(q):-len(q)]
    if 'r' not in prefix:
        try:
            body = body.encode('latin1').decode('unicode_escape', 'ignore')
        except Exception:
            pass
    return body


_FMT = re.compile(r'%[-+ #0]*\d*(?:\.\d+)?[sdixXfu]')


def _tokens(src):
    toks = []
    try:
        for t in tokenize.generate_tokens(io.StringIO(src).readline):
            if t[0] in (tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT):
                if t[0] == tokenize.NEWLINE:
                    toks.append(('NEWLINE', '\n', t[2][0]))
                continue
            toks.append((tokenize.tok_name[t[0]], t[1], t[2][0]))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        pass
    return toks


def _operand(toks, i, consts, gconsts):
    """value of the operand starting at toks[i] -> (string or None, next index)"""
    k, v, ln = toks[i]
    if k == 'STRING':
        s = ''
        while i < len(toks) and toks[i][0] == 'STRING':            # "a" "b" adjacent
            s += _str_value(toks[i][1])
            i += 1
        if i + 1 < len(toks) and toks[i][1] == '%':               # "x%d.sub" % i
            s = _FMT.sub(WILD, s)
            i = _skip_operand(toks, i + 1)
        return s, i
    if k == 'NAME':
        name = v
        j = i + 1
        while j + 1 < len(toks) and toks[j][1] == '.' and toks[j + 1][0] == 'NAME':
            name += '.' + toks[j + 1][1]
            j += 2
        if j < len(toks) and toks[j][1] in ('(', '['):
            return WILD, _skip_group(toks, j)
        if name in consts:
            return consts[name], j
        last = name.rsplit('.', 1)
        if len(last) == 2 and last[0].lower() in gconsts and last[1] in gconsts[last[0].lower()]:
            return gconsts[last[0].lower()][last[1]], j
        return WILD, j
    if v == '(':
        return WILD, _skip_group(toks, i)
    return None, i + 1


def _skip_group(toks, j):
    depth = 0
    while j < len(toks):
        if toks[j][1] in ('(', '[', '{'):
            depth += 1
        elif toks[j][1] in (')', ']', '}'):
            depth -= 1
            if depth == 0:
                return j + 1
        j += 1
    return j


def _skip_operand(toks, i):
    if i < len(toks) and toks[i][1] in ('(', '[', '{'):
        return _skip_group(toks, i)
    i += 1
    while i + 1 < len(toks) and toks[i][1] == '.':
        i += 2
    if i < len(toks) and toks[i][1] in ('(', '['):
        i = _skip_group(toks, i)
    return i


def _expr_at(toks, i, consts, gconsts):
    """a "+" chain starting at toks[i] -> (value, end)"""
    val, j = _operand(toks, i, consts, gconsts)
    if val is None:
        return None, j
    while j + 1 < len(toks) and toks[j][1] == '+':
        v2, j2 = _operand(toks, j + 1, consts, gconsts)
        if v2 is None:
            break
        val += v2
        j = j2
    return val, j


def module_consts(src, gconsts=None):
    """NAME = <string chain> anywhere (the last wins), resolved in order"""
    toks = _tokens(src)
    consts = {}
    for i in range(len(toks) - 2):
        if toks[i][0] == 'NAME' and toks[i + 1][1] == '=' and (i == 0 or toks[i - 1][1] in ('\n',)) \
                and toks[i + 2][0] in ('STRING', 'NAME'):
            v, j = _expr_at(toks, i + 2, consts, gconsts or {})
            if v is not None and j < len(toks) and toks[j][1] == '\n' and v.replace(WILD, ''):
                consts[toks[i][1]] = v
    return consts


def refs_of(src, consts, gconsts):
    """[(line, name-or-pattern, kind)] kind: 'path' | 'pattern' | 'bare'"""
    toks = _tokens(src)
    out = []
    i = 0
    folders = sorted(set(v for v in consts.values() if WILD not in v and '/' in v and
                         not v.lower().endswith(IMG_EXT)))
    while i < len(toks):
        k = toks[i][0]
        if k in ('STRING', 'NAME') and not (i and toks[i - 1][1] in ('+', '.')):
            v, j = _expr_at(toks, i, consts, gconsts)
            if v is not None and v.replace(WILD, ''):
                low = v.lower().rstrip()
                if low.endswith(IMG_EXT) and len(low) > 4:
                    n = _FMT.sub(WILD, norm(v.strip()))
                    if '/' not in n.replace(WILD, ''):
                        out.append((toks[i][2], n, 'bare', folders))
                    elif WILD in n:
                        out.append((toks[i][2], n, 'pattern', None))
                    else:
                        out.append((toks[i][2], n, 'path', None))
        i += 1
    return out


def sub_targets(sub_name, blob):
    """the names the exe opens for a .sub (EterLib GrpSubImage.cpp): "version 2.0" - the image next to the .sub when
    the .sub was opened by a backslash path, else the image name as it is; any other version - "d:/ymir work/ui/" +
    image (CGraphicSubImage::m_SearchPath). None: no image line."""
    m = re.search(rb'(?im)^\s*image\s+"([^"]+)"', blob)
    if not m:
        return None
    img = m.group(1).decode('latin1')
    v = re.search(rb'(?im)^\s*version\s+(\S+)', blob)
    if v and v.group(1) == b'2.0':
        return [norm(sub_name.rsplit('/', 1)[0] + '/' + img), norm(img)]
    return [norm('d:/ymir work/ui/' + img)]


# ---------------------------------------------------------------- the check
def check(files, install, base_names, extra=None, only=None):
    """files: {py name: bytes}. Returns {py name: [record]}"""
    extra = extra or {}
    gconsts = {}
    for fn, b in files.items():
        mod = fn.rsplit('/', 1)[-1][:-3]
        k = (fn, zlib.crc32(b), len(b))
        if k not in _GC:
            _GC[k] = module_consts(b.decode('latin1'))
        gconsts[mod] = _GC[k]
    have = set(install.names) | set(extra)
    res = {}
    subs_checked = {}

    def status(n):
        if n in extra:
            return 'new-pack', extra[n]
        w = install.where(n)
        if w:
            return 'ok', '%s (%s)' % w
        if n in base_names:
            return 'base', 'named by the base client root'
        return 'MISSING', None

    def sub_check(n):
        if n in subs_checked:
            return subs_checked[n]
        r = None
        try:
            blob = extra[n][1] if n in extra and isinstance(extra[n], tuple) else \
                install.read(n) if n in install.names else None
        except Exception as ex:
            blob, r = None, 'unreadable: %s' % ex
        if blob is not None:
            ts = sub_targets(n, blob)
            if ts is None:
                r = 'no image line'
            elif all(status(t)[0] == 'MISSING' for t in ts):
                r = 'image %s MISSING' % ts[0]
        subs_checked[n] = r
        return r

    for fn in sorted(files):
        if only and fn not in only:
            continue
        mod = fn.rsplit('/', 1)[-1][:-3]
        src = files[fn].decode('latin1')
        recs = []
        seen = set()
        for ln, n, kind, folders in refs_of(src, gconsts[mod], gconsts):
            if (n, kind) in seen:
                continue
            seen.add((n, kind))
            if kind == 'path':
                st, w = status(n)
                rec = dict(line=ln, name=n, status=st, where=w)
                if st in ('ok', 'new-pack') and n.endswith('.sub'):
                    s = sub_check(n)
                    if s:
                        rec['sub'] = s
                        rec['status'] = 'SUB-TARGET-MISSING'
                recs.append(rec)
            elif kind == 'pattern':
                rx = re.compile('^' + re.escape(n).replace(re.escape(WILD), '.*') + '$')
                hits = [x for x in have | base_names if rx.match(x)]
                recs.append(dict(line=ln, name=n.replace(WILD, '*'), status='ok' if hits else 'PATTERN-NO-MATCH',
                                 where='%d match(es)' % len(hits)))
            else:
                cands = [norm(f + n) for f in folders] if folders else []
                if WILD in n:
                    recs.append(dict(line=ln, name=n.replace(WILD, '*'), status='bare-pattern', where=None))
                    continue
                found = [(c, status(c)) for c in cands if status(c)[0] != 'MISSING']
                if found:
                    c, (st, w) = found[0]
                    rec = dict(line=ln, name=c, status=st, where=w, bare=n)
                    if c.endswith('.sub') and st in ('ok', 'new-pack'):
                        s = sub_check(c)
                        if s:
                            rec['sub'] = s
                            rec['status'] = 'SUB-TARGET-MISSING'
                    recs.append(rec)
                elif cands:
                    recs.append(dict(line=ln, name=cands[0] if len(cands) == 1 else n, status='MISSING',
                                     where=None, bare=n, tried=cands))
                else:
                    recs.append(dict(line=ln, name=n, status='bare-unresolved', where=None))
        res[fn] = recs
    return res


def install_has(inst, n, base=()):
    """item_list models live in the base packs (item, monster ...): only the icon is decided; a .gr2 under a
    base pack folder counts as there"""
    if n in inst.names or n in base:
        return True
    if n.endswith('.gr2'):
        return True
    return False


def base_root_names(base_root=BASE_ROOT, files=None):
    """the names the base client's own python opens (its windows worked: the names are in its packs)"""
    if files is None:
        files = repo_root_files(base_root) if os.path.isdir(base_root) else {}
    g = dict((fn.rsplit('/', 1)[-1][:-3], module_consts(b.decode('latin1'))) for fn, b in files.items())
    names = set()
    for fn, b in files.items():
        for ln, n, kind, folders in refs_of(b.decode('latin1'), g[fn.rsplit('/', 1)[-1][:-3]], g):
            if kind == 'path':
                names.add(n)
            elif kind == 'bare' and folders:
                names.update(norm(f + n) for f in folders)
    return names


BAD = ('MISSING', 'SUB-TARGET-MISSING', 'PATTERN-NO-MATCH')
_CACHE = {}


def feature_problems(out_dir, py_names, names=(), root=DEFAULT_ROOT, layers=None):
    """for the verifiers: the players' install (2.37 + 3.0.1 zips + OUT) against the pictures the given root .py
    (names relative to root, e.g. 'uiscript/autohunttestwindow.py') and the given in-pack names open. Returns
    (problems, install, count)."""
    key = tuple(list(DEFAULT_LAYERS if layers is None else layers) + [out_dir])
    if key not in _CACHE:
        inst = Install(list(key))
        _CACHE[key] = (inst, root_pack_files(inst.pack_layer['root']) if 'root' in inst.pack_layer else {},
                       base_root_names())
    inst, rootf, base = _CACHE[key]
    files = {}
    for n in py_names:
        files[n.lower()] = open(os.path.join(root, n), 'rb').read()
    # the other modules' constants (uiScriptLocale.X ...) from the root pack the install opens
    allf = dict(rootf)
    allf.update(files)
    res = check(allf, inst, base, only=set(files))
    probs, count = [], 0
    for fn in sorted(res):
        for r in res[fn]:
            count += 1
            if r['status'] in BAD:
                probs.append('%s:%s %s %s%s' % (fn, r['line'], r['status'], r['name'],
                                                 (' (' + r['sub'] + ')') if r.get('sub') else ''))
    for n in names:
        n = norm(n)
        count += 1
        if n not in inst.names and n not in base:
            probs.append('%s: in no pack of the players\' install' % n)
        elif n.endswith('.sub') and n in inst.names:
            ts = sub_targets(n, inst.read(n))
            if ts and all(t not in inst.names and t not in base for t in ts):
                probs.append('%s: its image %s in no pack' % (n, ts[0]))
    return probs, inst, count


def main(argv):
    layers, top, root, out_json, changed_only, only = list(DEFAULT_LAYERS), DEFAULT_TOP, DEFAULT_ROOT, None, False, None
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == '--top':
            top = argv[i + 1]; i += 2
        elif a == '--layer':
            if layers is DEFAULT_LAYERS or layers == DEFAULT_LAYERS:
                layers = []
            layers.append(argv[i + 1]); i += 2
        elif a == '--root':
            root = argv[i + 1]; i += 2
        elif a == '--json':
            out_json = argv[i + 1]; i += 2
        elif a == '--changed-only':
            changed_only = True; i += 1
        elif a == '--files':
            only = set(x.strip().lower() for x in argv[i + 1].split(',')); i += 2
        else:
            raise SystemExit('unknown argument %s' % a)
    inst = Install(layers + [top])
    topl = inst.layers[-1]
    files = root_pack_files(inst.pack_layer['root']) if 'root' in inst.pack_layer else {}
    if root and os.path.isdir(root):
        files.update(repo_root_files(root))
    prev, shipped = {}, set()
    for lp in DEFAULT_LAYERS:                       # what the players' earlier roots already named
        try:
            fs = root_pack_files(Layer(lp))
        except Exception:
            continue
        shipped |= base_root_names(files=fs)
        if lp == PREV_LAYER:
            prev = fs
    changed = set(fn for fn, b in files.items() if prev.get(fn) != b)
    if changed_only:
        only = (only or set(files)) & changed
    base = base_root_names()
    res = check(files, inst, base, only=only)
    bad = BAD
    total = 0
    print('layers: %s' % ' + '.join(os.path.basename(l.path) if l.zip else l.path for l in inst.layers))
    print('packs in Index: %d, with a listing: %d, base packs with no listing: %s' % (
        len(inst.index_packs), len(inst.pack_layer), ' '.join(inst.unlisted)))
    print('root .py checked: %d (changed since 3.0.1: %d), base-root names: %d' % (
        len(res), len(changed & set(res)), len(base)))
    for fn in sorted(res):
        miss = [r for r in res[fn] if r['status'] in bad]
        if not miss:
            continue
        total += len(miss)
        print('\n== %s%s  (%d missing)' % (fn, '  [changed since 3.0.1]' if fn in changed else '', len(miss)))
        for r in miss:
            r['shipped_before'] = r['name'] in shipped
            print('  %-18s L%-5s %s%s%s' % (r['status'], r['line'], r['name'],
                                            '  [named by the 2.37/3.0.1 root]' if r['shipped_before'] else '',
                                          ('  (' + r['sub'] + ')') if r.get('sub') else
                                          ('  (bare "%s", tried %d folder(s))' % (r['bare'], len(r.get('tried', []))))
                                          if r.get('bare') and r['status'] == 'MISSING' else ''))
    # gamedata/item_list.txt: the icon (and the model) of every item - the rows new or changed since 3.0.1 flagged
    il_res = []
    try:
        il = inst.read('gamedata/item_list.txt').decode('latin1')
        prev_il = set()
        try:
            pl = Layer(PREV_LAYER)
            ents = dict((e['name'].lower(), e) for e in _index_from_bytes(pl.read('gamedata.index')))
            prev_il = set(m2pack.read_entry(pl.read('gamedata.data'), ents['gamedata/item_list.txt'])
                          .decode('latin1').replace('\r', '').split('\n'))
        except Exception:
            pass
        for row in il.replace('\r', '').split('\n'):
            t = row.split('\t')
            if len(t) < 3 or not t[0].strip().isdigit():
                continue
            for col in t[2:4]:
                n = norm(col.strip())
                if not n or not n.endswith(IMG_EXT + ('.gr2',)):
                    continue
                if install_has(inst, n, base):
                    continue
                il_res.append(dict(vnum=t[0].strip(), name=n, new=row not in prev_il))
    except KeyError:
        pass
    # (the old rows' icons are mostly in the base packs "icon"/"item" of the base client - only counted)
    print('\n== gamedata/item_list.txt  (rows new or changed since 3.0.1 with an icon in no listed pack: %d;'
          ' old rows not in a listed pack: %d - the base client\'s icon/item packs)' % (
              sum(1 for r in il_res if r['new']), sum(1 for r in il_res if not r['new'])))
    for r in il_res:
        if r['new']:
            print('  %-18s %-7s %s' % ('MISSING', r['vnum'], r['name']))
    total += sum(1 for r in il_res if r['new'])
    print('\nTOTAL missing: %d (in %d root file(s) + item_list)' % (
        total, sum(1 for fn in res if any(r['status'] in bad for r in res[fn]))))
    if out_json:
        json.dump(dict(changed=sorted(changed), results=res, unlisted=inst.unlisted, item_list=il_res), open(out_json, 'w'),
                  indent=1, sort_keys=True)


if __name__ == '__main__':
    main(sys.argv[1:])
