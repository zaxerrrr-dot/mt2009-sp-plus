# Generated / converted files (MT2009 client 2.0.30, Arezzo phase 1) -> ../gen + final.json {add: {pack: {key: src}}}
import os, re, json, shutil
import common as c, dxt
shutil.rmtree(c.GEN + '/maps', ignore_errors=True); shutil.rmtree(c.GEN + '/d_', ignore_errors=True)
pl = json.load(open(c.HERE + '/plan.json'))
add = {p: dict(v) for p, v in pl['plan'].items()}
for p, v in pl['gens'].items(): add.setdefault(p, {}).update(v)
M = c.ALLOC['maps']
info = {v['name']: v for v in M.values()}
for m in c.MAPS:
    st = open(os.path.join(c.A, m, 'setting.txt'), 'rb').read().decode('latin1')
    env = c.norm(re.search(r'Environment\s+(\S+)', st, re.I).group(1))
    # 1. a copy of the environment in the map folder (as the maps pack keeps for 351/352/Ochao/419)
    src = c.AZ['d:/ymir work/environment/' + env]
    t = open(src, 'rb').read().decode('latin1')
    assert re.search(r'(?im)^\s*NearDistance', t) and re.search(r'(?im)^\s*FarDistance', t) and not re.search(r'(?im)^\s*foglevel', t), env
    add['maps']['maps/%s/%s' % (m, env)] = src
    # 2. big-map atlas from the sectors' minimaps (the GF atlases are exactly that: checked on 351, corr 0.98)
    w, h = info[m]['size']
    W, H, big = dxt.stitch(os.path.join(c.A, m), w, h)
    side = 512 if max(w, h) >= 4 else 256
    small = dxt.downscale(W, H, big, side, side)
    k = 'd:/ymir work/ui/%s_atlas.dds' % m
    p = os.path.join(c.GEN, k.replace('d:/', 'd_/')); os.makedirs(os.path.dirname(p), exist_ok=True)
    dxt.write_dxt1(p, side, side, small); add['az_maps'][k] = p
    k2 = 'd:/ymir work/ui/atlas/%s/atlas.sub' % m
    add['az_maps'][k2] = c.gen(k2, c.crlf('title subImage\nversion 1.0\nimage "%s_atlas.dds"\nleft 0\ntop 0\nright %d\nbottom %d\n' % (m, side, side)).encode())
# 3. natural_map: the leaf-crown effects of the 64-bit trunks out of areadata (plan.py TREE_DROP)
DROP = {2269369239, 3974574155}
n_drop = 0
for f in c.map_areadata('natural_map'):
    rel = os.path.relpath(f, c.A); key = c.norm('maps/' + rel)
    t = open(f, 'rb').read().decode('latin1').replace('\r', '').split('\n')
    out = []; i = 0; objs = []
    head = []
    while i < len(t):
        if t[i].startswith('Start Object'):
            j = i
            while not t[j].startswith('End Object'): j += 1
            blk = t[i:j + 1]; i = j + 1
            if int(blk[2].strip().split('#')[0]) in DROP: n_drop += 1; continue
            objs.append(blk)
        elif t[i].startswith('ObjectCount'):
            i += 1
        else:
            if not objs: head.append(t[i])
            i += 1
    if len(objs) == len(c.map_crcs_file(f)): continue
    body = [x for x in head if x != '' or True]
    lines = [l for l in head]
    while lines and lines[-1] == '': lines.pop()
    lines.append('')
    for n, blk in enumerate(objs):
        lines.append('Start Object%03d' % n); lines += blk[1:]
    lines += ['', 'ObjectCount %d' % len(objs), '']
    add['maps'][key] = c.gen(key, '\r\n'.join(lines).encode('latin1'))
print('natural_map: leaf effects dropped', n_drop)
for p in add: assert all(os.path.exists(v) for v in add[p].values()), p
json.dump(dict(add=add), open(c.HERE + '/final.json', 'w'), indent=1, sort_keys=True)
for p in sorted(add):
    print('%-10s add %4d (%5.1f MB)' % (p, len(add[p]), sum(os.path.getsize(v) for v in add[p].values()) / 1e6))
