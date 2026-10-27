# -*- coding: utf-8 -*-
# MT2009_PLUS_HALLOWEEN_V1 (Autor: Owsap - the event) - the Yohara (3.x) client build's check of the Halloween event,
# in the shape of the other Yohara verifiers (OUT [BASE], BASE by default the chain's azbase): it reads
# gamedata/item_list.txt, gamedata/npclist.txt and locale/pl/itemdesc.txt from the packs (OUT first - the one the
# client gets) and runs verify_halloween.py's checks on them (the pack "halloween" byte-equal to the GF sources,
# its Index line, the twelve item_list lines and icons, the twelve descriptions, 33008 -> halloween1).
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/halloween/verify_yhalloween.py <OUT pack dir> [<BASE pack dir>]
# The last line is "VERIFY halloween OK" or "VERIFY halloween FAILED (<n> problems)".
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, HERE)
import m2pack  # noqa: E402
import packlib  # noqa: E402
import verify_halloween as vh  # noqa: E402

FILES = {'gamedata': {'gamedata/item_list.txt': 'item_list.txt', 'gamedata/npclist.txt': 'npclist.txt'},
         'dbdata': {'locale/pl/itemdesc.txt': 'itemdesc.txt'}}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if len(args) not in (1, 2):
        raise SystemExit('usage: verify_yhalloween.py <OUT pack dir> [<BASE pack dir>]')
    out = args[0]
    base = args[1] if len(args) > 1 else '/opt/metin2/cache/cY/azbase'
    tmp = tempfile.mkdtemp(prefix='yhw')
    try:
        for pack, want in FILES.items():
            src = out if os.path.exists(os.path.join(out, pack + '.index')) else base
            f, v, ents = m2pack.read_index(os.path.join(src, pack + '.index'))
            dat = packlib.rd(os.path.join(src, pack + '.data'))
            for e in ents:
                if e['name'] in want:
                    open(os.path.join(tmp, want[e['name']]), 'wb').write(m2pack.read_entry(dat, e))
        for n in ('item_list.txt', 'itemdesc.txt', 'npclist.txt'):
            if not os.path.exists(os.path.join(tmp, n)):
                print('BAD no %s in the packs' % n)
                print('VERIFY halloween FAILED (1 problems)')
                sys.exit(1)
        sys.argv = [vh.__file__, base, out, tmp, os.path.join(tmp, 'npclist.txt')]
        vh.main()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    main()
