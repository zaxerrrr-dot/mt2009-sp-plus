# -*- coding: utf-8 -*-
# MT2009_PLUS_MOUNT_COMBO_HIT_V1 - the new client pack "konnekombo": every blow of a mounted combo hits again (the
# owner's list of 3 November 2026: "Walka na wierzchowcu: czesc atakow nie zadaje obrazen - Szaman dzwon/wachlarz,
# Ninja, Sura, od ~150 szybkosci ataku co drugi cios"; his own server's fix of the same day, ported).
#
# Why: when a normal attack hits, the client makes that target unhittable for the event's InvisibleTime
# (MotionEventData, AttackingData) of the attacking animation. Every mounted combo (d:/ymir work/pc{,2}/<class>/
# horse_<weapon>/combo_01..03.msa) has a fixed 0.30 s there, whatever the attack speed. The swing interval on a mount
# (combo_02 <-> combo_03) at attack speed 100 / 157 / 170: shaman 0.455-0.416 / 0.29-0.27 / 0.27-0.24 s, ninja
# 0.378-0.522 / 0.24-0.33 / 0.22-0.31 s, sura 0.456-0.514 / 0.29-0.33 / 0.27-0.30 s, warrior 0.52 / 0.33 / 0.31 s - every
# interval under 0.30 s swings at an "invisible" target and the blow is never sent to the server (the shaman lost every
# second hit from about 150, the ninja every second 02->03). The server caps the attack speed at 170 (GetLimitPoint);
# 0.15 s is under the shortest interval there. The server needs no change.
#
# The packs: "konnekombo" and its twin "konnekombo2" (the same content), the 42 mounted combos (pc and pc2, warrior / ninja / sura / shaman - no pc3) with every InvisibleTime set
# to 0.150000, nothing else touched. Their source, pliki/, is GF 26.1.11's set - byte for byte the files the players'
# 3.0.6 install opens (pack gf_official, which the exe registers before pc_1, pc_2, pc2_1 and pc2_2; md5 in
# konnekombo_files.json, read from the 3.0.6 base).
#
# Which pack's file the exe opens: CEterFileDict (CEterFileDict::InsertItem / GetItem) is a boost::unordered_multimap
# keyed by the name's CRC (boost 1.83 of the client's Extern): an equal key is inserted right AFTER the first node of
# its group, GetItem returns the group's first node, and every rehash (the dict grows to ~100 000 names while the packs
# register) moves each bucket's nodes to the front of the new bucket - it REVERSES every group. So a group's first node
# is always its 1st or its 2nd registered copy, by the parity of the rehashes after the 2nd: no later pack can ever win,
# and a single pack registered first wins only for some names (simulated on the 3.0.6 install's 100 157 names with
# that boost: one pack first - 27 of 42, gf_official the other 15, and the split flips as packs are added; one pack
# last, as on the owner's server - 0 of 42; today the pc_* packs win, not gf_official). Two identical packs registered
# as the 1st and 2nd copy of every name win for good: their Index lines go right after "PACK", konnekombo then
# konnekombo2 (a pack put above them later, e.g. fireghost, does not matter: no name or name CRC is shared - checked
# against BASE / OUT).
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/konnekombo/build_konnekombo_pack.py <BASE pack dir> <OUT pack dir> [--check]
#
# clientY.sh: a pack builder without gamedata / dbdata, after the azbase copy (e.g. next to quickslot2):
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/konnekombo/build_konnekombo_pack.py $C/azbase \
#     $C/out/pack > $C/konnekombo.json
# then konnekombo/verify_konnekombo.py on OUT in the verify loop. BASE: the client's packs so far (Index is read from
# OUT if an earlier step wrote one there, else from BASE); OUT: where konnekombo.index / .data and the Index go. A name
# some other pack of BASE / OUT has stops the build. Every entry written is read back. Idempotent.
import hashlib
import json
import os
import re
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
PACK = 'konnekombo'
PACKS = (PACK, PACK + '2')     # the twins: the 1st and 2nd registered copy of every name
SRC = os.path.join(HERE, 'pliki')
MANIFEST = os.path.join(HERE, 'konnekombo_files.json')
PREFIX = 'd:/ymir work/'
NAME_RE = re.compile(r'^d:/ymir work/pc2?/[a-z]+/horse_[a-z_]+/combo_0\d\.msa$')
INV_RE = re.compile(rb'(InvisibleTime[ \t]+)([0-9.]+)')
INVISIBLE = b'0.150000'
# the packs of the players' install that carry these names (the pack must be registered before all of them)
SHADOWED = (b'gf_official', b'pc_1', b'pc_2', b'pc2_1', b'pc2_2')
ZIP_LIMIT = 29 * 1024 * 1024


def files():
    """the new pack's entries: name -> bytes (every InvisibleTime 0.150000)"""
    man = json.load(open(MANIFEST))['files']
    out = {}
    for dp, dn, fn in os.walk(SRC):
        for f in fn:
            p = os.path.join(dp, f)
            name = PREFIX + os.path.relpath(p, SRC).replace(os.sep, '/')
            assert NAME_RE.match(name), name
            b = open(p, 'rb').read()
            assert name in man and hashlib.md5(b).hexdigest() == man[name]['md5'], '%s: not the players\' file' % name
            nb, n = INV_RE.subn(lambda m: m.group(1) + INVISIBLE, b)
            assert n >= 1, '%s: no InvisibleTime' % name
            out[name] = nb
    assert sorted(out) == sorted(man), 'pliki/ and konnekombo_files.json differ'
    return out


def main():
    import m2pack
    import packlib
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    check = '--check' in sys.argv
    base, out = args[:2]
    rd = packlib.rd
    items = files()
    crcs = dict((zlib.crc32(n.encode('cp1252')) & 0xffffffff, n) for n in items)
    for d in (base, out):
        if not os.path.isdir(d):
            continue
        for p in sorted(f[:-6] for f in os.listdir(d) if f.endswith('.index')):
            if p in PACKS:
                continue
            for e in m2pack.read_index(os.path.join(d, p + '.index'))[2]:
                if e['name'] in items:
                    raise SystemExit('%s: %s is in %s/%s already' % (PACK, e['name'], d, p))
                c = zlib.crc32(e['name'].encode('cp1252')) & 0xffffffff
                if c in crcs:
                    raise SystemExit('%s: %s (%s/%s) has the CRC of %s' % (PACK, e['name'], d, p, crcs[c]))
    tmpl = m2pack.read_index(os.path.join(base, 'az_mobs.index'))[2][-1]['raw']
    report = {}

    def write(pack, add):
        tmp_i, tmp_d = os.path.join(out, pack + '.index.kk'), os.path.join(out, pack + '.data.kk')
        r = packlib.repack_add_typed(None, None, {}, add, tmp_i, tmp_d, tmpl)
        os.replace(tmp_i, os.path.join(out, pack + '.index'))
        os.replace(tmp_d, os.path.join(out, pack + '.data'))
        f, v, nw = m2pack.read_index(os.path.join(out, pack + '.index'))
        nd = rd(os.path.join(out, pack + '.data'))
        got = {}
        for e in nw:
            assert zlib.crc32(nd[e['pos']:e['pos'] + e['size']]) & 0xffffffff == e['dcrc'], e['name']
            assert e['fcrc'] == zlib.crc32(e['name'].encode('cp1252')) & 0xffffffff, e['name']
            got[e['name']] = m2pack.read_entry(nd, e)
        assert sorted(got) == sorted(add)
        for n, (b, c) in add.items():
            assert got[n] == b, n
        return dict(old=r[0], added=r[1], replaced=r[2], entries=len(nw), data_kb=round(len(nd) / 1e3, 1),
                    under_zip_limit=len(nd) < ZIP_LIMIT)

    for pack in PACKS:
        done = [d for d in (base, out) if os.path.exists(os.path.join(d, pack + '.index'))]
        if done:
            f, v, ents = m2pack.read_index(os.path.join(done[0], pack + '.index'))
            dat = rd(os.path.join(done[0], pack + '.data'))
            if dict((e['name'], m2pack.read_entry(dat, e)) for e in ents) == items:
                report[pack] = 'in base' if done[0] == base else 'in out'
                continue
            if done[0] == out and not check:
                os.remove(os.path.join(out, pack + '.index'))
                os.remove(os.path.join(out, pack + '.data'))
            else:
                raise SystemExit('%s is in BASE with other content - drop it from BASE' % pack)
        if check:
            report[pack] = dict(files=len(items), data_kb=round(sum(len(m2pack.encode_entry(b, 2))
                                                                   for b in items.values()) / 1e3, 1))
        else:
            report[pack] = write(pack, dict((k, (b, 2)) for k, b in items.items()))
            assert report[pack]['under_zip_limit'], report[pack]

    # Index: "*" + "konnekombo", "*" + "konnekombo2" right after "PACK" - ahead of every pack carrying the names
    if not check:
        ix_path = os.path.join(out, 'Index') if os.path.exists(os.path.join(out, 'Index')) else os.path.join(base, 'Index')
        ix = rd(ix_path)
        nl = b'\r\n' if b'\r\n' in ix else b'\n'
        lines = ix.replace(b'\r\n', b'\n').split(b'\n')
        stripped = [l.strip() for l in lines]
        if stripped[0] != b'PACK':
            raise SystemExit('Index: the first line is not PACK')
        names = [p.encode() for p in PACKS]
        if any(n in stripped for n in names):
            problem = index_problem(stripped)
            if problem:
                raise SystemExit('Index: %s - remove the konnekombo lines and run again' % problem)
            new = ix
        else:
            lines[1:1] = [b'*', names[0], b'*', names[1]]
            new = nl.join(lines)
        if new != ix or ix_path != os.path.join(out, 'Index'):
            open(os.path.join(out, 'Index'), 'wb').write(new)
            report['Index'] = 'written'
        else:
            report['Index'] = 'unchanged'

    print(json.dumps(report, indent=1))


def index_problem(stripped):
    """None when both twins are listed, next to each other (konnekombo, "*", konnekombo2), and before every pack of
    the players' install that carries the names; else what is wrong (the verifier uses it too)."""
    names = [p.encode() for p in PACKS]
    if not all(n in stripped for n in names):
        return 'not both of %s listed' % (PACKS,)
    a, b = stripped.index(names[0]), stripped.index(names[1])
    if b != a + 2:
        return '%s does not follow %s' % PACKS[::-1]
    early = [p.decode() for p in SHADOWED if p in stripped and stripped.index(p) < a]
    if early:
        return '%s listed before %s' % (early, PACK)
    return None


if __name__ == '__main__':
    main()
