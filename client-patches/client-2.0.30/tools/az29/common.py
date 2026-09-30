# MT2009 client 2.0.30 - Arezzo phase 1 import (maps 360 metin2_map_exp, 362 natural_map, 363 plechito_chamber_of_wisdom)
# Shared indexes: Arezzo client tree (AZ), GF 26.1.11 (GF), our packs (OURS: c28 listings + pre-import base listing),
# our property pack by CRC (OURPROP).
import os, sys, json, zlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gfres
WORK = '/opt/metin2/cache/arezzo-work'
A = '/opt/metin2/cache/arezzo/cpack/files'
SNAP = WORK + '/c28snap'                       # read-only extraction of /opt/metin2/cache/tcm/c28/pack
GEN = WORK + '/client/gen'
ALLOC = json.load(open(WORK + '/data/allocation.json'))
MAPS = ['metin2_map_exp', 'natural_map', 'plechito_chamber_of_wisdom']
norm = gfres.norm
GF = dict(gfres.GF)

def build_az():
    m = {}
    for top in os.listdir(A):
        tp = os.path.join(A, top)
        if not os.path.isdir(tp): continue
        if top == 'ymir work': pref = 'd:/ymir work/'
        elif top in ('icon', 'sound', 'textureset', 'property', 'season1', 'season2', 'locale'): pref = top + '/'
        elif os.path.exists(os.path.join(tp, 'setting.txt')): pref = 'maps/' + top + '/'
        else: pref = top + '/'
        for dp, dn, fn in os.walk(tp):
            for f in fn:
                ap = os.path.join(dp, f)
                m[norm(pref + os.path.relpath(ap, tp))] = ap
    return m
AZ = build_az()

def load_ours():
    s = set(gfres.load_ours('/opt/metin2/cache/tcm/gf28/ourpacks_pre.txt'))
    for f in os.listdir(SNAP):
        if f.endswith('.lst'):
            for l in open(os.path.join(SNAP, f), encoding='utf-8', errors='replace'):
                if l.strip(): s.add(norm(l.rstrip('\n')))
    return s
OURS = load_ours()

def prop_crc(b):
    l = b.replace(b'\r', b'').split(b'\n')
    if l and l[0].strip() == b'YPRT' and len(l) > 1:
        try: return int(l[1].strip())
        except ValueError: return None
    return None
def prop_body(b): return b.replace(b'\r', b'').split(b'\n')[2:]

def prop_index_dir(root, pref):
    idx = {}
    for dp, dn, fn in os.walk(root):
        for f in fn:
            p = os.path.join(dp, f)
            c = prop_crc(open(p, 'rb').read())
            if c is not None: idx.setdefault(c, (norm(pref + os.path.relpath(p, root)), p))
    return idx
OURPROP = prop_index_dir(SNAP + '/property/property', 'property/')       # crc -> (key, path)
AZPROP = prop_index_dir(A + '/property', 'property/')

def map_crcs_file(path):
    t = open(path, 'rb').read().decode('latin1').replace('\r', '').split('\n')
    return [int(t[i + 2].strip().split('#')[0]) for i, l in enumerate(t) if l.startswith('Start Object')]
def map_areadata(m):
    out = []
    for dp, dn, fn in os.walk(os.path.join(A, m)):
        for f in fn:
            if f.lower() == 'areadata.txt': out.append(os.path.join(dp, f))
    return sorted(out)
def gen(key, data):
    p = os.path.join(GEN, key.replace('d:/', 'd_/', 1)); os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'wb').write(data); return p
def crlf(s): return s.replace('\r\n', '\n').replace('\n', '\r\n')
