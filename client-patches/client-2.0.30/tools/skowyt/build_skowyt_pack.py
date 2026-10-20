# -*- coding: utf-8 -*-
# MT2009_PLUS_SKOWYT_CLIENT_V1 - the new client pack "skowyt": Smoczy Skowyt's (shaman skill 93) motion files
# d:/ymir work/{pc,pc2}/shaman/skill/paeryong{,_2,_3,_4}.msa (the four grades, both shaman models), so the burst
# (paeryong*.mse) shows ONCE, where the skill strikes.
#
# Why ("animacja pojawia sie dwukrotnie - raz na celu i raz na postaci", the owner, 15 October): the base client's
# paeryong*.msa play the burst as MotionEventType 1 (EFFECT) on the Shaman, wherever the skill was aimed, and since
# 28 September the server (MT2009_PLUS_DRAGON_ROAR_EFFECT_V1) sent a second copy onto the target. Here the event is
# MotionEventType 10 (EFFECT_TO_TARGET, FollowingEnable 1): the exe (GameLib/ActorInstanceMotionEvent.cpp,
# ProcessMotionEventEffectToTargetEvent) attaches the effect to the caster's fly target - the selected target, or
# the Shaman itself when it has none (skilldesc CAN_USE_FOR_ME, patch_skowyt_client.py). The server no longer sends
# its copy (MT2009_PLUS_DRAGON_ROAR_EFFECT_V2, server-patches/playerqol; for a bot it sends the fly target).
# The files are the classic ones (same motion, duration, start time, effect file, screen waving of the higher
# grades) with the effect event changed and the two MotionEventType 4 (client-only splash, EnableHitProcess 0:
# pushes and hit sparks on what stands round the Shaman, not where the skill lands) left out - msa/{pc,pc2}/.
#
# The base packs pc_2 / pc2_2 carry the same names; the exe's file dict keeps the first pack that registers a name,
# so the pack's Index line goes BEFORE "pc2_1" (the first pc pack). Every entry written is read back.
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/skowyt/build_skowyt_pack.py <BASE pack dir> <OUT pack dir> [--check]
#
# clientY.sh: after the last Yohara pack line (before the verify loop):
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/skowyt/build_skowyt_pack.py $C/azbase $C/out/pack \
#     > $C/skowyt.json
# BASE: the client's packs so far (Index is read from OUT if an earlier step wrote one there, else from BASE; no other
# pack there may carry the names); OUT: where skowyt.index / skowyt.data and the Index go. --check measures only.
# Idempotent: a pack in OUT with the same content gives "unchanged" (one with other content is rebuilt).
import json
import os
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')

PACK = 'skowyt'
BEFORE = b'pc2_1'
FILES = dict(('d:/ymir work/%s/shaman/skill/paeryong%s.msa' % (race, g), os.path.join(HERE, 'msa', race, 'paeryong%s.msa' % g))
             for race in ('pc', 'pc2') for g in ('', '_2', '_3', '_4'))


def main():
    import m2pack
    import packlib
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    check = '--check' in sys.argv
    base, out = args[:2]
    rd = packlib.rd
    items = dict((k, rd(v)) for k, v in FILES.items())
    for k, b in items.items():
        assert b'MotionEventType      10' in b and b'MotionEventType      1\n' not in b, k
    report = {}

    built = False
    if os.path.exists(os.path.join(out, PACK + '.index')):
        f, v, ents = m2pack.read_index(os.path.join(out, PACK + '.index'))
        dat = rd(os.path.join(out, PACK + '.data'))
        if dict((e['name'], m2pack.read_entry(dat, e)) for e in ents) == items:
            report[PACK] = 'unchanged'
            built = True
    if not built:
        others = {}
        for d in (base, out):
            for p in sorted(f[:-6] for f in os.listdir(d) if f.endswith('.index')):
                if p == PACK:
                    continue
                for e in m2pack.read_index(os.path.join(d, p + '.index'))[2]:
                    others.setdefault(e['name'], p)
        clash = dict((k, others[k]) for k in items if k in others)
        if clash:
            raise SystemExit('names already in other packs: %s' % clash)
        if check:
            size = sum(len(m2pack.encode_entry(b, 2)) for b in items.values())
            report[PACK] = dict(files=len(items), data_kb=round(size / 1e3, 1))
        else:
            tmpl = m2pack.read_index(os.path.join(base, 'gf_mobs.index'))[2][-1]['raw']
            ti, td = os.path.join(out, PACK + '.index.tmp'), os.path.join(out, PACK + '.data.tmp')
            packlib.repack_add_typed(None, None, {}, dict((k, (b, 2)) for k, b in items.items()), ti, td, tmpl)
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
            report[PACK] = dict(entries=len(ents), data_kb=round(len(dat) / 1e3, 1))

    # Index: "*" + "skowyt" right before the "*" + "pc2_1" pair.
    if not check:
        ix_path = os.path.join(out, 'Index') if os.path.exists(os.path.join(out, 'Index')) else os.path.join(base, 'Index')
        ix = rd(ix_path)
        nl = b'\r\n' if b'\r\n' in ix else b'\n'
        lines = ix.replace(b'\r\n', b'\n').split(b'\n')
        stripped = [l.strip() for l in lines]
        if PACK.encode() in stripped:
            if stripped.index(PACK.encode()) > stripped.index(BEFORE):
                raise SystemExit('Index: %s stands after %s - remove its line and run again' % (PACK, BEFORE.decode()))
            new = ix
        else:
            at = stripped.index(BEFORE)
            if at < 1 or stripped[at - 1] != b'*':
                raise SystemExit('Index: no "*" line before %s' % BEFORE.decode())
            lines[at - 1:at - 1] = [b'*', PACK.encode()]
            new = nl.join(lines)
        if new != ix or ix_path != os.path.join(out, 'Index'):
            open(os.path.join(out, 'Index'), 'wb').write(new)
            report['Index'] = 'written'
        else:
            report['Index'] = 'unchanged'
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
