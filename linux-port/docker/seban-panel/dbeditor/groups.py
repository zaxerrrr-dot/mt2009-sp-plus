"""MT2009_PLUS_DB_EDITOR_GROUPS_V1: "Grupy potworów" (/db/grupy) - every
monster group (group.txt) and every group of groups (group_group.txt) in one
place: who is in it (names and levels from mob_proto), on which maps and in
how many spawn points it stands, and its composition edited the way the other
file parts of the editor edit (cube.py, chests.py).

The files (share/locale/poland in the game image), as every core reads them
while it boots (mob_manager.cpp CMobManager::Initialize -> LoadGroup /
LoadGroupGroup, CTextFileLoader):

    Group <one word>          a Group line of any other length exit(1)s the core
    {
        Leader  <name> <mob>  group.txt: the leader (the name is not used)
        Vnum    <n>           the group's number (regen "g" / "r" lines use it)
        1       <name> <mob>  group.txt: one monster each, numbered from 1
        1       <group> [w]   group_group.txt: one group each; the core reads
    }                         the weight but never uses it (AddMember(vnum)) -
                              every group of a set is equally likely.

A key is read once (the first line wins), the members stop at the first
missing number, at most 255, and the first group of a number wins.

How a change reaches the game (the m2-chests way, game/bin/m2-groups):

  the panel writes only the groups the operator changed or added, whole,
  into the spool volume both containers mount:
      groups/group.custom.txt          (key "mobgroup")
      groups/group_group.custom.txt    (key "mobgroupgroup")
  and before the cores boot (m2-supervise -> boot_cores, before m2-regen and
  m2-spawns) m2-groups checks them and rebuilds each live file: the image's
  file without those groups, then the panel's. A server update brings a new
  image, the panel's files stay in the spool and are merged into the new
  image's files at the next boot - nothing to re-apply by hand; a group
  the new image changed and the panel changed too keeps the panel's version
  (the page marks it "zmieniona w panelu", "Przywróć wersję z obrazu" drops
  it). The image's files come back as groups/*.base.txt, every map's npc.txt
  as groups/base/maps/<map>/npc.txt; groups/*.status says how the last
  apply went. Backups, "pending" (the "Zastosuj" page) and the game's report
  come from dropfiles.py's machinery; every save also writes a history line
  (groups/history.jsonl) with the group before and after - "Cofnij" puts
  the one group back as it was, while nothing changed it since.

Live editing: the core reads the files only while it boots ("/reload p"
re-reads the files the core already has, on one core) - a change works
after "Zastosuj" (restart of the cores), as the page says.
"""
import hashlib
import json
import os
import re
import time
import unicodedata
from datetime import datetime
from pathlib import Path

from flask import Response, abort, flash, g, jsonify, redirect, render_template, request, url_for

from dbeditor import dropfiles as df

MARK = "MT2009_PLUS_DB_EDITOR_GROUPS_V1"
FOLDER = "groups"
KEYS = {"g": "mobgroup", "r": "mobgroupgroup"}
FILE_NAMES = {"g": "group.txt", "r": "group_group.txt"}
KIND_NAMES = {"g": "Grupa", "r": "Zestaw grup"}
MAX_MEMBERS = 255            # LoadGroup / LoadGroupGroup read the numbers 1..255
WARN_MEMBERS = 40            # a bigger group stands on one spot - a lag and a wall of monsters
MAX_WEIGHT = 1000000
VNUM_MAX = 2147483647        # GetTokenInteger reads an int
PAGE_SIZE = 50
HISTORY_KEEP = 500
MOBS_SECONDS = 120
NAME_RE = re.compile(r"^[A-Za-z0-9_()+.\-]{1,64}$")
SORTS = {"vnum": "numer", "nazwa": "nazwa", "poziom": "poziom", "rozmiar": "liczebność", "spawny": "punkty spawnu"}
SPAWN_FILES = {"regen": "regen.txt (zwykły respawn)", "boss": "boss.txt (bossowie mapy)",
               "stone": "stone.txt (Metiny)", "npc": "npc.txt", "special": "bossowie czasowi"}


# ------------------------------------------------------------ the files ---
def register_file():
    """The two files in dropfiles' table: custom path, status, backups and the
    "pending" list of /db/apply come with them."""
    df.FILES.setdefault(KEYS["g"], (FOLDER, "group.custom.txt", "group.status", "Grupy potworów (group.txt)"))
    df.FILES.setdefault(KEYS["r"], (FOLDER, "group_group.custom.txt", "group_group.status",
                                    "Zestawy grup potworów (group_group.txt)"))
    df.BASES.setdefault(KEYS["g"], (FOLDER, "group.base.txt"))
    df.BASES.setdefault(KEYS["r"], (FOLDER, "group_group.base.txt"))


def root(spool):
    return Path(spool) / FOLDER


def base_candidates(spool, kind):
    """The image's file: m2-groups' copy, else the copies m2-spawns / m2-regen
    publish of the live file (an older game image)."""
    name = FILE_NAMES[kind]
    return [root(spool) / name.replace(".txt", ".base.txt"), Path(spool) / "spawns" / "base" / name,
            Path(spool) / "regen" / "base" / name]


def custom_path(spool, kind):
    return root(spool) / FILE_NAMES[kind].replace(".txt", ".custom.txt")


def npc_path(spool, folder):
    return root(spool) / "base" / "maps" / folder / "npc.txt"


def read_latin(path):
    try:
        data = Path(path).read_bytes()
    except OSError:
        return None
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    return data.decode("latin-1")


def stamp(path):
    try:
        info = Path(path).stat()
        return (info.st_mtime_ns, info.st_size)
    except OSError:
        return None


# --------------------------------------------------------------- parsing ---
def tokens_of(line):
    from dbeditor.spawnfiles import tokens_of as split
    return split(line)


def _int(text):
    """str_to_number: the digits, else 0."""
    return int(text) if re.fullmatch(r"\d{1,10}", text or "") else 0


def parse(text, kind):
    """group.txt (kind "g") / group_group.txt ("r") -> {"blocks": [...], "problems": [...]}.

    A block: {"vnum", "name", "line", "leader": (name word, mob) | None,
    "members": [(name word, mob)] (g) or [(group, weight)] (r), "bad": [why]}
    - read the way CTextFileLoader + LoadGroup / LoadGroupGroup read them."""
    blocks, problems, current, body = [], [], None, None
    for number, raw in enumerate((text or "").split("\n"), 1):
        words = tokens_of(raw)
        if not words or words[0].startswith(("//", "#", "--")):
            continue
        key = words[0].lower()
        if current is None:
            if key == "group":
                if len(words) != 2:
                    problems.append(f"linia {number}: „Group” z {len(words) - 1} słowami nazwy – rdzeń gry się zatrzyma")
                current = {"name": words[1] if len(words) > 1 else "", "line": number, "bad": []}
                body = {}
            continue
        if words[0].startswith("{"):
            continue
        if words[0].startswith("}"):
            vnum = body.get("vnum", [""])[0]
            if not re.fullmatch(r"\d{1,10}", vnum):
                problems.append(f"linia {current['line']}: grupa „{current['name']}” bez numeru (Vnum) – gra ją pomija")
            else:
                current["vnum"] = int(vnum)
                members = []
                for k in range(1, MAX_MEMBERS + 1):
                    entry = body.get(str(k))
                    if not entry:
                        break
                    if kind == "g":
                        if len(entry) < 2:
                            current["bad"].append(f"członek {k} bez numeru potwora")
                            continue
                        members.append((entry[0], _int(entry[1])))
                    else:
                        members.append((_int(entry[0]), _int(entry[1]) if len(entry) > 1 else 1))
                current["members"] = members
                if kind == "g":
                    leader = body.get("leader")
                    if not leader or len(leader) < 2:
                        problems.append(f"grupa {vnum}: bez lidera (Leader) – gra ją pomija")
                        current = body = None
                        continue
                    current["leader"] = (leader[0], _int(leader[1]))
                else:
                    current["leader"] = None
                blocks.append(current)
            current = body = None
            continue
        if len(words) < 2:
            continue
        body.setdefault(key, words[1:])
    if current is not None:
        problems.append(f"linia {current['line']}: grupa „{current['name']}” nie jest zamknięta „}}”")
    return {"blocks": blocks, "problems": problems}


def first_by_vnum(blocks):
    """{vnum: block} - the first group of a number wins (m_map_pkMobGroup.emplace)."""
    out = {}
    for block in blocks:
        out.setdefault(block["vnum"], block)
    return out


def word_of(text, fallback="mob"):
    """A name as one plain word of the file (the core does not use it)."""
    text = (text or "").replace("ł", "l").replace("Ł", "L")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^A-Za-z0-9_()+.\-]+", "_", text.strip()).strip("_")[:40]
    return text or fallback


def safe_group_name(name, vnum):
    name = re.sub(r'[\s"{}]+', "_", name or "").strip("_")
    return name or f"MT2009_grupa_{vnum}"


def render_block(block, kind, eol="\r\n"):
    lines = [f"Group\t{safe_group_name(block['name'], block['vnum'])}", "{"]
    if kind == "g":
        word, mob = block["leader"]
        lines.append(f"\tLeader\t{word_of(word)}\t{int(mob)}")
        lines.append(f"\tVnum\t{int(block['vnum'])}")
        for k, (word, mob) in enumerate(block["members"], 1):
            lines.append(f"\t{k}\t{word_of(word)}\t{int(mob)}")
    else:
        lines.append(f"\tVnum\t{int(block['vnum'])}")
        for k, (group, weight) in enumerate(block["members"], 1):
            lines.append(f"\t{k}\t{int(group)}\t{int(weight)}")
    lines.append("}")
    return eol.join(lines) + eol


def render_custom(blocks, kind):
    """The panel's file: the groups sorted by number, None when there is none."""
    if not blocks:
        return None
    # "#" starts a comment line for CTextFileLoader (SplitLine); "//" would be read as a key
    head = (f"# {MARK}: {FILE_NAMES[kind]} - groups changed in the Seban panel (merged into the image's file by "
            "m2-groups)\r\n")
    return head + "".join(render_block(blocks[v], kind) for v in sorted(blocks))


def same_block(a, b, kind):
    if a is None or b is None:
        return a is b
    return render_block(a, kind) == render_block(b, kind)


def display_name(name):
    """A group's name from the file (EUC-KR in the package's file) for the page."""
    data = (name or "").encode("latin-1", "replace")
    for encoding in ("utf-8", "euc_kr", "cp1250"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return name


# ---------------------------------------------------------------- state ---
_CACHE = {}
_BUILDS = {}      # key -> how many times it was built (a later cache keys on it, never on id())


def _cached(key, signature, build):
    hit = _CACHE.get(key)
    if hit and hit[0] == signature:
        return hit[1]
    value = build()
    _CACHE[key] = (signature, value)
    _BUILDS[key] = _BUILDS.get(key, 0) + 1
    return value


def generation(key):
    return _BUILDS.get(key, 0)


def base_of(spool, kind):
    """(blocks by vnum, source, problems) of the image's file."""
    for number, path in enumerate(base_candidates(spool, kind)):
        sig = stamp(path)
        if sig is None:
            continue
        parsed = _cached(("base", str(path), kind), sig, lambda p=path: parse(read_latin(p), kind))
        return first_by_vnum(parsed["blocks"]), "game" if number == 0 else "live", parsed["problems"]
    return {}, None, []


def custom_of(spool, kind):
    path = custom_path(spool, kind)
    sig = stamp(path)
    if sig is None:
        return {}
    parsed = _cached(("custom", str(path), kind), sig, lambda: parse(read_latin(path), kind))
    return first_by_vnum(parsed["blocks"])


def state(spool):
    """Both files as the game will run them after the next restart (the same
    objects while the files stay - the list's cache keys on them)."""
    paths = [p for kind in ("g", "r") for p in base_candidates(spool, kind) + [custom_path(spool, kind)]]
    return _cached(("state", str(spool)), tuple(stamp(p) for p in paths), lambda: _state(spool))


def _state(spool):
    out = {"spool": spool, "problems": []}
    for kind in ("g", "r"):
        base, source, problems = base_of(spool, kind)
        custom = custom_of(spool, kind)
        effective = dict(base)
        effective.update(custom)
        out[kind] = {"base": base, "custom": custom, "effective": effective, "source": source}
        out["problems"] += [f"{FILE_NAMES[kind]}: {p}" for p in problems[:20]]
    return out


def rev_of(spool):
    """The panel's two files now (a form saved over a newer state is refused)."""
    digest = hashlib.sha256()
    for kind in ("g", "r"):
        try:
            digest.update(custom_path(spool, kind).read_bytes())
        except OSError:
            digest.update(b"-")
        digest.update(b"\0")
    return digest.hexdigest()[:20]


def regen_groups(spool, kind):
    """group.txt / group_group.txt the way regen.parse_groups() gives them
    ({vnum: {"vnum", "name", "members"}}, the leader first) - the panel's
    changes included, for the "Spawny potworów" page. None without files."""
    st = state(spool)
    part = st["g" if kind == "group" else "r"]
    if part["source"] is None and not part["custom"]:
        return None
    key = ("regen_groups", str(spool), kind)
    return _cached(key, generation(("state", str(spool))), lambda: _regen_groups(part, kind))


def _regen_groups(part, kind):
    out = {}
    for vnum, block in part["effective"].items():
        if kind == "group":
            members = [block["leader"][1]] + [m for _w, m in block["members"] if m]
        else:
            members = [group for group, _w in block["members"] if group]
        out[vnum] = {"vnum": vnum, "name": block["name"], "members": members}
    return out


# --------------------------------------------------------- spawn points ---
def spawn_entries(text):
    """[(type letter, count, vnum)] of a regen-format file (regen.txt, npc.txt,
    boss.txt, stone.txt) the way regen.cpp read_line takes the words: 11 a
    line ("e": 6); an unknown type stops the reading."""
    from dbeditor.regen import tokenize
    out, words = [], [w for w, _line in tokenize(text or "")]
    i = 0
    while i < len(words):
        letter = words[i][:1]
        if letter == "e":
            i += 6
            continue
        if letter not in ("m", "g", "r", "s") or i + 11 > len(words):
            break
        entry = words[i:i + 11]
        out.append((letter, _int(entry[9].lstrip("+")), _int(entry[10])))
        i += 11
    return out


def map_sources(spool):
    """[(folder, map index, [(file kind, path)])] of every map the game published."""
    from dbeditor import regen
    from dbeditor import spawnfiles as sf
    found = {}
    for index, folder in regen.map_list(spool):
        found.setdefault(folder, {"index": index, "files": []})
        path = regen.custom_path(spool, folder)
        found[folder]["files"].append(("regen", path if path.exists() else regen.base_file(spool, folder)))
        found[folder]["regen_page"] = True
    maps = sf.cached(sf.base_path(spool, "map_index.txt"), sf.parse_map_index) or {}
    for index, folder in maps.items():
        entry = found.setdefault(folder, {"index": index, "files": []})
        entry["index"] = entry["index"] or index
        for kind in sf.MAP_FILES:
            try:
                custom = sf.map_custom_path(spool, folder, kind)
                base = sf.map_base_path(spool, folder, f"{kind}.txt")
            except ValueError:
                continue
            path = custom if custom.exists() else base
            if path.exists():
                entry["files"].append((kind, path))
                entry["spawn_page"] = True
    try:
        npc_folders = [p.name for p in (root(spool) / "base" / "maps").iterdir() if (p / "npc.txt").is_file()]
    except OSError:
        npc_folders = []
    indexes = {folder: index for index, folder in maps.items()}
    for folder in npc_folders:
        entry = found.setdefault(folder, {"index": indexes.get(folder, 0), "files": []})
        entry["files"].append(("npc", npc_path(spool, folder)))
    return found


def usage_index(spool):
    """{("g"|"r", vnum): [{"folder", "index", "file", "points", "count", "special"}]}
    - every spawn line of the maps' files (the panel's versions where it has
    them) and every timed boss that spawns a group."""
    from dbeditor import spawnfiles as sf
    sources = map_sources(spool)
    special_paths = [sf.base_path(spool, "special_spawns.txt"), sf.special_custom_path(spool)]
    signature = tuple(sorted((folder, kind, str(path), stamp(path)) for folder, info in sources.items()
                             for kind, path in info["files"])) + tuple(stamp(p) for p in special_paths)

    def build():
        out = {}
        for folder, info in sources.items():
            for kind, path in info["files"]:
                sig = stamp(path)
                if sig is None:
                    continue
                entries = _cached(("spawns", str(path)), sig, lambda p=path: spawn_entries(read_latin(p)))
                per = {}
                for letter, count, vnum in entries:
                    if letter in ("g", "r"):
                        item = per.setdefault((letter, vnum), {"folder": folder, "index": info["index"], "file": kind,
                                                               "points": 0, "count": 0,
                                                               "regen_page": bool(info.get("regen_page")),
                                                               "spawn_page": bool(info.get("spawn_page"))})
                        item["points"] += 1
                        item["count"] += count
                for key, item in per.items():
                    out.setdefault(key, []).append(item)
        try:
            index = sf.SpawnIndex(spool)
            special = index.special
            folders = index.maps
        except Exception:  # the page works without the timed bosses
            special, folders = [], {}
        for group in special:
            if group.get("removed") or group.get("spawn_type") != "group" or not group.get("spawn_vnum"):
                continue
            out.setdefault(("g", group["spawn_vnum"]), []).append(
                {"folder": folders.get(group["map_index"], ""), "index": group["map_index"] or 0, "file": "special",
                 "points": max(1, len(group.get("places") or [])), "count": group.get("count") or 0,
                 "special": group.get("vnum")})
        return out

    return _cached(("usage", str(spool)), signature, build)


# --------------------------------------------------------------- history ---
def history_path(spool):
    return root(spool) / "history.jsonl"


def read_history(spool, limit=40, kind=None, vnum=None):
    try:
        lines = history_path(spool).read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    out = []
    for number in range(len(lines) - 1, -1, -1):
        try:
            entry = json.loads(lines[number])
        except ValueError:
            continue
        if kind is not None and (entry.get("kind") != kind or entry.get("vnum") != vnum):
            continue
        entry.setdefault("id", str(number))
        entry["when"] = datetime.fromtimestamp(int(entry.get("time") or 0))
        out.append(entry)
        if len(out) >= limit:
            break
    return out


def history_entry(spool, entry_id):
    try:
        lines = history_path(spool).read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    for line in reversed(lines):
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if str(entry.get("id")) == str(entry_id):
            return entry
    return None


def _log(spool, entry):
    entry.setdefault("id", f"{time.time_ns():x}{os.getpid():x}")
    path = history_path(spool)
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        lines = []
    lines.append(json.dumps(entry, ensure_ascii=False))
    if len(lines) > HISTORY_KEEP:
        lines = lines[-HISTORY_KEEP:]
    try:
        df._prepare_folder(path.parent)
        tmp = path.parent / f".history.new{os.getpid()}"
        tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
        os.chmod(tmp, 0o664)
        os.replace(tmp, path)
    except OSError:
        pass


def meta_path(spool):
    return root(spool) / "custom.meta.json"


def read_meta(spool):
    """{"g": {vnum: sha of the image's group when the panel changed it}, "r": {...}}."""
    try:
        data = json.loads(meta_path(spool).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    return {kind: {int(v): sha for v, sha in (data.get(kind) or {}).items() if str(v).isdigit()} for kind in ("g", "r")}


def block_sha(block, kind):
    return hashlib.sha256(render_block(block, kind).encode("latin-1")).hexdigest()[:16] if block else ""


def drifted(spool, st, kind, vnum, meta=None):
    """True when a server update changed the image's version of a group the
    panel changed (the panel's version is the one the game runs)."""
    meta = read_meta(spool) if meta is None else meta
    if vnum not in st[kind]["custom"] or vnum not in meta[kind]:
        return False
    return meta[kind][vnum] != block_sha(st[kind]["base"].get(vnum), kind)


def _write_meta(spool, kind, vnum, sha):
    meta = read_meta(spool)
    if sha is None:
        meta[kind].pop(vnum, None)
    else:
        meta[kind][vnum] = sha
    try:
        df._prepare_folder(root(spool))
        tmp = root(spool) / f".custom.meta.new{os.getpid()}"
        tmp.write_text(json.dumps({k: {str(v): h for v, h in m.items()} for k, m in meta.items()}), encoding="utf-8")
        os.chmod(tmp, 0o664)
        os.replace(tmp, meta_path(spool))
    except OSError:
        pass


def save_group(spool, kind, vnum, block, what, note=""):
    """One group into the panel's file (block None: out of it - back to the
    image's group, or gone when the image has none) with a history line."""
    register_file()
    custom = dict(custom_of(spool, kind))
    base, _source, _problems = base_of(spool, kind)
    _write_meta(spool, kind, vnum, None if block is None else block_sha(base.get(vnum), kind))
    before = custom.get(vnum)
    if block is None:
        custom.pop(vnum, None)
    else:
        custom[vnum] = block
    text = render_custom(custom, kind)
    data = None if text is None else text.encode("latin-1")
    backup = df.write_custom(spool, KEYS[kind], data, df.ascii_comment(f"{KIND_NAMES[kind]} {vnum}: {what}"))
    _log(spool, {"time": int(time.time()), "kind": kind, "vnum": vnum, "what": what, "note": note,
                 "before": render_block(before, kind) if before else None,
                 "after": render_block(block, kind) if block else None, "backup": backup})
    return backup


def save_whole(spool, kind, data, what, note=""):
    """A whole panel file (a backup restored, an import) with a history line."""
    register_file()
    backup = df.write_custom(spool, KEYS[kind], data, df.ascii_comment(what))
    _log(spool, {"time": int(time.time()), "kind": kind, "vnum": None, "what": what, "note": note,
                 "before": None, "after": None, "backup": backup})
    return backup


# ----------------------------------------------------------------- forms ---
def form_int(form, name, label, low, high, default=None):
    raw = (form.get(name) or "").strip().replace(" ", "")
    if raw == "" and default is not None:
        return default
    if not re.fullmatch(r"\d{1,10}", raw):
        raise ValueError(f"{label}: „{raw[:20]}” to nie liczba całkowita.")
    value = int(raw)
    if not low <= value <= high:
        raise ValueError(f"{label}: dozwolone {low}–{high}.")
    return value


def members_from_form(form, kind):
    """[(vnum, count)] (g) / [(group, weight)] (r) of the form's rows."""
    vnums, amounts = form.getlist("m_vnum"), form.getlist("m_count")
    out = []
    for i, raw in enumerate(vnums):
        raw = (raw or "").strip()
        if not raw:
            continue
        row = {"v": raw, "c": amounts[i] if i < len(amounts) else ""}
        label = f"Wiersz {i + 1}"
        if kind == "g":
            vnum = form_int({"v": row["v"]}, "v", f"{label}: numer potwora", 1, VNUM_MAX)
            count = form_int({"c": row["c"]}, "c", f"{label}: ile sztuk", 1, MAX_MEMBERS, default=1)
        else:
            vnum = form_int({"v": row["v"]}, "v", f"{label}: numer grupy", 1, VNUM_MAX)
            count = form_int({"c": row["c"]}, "c", f"{label}: waga", 1, MAX_WEIGHT, default=1)
        out.append((vnum, count))
    return out


def build_block(kind, vnum, name, leader, rows, old=None, mob_word=None):
    """A block from the form's values; the file's own name words of the
    monsters an old block had are kept."""
    words = {}
    if old is not None and kind == "g":
        for word, mob in [old["leader"]] + list(old["members"]):
            words.setdefault(mob, word)
    mob_word = mob_word or (lambda mob: "mob")
    if kind == "g":
        members = []
        for mob, count in rows:
            members += [(words.get(mob) or mob_word(mob), mob)] * count
        return {"vnum": vnum, "name": name, "leader": (words.get(leader) or mob_word(leader), leader),
                "members": members, "bad": []}
    return {"vnum": vnum, "name": name, "leader": None, "members": list(rows), "bad": []}


def counted(members):
    """[(mob, count)] in the order of first appearance."""
    order, counts = [], {}
    for _word, mob in members:
        if mob not in counts:
            order.append(mob)
            counts[mob] = 0
        counts[mob] += 1
    return [(mob, counts[mob]) for mob in order]


def check_block(kind, block, st, mobs):
    """(errors, warnings) of a group about to be saved."""
    errors, warnings = [], []
    if not 1 <= block["vnum"] <= VNUM_MAX:
        errors.append(f"Numer grupy: dozwolone 1–{VNUM_MAX}.")
    if not block["members"] and kind == "r":
        errors.append("Zestaw grup potrzebuje co najmniej jednej grupy.")
    if len(block["members"]) > MAX_MEMBERS:
        errors.append(f"Za dużo członków: {len(block['members'])} (gra czyta najwyżej {MAX_MEMBERS}).")
    if kind == "g":
        unknown = sorted({m for m in [block["leader"][1]] + [m for _w, m in block["members"]] if m not in mobs})
        if mobs and unknown:
            errors.append("Nie ma takich potworów (mob_proto): " + ", ".join(map(str, unknown[:12])))
        size = 1 + len(block["members"])
        if size > WARN_MEMBERS:
            warnings.append(f"Grupa ma {size} potworów w jednym miejscu – to dużo (tłok i obciążenie serwera).")
    else:
        groups = st["g"]["effective"]
        unknown = sorted({group for group, _w in block["members"] if group not in groups})
        if unknown:
            errors.append("Nie ma takich grup (group.txt): " + ", ".join(map(str, unknown[:12])))
    return errors, warnings


# ---------------------------------------------------------------- install ---
def install(bp, ctx):
    import dbeditor
    register_file()
    df.register(bp)
    rows_db, game_text, login_required = ctx["rows"], ctx["game_text"], ctx["login_required"]
    _mob_cache = {}

    def mobs():
        """mob_proto {vnum: {...}} (a few seconds old at most; {} without the database)."""
        if "dbg_mobs" in g:
            return g.dbg_mobs
        hit = _mob_cache.get("mobs")
        if hit and time.time() - hit[0] < MOBS_SECONDS:
            g.dbg_mobs = hit[1]
            return hit[1]
        try:
            table = df.mob_table(rows_db, game_text)
        except Exception:  # the page works (numbers only) without the database
            table = {}
        if table:
            _mob_cache["mobs"] = (time.time(), table)
        g.dbg_mobs = table
        return table

    def mob_name(vnum):
        info = mobs().get(vnum)
        return (info["name"] or f"Potwór {vnum}") if info else f"NIEZNANY POTWÓR {vnum}"

    def mob_word(vnum):
        info = mobs().get(vnum)
        return word_of(info["name"] if info else "", "mob")

    def map_titles():
        from dbeditor import regen
        return regen.map_names()

    def map_label(index, folder, names):
        from dbeditor import regen
        return regen.map_label(index, folder, names)

    def summaries(st, usage):
        """[summary] of every group and set - the list's rows, cached while
        the files, the spawn points and the monster table stay."""
        table = mobs()
        spool = str(st["spool"])
        signature = (generation(("state", spool)), generation(("usage", spool)),
                     (_mob_cache.get("mobs") or (0,))[0], len(table))
        key = ("summaries", str(st["spool"]))
        hit = _CACHE.get(key)
        if hit and hit[0] == signature:
            return hit[1]
        groups, sets = st["g"]["effective"], st["r"]["effective"]
        meta = read_meta(st["spool"])
        out, by_group = [], {}
        for vnum, block in groups.items():
            mobs_in = [block["leader"][1]] + [m for _w, m in block["members"]]
            levels = [table[m]["level"] for m in mobs_in if m in table]
            names = [(table[m]["name"] if m in table else "") for m in mobs_in]
            item = {"kind": "g", "vnum": vnum, "name": display_name(block["name"]), "size": len(mobs_in),
                    "mobs": set(mobs_in), "lead": mob_name(block["leader"][1]),
                    "lmin": min(levels) if levels else 0, "lmax": max(levels) if levels else 0,
                    "hay": " ".join([display_name(block["name"])] + names).casefold(),
                    "custom": vnum in st["g"]["custom"], "new": vnum not in st["g"]["base"],
                    "drift": drifted(st["spool"], st, "g", vnum, meta),
                    "uses": usage.get(("g", vnum), []), "via": [],
                    "bad": any(m not in table for m in mobs_in) if table else False}
            by_group[vnum] = item
            out.append(item)
        for vnum, block in sets.items():
            inner = [by_group.get(group) for group, _w in block["members"]]
            known = [i for i in inner if i]
            levels = [lv for i in known for lv in (i["lmin"], i["lmax"]) if lv]
            item = {"kind": "r", "vnum": vnum, "name": display_name(block["name"]), "size": len(block["members"]),
                    "mobs": set().union(*[i["mobs"] for i in known]) if known else set(),
                    "groups": {group for group, _w in block["members"]},
                    "lead": " / ".join(i["lead"] for i in known[:3]) + (" / …" if len(known) > 3 else ""),
                    "lmin": min(levels) if levels else 0, "lmax": max(levels) if levels else 0,
                    "hay": " ".join([display_name(block["name"])] + [i["hay"] for i in known]).casefold(),
                    "custom": vnum in st["r"]["custom"], "new": vnum not in st["r"]["base"],
                    "drift": drifted(st["spool"], st, "r", vnum, meta),
                    "uses": usage.get(("r", vnum), []), "via": [], "bad": len(known) != len(inner)}
            out.append(item)
            for group in item["groups"]:
                if group in by_group:
                    by_group[group]["via"].append(vnum)
        set_uses = {i["vnum"]: i["uses"] for i in out if i["kind"] == "r"}
        for item in out:
            item["points"] = sum(u["points"] for u in item["uses"])
            item["folders"] = {u["folder"] for u in item["uses"] if u["folder"]}
            if item["kind"] == "g":
                for set_vnum in item["via"]:
                    item["folders"] |= {u["folder"] for u in set_uses.get(set_vnum, []) if u["folder"]}
            item["used"] = bool(item["uses"]) or any(set_uses.get(s) for s in item["via"])
        _CACHE[key] = (signature, out)
        return out

    def page_state():
        spool = df.spool_dir()
        st = state(spool)
        try:
            usage = usage_index(spool)
        except Exception:  # never break the list over a spawn file
            usage = {}
        return spool, st, usage

    def filters():
        args = request.args
        f = {k: (args.get(k) or "").strip() for k in ("q", "typ", "lvl_od", "lvl_do", "mapa", "uzycie", "zmienione",
                                                      "sort", "kier", "mob")}
        if f["typ"] not in ("", "g", "r"):
            f["typ"] = ""
        if f["sort"] not in SORTS:
            f["sort"] = "vnum"
        if f["kier"] not in ("", "malejaco"):
            f["kier"] = ""
        for k in ("lvl_od", "lvl_do", "mob"):
            if not re.fullmatch(r"\d{1,10}", f[k]):
                f[k] = ""
        return f

    def matches(item, f):
        if f["typ"] and item["kind"] != f["typ"]:
            return False
        if f["mob"] and int(f["mob"]) not in item["mobs"]:
            return False
        if f["q"]:
            q = f["q"]
            if q.isdigit():
                if not (item["vnum"] == int(q) or int(q) in item["mobs"] or int(q) in item.get("groups", ())):
                    return False
            elif q.casefold() not in item["hay"]:
                return False
        low = int(f["lvl_od"]) if f["lvl_od"] else None
        high = int(f["lvl_do"]) if f["lvl_do"] else None
        if (low is not None or high is not None) and not item["lmax"]:
            return False
        if low is not None and item["lmax"] < low:
            return False
        if high is not None and item["lmin"] > high:
            return False
        if f["mapa"] and f["mapa"] not in item["folders"]:
            return False
        if f["uzycie"] == "uzywane" and not item["used"]:
            return False
        if f["uzycie"] == "nieuzywane" and item["used"]:
            return False
        if f["zmienione"] and not item["custom"]:
            return False
        return True

    def sort_key(name):
        return {"vnum": lambda i: (i["kind"], i["vnum"]),
                "nazwa": lambda i: (i["lead"].casefold(), i["kind"], i["vnum"]),
                "poziom": lambda i: (i["lmin"] or 10 ** 6, i["lmax"], i["kind"], i["vnum"]),
                "rozmiar": lambda i: (i["size"], i["kind"], i["vnum"]),
                "spawny": lambda i: (i["points"], len(i["folders"]), i["kind"], i["vnum"])}[name]

    def file_states(spool):
        return {kind: df.live_state(spool, KEYS[kind]) for kind in ("g", "r")}

    def describe_members(kind, block, st):
        if kind == "g":
            out = [{"role": "Lider", "vnum": block["leader"][1], "count": 1}]
            out += [{"role": "Członek", "vnum": mob, "count": n} for mob, n in counted(block["members"])]
            for row in out:
                info = mobs().get(row["vnum"])
                row.update(name=mob_name(row["vnum"]), level=info["level"] if info else None,
                           rank=info["rank_name"] if info else "", kind_name=info["kind_name"] if info else "",
                           known=info is not None or not mobs())
            return out
        total = len(block["members"])
        out = []
        for group, weight in block["members"]:
            inner = st["g"]["effective"].get(group)
            text, levels = "", []
            if inner:
                parts = []
                for mob, n in counted([inner["leader"]] + list(inner["members"])):
                    parts.append((f"{n}× " if n > 1 else "") + mob_name(mob))
                    info = mobs().get(mob)
                    if info:
                        levels.append(info["level"])
                text = " + ".join(parts)
            out.append({"vnum": group, "weight": weight, "text": text, "known": inner is not None,
                        "size": (1 + len(inner["members"])) if inner else 0,
                        "levels": (min(levels), max(levels)) if levels else None,
                        "chance": 100.0 / total if total else 0})
        return out

    def uses_view(uses, names):
        known = endpoints()
        out = []
        for use in sorted(uses, key=lambda u: (map_label(u["index"], u["folder"], names).casefold(), u["file"])):
            link = None
            if use["file"] == "special":
                if use.get("special") is not None and "dbeditor.spawn_special" in known:
                    link = url_for("dbeditor.spawn_special", vnum=use["special"])
            elif use["file"] in ("boss", "stone") and "dbeditor.spawn_map" in known:
                link = url_for("dbeditor.spawn_map", mapdir=use["folder"]) + f"#plik-{use['file']}"
            elif use.get("regen_page") and "dbeditor.regen_map" in known:
                link = url_for("dbeditor.regen_map", folder=use["folder"])
            elif use.get("spawn_page") and "dbeditor.spawn_map" in known:
                link = url_for("dbeditor.spawn_map", mapdir=use["folder"])
            label = map_label(use["index"], use["folder"], names) if use["folder"] or use["index"] else "?"
            out.append(dict(use, label=label, file_name=SPAWN_FILES.get(use["file"], use["file"]), link=link))
        return out

    def endpoints():
        from flask import current_app
        return current_app.view_functions

    # ------------------------------------------------------------- list ---
    @bp.route("/grupy")
    @login_required
    def groups_index():
        spool, st, usage = page_state()
        f = filters()
        items = summaries(st, usage)
        found = [i for i in items if matches(i, f)]
        found.sort(key=sort_key(f["sort"]), reverse=f["kier"] == "malejaco")
        total = len(found)
        pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
        try:
            page = min(max(1, int(request.args.get("strona", "1"))), pages)
        except ValueError:
            page = 1
        shown = found[(page - 1) * PAGE_SIZE: page * PAGE_SIZE]
        names = map_titles()
        for item in shown:
            item["map_labels"] = sorted({map_label(u["index"], u["folder"], names) for u in item["uses"]
                                         if u["folder"] or u["index"]})
        folders = {}
        for item in items:
            for folder in item["folders"]:
                folders[folder] = folders.get(folder, 0) + 1
        sources = map_sources(spool) if folders else {}
        map_choices = sorted(((folder, map_label(sources.get(folder, {}).get("index", 0), folder, names), n)
                              for folder, n in folders.items()), key=lambda m: m[1].casefold())
        mob = int(f["mob"]) if f["mob"] else None
        args = {k: v for k, v in f.items() if v and not (k == "sort" and v == "vnum")}
        counts = {"g": len(st["g"]["effective"]), "r": len(st["r"]["effective"]),
                  "custom": len(st["g"]["custom"]) + len(st["r"]["custom"])}
        return render_template(
            "dbeditor/groups.html", items=shown, total=total, page=page, pages=pages, f=f, args=args,
            args_nomob={k: v for k, v in args.items() if k != "mob"},
            sorts=SORTS, map_choices=map_choices, counts=counts, st=st, status=file_states(spool),
            pending=[p for p in df.pending_changes(spool) if p["key"] in KEYS.values()],
            mob=mob, mob_label=mob_name(mob) if mob else "", problems=st["problems"],
            history=read_history(spool, 15), backups=df.list_backups(spool, list(KEYS.values()), 15),
            published=st["g"]["source"] is not None, csrf=df.csrf_token(), rev=rev_of(spool),
            kind_names=KIND_NAMES)

    # ----------------------------------------------------------- detail ---
    def load(kind, vnum):
        if kind not in KEYS:
            abort(404)
        spool, st, usage = page_state()
        return spool, st, usage, st[kind]["effective"].get(vnum)

    def edit_page(kind, vnum, block, spool, st, usage, form=None, new=False):
        names = map_titles()
        items = {(i["kind"], i["vnum"]): i for i in summaries(st, usage)}
        item = items.get((kind, vnum)) if block is not None and not new else None
        via = []
        if item and kind == "g":
            for set_vnum in item["via"]:
                set_item = items.get(("r", set_vnum))
                if set_item:
                    via.append({"vnum": set_vnum, "size": set_item["size"], "uses": uses_view(set_item["uses"], names),
                                "points": set_item["points"]})
        members = describe_members(kind, block, st) if block is not None else []
        if form is not None:
            rows = list(zip(form.getlist("m_vnum"), form.getlist("m_count")))
            leader = form.get("leader", "")
            name = form.get("name", "")
        elif block is not None:
            rows = [(str(m), str(n)) for m, n in (counted(block["members"]) if kind == "g" else block["members"])]
            leader = str(block["leader"][1]) if kind == "g" else ""
            name = display_name(block["name"])
        else:
            rows, leader, name = [], "", ""
        rows = rows + [("", "")] * max(3, 8 - len(rows))
        return render_template(
            "dbeditor/groups_edit.html", kind=kind, vnum=vnum, block=block, new=new, item=item, members=members,
            uses=uses_view(item["uses"], names) if item else [], via=via, rows=rows, leader=leader, name=name,
            raw_name=block["name"] if block else "", custom=vnum in st[kind]["custom"] if block is not None else False,
            in_base=vnum in st[kind]["base"], base_block=st[kind]["base"].get(vnum),
            drift=block is not None and not new and drifted(spool, st, kind, vnum),
            history=read_history(spool, 30, kind, vnum), status=file_states(spool)[kind],
            kind_names=KIND_NAMES, file_name=FILE_NAMES[kind], csrf=df.csrf_token(), rev=rev_of(spool),
            mob_name=mob_name, max_members=MAX_MEMBERS, max_weight=MAX_WEIGHT,
            rendered=render_block(block, kind, "\n") if block is not None else "",
            base_rendered=render_block(st[kind]["base"][vnum], kind, "\n") if vnum in st[kind]["base"] else "")

    @bp.route("/grupy/<kind>/<int:vnum>")
    @login_required
    def groups_edit(kind, vnum):
        spool, st, usage, block = load(kind, vnum)
        if block is None:
            flash(f"Nie ma {'grupy' if kind == 'g' else 'zestawu grup'} {vnum} w {FILE_NAMES.get(kind, '')}.", "error")
            return redirect(url_for("dbeditor.groups_index"))
        return edit_page(kind, vnum, block, spool, st, usage)

    @bp.route("/grupy/<kind>/nowa")
    @login_required
    def groups_new(kind):
        spool, st, usage, _block = load(kind, 0)
        taken = st[kind]["effective"]
        suggestion = (max(taken) + 1) if taken else 1
        copy = request.args.get("kopia", "")
        block = None
        if copy.isdigit() and int(copy) in taken:
            source = taken[int(copy)]
            block = dict(source, vnum=suggestion, name=f"MT2009_grupa_{suggestion}")
        return edit_page(kind, suggestion, block, spool, st, usage, new=True)

    @bp.route("/grupy/api/szukaj")
    @login_required
    def groups_search():
        query = (request.args.get("q") or "").strip()
        what = request.args.get("typ", "m")
        if not query or (len(query) < 2 and not query.isdigit()):
            return jsonify([])
        needle = query.casefold()
        if what == "g":
            spool, st, usage = page_state()
            out = []
            for item in summaries(st, usage):
                if item["kind"] != "g":
                    continue
                if (query.isdigit() and (item["vnum"] == int(query) or int(query) in item["mobs"])) or \
                        (not query.isdigit() and needle in item["hay"]):
                    out.append({"vnum": item["vnum"], "label": f"{item['lead']} ({item['size']} szt., poz. "
                                                                f"{item['lmin']}–{item['lmax']})"})
                if len(out) >= 30:
                    break
            out.sort(key=lambda o: (str(o["vnum"]) != query, o["vnum"]))
            return jsonify(out)
        found = [m for m in mobs().values() if str(m["vnum"]) == query or
                 (not query.isdigit() and needle in (m["name"] or "").casefold())]
        found.sort(key=lambda m: (str(m["vnum"]) != query, m["type"] != 0, m["level"], m["vnum"]))
        return jsonify([{"vnum": m["vnum"], "label": f"{m['name']} (poz. {m['level']}, {m['kind_name']})"}
                        for m in found[:30]])

    @bp.get("/grupy/plik/<kind>")
    @login_required
    def groups_file(kind):
        """The live file as the game will build it (image + the panel's groups)."""
        if kind not in KEYS:
            abort(404)
        st = state(df.spool_dir())
        text = "".join(render_block(st[kind]["effective"][v], kind) for v in sorted(st[kind]["effective"]))
        return Response(text.encode("latin-1", "replace"), mimetype="text/plain; charset=latin-1",
                        headers={"Content-Disposition": f"attachment; filename={FILE_NAMES[kind]}"})

    # ------------------------------------------------------------ saves ---
    def back(kind=None, vnum=None):
        if kind and vnum is not None:
            return redirect(url_for("dbeditor.groups_edit", kind=kind, vnum=vnum))
        return redirect(url_for("dbeditor.groups_index"))

    def in_use(st, usage, kind, vnum):
        """Why a group may not disappear (spawn lines, sets that list it)."""
        why = []
        uses = usage.get((kind, vnum), [])
        if uses:
            why.append(f"stoi w {sum(u['points'] for u in uses)} punktach spawnu")
        if kind == "g":
            sets = sorted(v for v, b in st["r"]["effective"].items() if any(gv == vnum for gv, _w in b["members"]))
            if sets:
                why.append("jest w zestawach grup " + ", ".join(map(str, sets[:8])))
        return why

    @bp.post("/grupy/zapisz")
    @login_required
    def groups_save():
        form = request.form
        kind = form.get("kind", "")
        if kind not in KEYS:
            abort(400)
        if not df.csrf_ok(form):
            flash("Sesja formularza wygasła – odśwież stronę i spróbuj jeszcze raz.", "error")
            return back()
        spool, st, usage = page_state()
        action = form.get("action", "save")
        note = (form.get("note") or "").strip()[:120]
        try:
            vnum = form_int(form, "vnum", "Numer grupy", 1, VNUM_MAX)
        except ValueError as exc:
            flash(str(exc), "error")
            return back()
        if form.get("rev") != rev_of(spool):
            flash("Grupy zmieniły się w międzyczasie (inna karta albo inna osoba) – sprawdź je i zapisz jeszcze raz.",
                  "error")
            return back(kind, vnum) if vnum in st[kind]["effective"] else back()
        title = f"{KIND_NAMES[kind]} {vnum}"
        current = st[kind]["custom"].get(vnum)
        try:
            if action == "revert":
                if current is None:
                    raise ValueError(f"{title} nie była zmieniana w panelu.")
                if vnum not in st[kind]["base"]:
                    raise ValueError(f"{title} jest nowa (nie ma jej w obrazie gry) – możesz ją tylko usunąć.")
                save_group(spool, kind, vnum, None, "przywrócono wersję z obrazu gry", note)
                flash(f"{title}: wróci wersja z obrazu gry. Działa po restarcie (Zastosuj).", "success")
                return back(kind, vnum)
            if action == "delete":
                if current is None or vnum in st[kind]["base"]:
                    raise ValueError("Usunąć można tylko grupę dodaną w panelu (grupy z obrazu gry można zmienić "
                                     "albo przywrócić).")
                why = in_use(st, usage, kind, vnum)
                if why:
                    raise ValueError(f"{title} jest używana ({'; '.join(why)}) – najpierw usuń te wpisy.")
                save_group(spool, kind, vnum, None, "usunięto grupę dodaną w panelu", note)
                flash(f"Usunięto: {title}. Działa po restarcie (Zastosuj).", "success")
                return back()
            if action not in ("save", "new"):
                raise ValueError("Nieznana operacja.")
            new = action == "new"
            if new and vnum in st[kind]["effective"]:
                raise ValueError(f"Numer {vnum} jest już zajęty – wybierz inny.")
            if not new and vnum not in st[kind]["effective"]:
                raise ValueError(f"Nie ma {title} – odśwież stronę.")
            old = None if new else st[kind]["effective"][vnum]
            name = (form.get("name") or "").strip()
            if old is not None and name == display_name(old["name"]):
                name = old["name"]
            elif name or new:
                name = name or f"MT2009_grupa_{vnum}"
                if not NAME_RE.fullmatch(name):
                    raise ValueError("Nazwa grupy: jedno słowo z liter bez polskich znaków, cyfr i _ ( ) + . - "
                                     "(najwyżej 64 znaki).")
            else:
                name = old["name"]
            rows = members_from_form(form, kind)
            leader = form_int(form, "leader", "Lider (numer potwora)", 1, VNUM_MAX) if kind == "g" else None
            block = build_block(kind, vnum, name, leader, rows, old, mob_word)
            errors, warnings = check_block(kind, block, st, mobs())
            if errors:
                for e in errors:
                    flash(e, "error")
                flash("Nic nie zapisano.", "error")
                return edit_page(kind, vnum, old, spool, st, usage, form=form, new=new)
            if old is not None and same_block(old, block, kind):
                flash("Nic się nie zmieniło.", "info")
                return back(kind, vnum)
            base = st[kind]["base"].get(vnum)
            target = None if base is not None and same_block(base, block, kind) else block
            if target is None and current is None:
                flash("Nic się nie zmieniło.", "info")
                return back(kind, vnum)
            what = ("nowa grupa: " if new else "zmiana składu: ") + summary_text(kind, block, st, mob_name)
            save_group(spool, kind, vnum, target, what, note)
            for w in warnings:
                flash(w, "info")
            flash(f"Zapisano – {title}. Gra wczyta zmianę po restarcie rdzeni (Zastosuj).", "success")
            return back(kind, vnum)
        except (ValueError, OSError) as exc:
            flash(f"Nie zapisano: {exc}", "error")
            if action in ("save", "new"):
                old = st[kind]["effective"].get(vnum) if action == "save" else None
                return edit_page(kind, vnum, old, spool, st, usage, form=form, new=action == "new")
            return back(kind, vnum) if vnum in st[kind]["effective"] else back()

    @bp.post("/grupy/cofnij")
    @login_required
    def groups_undo():
        form = request.form
        if not df.csrf_ok(form):
            flash("Sesja formularza wygasła – odśwież stronę i spróbuj jeszcze raz.", "error")
            return back()
        spool = df.spool_dir()
        try:
            if form.get("backup"):
                name = form.get("backup", "")
                for kind, key in KEYS.items():
                    path = df.backup_file(spool, key, name)
                    if path is not None:
                        raw = path.read_bytes()
                        save_whole(spool, kind, None if raw.startswith(df.NO_CHANGES_MARK) else raw,
                                   f"przywrócono kopię {name}")
                        flash(f"Przywrócono kopię {FILE_NAMES[kind]} (obecny stan też trafił do kopii). "
                              "Działa po restarcie (Zastosuj).", "success")
                        return back()
                raise ValueError("Nie ma takiej kopii.")
            entry = history_entry(spool, form.get("entry", ""))
            if not entry or entry.get("vnum") is None or entry.get("kind") not in KEYS:
                raise ValueError("Nie ma takiej zmiany (historia przesunęła się?) – odśwież stronę.")
            kind, vnum = entry["kind"], int(entry["vnum"])
            custom = custom_of(spool, kind)
            now = render_block(custom[vnum], kind) if vnum in custom else None
            if now != entry.get("after"):
                raise ValueError(f"{KIND_NAMES[kind]} {vnum} zmieniono później jeszcze raz – cofnij najpierw "
                                 "późniejszą zmianę.")
            before = None
            if entry.get("before"):
                blocks = parse(entry["before"], kind)["blocks"]
                if not blocks:
                    raise ValueError("Nie da się odczytać poprzedniej wersji.")
                before = blocks[0]
            save_group(spool, kind, vnum, before, f"cofnięto: {entry.get('what', '')}"[:200])
            flash(f"Cofnięto zmianę – {KIND_NAMES[kind]} {vnum}. Działa po restarcie (Zastosuj).", "success")
            st = state(spool)
            return back(kind, vnum) if vnum in st[kind]["effective"] else back()
        except (ValueError, OSError) as exc:
            flash(f"Nie udało się: {exc}", "error")
            return back()

    dbeditor.add_section("dbeditor.groups_index", "👥", "Grupy potworów",
                         "Wszystkie grupy i zestawy grup: kto w nich jest, na jakim poziomie, na których mapach "
                         "stoją – i zmiana ich składu.")


def summary_text(kind, block, st, mob_name):
    """'Wilk + 2× Wildhund' / '1 z 3: 101, 102, 103' for the history."""
    if kind == "g":
        parts = [(f"{n}x " if n > 1 else "") + mob_name(mob)
                 for mob, n in counted([block["leader"]] + list(block["members"]))]
        text = " + ".join(parts)
    else:
        text = f"1 z {len(block['members'])}: " + ", ".join(str(gv) for gv, _w in block["members"])
    return text[:160]
