# -*- coding: utf-8 -*-
# MT2009_PLUS_YOHARA_SETS_V1 - checks the packs build_ysets_packs.py wrote (on the OUT of the whole Yohara chain):
#   * every staged file of ysets_manifest.json is in its pack, byte for byte (sha1), each new pack under 29 MB and in
#     Index;
#   * the eight race msm (gamedata) parse: ShapeDataCount = the groups, names ShapeData00..N-1 in order, indexes
#     unique, every group of the manifest there; its model, the model's LODs it was staged with and its skins exist;
#   * every texture each staged .gr2 names (gr2dec) resolves to a name of the client (the OUT and BASE packs, the base
#     client's pre-import listing; <race>_face.dds is the base client's pc/pc2 packs');
#   * the 369 items: an item_proto record (dbdata) equal to the server's row (yitem_record), an item_list line whose
#     icon and model exist, an itemdesc line; the "now_used" lines without "(Na razie bez zastosowania ...)";
#   * npclist 20475-20479 -> blacksmith (a race the base client has), mob_proto rows for them.
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/ysets/verify_ysets.py \
#     <OUT pack dir> [<BASE pack dir>]
import hashlib
import os
import re
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, HERE)
import m2pack  # noqa: E402
import packlib  # noqa: E402
import patch_ysets_client as pc  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith('--')]
OUT = args[0]
BASE = args[1] if len(args) > 1 else '/opt/metin2/cache/cY/azbase'
PRE_LST = '/opt/metin2/cache/tcm/gf28/ourpacks_pre.txt'
GR2DEC = '/opt/metin2/cache/tcm/gf28/gr2/gr2dec'
ZIP_LIMIT = 29 * 1024 * 1024
RE_TEX = re.compile(rb'[\x20-\x7e]{1,200}?\.(?:dds|tga|bmp|jpg|png)(?![A-Za-z0-9])', re.I)
fails = []


def fail(msg):
    fails.append(msg)


def norm(p):
    p = p.replace('\\', '/').strip().lower()
    while '//' in p:
        p = p.replace('//', '/')
    return p


def pack_of(name):
    d = OUT if os.path.exists(os.path.join(OUT, name + '.index')) else BASE
    f, v, ents = m2pack.read_index(os.path.join(d, name + '.index'))
    return ents, packlib.rd(os.path.join(d, name + '.data')), d


names = set()
for d in (OUT, BASE):
    for f in os.listdir(d):
        if f.endswith('.index'):
            for e in m2pack.read_index(os.path.join(d, f))[2]:
                names.add(norm(e['name']))
for l in open(PRE_LST, encoding='utf-8', errors='replace'):
    t = l.rstrip('\n').split(' ', 3)
    if len(t) == 4:
        names.add(norm(t[3]))


def exists(n):
    n = norm(n)
    return n in names or n.endswith('_face.dds')


man = pc.manifest()
ix = [l.strip() for l in open(os.path.join(OUT, 'Index'), 'rb').read().decode('latin-1').replace('\r', '').split('\n')]
staged = 0
for pack, rows in man['packs'].items():
    if pack not in ix:
        fail('Index: %s missing' % pack)
    ents, dat, d = pack_of(pack)
    if len(dat) >= ZIP_LIMIT:
        fail('%s: %d bytes, over 29 MB' % (pack, len(dat)))
    got = dict((e['name'], e) for e in ents)
    for r in rows:
        e = got.get(r['name'])
        if not e:
            fail('%s: %s not in the pack' % (pack, r['name']))
            continue
        b = m2pack.read_entry(dat, e)
        if hashlib.sha1(b).hexdigest() != r['sha1']:
            fail('%s: %s differs from the staged file' % (pack, r['name']))
            continue
        staged += 1
        if r['name'].endswith('.gr2'):
            tmp = '/tmp/ysets_verify.gr2'
            open(tmp, 'wb').write(b)
            p = subprocess.run([GR2DEC, tmp], capture_output=True)
            if p.returncode:
                fail('%s: gr2dec cannot read it' % r['name'])
                continue
            for t in set(RE_TEX.findall(p.stdout)):
                t = norm(t.decode('latin-1'))
                if 'ymir work/' in t:
                    t = 'd:/ymir work/' + t.split('ymir work/', 1)[1]
                else:
                    t = r['name'].rsplit('/', 1)[0] + '/' + t.rsplit('/', 1)[-1]
                if not exists(t):
                    fail('%s names %s - in no pack' % (r['name'], t))

gd_ents, gd_dat, _ = pack_of('gamedata')
db_ents, db_dat, _ = pack_of('dbdata')
gd = dict((e['name'], m2pack.read_entry(gd_dat, e)) for e in gd_ents)
db = dict((e['name'], m2pack.read_entry(db_dat, e)) for e in db_ents)

groups_ok = 0
for race, want in man['msm'].items():
    text = gd['gamedata/%s.msm' % race].decode('cp1250')
    m = re.search(r'Group ShapeData\s*\{', text)
    blk = text[m.end():]
    cnt = int(re.search(r'ShapeDataCount\s+(\d+)', blk).group(1))
    gs = re.findall(r'Group ShapeData(\d+)\s*\{(.*?)\}', blk, re.S)
    if [int(n) for n, _ in gs] != list(range(len(gs))) or len(gs) != cnt:
        fail('%s.msm: ShapeDataCount %d, groups %d (names in order: %s)' % (race, cnt, len(gs),
                                                                           [int(n) for n, _ in gs] == list(range(len(gs)))))
    idx = {}
    for n, body in gs:
        kv = {}
        for line in body.splitlines():
            t = line.split(None, 1)
            if len(t) == 2:
                kv[t[0]] = t[1].strip().strip('"')
        i = int(kv.get('ShapeIndex', -1))
        if i in idx:
            fail('%s.msm: ShapeIndex %d twice' % (race, i))
        idx[i] = kv
    for g in want:
        kv = idx.get(g['index'])
        if not kv:
            fail('%s.msm: ShapeIndex %d missing' % (race, g['index']))
            continue
        path = norm(kv.get('SpecialPath', ''))
        for k in ('Model', 'SourceSkin', 'TargetSkin'):
            if not exists(path + norm(kv[k])):
                fail('%s.msm %d: %s %s not in any pack' % (race, g['index'], k, path + kv[k]))
        groups_ok += 1

d = pc.items_json()
import patch_yohara_client as py  # noqa: E402
b = db['gamedata/item_proto']
ver, stride, cnt, size = struct.unpack_from('<IIII', b, 4)
raw = m2pack.mcoz_decode(b[20:], pc.base.ITEM_KEY)
R = pc.base.RECORD
recs = dict((struct.unpack_from('<I', raw, i * R)[0], raw[i * R:(i + 1) * R]) for i in range(cnt))
il = {}
for l in gd['gamedata/item_list.txt'].decode('cp1250').replace('\r\n', '\n').split('\n'):
    p = l.split('\t')
    if p and p[0].strip().isdigit():
        il[int(p[0])] = p
desc = {}
for l in db['locale/pl/itemdesc.txt'].decode('cp1250').replace('\r\n', '\n').split('\n'):
    p = l.split('\t')
    if p and p[0].strip().isdigit():
        desc[int(p[0])] = l
items_ok = 0
for w in d['items']:
    v = w['vnum']
    r = recs.get(v)
    if r is None or r[:180] != py.yitem_record(r, w)[:180] or r != py.yitem_record(r, w):
        fail('item_proto %d: missing or not the server row' % v)
        continue
    p = il.get(v)
    if not p or not exists(p[2]) or (len(p) > 3 and p[3].strip() and not exists(p[3])):
        fail('item_list %d: %r (icon/model missing)' % (v, p))
        continue
    if w['type'] == 1 and (len(p) < 4 or 'ysets_' not in p[3]):
        fail('item_list %d: a weapon without its model' % v)
        continue
    if v not in desc or desc[v].split('\t')[1] != w['locale_name']:
        fail('itemdesc %d: missing or another name' % v)
        continue
    items_ok += 1
for v in d['now_used']:
    if v in desc and pc.SUFFIX in desc[v]:
        fail('itemdesc %d still says it has no use' % v)
npc = {}
for l in gd['gamedata/npclist.txt'].decode('cp1250').replace('\r\n', '\n').split('\n'):
    p = l.split()
    if p:
        npc[p[0]] = p[1:]
mb = gd['gamedata/mob_proto']
mcnt = struct.unpack_from('<I', mb, 4)[0]
mraw = m2pack.mcoz_decode(mb[12:], pc.sd.MOB_KEY)
mobs = set(struct.unpack_from('<I', mraw, i * 256)[0] for i in range(mcnt))
for v in pc.MOBS:
    if npc.get(str(v)) != ['blacksmith']:
        fail('npclist %d: %r' % (v, npc.get(str(v))))
    if v not in mobs:
        fail('mob_proto %d missing' % v)
if not exists('d:/ymir work/npc/blacksmith/blacksmith.msm') and not any(n.startswith('d:/ymir work/npc/blacksmith/')
                                                                        for n in names):
    print('note: the blacksmith race (npc/blacksmith) is not in the listings - it is the base client\'s (20016)')

print('staged files %d/%d, msm groups %d, items %d/%d, failures %d' % (
    staged, sum(len(r) for r in man['packs'].values()), groups_ok, items_ok, len(d['items']), len(fails)))
for f in fails[:60]:
    print('FAIL', f)
sys.exit(1 if fails else 0)
