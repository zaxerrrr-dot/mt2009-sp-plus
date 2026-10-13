# -*- coding: utf-8 -*-
# MT2009_PLUS_SHIP_DEFENSE_V1 (client data) - Obrona Statku (Hydra, map 367) in the client's gamedata:
#
#   mob_proto     the 24 races of the ship (3949-3965, 3970, 20432-20437) as linux-port/docker/mariadb/playerbot/
#                 shipdefense.sql writes them (read from that file: names, Polish names, type/rank/battle/level, flags,
#                 stats, HP, resists) on the record of 101 (monsters, stones) or 9012 (NPC), the zodiak layout -
#                 client 2.0.64 has none of them (the target window would show no name, no level);
#   atlasinfo.txt "metin2_map_defensewave 128000 486400 3 3" (= the server's Setting.txt; overlaps none of ours).
# npclist.txt has the races already (client 2.0.61: 3949-3970, 20432-20437, the defensewave_* aliases).
# APPEND ONLY: a vnum/map already there with other content is a collision and stops the run before anything is
# written. Idempotent: a second run changes nothing.
#
# Both files live in the "gamedata" pack (gamedata/mob_proto, gamedata/atlasinfo.txt). Run on plain copies, in the
# m2pack-lzo image (MCOZ):
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/shipdefense/patch_shipdefense_client.py <mob_proto> [<atlasinfo.txt>] [--check]
# build_shipdefense_packs.py calls the same functions on the gamedata pack.
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
SQL = os.path.join(HERE, '..', '..', '..', '..', 'linux-port', 'docker', 'mariadb', 'playerbot', 'shipdefense.sql')
MOB_KEY = (4813894, 18955, 552631, 6822045)
MOB_RECORD = 256
ATLAS = ['metin2_map_defensewave\t128000\t486400\t3\t3']
AI = ['AGGR', 'NOMOVE', 'COWARD', 'NOATTSHINSU', 'NOATTCHUNJO', 'NOATTJINNO', 'ATTMOB', 'BERSERK', 'STONESKIN', 'GODSPEED',
      'DEATHBLOW', 'REVIVE', 'IGNORE_LAST_ATTACK', 'NO_WANDER', 'SEE_OTHER_NPC', 'RETURN_LASTATTACK_POS', 'LOOSE_AGGRO_ON_DISTANCE']
RACE = ['ANIMAL', 'UNDEAD', 'DEVIL', 'HUMAN', 'ORC', 'MILGYO', 'INSECT', 'FIRE', 'ICE', 'DESERT', 'TREE',
        'ATT_ELEC', 'ATT_FIRE', 'ATT_ICE', 'ATT_WIND', 'ATT_EARTH', 'ATT_DARK']
IMMUNE = ['STUN', 'SLOW', 'FALL', 'CURSE', 'POISON', 'TERROR', 'REFLECT']
SIZE = {'': 0, 'NONE': 0, 'SMALL': 1, 'MEDIUM': 2, 'BIG': 3}


class Collision(Exception):
    pass


def _values(s):
    """the tuples of one INSERT ... VALUES list: strings ('' escapes \\'), numbers; "-- ..." comments skipped"""
    rows, row, i, n = [], None, 0, len(s)
    while i < n:
        c = s[i]
        if c == '-' and s.startswith('--', i):
            i = s.find('\n', i)
            i = n if i < 0 else i
        elif c == '(':
            row = []
            i += 1
        elif c == ')':
            rows.append(row)
            row = None
            i += 1
        elif c == ';' and row is None:
            break
        elif row is not None and c == "'":
            j, out = i + 1, []
            while s[j] != "'":
                if s[j] == '\\':
                    j += 1
                out.append(s[j])
                j += 1
            row.append(''.join(out))
            i = j + 1
        elif row is not None and (c.isdigit() or c in '-.'):
            m = re.match(r'-?[0-9.]+', s[i:])
            row.append(float(m.group(0)) if '.' in m.group(0) else int(m.group(0)))
            i += len(m.group(0))
        else:
            i += 1
    return rows


def sql_mobs(path=SQL):
    t = open(path, encoding='utf-8').read()
    m = re.search(r'INSERT IGNORE INTO world\.mob_proto \(([^)]*)\) VALUES', t)
    cols = [c.strip().strip('`') for c in m.group(1).split(',')]
    mobs = []
    for r in _values(t[m.end():]):
        assert len(r) == len(cols), r[:3]
        mobs.append(dict(zip(cols, r)))
    assert len(mobs) == 24, len(mobs)
    return mobs


def fixed(text, size):
    b = text.encode('cp1250')
    assert len(b) < size, text
    return b + b'\0' * (size - len(b))


def bits(s, names):
    return sum(1 << names.index(x.strip()) for x in s.split(',') if x.strip())


def mob_record(w, tmpl):
    r = bytearray(tmpl)
    struct.pack_into('<I', r, 0, w['vnum'])
    r[4:29] = fixed(w['name'][:24], 25)
    r[29:54] = fixed(w['locale_name'], 25)
    struct.pack_into('<5B', r, 54, w['type'], w['rank'], w['battle_type'], w['level'], SIZE[w['size']])
    struct.pack_into('<4I', r, 59, w['gold_min'], w['gold_max'], w['exp'], w['max_hp'])
    struct.pack_into('<BBH', r, 75, w['regen_cycle'], w['regen_percent'], w['def'])
    struct.pack_into('<3I', r, 79, bits(w['ai_flag'], AI), bits(w['setRaceFlag'], RACE), bits(w['setImmuneFlag'], IMMUNE))
    struct.pack_into('<4B', r, 91, w['st'], w['dx'], w['ht'], w['iq'])
    struct.pack_into('<2I', r, 95, w['damage_min'], w['damage_max'])
    struct.pack_into('<2h', r, 103, w['attack_speed'], w['move_speed'])
    struct.pack_into('<BHH', r, 107, w['aggressive_hp_pct'], w['aggressive_sight'], w['attack_range'])
    struct.pack_into('<6b', r, 112, w['enchant_curse'], w['enchant_slow'], w['enchant_poison'], w['enchant_stun'],
                     w['enchant_critical'], w['enchant_penetrate'])
    struct.pack_into('<11b', r, 118, w['resist_sword'], w['resist_twohand'], w['resist_dagger'], w['resist_bell'],
                     w['resist_fan'], w['resist_bow'], w['resist_fire'], w['resist_elect'], w['resist_magic'],
                     w['resist_wind'], w['resist_poison'])
    struct.pack_into('<2I', r, 129, w['resurrection_vnum'], w['drop_item'])
    struct.pack_into('<3B', r, 137, w['mount_capacity'], w['on_click'], w['empire'])
    r[140:204] = fixed(w['folder'], 64)
    return bytes(r)


def mob_proto(b):
    import m2pack
    magic, cnt, esize = struct.unpack_from('<4sII', b, 0)
    assert magic == b'MMPT', magic
    raw = m2pack.mcoz_decode(b[12:12 + esize], MOB_KEY)
    assert len(raw) == cnt * MOB_RECORD, (len(raw), cnt)
    recs = dict((struct.unpack_from('<I', raw, i * MOB_RECORD)[0], raw[i * MOB_RECORD:(i + 1) * MOB_RECORD])
                for i in range(cnt))
    want = dict((w['vnum'], mob_record(w, recs[101] if w['type'] in (0, 2) else recs[9012])) for w in sql_mobs())
    clash = [v for v, r in sorted(want.items()) if v in recs and recs[v] != r]
    if clash:
        raise Collision('mob_proto: %d vnum(s) already in the client with other content: %s' % (len(clash), clash))
    new = dict((v, r) for v, r in want.items() if v not in recs)
    if not new:
        return b, 0
    recs.update(new)
    out = b''.join(recs[v] for v in sorted(recs))
    blob = m2pack.mcoz_encode(out, MOB_KEY)
    return struct.pack('<4sII', b'MMPT', len(recs), len(blob)) + blob, len(new)


def atlasinfo(b):
    text = b.decode('cp1250')
    nl = '\r\n' if '\r\n' in text else '\n'
    lines = text.split(nl)
    tail = bool(lines) and lines[-1] == ''
    if tail:
        lines.pop()
    have = dict((l.split('\t')[0].strip().lower(), l) for l in lines if l.strip())
    new = []
    for row in ATLAS:
        k = row.split('\t')[0].lower()
        if k in have:
            if have[k].split() != row.split():
                raise Collision('atlasinfo.txt: %s already there as %r' % (k, have[k]))
            continue
        new.append(row)
    if not new:
        return b, 0
    return (nl.join(lines + new + ([''] if tail else []))).encode('cp1250'), len(new)


def main():
    args = [a for a in sys.argv[1:] if a != '--check']
    check = '--check' in sys.argv
    if not 1 <= len(args) <= 2:
        raise SystemExit('usage: patch_shipdefense_client.py <mob_proto> [<atlasinfo.txt>] [--check]')
    for path, fn in zip(args, (mob_proto, atlasinfo)):
        if path == '-':
            continue
        b = open(path, 'rb').read()
        nb, n = fn(b)
        if n and not check:
            open(path, 'wb').write(nb)
        print('%s: %d new%s' % (os.path.basename(path), n, ' (check only)' if check else ''))


if __name__ == '__main__':
    main()
