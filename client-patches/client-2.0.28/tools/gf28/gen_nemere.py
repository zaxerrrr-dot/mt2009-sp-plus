import sys, glob, collections; sys.path.insert(0, '/w/attr'); from srvattr import *
W, H, g = grid_from_client('/g/metin2_map_n_snow_dungeon_01', 4, 3)
write_server('/w/attr/server_attr.nemere', W, H, g)
w, h, secs = read_server('/w/attr/server_attr.nemere'); W2, H2, g2 = grid_from_server(w, h, secs)
assert (W2, H2) == (W, H) and g2 == g
print('server_attr', w, 'x', h, 'sectrees', collections.Counter(g).most_common())
pts = {'entry': (171, 270), 'lion': (172, 261), 'r2': (422, 261), 'r3': (764, 264), 'r4': (175, 535), 'r5': (422, 538),
       'r6': (748, 540), 'r7': (305, 708), 'r8': (571, 701), 'r9': (851, 693), 'r10': (927, 395),
       's1': (449, 488), 's2': (455, 445), 's3': (419, 422), 's4': (382, 444), 's5': (389, 488), 'metin6': (747, 494),
       'z1': (302, 678), 'z2': (281, 657), 'z3': (303, 635), 'z4': (324, 656), 'pillar': (849, 660), 'boss': (927, 333)}
for f in sorted(glob.glob('/d/*.txt')):
    for i, l in enumerate(open(f, errors='replace')):
        t = l.split()
        if len(t) > 3 and t[0] in ('r', 'g', 'm') : pts['%s:%d' % (f.split('/')[-1], i + 1)] = (int(t[1]), int(t[2]))
bad = []
for n, (x, y) in pts.items():
    v = g[(y * 2) * W + x * 2]
    free9 = sum(1 for dx in range(-4, 5) for dy in range(-4, 5) if not g[(y * 2 + dy) * W + x * 2 + dx] & 1)
    if v & 1 or free9 < 60: bad.append((n, x, y, v, free9))
print('points', len(pts), 'blocked/tight', bad)
