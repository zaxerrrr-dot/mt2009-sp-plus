# -*- coding: utf-8 -*-
# MT2009_PLUS_AUTOHUNT_TEST_V1 - the new client pack "autohunttest": the ground circle of the TEST auto hunt (Alt+H, root
# uiautohunt_test.py; the exe draws it with player.AutoHuntTestShowRange, client-patches/exe Mt2009AutoHuntTest.cpp):
#   d:/ymir work/effect/etc/auto_hunt/auto_hunt_range_01.mse   the effect (3 rings of the mesh below)
#   d:/ymir work/effect/etc/auto_hunt/auto_hunt_range_01.mde   the ring mesh (names the .dds by its full path)
#   d:/ymir work/effect/etc/auto_hunt/auto_hunt_range_01.dds   its texture
# and the TEST window's pictures (root uiscript/autohunttest*.py, uiautohunt_test.py):
#   d:/ymir work/ui/game/windows/auto_system_*.sub (11), d:/ymir work/ui/game/auto_hunting/*.sub (9)
#   d:/ymir work/ui/game/auto_hunting/auto_hunt_windows.dds   the atlas they cut (the package's ui/windows.dds)
# from the owner's package "Oto Av" (28 October 2026; pliki/ holds them, autohunt_test_files.json their sizes, sha256 and
# entry types). The effect is byte for byte GF 26.1.11's. The pictures: 3.0.4 shipped none (it counted the exe smoke
# client's etc pack, which is NOT the players' etc) and Alt+H died on "Failed to load image .../auto_system_edit_line.sub".
# The players' base etc has an OLDER d:/ymir work/ui/windows.dds that other windows' .sub cut - so the package's atlas
# goes in under its own name and every .sub's image line names it ("game/auto_hunting/auto_hunt_windows.dds": a version
# 1.0 .sub opens "d:/ymir work/ui/" + image); package_sha256 in the json = the package's own .sub bytes.
# Index line goes LAST (tools/uicheck/check_ui_assets.py checks every picture against the players' packs).
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/autohunt_test/build_autohunt_test_packs.py <BASE pack dir> <OUT pack dir> [--check]
#
# clientY.sh: after the last pack builder (fireghost), before the verify loop:
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/autohunt_test/build_autohunt_test_packs.py $C/azbase \
#     $C/out/pack > $C/autohunttest.json
# then autohunt_test/verify_autohunt_test.py on OUT. BASE: the client's packs so far (Index is read from OUT if an earlier
# step wrote one there, else from BASE); OUT: where autohunttest.index / autohunttest.data and the Index go. --check
# measures only. Every entry written is read back. Idempotent: a pack in OUT with the same content gives "unchanged"; the
# Index line is not added twice.
import hashlib
import json
import os
import re
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')

PACK = 'autohunttest'
DATA = os.path.join(HERE, 'pliki')
MANIFEST = os.path.join(HERE, 'autohunt_test_files.json')
EFFECT = 'd:/ymir work/effect/etc/auto_hunt/auto_hunt_range_01.mse'
MESH = 'd:/ymir work/effect/etc/auto_hunt/auto_hunt_range_01.mde'
TEXTURE = 'd:/ymir work/effect/etc/auto_hunt/auto_hunt_range_01.dds'
ATLAS = 'd:/ymir work/ui/game/auto_hunting/auto_hunt_windows.dds'


def manifest():
    return json.load(open(MANIFEST))['files']


def items():
    """{name: (bytes, ctype)} from pliki/, checked against the package's names, sizes and sha256"""
    m = manifest()
    out = {}
    on_disk = set()
    for root, dirs, files in os.walk(DATA):
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), DATA).replace(os.sep, '/')
            on_disk.add('d:/' + rel)
    if on_disk != set(m):
        raise SystemExit('pliki/ differs from autohunt_test_files.json: extra %s, missing %s'
                         % (sorted(on_disk - set(m)), sorted(set(m) - on_disk)))
    for name, w in sorted(m.items()):
        b = open(os.path.join(DATA, name[3:]), 'rb').read()
        if len(b) != w['size'] or hashlib.sha256(b).hexdigest() != w['sha256']:
            raise SystemExit('%s: not the package\'s file' % name)
        out[name] = (b, w['ctype'])
    # the chain the exe follows: the effect names the mesh (next to it), the mesh the texture (full path)
    assert re.search(rb'MeshFileName\s+"auto_hunt_range_01\.mde"', out[EFFECT][0]), EFFECT
    assert b'effect\\etc\\auto_hunt\\auto_hunt_range_01.dds' in out[MESH][0].lower(), MESH
    assert out[TEXTURE][0][:4] == b'DDS ', TEXTURE
    # the window's .sub cut the renamed atlas, which is in the pack
    assert out[ATLAS][0][:4] == b'DDS ', ATLAS
    subs = [k for k in out if k.endswith('.sub')]
    assert len(subs) == 20, len(subs)
    for k in subs:
        assert re.search(rb'(?im)^version\s+1\.0', out[k][0]) and re.search(
            rb'(?im)^image\s+"game/auto_hunting/auto_hunt_windows\.dds"', out[k][0]), k
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

    # the same names in other listed packs (a base install's etc would carry them; the chain's packs do not)
    others = {}
    for d in (base, out):
        for p in sorted(f[:-6] for f in os.listdir(d) if f.endswith('.index')):
            if p == PACK:
                continue
            for e in m2pack.read_index(os.path.join(d, p + '.index'))[2]:
                if e['name'] in want:
                    others.setdefault(p, set()).add(e['name'])
    report['also_in'] = dict((p, len(n)) for p, n in sorted(others.items()))

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

    # Index: "*" + "autohunttest" at the end (same bytes as etc - the order does not matter)
    if not check:
        ix_path = os.path.join(out, 'Index') if os.path.exists(os.path.join(out, 'Index')) else os.path.join(base, 'Index')
        ix = rd(ix_path)
        nl = b'\r\n' if b'\r\n' in ix else b'\n'
        lines = ix.replace(b'\r\n', b'\n').split(b'\n')
        stripped = [l.strip() for l in lines]
        if stripped[0] != b'PACK':
            raise SystemExit('Index: the first line is not PACK')
        if PACK.encode() in stripped:
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
