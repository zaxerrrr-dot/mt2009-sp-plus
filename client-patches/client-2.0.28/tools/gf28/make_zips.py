# MT2009 client 2.0.28 zips from /opt/metin2/cache/tcm/c28/pack (re-runnable):
# per-pack zips (<= 29 MB; packs appended to Index also carry pack/Index), the full
# klient-test-2.0.28.zip and its copy for SFTP: /opt/metin2/dist/klient/klient-test-2.0.28-pelny.zip
import os, zipfile, hashlib, shutil, time
C = '/opt/metin2/cache/tcm/c28/pack'; O = '/opt/metin2/cache/tcm'; V = '2.0.28'
LIMIT = 29 * 1024 * 1024
def mk(z, names):
    tmp = z + '.tmp'
    with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for n in names:
            zi = zipfile.ZipInfo('pack/' + n, time.localtime(os.path.getmtime(os.path.join(C, n)))[:6])
            zi.compress_type = zipfile.ZIP_DEFLATED; zi.external_attr = 0o644 << 16
            zf.writestr(zi, open(os.path.join(C, n), 'rb').read())
    with zipfile.ZipFile(tmp) as zf:
        assert zf.testzip() is None
        for n in names: assert zf.read('pack/' + n) == open(os.path.join(C, n), 'rb').read()
    os.replace(tmp, z); return os.path.getsize(z)
packs = sorted(f[:-6] for f in os.listdir(C) if f.endswith('.index'))
for p in packs:
    names = [p + '.index', p + '.data'] + (['Index'] if p in ('newpet', 'ochao', 'goblin') or p.startswith('gf_') else [])
    z = '%s/klient-test-%s-%s.zip' % (O, V, p); s = mk(z, names)
    assert s <= LIMIT, (z, s)
    print('%-36s %10d  %5.1f MB' % (os.path.basename(z), s, s / 1048576))
full = '%s/klient-test-%s.zip' % (O, V)
s = mk(full, [p + e for p in packs for e in ('.index', '.data')] + ['Index'])
print('%-36s %10d  %5.1f MB' % (os.path.basename(full), s, s / 1048576))
os.makedirs('/opt/metin2/dist/klient', exist_ok=True)
d = '/opt/metin2/dist/klient/klient-test-%s-pelny.zip' % V
shutil.copyfile(full, d); os.chmod(d, 0o644)
h = hashlib.sha256(open(d, 'rb').read()).hexdigest()
open(d + '.sha256', 'w').write('%s  %s\n' % (h, os.path.basename(d))); os.chmod(d + '.sha256', 0o644)
print(d, os.path.getsize(d), h)
