# Reference check over the extracted output packs (MT2009 2.0.28 GF import)
import os, sys, collections, gfres
S = '/tmp/claude-0/-root/9f475014-d1bc-4cf4-a3e1-da3c380fc52c/scratchpad/new'
ALL = {}
for pack in os.listdir(S):
    base = os.path.join(S, pack)
    for dp, dn, fn in os.walk(base):
        for f in fn:
            p = os.path.join(dp, f); k = gfres.norm(os.path.relpath(p, base).replace('d_/', 'd:/', 1))
            ALL.setdefault(k, (pack, p))
BASE = gfres.load_ours('/opt/metin2/cache/tcm/gf28/ourpacks_pre.txt')
def has(k): return k in ALL
def hasb(k): return k in ALL or k in BASE
# 1. every reference of every text file in the packs we built/extended
CHECK = sys.argv[1:] or ['gf_razador', 'gf_nemere', 'gf_misc', 'ochao', 'goblin']
miss = collections.defaultdict(set)
for k, (pack, p) in ALL.items():
    if pack not in CHECK: continue
    for r in gfres.refs_of(k, p):
        if r.endswith('.psd'): continue
        if not hasb(r): miss[r].add(k)
print('== unresolved references from', CHECK)
for r in sorted(miss): print('  ', r, '<-', sorted(miss[r])[:2], 'GF' if r in gfres.GF else 'notGF')
# 2. npclist races -> msm (exe order: guild npc npc2 npc_pet npc_mount monster monster2 #season1/npc #season2/npc #season1/monster #season2/monster)
PATHS = ['d:/ymir work/%s/' % x for x in ('guild', 'npc', 'npc2', 'npc_pet', 'npc_mount', 'monster', 'monster2')]
SPATHS = ['season1/npc/', 'season2/npc/', 'season1/monster/', 'season2/monster/']
npl = open(os.path.join(S, 'gamedata/gamedata/npclist.txt'), 'rb').read().decode('latin1').replace('\r', '').split('\n')
alias = {}; races = {}
for l in npl:
    t = l.split('\t')
    if len(t) >= 2 and t[0].strip().isdigit():
        v = int(t[0]); n = t[1].strip()
        if v == 0 and len(t) >= 3: alias[n.lower()] = t[2].strip().lower()
        elif v: races.setdefault(v, n)
def resolve(name):
    if name.startswith('#'):
        d = gfres.norm(name[1:]); return (d + 'shape.msm') if has(d + 'shape.msm') else None, d
    n = name.lower(); src = alias.get(n, n)
    for P in PATHS:
        k = P + src + '/' + n + '.msm'
        if has(k): return k, P + src + '/'
    for P in SPATHS:
        k = P + src + '/shape.msm'
        if has(k): return k, P + src + '/'
    return None, None
TARGET = [6001, 6002, 6003, 6004, 6005, 6006, 6007, 6008, 6009, 6051, 6091, 6101, 6102, 6103, 6104, 6105, 6106, 6107, 6108,
          6109, 6151, 6191, 8057, 8058, 20385, 20387, 20388, 20397, 20398, 20399, 6301, 6302, 6303, 6304, 6305, 6311, 6390,
          6400, 20415, 20426, 20856, 20857, 3005, 3104, 3401, 3501, 3552, 20386]
print('== races')
bad = 0
for v in TARGET:
    msm, d = resolve(races[v])
    if not msm:
        print('  %d %s -> NO MSM IN OUR PACKS' % (v, races[v])); bad += 1; continue
    probs = []
    refs = gfres.refs_of(msm, ALL[msm][1])
    ml = d + 'motlist.txt'
    if not has(ml): probs.append('no motlist')
    else:
        for r in gfres.refs_of(ml, ALL[ml][1]):
            if not has(r): probs.append('motion ' + r)
            else: refs |= gfres.refs_of(r, ALL[r][1])
    for r in refs:
        if not hasb(r) and not r.endswith('.psd'): probs.append(r)
    print('  %d %-22s %-58s %s %s' % (v, races[v], msm, ALL[msm][0], ('MISSING: ' + ', '.join(sorted(set(probs)))) if probs else 'ok'))
    bad += bool(probs)
print('races with problems:', bad)
