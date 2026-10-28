# -*- coding: utf-8 -*-
# MT2009_PLUS_BALATHOR_V1 (Autor: dracaryS) - checks the packs build_balathor_packs.py wrote (on the OUT of the whole
# Yohara chain), against balathor_manifest.json, balathor_client.json and the server's balathor.sql:
#   * every new pack is in OUT and in Index, under the 29 MB limit, and holds exactly the staged files (sha1);
#   * property holds the staged properties; every object CRC of the map's sectors has a property in OUT/BASE (or the
#     client listing), and the folder has setting.txt (2x2 at 1152000 921600), mapproperty.txt and the msenv;
#   * gamedata: the atlasinfo row, an npclist row of each of the 20 vnums whose race model (msm) is in OUT/BASE or the
#     client listing, a mob_proto record of every vnum the SQL has, the item_list lines of 30395/83075/83076 (icon in the repo's
#     root/icon/item or our packs); dbdata: their item_proto records equal to the SQL's, itemdesc lines;
#   * locale: the locale_game strings and the six cinema scripts; the boss window's pictures and the named effects are
#     somewhere (OUT/BASE, the full install's base pack etc, or the client listing).
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/balathor/verify_balathor_packs.py \
#     <OUT pack dir> [<BASE pack dir>]
import hashlib
import io
import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, HERE)
import m2pack  # noqa: E402
import packlib  # noqa: E402
import patch_balathor_client as pc  # noqa: E402
import build_balathor_packs as bp  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith('--')]
OUT = args[0]
BASE = args[1] if len(args) > 1 else '/opt/metin2/cache/cY/azbase'
WORK = '/opt/metin2/cache/yohara/cape301-work'
PRE_LST = '/opt/metin2/cache/tcm/gf28/ourpacks_pre.txt'
ETC_INDEX = '/opt/metin2/cache/exebuild/smoke/client/pack/etc.index'
ROOT_ICONS = os.path.normpath(os.path.join(HERE, '..', '..', 'root', 'icon', 'item'))
ZIP_LIMIT = 29 * 1024 * 1024
MAN = json.load(open(os.path.join(HERE, 'balathor_manifest.json'), encoding='utf-8'))
D = pc.data()
fails, notes = [], []


def norm(p):
    p = p.replace('\\', '/').strip().lower()
    while '//' in p:
        p = p.replace('//', '/')
    return p


CONTENT, PACK_OF = {}, {}
for d in (BASE, OUT):          # OUT last: its packs win
    for f in sorted(os.listdir(d)):
        if not f.endswith('.index'):
            continue
        p = f[:-6]
        if d == BASE and os.path.exists(os.path.join(OUT, f)):
            continue
        ents = m2pack.read_index(os.path.join(d, f))[2]
        dat = packlib.rd(os.path.join(d, p + '.data'))
        if p in MAN['new_packs'] and len(dat) >= ZIP_LIMIT:
            fails.append('pack %s: data %d bytes, over the 29 MB limit' % (p, len(dat)))
        for e in ents:
            CONTENT[e['name']] = (p, dat, e)
NAMES = set(CONTENT)
for l in open(os.path.join(WORK, 'c58.lst'), encoding='utf-8', errors='replace'):
    t = l.rstrip('\n').split(' ', 1)
    if len(t) == 2:
        NAMES.add(norm(t[1]))
for l in open(PRE_LST, encoding='utf-8', errors='replace'):
    t = l.rstrip('\n').split(' ', 3)
    if len(t) == 4:
        NAMES.add(norm(t[3]))
if os.path.exists(ETC_INDEX):
    NAMES |= set(e['name'] for e in m2pack.read_index(ETC_INDEX)[2])
else:
    notes.append('no full-install etc pack at %s - the window pictures are not checked against it' % ETC_INDEX)


def read(name):
    if name not in CONTENT:
        return None
    p, dat, e = CONTENT[name]
    return m2pack.read_entry(dat, e)


# 1) the new packs and property
ix = [l.strip() for l in open(os.path.join(OUT, 'Index'), 'rb').read().decode('latin1').replace('\r', '').split('\n')]
for p in MAN['new_packs']:
    if p not in ix:
        fails.append('pack %s is not in Index' % p)
    if not os.path.exists(os.path.join(OUT, p + '.index')):
        fails.append('pack %s is not in OUT' % p)
for p, ents in MAN['packs'].items():
    for e in ents:
        b = read(e['name'])
        if b is None:
            fails.append('staged %s (%s) is in no pack' % (e['name'], p))
        elif hashlib.sha1(b).hexdigest() != e['sha1'] and p != 'property':
            fails.append('staged %s (%s): other bytes in the pack' % (e['name'], p))

# 2) the map
M = D['map']
mp = 'maps/%s/' % M['folder']
st = (read(mp + 'setting.txt') or b'').decode('latin1')
if not (re.search(r'MapSize\s+%d\s+%d' % tuple(M['size']), st) and re.search(r'BasePosition\s+%d\s+%d' % tuple(M['base']), st)):
    fails.append('setting.txt of %s missing or not 2x2 at the base' % M['folder'])
for k in ('mapproperty.txt',):
    if read(mp + k) is None:
        fails.append(mp + k + ' missing')
env = re.search(r'Environment\s+(\S+)', st)
if env and 'd:/ymir work/environment/' + norm(env.group(1)) not in NAMES:
    fails.append('msenv %s missing' % env.group(1))
props = {}
for k in NAMES:
    if k.startswith('property/') and k in CONTENT:
        l = read(k).replace(b'\r', b'').split(b'\n')
        if l and l[0].strip() == b'YPRT' and len(l) > 1:
            try:
                props[int(l[1].strip())] = k
            except ValueError:
                pass
nsec = 0
for k in sorted(CONTENT):
    if k.startswith(mp) and k.endswith('/areadata.txt'):
        nsec += 1
        t = read(k).decode('latin1').replace('\r', '')
        for body in re.findall(r'Start Object\d+\n(.*?)End Object\n', t, re.S):
            crc = int(body.split('\n')[1].strip().split('#')[0])
            if crc not in props:
                notes.append('%s: object CRC %d has no property in OUT/BASE (may be in the client\'s own property)'
                             % (k, crc))
if nsec != M['size'][0] * M['size'][1]:
    fails.append('%d sectors of %s, not %d' % (nsec, M['folder'], M['size'][0] * M['size'][1]))

# 3) gamedata
at = (read('gamedata/atlasinfo.txt') or b'').decode('cp1250').replace('\r', '').split('\n')
for row in D['atlasinfo']:
    if row.split() not in [l.split() for l in at]:
        fails.append('atlasinfo: row %r missing' % row)
npc, alias = {}, {}
for l in (read('gamedata/npclist.txt') or b'').decode('cp1250').replace('\r', '').split('\n'):
    t = l.split()
    if len(t) >= 3 and t[0] == '0':
        alias[t[1].lower()] = t[2].lower()
    elif len(t) >= 2 and t[0].isdigit():
        npc[int(t[0])] = t[1].lower()
for v in D['vnums']:
    if v not in npc:
        fails.append('npclist: %d missing' % v)
        continue
    folder = alias.get(npc[v], npc[v])
    if not any('d:/ymir work/%s/%s/%s.msm' % (d, folder, folder) in NAMES
               for d in ('guild', 'npc', 'npc2', 'npc_pet', 'npc_mount', 'monster', 'monster2')):
        fails.append('race %d (%s): no msm in any pack or listing' % (v, folder))
b = read('gamedata/mob_proto')
magic, cnt, esize = struct.unpack_from('<4sII', b, 0)
raw = m2pack.mcoz_decode(b[12:12 + esize], pc.sd.MOB_KEY)
R = pc.sd.MOB_RECORD
mobs = set(struct.unpack_from('<I', raw, i * R)[0] for i in range(cnt))
sqlm = pc.sql_mobs()
for v in D['vnums']:
    if v not in mobs:
        (fails if v in sqlm else notes).append('mob_proto: %d not in the client%s' % (v, '' if v in sqlm else
                                                                                       ' (nor in balathor.sql)'))
lst = dict((l.split('\t')[0].strip(), l) for l in (read('gamedata/item_list.txt') or b'').decode('cp1250')
           .replace('\r', '').split('\n') if l.strip())
for k, line in D['item_list'].items():
    if lst.get(k, '').split() != line.split():
        fails.append('item_list %s: missing or other' % k)
    icon = line.split('\t')[2]
    if not os.path.isfile(os.path.join(ROOT_ICONS, os.path.basename(icon))) and norm(icon) not in NAMES:
        fails.append('item_list %s: icon %s neither in root/icon/item nor in our packs' % (k, icon))
    if len(line.split('\t')) > 3 and norm(line.split('\t')[3]) not in NAMES:
        notes.append('item_list %s: model %s not in our listing (the base client\'s item pack)' % (k, line.split('\t')[3]))
for icon in ('guild_whitedragon_boss.tga', 'guild_whitedragon_egg.tga'):
    if not os.path.isfile(os.path.join(ROOT_ICONS, icon)):
        fails.append('root/icon/item/%s missing (the boss window)' % icon)

# 4) dbdata
b = read('gamedata/item_proto')
ver, stride, icnt, size = struct.unpack_from('<IIII', b, 4)
iraw = m2pack.mcoz_decode(b[20:], pc.base.ITEM_KEY)
recs = dict((struct.unpack_from('<I', iraw, i * stride)[0], iraw[i * stride:(i + 1) * stride]) for i in range(icnt))
for vnum in D['items']:
    w = pc.sql_item(vnum)
    if recs.get(vnum) != pc.py.yitem_record(recs[pc.py.YITEM_TEMPLATE.get(w['type'], pc.py.TEMPLATE)], w):
        fails.append('item_proto %d: not the SQL\'s record' % vnum)
desc = dict((l.split('\t')[0].strip(), l) for l in (read('locale/pl/itemdesc.txt') or b'').decode('cp1250')
            .replace('\r', '').split('\n') if l.strip())
for k, line in D['itemdesc'].items():
    if desc.get(k) != line:
        fails.append('itemdesc %s: missing or other' % k)

# 5) locale and the named pictures / effects
lg = set(l.rstrip('\r') for l in (read('locale/pl/locale_game.txt') or b'').decode('cp1250').split('\n'))
for k, line in D['locale_game'].items():
    if line not in lg:
        fails.append('locale_game: %s missing or other' % k)
for n, b in bp.locale_files().items():
    if read(n) != b:
        fails.append('locale: %s missing or other' % n)
for k in D['effects']:
    if k not in NAMES:
        fails.append('effect %s in no pack or listing' % k)
for n in ('freezing_keyboard.sub', 'freezing_space_bar_default.sub', 'gauge_empty.sub', 'gauge_full.sub',
          'gauge_shine_01.sub'):
    if D['ui_dir'] + n not in NAMES:
        fails.append('window picture %s%s in no pack or listing' % (D['ui_dir'], n))

print('balathor: %d new pack(s) %s, %d staged files, %d problem(s), %d note(s)' % (
    len(MAN['new_packs']), MAN['new_packs'], sum(len(p) for p in MAN['packs'].values()), len(fails), len(notes)))
for f in fails:
    print('  FAIL ' + f)
for n in notes[:20]:
    print('  note ' + n)
sys.exit(1 if fails else 0)
