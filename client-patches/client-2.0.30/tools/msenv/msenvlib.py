# -*- coding: utf-8 -*-
# MT2009_PLUS_MAP_ENVIRONMENT_V1 - shared part of build_msenv_pack.py / verify_msenv.py: how exe 2.0.25 (our
# metin2client.exe, source cache/client-build "Source Client") finds and reads a map's environment, run over a whole pack
# set.
#
# The exe, on every warp (game.py Close() -> background.Destroy() wipes every registered environment first):
#   CMapManager::LoadMap -> CMapOutdoor::Load (GameLib/MapOutdoorLoad.cpp) -> LoadSetting(<dir>\Setting.txt) keeps the
#   first token of "Environment" (m_settings_envDataName); then LOCAL_ENVIRONMENT_DATA:
#     <dir>\<name> when a pack has it (dir = GetMapDataDirectory(): "maps/<atlas name>", or a copied map's
#     ParentMapName), else "d:/ymir work/environment/<name>" (an empty name: the map name's last 2 characters + ".msenv")
#   -> CMapManager::RegisterEnvironmentData(0, that) -> Environment_Load (GameLib/MapUtil.cpp) -> CTextFileLoader::Load
#   (EterLib/TextFileLoader.cpp): false when no pack has the file or LoadGroup ends with an open group (a "{" without
#   its "}", or a key with no value inside a group - LoadGroup breaks out of the group there).
#   A failed register leaves environment slot 0 empty (it was wiped), SetEnvironmentData(0) sets nothing, the map's
#   mc_pEnvironmentData stays NULL and CMapOutdoor::RenderBeforeLensFlare (GameLib/MapOutdoorRender.cpp) writes
#   "mc_pEnvironmentData is NULL" to syserr every frame (~60 lines a second) - no sky, fog, lights or screen filter.
#   Fog: the exe reads Group Fog Enable/IsDensity/NearDistance/FarDistance/Color - GF's later "foglevel N" is not read
#   (the fog then stays at Environment_Init's 12800/17920).
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ENVROOT = 'd:/ymir work/environment/'
GF_ENV = '/opt/metin2/cache/gf/Gameforge_26.1.11/_client/d_/ymir work/environment/'
AMERIA_ENV = '/opt/metin2/ameria/ameria-prj-2025/tools/FoxFSArchiver/source/etc/ymir work/environment/'
ENV_DIR = os.path.join(HERE, 'env')      # converted environments this tool ships (committed)
PACK = 'ymsenv'


def norm(n):
    return n.replace('\\', '/').lower()


class View(object):
    """the client's pack set: pack/Index (OUT's if an earlier step wrote one, else BASE's), each listed pack from OUT
    if it is there, else from BASE; a name belongs to the FIRST listed pack holding it (EterPackManager). skip: packs
    left out (the pack this tool writes, when the builder measures what is needed without it)."""

    def __init__(self, out, base=None, skip=()):
        import m2pack
        self.m2pack = m2pack
        dirs = [d for d in (out, base) if d]
        ix = None
        for d in dirs:
            if os.path.exists(os.path.join(d, 'Index')):
                ix = os.path.join(d, 'Index')
                break
        if ix is None:
            raise SystemExit('no pack/Index in %s' % dirs)
        lines = [l.strip() for l in open(ix, 'rb').read().decode('latin-1').replace('\r', '').split('\n')]
        if lines[0] != 'PACK':
            raise SystemExit('%s: the first line is not PACK' % ix)
        self.index_path = ix
        self.packs = [lines[i + 1] for i in range(1, len(lines) - 1, 2) if lines[i + 1]]
        self.where, self.missing, self.dirs = {}, [], {}
        for p in self.packs:
            if p in skip:
                continue
            d = next((d for d in dirs if os.path.exists(os.path.join(d, p + '.index'))), None)
            if d is None:
                self.missing.append(p)        # the base client's own packs (zone_*, map_* ...): not on vps1
                continue
            self.dirs[p] = d
            for e in m2pack.read_index(os.path.join(d, p + '.index'))[2]:
                self.where.setdefault(e['name'], (p, e))
        self._data = {}

    def has(self, n):
        return n in self.where

    def pack_of(self, n):
        return self.where[n][0] if n in self.where else None

    def get(self, n):
        if n not in self.where:
            return None
        p, e = self.where[n]
        if p not in self._data:
            self._data[p] = open(os.path.join(self.dirs[p], p + '.data'), 'rb').read()
        return self.m2pack.read_entry(self._data[p], e)


def tokens_setting(b):
    """CTokenVectorMap of LoadMultipleTextData: lower-cased key -> its tokens"""
    out = {}
    for l in b.decode('latin-1').replace('\r', '\n').split('\n'):
        t = split_line(l)[1]
        if t:
            out[t[0].lower()] = t[1:]
    return out


def split_line(l):
    """CMemoryTextFileLoader::SplitLine2 (delimiters space/tab, "quoted" tokens): (0 | -1 empty | -2 open quote, tokens)"""
    toks, pos, n = [], 0, len(l)
    while True:
        while pos < n and l[pos] in ' \t':
            pos += 1
        if pos >= n:
            return (0 if toks else -1), toks
        if l[pos] == '"':
            e = l.find('"', pos + 1)
            if e < 0:
                return -2, toks
            toks.append(l[pos + 1:e])
            pos = e + 1
        else:
            e = pos
            while e < n and l[e] not in ' \t':
                e += 1
            toks.append(l[pos:e])
            pos = e


def bind_lines(b):
    """CMemoryTextFileLoader::Bind: \\r, \\n or a pair of them end a line; a byte >= 0x80 takes the next one with it"""
    lines, cur, i, n = [], bytearray(), 0, len(b)
    while i < n:
        c = b[i]
        i += 1
        if c in (10, 13):
            if i < n and b[i] in (10, 13):
                i += 1
            lines.append(bytes(cur))
            cur = bytearray()
        elif c >= 0x80:
            cur += b[i - 1:i + 1]
            i += 1
        else:
            cur.append(c)
    lines.append(bytes(cur))
    return [l.decode('latin-1') for l in lines]


def text_load(b):
    """CTextFileLoader::Load/LoadGroup: (loaded, tree, problems). tree: {key: tokens, '#': {group: tree}}"""
    lines = bind_lines(b)
    pos = [0]
    probs = []

    def group(node):
        depth = 0
        while pos[0] < len(lines):
            r, t = split_line(lines[pos[0]])
            if r != 0:
                if r == -2:
                    probs.append('line %d: no closing "' % (pos[0] + 1))
                pos[0] += 1
                continue
            t[0] = t[0].lower()
            if t[0][0] == '{':
                depth += 1
                pos[0] += 1
                continue
            if t[0][0] == '}':
                depth -= 1
                break
            if t[0] == 'group':
                if len(t) != 2:
                    pos[0] += 1
                    continue
                ch = {}
                node.setdefault('#', {})[t[1].lower()] = ch
                pos[0] += 1
                if not group(ch):
                    return False
            elif t[0] == 'list':
                key = t[1].lower() if len(t) > 1 else ''
                vals = []
                pos[0] += 1
                while pos[0] < len(lines):
                    r, s = split_line(lines[pos[0]])
                    if r == 0 and s[0][0] == '}':
                        break
                    if r == 0 and s[0][0] != '{':
                        vals += s
                    pos[0] += 1
                node[key] = vals
            else:
                if len(t) == 1:
                    probs.append('line %d: key "%s" without a value (LoadGroup leaves the group)' % (pos[0] + 1, t[0]))
                    break
                node[t[0]] = t[1:]
            pos[0] += 1
        return depth == 0

    tree = {}
    ok = group(tree)
    return ok, tree, probs


def map_folders(view):
    """every map the client can load: the atlasinfo rows (CMapManager::__LoadMapInfoVector) and every maps/<x>/setting.txt
    of our packs -> {atlas name: 'atlas' | 'folder'}"""
    out = {}
    for n in sorted(view.where):
        if n.endswith('atlasinfo.txt'):
            for l in (view.get(n) or b'').decode('latin-1').replace('\r', '\n').split('\n'):
                t = l.split()
                if t:
                    out[t[0].lower()] = 'atlas'
    for n in view.where:
        if n.startswith('maps/') and n.endswith('/setting.txt'):
            out.setdefault(n[5:-12], 'folder')
    return out


def resolve(view, name):
    """the map's environment as the exe finds it: dict(state=..., ...). state: 'base' (setting.txt in no pack of ours -
    the base client's map), 'nosetting-copy' (a copied map's parent folder has no Setting.txt), or 'ok' with
    env (the name in setting.txt), path (the file the exe loads), local (whether it is the map folder's copy)"""
    mp = 'maps/%s' % name
    prop = view.get(mp + '/mapproperty.txt')
    ddir = mp
    if prop is not None:
        par = tokens_setting(prop).get('parentmapname')
        if par:
            ddir = norm(par[0])
    st = view.get(ddir + '/setting.txt')
    if st is None:
        if ddir != mp:
            return dict(state='nosetting-copy', dir=ddir)
        return dict(state='base')
    tv = tokens_setting(st)
    env = tv.get('environment', [''])[0] if tv.get('environment') else ''
    local = norm(ddir + '/' + env)
    if env and view.has(local):
        return dict(state='ok', env=env, path=local, local=True, dir=ddir)
    path = norm(ENVROOT + env) if env else ENVROOT + name[-2:] + '.msenv'
    return dict(state='ok', env=env, path=path, local=False, dir=ddir)


def check_env(b):
    """(fatal, fog, tree): fatal - why CTextFileLoader::Load fails (the map then has no environment at all); fog - why
    the exe would not read the file's fog (the map still has an environment)"""
    ok, tree, probs = text_load(b)
    if not ok:
        return ['CTextFileLoader::Load fails (%s)' % ('; '.join(probs) or 'a group is never closed')], [], tree
    out = []
    fog = tree.get('#', {}).get('fog')
    if fog is None:
        out.append('no Group Fog')
    else:
        if 'foglevel' in fog:
            out.append('Fog: "foglevel" (GF) - exe 2.0.25 reads NearDistance/FarDistance only')
        for k in ('neardistance', 'fardistance'):
            if k not in fog:
                out.append('Fog: no %s' % k)
    return [], out, tree


def env_textures(tree):
    """the texture names an environment makes the exe load (skybox faces, cloud, main flare)"""
    out = []
    sky = tree.get('#', {}).get('skybox', {})
    for k in ('frontfacefilename', 'backfacefilename', 'leftfacefilename', 'rightfacefilename', 'topfacefilename',
              'bottomfacefilename', 'cloudtexturefilename'):
        v = sky.get(k)
        if v and v[0]:
            out.append(norm(v[0]))
    lf = tree.get('#', {}).get('lensflare', {})
    if lf.get('mainflaretexturefilename') and lf['mainflaretexturefilename'][0]:
        out.append(norm(lf['mainflaretexturefilename'][0]))
    return out


def crlf(t):
    return t.replace('\r', '').replace('\n', '\r\n')


def source_env(env):
    """the environment file this tool ships for <env>: env/<env> (committed) - made by make_env() from GF's file of
    that name (the maps' own client's) with its "foglevel" turned into the values exe 2.0.25 reads (Ameria's same-named
    file's Enable/NearDistance/FarDistance, else on 5000/25000 as ../ymaps did)"""
    p = os.path.join(ENV_DIR, env.lower())
    if os.path.exists(p):
        return open(p, 'rb').read()
    return None


def make_env(env):
    gf = os.path.join(GF_ENV, env.lower())
    if not os.path.exists(gf):
        hit = [f for f in os.listdir(GF_ENV) if f.lower() == env.lower()]
        if not hit:
            raise SystemExit('%s: in no GF client environment folder' % env)
        gf = os.path.join(GF_ENV, hit[0])
    et = open(gf, 'rb').read().decode('latin-1').replace('\r', '')
    fog = (1, 5000.0, 25000.0)
    am = os.path.join(AMERIA_ENV, env.lower())
    if os.path.exists(am):
        ok, tree, probs = text_load(open(am, 'rb').read())
        f = tree.get('#', {}).get('fog', {})
        if ok and 'neardistance' in f and 'fardistance' in f:
            fog = (int(f.get('enable', ['1'])[0]), float(f['neardistance'][0]), float(f['fardistance'][0]))
    et, n = re.subn(r'(?im)^([ \t]*)foglevel[ \t]+\d+[ \t]*$',
                    lambda m: '%sEnable        %d\n%sNearDistance  %.6f\n%sFarDistance   %.6f' % (
                        m.group(1), fog[0], m.group(1), fog[1], m.group(1), fog[2]), et)
    assert n <= 1, env
    b = crlf(et).encode('latin-1')
    fatal, fog, tree = check_env(b)
    assert not fatal and not fog, (env, fatal, fog)
    return b


def needed(view):
    """{local name: (bytes, map, env)} - a copy in the map folder for every map of our packs whose environment the exe
    cannot load (missing, or not loadable); raises for one this tool cannot repair"""
    out = {}
    for name in sorted(map_folders(view)):
        r = resolve(view, name)
        if r['state'] != 'ok':
            continue
        b = view.get(r['path'])
        if b is not None and not check_env(b)[0]:
            continue                    # loads (its fog is verify_msenv.py's business)
        if not r['env']:
            raise SystemExit('%s: setting.txt names no Environment (the exe would read %s)' % (name, r['path']))
        local = norm(r['dir'] + '/' + r['env'])
        if r['local'] or view.has(local):
            raise SystemExit('%s: its folder\'s own %s does not load (%s) - a copy in a later pack would never be read'
                             % (name, local, check_env(b)[0] if b else 'missing'))
        src = source_env(r['env'])
        if src is None:
            raise SystemExit('%s: environment %s missing - run "build_msenv_pack.py --make %s" (GF -> env/) and '
                             'commit env/%s' % (name, r['path'], r['env'], r['env'].lower()))
        out[local] = (src, name, r['env'])
    return out
