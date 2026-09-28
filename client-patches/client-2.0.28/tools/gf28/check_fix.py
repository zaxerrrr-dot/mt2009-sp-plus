# Check dungeon spawn/jump points against server_attr; for Nemere also build fixed regen files.
import sys, os, glob, re, collections
sys.path.insert(0, '/w/attr'); from srvattr import *
def load(path):
    w, h, secs = read_server(path); return grid_from_server(w, h, secs)
def blocked(W, H, g, x, y):  # x,y local units of 100 -> server cells of 50
    cx, cy = x * 2, y * 2
    if not (0 <= cx < W and 0 <= cy < H): return True
    return bool(g[cy * W + cx] & 1)
def freefrac(W, H, g, x, y, r):
    n = f = 0
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            n += 1; f += not blocked(W, H, g, x + dx, y + dy)
    return f / n
def points_from_regen(files):
    pts = []
    for f in sorted(files):
        for i, l in enumerate(open(f, encoding='latin1')):
            t = l.split()
            if len(t) > 3 and t[0] in ('r', 'g', 'm', 's'):
                pts.append(('%s:%d' % (os.path.basename(f), i + 1), int(t[1]), int(t[2]), int(t[3])))
    return pts
def check(name, W, H, g, pts):
    bad = []
    for n, x, y, r in pts:
        fr = freefrac(W, H, g, x, y, max(r, 1))
        if blocked(W, H, g, x, y) or fr < 0.5: bad.append((n, x, y, round(fr, 2), 'BLOCKED' if blocked(W, H, g, x, y) else 'tight'))
    print('==', name, len(pts), 'points,', len(bad), 'blocked/tight:')
    for b in bad: print('   ', b)
    return bad
def snap(W, H, g, x, y, r=3, need=0.9):
    best = None
    for R in range(0, 60):
        for dy in range(-R, R + 1):
            for dx in range(-R, R + 1):
                if max(abs(dx), abs(dy)) != R: continue
                xx, yy = x + dx, y + dy
                if not blocked(W, H, g, xx, yy) and freefrac(W, H, g, xx, yy, r) >= need:
                    d = dx * dx + dy * dy
                    if best is None or d < best[0]: best = (d, xx, yy)
        if best: return best[1], best[2]
    raise SystemExit('no free cell near %d,%d' % (x, y))
def component_centroid(W, H, g, x, y):
    sx, sy = snap(W, H, g, x, y, 0, 1.0)
    seen = {(sx, sy)}; todo = [(sx, sy)]; sumx = sumy = 0
    while todo:
        a, b = todo.pop(); sumx += a; sumy += b
        for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            p = (a + da, b + db)
            if p not in seen and not blocked(W, H, g, *p):
                seen.add(p); todo.append(p)
    return sumx / len(seen), sumy / len(seen), len(seen)

mode = sys.argv[1]
if mode == 'razador':
    W, H, g = load('/f/server_attr')
    q = {'entry': (342, 584), 'statue': (350, 360), 'boss_room': (685, 710), 'boss': (686, 637), 'stone2': (195, 352),
         'ignitor': (470, 175), 'metin6': (511, 480)}
    for i, p in enumerate([(320,394),(293,359),(333,321),(378,320),(400,355),(394,401)]): q['door%d' % i] = p
    for i, p in enumerate([(268,447),(234,359),(300,264),(454,217),(470,355),(467,469)]): q['idoor%d' % i] = p
    for i, p in enumerate([(486,345),(511,336),(525,349),(521,365),(503,372),(486,365),(500,354)]): q['stone5_%d' % i] = p
    check('razador quest', W, H, g, [(k, x, y, 1) for k, (x, y) in q.items()])
    check('razador regen', W, H, g, points_from_regen(glob.glob('/d/razador_mt/*.txt')))
else:
    W, H, g = load('/w/attr/server_attr.nemere')
    q = {'entry': (171, 270), 'lion': (172, 261), 'r2': (422, 261), 'r3': (764, 264), 'r4': (175, 535), 'r5': (422, 538),
         'r6': (748, 540), 'r7': (305, 708), 'r8': (571, 701), 'r9': (851, 693), 'r10': (927, 395),
         'metin6': (747, 494), 'pillar': (849, 660), 'boss': (927, 333)}
    for i, p in enumerate([(449,488),(455,445),(419,422),(382,444),(389,488)]): q['seal%d' % i] = p
    for i, p in enumerate([(302,678),(281,657),(303,635),(324,656)]): q['szel%d' % i] = p
    check('nemere quest', W, H, g, [(k, x, y, 1) for k, (x, y) in q.items()])
    for k in ('r4', 'r5', 'r6', 'r9'):
        x, y = q[k]; print('  snap', k, (x, y), '->', snap(W, H, g, x, y, 2, 0.9))
    check('nemere regen (current)', W, H, g, points_from_regen(glob.glob('/d/nemere_mt/*.txt')))
    os.makedirs('/w/attr/nemere_mt_fixed', exist_ok=True)
    for f in sorted(glob.glob('/d/nemere_mt/*.txt')):
        lines = open(f, 'rb').read().decode('latin1').split('\n')
        m = re.search(r'room around \((\d+),(\d+)\)', lines[0])
        cx0, cy0 = int(m.group(1)), int(m.group(2))
        cx, cy, n = component_centroid(W, H, g, cx0, cy0)
        dx, dy = round(cx - cx0), round(cy - cy0)
        out = []; moved = 0
        for l in lines:
            t = l.rstrip('\r').split('\t')
            if len(t) > 3 and t[0] == 'r':
                x, y = int(t[1]) + dx, int(t[2]) + dy
                if blocked(W, H, g, x, y) or freefrac(W, H, g, x, y, int(t[3])) < 0.6:
                    x, y = snap(W, H, g, x, y, int(t[3]), 0.6)
                t[1], t[2] = str(x), str(y); moved += 1
                l = '\t'.join(t) + ('\r' if l.endswith('\r') else '')
            out.append(l)
        out[0] = out[0].replace('room around (%d,%d)' % (cx0, cy0), 'room around (%d,%d) - moved onto the real room by server_attr (GF client attr.atr)' % (cx0 + dx, cy0 + dy))
        open('/w/attr/nemere_mt_fixed/' + os.path.basename(f), 'wb').write('\n'.join(out).encode('latin1'))
        print('  %s: assumed centre (%d,%d) -> walkable area centroid (%d,%d) [%d cells], shift (%d,%d)' % (os.path.basename(f), cx0, cy0, cx, cy, n, dx, dy))
    check('nemere regen (fixed)', W, H, g, points_from_regen(glob.glob('/w/attr/nemere_mt_fixed/*.txt')))
