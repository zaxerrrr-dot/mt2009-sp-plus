# -*- coding: utf-8 -*-
"""MT2009_PLUS_SIDEBAR_CONFIG_V1 - the side bar's own arrangement per character (client-2.0.30/root/uisidebarconfig.py):
the default list, hiding and moving, the file per character, a button the file does not know yet, the defaults again.
MT2009_PLUS_SIDEBAR_WINDOWS_V1: the real catalogue (uiinventory.SidebarWindow.BUTTONS) has "Najemnicy", "Karty
Potworow" and "Relikty" with their icons and handlers, and a file saved with the older catalogue shows them.
Python 3 (and 2.7):

    python3 tests/uisidebarconfig_test.py
"""
import ast
import os
import re
import shutil
import struct
import sys
import tempfile
import types
import unittest

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'client-patches', 'client-2.0.30', 'root')

# uiinventory.SidebarWindow.BUTTONS before MT2009_PLUS_SIDEBAR_WINDOWS_V1 (the names; the file keeps only them)
OLD_NAMES = ['companion', 'autohunt', 'pickup', 'trash', 'battlepass', 'calendar', 'chestpreview', 'dungeon', 'teleport',
             'bonusswitch', 'missions', 'ranking', 'dropwiki', 'ekwipunek', 'pet', 'enasir']
NEW_BUTTONS = {
    'najemnicy': ('OnClickNajemnicy', None),
    'monstercard': ('OnClickMonsterCard', 'monster_card'),
    'relikt': ('OnClickRelic', 'relic'),
}


def real_source():
    with open(os.path.join(ROOT, 'uiinventory.py'), 'rb') as handle:
        return handle.read().decode('latin-1')     # CP1250 bytes, read as they are


def real_buttons():
    """SidebarWindow.BUTTONS of uiinventory.py, without importing the client's modules."""
    block = re.search(r'\n\tBUTTONS = \((.*?)\n\t\)\n', real_source(), re.S).group(1)
    return list(ast.literal_eval('(' + block + '\n)'))


CATALOGUE = [
    ('companion', 'Buffi', 'OnClickCompanion', 'companion'),
    ('autohunt', 'Autolowy', 'OnClickAutoHunt', 'autohunt'),
    ('missions', 'Usun misje', 'OnClickClearMissions', None),
    ('ekwipunek', 'Dodatkowy ekwipunek', 'OnClickExtraInventory', 'extra_inventory'),
]


def install(name):
    for n in ('player', 'ui', 'wndMgr'):
        sys.modules[n] = types.ModuleType(n)
    sys.modules['player'].GetName = lambda: name[0]
    ui = sys.modules['ui']
    for cls in ('Window', 'BoardWithTitleBar', 'Bar', 'ImageBox', 'ExpandedImageBox', 'TextLine', 'Button'):
        setattr(ui, cls, type(cls, (object,), {}))
    sys.modules.pop('uisidebarconfig', None)
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    import uisidebarconfig
    return uisidebarconfig


class SidebarConfigTest(unittest.TestCase):
    def setUp(self):
        self.cwd = os.getcwd()
        self.dir = tempfile.mkdtemp()
        os.chdir(self.dir)
        self.name = ['Wojownik']
        self.mod = install(self.name)

    def tearDown(self):
        os.chdir(self.cwd)
        shutil.rmtree(self.dir)

    def names(self, catalogue=CATALOGUE):
        return [entry[0] for entry in self.mod.Visible(catalogue)]

    def test_default_is_every_button(self):
        self.assertEqual(self.names(), ['companion', 'autohunt', 'missions', 'ekwipunek'])

    def test_hide_and_move_kept_for_the_character(self):
        self.mod.SetArrangement(['ekwipunek', 'companion', 'autohunt', 'missions'], ['missions'])
        self.assertEqual(self.names(), ['ekwipunek', 'companion', 'autohunt'])
        self.assertTrue(os.path.exists(os.path.join('autohunt', 'okna', 'pasek', 'Wojownik.cfg')))
        # read back from the file (a new client)
        self.mod = install(self.name)
        self.assertEqual(self.names(), ['ekwipunek', 'companion', 'autohunt'])
        # another character has its own (the default)
        self.name[0] = 'Ninja'
        self.assertEqual(self.names(), ['companion', 'autohunt', 'missions', 'ekwipunek'])

    def test_version_changes(self):
        v = self.mod.GetVersion()
        self.mod.SetArrangement(['companion', 'autohunt', 'missions', 'ekwipunek'], ['autohunt'])
        self.assertNotEqual(self.mod.GetVersion(), v)
        v = self.mod.GetVersion()
        self.name[0] = 'Ninja'
        self.assertNotEqual(self.mod.GetVersion(), v)

    def test_new_button_appears_at_its_place(self):
        self.mod.SetArrangement(['autohunt', 'companion', 'missions'], [])
        newer = CATALOGUE[:3] + [('pet', 'Zwierzak', 'OnClickPet', None)] + CATALOGUE[3:]
        self.assertEqual(self.names(newer), ['autohunt', 'companion', 'missions', 'pet', 'ekwipunek'])

    def test_unknown_name_dropped_and_defaults(self):
        self.mod.SetArrangement(['gone', 'missions', 'companion'], ['companion'])
        self.assertEqual(self.names(), ['missions', 'ekwipunek', 'autohunt'])  # each after its default predecessor
        self.mod.ResetArrangement()
        self.assertEqual(self.names(), ['companion', 'autohunt', 'missions', 'ekwipunek'])
        self.assertFalse(os.path.exists(os.path.join('autohunt', 'okna', 'pasek', 'Wojownik.cfg')))

    def test_no_character_yet(self):
        self.name[0] = ''
        self.assertEqual(self.names(), ['companion', 'autohunt', 'missions', 'ekwipunek'])
        self.mod.SetArrangement(['missions'], [])      # nothing to keep it for
        self.assertFalse(os.path.exists(os.path.join('autohunt', 'okna', 'pasek')))


    def test_real_catalogue_has_the_new_windows(self):
        buttons = real_buttons()
        names = [entry[0] for entry in buttons]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(names[-1], 'enasir')          # left out without remoteCall: stays the last
        self.assertEqual(sorted(set(names) - set(OLD_NAMES)), sorted(NEW_BUTTONS))
        self.assertEqual([n for n in names if n in OLD_NAMES], OLD_NAMES)
        self.assertEqual(names.index('monstercard'), names.index('dropwiki') + 1)
        self.assertEqual(names.index('relikt'), names.index('ekwipunek') + 1)
        self.assertEqual(names.index('najemnicy'), names.index('pet') + 1)
        source = real_source()
        side = os.path.join(ROOT, 'mt2009_ui', 'sidebar')
        for name, text, handler, action in buttons:
            if name in NEW_BUTTONS:
                self.assertEqual((handler, action), NEW_BUTTONS[name])
                self.assertIn('\tdef %s(self):' % handler, source)
                for frame in (1, 2, 3):
                    with open(os.path.join(side, '%s_%02d.tga' % (name, frame)), 'rb') as handle:
                        head = handle.read(18)
                    self.assertEqual(struct.unpack('<HH', head[12:16]), (32, 32))
        texts = dict((entry[0], entry[1]) for entry in buttons)
        self.assertEqual(texts['najemnicy'], 'Najemnicy')
        self.assertEqual(texts['monstercard'], 'Karty Potwor\xf3w')
        self.assertEqual(texts['relikt'], 'Relikty')

    def test_saved_older_file_gets_the_new_buttons(self):
        buttons = real_buttons()
        # a player's file of the older client: own order, "Usun misje" hidden
        order = ['dungeon', 'companion', 'autohunt'] + [n for n in OLD_NAMES if n not in ('dungeon', 'companion', 'autohunt')]
        self.mod.SetArrangement(order, ['missions'])
        self.mod = install(self.name)                   # the new client reads it
        shown = self.names(buttons)
        for name in NEW_BUTTONS:
            self.assertIn(name, shown)
        self.assertNotIn('missions', shown)
        self.assertEqual(shown[:3], ['dungeon', 'companion', 'autohunt'])
        self.assertEqual(shown.index('monstercard'), shown.index('dropwiki') + 1)
        self.assertEqual(shown.index('relikt'), shown.index('ekwipunek') + 1)
        self.assertEqual(shown.index('najemnicy'), shown.index('pet') + 1)
        self.assertEqual(shown[-1], 'enasir')
        # a new character: every button in the default order
        self.name[0] = 'Ninja'
        self.assertEqual(self.names(buttons), [entry[0] for entry in buttons])


if __name__ == '__main__':
    unittest.main()
