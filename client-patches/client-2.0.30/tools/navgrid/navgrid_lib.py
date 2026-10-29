# -*- coding: utf-8 -*-
# MT2009_PLUS_NAVGRID_V1 - the shared part of the navigation grid tools (build_navgrid.py, build_navgrid_pack.py,
# verify_navgrid.py). Auto Lowy navigation based on Path-Finder V1.0 by @coanitoa97 (tutorial by Kolen); the exe side is
# client-patches/exe/UserInterface/NavGrid.cpp. Pure Python 3 (no numpy): every per-cell step is a bytes.translate,
# a slice or a big-int OR, so the whole map set takes a minute or two and runs in the m2pack-lzo image.
#
# A grid is maps/<map>/navgrid.bin: 1 cell = 1 m = 100 units (the client's attr cell), walkable = attr without BLOCK
# (water that is not BLOCK stays walkable - shores, ground under bridges). Header "PXNV" version 4, 40 bytes:
#   0 magic "PXNV" | 4 version 4 | 6 flags (1 = cost layer) | 8 metres per cell (1) | 10 window w | 12 window h
#   14 window x0 | 16 window y0 | 18 the single terrain class (no cost layer) | 20 map w (cells) | 22 map h (cells)
#   24 base x | 28 base y | 32 stamp (CRC32 of the map's source files, see stamp_*) | 36 generator version | 38 source
# then the walk bits (1 bit per cell of the window, little bit order), then, with flag 1, the terrain classes (2 bits per
# cell: 0 road, 1 normal, 2 rough, 3 water). Version 3 (the package's own, 32-byte header) is read too.
import io
import os
import re
import struct
import zlib

GEN_VERSION = 1
NAV_MAGIC = b'PXNV'
NAV_VERSION = 4
HEADER = struct.Struct('<4sHHHHHHHHHHIIIHH')
assert HEADER.size == 40
FLAG_COST = 1
CLS_ROAD, CLS_NORMAL, CLS_ROUGH, CLS_WATER = 0, 1, 2, 3
SOURCE_PACK, SOURCE_SERVER, SOURCE_MIXED = 1, 2, 3
SOURCE_NAMES = {SOURCE_PACK: 'pack', SOURCE_SERVER: 'server_attr', SOURCE_MIXED: 'pack+server_attr'}

ATTR_MAGIC = 2634
A = 256                 # client cells per sector side
TILE_RAW = 258
C_BLOCK, C_WATER = 1, 2
S_BLOCK, S_WATER = 1, 2     # server_attr (low byte of the DWORD)
SECTREE = 6400
S_CELL = 50
S_SIDE = SECTREE // S_CELL  # 128 server cells per sectree

PACK_PATHS = ('/opt/metin2/cache/tcm/tz', '/opt/metin2/cache/arezzo-work/client/az58', '/opt/metin2/cache/c36')

# --- byte tables -----------------------------------------------------------------------------------------------------
T_WALK = bytes(0 if v & C_BLOCK else 1 for v in range(256))
T_BLOCKFF = bytes(0xFF if v & C_BLOCK else 0 for v in range(256))
T_WATER3 = bytes(3 if (v & C_WATER) and not (v & C_BLOCK) else 0 for v in range(256))
T_S_BLOCK = bytes(1 if v & S_BLOCK else 0 for v in range(256))
T_S_WATER = bytes(1 if v & S_WATER else 0 for v in range(256))
T_SHIFT = [bytes(((v & 1) << k) for v in range(256)) for k in range(8)]
T_SHIFT2 = [bytes(((v & 3) << (2 * k)) for v in range(256)) for k in range(4)]


def _or(parts, n):
    """elementwise OR of equal-length byte strings"""
    acc = 0
    for p in parts:
        acc |= int.from_bytes(p, 'little')
    return acc.to_bytes(n, 'little')


def pack_bits(cells):
    """one byte 0/1 per cell -> 1 bit per cell, little bit order (as numpy.packbits(bitorder='little'))"""
    n = (len(cells) + 7) // 8
    cells = cells + b'\0' * (n * 8 - len(cells))
    return _or([cells[k::8].translate(T_SHIFT[k]) for k in range(8)], n)


def unpack_bits(bits, count):
    out = bytearray(count)
    for k in range(8):
        sl = bytes(((b >> k) & 1) for b in range(256))
        part = bits.translate(sl)
        out[k::8] = part[:len(range(k, count, 8))]
    return bytes(out)


def pack_classes(cls):
    n = (len(cls) + 3) // 4
    cls = cls + b'\0' * (n * 4 - len(cls))
    return _or([cls[k::4].translate(T_SHIFT2[k]) for k in range(4)], n)


def unpack_classes(packed, count):
    out = bytearray(count)
    for k in range(4):
        sl = bytes(((b >> (2 * k)) & 3) for b in range(256))
        out[k::4] = packed.translate(sl)[:len(range(k, count, 4))]
    return bytes(out)


# --- texture classes (case-insensitive: the names in setting.txt have capitals, the packs are lower case) ----------
def texture_class(path):
    n = path.replace('\\', '/').lower().split('/')[-1]
    if n.startswith(('tile', 'field', 'road', 'stonefloor')):
        return CLS_ROAD
    if n.startswith(('stone', 'rock', 'beach', 'sand', 'snow_rock')):
        return CLS_ROUGH
    return CLS_NORMAL


def class_table(texset_text):
    """tile index -> class; tile N is the textureset's texture N-1 (index 0 unused), as the package assumes"""
    t = bytearray([CLS_NORMAL]) * 256
    if texset_text:
        for i, path in enumerate(re.findall(r'"([^"]+)"', texset_text)):
            if i + 1 < 256:
                t[i + 1] = texture_class(path)
    return bytes(t)


def read_setting(text):
    d = {}
    for line in text.splitlines():
        p = line.split()
        if len(p) >= 2:
            d[p[0].lower()] = p[1:]
    if 'mapsize' not in d or len(d['mapsize']) < 2:
        return None
    base = d.get('baseposition', ['0', '0'])
    tex = d.get('textureset', [''])[0].replace('\\', '/').split('/')[-1].lower()
    return dict(sx=int(d['mapsize'][0]), sy=int(d['mapsize'][1]), bx=int(base[0]), by=int(base[1]), texset=tex)


# --- packs ------------------------------------------------------------------------------------------------------------
def pack_modules():
    import sys
    for p in reversed(PACK_PATHS):
        if p not in sys.path:
            sys.path.insert(0, p)
    import m2pack
    return m2pack


class PackSet(object):
    """The client's packs as they ship: every *.index of OUT, then those of BASE OUT does not have. Entries are read
    one by one with seek (the map packs are hundreds of MB). A name in two packs: the later in Index wins (reported)."""

    def __init__(self, base, out):
        self.m2pack = pack_modules()
        files = {}
        for d in (base, out):
            if d and os.path.isdir(d):
                for f in os.listdir(d):
                    if f.endswith('.index'):
                        files[f[:-6]] = d
        order = self._index_order(base, out)
        names = sorted(files, key=lambda p: (order.get(p, -1), p))
        self.entries = {}
        self.duplicates = []
        for p in names:
            d = files[p]
            try:
                ents = self.m2pack.read_index(os.path.join(d, p + '.index'))[2]
            except Exception as ex:   # a broken or foreign index - reported, not fatal
                self.duplicates.append(('unreadable', p, str(ex)))
                continue
            for e in ents:
                n = e['name'].replace('\\', '/').lower()
                if n in self.entries and self.entries[n][0] != p:
                    self.duplicates.append((n, self.entries[n][0], p))
                self.entries[n] = (p, os.path.join(d, p + '.data'), e)
        self._fh = {}

    @staticmethod
    def _index_order(base, out):
        for d in (out, base):
            p = os.path.join(d or '', 'Index')
            if d and os.path.exists(p):
                lines = [l.strip().decode('latin-1').lower() for l in open(p, 'rb').read().replace(b'\r\n', b'\n').split(b'\n')]
                return dict((l, i) for i, l in enumerate(lines) if l and l != '*' and l != 'pack')
        return {}

    def has(self, name):
        return name in self.entries

    def crc(self, name):
        """the stored blob's CRC (the index has it): a stamp without reading the data"""
        e = self.entries[name][2]
        return '%s:%08x:%d' % (name, e['dcrc'], e['real'])

    def read(self, name):
        p, data, e = self.entries[name]
        fh = self._fh.get(data)
        if fh is None:
            fh = self._fh[data] = open(data, 'rb')
        fh.seek(e['pos'])
        blob = fh.read(e['size'])
        return self.m2pack.read_entry(blob, dict(e, pos=0))

    def maps(self):
        """{map: {'setting': name, 'sectors': {(x, y): (attr name, tile name or None)}}} of maps/<map>/..."""
        out = {}
        rx = re.compile(r'^maps/([^/]+)/(?:(\d{3})(\d{3})/)?([^/]+)$')
        for n in self.entries:
            m = rx.match(n)
            if not m:
                continue
            mp, sx, sy, f = m.groups()
            d = out.setdefault(mp, {'setting': None, 'sectors': {}})
            if sx is None:
                if f == 'setting.txt':
                    d['setting'] = n
            elif f in ('attr.atr', 'tile.raw'):
                s = d['sectors'].setdefault((int(sx), int(sy)), [None, None])
                s[0 if f == 'attr.atr' else 1] = n
        return out

    def close(self):
        for fh in self._fh.values():
            fh.close()


# --- server_attr ------------------------------------------------------------------------------------------------------
def find_server_maps(roots):
    """{lower map name: dir} of every map dir with server_attr and a setting file under the roots (first root wins)"""
    found = {}
    for root in roots:
        for r in sorted(_expand(root)):
            if not os.path.isdir(r):
                continue
            for name in sorted(os.listdir(r)):
                d = os.path.join(r, name)
                if os.path.isfile(os.path.join(d, 'server_attr')) and setting_path(d):
                    found.setdefault(name.lower(), d)
    return found


def _expand(root):
    import glob
    return glob.glob(root) if any(c in root for c in '*?[') else [root]


def setting_path(d):
    for n in ('Setting.txt', 'setting.txt', 'SETTING.TXT'):
        if os.path.isfile(os.path.join(d, n)):
            return os.path.join(d, n)
    return None


def file_stamp_parts(paths):
    parts = []
    for p in paths:
        b = open(p, 'rb').read()
        parts.append('%s:%08x:%d' % (os.path.basename(p).lower(), zlib.crc32(b) & 0xffffffff, len(b)))
    return parts


def read_server_attr(d, sx, sy):
    """the server's attr of a map, down to client cells (2x2 server cells each): (blocked bytes, water bytes), one byte
    0/1 per client cell, W = sx*256 by H = sy*256; a client cell is blocked when any of its four server cells is"""
    import lzo
    raw = open(os.path.join(d, 'server_attr'), 'rb').read()
    w, h = struct.unpack_from('<ii', raw, 0)
    off = 8
    W, H = sx * A, sy * A
    blk = bytearray(b'\1' * (W * H))
    wat = bytearray(W * H)
    half = S_SIDE // 2       # 64 client cells per sectree side
    for ty in range(h):
        for tx in range(w):
            size = struct.unpack_from('<I', raw, off)[0]
            off += 4
            cells = lzo.decompress(raw[off:off + size], False, S_SIDE * S_SIDE * 4)
            off += size
            low = cells[0::4]   # the low byte of every DWORD: BLOCK 1, WATER 2, OBJECT 128
            b = low.translate(T_S_BLOCK)
            wa = low.translate(T_S_WATER)
            for cy in range(half):
                gy = ty * half + cy
                if gy >= H:
                    break
                r0 = b[(2 * cy) * S_SIDE:(2 * cy + 1) * S_SIDE]
                r1 = b[(2 * cy + 1) * S_SIDE:(2 * cy + 2) * S_SIDE]
                row = _or([r0[0::2], r0[1::2], r1[0::2], r1[1::2]], half)
                w0 = wa[(2 * cy) * S_SIDE:(2 * cy + 1) * S_SIDE]
                w1 = wa[(2 * cy + 1) * S_SIDE:(2 * cy + 2) * S_SIDE]
                wrow = _or([w0[0::2], w0[1::2], w1[0::2], w1[1::2]], half)
                gx = tx * half
                if gx >= W:
                    continue
                n = min(half, W - gx)
                blk[gy * W + gx:gy * W + gx + n] = row[:n]
                wat[gy * W + gx:gy * W + gx + n] = wrow[:n]
    return bytes(blk), bytes(wat)


# --- the grid ---------------------------------------------------------------------------------------------------------
def assemble_pack_attr(packs, info, sx, sy):
    """client attr + tile of a map from the packs: (attr, tile, sectors read, sectors broken); a missing sector is BLOCK"""
    W, H = sx * A, sy * A
    attr = bytearray(bytes([C_BLOCK]) * (W * H))
    tile = bytearray(W * H)
    have, broken = set(), 0
    for (ix, iy), (an, tn) in info['sectors'].items():
        if an is None or ix >= sx or iy >= sy:
            continue
        raw = packs.read(an)
        if len(raw) < 6 + A * A or struct.unpack_from('<HHH', raw, 0) != (ATTR_MAGIC, A, A):
            broken += 1
            continue
        have.add((ix, iy))
        t = None
        if tn:
            tr = packs.read(tn)
            if len(tr) >= TILE_RAW * TILE_RAW:
                t = tr
        for r in range(A):
            o = (iy * A + r) * W + ix * A
            attr[o:o + A] = raw[6 + r * A:6 + (r + 1) * A]
            if t is not None:
                tile[o:o + A] = t[(r + 1) * TILE_RAW + 1:(r + 1) * TILE_RAW + 1 + A]
    return attr, tile, have, broken


def merge_server_sectors(attr, sblk, swat, sx, sy, missing):
    """sectors the packs lack, from the server's attr (BLOCK, WATER into client bits)"""
    W = sx * A
    tw = bytes(C_WATER if v else 0 for v in range(256))
    for (ix, iy) in missing:
        for r in range(A):
            o = (iy * A + r) * W + ix * A
            b = sblk[o:o + A]
            w = swat[o:o + A].translate(tw)
            attr[o:o + A] = _or([b, w], A)


def build_grid(attr, tile, cls_table, sx, sy, bx, by, stamp, source):
    """the navgrid.bin of a map from its client attr (one byte per cell, client bits) and tile indices (or None): the
    file's bytes and a report dict, or (None, reason)"""
    W, H = sx * A, sy * A
    attr = bytes(attr)
    walk = attr.translate(T_WALK)
    rows = [y for y in range(H) if 1 in walk[y * W:(y + 1) * W]]
    if not rows:
        return None, 'no walkable cell'
    y0, y1 = rows[0], rows[-1] + 1
    colmask = 0
    for y in range(y0, y1):
        colmask |= int.from_bytes(walk[y * W:(y + 1) * W], 'little')
    cb = colmask.to_bytes(W, 'little')
    x0 = next(i for i in range(W) if cb[i])
    x1 = W - next(i for i in range(W) if cb[W - 1 - i])
    ww, hh = x1 - x0, y1 - y0
    wcrop = b''.join(walk[y * W + x0:y * W + x1] for y in range(y0, y1))
    acrop = b''.join(attr[y * W + x0:y * W + x1] for y in range(y0, y1))
    n = ww * hh
    if tile is not None and cls_table is not None:
        tcrop = b''.join(bytes(tile[y * W + x0:y * W + x1]) for y in range(y0, y1))
        cls = tcrop.translate(cls_table)
    else:
        cls = bytes([CLS_NORMAL]) * n
    cls = _or([cls, acrop.translate(T_WATER3)], n)          # water (not blocked) -> 3
    bm = int.from_bytes(acrop.translate(T_BLOCKFF), 'little')
    ones = int.from_bytes(b'\x01' * n, 'little')
    c = int.from_bytes(cls, 'little')
    cls = ((c & ~bm) | (bm & ones)).to_bytes(n, 'little')   # blocked -> normal (unused)
    marked = ((int.from_bytes(cls, 'little') & ~bm) | bm).to_bytes(n, 'little')   # blocked -> 0xFF for counting
    counts = [marked.count(bytes([v])) for v in range(4)]
    present = [v for v in range(4) if counts[v]]
    uniform = len(present) <= 1
    single = present[0] if len(present) == 1 else CLS_NORMAL
    body = pack_bits(wcrop)
    if not uniform:
        body += pack_classes(cls)
    head = HEADER.pack(NAV_MAGIC, NAV_VERSION, 0 if uniform else FLAG_COST, 1, ww, hh, x0, y0, single, W, H,
                       bx, by, stamp, GEN_VERSION, source)
    data = head + body
    nwalk = sum(counts)
    comps, largest = components(wcrop, ww, hh)
    rep = dict(W=ww, H=hh, x0=x0, y0=y0, bytes=len(data), zlib=len(zlib.compress(data, 6)), walkable=nwalk,
               road=counts[CLS_ROAD], water=counts[CLS_WATER], uniform=uniform, components=comps,
               largest=round(100.0 * largest / max(nwalk, 1), 1))
    return data, rep


def components(wcrop, w, h):
    """4-connected components (the exe's rule: a diagonal step needs both straight neighbours open, so only straight
    steps join areas) by row runs and union-find: (count, size of the largest)"""
    parent = []
    sizes = []

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    prev = []
    rx = re.compile(b'\x01+')
    for y in range(h):
        row = wcrop[y * w:(y + 1) * w]
        cur = []
        j = 0
        for m in rx.finditer(row):
            s, e = m.start(), m.end()
            lab = len(parent)
            parent.append(lab)
            sizes.append(e - s)
            while j < len(prev) and prev[j][1] <= s:
                j += 1
            k = j
            while k < len(prev) and prev[k][0] < e:
                ra, rb = find(lab), find(prev[k][2])
                if ra != rb:
                    parent[max(ra, rb)] = min(ra, rb)
                k += 1
            cur.append((s, e, lab))
        prev = cur
    if not parent:
        return 0, 0
    tot = {}
    for lab, m in enumerate(sizes):
        r = find(lab)
        tot[r] = tot.get(r, 0) + m
    return len(tot), max(tot.values())


def parse_grid(data):
    """(header dict, walk bytes 0/1 per window cell, class bytes)"""
    if len(data) < 32 or data[:4] != NAV_MAGIC:
        raise ValueError('not a navgrid file')
    ver = struct.unpack_from('<H', data, 4)[0]
    if ver == 4:
        f = HEADER.unpack_from(data, 0)
        hdr = 40
    elif ver == 3:
        f = struct.unpack_from('<4sHHHHHHHHHHII', data, 0) + (0, 0, 0)
        hdr = 32
    else:
        raise ValueError('version %d' % ver)
    keys = ('magic', 'version', 'flags', 'metres', 'w', 'h', 'x0', 'y0', 'single', 'map_w', 'map_h', 'bx', 'by',
            'stamp', 'gen', 'source')
    h = dict(zip(keys, f))
    n = h['w'] * h['h']
    nb = (n + 7) // 8
    nc = (n + 3) // 4 if h['flags'] & FLAG_COST else 0
    if len(data) < hdr + nb + nc:
        raise ValueError('truncated')
    walk = unpack_bits(data[hdr:hdr + nb], n)
    cls = unpack_classes(data[hdr + nb:hdr + nb + nc], n) if nc else bytes([h['single']]) * n
    return h, walk, cls


def stamp_of(parts):
    return zlib.crc32(('gen%d;' % GEN_VERSION + ';'.join(sorted(parts))).encode('latin-1')) & 0xffffffff


# --- what is built from what ------------------------------------------------------------------------------------------
DEFAULT_SERVER_ROOTS = (
    # the base maps (the test tree's share; the same maps as the players' base client)
    '/opt/metin2/mt2009plustest/linux-port/docker/game/src/serverfiles/share/locale/poland/map',
    # our own maps (Yohara, Arezzo, Zodiac, dungeons...), from the repository the tool runs from
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'linux-port', 'docker', 'game',
                 '*', 'map'),
)


def atlas_maps(packs):
    """{map: (base x, base y, sectors x, sectors y)} of the client's atlasinfo.txt - the names the client calls its maps by"""
    n = 'gamedata/atlasinfo.txt'
    if not packs.has(n):
        return {}
    out = {}
    for line in packs.read(n).decode('latin-1').splitlines():
        p = line.split()
        if len(p) >= 5:
            try:
                out[p[0].lower()] = (int(p[1]), int(p[2]), int(p[3]), int(p[4]))
            except ValueError:
                pass
    return out


def servers_by_base(servers):
    """{(base x, base y, sectors x, sectors y): dir} - a server map dir may be named otherwise than the client's map (metin2_map_monkey_dungeon
    on the server is metin2_map_monkeydungeon in the client): the base position joins them"""
    out = {}
    for m, d in sorted(servers.items()):
        st = read_setting(open(setting_path(d), 'rb').read().decode('latin-1'))
        if st:
            out.setdefault((st['bx'], st['by'], st['sx'], st['sy']), d)
    return out


def plan_targets(packs, servers):
    """{map: plan} for every map the client can stand on: each map of the packs with a setting.txt and at least one
    sector, and each map of atlasinfo.txt; plan = dict(source, setting dict, parts (stamp), missing sectors, ...).
    Maps with no source go to the second dict with the reason."""
    pm = packs.maps()
    atlas = atlas_maps(packs)
    by_base = servers_by_base(servers)
    names = set(m for m, d in pm.items() if d['setting']) | set(atlas)
    plans, skipped = {}, {}
    for m in sorted(names):
        d = pm.get(m)
        srv = servers.get(m) or (by_base.get(atlas[m]) if m in atlas else None)
        st = None
        if d and d['setting'] and d['sectors']:
            st = read_setting(packs.read(d['setting']).decode('latin-1'))
        if st:
            sectors = set(k for k, v in d['sectors'].items() if v[0] and k[0] < st['sx'] and k[1] < st['sy'])
            missing = sorted(set((x, y) for x in range(st['sx']) for y in range(st['sy'])) - sectors)
            parts = [packs.crc(d['setting'])]
            for k in sorted(sectors):
                parts += [packs.crc(n) for n in d['sectors'][k] if n]
            tex = 'textureset/' + st['texset'] if st['texset'] else None
            if tex and packs.has(tex):
                parts.append(packs.crc(tex))
            else:
                tex = None
            source = SOURCE_PACK
            if missing and srv:
                srv_st = read_setting(open(setting_path(srv), 'rb').read().decode('latin-1'))
                if srv_st and (srv_st['sx'], srv_st['sy']) == (st['sx'], st['sy']):
                    source = SOURCE_MIXED
                    parts += file_stamp_parts([os.path.join(srv, 'server_attr'), setting_path(srv)])
            plans[m] = dict(source=source, setting=st, pack=d, server=srv if source == SOURCE_MIXED else None,
                            missing=missing, tex=tex, parts=parts)
        elif srv:
            st = read_setting(open(setting_path(srv), 'rb').read().decode('latin-1'))
            if not st:
                skipped[m] = 'server Setting.txt without MapSize'
                continue
            plans[m] = dict(source=SOURCE_SERVER, setting=st, pack=None, server=srv, missing=[], tex=None,
                            parts=file_stamp_parts([os.path.join(srv, 'server_attr'), setting_path(srv)]))
        else:
            skipped[m] = ('setting.txt without sectors in the packs, no server_attr' if d and d['setting']
                          else 'in atlasinfo only (no client sectors, no server_attr: not hosted)')
    for m, p in plans.items():
        p['stamp'] = stamp_of(p['parts'])
        p['server_any'] = servers.get(m) or (by_base.get(atlas[m]) if m in atlas else None)
    return plans, skipped


def generate(packs, plan):
    """(bytes, report) or (None, reason) for one plan of plan_targets"""
    st = plan['setting']
    sx, sy = st['sx'], st['sy']
    if plan['source'] == SOURCE_SERVER:
        blk, wat = read_server_attr(plan['server'], sx, sy)
        tw = bytes(C_WATER if v else 0 for v in range(256))
        attr = _or([blk, wat.translate(tw)], len(blk))
        return build_grid(attr, None, None, sx, sy, st['bx'], st['by'], plan['stamp'], plan['source'])
    attr, tile, have, broken = assemble_pack_attr(packs, plan['pack'], sx, sy)
    if plan['source'] == SOURCE_MIXED:
        blk, wat = read_server_attr(plan['server'], sx, sy)
        merge_server_sectors(attr, blk, wat, sx, sy, plan['missing'])
    table = class_table(packs.read(plan['tex']).decode('latin-1')) if plan['tex'] else None
    data, rep = build_grid(attr, tile if table else None, table, sx, sy, st['bx'], st['by'], plan['stamp'],
                           plan['source'])
    if data is not None:
        rep['broken_sectors'] = broken
        rep['missing_sectors'] = len(plan['missing'])
    return data, rep
