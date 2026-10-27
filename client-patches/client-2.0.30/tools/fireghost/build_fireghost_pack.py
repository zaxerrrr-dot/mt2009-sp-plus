# -*- coding: utf-8 -*-
# MT2009_PLUS_FIRE_GHOST_V1 - the new client pack "fireghost": Ognisty Duch (2202, 2232 in Ognista Ziemia; every race
# with the npclist folder fire_ghost / fire_ghost1: 2202, 2232, 2623, 4220, 4300, 4460, 6001, 7020) no longer flares up
# into a growing fireball that stalls the client (one full CPU core).
#
# Why (the owner's package p-ognisty-duch, 22 October 2026, OPIS.txt): the base pack monster2's
# d:/ymir work/monster2/fire_ghost/fire_ghost.msm attaches d:/ymir work/effect/monster2/fire_ghost_body.mse for good to
# Bip01 (AttachingData02, AttachingDataType 2, isAttaching 1), and that effect (pack etc) loops (CycleLoopEnable 1).
# The exe's CActorInstance::SetShape attaches the model's effects again without removing the old ones, so every
# re-attach (a player dying nearby, ...) adds one more never-ending copy. GF's set (pack gf_razador, which loses to
# monster2) has no lasting effect: each .msa fires a 1-second body effect.
#
# The pack: the package's pliki/ (38 files, copied here under pliki/ as data; fireghost_files.json holds the package's
# names, sizes, sha256 and entry types read back from its mt_duch.index / mt_duch.data):
#   d:/ymir work/monster2/fire_ghost/*   GF's full set from gf_razador (.gr2, .msa, fire_ghost.msm, fire_ghost1.msm,
#                                        .dds, motlist.txt, fire_ghost_lod_01.gr2); the 12 .msa name the effect below
#   d:/ymir work/effect/monster2/fire_ghost_body_gf.mse   GF's body effect (1 s, CycleLoopEnable 0) under a new name -
#                                        the looping fire_ghost_body.mse stays for 2009_recycle_monster (2281)
# The exe's file dict keeps the first pack that registers a name, so the pack's Index line goes FIRST (the "*" +
# "fireghost" pair right after "PACK"), ahead of monster2, etc and gf_razador. The exe fix (client-patches/exe/GameLib/
# ActorInstanceData.cpp, the same marker) removes the duplicates for any model; this pack is enough for the old exe.
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/fireghost/build_fireghost_pack.py <BASE pack dir> <OUT pack dir> [--check]
#
# clientY.sh: after the last pack builder (buffi), before the verify loop:
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/fireghost/build_fireghost_pack.py $C/azbase \
#     $C/out/pack > $C/fireghost.json
# then fireghost/verify_fireghost.py on OUT. BASE: the client's packs so far (Index is read from OUT if an earlier step
# wrote one there, else from BASE); OUT: where fireghost.index / fireghost.data and the Index go. --check measures only.
# Every entry written is read back. Idempotent: a pack in OUT with the same content gives "unchanged" (one with other
# content is rebuilt); the Index line is not added twice.
import hashlib
import json
import os
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')

PACK = 'fireghost'
AFTER = b'PACK'
DATA = os.path.join(HERE, 'pliki')
MANIFEST = os.path.join(HERE, 'fireghost_files.json')
NEW_EFFECT = 'd:/ymir work/effect/monster2/fire_ghost_body_gf.mse'
OLD_EFFECT = b'fire_ghost_body.mse'


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
        raise SystemExit('pliki/ differs from fireghost_files.json: extra %s, missing %s'
                         % (sorted(on_disk - set(m)), sorted(set(m) - on_disk)))
    for name, w in sorted(m.items()):
        b = open(os.path.join(DATA, name[3:]), 'rb').read()
        if len(b) != w['size'] or hashlib.sha256(b).hexdigest() != w['sha256']:
            raise SystemExit('%s: not the package\'s file' % name)
        out[name] = (b, w['ctype'])
    # the point of the fix: no .msa / .msm names the looping effect, the new effect does not loop
    for name, (b, c) in out.items():
        if name.endswith(('.msa', '.msm')):
            assert OLD_EFFECT not in b.lower(), name
        if name.endswith('.msm'):
            assert b'AttachingDataType    2' not in b, name
    assert b'CycleLoopEnable         1' not in out[NEW_EFFECT][0], NEW_EFFECT
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

    # names other listed packs carry too (the pack must win over them - its Index line goes first)
    others = {}
    for d in (base, out):
        for p in sorted(f[:-6] for f in os.listdir(d) if f.endswith('.index')):
            if p == PACK:
                continue
            for e in m2pack.read_index(os.path.join(d, p + '.index'))[2]:
                if e['name'] in want:
                    others.setdefault(p, set()).add(e['name'])
    report['overrides'] = dict((p, len(n)) for p, n in sorted(others.items()))

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

    # Index: "*" + "fireghost" right after "PACK" (the first pack the exe registers)
    if not check:
        ix_path = os.path.join(out, 'Index') if os.path.exists(os.path.join(out, 'Index')) else os.path.join(base, 'Index')
        ix = rd(ix_path)
        nl = b'\r\n' if b'\r\n' in ix else b'\n'
        lines = ix.replace(b'\r\n', b'\n').split(b'\n')
        stripped = [l.strip() for l in lines]
        if stripped[0] != AFTER:
            raise SystemExit('Index: the first line is not PACK')
        if PACK.encode() in stripped:
            if stripped.index(PACK.encode()) != 2:
                raise SystemExit('Index: %s is not the first pack - remove its line and run again' % PACK)
            new = ix
        else:
            lines[1:1] = [b'*', PACK.encode()]
            new = nl.join(lines)
        if new != ix or ix_path != os.path.join(out, 'Index'):
            open(os.path.join(out, 'Index'), 'wb').write(new)
            report['Index'] = 'written'
        else:
            report['Index'] = 'unchanged'
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
