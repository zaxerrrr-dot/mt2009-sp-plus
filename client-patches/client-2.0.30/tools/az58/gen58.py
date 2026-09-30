# Generated / converted files (MT2009 client 2.0.30, Arezzo phases 5-8) -> ../gen58 + final58.json {add: {pack: {key: src}}}
import os, re, json, shutil
import common58 as c, dxt
shutil.rmtree(c.GEN, ignore_errors=True)
pl = json.load(open(c.HERE + '/plan58.json'))
add = {p: dict(v) for p, v in pl['plan'].items()}
for p in ('maps', 'az_maps2', 'az_maps3'): add.setdefault(p, {})
info = {v['name']: v for v in c.ALLOC['maps'].values()}
MAPPACK = {'metin2_map_pustynia': 'az_maps2'}
for m in c.MAPS:
    st = open(os.path.join(c.A, m, 'setting.txt'), 'rb').read().decode('latin1')
    env = c.norm(re.search(r'Environment\s+(\S+)', st, re.I).group(1))
    src = c.AZ['d:/ymir work/environment/' + env]
    t = open(src, 'rb').read().decode('latin1')
    assert re.search(r'(?im)^\s*NearDistance', t) and re.search(r'(?im)^\s*FarDistance', t) and not re.search(r'(?im)^\s*foglevel', t), env
    add['maps']['maps/%s/%s' % (m, env)] = src          # a copy in the map folder, as for 351/352/Ochao/419/360-363
    w, h = info[m]['size']
    W, H, big = dxt.stitch(os.path.join(c.A, m), w, h)
    side = 512 if max(w, h) >= 4 else 256
    small = dxt.downscale(W, H, big, side, side)
    pack = MAPPACK.get(m, 'az_maps3')
    k = 'd:/ymir work/ui/%s_atlas.dds' % m
    p = os.path.join(c.GEN, k.replace('d:/', 'd_/')); os.makedirs(os.path.dirname(p), exist_ok=True)
    dxt.write_dxt1(p, side, side, small); add[pack][k] = p
    k2 = 'd:/ymir work/ui/atlas/%s/atlas.sub' % m
    add[pack][k2] = c.gen(k2, c.crlf('title subImage\nversion 1.0\nimage "%s_atlas.dds"\nleft 0\ntop 0\nright %d\nbottom %d\n' % (m, side, side)).encode())
for p in add: assert all(os.path.exists(v) for v in add[p].values()), p
json.dump(dict(add=add), open(c.HERE + '/final58.json', 'w'), indent=1, sort_keys=True)
for p in sorted(add):
    print('%-10s add %4d (%5.1f MB)' % (p, len(add[p]), sum(os.path.getsize(v) for v in add[p].values()) / 1e6))
