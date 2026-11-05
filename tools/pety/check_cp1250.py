#!/usr/bin/env python3
"""check_cp1250.py [file ...] -- MT2009_PLUS_GROWTH_PET_V1: fails (exit 1) on the two ways the pet's Polish chat texts
went wrong in 3.0.13 (Yohara list 3.0.14, item 5):

  (a) a C hex escape followed by a hex digit in the same literal: "mo\\xbfe" is ONE escape (\\xbfe - C reads every hex
      digit) - the letters are lost; write "mo\\xbf" "e";
  (b) ISO-8859-2 bytes where the game and the client speak CP1250: \\xb6 (s acute), \\xb1 (a ogonek), \\xbc (z acute),
      \\xa6, \\xa1, \\xac (the capitals) - in CP1250 they are \\x9c, \\xb9, \\x9f, \\x8c, \\xa5, \\x8f.

Checked by default: the pet's game sources (overlay growth_pet*.cpp / .h), the engine edits and installed files of
server-patches/pety, and pety.sql (its _cp1250 X'..' literals and any raw bytes). Other files can be given (C/C++,
.json with C code, .sql, .quest / .txt in CP1250).
"""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
ISO_ONLY = {0xb6: 0x9c, 0xb1: 0xb9, 0xbc: 0x9f, 0xa6: 0x8c, 0xa1: 0xa5, 0xac: 0x8f}

ESC_SWALLOW = re.compile(r'\\x[0-9a-fA-F]{2}[0-9a-fA-F]')
ESC_ISO = re.compile(r'\\x(?:b6|b1|bc|a6|a1|ac)(?![0-9a-fA-F])', re.I)
SQL_HEX = re.compile(r"_cp1250\s+X'([0-9A-Fa-f]*)'")


def default_files():
    out = []
    out += sorted(glob.glob(os.path.join(REPO, 'linux-port/overlays/playerbot/src/game/src/growth_pet*')))
    out.append(os.path.join(REPO, 'server-patches/pety/edits.json'))
    out += sorted(p for p in glob.glob(os.path.join(REPO, 'server-patches/pety/files/**/*'), recursive=True)
                  if os.path.isfile(p))
    out.append(os.path.join(REPO, 'linux-port/docker/mariadb/playerbot/pety.sql'))
    return out


def check_code(name, text, errors):
    for no, line in enumerate(text.split('\n'), 1):
        for m in ESC_SWALLOW.finditer(line):
            errors.append('%s:%d: escape swallows the next letter: %s' % (name, no, m.group(0)))
        for m in ESC_ISO.finditer(line):
            errors.append('%s:%d: ISO-8859-2 byte, not CP1250: %s' % (name, no, m.group(0)))


def check_bytes(name, data, errors, what='raw byte'):
    for i, b in enumerate(data):
        if b in ISO_ONLY:
            errors.append('%s: %s 0x%02x (ISO-8859-2; CP1250 is 0x%02x) at %d' % (name, what, b, ISO_ONLY[b], i))


def check_file(path, errors):
    rel = os.path.relpath(path, REPO)
    data = open(path, 'rb').read()
    if path.endswith('.json'):
        try:
            doc = json.loads(data.decode('utf-8'))
        except ValueError:
            doc = None
        texts = []

        def walk(v):
            if isinstance(v, str):
                texts.append(v)
            elif isinstance(v, list):
                for x in v:
                    walk(x)
            elif isinstance(v, dict):
                for x in v.values():
                    walk(x)
        walk(doc)
        for i, t in enumerate(texts):
            check_code('%s[%d]' % (rel, i), t, errors)
        return
    if path.endswith('.sql'):
        text = data.decode('utf-8', 'replace')
        for m in SQL_HEX.finditer(text):
            check_bytes(rel, bytes.fromhex(m.group(1)), errors, "_cp1250 X'..' byte")
        check_code(rel, text, errors)
        return
    try:
        text = data.decode('utf-8')
        raw_cp1250 = False
    except UnicodeDecodeError:
        text = data.decode('latin-1')
        raw_cp1250 = True
    check_code(rel, text, errors)
    if raw_cp1250:
        check_bytes(rel, data, errors)


def main():
    files = sys.argv[1:] or default_files()
    errors = []
    for f in files:
        if not os.path.exists(f):
            errors.append('%s: missing' % f)
            continue
        check_file(os.path.abspath(f), errors)
    for e in errors:
        print(e)
    print('check_cp1250: %d file(s), %d problem(s)' % (len(files), len(errors)))
    sys.exit(1 if errors else 0)


if __name__ == '__main__':
    main()
