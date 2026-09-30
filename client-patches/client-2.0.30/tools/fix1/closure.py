# Client 2.0.31 fix: the full reference closure of every file in the Arezzo packs, with the three kinds of
# references the phase 1/5-8 verifiers did not follow:
#   .spt  - the exe loads GetPath(spt) + NoPath(NoExtension(name)) + ".dds" for the branch (tag 2000), composite
#           (20002) and self-shadow (17749) textures; the leaf/frond .tga names are not loaded;
#   .mde  - binary EffectData with full texture paths ("D:\ymir work\...\x.dds", spaces inside);
#   .gr2  - BitKnit-compressed (gr2dec: compression 4): texture names unreadable, so every .dds/.tga next to the
#           model in the Arezzo tree is taken.
# Output fix1/add.json: key -> source for every referenced file no pack of ours has.
import sys, os, re, json, struct, subprocess, tempfile, collections
sys.path.insert(0, '/opt/metin2/cache/tcm/tz'); sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
import m2pack, gfres
BASE = sys.argv[1] if len(sys.argv) > 1 else '/opt/metin2/cache/tcm/c30/pack'
H = '/opt/metin2/cache/arezzo-work/client/fix1'
PACK = {}
for p in sorted(f[:-6] for f in os.listdir(BASE) if f.endswith('.index')):
    f, v, ents = m2pack.read_index(BASE + '/%s.index' % p); data = open(BASE + '/%s.data' % p, 'rb').read()
    for e in ents: PACK.setdefault(e['name'], (p, data, e))
PRE = gfres.load_ours('/opt/metin2/cache/tcm/gf28/ourpacks_pre.txt')
GF = gfres.GF
AZ = '/opt/metin2/cache/arezzo/cpack/files/'
def azsrc(k):
    if not k.startswith('d:/ymir work/'): 
        p = AZ + k
    else:
        p = AZ + k[3:]
    return p if os.path.isfile(p) else None
def content(k, src=None):
    if k in PACK:
        p, d, e = PACK[k]; return m2pack.read_entry(d, e)
    return open(src, 'rb').read()
GR2DEC = '/opt/metin2/cache/arezzo-work/client/az58/gr2/gr2dec'
TAGS = {2000: 'branch', 20002: 'composite', 17749: 'shadow'}
def spt_refs(k, b):
    d = k.rsplit('/', 1)[0] + '/'; out = set()
    for tag in TAGS:
        for m in re.finditer(re.escape(struct.pack('<I', tag)), b):
            i = m.end()
            if i + 4 > len(b): continue
            n = struct.unpack('<i', b[i:i + 4])[0]
            if 1 <= n <= 300:
                s = b[i + 4:i + 4 + n]
                if re.search(rb'[A-Za-z]', s) and all(c >= 32 for c in s):
                    base = re.split(r'[\\/]', s.decode('latin1'))[-1]
                    base = base.rsplit('.', 1)[0] if '.' in base else base
                    out.add((d + base + '.dds').lower())
    return out
RE_ABS = re.compile(rb'[A-Za-z]:[\\/][\x20-\x7e]{3,220}?\.(?:dds|tga|jpg|png|bmp|mde|mse|gr2|msa|msf|mss|wav|mp3|spt)(?![A-Za-z0-9])', re.I)
RE_YW = re.compile(rb'ymir work[\\/][\x20-\x7e]{3,220}?\.(?:dds|tga|jpg|png|bmp|mde|mse|gr2|msa|msf|mss|wav|mp3|spt)(?![A-Za-z0-9])', re.I)
def bin_refs(k, b):
    out = set()
    for s in RE_ABS.findall(b) + RE_YW.findall(b):
        s = gfres.norm(s.decode('latin1'))
        if 'ymir work/' in s: out.add('d:/ymir work/' + s.split('ymir work/', 1)[1])
    return out
fail = {}
def refs(k, src):
    b = content(k, src); out = set()
    if k.endswith('.spt'): return spt_refs(k, b)
    if k.endswith('.gr2'):
        fn = tempfile.mktemp(suffix='.gr2'); open(fn, 'wb').write(b)
        r = subprocess.run([GR2DEC, fn], capture_output=True); os.unlink(fn)
        if r.returncode == 0:
            gfres._gr2cache.pop(fn, None)
            fn2 = tempfile.mktemp(suffix='.gr2'); open(fn2, 'wb').write(b)
            out |= gfres.gr2_textures(k, fn2); os.unlink(fn2)
        else:
            fail[k] = r.stderr.decode('latin1').strip()
            a = azsrc(k)
            if a:
                dd = os.path.dirname(a)
                for f in os.listdir(dd):
                    if f.lower().endswith(('.dds', '.tga')):
                        out.add(gfres.norm(k.rsplit('/', 1)[0] + '/' + f))
        return out
    if k.endswith(gfres.TEXT_EXT) or k.endswith('.mde'):
        fn = tempfile.mktemp(); open(fn, 'wb').write(b)
        out |= gfres.refs_of(k, fn); os.unlink(fn)
        out |= bin_refs(k, b)
    return out
seeds = [k for k, v in PACK.items() if v[0].startswith('az_')]
seen = set(); todo = list(seeds); add = {}; unresolved = collections.defaultdict(set)
parent = {}
while todo:
    k = todo.pop()
    if k in seen or k.endswith('.psd'): continue
    seen.add(k)
    src = None
    if k in PACK: pass
    elif k in PRE: continue
    else:
        src = GF.get(k) or azsrc(k)
        if not src:
            unresolved[k].add(parent.get(k, '?')); continue
        add[k] = src
    try:
        for r in refs(k, src):
            if r not in seen:
                parent.setdefault(r, k); todo.append(r)
    except Exception as e:
        fail[k] = 'refs: %s' % e
tot = sum(os.path.getsize(s) for s in add.values())
json.dump({'add': add, 'unresolved': {k: sorted(v) for k, v in unresolved.items()}, 'gr2fail': fail,
           'parent': {k: parent.get(k) for k in add}}, open(H + '/closure.json', 'w'), indent=1)
by = collections.Counter(); bysz = collections.Counter()
for k, s in add.items():
    top = '/'.join(k.split('/')[:5]); by[top] += 1; bysz[top] += os.path.getsize(s)
for t, n in sorted(by.items(), key=lambda x: -bysz[x[0]]): print('%5d %8.1f KB %s' % (n, bysz[t] / 1024, t))
print('ADD', len(add), '%.1f MB' % (tot / 1048576), 'unresolved', len(unresolved), 'gr2fail', len(fail))
