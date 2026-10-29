# -*- coding: utf-8 -*-
# MT2009_PLUS_NAVGRID_V1 - the check of the "navgrid" pack (build_navgrid.py + build_navgrid_pack.py). Auto Lowy
# navigation based on Path-Finder V1.0 by @coanitoa97 (tutorial by Kolen).
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/navgrid/verify_navgrid.py <OUT pack dir> [<BASE pack dir>] \
#     [--server-maps root[:root...]]
#
# BASE defaults to <OUT>/../../azbase (clientY.sh's layout). Checks:
#  - the pack is there and Index names it;
#  - every map the client can stand on (navgrid_lib.plan_targets: the packs' maps with sectors, atlasinfo's maps with
#    a server_attr) has its grid, and no grid is left over;
#  - every grid: magic, version 4, the stamp of its sources now (a map edited after the grid was made = "stale"), and
#    the very bytes the generator makes from those sources now (walk = attr without BLOCK - water that is not BLOCK is
#    walkable: the package's verify() expected !(BLOCK|WATER) and called good grids wrong);
#  - client against server: for each map built from the client's attr whose server_attr is here, the share of cells
#    where the two disagree (the client walks where the server says blocked or the other way) - reported, WARN above 2%;
#  - the components: a map with more than 254 has "unknown" cells in the exe (the search answers there) - reported.
# Exit 1 with "FAIL" on a missing, stale or different grid; the last line is the summary.
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import navgrid_lib as nl

PACK = 'navgrid'


def full_walk(h, walk):
    W, H = h['map_w'], h['map_h']
    out = bytearray(W * H)
    for y in range(h['h']):
        o = (h['y0'] + y) * W + h['x0']
        out[o:o + h['w']] = walk[y * h['w']:(y + 1) * h['w']]
    return bytes(out)


def main():
    argv = sys.argv[1:]
    roots = None
    if '--server-maps' in argv:
        i = argv.index('--server-maps')
        roots = argv[i + 1].split(':')
        del argv[i:i + 2]
    args = [a for a in argv if not a.startswith('--')]
    out = args[0]
    base = args[1] if len(args) > 1 else os.path.normpath(os.path.join(out, '..', '..', 'azbase'))
    m2pack = nl.pack_modules()
    import packlib
    errors, warns = [], []

    if not os.path.exists(os.path.join(out, PACK + '.index')):
        print('FAIL verify_navgrid: no %s pack in %s' % (PACK, out))
        sys.exit(1)
    ix = os.path.join(out, 'Index') if os.path.exists(os.path.join(out, 'Index')) else os.path.join(base, 'Index')
    if PACK.encode() not in [l.strip() for l in open(ix, 'rb').read().replace(b'\r\n', b'\n').split(b'\n')]:
        errors.append('Index does not name %s' % PACK)
    ents = m2pack.read_index(os.path.join(out, PACK + '.index'))[2]
    dat = packlib.rd(os.path.join(out, PACK + '.data'))
    grids = dict((e['name'], m2pack.read_entry(dat, e)) for e in ents)

    packs = nl.PackSet(base, out)
    servers = nl.find_server_maps(roots or list(nl.DEFAULT_SERVER_ROOTS))
    plans, skipped = nl.plan_targets(packs, servers)
    keys = dict(('maps/%s/navgrid.bin' % m, m) for m in plans)
    for k in sorted(set(keys) - set(grids)):
        errors.append('%s: no grid' % keys[k])
    for k in sorted(set(grids) - set(keys)):
        warns.append('%s: a grid of no map the client stands on' % k)

    mism, comps, frag = [], [], 0
    for k in sorted(set(keys) & set(grids)):
        m, data = keys[k], grids[k]
        p = plans[m]
        try:
            h, walk, cls = nl.parse_grid(data)
        except ValueError as ex:
            errors.append('%s: %s' % (m, ex))
            continue
        if h['version'] != nl.NAV_VERSION:
            errors.append('%s: version %d' % (m, h['version']))
            continue
        if h['stamp'] != p['stamp']:
            errors.append('%s: stale (stamp %08x, the sources now %08x) - run build_navgrid.py' % (m, h['stamp'], p['stamp']))
            continue
        again, rep = nl.generate(packs, p)
        if again != data:
            errors.append('%s: differs from what the generator makes of its sources' % m)
            continue
        if rep['components'] > 254:
            comps.append(m)
        if rep['largest'] < 90.0:
            frag += 1
        srv = p.get('server_any')
        if p['source'] != nl.SOURCE_SERVER and srv:
            st = p['setting']
            sst = nl.read_setting(open(nl.setting_path(srv), 'rb').read().decode('latin-1'))
            if not sst or (sst['sx'], sst['sy']) != (st['sx'], st['sy']):
                warns.append('%s: the server map %s has another size' % (m, srv))
                continue
            blk, wat = nl.read_server_attr(srv, st['sx'], st['sy'])
            cw = full_walk(h, walk)
            sw = blk.translate(bytes([1, 0] + [0] * 254))
            if cw != sw:
                a, b = int.from_bytes(cw, 'little'), int.from_bytes(sw, 'little')
                diff = bin(a ^ b).count('1')
                share = 100.0 * diff / max(cw.count(1), 1)
                mism.append((round(share, 2), m, diff))
                if share > 2.0:
                    warns.append('%s: client and server attr differ in %d cells (%.1f%% of the walkable)' % (m, diff, share))
    packs.close()

    for w in warns:
        print('WARN ' + w)
    for e in errors:
        print('FAIL ' + e)
    print('verify_navgrid: %d grids, %d maps planned (%d from the packs, %d from server_attr), %d skipped (not hosted), '
          '%d compared with server_attr (%d differ, worst %s), %d fragmented, %d over 254 components, %.1f MB pack'
          % (len(grids), len(plans), sum(1 for p in plans.values() if p['source'] != nl.SOURCE_SERVER),
             sum(1 for p in plans.values() if p['source'] == nl.SOURCE_SERVER), len(skipped),
             sum(1 for p in plans.values() if p['source'] != nl.SOURCE_SERVER and p.get('server_any')),
             len(mism), sorted(mism, reverse=True)[:3] if mism else '-', frag, len(comps), len(dat) / 1048576.0))
    if errors:
        print('FAIL verify_navgrid: %d error(s)' % len(errors))
        sys.exit(1)
    print('OK verify_navgrid')


if __name__ == '__main__':
    main()
