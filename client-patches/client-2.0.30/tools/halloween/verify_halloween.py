# -*- coding: utf-8 -*-
# MT2009_PLUS_HALLOWEEN_V1 - checks the Halloween event's client half after a build (Autor: Owsap - the event):
#   * the pack "halloween" (OUT, else BASE): every entry's crc32 of its name and of its stored blob, the 14 files
#     of halloween_client.json "model_files" under d:/ymir work/npc2/halloween1/, byte-equal to the GF sources,
#     32-bit GR2 only, and the msm's BaseModelFileName / the motlist's motions / the mse's textures inside it;
#   * pack/Index (OUT, else BASE) lists "halloween";
#   * item_list.txt: the twelve vnums, each with its icon, and every icon in some pack (BASE + OUT);
#   * itemdesc.txt: the twelve descriptions;
#   * npclist.txt (optional): 33008 -> halloween1.
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/halloween/verify_halloween.py <BASE pack dir> <OUT pack dir> \
#     <data dir: item_list.txt, itemdesc.txt> [<npclist.txt>]
# The last line is "VERIFY halloween OK" or "VERIFY halloween FAILED (<n> problems)".
import io
import json
import os
import re
import sys
import zlib

sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
import m2pack  # noqa: E402
import packlib  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
with io.open(os.path.join(HERE, 'halloween_client.json'), encoding='utf-8') as _f:
    DATA = json.load(_f)
GF = '/opt/metin2/cache/gf/Gameforge_26.1.11/_client'
GR2_64 = b'\xe5\x9b\x49\x5e'
problems = []


def bad(msg):
    problems.append(msg)
    print('BAD', msg)


def norm(p):
    return p.replace('\\', '/').strip().lower()


def pack_dir_of(name, dirs):
    for d in dirs:
        if os.path.exists(os.path.join(d, name + '.index')):
            return d
    return None


def names_in(dirs):
    names = set()
    for d in dirs:
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            if f.endswith('.index'):
                for e in m2pack.read_index(os.path.join(d, f))[2]:
                    names.add(e['name'])
    return names


def lines_by_key(path):
    text = open(path, 'rb').read().decode('cp1250')
    out = {}
    for l in text.replace('\r\n', '\n').split('\n'):
        k = l.split('\t', 1)[0].strip()
        if k:
            out.setdefault(k, l)
    return out


def main():
    if len(sys.argv) not in (4, 5):
        raise SystemExit('usage: verify_halloween.py <BASE pack dir> <OUT pack dir> <data dir> [<npclist.txt>]')
    base, out, data = sys.argv[1:4]
    npclist = sys.argv[4] if len(sys.argv) == 5 else None
    pack = DATA['pack']
    where = pack_dir_of(pack, (out, base))
    if not where:
        bad('no %s.index in %s or %s' % (pack, out, base))
    else:
        f, v, ents = m2pack.read_index(os.path.join(where, pack + '.index'))
        dat = packlib.rd(os.path.join(where, pack + '.data'))
        got = {}
        for e in ents:
            if zlib.crc32(dat[e['pos']:e['pos'] + e['size']]) & 0xffffffff != e['dcrc']:
                bad('%s: data crc of %s' % (pack, e['name']))
            if e['fcrc'] != zlib.crc32(e['name'].encode('cp1252')) & 0xffffffff:
                bad('%s: name crc of %s' % (pack, e['name']))
            got[e['name']] = m2pack.read_entry(dat, e)
        want = set(DATA['model_dir'] + n for n in DATA['model_files'])
        if set(got) != want:
            bad('%s: entries %s, missing %s' % (pack, sorted(set(got) - want), sorted(want - set(got))))
        rel = DATA['model_dir'][len('d:/'):]
        for name in sorted(want & set(got)):
            srcp = os.path.join(GF, 'd_', rel, name[len(DATA['model_dir']):])
            if packlib.rd(srcp) != got[name]:
                bad('%s: %s differs from %s' % (pack, name, srcp))
            if name.endswith('.gr2') and got[name][:4] == GR2_64:
                bad('%s: %s is a 64-bit GR2' % (pack, name))
        msm = got.get(DATA['model_dir'] + 'halloween1.msm', b'').decode('latin-1')
        m = re.search(r'BaseModelFileName\s+"([^"]+)"', msm)
        if not m or norm(m.group(1)) not in got:
            bad('%s: the msm base model %s is not in the pack' % (pack, m.group(1) if m else None))
        for t in re.findall(r'"([^"]+\.(?:dds|tga))"', got.get(DATA['model_dir'] + 'fire_red1.mse', b'').decode('latin-1')):
            t = norm(t)
            if '/' not in t and DATA['model_dir'] + t not in got:
                bad('%s: the effect texture %s is not in the pack' % (pack, t))
        for l in got.get(DATA['model_dir'] + 'motlist.txt', b'').decode('latin-1').splitlines():
            parts = l.split()
            if len(parts) >= 3 and DATA['model_dir'] + parts[2].lower() not in got:
                bad('%s: motlist motion %s is not in the pack' % (pack, parts[2]))
        print('pack %s (%s): %d entries' % (pack, where, len(got)))
    ix = os.path.join(out, 'Index') if os.path.exists(os.path.join(out, 'Index')) else os.path.join(base, 'Index')
    lines = [l.strip() for l in packlib.rd(ix).replace(b'\r\n', b'\n').split(b'\n')]
    if pack.encode() not in lines:
        bad('%s does not list %s' % (ix, pack))
    names = names_in((base, out))
    il = lines_by_key(os.path.join(data, 'item_list.txt'))
    for vnum, icon in sorted(DATA['items_present'].items()):
        line = il.get(vnum)
        if not line:
            bad('item_list.txt: no %s' % vnum)
            continue
        cols = line.split('\t')
        if len(cols) < 3 or norm(cols[2]) != icon:
            bad('item_list.txt: %s has %r, not %s' % (vnum, line, icon))
        if icon not in names:
            bad('icon %s of %s is in no pack' % (icon, vnum))
    desc = lines_by_key(os.path.join(data, 'itemdesc.txt'))
    for vnum, line in sorted(DATA['itemdesc'].items()):
        if desc.get(vnum) != line:
            bad('itemdesc.txt: %s is %r' % (vnum, desc.get(vnum)))
    if npclist:
        npc = lines_by_key(npclist)
        for vnum, folder in DATA['npclist'].items():
            cols = npc.get(vnum, '').split('\t')
            if len(cols) < 2 or cols[1].strip() != folder:
                bad('npclist.txt: %s is %r, not %s' % (vnum, npc.get(vnum), folder))
    if problems:
        print('VERIFY halloween FAILED (%d problems)' % len(problems))
        sys.exit(1)
    print('VERIFY halloween OK')


if __name__ == '__main__':
    main()
