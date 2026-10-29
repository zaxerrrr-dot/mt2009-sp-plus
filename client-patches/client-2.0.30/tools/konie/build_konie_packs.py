# -*- coding: utf-8 -*-
# MT2009_PLUS_HORSE40_V1 - the client build's part of the horse past level 21 (server-patches/konie/README.md):
#   1) the new pack "konie" (stage_konie.py -> pliki/, konie_files.json): the Mount Upgrade window's images and the
#      horse skill icons (d:/ymir work/ui/konie/*: GF's riding_extend_001.dds and newskillcommon.dds by names of their
#      own, GF's .sub files pointing at them) and Potezny Kon Wojskowy's model (d:/ymir work/npc_mount/horse_guild/*,
#      20149-20151 - npclist.txt has the lines already); "*" + "konie" at the end of pack/Index;
#   2) the existing packs "dbdata" (gamedata/item_proto, locale/pl/itemdesc.txt) and "gamedata"
#      (gamedata/item_list.txt, gamedata/mob_proto): patch_konie_client.py (50046-50049, the books 55050-55067,
#      the mob records 20149-20151).
# The window itself (root/uikonierozwoj.py), its lines in game.py and uiaffectbar.py and the item icons
# (root/icon/item/50046-50049.tga) travel in client-2.0.30/root like every root change.
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/konie/build_konie_packs.py <BASE pack dir> <OUT pack dir> [--check]
#
# clientY.sh: after the czepiec line (it shares dbdata / gamedata with the item builders - after all of them, and
# after mobyglobal / protoglobal if those run later, the order is free: the records it writes are its own vnums),
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/konie/build_konie_packs.py $C/azbase \
#     $C/out/pack > $C/konie.json
# then konie/verify_konie.py in the verify loop. Every entry written is read back. Idempotent: a second run gives
# "unchanged".
import hashlib
import json
import os
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/c36')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, HERE)
ZIP_LIMIT = 29 * 1024 * 1024
PACK = 'konie'
AFTER = b'PACK'
DATA = os.path.join(HERE, 'pliki')
MANIFEST = os.path.join(HERE, 'konie_files.json')


def manifest():
    return json.load(open(MANIFEST))['files']


def items():
    """{name: (bytes, ctype)} from pliki/, checked against konie_files.json"""
    m = manifest()
    on_disk = set()
    for root, dirs, files in os.walk(DATA):
        for f in files:
            on_disk.add('d:/' + os.path.relpath(os.path.join(root, f), DATA).replace(os.sep, '/'))
    if on_disk != set(m):
        raise SystemExit('pliki/ differs from konie_files.json: extra %s, missing %s'
                         % (sorted(on_disk - set(m)), sorted(set(m) - on_disk)))
    out = {}
    for name, w in sorted(m.items()):
        b = open(os.path.join(DATA, name[3:]), 'rb').read()
        if len(b) != w['size'] or hashlib.sha256(b).hexdigest() != w['sha256']:
            raise SystemExit('%s: not the file of konie_files.json' % name)
        out[name] = (b, w['ctype'])
    # every .sub cuts one of the pack's own atlases, inside it
    size = {'"konie/riding_extend_001.dds"': (176, 100), '"konie/newskillcommon_konie.dds"': (256, 768)}
    for name, (b, c) in out.items():
        if name.endswith('.sub'):
            t = dict(l.split(None, 1) for l in b.decode('ascii').replace('\r\n', '\n').split('\n') if l.strip())
            w, h = size[t['image']]
            assert 0 <= int(t['left']) < int(t['right']) <= w and 0 <= int(t['top']) < int(t['bottom']) <= h, name
    return out


def main():
    import m2pack
    import packlib
    import patch_konie_client as pc
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    check = '--check' in sys.argv
    base, out = args[:2]
    rd = packlib.rd
    report = {}

    # ---------------------------------------------------------------- 1) the pack "konie"
    want = items()
    raw = dict((k, b) for k, (b, c) in want.items())
    others = {}
    for d in (base, out):
        for p in sorted(f[:-6] for f in os.listdir(d) if f.endswith('.index')):
            if p == PACK:
                continue
            for e in m2pack.read_index(os.path.join(d, p + '.index'))[2]:
                if e['name'] in want:
                    others.setdefault(p, set()).add(e['name'])
    if others:
        raise SystemExit('names of konie in other packs: %s' % dict((p, sorted(n)) for p, n in others.items()))
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

    # ---------------------------------------------------------------- 2) dbdata / gamedata
    def src_of(pack):
        return out if os.path.exists(os.path.join(out, pack + '.index')) else base

    def write(pack, src, rep, ents, dat):
        tmp_i, tmp_d = os.path.join(out, pack + '.index.kn'), os.path.join(out, pack + '.data.kn')
        r = packlib.repack_add_typed(os.path.join(src, pack + '.index'), os.path.join(src, pack + '.data'), rep, {},
                                     tmp_i, tmp_d, ents[-1]['raw'])
        os.replace(tmp_i, os.path.join(out, pack + '.index'))
        os.replace(tmp_d, os.path.join(out, pack + '.data'))
        f, v, nw = m2pack.read_index(os.path.join(out, pack + '.index'))
        nd = rd(os.path.join(out, pack + '.data'))
        names = [e['name'] for e in nw]
        assert len(set(names)) == len(names), pack
        got = {}
        for e in nw:
            assert zlib.crc32(nd[e['pos']:e['pos'] + e['size']]) & 0xffffffff == e['dcrc'], (pack, e['name'])
            got[e['name']] = m2pack.read_entry(nd, e)
        for n, b in rep.items():
            assert got[n] == b, (pack, n)
        for e in ents:
            if e['name'] not in rep:
                assert got[e['name']] == m2pack.read_entry(dat, e), (pack, e['name'])
        return dict(old=r[0], added=r[1], replaced=r[2], entries=len(nw), data_mb=round(len(nd) / 1e6, 2),
                    under_zip_limit=len(nd) < ZIP_LIMIT)

    jobs = {'gamedata': ['gamedata/item_list.txt', 'gamedata/mob_proto'],
            'dbdata': ['gamedata/item_proto', 'locale/pl/itemdesc.txt']}
    for pack, files in jobs.items():
        src = src_of(pack)
        f, v, ents = m2pack.read_index(os.path.join(src, pack + '.index'))
        dat = rd(os.path.join(src, pack + '.data'))
        have = dict((e['name'], e) for e in ents)
        rep = {}
        for n in files:
            b = m2pack.read_entry(dat, have[n])
            nb, changed = pc.JOBS[n](b)
            if nb != b:
                rep[n] = nb
                assert pc.JOBS[n](nb)[1] == 0, n     # a second pass changes nothing
        if not rep:
            report[pack] = 'unchanged'
        elif check:
            report[pack] = dict(replace=sorted(rep))
        else:
            report[pack] = write(pack, src, rep, ents, dat)
            report[pack]['replaced_names'] = sorted(rep)
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
