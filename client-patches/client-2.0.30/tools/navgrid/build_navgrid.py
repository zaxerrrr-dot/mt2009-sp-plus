# -*- coding: utf-8 -*-
# MT2009_PLUS_NAVGRID_V1 - the navigation grids of Auto Lowy (the owner, 29 October 2026; based on Path-Finder V1.0 by
# @coanitoa97, tutorial by Kolen): maps/<map>/navgrid.bin for every map the client can stand on, into a cache; the pack
# "navgrid" is made from the cache by build_navgrid_pack.py, checked by verify_navgrid.py. Format: navgrid_lib.py.
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/navgrid/build_navgrid.py <BASE pack dir> <OUT pack dir> \
#     [--cache /opt/metin2/cache/navgrid-cache] [--server-maps root[:root...]] [--maps a,b] [--force]
#
# Sources, per map: the client's own attr from the packs (OUT's packs, then BASE's - as the client ships them); a map
# whose sectors are not all in our packs gets the missing ones from the server's server_attr (the same attr, 50-unit
# cells, 2x2 down to the client's 1 m); a map with no client sectors at all (the base maps of the players' base client:
# a1, b1, c1, desert, flame...) is built from server_attr alone (no terrain classes there, so no road preference).
# Server roots by default: the test tree's share/locale/poland/map and the repository's linux-port/docker/game/*/map.
#
# Incremental: every grid carries a stamp - CRC32 of its sources (the packs' stored CRCs of setting.txt, attr.atr,
# tile.raw and the textureset; the server files' own CRC) - and the cache keeps <cache>/<map>/<stamp>.bin; a map whose
# stamp is in the cache is not built again. manifest.json in the cache lists the grids of this run for the pack builder.
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import navgrid_lib as nl

DEFAULT_CACHE = '/opt/metin2/cache/navgrid-cache'


def opt(name, default=None):
    if name in sys.argv:
        i = sys.argv.index(name)
        return sys.argv[i + 1]
    return default


def main():
    args = []
    skip = False
    for i, a in enumerate(sys.argv[1:]):
        if skip:
            skip = False
            continue
        if a in ('--cache', '--server-maps', '--maps'):
            skip = True
            continue
        if not a.startswith('--'):
            args.append(a)
    if len(args) < 2:
        raise SystemExit('usage: build_navgrid.py <BASE pack dir> <OUT pack dir> [--cache DIR] [--server-maps R:R] '
                         '[--maps a,b] [--force]')
    base, out = args[:2]
    cache = opt('--cache', DEFAULT_CACHE)
    roots = opt('--server-maps')
    roots = roots.split(':') if roots else list(nl.DEFAULT_SERVER_ROOTS)
    only = set(m.lower() for m in opt('--maps', '').split(',') if m)
    force = '--force' in sys.argv

    t0 = time.time()
    packs = nl.PackSet(base, out)
    servers = nl.find_server_maps(roots)
    plans, skipped = nl.plan_targets(packs, servers)
    old = {}
    mpath = os.path.join(cache, 'manifest.json')
    if os.path.exists(mpath):
        try:
            old = json.load(open(mpath)).get('maps', {})
        except ValueError:
            old = {}
    manifest = {}
    built, reused, failed = [], [], {}
    for m in sorted(plans):
        p = plans[m]
        if only and m not in only:
            if m in old:
                manifest[m] = old[m]
            continue
        d = os.path.join(cache, m.replace('/', '__'))   # season2/<map> - one flat dir per map
        f = os.path.join(d, '%08x.bin' % p['stamp'])
        rep = old.get(m, {}).get('report') if old.get(m, {}).get('stamp') == p['stamp'] else None
        if os.path.exists(f) and rep is not None and not force:
            reused.append(m)
        else:
            t = time.time()
            try:
                data, rep = nl.generate(packs, p)
            except Exception as ex:     # a damaged source: reported here, and verify_navgrid.py fails on the map
                failed[m] = '%s: %s' % (type(ex).__name__, ex)
                continue
            if data is None:
                skipped[m] = rep
                continue
            rep['seconds'] = round(time.time() - t, 2)
            os.makedirs(d, exist_ok=True)
            open(f + '.tmp', 'wb').write(data)
            os.replace(f + '.tmp', f)
            built.append(m)
        for x in os.listdir(d):     # only the current grid of a map stays
            if x != os.path.basename(f):
                os.remove(os.path.join(d, x))
        manifest[m] = dict(stamp=p['stamp'], file=os.path.relpath(f, cache), source=nl.SOURCE_NAMES[p['source']],
                           report=rep)
    # maps no longer planned leave the cache
    if os.path.isdir(cache) and not only:
        for x in os.listdir(cache):
            if os.path.isdir(os.path.join(cache, x)) and x not in set(k.replace('/', '__') for k in manifest):
                for y in os.listdir(os.path.join(cache, x)):
                    os.remove(os.path.join(cache, x, y))
                os.rmdir(os.path.join(cache, x))
    os.makedirs(cache, exist_ok=True)
    json.dump(dict(generator=nl.GEN_VERSION, maps=manifest), open(mpath + '.tmp', 'w'), indent=1, sort_keys=True)
    os.replace(mpath + '.tmp', mpath)
    packs.close()

    reps = [v['report'] for v in manifest.values()]
    summary = dict(
        maps=len(manifest), built=len(built), reused=len(reused), failed=failed, skipped=skipped,
        sources=dict((s, sum(1 for v in manifest.values() if v['source'] == s)) for s in nl.SOURCE_NAMES.values()),
        raw_mb=round(sum(r['bytes'] for r in reps) / 1048576.0, 2),
        zlib_mb=round(sum(r['zlib'] for r in reps) / 1048576.0, 2),
        seconds=round(time.time() - t0, 1),
        largest=sorted(((v['report']['bytes'] // 1024, m) for m, v in manifest.items()), reverse=True)[:8],
        fragmented=sorted((m, v['report']['components'], v['report']['largest']) for m, v in manifest.items()
                          if v['report']['largest'] < 90.0),
        over_254_components=sorted(m for m, v in manifest.items() if v['report']['components'] > 254),
        duplicate_entries=len([x for x in packs.duplicates if x[0] != 'unreadable']),
        unreadable_packs=[x[1] for x in packs.duplicates if x[0] == 'unreadable'],
    )
    if built:
        summary['built_maps'] = built if len(built) <= 40 else built[:40] + ['...']
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()
