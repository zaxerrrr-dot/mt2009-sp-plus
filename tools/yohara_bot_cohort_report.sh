#!/bin/sh
# MT2009_PLUS_BOT_YOHARA_COHORT_V1 - the night's report on the bot cohorts (test server, read-only).
#   sh noc-raport.sh [hours]        (default 2: the log window for the counts and the errors)
# Per cohort: members, where they are, resting, sent/arrived/deaths/runs/rest-outs, levels and EXP;
# the last census lines of every core of channel 1; the window's events; syserr lines of the
# handover / Yohara / cohort / navigation / dungeon runs; memory per core and the host's.
H=${1:-2}
G=mt2009plustest-game
DBC=mt2009plustest-db
CH=/opt/metin2/var/channel1
db() { docker exec -i $DBC sh -c 'mariadb -uroot -p"$MARIADB_ROOT_PASSWORD" --table 2>/dev/null'; }
CUT=$(date -d "-$H hours" +%m%d%H%M%S)
# syslog/syserr lines start "Oct 21 23:04:06" - keep the window's (MMDDhhmmss compared as text).
win() { awk -v cut="$CUT" 'BEGIN{split("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec",m," ");for(i=1;i<=12;i++)M[m[i]]=sprintf("%02d",i)}
  { if (!($1 in M)) next; t=$3; gsub(":","",t); k=M[$1] sprintf("%02d",$2) t; if (k >= cut) print }'; }
logs() { docker exec $G sh -c "tail -c 60000000 $CH/$1/$2 2>/dev/null"; }

echo "=== $(date '+%F %T')  window ${H} h (from $(date -d "-$H hours" '+%T'))"
echo
echo "=== host"
free -m | awk 'NR<=2'
uptime
echo
echo "=== game cores (RSS MB; 32-bit core limit 4096)"
docker exec $G sh -c 'for f in /opt/metin2/var/channel*/*/pid /opt/metin2/var/db/pid /opt/metin2/var/auth/pid; do
  [ -f "$f" ] || continue; p=$(cat $f); d=${f%/pid}; d=${d#/opt/metin2/var/}
  r=$(awk "/VmRSS/{print int(\$2/1024)}" /proc/$p/status 2>/dev/null); [ -n "$r" ] || r=DOWN
  echo "$d $r MB"; done'
docker stats --no-stream --format '{{.Name}} {{.MemUsage}} CPU {{.CPUPerc}}' $G $DBC 2>/dev/null
echo
echo "=== cohorts (DB; levels from player.player = the db core's last flush)"
echo "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='common' AND table_name='playerbot_yohara_cohort';" | db | grep -q ' 1 ' || echo "(no common.playerbot_yohara_cohort - the cohorts were not applied)"
db <<'EOF'
SELECT c.purpose, COUNT(*) AS members,
       COALESCE(SUM(h.state = 2 AND h.updated_at > NOW() - INTERVAL 180 SECOND), 0) AS staying,
       COALESCE(SUM(h.state = 1), 0) AS on_way, SUM(IFNULL(c.rest_until > NOW(), 0)) AS resting,
       SUM(c.sent) AS sent, SUM(c.arrived) AS arrived, SUM(c.deaths) AS deaths, SUM(c.runs) AS szc_runs,
       SUM(c.rest_outs) AS rest_outs, SUM(p.level - c.level_start) AS levels_gained,
       ROUND(AVG(p.level), 1) AS avg_level, MIN(p.level) AS lv_min, MAX(p.level) AS lv_max,
       SUM(c.exp_gained) AS exp_gained
  FROM common.playerbot_yohara_cohort c
  LEFT JOIN common.playerbot_core_handover h ON h.pid = c.pid
  LEFT JOIN player.player p ON p.id = c.pid
 GROUP BY c.purpose;
SELECT c.purpose, IFNULL(h.target_map, 0) AS row_map, IFNULL(h.state, 0) AS row_state, c.last_map, COUNT(*) AS bots
  FROM common.playerbot_yohara_cohort c LEFT JOIN common.playerbot_core_handover h ON h.pid = c.pid
 GROUP BY 1, 2, 3, 4 ORDER BY 1, 5 DESC;
SELECT purpose, state, target_map, COUNT(*) AS rows_all_bots FROM common.playerbot_core_handover GROUP BY 1, 2, 3;
EOF
echo
echo "=== last census of each core (channel 1)"
logs game1 syslog | grep "PLAYERBOT_HANDOVER: config" | tail -1 | sed 's/^/[game1] /'
logs game1 syslog | grep "PLAYERBOT_COHORT: loaded" | tail -1 | sed 's/^/[game1] /'
for c in game1 game2 game3 first; do
  logs $c syslog | grep -E "PLAYERBOT_HANDOVER: census|PLAYERBOT_COHORT: census" | tail -6 | sed "s/^/[$c] /"
done
echo
echo "=== events in the window (channel 1, all cores)"
ALL=$(for c in game1 game2 game3 first; do logs $c syslog | win | sed "s/^/$c /"; done)
cnt() { printf '%-34s %s\n' "$1" "$(printf '%s\n' "$ALL" | grep -c -E "$2")"; }
cnt "cohort dispatch" "PLAYERBOT_COHORT: dispatch"
cnt "handover claimed (any)" "PLAYERBOT_HANDOVER: claimed"
cnt "handover arrived (any)" "PLAYERBOT_HANDOVER: arrived"
cnt "cohort rest out" "PLAYERBOT_COHORT: rest out"
cnt "cohort level up" "PLAYERBOT_COHORT: level up"
cnt "deaths on other cores (any)" "PLAYERBOT_YOHARA: died"
cnt "szc run start" "PLAYERBOT_YOHARA: szc run start"
cnt "szc run end" "PLAYERBOT_YOHARA: szc run end"
cnt "refused / cancel / load lost" "PLAYERBOT_HANDOVER: (refused|cancel|load lost)"
cnt "goes home (non-cohort)" "PLAYERBOT_YOHARA: goes home"
cnt "bag still full" "PLAYERBOT_COHORT: bag still full"
cnt "out of band" "PLAYERBOT_COHORT: out of its band"
echo "-- szc run results:"; printf '%s\n' "$ALL" | grep "szc run end" | sed 's/.*result=\([^ ]*\).*/\1/' | sort | uniq -c
echo "-- rest-out reasons:"; printf '%s\n' "$ALL" | grep "COHORT: rest out" | sed 's/.*why=//' | sort | uniq -c | sort -rn | head
echo "-- deaths by map:"; printf '%s\n' "$ALL" | grep "YOHARA: died" | sed 's/.* map=\([0-9]*\).*/\1/' | sort | uniq -c
echo
# MT2009_PLUS_BOT_HYDRA_COHORT_V1: the Hydra's fixed parties - the cohort's rows (whole night) and the window's
# runs per party from the PLAYERBOT_HYDRA lines of game3 (run end: result, time, wave, mast, deaths, wipes,
# polymorphs, elixirs, repairs; polymorph; died).
echo "=== Hydra (Obrona Statku) - per fixed party"
db <<'EOF'
SELECT c.party, COUNT(*) AS members, MIN(pi.empire) AS kingdom,
       COALESCE(SUM(h.state = 2 AND h.updated_at > NOW() - INTERVAL 180 SECOND), 0) AS on_core3,
       COALESCE(SUM(h.state = 1), 0) AS on_way, SUM(IFNULL(c.rest_until > NOW(), 0)) AS resting,
       SUM(c.runs) AS member_runs, SUM(c.wins) AS member_wins, SUM(c.deaths) AS deaths, SUM(c.rest_outs) AS rest_outs,
       MIN(p.level) AS lv_min, MAX(p.level) AS lv_max
  FROM common.playerbot_yohara_cohort c
  LEFT JOIN common.playerbot_core_handover h ON h.pid = c.pid
  LEFT JOIN player.player p ON p.id = c.pid
  LEFT JOIN player.player_index pi ON pi.id = p.account_id
 WHERE c.purpose = 'hydra'
 GROUP BY c.party;
EOF
printf '%s\n' "$ALL" | grep "PLAYERBOT_HYDRA: run end" | awk '
  { for (i = 1; i <= NF; ++i) { split($i, kv, "="); v[kv[1]] = kv[2] }
    p = v["party"]; runs[p]++; res[p, v["result"]]++; if (v["won"] == 1) { won[p]++; tw[p] += v["took_s"] }
    if (v["wave"] > wave[p]) wave[p] = v["wave"]; d[p] += v["deaths"]; w[p] += v["wipes"]; pm[p] += v["polymorphs"]
    el[p] += v["elixirs"]; rp[p] += v["repairs"]; if (v["mast_min_pct"] >= 0) { mm[p] += v["mast_min_pct"]; mn[p]++ }
    parties[p] = 1 }
  END { printf "%-6s %5s %5s %8s %8s %7s %6s %10s %9s %8s %8s\n", "party", "runs", "won", "won_avg", "max_wave", "deaths",
          "wipes", "mast_avg%", "polymorph", "elixirs", "repairs"
        for (p in parties) printf "%-6s %5d %5d %7ds %8d %7d %6d %10d %9d %8d %8d\n", p, runs[p], won[p],
          won[p] ? tw[p] / won[p] : 0, wave[p], d[p], w[p], mn[p] ? mm[p] / mn[p] : -1, pm[p], el[p], rp[p] }'
echo "-- hydra results by party:"; printf '%s\n' "$ALL" | grep "PLAYERBOT_HYDRA: run end" | \
  sed 's/.* party=\([0-9]*\) .* result=\([^ ]*\) .*/party \1 \2/' | sort | uniq -c
cnt "hydra parties called" "PLAYERBOT_HYDRA: party called"
cnt "hydra runs started" "PLAYERBOT_HYDRA: run start"
cnt "hydra ships started" "PLAYERBOT_HYDRA: ship started"
cnt "hydra polymorphs" "PLAYERBOT_HYDRA: polymorph pid"
cnt "hydra polymorph refused / no marble" "PLAYERBOT_HYDRA: (polymorph refused|no marble)"
cnt "hydra deaths" "PLAYERBOT_HYDRA: died"
cnt "hydra kit given" "PLAYERBOT_HYDRA: kit"
echo "-- hydra deaths by class/path (job group polymorphed):"; printf '%s\n' "$ALL" | grep "PLAYERBOT_HYDRA: died" | \
  sed 's/.* wave=\([0-9]*\) job=\([0-9]*\) group=\([0-9]*\) polymorphed=\([01]\).*/wave \1 job \2 group \3 poly \4/' | sort | uniq -c | sort -rn | head
# MT2009_PLUS_BOT_CHAMPION_V1: the Hydra's end - the statue's errand (PLAYERBOT_CHAMPION lines of game3).
echo "-- champion errand (the statue, after the Hydra):"
cnt "champion errands started" "PLAYERBOT_CHAMPION: start"
cnt "champion flags set" "PLAYERBOT_CHAMPION: flags"
cnt "champion arrived at the statue" "PLAYERBOT_CHAMPION: arrived"
cnt "champion walk put beside" "PLAYERBOT_CHAMPION: walk too long"
cnt "champion unlocked" "PLAYERBOT_CHAMPION: unlocked"
cnt "champion refused" "PLAYERBOT_CHAMPION: refused"
cnt "champion skipped" "PLAYERBOT_CHAMPION: skip"
printf '%s\n' "$ALL" | grep "PLAYERBOT_CHAMPION: census" | tail -1
echo
# MT2009_PLUS_BOT_YOHARA_MAPS_V1: the Yohara maps' cohort ("yohara") - the rows by map and Champion level (DB), the
# last PLAYERBOT_SUNGMA census of game3 (a line a map, every 5 min: here, kills/h, exp/h, champion exp/h, deaths,
# stuck, navigation failures, level-ups, champion level-ups, moves) and the window's moves, points, step-downs.
echo "=== Yohara maps (Sung Ma) - the cohort 'yohara' and the bot Champions"
db <<'EOF'
SELECT IFNULL(h.target_map, c.last_map) AS map, COUNT(*) AS members,
       COALESCE(SUM(h.state = 2 AND h.updated_at > NOW() - INTERVAL 180 SECOND), 0) AS on_core3,
       COALESCE(SUM(h.state = 1), 0) AS on_way, SUM(IFNULL(c.rest_until > NOW(), 0)) AS resting,
       MIN(p.conqueror_level) AS champ_min, MAX(p.conqueror_level) AS champ_max, ROUND(AVG(p.conqueror_level), 1) AS champ_avg,
       SUM(p.conqueror_point) AS points_free, ROUND(AVG(p.sungma_str + p.sungma_hp + p.sungma_move + p.sungma_immune), 1) AS points_spent_avg,
       SUM(c.deaths) AS deaths, SUM(c.rest_outs) AS rest_outs, SUM(c.exp_gained) AS exp_gained
  FROM common.playerbot_yohara_cohort c
  LEFT JOIN common.playerbot_core_handover h ON h.pid = c.pid
  LEFT JOIN player.player p ON p.id = c.pid
 WHERE c.purpose = 'yohara'
 GROUP BY 1 ORDER BY 1;
SELECT p.conqueror_level AS champion, COUNT(*) AS bot_champions_all FROM player.player p
  JOIN account.account ac ON ac.id = p.account_id WHERE LEFT(ac.login, 10) = 'playerbot_' AND p.conqueror_level > 0
 GROUP BY 1 ORDER BY 1;
EOF
logs game3 syslog | grep "PLAYERBOT_SUNGMA: summary" | tail -1 | sed 's/^/[game3] /'
logs game3 syslog | grep "PLAYERBOT_SUNGMA: census" | tail -9 | sed 's/^.*PLAYERBOT_SUNGMA: census //; s/^/[game3] /'
cnt "sungma handover arrived" "PLAYERBOT_HANDOVER: arrived .*purpose=yohara"
cnt "sungma moves between maps" "PLAYERBOT_SUNGMA: move pid"
cnt "sungma portal walks" "PLAYERBOT_SUNGMA: to the portal"
cnt "sungma portal walk too long" "PLAYERBOT_SUNGMA: portal walk too long"
cnt "sungma move failed (navigation)" "PLAYERBOT_SUNGMA: move failed"
cnt "sungma chamber hops (Zejscie)" "PLAYERBOT_SUNGMA: chamber hop"
# MT2009_PLUS_BOT_YOHARA_MAPS_V2: warps instead of far portal walks, revivals at the safe point, Dongan's errands
cnt "sungma portal far, warped" "PLAYERBOT_SUNGMA: portal far, warp"
cnt "sungma revived at the safe point" "PLAYERBOT_SUNGMA: revived at the safe point"
cnt "sungma errands to Dongan" "PLAYERBOT_SUNGMA: errand to dongan"
cnt "sungma errands done" "PLAYERBOT_SUNGMA: errand done"
cnt "sungma errand fallbacks (belt in place)" "PLAYERBOT_SUNGMA: errand fallback"
cnt "sungma points spent" "PLAYERBOT_SUNGMA: points pid"
cnt "sungma champion level ups" "PLAYERBOT_SUNGMA: champion level up"
cnt "sungma step down (deaths)" "PLAYERBOT_SUNGMA: step down"
cnt "sungma map refused (sungma_map)" "refusal=sungma_map|reason=sungma_map"
echo "-- sungma moves (from -> to why):"; printf '%s\n' "$ALL" | grep "PLAYERBOT_SUNGMA: move pid" | \
  sed 's/.* from=\([0-9]*\) to=\([0-9]*\) why=\([a-z]*\).*/\1 -> \2 \3/' | sort | uniq -c | sort -rn | head
echo "-- sungma deaths by map:"; printf '%s\n' "$ALL" | grep "YOHARA: died.*purpose=yohara" | sed 's/.* map=\([0-9]*\).*/\1/' | sort | uniq -c
echo "-- sungma leaving (why):"; printf '%s\n' "$ALL" | grep -E "(goes home|rest out).*why=sungma" | sed 's/.*why=//' | sort | uniq -c | sort -rn
echo
echo "=== syserr in the window (HANDOVER / YOHARA / COHORT / NAV / BOT_DGRUN / HYDRA / SUNGMA / ship defense), all cores of channel 1 + db"
for c in game1 game2 game3 first; do
  E=$(logs $c syserr | win | grep -E "PLAYERBOT_HANDOVER|PLAYERBOT_YOHARA|PLAYERBOT_COHORT|PLAYERBOT_NAV|BOT_DGRUN|PLAYERBOT_HYDRA|PLAYERBOT_SUNGMA|ship defense")
  n=$(printf '%s' "$E" | grep -c .)
  echo "[$c] $n lines"; [ "$n" -gt 0 ] && printf '%s\n' "$E" | sed 's/^[A-Z][a-z]* [0-9]* [0-9:]* :: //' | sed 's/pid=[0-9]*/pid=N/g' | sort | uniq -c | sort -rn | head -8
done
for c in game1 game2 game3 first; do
  n=$(logs $c syserr | win | grep -c -E "already exist in game|login state already has main state|SIGSEGV|core dumped")
  [ "$n" -gt 0 ] && echo "[$c] DUPLICATE/CRASH markers: $n"
done
docker exec $G sh -c "ls -lt $CH/*/cores 2>/dev/null | grep -v '^total' | head -5"
