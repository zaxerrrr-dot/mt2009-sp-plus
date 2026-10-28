# -*- coding: utf-8 -*-
# MT2009_PLUS_GAYA_CURRENCY_V1 - the new client pack "gaya2": the images of the Gaya currency's counter (the owner,
# 28 October 2026: "the counter with the icon next to the Yang in the inventory, as on global"; server-patches/gaya2).
# From the owner's packages (cache/gaya2): "Expanded Money Taskbar" (emt/__extra__/metin2_patch_gem.rar - the money
# slots and the taskbar button) and "Gaya Taskbar" (b/t/Gaya Taskbar/gaya.tga - the Gaya icon). Every name is new
# (d:/ymir work/ui/gaya2/...), so no file of the client is replaced - the package's public.dds goes in as
# gaya2_public.dds and our three .sub files cut its slots (a version 1.0 .sub names its image from d:/ymir work/ui/):
#
#   d:/ymir work/ui/gaya2/gaya2_public.dds      the package's ui/public.dds (the newer slots: Yang, Won, Gaya)
#   d:/ymir work/ui/gaya2/gold_slot.sub         Yang slot 90 x 18 (the package's public/gold_slot.sub)
#   d:/ymir work/ui/gaya2/cheque_slot.sub       Won slot 24 x 18 (public/cheque_slot.sub) - only with constInfo.ENABLE_WON
#   d:/ymir work/ui/gaya2/gaya_slot.sub         Gaya slot 52 x 18 (public/parameter_slot_01.sub of the package)
#   d:/ymir work/ui/gaya2/gaya_icon.tga         the Gaya icon 13 x 11 (Gaya Taskbar/gaya.tga)
#   d:/ymir work/ui/gaya2/money_button_0[1-3].tga  the taskbar button of the money bar (game/taskbar/ex_gemshop_button_0N.tga)
#
# The root side (client-2.0.30/root: constinfo.py, gayacurrency.py, uiinventory.py, uiscript/inventorywindow.py,
# uiscript/expandedmoneytaskbar.py, uitaskbar.py, interfacemodule.py, game.py) names these files.
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/gaya2/build_gaya2_pack.py <BASE pack dir> <OUT pack dir> [--check]
#
# clientY.sh: after the last pack builder (fireghost), before the verify loop:
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/gaya2/build_gaya2_pack.py $C/azbase \
#     $C/out/pack > $C/gaya2.json
# then gaya2/verify_gaya2.py in the verify loop. BASE: the client's packs so far (Index is read from OUT if an earlier
# step wrote one there, else from BASE); OUT: where gaya2.index / gaya2.data and the Index go. --check measures only.
# Every entry written is read back. Idempotent: a pack in OUT with the same content gives "unchanged"; the Index line
# is not added twice.
import hashlib
import json
import os
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')

PACK = 'gaya2'
AFTER = b'PACK'
DATA = os.path.join(HERE, 'pliki')
MANIFEST = os.path.join(HERE, 'gaya2_files.json')
CTYPE = {'dds': 1, 'tga': 1, 'sub': 2}   # as root / minigames / az_ui keep them


def manifest():
    return json.load(open(MANIFEST))['files']


def items():
    """{name: (bytes, ctype)} from pliki/, checked against gaya2_files.json (size, sha256, entry type)"""
    m = manifest()
    on_disk = set()
    for root, dirs, files in os.walk(DATA):
        for f in files:
            on_disk.add('d:/' + os.path.relpath(os.path.join(root, f), DATA).replace(os.sep, '/'))
    if on_disk != set(m):
        raise SystemExit('pliki/ differs from gaya2_files.json: extra %s, missing %s'
                         % (sorted(on_disk - set(m)), sorted(set(m) - on_disk)))
    out = {}
    for name, w in sorted(m.items()):
        b = open(os.path.join(DATA, name[3:]), 'rb').read()
        if len(b) != w['size'] or hashlib.sha256(b).hexdigest() != w['sha256']:
            raise SystemExit('%s: not the file of gaya2_files.json' % name)
        assert w['ctype'] == CTYPE[name.rsplit('.', 1)[1]], name
        out[name] = (b, w['ctype'])
    # every .sub cuts the pack's own atlas, inside its 256 x 512
    for name, (b, c) in out.items():
        if name.endswith('.sub'):
            t = dict(l.split(None, 1) for l in b.decode('ascii').replace('\r\n', '\n').split('\n') if l.strip())
            assert t['image'] == '"gaya2/gaya2_public.dds"', name
            assert 0 <= int(t['left']) < int(t['right']) <= 256 and 0 <= int(t['top']) < int(t['bottom']) <= 512, name
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

    # no other pack may carry these names (they are new)
    others = {}
    for d in (base, out):
        for p in sorted(f[:-6] for f in os.listdir(d) if f.endswith('.index')):
            if p == PACK:
                continue
            for e in m2pack.read_index(os.path.join(d, p + '.index'))[2]:
                if e['name'] in want:
                    others.setdefault(p, set()).add(e['name'])
    if others:
        raise SystemExit('names of gaya2 in other packs: %s' % dict((p, sorted(n)) for p, n in others.items()))

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

    # Index: "*" + "gaya2" at the end (the names are new, any place would do; the first pack stays fireghost's -
    # fireghost/verify_fireghost.py checks that)
    if not check:
        ix_path = os.path.join(out, 'Index') if os.path.exists(os.path.join(out, 'Index')) else os.path.join(base, 'Index')
        ix = rd(ix_path)
        nl = b'\r\n' if b'\r\n' in ix else b'\n'
        lines = ix.replace(b'\r\n', b'\n').split(b'\n')
        stripped = [l.strip() for l in lines]
        if stripped[0] != AFTER:
            raise SystemExit('Index: the first line is not PACK')
        if PACK.encode() in stripped:
            new = ix
        else:
            tail = []
            while lines and not lines[-1].strip():
                tail.append(lines.pop())
            lines += [b'*', PACK.encode()] + tail
            new = nl.join(lines)
        if new != ix or ix_path != os.path.join(out, 'Index'):
            open(os.path.join(out, 'Index'), 'wb').write(new)
            report['Index'] = 'written'
        else:
            report['Index'] = 'unchanged'
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
