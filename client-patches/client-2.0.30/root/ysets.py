# MT2009_PLUS_YOHARA_SETS_V1: the client's side of the Yohara gear and the set effects (server-patches/ysets).
# The server tells every item's "yextra" by "YITEM <window> <cell> <yextra>" (game.py -> OnServer): window 1 = the
# inventory and the equipment (the cell as player.GetItemIndex takes it), 3 = the storehouse, 0 = forget everything
# (a new login / warp). yextra: bits 0-3 the set (ysets_data.SETS), bits 8-31 the three random base bonuses of a
# serpent piece (a byte each: the bonus of its line 1-15 | the wiki's value row << 4; ysets_data.RANDOM_GROUPS).
# uitooltip.py asks GetFor / Title / AppendInfo.
import player
import item
import localeInfo
import ysets_data as D

_items = {}

SET_COLOR = 0xffd8b26b           # the set's lines
ACTIVE_COLOR = 0xff89b88d        # a bonus the worn pieces give now
INACTIVE_COLOR = 0xff8a8a8a      # a bonus that needs more pieces
RANDOM_COLOR = 0xffd0c38f        # a serpent piece's random base bonuses

POINT_TEXT = {6: "Max. P\xaf +%d", 19: "Szybko\x9c\xe6 ruchu +%d%%", 53: "Silny przeciwko potworom +%d%%",
              116: "Punkty do\x9cwiadczenia +%d%%", 132: "Magia / walka wr\xeacz +%d%%"}


def OnServer(window="0", cell="0", value="0", *rest):
	try:
		w, c, v = int(window), int(cell), int(value)
	except ValueError:
		return
	if w == 0:
		_items.clear()
		return
	if v:
		_items[(w, c)] = v
	else:
		_items.pop((w, c), None)


def GetFor(window_type, slotIndex, safeboxSlot=-1):
	if safeboxSlot is not None and safeboxSlot >= 0:
		return _items.get((3, safeboxSlot), 0)
	if slotIndex is None or slotIndex < 0:
		return 0
	if window_type in (player.INVENTORY, getattr(player, "EQUIPMENT", -99)):
		return _items.get((1, slotIndex), 0)
	return 0


def Title(name, extra):
	s = extra & 0x0F
	if s in D.SETS:
		return D.SETS[s][0] + " " + name
	return name


def _Family(itemVnum):
	for base, kind in D.RANDOM_FAMILIES.items():
		if base <= itemVnum < base + 16:
			return kind, itemVnum - base
	return None, 0


def _ApplyText(point, value):
	try:
		s = localeInfo.GetApplyString(point, value)
	except:
		s = ""
	if not s and point in POINT_TEXT:
		s = POINT_TEXT[point] % value
	if s and value < 0:
		s = s.replace("+", "")
	return s


def _WornSet():
	"""(set, pieces) of the weapon, the armour and the helmet worn now (two or three of one set)"""
	count = {}
	for slot in (getattr(item, "EQUIPMENT_WEAPON", -1), getattr(item, "EQUIPMENT_BODY", -1), getattr(item, "EQUIPMENT_HEAD", -1)):
		if slot < 0 or not player.GetItemIndex(slot):
			continue
		s = _items.get((1, slot), 0) & 0x0F
		if s:
			count[s] = count.get(s, 0) + 1
	best, pieces = 0, 0
	for s, n in count.items():
		if n >= 2 and n > pieces:
			best, pieces = s, n
	return best, pieces


def AppendInfo(tooltip, itemVnum, extra):
	"""the random base bonuses of a serpent piece and the set effect of any piece"""
	kind, level = _Family(itemVnum)
	if kind:
		groups = D.RANDOM_GROUPS[kind]
		if extra >> 8:
			tooltip.AppendSpace(5)
			for line in xrange(3):
				b = (extra >> (8 + 8 * line)) & 0xFF
				opt, row = (b & 0x0F) - 1, b >> 4
				if opt < 0 or opt >= len(groups[line]):
					continue
				point, rows = groups[line][opt]
				if row >= len(rows):
					continue
				text = _ApplyText(point, rows[row][level])
				if text:
					tooltip.AppendTextLine(text, RANDOM_COLOR)
		else:
			tooltip.AppendTextLine("3 losowe bonusy podstawowe", INACTIVE_COLOR)
	s = extra & 0x0F
	if s not in D.SETS:
		return
	prefix, name, tiers = D.SETS[s]
	worn, pieces = _WornSet()
	tooltip.AppendSpace(5)
	tooltip.AppendTextLine(name, SET_COLOR)
	for n in sorted(tiers.keys()):
		active = worn == s and pieces == n      # the server gives the tier of the worn count only
		color = active and ACTIVE_COLOR or INACTIVE_COLOR
		parts = [t for t in (_ApplyText(p, v) for p, v in tiers[n]) if t]
		tooltip.AppendTextLine("%d cz\xea\x9cci: %s" % (n, ", ".join(parts)), color)
