# -*- coding: utf-8 -*-
# MT2009_PLUS_HELM100_V1 (client data) - the level-100 helmets, their materials and Straznik Smokow Jaharr in the
# client's data, the method of ../ygloves/patch_ygloves_client.py and ../yiluzja/patch_yiluzja_client.py:
#
#   gamedata/item_list.txt, gamedata/item_proto (dbdata), locale/pl/itemdesc.txt (dbdata)
#       the 84 items of tools/yhelm100/yhelm100_items.json (= the server's yohara_helm100.sql, tools/yhelm100/
#       gen_yhelm100.py): the helmets 12690-12769 (ITEM_ARMOR / ARMOR_HEAD) - a full record each over Helm Mistrza
#       Wojny+0 12280 (a helmet record) - and the materials 30620/30621/30622/30630 over Czerwona Smocza Stal 30512
#       (a material record) - ../yohara/patch_yohara_client.py yitem_record; their item_list lines (GF icons:
#       client-2.0.30/root/icon/item; 30622.tga is in the icon pack) and itemdesc lines;
#   gamedata/mob_proto      Jaharr 20421 (the json's mob row = the SQL's) on the record of 9012 (an NPC) -
#                           ../shipdefense/patch_shipdefense_client.py mob_record; APPEND ONLY: a 20421 already there with
#                           other content is a collision and stops the run;
#   gamedata/npclist.txt    20421 old_magic_M2 and its alias row "0 old_magic_M2 old_magic_M" - our npclist has both
#                           (from the base client); appended only when missing, a different row stops the run.
# Helmets are not drawn on the character in this client (only the hair part: InstanceBase / RaceData have no helmet
# part), so no helmet model goes with them. Jaharr's model (d:/ymir work/npc/old_magic_m) is build_yhelm100_packs.py's.
# Idempotent: a second run changes nothing. By hand, on plain copies, in the m2pack-lzo image (MCOZ):
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/yhelm100/patch_yhelm100_client.py <file> ... [--check]   (by its name)
import io
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, os.path.join(HERE, '..', 'shipdefense'))
sys.path.insert(0, os.path.join(HERE, '..', 'yohara'))
sys.path.insert(0, os.path.join(HERE, '..', 'monstercard'))
import patch_shipdefense_client as sd  # noqa: E402
import patch_monstercard_client as base  # noqa: E402
import patch_yohara_client as py  # noqa: E402

REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
ITEMS_JSON = os.path.join(REPO, 'tools', 'yhelm100', 'yhelm100_items.json')
ITEMS = 84
TEMPLATE = {2: 12280, 5: 30512}     # by type: a helmet (Helm Mistrza Wojny+0), a material (Czerwona Smocza Stal)
NPC_TEMPLATE = 9012
JAHARR = 20421
NPCLIST = ['0\told_magic_M2\told_magic_M', '20421\told_magic_M2']
Collision = sd.Collision


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
    want = {}
    for w in items_json()['items']:
        t = recs[TEMPLATE[w['type']]]
        assert t[74] == w['type'], (w['vnum'], t[74])      # the template is of the item's own type
        want[w['vnum']] = py.yitem_record(t, w)
    return want


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


def mob_recs(b):
    import m2pack
    magic, cnt, esize = struct.unpack_from('<4sII', b, 0)
    assert magic == b'MMPT', magic
    raw = m2pack.mcoz_decode(b[12:12 + esize], sd.MOB_KEY)
    assert len(raw) == cnt * sd.MOB_RECORD, (len(raw), cnt)
    R = sd.MOB_RECORD
    return dict((struct.unpack_from('<I', raw, i * R)[0], raw[i * R:(i + 1) * R]) for i in range(cnt))


def want_mobs(recs):
    return dict((w['vnum'], sd.mob_record(w, recs[NPC_TEMPLATE])) for w in items_json()['mobs'])


def mob_proto(b):
    import m2pack
    recs = mob_recs(b)
    want = want_mobs(recs)
    clash = [v for v, r in sorted(want.items()) if v in recs and recs[v] != r]
    if clash:
        raise Collision('mob_proto: %d vnum(s) already in the client with other content: %s' % (len(clash), clash))
    new = dict((v, r) for v, r in want.items() if v not in recs)
    if not new:
        return b, 0
    recs.update(new)
    out = b''.join(recs[v] for v in sorted(recs))
    blob = m2pack.mcoz_encode(out, sd.MOB_KEY)
    return struct.pack('<4sII', b'MMPT', len(recs), len(blob)) + blob, len(new)


def npclist_key(line):
    t = line.split()
    if not t:
        return ''
    return '0 ' + t[1].lower() if t[0] == '0' and len(t) > 1 else t[0]


def npclist(b):
    text = b.decode('cp1250')
    nl = '\r\n' if '\r\n' in text else '\n'
    lines = text.split(nl)
    tail = bool(lines) and lines[-1] == ''
    if tail:
        lines.pop()
    have = dict((npclist_key(l), l) for l in lines if l.strip() and not l.lstrip().startswith(('#', '//')))
    new = []
    for row in NPCLIST:
        k = npclist_key(row)
        if k in have:
            if [x.lower() for x in have[k].split()] != [x.lower() for x in row.split()]:
                raise Collision('npclist: %r already there as %r' % (k, have[k]))
            continue
        new.append(row)
    if not new:
        return b, 0
    return (nl.join(lines + new + ([''] if tail else []))).encode('cp1250'), len(new)


# in-pack name -> function
JOBS = {'gamedata/item_list.txt': item_list, 'gamedata/item_proto': item_proto, 'locale/pl/itemdesc.txt': itemdesc,
        'gamedata/mob_proto': mob_proto, 'gamedata/npclist.txt': npclist}
BY_FILE = dict((os.path.basename(k), f) for k, f in JOBS.items())


def main():
    args = [a for a in sys.argv[1:] if a != '--check']
    check = '--check' in sys.argv
    if not args:
        raise SystemExit('usage: patch_yhelm100_client.py <item_list.txt|item_proto|itemdesc.txt|mob_proto|npclist.txt>'
                         ' ... [--check]')
    for path in args:
        fn = BY_FILE[os.path.basename(path)]
        b = open(path, 'rb').read()
        nb, n = fn(b)
        if n and not check:
            open(path, 'wb').write(nb)
        print('%s: %d new/changed%s' % (os.path.basename(path), n, ' (check only)' if check else ''))


if __name__ == '__main__':
    main()
