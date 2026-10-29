# MT2009_PLUS_INVENTORY_V2_V1 - the official v2 inventory: the package "offical_inventory_v2" (Autor: dracaryS) on
# our client (the owner, 29 October 2026: three systems that change the game visually, for Yohara).
#
# What the package does: the inventory splits into two windows as on the official servers - the equipment window
# (the worn items on the new equipment picture, the rings and four round buttons under it, page tabs I-IV at the
# top) docked over the bag (four page tabs, the grid, the money). Its server half (four equipment pages: WEAR_*_2..4,
# a player.inv_idx column, the support skill 132 and the item 38306 used up to three times) is the same official
# feature our Druga strona ekwipunku already is (server-patches/addeq, MT2009_PLUS_ADDEQ_V1: two pages, the inactive
# one in a hidden store, item 38306 / 76055, skill 200) - so only the windows come over; the page tabs I / II are
# addeq's (uiaddeq.py), III / IV stay hidden. No server, exe, packet or database change.
#
# Here: the equipment window (EquipWindow, uiscript/inventoryequipwindow.py) and the glue for uiinventory.py's
# InventoryWindow (which loads uiscript/inventorywindowv2.py as the bag; every hook there is marked
# MT2009_PLUS_INVENTORY_V2_V1):
#   - Bind(inventory): loads the equipment window and lends its children to the inventory's dictionary
#     (GetChild("EquipmentSlot"), "DSSButton", "DepositButton", "MyShopButton", "CostumeButton",
#     "HorseInventoryWindow", "ChestPreviewButton", "Equipment_Tab_01/02"), so the rest of uiinventory.py works on
#     them as on the old one-window inventory;
#   - docking: the equipment window sits right over the bag and follows it; dragged away (more than DOCK_SNAP px)
#     it stays where it is put, dragged back near the bag it docks again. Docked or not and its own place are kept
#     per character (uiwindowpos: "ekwipunek_v2_dok", "ekwipunek_v2"). A bag too high for the window over it is
#     moved down once when it opens;
#   - it opens and closes with the bag (InventoryWindow.Show / Hide); its X or Esc closes only it (the package);
#   - the belt window hangs on its belt slot, the costume window opens left of it, the side bar spans both while
#     they are docked (uiinventory.py BeltInventoryWindow / ClickCostumeButton / SidebarWindow).
#
# ENABLED = 0 gives the old one-window inventory back (uiscript/inventorywindow.py); a v2 script that fails to load
# falls back to it too (syserr says why).
import ui
import app
import wndMgr
import dbg
from _weakref import proxy

ENABLED = 1

BAG_SCRIPT = "UIScript/InventoryWindowV2.py"
EQUIP_SCRIPT = "UIScript/InventoryEquipWindow.py"
DOCK_SNAP = 12
DOCK_KEY = "ekwipunek_v2_dok"
POS_KEY = "ekwipunek_v2"
PAGE_TABS = 4			# Equipment_PageBg_0..3 / Equipment_Tab_01..04 of the script
SERVER_PAGES = 2		# Druga strona ekwipunku: I / II
BELT_Y = 134			# the belt window's top under the window's top: its open button by the belt slot

_state = {'failed': False}


def IsEnabled():
	return ENABLED and not _state['failed']


def BagScript():
	return BAG_SCRIPT


def Failed(why):
	"""the v2 scripts did not load: the old inventory from now on (uiinventory.py loads it again)."""
	_state['failed'] = True
	dbg.TraceError("inventoryv2: %s - the old one-window inventory is used" % why)


def _GetValue(key, default):
	try:
		import uiwindowpos
		value = uiwindowpos.GetValue(key, default)
	except Exception:
		return None
	return value


def _SetValue(key, value):
	try:
		import uiwindowpos
		uiwindowpos.SetValue(key, value)
	except Exception:
		pass


class EquipWindow(ui.ScriptWindow):
	def __init__(self, inventory):
		ui.ScriptWindow.__init__(self)
		self.inventory = proxy(inventory)
		self.docked = True
		self.dockLoaded = False
		self.lastPos = None
		self.fixBag = False
		self.isLoaded = False

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def Load(self):
		ui.PythonScriptLoader().LoadScriptFile(self, EQUIP_SCRIPT)
		self.GetChild("board").SetCloseEvent(ui.__mem_func__(self.OnClickClose))
		self.isLoaded = True
		try:
			import uiwindowpos
			uiwindowpos.Track(self, POS_KEY)
		except Exception:
			pass

	def Destroy(self):
		self.Hide()
		self.ClearDictionary()
		self.inventory = None

	def __LoadDock(self):
		if self.dockLoaded:
			return
		value = _GetValue(DOCK_KEY, 1)
		if value is None:
			return
		self.docked = bool(value)
		self.dockLoaded = True

	def OpenWithBag(self):
		self.__LoadDock()
		self.Show()
		self.lastPos = None
		self.__Follow(False)	# at once (the belt window, shown next, hangs on it)
		self.fixBag = True		# the next frame: uiwindowpos has put the bag back by then

	def OnClickClose(self):
		try:
			self.inventory.SetEquipShowStatus(False)
		except (ReferenceError, AttributeError):
			self.Hide()

	def OnPressEscapeKey(self):
		self.OnClickClose()
		return True

	def DockPosition(self):
		bx, by = self.inventory.GetGlobalPosition()
		return bx, by - self.GetHeight()

	def IsDocked(self):
		return self.docked and self.IsShow()

	# dragged: near the bag's top it snaps on and docks, anywhere else it stays undocked
	def OnMoveWindow(self, x, y):
		try:
			dx, dy = self.DockPosition()
		except (ReferenceError, AttributeError):
			return
		docked = abs(x - dx) <= DOCK_SNAP and abs(y - dy) <= DOCK_SNAP and dy >= 0
		if docked:
			self.SetPosition(dx, dy)
		if docked != self.docked:
			self.docked = docked
			_SetValue(DOCK_KEY, 1 if docked else 0)

	def OnUpdate(self):
		self.__Follow(self.fixBag)

	def __Follow(self, fixBag):
		try:
			inventory = self.inventory
			if not inventory.IsShow():
				return
			if self.docked:
				bx, by = inventory.GetGlobalPosition()
				height = self.GetHeight()
				if fixBag and by < height:
					# a bag placed for the old, taller window: down under the equipment window, if the screen has room
					by = min(height, max(0, wndMgr.GetScreenHeight() - inventory.GetHeight()))
					inventory.SetPosition(bx, by)
				x, y = bx, max(0, by - height)
				if (x, y) != self.GetGlobalPosition():
					self.SetPosition(x, y)
			if fixBag:
				self.fixBag = False
			pos = self.GetGlobalPosition()
			if pos != self.lastPos:
				self.lastPos = pos
				wndBelt = getattr(inventory, "wndBelt", None)
				if wndBelt and wndBelt.IsShow():
					wndBelt.AdjustPositionAndSize()
		except (ReferenceError, AttributeError):
			pass


def Bind(inventory):
	"""uiinventory.py InventoryWindow.__LoadWindow, after the bag script: the equipment window, its children lent to the
	inventory. False (and the old inventory from then on) when the script does not load."""
	wnd = EquipWindow(inventory)
	try:
		wnd.Load()
	except Exception, e:
		import traceback
		dbg.TraceError("inventoryv2: %s" % str(e))
		for line in traceback.format_exc().splitlines():
			dbg.TraceError("    " + line)
		try:
			wnd.ClearDictionary()
		except Exception:
			pass
		return False
	for name, child in wnd.ElementDictionary.items():
		if not inventory.IsChild(name):
			inventory.InsertChild(name, child)
	for i in xrange(PAGE_TABS):
		bg = wnd.GetChild2("Equipment_PageBg_%d" % i)
		if bg:
			bg.Hide()
	wnd.Hide()
	inventory.wndEquipWindow = wnd
	return True


def RefreshPageTabs(inventory, unlocked, page):
	"""uiaddeq.py Refresh: tab I always (as the package shows one page), II once the second page is unlocked, the
	server's page pressed."""
	wnd = getattr(inventory, "wndEquipWindow", None)
	if not wnd:
		return
	count = SERVER_PAGES if unlocked else 1
	for i in xrange(PAGE_TABS):
		bg = wnd.GetChild2("Equipment_PageBg_%d" % i)
		tab = wnd.GetChild2("Equipment_Tab_%02d" % (i + 1))
		if not bg or not tab:
			continue
		if i < count:
			bg.Show()
			tab.Show()
			if i == page:
				tab.Down()
			else:
				tab.SetUp()
		else:
			bg.Hide()


def SideBarRect(inventory):
	"""the rect the side bar stands by: the bag, and the equipment window with it while docked over it."""
	x, y = inventory.GetGlobalPosition()
	width, height = inventory.GetWidth(), inventory.GetHeight()
	wnd = getattr(inventory, "wndEquipWindow", None)
	if wnd and wnd.IsDocked():
		ex, ey = wnd.GetGlobalPosition()
		if ex == x and ey < y:
			height += y - ey
			y = ey
	return x, y, width, height


def BeltBasePosition(inventory, sideBarOffset):
	"""the belt window's place: left of the equipment window, by its belt slot (None: the window is not open)."""
	wnd = getattr(inventory, "wndEquipWindow", None)
	if not wnd or not wnd.IsShow():
		return None
	x, y = wnd.GetGlobalPosition()
	if wnd.IsDocked():
		x -= sideBarOffset
	return x - 148, y + BELT_Y


def CostumePosition(inventory, costumeWidth):
	"""the costume window's first place: left of the equipment window (None: not open)."""
	wnd = getattr(inventory, "wndEquipWindow", None)
	if not wnd or not wnd.IsShow():
		return None
	x, y = wnd.GetGlobalPosition()
	wndSideBar = getattr(inventory, "wndSideBar", None)
	if wndSideBar and wnd.IsDocked():
		x -= wndSideBar.GetLeftOffset()
	return max(0, x - costumeWidth), y
