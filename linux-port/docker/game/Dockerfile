# syntax=docker/dockerfile:1.6
# =============================================================================
# mt2009 game image -- the martysama0134 r41023 server built for Linux/i386.
#
#  deps    : the 32-bit static dependency set (build-deps-mt2009.sh)
#  builder : the seven modules of the source tree, in the order the package's
#            own top-level Makefile uses; gcc -m32 -std=c++20 instead of clang
#  runtime : (later) the cores, share/, the rendered CONFIGs
#
# The source under src/server is the package's tree with linux-port-mt2009/
# port/linuxify.py applied (the launcher stages it that way); the build refuses
# a tree that has not been through it, because a kqueue libthecore compiles to
# nothing here and the failure would surface as a hundred link errors.
# =============================================================================
ARG BASE_IMAGE=ubuntu:24.04
# An apt mirror to use instead of archive.ubuntu.com, e.g.
# http://pl.archive.ubuntu.com/ubuntu/ -- the default archive crawls from some
# networks and this build installs ~600 MB of toolchain. Empty keeps the
# image's own sources.
ARG APT_MIRROR=

# -----------------------------------------------------------------------------
FROM ${BASE_IMAGE} AS deps

ARG APT_MIRROR
ENV DEBIAN_FRONTEND=noninteractive
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
ENV M2_EXTERN=/opt/m2extern

# Both Canonical hosts, or apt-get update still hangs on the security pocket
# while the main one answers from the mirror.
RUN if [ -n "${APT_MIRROR}" ]; then \
      sed -i -e "s|http://archive.ubuntu.com/ubuntu/|${APT_MIRROR}|g" \
             -e "s|http://security.ubuntu.com/ubuntu/|${APT_MIRROR}|g" \
             /etc/apt/sources.list.d/ubuntu.sources; \
      grep -q "${APT_MIRROR}" /etc/apt/sources.list.d/ubuntu.sources; \
      ! grep -E '^URIs:.*ubuntu\.com' /etc/apt/sources.list.d/ubuntu.sources; \
    fi

COPY build-deps-mt2009.sh /build/build-deps-mt2009.sh
COPY src/extern-tarballs /build/extern-tarballs
COPY src/extern/cryptopp /build/cryptopp

# CRLF guard: this repository is edited on Windows.
RUN sed -i 's/\r$//' /build/build-deps-mt2009.sh && chmod +x /build/build-deps-mt2009.sh

RUN PREFIX="${M2_EXTERN}" BUILD=/build/work TARBALLS=/build/extern-tarballs \
    CRYPTOPP_SRC=/build/cryptopp \
    /build/build-deps-mt2009.sh apt zlib openssl libmd cryptopp mysql devil verify \
 && rm -rf /build/work/src /build/work/stage /build/cryptopp /var/lib/apt/lists/*

# -----------------------------------------------------------------------------
# libs: the support libraries and the db core. A stage of its own so that
# `docker build --target libs` gives an image to iterate the game core in
# (bind-mount game/, run make) while the overlay is being ported.
# -----------------------------------------------------------------------------
FROM deps AS libs

# A job per core ran out of memory on an 8 GB laptop: Docker Desktop gives
# the build VM half the host, and cmd_general.cpp or char.cpp with -O2 -g
# takes over a gigabyte per compiler, so four of them on four gigabytes
# thrashed until the build looked stuck at "game builder 2/3 67%"
# (.unright, 12 September). MAKE_JOBS (M2_MAKE_JOBS in .env) still wins;
# the default is the smaller of the cores and the memory divided by 1400 MB.
# The game core's own step, below, sizes itself by the memory that is free.
ARG MAKE_JOBS=

RUN apt-get update \
 && apt-get install -y --no-install-recommends ccache \
 && rm -rf /var/lib/apt/lists/*

ENV PATH="/usr/lib/ccache:${PATH}"
ENV CCACHE_DIR=/root/.ccache
# Every module Makefile hard-codes clang; the command line wins over the file.
# ENABLE_GCC_AUTODEPEND=0 keeps game/db off the `sed -i ''` BSD-ism in their
# autodepend recipe (a fresh build compiles every file anyway).
ENV M2_MAKE="CC=gcc CXX=g++ ENABLE_GCC_AUTODEPEND=0"

# The Makefiles reach the dependencies as ../../../Extern relative to */src,
# so the tree is laid out exactly like the package: /src/Server, /src/Extern.
WORKDIR /src/Server

COPY src/extern/include /src/Extern/include
RUN set -eux; \
    mkdir -p /src/Extern/lib; \
    cp -a "${M2_EXTERN}/lib/." /src/Extern/lib/; \
    # The shipped mysql headers belong to another connector build; ours must
    # match the archive we link.  IL ships 1.7.8 headers, the archive is 1.8.0.
    rm -rf /src/Extern/include/mysql; \
    cp -a "${M2_EXTERN}/include/mysql" /src/Extern/include/mysql; \
    cp -a "${M2_EXTERN}/include/IL/." /src/Extern/include/IL/; \
    # libsql includes <mysql/mysql.h> through -I/usr/local/include only.
    mkdir -p /usr/local/include; ln -sfn /src/Extern/include/mysql /usr/local/include/mysql; \
    # game/db link /usr/lib32/lib{ssl,crypto}.a by absolute path.
    mkdir -p /usr/lib32; \
    ln -sfn /usr/lib/i386-linux-gnu/libssl.a /usr/lib32/libssl.a; \
    ln -sfn /usr/lib/i386-linux-gnu/libcrypto.a /usr/lib32/libcrypto.a

# Layer 1: the support libraries, built once and cached.
COPY src/server/__REVISION__ __REVISION__
COPY src/server/common common
COPY src/server/libthecore libthecore
COPY src/server/libpoly libpoly
COPY src/server/libgame libgame
COPY src/server/liblua liblua
COPY src/server/libsql libsql

RUN grep -q 'fdwatch_sndbuf_left' libthecore/src/fdwatch.c \
 && grep -q 'defined(__linux__)' libthecore/src/signal.c \
 || { echo "FATAL: the tree has not been through port/linuxify.py"; exit 1; }

RUN --mount=type=cache,target=/root/.ccache set -eux; \
    find . -name '*.o' -delete; \
    find . \( -name Makefile -o -name config -o -name Depend -o -name __REVISION__ \) -exec sed -i 's/\r$//' {} +; \
    J="${MAKE_JOBS:-}"; if [ -z "$J" ]; then J="$(nproc)"; M="$(awk '/MemTotal/ { print int($2 / 1024 / 1400) }' /proc/meminfo)"; [ "$M" -ge 1 ] || M=1; [ "$M" -ge "$J" ] || J="$M"; fi; echo "make -j$J (cores $(nproc), memory $(awk '/MemTotal/ { print int($2 / 1024) }' /proc/meminfo) MB)"; \
    make -C liblua/5.0 CC=gcc MYCFLAGS="-O2 -g -fno-strict-aliasing"; \
    for m in libsql libgame/src libpoly libthecore/src; do \
      : > "$m/Depend"; \
      make -C "$m" dep ${M2_MAKE}; \
      make -C "$m" -j"$J" ${M2_MAKE}; \
    done; \
    for a in liblua/5.0/lib/liblua.a liblua/5.0/lib/liblualib.a libsql/libsql.a \
             libgame/lib/libgame.a libpoly/libpoly.a libthecore/lib/libthecore.a; do \
      [ -f "$a" ] || { echo "FATAL: $a was not produced"; exit 1; }; \
    done; \
    echo "support archives built"

# Layer 2: the db core. GuildManager.cpp includes one header from the game
# core (../../game/src/locale.hpp, self-contained); copying just that keeps
# this layer cached across game-source edits.
COPY src/server/db db
COPY src/server/game/src/locale.hpp game/src/locale.hpp
RUN --mount=type=cache,target=/root/.ccache set -eux; \
    sed -i 's/\r$//' db/src/Makefile; \
    rm -rf db/src/.obj db/src/Depend; \
    J="${MAKE_JOBS:-}"; if [ -z "$J" ]; then J="$(nproc)"; M="$(awk '/MemTotal/ { print int($2 / 1024 / 1400) }' /proc/meminfo)"; [ "$M" -ge 1 ] || M=1; [ "$M" -ge "$J" ] || J="$M"; fi; echo "make -j$J (cores $(nproc), memory $(awk '/MemTotal/ { print int($2 / 1024) }' /proc/meminfo) MB)"; \
    make -C db/src -j"$J" ${M2_MAKE}; \
    mkdir -p /out; cp "db/db_r$(cat __REVISION__)" /out/db

# -----------------------------------------------------------------------------
FROM libs AS builder

ARG MAKE_JOBS=
ARG STRIP_BINARIES=1

# Layer 3: the game core. Its job count is sized by what is free, not by the
# VM's total, for two reasons measured on 24 September. playerbot_manager.cpp
# is the whole bot AI in one translation unit and takes about 2.3 GB at
# -O2 -g, where an engine file takes 0.5-0.7 GB (the whole core from nothing:
# 98 s and 3 GB at -j4). And an update builds while the old server still runs
# - `up --build` recreates the containers only once the images are built - so
# the bots and the database hold gigabytes of the same VM while this compiles
# (4.5 GB at 1100 bots). Sized by MemTotal, a laptop swapped until the build
# looked stuck at "game builder 2/3 (67%)" again (Drip, 24 September). So:
# room for the heavy file and 700 MB a job after it, out of MemAvailable, and
# a line in the log when even the heavy file does not fit.
# MT2009_PLUS_FAST_BUILD_V1: an image whose binaries are stripped anyway
# (STRIP_BINARIES=1, every player's) compiles without -g - the debug info was
# written only to be thrown away, and it is most of what playerbot_manager.cpp,
# the bots' whole AI in one file, costs in time and memory.
COPY src/server/game game
RUN --mount=type=cache,target=/root/.ccache set -eux; \
    sed -i 's/\r$//' game/src/Makefile; \
    rm -rf game/src/.obj game/src/Depend; \
    if [ "${STRIP_BINARIES}" = "1" ]; then sed -i -E '/^CFLAGS  = /s/ -g( |$)/ \1/' game/src/Makefile; echo "debug info off (STRIP_BINARIES=1): no -g"; fi; \
    T="$(awk '/^MemTotal:/ { print int($2 / 1024) }' /proc/meminfo)"; \
    A="$(awk '/^MemAvailable:/ { print int($2 / 1024) }' /proc/meminfo)"; [ -n "$A" ] && [ "$A" -gt 0 ] || A="$T"; \
    J="${MAKE_JOBS:-}"; if [ -z "$J" ]; then J="$(nproc)"; M=$(( 1 + (A - 2600) / 700 )); [ "$M" -ge 1 ] || M=1; [ "$M" -ge "$J" ] || J="$M"; fi; \
    echo "make -j$J (cores $(nproc), memory $T MB, free $A MB)"; \
    if [ "$A" -lt 2600 ]; then echo "UWAGA: w maszynie Dockera wolne jest tylko $A MB pamieci RAM (to nie miejsce na dysku), a najciezszy plik rdzenia potrzebuje okolo 2300 MB. Kompilacja moze trwac bardzo dlugo. Zatrzymaj serwer przed aktualizacja (w launcherze: ZATRZYMAJ I ZAPISZ, potem GRAJ albo SPRAWDZ AKTUALIZACJE)."; fi; \
    make -C game/src -j"$J" ${M2_MAKE}; \
    mkdir -p /out; cp "game/game_r$(cat __REVISION__)" /out/game

# Both cores must be 32-bit with a 32-bit time_t: the wire and DB structs
# depend on it.
RUN set -eux; \
    for b in /out/game /out/db; do \
      file -b "$b" | grep -q 'ELF 32-bit LSB .* Intel 80386' \
        || { echo "FATAL: $b is not a 32-bit i386 ELF"; file "$b"; exit 1; }; \
    done; \
    if strings -a /out/game | grep -q '_TIME_BITS=64'; then \
      echo "FATAL: _TIME_BITS=64 leaked into the build"; exit 1; \
    fi; \
    echo "unstripped: $(du -sh /out | cut -f1)"; \
    if [ "${STRIP_BINARIES}" = "1" ]; then strip --strip-unneeded /out/game /out/db; fi; \
    ls -la /out

# -----------------------------------------------------------------------------
# quests: the panel's in-game helper (web_admin.quest), the movement-speed
# bonus and the starter chest, compiled by the tree's own qc into object files
# the cores load at boot. High Risk is NOT on the list on purpose: an update
# never deletes a file, so every 2.0.0-2.0.5 tree still carries
# quest/high_risk.quest, and 2.0.6 - which only removed the file from the
# repository - kept compiling it on every player's machine ("po wgraniu update
# risk mode nadal jest"). The loop is the gate, not the directory. qc ships as a FreeBSD binary in the package's quest
# directory, so it is built here from game/src/quest against the in-tree Lua
# 5.0. The 300-odd stock quests keep the object files they came with; this
# stage produces only its own three and they are copied over as an addition.
# -----------------------------------------------------------------------------
FROM builder AS quests

COPY quest/ /quest-add/
COPY src/serverfiles/share/locale/poland/quest/quest_functions /quest-src/quest_functions

RUN set -eux; \
    mkdir -p /out-quest/poland/quest; \
    if [ ! -f /quest-add/web_admin.quest ]; then \
      echo "note: no web_admin.quest in the build context -- the panel will use"; \
      echo "      its database fallback and Teleport/Running speed will not work."; \
      exit 0; \
    fi; \
    sed -i 's/\r$//' game/src/quest/Makefile; \
    rm -f game/src/quest/qc game/src/quest/*.o; \
    make -C game/src/quest qc CXX="g++ -m32" \
         CPPFLAGS="-g -w -std=c++20 -include cstring -include cstdio -include cstdlib"; \
    test -x game/src/quest/qc; \
    file -b game/src/quest/qc | grep -q 'ELF 32-bit'; \
    out=/out-quest/poland/quest; \
    rm -rf /tmp/qc-work; mkdir -p /tmp/qc-work/object; \
    sed 's/\r$//' /quest-src/quest_functions > /tmp/qc-work/quest_functions; \
    # Functions the engine has and the package's list forgot, which qc would
    # otherwise refuse (gm_profile.quest: equipping, bonus lines, stack size,
    # the item's use path).
    # pc.open_special_shop for labirynth (fishing_pass_shop's until MT2009_PLUS_FISHING_FREE_V1); affect.add_new and
    # affect.remove_new for the panel's speed in web_admin (2.0.76).
    # pc.is_playerbot for the Devil's Catacomb's bot branches (2.2.21).
    # affect.get_duration and pc.has_affect for the ItemShop's Auto Lowy ticket
    # and anti-experience ring (autohunt_time, antiexp_ring; 2.2.26).
    # pc.warp_channel for the panels' teleport to a bot on another channel
    # (web_admin; 2.2.37).
    # mes.get_message, pc.get_special_flag and pc.set_special_flag for the quests' client
    # messages and web_admin's flags.
    # pc.clear_quest_letter for usun_misje (MT2009_PLUS_CLEAR_MISSIONS_V1,
    # server-patches/clearmissions).
    # guild.treasury_available and guild.treasury_spend for our guild_building
    # (MT2009_PLUS_GUILD_TREASURY_V1, server-patches/enginefixes).
    # zodiac_temple.*, pc.*animasphere, pc.*_flag_cz_ulimit_enter, d.zodiac_* and
    # game.zodiac_temple_table for the Zodiac Temple's quests (MT2009_PLUS_ZODIAC_V1,
    # playerbot_zodiac_questlua.cpp; Autor: Digi Rasta).
    # dw.* for Obrona Statku's quest (MT2009_PLUS_SHIP_DEFENSE_V1, playerbot_ship_defense_questlua.cpp).
    # pc.*conqueror*, pc.*sungma* and npc.get_sungma_exp for Poziom Czempiona (MT2009_PLUS_CHAMPION_V1,
    # playerbot_champion.cpp; czempion, czempion_nowa_wola).
    # d.zone_attack, d.zone_hurt, d.unique_damage_pct and d.kick_dead for Glebie and Swiatynia Wezy
    # (MT2009_PLUS_DUNGEON_ZONE_V1, server-patches/strefy).
    # game.open_changelook and item.get_changelook_vnum for Transmutacja at Teowaden (MT2009_PLUS_CHANGE_LOOK_V1,
    # playerbot_changelook.cpp; transmutacja).
    # game.open_aura for Szata Aury at Theowahdan (MT2009_PLUS_AURA_V1, playerbot_aura.cpp; szata_aury).
    # pc.get_riposte, pc.get_boost, pc.get_class_boost, pc.learn_passive_skill and pc.reset_passive_skills for
    # Riposty i Dopalacze (MT2009_PLUS_RIPOSTY_V1, playerbot_riposty.cpp; riposty).
    # game.drop_item_at for the boss loot on the ground of Razador, Nemere and Beran-Setaou (MT2009_PLUS_DUNGEON_GROUND_LOOT_V1,
    # server-patches/enginefixes; razador_dungeon, nemere_dungeon, blue_dragon_lair).
    # mlodzi.* for Bronie dla Mlodych Bohaterow (MT2009_PLUS_MLODZI_BOHATEROWIE_V1, playerbot_mlodzi.cpp; mlodzi_bohaterowie).
    # pc.seonpyeong_cells and pc.seonpyeong_refine for Seon-Pyeong's talk opening his refine window (MT2009_PLUS_SEONPYEONG_FIX_V1,
    # server-patches/seonpyeong; seon_pyeong).
    # guild.get_near_count/get_near_pids/get_flag/set_flag/get_level, guild.get_money, guild.set_ladder_point and balathor.* for
    # Krypta Balathora (MT2009_PLUS_BALATHOR_V1, server-patches/balathor, balathor_support.cpp; krypta_balathora).
    # set_summon_lifetime and summon_blocked_here for the 15-minute summoned Metin stones and veins and the dungeon
    # refusal (MT2009_PLUS_SUMMON_STONE_V1, server-patches/enginefixes; yohara_mapy2, yohara_mapy4).
    # pc.get_gaya and pc.change_gaya for the Gaya currency (MT2009_PLUS_GAYA_CURRENCY_V1, server-patches/gaya2; ygaya).
    # guild.get_level, guild.create_time, guild.age, guild.member_join_time, guild.member_age, guild.get_bank and
    # guild.check_requirements for the Balathor port (MT2009_PLUS_GUILDSYS_V1, server-patches/guildsys, guildsys.cpp).
    # q.set_clock_of for Spirala Czasu's refresh of another quest's letter clock (MT2009_PLUS_SPIRALA_CZASU_V2,
    # server-patches/spiralaclock; spirala_czasu).
    # remote_call.* for Enasir's quest remote_call (MT2009_PLUS_REMOTE_CALL_V1, server-patches/remotecall, remote_call.cpp).
    for fn in q.set_clock_of pc.seonpyeong_cells pc.seonpyeong_refine mes.get_message pc.get_special_flag pc.set_special_flag mysql_direct_query pc.equip_slot pc.unequip_slot item.set_attr item.get_max_stack item.use pc.open_special_shop affect.add_new affect.remove_new pc.is_playerbot affect.get_duration pc.has_affect pc.warp_channel game.get_catchking_score game.get_catchking_myscore game.catchking_claim_reward game.catchking_use_item game.catchking_deliver pc.clear_quest_letter guild.treasury_available guild.treasury_spend zodiac_temple.starttemple zodiac_temple.startlogin zodiac_temple.new_floor zodiac_temple.setflag zodiac_temple.getflag pc.set_animasphere pc.get_animasphere pc.delete_animasphere pc.is_flag_cz_ulimit_enter pc.set_flag_cz_ulimit_enter d.zodiac_notice d.zodiac_notice_clear d.zodiac_time d.zodiac_time_clear game.zodiac_temple_table guild.leave_war is_on_war_map dw.cfg dw.map_index dw.count dw.find dw.start dw.is_started dw.wave dw.state dw.mast_hp_pct dw.set_alliance_hp_pct dw.close pc.get_conqueror_level pc.get_conqueror_exp pc.get_conqueror_next_exp pc.get_conqueror_point pc.get_conqueror_unlock_state pc.set_conqueror pc.give_conqueror_exp pc.give_conqueror_exp2 pc.get_sungma_str pc.get_sungma_vit pc.get_sungma_res pc.get_sungma_int pc.reset_sungma_status npc.get_sungma_exp d.zone_attack d.zone_hurt d.unique_damage_pct d.kick_dead game.open_changelook item.get_changelook_vnum game.open_aura game.drop_item_at pc.get_riposte pc.get_boost pc.get_class_boost pc.learn_passive_skill pc.reset_passive_skills mlodzi.enabled mlodzi.offer mlodzi.tier_level mlodzi.weapons mlodzi.claim mlodzi.is_weapon set_summon_lifetime summon_blocked_here guild.get_money guild.set_ladder_point guild.get_near_count guild.get_near_pids guild.get_flag guild.set_flag guild.get_level balathor.is_open balathor.is_in_map balathor.get_stage balathor.set_stage balathor.can_use_hwatcha balathor.use_hwatcha balathor.revive_hwatcha balathor.is_hwatcha_dead balathor.get_register_config balathor.is_guild_dungeon_exist balathor.teleport balathor.warp_enter balathor.can_create balathor.create balathor.give_up balathor.claim_reward pc.get_gaya pc.change_gaya balathor.claim_reward guild.create_time guild.age guild.member_join_time guild.member_age guild.get_bank guild.check_requirements enasir.is_owner enasir.has_safebox enasir.has_shop enasir.open_safebox enasir.open_shop enasir.unsummon enasir.time_left; do \
      grep -qx "$fn" /tmp/qc-work/quest_functions || echo "$fn" >> /tmp/qc-work/quest_functions; \
    done; \
    # MT2009_PLUS_HORSE30_V1 (Digi Rasta's horse to level 30): konie is the
    # stable keeper's paid training (levels 1-9, 11-19, 21-28) and the Black
    # Steed's trial (29 -> 30). (MT2009_PLUS_HORSE40_V3: no horse bags on Yohara - our
    # horse_inventory is gone and the stock one loses its handlers in the runtime stage.) The package's training
    # missions, pony_levelup (1-10) and horse_levelup (11-20), are no longer
    # compiled and lose their stock handlers in the runtime stage.
    # gm_profile brings the admin account's game masters to one profile
    # through the engine (2.0.13).
    # new_quest_lv19 is the package's level-19 quest with its bear group
    # completed: the stock group names 140 and 141 only, so the Cursed Bear
    # (139) and the Cursed Brown Bear (142) never counted towards the five
    # bear skins (Pabloo, from Dixdros' report, 2.0.47).
    # teleport_ring answers the use of Pierscien Teleportacji (70058), which the
    # package drops and no stock quest handled (2.0.48).
    # pony_buy, horse_upgrade and horse_upgrade2 are the package's
    # stable-keeper quests with the wait for the horse taken out: twelve hours
    # for the pony and each upgrade (16 September, 2.0.56).
    # collect_quest_lv85 is the Biologist's red-branch row with its hand-in
    # asking for the right item: the stock quest counted 30166, the level-80
    # row's, so nobody could hand in a single 30167 (2.0.95).
    # collect_quest_lv70 drops its Konar Zelkova (30165) whatever the bag
    # already holds - the branch stacks (MT2009_PLUS_UPSTREAM_BOTLOGIC_ZELKOVA_V1).
    # collect_quest_lv80 / lv90 drop their Certyfikat Tugyisa (30166) / Notatka Przywodcy (30168) the same way - into
    # the stack the bag already holds, no empty cell needed (MT2009_PLUS_BIOLOG_STACK_V1, the owner 3 November 2026).
    # collect_quest_lv92 / lv94 are Seon-Pyeong's research (Klejnoty Zawisci, Klejnoty Madrosci and Kamien Dusz
    # Beran-Setaou, a permanent bonus of three to choose) over the package's empty lv92 stub - lv90 already sets it
    # to "run" - and collect_quest_cz1 / cz10 / cz20 Chaegirab's in Dongan (Oczyszczone Rdzenie, Krysztaly Metin,
    # Mroczne Paprocie from Poziom Czempiona 1 / 10 / 20, a random Wola SungMa +5), the pl-wiki's "Misje Biologa"
    # (MT2009_PLUS_BIOLOGIST_YOHARA_V1; the items: mariadb/playerbot/yohara_biolog.sql, tools/ybiolog).
    # towarzysz is the letter that makes and commands a player's companion
    # (playerbot_sidekick.h): class, path and name, then call, free, dismiss.
    # devilcatacomb_zone is the Devil's Catacomb, which the package kept in
    # quest/_unused and never compiled (26 September).
    # check_trans_ticket is the package's own with Koe-Pung's branch put back:
    # the Grotto of Exile for a Bloodstone from 75, in place of the free warp
    # 2.2.20 opened; heavens_cave_keyquest is Seon-Hae's daily quest for the
    # Bloodstone, from quest/_unused (2.2.21).
    # tanaka_ears is Yonah's exchange of Pirate Tanaka's ear for a Purple Ebony
    # Chest, the Tanaka event's reward (playerbot_world_events.h).
    # seon_pyeong is Seon-Pyeong's talk by the Grotto of Exile: what to drag onto him
    # (a +9 piece of level 65-66 into its level-80 successor, MT2009_PLUS_SEONPYEONG_GF_V1).
    # wytwarzanie_jae_seon_kim opens Jae-Seon Kim's (20383) cube window: the share's
    # 72 recipes of his (level-75 weapons and armours, the level-80 jewellery, belts)
    # that no quest opened (MT2009_PLUS_JAE_SEON_CUBE_V1).
    # flea_market is the Dom Towarowy's two options at the miscellaneous
    # merchant in M1, offered only while M2_FLEA_MARKET is on (Uxie [DSO]).
    # temple_of_the_ochao is the Temple of Ochao's entrance (Straznik Swiatyni,
    # 20426), its portal (20415) and the Bodyguard's reward (MT2009_PLUS_OCHAO_V1).
    # biblioteka_wiedzy is the Arezzo library dungeon (363) and map_warp the package's
    # Teleporter with Dolina Cyklopow (360) on its first page (MT2009_PLUS_AREZZO_V1).
    # dungeon_panel is the dungeon panel's part in the quests: the instances' start and the
    # bosses of the open maps (MT2009_PLUS_DUNGEON_PANEL_V1, playerbot_dungeon_panel.h).
    # wzgorze_wukonga, ruiny_skorpiona and starozytna_dzungla are the Arezzo dungeons 364-366
    # (MT2009_PLUS_AREZZO_V1, phases 5-7).
    # blue_dragon_lair is the Blue Dragon lair (map 208) entered at the Sura's Ghost in the Grotto of
    # Exile V2 (MT2009_PLUS_BLUE_DRAGON_V1).
    # ruiny_atlantydy is Ruiny Atlantydy (map 158), entered at Mag Atlantydy in Orc Valley beside the
    # Grotto of Exile with a Bilet do Atlantydy (MT2009_PLUS_ATLANTYDA_V1).
    # seonhae opens Seon-Hae's 6th/7th bonus window at 20095 while m2_seonhae_on is set
    # (MT2009_PLUS_SEONHAE_V1, playerbot_seonhae.h).
    # minigame_rumi is the Okey table (20417) of Owsap's Rumi: rankings, the top ten's prize, the
    # chests a left game owes (MT2009_PLUS_RUMI_V1, playerbot_rumi.h).
    # minigame_catchking is Catch the King's table NPC (20506: the prizes, the ranking, the top-10
    # prize), its King Card and King Deck used from the bag and a left game's Loot at login
    # (MT2009_PLUS_CATCH_KING_V1, playerbot_catchking.h; the game functions are added above).
    # minigame_yutnori is the Yut Nori table's menu (20502): the ranking, its prizes and the
    # game's window (MT2009_PLUS_YUTNORI_V1, playerbot_yutnori.h).
    # ksiegi_seonhae is Seon-Hae's book exchange (20095): the window, then "/nowy_ksiegi"
    # (MT2009_PLUS_DIGI_SERVER_QOL_V1, playerbot_digi_qol.h, Autor: Digi Rasta).
    # starter_kit dresses a player's new character in the world's starter kit,
    # M2_STARTER_KIT (the operator, 30 September, on Iwakura's proposal); the
    # seed dresses the bots it makes.
    # tp_bookmarks is the six saved teleport positions of the inventory sidebar's window
    # ("/tpzapis", a clean ItemShop Zwoj Powrotu each teleport, 15 minutes apart;
    # MT2009_PLUS_TP_BOOKMARKS_V1, client root uitpbookmarks.py).
    # usun_misje is "/usunmisje": the window of the missions open now (story, side
    # quests, Biologist, Baek-Go's herbs; never the Companion or Cor Draconis), the
    # checked ones to their finished state without a reward, their letters off at
    # once with pc.clear_quest_letter (MT2009_PLUS_CLEAR_MISSIONS_V1,
    # server-patches/clearmissions, client root uiusunmisje.py; its table from
    # tools/gen_usun_misje.py).
    # guild_building is the package's land purchase at the guild land NPC with the
    # land paid from the guild's treasury first, the master's own yang for the rest
    # (MT2009_PLUS_GUILD_TREASURY_V1: the treasury is spent only on the guild).
    # kolekcjoner_item answers the use of the ItemShop's "Kolekcjoner" (70115): the
    # collector's storage anywhere, "/kolekcjoner przedmiot" (MT2009_PLUS_COLLECTOR_ITEM_V1,
    # playerbot_collector.cpp).
    # mikstury_okno (MT2009_PLUS_WIKI_NPC_RECIPES_V1: the windows of Rybak, Baek-Go, Yu-Hwan, Huahn-So; pasy is no longer
    # compiled - the belts only at Yu-Hwan and Jae-Seon Kim, as on the wiki) and energia_alchemik (the Alchemist
    # dismantles items of level 35+ into Odlamki Energii; the belt system, MT2009_PLUS_BELTS_V1, Autor: Digi Rasta).
    # energia_krysztal: the Alchemist makes Krysztal Energii (51002) of 30 shards + 1 000 Yang, the first always, then 30 %
    # (MT2009_PLUS_ENERGY_V1, the pl-wiki "System Energii"; server-patches/energia).
    # zywioly (Mistrz 20082: the Kwiat Zywiolu shop and the elements' explanation) is the
    # elements and talismans (MT2009_PLUS_ELEMENTS_V1, Autor: Digi Rasta).
    # mapa_tab is the teleport map under TAB: "/tabteleport <key>" from the client's window
    # (root uiteleportmap.py), free, only while m2_teleport_map_on is set; "MAPA_TAB 1|0" tells
    # the client whether TAB opens it (MT2009_PLUS_TELEPORT_MAP_V1, Autor: Mur4s).
    # zodiac_temples (the twelve portals of the day on 358 and the Teleporter's entry),
    # zodiac_milbon (Mnich Milbon's insignia exchange), zodiac_prism_mission and
    # zodiac_emergency_mission are the Zodiac Temple (MT2009_PLUS_ZODIAC_V1, Autor: Digi Rasta).
    # obrona_statku is Obrona Statku (Hydra, map 367): the Fisherman's (9009) entry on 301, the wheel,
    # the repair planks, the portal and the completion flags (MT2009_PLUS_SHIP_DEFENSE_V1).
    # czempion (the Posag Wojownika 20433: becoming a Champion) and czempion_nowa_wola (Nowa Wola 72068-72071)
    # are Poziom Czempiona (MT2009_PLUS_CHAMPION_V1, server-patches/czempion).
    # port_yohary is Port Nowego Kontynentu (368): the statue's dungeon ranking and the way back to the Fisherman,
    # Pierscien Hydry (70303, three teleports to the port) and the level-90 guard (MT2009_PLUS_YOHARA_PORT_V1).
    # yohara_mapy is the first maps of Yohara - Opuszczona Twierdza (374) and Dongan (373): the statue's way there
    # from level 120, the way back to the port, the Teleporter of Dongan, the level-120 guard (MT2009_PLUS_YOHARA_MAPS1_V1).
    # yohara_mapy2 is the second batch - Seoganland, Namgan, Przelecz Yilad, Wawoz and Schronienie Polnocnego Wiatru
    # (376/377/385/388/393): the level-120 guard and the jade veins' pickaxe (MT2009_PLUS_YOHARA_MAPS2_V1).
    # yohara_mapy3 is the third batch of Yohara places (MT2009_PLUS_YOHARA_MAPS3_V1): the ways into Zejscie Polnocnego
    # Wiatru's level guard, the 1st level of Swiatynia Wezy (Straznik Wezy on Przelecz Yilad), Tajemnicza Instancja
    # (Tajemniczy Oltarz on Namgan: the ticket, the talisman crafting), Krolestwo Zywiolow and Plaskowyz Sil Natury
    # (the port's portal, the rings, the medal, the plateau's HP drain, death -> the port); ymaps3_glebie is Glebie
    # Polnocnego Wiatru (Alastor, slaby/silny, at Upiorny Straznik); swiatynia_wezy is the temple's 7 levels.
    # yohara_mapy4 is Rozpadlina Dusz (389, MT2009_PLUS_YOHARA_MAPS4_V1): its level guard and General Kohan's way
    # into Schronienie Polnocnego Wiatru.
    # jaskinie_gnolli is Jaskinie Gnolli 1-3 (Halabardnik in Dongan, the ticket, the stage portals, death -> Dongan) and
    # wieza_sung_mahi Wieza Sung Mahi's 50 floors (MT2009_PLUS_YOHARA_DUNG4_V1).
    # transmutacja is Teowaden's (60003) "Transmutacja": the change-look window for items and mounts
    # (MT2009_PLUS_CHANGE_LOOK_V1, server-patches/transmutacja).
    # ygaya is Kamienie Gaya and Statua Wojownika's other functions (MT2009_PLUS_GAYA_V1): Kamyki ground into Gaya
    # (70%), Portowy Sklep Gaya (3 rows of 3, the third unlocked); no elemental pet chests (the owner, 14 October).
    # przebudzeni_bossowie is the awakened bosses' entrance (Statua Iluzji's daily mission and way to Plaskowyz Iluzji,
    # Statua Przebudzenia, the plateau's statues and Handlarka Iluzji, Baek-Go's Lekarstwo Iluzji), razador_pb Twierdza
    # Czerwonego Smoka (PB), nemere_pb Straznica Nemere (PB) (MT2009_PLUS_YOHARA_PB_V1), beran_pb Grota Wygnancow 2 (PB),
    # jotun_pb Zaklety Las (PB) (MT2009_PLUS_YOHARA_ILUZJA_V1). szczelina_czasu is Statua Szczeliny Czasu on the plateau
    # (the Time Rift dungeons' entrance, Zegarek Kieszonkowy), jotun_szc Zaklety Las (SZC) (MT2009_PLUS_YOHARA_CRACK_V1);
    # beran_szc Grota Wygnancow 2 (SZC), razador_szc Twierdza Czerwonego Smoka (SZC), nemere_szc Straznica Nemere (SZC)
    # (MT2009_PLUS_YOHARA_CRACK2_V1).
    # zaklety_las is Zaklety Las's seven missions (Kamien Driad), erebu Erebu - Jotun Thrym's dungeon and the forest's
    # map rules (MT2009_PLUS_YOHARA_ZAKLETY_V1).
    # rekawice is Mistrz Chi's (20823, Dongan) "Rekawice SungMa": the four Sung Ma gloves +0 from runes, leather, patterns,
    # Kamien Runiczny, Gaya and Yang (75%; MT2009_PLUS_GLOVES_V1, tools/ygloves, server-patches/rekawice).
    # helm100 is Straznik Smokow Jaharr's (20421, Yongan / Joan / Pyungmoo) level-100 helmets: a level-80 helmet +5..+9
    # dragged on him, dragon horns, scales, plans (and wings) and 1 000 000 Yang (MT2009_PLUS_HELM100_V1, tools/yhelm100).
    # szata_aury is Szata Aury (MT2009_PLUS_AURA_V1, server-patches/aura): Theowahdan's (60003) three windows - bonuses
    # absorbed, runes for the level, the evolution - and Baek-Go's (20018) Zwyczajna Szata Aury (20%, the pl-wiki).
    # angmur is Admiral Angmur's (20378 cape, 20812 fortress) level-90 body armour from a level-66 one +9 dragged onto
    # him, the bonuses and stones kept (MT2009_PLUS_ANGMUR_V1, the pl-wiki).
    # kawuco opens Kawuco's (20413, Przyladek Smoczego Ognia) cube window: Ogniste Buty / Buty Oceanu from Buty Zimorodka /
    # Euforii +5..+9 (cube.buty.txt, 5-50% by plus; MT2009_PLUS_KAWUCO_V1).
    # eliksiry_yohary opens Huahn-So's (20022, Bokjung / Bakra / Jayang) cube window: the elixirs of Yohara from the
    # herbs and the empty bottles (cube.eliksiry.txt, blend.eliksiry.txt; MT2009_PLUS_YELIXIRS_V1, tools/yohara_eliksiry).
    # meley_dungeon is Schronienie Meley - Straznik Smokow Dolnarr on Doyyumhwaji, the Dragon Queen's lair (356)
    # (MT2009_PLUS_YOHARA_MELEY_V1).
    # riposty is Riposty i Dopalacze: Podrecznik: Riposta / Dopalacz (50515 / 50514), Kamien Duchowy+ (50525, G1 -> P)
    # and Zwoj Zmiany Treningu (71000) (MT2009_PLUS_RIPOSTY_V1, server-patches/riposty, playerbot_riposty.cpp).
    # mlodzi_bohaterowie is Bronie dla Mlodych Bohaterow: the letter at level 1, 10 ... 70 opens the client's window, "/mlodzi_wybor"
    # takes the weapon (MT2009_PLUS_MLODZI_BOHATEROWIE_V1, playerbot_mlodzi.cpp, server-patches/mlodzi).
    # buffi is Buffi, Ameria's support shaman: Kamien Duchowy Buffi (61031, G1 -> P), the new character's seal and name
    # scroll, the books and soul stones at the General Store (MT2009_PLUS_BUFFI_V1, server-patches/buffi, playerbot_buffi.cpp).
    # labirynth and black_steel_crafting are the package's, with Min-Sun (20402) on Pustynia Yongbi since Przelecz (69)
    # is gone (MT2009_PLUS_PASS69_OFF_V1) - their objects replace the stock ones.
    # skrzynie_klas (MT2009_PLUS_CLASS_CHESTS_V1): the eight class chests of the second ItemShop and their encyclopedias.
    # potega_madrosci (MT2009_PLUS_POTEGA_MADROSCI_V1): "Potega madrosci" - Uriel's experience bonus by level range while
    # the event flag potega_madrosci is on (the planner's kind "potega"), the village guard's table of it.
    # spirala_czasu (MT2009_PLUS_SPIRALA_CZASU_V1): Spirala Czasu 10 / 20 / 30% (72347-72349) cuts the remaining time of a
    # running mission wait - the Biologist, the stable keeper, Seon-Hae's 6th/7th bonus, the relics (never skill books).
    # eliksir_poszukiwacza (MT2009_PLUS_BIOLOG_ELIKSIR_V1): Eliksir Poszukiwacza (71035 / 76020 / 39023) - the next research
    # hand-in at Chaegirab / Seon-Pyeong at 90% instead of 60% (m2_mikstury.lua); at login the withdrawn Baek-Go potions'
    # effects still running come off (MT2009_PLUS_MIKSTURY_WYCOFANE_V1).
    # ishop_v3_przedmioty is the second ItemShop's items of the big servers' list: Auto Lowy 7 / 14 days, Szklo Handlu
    # (the Dom Aukcyjny from anywhere, server-patches/szklohandlu), Buff Premium SungMa, Eliksir W. SungMa
    # (MT2009_PLUS_ITEMSHOP_V3_V8, tools/itemshop3/global/owner_decisions.py).
    # krypta_balathora is Krypta Balathora - Straznik Smokow Dolnarr on Doyyumhwaji, the guild lair of the White Dragon (420)
    # (MT2009_PLUS_BALATHOR_V1, author dracaryS; offered only while M2_BALATHOR_ON=1 hosts the map).
    # event_halloween_hair is Owsap's Halloween event (MT2009_PLUS_HALLOWEEN_V1, Autor: Owsap) in
    # place of the package's copy, whose handlers the runtime stage removes first.
    # training_grandmaster_skill is the package's Soul Stone (50513) with the other specialisation's skills on G1-G10 in
    # its list while the event flag m2_skill_hack is on (MT2009_PLUS_SKILL_HACK_V1, server-patches/skillhack) - its
    # objects replace the stock ones.
    # remote_call is Enasir's click - Otworz Magazyn / Otworz sklep / Odeslij Enasira, for his owner only
    # (MT2009_PLUS_REMOTE_CALL_V1, server-patches/remotecall, remote_call.cpp).
    for q in web_admin speed_boost starter_chest starter_kit konie gm_profile new_quest_lv19 teleport_ring pony_buy horse_upgrade horse_upgrade2 deviltower_zone collect_quest_lv85 collect_quest_lv70 collect_quest_lv80 collect_quest_lv90 collect_quest_lv92 collect_quest_lv94 collect_quest_cz1 collect_quest_cz10 collect_quest_cz20 towarzysz devilcatacomb_zone check_trans_ticket heavens_cave_keyquest tanaka_ears acce_costume_uriel ah_yu_shop costume_bonus_transfer dragon_soul dragon_soul_refine dragon_soul_shop autohunt_time antiexp_ring seon_pyeong wytwarzanie_jae_seon_kim flea_market temple_of_the_ochao razador_dungeon nemere_dungeon blue_dragon_lair goblin_skarbow biblioteka_wiedzy map_warp dungeon_panel wzgorze_wukonga ruiny_skorpiona starozytna_dzungla ruiny_atlantydy seonhae minigame_rumi minigame_catchking minigame_yutnori tp_bookmarks ksiegi_seonhae usun_misje guild_building kolekcjoner_item mikstury_okno energia_alchemik energia_krysztal zywioly mapa_tab zodiac_temples zodiac_milbon zodiac_prism_mission zodiac_emergency_mission guild_war_join obrona_statku czempion czempion_nowa_wola port_yohary yohara_mapy yohara_mapy2 yohara_mapy3 ymaps3_glebie swiatynia_wezy yohara_mapy4 ysets jaskinie_gnolli wieza_sung_mahi transmutacja ygaya przebudzeni_bossowie razador_pb nemere_pb beran_pb jotun_pb szczelina_czasu jotun_szc zaklety_las erebu rekawice helm100 szata_aury kawuco angmur eliksiry_yohary meley_dungeon labirynth black_steel_crafting beran_szc razador_szc nemere_szc riposty worldboss_kupony buffi mlodzi_bohaterowie ishop_v3_przedmioty event_halloween_hair krypta_balathora relikt_bron relikt_zbroja relikt_alchemik relikt_uriel relikt_chaegirab relikt_uszlachetnianie skrzynie_klas spirala_czasu potega_madrosci eliksir_poszukiwacza training_grandmaster_skill ksiega_misji_wawoz remote_call; do \
      [ -f "/quest-add/$q.quest" ] || continue; \
      sed 's/\r$//' "/quest-add/$q.quest" > "/tmp/qc-work/$q.quest"; \
      ( cd /tmp/qc-work && /src/Server/game/src/quest/qc "$q.quest" ); \
      test -s "/tmp/qc-work/object/state/$q" \
        || { echo "FATAL: qc produced no state file for $q"; find /tmp/qc-work/object | head -50; exit 1; }; \
      cp -a "/tmp/qc-work/$q.quest" "$out/$q.quest"; \
    done; \
    test -d /tmp/qc-work/object/notarget/login \
      || { echo "FATAL: qc produced no login handler for web_admin"; exit 1; }; \
    cp -a /tmp/qc-work/object "$out/object"; \
    chmod -R a+rX "$out"; \
    echo "quest objects:"; find "$out/object" -type f | wc -l

# MT2009_PLUS_SKILL9_TALENT_V1: Mikstura Talentu (50527) trains the 9th skill G1 -> P (server-patches/skill9/README.md;
# the Soul Stones' training_grandmaster_skill stays the package's - it never offers a 9th skill). Compiled on its own
# into the objects above (qc-work still holds the stage's quest_functions with the engine's additions).
RUN set -eux; out=/out-quest/poland/quest; q=mikstura_talentu; \
    if [ ! -d /tmp/qc-work/object ] || [ ! -f "/quest-add/$q.quest" ]; then echo "note: no $q"; exit 0; fi; \
    sed 's/\r$//' "/quest-add/$q.quest" > "/tmp/qc-work/$q.quest"; \
    ( cd /tmp/qc-work && /src/Server/game/src/quest/qc "$q.quest" ); \
    test -s "/tmp/qc-work/object/state/$q"; \
    test -s "/tmp/qc-work/object/50527/use/$q.start"; \
    cp -a "/tmp/qc-work/$q.quest" "$out/$q.quest"; \
    mkdir -p "$out/object/state" "$out/object/50527/use"; \
    cp -a "/tmp/qc-work/object/state/$q" "$out/object/state/$q"; \
    cp -a "/tmp/qc-work/object/50527/use/$q.start" "$out/object/50527/use/$q.start"; \
    chmod -R a+rX "$out"; \
    echo "quest: $q (Mikstura Talentu)"

# MT2009_PLUS_HORSE40_V1: konie_rozwoj - the horse past level 21 (server-patches/konie/README.md: the Stajenny's window,
# the daily feed, the Zlota Ksiega Konia, the horse skill books 55050-55067, 50046 / 50047 / 50049). Compiled on its own
# with the engine's horse.konie_* functions (konie_rozwoj.cpp) added to the stage's quest_functions; every object it
# makes is copied into the objects above (its NPC chats, the item uses, kill and login).
RUN set -eux; out=/out-quest/poland/quest; q=konie_rozwoj; \
    if [ ! -d /tmp/qc-work/object ] || [ ! -f "/quest-add/$q.quest" ]; then echo "note: no $q"; exit 0; fi; \
    rm -rf /tmp/qc-konie; mkdir -p /tmp/qc-konie/object; \
    cp /tmp/qc-work/quest_functions /tmp/qc-konie/quest_functions; \
    for fn in horse.konie_otworz horse.konie_naucz horse.konie_zapomnij horse.konie_slot horse.konie_odswiez horse.konie_karm horse.set_stat0; do \
      grep -qx "$fn" /tmp/qc-konie/quest_functions || echo "$fn" >> /tmp/qc-konie/quest_functions; \
    done; \
    sed 's/\r$//' "/quest-add/$q.quest" > "/tmp/qc-konie/$q.quest"; \
    ( cd /tmp/qc-konie && /src/Server/game/src/quest/qc "$q.quest" ); \
    test -s "/tmp/qc-konie/object/state/$q"; \
    test -s "/tmp/qc-konie/object/50049/use/$q.start"; \
    cp -a "/tmp/qc-konie/$q.quest" "$out/$q.quest"; \
    cp -a /tmp/qc-konie/object/. "$out/object/"; \
    chmod -R a+rX "$out"; \
    echo "quest: $q (the horse past 21)"

# MT2009_PLUS_FISHING_GLOBAL_V1: rybak_wedki (the Rybak's free rod upgrade and Wedka Weglowa) and zloty_tunczyk (the
# golden tuna: release / cut / bait) - the talks are quest/libs/fishing/fishing.lua (lowienie/fishing.lua, below).
# Compiled on their own; every object they make is copied into the objects above.
RUN set -eux; out=/out-quest/poland/quest; \
    if [ ! -d /tmp/qc-work/object ]; then echo "note: no quest objects"; exit 0; fi; \
    rm -rf /tmp/qc-fish; mkdir -p /tmp/qc-fish/object; \
    cp /tmp/qc-work/quest_functions /tmp/qc-fish/quest_functions; \
    for q in rybak_wedki zloty_tunczyk; do \
      sed 's/\r$//' "/quest-add/$q.quest" > "/tmp/qc-fish/$q.quest"; \
      ( cd /tmp/qc-fish && /src/Server/game/src/quest/qc "$q.quest" ); \
      test -s "/tmp/qc-fish/object/state/$q"; \
      cp -a "/tmp/qc-fish/$q.quest" "$out/$q.quest"; \
    done; \
    test -s /tmp/qc-fish/object/9009/take/rybak_wedki.start; \
    test -s /tmp/qc-fish/object/27797/use/zloty_tunczyk.start; \
    cp -a /tmp/qc-fish/object/. "$out/object/"; \
    chmod -R a+rX "$out"; \
    echo "quest: rybak_wedki, zloty_tunczyk (MT2009_PLUS_FISHING_GLOBAL_V1)"

# -----------------------------------------------------------------------------
FROM ${BASE_IMAGE} AS runtime

ARG APT_MIRROR
ENV DEBIAN_FRONTEND=noninteractive

RUN if [ -n "${APT_MIRROR}" ]; then \
      sed -i -e "s|http://archive.ubuntu.com/ubuntu/|${APT_MIRROR}|g" \
             -e "s|http://security.ubuntu.com/ubuntu/|${APT_MIRROR}|g" \
             /etc/apt/sources.list.d/ubuntu.sources; \
    fi

# What `ldd` resolves on the two binaries: libstdc++, libgcc_s, libc, and -
# because the package's Makefiles link them dynamically (-lz, -lmd) - zlib and
# libmd. tzdata so the logs carry the operator's clock.
# Check-Date off, as in the panel: a Windows clock running behind makes apt
# refuse every Release file as "not valid yet" (Xewi, 19 September). Only this
# stage and the panel carry it - the deps stage is cached on every install that
# has built once, and a changed line there would rebuild every library.
RUN dpkg --add-architecture i386 \
 && apt-get -o Acquire::Check-Date=false update \
 && apt-get install -y --no-install-recommends \
        libc6:i386 libstdc++6:i386 libgcc-s1:i386 zlib1g:i386 libmd0:i386 \
        tzdata ca-certificates \
        mariadb-client \
 && rm -rf /var/lib/apt/lists/*

# Non-root: the game parses untrusted network input and needs no privilege
# beyond binding ports above 1024. The entrypoint starts as root only long
# enough to fix ownership of the state volume, then drops to this account.
RUN groupadd -r -g 2000 metin2 && useradd -r -u 2000 -g metin2 -d /opt/metin2 -s /usr/sbin/nologin metin2
# The rate spool is shared with the panel container; a FIXED gid in both
# images is what makes one volume usable from both.
RUN groupadd -r -g 2050 m2spool && usermod -a -G m2spool metin2

# ---- static half: never written at runtime, replaced by rebuilding the image
#      share/bin      the two binaries this build produced
#      share/CMD      the command permission table (a file, not a directory)
#      share/data     mob spawns, dungeons, pc tables
#      share/locale   quest objects, maps, translations (locale/poland)
#      share/package  (empty, kept because every core symlinks it)
#  There is no share/conf: the protos live in the database (PROTO_FROM_DB).
COPY --from=builder /out/game /opt/metin2/share/bin/game
COPY --from=builder /out/db   /opt/metin2/share/bin/db
COPY src/serverfiles/share/CMD     /opt/metin2/share/CMD
COPY src/serverfiles/share/data    /opt/metin2/share/data
COPY src/serverfiles/share/locale  /opt/metin2/share/locale
COPY src/serverfiles/share/package /opt/metin2/share/package

# What the r40250 image adds to its share, for the poland locale here
# (port/shareify.py renders the three files and this step):
#  * mob_drop_item.m3.append.txt - the level-30 weapon ladder's kill groups on
#    the guild map's cursed wolves;
#  * special_item_group.moonlight.txt - the Moonlight chest (50011) the bots
#    open, replacing the stock block (the reader keeps the first group per
#    vnum, so the stock one is cut out first);
#  * special_item_group.moonlight.custom.txt, when the operator made one -
#    their Moonlight chest (50011) instead of ours. No package, update or
#    launcher writes it, so an edit there survives them all (Piciu713,
#    26 September: an edit of the shipped file came back as the 16.09 one);
#  * special_item_group.unique_attr.txt - the ItemShop rings' and amulets' bonuses
#    (attr groups 100000-100005, MT2009_PLUS_UNIQUE_RING_BONUS_V1);
#  * special_item_group.starter.txt - the starter chest chain the playerbot
#    seed hands out and the package has no group for.
#  * special_item_group.cors.txt - the higher Cor Draconis grades (50256-50259)
#    open into dragon stones of their own grade (MT2009_PLUS_COR_GRADES_V1), and
#    so does the newer series 51501-51646 (its grade ranges, colours, "+" and
#    chests), which the stock file has no group for;
#  * special_item_group.goblin.txt - the Goblin board's money pouch (50023),
#    1 000 000 - 10 000 000 yang instead of the stock 10 000 - 50 000.
#  * special_item_group.dungeons.txt - the Razador (50270) and Nemere (50271)
#    boss chests the two dungeons' quests hand out (MT2009_PLUS_BOSS_CHESTS_V1).
#    And Skrzynia Berana-Setaou (54700), the Blue Dragon lair's (MT2009_PLUS_BERAN_CHEST_V1).
#  * special_item_group.rumi.txt - the Okey chests of Owsap's Rumi (50267-50269,
#    50275-50277) and their pools 950401-950403 (MT2009_PLUS_RUMI_V1).
#  * special_item_group.catchking.txt - Catch the King's three King's Loots
#    (50968-50970, MT2009_PLUS_CATCH_KING_V1).
COPY special_item_group.moonlight.custom*.txt mob_drop_item.m3.append.txt special_item_group.moonlight.txt special_item_group.starter.txt special_item_group.cors.txt special_item_group.dungeons.txt special_item_group.goblin.txt special_item_group.rumi.txt special_item_group.catchking.txt special_item_group.unique_attr.txt /tmp/share-add/
RUN set -eu; L=/opt/metin2/share/locale/poland \
 && for f in /tmp/share-add/*.txt; do sed -i '1s/^\xEF\xBB\xBF//; s/\r$//; s/$/\r/' "$f"; done \
 && m=/tmp/share-add/special_item_group.moonlight.txt; c=/tmp/share-add/special_item_group.moonlight.custom.txt \
 && if [ -s "$c" ]; then grep -q -E '^[[:blank:]]*Vnum[[:blank:]]+50011[[:space:]]*$' "$c" || { echo "FATAL: $c defines no Vnum 50011" >&2; exit 1; }; m="$c"; echo "share: the operator's Moonlight chest"; fi \
 && cat /tmp/share-add/mob_drop_item.m3.append.txt >> "$L/mob_drop_item.txt" \
 && f="$L/special_item_group.txt" \
 && awk 'BEGIN{keep=1} /^Group/{blk=""; keep=1} {blk=blk $0 "\n"} /Vnum[ \t]+(50011|50187|50212|50213|50188|50189|50190|50191|50192|50193|50194|50195|50196|50186|50254|50256|50257|50258|50259|50270|50271|50023|5026[789]|5027[567]|95040[123]|50968|50969|50970|515[0-9][0-9]|516[0-4][0-9])([^0-9]|$)/{keep=0} /^}/{ if (keep) printf "%s", blk; blk=""; keep=1 }' "$f" > "$f.new" \
 && cat "$m" /tmp/share-add/special_item_group.starter.txt /tmp/share-add/special_item_group.cors.txt /tmp/share-add/special_item_group.dungeons.txt /tmp/share-add/special_item_group.goblin.txt /tmp/share-add/special_item_group.rumi.txt /tmp/share-add/special_item_group.catchking.txt /tmp/share-add/special_item_group.unique_attr.txt >> "$f.new" \
 && test "$(grep -c -E '^[[:blank:]]*Vnum[[:blank:]]+(50968|50969|50970)([^0-9]|$)' "$f.new")" = 3 \
 && test "$(grep -c -E '^[[:blank:]]*Vnum[[:blank:]]+(50270|50271)([^0-9]|$)' "$f.new")" = 2 \
 && test "$(grep -c -E '^[[:blank:]]*Vnum[[:blank:]]+54700([^0-9]|$)' "$f.new")" = 1 \
 && test "$(grep -c -E '^[[:blank:]]*Vnum[[:blank:]]+(515[0-9][0-9]|516[0-4][0-9])([^0-9]|$)' "$f.new")" = 146 \
 && test "$(grep -c -E '^[[:blank:]]*Vnum[[:blank:]]+50023([^0-9]|$)' "$f.new")" = 1 \
 && test "$(grep -c -E '^[[:blank:]]*Vnum[[:blank:]]+(5026[789]|5027[567]|95040[123])([^0-9]|$)' "$f.new")" = 9 \
 && mv "$f.new" "$f" \
 && rm -rf /tmp/share-add \
 && echo "share: moonlight + starter + boss chests + Okey chests, M3 drops appended"

# MT2009_PLUS_PD_BONUS_V1 (server-patches/pdbonus): the map-90 Metins' Pierscien Doswiadczenia (39002) joins the experience
# rings' unique group 10000 (stock: 72001-72003, 72049, 72050, 70005) - outside it the ring gave nothing at all. In the group
# it gives the rings' +50% (item.cpp, POINT_RAMADAN_CANDY_BONUS_EXP) and cannot be worn with another ring of the group.
# The next free index (a group stops reading at the first index it lacks); once only.
RUN set -eu; f=/opt/metin2/share/locale/poland/special_item_group.txt \
 && awk 'BEGIN{g=0; n=0; has=0} /^[[:blank:]]*Group/{g=0} /^[[:blank:]]*Vnum[[:blank:]]+10000([^0-9]|$)/{g=1; n=0; has=0} g && $1 ~ /^[0-9]+$/ { n=$1+0; if ($2 == "39002") has=1 } g && /^[[:blank:]]*}/ { if (!has) { printf "\t%d\t39002\t1\t1\t-- Pierscien Doswiadczenia (Metiny map 90)\r\n", n+1; done=1 } g=0 } { print } END{ if (!done && !has) { print "FATAL: no unique group 10000" > "/dev/stderr"; exit 1 } }' "$f" > "$f.new" \
 && mv "$f.new" "$f" \
 && grep -q -E '^[[:blank:]]*[0-9]+[[:blank:]]+39002[[:blank:]]' "$f" \
 && echo "share: 39002 in the experience rings' group 10000"

# MT2009_PLUS_DRAGON_NO_ROTTEN_CHEST_V1: Beran-Setaou / the Blue Dragon (2493) no longer drops the
# Sprochniala Skrzynia (50124; the owner, 1 October). Its lines in the dragon's mob_drop_item groups
# get a 0 chance (the group's numbering stays as it is); every other mob keeps the chest.
RUN set -eu; F=/opt/metin2/share/locale/poland/mob_drop_item.txt \
 && awk 'BEGIN{d=0} /^[[:blank:]]*Group/{d=0} /^[[:blank:]]*Mob[[:blank:]]+2493([^0-9]|$)/{d=1} { if (d && $2 == "50124" && $1 ~ /^[0-9]+$/) { sub(/[0-9.]+([[:blank:]]*(--.*)?\r?)$/, "0" substr($0, match($0, /[[:blank:]]*(--.*)?\r?$/))); n++ } print } END{ if (n < 1) { print "FATAL: no 50124 line under mob 2493" > "/dev/stderr"; exit 1 } }' "$F" > "$F.new" \
 && mv "$F.new" "$F" \
 && echo "share: 2493 no longer drops 50124"

# MT2009_PLUS_DROP_EDIT_V1: the owner's edits of the drop workbook (1 October).
#  * mob_drop_item.dropedit.append.txt: the bosses' own new drops (Baronowna 9706, WuKong 9682,
#    Krol Skorpionow 9694, Azrael 2598, Krolowa Dzungli 9714 - a drop group joins one the mob may
#    already have) and the pseudo mob 98006, the drop group server-patches/raremobrules gives
#    Metin Ciemnosci inside Biblioteka Wiedzy;
#  * Beran-Setaou (2493): Malz x10 and Zwoj Blogoslawienstwa x5 (were 1) in its drop group,
#    Zaczarowanie / Wzmocnienie Przedmiotu x3 at 10% (was 0.2%) in its level-90 group;
#  * the shared boss groups: 10743 (Boss HighTier) Zwoj x5 and Peleryna Mestwa x20, 10755
#    (MiniBoss VeryHighTier) Zwoj x5 - every boss that rolls them.
#  * MT2009_PLUS_JEWELS75_LIMIT_V1: the level-80 jewellery of the Grotto of Exile's Commanders and
#    Generals (2491, 2492, 2494, 2495) is a limit group of theirs - none may have one before it.
# Razador's and Nemere's own drops are in their quests; the chests in special_item_group.dungeons.txt
# and arezzo/*.
COPY mob_drop_item.dropedit.append.txt /tmp/mob_drop_item.dropedit.append.txt
RUN set -eu; F=/opt/metin2/share/locale/poland/mob_drop_item.txt; G=/opt/metin2/share/locale/poland/special_item_group.txt; A=/tmp/mob_drop_item.dropedit.append.txt \
 && ! grep -q -E '^Group[[:blank:]]+MT2009_dropedit_' "$F" \
 && awk '{sub(/\r$/, "")} /^[[:blank:]]*Group/{t=""; m=""} tolower($1)=="mob"{m=$2} tolower($1)=="type"{t=tolower($2)} (t=="limit" && (m=="9714" || m=="2491" || m=="2492" || m=="2494" || m=="2495")) || m=="98006" {print "FATAL: mob " m " already has a " t " group" > "/dev/stderr"; bad=1; exit} END{exit bad}' "$F" \
 && sed -i 's/\r$//; s/$/\r/' "$A" \
 && { [ -z "$(tail -c 1 "$F")" ] || printf '\r\n' >> "$F"; } \
 && cat "$A" >> "$F" \
 && awk '{cr = sub(/\r$/, "")} /^[[:blank:]]*Group/{d=0; t=""} /^[[:blank:]]*Mob[[:blank:]]+2493([^0-9]|$)/{d=1} tolower($1)=="type"{t=tolower($2)} \
      { if (d && $1 ~ /^[0-9]+$/) { \
          if (t=="drop" && $3=="1" && ($2=="27987" || $2=="25040")) { c = ($2=="27987") ? 10 : 5; sub(/^[[:blank:]]*[0-9]+[[:blank:]]+[0-9]+[[:blank:]]+1[[:blank:]]/, "\t" $1 "\t" $2 "\t" c "\t"); n++ } \
          else if (t=="limit" && $3=="3" && ($2=="71084" || $2=="71085") && $4=="0.2") { sub(/[[:blank:]]0\.2([[:blank:]]|$)/, "\t10\t"); sub(/[[:blank:]]+$/, ""); n++ } } \
        printf "%s%s\n", $0, (cr ? "\r" : "") } \
      END{ if (n != 4) { print "FATAL: Beran lines changed: " n " (4 expected)" > "/dev/stderr"; exit 1 } }' "$F" > "$F.new" \
 && mv "$F.new" "$F" \
 && test "$(grep -c -E '^Group[[:blank:]]+MT2009_dropedit_' "$F")" = 9 \
 && awk '{cr = sub(/\r$/, "")} /^[[:blank:]]*Group/{v=""} tolower($1)=="vnum"{v=$2} \
      { if ($1 ~ /^[0-9]+$/ && $3=="1" && ((v=="10743" && ($2=="25040" || $2=="70038")) || (v=="10755" && $2=="25040"))) { c = ($2=="70038") ? 20 : 5; sub(/^[[:blank:]]*[0-9]+[[:blank:]]+[0-9]+[[:blank:]]+1[[:blank:]]/, "\t" $1 "\t" $2 "\t" c "\t"); n++ } \
        printf "%s%s\n", $0, (cr ? "\r" : "") } \
      END{ if (n != 3) { print "FATAL: shared boss group lines changed: " n " (3 expected)" > "/dev/stderr"; exit 1 } }' "$G" > "$G.new" \
 && mv "$G.new" "$G" \
 && rm -f "$A" \
 && echo "share: drop edit - 9 groups, Beran, shared groups 10743 / 10755"
# MT2009_PLUS_BERAN_DROP_V1: Beran-Setaou's (2493) drop as the pl-wiki lists it (the owner, 15 October) - the helmets
# +4 and the shard his stock group lacked, one drop group merged by the engine with his others (the file says which).
COPY mob_drop_item.beran.append.txt /tmp/mob_drop_item.beran.append.txt
RUN set -eu; F=/opt/metin2/share/locale/poland/mob_drop_item.txt; A=/tmp/mob_drop_item.beran.append.txt \
 && ! grep -q -E '^Group[[:blank:]]+MT2009_beran_' "$F" \
 && sed -i 's/\r$//; s/$/\r/' "$A" \
 && { [ -z "$(tail -c 1 "$F")" ] || printf '\r\n' >> "$F"; } \
 && cat "$A" >> "$F" \
 && rm -f "$A" \
 && test "$(grep -c -E '^Group[[:blank:]]+MT2009_beran_2493' "$F")" = 1 \
 && echo "share: Beran-Setaou's wiki drop appended"
# MT2009_PLUS_BOOTS_V1: Mleczny Sok (30192), a refine material of the level-65 boots, from Las Duchow's Driada, Duch
# Wierzby, Zle Drzewo and Duch Pniaka as on the pl-wiki (the owner, 15 October) - one drop group each.
COPY mob_drop_item.buty.append.txt /tmp/mob_drop_item.buty.append.txt
RUN set -eu; F=/opt/metin2/share/locale/poland/mob_drop_item.txt; A=/tmp/mob_drop_item.buty.append.txt \
 && ! grep -q -E '^Group[[:blank:]]+MT2009_buty_' "$F" \
 && sed -i 's/\r$//; s/$/\r/' "$A" \
 && { [ -z "$(tail -c 1 "$F")" ] || printf '\r\n' >> "$F"; } \
 && cat "$A" >> "$F" \
 && rm -f "$A" \
 && test "$(grep -c -E '^Group[[:blank:]]+MT2009_buty_' "$F")" = 4 \
 && echo "share: boots material Mleczny Sok - 4 groups"
# MT2009_PLUS_METIN_BEANS_V1: Green Dragon Bean (100300) at 2.5% from every Metin of level 70+
# (the owner, 3 October) - one small drop group per Metin, merged by the engine with any group
# the Metin already has.
COPY mob_drop_item.metinbeans.append.txt /tmp/mob_drop_item.metinbeans.append.txt
RUN set -eu; F=/opt/metin2/share/locale/poland/mob_drop_item.txt; A=/tmp/mob_drop_item.metinbeans.append.txt \
 && ! grep -q -E '^Group[[:blank:]]+MT2009_metinbean_' "$F" \
 && sed -i 's/\r$//; s/$/\r/' "$A" \
 && { [ -z "$(tail -c 1 "$F")" ] || printf '\r\n' >> "$F"; } \
 && cat "$A" >> "$F" \
 && rm -f "$A" \
 && echo "share: metin beans - $(grep -c -E '^Group[[:blank:]]+MT2009_metinbean_' "$F") groups"
# MT2009_PLUS_DT_DROPS_V1: the Demon Tower's brutal demons (1061-1071, the second life of every
# demon of floors 2-9) drop the tower's upgrade items 30086 / 30087 and level-65 weapons +0 as junk
# (the owner, 5 October) - one drop group each, merged by the engine with any group the mob has.
# The level fade inside the tower is server-patches/raremobrules (MT2009_PLUS_DT_DROPS_V1 (delta)).
COPY mob_drop_item.dtdrops.append.txt /tmp/mob_drop_item.dtdrops.append.txt
RUN set -eu; F=/opt/metin2/share/locale/poland/mob_drop_item.txt; A=/tmp/mob_drop_item.dtdrops.append.txt \
 && ! grep -q -E '^Group[[:blank:]]+MT2009_dtdrop_' "$F" \
 && sed -i 's/\r$//; s/$/\r/' "$A" \
 && { [ -z "$(tail -c 1 "$F")" ] || printf '\r\n' >> "$F"; } \
 && cat "$A" >> "$F" \
 && test "$(grep -c -E '^Group[[:blank:]]+MT2009_dtdrop_10(6[1-9]|7[01])([^0-9]|$)' "$F")" = 11 \
 && rm -f "$A" \
 && echo "share: Demon Tower brutal demons - 11 drop groups"
# MT2009_PLUS_ORNAMENT_DROP_V1: Ornament (30031, the talisman's refine material) from the Sworn
# Archers 302 / 332 at the start of the second villages, 2% a kill on top of their etc drop (the
# owner, 7 October) - one drop group each, merged by the engine with the archers' own group.
COPY mob_drop_item.ornaments.append.txt /tmp/mob_drop_item.ornaments.append.txt
RUN set -eu; F=/opt/metin2/share/locale/poland/mob_drop_item.txt; A=/tmp/mob_drop_item.ornaments.append.txt \
 && ! grep -q -E '^Group[[:blank:]]+MT2009_ornament_' "$F" \
 && sed -i 's/\r$//; s/$/\r/' "$A" \
 && { [ -z "$(tail -c 1 "$F")" ] || printf '\r\n' >> "$F"; } \
 && cat "$A" >> "$F" \
 && test "$(grep -c -E '^Group[[:blank:]]+MT2009_ornament_(302|332)([^0-9]|$)' "$F")" = 2 \
 && rm -f "$A" \
 && echo "share: Sworn Archers' ornaments - 2 drop groups"

# MT2009_PLUS_FLOWER_V1: the Flower Event's five gift boxes (83023-83027, Pudelko z Chryzantema ..
# ze Slonecznikiem; playerbot_flower.h gives them for 10 shoots of a flower), opened by their
# special_item_group groups. Appended once; the Seban panel's "Szkatulki" page edits them like any
# other chest (m2-chests). Their items and the five flowers 25121-25125 are mariadb/playerbot/apply.sh rows.
COPY special_item_group.flower.txt /tmp/special_item_group.flower.txt
RUN set -eu; f=/opt/metin2/share/locale/poland/special_item_group.txt; a=/tmp/special_item_group.flower.txt \
 && sed -i '1s/^\xEF\xBB\xBF//; s/\r$//; s/$/\r/' "$a" \
 && if ! grep -q -E '^[[:blank:]]*Vnum[[:blank:]]+8302[3-7]([^0-9]|$)' "$f"; then \
      { [ -z "$(tail -c 1 "$f")" ] || printf '\r\n' >> "$f"; }; cat "$a" >> "$f"; \
    fi \
 && test "$(grep -c -E '^[[:blank:]]*Vnum[[:blank:]]+8302[3-7]([^0-9]|$)' "$f")" = 5 \
 && rm -f "$a" \
 && echo "share: Flower Event gift boxes 83023-83027"

# MT2009_PLUS_HALLOWEEN_V1: the Halloween Chest (50215, Upiorna Skrzynia; Autor: Owsap - the event,
# quest/event_halloween_hair.quest), which neither the package nor Owsap has a group for. Appended
# once, after any group of the same vnum is cut out; the Seban panel's "Szkatulki" page edits it.
COPY special_item_group.halloween.txt /tmp/special_item_group.halloween.txt
RUN set -eu; f=/opt/metin2/share/locale/poland/special_item_group.txt; a=/tmp/special_item_group.halloween.txt \
 && sed -i '1s/^\xEF\xBB\xBF//; s/\r$//; s/$/\r/' "$a" \
 && awk 'BEGIN{keep=1} /^Group/{blk=""; keep=1} {blk=blk $0 "\n"} /Vnum[ \t]+50215([^0-9]|$)/{keep=0} /^}/{ if (keep) printf "%s", blk; blk=""; keep=1 }' "$f" > "$f.new" \
 && { [ -z "$(tail -c 1 "$f.new")" ] || printf '\r\n' >> "$f.new"; } \
 && cat "$a" >> "$f.new" \
 && test "$(grep -c -E '^[[:blank:]]*Vnum[[:blank:]]+50215([^0-9]|$)' "$f.new")" = 1 \
 && mv "$f.new" "$f" && rm -f "$a" \
 && echo "share: Halloween Chest 50215"

# MT2009_PLUS_RELIC_V1: Pakiet Dusz (30263, special_item_group.relikty.txt - tools/relikty/gen_relikty.py): one of
# each soul of Bonus Reliktu (Type Pct). Appended once, after any group of the same vnum is cut out.
COPY special_item_group.relikty.txt /tmp/special_item_group.relikty.txt
RUN set -eu; f=/opt/metin2/share/locale/poland/special_item_group.txt; a=/tmp/special_item_group.relikty.txt \
 && sed -i '1s/^\xEF\xBB\xBF//; s/\r$//; s/$/\r/' "$a" \
 && awk 'BEGIN{keep=1} /^Group/{blk=""; keep=1} {blk=blk $0 "\n"} /Vnum[ \t]+30263([^0-9]|$)/{keep=0} /^}/{ if (keep) printf "%s", blk; blk=""; keep=1 }' "$f" > "$f.new" \
 && { [ -z "$(tail -c 1 "$f.new")" ] || printf '\r\n' >> "$f.new"; } \
 && cat "$a" >> "$f.new" \
 && test "$(grep -c -E '^[[:blank:]]*Vnum[[:blank:]]+30263([^0-9]|$)' "$f.new")" = 1 \
 && mv "$f.new" "$f" && rm -f "$a" \
 && echo "share: Pakiet Dusz 30263"

# MT2009_PLUS_HORSE40_V1: Zestaw Opieki nad Koniem (83050, special_item_group.konie.txt - tools/konie/gen_konie.py):
# Pasza dla Konia x50, Czer. Zen-szen (premium) x5, Szlachetna Trawa (Type Pct). Appended once, after any group of the
# same vnum is cut out.
COPY special_item_group.konie.txt /tmp/special_item_group.konie.txt
RUN set -eu; f=/opt/metin2/share/locale/poland/special_item_group.txt; a=/tmp/special_item_group.konie.txt \
 && sed -i '1s/^\xEF\xBB\xBF//; s/\r$//; s/$/\r/' "$a" \
 && awk 'BEGIN{keep=1} /^Group/{blk=""; keep=1} {blk=blk $0 "\n"} /Vnum[ \t]+83050([^0-9]|$)/{keep=0} /^}/{ if (keep) printf "%s", blk; blk=""; keep=1 }' "$f" > "$f.new" \
 && { [ -z "$(tail -c 1 "$f.new")" ] || printf '\r\n' >> "$f.new"; } \
 && cat "$a" >> "$f.new" \
 && test "$(grep -c -E '^[[:blank:]]*Vnum[[:blank:]]+83050([^0-9]|$)' "$f.new")" = 1 \
 && mv "$f.new" "$f" && rm -f "$a" \
 && echo "share: Zestaw Opieki nad Koniem 83050"

# MT2009_PLUS_FISH_PUZZLE_V1: Zl. Skrzynia na Ryby (M) / (S) / (D) (83001-83003, special_item_group.fishpuzzle.txt) - the
# rewards of Event Rybacki - Puzzle (fish_puzzle.cpp). Appended once, after any group of the same vnums is cut out.
COPY special_item_group.fishpuzzle.txt /tmp/special_item_group.fishpuzzle.txt
RUN set -eu; f=/opt/metin2/share/locale/poland/special_item_group.txt; a=/tmp/special_item_group.fishpuzzle.txt \
 && sed -i '1s/^\xEF\xBB\xBF//; s/\r$//; s/$/\r/' "$a" \
 && awk 'BEGIN{keep=1} /^Group/{blk=""; keep=1} {blk=blk $0 "\n"} /Vnum[ \t]+(8300[1-3])([^0-9]|$)/{keep=0} /^}/{ if (keep) printf "%s", blk; blk=""; keep=1 }' "$f" > "$f.new" \
 && { [ -z "$(tail -c 1 "$f.new")" ] || printf '\r\n' >> "$f.new"; } \
 && cat "$a" >> "$f.new" \
 && test "$(grep -c -E '^[[:blank:]]*Vnum[[:blank:]]+8300[1-3]([^0-9]|$)' "$f.new")" = 3 \
 && mv "$f.new" "$f" && rm -f "$a" \
 && echo "share: Zl. Skrzynie na Ryby 83001-83003"

# MT2009_PLUS_YUTNORI_V1: the Yut Nori trophies and bundles (83030-83034,
# special_item_group.yutnori.txt; playerbot_yutnori.h hands them out). Appended
# once, after any stock group of the same vnums is cut out (the reader keeps
# the first group per vnum).
COPY special_item_group.yutnori.txt /tmp/special_item_group.yutnori.txt
RUN set -eu; f=/opt/metin2/share/locale/poland/special_item_group.txt; a=/tmp/special_item_group.yutnori.txt \
 && sed -i '1s/^\xEF\xBB\xBF//; s/\r$//; s/$/\r/' "$a" \
 && awk 'BEGIN{keep=1} /^Group/{blk=""; keep=1} {blk=blk $0 "\n"} /Vnum[ \t]+(8303[0-4])([^0-9]|$)/{keep=0} /^}/{ if (keep) printf "%s", blk; blk=""; keep=1 }' "$f" > "$f.new" \
 && cat "$a" >> "$f.new" \
 && test "$(grep -c -E '^[[:blank:]]*Vnum[[:blank:]]+8303[0-4]([^0-9]|$)' "$f.new")" = 5 \
 && mv "$f.new" "$f" && rm -f "$a" \
 && echo "share: Yut Nori boxes 83030-83034"

# The alchemy bonuses (server-patches/dragonsoulbalance): the package's
# BasicApplys and AdditionalApplys groups of dragon_soul_table.txt give way to
# the MT2009 Plus balance - no elemental resistance, a race bonus instead of
# the elemental one, the Amethyst's Sungma bonuses gone, the strong ones
# smaller. The engine half (the apply names the table may use) is
# dragon_soul_table.cpp, MT2009_PLUS_DS_APPLYS_V1.
COPY dragon_soul_applys.mt2009plus.txt /tmp/dragon_soul_applys.txt
RUN set -eu; f=/opt/metin2/share/locale/poland/dragon_soul_table.txt \
 && sed -i 's/\r$//; s/$/\r/' /tmp/dragon_soul_applys.txt \
 && awk -v add=/tmp/dragon_soul_applys.txt 'BEGIN{skip=0} /^Group[ \t]+BasicApplys/{ while ((getline l < add) > 0) print l; skip=1; next } skip && /^Group[ \t]+ApplyNumSettings/{ skip=0 } !skip{ print }' "$f" > "$f.new" \
 && grep -q 'ATTBONUS_MILGYO' "$f.new" && grep -q '^Group[[:blank:]]*ApplyNumSettings' "$f.new" \
 && ! grep -Eq '^[^#]*(RESIST_(ICE|FIRE|WIND|EARTH|ELEC|DARK)|ENCHANT_|SUNGMA_)' "$f.new" \
 && mv "$f.new" "$f" && rm -f /tmp/dragon_soul_applys.txt \
 && echo "share: MT2009 Plus alchemy bonuses"

# MT2009_PLUS_DS_GLOBAL_TABLE_V1 (server-patches/bonusyglobal): the alchemy of
# M2_BONUS_MODE=global - the default bonus groups (Owsap/GF, without Szafir's
# two Wolfman lines) in the same table, as dragon_soul_table.global.txt; the
# mt2009 table kept as dragon_soul_table.mt2009.txt. A core loads the global
# one in place of dragon_soul_table.txt when the mode is global and keeps the
# other two for a stone made under the other mode (DragonSoul.cpp).
COPY dragon_soul_applys.global.txt /tmp/dragon_soul_applys.global.txt
RUN set -eu; L=/opt/metin2/share/locale/poland; f=$L/dragon_soul_table.txt; g=$L/dragon_soul_table.global.txt \
 && cp -p "$f" "$L/dragon_soul_table.mt2009.txt" \
 && sed -i 's/\r$//; s/$/\r/' /tmp/dragon_soul_applys.global.txt \
 && awk -v add=/tmp/dragon_soul_applys.global.txt 'BEGIN{skip=0} /^Group[ \t]+BasicApplys/{ while ((getline l < add) > 0) print l; skip=1; next } skip && /^Group[ \t]+ApplyNumSettings/{ skip=0 } !skip{ print }' "$f" > "$g" \
 && grep -q 'ENCHANT_ICE' "$g" && grep -q 'SUNGMA_HP' "$g" && grep -q '^Group[[:blank:]]*ApplyNumSettings' "$g" \
 && ! grep -q 'WOLFMAN' "$g" && ! grep -q 'ATTBONUS_MILGYO' "$g" \
 && test "$(sed -n '/^Group[[:blank:]]*ApplyNumSettings/,$p' "$g" | md5sum)" = "$(sed -n '/^Group[[:blank:]]*ApplyNumSettings/,$p' "$f" | md5sum)" \
 && rm -f /tmp/dragon_soul_applys.global.txt \
 && echo "share: alchemy table of M2_BONUS_MODE=global"

# Maska Sabaha goes with the Hwang curse (playerbotify apply_hwang_curse_removed,
# port/shareify.py renders this step): its drop lines and the Hwang loot box roll
# it at nothing - a group stops reading at the first index it lacks, so a line is
# zeroed, not deleted - and the temple's introduction hands none out.
RUN set -eu; L=/opt/metin2/share/locale/poland \
 && sed -i -E 's/^([[:blank:]]*[0-9]+[[:blank:]]+7273[15][[:blank:]]+[0-9]+[[:blank:]]+)[0-9.]+/\10/' "$L/mob_drop_item.txt" \
 && sed -i -E '/^Group[[:blank:]]+LootBox_Hwang/,/^}/ s/^([[:blank:]]*[0-9]+[[:blank:]]+7273[15][[:blank:]]+[0-9]+[[:blank:]]+)[0-9.]+/\10/' "$L/special_item_group.txt" \
 && sed -i '/^reward_data\.hwang_introduction/,/^}/ { /{72731, 1},/d }' "$L/quest/libs/other/reward_data.lua" \
 && ! grep -E '^[[:blank:]]*[0-9]+[[:blank:]]+7273[15][[:blank:]]+[0-9]+[[:blank:]]+[1-9]' "$L/mob_drop_item.txt" \
 && ! grep -q '{72731, 1}' "$L/quest/libs/other/reward_data.lua" \
 && echo "share: Maska Sabaha removed"

# MT2009_PLUS_ANTI_RESIST_MAGIC_V1 (server-patches/antimagic; the owner, 28 October 2026: "Drop like all the other
# stones"): Kamien Duszy Antymagii (28g44) and Bialy Kamien Antymagii (28g45) wherever the package lists the 14 soul
# stone kinds - the groups Kamien_Duszy_0..4 (10980-10984, one line each at the same weight 1; the Losowy_Kamien_Duszy
# groups and every chest that names them follow) and Silna Lodowa Wiedzma's ice_witch (the +4 at 1 50 15 like the
# others; the lines after them renumbered - a group stops reading at the first index it lacks). The Metins draw them in
# the engine (char.cpp). Once (a file that has them is left alone).
RUN set -eu; L=/opt/metin2/share/locale/poland; f="$L/special_item_group.txt"; m="$L/mob_drop_item.txt" \
 && if ! grep -q -E '^[[:blank:]]+15[[:blank:]]+28044[[:blank:]]' "$f"; then \
      awk '/^Group/{g=$2; sub(/\r$/,"",g)} {print} g ~ /^Kamien_Duszy_[0-4]$/ && $1=="14" && $2 ~ /^28[0-4]43$/ { n=substr($2,3,1); printf "\t15\t28%s44\t1\t1\t-- Kamien Duszy Antymagii+%s\r\n\t16\t28%s45\t1\t1\t-- Bialy Kamien Antymagii+%s\r\n", n, n, n, n }' "$f" > "$f.new" \
      && mv "$f.new" "$f"; \
    fi \
 && test "$(grep -c -E '^[[:blank:]]+1[56][[:blank:]]+28[0-4]4[45][[:blank:]]+1[[:blank:]]+1[[:blank:]]' "$f")" = 10 \
 && if ! grep -q -E '^[[:blank:]]+[0-9]+[[:blank:]]+28444[[:blank:]]+1[[:blank:]]+50[[:blank:]]' "$m"; then \
      awk '/^Group/{g=$2; sub(/\r$/,"",g); sh=0} g=="ice_witch" && sh && $1 ~ /^[0-9]+$/ { l=$0; sub(/^[ \t]*[0-9]+/, "\t" ($1+sh), l); print l; next } {print} g=="ice_witch" && $2=="28443" { printf "\t%d\t28444\t1\t50\t15\t-- Kamien Duszy Antymagii+4\r\n\t%d\t28445\t1\t50\t15\t-- Bialy Kamien Antymagii+4\r\n", $1+1, $1+2; sh=2 }' "$m" > "$m.new" \
      && mv "$m.new" "$m"; \
    fi \
 && test "$(grep -c -E '^[[:blank:]]+[0-9]+[[:blank:]]+2844[45][[:blank:]]+1[[:blank:]]+50[[:blank:]]+15' "$m")" = 2 \
 && echo "share: Kamien Antymagii in Kamien_Duszy_0..4 and ice_witch"

# MT2009_PLUS_TEMPLE_CURSE_REMOVED_V1: what the Hwang curse left behind. The
# package's temple_map quest put the curse's affect (AFFECT_TEMPLE_CURSE, 306:
# "Klatwa Swiatyni ... Efekt nigdy sie nie konczy", an icon and nothing else
# since the curse went) on everybody logging in on map 65, and hwang_introduction
# (Nabira's "Ucieczka Nabiry", whose reward and shop were the Maska Sabaha) still
# dropped its List Gonczy (35004) off the temple's monsters 702-707 and handed
# out a Kamien Tygrysa (35003) for nothing (owner, 23 October: "usun ikonke
# Klatwy Swiatyni ... usun tez caly quest i system dropu z tym zwiazany"). Their
# handlers go, their state tables stay for the flags characters already carry;
# apply.sh takes the two quest items out of the bags once.
RUN set -eu; O=/opt/metin2/share/locale/poland/quest/object \
 && test -f "$O/notarget/login/temple_map.start" \
 && n=$(find "$O" -path "$O/state" -prune -o -type f \( -name 'temple_map.*' -o -name 'hwang_introduction.*' \) -print | wc -l) \
 && find "$O" -path "$O/state" -prune -o -type f \( -name 'temple_map.*' -o -name 'hwang_introduction.*' \) -exec rm -f {} + \
 && ! find "$O" -path "$O/state" -prune -o -type f \( -name 'temple_map.*' -o -name 'hwang_introduction.*' \) -print | grep -q . \
 && ! grep -rl 'AFFECT_TEMPLE_CURSE' "$O" --exclude-dir=state | grep -q . \
 && echo "share: Temple curse quests removed ($n handlers)"

# MT2009_PLUS_FISHING_FREE_V1: fishing without the Fisherman's introduction or
# Karta Wedkarska (owner, 27 October: "Z yohary usun calkowicie quest wedkarski,
# wraz z karta wedkarska, teraz mozna lowic od 30 poziomu kiedy sie chce i ile
# sie chce, bez ograniczen"). The package's fishing_onboarding (the Fisherman,
# Baek-Go, Uriel, Esencja Natury / Wody and the Oczyszczajacy Amulet Wod) loses
# its handlers; its state table stays for the flags characters already carry.
# fishing_quest (the catch itself) and fisher (his shop, the rod upgrade) stay.
# The engine's fishing() asks neither the quest's flag nor the card any more
# (server-patches/enginefixes) and apply.sh takes the card and the quest's
# items out of the bags once.
RUN set -eu; O=/opt/metin2/share/locale/poland/quest/object \
 && test -f "$O/state/fishing_quest" \
 && n=$(find "$O" -path "$O/state" -prune -o -type f -name 'fishing_onboarding.*' -print | wc -l) \
 && find "$O" -path "$O/state" -prune -o -type f -name 'fishing_onboarding.*' -exec rm -f {} + \
 && ! find "$O" -path "$O/state" -prune -o -type f -name 'fishing_onboarding.*' -print | grep -q . \
 && echo "share: fishing introduction removed ($n handlers)"

# Costumes, mounts, pets and weapon skins come from the ItemShop only
# (operator, 26 September 2026: players found mounts in Metin stones and
# chests). The world's item table gave two vnums of the old drop lines to
# ItemShop mounts - 71282 (Ekstraktor Skaz, gone) is the Niebieski Oldtimer
# and 71294 (the ItemShop's Rada Pustelnika) the Feniks Zmierzchu - so every
# kill, boss chest, mission book and fishing catch that rolled those rolled a
# mount. 71294 becomes the Rada Pustelnika that exists (71094); 71282 and the
# Pieczec Dzika Wojennego (71125) of the Tajemnicza Skrzynia roll at nothing -
# a group stops reading at the first index it lacks, so a line is zeroed, not
# deleted; the fishing table's row is commented out.
RUN set -eu; L=/opt/metin2/share/locale/poland \
 && for f in "$L/mob_drop_item.txt" "$L/special_item_group.txt"; do \
      sed -i -E 's/^([[:blank:]]*[0-9]+[[:blank:]]+)71294([[:blank:]])/\171094\2/' "$f"; \
      sed -i -E 's/^([[:blank:]]*[0-9]+[[:blank:]]+(71282|71125)[[:blank:]]+[0-9]+[[:blank:]]+)[0-9.]+/\10/' "$f"; \
      if grep -Eq '^[[:blank:]]*[0-9]+[[:blank:]]+71294[[:blank:]]' "$f" || \
         grep -Eq '^[[:blank:]]*[0-9]+[[:blank:]]+(71282|71125)[[:blank:]]+[0-9]+[[:blank:]]+[0-9.]*[1-9]' "$f"; then \
        echo "share: a mount still drops in $f" >&2; exit 1; \
      fi; \
    done \
 && F="$L/quest/libs/fishing/fishing_drop.lua" \
 && sed -i -E 's/^([[:blank:]]*)(71282,[[:blank:]]*1,)/\1-- \2/' "$F" \
 && ! grep -Eq '^[[:blank:]]*71282,' "$F" \
 && echo "share: costumes and mounts from the ItemShop only"

# MT2009_PLUS_GOBLIN_V1: Treasure Island (map 419) of the Treasure Hunt event
# (playerbot_goblin.h) - the map from the "Official Treasure Hunt System"
# archive, its line in the map index, and the Treasure Goblin's and the
# Giant Treasure Chest's motions (treasure_hunt/README.txt). Which core hosts
# it is m2-render-config's (MAPS_game2).
COPY treasure_hunt/ /tmp/treasure_hunt/
RUN set -eu; L=/opt/metin2/share/locale/poland; D=/opt/metin2/share/data/monster \
 && rm -rf "$L/map/metin2_map_treasure_hunt" \
 && cp -a /tmp/treasure_hunt/map/metin2_map_treasure_hunt "$L/map/metin2_map_treasure_hunt" \
 && LC_ALL=C sed -i '/^419[[:blank:]]/d' "$L/map/index" \
 && if [ -n "$(tail -c 1 "$L/map/index")" ]; then printf '\r\n' >> "$L/map/index"; fi \
 && printf '419\tmetin2_map_treasure_hunt\r\n' >> "$L/map/index" \
 && for m in treasure_hunt_goblin treasure_hunt_box; do rm -rf "$D/$m"; cp -a "/tmp/treasure_hunt/monster/$m" "$D/$m"; done \
 && chmod -R a+rX "$L/map/metin2_map_treasure_hunt" "$D/treasure_hunt_goblin" "$D/treasure_hunt_box" \
 && rm -rf /tmp/treasure_hunt \
 && test -s "$L/map/metin2_map_treasure_hunt/server_attr" \
 && echo "share: Treasure Island (419) and the goblin's motions"

# The quest texts name this world, not Metin2009 (port/shareify.py renders this
# step): the substitution l0st3k's translate.lua of 15 September makes, on both
# copies of the file.
RUN set -eu; L=/opt/metin2/share/locale/poland \
 && for f in "$L/translate.lua" "$L/quest/libs/translate/translate.lua"; do \
      [ -f "$f" ] || continue; \
      LC_ALL=C sed -i 's/Metin2009/Metin2 SinglePlayer/g' "$f"; \
      if LC_ALL=C grep -q 'Metin2009' "$f"; then echo "share: Metin2009 left in $f" >&2; exit 1; fi; \
    done \
 && echo "share: Metin2 SinglePlayer in the quest texts"

# The world's difficulty (port/shareify.py renders this step): m2_difficulty.lua
# is dofile'd after the quest libraries and puts the Biologist's wait and the
# stable keeper's waits on event flags the migrator writes from M2_DIFFICULTY.
# It replaces the 2.0.55 sed that made collect_data.is_research_in_progress
# answer false for everybody (namiot_, 15 September): that is what "easy" is.
COPY quest/m2_difficulty.lua /opt/metin2/share/locale/poland/quest/libs/other/m2_difficulty.lua
RUN set -eu; L=/opt/metin2/share/locale/poland/quest/libs/other/_otherModuleLoader.lua \
 && LC_ALL=C grep -q 'other/collect_data.lua' "$L" \
 && LC_ALL=C sed -i 's/\r$//' "$L" \
 && printf '\ndofile( LIBDIR .. "other/m2_difficulty.lua")\n' >> "$L" \
 && LC_ALL=C grep -q 'other/m2_difficulty.lua' "$L" \
 && test -s /opt/metin2/share/locale/poland/quest/libs/other/m2_difficulty.lua \
 && echo "share: difficulty hooked into the quest libraries"

# MT2009_PLUS_LANGUAGE_V1 (server-patches/language/README.md): the game in the language each player reads. The
# dictionaries lang/<code>/*.tsv (Polish<TAB>translation, UTF-8; tools/i18n/build_server_lang.py makes 10_/20_ and the
# names, 30_/35_/40_ are by hand) go to share/locale/poland/lang - a language is a folder, read when its first reader
# comes; quest/mt2009_language.lua (the engine loads it after locale.lua) hands the quest window's texts to mt2009_tr().
COPY quest/mt2009_language.lua /opt/metin2/share/locale/poland/quest/mt2009_language.lua
COPY lang/ /opt/metin2/share/locale/poland/lang/
RUN set -eu; L=/opt/metin2/share/locale/poland \
 && test -s "$L/quest/mt2009_language.lua" \
 && test -s "$L/lang/en/10_quest_stock.tsv" \
 && ! LC_ALL=C grep -q -P '[\x80-\xff]' "$L/quest/mt2009_language.lua" \
 && echo "share: languages $(ls "$L/lang" | tr '\n' ' ')"

# MT2009_PLUS_MIKSTURY_V1 (the owner, 4 November 2026; server-patches/mikstury/README.md): m2_mikstury_limity.lua is
# dofile'd after m2_difficulty.lua and before m2_mikstury.lua (the step below wraps what it sets) and replaces
# potion_system.use_potion - the herbal potions and the grilled fish (item type 36) with no group limit, no block by an
# ItemShop speed potion, the same bonus refreshed or upgraded (a weaker one refused), the fish exceptions (the EXP fish
# 27879 < 27883 < 27887 never together, Zloty Karas 27883 and Krab Krolewski 27886 exclude each other). The package's
# compiled herb_pick timer of quest herbalism calls m2_mikstury_limity.herb_picked() after a successful pick (Zlote
# Ziolo 50741, 1%, decision M3).
COPY quest/m2_mikstury_limity.lua /opt/metin2/share/locale/poland/quest/libs/other/m2_mikstury_limity.lua
RUN set -eu; L=/opt/metin2/share/locale/poland; O="$L/quest/libs/other/_otherModuleLoader.lua" \
 && LC_ALL=C grep -q 'other/m2_difficulty.lua' "$O" \
 && LC_ALL=C grep -q 'other/potion_system.lua' "$O" \
 && ! LC_ALL=C grep -q 'other/m2_mikstury.lua' "$O" \
 && if ! LC_ALL=C grep -q 'other/m2_mikstury_limity.lua' "$O"; then printf 'dofile( LIBDIR .. "other/m2_mikstury_limity.lua")\n' >> "$O"; fi \
 && test "$(LC_ALL=C grep -c 'other/m2_mikstury_limity.lua' "$O")" -eq 1 \
 && test -s "$L/quest/libs/other/m2_mikstury_limity.lua" \
 && H="$L/quest/object/herb_pick/timer/herbalism.start" \
 && test "$(tr -d '\r' < "$H" | LC_ALL=C grep -c '^pc \. add_player_stat ( PLAYER_STATS_HERBALISM_FLAG , item_count ) $')" -eq 1 \
 && if ! LC_ALL=C grep -q 'm2_mikstury_limity' "$H"; then LC_ALL=C sed -i 's/^\(pc \. add_player_stat ( PLAYER_STATS_HERBALISM_FLAG , item_count ) \)\(\r\?\)$/\1\2\nm2_mikstury_limity . herb_picked ( ) \2/' "$H"; fi \
 && test "$(tr -d '\r' < "$H" | LC_ALL=C grep -c '^m2_mikstury_limity \. herb_picked ( ) $')" -eq 1 \
 && echo "share: potions with no group limit, the fish exceptions, Zlote Ziolo from herbs (MT2009_PLUS_MIKSTURY_V1)"

# MT2009_PLUS_BIOLOG_ELIKSIR_V1 / MT2009_PLUS_MIKSTURY_WYCOFANE_V1 (the owner, 3 November 2026): m2_mikstury.lua is
# dofile'd after m2_difficulty.lua and wraps potion_system.use_potion (Mikstura Geniuszu 51782, Mikstura Determinacji
# 51783 and Mikstura Szybkiej Analizy 51785 refused - withdrawn, not on the pl-wiki) and collect_data.take_chance
# (Eliksir Poszukiwacza: the next research hand-in at half as much again, 60% -> 90%). The three potions leave
# Baek-Go's board (crafting_data.lua rows 71, 72, 74; apply.sh deletes them from world.crafting_proto) and their
# recipes (50932, 50933, 50935) leave the "super receptury" group s50902 - zeroed, not deleted (a group stops reading at
# the first index it lacks), so s50902 now always gives Receptura Mikstura Madrosci (50930) - rolled at a quarter of
# its old rate (MT2009_PLUS_RECEPTURY_SUPER_V1 below), so that recipe drops as often as before.
COPY quest/m2_mikstury.lua /opt/metin2/share/locale/poland/quest/libs/other/m2_mikstury.lua
RUN set -eu; L=/opt/metin2/share/locale/poland; O="$L/quest/libs/other/_otherModuleLoader.lua" \
 && LC_ALL=C grep -q 'other/m2_difficulty.lua' "$O" \
 && if ! LC_ALL=C grep -q 'other/m2_mikstury.lua' "$O"; then printf 'dofile( LIBDIR .. "other/m2_mikstury.lua")\n' >> "$O"; fi \
 && test "$(LC_ALL=C grep -c 'other/m2_mikstury.lua' "$O")" -eq 1 \
 && test -s "$L/quest/libs/other/m2_mikstury.lua" \
 && C="$L/quest/libs/crafting/crafting_data.lua" \
 && LC_ALL=C sed -i -E 's/^([[:blank:]]*67, 68, )71, 72, 73, 74, (78,\r?)$/\173, \2/' "$C" \
 && test "$(tr -d '\r' < "$C" | LC_ALL=C grep -c -E '^[[:blank:]]*67, 68, 73, 78,$')" -eq 1 \
 && ! tr -d '\r' < "$C" | LC_ALL=C grep -q -E '(^|[^0-9])(71|72|74),' \
 && S="$L/special_item_group.txt" \
 && LC_ALL=C sed -i -E '/^Group[[:blank:]]+Receptury_Super/,/^}/ s/^([[:blank:]]*[0-9]+[[:blank:]]+5093[235][[:blank:]]+[0-9]+[[:blank:]]+)[0-9.]+/\10/' "$S" \
 && test "$(sed -n '/^Group[[:blank:]]*Receptury_Super/,/^}/p' "$S" | LC_ALL=C grep -c -E '^[[:blank:]]*[0-9]+[[:blank:]]+5093[235][[:blank:]]+[0-9]+[[:blank:]]+0([[:blank:]]|$)')" -eq 3 \
 && echo "share: Eliksir Poszukiwacza and the withdrawn Baek-Go potions (m2_mikstury.lua)"

# MT2009_PLUS_RECEPTURY_SUPER_V1 (the owner, 3 November 2026): with three of its four recipes zeroed (the step above)
# s50902 gave Receptura Mikstura Madrosci (50930) at every roll - four times as often as before. The group itself cannot
# give "nothing", so receptury_super.awk cuts it where it is rolled: a mob's "Type drop" row s50902 at a quarter of its
# chance (RedLas_WorldBoss 3 x 400 -> 100, two Metins 3 -> 0.75 and 8 -> 2), and in the twelve weighted groups of
# special_item_group.txt holding an s50902 row (boss / mini-boss tiers, LootBox_Dolina / _Gigant, QuestBook_Hard /
# _Expert, WorldBoss1, PustyniaSkrzynia, the giant spider's chest) every other row's weight x4 - the recipe row at a
# quarter without fractions, the rest of the group at its own odds. Receptura Mikstura Madrosci drops as before.
COPY receptury_super.awk /tmp/receptury_super.awk
RUN set -eu; L=/opt/metin2/share/locale/poland; A=/tmp/receptury_super.awk; M="$L/mob_drop_item.txt"; G="$L/special_item_group.txt" \
 && awk -v report="$A.m" -f "$A" "$M" > "$M.new" \
 && awk -v report="$A.g" -f "$A" "$G" > "$G.new" \
 && cat "$A.m" "$A.g" \
 && test "$(tr -d '\r' < "$M" | wc -l)" -eq "$(tr -d '\r' < "$M.new" | wc -l)" \
 && test "$(tr -d '\r' < "$G" | wc -l)" -eq "$(tr -d '\r' < "$G.new" | wc -l)" \
 && test "$(sed -n 's/^drop //p' "$A.m")" = 5 && test "$(sed -n 's/^other //p' "$A.m")" = 0 \
 && test "$(sed -n 's/^weighted //p' "$A.g")" = 12 && test "$(sed -n 's/^other //p' "$A.g")" = 0 \
 && mv "$M.new" "$M" && mv "$G.new" "$G" \
 && test "$(LC_ALL=C grep -c -E '^[[:blank:]]*[0-9]+[[:blank:]]+s50902[[:blank:]]+1[[:blank:]]+(100|0\.75|2)[[:blank:]]' "$M")" -eq 5 \
 && rm -f "$A" "$A.m" "$A.g" \
 && echo "share: s50902 (super receptury) rolled at a quarter - Receptura Mikstura Madrosci as before (MT2009_PLUS_RECEPTURY_SUPER_V1)"

# MT2009_PLUS_EXCHANGE_CHANCE_V1: the NPC exchanges' chances follow the
# world's difficulty - soul stones to Magiczny Pyl, skill books to Pergamin,
# upgrade items to Materialy Rzemieslnicze. The
# package keeps its chances in a table local to item_exchange.lua and reads
# it twice: the window's chance field (item_exchange.open's cmdchat, which the
# client prints as it is) and the roll of each piece (item_exchange.exchange).
# Both reads go through m2_difficulty.exchange_chance (m2_difficulty.lua,
# loaded after the crafting libraries and asked only at run time), so the
# window shows the chance that is rolled; the package's number is what it
# answers when nothing else applies.
RUN set -eu; F=/opt/metin2/share/locale/poland/quest/libs/crafting/item_exchange.lua \
 && LC_ALL=C grep -q 'if number(1,100) <= exchange_data.chance then' "$F" \
 && LC_ALL=C grep -q 'exchange_data.price, exchange_data.chance, vnum))' "$F" \
 && LC_ALL=C sed -i \
      -e 's/^\([[:blank:]]*\)local success_count = 0/\1local m2_exchange_percent = m2_difficulty.exchange_chance(exchange_vnum, exchange_data.chance)\n\1local success_count = 0/' \
      -e 's/if number(1,100) <= exchange_data\.chance then/if number(1,100) <= m2_exchange_percent then/' \
      -e 's/exchange_data\.price, exchange_data\.chance, vnum))/exchange_data.price, m2_difficulty.exchange_chance(vnum, exchange_data.chance), vnum))/' \
      "$F" \
 && test "$(LC_ALL=C grep -c 'm2_difficulty.exchange_chance(' "$F")" = 2 \
 && LC_ALL=C grep -q 'if number(1,100) <= m2_exchange_percent then' "$F" \
 && ! LC_ALL=C grep -q '<= exchange_data.chance' "$F" \
 && LC_ALL=C grep -q 'm2_difficulty.exchange_chance = function' /opt/metin2/share/locale/poland/quest/libs/other/m2_difficulty.lua \
 && echo "share: the NPC exchanges' chances follow the difficulty"

# The monkey curse (port/shareify.py renders this step): the package's
# monkey_curse quest turned anybody 55 minutes into a Monkey Dungeon (35 on
# 108, 25 on 109) into a monkey and warped them out, bots included. Its event
# handlers go; its state table stays for the flags characters already carry.
RUN set -eu; O=/opt/metin2/share/locale/poland/quest/object \
 && n=$(find "$O" -path "$O/state" -prune -o -type f -name 'monkey_curse.*' -print | wc -l) \
 && find "$O" -path "$O/state" -prune -o -type f -name 'monkey_curse.*' -exec rm -f {} + \
 && rm -rf "$O/monkey_curse" \
 && ! find "$O" -path "$O/state" -prune -o -name 'monkey_curse*' -print | grep -q . \
 && echo "share: monkey curse removed ($n handlers)"

# MT2009_PLUS_STACK_CHESTS_COUPONS_V1: the Kupony SM (80014-80018) stack now
# (apply.sh), and the package's itemshop_manage quest cashed one with
# item.remove() - which takes the whole stack: a stack of twenty paid one
# coupon. Its five compiled "use" handlers remove one piece.
RUN set -eu; O=/opt/metin2/share/locale/poland/quest/object; n=0 \
 && for v in 80014 80015 80016 80017 80018; do \
      f="$O/$v/use/itemshop_manage.start"; \
      test -f "$f"; \
      grep -q 'item \. remove ( ) then' "$f" && sed -i 's/item \. remove ( ) then/item . remove ( 1 ) then/' "$f"; \
      grep -q 'item \. remove ( 1 ) then' "$f"; \
      if grep -q 'item \. remove ( ) then' "$f"; then echo "FATAL: $f" >&2; exit 1; fi; \
      n=$((n + 1)); \
    done \
 && echo "share: Kupon SM use takes one piece of a stack ($n handlers)"

# MT2009_PLUS_KINGDOM_WAR_OFF_V1: the Kingdom War (the package's forked_road, the Battle
# Executor's "Wojna Krolestw" and its GM start) is switched off - its maps (114,
# 118-128) are hosted by no core and no client of this world has them, so "Wejdz"
# went nowhere (the owner, 4 October: "Po prostu wylacz ja"). Its handlers go,
# its state table stays; the Executor keeps its other options.
RUN set -eu; O=/opt/metin2/share/locale/poland/quest/object \
 && n=$(find "$O" -path "$O/state" -prune -o -type f -name 'forked_road.*' -print | wc -l) \
 && find "$O" -path "$O/state" -prune -o -type f -name 'forked_road.*' -exec rm -f {} + \
 && ! find "$O" -path "$O/state" -prune -o -type f -name 'forked_road.*' -print | grep -q . \
 && echo "share: Kingdom War switched off ($n handlers)"

# MT2009_PLUS_HORSE30_V1 (Digi Rasta's horse to level 30, quest konie): the stable
# keeper trains the horse for a fee, so the package's training missions -
# pony_levelup (1-10) and horse_levelup (11-20), no longer compiled above - lose
# their stock handlers; their state tables stay for the flags characters already
# carry. The Black Horse's seal (71131-71134) rolls at nothing in the pet box
# (group 10030): the black horse is the level-30 trial's (as his 60_konie).
# MT2009_PLUS_AWAKENING_V1: Broszura Szermierki (70031, Seon-Pyeong's material)
# in Beran-Setaou's box, Zelazne Pudelko (50121 - the dragon of Leze Smoka and
# the Setaou of the Grotto drop it), weight 1 of 101: about 1% a box.
RUN set -eu; L=/opt/metin2/share/locale/poland; O="$L/quest/object"; F="$L/special_item_group.txt" \
 && n=$(find "$O" -path "$O/state" -prune -o -type f \( -name 'horse_levelup.*' -o -name 'pony_levelup.*' \) -print | wc -l) \
 && find "$O" -path "$O/state" -prune -o -type f \( -name 'horse_levelup.*' -o -name 'pony_levelup.*' \) -exec rm -f {} + \
 && ! find "$O" -path "$O/state" -prune -o -type f \( -name 'horse_levelup.*' -o -name 'pony_levelup.*' \) -print | grep -q . \
 && awk '{cr = sub(/\r$/, "")} /^Group/{v=""; last=0} $1=="Vnum"{v=$2} \
      v=="10030" && $1 ~ /^[0-9]+$/ && $2 ~ /^7113[1-4]$/ { $0 = "\t" $1 "\t" $2 "\t" $3 "\t0\t-- Pieczec Czarnego Konia: the level-30 horse trial (MT2009_PLUS_HORSE30_V1)"; z++ } \
      v=="50121" && $1 ~ /^[0-9]+$/ { last = $1 + 0; if ($2 == "70031") have = 1 } \
      v=="50121" && /^}/ && !have { printf "\t%d\t70031\t1\t1\t-- Broszura Szermierki (MT2009_PLUS_AWAKENING_V1)\r\n", last + 1; b++; have = 1 } \
      { printf "%s%s\n", $0, (cr ? "\r" : "") } \
      END { if (z != 4 || b != 1) { print "FATAL: pet box seals " z " (4 expected), brochure lines " b " (1 expected)" > "/dev/stderr"; exit 1 } }' "$F" > "$F.new" \
 && mv "$F.new" "$F" \
 && echo "share: horse training missions removed ($n handlers), black horse seals out of the pet box, Broszura Szermierki in 50121"

# MT2009_PLUS_HORSE40_V3 (the owner, 30 October 2026, poprawki-3.0.6 item 1): no horse bags on Yohara - the stock
# horse_inventory_init (the Stajenny's first row) and horse_inventory (the window's next rows) lose their handlers
# (their state tables stay); the engine opens no bag cell any more (server-patches/konie, CanUseHorseInventory) and
# what was kept there moved to the bag / the storeroom (mariadb/playerbot/juki_usuniecie.sql).
RUN set -eu; O=/opt/metin2/share/locale/poland/quest/object \
 && n=$(find "$O" -path "$O/state" -prune -o -type f \( -name 'horse_inventory.*' -o -name 'horse_inventory_init.*' \) -print | wc -l) \
 && find "$O" -path "$O/state" -prune -o -type f \( -name 'horse_inventory.*' -o -name 'horse_inventory_init.*' \) -exec rm -f {} + \
 && ! find "$O" -path "$O/state" -prune -o -type f \( -name 'horse_inventory.*' -o -name 'horse_inventory_init.*' \) -print | grep -q . \
 && echo "share: horse bags removed ($n handlers)"

# MT2009_PLUS_EASTER_METIN_CAP_V1: the package compiles three generations of
# the Easter event - event_easter, event_easter_2012 and event_easter_2013 -
# and all three answer the same easter_drop/easter_rabbit flags and the same
# kill of an Easter metin (8041-8050): one kill put two or three new metins
# down (_2013 on the killer's map, the other two on a map of the killer's
# kingdom and level), paid out a basket twice and an egg besides, and _2013
# put twelve more on a map at every login or map change while the Bunny was
# on - "Metin na Metinie" on every map (a player, 29 September). event_easter
# is the event the panel switches; the two older ones lose their handlers and
# keep their state tables for the flags characters already carry. The
# engine caps what is left per map (regen.cpp, EasterRegenMaySpawn).
RUN set -eu; O=/opt/metin2/share/locale/poland/quest/object \
 && n=$(find "$O" -path "$O/state" -prune -o -type f \( -name 'event_easter_2012.*' -o -name 'event_easter_2013.*' \) -print | wc -l) \
 && find "$O" -path "$O/state" -prune -o -type f \( -name 'event_easter_2012.*' -o -name 'event_easter_2013.*' \) -exec rm -f {} + \
 && ! find "$O" -path "$O/state" -prune -o -type f \( -name 'event_easter_2012.*' -o -name 'event_easter_2013.*' \) -print | grep -q . \
 && test -f "$O/8043/kill/event_easter.start" \
 && echo "share: old Easter event copies removed ($n handlers)"

# The Grotto of Exile's entrance (port/shareify.py renders this step): the
# package commented out Koe-Pung in Orc Valley's bottom-left corner (20093,
# cell 282,1455) - the Dragon Order's guard, who lets a character of 75
# through for a Bloodstone (quest/check_trans_ticket.quest, compiled above) -
# with a free warp on the same cell (10077) and Seon-Pyeong beside them
# (20091). Koe-Pung and Seon-Pyeong come back and the warp stays commented,
# as the game has it: "wejscie do groty chyba powinno wymagac jakiegos
# klucza" (Tieru, 26 September; 2.2.20 had opened the warp). The Bloodstone
# is Seon-Hae's daily quest (quest/heavens_cave_keyquest.quest), and the
# package stands Seon-Hae (20095) in Jinno's first village alone: Yongan and
# Joan get him beside their herbalist (20018), on cells measured free and on
# the main ground of their server_attr, far outside the market's ring. A bot
# is moved into the grotto server-side and asks nobody.
RUN set -eu; L=/opt/metin2/share/locale/poland/map; N=$L/map_n_threeway/npc.txt \
 && sed -i -E 's#^(m[[:blank:]]+282[[:blank:]]+1455[[:blank:]].*[[:blank:]]10077[[:space:]]*)$#//\1#; s#^//(m[[:blank:]]+282[[:blank:]]+1455[[:blank:]].*[[:blank:]]20093[[:space:]]*)$#\1#; s#^//(m[[:blank:]]+295[[:blank:]]+1442[[:blank:]].*[[:blank:]]20091[[:space:]]*)$#\1#' "$N" \
 && ! grep -q -E '^m[[:blank:]]+282[[:blank:]]+1455[[:blank:]].*[[:blank:]]10077' "$N" \
 && grep -q -E '^m[[:blank:]]+282[[:blank:]]+1455[[:blank:]].*[[:blank:]]20093' "$N" \
 && grep -q -E '^m[[:blank:]]+295[[:blank:]]+1442[[:blank:]].*[[:blank:]]20091' "$N" \
 && for p in "metin2_map_a1 698 652" "metin2_map_b1 677 585"; do \
      set -- $p; F="$L/$1/npc.txt"; \
      [ -z "$(tail -c 1 "$F")" ] || printf '\n' >> "$F"; \
      grep -q -E '[[:blank:]]20095[[:space:]]*$' "$F" || printf 'm\t%s\t%s\t0\t0\t0\t5\t1m\t100\t1\t20095\n' "$2" "$3" >> "$F"; \
      grep -q -E "^m[[:blank:]]+$2[[:blank:]]+$3[[:blank:]].*[[:blank:]]20095" "$F"; \
    done \
 && echo "share: Grotto of Exile entrance restored in Orc Valley"

# MT2009_PLUS_GROTA2_REGEN_V1: Grota Wygnancow V2 (73, metin2_map_skipia_dungeon_02) had whole rooms without a
# monster (the owner, 3 November 2026): the package's regen.txt is the old dump of the map, 84 of its 722 lines
# ("r ... 2410") commented out (our group_group.txt has no 2410 - the newer dump's skipia1_10 is groups 2417 + 2418,
# the same as 2409). MT2009_PLUS_GROTA2_REGEN_V2 (4 November 2026, "like the global server", with the players' map
# of the global Grota V2): the map's regen.txt is grota2/regen.txt whole (tools/grota2/gen_grota2.py, which also
# reports what was where) - the newer dump of the global server (Owsap's uk set) line for line, its density (the old
# points twice) and its 70 s, 2410 written as 2409; V1's fill where a walkable metre was still more than 40 m of
# walking from every spawn; and the spots of the players' map: the white ones (MK 1/2 and five rooms) and the blue
# PRESUB 1-3 the hardest - Komendant (2414) and Magistrat (2413) groups -, the green SOBA rooms Soldat and
# Bogenschuetze (2411, 2412), the red and orange ones the dump's own groups topped up; every centre on free ground of
# the map's server_attr. grota2/boss.grota2.txt: the dump's four Commanders (2491) we lacked (our 20 min).
COPY grota2/ /tmp/grota2-add/
RUN set -eu; M=/opt/metin2/share/locale/poland/map/metin2_map_skipia_dungeon_02; A=/tmp/grota2-add; L=/opt/metin2/share/locale/poland \
 && grep -q -E '^73[[:blank:]]+metin2_map_skipia_dungeon_02[[:space:]]*$' "$L/map/index" \
 && sed -i '1s/^\xEF\xBB\xBF//; s/\r$//; s/$/\r/' "$A/regen.txt" "$A/boss.grota2.txt" \
 && for v in $(awk '$1 == "r" { print $11 }' "$A/regen.txt" | tr -d '\r' | sort -u); do grep -q -E "^[[:blank:]]*Vnum[[:blank:]]+$v[[:space:]]*\$" "$L/group_group.txt"; done \
 && test "$(grep -c -E '^//r[[:blank:]].*[[:blank:]]2410[[:space:]]*$' "$M/regen.txt")" = 84 \
 && test "$(grep -c -E '^r[[:blank:]]' "$M/regen.txt")" = 638 \
 && n="$(grep -c -E '^r[[:blank:]]' "$A/regen.txt")" && test "$n" -ge 2000 \
 && ! grep -q -E '^[^/].*[[:blank:]]2410[[:space:]]*$' "$A/regen.txt" \
 && test "$(awk '$1 == "r" && NF == 11 && $2 ~ /^[0-9]+$/ && $3 ~ /^[0-9]+$/ && $2 < 1536 && $3 < 1536 && $8 == "70s"' "$A/regen.txt" | wc -l)" = "$n" \
 && cp "$A/regen.txt" "$M/regen.txt" \
 && test "$(grep -c -E '^r[[:blank:]]' "$M/regen.txt")" = "$n" \
 && b0="$(grep -c -E '^m[[:blank:]].*[[:blank:]]2491[[:space:]]*$' "$M/boss.txt")" \
 && { [ -z "$(tail -c 1 "$M/boss.txt")" ] || printf '\r\n' >> "$M/boss.txt"; } \
 && cat "$A/boss.grota2.txt" >> "$M/boss.txt" \
 && test "$(grep -c -E '^m[[:blank:]].*[[:blank:]]2491[[:space:]]*$' "$M/boss.txt")" = "$((b0 + $(grep -c . "$A/boss.grota2.txt")))" \
 && rm -rf "$A" \
 && echo "share: Grota Wygnancow V2 as the global server - $n spawn lines, $(grep -c -E '^m[[:blank:]]' "$M/boss.txt") Commanders"

# The Devil's Catacomb (port/shareify.py renders this step; the quest itself is
# compiled from quest/devilcatacomb_zone.quest above): its Guardian (20367)
# comes back to Hwang Temple, and the Reaper (1093) drops the Reaper's token -
# the Dried Head (30319) the third floor takes one of from every member - as
# r40250's Reaper does. It goes into his existing limit group, flat and certain
# like his casket, because a second limit group for one monster is ignored.
#
# MT2009 Plus (26 September 2026) kept the Guardian commented out while the
# client could not show the map. MT2009_PLUS_CATACOMB_MAP_V1 (1 October 2026,
# "Dodaj mape katakumb i calkowicie uruchom je na serwerze"): client 2.0.36
# brings the map whole - the client finds map 216 by position in atlasinfo
# (metin2_map_devilsCatacomb, 307200 1203200), its 7x7 terrain was already in
# pack maps, and the new pack catacomb_map adds what it lacked (the textureset,
# the environment, the floors' monsters, gates and statues). This server's
# map is 8x8 at the same base, but nothing walkable lies outside the 7x7, so
# the Guardian (20367, cell 548,494 of Hwang Temple) comes back.
RUN set -eu; L=/opt/metin2/share/locale/poland \
 && sed -i -E 's#^//(m[[:blank:]]+548[[:blank:]]+494[[:blank:]].*[[:blank:]]20367[[:space:]]*)$#\1#' "$L/map/metin2_map_milgyo/npc.txt" \
 && grep -q -E '^m[[:blank:]]+548[[:blank:]]+494[[:blank:]].*[[:blank:]]20367' "$L/map/metin2_map_milgyo/npc.txt" \
 && test "$(grep -c -E '^m[[:blank:]].*[[:blank:]]20367[[:space:]]*$' "$L/map/metin2_map_milgyo/npc.txt")" = 1 \
 && sed -i -E '/^Group[[:blank:]]+RiperLimit/,/^}/ s/^([[:blank:]]+1[[:blank:]]+50082[[:blank:]]+1[[:blank:]]+100.*)$/&\n\t2\t30319\t1\t100\r/' "$L/mob_drop_item.txt" \
 && awk '/^Group[[:blank:]]+RiperLimit/{f=1} f&&/^}/{f=0} f&&/[[:blank:]]30319[[:blank:]]/{n++} END{exit n==1?0:1}' "$L/mob_drop_item.txt" \
 && echo "share: Devil's Catacomb opened (the Guardian in Hwang, the Reaper's token)"

# MT2009 Plus (27 September 2026): the guild building materials - Kamien
# Wegielny 90010, Pien 90011, Dykta 90012 - drop ten times as often from the
# ordinary monsters that carry them (Mount Sohan's ice, the Fireland's fire,
# the Hwang Temple's frogs: 0.09-0.4 in mob_drop_item.txt, one piece in
# roughly a thousand to four thousand kills); the bosses' chances (40-300)
# stay. The guilds build with them (playerbot_guild_land.h) and the guild
# materials droppers farm them. Exactly fourteen lines, or the build stops.
RUN set -eu; L=/opt/metin2/share/locale/poland \
 && awk -F '\t' 'BEGIN{OFS="\t"} ($3 ~ /^9001[012]$/ && $5+0 > 0 && $5+0 < 1) {$5 = $5 * 10; n++} {print} END{print n > "/tmp/guildmat.count"}' "$L/mob_drop_item.txt" > /tmp/mob_drop_item.txt \
 && [ "$(cat /tmp/guildmat.count)" = 14 ] \
 && mv /tmp/mob_drop_item.txt "$L/mob_drop_item.txt" && rm -f /tmp/guildmat.count \
 && echo "share: guild building materials x10 from ordinary monsters (14 lines)"

# MT2009_PLUS_DROP90_V1 (2.x): 39002 joins the ring group 10000 - done once by MT2009_PLUS_PD_BONUS_V1 above.

# The costume sets (server-patches/playerqol, MT2009_PLUS_COSTUME_SET_V1): a
# body and a hair of one line give +800 HP and +15 attack value. The game
# reads it from its locale at the first equip; the client's tooltip has the
# same lists in costume_sets.py. MT2009_PLUS_COSTUME_SET_V2 (server-patches/
# zestawy): its "#Z" lines are the sets of the global server (parts, grades,
# bonuses; tools/zestawy/gen_zestawy.py, client root/costume_set_bonus.py) -
# a V1 line none of them claims keeps the old bonus.
COPY costume_sets.txt /opt/metin2/share/locale/poland/costume_sets.txt

# The drop wiki's extras (server-patches/dropwiki, MT2009_PLUS_DROP_WIKI_V2): the drops only quests or the
# engine give (dungeon bosses' chests, the Zodiac General's Zlota Skrzynia), Mnich Milbon's exchanges and the
# dungeons' regen files. The game reads it from its locale at the first wiki question; the rest the wiki
# reads from the tables themselves.
COPY drop_wiki.txt /opt/metin2/share/locale/poland/drop_wiki.txt

# MT2009_PLUS_BOT_I18N_V1: the bots' lines in their readers' languages (playerbot_i18n.h) - chat_<lang>.tsv
# (Polish template -> translation), input_<lang>.tsv (their words -> the bots' Polish), names/ (item and
# monster names by vnum), config.tsv. A language is there when its chat_<lang>.tsv is; tools/playerbot_i18n.
COPY playerbot_i18n /opt/metin2/share/locale/poland/playerbot_i18n

# MT2009_PLUS_SEONPYEONG_GF_V1 (the owner, 17 October): Seon-Pyeong (20091) has no cube recipe any more - a +9
# piece of level 65-66 (and the boots of 47..59) is dragged onto him as on the official server (item_proto
# refine_set 501 / 530 - since MT2009_PLUS_SEONPYEONG_ELITE_V1 refine_global.sql's fixed 39900-39903, tools/refineglobal
# ELITE, constants.cpp IsEliteRefine - server-patches/seonpyeong); NerrVoVy's cube.seon_pyeong.txt is gone (Partyzana+9 ->
# Pogromca Nieb. Smoka, its one recipe the sheet lacks, is an ELITE step now).

# MT2009_PLUS_NS_WIKI_ITEMS_V1 (share): the official PL wiki's item families and materials the world
# did not have (Autor: Digi Rasta, nowy-system 0.33.0; the items are mariadb/playerbot/wiki_nowe.sql):
#  * cube.wiki_nowe.txt - 8 recipes at Seon-Pyeong (20091), after his own above: the six Cyjanitowe
#    weapons from the level-87 +9 one, the Turmalin bracelet and necklace (the 10 Ogniste Buty / Buty
#    Oceanu recipes are cube.buty.txt since MT2009_PLUS_BOOTS_V1);
#  * special_item_group.wiki_nowe.txt - groups 951201 / 951202, the materials the Razador and Nemere
#    chests gave at 70% - since 15 October no chest names them (the owner: Razador / Nemere give only the sheet's
#    table, MT2009_PLUS_CHEST_DROPS_V1), the groups stay defined and unused.
# MT2009_PLUS_NS_WIKI_RECIPES_OFF (the owner, 9 October): the 18 recipes are NOT appended for now - the items
# stay in the world (wiki_nowe.sql) and the client, crafting them comes in a later update; cube.wiki_nowe.txt
# is kept as it is (to switch it on: the four cube.txt lines before this change back in place of "n=0").
# MT2009_PLUS_BOOTS_V1 (the owner, 15 October): the 10 boots recipes left cube.wiki_nowe.txt for cube.buty.txt
# (below, switched on) - 8 recipes (weapons, Turmalin) stay here and off (switching them on: "test $n -eq 8").
COPY cube.wiki_nowe.txt special_item_group.wiki_nowe.txt /tmp/wikinowe-add/
RUN set -eu; L=/opt/metin2/share/locale/poland; C=$L/cube.txt; G=$L/special_item_group.txt; A=/tmp/wikinowe-add \
 && for f in "$A"/*.txt; do sed -i '1s/^\xEF\xBB\xBF//; s/\r$//; s/$/\r/' "$f"; done \
 && ! grep -q 'MT2009_PLUS_NS_WIKI_ITEMS_V1' "$C" \
 && ! grep -q -E '^[[:blank:]]*Vnum[[:blank:]]+95120[12]([^0-9]|$)' "$G" \
 && n=0 \
 && { [ -z "$(tail -c 1 "$G")" ] || printf '\r\n' >> "$G"; } \
 && cat "$A/special_item_group.wiki_nowe.txt" >> "$G" \
 && test "$(grep -c -E '^[[:blank:]]*Vnum[[:blank:]]+95120[12]([^0-9]|$)' "$G")" -eq 2 \
 && test "$(grep -c -E '^[[:blank:]]*[0-9]+[[:blank:]]+s95120[12][[:blank:]]' "$G")" -eq 0 \
 && rm -rf "$A" \
 && echo "share: wiki items - $n recipes at Seon-Pyeong, chest groups 951201 / 951202 (MT2009_PLUS_NS_WIKI_ITEMS_V1)"

# MT2009_PLUS_BOOTS_V1 (share): the boots' crafting of the pl-wiki (the owner, 15 October) - cube.buty.txt: Buty
# Zimorodka / Euforii / Qilina / Kozaki Glorii +0 are dragged onto Seon-Pyeong since MT2009_PLUS_SEONPYEONG_GF_V1
# (not here); Ogniste Buty / Buty Oceanu from Buty Zimorodka / Euforii +5..+9 at Kawuco (20413, 5-50% by plus; MT2009_PLUS_KAWUCO_V1)
# - 10 recipes.
COPY cube.buty.txt /tmp/cube-buty/
RUN set -eu; C=/opt/metin2/share/locale/poland/cube.txt; A=/tmp/cube-buty/cube.buty.txt \
 && ! grep -q 'MT2009_PLUS_BOOTS_V1 (the owner, 15 October 2026)' "$C" \
 && sed -i '1s/^\xEF\xBB\xBF//; s/\r$//; s/$/\r/' "$A" \
 && n=$(grep -c -E '^section' "$A") && b=$(grep -c -E '^section' "$C") \
 && { [ -z "$(tail -c 1 "$C")" ] || printf '\r\n' >> "$C"; } \
 && cat "$A" >> "$C" \
 && test "$n" -eq 10 && test "$(grep -c -E '^section' "$C")" -eq "$((b + n))" \
 && test "$(grep -c -E '^npc[[:blank:]]+20413' "$A")" -eq 10 \
 && rm -rf /tmp/cube-buty \
 && echo "share: boots recipes at Kawuco ($n, MT2009_PLUS_BOOTS_V1 / MT2009_PLUS_KAWUCO_V1)"

# MT2009_PLUS_BELTS_V1 (share): the belt system (Pasy; Autor: Digi Rasta, nowy-system v0.27.0). Mistrz (20082; in
# mob_proto, the client knows him as "gm", no npc.txt line in the package) beside the Blacksmith in M1 and M3 of every
# kingdom, on the cells Digi Rasta measured free - quest/zywioly.quest's Kwiaty Zywiolu and talismans.
# MT2009_PLUS_WIKI_NPC_RECIPES_V1 (the owner, 17 October 2026): the belts are made only where the pl-wiki makes them -
# Yu-Hwan and Jae-Seon Kim (their recipes are the package's cube.txt) - cube.pasy.txt and quest/pasy.quest are gone
# (the bots still make the same nine recipes, playerbot_belts.h). The materials: special_item_group.dungeons.txt (951101 / 951102), energia_alchemik.
RUN set -eu; L=/opt/metin2/share/locale/poland; C=$L/cube.txt \
 && ! grep -q -E '^npc[[:blank:]]+20082[[:space:]]*$' "$C" \
 && for p in "metin2_map_a1 675 560 8" "metin2_map_b1 598 695 4" "metin2_map_c1 394 702 5" \
             "metin2_map_a3 422 613 3" "metin2_map_b3 392 350 2" "metin2_map_c3 487 393 8"; do \
      set -- $p; F="$L/map/$1/npc.txt"; \
      [ -z "$(tail -c 1 "$F")" ] || printf '\n' >> "$F"; \
      grep -q -E '[[:blank:]]20082[[:space:]]*$' "$F" || printf 'm\t%s\t%s\t0\t0\t0\t%s\t1m\t100\t1\t20082\n' "$2" "$3" "$4" >> "$F"; \
      test "$(grep -c -E '[[:blank:]]20082[[:space:]]*$' "$F")" -eq 1 || exit 1; \
    done \
 && echo "share: Mistrz (20082) in M1/M3 of the three kingdoms - no belt recipes (MT2009_PLUS_WIKI_NPC_RECIPES_V1)"

# MT2009_PLUS_OCHAO_V1 (share): Swiatynia Ochao, the Temple of Ochao of the
# "Version 16.2" package - map 209, metin2_map_mt_th_dungeon_01, an open map
# for level 95 and more, hosted on "first" (m2-render-config). Its server
# files as the package ships them, its groups (group.ochao.txt) and drops
# (mob_drop_item.ochao.txt: the package's vnums mapped to this world's), the
# En-Tai Guardian's motions (data/monster/trent_officer) and the entrance NPC,
# Straznik Swiatyni (20426). MT2009_PLUS_OCHAO_GAUTAMA_V1: he stands ONLY on
# Zbocze Gautama (302, metin2_map_dawnmistwood) at cell 1003 700, as on the
# wiki - no longer beside Koe-Pung in Orc Valley (a line an older image left in
# map_n_threeway's npc.txt is taken out); the quest talks only on 302.
# The Guardian's eleven rooms are playerbot_ochao.h; the NPCs' talk is
# quest/temple_of_the_ochao.quest (compiled above).
COPY ochao/ /tmp/ochao-add/
RUN set -eu; L=/opt/metin2/share/locale/poland; A=/tmp/ochao-add \
 && rm -rf "$L/map/metin2_map_mt_th_dungeon_01" && cp -a "$A/map/metin2_map_mt_th_dungeon_01" "$L/map/" \
 && { [ -z "$(tail -c 1 "$L/map/index")" ] || printf '\n' >> "$L/map/index"; } \
 && sed -i -E '/^209[[:blank:]]/d' "$L/map/index" && printf '209 metin2_map_mt_th_dungeon_01\n' >> "$L/map/index" \
 && test "$(grep -c -E '^209[[:blank:]]+metin2_map_mt_th_dungeon_01' "$L/map/index")" -eq 1 \
 && mkdir -p /opt/metin2/share/data/monster && rm -rf /opt/metin2/share/data/monster/trent_officer \
 && cp -a "$A/data/monster/trent_officer" /opt/metin2/share/data/monster/ \
 && ! grep -q -E '^Group[[:blank:]]+OchaoMonsters1[[:space:]]*$' "$L/group.txt" \
 && { [ -z "$(tail -c 1 "$L/group.txt")" ] || printf '\n' >> "$L/group.txt"; } \
 && sed 's/\r$//' "$A/group.ochao.txt" >> "$L/group.txt" \
 && sed -i 's/\r$//; s/$/\r/' "$A/mob_drop_item.ochao.txt" \
 && { [ -z "$(tail -c 1 "$L/mob_drop_item.txt")" ] || printf '\r\n' >> "$L/mob_drop_item.txt"; } \
 && cat "$A/mob_drop_item.ochao.txt" >> "$L/mob_drop_item.txt" \
 && sed -i -E '/[[:blank:]]20426[[:space:]]*$/d' "$L/map/map_n_threeway/npc.txt" "$L/map/metin2_map_dawnmistwood/npc.txt" \
 && ! grep -q -E '[[:blank:]]20426[[:space:]]*$' "$L/map/map_n_threeway/npc.txt" \
 && F="$L/map/metin2_map_dawnmistwood/npc.txt" \
 && { [ -z "$(tail -c 1 "$F")" ] || printf '\n' >> "$F"; } \
 && printf 'm\t1003\t700\t0\t0\t0\t1\t1m\t100\t1\t20426\n' >> "$F" \
 && test "$(grep -c -E '[[:blank:]]20426[[:space:]]*$' "$F")" = 1 \
 && grep -q -E '^m[[:blank:]]+1003[[:blank:]]+700[[:blank:]].*[[:blank:]]20426[[:space:]]*$' "$F" \
 && S="$L/settings.lua" \
 && { LC_ALL=C grep -a -q 'add_goto_info("ochao"' "$S" || printf 'add_goto_info("ochao", 0, 209, 8537, 14164)\r\n' >> "$S"; } \
 && rm -rf "$A" \
 && echo "share: Swiatynia Ochao (map 209, groups, drops, Straznik Swiatyni on Zbocze Gautama, /goto ochao)"

# MT2009_PLUS_DUNGEONS_V1: the Razador and Nemere dungeons (quest/razador_dungeon.quest and
# quest/nemere_dungeon.quest, compiled above; their monsters, keys and names are apply.sh's
# MT2009_PLUS_DUNGEONS_V1). Everything they need from the share goes in here:
#  * metin2_map_n_snow_dungeon_01 (index 352, 4x3 at 512000 153600 - where the client's
#    atlasinfo puts it) with its Setting/Town and a server_attr made by us (every cell
#    walkable: the package never shipped the map, and the client's own attr decides where
#    a player walks);
#  * MT2009_PLUS_DUNGEON_DROP_V1: metin2_map_n_flame_dungeon_01's server_attr (351) made from the
#    GF client's attr.atr (the one the 2.0.28 client walks on) with the package's no-PK cells
#    kept - the package's own blocked the bridges' middles, so a player could not cross them
#    (the owner, 29 September); 352's already is the client's;
#  * the regen files of the two dungeons (data/dungeon/razador_mt: every fourth line of the
#    package's flame_dungeon files, a party of level 55 and not the 100+ the package planned;
#    data/dungeon/nemere_mt: the ice rooms, the package's ice_dungeon groups of groups);
#    MT2009_PLUS_RZNM_OFFICIAL_V2: both now every line of Owsap's flame_dungeon / snow_dungeon
#    (the official density, zone_1..zone_10 for Nemere's ten floors), tools/rznm/gen_rznm_regen.py;
#  * the public copies of 351 and 352 are the lobbies (both maps on game2, see
#    m2-render-config): nothing spawns there but the NPC that opens the instance - the
#    Am-heh statue (20385) on 351, the stone lion (20397) on 352; the package's own
#    npc.txt/regen.txt filled 351 with Razador's hourly group;
#  * the two guards: the Fire Land's (20394) on map 62 at the archive's exit cell (91,916),
#    the Ice Land's (20395) on Mount Sohan (61) at (738,119); both cells measured free;
#  * the Nemere dungeon's drops, mirrored from the package's Razador groups;
#  * MT2009_PLUS_NEMERE_GOLEM_MAG_V1: the Lodowy Golem Mag's (6107, icegolem_magician) run
#    motion - the package's run.msa moves it BACKWARDS (Accumulation y +15.84, every other
#    mob's is negative), so the server's move speed for it was negative and every chase got
#    a move duration of ~4e9 ms (a negative int in a DWORD): its server position no longer
#    matched the one the client drew, the player's hits landed out of range (no HP taken)
#    and the player was pulled across the room. The client's run.msa
#    (gf_nemere, the same run.GR2) has -310.21; the server takes the same number.
# Older packages' shares (a VPS on 2.14.0, 29 September) list no 351 in map/index and
# already carry a Mob 6191 group: the index line is added like 352's, and the awk below
# drops any 6091/6191 group but the chest previews, so only our own groups guard against
# a second append.
COPY dungeons/ /tmp/dungeons-add/
RUN set -eu; L=/opt/metin2/share/locale/poland; A=/tmp/dungeons-add \
 && find "$A" -type f -name '*.txt' -exec sed -i '1s/^\xEF\xBB\xBF//; s/\r$//; s/$/\r/' {} + \
 && cp -a "$A/map/metin2_map_n_snow_dungeon_01" "$L/map/" \
 && cp "$A/map/metin2_map_n_flame_dungeon_01/server_attr" "$L/map/metin2_map_n_flame_dungeon_01/server_attr" \
 && { [ -z "$(tail -c 1 "$L/map/index")" ] || printf '\n' >> "$L/map/index"; } \
 && { grep -q -E '^352[[:blank:]]' "$L/map/index" || printf '352 metin2_map_n_snow_dungeon_01\n' >> "$L/map/index"; } \
 && { grep -q -E '^351[[:blank:]]' "$L/map/index" || printf '351 metin2_map_n_flame_dungeon_01\n' >> "$L/map/index"; } \
 && test "$(grep -c -E '^352[[:blank:]]+metin2_map_n_snow_dungeon_01[[:space:]]*$' "$L/map/index")" = 1 \
 && test "$(grep -c -E '^351[[:blank:]]+metin2_map_n_flame_dungeon_01[[:space:]]*$' "$L/map/index")" = 1 \
 && mkdir -p /opt/metin2/share/data/dungeon \
 && cp -a "$A/data/dungeon/razador_mt" "$A/data/dungeon/nemere_mt" /opt/metin2/share/data/dungeon/ \
 && M=/opt/metin2/share/data/monster/icegolem_magician/run.msa \
 && sed -i -E 's/^(Accumulation[[:blank:]]+)0\.00[[:blank:]]+15\.84[[:blank:]]+0\.00/\10.00\t-310.21\t0.00/' "$M" \
 && grep -q -E '^Accumulation[[:blank:]]+0\.00[[:blank:]]+-310\.21[[:blank:]]+0\.00' "$M" \
 && for f in regen.txt npc.txt boss.txt stone.txt; do : > "$L/map/metin2_map_n_flame_dungeon_01/$f"; done \
 && printf 'm\t348\t578\t0\t0\t0\t0\t60s\t100\t1\t20385\r\n' > "$L/map/metin2_map_n_flame_dungeon_01/npc.txt" \
 && for p in "metin2_map_n_flame_01 95 910 20394" "map_n_snowm_01 742 114 20395"; do \
      set -- $p; F="$L/map/$1/npc.txt"; \
      [ -z "$(tail -c 1 "$F")" ] || printf '\n' >> "$F"; \
      grep -q -E "[[:blank:]]$4[[:space:]]*\$" "$F" || printf 'm\t%s\t%s\t0\t0\t0\t0\t60s\t100\t1\t%s\n' "$2" "$3" "$4" >> "$F"; \
      grep -q -E "^m[[:blank:]]+$2[[:blank:]]+$3[[:blank:]].*[[:blank:]]$4" "$F"; \
    done \
 && ! grep -q -E '^Group[[:blank:]]+MT2009_nemere_' "$L/mob_drop_item.txt" \
 && { [ -z "$(tail -c 1 "$L/mob_drop_item.txt")" ] || printf '\r\n' >> "$L/mob_drop_item.txt"; } \
 && cat "$A/mob_drop_item.dungeons.append.txt" >> "$L/mob_drop_item.txt" \
 && awk '/^Group/{inb=1; blk=""; cut=0; name=$2} \
      inb { blk = blk $0 "\n"; if ($0 ~ /^[[:blank:]]*Mob[[:blank:]]+(6091|6191)([^0-9]|$)/ && name !~ /^MT2009_chest_preview_/) cut = 1; \
            if ($0 ~ /^}/) { inb = 0; if (!cut) printf "%s", blk }; next } \
      { print }' "$L/mob_drop_item.txt" > "$L/mob_drop_item.txt.new" && mv "$L/mob_drop_item.txt.new" "$L/mob_drop_item.txt" \
 && test "$(grep -c -E '^[[:blank:]]*Mob[[:blank:]]+(6091|6191)([^0-9]|$)' "$L/mob_drop_item.txt")" = 2 \
 && test "$(grep -c -E '^Group[[:blank:]]+MT2009_chest_preview_(6091|6191)' "$L/mob_drop_item.txt")" = 2 \
 && test "$(grep -c -E '^Group[[:blank:]]+MT2009_nemere_' "$L/mob_drop_item.txt")" = 9 \
 && test "$(od -An -tx1 -j4 -N4 "$L/map/metin2_map_n_snow_dungeon_01/server_attr" | tr -d ' ')" = 0c000000 \
 && test "$(od -An -tx1 -N8 "$L/map/metin2_map_n_flame_dungeon_01/server_attr" | tr -d ' ')" = 0c0000000c000000 \
 && rm -rf "$A" \
 && echo "share: Razador (351) and Nemere (352) dungeons, their guards and the Nemere drops"

# MT2009_PLUS_BLUE_DRAGON_V1: the Blue Dragon lair - Leze Smoka, map 208 (metin2_map_skipia_dungeon_boss,
# 2x2, on game2), for a party of level 90 (quest/blue_dragon_lair.quest, compiled above; the dragon's
# and the stones' numbers are apply.sh's MT2009_PLUS_BLUE_DRAGON_V1, the engine half - Beran-Setaou
# takes no damage while a stone stands - is server-patches/bluedragon). The Sura's Ghost (30121, the
# package's npc.txt line on map 73 at 266,175) asks game2 for an instance over P2P, like Razador's guard:
#  * data/dungeon/bluedragon_mt/regen.txt - the lair's monsters, Owsap's data/dungeon/dragon_lair.txt
#    without the stones and the dragon's group (the quest places both);
#  * the map's instance_regen.txt (the guild lair's, CDragonLairManager - no active quest starts it)
#    pointed seven lines at group_group 50000, which does not exist: now the lair's own packs with the
#    dragon and his four stones;
#  * the public copy of 208 is the fallback lobby, as Razador's 351: nothing spawns there but the
#    Sura's Ghost (30121) at 246,173, which opens the instance (the package filled it with the lair's
#    monsters and stones, regen.txt emptied);
#  * BlueDragon.lua with Beran-Setaou's weaker skills (dungeons/BlueDragon.lua; settings.lua loads it).
COPY dungeons/ /tmp/bluedragon-add/
RUN set -eu; L=/opt/metin2/share/locale/poland; A=/tmp/bluedragon-add; M="$L/map/metin2_map_skipia_dungeon_boss" \
 && test -d "$M" \
 && grep -q -E '^208[[:blank:]]+metin2_map_skipia_dungeon_boss' "$L/map/index" \
 && sed -i '1s/^\xEF\xBB\xBF//; s/\r$//; s/$/\r/' "$A/data/dungeon/bluedragon_mt/regen.txt" "$A/map/metin2_map_skipia_dungeon_boss/instance_regen.txt" \
 && mkdir -p /opt/metin2/share/data/dungeon && rm -rf /opt/metin2/share/data/dungeon/bluedragon_mt \
 && cp -a "$A/data/dungeon/bluedragon_mt" /opt/metin2/share/data/dungeon/ \
 && cp "$A/map/metin2_map_skipia_dungeon_boss/instance_regen.txt" "$M/instance_regen.txt" \
 && ! grep -q -E '[[:blank:]]50000[[:space:]]*$' "$M/instance_regen.txt" \
 && for f in regen.txt boss.txt stone.txt; do : > "$M/$f"; done \
 && printf 'm\t246\t173\t0\t0\t0\t0\t60s\t100\t1\t30121\r\n' > "$M/npc.txt" \
 && cp "$A/BlueDragon.lua" "$L/BlueDragon.lua" \
 && grep -q 'MT2009_PLUS_BLUE_DRAGON_V1' "$L/BlueDragon.lua" \
 && LC_ALL=C grep -a -q 'BlueDragon.lua' "$L/settings.lua" \
 && rm -rf "$A" \
 && echo "share: Blue Dragon lair (208): its regen, the lobby, instance_regen.txt and BlueDragon.lua"

# MT2009_PLUS_AREZZO_V1 (share): the first three places from the Arezzo files (the owner has the
# rights to them), for players - the bots come later:
#  * Dolina Cyklopow: metin2_map_exp, index 360, 4x4 at 230400 281600, level 45, on game1
#    (m2-render-config), entered by the Teleporter (quest/map_warp.quest, first page);
#  * (MT2009_PLUS_YOHARA_ZAKLETY_V1: Zaczarowany Las - natural_map, 362 - is gone; the En-Tai Guardian's portal in
#    the Temple of Ochao leads to Zaklety Las (353, the "share: Zaklety Las" step) - and 362 is in no index);
#  * Biblioteka Wiedzy: plechito_chamber_of_wisdom, 363, 2x2 at 947200 614400, the level-30 spider
#    dungeon on game2 (quest/biblioteka_wiedzy.quest, rooms in data/dungeon/biblioteka_wiedzy); its
#    guard, Straznik Biblioteki (20430), stands in Orc Valley beside the Temple guard (a cell measured
#    free) and in the public copy of 363 (the fallback lobby, as Razador's 351).
# MT2009_PLUS_AREZZO_MODULE_V1: the guards on the old maps (20430 here, 20423 and 20424 below) are no
# npc.txt lines any more - playerbot_arezzo.h spawns them while the module is on (M2_AREZZO, the panel)
# and removes them while it is off; these steps only make sure no npc.txt line is left behind.
# Arezzo's server_attr (cell for cell the client's attr.atr, checked) and Setting.txt; the regen is
# every other of Arezzo's spawn points with our monsters (the level-45 cyclopes 9601-9605, the
# lemures 9611-9615 spawned only in the removed forest - their rows stay) in groups 36001-36003 (group.arezzo.txt); Arezzo's C++ timed bosses and
# stones are boss.txt / stone.txt (Arges 9606, Polifem 9607, Metin Cienia 8009; Lemur Hrabia 3390,
# the Bodyguard 3391, 8052, 8053); a Teleporter (9012) at each open map's landing point. The drops
# (mob_drop_item.arezzo.txt), the library's chest 30773 (special_item_group.arezzo.txt), the names
# the Teleporter shows (translate.lua) and /goto cyklopy, /goto las for game masters.
COPY arezzo/ /tmp/arezzo-add/
RUN set -eu; L=/opt/metin2/share/locale/poland; A=/tmp/arezzo-add \
 && find "$A" -type f -name '*.txt' -exec sed -i '1s/^\xEF\xBB\xBF//; s/\r$//; s/$/\r/' {} + \
 && for m in metin2_map_exp plechito_chamber_of_wisdom; do rm -rf "$L/map/$m"; cp -a "$A/map/$m" "$L/map/"; done \
 && rm -rf "$L/map/natural_map" \
 && { [ -z "$(tail -c 1 "$L/map/index")" ] || printf '\n' >> "$L/map/index"; } \
 && sed -i -E '/^36[0-6][[:blank:]]/d' "$L/map/index" \
 && printf '360 metin2_map_exp\n363 plechito_chamber_of_wisdom\n' >> "$L/map/index" \
 && test "$(grep -c -E '^(360[[:blank:]]+metin2_map_exp|363[[:blank:]]+plechito_chamber_of_wisdom)[[:space:]]*$' "$L/map/index")" = 2 \
 && ! grep -q -E '^362[[:blank:]]' "$L/map/index" \
 && cp "$A/dungeon_info.txt" "$L/dungeon_info.txt" \
 && test "$(grep -c -E '^dungeon[[:blank:]]' "$L/dungeon_info.txt")" -ge 8 \
    # MT2009_PLUS_DUNGEON_PANEL_V1 (share): the dungeon panel's list, locale/poland/dungeon_info.txt.
 && mkdir -p /opt/metin2/share/data/dungeon && rm -rf /opt/metin2/share/data/dungeon/biblioteka_wiedzy \
 && cp -a "$A/data/dungeon/biblioteka_wiedzy" /opt/metin2/share/data/dungeon/ \
 && ! grep -q -E '^Group[[:blank:]]+MT2009_arezzo_' "$L/group.txt" \
 && { [ -z "$(tail -c 1 "$L/group.txt")" ] || printf '\n' >> "$L/group.txt"; } \
 && sed 's/\r$//' "$A/group.arezzo.txt" >> "$L/group.txt" \
 && test "$(grep -c -E '^[[:blank:]]*Vnum[[:blank:]]+3600[123][[:space:]]*$' "$L/group.txt")" = 3 \
 && ! grep -q -E '^Group[[:blank:]]+MT2009_arezzo_' "$L/mob_drop_item.txt" \
 && { [ -z "$(tail -c 1 "$L/mob_drop_item.txt")" ] || printf '\r\n' >> "$L/mob_drop_item.txt"; } \
 && cat "$A/mob_drop_item.arezzo.txt" >> "$L/mob_drop_item.txt" \
 && test "$(grep -c -E '^Group[[:blank:]]+MT2009_arezzo_' "$L/mob_drop_item.txt")" = 7 \
 && f="$L/special_item_group.txt" \
 && ! grep -q -E '^[[:blank:]]*Vnum[[:blank:]]+(30773|95073[123])([^0-9]|$)' "$f" \
 && { [ -z "$(tail -c 1 "$f")" ] || printf '\r\n' >> "$f"; } \
 && cat "$A/special_item_group.arezzo.txt" >> "$f" \
 && test "$(grep -c -E '^[[:blank:]]*Vnum[[:blank:]]+(30773|95073[123])([^0-9]|$)' "$f")" = 4 \
 && F="$L/map/map_n_threeway/npc.txt" \
 && sed -i -E '/[[:blank:]]20430[[:space:]]*$/d' "$F" \
 && ! grep -q -E '[[:blank:]]20430[[:space:]]*$' "$F" \
 && for f in "$L/translate.lua" "$L/quest/libs/translate/translate.lua"; do \
      [ -f "$f" ] || continue; \
      LC_ALL=C grep -a -q 'map_names\[360\]' "$f" && continue; \
      { [ -z "$(tail -c 1 "$f")" ] || printf '\r\n' >> "$f"; }; \
      printf '\r\n-- MT2009_PLUS_AREZZO_V1: the Arezzo places (the Teleporter lists 360)\r\ntranslate.general.map_names[360] = "Dolina Cyklop\363w"\r\ntranslate.general.map_names[363] = "Biblioteka Wiedzy"\r\n' >> "$f"; \
    done \
 && LC_ALL=C grep -a -q 'map_names\[360\]' "$L/quest/libs/translate/translate.lua" \
 && S="$L/settings.lua" \
 && { LC_ALL=C grep -a -q 'add_goto_info("cyklopy"' "$S" || printf 'add_goto_info("cyklopy", 0, 360, 2650, 3051)\r\n' >> "$S"; } \
 && test "$(od -An -tx1 -N8 "$L/map/metin2_map_exp/server_attr" | tr -d ' ')" = 1000000010000000 \
 && test "$(od -An -tx1 -N8 "$L/map/plechito_chamber_of_wisdom/server_attr" | tr -d ' ')" = 0800000008000000 \
 && rm -rf "$A" \
 && echo "share: Arezzo places - Dolina Cyklopow (360), Biblioteka Wiedzy (363)"

# MT2009_PLUS_AREZZO_V1 (share, phases 5-8): the three Arezzo dungeons and the fourth map, players only:
#  * Wzgorze Wukonga - plechito_wukong_dungeon, 364, 2x2 at 844800 537600, level 45, game2
#    (quest/wzgorze_wukonga.quest; its guard Straznik Wzgorza, 20423, in the Hwang Temple at 165,941);
#  * Ruiny Skorpiona - plechito_scorpion_dungeon, 365, 2x2 at 844800 588800, level 65 - harder than Razador
#    (quest/ruiny_skorpiona.quest; Straznik Ruin, 20424, on the Fire Land beside Razador's guard, 101,910);
#  * Starozytna Dzungla - plechito_easter2023_dungeon, 366, 3x3 at 768000 537600, level 95, the hardest
#    (quest/starozytna_dzungla.quest; Straznik Dzungli, 20425, in the Temple of Ochao beside its gate - spawned by
#    playerbot_arezzo.h while the module is on, MT2009_PLUS_YOHARA_ZAKLETY_V1: the Arezzo forest it stood in is gone);
#  * Pustkowie Faraona - metin2_map_pustynia, 361, 4x4 at 230400 384000, level 55, game1, by the Teleporter.
# The dungeons' public copies are the fallback lobbies (their guard only); their rooms are
# data/dungeon/<quest>. The Plechito monsters' motions (share/data/monster/<folder>, the .msa/.msm/motlist
# of the Arezzo share) - the server times attacks and moves by them. Every run.msa must carry its
# Accumulation (the run.gr2 track group's LoopTranslation, read with granny 2.11.8): without it the
# server's move speed is 0, a move's duration 0, and the mob arrives at once while the client still
# runs it there (the Arezzo share shipped the pyramid mobs' and bosses' without it; 8 Oct 2026). The desert's bosses' drops
# (mob_drop_item.arezzo2.txt), the three chests (special_item_group.arezzo2.txt), the Teleporter's names and
# /goto pustkowie for game masters. The groups are in group.arezzo.txt (the step above).
COPY arezzo/ /tmp/arezzo-p58/
RUN set -eu; L=/opt/metin2/share/locale/poland; A=/tmp/arezzo-p58 \
 && find "$A" -type f -name '*.txt' -exec sed -i '1s/^\xEF\xBB\xBF//; s/\r$//; s/$/\r/' {} + \
 && for m in metin2_map_pustynia plechito_wukong_dungeon plechito_scorpion_dungeon plechito_easter2023_dungeon; do rm -rf "$L/map/$m"; cp -a "$A/map/$m" "$L/map/"; done \
 && { [ -z "$(tail -c 1 "$L/map/index")" ] || printf '\n' >> "$L/map/index"; } \
 && sed -i -E '/^36[1456][[:blank:]]/d' "$L/map/index" \
 && printf '361 metin2_map_pustynia\n364 plechito_wukong_dungeon\n365 plechito_scorpion_dungeon\n366 plechito_easter2023_dungeon\n' >> "$L/map/index" \
 && test "$(grep -c -E '^(361[[:blank:]]+metin2_map_pustynia|364[[:blank:]]+plechito_wukong_dungeon|365[[:blank:]]+plechito_scorpion_dungeon|366[[:blank:]]+plechito_easter2023_dungeon)[[:space:]]*$' "$L/map/index")" = 4 \
 && for q in wzgorze_wukonga ruiny_skorpiona starozytna_dzungla; do rm -rf "/opt/metin2/share/data/dungeon/$q"; cp -a "$A/data/dungeon/$q" /opt/metin2/share/data/dungeon/; done \
 && mkdir -p /opt/metin2/share/data/monster \
 && for m in "$A"/data/monster/*; do rm -rf "/opt/metin2/share/data/monster/$(basename "$m")"; cp -a "$m" /opt/metin2/share/data/monster/; done \
 && test -s /opt/metin2/share/data/monster/plechi_wukong_mainboss/motlist.txt \
 && test -s /opt/metin2/share/data/monster/plechi_easter2023_bossmain/motlist.txt \
 && test -z "$(for m in "$A"/data/monster/*/run.msa; do grep -q -E '^Accumulation[[:blank:]]+[-0-9.]+[[:blank:]]+-[0-9]' "$m" || echo "$m"; done)" \
 && ! grep -q -E '^Group[[:blank:]]+MT2009_arezzo_(9675|9681)' "$L/mob_drop_item.txt" \
 && { [ -z "$(tail -c 1 "$L/mob_drop_item.txt")" ] || printf '\r\n' >> "$L/mob_drop_item.txt"; } \
 && cat "$A/mob_drop_item.arezzo2.txt" >> "$L/mob_drop_item.txt" \
 && test "$(grep -c -E '^Group[[:blank:]]+MT2009_arezzo_' "$L/mob_drop_item.txt")" = 9 \
 && f="$L/special_item_group.txt" \
 && ! grep -q -E '^[[:blank:]]*Vnum[[:blank:]]+(3077[456]|9507[456][123])([^0-9]|$)' "$f" \
 && { [ -z "$(tail -c 1 "$f")" ] || printf '\r\n' >> "$f"; } \
 && cat "$A/special_item_group.arezzo2.txt" >> "$f" \
 && test "$(grep -c -E '^[[:blank:]]*Vnum[[:blank:]]+(3077[456]|9507[456][123])([^0-9]|$)' "$f")" = 12 \
 && for p in "metin2_map_milgyo 20423" "metin2_map_n_flame_01 20424"; do \
      set -- $p; F="$L/map/$1/npc.txt"; \
      sed -i -E "/[[:blank:]]$2[[:space:]]*\$/d" "$F"; \
      ! grep -q -E "[[:blank:]]$2[[:space:]]*\$" "$F" || exit 1; \
    done \
 && ! grep -q -E '[[:blank:]]20425[[:space:]]*$' "$L/map/metin2_map_mt_th_dungeon_01/npc.txt" \
 && for f in "$L/translate.lua" "$L/quest/libs/translate/translate.lua"; do \
      [ -f "$f" ] || continue; \
      LC_ALL=C grep -a -q 'map_names\[361\]' "$f" && continue; \
      { [ -z "$(tail -c 1 "$f")" ] || printf '\r\n' >> "$f"; }; \
      printf '\r\n-- MT2009_PLUS_AREZZO_V1 (phases 5-8)\r\ntranslate.general.map_names[361] = "Pustkowie Faraona"\r\ntranslate.general.map_names[364] = "Wzg\363rze Wukonga"\r\ntranslate.general.map_names[365] = "Ruiny Skorpiona"\r\ntranslate.general.map_names[366] = "Staro\277ytna D\277ungla"\r\n' >> "$f"; \
    done \
 && LC_ALL=C grep -a -q 'map_names\[361\]' "$L/quest/libs/translate/translate.lua" \
 && S="$L/settings.lua" \
 && { LC_ALL=C grep -a -q 'add_goto_info("pustkowie"' "$S" || printf 'add_goto_info("pustkowie", 0, 361, 2409, 3940)\r\n' >> "$S"; } \
 && test "$(od -An -tx1 -N8 "$L/map/metin2_map_pustynia/server_attr" | tr -d ' ')" = 1000000010000000 \
 && test "$(od -An -tx1 -N8 "$L/map/plechito_wukong_dungeon/server_attr" | tr -d ' ')" = 0800000008000000 \
 && test "$(od -An -tx1 -N8 "$L/map/plechito_scorpion_dungeon/server_attr" | tr -d ' ')" = 0800000008000000 \
 && test "$(od -An -tx1 -N8 "$L/map/plechito_easter2023_dungeon/server_attr" | tr -d ' ')" = 0c0000000c000000 \
 && rm -rf "$A" \
 && echo "share: Arezzo phases 5-8 - Pustkowie Faraona (361), Wzgorze Wukonga (364), Ruiny Skorpiona (365), Starozytna Dzungla (366)"

# MT2009_PLUS_ATLANTYDA_V1 (share): Ruiny Atlantydy - plechito_summer2022_dungeon, 158, 3x3 at 3814400 2252800,
# the Plechito summer 2022 dungeon "Ruins of Atlantis" at the Grotto of Exile's band (entry 75, solo or a party;
# quest/ruiny_atlantydy.quest; apply.sh has the rows). Its entrance, Mag Atlantydy (9460), stands in Orc Valley
# beside the Grotto's entrance (286,1434; the Grotto's 20091 is at 295,1442, the Temple guard 20426 stood at
# 289,1448 until MT2009_PLUS_OCHAO_GAUTAMA_V1, all on one open ground measured on server_attr). The public copy of 158 is the fallback lobby (its npc.txt:
# the magician at the entry); the instance's two floors are data/dungeon/ruiny_atlantydy (wave1, wave2, hearts).
# The Plechito monsters' motions (share/data/monster/plechi_sum2022_*: the server times attacks by them), the
# stones' one-monster call groups 6408-6412 (group.atlantyda.txt), the ticket's drops from the Grotto's
# commanders and generals (mob_drop_item.atlantyda.txt), Skrzynia Atlantydy (special_item_group.atlantyda.txt),
# the Teleporter's name and /goto atlantyda for game masters.
COPY atlantyda/ /tmp/atlantyda-add/
RUN set -eu; L=/opt/metin2/share/locale/poland; A=/tmp/atlantyda-add \
 && find "$A" -type f -name '*.txt' -exec sed -i '1s/^\xEF\xBB\xBF//; s/\r$//; s/$/\r/' {} + \
 && rm -rf "$L/map/plechito_summer2022_dungeon" && cp -a "$A/map/plechito_summer2022_dungeon" "$L/map/" \
 && { [ -z "$(tail -c 1 "$L/map/index")" ] || printf '\n' >> "$L/map/index"; } \
 && sed -i -E '/^158[[:blank:]]/d' "$L/map/index" \
 && printf '158 plechito_summer2022_dungeon\n' >> "$L/map/index" \
 && test "$(grep -c -E '^158[[:blank:]]+plechito_summer2022_dungeon[[:space:]]*$' "$L/map/index")" = 1 \
 && mkdir -p /opt/metin2/share/data/dungeon /opt/metin2/share/data/monster \
 && rm -rf /opt/metin2/share/data/dungeon/ruiny_atlantydy && cp -a "$A/data/dungeon/ruiny_atlantydy" /opt/metin2/share/data/dungeon/ \
 && for m in "$A"/data/monster/*; do rm -rf "/opt/metin2/share/data/monster/$(basename "$m")"; cp -a "$m" /opt/metin2/share/data/monster/; done \
 && test -s /opt/metin2/share/data/monster/plechi_sum2022_boss3/motlist.txt \
 && test -s /opt/metin2/share/data/dungeon/ruiny_atlantydy/hearts.txt \
 && ! grep -q -E '^Group[[:blank:]]+MT2009_atlantyda_' "$L/group.txt" \
 && ! grep -q -E '^[[:blank:]]*Vnum[[:blank:]]+641[0-2]([^0-9]|$)|^[[:blank:]]*Vnum[[:blank:]]+640[89]([^0-9]|$)' "$L/group.txt" \
 && { [ -z "$(tail -c 1 "$L/group.txt")" ] || printf '\n' >> "$L/group.txt"; } \
 && sed 's/\r$//' "$A/group.atlantyda.txt" >> "$L/group.txt" \
 && test "$(grep -c -E '^Group[[:blank:]]+MT2009_atlantyda_' "$L/group.txt")" = 5 \
 && ! grep -q -E '^Group[[:blank:]]+MT2009_atlantyda_' "$L/mob_drop_item.txt" \
 && { [ -z "$(tail -c 1 "$L/mob_drop_item.txt")" ] || printf '\r\n' >> "$L/mob_drop_item.txt"; } \
 && cat "$A/mob_drop_item.atlantyda.txt" >> "$L/mob_drop_item.txt" \
 && test "$(grep -c -E '^Group[[:blank:]]+MT2009_atlantyda_' "$L/mob_drop_item.txt")" = 5 \
 && f="$L/special_item_group.txt" \
 && ! grep -q -E '^[[:blank:]]*Vnum[[:blank:]]+(30921|95092[1-9])([^0-9]|$)' "$f" \
 && { [ -z "$(tail -c 1 "$f")" ] || printf '\r\n' >> "$f"; } \
 && cat "$A/special_item_group.atlantyda.txt" >> "$f" \
 && test "$(grep -c -E '^[[:blank:]]*Vnum[[:blank:]]+(30921|95092[1-9])([^0-9]|$)' "$f")" = 10 \
 && F="$L/map/map_n_threeway/npc.txt" \
 && { [ -z "$(tail -c 1 "$F")" ] || printf '\n' >> "$F"; } \
 && { grep -q -E '[[:blank:]]9460[[:space:]]*$' "$F" || printf 'm\t286\t1434\t0\t0\t0\t5\t1m\t100\t1\t9460\n' >> "$F"; } \
 && test "$(grep -c -E '[[:blank:]]9460[[:space:]]*$' "$F")" = 1 \
 && for f in "$L/translate.lua" "$L/quest/libs/translate/translate.lua"; do \
      [ -f "$f" ] || continue; \
      LC_ALL=C grep -a -q 'map_names\[158\]' "$f" && continue; \
      { [ -z "$(tail -c 1 "$f")" ] || printf '\r\n' >> "$f"; }; \
      printf '\r\n-- MT2009_PLUS_ATLANTYDA_V1\r\ntranslate.general.map_names[158] = "Ruiny Atlantydy"\r\n' >> "$f"; \
    done \
 && LC_ALL=C grep -a -q 'map_names\[158\]' "$L/quest/libs/translate/translate.lua" \
 && S="$L/settings.lua" \
 && { LC_ALL=C grep -a -q 'add_goto_info("atlantyda"' "$S" || printf 'add_goto_info("atlantyda", 0, 158, 38343, 22769)\r\n' >> "$S"; } \
 && test "$(od -An -tx1 -N8 "$L/map/plechito_summer2022_dungeon/server_attr" | tr -d ' ')" = 0c0000000c000000 \
 && rm -rf "$A" \
 && echo "share: Ruiny Atlantydy (158), Mag Atlantydy in Orc Valley"

# MT2009_PLUS_ZODIAC_V1 (share): Swiatynia Zodiaku (Autor: Digi Rasta, nowy-system 0.35.0, from WLsj24's
# "ZodiacTemple"; server-patches/zodiak/README.md) - metin2_12zi_stage, 358, 6x6 at 307200 1408000 (its private
# copies 3580000-3589999 are the temple's floors), hosted by game1 (bin/m2-render-config). The temple's data
# (data/dungeon/zodiac: the portals of each weekday, the merchant), the monsters' motions (data/monster/12zi_*,
# cz_*: the server times attacks by them), 51 groups (vnums 2608-2937, none of ours), 41 server texts in Polish
# (locale_string.zodiak.txt), the map's name for the quests, /goto zodiac for game masters and Zlota Skrzynia
# Zodiaku's groups (special_item_group.zodiak.txt, MT2009_PLUS_ZODIAC_ITEMS_V1) with the temple's rewards Skarb
# Aureolin / Skarb Aventurin / Gwiezdny Skarb (33026-33028, MT2009_PLUS_CHEST_DROPS_V2).
COPY zodiak/ /tmp/zodiak-add/
RUN set -eu; L=/opt/metin2/share/locale/poland; A=/tmp/zodiak-add \
 && find "$A" -type f -name '*.txt' -exec sed -i '1s/^\xEF\xBB\xBF//; s/\r$//; s/$/\r/' {} + \
 && rm -rf "$L/map/metin2_12zi_stage" && cp -a "$A/map/metin2_12zi_stage" "$L/map/" \
 && { [ -z "$(tail -c 1 "$L/map/index")" ] || printf '\n' >> "$L/map/index"; } \
 && sed -i -E '/^358[[:blank:]]/d' "$L/map/index" \
 && printf '358 metin2_12zi_stage\n' >> "$L/map/index" \
 && test "$(grep -c -E '^358[[:blank:]]+metin2_12zi_stage[[:space:]]*$' "$L/map/index")" = 1 \
 && test -s "$L/map/metin2_12zi_stage/server_attr" \
 && mkdir -p /opt/metin2/share/data/dungeon /opt/metin2/share/data/monster \
 && rm -rf /opt/metin2/share/data/dungeon/zodiac && cp -a "$A/data/dungeon/zodiac" /opt/metin2/share/data/dungeon/ \
 && for m in "$A"/data/monster/*; do rm -rf "/opt/metin2/share/data/monster/$(basename "$m")"; cp -a "$m" /opt/metin2/share/data/monster/; done \
 && test -s /opt/metin2/share/data/monster/12zi_mouse_boss/motlist.txt \
 && ! grep -q -E '^Group[[:blank:]]+Zodiac' "$L/group.txt" \
 && { [ -z "$(tail -c 1 "$L/group.txt")" ] || printf '\n' >> "$L/group.txt"; } \
 && sed 's/\r$//' "$A/group.zodiak.txt" >> "$L/group.txt" \
 && test "$(grep -c -E '^Group[[:blank:]]+Zodiac' "$L/group.txt")" = 51 \
 && ! grep -q -F '"Osiagnieto limit zakupu tego przedmiotu.";' "$L/locale_string.txt" \
 && { [ -z "$(tail -c 1 "$L/locale_string.txt")" ] || printf '\n' >> "$L/locale_string.txt"; } \
 && printf '\n' >> "$L/locale_string.txt" && sed 's/\r$//' "$A/locale_string.zodiak.txt" >> "$L/locale_string.txt" \
 && grep -q -F '"Osiagnieto limit zakupu tego przedmiotu.";' "$L/locale_string.txt" \
 && for f in "$L/translate.lua" "$L/quest/libs/translate/translate.lua"; do \
      [ -f "$f" ] || continue; \
      LC_ALL=C grep -a -q 'map_names\[358\]' "$f" && continue; \
      { [ -z "$(tail -c 1 "$f")" ] || printf '\r\n' >> "$f"; }; \
      printf '\r\n-- MT2009_PLUS_ZODIAC_V1\r\ntranslate.general.map_names[358] = "\214wi\271tynia Zodiaku"\r\n' >> "$f"; \
    done \
 && f="$L/special_item_group.txt" \
 && ! grep -q -E '^[[:blank:]]*Vnum[[:blank:]]+(33033|951311|33026|33027|33028)([^0-9]|$)' "$f" \
 && { [ -z "$(tail -c 1 "$f")" ] || printf '\r\n' >> "$f"; } \
 && cat "$A/special_item_group.zodiak.txt" >> "$f" \
 && test "$(grep -c -E '^[[:blank:]]*Vnum[[:blank:]]+(33033|951311|33026|33027|33028)([^0-9]|$)' "$f")" = 5 \
 && F="$L/mob_drop_item.txt" \
 && ! grep -q -E '^Group[[:blank:]]+MT2009_zodiak_mat' "$F" \
 && { [ -z "$(tail -c 1 "$F")" ] || printf '\r\n' >> "$F"; } \
 && cat "$A/mob_drop_item.zodiak.txt" >> "$F" \
 && test "$(grep -c -E '^Group[[:blank:]]+MT2009_zodiak_mat' "$F")" = 11 \
 && S="$L/settings.lua" \
 && { LC_ALL=C grep -a -q 'add_goto_info("zodiac"' "$S" || printf 'add_goto_info("zodiac", 0, 358, 3332, 14325)\r\n' >> "$S"; } \
 && rm -rf "$A" \
 && echo "share: Swiatynia Zodiaku (358, 51 groups, temple data, motions, texts, /goto zodiac)"
# MT2009_PLUS_SHIP_DEFENSE_V1 (share): Obrona Statku (Hydra; server-patches/shipdefense/README.md, Owsap's
# "defense wave") - metin2_map_defensewave, 367 (Owsap's 358 is our Zodiac temple), 3x3 at 128000 486400, its
# private copies 3670000-3679999 hosted by game1 (bin/m2-render-config). Owsap's server_attr (56 of 2.36 million
# cells differ from the GF client's attr.atr, checked with tools/gf28/srvattr.py), Setting.txt and Town.txt;
# the waves' respawn lines data/dungeon/defense_wave (wave1-4, boss; the one line on a blocked cell, 378,430,
# moved to 379,430), the monsters' motions (data/monster/defensewave_*, metinstone_defensewave: the server
# times attacks and moves by them, every run.msa carries its Accumulation), 18 texts in Polish
# (locale_string.shipdefense.txt), the map's name for the quests and /goto statek for game masters, and the
# rewards (the owner, 13 October 2026): Skarb Hydry's (3965) limit group - 3-6 Skrzynia Hydry and the wiki's
# list (mob_drop_item.shipdefense.txt) - and Skrzynia Hydry's (54705) group, one item an opening, and
# Pakiet Kamieni Duszy's (72058) group, one spirit stone as a Metin's (special_item_group.shipdefense.txt).
# None may exist before (a mob's first limit group wins).
# The port (Owsap's 359, here 368): the step "share: Port Nowego Kontynentu" below (MT2009_PLUS_YOHARA_PORT_V1).
COPY shipdefense/ /tmp/shipdefense-add/
RUN set -eu; L=/opt/metin2/share/locale/poland; A=/tmp/shipdefense-add \
 && find "$A" -type f -name '*.txt' -exec sed -i '1s/^\xEF\xBB\xBF//; s/\r$//; s/$/\r/' {} + \
 && rm -rf "$L/map/metin2_map_defensewave" && cp -a "$A/map/metin2_map_defensewave" "$L/map/" \
 && { [ -z "$(tail -c 1 "$L/map/index")" ] || printf '\n' >> "$L/map/index"; } \
 && sed -i -E '/^367[[:blank:]]/d' "$L/map/index" \
 && printf '367 metin2_map_defensewave\n' >> "$L/map/index" \
 && test "$(grep -c -E '^367[[:blank:]]+metin2_map_defensewave[[:space:]]*$' "$L/map/index")" = 1 \
 && test "$(od -An -tx1 -N8 "$L/map/metin2_map_defensewave/server_attr" | tr -d ' ')" = 0c0000000c000000 \
 && mkdir -p /opt/metin2/share/data/dungeon /opt/metin2/share/data/monster \
 && rm -rf /opt/metin2/share/data/dungeon/defense_wave && cp -a "$A/data/dungeon/defense_wave" /opt/metin2/share/data/dungeon/ \
 && test -s /opt/metin2/share/data/dungeon/defense_wave/wave4.txt \
 && for m in "$A"/data/monster/*; do rm -rf "/opt/metin2/share/data/monster/$(basename "$m")"; cp -a "$m" /opt/metin2/share/data/monster/; done \
 && test -s /opt/metin2/share/data/monster/defensewave_hydra_boss/motlist.txt \
 && test -z "$(for m in "$A"/data/monster/*/run.msa; do grep -q -E '^Accumulation[[:blank:]]+[-0-9.]+[[:blank:]]+-[0-9]' "$m" || echo "$m"; done)" \
 && ! grep -q -F '"Ship defense: the mast has %d%% HP left!";' "$L/locale_string.txt" \
 && { [ -z "$(tail -c 1 "$L/locale_string.txt")" ] || printf '\n' >> "$L/locale_string.txt"; } \
 && printf '\n' >> "$L/locale_string.txt" && sed 's/\r$//' "$A/locale_string.shipdefense.txt" >> "$L/locale_string.txt" \
 && grep -q -F '"Ship defense: the mast has %d%% HP left!";' "$L/locale_string.txt" \
 && f="$L/special_item_group.txt" \
 && ! grep -q -E '^[[:blank:]]*Vnum[[:blank:]]+54705([^0-9]|$)' "$f" \
 && ! grep -q -E '^[[:blank:]]*Vnum[[:blank:]]+72058([^0-9]|$)' "$f" \
 && { [ -z "$(tail -c 1 "$f")" ] || printf '\r\n' >> "$f"; } \
 && cat "$A/special_item_group.shipdefense.txt" >> "$f" \
 && test "$(grep -c -E '^[[:blank:]]*Vnum[[:blank:]]+54705([^0-9]|$)' "$f")" = 1 \
 && test "$(grep -c -E '^[[:blank:]]*Vnum[[:blank:]]+72058([^0-9]|$)' "$f")" = 1 \
 && F="$L/mob_drop_item.txt" \
 && ! grep -q -i -E '^[[:blank:]]*mob[[:blank:]]+3965([^0-9]|$)' "$F" \
 && { [ -z "$(tail -c 1 "$F")" ] || printf '\r\n' >> "$F"; } \
 && cat "$A/mob_drop_item.shipdefense.txt" >> "$F" \
 && test "$(grep -c -i -E '^[[:blank:]]*mob[[:blank:]]+3965([^0-9]|$)' "$F")" = 1 \
 && for f in "$L/translate.lua" "$L/quest/libs/translate/translate.lua"; do \
      [ -f "$f" ] || continue; \
      LC_ALL=C grep -a -q 'map_names\[367\]' "$f" && continue; \
      { [ -z "$(tail -c 1 "$f")" ] || printf '\r\n' >> "$f"; }; \
      printf '\r\n-- MT2009_PLUS_SHIP_DEFENSE_V1\r\ntranslate.general.map_names[367] = "Obrona Statku"\r\n' >> "$f"; \
      LC_ALL=C grep -a -q 'map_names\[301\]' "$f" \
        || printf '\r\n-- MT2009_PLUS_YOHARA_MAPS302_V1: the Teleporter lists 301-304 from level 90\r\ntranslate.general.map_names[301] = "Przyl\271dek Smoczego Ognia"\r\ntranslate.general.map_names[302] = "Zbocze Gautama"\r\ntranslate.general.map_names[303] = "Nefrytowa Zatoka"\r\ntranslate.general.map_names[304] = "Gromiste G\363ry"\r\n' >> "$f"; \
    done \
 && S="$L/settings.lua" \
 && { LC_ALL=C grep -a -q 'add_goto_info("statek"' "$S" || printf 'add_goto_info("statek", 0, 367, 1667, 5223)\r\n' >> "$S"; } \
 && rm -rf "$A" \
 && echo "share: Obrona Statku (367, waves, motions, texts, /goto statek, Skarb Hydry, Skrzynia Hydry, Pakiet Kamieni Duszy)"
# MT2009_PLUS_CAPE301_V1 (share): Przyladek Smoczego Ognia (301, Metin2_map_CapeDragonHead, game2) - the client gets
# the map from the GF 26.1.11 client (client-patches/client-2.0.30/tools/cape301), so the server's server_attr
# becomes the one that matches that terrain: Owsap's (100% of the block/water/safe-zone cells equal GF's attr.atr,
# tools/gf28/srvattr.py; the base image's matched 99.76% / 100% / 98.51% - an older revision of the map).
# npc.txt: the base image's; Jae-Seon Kim (20383) faces 7 as in the official data. Rybak 9009 stays at 838 1187
# (official). MT2009_PLUS_YOHARA_MAPS302_V1: the two warp portals 10101 (to Nefrytowa Zatoka, 303) and 10103 (to
# Gromiste Gory, 304), commented out while our client had neither map, stand again - the client gets 302-304 in the
# same update (tools/maps302, the step below).
COPY cape301/ /tmp/cape301-add/
RUN set -eu; M=/opt/metin2/share/locale/poland/map/Metin2_map_CapeDragonHead; A=/tmp/cape301-add/map/Metin2_map_CapeDragonHead \
 && test -d "$M" \
 && test "$(od -An -tx1 -N8 "$A/server_attr" | tr -d ' \n')" = 1800000018000000 \
 && cp -f "$A/server_attr" "$M/server_attr" && cp -f "$A/npc.txt" "$M/npc.txt" \
 && test "$(grep -c -E '^m[[:blank:]]+838[[:blank:]]+1187[[:blank:]].*[[:blank:]]9009[[:blank:]]*$' "$M/npc.txt")" = 1 \
 && test "$(grep -c -E '^m[[:blank:]].*[[:blank:]]1010[13][[:blank:]]*$' "$M/npc.txt")" = 2 \
 && rm -rf /tmp/cape301-add \
 && echo "share: Przyladek Smoczego Ognia (301: server_attr of the GF terrain, npc.txt with the 303/304 portals)"
# MT2009_PLUS_TEOWADEN_V1 (share; the owner, 14 October 2026: "dodaj w koncu Teowadena w miejscach z wiki, ze WSZYSTKIMI
# opcjami szarf przeniesionymi z Uriela"): Theowahdan (60003, scholar_beige_M1 - the row is mariadb/playerbot/
# yohara_maps.sql, the model is in the client's Yohara pack, tools/ymaps) where the pl-wiki's "Theowahdan" puts him:
# Yongan 732,480, Joan 681,717, Pyungmoo 413,539 and Przyladek Smoczego Ognia 563,1167 (after the cape's npc.txt above);
# Dongan's 588,761 is in its npc.txt (yohara_maps). Every cell measured walkable on the server_attr, away from the other
# NPCs. Every sash option is his now (quest/acce_costume_uriel.quest: Wytwarzanie, Polacz Szarfy, Przechwyc bonus) and
# the bots' sash errand walks to these cells (playerbot_sash.h GetPlayerBotTheowahdan). One line on each map.
RUN set -eu; L=/opt/metin2/share/locale/poland/map \
 && for p in "metin2_map_a1 732 480 5" "metin2_map_b1 681 717 5" "metin2_map_c1 413 539 5" "Metin2_map_CapeDragonHead 563 1167 5"; do \
      set -- $p; F="$L/$1/npc.txt"; \
      test -f "$F" || { echo "FATAL: Theowahdan: no $F"; exit 1; }; \
      { [ -z "$(tail -c 1 "$F")" ] || printf '\r\n' >> "$F"; }; \
      grep -q -E '^m[[:blank:]].*[[:blank:]]60003[[:space:]]*$' "$F" || printf 'm\t%s\t%s\t0\t0\t0\t%s\t1m\t100\t1\t60003\r\n' "$2" "$3" "$4" >> "$F"; \
      { test "$(grep -c -E "^m[[:blank:]]+$2[[:blank:]]+$3[[:blank:]].*[[:blank:]]60003[[:space:]]*\$" "$F")" = 1 \
        && test "$(grep -c -E '[[:blank:]]60003[[:space:]]*$' "$F")" = 1; } \
        || { echo "FATAL: Theowahdan on $1"; exit 1; }; \
    done \
 && echo "share: Theowahdan (60003) in Yongan, Joan, Pyungmoo and on Przyladek Smoczego Ognia - the sash NPC"
# MT2009_PLUS_HELM100_V1 (share; the owner, 15 October 2026: the level-100 helmets as on the pl-wiki): Straznik Smokow
# Jaharr (20421, old_magic_M2 - the row is mariadb/playerbot/yohara_helm100.sql, the model the client's yhelm100 pack)
# where the official data puts him (Owsap's minimap points = the wikis'): Yongan 555,533, Joan 658,683, Pyungmoo
# 322,734. Every cell and its 5x5 neighbourhood measured walkable on the server_attr (15 October 2026), 18+ cells from
# the other NPCs. He makes the helmets (quest helm100). One line on each map.
RUN set -eu; L=/opt/metin2/share/locale/poland/map \
 && for p in "metin2_map_a1 555 533 5" "metin2_map_b1 658 683 5" "metin2_map_c1 322 734 5"; do \
      set -- $p; F="$L/$1/npc.txt"; \
      test -f "$F" || { echo "FATAL: Jaharr: no $F"; exit 1; }; \
      { [ -z "$(tail -c 1 "$F")" ] || printf '\r\n' >> "$F"; }; \
      grep -q -E '^m[[:blank:]].*[[:blank:]]20421[[:space:]]*$' "$F" || printf 'm\t%s\t%s\t0\t0\t0\t%s\t1m\t100\t1\t20421\r\n' "$2" "$3" "$4" >> "$F"; \
      { test "$(grep -c -E "^m[[:blank:]]+$2[[:blank:]]+$3[[:blank:]].*[[:blank:]]20421[[:space:]]*\$" "$F")" = 1 \
        && test "$(grep -c -E '[[:blank:]]20421[[:space:]]*$' "$F")" = 1; } \
        || { echo "FATAL: Jaharr on $1"; exit 1; }; \
    done \
 && echo "share: Straznik Smokow Jaharr (20421) in Yongan, Joan and Pyungmoo - the level-100 helmets"
# MT2009_PLUS_HELM100_CUBE_V1 (share; round 15.10 #3, the owner: "tak jak u innych NPC, np. Mistrz -> Wytwarzanie
# pasow"): Jaharr's helmets are made in his cube window - cube.helm100.txt (tools/yhelm100/gen_yhelm100.py), 40 recipes
# (4 helmets x +5..+9 x Smokow / Dragona; the window shows 8 rows), the Dragona ones with "fail_keep" (the helmet stays
# on a failure; server-patches/yhelm100). Quest helm100 opens the window.
COPY cube.helm100.txt /tmp/cube-helm100/
RUN set -eu; C=/opt/metin2/share/locale/poland/cube.txt; A=/tmp/cube-helm100/cube.helm100.txt \
 && ! grep -q -E '^npc[[:blank:]]+20421[[:space:]]*$' "$C" \
 && sed -i '1s/^\xEF\xBB\xBF//; s/\r$//; s/$/\r/' "$A" \
 && n=$(grep -c -E '^section' "$A") && b=$(grep -c -E '^section' "$C") \
 && { [ -z "$(tail -c 1 "$C")" ] || printf '\r\n' >> "$C"; } \
 && cat "$A" >> "$C" \
 && test "$n" -eq 40 && test "$(grep -c -E '^section' "$C")" -eq "$((b + n))" \
 && test "$(grep -c -E '^npc[[:blank:]]+20421[[:space:]]*$' "$C")" -eq 40 \
 && test "$(grep -c -E '^fail_keep[[:blank:]]' "$C")" -eq 20 \
 && rm -rf /tmp/cube-helm100 \
 && echo "share: Jaharr's cube window - $n level-100 helmet recipes (MT2009_PLUS_HELM100_CUBE_V1)"
# MT2009_PLUS_SERPENT_HOOD_V1 (share; the owner, 29 October 2026: Wezowy Czepiec as on the pl-wiki): Jaharr's recipe of
# the level-120 helmet - cube.czepiec.txt (tools/czepiec/gen_czepiec.py): 2 Sciegna / 2 Skrzydla Balathora, 7 Zroszonych
# Mlotow, 10 Jadeitow Nocy, 40 Wzorow Wezowych, 200 Gaya, 20 000 000 Yang, 50%. After his helmet recipes (the same
# window, quest helm100); the items are mariadb/playerbot/yohara_czepiec.sql's.
COPY cube.czepiec.txt /tmp/cube-czepiec/
RUN set -eu; C=/opt/metin2/share/locale/poland/cube.txt; A=/tmp/cube-czepiec/cube.czepiec.txt \
 && ! grep -q -E '^reward[[:blank:]]+12880[[:blank:]]' "$C" \
 && sed -i '1s/^\xEF\xBB\xBF//; s/\r$//; s/$/\r/' "$A" \
 && n=$(grep -c -E '^section' "$A") && b=$(grep -c -E '^section' "$C") \
 && { [ -z "$(tail -c 1 "$C")" ] || printf '\r\n' >> "$C"; } \
 && cat "$A" >> "$C" \
 && test "$n" -eq 1 && test "$(grep -c -E '^section' "$C")" -eq "$((b + n))" \
 && test "$(grep -c -E '^reward[[:blank:]]+12880[[:blank:]]' "$C")" -eq 1 \
 && test "$(grep -c -E '^npc[[:blank:]]+20421[[:space:]]*$' "$C")" -eq 41 \
 && rm -rf /tmp/cube-czepiec \
 && echo "share: Jaharr's cube window - Wezowy Czepiec (MT2009_PLUS_SERPENT_HOOD_V1)"

# MT2009_PLUS_YELIXIRS_V1 (share; the owner, 21 October 2026): the elixirs of Yohara (tools/yohara_eliksiry, the pl-wiki's
# "Zielarstwo"): Huahn-So (20022) makes 50830-50841 from 10 herbs (95733-95736, 50737, 50738) and 20 empty bottles
# (50739 power / 50740 resistance), 90% - cube.eliksiry.txt, appended to cube.txt; quest eliksiry_yohary opens his window.
# blend.eliksiry.txt gives each elixir its point (the element powers 178-183, the resistances 75/76/78/133/134/135),
# +8-20% and 1-10 minutes - appended to blend.txt. MT2009_PLUS_MIKSTURY_V1 (the owner, 4 November 2026): 50 000 Yang an
# elixir, and the golden ones 50842-50853 (+1 Zlote Ziolo 50741, 100 000 Yang, always +20% for 10 minutes) - 24 recipes,
# 24 blend rows. blend_item.cpp reads apply_type as a number (str_to_number), so the
# package's dews (Rosy 50821-50826, also Huahn-So's) had apply_type 0 - no effect; their names become the points here
# (CRITICAL_PCT 40, PENETRATE_PCT 41, ATTACK_SPEED 17, RESIST_MAGIC 77, ATT_BONUS 95 = ATT_GRADE_BONUS,
# DEF_BONUS 96 = DEF_GRADE_BONUS - the global data's apply names). Krysztal Energii's ENERGY (51002) is left as it is.
COPY cube.eliksiry.txt blend.eliksiry.txt /tmp/yelixirs/
RUN set -eu; L=/opt/metin2/share/locale/poland; C=$L/cube.txt; B=$L/blend.txt; A=/tmp/yelixirs \
 && ! grep -q 'MT2009_PLUS_YELIXIRS_V1' "$C" \
 && sed -i 's/\r$//; s/$/\r/' "$A/cube.eliksiry.txt" "$A/blend.eliksiry.txt" \
 && n=$(grep -c -E '^section' "$A/cube.eliksiry.txt") && b=$(grep -c -E '^section' "$C") \
 && { [ -z "$(tail -c 1 "$C")" ] || printf '\r\n' >> "$C"; } \
 && cat "$A/cube.eliksiry.txt" >> "$C" \
 && test "$n" -eq 24 && test "$(grep -c -E '^section' "$C")" -eq "$((b + n))" \
 && test "$(grep -c -E '^npc[[:blank:]]+20022[[:space:]]*$' "$C")" -eq 42 \
 && test "$(grep -c -E '^gold[[:blank:]]+(50000|100000)[[:space:]]*$' "$A/cube.eliksiry.txt")" -eq 24 \
 && sed -i -E 's/^([[:blank:]]*apply_type[[:blank:]]+)CRITICAL_PCT\b/\140/; s/^([[:blank:]]*apply_type[[:blank:]]+)PENETRATE_PCT\b/\141/; s/^([[:blank:]]*apply_type[[:blank:]]+)ATTACK_SPEED\b/\117/; s/^([[:blank:]]*apply_type[[:blank:]]+)RESIST_MAGIC\b/\177/; s/^([[:blank:]]*apply_type[[:blank:]]+)ATT_BONUS\b/\195/; s/^([[:blank:]]*apply_type[[:blank:]]+)DEF_BONUS\b/\196/' "$B" \
 && test "$(grep -c -E '^[[:blank:]]*apply_type[[:blank:]]+(40|41|17|77|95|96)[[:space:]]*$' "$B")" -eq 6 \
 && bb=$(grep -c -E '^section' "$B") \
 && { [ -z "$(tail -c 1 "$B")" ] || printf '\r\n' >> "$B"; } \
 && cat "$A/blend.eliksiry.txt" >> "$B" \
 && test "$(grep -c -E '^section' "$B")" -eq "$((bb + 24))" \
 && test "$(grep -c -E '^[[:blank:]]*item_vnum[[:blank:]]+508(3[0-9]|4[0-9]|5[0-3])[[:space:]]*$' "$B")" -eq 24 \
 && rm -rf "$A" \
 && echo "share: Huahn-So's elixirs of Yohara - $n recipes, 24 blend rows, the dews' apply types as points (MT2009_PLUS_YELIXIRS_V1, MT2009_PLUS_MIKSTURY_V1)"

# MT2009_PLUS_ENERGY_V1 (share; the owner, 5 November 2026 - "1:1 jak na Wiki"): Krysztal Energii (51002) as on the pl-wiki
# "System Energii" - the equipment's bonuses +1/3/5/7/10 % for 2 hours of play. Its blend.txt section had apply_type
# "ENERGY" (blend_item.cpp reads a number: 0, no point) and 1800 s; now POINT_ENERGY (128) and 7200 s for every value
# (the values 1 3 5 7 10 and their odds stay the package's). The engine (server-patches/energia, energia.cpp) gives the
# energy to the worn items' bonuses; the crystal is made at the Alchemist (quest energia_krysztal).
RUN set -eu; B=/opt/metin2/share/locale/poland/blend.txt \
 && test "$(grep -c -E '^[[:blank:]]*item_vnum[[:blank:]]+51002[[:space:]]*$' "$B")" = 1 \
 && awk '/^[ \t]*item_vnum[ \t]+51002[ \t\r]*$/ { e = 1 } \
      e && /^[ \t]*apply_type[ \t]/ { $0 = "\tapply_type\t128\r" } \
      e && /^[ \t]*apply_duration[ \t]/ { $0 = "\tapply_duration\t7200\t7200\t7200\t7200\t7200\r" } \
      /^end/ { e = 0 } { print }' "$B" > "$B.energia" \
 && mv "$B.energia" "$B" \
 && test "$(grep -c -E '^section' "$B")" -ge 7 \
 && sed -n '/item_vnum[[:blank:]]*51002/,/^end/p' "$B" | tr -d '\r' | grep -q -x -P '\tapply_type\t128' \
 && sed -n '/item_vnum[[:blank:]]*51002/,/^end/p' "$B" | tr -d '\r' | grep -q -x -P '\tapply_value\t1\t3\t5\t7\t10' \
 && sed -n '/item_vnum[[:blank:]]*51002/,/^end/p' "$B" | tr -d '\r' | grep -q -x -P '\tapply_duration\t7200\t7200\t7200\t7200\t7200' \
 && echo "share: Krysztal Energii (51002) - POINT_ENERGY 128, 2 hours (MT2009_PLUS_ENERGY_V1)"

# MT2009_PLUS_KAWUCO_V1 (share; the owner, 15 October 2026): Kawuco (20413, the boots NPC - mariadb/playerbot/kawuco.sql,
# quest/kawuco.quest, cube.buty.txt) where the pl-wiki's "Kawuco" and Owsap's npc.txt put him: Przyladek Smoczego Ognia
# 662,1224, facing 5 (the cell is free on the cape's server_attr, inside the safe zone). One line.
RUN set -eu; F=/opt/metin2/share/locale/poland/map/Metin2_map_CapeDragonHead/npc.txt \
 && test -f "$F" \
 && { [ -z "$(tail -c 1 "$F")" ] || printf '\r\n' >> "$F"; } \
 && { grep -q -E '^m[[:blank:]].*[[:blank:]]20413[[:space:]]*$' "$F" || printf 'm\t662\t1224\t0\t0\t0\t5\t1m\t100\t1\t20413\r\n' >> "$F"; } \
 && test "$(grep -c -E '^m[[:blank:]]+662[[:blank:]]+1224[[:blank:]].*[[:blank:]]20413[[:space:]]*$' "$F")" = 1 \
 && test "$(grep -c -E '[[:blank:]]20413[[:space:]]*$' "$F")" = 1 \
 && echo "share: Kawuco (20413) on Przyladek Smoczego Ognia 662,1224 - the boots NPC"
# MT2009_PLUS_YOHARA_MAPS302_V1 (share): Zbocze Gautama (302, metin2_map_dawnmistwood), Nefrytowa Zatoka (303,
# metin2_map_BayBlackSand) and Gromiste Gory (304, metin2_map_Mt_Thunder) - the client gets the three maps from the
# GF 26.1.11 client (client-patches/client-2.0.30/tools/maps302), so each server_attr becomes Owsap's, which matches
# that terrain: 100% of the block/water/safe-zone cells equal GF's attr.atr on 303 and 304, 100% block / 95.73% water /
# 100% safe zone on 302 (tools/gf28/srvattr.py; the base image's: 302 99.97/92.72/99.81, 303 99.84/99.93/99.59, 304
# 99.98/100/100). Every NPC, Town.txt point and warp-portal landing (10100-10105, all between 301-304) is on a free
# cell of the new files. The rest of the maps (npc/regen/boss/stone, Setting, Town) stays the base image's.
COPY maps302/ /tmp/maps302-add/
RUN set -eu; L=/opt/metin2/share/locale/poland/map; A=/tmp/maps302-add/map \
 && for p in "metin2_map_dawnmistwood 1c00000010000000 302" "metin2_map_BayBlackSand 0c00000018000000 303" \
             "metin2_map_Mt_Thunder 1000000018000000 304"; do \
      set -- $p; test -d "$L/$1"; \
      grep -q -E "^$3[[:blank:]]+$1[[:space:]]*$" "$L/index"; \
      test "$(od -An -tx1 -N8 "$A/$1/server_attr" | tr -d ' \n')" = "$2"; \
      cp -f "$A/$1/server_attr" "$L/$1/server_attr"; \
    done \
 && rm -rf /tmp/maps302-add \
 && echo "share: Zbocze Gautama / Nefrytowa Zatoka / Gromiste Gory (302-304: server_attr of the GF terrain)"
# MT2009_PLUS_YOHARA_PORT_V1 (share): Port Nowego Kontynentu (368, metin2_map_defensewave_port; Owsap's 359), 3x3 at
# 128000 563200 (next to the ship, 367), hosted by game2 beside Przyladek Smoczego Ognia (bin/m2-render-config). The
# client gets the map from the GF 26.1.11 client (client-patches/client-2.0.30/tools/port368), so server_attr is made
# from GF's attr.atr itself (tools/gf28/srvattr.py: 100% of the cells; Owsap's file blocks 2244 more cells - the
# whole square the NPCs stand in - and flags the whole map as water). Setting.txt and Town.txt (405 480) are Owsap's;
# npc.txt has only the Posag Wojownika (20433, 241 574 as in the official data) - no monsters, no Metins, the set
# blacksmiths later (the owner, 13 October 2026). Reached from level 90: the Hydra's portal after a won defence, the
# Fisherman after one, Pierscien Hydry (70303); the statue sails back to the Fisherman (quests obrona_statku,
# czempion, pierscien_hydry). The map's name for the quests and /goto port for game masters.
COPY yohara_port/ /tmp/yohara-port-add/
RUN set -eu; L=/opt/metin2/share/locale/poland; A=/tmp/yohara-port-add; M=metin2_map_defensewave_port \
 && find "$A" -type f -name '*.txt' -exec sed -i '1s/^\xEF\xBB\xBF//; s/\r$//; s/$/\r/' {} + \
 && rm -rf "$L/map/$M" && cp -a "$A/map/$M" "$L/map/" \
 && test "$(od -An -tx1 -N8 "$L/map/$M/server_attr" | tr -d ' \n')" = 0c0000000c000000 \
 && grep -q -E '^BasePosition[[:blank:]]+128000[[:blank:]]+563200' "$L/map/$M/Setting.txt" \
 && test "$(grep -c -E '^m[[:blank:]]+241[[:blank:]]+574[[:blank:]].*[[:blank:]]20433[[:space:]]*$' "$L/map/$M/npc.txt")" = 1 \
 && { [ -z "$(tail -c 1 "$L/map/index")" ] || printf '\n' >> "$L/map/index"; } \
 && sed -i -E '/^368[[:blank:]]/d' "$L/map/index" \
 && printf '368 %s\n' "$M" >> "$L/map/index" \
 && test "$(grep -c -E "^368[[:blank:]]+$M[[:space:]]*\$" "$L/map/index")" = 1 \
 && for f in "$L/translate.lua" "$L/quest/libs/translate/translate.lua"; do \
      [ -f "$f" ] || continue; \
      LC_ALL=C grep -a -q 'map_names\[368\]' "$f" && continue; \
      { [ -z "$(tail -c 1 "$f")" ] || printf '\r\n' >> "$f"; }; \
      printf '\r\n-- MT2009_PLUS_YOHARA_PORT_V1\r\ntranslate.general.map_names[368] = "Port Nowego Kontynentu"\r\n' >> "$f"; \
    done \
 && S="$L/settings.lua" \
 && { LC_ALL=C grep -a -q 'add_goto_info("port"' "$S" || printf 'add_goto_info("port", 0, 368, 1685, 6112)\r\n' >> "$S"; } \
 && rm -rf "$A" \
 && echo "share: Port Nowego Kontynentu (368: GF terrain's server_attr, the statue, /goto port)"
# MT2009_PLUS_YOHARA_MAPS1_V1 (share): the first maps of Yohara (cache/yohara/plan-mapy-yohary.md, pl-wiki "Opuszczona
# Twierdza", "Dongan") - Dongan (373, metin2_map_eastplain_01, 4x5 at 1049600 435200) and Opuszczona Twierdza (374,
# metin2_map_empirecastle, 2x2 at 512000 486400), Owsap's indexes, hosted by game2 beside the port (bin/m2-render-config).
# The client gets both maps from the GF 26.1.11 client (client-patches/client-2.0.30/tools/ymaps), so server_attr is
# made from GF's attr.atr (tools/gf28/srvattr.py, 100% of the cells; Owsap's blocks 612 / 56 more cells). Setting,
# Town, regen, boss, stone and npc are Owsap's: Twierdza's gate portal is 10144 here (Owsap's 10107 is our Lodowa
# Grota), Dongan's mailbox (30308, no mail here) and portal to Seoganland (10128, not here yet) are left out. Their
# spawn groups (group.yohara_maps.txt 6145-6152, 6194-6201; group_group.yohara_maps.txt 6700-6705, 6711-6714) and
# drops (mob_drop_item.yohara_maps.txt - the wiki's lists, what our items have) are appended; none may exist before.
# MT2009_PLUS_YOHARA_ITEMS1_V1: the drops name the Yohara items of mariadb/playerbot/yohara_items.sql (both files made by
# tools/yohara_items/gen_yitems.py), and the five chests among them get their contents (special_item_group
# .yohara_items.txt: Szkatulka Yohara 50528, Skrzynia Ksiag (9.skill) 50529, Skrzynia Ksiag: Riposta / Dopalacz
# 50323 / 50324, Zdobna Skrz. z Odlamkiem 39068) - appended to special_item_group.txt, none may exist before.
# The monsters' rows: mariadb/playerbot/yohara_maps.sql. Both names are in sungma_table.txt, so both maps become Sung
# Ma maps by their map/index lines (no bot may enter one). The maps' names for the quests, /goto twierdza, /goto dongan.
COPY yohara_maps/ /tmp/yohara-maps-add/
RUN set -eu; L=/opt/metin2/share/locale/poland; A=/tmp/yohara-maps-add \
 && find "$A" -type f -name '*.txt' -exec sed -i '1s/^\xEF\xBB\xBF//; s/\r$//; s/$/\r/' {} + \
 && for p in "373 metin2_map_eastplain_01 1000000014000000 1049600 435200" "374 metin2_map_empirecastle 0800000008000000 512000 486400"; do \
      set -- $p; \
      { rm -rf "$L/map/$2" && cp -a "$A/map/$2" "$L/map/" \
        && test "$(od -An -tx1 -N8 "$L/map/$2/server_attr" | tr -d ' \n')" = "$3" \
        && grep -q -E "^BasePosition[[:blank:]]+$4[[:blank:]]+$5" "$L/map/$2/Setting.txt" \
        && test -s "$L/map/$2/Town.txt" && test -s "$L/map/$2/npc.txt" && test -s "$L/map/$2/regen.txt" \
        && test -s "$L/map/$2/boss.txt" && test -s "$L/map/$2/stone.txt" \
        && { [ -z "$(tail -c 1 "$L/map/index")" ] || printf '\n' >> "$L/map/index"; } \
        && sed -i -E "/^$1[[:blank:]]/d" "$L/map/index" \
        && printf '%s %s\n' "$1" "$2" >> "$L/map/index" \
        && test "$(grep -c -E "^$1[[:blank:]]+$2[[:space:]]*\$" "$L/map/index")" = 1; } \
        || { echo "FATAL: Yohara map $1 $2"; exit 1; }; \
    done \
 && test "$(grep -c -E '^m[[:blank:]].*[[:blank:]]10144[[:space:]]*$' "$L/map/metin2_map_empirecastle/npc.txt")" = 1 \
 && ! grep -q -E '[[:blank:]](10107|10128|30308)[[:space:]]*$' "$L/map/metin2_map_empirecastle/npc.txt" "$L/map/metin2_map_eastplain_01/npc.txt" \
 && f="$L/group.txt" \
 && ! grep -q -E '^[[:blank:]]*Vnum[[:blank:]]+(614[5-9]|615[0-2]|619[4-9]|620[01])[[:space:]]*$' "$f" \
 && { [ -z "$(tail -c 1 "$f")" ] || printf '\n' >> "$f"; } \
 && cat "$A/group.yohara_maps.txt" >> "$f" \
 && test "$(grep -c -E '^[[:blank:]]*Vnum[[:blank:]]+(614[5-9]|615[0-2]|619[4-9]|620[01])[[:space:]]*$' "$f")" = 16 \
 && f="$L/group_group.txt" \
 && ! grep -q -E '^[[:blank:]]*Vnum[[:blank:]]+(670[0-5]|671[1-4])[[:space:]]*$' "$f" \
 && { [ -z "$(tail -c 1 "$f")" ] || printf '\r\n' >> "$f"; } \
 && cat "$A/group_group.yohara_maps.txt" >> "$f" \
 && test "$(grep -c -E '^[[:blank:]]*Vnum[[:blank:]]+(670[0-5]|671[1-4])[[:space:]]*$' "$f")" = 10 \
 && F="$L/mob_drop_item.txt" \
 && ! grep -q -i -E '^[[:blank:]]*mob[[:blank:]]+(66(8[6-9]|9[0-9])|67(0[0-6]|1[0-7])|8067|8625)([^0-9]|$)' "$F" \
 && { [ -z "$(tail -c 1 "$F")" ] || printf '\r\n' >> "$F"; } \
 && cat "$A/mob_drop_item.yohara_maps.txt" >> "$F" \
 && test "$(grep -c -i -E '^[[:blank:]]*mob[[:blank:]]+(66(8[6-9]|9[0-9])|67(0[0-6]|1[0-7])|8067|8625)([^0-9]|$)' "$F")" = 31 \
 && G="$L/special_item_group.txt" \
 && ! grep -q -E '^[[:blank:]]*Vnum[[:blank:]]+(50528|50529|50323|50324|39068)([^0-9]|$)' "$G" \
 && { [ -z "$(tail -c 1 "$G")" ] || printf '\r\n' >> "$G"; } \
 && cat "$A/special_item_group.yohara_items.txt" >> "$G" \
 && test "$(grep -c -E '^[[:blank:]]*Vnum[[:blank:]]+(50528|50529|50323|50324|39068)([^0-9]|$)' "$G")" = 5 \
 && for f in "$L/translate.lua" "$L/quest/libs/translate/translate.lua"; do \
      [ -f "$f" ] || continue; \
      LC_ALL=C grep -a -q 'map_names\[374\]' "$f" && continue; \
      { [ -z "$(tail -c 1 "$f")" ] || printf '\r\n' >> "$f"; }; \
      printf '\r\n-- MT2009_PLUS_YOHARA_MAPS1_V1\r\ntranslate.general.map_names[373] = "Dongan"\r\ntranslate.general.map_names[374] = "Opuszczona Twierdza"\r\n' >> "$f"; \
    done \
 && S="$L/settings.lua" \
 && { LC_ALL=C grep -a -q 'add_goto_info("twierdza"' "$S" || printf 'add_goto_info("twierdza", 0, 374, 5376, 4949)\r\n' >> "$S"; } \
 && { LC_ALL=C grep -a -q 'add_goto_info("dongan"' "$S" || printf 'add_goto_info("dongan", 0, 373, 11024, 5068)\r\n' >> "$S"; } \
 && rm -rf "$A" \
 && echo "share: Yohara - Opuszczona Twierdza (374), Dongan (373): GF terrain's server_attr, Owsap's spawns, groups, drops, the chests' groups"
# MT2009_PLUS_CHAMPION_V1 / MT2009_PLUS_SUNGMA_V1 (share): Poziom Czempiona and the Sung Ma stats (server-patches/czempion/
# README.md). sungma_table.txt - the Sung Ma requirements of the GF 26.1.11 client's 19 Yohara maps by name (the engine
# matches the names against map/index, so none of our maps is touched until a Yohara map comes); sungma_mob_exp.txt -
# the champion experience of 356 monsters (Owsap's SungMaExp), given only on a Sung Ma map. Both made by
# tools/champion/gen_sungma_data.py; "/champion reload" reads them again.
COPY champion/ /tmp/champion-add/
RUN set -eu; L=/opt/metin2/share/locale/poland; A=/tmp/champion-add \
 && for f in sungma_table.txt sungma_mob_exp.txt; do sed 's/\r$//' "$A/$f" > "$L/$f"; done \
 && test "$(grep -c -E '^metin2_map_[a-z0-9_]+([[:blank:]]+[0-9]+){5}$' "$L/sungma_table.txt")" = 19 \
 && test "$(grep -c -E '^[0-9]+[[:blank:]]+[0-9]+$' "$L/sungma_mob_exp.txt")" -gt 300 \
 && rm -rf "$A" \
 && echo "share: Poziom Czempiona (sungma_table.txt, sungma_mob_exp.txt)"
# MT2009_PLUS_YOHARA_SETS_V1 (share): the Yohara gear and the set effects (the owner, 14 October 2026; tools/ysets/
# gen_ysets.py made ysets/cube.ysets.txt): Statua Wezy (20807) crafts the serpent weapons and armours from their
# "(wykon.)" piece and Pyl Wezowy, Statua Wojownika (20433) refines the set shards, the five set blacksmiths
# (20475-20479) put a set on a weapon / armour / helmet of level 75+ at +7 or more (set_value / set_part:
# server-patches/ysets) - appended to cube.txt, none of their recipes may exist before; quest ysets opens the windows.
# The blacksmiths stand in the port beside Statua Wojownika in a row along the wall, as on the pl-wiki picture "Kowale z
# Portu Nowego Kontynentu" (fix 3.0 #14: Owsap's/GF's points 258 568 .. 254 572 are one metre apart - the five models
# stood in one another): the same diagonal, two cells apart (260 566 .. 252 574, all walkable on the port's server_attr).
COPY ysets/ /tmp/ysets-add/
RUN set -eu; L=/opt/metin2/share/locale/poland; C=$L/cube.txt; A=/tmp/ysets-add/cube.ysets.txt \
 && P=$L/map/metin2_map_defensewave_port/npc.txt \
 && ! grep -q -E '^npc[[:blank:]]+(20433|20807|2047[5-9])[[:space:]]*$' "$C" \
 && sed -i 's/\r$//; s/$/\r/' "$A" \
 && { [ -z "$(tail -c 1 "$C")" ] || printf '\r\n' >> "$C"; } \
 && cat "$A" >> "$C" \
 && test "$(grep -c -E '^npc[[:blank:]]+2047[5-9][[:space:]]*$' "$C")" -eq 15 \
 && test "$(grep -c -E '^npc[[:blank:]]+20807[[:space:]]*$' "$C")" -eq 13 \
 && test "$(grep -c -E '^npc[[:blank:]]+20433[[:space:]]*$' "$C")" -eq 15 \
 && { [ -z "$(tail -c 1 "$P")" ] || printf '\r\n' >> "$P"; } \
 && for p in "260 566 20475" "258 568 20476" "256 570 20477" "254 572 20478" "252 574 20479"; do \
      set -- $p; \
      grep -q -E "[[:blank:]]$3[[:space:]]*\$" "$P" || printf 'm\t%s\t%s\t0\t0\t0\t5\t60s\t100\t1\t%s\r\n' "$1" "$2" "$3" >> "$P"; \
      test "$(grep -c -E "[[:blank:]]$3[[:space:]]*\$" "$P")" = 1 || exit 1; \
    done \
 && rm -rf /tmp/ysets-add \
 && echo "share: Yohara sets - 43 cube recipes (Statua Wezy, Statua Wojownika, the set blacksmiths), the blacksmiths in the port"
# MT2009_PLUS_YOHARA_MAPS3_V1 (share): the third batch of Yohara places (the owner, 14 October 2026; cache/yohara/
# decyzje.md, plan-mapy-yohary.md; pl-wiki first, TR wiki for what it lacks) - Zejscie Polnocnego Wiatru (394,
# metin2_map_whitedragoncave_02), Glebie Polnocnego Wiatru (395, _boss; dungeon), 1. poziom Swiatyni Wezy (390,
# metin2_map_snake_temple_01), Swiatynia Wezy (391, _02; dungeon), Tajemnicza Instancja (396, metin2_map_anglar_dungeon_01)
# and Krolestwo Zywiolow (378-381, metin2_map_elemental_01..04 - the wiki's nine areas are the parts of _01-_03, _04 is
# Plaskowyz Sil Natury; Ameria's elemental_04_rework is its own copy, not used), Owsap's indexes, on the Yohara core
# (bin/m2-render-config, MT2009_PLUS_YOHARA_CORE_V1). tools/yohara_maps3/gen_ymaps3_maps.py made the folders:
# server_attr from GF 26.1.11's attr.atr (equal to Owsap's in every cell), Setting/Town Owsap's, npc.txt GF's official
# NPC and portal points (Owsap's for the elemental realm, our portal vnums), regen/boss/stone Owsap's where it has them
# and ours (GF's map_mob_list points, the TR wiki's bosses) for Zejscie and the 1st temple level; the dungeons have
# none - their quests spawn everything. Groups (group.yohara_maps3.txt: Owsap's 6156-6161, 6829-6838, ours 9160-9164,
# 9180-9189), drops (mob_drop_item.yohara_maps3.txt; 6797's Zamarzniety Klucz a "limit" group of its own - one a
# kill, the owner 14 October) and chests (special_item_group.yohara_maps3.txt, made with the
# items of mariadb/playerbot/yohara_items3.sql by tools/yohara_maps3/gen_yitems3.py) are appended; none may exist
# before. The port gets Owsap's elemental portal (3998, 229,585) and Staruszek (20009, 233,581: both teleport to the
# wiki's nine areas, quest yohara_mapy3, MT2009_PLUS_YOHARA_REALM_V2); sungma_table.txt the two dungeons (the wiki's first
# levels: Glebie slaby 60/50/60/65, the temple's 2nd level 35/25/35/40 - one requirement a map name here); the dungeon
# panel its three dungeons (Glebie from 1 person - the owner, 14 October; quest flag ymaps3_glebie_party); /goto
# zejscie, swiatynia, instancja, zywioly, plaskowyz. The monsters' rows: mariadb/playerbot/yohara_maps3.sql. The
# connections into other batches' maps: the late step "Yohara maps 3: links".
COPY yohara_maps3/ /tmp/yohara-maps3-add/
RUN set -eu; L=/opt/metin2/share/locale/poland; A=/tmp/yohara-maps3-add \
 && find "$A" -type f -name '*.txt' -exec sed -i '1s/^\xEF\xBB\xBF//; s/\r$//; s/$/\r/' {} + \
 && for p in "394 metin2_map_whitedragoncave_02 0c0000000c000000 1152000 1203200 map" \
             "395 metin2_map_whitedragoncave_boss 0800000008000000 1228800 1203200 dungeon" \
             "390 metin2_map_snake_temple_01 0c0000000c000000 0 1638400 map" \
             "391 metin2_map_snake_temple_02 0c0000000c000000 76800 1638400 dungeon" \
             "396 metin2_map_anglar_dungeon_01 1800000018000000 153600 1049600 map" \
             "378 metin2_map_elemental_01 1400000014000000 0 921600 map" \
             "379 metin2_map_elemental_02 1400000014000000 128000 921600 map" \
             "380 metin2_map_elemental_03 1400000014000000 256000 921600 map" \
             "381 metin2_map_elemental_04 0400000008000000 384000 921600 map"; do \
      set -- $p; \
      { rm -rf "$L/map/$2" && cp -a "$A/map/$2" "$L/map/" \
        && test "$(od -An -tx1 -N8 "$L/map/$2/server_attr" | tr -d ' \n')" = "$3" \
        && grep -q -E "^BasePosition[[:blank:]]+$4[[:blank:]]+$5" "$L/map/$2/Setting.txt" \
        && test -s "$L/map/$2/Town.txt" \
        && { [ "$6" = dungeon ] || test -s "$L/map/$2/regen.txt"; } \
        && { [ -z "$(tail -c 1 "$L/map/index")" ] || printf '\n' >> "$L/map/index"; } \
        && sed -i -E "/^$1[[:blank:]]/d" "$L/map/index" \
        && printf '%s %s\n' "$1" "$2" >> "$L/map/index" \
        && test "$(grep -c -E "^$1[[:blank:]]+$2[[:space:]]*\$" "$L/map/index")" = 1; } \
        || { echo "FATAL: Yohara map $1 $2"; exit 1; }; \
    done \
 && test "$(grep -c -E '[[:blank:]](10205|10206|10207|10208|10209|10210|10211|10212|10213|10214|10215|10216|10217|10218|10219|10220|10221|10222|10223|10224|10225|10203)[[:space:]]*$' "$L/map/metin2_map_whitedragoncave_02/npc.txt")" = 22 \
 && test "$(grep -c -E '[[:blank:]]10125[[:space:]]*$' "$L/map/metin2_map_elemental_01/npc.txt")" = 1 \
 && ! grep -q -E '[[:blank:]]10109[[:space:]]*$' "$L/map/metin2_map_elemental_01/npc.txt" \
 && GV='(615[6-9]|616[01]|68(29|3[0-8])|916[0-4]|918[0-9])' \
 && f="$L/group.txt" \
 && ! grep -q -E "^[[:blank:]]*Vnum[[:blank:]]+$GV[[:space:]]*\$" "$f" \
 && { [ -z "$(tail -c 1 "$f")" ] || printf '\r\n' >> "$f"; } \
 && cat "$A/group.yohara_maps3.txt" >> "$f" \
 && test "$(grep -c -E "^[[:blank:]]*Vnum[[:blank:]]+$GV[[:space:]]*\$" "$f")" = 31 \
 && MV='(39(8[0-9]|9[0-7])|400[0-6]|67(4[4-9]|5[0-6]|65|9[0-7])|685[0-4]|68(6[0-9]|7[01])|8076|8630|8631|8632|8633)' \
 && F="$L/mob_drop_item.txt" \
 && ! grep -q -i -E "^[[:blank:]]*mob[[:blank:]]+$MV([^0-9]|\$)" "$F" \
 && { [ -z "$(tail -c 1 "$F")" ] || printf '\r\n' >> "$F"; } \
 && cat "$A/mob_drop_item.yohara_maps3.txt" >> "$F" \
 && test "$(grep -c -i -E "^[[:blank:]]*mob[[:blank:]]+$MV([^0-9]|\$)" "$F")" = 56 \
 && SV='(70411|70412|70429|83051|83052|83053)' \
 && G="$L/special_item_group.txt" \
 && ! grep -q -E "^[[:blank:]]*Vnum[[:blank:]]+$SV([^0-9]|\$)" "$G" \
 && { [ -z "$(tail -c 1 "$G")" ] || printf '\r\n' >> "$G"; } \
 && cat "$A/special_item_group.yohara_maps3.txt" >> "$G" \
 && test "$(grep -c -E "^[[:blank:]]*Vnum[[:blank:]]+$SV([^0-9]|\$)" "$G")" = 6 \
 && P="$L/map/metin2_map_defensewave_port/npc.txt" \
 && { grep -q -E '[[:blank:]]3998[[:space:]]*$' "$P" || { { [ -z "$(tail -c 1 "$P")" ] || printf '\r\n' >> "$P"; }; printf 'm\t229\t585\t0\t0\t0\t4\t60s\t100\t1\t3998\r\n' >> "$P"; }; } \
 && test "$(grep -c -E '[[:blank:]]3998[[:space:]]*$' "$P")" = 1 \
 && { grep -q -E '[[:blank:]]20009[[:space:]]*$' "$P" || printf 'm\t233\t581\t0\t0\t0\t4\t60s\t100\t1\t20009\r\n' >> "$P"; } \
 && test "$(grep -c -E '[[:blank:]]20009[[:space:]]*$' "$P")" = 1 \
 && T="$L/sungma_table.txt" \
 && { grep -q '^metin2_map_whitedragoncave_boss[[:blank:]]' "$T" || printf 'metin2_map_whitedragoncave_boss\t60\t50\t60\t65\n' >> "$T"; } \
 && { grep -q '^metin2_map_snake_temple_02[[:blank:]]' "$T" || printf 'metin2_map_snake_temple_02\t35\t25\t35\t40\n' >> "$T"; } \
 && I="$L/dungeon_info.txt" \
 && { LC_ALL=C grep -a -q -E '^dungeon[[:blank:]]+swiatynia[[:blank:]]' "$I" \
      || { { [ -z "$(tail -c 1 "$I")" ] || printf '\n' >> "$I"; }; \
           printf 'dungeon\tglebie_slaby\t395\t1\txy\t394\t11903\t12646\t120\t0\t1\t8\t6790\tymaps3_glebie.entry\t0\t70410\t3\tG\263\352bie_P\363\263nocnego_Wiatru_(s\263aby)\tZej\234cie_P\363\263nocnego_Wiatru\ndrop\tglebie_slaby\t70411\t8\t100\n' >> "$I"; \
           printf 'dungeon\tglebie_silny\t395\t1\txy\t394\t11903\t12646\t120\t0\t1\t8\t6791\tymaps3_glebie.entry\t0\t70410\t3\tG\263\352bie_P\363\263nocnego_Wiatru_(silny)\tZej\234cie_P\363\263nocnego_Wiatru\ndrop\tglebie_silny\t70412\t8\t100\n' >> "$I"; \
           printf 'dungeon\tswiatynia\t391\t1\txy\t390\t404\t16748\t120\t0\t1\t8\t6756\tswiatynia_wezy.entry\t0\t0\t0\t\214wi\271tynia_W\352\277y\t1._poziom_\214wi\271tyni_W\352\277y\ndrop\tswiatynia\t70429\t8\t100\n' >> "$I"; }; } \
 && test "$(LC_ALL=C grep -a -c -E '^dungeon[[:blank:]]+(glebie_slaby|glebie_silny|swiatynia)[[:blank:]]' "$I")" = 3 \
 && for f in "$L/translate.lua" "$L/quest/libs/translate/translate.lua"; do \
      [ -f "$f" ] || continue; \
      LC_ALL=C grep -a -q 'map_names\[394\]' "$f" && continue; \
      { [ -z "$(tail -c 1 "$f")" ] || printf '\r\n' >> "$f"; }; \
      printf '\r\n-- MT2009_PLUS_YOHARA_MAPS3_V1\r\ntranslate.general.map_names[394] = "Zej\234cie P\363\263nocnego Wiatru"\r\ntranslate.general.map_names[395] = "G\263\352bie P\363\263nocnego Wiatru"\r\ntranslate.general.map_names[390] = "1. poziom \214wi\271tyni W\352\277y"\r\ntranslate.general.map_names[391] = "\214wi\271tynia W\352\277y"\r\ntranslate.general.map_names[396] = "Tajemnicza Instancja"\r\ntranslate.general.map_names[378] = "Kr\363lestwo \257ywio\263\363w"\r\ntranslate.general.map_names[379] = "Kr\363lestwo \257ywio\263\363w"\r\ntranslate.general.map_names[380] = "Kr\363lestwo \257ywio\263\363w"\r\ntranslate.general.map_names[381] = "P\263askowy\277 Si\263 Natury"\r\n' >> "$f"; \
    done \
 && S="$L/settings.lua" \
 && { LC_ALL=C grep -a -q 'add_goto_info("zejscie"' "$S" || printf 'add_goto_info("zejscie", 0, 394, 11590, 12182)\r\n' >> "$S"; } \
 && { LC_ALL=C grep -a -q 'add_goto_info("swiatynia"' "$S" || printf 'add_goto_info("swiatynia", 0, 390, 669, 17042)\r\n' >> "$S"; } \
 && { LC_ALL=C grep -a -q 'add_goto_info("instancja"' "$S" || printf 'add_goto_info("instancja", 0, 396, 1609, 10615)\r\n' >> "$S"; } \
 && { LC_ALL=C grep -a -q 'add_goto_info("zywioly"' "$S" || printf 'add_goto_info("zywioly", 0, 378, 149, 9620)\r\n' >> "$S"; } \
 && { LC_ALL=C grep -a -q 'add_goto_info("plaskowyz"' "$S" || printf 'add_goto_info("plaskowyz", 0, 381, 3966, 9526)\r\n' >> "$S"; } \
 && rm -rf "$A" \
 && echo "share: Yohara maps 3 - Zejscie/Glebie Polnocnego Wiatru, Swiatynia Wezy, Tajemnicza Instancja, Krolestwo Zywiolow: maps, groups, drops, chests, the port's portal, Sung Ma, the dungeon panel"
# MT2009_PLUS_YOHARA_DUNG4_V1 (share): Jaskinie Gnolli and Wieza Sung Mahi (the owner, 14 October 2026; cache/yohara/
# decyzje.md; pl-wiki first, TR wiki for what it lacks) - Jaskinie Gnolli 1/2/3 (382-384, metin2_map_maze_dungeon1..3,
# open maps: the official maze of GOTO portals, the bosses every 1/2/3 hours), Wieza Sung Mahi's hall (386,
# metin2_map_smhdungeon_01) and the tower (387, metin2_map_smhdungeon_02 - a dungeon, quest wieza_sung_mahi; its base
# is ours, 998400 614400: GF's is Komnata Wiedzy's), Owsap's indexes, on the Yohara core (bin/m2-render-config).
# tools/yohara_dung4/gen_ydung4_maps.py made the folders (server_attr from GF's attr.atr, GF's NPC/portal points,
# Owsap's spawn points with the wiki's monsters), groups (9230-9244 the caves, 9250-9268 the tower's waves),
# gen_yitems_d4.py the drops and the four chests (items: mariadb/playerbot/yohara_items_d4.sql); none may exist
# before. sungma_table.txt gets the tower (its first floors, 35/25/35/55 - the quest sets each floor's, d.set_sungma)
# and the hall (0/0/0/0: a Sung Ma map - no bot goes there); the tower's monsters give no champion experience (the
# pl-wiki: "Champion-EXP 0" on every one of them - their lines leave sungma_mob_exp.txt); the dungeon panel gets
# gnolle and wieza_smh (MT2009_PLUS_SMH_TOWER_V3: solo, the boss Tower Tyrant 7610); /goto gnolle, wieza. The
# monsters' rows: mariadb/playerbot/yohara_dung4.sql. The way in from
# Seoganland (4019): the late step "Yohara dung4: links".
COPY yohara_dung4/ /tmp/yohara-dung4-add/
RUN set -eu; L=/opt/metin2/share/locale/poland; A=/tmp/yohara-dung4-add \
 && find "$A" -type f -name '*.txt' -exec sed -i '1s/^\xEF\xBB\xBF//; s/\r$//; s/$/\r/' {} + \
 && for p in "382 metin2_map_maze_dungeon1 0c0000000c000000 768000 1203200 map 26" \
             "383 metin2_map_maze_dungeon2 0c0000000c000000 844800 1203200 map 25" \
             "384 metin2_map_maze_dungeon3 0c0000000c000000 921600 1203200 map 25" \
             "386 metin2_map_smhdungeon_01 0400000004000000 921600 614400 hall 3" \
             "387 metin2_map_smhdungeon_02 0800000008000000 998400 614400 dungeon 0"; do \
      set -- $p; \
      { rm -rf "$L/map/$2" && cp -a "$A/map/$2" "$L/map/" \
        && test "$(od -An -tx1 -N8 "$L/map/$2/server_attr" | tr -d ' \n')" = "$3" \
        && grep -q -E "^BasePosition[[:blank:]]+$4[[:blank:]]+$5" "$L/map/$2/Setting.txt" \
        && test -s "$L/map/$2/Town.txt" \
        && { [ "$6" != map ] || test -s "$L/map/$2/regen.txt"; } \
        && { [ "$7" = 0 ] || test "$(grep -c . "$L/map/$2/npc.txt")" = "$7"; } \
        && { [ -z "$(tail -c 1 "$L/map/index")" ] || printf '\n' >> "$L/map/index"; } \
        && sed -i -E "/^$1[[:blank:]]/d" "$L/map/index" \
        && printf '%s %s\n' "$1" "$2" >> "$L/map/index" \
        && test "$(grep -c -E "^$1[[:blank:]]+$2[[:space:]]*\$" "$L/map/index")" = 1; } \
        || { echo "FATAL: Yohara map $1 $2"; exit 1; }; \
    done \
 && GV='(92(3[0-9]|4[0-4]|5[0-9]|6[0-8]))' \
 && f="$L/group.txt" \
 && ! grep -q -E "^[[:blank:]]*Vnum[[:blank:]]+$GV[[:space:]]*\$" "$f" \
 && { [ -z "$(tail -c 1 "$f")" ] || printf '\r\n' >> "$f"; } \
 && cat "$A/group.yohara_dung4.txt" >> "$f" \
 && test "$(grep -c -E "^[[:blank:]]*Vnum[[:blank:]]+$GV[[:space:]]*\$" "$f")" = 34 \
 && MV='(68(0[0-9]|1[0-9]|20))' \
 && F="$L/mob_drop_item.txt" \
 && ! grep -q -i -E "^[[:blank:]]*mob[[:blank:]]+$MV([^0-9]|\$)" "$F" \
 && { [ -z "$(tail -c 1 "$F")" ] || printf '\r\n' >> "$F"; } \
 && cat "$A/mob_drop_item.yohara_dung4.txt" >> "$F" \
 && test "$(grep -c -i -E "^[[:blank:]]*mob[[:blank:]]+$MV([^0-9]|\$)" "$F")" = 21 \
 && SV='(3125[3-6])' \
 && G="$L/special_item_group.txt" \
 && ! grep -q -E "^[[:blank:]]*Vnum[[:blank:]]+$SV([^0-9]|\$)" "$G" \
 && { [ -z "$(tail -c 1 "$G")" ] || printf '\r\n' >> "$G"; } \
 && cat "$A/special_item_group.yohara_dung4.txt" >> "$G" \
 && test "$(grep -c -E "^[[:blank:]]*Vnum[[:blank:]]+$SV([^0-9]|\$)" "$G")" = 4 \
 && T="$L/sungma_table.txt" \
 && { grep -q '^metin2_map_smhdungeon_02[[:blank:]]' "$T" || printf 'metin2_map_smhdungeon_02\t35\t25\t35\t55\n' >> "$T"; } \
 && { grep -q '^metin2_map_smhdungeon_01[[:blank:]]' "$T" || printf 'metin2_map_smhdungeon_01\t0\t0\t0\t0\n' >> "$T"; } \
 && test "$(grep -c -E '^metin2_map_(maze_dungeon[123]|smhdungeon_0[12])[[:blank:]]' "$T")" = 5 \
 && X="$L/sungma_mob_exp.txt" \
 && sed -i -E '/^(75(5[0-9]|[6-9][0-9])|76(0[0-9]|1[0-9]|20))[[:blank:]]/d' "$X" \
 && ! grep -q -E '^(75(5[0-9]|[6-9][0-9])|76(0[0-9]|1[0-9]|20))[[:blank:]]' "$X" \
 && test "$(grep -c -E '^68(0[0-9]|1[0-9]|20)[[:blank:]]' "$X")" = 21 \
 && I="$L/dungeon_info.txt" \
 && { LC_ALL=C grep -a -q -E '^dungeon[[:blank:]]+wieza_smh[[:blank:]]' "$I" \
      || { { [ -z "$(tail -c 1 "$I")" ] || printf '\n' >> "$I"; }; \
           printf 'dungeon\tgnolle\t382\t0\txy\t373\t11486\t5325\t120\t0\t1\t8\t6820\t-\t0\t71095\t1\tJaskinie_Gnolli\tDongan\ndrop\tgnolle\t31256\t1\t100\ndrop\tgnolle\t31255\t3\t100\n' >> "$I"; \
           printf 'dungeon\twieza_smh\t387\t1\txy\t376\t11596\t5811\t120\t0\t1\t1\t7610\t-\t0\t70401\t1\tWie\277a_Sung_Mahi\tSeoganland\n' >> "$I"; }; } \
 && test "$(LC_ALL=C grep -a -c -E '^dungeon[[:blank:]]+(gnolle|wieza_smh)[[:blank:]]' "$I")" = 2 \
 && for f in "$L/translate.lua" "$L/quest/libs/translate/translate.lua"; do \
      [ -f "$f" ] || continue; \
      LC_ALL=C grep -a -q 'map_names\[382\]' "$f" && continue; \
      { [ -z "$(tail -c 1 "$f")" ] || printf '\r\n' >> "$f"; }; \
      printf '\r\n-- MT2009_PLUS_YOHARA_DUNG4_V1\r\ntranslate.general.map_names[382] = "Jaskinie Gnolli (pierwszy poziom)"\r\ntranslate.general.map_names[383] = "Jaskinie Gnolli (drugi poziom)"\r\ntranslate.general.map_names[384] = "Jaskinie Gnolli (trzeci poziom)"\r\ntranslate.general.map_names[386] = "Wie\277a Sung Mahi"\r\ntranslate.general.map_names[387] = "Wie\277a Sung Mahi"\r\n' >> "$f"; \
    done \
 && S="$L/settings.lua" \
 && { LC_ALL=C grep -a -q 'add_goto_info("gnolle"' "$S" || printf 'add_goto_info("gnolle", 0, 382, 7893, 12142)\r\n' >> "$S"; } \
 && { LC_ALL=C grep -a -q 'add_goto_info("wieza"' "$S" || printf 'add_goto_info("wieza", 0, 386, 9338, 6296)\r\n' >> "$S"; } \
 && rm -rf "$A" \
 && echo "share: Yohara - Jaskinie Gnolli (382-384), Wieza Sung Mahi (386, 387): maps, groups, drops, chests, Sung Ma, the dungeon panel"
# MT2009_PLUS_YOHARA_PB_V1 (share): the awakened bosses - Razador (PB) and Nemere (PB) (the owner, 14 October 2026,
# cache/yohara/decyzje.md "14.10 ok. 8:10"; pl-wiki first, Owsap v6.2.6 for the stages and numbers). Twierdza
# Czerwonego Smoka (PB) (369, metin2_map_boss_awaken_flame) and Strażnica Nemere (PB) (370, metin2_map_boss_awaken_snow)
# - dungeons on the Yohara core (bin/m2-render-config), copies of our 351 / 352 terrain at the official bases (the
# client's folders name the parent map, ParentMapName - client-2.0.30/tools/ypb); quests razador_pb / nemere_pb.
# tools/yohara_pb/gen_ypb.py made everything here: the folders (server_attr from GF's attr.atr of the parent = ours
# cell for cell), the rooms' spawn files (data/dungeon/razador_pb, nemere_pb: Owsap's points, the PB groups), groups
# 6101-6112 / 6121-6132 and groups of groups 6101-6103 (Owsap's), the bosses' and stones' drops, the three chests
# (items: mariadb/playerbot/yohara_items_pb.sql; monsters: yohara_pb.sql) - none may exist before. The entrance:
# Statua Iluzji (20470, the daily mission that gives Książka Przebudzenia, the way to Płaskowyż Iluzji) at the pl-wiki's
# cells of Yongan 540,500, Joan 688,748, Pyungmoo 342,800 - every cell measured walkable, away from the villages' NPCs
# (quest przebudzeni_bossowie); Statua Przebudzenia (20471, the dungeons) stands on Płaskowyż Iluzji (397, the step
# below, MT2009_PLUS_YOHARA_ILUZJA_V1), no longer in the villages. The dungeon panel gets razador_pb and nemere_pb
# (the ticket Książka Przebudzenia, party 2-8, level 110; the entrance: the plateau beside Statua Przebudzenia). The
# drops name the plans of the Dark Dragon gear (yohara_items_iluzja.sql).
COPY yohara_pb/ /tmp/yohara-pb-add/
RUN set -eu; L=/opt/metin2/share/locale/poland; A=/tmp/yohara-pb-add \
 && find "$A" -type f -name '*.txt' -exec sed -i '1s/^\xEF\xBB\xBF//; s/\r$//; s/$/\r/' {} + \
 && for p in "369 metin2_map_boss_awaken_flame 0c0000000c000000 153600 1971200" \
             "370 metin2_map_boss_awaken_snow 100000000c000000 230400 1971200"; do \
      set -- $p; \
      { rm -rf "$L/map/$2" && cp -a "$A/map/$2" "$L/map/" \
        && test "$(od -An -tx1 -N8 "$L/map/$2/server_attr" | tr -d ' \n')" = "$3" \
        && grep -q -E "^BasePosition[[:blank:]]+$4[[:blank:]]+$5" "$L/map/$2/Setting.txt" \
        && test -s "$L/map/$2/Town.txt" \
        && { [ -z "$(tail -c 1 "$L/map/index")" ] || printf '\n' >> "$L/map/index"; } \
        && sed -i -E "/^$1[[:blank:]]/d" "$L/map/index" \
        && printf '%s %s\n' "$1" "$2" >> "$L/map/index" \
        && test "$(grep -c -E "^$1[[:blank:]]+$2[[:space:]]*\$" "$L/map/index")" = 1; } \
        || { echo "FATAL: PB map $1 $2"; exit 1; }; \
    done \
 && mkdir -p /opt/metin2/share/data/dungeon && rm -rf /opt/metin2/share/data/dungeon/razador_pb /opt/metin2/share/data/dungeon/nemere_pb \
 && cp -a "$A/data/dungeon/razador_pb" "$A/data/dungeon/nemere_pb" /opt/metin2/share/data/dungeon/ \
 && test "$(ls /opt/metin2/share/data/dungeon/razador_pb | wc -l)" = 7 && test "$(ls /opt/metin2/share/data/dungeon/nemere_pb | wc -l)" = 10 \
 && GV='(61(0[1-9]|1[0-2]|2[1-9]|3[0-2]))' \
 && f="$L/group.txt" \
 && ! grep -q -E "^[[:blank:]]*Vnum[[:blank:]]+$GV[[:space:]]*\$" "$f" \
 && { [ -z "$(tail -c 1 "$f")" ] || printf '\r\n' >> "$f"; } \
 && cat "$A/group.yohara_pb.txt" >> "$f" \
 && test "$(grep -c -E "^[[:blank:]]*Vnum[[:blank:]]+$GV[[:space:]]*\$" "$f")" = 24 \
 && GG='(610[1-3])' \
 && f="$L/group_group.txt" \
 && ! grep -q -E "^[[:blank:]]*Vnum[[:blank:]]+$GG[[:space:]]*\$" "$f" \
 && { [ -z "$(tail -c 1 "$f")" ] || printf '\r\n' >> "$f"; } \
 && cat "$A/group_group.yohara_pb.txt" >> "$f" \
 && test "$(grep -c -E "^[[:blank:]]*Vnum[[:blank:]]+$GG[[:space:]]*\$" "$f")" = 3 \
 && MV='(4411|4412|8135|20538|4329|4325|4327|4324|4326|4328|4307|4308)' \
 && F="$L/mob_drop_item.txt" \
 && ! grep -q -i -E "^[[:blank:]]*mob[[:blank:]]+$MV([^0-9]|\$)" "$F" \
 && { [ -z "$(tail -c 1 "$F")" ] || printf '\r\n' >> "$F"; } \
 && cat "$A/mob_drop_item.yohara_pb.txt" >> "$F" \
 && test "$(grep -c -i -E "^[[:blank:]]*mob[[:blank:]]+$MV([^0-9]|\$)" "$F")" = 12 \
 && SV='(3114[1-3])' \
 && G="$L/special_item_group.txt" \
 && ! grep -q -E "^[[:blank:]]*Vnum[[:blank:]]+$SV([^0-9]|\$)" "$G" \
 && { [ -z "$(tail -c 1 "$G")" ] || printf '\r\n' >> "$G"; } \
 && cat "$A/special_item_group.yohara_pb.txt" >> "$G" \
 && test "$(grep -c -E "^[[:blank:]]*Vnum[[:blank:]]+$SV([^0-9]|\$)" "$G")" = 3 \
 && for p in "metin2_map_a1 540 500" "metin2_map_b1 688 748" "metin2_map_c1 342 800"; do \
      set -- $p; N="$L/map/$1/npc.txt"; \
      test -f "$N" || { echo "FATAL: PB statues: no $N"; exit 1; }; \
      { [ -z "$(tail -c 1 "$N")" ] || printf '\r\n' >> "$N"; }; \
      grep -q -E '[[:blank:]]20470[[:space:]]*$' "$N" || printf 'm\t%s\t%s\t0\t0\t0\t5\t1m\t100\t1\t20470\r\n' "$2" "$3" >> "$N"; \
      { test "$(grep -c -E "^m[[:blank:]]+$2[[:blank:]]+$3[[:blank:]].*[[:blank:]]20470[[:space:]]*\$" "$N")" = 1 \
        && ! grep -q -E '[[:blank:]]20471[[:space:]]*$' "$N"; } \
        || { echo "FATAL: PB statues on $1"; exit 1; }; \
    done \
 && I="$L/dungeon_info.txt" \
 && { LC_ALL=C grep -a -q -E '^dungeon[[:blank:]]+nemere_pb[[:blank:]]' "$I" \
      || { { [ -z "$(tail -c 1 "$I")" ] || printf '\n' >> "$I"; }; \
           printf 'dungeon\trazador_pb\t369\t1\txy\t397\t3222\t18015\t110\t0\t2\t8\t4411\t-\t0\t31146\t1\tTwierdza_Czerwonego_Smoka_(PB)\tP\263askowy\277_Iluzji\ndrop\trazador_pb\t31141\t4\t100\ndrop\trazador_pb\t31143\t3\t100\n' >> "$I"; \
           printf 'dungeon\tnemere_pb\t370\t1\txy\t397\t3222\t18015\t110\t0\t2\t8\t4412\t-\t0\t31146\t1\tStra\277nica_Nemere_(PB)\tP\263askowy\277_Iluzji\ndrop\tnemere_pb\t31142\t4\t100\ndrop\tnemere_pb\t31143\t3\t100\n' >> "$I"; }; } \
 && test "$(LC_ALL=C grep -a -c -E '^dungeon[[:blank:]]+(razador_pb|nemere_pb)[[:blank:]]' "$I")" = 2 \
 && for f in "$L/translate.lua" "$L/quest/libs/translate/translate.lua"; do \
      [ -f "$f" ] || continue; \
      LC_ALL=C grep -a -q 'map_names\[369\]' "$f" && continue; \
      { [ -z "$(tail -c 1 "$f")" ] || printf '\r\n' >> "$f"; }; \
      printf '\r\n-- MT2009_PLUS_YOHARA_PB_V1\r\ntranslate.general.map_names[369] = "Twierdza Czerwonego Smoka (PB)"\r\ntranslate.general.map_names[370] = "Stra\277nica Nemere (PB)"\r\n' >> "$f"; \
    done \
 && rm -rf "$A" \
 && echo "share: Yohara PB - Twierdza Czerwonego Smoka (PB) (369), Straznica Nemere (PB) (370): maps, rooms, groups, drops, chests, the statues, the dungeon panel"
# MT2009_PLUS_YOHARA_ILUZJA_V1 (share): Płaskowyż Iluzji and the two remaining awakened bosses (the owner, 14 October
# 2026, cache/yohara/decyzje.md; pl-wiki first, the de-wiki for the plans' sources, Owsap v6.2.6 for the stages and
# numbers) - Płaskowyż Iluzji (397, metin2_map_labyrinth, the hub: Statua Przebudzenia 20471, Statua Fabryki Broni
# 20473, Statua Kowala Zbroi 20474, Handlarka Iluzji 20469, Teleporter 9012 at the pl-wiki's cells; no monsters,
# level 110), Grota Wygnańców 2 (PB) (398, metin2_map_boss_awaken_skipia - Beran-Setaou (PB), quest beran_pb) and
# Zaklęty Las (PB) (371, metin2_map_boss_awaken_dawnmist - Jotun Thrym (PB), quest jotun_pb), all on the Yohara core
# (bin/m2-render-config). tools/yohara_iluzja/gen_yiluzja.py made everything here: the folders (server_attr from GF's
# attr.atr; the grotto's with the awakened map's own 000000 sector - Beran's temple open), the rooms' spawn files
# (data/dungeon/beran_pb, jotun_pb: Owsap's points), groups 4281-4292 / 6171-6177 and groups of groups 4281-4287, the
# drops, the two chests, the statues' cube recipes (Statua Iluzji: the awakening stones; Fabryka Broni / Kowal Zbroi:
# the Dark Dragon weapons, the dragon armours and helmets = Owsap's cube) - none may exist before (items:
# mariadb/playerbot/yohara_items_iluzja.sql; monsters, NPCs, the shop: yohara_iluzja.sql). The dungeon panel gets
# beran_pb and jotun_pb (the ticket Książka Przebudzenia, party 2-8, level 110, the entrance on the plateau).
COPY yohara_iluzja/ /tmp/yohara-iluzja-add/
RUN set -eu; L=/opt/metin2/share/locale/poland; A=/tmp/yohara-iluzja-add \
 && find "$A" -type f -name '*.txt' -exec sed -i '1s/^\xEF\xBB\xBF//; s/\r$//; s/$/\r/' {} + \
 && for p in "397 metin2_map_labyrinth 0400000004000000 307200 1792000" \
             "398 metin2_map_boss_awaken_skipia 1800000018000000 0 1971200" \
             "371 metin2_map_boss_awaken_dawnmist 0c00000010000000 332800 1971200"; do \
      set -- $p; \
      { rm -rf "$L/map/$2" && cp -a "$A/map/$2" "$L/map/" \
        && test "$(od -An -tx1 -N8 "$L/map/$2/server_attr" | tr -d ' \n')" = "$3" \
        && grep -q -E "^BasePosition[[:blank:]]+$4[[:blank:]]+$5" "$L/map/$2/Setting.txt" \
        && test -s "$L/map/$2/Town.txt" \
        && { [ -z "$(tail -c 1 "$L/map/index")" ] || printf '\n' >> "$L/map/index"; } \
        && sed -i -E "/^$1[[:blank:]]/d" "$L/map/index" \
        && printf '%s %s\n' "$1" "$2" >> "$L/map/index" \
        && test "$(grep -c -E "^$1[[:blank:]]+$2[[:space:]]*\$" "$L/map/index")" = 1; } \
        || { echo "FATAL: Iluzja map $1 $2"; exit 1; }; \
    done \
 && test "$(grep -c -E '[[:blank:]](20471|20473|20474|20469|9012)[[:space:]]*$' "$L/map/metin2_map_labyrinth/npc.txt")" = 5 \
 && mkdir -p /opt/metin2/share/data/dungeon && rm -rf /opt/metin2/share/data/dungeon/beran_pb /opt/metin2/share/data/dungeon/jotun_pb \
 && cp -a "$A/data/dungeon/beran_pb" "$A/data/dungeon/jotun_pb" /opt/metin2/share/data/dungeon/ \
 && test "$(ls /opt/metin2/share/data/dungeon/beran_pb | wc -l)" = 3 && test "$(ls /opt/metin2/share/data/dungeon/jotun_pb | wc -l)" = 4 \
 && GV='(428[1-9]|429[0-2]|617[1-7])' \
 && f="$L/group.txt" \
 && ! grep -q -E "^[[:blank:]]*Vnum[[:blank:]]+$GV[[:space:]]*\$" "$f" \
 && { [ -z "$(tail -c 1 "$f")" ] || printf '\r\n' >> "$f"; } \
 && cat "$A/group.yohara_iluzja.txt" >> "$f" \
 && test "$(grep -c -E "^[[:blank:]]*Vnum[[:blank:]]+$GV[[:space:]]*\$" "$f")" = 19 \
 && GG='(428[1-7])' \
 && f="$L/group_group.txt" \
 && ! grep -q -E "^[[:blank:]]*Vnum[[:blank:]]+$GG[[:space:]]*\$" "$f" \
 && { [ -z "$(tail -c 1 "$f")" ] || printf '\r\n' >> "$f"; } \
 && cat "$A/group_group.yohara_iluzja.txt" >> "$f" \
 && test "$(grep -c -E "^[[:blank:]]*Vnum[[:blank:]]+$GG[[:space:]]*\$" "$f")" = 7 \
 && MV='(4410|4413|4352|4345|4344|4351|4342|4348|8137|8136|4283|4285|4282)' \
 && F="$L/mob_drop_item.txt" \
 && ! grep -q -i -E "^[[:blank:]]*mob[[:blank:]]+$MV([^0-9]|\$)" "$F" \
 && { [ -z "$(tail -c 1 "$F")" ] || printf '\r\n' >> "$F"; } \
 && cat "$A/mob_drop_item.yohara_iluzja.txt" >> "$F" \
 && test "$(grep -c -i -E "^[[:blank:]]*mob[[:blank:]]+$MV([^0-9]|\$)" "$F")" = 13 \
 && SV='(31139|31140)' \
 && G="$L/special_item_group.txt" \
 && ! grep -q -E "^[[:blank:]]*Vnum[[:blank:]]+$SV([^0-9]|\$)" "$G" \
 && { [ -z "$(tail -c 1 "$G")" ] || printf '\r\n' >> "$G"; } \
 && cat "$A/special_item_group.yohara_iluzja.txt" >> "$G" \
 && test "$(grep -c -E "^[[:blank:]]*Vnum[[:blank:]]+$SV([^0-9]|\$)" "$G")" = 2 \
 && C="$L/cube.txt" \
 && ! grep -q -E '^npc[[:blank:]]+2047[034][[:space:]]*$' "$C" \
 && { [ -z "$(tail -c 1 "$C")" ] || printf '\r\n' >> "$C"; } \
 && cat "$A/cube.yohara_iluzja.txt" >> "$C" \
 && test "$(grep -c -E '^npc[[:blank:]]+2047[034][[:space:]]*$' "$C")" = 79 \
 && I="$L/dungeon_info.txt" \
 && { LC_ALL=C grep -a -q -E '^dungeon[[:blank:]]+jotun_pb[[:blank:]]' "$I" \
      || { { [ -z "$(tail -c 1 "$I")" ] || printf '\n' >> "$I"; }; \
           printf 'dungeon\tberan_pb\t398\t1\txy\t397\t3222\t18015\t110\t0\t2\t8\t4410\t-\t0\t31146\t1\tGrota_Wygna\361c\363w_2_(PB)\tP\263askowy\277_Iluzji\ndrop\tberan_pb\t31139\t2\t100\ndrop\tberan_pb\t31143\t1\t100\n' >> "$I"; \
           printf 'dungeon\tjotun_pb\t371\t1\txy\t397\t3222\t18015\t110\t0\t2\t8\t4413\t-\t0\t31146\t1\tZakl\352ty_Las_(PB)\tP\263askowy\277_Iluzji\ndrop\tjotun_pb\t31140\t4\t100\ndrop\tjotun_pb\t31143\t3\t100\n' >> "$I"; }; } \
 && test "$(LC_ALL=C grep -a -c -E '^dungeon[[:blank:]]+(beran_pb|jotun_pb)[[:blank:]]' "$I")" = 2 \
 && for f in "$L/translate.lua" "$L/quest/libs/translate/translate.lua"; do \
      [ -f "$f" ] || continue; \
      LC_ALL=C grep -a -q 'map_names\[397\]' "$f" && continue; \
      { [ -z "$(tail -c 1 "$f")" ] || printf '\r\n' >> "$f"; }; \
      printf '\r\n-- MT2009_PLUS_YOHARA_ILUZJA_V1\r\ntranslate.general.map_names[397] = "P\263askowy\277 Iluzji"\r\ntranslate.general.map_names[398] = "Grota Wygna\361c\363w 2 (PB)"\r\ntranslate.general.map_names[371] = "Zakl\352ty Las (PB)"\r\n' >> "$f"; \
    done \
 && rm -rf "$A" \
 && echo "share: Plaskowyz Iluzji (397), Grota Wygnancow 2 (PB) (398), Zaklety Las (PB) (371): maps, rooms, groups, drops, chests, the statues' recipes, the dungeon panel"
# MT2009_PLUS_WIKI_NPC_RECIPES_V1 (share; the owner, 17 October 2026: "everything is on the wiki - what from what and at
# whom"): cube.wiki_kto.txt - 10 recipes the pl-wiki / GF give the NPCs and this world lacked: Rybak (9009) the four
# juices, Baek-Go (20018) Charyzma / Inspiracja Eksperta, Jae-Seon Kim (20383) Bransoleta / Naszyjnik z Turmalinu and
# Kamien Czerw. Plomienia, Statua Wezy (20807) Jedwab Wezowy. Rybak / Baek-Go / Yu-Hwan / Huahn-So open their windows by
# quest/mikstury_okno.quest.
# After every other cube step (the share, boots, helmets, the Yohara sets and the Illusion statues): those check that
# their NPCs have no recipe yet, and Statua Wezy (20807) is one of them.
COPY cube.wiki_kto.txt /tmp/cube-kto/
RUN set -eu; C=/opt/metin2/share/locale/poland/cube.txt; A=/tmp/cube-kto/cube.wiki_kto.txt \
 && ! grep -q 'MT2009_PLUS_WIKI_NPC_RECIPES_V1' "$C" \
 && sed -i '1s/^\xEF\xBB\xBF//; s/\r$//; s/$/\r/' "$A" \
 && n=$(grep -c -E '^section' "$A") && b=$(grep -c -E '^section' "$C") \
 && { [ -z "$(tail -c 1 "$C")" ] || printf '\r\n' >> "$C"; } \
 && cat "$A" >> "$C" \
 && test "$n" -eq 10 && test "$(grep -c -E '^section' "$C")" -eq "$((b + n))" \
 && test "$(grep -c -E '^npc[[:blank:]]+9009[[:space:]]*$' "$C")" -eq 4 \
 && rm -rf /tmp/cube-kto \
 && echo "share: wiki NPC recipes ($n, MT2009_PLUS_WIKI_NPC_RECIPES_V1)"

# MT2009_PLUS_WIKI_NPC_AMOUNTS_V1 (share; the owner, 22 October 2026 - the package p-gf-po-3.0.1's cube.txt, the pl-wiki
# "Wytwarzanie Mikstur"): the share's own recipes as the wiki gives them - Woda Dok (50814) x100 from Sok z Pokrzywy +
# Bez at Yu-Hwan (20017) and Huahn-So (20022), not x1 (both recipes: the only "reward 50814 1" lines), and Biala Rosa
# (50826) from 10 Wody Sam-Bo (50818), not 20 (the only "item 50818 20" line). Each line must be there exactly as
# counted, or the build stops.
RUN set -eu; C=/opt/metin2/share/locale/poland/cube.txt; T="$(printf '\t')"; R="$(printf '\r')" \
 && test "$(grep -c "^reward${T}50814${T}1${R}\?\$" "$C")" -eq 2 \
 && test "$(grep -c "^item${T}50818${T}20${R}\?\$" "$C")" -eq 1 \
 && sed -i -E "s/^(reward${T}50814${T})1(${R}?)\$/\1100\2/; s/^(item${T}50818${T})20(${R}?)\$/\110\2/" "$C" \
 && test "$(grep -c "^reward${T}50814${T}100${R}\?\$" "$C")" -eq 2 \
 && test "$(grep -c "^item${T}50818${T}10${R}\?\$" "$C")" -eq 1 \
 && echo "share: Woda Dok x100, Biala Rosa from 10 Wody Sam-Bo (MT2009_PLUS_WIKI_NPC_AMOUNTS_V1)"

# MT2009_PLUS_ARMOR105_V1 (share; the owner, 17 October 2026): cube.zbroje105.txt - Kawuco (20413) makes the 16
# level-105..115 armours of the pl-wiki "Wytwarzanie Zbroi" from the level-90 one +5..+9 + Plan Zbroi + a dye + 5
# sheets (80 recipes, 5-50% by plus, 3 000 000 Yang; GF 25.2.17 cube.txt, the Lykan ones left out). The items and
# their refining: mariadb/playerbot/zbroje105.sql (tools/zbroje105). After cube.wiki_kto.txt, the last cube step before it.
COPY cube.zbroje105.txt /tmp/cube-105/
RUN set -eu; C=/opt/metin2/share/locale/poland/cube.txt; A=/tmp/cube-105/cube.zbroje105.txt \
 && ! grep -q 'MT2009_PLUS_ARMOR105_V1' "$C" \
 && sed -i '1s/^\xEF\xBB\xBF//; s/\r$//; s/$/\r/' "$A" \
 && n=$(grep -c -E '^section' "$A") && b=$(grep -c -E '^section' "$C") \
 && { [ -z "$(tail -c 1 "$C")" ] || printf '\r\n' >> "$C"; } \
 && cat "$A" >> "$C" \
 && test "$n" -eq 80 && test "$(grep -c -E '^section' "$C")" -eq "$((b + n))" \
 && test "$(grep -c -E '^npc[[:blank:]]+20413' "$A")" -eq 80 \
 && rm -rf /tmp/cube-105 \
 && echo "share: level-105 armours at Kawuco ($n, MT2009_PLUS_ARMOR105_V1)"

# MT2009_PLUS_NPC_CRAFT_WINDOW_V1 (share; the owner, 22 October 2026: "at every NPC with crafting a window must open and
# show what you need to give", as the global servers - their client's cube.txt gives these NPCs the window):
# cube.npc_okno.txt - the crafts that were quest talks: Mistrz Chi (20823, Dongan) the four SungMa gloves, the twelve
# jade jewellery pieces and the five Kamienie Mocy Demonow; Tajemniczy Oltarz (20850, Namgan) Esencja Talizmanu and
# Tajemniczy Talizman; Baek-Go (20018) Lekarstwo Iluzji and Zwyczajna Szata Aury; Admiral Angmur (20378 / 20812) his
# armours 66 > 90 > 105 with the stones and bonuses kept (copy_attr) - this world's amounts, Yang, Gaya and chances.
# Quests rekawice, yohara_mapy3, yohara_mapy4, przebudzeni_bossowie, szata_aury and angmur open the windows instead of
# crafting in the talk; Seon-Pyeong's (20091) rows the core makes from the elite refine sets (server-patches/gaya),
# so he may have none here. Mistrz Chi, the altar and Angmur must have no recipe before; the last cube step.
# cube_improve.txt: the window's chance-raising items (vnum, bonus, category) - read by the core (server-patches/gaya).
COPY cube_improve.txt /opt/metin2/share/locale/poland/cube_improve.txt
COPY cube.npc_okno.txt /tmp/cube-okno/
RUN set -eu; C=/opt/metin2/share/locale/poland/cube.txt; A=/tmp/cube-okno/cube.npc_okno.txt \
 && ! grep -q 'MT2009_PLUS_NPC_CRAFT_WINDOW_V1' "$C" \
 && ! grep -q -E '^npc[[:blank:]]+(20823|20850|20378|20812|20091)[[:space:]]*$' "$C" \
 && sed -i '1s/^\xEF\xBB\xBF//; s/\r$//; s/$/\r/' "$A" \
 && n=$(grep -c -E '^section' "$A") && b=$(grep -c -E '^section' "$C") \
 && { [ -z "$(tail -c 1 "$C")" ] || printf '\r\n' >> "$C"; } \
 && cat "$A" >> "$C" \
 && test "$n" -eq 49 && test "$(grep -c -E '^section' "$C")" -eq "$((b + n))" \
 && test "$(grep -c -E '^npc[[:blank:]]+(20378|20812)[[:space:]]*$' "$C")" -eq 24 \
 && test "$(grep -c -E '^npc[[:blank:]]+20823[[:space:]]*$' "$C")" -eq 21 \
 && test "$(grep -c -E '^npc[[:blank:]]+20850[[:space:]]*$' "$C")" -eq 2 \
 && rm -rf /tmp/cube-okno \
 && echo "share: NPC crafting windows ($n recipes: Mistrz Chi, Tajemniczy Oltarz, Baek-Go, Admiral Angmur; MT2009_PLUS_NPC_CRAFT_WINDOW_V1)"

# MT2009_PLUS_RUNY_WYKUWANIA_V1 (share; the owner, 5 November 2026: "dodaj wszystkie runy zgodnie z wiki"): cube.runy.txt
# (tools/runy/gen_runy.py) - Yu-Hwan (20017) turns two Runy Wykuwania of one kind into one of the next grade (2*..5*,
# 40%, 2/4/6/10 Gaya, 200 000..1 000 000 Yang - the pl-wiki's item pages); his window opens by quest mikstury_okno.
# The runes' items: runy_wykuwania.sql (apply.sh); their chance bonus: cube_improve.txt above. No rune recipe before.
COPY cube.runy.txt /tmp/cube-runy/
RUN set -eu; C=/opt/metin2/share/locale/poland/cube.txt; A=/tmp/cube-runy/cube.runy.txt \
 && ! grep -q 'MT2009_PLUS_RUNY_WYKUWANIA_V1' "$C" \
 && ! grep -q -E '^reward[[:blank:]]+796([0-5][0-9])[[:blank:]]' "$C" \
 && sed -i '1s/^\xEF\xBB\xBF//; s/\r$//; s/$/\r/' "$A" \
 && n=$(grep -c -E '^section' "$A") && b=$(grep -c -E '^section' "$C") \
 && { [ -z "$(tail -c 1 "$C")" ] || printf '\r\n' >> "$C"; } \
 && cat "$A" >> "$C" \
 && test "$n" -eq 44 && test "$(grep -c -E '^section' "$C")" -eq "$((b + n))" \
 && test "$(grep -c -E '^reward[[:blank:]]+796[0-5][0-9][[:blank:]]+1' "$C")" -eq 44 \
 && test "$(grep -c -E '^gaya[[:blank:]]+(2|4|6|10)[[:space:]]*$' "$A")" -eq 44 \
 && test "$(grep -c -E '^796[0-5][0-9][[:blank:]]' /opt/metin2/share/locale/poland/cube_improve.txt)" -eq 55 \
 && rm -rf /tmp/cube-runy \
 && echo "share: Runy Wykuwania at Yu-Hwan ($n recipes; MT2009_PLUS_RUNY_WYKUWANIA_V1)"

# MT2009_PLUS_YOHARA_CRACK_V1 (share): Statua Szczeliny Czasu and the first Time Rift dungeon (the owner, 14 October
# 2026: only Zaklety Las for now; pl-wiki "Statua Szczeliny Czasu", "Zaklety Las (SZC)", "Erebu (SZC)", the six SZC
# missions; Owsap v6.2.6 crack_dawnmist_dungeon for the spawns and the stages) - Zaklety Las (SZC) (404,
# metin2_map_boss_crack_dawnmist, the official base 332800 1817600 - no map of ours overlaps it; the terrain of Zaklety
# Las (PB), quest jotun_szc) on the Yohara core (bin/m2-render-config); Statua Szczeliny Czasu (20472) on Plaskowyz
# Iluzji at the wiki's cell 103,90 (quest szczelina_czasu). tools/yohara_crack/gen_ycrack.py made everything here: the
# folder, the rooms' spawn files (data/dungeon/jotun_szc: Owsap's points), groups 6178-6184 and 6193 (Owsap's
# 6401-6408) - none may exist before -, the statue's npc line. No drop file and no chest: the monsters drop nothing
# there (server-patches/szczelina). Monsters, NPCs, Handlarka Iluzji's Zegarek Kieszonkowy rows: yohara_crack.sql;
# items: yohara_items_crack.sql. The dungeon panel gets jotun_szc (the ticket Zegarek Kieszonkowy, party 2-8, level 110,
# the entrance on the plateau beside the statue).
COPY yohara_crack/ /tmp/yohara-crack-add/
RUN set -eu; L=/opt/metin2/share/locale/poland; A=/tmp/yohara-crack-add \
 && find "$A" -type f -name '*.txt' -exec sed -i '1s/^\xEF\xBB\xBF//; s/\r$//; s/$/\r/' {} + \
 && for p in "404 metin2_map_boss_crack_dawnmist 0c00000010000000 332800 1817600"; do \
      set -- $p; \
      { rm -rf "$L/map/$2" && cp -a "$A/map/$2" "$L/map/" \
        && test "$(od -An -tx1 -N8 "$L/map/$2/server_attr" | tr -d ' \n')" = "$3" \
        && grep -q -E "^BasePosition[[:blank:]]+$4[[:blank:]]+$5" "$L/map/$2/Setting.txt" \
        && test -s "$L/map/$2/Town.txt" \
        && { [ -z "$(tail -c 1 "$L/map/index")" ] || printf '\n' >> "$L/map/index"; } \
        && sed -i -E "/^$1[[:blank:]]/d" "$L/map/index" \
        && printf '%s %s\n' "$1" "$2" >> "$L/map/index" \
        && test "$(grep -c -E "^$1[[:blank:]]+$2[[:space:]]*\$" "$L/map/index")" = 1; } \
        || { echo "FATAL: Szczelina Czasu map $1 $2"; exit 1; }; \
    done \
 && N="$L/map/metin2_map_labyrinth/npc.txt" \
 && test -f "$N" \
 && { [ -z "$(tail -c 1 "$N")" ] || printf '\r\n' >> "$N"; } \
 && { grep -q -E '[[:blank:]]20472[[:space:]]*$' "$N" || cat "$A/plateau_npc.txt" >> "$N"; } \
 && test "$(grep -c -E '^m[[:blank:]]+103[[:blank:]]+90[[:blank:]].*[[:blank:]]20472[[:space:]]*$' "$N")" = 1 \
 && test "$(grep -c -E '[[:blank:]]20472[[:space:]]*$' "$N")" = 1 \
 && mkdir -p /opt/metin2/share/data/dungeon && rm -rf /opt/metin2/share/data/dungeon/jotun_szc \
 && cp -a "$A/data/dungeon/jotun_szc" /opt/metin2/share/data/dungeon/ \
 && test "$(ls /opt/metin2/share/data/dungeon/jotun_szc | wc -l)" = 4 \
 && GV='(617[89]|618[0-4]|6193)' \
 && f="$L/group.txt" \
 && ! grep -q -E "^[[:blank:]]*Vnum[[:blank:]]+$GV[[:space:]]*\$" "$f" \
 && { [ -z "$(tail -c 1 "$f")" ] || printf '\r\n' >> "$f"; } \
 && cat "$A/group.yohara_crack.txt" >> "$f" \
 && test "$(grep -c -E "^[[:blank:]]*Vnum[[:blank:]]+$GV[[:space:]]*\$" "$f")" = 8 \
 && MV='(426[0-9]|427[0-2]|4403|812[67])' \
 && ! grep -q -i -E "^[[:blank:]]*mob[[:blank:]]+$MV([^0-9]|\$)" "$L/mob_drop_item.txt" \
 && I="$L/dungeon_info.txt" \
 && { LC_ALL=C grep -a -q -E '^dungeon[[:blank:]]+jotun_szc[[:blank:]]' "$I" \
      || { { [ -z "$(tail -c 1 "$I")" ] || printf '\n' >> "$I"; }; \
           printf 'dungeon\tjotun_szc\t404\t1\txy\t397\t3178\t18016\t110\t0\t2\t8\t4403\t-\t0\t31147\t1\tZakl\352ty_Las_(SZC)\tP\263askowy\277_Iluzji\n' >> "$I"; }; } \
 && test "$(LC_ALL=C grep -a -c -E '^dungeon[[:blank:]]+jotun_szc[[:blank:]]' "$I")" = 1 \
 && for f in "$L/translate.lua" "$L/quest/libs/translate/translate.lua"; do \
      [ -f "$f" ] || continue; \
      LC_ALL=C grep -a -q 'map_names\[404\]' "$f" && continue; \
      { [ -z "$(tail -c 1 "$f")" ] || printf '\r\n' >> "$f"; }; \
      printf '\r\n-- MT2009_PLUS_YOHARA_CRACK_V1\r\ntranslate.general.map_names[404] = "Zakl\352ty Las (SZC)"\r\n' >> "$f"; \
    done \
 && rm -rf "$A" \
 && echo "share: Szczelina Czasu - Statua Szczeliny Czasu on Plaskowyz Iluzji, Zaklety Las (SZC) (404): map, rooms, groups, the dungeon panel"
# MT2009_PLUS_YOHARA_CRACK2_V1 (share): the three other Time Rift dungeons (the owner, 21 October 2026: "Szczeliny Czasu
# - 3 brakujace lochy"; pl-wiki "Statua Szczeliny Czasu", "Grota Wygnancow 2 (SZC)", "Twierdza Czerwonego Smoka (SZC)",
# "Straznica Nemere (SZC)" and their bosses; Owsap v6.2.6 crack_*_dungeon for the spawns, the groups and the stages) -
# Grota Wygnancow 2 (SZC) (405, metin2_map_boss_crack_skipia, base 0 1817600, quest beran_szc), Twierdza Czerwonego Smoka
# (SZC) (406, metin2_map_boss_crack_flame, base 153600 1817600, razador_szc), Straznica Nemere (SZC) (407,
# metin2_map_boss_crack_snow, base 230400 1817600, nemere_szc) - the official bases, no map of ours overlaps them; the
# PB twins' terrain - on the Yohara core (bin/m2-render-config), entered from Statua Szczeliny Czasu (quest
# szczelina_czasu). tools/yohara_crack2/gen_ycrack2.py made everything here: the folders, the rooms' spawn files
# (data/dungeon/beran_szc, razador_szc, nemere_szc: Owsap's points), Owsap's groups 4201-4212 / 6021-6031 / 6071-6082 and
# groups of groups 4201-4207 / 6021-6023 - none may exist before. No drop file and no chest: the monsters drop nothing
# there (server-patches/szczelina, MT2009_PLUS_YOHARA_CRACK2_V1) but Beran-Setaou (SZC)'s yang. Monsters and NPCs:
# yohara_crack2.sql; items: yohara_items_crack2.sql. The dungeon panel gets beran_szc / razador_szc / nemere_szc (the
# ticket Zegarek Kieszonkowy, party 2-8, level 110, the entrance on the plateau beside the statue).
COPY yohara_crack2/ /tmp/yohara-crack2-add/
RUN set -eu; L=/opt/metin2/share/locale/poland; A=/tmp/yohara-crack2-add \
 && find "$A" -type f -name '*.txt' -exec sed -i '1s/^\xEF\xBB\xBF//; s/\r$//; s/$/\r/' {} + \
 && for p in "405 metin2_map_boss_crack_skipia 1800000018000000 0 1817600" \
             "406 metin2_map_boss_crack_flame 0c0000000c000000 153600 1817600" \
             "407 metin2_map_boss_crack_snow 100000000c000000 230400 1817600"; do \
      set -- $p; \
      { rm -rf "$L/map/$2" && cp -a "$A/map/$2" "$L/map/" \
        && test "$(od -An -tx1 -N8 "$L/map/$2/server_attr" | tr -d ' \n')" = "$3" \
        && grep -q -E "^BasePosition[[:blank:]]+$4[[:blank:]]+$5" "$L/map/$2/Setting.txt" \
        && test -s "$L/map/$2/Town.txt" \
        && { [ -z "$(tail -c 1 "$L/map/index")" ] || printf '\n' >> "$L/map/index"; } \
        && sed -i -E "/^$1[[:blank:]]/d" "$L/map/index" \
        && printf '%s %s\n' "$1" "$2" >> "$L/map/index" \
        && test "$(grep -c -E "^$1[[:blank:]]+$2[[:space:]]*\$" "$L/map/index")" = 1; } \
        || { echo "FATAL: Szczelina Czasu map $1 $2"; exit 1; }; \
    done \
 && mkdir -p /opt/metin2/share/data/dungeon \
 && for s in beran_szc:3 razador_szc:7 nemere_szc:10; do \
      rm -rf "/opt/metin2/share/data/dungeon/${s%%:*}" \
      && cp -a "$A/data/dungeon/${s%%:*}" /opt/metin2/share/data/dungeon/ \
      && test "$(ls "/opt/metin2/share/data/dungeon/${s%%:*}" | wc -l)" = "${s##*:}" \
      || { echo "FATAL: Szczelina Czasu rooms ${s%%:*}"; exit 1; }; \
    done \
 && GV='(420[1-9]|421[0-2]|602[1-9]|603[01]|607[1-9]|608[0-2])' \
 && f="$L/group.txt" \
 && ! grep -q -E "^[[:blank:]]*Vnum[[:blank:]]+$GV[[:space:]]*\$" "$f" \
 && { [ -z "$(tail -c 1 "$f")" ] || printf '\r\n' >> "$f"; } \
 && cat "$A/group.yohara_crack2.txt" >> "$f" \
 && test "$(grep -c -E "^[[:blank:]]*Vnum[[:blank:]]+$GV[[:space:]]*\$" "$f")" = 35 \
 && GG='(420[1-7]|602[1-3])' \
 && f="$L/group_group.txt" \
 && ! grep -q -E "^[[:blank:]]*Vnum[[:blank:]]+$GG[[:space:]]*\$" "$f" \
 && { [ -z "$(tail -c 1 "$f")" ] || printf '\r\n' >> "$f"; } \
 && cat "$A/group_group.yohara_crack2.txt" >> "$f" \
 && test "$(grep -c -E "^[[:blank:]]*Vnum[[:blank:]]+$GG[[:space:]]*\$" "$f")" = 10 \
 && MV='(420[0-9]|4210|422[0-9]|424[0-9]|440[0-2]|812[0-5]|20518)' \
 && ! grep -q -i -E "^[[:blank:]]*mob[[:blank:]]+$MV([^0-9]|\$)" "$L/mob_drop_item.txt" \
 && I="$L/dungeon_info.txt" \
 && { LC_ALL=C grep -a -q -E '^dungeon[[:blank:]]+beran_szc[[:blank:]]' "$I" \
      || { { [ -z "$(tail -c 1 "$I")" ] || printf '\n' >> "$I"; }; \
           printf 'dungeon\tberan_szc\t405\t1\txy\t397\t3178\t18016\t110\t0\t2\t8\t4400\t-\t0\t31147\t1\tGrota_Wygna\361c\363w_2_(SZC)\tP\263askowy\277_Iluzji\n' >> "$I"; \
           printf 'dungeon\trazador_szc\t406\t1\txy\t397\t3178\t18016\t110\t0\t2\t8\t4401\t-\t0\t31147\t1\tTwierdza_Czerwonego_Smoka_(SZC)\tP\263askowy\277_Iluzji\n' >> "$I"; \
           printf 'dungeon\tnemere_szc\t407\t1\txy\t397\t3178\t18016\t110\t0\t2\t8\t4402\t-\t0\t31147\t1\tStra\277nica_Nemere_(SZC)\tP\263askowy\277_Iluzji\n' >> "$I"; }; } \
 && test "$(LC_ALL=C grep -a -c -E '^dungeon[[:blank:]]+(beran_szc|razador_szc|nemere_szc)[[:blank:]]' "$I")" = 3 \
 && for f in "$L/translate.lua" "$L/quest/libs/translate/translate.lua"; do \
      [ -f "$f" ] || continue; \
      LC_ALL=C grep -a -q 'map_names\[405\]' "$f" && continue; \
      { [ -z "$(tail -c 1 "$f")" ] || printf '\r\n' >> "$f"; }; \
      printf '\r\n-- MT2009_PLUS_YOHARA_CRACK2_V1\r\ntranslate.general.map_names[405] = "Grota Wygna\361c\363w 2 (SZC)"\r\ntranslate.general.map_names[406] = "Twierdza Czerwonego Smoka (SZC)"\r\ntranslate.general.map_names[407] = "Stra\277nica Nemere (SZC)"\r\n' >> "$f"; \
    done \
 && rm -rf "$A" \
 && echo "share: Szczelina Czasu - Grota Wygnancow 2 (SZC) (405), Twierdza Czerwonego Smoka (SZC) (406), Straznica Nemere (SZC) (407): maps, rooms, groups, the dungeon panel"
# MT2009_PLUS_YOHARA_ZAKLETY_V1 (share): Zaklety Las and Erebu - the official Enchanted Forest past the Temple of Ochao
# (the owner, 14 October 2026: it replaces the Arezzo forest, natural_map 362, gone from the Arezzo step above; pl-wiki
# "Zaklety Las", "Erebu", the seven missions; Owsap v6.2.6 metin2_map_dawnmist_dungeon_01 for the spawns) - Zaklety Las
# (353, metin2_map_dawnmist_dungeon_01, the official base 768000 1408000 - no map of ours overlaps it; GF's terrain, the
# same as the PB / SZC forests') on the Yohara core (bin/m2-render-config): the Temple of Ochao's portal leads there
# (quest temple_of_the_ochao), the guards' missions (quest zaklety_las), Erebu at Przywodca Strazy Lasu (quest erebu,
# a private copy of the map's boss corner). tools/yohara_zaklety/gen_yzaklety.py made everything here: the folder
# (Owsap's regen / boss / stone, the guards at the wiki's cells), Owsap's motions of the forest's races (data/monster:
# trent_*, thunder_boss - every run.msa with its Accumulation), groups 6311-6318 and 6330-6333 - none may exist before -,
# the wiki's drops (11 groups) and the two chests of Erebu (50266, 54701). Monsters and NPCs:
# yohara_zaklety.sql; items: yohara_items_zaklety.sql. The dungeon panel gets erebu (Kamien Driad, party 5-8, level 95,
# 2 h after the end: the flag erebu.end); /goto las for game masters.
COPY yohara_zaklety/ /tmp/yohara-zaklety-add/
RUN set -eu; L=/opt/metin2/share/locale/poland; A=/tmp/yohara-zaklety-add; D=/opt/metin2/share/data/monster \
 && find "$A" -type f -name '*.txt' -exec sed -i '1s/^\xEF\xBB\xBF//; s/\r$//; s/$/\r/' {} + \
 && for p in "353 metin2_map_dawnmist_dungeon_01 0c00000010000000 768000 1408000"; do \
      set -- $p; \
      { rm -rf "$L/map/$2" && cp -a "$A/map/$2" "$L/map/" \
        && test "$(od -An -tx1 -N8 "$L/map/$2/server_attr" | tr -d ' \n')" = "$3" \
        && grep -q -E "^BasePosition[[:blank:]]+$4[[:blank:]]+$5" "$L/map/$2/Setting.txt" \
        && test -s "$L/map/$2/Town.txt" && test -s "$L/map/$2/regen.txt" && test -s "$L/map/$2/npc.txt" \
        && { [ -z "$(tail -c 1 "$L/map/index")" ] || printf '\n' >> "$L/map/index"; } \
        && sed -i -E "/^$1[[:blank:]]/d" "$L/map/index" \
        && printf '%s %s\n' "$1" "$2" >> "$L/map/index" \
        && test "$(grep -c -E "^$1[[:blank:]]+$2[[:space:]]*\$" "$L/map/index")" = 1; } \
        || { echo "FATAL: Zaklety Las map $1 $2"; exit 1; }; \
    done \
 && ! grep -q -E '^362[[:blank:]]' "$L/map/index" \
 && mkdir -p "$D" \
 && for m in "$A"/data/monster/*; do rm -rf "$D/$(basename "$m")"; cp -a "$m" "$D/"; done \
 && test -s "$D/thunder_boss/motlist.txt" && test -s "$D/trent_boss2/motlist.txt" \
 && test -z "$(for m in "$A"/data/monster/*/run.msa; do grep -q -E '^Accumulation[[:blank:]]+[-0-9.]+[[:blank:]]+-[0-9]' "$m" || echo "$m"; done)" \
 && GV='(631[1-8]|633[0-3])' \
 && f="$L/group.txt" \
 && ! grep -q -E "^[[:blank:]]*Vnum[[:blank:]]+$GV[[:space:]]*\$" "$f" \
 && { [ -z "$(tail -c 1 "$f")" ] || printf '\r\n' >> "$f"; } \
 && cat "$A/group.yohara_zaklety.txt" >> "$f" \
 && test "$(grep -c -E "^[[:blank:]]*Vnum[[:blank:]]+$GV[[:space:]]*\$" "$f")" = 12 \
 && MV='(640[1-4]|640[6-8]|6414|6192|8059|8061)' \
 && F="$L/mob_drop_item.txt" \
 && ! grep -q -i -E "^[[:blank:]]*mob[[:blank:]]+$MV([^0-9]|\$)" "$F" \
 && { [ -z "$(tail -c 1 "$F")" ] || printf '\r\n' >> "$F"; } \
 && cat "$A/mob_drop_item.yohara_zaklety.txt" >> "$F" \
 && test "$(grep -c -i -E "^[[:blank:]]*mob[[:blank:]]+$MV([^0-9]|\$)" "$F")" = 11 \
 && SV='(50266|54701)' \
 && G="$L/special_item_group.txt" \
 && ! grep -q -E "^[[:blank:]]*Vnum[[:blank:]]+$SV([^0-9]|\$)" "$G" \
 && { [ -z "$(tail -c 1 "$G")" ] || printf '\r\n' >> "$G"; } \
 && cat "$A/special_item_group.yohara_zaklety.txt" >> "$G" \
 && test "$(grep -c -E "^[[:blank:]]*Vnum[[:blank:]]+$SV([^0-9]|\$)" "$G")" = 2 \
 && I="$L/dungeon_info.txt" \
 && { LC_ALL=C grep -a -q -E '^dungeon[[:blank:]]+erebu[[:blank:]]' "$I" \
      || { { [ -z "$(tail -c 1 "$I")" ] || printf '\n' >> "$I"; }; \
           printf 'dungeon\terebu\t353\t1\txy\t353\t8291\t14187\t95\t0\t5\t8\t6192\terebu.end\t7200\t30613\t1\tErebu_(Jotun_Thrym)\tZakl\352ty_Las\n' >> "$I"; }; } \
 && test "$(LC_ALL=C grep -a -c -E '^dungeon[[:blank:]]+erebu[[:blank:]]' "$I")" = 1 \
 && for f in "$L/translate.lua" "$L/quest/libs/translate/translate.lua"; do \
      [ -f "$f" ] || continue; \
      LC_ALL=C grep -a -q 'map_names\[353\]' "$f" && continue; \
      { [ -z "$(tail -c 1 "$f")" ] || printf '\r\n' >> "$f"; }; \
      printf '\r\n-- MT2009_PLUS_YOHARA_ZAKLETY_V1\r\ntranslate.general.map_names[353] = "Zakl\352ty Las"\r\n' >> "$f"; \
    done \
 && LC_ALL=C grep -a -q 'map_names\[353\]' "$L/quest/libs/translate/translate.lua" \
 && ! LC_ALL=C grep -a -q 'map_names\[362\]' "$L/quest/libs/translate/translate.lua" \
 && S="$L/settings.lua" \
 && { LC_ALL=C grep -a -q 'add_goto_info("las"' "$S" || printf 'add_goto_info("las", 0, 353, 8158, 15050)\r\n' >> "$S"; } \
 && LC_ALL=C grep -a -q 'add_goto_info("las", 0, 353,' "$S" \
 && rm -rf "$A" \
 && echo "share: Zaklety Las (353) and Erebu - map, motions, groups, drops, chests, the dungeon panel"
# MT2009_PLUS_YOHARA_MELEY_V1 (share): Schronienie Meley - the Dragon Queen Meley's lair (the owner, 15 October 2026:
# "dodaj loch Meley, drop zgodnie z wiki"; pl-wiki "Schronienie Meley (dla gildii)", its monsters, items and chests;
# Owsap v6.2.6 GuildDragonLair.lua / guild_dragonlair.cpp for the stages) - 356 metin2_map_n_flame_dragon (Owsap's
# index; GF's base 307200 1510400 is our Swiatynia Zodiaku's ground, so 281600 1510400 - no map of ours overlaps it)
# on game1 with the bots (bin/m2-render-config), quest meley_dungeon; Straznik Smokow Dolnarr (20419) on Doyyumhwaji
# (62) at the wiki's 83,851. tools/yohara_meley/gen_ymeley.py made everything here: the folder (GF's attr.atr, Meley's
# cells opened), the stages' spawn files (data/dungeon/meley), Owsap's motions of six races our share lacks
# (data/monster), groups 6337-6339 - none may exist before -, the wiki's drops (6 groups, TEMP rates - PROCENTY.md) and
# the two chests (54706, 54707 - the official 50270 / 50271 are our Razador / Nemere chests). Monsters and NPCs:
# yohara_meley.sql; items: yohara_items_meley.sql. The dungeon panel gets meley (party 1-8, level 90, the bots' 3 h
# rest: the flag meley_dungeon.entry).
COPY yohara_meley/ /tmp/yohara-meley-add/
RUN set -eu; L=/opt/metin2/share/locale/poland; A=/tmp/yohara-meley-add; D=/opt/metin2/share/data/monster \
 && find "$A" -type f -name '*.txt' -exec sed -i '1s/^\xEF\xBB\xBF//; s/\r$//; s/$/\r/' {} + \
 && for p in "356 metin2_map_n_flame_dragon 0400000004000000 281600 1510400"; do \
      set -- $p; \
      { rm -rf "$L/map/$2" && cp -a "$A/map/$2" "$L/map/" \
        && test "$(od -An -tx1 -N8 "$L/map/$2/server_attr" | tr -d ' \n')" = "$3" \
        && grep -q -E "^BasePosition[[:blank:]]+$4[[:blank:]]+$5" "$L/map/$2/Setting.txt" \
        && test -s "$L/map/$2/Town.txt" \
        && { [ -z "$(tail -c 1 "$L/map/index")" ] || printf '\n' >> "$L/map/index"; } \
        && sed -i -E "/^$1[[:blank:]]/d" "$L/map/index" \
        && printf '%s %s\n' "$1" "$2" >> "$L/map/index" \
        && test "$(grep -c -E "^$1[[:blank:]]+$2[[:space:]]*\$" "$L/map/index")" = 1; } \
        || { echo "FATAL: Schronienie Meley map $1 $2"; exit 1; }; \
    done \
 && N="$L/map/metin2_map_n_flame_01/npc.txt" \
 && test -f "$N" \
 && { [ -z "$(tail -c 1 "$N")" ] || printf '\r\n' >> "$N"; } \
 && { grep -q -E '[[:blank:]]20419[[:space:]]*$' "$N" || cat "$A/flame_npc.txt" >> "$N"; } \
 && test "$(grep -c -E '^m[[:blank:]]+83[[:blank:]]+851[[:blank:]].*[[:blank:]]20419[[:space:]]*$' "$N")" = 1 \
 && test "$(grep -c -E '[[:blank:]]20419[[:space:]]*$' "$N")" = 1 \
 && mkdir -p /opt/metin2/share/data/dungeon && rm -rf /opt/metin2/share/data/dungeon/meley \
 && cp -a "$A/data/dungeon/meley" /opt/metin2/share/data/dungeon/ \
 && test "$(ls /opt/metin2/share/data/dungeon/meley | wc -l)" = 3 \
 && mkdir -p "$D" \
 && for m in "$A"/data/monster/*; do rm -rf "$D/$(basename "$m")"; cp -a "$m" "$D/"; done \
 && test -s "$D/reddragon_room_boss2/motlist.txt" && test -s "$D/metinstone_reddragon_statue/motlist.txt" \
 && test -s "$D/metinstone_egg/motlist.txt" && test -s "$D/reddragon_room_human_boss/motlist.txt" \
 && GV='(633[7-9])' \
 && f="$L/group.txt" \
 && ! grep -q -E "^[[:blank:]]*Vnum[[:blank:]]+$GV[[:space:]]*\$" "$f" \
 && { [ -z "$(tail -c 1 "$f")" ] || printf '\r\n' >> "$f"; } \
 && cat "$A/group.yohara_meley.txt" >> "$f" \
 && test "$(grep -c -E "^[[:blank:]]*Vnum[[:blank:]]+$GV[[:space:]]*\$" "$f")" = 3 \
 && MV='(611[0134-5]|20422)' \
 && F="$L/mob_drop_item.txt" \
 && ! grep -q -i -E "^[[:blank:]]*mob[[:blank:]]+$MV([^0-9]|\$)" "$F" \
 && { [ -z "$(tail -c 1 "$F")" ] || printf '\r\n' >> "$F"; } \
 && cat "$A/mob_drop_item.yohara_meley.txt" >> "$F" \
 && test "$(grep -c -i -E "^[[:blank:]]*mob[[:blank:]]+$MV([^0-9]|\$)" "$F")" = 6 \
 && SV='(54706|54707|954706|954707)' \
 && G="$L/special_item_group.txt" \
 && ! grep -q -E "^[[:blank:]]*Vnum[[:blank:]]+$SV([^0-9]|\$)" "$G" \
 && { [ -z "$(tail -c 1 "$G")" ] || printf '\r\n' >> "$G"; } \
 && cat "$A/special_item_group.yohara_meley.txt" >> "$G" \
 && test "$(grep -c -E "^[[:blank:]]*Vnum[[:blank:]]+$SV([^0-9]|\$)" "$G")" = 4 \
 && I="$L/dungeon_info.txt" \
 && { LC_ALL=C grep -a -q -E '^dungeon[[:blank:]]+meley[[:blank:]]' "$I" \
      || { { [ -z "$(tail -c 1 "$I")" ] || printf '\n' >> "$I"; }; \
           printf 'dungeon\tmeley\t356\t1\txy\t62\t5972\t6997\t90\t0\t1\t8\t6193\tmeley_dungeon.entry\t10800\t0\t0\tSchronienie_Meley\tDoyyumhwaji\ncost\tmeley\t7500000\ndrop\tmeley\t54706\t1\t100\ndrop\tmeley\t54707\t1\t100\n' >> "$I"; }; } \
 && test "$(LC_ALL=C grep -a -c -E '^dungeon[[:blank:]]+meley[[:blank:]]' "$I")" = 1 \
 && for f in "$L/translate.lua" "$L/quest/libs/translate/translate.lua"; do \
      [ -f "$f" ] || continue; \
      LC_ALL=C grep -a -q 'map_names\[356\]' "$f" && continue; \
      { [ -z "$(tail -c 1 "$f")" ] || printf '\r\n' >> "$f"; }; \
      printf '\r\n-- MT2009_PLUS_YOHARA_MELEY_V1\r\ntranslate.general.map_names[356] = "Schronienie Meley"\r\n' >> "$f"; \
    done \
 && rm -rf "$A" \
 && echo "share: Schronienie Meley (356) - map, Dolnarr on Doyyumhwaji, stages, motions, groups, drops, chests, the dungeon panel"

# MT2009_PLUS_BALATHOR_V1: Krypta Balathora (author: dracaryS; server-patches/balathor, quest krypta_balathora) - the
# entrance: Straznik Smokow Dolnarr (20419) on Gora Sohan (61) at 668,93 as the wiki has it (owner, 29.10.2026) - the
# guild lair of the White Dragon: map 420 (metin2_map_guild_whitedragon_boss, 2x2 at 1152000 921600 - free in the
# atlas; its private copies 4200000+ are made by the engine's CBalathorManager), its line in the map index, the
# monsters' server motions (data/monster/guild_whitedragon*), balathor.json (the engine reads it from the locale
# folder: positions, timings, Dolnarr's exit on Doyyumhwaji 84 853, the register rules, the rewards) and the two
# chests (special_item_group.balathor.txt, items in balathor.sql). Which core hosts 420 is m2-render-config's: game1
# beside Doyyumhwaji, and only with M2_BALATHOR_ON=1 (MT2009_PLUS_BALATHOR_SWITCH_V1) - the lair is created on the core
# of the quest's NPC.
COPY balathor/ /tmp/balathor-add/
RUN set -eu; L=/opt/metin2/share/locale/poland; A=/tmp/balathor-add; D=/opt/metin2/share/data/monster \
 && rm -rf "$L/map/metin2_map_guild_whitedragon_boss" \
 && cp -a "$A/map/metin2_map_guild_whitedragon_boss" "$L/map/metin2_map_guild_whitedragon_boss" \
 && test -s "$L/map/metin2_map_guild_whitedragon_boss/server_attr" \
 && LC_ALL=C sed -i '/^420[[:blank:]]/d' "$L/map/index" \
 && { [ -z "$(tail -c 1 "$L/map/index")" ] || printf '\r\n' >> "$L/map/index"; } \
 && printf '420\tmetin2_map_guild_whitedragon_boss\r\n' >> "$L/map/index" \
 && test "$(grep -c -E '^420[[:blank:]]' "$L/map/index")" = 1 \
 && for m in "$A"/monster/*; do rm -rf "$D/$(basename "$m")"; cp -a "$m" "$D/"; done \
 && test -s "$D/guild_whitedragon_boss01/guild_whitedragon_boss01.msm" \
 && cp "$A/balathor.json" "$L/balathor.json" \
 && N="$L/map/map_n_snowm_01/npc.txt" \
 && test -f "$N" \
 && { [ -z "$(tail -c 1 "$N")" ] || printf '\r\n' >> "$N"; } \
 && { grep -q -E '^m[[:blank:]]+668[[:blank:]]+93[[:blank:]].*[[:blank:]]20419[[:space:]]*$' "$N" || printf 'm\t668\t93\t0\t0\t0\t3\t1m\t100\t1\t20419\r\n' >> "$N"; } \
 && test "$(grep -c -E '^m[[:blank:]]+668[[:blank:]]+93[[:blank:]].*[[:blank:]]20419[[:space:]]*$' "$N")" = 1 \
 && SV='(83075|83076)' \
 && G="$L/special_item_group.txt" \
 && ! grep -q -E "^[[:blank:]]*Vnum[[:blank:]]+$SV([^0-9]|\$)" "$G" \
 && { [ -z "$(tail -c 1 "$G")" ] || printf '\r\n' >> "$G"; } \
 && cat "$A/special_item_group.balathor.txt" >> "$G" \
 && test "$(grep -c -E "^[[:blank:]]*Vnum[[:blank:]]+$SV([^0-9]|\$)" "$G")" = 2 \
 && for f in "$L/translate.lua" "$L/quest/libs/translate/translate.lua"; do \
      [ -f "$f" ] || continue; \
      LC_ALL=C grep -a -q 'map_names\[420\]' "$f" && continue; \
      { [ -z "$(tail -c 1 "$f")" ] || printf '\r\n' >> "$f"; }; \
      printf '\r\n-- MT2009_PLUS_BALATHOR_V1\r\ntranslate.general.map_names[420] = "Krypta Balathora"\r\n' >> "$f"; \
    done \
 && chmod -R a+rX "$L/map/metin2_map_guild_whitedragon_boss" "$L/balathor.json" \
 && rm -rf "$A" \
 && echo "share: Krypta Balathora (420) - map, motions, balathor.json, chests 83075/83076"
# MT2009_PLUS_AREZZO_ARGES_SKILL_V1: Arges (9606, Dolina Cyklopow; the folder of the official
# cyclops boss 3190) uses skill 256, and the server times a monster's skill by the
# SPECIAL_ATTACKING event (type 4) of its motion - cyclops_boss/special_attack.msa has only
# effect events (its hit is the client's AttackingData), so every use ended in "UseMobSkill: No
# skill hit data for mob Arges index 0" (301 lines in one night's test, 6/7 October) and the skill
# never struck. A fifth event, the hit of the first impact (0.547 s), as Polifem's own
# special_attack.msa (cyclops_boss2) has it. Server side only; the client keeps its motion.
RUN set -eu; f=/opt/metin2/share/data/monster/cyclops_boss/special_attack.msa \
 && if ! grep -q 'MotionEventType      4' "$f"; then \
      test "$(grep -c 'MotionEventDataCount     4' "$f")" = 1; \
      sed -i 's/MotionEventDataCount     4/MotionEventDataCount     5/' "$f"; \
      n=$(grep -n '^}' "$f" | tail -1 | cut -d: -f1); \
      head -n $((n - 1)) "$f" > "$f.new"; \
      printf '    Group Event04\r\n    {\r\n        MotionEventType      4\r\n        StartingTime         0.547445\r\n        DuringTime           0.200000\r\n        EnableHitProcess     0\r\n        \r\n        AttackType           0\r\n        HittingType          2\r\n        StiffenTime          0.000000\r\n        InvisibleTime        0.300000\r\n        ExternalForce        0.000000\r\n        HitLimitCount        0\r\n        CollisionType        4\r\n        \r\n        SphereDataCount      1\r\n        Group SphereData00\r\n        {\r\n            Radius           400.000000\r\n            Position         0.000000 0.000000 0.000000\r\n        }\r\n    }\r\n}\r\n' >> "$f.new"; \
      mv "$f.new" "$f"; \
    fi \
 && test "$(grep -c 'MotionEventType      4' "$f")" = 1 \
 && test "$(grep -c 'MotionEventDataCount     5' "$f")" = 1 \
 && echo "share: Arges' skill hit (cyclops_boss/special_attack.msa)"
# (MT2009_PLUS_DUNGEON_DROP_V1: Razador (6091) and Nemere (6191) drop only yang - the owner,
# 29 September; their loot is the 2-5 chests per player of the quests - so every drop group
# of theirs is cut whole above but the 0% chest previews; item_manager.cpp drops nothing
# for them either.)
# The level-75 weapons, the Reaper's and Azrael's, not the Spider Baroness's
# (MT2009_PLUS_LEVEL75_DROP_V1; upstream 2.2.39, the operator's decision of
# 29 September). Her limit group (mob 2092) loses its 12 lines of
# level 75 - six families at +3 and +4 - and is numbered again: the reader
# stops at the first index a group lacks, and the drop preview lists every
# line whatever its chance. The Reaper (1093) and Azrael (2598) get the 7
# families of 75, the fan of 75 among them, in their own limit groups (a second
# one for a monster is ignored), numbered on from the last line - the Reaper's
# Dried Head above included: the Reaper +3 at 10%, +4 at 5%; Azrael
# +3 at 20%, +4 at 10%. The drop preview reads the loaded groups, so it follows.
RUN set -eu; F=/opt/metin2/share/locale/poland/mob_drop_item.txt \
 ; C='183 184 193 194 3163 3164 2173 2174 1133 1134 5123 5124' \
 ; A='1093:183:10:Zatruty_miecz+3 1093:184:5:Zatruty_miecz+4 \
      1093:193:10:Lwi_Miecz+3 1093:194:5:Lwi_Miecz+4 \
      1093:3163:10:Miecz_Zalu+3 1093:3164:5:Miecz_Zalu+4 \
      1093:2173:10:Stalowy_Luk_Kruka+3 1093:2174:5:Stalowy_Luk_Kruka+4 \
      1093:1133:10:Skrzydla_Demona_Chakr.+3 1093:1134:5:Skrzydla_Demona_Chakr.+4 \
      1093:7183:10:Wachlarz_8_Trigramow+3 1093:7184:5:Wachlarz_8_Trigramow+4 \
      1093:5123:10:Bambusowy_Dzwon+3 1093:5124:5:Bambusowy_Dzwon+4 \
      2598:183:20:Zatruty_miecz+3 2598:184:10:Zatruty_miecz+4 \
      2598:193:20:Lwi_Miecz+3 2598:194:10:Lwi_Miecz+4 \
      2598:3163:20:Miecz_Zalu+3 2598:3164:10:Miecz_Zalu+4 \
      2598:2173:20:Stalowy_Luk_Kruka+3 2598:2174:10:Stalowy_Luk_Kruka+4 \
      2598:1133:20:Skrzydla_Demona_Chakr.+3 2598:1134:10:Skrzydla_Demona_Chakr.+4 \
      2598:7183:20:Wachlarz_8_Trigramow+3 2598:7184:10:Wachlarz_8_Trigramow+4 \
      2598:5123:20:Bambusowy_Dzwon+3 2598:5124:10:Bambusowy_Dzwon+4' \
 && awk -v from=2092 -v cut="$C" -v add="$A" ' \
      function flush(   i, t, f, j, lead, mx, k, nm) { \
        if (typ == "limit" && mob == from) { \
          hits++; j = 0; \
          for (i = 1; i <= nb; i++) { \
            t = B[i]; sub(/\r$/, "", t); \
            if (split(t, f) >= 2 && f[1] ~ /^[0-9]+$/) { \
              if (f[2] in C) { gone++; continue; } \
              match(B[i], /^[ \t]*[0-9]+/); lead = substr(B[i], 1, RLENGTH); sub(/[0-9]+$/, "", lead); \
              print lead (++j) substr(B[i], RLENGTH + 1); \
            } else print B[i]; \
          } \
        } else if (typ == "limit" && (mob in NA)) { \
          got[mob]++; mx = 0; \
          for (i = 1; i <= nb; i++) { \
            t = B[i]; sub(/\r$/, "", t); \
            if (split(t, f) >= 2 && f[1] ~ /^[0-9]+$/) { \
              if (f[1] + 0 > mx) mx = f[1] + 0; \
              for (k = 1; k <= NA[mob]; k++) if (AV[mob, k] == f[2]) twice++; \
            } \
            if (i < nb) print B[i]; \
          } \
          for (k = 1; k <= NA[mob]; k++) { nm = AN[mob, k]; gsub(/_/, " ", nm); printf "\t%d\t%s\t1\t%s\t-- %s\r\n", mx + k, AV[mob, k], AP[mob, k], nm; } \
          print B[nb]; \
        } else for (i = 1; i <= nb; i++) print B[i]; \
      } \
      BEGIN { nc = split(cut, c, " "); for (i = 1; i <= nc; i++) C[c[i]] = 1; n = split(add, a, " "); for (i = 1; i <= n; i++) { split(a[i], p, ":"); k = ++NA[p[1]]; AV[p[1], k] = p[2]; AP[p[1], k] = p[3]; AN[p[1], k] = p[4]; } } \
      /^Group/ { inb = 1; nb = 0; mob = ""; typ = ""; } \
      !inb { print; next; } \
      { B[++nb] = $0; t = $0; sub(/\r$/, "", t); k = split(t, f); if (k >= 2 && tolower(f[1]) == "mob") mob = f[2]; if (k >= 2 && tolower(f[1]) == "type") typ = tolower(f[2]); } \
      /^}/ { flush(); inb = 0; } \
      END { if (inb) flush(); if (hits != 1 || gone != nc) { printf "share: %d limit groups of %s, %d of its %d lines of 75 cut\n", hits, from, gone, nc > "/dev/stderr"; bad = 1; } for (m in NA) if (got[m] != 1) { printf "share: %d limit groups of %s\n", got[m], m > "/dev/stderr"; bad = 1; } if (twice) { printf "share: %d lines of 75 were there already\n", twice > "/dev/stderr"; bad = 1; } exit bad; } \
      ' "$F" > "$F.new" \
 && mv "$F.new" "$F" \
 && awk -v from=2092 -v cut="$C" -v add="$A" ' \
      function check(   i, n, key, q) { \
        seen[mob]++; \
        for (i = 1; i <= nb; i++) if (I[i] != i) { printf "share: line %d of the limit group of %s is numbered %d\n", i, mob, I[i] > "/dev/stderr"; bad = 1; } \
        if (mob == from) { for (i = 1; i <= nb; i++) if (V[i] in C) { printf "share: %s is still in the limit group of %s\n", V[i], mob > "/dev/stderr"; bad = 1; } return; } \
        for (key in W) { split(key, q, SUBSEP); if (q[1] != mob) continue; n = 0; for (i = 1; i <= nb; i++) if (V[i] == q[2]) n++; if (n != 1) { printf "share: %s is %d times in the limit group of %s\n", q[2], n, mob > "/dev/stderr"; bad = 1; } } \
      } \
      BEGIN { nc = split(cut, c, " "); for (i = 1; i <= nc; i++) C[c[i]] = 1; n = split(add, a, " "); for (i = 1; i <= n; i++) { split(a[i], p, ":"); W[p[1], p[2]] = 1; M[p[1]] = 1; } } \
      /^Group/ { mob = ""; typ = ""; nb = 0; } \
      { t = $0; sub(/\r$/, "", t); k = split(t, f); if (k >= 2 && tolower(f[1]) == "mob") mob = f[2]; if (k >= 2 && tolower(f[1]) == "type") typ = tolower(f[2]); if (k >= 2 && f[1] ~ /^[0-9]+$/) { nb++; I[nb] = f[1] + 0; V[nb] = f[2]; } } \
      /^}/ && typ == "limit" && (mob == from || (mob in M)) { check(); } \
      END { if (seen[from] != 1) { printf "share: %d limit groups of %s\n", seen[from], from > "/dev/stderr"; bad = 1; } for (m in M) if (seen[m] != 1) { printf "share: %d limit groups of %s\n", seen[m], m > "/dev/stderr"; bad = 1; } exit bad; } \
      ' "$F" \
 && echo "share: the level-75 weapons are the Reaper's and Azrael's, not the Spider Baroness's"

# A herbal recipe is read without a wait (port/shareify.py renders this step;
# Iwakura for Derpsonkowy95, 29 September): crafting.learn_recipe wrote a wait
# of SKILLBOOK_LEARN_DELAY - twenty-one hours - on every recipe a read took and
# refused the next read until it ran out or an Exorcism Scroll was spent. It is
# no longer written, and one written before is no longer asked.
RUN set -eu; F=/opt/metin2/share/locale/poland/quest/libs/crafting/crafting.lua \
 && LC_ALL=C sed -i -E 's/^([[:blank:]]*local is_delay = )delta_delay > 0([[:space:]]*)$/\1false\2/; s/^([[:blank:]]*set_flag\("learn_delay"\.\.vnum, )get_time\(\) \+ SKILLBOOK_LEARN_DELAY\)([[:space:]]*)$/\10)\2/' "$F" \
 && test "$(LC_ALL=C grep -c -E '^[[:blank:]]*local is_delay = false[[:space:]]*$' "$F")" -eq 1 \
 && test "$(LC_ALL=C grep -c -E 'set_flag\("learn_delay"\.\.vnum, 0\)' "$F")" -eq 1 \
 && ! LC_ALL=C grep -q 'SKILLBOOK_LEARN_DELAY' "$F" \
 && echo "share: a recipe is read without a wait"

# MT2009_PLUS_RADA_PUSTELNIKA_V1 (the owner, 3 November 2026; server-patches/radapustelnika): Rada Pustelnika helps the
# skill books and the soul stones (pl-wiki), never a recipe - crafting.learn_recipe took its affect off at every recipe
# read and gave nothing for it. It stays on for the next book now.
RUN set -eu; F=/opt/metin2/share/locale/poland/quest/libs/crafting/crafting.lua \
 && test "$(LC_ALL=C grep -c -E '^[[:blank:]]*affect\.remove_new\(AFFECT_SKILL_BOOK_BONUS\)[[:space:]]*$' "$F")" -eq 1 \
 && LC_ALL=C sed -i -E 's/^([[:blank:]]*)affect\.remove_new\(AFFECT_SKILL_BOOK_BONUS\)([[:space:]]*)$/\1-- MT2009_PLUS_RADA_PUSTELNIKA_V1: Rada Pustelnika stays for the next book\2/' "$F" \
 && ! LC_ALL=C grep -q 'remove_new(AFFECT_SKILL_BOOK_BONUS)' "$F" \
 && echo "share: a recipe read leaves Rada Pustelnika on (MT2009_PLUS_RADA_PUSTELNIKA_V1)"

# Uriel's "Wytwarzanie" window (MT2009_PLUS_SASH_CLOTH_V1, the owner, 6 October):
# Metins and bosses drop Delikatne Sukno (80019) in place of the +0 sash
# (server-patches/raremobrules) and Theowahdan (60003; Uriel 20011 until MT2009_PLUS_TEOWADEN_V1) turns ten of them and 80 000
# yang into the plain sash, 85001 at 100% - crafting window 111 (CRAFTING_URIEL),
# which quest/acce_costume_uriel.quest opens, listing recipe 85001 of
# world.crafting_proto (mariadb/playerbot/apply.sh). Inside the crafting_data
# table, so the Seban panel's crafting editor reads it as the image's list.
RUN set -eu; F=/opt/metin2/share/locale/poland/quest/libs/crafting/crafting_data.lua \
 && if ! LC_ALL=C grep -q 'CRAFTING_URIEL' "$F"; then \
      test "$(tr -d '\r' < "$F" | LC_ALL=C grep -c -E '^CRAFTING_BUM = 110$')" -eq 1 \
      && test "$(tr -d '\r' < "$F" | LC_ALL=C grep -c -E '^[[:blank:]]*\[CRAFTING_BUM\] = \{ 221 \},$')" -eq 1 \
      && LC_ALL=C sed -i -E \
           -e 's/^CRAFTING_BUM = 110(\r?)$/&\nCRAFTING_URIEL = 111\1/' \
           -e 's/^([[:blank:]]*)\[CRAFTING_BUM\] = \{ 221 \},(\r?)$/&\n\1[CRAFTING_URIEL] = { 85001 },\2/' "$F"; \
    fi \
 && test "$(LC_ALL=C grep -c -E '^CRAFTING_URIEL = 111' "$F")" -eq 1 \
 && test "$(LC_ALL=C grep -c -E '^[[:blank:]]*\[CRAFTING_URIEL\] = \{ 85001 \},' "$F")" -eq 1 \
 && echo "share: Uriel's crafting window 111 (Delikatne Sukno -> the plain sash)"

# MT2009_PLUS_JEWELS75_V1 (the owner, 8 October: "dodaj kamienie z rud, tak samo jak dzialaja inne
# przetopy"): Rubin (50635), Granat (50636), Szmaragd (50637) and Szafir (50638) - the gems the
# Rubin/Granat/Szmaragd/Szafir jewellery's sockets take - are smelted as every przetop is, in a guild
# alchemist's crafting window (guild_building_melt.quest opens crafting.open(<the alchemist's
# race>)). The image has no alchemist of their own (Gameforge's 33010-33013 have no building here),
# so each of the twelve alchemists 20060-20072 lists the four after its own przetop, and they count
# as guild crafting (the 5% discount in the guild's own furnace) like 50621-50633. The recipes are
# world.crafting_proto 50635-50638 (mariadb/playerbot/apply.sh): 100 ore, 3 Magiczny Pyl, 60 000
# yang, 60%.
RUN set -eu; F=/opt/metin2/share/locale/poland/quest/libs/crafting/crafting_data.lua \
 && LC_ALL=C sed -i -E \
      -e 's/^([[:blank:]]*\[20(06[0-9]|07[0-2])\] = \{)(50(62[1-9]|63[0-3]))\},(\r?)$/\1\3, 50635, 50636, 50637, 50638},\5/' \
      -e 's/vnum >= 50621 and vnum <= 50633 -- przetopy/vnum >= 50621 and vnum <= 50638 -- przetopy/' "$F" \
 && test "$(LC_ALL=C grep -c -E '^[[:blank:]]*\[20(06[0-9]|07[0-2])\] = \{50(62[1-9]|63[0-3]), 50635, 50636, 50637, 50638\},' "$F")" -eq 12 \
 && test "$(LC_ALL=C grep -c 'vnum >= 50621 and vnum <= 50638 -- przetopy' "$F")" -eq 1 \
 && echo "share: the guild alchemists smelt Rubin / Granat / Szmaragd / Szafir too (MT2009_PLUS_JEWELS75_V1)"

# MT2009_PLUS_YOHARA_MAPS2_V1 (share): the second batch of Yohara maps (the owner, 14 October 2026; the pl-wiki for
# everything) on the Yohara core (game3, MT2009_PLUS_YOHARA_CORE_V1) - Seoganland (376, metin2_map_eastplain_02, 3x6),
# Namgan (377, metin2_map_eastplain_03, 4x2), Przelecz Yilad (385, metin2_map_snakevalley, 6x3), Wawoz Polnocnego
# Wiatru (388, metin2_map_icecrystalcave, 5x4 - the official folder of Northwind Canyon) and Schronienie Polnocnego
# Wiatru (393, metin2_map_whitedragoncave_01, 6x6), Owsap's indexes; every file made by tools/yohara_maps/gen_ymaps2.py
# (yohara_maps2/README.md: what came from where). server_attr from the GF client's attr.atr (tools/gf28 srvattr.py).
# Spawns: Owsap's (376, 377, 393) with the wiki's missing monsters / bosses / Metins at GF's positions, Ameria's (385)
# with the wiki's monsters and Metins, ours on Wawoz (Owsap's density, GF's positions decide lod / blyskawice). Jade
# veins (server-patches/jadeit) as the wiki names them. Portals: Dongan's to Seoganland (10128, appended to Dongan's
# npc.txt), Seoganland <-> Namgan <-> Przelecz Yilad <-> Wawoz (Owsap's 10127-10140); Wawoz <-> Schronienie go
# through Rozpadlina Dusz (the next step, MT2009_PLUS_YOHARA_MAPS4_V1). Groups: Owsap's group 6185-6192, 6711-6715,
# 9150-9157 / group_group 6706-6710, 6715-6719, 4030-4033, ours 9170-9175 / 4040-4041; drops
# mob_drop_item.yohara_maps2.txt (55 mobs; Wodz Wojenny Schronienia's Zamarzniety Klucz a "limit" group of its own -
# one a kill, the owner 14 October) and the new chests special_item_group.yohara_items2.txt
# (tools/yohara_items/gen_yitems2.py) - none may exist before. The jade ores are smelted by the guild alchemists
# (after MT2009_PLUS_JEWELS75_V1's step: the same lists). After the champion step (sungma_table.txt names all five:
# Sung Ma maps, no bot may enter) and before the belt materials' (which reads every drop group). Rows:
# mariadb/playerbot/yohara_maps2.sql, yohara_items2.sql.
COPY yohara_maps2/ /tmp/yohara-maps2-add/
RUN set -eu; L=/opt/metin2/share/locale/poland; A=/tmp/yohara-maps2-add \
 && find "$A" -type f -name '*.txt' -exec sed -i '1s/^\xEF\xBB\xBF//; s/\r$//; s/$/\r/' {} + \
 && for p in "376 metin2_map_eastplain_02 0c00000018000000 1152000 435200" "377 metin2_map_eastplain_03 1000000008000000 1228800 435200" \
             "385 metin2_map_snakevalley 180000000c000000 0 1408000" "388 metin2_map_icecrystalcave 1400000010000000 0 1510400" \
             "393 metin2_map_whitedragoncave_01 1800000018000000 998400 1203200"; do \
      set -- $p; \
      { rm -rf "$L/map/$2" && cp -a "$A/map/$2" "$L/map/" \
        && test "$(od -An -tx1 -N8 "$L/map/$2/server_attr" | tr -d ' \n')" = "$3" \
        && grep -q -E "^BasePosition[[:blank:]]+$4[[:blank:]]+$5" "$L/map/$2/Setting.txt" \
        && test -s "$L/map/$2/Town.txt" && test -s "$L/map/$2/npc.txt" && test -s "$L/map/$2/regen.txt" \
        && test -s "$L/map/$2/boss.txt" && test -f "$L/map/$2/stone.txt" \
        && grep -q -E "^$2[[:blank:]]" "$L/sungma_table.txt" \
        && { [ -z "$(tail -c 1 "$L/map/index")" ] || printf '\n' >> "$L/map/index"; } \
        && sed -i -E "/^$1[[:blank:]]/d" "$L/map/index" \
        && printf '%s %s\n' "$1" "$2" >> "$L/map/index" \
        && test "$(grep -c -E "^$1[[:blank:]]+$2[[:space:]]*\$" "$L/map/index")" = 1; } \
        || { echo "FATAL: Yohara map $1 $2"; exit 1; }; \
    done \
 && D="$L/map/metin2_map_eastplain_01/npc.txt" \
 && ! grep -q -E '[[:blank:]]10128[[:space:]]*$' "$D" \
 && { [ -z "$(tail -c 1 "$D")" ] || printf '\r\n' >> "$D"; } \
 && cat "$A/dongan_npc.yohara_maps2.txt" >> "$D" \
 && test "$(grep -c -E '^m[[:blank:]].*[[:blank:]]10128[[:space:]]*$' "$D")" = 1 \
 && f="$L/group.txt" \
 && ! grep -q -E '^[[:blank:]]*Vnum[[:blank:]]+(618[5-9]|619[0-2]|671[1-5]|915[0-7]|917[0-5])[[:space:]]*$' "$f" \
 && { [ -z "$(tail -c 1 "$f")" ] || printf '\n' >> "$f"; } \
 && cat "$A/group.yohara_maps2.txt" >> "$f" \
 && test "$(grep -c -E '^[[:blank:]]*Vnum[[:blank:]]+(618[5-9]|619[0-2]|671[1-5]|915[0-7]|917[0-5])[[:space:]]*$' "$f")" = 27 \
 && f="$L/group_group.txt" \
 && ! grep -q -E '^[[:blank:]]*Vnum[[:blank:]]+(670[6-9]|6710|671[5-9]|403[0-3]|404[01])[[:space:]]*$' "$f" \
 && { [ -z "$(tail -c 1 "$f")" ] || printf '\r\n' >> "$f"; } \
 && cat "$A/group_group.yohara_maps2.txt" >> "$f" \
 && test "$(grep -c -E '^[[:blank:]]*Vnum[[:blank:]]+(670[6-9]|6710|671[5-9]|403[0-3]|404[01])[[:space:]]*$' "$f")" = 16 \
 && F="$L/mob_drop_item.txt" \
 && ! grep -q -i -E '^[[:blank:]]*mob[[:blank:]]+(67(1[89]|2[0-9]|3[01]|5[89]|6[0-4]|7[0-6]|8[4-9])|68(7[5-9]|8[0-8])|806[3-6]|8077|862[67])([^0-9]|$)' "$F" \
 && { [ -z "$(tail -c 1 "$F")" ] || printf '\r\n' >> "$F"; } \
 && cat "$A/mob_drop_item.yohara_maps2.txt" >> "$F" \
 && test "$(grep -c -i -E '^[[:blank:]]*mob[[:blank:]]+(67(1[89]|2[0-9]|3[01]|5[89]|6[0-4]|7[0-6]|8[4-9])|68(7[5-9]|8[0-8])|806[3-6]|8077|862[67])([^0-9]|$)' "$F")" = 56 \
 && G="$L/special_item_group.txt" \
 && ! grep -q -E '^[[:blank:]]*Vnum[[:blank:]]+(31238|83065|83066|83067|50249)([^0-9]|$)' "$G" \
 && { [ -z "$(tail -c 1 "$G")" ] || printf '\r\n' >> "$G"; } \
 && cat "$A/special_item_group.yohara_items2.txt" >> "$G" \
 && test "$(grep -c -E '^[[:blank:]]*Vnum[[:blank:]]+(31238|83065|83066|83067|50249)([^0-9]|$)' "$G")" = 5 \
 && C="$L/quest/libs/crafting/crafting_data.lua" \
 && LC_ALL=C sed -i -E 's/^([[:blank:]]*\[20(06[0-9]|07[0-2])\] = \{50(62[1-9]|63[0-3]), 50635, 50636, 50637, 50638)\},(\r?)$/\1, 50661, 50662, 50663, 50664},\4/' "$C" \
 && test "$(LC_ALL=C grep -c -E '^[[:blank:]]*\[20(06[0-9]|07[0-2])\] = \{50(62[1-9]|63[0-3]), 50635, 50636, 50637, 50638, 50661, 50662, 50663, 50664\},' "$C")" -eq 12 \
 && for f in "$L/translate.lua" "$L/quest/libs/translate/translate.lua"; do \
      [ -f "$f" ] || continue; \
      LC_ALL=C grep -a -q 'map_names\[388\]' "$f" && continue; \
      { [ -z "$(tail -c 1 "$f")" ] || printf '\r\n' >> "$f"; }; \
      printf '\r\n-- MT2009_PLUS_YOHARA_MAPS2_V1\r\ntranslate.general.map_names[376] = "Seoganland"\r\ntranslate.general.map_names[377] = "Namgan"\r\ntranslate.general.map_names[385] = "Prze\263\352cz Yilad"\r\ntranslate.general.map_names[388] = "W\271w\363z P\363\263nocnego Wiatru"\r\ntranslate.general.map_names[393] = "Schronienie P\363\263nocnego Wiatru"\r\n' >> "$f"; \
    done \
 && S="$L/settings.lua" \
 && { LC_ALL=C grep -a -q 'add_goto_info("seoganland"' "$S" || printf 'add_goto_info("seoganland", 0, 376, 12218, 4895)\r\n' >> "$S"; } \
 && { LC_ALL=C grep -a -q 'add_goto_info("namgan"' "$S" || printf 'add_goto_info("namgan", 0, 377, 12780, 4411)\r\n' >> "$S"; } \
 && { LC_ALL=C grep -a -q 'add_goto_info("yilad"' "$S" || printf 'add_goto_info("yilad", 0, 385, 316, 14148)\r\n' >> "$S"; } \
 && { LC_ALL=C grep -a -q 'add_goto_info("wawoz"' "$S" || printf 'add_goto_info("wawoz", 0, 388, 1106, 15997)\r\n' >> "$S"; } \
 && { LC_ALL=C grep -a -q 'add_goto_info("schronienie"' "$S" || printf 'add_goto_info("schronienie", 0, 393, 10064, 12672)\r\n' >> "$S"; } \
 && rm -rf "$A" \
 && echo "share: Yohara - Seoganland (376), Namgan (377), Przelecz Yilad (385), Wawoz (388), Schronienie (393): GF terrain, spawns, groups, drops, chests, jade"
# MT2009_PLUS_YOHARA_MAPS4_V1 (share): Rozpadlina Dusz (389, metin2_map_whitdragonvalley, 3x3 at 128000 1510400 -
# Owsap's index; the owner, 14 October 2026, cache/yohara/decyzje.md "14.10 rano"; the pl-wiki) on the Yohara core
# (bin/m2-render-config MAPS_game3_all). Every file made by tools/yohara_maps4/gen_ymaps4.py (yohara_maps4/README.md):
# server_attr from GF 26.1.11's attr.atr, Ameria's bosses (8 spots, the wiki's four bosses, 1 h), Metins (two spots
# of each of its three rings, Shiho / Gumar, 30 min) and NPCs (= Owsap's = GF's points: Straznik Rozpad. Dusz,
# General Kohan, Lowca Glow, the portal 10143 to Wawoz), ours the regular monsters (Wawoz's method; groups 9190-9195,
# group_group 4042 lod / 4043 blyskawice), drops mob_drop_item.yohara_maps4.txt - none may exist before. The way as
# in the game, in place of the second batch's stand-in Wawoz <-> Schronienie (10145/10146, gone): Wawoz's portal
# 10142 (GF's point 235,267) and Schronienie's 10201 (GF's 19,640) from links.yohara_maps4.txt into those maps'
# npc.txt (after the second batch's step), General Kohan -> Schronienie (quest yohara_mapy4). sungma_table.txt has
# the map (35/25/35/40 - the wiki's): a Sung Ma map, no bot enters; sungma_mob_exp.txt the champion experience of
# all 14 monsters (checked). /goto rozpadlina. Rows:
# mariadb/playerbot/yohara_maps4.sql (+ yohara_maps4_zywioly.sql). MT2009_PLUS_YOHARA_ITEMS4_V1 (the owner's items
# of 14 October, tools/yohara_maps4/gen_yitems4.py, yohara_items4.sql): the chests special_item_group.yohara_items4.txt
# - Plat. Skrzynia Skarbow (83055; Przeb. Ksiega Zwierza 95737 has no group since MT2009_PLUS_GROWTH_PET_V1); the jade bracelets,
# Kamien Metin z Yohara and Mistrz Chi's crafting are quest yohara_mapy4 / server-patches/obreczjadeitu.
COPY yohara_maps4/ /tmp/yohara-maps4-add/
RUN set -eu; L=/opt/metin2/share/locale/poland; A=/tmp/yohara-maps4-add \
 && find "$A" -type f -name '*.txt' -exec sed -i '1s/^\xEF\xBB\xBF//; s/\r$//; s/$/\r/' {} + \
 && set -- 389 metin2_map_whitdragonvalley 0c0000000c000000 128000 1510400 \
 && { rm -rf "$L/map/$2" && cp -a "$A/map/$2" "$L/map/" \
      && test "$(od -An -tx1 -N8 "$L/map/$2/server_attr" | tr -d ' \n')" = "$3" \
      && grep -q -E "^BasePosition[[:blank:]]+$4[[:blank:]]+$5" "$L/map/$2/Setting.txt" \
      && test -s "$L/map/$2/Town.txt" && test -s "$L/map/$2/npc.txt" && test -s "$L/map/$2/regen.txt" \
      && test -s "$L/map/$2/boss.txt" && test -s "$L/map/$2/stone.txt" \
      && grep -q -E "^$2[[:blank:]]+35[[:blank:]]+25[[:blank:]]+35[[:blank:]]+40([[:blank:]]+[0-9]+)?[[:space:]]*\$" "$L/sungma_table.txt" \
      && { [ -z "$(tail -c 1 "$L/map/index")" ] || printf '\n' >> "$L/map/index"; } \
      && sed -i -E "/^$1[[:blank:]]/d" "$L/map/index" \
      && printf '%s %s\n' "$1" "$2" >> "$L/map/index" \
      && test "$(grep -c -E "^$1[[:blank:]]+$2[[:space:]]*\$" "$L/map/index")" = 1; } \
      || { echo "FATAL: Yohara map $1 $2"; exit 1; } \
 && for p in "388 metin2_map_icecrystalcave 10142 10145" "393 metin2_map_whitedragoncave_01 10201 10146"; do \
      set -- $p; N="$L/map/$2/npc.txt"; \
      { grep -q -E "^$1[[:blank:]]+$2[[:space:]]*\$" "$L/map/index" \
        && ! grep -q -E "[[:blank:]]($3|$4)[[:space:]]*\$" "$N" \
        && { [ -z "$(tail -c 1 "$N")" ] || printf '\r\n' >> "$N"; } \
        && grep -E "^$1[[:blank:]]" "$A/links.yohara_maps4.txt" | cut -f2- >> "$N" \
        && test "$(grep -c -E "^m[[:blank:]].*[[:blank:]]$3[[:space:]]*\$" "$N")" = 1; } \
        || { echo "FATAL: Rozpadlina Dusz link $3 on $2"; exit 1; }; \
    done \
 && f="$L/group.txt" \
 && ! grep -q -E '^[[:blank:]]*Vnum[[:blank:]]+919[0-5][[:space:]]*$' "$f" \
 && { [ -z "$(tail -c 1 "$f")" ] || printf '\r\n' >> "$f"; } \
 && cat "$A/group.yohara_maps4.txt" >> "$f" \
 && test "$(grep -c -E '^[[:blank:]]*Vnum[[:blank:]]+919[0-5][[:space:]]*$' "$f")" = 6 \
 && f="$L/group_group.txt" \
 && ! grep -q -E '^[[:blank:]]*Vnum[[:blank:]]+404[23][[:space:]]*$' "$f" \
 && { [ -z "$(tail -c 1 "$f")" ] || printf '\r\n' >> "$f"; } \
 && cat "$A/group_group.yohara_maps4.txt" >> "$f" \
 && test "$(grep -c -E '^[[:blank:]]*Vnum[[:blank:]]+404[23][[:space:]]*$' "$f")" = 2 \
 && F="$L/mob_drop_item.txt" \
 && MV='(677[7-9]|678[0-3]|6889|689[0-5])' \
 && ! grep -q -i -E "^[[:blank:]]*mob[[:blank:]]+$MV([^0-9]|\$)" "$F" \
 && { [ -z "$(tail -c 1 "$F")" ] || printf '\r\n' >> "$F"; } \
 && cat "$A/mob_drop_item.yohara_maps4.txt" >> "$F" \
 && test "$(grep -c -i -E "^[[:blank:]]*mob[[:blank:]]+$MV([^0-9]|\$)" "$F")" = 14 \
 && G="$L/special_item_group.txt" \
 && ! grep -q -E '^[[:blank:]]*Vnum[[:blank:]]+(83055|95737)([^0-9]|$)' "$G" \
 && { [ -z "$(tail -c 1 "$G")" ] || printf '\r\n' >> "$G"; } \
 && cat "$A/special_item_group.yohara_items4.txt" >> "$G" \
 && test "$(grep -c -E '^[[:blank:]]*Vnum[[:blank:]]+83055([^0-9]|$)' "$G")" = 1 \
 && E="$L/sungma_mob_exp.txt" \
 && test "$(grep -c -E '^(677[7-9]|678[0-3]|6889|689[0-5])[[:blank:]]+[0-9]+[[:space:]]*$' "$E")" = 14 \
 && for f in "$L/translate.lua" "$L/quest/libs/translate/translate.lua"; do \
      [ -f "$f" ] || continue; \
      LC_ALL=C grep -a -q 'map_names\[389\]' "$f" && continue; \
      { [ -z "$(tail -c 1 "$f")" ] || printf '\r\n' >> "$f"; }; \
      printf '\r\n-- MT2009_PLUS_YOHARA_MAPS4_V1\r\ntranslate.general.map_names[389] = "Rozpadlina Dusz"\r\n' >> "$f"; \
    done \
 && S="$L/settings.lua" \
 && { LC_ALL=C grep -a -q 'add_goto_info("rozpadlina"' "$S" || printf 'add_goto_info("rozpadlina", 0, 389, 1830, 15794)\r\n' >> "$S"; } \
 && rm -rf "$A" \
 && echo "share: Yohara - Rozpadlina Dusz (389): GF terrain, Ameria's bosses / Metins / NPCs, our monsters, groups, drops, the portals 10142 (Wawoz) / 10201 (Schronienie)"
# MT2009_PLUS_MAPS_WZ_V1 (share): Wezowe Pole (80, metin2_map_snakefield = the official metin2_map_WL_01, 4x4 at
# 1049600 716800 - the official index 69 is our Przelecz, metin2_map_wl_pass) and Kraina Gigantow (70,
# metin2_map_giantland = the official metin2_map_nusluck01, 2x2 at 819200 716800 - in place of the base share's
# "70 metin2_map_nusluck01" line) as the pl-wiki has them (the owner, 15 October 2026), on game2
# (bin/m2-render-config). Every file made by tools/maps_wz/gen_maps_wz.py (maps_wz/README.md): the official
# server_attr, spawns (group_group 1101-1104 / 1401 / 1402 / 1501-1504 and 1451-1453 of the base share, checked
# here), NPCs and Metins, Town = where a player comes in; the wiki's drops our groups lacked
# (mob_drop_item.maps_wz.txt, "drop" groups the reader merges with the mobs' own - Orkowa Maczuga 30194, Piasek
# Kwarcowy 30195 ...). The way in (the wiki): the desert's bottom-right portal - the base share's 10108 to Przelecz
# at 1477,1357 - becomes 10029 to Wezowe Pole (links.maps_wz.txt); Wezowe Pole's 10030 / 10032 lead to the desert /
# Kraina, Kraina's 10031 back. Przelecz is gone since (MT2009_PLUS_PASS69_OFF_V1 below). /goto sneak (it named 69), wezowe, giant (its
# map corner -> the arrival), gigantow. The monsters' levels: mariadb/playerbot/maps_wz.sql.
COPY maps_wz/ /tmp/maps-wz-add/
RUN set -eu; L=/opt/metin2/share/locale/poland; A=/tmp/maps-wz-add \
 && find "$A" -type f -name '*.txt' -exec sed -i '1s/^\xEF\xBB\xBF//; s/\r$//; s/$/\r/' {} + \
 && for v in 1101 1102 1103 1104 1401 1402 1451 1452 1453 1501 1502 1503 1504 20611; do \
      grep -q -E "^[[:blank:]]*Vnum[[:blank:]]+$v[[:space:]]*\$" "$L/group_group.txt" \
        || { echo "FATAL: group_group $v (Wezowe Pole / Kraina Gigantow) is not in group_group.txt"; exit 1; }; \
    done \
 && for m in "80 metin2_map_snakefield 1000000010000000 1049600 716800" "70 metin2_map_giantland 0800000008000000 819200 716800"; do \
      set -- $m; \
      { rm -rf "$L/map/$2" && cp -a "$A/map/$2" "$L/map/" \
        && test "$(od -An -tx1 -N8 "$L/map/$2/server_attr" | tr -d ' \n')" = "$3" \
        && grep -q -E "^BasePosition[[:blank:]]+$4[[:blank:]]+$5" "$L/map/$2/Setting.txt" \
        && test -s "$L/map/$2/Town.txt" && test -s "$L/map/$2/npc.txt" && test -s "$L/map/$2/regen.txt" \
        && { [ -z "$(tail -c 1 "$L/map/index")" ] || printf '\n' >> "$L/map/index"; } \
        && sed -i -E "/^$1[[:blank:]]/d" "$L/map/index" \
        && printf '%s %s\n' "$1" "$2" >> "$L/map/index" \
        && test "$(grep -c -E "^$1[[:blank:]]+$2[[:space:]]*\$" "$L/map/index")" = 1; } \
        || { echo "FATAL: map $1 $2"; exit 1; }; \
    done \
 && test -s "$L/map/metin2_map_giantland/stone.txt" \
 && N="$L/map/metin2_map_n_desert_01/npc.txt" \
 && W=$(grep -E '^63[[:blank:]]+metin2_map_n_desert_01[[:blank:]]' "$A/links.maps_wz.txt" | tr -d '\r') \
 && NEW=$(printf '%s\n' "$W" | cut -f3-13) && OLD=$(printf '%s\n' "$W" | cut -f14) \
 && test "$OLD" = 10108 && test "$(printf '%s\n' "$NEW" | cut -f11)" = 10029 \
 && test "$(grep -c -E "^m[[:blank:]].*[[:blank:]]$OLD[[:space:]]*\$" "$N")" = 1 \
 && ! grep -q -E "^m[[:blank:]].*[[:blank:]]10029[[:space:]]*\$" "$N" \
 && sed -i -E "/^m[[:blank:]].*[[:blank:]]$OLD[[:space:]]*\$/d" "$N" \
 && { [ -z "$(tail -c 1 "$N")" ] || printf '\r\n' >> "$N"; } \
 && printf '%s\r\n' "$NEW" >> "$N" \
 && test "$(grep -c -E "^m[[:blank:]].*[[:blank:]]10029[[:space:]]*\$" "$N")" = 1 \
 && F="$L/mob_drop_item.txt" \
 && ! grep -q -E '^Group[[:blank:]]+MT2009_maps_wz_' "$F" \
 && { [ -z "$(tail -c 1 "$F")" ] || printf '\r\n' >> "$F"; } \
 && cat "$A/mob_drop_item.maps_wz.txt" >> "$F" \
 && test "$(grep -c -E '^Group[[:blank:]]+MT2009_maps_wz_' "$F")" = 9 \
 && for f in "$L/translate.lua" "$L/quest/libs/translate/translate.lua"; do \
      [ -f "$f" ] || continue; \
      LC_ALL=C grep -a -q 'map_names\[80\]' "$f" && continue; \
      { [ -z "$(tail -c 1 "$f")" ] || printf '\r\n' >> "$f"; }; \
      printf '\r\n-- MT2009_PLUS_MAPS_WZ_V1\r\ntranslate.general.map_names[80] = "W\352\277owe Pole"\r\n' >> "$f"; \
    done \
 && S="$L/settings.lua" \
 && sed -i -E 's/^add_goto_info\("sneak", 0, 69, /add_goto_info("sneak", 0, 80, /; s/^add_goto_info\("giant", 0, 70, 8192, 7168\)/add_goto_info("giant", 0, 70, 8283, 7635)/' "$S" \
 && { LC_ALL=C grep -a -q 'add_goto_info("wezowe"' "$S" || printf 'add_goto_info("wezowe", 0, 80, 10590, 7262)\r\nadd_goto_info("gigantow", 0, 70, 8283, 7635)\r\n' >> "$S"; } \
 && ! LC_ALL=C grep -a -q -E '^add_goto_info\("sneak", 0, 69,' "$S" \
 && rm -rf "$A" \
 && echo "share: Wezowe Pole (80) and Kraina Gigantow (70): the official terrain / spawns / NPCs / Metins, the wiki's drops, the desert's portal 10029"
# MT2009_PLUS_PASS69_OFF_V1 (share): Przelecz (69, metin2_map_wl_pass) removed (the owner, 15 October 2026: "Przelecz 69
# usun"). No portal led there any more (the desert's 10108 became 10029 above; 10109 stood on the base share's
# metin2_map_nusluck01, which no index names since Kraina Gigantow is metin2_map_giantland). Out: its map/index line,
# its folder, its music line in settings.lua (its /goto sneak names 80 above), the map name (the step above no
# longer writes one) - bin/m2-render-config hosts it on no core, apply.sh moves whoever was saved there to Wezowe
# Pole's arrival once. Min-Sun (20402) lived only there - Labirynt (79), the Black Steel crafting and his shop: he
# stands on Pustynia Yongbi (63, game1 as Labirynt) at 1467,1365 now, 6 m south-west of where 10030 puts a player
# down and 12 m from the portal 10029 (GF's attr.atr: free 2 m round, walkable from the town - the old way to
# Przelecz); quest labirynth / black_steel_crafting (quest/, compiled above) return and warp to 1465,1360 beside him.
RUN set -eu; L=/opt/metin2/share/locale/poland \
 && sed -i -E '/^69[[:blank:]]/d' "$L/map/index" \
 && ! grep -q -E '^69[[:blank:]]' "$L/map/index" \
 && ! grep -q -E 'wl_pass' "$L/map/index" \
 && rm -rf "$L/map/metin2_map_wl_pass" \
 && S="$L/settings.lua" \
 && sed -i -E '/^add_bgm_info\(69,/d' "$S" \
 && ! LC_ALL=C grep -a -q -E '^add_bgm_info\(69,|^add_goto_info\("[^"]*", *0, *69,' "$S" \
 && N="$L/map/metin2_map_n_desert_01/npc.txt" \
 && ! grep -q -E '^m[[:blank:]].*[[:blank:]]20402[[:space:]]*$' "$N" \
 && { [ -z "$(tail -c 1 "$N")" ] || printf '\r\n' >> "$N"; } \
 && printf 'm\t1467\t1365\t0\t0\t0\t4\t1m\t100\t1\t20402\r\n' >> "$N" \
 && test "$(grep -c -E '^m[[:blank:]].*[[:blank:]]20402[[:space:]]*$' "$N")" = 1 \
 && echo "share: Przelecz (69) removed - Min-Sun (20402) on Pustynia Yongbi (63) at 1467,1365"

# MT2009_PLUS_YOHARA_MOTIONS_V1 (share): the server's motions of the Yohara monsters (the owner's test list of
# 14 October, item 7 - "GetMoveMotionSpeed: cannot find motion" for Myr, Troll Zolnierz and the rest): the core
# times moves and attacks by data/monster/<mob_proto folder>/motlist.txt and its .msa files. 105 folders the image
# had none of (Seoganland, Namgan, Yilad, Wawoz, Schronienie, Rozpadlina, Swiatynia Wezy, Krolestwo Zywiolow,
# Jaskinie Gnolli, Wieza Sung Mahi, the awakened bosses' / Iluzja / Szczelina monsters ...), Owsap's official files
# (tools/yohara_motions/gen_ymotions.py writes ymotions/: motlist.txt with two official slips fixed, the .msa).
# After every Yohara step; a folder there already is replaced by this one. The NPC historian walks in place (no
# Accumulation in its run.msa, as official).
COPY ymotions/ /tmp/ymotions-add/
RUN set -eu; A=/tmp/ymotions-add; D=/opt/metin2/share/data/monster \
 && mkdir -p "$D" \
 && n=0 && for m in "$A"/data/monster/*; do rm -rf "$D/$(basename "$m")"; cp -a "$m" "$D/"; n=$((n + 1)); done \
 && test "$n" = 105 \
 && for f in east_earth_knight east_earth_soldier2 east_earth_magic east_gnoll_soldier snakevalley_pawn smhtower_boss trent_soldier; do test -s "$D/$f/motlist.txt"; test -s "$D/$f/run.msa"; done \
 && test -z "$(for m in "$A"/data/monster/*/run.msa; do case "$m" in */historian/*) continue;; esac; grep -q -E '^Accumulation[[:blank:]]+[-0-9.]+[[:blank:]]+-[0-9]' "$m" || echo "$m"; done)" \
 && rm -rf "$A" \
 && echo "share: Yohara monster motions - $n folders (MT2009_PLUS_YOHARA_MOTIONS_V1)"

# MT2009_PLUS_BELT_MATS_V1 (the owner, 7 October): the belt materials drop. After every other
# mob_drop_item.txt append (dungeons, Arezzo, the drop edit), so it sees all of their groups:
#  * mob_drop_item.beltmats.append.txt - Beran-Setaou's gems (special group 951103, a drop group
#    joining his), limit groups adding the x3 of the gold parts (30518/30519/30522/30523) to the
#    twenty level 103-107 bosses (3090-3891) and x2 to the four Metins 8051/8052/8055/8056, and
#    the flame stones (30524 / 30525) from the fire (6005-6009) and ice (6105-6109) monsters. Those
#    mobs must not have a limit group yet (the reader keeps a mob's first);
#  * mob_drop_item.beltmats.awk - every kill group with a gold part or Niebieski Rzemyk (30550):
#    that item x3 at the same rate for the rest (weight x3, kill_drop lowered); and Wladca Ochao's
#    (6390) limit group gets Zlota Przedza and Zloty Hak at 25%.
# The gems in the chests: special_item_group.dungeons.txt (951103, Skrzynia Nemere), arezzo2
# (Skrzynia Dzungli), starter (Skrzynia Mroku 50254); the Razador / Nemere quests drop the
# flame stones to the killer's party (boss_drop).
COPY mob_drop_item.beltmats.append.txt mob_drop_item.beltmats.awk /tmp/beltmats/
RUN set -eu; F=/opt/metin2/share/locale/poland/mob_drop_item.txt; A=/tmp/beltmats \
 && ! grep -q -E '^Group[[:blank:]]+MT2009_beltmats_' "$F" \
 && M=$(sed -n 's/^[[:blank:]]*Mob[[:blank:]]\{1,\}\([0-9]\{1,\}\).*/\1/p' "$A/mob_drop_item.beltmats.append.txt" | grep -v -x 2493 | sort -u | tr '\n' ' ') \
 && awk -v mobs="$M" 'function chk() { if (t == "limit" && (m in W)) { print "FATAL: mob " m " already has a limit group" > "/dev/stderr"; bad = 1 } } BEGIN{n = split(mobs, a, " "); for (i = 1; i <= n; i++) W[a[i]] = 1} {sub(/\r$/, "")} /^[[:blank:]]*Group/{chk(); t = ""; m = ""} tolower($1)=="mob"{m=$2} tolower($1)=="type"{t=tolower($2)} END{chk(); exit bad}' "$F" \
 && sed -i 's/\r$//; s/$/\r/' "$A/mob_drop_item.beltmats.append.txt" \
 && { [ -z "$(tail -c 1 "$F")" ] || printf '\r\n' >> "$F"; } \
 && cat "$A/mob_drop_item.beltmats.append.txt" >> "$F" \
 && awk -v report="$A/report" -f "$A/mob_drop_item.beltmats.awk" "$F" > "$F.new" \
 && mv "$F.new" "$F" \
 && cat "$A/report" \
 && test "$(sed -n 's/^kill //p' "$A/report")" -ge 40 \
 && test "$(sed -n 's/^ochao //p' "$A/report")" = 1 \
 && test "$(grep -c -E '^Group[[:blank:]]+MT2009_beltmats_' "$F")" = 35 \
 && ! grep -q -E '^[[:blank:]]*kill_drop[[:blank:]]+0([^0-9]|$)' "$F" \
 && rm -rf "$A" \
 && echo "share: belt materials - Beran's gems, the gold parts x3, the flame stones (MT2009_PLUS_BELT_MATS_V1)"

# The Spider Baroness (port/shareify.py renders special_spawns.baroness.txt and
# this step): the level-75 boss who drops the Stalki, stood in the second
# Spider Dungeon's last room every four to five hours (the operator's decision
# of 28 September). The package spawns her nowhere; the damage multiplier her
# lair would give her is the engine's (playerbotify apply_spider_baroness_damage).
COPY special_spawns.baroness.txt /tmp/spawn-add/
RUN set -eu; S=/opt/metin2/share/locale/poland/special_spawns.txt; A=/tmp/spawn-add/special_spawns.baroness.txt \
 && ! grep -q -E '^[[:blank:]]*vnum[[:blank:]]+2092[[:space:]]*$' "$S" \
 && sed -i 's/\r$//; s/$/\r/' "$A" \
 && { [ -z "$(tail -c 1 "$S")" ] || printf '\r\n' >> "$S"; } \
 && cat "$A" >> "$S" \
 && rm -rf /tmp/spawn-add \
 && test "$(grep -c -E '^[[:blank:]]*spawn_vnum[[:blank:]]+2092[[:space:]]*$' "$S")" -eq 1 \
 && echo "share: the Spider Baroness spawns in the second Spider Dungeon"

# MT2009_PLUS_SPIDER3_V1: 3 Loch Pajakow (217, metin2_map_spiderdungeon_03) - an ordinary hunting map again, as
# the pl-wiki's "3 Loch Pajakow" (the owner, 28 October 2026), hosted by game1 beside V1 / V2 (bin/m2-render-config). The package
# has the whole map (Setting.txt 3x3 at 51200 563200, Town.txt 478 79, server_attr = GF 26.1.11's attr.atr cell for
# cell, regen.txt = Owsap's but seven groups, npc.txt: the Nagrobek 30130 at 178 489 and the warp 10097 at 483 79
# back to the second Spider Dungeon, 7040 5235); its monsters are the five Best. poison spiders 2071-2075 of 60-68
# in group_group 2701-2707 - no Metin, no ore, no boss (the wiki's). Two changes:
#  * MT2009_PLUS_SPIDER3_SWITCH_V1: all of it behind M2_SPIDER3_ON (.env, default 0 until the client with the map is
#    out): 0 - no core hosts 217 and the warp line below stays commented; 1 - game1 hosts it and m2-render-config
#    uncomments the warp at the container's start. The drops and spawns of 217's own monsters change nothing while
#    the map is not hosted;
#  * the way in: the second Spider Dungeon (71) gets the warp 10098 (mob_proto "... 984 5711" -> V3 at 472 79,
#    beside Town.txt) at 385 893 of its last room, as Owsap's npc.txt has it - the package left it out. Both ends
#    walkable in server_attr (9x9 cells free around them); no level check, the wiki's "od Lv. 1". Bots never take a
#    warp NPC (FuncCheckWarp skips them): the bots that did very well in V2 are moved in server-side
#    (MT2009_PLUS_SPIDER3_BOTS_V1);
#  * the wiki's "all monsters are NOT aggressive": the 35 "ga" spawns (aggressive groups) become "g".
# The drops are the package's limit groups (level_limit 60: the level-65 weapons +4, helmets, shields) and the
# global ones (MT2009_mglobal_2071..2075) - the wiki's "weapons and helmets from level 60". The poison stops at level
# 78 by itself: the engine's poison_level_adjust (char_resist.cpp) by the level difference to the spiders' 68.
RUN set -eu; L=/opt/metin2/share/locale/poland/map; V2="$L/metin2_map_spiderdungeon_02/npc.txt"; V3="$L/metin2_map_spiderdungeon_03" \
 && grep -q -E '^217[[:blank:]]+metin2_map_spiderdungeon_03[[:space:]]*$' "$L/index" \
 && ! grep -q -E '[[:blank:]]10098[[:space:]]*$' "$V2" \
 && { [ -z "$(tail -c 1 "$V2")" ] || printf '\r\n' >> "$V2"; } \
 && printf '// MT2009_PLUS_SPIDER3_V1: the warp to 3 Loch Pajakow (217) - commented while M2_SPIDER3_ON is 0 (bin/m2-render-config)\r\n//m\t385\t893\t0\t0\t0\t1\t1m\t100\t1\t10098\r\n' >> "$V2" \
 && test "$(grep -c -E '^//m[[:blank:]]+385[[:blank:]]+893[[:blank:]].*[[:blank:]]10098[[:space:]]*$' "$V2")" = 1 \
 && grep -q -E '^m[[:blank:]]+483[[:blank:]]+79[[:blank:]].*[[:blank:]]10097[[:space:]]*$' "$V3/npc.txt" \
 && test "$(grep -c -E '^ga[[:blank:]]' "$V3/regen.txt")" = 35 \
 && sed -i -E 's/^ga([[:blank:]])/g\1/' "$V3/regen.txt" \
 && ! grep -q -E '^[a-z]a[[:blank:]]' "$V3/regen.txt" \
 && test "$(grep -c -E '^[rg][[:blank:]]' "$V3/regen.txt")" -ge 660 \
 && echo "share: 3 Loch Pajakow (217) - the warp from the second Spider Dungeon, no aggressive spawns"

# MT2009_PLUS_DEMON_STONES_V1 (the owner, 14 October 2026; pl-wiki "Kamien Demonow", "Kamien Mocy", "Kamien Mocy
# Demonow"): Kamien Demonow +1 to +4 had no source. After every share append (the Yohara batches' groups are in):
# demonstones/mob_drop_item.demonstones.append.txt - the Yohara Metins +1/+2, the chiefs +1 to +3 (own groups,
# 18 mobs). Mistrz Chi makes Kamien Mocy Demonow +0..+4 (quest rekawice). The chests' grades (70411, 70412, 70429,
# Skrzynia Hydry 54705) come with the owner's sheet of 15 October 2026 since MT2009_PLUS_CHEST_DROPS_V1
# (tools/yohara_chestdrops) - the sheet's table is each chest's whole content, nothing is added to it here.
# The same file gives Krol Bao (6699) the wiki's Ksiega Precyzji (MT2009_PLUS_PRECISION_BOOK_DROP_V1).
COPY demonstones/ /tmp/demonstones/
RUN set -eu; L=/opt/metin2/share/locale/poland; A=/tmp/demonstones; F="$L/mob_drop_item.txt" \
 && ! grep -q -E '^Group[[:blank:]]+MT2009_demonstones_' "$F" \
 && sed -i 's/\r$//; s/$/\r/' "$A/mob_drop_item.demonstones.append.txt" \
 && { [ -z "$(tail -c 1 "$F")" ] || printf '\r\n' >> "$F"; } \
 && cat "$A/mob_drop_item.demonstones.append.txt" >> "$F" \
 && test "$(grep -c -E '^Group[[:blank:]]+MT2009_demonstones_' "$F")" = 18 \
 && test "$(grep -c -E '^Group[[:blank:]]+MT2009_precyzja_6699' "$F")" = 1 \
 && rm -rf "$A" \
 && echo "share: Kamien Demonow +1..+4 - Metins, chiefs (MT2009_PLUS_DEMON_STONES_V1)"

# MT2009_PLUS_JADE_JEWELLERY_V1 (the owner, 14 October 2026): the jade necklaces / earrings / bracelets +0 in the
# chests the wiki names (83052, 83053, 31256, 50528) - since MT2009_PLUS_CHEST_DROPS_V1 (the owner's sheet of 15 October
# 2026, tools/yohara_chestdrops) they are rows of those chests' own groups, no step adds them here any more. Mistrz Chi
# makes all twelve (quest yohara_mapy4).

# The cores run unprivileged and read this tree by path; a directory only root
# can enter costs every quest below it, silently. Repair, then assert.
RUN set -eu; \
    find /opt/metin2/share -type d ! -perm -005 -exec chmod a+rx {} + ; \
    find /opt/metin2/share -type f ! -perm -004 -exec chmod a+r  {} + ; \
    bad="$(find /opt/metin2/share \( -type d ! -perm -005 \) -o \( -type f ! -perm -004 \) | head -5)"; \
    if [ -n "$bad" ]; then \
      echo "FATAL: still not readable by the server account:"; echo "$bad"; exit 1; \
    fi; \
    echo "share tree is readable by the server account"

# MT2009_PLUS_HALLOWEEN_V1: the package's own event_halloween_hair (quest/events/halloween) is
# replaced by Owsap's port compiled above. Its handlers go first - the login/enter spawn of
# Jack Pumpkin (the event manager stands him now) and the masks' "use" handlers, which call
# affect.add_hair, a function this engine does not have - so none of them outlives the copy.
RUN set -eu; O=/opt/metin2/share/locale/poland/quest/object \
 && n=$(find "$O" -path "$O/state" -prune -o -type f -name 'event_halloween_hair.*' -print | wc -l) \
 && find "$O" -path "$O/state" -prune -o -type f -name 'event_halloween_hair.*' -exec rm -f {} + \
 && ! find "$O" -path "$O/state" -prune -o -type f -name 'event_halloween_hair.*' -print | grep -q . \
 && echo "share: the package's event_halloween_hair handlers removed ($n)"

# The three quests compiled in the quests stage, as a pure addition on top of
# the package's own object tree (new files under quest/object/, the sources
# beside the stock ones). Empty when web_admin.quest was left out.
# MT2009_PLUS_YOHARA_MAPS3_V1 (links): the ways into the third batch from the maps of the second (claude/yohara-maps2:
# Schronienie Polnocnego Wiatru 393, Przelecz Yilad 385, Namgan 377) - after every share step, so whatever order the
# batches' steps take. Each map that is in map/index gets its official point if it lacks it (GF's _point.txt):
# 10202 (Schronienie 1358,1467 -> Zejscie), Straznik Wezy 20804 (Yilad 637,494 -> 1. poziom Swiatyni Wezy, quest
# yohara_mapy3), Tajemniczy Oltarz 20850 (Namgan 960,242 -> Tajemnicza Instancja); a map not in map/index yet is
# only reported (its batch is not merged).
RUN set -eu; L=/opt/metin2/share/locale/poland \
 && for p in "393 metin2_map_whitedragoncave_01 1358 1467 1 10202" "385 metin2_map_snakevalley 637 494 1 20804" \
             "377 metin2_map_eastplain_03 960 242 1 20850"; do \
      set -- $p; \
      if ! grep -q -E "^$1[[:blank:]]+$2[[:space:]]*\$" "$L/map/index"; then \
        echo "links: map $1 $2 is not in map/index - its point ($6) waits for that batch"; continue; \
      fi; \
      N="$L/map/$2/npc.txt"; test -f "$N" || : > "$N"; \
      if ! grep -q -E "[[:blank:]]$6[[:space:]]*\$" "$N"; then \
        { [ -z "$(tail -c 1 "$N")" ] || printf '\r\n' >> "$N"; }; \
        printf 'm\t%s\t%s\t0\t0\t0\t%s\t1m\t100\t1\t%s\r\n' "$3" "$4" "$5" "$6" >> "$N"; \
      fi; \
      test "$(grep -c -E "[[:blank:]]$6[[:space:]]*\$" "$N")" -ge 1 || { echo "FATAL: link $6 on $2"; exit 1; }; \
    done \
 && echo "links: Yohara maps 3 (Schronienie -> Zejscie, Yilad -> Swiatynia Wezy, Namgan -> Tajemnicza Instancja)"
# MT2009_PLUS_YOHARA_DUNG4_V1 (links): the way into Wieza Sung Mahi from Seoganland (376, claude/yohara-maps2) - after
# every share step, as the third batch's links. Wejscie Piekielnej Wiezy (4019) on GF's point (76,1459) -> the hall
# (quest wieza_sung_mahi); Halabardnik (20836, Dongan's own npc.txt) leads to Jaskinie Gnolli (quest jaskinie_gnolli).
# A map not in map/index yet is only reported.
RUN set -eu; L=/opt/metin2/share/locale/poland \
 && for p in "376 metin2_map_eastplain_02 76 1459 1 4019" "373 metin2_map_eastplain_01 990 973 7 20836"; do \
      set -- $p; \
      if ! grep -q -E "^$1[[:blank:]]+$2[[:space:]]*\$" "$L/map/index"; then \
        echo "links: map $1 $2 is not in map/index - its point ($6) waits for that batch"; continue; \
      fi; \
      N="$L/map/$2/npc.txt"; test -f "$N" || : > "$N"; \
      if ! grep -q -E "[[:blank:]]$6[[:space:]]*\$" "$N"; then \
        { [ -z "$(tail -c 1 "$N")" ] || printf '\r\n' >> "$N"; }; \
        printf 'm\t%s\t%s\t0\t0\t0\t%s\t1m\t100\t1\t%s\r\n' "$3" "$4" "$5" "$6" >> "$N"; \
      fi; \
      test "$(grep -c -E "[[:blank:]]$6[[:space:]]*\$" "$N")" -ge 1 || { echo "FATAL: link $6 on $2"; exit 1; }; \
    done \
 && echo "links: Yohara dung4 (Seoganland -> Wieza Sung Mahi, Dongan -> Jaskinie Gnolli)"
# MT2009_PLUS_YOHARA_LOKACJE_V1: every spawn point of the owner's spreadsheet of 20 October 2026 (Yohara monster
# locations = GF's map_mob_list.txt) a spawn of that monster did not reach (40 m) gets one - tools/yohara_lokacje/
# gen_ylokacje.py made yohara_lokacje/ (gen_report.txt: what, where). After every Yohara map step: each
# map/<folder>/<file>.lokacje.txt is appended to that map's <file> (regen.txt, boss.txt, stone.txt); a map not in
# map/index yet is only reported. Groups 9400-9439 (one boss each) and group_groups 4060-4069 (one boss of those the
# sheet puts at one point, "r" lines of boss.txt) - none may exist before. MT2009_PLUS_YOHARA_LOKACJE_V2 (the owner,
# 20 October): Yilad/Wawoz/Rozpadlina bosses and Metins only the sheet's (their batches write none), and
# special_spawns.yohara_lokacje.txt: Wodz Wojenny Schronienia (6789) three at a time on 3 random of its 12 sheet
# points (SpecialSpawn: a free point drawn per spawn, 1 h after a kill) - appended to special_spawns.txt.
COPY yohara_lokacje/ /tmp/yohara-lokacje-add/
RUN set -eu; L=/opt/metin2/share/locale/poland; A=/tmp/yohara-lokacje-add \
 && find "$A" -type f -name '*.txt' -exec sed -i '1s/^\xEF\xBB\xBF//; s/\r$//; s/$/\r/' {} + \
 && f="$L/group.txt" \
 && ! grep -q -E '^[[:blank:]]*Vnum[[:blank:]]+94[0-3][0-9][[:space:]]*$' "$f" \
 && { [ -z "$(tail -c 1 "$f")" ] || printf '\r\n' >> "$f"; } \
 && cat "$A/group.yohara_lokacje.txt" >> "$f" \
 && test "$(grep -c -E '^[[:blank:]]*Vnum[[:blank:]]+94[0-3][0-9][[:space:]]*$' "$f")" = "$(grep -c -E '^[[:blank:]]*Vnum' "$A/group.yohara_lokacje.txt")" \
 && f="$L/group_group.txt" \
 && ! grep -q -E '^[[:blank:]]*Vnum[[:blank:]]+406[0-9][[:space:]]*$' "$f" \
 && { [ -z "$(tail -c 1 "$f")" ] || printf '\r\n' >> "$f"; } \
 && cat "$A/group_group.yohara_lokacje.txt" >> "$f" \
 && test "$(grep -c -E '^[[:blank:]]*Vnum[[:blank:]]+406[0-9][[:space:]]*$' "$f")" = "$(grep -c -E '^[[:blank:]]*Vnum' "$A/group_group.yohara_lokacje.txt")" \
 && for d in "$A"/map/*/; do \
      m="$(basename "$d")"; \
      if ! grep -q -E "^[0-9]+[[:blank:]]+$m[[:space:]]*\$" "$L/map/index"; then \
        echo "lokacje: map $m is not in map/index - its points wait for that batch"; continue; \
      fi; \
      for s in "$d"*.lokacje.txt; do \
        T="$L/map/$m/$(basename "$s" .lokacje.txt).txt"; test -f "$T" || : > "$T"; \
        n0="$(grep -c -E '^[mgrs][[:blank:]]' "$T" || true)"; \
        { [ -z "$(tail -c 1 "$T")" ] || printf '\r\n' >> "$T"; }; \
        cat "$s" >> "$T"; \
        test "$(grep -c -E '^[mgrs][[:blank:]]' "$T")" = "$((n0 + $(grep -c -E '^[mgrs][[:blank:]]' "$s")))" \
          || { echo "FATAL: lokacje $s"; exit 1; }; \
      done; \
    done \
 && S="$L/special_spawns.txt" \
 && ! grep -q -E '^[[:blank:]]*vnum[[:blank:]]+6789[[:space:]]*$' "$S" \
 && { [ -z "$(tail -c 1 "$S")" ] || printf '\r\n' >> "$S"; } \
 && cat "$A/special_spawns.yohara_lokacje.txt" >> "$S" \
 && test "$(grep -c -E '^[[:blank:]]*spawn_vnum[[:blank:]]+6789[[:space:]]*$' "$S")" -eq 1 \
 && echo "lokacje: Yohara spawn points of the spreadsheet added ($(cat "$A"/map/*/*.lokacje.txt | wc -l) lines; Wodz Wojenny Schronienia 3 of 12 points)"

# MT2009_PLUS_MOBY_ARKUSZ_V1: the drops of the owner's sheet of 20 October 2026 (Metin2_Moby_statystyki_EXP_i_drop.xlsx)
# our Yohara monsters lacked - mob_drop_item.yohara_arkusz.txt (tools/ymoby_arkusz/gen_ymoby_arkusz.py, yohara_arkusz/
# README.md): groups MT2009_yarkusz_<mob> of Type drop, which the engine adds to the monster's own groups. After every
# Yohara share step (their monsters' groups are in already); none may exist before. Every item and monster is in the
# world of the Yohara SQL files (apply.sh).
COPY yohara_arkusz/ /tmp/yohara-arkusz-add/
RUN set -eu; L=/opt/metin2/share/locale/poland; A=/tmp/yohara-arkusz-add \
 && F="$L/mob_drop_item.txt" \
 && sed -i '1s/^\xEF\xBB\xBF//; s/\r$//; s/$/\r/' "$A/mob_drop_item.yohara_arkusz.txt" \
 && n="$(grep -c -E '^Group[[:blank:]]+MT2009_yarkusz_' "$A/mob_drop_item.yohara_arkusz.txt")" \
 && ! grep -q -E '^Group[[:blank:]]+MT2009_yarkusz_' "$F" \
 && { [ -z "$(tail -c 1 "$F")" ] || printf '\r\n' >> "$F"; } \
 && cat "$A/mob_drop_item.yohara_arkusz.txt" >> "$F" \
 && test "$(grep -c -E '^Group[[:blank:]]+MT2009_yarkusz_' "$F")" = "$n" \
 && rm -rf "$A" \
 && echo "share: Yohara monsters' drops of the owner's sheet ($n groups)"
# MT2009_PLUS_MOBY_GLOBAL_V1: the monsters before Yohara drop as the owner's sheet of 20 October 2026 lists
# (tools/ymoby_arkusz/gen_moby_global.py, moby_global/README.md): the package's rows the sheet does not list are cut
# (mob_drop_item.moby_global.remove.txt - exactly those rows, in that monster's groups that are not ours, the group
# numbered again, a group left empty dropped; every listed row must be found) and the sheet's items we lacked are
# appended (groups MT2009_mglobal_<mob>, Type drop). Our own groups and rows, the special groups and a quest's items stay.
COPY moby_global/ /tmp/moby-global-add/
RUN set -eu; L=/opt/metin2/share/locale/poland; A=/tmp/moby-global-add; F="$L/mob_drop_item.txt" \
 && awk -v R="$A/mob_drop_item.moby_global.remove.txt" -f "$A/cut_rows.awk" "$F" > "$F.new" \
 && mv "$F.new" "$F" \
 && sed -i '1s/^\xEF\xBB\xBF//; s/\r$//; s/$/\r/' "$A/mob_drop_item.moby_global.txt" \
 && n="$(grep -c -E '^Group[[:blank:]]+MT2009_mglobal_' "$A/mob_drop_item.moby_global.txt")" \
 && ! grep -q -E '^Group[[:blank:]]+MT2009_mglobal_' "$F" \
 && { [ -z "$(tail -c 1 "$F")" ] || printf '\r\n' >> "$F"; } \
 && cat "$A/mob_drop_item.moby_global.txt" >> "$F" \
 && test "$(grep -c -E '^Group[[:blank:]]+MT2009_mglobal_' "$F")" = "$n" \
 && rm -rf "$A" \
 && echo "share: monsters before Yohara - the sheet's drops ($n groups added)"
# MT2009_PLUS_BUFFI_STONE_DROP_V1: Kamien Duchowy Buffi (61031) from every Metin and boss of Zaklety Las (353) and of
# every map above it, the whole of Yohara too (the owner, 21 October 2026) - mob_drop_item.buffi_stone.txt
# (tools/ymoby_arkusz/gen_buffi_stone.py): groups MT2009_buffistone_<mob> of Type drop, which the engine adds to the
# monster's own groups; none may exist before. The item is mariadb/playerbot/buffi.sql's (apply.sh).
COPY buffi_stone/ /tmp/buffi-stone-add/
RUN set -eu; L=/opt/metin2/share/locale/poland; A=/tmp/buffi-stone-add; F="$L/mob_drop_item.txt" \
 && sed -i '1s/^\xEF\xBB\xBF//; s/\r$//; s/$/\r/' "$A/mob_drop_item.buffi_stone.txt" \
 && n="$(grep -c -E '^Group[[:blank:]]+MT2009_buffistone_' "$A/mob_drop_item.buffi_stone.txt")" \
 && ! grep -q -E '^Group[[:blank:]]+MT2009_buffistone_' "$F" \
 && { [ -z "$(tail -c 1 "$F")" ] || printf '\r\n' >> "$F"; } \
 && cat "$A/mob_drop_item.buffi_stone.txt" >> "$F" \
 && test "$(grep -c -E '^Group[[:blank:]]+MT2009_buffistone_' "$F")" = "$n" \
 && rm -rf "$A" \
 && echo "share: Kamien Duchowy Buffi from the Metins and bosses of Zaklety Las and above ($n groups)"
# MT2009_PLUS_NO_ROTTEN_CHEST_V1: Sprochniala Skrzynia (50124) drops from nothing any more (the owner, 15 October
# 2026, fix 7) - after every share step, so no append brings it back. The Yohara files (tools/yohara_items, yohara_maps3,
# yohara_pb, yohara_iluzja, yohara_chestdrops) and special_item_group.dungeons.txt (54700) no longer have it; this
# takes the package's rows too: the ice monsters 1131-1137, the Setaou 2401-2403, Beran-Setaou's 0% rows
# (MT2009_PLUS_DRAGON_NO_ROTTEN_CHEST_V1) and the Zelazna Skrzynia's group (50122). The loaders stop at the first
# missing number (item_manager_read_tables.cpp, k = 1, 2, ...), so a group that lost a row is numbered again; the chest's
# own group (Vnum 50124) stays - a chest someone already has still opens.
RUN set -eu; L=/opt/metin2/share/locale/poland \
 && for F in "$L/mob_drop_item.txt" "$L/special_item_group.txt"; do \
      awk -v v=50124 ' \
        /^[[:blank:]]*Group([[:blank:]]|$)/ { k = 0; gone = 0; print; next } \
        /^[[:blank:]]*}/ { if (gone && k == 0) { print "FATAL: a group of nothing but 50124" > "/dev/stderr"; bad = 1 } gone = 0; print; next } \
        $1 ~ /^[0-9]+$/ && NF >= 3 { \
          if ($2 == v) { cut++; gone = 1; next } \
          k++; \
          if (gone) { match($0, /^[[:blank:]]*[0-9]+/); lead = substr($0, 1, RLENGTH); sub(/[0-9]+$/, "", lead); $0 = lead k substr($0, RLENGTH + 1) } \
          print; next } \
        { print } \
        END { printf "share: %d row(s) of 50124 cut\n", cut > "/dev/stderr"; if (bad) exit 1 }' "$F" > "$F.new"; \
      mv "$F.new" "$F"; \
      test "$(awk '$1 ~ /^[0-9]+$/ && $2 == "50124"' "$F" | wc -l)" = 0 || { echo "FATAL: 50124 left in $F"; exit 1; }; \
    done
# MT2009_PLUS_WORLDBOSS_V1: Boss Swiata (playerbot_worldboss.h) - the bosses, their men, the maps' spots, the loot
# tiers and the season's prizes the game reads from its locale (worldboss.txt), and Skrzynka Tajemnic's contents (38015,
# special_item_group.worldboss.txt; appended once). Both GENERATED by tools/worldboss/gen_worldboss.py; the monsters,
# items and tables are mariadb/playerbot/worldboss.sql.
COPY worldboss/ /tmp/worldboss-add/
RUN set -eu; A=/tmp/worldboss-add; L=/opt/metin2/share/locale/poland; f=$L/special_item_group.txt \
 && cp "$A/worldboss.txt" "$L/worldboss.txt" \
 && test "$(grep -c '^boss' "$L/worldboss.txt")" = 6 \
 && a="$A/special_item_group.worldboss.txt" \
 && sed -i '1s/^\xEF\xBB\xBF//; s/\r$//; s/$/\r/' "$a" \
 && if ! grep -q -E '^[[:blank:]]*Vnum[[:blank:]]+38015([^0-9]|$)' "$f"; then \
      { [ -z "$(tail -c 1 "$f")" ] || printf '\r\n' >> "$f"; }; cat "$a" >> "$f"; \
    fi \
 && test "$(grep -c -E '^[[:blank:]]*Vnum[[:blank:]]+38015([^0-9]|$)' "$f")" = 1 \
 && rm -rf "$A" \
 && echo "share: Boss Swiata - worldboss.txt and Skrzynka Tajemnic (38015)"

# MT2009_PLUS_SPIDER3_DROPS_V2 (the owner, 28 October 2026): the five Best. poison spiders of 3 Loch Pajakow (2071-2075)
# drop the weapons and shields of their pl-wiki pages and the helmets of the package's old groups, from level 60, no
# level-65 weapons - spider3/mob_drop_item.spider3.txt, one limit group a monster. After every share append: each group
# of theirs (the package's limit groups of level 60 - the weapons of 45-60 at +4, helmets, shields - and moby_global's
# MT2009_mglobal_2071..2075) is taken out whole, then ours go in (a monster has one limit group: the engine keeps the first).
COPY spider3/ /tmp/spider3-add/
RUN set -eu; L=/opt/metin2/share/locale/poland; A=/tmp/spider3-add; F="$L/mob_drop_item.txt" \
 && ! grep -q -E '^Group[[:blank:]]+MT2009_spider3_' "$F" \
 && awk ' \
      function flush(   i) { if (keep) for (i = 1; i <= nb; i++) print B[i]; else cut++; nb = 0; ing = 0 } \
      /^Group([[:blank:]]|$)/ { if (ing) flush(); ing = 1; keep = 1; nb = 0 } \
      ing { B[++nb] = $0; t = $0; sub(/\r$/, "", t); split(t, f); if (tolower(f[1]) == "mob" && f[2] + 0 >= 2071 && f[2] + 0 <= 2075) keep = 0; if (t ~ /^}/) flush(); next } \
      { print } \
      END { if (ing) flush(); printf "share: %d group(s) of 2071-2075 cut\n", cut > "/dev/stderr"; if (cut < 10) exit 1 }' "$F" > "$F.new" \
 && mv "$F.new" "$F" \
 && ! awk '{ t = $0; sub(/\r$/, "", t); split(t, f); if (tolower(f[1]) == "mob" && f[2] + 0 >= 2071 && f[2] + 0 <= 2075) n++ } END { exit n ? 0 : 1 }' "$F" \
 && sed -i '1s/^\xEF\xBB\xBF//; s/\r$//; s/$/\r/' "$A/mob_drop_item.spider3.txt" \
 && { [ -z "$(tail -c 1 "$F")" ] || printf '\r\n' >> "$F"; } \
 && cat "$A/mob_drop_item.spider3.txt" >> "$F" \
 && test "$(grep -c -E '^Group[[:blank:]]+MT2009_spider3_207[1-5][[:space:]]*$' "$F")" = 5 \
 && rm -rf "$A" \
 && echo "share: 3 Loch Pajakow - the five spiders' drops (5 limit groups of level 60)"

# MT2009_PLUS_DROP307_V1 (the owner's list of 3 November 2026, Yohara 3.x section C) - after every share append:
#  * drop307/drop307.awk over mob_drop_item.txt and special_item_group.txt: Lza Bogini (70012), Plaszcz Uciekiniera
#    (70048), Symbol / Rekawica Krola Przepowiedni (70050 / 70051) drop from no monster, Metin, boss nor boss / dungeon
#    chest any more (the event's and the Biologist's boxes keep them; the fishing too); Krol Bao (misja) (6692) loses
#    every drop group (the pl-wiki: no drop; server-patches/drop307 takes the world's extras and the preview); the
#    bosses' and the boss chests' Kamien Kowala / Magiczny Metal are the tradeable 39015 / 39016 (mariadb drop307.sql);
#  * drop307/mob_drop_item.drop307.txt: the 90+ maps' and the Sung Ma field maps' bosses (39 groups) - Pozwolenie na
#    Zaczarowanie x2 15%, Pozwolenie na Wzmocnienie x2 8%, Magiczny Metal 5%; the champion maps' also Cor Draconis
#    (szlif.) x2 50% and Blogoslawienstwo Przedmiotu 5%;
#  * fishing_drop.lua: the fishing's Kamien Kowala / Magiczny Metal are 39015 / 39016;
#  * crafting_data.lua: Kowal's window (CRAFTING_BLACKSMITH) lists recipes 7-10 (world.crafting_proto, drop307.sql) -
#    the tradeable 39015 / 39016 make the same Podrecznik Kowala / Zwoj Boga Smokow as 71025 / 71026.
COPY drop307/ /tmp/drop307/
RUN set -eu; L=/opt/metin2/share/locale/poland; A=/tmp/drop307; F="$L/mob_drop_item.txt" \
 && ! grep -q -E '^Group[[:blank:]]+MT2009_drop307_' "$F" \
 && awk -v kind=mob -f "$A/drop307.awk" "$F" > "$F.new" && mv "$F.new" "$F" \
 && awk -v kind=sig -f "$A/drop307.awk" "$L/special_item_group.txt" > "$L/special_item_group.txt.new" \
 && mv "$L/special_item_group.txt.new" "$L/special_item_group.txt" \
 && sed -i '1s/^\xEF\xBB\xBF//; s/\r$//; s/$/\r/' "$A/mob_drop_item.drop307.txt" \
 && { [ -z "$(tail -c 1 "$F")" ] || printf '\r\n' >> "$F"; } \
 && cat "$A/mob_drop_item.drop307.txt" >> "$F" \
 && test "$(grep -c -E '^Group[[:blank:]]+MT2009_drop307_[0-9]+[[:space:]]*$' "$F")" = 39 \
 && ! awk '{ t = $0; sub(/\r$/, "", t); split(t, f); if (tolower(f[1]) == "mob" && f[2] == "6692") n++ } END { exit n ? 0 : 1 }' "$F" \
 && ! awk '{ t = $0; sub(/\r$/, "", t); split(t, f); if (f[1] ~ /^[0-9]+$/ && (f[2] == "70012" || f[2] == "70048" || f[2] == "70050" || f[2] == "70051")) n++ } END { exit n ? 0 : 1 }' "$F" \
 && G="$L/quest/libs/fishing/fishing_drop.lua" \
 && sed -i -E 's/^([[:blank:]]*)71025(,[[:blank:]]*1,)/\139015\2/; s/^([[:blank:]]*)71026(,[[:blank:]]*1,)/\139016\2/' "$G" \
 && ! grep -q -E '^[[:blank:]]*710(25|26),' "$G" \
 && test "$(grep -c -E '^[[:blank:]]*3901[56],' "$G")" -ge 2 \
 && C="$L/quest/libs/crafting/crafting_data.lua" \
 && sed -i -E 's/^([[:blank:]]*)1,2,3,4,5,6([[:blank:]]*\r?)$/\11,2,3,4,5,6,7,8,9,10\2/' "$C" \
 && test "$(grep -c -E '^[[:blank:]]*1,2,3,4,5,6,7,8,9,10[[:space:]]*$' "$C")" -eq 1 \
 && rm -rf "$A" \
 && echo "share: drop 3.0.7 - no Lza Bogini / Plaszcz / Krol Przepowiedni drops, Krol Bao (misja) without drop, the 90+ and champion bosses' rows, tradeable smith materials (MT2009_PLUS_DROP307_V1)"

# MT2009_PLUS_ZWOJ_SKARBU_OFF_V1 (the owner, 3 November 2026): Zwoj Skarbu (Stopien A) 70434 drops nowhere - it leads to
# Swiatynia Enigma, which this world does not have; the item itself stays as the wiki has it (no stacking, 3 days). Every
# "drop" row of it in mob_drop_item.txt (the Yohara maps' and dungeons' groups) gets chance 0, so the groups' numbering
# stays. Checked: no row of 70434 with a chance above 0 is left.
RUN set -eu; F=/opt/metin2/share/locale/poland/mob_drop_item.txt \
 && awk 'BEGIN{OFS="\t"} { line=$0; sub(/\r$/, "", line); n=split(line, f, /[\t]+/); if (n >= 5 && f[3] == "70434") { f[5] = "0"; out=f[1]; for (k=2; k<=n; k++) out=out "\t" f[k]; print out "\r"; c++ } else print $0 } END { print c+0 > "/tmp/zwoj.count" }' "$F" > "$F.new" \
 && mv "$F.new" "$F" \
 && echo "share: Zwoj Skarbu 70434 off in $(cat /tmp/zwoj.count) drop rows" && rm -f /tmp/zwoj.count

# MT2009_PLUS_ARMOR105_V1 (the owner, 22 October 2026): the level-105 armours' materials (tools/zbroje105) drop from
# our generators' files, appended by their own steps above - the owner's monster sheet (yohara_arkusz: the En-Tai,
# moby_global: the Ochao), the pl-wiki's lists (yohara_zaklety: Bojownik En-Tai, Bagjanamu, Jotun Thrym) and the chests
# (tools/yohara_chestdrops: Razador / Nemere in special_item_group.dungeons.txt, Jotun Thrym / Bagjanamu in
# yohara_zaklety, worldboss's Skrzynka Tajemnic) - the package's mob_drop_item / special_item_group.zbroje105.txt are not
# needed.
COPY --from=quests /out-quest/ /opt/metin2/share/locale/

# MT2009_PLUS_FISHING_GLOBAL_V1 (share; the owner, 4 November 2026 - cache/yohara/decyzje-lowienie-mikstury.md "Lowienie"):
# fishing as on the global server (server-patches/fishglobal, mariadb/playerbot/yohara_lowienie.sql):
#  * lowienie/fishing.lua and fishing_drop.lua replace the package's quest/libs/fishing ones (after every earlier edit
#    of them above - ours have no 71282 and the tradeable 39015 / 39016): rods +1..+20 and Wedka Weglowa (22), the
#    wiki's minimum rod a fish, the rare fish only with Rybie Wnetrznosci or the golden tuna's bonus, Zloty Tunczyk once
#    a day, the Rybak's upgrade dialog; bin/m2-fishing / the Seban panel edit the table's lines;
#  * the package's quest fisher loses its take handler (9009/take/fisher.start - the refine window's recipe talk):
#    rybak_wedki takes every rod now; its shop and chat stay;
#  * special_item_group.lowienie.txt - Skrzynia Nimfy Wodnej 27625 (Klucz Nimfy Wodnej opens it), appended once;
#  * cube.lowienie.txt - Wedka Weglowa at the Rybak (9009), appended once.
COPY lowienie/ /tmp/lowienie/
RUN set -eu; L=/opt/metin2/share/locale/poland; A=/tmp/lowienie; F="$L/quest/libs/fishing" \
 && test -f "$F/fishing_drop.lua" && test -f "$F/fishing.lua" \
 && cp "$A/fishing_drop.lua" "$F/fishing_drop.lua" && cp "$A/fishing.lua" "$F/fishing.lua" \
 && sed -i 's/\r$//' "$F/fishing_drop.lua" "$F/fishing.lua" \
 && grep -q 'MT2009_PLUS_FISHING_GLOBAL_V1' "$F/fishing_drop.lua" \
 && ! grep -Eq '^[[:blank:]]*71282,' "$F/fishing_drop.lua" \
 && test "$(grep -c -E '^[[:blank:]]*3901[56],' "$F/fishing_drop.lua")" -eq 2 \
 && O="$L/quest/object" && rm -f "$O/9009/take/fisher.start" \
 && test -s "$O/9009/take/rybak_wedki.start" && test "$(ls "$O/9009/take" | wc -l)" -eq 1 \
 && S="$L/special_item_group.txt" && a="$A/special_item_group.lowienie.txt" \
 && sed -i '1s/^\xEF\xBB\xBF//; s/\r$//; s/$/\r/' "$a" \
 && awk 'BEGIN{keep=1} /^Group/{blk=""; keep=1} {blk=blk $0 "\n"} /Vnum[ \t]+(27625)([^0-9]|$)/{keep=0} /^}/{ if (keep) printf "%s", blk; blk=""; keep=1 }' "$S" > "$S.new" \
 && { [ -z "$(tail -c 1 "$S.new")" ] || printf '\r\n' >> "$S.new"; } \
 && cat "$a" >> "$S.new" \
 && test "$(grep -c -E '^[[:blank:]]*Vnum[[:blank:]]+27625([^0-9]|$)' "$S.new")" = 1 \
 && mv "$S.new" "$S" \
 && C="$L/cube.txt" && c="$A/cube.lowienie.txt" \
 && ! grep -q -E '^reward[[:blank:]]+27591[[:blank:]]' "$C" \
 && sed -i '1s/^\xEF\xBB\xBF//; s/\r$//; s/$/\r/' "$c" \
 && { [ -z "$(tail -c 1 "$C")" ] || printf '\r\n' >> "$C"; } \
 && cat "$c" >> "$C" \
 && test "$(grep -c -E '^reward[[:blank:]]+27591[[:blank:]]' "$C")" -eq 1 \
 && rm -rf "$A" \
 && echo "share: fishing as on the global server - libs, Rybak's take, Skrzynia Nimfy Wodnej, Wedka Weglowa (MT2009_PLUS_FISHING_GLOBAL_V1)"

# MT2009_PLUS_GROWTH_PET_V1 (share; 4 November 2026): the growth pets' drops and chests (pety/; the items are
# mariadb/playerbot/pety.sql) - after moby_global (it cuts rows from groups that are not ours) and after every step
# that appends or edits a group this one touches:
#  * mob_drop_item.pety.txt - 26 "drop" groups MT2009_pety_<mob>: Jajo Mini Azraela (Charon, Azrael), Ksiega Dzikiego /
#    Dzielnego Zwierza (Metin Lasu and the pl-wiki's bosses), Bohat. Ksiega Zwierza (Gnoll / Ahtrin Kapitan, Ahtrin
#    Wielki Mistrz), Smakolyk / Smakolyk+ (Metin Lasu, for Metin Agonii); none may exist before;
#  * special_item_group.pety.txt - Skrzynka na Zwierzaka (55400, one egg) and Skrzynia Ksiag Zwierza (55009, one of the
#    23 books); neither may have a group before.
# The other chests' pet rows live in their own files (dungeons, rumi, catchking, yutnori, flower, balathor, arezzo,
# atlantyda, yohara_meley, yohara_maps3, yohara_zaklety).
COPY pety/ /tmp/pety-add/
RUN set -eu; L=/opt/metin2/share/locale/poland; A=/tmp/pety-add \
 && find "$A" -type f -name '*.txt' -exec sed -i '1s/^\xEF\xBB\xBF//; s/\r$//; s/$/\r/' {} + \
 && F="$L/mob_drop_item.txt" \
 && ! grep -q -E '^Group[[:blank:]]+MT2009_pety_' "$F" \
 && { [ -z "$(tail -c 1 "$F")" ] || printf '\r\n' >> "$F"; } \
 && cat "$A/mob_drop_item.pety.txt" >> "$F" \
 && test "$(grep -c -E '^Group[[:blank:]]+MT2009_pety_[0-9]+[[:space:]]*$' "$F")" = 26 \
 && G="$L/special_item_group.txt" \
 && ! grep -q -E '^[[:blank:]]*Vnum[[:blank:]]+(55400|55009)([^0-9]|$)' "$G" \
 && { [ -z "$(tail -c 1 "$G")" ] || printf '\r\n' >> "$G"; } \
 && cat "$A/special_item_group.pety.txt" >> "$G" \
 && test "$(grep -c -E '^[[:blank:]]*Vnum[[:blank:]]+(55400|55009)([^0-9]|$)' "$G")" = 2 \
 && ! grep -q -E '^[[:blank:]]*Vnum[[:blank:]]+95737([^0-9]|$)' "$G" \
 && rm -rf "$A" \
 && echo "share: growth pets - 26 drop groups, Skrzynka na Zwierzaka / Skrzynia Ksiag Zwierza (MT2009_PLUS_GROWTH_PET_V1)"

# MT2009_PLUS_BRAKI_WIKI_V1 (share; the owner, 5 November 2026: "Dodaj zgodnie z Wiki Global" - braki-yohara.md B9;
# brakiwiki/ GENERATED by tools/brakiwiki/gen_brakiwiki.py, the items: mariadb/playerbot/braki_wiki.sql) - after
# moby_global and pety (it adds a group of its own, cuts nothing):
#  * cube.brakiwiki.txt - Mistrz Chi's (20823, Dongan; quest rekawice opens the window) 40 recipes of Rekawice Weza
#    (23050-23089): the Sung Ma glove of the same Will +0..+9, Kamien Ksiezycowy, Agat, Dwutlenek Tytanu, 10 000 000
#    Yang, 30-100% by the plus (the pl-wiki "Wytwarzanie Rekawic");
#  * mob_drop_item.brakiwiki.txt - Zolnierz Ochao's Stalowe Plyty (the pl-wiki "Stalowe Plyty"; group
#    MT2009_bwiki_6302, none may exist before).
# Ksiega Misji (W.Pln.W.) (50336) is quest ksiega_misji_wawoz (the quests stage above).
COPY brakiwiki/ /tmp/brakiwiki-add/
RUN set -eu; L=/opt/metin2/share/locale/poland; A=/tmp/brakiwiki-add \
 && find "$A" -type f -name '*.txt' -exec sed -i '1s/^\xEF\xBB\xBF//; s/\r$//; s/$/\r/' {} + \
 && C="$L/cube.txt" \
 && ! grep -q -E '^reward[[:blank:]]+23050[[:blank:]]' "$C" \
 && n=$(grep -c -E '^section' "$A/cube.brakiwiki.txt") && b=$(grep -c -E '^section' "$C") \
 && { [ -z "$(tail -c 1 "$C")" ] || printf '\r\n' >> "$C"; } \
 && cat "$A/cube.brakiwiki.txt" >> "$C" \
 && test "$n" -eq 40 && test "$(grep -c -E '^section' "$C")" -eq "$((b + n))" \
 && test "$(grep -c -E '^reward[[:blank:]]+230[5-8]0[[:blank:]]+1[[:space:]]*$' "$C")" -eq 40 \
 && F="$L/mob_drop_item.txt" \
 && ! grep -q -E '^Group[[:blank:]]+MT2009_bwiki_' "$F" \
 && { [ -z "$(tail -c 1 "$F")" ] || printf '\r\n' >> "$F"; } \
 && cat "$A/mob_drop_item.brakiwiki.txt" >> "$F" \
 && test "$(grep -c -E '^Group[[:blank:]]+MT2009_bwiki_[0-9]+[[:space:]]*$' "$F")" = 1 \
 && rm -rf "$A" \
 && echo "share: Yohara items as on the wiki - Mistrz Chi's $n serpent glove recipes, Zolnierz Ochao's Stalowe Plyty (MT2009_PLUS_BRAKI_WIKI_V1)"

# MT2009_PLUS_NPC_LOCATION_HELPER_V1 (Autor: Best Studio): Lokalizator NPC - the map list and each map's NPC points
# (npc_location_helper/, GENERATED by tools/npcloc/gen_npcloc_data.py from our world) in locale/poland/
# npc_location_helper/, where npc_location_helper.cpp reads them (LocaleService_GetBasePath() + "/npc_location_helper/":
# a teleport to an NPC must match one of these points). PL: lista map i punkty NPC Lokalizatora NPC.
COPY npc_location_helper/ /opt/metin2/share/locale/poland/npc_location_helper/
RUN set -eu; H=/opt/metin2/share/locale/poland/npc_location_helper \
 && find "$H" -type f -name '*.txt' -exec sed -i 's/\r$//' {} + \
 && test -s "$H/npc_location_helper.txt" \
 && test "$(find "$H" -type f -name '*_point.txt' | wc -l)" -ge 40 \
 && echo "share: Lokalizator NPC - $(grep -c -E '^[[:blank:]]+[0-9]+[[:blank:]]' "$H/npc_location_helper.txt") maps, $(find "$H" -type f -name '*_point.txt' | wc -l) point files"

# MT2009_PLUS_WEAPON_ELEMENT_V1 (share): Zaczarowanie Zywiolu Broni (server-patches/zywiolbroni; the owner, 29 October
# 2026) - weapon_element.txt (THE config: prices, fees, chance, the weighted value tables, guild levels) in
# locale/poland, where the engine reads it at boot and on "/welem_reload"; Straznik Medali (20650, mariadb/playerbot/
# zywiol_broni.sql: on_click = his shop 9560) on the three guild lands at the wiki's cells - Jungrang (4,
# metin2_map_guild_01) 346,171, Waryong (24, guild_02) 253,236, Imha (44, guild_03) 284,240.
COPY zywiolbroni/weapon_element.txt /opt/metin2/share/locale/poland/weapon_element.txt
RUN set -eu; L=/opt/metin2/share/locale/poland; sed -i 's/\r$//' "$L/weapon_element.txt" \
 && grep -q -E '^chance[[:blank:]]' "$L/weapon_element.txt" \
 && for p in "metin2_map_guild_01 346 171 5" "metin2_map_guild_02 253 236 5" "metin2_map_guild_03 284 240 5"; do \
      set -- $p; F="$L/map/$1/npc.txt"; test -f "$F"; \
      [ -z "$(tail -c 1 "$F")" ] || printf '\n' >> "$F"; \
      grep -q -E '[[:blank:]]20650[[:space:]]*$' "$F" || printf 'm\t%s\t%s\t0\t0\t0\t%s\t60s\t100\t1\t20650\n' "$2" "$3" "$4" >> "$F"; \
      test "$(grep -c -E '[[:blank:]]20650[[:space:]]*$' "$F")" -eq 1 || exit 1; \
    done \
 && echo "share: Straznik Medali (20650) on the three guild lands, weapon_element.txt (MT2009_PLUS_WEAPON_ELEMENT_V1)"

# Seed for a core's mark/ directory (guild symbols): copied into the state
# volume on first run only.
COPY src/serverfiles/mark-default /opt/metin2/share/mark-default

COPY bin/ /usr/local/bin/
RUN sed -i 's/\r$//' /usr/local/bin/entrypoint.sh /usr/local/bin/m2-* /usr/local/bin/m2ctl \
 && chmod 0755 /usr/local/bin/entrypoint.sh /usr/local/bin/m2-* /usr/local/bin/m2ctl \
 && chmod 0755 /opt/metin2/share/bin/game /opt/metin2/share/bin/db

# ---- mutable half: everything the cores write lives here, and only here.
RUN mkdir -p /opt/metin2/var && chown metin2:metin2 /opt/metin2/var
VOLUME ["/opt/metin2/var"]

ENV M2_SHARE_DIR=/opt/metin2/share \
    M2_VAR_DIR=/opt/metin2/var \
    TZ=UTC

EXPOSE 11000/tcp 13000/tcp 13001/tcp 13002/tcp 13003/tcp

HEALTHCHECK --interval=15s --timeout=5s --start-period=180s --retries=4 \
    CMD ["/usr/local/bin/m2-healthcheck"]

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["m2-supervise"]
