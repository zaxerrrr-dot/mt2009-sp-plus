# MT2009_PLUS_AREZZO_COSTUME_SETS_V1 - the client build's part for the Arezzo costume sets: the new
# packs az_cost01..NN (the models, textures, effects and icons our client lacks, staged by
# build_azcostume.py --stage under <staging>/add/<pack>/<in-pack path>, "d_/" = "d:/"), their
# lines at the end of pack/Index, and the rows in the gamedata and dbdata packs
# (patch_azcostume_client.py on plain copies of their files; the gamedata pack also gets the new
# gamedata/shiningtable.txt).  For the builder of the next client (a copy of buildNN.py): run this
# after the build's own packs, on its OUT, or merge its three steps into the build script.
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/azcostume/build_azcostume_packs.py \
#     <BASE pack dir> <OUT pack dir> <staging dir> [--data <dir with gamedata/item_list.txt and
#     locale/pl/itemdesc.txt to start from, e.g. the build's patched data dir>]
#   ... build_azcostume_packs.py <BASE> - <staging> --check      # measure only, writes nothing
#
# BASE = the full pack set the build starts from (e.g. c55/pack), OUT = where the build writes
# changed packs (az_cost*, gamedata, dbdata, Index).  A gamedata / dbdata pack already in OUT
# (the build changed it) is the one patched.  Every entry written is read back; an added name
# must be new to the whole BASE.  Idempotent.
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


def ctype(name):
    return 2 if name.endswith(TEXT) else 1


def main():
    import m2pack
    import packlib
    import patch_azcostume_client as pc
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    check = '--check' in sys.argv
    data_from = sys.argv[sys.argv.index('--data') + 1] if '--data' in sys.argv else None
    if data_from:
        args.remove(data_from)
    base, out, staging = args[:3]
    d = json.load(open(os.path.join(HERE, 'azcostume_items.json'), encoding='utf-8'))
    rd = packlib.rd
    allnames = {}
    for p in sorted(f[:-6] for f in os.listdir(base) if f.endswith('.index')):
        for e in m2pack.read_index(os.path.join(base, p + '.index'))[2]:
            allnames.setdefault(e['name'], p)
    tmpl = m2pack.read_index(os.path.join(base, 'az_mobs.index'))[2][-1]['raw']
    report = {}
    # 1) the new packs
    for pack, keys in sorted(d['packs'].items()):
        add = {}
        for k in keys:
            src = os.path.join(staging, 'add', pack, k.replace('d:/', 'd_/', 1))
            assert k == k.lower() and k not in allnames, (pack, k, allnames.get(k))
            add[k] = (rd(src), ctype(k))
        if check:
            size = sum(len(m2pack.encode_entry(b, c)) for b, c in add.values())
            report[pack] = dict(files=len(add), raw_mb=round(sum(len(b) for b, c in add.values()) / 1e6, 1),
                                data_mb=round(size / 1e6, 1), under_zip_limit=size < ZIP_LIMIT)
            continue
        if os.path.exists(os.path.join(base, pack + '.index')):
            raise SystemExit('%s is in BASE already - this build has it; nothing to add' % pack)
        r = packlib.repack_add_typed(None, None, {}, add, os.path.join(out, pack + '.index'), os.path.join(out, pack + '.data'), tmpl)
        f, v, ents = m2pack.read_index(os.path.join(out, pack + '.index'))
        nd = rd(os.path.join(out, pack + '.data'))
        for e in ents:
            assert zlib.crc32(nd[e['pos']:e['pos'] + e['size']]) & 0xffffffff == e['dcrc'], (pack, e['name'])
            assert m2pack.read_entry(nd, e) == add[e['name']][0], (pack, e['name'])
        report[pack] = dict(added=r[1], data_mb=round(len(nd) / 1e6, 1), under_zip_limit=len(nd) < ZIP_LIMIT)
    if check:
        print(json.dumps(report, indent=1))
        return
    # 2) Index: the new packs at the end (after the build's own lines)
    ix_path = os.path.join(out, 'Index') if os.path.exists(os.path.join(out, 'Index')) else os.path.join(base, 'Index')
    ix = rd(ix_path)
    # MT2009_PLUS_AREZZO_COSTUME_SETS_V2: an az_costNN of an earlier (V1) run that this list no longer has
    # (V1 had 15 packs, V2 14) leaves Index and OUT - its "*" line with it
    import re
    lines = ix.replace(b'\r\n', b'\n').split(b'\n')
    stale = set(l.strip() for l in lines if re.match(rb'^az_cost\d+$', l.strip()) and l.strip().decode() not in d['packs'])
    if stale:
        ixl = ix.split(b'\n')
        keep = []
        for l in ixl:
            if l.strip() in stale and keep and keep[-1].strip() == b'*':
                keep.pop()
                continue
            keep.append(l)
        ix = b'\n'.join(keep)
        for s in sorted(stale):
            for ext in ('.index', '.data'):
                f = os.path.join(out, s.decode() + ext)
                if os.path.exists(f):
                    os.remove(f)
        print('removed stale packs (V1) from Index and OUT: %s' % ', '.join(sorted(x.decode() for x in stale)))
    for pack in sorted(d['packs']):
        if (b'\n' + pack.encode() + b'\n') not in ix + b'\n':
            ix = ix.rstrip(b'\r\n') + b'\n*\n' + pack.encode() + b'\n'
    open(os.path.join(out, 'Index'), 'wb').write(ix)
    # 3) the rows: gamedata (tables, item_list, item_scale, 8 msm, + shiningtable.txt) and dbdata (itemdesc)
    work = os.path.join(out, '.azcostume-data')
    names = {'gamedata': ['gamedata/gf_official_costumes.txt', 'gamedata/costume_attr_items.txt', 'gamedata/item_list.txt',
                          'gamedata/item_scale.txt'] + ['gamedata/%s.msm' % r for r in pc.RACES],
             'dbdata': ['locale/pl/itemdesc.txt']}
    packs = {}
    for pack, files in names.items():
        src = out if os.path.exists(os.path.join(out, pack + '.index')) else base
        f, v, ents = m2pack.read_index(os.path.join(src, pack + '.index'))
        dat = rd(os.path.join(src, pack + '.data'))
        have = dict((e['name'], e) for e in ents)
        packs[pack] = (src, have, dat, ents)
        for n in files:
            b = m2pack.read_entry(dat, have[n])
            if data_from and os.path.exists(os.path.join(data_from, n)):
                b = rd(os.path.join(data_from, n))
            os.makedirs(os.path.dirname(os.path.join(work, n)), exist_ok=True)
            open(os.path.join(work, n), 'wb').write(b)
    pc.patch(work)
    for pack, files in names.items():
        src, have, dat, ents = packs[pack]
        rep = dict((n, rd(os.path.join(work, n))) for n in files)
        rep = dict((n, b) for n, b in rep.items() if m2pack.read_entry(dat, have[n]) != b)
        add = {}
        if pack == 'gamedata':
            sh = rd(os.path.join(work, 'gamedata/shiningtable.txt'))
            if 'gamedata/shiningtable.txt' in have:
                if m2pack.read_entry(dat, have['gamedata/shiningtable.txt']) != sh:
                    rep['gamedata/shiningtable.txt'] = sh
            else:
                add['gamedata/shiningtable.txt'] = (sh, 2)
        if not rep and not add:
            report[pack] = 'unchanged'
            continue
        tmp_i, tmp_d = os.path.join(out, pack + '.index.az'), os.path.join(out, pack + '.data.az')
        r = packlib.repack_add_typed(os.path.join(src, pack + '.index'), os.path.join(src, pack + '.data'), rep, add,
                                     tmp_i, tmp_d, ents[-1]['raw'])
        os.replace(tmp_i, os.path.join(out, pack + '.index'))
        os.replace(tmp_d, os.path.join(out, pack + '.data'))
        f, v, nw = m2pack.read_index(os.path.join(out, pack + '.index'))
        nd = rd(os.path.join(out, pack + '.data'))
        got = dict((e['name'], m2pack.read_entry(nd, e)) for e in nw)
        for n, b in list(rep.items()) + [(k, b) for k, (b, c) in add.items()]:
            assert got[n] == b, (pack, n)
        for e in ents:
            if e['name'] not in rep:
                assert got[e['name']] == m2pack.read_entry(dat, e), (pack, e['name'])
        report[pack] = dict(replaced=sorted(rep), added=sorted(add), entries=len(nw))
    import shutil
    shutil.rmtree(work, ignore_errors=True)
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
