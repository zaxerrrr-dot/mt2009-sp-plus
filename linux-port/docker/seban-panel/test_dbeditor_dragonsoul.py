"""MT2009_PLUS_DB_EDITOR_DRAGONSOUL_V1: python3 -m unittest test_dbeditor_dragonsoul

The database editor's "Alchemia (Smocze Kamienie)" part (dbeditor/dragonsoul.py)
through Flask's test client on a temporary spool, its config export /
import adapter, and the game side (bin/m2-dragonsoul) under sh."""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from flask import Blueprint, Flask
from jinja2 import ChoiceLoader, DictLoader, FileSystemLoader

import dbeditor
from dbeditor import config, dragonsoul as ds
from dbeditor import dropfiles as df

HERE = Path(__file__).resolve().parent
M2_DS = HERE.parent / "game" / "bin" / "m2-dragonsoul"
IMAGE = ds.SNAPSHOT.read_bytes()


def make_app(spool):
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
    ds.install(bp, {"login_required": lambda view: view, "rows": None, "game_text": lambda v: v or ""})
    app.register_blueprint(bp)
    return app


class ModelTests(unittest.TestCase):
    def test_snapshot_parses_and_is_valid(self):
        m = ds.model(IMAGE)
        self.assertEqual([s["name"] for s in m["stones"]],
                         ["Diament", "Rubin", "Jadeit", "Szafir", "Granat", "Onyks", "Ametyst"])
        diamond = m["stones"][0]
        self.assertEqual([(b["apply"]["value"], b["value"]["value"]) for b in diamond["basic"]],
                         [("INT", "8"), ("ATTBONUS_MILGYO", "9")])
        self.assertEqual(diamond["basic"][0]["name"], "Inteligencja")
        self.assertEqual(len(m["stones"][2]["additional"]), 5)
        self.assertEqual(ds.max_weight(m["root"]), 160.0)
        self.assertEqual(ds.on_stone(9, 160), 15)
        self.assertEqual(len(m["weights"]), 6)
        self.assertEqual(m["weights"][5]["steps"][4]["cells"][6]["value"], "160")
        self.assertEqual(m["refine_grade"][0]["fee"]["value"], "30000")
        self.assertEqual(m["refine_strength"][2]["probs"][0]["value"], "100")
        self.assertEqual(ds.validate(IMAGE, IMAGE), [])

    def test_multiply_keeps_everything_else(self):
        text, changed = ds.multiply(ds.decode(IMAGE), 2.0)
        self.assertGreater(changed, 40)
        new = ds.encode(text)
        m = ds.model(new)
        self.assertEqual(m["stones"][0]["basic"][0]["value"]["value"], "16")
        self.assertEqual(m["stones"][1]["additional"][0]["value"]["value"], "400")
        self.assertEqual(m["stones"][1]["additional"][0]["prob"]["value"], "10")     # chances stay
        self.assertEqual(len(new.splitlines()), len(IMAGE.splitlines()))
        self.assertIn("성혼석".encode("euc_kr"), new)
        self.assertEqual(new.count(b"\r\n"), IMAGE.count(b"\r\n"))
        self.assertEqual(ds.validate(new, IMAGE), [])
        only, n = ds.multiply(ds.decode(IMAGE), 1.5, ("basic",))
        self.assertEqual(n, 14)
        self.assertEqual(ds.parse_factor("+100%"), 2.0)
        self.assertEqual(ds.parse_factor("×1,5"), 1.5)
        self.assertEqual(ds.parse_factor("200%"), 2.0)
        self.assertIsNone(ds.parse_factor("abc"))
        self.assertIsNone(ds.parse_factor("100"))

    def test_weights_and_validation(self):
        text, n = ds.scale_weights(ds.decode(IMAGE), 2)
        self.assertGreater(n, 100)
        m = ds.model(text)
        self.assertEqual(m["weights"][5]["steps"][4]["cells"][6]["value"], "320")
        self.assertEqual(m["weights"][0]["steps"][0]["cells"][6]["value"], "0")
        bad = ds.decode(IMAGE).replace("Group RefineStepTables", "Group Nope", 1)
        self.assertTrue(any("RefineStepTables" in p for p in ds.validate(bad)))
        bad = ds.decode(IMAGE).replace("\tINT\t8", "\tINT\t30000", 1)
        self.assertTrue(any("przekracza" in p for p in ds.validate(bad)))
        bad = ds.decode(IMAGE).replace("\tINT\t8", "\tFOO\t8", 1)
        self.assertTrue(any("FOO" in p for p in ds.validate(bad)))


class PageTests(unittest.TestCase):
    def setUp(self):
        self.sections = list(dbeditor.SECTIONS)
        self.tmp = tempfile.TemporaryDirectory()
        self.spool = Path(self.tmp.name)
        self.client = make_app(self.spool).test_client()
        with self.client.session_transaction() as session:
            session["dbe_drops_csrf"] = "tok"

    def tearDown(self):
        dbeditor.SECTIONS[:] = self.sections
        self.tmp.cleanup()

    def post(self, data):
        return self.client.post("/db/alchemia", data=dict(data, dbe_csrf="tok"), follow_redirects=True) \
            .get_data(as_text=True)

    def test_page_edit_multiply_reset_export(self):
        page = self.client.get("/db/alchemia").get_data(as_text=True)
        for text in ("Alchemia (Smocze Kamienie)", "Diament", "Ametyst", "Inteligencja", "Mnożnik bonusów",
                     "Ulepszanie siły", "Bez zmian z panelu", "Mityczny"):
            self.assertIn(text, page)
        m = ds.model(IMAGE)
        sha = ds.sha(IMAGE)
        cid = m["stones"][0]["basic"][0]["value"]["id"]
        fee = m["refine_grade"][0]["fee"]["id"]
        page = self.post({"sha": sha, cid: "10", fee: "25000", "action": "save"})
        self.assertIn("Zapisano tabelę alchemii (2 zmienionych", page)
        saved = df.custom_path(self.spool, "dragonsoul").read_bytes()
        m2 = ds.model(saved)
        self.assertEqual((m2["stones"][0]["basic"][0]["value"]["value"], m2["refine_grade"][0]["fee"]["value"]),
                         ("10", "25000"))
        self.assertEqual([p["key"] for p in df.pending_changes(self.spool)], ["dragonsoul"])
        # a stale form is refused
        self.assertIn("zmieniła się w międzyczasie", self.post({"sha": sha, cid: "11"}))
        # bad value: nothing saved
        page = self.post({"sha": ds.sha(saved), cid: "abc"})
        self.assertIn("Nic nie zapisano", page)
        page = self.post({"sha": ds.sha(saved), "action": "multiply", "factor": "+100%", "scope": "all"})
        self.assertIn("Zapisano", page)
        doubled = ds.model(df.custom_path(self.spool, "dragonsoul").read_bytes())
        self.assertEqual(doubled["stones"][0]["basic"][0]["value"]["value"], "20")
        # export carries the whole file, import of it into a fresh spool brings it back
        adapter = config.FILE_ADAPTERS["dragonsoul"]
        self.assertTrue(adapter.available())
        self.assertEqual(adapter.keys(self.spool), ["dragonsoul"])
        data = adapter.read(self.spool, "dragonsoul")
        self.assertTrue(adapter.effective("dragonsoul", data))
        self.assertEqual(adapter.base(self.spool, "dragonsoul"), IMAGE)
        self.assertEqual(adapter.check(self.spool, "dragonsoul", data, lambda k, v: set(v))[0], [])
        content = {"dragonsoul": {"records": [], "files": [{"key": "dragonsoul", "data": data,
                                                            "title": adapter.title("dragonsoul")}]}}
        text = config.render_text(content)
        self.assertIn("[dragonsoul]", text)
        parsed = config.parse(text)
        self.assertEqual(parsed["parts"]["dragonsoul"]["files"][0]["data"], data)   # bytes come back exactly
        # reset: back to the image's file, two backups to restore from
        self.post({"action": "reset"})
        self.assertFalse(df.custom_path(self.spool, "dragonsoul").exists())
        backups = df.list_backups(self.spool, ["dragonsoul"])
        self.assertEqual(len(backups), 3)
        self.post({"action": "restore", "name": backups[0]["name"]})
        self.assertEqual(df.custom_path(self.spool, "dragonsoul").read_bytes(), data)


@unittest.skipUnless(shutil.which("sh") and M2_DS.is_file(), "no sh or m2-dragonsoul")
class GameSideTests(unittest.TestCase):
    def run_m2(self, root, *commands):
        env = dict(os.environ, M2_SHARE_DIR=str(root / "share"), M2_VAR_DIR=str(root / "var"),
                   M2_RATES_SPOOL=str(root / "spool"), PATH="/usr/bin:/bin")
        for command in commands:
            subprocess.run(["sh", str(M2_DS), command], env=env, check=True, capture_output=True)

    def test_m2_dragonsoul_takes_the_panels_table(self):
        ds.register_file()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            locale = root / "share" / "locale" / "poland"
            locale.mkdir(parents=True)
            (root / "spool" / "dragonsoul").mkdir(parents=True)
            live = locale / "dragon_soul_table.txt"
            live.write_bytes(IMAGE)
            spool = root / "spool"
            doubled = ds.encode(ds.multiply(ds.decode(IMAGE), 2)[0])
            df.write_custom(spool, "dragonsoul", doubled)
            self.run_m2(root, "prepare", "apply")
            self.assertEqual(live.read_bytes(), doubled)
            self.assertEqual((spool / "dragonsoul" / "dragon_soul_table.base.txt").read_bytes(), IMAGE)
            self.assertEqual(df.live_state(spool, "dragonsoul")["kind"], "ok")
            self.assertEqual(df.pending_changes(spool), [])
            # a different stone list: rejected, the image's table goes back
            bad = ds.decode(doubled).replace("\t7\t", "\t8\t", 1)
            df.write_custom(spool, "dragonsoul", ds.encode(bad))
            self.run_m2(root, "apply")
            self.assertEqual(live.read_bytes(), IMAGE)
            state = df.live_state(spool, "dragonsoul")
            self.assertEqual(state["kind"], "error")
            self.assertIn("VnumMapper", state["text"])
            # an unclosed group
            df.write_custom(spool, "dragonsoul", doubled.rsplit(b"}", 1)[0])
            self.run_m2(root, "apply")
            self.assertIn("not closed", df.live_state(spool, "dragonsoul")["text"])
            # no file: the image's
            df.write_custom(spool, "dragonsoul", None)
            self.run_m2(root, "apply")
            self.assertEqual(live.read_bytes(), IMAGE)
            self.assertEqual(df.live_state(spool, "dragonsoul")["kind"], "ok")


if __name__ == "__main__":
    unittest.main()
