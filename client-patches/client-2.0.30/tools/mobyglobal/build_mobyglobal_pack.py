# -*- coding: utf-8 -*-
# MT2009_PLUS_MOBY_GLOBAL_V1 (client data) - the monsters before Yohara as on the global server (the owner, 20 October
# 2026; server side: tools/ymoby_arkusz/gen_moby_global.py -> mariadb/playerbot/moby_global.sql). The client shows a
# monster's level (and the HP / stats the target window and the drop wiki read) from its own gamedata/mob_proto, so
# the records of the changed monsters take the same values: tools/ymoby_arkusz/moby_global_client.json
# ({vnum: {column: the new value}}): level, HP, EXP, defence, STR/DEX/VIT/INT, damage, speeds, regeneration, the
# effects' chances, the eleven resistances; ai_flag / setImmuneFlag - only the bits the server file changes
# (AGGR BERSERK STONESKIN GODSPEED DEATHBLOW REVIVE COWARD / STUN SLOW CURSE POISON TERROR); setRaceFlag:<RACE> - the
# race bit added (the element bits 11-16 stay the client's). A vnum the client lacks is reported, not added.
# Run on the same OUT as the other builders, after every step that writes gamedata/mob_proto (clientY.sh: after
# yfinal, before protoglobal):
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/mobyglobal/build_mobyglobal_pack.py \
#     $C/azbase $C/out/pack > $C/mobyglobal.json
# --check measures only. Idempotent: a second run reports "unchanged".
import json
import os
import struct
import sys
import zlib

sys.path.insert(0, '/opt/metin2/cache/c36')
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..', 'tools', 'ymoby_arkusz', 'moby_global_client.json'))
MOB_KEY = (4813894, 18955, 552631, 6822045)
RECORD = 256
NAME = 'gamedata/mob_proto'
# column -> (struct format, offset) of the 256-byte record (patch_shipdefense_client.mob_record)
FIELD = {
    'level': ('<B', 57), 'exp': ('<I', 67), 'max_hp': ('<I', 71), 'regen_cycle': ('<B', 75),
    'regen_percent': ('<B', 76), 'def': ('<H', 77), 'st': ('<B', 91), 'dx': ('<B', 92), 'ht': ('<B', 93),
    'iq': ('<B', 94), 'damage_min': ('<I', 95), 'damage_max': ('<I', 99), 'attack_speed': ('<h', 103),
    'move_speed': ('<h', 105),
}
for _i, _c in enumerate(('enchant_curse', 'enchant_slow', 'enchant_poison', 'enchant_stun', 'enchant_critical',
                         'enchant_penetrate')):
    FIELD[_c] = ('<b', 112 + _i)
for _i, _c in enumerate(('resist_sword', 'resist_twohand', 'resist_dagger', 'resist_bell', 'resist_fan', 'resist_bow',
                         'resist_fire', 'resist_elect', 'resist_magic', 'resist_wind', 'resist_poison')):
    FIELD[_c] = ('<b', 118 + _i)
AI = ['AGGR', 'NOMOVE', 'COWARD', 'NOATTSHINSU', 'NOATTCHUNJO', 'NOATTJINNO', 'ATTMOB', 'BERSERK', 'STONESKIN', 'GODSPEED',
      'DEATHBLOW', 'REVIVE']
RACE = ['ANIMAL', 'UNDEAD', 'DEVIL', 'HUMAN', 'ORC', 'MILGYO', 'INSECT', 'FIRE', 'ICE', 'DESERT', 'TREE']
IMMUNE = ['STUN', 'SLOW', 'FALL', 'CURSE', 'POISON', 'TERROR', 'REFLECT']
MANAGED = {'ai_flag': (79, AI, ['AGGR', 'BERSERK', 'STONESKIN', 'GODSPEED', 'DEATHBLOW', 'REVIVE', 'COWARD']),
           'setImmuneFlag': (87, IMMUNE, ['STUN', 'SLOW', 'CURSE', 'POISON', 'TERROR'])}


def patch(rec, want):
    r = bytearray(rec)
    for c, val in want.items():
        if c in FIELD:
            fmt, off = FIELD[c]
            struct.pack_into(fmt, r, off, val)
        elif c in MANAGED:
            off, names, keys = MANAGED[c]
            new = set(x for x in val.split(',') if x)
            cur = struct.unpack_from('<I', r, off)[0]
            for k in keys:
                bit = 1 << names.index(k)
                cur = (cur | bit) if k in new else (cur & ~bit)
            struct.pack_into('<I', r, off, cur)
        elif c.startswith('setRaceFlag:'):
            cur = struct.unpack_from('<I', r, 83)[0]
            if not cur & 0x7ff:
                struct.pack_into('<I', r, 83, cur | (1 << RACE.index(c.split(':')[1])))
        else:
            raise SystemExit('mobyglobal: unknown column %s' % c)
    return bytes(r)


def make(b):
    import m2pack
    magic, cnt, esize = struct.unpack_from('<4sII', b, 0)
    assert magic == b'MMPT', magic
    raw = m2pack.mcoz_decode(b[12:12 + esize], MOB_KEY)
    assert len(raw) == cnt * RECORD, (len(raw), cnt)
    recs = [raw[i * RECORD:(i + 1) * RECORD] for i in range(cnt)]
    data = json.load(open(DATA))
    report = dict(monsters=len(data), changed=0, same=0, missing=[])
    seen = set()
    for i, rec in enumerate(recs):
        v = str(struct.unpack_from('<I', rec, 0)[0])
        if v in data:
            seen.add(v)
            new = patch(rec, data[v])
            if new != rec:
                recs[i] = new
                report['changed'] += 1
            else:
                report['same'] += 1
    report['missing'] = sorted(int(v) for v in data if v not in seen)
    blob = m2pack.mcoz_encode(b''.join(recs), MOB_KEY)
    return struct.pack('<4sII', b'MMPT', cnt, len(blob)) + blob, report


def main():
    import m2pack
    import packlib
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    check = '--check' in sys.argv
    base, out = args[:2]
    rd = packlib.rd
    src = out if os.path.exists(os.path.join(out, 'gamedata.index')) else base
    f, v, ents = m2pack.read_index(os.path.join(src, 'gamedata.index'))
    dat = rd(os.path.join(src, 'gamedata.data'))
    have = dict((e['name'], e) for e in ents)
    old = m2pack.read_entry(dat, have[NAME])
    new, report = make(old)
    if report['changed'] == 0:
        report['gamedata'] = 'unchanged'
    elif check:
        report['gamedata'] = 'would replace %s' % NAME
    else:
        tmp_i, tmp_d = os.path.join(out, 'gamedata.index.mg'), os.path.join(out, 'gamedata.data.mg')
        r = packlib.repack_add_typed(os.path.join(src, 'gamedata.index'), os.path.join(src, 'gamedata.data'),
                                     {NAME: new}, {}, tmp_i, tmp_d, ents[-1]['raw'])
        os.replace(tmp_i, os.path.join(out, 'gamedata.index'))
        os.replace(tmp_d, os.path.join(out, 'gamedata.data'))
        f, v, nw = m2pack.read_index(os.path.join(out, 'gamedata.index'))
        nd = rd(os.path.join(out, 'gamedata.data'))
        for e in nw:
            assert zlib.crc32(nd[e['pos']:e['pos'] + e['size']]) & 0xffffffff == e['dcrc'], e['name']
            got = m2pack.read_entry(nd, e)
            if e['name'] == NAME:
                assert got == new, NAME
            else:
                assert got == m2pack.read_entry(dat, have[e['name']]), e['name']
        # read back: a second pass changes nothing
        assert make(new)[1]['changed'] == 0
        report['gamedata'] = dict(old=r[0], added=r[1], replaced=r[2], entries=len(nw))
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
