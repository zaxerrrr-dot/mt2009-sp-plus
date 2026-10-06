"""MT2009_PLUS_DB_EDITOR_CUBE_V1: python3 -m unittest test_dbeditor_cube

The database editor's "Wytwarzanie (cube)" part (dbeditor/cube.py): the
parser / writer on the image's real cube.txt (byte for byte when nothing
changes), the checks, the pages through Flask's test client on a temporary
spool, its config export / import adapter, and the game side (bin/m2-cube)
under sh."""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from flask import Blueprint, Flask
from jinja2 import ChoiceLoader, DictLoader, FileSystemLoader

import dbeditor
from dbeditor import config, cube
from dbeditor import dropfiles as df

HERE = Path(__file__).resolve().parent
M2_CUBE = HERE.parent / "game" / "bin" / "m2-cube"
IMAGE = cube.SNAPSHOT.read_bytes()
SEON = 20091


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
    cube.install(bp, {"login_required": lambda view: view, "rows": None, "game_text": lambda v: v or ""})
    app.register_blueprint(bp)
    return app


class ModelTests(unittest.TestCase):
    def test_real_file_round_trip(self):
        doc = cube.parse(IMAGE)
        self.assertEqual(len(doc["recipes"]), 118)
        self.assertEqual(cube.serialize(doc), IMAGE)                      # byte for byte
        self.assertEqual(doc["problems"], [])
        self.assertEqual(cube.validate(IMAGE), ([], []))
        npcs = {}
        for r in doc["recipes"]:
            npcs[cube.npc_of(r)] = npcs.get(cube.npc_of(r), 0) + 1
        self.assertEqual(npcs, {20017: 12, 20018: 4, 20022: 18, 20383: 72, SEON: 12})
        first = doc["recipes"][0]
        self.assertEqual((first["items"], first["rewards"], first["percent"], first["gold"]),
                         ([(50721, 1)], [(50801, 1)], 100, 0))
        self.assertEqual(cube.comment_of(first), "복숭아꽃진액")              # EUC-KR comment
        last = doc["recipes"][-1]
        self.assertEqual((last["npcs"], last["rewards"], last["gold"], len(last["items"])),
                         ([SEON], [(12040, 1)], 2000000, 5))
        self.assertIn("Czarna Szata+9", cube.comment_of(last))

    def test_edit_add_copy_delete(self):
        doc = cube.parse(IMAGE)
        values = cube.values_of(doc[("recipes")][-1])
        values.update(percent=50, gold=1500000)
        cube.update_recipe(doc, len(doc["recipes"]) - 1, values)
        data = cube.serialize(doc)
        self.assertTrue(data.startswith(IMAGE.rsplit(b"section", 1)[0]))  # everything before stays
        self.assertTrue(data.endswith(b"reward\t12040\t1\r\npercent\t50\r\ngold\t1500000\r\nend\r\n"))
        # a copy goes right after its source; a new one after its NPC's last recipe
        i = cube.add_recipe(doc, cube.values_of(doc["recipes"][0]), "kopia", after=0)
        self.assertEqual(i, 1)
        j = cube.add_recipe(doc, {"npcs": [20018], "items": [(50721, 2)], "rewards": [(50801, 1)],
                                  "percent": 30, "gold": 0}, "Nowy łódź")
        self.assertEqual(cube.npc_of(doc["recipes"][j - 1]), 20018)
        self.assertNotEqual(cube.npc_of(doc["recipes"][j + 1]), 20018)
        again = cube.parse(cube.serialize(doc))
        self.assertEqual(len(again["recipes"]), 120)
        self.assertEqual(cube.comment_of(again["recipes"][j]), "Nowy lodz")       # ASCII in the file
        self.assertEqual(again["recipes"][j]["items"], [(50721, 2)])
        self.assertEqual(cube.validate(again)[0], [])
        # deleting the additions gives the edited file back
        cube.delete_recipe(doc, j)
        cube.delete_recipe(doc, i)
        self.assertEqual(cube.serialize(doc), data)
        # deleting a real recipe removes its comment, the rest stays parseable
        cube.delete_recipe(doc, 0)
        rest = cube.serialize(doc)
        self.assertNotIn("복숭아꽃진액".encode("euc_kr"), rest.split(b"section", 1)[0])
        self.assertEqual(len(cube.parse(rest)["recipes"]), 117)

    def test_validation(self):
        text = IMAGE.decode("latin-1")
        bad = text.replace("percent\t100", "percent\t101", 1).encode("latin-1")
        self.assertTrue(any("szansa 101%" in e for e in cube.validate(bad)[0]))
        bad = text.replace("item\t50721\t1", "item\t50721\t201", 1).encode("latin-1")
        self.assertTrue(any("1–200" in e for e in cube.validate(bad)[0]))
        bad = text.replace("end", "", 1).encode("latin-1")
        self.assertTrue(any("bez „end”" in e for e in cube.validate(bad)[0]))
        bad = (b"npc\t20018\r\n" + IMAGE)
        self.assertTrue(any("poza sekcją" in e for e in cube.validate(bad)[0]))
        head, tail = text.rsplit("item\t11899\t1\r\n", 1)                # the last recipe has 5
        six = (head + "item\t11899\t1\r\nitem\t1\t1\r\n" + tail).encode("latin-1")
        self.assertTrue(any("najwyżej 5" in e for e in cube.validate(six)[0]))
        nonpc = text.replace("npc\t20018\t\r\n", "", 1).encode("latin-1")
        self.assertTrue(any("brak NPC" in e for e in cube.validate(nonpc)[0]))
        gold = text.replace("gold\t2000000", "gold\t3000000000", 1).encode("latin-1")
        self.assertTrue(any("koszt" in e for e in cube.validate(gold)[0]))
        known_items = {v for r in cube.parse(IMAGE)["recipes"] for v, _c in r["items"] + r["rewards"]}
        errors, _w = cube.validate(IMAGE, known_items - {50801}, {20017, 20018, 20022, 20383})
        self.assertTrue(any("przedmiotu 50801 nie ma" in e for e in errors))
        self.assertTrue(any(f"NPC {SEON} nie istnieje" in e for e in errors))
        # a recipe that the one above it always beats
        doc = cube.parse(IMAGE)
        cube.add_recipe(doc, {"npcs": [20018], "items": [(50721, 1), (50722, 1)], "rewards": [(50802, 1)],
                              "percent": 100, "gold": 0})
        self.assertTrue(any("nigdy nie zadziała" in w for w in cube.validate(doc)[1]))
        values, _c, errors = cube.form_values({"npc": "20091", "mv_0": "149", "mc_0": "1", "mv_2": "abc",
                                               "reward_v": "270", "reward_c": "", "percent": "100", "gold": ""})
        self.assertTrue(any("nie liczba" in e for e in errors))
        values, _c, errors = cube.form_values({"npc": "20091", "mv_0": "149", "mc_0": "1", "reward_v": "270",
                                               "percent": "100"})
        self.assertEqual(errors, [])
        self.assertEqual(values, {"npcs": [SEON], "items": [(149, 1)], "rewards": [(270, 1)], "percent": 100,
                                  "gold": 0})


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
        return self.client.post("/db/wytwarzanie", data=dict(data, dbe_csrf="tok"), follow_redirects=True) \
            .get_data(as_text=True)

    def custom(self):
        return df.custom_path(self.spool, "cube").read_bytes()

    def test_pages_edit_add_copy_delete_undo_export(self):
        page = self.client.get(f"/db/wytwarzanie?npc={SEON}").get_data(as_text=True)
        for text in ("Wytwarzanie (Seon-Pyeong)", "NPC 20091", "Kopiuj przepis", "Bez zmian z panelu", "2 000 000",
                     "Czarna Szata+9", "106 z nich należy do NPC bez okna kostki"):
            self.assertIn(text, page)
        # MT2009_PLUS_DB_EDITOR_CRAFTING_V1: only Seon-Pyeong opens the cube window - Baek-Go & co. are not listed
        self.assertNotIn("npc=20018", page)
        self.assertNotIn("bez okna</small>", page)
        sha = cube.sha(IMAGE)
        last = len(cube.parse(IMAGE)["recipes"]) - 1
        form = self.client.get(f"/db/wytwarzanie/przepis/{last}").get_data(as_text=True)
        self.assertIn('name="mv_4" value="27994"', form)
        self.assertIn('name="reward_v" value="12040"', form)
        self.assertIn("Kopia przepisu", self.client.get(f"/db/wytwarzanie/nowy?kopia={last}").get_data(as_text=True))
        recipe = {"npc": str(SEON), "mv_0": "11899", "mc_0": "1", "mv_1": "70031", "mc_1": "1", "mv_2": "27992",
                  "mc_2": "2", "mv_3": "27993", "mc_3": "2", "mv_4": "27994", "mc_4": "2", "reward_v": "12040",
                  "reward_c": "1", "percent": "75", "gold": "1000000",
                  "comment": "Czarna Szata+9 (66) -> Szata Smoka+0 (80)"}
        page = self.post(dict(recipe, sha=sha, index=str(last)))
        self.assertIn("Zapisano (zmiana przepisu", page)
        saved = self.custom()
        r = cube.parse(saved)["recipes"][last]
        self.assertEqual((r["percent"], r["gold"]), (75, 1000000))
        self.assertEqual([p["key"] for p in df.pending_changes(self.spool)], ["cube"])
        self.assertIn("zmieniły się w międzyczasie", self.post(dict(recipe, sha=sha, index=str(last))))
        # a copy (new recipe after the source)
        page = self.post(dict(recipe, sha=cube.sha(saved), index="", after=str(last), percent="10"))
        self.assertIn("nowy przepis", page)
        doc = cube.parse(self.custom())
        self.assertEqual(len(doc["recipes"]), last + 2)
        self.assertEqual(doc["recipes"][-1]["percent"], 10)
        # bad values: nothing saved, the form comes back
        before = self.custom()
        page = self.post(dict(recipe, sha=cube.sha(before), index="", percent="150", mc_0="0"))
        self.assertIn("Nic nie zapisano", page)
        self.assertIn('name="percent"', page)
        self.assertEqual(self.custom(), before)
        # delete the copy: the file is the edited one again
        self.post({"sha": cube.sha(before), "index": str(last + 1), "action": "delete"})
        self.assertEqual(self.custom(), saved)
        # history and undo
        history = cube.read_history(self.spool)
        self.assertEqual(len(history), 3)
        self.assertIn("usunięto przepis", history[0]["what"])
        self.post({"action": "undo"})
        self.assertEqual(self.custom(), before)
        # the config export carries the whole file and imports back exactly
        adapter = config.FILE_ADAPTERS["cube"]
        self.assertTrue(adapter.available())
        self.assertEqual(adapter.keys(self.spool), ["cube"])
        data = adapter.read(self.spool, "cube")
        self.assertTrue(adapter.effective("cube", data))
        self.assertEqual(adapter.base(self.spool, "cube"), IMAGE)
        errors, warnings = adapter.check(self.spool, "cube", data, lambda kind, v: set(v))
        self.assertEqual(errors, [])
        content = {"cube": {"records": [], "files": [{"key": "cube", "data": data, "title": adapter.title("cube")}]}}
        text = config.render_text(content)
        self.assertIn("[cube]", text)
        self.assertEqual(config.parse(text)["parts"]["cube"]["files"][0]["data"], data)
        # reset: back to the image's file; a restore brings the backup back
        self.post({"action": "reset"})
        self.assertFalse(df.custom_path(self.spool, "cube").exists())
        adapter.write(self.spool, "cube", data, "import")
        self.assertEqual(self.custom(), data)
        adapter.write(self.spool, "cube", IMAGE, "import")       # the image's own bytes = no file
        self.assertFalse(df.custom_path(self.spool, "cube").exists())
        backups = df.list_backups(self.spool, ["cube"])
        self.post({"action": "restore", "name": backups[0]["name"]})
        self.assertEqual(self.custom(), data)
        self.assertIn(b"text/plain", self.client.get("/db/wytwarzanie/plik").headers["Content-Type"].encode())


@unittest.skipUnless(shutil.which("sh") and shutil.which("awk") and M2_CUBE.is_file(), "no sh/awk or m2-cube")
class GameSideTests(unittest.TestCase):
    def run_m2(self, root, *commands):
        env = dict(os.environ, M2_SHARE_DIR=str(root / "share"), M2_VAR_DIR=str(root / "var"),
                   M2_RATES_SPOOL=str(root / "spool"), PATH="/usr/bin:/bin")
        for command in commands:
            subprocess.run(["sh", str(M2_CUBE), command], env=env, check=True, capture_output=True)

    def test_m2_cube_takes_the_panels_recipes(self):
        cube.register_file()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            locale = root / "share" / "locale" / "poland"
            (locale / "quest" / "object" / str(SEON) / "chat").mkdir(parents=True)
            (locale / "quest" / "object" / str(SEON) / "chat" / "seon_pyeong.start.0.script").write_text(
                'command("cube open")\n')
            (locale / "quest" / "object" / "20016").mkdir()
            (root / "spool" / "cube").mkdir(parents=True)
            live = locale / "cube.txt"
            live.write_bytes(IMAGE)
            spool = root / "spool"
            doc = cube.parse(IMAGE)
            cube.add_recipe(doc, {"npcs": [SEON], "items": [(149, 1)], "rewards": [(270, 1)], "percent": 50,
                                  "gold": 10})
            new = cube.serialize(doc)
            cube.save(spool, new, "test")
            self.run_m2(root, "prepare", "apply")
            self.assertEqual(live.read_bytes(), new)
            self.assertEqual((spool / "cube" / "cube.base.txt").read_bytes(), IMAGE)
            self.assertEqual((spool / "cube" / "cube_npcs.txt").read_text().split(), [str(SEON)])
            self.assertEqual(df.live_state(spool, "cube")["kind"], "ok")
            self.assertEqual(df.pending_changes(spool), [])
            # broken files: rejected, the image's recipes go back
            text = new.decode("latin-1")
            for bad, why in ((text.replace("percent\t50", "percent\t500"), "percent"),
                             (text.replace("item\t149\t1", "item\t149\t0"), "count"),
                             (text.rsplit("end", 1)[0], "not closed"),
                             ("npc\t20091\r\n" + text, "outside a section"),
                             (text.replace("item\t149\t1\r\n", "item\t149\t1\r\n" + "item\t1\t1\r\n" * 5), "5 items")):
                df.write_custom(spool, "cube", bad.encode("latin-1"))
                self.run_m2(root, "apply")
                self.assertEqual(live.read_bytes(), IMAGE)
                state = df.live_state(spool, "cube")
                self.assertEqual(state["kind"], "error")
                self.assertIn(why, state["text"])
            # no file: the image's
            df.write_custom(spool, "cube", None)
            self.run_m2(root, "apply")
            self.assertEqual(live.read_bytes(), IMAGE)
            self.assertEqual(df.live_state(spool, "cube")["kind"], "ok")


if __name__ == "__main__":
    unittest.main()
