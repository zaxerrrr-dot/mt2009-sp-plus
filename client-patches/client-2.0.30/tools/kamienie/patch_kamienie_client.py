# -*- coding: utf-8 -*-
# MT2009_PLUS_ELEMENT_STONES_V1 (client data) - Kamien Ochrony Zywiolow (39120) and Kamien Mocy Zywiolow (39119), the
# method of ../yeliksiry/patch_yeliksiry_client.py:
#
#   gamedata/item_list.txt, gamedata/item_proto (dbdata), locale/pl/itemdesc.txt (dbdata)
#       the two items of tools/kamienie_zywiolow/kamienie_zywiolow.json (= the server's kamienie_zywiolow.sql,
#       tools/kamienie_zywiolow/gen_kamienie_zywiolow.py): a full record each over Lizak Potegi 71136 (ITEM_UNIQUE, the
#       unique slot; ../yohara/patch_yohara_client.py yitem_record), its item_list line (the GF icon in
#       client-2.0.30/root/icon/item) and its itemdesc line;
#   gamedata/item_extra_apply.txt (dbdata)
#       the six bonus lines of each (MT2009_PLUS_ITEM_EXTRA_APPLY_V1 - uitooltip.py shows them under the item; the
#       record has none, item_proto's three slots are empty). A pack without the file gets none (an older client).
# A vnum the client has with another record is replaced. Idempotent: a second run changes nothing.
# build_kamienie_packs.py calls these functions on the packs; by hand, on plain copies, in the m2pack-lzo image:
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/kamienie/patch_kamienie_client.py <file> ... [--check]   (by its name)
import io
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, os.path.join(HERE, '..', 'yohara'))
sys.path.insert(0, os.path.join(HERE, '..', 'monstercard'))
import patch_monstercard_client as base  # noqa: E402
import patch_yohara_client as py  # noqa: E402

REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
ITEMS_JSON = os.path.join(REPO, 'tools', 'kamienie_zywiolow', 'kamienie_zywiolow.json')
ITEMS = 2
TEMPLATE = 71136    # Lizak Potegi: ITEM_UNIQUE, WEAR_UNIQUE, LIMIT_REAL_TIME


def items_json():
    with io.open(ITEMS_JSON, encoding='utf-8') as f:
        d = json.load(f)
    assert len(d['items']) == ITEMS, len(d['items'])
    return d


def records(b):
    import m2pack
    assert b[:4] == b'MIPX'
    ver, stride, cnt, size = struct.unpack_from('<IIII', b, 4)
    assert stride == base.RECORD, stride
    raw = m2pack.mcoz_decode(b[20:], base.ITEM_KEY)
    return ver, dict((struct.unpack_from('<I', raw, i * base.RECORD)[0], raw[i * base.RECORD:(i + 1) * base.RECORD])
                     for i in range(cnt))


def want_records(recs):
    d = items_json()
    return dict((w['vnum'], py.yitem_record(recs[TEMPLATE], w)) for w in d['items'])


def item_proto(b):
    import m2pack
    ver, recs = records(b)
    changed = 0
    for v, r in want_records(recs).items():
        if recs.get(v) != r:
            recs[v] = r
            changed += 1
    if not changed:
        return b, 0
    out = b''.join(recs[v] for v in sorted(recs))
    blob = m2pack.mcoz_encode(out, base.ITEM_KEY)
    return b'MIPX' + struct.pack('<IIII', ver, base.RECORD, len(recs), len(blob)) + blob, changed


def item_list(b):
    d = items_json()
    return base.set_rows(b, [d['item_list'][k] for k in sorted(d['item_list'], key=int)])


def itemdesc(b):
    d = items_json()
    return base.set_rows(b, [d['itemdesc'][k] for k in sorted(d['itemdesc'], key=int)])


def extra_lines():
    d = items_json()
    out = []
    for k in sorted(d['extra_apply'], key=int):
        out += ['%s\t%d\t%d' % (k, p, v) for p, v in d['extra_apply'][k]]
    return out


def item_extra_apply(b):
    """vnum<TAB>point<TAB>value, a line a bonus: the stones' lines replaced, everything else kept (CRLF, ASCII)."""
    d = items_json()
    text = b.decode('ascii')
    nl = '\r\n' if '\r\n' in text or not text else '\n'
    lines = text.split(nl)
    if lines and lines[-1] == '':
        lines.pop()
    kept = [l for l in lines if l.split('\t')[0] not in d['extra_apply']]
    new = kept + extra_lines()
    if new == lines:
        return b, 0
    return (nl.join(new) + nl).encode('ascii'), len(extra_lines())


# in-pack name -> function
JOBS = {'gamedata/item_list.txt': item_list, 'gamedata/item_proto': item_proto, 'locale/pl/itemdesc.txt': itemdesc,
        'gamedata/item_extra_apply.txt': item_extra_apply}
BY_FILE = dict((os.path.basename(k), f) for k, f in JOBS.items())


def main():
    args = [a for a in sys.argv[1:] if a != '--check']
    check = '--check' in sys.argv
    if not args:
        raise SystemExit('usage: patch_kamienie_client.py <item_list.txt|item_proto|itemdesc.txt|item_extra_apply.txt> ... '
                         '[--check]')
    for path in args:
        fn = BY_FILE[os.path.basename(path)]
        b = open(path, 'rb').read()
        nb, n = fn(b)
        if n and not check:
            open(path, 'wb').write(nb)
        print('%s: %d new/changed%s' % (os.path.basename(path), n, ' (check only)' if check else ''))


if __name__ == '__main__':
    main()
