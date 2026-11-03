"""MT2009_PLUS_DB_EDITOR_V1: "Potwory i bossowie" - world.mob_proto for an
operator who is not a programmer.

The db core reads world.mob_proto once, while it boots (PROTO_FROM_DB, the
same as item_proto; player.mob_proto is only a view of it), so an edit made
here changes the database at once and the game after "Zastosuj" (a restart).
Every saved field goes through common_items.save_rows() into the editor's
one history (player.web_dbeditor_history, tbl 'world.mob_proto'), so the
history page undoes a single monster as well as a whole mass change, and
"Zastosuj" (clientdata.py) lists them as pending.

What the columns mean in this engine (common/tables.h TMobTable, battle.cpp,
char_state.cpp):
  level         BYTE (1-255)   rank  0 PAWN .. 4 BOSS, 5 KING (Metin stones are 5)
  max_hp        DWORD          damage_min/max  the base hit (x dam_multiply)
  def           WORD           exp, gold_min/max  for the kill (before the rates)
  ai_flag       SET - AGGR = attacks on sight within aggressive_sight
  attack_speed / move_speed  100 = normal       resist_*  -100..100 %

The client draws the monster's name and level from its own mob_proto, which
the editor does not rebuild: a new level shows in the game's fights at once
after the restart, but the level above a monster's head stays the client's.

MT2009_PLUS_DB_EDITOR_MOB_SKILL_POWER_V1: dam_multiply and the levels of the
monster's skills (skill_level0..4) are edited too, one by one and in the mass
change, and every page shows the estimated hits of the monster - its plain
blow and the blow of each of its skills - computed by the engine's own
formula (hit_estimate() below). The db core loads both columns from
world.mob_proto at boot (ClientManagerBoot.cpp InitializeMobTableFromDB,
dam_multiply -> fDamMultiply, skill_levelN -> Skills[N].bLevel), so they take
effect after "Zastosuj". The client's mob_proto has neither any say in the
damage (the server counts every blow) - nothing to rebuild there.
"""
import re

from flask import abort, flash, redirect, render_template, request, url_for

from dbeditor import common_items as common

TABLE = "world.mob_proto"
LIMIT = 300
MASS_PREVIEW_ROWS = 200
MASS_MAX_ROWS = 3000

RANKS = {0: "Zwykły", 1: "Silniejszy", 2: "Rycerz", 3: "Elitarny", 4: "Boss", 5: "Król / Metin"}
TYPES = {0: "Potwór", 1: "NPC", 2: "Kamień Metin", 3: "Teleport", 4: "Drzwi", 5: "Budynek", 6: "Gracz",
         7: "Przemiana", 8: "Koń", 9: "Przejście", 10: "Obszar", 11: "Zwierzak"}
KINDS = {
    "walka": ("Potwory, bossowie i Metiny", "type IN (0,2)"),
    "potwory": ("Zwykłe potwory (bez bossów)", "type=0 AND `rank`<4"),
    "bossowie": ("Bossowie (ranga Boss i Król)", "type=0 AND `rank`>=4"),
    "metiny": ("Kamienie Metin", "type=2"),
    "wszystko": ("Wszystko (także NPC, konie, drzwi…)", None),
}
AI_FLAGS = ["AGGR", "NOMOVE", "COWARD", "NOATTSHINSU", "NOATTCHUNJO", "NOATTJINNO", "ATTMOB", "BERSERK",
            "STONESKIN", "GODSPEED", "DEATHBLOW", "REVIVE", "IGNORE_LAST_ATTACK", "NO_WANDER", "SEE_OTHER_NPC",
            "RETURN_LASTATTACK_POS", "LOOSE_AGGRO_ON_DISTANCE"]
AI_FLAG_LABELS = {
    "AGGR": "Agresywny – atakuje sam, gdy zobaczy gracza", "NOMOVE": "Stoi w miejscu (nie chodzi)",
    "COWARD": "Tchórz – ucieka przy niskim PŻ", "NOATTSHINSU": "Nie atakuje Shinsoo",
    "NOATTCHUNJO": "Nie atakuje Chunjo", "NOATTJINNO": "Nie atakuje Jinno", "ATTMOB": "Atakuje inne potwory",
    "BERSERK": "Szał (silniejszy przy niskim PŻ)", "STONESKIN": "Kamienna skóra", "GODSPEED": "Boska szybkość",
    "DEATHBLOW": "Śmiertelny cios", "REVIVE": "Odradza się po śmierci",
    "IGNORE_LAST_ATTACK": "Nie goni ostatniego napastnika", "NO_WANDER": "Nie wędruje",
    "SEE_OTHER_NPC": "Widzi inne NPC", "RETURN_LASTATTACK_POS": "Wraca na miejsce ataku",
    "LOOSE_AGGRO_ON_DISTANCE": "Odpuszcza pościg na dystans",
}
RESISTS = [("sword", "Miecze"), ("twohand", "Broń dwuręczna"), ("dagger", "Sztylety"), ("bell", "Dzwony"),
           ("fan", "Wachlarze"), ("bow", "Łuki"), ("fire", "Ogień"), ("elect", "Błyskawice"),
           ("magic", "Magia"), ("wind", "Wiatr"), ("poison", "Trucizna")]


def _int(low, high, label):
    return {"kind": "int", "min": low, "max": high, "label": label}


SPECS = {
    "level": _int(1, 255, "Poziom"),
    "rank": _int(0, 5, "Ranga"),
    "max_hp": _int(1, 2000000000, "PŻ (punkty życia)"),
    "damage_min": _int(0, 65535, "Obrażenia – minimum"),
    "damage_max": _int(0, 65535, "Obrażenia – maksimum"),
    "def": _int(0, 65535, "Obrona"),
    "exp": _int(0, 2000000000, "Doświadczenie za zabicie"),
    "gold_min": _int(0, 2000000000, "Yang za zabicie – minimum"),
    "gold_max": _int(0, 2000000000, "Yang za zabicie – maksimum"),
    "ai_flag": {"kind": "set", "members": AI_FLAGS, "label": "Zachowanie (ai_flag)"},
    "aggressive_sight": _int(0, 10000, "Zasięg wzroku agresji"),
    "attack_speed": _int(10, 1000, "Szybkość ataku (100 = zwykła)"),
    "move_speed": _int(10, 1000, "Szybkość ruchu (100 = zwykła)"),
    # MT2009_PLUS_DB_EDITOR_MOB_SKILL_POWER_V1: a FLOAT column (char.cpp GetMobDamageMultiply, x2 in BERSERK)
    "dam_multiply": {"kind": "float", "min": 0.1, "max": 20.0, "digits": 2, "label": "Mnożnik obrażeń"},
}
for _key, _label in RESISTS:
    SPECS[f"resist_{_key}"] = _int(-100, 100, f"Odporność: {_label} (%)")
# MT2009_PLUS_DB_EDITOR_MOB_SKILL_POWER_V1: the level (power) of each of the
# monster's five skills - 0..40 (SKILL_MAX_LEVEL, GetSkillPowerByLevel clamps
# there). The skill itself (skill_vnumN) stays read-only: a slot without a
# skill is never given a level, here or in the mass change.
SKILL_SLOTS = range(5)
SKILL_LEVEL_COLS = [f"skill_level{i}" for i in SKILL_SLOTS]
SKILL_VNUM_COLS = [f"skill_vnum{i}" for i in SKILL_SLOTS]
for _i in SKILL_SLOTS:
    SPECS[f"skill_level{_i}"] = _int(0, 40, f"Umiejętność {_i + 1} – poziom (siła)")
EDIT_COLS = list(SPECS)

# MT2009_PLUS_DB_EDITOR_MOB_MELEE_V1: "Zwykłe potwory: atak z dystansu →
# wręcz" - the owner's one-click form of
#   UPDATE world.mob_proto SET battle_type = 0, attack_range = 175
#   WHERE battle_type IN (1, 2) AND `rank` IN (0, 1, 2, 3) AND `type` = 0;
# (ordinary archers and casters fight in melee, bosses, kings/Metins and NPCs
# untouched). Written through common.save_rows() as ONE batch, so every field
# is in the history, "Zastosuj" lists it and one click undoes the lot. The two
# columns stay off the monster's own form (EDIT_COLS); they are registered
# with the history only so it can write and undo them. common/length.h
# EBattleType: 0 MELEE, 1 RANGE, 2 MAGIC; char_state.cpp keeps a RANGE/MAGIC
# monster at attack_range*0.8 and shoots - a MELEE one walks up and hits.
# apply.sh never rewrites battle_type, and attack_range only for 9706 (rank
# 5, not matched); its mob_proto.mt2009plus.sql and the Ochao / pet clones
# are INSERT IGNORE (a row that is there is never changed), mod/30_costume_
# pack.sql (REPLACE) runs once per install and holds only NPCs (type 1).
BATTLE_TYPES = {0: "wręcz", 1: "dystans (łuk)", 2: "magia (dystans)", 3: "specjalny", 4: "siłacz", 5: "tank",
                6: "super siłacz", 7: "super tank"}
MELEE_SPECS = {
    "battle_type": {"kind": "int", "min": 0, "max": 7, "label": "Sposób walki (battle_type)"},
    "attack_range": {"kind": "int", "min": 0, "max": 65535, "label": "Zasięg ataku"},
}
MELEE_WHERE = "battle_type IN (1, 2) AND `rank` IN (0, 1, 2, 3) AND `type` = 0"
MELEE_VALUES = {"battle_type": 0, "attack_range": 175}
MELEE_NOTE = "Zwykłe potwory: atak z dystansu → wręcz"
# What the history may write for a monster: the form's fields and the two above.
ALL_SPECS = dict(SPECS, **MELEE_SPECS)
READ_ONLY = ["type", "battle_type", "st", "dx", "ht", "iq", "drop_item", "regen_cycle",
             "regen_percent", "aggressive_hp_pct", "attack_range", "summon", "resurrection_vnum"] + SKILL_VNUM_COLS

# Mass changes: what can be changed, and which columns move together.
MASS_FIELDS = {
    "max_hp": ("PŻ", ["max_hp"]),
    "damage": ("Obrażenia (min. i maks.)", ["damage_min", "damage_max"]),
    "def": ("Obrona", ["def"]),
    "exp": ("Doświadczenie za zabicie", ["exp"]),
    "gold": ("Yang za zabicie (min. i maks.)", ["gold_min", "gold_max"]),
    "level": ("Poziom", ["level"]),
    "attack_speed": ("Szybkość ataku", ["attack_speed"]),
    "move_speed": ("Szybkość ruchu", ["move_speed"]),
    "aggressive_sight": ("Zasięg wzroku agresji", ["aggressive_sight"]),
    # MT2009_PLUS_DB_EDITOR_MOB_SKILL_POWER_V1
    "dam_multiply": ("Mnożnik obrażeń", ["dam_multiply"]),
    "skill": ("Siła umiejętności (poziom 1–40)", SKILL_LEVEL_COLS),
}
MASS_OPS = {"mul": "pomnóż przez", "add": "dodaj (lub odejmij)", "set": "ustaw na"}
# The mass fields whose change moves the estimated hits (the preview shows them before -> after).
HIT_FIELDS = ("damage", "dam_multiply", "skill", "level")
MASS_FLOAT_FIELDS = ("dam_multiply",)

# What linux-port/docker/mariadb/playerbot/apply.sh writes into
# world.mob_proto at EVERY start of the server (the playerbot-migrate step,
# before the db core boots) - an edit of these fields lasts only until the
# next start. Only its unconditional UPDATEs and only the columns this page
# edits; test_dbeditor_mobs.py keeps the list in step with apply.sh.
BOOT_RULES = [
    ((6001, 6002, 6003, 6004, 6005, 6006, 6007, 6008, 6009, 6051, 6091, 6101, 6102, 6103, 6104, 6105, 6106,
      6107, 6108, 6109, 6151, 6191),
     ("level", "max_hp", "damage_min", "damage_max", "def", "exp", "gold_min", "gold_max", "resist_sword",
      "resist_twohand", "resist_dagger", "resist_bell", "resist_fan", "resist_bow", "resist_fire", "resist_elect",
      "resist_magic", "resist_wind", "resist_poison", "dam_multiply"), "Ognista i Lodowa Kraina (Razador, Nemere)"),
    ((2493, 8057, 9677, 9678, 9696, 9701, 9702, 9710, 9711), ("level", "max_hp", "def", "exp"),
     "potwory i Metiny dodatków MT2009 Plus"),
    # MT2009_PLUS_RZNM_GLOBAL_LEVEL_V1: the two dungeons' monsters on Owsap's (the official) numbers - gold and
    # resists too; their Metins as well (a Metin's attack_speed / move_speed are the groups it calls).
    ((8057, 8058, 20399), ("level", "max_hp", "def", "exp", "gold_min", "gold_max", "attack_speed", "move_speed"),
     "Ognista i Lodowa Kraina (Razador, Nemere)"),
    ((8031, 8032, 8033, 8034), ("level", "max_hp", "def"), "Metiny dodatków MT2009 Plus"),
    ((9601, 9602, 9603, 9604, 9605, 9606, 9607, 9671, 9672, 9673, 9674, 9675, 9676, 9679, 9680, 9681, 9682,
      9683, 9684, 9690, 9691, 9692, 9693, 9694, 9695, 9697, 9698, 9699, 9700, 9707, 9708, 9709, 9712, 9713,
      9714),
     ("rank", "level", "max_hp", "damage_min", "damage_max", "def", "exp", "gold_min", "gold_max", "ai_flag",
      "dam_multiply"),
     "potwory map Arezzo"),
    ((9611, 9612, 9613, 9614, 9615), ("max_hp", "damage_min", "damage_max", "exp", "gold_min", "gold_max"),
     "Lemury (Arezzo)"),
    ((9703,), ("rank", "level", "max_hp", "damage_min", "damage_max", "def", "exp", "gold_min", "gold_max",
               "ai_flag", "resist_poison", "dam_multiply"), "Loch Pająków (Arezzo)"),
    ((9704,), ("rank", "level", "max_hp", "def", "exp", "gold_min", "gold_max", "resist_fire", "resist_poison"),
     "Loch Pająków (Arezzo)"),
    ((9705,), ("rank", "level", "max_hp", "damage_min", "damage_max", "def", "exp", "gold_min", "gold_max",
               "resist_fire", "resist_poison", "dam_multiply", "skill_level0"), "Loch Pająków (Arezzo)"),
    ((9706,), ("rank", "level", "max_hp", "damage_min", "damage_max", "def", "exp", "gold_min", "gold_max",
               "ai_flag", "attack_speed", "move_speed", "attack_range", "dam_multiply", "skill_level0"),
     "Loch Pająków (Arezzo)"),
    # MT2009_PLUS_MAPS_WZ_V1: mariadb/playerbot/maps_wz.sql (run by apply.sh at every start) puts the Giants'
    # and ogres' wiki levels back.
    ((1401, 1402, 1403, 1601, 1602, 1603), ("level",), "Wężowe Pole i Kraina Gigantów"),
    # MT2009_PLUS_DB_EDITOR_MOB_SKILL_POWER_V1: the bosses' skill levels and yang of MT2009_PLUS_AREZZO_BALANCE_V1
    # (Arezzo, Razador/Nemere, Azrael, the Grotto's Generals; a "WHERE vnum ... AND skill_vnumN = X" is
    # unconditional here - the editor never changes the skill itself) and Wukong's dam_multiply.
    ((9683, 9684, 9695, 9714), ("skill_level0",), "bossowie Arezzo (siła umiejętności)"),
    ((9694, 6091, 6191), ("skill_level0", "skill_level1"), "bossowie Arezzo, Razador i Nemere (siła umiejętności)"),
    ((2191, 2192, 8614, 8615, 3790, 3890), ("skill_level0",), "bossowie lochów (siła umiejętności)"),
    ((3691, 3791, 3391), ("skill_level1",), "bossowie lochów (siła umiejętności)"),
    ((2598, 2492, 2495, 3390, 3391), ("gold_min", "gold_max"), "bossowie lochów (yang)"),
    # MT2009_PLUS_ATLANTYDA_V1: Ruiny Atlantydy - its monsters and bosses whole, its stones' numbers.
    ((4550, 4551, 4552, 4553, 4554, 4555, 4556, 4557, 4558, 4559),
     ("rank", "battle_type", "level", "max_hp", "damage_min", "damage_max", "def", "exp", "gold_min", "gold_max",
      "attack_speed", "move_speed", "attack_range", "ai_flag", "aggressive_sight", "resist_sword", "resist_twohand",
      "resist_dagger", "resist_bell", "resist_fan", "resist_bow", "resist_fire", "resist_elect", "resist_magic",
      "resist_wind", "resist_poison", "dam_multiply", "skill_level0", "skill_level1", "skill_level2", "skill_level3",
      "skill_level4"), "Ruiny Atlantydy"),
    ((8729, 8730, 8731), ("level", "max_hp", "def", "exp", "gold_min", "gold_max", "attack_speed", "move_speed"),
     "Ruiny Atlantydy (kamienie)"),
]
BOOT_WARNING = "Te pola skrypt startowy bazy ustawia na nowo przy KAŻDYM starcie serwera – Twoja zmiana zniknie po restarcie"


def boot_cols(vnum):
    """The edited columns apply.sh puts back for this monster at every start."""
    cols = set()
    for vnums, rule_cols, _note in BOOT_RULES:
        if int(vnum) in vnums:
            cols |= set(rule_cols)
    return cols


def boot_notes(vnum):
    return [(note, cols) for vnums, cols, note in BOOT_RULES if int(vnum) in vnums]


# ---- estimated hits (MT2009_PLUS_DB_EDITOR_MOB_SKILL_POWER_V1) ------------------------
#
# How hard a monster hits a player, by the engine's own formula (game/src
# battle.cpp CalcMeleeDamage / CalcAttackRating / CalcAttBonus, char.cpp
# ComputePoints for an NPC and GetMobDamageMultiply, char_skill.cpp
# UseMobSkill / ComputeSkillAtPosition / FuncSplashDamage):
#
#   plain blow (CalcMeleeDamage, no weapon, an NPC attacker):
#     ATT_GRADE = 2*level + 2*st                     (ComputePoints, NPC branch)
#     roll      = random(damage_min, damage_max) * 2
#     AR        = (min(90, (4*dx + 2*level) / 6) + 210) / 300            the monster's rating
#     ER        = (2*e + 5) / (e + 95) * 0.3,  e = min(90, (4*dex + 2*lv) / 6)  of the PLAYER
#     atk       = int((ATT_GRADE + roll - 2*level) * (AR - ER)) + 2*level
#     atk       = int(atk * dam_multiply)            (x2 more while BERSERK)
#     CalcAttBonus: x mob damage rate 100/100, "*= 115/100" is integer 1 - no change
#     hit       = max(1, atk - player's defence)     (then the player's resists, criticals...)
#   skill blow (skills 256-263 "EnemyCrush200"...: szPointPoly "-5*k*atk",
#   flags ATTACK, USE_MELEE_DAMAGE, SPLASH, type MELEE):
#     k         = SKILL_POWER_BY_LEVEL[skill_level] * bMaxLevel / 100   (the mob's table:
#                 common.locale SKILL_POWER_BY_LEVEL, level 40 = 125 -> k 1.25 with bMaxLevel 1)
#     atk       = the plain blow above, counted per victim WITHOUT the defence
#                 (CalcMeleeDamage(mob, victim, bIgnoreDefense=true))
#     hit       = int(5 * k * atk), then minus the player's defence (FuncSplashDamage, SKILL_ATTR_TYPE_MELEE)
#   so a skill of level 40 is 6.25x the plain blow before the defence, 30 is
#   4.1x, 20 is 2.5x, 10 is 1.1x.
#
# The page shows the hit BEFORE the player's defence and resists, for a player
# of the monster's level: the low end with the lowest roll against a nimble
# player (dex 90, ER near its cap), the high end with the highest roll against
# a player of little dexterity (dex 10). Not counted: criticals (enchant_
# critical, x2), BERSERK (x2 dam_multiply), a dungeon's rage bonus, Zodiac's
# flat bonus, the player's defence / "odporność na potwory" / skill resists.
MOB_SKILL_POWER = [0, 5, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 50, 52, 54, 56, 58, 60,
                   63, 66, 69, 72, 82, 85, 88, 91, 94, 98, 102, 106, 110, 115, 125]
SKILL_MAX_LEVEL = 40
VICTIM_DEX_NIMBLE = 90
VICTIM_DEX_CLUMSY = 10
VICTIM_MAX_LEVEL = 120
HIT_NOTE = ("szacunek przed obroną i odpornościami gracza (gracz na poziomie potwora; mniej – zręczny gracz i najsłabszy "
            "rzut, więcej – mało zręczny i najmocniejszy rzut); bez krytyków i szału")
SKILL_LEVEL_HINT = "Poziom 40 = ok. 6× zwykły cios, 30 = ok. 4×, 20 = ok. 2,5×, 10 = ok. 1×, 0 = umiejętność nie zadaje obrażeń"


def _rating_src(dex, level):
    return min(90, max(0, (4 * int(dex) + 2 * int(level))) // 6)


def attack_rating(dex, level):
    return (_rating_src(dex, level) + 210.0) / 300.0


def evasion_rating(dex, level):
    src = _rating_src(dex, level)
    return ((src * 2 + 5) / (src + 95)) * 3.0 / 10.0


def _trunc(value):
    return int(value)  # C's (int) cast: towards zero


def melee_atk(row, roll, victim_dex, victim_level=None):
    """CalcMeleeDamage of the monster `row` for one damage roll (damage_min..
    max), against a player of victim_dex / victim_level, before the defence."""
    level, st, dex = int(row.get("level") or 0), int(row.get("st") or 0), int(row.get("dx") or 0)
    mult = float(row.get("dam_multiply") or 0)
    if victim_level is None:
        victim_level = min(max(level, 1), VICTIM_MAX_LEVEL)
    f_ar = attack_rating(dex, level) - evasion_rating(victim_dex, victim_level)
    att_grade = 2 * level + 2 * st
    atk = _trunc((att_grade + int(roll) * 2 - 2 * level) * f_ar) + 2 * level
    atk = _trunc(atk * mult)
    return max(1, atk)


def melee_range(row):
    low_roll, high_roll = sorted((int(row.get("damage_min") or 0), int(row.get("damage_max") or 0)))
    return (melee_atk(row, low_roll, VICTIM_DEX_NIMBLE), melee_atk(row, high_roll, VICTIM_DEX_CLUMSY))


def skill_k(level, max_level=1, table=None):
    table = table or MOB_SKILL_POWER
    level = max(0, min(SKILL_MAX_LEVEL, int(level or 0), len(table) - 1))
    return table[level] * int(max_level or 0) / 100.0


_POLY_NAMES = {"k", "atk", "lv", "str", "dex", "con", "iq"}


def eval_poly(text, names):
    """A skill formula (szPointPoly) with only + - * / ( ) numbers and the
    given names - None for anything else (no eval() of database text)."""
    import ast
    try:
        tree = ast.parse(str(text or "").strip(), mode="eval")
    except SyntaxError:
        return None

    def walk(node):
        if isinstance(node, ast.Expression):
            return walk(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return float(node.value)
        if isinstance(node, ast.Name) and node.id in names:
            return float(names[node.id])
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            value = walk(node.operand)
            return -value if isinstance(node.op, ast.USub) else value
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
            left, right = walk(node.left), walk(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            return left / right if right else 0.0
        raise ValueError(type(node).__name__)

    try:
        return walk(tree)
    except (ValueError, KeyError, OverflowError, RecursionError):
        return None


def skill_flags(info):
    return {f.strip().upper() for f in str(common.text_of((info or {}).get("setFlag")) or "").split(",") if f.strip()}


def skill_hit(row, info, level, atk, table=None):
    """(hit, why): the skill's blow for one atk (the plain blow before the
    defence), or (None, the reason it deals no estimated damage)."""
    if not info:
        return None, "nie ma jej w tabeli umiejętności – gra jej nie użyje"
    flags = skill_flags(info)
    if "SPLASH" not in flags:
        return None, "bez flagi SPLASH – potwór nią nie uderza"
    if not flags & {"USE_MELEE_DAMAGE", "USE_MAGIC_DAMAGE"}:
        return None, "nie liczy obrażeń od ataku potwora"
    if str(common.text_of(info.get("szPointOn")) or "").strip().upper() != "HP":
        return None, "nie zadaje obrażeń (działa na inny parametr)"
    if int(level or 0) <= 0:
        return None, "poziom 0 – nie zadaje obrażeń"
    names = {"k": skill_k(level, info.get("bMaxLevel"), table), "atk": atk, "lv": int(row.get("level") or 0),
             "str": int(row.get("st") or 0), "dex": int(row.get("dx") or 0), "con": int(row.get("ht") or 0),
             "iq": int(row.get("iq") or 0)}
    amount = eval_poly(common.text_of(info.get("szPointPoly")), names)
    if amount is None:
        return None, "wzoru tej umiejętności panel nie umie policzyć"
    hit = -_trunc(amount)
    return (max(1, hit) if hit > 0 else None), (None if hit > 0 else "wzór nie daje obrażeń")


def skill_label(vnum, info):
    if not info:
        return f"#{vnum}"
    name = common.text_of(info.get("szName")) or f"#{vnum}"
    extra = [label for flag, label in (("ATTACK_POISON", "trucizna"), ("ATTACK_SLOW", "spowolnienie"),
                                       ("ATTACK_STUN", "ogłuszenie")) if flag in skill_flags(info)]
    return name + (f" ({', '.join(extra)})" if extra else "")


def hit_estimate(row, skills=None, table=None):
    """{"melee": (low, high), "skills": [...], "skill_max": (low, high) or None}
    - see the formula above. skills = {vnum: skill_proto row} (load_skills)."""
    skills = skills or {}
    low_roll, high_roll = sorted((int(row.get("damage_min") or 0), int(row.get("damage_max") or 0)))
    melee = (melee_atk(row, low_roll, VICTIM_DEX_NIMBLE), melee_atk(row, high_roll, VICTIM_DEX_CLUMSY))
    found, best = [], None
    for i in SKILL_SLOTS:
        vnum = int(row.get(f"skill_vnum{i}") or 0)
        if not vnum:
            continue
        level = int(row.get(f"skill_level{i}") or 0)
        info = skills.get(vnum)
        low, why = skill_hit(row, info, level, melee[0], table)
        high, _why = skill_hit(row, info, level, melee[1], table)
        hit = (low, high) if low and high else None
        found.append({"slot": i, "col": f"skill_level{i}", "vnum": vnum, "level": level, "name": skill_label(vnum, info),
                      "k": skill_k(level, (info or {}).get("bMaxLevel"), table) if info else 0.0,
                      "hit": hit, "why": None if hit else why,
                      "ratio": (hit[1] / melee[1]) if hit and melee[1] else None})
        if hit and (best is None or hit[1] > best[1]):
            best = hit
    return {"melee": melee, "skills": found, "skill_max": best}


def fmt_hits(pair):
    """(1968, 2924) -> "1 968–2 924"."""
    if not pair:
        return "—"
    low, high = ("{:,}".format(int(v)).replace(",", " ") for v in pair)
    return low if low == high else f"{low}–{high}"


# ---- rows ------------------------------------------------------------------

ROW_COLS = ["vnum", "locale_name", "name"] + EDIT_COLS + READ_ONLY


def select_sql(where, order="level, vnum", limit=None):
    parts = []
    for col in ROW_COLS:
        if col in ("locale_name", "name"):
            parts.append(f"CAST(`{col}` AS BINARY) AS `{col}`")
        elif col == "ai_flag":
            parts.append("CAST(`ai_flag` AS CHAR) AS `ai_flag`")
        else:
            parts.append(f"`{col}`")
    sql = f"SELECT {', '.join(parts)} FROM {TABLE} WHERE {where} ORDER BY {order}"
    return sql + (f" LIMIT {int(limit)}" if limit else "")


def flags_of(value):
    return {p.strip().upper() for p in (common.text_of(value) or "").split(",") if p.strip()}


def kind_of(row):
    mob_type, rank = int(row.get("type") or 0), int(row.get("rank") or 0)
    if mob_type == 2:
        return "metin", "🗿", "Metin"
    if mob_type == 0 and rank >= 4:
        return "boss", "👑", "Boss"
    if mob_type == 0:
        return "mob", "👹", "Potwór"
    return "other", "🧍", TYPES.get(mob_type, f"Typ {mob_type}")


def decorate(row):
    row = dict(row)
    for col in ("locale_name", "name"):
        row[col] = common.text_of(row.get(col)) or ""
    row["display_name"] = row["locale_name"] or row["name"] or f"#{row['vnum']}"
    row["ai_flag"] = common.text_of(row.get("ai_flag")) or ""
    row["flags"] = flags_of(row["ai_flag"])
    row["aggressive"] = "AGGR" in row["flags"]
    row["kind"], row["kind_icon"], row["kind_name"] = kind_of(row)
    row["rank_name"] = RANKS.get(int(row.get("rank") or 0), str(row.get("rank")))
    row["type_name"] = TYPES.get(int(row.get("type") or 0), str(row.get("type")))
    row["dam_text"] = _num(row.get("dam_multiply") or 0)  # MT2009_PLUS_DB_EDITOR_MOB_SKILL_POWER_V1
    return row


def history_formatter(col, value):
    if col == "rank":
        return f"{RANKS.get(int(value), value)} [{value}]"
    if col == "battle_type":  # MT2009_PLUS_DB_EDITOR_MOB_MELEE_V1
        return f"{BATTLE_TYPES.get(int(value), value)} [{value}]"
    if col == "ai_flag":
        return ", ".join(sorted(flags_of(value))) or "(brak flag)"
    if col == "dam_multiply" and value not in (None, ""):  # MT2009_PLUS_DB_EDITOR_MOB_SKILL_POWER_V1
        try:
            return f"×{_num(float(value))}"
        except ValueError:
            return None
    return None


def search_where(args, map_vnums=None):
    """(where, params, filters) for the search / mass change form."""
    filters = {"q": (args.get("q") or "").strip(), "ranga": args.get("ranga", ""),
               "rodzaj": args.get("rodzaj") or "walka", "lvl_od": (args.get("lvl_od") or "").strip(),
               "lvl_do": (args.get("lvl_do") or "").strip(), "mapa": (args.get("mapa") or "").strip()}
    if filters["rodzaj"] not in KINDS:
        filters["rodzaj"] = "walka"
    where, params = [], []
    query = filters["q"]
    if query:
        if query.isdigit():
            where.append("(vnum=%s OR locale_name LIKE %s)")
            params += [int(query), f"%{query}%"]
        else:
            where.append("locale_name LIKE %s")
            params.append(f"%{query}%")
    if filters["ranga"].isdigit() and int(filters["ranga"]) in RANKS:
        where.append("`rank`=%s")
        params.append(int(filters["ranga"]))
    else:
        filters["ranga"] = ""
    for key, op in (("lvl_od", ">="), ("lvl_do", "<=")):
        if filters[key].isdigit():
            where.append(f"level{op}%s")
            params.append(int(filters[key]))
        else:
            filters[key] = ""
    if map_vnums is not None:
        vnums = sorted(map_vnums)[:5000] or [-1]
        where.append(f"vnum IN ({','.join(['%s'] * len(vnums))})")
        params += vnums
    kind_sql = KINDS[filters["rodzaj"]][1]
    searched = bool(where) or filters["rodzaj"] != "walka"
    if kind_sql:
        where.append(kind_sql)
    return (" AND ".join(where) or "1=1"), params, filters, searched


# ---- mass change -------------------------------------------------------------

def parse_mass(args):
    """(field, op, value, error) of the mass change form."""
    field = args.get("pole") or "max_hp"
    op = args.get("operacja") or "mul"
    raw = (args.get("wartosc") or "").strip().replace(",", ".").replace("×", "").replace("x", "")
    if field not in MASS_FIELDS:
        return field, op, None, "Wybierz, co zmienić."
    if op not in MASS_OPS:
        return field, op, None, "Wybierz rodzaj zmiany."
    if not raw:
        return field, op, None, None
    decimal = op == "mul" or field in MASS_FLOAT_FIELDS
    try:
        value = float(raw) if decimal else int(raw)
    except ValueError:
        return field, op, None, f"„{args.get('wartosc')}” nie jest liczbą" + (" (np. 2 albo 1,5)." if decimal else " całkowitą.")
    if value != value or value in (float("inf"), float("-inf")):
        return field, op, None, f"„{args.get('wartosc')}” nie jest liczbą."
    if op == "mul" and not 0.01 <= value <= 100:
        return field, op, None, "Mnożnik musi być od 0,01 do 100 (np. 2 = dwa razy więcej, 0,5 = o połowę mniej)."
    if field in MASS_FLOAT_FIELDS and op == "set":  # MT2009_PLUS_DB_EDITOR_MOB_SKILL_POWER_V1
        spec = SPECS[MASS_FIELDS[field][1][0]]
        if not spec["min"] <= value <= spec["max"]:
            return field, op, None, (f"{spec['label']}: dozwolone {_num(spec['min'])}…{_num(spec['max'])} "
                                     "(1 = zwykłe obrażenia, 2 = dwa razy mocniej).")
    return field, op, value, None


def _num(value, digits=2):
    """2.5 -> "2,5", 4.0 -> "4" - a float the Polish way, for the pages."""
    if value is None:
        return "—"
    return ("%g" % round(float(value), digits)).replace(".", ",")


def mass_value(op, value, current):
    if op == "mul":
        return int(round(int(current or 0) * value))
    if op == "add":
        return int(current or 0) + int(value)
    return int(value)


def mass_float(op, value, current):
    """MT2009_PLUS_DB_EDITOR_MOB_SKILL_POWER_V1: dam_multiply's new value."""
    current = float(current or 0)
    if op == "mul":
        return round(current * value, 2)
    if op == "add":
        return round(current + value, 2)
    return round(float(value), 2)


def mass_plan(rows, field, op, value):
    """[(row, {col: (old, new)}, [notes])] - the new values clamped to what
    the column (and the game) takes; min/max pairs kept in order.
    MT2009_PLUS_DB_EDITOR_MOB_SKILL_POWER_V1: "skill" changes only the slots
    that have a skill (skill_vnumN and skill_levelN > 0), clamped to 1..40 -
    a 0 never becomes a skill; dam_multiply is a float, rounded to 0,01 and
    clamped to its range only when it really changes (a 0 times 2 stays 0)."""
    cols = MASS_FIELDS[field][1]
    plan = []
    for row in rows:
        changes, notes = {}, []
        if field == "skill":
            for i in SKILL_SLOTS:
                col, old = f"skill_level{i}", int(row.get(f"skill_level{i}") or 0)
                if old <= 0 or not int(row.get(f"skill_vnum{i}") or 0):
                    continue
                new = mass_value(op, value, old)
                if not 1 <= new <= SPECS[col]["max"]:
                    clamped = max(1, min(SPECS[col]["max"], new))
                    notes.append(f"umiejętność {i + 1}: {new} poza zakresem 1–40 – ustawiono {clamped}")
                    new = clamped
                changes[col] = (old, new)
            if any(old != new for old, new in changes.values()):
                plan.append((row, changes, notes))
            continue
        if field in MASS_FLOAT_FIELDS:
            col = cols[0]
            spec = SPECS[col]
            old = round(float(row.get(col) or 0), 2)
            new = mass_float(op, value, old)
            if new != old and not spec["min"] <= new <= spec["max"]:
                clamped = max(spec["min"], min(spec["max"], new))
                notes.append(f"{spec['label']}: {_num(new)} poza zakresem – ustawiono {_num(clamped)}")
                new = clamped
            if new != old:
                plan.append((row, {col: (old, new)}, notes))
            continue
        for col in cols:
            spec = SPECS[col]
            new = mass_value(op, value, row.get(col))
            if new < spec["min"] or new > spec["max"]:
                clamped = max(spec["min"], min(spec["max"], new))
                notes.append(f"{spec['label']}: {new} poza zakresem – ustawiono {clamped}")
                new = clamped
            changes[col] = (int(row.get(col) or 0), new)
        if len(cols) == 2 and changes[cols[0]][1] > changes[cols[1]][1]:
            low = changes[cols[1]][1]
            changes[cols[0]] = (changes[cols[0]][0], low)
            notes.append("minimum nie może przekroczyć maksimum – wyrównano")
        if any(old != new for old, new in changes.values()):
            plan.append((row, changes, notes))
    return plan


# ---- ranged -> melee (MT2009_PLUS_DB_EDITOR_MOB_MELEE_V1) -----------------------

def melee_plan(rows):
    """[(row, {col: (old, new)}, boot_lost)] for the rows MELEE_WHERE found:
    the fields that change, and the ones apply.sh would put back at the next
    start (none today - the warning keeps that visible if it ever changes)."""
    plan = []
    for row in rows:
        changes = {col: (int(row.get(col) or 0), new) for col, new in MELEE_VALUES.items()
                   if int(row.get(col) or 0) != new}
        if changes:
            plan.append((row, changes, sorted(set(changes) & boot_cols(row["vnum"]))))
    return plan


def melee_batches(rows_fn, limit=20):
    """The editor's earlier "ranged -> melee" saves, newest first, with the
    state of each (undone / waiting for a restart / in the game)."""
    common.ensure_table()
    return rows_fn(f"""SELECT batch, MIN(id) AS first_id, MIN(changed_at) AS changed_at, MIN(who) AS who,
            COUNT(*) AS fields, COUNT(DISTINCT row_key) AS row_count, SUM(reverted_in IS NULL) AS live,
            SUM(applied_at IS NULL) AS unapplied
        FROM {common.HISTORY_TABLE} WHERE tbl=%s AND note=%s GROUP BY batch ORDER BY first_id DESC
        LIMIT {int(limit)}""", (TABLE, MELEE_NOTE))


def mass_description(field, op, value):
    label = MASS_FIELDS[field][0]
    if op == "mul":
        return f"{label} ×{('%g' % value).replace('.', ',')}"
    if field in MASS_FLOAT_FIELDS:  # MT2009_PLUS_DB_EDITOR_MOB_SKILL_POWER_V1
        return f"{label} {'+' if op == 'add' and value >= 0 else ''}{_num(value)}" if op == "add" else f"{label} = {_num(value)}"
    if op == "add":
        return f"{label} {int(value):+d}"
    return f"{label} = {int(value)}"


# ---- the pages ---------------------------------------------------------------

def install(bp, ctx):
    import dbeditor
    from dbeditor import spawnfiles

    common.init(ctx)
    common.register_table(TABLE, "vnum", ALL_SPECS, "Potwór", "dbeditor.mob_edit", history_formatter)
    common.install_history(bp, ctx)
    login_required = ctx["login_required"]

    def rows(sql, params=()):
        # looked up per call, so the panel's helpers can be swapped (tests)
        return common.ctx()["rows"](sql, params)

    def page_context():
        try:
            pending = common.pending_context()
        except Exception:
            pending = {"pending_total": 0}
        try:
            pending["pending_spawns"] = len(spawnfiles.pending_changes(spawnfiles.spool_dir()))
        except Exception:
            pending["pending_spawns"] = 0
        return pending

    def spawn_index():
        try:
            return spawnfiles.SpawnIndex.load(spawnfiles.spool_dir())
        except Exception:
            return None

    def load(vnum):
        found = rows(select_sql("vnum=%s"), (vnum,))
        return decorate(found[0]) if found else None

    # MT2009_PLUS_DB_EDITOR_MOB_SKILL_POWER_V1: the skills of the shown monsters and the mob power table
    def load_skills(mob_rows):
        vnums = sorted({int(r.get(c) or 0) for r in mob_rows for c in SKILL_VNUM_COLS} - {0})
        if not vnums:
            return {}
        try:
            found = rows("SELECT dwVnum, CAST(`szName` AS BINARY) AS szName, bMaxLevel, szPointOn, szPointPoly, "
                         f"CAST(`setFlag` AS CHAR) AS setFlag FROM world.skill_proto WHERE dwVnum IN "
                         f"({','.join(['%s'] * len(vnums))})", vnums)
        except Exception:
            return {}
        return {int(r["dwVnum"]): r for r in found}

    def power_table():
        """common.locale SKILL_POWER_BY_LEVEL as the game reads it (config.cpp) - the built-in copy if unreadable."""
        try:
            found = rows("SELECT mValue FROM common.locale WHERE mKey='SKILL_POWER_BY_LEVEL'")
            values = [int(v) for v in str(common.text_of(found[0]["mValue"])).split()][:SKILL_MAX_LEVEL + 1]
            return values if len(values) == SKILL_MAX_LEVEL + 1 else MOB_SKILL_POWER
        except Exception:
            return MOB_SKILL_POWER

    def estimates(mob_rows):
        skills, table = load_skills(mob_rows), power_table()
        return {int(r["vnum"]): hit_estimate(r, skills, table) for r in mob_rows}, skills, table

    def map_choices(index):
        if not index:
            return []
        return [(idx, index.map_title(idx), len(vnums)) for idx, vnums in sorted(index.mobs_by_map().items())
                if vnums]

    def filtered_rows(args, limit, force=False):
        index = spawn_index()
        map_vnums = None
        mapa = (args.get("mapa") or "").strip()
        if mapa.isdigit() and index:
            map_vnums = index.mobs_by_map().get(int(mapa), set())
        where, params, filters, searched = search_where(args, map_vnums)
        if map_vnums is None:
            filters["mapa"] = ""
        else:
            searched = True
        searched = searched or force
        found = rows(select_sql(where, limit=limit + 1), params) if searched else []
        return [decorate(r) for r in found[:limit]], len(found) > limit, filters, searched, index

    @bp.route("/mobs")
    @login_required
    def mobs():
        results, more, filters, searched, index = filtered_rows(request.args, LIMIT)
        where_map = {}
        if index and results:
            for row in results:
                where_map[row["vnum"]] = index.maps_of_mob(row["vnum"])[:4]
        bosses = [r for r in results if r["kind"] == "boss"]
        hits = estimates(bosses)[0] if bosses else {}
        return render_template("dbeditor/mobs.html", results=results, more=more, limit=LIMIT, f=filters,
                               hits=hits, fmt_hits=fmt_hits, hit_note=HIT_NOTE,
                               searched=searched, ranks=RANKS, kinds=KINDS, maps=map_choices(index),
                               has_index=bool(index), where_map=where_map,
                               map_title=index.map_title if index else str, **page_context())

    @bp.route("/mobs/<int:vnum>", methods=["GET", "POST"])
    @login_required
    def mob_edit(vnum):
        mob = load(vnum)
        if not mob:
            abort(404)
        raw = {}
        if request.method == "POST":
            if not common.check_csrf():
                return redirect(url_for("dbeditor.mob_edit", vnum=vnum))
            new, errors = {}, []
            for col in EDIT_COLS:
                if col in SKILL_LEVEL_COLS and not int(mob.get(col.replace("level", "vnum")) or 0):
                    continue  # MT2009_PLUS_DB_EDITOR_MOB_SKILL_POWER_V1: no skill in the slot - no level
                if col == "dam_multiply" and col in request.form and common._same(
                        SPECS[col], str(request.form.get(col)).strip().replace(",", ".") or None, mob.get(col)):
                    continue  # unchanged (a 0 from the old data is kept although under the form's minimum)
                if col == "ai_flag":
                    if "ai_flag_sent" not in request.form:
                        continue
                    value, error = common.validate(SPECS[col], request.form.getlist("ai_flag"), SPECS[col]["label"])
                elif col in request.form:
                    raw[col] = request.form.get(col, "")
                    value, error = common.validate(SPECS[col], raw[col], SPECS[col]["label"])
                else:
                    continue
                if error:
                    errors.append(error)
                else:
                    new[col] = value
            for low, high, label in (("damage_min", "damage_max", "Obrażenia"), ("gold_min", "gold_max", "Yang")):
                if low in new and high in new and new[low] > new[high]:
                    errors.append(f"{label}: minimum ({new[low]}) jest większe niż maksimum ({new[high]}).")
            if errors:
                for error in errors[:8]:
                    flash(error, "error")
                flash("Nic nie zapisano – popraw zaznaczone pola.", "error")
            else:
                try:
                    _batch, saved = common.save_rows(TABLE, [(vnum, new)], note="Edycja potwora",
                                                     label_of=lambda key: mob["display_name"])
                except Exception as exc:
                    flash(f"Nie udało się zapisać: {exc}", "error")
                    return redirect(url_for("dbeditor.mob_edit", vnum=vnum))
                if not saved:
                    flash("Brak zmian do zapisania.", "success")
                else:
                    lost = sorted({col for _k, col, *_r in saved if col in boot_cols(vnum)})
                    if lost:
                        flash(f"{BOOT_WARNING}: {', '.join(SPECS[c]['label'] for c in lost)}.", "warning")
                    flash(f"Zapisano {len(saved)} zmian(y). Zmiany czekają na zastosowanie (restart gry – „Zastosuj”).",
                          "success")
                return redirect(url_for("dbeditor.mob_edit", vnum=vnum))
        try:
            history = common.history_batches(10, TABLE, vnum)
        except Exception:
            history = []
        index = spawn_index()
        spawns = index.spawns_of_mob(vnum) if index else []
        hits, _skills, table = estimates([mob])
        return render_template("dbeditor/mobs_edit.html", mob=mob, raw=raw, specs=ALL_SPECS, ranks=RANKS,
                               hit=hits[int(mob["vnum"])], fmt_hits=fmt_hits, hit_note=HIT_NOTE,
                               skill_hint=SKILL_LEVEL_HINT, power=table, num=_num,
                               resists=RESISTS, ai_flags=AI_FLAGS, ai_labels=AI_FLAG_LABELS, history=history,
                               boot_notes=boot_notes(vnum), boot_always=sorted(boot_cols(vnum)),
                               boot_warning=BOOT_WARNING, spawns=spawns[:30], has_index=bool(index),
                               map_title=index.map_title if index else str,
                               dbe_csrf=common.csrf_token(), **common.template_helpers(), **page_context())

    @bp.route("/mobs/masowo", methods=["GET", "POST"])
    @login_required
    def mobs_mass():
        source = request.form if request.method == "POST" else request.args
        field, op, value, error = parse_mass(source)
        results, more, filters, searched, index = filtered_rows(
            source, MASS_MAX_ROWS, force=request.method == "POST" or "podglad" in source)
        plan = []
        if searched and value is not None and not error and not more:
            plan = mass_plan(results, field, op, value)
        if request.method == "POST":
            back = url_for("dbeditor.mobs_mass", podglad=1,
                           **{k: v for k, v in source.items() if k not in ("dbe_csrf", "vnums", "podglad")})
            if not common.check_csrf():
                return redirect(back)
            if error or value is None:
                flash(error or "Podaj wartość zmiany.", "error")
                return redirect(back)
            if more:
                flash(f"Filtr obejmuje ponad {MASS_MAX_ROWS} potworów – zawęź go.", "error")
                return redirect(back)
            previewed = {int(v) for v in (request.form.get("vnums") or "").split(",") if v.strip().isdigit()}
            planned = {int(row["vnum"]) for row, _c, _n in plan}
            if not plan or previewed != planned:
                flash("Lista potworów zmieniła się od podglądu – sprawdź podgląd jeszcze raz i zatwierdź ponownie.", "error")
                return redirect(back)
            description = mass_description(field, op, value)
            names = {int(row["vnum"]): row["display_name"] for row, _c, _n in plan}
            updates = [(int(row["vnum"]), {col: new for col, (_old, new) in changes.items()}) for row, changes, _n in plan]
            try:
                batch, saved = common.save_rows(TABLE, updates, note=f"Masowo: {description}",
                                                label_of=lambda key: names.get(int(key), ""))
            except Exception as exc:
                flash(f"Nie udało się zapisać: {exc}", "error")
                return redirect(back)
            lost = sorted({int(k) for k, col, *_r in saved if col in boot_cols(k)})
            if lost:
                flash(f"{BOOT_WARNING} – dotyczy {len(lost)} potworów (np. {', '.join(str(v) for v in lost[:6])}).",
                      "warning")
            flash(f"Zmieniono {len({k for k, *_r in saved})} potworów ({description}). Cofniesz to jednym kliknięciem "
                  "w historii zmian. Zmiany czekają na zastosowanie (restart gry – „Zastosuj”).", "success")
            return redirect(url_for("dbeditor.proto_history", tbl=TABLE))
        boot_hits = sum(1 for row, changes, _n in plan if set(changes) & boot_cols(row["vnum"]))
        # MT2009_PLUS_DB_EDITOR_MOB_SKILL_POWER_V1: the estimated hits before -> after, for the shown rows
        shown = plan[:MASS_PREVIEW_ROWS]
        hit_changes = {}
        if field in HIT_FIELDS and shown:
            skills, table = load_skills([row for row, _c, _n in shown]), power_table()
            for row, changes, _n in shown:
                after = dict(row, **{col: new for col, (_old, new) in changes.items()})
                hit_changes[int(row["vnum"])] = (hit_estimate(row, skills, table), hit_estimate(after, skills, table))
        return render_template("dbeditor/mobs_mass.html", hit_changes=hit_changes, fmt_hits=fmt_hits,
                               hit_note=HIT_NOTE, skill_hint=SKILL_LEVEL_HINT, num=_num, f=filters, field=field, op=op, value=value, error=error,
                               raw_value=source.get("wartosc", ""), searched=searched, more=more,
                               matched=len(results), plan=plan[:MASS_PREVIEW_ROWS], plan_total=len(plan),
                               plan_vnums=",".join(str(row["vnum"]) for row, _c, _n in plan),
                               fields=MASS_FIELDS, ops=MASS_OPS, ranks=RANKS, kinds=KINDS, maps=map_choices(index),
                               specs=SPECS, max_rows=MASS_MAX_ROWS, boot_hits=boot_hits,
                               description=mass_description(field, op, value) if value is not None else "",
                               dbe_csrf=common.csrf_token(), **page_context())

    @bp.route("/mobs/wrecz", methods=["GET", "POST"])
    @login_required
    def mobs_melee():
        """MT2009_PLUS_DB_EDITOR_MOB_MELEE_V1: preview, then one save (one
        history batch) of every ordinary ranged monster turned melee."""
        try:
            found = [decorate(r) for r in rows(select_sql(MELEE_WHERE, order="level, vnum"))]
            error = None
        except Exception as exc:  # pymysql errors: show, do not 500
            found, error = [], str(exc)
        plan = melee_plan(found)
        if request.method == "POST":
            back = url_for("dbeditor.mobs_melee")
            if not common.check_csrf():
                return redirect(back)
            previewed = {int(v) for v in (request.form.get("vnums") or "").split(",") if v.strip().isdigit()}
            planned = {int(row["vnum"]) for row, _c, _b in plan}
            if not plan:
                flash("Nie ma już zwykłych potworów walczących z dystansu – nic do zmiany.", "error")
                return redirect(back)
            if previewed != planned:
                flash("Lista potworów zmieniła się od podglądu – sprawdź podgląd jeszcze raz i zatwierdź ponownie.", "error")
                return redirect(back)
            names = {int(row["vnum"]): row["display_name"] for row, _c, _b in plan}
            updates = [(int(row["vnum"]), {col: new for col, (_old, new) in changes.items()}) for row, changes, _b in plan]
            try:
                _batch, saved = common.save_rows(TABLE, updates, note=MELEE_NOTE,
                                                 label_of=lambda key: names.get(int(key), ""))
            except Exception as exc:
                flash(f"Nie udało się zapisać: {exc}", "error")
                return redirect(back)
            lost = sorted({int(k) for k, col, *_r in saved if col in boot_cols(k)})
            if lost:
                flash(f"{BOOT_WARNING} – dotyczy {len(lost)} potworów (np. {', '.join(str(v) for v in lost[:6])}).",
                      "warning")
            flash(f"{len({k for k, *_r in saved})} potworów walczy teraz wręcz (zasięg ataku "
                  f"{MELEE_VALUES['attack_range']}). Cofniesz to jednym kliknięciem niżej albo w historii. "
                  "Gra wczyta zmianę dopiero po restarcie – kliknij „Zastosuj”.", "success")
            return redirect(back)
        try:
            done = melee_batches(rows)
        except Exception:
            done = []
        return render_template("dbeditor/mobs_melee.html", plan=plan, error=error, done=done,
                               plan_vnums=",".join(str(row["vnum"]) for row, _c, _b in plan),
                               boot_hits=sum(1 for _r, _c, lost in plan if lost), values=MELEE_VALUES,
                               battle_types=BATTLE_TYPES, where=MELEE_WHERE,
                               dbe_csrf=common.csrf_token(), **page_context())

    dbeditor.add_section("dbeditor.mobs", "👹", "Potwory i bossowie",
                         "PŻ, obrażenia, mnożnik obrażeń i siła umiejętności (z podglądem ciosów), obrona, poziom, exp i "
                         "yang, agresja, odporności – także masowo (np. ×2 PŻ bossów)")
