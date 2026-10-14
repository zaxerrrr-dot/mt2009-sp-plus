# -*- coding: utf-8 -*-
# MT2009_PLUS_SKILL9_V1 - the client build's part for the 9th skills of Yohara (server-patches/skill9/README.md):
#   1) the new pack(s) of yskill9_manifest.json "new_packs" (yskill9: the skills' motions on all 8 races, their
#      effects and sounds, the icons and their atlases - staged by stage_yskill9.py under <staging>/add/<pack>/...);
#   2) their lines at the end of pack/Index;
#   3) the existing pack "dbdata" (patch_yskill9_client.py): locale/pl/skilldesc.txt and gamedata/skilltable.txt -
#      the rows 176-182 and the passive skill Precyzja's 246, and its icon d:/ymir work/ui/skill/common/support/
#      hit_attribute.sub (a new dbdata entry; MT2009_PLUS_PRECISION_SKILL_V1).
# The exe must register the motions (client-patches/exe, MT2009_PLUS_SKILL9_V1 in PythonPlayerSettingsModule.cpp) and
# root/playersettingmodule.py puts the skill in the skill window (place 7).
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/yskill9/build_yskill9_packs.py <BASE pack dir> <OUT pack dir> <staging dir>
#   ... build_yskill9_packs.py <BASE> <OUT> <staging> --check      # measure only, writes nothing
#
# clientY.sh: after the ymaps3 line (any order after build57.py: it patches OUT's dbdata, the build's own),
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/yskill9/build_yskill9_packs.py $C/azbase $C/out/pack \
#     /opt/metin2/cache/yohara/yskill9-staging > $C/yskill9.json
# then verify_yskill9.py on OUT. A staged name the client has already (BASE, OUT - another builder's pack) with the same
# bytes is left out of the new pack (reported as "shared"); with other bytes the build stops. Every entry written is
# read back. Idempotent: a second run gives "in out"/"unchanged".
import json
import os
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, HERE)
TEXT = ('.txt', '.msa', '.msm', '.mse', '.mss', '.msenv', '.sub', '.prb', '.prd', '.pre', '.prt', '.py', '.ifl', '.pra',
        '.msf', '.mde')
ZIP_LIMIT = 29 * 1024 * 1024


def ctype(name):
    return 2 if name.endswith(TEXT) else 1


def main():
    import m2pack
    import packlib
    import patch_yskill9_client as pc
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    check = '--check' in sys.argv
    base, out, staging = args[:3]
    man = json.load(open(os.path.join(HERE, 'yskill9_manifest.json'), encoding='utf-8'))
    new_packs = man['new_packs']
    rd = packlib.rd
    where = {}
    for d in (base, out):
        if not os.path.isdir(d):
            continue
        for p in sorted(f[:-6] for f in os.listdir(d) if f.endswith('.index')):
            if p in new_packs:
                continue
            for e in m2pack.read_index(os.path.join(d, p + '.index'))[2]:
                where.setdefault(e['name'], (d, p, e))
    tmpl = m2pack.read_index(os.path.join(base, 'az_mobs.index'))[2][-1]['raw']
    datcache = {}

    def entry_bytes(d, p, e):
        if (d, p) not in datcache:
            datcache[(d, p)] = rd(os.path.join(d, p + '.data'))
        return m2pack.read_entry(datcache[(d, p)], e)

    def staged(pack, k):
        return rd(os.path.join(staging, 'add', pack, k.replace('d:/', 'd_/', 1)))

    def src_of(pack):
        return out if os.path.exists(os.path.join(out, pack + '.index')) else base

    report = {}

    def write(pack, src, rep, add, ents, dat):
        tmp_i, tmp_d = os.path.join(out, pack + '.index.ys9'), os.path.join(out, pack + '.data.ys9')
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

    # 1) the new packs
    for pack in new_packs:
        items, shared = {}, []
        for e in man['packs'][pack]:
            k = e['name']
            b = staged(pack, k)
            if k in where:
                d, p, ent = where[k]
                if entry_bytes(d, p, ent) != b:
                    raise SystemExit('%s: %s is in %s/%s with other bytes - stage again' % (pack, k, d, p))
                shared.append(k)
                continue
            assert k == k.lower(), k
            items[k] = b
        done = [d for d in (base, out) if os.path.exists(os.path.join(d, pack + '.index'))]
        if done:
            f, v, ents = m2pack.read_index(os.path.join(done[0], pack + '.index'))
            dat = rd(os.path.join(done[0], pack + '.data'))
            have = dict((e['name'], m2pack.read_entry(dat, e)) for e in ents)
            if have == items:
                report[pack] = 'in base' if done[0] == base else 'in out'
                continue
            if done[0] == out and not check:
                os.remove(os.path.join(out, pack + '.index'))
                os.remove(os.path.join(out, pack + '.data'))
            else:
                raise SystemExit('%s is in BASE with other content - stage again or drop it from BASE' % pack)
        if check:
            size = sum(len(m2pack.encode_entry(b, ctype(k))) for k, b in items.items())
            report[pack] = dict(files=len(items), shared=len(shared), raw_mb=round(sum(len(b) for b in items.values()) / 1e6, 2),
                                data_mb=round(size / 1e6, 2), under_zip_limit=size < ZIP_LIMIT)
            continue
        report[pack] = write(pack, None, {}, dict((k, (b, ctype(k))) for k, b in items.items()), [], b'')
        report[pack]['shared'] = shared
        assert report[pack]['under_zip_limit'], (pack, report[pack])

    # 2) Index: the new packs at the end
    if not check:
        ix_path = os.path.join(out, 'Index') if os.path.exists(os.path.join(out, 'Index')) else os.path.join(base, 'Index')
        ix = rd(ix_path)
        lines = [l.strip() for l in ix.replace(b'\r\n', b'\n').split(b'\n')]
        for pack in new_packs:
            if pack.encode() not in lines and (os.path.exists(os.path.join(out, pack + '.index')) or
                                               os.path.exists(os.path.join(base, pack + '.index'))):
                ix = ix.rstrip(b'\r\n') + b'\n*\n' + pack.encode() + b'\n'
        if ix != rd(ix_path) or ix_path != os.path.join(out, 'Index'):
            open(os.path.join(out, 'Index'), 'wb').write(ix)
            report['Index'] = 'written'

    # 3) dbdata: skilldesc and skilltable rows 176-182 and 246, Precyzja's icon
    pack = 'dbdata'
    src = src_of(pack)
    f, v, ents = m2pack.read_index(os.path.join(src, pack + '.index'))
    dat = rd(os.path.join(src, pack + '.data'))
    have = dict((e['name'], e) for e in ents)
    rep = {}
    for n, fn in (('locale/pl/skilldesc.txt', pc.skilldesc), ('gamedata/skilltable.txt', pc.skilltable)):
        b = m2pack.read_entry(dat, have[n])
        nb, changed = fn(b)
        if changed:
            rep[n] = nb
    # MT2009_PLUS_PRECISION_SKILL_V1: the support tab's icon of Precyzja (246) - a new dbdata entry (its atlas is the
    # yskill9 pack's skill9_common.dds); kept where another pack has it with the same bytes
    add = {}
    icon = pc.PRECISION_ICON
    if icon in have:
        if m2pack.read_entry(dat, have[icon]) != pc.PRECISION_ICON_SUB:
            rep[icon] = pc.PRECISION_ICON_SUB
    elif icon in where:
        if entry_bytes(*where[icon]) != pc.PRECISION_ICON_SUB:
            raise SystemExit('%s is in %s/%s with other bytes' % (icon, where[icon][0], where[icon][1]))
    else:
        add[icon] = (pc.PRECISION_ICON_SUB, ctype(icon))
    if not rep and not add:
        report[pack] = 'unchanged'
    elif check:
        report[pack] = dict(replace=sorted(rep), add=sorted(add))
    else:
        report[pack] = write(pack, src, rep, add, ents, dat)
        report[pack]['replaced_names'] = sorted(rep)
        report[pack]['added_names'] = sorted(add)

    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
