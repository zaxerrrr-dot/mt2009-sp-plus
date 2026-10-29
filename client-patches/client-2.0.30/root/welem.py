# MT2009_PLUS_WEAPON_ELEMENT_V1: the client's side of Zaczarowanie Zywiolu Broni (server-patches/zywiolbroni; based on
# the "[System] Elemental Spell" package by WorldArd, the windows and graphics of the GF client).
# The server tells every enchanted weapon (or the sash that absorbed one) by "WELEM <window> <cell> <packed>"
# (game.py -> OnServer): window 0 = forget everything (a new login / warp), 1 = the inventory and the equipment (the
# cell as player.GetItemIndex takes it), 3 = the storehouse, 4 = the exchange (own side), 5 = the exchange (the other
# side); cell -1 = forget that window; packed 0 = the item has none.
# packed: bits 0-2 the element (1 Blyskawica 178, 2 Ogien 179, 3 Lod 180, 4 Wiatr 181, 5 Ziemia 182, 6 Mrok 183 -
# the point POINT_ENCHANT_* = 177 + element), bits 3-4 the level 0..3, level i (0..2): the Wartosc Ataku it rolled in
# bits 8+8i..11+8i, the Sila Zywiolu (%) in bits 12+8i..15+8i.
# uitooltip.py asks Setup / AppendTitle / AttackSuffix / AppendPower (the official layout: "<Zywiol> +n" under the
# name, "Wartosc Ataku: x - y (+a)", "Sila <zywiolu> +p%" after the base bonuses, in the element's colour);
# uiweaponelement.py has the windows.
import app
import item
import player
import localeInfo

_items = {}

ELEMENT_MAX = 6
GRADE_MAX = 3

# the official names (locale_game: REFINE_ELEMENT_TEXT_*), the power lines (localeinfo_point.py 178-183,
# TOOLTIP_APPLY_ENCHANT_*2) and the colours (the official REFINE_ELEMENT_COLOR_DICT)
_KEY = {1: "ELECT", 2: "FIRE", 3: "ICE", 4: "WIND", 5: "EARTH", 6: "DARK"}
NAME = {1: "B\xb3yskawica", 2: "Ogie\xf1", 3: "L\xf3d", 4: "Wiatr", 5: "Ziemia", 6: "Mrok"}
POWER = {1: "Si\xb3a B\xb3yskawic", 2: "Si\xb3a Ognia", 3: "Si\xb3a Lodu", 4: "Si\xb3a Wiatru", 5: "Si\xb3a Ziemi",
         6: "Si\xb3a Mroku"}
COLOR = {1: 4280530920L, 2: 4292692027L, 3: 4282215647L, 4: 4281847585L, 5: 4294232596L, 6: 4290195180L}
# the scrolls: vnum -> the element (0 = Zwoj Klatwy, -1 = Zwoj Zmiany)
SCROLLS = {56002: 2, 56003: 3, 56004: 1, 56005: 4, 56006: 5, 56007: 6, 56008: 0, 56009: -1}


def Text(name, fallback):
	try:
		v = getattr(localeInfo, name)
		if v:
			return v
	except:
		pass
	return fallback


def IsScroll(vnum):
	return vnum in SCROLLS


def ElementText(t, grade):
	if t not in NAME:
		return ""
	return Text("REFINE_ELEMENT_TEXT_" + _KEY[t], NAME[t] + " +%d") % grade


def PowerText(t, value):
	return POWER.get(t, "") + " +%d%%" % value


def PowerRangeText(t, lo, hi):
	return Text("TOOLTIP_APPLY_ENCHANT_%s2" % _KEY.get(t, ""), POWER.get(t, "") + " +%d%% ~ +%d%%") % (lo, hi)


def Decode(packed):
	"""(element, level, [(attack, power) of each level reached])"""
	packed = int(packed)
	t = packed & 7
	g = (packed >> 3) & 3
	levels = []
	for i in xrange(min(g, GRADE_MAX)):
		levels.append(((packed >> (8 + 8 * i)) & 15, (packed >> (12 + 8 * i)) & 15))
	return t, g, levels


def Sums(packed, grade=None):
	t, g, levels = Decode(packed)
	if grade is not None:
		levels = levels[:grade]
	return sum(a for a, p in levels), sum(p for a, p in levels)


def OnServer(window="0", cell="0", value="0", *rest):
	try:
		w, c, v = int(window), int(cell), int(value) & 0xFFFFFFFF
	except ValueError:
		return
	if w == 0:
		_items.clear()
		try:
			__import__("uiweaponelement").Reset()
		except:
			pass
		return
	if c < 0:
		for k in _items.keys():
			if k[0] == w:
				del _items[k]
		return
	if v & 7 and (v >> 3) & 3:
		_items[(w, c)] = v
	else:
		_items.pop((w, c), None)


def Get(window, cell):
	return _items.get((window, cell), 0)


_asked = [0.0]


def Sync():
	"""all WELEM lines again ("/welem_sync", at most every 2 s)"""
	try:
		import net
		now = app.GetTime()
		if _asked[0] > 0.0 and now - _asked[0] < 2.0:
			return
		_asked[0] = now
		net.SendChatPacket("/welem_sync")
	except:
		pass


# ---- the tooltip --------------------------------------------------------------------------------------------------
# tooltip.welemData = {"type", "grade", "att", "pow", "rng"} for the item drawn now (None: no element); rng =
# (attMin, attMax, powMin, powMax) in the upgrade window's preview (the official isRefineElementItem).
def _Find(tooltip, window_type, slotIndex):
	slot = getattr(tooltip, "welemSlot", None)            # the exchange (uitooltip SetExchange*Item)
	if slot:
		return _items.get(slot, 0)
	safebox = getattr(tooltip, "ysetsSafeboxSlot", -1)
	if safebox is not None and safebox >= 0:
		return _items.get((3, safebox), 0)
	if slotIndex is None or slotIndex < 0:
		return 0
	if window_type in (player.INVENTORY, getattr(player, "EQUIPMENT", -99)):
		return _items.get((1, slotIndex), 0)
	return 0


def Setup(tooltip, window_type, slotIndex):
	"""AddItemData, the item selected: what this tooltip shows of the element"""
	tooltip.welemData = None
	try:
		itemType = item.GetItemType()
		isWeapon = itemType == item.ITEM_TYPE_WEAPON
		isSash = itemType == item.ITEM_TYPE_COSTUME and item.GetItemSubType() == getattr(item, "COSTUME_TYPE_ACCE", -99)
	except:
		return
	if not isWeapon and not isSash:
		return
	preview = getattr(tooltip, "welemPreview", None)
	if preview:
		tooltip.welemData = preview
		return
	packed = _Find(tooltip, window_type, slotIndex)
	if not packed:
		return
	t, g, levels = Decode(packed)
	if t < 1 or t > ELEMENT_MAX or g < 1:
		return
	tooltip.welemData = {"type": t, "grade": g, "att": sum(a for a, p in levels), "pow": sum(p for a, p in levels),
	                     "rng": None}


def AppendTitle(tooltip):
	d = getattr(tooltip, "welemData", None)
	if not d or d["grade"] < 1:
		return
	tooltip.AppendSpace(5)
	tooltip.AppendTextLine(ElementText(d["type"], d["grade"]), COLOR[d["type"]])


def _Drain(tooltip, value, absChance):
	if not absChance:
		return value
	try:
		return max(1, int(tooltip.CalcAcceValue(value, absChance)))
	except:
		return max(1, int(value * absChance / 100))


def AttackSuffix(tooltip, absChance=0):
	"""" (+a)" after the weapon's attack value; " (+a~+b)" in the upgrade preview"""
	d = getattr(tooltip, "welemData", None)
	if not d:
		return ""
	if d["rng"]:
		return " (+%d~+%d)" % (d["att"] + d["rng"][0], d["att"] + d["rng"][1])
	if not d["att"]:
		return ""
	return " (+%d)" % _Drain(tooltip, d["att"], absChance)


def AppendPower(tooltip, absChance=0):
	d = getattr(tooltip, "welemData", None)
	if not d:
		return
	t = d["type"]
	if d["rng"]:
		tooltip.AppendTextLine(PowerRangeText(t, d["pow"] + d["rng"][2], d["pow"] + d["rng"][3]), COLOR[t])
	elif d["pow"]:
		tooltip.AppendTextLine(PowerText(t, _Drain(tooltip, d["pow"], absChance)), COLOR[t])


def Preview(mode, newType, newGrade, curPacked, rng):
	"""the upgrade window's tooltip data (mode 1: the level being added with its range; 2: the levels left)"""
	t, g, levels = Decode(curPacked)
	if mode == 1:
		if t != newType:
			levels = []
		levels = levels[:max(0, newGrade - 1)]
		return {"type": newType, "grade": newGrade, "att": sum(a for a, p in levels),
		        "pow": sum(p for a, p in levels), "rng": tuple(rng)}
	levels = levels[:max(0, newGrade)]
	if newGrade < 1:
		return {"type": t, "grade": 0, "att": 0, "pow": 0, "rng": None}
	return {"type": t, "grade": newGrade, "att": sum(a for a, p in levels), "pow": sum(p for a, p in levels),
	        "rng": None}
