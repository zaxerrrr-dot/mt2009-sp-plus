# MT2009_PLUS_EKWIPUNEK_V1 - Dodatkowy ekwipunek: Ameria Project's special storage
# (root/uispecialstorage.py, uispecialinventory.py), ported for Yohara 3.0 (the
# owner, 21 October 2026: "Dodaj okno dodatkowego ekwipunku z Amerii, z
# automatycznym wpadaniem przedmiotow do danych kategorii").
#
# Five storages of four pages 5 x 9, the server's item windows 11-15
# (server-patches/ekwipunek, playerbot_ekwipunek.cpp): Materialy ulepszen,
# Ksiegi, Kamienie Duszy, Zaczarowania, Skrzynie. The server puts there what a
# player picks up or gets of each kind; the window (Shift+I, the inventory's
# side bar) shows them, and:
#   - drag in from the bag (only the kind of the open tab), from the safebox
#     or the item mall; drag out into the bag (an empty cell, the same item's
#     stack, a soul stone onto the piece it goes into - with a question -, an
#     enchantment onto the piece it changes);
#   - right click / double click uses (a book is read, a chest opened);
#     Ctrl + right click on a stack of chests opens the whole stack, as in the
#     bag;
#   - Shift + click splits a stack; the shop's sell cursor sells (asks first);
#   - the trade window and the crafting window take its items too
#     (uiexchange.py, uicube.py);
#   - "Sortuj": the stacks joined and the items ordered by kind (Ameria's two
#     buttons, "/ekwipunek sortuj").
#
# MT2009_PLUS_EKWIPUNEK_REFINE_V1 (the owner, 21 October 2026: "jak ulepszacz
# jest w dodatkowym EQ, to mozna ulepszac"): the refine scrolls (USE_TUNING)
# go with the materials; a scroll dragged from here onto an item of the bag or
# of a storage opens the refine window, an item of a storage dragged onto the
# blacksmith is refined in its cell. The server tells which window the refine
# window is for ("ekwipunek_refine <window>", OnRefineWindow), uirefine.py
# shows that item and counts the materials here too (CountInStorages).
# MT2009_PLUS_EKWIPUNEK_MOVE_V1: "Przenies do extra EQ", the third choice of
# the inventory's sort button (inventoryarrange.py, RequestMoveFromBag).
#
# The windows need the 3.0 exe (client-patches/exe, ENABLE_SPECIAL_STORAGE:
# player.UPGRADE_INVENTORY ...). With an older exe this module does nothing and
# never says hello, so the server keeps every item in the bag.
#
# Python 2.7 as the client has it; the Polish letters are CP1250 escapes.

import app
import chat
import item
import mouseModule
import net
import player
import snd
import ui
import uiCommon
import uiToolTip
import wndMgr

TEXT_TITLE = "Dodatkowy ekwipunek"
TEXT_SORT = "Sortuj"
TEXT_SORT_TIP = "Po\xb3\xb9cz stosy i posortuj t\xea kategori\xea"
TEXT_SORT_ASK = "Po\xb3\xb9czy\xe6 stosy i posortowa\xe6 kategori\xea \"%s\"?"
TEXT_NEEDS_EXE = "Dodatkowy ekwipunek wymaga nowego klienta (exe 3.0)."
TEXT_WRONG_KIND = "Ten przedmiot nie pasuje do kategorii \"%s\"."
TEXT_ATTACH_ASK = "W\xb3o\xbfy\xe6 %s do przedmiotu?"
TEXT_OPEN_START = "Otwieranie skrzynek: %d szt."
TEXT_OPEN_DONE = "Otwarto skrzynek: %d."
TEXT_OPEN_STOP = "Otwieranie przerwane, otwarto skrzynek: %d."
TEXT_HINT = "PPM: u\xbfyj  |  Shift+klik: podziel  |  przeci\xb9gnij do ekwipunku"

# (window constant, slot type constant, name, icon) in the tabs' order.
CATEGORY_DEFS = (
	("UPGRADE_INVENTORY", "SLOT_TYPE_UPGRADE_INVENTORY", "Materia\xb3y ulepsze\xf1", "upgrade"),
	("BOOK_INVENTORY", "SLOT_TYPE_BOOK_INVENTORY", "Ksi\xeagi", "book"),
	("STONE_INVENTORY", "SLOT_TYPE_STONE_INVENTORY", "Kamienie Duszy", "stone"),
	("CHANGE_INVENTORY", "SLOT_TYPE_CHANGE_INVENTORY", "Zaczarowania", "bonus"),
	("CHEST_INVENTORY", "SLOT_TYPE_CHEST_INVENTORY", "Skrzynie", "chest"),
)

ICON_IMAGE = "mt2009_ui/ekwipunek/btn_%s_%d.png"
SLOT_BASE_IMAGE = "d:/ymir work/ui/public/slot_base.sub"
TAB_IMAGE = "d:/ymir work/ui/game/windows/tab_button_large_half_%02d.sub"
BUTTON_IMAGE = "d:/ymir work/ui/public/middle_button_%02d.sub"
PAGE_NAMES = ("I", "II", "III", "IV")

COLUMNS = 5
ROWS = 9
CELL = 32

# Ameria's own vnums of each kind (playerbot_ekwipunek.cpp, Mt2009EkwCategoryOf).
EXTRA_VNUMS = {
	27987: "UPGRADE_INVENTORY", 27799: "UPGRADE_INVENTORY", 70031: "UPGRADE_INVENTORY",
	27992: "UPGRADE_INVENTORY", 27993: "UPGRADE_INVENTORY", 27994: "UPGRADE_INVENTORY",
	50301: "BOOK_INVENTORY", 50302: "BOOK_INVENTORY", 50303: "BOOK_INVENTORY",
	72346: "CHANGE_INVENTORY",
}

_state = {
	'window': None,
	'icon': 0,
	'server': False,
	'categories': None,
	'refineWindow': None,
}


def IsSupported():
	return hasattr(player, "UPGRADE_INVENTORY") and hasattr(player, "SLOT_TYPE_UPGRADE_INVENTORY")


def Categories():
	"""[(window, slotType, name, icon)] - empty with an old exe."""
	cats = _state['categories']
	if cats is None:
		cats = []
		if IsSupported():
			for win, slot, name, icon in CATEGORY_DEFS:
				cats.append((getattr(player, win), getattr(player, slot), name, icon))
		_state['categories'] = cats
	return cats


def IsEkwSlotType(slotType):
	for win, slot, name, icon in Categories():
		if slot == slotType:
			return True
	return False


def WindowOfSlotType(slotType):
	for win, slot, name, icon in Categories():
		if slot == slotType:
			return win
	return -1


def NameOfWindow(window):
	for win, slot, name, icon in Categories():
		if win == window:
			return name
	return ""


def CategoryOf(vnum):
	"""The storage window an item kind belongs in (the server's rule), 0 for none."""
	if not vnum or not IsSupported():
		return 0
	if vnum in EXTRA_VNUMS:
		return getattr(player, EXTRA_VNUMS[vnum])
	item.SelectItem(vnum)
	itemType = item.GetItemType()
	subType = item.GetItemSubType()
	if itemType == getattr(item, "ITEM_TYPE_MATERIAL", -1) and subType == 0:
		return player.UPGRADE_INVENTORY
	# MT2009_PLUS_EKWIPUNEK_REFINE_V1: the refine scrolls with the materials (the server's rule)
	if item.IsRefineScroll(vnum):
		return player.UPGRADE_INVENTORY
	if itemType == getattr(item, "ITEM_TYPE_SKILLBOOK", -1):
		return player.BOOK_INVENTORY
	if itemType == getattr(item, "ITEM_TYPE_METIN", -1) and subType == getattr(item, "METIN_NORMAL", 0):
		return player.STONE_INVENTORY
	if itemType == getattr(item, "ITEM_TYPE_USE", -1) and item.GetUseType(vnum) == "USE_CHANGE_ATTRIBUTE":
		return player.CHANGE_INVENTORY
	if itemType == getattr(item, "ITEM_TYPE_GIFTBOX", -1):
		return player.CHEST_INVENTORY
	return 0


# ---------------------------------------------------------------- the cursor

def _Controller():
	return getattr(mouseModule, 'mouseController', None)


def AttachItem(owner, slotType, pos, vnum, count):
	"""Puts a storage's item on the cursor. mouseModule.AttachObject finds the
	icon only for the stock slot types, so it is handed over first (as
	uisidekickinventory.py does) and wndMgr told the real size after."""
	controller = _Controller()
	if not controller or controller.isAttached():
		return False
	ReleaseIcon()
	item.SelectItem(vnum)
	handle = item.GetIconInstance()
	if not handle:
		return False
	(width, height) = item.GetItemSize()
	controller.AttachedIconHandle = handle
	controller.AttachObject(owner, slotType, pos, vnum, count)
	if controller.isAttached() and controller.GetAttachedType() == slotType and controller.AttachedIconHandle == handle:
		_state['icon'] = handle
		wndMgr.AttachIcon(slotType, vnum, pos, width, height)
		return True
	if controller.isAttached() and controller.GetAttachedType() == slotType:
		controller.DeattachObject()
	if controller.AttachedIconHandle == handle:
		controller.AttachedIconHandle = 0
	item.DeleteIconInstance(handle)
	return False


def ReleaseIcon(force=False):
	"""Deletes the icon this module gave the cursor once the cursor let go of it
	(the stock DeattachObject deletes the stock types' icons only)."""
	handle = _state['icon']
	if not handle:
		return
	controller = _Controller()
	held = bool(controller) and controller.isAttached() and getattr(controller, 'AttachedIconHandle', 0) == handle
	if held:
		if not force:
			return
		controller.DeattachObject()
	item.DeleteIconInstance(handle)
	_state['icon'] = 0


def Deattach():
	controller = _Controller()
	if controller and controller.isAttached():
		controller.DeattachObject()
	ReleaseIcon()


# ---------------------------------------------------------------- the hooks of the other windows

def DropIntoPlayerBag(attachedType, attachedPos, cell):
	"""uiinventory.py's SelectEmptySlot: a storage's item dropped on an empty
	cell of the bag. True when it was one (the move went)."""
	if not IsEkwSlotType(attachedType):
		return False
	window = WindowOfSlotType(attachedType)
	controller = _Controller()
	count = controller.GetAttachedItemCount() if controller else 0
	net.SendItemMovePacket(window, attachedPos, player.INVENTORY, cell, count)
	Deattach()
	return True


def DropOnPlayerItem(attachedType, attachedPos, cell):
	"""uiinventory.py's SelectItemSlot: a storage's item dropped on an item of
	the bag - the same item's stack takes it, a soul stone goes into the piece
	(after a question), an enchantment or another item used on items works on
	it. True when it was a storage's item."""
	if not IsEkwSlotType(attachedType):
		return False
	window = WindowOfSlotType(attachedType)
	srcVnum = player.GetItemIndex(window, attachedPos)
	dstVnum = player.GetItemIndex(cell)
	controller = _Controller()
	count = controller.GetAttachedItemCount() if controller else 0
	Deattach()
	if not srcVnum or not dstVnum:
		return True
	if srcVnum == dstVnum:
		net.SendItemMovePacket(window, attachedPos, player.INVENTORY, cell, count)
		return True
	if player.IsEquipmentSlot(cell):
		return True
	# MT2009_PLUS_EKWIPUNEK_REFINE_V1: a refine scroll from the materials' storage
	# opens the refine window for the item (the server takes the scroll from here)
	if item.IsRefineScroll(srcVnum):
		if player.REFINE_OK == player.CanRefine(srcVnum, cell):
			net.SendItemUseToItemPacket(window, attachedPos, player.INVENTORY, cell)
		return True
	if window == player.STONE_INVENTORY and item.IsMetin(srcVnum):
		_AskAttachMetin(window, attachedPos, cell, srcVnum)
		return True
	if window == player.CHANGE_INVENTORY:
		net.SendItemUseToItemPacket(window, attachedPos, player.INVENTORY, cell)
		return True
	ITEM_FLAG_APPLICABLE = 1 << 14
	if (player.GetItemFlags(window, attachedPos) & ITEM_FLAG_APPLICABLE) == ITEM_FLAG_APPLICABLE:
		net.SendItemUseToItemPacket(window, attachedPos, player.INVENTORY, cell)
	return True


def _AskAttachMetin(window, pos, cell, vnum):
	item.SelectItem(vnum)
	dialog = uiCommon.QuestionDialog()
	dialog.SetText(TEXT_ATTACH_ASK % item.GetItemName())

	def Accept(dialog=dialog):
		net.SendItemUseToItemPacket(window, pos, player.INVENTORY, cell)
		dialog.Close()
		_state['dialog'] = None

	def Cancel(dialog=dialog):
		dialog.Close()
		_state['dialog'] = None

	dialog.SetAcceptEvent(Accept)
	dialog.SetCancelEvent(Cancel)
	dialog.Open()
	_state['dialog'] = dialog


def GiveToCharacter(attachedType, attachedPos, count, dstChrID):
	"""game.py, a storage's item let go over a character: an NPC gets it (the
	blacksmith refines a soul stone where it lies - the server reads the
	window). True when it was a storage's item."""
	if not IsEkwSlotType(attachedType):
		return False
	import chr
	if dstChrID and chr.HasInstance(dstChrID) and player.GetMainCharacterIndex() != dstChrID and chr.IsNPC(dstChrID):
		net.SendGiveItemPacket(dstChrID, WindowOfSlotType(attachedType), attachedPos, count)
	return True


def OnRefineWindow(window="0", *args):
	"""game.py, "ekwipunek_refine <window>": the window of the item the refine
	packet right after it is for."""
	try:
		_state['refineWindow'] = int(window)
	except (TypeError, ValueError):
		_state['refineWindow'] = None


def TakeRefineWindow():
	"""uirefine.py, opening the refine window: the window its cell is in (and
	forgotten - every refine packet of a client with the storages has its own
	command before it)."""
	window = _state['refineWindow']
	_state['refineWindow'] = None
	if window is None or not IsSupported() or window == player.INVENTORY:
		return player.INVENTORY
	for win, slot, name, icon in Categories():
		if win == window:
			return window
	return player.INVENTORY


def CountInStorages(vnum):
	"""How many of an item the storages hold (the refine window's materials)."""
	count = 0
	if not vnum or not IsSupported():
		return 0
	for win, slot, name, icon in Categories():
		for pos in xrange(COLUMNS * ROWS * len(PAGE_NAMES)):
			if player.GetItemIndex(win, pos) == vnum:
				count += player.GetItemCount(win, pos)
	return count


def RequestMoveFromBag():
	"""inventoryarrange.py's third choice: every item of the bag that belongs
	to a category into its storage (the server joins the stacks first and
	leaves worn, locked, traded and sort-locked items where they are)."""
	if not IsSupported():
		chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_NEEDS_EXE)
		return False
	words = ["/ekwipunek", "przenies"]
	try:
		import inventorysortlock
		keep = inventorysortlock.KeepArgument()
	except Exception:
		keep = ""
	if keep:
		words.append(keep)
	net.SendChatPacket(" ".join(words))
	return True


def CubeItemOf(attachedType, attachedPos):
	"""uicube.py: (window, cell) of a storage's item on the cursor, or None."""
	if not IsEkwSlotType(attachedType):
		return None
	return (WindowOfSlotType(attachedType), attachedPos)


# ---------------------------------------------------------------- opening a stack of chests

class OpenAllRunner(ui.Window):
	"""Ctrl + right click on a stack of chests in the storage opens the whole
	stack (up to OPEN_LIMIT) - the bag's Ctrl + right click (uiinventory.py,
	ItemOpenAllRunner) for the Skrzynie storage: uses go out RATE_COUNT a
	RATE_WINDOW, at most IN_FLIGHT unanswered; a stack that stops shrinking
	for LOST_AFTER seconds MAX_RETRIES times (the bag full, the server's
	limits) ends the run."""
	OPEN_LIMIT = 50
	IN_FLIGHT = 20
	RATE_COUNT = 20
	RATE_WINDOW = 0.5
	LOST_AFTER = 0.8
	MAX_RETRIES = 2

	def __init__(self):
		ui.Window.__init__(self)
		self.__Reset()

	def __del__(self):
		ui.Window.__del__(self)

	def __Reset(self):
		self.window = -1
		self.pos = -1
		self.vnum = 0
		self.count = 0
		self.opened = 0
		self.target = 0
		self.inFlight = 0
		self.sendTimes = []
		self.lastProgress = 0.0
		self.retries = 0

	def IsRunning(self):
		return 0 != self.vnum

	def Start(self, window, pos):
		vnum = player.GetItemIndex(window, pos)
		count = player.GetItemCount(window, pos)
		if not vnum or count <= 0:
			return False
		item.SelectItem(vnum)
		if item.GetItemType() != getattr(item, "ITEM_TYPE_GIFTBOX", 23):
			return False
		if hasattr(item, "ITEM_FLAG_CONFIRM_WHEN_USE") and item.IsFlag(item.ITEM_FLAG_CONFIRM_WHEN_USE):
			return False
		self.__Reset()
		self.window = window
		self.pos = pos
		self.vnum = vnum
		self.count = count
		self.target = min(count, self.OPEN_LIMIT)
		self.lastProgress = app.GetTime()
		chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_OPEN_START % self.target)
		self.Show()
		return True

	def Stop(self, message=None):
		if not self.IsRunning():
			return
		if message is None:
			message = TEXT_OPEN_STOP % self.opened
		self.__Reset()
		self.Hide()
		chat.AppendChat(chat.CHAT_TYPE_INFO, message)

	def OnUpdate(self):
		if not self.IsRunning():
			return
		if not __import__("warpsafe").InGame():
			self.Stop()
			return
		now = app.GetTime()
		if player.GetItemIndex(self.window, self.pos) == self.vnum:
			count = player.GetItemCount(self.window, self.pos)
		else:
			count = 0
		if count < self.count:
			taken = self.count - count
			self.opened += taken
			self.inFlight = max(0, self.inFlight - taken)
			self.lastProgress = now
			self.retries = 0
		self.count = count
		if self.opened >= self.target or 0 == count:
			self.Stop(TEXT_OPEN_DONE % self.opened)
			return
		if self.inFlight > 0 and now - self.lastProgress > self.LOST_AFTER:
			self.retries += 1
			if self.retries > self.MAX_RETRIES:
				self.Stop()
				return
			self.inFlight = 0
			self.lastProgress = now
		controller = _Controller()
		if controller and controller.isAttached():
			self.Stop()
			return
		self.sendTimes = [t for t in self.sendTimes if now - t < self.RATE_WINDOW]
		while self.opened + self.inFlight < self.target and self.inFlight < min(self.IN_FLIGHT, self.count) \
				and len(self.sendTimes) < self.RATE_COUNT:
			if 0 == self.inFlight:
				self.lastProgress = now
			self.inFlight += 1
			self.sendTimes.append(now)
			net.SendItemUsePacket(self.window, self.pos)


# ---------------------------------------------------------------- the window

class EkwipunekWindow(ui.BoardWithTitleBar):
	WIDTH = 184
	GRID_X = 12
	GRID_Y = 34

	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)
		self.widgets = []
		self.pageTabs = []
		self.categoryButtons = []
		self.page = 0
		self.category = 0
		self.questionDialog = None
		self.sellPos = -1
		self.sellCount = 0
		self.pickDialog = None
		self.pickPos = -1
		self.openAll = OpenAllRunner()
		self.AddFlag('movable')
		self.AddFlag('float')
		self.SetCloseEvent(ui.__mem_func__(self.Close))
		self.__Build()
		(screenWidth, screenHeight) = (wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight())
		self.SetPosition(max(0, screenWidth - 176 - self.WIDTH - 12), 88)

	def __del__(self):
		ui.BoardWithTitleBar.__del__(self)

	def __Build(self):
		y = self.GRID_Y
		grid = ui.GridSlotWindow()
		grid.SetParent(self)
		grid.SetPosition(self.GRID_X, y)
		grid.ArrangeSlot(0, COLUMNS, ROWS, CELL, CELL, 0, 0)
		grid.SetSlotBaseImage(SLOT_BASE_IMAGE, 1.0, 1.0, 1.0, 1.0)
		grid.SetSelectEmptySlotEvent(ui.__mem_func__(self.OnSelectEmptySlot))
		grid.SetSelectItemSlotEvent(ui.__mem_func__(self.OnSelectItemSlot))
		grid.SetUnselectItemSlotEvent(ui.__mem_func__(self.OnUseSlot))
		grid.SetUseSlotEvent(ui.__mem_func__(self.OnUseSlot))
		grid.SetOverInItemEvent(ui.__mem_func__(self.OnOverInItem))
		grid.SetOverOutItemEvent(ui.__mem_func__(self.OnOverOutItem))
		grid.Show()
		self.widgets.append(grid)
		self.grid = grid
		y += ROWS * CELL + 4

		for i, name in enumerate(PAGE_NAMES):
			tab = ui.RadioButton()
			tab.SetParent(self)
			tab.SetPosition(14 + 39 * i, y)
			tab.SetUpVisual(TAB_IMAGE % 1)
			tab.SetOverVisual(TAB_IMAGE % 2)
			tab.SetDownVisual(TAB_IMAGE % 3)
			tab.SetText(name)
			tab.SAFE_SetEvent(self.SetPage, i)
			tab.Show()
			self.widgets.append(tab)
			self.pageTabs.append(tab)
		y += 26

		for i, (win, slot, name, icon) in enumerate(Categories()):
			button = ui.RadioButton()
			button.SetParent(self)
			button.SetPosition(8 + 34 * i, y)
			button.SetUpVisual(ICON_IMAGE % (icon, 1))
			button.SetOverVisual(ICON_IMAGE % (icon, 2))
			button.SetDownVisual(ICON_IMAGE % (icon, 3))
			button.SetToolTipText(name)
			button.SAFE_SetEvent(self.SetCategory, i)
			button.Show()
			self.widgets.append(button)
			self.categoryButtons.append(button)
		y += 36

		sortButton = ui.Button()
		sortButton.SetParent(self)
		sortButton.SetPosition((self.WIDTH - 61) // 2, y)
		sortButton.SetUpVisual(BUTTON_IMAGE % 1)
		sortButton.SetOverVisual(BUTTON_IMAGE % 2)
		sortButton.SetDownVisual(BUTTON_IMAGE % 3)
		sortButton.SetText(TEXT_SORT)
		sortButton.SetToolTipText(TEXT_SORT_TIP)
		sortButton.SAFE_SetEvent(self.AskSort)
		sortButton.Show()
		self.widgets.append(sortButton)
		y += 30

		self.SetSize(self.WIDTH, y + 4)

		tooltip = uiToolTip.ItemToolTip()
		tooltip.HideToolTip()
		self.tooltip = tooltip

		self.SetPage(0)
		self.SetCategory(0)

	def Destroy(self):
		self.Hide()
		self.__CloseDialogs()
		if self.openAll:
			self.openAll.Stop()
			self.openAll.Hide()
		self.openAll = None
		if self.pickDialog:
			self.pickDialog.Destroy()
			self.pickDialog = None
		if self.tooltip:
			self.tooltip.HideToolTip()
		self.tooltip = None
		for widget in self.widgets:
			widget.Hide()
		self.widgets = []
		self.pageTabs = []
		self.categoryButtons = []
		self.grid = None

	def __CloseDialogs(self):
		if self.questionDialog:
			self.questionDialog.Close()
			self.questionDialog = None
		if self.pickDialog:
			self.pickDialog.Close()

	def Open(self):
		self.Show()
		self.SetTop()
		self.Refresh()

	def Close(self):
		self.__CloseDialogs()
		if self.tooltip:
			self.tooltip.HideToolTip()
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	# ---------------------------------------------------------- state

	def Window(self):
		cats = Categories()
		if not cats:
			return -1
		return cats[self.category][0]

	def SlotType(self):
		return Categories()[self.category][1]

	def CategoryName(self):
		return Categories()[self.category][2]

	def GlobalPos(self, local):
		return self.page * COLUMNS * ROWS + local

	def SetPage(self, page):
		self.page = page
		for i, tab in enumerate(self.pageTabs):
			if i == page:
				tab.Down()
			else:
				tab.SetUp()
		self.Refresh()

	def SetCategory(self, index):
		if index >= len(Categories()):
			return
		self.category = index
		for i, button in enumerate(self.categoryButtons):
			if i == index:
				button.Down()
			else:
				button.SetUp()
		self.SetTitleName("%s - %s" % (TEXT_TITLE, self.CategoryName()))
		self.Refresh()

	def Refresh(self):
		if not self.grid:
			return
		window = self.Window()
		for local in xrange(COLUMNS * ROWS):
			pos = self.GlobalPos(local)
			vnum = player.GetItemIndex(window, pos)
			if not vnum:
				self.grid.ClearSlot(local)
				continue
			count = player.GetItemCount(window, pos)
			self.grid.SetItemSlot(local, vnum, count if count > 1 else 0)
		self.grid.RefreshSlot()

	def OnUpdate(self):
		ReleaseIcon()

	# ---------------------------------------------------------- slots

	def OnOverInItem(self, local):
		if not self.tooltip:
			return
		controller = _Controller()
		if controller and controller.isAttached():
			return
		self.tooltip.ClearToolTip()
		self.tooltip.SetInventoryItem(self.GlobalPos(local), self.Window())

	def OnOverOutItem(self):
		if self.tooltip:
			self.tooltip.HideToolTip()

	def __DropHere(self, pos):
		"""Whatever the cursor holds, dropped on this storage's cell pos."""
		controller = _Controller()
		attachedType = controller.GetAttachedType()
		attachedPos = controller.GetAttachedSlotNumber()
		attachedCount = controller.GetAttachedItemCount()
		vnum = controller.GetAttachedItemIndex()
		window = self.Window()

		# MT2009_PLUS_EKWIPUNEK_REFINE_V1: a refine scroll (from the bag or a storage)
		# dropped on another item here opens the refine window for that item
		targetVnum = player.GetItemIndex(window, pos)
		if vnum and targetVnum and targetVnum != vnum and item.IsRefineScroll(vnum) and \
				(attachedType == player.SLOT_TYPE_INVENTORY or IsEkwSlotType(attachedType)):
			if attachedType == player.SLOT_TYPE_INVENTORY:
				srcWindow = player.INVENTORY
			else:
				srcWindow = WindowOfSlotType(attachedType)
			if not (attachedType == player.SLOT_TYPE_INVENTORY and player.IsEquipmentSlot(attachedPos)):
				net.SendItemUseToItemPacket(srcWindow, attachedPos, window, pos)
		elif IsEkwSlotType(attachedType):
			srcWindow = WindowOfSlotType(attachedType)
			if srcWindow != window:
				chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_WRONG_KIND % self.CategoryName())
			elif attachedPos != pos:
				net.SendItemMovePacket(srcWindow, attachedPos, window, pos, attachedCount)
		elif attachedType == player.SLOT_TYPE_INVENTORY:
			if player.IsEquipmentSlot(attachedPos):
				pass
			elif CategoryOf(player.GetItemIndex(attachedPos)) != window:
				chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_WRONG_KIND % self.CategoryName())
			else:
				net.SendItemMovePacket(player.INVENTORY, attachedPos, window, pos, attachedCount)
		elif attachedType == player.SLOT_TYPE_SAFEBOX:
			if CategoryOf(vnum) != window:
				chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_WRONG_KIND % self.CategoryName())
			else:
				net.SendSafeboxCheckoutPacket(attachedPos, window, pos)
		elif attachedType == player.SLOT_TYPE_MALL:
			if CategoryOf(vnum) != window:
				chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_WRONG_KIND % self.CategoryName())
			else:
				net.SendMallCheckoutPacket(attachedPos, window, pos)
		Deattach()

	def OnSelectEmptySlot(self, local):
		controller = _Controller()
		if controller and controller.isAttached():
			self.__DropHere(self.GlobalPos(local))

	def OnSelectItemSlot(self, local):
		pos = self.GlobalPos(local)
		window = self.Window()
		controller = _Controller()
		if controller and controller.isAttached():
			# the same item's stack takes it; anything else is refused by the server
			self.__DropHere(pos)
			return

		vnum = player.GetItemIndex(window, pos)
		count = player.GetItemCount(window, pos)
		if not vnum:
			return

		cursor = app.GetCursor()
		if app.SELL == cursor:
			self.AskSell(pos)
			return
		if app.BUY == cursor:
			return

		if app.IsPressed(app.DIK_LSHIFT) or app.IsPressed(app.DIK_RSHIFT):
			if count > 1:
				self.OpenPick(pos, count)
			return

		if AttachItem(self, self.SlotType(), pos, vnum, count):
			snd.PlaySound("sound/ui/pick.wav")

	def OnUseSlot(self, local):
		controller = _Controller()
		if controller and controller.isAttached():
			return
		pos = self.GlobalPos(local)
		window = self.Window()
		if not player.GetItemIndex(window, pos):
			return
		if self.openAll:
			if self.openAll.IsRunning():
				self.openAll.Stop()
				return
			if (app.IsPressed(app.DIK_LCONTROL) or app.IsPressed(app.DIK_RCONTROL)) and self.openAll.Start(window, pos):
				self.OnOverOutItem()
				return
		net.SendItemUsePacket(window, pos)
		self.OnOverOutItem()

	# ---------------------------------------------------------- split

	def OpenPick(self, pos, count):
		if not self.pickDialog:
			import uiPickETC
			dialog = uiPickETC.PickETCDialog()
			dialog.LoadDialog()
			self.pickDialog = dialog
		self.pickPos = pos
		self.pickDialog.SetTitleName("Podziel stos")
		self.pickDialog.SetAcceptEvent(ui.__mem_func__(self.OnPick))
		self.pickDialog.Open(count)

	def OnPick(self, count, *args):
		pos = self.pickPos
		window = self.Window()
		vnum = player.GetItemIndex(window, pos)
		if not vnum or count <= 0:
			return
		AttachItem(self, self.SlotType(), pos, vnum, count)

	# ---------------------------------------------------------- sell and sort

	def AskSell(self, pos):
		window = self.Window()
		vnum = player.GetItemIndex(window, pos)
		count = player.GetItemCount(window, pos)
		if not vnum:
			return
		item.SelectItem(vnum)
		if item.IsAntiFlag(item.ANTIFLAG_SELL):
			import localeInfo
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.SHOP_CANNOT_SELL_ITEM)
			return
		price = item.GetISellItemPrice()
		if item.Is1GoldItem():
			price = count / max(1, price)
		else:
			price = price * count
		if not getattr(app, "ENABLE_NO_SELL_PRICE_DIVIDED_BY_5", 0) and not (80003 <= vnum <= 80008):
			price /= 5
		import localeInfo
		self.__CloseDialogs()
		self.sellPos = pos
		self.sellCount = count
		dialog = uiCommon.QuestionDialog()
		dialog.SetText(localeInfo.DO_YOU_SELL_ITEM(item.GetItemName(), count, price))
		dialog.SetAcceptEvent(ui.__mem_func__(self.Sell))
		dialog.SetCancelEvent(ui.__mem_func__(self.__CloseDialogs))
		dialog.Open()
		self.questionDialog = dialog

	def Sell(self):
		net.SendChatPacket("/ekwipunek sprzedaj %d %d %d" % (self.Window(), self.sellPos, self.sellCount))
		self.__CloseDialogs()

	def AskSort(self):
		self.__CloseDialogs()
		dialog = uiCommon.QuestionDialog()
		dialog.SetText(TEXT_SORT_ASK % self.CategoryName())
		dialog.SetAcceptEvent(ui.__mem_func__(self.Sort))
		dialog.SetCancelEvent(ui.__mem_func__(self.__CloseDialogs))
		dialog.Open()
		self.questionDialog = dialog

	def Sort(self):
		net.SendChatPacket("/ekwipunek sortuj %d" % self.Window())
		self.__CloseDialogs()


# ---------------------------------------------------------------- module API

def Start():
	"""game.py, once the character is in the world (and after every warp): the
	hello that makes the server route items here. Nothing with an old exe."""
	if IsSupported():
		net.SendChatPacket("/ekwipunek hello")


def OnServerOk(*args):
	_state['server'] = True


def GetWindow():
	window = _state['window']
	if window is None:
		import uiminigameutil
		window = uiminigameutil.SafeCreate(EkwipunekWindow, TEXT_TITLE)
		_state['window'] = window
	return window


def OpenWindow():
	if not IsSupported():
		chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_NEEDS_EXE)
		return
	window = GetWindow()
	if window:
		window.Open()


def ToggleWindow():
	window = _state['window']
	if window is not None and window.IsShow():
		window.Close()
		return
	OpenWindow()


def Refresh():
	"""interfacemodule.RefreshInventory: every item packet."""
	window = _state['window']
	if window is not None and window.IsShow():
		window.Refresh()


def DestroyWindow():
	window = _state['window']
	_state['window'] = None
	dialog = _state.get('dialog')
	if dialog:
		dialog.Close()
		_state['dialog'] = None
	ReleaseIcon(True)
	if window is not None:
		window.Destroy()
