# -*- coding: utf-8 -*-
# MT2009_PLUS_HALLOWEEN_V1 - the Halloween event in the client's data (Autor: Owsap, event_halloween_hair,
# v6.2.6). The client already has the event's records - item_proto 30321 Upiorna Dynia, 30322 Czarodziejska
# Rozdzka, 30323 Karta Maski Dyni, 50215 Upiorna Skrzynia and the eight Pumpkin Masks 74020 ... 75620, their
# item_list.txt lines and icons, the official itemdesc.txt lines, mob_proto and npclist 33008 Jack Pumpkin
# (checked on client 2.0.69) - so this only
#   item_list.txt  adds a line per vnum of halloween_client.json "items_present" where the key is missing
#                  (none on 2.0.69; a safety net for an older data set);
#   itemdesc.txt   writes the twelve descriptions of halloween_client.json over the official ones (the same
#                  Polish texts, Owsap's, but the pumpkin and the wand say where they drop in this world, the
#                  card where it is traded, the chest that it may hold the card, a mask that it has one bonus),
#                  and appends any the file lacks.
# The NPC's model is the pack "halloween" (build_halloween_pack.py next to this file).
# From client 2.0.52 itemdesc.txt lives in the "dbdata" pack (locale/pl/itemdesc.txt), item_list.txt in
# "gamedata" (gamedata/item_list.txt). Plain files, no MCOZ - runs anywhere python 3 is:
#   python3 <repo>/client-patches/client-2.0.30/tools/halloween/patch_halloween_client.py \
#     <item_list.txt> <itemdesc.txt> [<out dir>]
# Either file may be "-" to leave it alone. Without an out dir the files are rewritten in place.
# Idempotent: a second run changes nothing.
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
with io.open(os.path.join(HERE, 'halloween_client.json'), encoding='utf-8') as _f:
    DATA = json.load(_f)


def add_missing(b, rows):
    """append the rows ({key: line}) whose key the file lacks; existing lines stay as they are"""
    text = b.decode('cp1250')
    nl = '\r\n' if '\r\n' in text else '\n'
    lines = text.split(nl)
    tail = bool(lines) and lines[-1] == ''
    if tail:
        lines.pop()
    have = set(l.split('\t', 1)[0].strip() for l in lines)
    new = [rows[k] for k in sorted(rows, key=int) if k not in have]
    if not new:
        return b, 0
    return nl.join(lines + new + ([''] if tail else [])).encode('cp1250'), len(new)


def item_list(b):
    rows = dict((k, '%s\tETC\t%s' % (k, icon)) for k, icon in DATA['items_present'].items())
    return add_missing(b, rows)


def set_rows(b, rows):
    """each row ({key: line}) replaces the file's line of that key, or is appended; the rest stays"""
    text = b.decode('cp1250')
    nl = '\r\n' if '\r\n' in text else '\n'
    lines = text.split(nl)
    tail = bool(lines) and lines[-1] == ''
    if tail:
        lines.pop()
    changed = 0
    seen = set()
    for i, l in enumerate(lines):
        k = l.split('\t', 1)[0].strip()
        if k in rows and k not in seen:
            seen.add(k)
            if l != rows[k]:
                lines[i] = rows[k]
                changed += 1
    new = [rows[k] for k in sorted(rows, key=int) if k not in seen]
    changed += len(new)
    if not changed:
        return b, 0
    return nl.join(lines + new + ([''] if tail else [])).encode('cp1250'), changed


def itemdesc(b):
    return set_rows(b, DATA['itemdesc'])


def main():
    if len(sys.argv) not in (3, 4):
        raise SystemExit('usage: patch_halloween_client.py <item_list.txt> <itemdesc.txt> [<out dir>]')
    out_dir = sys.argv[3] if len(sys.argv) == 4 else None
    for path, fn in ((sys.argv[1], item_list), (sys.argv[2], itemdesc)):
        if path == '-':
            continue
        with open(path, 'rb') as f:
            data, changed = fn(f.read())
        target = os.path.join(out_dir, os.path.basename(path)) if out_dir else path
        if out_dir or changed:
            if out_dir and not os.path.isdir(out_dir):
                os.makedirs(out_dir)
            with open(target, 'wb') as f:
                f.write(data)
        print('%s: %d change(s)%s' % (os.path.basename(path), changed, '' if target == path else ' -> ' + target))


if __name__ == '__main__':
    main()
