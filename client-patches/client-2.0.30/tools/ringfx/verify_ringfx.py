# -*- coding: utf-8 -*-
# MT2009_PLUS_RING_EFFECTS_V1 - checks the pack build_ringfx_packs.py wrote (on the OUT of the whole Yohara chain):
#   ringfx.index / ringfx.data hold exactly the manifest's names (ringfx_files.json: size, sha256, entry type), every
#   entry's crc and read-back; pack/Index lists "ringfx"; no other pack carries one of its names;
#   the exe overlay (PythonPlayerSettingsModule.cpp, ENABLE_MT2009_RING_EFFECTS) registers all nine EFFECT_*_EQUIP, each
#   .mse is in this pack or in the install's etc pack with the GF client 26.1.11's bytes (OFFICIAL below), and every
#   texture / mesh an .mse names is in this pack or in a listed pack;
#   the SE numbers: server-patches/ringfx (edits.json) and the exe's Server/common/length.h append the same nine
#   SE_EQUIP_* in the same order right after SE_ELEC_ATTACK_HIT (54), i.e. 55-63, and the exe maps each to its effect.
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/ringfx/verify_ringfx.py \
#     <OUT pack dir> [<BASE pack dir>] [--etc=<the install's pack dir with etc.index>]
import hashlib
import json
import os
import re
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, HERE)
import m2pack  # noqa: E402
import packlib  # noqa: E402
import build_ringfx_packs as B  # noqa: E402

REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
EXE = os.path.join(REPO, 'client-patches', 'exe')
BUFF = 'd:/ymir work/effect/etc/buff/'
# SE / EFFECT name -> (vnum, the .mse the exe registers)
EFFECTS = [
    ('WILL_RING', 71148, 'buff_item5.mse'),
    ('DEADLY_RING', 71149, 'deadly_ring.mse'),
    ('HERO_MEDAL', 71158, 'buff_symbol1.mse'),
    ('BLUE_CANDY', 71180, 'buff_item16.mse'),
    ('GREEN_CANDY', 71181, 'green_candy.mse'),
    ('YELLOW_CANDY', 71188, 'buff_item8.mse'),
    ('CHOCOLATE_PENDANT', 71199, 'buff_item10.mse'),
    ('EVIL_PENDANT', 71202, 'buff_item13.mse'),
    ('GUARD_PENDANT', 72054, 'buff_item14.mse'),
]
# the GF client 26.1.11's files the seven official effects use (md5, as in d_/ymir work/effect/etc/buff and our etc pack)
OFFICIAL = {
    'buff_item5.mse': '3dc1f2e7474c9da38ad849b305da80ef',
    'buff_symbol1.mse': '3cfa4c74f8db3fd3b6172f1d5f535c84',
    'buff_item16.mse': 'c27013267039f7ecab8d632ad662610d',
    'buff_item8.mse': '195c5988afdc841cefbf3f7c70563e60',
    'buff_item10.mse': '8f488786956c3d226c2ee93de0d53001',
    'buff_item13.mse': '742ef160bc830c6d202af099cb087aa3',
    'buff_item14.mse': '3c4f9bc957f63395b25f2bcc561e470a',
    'buff_item1.mde': '4f6ff5f47f20f0a0fa4b75c1af7995b2',
    'item_buff1.dds': '544dfe605bb7ed25b4197ea5446852ac',
    'light616.dds': '7fc5c4a0c7358a6d603e9fafa175a8b2',
    'magic_ring1.dds': 'b7d61855a8060aefd0fc0170b593f3fe',
    'item_symbol1_1.dds': '32c7b617323a08f17330e75c3343934b',
    'item_symbol1_2.dds': '6e291075768da1f9c2ea7d90af71d046',
    'candy2.dds': 'e743d6078fde367b2b7572aab348393c',
    'candy3.dds': '97ed47f7283088386356f1b85dfbf37b',
    'chocolate_pendant1.dds': '1167c3a9bdbf923cdbde58b05e945f58',
    '71202_eff2.dds': '24f124f6faaeef7c91307f6b15741c2c',
    '71202_eff3.dds': 'db1ade9fda6377d1f2628ee21425bce4',
    '72054_eff01.dds': '78e355b71524dc56fd13544e35ab2707',
    '72054_eff02.dds': 'a5e03fcb5628d58c4b378c54aec5467c',
}

args = [a for a in sys.argv[1:] if not a.startswith('--')]
opts = dict(a[2:].split('=', 1) for a in sys.argv[1:] if a.startswith('--') and '=' in a)
OUT = args[0]
BASE = args[1] if len(args) > 1 else '/opt/metin2/cache/cY/azbase'
ETC = opts.get('etc', B.ETC_DEFAULT)
fails = []


def text(path):
    return open(path, 'rb').read().decode('latin-1').replace('\r\n', '\n') if os.path.exists(path) else ''


# ---- the pack
m = B.manifest()
got = {}
if not os.path.exists(os.path.join(OUT, B.PACK + '.index')):
    fails.append('%s.index: not in OUT' % B.PACK)
else:
    f, v, ents = m2pack.read_index(os.path.join(OUT, B.PACK + '.index'))
    dat = packlib.rd(os.path.join(OUT, B.PACK + '.data'))
    for e in ents:
        if zlib.crc32(dat[e['pos']:e['pos'] + e['size']]) & 0xffffffff != e['dcrc']:
            fails.append('%s: data crc' % e['name'])
            continue
        b = m2pack.read_entry(dat, e)
        got[e['name']] = b
        w = m.get(e['name'])
        if w is None:
            fails.append('%s: not in the manifest' % e['name'])
        elif len(b) != w['size'] or hashlib.sha256(b).hexdigest() != w['sha256']:
            fails.append('%s: not the manifest\'s bytes' % e['name'])
        elif e['ctype'] != w['ctype']:
            fails.append('%s: entry type %d, the manifest %d' % (e['name'], e['ctype'], w['ctype']))
    fails += ['%s: missing' % n for n in sorted(set(m) - set(got))]

ix = open(os.path.join(OUT, 'Index'), 'rb').read() if os.path.exists(os.path.join(OUT, 'Index')) else b''
packs = [l.strip() for l in ix.replace(b'\r\n', b'\n').split(b'\n')]
if not packs or packs[0] != b'PACK' or B.PACK.encode() not in packs:
    fails.append('pack/Index: no %s line' % B.PACK)

# ---- every other pack (BASE, OUT, the install's etc pack): where each name lives
WHERE = {}
etc_files = {}
for _d in (BASE, OUT, ETC):
    if not os.path.isdir(_d):
        if _d == ETC:
            fails.append('%s: no install pack dir (--etc=)' % ETC)
        continue
    for _f in sorted(os.listdir(_d)):
        if _f.endswith('.index') and _f[:-6] != B.PACK:
            for e in m2pack.read_index(os.path.join(_d, _f))[2]:
                WHERE.setdefault(e['name'], _f[:-6])
                if _d == ETC and _f == 'etc.index' and e['name'].startswith(BUFF):
                    etc_files[e['name']] = e
for n in sorted(m):
    if n in WHERE:
        fails.append('%s: also in pack %s (it would win)' % (n, WHERE[n]))

# the official files: in the etc pack with the GF bytes
etc_bytes = {}
if etc_files:
    dat = packlib.rd(os.path.join(ETC, 'etc.data'))
    for short, md5 in sorted(OFFICIAL.items()):
        e = etc_files.get(BUFF + short)
        if e is None:
            fails.append('%s: not in the etc pack' % short)
            continue
        b = m2pack.read_entry(dat, e)
        etc_bytes[BUFF + short] = b
        if hashlib.md5(b).hexdigest() != md5:
            fails.append('%s: the etc pack\'s bytes are not the GF client\'s' % short)
else:
    fails.append('%s/etc.index: no effect/etc/buff files' % ETC)

# ---- each effect: the exe registers it, its .mse is there, every file it names is there
src = text(os.path.join(EXE, 'UserInterface', 'PythonPlayerSettingsModule.cpp'))
refs_n = 0
for name, vnum, mse in EFFECTS:
    full = BUFF + mse
    if not re.search(r'\{pkBase\.EFFECT_%s_EQUIP,\s*"",\s*"%s"\}' % (name, re.escape(full)), src):
        fails.append('PythonPlayerSettingsModule.cpp: EFFECT_%s_EQUIP does not load %s' % (name, full))
    body = got.get(full) or etc_bytes.get(full)
    if body is None:
        fails.append('%s (%d): %s in neither ringfx nor the etc pack' % (name, vnum, mse))
        continue
    if re.search(rb'CycleLoopEnable\s+1', body):
        fails.append('%s: loops' % mse)
    for r in re.findall(rb'"([^"]+\.(?:dds|tga|mse|mde|msf))"', body, re.I):
        r = r.decode('latin-1').replace('\\', '/').lower()
        if '/' not in r:
            r = BUFF + r
        refs_n += 1
        if r not in got and r not in WHERE:
            fails.append('%s: %s is in no listed pack' % (mse, r))

# ---- the SE numbers: server == exe, 55-63 after SE_ELEC_ATTACK_HIT
want = ['SE_EQUIP_%s' % n for n, v, f in EFFECTS]
srv = json.load(open(os.path.join(REPO, 'server-patches', 'ringfx', 'edits.json')))
srv_len = [e for e in srv if e['file'].endswith('common/length.h')]
srv_se = re.findall(r'\t(SE_\w+),', srv_len[0]['new']) if srv_len else []
if srv_se != ['SE_ELEC_ATTACK_HIT'] + want:
    fails.append('server-patches/ringfx length.h: %s' % srv_se)
exe_len = text(os.path.join(EXE, 'Server', 'common', 'length.h'))
mm = re.search(r'enum SPECIAL_EFFECT\s*\{(.*?)\};', exe_len, re.S)
exe_se = re.findall(r'^\s*(SE_\w+)\s*,', mm.group(1), re.M) if mm else []
if exe_se[-10:] != ['SE_ELEC_ATTACK_HIT'] + want or len(exe_se) != 64:
    fails.append('exe Server/common/length.h: the last ones %s, %d values (55-63 need 64)' % (exe_se[-10:], len(exe_se)))
item = text(os.path.join(EXE, 'UserInterface', 'PythonNetworkStreamPhaseGameItem.cpp'))
mod = text(os.path.join(EXE, 'UserInterface', 'PythonCharacterManagerModule.cpp'))
ib = text(os.path.join(EXE, 'UserInterface', 'InstanceBase.h'))
for n, v, f in EFFECTS:
    if not re.search(r'case SE_EQUIP_%s:[^\n]*\n(?:[^\n]*static_assert[^\n]*\n)?\s*effect = CInstanceBase::EFFECT_%s_EQUIP;' % (n, n), item):
        fails.append('PythonNetworkStreamPhaseGameItem.cpp: SE_EQUIP_%s is not mapped' % n)
    if '"EFFECT_%s_EQUIP", CInstanceBase::EFFECT_%s_EQUIP' % (n, n) not in mod:
        fails.append('PythonCharacterManagerModule.cpp: no chrmgr.EFFECT_%s_EQUIP' % n)
    if '\tEFFECT_%s_EQUIP,' % n not in ib:
        fails.append('InstanceBase.h: no EFFECT_%s_EQUIP' % n)
if ib.find('EFFECT_GUARD_PENDANT_EQUIP') > ib.find('\t\t\tEFFECT_NUM,'):
    fails.append('InstanceBase.h: EFFECT_NUM is not last')

print('ringfx: %d files, 9 effects (%d official from etc), %d texture/mesh names, SE 55-63, %d problem(s)'
      % (len(got), sum(1 for n, v, f in EFFECTS if BUFF + f in etc_bytes), refs_n, len(fails)))
for f in fails:
    print('  ' + f)
sys.exit(1 if fails else 0)
