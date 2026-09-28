# GF client (unpacked) dependency resolver for MT2009 client 2.0.28 asset import
import os, re, sys, json
G = '/opt/metin2/cache/gf/Gameforge_26.1.11/_client'
ROOTS = ('icon/', 'sound/', 'textureset/', 'property/', 'season1/', 'season2/', 'maps/', 'locale/')
EXT = 'gr2|dds|tga|mse|msa|msm|mss|wav|mp3|jpg|bmp|png|txt|msenv|ifl|spt|prb|prd|pre|prt|mde|pra|msf|psd|sub|mdatr|atr|wtr|raw'
RE_Q = re.compile(r'"([^"\r\n]+\.(?:%s))"' % EXT, re.I)
RE_U = re.compile(r'(?:^|[\s,])([^\s"#,]+\.(?:%s))(?=$|[\s,])' % EXT, re.I | re.M)
TEXT_EXT = ('.msm', '.msa', '.mse', '.mss', '.msenv', '.txt', '.prb', '.prd', '.pre', '.prt', '.ifl', '.mde', '.pra', '.msf')

def norm(p):
    p = p.replace('\\', '/').strip().lower()
    while '//' in p: p = p.replace('//', '/')
    return p

MAPDIRS = set()
def build_gf():
    m = {}
    for top in os.listdir(G):
        tp = os.path.join(G, top)
        if not os.path.isdir(tp): continue
        if top == 'd_':
            pref = 'd:/'
        elif top in ('icon', 'sound', 'textureset', 'property', 'season1'):
            pref = top + '/'
        elif os.path.exists(os.path.join(tp, 'setting.txt')) or os.path.exists(os.path.join(tp, 'Setting.txt')):
            pref = 'maps/' + top + '/'; MAPDIRS.add(top.lower())
        else:
            continue
        for dp, dn, fn in os.walk(tp):
            for f in fn:
                ap = os.path.join(dp, f)
                rel = os.path.relpath(ap, tp)
                m[norm(pref + rel)] = ap
    return m

GF = build_gf()

def load_ours(listing):
    s = set()
    for l in open(listing, encoding='utf-8', errors='replace'):
        t = l.rstrip('\n').split(' ', 3)
        if len(t) == 4: s.add(norm(t[3]))
    return s

def refs_of(key, path):
    out = set()
    k = key.lower()
    if not k.endswith(TEXT_EXT): return out
    try: txt = open(path, 'rb').read().decode('latin1')
    except Exception: return out
    cands = set(RE_Q.findall(txt)) | set(RE_U.findall(txt))
    d = key.rsplit('/', 1)[0] + '/'
    for c in cands:
        c = norm(c)
        if c.startswith('d:/') or c.startswith(ROOTS):
            out.add(c)
        elif c.startswith('ymir work/'):
            out.add('d:/' + c)
        else:
            out.add(d + c)
    return out

def sound_of(key):
    # d:/ymir work/monster2/x/walk.msa -> sound/monster2/x/walk.mss
    if key.startswith('d:/ymir work/') and key.endswith(('.msa', '.gr2')):
        return 'sound/' + key[len('d:/ymir work/'):-4] + '.mss'
    return None

def closure(seeds, ours, follow_ours=True):
    """seeds: keys or 'dir/' prefixes. Returns (files dict key->src, unresolved set, already_ours set)."""
    files = {}; unresolved = {}; ours_hit = set(); todo = []
    for s in seeds:
        s = norm(s)
        if s.endswith('/'):
            hit = [k for k in GF if k.startswith(s)]
            if not hit: unresolved[s] = 'seed'
            todo += hit
        else:
            todo.append(s)
    seen = set()
    while todo:
        k = todo.pop()
        if k in seen: continue
        seen.add(k)
        if k.endswith('.psd'): continue
        src = GF.get(k)
        if src is None:
            if k in ours: ours_hit.add(k)
            else: unresolved.setdefault(k, 'ref')
            continue
        if k in ours: ours_hit.add(k)
        files[k] = src
        for r in refs_of(k, src):
            if r not in seen: todo.append(r)
        s = sound_of(k)
        if s and s in GF and s not in seen: todo.append(s)
    return files, unresolved, ours_hit
