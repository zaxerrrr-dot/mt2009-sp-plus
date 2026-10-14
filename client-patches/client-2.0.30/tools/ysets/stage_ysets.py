# -*- coding: utf-8 -*-
# MT2009_PLUS_YOHARA_SETS_V1 - stages every asset the Yohara gear (tools/ysets/yohara_sets.json, made by
# tools/ysets/gen_ysets.py with the server's yohara_sets.sql) needs and our client lacks, from the unpacked GF 26.1.11
# client, and writes ysets_manifest.json (what build_ysets_packs.py packs and patches, what verify_ysets.py checks):
#
#   * the 14 weapon families' models (GF item_list: d:/ymir work/item/weapon/0XXXX.gr2) and their textures - each
#     model under a name of its own, d:/ymir work/item/weapon/ysets_0XXXX.gr2 (the item_list line names it): the base
#     client may hold an older file of GF's name, and the exe's pack dictionary (an unordered multimap) would give
#     either one;
#   * the 8 armour families' bodies for the eight player races (no Lycan): the dragon armours are GF's ShapeIndex 32
#     of every <race>.msm, the serpent ones its ShapeIndex 34 - the model (and its _lod_01.._03, which
#     ActorInstanceData loads by name) as ysets_<model>.gr2 next to GF's, its textures as GF names them; the race's
#     msm gets a ShapeData group with ShapeIndex = the family's base vnum (= the item's value3, server and client),
#     SpecialPath = GF's folder of that race;
#   * the items' icons (GF icon/item/*.tga) our packs lack.
# A texture already in our client (the BASE/OUT packs, the base client's pre-import listing; every race's
# <race>_face.dds is in the base client's pc/pc2 packs) is not staged.
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/ysets/stage_ysets.py <staging dir> <BASE pack dir> [<OUT pack dir>]
#
# <staging>/add/<pack>/<in-pack path> ("d:/" -> "d_/"); ysets_manifest.json next to this file.
import hashlib
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, '/opt/metin2/cache/tcm/gf28')
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
JSON = os.path.join(REPO, 'tools', 'ysets', 'yohara_sets.json')
MANIFEST = os.path.join(HERE, 'ysets_manifest.json')
G = '/opt/metin2/cache/gf/Gameforge_26.1.11/_client'
PRE_LST = '/opt/metin2/cache/tcm/gf28/ourpacks_pre.txt'
RACES = ('warrior_m', 'warrior_w', 'assassin_m', 'assassin_w', 'sura_m', 'sura_w', 'shaman_m', 'shaman_w')
SHAPE = {'da': 32, 'sa': 34}          # GF's ShapeIndex of the dragon / serpent armour bodies
CLASS_OF = {21210: 'warrior', 21230: 'assassin', 21250: 'sura', 21270: 'shaman',
            21310: 'warrior', 21330: 'assassin', 21350: 'sura', 21370: 'shaman'}
PACK_BUDGET = 26 * 1000 * 1000        # raw bytes a pack; the data file stays under 29 MB
PREFIX = 'ysets_'


def norm(p):
    p = p.replace('\\', '/').strip().lower()
    while '//' in p:
        p = p.replace('//', '/')
    return p


def renamed(key):
    d, f = key.rsplit('/', 1)
    return d + '/' + PREFIX + f


def parse_msm(path):
    """GF <race>.msm: (PathName, {ShapeIndex: {Model, SourceSkin, TargetSkin, SpecialPath}})"""
    text = open(path, 'rb').read().decode('cp1250')
    m = re.search(r'Group ShapeData\s*\{\s*PathName\s+"([^"]+)"', text)
    path_name = m.group(1)
    shapes = {}
    for g in re.finditer(r'Group ShapeData\d+\s*\{(.*?)\}', text, re.S):
        kv = {}
        for line in g.group(1).splitlines():
            t = line.split(None, 1)
            if len(t) == 2:
                kv[t[0]] = t[1].strip().strip('"')
        if 'ShapeIndex' in kv:
            shapes[int(kv['ShapeIndex'])] = kv
    return path_name, shapes


def ours_names(dirs):
    import m2pack
    names = set()
    for d in dirs:
        if not d or not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if f.endswith('.index'):
                for e in m2pack.read_index(os.path.join(d, f))[2]:
                    names.add(norm(e['name']))
    for l in open(PRE_LST, encoding='utf-8', errors='replace'):
        t = l.rstrip('\n').split(' ', 3)
        if len(t) == 4:
            names.add(norm(t[3]))
    return names


def main():
    import gfres
    staging, base = sys.argv[1], sys.argv[2]
    out = sys.argv[3] if len(sys.argv) > 3 else None
    d = json.load(open(JSON, encoding='utf-8'))
    ours = ours_names([base, out])
    files = {}            # in-pack name -> (GF source file, source key)
    gf_missing = []

    def want(key, src_key=None, as_name=None):
        src_key = src_key or key
        src = gfres.GF.get(norm(src_key))
        if src is None:
            gf_missing.append(src_key)
            return
        files[norm(as_name or key)] = (src, norm(src_key))

    def textures(model_key):
        for t in sorted(gfres.gr2_textures(model_key, gfres.GF[model_key])):
            if t in ours or t.endswith('_face.dds'):
                continue
            want(t)

    weapons = {}
    for k, kind in sorted(d['families'].items(), key=lambda x: int(x[0])):
        if kind not in ('sw', 'dw'):
            continue
        model = norm(d['item_list'][k].split('\t')[3])
        assert model in gfres.GF, model
        weapons[k] = renamed(model)
        want(model, as_name=renamed(model))
        textures(model)
    msm = {}
    for race in RACES:
        path_name, shapes = parse_msm(os.path.join(G, 'shared', 'common', race + '.msm'))
        cls = race.split('_')[0]
        groups = []
        for k, kind in sorted(d['families'].items(), key=lambda x: int(x[0])):
            if kind not in SHAPE or CLASS_OF[int(k)] != cls:
                continue
            g = shapes[SHAPE[kind]]
            folder = norm(g.get('SpecialPath', path_name)).rstrip('/') + '/'
            model = folder + norm(g['Model'])
            assert model in gfres.GF, model
            want(model, as_name=renamed(model))
            textures(model)
            stem = model[:-4]
            for lod in ('_lod_01', '_lod_02', '_lod_03'):
                if stem + lod + '.gr2' in gfres.GF:
                    want(stem + lod + '.gr2', as_name=renamed(stem + lod + '.gr2'))
            for sk in ('SourceSkin', 'TargetSkin'):
                t = folder + norm(g[sk])
                if t not in ours and not t.endswith('_face.dds'):
                    want(t)
            groups.append(dict(index=int(k), SpecialPath=folder, Model=PREFIX + norm(g['Model']),
                               SourceSkin=norm(g['SourceSkin']), TargetSkin=norm(g['TargetSkin'])))
        msm[race] = groups
    icons = sorted(set(norm(l.split('\t')[2]) for l in d['item_list'].values()))
    for ic in icons:
        if ic not in ours:
            want(ic)
    clash = sorted(n for n in files if n in ours)
    assert not clash, ('a staged name is in our client already', clash)
    assert not gf_missing, ('not in the GF client', gf_missing)

    # packs: models and textures by size into ysets_eq, ysets_eq2, ...; the icons last
    packs, cur, size = [], [], 0
    for n in sorted(files, key=lambda n: (n.startswith('icon/'), n)):
        s = os.path.getsize(files[n][0])
        if cur and size + s > PACK_BUDGET:
            packs.append(cur)
            cur, size = [], 0
        cur.append(n)
        size += s
    if cur:
        packs.append(cur)
    names = ['ysets_eq' + ('' if i == 0 else str(i + 1)) for i in range(len(packs))]
    if os.path.isdir(os.path.join(staging, 'add')):
        shutil.rmtree(os.path.join(staging, 'add'))
    man = {'new_packs': names, 'packs': {}, 'weapon_models': weapons, 'msm': msm, 'icons': icons}
    for pname, members in zip(names, packs):
        rows = []
        for n in members:
            src = files[n][0]
            dst = os.path.join(staging, 'add', pname, n.replace('d:/', 'd_/', 1))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(src, dst)
            b = open(src, 'rb').read()
            rows.append(dict(name=n, size=len(b), sha1=hashlib.sha1(b).hexdigest(), source='gf:' + files[n][1]))
        man['packs'][pname] = rows
    with open(MANIFEST, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(man, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print(json.dumps(dict(packs=dict((p, dict(files=len(r), raw_mb=round(sum(x['size'] for x in r) / 1e6, 2)))
                                     for p, r in man['packs'].items()),
                          weapons=len(weapons), msm_groups=sum(len(g) for g in msm.values()), icons_staged=sum(
                              1 for r in man['packs'].values() for x in r if x['name'].startswith('icon/'))), indent=1))


if __name__ == '__main__':
    main()
