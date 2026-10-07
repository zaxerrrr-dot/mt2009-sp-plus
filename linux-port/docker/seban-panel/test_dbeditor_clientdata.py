"""MT2009_PLUS_DB_EDITOR_V1: python3 test_dbeditor_clientdata.py

The client files builder (m2clientpack) without a database or the client:
the pure-Python LZO1X and XTEA, the release's dbdata pack read and written
back, and a whole build from a mocked history and item/skill tables - the
new dbdata pack read back entry by entry and the zip the panel hands out."""
import io
import os
import random
import time
import unittest
import zipfile

from m2clientpack import clientfiles, dbdata, dbsource, eterpack, lzo1x

BASE = dbdata.latest_base()


def fake_query(tables):
    """query(sql, params) over {qualified table: [rows]} (SELECT ... FROM t WHERE key IN (...))."""
    def query(sql, params=()):
        table = sql.split(' FROM ', 1)[1].split()[0]
        key = sql.split(' WHERE ', 1)[1].split()[0]
        return [dict(r) for r in tables.get(table, []) if r[key] in params]
    return query


def change(tbl, key, col, old='0', new='1'):
    return {'tbl': tbl, 'row_key': str(key), 'col': col, 'old_value': old, 'new_value': new}


def item_row(vnum, **values):
    row = dict((f, 0) for f in clientfiles.ITEM_FIELDS)
    row.update(vnum=vnum, name='x', locale_name='x', immuneflag='', socket0=-1, socket1=-1, socket2=-1)
    row.update(values)
    return row


def skill_row(vnum, **values):
    row = dict((c, '') for c in clientfiles.SKILL_COLUMNS)
    row.update(dwVnum=vnum, szName='TEST', bType=1, bLevelStep=1, bMaxLevel=1, bLevelLimit=0,
               szPointOn='HP', setFlag='ATTACK,USE_MELEE_DAMAGE', setAffectFlag='NONE',
               szPointOn2='NONE', setAffectFlag2='NONE', prerequisiteSkillVnum=0,
               prerequisiteSkillLevel=0, eSkillType='MELEE', iMaxHit=5,
               szSplashAroundDamageAdjustPoly='1', dwTargetRange=0, dwSplashRange=0)
    row.update(values)
    return row


class LzoTests(unittest.TestCase):
    def test_round_trip(self):
        rnd = random.Random(7)
        samples = [b'a', b'abc', b'abcd' * 50, bytes(range(256)) * 20, b'\0' * 70000,
                   BASE.file('locale/pl/skilldesc.txt')]
        for _ in range(60):
            alpha = rnd.randint(1, 255)
            samples.append(bytes(rnd.randint(0, alpha) for _ in range(rnd.randint(1, 4000))))
        for s in samples:
            c = lzo1x._compress_py(s)
            self.assertEqual(lzo1x._decompress_py(c, len(s)), s)

    def test_xtea(self):
        data = os.urandom(800)
        self.assertEqual(eterpack.tea_decrypt(eterpack.tea_encrypt(data, eterpack.DAT_KEY), eterpack.DAT_KEY), data)


class PackTests(unittest.TestCase):
    def test_release_pack_round_trip(self):
        index, data = BASE.original()
        ver, entries = eterpack.read_index_bytes(index)
        self.assertEqual(sorted(e.name for e in entries), BASE.names())
        for e in entries:
            self.assertEqual(eterpack.read_entry(data, e), BASE.file(e.name))
            self.assertEqual(e.ctype, BASE.ctype(e.name))
        index2, data2 = eterpack.write_pack([(n, BASE.file(n), BASE.ctype(n)) for n in BASE.names()])
        dbdata.verify(index2, data2, dict((n, BASE.file(n)) for n in BASE.names()))

    def test_item_proto_round_trip(self):
        ver, stride, recs = clientfiles.read_item_proto(BASE.file('gamedata/item_proto'))
        blob = clientfiles.write_item_proto(ver, stride, recs)
        self.assertEqual(clientfiles.read_item_proto(blob)[2], recs)


class BuildTests(unittest.TestCase):
    def setUp(self):
        ver, stride, self.recs = clientfiles.read_item_proto(BASE.file('gamedata/item_proto'))
        self.vnum = 19 if 19 in self.recs else sorted(self.recs)[0]
        self.old_type = self.recs[self.vnum][74]
        desc = BASE.file('locale/pl/itemdesc.txt').decode('cp1250')
        self.vnum_in_desc = any(l.split('\t')[0] == str(self.vnum) for l in desc.splitlines())

    def build(self, tables, changes):
        return dbsource.build_dbdata(fake_query(tables), changes, BASE)

    def test_nothing_edited_is_the_release(self):
        base, index, data, changed, _summary = self.build({}, [])
        self.assertEqual(changed, [])
        self.assertEqual((index, data), BASE.original())
        name, blob = dbdata.make_zip(base, index, data, 'localhost', changed)
        self.assertTrue(name.startswith('dbdata-localhost-klient-%s-' % BASE.version) and name.endswith('.zip'), name)
        with zipfile.ZipFile(io.BytesIO(blob)) as z:
            self.assertEqual(sorted(z.namelist()), ['CZYTAJ_MNIE.txt', 'dbdata_stamp.txt', 'pack/dbdata.data',
                                                    'pack/dbdata.index'])
            self.assertEqual(z.read('pack/dbdata.index'), index)
            readme = z.read('CZYTAJ_MNIE.txt').decode('utf-8-sig')
            stamp_file = z.read('dbdata_stamp.txt')
        # MT2009_PLUS_DBDATA_STAMP_V1: nothing edited - the release's version alone
        self.assertEqual(_summary['stamp'], BASE.version)
        self.assertEqual(dbdata.read_stamp_text(stamp_file), BASE.version)
        self.assertIn('dbdata_stamp.txt', readme)
        self.assertIn('Działa z klientem %s' % BASE.version, readme)
        self.assertIn('znajomemu', readme)
        name, _blob = dbdata.make_zip(base, index, data, 'localhost', [], original=True)
        self.assertIn('oryginal', name)

    def test_items_skills_and_texts(self):
        changes = [
            change('world.item_proto', self.vnum, 'locale_name', 'a', 'b'),
            change('world.item_proto', self.vnum, 'applyvalue0'),
            change('world.item_proto', self.vnum, 'addon_type'),  # not in the client record
            change('world.skill_proto', 1, 'szCooldownPoly'),
            change('world.item_proto', 999001, 'limitvalue0'),
        ]
        tables = {
            'world.item_proto': [
                item_row(self.vnum, locale_name=u'Miecz Próby'.encode('cp1250'), applytype0=7, applyvalue0=33, type=34),
                item_row(999001, locale_name=u'Nowość'.encode('cp1250'), type=3, stack=200, limittype0=1, limitvalue0=50),
            ],
            'world.skill_proto': [skill_row(1, szCooldownPoly='99')],
        }
        base, index, data, changed, summary = self.build(tables, changes)
        expect = ['gamedata/item_proto', 'gamedata/skilltable.txt'] + (['locale/pl/itemdesc.txt'] if self.vnum_in_desc else [])
        self.assertEqual(changed, sorted(expect))
        self.assertEqual(summary['items'], [self.vnum, 999001])
        self.assertEqual(summary['skills'], [1])

        _ver, entries = eterpack.read_index_bytes(index)
        self.assertEqual(sorted(e.name for e in entries), BASE.names())  # the same names, nothing else

        def read(name):
            return eterpack.read_entry(data, [e for e in entries if e.name == name][0])

        recs = clientfiles.read_item_proto(read('gamedata/item_proto'))[2]
        rec = recs[self.vnum]
        self.assertEqual(clientfiles.get_field(rec, 'locale_name'), u'Miecz Próby')
        self.assertEqual(clientfiles.get_field(rec, 'applyvalue0'), 33)
        self.assertEqual(rec[74], self.old_type)  # type was not edited: the client's stays
        self.assertEqual(len(recs), len(self.recs) + 1)
        self.assertEqual(clientfiles.get_field(recs[999001], 'limitvalue0'), 50)
        self.assertEqual(clientfiles.get_field(recs[999001], 'socket0'), 0)

        table = read('gamedata/skilltable.txt').decode('cp1250')
        line = [l for l in table.split('\r\n') if l.split('\t')[0] == '1'][0].split('\t')
        self.assertEqual(len(line), len(clientfiles.SKILL_COLUMNS))
        self.assertEqual(line[11], '99')
        if self.vnum_in_desc:
            desc = read('locale/pl/itemdesc.txt').decode('cp1250')
            line = [l for l in desc.split('\r\n') if l.split('\t')[0] == str(self.vnum)][0]
            self.assertEqual(line.split('\t')[1], u'Miecz Próby')
        self.assertEqual(read('locale/pl/skilldesc.txt'), BASE.file('locale/pl/skilldesc.txt'))

        # the same database builds the same pack
        self.assertEqual(self.build(tables, changes)[1:3], (index, data))

        # MT2009_PLUS_DBDATA_STAMP_V1: the stamp - the version and a hash of the
        # changed files; the same from the pack, from the lightweight check and
        # from a second build; another value gives another stamp
        stamp = summary['stamp']
        self.assertRegex(stamp, r'^%s-[0-9a-f]{12}$' % BASE.version.replace('.', r'\.'))
        self.assertEqual(dbdata.pack_stamp(BASE, index, data), stamp)
        self.assertEqual(dbsource.current_stamp(fake_query(tables), changes, BASE), (BASE, stamp))
        self.assertEqual(self.build(tables, changes)[4]['stamp'], stamp)
        tables['world.skill_proto'] = [skill_row(1, szCooldownPoly='98')]
        other = self.build(tables, changes)[4]['stamp']
        self.assertNotEqual(other, stamp)
        self.assertTrue(other.startswith(BASE.version + '-'))
        # the zip carries it with the sizes of its pack files
        name, blob = dbdata.make_zip(base, index, data, 'localhost', changed, stamp_value=stamp)
        with zipfile.ZipFile(io.BytesIO(blob)) as z:
            text = z.read('dbdata_stamp.txt').decode('ascii')
            readme = z.read('CZYTAJ_MNIE.txt').decode('utf-8-sig')
        self.assertIn('\r\nstamp %s\r\n' % stamp, text)
        self.assertIn('size pack/dbdata.index %d' % len(index), text)
        self.assertIn('size pack/dbdata.data %d' % len(data), text)
        self.assertIn(stamp, readme)
        # without a stamp given: read from the pack; the original files: the version alone
        name, blob = dbdata.make_zip(base, index, data, 'localhost', changed)
        with zipfile.ZipFile(io.BytesIO(blob)) as z:
            self.assertEqual(dbdata.read_stamp_text(z.read('dbdata_stamp.txt')), stamp)
        orig_index, orig_data = BASE.original()
        name, blob = dbdata.make_zip(base, orig_index, orig_data, 'x', [], original=True, stamp_value=stamp)
        with zipfile.ZipFile(io.BytesIO(blob)) as z:
            self.assertEqual(dbdata.read_stamp_text(z.read('dbdata_stamp.txt')), BASE.version)

    def test_extra_apply_file(self):
        """MT2009_PLUS_ITEM_EXTRA_APPLY_V1: the extra bonus lines become
        gamedata/item_extra_apply.txt, a name the 2.0.52 pack does not have."""
        extra = [dict(vnum=11299, slot=2, apply_type=13, apply_value=20), dict(vnum=11299, slot=1, apply_type=15, apply_value=20),
                 dict(vnum=140, slot=1, apply_type=12, apply_value=-5), dict(vnum=141, slot=1, apply_type=0, apply_value=9)]

        def query(sql, params=()):
            if dbsource.EXTRA_TABLE in sql:
                return [dict(r) for r in extra]
            return fake_query({})(sql, params)

        base, index, data, changed, summary = dbsource.build_dbdata(query, [], BASE)
        self.assertEqual(changed, [dbsource.EXTRA_FILE])
        self.assertEqual(summary['extra_apply'], {'lines': 3, 'items': 2})
        _ver, entries = eterpack.read_index_bytes(index)
        names = sorted(e.name for e in entries)
        self.assertEqual(names, sorted(set(BASE.names()) | {dbsource.EXTRA_FILE}))  # 2.0.53 has it already
        dbdata.verify(index, data, dict([(n, BASE.file(n)) for n in BASE.names()] + [(dbsource.EXTRA_FILE, dbsource.extra_apply_file(query, [])[0])]))
        entry = [e for e in entries if e.name == dbsource.EXTRA_FILE][0]
        self.assertEqual(entry.ctype, 2)
        text = eterpack.read_entry(data, entry).decode('ascii')
        self.assertTrue(text.startswith('# MT2009_PLUS_ITEM_EXTRA_APPLY_V1'))
        body = [l for l in text.split('\r\n') if l and not l.startswith('#')]
        self.assertEqual(body, ['140\t12\t-5', '11299\t15\t20', '11299\t13\t20'])
        for e in entries:  # every release file unchanged
            if e.name != dbsource.EXTRA_FILE:
                self.assertEqual(eterpack.read_entry(data, e), BASE.file(e.name))

        # no lines, or no table at all: the release's pack, byte for byte
        extra[:] = []
        self.assertEqual(dbsource.build_dbdata(query, [], BASE)[1:3], BASE.original())

        def broken(sql, params=()):
            if dbsource.EXTRA_TABLE in sql:
                raise RuntimeError("Table 'world.item_extra_apply' doesn't exist")
            return fake_query({})(sql, params)

        _b, index2, data2, _c, summary2 = dbsource.build_dbdata(broken, [], BASE)
        self.assertEqual((index2, data2), BASE.original())
        self.assertTrue(any('item_extra_apply' in n for n in summary2['notes']))
        # an unknown name is still refused
        with self.assertRaises(ValueError):
            dbdata.build(BASE, {'gamedata/nope.txt': b'x'})

    def test_stamp_values(self):
        self.assertEqual(dbdata.stamp(BASE, {}), BASE.version)
        a = dbdata.stamp(BASE, {'gamedata/item_proto': b'a'})
        self.assertEqual(a, dbdata.stamp(BASE, {'gamedata/item_proto': b'a'}))
        self.assertNotEqual(a, dbdata.stamp(BASE, {'gamedata/item_proto': b'b'}))
        self.assertNotEqual(a, dbdata.stamp(BASE, {'gamedata/skilltable.txt': b'a'}))
        self.assertEqual(dbdata.read_stamp_text(dbdata.stamp_text(a)), a)
        self.assertNotIn(b'size ', dbdata.stamp_text(a))  # the spool's copy: no pack beside it
        self.assertIsNone(dbdata.read_stamp_text(b'# nothing\r\n'))

    def test_skill_effect_types_reach_skilldesc(self):
        # MT2009_PLUS_DB_EDITOR_SKILL_POINT_TYPES_V1: a new effect type shows in
        # the tooltip through skilldesc.txt's affect line of that effect
        changes = [change('world.skill_proto', 3, 'szPointOn2', 'MOV_SPEED', 'ATT_GRADE'),
                   change('world.skill_proto', 3, 'szPointPoly2'),
                   change('world.skill_proto', 3, 'szPointOn3', '', 'CRITICAL'),
                   change('world.skill_proto', 4, 'szPointPoly')]
        self.assertEqual(dbsource.skill_type_targets(changes), {3: {2, 3}})
        tables = {'world.item_proto': [],
                  'world.skill_proto': [skill_row(3, szPointOn2='ATT_GRADE', szPointPoly2='10*k+iq/4',
                                                  szPointOn3='CRITICAL', szPointPoly3='atk*k'),
                                        skill_row(4)]}
        base, index, data, changed, summary = self.build(tables, changes)
        self.assertIn('locale/pl/skilldesc.txt', changed)
        self.assertEqual(summary['skilldesc'], [3])
        _ver, entries = eterpack.read_index_bytes(index)
        desc = eterpack.read_entry(data, [e for e in entries if e.name == 'locale/pl/skilldesc.txt'][0]).decode('cp1250')
        old = BASE.file('locale/pl/skilldesc.txt').decode('cp1250')
        line = [l for l in desc.split('\r\n') if l.split('\t')[0] == '3'][0].split('\t')
        old_line = [l for l in old.split('\r\n') if l.split('\t')[0] == '3'][0].split('\t')
        self.assertEqual(len(line), len(old_line))
        self.assertEqual(line[17:20], old_line[17:20])                     # effect 1 untouched
        self.assertEqual(line[20:23], [u'Wartość Ataku +%.0f', '10*k+iq/4', ''])
        self.assertEqual(line[23:26], [u'Szansa na cios krytyczny', '', ''])   # atk: no value in a tooltip
        self.assertEqual([l for l in desc.split('\r\n') if l.split('\t')[0] != '3'],
                         [l for l in old.split('\r\n') if l.split('\t')[0] != '3'])
        # back to NONE clears the line; a skill without a line there is a note
        self.assertEqual(clientfiles.effect_affect('NONE', '5'), ('', '', ''))
        self.assertEqual(clientfiles.effect_affect('MOV_SPEED', '-20'), (u'Szybkość Ruchu -%.0f%%', '-20', ''))
        notes = []
        blob, done = clientfiles.patch_skilldesc_effects(old.encode('cp1250'), {99999: {2: ('a', '1', '')}}, notes)
        self.assertEqual((done, len(notes)), ([], 1))

    def test_targets(self):
        items, skills = dbsource.targets([
            change('world.item_proto', 27001, 'gold'), change('world.item_proto', 27001, 'shop_buy_price'),
            change('world.item_proto', 27002, 'socket5'), change('world.skill_proto', 4, 'szPointPoly'),
            change('world.mob_proto', 101, 'exp')])
        self.assertEqual(items, {27001: {'gold', 'shop_buy_price'}})
        self.assertEqual(skills, {4})


class StampPanelTests(unittest.TestCase):
    """MT2009_PLUS_DBDATA_STAMP_V1: the panel's side (dbeditor/clientdata.py) -
    the game's copy in the spool, the new-client banner, the routes."""

    def setUp(self):
        import tempfile
        self.tmp = tempfile.TemporaryDirectory()
        self.spool = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def test_server_stamp_file(self):
        from dbeditor import clientdata
        self.assertIsNone(clientdata.read_server_stamp(self.spool))
        self.assertTrue(clientdata.write_server_stamp(self.spool, '2.0.53-0123456789ab'))
        self.assertFalse(clientdata.write_server_stamp(self.spool, '2.0.53-0123456789ab'))  # unchanged
        self.assertEqual(clientdata.read_server_stamp(self.spool), '2.0.53-0123456789ab')
        path = os.path.join(self.spool, 'dbdata_stamp.txt')
        self.assertEqual(os.stat(path).st_mode & 0o777, 0o664)
        with open(path, 'rb') as f:
            lines = [l for l in f.read().decode('ascii').split('\r\n') if l and not l.startswith('#')]
        self.assertEqual(lines, ['stamp 2.0.53-0123456789ab'])  # what playerbot_dbdata_stamp.h reads
        clientdata.write_server_stamp(self.spool, '2.0.53')
        self.assertEqual(clientdata.read_server_stamp(self.spool), '2.0.53')

    def test_new_client_banner(self):
        from dbeditor import clientdata
        self.assertIsNone(clientdata.new_client_banner({}, '2.0.53'))  # never downloaded
        self.assertIsNone(clientdata.new_client_banner({'base': '2.0.53'}, '2.0.53'))
        self.assertIsNone(clientdata.new_client_banner({'base': '2.0.53'}, None))
        text = clientdata.new_client_banner({'base': '2.0.52', 'stamp': '2.0.52-aaaaaaaaaaaa'}, '2.0.53')
        self.assertIn('Wyszła nowa wersja klienta (2.0.53) – pobierz ponownie pliki klienta, bo stary zip nie zawiera '
                      'nowych przedmiotów', text)

    def test_zip_popup_due(self):
        from dbeditor import clientdata
        due = clientdata.zip_popup_due
        self.assertTrue(due(100, 0, 0, True, False))       # a restart, edits, never downloaded
        self.assertTrue(due(100, 50, 60, True, False))     # a restart after the download and "Rozumiem"
        self.assertFalse(due(100, 100, 0, True, False))    # downloaded at/after the restart
        self.assertFalse(due(100, 0, 100, True, False))    # "Rozumiem" for this restart
        self.assertFalse(due(100, 0, 0, False, False))     # nothing client-visible edited
        self.assertTrue(due(100, 0, 0, False, True))       # ... but a new client base
        self.assertFalse(due(0, 0, 0, True, True))         # no restart known
        self.assertEqual(clientdata.last_restart(self.spool), 0)
        self.assertEqual(clientdata.last_restart(self.spool, {'time': 70}), 70)
        with open(os.path.join(self.spool, 'panel-restart.time'), 'w') as f:
            f.write('90\n')
        self.assertEqual(clientdata.last_restart(self.spool, {'time': 70}), 90)

    def test_routes(self):
        """The zip download writes the game's stamp and the download record;
        the hub and "Zastosuj" show the banner once the base is newer."""
        try:
            from flask import Blueprint, Flask
            from dbeditor import clientdata, common_items
            import dbeditor
        except ImportError as exc:  # pragma: no cover
            self.skipTest(str(exc))
        import json
        from jinja2 import ChoiceLoader, DictLoader, FileSystemLoader
        here = os.path.dirname(os.path.abspath(__file__))
        app = Flask('stamp')
        with open(os.path.join(here, 'templates', 'base.html'), encoding='utf-8') as f:
            popup_line = [l for l in f.read().splitlines() if 'dbe_zip_popup' in l][0]  # base.html's own line
        app.jinja_loader = ChoiceLoader([
            DictLoader({'base.html': '<main>{% block content %}{% endblock %}</main>' + popup_line}),
            FileSystemLoader(os.path.join(here, 'templates'))])
        app.secret_key = 't'
        app.config.update(TESTING=True)
        app.jinja_env.globals.update(panel_brand='MT2009 PLUS')
        bp = Blueprint('dbeditor', 'dbeditor', url_prefix='/db')
        history = [change('world.skill_proto', 1, 'szCooldownPoly', '1', '2')]
        tables = {'world.skill_proto': [skill_row(1, szCooldownPoly='77')]}
        query = fake_query(tables)
        ctx = {'app': app, 'db': None, 'rows': query, 'one': None, 'login_required': lambda v: v,
               'game_text': lambda v: v or '', 'spool': self.spool}
        os.environ.pop('DBEDITOR_SPOOL_ROOT', None)
        old_ctx = dict(common_items.ctx())
        old_net, old_notices = common_items.net_changes, list(dbeditor.HUB_NOTICES)
        try:
            common_items.net_changes = lambda include_applied=False: list(history)
            del dbeditor.HUB_NOTICES[:]
            clientdata.install(bp, ctx)
            bp.add_url_rule('/', 'index', lambda: '|'.join(n() or '' for n in dbeditor.HUB_NOTICES))
            app.register_blueprint(bp)
            client = app.test_client()
            # the hub finds no stamp in the spool and makes it
            self.assertEqual(client.get('/db/').get_data(as_text=True), '')
            _b, expected = dbsource.current_stamp(query, history, BASE)
            self.assertTrue(expected.startswith(BASE.version + '-'))
            self.assertEqual(clientdata.read_server_stamp(self.spool), expected)
            # a save of a client-visible table follows the edit
            tables['world.skill_proto'] = [skill_row(1, szCooldownPoly='78')]
            common_items._changed({'world.mob_proto'})
            self.assertEqual(clientdata.read_server_stamp(self.spool), expected)
            common_items._changed({'world.skill_proto'})
            clientdata.wait_stamp()  # worked out in the background
            edited = clientdata.read_server_stamp(self.spool)
            self.assertNotEqual(edited, expected)
            # no restart yet: no popup
            self.assertNotIn('dbe-zip-popup', client.get('/db/apply').get_data(as_text=True))
            # after a restart (app.py's panel-restart.time) every editor page has it
            restart = int(time.time()) - 5
            with open(os.path.join(self.spool, 'panel-restart.time'), 'w') as f:
                f.write('%d\n' % restart)
            page = client.get('/db/apply').get_data(as_text=True)
            self.assertIn('id="dbe-zip-popup"', page)
            self.assertIn('data-restart="%d"' % restart, page)
            self.assertIn('UWAGA! Aby zmiany z edytora bazy danych były widoczne w Twoim kliencie gry, musisz pobrać '
                          'ten plik ZIP i rozpakować go do folderu z klientem (zastąp pliki). Bez tego w grze zobaczysz '
                          'stare nazwy, bonusy i opisy. MT2009-Patcher robi to sam', page)
            self.assertIn('href="/db/clientdata.zip"', page)
            self.assertIn('Rozumiem', page)
            # "Rozumiem" (the cookie of that restart): gone until the next restart
            client.set_cookie(clientdata.POPUP_COOKIE, str(restart))
            self.assertNotIn('dbe-zip-popup', client.get('/db/apply').get_data(as_text=True))
            client.delete_cookie(clientdata.POPUP_COOKIE)
            self.assertIn('dbe-zip-popup', client.get('/db/apply').get_data(as_text=True))
            # the zip carries the game's stamp and is recorded
            res = client.get('/db/clientdata.zip')
            self.assertEqual(res.status_code, 200)
            with zipfile.ZipFile(io.BytesIO(res.get_data())) as z:
                self.assertEqual(dbdata.read_stamp_text(z.read('dbdata_stamp.txt')), edited)
            with open(os.path.join(self.spool, 'dbeditor', 'clientdata-download.json'), encoding='utf-8') as f:
                self.assertEqual(json.load(f)['base'], BASE.version)
            self.assertEqual(client.get('/db/').get_data(as_text=True), '')  # same base: no banner
            # the download hides the popup (the record, and the cookie it set)
            self.assertNotIn('dbe-zip-popup', client.get('/db/apply').get_data(as_text=True))
            client.delete_cookie(clientdata.POPUP_COOKIE)
            self.assertNotIn('dbe-zip-popup', client.get('/db/apply').get_data(as_text=True))
            with open(os.path.join(self.spool, 'panel-restart.time'), 'w') as f:  # the next restart
                f.write('%d\n' % (int(time.time()) + 5))
            self.assertIn('dbe-zip-popup', client.get('/db/apply').get_data(as_text=True))
            # an older base in the record (the panel got a new client since): the banner
            with open(os.path.join(self.spool, 'dbeditor', 'clientdata-download.json'), 'w', encoding='utf-8') as f:
                json.dump({'base': '2.0.1', 'stamp': '2.0.1-aaaaaaaaaaaa'}, f)
            self.assertIn('Wyszła nowa wersja klienta (%s)' % BASE.version, client.get('/db/').get_data(as_text=True))
            # a spool stamp of another base is made again
            clientdata.write_server_stamp(self.spool, '2.0.1-aaaaaaaaaaaa')
            client.get('/db/')
            self.assertEqual(clientdata.read_server_stamp(self.spool), edited)
        finally:
            common_items.net_changes = old_net
            dbeditor.HUB_NOTICES[:] = old_notices
            common_items.CHANGE_LISTENERS.pop('clientdata', None)
            common_items.ctx().clear()
            common_items.ctx().update(old_ctx)


class AutoDbDataTests(unittest.TestCase):
    """MT2009_PLUS_DBDATA_AUTO_V1: the public manifest and pack files for
    MT2009-Patcher (dbeditor/autodbdata.py), without the panel login."""

    def setUp(self):
        import tempfile
        self.tmp = tempfile.TemporaryDirectory()
        self.spool = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()
        os.environ.pop('DBDATA_AUTO', None)

    def make_app(self, history, tables):
        try:
            from flask import Blueprint, Flask
            from dbeditor import clientdata, common_items, autodbdata
            import dbeditor
        except ImportError as exc:  # pragma: no cover
            self.skipTest(str(exc))
        app = Flask('auto')
        app.secret_key = 't'
        app.config.update(TESTING=True)
        bp = Blueprint('dbeditor', 'dbeditor', url_prefix='/db')

        def login_required(view):  # the panel with its login on: every editor page refuses
            from functools import wraps

            @wraps(view)
            def wrapped(*a, **k):
                return ('login', 403)
            return wrapped

        query = fake_query(tables)
        ctx = {'app': app, 'db': None, 'rows': query, 'one': None, 'login_required': login_required,
               'game_text': lambda v: v or '', 'spool': self.spool,
               'panel_name': lambda: 'Tajny Serwer Testowy'}
        os.environ.pop('DBEDITOR_SPOOL_ROOT', None)
        self.old = (dict(common_items.ctx()), common_items.net_changes, list(dbeditor.HUB_NOTICES))
        common_items.net_changes = lambda include_applied=False: list(history)
        clientdata.install(bp, ctx)
        app.register_blueprint(bp)
        self.builds = []
        publisher = ctx['dbdata_publisher']
        real_build = publisher.build

        def counted():
            self.builds.append(1)
            return real_build()
        publisher.build = counted
        self.addCleanup(self.restore)
        return app, app.test_client(), query

    def restore(self):
        from dbeditor import common_items
        import dbeditor
        ctx, net, notices = self.old
        common_items.net_changes = net
        dbeditor.HUB_NOTICES[:] = notices
        common_items.CHANGE_LISTENERS.pop('clientdata', None)
        common_items.ctx().clear()
        common_items.ctx().update(ctx)

    def check_files(self, client, manifest):
        import hashlib
        got = {}
        for f in manifest['files']:
            self.assertFalse(f['url'].startswith('/'), 'relative to the manifest (works behind a gate)')
            res = client.get('/klient/dbdata/' + f['url'])
            self.assertEqual(res.status_code, 200, f['url'])
            blob = res.get_data()
            self.assertEqual(len(blob), f['size'])
            self.assertEqual(hashlib.sha256(blob).hexdigest().upper(), f['sha256'])
            got[f['name']] = blob
        self.assertEqual(sorted(got), ['pack/dbdata.data', 'pack/dbdata.index'])
        return got['pack/dbdata.index'], got['pack/dbdata.data']

    def test_edited_manifest_and_files(self):
        from dbeditor import clientdata
        history = [change('world.skill_proto', 1, 'szCooldownPoly', '1', '2')]
        tables = {'world.skill_proto': [skill_row(1, szCooldownPoly='77')]}
        app, client, query = self.make_app(history, tables)
        # the editor's pages need the login, the patcher's paths do not
        self.assertEqual(client.get('/db/apply').status_code, 403)
        self.assertEqual(client.get('/db/clientdata.zip').status_code, 403)
        res = client.get('/klient/dbdata/manifest.json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers['Cache-Control'], 'no-store')
        m = res.get_json()
        _b, expected = dbsource.current_stamp(query, history, BASE)
        self.assertEqual(m['format'], 'MT2009_PLUS_DBDATA_AUTO_V1')
        self.assertEqual(m['client_version_base'], BASE.version)
        self.assertEqual(m['stamp'], expected)
        self.assertTrue(m['edited'])
        self.assertEqual(clientdata.read_server_stamp(self.spool), expected)  # what the game sends
        index, data = self.check_files(client, m)
        self.assertEqual(dbdata.pack_stamp(BASE, index, data), expected)
        self.assertEqual(m['base'], {'index_sha256': BASE.meta['pack']['indexSha256'],
                                     'data_sha256': BASE.meta['pack']['dataSha256']})
        stamp_file = m['stamp_file'].encode('ascii')
        self.assertEqual(stamp_file, dbdata.stamp_text(expected, index, data))
        self.assertIn(b'size pack/dbdata.data %d' % len(data), stamp_file)
        # nothing of the panel in the answer: no name, no paths, no history
        text = res.get_data(as_text=True)
        for secret in ('Tajny', self.spool, 'szCooldownPoly', 'world.', '/opt'):
            self.assertNotIn(secret, text)
        self.assertEqual(set(m), {'format', 'client_version_base', 'stamp', 'edited', 'built', 'files', 'base', 'stamp_file'})
        # built once, then from the cache (both workers share the spool's copy)
        self.assertEqual(len(self.builds), 1)
        self.assertEqual(client.get('/klient/dbdata/manifest.json').get_json()['stamp'], expected)
        self.assertEqual(len(self.builds), 1)
        self.assertTrue(os.path.isdir(os.path.join(self.spool, 'dbeditor', 'autodbdata', expected)))
        # only the two pack files of a known stamp; nothing else is a path
        for bad in ('/klient/dbdata/%s/meta.json' % expected, '/klient/dbdata/%s/..%%2Fmeta.json' % expected,
                    '/klient/dbdata/2.0.1-aaaaaaaaaaaa/dbdata.data', '/klient/dbdata/../dbdata_stamp.txt',
                    '/klient/dbdata/%2E%2E/dbdata.index', '/klient/dbdata/x/y/dbdata.index'):
            self.assertEqual(client.get(bad).status_code, 404, bad)
        self.assertEqual(client.post('/klient/dbdata/manifest.json').status_code, 405)
        # an edit: a new stamp, a new pack
        tables['world.skill_proto'] = [skill_row(1, szCooldownPoly='78')]
        clientdata.write_server_stamp(self.spool, dbsource.current_stamp(query, history, BASE)[1])
        m2 = client.get('/klient/dbdata/manifest.json').get_json()
        self.assertNotEqual(m2['stamp'], expected)
        self.check_files(client, m2)
        self.assertEqual(len(self.builds), 2)
        # a stale spool stamp: the build is the truth and goes to the spool
        tables['world.skill_proto'] = [skill_row(1, szCooldownPoly='79')]
        m3 = client.get('/klient/dbdata/manifest.json').get_json()
        self.assertEqual(m3['stamp'], m2['stamp'])  # still the cached pack of the spool's stamp
        clientdata.write_server_stamp(self.spool, BASE.version + '-ffffffffffff')  # unknown to the cache
        m4 = client.get('/klient/dbdata/manifest.json').get_json()
        self.assertEqual(m4['stamp'], dbsource.current_stamp(query, history, BASE)[1])
        self.assertEqual(clientdata.read_server_stamp(self.spool), m4['stamp'])

    def test_base_needs_no_build(self):
        app, client, _q = self.make_app([], {})
        m = client.get('/klient/dbdata/manifest.json').get_json()
        self.assertEqual(m['stamp'], BASE.version)
        self.assertFalse(m['edited'])
        pack = BASE.meta['pack']
        self.assertEqual([f['sha256'] for f in m['files']], [pack['indexSha256'], pack['dataSha256']])
        self.assertEqual(self.check_files(client, m), BASE.original())
        self.assertEqual(self.builds, [])
        self.assertIn('stamp %s\r\n' % BASE.version, m['stamp_file'])

    def test_switch_and_rate_limit(self):
        from dbeditor import autodbdata
        app, client, _q = self.make_app([], {})
        os.environ['DBDATA_AUTO'] = '0'
        self.assertEqual(client.get('/klient/dbdata/manifest.json').status_code, 404)
        os.environ.pop('DBDATA_AUTO')
        codes = [client.get('/klient/dbdata/manifest.json').status_code for _ in range(autodbdata.RATE_MANIFEST + 1)]
        self.assertEqual(codes[:-1], [200] * autodbdata.RATE_MANIFEST)
        self.assertEqual(codes[-1], 429)
        limit = autodbdata.RateLimit(2, 10)
        self.assertTrue(limit.allow('a', 0) and limit.allow('a', 1))
        self.assertFalse(limit.allow('a', 2))
        self.assertTrue(limit.allow('b', 2))
        self.assertTrue(limit.allow('a', 11))


if __name__ == '__main__':
    unittest.main()
