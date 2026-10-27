# MT2009_PLUS_YOHARA_EXE2_V1: the Sung Ma state of the player for the root (server-patches/czempion, precyzja):
#   * the map's requirements - "sungma_map <str> <hp> <move> <immune> [<hit>]" (game.py; all 0 off a Sung Ma map),
#     the 5th number the map's Precyzja (MT2009_PLUS_PRECISION_V1);
#   * the effective Sung Ma stats - the point (player.SUNGMA_*) raised by its per cent bonus (player.SUNGMA_PER_*,
#     points 193-196 of the exe of the second Yohara round), as the server counts them (playerbot_yohara_gear.cpp);
#   * the affect bar's Sung Ma icons (GF's): on a Sung Ma map one buff icon (the requirements and your values) and a
#     debuff icon for each stat below the requirement (what it costs there) and for too little Precyzja.
# The icons are GF's .sub (client-2.0.30/atlas/d_: d:/ymir work/ui/skill/common/affect/mt2009_sungma_*.sub) cut from
# skill9_common.dds (the yskill9 pack); without that picture the character window's Sung Ma icons stand in.
import app
import player

MAP = [0, 0, 0, 0, 0]	# str, hp, move, immune, hit (Precyzja)

STAT_POINT_NAMES = ("SUNGMA_STR", "SUNGMA_HP", "SUNGMA_MOVE", "SUNGMA_IMMUNE")
STAT_PER_NAMES = ("SUNGMA_PER_STR", "SUNGMA_PER_HP", "SUNGMA_PER_MOVE", "SUNGMA_PER_IMMUNE")
STAT_NAMES = ("Si\xb3a Sung Ma", "Witalno\x9c\xe6 Sung Ma", "Odporno\x9c\xe6 Sung Ma", "Inteligencja Sung Ma")
STAT_COSTS = ("obra\xbfenia zadawane potworom s\xb9 o po\xb3ow\xea mniejsze",
	"maksymalne P\xaf s\xb9 o po\xb3ow\xea mniejsze",
	"pr\xeadko\x9c\xe6 ruchu jest o po\xb3ow\xea mniejsza",
	"trucizna, ogie\xf1 i krwawienie dzia\xb3aj\xb9 rzadziej")
STAT_ICON = ("str", "hp", "move", "immune")

# client-only affect types (the server never sends these numbers)
AFFECT_SUNGMA_BUFF = 9900
AFFECT_SUNGMA_DEBUFF = (9901, 9902, 9903, 9904)
AFFECT_PRECISION_DEBUFF = 9905
ALL_AFFECTS = (AFFECT_SUNGMA_BUFF,) + AFFECT_SUNGMA_DEBUFF + (AFFECT_PRECISION_DEBUFF,)

ICON_DIR = "d:/ymir work/ui/skill/common/affect/"
ICON_ATLAS = "d:/ymir work/ui/skill9_common.dds"
FALLBACK_ICON = "d:/ymir work/ui/game/windows/char_info_sungma_%s.sub"

_shown = {}		# affect type -> description it was shown with


def SetMap(*args):
	for i in xrange(len(MAP)):
		try:
			MAP[i] = int(args[i])
		except (IndexError, ValueError):
			MAP[i] = 0


def IsSungmaMap():
	return MAP[0] > 0 or MAP[1] > 0 or MAP[2] > 0 or MAP[3] > 0 or MAP[4] > 0


def _Point(name):
	if not hasattr(player, name):
		return 0
	return player.GetStatus(getattr(player, name))


def Effective(i):
	"""The i-th Sung Ma stat (0 str, 1 hp, 2 move, 3 immune) with its per cent bonus."""
	base = _Point(STAT_POINT_NAMES[i])
	pct = max(-100, _Point(STAT_PER_NAMES[i]))
	return base * (100 + pct) / 100


# MT2009_PLUS_SUNGMA_BONUS_V1: what the Will above the map's requirement gives there (the server's playerbot_champion.cpp):
# Sila +0.01% damage at the monsters a point, Witalnosc +5.33 max HP a point, Odpornosc +1 movement speed every 100,
# Inteligencja +1% stun and slow chance every 100. No '%' in the texts: the affect bar formats its descriptions with '%'.
def Surplus(i):
	if not IsSungmaMap():
		return 0
	return max(0, Effective(i) - MAP[i])


def BonusText(i):
	"""The i-th stat's bonus above the requirement on this map ("" when none)."""
	surplus = Surplus(i)
	if surplus <= 0:
		return ""
	if 0 == i:
		return "Premia: +%.2f proc. obra\xbfe\xf1 zadawanych potworom" % (surplus / 100.0)
	if 1 == i:
		return "Premia: +%d maks. P\xaf" % (surplus * 533 / 100)
	if 2 == i:
		if surplus < 100:
			return "Nadwy\xbfka %d (pr\xeadko\x9c\xe6 ruchu +1 co 100)" % surplus
		return "Premia: +%d pr\xeadko\x9cci ruchu" % (surplus / 100)
	if surplus < 100:
		return "Nadwy\xbfka %d (omdlenie i spowolnienie +1 proc. co 100)" % surplus
	return "Premia: +%d proc. szansy na omdlenie i spowolnienie" % (surplus / 100)


def Precision():
	return max(0, _Point("HIT_PCT"))


def _Icon(name, fallback):
	try:
		if app.IsExistFile(ICON_ATLAS):
			return ICON_DIR + "mt2009_sungma_%s.sub" % name
	except:
		pass
	return FALLBACK_ICON % fallback


def _Wanted():
	"""affect type -> (icon, description, debuff) of what should be on the bar now."""
	wanted = {}
	if not IsSungmaMap() or not hasattr(player, "SUNGMA_STR"):
		return wanted
	if not hasattr(player, "CONQUEROR_LEVEL") or player.GetStatus(player.CONQUEROR_LEVEL) < 1:
		wanted[AFFECT_SUNGMA_DEBUFF[0]] = (_Icon("str_debuff", "str"),
			"Ziemia Sung Ma;Bez Poziomu Czempiona nie zranisz tutejszych potwor\xf3w.", True)
		return wanted
	lines = ["Wola Sung Ma tej mapy", " "]
	bonuses = []
	for i in xrange(4):
		value = Effective(i)
		need = MAP[i]
		lines.append("%s: %d / %d" % (STAT_NAMES[i], value, need))
		bonus = BonusText(i)	# MT2009_PLUS_SUNGMA_BONUS_V1
		if bonus and Surplus(i) >= (100 if i >= 2 else 1):
			bonuses.append(bonus)
		if need > 0 and value < need:
			wanted[AFFECT_SUNGMA_DEBUFF[i]] = (_Icon(STAT_ICON[i] + "_debuff", STAT_ICON[i]),
				"%s poni\xbfej wymaga\xf1 mapy;(%d / %d);Na tej mapie %s." % (STAT_NAMES[i], value, need, STAT_COSTS[i]), True)
	if MAP[4] > 0:
		precision = Precision()
		lines.append("Precyzja: %d / %d" % (precision, MAP[4]))
		if precision < MAP[4]:
			miss = (MAP[4] - precision) * 100 / MAP[4]
			wanted[AFFECT_PRECISION_DEBUFF] = (_Icon("control_debuff", "str"),
				"Za ma\xb3o Precyzji (%d / %d);Chybiasz tutejsze potwory w oko\xb3o %d procentach cios\xf3w." % (precision, MAP[4], miss), True)
	if len(wanted) == 0:
		lines.append(" ")
		lines.append("Spe\xb3niasz wszystkie wymagania mapy.")
	if bonuses:	# MT2009_PLUS_SUNGMA_BONUS_V1
		lines.append(" ")
		lines.extend(bonuses)
	wanted[AFFECT_SUNGMA_BUFF] = (_Icon("buff", "str"), ";".join(lines), False)
	return wanted


def Refresh(affectBar):
	"""Puts the Sung Ma icons on the affect bar (uiaffectbar.AffectShower) or takes them off."""
	if not affectBar:
		return
	import uiAffectBar
	wanted = _Wanted()
	for affect in ALL_AFFECTS:
		old = _shown.get(affect)
		new = wanted.get(affect)
		if old is not None and (new is None or old != new):
			affectBar.RemoveAffect(affect, 0)
			_shown.pop(affect, None)
			old = None
		if new is not None and old is None:
			(icon, description, debuff) = new
			uiAffectBar.AFFECT_SHOW_DATA[affect] = {"description" : description, "icon" : icon}
			if debuff:
				if affect not in uiAffectBar.AFFECT_CATEGORIES["debuff"]:
					uiAffectBar.AFFECT_CATEGORIES["debuff"].append(affect)
			affectBar.AddAffect(affect, 0, 0, 365 * 24 * 3600, 0, 0)
			_shown[affect] = new


def Clear():
	"""A new game window (warp, login): its affect bar has none of the icons; the server sends sungma_map again."""
	_shown.clear()
	for i in xrange(len(MAP)):
		MAP[i] = 0
