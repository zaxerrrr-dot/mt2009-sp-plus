"""MT2009_PLUS_POTEGA_MADROSCI_V1: the rules of "Potęga mądrości" (potega_madrosci.py) and that the quest, the SQL,
the core and the panels agree on the names."""
import re
import time
import unittest
from pathlib import Path

import potega_madrosci as pm

ROOT = Path(__file__).resolve().parents[2]


def wiki():
    return [{"id": i + 1, "enabled": 1, "champion": c, "lvl_from": f, "lvl_to": t, "pct": p}
            for i, (c, f, t, p) in enumerate(pm.WIKI_TIERS)]


class RuleTests(unittest.TestCase):
    def test_wiki_table(self):
        tiers = wiki()
        self.assertEqual(pm.pct_for(tiers, 40), 0)
        self.assertEqual(pm.pct_for(tiers, 41), 25)
        self.assertEqual(pm.pct_for(tiers, 80), 25)
        self.assertEqual(pm.pct_for(tiers, 81), 50)
        self.assertEqual(pm.pct_for(tiers, 101), 100)
        self.assertEqual(pm.pct_for(tiers, 120), 100)
        self.assertEqual(pm.pct_for(tiers, 120, 1), 125)
        self.assertEqual(pm.pct_for(tiers, 120, 10), 125)
        self.assertEqual(pm.pct_for(tiers, 120, 11), 100)
        self.assertEqual(pm.pct_for(tiers, 120, 30), 100)
        # A Champion past the last range gets nothing - not the level range's 100%.
        self.assertEqual(pm.pct_for(tiers, 120, 31), 0)

    def test_disabled_and_order(self):
        tiers = wiki()
        tiers[0]["enabled"] = 0
        self.assertEqual(pm.pct_for(tiers, 50), 0)
        tiers.append({"id": 9, "enabled": 1, "champion": 0, "lvl_from": 30, "lvl_to": 60, "pct": 10})
        self.assertEqual(pm.pct_for(tiers, 50), 10)
        tiers[0]["enabled"] = 1
        # The lower "from" wins an overlap, as the quest and the core read them.
        self.assertEqual(pm.pct_for(tiers, 50), 10)
        self.assertEqual(len(pm.overlaps(tiers)), 1)
        self.assertEqual(pm.overlaps(wiki()), [])

    def test_form(self):
        t = pm.tier_from_form({"champion": "1", "lvl_from": "1", "lvl_to": "10", "pct": "125", "enabled": "1"})
        self.assertEqual((t["champion"], t["lvl_from"], t["lvl_to"], t["pct"], t["enabled"]), (1, 1, 10, 125, 1))
        for bad in ({"lvl_from": "50", "lvl_to": "40", "pct": "10"}, {"lvl_from": "0", "lvl_to": "40", "pct": "10"},
                    {"lvl_from": "1", "lvl_to": "40", "pct": "0"}, {"lvl_from": "x", "lvl_to": "40", "pct": "1"},
                    {"lvl_from": "1", "lvl_to": "251", "pct": "1"}):
            with self.assertRaises(ValueError):
                pm.tier_from_form(bad)
        c = pm.config_from_form({"minutes": "240", "bots": "1", "bot_share": "60"})
        self.assertEqual(c, {"minutes": 240, "bots": 1, "bot_share": 60})
        with self.assertRaises(ValueError):
            pm.config_from_form({"minutes": "0", "bot_share": "60"})

    def test_texts(self):
        self.assertEqual(pm.minutes_text(240), "4 godz.")
        self.assertEqual(pm.minutes_text(90), "1 godz. 30 min")
        self.assertEqual(pm.minutes_text(45), "45 min")
        self.assertIsNone(pm.now_line({"potega": {"until": 1}}))
        self.assertIsNotNone(pm.now_line({"potega": {"until": int(time.time()) + 60}}))


class AgreementTests(unittest.TestCase):
    def read(self, rel, enc="utf-8"):
        return (ROOT / rel).read_text(encoding=enc, errors="replace")

    def test_sql_seed_is_the_wiki(self):
        sql = self.read("docker/mariadb/playerbot/potega_madrosci.sql")
        seeded = re.findall(r"SELECT (\d) ?(?:AS c)?, (\d+)(?: AS f)?, (\d+)(?: AS t)?, (\d+)", sql)
        self.assertEqual([tuple(int(x) for x in s) for s in seeded], list(pm.WIKI_TIERS))
        for statement in pm.DDL:
            self.assertTrue(statement.split("(")[0].split()[-1] in sql or "INSERT" in statement)

    def test_names_agree(self):
        quest = self.read("docker/game/quest/potega_madrosci.quest", "cp1250")
        core = self.read("overlays/playerbot/src/game/src/playerbot_potega.h")
        rules = self.read("overlays/playerbot/src/game/src/playerbot_event_rules.h")
        ingame = self.read("overlays/playerbot/src/game/src/playerbot_ingame_events.h")
        app = self.read("docker/seban-panel/app.py")
        self.assertIn('game.get_event_flag("potega_madrosci")', quest)
        self.assertIn('"potega_madrosci"', core)
        self.assertIn('"potega_madrosci"', ingame)
        self.assertIn('case KIND_POTEGA: return "potega";', rules)
        self.assertIn('"potega")  # MT2009_PLUS_POTEGA_MADROSCI_V1', app)
        # The affect and the point: quest and core give the same one.
        self.assertIn("affect.add_new(730, 127,", quest)
        self.assertIn("AFFECT_POTEGA_MADROSCI = 730", core)
        self.assertIn("POINT_RAMADAN_CANDY_BONUS_EXP", core)
        # The wiki's fallback in the quest and in the core.
        for c, f, t, p in pm.WIKI_TIERS:
            self.assertIn(f"champion = {c}, from = {f}, to = {t}, pct = {p}", quest)
            self.assertIn(f"{{ {c}, {f}, {t}, {p} }}", core)

    def test_quest_strings_qc_safe(self):
        raw = (ROOT / "docker/game/quest/potega_madrosci.quest").read_bytes()
        for literal in re.findall(rb'"([^"\n]*)"', raw):
            self.assertFalse(literal and literal[-1] >= 0x80, literal)
        for word in (b"Metin2", b"Gameforge", b"oficjaln"):
            self.assertNotIn(word, raw)


if __name__ == "__main__":
    unittest.main()
