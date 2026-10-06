"""MT2009_PLUS_DB_EDITOR_QUESTS_V1: python3 -m unittest test_dbeditor_quests

The database editor's "Questy" part (dbeditor/quests.py): the reward parser
on real quest files (the Biologist snapshot, the repository's game/quest and -
when M2_QUEST_TREE names it - the whole quest tree of a server), the panel's
file and its checks, the pages through Flask's test client on a temporary
spool, the config export / import adapter, and the game side
(bin/m2-quests) under sh when the game folder is next to the panel (or
M2_GAME_BIN names it)."""
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
from dbeditor import quests as qs

HERE = Path(__file__).resolve().parent
GAME_BIN = Path(os.environ.get("M2_GAME_BIN") or HERE.parent / "game" / "bin")
M2_QUESTS = GAME_BIN / "m2-quests"
REPO_QUESTS = HERE.parent / "game" / "quest"
QUEST_TREE = os.environ.get("M2_QUEST_TREE")
SOURCES = qs.snapshot_sources()


def make_app(spool, rows=None):
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
    qs.install(bp, {"login_required": lambda view: view, "rows": rows, "game_text": lambda v: v or ""})
    app.register_blueprint(bp)
    return app


def groups_of(name):
    return qs.reward_groups(qs.parse_quest(SOURCES[name]))


class ParserTests(unittest.TestCase):
    def test_biologist_missions(self):
        self.assertEqual(sorted(SOURCES), [q for q, _l, _n in qs.BIOLOGIST])
        P = qs.point_numbers()
        expected = {   # quest -> (bonuses (point, value), reward items)
            "collect_quest_lv30": ([(P["POINT_MOV_SPEED"], 10)], [50109]),
            "collect_quest_lv40": ([(P["POINT_ATT_SPEED"], 5)], [50110]),
            "collect_quest_lv50": ([(P["POINT_DEF_GRADE_BONUS"], 60)], [50111]),
            "collect_quest_lv60": ([(P["POINT_ATT_GRADE_BONUS"], 50)], [50112]),
            "collect_quest_lv70": ([(P["POINT_MOV_SPEED"], 11), (P["POINT_DEF_BONUS"], 10)], [50113]),
            "collect_quest_lv80": ([(P["POINT_ATT_SPEED"], 6), (P["POINT_ATT_BONUS"], 10)], [50114]),
            "collect_quest_lv85": ([(P["POINT_RESIST_HUMAN"], 10)], [50115]),
            "collect_quest_lv90": ([(P["POINT_ATTBONUS_HUMAN"], 8)], [50114]),
            "collect_quest_lv92": ([], []),
        }
        self.assertEqual((P["POINT_MOV_SPEED"], P["POINT_ATT_SPEED"], P["POINT_ATTBONUS_HUMAN"]), (19, 17, 43))
        for name, (bonuses, items) in expected.items():
            q = qs.parse_quest(SOURCES[name])
            self.assertEqual(q["name"], name)
            main = [g for g in qs.reward_groups(q) if not g["drop"]]
            self.assertEqual([(g["point"], g["value"]) for g in main if g["kind"] == "bonus"], bonuses, name)
            self.assertEqual([g["vnum"] for g in main if g["kind"] == "item"], items, name)
            for g in main:
                self.assertTrue(g["editable"], (name, g["key"]))
                self.assertEqual(g["states"], ["__reward"], (name, g["key"]))
                self.assertFalse(g["conditional"], (name, g["key"]))
            if bonuses:
                self.assertIn("__complete", q["states_set"])
                self.assertEqual(qs.default_anchor(q), "state:__complete")
        # the quest items the missions collect: drops, conditional, random
        drops = [g for g in groups_of("collect_quest_lv30") if g["drop"]]
        self.assertEqual(sorted(g["vnum"] for g in drops), [30006, 30220])
        self.assertTrue(all(g["conditional"] and g["random"] for g in drops))
        self.assertEqual(qs.point_label(19), "Szybkość ruchu (%)")
        self.assertEqual(qs.point_label(6), "Maks. PŻ")

    def test_calls_and_values(self):
        text = "\n".join([
            "quest demo begin",
            "  state start begin",
            "    when 20011.chat.\"x\" begin",
            "      pc.change_money(-5000) -- a payment",
            "      pc.change_money(25000)",
            "      pc.give_exp2(pc.get_level() * 100)",
            "      pc.give_exp(\"demo\", 4000)",
            "      pc.give_exp_perc(\"demo\", 30, 5)",
            "      if pc.level > 10 then",
            "        pc.give_item2(\"27001\", 20)",
            "      else",
            "        pc.give_item(\"demo\", 27002, 5)",
            "      end",
            "      give_reward(\"demo_reward\")",
            "      pc.give_item2_select(19)",
            "      say_reward(\"Nagroda: 25 000 yang\")",
            "      set_state(\"__complete\")",
            "    end",
            "  end",
            "end"])
        q = qs.parse_quest(text)
        kinds = [(r["kind"], r.get("amount"), r.get("vnum"), r["conditional"]) for r in q["rewards"]]
        self.assertEqual(kinds, [("gold", 25000, None, False), ("exp", None, None, False), ("exp", 4000, None, False),
                                 ("exp", None, None, False), ("item", None, 27001, True), ("item", None, 27002, True),
                                 ("table", None, None, False), ("special", None, None, False)])
        self.assertEqual(q["rewards"][4]["count"], 20)
        self.assertEqual(q["rewards"][5]["count"], 5)
        self.assertEqual(q["rewards"][6]["table_key"], "demo_reward")
        self.assertEqual(q["states_set"], ["__complete"])
        self.assertEqual(q["say_rewards"], [("start", '"Nagroda: 25 000 yang"')])
        anchors = dict(qs.anchors(q))
        self.assertIn("state:__complete", anchors)
        self.assertIn("gold:*", anchors)
        self.assertIn("item:27001", anchors)
        self.assertEqual(qs.literal_int('"30006"'), 30006)
        self.assertIsNone(qs.literal_int("pc.level"))
        self.assertEqual(qs.split_args('a, f(b, c), "d,e"'), ["a", "f(b, c)", '"d,e"'])
        self.assertEqual(qs.strip_comment('x("--") -- y'), 'x("--") ')

    @unittest.skipUnless(REPO_QUESTS.is_dir(), "no game/quest next to the panel")
    def test_repository_quests_parse(self):
        files = sorted(REPO_QUESTS.glob("*.quest"))
        self.assertGreater(len(files), 40)
        names = {}
        for path in files:
            q = qs.parse_quest(path.read_bytes())
            if q["name"]:                  # a superseded file is all comments
                names[q["name"]] = q
        self.assertGreater(len(names), 40)
        self.assertIn("web_admin", names)
        lv85 = qs.reward_groups(names["collect_quest_lv85"])
        self.assertIn(50115, [g["vnum"] for g in lv85 if g["kind"] == "item" and not g["drop"]])

    @unittest.skipUnless(QUEST_TREE and Path(QUEST_TREE).is_dir(), "M2_QUEST_TREE not set")
    def test_whole_quest_tree(self):
        total, rewards, named = 0, 0, 0
        for path in Path(QUEST_TREE).rglob("*.quest"):
            if "_unused" in path.parts:
                continue
            q = qs.parse_quest(path.read_bytes())
            total += 1
            named += q["name"] is not None
            rewards += len(q["rewards"])
            qs.reward_groups(q)
            qs.anchors(q)
        self.assertGreater(total, 150)
        self.assertGreater(named, total * 0.95)
        self.assertGreater(rewards, 300)


class FileTests(unittest.TestCase):
    def model(self):
        m = {"off": {"event_easter"}, "rules": {}, "problems": []}
        r = m["rules"]["collect_quest_lv30"] = qs.empty_rules()
        r["bonus"][(19, 10)] = (6, 2000)
        r["items"][50109] = (27001, 10)
        r["gold"]["*"] = ("mul", 1.5)
        r["exp"][4000] = ("set", 100000)
        r["extras"] += [("state:__complete", "gold", 10000000, 0), ("state:__complete", "item", 27002, 10),
                        ("bonus:19:10", "bonus", 1, 500)]
        return m

    def test_round_trip_and_checks(self):
        data = qs.render_custom(self.model(), {"collect_quest_lv30": "Biolog – Zęby Orka (poz. 30)"})
        self.assertIn(b"off\tevent_easter\n", data)
        self.assertIn(b"bonus\tcollect_quest_lv30\t19\t10\t6\t2000\n", data)
        self.assertIn(b"gold\tcollect_quest_lv30\t*\tmul\t1.5\n", data)
        self.assertIn(b"extra\tcollect_quest_lv30\tstate:__complete\tgold\t10000000\t0\n", data)
        self.assertTrue(data.decode("ascii"))          # comments are ASCII (Polish letters -> ?)
        back = qs.parse_custom(data)
        self.assertEqual(back["off"], {"event_easter"})
        self.assertEqual(back["rules"], self.model()["rules"])
        self.assertEqual(qs.render_custom(back, {"collect_quest_lv30": "Biolog – Zęby Orka (poz. 30)"}), data)
        self.assertEqual(qs.validate_custom(data), [])
        self.assertIsNone(qs.render_custom({"off": set(), "rules": {}}))
        bad = self.model()
        bad["off"].add("web_admin")
        bad["rules"]["collect_quest_lv30"]["items"][50109] = (27001, 20000)
        bad["rules"]["collect_quest_lv30"]["extras"].append(("nowhere", "gold", 5, 0))
        problems = qs.validate_model(bad)
        self.assertEqual(len(problems), 3, problems)
        self.assertTrue(qs.parse_custom(b"item\tx y\t1\n")["problems"])


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

    def sha(self):
        return qs.sha(df.custom_path(self.spool, qs.KEY).read_bytes() if df.custom_path(self.spool, qs.KEY).exists() else b"")

    def post(self, url, data):
        return self.client.post(url, data=dict(data, dbe_csrf="tok", sha=self.sha()), follow_redirects=True) \
            .get_data(as_text=True)

    def publish_catalog(self):
        folder = self.spool / "quests"
        (folder / "src").mkdir(parents=True)
        lines = []
        for name, text in SOURCES.items():
            (folder / "src" / f"{name}.quest").write_bytes(text.encode("cp1250"))
            lines.append(f"{name}\ton\tquest/collect/{name}.quest")
        lines += ["web_admin\ton\tweb_admin.quest", "blacksmith\ton\tquest/npc/blacksmith.quest",
                  "event_easter\ton\tquest/events/event_easter.quest"]
        (folder / "catalog.txt").write_text("\n".join(lines) + "\n")
        (folder / "translate.lua").write_bytes('gameforge.collect_quest_lv30._10_sendLetter = "Prośba Biologa "\n'
                                               .encode("cp1250"))

    def test_biologist_example(self):
        """The owner's example: Zęby Orka -> Max PŻ instead of the movement speed,
        + 10 000 000 yang, + 10x an item."""
        page = self.client.get("/db/questy").get_data(as_text=True)
        self.assertIn("Biolog – Zęby Orka (poz. 30)", page)
        self.assertIn("kopii panelu", page)                   # no catalog yet: the snapshot
        page = self.client.get("/db/questy/biolog").get_data(as_text=True)
        for text in ("Zęby Orka", "Szybkość ruchu (%) 10", "Notatka Przywódcy", "Klejnoty", "Dodatkowy yang",
                     "nie jest możliwe"):
            self.assertIn(text, page)
        page = self.post("/db/questy/biolog", {
            "collect_quest_lv30_b_19_10_point": "6", "collect_quest_lv30_b_19_10_val": "2000",
            "collect_quest_lv30_gold": "10 000 000", "collect_quest_lv30_x0_item": "27001 – Czerwona mikstura",
            "collect_quest_lv30_x0_count": "10",
            "collect_quest_lv40_b_17_5_point": "17", "collect_quest_lv40_b_17_5_val": "5"})   # unchanged
        self.assertIn("Zapisano nagrody Biologa (1 misji)", page)
        model = qs.parse_custom(df.custom_path(self.spool, qs.KEY).read_bytes())
        self.assertEqual(model["rules"], {"collect_quest_lv30": {
            "items": {}, "gold": {}, "exp": {}, "bonus": {(19, 10): (6, 2000)},
            "extras": [("state:__complete", "gold", 10000000, 0), ("state:__complete", "item", 27001, 10)]}})
        self.assertEqual([p["key"] for p in df.pending_changes(self.spool)], ["quests"])
        page = self.client.get("/db/questy/biolog").get_data(as_text=True)
        self.assertIn('value="10000000"', page)
        self.assertIn("zmieniony", page)
        # a bad value saves nothing
        page = self.post("/db/questy/biolog", {"collect_quest_lv50_gold": "abc"})
        self.assertIn("Nic nie zapisano", page)
        # undo: back to no file
        self.post("/db/questy/kopie", {"action": "undo"})
        self.assertFalse(df.custom_path(self.spool, qs.KEY).exists())

    def test_quest_page_switch_and_config(self):
        self.publish_catalog()
        page = self.client.get("/db/questy").get_data(as_text=True)
        self.assertIn("Biolog – Zęby Orka (poz. 30)", page)
        self.assertIn("web_admin", page)
        self.assertNotIn("kopii panelu", page)
        page = self.client.get("/db/questy/q/collect_quest_lv30").get_data(as_text=True)
        for text in ("Nagrody z kodu questa", "Szybkość ruchu (%)", "50109", "drop questowy", "Dodatkowe nagrody",
                     "zakończenie questa", "Wyłącz quest"):
            self.assertIn(text, page)
        self.assertEqual(self.client.get("/db/questy/q/nope").status_code, 404)
        page = self.post("/db/questy/q/collect_quest_lv30", {
            "i_50109_new": "27003", "i_50109_count": "3", "b_19_10_point": "", "b_19_10_val": "",
            "g_all_mode": "mul", "g_all_val": "2,5",
            "x0_anchor": "state:__complete", "x0_kind": "exp", "x0_num": "500000",
            "x1_anchor": "item:50109", "x1_kind": "bonus", "x1_point": "6", "x1_num": "300",
            "x2_anchor": "state:__complete", "x2_kind": "item", "x2_item": "", "x2_num": ""})
        self.assertIn("Zapisano nagrody questa", page)
        rules = qs.parse_custom(df.custom_path(self.spool, qs.KEY).read_bytes())["rules"]["collect_quest_lv30"]
        self.assertEqual(rules["items"], {50109: (27003, 3)})
        self.assertEqual(rules["gold"], {"*": ("mul", 2.5)})
        self.assertEqual(rules["bonus"], {})
        self.assertEqual(rules["extras"], [("state:__complete", "exp", 500000, 0), ("item:50109", "bonus", 6, 300)])
        # an anchor the quest does not have is refused
        page = self.post("/db/questy/q/collect_quest_lv30", {"x0_anchor": "state:nowhere", "x0_kind": "gold",
                                                              "x0_num": "5"})
        self.assertIn("Nic nie zapisano", page)
        # switches: protected never, critical with a confirmation, a plain one at once
        page = self.post("/db/questy/przelacz", {"name": "web_admin", "on": "0"})
        self.assertIn("nie można wyłączyć", page)
        page = self.post("/db/questy/przelacz", {"name": "blacksmith", "on": "0"})
        self.assertIn("krytyczny", page)
        page = self.post("/db/questy/przelacz", {"name": "blacksmith", "on": "0", "potwierdz": "1"})
        self.assertIn("WYŁĄCZONY", page)
        self.post("/db/questy/przelacz", {"name": "event_easter", "on": "0"})
        model = qs.parse_custom(df.custom_path(self.spool, qs.KEY).read_bytes())
        self.assertEqual(model["off"], {"blacksmith", "event_easter"})
        self.post("/db/questy/przelacz", {"name": "blacksmith", "on": "1"})
        self.assertEqual(qs.parse_custom(df.custom_path(self.spool, qs.KEY).read_bytes())["off"], {"event_easter"})
        page = self.client.get("/db/questy?tylko=wylaczone").get_data(as_text=True)
        self.assertIn("event_easter", page)
        self.assertNotIn("collect_quest_lv40", page)
        # config export / import adapter
        adapter = config.FILE_ADAPTERS["quests"]
        self.assertIn(("quests", qs.TITLE), config.FILE_PARTS)
        self.assertEqual(adapter.keys(self.spool), ["quests"])
        data = adapter.read(self.spool, "quests")
        self.assertTrue(adapter.effective("quests", data))
        self.assertEqual(adapter.check(self.spool, "quests", data, lambda k, v: set(v)), ([], []))
        content = {"quests": {"records": [], "files": [{"key": "quests", "data": data, "title": adapter.title("quests")}]}}
        text = config.render_text(content)
        self.assertIn("[quests]", text)
        self.assertEqual(config.parse(text)["parts"]["quests"]["files"][0]["data"], data)
        # reset of one quest's rules
        self.post("/db/questy/q/collect_quest_lv30", {"action": "reset"})
        self.assertNotIn("collect_quest_lv30", qs.parse_custom(df.custom_path(self.spool, qs.KEY).read_bytes())["rules"])


class RewardTableTests(unittest.TestCase):
    """give_reward("key"): the world.quest_reward_proto row's exp, yang and items as rewards of their own."""

    def rows(self, sql, params=()):
        if "quest_reward_proto" in sql:
            return [{"quest_name": "main_quest_lv2", "exp": 250, "gold": 2500, "items": "27001,20,s10989,1",
                     "warrior_items": "", "assassin_items": "", "sura_items": "", "shaman_items": ""}]
        if "item_proto" in sql:
            return [{"vnum": 27001, "locale_name": "Czerwona mikstura (M)", "type": 1}]
        return []

    def test_table_rewards_are_editable(self):
        sections = list(dbeditor.SECTIONS)
        with tempfile.TemporaryDirectory() as tmp:
            spool = Path(tmp)
            folder = spool / "quests"
            (folder / "src").mkdir(parents=True)
            (folder / "src" / "main_quest_lv2.quest").write_text(
                'quest main_quest_lv2 begin\n state start begin\n  when 20011.chat."x" begin\n'
                '   give_reward("main_quest_lv2")\n   set_state("__COMPLETE__")\n  end\n end\nend\n')
            (folder / "catalog.txt").write_text("main_quest_lv2\ton\tquest/story/main_quest_lv2.quest\n")
            client = make_app(spool, self.rows).test_client()
            with client.session_transaction() as session:
                session["dbe_drops_csrf"] = "tok"
            page = client.get("/db/questy/q/main_quest_lv2").get_data(as_text=True)
            for text in ("give_reward", "2 500", "Czerwona mikstura (M)", "z tabeli", "g_2500_mode", "i_27001_new",
                         "e_250_mode", "przy nagrodzie: przedmiot 27001 (z tabeli)"):
                self.assertIn(text, page)
            self.assertNotIn("i_10989_new", page)                  # a special-group draw stays as it is
            page = client.post("/db/questy/q/main_quest_lv2", data={
                "dbe_csrf": "tok", "sha": qs.sha(b""), "g_2500_mode": "set", "g_2500_val": "50000",
                "i_27001_new": "27002", "i_27001_count": "", "x0_anchor": "item:27001", "x0_kind": "gold",
                "x0_num": "1000"}, follow_redirects=True).get_data(as_text=True)
            self.assertIn("Zapisano nagrody questa", page)
            rules = qs.parse_custom(df.custom_path(spool, qs.KEY).read_bytes())["rules"]["main_quest_lv2"]
            self.assertEqual(rules["gold"], {2500: ("set", 50000)})
            self.assertEqual(rules["items"], {27001: (27002, 0)})
            self.assertEqual(rules["extras"], [("item:27001", "gold", 1000, 0)])
        dbeditor.SECTIONS[:] = sections


@unittest.skipUnless(shutil.which("sh") and shutil.which("awk") and M2_QUESTS.is_file(), "no sh/awk or m2-quests")
class GameSideTests(unittest.TestCase):
    def run_m2(self, root, *commands):
        env = dict(os.environ, M2_SHARE_DIR=str(root / "share"), M2_VAR_DIR=str(root / "var"),
                   M2_RATES_SPOOL=str(root / "spool"), PATH="/usr/bin:/bin")
        for command in commands:
            subprocess.run(["sh", str(M2_QUESTS), command], env=env, check=True, capture_output=True)

    def test_m2_quests_switches_and_rules(self):
        qs.register_file()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            quest = root / "share" / "locale" / "poland" / "quest"
            obj = quest / "object"
            for rel in ("state/collect_quest_lv30", "state/collect_quest_lv40", "state/web_admin",
                        "20018/chat/collect_quest_lv30.__reward.0.script", "601/kill/collect_quest_lv30.go_to_disciple",
                        "notarget/letter/collect_quest_lv30.information", "notarget/login/web_admin.start",
                        "notarget/letter/collect_quest_lv40.information"):
                (obj / rel).parent.mkdir(parents=True, exist_ok=True)
                (obj / rel).write_text("-- " + rel)
            (quest / "quest" / "collect").mkdir(parents=True)
            for name in ("collect_quest_lv30", "collect_quest_lv40"):
                (quest / "quest" / "collect" / f"{name}.quest").write_bytes(SOURCES[name].encode("cp1250"))
            (quest / "web_admin.quest").write_text("quest web_admin begin\nend\n")
            (root / "share" / "locale" / "poland" / "translate.lua").write_text("gameforge = {}\n")
            spool = root / "spool"
            (spool / "quests").mkdir(parents=True)
            model = FileTests().model()
            model["off"] = {"collect_quest_lv30", "web_admin"}
            df.write_custom(spool, qs.KEY, qs.render_custom(model))
            self.run_m2(root, "prepare", "apply")
            off = quest / "object.off"
            self.assertTrue((off / "20018/chat/collect_quest_lv30.__reward.0.script").is_file())
            self.assertFalse((obj / "601/kill/collect_quest_lv30.go_to_disciple").exists())
            self.assertTrue((obj / "state/collect_quest_lv30").is_file())          # the state table stays
            self.assertTrue((obj / "notarget/login/web_admin.start").is_file())     # protected
            rules = (quest / "reward_overrides.txt").read_text()
            self.assertIn("bonus\tcollect_quest_lv30\t19\t10\t6\t2000\n", rules)
            self.assertIn("extra\tcollect_quest_lv30\tbonus:19:10\tbonus\t1\t500\n", rules)
            self.assertNotIn("off\t", rules)
            catalog = (spool / "quests" / "catalog.txt").read_text()
            self.assertIn("collect_quest_lv30\toff\tquest/collect/collect_quest_lv30.quest\n", catalog)
            self.assertIn("web_admin\ton\tweb_admin.quest\n", catalog)
            self.assertTrue((spool / "quests" / "src" / "collect_quest_lv40.quest").is_file())
            self.assertEqual(df.live_state(spool, qs.KEY)["kind"], "ok")
            self.assertEqual(df.pending_changes(spool), [])
            self.assertEqual([r["name"] for r in qs.catalog(spool)],
                             ["collect_quest_lv30", "collect_quest_lv40", "web_admin"])
            # switched on again: the handlers come back
            model["off"] = set()
            df.write_custom(spool, qs.KEY, qs.render_custom(model))
            self.run_m2(root, "apply")
            self.assertTrue((obj / "601/kill/collect_quest_lv30.go_to_disciple").is_file())
            self.assertFalse(any(p.is_file() for p in off.rglob("*")))
            # a broken file: not used, every quest on, no rules
            df.write_custom(spool, qs.KEY, b"off\tcollect_quest_lv30\nitem\tx y\t1\n")
            self.run_m2(root, "apply")
            self.assertTrue((obj / "601/kill/collect_quest_lv30.go_to_disciple").is_file())
            self.assertNotIn("bonus", (quest / "reward_overrides.txt").read_text())
            self.assertEqual(df.live_state(spool, qs.KEY)["kind"], "error")
            # no file: nothing
            df.write_custom(spool, qs.KEY, None)
            self.run_m2(root, "apply")
            self.assertEqual(df.live_state(spool, qs.KEY)["kind"], "ok")


if __name__ == "__main__":
    unittest.main()
