import datetime
import re
import unittest
from pathlib import Path
from unittest.mock import MagicMock

import sm_grants as smg


def tier(id, target="player", period="day", level=20, champion=0, amount=50, active=0, name=None):
    return {"id": id, "target": target, "period": period, "min_level": level, "min_champion_level": champion,
            "amount": amount, "active_days": active, "enabled": 1, "name": name or f"T{id}"}


class PeriodTests(unittest.TestCase):
    def test_keys(self):
        now = datetime.datetime(2026, 10, 28, 23, 59)
        self.assertEqual(smg.period_key("day", now), "2026-10-28")
        self.assertEqual(smg.period_key("week", now), "2026-W44")
        self.assertEqual(smg.period_key("month", now), "2026-10")
        # ISO week of 1 January 2027 belongs to 2026.
        self.assertEqual(smg.period_key("week", datetime.datetime(2027, 1, 1)), "2026-W53")

    def test_next_start(self):
        now = datetime.datetime(2026, 12, 31, 10, 0)   # a Thursday
        self.assertEqual(smg.next_period_start("day", now), datetime.datetime(2027, 1, 1))
        self.assertEqual(smg.next_period_start("week", now), datetime.datetime(2027, 1, 4))
        self.assertEqual(smg.next_period_start("month", now), datetime.datetime(2027, 1, 1))


class AssignTests(unittest.TestCase):
    def test_best_tier_per_period(self):
        tiers = [tier(1, level=20, amount=50), tier(2, level=120, champion=1, amount=150),
                 tier(3, period="month", level=20, amount=500)]
        best = smg.assign(tiers, {1: [10, 11], 2: [11], 3: [10, 11]})
        self.assertEqual(best[("day", 10)]["id"], 1)
        self.assertEqual(best[("day", 11)]["id"], 2)      # the Champion tier beats the level-20 one
        self.assertNotIn(("month", 11), best)             # one best tier over all intervals
        self.assertNotIn(("month", 10), best)             # 50 a day beats 500 a month

    def test_level_then_amount(self):
        tiers = [tier(1, level=50, amount=10), tier(2, level=75, amount=5), tier(3, level=75, amount=8)]
        self.assertEqual(smg.assign(tiers, {1: [1], 2: [1], 3: [1]})[("day", 1)]["id"], 3)


class SqlTests(unittest.TestCase):
    def test_player_tier(self):
        sql, params = smg.qualifying_sql(tier(1, level=20))
        self.assertIn("NOT " + smg.BOT_ACCOUNT, sql)
        self.assertIn("a.status = 'OK'", sql)
        self.assertNotIn("conqueror_level >=", sql)
        self.assertIn("a.last_play >=", sql)
        self.assertEqual(params, [20, 1])                # a daily tier: played within the last day

    def test_bot_champion_active(self):
        sql, params = smg.qualifying_sql(tier(1, target="bot", level=120, champion=3, active=7))
        self.assertIn(smg.BOT_ACCOUNT, sql)
        self.assertNotIn("NOT " + smg.BOT_ACCOUNT, sql)
        self.assertNotIn("status", sql)
        self.assertIn("p.conqueror_level >= %s", sql)
        self.assertEqual(params, [120, 3, 7])
        self.assertEqual(sql.count("%s"), len(params))

    def test_sql_file_matches_ddl(self):
        sql = (Path(__file__).resolve().parent.parent / "mariadb/playerbot/sm_grants.sql").read_text()
        norm = lambda text: re.sub(r"\s+", " ", text).strip()
        body = norm(re.sub(r"--[^\n]*", "", sql))
        for statement in smg.DDL:
            self.assertIn(norm(statement), body)


class PayTests(unittest.TestCase):
    def items(self, *ids):
        t = tier(7, amount=40)
        return [{"account_id": i, "tier": t, "period": "day", "period_key": "2026-10-28", "detail": {}} for i in ids]

    def test_paid_once(self):
        con = MagicMock()
        cur = con.cursor.return_value.__enter__.return_value
        counts = iter([1, 1, 0])   # insert ok, update ok, insert ignored (already paid)
        type(cur).rowcount = property(lambda self: next(counts))
        cur.lastrowid = 5
        done, skipped = smg.pay(con, self.items(1, 2))
        self.assertEqual([d["account_id"] for d in done], [1])
        self.assertEqual(skipped, 1)
        sqls = [c.args[0] for c in cur.execute.call_args_list]
        self.assertEqual(sum("UPDATE account.account SET cash" in s for s in sqls), 1)
        con.commit.assert_called_once()

    def test_gone_account_undoes_log(self):
        con = MagicMock()
        cur = con.cursor.return_value.__enter__.return_value
        counts = iter([1, 0])
        type(cur).rowcount = property(lambda self: next(counts))
        cur.lastrowid = 9
        done, skipped = smg.pay(con, self.items(3))
        self.assertEqual((done, skipped), ([], 1))
        self.assertTrue(any("DELETE FROM account.sm_grant_log" in c.args[0] for c in cur.execute.call_args_list))

    def test_disabled_run_pays_nothing(self):
        con = MagicMock()
        cur = con.cursor.return_value.__enter__.return_value
        cur.fetchone.return_value = {"enabled": 0, "per_run_limit": 500}
        result = smg.run(con)
        self.assertTrue(result["disabled"])
        self.assertFalse(any("cash" in c.args[0] for c in cur.execute.call_args_list))


class FormTests(unittest.TestCase):
    def number(self, raw, label, maximum):
        value = int(raw)
        if not 0 <= value <= maximum:
            raise ValueError(label)
        return value

    def test_valid(self):
        t = smg.tier_from_form({"target": "bot", "period": "week", "name": " Boty 50+ ", "enabled": "1",
                                "min_level": "50", "min_champion_level": "", "amount": "100"}, self.number)
        self.assertEqual((t["target"], t["period"], t["name"], t["min_champion_level"], t["enabled"]),
                         ("bot", "week", "Boty 50+", 0, 1))

    def test_invalid(self):
        for form in ({"target": "x", "period": "day", "name": "a", "min_level": "1", "amount": "1"},
                     {"target": "bot", "period": "year", "name": "a", "min_level": "1", "amount": "1"},
                     {"target": "bot", "period": "day", "name": "", "min_level": "1", "amount": "1"},
                     {"target": "bot", "period": "day", "name": "a", "min_level": "1", "amount": "0"}):
            with self.assertRaises(ValueError):
                smg.tier_from_form(form, self.number)


if __name__ == "__main__":
    unittest.main()
