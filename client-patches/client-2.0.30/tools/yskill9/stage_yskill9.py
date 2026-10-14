# -*- coding: utf-8 -*-
# MT2009_PLUS_SKILL9_V1 (client) - the 9th skills of Yohara: the files of the new pack(s) "yskill9", staged from the GF
# 26.1.11 client (and, for what GF lacks, the Ameria client sources) for build_yskill9_packs.py.
#
#   python3 stage_yskill9.py [<staging dir>] [<work dir>]        (host; no lzo needed)
#
# defaults: /opt/metin2/cache/yohara/yskill9-staging, /opt/metin2/cache/yohara/cape301-work (c58.lst: the client we
# build on). Writes <staging>/add/<pack>/<in-pack name> ("d:/" as "d_/") and tools/yskill9/yskill9_manifest.json.
#
# What the client needs (server-patches/skill9/README.md), per race folder - pc/ and pc2/ of each class (exe 2.0.25:
# warrior_m pc/warrior, warrior_w pc2/warrior, assassin_w pc/assassin, assassin_m pc2/assassin, sura_m pc/sura,
# sura_w pc2/sura, shaman_w pc/shaman, shaman_m pc2/shaman):
#   skill/<motion>.msa, _2/_3/_4.msa (the four grades) and <motion>.gr2      (the exe registers them: client-patches/exe
#                                                                            PythonPlayerSettingsModule.cpp)
#   everything the motions name (effects .mse/.msf/.mde, their textures and models) and their sounds (sound/<folder>/
#   skill/<motion>*.mss and the .wav they play) - gfres.closure
#   d:/ymir work/ui/skill/<job>/<icon>_01..03.sub - the skill window's icons (skilldesc's icon column) and
#   d:/ymir work/ui/skill/common/affect/cheonun.sub - Tarcza Eteru's affect icon. GF's .sub cut them from the class
#   atlases SkillWarrior/Assassin/Sura/Shaman.dds of 256x288 and newskillcommon.dds - ours are 256x256 (and our
#   newskillcommon is another size): the atlases go in under new names (d:/ymir work/ui/skill9_<class>.dds,
#   skill9_common.dds - GF's, from the Ameria sources: GF's own are in its encrypted blobs) and the .sub are GF's
#   with their image renamed (generated, version 1.0: the exe looks for the image in d:/ymir work/ui/).
#   d:/ymir work/pc/shaman/effect/chunwoon_moojuk.mse - the protection's effect (the server's SpecificEffectPacket)
# A name our client has already (c58.lst, the base packs' listing ourpacks_pre.txt, the earlier Yohara builders'
# manifests) is not staged again: ours stays.
import hashlib
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'az58'))
import gfres  # noqa: E402  (indexes the GF client at import)

gfres.GR2DIR = '/opt/metin2/cache/arezzo-work/client/az58/gr2'
gfres.GR2DEC = os.path.join(gfres.GR2DIR, 'gr2dec')

STAGING = sys.argv[1] if len(sys.argv) > 1 else '/opt/metin2/cache/yohara/yskill9-staging'
WORK = sys.argv[2] if len(sys.argv) > 2 else '/opt/metin2/cache/yohara/cape301-work'
OURS_LST = os.path.join(WORK, 'c58.lst')
PRE_LST = '/opt/metin2/cache/tcm/gf28/ourpacks_pre.txt'
AMERIA = '/opt/metin2/ameria/ameria-prj-2025/tools/FoxFSArchiver/source'
GR2_64 = b'\xe5\x9b\x49\x5e'
SPLIT = 26 * 1000 * 1000
PACK = 'yskill9'
norm = gfres.norm

# class -> (folders, [(skill vnum, motion file, icon)])
SKILLS = {
    'warrior': [(176, 'finish', 'finish')],
    'assassin': [(177, 'ilgangpyo', 'ilgwangpyo'), (178, 'pungraepo', 'pungloepo')],
    'sura': [(179, 'akgi', 'geomaggwi'), (180, 'akgi_dark', 'mabeobaggwi')],
    'shaman': [(181, 'meteo', 'meteo'), (182, 'chunwoon', 'cheonun')],
}
EXTRA = ['d:/ymir work/pc/shaman/effect/chunwoon_moojuk.mse']
ATLAS = {'warrior': 'etc/ymir work/ui/skillwarrior.dds', 'assassin': 'etc/ymir work/ui/skillassassin.dds',
         'sura': 'etc/ymir work/ui/skillsura.dds', 'shaman': 'etc/ymir work/ui/skillshaman.dds',
         'common': 'patch2/ymir work/ui/newskillcommon.dds'}
GEN = '/opt/metin2/cache/yohara/yskill9-gen'

OURS = set(gfres.load_ours(PRE_LST))
for l in open(OURS_LST, encoding='utf-8', errors='replace'):
    t = l.rstrip('\n').split(' ', 1)
    if len(t) == 2:
        OURS.add(norm(t[1]))
for d in ('cape301', 'maps302', 'shipdefense', 'port368', 'ymaps', 'ymaps2', 'ymaps3'):
    mp = os.path.join(HERE, '..', d, d + '_manifest.json')
    if os.path.exists(mp):
        man = json.load(open(mp, encoding='utf-8'))
        OURS |= set(e['name'] for p in man['packs'].values() for e in p)


def index_ameria(root):
    m = {}
    if not os.path.isdir(root):
        return m
    for top in sorted(os.listdir(root)):
        tp = os.path.join(root, top)
        if not os.path.isdir(tp):
            continue
        for sub in os.listdir(tp):
            sp = os.path.join(tp, sub)
            if not os.path.isdir(sp):
                continue
            if sub.lower() == 'ymir work':
                pref = 'd:/ymir work/'
            elif sub.lower() in ('sound', 'icon'):
                pref = sub.lower() + '/'
            else:
                continue
            for dp, dn, fn in os.walk(sp):
                for f in fn:
                    ap = os.path.join(dp, f)
                    m.setdefault(norm(pref + os.path.relpath(ap, sp)), ap)
    return m


AMERIA_IDX = index_ameria(AMERIA)

seeds = list(EXTRA)
motions = {}
icons = {}
for job, skills in SKILLS.items():
    for vnum, motion, icon in skills:
        for i in (1, 2, 3):
            icons['d:/ymir work/ui/skill/%s/%s_0%d.sub' % (job, icon, i)] = job
        for folder in ('pc', 'pc2'):
            base = 'd:/ymir work/%s/%s/skill/%s' % (folder, job, motion)
            names = [base + '.gr2'] + [base + s + '.msa' for s in ('', '_2', '_3', '_4')]
            seeds += names
            motions.setdefault(str(vnum), []).extend(names)

files, unresolved, ours_hit = gfres.closure(seeds, OURS)
# What GF lacks (its encrypted blobs) from Ameria's sources, followed the same way.
from_ameria = {}
todo = sorted(k for k in unresolved if k in AMERIA_IDX)
while todo:
    k = todo.pop()
    if k in files or k in from_ameria:
        continue
    from_ameria[k] = AMERIA_IDX[k]
    unresolved.pop(k, None)
    for r in gfres.refs_of(k, AMERIA_IDX[k]):
        if r in files or r in from_ameria or r in OURS:
            continue
        if r in gfres.GF:
            f2, u2, o2 = gfres.closure([r], OURS)
            files.update(f2)
            for kk in u2:
                if kk in AMERIA_IDX:
                    todo.append(kk)
                else:
                    unresolved.setdefault(kk, 'ref')
        elif r in AMERIA_IDX:
            todo.append(r)
        else:
            unresolved.setdefault(r, 'ref')
files.update(from_ameria)

# the icons: GF's .sub with the image renamed, the atlases under their new names
if os.path.isdir(GEN):
    shutil.rmtree(GEN)
icons['d:/ymir work/ui/skill/common/affect/cheonun.sub'] = 'common'
for key, job in sorted(icons.items()):
    src = gfres.GF[key]
    txt = open(src, 'rb').read().decode('latin-1').replace('\r\n', '\n')
    lines = []
    for l in txt.split('\n'):
        if l.lower().startswith('image'):
            l = 'image "skill9_%s.dds"' % job
        if l.lower().startswith('version'):
            assert l.split()[1] == '1.0', (key, l)
        lines.append(l)
    dst = os.path.join(GEN, key.replace('d:/', 'd_/', 1))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, 'wb').write('\r\n'.join(lines).encode('latin-1'))
    files[key] = dst
for job, rel in ATLAS.items():
    src = os.path.join(AMERIA, rel)
    b = open(src, 'rb').read(128)
    h, w = __import__('struct').unpack_from('<II', b, 12)
    assert b[:4] == b'DDS ' and w == 256 and h >= (288 if job != 'common' else 448), (rel, w, h)
    files['d:/ymir work/ui/skill9_%s.dds' % job] = src

add = {}
for k, src in files.items():
    if k in OURS:
        continue
    if k.endswith('.gr2'):
        assert open(src, 'rb').read(4) != GR2_64, ('64-bit gr2, exe 2.0.25 cannot read it', k)
    add[k] = src
for k in motions['176'] + motions['182']:
    assert k in add or k in OURS, ('motion not found', k)
for v, names in motions.items():
    for k in names:
        assert k in add or k in OURS, ('motion not found', v, k)

if os.path.isdir(STAGING):
    shutil.rmtree(STAGING)
packs = {}
cur, size, n = {}, 0, 1
for k in sorted(add):
    s = os.path.getsize(add[k])
    if cur and size + s > SPLIT:
        packs[PACK if n == 1 else '%s%d' % (PACK, n)] = cur
        cur, size, n = {}, 0, n + 1
    cur[k] = add[k]
    size += s
if cur:
    packs[PACK if n == 1 else '%s%d' % (PACK, n)] = cur

manifest = dict(new_packs=list(packs), packs={}, motions=motions,
                unresolved=sorted(k for k in unresolved if not k.endswith('.psd')),
                already_ours=sorted(ours_hit))
for p in packs:
    ents = []
    for k in sorted(packs[p]):
        assert k == k.lower() and '\\' not in k and len(k.encode('cp1252')) < 161, k
        src = packs[p][k]
        dst = os.path.join(STAGING, 'add', p, k.replace('d:/', 'd_/', 1))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst)
        b = open(src, 'rb').read()
        where = 'gf' if src.startswith(gfres.G) else 'ameria' if src.startswith(AMERIA) else 'gen' if src.startswith(GEN) else src
        ents.append(dict(name=k, source=where, size=len(b), sha1=hashlib.sha1(b).hexdigest()))
    manifest['packs'][p] = ents
json.dump(manifest, open(os.path.join(HERE, 'yskill9_manifest.json'), 'w', encoding='utf-8'), indent=1,
          sort_keys=True, ensure_ascii=False)
for p in packs:
    print('%-9s %4d files %6.2f MB' % (p, len(packs[p]), sum(os.path.getsize(v) for v in packs[p].values()) / 1e6))
print('from ameria:', len(from_ameria), 'already ours:', len(ours_hit))
print('unresolved:', manifest['unresolved'])
