# -*- coding: utf-8 -*-
# MT2009_PLUS_ROOT_ENCODING_CHECK_V1 - every .py in the built root pack declares only an encoding the client's
# embedded Python 2.7 decodes with its built-in codecs: ascii, latin-1 (iso-8859-1) or utf-8. Anything else
# (cp1250, cp1252, ...) aborts the client when the module is imported - 3.0.6 died at the character select with
# "SyntaxError: unknown encoding: cp1250 (questrenewal.py, line 0)". A utf-8 file must also decode as utf-8.
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/uicheck/verify_root_encoding.py \
#     <OUT pack dir with root.index/root.data | extracted root dir>
import os
import re
import sys

ALLOWED = {'ascii': 'ascii', 'us-ascii': 'ascii', 'utf-8': 'utf-8', 'utf8': 'utf-8',
           'latin-1': 'latin-1', 'latin1': 'latin-1', 'iso-8859-1': 'latin-1', 'iso8859-1': 'latin-1',
           'iso-latin-1': 'latin-1'}
COOKIE = re.compile(br'^[ \t\f]*#.*?coding[:=][ \t]*([-\w.]+)')


def cookie(raw):
    """PEP 263: the declaration counts only on line 1 or 2 (line 2 only when line 1 is a comment / blank)."""
    lines = raw.split(b'\n', 2)[:2]
    if lines and lines[0].startswith(b'\xef\xbb\xbf'):
        lines[0] = lines[0][3:]
    for i, line in enumerate(lines):
        m = COOKIE.match(line)
        if m:
            return m.group(1).decode('ascii', 'replace')
        if i == 0 and not re.match(br'^[ \t\f]*(#.*)?\r?$', line):
            break
    return None


def problems(name, raw):
    out = []
    enc = cookie(raw)
    bom = raw.startswith(b'\xef\xbb\xbf')
    if enc is None:
        return []
    norm = ALLOWED.get(enc.lower().replace('_', '-'))
    if norm is None:
        return ['%s: coding %r - the client has no such codec (use latin-1 for cp125x bytes, or utf-8)' % (name, enc)]
    if bom and norm != 'utf-8':
        out.append('%s: UTF-8 BOM with coding %r' % (name, enc))
    if norm == 'utf-8':
        try:
            raw.decode('utf-8')
        except UnicodeDecodeError as e:
            out.append('%s: declares utf-8 but byte %d is not utf-8' % (name, e.start))
    if norm == 'ascii':
        try:
            raw.decode('ascii')
        except UnicodeDecodeError as e:
            out.append('%s: declares ascii but byte %d is not ascii' % (name, e.start))
    return out


def files(src):
    if os.path.exists(os.path.join(src, 'root.index')):
        sys.path.insert(0, '/opt/metin2/cache/c36')
        sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
        import m2pack
        import packlib
        _, _, ents = m2pack.read_index(os.path.join(src, 'root.index'))
        data = packlib.rd(os.path.join(src, 'root.data'))
        for e in ents:
            if e['name'].endswith('.py'):
                yield e['name'], m2pack.read_entry(data, e)
    else:
        for dp, _, fn in os.walk(src):
            for f in fn:
                if f.endswith('.py'):
                    p = os.path.join(dp, f)
                    yield os.path.relpath(p, src).replace(os.sep, '/'), open(p, 'rb').read()


def main():
    src = [a for a in sys.argv[1:] if not a.startswith('--')][0]
    n, decl, bad = 0, {}, []
    for name, raw in files(src):
        n += 1
        enc = cookie(raw)
        if enc:
            decl[enc.lower()] = decl.get(enc.lower(), 0) + 1
        bad += problems(name, raw)
    print('root encoding: %d .py file(s), declared %s, %d problem(s)' % (
        n, ', '.join('%s x%d' % kv for kv in sorted(decl.items())) or 'none', len(bad)))
    for b in bad:
        print('  ' + b)
    if not n:
        print('  no .py files found in %s' % src)
        sys.exit(1)
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
