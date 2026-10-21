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
echo "=== syserr in the window (HANDOVER / YOHARA / COHORT / NAV / BOT_DGRUN), all cores of channel 1 + db"
for c in game1 game2 game3 first; do
  E=$(logs $c syserr | win | grep -E "PLAYERBOT_HANDOVER|PLAYERBOT_YOHARA|PLAYERBOT_COHORT|PLAYERBOT_NAV|BOT_DGRUN")
  n=$(printf '%s' "$E" | grep -c .)
  echo "[$c] $n lines"; [ "$n" -gt 0 ] && printf '%s\n' "$E" | sed 's/^[A-Z][a-z]* [0-9]* [0-9:]* :: //' | sed 's/pid=[0-9]*/pid=N/g' | sort | uniq -c | sort -rn | head -8
done
for c in game1 game2 game3 first; do
  n=$(logs $c syserr | win | grep -c -E "already exist in game|login state already has main state|SIGSEGV|core dumped")
  [ "$n" -gt 0 ] && echo "[$c] DUPLICATE/CRASH markers: $n"
done
docker exec $G sh -c "ls -lt $CH/*/cores 2>/dev/null | grep -v '^total' | head -5"
