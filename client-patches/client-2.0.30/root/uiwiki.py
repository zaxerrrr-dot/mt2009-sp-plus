# MT2009_PLUS_WIKI_V1 - the in-game wiki ("Encyklopedia"), the owner's Valiant2 wiki package rebuilt for our client
# (the owner, 10 November 2026: "Chce aby bylo tam doslownie wszystko co jest na serwerze, kazdy przedmiot, kazdy
# ulepszacz, z czego dropi, z jaka szansa, jak sie ulepsza dane przedmioty, jakie wartosci maja dane przedmioty (po
# najechaniu na dany + przedmiotu w wiki). Jakie sa craftingi, gdzie sa te craftingi ... wykorzystaj ten kod").
#
# Valiant2's look: its pictures (d:/ymir work/ui/game/wiki/, pack "wikiv2": the board's background, the category
# banners - in Polish now, tools/wikiv2/make_wiki_images.py -, the category list's bars, the search slot, the class
# buttons, the refine table's slots, the monster card) and its layout (750x537: banner, search, categories on the left,
# the result page on the right, the class buttons over the equipment). Its code drew everything through its own clip
# hacks (SetRenderingRect per picture) and hard-coded lists in the exe; here the result page is a clipped scroll view
# (wndMgr.SetClippingMaskWindow - our exe clips text, pictures and the render target) filled a few blocks a frame, and
# every list comes from module wikipedia (the exe's Mt2009Wiki.cpp), which reads the files OUR server data generates
# (tools/wikiv2/gen_wiki_data.py). The package's README bugs are gone with its code: RunHistoryArgument (a real
# history now - "Wstecz"), constInfo.NumberToString, the sura/shaman flag swap, the +9 name test.
#
# What it shows:
#   - every item: its tooltip (mouse over), where it drops (monsters with the chance per kill and the count, chests with
#     the chance per opening), recipes (NPC, where it stands, materials, Yang, chance), NPC shops, quest / other notes,
#     the refine step that makes it, what it is for (recipes, refine steps it is a material of), a chest's content;
#   - equipment by class and kind: the refine table +0..+N - per step the materials, Yang and the chance; the mouse
#     over "+X" shows the item at +X (its values and bonuses), over a material its tooltip;
#   - costumes, hair, sashes, auras, mounts, pets (3D preview on the player's race / the mount's model);
#   - Metin stones, bosses, monsters by level / map: 3D model, stats, places, drop table;
#   - crafting: every recipe NPC, where it stands, its recipes.
# Opened by: the key "wiki" (keybind.py, "/" - the old drop wiki's key; H is the help), the inventory side bar's
# "Encyklopedia", the target board's (i) (that monster), Shift+H over an item's tooltip (that item).
# Chances: per kill, for a killer at the monster's level, without premium, gloves or events (the server's own
# arithmetic, gen_wiki_data.py's header).
#
# Python 2.7 as the client has it; the texts are CP1250 escapes (made from this file's UTF-8 source by
# tools/wikiv2/escape_cp1250.py).

import app
import chr
import grp
import item
import nonplayer
import player
import ui
import uiToolTip
import wndMgr
from _weakref import proxy

try:
	import wikipedia
except ImportError:
	wikipedia = None
try:
	import renderTarget
except ImportError:
	renderTarget = None
try:
	import dropwikiportraits
except Exception:
	dropwikiportraits = None

IMG = "d:/ymir work/ui/game/wiki/"
BOARD_W = 750
BOARD_H = 537
VIEW_X = 190
VIEW_Y = 144
VIEW_Y_JOBS = 190
VIEW_W = 551
VIEW_BOTTOM = 517
SCROLL_W = 9
ROW_W = 541
ROW_H = 36
BUILD_BUDGET = 0.012	# seconds of block building a frame
MAX_ITEM_ROWS = 120		# rows of one list on an item's page (the rest: a "more" line)

COLOR_GOLD = 0xffffb96d
COLOR_HEADER = 0xffc8aa80
COLOR_WHITE = 0xfff0f0f0
COLOR_DIM = 0xffa0a0a0
COLOR_SUB = 0xffb4a68c
COLOR_GREEN = 0xff8ec292
COLOR_RED = 0xffe57975
ROW_SHADE = 0x90000000
ROW_LINE = 0xff4a3e30
ROW_HOVER = 0x24ffffff
COLOR_CHANCES = ((10.0, 0xffffffff), (1.0, 0xff9be36b), (0.1, 0xff6bb6ff), (0.0, 0xffffb050))

TEXT_TITLE = "Encyklopedia"
TEXT_BACK = "Wstecz"
TEXT_HOME = "Start"
TEXT_SEARCH_ITEM = "Szukaj przedmiotu..."
TEXT_SEARCH_MOB = "Szukaj potwora..."
TEXT_SEARCH_TIP_ITEM = "Szukasz przedmiotu - kliknij, by szuka\xe6 potwora"
TEXT_SEARCH_TIP_MOB = "Szukasz potwora - kliknij, by szuka\xe6 przedmiotu"
TEXT_SEARCH_BUTTON = "Szukaj (Enter)"
TEXT_NOTHING = "Nic nie znaleziono."
TEXT_NO_DATA = "Brak danych encyklopedii - zaktualizuj klienta."
TEXT_LOADING = "Wczytuj\xea..."
TEXT_MORE = "... i %d wi\xeacej"
TEXT_UNKNOWN_ITEM = "Przedmiot %d"

TEXT_CAT_EQUIP = "Ekwipunek"
TEXT_CAT_COSTUME = "Kostiumy"
TEXT_CAT_MOUNT = "Wierzchowce i zwierzaki"
TEXT_CAT_CHEST = "Skrzynie"
TEXT_CAT_METIN = "Kamienie Metin"
TEXT_CAT_BOSS = "Bossowie"
TEXT_CAT_MOB = "Potwory"
TEXT_CAT_CRAFT = "Wytwarzanie"

EQUIP_NAMES = ("Bro\xf1", "Zbroje", "He\xb3my", "Tarcze", "Kolczyki", "Bransolety", "Naszyjniki", "Buty", "Pasy", "Talizmany",
	"R\xeakawice", "Pozosta\xb3e")
COSTUME_MENU = ((0, "Kostiumy broni", "weapon_skins"), (1, "Kostiumy", "body_costumes"), (2, "Fryzury", "hair_styles"),
	(3, "Szarfy", "acce_system"), (4, "Kostiumy szarf", "acce_costumes"), (7, "Aury", "aura"), (8, "Pozosta\xb3e", "body_costumes"))
MOUNT_MENU = ((5, "Wierzchowce", "mounts"), (6, "Zwierzaki", "pets"))
# the class buttons: (name, picture of character4/, wikipedia job mask bit)
JOBS = (("Wojownik", 0, 1), ("Ninja", 1, 2), ("Sura", 3, 4), ("Szaman", 2, 8))
JOB_X = (198, 330, 462, 594)

RANK_NAMES = ("Zwyk\xb3y", "Silny", "Elita", "Silna elita", "Boss", "Kr\xf3l")
RESIST_NAMES = ("Miecz", "Bro\xf1 dwur\xeaczna", "Sztylet", "Dzwon", "Wachlarz", "\xa3uk", "Ogie\xf1", "B\xb3yskawica", "Magia",
	"Wiatr", "Trucizna")
ELEMENT_NAMES = ("B\xb3yskawica", "Ogie\xf1", "L\xf3d", "Wiatr", "Ziemia", "Mrok")
PLACE_KINDS = ("Mapa", "Loch", "Boss lochu")
TEXT_LEVEL = "Poziom %d"
TEXT_LEVELS = "Poziom %d - %d"
TEXT_REFINE_HEAD = "Ulepszanie (+0 - +%d)"
TEXT_YANG_LABEL = "Yang"
TEXT_CHANCE_LABEL = "Szansa"
TEXT_STEP = "+%d  >  +%d"
TEXT_STEP_CHANCE = "Szansa: %d%%"
TEXT_STEP_COST = "Koszt: %s Yang"
TEXT_STEP_MATS = "Materia\xb3y:"
TEXT_LAST_STEP = "Najwy\xbfszy poziom"

SEC_CONTENT = "Zawarto\x9c\xe6 (szansa przy jednym otwarciu)"
SEC_MOBS = "Wypada z potwor\xf3w (szansa za zab\xf3jstwo)"
SEC_CHESTS = "Ze skrzy\xf1 (szansa przy jednym otwarciu)"
SEC_RECIPES = "Wytwarzanie"
SEC_SHOPS = "Sklepy NPC"
SEC_REFINE_FROM = "Ulepszenie"
SEC_NOTES = "Inne \x9fr\xf3d\xb3a"
SEC_USES = "Zastosowanie: receptury"
SEC_REFINE_USES = "Zastosowanie: materia\xb3 do ulepszania"
SEC_DROPS = "Drop (szansa za zab\xf3jstwo)"
SEC_PLACES = "Wyst\xeapowanie"
SEC_STATS = "Statystyki"
SEC_RECIPES_OF = "Receptury"
TEXT_RECIPE = "Receptura"
TEXT_EXCHANGE = "Wymiana"
TEXT_AT = "u: %s"
TEXT_WHERE = "%s (%d, %d)"
TEXT_NO_PLACE = "miejsce nieznane"
TEXT_YANG = "%s Yang"
TEXT_PRICE = "Cena: %s Yang"
TEXT_COUNT = "Ilo\x9c\xe6"
TEXT_CHANCE = "Szansa"
TEXT_ANY_OF = "dowolny z %d"
TEXT_FROM_STEP = "Ulepszenie z: %s"
TEXT_STEP_TO = "Ulepsza: %s"
TEXT_STEP_TO_SUB = "%d szt.  \xb7  szansa %d%%  \xb7  %s Yang"
TEXT_FROM_MOB = "z: %s"
TEXT_HP = "HP: %s"
TEXT_EXP = "Do\x9cwiadczenie: %s"
TEXT_DMG = "Atak: %s - %s"
TEXT_DEF = "Obrona: %s"
TEXT_GOLD = "Yang: %s - %s"
TEXT_ELEMENT = "\xafywio\xb3: %s"
TEXT_RESIST = "Odporno\x9cci: %s"
TEXT_LEVEL_RANK = "Poziom %d  \xb7  %s"
TEXT_STONE = "Kamie\xf1 Metin"
TEXT_CLICK_MOTION = "Kliknij model: kolejny ruch"
TEXT_WEARS = "Podgl\xb9d: %s"
TEXT_NPC_HEAD = "%s - receptury: %d"
TEXT_HOME_LINES = (
	"Witaj w encyklopedii!",
	"",
	"Tu znajdziesz ka\xbfdy przedmiot, potwora, skrzyni\xea i receptur\xea z naszego serwera.",
	"Dane pochodz\xb9 wprost z tabel serwera, wi\xeac szanse s\xb9 takie, jak liczy serwer.",
	"",
	"- Klawisz / (zmienisz go w Skr\xf3tach klawiszowych) i przycisk przy ekwipunku otwieraj\xb9 encyklopedi\xea.",
	"- Wybierz kategori\xea po lewej albo wpisz nazw\xea w polu wyszukiwania.",
	"- Strza\xb3ki obok pola prze\xb3\xb9czaj\xb9 szukanie przedmiot\xf3w i potwor\xf3w.",
	"- Najed\x9f na przedmiot, by zobaczy\xe6 jego opis; kliknij, by otworzy\xe6 jego stron\xea.",
	"- W tabeli ulepszania najed\x9f na +X, by zobaczy\xe6 warto\x9cci przedmiotu na tym poziomie.",
	"- Shift+H nad opisem przedmiotu otwiera go w encyklopedii.",
	"- Przycisk (i) przy celu otwiera stron\xea potwora.",
	"",
	"Szansa dropu: za jedno zab\xf3jstwo, dla gracza na poziomie potwora,",
	"bez premium, r\xeakawic z\xb3odzieja i wydarze\xf1 (te j\xb9 zwi\xeakszaj\xb9).",
)

_window = [None]


# ----------------------------------------------------------------------------------------------------------- helpers

_known = {}


def Known(vnum):
	"""the client's item_proto has the item (the server's tables may name one the client lacks; item.SelectItem of
	such a vnum leaves the next call an error)"""
	if not vnum:
		return False
	known = _known.get(vnum)
	if known is None:
		result = Call("ItemExists", vnum)
		known = bool(result) if result is not None else True
		_known[vnum] = known
	return known


def ItemName(vnum):
	if not Known(vnum):
		return TEXT_UNKNOWN_ITEM % vnum
	try:
		item.SelectItem(vnum)
		return item.GetItemName() or str(vnum)
	except Exception:
		return str(vnum)


def ItemIcon(vnum):
	if not Known(vnum):
		return IMG + "slot/empty_slot.tga"
	try:
		item.SelectItem(vnum)
		path = item.GetIconImageFileName()
		if path and path.lower().find("gr2") == -1:
			return path
	except Exception:
		pass
	return IMG + "slot/empty_slot.tga"


def MobName(vnum):
	try:
		name = nonplayer.GetMonsterName(vnum)
		if name:
			return name
	except Exception:
		pass
	return str(vnum)


def MobIcon(vnum):
	if not dropwikiportraits:
		return ""
	try:
		return dropwikiportraits.Icon(vnum) or ""
	except Exception:
		return ""


def MapName(mapIndex):
	name = ""
	if wikipedia:
		try:
			name = wikipedia.GetMapName(mapIndex)
		except Exception:
			name = ""
	return name or ("Mapa %d" % mapIndex)


def SplitPlus(name):
	pos = name.rfind("+")
	if pos > 0 and name[pos + 1:].isdigit():
		return name[:pos].rstrip(), int(name[pos + 1:])
	return name, -1


def FormatYang(value):
	text = str(abs(long(value)))
	parts = []
	while len(text) > 3:
		parts.insert(0, text[-3:])
		text = text[:-3]
	parts.insert(0, text)
	return ("-" if value < 0 else "") + ".".join(parts)


def ShortYang(value):
	value = long(value)
	if value >= 1000000000 and value % 10000000 == 0:
		return ("%.2f" % (value / 1000000000.0)).rstrip("0").rstrip(".") + "kkk"
	if value >= 1000000 and value % 10000 == 0:
		return ("%.2f" % (value / 1000000.0)).rstrip("0").rstrip(".") + "kk"
	if value >= 1000 and value % 100 == 0:
		return ("%.1f" % (value / 1000.0)).rstrip("0").rstrip(".") + "k"
	return str(value)


def FormatChance(value):
	pct = value / 1000000.0
	if pct >= 100.0:
		return "100%"
	if pct >= 1.0:
		text = "%.2f" % pct
	else:
		digits = 2
		limit = 0.1
		while pct < limit and digits < 7:
			digits += 1
			limit /= 10.0
		text = "%.*f" % (digits, pct)
	if "." in text:
		text = text.rstrip("0").rstrip(".")
	return text + "%"


def ChanceColor(value):
	pct = value / 1000000.0
	for limit, color in COLOR_CHANCES:
		if pct >= limit:
			return color
	return COLOR_CHANCES[-1][1]


def FormatCount(countMin, countMax):
	if countMin == countMax:
		return "%dx" % countMin
	return "%d-%dx" % (countMin, countMax)


def FitText(textLine, text, width):
	textLine.SetText(text)
	try:
		if textLine.GetTextSize()[0] <= width:
			return
		low, high = 0, len(text)
		while low < high:
			middle = (low + high + 1) // 2
			textLine.SetText(text[:middle].rstrip() + "...")
			if textLine.GetTextSize()[0] <= width:
				low = middle
			else:
				high = middle - 1
		textLine.SetText(text[:low].rstrip() + "...")
	except Exception:
		if len(text) > 60:
			textLine.SetText(text[:57] + "...")


def WrapText(text, chars):
	words = text.split(" ")
	lines = []
	line = ""
	for word in words:
		if line and len(line) + 1 + len(word) > chars:
			lines.append(line)
			line = word
		else:
			line = (line + " " + word) if line else word
	if line:
		lines.append(line)
	return lines


def ItemDescription(vnum):
	if not Known(vnum):
		return ""
	try:
		item.SelectItem(vnum)
		text = item.GetItemDescription() or ""
	except Exception:
		return ""
	for code in ("[ENTER]", "\r", "\n", "\t"):
		text = text.replace(code, " ")
	out = []
	i = 0
	while i < len(text):
		if text[i] == "|" and i + 1 < len(text):
			if text[i + 1] in "cC":
				i += 10
				continue
			if text[i + 1] in "rRhH":
				i += 2
				continue
		out.append(text[i])
		i += 1
	return " ".join("".join(out).split())


def ItemLevel(vnum):
	if not Known(vnum):
		return 0
	try:
		item.SelectItem(vnum)
		for i in xrange(item.LIMIT_MAX_NUM):
			(limitType, limitValue) = item.GetLimit(i)
			if limitType == item.LIMIT_LEVEL:
				return limitValue
	except Exception:
		pass
	return 0


def _Proxy(obj):
	"""a weak proxy (a proxy given stays as it is): the blocks and rows point back at their view, and ui.Window has a
	__del__ - a strong cycle through them would never be collected"""
	try:
		return proxy(obj)
	except TypeError:
		return obj


def Call(name, *args):
	if not wikipedia:
		return None
	try:
		return getattr(wikipedia, name)(*args)
	except Exception:
		return None


def MaterialText(mat):
	vnum, count, last = mat
	if last > vnum:
		return "%dx %s (%s)" % (count, ItemName(vnum), TEXT_ANY_OF % (last - vnum + 1))
	return "%dx %s" % (count, ItemName(vnum))


def NpcPlaces(npc):
	places = Call("GetNpcLocations", npc) or []
	texts = []
	for mapIndex, x, y in places[:3]:
		texts.append(TEXT_WHERE % (MapName(mapIndex), x, y))
	return ", ".join(texts) if texts else TEXT_NO_PLACE


def PlayerJobIndex():
	try:
		job = chr.RaceToJob(player.GetRace())
	except Exception:
		return 0
	# JOBS order: warrior, ninja, sura, shaman = the client's jobs 0..3
	return job if 0 <= job < 4 else 0


# ----------------------------------------------------------------------------------------------------------- widgets

class _RenderTarget(ui.Window):
	def RegisterWindow(self, layer):
		self.hWnd = wndMgr.RegisterRenderTarget(self, layer)

	def SetRenderTarget(self, index):
		wndMgr.SetRenderTarget(self.hWnd, index)


def MakeText(parent, x, y, text="", color=None, center=False, outline=False):
	t = ui.TextLine()
	t.SetParent(parent)
	t.SetPosition(x, y)
	if center:
		t.SetHorizontalAlignCenter()
	if outline:
		t.SetOutline()
	if color is not None:
		t.SetPackedFontColor(color)
	t.SetText(text)
	t.AddFlag("not_pick")
	t.Show()
	return t


def MakeBar(parent, x, y, w, h, color, pick=False):
	b = ui.Bar()
	b.SetParent(parent)
	b.SetPosition(x, y)
	b.SetSize(w, h)
	b.SetColor(color)
	if not pick:
		b.AddFlag("not_pick")
	b.Show()
	return b


def MakeLine(parent, x, y, w, color=ROW_LINE):
	l = ui.Line()
	l.SetParent(parent)
	l.SetPosition(x, y)
	l.SetSize(w, 0)
	l.SetColor(color)
	l.AddFlag("not_pick")
	l.Show()
	return l


def MakeImage(parent, x, y, path, pick=False):
	i = ui.ExpandedImageBox()
	i.SetParent(parent)
	i.SetPosition(x, y)
	try:
		i.LoadImage(path)
	except Exception:
		pass
	if not pick:
		i.AddFlag("not_pick")
	i.Show()
	return i


class HotSpot(ui.Window):
	"""a mouse area: over -> owner.ShowTip(tip), out -> owner.HideTip(), click -> owner.Go(target)"""

	def __init__(self, view, tip=None, target=None, hover=None):
		ui.Window.__init__(self)
		self.view = _Proxy(view)
		self.tip = tip
		self.target = target
		self.hover = hover

	def __del__(self):
		ui.Window.__del__(self)

	def OnMouseOverIn(self):
		if not self.view.IsMouseIn():
			return
		if self.hover:
			self.hover.Show()
		if self.tip:
			self.view.wiki.ShowTip(self.tip)

	def OnMouseOverOut(self):
		if self.hover:
			self.hover.Hide()
		self.view.wiki.HideTip()

	def OnMouseLeftButtonUp(self):
		if self.target and self.view.IsMouseIn():
			self.view.wiki.HideTip()
			self.view.wiki.Go(self.target)


def AddIcon(view, parent, x, y, vnum, size=32, click=True, count=None):
	"""an item's icon at (x, y), size x size at most (a 32x64/96 icon shrinks), its tooltip and its page on a click"""
	icon = MakeImage(parent, x, y, ItemIcon(vnum))
	w = max(1, icon.GetWidth())
	h = max(1, icon.GetHeight())
	scale = min(1.0, float(size) / h, float(size) / w)
	if scale < 1.0:
		icon.SetScale(scale, scale)
	icon.SetPosition(x + int((size - w * scale) // 2), y + int((size - h * scale) // 2))
	spot = HotSpot(view, ("i", vnum), ("i", vnum) if click else None)
	spot.SetParent(parent)
	spot.SetPosition(x, y)
	spot.SetSize(size, size)
	spot.Show()
	spot.icon = icon	# the spot keeps its picture and count (a window nobody holds is gone)
	spot.countText = None
	if count is not None and count != 1:
		t = MakeText(parent, x + size - 1, y + size - 13, str(count), COLOR_WHITE, False, True)
		t.SetHorizontalAlignRight()
		spot.countText = t
	return spot


class Block(ui.Window):
	"""one piece of a result page (a row, a header, a table); kept by the page, built once"""

	def __init__(self, view, height):
		ui.Window.__init__(self)
		self.view = _Proxy(view)
		self.keep = []
		self.SetSize(ROW_W, height)

	def __del__(self):
		ui.Window.__del__(self)

	def K(self, widget):
		self.keep.append(widget)
		return widget

	def Destroy(self):
		self.keep = []

	def OnMouseWheel(self, delta):
		return self.view.OnMouseWheel(delta)


class HeaderBlock(Block):
	def __init__(self, view, text, sub=""):
		Block.__init__(self, view, 26)
		self.K(MakeBar(self, 0, 4, ROW_W, 20, 0x60201810))
		self.K(MakeLine(self, 0, 24, ROW_W, 0xff8a6a44))
		self.K(MakeText(self, 6, 7, text, COLOR_GOLD, False, True))
		if sub:
			t = self.K(MakeText(self, ROW_W - 6, 7, sub, COLOR_DIM))
			t.SetHorizontalAlignRight()


class TextBlock(Block):
	def __init__(self, view, lines, color=COLOR_WHITE):
		Block.__init__(self, view, 6 + 16 * len(lines))
		for n, line in enumerate(lines):
			self.K(MakeText(self, 8, 3 + 16 * n, line, color))


class RowBlock(Block):
	"""an icon ('i'|'m', vnum), a title, a second line, a count and a chance (hundred-millionths) / a right text"""

	def __init__(self, view, icon, title, sub="", count="", chance=None, right="", target=None, tip=None, height=ROW_H):
		Block.__init__(self, view, height)
		self.K(MakeBar(self, 0, 1, ROW_W, height - 2, ROW_SHADE))
		self.K(MakeLine(self, 0, 0, ROW_W))
		hover = self.K(MakeBar(self, 0, 1, ROW_W, height - 2, ROW_HOVER))
		hover.Hide()
		spot = self.K(HotSpot(view, tip, target, hover))
		spot.SetParent(self)
		spot.SetPosition(0, 0)
		spot.SetSize(ROW_W, height)
		spot.Show()
		x = 6
		if icon:
			kind, vnum = icon
			path = ItemIcon(vnum) if kind == "i" else MobIcon(vnum)
			if path:
				img = self.K(MakeImage(self, 0, 0, path))
				w = max(1, img.GetWidth())
				h = max(1, img.GetHeight())
				scale = min(1.0, 32.0 / h, 32.0 / w)
				if scale < 1.0:
					img.SetScale(scale, scale)
				img.SetPosition(4 + int((32 - w * scale) // 2), int((height - h * scale) // 2))
			x = 42
		textY = (height - 14) // 2
		if sub:
			textY = 3
			s = self.K(MakeText(self, x, 19, "", COLOR_SUB))
			FitText(s, sub, ROW_W - x - 150 if (count or chance is not None or right) else ROW_W - x - 8)
		t = self.K(MakeText(self, x, textY, "", COLOR_WHITE))
		FitText(t, title, ROW_W - x - 160 if (count or chance is not None or right) else ROW_W - x - 8)
		if count:
			self.K(MakeText(self, ROW_W - 120, textY, count, COLOR_WHITE, True))
		if chance is not None:
			c = self.K(MakeText(self, ROW_W - 45, textY, FormatChance(chance), ChanceColor(chance), True))
		if right:
			r = self.K(MakeText(self, ROW_W - 8, textY, right, COLOR_GOLD))
			r.SetHorizontalAlignRight()


class ColumnsBlock(Block):
	"""the column heads of a row list"""

	def __init__(self, view, first, count=True, chance=True):
		Block.__init__(self, view, 18)
		self.K(MakeText(self, 42, 2, first, COLOR_DIM))
		if count:
			self.K(MakeText(self, ROW_W - 120, 2, TEXT_COUNT, COLOR_DIM, True))
		if chance:
			self.K(MakeText(self, ROW_W - 45, 2, TEXT_CHANCE, COLOR_DIM, True))


class RefineBlock(Block):
	"""Valiant2's refine table: the item's +0 and +max, then a column a level: "+X" (the item at +X under the mouse),
	the materials of the step +X -> +X+1, its Yang and its chance"""
	COLS = 10
	COL_W = 41
	COL_X = 130

	def __init__(self, view, chain):
		self.chain = list(chain)
		self.steps = []
		mats = 2
		for vnum in self.chain[:-1]:
			step = Call("GetRefineStep", vnum)
			self.steps.append(step)
			if step:
				mats = max(mats, len(step[3]))
		self.steps.append(None)
		self.mats = min(5, mats)
		self.bgHeight = {2: 156, 3: 200, 4: 248, 5: 296}[self.mats]
		Block.__init__(self, view, self.bgHeight + 22)
		self.offset = 0
		self.colWidgets = []
		bg = self.K(MakeImage(self, 0, 0, IMG + "slot/slot_%d.tga" % self.mats))
		base = self.chain[0]
		top = self.chain[-1]
		name = SplitPlus(ItemName(base))[0]
		self.K(MakeText(self, 6, 4, name, COLOR_GOLD, False, True))
		low, high = ItemLevel(base), ItemLevel(top)
		levelText = (TEXT_LEVELS % (low, high)) if high and high != low else (TEXT_LEVEL % low if low else "")
		lvl = self.K(MakeText(self, 400, 4, levelText, COLOR_DIM))
		lvl.SetHorizontalAlignRight()
		if len(self.chain) > 1:
			self.K(MakeText(self, 520, 4, TEXT_REFINE_HEAD % (len(self.chain) - 1), COLOR_SUB)).SetHorizontalAlignRight()
		iconY = {2: 55, 3: 70, 4: 80, 5: 115}[self.mats]
		self.K(AddIcon(view, self, 8, iconY, base, 32))
		if top != base:
			self.K(AddIcon(view, self, 76, iconY, top, 32))
			self.K(MakeText(self, 58, iconY + 10, ">", COLOR_DIM, True))
		# Valiant2's places in its slot pictures: "+X" at 25, the materials at 45 + 47 a row, the Yang row at these
		self.priceY = (140, 140, 140, 180, 230, 275)[self.mats] - 1
		self.K(MakeText(self, 66, self.priceY, TEXT_YANG_LABEL, COLOR_DIM, True))
		# the chance row under the slot
		self.K(MakeBar(self, 0, self.bgHeight, 541, 20, 0xc0100c08))
		self.K(MakeLine(self, 0, self.bgHeight + 20, 541, 0xff3a3026))
		self.K(MakeText(self, 66, self.bgHeight + 3, TEXT_CHANCE_LABEL, COLOR_DIM, True))
		if len(self.chain) > self.COLS:
			left = ui.Button()
			left.SetParent(self)
			left.SetUpVisual(IMG + "left.tga")
			left.SetOverVisual(IMG + "left.tga")
			left.SetDownVisual(IMG + "left.tga")
			left.SetPosition(self.COL_X - 26, 27)
			left.SetEvent(ui.__mem_func__(self.Page), -1)
			left.Show()
			self.K(left)
			right = ui.Button()
			right.SetParent(self)
			right.SetUpVisual(IMG + "right.tga")
			right.SetOverVisual(IMG + "right.tga")
			right.SetDownVisual(IMG + "right.tga")
			right.SetPosition(self.COL_X - 14, 27)
			right.SetEvent(ui.__mem_func__(self.Page), 1)
			right.Show()
			self.K(right)
		self.BuildColumns()

	def Page(self, delta):
		maxOffset = max(0, len(self.chain) - self.COLS)
		offset = max(0, min(maxOffset, self.offset + delta * (self.COLS - 2)))
		if offset != self.offset:
			self.offset = offset
			self.BuildColumns()
			self.view.ClipBlock(self)

	def BuildColumns(self):
		for w in self.colWidgets:
			w.Hide()
		self.colWidgets = []
		view = self.view
		for col in xrange(self.COLS):
			level = self.offset + col
			if level >= len(self.chain):
				break
			x = self.COL_X + col * self.COL_W
			vnum = self.chain[level]
			step = self.steps[level]
			plus = SplitPlus(ItemName(vnum))[1]
			label = "+%d" % (plus if plus >= 0 else level)
			hover = MakeBar(self, x + 1, 21, self.COL_W - 1, 19, ROW_HOVER)
			hover.Hide()
			self.colWidgets.append(hover)
			self.colWidgets.append(MakeText(self, x + 21, 24, label, COLOR_GOLD, True))
			spot = HotSpot(view, ("i", vnum), ("i", vnum), hover)
			spot.SetParent(self)
			spot.SetPosition(x, 20)
			spot.SetSize(self.COL_W, 20)
			spot.Show()
			self.colWidgets.append(spot)
			if not step:
				self.colWidgets.append(MakeText(self, x + 21, self.priceY, "-", COLOR_DIM, True))
				continue
			to, cost, prob, mats = step
			for n, mat in enumerate(mats[:self.mats]):
				mvnum, mcount, mlast = mat
				self.colWidgets.append(AddIcon(view, self, x + 4, 45 + n * 47, mvnum, 32, True, mcount))
			self.colWidgets.append(MakeText(self, x + 21, self.priceY, ShortYang(cost) if cost else "0", COLOR_WHITE, True))
			self.colWidgets.append(MakeText(self, x + 21, self.bgHeight + 3, "%d%%" % prob,
				COLOR_GREEN if prob >= 70 else (COLOR_GOLD if prob >= 40 else COLOR_RED), True))
			tip = [TEXT_STEP % (level, level + 1), TEXT_STEP_CHANCE % prob, TEXT_STEP_COST % FormatYang(cost)]
			if mats:
				tip.append(TEXT_STEP_MATS)
				tip.extend(MaterialText(m) for m in mats)
			cspot = HotSpot(view, ("t", tip), None)
			cspot.SetParent(self)
			cspot.SetPosition(x, self.bgHeight)
			cspot.SetSize(self.COL_W, 20)
			cspot.Show()
			self.colWidgets.append(cspot)


class ModelCard(Block):
	"""Valiant2's monster card (special_slot.tga): the 3D model on the left, lines on the right"""

	def __init__(self, view, lines, model=None, icon=None, motion=False):
		Block.__init__(self, view, 190)
		self.K(MakeImage(self, 0, 0, IMG + "slot/special_slot.tga"))
		self.index = -1
		shown = False
		if model and renderTarget and hasattr(wndMgr, "RegisterRenderTarget"):
			try:
				self.index = renderTarget.GetFreeIndex(8000, 8999)
				renderTarget.SetBackground(self.index, IMG + "preview_back.tga")
				renderTarget.SetRotation(self.index, 1)
				if renderTarget.SetModel(self.index, *model):
					rt = self.K(_RenderTarget())
					rt.SetParent(self)
					rt.SetPosition(1, 1)
					rt.SetSize(187, 163)
					rt.SetRenderTarget(self.index)
					rt.Show()
					if motion:
						spot = self.K(ui.Window())
						spot.SetParent(self)
						spot.SetPosition(1, 1)
						spot.SetSize(187, 163)
						spot.OnMouseLeftButtonUp = ui.__mem_func__(self.OnClickModel)
						spot.Show()
						self.K(MakeText(self, 94, 170, "", COLOR_DIM, True))
					shown = True
			except Exception:
				shown = False
		if not shown and icon:
			kind, vnum = icon
			if kind == "i":
				spot = AddIcon(view, self, 78, 66, vnum, 32, False)
				self.K(spot)
			else:
				path = MobIcon(vnum)
				if path:
					self.K(MakeImage(self, 78, 66, path))
		y = 8
		for line in lines:
			text, color = line[0], line[1]
			t = self.K(MakeText(self, 200, y, "", color, False, len(line) > 2 and line[2]))
			FitText(t, text, 330)
			y += 17 if y > 8 else 22
			if y > 150:
				break

	def OnClickModel(self):
		if self.index >= 0 and self.view.IsMouseIn():
			renderTarget.Motion(self.index)

	def Destroy(self):
		if self.index >= 0 and renderTarget:
			renderTarget.Destroy(self.index)
			self.index = -1
		Block.Destroy(self)


class RecipeBlock(Block):
	"""a cube recipe: the result, the materials, Yang and chance, the NPC and where it stands"""

	def __init__(self, view, index, showNpc=True):
		data = Call("GetCube", index)
		Block.__init__(self, view, 64)
		self.K(MakeBar(self, 0, 1, ROW_W, 62, ROW_SHADE))
		self.K(MakeLine(self, 0, 0, ROW_W))
		if not data:
			return
		npcs, kind, result, count, gold, pct, mats = data
		self.K(AddIcon(view, self, 6, 6, result, 32, True, count))
		title = self.K(MakeText(self, 44, 4, "", COLOR_WHITE))
		FitText(title, ("%dx " % count if count > 1 else "") + ItemName(result), 200)
		info = "%s  \xb7  %s%%" % (TEXT_EXCHANGE if kind else TEXT_RECIPE, pct)
		if gold:
			info += "  \xb7  " + TEXT_YANG % FormatYang(gold)
		self.K(MakeText(self, 44, 21, info, COLOR_SUB))
		if showNpc and npcs:
			where = self.K(MakeText(self, 44, 41, "", COLOR_DIM))
			FitText(where, TEXT_AT % ("%s - %s" % (MobName(npcs[0]), NpcPlaces(npcs[0]))), 200)
			spot = self.K(HotSpot(view, ("t", [MobName(n) + ": " + NpcPlaces(n) for n in npcs]), ("n", npcs[0])))
			spot.SetParent(self)
			spot.SetPosition(44, 39)
			spot.SetSize(200, 18)
			spot.Show()
		x = 250
		for mat in mats[:7]:
			mvnum, mcount, mlast = mat
			self.K(AddIcon(view, self, x, 14, mvnum, 32, True, mcount))
			if mlast > mvnum:
				self.K(MakeText(self, x + 16, 48, TEXT_ANY_OF % (mlast - mvnum + 1), COLOR_DIM, True))
			x += 40
		self.K(MakeText(self, 236, 22, "=", COLOR_DIM, True))


class GridBlock(Block):
	"""a row of icon tiles with names (costumes, mounts, pets): a click opens the item"""
	TILE_W = 180

	def __init__(self, view, vnums):
		Block.__init__(self, view, 40)
		for n, vnum in enumerate(vnums[:3]):
			x = n * self.TILE_W
			self.K(MakeBar(self, x, 1, self.TILE_W - 3, 38, ROW_SHADE))
			hover = self.K(MakeBar(self, x, 1, self.TILE_W - 3, 38, ROW_HOVER))
			hover.Hide()
			spot = self.K(HotSpot(view, ("i", vnum), ("i", vnum), hover))
			spot.SetParent(self)
			spot.SetPosition(x, 0)
			spot.SetSize(self.TILE_W - 3, 40)
			spot.Show()
			img = self.K(MakeImage(self, 0, 0, ItemIcon(vnum)))
			w = max(1, img.GetWidth())
			h = max(1, img.GetHeight())
			scale = min(1.0, 32.0 / h, 32.0 / w)
			if scale < 1.0:
				img.SetScale(scale, scale)
			img.SetPosition(x + 4 + int((32 - w * scale) // 2), 4 + int((32 - h * scale) // 2))
			t = self.K(MakeText(self, x + 40, 13, "", COLOR_WHITE))
			FitText(t, ItemName(vnum), self.TILE_W - 48)


# ----------------------------------------------------------------------------------------------------------- the view

class ScrollView(ui.Window):
	"""the result page: blocks one under another, clipped to the view, scrolled by the wheel / the bar; built a few
	blocks a frame (a class's weapons are a hundred tables)"""

	def __init__(self, wiki):
		ui.Window.__init__(self)
		self.wiki = proxy(wiki)
		self.page = ui.Window()
		self.page.SetParent(self)
		self.page.SetPosition(0, 0)
		self.page.Show()
		self.page.OnMouseWheel = ui.__mem_func__(self.OnMouseWheel)
		self.blocks = []
		self.queue = []
		self.height = 0
		self.pos = 0
		self.scrollBar = ui.SmallThinScrollBar()
		self.scrollBar.SetParent(self)
		self.scrollBar.SetScrollEvent(ui.__mem_func__(self.OnScroll))
		self.scrollBar.Hide()

	def __del__(self):
		ui.Window.__del__(self)

	def Destroy(self):
		self.Clear()
		self.scrollBar = None

	def SetViewSize(self, width, height):
		self.SetSize(width, height)
		self.page.SetSize(ROW_W, max(height, self.height))
		self.scrollBar.SetPosition(width - self.scrollBar.SCROLLBAR_WIDTH, 0)
		self.scrollBar.SetScrollBarSize(height)
		self.Refresh()

	def Clear(self):
		for block in self.blocks:
			block.Hide()
			block.Destroy()
		self.blocks = []
		self.queue = []
		self.height = 0
		self.pos = 0
		self.page.SetPosition(0, 0)
		self.scrollBar.SetPos(0)
		self.scrollBar.Hide()

	def Add(self, builder, *args):
		"""a block made later (OnUpdate), in order"""
		self.queue.append((builder, args))

	def AddNow(self, block):
		self.__Append(block)

	def __Append(self, block):
		block.SetParent(self.page)
		block.SetPosition(0, self.height)
		block.Show()
		block.SetClippingMaskWindow(self)
		self.blocks.append(block)
		self.height += block.GetHeight() + 2
		self.page.SetSize(ROW_W, max(self.GetHeight(), self.height))

	def ClipBlock(self, block):
		block.SetClippingMaskWindow(self)
		self.Refresh()

	def IsBuilding(self):
		return bool(self.queue)

	def Build(self):
		if not self.queue:
			return
		end = app.GetTime() + BUILD_BUDGET
		while self.queue:
			builder, args = self.queue.pop(0)
			try:
				block = builder(_Proxy(self), *args)
			except Exception:
				import dbg
				import sys
				import traceback
				dbg.TraceError("uiwiki: block failed: " + "".join(traceback.format_exception(*sys.exc_info())))
				block = None
			if block:
				self.__Append(block)
			if app.GetTime() > end:
				break
		self.Refresh()

	def MaxScroll(self):
		return max(0, self.height - self.GetHeight())

	def Refresh(self):
		maxScroll = self.MaxScroll()
		if maxScroll > 0:
			self.scrollBar.SetMiddleBarSize(max(0.08, float(self.GetHeight()) / max(1, self.height)))
			self.scrollBar.SetScrollStep(min(0.5, 60.0 / maxScroll))
			self.scrollBar.Show()
		else:
			self.scrollBar.Hide()
		self.pos = min(self.pos, maxScroll)
		self.page.SetPosition(0, -self.pos)
		self.__ShowVisible()

	def __ShowVisible(self):
		top = self.pos
		bottom = self.pos + self.GetHeight()
		for block in self.blocks:
			(x, y) = block.GetLocalPosition()
			if y + block.GetHeight() < top or y > bottom:
				if block.IsShow():
					block.Hide()
			elif not block.IsShow():
				block.Show()

	def OnScroll(self):
		maxScroll = self.MaxScroll()
		self.pos = int(self.scrollBar.GetPos() * maxScroll)
		self.page.SetPosition(0, -self.pos)
		self.__ShowVisible()

	def ScrollBy(self, pixels):
		maxScroll = self.MaxScroll()
		if maxScroll <= 0:
			return
		self.pos = max(0, min(maxScroll, self.pos + pixels))
		self.scrollBar.SetPos(float(self.pos) / maxScroll)

	def OnMouseWheel(self, delta):
		self.ScrollBy(-48 if delta > 0 else 48)
		return True

	def IsMouseIn(self):
		(mx, my) = wndMgr.GetMousePosition()
		(x, y) = self.GetGlobalPosition()
		return x <= mx < x + self.GetWidth() and y <= my < y + self.GetHeight()


# ----------------------------------------------------------------------------------------------------------- the menu

class MenuEntry(ui.Window):
	def __init__(self, menu, text, header, action):
		ui.Window.__init__(self)
		self.menu = _Proxy(menu)
		self.header = header
		self.action = action
		self.children = []
		self.expanded = False
		self.over = False
		self.selected = False
		self.image = ui.ExpandedImageBox()
		self.image.SetParent(self)
		self.image.AddFlag("not_pick")
		self.image.SetPosition(0 if header else 1, 0)
		self.image.LoadImage(IMG + ("kategori.png" if header else "altkategori.png"))
		self.image.Show()
		self.SetSize(165 if header else 164, 29 if header else 24)
		self.text = ui.TextLine()
		self.text.SetParent(self)
		self.text.AddFlag("not_pick")
		self.text.SetPosition(self.GetWidth() // 2, (self.GetHeight() - 14) // 2)
		self.text.SetHorizontalAlignCenter()
		if header:
			self.text.SetOutline()
		FitText(self.text, text, self.GetWidth() - 14)
		self.text.Show()
		self.Refresh()

	def __del__(self):
		ui.Window.__del__(self)

	def Refresh(self):
		if self.header:
			self.text.SetPackedFontColor(COLOR_GOLD if self.expanded else 0xb3ffffff)
			return
		if self.selected:
			self.image.LoadImage(IMG + "altkategori3.png")
			self.text.SetPackedFontColor(COLOR_GOLD)
		elif self.over:
			self.image.LoadImage(IMG + "altkategori2.png")
			self.text.SetPackedFontColor(0xffffffff)
		else:
			self.image.LoadImage(IMG + "altkategori.png")
			self.text.SetPackedFontColor(0xb3ffffff)

	def OnMouseOverIn(self):
		if self.menu.IsMouseIn():
			self.over = True
			self.Refresh()

	def OnMouseOverOut(self):
		self.over = False
		self.Refresh()

	def OnMouseLeftButtonUp(self):
		if self.menu.IsMouseIn():
			self.menu.OnClick(self)

	def OnMouseWheel(self, delta):
		return self.menu.OnMouseWheel(delta)


class Menu(ui.Window):
	"""Valiant2's category list: headers (kategori.png) that fold out their entries (altkategori*.png)"""

	def __init__(self, wiki):
		ui.Window.__init__(self)
		self.wiki = proxy(wiki)
		self.headers = []
		self.pos = 0
		self.height = 0
		self.selected = None
		self.scrollBar = ui.SmallThinScrollBar()
		self.scrollBar.SetParent(self)
		self.scrollBar.SetScrollEvent(ui.__mem_func__(self.OnScroll))
		self.scrollBar.Hide()

	def __del__(self):
		ui.Window.__del__(self)

	def Destroy(self):
		self.headers = []
		self.selected = None
		self.scrollBar = None

	def SetMenuSize(self, width, height):
		self.SetSize(width, height)
		self.scrollBar.SetPosition(width - self.scrollBar.SCROLLBAR_WIDTH, 0)
		self.scrollBar.SetScrollBarSize(height)

	def AddHeader(self, text, banner):
		entry = MenuEntry(self, text, True, ("header", banner))
		entry.SetParent(self)
		entry.SetClippingMaskWindow(self)
		self.headers.append(entry)
		return entry

	def AddEntry(self, header, text, action):
		entry = MenuEntry(self, text, False, action)
		entry.SetParent(self)
		entry.SetClippingMaskWindow(self)
		header.children.append(entry)
		return entry

	def OnClick(self, entry):
		if entry.header:
			entry.expanded = not entry.expanded
			entry.Refresh()
			self.Layout()
			return
		self.Select(entry)
		self.wiki.Go(entry.action)

	def Select(self, entry):
		if self.selected and self.selected is not entry:
			self.selected.selected = False
			self.selected.Refresh()
		self.selected = entry
		if entry:
			entry.selected = True
			entry.Refresh()

	def FindEntry(self, action):
		for header in self.headers:
			for child in header.children:
				if child.action == action:
					return child
		return None

	def Layout(self):
		y = 0
		visible = []
		for header in self.headers:
			visible.append((header, y))
			y += header.GetHeight() + 1
			for child in header.children:
				if header.expanded:
					visible.append((child, y))
					y += child.GetHeight() + 1
				else:
					child.Hide()
		self.height = y
		maxScroll = max(0, self.height - self.GetHeight())
		self.pos = min(self.pos, maxScroll)
		if maxScroll > 0:
			self.scrollBar.SetMiddleBarSize(max(0.1, float(self.GetHeight()) / self.height))
			self.scrollBar.SetScrollStep(min(0.5, 50.0 / maxScroll))
			self.scrollBar.Show()
		else:
			self.scrollBar.Hide()
		for entry, ey in visible:
			top = ey - self.pos
			entry.SetPosition(0, top)
			if top + entry.GetHeight() < 0 or top > self.GetHeight():
				entry.Hide()
			else:
				entry.Show()

	def OnScroll(self):
		maxScroll = max(0, self.height - self.GetHeight())
		self.pos = int(self.scrollBar.GetPos() * maxScroll)
		self.Layout()

	def OnMouseWheel(self, delta):
		maxScroll = max(0, self.height - self.GetHeight())
		if maxScroll <= 0:
			return True
		self.pos = max(0, min(maxScroll, self.pos + (-40 if delta > 0 else 40)))
		self.scrollBar.SetPos(float(self.pos) / maxScroll)
		return True

	def IsMouseIn(self):
		(mx, my) = wndMgr.GetMousePosition()
		(x, y) = self.GetGlobalPosition()
		return x <= mx < x + self.GetWidth() and y <= my < y + self.GetHeight()


# ----------------------------------------------------------------------------------------------------------- search

class SearchResult(ui.Window):
	def __init__(self, box, index):
		ui.Window.__init__(self)
		self.box = _Proxy(box)
		self.index = index
		self.SetSize(300, 20)
		self.back = MakeBar(self, 0, 0, 300, 20, 0xf0101010)
		self.hover = MakeBar(self, 0, 0, 300, 20, 0x40ffb96d)
		self.hover.Hide()
		self.text = MakeText(self, 6, 3, "", COLOR_WHITE)
		self.sub = MakeText(self, 294, 3, "", COLOR_DIM)
		self.sub.SetHorizontalAlignRight()

	def __del__(self):
		ui.Window.__del__(self)

	def SetData(self, text, sub):
		FitText(self.text, text, 230)
		self.sub.SetText(sub)

	def OnMouseOverIn(self):
		self.hover.Show()

	def OnMouseOverOut(self):
		self.hover.Hide()

	def OnMouseLeftButtonUp(self):
		self.box.Pick(self.index)


class SearchBox(ui.Window):
	ROWS = 12

	def __init__(self, wiki):
		ui.Window.__init__(self, "TOP_MOST")
		self.wiki = proxy(wiki)
		self.rows = []
		self.results = []
		self.mode = "i"
		self.SetSize(302, self.ROWS * 20 + 2)
		MakeBar(self, 0, 0, 302, self.ROWS * 20 + 2, 0xff5a4a36)
		for n in xrange(self.ROWS):
			row = SearchResult(self, n)
			row.SetParent(self)
			row.SetPosition(1, 1 + n * 20)
			self.rows.append(row)

	def __del__(self):
		ui.Window.__del__(self)

	def Destroy(self):
		self.rows = []

	def SetResults(self, mode, results):
		self.mode = mode
		self.results = results[:self.ROWS]
		if not self.results:
			self.Hide()
			return
		for n, row in enumerate(self.rows):
			if n < len(self.results):
				vnum = self.results[n]
				if mode == "i":
					level = ItemLevel(vnum)
					row.SetData(SplitPlus(ItemName(vnum))[0], (TEXT_LEVEL % level) if level else "")
				else:
					stats = Call("GetMobStats", vnum)
					row.SetData(MobName(vnum), (TEXT_LEVEL % stats[0]) if stats else "")
				row.Show()
			else:
				row.Hide()
		self.SetSize(302, len(self.results) * 20 + 2)
		self.Show()
		self.SetTop()

	def Pick(self, index):
		if 0 <= index < len(self.results):
			self.Hide()
			self.wiki.Go((self.mode, self.results[index]))


# ----------------------------------------------------------------------------------------------------------- the window

class WikiWindow(ui.BoardWithTitleBar):
	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)
		self.AddFlag("movable")
		self.AddFlag("float")
		self.SetSize(BOARD_W, BOARD_H)
		self.SetTitleName(TEXT_TITLE)
		self.SetCloseEvent(ui.__mem_func__(self.Close))
		self.history = []
		self.current = None
		self.job = PlayerJobIndex()
		self.searchMode = "i"
		self.searchDue = 0.0
		self.lastQuery = ""
		self.tipItem = uiToolTip.ItemToolTip()
		self.tipItem.HideToolTip()
		self.tipText = uiToolTip.ToolTip()
		self.tipText.HideToolTip()
		self.loaded = bool(wikipedia) and bool(Call("Load"))

		# the background, then the result page: what comes after (banner, search, class buttons) is drawn over it and
		# takes the mouse first (a child's SetTop moves only "float" windows)
		self.background = MakeImage(self, 10, 30, IMG + "background_image.png")
		self.background.AddFlag("not_pick")

		self.view = ScrollView(self)
		self.view.SetParent(self)
		self.view.SetPosition(VIEW_X, VIEW_Y)
		self.view.SetViewSize(VIEW_W, VIEW_BOTTOM - VIEW_Y)
		self.view.Show()

		self.banner = MakeImage(self, 14, 32, IMG + "category/wikipedia.png", True)
		self.banner.SetEvent(ui.__mem_func__(self.GoHome), "mouse_click")
		self.bannerSub = MakeText(self, 375, 116, "", COLOR_GOLD, True, True)

		self.backButton = self.__SmallButton(TEXT_BACK, 650, 112, self.GoBack)
		self.homeButton = self.__SmallButton(TEXT_HOME, 590, 112, self.GoHome)

		# search (Valiant2's slot): the search button, the line, the item/monster switch
		self.searchSlot = MakeImage(self, 15, 146, IMG + "search_slot.png", True)
		self.searchButton = ui.Button()
		self.searchButton.SetParent(self.searchSlot)
		self.searchButton.SetUpVisual(IMG + "search_btn_s_0.png")
		self.searchButton.SetOverVisual(IMG + "search_btn_s_1.png")
		self.searchButton.SetDownVisual(IMG + "search_btn_s_2.png")
		self.searchButton.SetPosition(6, 6)
		self.searchButton.SetToolTipText(TEXT_SEARCH_BUTTON)
		self.searchButton.SetEvent(ui.__mem_func__(self.OnSearchEnter))
		self.searchButton.Show()
		self.searchLine = ui.EditLine()
		self.searchLine.SetParent(self.searchSlot)
		self.searchLine.SetPosition(32, 9)
		self.searchLine.SetSize(104, 16)
		self.searchLine.SetMax(30)
		self.searchLine.SetReturnEvent(ui.__mem_func__(self.OnSearchEnter))
		self.searchLine.SetEscapeEvent(ui.__mem_func__(self.OnSearchEscape))
		self.searchLine.OnIMEUpdate = ui.__mem_func__(self.OnSearchType)
		self.searchLine.Show()
		self.searchHint = MakeText(self.searchSlot, 32, 9, TEXT_SEARCH_ITEM, COLOR_DIM)
		self.searchSwitch = ui.Button()
		self.searchSwitch.SetParent(self.searchSlot)
		self.searchSwitch.SetUpVisual(IMG + "change_btn_s_0.png")
		self.searchSwitch.SetOverVisual(IMG + "change_btn_s_1.png")
		self.searchSwitch.SetDownVisual(IMG + "change_btn_s_2.png")
		self.searchSwitch.SetPosition(139, 7)
		self.searchSwitch.SetToolTipText(TEXT_SEARCH_TIP_ITEM)
		self.searchSwitch.SetEvent(ui.__mem_func__(self.OnSearchSwitch))
		self.searchSwitch.Show()
		self.searchBox = SearchBox(self)
		self.searchBox.Hide()

		self.menu = Menu(self)
		self.menu.SetParent(self)
		self.menu.SetPosition(13, 183)
		self.menu.SetMenuSize(175, VIEW_BOTTOM - 183)
		self.menu.Show()

		self.jobButtons = []
		for n, (name, picture, bit) in enumerate(JOBS):
			button = ui.RadioButton()
			button.SetParent(self)
			button.SetUpVisual(IMG + "character4/%d_0.png" % picture)
			button.SetOverVisual(IMG + "character4/%d_1.png" % picture)
			button.SetDownVisual(IMG + "character4/%d_2.png" % picture)
			button.SetPosition(JOB_X[n], 151)
			button.SetEvent(ui.__mem_func__(self.OnJob), n)
			button.SetToolTipText(name)
			button.Hide()
			self.jobButtons.append(button)

		self.__BuildMenu()
		self.GoHome()
		self.SetCenterPosition()

	def __del__(self):
		ui.BoardWithTitleBar.__del__(self)

	def __SmallButton(self, text, x, y, event):
		button = ui.Button()
		button.SetParent(self)
		button.SetUpVisual("d:/ymir work/ui/public/small_button_01.sub")
		button.SetOverVisual("d:/ymir work/ui/public/small_button_02.sub")
		button.SetDownVisual("d:/ymir work/ui/public/small_button_03.sub")
		button.SetText(text)
		button.SetPosition(x, y)
		button.SetEvent(ui.__mem_func__(event))
		button.Show()
		return button

	def Destroy(self):
		self.HideTip()
		if self.view:
			self.view.Destroy()
		if self.menu:
			self.menu.Destroy()
		if self.searchBox:
			self.searchBox.Hide()
			self.searchBox.Destroy()
		self.view = None
		self.menu = None
		self.searchBox = None
		self.jobButtons = []
		self.tipItem = None
		self.tipText = None

	# --------------------------------------------------------------------------------------------- menu
	def __BuildMenu(self):
		menu = self.menu
		if not self.loaded:
			return
		header = menu.AddHeader(TEXT_CAT_EQUIP, "equipments")
		for cat, name in enumerate(EQUIP_NAMES):
			if Call("GetEquipList", cat, 0):
				menu.AddEntry(header, name, ("equip", cat))
		header = menu.AddHeader(TEXT_CAT_COSTUME, "body_costumes")
		for cat, name, banner in COSTUME_MENU:
			if Call("GetCostumeList", cat):
				menu.AddEntry(header, name, ("costume", cat))
		header = menu.AddHeader(TEXT_CAT_MOUNT, "mounts")
		for cat, name, banner in MOUNT_MENU:
			if Call("GetCostumeList", cat):
				menu.AddEntry(header, name, ("costume", cat))
		chests = Call("GetChestCategories") or []
		if chests:
			header = menu.AddHeader(TEXT_CAT_CHEST, "chests")
			for catId, label in chests:
				menu.AddEntry(header, label, ("chests", catId))
		groups = ((0, TEXT_CAT_METIN, "metin_stones"), (1, TEXT_CAT_BOSS, "bosses"), (2, TEXT_CAT_MOB, "monsters"))
		cats = Call("GetMobCategories") or []
		for group, title, banner in groups:
			entries = [(catId, label) for catId, g, label in cats if g == group]
			if not entries:
				continue
			header = menu.AddHeader(title, banner)
			for catId, label in entries:
				menu.AddEntry(header, label, ("mobs", catId))
		npcs = Call("GetCraftNpcs") or []
		if npcs:
			header = menu.AddHeader(TEXT_CAT_CRAFT, "crafting")
			for npc, label in npcs:
				menu.AddEntry(header, MobName(npc), ("n", npc))
		menu.Layout()

	# --------------------------------------------------------------------------------------------- tooltips
	def ShowTip(self, tip):
		kind, value = tip
		if kind == "i" and not Known(value):
			kind, value = "t", [ItemName(value)]
		if kind == "i":
			self.tipText.HideToolTip()
			self.tipItem.ClearToolTip()
			self.tipItem.SetItemToolTip(value)
			self.tipItem.ShowToolTip()
		elif kind == "t":
			self.tipItem.HideToolTip()
			self.tipText.ClearToolTip()
			for n, line in enumerate(value):
				self.tipText.AppendTextLine(line, COLOR_GOLD if n == 0 else self.tipText.FONT_COLOR)
			self.tipText.ShowToolTip()

	def HideTip(self):
		if self.tipItem:
			self.tipItem.HideToolTip()
		if self.tipText:
			self.tipText.HideToolTip()

	# --------------------------------------------------------------------------------------------- navigation
	def Go(self, target, remember=True):
		if not target:
			return
		if remember and self.current and self.current != target:
			self.history.append(self.current)
			if len(self.history) > 50:
				self.history.pop(0)
		self.current = target
		self.HideTip()
		self.searchBox.Hide()
		self.view.Clear()
		kind = target[0]
		entry = self.menu.FindEntry(target)
		self.menu.Select(entry)
		showJobs = kind == "equip"
		for button in self.jobButtons:
			if showJobs:
				button.Show()
			else:
				button.Hide()
		if showJobs:
			for n, button in enumerate(self.jobButtons):
				if n == self.job:
					button.Down()
				else:
					button.SetUp()
			self.view.SetPosition(VIEW_X, VIEW_Y_JOBS)
			self.view.SetViewSize(VIEW_W, VIEW_BOTTOM - VIEW_Y_JOBS)
		else:
			self.view.SetPosition(VIEW_X, VIEW_Y)
			self.view.SetViewSize(VIEW_W, VIEW_BOTTOM - VIEW_Y)
		self.bannerSub.SetText("")
		if not self.loaded:
			self.SetBanner("wikipedia")
			self.view.AddNow(TextBlock(self.view, [TEXT_NO_DATA], COLOR_RED))
			return
		handler = {
			"home": self.PageHome, "equip": self.PageEquip, "costume": self.PageCostume, "chests": self.PageChests,
			"mobs": self.PageMobs, "n": self.PageNpc, "i": self.PageItem, "m": self.PageMob,
		}.get(kind)
		if handler:
			handler(target[1])
		self.view.Build()

	def GoBack(self):
		if not self.history:
			return
		self.Go(self.history.pop(), False)

	def GoHome(self, *args):
		self.Go(("home", 0))

	def OnJob(self, index):
		self.job = index
		if self.current and self.current[0] == "equip":
			self.Go(self.current, False)

	def SetBanner(self, name, sub=""):
		self.banner.LoadImage(IMG + "category/%s.png" % name)
		self.bannerSub.SetText(sub)

	# --------------------------------------------------------------------------------------------- pages
	def PageHome(self, arg):
		self.SetBanner("wikipedia")
		view = self.view
		lines = list(TEXT_HOME_LINES)
		view.AddNow(TextBlock(view, lines))

	def PageEquip(self, cat):
		self.SetBanner("equipments", EQUIP_NAMES[cat] if 0 <= cat < len(EQUIP_NAMES) else "")
		bit = JOBS[self.job][2]
		for v0, level, mask in Call("GetEquipList", cat, bit) or []:
			self.view.Add(lambda view, v=v0: RefineBlock(view, Call("GetChain", v) or (v,)))

	def PageCostume(self, cat):
		banner, title = "body_costumes", ""
		for c, name, b in COSTUME_MENU + MOUNT_MENU:
			if c == cat:
				banner, title = b, name
		# the banner says it already (but "Pozostale")
		self.SetBanner(banner, title if cat == 8 else "")
		vnums = [vnum for vnum, preview in Call("GetCostumeList", cat) or []]
		for n in xrange(0, len(vnums), 3):
			self.view.Add(lambda view, part=vnums[n:n + 3]: GridBlock(view, part))

	def PageChests(self, catId):
		label = ""
		for c, l in Call("GetChestCategories") or []:
			if c == catId:
				label = l
		self.SetBanner("chests", label)
		for chest, fromMob in Call("GetChestCategory", catId) or []:
			sub = (TEXT_FROM_MOB % MobName(fromMob)) if fromMob else ""
			count = len(Call("GetChestContent", chest) or [])
			self.view.Add(lambda view, c=chest, s=sub, n=count: RowBlock(view, ("i", c), ItemName(c), s, "",
				None, str(n), ("i", c), ("i", c)))

	def PageMobs(self, catId):
		group, label = 2, ""
		for c, g, l in Call("GetMobCategories") or []:
			if c == catId:
				group, label = g, l
		self.SetBanner(("metin_stones", "bosses", "monsters")[group] if 0 <= group <= 2 else "monsters", label)
		for mob in Call("GetMobCategory", catId) or []:
			self.view.Add(self.__MobRow, mob)

	def __MobRow(self, view, mob):
		stats = Call("GetMobStats", mob)
		sub = ""
		if stats:
			rank = RANK_NAMES[stats[1]] if 0 <= stats[1] < len(RANK_NAMES) else ""
			if stats[2] == 2:
				rank = TEXT_STONE
			sub = TEXT_LEVEL_RANK % (stats[0], rank)
		drops = len(Call("GetMobDrops", mob) or [])
		return RowBlock(view, ("m", mob), MobName(mob), sub, "", None, str(drops) if drops else "", ("m", mob), None)

	def PageNpc(self, npc):
		self.SetBanner("crafting", MobName(npc))
		view = self.view
		label = ""
		for n, l in Call("GetCraftNpcs") or []:
			if n == npc:
				label = l
		recipes = Call("GetNpcCubes", npc) or []
		lines = [TEXT_NPC_HEAD % (MobName(npc), len(recipes))]
		if label:
			lines.append(label)
		places = Call("GetNpcLocations", npc) or []
		for mapIndex, x, y in places[:6]:
			lines.append(TEXT_WHERE % (MapName(mapIndex), x, y))
		if not places:
			lines.append(TEXT_NO_PLACE)
		view.AddNow(TextBlock(view, lines, COLOR_WHITE))
		view.AddNow(HeaderBlock(view, SEC_RECIPES_OF, str(len(recipes))))
		for index in recipes:
			view.Add(RecipeBlock, index, False)

	def PageItem(self, vnum):
		view = self.view
		chain = Call("GetChain", vnum) or (vnum,)
		name = SplitPlus(ItemName(vnum))[0]
		self.SetBanner(self.__ItemBanner(vnum), name)
		# the card: the 3D preview (wearables), the name, kind, level, description
		model = None
		try:
			model = __import__("tooltipmodel").ModelOf(vnum)
		except Exception:
			model = None
		lines = [(ItemName(vnum), COLOR_GOLD, True)]
		level = ItemLevel(vnum)
		if level:
			lines.append((TEXT_LEVEL % level, COLOR_SUB))
		desc = ItemDescription(vnum)
		for line in WrapText(desc, 52)[:6]:
			lines.append((line, COLOR_WHITE))
		view.AddNow(ModelCard(view, [l for l in lines if l[0]], model, ("i", vnum)))
		if len(chain) > 1:
			view.Add(RefineBlock, chain)
		# a chest's content
		content = Call("GetChestContent", vnum) or []
		if content:
			view.Add(HeaderBlock, SEC_CONTENT, str(len(content)))
			view.Add(ColumnsBlock, "")
			self.__ItemRows(content, "i")
		# where it comes from
		mobs = Call("GetItemMobs", vnum) or []
		if mobs:
			view.Add(HeaderBlock, SEC_MOBS, str(len(mobs)))
			view.Add(ColumnsBlock, "")
			self.__ItemRows(mobs, "m")
		chests = Call("GetItemChests", vnum) or []
		if chests:
			view.Add(HeaderBlock, SEC_CHESTS, str(len(chests)))
			self.__ItemRows(chests, "i")
		recipes = Call("GetItemCubeSources", vnum) or []
		if recipes:
			view.Add(HeaderBlock, SEC_RECIPES, str(len(recipes)))
			for index in recipes[:MAX_ITEM_ROWS]:
				view.Add(RecipeBlock, index, True)
		shops = Call("GetItemShops", vnum) or []
		if shops:
			view.Add(HeaderBlock, SEC_SHOPS, str(len(shops)))
			for npc, price, count in shops[:MAX_ITEM_ROWS]:
				view.Add(lambda v, n=npc, p=price, c=count: RowBlock(v, ("m", n), MobName(n), NpcPlaces(n),
					FormatCount(c, c) if c > 1 else "", None, TEXT_PRICE % FormatYang(p), ("n", n),
					("t", [MobName(n), NpcPlaces(n)])))
		before = Call("GetRefineFrom", vnum)
		if before:
			step = Call("GetRefineStep", before)
			view.Add(HeaderBlock, SEC_REFINE_FROM)
			sub = ""
			if step:
				sub = "%d%%  \xb7  %s  \xb7  %s" % (step[2], TEXT_YANG % FormatYang(step[1]), ", ".join(MaterialText(m) for m in step[3]))
			view.Add(lambda v, b=before, s=sub: RowBlock(v, ("i", b), TEXT_FROM_STEP % ItemName(b), s, "", None, "",
				("i", b), ("i", b)))
		notes = Call("GetItemNotes", vnum) or []
		if notes:
			view.Add(HeaderBlock, SEC_NOTES)
			lines = []
			for note in notes:
				lines.extend(WrapText(note, 80))
			view.Add(TextBlock, lines, COLOR_WHITE)
		# what it is for
		uses = Call("GetItemCubeUses", vnum) or []
		if uses:
			view.Add(HeaderBlock, SEC_USES, str(len(uses)))
			for index in uses[:MAX_ITEM_ROWS]:
				view.Add(RecipeBlock, index, True)
			if len(uses) > MAX_ITEM_ROWS:
				view.Add(TextBlock, [TEXT_MORE % (len(uses) - MAX_ITEM_ROWS)], COLOR_DIM)
		refineUses = Call("GetItemRefineUses", vnum) or []
		if refineUses:
			view.Add(HeaderBlock, SEC_REFINE_USES, str(len(refineUses)))
			for fromVnum, count in refineUses[:MAX_ITEM_ROWS]:
				view.Add(self.__RefineUseRow, fromVnum, count)
			if len(refineUses) > MAX_ITEM_ROWS:
				view.Add(TextBlock, [TEXT_MORE % (len(refineUses) - MAX_ITEM_ROWS)], COLOR_DIM)

	def __RefineUseRow(self, view, fromVnum, count):
		step = Call("GetRefineStep", fromVnum)
		target = step[0] if step else fromVnum
		sub = (TEXT_STEP_TO_SUB % (count, step[2], FormatYang(step[1]))) if step else ""
		return RowBlock(view, ("i", target), TEXT_STEP_TO % ("%s  >  %s" % (ItemName(fromVnum), ItemName(target))), sub,
			"", None, "", ("i", target), ("i", target))

	def __ItemRows(self, rows, kind):
		for n, (vnum, cmin, cmax, chance) in enumerate(rows):
			if n >= MAX_ITEM_ROWS:
				self.view.Add(TextBlock, [TEXT_MORE % (len(rows) - MAX_ITEM_ROWS)], COLOR_DIM)
				break
			if kind == "m":
				self.view.Add(self.__DropMobRow, vnum, cmin, cmax, chance)
			else:
				self.view.Add(lambda view, v=vnum, a=cmin, b=cmax, c=chance: RowBlock(view, ("i", v), ItemName(v), "",
					FormatCount(a, b), c, "", ("i", v), ("i", v)))

	def __DropMobRow(self, view, mob, cmin, cmax, chance):
		stats = Call("GetMobStats", mob)
		sub = ""
		if stats:
			places = Call("GetMobPlaces", mob) or []
			where = ", ".join(MapName(m) for m, k in places[:2])
			sub = (TEXT_LEVEL % stats[0]) + (("  \xb7  " + where) if where else "")
		return RowBlock(view, ("m", mob), MobName(mob), sub, FormatCount(cmin, cmax), chance, "", ("m", mob), None)

	def __ItemBanner(self, vnum):
		info = Call("GetCostumeInfo", vnum)
		if info:
			for c, name, banner in COSTUME_MENU + MOUNT_MENU:
				if c == info[0]:
					return banner
		if Call("GetChestContent", vnum):
			return "chests"
		if not Known(vnum):
			return "wikipedia"
		try:
			item.SelectItem(vnum)
			if item.GetItemType() in (item.ITEM_TYPE_WEAPON, item.ITEM_TYPE_ARMOR):
				return "equipments"
		except Exception:
			pass
		return "wikipedia"

	def PageMob(self, mob):
		view = self.view
		stats = Call("GetMobStats", mob)
		group = "monsters"
		lines = [(MobName(mob), COLOR_GOLD, True)]
		if stats:
			level, rank, mtype, hp, exp, dmin, dmax, defence, gmin, gmax, raceFlag, immune, ai, resists, elements = stats
			rankName = RANK_NAMES[rank] if 0 <= rank < len(RANK_NAMES) else ""
			if mtype == 2:
				rankName = TEXT_STONE
				group = "metin_stones"
			elif rank >= 4:
				group = "bosses"
			lines.append((TEXT_LEVEL_RANK % (level, rankName), COLOR_SUB))
			lines.append((TEXT_HP % FormatYang(hp), COLOR_WHITE))
			if exp:
				lines.append((TEXT_EXP % FormatYang(exp), COLOR_WHITE))
			if dmax:
				lines.append((TEXT_DMG % (FormatYang(dmin), FormatYang(dmax)), COLOR_WHITE))
			if defence:
				lines.append((TEXT_DEF % FormatYang(defence), COLOR_WHITE))
			if gmax:
				lines.append((TEXT_GOLD % (FormatYang(gmin), FormatYang(gmax)), COLOR_WHITE))
			els = [ELEMENT_NAMES[n] for n, flag in enumerate(elements) if flag and n < len(ELEMENT_NAMES)]
			if els:
				lines.append((TEXT_ELEMENT % ", ".join(els), COLOR_GOLD))
			res = ["%s %d%%" % (RESIST_NAMES[n], value) for n, value in enumerate(resists) if value and n < len(RESIST_NAMES)]
			if res:
				for line in WrapText(TEXT_RESIST % ", ".join(res), 52)[:2]:
					lines.append((line, COLOR_DIM))
		self.SetBanner(group, MobName(mob))
		view.AddNow(ModelCard(view, lines, (mob, 0, 0, 0, 0, 0), ("m", mob), True))
		places = Call("GetMobPlaces", mob) or []
		if places:
			view.Add(HeaderBlock, SEC_PLACES)
			texts = []
			for mapIndex, kind in places:
				texts.append("%s (%s)" % (MapName(mapIndex), PLACE_KINDS[kind] if 0 <= kind < len(PLACE_KINDS) else ""))
			view.Add(TextBlock, WrapText(", ".join(texts), 80), COLOR_WHITE)
		drops = Call("GetMobDrops", mob) or []
		view.Add(HeaderBlock, SEC_DROPS, str(len(drops)))
		if drops:
			view.Add(ColumnsBlock, "")
			self.__ItemRows(drops, "i")

	# --------------------------------------------------------------------------------------------- search
	def OnSearchType(self):
		ui.EditLine.OnIMEUpdate(self.searchLine)
		text = self.searchLine.GetText()
		if text:
			self.searchHint.Hide()
		else:
			self.searchHint.Show()
			self.searchBox.Hide()
		self.searchDue = app.GetTime() + 0.25

	def __RunSearch(self):
		self.searchDue = 0.0
		text = self.searchLine.GetText()
		if text:
			self.searchHint.Hide()
		if len(text) < 2 and not text.isdigit():
			self.searchBox.Hide()
			return []
		if self.searchMode == "i":
			results = Call("SearchItems", text, SearchBox.ROWS) or []
		else:
			results = Call("SearchMobs", text, SearchBox.ROWS) or []
		(x, y) = self.searchSlot.GetGlobalPosition()
		self.searchBox.SetPosition(x, y + 34)
		self.searchBox.SetResults(self.searchMode, results)
		return results

	def OnSearchEnter(self):
		results = self.__RunSearch()
		if results:
			self.searchBox.Pick(0)
			self.searchLine.KillFocus()
		return True

	def OnSearchEscape(self):
		self.searchBox.Hide()
		self.searchLine.KillFocus()
		return True

	def OnSearchSwitch(self):
		self.searchMode = "m" if self.searchMode == "i" else "i"
		self.searchHint.SetText(TEXT_SEARCH_ITEM if self.searchMode == "i" else TEXT_SEARCH_MOB)
		self.searchSwitch.SetToolTipText(TEXT_SEARCH_TIP_ITEM if self.searchMode == "i" else TEXT_SEARCH_TIP_MOB)
		if self.searchLine.GetText():
			self.__RunSearch()

	# --------------------------------------------------------------------------------------------- frame
	def OnUpdate(self):
		if self.view:
			self.view.Build()
		if self.searchDue and app.GetTime() >= self.searchDue:
			self.__RunSearch()
		if self.searchBox and self.searchBox.IsShow():
			(x, y) = self.searchSlot.GetGlobalPosition()
			self.searchBox.SetPosition(x, y + 34)

	def Open(self):
		self.Show()
		self.SetTop()

	def Close(self):
		self.HideTip()
		if self.searchBox:
			self.searchBox.Hide()
		if self.searchLine:
			self.searchLine.KillFocus()
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def OnPressExitKey(self):
		self.Close()
		return True


# ----------------------------------------------------------------------------------------------------------- module

def _Window():
	if _window[0] is None:
		_window[0] = WikiWindow()
	return _window[0]


def Toggle():
	window = _window[0]
	if window and window.IsShow():
		window.Close()
	else:
		_Window().Open()


def Open():
	_Window().Open()


def OpenItem(vnum):
	window = _Window()
	window.Open()
	window.Go(("i", Call("GetChain", vnum) and vnum or vnum))


def OpenMob(vnum):
	window = _Window()
	window.Open()
	window.Go(("m", vnum))


def Available():
	"""the exe has the wiki (module wikipedia)"""
	return wikipedia is not None


def IsOpen():
	window = _window[0]
	return bool(window and window.IsShow())


def Destroy():
	window = _window[0]
	if window:
		window.Close()
		window.Destroy()
	_window[0] = None
