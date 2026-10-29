"""MT2009_PLUS_SEBAN_BOT_STATS_V1: "Statystyki botow" - the bosses and Metin
stones the bots kill and the dungeons they run (the owner, 29 October).

Where the numbers come from
---------------------------
* Kills: log.log's STONE_KILL and BOSS_KILL rows (char_battle.cpp, a monster of
  rank BOSS or higher killed by a character), folded by log_maintenance.py's
  "botkill" source into player.web_seban_bot_kill_hourly (hour, kind, bot,
  monster, base map, count, last kill). The page reads only that small table,
  never log.log, and the counts survive the log retention's prune.
* Dungeons: one row a run, written by the game cores when a run closes, in
  their working directories (the collector's /opt/metin2/var mount):
    playerbot_dungeon_runs.tsv          the bots' own dungeon runs
                                        (playerbot_dungeon_runs.h, BOT_DGRUN)
    playerbot_arezzo_dungeon_runs.tsv   the Arezzo dungeon cohort (ARZ_DG)
    playerbot_zodiac_runs.tsv           the Zodiac Temple runs (ZODIAC_RUN)
  The collector reads what was added since the last round (byte offsets in
  player.web_seban_chat_offset, "botdg:<path>") into
  player.web_seban_bot_dungeon_run, one row a run; the key makes a re-read
  harmless.

Pure pymysql: collector.py calls import_dungeon_runs(), app.py the readers.
"""
import re
from datetime import datetime, timedelta
from pathlib import Path

KIND_BOSS = 1
KIND_STONE = 2

PERIODS = {"24h": ("24 godziny", 1), "7d": ("7 dni", 7), "30d": ("30 dni", 30), "all": ("Od początku", None)}
DEFAULT_PERIOD = "7d"

DUNGEON_LABELS = {
    "biblioteka": "Biblioteka Wiedzy",
    "wieza": "Wieża Demonów",
    "wukong": "Wzgórze Wukonga",
    "razador": "Czyściec Ognia (Razador)",
    "skorpion": "Ruiny Skorpiona",
    "nemere": "Lodowa Kraina (Nemere)",
    "smok": "Leże Niebieskiego Smoka",
    "dzungla": "Starożytna Dżungla",
    "atlantyda": "Ruiny Atlantydy",
    "zodiak": "Świątynia Zodiaku",
    "hydra": "Hydra",
    "meley": "Leże Meley",
}
# Dungeon maps the panel's MAP_NAMES (the world the live map draws) has not.
DUNGEON_MAP_NAMES = {
    351: "Czyściec Ognia", 352: "Lodowa Kraina", 208: "Leże Niebieskiego Smoka", 158: "Ruiny Atlantydy",
    358: "Świątynia Zodiaku", 66: "Wieża Demonów", 363: "Biblioteka Wiedzy",
}
SOURCE_LABELS = {"dgrun": "wyprawy botów", "arezzo": "kohorta Arezzo", "zodiak": "Zodiak"}

# result -> outcome: ok (done), fail (wipe, time out, lost), abandon (given up,
# left), disband (the party never got in). Anything else counts as fail.
OUTCOMES = {
    "dgrun": {"finished": "ok", "wipe": "fail", "timeout": "fail", "lost": "fail", "mast_lost": "fail",
              "abandoned": "abandon", "aborted": "abandon", "left": "abandon",
              "disbanded": "disband", "no_stone": "disband"},
    "arezzo": {"finished": "ok", "abandoned": "abandon", "left": "abandon"},
    "zodiak": {"target": "ok", "finished": "ok", "wipe": "fail", "time_up": "fail", "expelled": "fail",
               "stalled": "fail", "leader_out": "abandon", "out": "abandon", "aborted": "abandon",
               "no_gathering": "disband"},
}
RUN_FILES = (("playerbot_dungeon_runs.tsv", "dgrun"), ("playerbot_arezzo_dungeon_runs.tsv", "arezzo"),
             ("playerbot_zodiac_runs.tsv", "zodiak"))
MAX_READ = 8 * 1024 * 1024


def ensure_tables(cur):
    cur.execute("""CREATE TABLE IF NOT EXISTS player.web_seban_bot_dungeon_run (
      source VARCHAR(8) NOT NULL, channel TINYINT UNSIGNED NOT NULL, core VARCHAR(16) NOT NULL,
      run_id INT NOT NULL, closed_at DATETIME NOT NULL, dungeon VARCHAR(24) NOT NULL,
      result VARCHAR(16) NOT NULL, outcome VARCHAR(8) NOT NULL, took_s INT UNSIGNED NOT NULL DEFAULT 0,
      members TINYINT UNSIGNED NOT NULL DEFAULT 0, level_min SMALLINT UNSIGNED NOT NULL DEFAULT 0,
      level_max SMALLINT UNSIGNED NOT NULL DEFAULT 0, deaths INT NOT NULL DEFAULT 0,
      PRIMARY KEY (source, channel, core, run_id, closed_at),
      KEY closed_idx (closed_at), KEY dungeon_closed (dungeon, closed_at)) ENGINE=InnoDB""")
    cur.execute("""CREATE TABLE IF NOT EXISTS player.web_seban_chat_offset (
      path VARCHAR(255) NOT NULL PRIMARY KEY, byte_offset BIGINT UNSIGNED NOT NULL DEFAULT 0,
      updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
      ) ENGINE=InnoDB""")


def _int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def parse_run_line(source, line):
    """One TSV row -> (run_id, closed_at, dungeon, result, took_s, members,
    level_min, level_max, deaths), or None."""
    f = line.rstrip("\r\n").split("\t")
    try:
        closed_at = datetime.fromtimestamp(int(f[0]))
        run_id = int(f[1])
    except (ValueError, IndexError, OverflowError, OSError):
        return None
    if source == "dgrun" and len(f) >= 13:
        # time run dungeon instance empire members lvlow lvhigh result took_s stage stage_s deaths ...
        return (run_id, closed_at, f[2][:24], f[8][:16], _int(f[9]), _int(f[5]), _int(f[6]), _int(f[7]), _int(f[12]))
    if source == "arezzo" and len(f) >= 10:
        # time run dungeon instance empire result took_s stage stage_s deaths wipes
        return (run_id, closed_at, f[2][:24], f[5][:16], _int(f[6]), 0, 0, 0, _int(f[9]))
    if source == "zodiak" and len(f) >= 14:
        # time run sign portal instance kingdom members lvlow lvhigh result floor seconds floors deaths ...
        return (run_id, closed_at, "zodiak", f[9][:16], _int(f[11]), _int(f[6]), _int(f[7]), _int(f[8]), _int(f[13]))
    return None


def _outcome(source, result):
    return OUTCOMES.get(source, {}).get(result, "fail")


def run_files(var_root):
    """(channel, core, source, path) of every runs file under the var root."""
    root = Path(var_root)
    try:
        channels = sorted(root.glob("channel*"))
    except OSError:
        return
    for channel_dir in channels:
        match = re.fullmatch(r"channel(\d+)", channel_dir.name)
        if not match or not channel_dir.is_dir():
            continue
        for name, source in RUN_FILES:
            try:
                paths = sorted(channel_dir.glob(f"*/{name}"))
            except OSError:
                continue
            for path in paths:
                yield int(match.group(1)), path.parent.name[:16], source, path


def import_dungeon_runs(cur, var_root):
    """Reads what the runs files gained since the last call. Returns rows read."""
    ensure_tables(cur)
    total = 0
    for channel, core, source, path in run_files(var_root):
        key = f"botdg:{path}"[:255]
        cur.execute("SELECT byte_offset FROM player.web_seban_chat_offset WHERE path=%s", (key,))
        row = cur.fetchone()
        offset = int(row[0]) if row else 0
        try:
            size = path.stat().st_size
            if size < offset:  # the file was cut or started anew
                offset = 0
            if size == offset:
                continue
            with path.open("rb") as handle:
                handle.seek(offset)
                data = handle.read(MAX_READ)
        except OSError:
            continue
        end = data.rfind(b"\n")
        if end < 0:
            continue
        data = data[:end + 1]
        items = []
        for raw in data.decode("cp1250", "replace").splitlines():
            parsed = parse_run_line(source, raw)
            if parsed:
                run_id, closed_at, dungeon, result, took, members, lv_min, lv_max, deaths = parsed
                items.append((source, channel, core, run_id, closed_at, dungeon, result, _outcome(source, result),
                              max(0, took), min(255, max(0, members)), max(0, lv_min), max(0, lv_max), deaths))
        for start in range(0, len(items), 500):
            cur.executemany("""INSERT IGNORE INTO player.web_seban_bot_dungeon_run
              (source,channel,core,run_id,closed_at,dungeon,result,outcome,took_s,members,level_min,level_max,deaths)
              VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", items[start:start + 500])
        cur.execute("""INSERT INTO player.web_seban_chat_offset (path, byte_offset) VALUES (%s,%s)
          ON DUPLICATE KEY UPDATE byte_offset=VALUES(byte_offset)""", (key, offset + len(data)))
        total += len(items)
    return total


# ---------------------------------------------------------------- reading
def period_key(value):
    return value if value in PERIODS else DEFAULT_PERIOD


def dungeon_label(key):
    return DUNGEON_LABELS.get(key) or (key or "?").replace("_", " ").capitalize()


def _since(period, now):
    days = PERIODS[period][1]
    if days is None:
        return None
    return now - timedelta(days=days)


def kill_rows(rows, kind, period, now, limit=50):
    """Top monsters of one kind killed by bots in the period: vnum, kills,
    players' kills of the same monster, last kill, maps (base map -> kills)."""
    since = _since(period, now)
    where, params = "kind=%s", [kind]
    if since is not None:
        where += " AND hour >= %s"
        params.append(since.replace(minute=0, second=0, microsecond=0))
    found = rows(f"""SELECT vnum, map_index, bot, SUM(n) AS n, MAX(last_at) AS last_at
      FROM player.web_seban_bot_kill_hourly WHERE {where} GROUP BY vnum, map_index, bot""", tuple(params))
    by_vnum = {}
    for row in found:
        entry = by_vnum.setdefault(int(row["vnum"]), {"vnum": int(row["vnum"]), "kills": 0, "player_kills": 0,
                                                       "last_at": None, "maps": {}})
        n = int(row["n"] or 0)
        if int(row["bot"]):
            entry["kills"] += n
            entry["maps"][int(row["map_index"] or 0)] = entry["maps"].get(int(row["map_index"] or 0), 0) + n
            if row["last_at"] and (entry["last_at"] is None or row["last_at"] > entry["last_at"]):
                entry["last_at"] = row["last_at"]
        else:
            entry["player_kills"] += n
    result = sorted((e for e in by_vnum.values() if e["kills"]), key=lambda e: (-e["kills"], e["vnum"]))
    totals = {"kills": sum(e["kills"] for e in result), "kinds": len(result),
              "player_kills": sum(e["player_kills"] for e in by_vnum.values())}
    return result[:limit], totals


def kill_maps(entries):
    """Kills per base map over all the listed monsters."""
    maps = {}
    for entry in entries:
        for index, n in entry["maps"].items():
            maps[index] = maps.get(index, 0) + n
    return sorted(maps.items(), key=lambda item: -item[1])


def dungeon_rows(rows, period, now):
    since = _since(period, now)
    where, params = "", ()
    if since is not None:
        where, params = "WHERE closed_at >= %s", (since,)
    found = rows(f"""SELECT dungeon, COUNT(*) AS runs,
        SUM(outcome<>'disband') AS entered, SUM(outcome='ok') AS ok, SUM(outcome='fail') AS fail,
        SUM(outcome='abandon') AS abandon, SUM(outcome='disband') AS disband,
        AVG(IF(outcome='ok' AND took_s>0, took_s, NULL)) AS avg_ok_s,
        MIN(IF(outcome='ok' AND took_s>0, took_s, NULL)) AS best_s,
        SUM(deaths) AS deaths, AVG(IF(members>0, members, NULL)) AS avg_members,
        MAX(closed_at) AS last_at
      FROM player.web_seban_bot_dungeon_run {where} GROUP BY dungeon""", params)
    result = []
    for row in found:
        entered = int(row["entered"] or 0)
        ok = int(row["ok"] or 0)
        result.append({"key": row["dungeon"], "name": dungeon_label(row["dungeon"]), "runs": int(row["runs"] or 0),
                       "entered": entered, "ok": ok, "fail": int(row["fail"] or 0),
                       "abandon": int(row["abandon"] or 0), "disband": int(row["disband"] or 0),
                       "rate": round(100.0 * ok / entered, 1) if entered else None,
                       "avg_ok_s": int(row["avg_ok_s"]) if row["avg_ok_s"] is not None else None,
                       "best_s": int(row["best_s"]) if row["best_s"] is not None else None,
                       "deaths": int(row["deaths"] or 0),
                       "avg_members": round(float(row["avg_members"]), 1) if row["avg_members"] is not None else None,
                       "last_at": row["last_at"]})
    result.sort(key=lambda r: (-r["entered"], -r["runs"], r["name"]))
    totals = {key: sum(r[key] for r in result) for key in ("runs", "entered", "ok", "fail", "abandon", "disband")}
    totals["rate"] = round(100.0 * totals["ok"] / totals["entered"], 1) if totals["entered"] else None
    return result, totals


def last_runs(rows, limit=15):
    found = rows("""SELECT source, channel, core, closed_at, dungeon, result, outcome, took_s, members,
        level_min, level_max, deaths FROM player.web_seban_bot_dungeon_run
      ORDER BY closed_at DESC LIMIT %s""", (int(limit),))
    for row in found:
        row["name"] = dungeon_label(row["dungeon"])
        row["source_label"] = SOURCE_LABELS.get(row["source"], row["source"])
    return found


def duration(seconds):
    if seconds is None:
        return "—"
    seconds = int(seconds)
    if seconds >= 3600:
        return f"{seconds // 3600} h {seconds % 3600 // 60:02d} min"
    return f"{seconds // 60} min {seconds % 60:02d} s"
