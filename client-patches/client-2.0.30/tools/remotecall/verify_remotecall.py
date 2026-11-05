# -*- coding: utf-8 -*-
# MT2009_PLUS_REMOTE_CALL_V1 - checks the client part of Enasir (server-patches/remotecall) on the OUT of the whole
# Yohara chain:
#   gamedata/item_proto, gamedata/item_list.txt, locale/pl/itemdesc.txt: 72368-72371 exactly as
#   patch_remotecall_client.py writes them (items.json); gamedata/mob_proto: 20874 Enasir with the folder
#   "peddler_call"; gamedata/npclist.txt: "20874 peddler_call";
#   remotecall.index / .data: every entry's crc and read-back, each the GF 26.1.11 file's bytes, the model, its two
#   motions and two effects, the icons; every name the model / motions / effects need is in some pack of OUT / BASE;
#   pack/Index lists "remotecall";
#   the root pack (OUT, else BASE): uiremotecall.py and its hooks (game.py, interfacemodule.py, uisafebox.py,
#   uiinventory.py - each with the marker), the side bar's pictures mt2009_ui/sidebar/enasir_01..03.tga.
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/remotecall/verify_remotecall.py \
#     <OUT pack dir> [<BASE pack dir>]
import os
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, '/opt/metin2/cache/tcm/gf28')
sys.path.insert(0, HERE)
import m2pack  # noqa: E402
import packlib  # noqa: E402
import patch_remotecall_client as pc  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith('--')]
OUT = args[0]
BASE = args[1] if len(args) > 1 else '/opt/metin2/cache/cY/azbase'
MARK = b'MT2009_PLUS_REMOTE_CALL_V1'
PACK = 'remotecall'
GF = '/opt/metin2/cache/gf/Gameforge_26.1.11/_client/'
fails = []
_dat = {}


def entries(pack):
    """({name: entry}, data) of pack from OUT, else BASE (None, None: in neither)"""
    for d in (OUT, BASE):
        if d and os.path.exists(os.path.join(d, pack + '.index')):
            f, v, ents = m2pack.read_index(os.path.join(d, pack + '.index'))
            if (d, pack) not in _dat:
                _dat[(d, pack)] = packlib.rd(os.path.join(d, pack + '.data'))
            return dict((e['name'], e) for e in ents), _dat[(d, pack)]
    return None, None


def read(pack, name):
    idx, dat = entries(pack)
    if idx is None or name not in idx:
        fails.append('%s: not in pack %s' % (name, pack))
        return None
    return m2pack.read_entry(dat, idx[name])


# 1) the data: the patcher's output is what OUT has (a second patch changes nothing)
for name, fn in sorted(pc.JOBS.items()):
    b = read(pc.PACK_OF[name], name)
    if b is None:
        continue
    nb, changed = fn(b)
    if changed:
        fails.append('%s: %d record(s) / line(s) of Enasir differ from patch_remotecall_client.py' % (name, changed))
b = read('gamedata', 'gamedata/mob_proto')
if b is not None:
    r = pc.mob_records(b).get(pc.MOB_VNUM)
    if r is None or r[140:204].split(b'\0')[0] != pc.MOB_FOLDER.encode():
        fails.append('gamedata/mob_proto: 20874 without the folder peddler_call')
b = read('gamedata', 'gamedata/npclist.txt')
if b is not None and not pc.npclist_ok(b):
    fails.append('gamedata/npclist.txt: no "20874 peddler_call"')

# 2) the pack: GF's bytes, the model and what it needs
need = ['d:/ymir work/npc2/peddler_call/peddler_call.msm', 'd:/ymir work/npc2/peddler_call/peddler_call.gr2',
        'd:/ymir work/npc2/peddler_call/motlist.txt', 'd:/ymir work/npc2/peddler_call/spawn.msa',
        'd:/ymir work/npc2/peddler_call/wait.msa', 'd:/ymir work/npc2/peddler_call/wait.gr2',
        'd:/ymir work/effect/npc2/peddler_call_spawn_01.mse', 'd:/ymir work/effect/npc2/peddler_call_spawn_02.mse',
        'icon/item/72368.tga', 'icon/item/72369.tga']
got = {}
if not os.path.exists(os.path.join(OUT, PACK + '.index')):
    fails.append('%s.index: not in OUT' % PACK)
else:
    f, v, ents = m2pack.read_index(os.path.join(OUT, PACK + '.index'))
    dat = packlib.rd(os.path.join(OUT, PACK + '.data'))
    for e in ents:
        if zlib.crc32(dat[e['pos']:e['pos'] + e['size']]) & 0xffffffff != e['dcrc']:
            fails.append('%s: data crc' % e['name'])
            continue
        got[e['name']] = m2pack.read_entry(dat, e)
        src = GF + (e['name'].replace('d:/', 'd_/', 1))
        if not os.path.exists(src) or open(src, 'rb').read() != got[e['name']]:
            fails.append('%s: not the GF 26.1.11 file' % e['name'])
everything = set(got)
for d in (OUT, BASE):
    if d and os.path.isdir(d):
        for p in os.listdir(d):
            if p.endswith('.index'):
                everything |= set(e['name'].lower() for e in m2pack.read_index(os.path.join(d, p))[2])
try:
    import gfres
    pre = gfres.load_ours('/opt/metin2/cache/tcm/gf28/ourpacks_pre.txt')
except Exception:
    pre = set()
for n in need:
    if n not in everything and n not in pre:
        fails.append('%s: in no pack' % n)
for n in sorted(got):
    if n.endswith(('.msa', '.mse', '.msm')):
        import re
        for ref in re.findall(rb'"([^"]+\.(?:dds|tga|gr2|mse|wav))"', got[n], re.I):
            ref = ref.decode('latin-1').replace('\\', '/').lower()
            if not ref.startswith('d:/'):
                ref = n.rsplit('/', 1)[0] + '/' + ref
            if ref not in everything and ref not in pre:
                fails.append('%s: names %s, in no pack' % (n, ref))

ix = open(os.path.join(OUT, 'Index'), 'rb').read() if os.path.exists(os.path.join(OUT, 'Index')) else b''
packs = [l.strip() for l in ix.replace(b'\r\n', b'\n').split(b'\n')]
if not packs or packs[0] != b'PACK' or PACK.encode() not in packs:
    fails.append('pack/Index: no %s line' % PACK)

# 3) root
idx, dat = entries('root')
if idx is None:
    fails.append('root: no pack')
else:
    want = {
        'uiremotecall.py': [b'def OnEvent(sub, value)', b'def UseBagItem(cell, vnum)', b'def TakeSafeboxRemote()'],
        'game.py': [b'def BINARY_RemoteCall_Event(self, sub, value)'],
        'interfacemodule.py': [b'TakeSafeboxRemote()'],
        'uisafebox.py': [b'remoteCallNext'],
        'uiinventory.py': [b'("enasir", "Enasir", "OnClickEnasir", None)', b'.UseBagItem(slotIndex, ItemVNum)'],
    }
    for name, pats in sorted(want.items()):
        if name not in idx:
            fails.append('root: %s missing' % name)
            continue
        src = m2pack.read_entry(dat, idx[name]).replace(b'\r\n', b'\n')
        if MARK not in src:
            fails.append('root %s: no %s' % (name, MARK.decode()))
        for p in pats:
            if p not in src:
                fails.append('root %s: no %r' % (name, p))
    for i in (1, 2, 3):
        n = 'mt2009_ui/sidebar/enasir_%02d.tga' % i
        if n not in idx:
            fails.append('root: %s missing' % n)

print('remotecall: %d pack entries, %s' % (len(got), 'OK' if not fails else '%d FAIL' % len(fails)))
for f in fails:
    print('FAIL ' + f)
sys.exit(1 if fails else 0)
