"""MT2009_PLUS_DB_EDITOR_REAPPLY_V1: python3 test_dbeditor_reapply.py

The database editor's history against the data (dbeditor/reapply.py): the
drift after a world reset ("Przywróć zmiany z historii"), the replay SQL the
whole-world reset runs, the labels that lost their Polish letters, the
reset page's "zachowaj zmiany z Edytora bazy danych" and the client-data
stamp following the database. Same FakeDB as test_dbeditor_items.py."""
import os
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import test_dbeditor_items as base  # sets the environment and imports the panel

from dbeditor import clientdata, common_items, items, reapply  # noqa: E402
from m2clientpack import dbdata, dbsource  # noqa: E402

panel = base.panel


class FakeDB(base.FakeDB):
    history_dropped = False

    def execute(self, sql, params):
        flat = " ".join(sql.split())
        if "web_dbeditor_history" in flat:
            if flat.startswith("CREATE TABLE"):
                self.history_dropped = False
            elif self.history_dropped:
                import pymysql
                raise pymysql.err.ProgrammingError(1146, "Table 'player.web_dbeditor_history' doesn't exist")
        if flat.startswith("SELECT DISTINCT tbl, row_key, label FROM player.web_dbeditor_history"):
            seen, out = set(), []
            for r in self.history:
                key = (r["tbl"], r["row_key"], r["label"])
                if "?" in (r["label"] or "") and key not in seen:
                    seen.add(key)
                    out.append({"tbl": r["tbl"], "row_key": r["row_key"], "label": r["label"]})
            return out, 0
        if flat.startswith("UPDATE player.web_dbeditor_history SET label"):
            label, tbl, key, old = params
            count = 0
            for r in self.history:
                if (r["tbl"], r["row_key"], r["label"]) == (tbl, key, old):
                    r["label"] = label
                    count += 1
            return [], count
        return super().execute(sql, params)


def world_reset(fake):
    """What "Reset całego świata" leaves: the image's tables, the history kept."""
    fresh = base.FakeDB()
    fake.tables = fresh.tables


class ReapplyTests(unittest.TestCase):
    def setUp(self):
        self.fake = FakeDB()
        common_items._STATE["table_ready"] = False
        common_items._CTX.update(rows=self.fake.rows, db=self.fake.db)
        reapply._CACHE.update(at=0.0, result=None)
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
        clientdata.wait_stamp()
        for p in self.patches:
            p.stop()

    def panel_rows(self, sql, params=()):
        if re.search(r"item_proto|skill_proto|web_dbeditor_history|common\.locale", sql):
            return self.fake.rows(sql, params)
        return []

    def edits(self):
        """The owner's edits: a skill formula, an item's Polish name and level."""
        with panel.app.test_request_context("/"):
            common_items.save_rows("world.skill_proto", [(3, {"szDurationPoly": "(60+100*k)*6"})],
                                   label_of=lambda _k: "Zwiększenie Ataku")
            common_items.save_rows("world.item_proto", [(149, {"locale_name": "Miecz Żołnierza+9", "limitvalue0": 70})],
                                   label_of=lambda _k: "Miecz Bojowy+9")
            # MT2009_PLUS_ITEM_EXTRA_APPLY_V1: a whole row added
            common_items.write_rows("world.item_extra_apply",
                                    inserts=[{"vnum": 149, "slot": 3, "apply_type": 17, "apply_value": 5}],
                                    label_of=lambda _k: "Miecz Bojowy+9")

    # ---- drift and "Przywróć zmiany z historii" ----------------------------------------
    def test_drift_after_world_reset_and_restore(self):
        self.edits()
        self.assertEqual(reapply.drift()["restore"], [])
        world_reset(self.fake)
        found = reapply.drift()
        self.assertEqual(len(found["restore"]), 4)
        self.assertEqual(found["conflict"], [])
        # the undo refuses, pointing at the restore
        with panel.app.test_request_context("/"):
            _b, message, ok = common_items.revert(batch=self.fake.history[0]["batch"])
        self.assertFalse(ok)
        self.assertIn("Przywróć zmiany z historii", message)
        # the hub says so
        page = self.client.get("/db/").get_data(as_text=True)
        self.assertIn("Wykryto 4 zmian z historii, których nie ma w bazie", page)
        self.assertIn("/db/historia/przywroc", page)
        page = self.client.get("/db/historia/przywroc").get_data(as_text=True)
        self.assertIn("Do przywrócenia: 4", page)
        res = self.client.post("/db/historia/przywroc", data={"dbe_csrf": "tok"}, follow_redirects=True)
        self.assertIn("Przywrócono 4 zmian(y) z historii", res.get_data(as_text=True))
        skill = self.fake.tables["world.skill_proto"][3]
        self.assertEqual(skill["szDurationPoly"], "(60+100*k)*6")
        item = self.fake.tables["world.item_proto"][149]
        self.assertEqual(item["locale_name"], "Miecz Żołnierza+9".encode("cp1250"))
        self.assertEqual(int(item["limitvalue0"]), 70)
        self.assertIn((149, 3), self.fake.tables["world.item_extra_apply"])
        restored = [r for r in self.fake.history if r["note"] == reapply.RESTORE_NOTE]
        self.assertEqual(len(restored), 4)
        self.assertEqual(len({r["batch"] for r in restored}), 1)  # one save
        self.assertTrue(all(r["applied_at"] is None for r in restored))  # waits for "Zastosuj"
        reapply._CACHE.update(at=0.0, result=None)
        self.assertEqual(reapply.drift()["restore"], [])
        self.assertNotIn("Wykryto", self.client.get("/db/").get_data(as_text=True))
        # and the owner's undo works again
        with panel.app.test_request_context("/"):
            _b, message, ok = common_items.revert(batch=self.fake.history[0]["batch"])
        self.assertTrue(ok, message)
        self.assertEqual(self.fake.tables["world.skill_proto"][3]["szDurationPoly"], "60+90*k")

    def test_values_neither_old_nor_new_are_listed_not_touched(self):
        self.edits()
        world_reset(self.fake)
        self.fake.tables["world.skill_proto"][3]["szDurationPoly"] = "99*k"
        found = reapply.drift()
        self.assertEqual(len(found["restore"]), 3)
        self.assertEqual([(c["row_key"], c["col"], c["current"]) for c in found["conflict"]],
                         [("3", "szDurationPoly", "99*k")])
        page = self.client.get("/db/historia/przywroc").get_data(as_text=True)
        self.assertIn("Inna wartość w bazie: 1", page)
        with panel.app.test_request_context("/"):
            batch, restored, errors, conflicts = reapply.restore()
        self.assertEqual((restored, errors, conflicts), (3, [], 1))
        self.assertTrue(batch)
        self.assertEqual(self.fake.tables["world.skill_proto"][3]["szDurationPoly"], "99*k")

    def test_nothing_to_restore(self):
        self.edits()
        res = self.client.post("/db/historia/przywroc", data={"dbe_csrf": "tok"}, follow_redirects=True)
        self.assertIn("Nic do przywrócenia", res.get_data(as_text=True))
        self.assertFalse([r for r in self.fake.history if r["note"] == reapply.RESTORE_NOTE])

    def test_restore_needs_the_form_token(self):
        self.edits()
        world_reset(self.fake)
        self.client.post("/db/historia/przywroc", data={"dbe_csrf": "wrong"})
        self.assertEqual(self.fake.tables["world.skill_proto"][3]["szDurationPoly"], "60+90*k")

    # ---- the history table dropped under the panel ------------------------------------------
    def test_save_recovers_when_the_reset_dropped_the_history_table(self):
        with panel.app.test_request_context("/"):
            common_items.save_rows("world.item_proto", [(140, {"limitvalue0": 66})])
        self.assertTrue(common_items._STATE["table_ready"])
        self.fake.history_dropped = True  # "Reset całego świata" while the panel runs
        res = self.client.post("/db/items/149", data=dict(self.item_form(149, level=71), dbe_csrf="tok"),
                               follow_redirects=True)
        self.assertNotIn("1146", res.get_data(as_text=True))
        self.assertEqual(int(self.fake.tables["world.item_proto"][149]["limitvalue0"]), 71)
        self.assertEqual(self.fake.history[-1]["new_value"], "71")
        self.fake.history_dropped = True
        with panel.app.test_request_context("/"):
            _b, message, ok = common_items.revert(batch=self.fake.history[-1]["batch"])
        self.assertTrue(ok, message)
        self.assertTrue(common_items.history_missing(
            __import__("pymysql").err.ProgrammingError(1146, "Table 'player.web_dbeditor_history' doesn't exist")))
        self.assertFalse(common_items.history_missing(
            __import__("pymysql").err.ProgrammingError(1146, "Table 'world.item_proto' doesn't exist")))

    def item_form(self, vnum, **changes):
        return base.DbEditorItemsTests.item_form(self, vnum, **changes)

    # ---- labels ----------------------------------------------------------------------------
    def test_broken_label_shown_and_repaired_from_current_name(self):
        self.edits()
        for r in self.fake.history:  # what a backup dumped as latin1 gives back
            r["label"] = r["label"].replace("ę", "?").replace("Ż", "?").replace("ł", "?")
        self.fake.history[0]["label"] = "Zwi?kszenie Ataku"
        self.assertEqual(common_items.display_label(self.fake.history[0]), "Berserk")  # skills.SKILL_NAMES_PL
        page = self.client.get("/db/historia").get_data(as_text=True)
        self.assertNotIn("Zwi?kszenie", page)
        self.assertIn("Berserk", page)
        world_reset(self.fake)
        with panel.app.test_request_context("/"):
            _b, message, ok = common_items.revert(batch=self.fake.history[0]["batch"])
        self.assertIn("Berserk · szDurationPoly", message)
        self.assertGreaterEqual(reapply.repair_labels(), 1)
        self.assertEqual(self.fake.history[0]["label"], "Berserk")
        self.assertEqual(common_items.display_label({"tbl": "world.item_proto", "row_key": "149", "label": "Miecz ?"}),
                         "Miecz Bojowy+9")
        # a good label is kept as it was written
        self.assertEqual(common_items.display_label({"tbl": "world.skill_proto", "row_key": "3", "label": "Zwiększenie"}),
                         "Zwiększenie")

    def test_new_labels_keep_polish_letters(self):
        self.edits()
        self.assertEqual(self.fake.history[0]["label"], "Zwiększenie Ataku")

    # ---- the whole-world reset's replay ----------------------------------------------------------
    def test_replay_sql_is_ascii_and_sets_every_net_change(self):
        self.edits()
        with panel.app.test_request_context("/"):  # an undone change is not replayed
            common_items.save_rows("world.item_proto", [(140, {"limitvalue0": 66})])
            common_items.revert(batch=self.fake.history[-1]["batch"])
        text = reapply.replay_sql("reset-abc")
        text.encode("ascii")
        lines = text.splitlines()
        self.assertEqual(lines[0], "-- id=reset-abc")
        self.assertIn("UPDATE world.skill_proto SET `szDurationPoly`=X'%s' WHERE `dwVnum`=3;"
                      % b"(60+100*k)*6".hex(), lines)
        self.assertIn("UPDATE world.item_proto SET `locale_name`=X'%s' WHERE `vnum`=149;"
                      % "Miecz Żołnierza+9".encode("cp1250").hex(), lines)
        self.assertIn("UPDATE world.item_proto SET `limitvalue0`=70 WHERE `vnum`=149;", lines)
        self.assertIn("DELETE FROM world.item_extra_apply WHERE `vnum`=149 AND `slot`=3;", lines)
        insert = [l for l in lines if l.startswith("INSERT INTO world.item_extra_apply")]
        self.assertEqual(len(insert), 1)
        self.assertIn("149", insert[0])
        self.assertFalse([l for l in lines if "`vnum`=140" in l])

    def test_replay_of_a_removed_row_only_deletes(self):
        with panel.app.test_request_context("/"):
            common_items.write_rows("world.item_extra_apply",
                                    inserts=[{"vnum": 140, "slot": 3, "apply_type": 1, "apply_value": 2}])
            common_items.ctx()["rows"]("UPDATE player.web_dbeditor_history SET applied_at=NOW()")
            common_items.write_rows("world.item_extra_apply", deletes=[{"vnum": 140, "slot": 3}])
        statements, skipped = reapply.replay_statements()
        # added then removed: no net change at all
        self.assertEqual((statements, skipped), ([], []))
        changes = [{"tbl": "world.item_extra_apply", "row_key": "140:3", "col": "*",
                    "old_value": '{"apply_type": 1, "apply_value": 2, "slot": 3, "vnum": 140}', "new_value": None}]
        statements, _ = reapply.replay_statements(changes)
        self.assertEqual(statements, ["DELETE FROM world.item_extra_apply WHERE `vnum`=140 AND `slot`=3;"])

    def test_replay_skips_unknown_tables_and_bad_values(self):
        changes = [{"tbl": "world.nope", "row_key": "1", "col": "x", "old_value": "1", "new_value": "2"},
                   {"tbl": "world.item_proto", "row_key": "149", "col": "limitvalue0", "old_value": "1",
                    "new_value": "1; DROP TABLE x"},
                   {"tbl": "world.item_proto", "row_key": "149", "col": "not_a_column", "old_value": "1", "new_value": "2"}]
        statements, skipped = reapply.replay_statements(changes)
        self.assertEqual(statements, [])
        self.assertEqual(len(skipped), 3)

    # ---- the reset page --------------------------------------------------------------------------
    def reset_post(self, spool, **form):
        data = {"reset_csrf": "tok", "kind": "all", "db_password": os.environ["DB_PASSWORD"], "confirm": "RESET"}
        data.update(form)
        with patch.object(panel, "RATES_SPOOL", spool), \
                patch.object(panel, "WORLD_RESET_REQUEST", spool / "world-reset.request"), \
                patch.object(panel, "WORLD_RESET_STATUS", spool / "world-reset.status"), \
                patch.object(panel, "WORLD_RESET_DBEDITOR_SQL", spool / "world-reset.dbeditor.sql"), \
                patch.object(panel, "mark_panel_restart", return_value=None):
            page = self.client.get("/advanced/world-reset").get_data(as_text=True)
            res = self.client.post("/advanced/world-reset", data=data, follow_redirects=True)
        return page, res.get_data(as_text=True)

    def test_world_reset_keeps_the_editor_changes_by_default(self):
        self.edits()
        spool = Path(tempfile.mkdtemp(prefix="dbe-reset-"))
        page, result = self.reset_post(spool, keep_dbeditor="1")
        self.assertIn('name="keep_dbeditor" value="1" checked', page)
        self.assertIn("Zachowaj zmiany z Edytora bazy danych", page)
        self.assertIn("prośba przyjęta", result)
        request_text = (spool / "world-reset.request").read_text(encoding="utf-8")
        self.assertIn("dbeditor=keep", request_text)
        request_id = re.search(r"id=(\S+)", request_text).group(1)
        sql = (spool / "world-reset.dbeditor.sql").read_text(encoding="ascii")
        self.assertTrue(sql.startswith(f"-- id={request_id}\n"))
        self.assertIn("`szDurationPoly`=X'%s'" % b"(60+100*k)*6".hex(), sql)

    def test_world_reset_clean_archives_and_writes_no_replay(self):
        self.edits()
        spool = Path(tempfile.mkdtemp(prefix="dbe-reset-"))
        _page, result = self.reset_post(spool)  # the box unticked: not sent
        self.assertIn("prośba przyjęta", result)
        self.assertIn("dbeditor=clean", (spool / "world-reset.request").read_text(encoding="utf-8"))
        self.assertFalse((spool / "world-reset.dbeditor.sql").exists())

    def test_world_reset_refused_when_the_changes_cannot_be_prepared(self):
        spool = Path(tempfile.mkdtemp(prefix="dbe-reset-"))
        with patch.object(reapply, "replay_sql", side_effect=RuntimeError("baza nie odpowiada")):
            _page, result = self.reset_post(spool, keep_dbeditor="1")
        self.assertIn("Nie udało się przygotować zmian z Edytora bazy danych", result)
        self.assertFalse((spool / "world-reset.request").exists())

    def test_bots_reset_never_touches_the_editor(self):
        spool = Path(tempfile.mkdtemp(prefix="dbe-reset-"))
        _page, result = self.reset_post(spool, kind="bots")
        self.assertIn("dbeditor=keep", (spool / "world-reset.request").read_text(encoding="utf-8"))
        self.assertFalse((spool / "world-reset.dbeditor.sql").exists())

    # ---- the client-data stamp ----------------------------------------------------------------------
    def test_stamp_and_zip_agree_with_the_database_after_drift(self):
        self.edits()
        query = common_items.ctx()["rows"]
        changes = common_items.net_changes(include_applied=True)
        _base, edited = dbsource.current_stamp(query, changes)
        self.assertIn("-", edited)
        world_reset(self.fake)
        _base, stamp_now = dbsource.current_stamp(query, changes)
        built = dbsource.build_dbdata(query, changes)
        self.assertEqual(built[4]["stamp"], stamp_now)  # the zip's = the server's, whatever the drift
        self.assertNotEqual(stamp_now, edited)
        # the hub makes the spool's stamp follow the database
        stamp_path = os.path.join(base.SPOOL, "dbdata_stamp.txt")
        clientdata.write_server_stamp(base.SPOOL, edited)
        self.client.get("/db/")
        clientdata.wait_stamp()
        with open(stamp_path, "rb") as f:
            self.assertEqual(dbdata.read_stamp_text(f.read()), stamp_now)
        # after the restore the fresh stamp is the edited one again
        with panel.app.test_request_context("/"):
            reapply.restore()
        clientdata.wait_stamp()
        with open(stamp_path, "rb") as f:
            self.assertEqual(dbdata.read_stamp_text(f.read()), edited)


if __name__ == "__main__":
    unittest.main()
