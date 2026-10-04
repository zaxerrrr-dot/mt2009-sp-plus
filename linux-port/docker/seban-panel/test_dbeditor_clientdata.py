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
        desc = BASE.file('locale/pl/itemdesc.txt').decode('cp1250')
        self.vnum_in_desc = any(l.split('\t')[0] == str(self.vnum) for l in desc.splitlines())

    def tearDown(self):
        self.tmp.cleanup()

    def build(self, tables, changes):
        out = os.path.join(self.tmp.name, 'out')
        return out, dbsource.build_from_db(fake_query(tables), out, changes, BASE)

    def test_nothing_edited(self):
        out, m = self.build({}, [])
        self.assertEqual(m['packs'], [])
        self.assertEqual(m['stamp'], 'oryginal')

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
        out, m = self.build(tables, changes)
        self.assertEqual(sorted(p['name'] for p in m['packs']), ['gamedata', 'locale'] if self.vnum_in_desc else ['gamedata'])
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
        self.assertEqual(sorted(overlay.apply_to_folder(m, out, packdir)), sorted(p['name'] for p in m['packs']))

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
        if self.vnum_in_desc:
            desc = read('locale', 'locale/pl/itemdesc.txt').decode('cp1250')
            line = [l for l in desc.split('\r\n') if l.split('\t')[0] == str(self.vnum)][0]
            self.assertEqual(line.split('\t')[1], u'Miecz Próby')

        # unchanged entries keep their place in the release's data
        for pack in BASE.meta['packs']:
            _, old = eterpack.read_index_bytes(BASE.index_bytes(pack))
            with open(os.path.join(packdir, pack + '.index'), 'rb') as f:
                new = dict((e.name, e) for e in eterpack.read_index_bytes(f.read())[1])
            touched = ([p['entries'] for p in m['packs'] if p['name'] == pack] or [[]])[0]
            for e in old:
                if e.name not in touched:
                    self.assertEqual(new[e.name].raw, e.raw)

        # the same database builds the same stamp
        out2, m2 = self.build(tables, changes)
        self.assertEqual(m2['stamp'], m['stamp'])

    def test_targets(self):
        items, skills = dbsource.targets([
            change('world.item_proto', 27001, 'gold'), change('world.item_proto', 27001, 'shop_buy_price'),
            change('world.item_proto', 27002, 'socket5'), change('world.skill_proto', 4, 'szPointPoly'),
            change('world.mob_proto', 101, 'exp')])
        self.assertEqual(items, {27001: {'gold', 'shop_buy_price'}})
        self.assertEqual(skills, {4})


if __name__ == '__main__':
    unittest.main()
