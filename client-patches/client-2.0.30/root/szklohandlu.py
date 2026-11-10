# MT2009_PLUS_SZKLO_MIDDLECLICK_V1 (the owner, 10 November 2026): "Po kliknieciu scrollem na dowolny przedmiot, rowniez
# na przyklad w oknie ulepszania na ikonke Pamiatka po Demonie, i posiadajac Szklo Handlu w EQ, otwiera sie Szklo Handlu
# od razu z wyszukiwarka danego przedmiotu."
#
# The middle mouse button (wheel click) on any item anywhere in the client - inventory, extra bags, the refine window's
# material icons, storage / mall, NPC and player shops, trade, cube / crafting, chest and drop lists, quest rewards, the
# Dom Aukcyjny's own rows ... - opens the Dom Aukcyjny (the window Szklo Handlu 72802 opens, uiauctionhouse.py) locked to
# exactly that item (vnum, a skill book also its skill: AuctionHouseWindow.LockItem, the same "Tylko ten przedmiot" lock
# as a click on an offer row) and searches it. Without the glass in the bag only a short chat hint (at most every 5 s).
# The server already lets every /ah_* command work on any map while the glass is in the bag (MT2009_PLUS_SZKLO_HANDLU_V1,
# server-patches/szklohandlu), so the window is opened here on the client, no server change.
#
# No exe change: the exe already sends WM_MBUTTONDOWN to the Python object of the window under the cursor
# (CWindowManager::RunMouseMiddleButtonDown -> handler.OnMouseMiddleButtonDown), only no ui class had that method
# except game.py's GameWindow (camera rotation - it keeps its own, the 3D world is not an item).
#   - ui.Window gets a default OnMouseMiddleButtonDown (only when ui.Window has none of its own) that calls OnMiddleClick.
#   - Which item is under the cursor: every client window shows a floating (follow) ItemToolTip while an item icon is
#     hovered, so ItemToolTip.AddItemData / AddItemData_Offline remember (vnum, sockets) on the tooltip and ClearToolTip
#     forgets it; the newest shown follow tooltip with an item is the hovered item. Embedded tooltips (SetFollow(False),
#     e.g. the refine window's result item) never count.
# The client imports modules by exact name (system.py: sys.modules[name]), so "uiToolTip" and "uitooltip" are two module
# objects with two ItemToolTip classes - both are patched.
# Installed by uiauctionhouse.AuctionHouseWindow.__init__ (one line), i.e. at every entry into the game.
# Python 2.7 as the client has it; the file is ASCII (Polish strings as CP1250 escapes).
import sys
import app
import chat
import player
from _weakref import ref as _ref

GLASS_VNUM = 72802					# Szklo Handlu (ITEM_QUEST, 7 / 15 / 30 days, the second ItemShop)
HINT_GAP = 5.0						# seconds between two "no glass" hints
TEXT_NO_GLASS = "Potrzebujesz Szk\xb3a Handlu w ekwipunku, aby wyszuka\xe6 ten przedmiot w Domu Aukcyjnym."

_state = {
	"ah": None,						# _weakref.ref of the AuctionHouseWindow of this game session
	"hintAt": -100.0,
	"seq": 0,
}
_shown = {}							# id(tooltip) -> [ref(tooltip), seq, (vnum, sockets) or None]
_patched = set()					# id() of the classes already patched


# ---- the hovered item --------------------------------------------------------------------------------------------
def _Note(tooltip, itemData):
	try:
		_state["seq"] += 1
		key = id(tooltip)
		entry = _shown.get(key)
		if entry is None or entry[0]() is not tooltip:
			_shown[key] = [_ref(tooltip), _state["seq"], itemData]
		else:
			entry[1] = _state["seq"]
			entry[2] = itemData
	except:
		pass


def _Sockets(metinSlot):
	try:
		return [int(value) for value in metinSlot]
	except:
		return []


def HoveredItem():
	best = None
	for key, entry in _shown.items():
		tooltip = entry[0]()
		if tooltip is None:
			del _shown[key]
			continue
		if not entry[2]:
			continue
		try:
			if not getattr(tooltip, "followFlag", True) or not tooltip.IsShow():
				continue
		except:
			continue
		if best is None or entry[1] > best[0]:
			best = (entry[1], entry[2])
	if best:
		return best[1]
	return None


def _PatchToolTipClass(cls):
	if id(cls) in _patched:
		return
	_patched.add(id(cls))

	addItemData = cls.__dict__.get("AddItemData")
	if addItemData:
		def AddItemData(self, itemVnum, metinSlot, *args, **kwargs):
			_Note(self, (itemVnum, _Sockets(metinSlot)) if itemVnum else None)
			return addItemData(self, itemVnum, metinSlot, *args, **kwargs)
		cls.AddItemData = AddItemData

	addItemDataOffline = cls.__dict__.get("AddItemData_Offline")
	if addItemDataOffline:
		def AddItemData_Offline(self, itemVnum, itemDesc, itemSummary, metinSlot, attrSlot, *args, **kwargs):
			_Note(self, (itemVnum, _Sockets(metinSlot)) if itemVnum else None)
			return addItemDataOffline(self, itemVnum, itemDesc, itemSummary, metinSlot, attrSlot, *args, **kwargs)
		cls.AddItemData_Offline = AddItemData_Offline

	clearToolTip = cls.__dict__.get("ClearToolTip")
	if clearToolTip:
		def ClearToolTip(self, *args, **kwargs):
			entry = _shown.get(id(self))
			if entry is not None:
				entry[2] = None
			return clearToolTip(self, *args, **kwargs)
		cls.ClearToolTip = ClearToolTip


def _PatchAll():
	for name in ("uiToolTip", "uitooltip"):
		module = sys.modules.get(name)
		cls = getattr(module, "ItemToolTip", None) if module else None
		if cls is not None:
			try:
				_PatchToolTipClass(cls)
			except:
				pass
	ui = sys.modules.get("ui")
	if ui is not None and "OnMouseMiddleButtonDown" not in ui.Window.__dict__:
		def OnMouseMiddleButtonDown(self):
			return OnMiddleClick()
		ui.Window.OnMouseMiddleButtonDown = OnMouseMiddleButtonDown


def Install(auctionHouse):
	try:
		import uiToolTip	# the name the interface uses (system.py keys modules by their exact name)
	except:
		pass
	_state["ah"] = _ref(auctionHouse)
	_PatchAll()


# ---- the middle click ----------------------------------------------------------------------------------------------
def OnMiddleClick():
	try:
		return _OnMiddleClick()
	except:
		import dbg
		dbg.TraceError("szklohandlu.OnMiddleClick failed")
		return False


def _OnMiddleClick():
	_PatchAll()			# a tooltip module imported later (uiikashop's "uitooltip")
	hovered = HoveredItem()
	if not hovered:
		return False
	try:
		import mouseModule
		if mouseModule.mouseController.isAttached():
			return False
	except:
		pass

	vnum, sockets = hovered
	if player.GetItemCountByVnum(GLASS_VNUM) <= 0:
		now = app.GetTime()
		if now < _state["hintAt"] or now - _state["hintAt"] >= HINT_GAP:
			_state["hintAt"] = now
			chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_NO_GLASS)
		return True

	ah = _state["ah"]() if _state["ah"] else None
	if ah is None:
		return False

	if not ah.IsShow():
		ah.Open()
	else:
		ah.SetTop()

	socket0 = -1
	try:
		import uiauctionhouse
		if vnum in uiauctionhouse.BOOK_VNUMS and sockets:
			socket0 = sockets[0]
	except:
		pass
	locked = getattr(ah, "lockedItem", None)
	if locked and locked[0] == vnum and locked[1] == socket0:
		return True		# already showing exactly this item

	# a fresh search: no leftover category / class / refine / bonus filter may hide the item
	ah.ResetFilters()
	ah.LockItem({"vnum": vnum, "sockets": sockets or [0]})
	return True
