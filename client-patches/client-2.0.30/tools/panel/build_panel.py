# MT2009_PLUS_DUNGEON_PANEL_V1 - client packs of the dungeon panel on the CURRENT base (default c30/pack):
# root (4 new modules, 3 sidebar icons, game.py + uiinventory.py marker edits) and the new pack az_ui (the
# window's images). Output: only the changed packs + Index.
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 .../build_panel.py [BASE] [OUT]
import os, sys, json, zlib, shutil, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
W = '/opt/metin2/cache/arezzo-work/panel/client'
sys.path.insert(0, '/opt/metin2/cache/tcm/tz'); sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az29')
import m2pack, packlib
BASE = sys.argv[1] if len(sys.argv) > 1 else '/opt/metin2/cache/tcm/c30/pack'
OUT = sys.argv[2] if len(sys.argv) > 2 else W + '/out/pack'
TEXT = ('.txt', '.sub', '.py')
def ctype(name): return 2 if name.endswith(TEXT) else 1
rd = packlib.rd
shutil.rmtree(OUT, ignore_errors=True); os.makedirs(OUT)
allnames = {}
for p in sorted(f[:-6] for f in os.listdir(BASE) if f.endswith('.index')):
    for e in m2pack.read_index(BASE + '/%s.index' % p)[2]: allnames.setdefault(e['name'], p)
def entry(pack, name):
    f, v, ents = m2pack.read_index(BASE + '/%s.index' % pack); d = rd(BASE + '/%s.data' % pack)
    return [m2pack.read_entry(d, e) for e in ents if e['name'] == name][0]
report = {}; expect = {}
def build(pack, add_items, rep_items):
    idx, dat = BASE + '/%s.index' % pack, BASE + '/%s.data' % pack
    exists = os.path.exists(idx)
    have = {}
    if exists:
        f, v, ents = m2pack.read_index(idx); data = rd(dat); have = dict((e['name'], e) for e in ents); tmpl = ents[-1]['raw']
    else:
        f, v, ents = m2pack.read_index(BASE + '/goblin.index'); tmpl = ents[-1]['raw']; data = b''
    rep, add = {}, {}
    for k, b in rep_items.items():
        assert k in have, (pack, 'replace of a missing entry', k)
        if m2pack.read_entry(data, have[k]) != b: rep[k] = b
    for k, b in add_items.items():
        if k in have:
            if m2pack.read_entry(data, have[k]) != b: rep[k] = b
        else:
            assert k not in allnames, (pack, k, 'already in pack', allnames.get(k))
            add[k] = (b, ctype(k))
    if not rep and not add:
        report[pack] = 'unchanged'; return
    r = packlib.repack_add_typed(idx if exists else None, dat if exists else None, rep, add,
                                 OUT + '/%s.index' % pack, OUT + '/%s.data' % pack, tmpl)
    report[pack] = dict(old=r[0], added=r[1], replaced=r[2])
    expect[pack] = dict(list(rep.items()) + [(k, b) for k, (b, c) in add.items()])

# root: the current game.py / uiinventory.py with the marker edits (patch_root.py, idempotent)
tmp = W + '/tmp_root'; shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
for n in ('game.py', 'uiinventory.py'):
    open(tmp + '/' + n, 'wb').write(entry('root', n))
subprocess.check_call([sys.executable, W + '/patch_root.py', tmp, tmp])
root_rep = dict((n, rd(tmp + '/' + n)) for n in ('game.py', 'uiinventory.py'))
R = W + '/root/'
root_add = {}
for n in ('dungeoninfo.py', 'uidungeoninfo.py', 'uiscript/dungeoninfowindow.py', 'uiscript/dungeonrankingwindow.py',
          'mt2009_ui/sidebar/dungeon_01.tga', 'mt2009_ui/sidebar/dungeon_02.tga', 'mt2009_ui/sidebar/dungeon_03.tga'):
    root_add[n] = rd(R + n)
build('root', root_add, root_rep)
shutil.rmtree(tmp, ignore_errors=True)

# az_ui: the window's images
A = '/opt/metin2/cache/arezzo/cpack/files/'
UI = 'd:/ymir work/ui/game/dungeon_info/'
ui = {}
for n in ('bonus.png', 'clock.png', 'dropbutton0.png', 'dropbutton1.png', 'dropbutton2.png', 'dungeon_bg.png', 'header.png',
          'list_btn_default.png', 'list_btn_down.png', 'list_btn_over.png', 'slot_grid.png', 'teleportbutton0.png',
          'teleportbutton1.png', 'teleportbutton2.png', 'unkown-element.png'):
    ui[UI + n] = rd(A + 'ymir work/ui/game/dungeon_info/' + n)
for src, dst in (('dungeon_allbg.png', 'dungeon_allbg.png'), ('header_dungeon.png', 'header_dungeon.png'),
                 ('ranking_header.png', 'ranking_header.png'), ('ranking_slot.png', 'ranking_slot.png'),
                 ('itemshop/scroll_slot.png', 'scroll_slot.png'), ('itemshop/scroll_button.png', 'scroll_button.png')):
    ui[UI + dst] = rd(A + 'ymir work/ui/' + src)
G = W + '/ui/game/dungeon_info/'
ui[UI + 'req_slot_frame.tga'] = rd(G + 'req_slot_frame.tga')
for a in range(3):
    for b in range(3):
        for ext in ('sub', 'tga'):
            ui[UI + 'button/rank_button%d%d.%s' % (a, b, ext)] = rd(G + 'button/rank_button%d%d.%s' % (a, b, ext))
# dungeon icons by OUR map index (the list names a dungeon by its map)
ICONS = {0: 'locale/pl/dungeon_info/0.png', 66: 'locale/pl/dungeon_info/66.png', 216: 'locale/pl/dungeon_info/216.png',
         71: 'locale/pl/dungeon_info/217.png', 351: 'locale/pl/dungeon_info/351.png', 352: 'locale/pl/dungeon_info/352.png',
         363: 'ymir work/ui/dungeon_info/17.png', 364: 'ymir work/ui/dungeon_info/13.png', 365: 'ymir work/ui/dungeon_info/14.png',
         366: 'ymir work/ui/dungeon_info/12.png'}
for m, src in ICONS.items():
    ui['d:/ymir work/ui/dungeon_info/%d.png' % m] = rd(A + src)
build('az_ui', ui, {})

ix = rd(BASE + '/Index')
if b'\naz_ui\n' not in ix and os.path.exists(OUT + '/az_ui.index'):
    ix = ix.rstrip(b'\n') + b'\n*\naz_ui\n'
if ix != rd(BASE + '/Index'):
    open(OUT + '/Index', 'wb').write(ix); report['Index'] = 'updated'

for pack, exp in expect.items():
    f, v, nw = m2pack.read_index(OUT + '/%s.index' % pack); nd = rd(OUT + '/%s.data' % pack)
    names = [e['name'] for e in nw]; assert len(set(names)) == len(names), pack
    got = {}
    for e in nw:
        assert zlib.crc32(nd[e['pos']:e['pos'] + e['size']]) & 0xffffffff == e['dcrc'], (pack, e['name'])
        assert e['fcrc'] == zlib.crc32(e['name'].encode('cp1252')) & 0xffffffff, (pack, e['name'])
        got[e['name']] = m2pack.read_entry(nd, e)
    bad = [k for k, b in exp.items() if got.get(k) != b]; assert not bad, (pack, bad[:5])
    if os.path.exists(BASE + '/%s.index' % pack):
        f, v, old = m2pack.read_index(BASE + '/%s.index' % pack); od = rd(BASE + '/%s.data' % pack)
        ch = [e['name'] for e in old if e['name'] not in exp and m2pack.read_entry(od, e) != got[e['name']]]
        assert not ch, (pack, ch[:5])
    report[pack]['verified_entries'] = len(nw)
json.dump(report, open(W + '/build_report.json', 'w'), indent=1)
print(json.dumps(report, indent=1))
