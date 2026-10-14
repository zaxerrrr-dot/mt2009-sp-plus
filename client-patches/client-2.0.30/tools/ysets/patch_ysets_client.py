# -*- coding: utf-8 -*-
# MT2009_PLUS_YOHARA_SETS_V1 (client data) - the Yohara gear and the set blacksmiths in the client's data:
#
#   gamedata/<race>.msm       (8 player races) a ShapeData group per armour family of the race's class - ShapeIndex
#                             = the family's base vnum (21210/21230/21250/21270 dragon, 21310/21330/21350/21370
#                             serpent = the items' value3 in the server's yohara_sets.sql), the GF body staged by
#                             stage_ysets.py (ysets_manifest.json "msm");
#   gamedata/item_list.txt    the 369 items' lines of tools/ysets/yohara_sets.json - a weapon's model is its staged
#                             ysets_0XXXX.gr2 (ysets_manifest.json "weapon_models");
#   gamedata/npclist.txt      20475-20479 -> blacksmith (the base list has them already: nothing then);
#   gamedata/mob_proto        the five set blacksmiths (rows of yohara_sets.sql on the record of 9012, an NPC);
#   gamedata/item_proto       (dbdata) a full record for each of the 369 items (../yohara/patch_yohara_client.py
#                             yitem_record writes every column the server has);
#   locale/pl/itemdesc.txt    (dbdata) their lines, and the materials of the earlier Yohara batches that have a use
#                             now ("now_used") lose "(Na razie bez zastosowania ...)".
# APPEND ONLY for msm/npclist/mob_proto: an index/vnum there with other content is a collision and stops the run.
# Idempotent. build_ysets_packs.py calls these on the packs; by hand, on plain copies, in the m2pack-lzo image:
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/ysets/patch_ysets_client.py <file> ...   (by its name)
import io
import json
import os
import re
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
SQL = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot', 'yohara_sets.sql')
ITEMS_JSON = os.path.join(REPO, 'tools', 'ysets', 'yohara_sets.json')
MANIFEST = os.path.join(HERE, 'ysets_manifest.json')
ITEMS = 369
MOBS = (20475, 20476, 20477, 20478, 20479)
RACES = ('warrior_m', 'warrior_w', 'assassin_m', 'assassin_w', 'sura_m', 'sura_w', 'shaman_m', 'shaman_w')
SUFFIX = u' (Na razie bez zastosowania - przyjdzie z kolejną aktualizacją Yohary.)'
NPC_TEMPLATE = 9012
Collision = sd.Collision


def items_json():
    with io.open(ITEMS_JSON, encoding='utf-8') as f:
        d = json.load(f)
    assert len(d['items']) == ITEMS, len(d['items'])
    return d


def manifest():
    with io.open(MANIFEST, encoding='utf-8') as f:
        return json.load(f)


def sql_mobs(path=SQL):
    t = open(path, encoding='utf-8').read()
    # the Polish names are hex literals (_cp1250 X'...'): as plain strings for the row reader
    t = re.sub(r"_cp1250 X'([0-9A-F]*)'",
               lambda m: "'%s'" % bytes.fromhex(m.group(1)).decode('cp1250').replace("'", "\\'"), t)
    m = re.search(r'INSERT IGNORE INTO world\.mob_proto \(([^)]*)\) VALUES', t)
    cols = [c.strip().strip('`') for c in m.group(1).split(',')]
    mobs = []
    for r in sd._values(t[m.end():]):
        assert len(r) == len(cols), r[:3]
        mobs.append(dict(zip(cols, r)))
    assert sorted(w['vnum'] for w in mobs) == list(MOBS), [w['vnum'] for w in mobs]
    return mobs


def mob_proto(b):
    import m2pack
    magic, cnt, esize = struct.unpack_from('<4sII', b, 0)
    assert magic == b'MMPT', magic
    raw = m2pack.mcoz_decode(b[12:12 + esize], sd.MOB_KEY)
    R = sd.MOB_RECORD
    assert len(raw) == cnt * R, (len(raw), cnt)
    recs = dict((struct.unpack_from('<I', raw, i * R)[0], raw[i * R:(i + 1) * R]) for i in range(cnt))
    want = dict((w['vnum'], sd.mob_record(w, recs[NPC_TEMPLATE])) for w in sql_mobs())
    # a base client row of the same vnum is GF's set blacksmith: an NPC of the blacksmith's look, ours replaces it
    clash = [v for v, r in sorted(want.items()) if v in recs and recs[v] != r and recs[v][54] != r[54]]
    if clash:
        raise Collision('mob_proto: vnum(s) already in the client as another kind: %s' % clash)
    new = dict((v, r) for v, r in want.items() if recs.get(v) != r)
    if not new:
        return b, 0
    recs.update(new)
    out = b''.join(recs[v] for v in sorted(recs))
    blob = m2pack.mcoz_encode(out, sd.MOB_KEY)
    return struct.pack('<4sII', b'MMPT', len(recs), len(blob)) + blob, len(new)


def npclist(b):
    text = b.decode('cp1250')
    nl = '\r\n' if '\r\n' in text else '\n'
    lines = text.split(nl)
    tail = bool(lines) and lines[-1] == ''
    if tail:
        lines.pop()
    have = {}
    for l in lines:
        p = l.split()
        if p and not l.lstrip().startswith(('#', '//')):
            have[p[0]] = p[1:]
    new = []
    for v in MOBS:
        if str(v) in have:
            if have[str(v)] != ['blacksmith']:
                raise Collision('npclist: %d already there as %r' % (v, have[str(v)]))
            continue
        new.append('%d\tblacksmith' % v)
    if not new:
        return b, 0
    return (nl.join(lines + new + ([''] if tail else []))).encode('cp1250'), len(new)


def msm_groups(b, groups):
    """Appends ShapeData groups [{index, SpecialPath, Model, SourceSkin, TargetSkin}] to the msm's ShapeData block
    (named on from its count - the loader reads ShapeData%02d 0..count-1). A group of the same index with the same
    content is left; with other content it is a collision."""
    text = b.decode('cp1250')
    lines = text.splitlines(True)
    nl = '\r\n' if lines and lines[0].endswith('\r\n') else '\n'
    start = next(i for i, l in enumerate(lines) if l.strip() == 'Group ShapeData')
    depth, end = 0, None
    for i in range(start + 1, len(lines)):
        s = lines[i].strip()
        if s == '{':
            depth += 1
        elif s == '}':
            depth -= 1
            if depth == 0:
                end = i
                break
    cnt_i = next(i for i in range(start, end) if lines[i].strip().startswith('ShapeDataCount'))
    cnt = int(lines[cnt_i].split()[1])
    block = ''.join(lines[start:end])
    have = {}
    for g in re.finditer(r'Group ShapeData\d+\s*\{(.*?)\}', block, re.S):
        kv = {}
        for line in g.group(1).splitlines():
            t = line.split(None, 1)
            if len(t) == 2:
                kv[t[0]] = t[1].strip().strip('"')
        if kv.get('ShapeIndex', '').isdigit():
            have[int(kv['ShapeIndex'])] = kv
    add, n = [], cnt
    for g in groups:
        if g['index'] in have:
            h = have[g['index']]
            if [h.get(k, '').lower() for k in ('SpecialPath', 'Model', 'SourceSkin', 'TargetSkin')] != \
                    [g[k].lower() for k in ('SpecialPath', 'Model', 'SourceSkin', 'TargetSkin')]:
                raise Collision('msm: ShapeIndex %d already there as %r' % (g['index'], h))
            continue
        body = [u'\tGroup ShapeData%02d' % n, u'\t{', u'\t\tShapeIndex\t\t\t%d' % g['index'],
                u'\t\tSpecialPath\t\t\t"%s"' % g['SpecialPath'], u'\t\tModel\t\t\t\t"%s"' % g['Model'],
                u'\t\tSourceSkin\t\t\t"%s"' % g['SourceSkin'], u'\t\tTargetSkin\t\t\t"%s"' % g['TargetSkin'], u'\t}']
        add.append(nl + nl.join(body) + nl)
        n += 1
    if not add:
        return b, 0
    lines[cnt_i] = lines[cnt_i].replace(str(cnt), str(n), 1)
    lines[end:end] = add
    return ''.join(lines).encode('cp1250'), len(add)


def msm_job(race):
    def job(b):
        return msm_groups(b, manifest()['msm'][race])
    return job


def item_list_rows():
    d, wm = items_json(), manifest()['weapon_models']
    rows = []
    for k in sorted(d['item_list'], key=int):
        p = d['item_list'][k].split('\t')
        if len(p) > 3:
            fam = next(f for f in wm if int(f) <= int(k) < int(f) + 16)
            p[3] = wm[fam]
        rows.append('\t'.join(p))
    return rows


def item_list(b):
    return base.set_rows(b, item_list_rows())


def item_proto(b):
    import m2pack
    assert b[:4] == b'MIPX'
    ver, stride, cnt, size = struct.unpack_from('<IIII', b, 4)
    assert stride == base.RECORD, stride
    raw = m2pack.mcoz_decode(b[20:], base.ITEM_KEY)
    recs = dict((struct.unpack_from('<I', raw, i * base.RECORD)[0], raw[i * base.RECORD:(i + 1) * base.RECORD])
                for i in range(cnt))
    changed = 0
    for w in items_json()['items']:
        r = py.yitem_record(recs[py.YITEM_TEMPLATE.get(w['type'], py.TEMPLATE)], w)
        if recs.get(w['vnum']) != r:
            recs[w['vnum']] = r
            changed += 1
    if not changed:
        return b, 0
    out = b''.join(recs[v] for v in sorted(recs))
    blob = m2pack.mcoz_encode(out, base.ITEM_KEY)
    return b'MIPX' + struct.pack('<IIII', ver, stride, len(recs), len(blob)) + blob, changed


def itemdesc_rows(b):
    d = items_json()
    rows = [d['itemdesc'][k] for k in sorted(d['itemdesc'], key=int)]
    have = {}
    for l in b.decode('cp1250').replace('\r\n', '\n').split('\n'):
        p = l.split('\t')
        if p and p[0].strip().isdigit():
            have[int(p[0])] = l
    for v in d['now_used']:
        l = have.get(v)
        if l and SUFFIX in l:
            rows.append(l.replace(SUFFIX, ''))
    return rows


def itemdesc(b):
    return base.set_rows(b, itemdesc_rows(b))


# in-pack name -> function
JOBS = dict([('gamedata/mob_proto', mob_proto), ('gamedata/npclist.txt', npclist),
             ('gamedata/item_list.txt', item_list), ('gamedata/item_proto', item_proto),
             ('locale/pl/itemdesc.txt', itemdesc)] +
            [('gamedata/%s.msm' % r, msm_job(r)) for r in RACES])
BY_FILE = dict((os.path.basename(k), f) for k, f in JOBS.items())


def main():
    args = [a for a in sys.argv[1:] if a != '--check']
    check = '--check' in sys.argv
    if not args:
        raise SystemExit('usage: patch_ysets_client.py <mob_proto|npclist.txt|item_list.txt|item_proto|itemdesc.txt|'
                         '<race>.msm> ... [--check]')
    for path in args:
        fn = BY_FILE[os.path.basename(path)]
        b = open(path, 'rb').read()
        nb, n = fn(b)
        if n and not check:
            open(path, 'wb').write(nb)
        print('%s: %d new/changed%s' % (os.path.basename(path), n, ' (check only)' if check else ''))


if __name__ == '__main__':
    main()
