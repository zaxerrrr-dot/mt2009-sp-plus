"""MT2009_PLUS_DB_EDITOR_ITEMSHOP_V1: python3 test_dbeditor_itemshop.py

The database editor's "ItemShop" (dbeditor/itemshop.py) through Flask's test
client, on an in-memory SQLite with the common / player / world schemas
attached (the MariaDB statements after a few mechanical rewrites; ENUM
currency kept as its number, DATETIMEs as text through UNIX_TIMESTAMP /
FROM_UNIXTIME stand-ins). apply.sh is read to check BOOT_ONCE against its
ishop_once blocks (and that nothing else writes common.itemshop_items at
every start), and the client's root/uiitemshop.py to check the tabs."""
import json
import os
import re
import sqlite3
import subprocess
import tempfile
import time
import unittest
from datetime import datetime
from unittest.mock import patch

os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("DB_HOST", "127.0.0.1")
os.environ.setdefault("DB_PORT", "1")
os.environ.setdefault("DBEDITOR_SPOOL_ROOT", tempfile.mkdtemp(prefix="dbe-spool-"))

import app as panel  # noqa: E402
from dbeditor import common_items, config, itemshop, reapply  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
APPLY = os.path.join(HERE, "..", "mariadb", "playerbot", "apply.sh")
CLIENT_UI = os.path.join(HERE, "..", "..", "..", "client-patches", "client-2.0.25", "root", "uiitemshop.py")

SCHEMA = """
CREATE TABLE world.item_proto (vnum INTEGER PRIMARY KEY, locale_name BLOB, type INTEGER, stack INTEGER);
CREATE TABLE common.itemshop_items (`index` INTEGER PRIMARY KEY, vnum INTEGER NOT NULL, `count` INTEGER NOT NULL,
    price INTEGER NOT NULL, currency INTEGER NOT NULL DEFAULT 1, minLevel INTEGER NOT NULL DEFAULT 0,
    socket0 INTEGER NOT NULL DEFAULT 0, socket1 INTEGER NOT NULL DEFAULT 0, socket2 INTEGER NOT NULL DEFAULT 0);
CREATE TABLE common.itemshop_promotions (item_index INTEGER PRIMARY KEY, price INTEGER NOT NULL,
    start_time TEXT NOT NULL, end_time TEXT NOT NULL);
CREATE TABLE common.itemshop_time_auctions (item_index INTEGER PRIMARY KEY, max_amount INTEGER NOT NULL DEFAULT 0,
    account_limit INTEGER NOT NULL DEFAULT 0, start_time TEXT NOT NULL, end_time TEXT NOT NULL);
CREATE TABLE player.itemshop_time_auction (item_index INTEGER PRIMARY KEY, buy_count INTEGER NOT NULL DEFAULT 0);
CREATE TABLE player.playerbot_migrations (name TEXT PRIMARY KEY, done_at TEXT);
CREATE TABLE player.web_dbeditor_history (id INTEGER PRIMARY KEY AUTOINCREMENT,
    changed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, who TEXT NOT NULL DEFAULT '', tbl TEXT NOT NULL,
    row_key TEXT NOT NULL, label TEXT NOT NULL DEFAULT '', col TEXT NOT NULL, old_value TEXT, new_value TEXT,
    batch TEXT NOT NULL, note TEXT NOT NULL DEFAULT '', reverted_in TEXT, applied_at TEXT);
"""


def unix_timestamp(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value)
    if text.isdigit():
        return int(text)
    return int(time.mktime(datetime.strptime(text[:19], "%Y-%m-%d %H:%M:%S").timetuple()))


def from_unixtime(value):
    return None if value is None else time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(value)))


class SqliteDB:
    def __init__(self):
        self.con = sqlite3.connect(":memory:", isolation_level=None, check_same_thread=False)
        self.con.row_factory = sqlite3.Row
        self.con.create_function("UNIX_TIMESTAMP", 1, unix_timestamp)
        self.con.create_function("FROM_UNIXTIME", 1, from_unixtime)
        for name in ("world", "common", "player"):
            self.con.execute(f"ATTACH DATABASE ':memory:' AS {name}")
        self.con.executescript(SCHEMA)

    @staticmethod
    def translate(sql):
        sql = " ".join(sql.split())
        sql = re.sub(r"CAST\((`?\w+`?) AS BINARY\)", r"\1", sql)
        sql = sql.replace(" FOR UPDATE", "").replace("NOW()", "CURRENT_TIMESTAMP")
        if sql.startswith("DELETE"):
            sql = sql.replace(" LIMIT 1", "")
        return sql.replace("%s", "?")

    def execute(self, sql, params=()):
        if sql.strip().startswith("CREATE TABLE IF NOT EXISTS player.web_dbeditor_history"):
            return [], 0
        cur = self.con.execute(self.translate(sql), list(params or ()))
        found = [dict(r) for r in cur.fetchall()] if cur.description else []
        return found, cur.rowcount

    def rows(self, sql, params=()):
        return self.execute(sql, params)[0]

    def one(self, sql, params=()):
        found = self.rows(sql, params)
        return found[0] if found else None

    def db(self):
        return Connection(self)

    def insert(self, table, **values):
        cols = ", ".join(f"`{c}`" for c in values)
        self.con.execute(f"INSERT INTO {table} ({cols}) VALUES ({', '.join('?' * len(values))})", list(values.values()))


class Cursor:
    def __init__(self, fake):
        self.fake, self.result, self.rowcount = fake, [], 0

    def execute(self, sql, params=()):
        self.result, self.rowcount = self.fake.execute(sql, params)

    def fetchone(self):
        return self.result[0] if self.result else None

    def fetchall(self):
        return self.result

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class Connection:
    def __init__(self, fake):
        self.fake = fake

    def begin(self):
        self.fake.con.execute("BEGIN")

    def commit(self):
        self.fake.con.execute("COMMIT")

    def rollback(self):
        if self.fake.con.in_transaction:
            self.fake.con.execute("ROLLBACK")

    def cursor(self):
        return Cursor(self.fake)

    def close(self):
        pass


def seed(fake):
    for vnum, text, stack in ((72322, "Karta Nowego Początku", 200), (72323, "Karta Nowego Układu", 200),
                              (71004, "Zwój Medytacji", 200), (41986, "Zbroja Króla Wojowników+", 1),
                              (27989, "Kamień Duchowy", 200), (70058, "Pierścień Anty-Exp", 1),
                              (71094, "Zwój Ochrony", 200)):
        fake.insert("world.item_proto", vnum=vnum, locale_name=text, type=3, stack=stack)
    line = lambda index, vnum, count=1, price=49, currency=1, level=0: fake.insert(
        "common.itemshop_items", index=index, vnum=vnum, count=count, price=price, currency=currency, minLevel=level)
    line(8, 70058, price=149, level=30)
    line(601, 71004, count=10)
    line(617, 72322)
    line(618, 72323)
    line(701, 71094, price=599, currency=2)
    line(906, 27989, price=99)
    line(20212, 41986, price=100)
    line(1000, 71004)  # outside every tab
    fake.insert("common.itemshop_promotions", item_index=601, price=29, start_time="2020-01-01 00:00:00",
                end_time="2030-01-01 00:00:00")
    fake.insert("common.itemshop_time_auctions", item_index=906, max_amount=5, account_limit=1,
                start_time="2026-10-01 00:00:00", end_time="2026-10-02 00:00:00")
    fake.insert("player.itemshop_time_auction", item_index=906, buy_count=3)
    fake.insert("player.playerbot_migrations", name="mod:10_ingame_itemshop.sql", done_at="2026-10-01")
    fake.insert("player.playerbot_migrations", name="ishop:monster_cards_617", done_at="2026-10-01")


class Base(unittest.TestCase):
    def setUp(self):
        self.fake = SqliteDB()
        seed(self.fake)
        common_items._STATE["table_ready"] = False
        self.queued = []
        self.queue_result = True
        common_items._CTX.update(rows=self.fake.rows, db=self.fake.db, queue_gm_command=self.queue)
        self.patches = [
            patch.object(panel, "settings", return_value={"setup_complete": "1", "auth_enabled": "0"}),
            patch.object(panel, "check_all_notifications", return_value=None, create=True),
            patch.object(panel, "rows", side_effect=self.panel_rows),
        ]
        for p in self.patches:
            p.start()
        panel.app.config["TESTING"] = True
        self.client = panel.app.test_client()
        with self.client.session_transaction() as sess:
            sess["seban_update_csrf"] = "tok"

    def tearDown(self):
        for p in self.patches:
            p.stop()

    def queue(self, cmd):
        self.queued.append(cmd)
        return self.queue_result

    def panel_rows(self, sql, params=()):
        if re.search(r"world\.|common\.itemshop|player\.(itemshop|playerbot_migrations|item_proto)|web_dbeditor_history", sql):
            return self.fake.rows(sql.replace("player.item_proto", "world.item_proto"), params)
        return []

    def post(self, url, data, **kw):
        data = dict(data)
        data.setdefault("dbe_csrf", "tok")
        return self.client.post(url, data=data, follow_redirects=True, **kw)

    def line(self, index):
        return self.fake.one("SELECT * FROM common.itemshop_items WHERE `index`=%s", (index,))

    def indexes(self):
        return [r["index"] for r in self.fake.rows("SELECT `index` FROM common.itemshop_items ORDER BY `index`")]

    def history(self):
        return self.fake.rows("SELECT * FROM player.web_dbeditor_history ORDER BY id")

    def tab_form(self, tab, **changes):
        lines = itemshop.load_lines(self.fake.rows)
        form = {"action": "save", "tab": tab, "line": []}
        for index, l in lines.items():
            if tab not in itemshop.line_tabs(l):
                continue
            form["line"].append(str(index))
            for col in ("vnum", "count", "price", "currency", "minLevel"):
                form[f"{col}_{index}"] = str(l[col])
        form.update(changes)
        return form


class ItemShopTests(Base):
    def test_hub_and_tabs(self):
        self.assertIn("ItemShop", self.client.get("/db/").get_data(as_text=True))
        page = self.client.get("/db/itemshop?tab=zwoje").get_data(as_text=True)
        self.assertIn("Karta Nowego Początku", page)
        self.assertIn("Zwój Medytacji", page)
        self.assertIn("promocja trwa", page)
        self.assertNotIn("Zbroja Króla", page)
        page = self.client.get("/db/itemshop?tab=znaki").get_data(as_text=True)
        self.assertIn("Zwój Ochrony", page)
        page = self.client.get("/db/itemshop?tab=niewidoczne").get_data(as_text=True)
        self.assertIn("niewidoczna w kliencie", page)
        page = self.client.get("/db/itemshop?q=Zbroja").get_data(as_text=True)
        self.assertIn("Zbroja Króla Wojowników+", page)
        self.assertIn("apply.sh", page)  # king03 not marked on this install yet
        self.assertEqual(self.client.get("/db/itemshop/4242").status_code, 404)
        self.assertIn("Oferta błyskawiczna", self.client.get("/db/itemshop/906").get_data(as_text=True))

    def test_rules(self):
        self.assertEqual(itemshop.index_tabs(617), ["zwoje"])
        self.assertEqual(itemshop.index_tabs(12000), ["fryzury"])
        self.assertEqual(itemshop.index_tabs(114), [])
        self.assertEqual(itemshop.line_tabs({"index": 701, "currency": 2}), ["znaki"])
        self.assertEqual(itemshop.free_index("zwoje", {601, 617, 618}), 602)
        self.assertEqual(itemshop.free_index("vip", set(range(101, 114))), None)

    def test_edit_fields_history_undo_and_reload(self):
        form = self.tab_form("zwoje", price_617="39", currency_617="2", minLevel_617="20", count_618="5")
        text = self.post("/db/itemshop", form).get_data(as_text=True)
        self.assertIn("Zapisano", text)
        self.assertEqual((self.line(617)["price"], self.line(617)["currency"], self.line(617)["minLevel"]), (39, 2, 20))
        self.assertEqual(self.line(618)["count"], 5)
        hist = self.history()
        self.assertEqual({h["col"] for h in hist}, {"price", "currency", "minLevel", "count"})
        self.assertEqual(len({h["batch"] for h in hist}), 1)
        # now in Smocze Znaki too
        self.assertIn("Karta Nowego Początku", self.client.get("/db/itemshop?tab=znaki").get_data(as_text=True))
        self.assertIn("Odśwież sklep w grze", self.client.get("/db/itemshop").get_data(as_text=True))
        res = self.post("/db/itemshop/odswiez", {})
        self.assertIn("Sklep odświeżony", res.get_data(as_text=True))
        self.assertEqual(self.queued, ["ISHOP_RELOAD"])
        self.assertEqual(common_items.pending_changes(), [])
        res = self.post("/db/historia/cofnij", {"batch": hist[0]["batch"]})
        self.assertIn("Cofnięto", res.get_data(as_text=True))
        self.assertEqual((self.line(617)["price"], self.line(617)["currency"]), (49, 1))

    def test_reload_without_an_implementor(self):
        self.queue_result = False
        self.post("/db/itemshop", self.tab_form("zwoje", price_617="39"))
        res = self.post("/db/itemshop/odswiez", {})
        self.assertIn("Żaden IMPLEMENTOR", res.get_data(as_text=True))
        self.assertEqual(len(common_items.pending_changes()), 1)

    def test_refused_values(self):
        for changes, expected in (({"price_617": "0"}, "dozwolone 1"), ({"vnum_617": "99999"}, "nie ma przedmiotu"),
                                  ({"minLevel_617": "300"}, "dozwolone 0"), ({"count_617": "40000"}, "dozwolone 1")):
            text = self.post("/db/itemshop", self.tab_form("zwoje", **changes)).get_data(as_text=True)
            self.assertIn(expected, text, changes)
        self.assertEqual(self.history(), [])

    def test_add_with_auto_index_and_checks(self):
        base = {"action": "add", "tab": "zwoje", "new_tab": "zwoje", "new_vnum": "71094", "new_count": "1",
                "new_price": "19", "new_currency": "1", "new_minLevel": "0"}
        text = self.post("/db/itemshop", base).get_data(as_text=True)
        self.assertIn("poz. 602", text)
        self.assertEqual(self.line(602)["vnum"], 71094)
        self.assertEqual(self.history()[0]["col"], "*")
        text = self.post("/db/itemshop", dict(base, new_index="250")).get_data(as_text=True)
        self.assertIn("nie leży w zakładce", text)
        text = self.post("/db/itemshop", dict(base, new_index="617")).get_data(as_text=True)
        self.assertIn("jest już zajęty", text)
        text = self.post("/db/itemshop", dict(base, new_vnum="99999")).get_data(as_text=True)
        self.assertIn("nie ma przedmiotu", text)
        # Smocze Znaki: always SZ, index from 700
        self.post("/db/itemshop", dict(base, new_tab="znaki"))
        self.assertEqual((self.line(700)["vnum"], self.line(700)["currency"]), (71094, 2))
        # VIP: the client's fixed 101-113
        self.post("/db/itemshop", dict(base, new_tab="vip"))
        self.assertEqual(self.line(101)["vnum"], 71094)
        self.post("/db/itemshop", dict(base, new_tab="vip"))
        self.assertIn(102, self.indexes())

    def test_delete_takes_promotion_and_offer_and_undo_brings_them_back(self):
        self.post("/db/itemshop", self.tab_form("zwoje", del_601="1"))
        self.assertIsNone(self.line(601))
        self.assertIsNone(self.fake.one("SELECT * FROM common.itemshop_promotions WHERE item_index=601"))
        self.post("/db/itemshop", self.tab_form("blyskawiczne", del_906="1"))
        self.assertIsNone(self.fake.one("SELECT * FROM common.itemshop_time_auctions WHERE item_index=906"))
        self.assertIsNone(self.fake.one("SELECT * FROM player.itemshop_time_auction WHERE item_index=906"))
        batches = [b["batch"] for b in common_items.history_batches(10)]
        for batch in batches:
            res = self.post("/db/historia/cofnij", {"batch": batch})
            self.assertIn("Cofnięto", res.get_data(as_text=True))
        self.assertEqual(self.line(601)["count"], 10)
        promo = self.fake.one("SELECT * FROM common.itemshop_promotions WHERE item_index=601")
        self.assertEqual((promo["price"], promo["end_time"]), (29, "2030-01-01 00:00:00"))
        self.assertEqual(self.fake.one("SELECT max_amount FROM common.itemshop_time_auctions WHERE item_index=906")
                         ["max_amount"], 5)
        self.assertIsNotNone(self.fake.one("SELECT * FROM player.itemshop_time_auction WHERE item_index=906"))

    def test_removing_a_boot_line_warns_until_marked(self):
        text = self.post("/db/itemshop", self.tab_form("kostiumy", del_20212="1")).get_data(as_text=True)
        self.assertIn("doda ją jeszcze raz", text)
        text = self.post("/db/itemshop", self.tab_form("zwoje", del_617="1")).get_data(as_text=True)
        self.assertNotIn("doda ją jeszcze raz", text)  # monster_cards_617 already written on this install

    def test_promotion_and_flash_offer(self):
        res = self.post("/db/itemshop/617", {"action": "promo", "promo_price": "29", "promo_start": "2026-10-06T10:00",
                                             "promo_end": "2026-10-13T10:00"})
        self.assertIn("Zapisano promocję", res.get_data(as_text=True))
        promo = self.fake.one("SELECT * FROM common.itemshop_promotions WHERE item_index=617")
        self.assertEqual((promo["price"], promo["start_time"]), (29, "2026-10-06 10:00:00"))
        res = self.post("/db/itemshop/617", {"action": "promo", "promo_price": "60", "promo_start": "2026-10-06T10:00",
                                             "promo_end": "2026-10-13T10:00"})
        self.assertIn("niższa niż zwykła", res.get_data(as_text=True))
        res = self.post("/db/itemshop/617", {"action": "promo", "promo_price": "20", "promo_start": "2026-10-13T10:00",
                                             "promo_end": "2026-10-06T10:00"})
        self.assertIn("po jej początku", res.get_data(as_text=True))
        # a flash offer writes the core's counter row too
        res = self.post("/db/itemshop/618", {"action": "auction", "max_amount": "10", "account_limit": "2",
                                             "auction_start": "2026-10-06T10:00", "auction_end": "2026-10-07T10:00"})
        self.assertIn("Zapisano ofertę", res.get_data(as_text=True))
        self.assertEqual(self.fake.one("SELECT buy_count FROM player.itemshop_time_auction WHERE item_index=618")
                         ["buy_count"], 0)
        # changing it keeps the sales count
        self.fake.rows("UPDATE player.itemshop_time_auction SET buy_count=4 WHERE item_index=618")
        self.post("/db/itemshop/618", {"action": "auction", "max_amount": "20", "account_limit": "2",
                                       "auction_start": "2026-10-06T10:00", "auction_end": "2026-10-07T10:00"})
        self.assertEqual(self.fake.one("SELECT buy_count FROM player.itemshop_time_auction WHERE item_index=618")
                         ["buy_count"], 4)
        self.post("/db/itemshop/618", {"action": "auction_del"})
        self.assertIsNone(self.fake.one("SELECT * FROM common.itemshop_time_auctions WHERE item_index=618"))
        self.assertIsNone(self.fake.one("SELECT * FROM player.itemshop_time_auction WHERE item_index=618"))
        self.post("/db/itemshop/617", {"action": "promo_del"})
        self.assertIsNone(self.fake.one("SELECT * FROM common.itemshop_promotions WHERE item_index=617"))

    def test_move_to_another_tab(self):
        res = self.post("/db/itemshop/601", {"action": "move", "move_tab": "wyposazenie"})
        self.assertIn("Przeniesiono", res.get_data(as_text=True))
        self.assertIsNone(self.line(601))
        self.assertEqual(self.line(1)["vnum"], 71004)
        self.assertEqual(self.fake.one("SELECT price FROM common.itemshop_promotions WHERE item_index=1")["price"], 29)
        res = self.post("/db/itemshop/906", {"action": "move", "move_tab": "blyskawiczne", "move_index": "950"})
        self.assertEqual(self.line(950)["vnum"], 27989)
        self.assertIsNotNone(self.fake.one("SELECT * FROM player.itemshop_time_auction WHERE item_index=950"))
        res = self.post("/db/itemshop/617", {"action": "move", "move_tab": "zwoje", "move_index": "618"})
        self.assertIn("zajęty", res.get_data(as_text=True))

    def test_replay_and_config_export(self):
        self.post("/db/itemshop", self.tab_form("zwoje", price_617="39", currency_617="2"))
        self.post("/db/itemshop/618", {"action": "auction", "max_amount": "10", "account_limit": "0",
                                       "auction_start": "2026-10-06T10:00", "auction_end": "2026-10-07T10:00"})
        content = config.collect(parts=["ishop", "ishop_auction", "ishop_counter"])
        self.assertTrue(any(r["col"] == "currency" and r["new"] == 2 for r in content["ishop"]["records"]))
        self.assertEqual(content["ishop_auction"]["records"][0]["new"]["max_amount"], 10)
        self.assertEqual(content["ishop_counter"]["records"][0]["new"], {"item_index": 618})
        statements, skipped = reapply.replay_statements()
        self.assertEqual(skipped, [])
        text = "\n".join(statements)
        self.assertIn("UPDATE common.itemshop_items SET `currency`=2 WHERE `index`=617;", text)
        self.assertRegex(text, r"INSERT INTO common.itemshop_time_auctions \(.*\) VALUES \(618, 10, 0, FROM_UNIXTIME\(\d+\), FROM_UNIXTIME\(\d+\)\);")
        self.assertIn("INSERT INTO player.itemshop_time_auction (`item_index`) VALUES (618);", text)
        # the replay runs against a reset copy (here: this database after the undo of everything)
        for batch in [b["batch"] for b in common_items.history_batches(10)]:
            self.post("/db/historia/cofnij", {"batch": batch, "force": "1"})
        for statement in statements:
            self.fake.rows(statement)
        self.assertEqual((self.line(617)["price"], self.line(617)["currency"]), (39, 2))
        self.assertEqual(self.fake.one("SELECT start_time FROM common.itemshop_time_auctions WHERE item_index=618")
                         ["start_time"], "2026-10-06 10:00:00")


class BootAndClientTests(unittest.TestCase):
    def apply_text(self):
        with open(APPLY, encoding="utf-8") as handle:
            return handle.read()

    def test_boot_once_matches_apply_sh(self):
        text = self.apply_text()
        blocks = dict(re.findall(r'^ishop_once ([a-z0-9_]+) "(.*?)"\s*\\?\s*"', text, re.S | re.M))
        self.assertEqual(set(blocks), set(itemshop.BOOT_ONCE))
        for name, sql in blocks.items():
            adds = {int(i) for i in re.findall(r"\((\d+), \d+, \d+, \d+, 'DRAGON_\w+', \d+\)", sql)}
            adds |= {int(i) for i in re.findall(r"SELECT (\d+), \d+, \d+, \d+, 'DRAGON_\w+'", sql)}
            self.assertEqual(adds, set(itemshop.BOOT_ONCE[name]["adds"]), name)
            removes = re.search(r"DELETE FROM common.itemshop_items WHERE vnum IN \(([\d, ]+)\)", sql)
            self.assertEqual({int(v) for v in removes.group(1).split(",")} if removes else set(),
                             set(itemshop.BOOT_ONCE[name].get("remove_vnums", ())), name)
            pairs = re.search(r"DELETE FROM common.itemshop_items WHERE \(\\`index\\`, vnum\) IN \((.*?)\);", sql)
            self.assertEqual({int(i) for i in re.findall(r"\((\d+), \d+\)", pairs.group(1))} if pairs else set(),
                             set(itemshop.BOOT_ONCE[name].get("remove_indexes", ())), name)
        # nothing else writes the shop's lines at every start
        outside = re.sub(r'^ishop_once [a-z0-9_]+ ".*?"\s*\\?\s*"[^"\n]*"', "", text, flags=re.S | re.M)
        self.assertNotRegex(outside, r"(INSERT|UPDATE|DELETE)[^;\n]*common\.itemshop_items")

    def test_ishop_once_marks_only_after_the_seed(self):
        text = self.apply_text()
        function = re.search(r"\nishop_once\(\) \{\n.*?\n\}\n", text, re.S).group(0)
        script = """
fail_step() { echo "FAIL $*"; }
db() {
    case "$2" in
        *"name = 'mod:10_ingame_itemshop.sql'"*) echo "$SEED" ;;
        *"name = 'ishop:"*) grep -qx "$(echo "$2" | sed "s/.*name = '\\(ishop:[a-z_0-9]*\\)'.*/\\1/")" "$MARKS" && echo 1 || echo 0 ;;
        *"INSERT IGNORE INTO player.playerbot_migrations"*) echo "$2" | sed "s/.*VALUES ('\\(ishop:[a-z_0-9]*\\)'.*/\\1/" >> "$MARKS" ;;
        *) echo "RAN $2" ;;
    esac
}
""" + function + """
ishop_once test_a "SQL-A" "a failed"
ishop_once test_a "SQL-A" "a failed"
"""
        with tempfile.NamedTemporaryFile("w", delete=False) as marks:
            pass
        try:
            out = subprocess.run(["sh", "-c", script], env={"SEED": "0", "MARKS": marks.name, "PATH": os.environ["PATH"]},
                                 capture_output=True, text=True).stdout
            self.assertEqual(out.count("RAN SQL-A"), 2)  # no seed yet: every run, never marked
            self.assertEqual(open(marks.name).read(), "")
            out = subprocess.run(["sh", "-c", script], env={"SEED": "1", "MARKS": marks.name, "PATH": os.environ["PATH"]},
                                 capture_output=True, text=True).stdout
            self.assertEqual(out.count("RAN SQL-A"), 1)  # once, then marked
            self.assertEqual(open(marks.name).read().split(), ["ishop:test_a"])
        finally:
            os.unlink(marks.name)

    @unittest.skipUnless(os.path.exists(CLIENT_UI), "client-patches not in this tree")
    def test_tabs_match_the_client(self):
        with open(CLIENT_UI, encoding="utf-8", errors="replace") as handle:
            ui = handle.read()
        ui = "\n".join(l for l in ui.splitlines() if not l.lstrip().startswith("#"))
        client = set()
        for value in re.findall(r'"range"\s*:\s*"(\d+-\d+)"', ui) + \
                [v for group in re.findall(r'"ranges"\s*:\s*\[([^\]]*)\]', ui) for v in re.findall(r'"(\d+-\d+)"', group)]:
            lo, hi = value.split("-")
            client.add((int(lo), int(hi)))
        ours = {r for t in itemshop.TABS if t[0] != "vip" for r in t[2]}
        self.assertEqual(ours, client)
        vip = re.search(r'ITEMSHOP_CATEGORY_VIP,\s*"action"\s*:\s*\{[^}]*"items"\s*:\s*\[([^\]]*)\]', ui)
        self.assertEqual({int(v) for v in vip.group(1).split(",")} - {999}, set(range(101, 114)))
        custom = ui[ui.index("ITEMSHOP_CUSTOM_ITEM_DATA = {"):ui.index("ITEMSHOP_BASE_DATA")]
        self.assertEqual({int(k) for k in re.findall(r"^\s*(\d+)\s*:", custom, re.M)}, set(itemshop.CLIENT_NAME_SUFFIX))

    def test_quest_has_the_reload(self):
        for path in (os.path.join(HERE, "..", "game", "quest", "web_admin.quest"), os.path.join(HERE, "web_admin.quest")):
            if os.path.exists(path):
                text = open(path, encoding="utf-8", errors="replace").read()
                self.assertIn('cmd == "ISHOP_RELOAD"', text, path)
                self.assertIn('command("reload i")', text, path)
        self.assertLessEqual(len("ISHOP_RELOAD"), 16)  # the old panel's web_admin_queue.cmd VARCHAR(16)


if __name__ == "__main__":
    unittest.main()
