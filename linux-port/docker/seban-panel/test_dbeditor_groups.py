"""MT2009_PLUS_DB_EDITOR_GROUPS_V1: python3 -m unittest test_dbeditor_groups

The database editor's "Grupy potworów" part (dbeditor/groups.py): the
group.txt / group_group.txt reader and writer, the spawn points it counts per
map (regen.txt, boss.txt, npc.txt, the timed bosses), the list with its
filters and pages, the edits with history and undo through the Flask test
client on a temporary spool, the config export adapter, the "Spawny
potworów" page seeing the panel's groups, and the game side (bin/m2-groups)
merging what the panel wrote into the image's files."""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from flask import Blueprint, Flask
from jinja2 import ChoiceLoader, DictLoader, FileSystemLoader

import dbeditor
from dbeditor import config
from dbeditor import dropfiles as df
from dbeditor import groups as G
from dbeditor import regen

HERE = Path(__file__).resolve().parent
M2_GROUPS = HERE.parent / "game" / "bin" / "m2-groups"

KOREAN = "들개".encode("euc_kr").decode("latin-1")      # the package's names are EUC-KR bytes
GROUPS = (f"Group\tL01_{KOREAN}(PAWN)\n{{\n\tLeader\tWildhund\t101\n\tVnum\t101\n\t1\tWildhund\t101\n"
          "\t2\tWildhund\t101\n}\n"
          "Group\tWolves\n{\n\tLeader\tWolf\t102\n\tVnum\t102\n\t1\tWildhund\t101\n\t2\tWildhund\t101\n}\n"
          "// a comment between groups\n"
          "Group\tAlpha\n{\n\tLeader\tAlpha\t103\n\tVnum\t103\n\t1\tWolf\t102\n\t2\tWolf\t102\n\t3\tWolf\t102\n}\n"
          "Group\tLonely\n{\n\tLeader\tHorse\t20101\n\tVnum\t900\n}\n"
          "Group\tDuplicate\n{\n\tLeader\tWolf\t102\n\tVnum\t101\n}\n")          # the first 101 wins
GROUP_GROUPS = ("Group\ta1_01\t\t\r\n{\t\t\t\r\n\tVnum\t101\t\r\n\t1\t101\t1\r\n\t2\t102\t5\r\n}\t\t\t\r\n"
                "Group\ta1_02\r\n{\r\n\tVnum\t102\r\n\t1\t103\r\n}\r\n")
REGEN = ("r\t100\t100\t10\t10\t0\t0\t60s\t100\t2\t101\r\n"
         "g\t200\t200\t10\t10\t0\t0\t60s\t100\t3\t103\r\n"
         "g\t250\t200\t10\t10\t0\t0\t60s\t100\t1\t103\r\n"
         "m\t300\t300\t10\t10\t0\t0\t60s\t100\t5\t101\r\n")
BOSS = "g\t50\t50\t1\t1\t0\t0\t30m\t100\t1\t102\r\n"
NPC = "g\t60\t60\t1\t1\t0\t0\t1m\t100\t1\t900\r\n"
SPECIAL = ("Group\tWolfBoss\r\n{\r\n\tvnum\t5001\r\n\tspawn_vnum\t103\r\n\tspawn_type\tgroup\r\n\tmap_index\t1\r\n"
           "\ttime\t600-900\r\n\ttime_type\tnormal\r\n\tcount\t1\r\n\t1\t100\t100\t0\r\n}\r\n")
SETTING = "ScriptType\tMapSetting\r\n\r\nCellScale\t200\r\nMapSize\t4\t5\r\nBasePosition\t409600\t896000\r\n"
MOBS = {101: ("Dziki Pies", 0, 0, 1), 102: ("Wilk", 0, 0, 3), 103: ("Alfa Wilk", 1, 0, 5),
        104: ("Niebieski Wilk", 0, 0, 7), 20101: ("Koń", 0, 1, 1)}


def fake_rows(sql, params=()):
    if "FROM player.mob_proto" in sql:
        return [{"vnum": v, "locale_name": n, "name": "", "rank": rank, "type": kind, "level": level, "drop_item": 0}
                for v, (n, rank, kind, level) in MOBS.items()]
    return []


def publish(spool, with_groups_base=True):
    """The files the game publishes into the spool (m2-groups, m2-regen, m2-spawns)."""
    spool = Path(spool)
    if with_groups_base:
        (spool / "groups" / "base" / "maps" / "metin2_map_a1").mkdir(parents=True)
        (spool / "groups" / "group.base.txt").write_bytes(GROUPS.encode("latin-1"))
        (spool / "groups" / "group_group.base.txt").write_bytes(GROUP_GROUPS.encode("latin-1"))
        (spool / "groups" / "base" / "maps" / "metin2_map_a1" / "npc.txt").write_text(NPC)
    base = spool / "regen" / "base"
    (base / "maps" / "metin2_map_a1").mkdir(parents=True)
    (base / "maps" / "metin2_map_a1" / "regen.txt").write_text(REGEN)
    (base / "maps" / "metin2_map_a1" / "Setting.txt").write_text(SETTING)
    (base / "index").write_text("1\tmetin2_map_a1\n64\tmap_n_threeway\n")
    (base / "group.txt").write_bytes(GROUPS.encode("latin-1"))
    (base / "group_group.txt").write_bytes(GROUP_GROUPS.encode("latin-1"))
    spawns = spool / "spawns" / "base"
    (spawns / "maps" / "map_n_threeway").mkdir(parents=True)
    (spawns / "maps" / "map_n_threeway" / "boss.txt").write_text(BOSS)
    (spawns / "map_index.txt").write_text("1\tmetin2_map_a1\r\n64\tmap_n_threeway\r\n")
    (spawns / "special_spawns.txt").write_text(SPECIAL)


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
    ctx = {"login_required": lambda view: view, "rows": fake_rows, "game_text": lambda v: v or ""}
    regen.install(bp, ctx)
    G.install(bp, ctx)
    app.register_blueprint(bp)
    return app


class ParserTests(unittest.TestCase):
    def test_reads_like_the_core(self):
        parsed = G.parse(GROUPS, "g")
        self.assertEqual(parsed["problems"], [])
        groups = G.first_by_vnum(parsed["blocks"])
        self.assertEqual(sorted(groups), [101, 102, 103, 900])
        self.assertEqual(groups[101]["leader"], ("Wildhund", 101))        # the first 101, not "Duplicate"
        self.assertEqual(groups[103]["members"], [("Wolf", 102)] * 3)
        self.assertEqual(groups[900]["members"], [])
        self.assertEqual(G.display_name(groups[101]["name"]), "L01_들개(PAWN)")
        sets = G.first_by_vnum(G.parse(GROUP_GROUPS, "r")["blocks"])
        self.assertEqual(sets[101]["members"], [(101, 1), (102, 5)])
        self.assertEqual(sets[102]["members"], [(103, 1)])                 # no weight: 1

    def test_problems_the_core_would_trip_on(self):
        text = "Group\tTwo words\n{\n\tLeader\tA\t101\n\tVnum\t5\n}\nGroup\tNoVnum\n{\n\tLeader\tA\t101\n}\n" \
               "Group\tNoLeader\n{\n\tVnum\t6\n}\nGroup\tOpen\n{\n\tVnum\t7\n"
        parsed = G.parse(text, "g")
        problems = " | ".join(parsed["problems"])
        self.assertIn("rdzeń gry się zatrzyma", problems)
        self.assertIn("bez numeru", problems)
        self.assertIn("bez lidera", problems)
        self.assertIn("nie jest zamknięta", problems)
        # numbering stops at the first gap, like LoadGroup
        gap = G.parse("Group\tGap\n{\n\tLeader\tA\t101\n\tVnum\t8\n\t1\tA\t101\n\t3\tA\t102\n}\n", "g")
        self.assertEqual(gap["blocks"][0]["members"], [("A", 101)])

    def test_render_round_trip(self):
        groups = G.first_by_vnum(G.parse(GROUPS, "g")["blocks"])
        text = G.render_custom(groups, "g")
        again = G.first_by_vnum(G.parse(text, "g")["blocks"])
        for vnum in groups:
            self.assertTrue(G.same_block(groups[vnum], again[vnum], "g"))
        self.assertIn(f"Group\tL01_{KOREAN}(PAWN)\r\n", text)           # the name's bytes kept
        sets = G.first_by_vnum(G.parse(GROUP_GROUPS, "r")["blocks"])
        self.assertEqual(G.render_block(sets[101], "r"), "Group\ta1_01\r\n{\r\n\tVnum\t101\r\n\t1\t101\t1\r\n"
                                                         "\t2\t102\t5\r\n}\r\n")
        self.assertIsNone(G.render_custom({}, "g"))
        # a name the file can not hold as one word becomes one
        block = dict(groups[102], name='Two "words"')
        self.assertTrue(G.render_block(block, "g").startswith("Group\tTwo_words\r\n"))

    def test_build_block_keeps_the_files_words(self):
        old = G.first_by_vnum(G.parse(GROUPS, "g")["blocks"])[102]
        block = G.build_block("g", 102, old["name"], 103, [(101, 1), (104, 2)], old, lambda mob: f"m{mob}")
        self.assertEqual(block["leader"], ("m103", 103))
        self.assertEqual(block["members"], [("Wildhund", 101), ("m104", 104), ("m104", 104)])
        self.assertEqual(G.counted(block["members"]), [(101, 1), (104, 2)])
        self.assertEqual(G.word_of("Łódź Wilk"), "Lodz_Wilk")

    def test_spawn_entries(self):
        self.assertEqual(G.spawn_entries(REGEN), [("r", 2, 101), ("g", 3, 103), ("g", 1, 103), ("m", 5, 101)])
        # an exception area takes 6 words, an unknown type stops the reading (the core exits on it)
        self.assertEqual(G.spawn_entries("e\t1\t1\t1\t1\t0\r\n" + BOSS + "x\t1\r\n" + BOSS), [("g", 1, 102)])


class PageTests(unittest.TestCase):
    def setUp(self):
        self.sections = list(dbeditor.SECTIONS)
        G._CACHE.clear()
        self.tmp = tempfile.TemporaryDirectory()
        self.spool = Path(self.tmp.name)
        publish(self.spool)
        self.client = make_app(self.spool).test_client()
        with self.client.session_transaction() as session:
            session["dbe_drops_csrf"] = "tok"

    def tearDown(self):
        dbeditor.SECTIONS[:] = self.sections
        self.tmp.cleanup()

    def get(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, url)
        return response.get_data(as_text=True)

    def post(self, url, data):
        data = dict(data, dbe_csrf="tok")
        data.setdefault("rev", G.rev_of(self.spool))
        return self.client.post(url, data=data, follow_redirects=True).get_data(as_text=True)

    def custom(self, kind="g"):
        path = G.custom_path(self.spool, kind)
        return path.read_bytes().decode("latin-1") if path.exists() else None

    def test_usage_per_map(self):
        usage = G.usage_index(self.spool)
        self.assertEqual([(u["folder"], u["file"], u["points"], u["count"]) for u in usage[("g", 103)]],
                         [("metin2_map_a1", "regen", 2, 4), ("metin2_map_a1", "special", 1, 1)])
        self.assertEqual([(u["folder"], u["file"]) for u in usage[("g", 102)]], [("map_n_threeway", "boss")])
        self.assertEqual([(u["folder"], u["file"]) for u in usage[("g", 900)]], [("metin2_map_a1", "npc")])
        self.assertEqual(usage[("r", 101)][0]["points"], 1)
        self.assertNotIn(("g", 101), usage)
        # the panel's regen.txt of a map counts instead of the image's
        (self.spool / "regen" / "custom").mkdir(parents=True)
        (self.spool / "regen" / "custom" / "metin2_map_a1.txt").write_text("g\t1\t1\t1\t1\t0\t0\t60s\t100\t1\t101\r\n")
        usage = G.usage_index(self.spool)
        self.assertIn(("g", 101), usage)
        self.assertEqual([u["file"] for u in usage[("g", 103)]], ["special"])

    def test_list_filters_and_pages(self):
        page = self.get("/db/grupy")
        for text in ("Grupy potworów", "4</b> grup", "2</b> zestawów grup", "L01_들개(PAWN)", "Alfa Wilk",
                     "Nowa grupa", "Zastosuj"):
            self.assertIn(text, page)
        self.assertIn("Alfa Wilk", self.get("/db/grupy?q=alfa"))
        self.assertNotIn("/db/grupy/g/900", self.get("/db/grupy?q=alfa"))
        page = self.get("/db/grupy?mob=104")
        self.assertIn("0 wyników", page)
        page = self.get("/db/grupy?mob=101")                      # 101, 102 and the set of them
        self.assertIn("3 wyników", page)
        self.assertIn("/db/grupy/r/101", page)
        self.assertIn("2 wyników", self.get("/db/grupy?lvl_od=4&lvl_do=9"))   # group 103 and set 102
        self.assertIn("1 wynik", self.get("/db/grupy?mapa=map_n_threeway&typ=g"))
        page = self.get("/db/grupy?uzycie=nieuzywane")              # 101 stands through its set
        self.assertIn("/db/grupy/r/102", page)
        self.assertNotIn("/db/grupy/g/101", page)
        order = self.get("/db/grupy?typ=g&sort=spawny&kier=malejaco")
        self.assertLess(order.index("/db/grupy/g/103"), order.index("/db/grupy/g/101"))
        old = G.PAGE_SIZE
        G.PAGE_SIZE = 2
        try:
            page = self.get("/db/grupy?strona=2")
            self.assertIn("strona 2 z 3", page)
            self.assertIn("strona=3", page)
            self.assertIn("strona 3 z 3", self.get("/db/grupy?strona=99"))
        finally:
            G.PAGE_SIZE = old

    def test_detail_pages(self):
        page = self.get("/db/grupy/g/103")
        for text in ("Grupa 103", "Alfa Wilk", "Wilk", "/db/regen/metin2_map_a1", "bossowie czasowi",
                     "W zestawach grup", "Zestaw 102", "Zmień skład", 'name="leader" value="103"'):
            self.assertIn(text, page)
        page = self.get("/db/grupy/r/101")
        for text in ("Zestaw grup 101", "50,0%", "nie korzysta", "Dziki Pies"):
            self.assertIn(text, page)
        self.assertIn("Nie ma grupy", self.client.get("/db/grupy/g/7777", follow_redirects=True).get_data(as_text=True))
        self.assertEqual(self.client.get("/db/grupy/x/1").status_code, 404)
        found = self.client.get("/db/grupy/api/szukaj?q=wilk").get_json()
        self.assertEqual([m["vnum"] for m in found], [102, 103, 104])
        self.assertEqual([m["vnum"] for m in self.client.get("/db/grupy/api/szukaj?typ=g&q=103").get_json()], [103])
        self.assertIn(b"Vnum\t103", self.client.get("/db/grupy/plik/g").data)

    def test_edit_history_undo_revert(self):
        form = {"kind": "g", "vnum": "102", "action": "save", "leader": "102", "name": "Wolves",
                "m_vnum": ["101", "104", ""], "m_count": ["1", "2", ""], "note": "test"}
        page = self.post("/db/grupy/zapisz", form)
        self.assertIn("Zapisano", page)
        custom = self.custom()
        self.assertIn("Group\tWolves\r\n{\r\n\tLeader\tWolf\t102\r\n\tVnum\t102\r\n\t1\tWildhund\t101\r\n"
                      "\t2\tNiebieski_Wilk\t104\r\n\t3\tNiebieski_Wilk\t104\r\n}\r\n", custom)
        self.assertEqual([p["key"] for p in df.pending_changes(self.spool)], ["mobgroup"])
        self.assertIn("zmieniona w panelu", self.get("/db/grupy/g/102"))
        # the form of an older state is refused
        self.assertIn("zmieniły się w międzyczasie", self.post("/db/grupy/zapisz", dict(form, rev="old")))
        # the same again: nothing to do; back to the image's composition: the panel's group goes away
        self.assertIn("Nic się nie zmieniło", self.post("/db/grupy/zapisz", form))
        self.post("/db/grupy/zapisz", dict(form, m_vnum=["101", "101"], m_count=["1", "1"]))
        self.assertIsNone(self.custom())
        # an unknown monster: nothing saved, the form comes back with the values
        page = self.post("/db/grupy/zapisz", dict(form, m_vnum=["99999"], m_count=["1"]))
        self.assertIn("Nie ma takich potworów", page)
        self.assertIn('value="99999"', page)
        self.assertIsNone(self.custom())
        # history (newest first) and undo of one group
        self.post("/db/grupy/zapisz", form)
        history = G.read_history(self.spool)
        self.assertEqual(len(history), 3)
        self.assertIn("zmiana składu", history[0]["what"])
        self.post("/db/grupy/cofnij", {"entry": history[0]["id"]})
        self.assertIsNone(self.custom())
        self.assertIn("cofnięto", G.read_history(self.spool)[0]["what"])
        # an undo of a change made over later: refused (the first save; the group is the image's now)
        self.assertIn("zmieniono później", self.post("/db/grupy/cofnij", {"entry": history[2]["id"]}))
        # the step before it ("back to the image") can be undone: the first save's group comes back
        self.post("/db/grupy/cofnij", {"entry": history[1]["id"]})
        self.assertIn("\t3\tNiebieski_Wilk\t104", self.custom())
        self.post("/db/grupy/cofnij", {"entry": G.read_history(self.spool)[0]["id"]})
        self.assertIsNone(self.custom())
        # revert to the image
        self.post("/db/grupy/zapisz", form)
        self.post("/db/grupy/zapisz", {"kind": "g", "vnum": "102", "action": "revert"})
        self.assertIsNone(self.custom())
        # a server update changes the image's 102 under the panel's version: the page says so
        self.post("/db/grupy/zapisz", form)
        self.assertNotIn("Aktualizacja serwera zmieniła", self.get("/db/grupy/g/102"))
        (self.spool / "groups" / "group.base.txt").write_bytes(
            GROUPS.replace(
                "Group\tWolves\n{\n\tLeader\tWolf\t102\n\tVnum\t102\n\t1\tWildhund\t101\n",
                "Group\tWolves\n{\n\tLeader\tWolf\t102\n\tVnum\t102\n\t1\tWolf\t102\n").encode("latin-1"))
        os.utime(self.spool / "groups" / "group.base.txt", (1, 1))
        self.assertIn("Aktualizacja serwera zmieniła", self.get("/db/grupy/g/102"))
        self.assertIn("obraz gry się zmienił", self.get("/db/grupy?zmienione=1"))
        self.post("/db/grupy/zapisz", {"kind": "g", "vnum": "102", "action": "revert"})
        self.assertIsNone(self.custom())
        # a whole-file backup restore
        backups = df.list_backups(self.spool, ["mobgroup"])
        self.post("/db/grupy/cofnij", {"backup": backups[0]["name"]})
        self.assertIn("\t3\tNiebieski_Wilk\t104", self.custom())

    def test_new_group_set_and_delete(self):
        self.assertIn('name="vnum" value="901"', self.get("/db/grupy/g/nowa"))
        self.assertIn('value="102"', self.get("/db/grupy/g/nowa?kopia=103"))
        form = {"kind": "g", "vnum": "5000", "action": "new", "leader": "104", "name": "MT2009_niebieskie",
                "m_vnum": ["102"], "m_count": ["2"]}
        self.assertIn("jedno słowo", self.post("/db/grupy/zapisz", dict(form, name="dwa słowa")))
        self.assertIn("już zajęty", self.post("/db/grupy/zapisz", dict(form, vnum="103")))
        self.assertIn("Zapisano", self.post("/db/grupy/zapisz", form))
        self.assertIn("nowa w panelu", self.get("/db/grupy?zmienione=1"))
        # a set with the new group (the panel's group is known before a restart)
        rset = {"kind": "r", "vnum": "300", "action": "new", "name": "", "m_vnum": ["5000", "103"],
                "m_count": ["", "3"]}
        self.assertIn("Nie ma takich grup", self.post("/db/grupy/zapisz", dict(rset, m_vnum=["6000"])))
        self.assertIn("Zapisano", self.post("/db/grupy/zapisz", rset))
        self.assertIn("Group\tMT2009_grupa_300\r\n{\r\n\tVnum\t300\r\n\t1\t5000\t1\r\n\t2\t103\t3\r\n}",
                      self.custom("r"))
        # in a set: may not go; out of the set: may
        page = self.post("/db/grupy/zapisz", {"kind": "g", "vnum": "5000", "action": "delete"})
        self.assertIn("zestawach grup 300", page)
        self.post("/db/grupy/zapisz", {"kind": "r", "vnum": "300", "action": "delete"})
        self.assertIsNone(self.custom("r"))
        self.post("/db/grupy/zapisz", {"kind": "g", "vnum": "5000", "action": "delete"})
        self.assertIsNone(self.custom("g"))
        # an image's group can not be deleted
        self.assertIn("Usunąć można tylko", self.post("/db/grupy/zapisz", {"kind": "g", "vnum": "101",
                                                                          "action": "delete"}))

    def test_regen_page_sees_the_panels_groups(self):
        form = {"kind": "g", "vnum": "5000", "action": "new", "leader": "104", "name": "", "m_vnum": [], "m_count": []}
        self.post("/db/grupy/zapisz", form)
        found = self.client.get("/db/regen/api/search?q=5000").get_json()
        self.assertIn(5000, [g["vnum"] for g in found["groups"]])
        page = self.get("/db/regen/metin2_map_a1")
        self.assertIn("/db/grupy/g/103", page)                          # the summary links the group

    def test_config_adapter(self):
        self.post("/db/grupy/zapisz", {"kind": "g", "vnum": "102", "action": "save", "leader": "104",
                                       "name": "Wolves", "m_vnum": ["101"], "m_count": ["1"]})
        adapter = config.FILE_ADAPTERS["groups"]
        self.assertTrue(adapter.available())
        self.assertEqual(adapter.keys(self.spool), ["mobgroup"])
        data = adapter.read(self.spool, "mobgroup")
        self.assertTrue(adapter.effective("mobgroup", data))
        self.assertEqual(adapter.base(self.spool, "mobgroup"), GROUPS.encode("latin-1"))
        errors, warnings = adapter.check(self.spool, "mobgroup", data, lambda kind, v: set(v))
        self.assertEqual((errors, warnings), ([], []))
        adapter.write(self.spool, "mobgroup", None, "import")
        self.assertIsNone(self.custom())
        adapter.write(self.spool, "mobgroup", data, "import")
        self.assertEqual(self.custom().encode("latin-1"), data)
        self.assertIn("import", G.read_history(self.spool)[0]["what"])
        errors, _w = adapter.check(self.spool, "mobgroupgroup", b"Group\tx y\r\n{\r\n\tVnum\t1\r\n\t1\t5\r\n}\r\n",
                                   lambda kind, v: set(v))
        self.assertTrue(errors)


@unittest.skipUnless(shutil.which("sh") and shutil.which("awk") and M2_GROUPS.is_file(), "no sh/awk or m2-groups")
class GameSideTests(unittest.TestCase):
    def run_m2(self, root, *commands):
        env = dict(os.environ, M2_SHARE_DIR=str(root / "share"), M2_VAR_DIR=str(root / "var"),
                   M2_RATES_SPOOL=str(root / "spool"), PATH="/usr/bin:/bin")
        for command in commands:
            result = subprocess.run(["sh", str(M2_GROUPS), command], env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_m2_groups_merges_the_panels_groups(self):
        G.register_file()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            locale = root / "share" / "locale" / "poland"
            (locale / "map" / "metin2_map_a1").mkdir(parents=True)
            (locale / "map" / "metin2_map_a1" / "npc.txt").write_text(NPC)
            (locale / "group.txt").write_bytes(GROUPS.encode("latin-1"))
            (locale / "group_group.txt").write_bytes(GROUP_GROUPS.encode("latin-1"))
            spool = root / "spool"
            self.run_m2(root, "prepare", "apply")
            self.assertEqual((spool / "groups" / "group.base.txt").read_bytes(), GROUPS.encode("latin-1"))
            self.assertEqual((spool / "groups" / "base" / "maps" / "metin2_map_a1" / "npc.txt").read_bytes(),
                             (locale / "map" / "metin2_map_a1" / "npc.txt").read_bytes())
            self.assertEqual(df.live_state(spool, "mobgroup")["kind"], "ok")
            # the panel changes 102 and adds 5000 and a set with it
            st = G.state(spool)
            G.save_group(spool, "g", 102, G.build_block("g", 102, "Wolves", 104, [(101, 3)], st["g"]["base"][102]),
                         "test")
            G.save_group(spool, "g", 5000, G.build_block("g", 5000, "New", 104, [(102, 1)]), "test")
            G.save_group(spool, "r", 300, G.build_block("r", 300, "Set", None, [(5000, 1), (101, 2)]), "test")
            self.assertEqual(len(df.pending_changes(spool)), 2)
            self.run_m2(root, "apply")
            live = (locale / "group.txt").read_bytes().decode("latin-1")
            self.assertEqual(live.count("\tVnum\t102"), 1)
            self.assertNotIn("Group\tWolves\n{\n\tLeader\tWolf\t102", live)  # the image's 102 is out
            self.assertIn("Group\tAlpha\n", live)                          # the rest stays as it was
            self.assertIn("// a comment between groups\n", live)
            self.assertNotIn("\r", live)                                   # the image's line ends (LF)
            parsed = G.first_by_vnum(G.parse(live, "g")["blocks"])
            self.assertEqual(parsed[102]["leader"][1], 104)
            self.assertEqual(parsed[5000]["members"], [("mob", 102)])
            live_r = (locale / "group_group.txt").read_bytes().decode("latin-1")
            self.assertIn("\tVnum\t300\r\n", live_r)                       # CRLF like the image's
            self.assertEqual(df.pending_changes(spool), [])
            self.assertEqual(df.live_state(spool, "mobgroupgroup")["kind"], "ok")
            # broken files are not used: the image's file goes back
            good = G.custom_path(spool, "g").read_bytes()
            for bad, why in ((b"Group\ttwo words\r\n{\r\n\tLeader\tA\t101\r\n\tVnum\t7\r\n}\r\n", "exactly two"),
                             (b"Group\tx\r\n{\r\n\tVnum\t7\r\n\t1\tA\t101\r\n}\r\n", "without Leader"),
                             (b"Group\tx\r\n{\r\n\tLeader\tA\t101\r\n\tVnum\t7\r\n\t2\tA\t101\r\n}\r\n", "member 2"),
                             (b"Group\tx\r\n{\r\n\tLeader\tA\t101\r\n\tVnum\t7\r\n", "not closed"),
                             (b"// a comment\r\n", "expected Group"),
                             (b"Group\tx\r\n{\r\n\tLeader\tA\t101\r\n\tVnum\t7\r\n\t1\r\n}\r\n", "without a value")):
                G.custom_path(spool, "g").write_bytes(bad)
                self.run_m2(root, "apply")
                self.assertEqual((locale / "group.txt").read_bytes(), GROUPS.encode("latin-1"), why)
                state = df.live_state(spool, "mobgroup")
                self.assertEqual(state["kind"], "error", why)
                self.assertIn(why, state["text"])
                # the set needs the panel's group 5000, which the image's file has not
                self.assertIn("no such group (group.txt): 5000", df.live_state(spool, "mobgroupgroup")["text"])
            G.custom_path(spool, "g").write_bytes(good)
            G.custom_path(spool, "g").unlink()
            G.custom_path(spool, "r").unlink()
            self.run_m2(root, "apply")
            self.assertEqual((locale / "group.txt").read_bytes(), GROUPS.encode("latin-1"))
            self.assertEqual((locale / "group_group.txt").read_bytes(), GROUP_GROUPS.encode("latin-1"))


if __name__ == "__main__":
    unittest.main()
