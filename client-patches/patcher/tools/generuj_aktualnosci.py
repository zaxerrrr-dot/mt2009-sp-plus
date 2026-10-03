#!/usr/bin/env python3
"""MT2009 PLUS Patcher - builds news.json (the news box of the patcher).

The patcher reads <News> = a JSON array of NewsItem (N2Play Patcher format):

    {"newsType": 2,           0 = WYDARZENIE, 1 = NOWOŚĆ, 2 = AKTUALIZACJA
     "topic": "Klient 2.0.28", the big title (about 3 lines of ~12 letters)
     "creator": "MT2009 PLUS", orange text next to the type
     "threadUrl": "https://...", optional; the title is then clickable
     "date": "2026-09-29",     kept in the JSON, not shown
     "message": "...",         kept in the JSON, not shown
     "avatarLink": ""}         not shown

Source: aktualnosci.md (next to this folder's README), entries in order:

    ## AKTUALIZACJA | Klient 2.0.28
    autor: MT2009 PLUS
    link: https://metin2sp.pl/zmiany.php
    data: 2026-09-29
    Any further lines = "message".

--changelog CHANGELOG.md --ile N puts the N newest CHANGELOG entries before
them (type AKTUALIZACJA, title "Serwer X.Y.Z" / "Klient X.Y.Z", the date as
the author, link to the change list).
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TYPES = {'WYDARZENIE': 0, 'EVENT': 0, 'NOWOSC': 1, 'NOWOŚĆ': 1, 'NEWS': 1, 'AKTUALIZACJA': 2, 'UPDATE': 2}
MAX_TOPIC = 40
CHANGES_URL = 'https://metin2sp.pl/zmiany.php'


def parse_md(path):
    items = []
    cur = None
    with open(path, encoding='utf-8-sig') as f:
        for n, raw in enumerate(f, 1):
            line = raw.rstrip('\n').rstrip('\r')
            if line.startswith('## '):
                head = line[3:]
                if '|' not in head:
                    sys.exit('%s:%d: nagłówek musi mieć postać "## TYP | Tytuł"' % (path, n))
                typ, topic = [x.strip() for x in head.split('|', 1)]
                if typ.upper() not in TYPES:
                    sys.exit('%s:%d: nieznany typ "%s" (WYDARZENIE, NOWOŚĆ, AKTUALIZACJA)' % (path, n, typ))
                cur = {'newsType': TYPES[typ.upper()], 'topic': topic, 'creator': 'MT2009 PLUS',
                       'threadUrl': '', 'date': '', 'message': '', 'avatarLink': ''}
                items.append(cur)
                continue
            if cur is None:
                continue          # file header / comments before the first entry
            m = re.match(r'^(autor|link|data)\s*:\s*(.*)$', line, re.I)
            if m and not cur['message']:
                key = {'autor': 'creator', 'link': 'threadUrl', 'data': 'date'}[m.group(1).lower()]
                cur[key] = m.group(2).strip()
            elif line.strip() or cur['message']:
                cur['message'] = (cur['message'] + '\n' + line).strip('\n') if cur['message'] else line.strip()
    for it in items:
        it['message'] = it['message'].strip()
    return items


def from_changelog(path, count):
    # MT2009_PLUS_PATCHER_NEWS_AUTO_V1: "## X.Y.Z - date - title" and
    # "## Klient X.Y.Z - date[ - title]"; a client entry without a title takes
    # its first bullet as the message.
    items = []
    with open(path, encoding='utf-8') as f:
        lines = f.read().splitlines()
    for i, line in enumerate(lines):
        m = re.match(r'^## (Klient )?([0-9][0-9.]*) \S (\d{4})-(\d\d)-(\d\d)(?: \S (.*))?$', line.strip())
        if not m:
            continue
        client, ver, y, mo, d, title = m.groups()
        title = (title or '').strip()
        if not title:
            for nxt in lines[i + 1:]:
                if nxt.startswith('## '):
                    break
                if nxt.lstrip().startswith('- '):
                    title = re.sub(r'\*\*|`', '', nxt.lstrip()[2:]).strip()
                    if len(title) > 200:
                        title = title[:197].rstrip() + '...'
                    break
        items.append({'newsType': 2, 'topic': ('Klient ' if client else 'Serwer ') + ver,
                      'creator': '%s.%s.%s' % (d, mo, y), 'threadUrl': CHANGES_URL,
                      'date': '%s-%s-%s' % (y, mo, d), 'message': title, 'avatarLink': ''})
        if len(items) >= count:
            break
    return items


def main():
    ap = argparse.ArgumentParser(description='Buduje news.json patchera MT2009 PLUS.',
                                 formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument('--zrodlo', default=os.path.join(HERE, '..', 'aktualnosci.md'), help='plik z aktualnościami (domyślnie aktualnosci.md)')
    ap.add_argument('--changelog', help='CHANGELOG.md repozytorium - dokłada najnowsze wpisy')
    ap.add_argument('--ile', type=int, default=2, help='ile wpisów z CHANGELOG (domyślnie 2)')
    ap.add_argument('--wyjscie', default='/opt/metin2/dist/patcher/news.json', help='plik wyjściowy (domyślnie %(default)s)')
    args = ap.parse_args()

    items = parse_md(args.zrodlo) if args.zrodlo and os.path.exists(args.zrodlo) else []
    if args.changelog:
        # The newest releases first, then the standing entries of aktualnosci.md.
        items = from_changelog(args.changelog, args.ile) + items
    for it in items:
        if len(it['topic']) > MAX_TOPIC:
            print('UWAGA: długi tytuł (%d znaków, zmieści się ok. %d): %s' % (len(it['topic']), MAX_TOPIC, it['topic']))
        if it['threadUrl'] and not re.match(r'^https?://', it['threadUrl']):
            sys.exit('Link musi zaczynać się od http:// lub https://: %s' % it['threadUrl'])
    os.makedirs(os.path.dirname(os.path.abspath(args.wyjscie)), exist_ok=True)
    tmp = args.wyjscie + '.tmp'
    with open(tmp, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(items, f, ensure_ascii=False, indent=1)
        f.write('\n')
    os.chmod(tmp, 0o644)
    os.replace(tmp, args.wyjscie)
    print('Zapisano %s: %d wpisów' % (args.wyjscie, len(items)))
    for it in items:
        print('  [%d] %s - %s' % (it['newsType'], it['topic'], it['creator']))


if __name__ == '__main__':
    main()
