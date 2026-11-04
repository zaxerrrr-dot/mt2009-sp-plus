# -*- coding: utf-8 -*-
# MT2009_PLUS_ALCHEMY_WIKI_NAMES_V1 - the client build's part of the Dragon Stone bonus names (alchemia_names.py): the
# locale pack's locale/pl/locale_game.txt gets the DS_APPLY_* lines. No new pack, no other file. The tooltip code that
# reads them (localeinfo_point.GetDragonSoulApplyString, uitooltip.py's ITEM_TYPE_DS branch) travels in
# client-2.0.30/root like every root change (build57.py); without these lines it shows the shared names as before.
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/alchemia/build_alchemia_pack.py <BASE pack dir> <OUT pack dir> [--check]
#
# clientY.sh: anywhere after the azbase copy (a locale pack already in OUT - an earlier step changed it - is the one
# patched; no other step touches locale_game.txt's DS_APPLY_ lines), e.g. after S_msenv_pack:
#   S_alchemia_pack() { docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/alchemia/build_alchemia_pack.py $C/azbase $C/out/pack; }; step alchemia_pack $C/alchemia.json S_alchemia_pack
# and alchemia/verify_alchemia.py in the verify loop. Every entry written is read back. Idempotent: a second run
# gives "unchanged".
import json
import os
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/c36')
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, HERE)
import alchemia_names as an  # noqa: E402

PACK = 'locale'
NAME = 'locale/pl/locale_game.txt'


def main():
    import m2pack
    import packlib
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    check = '--check' in sys.argv
    base, out = args[:2]
    rd = packlib.rd
    src = out if os.path.exists(os.path.join(out, PACK + '.index')) else base
    f, v, ents = m2pack.read_index(os.path.join(src, PACK + '.index'))
    dat = rd(os.path.join(src, PACK + '.data'))
    have = dict((e['name'], e) for e in ents)
    old = m2pack.read_entry(dat, have[NAME])
    new = an.patch_locale_game(old)
    report = {'source': src, 'lines': len(an.NAMES)}
    if new == old:
        report[PACK] = 'unchanged'
    elif check:
        report[PACK] = dict(replace=[NAME])
    else:
        os.makedirs(out, exist_ok=True)
        tmp_i, tmp_d = os.path.join(out, PACK + '.index.nl'), os.path.join(out, PACK + '.data.nl')
        r = packlib.repack_add_typed(os.path.join(src, PACK + '.index'), os.path.join(src, PACK + '.data'),
                                     {NAME: new}, {}, tmp_i, tmp_d, ents[-1]['raw'])
        os.replace(tmp_i, os.path.join(out, PACK + '.index'))
        os.replace(tmp_d, os.path.join(out, PACK + '.data'))
        f, v, nw = m2pack.read_index(os.path.join(out, PACK + '.index'))
        nd = rd(os.path.join(out, PACK + '.data'))
        names = [e['name'] for e in nw]
        assert len(set(names)) == len(names)
        assert sorted(names) == sorted(have), 'entry list changed'
        for e in nw:
            assert zlib.crc32(nd[e['pos']:e['pos'] + e['size']]) & 0xffffffff == e['dcrc'], e['name']
            b = m2pack.read_entry(nd, e)
            if e['name'] == NAME:
                assert b == new
            else:
                assert b == m2pack.read_entry(dat, have[e['name']]), e['name']
        report[PACK] = dict(old=r[0], added=r[1], replaced=r[2], replaced_names=[NAME], entries=len(nw))
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
