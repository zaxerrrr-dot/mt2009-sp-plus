# -*- coding: utf-8 -*-
# MT2009_PLUS_JEWELS75_V1 - the new client pack "gf_ore": the Gameforge vein models of Rubin, Granat,
# Szmaragd and Szafir (races 30302 / 30303 / 30304 / 30305, which the bots' vein keeper stands in the Red
# Forest and the Grotto of Exile - playerbot_mining.h). npclist.txt already names them (30302 mineral2_ruby,
# 30303 mineral2_garnet, 30304 mineral2_bery, 30305 mineral2_sapphire; aliases "0 <name> mineral2"), so the
# exe looks for d:/ymir work/npc/mineral2/<name>.msm - a folder our packs do not carry and the old base
# client most likely lacks (it is newer Gameforge content). Taken as they are from the unpacked Gameforge
# 26.1.11 client (/opt/metin2/cache/gf/Gameforge_26.1.11/_client/d_/ymir work/npc/mineral2):
#   the four .msm and .gr2, the textures the models reference (ore_02.dds, ore_base_02.dds - read out of
#   the .gr2 with tcm/gf28's gfres.gr2_textures), motlist.txt, wait.msa and wait.gr2 (the one motion every
#   line of motlist.txt points at) - 13 files, 0.42 MB packed.
# The pack is new (an index/data pair of its own, entries typed as the other GF packs: text 2, binary 1) and
# its line goes at the end of pack/Index. Every entry written is read back.
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/gfore/build_gfore_pack.py <BASE pack dir> <OUT pack dir> [--check]
#
# BASE: the client's packs so far (to read Index from and to make sure no name is in another pack); OUT: where
# gf_ore.index / gf_ore.data and the Index go (an Index already in OUT - written by an earlier step - is the one
# extended). --check measures only. Idempotent: a BASE or OUT that has gf_ore with the same content gives
# "unchanged".
import json
import os
import sys
import zlib

sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')

PACK = 'gf_ore'
GF_DIR = '/opt/metin2/cache/gf/Gameforge_26.1.11/_client/d_/ymir work/npc/mineral2'
IN_PACK = 'd:/ymir work/npc/mineral2/'
FILES = (
    'mineral2_ruby.msm', 'mineral2_ruby.gr2',
    'mineral2_garnet.msm', 'mineral2_garnet.gr2',
    'mineral2_bery.msm', 'mineral2_bery.gr2',
    'mineral2_sapphire.msm', 'mineral2_sapphire.gr2',
    'ore_02.dds', 'ore_base_02.dds',
    'motlist.txt', 'wait.msa', 'wait.gr2',
)
TEXT = ('.txt', '.msa', '.msm')


def ctype(name):
    return 2 if name.endswith(TEXT) else 1


def main():
    import m2pack
    import packlib
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    check = '--check' in sys.argv
    base, out = args[:2]
    rd = packlib.rd
    items = dict((IN_PACK + f, rd(os.path.join(GF_DIR, f))) for f in FILES)
    report = {}

    # Already built (in OUT or BASE) with this content?
    for where in (out, base):
        if where != '-' and os.path.exists(os.path.join(where, PACK + '.index')):
            f, v, ents = m2pack.read_index(os.path.join(where, PACK + '.index'))
            dat = rd(os.path.join(where, PACK + '.data'))
            if dict((e['name'], m2pack.read_entry(dat, e)) for e in ents) != items:
                raise SystemExit('%s in %s has other content - remove it and run again' % (PACK, where))
            report[PACK] = 'unchanged (%s)' % where
            break
    else:
        others = {}
        for p in sorted(f[:-6] for f in os.listdir(base) if f.endswith('.index')):
            if p == PACK:
                continue
            for e in m2pack.read_index(os.path.join(base, p + '.index'))[2]:
                others.setdefault(e['name'], p)
        clash = dict((k, others[k]) for k in items if k in others)
        if clash:
            raise SystemExit('names already in other packs: %s' % clash)
        if check:
            size = sum(len(m2pack.encode_entry(b, ctype(k))) for k, b in items.items())
            report[PACK] = dict(files=len(items), raw_mb=round(sum(map(len, items.values())) / 1e6, 2),
                                data_mb=round(size / 1e6, 2))
        else:
            tmpl = m2pack.read_index(os.path.join(base, 'gf_mobs.index'))[2][-1]['raw']
            ti, td = os.path.join(out, PACK + '.index.tmp'), os.path.join(out, PACK + '.data.tmp')
            packlib.repack_add_typed(None, None, {}, dict((k, (b, ctype(k))) for k, b in items.items()), ti, td, tmpl)
            os.replace(ti, os.path.join(out, PACK + '.index'))
            os.replace(td, os.path.join(out, PACK + '.data'))
            f, v, ents = m2pack.read_index(os.path.join(out, PACK + '.index'))
            dat = rd(os.path.join(out, PACK + '.data'))
            got = {}
            for e in ents:
                assert zlib.crc32(dat[e['pos']:e['pos'] + e['size']]) & 0xffffffff == e['dcrc'], e['name']
                assert e['fcrc'] == zlib.crc32(e['name'].encode('cp1252')) & 0xffffffff, e['name']
                got[e['name']] = m2pack.read_entry(dat, e)
            assert got == items, 'read-back differs'
            report[PACK] = dict(entries=len(ents), data_mb=round(len(dat) / 1e6, 2))

    # Index: the pack's line at the end.
    if not check:
        ix_path = os.path.join(out, 'Index') if os.path.exists(os.path.join(out, 'Index')) else os.path.join(base, 'Index')
        ix = rd(ix_path)
        lines = [l.strip() for l in ix.replace(b'\r\n', b'\n').split(b'\n')]
        new = ix if PACK.encode() in lines else ix.rstrip(b'\r\n') + b'\n*\n' + PACK.encode() + b'\n'
        if new != ix or ix_path != os.path.join(out, 'Index'):
            open(os.path.join(out, 'Index'), 'wb').write(new)
            report['Index'] = 'written'
        else:
            report['Index'] = 'unchanged'
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
