#!/usr/bin/env python3
"""gen_ymaps_groups.py <Owsap share/locale/uk dir> <out dir>

MT2009_PLUS_YOHARA_MAPS1_V1: the spawn groups of Opuszczona Twierdza (374) and Dongan (373), copied from Owsap
v6.2.6 (the official vnums; none of them is taken in our group.txt / group_group.txt - the Dockerfile step
"Yohara: Opuszczona Twierdza, Dongan" stops the build if one is):
  group.yohara_maps.txt        6145-6152 (Dongan, EastPlane_01_*), 6194-6201 (Twierdza, EmpireCastle_*)
  group_group.yohara_maps.txt  6700-6705 (east_plane_01_*), 6711-6714 (empire_castle_*) - the "r" lines of regen.txt
The member names become the Polish names (gen_ymaps_sql.NAMES; the engine reads only the vnums).

Example: python3 tools/yohara_maps/gen_ymaps_groups.py /opt/metin2/cache/owsap/Server/Server/share/locale/uk \
         linux-port/docker/game/yohara_maps
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_ymaps_sql import NAMES  # noqa: E402

GROUPS = list(range(6145, 6153)) + list(range(6194, 6202))
GROUP_GROUPS = list(range(6700, 6706)) + list(range(6711, 6715))


def blocks(path):
    text = open(path, encoding='latin-1').read().replace('\r', '')
    out = {}
    for name, body in re.findall(r'Group\s+(\S+)\s*\{(.*?)\n\}', text, re.S):
        v = re.search(r'Vnum\s+(\d+)', body)
        if v:
            out[int(v.group(1))] = (name, body)
    return out


def ascii_pl(s):
    return s.translate(str.maketrans('ąćęłńóśźżĄĆĘŁŃÓŚŹŻ', 'acelnoszzACELNOSZZ'))


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    src, out = sys.argv[1:]
    g = blocks(os.path.join(src, 'group.txt'))
    gg = blocks(os.path.join(src, 'group_group.txt'))
    lines = ['// MT2009_PLUS_YOHARA_MAPS1_V1: Opuszczona Twierdza (374) and Dongan (373) - Owsap v6.2.6 group.txt',
             '// (tools/yohara_maps/gen_ymaps_groups.py; GENERATED)']
    for v in GROUPS:
        name, body = g[v]
        lines += ['Group\tMT2009_ymaps_%s' % name, '{', '\tVnum\t%d' % v]
        for l in body.split('\n'):
            t = l.split()
            if not t or t[0] == 'Vnum':
                continue
            mob = int(t[-1])
            assert mob in NAMES, (v, mob)
            lines.append('\t%s\t"%s"\t%d' % (t[0], ascii_pl(NAMES[mob]), mob))
        lines += ['}', '']
    open(os.path.join(out, 'group.yohara_maps.txt'), 'w', newline='\n').write('\n'.join(lines))
    lines = ['// MT2009_PLUS_YOHARA_MAPS1_V1: Opuszczona Twierdza (374) and Dongan (373) - Owsap v6.2.6 group_group.txt',
             '// (tools/yohara_maps/gen_ymaps_groups.py; GENERATED)']
    for v in GROUP_GROUPS:
        name, body = gg[v]
        lines += ['Group\tMT2009_ymaps_%s' % name, '{', '\tVnum\t%d' % v]
        for l in body.split('\n'):
            t = l.split()
            if not t or t[0] == 'Vnum':
                continue
            assert int(t[1]) in GROUPS, (v, t)
            lines.append('\t%s\t%s\t%s' % (t[0], t[1], t[2]))
        lines += ['}', '']
    open(os.path.join(out, 'group_group.yohara_maps.txt'), 'w', newline='\n').write('\n'.join(lines))


if __name__ == '__main__':
    main()
