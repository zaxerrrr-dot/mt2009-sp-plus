# -*- coding: utf-8 -*-
# MT2009_PLUS_RIPOSTY_V1 - the client build's part for Riposty i Dopalacze (server-patches/riposty/README.md):
#   1) a new pack "yriposty": the skill window's icons d:/ymir work/ui/skill/passive/{p,pp}_<skill>_01..03.sub (GF 26.1.11's,
#      48 of them - the Lycan's salpoong left out) with their atlases renamed as the yskill9 builder does (the exe looks
#      for a .sub's image in d:/ymir work/ui/): the ripostes' SkillAssassin.dds is GF's 256x288 class atlas = the yskill9
#      pack's skill9_assassin.dds (the same bytes - Ameria's sources, GF's own are encrypted), the boosts' SkillPahe.dds
#      goes in as d:/ymir work/ui/yriposty_pahe.dds (Ameria's etc/ymir work/ui/skillpahe.dds, 256x128 DXT5);
#   2) its line at the end of pack/Index;
#   3) the existing pack "dbdata" (patch_yriposty_client.py): locale/pl/skilldesc.txt and gamedata/skilltable.txt - the
#      rows 221-228 and 236-243.
# root/riposty.py (in the root pack with the other root files) puts them in the skill window and writes their tooltips.
# Exe unchanged: job PASSIVE is the exe's ("passive" -> an active-type skill, icons under ui/skill/passive/), skill
# levels up to SKILL_MAX_NUM 265 come in the skill packet, slots 221-243 are free.
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/yriposty/build_yriposty_packs.py <BASE pack dir> <OUT pack dir> [--check]
#
# clientY.sh: after the yskill9 line (its skill9_assassin.dds is the ripostes' atlas; it patches OUT's dbdata as well):
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/yriposty/build_yriposty_packs.py $C/azbase $C/out/pack \
#     > $C/yriposty.json
# then verify_yriposty.py on OUT. A name the client has already (BASE, OUT) with the same bytes is left out of the new
# pack ("shared"); with other bytes the build stops. Every entry written is read back. Idempotent.
import json
import os
import re
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, HERE)
GF_PASSIVE = '/opt/metin2/cache/gf/Gameforge_26.1.11/_client/d_/ymir work/ui/skill/passive'
AMERIA_UI = '/opt/metin2/ameria/ameria-prj-2025/tools/FoxFSArchiver/source/etc/ymir work/ui'
PACK = 'yriposty'
ATLAS = {'skillassassin.dds': 'skill9_assassin.dds', 'skillpahe.dds': 'yriposty_pahe.dds'}
PAHE = 'd:/ymir work/ui/yriposty_pahe.dds'
TEXT = ('.txt', '.sub')
ZIP_LIMIT = 29 * 1024 * 1024


def ctype(name):
    return 2 if name.endswith(TEXT) else 1


def files():
    """the new pack's entries: name -> bytes"""
    import patch_yriposty_client as pc
    out = {}
    for icon in pc.ICONS:
        for g in (1, 2, 3):
            src = os.path.join(GF_PASSIVE, '%s_0%d.sub' % (icon, g))
            t = open(src, 'rb').read().decode('latin-1')
            m = re.search(r'^image\s+"([^"]+)"', t, re.M | re.I)
            assert m, src
            new = ATLAS[m.group(1).lower()]
            t = t[:m.start(1)] + new + t[m.end(1):]
            out['d:/ymir work/ui/skill/passive/%s_0%d.sub' % (icon, g)] = t.encode('latin-1')
    out[PAHE] = open(os.path.join(AMERIA_UI, 'skillpahe.dds'), 'rb').read()
    return out


def main():
    import m2pack
    import packlib
    import patch_yriposty_client as pc
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
        tmp_i, tmp_d = os.path.join(out, pack + '.index.yrp'), os.path.join(out, pack + '.data.yrp')
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

    # 3) dbdata: skilldesc and skilltable rows 221-228 / 236-243
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
