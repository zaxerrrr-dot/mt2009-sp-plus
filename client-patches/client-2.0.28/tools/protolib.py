# MIPX/MMPT helpers (same keys/method as dungeons_client/tools/patch_protos.py and the pets agent)
import sys, struct
sys.path.insert(0, '/w')
import m2pack
MOB_KEY = (4813894, 18955, 552631, 6822045)
ITEM_KEY = (173217, 72619434, 408587239, 27973291)
MOB_REC, ITEM_REC = 256, 184
def load_item(b):
    assert b[:4] == b'MIPX'
    ver, stride, cnt, size = struct.unpack_from('<IIII', b, 4)
    assert stride == ITEM_REC
    raw = m2pack.mcoz_decode(b[20:], ITEM_KEY)
    assert len(raw) == cnt*ITEM_REC, (len(raw), cnt)
    return ver, [raw[i*ITEM_REC:(i+1)*ITEM_REC] for i in range(cnt)]
def save_item(ver, recs):
    blob = m2pack.mcoz_encode(b''.join(recs), ITEM_KEY)
    return b'MIPX' + struct.pack('<IIII', ver, ITEM_REC, len(recs), len(blob)) + blob
def load_mob(b):
    assert b[:4] == b'MMPT'
    cnt = struct.unpack_from('<I', b, 4)[0]
    raw = m2pack.mcoz_decode(b[12:], MOB_KEY)
    assert len(raw) == cnt*MOB_REC
    return [raw[i*MOB_REC:(i+1)*MOB_REC] for i in range(cnt)]
def save_mob(recs):
    blob = m2pack.mcoz_encode(b''.join(recs), MOB_KEY)
    return b'MMPT' + struct.pack('<II', len(recs), len(blob)) + blob
def vnum(r): return struct.unpack_from('<I', r, 0)[0]
def setstr(rec, off, size, s):
    b = s.encode('cp1250'); assert len(b) < size, s
    return rec[:off] + b + b'\0'*(size-len(b)) + rec[off+size:]
