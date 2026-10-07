# -*- coding: utf-8 -*-
# MT2009_PLUS_AREZZO_COSTUME_SETS_V1 - everything the Arezzo costume sets need, read out of the
# unpacked Arezzo client (/opt/metin2/cache/arezzo: cmp/arezzo_item_raw.json = its decoded
# item_proto, cpack/files = its packs unpacked: arezzo/item_list.txt, arezzo/shiningtable.txt,
# the eight *.msm, ymir work/..., icon/...).  Plain Python 3 on the VPS (gr2 texture names through
# /opt/metin2/cache/tcm/gf28/gr2/gr2dec, as the gf28 import).
#
#   python3 build_azcostume.py                 # writes azcostume_items.json next to this file
#   python3 build_azcostume.py --stage <dir>   # + copies every asset our client lacks to
#                                              #   <dir>/add/<pack>/<in-pack path> (d:/... -> d_/...)
#
# azcostume_items.json (tracked) is all the other tools need - patch_azcostume_client.py (the
# client's gamedata / locale files) and gen_azcostume_server.py (apply.sh SQL, costume_sets.txt,
# costume_sets.py) - so they run without the Arezzo files.  Its "assets" list is every file the
# rows name (icons, weapon / back piece models, msm models and skins, the glow effects, and every
# texture / mesh those name in turn) with its size and Arezzo source; "ours" marks the ones our
# client already ships (c55 packs and the base-pack listing tcm/gf28/ourpacks_pre.txt).
#
# Body / hair models: Arezzo's msm has the Chwala and Druid sets (andun_glory, easter2023_1) for
# the male warrior only and the Mandaryn helmet without the male ninja, though the models for
# every class are in its packs; the missing groups are written the same way (the class's
# <race>.gr2 next to the warrior's, its own texture as the skin - the name the gr2 itself holds).
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import azcostume_sets as A  # noqa: E402

AZ = '/opt/metin2/cache/arezzo'
FILES = AZ + '/cpack/files'
GR2DEC = '/opt/metin2/cache/tcm/gf28/gr2/gr2dec'
OURS = ('/opt/metin2/cache/c55/pack', '/opt/metin2/cache/tcm/gf28/ourpacks_pre.txt')
RACES = ('warrior_m', 'assassin_m', 'sura_m', 'shaman_m', 'warrior_w', 'assassin_w', 'sura_w', 'shaman_w')
PACK_BUDGET = 28 * 1000 * 1000
RE_TEX = re.compile(rb'[\x20-\x7e]{1,200}?\.(?:dds|tga|bmp|jpg|png|gr2|mde|mse|msa)(?![A-Za-z0-9])', re.I)
RE_Q = re.compile(r'"([^"\r\n]+\.(?:dds|tga|bmp|jpg|png|gr2|mde|mse|msa|mss|wav))"', re.I)


def norm(p):
    p = p.replace('\\', '/').strip().lower()
    while '//' in p:
        p = p.replace('//', '/')
    if p.startswith('d:ymir'):
        p = 'd:/' + p[2:]
    return p


def az_index():
    idx = {}
    for top, pref in (('ymir work', 'd:/ymir work/'), ('icon', 'icon/')):
        base = os.path.join(FILES, top)
        for dp, dn, fn in os.walk(base):
            for f in fn:
                ap = os.path.join(dp, f)
                idx[norm(pref + os.path.relpath(ap, base))] = ap
    return idx


def our_names():
    names = set()
    sys.path.insert(0, '/opt/metin2/cache/tcm/tz')   # m2pack.py (the old c36 copy is gone)
    try:
        import m2pack  # noqa: F401  (needs python-lzo only for the data; read_index reads the index)
        for f in os.listdir(OURS[0]):
            if f.endswith('.index'):
                for e in m2pack.read_index(os.path.join(OURS[0], f))[2]:
                    names.add(norm(e['name']))
    except Exception as e:  # outside the m2pack-lzo image: a listing written by it
        listing = os.environ.get('AZ_OUR_NAMES')
        if not listing:
            raise SystemExit('cannot read our packs (%s); run in the m2pack-lzo image or set AZ_OUR_NAMES '
                             'to a "pack<TAB>name<TAB>size" listing' % e)
        for l in open(listing, encoding='utf-8', errors='replace'):
            names.add(norm(l.split('\t')[1]))
    for l in open(OURS[1], encoding='utf-8', errors='replace'):
        t = l.rstrip('\n').split(' ', 3)
        if len(t) == 4:
            names.add(norm(t[3]))
    return names


def az_items():
    out = {}
    import struct
    for x in json.load(open(AZ + '/cmp/arezzo_item_raw.json')):
        b = bytes.fromhex(x['raw'])
        if b[70] != 28:
            continue
        out[x['vnum']] = dict(name=b[39:70].split(b'\0')[0].decode('cp1250', 'replace'), sub=b[71], size=b[73],
                              anti=struct.unpack_from('<I', b, 74)[0], val=list(struct.unpack_from('<6i', b, 133)))
    il = {}
    for l in open(FILES + '/arezzo/item_list.txt', encoding='cp1250', errors='replace'):
        p = l.rstrip('\r\n').split('\t')
        if p and p[0].strip().isdigit():
            il[int(p[0])] = [norm(x) for x in p[2:]]
    return out, il


def parse_msm(path):
    t = open(path, encoding='cp1250', errors='replace').read()
    res = {'ShapeData': {}, 'HairData': {}}
    for kind in res:
        top = re.search(r'Group\s+%s\s*\{\s*PathName\s+"([^"]+)"' % kind, t)
        for m in re.finditer(r'Group\s+%s\d+\s*\{(.*?)\}' % kind, t, re.S):
            kv = {}
            for line in m.group(1).splitlines():
                line = line.split('#')[0].strip()
                if not line:
                    continue
                kvm = re.match(r'(\S+)\s+(.*)$', line)
                if kvm:
                    kv[kvm.group(1)] = kvm.group(2).strip().strip('"')
            key = 'ShapeIndex' if kind == 'ShapeData' else 'HairIndex'
            if 'SpecialPath' not in kv and top:
                kv['SpecialPath'] = top.group(1)
            if key in kv:
                res[kind][int(re.match(r'\d+', kv[key]).group(0))] = kv
    return res


_gr2 = {}
CLASS_TAGS = {'warrior': ('w', 'wa'), 'assassin': ('as', 'a'), 'sura': ('su',), 'shaman': ('sh',)}


def guess_skin(special, model, race):
    cls, sex = race.split('_')
    sub = model.rsplit('/', 1)[0] + '/' if '/' in model else ''
    folder = norm(special.rstrip('/') + '/' + sub)
    for tag in CLASS_TAGS[cls]:
        for name in ('plechito_tex_%s_%s.dds' % (sex, tag), 'plechito_tex_%s.dds' % sex):
            if folder + name in IDX:
                return sub + name
    return None


IDX = {}


def fix_skin(g, race, kind):
    """Arezzo's msm names some skins its packs do not have (the Krwawa Zemsta and the two Smok
    helmets, the Joker's female costume): a skin that is not there is replaced by the texture of
    that folder the class / sex uses (body_<m|f><class>.dds, hair_<m|f>.dds, plechito_tex_...),
    or left out (the model's own texture)."""
    folder = norm(g['SpecialPath'].rstrip('/') + '/')
    if folder + norm(g.get('SourceSkin', '')) in IDX and folder + norm(g.get('TargetSkin', '')) in IDX:
        return g
    cls, sex = race.split('_')
    fs = 'm' if sex == 'm' else 'f'
    sub = g['Model'].rsplit('/', 1)[0] + '/' if '/' in g['Model'] else ''
    tags = {'warrior': 'wa', 'assassin': 'as', 'sura': 'su', 'shaman': 'sh'}[cls]
    names = (['hair_%s.dds' % fs] if kind == 'HairData' else []) + [
        'body_%s%s.dds' % (fs, tags), 'body_%s_%s.dds' % (fs, tags), 'body_%s.dds' % fs] + [
        'plechito_tex_%s_%s.dds' % (sex, t) for t in CLASS_TAGS[cls]] + ['plechito_tex_%s.dds' % sex]
    g = dict(g)
    for n in names:
        for p in (sub + n, n):
            if folder + p in IDX:
                g['SourceSkin'] = g['TargetSkin'] = p
                return g
    g.pop('SourceSkin', None)
    g.pop('TargetSkin', None)
    return g


def gr2_refs(path):
    """Texture names a .gr2 holds; None when gr2dec cannot read it (BitKnit, compression 4)."""
    if path not in _gr2:
        r = subprocess.run([GR2DEC, path], capture_output=True)
        ok = r.returncode == 0 and b'unsupported' not in r.stderr and b'unsupported' not in r.stdout
        _gr2[path] = sorted(set(norm(x.decode('latin1')) for x in RE_TEX.findall(r.stdout))) if ok else None
    return _gr2[path]


def file_refs(key, path):
    """Files a model / effect names, as in-pack keys (a bare name sits next to the file)."""
    d = key.rsplit('/', 1)[0] + '/'
    if key.endswith('.gr2'):
        raw = gr2_refs(path)
        if raw is None:   # unreadable: every texture next to it (the model's skins live there)
            folder = os.path.dirname(path)
            return [d + f.lower() for f in sorted(os.listdir(folder)) if f.lower().endswith('.dds')]
    elif key.endswith(('.mse', '.msa', '.mss')):
        raw = [norm(x) for x in RE_Q.findall(open(path, encoding='cp1250', errors='replace').read())]
    elif key.endswith('.mde'):
        raw = [norm(x.decode('latin1')) for x in RE_TEX.findall(open(path, 'rb').read())]
    else:
        return []
    out = []
    for t in raw:
        if ':' in t[:3]:
            t = 'd:/' + t.split(':', 1)[1].lstrip('/')
        if t.startswith('d:/'):
            out.append(t)
        elif 'ymir work/' in t:
            out.append('d:/ymir work/' + t.split('ymir work/', 1)[1])
        elif key.endswith('.gr2'):
            out.append(d + t.rsplit('/', 1)[-1])   # an artist's own path: the skin sits next to the model
        else:
            # MT2009_PLUS_AREZZO_COSTUME_SETS_V3: an effect's relative name keeps its folder
            # ("smoke\smoke_1_01.dds" next to the .mse is <folder>/smoke/smoke_1_01.dds)
            out.append(d + t.lstrip('./'))
    return out


def main():
    stage = sys.argv[sys.argv.index('--stage') + 1] if '--stage' in sys.argv else None
    idx = az_index()
    IDX.update(idx)
    items, il = az_items()
    msm = dict((r, parse_msm(os.path.join(FILES, r + '.msm'))) for r in RACES)
    shining = {}
    for l in open(FILES + '/arezzo/shiningtable.txt', encoding='cp1250', errors='replace'):
        p = [x for x in l.strip().split('\t') if x]
        if len(p) >= 2 and p[0].isdigit():
            shining.setdefault(int(p[0]), [])
            for f in p[1:]:
                f = norm(f.strip().strip('"'))
                if f not in shining[int(p[0])]:
                    shining[int(p[0])].append(f)
    need = {}

    def want(key, why):
        need.setdefault(norm(key), set()).add(why)

    def msm_group(kind, race, az_idx, sibling_idx):
        """The msm group of Arezzo index az_idx for this race, or one written after another class's
        (or the other sex's) group of the same look: the race's own <race>.gr2 in that folder."""
        g = msm[race][kind].get(az_idx)
        if g is not None:
            return {k: g[k] for k in ('SpecialPath', 'Model', 'SourceSkin', 'TargetSkin') if k in g}, False
        for i in (az_idx, sibling_idx):
            for tr in RACES:
                tmpl = msm[tr][kind].get(i)
                if tmpl is None or tr not in tmpl['Model']:
                    continue
                model = tmpl['Model'].replace(tr, race)
                path = norm(tmpl['SpecialPath'].rstrip('/') + '/' + model)
                if path not in idx:
                    continue
                tex = [t for t in (gr2_refs(idx[path]) or []) if t.endswith('.dds')]
                if tex:
                    skin = tex[0].rsplit('/', 1)[-1]
                else:     # gr2dec cannot read it: the folder's naming, plechito_tex_<sex>_<class>.dds
                    skin = guess_skin(tmpl['SpecialPath'], model, race)
                    if not skin:
                        continue
                sub = model.rsplit('/', 1)[0] + '/' if '/' in model else ''
                if norm(tmpl['SpecialPath'].rstrip('/') + '/' + sub + skin) not in idx:
                    sub = ''
                return {'SpecialPath': tmpl['SpecialPath'], 'Model': model, 'SourceSkin': sub + skin,
                        'TargetSkin': sub + skin}, True
        return None, False

    rows, sets, made_groups, problems = [], [], [], []
    for key, set_name, word, bodies, hairs, hair_word, first_weapon, back in A.SETS:
        adj = word.endswith(('y', 'i')) and ' ' not in word and '.' not in word
        srow = dict(key=key, name=set_name, bodies=[], hairs=[], weapons=[], skin=0)
        for kind, arez, base_word in (('ShapeData', bodies, u'Kostium'), ('HairData', hairs, hair_word)):
            for sex_i, av in enumerate(arez):
                it = items[av]
                sex = ('m', 'k')[sex_i]
                vnum = av + A.BODY_SHIFT if kind == 'ShapeData' else av
                az_idx = it['val'][3]
                groups = {}
                for race in RACES:
                    if not race.endswith('_' + ('m', 'w')[sex_i]):
                        continue
                    g, made = msm_group(kind, race, az_idx, items[arez[1 - sex_i]]['val'][3])
                    if g is None:
                        problems.append('%s %d: no %s group for %s' % (key, av, kind, race))
                        continue
                    g = fix_skin(g, race, kind)
                    if made:
                        made_groups.append('%s %d %s' % (key, vnum, race))
                    groups[race] = g
                    for f in [x for x in ('Model', 'SourceSkin', 'TargetSkin') if x in g]:
                        want(g['SpecialPath'].rstrip('/') + '/' + g[f], 'msm %d %s' % (vnum, race))
                icon = il[av][0]
                want(icon, 'icon %d' % vnum)
                name = u'%s %s (%s)' % (base_word, word, sex)
                anti = A.ANTI_BASE | (A.ANTI_FEMALE if sex == 'm' else A.ANTI_MALE)
                rows.append(dict(vnum=vnum, arezzo=av, set=key, name=name, type=28,
                                 sub=0 if kind == 'ShapeData' else 1, size=2 if kind == 'ShapeData' else 1,
                                 anti=anti, values=[5 if kind == 'ShapeData' else 0, 0, 0, vnum, 0, 0],
                                 icon=icon, model='', msm=dict((r, dict(g, Index=vnum)) for r, g in groups.items()),
                                 kind=kind, shining=shining.get(av, [])))
                srow['bodies' if kind == 'ShapeData' else 'hairs'].append(vnum)
        if first_weapon:
            for i in range(6):
                av = first_weapon + i
                it = items[av]
                assert it['val'][3] == i, (av, it['val'])
                icon, model = A.WEAPON_FIX.get(av, (None, None))
                if not icon:
                    icon, model = il[av][0], il[av][1]
                icon, model = norm(icon), norm(model)
                want(icon, 'icon %d' % av)
                want(model, 'model %d' % av)
                kind_word, size, cls = A.WEAPON_KINDS[i]
                w = word
                if adj and kind_word == u'Ostrze':
                    w = word[:-1] + ('e' if word.endswith('y') else 'ie')
                rows.append(dict(vnum=av, arezzo=av, set=key, name=u'%s %s' % (kind_word, w), type=28, sub=4,
                                 size=size, anti=A.ANTI_WEAPON_BASE | cls, values=[0, 0, 0, i, 0, 0], icon=icon,
                                 model=model, msm={}, kind='Weapon', shining=shining.get(av, [])))
                srow['weapons'].append(av)
        if back and back + A.SKIN_SHIFT not in A.REMOVED_ITEMS:   # V4: the me_w wing skins are out
            vnum = back + A.SKIN_SHIFT
            icon, model = il[back][0], il[back][1]
            want(icon, 'icon %d' % vnum)
            want(model, 'model %d' % vnum)
            w = word[:-1] + 'a' if adj else word
            rows.append(dict(vnum=vnum, arezzo=back, set=key, name=u'Szarfa %s (nakł.)' % w, type=3, sub=10,
                             size=1, anti=0, values=[0, 0, 0, 0, 0, 0], icon=icon, model=model, msm={},
                             kind='SashSkin', shining=[]))
            srow['skin'] = vnum
        sets.append(srow)
    for r in rows:
        for f in r['shining']:
            want(f, 'shining %d' % r['vnum'])
        assert len(r['name'].encode('cp1250')) <= 32, r['name']
    # closure: what each wanted file names in turn
    todo = list(need)
    while todo:
        k = todo.pop()
        if k not in idx:
            continue
        for t in file_refs(k, idx[k]):
            if t not in need:
                need[t] = set()
                todo.append(t)
            need[t].add('ref ' + k)
    ours = our_names()
    assets = []
    for k in sorted(need):
        a = dict(key=k, why=sorted(need[k])[:3], ours=k in ours)
        if k in idx:
            a['src'] = os.path.relpath(idx[k], FILES)
            a['size'] = os.path.getsize(idx[k])
        assets.append(a)
    missing = [a['key'] for a in assets if not a['ours'] and 'src' not in a]
    # the new files in packs az_cost01.. of at most PACK_BUDGET bytes each (raw; the per-pack zip
    # limit of the release is 29 MB - LZO hardly shrinks DXT textures), in path order so a set's
    # folders stay together
    packs, cur, size = {}, None, 0
    for a in sorted((a for a in assets if not a['ours'] and 'src' in a), key=lambda a: a['key']):
        if cur is None or size + a['size'] > PACK_BUDGET:
            cur, size = 'az_cost%02d' % (len(packs) + 1), 0
            packs[cur] = []
        packs[cur].append(a['key'])
        a['pack'] = cur
        size += a['size']
    out = dict(marker='MT2009_PLUS_AREZZO_COSTUME_SETS_V1', sets=sets, items=rows, assets=assets, packs=packs,
               msm_written=made_groups, problems=problems, missing=missing)
    with open(os.path.join(HERE, 'azcostume_items.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1, sort_keys=True)
    new = [a for a in assets if not a['ours'] and 'src' in a]
    print('sets %d, items %d (bodies %d, hairs %d, weapon skins %d, sash skins %d)' % (
        len(sets), len(rows), sum(r['kind'] == 'ShapeData' for r in rows), sum(r['kind'] == 'HairData' for r in rows),
        sum(r['kind'] == 'Weapon' for r in rows), sum(r['kind'] == 'SashSkin' for r in rows)))
    print('assets %d: in our client %d, new %d (%.1f MB), missing everywhere %d; msm groups written %d; problems %d' % (
        len(assets), sum(a['ours'] for a in assets), len(new), sum(a['size'] for a in new) / 1e6, len(missing),
        len(made_groups), len(problems)))
    for p in problems:
        print('  problem:', p)
    if stage:
        for a in new:   # hard links where the file system allows (no second copy on a full disk)
            dst = os.path.join(stage, 'add', a['pack'], a['key'].replace('d:/', 'd_/', 1))
            if not os.path.exists(dst) or os.path.getsize(dst) != a['size']:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                if os.path.exists(dst):
                    os.remove(dst)
                try:
                    os.link(os.path.join(FILES, a['src']), dst)
                except OSError:
                    shutil.copyfile(os.path.join(FILES, a['src']), dst)
        print('staged %d files under %s/add/<pack>/ (%s)' % (len(new), stage, ', '.join(
            '%s %d files %.1f MB' % (p, len(k), sum(x['size'] for x in new if x['pack'] == p) / 1e6) for p, k in packs.items())))


if __name__ == '__main__':
    main()
