# MT2009_PLUS_WEAPON_ELEMENT_V1: Zaczarowanie Zywiolu Broni - the two windows (server-patches/zywiolbroni; the official
# RefineElementDialog / RefineElementChangeDialog, the "[System] Elemental Spell" package by WorldArd, GF graphics).
# The server opens them ("WELEMOPEN <mode> <weaponCell> <scrollCell> <fee> <type> <newGrade> <curPacked> <attMin>
# <attMax> <powMin> <powMax>", game.py -> OnServer):
#   mode 1  a scroll of an element on a weapon: "Ulepszenie" - the weapon's tooltip with the level it would reach
#           ("<Zywiol> +n", "Wartosc Ataku: x - y (+a~+b)", "Sila <zywiolu> +a% ~ +b%" - the range one level can add),
#           the fee, OK / Anuluj;
#   mode 2  Zwoj Klatwy: the same window with the level after the curse (no cost line when the fee is 0);
#   mode 3  Zwoj Zmiany: the GF window with the six elements (the weapon's own one off) and the fee.
# OK sends "/welem ok" (1, 2) or "/welem change <element>" (3); Anuluj / Esc / X "/welem close". The server checks
# everything again by the item ids it kept and answers "WELEMRESULT <mode> <success> <element>" (the official popup)
# or "WELEMCLOSE".
import app
import chat
import item
import net
import player
import ui
import uiCommon
import uiToolTip
import localeInfo
import welem

MODE_UPGRADE, MODE_CURSE, MODE_CHANGE = 1, 2, 3

_wnd = {}


def _Send(text):
	try:
		net.SendChatPacket(text)
	except:
		pass


class WeaponElementDialog(ui.ScriptWindow):
	"""the upgrade / curse window: the weapon's tooltip as it would be after the attempt (the refine window layout)"""

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.isLoaded = False
		self.mode = 0
		self.fee = 0
		self.weaponCell = -1
		self.tooltip = None
		self.slotList = []
		self.itemImage = None

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __LoadScript(self):
		try:
			ui.PythonScriptLoader().LoadScriptFile(self, "uiscript/weaponelementdialog.py")
			self.board = self.GetChild("Board")
			self.titleBar = self.GetChild("TitleBar")
			self.costText = self.GetChild("Cost")
			self.GetChild("AcceptButton").SetEvent(ui.__mem_func__(self.__OnAccept))
			self.GetChild("CancelButton").SetEvent(ui.__mem_func__(self.Cancel))
		except:
			import exception
			exception.Abort("WeaponElementDialog.__LoadScript")

		tooltip = uiToolTip.ItemToolTip()
		tooltip.SetParent(self)
		tooltip.SetFollow(False)
		tooltip.SetPosition(15, 38)
		tooltip.Show()
		self.tooltip = tooltip

		self.slotList = []
		for i in xrange(3):
			slot = ui.ImageBox()
			slot.LoadImage("d:/ymir work/ui/public/slot_base.sub")
			slot.SetParent(tooltip)
			slot.SetWindowVerticalAlignCenter()
			slot.Show()
			self.slotList.append(slot)

		itemImage = ui.ImageBox()
		itemImage.SetParent(tooltip)
		itemImage.SetWindowVerticalAlignCenter()
		itemImage.SetPosition(-35, 0)
		itemImage.Show()
		self.itemImage = itemImage

		self.titleBar.SetCloseEvent(ui.__mem_func__(self.Cancel))
		self.isLoaded = True

	def Destroy(self):
		self.ClearDictionary()
		self.tooltip = None
		self.slotList = []
		self.itemImage = None
		self.isLoaded = False

	def Open(self, mode, weaponCell, fee, newType, newGrade, curPacked, rng):
		if not self.isLoaded:
			self.__LoadScript()
		vnum = player.GetItemIndex(weaponCell)
		if not vnum:
			_Send("/welem close")
			return
		self.mode = mode
		self.fee = fee
		self.weaponCell = weaponCell

		metinSlot = [player.GetItemMetinSocket(weaponCell, i) for i in xrange(player.METIN_SOCKET_MAX_NUM)]
		attrSlot = [player.GetItemAttribute(weaponCell, i) for i in xrange(player.ATTRIBUTE_SLOT_MAX_NUM)]
		self.tooltip.ClearToolTip()
		self.tooltip.welemPreview = welem.Preview(mode, newType, newGrade, curPacked, rng)
		try:
			self.tooltip.AddItemData(vnum, metinSlot, attrSlot, 0, 0, player.INVENTORY, weaponCell)
		finally:
			self.tooltip.welemPreview = None

		item.SelectItem(vnum)
		self.itemImage.LoadImage(item.GetIconImageFileName())
		(w, h) = item.GetItemSize()
		for slot in self.slotList:
			slot.Hide()
		for i in xrange(min(3, h)):
			self.slotList[i].SetPosition(-35, i * 32 - (h - 1) * 16)
			self.slotList[i].Show()

		if fee > 0:
			self.costText.SetText("Cena za Ulepszenie: %s" % localeInfo.NumberToMoneyString(fee))
			self.costText.Show()
		else:
			self.costText.Hide()
		self.__UpdateDialog()
		self.SetTop()
		self.Show()

	def __UpdateDialog(self):
		width = self.tooltip.GetWidth() + 60
		height = self.tooltip.GetHeight() + 103
		self.board.SetSize(width, height)
		self.tooltip.SetPosition(15 + 35, 38)
		self.titleBar.SetWidth(width - 15)
		self.SetSize(width, height)
		(x, y) = self.GetLocalPosition()
		self.SetPosition(x, y)

	def __OnAccept(self):
		if self.fee > 0 and player.GetElk() < self.fee:
			chat.AppendChat(chat.CHAT_TYPE_INFO, welem.Text("REFINE_ELEMENT_NOT_ENOUGHT_YANG", "Za ma\xb3o Yang."))
			return
		_Send("/welem ok")
		self.Hide()

	def Cancel(self):
		if self.IsShow():
			_Send("/welem close")
		self.Hide()

	def OnPressEscapeKey(self):
		self.Cancel()
		return True


class WeaponElementChangeDialog(ui.ScriptWindow):
	"""Zwoj Zmiany: the GF window with the six elements"""

	BUTTONS = (("FireButton", 2), ("IceButton", 3), ("WindButton", 4), ("ElectButton", 1), ("EarthButton", 5),
	           ("DarkButton", 6))

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.isLoaded = False
		self.buttons = {}
		self.current = 0
		self.selected = 0
		self.fee = 0

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __LoadScript(self):
		try:
			ui.PythonScriptLoader().LoadScriptFile(self, "uiscript/weaponelementchange.py")
			self.buttons = {}
			for name, t in self.BUTTONS:
				button = self.GetChild(name)
				button.SetEvent(ui.__mem_func__(self.__OnClickElement), t)
				self.buttons[t] = button
			self.costText = self.GetChild("Cost")
			self.GetChild("board").SetCloseEvent(ui.__mem_func__(self.Cancel))
			self.GetChild("AcceptButton").SetEvent(ui.__mem_func__(self.__OnAccept))
			self.GetChild("CancelButton").SetEvent(ui.__mem_func__(self.Cancel))
		except:
			import exception
			exception.Abort("WeaponElementChangeDialog.__LoadScript")
		self.isLoaded = True

	def Destroy(self):
		self.ClearDictionary()
		self.buttons = {}
		self.isLoaded = False

	def Open(self, current, fee):
		if not self.isLoaded:
			self.__LoadScript()
		self.current = current
		self.selected = 0
		self.fee = fee
		for t, button in self.buttons.items():
			button.SetUp()
			button.Enable()
		if current in self.buttons:
			self.buttons[current].Disable()
		self.costText.SetText(localeInfo.NumberToMoneyString(fee))
		self.SetTop()
		self.Show()

	def __OnClickElement(self, t):
		for k, button in self.buttons.items():
			if k != t and k != self.current:
				button.SetUp()
		if t in self.buttons:
			self.buttons[t].Down()
		self.selected = t

	def __OnAccept(self):
		if not self.selected or self.selected == self.current:
			return
		if self.fee > 0 and player.GetElk() < self.fee:
			chat.AppendChat(chat.CHAT_TYPE_INFO, welem.Text("REFINE_ELEMENT_NOT_ENOUGHT_YANG", "Za ma\xb3o Yang."))
			return
		_Send("/welem change %d" % self.selected)
		self.Hide()

	def Cancel(self):
		if self.IsShow():
			_Send("/welem close")
		self.Hide()

	def OnPressEscapeKey(self):
		self.Cancel()
		return True


def _Get(name, cls):
	w = _wnd.get(name)
	if w is None:
		w = cls()
		_wnd[name] = w
	return w


def _HideAll():
	for w in _wnd.values():
		try:
			w.Hide()
		except:
			pass


def Reset():
	"""a new login / warp: the windows go (made again when the server opens one)"""
	for w in _wnd.values():
		try:
			w.Hide()
			w.Destroy()
		except:
			pass
	_wnd.clear()


_last = {"vnum": 0}


def _Popup(text):
	try:
		popup = uiCommon.PopupDialog()
		popup.SetText(text)
		popup.Open()
		_wnd["popup"] = popup
	except:
		chat.AppendChat(chat.CHAT_TYPE_INFO, text)


def OnOpen(mode="0", weaponCell="-1", scrollCell="-1", fee="0", t="0", newGrade="0", curPacked="0", attMin="0",
           attMax="0", powMin="0", powMax="0", *rest):
	try:
		mode, weaponCell, fee, t, newGrade = int(mode), int(weaponCell), int(fee), int(t), int(newGrade)
		curPacked = int(curPacked) & 0xFFFFFFFF
		rng = (int(attMin), int(attMax), int(powMin), int(powMax))
	except ValueError:
		return
	_HideAll()
	_last["vnum"] = player.GetItemIndex(weaponCell)
	if curPacked:
		welem.OnServer("1", str(weaponCell), str(curPacked))
	if mode == MODE_CHANGE:
		_Get("change", WeaponElementChangeDialog).Open(t, fee)
	elif mode in (MODE_UPGRADE, MODE_CURSE):
		_Get("dialog", WeaponElementDialog).Open(mode, weaponCell, fee, t, newGrade, curPacked, rng)


def OnClose(*rest):
	_HideAll()


def OnResult(mode="0", success="0", t="0", *rest):
	_HideAll()
	try:
		mode, success, t = int(mode), int(success), int(t)
	except ValueError:
		return
	if mode == MODE_UPGRADE:
		if success:
			_Popup(welem.Text("REFINE_ELEMENT_UPGRADE_SUCCESS_TEXT", "Zaczarowanie \xbfywio\xb3u powiod\xb3o si\xea!"))
		else:
			_Popup(welem.Text("REFINE_ELEMENT_UPGRADE_FAIL_TEXT", "Zaczarowanie \xbfywio\xb3u nie powiod\xb3o si\xea!"))
	elif mode == MODE_CURSE:
		_Popup(welem.Text("REFINE_ELEMENT_DOWNGRADE_TEXT", "Zosta\xb3 zmniejszony poziom zaczarowania \xbfywio\xb3u."))
	elif mode == MODE_CHANGE and success:
		name = ""
		if _last["vnum"]:
			item.SelectItem(_last["vnum"])
			name = item.GetItemName()
		_Popup(welem.Text("REFINE_ELEMENT_CHANGE_TEXT", "%s posiada teraz \xbfywio\xb3: %s!") % (name, welem.NAME.get(t, "")))
