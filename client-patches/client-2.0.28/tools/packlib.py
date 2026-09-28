import struct, zlib, sys
sys.path.insert(0, "/w")
import m2pack
def rd(p): return open(p, "rb").read()
def pack_blob(newidx):
    import lzo
    comp = lzo.compress(bytes(newidx), 1, False)
    enc_len = (len(comp) + 19 + 7) // 8 * 8
    inner = struct.pack('<I', m2pack.MCOZ) + comp; inner += b'\0' * (enc_len - len(inner))
    return struct.pack('<4I', m2pack.MCOZ, enc_len, len(comp), len(newidx)) + m2pack.tea_encrypt(inner, m2pack.IDX_KEY) + b'\0' * 4

def repack_add_typed(index_path, data_path, replace, add, out_index, out_data, template_rec=None):
    """m2pack.repack_add with a type per new entry: add = {name: (raw, ctype)}.
    Existing entries keep their id/type; new ones get the next ids,
    crc32(name) and their own type; the header's count follows."""
    four, ver, ents = m2pack.read_index(index_path) if index_path else (b'EPKD', 2, [])
    data = rd(data_path) if data_path else b''
    head = bytearray(m2pack.mcoz_decode(rd(index_path), m2pack.IDX_KEY)[:12]) if index_path else bytearray(b'EPKD' + struct.pack('<II', 2, 0))
    tmpl = template_rec or ents[-1]['raw']
    next_id = max([e['id'] for e in ents] + [-1]) + 1
    names = set(e['name'] for e in ents)
    replace = dict(replace)
    added = []
    for name, (content, ct) in sorted(add.items()):
        assert name == name.lower() and '\\' not in name, name
        if name in names:
            raise SystemExit('add: exists ' + name)
        rec = bytearray(tmpl)
        struct.pack_into('<I', rec, 0, next_id)
        nb = name.encode('cp1252'); assert len(nb) < 161, name
        rec[4:165] = nb + b'\0' * (161 - len(nb))
        struct.pack_into('<I', rec, 168, zlib.crc32(nb) & 0xffffffff)
        rec[188] = ct
        added.append(dict(id=next_id, name=name, pos=1 << 40, ctype=ct, raw=bytes(rec)))
        replace[name] = content
        next_id += 1
    for n in replace: assert n in names or n in add, 'replace: missing ' + n
    allents = ents + added
    out = bytearray(); by_id = {}; pos = 0
    for e in sorted(allents, key=lambda x: (x['pos'], x['id'])):
        blob = m2pack.encode_entry(replace[e['name']], e['ctype']) if e['name'] in replace else data[e['pos']:e['pos'] + e['size']]
        slot = (len(blob) + 255) // 256 * 256
        rec = bytearray(e['raw'])
        struct.pack_into('<iiIi', rec, 172, slot, len(blob), zlib.crc32(blob) & 0xffffffff, pos)
        by_id[e['id']] = bytes(rec)
        out += blob + b'\0' * (slot - len(blob)); pos += slot
    struct.pack_into('<I', head, 8, len(allents))
    newidx = bytes(head) + b''.join(by_id[e['id']] for e in allents)
    open(out_index, 'wb').write(pack_blob(newidx)); open(out_data, 'wb').write(bytes(out))
    return len(ents), len(added), len(replace) - len(added)

