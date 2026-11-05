# -*- coding: utf-8 -*-
# MT2009_PLUS_ENERGY_V1 - the new client pack "energia": the pictures of the energy bar of System Energii (Krysztal
# Energii 51002; server-patches/energia). The bar's script (locale/pl/ui/energybar.py, uiscript/energybar.py) and its
# code (root uitaskbar.py EnergyBar, interfacemodule.py - built by build57 from client-2.0.30/root) are in our packs;
# the four pictures they name were not:
#   d:/ymir work/ui/pattern/energygauge/energygauge_base.tga   the frame
#   d:/ymir work/ui/pattern/energygauge/gauge_full.tga         energy, more than 15 % of the 2 hours left
#   d:/ymir work/ui/pattern/energygauge/gauge_hungry.tga       energy, under 15 % left
#   d:/ymir work/ui/pattern/energygauge/gauge_empty.tga        no energy
# pliki/: the GF client 26.1.11's own bytes (energia_files.json: names, sizes, sha256, entry types) - the same bytes
# as the owner's uploaded energy package. The pack's Index line goes LAST: it overrides nothing.
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/energia/build_energia_pack.py <BASE pack dir> <OUT pack dir> [--check]
#
# clientY.sh: after the last pack builder, before the npclist and the verify loop:
#   S_energia_pack() { docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/energia/build_energia_pack.py \
#     $C/azbase $C/out/pack; }; step energia_pack $C/energia.json S_energia_pack
# then energia/verify_energia.py on OUT (in the verify loop). --check measures only. Every entry written is read back.
# Idempotent: a pack in OUT with the same content gives "unchanged"; the Index line is not added twice.
import hashlib
import json
import os
import re
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')

PACK = 'energia'
DATA = os.path.join(HERE, 'pliki')
MANIFEST = os.path.join(HERE, 'energia_files.json')


def manifest():
    return json.load(open(MANIFEST))['files']


def items():
    """{name: (bytes, ctype)} from pliki/, checked against the manifest's names, sizes and sha256"""
    m = manifest()
    on_disk = set()
    for root, dirs, files in os.walk(DATA):
        for f in files:
            on_disk.add('d:/' + os.path.relpath(os.path.join(root, f), DATA).replace(os.sep, '/'))
    if on_disk != set(m):
        raise SystemExit('pliki/ differs from energia_files.json: extra %s, missing %s'
                         % (sorted(on_disk - set(m)), sorted(set(m) - on_disk)))
    out = {}
    for name, w in sorted(m.items()):
        b = open(os.path.join(DATA, name[3:]), 'rb').read()
        if len(b) != w['size'] or hashlib.sha256(b).hexdigest() != w['sha256']:
            raise SystemExit('%s: not the manifest\'s file' % name)
        out[name] = (b, w['ctype'])
    # Targa pictures (RGBA, run-length) the bar's script names
    for name, (b, c) in out.items():
        assert b[2] in (2, 10) and b[16] == 32, name
    return out


def main():
    import m2pack
    import packlib
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    check = '--check' in sys.argv
    base, out = args[:2]
    rd = packlib.rd
    want = items()
    raw = dict((k, b) for k, (b, c) in want.items())
    report = {}

    # names other listed packs carry too (they win: this pack's Index line is the last)
    others = {}
    for d in (base, out):
        for p in sorted(f[:-6] for f in os.listdir(d) if f.endswith('.index')):
            if p == PACK:
                continue
            for e in m2pack.read_index(os.path.join(d, p + '.index'))[2]:
                if e['name'] in want:
                    others.setdefault(p, set()).add(e['name'])
    report['also_in'] = dict((p, sorted(n)) for p, n in sorted(others.items()))

    built = False
    if os.path.exists(os.path.join(out, PACK + '.index')):
        f, v, ents = m2pack.read_index(os.path.join(out, PACK + '.index'))
        dat = rd(os.path.join(out, PACK + '.data'))
        if (dict((e['name'], m2pack.read_entry(dat, e)) for e in ents) == raw and
                all(e['ctype'] == want[e['name']][1] for e in ents)):
            report[PACK] = 'unchanged'
            built = True
    if not built:
        if check:
            size = sum(len(m2pack.encode_entry(b, c)) for b, c in want.values())
            report[PACK] = dict(files=len(want), data_kb=round(size / 1e3, 1))
        else:
            tmpl = m2pack.read_index(os.path.join(base, 'gf_mobs.index'))[2][-1]['raw']
            ti, td = os.path.join(out, PACK + '.index.tmp'), os.path.join(out, PACK + '.data.tmp')
            packlib.repack_add_typed(None, None, {}, want, ti, td, tmpl)
            os.replace(ti, os.path.join(out, PACK + '.index'))
            os.replace(td, os.path.join(out, PACK + '.data'))
            f, v, ents = m2pack.read_index(os.path.join(out, PACK + '.index'))
            dat = rd(os.path.join(out, PACK + '.data'))
            got = {}
            for e in ents:
                assert zlib.crc32(dat[e['pos']:e['pos'] + e['size']]) & 0xffffffff == e['dcrc'], e['name']
                assert e['fcrc'] == zlib.crc32(e['name'].encode('cp1252')) & 0xffffffff, e['name']
                assert e['ctype'] == want[e['name']][1], e['name']
                got[e['name']] = m2pack.read_entry(dat, e)
            assert got == raw, 'read-back differs'
            report[PACK] = dict(entries=len(ents), data_kb=round(len(dat) / 1e3, 1))

    # Index: "*" + "energia" at the end
    if not check:
        ix_path = os.path.join(out, 'Index') if os.path.exists(os.path.join(out, 'Index')) else os.path.join(base, 'Index')
        ix = rd(ix_path)
        nl = b'\r\n' if b'\r\n' in ix else b'\n'
        lines = ix.replace(b'\r\n', b'\n').split(b'\n')
        if lines[0].strip() != b'PACK':
            raise SystemExit('Index: the first line is not PACK')
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
