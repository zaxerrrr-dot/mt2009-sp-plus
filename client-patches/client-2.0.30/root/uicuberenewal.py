# MT2009_PLUS_CUBE_RENEWAL_V1 (the owner, 28 October 2026: "the crafting windows like on global"): the crafting window
# of the global servers (GF 26.1.11's cube renewal: uiscript/cuberenewalwindow.py, d:/ymir work/ui/game/cube) for both
# of our crafting systems - no new packet, no server change:
#  * CubeRenewalWindow - the NPCs' cube (cube.txt and every cube.*.txt merged into it, Seon-Pyeong's rows from the elite
#    refine sets). It takes the place of uicubeokno.py and keeps its protocol and interface: the server's "cube r_list" /
#    "cube m_info" (game.py: AddCubeResultItem, AddMaterialInfo, SetResultExtra - the Yang, chance, Gaya and category of
#    a row), "/cube pick" (the chosen row), "/cube improve" (the chance-raising slot, "CubeImprove" back), "/cube add" /
#    "/ekwipunek kostka" (the materials from the bag and the extra inventory) and "/cube make". The quantity: the stacks
#    for N attempts go into the server's window once and "/cube make" is sent N times (each attempt its own chance, the
#    chance-raising item one piece an attempt, as before); only for a stackable result, as on global.
#    MT2009_PLUS_CUBE_RENEWAL_V2 (fix 3.0.4 #5): the set blacksmiths (20475-20479, V1 left them on uicube.py) here
#    too, as the global "Uszlachetnienie": "Wykonaj zestaw broni / zbroi / helmu" -> every piece of level 75+ (+7 or
#    more) by its base item -> +7 / +8 / +9 ... (cube_setsmith_data.py and the bag), the chosen piece's own cell put in.
#  * CraftingRenewalWindow - the quest crafting windows (crafting.open(...), crafting_data.lua, world.crafting_proto:
#    the blacksmith 20016, Baek-Go, the cook, the alchemists, ...). It takes the place of uicraft.py's CraftingWindow and
#    keeps its interface (current_crafting_vnum, Open, OnCraftUpdate, Close; game.py's craft_recipe / craft_avail /
#    craft_open fill constInfo.CRAFTING_DATA) and its command "/craft create <recipe> <quantity>" (crafting.lua, the
#    server limits the quantity to 99). The categories are uicraft.py's own (by the crafting window), the recipes a
#    player cannot make yet (level, recipe progress) stay in the list in red, as before.
# The list: the categories (+/-), a result with more than one recipe as its own +/- row, the recipes with the chance and
# "[n]" - how many times the bag's materials, Yang and Gaya make it; a search line over the list. The materials show
# "have/need" for the chosen quantity. Texts in Polish (CP1250).
import ui
import net
import player
import item
import grp
import app
import chat
import snd
import mouseModule
import constInfo
import uiCube

GAYA_VNUM = 95927
MAX_MATERIALS = 6
CUBE_SLOT_MAX = 24
USE_LIMIT_RANGE = 1000
CUBE_MAX_QUANTITY = 200
CRAFT_MAX_QUANTITY = 99
VIEW_ROWS = 12
ROW_STEP = 20
ROW_Y = 11
ROW_RIGHT = 340		# the rows end here (the list's scroll bar is right of it)
REFRESH_TIME = 0.5
BATCH_TIMEOUT = 4.0

IMG = "d:/ymir work/ui/game/cube/"
COLOR_OK = grp.GenerateColor(0.5411, 0.7254, 0.5568, 1.0)
COLOR_BAD = grp.GenerateColor(0.9, 0.4745, 0.4627, 1.0)
COLOR_NORMAL = grp.GenerateColor(0.7607, 0.7607, 0.7607, 1.0)
COLOR_SUB = 0xffa28b5f
COLOR_GOLD = grp.GenerateColor(1.0, 0.85, 0.4, 1.0)
COLOR_GAYA = grp.GenerateColor(0.6, 0.85, 1.0, 1.0)

TEXT_TITLE = "Wytwarzanie"
TEXT_MAKE = "Wytw\xf3rz"
TEXT_CLOSE = "Zamknij"
TEXT_IMPROVE = "Szansa+"
TEXT_IMPROVE_TITLE = "Zwi\xeaksz szans\xea"
TEXT_IMPROVE_HINT = "Po\xb3\xf3\xbf tu przedmiot zwi\xeakszaj\xb9cy szans\xea."
TEXT_IMPROVE_NONE = "Tu nie mo\xbfna zwi\xeakszy\xe6 szansy."
TEXT_CLICK_REMOVE = "Kliknij, aby go wyj\xb9\xe6."
TEXT_SEARCH = "Szukaj..."
TEXT_PICK = "Wybierz przepis z listy."
TEXT_NOTHING = "Nic nie znaleziono."
TEXT_CHANCE = "Szansa: %s%%"
TEXT_CHANCE_BONUS = "Szansa: %s%% (+%d%%)"
TEXT_COST = "Koszt: %s Yang"
TEXT_GAYA = "Gaya: %d"
TEXT_MISSING = "Brakuje: %s"
TEXT_NO_GOLD = "Masz za ma\xb3o Yang."
TEXT_NO_GAYA = "Masz za ma\xb3o Gaya."
TEXT_TOO_MANY = "Za du\xbfo stos\xf3w materia\xb3\xf3w - po\xb3\xb9cz je w ekwipunku albo wytw\xf3rz mniej."
TEXT_SUCCESS = "Uda\xb3o si\xea: %s"
TEXT_FAIL = "Nie uda\xb3o si\xea."
TEXT_BATCH = "Udane pr\xf3by: %d z %d."
TEXT_OR = "albo"
TEXT_QTY = "Ilo\x9c\xe6 pr\xf3b: - jedna, + najwi\xeacej, ile si\xea da."
TEXT_QTY_ONE = "Ten przedmiot wytwarza si\xea pojedynczo."
TEXT_NOT_AVAILABLE = "Ten przepis jest jeszcze niedost\xeapny."
TEXT_REQ_LEVEL = "Wymagany poziom: %d"
TEXT_REQ_RECIPE = "Przeczytane receptury: %d/%d"
TEXT_RECIPES = "przepisy: %d"

# the server's cube categories (cube.cpp, MT2009_CUBE_CAT_*; locale/cube_improve.txt) - the order of the list
CUBE_CATEGORY_NAMES = {
	0 : "Zbroje i he\xb3my",
	1 : "Bronie",
	2 : "Akcesoria",
	3 : "Pasy",
	4 : "Wydarzenia",
	5 : "Pozosta\xb3e",
	6 : "Rzemios\xb3o",
	7 : "Zestawy: bro\xf1",
	8 : "Zestawy: zbroje",
	9 : "Zestawy: he\xb3my",
	10 : "Zwierzaki",
	11 : "Ksi\xeagi umiej\xeatno\x9cci",
	12 : "R\xeakawice",
	13 : "Alchemia",
}
CUBE_CATEGORY_ORDER = (1, 0, 12, 2, 3, 7, 8, 9, 11, 10, 13, 6, 4, 5)
CUBE_CATEGORY_OTHER = 5

# MT2009_PLUS_CUBE_RENEWAL_V2 (fix 3.0.4 #5): the set blacksmiths in this window, as the global "Uszlachetnienie".
# NPC -> the set it puts on a piece (cube.txt "set_value", tools/ysets/gen_ysets.py; ysets_data.SETS for the prefix)
SET_SMITHS = {20475 : 1, 20476 : 2, 20477 : 3, 20478 : 4, 20479 : 5}
SET_PART_CATEGORY = {1 : 7, 2 : 8, 3 : 9}	# set_part (1 weapon, 2 armour, 3 helmet) -> the server's category
SET_CATEGORY_NAMES = {
	7 : "Wykonaj zestaw broni",
	8 : "Wykonaj zestaw zbroi",
	9 : "Wykonaj zestaw he\xb3mu",
}
SET_MIN_LEVEL = 75
SET_MIN_REFINE = 7
TEXT_SET_TITLE = "Uszlachetnienie"
TEXT_SET_OK = "OK"
TEXT_SET_CANCEL = "Anuluj"
TEXT_SET_IMPROVE = "Podwy\xbfsz szans\xea"
TEXT_SET_HAS = "Ten przedmiot ma ju\xbf ten efekt zestawu."

# the search: CP1250 letters folded to plain small ones ("zbroja" finds "Zbroja", "helm" finds "Helm")
_FOLD = {}
for _a, _b in (("\xa5\xb9", "a"), ("\xc6\xe6", "c"), ("\xca\xea", "e"), ("\xa3\xb3", "l"), ("\xd1\xf1", "n"), ("\xd3\xf3", "o"),
				("\x8c\x9c", "s"), ("\x8f\x9f", "z"), ("\xaf\xbf", "z")):
	for _c in _a:
		_FOLD[_c] = _b


def _Fold(text):
	return "".join([_FOLD.get(c, c) for c in text]).lower()


def _Money(value):
	text = str(max(0, int(value)))
	parts = []
	while len(text) > 3:
		parts.insert(0, text[-3:])
		text = text[:-3]
	parts.insert(0, text)
	return ".".join(parts)


def _ChanceMin(chance):
	try:
		return int(str(chance).split("-")[0])
	except ValueError:
		return 0


def _ItemName(vnum):
	item.SelectItem(vnum)
	return item.GetItemName()


def _IsStackable(vnum):
	item.SelectItem(vnum)
	try:
		if item.IsAntiFlag(item.ANTIFLAG_STACK):
			return False
		return bool(item.IsFlag(item.ITEM_FLAG_STACKABLE))
	except Exception:
		return False


def _BagCountsCube():
	# every item of the bag and the extra inventory once (the cube window takes from both - uicube.py)
	counts = {}
	for pos in uiCube._CubePositions():
		vnum = uiCube._ItemIndex(pos)
		if vnum:
			counts[vnum] = counts.get(vnum, 0) + uiCube._ItemCount(pos)
	# MT2009_PLUS_GAYA_CURRENCY_V1: the Gaya is the counter next to the Yang (gayacurrency.py), not a bag item
	gaya = __import__("gayacurrency")
	if gaya.Enabled():
		counts[GAYA_VNUM] = counts.get(GAYA_VNUM, 0) + gaya.Get()
	return counts


def _BagCountsCraft():
	# the inventory pages (uicraft.py: utils.CountItemCountInInventory) and the extra inventory - what crafting.lua's
	# pc.count_item counts
	counts = {}
	try:
		pageCount = player.INVENTORY_PAGE_COUNT - 1
		if constInfo.IS_HORSE_SUMMONED:
			pageCount += 1
		cells = player.INVENTORY_PAGE_SIZE * pageCount
	except Exception:
		cells = player.INVENTORY_SLOT_COUNT
	for i in xrange(cells):
		vnum = player.GetItemIndex(i)
		if vnum:
			counts[vnum] = counts.get(vnum, 0) + player.GetItemCount(i)
	# MT2009_PLUS_EKWIPUNEK_CATS_V2 (the owner, 3 November 2026: "Okna wytwarzania u NPC (kowal, kucharz, alchemicy...)
	# licza i zabieraja materialy z dodatkowego EQ"): crafting.lua's pc.count_item / pc.remove_item are the engine's
	# CountSpecifyItem / RemoveSpecifyItem, which count and take the extra inventory's storages too
	# (server-patches/ekwipunek "count" / "remove") - the window counts them as well
	try:
		import uiekwipunek
		for window, slotType, name, icon in uiekwipunek.Categories():
			for pos in xrange(uiekwipunek.COLUMNS * uiekwipunek.ROWS * len(uiekwipunek.PAGE_NAMES)):
				vnum = player.GetItemIndex(window, pos)
				if vnum:
					counts[vnum] = counts.get(vnum, 0) + player.GetItemCount(window, pos)
	except Exception:
		pass
	return counts


_SET_PIECE_INFO = {}


def _SetPieceInfo(vnum):
	# (part, base vnum, base name, refine level, level limit) of a piece a set blacksmith works on, else None - the
	# server's rule (server-patches/ysets, Mt2009YSetsPart + Mt2009YSetsCubeGear): a weapon (not an arrow), a body
	# armour or a helmet of level 75+, refined to +7 or more (the number after the last "+" of its name)
	if vnum in _SET_PIECE_INFO:
		return _SET_PIECE_INFO[vnum]
	info = None
	try:
		item.SelectItem(vnum)
		itemType = item.GetItemType()
		subType = item.GetItemSubType()
		part = 0
		if itemType == item.ITEM_TYPE_WEAPON and subType != getattr(item, "WEAPON_ARROW", 6):
			part = 1
		elif itemType == item.ITEM_TYPE_ARMOR and subType == getattr(item, "ARMOR_BODY", 0):
			part = 2
		elif itemType == item.ITEM_TYPE_ARMOR and subType == getattr(item, "ARMOR_HEAD", 1):
			part = 3
		level = 0
		for i in xrange(getattr(item, "LIMIT_MAX_NUM", 2)):
			(limitType, limitValue) = item.GetLimit(i)
			if limitType == getattr(item, "LIMIT_LEVEL", 1):
				level = limitValue
				break
		name = item.GetItemName()
		plus = name.rfind("+")
		refine = 0
		if plus >= 0:
			digits = ""
			for c in name[plus + 1:]:
				if not c.isdigit():
					break
				digits += c
			refine = digits and int(digits) or 0
		if part and level >= SET_MIN_LEVEL and refine >= SET_MIN_REFINE:
			info = (part, vnum - refine, name[:plus].rstrip(), refine, level)
	except Exception:
		info = None
	_SET_PIECE_INFO[vnum] = info
	return info


def _SetListedPieces():
	# the generated list (tools/cube/gen_setsmith_items.py) - every piece of the server's item_proto the rule takes
	try:
		import cube_setsmith_data
		return cube_setsmith_data.PIECES
	except Exception:
		return {}


def _SetOf(cell):
	# the set effect a piece of the bag has now (ysets.py: the server's "YITEM" lines)
	try:
		import ysets
		return ysets.GetFor(player.INVENTORY, cell) & 0x0F
	except Exception:
		return 0


def _SetPrefix(setValue):
	try:
		import ysets_data
		return ysets_data.SETS[setValue][0]
	except Exception:
		return ""


class ListRow(ui.Window):
	# one line of the list: a category (kind 1), a result with more recipes (kind 2) or a recipe (kind 3)
	IMAGES = {
		1 : (IMG + "cube_menu_tab1.sub", IMG + "cube_menu_tab1.sub", 306),
		2 : (IMG + "cube_menu_tab2.sub", IMG + "cube_menu_tab2.sub", 275),
		3 : (IMG + "cube_menu_tab3_default.sub", IMG + "cube_menu_tab3_select.sub", 255),
	}

	def __init__(self, owner):
		ui.Window.__init__(self)
		self.owner = owner
		self.entry = None
		self.kind = 0
		self.selected = False
		self.over = False
		self.scaleX = 1.0
		self.bgImage = ""

		self.bg = ui.ExpandedImageBox()
		self.bg.SetParent(self)
		self.bg.AddFlag("not_pick")
		self.bg.Show()

		self.icon = ui.ImageBox()
		self.icon.SetParent(self)
		self.icon.AddFlag("not_pick")

		self.countText = ui.TextLine()
		self.countText.SetParent(self)
		self.countText.AddFlag("not_pick")
		self.countText.SetPosition(17, 2)
		self.countText.SetPackedFontColor(COLOR_OK)

		self.text = ui.TextLine()
		self.text.SetParent(self)
		self.text.AddFlag("not_pick")
		self.text.SetPosition(17, 2)
		self.text.Show()

	def __del__(self):
		ui.Window.__del__(self)

	def __SetBg(self, path):
		# MT2009_PLUS_CUBE_RENEWAL_V2 (fix 3.0.4 #3): ExpandedImageBox.LoadImage makes a new image instance
		# (CImageBox::LoadImageFromGraphicImage -> OnCreateInstance) - its scale is 1.0 again and the window takes the
		# image's own size. V1 loaded the "select" bar on the mouse's "over in" without the scale: the row got narrower
		# (255 instead of 299-319) until the half-second refresh bound it again. Every load sets the scale again now.
		if path != self.bgImage:
			self.bg.LoadImage(path)
			self.bgImage = path
		self.bg.SetScale(self.scaleX, 1.0)

	def Bind(self, entry, x, y, selected):
		self.entry = entry
		self.selected = selected
		kind = entry["kind"]
		width = ROW_RIGHT - x
		if kind != self.kind:
			self.kind = kind
			self.over = False
		(up, down, imgWidth) = self.IMAGES[kind]
		self.scaleX = float(width) / imgWidth
		self.__SetBg((selected or self.over) and down or up)
		self.SetSize(width, 18)
		self.SetPosition(x, y)

		textX = 17
		if kind == 1:
			self.icon.LoadImage(IMG + (entry["open"] and "cube_menu_tab1_minus.sub" or "cube_menu_tab1_plus.sub"))
			self.icon.SetPosition(7, 3)
			self.icon.Show()
			textX = 25
			self.text.SetPackedFontColor(COLOR_NORMAL)
		elif kind == 2:
			self.icon.LoadImage(IMG + (entry["open"] and "cube_menu_tab2_minus.sub" or "cube_menu_tab2_plus.sub"))
			self.icon.SetPosition(7, 4)
			self.icon.Show()
			textX = 21
			self.text.SetPackedFontColor(COLOR_SUB)
		else:
			self.icon.Hide()
			self.text.SetPackedFontColor(entry.get("color", COLOR_NORMAL))
		count = entry.get("count", 0)
		if count > 0:
			self.countText.SetText("[%d]" % count)
			self.countText.SetPosition(textX, 2)
			self.countText.Show()
			(w, h) = self.countText.GetTextSize()
			textX += w + 3
		else:
			self.countText.Hide()
		self.text.SetPosition(textX, 2)
		self.text.SetText(entry["text"])
		self.Show()

	def OnMouseLeftButtonUp(self):
		if self.entry:
			self.owner.OnRowClick(self.entry)

	def OnMouseOverIn(self):
		self.over = True
		if self.kind == 3 and not self.selected:
			self.__SetBg(self.IMAGES[3][1])

	def OnMouseOverOut(self):
		self.over = False
		if self.kind == 3 and not self.selected:
			self.__SetBg(self.IMAGES[3][0])

	def OnMouseWheel(self, delta):
		self.owner.OnListWheel(delta)
		return True


class _RenewalBase(ui.ScriptWindow):
	# the window and the list; a source fills self.recipes (dicts: key, reward, count, columns [[(vnum, count), ...]],
	# gold, chance, gaya, category name and order, available, color, info) and makes the chosen one
	HAS_IMPROVE = False
	HAS_GAYA = False

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.tooltipItem = None
		self.recipes = []
		self.defaultOpen = True	# a category's +/- before the player clicks it
		self.selectedKey = None
		self.openCategories = {}
		self.openRewards = {}
		self.entries = []
		self.startLine = 0
		self.rows = []
		self.counts = {}
		self.nextRefresh = 0.0
		self.listDirty = False
		self.shownMaterials = []
		self.infoUntil = 0.0
		self.isLoaded = False
		self.ignoreScroll = False
		self.improveTipShown = False
		self.xStart = 0
		self.yStart = 0

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def LoadWindow(self):
		if self.isLoaded:
			return
		self.isLoaded = True
		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "uiscript/cuberenewalwindow.py")
		except:
			import exception
			exception.Abort("CubeRenewalWindow.LoadWindow.LoadObject")

		try:
			GetObject = self.GetChild
			self.board = GetObject("board")
			self.listBoard = GetObject("item_list_board")
			self.scrollBar = GetObject("cube_list_scroll_bar")
			self.itemSlotImage = GetObject("item_slot")
			self.searchEdit = GetObject("search_edit")
			self.infoText = GetObject("info_text")
			self.yangText = GetObject("yang_text")
			self.gemText = GetObject("gem_text")
			self.gemIcon = GetObject("gem_icon")
			self.gemTextBg = GetObject("gem_textbg")
			self.qtyEdit = GetObject("result_qty")
			self.qtySub = GetObject("qty_sub_button")
			self.qtyAdd = GetObject("qty_add_button")
			self.improveImage = GetObject("imporve_slot")
			self.improveText = GetObject("improve_text")
			self.okButton = GetObject("button_ok")
			self.cancelButton = GetObject("button_cancel")
			self.materialTexts = [GetObject("material_qty_text_%d" % (i + 1)) for i in xrange(MAX_MATERIALS)]
		except:
			import exception
			exception.Abort("CubeRenewalWindow.LoadWindow.BindObject")

		self.board.SetTitleName(TEXT_TITLE)
		self.board.SetCloseEvent(ui.__mem_func__(self.OnPressCancel))
		self.okButton.SetText(TEXT_MAKE)
		self.okButton.SetEvent(ui.__mem_func__(self.OnPressMake))
		self.cancelButton.SetText(TEXT_CLOSE)
		self.cancelButton.SetEvent(ui.__mem_func__(self.OnPressCancel))
		self.qtySub.SetEvent(ui.__mem_func__(self.__OnQtySub))
		self.qtyAdd.SetEvent(ui.__mem_func__(self.__OnQtyAdd))
		self.qtyEdit.SetReturnEvent(ui.__mem_func__(self.__OnQtyReturn))
		self.qtyEdit.SetEscapeEvent(ui.__mem_func__(self.__OnQtyReturn))
		self.improveText.SetText(TEXT_IMPROVE)
		self.searchEdit.SetPlaceholder(TEXT_SEARCH)
		self.searchEdit.OnIMEUpdate = ui.__mem_func__(self.__OnSearchUpdate)
		self.searchEdit.SetReturnEvent(ui.__mem_func__(self.__OnSearchReturn))
		self.searchEdit.SetEscapeEvent(ui.__mem_func__(self.__OnSearchReturn))
		self.scrollBar.SetScrollEvent(ui.__mem_func__(self.__OnScroll))
		self.listBoard.SetMouseWheelEvent(self.OnListWheel)

		for i in xrange(VIEW_ROWS):
			row = ListRow(self)
			row.SetParent(self.listBoard)
			row.Hide()
			self.rows.append(row)

		# the result and the material columns: a slot of 32 x 96 each over cube_slot_bg's frames
		self.columnSlots = []
		for i in xrange(MAX_MATERIALS + 1):
			x = 25 if i == 0 else 25 + 62 + 46 * (i - 1)
			slot = ui.SlotWindow()
			slot.SetParent(self.itemSlotImage)
			slot.SetPosition(x, 13)
			slot.SetSize(32, 96)
			slot.AppendSlot(0, 0, 0, 32, 96)
			slot.baseX = x
			slot.SetOverInItemEvent(lambda trash = 0, col = i: self.__OverInColumn(col))
			slot.SetOverOutItemEvent(ui.__mem_func__(self.__OverOut))
			slot.Show()
			self.columnSlots.append(slot)

		self.improveSlot = ui.SlotWindow()
		self.improveSlot.SetParent(self.improveImage)
		self.improveSlot.SetPosition(6, 5)
		self.improveSlot.SetSize(32, 32)
		self.improveSlot.AppendSlot(0, 0, 0, 32, 32)
		self.improveSlot.SetSelectEmptySlotEvent(ui.__mem_func__(self.__OnImproveDrop))
		self.improveSlot.SetSelectItemSlotEvent(ui.__mem_func__(self.__OnImproveClick))
		self.improveSlot.SetOverInItemEvent(ui.__mem_func__(self.__OverInImprove))
		self.improveSlot.SetOverOutItemEvent(ui.__mem_func__(self.__OverOut))
		self.improveSlot.Show()
		for w in (self.improveImage, self.improveText, self.improveSlot):
			if self.HAS_IMPROVE:
				w.Show()
			else:
				w.Hide()
		for w in (self.gemIcon, self.gemTextBg):
			if self.HAS_GAYA:
				w.Show()
			else:
				w.Hide()
		self.SetCenterPosition()
		self.ShowRecipe()

	def SetItemToolTip(self, tooltipItem):
		self.tooltipItem = tooltipItem

	def Destroy(self):
		self.tooltipItem = None
		for row in self.rows:
			row.owner = None
			row.entry = None
		self.rows = []
		self.columnSlots = []
		self.recipes = []
		self.entries = []
		self.ClearDictionary()

	# ------------------------------------------------------------------ the source's part
	def GetBagCounts(self):
		return {}

	def GetImproveBonus(self, recipe):
		return 0

	def MaxQuantity(self, recipe):
		return 1

	def MakeRecipe(self, recipe, quantity):
		pass

	def SendClose(self):
		pass

	# ------------------------------------------------------------------ open / close
	def _OpenCommon(self, title):
		self.LoadWindow()
		self.board.SetTitleName(title)
		self.selectedKey = None
		self.startLine = 0
		self.openCategories = {}
		self.openRewards = {}
		self.searchEdit.SetText("")
		self.searchEdit.KillFocus()
		if getattr(self.searchEdit, "placeholderTextLine", None):
			self.searchEdit.placeholderTextLine.Show()
		self.qtyEdit.SetText("1")
		self.SetInfo("", COLOR_NORMAL, 0)
		self.counts = self.GetBagCounts()
		self.listDirty = True
		self.Show()
		self.SetTop()
		(self.xStart, self.yStart, z) = player.GetMainCharacterPosition()

	def OnPressCancel(self):
		self.SendClose()
		self.CloseWindow()

	def CloseWindow(self):
		if self.tooltipItem:
			self.tooltipItem.HideToolTip()
		if self.isLoaded:
			self.searchEdit.KillFocus()
			self.qtyEdit.KillFocus()
		self.Hide()

	def OnPressEscapeKey(self):
		self.OnPressCancel()
		return True

	def SetInfo(self, text, color, seconds):
		if not self.isLoaded:
			return
		self.infoText.SetText(text)
		self.infoText.SetPackedFontColor(color)
		self.infoUntil = (app.GetTime() + seconds) if seconds else 0.0

	def OnUpdate(self):
		(x, y, z) = player.GetMainCharacterPosition()
		if abs(x - self.xStart) > USE_LIMIT_RANGE or abs(y - self.yStart) > USE_LIMIT_RANGE:
			self.OnPressCancel()
			return
		now = app.GetTime()
		if self.listDirty:
			self.counts = self.GetBagCounts()
			self.RebuildList()
			self.ShowRecipe()
			self.nextRefresh = now + REFRESH_TIME
		elif now >= self.nextRefresh:	# the bag changes: "[n]" and "have/need" every half second
			self.nextRefresh = now + REFRESH_TIME
			self.counts = self.GetBagCounts()
			self.RebuildList()
			self.ShowRecipe()
		if self.infoUntil and now >= self.infoUntil:
			self.infoUntil = 0.0
			self.ShowChance()
		# an empty slot has no "over in" event: the chance-raising slot's hint while the mouse is over it
		if self.HAS_IMPROVE and not self.ImproveVnum():
			over = self.improveImage.IsIn() and not mouseModule.mouseController.isAttached()
			if over and not self.improveTipShown:
				self.ShowImproveTip()
			elif not over and self.improveTipShown:
				self.HideTip()
			self.improveTipShown = over
		else:
			self.improveTipShown = False

	# ------------------------------------------------------------------ the list
	def CanMake(self, recipe, quantity = 1):
		# how many attempts the bag's materials, Yang and Gaya allow (0: none)
		if not recipe["available"]:
			return 0
		best = 1 << 30
		for alternatives in recipe["columns"]:
			if not alternatives:
				continue
			have = 0
			for (vnum, count) in alternatives:
				if count > 0:
					have = max(have, self.counts.get(vnum, 0) / count)
			best = min(best, have)
		if recipe["gold"] > 0:
			best = min(best, int(player.GetElk() / recipe["gold"]))
		if recipe["gaya"] > 0:
			best = min(best, self.counts.get(GAYA_VNUM, 0) / recipe["gaya"])
		if best == 1 << 30:
			best = 0
		return max(0, best)

	def __Matches(self, recipe, words):
		if not words:
			return True
		name = recipe.setdefault("fold", _Fold(_ItemName(recipe["reward"])))
		for w in words:
			if name.find(w) < 0:
				return False
		return True

	def RebuildList(self):
		self.listDirty = False
		words = _Fold(self.searchEdit.GetText()).split()
		groups = {}
		order = []
		for recipe in self.recipes:
			if not self.__Matches(recipe, words):
				continue
			cat = recipe["category"]
			if cat not in groups:
				groups[cat] = ([], {})
				order.append(cat)
			(rewards, byReward) = groups[cat]
			group = recipe.get("group", recipe["reward"])	# MT2009_PLUS_CUBE_RENEWAL_V2: the set blacksmiths' base piece
			if group not in byReward:
				byReward[group] = []
				rewards.append(group)
			byReward[group].append(recipe)
		order.sort(key = lambda c: (self.CategoryOrder(c), c))

		entries = []
		for cat in order:
			(rewards, byReward) = groups[cat]
			isOpen = bool(words) or self.openCategories.get(cat, self.defaultOpen)
			entries.append({"kind" : 1, "cat" : cat, "open" : isOpen, "text" : self.CategoryName(cat)})
			if not isOpen:
				continue
			for reward in rewards:
				recipes = byReward[reward]
				if len(recipes) == 1 and not recipes[0].get("alwaysGroup"):
					entries.append(self.__RecipeEntry(recipes[0], 15))
					continue
				rewardKey = (cat, reward)
				rewardOpen = bool(words) or self.openRewards.get(rewardKey, False)
				text = recipes[0].get("groupText") or "%s (%s)" % (_ItemName(reward), TEXT_RECIPES % len(recipes))
				entries.append({"kind" : 2, "rkey" : rewardKey, "open" : rewardOpen, "indent" : 15,
								"text" : text, "count" : self.GroupCount(recipes)})
				if rewardOpen:
					for recipe in recipes:
						entries.append(self.__RecipeEntry(recipe, 35))
		self.entries = entries
		self.__UpdateScroll()
		self.__ShowRows()

	def GroupCount(self, recipes):
		# "[n]" of a result's own row: how many times the bag makes its recipes
		return sum([self.CanMake(r) for r in recipes])

	def RecipeCount(self, recipe):
		# "[n]" of a recipe's row
		return self.CanMake(recipe)

	def __RecipeEntry(self, recipe, indent):
		name = recipe.get("label") or _ItemName(recipe["reward"])
		if recipe["count"] > 1:
			name = "%s x%d" % (name, recipe["count"])
		chance = recipe["chance"]
		if chance:
			bonus = self.GetImproveBonus(recipe)
			if bonus > 0 and str(chance).isdigit():
				chance = str(min(100, int(chance) + bonus))
			name = "%s (%s%%)" % (name, chance)
		count = self.RecipeCount(recipe)
		color = recipe.get("color") or (count > 0 and COLOR_NORMAL or grp.GenerateColor(0.6, 0.6, 0.6, 1.0))
		return {"kind" : 3, "recipe" : recipe, "indent" : indent, "text" : name, "count" : count, "color" : color}

	def __UpdateScroll(self):
		over = len(self.entries) - VIEW_ROWS
		if over <= 0:
			self.startLine = 0
			self.scrollBar.Hide()
			return
		self.startLine = min(self.startLine, over)
		self.scrollBar.SetMiddleBarSize(float(VIEW_ROWS) / float(len(self.entries)))
		self.scrollBar.SetScrollStep(1.0 / over)
		self.ignoreScroll = True
		self.scrollBar.SetPos(float(self.startLine) / over)
		self.ignoreScroll = False
		self.scrollBar.Show()

	def __ShowRows(self):
		for i in xrange(VIEW_ROWS):
			index = self.startLine + i
			row = self.rows[i]
			if index >= len(self.entries):
				row.Hide()
				continue
			entry = self.entries[index]
			x = 6 + entry.get("indent", 0)
			selected = entry["kind"] == 3 and entry["recipe"]["key"] == self.selectedKey
			row.Bind(entry, x, ROW_Y + ROW_STEP * i, selected)

	def __OnScroll(self):
		over = len(self.entries) - VIEW_ROWS
		if over <= 0 or self.ignoreScroll:
			return
		start = int(round(over * self.scrollBar.GetPos()))
		if start != self.startLine:
			self.startLine = start
			self.__ShowRows()

	def OnListWheel(self, delta):
		over = len(self.entries) - VIEW_ROWS
		if over <= 0:
			return True
		self.startLine = max(0, min(over, self.startLine + (delta > 0 and -1 or 1)))
		self.__UpdateScroll()
		self.__ShowRows()
		return True

	def OnMouseWheel(self, delta):
		return self.OnListWheel(delta)

	def OnRowClick(self, entry):
		kind = entry["kind"]
		if kind == 1:
			self.openCategories[entry["cat"]] = not entry["open"]
			self.RebuildList()
		elif kind == 2:
			self.openRewards[entry["rkey"]] = not entry["open"]
			self.RebuildList()
		else:
			self.SelectRecipe(entry["recipe"])

	def SelectRecipe(self, recipe):
		if recipe["key"] != self.selectedKey:
			self.selectedKey = recipe["key"]
			self.qtyEdit.SetText("1")
			self.OnSelected(recipe)
		self.SetInfo("", COLOR_NORMAL, 0)
		self.__ShowRows()
		self.ShowRecipe()

	def OnSelected(self, recipe):
		pass

	def CategoryName(self, cat):
		return str(cat)

	def CategoryOrder(self, cat):
		return 0

	# ------------------------------------------------------------------ the chosen recipe
	def Selected(self):
		for recipe in self.recipes:
			if recipe["key"] == self.selectedKey:
				return recipe
		return None

	def Quantity(self, recipe):
		# the typed number, at most what the source allows and what the bag makes (at least one)
		try:
			qty = int(self.qtyEdit.GetText())
		except ValueError:
			qty = 1
		return max(1, min(qty, self.MaxQuantity(recipe), max(1, self.CanMake(recipe))))

	def __BestAlternative(self, alternatives, quantity):
		# the first alternative the bag has enough of; with none, the one it has most of (uicubeokno.py)
		best = None
		for (vnum, count) in alternatives:
			have = self.counts.get(vnum, 0)
			need = count * quantity
			if best is None:
				best = (vnum, need, have)
				continue
			bestOk = best[2] >= best[1]
			if have >= need and not bestOk:
				best = (vnum, need, have)
			elif not bestOk and have > best[2]:
				best = (vnum, need, have)
		return best

	def BestAlternative(self, alternatives, quantity):
		return self.__BestAlternative(alternatives, quantity)

	def __PlaceItem(self, slot, vnum, count):
		if not vnum:
			slot.ClearSlot(0)
			slot.RefreshSlot()
			return
		item.SelectItem(vnum)
		sizeY = max(1, min(3, item.GetItemSize()[1]))
		slot.SetSize(32, 32 * sizeY)
		slot.SetPosition(slot.baseX, 13 + (96 - 32 * sizeY) / 2)
		slot.SetItemSlot(0, vnum, count)
		slot.RefreshSlot()

	def ShowChance(self):
		recipe = self.Selected()
		if self.recipes and not self.entries and self.searchEdit.GetText():
			self.SetInfo(TEXT_NOTHING, COLOR_BAD, 0)
			return
		if not recipe:
			self.SetInfo(self.recipes and TEXT_PICK or "", COLOR_NORMAL, 0)
			return
		if not recipe["available"]:
			self.SetInfo(recipe.get("info") or TEXT_NOT_AVAILABLE, COLOR_BAD, 0)
			return
		chance = recipe["chance"]
		bonus = self.GetImproveBonus(recipe)
		if chance and bonus > 0:
			self.SetInfo(TEXT_CHANCE_BONUS % (chance, bonus), COLOR_OK, 0)
		elif chance:
			self.SetInfo(TEXT_CHANCE % chance, COLOR_OK, 0)
		else:
			self.SetInfo("", COLOR_NORMAL, 0)

	def ShowRecipe(self):
		if not self.isLoaded:
			return
		self.shownMaterials = []
		recipe = self.Selected()
		if not recipe:
			for i in xrange(MAX_MATERIALS + 1):
				self.__PlaceItem(self.columnSlots[i], 0, 0)
			for t in self.materialTexts:
				t.SetText("")
			self.yangText.SetText("")
			self.gemText.SetText("")
			self.qtyEdit.SetText("")
			if not self.infoUntil:
				self.ShowChance()
			return
		qty = self.Quantity(recipe)
		self.__PlaceItem(self.columnSlots[0], recipe["reward"], recipe["count"] * qty)
		columns = recipe["columns"]
		for i in xrange(MAX_MATERIALS):
			if i < len(columns) and columns[i]:
				best = self.__BestAlternative(columns[i], qty)
				self.shownMaterials.append(best)
				self.__PlaceItem(self.columnSlots[i + 1], best[0], best[1])
				self.materialTexts[i].SetText("%d/%d" % (min(best[2], 999999), best[1]))
				self.materialTexts[i].SetPackedFontColor(best[2] >= best[1] and COLOR_OK or COLOR_BAD)
			else:
				self.shownMaterials.append(None)
				self.__PlaceItem(self.columnSlots[i + 1], 0, 0)
				self.materialTexts[i].SetText("")
		gold = recipe["gold"] * qty
		self.yangText.SetText(_Money(gold))
		self.yangText.SetPackedFontColor(player.GetElk() >= gold and COLOR_NORMAL or COLOR_BAD)
		gaya = recipe["gaya"] * qty
		self.gemText.SetText(str(gaya))
		self.gemText.SetPackedFontColor(self.counts.get(GAYA_VNUM, 0) >= gaya and COLOR_NORMAL or COLOR_BAD)
		if not self.qtyEdit.IsFocus():
			self.qtyEdit.SetText(str(qty))
		if not self.infoUntil:
			self.ShowChance()

	# ------------------------------------------------------------------ the quantity
	def __OnQtySub(self):
		self.qtyEdit.SetText("1")
		self.qtyEdit.KillFocus()
		self.ShowRecipe()

	def __OnQtyAdd(self):
		recipe = self.Selected()
		if not recipe:
			return
		maxQty = self.MaxQuantity(recipe)
		if maxQty <= 1:
			self.SetInfo(TEXT_QTY_ONE, COLOR_NORMAL, 3)
		self.qtyEdit.SetText(str(max(1, min(maxQty, self.CanMake(recipe)))))
		self.qtyEdit.KillFocus()
		self.ShowRecipe()

	def __OnQtyReturn(self):
		self.qtyEdit.KillFocus()
		self.ShowRecipe()

	# ------------------------------------------------------------------ the search
	def __OnSearchUpdate(self):
		ui.EditLine.OnIMEUpdate(self.searchEdit)
		self.startLine = 0
		self.RebuildList()
		self.ShowRecipe()

	def __OnSearchReturn(self):
		self.searchEdit.KillFocus()

	# ------------------------------------------------------------------ making
	def OnPressMake(self):
		recipe = self.Selected()
		if not recipe:
			chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_PICK)
			return
		if self.qtyEdit.IsFocus():
			self.qtyEdit.KillFocus()
		if not recipe["available"]:
			chat.AppendChat(chat.CHAT_TYPE_INFO, recipe.get("info") or TEXT_NOT_AVAILABLE)
			return
		self.counts = self.GetBagCounts()
		qty = self.Quantity(recipe)
		if player.GetElk() < recipe["gold"] * qty:
			chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_NO_GOLD)
			return
		if recipe["gaya"] > 0 and self.counts.get(GAYA_VNUM, 0) < recipe["gaya"] * qty:
			chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_NO_GAYA)
			return
		for alternatives in recipe["columns"]:
			if not alternatives:
				continue
			best = self.__BestAlternative(alternatives, qty)
			if best[2] < best[1]:
				chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_MISSING % _ItemName(best[0]))
				return
		self.MakeRecipe(recipe, qty)

	# ------------------------------------------------------------------ tooltips
	def __OverOut(self):
		if self.tooltipItem:
			self.tooltipItem.HideToolTip()

	def __ShowItemTip(self, vnum):
		if not self.tooltipItem or not vnum:
			return
		self.tooltipItem.ClearToolTip()
		metinSlot = [0 for i in xrange(player.METIN_SOCKET_MAX_NUM)]
		attrSlot = [(0, 0) for i in xrange(player.ATTRIBUTE_SLOT_MAX_NUM)]
		self.tooltipItem.AddItemData(vnum, metinSlot, attrSlot)

	def __OverInColumn(self, col):
		recipe = self.Selected()
		if not recipe:
			return
		if col == 0:
			self.__ShowItemTip(recipe["reward"])
			if self.tooltipItem:
				self.tooltipItem.AppendSpace(5)
				if recipe["gold"] > 0:
					self.tooltipItem.AppendTextLine(TEXT_COST % _Money(recipe["gold"]), COLOR_GOLD)
				if recipe["gaya"] > 0:
					self.tooltipItem.AppendTextLine(TEXT_GAYA % recipe["gaya"], COLOR_GAYA)
				if recipe["chance"]:
					self.tooltipItem.AppendTextLine(TEXT_CHANCE % recipe["chance"], COLOR_OK)
				self.tooltipItem.AppendTextLine(TEXT_QTY)
				self.tooltipItem.ResizeToolTip()
			return
		columns = recipe["columns"]
		index = col - 1
		if index >= len(columns) or not columns[index] or index >= len(self.shownMaterials) or not self.shownMaterials[index]:
			return
		self.__ShowItemTip(self.shownMaterials[index][0])
		if self.tooltipItem and len(columns[index]) > 1:	# a merged row's +5..+9: any of them
			self.tooltipItem.AppendSpace(5)
			first = True
			for (vnum, count) in columns[index]:
				if not first:
					self.tooltipItem.AppendTextLine(TEXT_OR)
				first = False
				self.tooltipItem.AppendTextLine(_ItemName(vnum), self.counts.get(vnum, 0) >= count and COLOR_OK or COLOR_BAD)
			self.tooltipItem.ResizeToolTip()

	def __OverInImprove(self, slotIndex = 0):
		self.ShowImproveTip()

	def ShowImproveTip(self):
		if not self.tooltipItem:
			return
		vnum = self.ImproveVnum()
		if vnum:
			self.__ShowItemTip(vnum)
			self.tooltipItem.AppendTextLine(TEXT_CLICK_REMOVE)
			self.tooltipItem.ResizeToolTip()
			return
		self.tooltipItem.ClearToolTip()
		self.tooltipItem.AppendTextLine(TEXT_IMPROVE_TITLE)
		self.tooltipItem.AppendTextLine(self.HAS_IMPROVE and TEXT_IMPROVE_HINT or TEXT_IMPROVE_NONE)
		self.tooltipItem.ResizeToolTip()
		self.tooltipItem.ShowToolTip()

	def HideTip(self):
		self.__OverOut()

	def ImproveVnum(self):
		return 0

	def __OnImproveDrop(self, slotIndex = 0):
		self.OnImproveDrop()

	def __OnImproveClick(self, slotIndex = 0):
		self.OnImproveClick()

	def OnImproveDrop(self):
		if mouseModule.mouseController.isAttached():
			mouseModule.mouseController.DeattachObject()

	def OnImproveClick(self):
		self.OnImproveDrop()


class CubeRenewalWindow(_RenewalBase):
	HAS_IMPROVE = True
	HAS_GAYA = True

	def __init__(self):
		_RenewalBase.__init__(self)
		self.npcVnum = 0
		self.isUsable = False
		self.cubeResultInfos = []
		self.cubeMaterialInfos = {}
		self.cubeResultExtra = {}
		self.placed = []
		self.improvePos = -1
		self.improveVnum = 0
		self.improveBonus = 0
		self.improveCategory = -1
		self.batchLeft = 0
		self.batchTotal = 0
		self.batchOk = 0
		self.batchUntil = 0.0
		self.setValue = 0		# MT2009_PLUS_CUBE_RENEWAL_V2: a set blacksmith's set (1-5), 0 at every other NPC
		self.setBagPieces = ()	# the pieces of the bag the list does not have (an item newer than cube_setsmith_data)
		self.setHeld = {}		# vnum -> pieces in the bag, with this blacksmith's set or not

	def __del__(self):
		_RenewalBase.__del__(self)

	# ------------------------------------------------------------------ the interface of uicubeokno.CubeOknoWindow
	def Open(self, npcVnum = 0):
		self.npcVnum = int(npcVnum)
		self.setValue = SET_SMITHS.get(self.npcVnum, 0)
		self.setBagPieces = ()
		self.setHeld = {}
		self.defaultOpen = not self.setValue	# global: the three set categories closed
		self.cubeResultInfos = []
		self.cubeMaterialInfos = {}
		self.cubeResultExtra = {}
		self.recipes = []
		self.placed = []
		self.__ClearImprove()
		self.__EndBatch(False)
		title = TEXT_TITLE
		try:
			import nonplayer
			name = nonplayer.GetMonsterName(self.npcVnum)
			if name:
				title = "%s - %s" % (TEXT_TITLE, name)
		except Exception:
			pass
		if self.setValue:
			title = TEXT_SET_TITLE
		self._OpenCommon(title)
		self.okButton.SetText(self.setValue and TEXT_SET_OK or TEXT_MAKE)
		self.cancelButton.SetText(self.setValue and TEXT_SET_CANCEL or TEXT_CLOSE)
		self.improveText.SetText(self.setValue and TEXT_SET_IMPROVE or TEXT_IMPROVE)
		self.isUsable = True

	def Close(self):
		self.isUsable = False
		self.CloseWindow()
		self.cubeResultInfos = []
		self.cubeMaterialInfos = {}
		self.cubeResultExtra = {}
		self.recipes = []
		self.selectedKey = None
		self.placed = []
		self.__ClearImprove()
		self.__EndBatch(False)

	def SendClose(self):
		if self.isUsable:
			self.isUsable = False
			net.SendChatPacket("/cube close")
		self.cubeResultInfos = []
		self.recipes = []
		self.selectedKey = None
		self.placed = []
		self.__ClearImprove()
		self.__EndBatch(False)

	def AddCubeResultItem(self, itemVnum, count):
		self.cubeResultInfos.append((itemVnum, count))
		self.__Dirty()

	def AddMaterialInfo(self, itemIndex, orderIndex, itemVnum, itemCount):
		columns = self.cubeMaterialInfos.setdefault(itemIndex, [])
		while len(columns) <= orderIndex:
			columns.append([])
		columns[orderIndex].append((itemVnum, itemCount))
		self.__Dirty()

	def SetResultExtra(self, itemIndex, gold, chance, gaya, category = -1):
		self.cubeResultExtra[itemIndex] = (gold, chance, gaya, category)
		self.__Dirty()

	def SetImproveInfo(self, vnum, bonus, category):
		self.improveVnum = vnum
		self.improveBonus = bonus
		self.improveCategory = category
		if not vnum:
			self.improvePos = -1
		self.__ShowImprove()
		self.listDirty = True

	def ClearCubeResultItem(self):
		self.cubeResultInfos = []
		self.__Dirty()

	def UpdateInfo(self, gold, itemVnum, count):
		pass	# the server's "cube info": the window shows the chosen recipe's own Yang

	def Clear(self):
		self.Refresh()

	def Refresh(self):
		self.__Dirty()

	def OnCubeResult(self, success, itemVnum = 0, count = 0):
		if self.batchLeft > 0:
			self.batchLeft -= 1
			if success:
				self.batchOk += 1
			self.batchUntil = app.GetTime() + BATCH_TIMEOUT
			if self.batchLeft <= 0:
				self.__EndBatch(True)
		elif success:
			self.SetInfo(TEXT_SUCCESS % _ItemName(itemVnum), COLOR_OK, 4)
		else:
			self.SetInfo(TEXT_FAIL, COLOR_BAD, 4)
		self.__ShowImprove()
		self.listDirty = True

	# ------------------------------------------------------------------ the rows from the server's lists
	def __Dirty(self):
		self.recipes = []
		if self.setValue:
			self.recipes = self.__SetRecipes()
			self.listDirty = True
			return
		for i in xrange(len(self.cubeResultInfos)):
			(vnum, count) = self.cubeResultInfos[i]
			(gold, chance, gaya, category) = self.cubeResultExtra.get(i, (0, "", 0, -1))
			if category not in CUBE_CATEGORY_NAMES:
				category = CUBE_CATEGORY_OTHER
			self.recipes.append({
				"key" : i, "reward" : vnum, "count" : max(1, count), "columns" : self.cubeMaterialInfos.get(i, []),
				"gold" : max(0, int(gold)), "chance" : chance, "gaya" : max(0, int(gaya)), "category" : category,
				"realCategory" : self.cubeResultExtra.get(i, (0, "", 0, -1))[3], "available" : True,
			})
		self.listDirty = True

	# ------------------------------------------------------------------ MT2009_PLUS_CUBE_RENEWAL_V2: the set blacksmiths
	# Why V1 left them on uicube.py: a set recipe makes no new item - it puts the set (yextra, server-patches/ysets
	# Mt2009YSetsCubeMake) on the piece itself, which stays in place with its stones and bonuses (nothing to copy, unlike
	# copy_attr's new item) and stays on a failure. Its row (cube.cpp Mt2009YSetsCubeMaterialInfo) is one a part with a
	# sample +7 piece of the player's class as the result and the first material, the Gaya as a material - V1's window
	# would have put exactly that sample vnum into the cube, so any other piece (or the +8/+9) could not be used.
	# Here: the server's three rows give each part's materials, Yang, chance, Gaya and category; the list is every piece
	# of that part (cube_setsmith_data + the bag's) grouped by its base item, +7/+8/+9... below it with "[n]" - the
	# pieces of the bag without this set. Making puts the chosen piece's own cell first, then the materials, "/cube pick
	# 0" (the server's set recipe is found by the piece's part, FN_find_cube) and one "/cube make".
	def __SetServerRows(self):
		rows = {}
		for i in xrange(len(self.cubeResultInfos)):
			(sample, count) = self.cubeResultInfos[i]
			(gold, chance, gaya, category) = self.cubeResultExtra.get(i, (0, "", 0, -1))
			part = 0
			for (p, cat) in SET_PART_CATEGORY.items():
				if cat == category:
					part = p
			if not part:
				info = _SetPieceInfo(sample)
				part = info and info[0] or 0
			if not part or part in rows:
				continue
			gaya = max(0, int(gaya))
			materials = []
			for alternatives in self.cubeMaterialInfos.get(i, []):
				if not alternatives:
					continue
				if len(alternatives) == 1 and alternatives[0][0] == sample:
					continue	# the server's sample piece - the chosen piece takes its place
				if len(alternatives) == 1 and alternatives[0][0] == GAYA_VNUM:
					gaya += alternatives[0][1]	# a material on the server's row, the Gaya field here
					continue
				materials.append(alternatives)
			rows[part] = (max(0, int(gold)), chance, gaya, SET_PART_CATEGORY[part], materials)
		return rows

	def __SetRecipes(self):
		rows = self.__SetServerRows()
		listed = _SetListedPieces()
		prefix = _SetPrefix(self.setValue)
		recipes = []
		for part in (1, 2, 3):
			if part not in rows:
				continue
			(gold, chance, gaya, category, materials) = rows[part]
			vnums = list(listed.get(part, ()))
			for vnum in self.setBagPieces:
				if vnum not in vnums:
					vnums.append(vnum)
			groups = {}
			for vnum in vnums:
				info = _SetPieceInfo(vnum)
				if not info or info[0] != part:
					continue
				(p, base, baseName, refine, level) = info
				groups.setdefault(base, []).append((refine, vnum, baseName, level))
			order = []
			for (base, pieces) in groups.items():
				pieces.sort()
				order.append((min([x[3] for x in pieces]), base))
			order.sort()
			for (level, base) in order:
				baseName = groups[base][0][2]
				groupText = prefix and "%s %s" % (prefix, baseName) or baseName
				for (refine, vnum, name, lvl) in groups[base]:
					recipes.append({
						"key" : ("set", vnum), "reward" : vnum, "count" : 1, "columns" : [[(vnum, 1)]] + materials,
						"gold" : gold, "chance" : chance, "gaya" : gaya, "category" : category, "realCategory" : category,
						"available" : True, "group" : ("set", base), "groupText" : groupText, "alwaysGroup" : True,
						"label" : "%s +%d" % (groupText, refine), "setPiece" : True,
					})
		return recipes

	def __SetCounts(self, counts):
		# a piece counts when it lies in the bag (not worn) without this blacksmith's set - the server refuses the others
		held = {}
		usable = {}
		extra = []
		listed = _SetListedPieces()
		for cell in xrange(player.INVENTORY_SLOT_COUNT):
			vnum = player.GetItemIndex(cell)
			if not vnum or not _SetPieceInfo(vnum):
				continue
			held[vnum] = held.get(vnum, 0) + 1
			if _SetOf(cell) != self.setValue:
				usable[vnum] = usable.get(vnum, 0) + 1
			if vnum not in listed.get(_SetPieceInfo(vnum)[0], ()) and vnum not in extra:
				extra.append(vnum)
		for vnum in held.keys():
			counts[vnum] = usable.get(vnum, 0)
		self.setHeld = held
		extra = tuple(sorted(extra))
		if extra != tuple(sorted(self.setBagPieces)):
			self.setBagPieces = extra
			self.recipes = self.__SetRecipes()
		return counts

	def __SetGearCell(self, vnum):
		for cell in xrange(player.INVENTORY_SLOT_COUNT):
			if player.GetItemIndex(cell) == vnum and _SetOf(cell) != self.setValue:
				return cell
		return -1

	def GroupCount(self, recipes):
		if self.setValue:
			return sum([self.counts.get(r["reward"], 0) for r in recipes])
		return _RenewalBase.GroupCount(self, recipes)

	def RecipeCount(self, recipe):
		if self.setValue:
			return self.counts.get(recipe["reward"], 0)
		return _RenewalBase.RecipeCount(self, recipe)

	def OnPressMake(self):
		recipe = self.Selected()
		if self.setValue and recipe:
			self.counts = self.GetBagCounts()
			if self.setHeld.get(recipe["reward"], 0) > 0 and self.counts.get(recipe["reward"], 0) <= 0:
				chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_SET_HAS)
				return
		_RenewalBase.OnPressMake(self)

	def CategoryName(self, cat):
		if self.setValue and cat in SET_CATEGORY_NAMES:
			return SET_CATEGORY_NAMES[cat]
		return CUBE_CATEGORY_NAMES.get(cat, CUBE_CATEGORY_NAMES[CUBE_CATEGORY_OTHER])

	def CategoryOrder(self, cat):
		if cat in CUBE_CATEGORY_ORDER:
			return CUBE_CATEGORY_ORDER.index(cat)
		return len(CUBE_CATEGORY_ORDER)

	def GetBagCounts(self):
		if self.setValue:
			return self.__SetCounts(_BagCountsCube())
		return _BagCountsCube()

	def GetImproveBonus(self, recipe):
		cat = recipe.get("realCategory", -1)
		if self.improveVnum and self.improveBonus > 0 and self.improveCategory == cat and cat >= 0:
			return self.improveBonus
		return 0

	def MaxQuantity(self, recipe):
		if not recipe.get("setPiece") and _IsStackable(recipe["reward"]):
			return CUBE_MAX_QUANTITY
		return 1

	def OnSelected(self, recipe):
		# a set row: "pick 0" - the server finds the set recipe by the piece's part (its reward is the Projekt)
		net.SendChatPacket("/cube pick %d" % (not recipe.get("setPiece") and recipe["reward"] or 0))

	def OnUpdate(self):
		_RenewalBase.OnUpdate(self)
		if self.batchLeft > 0 and app.GetTime() >= self.batchUntil:
			self.__EndBatch(True)	# the server made fewer (the materials, Yang or the bag ran out) - it said why

	def MakeRecipe(self, recipe, quantity):
		plan = []
		used = {}
		columns = recipe["columns"]
		if recipe.get("setPiece"):
			# the chosen piece itself - its own cell (one without this set), the first item of the server's window
			quantity = 1
			cell = self.__SetGearCell(recipe["reward"])
			if cell < 0:
				chat.AppendChat(chat.CHAT_TYPE_INFO, self.setHeld.get(recipe["reward"], 0) and TEXT_SET_HAS or TEXT_MISSING % _ItemName(recipe["reward"]))
				return
			used[cell] = True
			plan.append(cell)
			columns = columns[1:]
		for alternatives in columns:
			if not alternatives:
				continue
			best = self.BestAlternative(alternatives, quantity)
			need = best[1]
			for pos in uiCube._CubePositions():
				if need <= 0:
					break
				if pos in used or uiCube._ItemIndex(pos) != best[0]:
					continue
				used[pos] = True
				plan.append(pos)
				need -= uiCube._ItemCount(pos)
		if len(plan) > CUBE_SLOT_MAX:
			chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_TOO_MANY)
			return
		for slot in self.placed:	# what an earlier attempt left in the server's window
			net.SendChatPacket("/cube del %d" % slot)
		self.placed = []
		for slot in xrange(len(plan)):
			uiCube._CubeAdd(slot, plan[slot])
			self.placed.append(slot)
		self.SetInfo("", COLOR_NORMAL, 0)
		net.SendChatPacket("/cube pick %d" % (not recipe.get("setPiece") and recipe["reward"] or 0))
		if quantity > 1:
			self.batchTotal = quantity
			self.batchLeft = quantity
			self.batchOk = 0
			self.batchUntil = app.GetTime() + BATCH_TIMEOUT
		for i in xrange(quantity):
			net.SendChatPacket("/cube make")

	def __EndBatch(self, report):
		if report and self.batchTotal > 0:
			done = self.batchTotal - max(0, self.batchLeft)
			self.SetInfo(TEXT_BATCH % (self.batchOk, done), self.batchOk > 0 and COLOR_OK or COLOR_BAD, 5)
			chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_BATCH % (self.batchOk, done))
		self.batchLeft = 0
		self.batchTotal = 0
		self.batchOk = 0
		self.batchUntil = 0.0

	# ------------------------------------------------------------------ the chance-raising slot
	def ImproveVnum(self):
		return self.improveVnum

	def __ClearImprove(self):
		self.improvePos = -1
		self.improveVnum = 0
		self.improveBonus = 0
		self.improveCategory = -1
		if self.isLoaded:
			self.__ShowImprove()

	def __ShowImprove(self):
		if not self.isLoaded:
			return
		if self.improvePos >= 0 and self.improveVnum and player.GetItemIndex(self.improvePos) == self.improveVnum:
			self.improveSlot.SetItemSlot(0, self.improveVnum, player.GetItemCount(self.improvePos))
		else:
			if self.improveVnum and self.improvePos >= 0:	# used up or moved
				self.improvePos = -1
				self.improveVnum = 0
				self.improveBonus = 0
				self.listDirty = True
			self.improveSlot.ClearSlot(0)
		self.improveSlot.RefreshSlot()

	def OnImproveDrop(self):
		if not mouseModule.mouseController.isAttached():
			return
		attachedType = mouseModule.mouseController.GetAttachedType()
		attachedPos = mouseModule.mouseController.GetAttachedSlotNumber()
		mouseModule.mouseController.DeattachObject()
		if player.SLOT_TYPE_INVENTORY != attachedType:
			return
		self.improvePos = attachedPos
		self.improveVnum = 0
		net.SendChatPacket("/cube improve %d" % attachedPos)

	def OnImproveClick(self):
		if mouseModule.mouseController.isAttached():
			self.OnImproveDrop()
			return
		self.__ClearImprove()
		net.SendChatPacket("/cube improve -1")
		self.listDirty = True


class CraftingRenewalWindow(_RenewalBase):
	HAS_IMPROVE = False
	HAS_GAYA = False

	def __init__(self):
		_RenewalBase.__init__(self)
		self.current_crafting_vnum = 0
		self.categoryData = {}

	def __del__(self):
		_RenewalBase.__del__(self)

	# ------------------------------------------------------------------ the interface of uicraft.CraftingWindow
	def Open(self):
		try:
			import uiCraft
			byVnum = uiCraft.CRAFTING_CATEGORIES_BY_VNUM
			self.categoryData = byVnum.get(self.current_crafting_vnum, byVnum["default"])
		except Exception:
			self.categoryData = {0 : {"name" : CUBE_CATEGORY_NAMES[CUBE_CATEGORY_OTHER]}}
		self._OpenCommon(TEXT_TITLE)
		self.__Load()

	def Close(self):
		self.OnPressCancel()

	def SendClose(self):
		if self.IsShow():
			net.SendChatPacket("/craft close")
		try:
			constInfo.CRAFTING_LOAD_DATA.pop(self.current_crafting_vnum, None)
		except Exception:
			pass

	def OnCraftUpdate(self):
		self.__Load()
		if self.current_crafting_vnum == 102:
			snd.PlaySound("sound/ui/%s.wav" % ("brewing", "brewing2")[app.GetRandom(0, 1)])
		else:
			snd.PlaySound("sound/ui/craft.wav")

	def UpdateAllListItem(self):
		self.__Load()

	# ------------------------------------------------------------------ the rows from constInfo.CRAFTING_DATA
	def __CategoryOf(self, key, data):
		for cat in sorted(self.categoryData.keys()):
			value = self.categoryData[cat]
			flt = value.get("filters")
			if not flt:
				return cat
			item.SelectItem(data["item_vnum"])
			if flt.has_key("item_type") and flt["item_type"] != item.GetItemType():
				continue
			if flt.has_key("item_subtype") and flt["item_subtype"] != item.GetItemSubType():
				continue
			if flt.has_key("antiflag") and not item.IsAntiFlag(flt["antiflag"]):
				continue
			if flt.has_key("item_value") and item.GetValue(flt["item_value"][0]) != flt["item_value"][1]:
				continue
			if flt.has_key("item_vnum") and data["item_vnum"] not in flt["item_vnum"]:
				continue
			if flt.has_key("craft_vnum") and key not in flt["craft_vnum"]:
				continue
			return cat
		return max(self.categoryData.keys() or [0])

	def __Load(self):
		self.recipes = []
		try:
			allData = constInfo.CRAFTING_DATA.get(self.current_crafting_vnum, {})
		except Exception:
			allData = {}
		for key in sorted(allData.keys()):
			data = allData[key]
			if not data.has_key("item_vnum"):
				continue
			columns = []
			recipe = data.get("recipe", ())
			for i in xrange(0, len(recipe) - 1, 2):
				vnums = recipe[i]
				if not isinstance(vnums, tuple):
					vnums = (vnums, )
				for vnum in vnums:	# crafting.lua takes every vnum of a group
					columns.append([(int(vnum), int(recipe[i + 1]))])
			available = bool(data.get("is_available", 1))
			info = ""
			if not available:
				req = data.get("requirements", {})
				if req.get("min_level", 0) > player.GetStatus(player.LEVEL):
					info = TEXT_REQ_LEVEL % req["min_level"]
				elif req.has_key("recipe_progress"):
					info = TEXT_REQ_RECIPE % tuple(req["recipe_progress"])
				else:
					info = TEXT_NOT_AVAILABLE
			self.recipes.append({
				"key" : key, "reward" : data["item_vnum"], "count" : max(1, data.get("count", 1)), "columns" : columns,
				"gold" : max(0, int(data.get("price", 0))), "chance" : str(data.get("chance", 100)), "gaya" : 0,
				"category" : self.__CategoryOf(key, data), "available" : available, "info" : info,
				"color" : (not available) and COLOR_BAD or None,
			})
		self.listDirty = True

	def CategoryName(self, cat):
		return self.categoryData.get(cat, {}).get("name", "")

	def CategoryOrder(self, cat):
		return cat

	def GetBagCounts(self):
		return _BagCountsCraft()

	def MaxQuantity(self, recipe):
		item.SelectItem(recipe["reward"])
		if item.GetItemSize()[1] > 1 or not _IsStackable(recipe["reward"]):
			return 1	# crafting.lua makes these one at a time
		return CRAFT_MAX_QUANTITY

	def MakeRecipe(self, recipe, quantity):
		self.SetInfo("", COLOR_NORMAL, 0)
		net.SendChatPacket("/craft create %d %d" % (recipe["key"], quantity))
