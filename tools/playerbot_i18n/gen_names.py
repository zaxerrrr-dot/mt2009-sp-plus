#!/usr/bin/env python3
"""Item and monster names per language for the bots' chat (playerbot_i18n.h).

Reads the dumped protos' name tables of the reference sources
(Tools/Dump Proto/share/<lang>/item_names.txt, mob_names.txt - each in its
language's Windows code page) and writes them as UTF-8 "vnum<TAB>name" to
linux-port/docker/game/playerbot_i18n/names/. The game core matches a Polish
name of a line to its vnum through its own protos and says the reader's name.

    gen_names.py [--src DIR] [lang ...]
"""
import argparse, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', '..', 'linux-port/docker/game/playerbot_i18n/names')
SRC = '/opt/metin2/cache/owsap/Tools/Tools/Dump Proto/share'
PAGES = {'en': 1252, 'de': 1252, 'es': 1252, 'fr': 1252, 'it': 1252, 'pt': 1252,
         'cz': 1250, 'hu': 1250, 'ro': 1250, 'tr': 1254, 'gr': 1253, 'ae': 1256}
BANNED = ('metin2', 'gameforge')


def convert(path, page, out):
    rows = 0
    with open(path, 'rb') as fp, open(out, 'w', encoding='utf-8', newline='\n') as w:
        for raw in fp:
            line = raw.rstrip(b'\r\n').decode('cp%d' % page, 'replace')
            parts = line.split('\t')
            if len(parts) < 2 or not parts[0].strip().isdigit():
                continue
            name = parts[1].strip()
            if not name or any(b in name.lower() for b in BANNED):
                continue
            w.write('%s\t%s\n' % (parts[0].strip(), name))
            rows += 1
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', default=SRC)
    ap.add_argument('langs', nargs='*')
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    for lang in a.langs or sorted(PAGES):
        for kind in ('item_names', 'mob_names'):
            src = os.path.join(a.src, lang, kind + '.txt')
            if not os.path.exists(src):
                continue
            n = convert(src, PAGES[lang], os.path.join(OUT, '%s_%s.txt' % (kind, lang)))
            print(lang, kind, n)


if __name__ == '__main__':
    main()
