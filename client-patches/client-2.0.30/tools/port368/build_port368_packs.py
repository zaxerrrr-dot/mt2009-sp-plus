# -*- coding: utf-8 -*-
# MT2009_PLUS_YOHARA_PORT_V1 (client) - the client build's part for Port Nowego Kontynentu (map 368,
# metin2_map_defensewave_port):
#   1) the new pack port_map (the map folder, setting.txt with BasePosition 128000 563200, the msenv copy, the atlas,
#      the port's object models and textures), staged by stage_port368.py under <staging>/add/<pack>/<in-pack path>
#      ("d_/" = "d:/"), listed in port368_manifest.json;
#   2) the existing pack "property": the port's 7 object properties (property/defensewave/b_general_*, b_old_dock_*,
#      property/eastplain/deadwood_08) added;
#   3) its line at the end of pack/Index;
#   4) the row "metin2_map_defensewave_port 128000 563200 3 3" in gamedata/atlasinfo.txt (append only).
# The textureset, the msenv and the statue's race (20433 defensewave_statue, its mob_proto row) are the ship's:
# ../shipdefense. The map's name "Port Nowego Kontynentu" (localeinfo.py MINIMAP_ZONE_NAME_DICT) travels in
# client-2.0.30/root like every root change.
# BUILD ORDER - they share pack/Index, property and gamedata: the build's own packs, then cape301 (it also fixes our
# property/devils_dragon_island/thing/ships_brokenbody00.prb, an object of the port), maps302, shipdefense, then this
# one, all on the same OUT (a property/gamedata pack already in OUT - an earlier step changed it - is the one patched):
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/port368/build_port368_packs.py \
#     <BASE pack dir> <OUT pack dir> <staging dir> [--data <dir>]
#   ... build_port368_packs.py <BASE> - <staging> --check      # measure only, writes nothing
#
# client61.sh-style builds: after the shipdefense line,
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/port368/build_port368_packs.py $C/azbase \
#     $C/out/pack /opt/metin2/cache/yohara/port-staging > $C/port368.json
# then verify_port368.py on OUT. --data: a directory with the build's patched copies (flat: atlasinfo.txt) to start
# from instead of the pack's entry.
# Every entry written is read back. A staged name that BASE or another OUT pack already has is left out when the
# bytes are the same and stops the run when they differ (stage again: stage_port368.py). Idempotent: a BASE/OUT that
# has it all gives "in base"/"in out"/"unchanged".
import json
import os
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, HERE)
TEXT = ('.txt', '.msa', '.msm', '.mse', '.mss', '.msenv', '.sub', '.prb', '.prd', '.pre', '.prt', '.py', '.ifl', '.pra')
ZIP_LIMIT = 29 * 1024 * 1024
NEW_PACKS = ('port_map',)
ATLAS = ['metin2_map_defensewave_port\t128000\t563200\t3\t3']   # = the server's Setting.txt
OLD_PACKS = ('property',)


class Collision(Exception):
    pass


def atlasinfo(b):
    """APPEND ONLY: the port's row; a row of that map with other numbers is a collision"""
    text = b.decode('cp1250')
    nl = '\r\n' if '\r\n' in text else '\n'
    lines = text.split(nl)
    tail = bool(lines) and lines[-1] == ''
    if tail:
        lines.pop()
    have = dict((l.split('\t')[0].strip().lower(), l) for l in lines if l.strip())
    new = []
    for row in ATLAS:
        k = row.split('\t')[0].lower()
        if k in have:
            if have[k].split() != row.split():
                raise Collision('atlasinfo.txt: %s already there as %r' % (k, have[k]))
            continue
        new.append(row)
    if not new:
        return b, 0
    return (nl.join(lines + new + ([''] if tail else []))).encode('cp1250'), len(new)


def ctype(name):
    return 2 if name.endswith(TEXT) else 1


def main():
    import m2pack
    import packlib
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    check = '--check' in sys.argv
    data_from = sys.argv[sys.argv.index('--data') + 1] if '--data' in sys.argv else None
    if data_from:
        args.remove(data_from)
    base, out, staging = args[:3]
    man = json.load(open(os.path.join(HERE, 'port368_manifest.json'), encoding='utf-8'))
    rd = packlib.rd

    # every name of BASE and of the other packs already in OUT (OUT's copy of a pack wins)
    dirs = [base] + ([out] if not check and os.path.isdir(out) else [])
    where = {}
    for d in dirs:
        for p in sorted(f[:-6] for f in os.listdir(d) if f.endswith('.index')):
            if p in NEW_PACKS:
                continue
            where[p] = d
    allnames = {}
    for p, d in sorted(where.items()):
        for e in m2pack.read_index(os.path.join(d, p + '.index'))[2]:
            allnames.setdefault(e['name'], (p, d, e))
    datcache = {}

    def existing(k):
        p, d, e = allnames[k]
        if (p, d) not in datcache:
            datcache[(p, d)] = rd(os.path.join(d, p + '.data'))
        return m2pack.read_entry(datcache[(p, d)], e)

    tmpl = m2pack.read_index(os.path.join(base, 'az_mobs.index'))[2][-1]['raw']

    def staged(pack, k):
        return rd(os.path.join(staging, 'add', pack, k.replace('d:/', 'd_/', 1)))

    def src_of(pack):
        if not check and os.path.exists(os.path.join(out, pack + '.index')):
            return out
        return base

    report = {}
    shared = []

    def write(pack, src, rep, add, ents, dat):
        tmp_i, tmp_d = os.path.join(out, pack + '.index.po'), os.path.join(out, pack + '.data.po')
        exists = src is not None
        r = packlib.repack_add_typed(os.path.join(src, pack + '.index') if exists else None,
                                     os.path.join(src, pack + '.data') if exists else None, rep, add, tmp_i, tmp_d,
                                     ents[-1]['raw'] if ents else tmpl)
        os.replace(tmp_i, os.path.join(out, pack + '.index'))
        os.replace(tmp_d, os.path.join(out, pack + '.data'))
        f, v, nw = m2pack.read_index(os.path.join(out, pack + '.index'))
        nd = rd(os.path.join(out, pack + '.data'))
        names = [e['name'] for e in nw]
        assert len(set(names)) == len(names), pack
        got = {}
        for e in nw:
            assert zlib.crc32(nd[e['pos']:e['pos'] + e['size']]) & 0xffffffff == e['dcrc'], (pack, e['name'])
            assert e['fcrc'] == zlib.crc32(e['name'].encode('cp1252')) & 0xffffffff, (pack, e['name'])
            got[e['name']] = m2pack.read_entry(nd, e)
        for n, b in list(rep.items()) + [(k, b) for k, (b, c) in add.items()]:
            assert got[n] == b, (pack, n)
        for e in ents:
            if e['name'] not in rep:
                assert got[e['name']] == m2pack.read_entry(dat, e), (pack, e['name'])
        return dict(old=r[0], added=r[1], replaced=r[2], entries=len(nw), data_mb=round(len(nd) / 1e6, 2),
                    under_zip_limit=len(nd) < ZIP_LIMIT)

    def new_name(pack, k, b):
        """True: add it; False: an identical copy is there already; a different one stops the run"""
        assert k == k.lower(), (pack, k)
        if k not in allnames:
            return True
        if existing(k) != b:
            raise SystemExit('%s: %s is in %s with other content - stage again' % (pack, k, allnames[k][0]))
        shared.append(k)
        return False

    # 1) the new packs
    for pack in NEW_PACKS:
        keys = [e['name'] for e in man['packs'].get(pack, [])]
        items = dict((k, staged(pack, k)) for k in keys)
        done = None
        for d, label in ((base, 'in base'), (None if check else out, 'in out')):
            if d and os.path.exists(os.path.join(d, pack + '.index')):
                f, v, ents = m2pack.read_index(os.path.join(d, pack + '.index'))
                dat = rd(os.path.join(d, pack + '.data'))
                have = dict((e['name'], m2pack.read_entry(dat, e)) for e in ents)
                if any(have.get(k, b) != b for k, b in items.items()) or set(have) - set(items):
                    raise SystemExit('%s is in %s with other content - stage again or drop it' % (pack, d))
                done = label
                break
        if done:
            report[pack] = done
            continue
        items = dict((k, b) for k, b in items.items() if new_name(pack, k, b))
        if check:
            size = sum(len(m2pack.encode_entry(b, ctype(k))) for k, b in items.items())
            report[pack] = dict(files=len(items), raw_mb=round(sum(len(b) for b in items.values()) / 1e6, 2),
                                data_mb=round(size / 1e6, 2), under_zip_limit=size < ZIP_LIMIT)
            continue
        report[pack] = write(pack, None, {}, dict((k, (b, ctype(k))) for k, b in items.items()), [], b'')
        assert report[pack]['under_zip_limit'], (pack, report[pack])

    # 2) property: the new names added (none of ours replaced)
    for pack in OLD_PACKS:
        src = src_of(pack)
        f, v, ents = m2pack.read_index(os.path.join(src, pack + '.index'))
        dat = rd(os.path.join(src, pack + '.data'))
        have = dict((e['name'], e) for e in ents)
        add = {}
        for e in man['packs'].get(pack, []):
            k = e['name']
            b = staged(pack, k)
            if k in have:
                if m2pack.read_entry(dat, have[k]) != b:
                    raise SystemExit('%s: %s is there with other content - stage again' % (pack, k))
                continue
            if new_name(pack, k, b):
                add[k] = (b, ctype(k))
        if not add:
            report[pack] = 'unchanged'
        elif check:
            report[pack] = dict(add=len(add))
        else:
            report[pack] = write(pack, src, {}, add, ents, dat)

    # 3) Index: the new packs at the end (after the build's own lines)
    if not check:
        ix_path = os.path.join(out, 'Index') if os.path.exists(os.path.join(out, 'Index')) else os.path.join(base, 'Index')
        ix = rd(ix_path)
        lines = [l.strip() for l in ix.replace(b'\r\n', b'\n').split(b'\n')]
        for pack in NEW_PACKS:
            if pack.encode() not in lines and (os.path.exists(os.path.join(out, pack + '.index')) or
                                               os.path.exists(os.path.join(base, pack + '.index'))):
                ix = ix.rstrip(b'\r\n') + b'\n*\n' + pack.encode() + b'\n'
        if ix != rd(ix_path) or ix_path != os.path.join(out, 'Index'):
            open(os.path.join(out, 'Index'), 'wb').write(ix)
            report['Index'] = 'written'

    # 4) the rows
    jobs = {'gamedata': [('gamedata/atlasinfo.txt', atlasinfo)]}
    for pack, files in jobs.items():
        src = src_of(pack)
        f, v, ents = m2pack.read_index(os.path.join(src, pack + '.index'))
        dat = rd(os.path.join(src, pack + '.data'))
        have = dict((e['name'], e) for e in ents)
        rep = {}
        for n, fn in files:
            b = m2pack.read_entry(dat, have[n])
            if data_from:
                for cand in (os.path.join(data_from, os.path.basename(n)), os.path.join(data_from, n)):
                    if os.path.exists(cand):
                        b = rd(cand)
                        break
            nb, changed = fn(b)
            if nb != m2pack.read_entry(dat, have[n]):
                rep[n] = nb
        if not rep:
            report[pack] = 'unchanged'
        elif check:
            report[pack] = dict(replace=sorted(rep))
        else:
            report[pack] = write(pack, src, rep, {}, ents, dat)
            report[pack]['replaced_names'] = sorted(rep)
    report['shared_identical'] = sorted(shared)
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
