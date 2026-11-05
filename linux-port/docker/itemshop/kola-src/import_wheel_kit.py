#!/usr/bin/env python3
# MT2009_PLUS_KOLA_V1 (wheel 246, the owner 5 Nov 2026: "Dodaj nowe kolo do listy kol"): adds one wheel from the
# owner's simulator package (wheel-kit: config/<id>.json + assets/*.webp) to app/itemshop/kola/kola.json -
# name, costs per tier, the 16 field pictures per tier, the special/standard pools 1:1 (source id, count, weight,
# in the package's order), the new source items (name, description, duration, picture) - and appends the wheel
# to the end of the rotation. Converts the pictures the shop does not have yet:
#   app/itemshop/kola/img/i_<hash>.png   - prize/field icons, 112x112 RGBA (as the other wheels' icons)
#   app/itemshop/kola/img/bg_<id>.jpg    - the page background, the middle 740x475 of the source's 972x490
#   client-2.0.30/tools/kola/bg/bg_<id>.jpg - the whole 972x490 art for the F12 window (make_kola_ui.py)
# The package's mechanics (special fields, key fields, keys to advance, tier time) must be ours - else it stops.
# The item mapping (source id -> our vnum) stays in przedmioty.json; then gen_kola_sql.py and make_kola_ui.py.
# Only reads the package (JSON and images) - never runs its code.
#   python3 import_wheel_kit.py <wheel-kit dir> <wheel id>      (needs PIL with webp)
import json
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
KOLA = os.path.normpath(os.path.join(HERE, '..', 'app', 'itemshop', 'kola'))
CFG = os.path.join(KOLA, 'kola.json')
IMG = os.path.join(KOLA, 'img')
CLIENT_BG = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..', 'client-patches', 'client-2.0.30', 'tools', 'kola', 'bg'))
ICON = 112
PAGE_BG = (740, 475)


def num(x):
    f = float(x)
    return int(f) if f == int(f) else f


def icon_name(webp):
    return 'i_' + webp.rsplit('.', 1)[0] + '.png'


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__ or 'usage: import_wheel_kit.py <wheel-kit dir> <wheel id>')
    kit, wid = sys.argv[1], sys.argv[2]
    assets = os.path.join(kit, 'assets')
    src = json.load(open(os.path.join(kit, 'config', wid + '.json'), encoding='utf-8'))
    cfg = json.load(open(CFG, encoding='utf-8'))
    if str(src['id']) != wid:
        raise SystemExit('config id %s != %s' % (src['id'], wid))
    # the mechanics must be ours
    if src['keyPositions'] != cfg['key_fields'] or int(src['keysToAdvance']) != int(cfg['keys_needed']) \
            or int(src['slotCount']) != 16:
        raise SystemExit('key fields / keys / field count differ from kola.json')
    for t in src['tiers']:
        lv = str(t['level'])
        if t['specialPositions'] != cfg['special_fields'][lv]:
            raise SystemExit('tier %s special fields %s, ours %s' % (lv, t['specialPositions'], cfg['special_fields'][lv]))
        if int(t['timeLimitSeconds']) not in (0, int(cfg['tier_seconds'])):
            raise SystemExit('tier %s time %s, ours %s' % (lv, t['timeLimitSeconds'], cfg['tier_seconds']))
        if len(t['previewIcons']) != 16:
            raise SystemExit('tier %s has %d field pictures' % (lv, len(t['previewIcons'])))

    pictures = set()
    wheel = {'name': src['name'], 'bg': 'bg_%s.jpg' % wid, 'currency': 1, 'costs': {}, 'fields': {}, 'prizes': {}}
    new_items = 0
    for t in src['tiers']:
        lv = str(t['level'])
        wheel['costs'][lv] = int(t['cost'])
        wheel['fields'][lv] = [icon_name(x) for x in t['previewIcons']]
        pictures.update(t['previewIcons'])
        wheel['prizes'][lv] = {}
        for pool in ('special', 'standard'):
            entries = []
            for p in t['prizes'][pool]:
                sid = str(p['sourceItemShopId'])
                entries.append([sid, int(p['quantity']), num(p['weight'])])
                pictures.add(p['icon'])
                if sid not in cfg['src_items']:
                    cfg['src_items'][sid] = {'name': p['name'], 'desc': p.get('description') or '',
                                             'dur': p.get('durationSeconds'), 'img': icon_name(p['icon'])}
                    new_items += 1
            wheel['prizes'][lv][pool] = entries
    cfg['wheels'][wid] = wheel
    if int(wid) not in cfg['rotation']['order']:
        cfg['rotation']['order'].append(int(wid))

    made = 0
    for webp in sorted(pictures):
        dst = os.path.join(IMG, icon_name(webp))
        if os.path.exists(dst):
            continue
        im = Image.open(os.path.join(assets, webp)).convert('RGBA')
        im.resize((ICON, ICON), Image.LANCZOS).save(dst, optimize=True)
        made += 1
    bg = Image.open(os.path.join(assets, src['background'])).convert('RGB')
    os.makedirs(CLIENT_BG, exist_ok=True)
    bg.save(os.path.join(CLIENT_BG, 'bg_%s.jpg' % wid), quality=92)
    left = (bg.size[0] - PAGE_BG[0]) // 2
    top = (bg.size[1] - PAGE_BG[1]) // 2
    bg.crop((left, top, left + PAGE_BG[0], top + PAGE_BG[1])).save(os.path.join(IMG, 'bg_%s.jpg' % wid), quality=90)

    open(CFG, 'w', encoding='utf-8').write(json.dumps(cfg, ensure_ascii=False, indent=1))
    print('wheel %s %s: costs %s, %d entries, %d new source items, %d new pictures, rotation %s' % (
        wid, src['name'], wheel['costs'],
        sum(len(v) for t in wheel['prizes'].values() for v in t.values()), new_items, made, cfg['rotation']['order']))


if __name__ == '__main__':
    main()
