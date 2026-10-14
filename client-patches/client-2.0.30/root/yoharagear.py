# -*- coding: cp1250 -*-
# MT2009_PLUS_YOHARA_EXE2_V1: the root's side of the Yohara gear of the second exe round (server-patches/rekawice,
# obreczjadeitu2 - the same numbers as the server's playerbot_yohara_gear.cpp):
#   * Rekawice Sung Ma (23000-23039): a Kamien (Mocy) Demonow in a socket is Owsap's number
#     apply * 10000 + stone level * 1000 + stone kind * 100 + value (apply = POINT_SUNGMA_* 184-187);
#   * Obrecze Jadeitu (14580-14619): what the jade in the k-th socket adds to its two lines (pl-wiki).
import localeinfo_point

SUNGMA_SOCKET_MIN = 1000000
POINT_SUNGMA_STR = 184
POINT_SUNGMA_IMMUNE = 187
POINT_HIT_PCT = 197
STONE_VNUM_DEMON = 28046	# Kamien Demonow+0 (+1: 28146 ...); Kamien Mocy Demonow+0 28047 ...

JADE_SOCKET_PRECISION = ((1, 1, 1, 1, 1, 1, 1, 1, 1, 1), (1, 1, 1, 1, 1, 1, 1, 1, 1, 2), (1, 1, 1, 1, 1, 1, 1, 1, 1, 2))
JADE_SOCKET_WILL = ((1, 1, 1, 1, 1, 1, 1, 1, 1, 2), (1, 1, 1, 1, 1, 1, 1, 2, 2, 2), (1, 1, 1, 1, 1, 2, 3, 3, 4, 4))
JADE_WILL = {14580: 186, 14590: 187, 14600: 185, 14610: 184}	# Mgly ODP, Slonca INT, Nocy WIT, Dymu SILA
JADE_JEWEL = {14580: 50664, 14590: 50661, 14600: 50662, 14610: 50663}


def IsGlove(vnum):
	return 23000 <= vnum <= 23039


def IsJadeBracelet(vnum):
	return 14580 <= vnum <= 14619


def DecodeSungmaSocket(number):
	"""(point, value, stone level, stone kind) of a Sung Ma stone's socket, None for anything else."""
	if number < SUNGMA_SOCKET_MIN:
		return None
	point = (number / 10000) % 1000
	if point < POINT_SUNGMA_STR or point > POINT_SUNGMA_IMMUNE:
		return None
	return (point, number % 100, (number / 1000) % 10, (number / 100) % 10)


def GloveSocketData(number):
	"""(the stone's vnum for its icon and name, the line) of a glove's socket - or (number, "") as it is."""
	decoded = DecodeSungmaSocket(number)
	if not decoded:
		return (number, "")
	(point, value, level, kind) = decoded
	vnum = STONE_VNUM_DEMON + level * 100 + (1 if kind == 2 else 0)
	return (vnum, localeinfo_point.GetApplyString(point, value) or "")


def JadeJewel(vnum):
	return JADE_JEWEL.get(vnum - vnum % 10, 0)


def JadeSocketLines(vnum, socket, attrSlot):
	"""The two lines (Precyzja, Wola) the jade in socket 0..2 adds - only to a line the bracelet has."""
	base = vnum - vnum % 10
	level = vnum % 10
	if base not in JADE_WILL or socket < 0 or socket > 2:
		return ("", "")
	hasPrecision, hasWill = False, False
	if attrSlot:
		for (attrType, attrValue) in attrSlot:
			if attrType == POINT_HIT_PCT:
				hasPrecision = True
			elif attrType == JADE_WILL[base]:
				hasWill = True
	first = localeinfo_point.GetApplyString(POINT_HIT_PCT, JADE_SOCKET_PRECISION[socket][level]) if hasPrecision else ""
	second = localeinfo_point.GetApplyString(JADE_WILL[base], JADE_SOCKET_WILL[socket][level]) if hasWill else ""
	if not first and not second:
		return ("Bez bonus\xf3w podstawowych - jadeit nic nie dodaje", "")
	return (first or second, second if first else "")
