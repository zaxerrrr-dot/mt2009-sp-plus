# MT2009_PLUS_GAYA_CURRENCY_V1: Gaya as a currency of the character, as on the global servers (the owner, 28 October
# 2026: "no icon / counter next to the Yang - the Gaya piles up as slots in the inventory"; server-patches/gaya2).
#
#   server -> client  "GAYA <total> <change>" (on entering the game and at every change; game.py __GayaPoint)
#
# The counter lives here (constInfo.GAYA) and is shown in:
#   - the inventory: a Gaya row (icon + counter) over the Yang row (uiscript/inventorywindow.py; BindInventory /
#     RefreshInventory below, called by uiinventory.py);
#   - the money bar ("Expanded Money Taskbar" of the owner's package cache/gaya2/emt, uiscript/expandedmoneytaskbar.py):
#     Won (only with constInfo.ENABLE_WON - the server has no Won yet), Gaya and Yang, opened by a button on the
#     taskbar left of the character button (MakeMoneyBar, called by interfacemodule.py);
#   - the crafting windows' Gaya cost (uicuberenewal.py, uicubeokno.py, uicube.py: Have(95927)).
# The images are the client pack "gaya2" (client-2.0.30/tools/gaya2, d:/ymir work/ui/gaya2/).
import constInfo
import player
import ui
import uiToolTip

GAYA_VNUM = 95927
GAYA_MAX = 999999
GAYA2_UI = "d:/ymir work/ui/gaya2/"
ICON_GAYA = GAYA2_UI + "gaya_icon.tga"

TIP_YANG = ("Yang", "Podstawowa waluta gry.")
TIP_GAYA = ("Gaya", "Waluta Yohary (najwy\xbfej 999 999). Szlifuj Kamyki u Statuy Wojownika w Porcie, p\xb3a\xe6 w Sklepie Gaya i przy wytwarzaniu.")
TIP_WON = ("Won", "Waluta wymiany: 1 Won = 100 000 000 Yang.")
TEXT_BUTTON = "Waluty (Yang, Gaya)"
TEXT_GOT = "Otrzymujesz %s Gaya."

COLOR_TITLE = 0xfff1e6c0


def Enabled():
	return getattr(constInfo, "ENABLE_GAYA_CURRENCY", 0)


def WonEnabled():
	return getattr(constInfo, "ENABLE_WON", 0)


def Get():
	return getattr(constInfo, "GAYA", 0)


def Have(vnum):
	# the crafting windows: Gaya is the counter, every other material the bag
	if vnum == GAYA_VNUM and Enabled():
		return Get()
	return player.GetItemCountByVnum(vnum)


def Format(n):
	s = str(max(0, int(n)))
	parts = []
	while len(s) > 3:
		parts.insert(0, s[-3:])
		s = s[:-3]
	parts.insert(0, s)
	return ".".join(parts)


def Won():
	return getattr(constInfo, "WON", 0)


# ------------------------------------------------------------------ the server's line
def OnServer(game, total, delta):
	try:
		total = max(0, min(GAYA_MAX, int(total)))
		delta = int(delta)
	except ValueError:
		return
	constInfo.GAYA = total
	interface = getattr(game, "interface", None)
	if interface:
		Refresh(interface)
		for name in ("wndCube", "wndCubeRenewal"):
			wnd = getattr(interface, name, None)
			if wnd and hasattr(wnd, "Refresh") and wnd.IsShow():
				try:
					wnd.Refresh()
				except Exception:
					pass


# ------------------------------------------------------------------ tooltips
_toolTip = None


def _Tip(lines):
	global _toolTip
	if not _toolTip:
		_toolTip = uiToolTip.ToolTip()
	_toolTip.ClearToolTip()
	_toolTip.AppendTextLine(lines[0], COLOR_TITLE)
	_toolTip.AppendTextLine(lines[1])
	_toolTip.ShowToolTip()


def _TipOut():
	if _toolTip:
		_toolTip.HideToolTip()


def _BindTip(wnd, lines):
	if not wnd:
		return
	try:
		wnd.SetEvent(lambda *args: _Tip(lines), "mouse_over_in", 0)
		wnd.SetEvent(lambda *args: _TipOut(), "mouse_over_out", 0)
	except Exception:
		try:
			wnd.SetStringEvent("MOUSE_OVER_IN", lambda: _Tip(lines))
			wnd.SetStringEvent("MOUSE_OVER_OUT", _TipOut)
		except Exception:
			pass


# ------------------------------------------------------------------ the inventory's Gaya row
def BindInventory(inventory):
	inventory.wndGaya = inventory.GetChild2("Gaya")
	_BindTip(inventory.GetChild2("Gaya_Icon"), TIP_GAYA)
	_BindTip(inventory.GetChild2("Gaya_Slot"), TIP_GAYA)
	_BindTip(inventory.GetChild2("Won_Icon"), TIP_WON)
	inventory.wndWon = inventory.GetChild2("Won")
	RefreshInventory(inventory)


def RefreshInventory(inventory):
	wnd = getattr(inventory, "wndGaya", None)
	if wnd:
		wnd.SetText(Format(Get()))
	won = getattr(inventory, "wndWon", None)
	if won:
		won.SetText(Format(Won()))


# ------------------------------------------------------------------ the money bar (Won / Gaya / Yang)
class ExpandedMoneyTaskBar(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.wndMoney = None
		self.wndGaya = None
		self.wndWon = None

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def LoadWindow(self):
		try:
			ui.PythonScriptLoader().LoadScriptFile(self, "UIScript/ExpandedMoneyTaskbar.py")
			self.wndMoney = self.GetChild("Money")
			self.wndGaya = self.GetChild("Gaya")
			self.wndWon = self.GetChild2("Won")
		except:
			import exception
			exception.Abort("ExpandedMoneyTaskBar.LoadWindow.LoadObject")
		_BindTip(self.GetChild2("Money_Icon"), TIP_YANG)
		_BindTip(self.GetChild2("Gaya_Icon"), TIP_GAYA)
		_BindTip(self.GetChild2("Won_Icon"), TIP_WON)
		self.Refresh()

	def Destroy(self):
		self.ClearDictionary()
		self.wndMoney = None
		self.wndGaya = None
		self.wndWon = None

	def Refresh(self):
		if self.wndMoney:
			self.wndMoney.SetText(Format(player.GetGold()))
		if self.wndGaya:
			self.wndGaya.SetText(Format(Get()))
		if self.wndWon:
			self.wndWon.SetText(Format(Won()))

	def Toggle(self):
		if self.IsShow():
			self.Close()
		else:
			self.Refresh()
			self.Show()
			self.SetTop()

	def Close(self):
		_TipOut()
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True


_bar = None
_button = None


def MakeMoneyBar(interface):
	# the bar and its button on the taskbar (left of the character button, when the taskbar has room there)
	global _bar, _button
	if not Enabled():
		return
	DestroyMoneyBar()
	_bar = ExpandedMoneyTaskBar()
	_bar.LoadWindow()
	_bar.Hide()
	taskBar = getattr(interface, "wndTaskBar", None)
	if not taskBar:
		return
	try:
		x, y = taskBar.GetChild("CharacterButton").GetLocalPosition()
		x -= 34
		right = taskBar.GetChild2("RightMouseButton")
		if right:
			rx, ry = right.GetLocalPosition()
			if x < rx + right.GetWidth() + 2:
				return	# a narrow screen: no room - the inventory's row shows the Gaya anyway
		btn = ui.Button()
		btn.SetParent(taskBar)
		btn.SetPosition(x, y)
		btn.SetUpVisual(GAYA2_UI + "money_button_01.tga")
		btn.SetOverVisual(GAYA2_UI + "money_button_02.tga")
		btn.SetDownVisual(GAYA2_UI + "money_button_03.tga")
		btn.SetToolTipText(TEXT_BUTTON)
		btn.SetEvent(ToggleMoneyBar)
		btn.Show()
		_button = btn
	except Exception, msg:
		import dbg
		dbg.TraceError("gayacurrency.MakeMoneyBar: %s" % str(msg))


def ToggleMoneyBar():
	if _bar:
		_bar.Toggle()


def HideMoneyBar():
	_TipOut()
	if _bar:
		_bar.Hide()


def DestroyMoneyBar():
	global _bar, _button, _toolTip
	if _button:
		_button.Hide()
		_button = None
	if _bar:
		_bar.Hide()
		_bar.Destroy()
		_bar = None
	if _toolTip:
		_toolTip.HideToolTip()
		_toolTip = None


def Refresh(interface=None):
	# the counters: the inventory's row and the bar (RefreshStatus, the server's line)
	if interface:
		inventory = getattr(interface, "wndInventory", None)
		if inventory:
			RefreshInventory(inventory)
	if _bar and _bar.IsShow():
		_bar.Refresh()
