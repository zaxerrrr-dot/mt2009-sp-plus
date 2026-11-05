import player
import localeInfo
import nonplayer
import item

AFFECT_DICT = {
	player.POINT_MAX_HP: localeInfo.TOOLTIP_MAX_HP,
	player.POINT_MAX_SP: localeInfo.TOOLTIP_MAX_SP,
	player.POINT_HT: localeInfo.TOOLTIP_CON,
	player.POINT_IQ: localeInfo.TOOLTIP_INT,
	player.POINT_ST: localeInfo.TOOLTIP_STR,
	player.POINT_DX: localeInfo.TOOLTIP_DEX,
	player.POINT_ATT_SPEED: localeInfo.TOOLTIP_ATT_SPEED,
	player.POINT_MOV_SPEED: localeInfo.TOOLTIP_MOV_SPEED,
	player.POINT_CASTING_SPEED: localeInfo.TOOLTIP_CAST_SPEED,
	player.POINT_HP_REGEN: localeInfo.TOOLTIP_HP_REGEN,
	player.POINT_SP_REGEN: localeInfo.TOOLTIP_SP_REGEN,
	player.POINT_POISON_PCT: localeInfo.TOOLTIP_APPLY_POISON_PCT,
	player.POINT_STUN_PCT: localeInfo.TOOLTIP_APPLY_STUN_PCT,
	player.POINT_SLOW_PCT: localeInfo.TOOLTIP_APPLY_SLOW_PCT,
	player.POINT_CRITICAL_PCT: localeInfo.TOOLTIP_APPLY_CRITICAL_PCT,
	player.POINT_PENETRATE_PCT: localeInfo.TOOLTIP_APPLY_PENETRATE_PCT,
	player.POINT_ATTBONUS_WARRIOR: localeInfo.TOOLTIP_APPLY_ATTBONUS_WARRIOR,
	player.POINT_ATTBONUS_ASSASSIN: localeInfo.TOOLTIP_APPLY_ATTBONUS_ASSASSIN,
	player.POINT_ATTBONUS_SURA: localeInfo.TOOLTIP_APPLY_ATTBONUS_SURA,
	player.POINT_ATTBONUS_SHAMAN: localeInfo.TOOLTIP_APPLY_ATTBONUS_SHAMAN,
	player.POINT_ATTBONUS_MONSTER: localeInfo.TOOLTIP_APPLY_ATTBONUS_MONSTER,
	player.POINT_ATTBONUS_HUMAN: localeInfo.TOOLTIP_APPLY_ATTBONUS_HUMAN,
	player.POINT_ATTBONUS_ANIMAL: localeInfo.TOOLTIP_APPLY_ATTBONUS_ANIMAL,
	player.POINT_ATTBONUS_ORC: localeInfo.TOOLTIP_APPLY_ATTBONUS_ORC,
	player.POINT_ATTBONUS_MILGYO: localeInfo.TOOLTIP_APPLY_ATTBONUS_MILGYO,
	player.POINT_ATTBONUS_UNDEAD: localeInfo.TOOLTIP_APPLY_ATTBONUS_UNDEAD,
	player.POINT_ATTBONUS_DEVIL: localeInfo.TOOLTIP_APPLY_ATTBONUS_DEVIL,
	player.POINT_STEAL_HP: localeInfo.TOOLTIP_APPLY_STEAL_HP,
	player.POINT_STEAL_SP: localeInfo.TOOLTIP_APPLY_STEAL_SP,
	player.POINT_MANA_BURN_PCT: localeInfo.TOOLTIP_APPLY_MANA_BURN_PCT,
	player.POINT_DAMAGE_SP_RECOVER: localeInfo.TOOLTIP_APPLY_DAMAGE_SP_RECOVER,
	player.POINT_BLOCK: localeInfo.TOOLTIP_APPLY_BLOCK,
	player.POINT_DODGE: localeInfo.TOOLTIP_APPLY_DODGE,
	player.POINT_RESIST_SWORD: localeInfo.TOOLTIP_APPLY_RESIST_SWORD,
	player.POINT_RESIST_TWOHAND: localeInfo.TOOLTIP_APPLY_RESIST_TWOHAND,
	player.POINT_RESIST_DAGGER: localeInfo.TOOLTIP_APPLY_RESIST_DAGGER,
	player.POINT_RESIST_BELL: localeInfo.TOOLTIP_APPLY_RESIST_BELL,
	player.POINT_RESIST_FAN: localeInfo.TOOLTIP_APPLY_RESIST_FAN,
	player.POINT_RESIST_BOW: localeInfo.TOOLTIP_RESIST_BOW,
	player.POINT_RESIST_FIRE: localeInfo.TOOLTIP_RESIST_FIRE,
	player.POINT_RESIST_ELEC: localeInfo.TOOLTIP_RESIST_ELEC,
	player.POINT_RESIST_MAGIC: localeInfo.TOOLTIP_RESIST_MAGIC,
	player.POINT_RESIST_WIND: localeInfo.TOOLTIP_APPLY_RESIST_WIND,
	player.POINT_REFLECT_MELEE: localeInfo.TOOLTIP_APPLY_REFLECT_MELEE,
	player.POINT_REFLECT_ARROW: localeInfo.TOOLTIP_APPLY_REFLECT_ARROW,
	player.POINT_POISON_REDUCE: localeInfo.TOOLTIP_APPLY_POISON_REDUCE,
	player.POINT_KILL_SP_RECOVER: localeInfo.TOOLTIP_APPLY_KILL_SP_RECOVER,
	player.POINT_KILL_HP_RECOVERY: localeInfo.TOOLTIP_APPLY_KILL_HP_RECOVER,
	player.POINT_EXP_DOUBLE_BONUS: localeInfo.TOOLTIP_APPLY_EXP_DOUBLE_BONUS,
	player.POINT_GOLD_DOUBLE_BONUS: localeInfo.TOOLTIP_APPLY_GOLD_DOUBLE_BONUS,
	player.POINT_ITEM_DROP_BONUS: localeInfo.TOOLTIP_APPLY_ITEM_DROP_BONUS,
	player.POINT_POTION_BONUS: localeInfo.TOOLTIP_APPLY_POTION_BONUS,
	player.POINT_IMMUNE_STUN: localeInfo.TOOLTIP_APPLY_IMMUNE_STUN,
	player.POINT_IMMUNE_SLOW: localeInfo.TOOLTIP_APPLY_IMMUNE_SLOW,
	player.POINT_IMMUNE_FALL: localeInfo.TOOLTIP_APPLY_IMMUNE_FALL,
	player.POINT_BOW_DISTANCE: localeInfo.TOOLTIP_BOW_DISTANCE,
	player.POINT_DEF_GRADE_BONUS: localeInfo.TOOLTIP_DEF_GRADE,
	player.POINT_ATT_GRADE_BONUS: localeInfo.TOOLTIP_ATT_GRADE,
	player.POINT_MAGIC_ATT_GRADE_BONUS: localeInfo.TOOLTIP_MAGIC_ATT_GRADE,
	player.POINT_MAGIC_DEF_GRADE_BONUS: localeInfo.TOOLTIP_MAGIC_DEF_GRADE,
	player.POINT_MAX_STAMINA: localeInfo.TOOLTIP_MAX_STAMINA,
	player.POINT_MALL_ATTBONUS: localeInfo.TOOLTIP_MALL_ATTBONUS,
	player.POINT_MALL_DEFBONUS: localeInfo.TOOLTIP_MALL_DEFBONUS,
	player.POINT_MALL_EXPBONUS: localeInfo.TOOLTIP_MALL_EXPBONUS,
	player.POINT_MALL_ITEMBONUS: localeInfo.TOOLTIP_MALL_ITEMBONUS,
	player.POINT_MALL_GOLDBONUS: localeInfo.TOOLTIP_MALL_GOLDBONUS,
	player.POINT_SKILL_DAMAGE_BONUS: localeInfo.TOOLTIP_SKILL_DAMAGE_BONUS,
	player.POINT_NORMAL_HIT_DAMAGE_BONUS: localeInfo.TOOLTIP_NORMAL_HIT_DAMAGE_BONUS,
	player.POINT_SKILL_DEFEND_BONUS: localeInfo.TOOLTIP_SKILL_DEFEND_BONUS,
	player.POINT_NORMAL_HIT_DEFEND_BONUS: localeInfo.TOOLTIP_NORMAL_HIT_DEFEND_BONUS,
	player.POINT_RESIST_WARRIOR: localeInfo.TOOLTIP_APPLY_RESIST_WARRIOR,
	player.POINT_RESIST_ASSASSIN: localeInfo.TOOLTIP_APPLY_RESIST_ASSASSIN,
	player.POINT_RESIST_SURA: localeInfo.TOOLTIP_APPLY_RESIST_SURA,
	player.POINT_RESIST_SHAMAN: localeInfo.TOOLTIP_APPLY_RESIST_SHAMAN,
	player.POINT_MAX_HP_PCT: localeInfo.TOOLTIP_APPLY_MAX_HP_PCT,
	player.POINT_MAX_SP_PCT: localeInfo.TOOLTIP_APPLY_MAX_SP_PCT,
	player.POINT_ENERGY: localeInfo.TOOLTIP_ENERGY,
	player.POINT_COSTUME_ATTR_BONUS: localeInfo.TOOLTIP_COSTUME_ATTR_BONUS,
	player.POINT_RESIST_ICE: localeInfo.TOOLTIP_RESIST_ICE,
	player.POINT_RESIST_EARTH: localeInfo.TOOLTIP_RESIST_EARTH,
	player.POINT_RESIST_DARK: localeInfo.TOOLTIP_RESIST_DARK,
	player.POINT_RESIST_CRITICAL: localeInfo.TOOLTIP_ANTI_CRITICAL_PCT,
	player.POINT_RESIST_PENETRATE: localeInfo.TOOLTIP_ANTI_PENETRATE_PCT,
	player.POINT_MAGIC_ATT_BONUS_PER: localeInfo.TOOLTIP_MAGIC_ATTBONUS_PER,
	player.POINT_MELEE_MAGIC_ATT_BONUS_PER: localeInfo.TOOLTIP_MELEE_MAGIC_ATTBONUS_PER,
	player.POINT_PC_BANG_EXP_BONUS: localeInfo.TOOLTIP_MALL_EXPBONUS_P_STATIC,
	player.POINT_PC_BANG_DROP_BONUS: localeInfo.TOOLTIP_MALL_ITEMBONUS_P_STATIC,
	player.POINT_HIT_HP_RECOVERY: localeInfo.TOOLTIP_APPLY_HIT_HP_RECOVERY,
	player.POINT_TERROR: localeInfo.TOOLTIP_APPLY_TERROR,
	player.POINT_RESIST_NORMAL_DAMAGE: localeInfo.TOOLTIP_APPLY_RESIST_NORMAL_DAMAGE,
	player.POINT_POLYMORPH: localeInfo.TOOLTIP_POINT_POLYMORPH,
	player.POINT_ATT_BONUS: localeInfo.TOOLTIP_POINT_ATT_BONUS,
	player.POINT_ST_REGEN: localeInfo.TOOLTIP_ST_REGEN,
	player.POINT_DAGGER_ATT_GRADE_MONSTER: localeInfo.TOOLTIP_DAGGER_ATT_GRADE_MONSTER,
	player.POINT_ATT_GRADE_MONSTER: localeInfo.TOOLTIP_ATT_GRADE_MONSTER,
	player.POINT_RESIST_MONSTER_1000PCT: localeInfo.TOOLTIP_RESIST_MONSTER_1000PCT,
	player.POINT_ABSORB_DAMAGE: localeInfo.TOOLTIP_APPLY_ABSORB_DAMAGE,
	player.POINT_ABSORB_DAMAGE_MONSTER: localeInfo.TOOLTIP_APPLY_ABSORB_DAMAGE_MONSTER,
	player.POINT_IMMUNE_STUN_BREAK: localeInfo.TOOLTIP_APPLY_IMMUNE_STUN_BREAK_PCT,
	player.POINT_SKILL_DURATION: localeInfo.TOOLTIP_APPLY_SKILL_DURATION,
	player.POINT_BREAK_TEMPLE_CURSE: localeInfo.TOOLTIP_BREAK_TEMPLE_CURSE,
	player.POINT_ATTBONUS_ORC_VALLEY: localeInfo.TOOLTIP_APPLY_ATTBONUS_ORC_VALLEY,
	player.POINT_ATTBONUS_STONE: localeInfo.TOOLTIP_APPLY_ATTBONUS_STONE,
	player.POINT_ATTBONUS_BOSS: localeInfo.TOOLTIP_APPLY_ATTBONUS_BOSS,
	player.POINT_MAGIC_ATT_MONSTER: localeInfo.TOOLTIP_APPLY_MAGIC_ATT_MONSTER,
	player.POINT_BREAK_RESIST_SWORD: localeInfo.TOOLTIP_APPLY_BREAK_RESIST_SWORD,
	player.POINT_BREAK_RESIST_TWOHAND: localeInfo.TOOLTIP_APPLY_POINT_BREAK_RESIST_TWOHAND,
	player.POINT_BREAK_RESIST_DAGGER: localeInfo.TOOLTIP_APPLY_BREAK_RESIST_DAGGER,
	player.POINT_BREAK_RESIST_BELL: localeInfo.TOOLTIP_APPLY_BREAK_RESIST_BELL,
	player.POINT_BREAK_RESIST_FAN: localeInfo.TOOLTIP_APPLY_BREAK_RESIST_FAN,
	player.POINT_BREAK_RESIST_BOW: localeInfo.TOOLTIP_APPLY_BREAK_RESIST_BOW,
	player.POINT_RESIST_HUMAN: localeInfo.TOOLTIP_APPLY_RESIST_HUMAN,
	player.POINT_LEARN_CHANCE: localeInfo.TOOLTIP_POINT_LEARN_CHANCE,
	player.POINT_MAGIC_ATT: localeInfo.TOOLTIP_APPLY_MAGIC_ATT,
	player.POINT_FIRE_PCT: localeInfo.TOOLTIP_APPLY_FIRE_PCT,
	player.POINT_CONVERT_DAMAGE_TO_SP: localeInfo.TOOLTIP_APPLY_CONVERT_DAMAGE_TO_SP,
	player.POINT_DEF_BONUS: localeInfo.TOOLTIP_DEF_BONUS,
	player.POINT_DROP_RARE: localeInfo.TOOLTIP_APPLY_DROP_RARE,
	player.POINT_CURSE_PCT: localeInfo.TOOLTIP_POINT_CURSE_PCT,
	player.POINT_MAGIC_ATT_GRADE_BONUS_MONSTER: localeInfo.TOOLTIP_APPLY_MAGIC_ATT_GRADE_MONSTER,
	player.POINT_ATT_SPECIAL: localeInfo.TOOLTIP_POINT_ATT_SPECIAL,
	#player.POINT_DEATH_PENALTY: localeInfo.TOOLTIP_POINT_DEATH_PENALTY,

	## custom, only client
	991: localeInfo.TOOLTIP_RARE_PCT,
}

# if app.ENABLE_WOLFMAN_CHARACTER:
# 	AFFECT_DICT.update({
# 		item.APPLY_BLEEDING_PCT: localeInfo.TOOLTIP_APPLY_BLEEDING_PCT,
# 		item.APPLY_BLEEDING_REDUCE: localeInfo.TOOLTIP_APPLY_BLEEDING_REDUCE,
# 		item.APPLY_ATTBONUS_WOLFMAN: localeInfo.TOOLTIP_APPLY_ATTBONUS_WOLFMAN,
# 		item.APPLY_RESIST_CLAW: localeInfo.TOOLTIP_APPLY_RESIST_CLAW,
# 		item.APPLY_RESIST_WOLFMAN: localeInfo.TOOLTIP_APPLY_RESIST_WOLFMAN,
# 		item.APPLY_ATTBONUS_CLAW: localeInfo.TOOLTIP_APPLY_ATTBONUS_CLAW,
# 	})
#
# if app.ENABLE_MAGIC_REDUCTION_SYSTEM:
# 	AFFECT_DICT.update({
# 		item.APPLY_RESIST_MAGIC_REDUCTION: localeInfo.TOOLTIP_RESIST_MAGIC_REDUCTION,
# 	})
#
# AFFECT_DICT.update({
# 	item.APPLY_ENCHANT_ELECT: localeInfo.TOOLTIP_APPLY_ENCHANT_ELECT,
# 	item.APPLY_ENCHANT_FIRE: localeInfo.TOOLTIP_APPLY_ENCHANT_FIRE,
# 	item.APPLY_ENCHANT_ICE: localeInfo.TOOLTIP_APPLY_ENCHANT_ICE,
# 	item.APPLY_ENCHANT_WIND: localeInfo.TOOLTIP_APPLY_ENCHANT_WIND,
# 	item.APPLY_ENCHANT_EARTH: localeInfo.TOOLTIP_APPLY_ENCHANT_EARTH,
# 	item.APPLY_ENCHANT_DARK: localeInfo.TOOLTIP_APPLY_ENCHANT_DARK,
# })

POINT_1000PCT_Tuple = (
	player.POINT_RESIST_MONSTER_1000PCT,
)

ATTR_MAX_VALUES = {
	player.POINT_MAX_HP: 1500,
	player.POINT_MAX_SP: 250,
	player.POINT_HT: 12,
	player.POINT_IQ: 12,
	player.POINT_ST: 12,
	player.POINT_DX: 12,
	player.POINT_ATT_SPEED: 8,
	player.POINT_MOV_SPEED: 20,
	player.POINT_CASTING_SPEED: 20,
	player.POINT_HP_REGEN: 12,
	player.POINT_SP_REGEN: 12,
	player.POINT_POISON_PCT: 8,
	player.POINT_STUN_PCT: 8,
	player.POINT_SLOW_PCT: 8,
	player.POINT_CRITICAL_PCT: 10,
	player.POINT_PENETRATE_PCT: 10,
	player.POINT_ATTBONUS_HUMAN: 10,
	player.POINT_ATTBONUS_ANIMAL: 20,
	player.POINT_ATTBONUS_ORC: 20,
	player.POINT_ATTBONUS_MILGYO: 20,
	player.POINT_ATTBONUS_UNDEAD: 20,
	player.POINT_ATTBONUS_DEVIL: 20,
	player.POINT_STEAL_HP: 10,
	player.POINT_STEAL_SP: 10,
	player.POINT_MANA_BURN_PCT: 10,
	player.POINT_BLOCK: 15,
	player.POINT_DODGE: 15,
	player.POINT_RESIST_SWORD: 15,
	player.POINT_RESIST_TWOHAND: 15,
	player.POINT_RESIST_DAGGER: 15,
	player.POINT_RESIST_BELL: 15,
	player.POINT_RESIST_FAN: 15,
	player.POINT_RESIST_BOW: 15,
	player.POINT_ST_REGEN: 10,
	player.POINT_SKILL_DURATION: 12,
	player.POINT_RESIST_MAGIC: 15,
	player.POINT_MAX_STAMINA: 400,
	player.POINT_REFLECT_MELEE: 10,
	player.POINT_POISON_REDUCE: 5,
	player.POINT_MALL_EXPBONUS: 5,
	player.POINT_GOLD_DOUBLE_BONUS: 20,
	player.POINT_REFLECT_ARROW: 10,
	player.POINT_IMMUNE_STUN: 1,
	player.POINT_IMMUNE_SLOW: 1,
	player.POINT_ATT_GRADE_BONUS: 50,
}

# MT2009_PLUS_GLOBAL_BONUS_V1: the server's M2_BONUS_MODE ("BonusMode 0|1" at login, quest zywioly, game.py).
# global (2.2.31 "Bonusy jak na serwerze globalnym"): Max HP 2000, Max SP 80 (200 on a necklace - also
# orange), regeneration 30%, fire/lightning/wind resistance 15%, the experience and double-item chances 20%; the
# maxima above are mt2009's. BONUS_GLOBAL also switches uitarget.py's element icons to zywioly_global.py.
BONUS_GLOBAL = 0
ATTR_MAX_VALUES_MT2009 = dict(ATTR_MAX_VALUES)
ATTR_MAX_VALUES_GLOBAL = dict(ATTR_MAX_VALUES)
ATTR_MAX_VALUES_GLOBAL.update({
	player.POINT_MAX_HP: 2000,
	player.POINT_MAX_SP: 80,
	player.POINT_HP_REGEN: 30,
	player.POINT_SP_REGEN: 30,
	player.POINT_RESIST_FIRE: 15,
	player.POINT_RESIST_ELEC: 15,
	player.POINT_RESIST_WIND: 15,
	player.POINT_EXP_DOUBLE_BONUS: 20,
	player.POINT_ITEM_DROP_BONUS: 20,
})

def SetBonusMode(isGlobal):
	global BONUS_GLOBAL
	BONUS_GLOBAL = 1 if isGlobal else 0
	ATTR_MAX_VALUES.clear()
	ATTR_MAX_VALUES.update(ATTR_MAX_VALUES_GLOBAL if BONUS_GLOBAL else ATTR_MAX_VALUES_MT2009)

# MT2009_PLUS_PD_BONUS_V1 (attr max): the bonus maxima of this world (server-patches/pdbonus, mt2009_attrmax.cpp). At every
# login the server sends what its world.item_attr / item_attr_rare give at the highest level an item kind may roll - the
# bonus mode (mt2009 / global) and the Seban panel's editor included: "AttrMaxBegin <sets>", "AttrMax <rare>
# <apply>:<v0>/<v1>/... ..." (one value per attribute set, 0 = that kind never rolls it), "AttrMaxEnd" (game.py). The
# tooltip's gold line (uitooltip.py) asks IsMaxAttrValue; without the server's table (an older server) the fixed
# ATTR_MAX_VALUES above decide, as before.
SERVER_ATTR_MAX = {}	# (rare 0/1, POINT_*) -> [the maximum per attribute set]
SERVER_ATTR_SETS = [0]
_serverAttrMaxNew = [None]

# the server's EAttributeSet with every system of the game on (CItem::GetAttributeSetIndex)
ATTR_SET_WEAPON, ATTR_SET_BODY, ATTR_SET_WRIST, ATTR_SET_FOOTS, ATTR_SET_NECK, ATTR_SET_HEAD, ATTR_SET_SHIELD, ATTR_SET_EAR, \
	ATTR_SET_COSTUME_BODY, ATTR_SET_COSTUME_HAIR, ATTR_SET_COSTUME_WEAPON, ATTR_SET_PENDANT, ATTR_SET_GLOVE = range(13)
ATTR_SET_COUNT = 13
# ARMOR_BODY 0, HEAD 1, SHIELD 2, WRIST 3, FOOTS 4, NECK 5, EAR 6, PENDANT 7, GLOVE 8 (common/item_length.h)
_ARMOR_ATTR_SET = {0: ATTR_SET_BODY, 1: ATTR_SET_HEAD, 2: ATTR_SET_SHIELD, 3: ATTR_SET_WRIST, 4: ATTR_SET_FOOTS,
	5: ATTR_SET_NECK, 6: ATTR_SET_EAR, 7: ATTR_SET_PENDANT, 8: ATTR_SET_GLOVE}
# COSTUME_BODY 0, COSTUME_HAIR 1, COSTUME_WEAPON 4 (a sash, a mount, an aura: no set of their own)
_COSTUME_ATTR_SET = {0: ATTR_SET_COSTUME_BODY, 1: ATTR_SET_COSTUME_HAIR, 4: ATTR_SET_COSTUME_WEAPON}

def AttrMaxBegin(sets):
	try:
		SERVER_ATTR_SETS[0] = int(sets)
	except ValueError:
		SERVER_ATTR_SETS[0] = 0
	_serverAttrMaxNew[0] = {}

def AttrMaxLine(rare, tokens):
	table = _serverAttrMaxNew[0]
	if table is None:
		return
	try:
		rare = 1 if int(rare) else 0
	except ValueError:
		return
	for token in tokens:
		try:
			apply, values = token.split(":", 1)
			table[(rare, int(apply))] = [int(v) for v in values.split("/")]
		except ValueError:
			continue

def AttrMaxEnd():
	table = _serverAttrMaxNew[0]
	_serverAttrMaxNew[0] = None
	if table is None:
		return
	SERVER_ATTR_MAX.clear()
	SERVER_ATTR_MAX.update(table)

def GetAttrSetIndex(itemType, itemSubType):
	if itemType == item.ITEM_TYPE_WEAPON:
		if itemSubType in (6, 9):	# WEAPON_ARROW, WEAPON_QUIVER
			return -1
		return ATTR_SET_WEAPON
	if itemType == item.ITEM_TYPE_ARMOR:
		return _ARMOR_ATTR_SET.get(itemSubType, -1)
	if itemType == getattr(item, "ITEM_TYPE_COSTUME", 28):
		return _COSTUME_ATTR_SET.get(itemSubType, -1)
	return -1

def IsMaxAttrValue(attrType, value, slotIndex, itemType, itemSubType):
	"""True when an item's bonus line stands at this world's maximum for its kind of item."""
	if value <= 0:
		return False
	if not SERVER_ATTR_MAX:
		return ATTR_MAX_VALUES.has_key(attrType) and ATTR_MAX_VALUES[attrType] <= value
	rareStart = getattr(player, "ATTRIBUTE_SLOT_RARE_START", 5)
	rareEnd = getattr(player, "ATTRIBUTE_SLOT_RARE_END", 7)
	rare = 1 if rareStart <= slotIndex < rareEnd else 0
	row = SERVER_ATTR_MAX.get((rare, attrType))
	if not row:
		return False
	setIndex = GetAttrSetIndex(itemType, itemSubType)
	if SERVER_ATTR_SETS[0] == ATTR_SET_COUNT and 0 <= setIndex < len(row) and row[setIndex] > 0:
		return value >= row[setIndex]
	# an item kind the table does not know (a sash's absorbed lines) or a line its kind never rolls: the best of all kinds
	top = max(row)
	return top > 0 and value >= top

# MT2009_PLUS_PD_BONUS_V1 (mall multipliers): Mikstura / Medal Szczescia (POINT_MALL_GOLDBONUS) and Rekawica Zlodzieja
# (POINT_MALL_ITEMBONUS) hold +x% (the server multiplies the chance by 1 + x/100): the locale's "pomnozona o %.1f" got
# the 50 itself ("x50.0"); the line shows the multiplier, x1.5 for +50.
MALL_MULTIPLIER_TEXT = {
	player.POINT_MALL_GOLDBONUS: "Szansa na zdobycie Yang x%.1f",
	player.POINT_MALL_ITEMBONUS: "Szansa na zdobycie przedmiot\xf3w x%.1f",
}

# MT2009_PLUS_ELEMENTS_V1 (Autor: Digi Rasta, Zywioly i talizmany, nowy-system 0.28.0): the
# talisman's bonus names. 178-183 are the element powers - points of the server only (the points
# packet stops at 177), so the player module has no name for them; an item's line shows them.
# 49 / 52 (Silny przeciwko Insektom / Potworom Pustyni) are two of the talisman's random bonuses
# the dict did not name. setdefault: a name the client has already stays.
for _zywPoint, _zywName in (
		(49, "Silny przeciwko Insektom +%d%%"),
		(52, "Silny przeciwko Potworom Pustyni +%d%%"),
		(178, "Si\xb3a B\xb3yskawic +%d%%"),
		(179, "Si\xb3a Ognia +%d%%"),
		(180, "Si\xb3a Lodu +%d%%"),
		(181, "Si\xb3a Wiatru +%d%%"),
		(182, "Si\xb3a Ziemi +%d%%"),
		(183, "Si\xb3a Mroku +%d%%"),
		# MT2009_PLUS_CHAMPION_V2: the Sung Ma stats of Yohara's items (APPLY_SUNGMA_* = points 184-187)
		(getattr(player, "POINT_SUNGMA_STR", 184), "Si\xb3a Sung Ma +%d"),
		(getattr(player, "POINT_SUNGMA_HP", 185), "Witalno\x9c\xe6 Sung Ma +%d"),
		(getattr(player, "POINT_SUNGMA_MOVE", 186), "Odporno\x9c\xe6 Sung Ma +%d"),
		(getattr(player, "POINT_SUNGMA_IMMUNE", 187), "Inteligencja Sung Ma +%d"),
		# MT2009_PLUS_YOHARA_EXE2_V1: the Sung Ma per cent bonuses (GF's APPLY_SUNGMA_PER_*, points 193-196) and Precyzja
		# (GF's APPLY_HIT_PCT, point 197) - server-patches/precyzja
		(getattr(player, "POINT_SUNGMA_PER_STR", 193), "%d%% Wola SungMa (SI\xa3A)"),
		(getattr(player, "POINT_SUNGMA_PER_HP", 194), "%d%% Wola SungMa (WIT)"),
		(getattr(player, "POINT_SUNGMA_PER_MOVE", 195), "%d%% Wola SungMa (ODP)"),
		(getattr(player, "POINT_SUNGMA_PER_IMMUNE", 196), "%d%% Wola SungMa (INT)"),
		(getattr(player, "POINT_HIT_PCT", 197), "Precyzja +%d"),
	):
	AFFECT_DICT.setdefault(_zywPoint, _zywName)

# MT2009_PLUS_BONUS67_V1: the 6th/7th bonuses of the wiki the server's engine lacked (points 198-251,
# server-patches/bonusy67, tools/bonusy67/bonusy67_data.py - the same order). Server-only points (the exe's
# POINT_MAX_NUM is 198): no player.POINT_* constant, only an item's line shows them - with the wiki's words.
for _b67Point, _b67Name in (
	(198, "Otrzymujesz moc ognia na %d sek. w walce"),	# POINT_HIT_BUFF_ENCHANT_FIRE
	(199, "Otrzymujesz moc lodu na %d sek. w walce"),	# POINT_HIT_BUFF_ENCHANT_ICE
	(200, "Otrzymujesz moc b\xb3yskawic na %d sek. w walce"),	# POINT_HIT_BUFF_ENCHANT_ELEC
	(201, "Otrzymujesz moc wiatru na %d sek. w walce"),	# POINT_HIT_BUFF_ENCHANT_WIND
	(202, "Otrzymujesz moc mroku na %d sek. w walce"),	# POINT_HIT_BUFF_ENCHANT_DARK
	(203, "Otrzymujesz moc ziemi na %d sek. w walce"),	# POINT_HIT_BUFF_ENCHANT_EARTH
	(204, "Otrzymujesz odporno\x9c\xe6 na ogie\xf1 na %d sek. w walce"),	# POINT_HIT_BUFF_RESIST_FIRE
	(205, "Otrzymujesz odporno\x9c\xe6 na l\xf3d na %d sek. w walce"),	# POINT_HIT_BUFF_RESIST_ICE
	(206, "Otrzymujesz odporno\x9c\xe6 na b\xb3yskawice na %d sek. w walce"),	# POINT_HIT_BUFF_RESIST_ELEC
	(207, "Otrzymujesz odporno\x9c\xe6 na wiatr na %d sek. w walce"),	# POINT_HIT_BUFF_RESIST_WIND
	(208, "Otrzymujesz odporno\x9c\xe6 na mrok na %d sek. w walce"),	# POINT_HIT_BUFF_RESIST_DARK
	(209, "Otrzymujesz odporno\x9c\xe6 na ziemi\xea na %d sek. w walce"),	# POINT_HIT_BUFF_RESIST_EARTH
	(210, "Silny przeciwko potworom (+%d%% \xb3\xb9cznej warto\x9cci)"),	# POINT_ATTBONUS_PER_MONSTER
	(211, "Si\xb3a w walce z kamieniami Metin (+%d%% \xb3\xb9cznej warto\x9cci)"),	# POINT_ATTBONUS_PER_STONE
	(212, "Silny przeciwko potworom Zodiaku (+%d%% \xb3\xb9cznej warto\x9cci)"),	# POINT_ATTBONUS_PER_CZ
	(213, "Si\xb3a w walce z mistykami (+%d%% \xb3\xb9cznej warto\x9cci)"),	# POINT_ATTBONUS_PER_MILGYO
	(214, "Si\xb3a w walce z orkami (+%d%% \xb3\xb9cznej warto\x9cci)"),	# POINT_ATTBONUS_PER_ORC
	(215, "Si\xb3a w walce z diab\xb3ami (+%d%% \xb3\xb9cznej warto\x9cci)"),	# POINT_ATTBONUS_PER_DEVIL
	(216, "Si\xb3a w walce z insektami (+%d%% \xb3\xb9cznej warto\x9cci)"),	# POINT_ATTBONUS_PER_INSECT
	(217, "Si\xb3a w walce ze zwierz\xeatami (+%d%% \xb3\xb9cznej warto\x9cci)"),	# POINT_ATTBONUS_PER_ANIMAL
	(218, "Si\xb3a B\xb3yskawic (+%d%% \xb3\xb9cznej warto\x9cci)"),	# POINT_ENCHANT_PER_ELECT
	(219, "Si\xb3a Ognia (+%d%% \xb3\xb9cznej warto\x9cci)"),	# POINT_ENCHANT_PER_FIRE
	(220, "Si\xb3a Lodu (+%d%% \xb3\xb9cznej warto\x9cci)"),	# POINT_ENCHANT_PER_ICE
	(221, "Si\xb3a Wiatru (+%d%% \xb3\xb9cznej warto\x9cci)"),	# POINT_ENCHANT_PER_WIND
	(222, "Si\xb3a Ziemi (+%d%% \xb3\xb9cznej warto\x9cci)"),	# POINT_ENCHANT_PER_EARTH
	(223, "Si\xb3a Mroku (+%d%% \xb3\xb9cznej warto\x9cci)"),	# POINT_ENCHANT_PER_DARK
	(224, "Odporno\x9c\xe6 na Ludzi (+%d%% \xb3\xb9cznej warto\x9cci)"),	# POINT_RESIST_PER_HUMAN
	(225, "Odporno\x9c\xe6 na Magi\xea (+%d%% \xb3\xb9cznej warto\x9cci)"),	# POINT_RESIST_PER_MAGIC
	(226, "Odporno\x9c\xe6 na B\xb3yskawice (+%d%% \xb3\xb9cznej warto\x9cci)"),	# POINT_RESIST_PER_ELEC
	(227, "Odporno\x9c\xe6 na Ogie\xf1 (+%d%% \xb3\xb9cznej warto\x9cci)"),	# POINT_RESIST_PER_FIRE
	(228, "Odporno\x9c\xe6 na L\xf3d (+%d%% \xb3\xb9cznej warto\x9cci)"),	# POINT_RESIST_PER_ICE
	(229, "Odporno\x9c\xe6 na Wiatr (+%d%% \xb3\xb9cznej warto\x9cci)"),	# POINT_RESIST_PER_WIND
	(230, "Odporno\x9c\xe6 na Ziemi\xea (+%d%% \xb3\xb9cznej warto\x9cci)"),	# POINT_RESIST_PER_EARTH
	(231, "Odporno\x9c\xe6 na Mrok (+%d%% \xb3\xb9cznej warto\x9cci)"),	# POINT_RESIST_PER_DARK
	(232, "Obra\xbfenia od ataku boss\xf3w -%d%%"),	# POINT_NORMAL_HIT_DEFEND_BONUS_BOSS_OR_MORE
	(233, "Obra\xbfenia od umiej\xeatno\x9cci boss\xf3w -%d%%"),	# POINT_SKILL_DEFEND_BONUS_BOSS_OR_MORE
	(234, "Obra\xbfenia od ataku przeciwko bossom +%d%%"),	# POINT_NORMAL_HIT_DAMAGE_BONUS_BOSS_OR_MORE
	(235, "Obra\xbfenia od umiej\xeatno\x9cci przeciwko bossom +%d%%"),	# POINT_SKILL_DAMAGE_BONUS_BOSS_OR_MORE
	(236, "1. dodany bonus +%d%%"),	# POINT_FIRST_ATTRIBUTE_BONUS
	(237, "2. dodany bonus +%d%%"),	# POINT_SECOND_ATTRIBUTE_BONUS
	(238, "3. dodany bonus +%d%%"),	# POINT_THIRD_ATTRIBUTE_BONUS
	(239, "4. dodany bonus +%d%%"),	# POINT_FOURTH_ATTRIBUTE_BONUS
	(240, "5. dodany bonus +%d%%"),	# POINT_FIFTH_ATTRIBUTE_BONUS
	(241, "Podczas walki istnieje %d%% prawdopodobie\xf1stwa na odporno\x9c\xe6 na upadek (czas regeneracji 60 sek.)."),	# POINT_GLOVE_FALL_RESIST
	(242, "Atakuj potwory w pobli\xbfu podczas walki za pomoc\xb9 b\xb3yskawic, kt\xf3rych obra\xbfenia odpowiadaj\xb9 obra\xbfeniom od automatycznego ataku (czas regeneracji 15 sek.)."),	# POINT_GLOVE_LIGHTNING
	(243, "W przypadku u\xbfycia Trz\xeasienia z prawdopodobie\xf1stwem %d%% skraca kolejny czas regeneracji Trz\xeasienia o 5 sekund."),	# POINT_GLOVE_COOLDOWN_FINISH
	(244, "W przypadku u\xbfycia \x8cwiat\xb3a Gwiazd z prawdopodobie\xf1stwem od %d%% skraca kolejny czas regeneracji \x8cwiat\xb3a Gwiazd o 5 sekund."),	# POINT_GLOVE_COOLDOWN_ILGWANGPYO
	(245, "W przypadku u\xbfycia Strza\xb3u Wichury z prawdopodobie\xf1stwem od %d%% skraca kolejny czas regeneracji Strza\xb3u Wichury o 5 sekund."),	# POINT_GLOVE_COOLDOWN_PUNGLOEPO
	(246, "W przypadku u\xbfycia Piekielnego Ciosu z prawdopodobie\xf1stwem od %d%% skraca kolejny czas regeneracji Piekielnego Ciosu o 5 sekund."),	# POINT_GLOVE_COOLDOWN_GEOMAGGWI
	(247, "W przypadku u\xbfycia Fali \x8cmierci z prawdopodobie\xf1stwem od %d%% skraca kolejny czas regeneracji Fali \x8cmierci o 5 sekund."),	# POINT_GLOVE_COOLDOWN_MABEOBAGGWI
	(248, "W przypadku u\xbfycia Meteoru z prawdopodobie\xf1stwem od %d%% skraca kolejny czas regeneracji Meteoru o 5 sekund."),	# POINT_GLOVE_COOLDOWN_METEO
	(249, "W przypadku u\xbfycia Tarczy Eteru z prawdopodobie\xf1stwem od %d%% skraca kolejny czas regeneracji Tarczy Eteru o 5 sekund."),	# POINT_GLOVE_COOLDOWN_CHEONUN
	(250, "W przypadku u\xbfycia Burzy Szpon\xf3w z prawdopodobie\xf1stwem od %d%% skraca kolejny czas regeneracji Burzy Szpon\xf3w o 5 sekund."),	# POINT_GLOVE_COOLDOWN_ILIPUNGU
	(251, "Atrybuty podstawowe r\xeakawic s\xb9 zwi\xeakszone o %d %% (bonusy wbudowane r\xeakawic)"),	# POINT_GLOVE_BASE_ATTR_PCT
	):
	AFFECT_DICT.setdefault(_b67Point, _b67Name)

# MT2009_PLUS_ANTI_RESIST_MAGIC_V1: Kamien Duszy Antymagii / Bialy Kamien Antymagii (28044/28045 +0..+9) - the server's
# POINT_ANTI_RESIST_MAGIC 252 (server-patches/antimagic): a player's magic skill ignores x points of another player's
# magic resistance (a Sura gets half). The new exe has it as player.POINT_ANTI_RESIST_MAGIC (a point change; the
# character window's line, player.POINT_RESIST_MAGIC_REDUCTION) and item.APPLY_ANTI_RESIST_MAGIC; an older one: 252.
AFFECT_DICT.setdefault(getattr(player, "POINT_ANTI_RESIST_MAGIC", 252), "Ignoruje %d%% odporno\x9c\xe6 na magi\xea (PvP)")

# MT2009_PLUS_BONUS67_WIKI_V1: the 6th/7th bonuses of the wiki round 2 (server-patches/bonusy67b, points 253-255 - the
# last three numbers an item's bonus type has), the wiki's words: the body armour's "+90% PZ" line, the bleeding of
# every item but the gloves. A new exe names them (player.POINT_RESIST_COMBAT ...); an older one: the numbers.
for _b67bPoint, _b67bName in (
	(getattr(player, "POINT_RESIST_COMBAT", 253), "Je\x9cli masz powy\xbfej 90%% P\xaf, doznajesz obra\xbfenia ni\xbfsze o %d%%."),
	(getattr(player, "POINT_BLEEDING_PCT", 254), "Atak krwawienia + %d%%"),
	(getattr(player, "POINT_BLEEDING_REDUCE", 255), "Odporno\x9c\xe6 na Atak Krwawienia + %d%%"),
	):
	AFFECT_DICT.setdefault(_b67bPoint, _b67bName)

# MT2009_PLUS_BONUS67_SKILL_V1 (begin)
# The 6th/7th bonuses of the wiki round 3 (server-patches/bonusy67c, tools/bonusy67/bonusy67c_data.py - generated by
# gen_bonusy67c_misc.py): the first two-byte points (256-318) - the wiki's words; an item line of them needs the exe
# with two-byte bonus types (app.MT2009_WIDE_ATTR_EXE). "Odpornosc na Upadek" (the body armour, POINT_IMMUNE_FALL 90)
# is a chance now, no more a flag.
for _b67cPoint, _b67cName in (
	(256, "Niski ranking powoduje zwi\xeakszenie zadawanych obra\xbfe\xf1"),	# POINT_ALIGNMENT_DAMAGE_BONUS
	(257, "Silny przeciwko p\xf3\xb3-ludziom (+%d%% \xb3\xb9cznej warto\x9cci)"),	# POINT_ATTBONUS_PER_HUMAN
	(258, "Silny przeciwko nieumar\xb3ym (+%d%% \xb3\xb9cznej warto\x9cci)"),	# POINT_ATTBONUS_PER_UNDEAD
	(259, "Silny przeciwko potworom pustyni (+%d%% \xb3\xb9cznej warto\x9cci)"),	# POINT_ATTBONUS_PER_DESERT
	(260, "Absorbuje %d%% P\xaf przy u\xbfyciu wiru miecza"),	# POINT_USE_SKILL_PALBANG_HP_ABSORB
	(261, "Absorbuje %d%% P\xaf przy u\xbfyciu zasadzki"),	# POINT_USE_SKILL_AMSEOP_HP_ABSORB
	(262, "Absorbuje %d%% P\xaf przy u\xbfyciu powtarzalnego strza\xb3u"),	# POINT_USE_SKILL_YEONSA_HP_ABSORB
	(263, "Absorbuje %d%% P\xaf przy u\xbfyciu duchowego ciosu"),	# POINT_USE_SKILL_TUSOK_HP_ABSORB
	(264, "Absorbuje %d%% P\xaf przy u\xbfyciu strzelaj\xb9cego smoka"),	# POINT_USE_SKILL_YONGBI_HP_ABSORB
	(265, "Absorbuje %d%% P\xaf przy u\xbfyciu smoczego skowytu"),	# POINT_USE_SKILL_PAERYONG_HP_ABSORB
	(266, "Absorbujesz do %d%% P\xaf przy u\xbfyciu przywo\xb3ania b\xb3yskawicy"),	# POINT_USE_SKILL_BYEURAK_HP_ABSORB
	(267, "Absorbuje %d%% P\xaf przy u\xbfyciu burzowego szponu"),	# POINT_USE_SKILL_CHAIN_HP_ABSORB
	(268, "Czas regeneracji trzystronnego ci\xeacia: -%d sek. z 10%% szans"),	# POINT_USE_SKILL_SAMYEON_NEXT_COOLTIME_DECREASE_10PER
	(269, "Czas regeneracji uderzenia miecza: -%d sek. z 10%% szans"),	# POINT_USE_SKILL_GEOMPUNG_NEXT_COOLTIME_DECREASE_10PER
	(270, "Czas regeneracji szybkiego ataku: -%d sek. z 10%% szans"),	# POINT_USE_SKILL_GUNGSIN_NEXT_COOLTIME_DECREASE_10PER
	(271, "Czas regeneracji deszczu strza\xb3: -%d sek. z 10%% szans"),	# POINT_USE_SKILL_KWANKYEOK_NEXT_COOLTIME_DECREASE_10PER
	(272, "Czas regeneracji smoczego wiru: -%d sek. z 10%% szans"),	# POINT_USE_SKILL_YONGKWON_NEXT_COOLTIME_DECREASE_10PER
	(273, "Czas regeneracji mrocznego uderzenia: -%d sek. z 10%% szans"),	# POINT_USE_SKILL_MARYUNG_NEXT_COOLTIME_DECREASE_10PER
	(274, "Czas regeneracji lataj\xb9cego talizmanu: -%d sek. z 10%% szans"),	# POINT_USE_SKILL_BIPABU_NEXT_COOLTIME_DECREASE_10PER
	(275, "Czas regeneracji b\xb3yskawicznego rzutu: -%d sek. z 10%% szans"),	# POINT_USE_SKILL_NOEJEON_NEXT_COOLTIME_DECREASE_10PER
	(276, "Czas regeneracji trzystronnego ci\xeacia: -%d sek. z 20%% szans"),	# POINT_USE_SKILL_SAMYEON_NEXT_COOLTIME_DECREASE_20PER
	(277, "Czas regeneracji uderzenia miecza: -%d sek. z 20%% szans"),	# POINT_USE_SKILL_GEOMPUNG_NEXT_COOLTIME_DECREASE_20PER
	(278, "Czas regeneracji szybkiego ataku: -%d sek. z 20%% szans"),	# POINT_USE_SKILL_GUNGSIN_NEXT_COOLTIME_DECREASE_20PER
	(279, "Czas regeneracji deszczu strza\xb3: -%d sek. z 20%% szans"),	# POINT_USE_SKILL_KWANKYEOK_NEXT_COOLTIME_DECREASE_20PER
	(280, "Czas regeneracji smoczego wiru: -%d sek. z 20%% szans"),	# POINT_USE_SKILL_YONGKWON_NEXT_COOLTIME_DECREASE_20PER
	(281, "Czas regeneracji mrocznego uderzenia: -%d sek. z 20%% szans"),	# POINT_USE_SKILL_MARYUNG_NEXT_COOLTIME_DECREASE_20PER
	(282, "Czas regeneracji lataj\xb9cego talizmanu: -%d sek. z 20%% szans"),	# POINT_USE_SKILL_BIPABU_NEXT_COOLTIME_DECREASE_20PER
	(283, "Czas regeneracji b\xb3yskawicznego rzutu: -%d sek. z 20%% szans"),	# POINT_USE_SKILL_NOEJEON_NEXT_COOLTIME_DECREASE_20PER
	(284, "Czas trwania aury miecza +%d sek."),	# POINT_SKILL_DURATION_INCREASE_GEOMKYUNG
	(285, "Czas trwania krycia si\xea +%d sek."),	# POINT_SKILL_DURATION_INCREASE_EUNHYUNG
	(286, "Czas trwania bezszelestnego chodu +%d sek."),	# POINT_SKILL_DURATION_INCREASE_GYEONGGONG
	(287, "Na %d sek. otrzymujesz bonus do ataku przy u\xbfyciu woli \xbfycia"),	# POINT_USE_SKILL_GIHYEOL_ATT_GRADE_BONUS
	(288, "Na %d sek. otrzymujesz bonus do ataku przy u\xbfyciu kr\xeagu mieczy"),	# POINT_USE_SKILL_NOEGEOM_ATT_GRADE_BONUS
	(289, "Na %d sek. otrzymujesz bonus do ataku przy u\xbfyciu truj\xb9cej chmury"),	# POINT_USE_SKILL_SANGONG_ATT_GRADE_BONUS
	(290, "Na %d sek. otrzymujesz bonus do ataku przy u\xbfyciu zatrutej strza\xb3y"),	# POINT_USE_SKILL_GIGUNG_ATT_GRADE_BONUS
	(291, "Na %d sek. otrzymujesz bonus do ataku przy u\xbfyciu strachu"),	# POINT_USE_SKILL_TERROR_ATT_GRADE_BONUS
	(292, "Na %d sek. otrzymujesz bonus do ataku przy u\xbfyciu ognistego ducha"),	# POINT_USE_SKILL_MUYEONG_ATT_GRADE_BONUS
	(293, "Na %d sek. zwi\xeaksza bonus do ataku przy u\xbfyciu pomocy smoka"),	# POINT_USE_SKILL_GICHEON_ATT_GRADE_BONUS
	(294, "Na %d sek. otrzymujesz bonus do ataku przy u\xbfyciu leczenia"),	# POINT_USE_SKILL_JEONGEOP_ATT_GRADE_BONUS
	(295, "Na %d sek. otrzymujesz bonus do obrony przy u\xbfyciu czarowanego ostrza"),	# POINT_USE_SKILL_GWIGEOM_DEF_BONUS
	(296, "Na %d sek. otrzymujesz bonus do obrony przy u\xbfyciu b\xb3ogos\xb3awie\xf1stwa"),	# POINT_USE_SKILL_HOSIN_DEF_BONUS
	(297, "Na %d sek. otrzymujesz bonus do obrony przy u\xbfyciu ataku+"),	# POINT_USE_SKILL_JEUNGRYEOK_DEF_BONUS
	(298, "Na %d sek. zwi\xeaksza szybko\x9c\xe6 zakl\xeacia przy u\xbfyciu silnego cia\xb3a"),	# POINT_USE_SKILL_CHUNKEON_CASTING_SPEED
	(299, "Na %d sek. zwi\xeaksza szybko\x9c\xe6 zakl\xeacia przy u\xbfyciu mrocznej ochrony"),	# POINT_USE_SKILL_MANASHIELD_CASTING_SPEED
	(300, "Trzystronne ci\xeacie ma %d%% szans na og\xb3uszenie przeciwnika"),	# POINT_USE_SKILL_SAMYEON_STUN
	(301, "Duchowe uderzenie ma %d%% szans na og\xb3uszenie przeciwnika"),	# POINT_USE_SKILL_GIGONGCHAM_STUN
	(302, "Wiruj\xb9cy sztylet ma %d%% szans na og\xb3uszenie przeciwnika"),	# POINT_USE_SKILL_CHARYUN_STUN
	(303, "Rozproszenie magii ma %d%% szans na og\xb3uszenie przeciwnika"),	# POINT_USE_SKILL_PABEOB_STUN
	(304, "Mroczna sfera ma %d%% szans na og\xb3uszenie przeciwnika"),	# POINT_USE_SKILL_MAHWAN_STUN
	(305, "Walni\xeacie ma %d%% szans na oddanie przeciwnikowi"),	# POINT_USE_SKILL_GYOKSAN_KNOCKBACK
	(306, "Wolno dzia\xb3aj\xb9ca trucizna ma %d%% szans na oddanie przeciwnikowi"),	# POINT_USE_SKILL_SEOMJEON_KNOCKBACK
	(307, "Deszcz strza\xb3 ma %d%% szans na oddanie przeciwnikowi"),	# POINT_USE_SKILL_KWANKYEOK_KNOCKBACK
	(308, "Uderzenie palcem ma %d%% szans na oddanie przeciwnikowi"),	# POINT_USE_SKILL_SWAERYUNG_KNOCKBACK
	(309, "Ogniste uderzenie ma %d%% szans na oddanie przeciwnikowi"),	# POINT_USE_SKILL_HWAYEOMPOK_KNOCKBACK
	(310, "Obra\xbfenia od trzystronnego ci\xeacia +%d%%"),	# POINT_SKILL_DAMAGE_SAMYEON
	(311, "Obra\xbfenia od uderzenia miecza +%d%%"),	# POINT_SKILL_DAMAGE_GEOMPUNG
	(312, "Obra\xbfenia od szybkiego ataku +%d%%"),	# POINT_SKILL_DAMAGE_GUNGSIN
	(313, "Obra\xbfenia od deszczu strza\xb3 +%d%%"),	# POINT_SKILL_DAMAGE_KWANKYEOK
	(314, "Obra\xbfenia od smoczego wiru +%d%%"),	# POINT_SKILL_DAMAGE_YONGKWON
	(315, "Obra\xbfenia od mrocznego uderzenia +%d%%"),	# POINT_SKILL_DAMAGE_MARYUNG
	(316, "Obra\xbfenia od lataj\xb9cego talizmanu +%d%%"),	# POINT_SKILL_DAMAGE_BIPABU
	(317, "Obra\xbfenia od strzelaj\xb9cego smoka +%d%%"),	# POINT_SKILL_DAMAGE_YONGBI
	(318, "Obra\xbfenia od b\xb3yskawicznego rzutu +%d%%"),	# POINT_SKILL_DAMAGE_NOEJEON
	):
	AFFECT_DICT.setdefault(_b67cPoint, _b67cName)
AFFECT_DICT[getattr(player, "POINT_IMMUNE_FALL", 90)] = "Odporno\x9c\xe6 na Upadek +%d%%"
# MT2009_PLUS_BONUS67_SKILL_V1 (end)
# MT2009_PLUS_BONUS67_WIKI_NAMES_V1 (begin) (poprawki 3.0.10 #1)
# Every 6th/7th bonus line word for word as on the pl-wiki's "6. i 7. bonus" - its capitals and punctuation, its own
# slips ("z orkom", "w walce diablami") - fixed to "z orkami" / "z diablami" at the owner's word (4 Nov). "Max PZ",
# "Max PE" and "Sila w walce z kamieniami Metin" are the wiki's names of those bonuses on any item. The wiki words the
# shield's block and the PE absorption of the 6th/7th bonus otherwise than the bonus list does: an item's 6th/7th
# slot shows those two through GetRareApplyString (uitooltip.py), its 1st-5th slots keep the list's names.
AFFECT_DICT[player.POINT_MAX_HP] = "Max P\xaf: +%d"
AFFECT_DICT[player.POINT_MAX_SP] = "Max PE: +%d"
AFFECT_DICT[getattr(player, "POINT_ATTBONUS_STONE", 149)] = "Si\xb3a w walce z kamieniami Metin +%d%%"
RARE_AFFECT_DICT = {
	player.POINT_STEAL_SP: "Absorbuje obra\xbfenia do %d%% jako PE",
	player.POINT_BLOCK: "%d%% szans na zablokowanie obra\xbfe\xf1 od ataku",
}

def GetRareApplyString(affectType, affectValue):
	"""The text of an item's 6th/7th bonus line (the wiki's words where they differ from the bonus list's)."""
	if affectValue and affectType in RARE_AFFECT_DICT:
		return RARE_AFFECT_DICT[affectType] % affectValue
	return GetApplyString(affectType, affectValue)
# MT2009_PLUS_BONUS67_WIKI_NAMES_V1 (end)
# MT2009_PLUS_ALCHEMY_WIKI_NAMES_V1 (begin) (the owner, 4 Nov 2026: the alchemy bonus names exactly as on the pl-wiki)
# A dragon stone's bonus lines (uitooltip.py, ITEM_TYPE_DS) in the wiki's alchemy words and form ("6% Odpornosc na Mrok",
# "+2.400 Max. PZ"): the DS_APPLY_<POINT> lines of locale/pl/locale_game.txt (client-2.0.30/tools/alchemia, the list
# and its wiki sources in alchemia_names.py). DS_APPLY_BASIC_<POINT> names the stone's 1st (basic) bonus where the wiki
# names it otherwise than an additional one (Jadeit "PE" / Granat "PZ"). "%s" in a name = the value grouped by dots.
# A bonus without a line (the mt2009 bonus mode's race bonuses; a locale file without the lines) keeps the shared name
# (GetApplyString) - the names of every other item are not touched. DS_FALLBACK_POINTS: the points the exe's player
# module has no POINT_ name for (the element powers 178-183, Sung Ma 184-187, Precyzja 197).
DS_FALLBACK_POINTS = {
	"ENCHANT_ELECT": 178, "ENCHANT_FIRE": 179, "ENCHANT_ICE": 180, "ENCHANT_WIND": 181, "ENCHANT_EARTH": 182,
	"ENCHANT_DARK": 183, "SUNGMA_STR": 184, "SUNGMA_HP": 185, "SUNGMA_MOVE": 186, "SUNGMA_IMMUNE": 187,
	"HIT_PCT": 197, "ATTBONUS_STONE": 149,
}
_dsApplyNames = None

def _LoadDragonSoulApplyNames():
	basic, other = {}, {}
	for key in dir(localeInfo):
		if not key.startswith("DS_APPLY_"):
			continue
		text = getattr(localeInfo, key)
		if not isinstance(text, str) or not text:
			continue
		name, table = key[9:], other
		if name.startswith("BASIC_"):
			name, table = name[6:], basic
		point = getattr(player, "POINT_" + name, DS_FALLBACK_POINTS.get(name))
		if point is not None:
			table[point] = text
	return (basic, other)

def _DragonSoulNumber(value):
	digits = str(abs(int(value)))
	groups = []
	while len(digits) > 3:
		groups.insert(0, digits[-3:])
		digits = digits[:-3]
	groups.insert(0, digits)
	return ("-" if value < 0 else "") + ".".join(groups)

def GetDragonSoulApplyString(slotIndex, affectType, affectValue):
	"""The text of a dragon stone's bonus line (slot 0 = the stone's basic bonus) - the pl-wiki's alchemy name."""
	global _dsApplyNames
	if not affectType or not affectValue:
		return None
	if _dsApplyNames is None:
		_dsApplyNames = _LoadDragonSoulApplyNames()
	text = None
	if 0 == slotIndex:
		text = _dsApplyNames[0].get(affectType)
	if text is None:
		text = _dsApplyNames[1].get(affectType)
	if text is None:
		return GetApplyString(affectType, affectValue)
	try:
		if "%s" in text:
			return text % _DragonSoulNumber(affectValue)
		return text % affectValue
	except (TypeError, ValueError):
		return GetApplyString(affectType, affectValue)
# MT2009_PLUS_ALCHEMY_WIKI_NAMES_V1 (end)
def Is1000PCT(affectType):
	return affectType in POINT_1000PCT_Tuple

def GetApplyString(affectType, affectValue):
	if 0 == affectType:
		return None

	if 0 == affectValue:
		return None

	if affectType == player.POINT_POLYMORPH:
		return AFFECT_DICT[affectType] % nonplayer.GetMonsterName(affectValue)

	if affectType in MALL_MULTIPLIER_TEXT: # MT2009_PLUS_PD_BONUS_V1 (mall multipliers)
		return MALL_MULTIPLIER_TEXT[affectType] % (1.0 + float(affectValue) / 100.0)

	if Is1000PCT(affectType):
		affectValue = float(affectValue)/10

	if affectType == player.POINT_LEARN_CHANCE:
		affectValue = 1.0 + float(affectValue)/100

	try:
		return AFFECT_DICT[affectType](affectValue)
	except:
		try:
			return AFFECT_DICT[affectType] % (affectValue)
		except TypeError:
			return AFFECT_DICT[affectType]
		except KeyError:
			return "UNKNOWN_TYPE[%s] %s" % (affectType, affectValue)

# def GetMarcin():
# 	for i,v in AFFECT_DICT.iteritems():
# 		print str(i) + "()" + GetApplyString(i, 12345) + "!@#$ "

# MT2009_PLUS_LANG_APPLY_TEXT_V1: a bonus line in the client's language as a whole - the tooltip colours the numbers of a
# maximal bonus (uitooltip.format_attributes: "|cffffb52b15|r") and splits long ones, after which the text sink of
# ui.TextLine (mt2009lang, MT2009_PLUS_LANG_V1) no longer recognised the Polish line (Rekawice Weza 23000: the lightning
# line stayed Polish in an English client). The formatted Polish line is translated here (the language's %-templates
# fill the values back in), before anyone colours or splits it. Polish clients: unchanged.
def _LangWrap(func):
	def wrapped(*args, **kwargs):
		text = func(*args, **kwargs)
		if text.__class__ is str and text:
			try:
				import mt2009lang
				return mt2009lang.Translate(text)
			except Exception:
				return text
		return text
	wrapped.__doc__ = func.__doc__
	return wrapped

GetApplyString = _LangWrap(GetApplyString)
GetRareApplyString = _LangWrap(GetRareApplyString)
GetDragonSoulApplyString = _LangWrap(GetDragonSoulApplyString)
