# -*- coding: utf-8 -*-
# MT2009_PLUS_UICHECK_V1 - the verify loop's check of the 3.0.4 windows on the PLAYERS' install (klient-test-2.37 +
# yohara-3.0.0 + 3.0.3 update zips + OUT; check_ui_assets.py): every picture each new / changed window opens (and the image of every
# .sub among them) is in a pack the client lists, and every item_list row new since 3.0.1 has its icon (Kamienie
# Zywiolow, Wezowy Czepiec, the boxes...). The players' base packs (etc, item ...) have no listing here: a name counts
# as theirs only when the base client's own root opens it (/opt/metin2/cache/tcm/ours/root). 3.0.4 crashed on
# Alt+H and on Balathor's boss window because its builders took the exe smoke client's etc for the players'.
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/uicheck/verify_ui_304.py \
#     <OUT pack dir>
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import check_ui_assets as U  # noqa: E402

FEATURES = [
    ('autohunt_test', ['uiautohunt_test.py', 'uiscript/autohunttestwindow.py', 'uiscript/autohunttestoptionwindow.py',
                       'uiscript/autohunttestrangewindow.py']),
    ('balathor', ['uiguildwhitedragon.py', 'uiscript/guildwhitedragonlairwindow.py']),
    ('wieza', ['uiwiezasm.py', 'sungmastate.py', 'uiscript/sungmaheetowerenter.py',
               'uiscript/sungmaheetowerinformationboard.py']),
    ('community', ['uicommunity.py']),
    ('npcloc', ['uinpclocationhelper.py', 'uiscript/npclocationhelper_atlaswindow.py',
                'uiscript/npclocationhelper_npcinfowindow.py', 'uiscript/npclocationhelper_mobinfowindow.py']),
    ('cube', ['uicuberenewal.py', 'uiscript/cuberenewalwindow.py']),
    ('chardetails', ['uiattributelist.py', 'uiscript/characterdetailswindow.py']),
    ('gaya2', ['gayacurrency.py', 'uiscript/expandedmoneytaskbar.py']),
    ('addeq', ['uiaddeq.py']),
    ('monstercard', ['uimonstercard.py', 'uiscript/monstercardwindow.py', 'uiscript/monstercardachievdetailwindow.py']),
    ('questren', ['questrenewal.py', 'uicharacter.py', 'uiscript/characterwindow.py']),  # MT2009_PLUS_QUEST_RENEWAL_V1
    # 3.0.6 (hotfix 30.10: the expanded quick slot's pictures were in no pack of the players' install)
    ('quickslot2', ['uitaskbar.py', 'quickslotstate.py', 'uiscript/expandedquickslot.py']),
    ('inv2', ['inventoryv2.py', 'uiinventory.py', 'uiscript/inventorywindowv2.py', 'uiscript/inventoryequipwindow.py',
              'uiscript/inventorywindow.py']),
    ('relikty', ['uirelikt.py', 'relikt_data.py', 'uiscript/reliktwindow.py']),
    ('konie', ['uikonierozwoj.py']),
    ('zywiolbroni', ['uiweaponelement.py', 'welem.py', 'welemfx.py', 'uiscript/weaponelementdialog.py',
                     'uiscript/weaponelementchange.py']),
    ('dmgprint+round306', ['game.py', 'interfacemodule.py', 'uiaffectbar.py', 'uiattributelist.py', 'uiautohunt.py',
                           'uisystem.py', 'uitooltip.py', 'uiaddeq.py', 'uiingameevent.py', 'keybind.py',
                           'uiscript/systemdialog.py']),
    # MT2009_PLUS_FISH_PUZZLE_V1 / V2: Event Rybacki - Puzzle, the package "Mini Game Fish Event (17.3)" (the pictures in the
    # pack "fishpuzzle", tools/fishpuzzle; the completion effects and the page buttons in "minigames")
    ('fishpuzzle', ['uifishpuzzle.py', 'uiminigame.py', 'uiminigamefishevent.py', 'uiscript/minigamewindow.py',
                    'uiscript/minigamedialog.py', 'uiscript/minigamefishgamepage.py',
                    'uiscript/minigamefisheventwaitingpage.py']),
    # MT2009_PLUS_GROWTH_PET_V1: the growth pet's windows (their art: pack "pety", tools/pety/build_pety_packs.py)
    ('pety', ['uipetinfo.py', 'uiscript/petinformationwindow.py', 'uiscript/petfeedwindow.py',
              'uiscript/pethatchingwindow.py', 'uiscript/petnamechangewindow.py',
              'uiscript/petminiinformationwindow.py', 'uiscript/petpotentialwindow.py']),
]

OUT = [a for a in sys.argv[1:] if not a.startswith('--')][0]
# names known to be fine although no listed pack has them (with the reason) - matched on the problem's text
ACCEPTED = {
    'game.py:128 MISSING d:/ymir work/pc/common/effect/armor/armor-4-2-2.mse':
        'costume set aura since 2.x: in the base pc packs (no listing); the 2.37 / 3.0.1 roots named it already',
    'uiingameevent.py:95 PATTERN-NO-MATCH d:/ymir work/ui/minimap/e_open_*.tga':
        'pack.Exist() first, FALLBACK_BUTTON otherwise',
}
fails, total = [], 0
inst = None
for name, pys in FEATURES:
    probs, inst, n = U.feature_problems(OUT, pys)
    total += n
    fails += ['%s: %s' % (name, p) for p in probs if p not in ACCEPTED]

# item_list rows new or changed since 3.0.1: their icons
prev = set()
try:
    pl = U.Layer(U.PREV_LAYER)
    ents = dict((e['name'].lower(), e) for e in U._index_from_bytes(pl.read('gamedata.index')))
    prev = set(U.m2pack.read_entry(pl.read('gamedata.data'), ents['gamedata/item_list.txt']).decode('latin1')
               .replace('\r', '').split('\n'))
except Exception as ex:
    fails.append('3.0.1 item_list not readable: %s' % ex)
rows = 0
for row in inst.read('gamedata/item_list.txt').decode('latin1').replace('\r', '').split('\n'):
    t = row.split('\t')
    if len(t) < 3 or not t[0].strip().isdigit() or row in prev:
        continue
    rows += 1
    icon = U.norm(t[2].strip())
    if icon not in inst.names:
        fails.append('item_list %s: icon %s in no pack' % (t[0].strip(), icon))

print('ui 3.0.4: %d feature(s), %d picture(s), %d new item_list row(s) checked on the players\' install, %d problem(s)'
      % (len(FEATURES), total, rows, len(fails)))
for f in fails:
    print('  ' + f)
sys.exit(1 if fails else 0)
