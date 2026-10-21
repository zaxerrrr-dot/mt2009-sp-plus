# -*- coding: utf-8 -*-
# MT2009_PLUS_WORLDBOSS_V1 (client) - Boss Swiata: the six world bosses' models staged for build_yworldboss_packs.py,
# from the GF 26.1.11 client (the races part of ../ymeley/stage_ymeley.py). GF's world bosses are their base boss
# twice the size in a model folder of their own (npclist 4429 w_trent_boss2, 4439 w_cyclops_boss2, 4449
# w_zombie_bigboss2, 4459 w_yellow_tigerman, 4469 w_reddragon_human_boss, 4479 w_ogre_boss2 - our client's npclist
# has these rows already); their men use models our client has (checked: gf_mobs, gf_misc, catacomb_map, gf_razador,
# ymeley_mobs, the ycrack builder, the base client's Hwang Temple monsters).
#
#   python3 stage_yworldboss.py [<staging dir>] [<work dir>]        (host; no lzo needed)
#
# defaults: /opt/metin2/cache/yohara/yworldboss-staging, /opt/metin2/cache/yohara/cape301-work (c58.lst - the client we
# build on). Writes <staging>/add/yworldboss/<in-pack name> ("d:/" as "d_/") and tools/yworldboss/yworldboss_manifest.json:
# every model folder whole plus what it names (textures, motions' sounds, effects and their textures) that neither our
# listing nor an earlier builder has.
import hashlib
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'az58'))
import gfres  # noqa: E402  (indexes the GF client at import)

gfres.GR2DIR = '/opt/metin2/cache/arezzo-work/client/az58/gr2'
gfres.GR2DEC = os.path.join(gfres.GR2DIR, 'gr2dec')

STAGING = sys.argv[1] if len(sys.argv) > 1 else '/opt/metin2/cache/yohara/yworldboss-staging'
WORK = sys.argv[2] if len(sys.argv) > 2 else '/opt/metin2/cache/yohara/cape301-work'
OURS_LST = os.path.join(WORK, 'c58.lst')
PRE_LST = '/opt/metin2/cache/tcm/gf28/ourpacks_pre.txt'
PACK = 'yworldboss'
SPLIT = 26 * 1000 * 1000
GR2_64 = b'\xe5\x9b\x49\x5e'
MODELS = ('w_trent_boss2', 'w_cyclops_boss2', 'w_zombie_bigboss2', 'w_yellow_tigerman', 'w_reddragon_human_boss',
          'w_ogre_boss2')
EARLIER = ('cape301', 'maps302', 'shipdefense', 'port368', 'ymaps', 'ymaps2', 'ymaps3', 'ymaps4', 'ysets', 'ydung4',
           'ypb', 'yiluzja', 'ycrack', 'ycrack2', 'yzaklety', 'yskill9', 'zodiak', 'atlantis', 'ymeley', 'wzmaps')
norm = gfres.norm

OURS = set(gfres.load_ours(PRE_LST))
for l in open(OURS_LST, encoding='utf-8', errors='replace'):
    t = l.rstrip('\n').split(' ', 1)
    if len(t) == 2:
        OURS.add(norm(t[1]))
for d in EARLIER:
    mp = os.path.join(HERE, '..', d, d + '_manifest.json')
    if os.path.exists(mp):
        man = json.load(open(mp, encoding='utf-8'))
        OURS |= set(e['name'] for p in man['packs'].values() for e in p)

add = {}
unresolved = {}
for m in MODELS:
    seed = 'd:/ymir work/monster2/%s/' % m
    assert any(k.startswith(seed) for k in gfres.GF), seed
    # (catacomb_map has w_zombie_bigboss2's two textures already - such names stay ours, the rest is staged)
    assert not any(k.startswith(seed) and k.endswith('.msm') for k in OURS), (m, 'already ours')
    f, u, o = gfres.closure([seed], OURS)
    for k, s in f.items():
        if k not in OURS:
            add[k] = s
    if u:
        unresolved[m] = sorted(u)

# the textures an effect mesh (.mde) or script (.mse) names with a full path (the closure does not read them)
extra_missing = set()
for _ in range(2):
    for k, src in list(add.items()):
        if not k.endswith(('.mde', '.mse')):
            continue
        for mm in re.findall(rb'[A-Za-z]:[\\/][^\x00"\r\n]+?\.(?:dds|tga|png|jpg|mde)', open(src, 'rb').read(), re.I):
            t = 'd:' + mm.decode('latin1').replace('\\', '/').lower()[2:]
            if t in OURS or t in add:
                continue
            if t in gfres.GF:
                add[t] = gfres.GF[t]
            else:
                extra_missing.add(t)

bad64 = sorted(k for k, s in add.items() if k.endswith('.gr2') and open(s, 'rb').read(4) == GR2_64)
if bad64:
    raise SystemExit('64-bit GR2 staged: %s' % bad64)
for k in add:
    assert k == k.lower() and '\\' not in k and len(k.encode('cp1252')) < 161, k
size = sum(os.path.getsize(s) for s in add.values())
assert size < SPLIT, size

shutil.rmtree(STAGING, ignore_errors=True)
ents = []
for k in sorted(add):
    src = add[k]
    dst = os.path.join(STAGING, 'add', PACK, k.replace('d:/', 'd_/', 1))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(src, dst)
    b = open(src, 'rb').read()
    ents.append(dict(name=k, source='gf', size=len(b), sha1=hashlib.sha1(b).hexdigest()))
manifest = {'new_packs': [PACK], 'packs': {PACK: ents}, 'models': list(MODELS),
            'unresolved': {'models': unresolved, 'effects': sorted(extra_missing)}}
json.dump(manifest, open(os.path.join(HERE, 'yworldboss_manifest.json'), 'w', encoding='utf-8'), indent=1,
          sort_keys=True, ensure_ascii=False)
print('%s: %d files %.2f MB' % (PACK, len(ents), size / 1e6))
print('unresolved:', unresolved)
print('unresolved effects:', sorted(extra_missing))
print('gr2 texture decode failures (motions): %d' % len(gfres.GR2_FAIL))
