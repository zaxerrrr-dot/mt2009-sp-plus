# -*- coding: utf-8 -*-
# MT2009_PLUS_RING_EFFECTS_V1 - the new client pack "ringfx": the equip effects of the rings / medal / candies / pendants
# (server-patches/ringfx sends SE_EQUIP_WILL_RING..SE_EQUIP_GUARD_PENDANT 55-63 when one is put on; the exe shows
# EFFECT_*_EQUIP - client-patches/exe, ENABLE_MT2009_RING_EFFECTS, PythonPlayerSettingsModule.cpp).
#
# Seven of the nine effects are the official files of the GF client 26.1.11, already in our install's etc pack with the
# same bytes (verify_ringfx.py checks them): 71148 buff_item5.mse, 71158 buff_symbol1.mse, 71180 buff_item16.mse,
# 71188 buff_item8.mse, 71199 buff_item10.mse, 71202 buff_item13.mse, 72054 buff_item14.mse (+ their textures and
# buff_item1.mde). The uploaded pack "offical_ring" holds the same effects under other names (will_ring.mse = buff_item5,
# blue_candy.dds = candy3.dds, ...) - those are not shipped. Only the two it has and GF has not go into this pack
# (pliki/, ringfx_files.json holds their names, sizes, sha256 and entry types; the uploaded pack's bytes):
#   d:/ymir work/effect/etc/buff/deadly_ring.mse + magic_ring2.dds     71149 Pierscien Smierc. Mocy
#   d:/ymir work/effect/etc/buff/green_candy.mse + green_candy.dds     71181 (the green candy)
# The pack's Index line goes LAST and its four names are in no other pack (a listed pack would win - the exe's file dict
# keeps the first pack that registers a name): the build stops if one is.
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/ringfx/build_ringfx_packs.py <BASE pack dir> <OUT pack dir> [--check]
#
# clientY.sh: after the last pack builder (gaya2), before the verify loop:
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/ringfx/build_ringfx_packs.py $C/azbase \
#     $C/out/pack > $C/ringfx.json
# then ringfx/verify_ringfx.py on OUT (in the verify loop). BASE: the client's packs so far (Index is read from OUT if
# an earlier step wrote one there, else from BASE); OUT: where ringfx.index / ringfx.data and the Index go. --check
# measures only. Every entry written is read back. Idempotent: a pack in OUT with the same content gives "unchanged"
# (one with other content is rebuilt); the Index line is not added twice.
import hashlib
import json
import os
import re
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')

PACK = 'ringfx'
DATA = os.path.join(HERE, 'pliki')
MANIFEST = os.path.join(HERE, 'ringfx_files.json')
EFFECTS = ('d:/ymir work/effect/etc/buff/deadly_ring.mse', 'd:/ymir work/effect/etc/buff/green_candy.mse')
# the install's etc pack (not in the build chain's BASE): its names count as "other packs" too
ETC_DEFAULT = '/opt/metin2/cache/exebuild/smoke/client/pack'


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
        raise SystemExit('pliki/ differs from ringfx_files.json: extra %s, missing %s'
                         % (sorted(on_disk - set(m)), sorted(set(m) - on_disk)))
    out = {}
    for name, w in sorted(m.items()):
        b = open(os.path.join(DATA, name[3:]), 'rb').read()
        if len(b) != w['size'] or hashlib.sha256(b).hexdigest() != w['sha256']:
            raise SystemExit('%s: not the manifest\'s file' % name)
        out[name] = (b, w['ctype'])
    # an equip effect: plays once (like buff_item1-16), no loop
    for eff in EFFECTS:
        assert not re.search(rb'CycleLoopEnable\s+1', out[eff][0]), eff
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

    # names other packs carry too - they would win (this pack's Index line is the last), so none may
    others = {}
    etc = ETC_DEFAULT if os.path.exists(os.path.join(ETC_DEFAULT, 'etc.index')) else None
    for d in (base, out) + ((etc,) if etc else ()):
        for p in sorted(f[:-6] for f in os.listdir(d) if f.endswith('.index')):
            if p == PACK:
                continue
            for e in m2pack.read_index(os.path.join(d, p + '.index'))[2]:
                if e['name'] in want:
                    others.setdefault(p, set()).add(e['name'])
    report['also_in'] = dict((p, sorted(n)) for p, n in sorted(others.items()))
    if others:
        raise SystemExit('ringfx: names already in other packs (they would win): %s' % report['also_in'])

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

    # Index: "*" + "ringfx" at the end
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
