# Read back every entry of every pack in a pack dir (default c28/pack); report duplicates across packs.
import sys, os, zlib, collections
sys.path.insert(0, '/opt/metin2/cache/tcm/tz'); import m2pack
D = sys.argv[1] if len(sys.argv) > 1 else '/opt/metin2/cache/tcm/c28/pack'
order = [l.strip() for l in open(D + '/Index').read().split('\n') if l.strip() and l.strip() not in ('PACK', '*')]
owner = collections.defaultdict(list); tot = 0
for p in sorted(f[:-6] for f in os.listdir(D) if f.endswith('.index')):
    f, v, ents = m2pack.read_index(D + '/%s.index' % p); data = open(D + '/%s.data' % p, 'rb').read()
    n = 0; size = 0
    for e in ents:
        blob = data[e['pos']:e['pos'] + e['size']]
        assert len(blob) == e['size'], (p, e['name'])
        assert zlib.crc32(blob) & 0xffffffff == e['dcrc'], (p, e['name'])
        assert e['fcrc'] == zlib.crc32(e['name'].encode('cp1252')) & 0xffffffff, (p, e['name'])
        raw = m2pack.read_entry(data, e); size += len(raw); n += 1
        owner[e['name']].append(p)
    tot += n
    print('%-11s %5d entries OK, %7.1f MB unpacked, in Index: %s' % (p, n, size / 1e6, p in order))
dups = dict((k, v) for k, v in owner.items() if len(v) > 1)
print('total', tot, 'entries; names in more than one pack:', len(dups))
for k, v in sorted(dups.items())[:30]: print('  dup', k, v)
