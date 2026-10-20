# MT2009_PLUS_YOHARA_EXE2_V1: the root's side of the Yohara gear of the second exe round (server-patches/rekawice,
# obreczjadeitu2 - the same numbers as the server's playerbot_yohara_gear.cpp):
#   * Rekawice Sung Ma (23000-23039): a Kamien (Mocy) Demonow in a socket is Owsap's number
#     apply * 10000 + stone level * 1000 + stone kind * 100 + value (apply = POINT_SUNGMA_* 184-187); the glove's own
#     Will is its base attribute (MT2009_PLUS_GLOVE_BASE_V1, GloveBaseLine);
#   * Obrecze Jadeitu (14580-14619), Kolie Jadeitu (16580-16619) and Klipsy Jadeitu (17570-17609,
#     MT2009_PLUS_JADE_JEWELLERY_V1): what the jade in the k-th socket adds to their two lines (pl-wiki, each kind).
import localeinfo_point

SUNGMA_SOCKET_MIN = 1000000
POINT_SUNGMA_STR = 184
POINT_SUNGMA_IMMUNE = 187
POINT_HIT_PCT = 197
STONE_VNUM_DEMON = 28046	# Kamien Demonow+0 (+1: 28146 ...); Kamien Mocy Demonow+0 28047 ...

# the jade in socket k (0..2) at +0..+9: the bracelets'; the necklaces' and earrings' (Precyzja +2 only in the 3rd
# socket at +9; the earrings' Will +1 in the 1st at +9) - playerbot_yohara_gear.cpp s_aJadeKinds
JADE_SOCKET_PRECISION = ((1, 1, 1, 1, 1, 1, 1, 1, 1, 1), (1, 1, 1, 1, 1, 1, 1, 1, 1, 2), (1, 1, 1, 1, 1, 1, 1, 1, 1, 2))
JADE_SOCKET_WILL = ((1, 1, 1, 1, 1, 1, 1, 1, 1, 2), (1, 1, 1, 1, 1, 1, 1, 2, 2, 2), (1, 1, 1, 1, 1, 2, 3, 3, 4, 4))
JADE_NECK_EAR_SOCKET_PRECISION = ((1, 1, 1, 1, 1, 1, 1, 1, 1, 1), (1, 1, 1, 1, 1, 1, 1, 1, 1, 1),
	(1, 1, 1, 1, 1, 1, 1, 1, 1, 2))
JADE_EAR_SOCKET_WILL = ((1, 1, 1, 1, 1, 1, 1, 1, 1, 1), (1, 1, 1, 1, 1, 1, 1, 2, 2, 2), (1, 1, 1, 1, 1, 2, 3, 3, 4, 4))
JADE_KIND_TABLES = {
	"wrist": (JADE_SOCKET_PRECISION, JADE_SOCKET_WILL),
	"neck": (JADE_NECK_EAR_SOCKET_PRECISION, JADE_SOCKET_WILL),
	"ear": (JADE_NECK_EAR_SOCKET_PRECISION, JADE_EAR_SOCKET_WILL),
}
# the +0 of each piece: (its Will - Mgly ODP, Slonca INT, Nocy WIT, Dymu SILA -, its jade, its kind)
JADE_ITEMS = {
	14580: (186, 50664, "wrist"), 14590: (187, 50661, "wrist"), 14600: (185, 50662, "wrist"), 14610: (184, 50663, "wrist"),
	16580: (186, 50664, "neck"), 16590: (187, 50661, "neck"), 16600: (185, 50662, "neck"), 16610: (184, 50663, "neck"),
	17570: (186, 50664, "ear"), 17580: (187, 50661, "ear"), 17590: (185, 50662, "ear"), 17600: (184, 50663, "ear"),
}


def IsGlove(vnum):
	return 23000 <= vnum <= 23039


def IsJadeJewellery(vnum):
	"""An Obrecz / Kolia / Klipsy Jadeitu."""
	return (vnum - vnum % 10) in JADE_ITEMS


IsJadeBracelet = IsJadeJewellery	# the V2 name


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


# MT2009_PLUS_GLOVE_BASE_V1: a glove's Will SungMa is its base attribute (the owner, 20 Oct: 5 bonuses as usual, the 6th
# and 7th from the 6/7 system) - the server keeps it in the item's yextra, bits 8-15 (YITEM, ysets.py), not in a bonus
# slot. Its kind by the glove (23000 SILA, 23010 ODP, 23020 WIT, 23030 INT), the wiki's range of each level when the
# client has not heard the value (a glove that is not the player's own: a trade, a shop, Seon-Hae's window).
GLOVE_WILL = {23000: 184, 23010: 186, 23020: 185, 23030: 187}
GLOVE_WILL_RANGE = ((3, 7), (5, 11), (9, 17), (14, 22), (19, 28), (24, 34), (29, 40), (34, 46), (39, 52), (58, 63))
POINT_GLOVE_BASE_ATTR_PCT = 251


def GloveBaseLine(vnum, extra, attrSlot):
	"""(the glove's Will line - as worn, raised by its "Atrybuty podstawowe rekawic +x%" lines -, known)."""
	point = GLOVE_WILL.get(vnum - vnum % 10)
	if not point:
		return ("", False)
	value = (extra >> 8) & 0xFF
	if value <= 0:
		low, high = GLOVE_WILL_RANGE[vnum % 10]
		text = localeinfo_point.GetApplyString(point, low) or ""
		return ((text + " - %d" % high) if text else "", False)
	pct = 0
	if attrSlot:
		for (attrType, attrValue) in attrSlot[5:7]:
			if attrType == POINT_GLOVE_BASE_ATTR_PCT:
				pct += attrValue
	if pct > 0:
		value += value * pct / 100
	return (localeinfo_point.GetApplyString(point, value) or "", True)


def JadeJewel(vnum):
	data = JADE_ITEMS.get(vnum - vnum % 10)
	return data[1] if data else 0


def JadeSocketLines(vnum, socket, attrSlot):
	"""The two lines (Precyzja, Wola) the jade in socket 0..2 adds - only to a line the item has."""
	data = JADE_ITEMS.get(vnum - vnum % 10)
	level = vnum % 10
	if not data or socket < 0 or socket > 2:
		return ("", "")
	(will, jewel, kind) = data
	(socketPrecision, socketWill) = JADE_KIND_TABLES[kind]
	hasPrecision, hasWill = False, False
	if attrSlot:
		for (attrType, attrValue) in attrSlot:
			if attrType == POINT_HIT_PCT:
				hasPrecision = True
			elif attrType == will:
				hasWill = True
	first = localeinfo_point.GetApplyString(POINT_HIT_PCT, socketPrecision[socket][level]) if hasPrecision else ""
	second = localeinfo_point.GetApplyString(will, socketWill[socket][level]) if hasWill else ""
	if not first and not second:
		return ("Bez bonus\xf3w podstawowych - jadeit nic nie dodaje", "")
	return (first or second, second if first else "")
