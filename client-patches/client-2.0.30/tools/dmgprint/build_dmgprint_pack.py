# -*- coding: utf-8 -*-
# MT2009_PLUS_DAMAGE_PRINT_V1 - the new client pack "dmgprint": the damage marks of "Damage Print Improve v26.0.5"
# (the owner, 29 October 2026: "systems that change the game visually - add them to Yohara"). The exe side is
# client-patches/exe (ENABLE_DAMAGE_PRINT_IMPROVE: CInstanceBase::ProcessDamage, CEffectManager's damage set, the
# "EnableFrustum" token), the server side server-patches/dmgprint (DAMAGE_MISS / DAMAGE_ATTACKER_PC in the flag byte).
#
# The pack: pliki/ (the package's ymir work/effect/affect/damagevalue - 38 files, byte for byte GF client 26.1.11's
# folder; dmgprint_files.json holds names, sizes, sha256 and entry types) under a folder of its own:
#   d:/ymir work/effect/affect/damagevalue2/   target.mse, damage.mse, damage_1.mse, miss.mse, target_miss.mse,
#       dodge.mse, block.mse, damage_critical.mse, damage_penetration.mse, damage_mix.mse (+ critical.mse, unused),
#       target_0-9.dds, damage_0-9.dds, the marks' textures (miss, dodge, block, critical, penetration, mix)
# Every name is new, so nothing of the client is replaced: the old exe keeps reading damagevalue/ (its own crit_ /
# pen_ / poison_ digits), only the new exe registers damagevalue2/ (PythonPlayerSettingsModule.cpp) and builds the
# digit names from it (InstanceBaseEffect.cpp). The .mse files name their textures without a folder (the folder of
# the .mse), critical.mse names d:/ymir work/pc/shaman/effect/noe_splitlife.dds (base pack; the exe does not load it).
# The pack's Index line goes LAST.
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/dmgprint/build_dmgprint_pack.py <BASE pack dir> <OUT pack dir> [--check]
#
# clientY.sh: after the last pack builder (gaya2), before the verify loop:
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/dmgprint/build_dmgprint_pack.py $C/azbase \
#     $C/out/pack > $C/dmgprint.json
# then dmgprint/verify_dmgprint.py on OUT (in the verify loop). BASE: the client's packs so far (Index is read from
# OUT if an earlier step wrote one there, else from BASE); OUT: where dmgprint.index / dmgprint.data and the Index go.
# --check measures only. Every entry written is read back. Idempotent: a pack in OUT with the same content gives
# "unchanged" (one with other content is rebuilt); the Index line is not added twice.
import hashlib
import json
import os
import re
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')

PACK = 'dmgprint'
DATA = os.path.join(HERE, 'pliki')
MANIFEST = os.path.join(HERE, 'dmgprint_files.json')
FOLDER = 'd:/ymir work/effect/affect/damagevalue2/'
# the effects the exe registers (PythonPlayerSettingsModule.cpp) and the digit textures it names (InstanceBaseEffect.cpp)
EFFECTS = ('target.mse', 'damage.mse', 'damage_1.mse', 'miss.mse', 'target_miss.mse', 'damage_critical.mse',
           'dodge.mse', 'block.mse', 'damage_penetration.mse', 'damage_mix.mse')
DIGITS = tuple('%s_%d.dds' % (p, d) for p in ('target', 'damage') for d in range(10))


def manifest():
    return json.load(open(MANIFEST))['files']


def mse_textures(b, name):
    """the texture names an .mse lists (lower case, full d:/ path)"""
    out = []
    for r in re.findall(rb'"([^"]+\.(?:dds|tga))"', b, re.I):
        r = r.decode('latin-1').replace('\\', '/').lower()
        if '/' not in r:
            r = name.rsplit('/', 1)[0] + '/' + r
        out.append(r)
    return out


def items():
    """{name: (bytes, ctype)} from pliki/, checked against the manifest's names, sizes and sha256"""
    m = manifest()
    on_disk = set()
    for root, dirs, files in os.walk(DATA):
        for f in files:
            on_disk.add('d:/' + os.path.relpath(os.path.join(root, f), DATA).replace(os.sep, '/'))
    if on_disk != set(m):
        raise SystemExit('pliki/ differs from dmgprint_files.json: extra %s, missing %s'
                         % (sorted(on_disk - set(m)), sorted(set(m) - on_disk)))
    out = {}
    for name, w in sorted(m.items()):
        b = open(os.path.join(DATA, name[3:]), 'rb').read()
        if len(b) != w['size'] or hashlib.sha256(b).hexdigest() != w['sha256']:
            raise SystemExit('%s: not the manifest\'s file' % name)
        out[name] = (b, w['ctype'])
    for f in EFFECTS + DIGITS:
        assert FOLDER + f in out, f
    for f in EFFECTS:
        b = out[FOLDER + f][0]
        # one particle group (CEffectManager::SetSingleParticleTexture), no loop, its texture in this pack
        assert len(re.findall(rb'Group Particle\s*\n', b)) == 1, f
        assert not re.search(rb'CycleLoopEnable\s+1', b), f
        for t in mse_textures(b, FOLDER + f):
            assert t in out, (f, t)
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

    # names other listed packs carry too (none expected: damagevalue2/ is new)
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

    # Index: "*" + "dmgprint" at the end
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
