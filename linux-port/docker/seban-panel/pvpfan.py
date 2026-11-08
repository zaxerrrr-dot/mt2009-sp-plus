"""MT2009_PLUS_PVPFAN_V1: "PVP Fan" - wojny botów dla zabawy (właściciel, 7 listopada 2026: "tworzysz boty - 10, 100,
500 - których jedynym zadaniem jest walczyć ze sobą ... np. 50 Wojowników Ciało vs 50 Szamanów Smok").

What this page does (nothing here talks to the game directly; the tables are mariadb/playerbot/pvpfan.sql):

* categories (player.pvpfan_category): name, code for the command, the arena (map + global x,y of the centre - or the
  GM's "/pvpfan tu <kod>"), teams' distance from it, the arena's leash, channel, countdown, time limit, people allowed,
  potions; their teams (player.pvpfan_team, 2..8) and slots (player.pvpfan_slot: N x class/path/sex/level/skill
  level/stats/equipment set). A new category is made from one line - "50 Wojownik Ciało vs 50 Szaman Smok" (several
  slots in a team with "+": "25 Sura Broń + 25 Ninja Łuk vs 50 Wojownik Mental");
* equipment sets (player.pvpfan_set / _set_item): per slot of the body the item (search by name or vnum, the refine
  level = the vnum of its family), count, three sockets (stones), seven bonus lines (1-5 from world.item_attr, 6-7 from
  world.item_attr_rare, the values allowed for that kind of item with their maximum; "dowolne" lets any bonus in) and
  the potions. Presets "super PvP" per class and path (PRESETS) are written at the first visit and can be restored;
  set 0 in a slot means the class's preset;
* the characters: "Generuj postacie" makes what the slots ask for (an account playerbot_pfNNNN with password '!' and
  status BLOCK - no person logs in there -, the character, its player_index row, player.pvpfan_char) and retires what
  no longer fits (a changed class, sex or kingdom, a lower count, a deleted slot). Level, stats, skills and gear are
  the game's at every "/pvpfan start", so a change to them needs no new characters. Retired characters are deleted
  here once they have been offline 15 minutes (the game's item cache);
* Start / Gotowi / Stop: rows of player.pvpfan_command; the core that hosts the arena's map on its channel takes them
  within 3 s (playerbot_pvpfan.h) - the same as the GM's "/pvpfan start|gotowi|stop <kod>";
* the switch: the event flag m2_pvpfan_off (a player.quest row the game reads every 10 s); the env M2_PVPFAN is the
  .env page's;
* the results: player.pvpfan_war / _war_team.
"""
import os
import re
import secrets

MAX_TEAMS = 8
MAX_SLOTS_PER_TEAM = 12
CLASSES = {0: "Wojownik", 1: "Ninja", 2: "Sura", 3: "Szaman"}
PATHS = {(0, 1): "Ciało", (0, 2): "Mental", (1, 1): "Skrytobójca", (1, 2): "Łucznik",
         (2, 1): "Broń", (2, 2): "Czarna Magia", (3, 1): "Smok", (3, 2): "Leczenie"}
PATH_TAGS = {(0, 1): "Cialo", (0, 2): "Mental", (1, 1): "Skryt", (1, 2): "Luk",
             (2, 1): "Bron", (2, 2): "Magia", (3, 1): "Smok", (3, 2): "Lecz"}
PRESET_KEYS = {(0, 1): "w1", (0, 2): "w2", (1, 1): "n1", (1, 2): "n2", (2, 1): "s1", (2, 2): "s2", (3, 1): "sh1", (3, 2): "sh2"}
# Words of the one-line composition, without Polish letters (normalise() strips them).
CLASS_WORDS = {"wojownik": 0, "wojownicy": 0, "wojownikow": 0, "woj": 0, "warrior": 0,
               "ninja": 1, "ninje": 1, "ninjow": 1, "sura": 2, "sury": 2, "sur": 2,
               "szaman": 3, "szamani": 3, "szamanow": 3, "szamanka": 3, "shaman": 3}
PATH_WORDS = {"cialo": 1, "body": 1, "mental": 2, "mentalny": 2, "mentale": 2,
              "skrytobojca": 1, "skryt": 1, "sztylet": 1, "sztylety": 1, "dagger": 1, "assassin": 1,
              "lucznik": 2, "luk": 2, "luki": 2, "archer": 2, "bow": 2,
              "bron": 1, "weapon": 1, "magia": 2, "czarna": 2, "black": 2, "bm": 2,
              "smok": 1, "dragon": 1, "leczenie": 2, "heal": 2, "uzdrowienie": 2, "leczacy": 2}
SKILL_LEVELS = ((40, "P (Perfect)"), (39, "G10"), (34, "G5"), (30, "G1"), (29, "M10"), (20, "M1"), (17, "17"))
EMPIRE_NAMES = {0: "auto", 1: "Shinsoo", 2: "Chunjo", 3: "Jinno"}
RACE_BY_JOB_SEX = {(0, "male"): 0, (0, "female"): 4, (1, "male"): 5, (1, "female"): 1,
                   (2, "male"): 2, (2, "female"): 6, (3, "male"): 7, (3, "female"): 3}
JOB_STARTS = {0: (6, 4, 3, 3, 600, 200), 1: (4, 3, 6, 3, 650, 200), 2: (5, 3, 3, 6, 650, 200), 3: (3, 5, 3, 5, 700, 200)}
EMPIRE_STARTS = {1: (469300, 964200, 1), 2: (55700, 157900, 21), 3: (969600, 278400, 41)}
STATES = {"idle": "Bezczynna", "starting": "Boty wchodzą", "waiting": "Czekają na sygnał", "countdown": "Odliczanie",
          "fighting": "Walka trwa", "finished": "Koniec – boty wychodzą", "stopping": "Zatrzymywanie"}
CMD_NAMES = {"start": "Start", "ready": "Gotowi", "stop": "Stop"}
LOGIN_PREFIX = "playerbot_pf"
NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]{1,11}$")
CODE_RE = re.compile(r"^[a-z0-9_-]{1,32}$")
CLEANUP_MINUTES = 15

# The body's slots of an equipment set: key, label, the item_attr column of its bonuses (None = any bonus), and what
# item fits (item_proto type, subtypes or None for any subtype).
SLOTS = (
    ("weapon", "Broń", "weapon", 1, (0, 1, 2, 3, 4, 5, 7, 8)),
    ("body", "Zbroja", "body", 2, (0,)),
    ("head", "Hełm", "head", 2, (1,)),
    ("shield", "Tarcza", "shield", 2, (2,)),
    ("wrist", "Bransoleta", "wrist", 2, (3,)),
    ("foots", "Buty", "foots", 2, (4,)),
    ("neck", "Naszyjnik", "neck", 2, (5,)),
    ("ear", "Kolczyki", "ear", 2, (6,)),
    ("pendant", "Talizman", "pendant", 2, (7,)),
    ("glove", "Rękawice", "glove", 2, (8,)),
    ("belt", "Pas", None, 34, None),
    ("ring1", "Pierścień 1", None, 16, None),
    ("ring2", "Pierścień 2", None, 16, None),
    ("arrow", "Strzały / kołczan", None, 1, (6,)),
    ("costume_body", "Kostium", "costume_body", 28, (0,)),
    ("costume_hair", "Fryzura", "costume_hair", 28, (1,)),
    ("costume_weapon", "Kostium broni", "costume_weapon", 28, (4,)),
    ("sash", "Szarfa", None, 28, (3,)),
    ("mount", "Wierzchowiec", None, 28, (2,)),
) + tuple(("ds%d" % (k + 1), "Alchemia %d" % (k + 1), None, 29, (k,)) for k in range(7))
SLOT_KEYS = tuple(s[0] for s in SLOTS)
SLOT = {s[0]: s for s in SLOTS}
ATTR_COLS = ("weapon", "body", "wrist", "foots", "neck", "head", "shield", "ear", "costume_body", "costume_hair",
             "costume_weapon", "pendant", "glove")

# "Super PvP" presets: (vnum, (stones), ((bonus, value) x up to 7)) per slot. Bonuses are POINT numbers
# (world.item_attr.apply+0): 6 Max PŻ, 12-15 Siła/Witalność/Zręczność/Inteligencja, 17 szybkość ataku, 19 szybkość
# ruchu, 21 szybkość zaklęć, 32 regeneracja PŻ, 38 omdlenie, 40 krytyk, 41 przebicie, 43 silny przeciwko ludziom,
# 63/64 kradzież PŻ/PE, 67 blok, 69-74 odporność na broń, 77 odporność na magię, 79 odbicie, 88 odporność na
# omdlenie, 95/97 wartość ataku / ataku magicznego, 224 odporność na ludzi %, 225 odporność na magię %, 257 silny
# przeciwko ludziom %. Lines 1-5 normal bonuses, 6-7 the rare ones.
_STAT_BY = {"w1": 12, "w2": 12, "n1": 14, "n2": 14, "s1": 12, "s2": 15, "sh1": 15, "sh2": 15}
_CASTER = {"s2", "sh1", "sh2"}
_CLASS_GEAR = {
    "w1": (19299, 12699, 21970), "w2": (19299, 12699, 21973),
    "n1": (19499, 12709, 21971), "n2": (19499, 12709, 2169),
    "s1": (19699, 12719, 21970), "s2": (19699, 12719, 289),
    "sh1": (19899, 12729, 7199), "sh2": (19899, 12729, 5339),
}
_RARE_ATT = ((6, 500), (95, 50))
_RARE_MAG = ((6, 500), (97, 50))


def _preset_items(key):
    body, head, weapon = _CLASS_GEAR[key]
    caster = key in _CASTER
    rare = _RARE_MAG if caster else _RARE_ATT
    items = {
        "weapon": (weapon, (28431, 28430, 28432),
                   ((43, 10), (40, 10), (41, 10), (_STAT_BY[key], 12), (21, 20) if caster else (13, 12),
                    (257, 15), (97 if caster else 95, 50))),
        "body": (body, (28441, 28439, 28442), ((6, 2000), (69, 15), (71, 15), (77, 15), (63, 10), (224, 5), (225, 15))),
        "head": (head, (), ((43, 10), (17, 8), (32, 30), (77, 15), (64, 10)) + rare),
        "foots": (15449, (), ((6, 2000), (17, 8), (19, 20), (40, 10), (38, 8)) + rare),
        "wrist": (14549, (), ((6, 2000), (43, 10), (41, 10), (63, 10), (77, 15)) + rare),
        "neck": (16549, (), ((6, 2000), (40, 10), (41, 10), (71, 15), (74, 15)) + rare),
        "ear": (17549, (), ((43, 10), (19, 20), (72, 15), (73, 15), (70, 15)) + rare),
        "shield": (13149, (), ((43, 10), (67, 15), (79, 10), (12, 12), (88, 1), (6, 500), (67, 5))),
        "belt": (18089, (), ()),
        "glove": (23003, (), ()),
        "sash": (85014, (), ()),
    }
    if key == "n2":
        items["arrow"] = (8010, (), ())
    return items


PRESETS = {key: {"name": "Super PvP – %s %s" % (CLASSES[job], PATHS[(job, group)]), "job": job, "group": group,
                 "items": _preset_items(key)}
           for (job, group), key in PRESET_KEYS.items()}


def normalise(text):
    table = str.maketrans("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ", "acelnoszzACELNOSZZ")
    return (text or "").translate(table).lower()


def default_empire(idx):
    return (1, 3, 2)[(int(idx) - 1) % 3]


def slugify(text):
    slug = re.sub(r"[^a-z0-9]+", "_", normalise(text)).strip("_")
    return slug[:32] or "kategoria"


def parse_composition(line):
    """'50 Wojownik Ciało vs 50 Szaman Smok' -> [[(count, job, group)], [...]]; ValueError with a Polish message."""
    teams = []
    parts = re.split(r"\s+(?:vs\.?|kontra|przeciw)\s+|\s*/\s*", normalise(line).strip())
    if len(parts) < 2:
        raise ValueError("Skład: co najmniej dwie drużyny rozdzielone „vs”, np. „50 Wojownik Ciało vs 50 Szaman Smok”.")
    if len(parts) > MAX_TEAMS:
        raise ValueError(f"Najwyżej {MAX_TEAMS} drużyn.")
    for part in parts:
        slots = []
        for chunk in re.split(r"\s*[+,&]\s*|\s+i\s+", part.strip()):
            words = re.findall(r"[a-z]+|\d+", chunk)
            if not words:
                continue
            count, job, group = None, None, None
            for w in words:
                if w.isdigit():
                    count = int(w)
                elif w in CLASS_WORDS and job is None:
                    job = CLASS_WORDS[w]
                elif w in PATH_WORDS and group is None:
                    group = PATH_WORDS[w]
                elif w in ("x", "razy", "szt"):
                    continue
            if job is None:
                raise ValueError(f"Nie rozpoznano klasy w „{chunk}” (Wojownik, Ninja, Sura, Szaman).")
            slots.append((max(1, min(500, count or 10)), job, group or 1))
        if not slots:
            raise ValueError("Pusta drużyna w składzie.")
        teams.append(slots)
    return teams


def team_label(slots):
    return " + ".join(f"{s['count']}× {CLASSES.get(int(s['job']), '?')} {PATHS.get((int(s['job']), int(s['skill_group'])), '')}"
                      for s in slots) or "(pusta)"


def number(value, label, low, high, default=None):
    try:
        n = int(str(value).strip())
    except (TypeError, ValueError):
        if default is not None:
            return default
        raise ValueError(f"{label}: wpisz liczbę.")
    if n < low or n > high:
        raise ValueError(f"{label}: od {low} do {high}.")
    return n


def max_per_category():
    try:
        return max(2, min(1000, int(os.environ.get("M2_PVPFAN_MAX_CATEGORY", "500"))))
    except ValueError:
        return 500


DDL_CHECK = "SELECT 1 FROM information_schema.TABLES WHERE TABLE_SCHEMA='player' AND TABLE_NAME='pvpfan_category'"


def tables_ready(cur):
    cur.execute(DDL_CHECK)
    return bool(cur.fetchone())


def ensure_presets(cur, force_key=None):
    """Writes the presets that are missing (or the one asked for again)."""
    for key, preset in PRESETS.items():
        cur.execute("SELECT id FROM player.pvpfan_set WHERE preset_key=%s ORDER BY id LIMIT 1", (key,))
        row = cur.fetchone()
        if row and force_key != key:
            continue
        if row:
            set_id = row["id"]
            cur.execute("DELETE FROM player.pvpfan_set_item WHERE set_id=%s", (set_id,))
            cur.execute("UPDATE player.pvpfan_set SET name=%s, job=%s, skill_group=%s, red_vnum=27003, red_count=400, "
                        "blue_vnum=27006, blue_count=400 WHERE id=%s", (preset["name"], preset["job"], preset["group"], set_id))
        else:
            cur.execute("INSERT INTO player.pvpfan_set (name, job, skill_group, preset_key, note) VALUES (%s,%s,%s,%s,%s)",
                        (preset["name"], preset["job"], preset["group"], key,
                         "Preset – zmień, jak chcesz; „Przywróć preset” wraca do tych wartości."))
            set_id = cur.lastrowid
        for slot, (vnum, stones, bonuses) in preset["items"].items():
            values = [set_id, slot, vnum, 1] + [stones[i] if i < len(stones) else 0 for i in range(3)]
            for i in range(7):
                values += list(bonuses[i]) if i < len(bonuses) else [0, 0]
            cur.execute("INSERT INTO player.pvpfan_set_item (set_id, slot, vnum, count, socket0, socket1, socket2, "
                        + ", ".join(f"attrtype{i}, attrvalue{i}" for i in range(7)) + ") VALUES ("
                        + ",".join(["%s"] * len(values)) + ")", values)


def read_flag_off(cur):
    cur.execute("SELECT lValue FROM player.quest WHERE dwPID=0 AND szName='m2_pvpfan_off' LIMIT 1")
    row = cur.fetchone()
    return bool(row and int(row["lValue"] or 0) != 0)


def read_categories(cur):
    cur.execute("SELECT * FROM player.pvpfan_category ORDER BY id")
    cats = cur.fetchall()
    for cat in cats:
        cur.execute("SELECT * FROM player.pvpfan_team WHERE category_id=%s ORDER BY idx, id", (cat["id"],))
        cat["teams"] = cur.fetchall()
        cur.execute("SELECT * FROM player.pvpfan_slot WHERE category_id=%s ORDER BY sort, id", (cat["id"],))
        slots = cur.fetchall()
        for team in cat["teams"]:
            team["slots"] = [s for s in slots if s["team_id"] == team["id"]]
            team["wanted"] = sum(int(s["count"]) for s in team["slots"])
            team["label"] = team_label(team["slots"])
        cur.execute("SELECT COUNT(*) AS n FROM player.pvpfan_char WHERE category_id=%s AND retired=0", (cat["id"],))
        cat["chars"] = int(cur.fetchone()["n"])
        cat["wanted"] = sum(t["wanted"] for t in cat["teams"])
        cat["state_name"] = STATES.get(cat["state"], cat["state"])
        cat["busy"] = cat["state"] not in ("idle",)
        cat["vs"] = " vs ".join(t["label"] for t in cat["teams"])
    return cats


def read_sets(cur):
    cur.execute("SELECT s.*, (SELECT COUNT(*) FROM player.pvpfan_set_item i WHERE i.set_id=s.id AND i.vnum>0) AS items "
                "FROM player.pvpfan_set s ORDER BY (s.preset_key='') , s.job, s.skill_group, s.id")
    sets = cur.fetchall()
    for s in sets:
        job = int(s["job"])
        s["class_name"] = (CLASSES.get(job, "każda klasa") + (" " + PATHS.get((job, int(s["skill_group"])), "")
                           if job in CLASSES and int(s["skill_group"]) else "")).strip()
    return sets


def generate_characters(cur, cat_id, max_cat):
    """Makes and retires the category's characters to fit its slots; (made, retired, message)."""
    cur.execute("SELECT * FROM player.pvpfan_category WHERE id=%s", (cat_id,))
    cat = cur.fetchone()
    if not cat:
        raise ValueError("Nie ma takiej kategorii.")
    if cat["state"] != "idle":
        raise ValueError("Ta kategoria właśnie walczy albo boty wchodzą/wychodzą – zatrzymaj ją i poczekaj, aż będzie bezczynna.")
    cur.execute("SELECT * FROM player.pvpfan_team WHERE category_id=%s ORDER BY idx, id", (cat_id,))
    teams = {t["id"]: t for t in cur.fetchall()}
    cur.execute("SELECT * FROM player.pvpfan_slot WHERE category_id=%s ORDER BY sort, id", (cat_id,))
    slots = [s for s in cur.fetchall() if s["team_id"] in teams]
    wanted = sum(int(s["count"]) for s in slots)
    if wanted > max_cat:
        raise ValueError(f"Kategoria chce {wanted} postaci – limit to {max_cat} (M2_PVPFAN_MAX_CATEGORY).")
    cur.execute("SELECT c.*, IFNULL(pi.empire,0) AS empire, IFNULL(p.job, 255) AS race FROM player.pvpfan_char c "
                "LEFT JOIN player.player p ON p.id=c.pid LEFT JOIN player.player_index pi ON pi.id=c.account_id "
                "WHERE c.category_id=%s AND c.retired=0 ORDER BY c.seq", (cat_id,))
    existing = cur.fetchall()
    by_slot = {}
    for c in existing:
        by_slot.setdefault(c["slot_id"], []).append(c)
    retire, create = [], []
    slot_ids = {s["id"] for s in slots}
    for c in existing:
        if c["slot_id"] not in slot_ids:
            retire.append(c["pid"])
    for s in slots:
        team = teams[s["team_id"]]
        empire = int(team["empire"]) or default_empire(team["idx"])
        race = RACE_BY_JOB_SEX[(int(s["job"]), s["sex"])]
        mine = by_slot.get(s["id"], [])
        keep = [c for c in mine if int(c["race"]) == race and int(c["empire"]) == empire]
        retire += [c["pid"] for c in mine if c not in keep]
        if len(keep) > int(s["count"]):
            retire += [c["pid"] for c in keep[int(s["count"]):]]
            keep = keep[:int(s["count"])]
        for _ in range(int(s["count"]) - len(keep)):
            create.append((s, team, empire, race))
    if retire:
        cur.execute("UPDATE player.pvpfan_char SET retired=1 WHERE pid IN (" + ",".join(["%s"] * len(retire)) + ")", retire)
    # Logins and names: the next free numbers; names <prefix><n> unique in player.player.
    cur.execute("SELECT seq FROM player.pvpfan_char")
    used_seq = {int(r["seq"]) for r in cur.fetchall()}
    cur.execute("SELECT login FROM account.account WHERE login LIKE 'playerbot\\_pf%%'")
    used_logins = {r["login"] for r in cur.fetchall()}
    seq = 0
    made = 0
    name_cache = {}
    for s, team, empire, race in create:
        while True:
            seq += 1
            if seq > 99999:
                raise ValueError("Brak wolnych numerów kont playerbot_pf (usuń stare postacie).")
            login = "%s%04d" % (LOGIN_PREFIX, seq)
            if seq not in used_seq and login not in used_logins and len(login) <= 16:
                break
        prefix = (team["name_prefix"] or PATH_TAGS[(int(s["job"]), int(s["skill_group"]))])[:12]
        if prefix not in name_cache:
            cur.execute("SELECT name FROM player.player WHERE name LIKE %s", (prefix + "%",))
            name_cache[prefix] = {r["name"].lower() for r in cur.fetchall()}
        n = 1
        while (prefix + str(n)).lower() in name_cache[prefix] or len(prefix + str(n)) > 16:
            n += 1
            if len(prefix + str(n)) > 16:
                raise ValueError(f"Za długi przedrostek nazw „{prefix}”.")
        name = prefix + str(n)
        name_cache[prefix].add(name.lower())
        st, ht, dx, iq, hp, mp = JOB_STARTS[int(s["job"])]
        if int(cat["map_index"]) > 0 and int(cat["x"]) > 0:
            x, y, map_index = int(cat["x"]), int(cat["y"]), int(cat["map_index"])
        else:
            x, y, map_index = EMPIRE_STARTS[empire]
        cur.execute("INSERT INTO account.account (login, password, social_id, email, create_time, status, availDt, last_play) "
                    "VALUES (%s, '!', %s, '', UTC_TIMESTAMP(), 'BLOCK', UTC_TIMESTAMP(), UTC_TIMESTAMP())",
                    (login, "7%012d" % seq))
        account_id = cur.lastrowid
        cur.execute("""INSERT INTO player.player
          (account_id,name,job,dir,x,y,map_index,exit_x,exit_y,exit_map_index,hp,mp,stamina,random_hp,random_sp,level,st,ht,dx,iq,
           stat_point,skill_point,sub_skill_point,part_main,part_base,part_hair,skill_group,horse_hp,horse_stamina,horse_level,
           horse_hp_droptime,horse_riding,horse_skill_point)
          VALUES (%s,%s,%s,0,%s,%s,%s,%s,%s,%s,%s,%s,1000,0,0,1,%s,%s,%s,%s,0,0,0,0,0,0,%s,0,0,0,0,0,0)""",
                    (account_id, name, race, x, y, map_index, x, y, map_index, hp, mp, st, ht, dx, iq, int(s["skill_group"])))
        pid = cur.lastrowid
        cur.execute("INSERT INTO player.player_index (id, pid1, empire) VALUES (%s,%s,%s)", (account_id, pid, empire))
        cur.execute("INSERT INTO player.pvpfan_char (pid, account_id, category_id, team_id, slot_id, seq, name, job) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", (pid, account_id, cat_id, team["id"], s["id"], seq, name, race))
        used_seq.add(seq)
        used_logins.add(login)
        made += 1
    return made, len(retire)


def cleanup_retired(cur, limit=300):
    """Deletes retired characters offline for CLEANUP_MINUTES (and their account, items, flags); how many."""
    cur.execute("SELECT c.pid, c.account_id FROM player.pvpfan_char c LEFT JOIN player.player p ON p.id=c.pid "
                "LEFT JOIN player.pvpfan_category k ON k.id=c.category_id "
                "WHERE c.retired=1 AND (p.id IS NULL OR p.last_play < NOW() - INTERVAL %s MINUTE) "
                "AND (k.id IS NULL OR k.state='idle') LIMIT %s", (CLEANUP_MINUTES, limit))
    gone = cur.fetchall()
    for c in gone:
        pid, acc = int(c["pid"]), int(c["account_id"])
        cur.execute("DELETE FROM player.item WHERE owner_id=%s AND `window` NOT IN ('SAFEBOX','MALL')", (pid,))
        cur.execute("DELETE FROM player.item WHERE owner_id=%s AND `window` IN ('SAFEBOX','MALL')", (acc,))
        for table, col in (("player.affect", "dwPID"), ("player.quest", "dwPID")):
            try:
                cur.execute(f"DELETE FROM {table} WHERE {col}=%s", (pid,))
            except Exception:
                pass
        cur.execute("DELETE FROM player.player WHERE id=%s AND account_id=%s", (pid, acc))
        cur.execute("DELETE FROM player.player_index WHERE id=%s", (acc,))
        cur.execute("DELETE FROM account.account WHERE id=%s AND login LIKE 'playerbot\\_pf%%' AND password='!'", (acc,))
        cur.execute("DELETE FROM player.pvpfan_char WHERE pid=%s", (pid,))
    return len(gone)


def install(app, db, login_required, csrf_token, game_text=None, map_names=None, map_bounds=None, icon_url=None):
    from flask import abort, flash, jsonify, redirect, render_template, request, session, url_for

    map_names = map_names or {}
    map_bounds = map_bounds or {}
    text = game_text or (lambda value: value or "")
    icon = icon_url or (lambda vnum: None)

    def check_csrf():
        expected = session.get("seban_update_csrf", "")
        if not expected or not secrets.compare_digest(request.form.get("pf_csrf", ""), expected):
            abort(400, "Odśwież stronę i spróbuj ponownie.")

    def pending_commands(cur, cat_id=None):
        cur.execute("SELECT c.*, k.name AS category_name FROM player.pvpfan_command c LEFT JOIN player.pvpfan_category k "
                    "ON k.id=c.category_id " + ("WHERE c.category_id=%s " if cat_id else "") +
                    "ORDER BY c.id DESC LIMIT 12", (cat_id,) if cat_id else ())
        cmds = cur.fetchall()
        for c in cmds:
            c["cmd_name"] = CMD_NAMES.get(c["cmd"], c["cmd"])
        return cmds

    def wars(cur, cat_id=None, limit=20):
        cur.execute("SELECT * FROM player.pvpfan_war " + ("WHERE category_id=%s " if cat_id else "") +
                    "ORDER BY id DESC LIMIT %s", ((cat_id, limit) if cat_id else (limit,)))
        found = cur.fetchall()
        for w in found:
            cur.execute("SELECT * FROM player.pvpfan_war_team WHERE war_id=%s ORDER BY idx", (w["id"],))
            w["teams"] = cur.fetchall()
            d = int(w["duration_sec"] or 0)
            w["clock"] = f"{d // 60}:{d % 60:02d}"
        return found

    def queue(cur, cat_id, cmd):
        cur.execute("INSERT INTO player.pvpfan_command (category_id, cmd, source) VALUES (%s,%s,'panel')", (cat_id, cmd))

    def make_category(cur, name, code, composition):
        teams = parse_composition(composition)
        cur.execute("SELECT id FROM player.pvpfan_category WHERE code=%s", (code,))
        if cur.fetchone():
            raise ValueError(f"Kod „{code}” jest już zajęty – wpisz inny.")
        cur.execute("INSERT INTO player.pvpfan_category (code, name) VALUES (%s,%s)", (code, name))
        cat_id = cur.lastrowid
        for i, slots in enumerate(teams, 1):
            label = " + ".join(PATHS[(job, group)] for _c, job, group in slots)
            cur.execute("INSERT INTO player.pvpfan_team (category_id, idx, name, empire) VALUES (%s,%s,%s,%s)",
                        (cat_id, i, label[:32], default_empire(i)))
            team_id = cur.lastrowid
            for k, (count, job, group) in enumerate(slots):
                cur.execute("INSERT INTO player.pvpfan_slot (category_id, team_id, job, skill_group, sex, count, sort) "
                            "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                            (cat_id, team_id, job, group, "female" if job in (1, 3) else "male", count, k))
        return cat_id

    # ------------------------------------------------------------------ hub

    @app.route("/events/pvp-fan", methods=["GET", "POST"])
    @login_required
    def pvpfan():
        with db() as con, con.cursor() as cur:
            if not tables_ready(cur):
                return render_template("pvpfan.html", missing=True, pf_csrf=csrf_token())
            if request.method == "POST":
                check_csrf()
                action = request.form.get("action", "")
                try:
                    if action == "new":
                        name = (request.form.get("name") or "").strip()[:64]
                        if not name:
                            raise ValueError("Wpisz nazwę kategorii.")
                        code = (request.form.get("code") or "").strip().lower() or slugify(name)
                        if not CODE_RE.match(code):
                            raise ValueError("Kod: małe litery, cyfry, _ i -, do 32 znaków (wpisuje się go w /pvpfan start <kod>).")
                        cat_id = make_category(cur, name, code, request.form.get("composition", ""))
                        flash(f"Utworzono kategorię „{name}” (kod {code}). Ustaw arenę i wygeneruj postacie.", "success")
                        return redirect(url_for("pvpfan_category", cat_id=cat_id))
                    if action == "switch":
                        off = request.form.get("off") == "1"
                        cur.execute("REPLACE INTO player.quest (dwPID, szName, szState, lValue) VALUES (0, 'm2_pvpfan_off', '', %s)",
                                    (1 if off else 0,))
                        flash("PVP Fan wyłączony – gra nie zacznie nowej wojny, trwające zatrzyma (w ciągu 10 s)." if off
                              else "PVP Fan włączony.", "success")
                    elif action in ("start", "ready", "stop"):
                        cat_id = number(request.form.get("id"), "Kategoria", 1, 2 ** 31)
                        queue(cur, cat_id, action)
                        flash(f"Polecenie „{CMD_NAMES[action]}” w kolejce – rdzeń areny odbierze je w ciągu kilku sekund.", "success")
                    elif action == "cleanup":
                        flash(f"Usunięto {cleanup_retired(cur, 2000)} wycofanych postaci.", "success")
                    elif action == "presets":
                        ensure_presets(cur)
                        flash("Presety zestawów są na miejscu.", "success")
                    else:
                        abort(400, "Nieznana akcja.")
                except ValueError as exc:
                    flash(str(exc), "error")
                return redirect(url_for("pvpfan"))
            ensure_presets(cur)
            try:
                cleaned = cleanup_retired(cur)
            except Exception:
                cleaned = 0
            cats = read_categories(cur)
            off = read_flag_off(cur)
            cur.execute("SELECT COUNT(*) AS n, COALESCE(SUM(retired),0) AS retired FROM player.pvpfan_char")
            counts = cur.fetchone()
            return render_template("pvpfan.html", missing=False, cats=cats, off=off, counts=counts, cleaned=cleaned,
                                   commands=pending_commands(cur), wars=wars(cur), sets=read_sets(cur),
                                   env_on=os.environ.get("M2_PVPFAN", "1") != "0", max_cat=max_per_category(),
                                   map_names=map_names, pf_csrf=csrf_token())

    # ------------------------------------------------------------------ one category

    def save_category_form(cur, cat_id, form):
        code = (form.get("code") or "").strip().lower()
        if not CODE_RE.match(code):
            raise ValueError("Kod: małe litery, cyfry, _ i -, do 32 znaków.")
        cur.execute("SELECT id FROM player.pvpfan_category WHERE code=%s AND id<>%s", (code, cat_id))
        if cur.fetchone():
            raise ValueError(f"Kod „{code}” ma już inna kategoria.")
        map_index = number(form.get("map_index"), "Mapa", 0, 99999)
        x = number(form.get("x"), "X", 0, 10 ** 8)
        y = number(form.get("y"), "Y", 0, 10 ** 8)
        lx, ly = (form.get("local_x") or "").strip(), (form.get("local_y") or "").strip()
        if lx and ly and map_index in map_bounds:
            base_x, base_y = map_bounds[map_index][0], map_bounds[map_index][1]
            x = base_x + number(lx, "X lokalne", 0, 10 ** 5) * 100
            y = base_y + number(ly, "Y lokalne", 0, 10 ** 5) * 100
        values = {
            "code": code, "name": (form.get("name") or code).strip()[:64], "enabled": 1 if form.get("enabled") else 0,
            "map_index": map_index, "x": x, "y": y,
            "radius": number(form.get("radius"), "Odległość drużyn od środka", 200, 20000),
            "arena_radius": number(form.get("arena_radius"), "Promień areny", 1000, 50000),
            "channel": number(form.get("channel"), "Kanał", 1, 4),
            "countdown_sec": number(form.get("countdown_sec"), "Odliczanie", 0, 60),
            "max_minutes": number(form.get("max_minutes"), "Limit czasu", 1, 180),
            "exit_sec": number(form.get("exit_sec"), "Wyjście po walce", 0, 600),
            "allow_players": 1 if form.get("allow_players") else 0,
            "potions": 1 if form.get("potions") else 0,
        }
        # MT2009_PLUS_PVPFAN_TACTICS_V1: the tactics' columns, once pvpfan.sql has added them (a panel ahead of the
        # migration saves the rest as before).
        cur.execute("SELECT COUNT(*) AS n FROM information_schema.COLUMNS WHERE TABLE_SCHEMA='player' "
                    "AND TABLE_NAME='pvpfan_category' AND COLUMN_NAME IN ('tactics','squad_size','kite_distance','retreat_hp')")
        if int(cur.fetchone()["n"]) == 4:
            kite = number(form.get("kite_distance") or 0, "Dystans uciekania", 0, 900)
            retreat = number(form.get("retreat_hp") or 0, "Odwrót przy HP %", 0, 80)
            values.update({
                "tactics": 1 if form.get("tactics") else 0,
                "squad_size": number(form.get("squad_size") or 5, "Wielkość oddziału", 2, 12),
                "kite_distance": 0 if kite == 0 else max(150, kite),
                "retreat_hp": 0 if retreat == 0 else max(5, retreat),
            })
        cur.execute("UPDATE player.pvpfan_category SET " + ", ".join(f"{k}=%s" for k in values) + " WHERE id=%s",
                    tuple(values.values()) + (cat_id,))

    def slot_values(form, prefix=""):
        jg = (form.get(prefix + "jobgroup") or "0:1").split(":")
        job = number(jg[0], "Klasa", 0, 3)
        group = number(jg[1] if len(jg) > 1 else 1, "Ścieżka", 1, 2)
        sex = form.get(prefix + "sex", "male")
        if sex not in ("male", "female"):
            sex = "male"
        values = {"job": job, "skill_group": group, "sex": sex,
                  "count": number(form.get(prefix + "count"), "Liczba postaci", 1, 500),
                  "level": number(form.get(prefix + "level"), "Poziom", 1, 250),
                  "skill_level": number(form.get(prefix + "skill_level"), "Poziom umiejętności", 0, 40),
                  "set_id": number(form.get(prefix + "set_id") or 0, "Zestaw", 0, 2 ** 31)}
        for stat in ("st", "ht", "dx", "iq"):
            values[stat] = number(form.get(prefix + stat) or 0, stat.upper(), 0, 90)
        return values

    @app.route("/events/pvp-fan/kategoria/<int:cat_id>", methods=["GET", "POST"])
    @login_required
    def pvpfan_category(cat_id):
        with db() as con, con.cursor() as cur:
            if not tables_ready(cur):
                return redirect(url_for("pvpfan"))
            cur.execute("SELECT * FROM player.pvpfan_category WHERE id=%s", (cat_id,))
            cat = cur.fetchone()
            if not cat:
                abort(404)
            if request.method == "POST":
                check_csrf()
                action = request.form.get("action", "")
                anchor = ""
                try:
                    if action == "save":
                        save_category_form(cur, cat_id, request.form)
                        flash("Zapisano ustawienia kategorii. Działa od następnego /pvpfan start.", "success")
                        anchor = "ustawienia"
                    elif action == "gm_pos":
                        cur.execute("SELECT * FROM player.pvpfan_gm_pos ORDER BY at DESC LIMIT 1")
                        pos = cur.fetchone()
                        if not pos:
                            raise ValueError("Brak zapisanej pozycji – w grze wpisz /pvpfan pozycja.")
                        cur.execute("UPDATE player.pvpfan_category SET map_index=%s, x=%s, y=%s WHERE id=%s",
                                    (pos["map_index"], pos["x"], pos["y"], cat_id))
                        flash(f"Środek areny = pozycja {pos['gm_name']} (mapa {pos['map_index']}, {pos['x']}, {pos['y']}).", "success")
                        anchor = "ustawienia"
                    elif action == "save_team":
                        team_id = number(request.form.get("team_id"), "Drużyna", 1, 2 ** 31)
                        prefix = (request.form.get("name_prefix") or "").strip()
                        if prefix and not NAME_RE.match(prefix):
                            raise ValueError("Przedrostek nazw: 2–12 liter i cyfr (bez polskich znaków), zaczyna się literą.")
                        cur.execute("UPDATE player.pvpfan_team SET name=%s, empire=%s, x=%s, y=%s, name_prefix=%s "
                                    "WHERE id=%s AND category_id=%s",
                                    ((request.form.get("name") or "Drużyna").strip()[:32],
                                     number(request.form.get("empire"), "Królestwo", 0, 3),
                                     number(request.form.get("x") or 0, "X", 0, 10 ** 8),
                                     number(request.form.get("y") or 0, "Y", 0, 10 ** 8), prefix, team_id, cat_id))
                        flash("Zapisano drużynę. Zmiana królestwa – wygeneruj postacie ponownie.", "success")
                        anchor = "druzyny"
                    elif action == "add_team":
                        cur.execute("SELECT COUNT(*) AS n, COALESCE(MAX(idx),0) AS m FROM player.pvpfan_team WHERE category_id=%s", (cat_id,))
                        row = cur.fetchone()
                        if int(row["n"]) >= MAX_TEAMS:
                            raise ValueError(f"Najwyżej {MAX_TEAMS} drużyn.")
                        idx = int(row["m"]) + 1
                        cur.execute("INSERT INTO player.pvpfan_team (category_id, idx, name, empire) VALUES (%s,%s,%s,%s)",
                                    (cat_id, idx, f"Drużyna {idx}", default_empire(idx)))
                        flash("Dodano drużynę – dodaj jej postacie.", "success")
                        anchor = "druzyny"
                    elif action == "delete_team":
                        team_id = number(request.form.get("team_id"), "Drużyna", 1, 2 ** 31)
                        cur.execute("UPDATE player.pvpfan_char SET retired=1 WHERE team_id=%s AND category_id=%s", (team_id, cat_id))
                        cur.execute("DELETE FROM player.pvpfan_slot WHERE team_id=%s AND category_id=%s", (team_id, cat_id))
                        cur.execute("DELETE FROM player.pvpfan_team WHERE id=%s AND category_id=%s", (team_id, cat_id))
                        flash("Usunięto drużynę (jej postacie są wycofane).", "success")
                        anchor = "druzyny"
                    elif action == "add_slot":
                        team_id = number(request.form.get("team_id"), "Drużyna", 1, 2 ** 31)
                        cur.execute("SELECT COUNT(*) AS n FROM player.pvpfan_slot WHERE team_id=%s", (team_id,))
                        if int(cur.fetchone()["n"]) >= MAX_SLOTS_PER_TEAM:
                            raise ValueError(f"Najwyżej {MAX_SLOTS_PER_TEAM} wierszy w drużynie.")
                        v = slot_values(request.form)
                        cur.execute("INSERT INTO player.pvpfan_slot (category_id, team_id, " + ", ".join(v) + ", sort) VALUES ("
                                    + ",".join(["%s"] * (len(v) + 3)) + ")", (cat_id, team_id, *v.values(), 99))
                        flash("Dodano postacie do drużyny – „Generuj postacie”, by je utworzyć.", "success")
                        anchor = "druzyny"
                    elif action == "save_slot":
                        slot_id = number(request.form.get("slot_id"), "Wiersz", 1, 2 ** 31)
                        v = slot_values(request.form)
                        cur.execute("UPDATE player.pvpfan_slot SET " + ", ".join(f"{k}=%s" for k in v) +
                                    " WHERE id=%s AND category_id=%s", (*v.values(), slot_id, cat_id))
                        flash("Zapisano. Klasa, płeć albo liczba się zmieniły? – „Generuj postacie”. Poziom, statystyki, "
                              "umiejętności i zestaw działają od następnego startu.", "success")
                        anchor = "druzyny"
                    elif action == "delete_slot":
                        slot_id = number(request.form.get("slot_id"), "Wiersz", 1, 2 ** 31)
                        cur.execute("UPDATE player.pvpfan_char SET retired=1 WHERE slot_id=%s AND category_id=%s", (slot_id, cat_id))
                        cur.execute("DELETE FROM player.pvpfan_slot WHERE id=%s AND category_id=%s", (slot_id, cat_id))
                        flash("Usunięto wiersz (jego postacie są wycofane).", "success")
                        anchor = "druzyny"
                    elif action == "generate":
                        made, retired = generate_characters(cur, cat_id, max_per_category())
                        flash(f"Postacie gotowe: utworzono {made}, wycofano {retired}. Wycofane znikną po {CLEANUP_MINUTES} min offline.",
                              "success")
                        anchor = "postacie"
                    elif action == "retire_all":
                        if cat["state"] != "idle":
                            raise ValueError("Najpierw zatrzymaj walkę.")
                        cur.execute("UPDATE player.pvpfan_char SET retired=1 WHERE category_id=%s", (cat_id,))
                        flash("Wszystkie postacie tej kategorii wycofane.", "success")
                        anchor = "postacie"
                    elif action in ("start", "ready", "stop"):
                        queue(cur, cat_id, action)
                        flash(f"Polecenie „{CMD_NAMES[action]}” w kolejce – rdzeń areny odbierze je w ciągu kilku sekund.", "success")
                        anchor = "sterowanie"
                    elif action == "reset_state":
                        cur.execute("UPDATE player.pvpfan_category SET state='idle', state_note='Stan wyczyszczony w panelu', "
                                    "online=0, core='' WHERE id=%s", (cat_id,))
                        flash("Stan ustawiony na bezczynny (użyj tylko, gdy rdzeń areny nie działa – inaczej Stop).", "success")
                        anchor = "sterowanie"
                    elif action == "delete":
                        if cat["state"] != "idle":
                            raise ValueError("Najpierw zatrzymaj walkę.")
                        cur.execute("UPDATE player.pvpfan_char SET retired=1 WHERE category_id=%s", (cat_id,))
                        cur.execute("DELETE FROM player.pvpfan_slot WHERE category_id=%s", (cat_id,))
                        cur.execute("DELETE FROM player.pvpfan_team WHERE category_id=%s", (cat_id,))
                        cur.execute("DELETE FROM player.pvpfan_category WHERE id=%s", (cat_id,))
                        flash("Usunięto kategorię (postacie znikną po kwadransie offline).", "success")
                        return redirect(url_for("pvpfan"))
                    else:
                        abort(400, "Nieznana akcja.")
                except ValueError as exc:
                    flash(str(exc), "error")
                return redirect(url_for("pvpfan_category", cat_id=cat_id, _anchor=anchor or None))
            cat = [c for c in read_categories(cur) if c["id"] == cat_id][0]
            cur.execute("SELECT c.slot_id, COUNT(*) AS n FROM player.pvpfan_char c WHERE c.category_id=%s AND c.retired=0 "
                        "GROUP BY c.slot_id", (cat_id,))
            made = {r["slot_id"]: int(r["n"]) for r in cur.fetchall()}
            cur.execute("SELECT c.name, c.team_id, c.slot_id, p.level, p.last_play FROM player.pvpfan_char c "
                        "LEFT JOIN player.player p ON p.id=c.pid WHERE c.category_id=%s AND c.retired=0 ORDER BY c.team_id, c.seq "
                        "LIMIT 40", (cat_id,))
            sample = cur.fetchall()
            cur.execute("SELECT * FROM player.pvpfan_gm_pos ORDER BY at DESC LIMIT 1")
            gm_pos = cur.fetchone()
            return render_template("pvpfan_category.html", cat=cat, made=made, sample=sample, gm_pos=gm_pos,
                                   sets=read_sets(cur), commands=pending_commands(cur, cat_id), wars=wars(cur, cat_id, 15),
                                   classes=CLASSES, paths=PATHS, skill_levels=SKILL_LEVELS, empires=EMPIRE_NAMES,
                                   default_empire=default_empire, map_names=map_names, map_bounds=map_bounds,
                                   max_cat=max_per_category(), pf_csrf=csrf_token())

    # ------------------------------------------------------------------ equipment sets

    def read_set(cur, set_id):
        cur.execute("SELECT * FROM player.pvpfan_set WHERE id=%s", (set_id,))
        s = cur.fetchone()
        if not s:
            return None, {}
        cur.execute("SELECT * FROM player.pvpfan_set_item WHERE set_id=%s", (set_id,))
        items = {r["slot"]: r for r in cur.fetchall()}
        vnums = [int(r["vnum"]) for r in items.values() if int(r["vnum"] or 0) > 0]
        names = {}
        if vnums:
            cur.execute("SELECT vnum, name, locale_name FROM player.item_proto WHERE vnum IN (" + ",".join(["%s"] * len(vnums)) + ")",
                        vnums)
            names = {int(r["vnum"]): text(r["locale_name"] or r["name"]) for r in cur.fetchall()}
        for r in items.values():
            r["item_name"] = names.get(int(r["vnum"] or 0), "")
        return s, items

    def bonus_tables(cur):
        """{col: {"normal": [[point, max]], "rare": [[point, max]]}} for the set editor's selects."""
        from dbeditor.items import POINT_LABELS
        out = {col: {"normal": [], "rare": []} for col in ATTR_COLS}
        for kind, table in (("normal", "world.item_attr"), ("rare", "world.item_attr_rare")):
            try:
                cur.execute(f"SHOW COLUMNS FROM {table}")
                cols = {r["Field"] for r in cur.fetchall()}
                usable = [c for c in ATTR_COLS if c in cols]
                cur.execute(f"SELECT apply+0 AS point, lv1, lv2, lv3, lv4, lv5, " + ", ".join(f"`{c}`" for c in usable)
                            + f" FROM {table} ORDER BY apply+0")
                for r in cur.fetchall():
                    for c in usable:
                        level = int(r[c] or 0)
                        if level > 0:
                            out[c][kind].append([int(r["point"]), int(r["lv%d" % min(5, level)] or 0)])
            except Exception:
                continue
        labels = {int(k): v[0] + (" " + v[1] if v[1] else "") for k, v in POINT_LABELS.items() if int(k) > 0}
        return out, labels

    def save_set_form(cur, set_id, form):
        values = {"name": (form.get("name") or "Zestaw").strip()[:64],
                  "job": number(form.get("job"), "Klasa", 0, 255),
                  "skill_group": number(form.get("skill_group") or 0, "Ścieżka", 0, 2),
                  "red_vnum": number(form.get("red_vnum") or 0, "Czerwone mikstury", 0, 2 ** 31),
                  "red_count": number(form.get("red_count") or 0, "Ile czerwonych", 0, 2000),
                  "blue_vnum": number(form.get("blue_vnum") or 0, "Niebieskie mikstury", 0, 2 ** 31),
                  "blue_count": number(form.get("blue_count") or 0, "Ile niebieskich", 0, 2000),
                  "note": (form.get("note") or "").strip()[:255]}
        cur.execute("UPDATE player.pvpfan_set SET " + ", ".join(f"{k}=%s" for k in values) + " WHERE id=%s",
                    (*values.values(), set_id))
        problems = []
        for key, label, col, item_type, subtypes in SLOTS:
            vnum = number(form.get(f"{key}_vnum") or 0, f"{label}: VNUM", 0, 2 ** 31)
            if vnum <= 0:
                cur.execute("DELETE FROM player.pvpfan_set_item WHERE set_id=%s AND slot=%s", (set_id, key))
                continue
            cur.execute("SELECT type, subtype FROM player.item_proto WHERE vnum=%s", (vnum,))
            proto = cur.fetchone()
            if not proto:
                problems.append(f"{label}: nie ma przedmiotu {vnum}")
                continue
            if int(proto["type"]) != item_type or (subtypes and int(proto["subtype"]) not in subtypes):
                problems.append(f"{label}: przedmiot {vnum} nie pasuje do tego miejsca")
                continue
            row = [number(form.get(f"{key}_count") or 1, f"{label}: ilość", 1, 200)]
            row += [number(form.get(f"{key}_s{i}") or 0, f"{label}: kamień {i + 1}", -2 ** 31, 2 ** 31 - 1) for i in range(3)]
            for i in range(7):
                point = number(form.get(f"{key}_a{i}t") or 0, f"{label}: bonus {i + 1}", 0, 511)
                value = number(form.get(f"{key}_a{i}v") or 0, f"{label}: wartość bonusu {i + 1}", -32768, 32767)
                row += [point, value if point else 0]
            cur.execute("REPLACE INTO player.pvpfan_set_item (set_id, slot, vnum, count, socket0, socket1, socket2, "
                        + ", ".join(f"attrtype{i}, attrvalue{i}" for i in range(7)) + ") VALUES ("
                        + ",".join(["%s"] * (len(row) + 3)) + ")", (set_id, key, vnum, *row))
        return problems

    @app.route("/events/pvp-fan/zestaw/<int:set_id>", methods=["GET", "POST"])
    @login_required
    def pvpfan_set(set_id):
        with db() as con, con.cursor() as cur:
            if not tables_ready(cur):
                return redirect(url_for("pvpfan"))
            s, items = read_set(cur, set_id)
            if not s:
                abort(404)
            if request.method == "POST":
                check_csrf()
                action = request.form.get("action", "save")
                try:
                    if action == "save":
                        problems = save_set_form(cur, set_id, request.form)
                        if problems:
                            flash("Zapisano, poza: " + "; ".join(problems) + ".", "error")
                        else:
                            flash("Zapisano zestaw. Boty założą go przy następnym /pvpfan start.", "success")
                    elif action == "copy":
                        cur.execute("INSERT INTO player.pvpfan_set (name, job, skill_group, red_vnum, red_count, blue_vnum, "
                                    "blue_count, note) SELECT CONCAT(LEFT(name,56),' (kopia)'), job, skill_group, red_vnum, "
                                    "red_count, blue_vnum, blue_count, note FROM player.pvpfan_set WHERE id=%s", (set_id,))
                        new_id = cur.lastrowid
                        cur.execute("INSERT INTO player.pvpfan_set_item (set_id, slot, vnum, count, socket0, socket1, socket2, "
                                    + ", ".join(f"attrtype{i}, attrvalue{i}" for i in range(7)) + ") SELECT %s, slot, vnum, count, "
                                    "socket0, socket1, socket2, " + ", ".join(f"attrtype{i}, attrvalue{i}" for i in range(7))
                                    + " FROM player.pvpfan_set_item WHERE set_id=%s", (new_id, set_id))
                        flash("Skopiowano zestaw – to jest kopia.", "success")
                        return redirect(url_for("pvpfan_set", set_id=new_id))
                    elif action == "restore":
                        if not s["preset_key"]:
                            raise ValueError("To nie jest preset.")
                        ensure_presets(cur, force_key=s["preset_key"])
                        flash("Przywrócono preset.", "success")
                    elif action == "delete":
                        if s["preset_key"]:
                            raise ValueError("Presetu nie można usunąć (można go zmienić albo przywrócić).")
                        cur.execute("UPDATE player.pvpfan_slot SET set_id=0 WHERE set_id=%s", (set_id,))
                        cur.execute("DELETE FROM player.pvpfan_set_item WHERE set_id=%s", (set_id,))
                        cur.execute("DELETE FROM player.pvpfan_set WHERE id=%s", (set_id,))
                        flash("Usunięto zestaw (postacie, które go miały, wracają do presetu klasy).", "success")
                        return redirect(url_for("pvpfan", _anchor="zestawy"))
                    else:
                        abort(400, "Nieznana akcja.")
                except ValueError as exc:
                    flash(str(exc), "error")
                return redirect(url_for("pvpfan_set", set_id=set_id))
            tables, labels = bonus_tables(cur)
            cur.execute("SELECT vnum, name, locale_name FROM player.item_proto WHERE type=10 ORDER BY vnum DESC LIMIT 400")
            stones = [{"vnum": int(r["vnum"]), "name": text(r["locale_name"] or r["name"])} for r in cur.fetchall()]
            cur.execute("SELECT COUNT(*) AS n FROM player.pvpfan_slot WHERE set_id=%s", (set_id,))
            used = int(cur.fetchone()["n"])
            return render_template("pvpfan_set.html", s=s, items=items, slots=SLOTS, tables=tables, labels=labels,
                                   stones=stones, used=used, classes=CLASSES, paths=PATHS, pf_csrf=csrf_token())

    @app.post("/events/pvp-fan/zestaw/nowy")
    @login_required
    def pvpfan_set_new():
        check_csrf()
        with db() as con, con.cursor() as cur:
            cur.execute("INSERT INTO player.pvpfan_set (name, note) VALUES (%s, '')",
                        ((request.form.get("name") or "Nowy zestaw").strip()[:64],))
            new_id = cur.lastrowid
        flash("Nowy pusty zestaw – wybierz przedmioty.", "success")
        return redirect(url_for("pvpfan_set", set_id=new_id))

    @app.get("/events/pvp-fan/api/przedmioty")
    @login_required
    def pvpfan_api_items():
        q = (request.args.get("q") or "").strip()[:60]
        key = request.args.get("slot", "")
        where, params = [], []
        if key in SLOT:
            _k, _l, _c, item_type, subtypes = SLOT[key]
            where.append("type=%s")
            params.append(item_type)
            if subtypes:
                where.append("subtype IN (" + ",".join(["%s"] * len(subtypes)) + ")")
                params += list(subtypes)
        if q.isdigit():
            where.append("(vnum=%s OR vnum DIV 10=%s DIV 10)")
            params += [int(q), int(q)]
        elif q:
            where.append("(locale_name LIKE %s OR name LIKE %s)")
            params += [f"%{q}%", f"%{q}%"]
        with db() as con, con.cursor() as cur:
            cur.execute("SELECT vnum, name, locale_name, limitvalue0 FROM player.item_proto" +
                        (" WHERE " + " AND ".join(where) if where else "") + " ORDER BY limitvalue0 DESC, vnum DESC LIMIT 60",
                        params)
            found = [{"vnum": int(r["vnum"]), "name": text(r["locale_name"] or r["name"]), "level": int(r["limitvalue0"] or 0),
                      "icon": icon(r["vnum"])} for r in cur.fetchall()]
        return jsonify(ok=True, items=found)

    @app.get("/events/pvp-fan/api/rodzina")
    @login_required
    def pvpfan_api_family():
        """The refine levels of an item: the vnums of its family (vnum // 10)."""
        try:
            vnum = int(request.args.get("vnum", "0"))
        except ValueError:
            vnum = 0
        with db() as con, con.cursor() as cur:
            cur.execute("SELECT vnum, name, locale_name FROM player.item_proto WHERE vnum BETWEEN %s AND %s ORDER BY vnum",
                        (vnum - vnum % 10, vnum - vnum % 10 + 9))
            found = [{"vnum": int(r["vnum"]), "name": text(r["locale_name"] or r["name"]), "icon": icon(r["vnum"])}
                     for r in cur.fetchall()]
        return jsonify(ok=True, items=found)
