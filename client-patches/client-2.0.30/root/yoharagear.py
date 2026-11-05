# MT2009_PLUS_YOHARA_EXE2_V1: the root's side of the Yohara gear of the second exe round (server-patches/rekawice,
# obreczjadeitu2 - the same numbers as the server's playerbot_yohara_gear.cpp):
#   * Rekawice Sung Ma (23000-23039): a Kamien (Mocy) Demonow in a socket is Owsap's number
#     apply * 10000 + stone level * 1000 + stone kind * 100 + value (apply = POINT_SUNGMA_* 184-187); the glove's own
#     Will is its base attribute (MT2009_PLUS_GLOVE_BASE_V1, GloveBaseLine);
#   * Obrecze Jadeitu (14580-14619), Kolie Jadeitu (16580-16619) and Klipsy Jadeitu (17570-17609,
#     MT2009_PLUS_JADE_JEWELLERY_V1): what the jade in the k-th socket adds to their two lines (pl-wiki, each kind); the
#     two lines are their base attribute (MT2009_PLUS_JADE_BASE_V1, JadeBaseLines), the 6th / 7th the 6/7 system's.
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
	# MT2009_PLUS_BRAKI_WIKI_V1: Rekawice Weza 23050-23089 too
	return 23000 <= vnum <= 23039 or 23050 <= vnum <= 23089


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
# MT2009_PLUS_BRAKI_WIKI_V1: Rekawice Weza (SILA 23050, ODP 23060, WIT 23070, INT 23080) - the pl-wiki's Will ranges
GLOVE_WILL.update({23050: 184, 23060: 186, 23070: 185, 23080: 187})
SERPENT_GLOVE_WILL_RANGE = ((6, 9), (10, 13), (14, 19), (19, 25), (24, 31), (30, 38), (36, 44), (42, 50), (49, 58), (69, 78))
POINT_GLOVE_BASE_ATTR_PCT = 251


def GloveBaseLine(vnum, extra, attrSlot):
	"""(the glove's Will line - as worn, raised by its "Atrybuty podstawowe rekawic +x%" lines -, known)."""
	point = GLOVE_WILL.get(vnum - vnum % 10)
	if not point:
		return ("", False)
	value = (extra >> 8) & 0xFF
	if value <= 0:
		low, high = (SERPENT_GLOVE_WILL_RANGE if vnum >= 23050 else GLOVE_WILL_RANGE)[vnum % 10]
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


# MT2009_PLUS_JADE_BASE_V1 (3.0.7, the owner: a Kolia Jadeitu Nocy+9 with five bonuses "already had" the 6th/7th): the
# two lines of a piece of jade jewellery (Precyzja, the Will of the jade) are its base attribute - the server keeps them
# in the item's yextra (YITEM, ysets.py): bits 8-15 the Will, 16-23 Precyzja (0: none), bit 24 set once they are there;
# the 6th and 7th bonus slots are the 6/7 system's (Seon-Hae, 71051, 71052 / 72351). A piece the server has not moved
# yet (or the client has not heard: a trade, a shop, Seon-Hae's window) - the old lines of its bonus slots, else the
# wiki's ranges of its level.
JADE_BASE_KNOWN = 1 << 24
JADE_PRECISION_RANGE = ((1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 8), (8, 10), (9, 11), (10, 14))
JADE_WILL_RANGE = ((1, 2), (3, 4), (5, 6), (7, 8), (9, 10), (11, 12), (13, 14), (15, 17), (18, 20), (21, 24))
JADE_EAR_WILL_RANGE = ((1, 2), (2, 4), (3, 6), (5, 8), (7, 10), (9, 12), (13, 14), (15, 17), (18, 20), (21, 24))


def JadeLegacySlots(vnum, attrSlot):
	"""The 6th/7th slots holding a piece's old base line (Precyzja or its Will - the 6/7 pool never gives them)."""
	data = JADE_ITEMS.get(vnum - vnum % 10)
	if not data or not attrSlot:
		return []
	return [i for i in xrange(5, min(7, len(attrSlot))) if attrSlot[i][0] in (POINT_HIT_PCT, data[0])]


def JadeBase(vnum, extra, attrSlot):
	"""(Precyzja, Will, known) of a piece of jade jewellery: its base lines (0 = none); known False - the ranges."""
	data = JADE_ITEMS.get(vnum - vnum % 10)
	if not data:
		return (0, 0, False)
	legacy = JadeLegacySlots(vnum, attrSlot)
	if legacy:
		precision, will = 0, 0
		for i in legacy:
			if attrSlot[i][0] == POINT_HIT_PCT:
				precision = attrSlot[i][1]
			else:
				will = attrSlot[i][1]
		return (precision, will, True)
	if extra & JADE_BASE_KNOWN:
		return ((extra >> 16) & 0xFF, (extra >> 8) & 0xFF, True)
	return (0, 0, False)


def JadeBaseLines(vnum, extra, attrSlot):
	"""[(text, known)] - the base lines of a piece of jade jewellery to draw as its own lines."""
	data = JADE_ITEMS.get(vnum - vnum % 10)
	if not data:
		return []
	(will, jewel, kind) = data
	level = vnum % 10
	(precision, willValue, known) = JadeBase(vnum, extra, attrSlot)
	if known:
		lines = []
		if precision > 0:
			lines.append((localeinfo_point.GetApplyString(POINT_HIT_PCT, precision) or "", True))
		if willValue > 0:
			lines.append((localeinfo_point.GetApplyString(will, willValue) or "", True))
		return [l for l in lines if l[0]]
	lines = []
	for (point, (low, high)) in ((POINT_HIT_PCT, JADE_PRECISION_RANGE[level]),
			(will, (JADE_EAR_WILL_RANGE if kind == "ear" else JADE_WILL_RANGE)[level])):
		text = localeinfo_point.GetApplyString(point, low) or ""
		if text:
			lines.append((text + " - %d" % high, False))
	return lines


def JadeJewel(vnum):
	data = JADE_ITEMS.get(vnum - vnum % 10)
	return data[1] if data else 0


def JadeSocketLines(vnum, socket, attrSlot, extra=0):
	"""The two lines (Precyzja, Wola) the jade in socket 0..2 adds - only to a line the item has."""
	data = JADE_ITEMS.get(vnum - vnum % 10)
	level = vnum % 10
	if not data or socket < 0 or socket > 2:
		return ("", "")
	(will, jewel, kind) = data
	(socketPrecision, socketWill) = JADE_KIND_TABLES[kind]
	# MT2009_PLUS_JADE_BASE_V1: the lines of its base (unknown: the Will always, Precyzja most likely)
	(precision, willValue, known) = JadeBase(vnum, extra, attrSlot)
	hasPrecision = precision > 0 or not known
	hasWill = willValue > 0 or not known
	first = localeinfo_point.GetApplyString(POINT_HIT_PCT, socketPrecision[socket][level]) if hasPrecision else ""
	second = localeinfo_point.GetApplyString(will, socketWill[socket][level]) if hasWill else ""
	if not first and not second:
		return ("Bez bonus\xf3w podstawowych - jadeit nic nie dodaje", "")
	return (first or second, second if first else "")
