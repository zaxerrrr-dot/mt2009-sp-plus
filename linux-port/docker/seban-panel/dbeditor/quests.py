"""MT2009_PLUS_DB_EDITOR_QUESTS_V1: "Questy" - every quest of the game with a
switch, and its rewards: replaced (item X -> item Y x N, yang / experience x
a factor or a fixed amount, another permanent bonus) or added to (any item x
count, yang, experience, a bonus). The Biologist (collect_quest_lv30 ... lv92)
has its own page: each mission one reward entry.

Where it all lives
  * The quests are compiled into the game image (quest/object). The game's
    bin/m2-quests publishes what the panel shows into the spool volume both
    containers mount:  quests/catalog.txt (every compiled quest, on/off, its
    source), quests/src/<quest>.quest (the source) and quests/translate.lua
    (the quest texts, cp1250). Until a game with m2-quests has run, the
    panel shows the Biologist from its snapshot (quests_biolog.snapshot.txt).
  * The panel writes ONE file, quests/quests.custom.txt (render_custom()):
        off    <quest>
        item   <quest> <vnum> <new vnum|0 = nothing> <count|0 = the call's>
        gold   <quest> <amount|*> mul|set <value>
        exp    <quest> <amount|*> mul|set <value>
        bonus  <quest> <point> <value|*> <new point|0 = none> <new value>
        extra  <quest> <anchor> item|gold|exp|bonus <a> <b>
    and m2-quests, before the cores boot (Zastosuj), moves a switched-off
    quest's event handlers out of quest/object (its state table stays) and
    hands the rules to the cores (quest/reward_overrides.txt).
  * The engine (server-patches/questrewards, playerbot_quest_rewards.cpp,
    MT2009_PLUS_QUEST_REWARD_OVERRIDES_V1) consults the rules in the quests'
    reward functions: the calling quest + the call's ORIGINAL arguments say
    which rule ("item 50109 of collect_quest_lv30"). An extra is given when
    its anchor happens: item:<vnum>, bonus:<point>:<value>, gold:*, exp:* (that
    call of the quest) or state:<name> (the quest's set_state to that state -
    the Biologist's extras hang on state:__complete, which it sets right
    before its rewards).

What the editor reads from a quest's code (parse_quest, best effort): the
calls of pc.give_item2 / give_item, pc.change_money / changemoney /
change_gold / give_gold, pc.give_exp2 / give_exp / give_exp_perc,
affect.add_collect and give_reward("...") (world.quest_reward_proto), with the
state and "when" they are in; a call inside an if / a loop is marked
conditional, after number() / math.random / take_chance random, in a kill
event a quest drop. A value that is not a literal number is shown as the
code and can only be changed by "all calls of this quest" (gold/exp).

Only rewards given after Zastosuj change; nothing is recomputed for players
who already finished a quest (see RETRO_NOTE).

Backups, "pending" (/db/apply) and the game's report use dropfiles.py's
machinery (key "quests"); the config export / import carries the file as
part "quests" (config.register_file_part).
"""
import hashlib
import re
import time
from pathlib import Path

from flask import Response, abort, flash, redirect, render_template, request, url_for

from dbeditor import dropfiles as df
from dbeditor import tables_common
from dbeditor.items import POINT_LABELS, TECHNICAL_POINTS

MARK = "MT2009_PLUS_DB_EDITOR_QUESTS_V1"
KEY = "quests"
FOLDER = "quests"
CUSTOM_NAME = "quests.custom.txt"
TITLE = "Questy (włączenie, nagrody)"
SNAPSHOT = Path(__file__).resolve().parent / "quests_biolog.snapshot.txt"   # the Biologist's sources, 6 Oct 2026
ENCODING = "cp1250"
MAX_BYTES = 256 * 1024              # bin/m2-quests MAX_BYTES

GOLD_MAX = 2000000000               # playerbot_quest_rewards.cpp GOLD_CAP / EXP_CAP
EXP_MAX = 2000000000
COUNT_MAX = 10000                   # COUNT_CAP
FACTOR_MAX = 1000.0
BONUS_MAX = 1000000                 # BONUS_CAP
POINT_MAX = 255

# never switched off (bin/m2-quests PROTECTED): the panels' and the GM's quests
PROTECTED = {
    "web_admin": "pomocnik panelu w grze (teleport, prędkość, komendy panelu)",
    "gm_profile": "profil GM-a z panelu",
    "usun_misje": "okno /usunmisje",
    "cmd": "komendy czatu (game_commands)",
}
# critical: allowed off, but only after a confirmation (whole systems / dungeons go with them)
CRITICAL_NAMES = {
    "blacksmith", "stash", "skill_group", "skill_reset2", "training_grandmaster_skill", "map_warp", "teleport_ring",
    "tp_bookmarks", "itemshop_manage", "potion_use", "potion_recharge_manage", "reset_status", "reset_status_items",
    "change_empire", "marriage_manage", "special_shop", "game_option", "captcha_manage", "loot_chest",
    "inventory_remove_item", "item_change_sex", "horse_ride", "horse_summon", "horse_menu", "horse_inventory",
    "horse_inventory_init", "konie", "qbook_manage", "crafting_manage", "shop_unlock_slots", "dragon_soul",
    "dragon_soul_refine", "dragon_soul_shop", "guild_building", "guild_create", "guild_war_join",
    "kolekcjoner_item", "starter_kit", "starter_chest", "towarzysz", "dungeon_panel", "dungeon_return",
    "seonhae", "ksiegi_seonhae", "seon_pyeong", "affect_remove", "warehouse_expand", "speed_boost",
    "minigame_rumi", "minigame_catchking", "minigame_yutnori", "deviltower_zone", "devilcatacomb_zone",
    "razador_dungeon", "nemere_dungeon", "blue_dragon_lair", "biblioteka_wiedzy", "temple_of_the_ochao",
    "wzgorze_wukonga", "ruiny_skorpiona", "starozytna_dzungla", "spider_dungeon_2floor", "heavens_cave_escape",
    "heavens_cave_keyquest", "check_trans_ticket", "fishing_pass_shop", "autohunt_time", "antiexp_ring",
}
CATEGORIES = (
    ("biolog", "Biolog i zielarstwo"),
    ("fabula", "Fabuła i misje poboczne"),
    ("eventy", "Eventy"),
    ("lochy", "Lochy i wejścia"),
    ("systemy", "Systemy gry"),
    ("plus", "MT2009 PLUS (dodane)"),
    ("inne", "Inne"),
)
CATEGORY_NAMES = dict(CATEGORIES)
# our own quests (game/quest/*.quest, compiled by the Dockerfile): a Polish line each
OWN_TITLES = {
    "web_admin": "Pomocnik panelu (teleport, prędkość)", "speed_boost": "Premia do szybkości ruchu",
    "starter_chest": "Skrzynia startowa", "starter_kit": "Zestaw startowy", "konie": "Trening konia (stajenny)",
    "horse_inventory": "Sakwy konia", "gm_profile": "Profil GM", "new_quest_lv19": "Skóry niedźwiedzi (poz. 19)",
    "teleport_ring": "Pierścień Teleportacji", "pony_buy": "Kupno kucyka", "horse_upgrade": "Ulepszenie konia",
    "horse_upgrade2": "Ulepszenie konia (2)", "deviltower_zone": "Wieża Demonów",
    "fishing_pass_shop": "Sklep rybaka (Karta Wędkarska)", "collect_quest_lv85": "Biolog – Czerwony Konar (85)",
    "towarzysz": "Towarzysz (list)", "devilcatacomb_zone": "Katakumby Diabła",
    "check_trans_ticket": "Grota Wygnańców – przepustka", "heavens_cave_keyquest": "Seon-Hae – dzienna misja",
    "tanaka_ears": "Uszy Tanaki (Yonah)", "acce_costume_uriel": "Szarfy (Uriel)", "ah_yu_shop": "Sklep Ah-Yu",
    "costume_bonus_transfer": "Przenoszenie bonusów kostiumu", "dragon_soul": "Smocze Kamienie",
    "dragon_soul_refine": "Smocze Kamienie – ulepszanie", "dragon_soul_shop": "Smocze Kamienie – sklep",
    "autohunt_time": "Bilet Auto Łowy", "antiexp_ring": "Pierścień anty-doświadczenia",
    "seon_pyeong": "Seon-Pyeong (kostka +9)", "flea_market": "Dom Towarowy", "temple_of_the_ochao": "Świątynia Ochao",
    "razador_dungeon": "Loch Razadora", "nemere_dungeon": "Loch Nemere", "blue_dragon_lair": "Leże Niebieskiego Smoka",
    "goblin_skarbow": "Goblin skarbów", "biblioteka_wiedzy": "Biblioteka Wiedzy", "map_warp": "Teleporter",
    "dungeon_panel": "Panel lochów", "wzgorze_wukonga": "Wzgórze Wukonga", "ruiny_skorpiona": "Ruiny Skorpiona",
    "starozytna_dzungla": "Starożytna Dżungla", "seonhae": "Seon-Hae (bonus 6/7)", "minigame_rumi": "Rumi (Okey)",
    "minigame_catchking": "Złap Króla", "minigame_yutnori": "Yut Nori", "tp_bookmarks": "Zapisane teleporty",
    "ksiegi_seonhae": "Księgi Seon-Hae", "usun_misje": "/usunmisje", "guild_building": "Ziemia gildii",
    "kolekcjoner_item": "Kolekcjoner (przedmiot)", "cmd": "Komendy czatu",
    "mapa_tab": "Mapa teleportacji (TAB) – autor: Mur4s",
}
# The Biologist (Chaegirab, 20084; the reward at 20018): its missions in order.
BIOLOGIST = (
    ("collect_quest_lv30", 30, "Zęby Orka"),
    ("collect_quest_lv40", 40, "Księgi Klątw"),
    ("collect_quest_lv50", 50, "Pamiątki Demonów"),
    ("collect_quest_lv60", 60, "Matowy Lód"),
    ("collect_quest_lv70", 70, "Konar Zelkowy"),
    ("collect_quest_lv80", 80, "Certyfikat Tugyis"),
    ("collect_quest_lv85", 85, "Czerwony Konar Duchodrzewa"),
    ("collect_quest_lv90", 90, "Notatka Przywódcy"),
    ("collect_quest_lv92", 92, "Klejnoty"),
)
BIOLOGIST_NAMES = {q: (level, name) for q, level, name in BIOLOGIST}
BIOLOGIST_ANCHOR = "state:__complete"
BIOLOGIST_EXTRA_ROWS = 3
EXTRA_KINDS = (("item", "Przedmiot"), ("gold", "Yang"), ("exp", "Doświadczenie"), ("bonus", "Bonus stały"))
EXTRA_KIND_NAMES = dict(EXTRA_KINDS)
RETRO_NOTE = ("Zmiana działa dla graczy, którzy oddadzą misję PO restarcie (Zastosuj). Przeliczenie dla tych, "
              "co już oddali, nie jest możliwe: gra sumuje wszystkie bonusy Biologa tego samego rodzaju w jeden "
              "efekt (np. szybkość ruchu z poz. 30 i 70), więc nie da się ustalić, ile z niego dała która misja. "
              "Wyrównać można tylko ręcznie (np. dodatkowa nagroda przez ItemShop / komendę GM).")

NAME_RE = re.compile(r"^[A-Za-z0-9_]{1,64}$")
STATE_NAME_RE = re.compile(r"^[A-Za-z0-9_]{1,64}$")
QUEST_RE = re.compile(r"^\s*quest\s+([A-Za-z0-9_]+)\s+begin\b")
STATE_RE = re.compile(r"^\s*state\s+([A-Za-z0-9_]+)\s+begin\b")
WHEN_RE = re.compile(r"^\s*when\s+(.*?)\s+begin\s*$")
CALL_RE = re.compile(
    r"\b(?:(pc)\s*\.\s*(give_item2_select|give_item2|give_item_from_special_item_group2?|give_item|change_money|"
    r"changemoney|change_gold|give_gold|give_exp_perc|give_exp2|give_exp)|(affect)\s*\.\s*(add_collect)|"
    r"(give_reward|set_state|setstate|newstate|set_quest_state|send_letter|say_title|say_reward)"
    r"|(q)\s*\.\s*(set_state|setstate))\s*\(")
BLOCK_RE = re.compile(r"\b(if|elseif|for|while|function|repeat|until|end)\b")
RANDOM_RE = re.compile(r"\bnumber\s*\(|math\s*\.\s*random|take_chance|\bdice\b")
GAMEFORGE_RE = re.compile(r'^\s*gameforge\.([A-Za-z0-9_]+)\.([A-Za-z0-9_]+)\s*=\s*"(.*)"\s*$')
INT_RE = re.compile(r"^-?\d{1,12}$")
ITEM_INPUT_RE = re.compile(r"^\s*s?(\d{1,10})\b")
FACTOR_RE = re.compile(r"^\d{1,4}([.,]\d{1,4})?$")

KIND_NAMES = {"item": "Przedmiot", "gold": "Yang", "exp": "Doświadczenie", "bonus": "Bonus stały",
              "table": "Nagroda z tabeli quest_reward_proto", "special": "Losowanie z grupy (special_item_group)"}
FUNC_KIND = {
    "give_item2": "item", "give_item": "item", "give_item2_select": "special",
    "give_item_from_special_item_group": "special", "give_item_from_special_item_group2": "special",
    "change_money": "gold", "changemoney": "gold", "change_gold": "gold", "give_gold": "gold",
    "give_exp2": "exp", "give_exp": "exp", "give_exp_perc": "exp", "add_collect": "bonus", "give_reward": "table",
}


# ----------------------------------------------------------------- points ---
_POINTS = {}


def point_numbers():
    """{"POINT_MOV_SPEED": 19, ...} - the engine's EPointTypes (attrs.POINT_NAMES:
    the position is the number)."""
    if not _POINTS:
        try:
            from dbeditor.attrs import POINT_NAMES
            _POINTS.update({name: i + 1 for i, name in enumerate(POINT_NAMES)})
        except ImportError:
            pass
        _POINTS.setdefault("POINT_NONE", 0)
    return _POINTS


def point_label(point):
    name, unit = POINT_LABELS.get(int(point or 0), (f"Bonus #{point}", ""))
    return name + (f" ({unit})" if unit == "%" else "")


def bonus_choices():
    """[(point, Polish name)] for the bonus pickers, the regular ones first."""
    regular = sorted((p for p in POINT_LABELS if p and p not in TECHNICAL_POINTS), key=lambda p: point_label(p).lower())
    return [(p, point_label(p)) for p in regular]


# --------------------------------------------------------- reading a quest ---
def strip_comment(line):
    """The line without its "--" comment (quotes respected)."""
    quote = None
    i = 0
    while i < len(line):
        c = line[i]
        if quote:
            if c == "\\":
                i += 2
                continue
            if c == quote:
                quote = None
        elif c in "\"'":
            quote = c
        elif c == "-" and line.startswith("--", i):
            return line[:i]
        i += 1
    return line


def code_only(line):
    """The line with every string literal emptied (for the block keywords)."""
    return re.sub(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', '""', line)


def call_args(line, start):
    """The text between the "(" at start-1 and its ")" (None when the call
    goes on to the next line)."""
    depth, quote, i = 1, None, start
    while i < len(line):
        c = line[i]
        if quote:
            if c == "\\":
                i += 2
                continue
            if c == quote:
                quote = None
        elif c in "\"'":
            quote = c
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return line[start:i]
        i += 1
    return None


def split_args(text):
    out, depth, quote, cur = [], 0, None, ""
    i = 0
    while i < len(text):
        c = text[i]
        if quote:
            cur += c
            if c == "\\" and i + 1 < len(text):
                cur += text[i + 1]
                i += 2
                continue
            if c == quote:
                quote = None
        elif c in "\"'":
            quote = c
            cur += c
        elif c in "({[":
            depth += 1
            cur += c
        elif c in ")}]":
            depth -= 1
            cur += c
        elif c == "," and depth == 0:
            out.append(cur.strip())
            cur = ""
        else:
            cur += c
        i += 1
    if cur.strip() or out:
        out.append(cur.strip())
    return out


def literal_int(arg):
    """12 / "12" / -5 -> int; anything computed -> None."""
    if arg is None:
        return None
    a = arg.strip()
    if len(a) >= 2 and a[0] == a[-1] and a[0] in "\"'":
        a = a[1:-1].strip()
    return int(a) if INT_RE.match(a) else None


def literal_point(arg):
    if arg is None:
        return None
    a = arg.strip()
    if a in point_numbers():
        return point_numbers()[a]
    return literal_int(a)


def literal_string(arg):
    a = (arg or "").strip()
    if len(a) >= 2 and a[0] == a[-1] and a[0] in "\"'":
        return a[1:-1]
    return None


def parse_quest(text):
    """A quest's source -> {"name", "states", "rewards", "states_set",
    "letters", "say_rewards", "problems"} (see the module's docstring)."""
    if isinstance(text, (bytes, bytearray)):
        text = text.decode(ENCODING, "replace")
    q = {"name": None, "states": [], "rewards": [], "states_set": [], "letters": [], "say_rewards": [],
         "problems": []}
    state, when, depth, random_seen, drop = None, None, 0, False, False
    pending_when = None          # a "when a or" whose "begin" is on a later line
    for number, raw in enumerate(text.splitlines(), 1):
        line = strip_comment(raw)
        if not line.strip():
            continue
        if pending_when is not None:
            pending_when += " " + line.strip()
            if re.search(r"\bbegin\s*$", line):
                line, pending_when = pending_when, None
            else:
                continue
        elif state is not None and re.match(r"^\s*when\b", line) and not re.search(r"\bbegin\s*$", line):
            pending_when = line.strip()
            continue
        m = QUEST_RE.match(line)
        if m and q["name"] is None:
            q["name"] = m.group(1)
            continue
        m = STATE_RE.match(line)
        if m:
            state, when, depth = m.group(1), None, 0
            if state not in q["states"]:
                q["states"].append(state)
            continue
        m = WHEN_RE.match(line)
        if m and state is not None:
            when, depth, random_seen = m.group(1).strip(), 0, False
            drop = ".kill" in when
            continue
        code = code_only(line)
        if when is not None and RANDOM_RE.search(code):
            random_seen = True
        for cm in CALL_RE.finditer(line):
            func = cm.group(2) or cm.group(4) or cm.group(5) or cm.group(7)
            args_text = call_args(line, cm.end())
            if args_text is None:
                q["problems"].append(f"linia {number}: wywołanie {func} w kilku liniach – pominięte")
                continue
            args = split_args(args_text)
            if func in ("set_state", "setstate", "newstate"):
                target = literal_string(args[0] if args else None) or (args[0] if args else "")
                if STATE_NAME_RE.match(target or "") and target not in q["states_set"]:
                    q["states_set"].append(target)
                continue
            if func in ("send_letter", "say_title"):
                if args:
                    q["letters"].append(args[0])
                continue
            if func == "say_reward":
                if args:
                    q["say_rewards"].append((state, args[0]))
                continue
            if func == "set_quest_state":
                continue
            kind = FUNC_KIND.get(func)
            if kind is None:
                continue
            r = {"kind": kind, "func": ("affect." if func == "add_collect" else ("" if func == "give_reward" else "pc."))
                 + func, "state": state, "when": when, "line": number, "code": raw.strip()[:200], "args": args,
                 "conditional": depth > 0, "random": random_seen and depth > 0, "drop": drop, "literal": True,
                 "key": None, "note": ""}
            if kind == "item":
                vi, ci = (1, 2) if func == "give_item" else (0, 1)
                r["vnum"] = literal_int(args[vi] if len(args) > vi else None)
                r["count"] = literal_int(args[ci]) if len(args) > ci else 1
                r["literal"] = r["vnum"] is not None and r["count"] is not None
                if r["vnum"] is not None:
                    r["key"] = f"item:{r['vnum']}"
            elif kind == "gold":
                r["amount"] = literal_int(args[-1] if args else None)
                if r["amount"] is not None and r["amount"] <= 0:
                    continue          # a payment, not a reward
                r["literal"] = r["amount"] is not None
                r["key"] = f"gold:{r['amount']}" if r["literal"] else "gold:*"
            elif kind == "exp":
                if func == "give_exp_perc":
                    r["amount"] = None
                    r["note"] = "procent doświadczenia poziomu"
                else:
                    r["amount"] = literal_int(args[0 if func == "give_exp2" else 1] if len(args) > (0 if func == "give_exp2" else 1) else None)
                r["literal"] = r["amount"] is not None
                r["key"] = f"exp:{r['amount']}" if r["literal"] else "exp:*"
            elif kind == "bonus":
                r["point"] = literal_point(args[0] if args else None)
                r["value"] = literal_int(args[1] if len(args) > 1 else None)
                r["literal"] = r["point"] is not None and r["value"] is not None
                if r["point"] is not None:
                    r["key"] = f"bonus:{r['point']}:{r['value'] if r['value'] is not None else '*'}"
            elif kind == "table":
                r["table_key"] = literal_string(args[0] if args else None)
                r["literal"] = r["table_key"] is not None
            elif kind == "special":
                r["literal"] = False
                r["note"] = "losowanie z grupy – tego edytor nie zmienia"
            q["rewards"].append(r)
        if when is not None:
            for bm in BLOCK_RE.finditer(code):
                word = bm.group(1)
                if word in ("if", "for", "while", "function", "repeat"):
                    depth += 1
                elif word in ("end", "until"):
                    if depth == 0:
                        when = None          # the when's own "end"
                        break
                    depth -= 1
    return q


def reward_groups(q):
    """The quest's rewards grouped by the rule they would take: [{"key",
    "kind", "calls", "main", ...}], the rewards first, quest drops last."""
    groups, order = {}, []
    for r in q["rewards"]:
        if r["kind"] in ("table", "special") or r["key"] is None:
            key = f"{r['kind']}#{r['line']}"
        else:
            key = r["key"]
        g = groups.get(key)
        if g is None:
            g = groups[key] = {"key": key, "kind": r["kind"], "calls": [], "drop": True, "editable": False}
            order.append(key)
        g["calls"].append(r)
        g["drop"] = g["drop"] and r["drop"]
    for g in groups.values():
        first = g["calls"][0]
        g.update({k: first.get(k) for k in ("vnum", "count", "amount", "point", "value", "table_key", "func", "note")})
        g["conditional"] = any(r["conditional"] for r in g["calls"])
        g["random"] = any(r["random"] for r in g["calls"])
        g["literal"] = all(r["literal"] for r in g["calls"])
        g["states"] = sorted({r["state"] or "?" for r in g["calls"]})
        g["editable"] = g["kind"] in ("item", "bonus") and first.get("key") is not None \
            or g["kind"] in ("gold", "exp")
        g["field"] = field_name(g)
    out = [groups[k] for k in order]
    out.sort(key=lambda g: (g["drop"], g["kind"] in ("table", "special")))
    return out


def field_name(g):
    """The form fields' prefix of a reward group (quests_edit.html, quests_biolog.html)."""
    if g["kind"] == "item":
        return f"i_{g.get('vnum')}"
    if g["kind"] == "bonus":
        value = g.get("value")
        return f"b_{g.get('point')}_{'x' if value is None else str(value).replace('-', 'm')}"
    return ""


def table_groups(groups, table):
    """The rewards a give_reward("key") call gives (world.quest_reward_proto
    rows in table) as reward groups of their own - questlib's give_reward
    hands them out through pc.give_exp2 / pc.change_money / pc.give_item2 in
    the calling quest, so the same rules apply to them."""
    seen = {g["key"] for g in groups}
    out = []
    for g in groups:
        row = table.get(g.get("table_key") or "") if g["kind"] == "table" else None
        if not row:
            continue
        wanted = [("exp", {"amount": row["exp"]}), ("gold", {"amount": row["gold"]})]
        wanted += [("item", {"vnum": v, "count": c}) for v, c, special, _col in row["items"] if not special]
        for kind, values in wanted:
            if kind != "item" and values["amount"] <= 0:
                continue
            key = f"item:{values['vnum']}" if kind == "item" else f"{kind}:{values['amount']}"
            if key in seen:
                continue
            seen.add(key)
            s = {"key": key, "kind": kind, "calls": g["calls"], "drop": False, "editable": True,
                 "conditional": g["conditional"], "random": False, "literal": True, "states": g["states"],
                 "vnum": None, "count": None, "amount": None, "point": None, "value": None,
                 "table_key": g["table_key"], "func": "give_reward", "note": f"z tabeli „{g['table_key']}”",
                 "from_table": True}
            s.update(values)
            s["field"] = field_name(s)
            out.append(s)
    return out


def anchors(q, extra_groups=()):
    """[(anchor, Polish label)] an extra of this quest can hang on."""
    out = []
    for s in q["states_set"]:
        label = "zakończenie questa" if s.lower() in ("__complete", "complete", "__complete__") else f"przejście do stanu {s}"
        out.append((f"state:{s}", label))
    seen = set()
    for r in q["rewards"]:
        key = r.get("key")
        if not key or key in seen or r["kind"] not in ("item", "bonus", "gold", "exp"):
            continue
        if r["kind"] == "item":
            if r["drop"]:
                continue
            seen.add(key)
            out.append((key, f"przy nagrodzie: przedmiot {r['vnum']}"))
        elif r["kind"] == "bonus" and r.get("value") is not None:
            seen.add(key)
            out.append((key, f"przy nagrodzie: bonus {point_label(r['point'])} {r['value']}"))
        elif r["kind"] in ("gold", "exp"):
            anchor = f"{r['kind']}:*"
            if anchor not in seen:
                seen.add(anchor)
                out.append((anchor, "przy każdej wypłacie yang" if r["kind"] == "gold" else "przy każdym doświadczeniu"))
    for g in extra_groups:
        if g["kind"] == "item" and g["key"] not in seen:
            seen.add(g["key"])
            out.append((g["key"], f"przy nagrodzie: przedmiot {g['vnum']} (z tabeli)"))
        elif g["kind"] in ("gold", "exp") and f"{g['kind']}:*" not in seen:
            seen.add(f"{g['kind']}:*")
            out.append((f"{g['kind']}:*", "przy każdej wypłacie yang" if g["kind"] == "gold" else "przy każdym doświadczeniu"))
    return out


def default_anchor(q):
    for anchor, _label in anchors(q):
        if anchor in ("state:__complete", "state:complete", "state:__COMPLETE__"):
            return anchor
    found = anchors(q)
    return found[0][0] if found else None


# --------------------------------------------------------- the quest texts ---
_TRANSLATE = {"key": None, "map": {}}


def translations(spool):
    """{(quest, key): Polish text} from the published translate.lua (cached by mtime)."""
    path = Path(spool) / FOLDER / "translate.lua"
    try:
        stamp = path.stat().st_mtime
    except OSError:
        return {}
    if _TRANSLATE["key"] != (str(path), stamp):
        result = {}
        try:
            for line in path.read_bytes().decode(ENCODING, "replace").splitlines():
                m = GAMEFORGE_RE.match(line)
                if m:
                    result[(m.group(1), m.group(2))] = m.group(3)
        except OSError:
            pass
        _TRANSLATE.update(key=(str(path), stamp), map=result)
    return _TRANSLATE["map"]


def clean_text(text):
    text = re.sub(r"\[ENTER\]", " ", text or "")
    text = re.sub(r"\[[A-Z_]+[^\]]*\]", "", text)
    text = text.replace('\\"', '"')
    return re.sub(r"\s+", " ", text).strip()


def resolve_text(arg, texts):
    """gameforge.x.y / "literal" -> Polish text (or "")."""
    a = (arg or "").strip()
    lit = literal_string(a)
    if lit is not None:
        return clean_text(lit)
    m = re.match(r"^gameforge\s*\.\s*([A-Za-z0-9_]+)\s*\.\s*([A-Za-z0-9_]+)$", a)
    if m:
        return clean_text(texts.get((m.group(1), m.group(2)), ""))
    return ""


def quest_title(name, q, texts):
    if name in BIOLOGIST_NAMES:
        level, title = BIOLOGIST_NAMES[name]
        return f"Biolog – {title} (poz. {level})"
    if name in OWN_TITLES:
        return OWN_TITLES[name]
    for arg in (q or {}).get("letters", []):
        text = resolve_text(arg, texts)
        if text:
            return text[:80]
    return ""


def category(name, rel):
    rel = rel or ""
    if name in BIOLOGIST_NAMES or name.startswith(("collect_", "make_herb", "herbalism")) or "/collect/" in rel:
        return "biolog"
    if rel and "/" not in rel:
        return "plus"
    for part, cat in (("/story/", "fabula"), ("/events/", "eventy"), ("/dungeon/", "lochy"),
                      ("/map_entrance/", "lochy"), ("/systems/", "systemy"), ("/item/", "systemy"),
                      ("/npc/", "systemy")):
        if part in "/" + rel:
            return cat
    if name.startswith(("main_quest", "subquest", "new_quest", "desert_", "find_")):
        return "fabula"
    if name.startswith(("event_", "new_christmas", "new_easter", "christmas", "valentine", "harvest")):
        return "eventy"
    return "inne"


def criticality(name, cat):
    """"protected" (never off), "critical" (off after a confirmation) or ""."""
    if name in PROTECTED:
        return "protected"
    if name in CRITICAL_NAMES or cat in ("systemy", "lochy") or name.endswith(("_zone", "_dungeon", "_manage")):
        return "critical"
    return ""


# ---------------------------------------------------------- the catalogue ---
_PARSED = {}


def snapshot_sources():
    """{quest: source text} of the Biologist snapshot."""
    out = {}
    try:
        text = SNAPSHOT.read_bytes().decode(ENCODING, "replace")
    except OSError:
        return out
    name, buf = None, []
    for line in text.splitlines(keepends=True):
        m = re.match(r"^-- @@ ([A-Za-z0-9_]+) ", line)
        if m:
            if name:
                out[name] = "".join(buf)
            name, buf = m.group(1), []
            continue
        buf.append(line)
    if name:
        out[name] = "".join(buf)
    return out


def catalog(spool):
    """[{"name", "on", "rel", "source"}]: the game's catalog, or the snapshot's
    Biologist ("source" "snapshot") until the game has published one."""
    path = Path(spool) / FOLDER / "catalog.txt"
    rows = []
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            parts = line.split("\t")
            if len(parts) >= 3 and NAME_RE.match(parts[0]):
                rows.append({"name": parts[0], "on": parts[1] != "off", "rel": "" if parts[2] == "-" else parts[2],
                             "source": "game"})
    except OSError:
        pass
    if rows:
        return rows
    return [{"name": n, "on": True, "rel": f"quest/collect/{n}.quest", "source": "snapshot"}
            for n in snapshot_sources()]


def source_text(spool, name):
    path = Path(spool) / FOLDER / "src" / f"{name}.quest"
    try:
        return path.read_bytes().decode(ENCODING, "replace")
    except OSError:
        return snapshot_sources().get(name)


def parsed(spool, name):
    """parse_quest of the quest's published source (cached by mtime)."""
    path = Path(spool) / FOLDER / "src" / f"{name}.quest"
    try:
        stamp = ("game", path.stat().st_mtime, path.stat().st_size)
    except OSError:
        stamp = ("snapshot", SNAPSHOT.stat().st_mtime if SNAPSHOT.exists() else 0)
    hit = _PARSED.get(name)
    if hit and hit[0] == stamp:
        return hit[1]
    text = source_text(spool, name)
    q = parse_quest(text) if text is not None else None
    _PARSED[name] = (stamp, q)
    return q


# ------------------------------------------------------- the panel's file ---
def empty_rules():
    return {"items": {}, "gold": {}, "exp": {}, "bonus": {}, "extras": []}


def parse_custom(text):
    """quests.custom.txt -> {"off": set, "rules": {quest: rules}, "problems": [...]}"""
    if isinstance(text, (bytes, bytearray)):
        text = text.decode("utf-8", "replace")
    model = {"off": set(), "rules": {}, "problems": []}
    for number, raw in enumerate((text or "").splitlines(), 1):
        line = raw.rstrip("\r")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        t = line.split("\t")
        bad = lambda why: model["problems"].append(f"linia {number}: {why}")  # noqa: E731
        if len(t) < 2 or not NAME_RE.match(t[1]):
            bad("zła nazwa questa")
            continue
        quest = t[1]
        rules = model["rules"].setdefault(quest, empty_rules())
        try:
            if t[0] == "off":
                model["off"].add(quest)
            elif t[0] == "item" and len(t) >= 5:
                rules["items"][int(t[2])] = (int(t[3]), int(t[4]))
            elif t[0] in ("gold", "exp") and len(t) >= 5 and t[3] in ("mul", "set"):
                key = "*" if t[2] == "*" else int(t[2])
                value = float(t[4]) if t[3] == "mul" else int(t[4])
                rules[t[0]][key] = (t[3], value)
            elif t[0] == "bonus" and len(t) >= 6:
                rules["bonus"][(int(t[2]), "*" if t[3] == "*" else int(t[3]))] = (int(t[4]), int(t[5]))
            elif t[0] == "extra" and len(t) >= 6 and t[3] in EXTRA_KIND_NAMES:
                rules["extras"].append((t[2], t[3], int(t[4]), int(t[5])))
            else:
                bad(f"nieznany wpis „{t[0][:20]}”")
        except ValueError:
            bad("zła liczba")
    for quest in [q for q, r in model["rules"].items() if not any(r.values())]:
        del model["rules"][quest]
    return model


def fmt_factor(value):
    text = f"{float(value):.4f}".rstrip("0").rstrip(".")
    return text or "0"


def render_custom(model, names=None):
    """The model -> the file (deterministic order; None when it changes nothing).
    names: {quest: Polish title} for the comment lines."""
    names = names or {}
    lines = [f"# {MARK}: questy z panelu Sebana (Edytor bazy danych -> Questy)",
             "# off/item/gold/exp/bonus/extra <TAB> quest ... - opis w dbeditor/quests.py i bin/m2-quests"]
    body = []
    for quest in sorted(model["off"]):
        body.append(f"off\t{quest}")
    for quest in sorted(model["rules"]):
        r = model["rules"][quest]
        block = []
        for vnum in sorted(r["items"]):
            new, count = r["items"][vnum]
            block.append(f"item\t{quest}\t{vnum}\t{new}\t{count}")
        for kind in ("gold", "exp"):
            for key in sorted(r[kind], key=lambda k: (k != "*", k if k != "*" else 0)):
                mode, value = r[kind][key]
                block.append(f"{kind}\t{quest}\t{key}\t{mode}\t{fmt_factor(value) if mode == 'mul' else int(value)}")
        for (point, value) in sorted(r["bonus"], key=lambda k: (k[0], k[1] == "*", k[1] if k[1] != "*" else 0)):
            new_point, new_value = r["bonus"][(point, value)]
            block.append(f"bonus\t{quest}\t{point}\t{value}\t{new_point}\t{new_value}")
        for anchor, kind, a, b in r["extras"]:
            block.append(f"extra\t{quest}\t{anchor}\t{kind}\t{a}\t{b}")
        if block:
            title = re.sub(r"[^\x20-\x7e]", "?", names.get(quest, ""))[:60]
            body.append(f"# {quest}" + (f" - {title}" if title else ""))
            body += block
    if not body:
        return None
    return ("\n".join(lines + body) + "\n").encode("utf-8")


ANCHOR_RE = re.compile(r"^(item:\d{1,10}|bonus:\d{1,3}:-?\d{1,10}|gold:\*|exp:\*|state:[A-Za-z0-9_]{1,64})$")


def validate_model(model):
    """Problems in Polish the game would refuse ([] = fine) - the checks of
    bin/m2-quests and playerbot_quest_rewards.cpp."""
    problems = list(model.get("problems", []))
    for quest in model["off"]:
        if quest in PROTECTED:
            problems.append(f"{quest}: tego questa nie można wyłączyć ({PROTECTED[quest]}).")
    for quest, r in model["rules"].items():
        for vnum, (new, count) in r["items"].items():
            if vnum <= 0 or new < 0 or not 0 <= count <= COUNT_MAX:
                problems.append(f"{quest}: przedmiot {vnum} → {new} × {count} – zła wartość (ilość 0–{COUNT_MAX}).")
        for kind, cap in (("gold", GOLD_MAX), ("exp", EXP_MAX)):
            for key, (mode, value) in r[kind].items():
                if key != "*" and (not isinstance(key, int) or key <= 0):
                    problems.append(f"{quest}: {kind} – zła kwota wywołania „{key}”.")
                if mode == "mul" and not 0 <= float(value) <= FACTOR_MAX:
                    problems.append(f"{quest}: {kind} – mnożnik od 0 do {fmt_factor(FACTOR_MAX)}.")
                if mode == "set" and not 0 <= int(value) <= cap:
                    problems.append(f"{quest}: {kind} – kwota od 0 do {cap:,}.".replace(",", " "))
        for (point, value), (new_point, new_value) in r["bonus"].items():
            if not 0 < point <= POINT_MAX or not 0 <= new_point <= POINT_MAX or abs(new_value) > BONUS_MAX:
                problems.append(f"{quest}: bonus {point} {value} → {new_point} {new_value} – zła wartość.")
        for anchor, kind, a, b in r["extras"]:
            if not ANCHOR_RE.match(anchor):
                problems.append(f"{quest}: dodatkowa nagroda – zły punkt zaczepienia „{anchor[:40]}”.")
            if kind == "item" and (a <= 0 or not 0 < b <= COUNT_MAX):
                problems.append(f"{quest}: dodatkowy przedmiot {a} × {b} – zła wartość (ilość 1–{COUNT_MAX}).")
            if kind in ("gold", "exp") and not 0 < a <= GOLD_MAX:
                problems.append(f"{quest}: dodatkowe {'yang' if kind == 'gold' else 'doświadczenie'} – od 1 do 2 000 000 000.")
            if kind == "bonus" and (not 0 < a <= POINT_MAX or abs(b) > BONUS_MAX):
                problems.append(f"{quest}: dodatkowy bonus {a} {b} – zła wartość.")
    return problems


def validate_custom(data):
    if data is not None and len(data) > MAX_BYTES:
        return [f"Plik jest za duży (ponad {MAX_BYTES // 1024} KB)."]
    return validate_model(parse_custom(data or b""))


# ------------------------------------------------------------------ files ---
def register_file():
    """The file in dropfiles' table (backups, "pending" on /db/apply, the
    game's report) and in the config export / import."""
    df.FILES.setdefault(KEY, (FOLDER, CUSTOM_NAME, "status", TITLE))
    df.BASES.setdefault(KEY, (FOLDER, "quests.base.txt"))     # never written: the image has no rules
    try:
        from dbeditor import config
        if hasattr(config, "register_file_part"):
            config.register_file_part(KEY, TITLE, QuestFiles(KEY, config.FilePart))
    except ImportError:
        pass


def QuestFiles(part, base):
    """The config adapter (a FilePart of config.py), made here so config.py
    only has to know register_file_part."""

    class _QuestFiles(base):
        def keys(self, spool):
            return [KEY] if df.custom_path(spool, KEY).exists() else []

        def valid_key(self, key):
            return key == KEY

        def read(self, spool, key):
            try:
                return df.custom_path(spool, key).read_bytes()
            except OSError:
                return None

        def base(self, spool, key):
            return None

        def write(self, spool, key, data, reason):
            df.write_custom(spool, key, data, reason)

        def title(self, key):
            return TITLE

        def effective(self, key, data):
            return data is not None and bool(parse_custom(data)["off"] or parse_custom(data)["rules"])

        def check(self, spool, key, data, lookup):
            errors = validate_custom(data)[:10]
            model = parse_custom(data)
            items = set()
            for r in model["rules"].values():
                items.update(v for v, _c in r["items"].values() if v)
                items.update(a for _an, kind, a, _b in r["extras"] if kind == "item")
            warnings = []
            unknown = sorted(items - lookup("item", sorted(items))) if items else []
            if unknown:
                warnings.append("nieznane na tym serwerze przedmioty: " + ", ".join(map(str, unknown[:12])))
            known = {row["name"] for row in catalog(spool)}
            missing = sorted((set(model["rules"]) | model["off"]) - known) if known else []
            if missing:
                warnings.append("questy, których ten serwer nie ma: " + ", ".join(missing[:12]))
            return errors, warnings

    return _QuestFiles(part)


def current_model(spool):
    try:
        data = df.custom_path(spool, KEY).read_bytes()
    except OSError:
        data = b""
    return parse_custom(data), data


def sha(data):
    return hashlib.sha256(data or b"").hexdigest()[:16]


def save_model(spool, model, reason, names=None):
    data = render_custom(model, names)
    problems = validate_model(parse_custom(data or b""))
    if problems:
        raise ValueError("; ".join(problems[:6]))
    return df.write_custom(spool, KEY, data, reason)


# ----------------------------------------------------------- form helpers ---
def parse_amount(raw, label, low, high, integer=True):
    raw = (raw or "").replace(" ", "").replace("\u00a0", "").replace(",", "." if not integer else "").strip()
    if not raw:
        return None
    try:
        value = int(raw) if integer else float(raw)
    except ValueError:
        raise ValueError(f"{label}: „{raw[:20]}” to nie liczba.")
    if not low <= value <= high:
        raise ValueError(f"{label}: od {low} do {high}.")
    return value


def parse_item(raw, label, lookup=None):
    """"27001", "27001 – Czerwona mikstura", "s27001" -> 27001 (None: empty)."""
    raw = (raw or "").strip()
    if not raw:
        return None
    m = ITEM_INPUT_RE.match(raw)
    if not m:
        if lookup:
            found = lookup(raw)
            if found:
                return found
        raise ValueError(f"{label}: wpisz VNUM przedmiotu albo wybierz go z listy.")
    return int(m.group(1))


def rule_summary(kind, rule, names):
    """A rule in Polish, for the list and the history."""
    if kind == "item":
        new, count = rule
        if not new:
            return "nic"
        return f"{names.get(new, {}).get('name') or new} × {count or 'jak w queście'}"
    if kind in ("gold", "exp"):
        mode, value = rule
        return f"× {fmt_factor(value).replace('.', ',')}" if mode == "mul" else f"= {int(value):,}".replace(",", " ")
    if kind == "bonus":
        point, value = rule
        return "brak bonusu" if not point else f"{point_label(point)} {value}"
    return ""


def extra_summary(extra, names):
    _anchor, kind, a, b = extra
    if kind == "item":
        return f"+ {names.get(a, {}).get('name') or a} × {b}"
    if kind == "gold":
        return f"+ {a:,} yang".replace(",", " ")
    if kind == "exp":
        return f"+ {a:,} doświadczenia".replace(",", " ")
    return f"+ {point_label(a)} {b}"


# ------------------------------------------------------------------ pages ---
def install(bp, ctx):
    import dbeditor
    register_file()
    df.register(bp)
    tables_common.register(bp)
    login_required = ctx["login_required"]
    game_text = ctx.get("game_text") or (lambda v: v or "")

    def rows(sql, params=()):
        function = ctx.get("rows")
        if function is None:
            return []
        try:
            return function(sql, params)
        except Exception:  # the database is not worth a broken page
            return []

    def item_names(vnums):
        if ctx.get("rows") is None:
            return {}
        try:
            return df.item_names(rows, game_text, vnums)
        except Exception:
            return {}

    def item_lookup(text):
        found = [i for i in df.search_items(rows, game_text, text, 5)] if ctx.get("rows") else []
        exact = [i for i in found if i["name"].casefold() == text.casefold()]
        return (exact or found or [{"vnum": None}])[0]["vnum"]

    def reward_table():
        """{key: {"exp", "gold", "items": [(vnum, count, special)]}} of world.quest_reward_proto."""
        out = {}
        for row in rows("SELECT quest_name, exp, gold, items, warrior_items, assassin_items, sura_items, "
                        "shaman_items FROM world.quest_reward_proto"):
            items = []
            for col in ("items", "warrior_items", "assassin_items", "sura_items", "shaman_items"):
                parts = [p.strip() for p in game_text(row.get(col) or "").split(",") if p.strip()]
                for i in range(0, len(parts) - 1, 2):
                    v = parts[i].lstrip("s")
                    if v.isdigit() and parts[i + 1].lstrip("-").isdigit():
                        items.append((int(v), int(parts[i + 1]), parts[i].startswith("s"), col))
            out[game_text(row.get("quest_name") or "")] = {"exp": int(row.get("exp") or 0),
                                                            "gold": int(row.get("gold") or 0), "items": items}
        return out

    def back(name=None):
        if name == "biolog":
            return redirect(url_for("dbeditor.quests_biolog"))
        if name:
            return redirect(url_for("dbeditor.quests_edit", name=name))
        return redirect(url_for("dbeditor.quests"))

    def titles_for(spool, names):
        texts = translations(spool)
        return {n: quest_title(n, parsed(spool, n), texts) for n in names}

    def check_form():
        if not df.csrf_ok(request.form):
            flash("Sesja formularza wygasła – odśwież stronę i spróbuj jeszcze raz.", "error")
            return False
        return True

    def stale(data):
        if request.form.get("sha") != sha(data):
            flash("Ustawienia questów zmieniły się w międzyczasie (inny zapis) – odśwież stronę i wprowadź zmiany "
                  "jeszcze raz.", "error")
            return True
        return False

    def common_page():
        spool = df.spool_dir()
        state = df.live_state(spool, KEY)
        return spool, state

    # --------------------------------------------------------- the list ---
    @bp.route("/questy")
    @login_required
    def quests():
        spool, state = common_page()
        model, data = current_model(spool)
        texts = translations(spool)
        query = (request.args.get("q") or "").strip().casefold()
        cat_filter = request.args.get("kat") or ""
        only = request.args.get("tylko") or ""
        entries, vnums = [], set()
        for row in catalog(spool):
            name = row["name"]
            q = parsed(spool, name)
            cat = category(name, row["rel"])
            rules = model["rules"].get(name)
            groups = reward_groups(q) if q else []
            main = [g for g in groups if not g["drop"]]
            for g in main:
                if g.get("vnum"):
                    vnums.add(g["vnum"])
            entry = {"name": name, "title": quest_title(name, q, texts), "rel": row["rel"], "cat": cat,
                     "cat_name": CATEGORY_NAMES[cat], "off": name in model["off"], "game_off": not row["on"],
                     "crit": criticality(name, cat), "changed": bool(rules), "rewards": main[:6],
                     "more": max(0, len(main) - 6), "drops": len(groups) - len(main), "parsed": q is not None,
                     "rules": rules}
            if query and query not in name.casefold() and query not in entry["title"].casefold():
                continue
            if cat_filter and cat != cat_filter:
                continue
            if only == "zmienione" and not (entry["changed"] or entry["off"]):
                continue
            if only == "wylaczone" and not entry["off"]:
                continue
            entries.append(entry)
        entries.sort(key=lambda e: (e["cat"] != "biolog", e["cat"], e["name"]))
        names = item_names(vnums)
        source = catalog(spool)[0]["source"] if catalog(spool) else "none"
        return render_template("dbeditor/quests.html", entries=entries, names=names, status=state,
                               pending=[1] if state["pending"] else [], categories=CATEGORIES, query=query,
                               cat_filter=cat_filter, only=only, source=source, model=model,
                               backups=df.list_backups(spool, [KEY], 15), sha=sha(data), csrf=df.csrf_token(),
                               point_label=point_label, kind_names=KIND_NAMES, protected=PROTECTED,
                               fmt_int=lambda v: f"{int(v):,}".replace(",", " "))

    @bp.post("/questy/przelacz")
    @login_required
    def quests_toggle():
        spool = df.spool_dir()
        if not check_form():
            return back()
        name = request.form.get("name", "")
        model, data = current_model(spool)
        if stale(data):
            return back()
        known = {r["name"]: r for r in catalog(spool)}
        if not NAME_RE.match(name) or (known and name not in known):
            flash("Nie ma takiego questa.", "error")
            return back()
        turn_on = request.form.get("on") == "1"
        cat = category(name, known.get(name, {}).get("rel"))
        crit = criticality(name, cat)
        if not turn_on and crit == "protected":
            flash(f"Questa {name} nie można wyłączyć: {PROTECTED[name]}.", "error")
            return back()
        if not turn_on and crit == "critical" and request.form.get("potwierdz") != "1":
            flash(f"{name} to quest krytyczny (system gry / loch) – zaznacz „Rozumiem” i spróbuj jeszcze raz.", "error")
            return back(request.form.get("wroc") or None)
        if turn_on:
            model["off"].discard(name)
        else:
            model["off"].add(name)
        try:
            save_model(spool, model, f"quest {name} {'wlaczony' if turn_on else 'wylaczony'}", titles_for(spool, model["rules"]))
        except (OSError, ValueError) as exc:
            flash(f"Nie udało się zapisać: {exc}", "error")
            return back()
        flash(f"Quest {name} będzie {'WŁĄCZONY' if turn_on else 'WYŁĄCZONY'} po restarcie (Zastosuj)."
              + ("" if turn_on else " Postacie zachowują swój postęp – po ponownym włączeniu quest rusza dalej."),
              "success")
        return back(request.form.get("wroc") or None)

    @bp.post("/questy/kopie")
    @login_required
    def quests_backup():
        spool = df.spool_dir()
        if not check_form():
            return back()
        try:
            name = request.form.get("name", "")
            if request.form.get("action") == "undo":
                found = df.list_backups(spool, [KEY], 1)
                if not found:
                    flash("Nie ma czego cofać.", "info")
                    return back()
                name = found[0]["name"]
            df.restore_backup(spool, KEY, name)
        except (OSError, ValueError) as exc:
            flash(f"Nie udało się: {exc}", "error")
            return back()
        flash("Przywrócono poprzednie ustawienia questów. Działają po restarcie (Zastosuj).", "success")
        return back()

    @bp.get("/questy/plik")
    @login_required
    def quests_file():
        _model, data = current_model(df.spool_dir())
        return Response(data or b"# brak zmian\n", mimetype="text/plain; charset=utf-8",
                        headers={"Content-Disposition": "attachment; filename=quests.custom.txt"})

    # ------------------------------------------------------ one quest ---
    def quest_or_404(spool, name):
        if not NAME_RE.match(name or ""):
            abort(404)
        known = {r["name"]: r for r in catalog(spool)}
        if name not in known:
            abort(404)
        return known[name]

    @bp.route("/questy/q/<name>")
    @login_required
    def quests_edit(name):
        spool, state = common_page()
        row = quest_or_404(spool, name)
        q = parsed(spool, name)
        model, data = current_model(spool)
        rules = model["rules"].get(name, empty_rules())
        texts = translations(spool)
        groups, extra_groups, table = edit_groups(q)
        groups = groups + extra_groups
        vnums = {g["vnum"] for g in groups if g.get("vnum")} | {v for v, _c in rules["items"].values() if v} \
            | {a for _an, kind, a, _b in rules["extras"] if kind == "item"}
        for g in groups:
            if g["kind"] == "table" and g.get("table_key") in table:
                vnums |= {v for v, _c, _s, _col in table[g["table_key"]]["items"]}
        names = item_names(vnums)
        cat = category(name, row["rel"])
        say_rewards = [(s, resolve_text(a, texts) or a) for s, a in (q or {}).get("say_rewards", [])]
        return render_template("dbeditor/quests_edit.html", name=name, row=row, q=q, groups=groups, rules=rules,
                               title=quest_title(name, q, texts), cat_name=CATEGORY_NAMES[cat],
                               crit=criticality(name, cat), off=name in model["off"], names=names, table=table,
                               anchors=anchors(q, extra_groups) if q else [],
                               default_anchor=default_anchor(q) if q else None,
                               bonuses=bonus_choices(), point_label=point_label, kind_names=KIND_NAMES,
                               extra_kinds=EXTRA_KINDS, say_rewards=say_rewards, status=state,
                               pending=[1] if state["pending"] else [], sha=sha(data), csrf=df.csrf_token(),
                               protected=PROTECTED, is_biologist=name in BIOLOGIST_NAMES, retro=RETRO_NOTE,
                               rule_summary=rule_summary, fmt_factor=fmt_factor, extra_summary=extra_summary,
                               fmt_int=lambda v: f"{int(v):,}".replace(",", " "))

    def edit_groups(q):
        """(the quest's reward groups, the ones its give_reward rows add, those rows)."""
        groups = reward_groups(q) if q else []
        table = reward_table() if any(g["kind"] == "table" for g in groups) else {}
        return groups, table_groups(groups, table), table

    def rules_from_form(form, q, old):
        """The edit form -> the quest's rules (ValueError in Polish)."""
        new = empty_rules()
        base_groups, extra_groups, _table = edit_groups(q)
        all_groups = base_groups + extra_groups
        for g in all_groups:
            if not g["editable"]:
                continue
            if g["kind"] == "item":
                vnum = g["vnum"]
                f = g["field"]
                if form.get(f + "_none"):
                    new["items"][vnum] = (0, 0)
                    continue
                item = parse_item(form.get(f + "_new"), f"Przedmiot {vnum} – zamiennik", item_lookup)
                count = parse_amount(form.get(f + "_count"), f"Przedmiot {vnum} – ilość", 1, COUNT_MAX)
                if item in (None, vnum) and count is None:
                    continue
                new["items"][vnum] = (item if item is not None else vnum, count or 0)
            elif g["kind"] == "bonus":
                point, value = g["point"], g["value"] if g["value"] is not None else "*"
                f = g["field"]
                if form.get(f + "_none"):
                    new["bonus"][(point, value)] = (0, 0)
                    continue
                raw_point = (form.get(f + "_point") or "").strip()
                raw_value = form.get(f + "_val")
                if not raw_point and not (raw_value or "").strip():
                    continue
                new_point = int(raw_point) if raw_point.isdigit() else point
                if new_point not in POINT_LABELS or new_point in TECHNICAL_POINTS and new_point != point:
                    raise ValueError(f"Bonus {point_label(point)}: wybierz bonus z listy.")
                new_value = parse_amount(raw_value, f"Bonus {point_label(point)} – wartość", -BONUS_MAX, BONUS_MAX)
                if new_value is None:
                    new_value = g["value"] if g["value"] is not None else 0
                if (new_point, new_value) != (point, g["value"]):
                    new["bonus"][(point, value)] = (new_point, new_value)
        for kind, label in (("gold", "Yang"), ("exp", "Doświadczenie")):
            keys = ["*"] + sorted({g["amount"] for g in all_groups if g["kind"] == kind and g.get("amount") is not None})
            for key in keys:
                f = f"{kind[0]}_{key}".replace("*", "all")
                mode = form.get(f + "_mode") or ""
                if mode not in ("mul", "set"):
                    continue
                if mode == "mul":
                    value = parse_amount(form.get(f + "_val"), f"{label} – mnożnik", 0, FACTOR_MAX, integer=False)
                else:
                    value = parse_amount(form.get(f + "_val"), f"{label} – kwota", 0, GOLD_MAX)
                if value is None:
                    raise ValueError(f"{label}: wpisz {'mnożnik' if mode == 'mul' else 'kwotę'}.")
                new[kind][key] = (mode, value)
        allowed = {a for a, _l in (anchors(q, extra_groups) if q else [])}
        for i in range(0, 60):
            f = f"x{i}"
            if f + "_kind" not in form:
                continue
            if form.get(f + "_del"):
                continue
            kind = form.get(f + "_kind")
            anchor = form.get(f + "_anchor") or ""
            if kind not in EXTRA_KIND_NAMES:
                continue
            if kind == "item":
                a = parse_item(form.get(f + "_item"), "Dodatkowy przedmiot", item_lookup)
                b = parse_amount(form.get(f + "_num"), "Dodatkowy przedmiot – ilość", 1, COUNT_MAX)
                if a is None and b is None:
                    continue
                if a is None:
                    raise ValueError("Dodatkowy przedmiot: wybierz przedmiot.")
                b = b or 1
            elif kind == "bonus":
                raw_point = (form.get(f + "_point") or "").strip()
                b = parse_amount(form.get(f + "_num"), "Dodatkowy bonus – wartość", -BONUS_MAX, BONUS_MAX)
                if not raw_point and b is None:
                    continue
                if not raw_point.isdigit() or int(raw_point) not in POINT_LABELS:
                    raise ValueError("Dodatkowy bonus: wybierz bonus z listy.")
                a, b = int(raw_point), b or 0
            else:
                a = parse_amount(form.get(f + "_num"), "Dodatkowe " + ("yang" if kind == "gold" else "doświadczenie"),
                                 1, GOLD_MAX)
                if a is None:
                    continue
                b = 0
            if anchor not in allowed and not any(anchor == ex[0] for ex in old["extras"]):
                raise ValueError("Dodatkowa nagroda: wybierz, kiedy ma być dawana.")
            new["extras"].append((anchor, kind, a, b))
        return new

    @bp.post("/questy/q/<name>")
    @login_required
    def quests_save(name):
        spool = df.spool_dir()
        quest_or_404(spool, name)
        if not check_form():
            return back(name)
        model, data = current_model(spool)
        if stale(data):
            return back(name)
        q = parsed(spool, name)
        if request.form.get("action") == "reset":
            model["rules"].pop(name, None)
            what = "przywrocono nagrody z questa"
        else:
            try:
                rules = rules_from_form(request.form, q, model["rules"].get(name, empty_rules()))
            except ValueError as exc:
                flash(str(exc), "error")
                flash("Nic nie zapisano – popraw wartości.", "error")
                return back(name)
            if any(rules.values()):
                model["rules"][name] = rules
            else:
                model["rules"].pop(name, None)
            what = (request.form.get("note") or "").strip()[:120] or "zmiana nagrod questa"
        try:
            save_model(spool, model, f"{name}: {what}", titles_for(spool, model["rules"]))
        except (OSError, ValueError) as exc:
            flash(f"Nie udało się zapisać: {exc}", "error")
            return back(name)
        flash("Zapisano nagrody questa. Gra użyje ich po restarcie (Zastosuj) – dla misji oddanych po restarcie.",
              "success")
        return back(name)

    # ------------------------------------------------------ the Biologist ---
    def biologist_missions(spool, model):
        known = {r["name"]: r for r in catalog(spool)}
        out = []
        for name, level, title in BIOLOGIST:
            q = parsed(spool, name) if name in known else None
            groups = [g for g in reward_groups(q) if not g["drop"]] if q else []
            rules = model["rules"].get(name, empty_rules())
            extras = [e for e in rules["extras"] if e[0] == BIOLOGIST_ANCHOR]
            out.append({"name": name, "level": level, "title": title, "known": name in known, "q": q,
                        "bonuses": [g for g in groups if g["kind"] == "bonus" and g["editable"]],
                        "reward_items": [g for g in groups if g["kind"] == "item" and g["editable"]],
                        "others": [g for g in groups if g["kind"] not in ("bonus", "item")],
                        "rules": rules, "off": name in model["off"],
                        "anchor_ok": q is not None and "__complete" in q["states_set"],
                        "extra_gold": sum(a for _an, k, a, _b in extras if k == "gold"),
                        "extra_exp": sum(a for _an, k, a, _b in extras if k == "exp"),
                        "extra_items": [(a, b) for _an, k, a, b in extras if k == "item"],
                        "extra_bonus": [(a, b) for _an, k, a, b in extras if k == "bonus"]})
        return out

    @bp.route("/questy/biolog")
    @login_required
    def quests_biolog():
        spool, state = common_page()
        model, data = current_model(spool)
        missions = biologist_missions(spool, model)
        vnums = set()
        for m in missions:
            vnums |= {g["vnum"] for g in m["reward_items"]} | {v for v, _c in m["rules"]["items"].values() if v} \
                | {a for a, _b in m["extra_items"]}
        return render_template("dbeditor/quests_biolog.html", missions=missions, names=item_names(vnums),
                               bonuses=bonus_choices(), point_label=point_label, status=state,
                               pending=[1] if state["pending"] else [], sha=sha(data), csrf=df.csrf_token(),
                               rows=BIOLOGIST_EXTRA_ROWS, retro=RETRO_NOTE, source=catalog(spool)[0]["source"]
                               if catalog(spool) else "none", fmt_int=lambda v: f"{int(v):,}".replace(",", " "))

    @bp.post("/questy/biolog")
    @login_required
    def quests_biolog_save():
        spool = df.spool_dir()
        if not check_form():
            return back("biolog")
        model, data = current_model(spool)
        if stale(data):
            return back("biolog")
        form = request.form
        changed = 0
        try:
            for m in biologist_missions(spool, model):
                name = m["name"]
                if not m["known"] or m["q"] is None:
                    continue
                rules = model["rules"].get(name, empty_rules())
                before = repr(rules)
                p = f"{name}_"
                for g in m["bonuses"]:
                    point, value = g["point"], g["value"]
                    f = p + g["field"]
                    raw_point = (form.get(f + "_point") or "").strip()
                    if raw_point == "0":
                        rules["bonus"][(point, value)] = (0, 0)
                        continue
                    new_point = int(raw_point) if raw_point.isdigit() else point
                    if new_point not in POINT_LABELS:
                        raise ValueError(f"{m['title']}: wybierz bonus z listy.")
                    new_value = parse_amount(form.get(f + "_val"), f"{m['title']} – wartość bonusu", -BONUS_MAX, BONUS_MAX)
                    new_value = value if new_value is None else new_value
                    if (new_point, new_value) == (point, value):
                        rules["bonus"].pop((point, value), None)
                    else:
                        rules["bonus"][(point, value)] = (new_point, new_value)
                for g in m["reward_items"]:
                    vnum = g["vnum"]
                    f = p + g["field"]
                    item = parse_item(form.get(f + "_new"), f"{m['title']} – przedmiot", item_lookup)
                    count = parse_amount(form.get(f + "_count"), f"{m['title']} – ilość", 0, COUNT_MAX)
                    if (item in (None, vnum)) and not count:
                        rules["items"].pop(vnum, None)
                    else:
                        rules["items"][vnum] = (item if item is not None else vnum, count or 0)
                extras = [e for e in rules["extras"] if e[0] != BIOLOGIST_ANCHOR]
                if m["anchor_ok"]:
                    gold = parse_amount(form.get(p + "gold"), f"{m['title']} – dodatkowy yang", 0, GOLD_MAX)
                    exp = parse_amount(form.get(p + "exp"), f"{m['title']} – dodatkowe doświadczenie", 0, EXP_MAX)
                    if gold:
                        extras.append((BIOLOGIST_ANCHOR, "gold", gold, 0))
                    if exp:
                        extras.append((BIOLOGIST_ANCHOR, "exp", exp, 0))
                    for k in range(BIOLOGIST_EXTRA_ROWS):
                        item = parse_item(form.get(f"{p}x{k}_item"), f"{m['title']} – dodatkowy przedmiot", item_lookup)
                        count = parse_amount(form.get(f"{p}x{k}_count"), f"{m['title']} – ilość", 1, COUNT_MAX)
                        if item:
                            extras.append((BIOLOGIST_ANCHOR, "item", item, count or 1))
                    raw_point = (form.get(p + "xb_point") or "").strip()
                    if raw_point.isdigit() and int(raw_point) in POINT_LABELS and int(raw_point) > 0:
                        value = parse_amount(form.get(p + "xb_val"), f"{m['title']} – wartość dodatkowego bonusu",
                                             -BONUS_MAX, BONUS_MAX)
                        if value:
                            extras.append((BIOLOGIST_ANCHOR, "bonus", int(raw_point), value))
                rules["extras"] = extras
                if repr(rules) != before:
                    changed += 1
                if any(rules.values()):
                    model["rules"][name] = rules
                else:
                    model["rules"].pop(name, None)
        except ValueError as exc:
            flash(str(exc), "error")
            flash("Nic nie zapisano – popraw wartości.", "error")
            return back("biolog")
        if not changed:
            flash("Nic się nie zmieniło.", "info")
            return back("biolog")
        try:
            save_model(spool, model, (form.get("note") or "").strip()[:120] or "nagrody Biologa",
                       titles_for(spool, model["rules"]))
        except (OSError, ValueError) as exc:
            flash(f"Nie udało się zapisać: {exc}", "error")
            return back("biolog")
        flash(f"Zapisano nagrody Biologa ({changed} misji). Działają po restarcie (Zastosuj) dla misji oddanych "
              "po restarcie.", "success")
        return back("biolog")

    dbeditor.add_section("dbeditor.quests", "📜", "Questy",
                         "każdy quest z włącznikiem; nagrody: inny przedmiot, yang/doświadczenie ×, bonusy "
                         "Biologa, dodatkowe nagrody")
