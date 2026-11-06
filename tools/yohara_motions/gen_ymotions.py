#!/usr/bin/env python3
"""gen_ymotions.py [--check]

MT2009_PLUS_YOHARA_MOTIONS_V1 - the server's motions of the Yohara monsters (the owner's test list of 14 October,
cache/yohara/bledy-3.0.md item 7: "GetMoveMotionSpeed: cannot find motion" for Myr 6719/6720/6722, Troll Zolnierz
6712 and the rest). The game core times moves and attacks by share/data/monster/<mob_proto folder>/motlist.txt and
its .msa files (motion.cpp); a folder that is not there leaves the monster without a move speed (syserr flood, odd
walking). FOLDERS are every folder of the repo's mob_proto rows (linux-port/docker/mariadb/playerbot/*.sql) and of
the test server's syserr of 14 October that the server image had no motlist.txt for, minus those a batch ships
itself (zodiak/data/monster ...) and the static objects with no motion at all (defensewave_woodrepair, ice_keybox,
ICE_lionstone - the GF client has only their model). All of them are Owsap v6.2.6's (share/data/monster: the
official server files) - motlist.txt and the .msa files, nothing else. motlist.txt as Owsap's but for two slips of
the official files (fix_motlist): "normal_attack2msa" (no dot) -> normal_attack2.msa and a name whose case differs
from the file's (hanma_boss back_Standup.msa -> back_standup.msa; Linux is case-sensitive). A line whose .msa the
official folder lacks (snakevalley_pawn back_damage.msa ...) stays - the core reads only WALK/RUN/NORMAL_ATTACK/
SPECIAL* and skips a file it cannot open.

MT2009_PLUS_YONGHAN_SKILL_HIT_V1 (6 November 2026, the second bot analysis, item 11): + ch_general - Dowodca /
General Yonghan (2491/2492) and Huashin (2494/2495). The image's folder carries the client's 24.msa/25.msa (the
SPECIAL motions) without the official server's hit events (MotionEventType 4 with SphereData), so the core had
no skill hit data for them ("UseMobSkill: No skill hit data", ~1 400 a day on the Yohara test) and the generals
never used their two skills. Owsap's files are the official server's (the same motlist.txt; RUN/attack equal).

Writes linux-port/docker/game/ymotions/data/monster/<folder>/ (GENERATED - edit FOLDERS, run it again); the
Dockerfile step "share: Yohara monster motions" copies them (an existing folder of the image is replaced).
"""
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
OWSAP = '/opt/metin2/cache/owsap/Server/Server/share/data/monster'
OUT = os.path.join(REPO, 'linux-port', 'docker', 'game', 'ymotions', 'data', 'monster')

FOLDERS = """
east_earth_general east_earth_king east_earth_knight east_earth_magic east_earth_officer east_earth_soldier
east_earth_soldier2 east_gnoll_hellhound east_gnoll_soldier east_troll_archer east_troll_argus_boss
east_troll_commander east_troll_mage east_troll_warrior east_wl_soldier elemental_pawn_1 elemental_pawn_2
elemental_pawn_3 elemental_pawn_4 elemental_pawn_5 elemental_pawn_6 elemental_soul_6 empire_caocao_boss
empire_gongbing empire_jianbing empire_maobing empire_qiangbing empire_zhangbao_king empire_zhanglu garrison
gnoll_hellhound hanma_boss historian ice_stonepillar icecrystal_valley_boss icecrystal_valley_knight01
icecrystal_valley_knight02 icecrystal_valley_knight03 icecrystal_valley_pawn icecrystal_valley_s_knight
icecrystal_valley_s_pawn king_npc maze_gnoll_boss maze_gnoll_general maze_gnoll_magic maze_gnoll_soldier
maze_keindog_boss maze_keindog_general maze_keindog_magic maze_keindog_soldier maze_keingnoll_boss metinstone_02
metinstone_east metinstone_egg_whitedragon metinstone_snake npc_empirestone okey_npc reddragon_room_box
smhtower_boss smhtower_general smhtower_king smhtower_knight smhtower_magic smhtower_soldier smhtower_soldier2
snake_head_01 snake_head_02 snake_head_03 snake_head_04 snaketemple_boss snaketemple_knight01 snaketemple_knight02
snaketemple_knight03 snaketemple_pawn snaketemple_s_knight snaketemple_s_pawn snakevalley_boss snakevalley_knight
snakevalley_knight02 snakevalley_knight03 snakevalley_pawn snakevalley_s_knight snakevalley_s_pawn starveling
thunder_boss trent_boss trent_boss2 trent_general trent_magic trent_soldier whitedragon_cave_boss
whitedragon_cave_boss2 whitedragon_cave_knight01 whitedragon_cave_knight02 whitedragon_cave_knight03
whitedragon_cave_s_knight whitedragon_cave_s_pawn whitedragon_npc_ice whitedragonvalley_boss
whitedragonvalley_knight01 whitedragonvalley_knight02 whitedragonvalley_pawn whitedragonvalley_s_knight
whitedragonvalley_s_pawn yamachun
ch_general
""".split()


def files_of(folder):
    src = os.path.join(OWSAP, folder)
    names = sorted(os.listdir(src))
    assert 'motlist.txt' in names, folder
    return [n for n in names if n == 'motlist.txt' or n.lower().endswith('.msa')]


def content(folder, name, names):
    b = open(os.path.join(OWSAP, folder, name), 'rb').read()
    if name != 'motlist.txt':
        return b, []
    text, fixes = fix_motlist(folder, b.decode('latin-1'), names)
    return text.encode('latin-1'), fixes


def fix_motlist(folder, text, names):
    """(text, [fixes]) - the motlist's file names made to match the folder's files."""
    have = dict((n.lower(), n) for n in names)
    fixes = []
    out = []
    for line in text.split('\n'):
        t = line.split()
        if len(t) >= 3 and t[2] not in names:
            cand = t[2]
            if cand.lower().endswith('msa') and not cand.lower().endswith('.msa'):
                cand = cand[:-3] + '.msa'
            cand = have.get(cand.lower())
            if cand:
                fixes.append('%s: %s -> %s' % (folder, t[2], cand))
                line = line.replace(t[2], cand, 1)
        out.append(line)
    return '\n'.join(out), fixes


def main():
    check = '--check' in sys.argv
    assert len(set(FOLDERS)) == len(FOLDERS)
    want = dict((f, files_of(f)) for f in FOLDERS)
    if check:
        bad = []
        for f, names in want.items():
            for n in names:
                p = os.path.join(OUT, f, n)
                if not os.path.isfile(p) or open(p, 'rb').read() != content(f, n, names)[0]:
                    bad.append(p)
        extra = sorted(set(os.listdir(OUT)) - set(want)) if os.path.isdir(OUT) else []
        print('ymotions: %d folders, %d files differ, extra %s' % (len(want), len(bad), extra))
        sys.exit(1 if bad or extra else 0)
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    n = 0
    for f, names in want.items():
        os.makedirs(os.path.join(OUT, f))
        for name in names:
            b, fixes = content(f, name, names)
            open(os.path.join(OUT, f, name), 'wb').write(b)
            for x in fixes:
                print('  motlist fixed: ' + x)
            n += 1
    print('ymotions: %d folders, %d files -> %s' % (len(want), n, OUT))


if __name__ == '__main__':
    main()
