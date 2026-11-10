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
#   - right click moves the whole stack into the bag (MT2009_PLUS_EKWIPUNEK_
#     TOBAG_V1, "/ekwipunek dotorby"); double click or Ctrl + right click
#     uses (a book is read, a chest opened); Ctrl + right click on a stack of
#     chests opens the whole stack, as in the bag;
#   - Shift + click splits a stack; the shop's sell cursor sells (asks first);
#   - the trade window and the crafting window take its items too
#     (uiexchange.py, uicube.py);
#   - Ameria's settings bar: "stack" joins the stacks ("/ekwipunek stos"),
#     "sort" joins them and orders the items by kind ("/ekwipunek sortuj"), the
#     search field shows the category's items with the text in their name.
#
# MT2009_PLUS_EKWIPUNEK_LOOK_V1 (the owner, 21 October 2026: "okno ma wygladac
# jak w Amerii"): the window is Ameria's 1:1 - uiscript/ekwipunekwindow.py,
# Ameria's images in mt2009_ui/ekwipunek.
# MT2009_PLUS_EKWIPUNEK_BOOKS_V1: every read book in Ksiegi (BOOK_VNUMS, the
# server's Mt2009EkwCategoryOf in step).
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
# MT2009_PLUS_EKWIPUNEK_ROW2_V1 (the owner, 21 October 2026: "dodaj tam
# Kostiumy, Alchemie i ItemShop", "okno kostiumow, nie magazyn kostiumow"): the
# second row of category buttons as Ameria's - Kostiumy opens the costume window
# (uiinventory.py CostumeWindow; the inventory's own costume button is gone,
# MT2009_PLUS_INVENTORY_DSS_V1), Alchemia the Dragon Soul window, ItemShop the
# in-game ItemShop (as the minimap's / taskbar's button). interfacemodule.py
# binds the interface (BindInterface).
#
# The windows need the 3.0 exe (client-patches/exe, ENABLE_SPECIAL_STORAGE:
# player.UPGRADE_INVENTORY ...). With an older exe this module does nothing and
# never says hello, so the server keeps every item in the bag.
#
# MT2009_PLUS_EKWIPUNEK_CATS_V2 (the owner's list of 3 November 2026, section B):
#   - the second row's Kostiumy / Alchemia / ItemShop buttons are gone (the
#     equipment window has its own round buttons 15-18 again); only Skrzynie
#     stays in that row;
#   - the categories as the owner sorts them (CategoryOf, with the server's
#     Mt2009EkwCategoryOf in step): Zaczarowanie also takes the Pozwolenia,
#     Marmur Blogoslawienstwa, Blogoslawienstwo Przedmiotu, the 6/7 shards and
#     supplements, Wzmocnienie Przedmiotu, Zielona Sila, Zaczaruj / Transformuj
#     kostium; the aura runes stay with the materials; the herbalism recipes go
#     to Ksiegi; the refine scrolls and Kamien Runiczny stay in the bag (those
#     stored before are dragged / right-clicked out; the server moves the stored
#     items whose category moved at the hello);
#   - a skill book shows its own skill's icon, as in the bag (the slot gets the
#     sockets: ui.SlotWindow.SetItemSlot, skillbookicon.py);
#   - "Sortuj" sorts every category at once ("/ekwipunek sortuj wszystko");
#   - Ctrl + right click on a bag item while this window is open moves it into
#     its category (MoveBagItemByCtrl, "/ekwipunek doekw <cell>") - a chest is
#     moved, not opened;
#   - a supplement dragged from here onto the Seon-Hae window's additive slot
#     (uiseonhae.py: SupportOf).
#
# MT2009_PLUS_EKWIPUNEK_HANDEL_V1 (the owner, 3 November 2026: "Z dodatkowego
# EQ mozna dawac przedmioty bezposrednio na handel i na tobol (sklep
# offline)"): an item of a storage goes straight into
#   - the trade window (uiexchange.py) - dragged onto the own side, or a right
#     click here while the trade is open;
#   - the offline shop - the new shop's window (offlineshopbuilder.py) and the
#     open shop's (offlineshopmanage.py, offlineshopui.py MyShopSlots, the
#     second page too): dragged onto a free cell, or a right click here while
#     one of them is open; the price window asks the Dom Towarowy's hint for it
#     as for a bag item (shopautoprice.py; the server's /flea_price reads the
#     storages, server-patches/ekwipunek "HANDEL" edits).
# The server took a storage's item there already (CExchange::AddItem,
# CHARACTER::OpenMyShop, the Ikarus shop's add-item: GetItem by the item's
# window, every check of a bag item - antiflags, lock, trade, owner); the
# client offered the bag only. An item in the trade or on the new shop's list
# is dimmed here and can't be picked up or right-clicked into another window
# (InUse: uiinventory.py's trade / shop builder events, by the item's window -
# the bag marked its own cell of the same number before); the trade's server
# lock (SetExchanging) keeps every move, use and /ekwipunek command off it, and
# a shop's line leaves the storage the moment it is listed (MoveAndDestroyInstance).
#
# Python 2.7 as the client has it; the Polish letters are CP1250 escapes.

import app
import chat
import eventManager
import item
import mouseModule
import net
import player
import snd
import ui
import uiCommon
import uiToolTip
import weakref
import wndMgr

TEXT_TITLE = "Dodatkowy ekwipunek"
# MT2009_PLUS_EKWIPUNEK_LOOK_V1: the title bar is Ameria's (128 wide, the close
# button on it) - a short title fits it whole
TEXT_TITLE_BAR = "Dodatkowy EQ"
TEXT_MANAGE_TIP = "Sortowanie i wyszukiwanie"
TEXT_STACK_TIP = "Po\xb3\xb9cz stosy"
TEXT_STACK_ASK = "Po\xb3\xb9czy\xe6 stosy w kategorii \"%s\"?"
TEXT_SORT_TIP = "Sortuj"
# MT2009_PLUS_EKWIPUNEK_CATS_V2: every category at once
TEXT_SORT_ASK = "Po\xb3\xb9czy\xe6 stosy i posortowa\xe6 wszystkie kategorie?"
TEXT_NEEDS_EXE = "Dodatkowy ekwipunek wymaga nowego klienta (exe 3.0)."
TEXT_WRONG_KIND = "Ten przedmiot nie pasuje do kategorii \"%s\"."
TEXT_ATTACH_ASK = "W\xb3o\xbfy\xe6 %s do przedmiotu?"
TEXT_OPEN_START = "Otwieranie skrzynek: %d szt."
TEXT_OPEN_DONE = "Otwarto skrzynek: %d."
TEXT_OPEN_STOP = "Otwieranie przerwane, otwarto skrzynek: %d."

# (window constant, slot type constant, name, icon) in the tabs' order.
CATEGORY_DEFS = (
	("UPGRADE_INVENTORY", "SLOT_TYPE_UPGRADE_INVENTORY", "Materia\xb3y ulepsze\xf1", "upgrade"),
	("BOOK_INVENTORY", "SLOT_TYPE_BOOK_INVENTORY", "Ksi\xeagi", "book"),
	("STONE_INVENTORY", "SLOT_TYPE_STONE_INVENTORY", "Kamienie Duszy", "stone"),
	("CHANGE_INVENTORY", "SLOT_TYPE_CHANGE_INVENTORY", "Zaczarowania", "bonus"),
	("CHEST_INVENTORY", "SLOT_TYPE_CHEST_INVENTORY", "Skrzynie", "chest"),
)

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

# MT2009_PLUS_EKWIPUNEK_CATS_V2 (playerbot_ekwipunek.cpp, Mt2009EkwCategoryOf - keep both in step):
# Zaczarowanie by vnum - Pozwolenie na Wzmocnienie (x2) / na Zaczarowanie 30368-30370, Blogoslawienstwo
# Przedmiotu 71052, the 6/7 shards 39070-39081, the supplements 72064-72067; and by the use subtype
# (ITEM_USE): USE_ADD_ATTRIBUTE 19 (Wzmocnienie Przedmiotu, Zielona Sila), USE_ADD_ATTRIBUTE2 22 (Marmur
# Blogoslawienstwa), USE_CHANGE_COSTUME_ATTR 34 (Zaczaruj kostium), USE_RESET_COSTUME_ATTR 35 (Transformuj
# kostium). Ulepszacze by vnum: the aura runes 49990-49995. Ksiegi: USE_CRAFT_RECIPE 33 (the herbalism
# recipes) and Losowa Receptura 50910. The bag: Kamien Runiczny 31225 and the refine scrolls.
CHANGE_VNUMS = set(range(30368, 30371) + [71052] + range(39070, 39082) + range(72064, 72068))
CHANGE_USE_SUBTYPES = (19, 22, 34, 35)
UPGRADE_VNUMS = set(range(49990, 49996))
USE_CRAFT_RECIPE = 33
RECIPE_VNUMS = set([50910])
BAG_VNUMS = set([31225])

# MT2009_PLUS_EKWIPUNEK_BOOKS_V1: the books of other types than ITEM_SKILLBOOK
# (playerbot_ekwipunek.cpp, Mt2009EkwCategoryOf - keep both in step): Sztuka
# Combo, Ksiega Misji, the language books, Ksiega Polimorfii, Ksiega Precyzji,
# Charyzma / Inspiracja, Podrecznik: Dopalacz / Riposta, the horse books, the
# horse skills' books (Jazda ...) and the pet's skill books (Sztuka ...).
# Ksiega Zapomnienia (ITEM_SKILLFORGET) goes there by its type.
BOOK_VNUMS = set(range(50304, 50307) + range(50307, 50311) + range(50317, 50322) + [50336]
	+ range(71088, 71091) + range(50311, 50314) + range(50314, 50317) + [71092, 50325]
	+ range(50338, 50344) + [50514, 50515, 50052, 50053, 50060]
	+ range(55050, 55068)
	# MT2009_PLUS_PET_BOOKS_KSIEGI_V1 (3.0.14 item 7): the growth pet's evolution books 55003-55007, Skrzynia Ksiag
	# Zwierza 55009 and its skill books 55010-55027 / 55034-55038; the treats 55028-55031 stay in the bag
	+ range(55003, 55008) + [55009] + range(55010, 55028) + range(55034, 55039))

_state = {
	'window': None,
	'icon': 0,
	'server': False,
	'categories': None,
	'refineWindow': None,
	'interface': None,	# MT2009_PLUS_EKWIPUNEK_ROW2_V1: weakref.ref of interfacemodule.Interface
	'inUse': set(),		# MT2009_PLUS_EKWIPUNEK_HANDEL_V1: (window, cell) in the trade / on the new shop's list
}

# MT2009_PLUS_EKWIPUNEK_HANDEL_V1
TEXT_QUICK_EXCHANGE = "PPM: dodaj do handlu"
TEXT_QUICK_SHOP = "PPM: wystaw w sklepie"
TEXT_BUSY_SORT = "Zamknij handel lub okno zak\xb3adania sklepu, zanim po\xb3\xb9czysz lub posortujesz przedmioty."
TEXT_IN_USE = "Ten przedmiot jest ju\xbf w handlu lub na li\x9cie sklepu."

_USE_TYPE = getattr(item, "ITEM_TYPE_USE", 3)


# ---------------------------------------------------------------- MT2009_PLUS_EKWIPUNEK_ROW2_V1

def BindInterface(interface):
	"""interfacemodule.py, when it builds the inventory. (The second row's
	window buttons it served - MT2009_PLUS_EKWIPUNEK_ROW2_V1 - are gone since
	MT2009_PLUS_EKWIPUNEK_CATS_V2; the reference stays for later buttons.)"""
	_state['interface'] = weakref.ref(interface) if interface else None


def _Interface():
	ref = _state['interface']
	if ref is None:
		return None
	return ref()


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


def IsEkwWindow(window):
	"""MT2009_PLUS_EKWIPUNEK_HANDEL_V1: one of the storages' item windows."""
	for win, slot, name, icon in Categories():
		if win == window:
			return True
	return False


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
	if vnum in BOOK_VNUMS:
		return player.BOOK_INVENTORY
	# MT2009_PLUS_EKWIPUNEK_CATS_V2: the owner's categories of 3 November 2026
	if vnum in CHANGE_VNUMS:
		return player.CHANGE_INVENTORY
	item.SelectItem(vnum)
	itemType = item.GetItemType()
	subType = item.GetItemSubType()
	if itemType == _USE_TYPE and subType in CHANGE_USE_SUBTYPES:
		return player.CHANGE_INVENTORY
	if vnum in UPGRADE_VNUMS:
		return player.UPGRADE_INVENTORY
	if vnum in BAG_VNUMS:
		return 0
	if vnum in RECIPE_VNUMS or (itemType == _USE_TYPE and subType == USE_CRAFT_RECIPE):
		return player.BOOK_INVENTORY
	if itemType == getattr(item, "ITEM_TYPE_MATERIAL", -1) and subType == 0:
		return player.UPGRADE_INVENTORY
	# MT2009_PLUS_EKWIPUNEK_REFINE_V1 put the refine scrolls with the materials;
	# MT2009_PLUS_EKWIPUNEK_CATS_V2: they stay in the bag (the server's rule)
	if itemType == getattr(item, "ITEM_TYPE_SKILLBOOK", -1):
		return player.BOOK_INVENTORY
	if itemType == getattr(item, "ITEM_TYPE_SKILLFORGET", 22):
		return player.BOOK_INVENTORY
	if itemType == getattr(item, "ITEM_TYPE_METIN", -1) and subType == getattr(item, "METIN_NORMAL", 0):
		return player.STONE_INVENTORY
	if itemType == getattr(item, "ITEM_TYPE_USE", -1) and item.GetUseType(vnum) == "USE_CHANGE_ATTRIBUTE":
		return player.CHANGE_INVENTORY
	if vnum in STARTER_CHESTS:	# MT2009_PLUS_EKWIPUNEK_STARTER_V1: they stay in the bag
		return 0
	if itemType == getattr(item, "ITEM_TYPE_GIFTBOX", -1):
		return player.CHEST_INVENTORY
	# MT2009_PLUS_EKWIPUNEK_KEYS_V1: the boxes opened with a key and their keys
	if itemType in TREASURE_TYPES:
		return player.CHEST_INVENTORY
	return 0


# MT2009_PLUS_EKWIPUNEK_STARTER_V1 (the owner, 27 October 2026): the level chests of a new character - Skrzynia Ucznia
# I-III, Eksperta I-III, Mistrza I-III, Arcymistrza - never go into the chests' storage (playerbot_ekwipunek.cpp,
# Mt2009EkwCategoryOf - keep both in step).
STARTER_CHESTS = set(range(50187, 50197) + [50212, 50213])

# MT2009_PLUS_EKWIPUNEK_KEYS_V1 (a player's report on Yohara 3.0.7, 3 November 2026): the boxes that open only with
# their key (ITEM_TREASURE_BOX - Zlota / Srebrna Szkatulka, Plat. Skrzynia Skarbow, the Yohara jewel chests) and the
# keys (ITEM_TREASURE_KEY - Zloty / Srebrny Klucz, Klucz Nimfy Wodnej, Idealny Klucz, Plat. Klucz) go with the chests
# (playerbot_ekwipunek.cpp, Mt2009EkwCategoryOf - keep both in step). A key dropped on a box - in this window, from the
# bag onto a box here or from here onto a box in the bag - opens it (UseKeyOnBox: the item-on-item use, the server's
# ITEM_TREASURE_KEY takes a box of any window and checks the pair).
TREASURE_BOX_TYPE = getattr(item, "ITEM_TYPE_TREASURE_BOX", 20)
TREASURE_KEY_TYPE = getattr(item, "ITEM_TYPE_TREASURE_KEY", 21)
TREASURE_TYPES = (TREASURE_BOX_TYPE, TREASURE_KEY_TYPE)


def IsKeyOnBox(srcVnum, dstVnum):
	"""MT2009_PLUS_EKWIPUNEK_KEYS_V1: a key (ITEM_TREASURE_KEY) held over a box (ITEM_TREASURE_BOX)."""
	if not srcVnum or not dstVnum or srcVnum == dstVnum:
		return False
	item.SelectItem(srcVnum)
	if item.GetItemType() != TREASURE_KEY_TYPE:
		return False
	item.SelectItem(dstVnum)
	return item.GetItemType() == TREASURE_BOX_TYPE


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
	if IsKeyOnBox(srcVnum, dstVnum):	# MT2009_PLUS_EKWIPUNEK_KEYS_V1: a stored key opens the bag's box
		net.SendItemUseToItemPacket(window, attachedPos, player.INVENTORY, cell)
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
		# MT2009_PLUS_EKWIPUNEK_CATS_V2: the stones, marbles and 71052 are used on the piece; the Pozwolenia, shards
		# and supplements kept here too (materials) only when their item table says they apply to an item
		item.SelectItem(srcVnum)
		if item.GetItemType() == _USE_TYPE:
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


# ---------------------------------------------------------------- MT2009_PLUS_EKWIPUNEK_HANDEL_V1: trade and shop

def IsInUse(window, cell):
	"""A storage's item put in the trade or on the new shop's list."""
	return (window, cell) in _state['inUse']


def MarkInUse(window, cell):
	"""uiinventory.py: the trade (EVENT_ADD_ITEM_TO_EXCHANGE) or the new shop's
	list (ADD_ITEM_TO_SHOP_BUILDER) took the storage's item at (window, cell)."""
	if not IsEkwWindow(window):
		return False
	_state['inUse'].add((window, cell))
	Refresh()
	return True


def MarkClean(window, cell):
	"""uiinventory.py: the item came off the new shop's list."""
	if not IsEkwWindow(window):
		return False
	_state['inUse'].discard((window, cell))
	Refresh()
	return True


def ClearInUse():
	"""uiinventory.py: the trade or the new shop's window closed."""
	if not _state['inUse']:
		return
	_state['inUse'].clear()
	Refresh()


def _QuickTarget():
	"""(window, kind) of the open window a right click here gives the item to:
	the trade, the new shop's window, the open shop's - the bag's order
	(uiinventory.UseItemSlot) - or None."""
	interface = _Interface()
	if not interface:
		return None
	for attr, kind in (("dlgExchange", "exchange"), ("offlineShopBuilder", "myshop"), ("offlineShopManage", "myshop_manage")):
		wnd = getattr(interface, attr, None)
		try:
			if wnd and wnd.IsShow() and hasattr(wnd, "QuickAddFrom"):
				return (wnd, kind)
		except Exception:
			pass
	return None


def QuickAddText():
	"""The tooltip's hint line while a right click here gives the item away."""
	target = _QuickTarget()
	if not target:
		return _AuraHint()	# MT2009_PLUS_AURA_RUNE_STACK_V1
	if target[1] == "exchange":
		return TEXT_QUICK_EXCHANGE
	return TEXT_QUICK_SHOP


def _AuraHint():
	try:
		return __import__("uiaura").QuickHint()
	except Exception:
		return ""


def QuickAdd(window, cell):
	"""A right click on a storage's item with the trade or a shop window open:
	the item goes there (the price window for a shop). True when one was open
	(the click is taken). MT2009_PLUS_AURA_RUNE_STACK_V1 (the owner, 10 November
	2026): with Theowahdan's aura window open the item (the runes - the whole
	stack -, a material) goes into it (uiaura.TakeItem)."""
	target = _QuickTarget()
	if not target:
		if IsInUse(window, cell):
			return False
		try:
			return bool(__import__("uiaura").TakeItem(window, cell))
		except Exception:
			return False
	if IsInUse(window, cell):
		chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_IN_USE)
		return True
	if not player.GetItemIndex(window, cell):
		return True
	target[0].QuickAddFrom(window, cell)
	return True


def IsWindowOpen():
	window = _state['window']
	return window is not None and window.IsShow()


def MoveBagItemByCtrl(cell):
	"""MT2009_PLUS_EKWIPUNEK_CATS_V2 - uiinventory.py's right click on a bag
	item: with Ctrl held and this window open the item goes into its category
	("/ekwipunek doekw <cell>": its stacks first, then a free cell; a chest is
	moved, not opened). True when it was taken (the bag does nothing else)."""
	if not IsSupported() or not IsWindowOpen():
		return False
	if not (app.IsPressed(app.DIK_LCONTROL) or app.IsPressed(getattr(app, "DIK_RCONTROL", app.DIK_LCONTROL))):
		return False
	if player.IsEquipmentSlot(cell):
		return False
	vnum = player.GetItemIndex(cell)
	if not vnum:
		return False
	window = CategoryOf(vnum)
	if not window:
		return False	# no category: the bag's own Ctrl + right click (open the stack, use)
	net.SendChatPacket("/ekwipunek doekw %d" % cell)
	return True


def SupportOf(attachedType, attachedPos):
	"""MT2009_PLUS_EKWIPUNEK_CATS_V2 - uiseonhae.py: (window, cell, vnum) of a
	storage's item on the cursor (a supplement from Zaczarowanie), or None."""
	if not IsEkwSlotType(attachedType):
		return None
	window = WindowOfSlotType(attachedType)
	return (window, attachedPos, player.GetItemIndex(window, attachedPos))


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

# MT2009_PLUS_EKWIPUNEK_LOOK_V1: CP1250 upper -> lower case of the Polish letters
# for the search field (str.lower knows ASCII only).
_LOWER_PL = {'\xa5': '\xb9', '\xc6': '\xe6', '\xca': '\xea', '\xa3': '\xb3', '\xd1': '\xf1',
	'\xd3': '\xf3', '\x8c': '\x9c', '\x8f': '\x9f', '\xaf': '\xbf'}


def _Lower(text):
	return "".join([_LOWER_PL.get(c, c) for c in text.lower()])


class EkwipunekWindow(ui.ScriptWindow):
	"""MT2009_PLUS_EKWIPUNEK_LOOK_V1: Ameria's special storage window 1:1
	(uiscript/ekwipunekwindow.py; Ameria root/uispecialinventory.py
	InventoryWindowNew): the settings button left of the title opens / closes
	the bar with "stack", "sort" and the search field (open from the start, the
	grid, page tabs and category buttons 25 lower then), pages I-IV, the
	category buttons in Ameria's frame under them.

	Mouse (MT2009_PLUS_EKWIPUNEK_TOBAG_V1): right click - the whole stack into
	the bag (joins its stacks there first, then the first free cell); double
	click or Ctrl + right click - use (Ameria uses on a right click; the owner
	wanted the move to the bag there); Ctrl + right click on a stack of chests
	opens the whole stack, as in the bag; Shift + click - split; the shop's sell
	cursor sells (asks first); drag - into the bag, onto an item, to an NPC."""

	MANAGE_SHIFT = 25
	PAGE_SIZE = COLUMNS * ROWS

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.page = 0
		self.category = 0
		self.questionDialog = None
		self.sellPos = -1
		self.sellCount = 0
		self.pickDialog = None
		self.pickPos = -1
		self.manageOpen = False
		self.searchMap = None
		self.pageTabs = []
		self.categoryButtons = []
		self.objectToMove = []
		self.grid = None
		self.tooltip = None
		self.openAll = OpenAllRunner()
		self.__Load()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __Load(self):
		ui.PythonScriptLoader().LoadScriptFile(self, "uiscript/ekwipunekwindow.py")

		self.board = self.GetChild("board")
		self.GetChild("TitleBar").SetCloseEvent(ui.__mem_func__(self.Close))
		self.GetChild("TitleName").SetText(TEXT_TITLE_BAR)

		manageButton = self.GetChild("ManageInventory")
		manageButton.SetToolTipText(TEXT_MANAGE_TIP)
		manageButton.SAFE_SetEvent(self.ManageInventory)

		self.manageBar = self.GetChild("ManageBar")
		stackButton = self.GetChild("StackButton")
		stackButton.SetToolTipText(TEXT_STACK_TIP)
		stackButton.SAFE_SetEvent(self.AskStack)
		sortButton = self.GetChild("SortButton")
		sortButton.SetToolTipText(TEXT_SORT_TIP)
		sortButton.SAFE_SetEvent(self.AskSort)

		search = self.GetChild("SearchEdit")
		search.OnIMEUpdate = ui.__mem_func__(self.OnSearchUpdate)
		search.SetEscapeEvent(ui.__mem_func__(self.Close))
		search.SetReturnEvent(ui.__mem_func__(self.OnSearchReturn))
		self.search = search

		grid = self.GetChild("ItemSlot")
		grid.SetSelectEmptySlotEvent(ui.__mem_func__(self.OnSelectEmptySlot))
		grid.SetSelectItemSlotEvent(ui.__mem_func__(self.OnSelectItemSlot))
		grid.SetUnselectItemSlotEvent(ui.__mem_func__(self.OnRightClick))
		grid.SetUseSlotEvent(ui.__mem_func__(self.OnUseSlot))
		grid.SetOverInItemEvent(ui.__mem_func__(self.OnOverInItem))
		grid.SetOverOutItemEvent(ui.__mem_func__(self.OnOverOutItem))
		self.grid = grid

		for i in xrange(len(PAGE_NAMES)):
			tab = self.GetChild("Inventory_Tab_%02d" % (i + 1))
			tab.SAFE_SetEvent(self.SetPage, i)
			self.pageTabs.append(tab)

		categoryBoard = self.GetChild("CategoryBoard")
		for i, (win, slot, name, icon) in enumerate(Categories()):
			button = self.GetChild("Category_%s" % icon)
			button.SetToolTipText(name)
			button.SAFE_SetEvent(self.SetCategory, i)
			self.categoryButtons.append(button)
		self.objectToMove = [grid, categoryBoard] + self.pageTabs

		tooltip = uiToolTip.ItemToolTip()
		tooltip.HideToolTip()
		self.tooltip = tooltip

		self.manageBar.Hide()
		self.ManageInventory()	# open at the start, as Ameria's window
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
		if self.search and self.search.IsFocus():
			self.search.KillFocus()
		self.search = None
		self.manageBar = None
		self.board = None
		self.pageTabs = []
		self.categoryButtons = []
		self.objectToMove = []
		self.grid = None
		self.ClearDictionary()

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
		if self.search and self.search.IsFocus():
			self.search.KillFocus()
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	# ---------------------------------------------------------- Ameria's settings bar

	def ManageInventory(self):
		"""Ameria's ManageInventory: the bar shown / hidden, everything under it
		25 lower / higher."""
		shift = self.MANAGE_SHIFT
		if self.manageOpen:
			self.manageOpen = False
			self.manageBar.Hide()
			if self.search.IsFocus():
				self.search.KillFocus()
			self.search.SetText("")
			if self.search.CanPlaceholder():
				self.search.placeholderTextLine.Show()
			self.searchMap = None
			shift = -shift
		else:
			self.manageOpen = True
			self.manageBar.Show()
		self.SetSize(self.GetWidth(), self.GetHeight() + shift)
		self.board.SetSize(self.board.GetWidth(), self.board.GetHeight() + shift)
		for widget in self.objectToMove:
			(x, y) = widget.GetLocalPosition()
			widget.SetPosition(x, y + shift)
		self.Refresh()

	def OnSearchUpdate(self):
		if self.search.IsFocus():
			ui.EditLine.OnIMEUpdate(self.search)
		self.Refresh()

	def OnSearchReturn(self):
		self.search.KillFocus()

	def SearchText(self):
		if not self.manageOpen or not self.search:
			return ""
		return self.search.GetText().strip()

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
		"""The storage cell of a grid slot: the page's, or the item the search
		put there (-1 for an empty slot of the search)."""
		if self.searchMap is not None:
			return self.searchMap.get(local, -1)
		return self.page * self.PAGE_SIZE + local

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
		self.Refresh()

	def Refresh(self):
		if not self.grid:
			return
		window = self.Window()
		text = _Lower(self.SearchText())
		if text:
			self.__RefreshSearch(window, text)
			return
		self.searchMap = None
		for local in xrange(self.PAGE_SIZE):
			pos = self.GlobalPos(local)
			vnum = player.GetItemIndex(window, pos)
			if not vnum:
				self.grid.ClearSlot(local)
				continue
			count = player.GetItemCount(window, pos)
			self.grid.SetItemSlot(local, vnum, count if count > 1 else 0, socket=self.__Sockets(window, pos))
			self.__Dim(local, window, pos)
		self.grid.RefreshSlot()

	def __Dim(self, local, window, pos):
		"""MT2009_PLUS_EKWIPUNEK_HANDEL_V1: an item in the trade / on the new
		shop's list dimmed, as the bag's."""
		try:
			if IsInUse(window, pos):
				self.grid.DisableSlot(local)
			else:
				self.grid.EnableSlot(local)
		except Exception:
			pass

	def __Sockets(self, window, pos):
		"""MT2009_PLUS_EKWIPUNEK_CATS_V2: the item's sockets for the slot - a
		skill book (50300) shows its own skill's icon then, as in the bag
		(uiinventory.RefreshBagSlotWindow, ui.SlotWindow.SetItemSlot)."""
		try:
			return tuple([player.GetItemMetinSocket(window, pos, j) for j in xrange(player.METIN_SOCKET_MAX_NUM)])
		except Exception:
			return None

	def __ItemName(self, window, pos, vnum):
		item.SelectItem(vnum)
		name = item.GetItemName()
		if vnum == 50300:
			try:
				import skill
				name = skill.GetSkillName(player.GetItemMetinSocket(window, pos, 0)) or name
			except Exception:
				pass
		return name

	def __RefreshSearch(self, window, text):
		"""Ameria's search field: the category's items (all four pages) whose
		name has the text, one after another in the grid."""
		used = [False] * self.PAGE_SIZE
		found = {}
		for pos in xrange(self.PAGE_SIZE * len(PAGE_NAMES)):
			vnum = player.GetItemIndex(window, pos)
			if not vnum:
				continue
			if text not in _Lower(self.__ItemName(window, pos, vnum)):
				continue
			item.SelectItem(vnum)
			height = max(1, item.GetItemSize()[1])
			local = -1
			for cell in xrange(self.PAGE_SIZE):
				if cell // COLUMNS + height > ROWS:
					break
				if not [1 for h in xrange(height) if used[cell + h * COLUMNS]]:
					local = cell
					break
			if local < 0:
				break
			for h in xrange(height):
				used[local + h * COLUMNS] = True
			found[local] = pos
		self.searchMap = found
		for local in xrange(self.PAGE_SIZE):
			if local not in found:
				self.grid.ClearSlot(local)
				continue
			pos = found[local]
			count = player.GetItemCount(window, pos)
			self.grid.SetItemSlot(local, player.GetItemIndex(window, pos), count if count > 1 else 0,
				socket=self.__Sockets(window, pos))
			self.__Dim(local, window, pos)
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
		pos = self.GlobalPos(local)
		if pos < 0:
			return
		self.tooltip.ClearToolTip()
		self.tooltip.SetInventoryItem(pos, self.Window())
		# MT2009_PLUS_EKWIPUNEK_HANDEL_V1: the right click's way into the open trade / shop
		hint = QuickAddText()
		if hint and player.GetItemIndex(self.Window(), pos):
			self.tooltip.AppendSpace(5)
			self.tooltip.AppendTextLine(hint)

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
		if targetVnum and IsInUse(window, pos):
			# MT2009_PLUS_EKWIPUNEK_HANDEL_V1: nothing joins or goes onto an item in the trade / on the shop's list
			chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_IN_USE)
			Deattach()
			return
		# MT2009_PLUS_EKWIPUNEK_KEYS_V1: a key (from the bag or a storage) dropped on a box here opens it
		keyOnBox = vnum and targetVnum and IsKeyOnBox(vnum, targetVnum)
		if (keyOnBox or (vnum and targetVnum and targetVnum != vnum and item.IsRefineScroll(vnum))) and \
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
		if not controller or not controller.isAttached():
			return
		pos = self.GlobalPos(local)
		if pos < 0:
			# an empty slot of the search has no cell - the item stays on the cursor
			return
		self.__DropHere(pos)

	def OnSelectItemSlot(self, local):
		pos = self.GlobalPos(local)
		if pos < 0:
			return
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
		# MT2009_PLUS_EKWIPUNEK_HANDEL_V1: in the trade / on the new shop's list - stays where it is
		if IsInUse(window, pos):
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

	def OnRightClick(self, local):
		"""MT2009_PLUS_EKWIPUNEK_TOBAG_V1: right click - the whole stack into the
		bag ("/ekwipunek dotorby": its stacks there first, then the first free
		cell); Ctrl + right click - use (a stack of chests: open all of it)."""
		controller = _Controller()
		if controller and controller.isAttached():
			return
		pos = self.GlobalPos(local)
		window = self.Window()
		if pos < 0 or not player.GetItemIndex(window, pos):
			return
		if app.SELL == app.GetCursor():
			return
		if self.openAll and self.openAll.IsRunning():
			self.openAll.Stop()
			return
		# MT2009_PLUS_EKWIPUNEK_HANDEL_V1: with the trade or a shop window open the item goes there (as the bag's
		# right click); an item already there stays
		if QuickAdd(window, pos):
			self.OnOverOutItem()
			return
		if IsInUse(window, pos):
			return
		if app.IsPressed(app.DIK_LCONTROL) or app.IsPressed(app.DIK_RCONTROL):
			if self.openAll and self.openAll.Start(window, pos):
				self.OnOverOutItem()
				return
			self.UseItem(pos)
			return
		net.SendChatPacket("/ekwipunek dotorby %d %d" % (window, pos))
		self.OnOverOutItem()

	def OnUseSlot(self, local):
		"""A double click uses the item, as in Ameria (its first click put the
		item on the cursor - it comes off)."""
		pos = self.GlobalPos(local)
		if pos < 0:
			return
		controller = _Controller()
		if controller and controller.isAttached():
			if controller.GetAttachedType() != self.SlotType() or controller.GetAttachedSlotNumber() != pos:
				return
			Deattach()
		if not player.GetItemIndex(self.Window(), pos):
			return
		if IsInUse(self.Window(), pos):	# MT2009_PLUS_EKWIPUNEK_HANDEL_V1
			return
		if self.openAll and self.openAll.IsRunning():
			self.openAll.Stop()
			return
		self.UseItem(pos)

	def UseItem(self, pos):
		net.SendItemUsePacket(self.Window(), pos)
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

	# ---------------------------------------------------------- sell, stack and sort

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

	def __Ask(self, text, event):
		self.__CloseDialogs()
		dialog = uiCommon.QuestionDialog()
		dialog.SetText(text)
		dialog.SetAcceptEvent(ui.__mem_func__(event))
		dialog.SetCancelEvent(ui.__mem_func__(self.__CloseDialogs))
		dialog.Open()
		self.questionDialog = dialog

	def __Busy(self):
		"""MT2009_PLUS_EKWIPUNEK_HANDEL_V1: the new shop's list holds the cells
		of its items (the server does not know them before the shop opens) - no
		stacking or sorting under it, nor under the trade."""
		if _state['inUse']:
			chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_BUSY_SORT)
			return True
		return False

	def AskStack(self):
		if self.__Busy():
			return
		self.__Ask(TEXT_STACK_ASK % self.CategoryName(), self.Stack)

	def Stack(self):
		net.SendChatPacket("/ekwipunek stos %d" % self.Window())
		self.__CloseDialogs()

	def AskSort(self):
		if self.__Busy():
			return
		self.__Ask(TEXT_SORT_ASK, self.Sort)

	def Sort(self):
		# MT2009_PLUS_EKWIPUNEK_CATS_V2: every category at once
		net.SendChatPacket("/ekwipunek sortuj wszystko")
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
	_state['inUse'].clear()	# MT2009_PLUS_EKWIPUNEK_HANDEL_V1
	dialog = _state.get('dialog')
	if dialog:
		dialog.Close()
		_state['dialog'] = None
	ReleaseIcon(True)
	if window is not None:
		window.Destroy()
