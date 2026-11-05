# -*- coding: utf-8 -*-
# MT2009_PLUS_VERIFY_LATER_WRITERS_V1 - the "a second patch must change nothing" checks of the early Yohara batch
# verifiers (ymaps3, ymaps4, yiluzja, yworldboss) run on the OUT of the WHOLE chain. Later builders rewrite some of
# the batch's rows on purpose - gfint / protoglobal / mobyglobal / refineglobal / brakiwiki / pety ... put the global
# server's values over them - so re-applying an early batch changes rows that are there, only with the later values.
# That is not a missing row. split(name, before, after) tells the two apart: the keys (item / mob vnum, the first
# column of a text table) the re-patch ADDS are missing rows (a real failure); keys present in both whose bytes
# differ were rewritten by a later step (a note).
import struct

ITEM_KEY = (173217, 72619434, 408587239, 27973291)
ITEM_RECORD = 184
MOB_KEY = (4813894, 18955, 552631, 6822045)
MOB_RECORD = 256


def _records(name, b):
    import m2pack
    if name.endswith('item_proto'):
        assert b[:4] == b'MIPX'
        ver, stride, cnt, size = struct.unpack_from('<IIII', b, 4)
        raw = m2pack.mcoz_decode(b[20:], ITEM_KEY)
        return dict((struct.unpack_from('<I', raw, i * stride)[0], raw[i * stride:(i + 1) * stride])
                    for i in range(cnt))
    if name.endswith('mob_proto'):
        magic, cnt, esize = struct.unpack_from('<4sII', b, 0)
        assert magic == b'MMPT', magic
        raw = m2pack.mcoz_decode(b[12:12 + esize], MOB_KEY)
        R = MOB_RECORD
        return dict((struct.unpack_from('<I', raw, i * R)[0], raw[i * R:(i + 1) * R]) for i in range(cnt))
    rows = {}
    for line in b.replace(b'\r', b'').split(b'\n'):
        s = line.strip()
        if not s or s.startswith((b'#', b'//')):
            continue
        k = s.split(None, 1)[0]
        rows.setdefault(k, []).append(s)
    return rows


def split(name, before, after):
    """(missing keys, keys present with other content) of the re-patched `after` against `before`"""
    a = _records(name, before)
    b = _records(name, after)
    missing = sorted(k for k in b if k not in a)
    rewritten = sorted(k for k in b if k in a and a[k] != b[k]) + sorted(k for k in a if k not in b)
    return missing, rewritten


def check(name, before, after, fail, notes):
    """append to fail the missing rows, to notes the rows a later step rewrote"""
    missing, rewritten = split(name, before, after)
    if missing:
        fail.append('%s: %d row(s) missing %s' % (name, len(missing), [k if isinstance(k, int) else k.decode('latin1')
                                                                       for k in missing[:10]]))
    if rewritten:
        notes.append('%s: %d row(s) of this batch rewritten by a later step (global values) - kept'
                     % (name, len(rewritten)))
    return missing, rewritten
