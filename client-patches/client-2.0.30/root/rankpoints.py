# MT2009_PLUS_RANK_POINTS_V1 - Punkty Rangi: the extra ranks raised by eating the rank
# fruits (Jablko, Gruszka, Winogrono, Arbuz, Ananas - Arezzo's "dodatkowe rangi"; the
# server: playerbot_rank_points.h, server-patches/rankpoints).
#
# MT2009_PLUS_RANK_POINTS_V2 - ONE scale: the game's own alignment ("Punkty Rangi",
# up to 20 000) is its bottom, Arezzo's points continue it above 20 000:
#   total = alignment            while the alignment is under 20 000
#   total = 20 000 + Arezzo's    once the alignment stands at 20 000
# Jablko raises the alignment itself (0 - 20 000), the other fruits the points above it.
# The character window's alignment tooltip shows that ONE total (uicharacter.py,
# BuildAlignmentToolTip); under 20 000 it is the client's live alignment, above it the
# server's "RANGA self". A server that never sent "RANGA self": the old tooltip.
#
# From 21 000 points a character's rank stands, in the rank's own colour, where its
# alignment title stood (Arezzo's names and colours, colorinfo.py TITLE_RGB_GOOD_*):
#
#   "RANGA tail <vid> <tier>"     a character with a rank came into view (or its rank
#                                 changed); tier 0 = the alignment title again
#   "RANGA self <total> <tier>"   the player's own total (V2; V1: its separate points),
#                                 for the character window's alignment tooltip
#
# An exe with ENABLE_RANK_TITLE (client-patches/exe) keeps the rank on the character
# (chrmgr.SetRankTitle) and draws it whenever it draws the title; with an older exe the
# keeper below puts it back over the alignment title every half second
# (textTail.AttachTitle), the exe drawing the alignment title in between.
#
# CP1250 as escapes, like every name the client draws.

POINTS_MAX = 200000
ALIGN_CAP = 20000	# the alignment's cap as shown; the Arezzo points start here

# tier: (from, Polish name, English name, colour)
TIERS = {
	1: (21000, "Waleczny", "Valiant", (245, 170, 66)),
	2: (31000, "Mocarny", "Mighty", (255, 140, 0)),
	3: (41000, "Pot\xea\xbfny", "Powerful", (203, 66, 245)),
	4: (51000, "W\xb3adca", "Ruler", (245, 66, 108)),
	5: (81000, "Arcymistrz", "Grandmaster", (250, 57, 57)),
	6: (101000, "Legenda", "Legend", (57, 250, 67)),
	7: (121000, "Legenda", "Legend", (0, 230, 255)),
	8: (200000, "Legenda", "Legend", (255, 215, 0)),
}

# tier: (monsters %, people %, Metins %, bosses %, average damage %, HP) - = the server's TIERS
BONUS = {
	1: (10, 10, 0, 0, 0, 1000),
	2: (12, 12, 0, 0, 0, 1500),
	3: (15, 15, 0, 0, 0, 1900),
	4: (18, 18, 0, 0, 0, 2200),
	5: (18, 18, 10, 0, 0, 2900),
	6: (18, 18, 15, 10, 0, 3500),
	7: (18, 18, 15, 15, 0, 4000),
	8: (20, 20, 18, 18, 10, 5000),
}
BONUS_LABELS = (
	"Silny przeciwko potworom +%d%%",
	"Silny przeciwko ludziom +%d%%",
	"Silny przeciwko Metinom +%d%%",
	"Silny przeciwko bossom +%d%%",
	"\x8crednie obra\xbfenia +%d%%",
	"Maks. P\xaf +%d",
)

# (from, to, name, points a piece) - V2: four times V1's 50 / 50 / 100 / 100 / 100
FRUITS = (
	(0, 20000, "Jab\xb3ko", 200),
	(20000, 40000, "Gruszka", 200),
	(40000, 80000, "Winogrono", 400),
	(80000, 120000, "Arbuz", 400),
	(120000, 200000, "Ananas", 400),
)

TEXT_NEXT = "Nast\xeapna: %s od %d"
TEXT_FRUIT = "Teraz jedz: %s (+%d)"
TEXT_MAX = "Najwy\xbfsza ranga"
TEXT_TOTAL = "Punkty Rangi: %d"
TEXT_NEGATIVE = "Owoce rangi dzia\xb3aj\xb9 od 0 punkt\xf3w"

REFRESH_SECONDS = 0.5

_english = False
try:
	import systemSetting
	_english = systemSetting.GetLanguage() == "en"
except Exception:
	pass


def TierName(tier):
	t = TIERS.get(tier)
	if not t:
		return ""
	return t[2] if _english else t[1]


def TierOf(points):
	tier = 0
	for t, row in TIERS.items():
		if points >= row[0] and t > tier:
			tier = t
	return tier


def FruitFor(points):
	for row in FRUITS:
		if row[0] <= points < row[1]:
			return row
	return None


_registered = False


def _Register():
	global _registered
	if _registered:
		return
	_registered = True
	import chrmgr
	if not hasattr(chrmgr, "RegisterRankTitle"):
		return
	for tier, row in TIERS.items():
		(r, g, b) = row[3]
		chrmgr.RegisterRankTitle(tier, TierName(tier), r, g, b)


def HasNativeTitle():
	import chrmgr
	return hasattr(chrmgr, "SetRankTitle")


def _ToInt(value, default=None):
	try:
		return int(value)
	except (ValueError, TypeError):
		return default


def _Vid(value):
	vid = _ToInt(value)
	if vid is None or vid <= 0 or vid > 0xffffffff:
		return None
	# the text tail and chrmgr read the VID as a signed int
	if vid >= 0x80000000:
		vid -= 0x100000000
	return vid


class Keeper(object):
	"""With an exe without chrmgr.SetRankTitle: every rank heard of, put back over
	the alignment title every REFRESH_SECONDS while its character is in view."""

	def __init__(self):
		self.titles = {}
		self.nextRefresh = 0.0

	def Set(self, vid, tier):
		if tier in TIERS:
			self.titles[vid] = tier
			self.Attach(vid, tier)
		elif vid in self.titles:
			del self.titles[vid]

	def Attach(self, vid, tier):
		import textTail
		(r, g, b) = TIERS[tier][3]
		textTail.AttachTitle(vid, TierName(tier), r / 255.0, g / 255.0, b / 255.0)

	def CanUpdate(self):
		return bool(self.titles)

	def OnUpdate(self):
		import app
		now = app.GetTime()
		if now < self.nextRefresh:
			return
		self.nextRefresh = now + REFRESH_SECONDS
		import chr
		for vid, tier in list(self.titles.items()):
			if not chr.HasInstance(vid):
				del self.titles[vid]
				continue
			self.Attach(vid, tier)

	def Destroy(self):
		self.titles = {}


_keeper = None


def GetKeeper():
	global _keeper
	if _keeper is None:
		_keeper = Keeper()
	return _keeper


# The player's own points ("RANGA self"), None until the server says.
selfPoints = None
selfTier = 0


def OnCommand(*args):
	"""True when the fallback keeper holds a title (game.py registers it)."""
	global selfPoints, selfTier
	if not args:
		return False
	if args[0] == "self" and len(args) >= 3:
		points = _ToInt(args[1], 0)
		selfPoints = max(-ALIGN_CAP, min(points, POINTS_MAX))
		selfTier = _ToInt(args[2], 0)
		return False
	if args[0] == "tail" and len(args) >= 3:
		vid = _Vid(args[1])
		tier = _ToInt(args[2], 0)
		if vid is None or tier is None:
			return False
		_Register()
		if HasNativeTitle():
			import chrmgr
			chrmgr.SetRankTitle(vid, tier if tier in TIERS else 0)
			return False
		keeper = GetKeeper()
		keeper.Set(vid, tier)
		return bool(keeper.titles)
	return False


def Total(alignment):
	"""The one total of the scale from the client's live alignment (as shown) and the
	server's last "RANGA self"; None when the server never sent it."""
	if selfPoints is None:
		return None
	if alignment < ALIGN_CAP:
		return alignment
	return max(ALIGN_CAP, selfPoints)


def BuildAlignmentToolTip(toolTip, alignment, gradeTitle, gradeColor, pointsLabel=None):
	"""The whole alignment tooltip on the one scale: the rank (or the alignment's title
	under the first rank), ONE "Punkty Rangi: <total>", the rank's bonus, the next rank
	and the fruit wanted now. False (nothing written) when the server never sent
	"RANGA self" - the caller writes the old tooltip."""
	total = Total(alignment)
	if total is None:
		return False
	import ui
	tier = TierOf(total)
	if tier:
		(r, g, b) = TIERS[tier][3]
		toolTip.AutoAppendTextLine(TierName(tier), ui.GenerateColor(r, g, b))
	else:
		toolTip.AutoAppendTextLine(gradeTitle, gradeColor)
	if pointsLabel:
		toolTip.AutoAppendTextLine(pointsLabel + str(total))
	else:
		toolTip.AutoAppendTextLine(TEXT_TOTAL % total)
	if tier:
		color = getattr(toolTip, "POSITIVE_COLOR", 0xff6cff6c)
		for i, value in enumerate(BONUS[tier]):
			if value > 0:
				toolTip.AutoAppendTextLine(BONUS_LABELS[i] % value, color)
	fruit = FruitFor(total)
	if tier + 1 in TIERS and total >= 0:
		toolTip.AutoAppendTextLine(TEXT_NEXT % (TierName(tier + 1), TIERS[tier + 1][0]))
	if fruit:
		toolTip.AutoAppendTextLine(TEXT_FRUIT % (fruit[2], fruit[3]))
	elif total < 0:
		toolTip.AutoAppendTextLine(TEXT_NEGATIVE)
	else:
		toolTip.AutoAppendTextLine(TEXT_MAX)
	return True
