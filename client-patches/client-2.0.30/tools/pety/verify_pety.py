# -*- coding: utf-8 -*-
# MT2009_PLUS_GROWTH_PET_V1 - System Zwierzat Domowych's client data in OUT (build_pety_packs.py):
#   - gamedata/item_proto, item_list.txt, itemdesc.txt, mob_proto, npclist.txt exactly as patch_pety_client.py makes
#     them from <repo>/tools/pety/pety_items.json (its jobs change nothing); the old New Pet elixirs 55101-55118 gone;
#   - a mob_proto record and an npclist row for each of the 42 pet mobs, and each npclist model resolves (the exe's
#     d:/ymir work/<npc2|npc_pet|...>/<folder>/<model>.msm) to an .msm some pack has (OUT, BASE or the base-pack
#     listing tcm/gf28/ourpacks_pre.txt);
#   - pack "pety" = what the builder packs for this BASE / OUT, listed in pack/Index, no other pack of OUT with one of
#     its names;
#   - locale/pl/pet_skill.txt: 23 lines, cp1250, 6 tab columns (id, name, icon, PASSIVE|AUTO, description, cooldown);
#   - every d:/ymir work/ui/skill/pet/<icon>.sub of the 23 skills there, every icon of the json a 32x32 TGA, every
#     .sub of ui/pet/** and ui/skill/pet/ inside its picture.
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/pety/verify_pety.py \
#     <OUT pack dir> [<BASE pack dir>]        (BASE default /opt/metin2/cache/c55/pack; clientY.sh: $C/azbase)
# Exit 1 on a problem.
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, '/opt/metin2/cache/tcm/gf28')
sys.path.insert(0, HERE)
import m2pack  # noqa: E402
import packlib  # noqa: E402
import patch_pety_client as pc  # noqa: E402
import build_pety_packs as B  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith('--')]
OUT = args[0]
BASE = args[1] if len(args) > 1 else '/opt/metin2/cache/c55/pack'
fails = []
_dat = {}


def pack_entries(d, pack):
    pi = os.path.join(d, pack + '.index')
    if not os.path.exists(pi):
        return None
    return dict((e['name'], e) for e in m2pack.read_index(pi)[2])


def read(d, pack, e):
    if (d, pack) not in _dat:
        _dat[(d, pack)] = packlib.rd(os.path.join(d, pack + '.data'))
    return m2pack.read_entry(_dat[(d, pack)], e)


# where every name is (pety first, then OUT, then BASE - the packs a build has)
where = {}
pety = pack_entries(OUT, B.PACK)
if pety is None:
    fails.append('OUT has no %s pack' % B.PACK)
    pety = {}
for n, e in pety.items():
    where[n] = (OUT, B.PACK, e)
for d in (OUT, BASE):
    if not os.path.isdir(d):
        continue
    for p in sorted(f[:-6] for f in os.listdir(d) if f.endswith('.index')):
        if p == B.PACK:
            continue
        for n, e in pack_entries(d, p).items():
            where.setdefault(n, (d, p, e))
pre = B.pre_names()


def content(name):
    w = where.get(name)
    if w is None:
        return None
    try:
        return read(*w)
    except (IOError, OSError):
        return None


# 1) the data files
data = {}
for name, pack in sorted(pc.PACK_OF.items()):
    src = OUT if os.path.exists(os.path.join(OUT, pack + '.index')) else BASE
    ents = pack_entries(src, pack) or {}
    if name not in ents:
        fails.append('%s: missing in %s/%s' % (name, src, pack))
        continue
    data[name] = read(src, pack, ents[name])
    nb, changed = pc.JOBS[name](data[name])
    if changed:
        fails.append('%s: %d record(s) / line(s) not as patch_pety_client makes them' % (name, changed))
if 'gamedata/item_proto' in data:
    b = data['gamedata/item_proto']
    ver, stride, cnt, size = struct.unpack_from('<IIII', b, 4)
    raw = m2pack.mcoz_decode(b[20:], pc.base.ITEM_KEY)
    vn = set(struct.unpack_from('<I', raw, i * stride)[0] for i in range(cnt))
    left = sorted(set(pc.OLD_REMOVE) & vn)
    if left:
        fails.append('item_proto: old New Pet records still there: %s' % left)
    miss = sorted(set(it['vnum'] for it in pc.items()) - vn)
    if miss:
        fails.append('item_proto: no record of %s' % miss)
for name in ('gamedata/item_list.txt', 'locale/pl/itemdesc.txt'):
    if name in data:
        keys = set(l.split('\t')[0].strip() for l in data[name].decode('cp1250').splitlines())
        left = sorted(k for k in keys if k in set(str(v) for v in pc.OLD_REMOVE))
        if left:
            fails.append('%s: old New Pet lines still there: %s' % (name, left))
if 'gamedata/mob_proto' in data:
    b = data['gamedata/mob_proto']
    magic, cnt, es = struct.unpack_from('<4sII', b, 0)
    raw = m2pack.mcoz_decode(b[12:12 + es], pc.sd.MOB_KEY)
    R = pc.sd.MOB_RECORD
    vn = set(struct.unpack_from('<I', raw, i * R)[0] for i in range(cnt))
    miss = sorted(set(m['vnum'] for m in pc.data()['mobs']) - vn)
    if miss:
        fails.append('mob_proto: no record of %s' % miss)
if 'gamedata/npclist.txt' in data:
    race, src = {}, {}
    for l in data['gamedata/npclist.txt'].decode('cp1250').splitlines():
        t = [x.strip() for x in l.split('\t')]
        if len(t) >= 2 and t[0].isdigit():
            if t[0] == '0' and len(t) >= 3 and t[2]:
                src[t[1].lower()] = t[2].lower()
            elif t[0] != '0':
                race[int(t[0])] = t[1].lower()
    cats = ('npc_pet', 'npc2', 'npc', 'npc_mount', 'monster', 'monster2', 'guild')
    for m in pc.data()['mobs']:
        model = race.get(m['vnum'])
        if not model:
            fails.append('npclist.txt: no row of %d' % m['vnum'])
            continue
        folder = src.get(model, model)
        cands = ['d:/ymir work/%s/%s/%s.msm' % (c, folder, model) for c in cats]
        if not any(k in where or k in pre for k in cands):
            fails.append('npclist.txt: %d -> %s/%s.msm is in no pack' % (m['vnum'], folder, model))

# 2) pack "pety" = the builder's plan
try:
    want, info = B.plan(BASE, OUT)
except SystemExit as e:
    want, info = None, None
    fails.append('builder plan: %s' % e)
if want is not None:
    have = dict((n, read(OUT, B.PACK, e)) for n, e in pety.items())
    if set(have) != set(want):
        fails.append('%s: names differ from the plan: missing %s, extra %s' % (
            B.PACK, sorted(set(want) - set(have))[:10], sorted(set(have) - set(want))[:10]))
    diff = sorted(n for n in set(have) & set(want) if have[n] != want[n])
    if diff:
        fails.append('%s: content differs from the plan: %s' % (B.PACK, diff[:10]))
ix = open(os.path.join(OUT, 'Index'), 'rb').read() if os.path.exists(os.path.join(OUT, 'Index')) else b''
if B.PACK.encode() not in [l.strip() for l in ix.replace(b'\r\n', b'\n').split(b'\n')]:
    fails.append('pack/Index: no %s line' % B.PACK)
for p in sorted(x[:-6] for x in os.listdir(OUT) if x.endswith('.index')):
    if p == B.PACK:
        continue
    for n in pack_entries(OUT, p):
        if n in pety:
            fails.append('%s: also in %s (OUT)' % (n, p))

# 3) pet_skill.txt
ps = content('locale/pl/pet_skill.txt')
if ps is None:
    fails.append('locale/pl/pet_skill.txt missing')
else:
    if ps != pc.pet_skill_txt():
        fails.append('locale/pl/pet_skill.txt differs from the json')
    try:
        lines = [l for l in ps.decode('cp1250').split('\r\n') if l]
    except UnicodeDecodeError:
        lines = []
        fails.append('pet_skill.txt: not cp1250')
    if len(lines) != 23:
        fails.append('pet_skill.txt: %d lines, want 23' % len(lines))
    for i, l in enumerate(lines):
        t = l.split('\t')
        if len(t) != 6 or t[0] != str(i + 1) or t[3] not in ('PASSIVE', 'AUTO') or not t[5].isdigit() or \
                not all(t[:5]):
            fails.append('pet_skill.txt line %d: %r' % (i + 1, l))
            continue
        if content('d:/ymir work/ui/skill/pet/%s.sub' % t[2]) is None:
            fails.append('pet_skill.txt line %d: d:/ymir work/ui/skill/pet/%s.sub in no pack' % (i + 1, t[2]))

# 4) icons and .sub pictures
for icon in sorted(set(B.norm(it['icon']) for it in pc.items())):
    b = content(icon)
    if b is None:
        if icon not in pre:
            fails.append('%s: in no pack' % icon)
    elif not (len(b) > 18 and b[2] in (2, 10) and (b[12] | b[13] << 8) == 32 and (b[14] | b[15] << 8) == 32):
        fails.append('%s: not a 32x32 true-colour TGA' % icon)


def tex_size(b, name):
    if b[:4] == b'DDS ':
        return struct.unpack_from('<II', b, 12)[::-1]        # (width, height)
    if name.endswith('.tga') and len(b) > 18:
        return struct.unpack_from('<HH', b, 12)
    return None


subs = sorted(n for n in where if n.startswith(B.UI_DIRS) and n.endswith('.sub'))
if len([n for n in subs if n.startswith('d:/ymir work/ui/skill/pet/')]) < 19:
    fails.append('ui/skill/pet: %d .sub, want 19' % len([n for n in subs if n.startswith('d:/ymir work/ui/skill/pet/')]))
for n in subs:
    b = content(n)
    img = B.sub_image(n, b)
    tb = content(img)
    if tb is None:
        fails.append('%s: picture %s in no pack' % (n, img))
        continue
    wh = tex_size(tb, img)
    kv = dict(l.split(None, 1) for l in b.decode('latin1').splitlines() if len(l.split(None, 1)) == 2)
    try:
        l, t, r, bt = [int(kv[k]) for k in ('left', 'top', 'right', 'bottom')]
    except (KeyError, ValueError):
        fails.append('%s: no rectangle' % n)
        continue
    if wh is None or not (0 <= l < r <= wh[0] and 0 <= t < bt <= wh[1]):
        fails.append('%s: rectangle %s outside %s %s' % (n, (l, t, r, bt), img, wh))

print('pety: %d items, %d mobs, %d pack files, %d .sub checked, %d problem(s)' % (
    len(pc.items()), len(pc.data()['mobs']), len(pety), len(subs), len(fails)))
for x in fails:
    print('  ' + x)
sys.exit(1 if fails else 0)
