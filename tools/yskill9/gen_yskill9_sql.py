#!/usr/bin/env python3
"""gen_yskill9_sql.py - writes linux-port/docker/mariadb/playerbot/yskill9.sql (MT2009_PLUS_SKILL9_V1, the 9th skills
of Yohara; server-patches/skill9/README.md).

The rows are Owsap v6.2.6's skill_proto 176-182 (Server/db/data/player.sql - the GF formulas: the pl wiki's numbers
come out of them, e.g. Tarcza Eteru 390/426/451/486 s cooldown = 386+80*k, 0/9/15/23 % = 0.4*k+18*k) in our
columns (setAffectFlag3), with:
  - szPointOn2 'NONE' instead of 'HIT_PCT' (Bonus Precyzji: our engine has no precision point - its polys stay as
    the record of it, inert; Meteor's PointPoly2/DurationPoly2 are its fire amount / chance, ATTACK_FIRE_CONT);
  - setAffectFlag* 'NONE' (Owsap's '' is no member of our enum), szPointOn3 'NONE';
  - Tarcza Eteru's PARTY flag: world.skill_proto.setFlag gets the members 'ATTACK_BLEEDING' (bit 27) and 'PARTY'
    (bit 28 = SKILL_FLAG_PARTY, ENABLE_SKILL_FLAG_PARTY) when it has none - the db core reads setFlag+0.
183 (Burza Szponow) is the Lycan's: no Lycan, no row. Idempotent: the rows are written whole every run
(INSERT ... ON DUPLICATE KEY UPDATE), the set is widened once.
    python3 tools/yskill9/gen_yskill9_sql.py
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', '..', 'linux-port', 'docker', 'mariadb', 'playerbot', 'yskill9.sql')

import sys
sys.path.insert(0, HERE)
from yskill9_data import COLS, ROWS  # noqa: E402


def q(v):
    if isinstance(v, int):
        return str(v)
    return "'" + v.replace("\\", "\\\\").replace("'", "''") + "'"


def main():
    out = []
    out.append('-- MT2009_PLUS_SKILL9_V1: the 9th skills of Yohara - skill_proto 176-182 (tools/yskill9/gen_yskill9_sql.py;')
    out.append('-- server-patches/skill9/README.md). Idempotent: the set is widened once, the rows are written whole every run.')
    out.append('-- Tarcza Eteru needs SKILL_FLAG_PARTY (bit 28): setFlag gets ATTACK_BLEEDING (27) and PARTY (28) when it has no PARTY;')
    out.append("-- any other shape of the set stops the script (the db core reads setFlag+0 - a member in another place moves the bits).")
    out.append("SET @yskill9_t := (SELECT COLUMN_TYPE FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = 'world' AND TABLE_NAME = 'skill_proto' AND COLUMN_NAME = 'setFlag');")
    out.append("SET @yskill9_sql := IF(@yskill9_t LIKE '%''PARTY''%', 'DO 0',")
    out.append("    IF(@yskill9_t LIKE '%,''THIRD_POINT_SELFONLY'')',")
    out.append("       CONCAT('ALTER TABLE world.skill_proto MODIFY setFlag ', LEFT(@yskill9_t, LENGTH(@yskill9_t) - 1), ',''ATTACK_BLEEDING'',''PARTY'') DEFAULT ''''')," )
    out.append("       'SIGNAL SQLSTATE ''45000'' SET MESSAGE_TEXT = ''yskill9: world.skill_proto.setFlag has an unexpected shape'''));")
    out.append('PREPARE yskill9_stmt FROM @yskill9_sql;')
    out.append('EXECUTE yskill9_stmt;')
    out.append('DEALLOCATE PREPARE yskill9_stmt;')
    out.append('')
    cols = ', '.join(COLS)
    upd = ', '.join('%s = VALUES(%s)' % (c, c) for c in COLS[1:])
    for r in ROWS:
        assert len(r) == len(COLS), (r[0], len(r))
        out.append('INSERT INTO world.skill_proto (%s)\n  VALUES (%s)\n  ON DUPLICATE KEY UPDATE %s;' % (
            cols, ', '.join(q(v) for v in r), upd))
    out.append('')
    out.append("-- the check: seven rows, Tarcza Eteru with PARTY")
    out.append("SELECT IF((SELECT COUNT(*) FROM world.skill_proto WHERE dwVnum BETWEEN 176 AND 182) = 7 AND (SELECT FIND_IN_SET('PARTY', setFlag) FROM world.skill_proto WHERE dwVnum = 182) > 0, 'yskill9 ok', NULL) INTO @yskill9_ok;")
    out.append("SET @yskill9_sql := IF(@yskill9_ok IS NULL, 'SIGNAL SQLSTATE ''45000'' SET MESSAGE_TEXT = ''yskill9: rows missing''', 'DO 0');")
    out.append('PREPARE yskill9_stmt FROM @yskill9_sql;')
    out.append('EXECUTE yskill9_stmt;')
    out.append('DEALLOCATE PREPARE yskill9_stmt;')
    open(OUT, 'w', newline='\n').write('\n'.join(out) + '\n')
    print('written', os.path.normpath(OUT), len(ROWS), 'rows')


if __name__ == '__main__':
    main()
