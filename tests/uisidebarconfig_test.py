# -*- coding: utf-8 -*-
"""MT2009_PLUS_SIDEBAR_CONFIG_V1 - the side bar's own arrangement per character (client-2.0.30/root/uisidebarconfig.py):
the default list, hiding and moving, the file per character, a button the file does not know yet, the defaults again.
Python 3 (and 2.7):

    python3 tests/uisidebarconfig_test.py
"""
import os
import shutil
import sys
import tempfile
import types
import unittest

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'client-patches', 'client-2.0.30', 'root')

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


if __name__ == '__main__':
    unittest.main()
