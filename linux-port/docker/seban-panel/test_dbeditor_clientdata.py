"""MT2009_PLUS_DB_EDITOR_V1: python3 test_dbeditor_clientdata.py

The client files builder (m2clientpack) without a database or the client:
the pure-Python LZO1X and XTEA, the release's dbdata pack read and written
back, and a whole build from a mocked history and item/skill tables - the
new dbdata pack read back entry by entry and the zip the panel hands out."""
import io
import os
import random
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
            self.assertEqual(sorted(z.namelist()), ['CZYTAJ_MNIE.txt', 'pack/dbdata.data', 'pack/dbdata.index'])
            self.assertEqual(z.read('pack/dbdata.index'), index)
            readme = z.read('CZYTAJ_MNIE.txt').decode('utf-8-sig')
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
        self.assertEqual(names, sorted(BASE.names() + [dbsource.EXTRA_FILE]))
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

    def test_targets(self):
        items, skills = dbsource.targets([
            change('world.item_proto', 27001, 'gold'), change('world.item_proto', 27001, 'shop_buy_price'),
            change('world.item_proto', 27002, 'socket5'), change('world.skill_proto', 4, 'szPointPoly'),
            change('world.mob_proto', 101, 'exp')])
        self.assertEqual(items, {27001: {'gold', 'shop_buy_price'}})
        self.assertEqual(skills, {4})


if __name__ == '__main__':
    unittest.main()
