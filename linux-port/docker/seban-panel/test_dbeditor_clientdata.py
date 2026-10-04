"""MT2009_PLUS_DB_EDITOR_V1: python3 test_dbeditor_clientdata.py

The client data builder (m2clientpack) without a database or the client:
the pure-Python LZO1X and XTEA, the released client's index read and
written back, and a whole build from a mocked history and item/skill
tables, laid onto a stand-in pack folder (the release's index + a .data
of the release's length) and read back entry by entry."""
import os
import random
import tempfile
import unittest

from m2clientpack import clientfiles, dbsource, eterpack, lzo1x, overlay

BASE = overlay.latest_base()


def fake_query(tables):
    """query(sql, params) over {qualified table: [rows]}."""
    def query(sql, params=()):
        if 'information_schema.TABLES' in sql:
            return [{'1': 1}] if '%s.%s' % params in tables else []
        table = sql.split(' FROM ', 1)[1].split()[0]
        data = tables.get(table, [])
        if ' IN (' in sql:
            key = sql.split(' WHERE ', 1)[1].split()[0]
            return [r for r in data if r[key] in params]
        if ' WHERE id > ' in sql:
            return [r for r in data if r['id'] > params[0]]
        return list(data)
    return query


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
    def test_base_index_round_trip(self):
        for pack in BASE.meta['packs']:
            ver, entries = eterpack.read_index_bytes(BASE.index_bytes(pack))
            self.assertEqual(len(entries), BASE.meta['packs'][pack]['entries'])
            again = eterpack.write_index_bytes(ver, entries)
            self.assertEqual([e.raw for e in eterpack.read_index_bytes(again)[1]], [e.raw for e in entries])

    def test_item_proto_round_trip(self):
        ver, stride, recs = clientfiles.read_item_proto(BASE.file('gamedata/item_proto'))
        blob = clientfiles.write_item_proto(ver, stride, recs)
        self.assertEqual(clientfiles.read_item_proto(blob)[2], recs)


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        ver, stride, self.recs = clientfiles.read_item_proto(BASE.file('gamedata/item_proto'))
        self.vnum = 19 if 19 in self.recs else sorted(self.recs)[0]
        self.old_type = self.recs[self.vnum][74]

    def tearDown(self):
        self.tmp.cleanup()

    def build(self, tables):
        out = os.path.join(self.tmp.name, 'out')
        return out, dbsource.build_from_db(fake_query(tables), out, BASE)

    def test_nothing_edited(self):
        out, m = self.build({})
        self.assertEqual(m['packs'], [])
        self.assertEqual(m['stamp'], 'oryginal')

    def test_items_skills_and_texts(self):
        tables = {
            dbsource.HISTORY: [
                {'id': 1, 'created_at': '2026-10-04 12:00', 'table_name': 'item_proto', 'vnum': self.vnum,
                 'changes': '{"locale_name": {"old": "a", "new": "b"}, "applyvalue0": {"old": 1, "new": 2}}'},
                {'id': 2, 'table_name': 'skill_proto', 'vnum': 1, 'field': 'szCooldownPoly'},
                {'id': 3, 'table_name': 'item_proto', 'vnum': 999001, 'summary': 'nowy'},
            ],
            'player.item_proto': [
                item_row(self.vnum, locale_name=u'Miecz Próby', applytype0=7, applyvalue0=33, type=34),
                item_row(999001, locale_name=u'Nowość', type=3, stack=200, limittype0=1, limitvalue0=50),
            ],
            'world.skill_proto': [skill_row(1, szCooldownPoly='99')],
            dbsource.ITEMDESC: [{'vnum': self.vnum, 'description': u'Opis z panelu', 'summary': None}],
            dbsource.SKILLDESC: [{'vnum': 1, 'name1': u'Cięcie Testowe', 'name2': None, 'name3': '', 'description': None}],
        }
        out, m = self.build(tables)
        self.assertEqual(sorted(p['name'] for p in m['packs']), ['gamedata', 'locale'])
        self.assertEqual(m['summary']['items'], [self.vnum, 999001])
        self.assertEqual(m['summary']['skills'], [1])

        # the launcher's work on a stand-in client: release index + data of the release's length
        packdir = os.path.join(self.tmp.name, 'pack')
        os.makedirs(packdir)
        for pack, meta in BASE.meta['packs'].items():
            with open(os.path.join(packdir, pack + '.index'), 'wb') as f:
                f.write(BASE.index_bytes(pack))
            with open(os.path.join(packdir, pack + '.data'), 'wb') as f:
                f.truncate(meta['dataSize'])
        self.assertEqual(sorted(overlay.apply_to_folder(m, out, packdir)), ['gamedata', 'locale'])

        def read(pack, name):
            with open(os.path.join(packdir, pack + '.index'), 'rb') as f:
                entry = [e for e in eterpack.read_index_bytes(f.read())[1] if e.name == name][0]
            with open(os.path.join(packdir, pack + '.data'), 'rb') as f:
                return eterpack.read_entry(f.read(), entry)

        recs = clientfiles.read_item_proto(read('gamedata', 'gamedata/item_proto'))[2]
        rec = recs[self.vnum]
        self.assertEqual(clientfiles.get_field(rec, 'locale_name'), u'Miecz Próby')
        self.assertEqual(clientfiles.get_field(rec, 'applyvalue0'), 33)
        self.assertEqual(rec[74], self.old_type)  # type was not edited: the client's stays
        self.assertEqual(len(recs), len(self.recs) + 1)
        self.assertEqual(clientfiles.get_field(recs[999001], 'limitvalue0'), 50)
        self.assertEqual(clientfiles.get_field(recs[999001], 'socket0'), 0)

        table = read('gamedata', 'gamedata/skilltable.txt').decode('cp1250')
        line = [l for l in table.split('\r\n') if l.split('\t')[0] == '1'][0].split('\t')
        self.assertEqual(len(line), len(clientfiles.SKILL_COLUMNS))
        self.assertEqual(line[11], '99')
        desc = read('locale', 'locale/pl/itemdesc.txt').decode('cp1250')
        self.assertIn(u'\t'.join([str(self.vnum), u'Miecz Próby', u'Opis z panelu']), desc)
        sdesc = read('locale', 'locale/pl/skilldesc.txt').decode('cp1250')
        cols = [l for l in sdesc.splitlines() if l.split('\t')[0] == '1'][0].split('\t')
        self.assertEqual(cols[2], u'Cięcie Testowe')

        # unchanged entries keep their place in the release's data
        for pack in BASE.meta['packs']:
            _, old = eterpack.read_index_bytes(BASE.index_bytes(pack))
            with open(os.path.join(packdir, pack + '.index'), 'rb') as f:
                new = dict((e.name, e) for e in eterpack.read_index_bytes(f.read())[1])
            touched = [p['entries'] for p in m['packs'] if p['name'] == pack][0]
            for e in old:
                if e.name not in touched:
                    self.assertEqual(new[e.name].raw, e.raw)

        # the same database builds the same stamp
        out2, m2 = self.build(tables)
        self.assertEqual(m2['stamp'], m['stamp'])

    def test_history_shapes(self):
        rows = [
            {'id': 5, 'tbl': 'ITEM_PROTO', 'row_key': '27001', 'fields': 'gold, shop_buy_price'},
            {'id': 6, 'kind': 'drop', 'summary': 'Metin'},
            {'id': 7, 'target': 'item', 'record_key': 27002},
        ]
        norm = [dbsource.normalize(r) for r in rows]
        self.assertEqual([n['kind'] for n in norm], ['item', 'drop', 'item'])
        items, skills = dbsource.edited_targets(norm)
        self.assertEqual(items[27001], {'gold', 'shop_buy_price'})
        self.assertEqual(items[27002], set(clientfiles.SAFE_FIELDS))
        self.assertEqual(dbsource.history(fake_query({})), [])


if __name__ == '__main__':
    unittest.main()
