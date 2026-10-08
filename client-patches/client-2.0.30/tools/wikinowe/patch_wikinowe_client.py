# -*- coding: utf-8 -*-
# MT2009_PLUS_NS_WIKI_ITEMS_V1 - the official PL wiki's item families and upgrade materials our world did not have,
# in the client's data (Autor: Digi Rasta, nowy-system 0.33.0, his klient.py patch_nowe / rekord_klienta /
# dopisz_brakujace). The rows come from tools/wikinowe/wiki_nowe.json - the same data the server's wiki_nowe.sql is
# generated from (tools/wikinowe/gen_wikinowe_sql.py), so the tooltips always match the server:
#   item_proto     116 records - Cyjanitowy Miecz 500 / Sztylet 1500 / Luk 2500 / Ostrze 3500 / Dzwon 5500 /
#                  Wachlarz 7500, Bransoleta 14570 / Naszyjnik 16570 z Turmalinu, Ogniste Buty 15440, Buty Oceanu 15450
#                  (+0..+9) and 16 materials (30602-30629, 50639, 95601-95603); each on the record of his template
#                  item ("szablon_klienta": an item of the same type and class), every server column written over it;
#   item_list.txt  a line per new vnum (icon, and the weapon's model) - only where the key is missing;
#   itemdesc.txt   the 9 materials' descriptions - only where the key is missing.
# A record of one of our vnums that holds another item (another name: the mod made the vnum its own) is left alone,
# as the server's INSERT IGNORE leaves the mod's row. Idempotent: a second run changes nothing.
#
# The icons and the weapons' models are the pack "wiki_nowe" (build_wikinowe_pack.py next to this file).
# From client 2.0.52 item_proto and itemdesc.txt live in the "dbdata" pack (gamedata/item_proto,
# locale/pl/itemdesc.txt), item_list.txt in "gamedata" (gamedata/item_list.txt). Run on plain copies, in the
# m2pack-lzo image (MCOZ):
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/wikinowe/patch_wikinowe_client.py \
#     <item_proto> <item_list.txt> <itemdesc.txt> [<out dir>]
# Any file may be "-" to leave it alone. Without an out dir the files are rewritten in place.
import io
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/cli')
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
DATA_PATH = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..', 'tools', 'wikinowe', 'wiki_nowe.json'))
with io.open(DATA_PATH, encoding='utf-8') as _f:
    DATA = json.load(_f)
ITEM_KEY = (173217, 72619434, 408587239, 27973291)
ITEM_RECORD = 184


def fixed(text, size):
    b = text.encode('cp1250')
    assert len(b) < size, text
    return b + b'\0' * (size - len(b))


def item_record(w, tmpl):
    r = bytearray(tmpl)
    struct.pack_into('<II', r, 0, w['vnum'], 0)
    r[8:41] = fixed(w['name'], 33)
    r[41:74] = fixed(w['locale_name'], 33)
    struct.pack_into('<BBBB', r, 74, w['type'], w['subtype'], w['weight'], w['size'])
    struct.pack_into('<IIII', r, 78, w['stack'], w['antiflag'], w['flag'], w['wearflag'])
    struct.pack_into('<qq', r, 98, w['gold'], w['shop_buy_price'])
    struct.pack_into('<BiBi', r, 114, w['limittype0'], w['limitvalue0'], w['limittype1'], w['limitvalue1'])
    struct.pack_into('<BiBiBi', r, 124, w['applytype0'], w['applyvalue0'], w['applytype1'], w['applyvalue1'],
                     w['applytype2'], w['applyvalue2'])
    struct.pack_into('<6i', r, 139, *(w['value%d' % j] for j in range(6)))
    struct.pack_into('<IHBBB', r, 175, w['refined_vnum'], w['refine_set'], w['magic_pct'], w['specular'], w['socket_pct'])
    return bytes(r)


def item_proto(b):
    import m2pack
    assert b[:4] == b'MIPX'
    ver, stride, cnt, size = struct.unpack_from('<IIII', b, 4)
    assert stride == ITEM_RECORD, stride
    raw = m2pack.mcoz_decode(b[20:], ITEM_KEY)
    recs = dict((struct.unpack_from('<I', raw, i * ITEM_RECORD)[0], raw[i * ITEM_RECORD:(i + 1) * ITEM_RECORD])
                for i in range(cnt))
    changed = kept = 0
    for vs in sorted(DATA['items'], key=int):
        w = DATA['items'][vs]
        vnum = int(vs)
        tmpl = recs.get(DATA['szablon_klienta'][vs])
        if tmpl is None:
            raise SystemExit('item_proto: no template record %d for %d' % (DATA['szablon_klienta'][vs], vnum))
        if vnum in recs and recs[vnum][41:74].split(b'\0')[0] != w['locale_name'].encode('cp1250'):
            kept += 1          # the mod's own item under this vnum
            continue
        r = item_record(w, tmpl)
        if recs.get(vnum) != r:
            recs[vnum] = r
            changed += 1
    if kept:
        print('item_proto: %d vnum(s) hold another item - left alone' % kept)
    if not changed:
        return b, 0
    out = b''.join(recs[v] for v in sorted(recs))
    blob = m2pack.mcoz_encode(out, ITEM_KEY)
    return b'MIPX' + struct.pack('<IIII', ver, stride, len(recs), len(blob)) + blob, changed


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
    return add_missing(b, DATA['item_list'])


def itemdesc(b):
    return add_missing(b, DATA['itemdesc'])


def main():
    if len(sys.argv) not in (4, 5):
        raise SystemExit('usage: patch_wikinowe_client.py <item_proto> <item_list.txt> <itemdesc.txt> [<out dir>]')
    out_dir = sys.argv[4] if len(sys.argv) == 5 else None
    for path, fn in ((sys.argv[1], item_proto), (sys.argv[2], item_list), (sys.argv[3], itemdesc)):
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
