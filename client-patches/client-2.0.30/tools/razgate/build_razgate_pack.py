# -*- coding: utf-8 -*-
# MT2009_PLUS_RAZADOR_GATE_CLIENT_V1 - the client half of MT2009_PLUS_RAZADOR_GATE_V1 (server-patches/enginefixes,
# input_main.cpp): the gates of Razador's dungeon get a collision of their own in the client, so the player stops
# at the gate instead of running into it and being pulled back by the server.
#
# The gates are quest NPCs (20387 Zamek Przeznaczenia = npc2/flame_bridge_block_chain, the chains on the bridge;
# 20388 Smocza Brama = npc2/flame_door_npc). For an actor the exe (GameLib/RaceDataFile.cpp) reads an .mdatr only
# when the race's .msm names it on an "AttributeFileName" line; the actor then carries the file's collisions as
# static collision instances (CActorInstance::UpdateAttribute -> AddCollision with its world matrix), it is in the
# culling tree (CInstanceBase::RegisterBoundingSphere), and the main character's CPythonBackground::CheckAdvancing
# tests every object of the tree in range - AvoidObject (slide along) and IsBlockObject (BlockMovement). That path
# does not look at the actor's type, so it works for an NPC too (TestActorCollision skips NPCs altogether:
# ENABLE_NPC_WITHOUT_COLLISIONS). The collision goes away with the actor (its culling handle is unregistered when
# the instance is destroyed - the server removes the dead gate some 10 s after d.kill_unique).
#
#   flame_door_npc.msm      + AttributeFileName -> flame_door_npc.mdatr (Gameforge's own file, 94 B, was already
#                             in gf_razador but nothing named it): one plane 1032 x 1512 (wide x high), centre
#                             (8.3, 0, 680), standing upright across the door.
#   bridge_block_chain.msm  + AttributeFileName -> bridge_block_chain.mdatr (new, made here - bridge_mdatr()):
#                             one upright plane 1300 x 1000, centre (0, 0, 250) - the chain mesh spans
#                             x -600..580, y -48..45, z 73..434 (read out of bridge_block_chain.gr2), the
#                             .msm's body spheres are 3 x r300 at x = -300 / 0 / 300, z = 150.
#
# .mdatr (EterLib/AttributeData.cpp, CAttributeData::OnLoad), little endian:
#   "AttributeData\0" (14 B), DWORD collision count, DWORD height-data count, then per collision:
#   DWORD type (0 plane, 1 box, 2 sphere, 3 cylinder, 4 AABB, 5 OBB), char name[32], float pos[3],
#   dimensions (plane 2 floats: width along local x, length along local y; box/AABB/OBB 3; sphere 1: radius;
#   cylinder 2: radius, height), float quaternion[4] (x, y, z, w); then the height data
#   (char name[32], DWORD vertex count, float[3] per vertex). A plane's quad lies in its local x/y; the
#   quaternion (sin 45, 0, 0, cos 45) turns it upright (local y -> z), so it blocks movement along local y.
#
# The two .msm and the new .mdatr live in client-patches/client-2.0.28/gf_razador; the entries are replaced /
# added in the existing pack gf_razador (a name in a pack later in Index would not win: the exe's file dict
# keeps the first pack that registered a name), the rest of the pack is copied as it is. Every entry is read back.
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/razgate/build_razgate_pack.py <BASE pack dir> <OUT pack dir> [--check]
#
# BASE: the client's packs so far; OUT: where gf_razador.index / .data go (a gf_razador already in OUT is the one
# changed). Index is not touched (gf_razador is in it). --check only tells what would change. Idempotent:
# a pack that already has these contents gives "unchanged".
import json
import os
import struct
import sys
import zlib

sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')

PACK = 'gf_razador'
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.normpath(os.path.join(HERE, '..', '..', '..', 'client-2.0.28', 'gf_razador', 'd_'))
DOOR = 'd:/ymir work/npc2/flame_door_npc/'
CHAIN = 'd:/ymir work/npc2/flame_bridge_block_chain/'
# 13 October (owner): no collision on the chains at all - only the Smocza Brama's grating collides.
FILES = (DOOR + 'flame_door_npc.msm', DOOR + 'flame_door_npc.mdatr')
TEXT = ('.txt', '.msa', '.msm')
UPRIGHT = (0.70710677, 0.0, 0.0, 0.70710677)


def ctype(name):
    return 2 if name.endswith(TEXT) else 1


def mdatr(collisions):
    """collisions: [(type, name, (x, y, z), dims, quat)] -> .mdatr bytes (no height data)"""
    dims_n = {0: 2, 1: 3, 2: 1, 3: 2, 4: 3, 5: 3}
    out = b'AttributeData\0' + struct.pack('<II', len(collisions), 0)
    for t, name, pos, dims, quat in collisions:
        assert len(dims) == dims_n[t] and len(name) < 32
        out += struct.pack('<I', t) + name.encode() + b'\0' * (32 - len(name))
        out += struct.pack('<3f', *pos) + struct.pack('<%df' % len(dims), *dims) + struct.pack('<4f', *quat)
    return out


def parse_mdatr(b):
    assert b[:14] == b'AttributeData\0', 'header'
    n, h = struct.unpack_from('<II', b, 14)
    p, res = 22, []
    for _ in range(n):
        t, = struct.unpack_from('<I', b, p)
        name = b[p + 4:p + 36].split(b'\0')[0].decode()
        pos = struct.unpack_from('<3f', b, p + 36)
        k = {0: 2, 1: 3, 2: 1, 3: 2, 4: 3, 5: 3}[t]
        dims = struct.unpack_from('<%df' % k, b, p + 48)
        quat = struct.unpack_from('<4f', b, p + 48 + 4 * k)
        p += 48 + 4 * k + 16
        res.append((t, name, pos, dims, quat))
    assert h == 0 and p == len(b), 'trailing data / height data'
    return res


def bridge_mdatr():
    # One upright plane across the bridge: 1300 wide (chain x -600..580, +-650), 1000 high (z -250..750).
    return mdatr([(0, 'collision00', (0.0, 0.0, 250.0), (1300.0, 1000.0), UPRIGHT)])


def items():
    got = dict((n, open(os.path.join(SRC, n[3:]), 'rb').read()) for n in FILES)
    for n in FILES:
        if n.endswith('.msm'):
            path = ('D:/' + n[3:-4] + '.mdatr').replace('/', '\\')
            want = ('AttributeFileName     "%s"' % path).encode()
            if want not in got[n]:
                raise SystemExit('%s has no line %s' % (n, want))
        else:
            parse_mdatr(got[n])
    return got


def main():
    import m2pack
    import packlib
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if '--write-mdatr' in sys.argv:
        open(os.path.join(SRC, CHAIN[3:] + 'bridge_block_chain.mdatr'), 'wb').write(bridge_mdatr())
        print('written')
        return
    check = '--check' in sys.argv
    base, out = args[:2]
    rd = packlib.rd
    want = items()
    src = out if os.path.exists(os.path.join(out, PACK + '.index')) else base
    f, v, ents = m2pack.read_index(os.path.join(src, PACK + '.index'))
    dat = rd(os.path.join(src, PACK + '.data'))
    have = dict((e['name'], m2pack.read_entry(dat, e)) for e in ents)
    replace = dict((n, b) for n, b in want.items() if n in have and have[n] != b)
    add = dict((n, (b, ctype(n))) for n, b in want.items() if n not in have)
    report = {'from': src, 'mdatr': dict((n, parse_mdatr(b)) for n, b in want.items() if n.endswith('.mdatr'))}
    if not replace and not add:
        report[PACK] = 'unchanged (%s)' % src
    elif check:
        report[PACK] = dict(replace=sorted(replace), add=sorted(add))
    else:
        ti, td = os.path.join(out, PACK + '.index.tmp'), os.path.join(out, PACK + '.data.tmp')
        kept, added, replaced = packlib.repack_add_typed(os.path.join(src, PACK + '.index'),
                                                         os.path.join(src, PACK + '.data'), replace, add, ti, td)
        os.replace(ti, os.path.join(out, PACK + '.index'))
        os.replace(td, os.path.join(out, PACK + '.data'))
        f, v, ents2 = m2pack.read_index(os.path.join(out, PACK + '.index'))
        dat2 = rd(os.path.join(out, PACK + '.data'))
        got = {}
        for e in ents2:
            assert zlib.crc32(dat2[e['pos']:e['pos'] + e['size']]) & 0xffffffff == e['dcrc'], e['name']
            assert e['fcrc'] == zlib.crc32(e['name'].encode('cp1252')) & 0xffffffff, e['name']
            got[e['name']] = m2pack.read_entry(dat2, e)
        expect = dict(have)
        expect.update(want)
        assert got == expect, 'read-back differs'
        report[PACK] = dict(entries=len(ents2), replaced=sorted(replace), added=sorted(add),
                            data_mb=round(len(dat2) / 1e6, 2))
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
