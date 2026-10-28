# -*- coding: utf-8 -*-
# MT2009_PLUS_CUBE_RENEWAL_V1 - the files of the global crafting window (root/uicuberenewal.py) in the "root" pack:
# the module, its uiscript and GF 26.1.11's graphics (d:/ymir work/ui/making_001.dds, d:/ymir work/ui/game/cube/*.sub
# plus our two crops mt2009_cube_slot_col.sub / mt2009_cube_slot_end.sub). The build of the root pack (build57.py)
# already takes them from client-2.0.30/root and client-2.0.30/atlas/d_; build_cube_packs.py makes sure of it and
# verify_cube_packs.py checks it. Shared by both.
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CLIENT = os.path.normpath(os.path.join(HERE, '..', '..'))
ROOT = os.path.join(CLIENT, 'root')
ATLAS = os.path.join(CLIENT, 'atlas')
CUBE_DIR = os.path.join(ATLAS, 'd_', 'ymir work', 'ui', 'game', 'cube')

# the 19 GF .sub files of d:/ymir work/ui/game/cube (GF 26.1.11, byte for byte) and our two crops of cube_slot_bg
GF_SUBS = ('cube_gem_icon', 'cube_improve_slot', 'cube_menu_tab1', 'cube_menu_tab1_minus', 'cube_menu_tab1_plus',
           'cube_menu_tab2', 'cube_menu_tab2_minus', 'cube_menu_tab2_plus', 'cube_menu_tab3_default',
           'cube_menu_tab3_select', 'cube_qty_add_default', 'cube_qty_add_down', 'cube_qty_add_over',
           'cube_qty_sub_default', 'cube_qty_sub_down', 'cube_qty_sub_over', 'cube_slot_bg', 'cube_yang_icon',
           'cube_yang_textbg')
OWN_SUBS = ('mt2009_cube_slot_col', 'mt2009_cube_slot_end')

# what the window needs that an earlier step ships (gemshop_001.dds: the Gaya shop, client-2.0.30/atlas)
NEEDED_ELSEWHERE = ('d:/ymir work/ui/gemshop_001.dds', 'uicube.py', 'uicraft.py')
# the hooks in the pack's interfacemodule.py (build57.py takes it from client-2.0.30/root)
INTERFACE_HOOKS = ('import uiCubeRenewal', 'uiCubeRenewal.CraftingRenewalWindow()', 'uiCubeRenewal.CubeRenewalWindow()')


def entries():
    """{pack entry name: (local file, entry type)} - .py and d:/ entries type 2, as build57.py writes them"""
    out = {
        'uicuberenewal.py': (os.path.join(ROOT, 'uicuberenewal.py'), 2),
        'uiscript/cuberenewalwindow.py': (os.path.join(ROOT, 'uiscript', 'cuberenewalwindow.py'), 2),
        'd:/ymir work/ui/making_001.dds': (os.path.join(ATLAS, 'd_', 'ymir work', 'ui', 'making_001.dds'), 2),
    }
    for name in GF_SUBS + OWN_SUBS:
        out['d:/ymir work/ui/game/cube/%s.sub' % name] = (os.path.join(CUBE_DIR, name + '.sub'), 2)
    return out


def read(path):
    with open(path, 'rb') as f:
        return f.read()
