# -*- coding: utf-8 -*-
# MT2009_PLUS_MAP_ENVIRONMENT_V1 - the new client pack "ymsenv": a map-folder copy of the environment of every map of
# our packs whose environment exe 2.0.25 cannot load (msenvlib.py has the exe's path; without it the map has no sky,
# fog or lights and syserr gets "CMapOutdoor::RenderBeforeLensFlare mc_pEnvironmentData is NULL" every frame).
#
# Written for the Yohara 3.0.6 player's syserr of 3 November 2026. Found on the 3.0.0 + 3.0.3 + 3.0.6 + 3.0.6b
# client (and the 3.0.7 build): Wezowe Pole (metin2_map_snakefield) and Kraina Gigantow (metin2_map_giantland) -
# ../wzmaps - name "Environment milgyo.msenv" (GF's setting.txt of metin2_map_wl_01 / nusluck01) and ship no copy:
# the exe then reads d:/ymir work/environment/milgyo.msenv, which no pack of ours has, and the base client keeps its
# environments in the map folders (its season2 pack: season2/<map>/skipia_dungeon.msenv; no d:/ymir work/environment
# in its etc pack) - so the base client's Hwang Temple's environment is not there under that name either.
# The fix: maps/metin2_map_snakefield/milgyo.msenv and maps/metin2_map_giantland/milgyo.msenv (the exe's
# LOCAL_ENVIRONMENT_DATA reads the map folder's copy first) = env/milgyo.msenv: GF's milgyo.msenv (the file GF's
# client gives these two maps) with "foglevel 2" turned into Enable 1 / NearDistance 2000 / FarDistance 50000 (the
# classic milgyo.msenv's of the Ameria sources) - its cloud (clouds_zone01.tga, az_maps) and flare (clouds_zone02.tga,
# iluzja_map) textures are in our packs, it names no skybox faces.
# Any later map with the same fault is found the same way: the builder stops and asks for env/<name>
# ("--make <name>" converts GF's file of that name into env/<name>; commit it).
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/msenv/build_msenv_pack.py <BASE pack dir> <OUT pack dir> [--check]
#   ... build_msenv_pack.py --make <env name>       # GF -> env/<env name> (exe 2.0.25 fog), then commit it
#
# clientY.sh: after every map builder (wzmaps, ycopymaps ...) - after navgrid_pack, before the npclist / verify loop:
#   S_msenv_pack() { docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/msenv/build_msenv_pack.py \
#     $C/azbase $C/out/pack; }; step msenv_pack $C/msenv.json S_msenv_pack
# then msenv/verify_msenv.py on OUT (in the verify loop). BASE: the client's packs so far (Index is read from OUT if an
# earlier step wrote one there, else from BASE); OUT: where ymsenv.index / ymsenv.data and the Index go. Its Index line
# goes LAST: every name it holds is new (a map folder's own copy) - the builder stops if one is not.
# --check measures only. Every entry written is read back. Idempotent: the same content gives "unchanged"; the Index
# line is not added twice; nothing needed and no pack yet -> no pack and no Index line.
import json
import os
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, HERE)
import msenvlib as L  # noqa: E402

PACK = L.PACK


def main():
    if '--make' in sys.argv:
        env = sys.argv[sys.argv.index('--make') + 1]
        b = L.make_env(env)
        os.makedirs(L.ENV_DIR, exist_ok=True)
        open(os.path.join(L.ENV_DIR, env.lower()), 'wb').write(b)
        print('env/%s: %d bytes' % (env.lower(), len(b)))
        return
    import m2pack
    import packlib
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    check = '--check' in sys.argv
    base, out = args[:2]
    rd = packlib.rd
    view = L.View(out, base, skip=(PACK,))
    want = L.needed(view)
    report = {'maps': dict((n, '%s (%s)' % (m, e)) for n, (b, m, e) in sorted(want.items())),
              'base_client_packs_not_here': len(view.missing)}
    for n in want:
        if view.has(n):
            raise SystemExit('%s: already in pack %s' % (n, view.pack_of(n)))
    have_pack = os.path.exists(os.path.join(out, PACK + '.index'))
    if not want and not have_pack:
        report[PACK] = 'nothing needed'
        print(json.dumps(report, indent=1))
        return
    items = dict((n, (b, 2)) for n, (b, m, e) in want.items())
    raw = dict((n, b) for n, (b, c) in items.items())

    built = False
    if have_pack:
        f, v, ents = m2pack.read_index(os.path.join(out, PACK + '.index'))
        dat = rd(os.path.join(out, PACK + '.data'))
        if dict((e['name'], m2pack.read_entry(dat, e)) for e in ents) == raw and all(e['ctype'] == 2 for e in ents):
            report[PACK] = 'unchanged'
            built = True
    if not built:
        if check:
            report[PACK] = dict(files=len(items), data_kb=round(sum(len(m2pack.encode_entry(b, c))
                                                                    for b, c in items.values()) / 1e3, 1))
        else:
            if not items:
                raise SystemExit('%s.index in OUT but nothing is needed any more: remove it and its Index line' % PACK)
            tdir = base if os.path.exists(os.path.join(base, 'gf_mobs.index')) else out
            tmpl = m2pack.read_index(os.path.join(tdir, 'gf_mobs.index'))[2][-1]['raw']
            ti, td = os.path.join(out, PACK + '.index.tmp'), os.path.join(out, PACK + '.data.tmp')
            packlib.repack_add_typed(None, None, {}, items, ti, td, tmpl)
            os.replace(ti, os.path.join(out, PACK + '.index'))
            os.replace(td, os.path.join(out, PACK + '.data'))
            f, v, ents = m2pack.read_index(os.path.join(out, PACK + '.index'))
            dat = rd(os.path.join(out, PACK + '.data'))
            got = {}
            for e in ents:
                assert zlib.crc32(dat[e['pos']:e['pos'] + e['size']]) & 0xffffffff == e['dcrc'], e['name']
                assert e['fcrc'] == zlib.crc32(e['name'].encode('cp1252')) & 0xffffffff, e['name']
                assert e['ctype'] == 2, e['name']
                got[e['name']] = m2pack.read_entry(dat, e)
            assert got == raw, 'read-back differs'
            report[PACK] = dict(entries=len(ents), data_kb=round(len(dat) / 1e3, 1))

    # Index: "*" + "ymsenv" at the end
    if not check:
        ix_path = view.index_path
        ix = rd(ix_path)
        nl = b'\r\n' if b'\r\n' in ix else b'\n'
        lines = ix.replace(b'\r\n', b'\n').split(b'\n')
        if PACK.encode() in [l.strip() for l in lines]:
            new = ix
        else:
            while lines and not lines[-1].strip():
                lines.pop()
            lines += [b'*', PACK.encode(), b'']
            new = nl.join(lines)
        if new != ix or ix_path != os.path.join(out, 'Index'):
            open(os.path.join(out, 'Index'), 'wb').write(new)
            report['Index'] = 'written'
        else:
            report['Index'] = 'unchanged'
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
