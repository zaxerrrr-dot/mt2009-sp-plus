import datetime
import unittest

import ishop_rotation as rot

IDS = list(range(1, 46))


class ScheduleTests(unittest.TestCase):
    # MT2009_PLUS_ISHOP_ROTACJA_V1: the same days as the shop's PHP (Shop::rotationDay) gives for the default seed -
    # checked against it on 8 November 2026 (800 days x per_day 1, 2, 3, 7 identical); a change here must change both.
    def test_golden_days(self):
        s = rot.Schedule(IDS, 2, "mt2009plus")
        got = [s.day(datetime.date(2026, 11, 8) + datetime.timedelta(days=i)) for i in range(4)]
        self.assertEqual(got, [[15, 10], [43, 2], [17, 23], [20, 45]])

    def test_every_chest_once_a_cycle_no_repeat_two_days_running(self):
        for k in (1, 2, 3, 7, 10):
            s = rot.Schedule(IDS, k, "mt2009plus")
            last = {}
            for i in range(1200):
                ids = s.day(rot.EPOCH + datetime.timedelta(days=i))
                self.assertEqual(len(ids), k)
                self.assertEqual(len(set(ids)), k)
                for c in ids:
                    if c in last:
                        self.assertGreaterEqual(i - last[c], 2, (k, i, c))
                    last[c] = i
            for order in s.orders:
                self.assertEqual(sorted(order), IDS)

    def test_pins_first_then_rotation(self):
        s = rot.Schedule(IDS, 2, "mt2009plus")
        day = datetime.date(2026, 11, 20)
        self.assertEqual(s.day(day, [5, 7, 5]), [5, 7])
        plain = s.day(day)
        mixed = s.day(day, [44])
        self.assertEqual(mixed[0], 44)
        self.assertEqual(len(mixed), 2)
        self.assertEqual(s.day(day, [99]), plain)    # not a set chest - ignored

    def test_day_index_and_seed(self):
        self.assertEqual(rot.day_index(datetime.date(2026, 1, 1)), 0)
        self.assertEqual(rot.day_index(datetime.date(2025, 12, 31)), 0)
        a = rot.Schedule(IDS, 2, "a").day(datetime.date(2026, 11, 8))
        b = rot.Schedule(IDS, 2, "b").day(datetime.date(2026, 11, 8))
        self.assertNotEqual(a, b)


if __name__ == "__main__":
    unittest.main()
