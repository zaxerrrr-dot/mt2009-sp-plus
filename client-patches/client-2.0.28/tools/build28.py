# -*- coding: utf-8 -*-
# Client 2.0.28 (MT2009 PLUS): c27 packs + root (w27) + New Pet System + Temple of
# Ochao + Razador/Nemere protos + Treasure Hunt (goblin) + Wheel of Fortune ticket.
#   docker run --rm -v /opt/metin2/cache/tcm/tz:/w -v /opt/metin2/cache/tcm:/t \
#     -v /opt/metin2/cache/tcm/c28w:/s m2pack-lzo python3 /s/build28.py
import os, sys, struct, zlib, shutil, json
sys.path.insert(0, '/w')
import m2pack
sys.path.insert(0, '/s')
import protolib as P

T = '/t'
C27 = T + '/c27/pack'
X27 = '/s/x27'
OUT = '/s/out/pack'
STAGE = '/s/stage'
GOB = '/s/goblin/02. Client'
LOG = []
def log(*a):
    s = ' '.join(str(x) for x in a); print(s); LOG.append(s)

for d in (OUT, STAGE):
    if os.path.isdir(d): shutil.rmtree(d)
    os.makedirs(d)

def rd(p): return open(p, 'rb').read()
def stage(rel, data):
    p = os.path.join(STAGE, rel.replace('d:/', 'd_/'))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'wb').write(data)

TEXT_EXT = {'txt', 'msm', 'msa', 'mse', 'msf', 'mde', 'msenv', 'prb', 'prd', 'pre', 'sub', 'py', 'mss', 'json'}
def ctype_for(name):
    ext = name.rsplit('.', 1)[-1].lower()
    return 2 if ext in TEXT_EXT else 1

def pack_blob(newidx):
    import lzo
    comp = lzo.compress(bytes(newidx), 1, False)
    enc_len = (len(comp) + 19 + 7) // 8 * 8
    inner = struct.pack('<I', m2pack.MCOZ) + comp; inner += b'\0' * (enc_len - len(inner))
    return struct.pack('<4I', m2pack.MCOZ, enc_len, len(comp), len(newidx)) + m2pack.tea_encrypt(inner, m2pack.IDX_KEY) + b'\0' * 4

def repack_add_typed(index_path, data_path, replace, add, out_index, out_data, template_rec=None):
    """m2pack.repack_add with a type per new entry: add = {name: (raw, ctype)}.
    Existing entries keep their id/type; new ones get the next ids,
    crc32(name) and their own type; the header's count follows."""
    four, ver, ents = m2pack.read_index(index_path) if index_path else (b'EPKD', 2, [])
    data = rd(data_path) if data_path else b''
    head = bytearray(m2pack.mcoz_decode(rd(index_path), m2pack.IDX_KEY)[:12]) if index_path else bytearray(b'EPKD' + struct.pack('<II', 2, 0))
    tmpl = template_rec or ents[-1]['raw']
    next_id = max([e['id'] for e in ents] + [-1]) + 1
    names = set(e['name'] for e in ents)
    replace = dict(replace)
    added = []
    for name, (content, ct) in sorted(add.items()):
        assert name == name.lower() and '\\' not in name, name
        if name in names:
            raise SystemExit('add: exists ' + name)
        rec = bytearray(tmpl)
        struct.pack_into('<I', rec, 0, next_id)
        nb = name.encode('cp1252'); assert len(nb) < 161, name
        rec[4:165] = nb + b'\0' * (161 - len(nb))
        struct.pack_into('<I', rec, 168, zlib.crc32(nb) & 0xffffffff)
        rec[188] = ct
        added.append(dict(id=next_id, name=name, pos=1 << 40, ctype=ct, raw=bytes(rec)))
        replace[name] = content
        next_id += 1
    for n in replace: assert n in names or n in add, 'replace: missing ' + n
    allents = ents + added
    out = bytearray(); by_id = {}; pos = 0
    for e in sorted(allents, key=lambda x: (x['pos'], x['id'])):
        blob = m2pack.encode_entry(replace[e['name']], e['ctype']) if e['name'] in replace else data[e['pos']:e['pos'] + e['size']]
        slot = (len(blob) + 255) // 256 * 256
        rec = bytearray(e['raw'])
        struct.pack_into('<iiIi', rec, 172, slot, len(blob), zlib.crc32(blob) & 0xffffffff, pos)
        by_id[e['id']] = bytes(rec)
        out += blob + b'\0' * (slot - len(blob)); pos += slot
    struct.pack_into('<I', head, 8, len(allents))
    newidx = bytes(head) + b''.join(by_id[e['id']] for e in allents)
    open(out_index, 'wb').write(pack_blob(newidx)); open(out_data, 'wb').write(bytes(out))
    return len(ents), len(added), len(replace) - len(added)

def verify_pack(pack, expect):
    """read every entry back; expect = {name: raw bytes} must match."""
    f, v, ents = m2pack.read_index(OUT + '/%s.index' % pack)
    data = rd(OUT + '/%s.data' % pack)
    names = [e['name'] for e in ents]
    assert len(names) == len(set(names)), pack + ' duplicate names'
    got = {}
    for e in ents:
        raw = m2pack.read_entry(data, e)
        assert zlib.crc32(data[e['pos']:e['pos'] + e['size']]) & 0xffffffff == e['dcrc']
        assert e['fcrc'] == zlib.crc32(e['name'].encode('cp1252')) & 0xffffffff
        got[e['name']] = raw
    for n, b in expect.items():
        assert got.get(n) == b, pack + ': mismatch ' + n
    log('verify %s: %d entries readable, %d checked byte-exact' % (pack, len(ents), len(expect)))
    return got

def crlf_append(b, lines):
    if b and not b.endswith(b'\r\n'):
        b = b + b'\r\n'
    return b + b''.join(l.encode('cp1250') + b'\r\n' for l in lines)

def vnums_of_text(b):
    s = set()
    for l in b.decode('cp1250').split('\n'):
        t = l.split('\t')[0].strip()
        if t.isdigit(): s.add(int(t))
    return s

# ---------------------------------------------------------------- gamedata
GD = X27 + '/gamedata/gamedata/'
base_item = rd(GD + 'item_proto'); base_mob = rd(GD + 'mob_proto')
ver0, base_irecs = P.load_item(base_item); base_mrecs = P.load_mob(base_mob)
log('c27: item_proto %d rows, mob_proto %d rows' % (len(base_irecs), len(base_mrecs)))

# 1) New Pet System: their item_proto / item_list / itemdesc (built from c27)
pet_item = rd(T + '/newpet_pack/gamedata/item_proto')
_, pet_irecs = P.load_item(pet_item)
pet_by = dict((P.vnum(r), r) for r in pet_irecs)
for r in base_irecs:
    assert pet_by.get(P.vnum(r)) == r, 'newpet item_proto changed a c27 row %d' % P.vnum(r)
PET_NEW = sorted(set(pet_by) - set(P.vnum(r) for r in base_irecs))
log('pets: +%d item rows (%d..%d), 55009 in: %s' % (len(PET_NEW), PET_NEW[0], PET_NEW[-1], 55009 in pet_by))
item_list = rd(T + '/newpet_pack/gamedata/item_list.txt')
assert item_list.startswith(rd(GD + 'item_list.txt'))
itemdesc = rd(T + '/newpet_pack/locale/pl/itemdesc.txt')
base_desc = rd(X27 + '/locale/locale/pl/itemdesc.txt')
assert itemdesc.startswith(base_desc)
item_bytes = pet_item
mob_bytes = base_mob
npclist = rd(GD + 'npclist.txt'); atlas = rd(GD + 'atlasinfo.txt')

# 2) Temple of Ochao: their idempotent patcher on the current files
sys.path.insert(0, T + '/ochao_client/tools')
import patch_gamedata_ochao as OCH
atlas, n1 = OCH.patch_atlas(atlas); npclist, n2 = OCH.patch_npclist(npclist); mob_bytes, n3 = OCH.patch_mob_proto(mob_bytes)
log('ochao: atlasinfo +%d, npclist +%d, mob_proto +%d' % (n1, n2, n3))

# 3) Razador / Nemere: their idempotent patcher on the current protos
sys.path.insert(0, T + '/dungeons_client/tools')
import patch_protos as DUN
tmp = '/s/tmp_dun'; os.makedirs(tmp, exist_ok=True)
open(tmp + '/mob_in', 'wb').write(mob_bytes); open(tmp + '/item_in', 'wb').write(item_bytes)
DUN.patch_mob(tmp + '/mob_in', tmp + '/mob_out'); DUN.patch_item(tmp + '/item_in', tmp + '/item_out')
mob_bytes = rd(tmp + '/mob_out'); item_bytes = rd(tmp + '/item_out')
have = vnums_of_text(item_list)
add = [l for l in rd(T + '/dungeons_client/gamedata/item_list.add.txt').decode('cp1250').splitlines() if l.strip() and int(l.split('\t')[0]) not in have]
item_list = crlf_append(item_list, add)
have = vnums_of_text(itemdesc)
add = [l for l in rd(T + '/dungeons_client/locale/pl/itemdesc.add.txt').decode('cp1250').splitlines() if l.strip() and int(l.split('\t')[0]) not in have]
itemdesc = crlf_append(itemdesc, add)
log('dungeons: item_list/itemdesc +%d lines' % len(add))

# 4) Treasure Hunt (goblin) + 5) Wheel of Fortune ticket
ver, irecs = P.load_item(item_bytes); mrecs = P.load_mob(mob_bytes)
iby = dict((P.vnum(r), i) for i, r in enumerate(irecs)); mby = dict((P.vnum(r), i) for i, r in enumerate(mrecs))

def mk_item(v, tpl, name, lname, typ, sub, antiflag, flag, limit0=None, value0=0):
    r = bytearray(irecs[iby[tpl]])
    struct.pack_into('<II', r, 0, v, 0)
    r = bytearray(P.setstr(bytes(r), 8, 33, name)); r = bytearray(P.setstr(bytes(r), 41, 33, lname))
    r[74] = typ; r[75] = sub; r[76] = 0; r[77] = 1
    struct.pack_into('<I', r, 78, 200)              # stack
    struct.pack_into('<I', r, 82, antiflag)
    struct.pack_into('<I', r, 86, flag)
    struct.pack_into('<II', r, 90, 0, 0)            # wear, immune
    r[98:114] = b'\0' * 16                          # gold, shop price
    r[114:124] = b'\0' * 10                         # limits
    if limit0: r[114] = limit0[0]; struct.pack_into('<i', r, 115, limit0[1])
    r[124:139] = b'\0' * 15                         # applies
    struct.pack_into('<6i', r, 139, value0, 0, 0, 0, 0, 0)
    return bytes(r)

def mk_mob(v, tpl, name, typ, rank, level, maxhp, regen, def_, ai, immune, rng, onclick):
    r = bytearray(mrecs[mby[tpl]])
    struct.pack_into('<I', r, 0, v)
    r = bytearray(P.setstr(bytes(r), 4, 25, name)); r = bytearray(P.setstr(bytes(r), 29, 25, name))
    r[54] = typ; r[55] = rank; r[56] = 0; r[57] = level
    struct.pack_into('<IIII', r, 59, 0, 0, 0, maxhp)   # gold min/max, exp, max hp
    r[75], r[76] = regen
    struct.pack_into('<HIII', r, 77, def_, ai, 0, immune)
    r[91:103] = b'\0' * 12                               # st dx ht iq, damage
    struct.pack_into('<hhBHH', r, 103, 100, 100, 0, 2000, rng)
    r[138] = onclick; r[139] = 0
    return bytes(r)

NEW_ITEMS = {
    70617: mk_item(70617, 80017, 'Treasure Ticket', u'Bilet Skarbów', 3, 10, 221312, 8196, limit0=(1, 70)),
    70618: mk_item(70618, 80017, 'Goblin Key', u'Klucz Goblina', 3, 10, 221312, 8196),
    70619: mk_item(70619, 80017, 'Goblin Key Box', u'Szkatułka z Kluczami Goblina', 3, 10, 221312, 8196),
    80030: mk_item(80030, 80017, 'Bilet Kola Fortuny', u'Bilet Koła Fortuny', 18, 0, 384, 8196),
}
NEW_MOBS = {
    20856: mk_mob(20856, 9012, u'Goblin Skarbów', 1, 0, 1, 180000, (0, 0), 0, 0, 0x22, 175, 0),
    20857: mk_mob(20857, 9012, u'Wielka Skrzynia Skarbów', 1, 0, 1, 120, (3, 1), 4, 2, 0x23, 175, 0),
}
for v, r in NEW_ITEMS.items():
    if v in iby: irecs[iby[v]] = r
    else: irecs.append(r)
for v, r in NEW_MOBS.items():
    if v in mby: mrecs[mby[v]] = r
    else: mrecs.append(r)
irecs.sort(key=P.vnum); mrecs.sort(key=P.vnum)
item_bytes = P.save_item(ver, irecs); mob_bytes = P.save_mob(mrecs)

ATL = 'metin2_map_treasure_hunt\t512000\t1203200\t3\t3'
if not any(l.split('\t')[0].strip().lower() == 'metin2_map_treasure_hunt' for l in atlas.decode('cp1250').splitlines()):
    atlas = crlf_append(atlas.rstrip(b'\r\n') + b'\r\n', [ATL])
npl = npclist.decode('cp1250')
for v, f in ((20856, 'treasure_hunt_goblin'), (20857, 'treasure_hunt_box')):
    assert '%d\t%s' % (v, f) in npl, 'npclist lacks %d' % v
have = vnums_of_text(item_list)
item_list = crlf_append(item_list, [l for l in (
    '70617\tETC\ticon/item/70617.tga', '70618\tETC\ticon/item/70618.tga', '70619\tETC\ticon/item/70619.tga',
    '80030\tETC\ticon/item/dragonticket.tga') if int(l.split('\t')[0]) not in have])
have = vnums_of_text(itemdesc)
itemdesc = crlf_append(itemdesc, [l for l in (
    u'70617\tBilet Skarbów\tTym biletem możesz udać się na Wyspę Skarbów.',
    u'70618\tKlucz Goblina\tTym kluczem zdobędziesz więcej nagród w Poszukiwaniu skarbów.',
    u'70619\tSzkatułka z Kluczami Goblina\tZawiera 8 Kluczy Goblina.',
    u'80030\tBilet Koła Fortuny\tBilet na jeden obrót Kołem Fortuny (F12). Kupisz go w ItemShopie za Smocze Monety.',
) if int(l.split('\t')[0]) not in have])

GD_FILES = {'gamedata/item_proto': item_bytes, 'gamedata/mob_proto': mob_bytes, 'gamedata/item_list.txt': item_list,
            'gamedata/npclist.txt': npclist, 'gamedata/atlasinfo.txt': atlas}
GD_FILES = dict((k, v) for k, v in GD_FILES.items() if v != rd(GD + k.split('/', 1)[1]))
log('gamedata changed:', sorted(GD_FILES))
r = repack_add_typed(C27 + '/gamedata.index', C27 + '/gamedata.data', GD_FILES, {}, OUT + '/gamedata.index', OUT + '/gamedata.data')
log('gamedata pack: %d entries, +%d new, %d replaced' % r)
for k, v in GD_FILES.items(): stage('gamedata/' + k, v)

# locale
LOC = {'locale/pl/itemdesc.txt': itemdesc}
r = repack_add_typed(C27 + '/locale.index', C27 + '/locale.data', LOC, {}, OUT + '/locale.index', OUT + '/locale.data')
log('locale pack: %d entries, +%d new, %d replaced' % r)
for k, v in LOC.items(): stage('locale/' + k, v)

# icon
ICON = {}
for v in (70617, 70618, 70619):
    ICON['icon/item/%d.tga' % v] = (rd(GOB + '/icon/icon/item/%d.tga' % v), 1)
f_, v_, icon_ents = m2pack.read_index(C27 + '/icon.index')
tmpl = [e for e in icon_ents if e['name'] == 'icon/item/80017.tga'][0]['raw']
assert any(e['name'] == 'icon/item/dragonticket.tga' for e in icon_ents)
r = repack_add_typed(C27 + '/icon.index', C27 + '/icon.data', {}, ICON, OUT + '/icon.index', OUT + '/icon.data', tmpl)
log('icon pack: %d entries, +%d new, %d replaced' % r)
for k, (v, c) in ICON.items(): stage('icon/' + k, v)

# maps: Treasure Island + Temple of Ochao
MAPS = {}
def add_tree(dst, src, prefix):
    for dp, dn, fn in os.walk(src):
        for f in fn:
            p = os.path.join(dp, f)
            name = (prefix + os.path.relpath(p, src).replace(os.sep, '/')).lower()
            dst[name] = (rd(p), ctype_for(name))
add_tree(MAPS, GOB + '/map/metin2_map_treasure_hunt', 'maps/metin2_map_treasure_hunt/')
MAPS['maps/metin2_map_treasure_hunt/metin2_map_treasure_hunt.msenv'] = (rd(GOB + '/d/ymir work/environment/metin2_map_treasure_hunt.msenv'), 2)
add_tree(MAPS, T + '/ochao_client/maps/maps/metin2_map_mt_th_dungeon_01', 'maps/metin2_map_mt_th_dungeon_01/')
r = repack_add_typed(C27 + '/maps.index', C27 + '/maps.data', {}, MAPS, OUT + '/maps.index', OUT + '/maps.data')
log('maps pack: %d entries, +%d new, %d replaced' % r)
for k, (v, c) in MAPS.items(): stage('maps/' + k, v)

# new pack: goblin (Treasure Island assets)
GOBP = {}
add_tree(GOBP, GOB + '/npc2/ymir work/npc2/treasure_hunt_goblin', 'd:/ymir work/npc2/treasure_hunt_goblin/')
add_tree(GOBP, GOB + '/npc2/ymir work/npc2/treasure_hunt_box', 'd:/ymir work/npc2/treasure_hunt_box/')
add_tree(GOBP, GOB + '/zone/treasure_hunt', 'd:/ymir work/zone/treasure_hunt/')
for rel in ('environment/metin2_map_treasure_hunt.msenv', 'ui/atlas/metin2_map_treasure_hunt/atlas.sub',
            'ui/atlas_resize/metin2_map_treasure_hunt/atlas.sub', 'ui/atlas_resize/metin2_map_treasure_hunt_atlas.dds',
            'ui/metin2_map_treasure_hunt_atlas.dds', 'ui/treasure_hunt_01.dds'):
    n = 'd:/ymir work/' + rel
    GOBP[n] = (rd(GOB + '/d/ymir work/' + rel), ctype_for(n))
GOBP['textureset/metin2_map_treasure_hunt.txt'] = (rd('/s/textureset_treasure_hunt.txt'), 2)
tmpl = [e for e in m2pack.read_index(T + '/newpet_pack/pack/newpet.index')[2]][0]['raw']
r = repack_add_typed(None, None, {}, GOBP, OUT + '/goblin.index', OUT + '/goblin.data', tmpl)
log('goblin pack: %d entries, +%d new' % r[:2])
for k, (v, c) in GOBP.items(): stage('goblin/' + k, v)

# new pack: ochao
OCHP = {}
add_tree(OCHP, T + '/ochao_client/ochao_pack/d_', 'd:/')
add_tree(OCHP, T + '/ochao_client/ochao_pack/sound', 'sound/')
add_tree(OCHP, T + '/ochao_client/ochao_pack/textureset', 'textureset/')
r = repack_add_typed(None, None, {}, OCHP, OUT + '/ochao.index', OUT + '/ochao.data', tmpl)
log('ochao pack: %d entries, +%d new' % r[:2])
for k, (v, c) in OCHP.items(): stage('ochao/' + k, v)

# new pack: newpet (as built by the pets agent)
for ext in ('index', 'data'):
    shutil.copy(T + '/newpet_pack/pack/newpet.' + ext, OUT + '/newpet.' + ext)
f_, v_, np_ents = m2pack.read_index(OUT + '/newpet.index'); np_data = rd(OUT + '/newpet.data')
for e in np_ents: stage('newpet/' + e['name'], m2pack.read_entry(np_data, e))

# property (NOT packable here: needs the client's own pack/property)
for src, pre in ((GOB + '/property/treasure_hunt', 'property/property/treasure_hunt/'),
                 (T + '/ochao_client/property/property', 'property/property/')):
    for dp, dn, fn in os.walk(src):
        for f in fn:
            p = os.path.join(dp, f); stage(pre + os.path.relpath(p, src).replace(os.sep, '/'), rd(p))

# root: every w27 file that differs from / is missing in c27 root
f_, v_, root_ents = m2pack.read_index(C27 + '/root.index'); root_data = rd(C27 + '/root.data')
root_have = dict((e['name'], m2pack.read_entry(root_data, e)) for e in root_ents)
RREP = {}; RADD = {}
for dp, dn, fn in os.walk(T + '/w27'):
    for f in fn:
        p = os.path.join(dp, f); name = os.path.relpath(p, T + '/w27').replace(os.sep, '/')
        b = rd(p)
        if name in root_have:
            if root_have[name] != b: RREP[name] = b
        else:
            RADD[name] = (b, 1 if name.endswith('.tga') else 2)
tmpl_py = [e for e in root_ents if e['name'] == 'uiscript/mt2009battlepass.py'][0]['raw']
r = repack_add_typed(C27 + '/root.index', C27 + '/root.data', RREP, RADD, OUT + '/root.index', OUT + '/root.data', tmpl_py)
log('root pack: %d entries, +%d new, %d replaced' % r)
for k, v in RREP.items(): stage('root/' + k, v)
for k, (v, c) in RADD.items(): stage('root/' + k, v)

# Index
idx = rd(C27 + '/Index')
assert idx.endswith(b'maps\n')
idx += b'*\nnewpet\n*\nochao\n*\ngoblin\n'
open(OUT + '/Index', 'wb').write(idx)
stage('Index', idx)

# ---------------------------------------------------------------- verification
got = verify_pack('gamedata', GD_FILES)
verify_pack('locale', LOC)
verify_pack('icon', dict((k, v) for k, (v, c) in ICON.items()))
verify_pack('maps', dict((k, v) for k, (v, c) in MAPS.items()))
verify_pack('goblin', dict((k, v) for k, (v, c) in GOBP.items()))
verify_pack('ochao', dict((k, v) for k, (v, c) in OCHP.items()))
verify_pack('newpet', {})
rootx = dict(RREP); rootx.update((k, v) for k, (v, c) in RADD.items())
verify_pack('root', rootx)
# old entries unchanged
for pack in ('gamedata', 'locale', 'icon', 'maps', 'root'):
    f_, v_, old = m2pack.read_index(C27 + '/%s.index' % pack); od = rd(C27 + '/%s.data' % pack)
    f_, v_, new = m2pack.read_index(OUT + '/%s.index' % pack); nd = rd(OUT + '/%s.data' % pack)
    nb = dict((e['name'], e) for e in new)
    changed = [e['name'] for e in old if m2pack.read_entry(od, e) != m2pack.read_entry(nd, nb[e['name']])]
    log('%s: %d old entries kept, %d changed: %s, total %d' % (pack, len(old), len(changed), changed[:12] if len(changed) <= 12 else str(len(changed)) + ' files', len(new)))

ver, irecs = P.load_item(got['gamedata/item_proto']); mrecs = P.load_mob(got['gamedata/mob_proto'])
iv = [P.vnum(r) for r in irecs]; mv = [P.vnum(r) for r in mrecs]
EXP_I = set(PET_NEW) | {30760, 30761, 30762, 70617, 70618, 70619, 80030}
EXP_M = {6301, 6302, 6303, 6304, 6305, 6311, 6390, 6400, 20415, 20426, 8058, 20397, 20398, 20399, 20856, 20857}
base_iv = set(P.vnum(r) for r in base_irecs); base_mv = set(P.vnum(r) for r in base_mrecs)
new_i = EXP_I - base_iv; new_m = EXP_M - base_mv
log('item_proto: %d rows = c27 %d + %d new (expected %d), dups %d, sorted %s, missing %s' % (
    len(iv), len(base_iv), len(set(iv) - base_iv), len(new_i), len(iv) - len(set(iv)), iv == sorted(iv), sorted(EXP_I - set(iv))))
log('mob_proto: %d rows = c27 %d + %d new (expected %d), dups %d, sorted %s, missing %s' % (
    len(mv), len(base_mv), len(set(mv) - base_mv), len(new_m), len(mv) - len(set(mv)), mv == sorted(mv), sorted(EXP_M - set(mv))))
assert set(iv) - base_iv == new_i and set(mv) - base_mv == new_m and len(iv) == len(set(iv)) and len(mv) == len(set(mv))
il = got['gamedata/item_list.txt'].decode('cp1250').splitlines()
ilv = [int(l.split('\t')[0]) for l in il if l.split('\t')[0].strip().isdigit()]
log('item_list: %d lines, dup vnums %d, missing new %s' % (len(il), len(ilv) - len(set(ilv)), sorted(EXP_I - set(ilv))))
dl = itemdesc.decode('cp1250').splitlines()
dlv = [int(l.split('\t')[0]) for l in dl if l.split('\t')[0].strip().isdigit()]
log('itemdesc: %d lines, dup vnums %d, missing new %s' % (len(dl), len(dlv) - len(set(dlv)), sorted(EXP_I - set(dlv))))
# atlasinfo rect overlaps
rects = []
for l in got['gamedata/atlasinfo.txt'].decode('cp1250').splitlines():
    t = l.split()
    if len(t) == 5: rects.append((t[0], int(t[1]), int(t[2]), int(t[1]) + int(t[3]) * 25600, int(t[2]) + int(t[4]) * 25600))
for nm in ('metin2_map_treasure_hunt', 'metin2_map_mt_th_dungeon_01'):
    me = [x for x in rects if x[0].lower() == nm]; assert len(me) == 1, nm
    a = me[0]
    ov = [x[0] for x in rects if x is not a and x[1] < a[3] and a[1] < x[3] and x[2] < a[4] and a[2] < x[4]]
    log('atlasinfo %s %s overlaps: %s' % (nm, a[1:], ov))
for v in sorted(EXP_I & {70617, 70618, 70619, 80030, 55009}):
    r = irecs[iv.index(v)]
    log('item %d: %s | type %d/%d stack %d anti %d flag %d limit0 %d/%d value0 %d' % (
        v, r[41:74].split(b'\0')[0].decode('cp1250'), r[74], r[75], struct.unpack_from('<I', r, 78)[0],
        struct.unpack_from('<I', r, 82)[0], struct.unpack_from('<I', r, 86)[0], r[114], struct.unpack_from('<i', r, 115)[0],
        struct.unpack_from('<i', r, 139)[0]))
for v in (20856, 20857):
    r = mrecs[mv.index(v)]
    log('mob %d: %s | type %d rank %d lvl %d hp %d ai %d immune %#x' % (v, r[29:54].split(b'\0')[0].decode('cp1250'), r[54], r[55], r[57],
        struct.unpack_from('<I', r, 71)[0], struct.unpack_from('<I', r, 79)[0], struct.unpack_from('<I', r, 87)[0]))
open('/s/build28.log', 'w').write('\n'.join(LOG) + '\n')
json.dump({'root_replaced': sorted(RREP), 'root_added': sorted(RADD), 'gamedata': sorted(GD_FILES), 'locale': sorted(LOC),
           'icon': sorted(ICON), 'maps': sorted(MAPS), 'goblin': sorted(GOBP), 'ochao': sorted(OCHP),
           'newpet': sorted(e['name'] for e in np_ents)}, open('/s/build28.files.json', 'w'), indent=1)
print('OK')
