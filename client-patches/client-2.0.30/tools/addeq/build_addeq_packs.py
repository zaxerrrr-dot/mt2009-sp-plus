# -*- coding: utf-8 -*-
# MT2009_PLUS_ADDEQ_V1 - the client build's part for Druga strona ekwipunku (server-patches/addeq/README.md):
#   1) a new pack "addeq": the support skill's icon d:/ymir work/ui/skill/common/support/change_equipment.sub (GF 26.1.11's
#      name and place) over d:/ymir work/ui/addeq_change_equipment.dds - the icon's 32 x 32 DXT5 blocks cut out of GF's
#      newskillcommon.dds (left 32, top 544; ours of that name is an older atlas without it), kept in this directory
#      (addeq_change_equipment.dds) - the exe looks for a .sub's image in d:/ymir work/ui/ (../yriposty);
#   2) its line at the end of pack/Index;
#   3) the existing packs "gamedata" (gamedata/item_list.txt) and "dbdata" (gamedata/item_proto, locale/pl/itemdesc.txt,
#      locale/pl/skilldesc.txt, gamedata/skilltable.txt) - patch_addeq_client.py: the unlock items 38306 / 76055 and the
#      skill 200 of tools/addeq/addeq.json.
# The items' icon (root/icon/item/38306.tga, GF 26.1.11 = the package's) and root/uiaddeq.py travel in client-2.0.30/root
# like every root change.
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/addeq/build_addeq_packs.py <BASE pack dir> <OUT pack dir> [--check]
#
# clientY.sh: after the kamienie line (it patches gamedata and dbdata too; on the same OUT a pack already there - an
# earlier step changed it - is the one patched):
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/addeq/build_addeq_packs.py $C/azbase $C/out/pack \
#     > $C/addeq.json
# then addeq/verify_addeq.py in the verify loop. A name the client has already (BASE, OUT) with the same bytes is left out
# of the new pack ("shared"); with other bytes the build stops. Every entry written is read back. Idempotent.
import json
import os
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, HERE)
PACK = 'addeq'
SUB = 'd:/ymir work/ui/skill/common/support/change_equipment.sub'
DDS = 'd:/ymir work/ui/addeq_change_equipment.dds'
DDS_FILE = os.path.join(HERE, 'addeq_change_equipment.dds')
TEXT = ('.txt', '.sub')
ZIP_LIMIT = 29 * 1024 * 1024


def ctype(name):
    return 2 if name.endswith(TEXT) else 1


def files():
    """the new pack's entries: name -> bytes"""
    sub = (b'title subImage\r\nversion 1.0\r\nimage "addeq_change_equipment.dds"\r\n'
           b'left 0\r\ntop 0\r\nright 32\r\nbottom 32\r\n')
    dds = open(DDS_FILE, 'rb').read()
    assert dds[:4] == b'DDS ' and dds[84:88] == b'DXT5' and len(dds) == 128 + 1024, DDS_FILE
    return {SUB: sub, DDS: dds}


def main():
    import m2pack
    import packlib
    import patch_addeq_client as pc
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    check = '--check' in sys.argv
    base, out = args[:2]
    rd = packlib.rd
    where = {}
    for d in (base, out):
        if not os.path.isdir(d):
            continue
        for p in sorted(f[:-6] for f in os.listdir(d) if f.endswith('.index')):
            if p == PACK:
                continue
            for e in m2pack.read_index(os.path.join(d, p + '.index'))[2]:
                where.setdefault(e['name'], (d, p, e))
    tmpl = m2pack.read_index(os.path.join(base, 'az_mobs.index'))[2][-1]['raw']
    datcache = {}

    def entry_bytes(d, p, e):
        if (d, p) not in datcache:
            datcache[(d, p)] = rd(os.path.join(d, p + '.data'))
        return m2pack.read_entry(datcache[(d, p)], e)

    def src_of(pack):
        return out if os.path.exists(os.path.join(out, pack + '.index')) else base

    report = {}

    def write(pack, src, rep, add, ents, dat):
        tmp_i, tmp_d = os.path.join(out, pack + '.index.adq'), os.path.join(out, pack + '.data.adq')
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

    # 1) the new pack
    items, shared = {}, []
    for k, b in sorted(files().items()):
        if k in where:
            if entry_bytes(*where[k]) != b:
                raise SystemExit('%s: %s is in %s/%s with other bytes' % (PACK, k, where[k][0], where[k][1]))
            shared.append(k)
            continue
        assert k == k.lower(), k
        items[k] = b
    done = [d for d in (base, out) if os.path.exists(os.path.join(d, PACK + '.index'))]
    skip = False
    if done:
        f, v, ents = m2pack.read_index(os.path.join(done[0], PACK + '.index'))
        dat = rd(os.path.join(done[0], PACK + '.data'))
        have = dict((e['name'], m2pack.read_entry(dat, e)) for e in ents)
        if have == items:
            report[PACK] = 'in base' if done[0] == base else 'in out'
            skip = True
        elif done[0] == out and not check:
            os.remove(os.path.join(out, PACK + '.index'))
            os.remove(os.path.join(out, PACK + '.data'))
        else:
            raise SystemExit('%s is in BASE with other content - drop it from BASE' % PACK)
    if not skip:
        if check:
            size = sum(len(m2pack.encode_entry(b, ctype(k))) for k, b in items.items())
            report[PACK] = dict(files=len(items), shared=len(shared), data_mb=round(size / 1e6, 2))
        else:
            report[PACK] = write(PACK, None, {}, dict((k, (b, ctype(k))) for k, b in items.items()), [], b'')
            report[PACK]['shared'] = shared
            assert report[PACK]['under_zip_limit'], report[PACK]

    # 2) Index: the new pack at the end
    if not check:
        ix_path = os.path.join(out, 'Index') if os.path.exists(os.path.join(out, 'Index')) else os.path.join(base, 'Index')
        ix = rd(ix_path)
        lines = [l.strip() for l in ix.replace(b'\r\n', b'\n').split(b'\n')]
        if PACK.encode() not in lines and (os.path.exists(os.path.join(out, PACK + '.index')) or
                                           os.path.exists(os.path.join(base, PACK + '.index'))):
            ix = ix.rstrip(b'\r\n') + b'\n*\n' + PACK.encode() + b'\n'
        if ix != rd(ix_path) or ix_path != os.path.join(out, 'Index'):
            open(os.path.join(out, 'Index'), 'wb').write(ix)
            report['Index'] = 'written'

    # 3) gamedata and dbdata: the items and the skill 200
    jobs = {'gamedata': [('gamedata/item_list.txt', pc.item_list)],
            'dbdata': [('gamedata/item_proto', pc.item_proto), ('locale/pl/itemdesc.txt', pc.itemdesc),
                       ('locale/pl/skilldesc.txt', pc.skilldesc), ('gamedata/skilltable.txt', pc.skilltable)]}
    for pack, jfiles in sorted(jobs.items()):
        src = src_of(pack)
        f, v, ents = m2pack.read_index(os.path.join(src, pack + '.index'))
        dat = rd(os.path.join(src, pack + '.data'))
        have = dict((e['name'], e) for e in ents)
        rep = {}
        for n, fn in jfiles:
            if n not in have:
                raise SystemExit('%s: %s is not in the pack' % (pack, n))
            b = m2pack.read_entry(dat, have[n])
            nb, changed = fn(b)
            if nb != b:
                rep[n] = nb
        if not rep:
            report[pack] = 'unchanged'
        elif check:
            report[pack] = dict(replace=sorted(rep))
        else:
            report[pack] = write(pack, src, rep, {}, ents, dat)
            report[pack]['replaced_names'] = sorted(rep)

    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
