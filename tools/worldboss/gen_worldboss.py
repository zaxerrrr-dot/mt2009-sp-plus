#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MT2009_PLUS_WORLDBOSS_V1 - Boss Swiata (World Boss): generates the server's and the client tool's files from
worldboss_data.py (the pl-wiki's event) and base_rows.json (the base monsters' and items' rows of our world,
taken from the test server's world.mob_proto / world.item_proto with --snapshot):

    linux-port/docker/mariadb/playerbot/worldboss.sql   world.mob_proto (INSERT IGNORE) - the six bosses 4429 ...
                                                        4479 and their thirty men 4420-4474 (GF's numbers); their
                                                        element and race (UPDATE, every start after
                                                        zywioly_moby.sql); world.item_proto (INSERT IGNORE) -
                                                        Skrzynka Tajemnic 38015, Kupon SM (20) 80031, (10) 80032;
                                                        the event's tables (CREATE TABLE IF NOT EXISTS)
    linux-port/docker/game/worldboss/worldboss.txt      the game's data: bosses, men, maps and spots, the loot
                                                        tiers, the season's rewards (playerbot_worldboss.h)
    linux-port/docker/game/worldboss/special_item_group.worldboss.txt   Skrzynka Tajemnic's contents
    tools/worldboss/worldboss_client.json               the client tool's rows (client-2.0.30/tools/yworldboss)

    python3 tools/worldboss/gen_worldboss.py [--snapshot]
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, 'tools', 'yohara_maps'))
sys.path.insert(0, os.path.join(REPO, 'tools', 'yohara_items'))
import worldboss_data as D  # noqa: E402
from gen_ymaps_sql import COLS  # noqa: E402
import gen_yitems as Y  # noqa: E402

M = 'MT2009_PLUS_WORLDBOSS_V1'
BASE_JSON = os.path.join(HERE, 'base_rows.json')
SQL_OUT = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot', 'worldboss.sql')
GAME_DIR = os.path.join(REPO, 'linux-port', 'docker', 'game', 'worldboss')
JSON_OUT = os.path.join(HERE, 'worldboss_client.json')
SNAP_MOBS = sorted(set([D.STAT_TEMPLATE_BOSS] + [b['base'] for b in D.BOSSES] +
                       [m[4] for b in D.BOSSES for m in b['minions']] + list(D.MINION_TEMPLATE.values())))
SNAP_ITEMS = sorted(set([i['src'] for i in D.ITEMS_NEW] + [v for v, n in D.MYSTERY] +
                        [v for t in D.TIERS for v, c in t[5]] + [v for s in D.SEASON_CHAR + D.SEASON_GUILD
                                                                for v, c, d in s[2]]) - set(i['vnum'] for i in D.ITEMS_NEW))


def db(sql):
    out = subprocess.run(['docker', 'exec', '-i', 'mt2009plustest-db', 'sh', '-c',
                          'mariadb -uroot -p"$MARIADB_ROOT_PASSWORD" --default-character-set=utf8mb4 -B world'],
                         input=sql.encode(), capture_output=True, check=True).stdout.decode('utf-8')
    lines = out.rstrip('\n').split('\n')
    head = lines[0].split('\t')
    return [dict(zip(head, l.split('\t'))) for l in lines[1:]]


def snapshot():
    mobs = db('SELECT %s FROM mob_proto WHERE vnum IN (%s) ORDER BY vnum;' % (
        ','.join('`%s`' % c for c in COLS), ','.join(map(str, SNAP_MOBS))))
    items = db('SELECT %s FROM item_proto WHERE vnum IN (%s) ORDER BY vnum;' % (
        ','.join('`%s`' % c for c in Y.COLS), ','.join(map(str, SNAP_ITEMS))))
    free = db('SELECT vnum FROM mob_proto WHERE vnum BETWEEN 4420 AND 4479 UNION ALL '
              'SELECT vnum FROM item_proto WHERE vnum IN (%s);' % ','.join(str(i['vnum']) for i in D.ITEMS_NEW))
    json.dump({'source': 'mt2009plustest world.mob_proto / world.item_proto (gen_worldboss.py --snapshot)',
               'taken_vnums': [int(r['vnum']) for r in free], 'mob_cols': list(COLS), 'mobs': mobs,
               'item_cols': list(Y.COLS), 'items': items},
              open(BASE_JSON, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('snapshot: %d mobs, %d items, taken %s' % (len(mobs), len(items), [r['vnum'] for r in free]))


def q(s):
    return "'" + s.replace('\\', '\\\\').replace("'", "\\'") + "'"


def pl_name(v, name):
    if len(name.encode('cp1250')) <= 24:
        return name
    s = D.SHORT[v]
    assert len(s.encode('cp1250')) <= 24, (v, s)
    return s


def flag_join(*parts):
    out = []
    for p in parts:
        for f in (p or '').split(','):
            f = f.strip()
            if f and f not in out:
                out.append(f)
    return ','.join(out)


def scale(x, pct):
    return int(round(float(x) * pct))


def mob_rows(base):
    rows = []
    elements = {}
    for b in D.BOSSES:
        src = dict(base[b['base']])
        st = base[D.STAT_TEMPLATE_BOSS]
        r = dict(src)
        race = D.RACE[b['race']]
        r.update(vnum=b['vnum'], name=Y.ascii_name(pl_name(b['vnum'], b['name'])).replace('(BS)', '(WB)'),
                 locale_name=pl_name(b['vnum'], b['name']), rank=5, level=D.BOSS_LEVEL, ai_flag=D.BOSS_AI,
                 setRaceFlag=flag_join(race, D.ELEMENT_NAME[b['element']]), setImmuneFlag=D.BOSS_IMMUNE,
                 max_hp=D.BOSS_HP_PROTO, regen_cycle=0, regen_percent=0, gold_min=0, gold_max=0, exp=0, drop_item=0,
                 resurrection_vnum=0, summon=0, polymorph_item=0)
        for k in ('st', 'dx', 'ht', 'iq', 'damage_min', 'damage_max', 'def', 'dam_multiply'):
            r[k] = st[k]
        rows.append(r)
        elements[b['vnum']] = D.ATT[b['element']]
        for v, name, lvl, rank, mbase in b['minions']:
            src = dict(base[mbase])
            t = base[D.MINION_TEMPLATE[rank]]
            g = 1.0 + 0.02 * (lvl - int(t['level']))
            r = dict(src)
            r.update(vnum=v, name=Y.ascii_name(pl_name(v, name)).replace('(BS)', '(WB)'), locale_name=pl_name(v, name),
                     rank=rank, level=lvl, ai_flag=flag_join('AGGR', ','.join(
                         f for f in src['ai_flag'].split(',') if f.strip() not in ('REVIVE', 'AGGR'))),
                     setRaceFlag=flag_join(D.RACE[D.MINION_RACE[v]] if v in D.MINION_RACE else race,
                                           D.ELEMENT_NAME[b['element']]),
                     setImmuneFlag=flag_join(src['setImmuneFlag'], D.MINION_IMMUNE),
                     gold_min=0, gold_max=0, exp=0, drop_item=0, resurrection_vnum=0, summon=0, polymorph_item=0)
            for k in ('st', 'dx', 'ht', 'iq', 'regen_cycle', 'regen_percent', 'dam_multiply'):
                r[k] = t[k]
            hp = scale(t['max_hp'], g * (D.MINION_RANK4_HP if rank == 4 else 1.0))
            r.update(damage_min=scale(t['damage_min'], g), damage_max=scale(t['damage_max'], g),
                     max_hp=hp, **{'def': scale(t['def'], g)})
            rows.append(r)
            elements[v] = D.ATT[b['element']]
    return rows, elements


NUMERIC_STR = ('name', 'locale_name', 'size', 'ai_flag', 'setRaceFlag', 'setImmuneFlag', 'folder')


def mob_sql_tuple(r):
    out = []
    for c in COLS:
        v = r[c]
        if c in NUMERIC_STR:
            out.append(q(str(v)))
        elif c == 'dam_multiply':
            out.append('%.1f' % float(v))
        else:
            out.append(str(int(float(v))))
    return out


def item_rows(base):
    items = []
    for it in D.ITEMS_NEW:
        r = dict(base[it['src']])
        r.update(vnum=it['vnum'], name=Y.ascii_name(it['name']), locale_name=it['name'])
        if 'value0' in it:
            r['value0'] = it['value0']
        for k in Y.COLS:
            if k not in ('name', 'locale_name', 'immuneflag'):
                r[k] = int(float(r[k]))
        r.update(status=Y.ST, desc=it['desc'], icon=it['icon'], list_type='ETC',
                 model='d:/ymir work/item/etc/boss_box.gr2' if it['vnum'] == D.SKRZYNKA_TAJEMNIC else '')
        items.append(r)
    return items


SQL_HEAD = """-- %(m)s: Boss Swiata (World Boss, the owner's decision of 21 October 2026 - the pl-wiki's event). GENERATED by
-- tools/worldboss/gen_worldboss.py - do not edit, rerun it. Every start (apply.sh, after zywioly_moby.sql), idempotent.
--  * world.mob_proto (INSERT IGNORE - a row the operator changed is kept): the six bosses of the wiki (GF's numbers,
--    the client's npclist has their "w_*" models twice the size) and the five men each summons at 75/50/25 %% of its
--    health. Level 120, rank 5, Basis-EXP 0, no yang, no drop, no regeneration (the wiki); the bosses' strength is
--    Bagjanamu's (6408), their health in the proto the full one (the game sets it at a spawn: worldboss_config);
--    a man takes his model's monster (folder, AI, attack) and the strength of Zaklety Las' men of his rank, grown 2 %%
--    a level to the wiki's level.
--  * their element and race (UPDATE, after zywioly_moby.sql clears the element bits of what it does not list).
--  * world.item_proto (INSERT IGNORE): Skrzynka Tajemnic (38015, GF's number - a copy of Zagadkowa Szkatulka 50033),
--    Kupon SM (20) 80031 and Kupon SM (10) 80032 (copies of Kupon SM (50) 80017 - the wiki's Kupon TM: this world
--    has no Tiger Coins; worldboss_kupony.quest cashes them).
--  * the event's tables in player (playerbot_worldboss.h): worldboss_config, worldboss_state, worldboss_damage,
--    worldboss_reward, worldboss_points.
SET NAMES utf8mb4;

"""

TABLES = """
-- the operator's settings (Seban Panel "Boss Swiata"; the game reads them every 30 s)
CREATE TABLE IF NOT EXISTS player.worldboss_config (
  id TINYINT UNSIGNED NOT NULL PRIMARY KEY,
  mode TINYINT UNSIGNED NOT NULL DEFAULT 1 COMMENT '0 off, 1 always on, 2 only while the scheduler event worldboss runs',
  channel TINYINT UNSIGNED NOT NULL DEFAULT 1,
  break_min SMALLINT UNSIGNED NOT NULL DEFAULT 120 COMMENT 'minutes from a boss appearing to the next (at least 5 after its end)',
  break_max SMALLINT UNSIGNED NOT NULL DEFAULT 120,
  fight_minutes SMALLINT UNSIGNED NOT NULL DEFAULT 45 COMMENT 'the boss escapes after this',
  min_damage INT UNSIGNED NOT NULL DEFAULT 250000 COMMENT 'the least damage for a loot tier',
  mission_damage INT UNSIGNED NOT NULL DEFAULT 100000 COMMENT 'Pokonaj Bossa Swiata: attack +20 % for 3 h, once a day',
  min_level TINYINT UNSIGNED NOT NULL DEFAULT 30,
  hp_full INT UNSIGNED NOT NULL DEFAULT 8000000,
  hp_start_pct TINYINT UNSIGNED NOT NULL DEFAULT 30 COMMENT 'the first bosses are weak (the wiki) ...',
  hp_step_pct TINYINT UNSIGNED NOT NULL DEFAULT 5 COMMENT '... and grow this much a fall, up to 100',
  groups_per_call TINYINT UNSIGNED NOT NULL DEFAULT 6 COMMENT 'groups of five men at 75/50/25 % (the it-wiki: about 10)',
  bots TINYINT UNSIGNED NOT NULL DEFAULT 1 COMMENT 'the bots raid the boss (and rank and get rewards like players)',
  season_weeks TINYINT UNSIGNED NOT NULL DEFAULT 8,
  force_at INT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'the next boss at this epoch (0 = the game draws)',
  force_boss TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '1-6 = that boss, 0 = drawn',
  force_map SMALLINT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'map index, 0 = drawn',
  escape_now INT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'an epoch: the boss standing then escapes',
  season_end_now INT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'an epoch: the season ends then (its rewards given)'
) ENGINE=InnoDB;
INSERT IGNORE INTO player.worldboss_config (id) VALUES (1);
-- MT2009_PLUS_WORLDBOSS_ICON_V1 (the owner, 21 October 2026: "Boss Swiata niech bedzie co 120 minut"): a boss every
-- 120 minutes from the last one's appearance. Once (defaults_rev 0 -> 1): an install still on the first default break
-- (60-120 minutes) moves to 120-120; one the operator changed keeps its own.
ALTER TABLE player.worldboss_config ADD COLUMN IF NOT EXISTS defaults_rev TINYINT UNSIGNED NOT NULL DEFAULT 0
  COMMENT 'the default migrations done (1: the break 60-120 -> 120-120)';
ALTER TABLE player.worldboss_config ALTER COLUMN break_min SET DEFAULT 120, ALTER COLUMN break_max SET DEFAULT 120;
UPDATE player.worldboss_config SET break_min = 120, break_max = 120 WHERE defaults_rev < 1 AND break_min = 60 AND break_max = 120;
UPDATE player.worldboss_config SET defaults_rev = 1 WHERE defaults_rev < 1;
-- the event's state, one row; written by the core that runs the boss (its channel's core of maps 61-64)
CREATE TABLE IF NOT EXISTS player.worldboss_state (
  id TINYINT UNSIGNED NOT NULL PRIMARY KEY,
  serial INT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'one a boss spawned',
  state TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '0 waiting, 1 standing, 2 defeated, 3 escaped',
  boss_vnum INT UNSIGNED NOT NULL DEFAULT 0,
  map_index INT UNSIGNED NOT NULL DEFAULT 0,
  pos_x INT NOT NULL DEFAULT 0,
  pos_y INT NOT NULL DEFAULT 0,
  area VARCHAR(64) NOT NULL DEFAULT '',
  channel TINYINT UNSIGNED NOT NULL DEFAULT 1,
  spawned_at INT UNSIGNED NOT NULL DEFAULT 0,
  fight_end INT UNSIGNED NOT NULL DEFAULT 0,
  ended_at INT UNSIGNED NOT NULL DEFAULT 0,
  next_at INT UNSIGNED NOT NULL DEFAULT 0,
  falls INT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'bosses defeated (the health grows with them)',
  hp_max INT UNSIGNED NOT NULL DEFAULT 0,
  hp_pct TINYINT UNSIGNED NOT NULL DEFAULT 0,
  season INT UNSIGNED NOT NULL DEFAULT 1,
  season_end INT UNSIGNED NOT NULL DEFAULT 0,
  updated_at INT UNSIGNED NOT NULL DEFAULT 0
) ENGINE=InnoDB;
INSERT IGNORE INTO player.worldboss_state (id) VALUES (1);
-- a defeated boss's ranking: the players with the least damage or more, on the map at the fall
CREATE TABLE IF NOT EXISTS player.worldboss_damage (
  serial INT UNSIGNED NOT NULL,
  pid INT UNSIGNED NOT NULL,
  pos SMALLINT UNSIGNED NOT NULL,
  tier TINYINT UNSIGNED NOT NULL,
  damage BIGINT UNSIGNED NOT NULL,
  name VARCHAR(24) NOT NULL DEFAULT '',
  guild_id INT UNSIGNED NOT NULL DEFAULT 0,
  guild_name VARCHAR(24) NOT NULL DEFAULT '',
  empire TINYINT UNSIGNED NOT NULL DEFAULT 0,
  level TINYINT UNSIGNED NOT NULL DEFAULT 0,
  boss_vnum INT UNSIGNED NOT NULL DEFAULT 0,
  at INT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (serial, pid),
  KEY serial_pos (serial, pos)
) ENGINE=InnoDB;
-- what a player collects with "Odbierz nagrode": kind 0 a loot tier (until the next boss), 1 the season's
-- character prize, 2 the season's guild prize (both until taken), 3 the daily "Pokonaj Bossa Swiata" (until the next
-- boss); state 0 waiting, 1 taken, 2 lost
CREATE TABLE IF NOT EXISTS player.worldboss_reward (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pid INT UNSIGNED NOT NULL,
  kind TINYINT UNSIGNED NOT NULL,
  serial INT UNSIGNED NOT NULL DEFAULT 0,
  season INT UNSIGNED NOT NULL DEFAULT 0,
  tier TINYINT UNSIGNED NOT NULL DEFAULT 0,
  pos SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  items VARCHAR(255) NOT NULL DEFAULT '' COMMENT 'vnum:count:days,...',
  buff_drop TINYINT UNSIGNED NOT NULL DEFAULT 0,
  buff_attack TINYINT UNSIGNED NOT NULL DEFAULT 0,
  created INT UNSIGNED NOT NULL DEFAULT 0,
  day INT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'kind 3: the server day (YYYYMMDD)',
  state TINYINT UNSIGNED NOT NULL DEFAULT 0,
  taken_at INT UNSIGNED NOT NULL DEFAULT 0,
  KEY pid_state (pid, state),
  KEY serial_kind (serial, kind)
) ENGINE=InnoDB;
-- MT2009_PLUS_WORLDBOSS_ICON_V1: every core looks for its bots' waiting rewards (BotClaims, every 30 s)
ALTER TABLE player.worldboss_reward ADD INDEX IF NOT EXISTS state_pid (state, pid);
-- rank points (10/5/2/1 by tier) per season, character and the guild the character was in when it earned them
CREATE TABLE IF NOT EXISTS player.worldboss_points (
  season INT UNSIGNED NOT NULL,
  pid INT UNSIGNED NOT NULL,
  guild_id INT UNSIGNED NOT NULL DEFAULT 0,
  name VARCHAR(24) NOT NULL DEFAULT '',
  guild_name VARCHAR(24) NOT NULL DEFAULT '',
  empire TINYINT UNSIGNED NOT NULL DEFAULT 0,
  points INT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (season, pid, guild_id),
  KEY season_guild (season, guild_id)
) ENGINE=InnoDB;
"""


def write_sql(mrows, elements, items):
    L = [SQL_HEAD % dict(m=M)]
    L.append('INSERT IGNORE INTO world.mob_proto (%s) VALUES' % ','.join('`%s`' % c for c in COLS))
    L.append(',\n'.join('(%s)' % ','.join(mob_sql_tuple(r)) for r in mrows) + ';')
    L.append('')
    by = {}
    for v, e in elements.items():
        by.setdefault(e, []).append(v)
    L.append('-- the element (zywioly_moby.sql clears bits 11-16 of every monster it does not list - so after it)')
    for e, vs in sorted(by.items()):
        L.append('UPDATE world.mob_proto SET setRaceFlag = ((setRaceFlag + 0) & ~%d) | %d WHERE vnum IN (%s);'
                 % (D.ELEMENT_BITS, e, ','.join(map(str, sorted(vs)))))
    L.append('')
    L.append('INSERT IGNORE INTO world.item_proto (%s) VALUES' % ','.join('`%s`' % c for c in Y.COLS))
    L.append(',\n'.join(Y.sqlrow(i) for i in items) + ';')
    L.append(TABLES)
    with open(SQL_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L))


def area_name(name, x, y):
    t = D.MAP_CELLS / 3.0
    col = 0 if x < t else (1 if x < 2 * t else 2)
    row = 0 if y < t else (1 if y < 2 * t else 2)
    part = [['północno-zachodnia', 'północna', 'północno-wschodnia'],
            ['zachodnia', 'środkowa', 'wschodnia'],
            ['południowo-zachodnia', 'południowa', 'południowo-wschodnia']][row][col]
    return '%s (%s część)' % (name, part)


def write_game():
    os.makedirs(GAME_DIR, exist_ok=True)
    L = ['# %s - Boss Swiata. GENERATED by tools/worldboss/gen_worldboss.py - do not edit, rerun it.' % M,
         '# Read by playerbot_worldboss.h (<locale>/worldboss.txt) at the boot and by "/worldboss przeladuj".',
         '# Tab-separated; text in CP1250 (the notices).',
         '#   boss <vnum> <men vnums,> <name>',
         '#   spot <map> <x> <y> <area>            the map\'s local cells',
         '#   tier <n> <first rank> <last rank, 0 none> <rank points> <drop buff %> <buff seconds> <vnum:count,...>',
         '#   mission <attack %> <seconds>',
         '#   season_char|season_guild <first> <last> <vnum:count:days,...>',
         '#   season_weeks <n>']
    for b in D.BOSSES:
        L.append('boss\t%d\t%s\t%s' % (b['vnum'], ','.join(str(m[0]) for m in b['minions']), b['name']))
    for m, name, spots in D.MAPS:
        for x, y in spots:
            L.append('spot\t%d\t%d\t%d\t%s' % (m, x, y, area_name(name, x, y)))
    for n, a, z, pts, drop, items in D.TIERS:
        L.append('tier\t%d\t%d\t%d\t%d\t%d\t%d\t%s' % (n, a, z, pts, drop, D.DROP_BUFF_SECONDS if drop else 0,
                                                       ','.join('%d:%d' % i for i in items)))
    L.append('mission\t%d\t%d' % (D.MISSION_ATTACK_PCT, D.MISSION_SECONDS))
    for kind, rows in (('season_char', D.SEASON_CHAR), ('season_guild', D.SEASON_GUILD)):
        for a, z, items in rows:
            L.append('%s\t%d\t%d\t%s' % (kind, a, z, ','.join('%d:%d:%d' % i for i in items)))
    L.append('season_weeks\t%d' % D.SEASON_WEEKS)
    with open(os.path.join(GAME_DIR, 'worldboss.txt'), 'wb') as f:
        f.write(('\r\n'.join(L) + '\r\n').encode('cp1250'))
    G = ['# %s: Skrzynka Tajemnic (38015) - "Zawiera losowy rzadki przedmiot." (the pl-wiki\'s list, equal shares;' % M,
         '# Barwnik zloty metalik is not in this world). GENERATED by tools/worldboss/gen_worldboss.py.',
         'Group\tworldboss_skrzynka_tajemnic', '{', '\tVnum\t%d' % D.SKRZYNKA_TAJEMNIC]
    for i, (v, n) in enumerate(D.MYSTERY, 1):
        G.append('\t%d\t%d\t1\t10 -- %s' % (i, v, Y.ascii_name(n)))
    G.append('}')
    with open(os.path.join(GAME_DIR, 'special_item_group.worldboss.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(G) + '\n')


def write_client(mrows, elements, items):
    keys = ('vnum', 'name', 'locale_name', 'type', 'subtype', 'stack', 'weight', 'size', 'antiflag', 'flag',
            'wearflag', 'gold', 'shop_buy_price', 'refined_vnum', 'refine_set', 'magic_pct', 'specular', 'socket_pct',
            'limittype0', 'limitvalue0', 'limittype1', 'limitvalue1', 'applytype0', 'applyvalue0', 'applytype1',
            'applyvalue1', 'applytype2', 'applyvalue2', 'value0', 'value1', 'value2', 'value3', 'value4', 'value5')

    def lst(i):
        return '%d\t%s\t%s' % (i['vnum'], i['list_type'], i['icon']) + ('\t' + i['model'] if i['model'] else '')
    # the client's flag names (shipdefense's RACE): the SET's 'SAVAGE' / 'ATT_TEMPLE' are bits 11 / 14 - lightning / wind
    crows = []
    for r in mrows:
        c = dict(r)
        c['setRaceFlag'] = ','.join({'SAVAGE': 'ATT_ELEC', 'ATT_TEMPLE': 'ATT_WIND'}.get(f, f)
                                    for f in r['setRaceFlag'].split(',') if f)
        crows.append(c)
    out = {'cols': list(COLS), 'rows': [mob_sql_tuple(r) for r in crows],
           'elements': dict((str(v), e) for v, e in elements.items()),
           'models': dict((str(b['vnum']), b['model']) for b in D.BOSSES),
           'items': [dict((k, i[k]) for k in keys) for i in items],
           'item_list': dict((str(i['vnum']), lst(i)) for i in items),
           'itemdesc': dict((str(i['vnum']), '%d\t%s\t%s' % (i['vnum'], i['locale_name'], Y.client_desc(i)))
                            for i in items),
           'icons_added': {'icon/item/38015.tga': 'icon/item/38015.tga'},
           'bosses': [dict(vnum=b['vnum'], name=b['name'], minions=[m[0] for m in b['minions']]) for b in D.BOSSES]}
    with open(JSON_OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=0)
        f.write('\n')


def main():
    if '--snapshot' in sys.argv:
        snapshot()
    snap = json.load(open(BASE_JSON, encoding='utf-8'))
    base = dict((int(r['vnum']), r) for r in snap['mobs'])
    ibase = dict((int(r['vnum']), r) for r in snap['items'])
    missing = [v for v in SNAP_MOBS if v not in base] + [v for v in SNAP_ITEMS if v not in ibase]
    assert not missing, 'not in base_rows.json (run --snapshot): %s' % missing
    new_vnums = set([b['vnum'] for b in D.BOSSES] + [m[0] for b in D.BOSSES for m in b['minions']] +
                    [i['vnum'] for i in D.ITEMS_NEW])
    clash = sorted(set(snap.get('taken_vnums', [])) & new_vnums)
    assert not clash, 'already in the world: %s' % clash
    mrows, elements = mob_rows(base)
    items = item_rows(ibase)
    for r in mrows:
        assert len(r['locale_name'].encode('cp1250')) <= 24, r['vnum']
    write_sql(mrows, elements, items)
    write_game()
    write_client(mrows, elements, items)
    print('mob rows %d, items %d -> %s, %s, %s' % (len(mrows), len(items), os.path.relpath(SQL_OUT, REPO),
                                                 os.path.relpath(GAME_DIR, REPO), os.path.relpath(JSON_OUT, REPO)))


if __name__ == '__main__':
    main()
