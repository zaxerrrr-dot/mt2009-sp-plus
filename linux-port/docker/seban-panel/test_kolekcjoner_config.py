"""MT2009_PLUS_KOLEKCJONER_CONFIG_V1: the rules of the collector's task editor (kolekcjoner_config.py) and that the panel's
reward names are the game's (playerbot_kolekcjoner_najemnikow.cpp s_aKnPoints)."""
import re
import unittest
from pathlib import Path

import kolekcjoner_config as kc

ROOT = Path(__file__).resolve().parents[2]
CPP = ROOT / "overlays/playerbot/src/game/src/playerbot_kolekcjoner_najemnikow.cpp"


class ValidationTests(unittest.TestCase):
    def test_task(self):
        t = kc.validate_task({"name": "Skrzynie bossow", "title": "Skrzynie bossów", "description": "  a   b ",
                              "percent": "95", "min_level": "", "sort_order": "10"})
        self.assertEqual((t["percent"], t["min_level"], t["sort_order"], t["description"]), (95, 0, 10, "a b"))
        for bad in ({"name": "", "percent": "95"}, {"name": "Zła", "percent": "95"}, {"name": "x", "percent": "0"},
                    {"name": "x", "percent": "101"}, {"name": "x", "percent": "abc"},
                    {"name": "x", "percent": "50", "min_level": "121"}, {"name": "x", "percent": "50", "title": "x" * 65},
                    {"name": "x", "percent": "50", "title": "日本"}):
            with self.assertRaises(ValueError):
                kc.validate_task(bad)

    def test_item(self):
        exists = {50255, 50271}.__contains__
        i = kc.validate_item({"vnum": "50255", "count": "100", "pack": "10"}, exists)
        self.assertEqual((i["vnum"], i["count"], i["pack"], i["unopened"]), (50255, 100, 10, 0))
        self.assertEqual(kc.validate_item({"vnum": "50271", "count": "10", "unopened": "1"}, exists)["unopened"], 1)
        for bad in ({"vnum": "1", "count": "1"}, {"vnum": "50255", "count": "0"}, {"vnum": "50255", "count": "5", "pack": "6"},
                    {"vnum": "50255", "count": "5", "pack": "0"}, {"vnum": "x", "count": "1"}):
            with self.assertRaises(ValueError):
                kc.validate_item(bad, exists)

    def test_reward(self):
        self.assertEqual(kc.validate_reward({"point": "max_hp", "value": "5000"}), {"point": "MAX_HP", "value": 5000})
        for bad in ({"point": "NOPE", "value": "1"}, {"point": "MAX_HP", "value": "0"}, {"point": "MAX_HP", "value": ""}):
            with self.assertRaises(ValueError):
                kc.validate_reward(bad)

    def test_tiers(self):
        self.assertEqual(kc.validate_tiers([("2", "3", "85"), ("1", "2", "80")]), [(1, 2, 80), (2, 3, 85)])
        for bad in ([(1, 3, 80), (2, 2, 85)], [(1, 2, 85), (2, 3, 80)], [(1, 8, 80)], [(1, 2, 80), (1, 3, 85)],
                    [(0, 2, 80)], [(1, 2, 121)]):
            with self.assertRaises(ValueError):
                kc.validate_tiers(bad)

    def test_slots(self):
        d = kc.DEFAULT_TIERS
        self.assertEqual(kc.slots_for_tiers(d, 0, 120), 0)
        self.assertEqual(kc.slots_for_tiers(d, 1, 79), 0)
        self.assertEqual(kc.slots_for_tiers(d, 1, 80), 2)
        self.assertEqual(kc.slots_for_tiers(d, 6, 82), 2)
        self.assertEqual(kc.slots_for_tiers(d, 3, 85), 3)
        self.assertEqual(kc.slots_for_tiers(d, 6, 105), 7)
        self.assertEqual(kc.slots_for_tiers([], 6, 105), 7)	# empty table: the built-in one
        self.assertEqual(kc.slots_for_tiers([(1, 4, 50)], 1, 50), 4)

    def test_swap(self):
        self.assertEqual(kc.swap_order([1, 2, 3], 2, -1), [2, 1, 3])
        self.assertEqual(kc.swap_order([1, 2, 3], 3, 1), [1, 2, 3])
        self.assertEqual(kc.swap_order([1, 2, 3], 9, 1), [1, 2, 3])

    def test_labels(self):
        self.assertEqual(kc.label("ATTBONUS_BOSS", 10), "Silny przeciwko bossom +10%")
        self.assertEqual(kc.label("MAX_HP", 5000), "Maks. PŻ +5000")
        for name, lab in kc.POINTS:
            lab % 1	# one %d each
            lab.encode("cp1250")


class GameAgreementTests(unittest.TestCase):
    @unittest.skipUnless(CPP.exists(), "the overlay is not in this checkout")
    def test_points_match_the_game(self):
        text = CPP.read_text(encoding="latin-1")
        table = text[text.index("s_aKnPoints[] ="):]
        table = table[:table.index("};")]
        game = set(re.findall(r'\{\s*"([A-Z_]+)"\s*,\s*POINT_', table))
        self.assertTrue(game)
        self.assertEqual(game, set(kc.POINT_NAMES))


if __name__ == "__main__":
    unittest.main()
