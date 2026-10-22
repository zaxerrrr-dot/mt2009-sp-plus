#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""port_las237.py [--ref claude/yohara-3] [--yohara /opt/metin2/git/wt-yohara]     (host python3)

MT2009_PLUS_237_ZAKLETY_LAS_V1 / MT2009_PLUS_237_MAPS90_V1 - the 2.x line (2.37) takes Zaklety Las (353) and the
server files of the level-90 maps (301-304) from the Yohara branch, where tools/yohara_zaklety/gen_yzaklety.py and the
cape301 / maps302 work made them. The generator itself needs half of Yohara (its items, maps, chests, the PB / SZC
forests), so the 2.x line does not run it: this script copies its OUTPUT from the given git ref, file for file, and
leaves out what the 2.x world has not:

  * mob_drop_item.yohara_zaklety.txt / special_item_group.yohara_zaklety.txt: a row whose item vnum is in no item
    table of this tree (mariadb/playerbot/item_proto.mt2009plus.sql, the mod's item SQL files, apply.sh's own
    INSERTs, yohara_items_zaklety.sql) is dropped and the group renumbered (a group stops reading at the first index
    it lacks); "exp" / "gold" rows stay; every dropped row is printed and named in the file's header;
  * everything else verbatim (the map folder, the motions, the groups, the mob / item / element SQL, the cape's and
    302-304's server_attr).

Run it again after the Yohara branch regenerates these files; never edit the outputs by hand. Idempotent.
"""
import argparse
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
M = 'MT2009_PLUS_237_ZAKLETY_LAS_V1'

GAME = 'linux-port/docker/game'
PB = 'linux-port/docker/mariadb/playerbot'
# verbatim: directories (every tracked file under them) and files
COPY_DIRS = [GAME + '/yohara_zaklety/map', GAME + '/yohara_zaklety/data',
             GAME + '/cape301', GAME + '/maps302']
COPY_FILES = [GAME + '/yohara_zaklety/group.yohara_zaklety.txt', GAME + '/yohara_zaklety/spawned.txt',
              PB + '/yohara_zaklety.sql', PB + '/yohara_items_zaklety.sql', PB + '/yohara_zaklety_zywioly.sql',
              PB + '/playerbot_core_handover.sql']
FILTER_DROP = GAME + '/yohara_zaklety/mob_drop_item.yohara_zaklety.txt'
FILTER_CHEST = GAME + '/yohara_zaklety/special_item_group.yohara_zaklety.txt'
ITEM_SQL = ['item_proto.mt2009plus.sql', 'wiki_nowe.sql', 'zodiak.sql', 'arezzo_costumes.sql',
            'zywioly_talizmany.sql', 'yohara_items_zaklety.sql']


def git(yohara, *args):
    return subprocess.run(['git', '-C', yohara] + list(args), check=True, stdout=subprocess.PIPE).stdout


def known_items():
    have = set()
    pb = os.path.join(REPO, PB)
    for f in ITEM_SQL:
        p = os.path.join(pb, f)
        if not os.path.exists(p):
            continue
        for m in re.finditer(rb'^\((\d+),', open(p, 'rb').read(), re.M):
            have.add(int(m.group(1)))
    # apply.sh's own INSERT ... item_proto blocks: every row "(vnum, ..." until the statement's end
    on = False
    for line in open(os.path.join(pb, 'apply.sh'), 'rb').read().split(b'\n'):
        if b'INSERT' in line.upper():
            on = b'item_proto' in line
        m = re.match(rb'^\s*(?:VALUES\s*)?\((\d+),', line) if on else None
        if m:
            have.add(int(m.group(1)))
        if on and line.rstrip().endswith(b';'):
            on = False
    return have


def filter_groups(text, have, what):
    """text: cp1250 bytes of a group file. Drops item rows whose vnum is unknown, renumbers each group."""
    out, dropped = [], []
    in_group = False
    idx = 0
    group = ''
    for line in text.split(b'\n'):
        s = line.rstrip(b'\r')
        if s.strip().startswith(b'Group'):
            group = s.split()[1].decode('ascii', 'replace')
        if s.strip() == b'{':
            in_group, idx = True, 0
            out.append(line)
            continue
        if s.strip() == b'}':
            in_group = False
            out.append(line)
            continue
        m = re.match(rb'^(\s*)(\d+)(\s+)(\S+)(.*)$', s) if in_group else None
        if m:
            v = m.group(4)
            if v.isdigit() and int(v) not in have:
                name = m.group(5).decode('cp1250').split('--', 1)[-1].strip() if b'--' in m.group(5) else ''
                dropped.append('%s %s%s' % (group, v.decode(), ' (%s)' % name if name else ''))
                continue
            idx += 1
            out.append(m.group(1) + str(idx).encode() + m.group(3) + m.group(4) + m.group(5)
                       + (b'\r' if line.endswith(b'\r') else b''))
            continue
        out.append(line)
    body = b'\n'.join(out)
    if dropped:
        note = ('// %s: the 2.x line (2.37) leaves out what its world has not (tools/las237/port_las237.py): %s\n'
                % (M, '; '.join(dropped))) if what == 'drop' else \
               ('# %s: the 2.x line (2.37) leaves out what its world has not (tools/las237/port_las237.py): %s\n'
                % (M, '; '.join(dropped)))
        body = note.encode('cp1250') + body
    return body, dropped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ref', default='claude/yohara-3')
    ap.add_argument('--yohara', default='/opt/metin2/git/wt-yohara')
    a = ap.parse_args()
    files = list(COPY_FILES)
    for d in COPY_DIRS:
        files += git(a.yohara, 'ls-tree', '-r', '--name-only', a.ref, d).decode().split()
    n = 0
    for f in files:
        data = git(a.yohara, 'show', '%s:%s' % (a.ref, f))
        dst = os.path.join(REPO, f)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if not os.path.exists(dst) or open(dst, 'rb').read() != data:
            open(dst, 'wb').write(data)
            n += 1
    have = known_items()
    for f, what in ((FILTER_DROP, 'drop'), (FILTER_CHEST, 'chest')):
        data = git(a.yohara, 'show', '%s:%s' % (a.ref, f))
        body, dropped = filter_groups(data, have, what)
        dst = os.path.join(REPO, f)
        if not os.path.exists(dst) or open(dst, 'rb').read() != body:
            open(dst, 'wb').write(body)
            n += 1
        for d in dropped:
            print('%s: left out %s' % (os.path.basename(f), d))
    print('%d file(s) written from %s (%d copied in all)' % (n, a.ref, len(files) + 2))


if __name__ == '__main__':
    sys.exit(main())
