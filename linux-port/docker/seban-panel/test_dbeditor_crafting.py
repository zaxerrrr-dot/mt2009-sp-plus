"""MT2009_PLUS_DB_EDITOR_CRAFTING_V1: python3 test_dbeditor_crafting.py

The database editor's "Wytwarzanie przedmiotów" part (dbeditor/crafting.py):
the image's window lists (crafting_data.lua), the client's categories, the
recipes (world.crafting_proto) and the panel's list changes
(world.crafting_window) through Flask's test client on an in-memory SQLite
(SqliteDB of test_dbeditor_tables: the very statements of common_items run),
the history's undo, the config export / import, the world reset's replay and
the game side (bin/m2-crafting) with a stand-in mariadb client."""
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from flask import Blueprint, Flask
from jinja2 import ChoiceLoader, DictLoader, FileSystemLoader

import dbeditor
from dbeditor import common_items, config, crafting, reapply
from test_dbeditor_tables import SqliteDB

HERE = Path(__file__).resolve().parent
M2_CRAFTING = HERE.parent / "game" / "bin" / "m2-crafting"
SNAPSHOT = crafting.SNAPSHOT.read_bytes().decode("latin-1")
MYSHOP = crafting.ANTIFLAG_MYSHOP

ITEMS = [  # vnum, name, type, subtype, antiflag, value1
    (25040, "Zwój Błogosławieństwa", 3, 2, 0, 0), (25041, "Zwój Smoka", 3, 2, 0, 0),
    (70035, "Magiczna Miedź", 5, 0, 0, 0), (71026, "Kamień", 5, 0, 0, 0), (71025, "Podręcznik", 5, 0, 0, 0),
    (25044, "Zwój Wojny", 3, 2, 0, 0), (25045, "Zwój Boga Smoków", 3, 2, 0, 0), (25043, "Podręcznik Kowala", 3, 2, 0, 0),
    (71021, "Zwój Wojny", 3, 2, 106880, 0), (71032, "Zwój Boga Smoków", 3, 2, MYSHOP, 0),
    (70039, "Podręcznik Kowala", 3, 2, MYSHOP, 0),
    (30370, "Księga", 5, 0, 0, 0), (30364, "Zaczarowany Klejnot", 5, 0, 0, 0), (30366, "Pył", 5, 0, 0, 0),
    (30368, "Esencja", 5, 0, 0, 0), (30360, "Kamień Duszy", 5, 0, 0, 0),
    (71284, "Zaczarowanie Przedmiotu", 3, 18, 0, 0), (71285, "Wzmocnienie Przedmiotu", 3, 18, 0, 0),
    (70124, "Marmur Błogosławieństwa", 3, 18, 0, 0),
    (27103, "Fioletowa Mikstura(M)", 36, 0, 0, 1), (50901, "Woda", 5, 0, 0, 0), (50721, "Zioło", 5, 0, 0, 0),
    (11290, "Zbroja Z Czarnej Stali+0", 2, 0, 56, 90), (30372, "Czarna Stal", 5, 0, 0, 0), (30371, "Węgiel", 5, 0, 0, 0),
]
RECIPES = [  # vnum, item_vnum, count, price, chance, recipe, req_progress, req_level, recipe_vnum
    (1, 25044, 1, 400000, 100, "25040,1,70035,1", 0, 0, 0), (2, 25045, 1, 100000, 100, "25040,1,71026,1", 0, 0, 0),
    (3, 25043, 1, 200000, 100, "25040,1,71025,1", 0, 0, 0), (4, 71021, 1, 400000, 100, "25041,1,70035,1", 0, 0, 0),
    (5, 71032, 1, 100000, 100, "25041,1,71026,1", 0, 0, 0), (6, 70039, 1, 200000, 100, "25041,1,71025,1", 0, 0, 0),
    (11, 27103, 5, 12500, 100, "50901,5,50721,10", 1, 15, 11),
    (100, 71284, 1, 100000, 100, "30370,1,30364,1,30366,1", 0, 0, 0),
    (101, 71285, 1, 1500000, 100, "30368,1,30364,2,30366,2", 0, 0, 0),
    (102, 70124, 1, 1000000, 100, "71285,2", 0, 0, 0), (103, 30364, 1, 50000, 75, "30360,10", 0, 0, 0),
    (104, 71284, 1, 100000, 100, "71285,1", 0, 0, 0),
    (201, 11290, 1, 3000000, 100, "30372,2,30371,1", 0, 70, 0),
]


class CraftDB(SqliteDB):
    def __init__(self):
        super().__init__()
        c = self.con
        c.execute("CREATE TABLE world.item_proto (vnum INTEGER PRIMARY KEY, locale_name BLOB, type INTEGER DEFAULT 0, "
                  "subtype INTEGER DEFAULT 0, antiflag INTEGER DEFAULT 0, value1 INTEGER DEFAULT 0)")
        c.execute("CREATE TABLE player.mob_proto (vnum INTEGER PRIMARY KEY, locale_name BLOB)")
        c.execute("CREATE TABLE world.crafting_proto (vnum INTEGER PRIMARY KEY, item_vnum INTEGER NOT NULL, "
                  "count INTEGER NOT NULL, price INTEGER NOT NULL, chance INTEGER NOT NULL, recipe TEXT NOT NULL, "
                  "req_progress INTEGER NOT NULL, req_level INTEGER NOT NULL, recipe_vnum INTEGER NOT NULL DEFAULT 0, "
                  "comment TEXT)")
        c.executemany("INSERT INTO world.item_proto VALUES (?, ?, ?, ?, ?, ?)",
                      [(v, n.encode("cp1250"), t, s, a, v1) for v, n, t, s, a, v1 in ITEMS])
        c.executemany("INSERT INTO player.mob_proto VALUES (?, ?)",
                      [(20016, "Kowal".encode("cp1250")), (20090, b"Heuk-Young"), (20018, b"Baek-Go"),
                       (20402, b"Min-Sun")])
        c.executemany("INSERT INTO world.crafting_proto (vnum, item_vnum, count, price, chance, recipe, req_progress, "
                      "req_level, recipe_vnum) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", RECIPES)

    def run(self, sql, params=()):
        sql = sql.replace(" AS BINARY)", " AS BLOB)").replace(" ENGINE=InnoDB", "")
        if sql.lstrip().startswith("DELETE"):
            sql = sql.replace(" LIMIT 1", "")
        return super().run(sql, params)


def game_text(value):
    if isinstance(value, (bytes, bytearray, memoryview)):
        return bytes(value).decode("cp1250")
    return value or ""


def make_app(fake, spool):
    app = Flask(__name__, static_folder=str(HERE / "static"))
    app.secret_key = "test-only"
    app.config.update(TESTING=True, DBE_SPOOL=str(spool))
    app.jinja_loader = ChoiceLoader([
        DictLoader({"base.html": "<main>{% with m=get_flashed_messages(with_categories=true) %}{% for c, t in m %}"
                                 "<p class='flash {{ c }}'>{{ t }}</p>{% endfor %}{% endwith %}"
                                 "{% block content %}{% endblock %}</main>"}),
        FileSystemLoader(str(HERE / "templates"))])
    bp = Blueprint("dbeditor", "dbeditor", url_prefix="/db")
    bp.add_url_rule("/", "index", lambda: "hub")
    bp.add_url_rule("/apply", "apply_page", lambda: "apply")
    ctx = {"app": app, "db": fake.db, "rows": fake.rows, "one": None, "login_required": lambda view: view,
           "game_text": game_text, "server_version": lambda: "2.22.0", "panel_name": lambda: "Test"}
    for module in (crafting, config):
        module.install(bp, ctx)
    app.register_blueprint(bp)
    return app


class ModelTests(unittest.TestCase):
    def test_image_lists(self):
        lists = crafting.parse_lua(SNAPSHOT)
        self.assertEqual(lists[101], [1, 2, 3, 4, 5, 6])
        self.assertEqual(lists[104], [100, 101, 102, 103])
        self.assertEqual(lists[106], [8001, 8002, 8003, 8004, 8005])
        self.assertEqual(lists[20060], [50621])
        self.assertEqual(lists[111], [85001])                          # MT2009_PLUS_SASH_CLOTH_V1: Uriel
        self.assertEqual(crafting.WINDOW_BY_VNUM[111][1], (20011,))
        self.assertNotIn(20061, lists)
        self.assertEqual(len(lists[102]), 68)
        self.assertFalse(set(range(58, 67)) & set(lists[102]))       # the --[[ ]] PvP dews are not listed
        self.assertTrue(set(lists) <= set(crafting.WINDOW_BY_VNUM))   # every window has a known quest

    def test_materials(self):
        self.assertEqual(crafting.parse_materials("25040,1,70035,1"), ([(25040, 1), (70035, 1)], None))
        self.assertEqual(crafting.parse_materials(""), ([], None))
        self.assertIn("bez ilości", crafting.parse_materials("25040,1,70035")[1])
        self.assertIn("tylko liczby", crafting.parse_materials("25040,a")[1])
        self.assertIn("ucięłaby", crafting.parse_materials("25040,0")[1])
        self.assertIn("najwyżej 10", crafting.parse_materials(",".join(["1,1"] * 11))[1])
        self.assertEqual(crafting.format_materials([(1, 2), (3, 4)]), "1,2,3,4")

    def test_client_categories(self):
        cat = crafting.category
        self.assertEqual(cat(101, 4, {"antiflag": 106880}), "Niehandlowalne")      # 106880 has ANTIFLAG_MYSHOP
        self.assertEqual(cat(101, 1, {"antiflag": 0}), "Handlowalne")
        self.assertEqual(cat(104, 100, {}), "Zwoje i Marmury")
        self.assertEqual(cat(104, 103, {}), "Inne")
        self.assertEqual(cat(104, 104, {}), "Wymiany")
        self.assertEqual(cat(102, 11, {"value1": 1}), "Wzmacniające")
        self.assertEqual(cat(102, 11, {"value1": 7}), "Inne")
        self.assertEqual(cat(107, 201, {"type": 2, "subtype": 0}), "Pancerze")
        self.assertEqual(cat(106, 8001, {"type": 1}), "Bronie")
        self.assertEqual(crafting.categories(104), ["Zwoje i Marmury", "Wymiany", "Inne"])

    def test_window_ops_and_effective(self):
        base = {101: [1, 2, 3]}
        ops = crafting.window_ops
        self.assertEqual(ops(base, [], 101, 7, True), ([{"craft_vnum": 101, "recipe_vnum": 7, "present": 1}], []))
        self.assertEqual(ops(base, [], 101, 2, True), ([], []))
        self.assertEqual(ops(base, [], 101, 2, False), ([{"craft_vnum": 101, "recipe_vnum": 2, "present": 0}], []))
        rows = [{"craft_vnum": 101, "recipe_vnum": 2, "present": 0}, {"craft_vnum": 101, "recipe_vnum": 7, "present": 1}]
        self.assertEqual(ops(base, rows, 101, 2, True), ([], [rows[0]]))
        self.assertEqual(ops(base, rows, 101, 7, False), ([], [rows[1]]))
        self.assertEqual(ops(base, rows, 101, 7, True), ([], []))
        self.assertEqual(crafting.effective(base, rows + [{"craft_vnum": 20061, "recipe_vnum": 50621, "present": 1}]),
                         {101: [1, 3, 7], 20061: [50621]})


class Base(unittest.TestCase):
    def setUp(self):
        self.sections = list(dbeditor.SECTIONS)
        self.tables = dict(common_items.TABLES)
        self.tmp = tempfile.TemporaryDirectory()
        self.spool = Path(self.tmp.name) / "spool"
        self.spool.mkdir()
        self.fake = CraftDB()
        common_items._CTX.clear()
        common_items._STATE.update(table_ready=True, history_installed=False)
        crafting._STATE["window_table"] = False
        self.app = make_app(self.fake, self.spool)
        self.client = self.app.test_client()
        with self.client.session_transaction() as session:
            session["seban_update_csrf"] = "tok"
            session["dbe_drops_csrf"] = "tok"
        self.use(self.fake)

    def tearDown(self):
        dbeditor.SECTIONS[:] = self.sections
        common_items.TABLES.clear()
        common_items.TABLES.update(self.tables)
        common_items._STATE.update(table_ready=False, history_installed=False)
        self.tmp.cleanup()

    def use(self, fake):
        common_items._CTX.update(rows=fake.rows, db=fake.db)
        crafting._STATE["window_table"] = False

    def get(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, url)
        return response.get_data(as_text=True)

    def post(self, url, data):
        return self.client.post(url, data=dict(data, dbe_csrf="tok"), follow_redirects=True).get_data(as_text=True)

    def recipe(self, vnum, fake=None):
        found = (fake or self.fake).rows("SELECT * FROM world.crafting_proto WHERE vnum=?", (vnum,))
        return found[0] if found else None

    def window_rows(self, fake=None):
        return [(r["craft_vnum"], r["recipe_vnum"], r["present"]) for r in
                (fake or self.fake).rows("SELECT * FROM world.crafting_window ORDER BY craft_vnum, recipe_vnum")]

    def form(self, vnum, windows, **changes):
        rec = self.recipe(vnum)
        data = {f: str(rec[f]) for f in crafting.FORM_FIELDS}
        for k, (v, c) in enumerate(crafting.parse_materials(rec["recipe"])[0]):
            data[f"mv_{k}"], data[f"mc_{k}"] = str(v), str(c)
        data["okna"] = [str(w) for w in windows]
        data.update(changes)
        return data


class PageTests(Base):
    def test_windows_and_categories(self):
        page = self.get("/db/wytwarzanie-przedmiotow?okno=104")
        for text in ("Heuk-Young", "Zwoje i Marmury", "Zaczarowanie Przedmiotu", "Marmur Błogosławieństwa",
                     "Zaczarowany Klejnot", "Wymiany", "Kowal", "Min-Sun", "1 500 000", "Dodaj do okna"):
            self.assertIn(text, page)
        # 100-102 under "Zwoje i Marmury", Zaczarowany Klejnot (103) under "Inne" - as the client sorts them
        order = [page.index(t) for t in ('dbk-cat">Zwoje i Marmury', 'muted">#100</td>', 'muted">#102</td>', 'dbk-cat">Wymiany',
                                         'dbk-cat">Inne', 'muted">#103</td>')]
        self.assertEqual(order, sorted(order))
        page = self.get("/db/wytwarzanie-przedmiotow?okno=101")
        self.assertIn("Niehandlowalne", page)
        self.assertIn("Handlowalne", page)
        order = [page.index(t) for t in ('dbk-cat">Niehandlowalne', 'muted">#4</td>', 'muted">#6</td>',
                                         'dbk-cat">Handlowalne', 'muted">#1</td>', 'muted">#3</td>')]
        self.assertEqual(order, sorted(order))                            # 71021 & co. have ANTIFLAG_MYSHOP
        page = self.get("/db/wytwarzanie-przedmiotow?okno=0")
        self.assertIn("Wszystkie przepisy", page)
        self.assertIn("1 przepisów nie ma w żadnym oknie", page)          # 104 (no window lists it)
        self.assertIn("Kopia przepisu #1", self.get("/db/wytwarzanie-przedmiotow/nowy?kopia=1&okno=101"))
        form = self.get("/db/wytwarzanie-przedmiotow/przepis/100")
        self.assertIn('name="mv_2" value="30366"', form)
        self.assertIn('value="104" checked', form)
        self.assertIn("kategoria: Zwoje i Marmury", form)

    def test_edit_add_remove_delete_undo(self):
        # edit the price of Zwój Wojny: one field in the history, pending
        page = self.post("/db/wytwarzanie-przedmiotow/przepis", dict(self.form(1, [101], price="450000"),
                                                                     vnum_old="1", okno="101"))
        self.assertIn("Zapisano przepis #1", page)
        self.assertEqual(self.recipe(1)["price"], 450000)
        pending = [c for c in common_items.pending_changes() if c["tbl"] == crafting.PROTO]
        self.assertEqual([(c["row_key"], c["col"], c["new_value"]) for c in pending], [("1", "price", "450000")])
        # a new recipe for Kowal with two materials
        new = {"vnum": "7", "item_vnum": "25044", "count": "2", "price": "5", "chance": "50", "req_level": "10",
               "req_progress": "0", "recipe_vnum": "0", "mv_0": "25040", "mc_0": "3", "mv_1": "70035 – Magiczna Miedź",
               "mc_1": "1", "okna": ["101", "104"], "okno": "101"}
        page = self.post("/db/wytwarzanie-przedmiotow/przepis", new)
        self.assertIn("Zapisano przepis #7", page)
        self.assertEqual(self.recipe(7)["recipe"], "25040,3,70035,1")
        self.assertEqual(self.window_rows(), [(101, 7, 1), (104, 7, 1)])
        self.assertIn("Też w oknach", self.get("/db/wytwarzanie-przedmiotow?okno=101"))
        # the same number again, an unknown item, a broken count: refused, nothing written
        page = self.post("/db/wytwarzanie-przedmiotow/przepis", dict(new, mv_2="99999", mc_2="1"))
        self.assertIn("już istnieje", page)
        self.assertIn("Nie ma przedmiotu 99999", page)
        page = self.post("/db/wytwarzanie-przedmiotow/przepis", dict(new, vnum="8", mc_0="0"))
        self.assertIn("Nic nie zapisano", page)
        self.assertIsNone(self.recipe(8))
        # take recipe 3 off Kowal's list, take 7 off Heuk-Young's (only its own row goes)
        self.post("/db/wytwarzanie-przedmiotow/okno", {"okno": "101", "przepis": "3", "action": "remove"})
        self.post("/db/wytwarzanie-przedmiotow/okno", {"okno": "104", "przepis": "7", "action": "remove"})
        self.assertEqual(self.window_rows(), [(101, 3, 0), (101, 7, 1)])
        page = self.post("/db/wytwarzanie-przedmiotow/okno", {"okno": "101", "przepis": "3", "action": "add"})
        self.assertIn("dodany do okna 101", page)
        self.assertEqual(self.window_rows(), [(101, 7, 1)])
        # delete recipe 2: the row and its place on Kowal's list, in one batch
        before = self.recipe(2)
        page = self.post("/db/wytwarzanie-przedmiotow/usun", {"vnum": "2", "okno": "101"})
        self.assertIn("Usunięto przepis #2", page)
        self.assertIsNone(self.recipe(2))
        self.assertEqual(self.window_rows(), [(101, 2, 0), (101, 7, 1)])
        batch = self.fake.rows("SELECT batch FROM player.web_dbeditor_history ORDER BY id DESC LIMIT 1")[0]["batch"]
        self.assertEqual({r["tbl"] for r in self.fake.rows("SELECT tbl FROM player.web_dbeditor_history WHERE batch=?",
                                                          (batch,))}, {crafting.PROTO, crafting.WINDOW})
        with self.app.test_request_context():
            _b, message, ok = common_items.revert(batch=batch)
        self.assertTrue(ok, message)
        self.assertEqual({k: self.recipe(2)[k] for k in crafting.ROW_COLS}, {k: before[k] for k in crafting.ROW_COLS})
        self.assertEqual(self.window_rows(), [(101, 7, 1)])
        # the page's history lists the saves
        page = self.get("/db/wytwarzanie-przedmiotow?okno=101")
        self.assertIn("Wytwarzanie: usunięty przepis", page)
        self.assertIn("dodany do okna", page)

    def test_export_import_and_world_reset_replay(self):
        with self.app.test_request_context():
            crafting.ensure_window_table()
            common_items.save_rows(crafting.PROTO, [(103, {"chance": 80, "recipe": "30360,12"})])
            common_items.write_rows(crafting.PROTO, inserts=[{"vnum": 105, "item_vnum": 70124, "count": 1, "price": 7,
                                                              "chance": 50, "recipe": "71285,3,30364,1",
                                                              "req_progress": 0, "req_level": 30, "recipe_vnum": 0}])
            common_items.write_rows(crafting.WINDOW, inserts=[{"craft_vnum": 104, "recipe_vnum": 105, "present": 1},
                                                              {"craft_vnum": 101, "recipe_vnum": 6, "present": 0}])
        text = self.client.get("/db/config/eksport.txt").get_data(as_text=True)
        self.assertIn("[crafting] world.crafting_proto", text)
        self.assertIn("[crafting_win] world.crafting_window", text)
        self.assertIn('103\trecipe\t"30360,10" -> "30360,12"', text)
        self.assertIn('"recipe":"71285,3,30364,1"', text.replace(" ", ""))
        # server B: the same stock game, the export imported
        other = CraftDB()
        self.use(other)
        page = self.post("/db/config/podglad", {"tekst": config.compact(text)})
        payload = re.search(r'name="payload" value="([^"]+)"', page).group(1)
        page = self.post("/db/config/importuj", {"payload": payload, "czesc": ["crafting", "crafting_win"]})
        self.assertIn("Zaimportowano konfigurację", page)
        self.assertEqual(self.recipe(105, other)["recipe"], "71285,3,30364,1")
        self.assertEqual((self.recipe(103, other)["chance"], self.recipe(103, other)["recipe"]), (80, "30360,12"))
        self.assertEqual(self.window_rows(other), [(101, 6, 0), (104, 105, 1)])
        # a world reset: stock tables again, the history's replay sets the changes again
        self.use(self.fake)
        statements, skipped = reapply.replay_statements()
        self.assertEqual(skipped, [])
        self.assertTrue(all(s.isascii() for s in statements))
        fresh = CraftDB()
        fresh.con.execute("CREATE TABLE world.crafting_window (craft_vnum INTEGER, recipe_vnum INTEGER, "
                          "present INTEGER DEFAULT 1, PRIMARY KEY (craft_vnum, recipe_vnum))")   # apply.sh's
        for sql in statements:
            fresh.con.execute(sql)
        self.use(fresh)
        self.assertEqual(game_text(self.recipe(105, fresh)["recipe"]), "71285,3,30364,1")
        self.assertEqual(self.recipe(103, fresh)["chance"], 80)
        self.assertEqual(self.window_rows(fresh), [(101, 6, 0), (104, 105, 1)])
        self.assertEqual(reapply.drift()["restore"], [])

    def test_game_status_shown(self):
        (self.spool / "crafting").mkdir()
        (self.spool / "crafting" / "status").write_text(
            "state=ok\ntime=1791294649\ngroups=2\nsha=x\nmessage=applied: 2 window list(s) changed by the panel; "
            "left out (no such recipe in crafting_proto): 9\n")
        page = self.get("/db/wytwarzanie-przedmiotow?okno=101")
        self.assertIn("listy zmienione w panelu działają (2 okien)", page)
        self.assertIn("pominięto przepisy, których nie ma w bazie:  9", page)
        (self.spool / "crafting" / crafting.BASE_NAME).write_text("crafting_data = {\r\n [101] = {1, 2},\r\n}\r\n")
        self.assertEqual(crafting.base_lists(self.spool), ({101: [1, 2]}, "game"))


@unittest.skipUnless(shutil.which("sh") and shutil.which("awk") and M2_CRAFTING.is_file(), "no sh/awk or m2-crafting")
class GameSideTests(unittest.TestCase):
    def run_m2(self, root, rows, *commands, schema=True):
        bindir = root / "bin"
        bindir.mkdir(exist_ok=True)
        fake = bindir / "mariadb"
        fake.write_text("#!/bin/sh\ncase \"$*\" in\n"
                        f" *information_schema*) echo {1 if schema else 0} ;;\n"
                        f" *crafting_window*) printf '{rows}' ;;\nesac\n")
        fake.chmod(0o755)
        env = dict(os.environ, M2_SHARE_DIR=str(root / "share"), M2_VAR_DIR=str(root / "var"),
                   M2_RATES_SPOOL=str(root / "spool"), PATH=f"{bindir}:/usr/bin:/bin")
        for command in commands:
            subprocess.run(["sh", str(M2_CRAFTING), command], env=env, check=True, capture_output=True)

    def test_m2_crafting_appends_the_lists(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lib = root / "share" / "locale" / "poland" / "quest" / "libs" / "crafting"
            lib.mkdir(parents=True)
            (root / "spool" / "crafting").mkdir(parents=True)
            image = crafting.SNAPSHOT.read_bytes()
            (lib / "crafting_data.lua").write_bytes(image)
            rows = "101\\t3\\t0\\t1\\n101\\t7\\t1\\t1\\n101\\t9\\t1\\t0\\n20061\\t50621\\t1\\t1\\n"
            self.run_m2(root, rows, "prepare", "apply")
            live = (lib / "crafting_data.lua").read_bytes()
            self.assertTrue(live.startswith(image))                          # the image's file stays as it is
            tail = live[len(image):].decode("ascii")
            self.assertIn(crafting.MARK, tail)
            self.assertIn("mt2009_crafting_window(101, {7}, {3})\r\n", tail)
            self.assertIn("mt2009_crafting_window(20061, {50621}, {})\r\n", tail)
            self.assertNotIn("9}", tail)                                     # no such recipe: left out
            self.assertEqual((root / "spool" / "crafting" / crafting.BASE_NAME).read_bytes(), image)
            status = crafting.game_status(root / "spool")
            self.assertEqual((status["state"], status["groups"]), ("ok", "2"))
            self.assertIn("left out (no such recipe in crafting_proto): 9", status["message"])
            # what the panel would compute is what the Lua does
            base = crafting.parse_lua(image.decode("latin-1"))
            rows_list = [{"craft_vnum": 101, "recipe_vnum": 3, "present": 0}, {"craft_vnum": 101, "recipe_vnum": 7, "present": 1},
                         {"craft_vnum": 20061, "recipe_vnum": 50621, "present": 1}]
            self.assertEqual(crafting.effective(base, rows_list)[101], [1, 2, 4, 5, 6, 7])
            # no rows: the image's file again
            self.run_m2(root, "", "apply")
            self.assertEqual((lib / "crafting_data.lua").read_bytes(), image)
            self.assertEqual(crafting.game_status(root / "spool")["state"], "base")
            # no table yet (an older world): the image's file
            self.run_m2(root, rows, "apply", schema=False)
            self.assertEqual((lib / "crafting_data.lua").read_bytes(), image)


if __name__ == "__main__":
    unittest.main()
