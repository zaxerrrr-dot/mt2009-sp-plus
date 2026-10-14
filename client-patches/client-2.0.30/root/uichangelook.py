# MT2009_PLUS_CHANGE_LOOK_V1 (the owner, 14 October): Transmutacja at Teowaden - Owsap's change-look window
# (uichangelook.py, Autor: blackdragonx61 / Mali) on chat commands instead of its packets, the rules of the pl-wiki
# "Transmutacja" (server-patches/transmutacja; the server checks everything again at "accept"):
#   left slot   the item that gets the look (a weapon, an armour, a costume, a weapon skin; a mount)
#   right slot  the item whose look it takes - destroyed
#   small slot  a ticket (Bilet Transmutacji / Polimorfii Wierzchowca) instead of 50 / 30 mln Yang
# server -> ChangeLookOpen <type>, ChangeLookSet <slot> <cell> <vnum>, ChangeLookDel <slot>, ChangeLookClose,
#           ChangeLookDone (game.py, bound methods)
# client -> /transmutacja in <slot> <cell> | out <slot> | accept | cancel
# Also here: the mark of a transmuted item on its slot (MarkSlot, uiinventory.py) and the tooltip's line
# (AppendLookInfo, uitooltip.py) - player.GetChangeLookVnum & co. of the 3.0 exe (Mt2009ChangeLook.cpp).
#
# Python 2.7 as the client has it; the texts are CP1250 escapes.

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
import localeInfo

MARK_IMAGE = "d:/ymir work/ui/game/changelook/ingame_convert_mark.tga"

TYPE_ITEM = 0
TYPE_MOUNT = 1
SLOT_LEFT = 0
SLOT_RIGHT = 1
SLOT_PASS = 2
PRICE = {TYPE_ITEM: 50000000, TYPE_MOUNT: 30000000}
LIMIT_RANGE = 1000

TITLE = {TYPE_ITEM: 'Transmutacja', TYPE_MOUNT: 'Polimorfia wierzchowca'}
LOOK_TITLE = 'Transmutacja'
LOOK_COLOR = 0xffb4d5ff
HELP = {
	TYPE_ITEM: (
		'Lewe pole: przedmiot, kt\xf3ry dostanie nowy wygl\xb9d.',
		'Prawe pole: przedmiot, kt\xf3rego wygl\xb9d przejmie - zniknie.',
		'Bro\xf1 jednor\xeaczna tylko z jednor\xeaczn\xb9, dwur\xeaczna z dwur\xeaczn\xb9;',
		'zbroje i kostiumy mi\xeadzy sob\xb9, wizerunek broni z broni\xb9 tego rodzaju.',
		'Klasa i p\xb3e\xe6 musz\xb9 pasowa\xe6. Ulepszenie usuwa transmutacj\xea.',
		'Koszt: 50 000 000 Yang albo Bilet Transmutacji (ma\xb3e pole).',
	),
	TYPE_MOUNT: (
		'Lewe pole: wierzchowiec, kt\xf3ry dostanie nowy wygl\xb9d.',
		'Prawe pole: wierzchowiec, kt\xf3rego wygl\xb9d przejmie - zniknie.',
		'Czas wierzchowca z limitem si\xea nie zmienia.',
		'Koszt: 30 000 000 Yang albo Bilet Polimorfii Wierzchowca (ma\xb3e pole).',
	),
}
TEXT_QUESTION = 'Przedmiot z prawego pola zniknie. Przenie\xb6\xe6 wygl\xb9d?'
TEXT_PUT_LEFT = 'Najpierw w\xb3\xf3\xbf przedmiot do lewego pola.'
TEXT_PUT_BOTH = 'W\xb3\xf3\xbf oba przedmioty.'
TEXT_NOT_BAG = 'Przeci\xb9gnij przedmiot z ekwipunku (nie za\xb3o\xbfony).'
TEXT_COST = 'Koszt: %s'


def GetLook(window, slot):
	if not hasattr(player, "GetChangeLookVnum"):
		return 0
	try:
		if window is None:
			return player.GetChangeLookVnum(slot)
		return player.GetChangeLookVnum(window, slot)
	except Exception:
		return 0


def MarkSlot(wndSlot, renderSlot, globalSlot, window=None):
	"""The mark in the corner of a transmuted item's slot (the slot's cover image; ClearSlot takes it off)."""
	try:
		if GetLook(window, globalSlot):
			wndMgr.SetSlotCoverImage(wndSlot.hWnd, renderSlot, MARK_IMAGE)
		else:
			wndMgr.EnableSlotCoverImage(wndSlot.hWnd, renderSlot, False)
	except Exception:
		pass


def AppendLookInfo(toolTip, look):
	"""uitooltip.py: "[ Transmutacja ]" and the name of the item whose look this one has."""
	if not look:
		return
	try:
		item.SelectItem(look)
		name = item.GetItemName()
	except Exception:
		return
	toolTip.AppendSpace(5)
	toolTip.AppendTextLine('[ %s ]' % LOOK_TITLE, LOOK_COLOR)
	toolTip.AppendTextLine(name, LOOK_COLOR)


def Money(n):
	try:
		return localeInfo.NumberToMoneyString(n)
	except Exception:
		return '%d Yang' % n


class ChangeLookWindow(ui.ScriptWindow):

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.isLoaded = False
		self.type = TYPE_ITEM
		self.items = {}  # slot -> (cell, vnum)
		self.toolTipItem = None
		self.helpToolTip = None
		self.question = None
		self.startPos = (0, 0)

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def Destroy(self):
		self.question = None
		self.helpToolTip = None
		self.toolTipItem = None
		self.ClearDictionary()
		self.isLoaded = False

	def __Load(self):
		if self.isLoaded:
			return True
		try:
			ui.PythonScriptLoader().LoadScriptFile(self, "UIScript/ChangeLookWindow.py")
			self.wndItem = self.GetChild("ChangeLookSlot")
			self.wndPass = self.GetChild("ChangeLookSlot_PassYangItem")
			self.titleName = self.GetChild("TitleName")
			self.cost = self.GetChild("Cost")
			self.helpButton = self.GetChild("ChangeLookToolTipButton")
			self.GetChild("TitleBar").SetCloseEvent(ui.__mem_func__(self.Close))
			self.GetChild("AcceptButton").SetEvent(ui.__mem_func__(self.__Accept))
			self.GetChild("CancelButton").SetEvent(ui.__mem_func__(self.Close))
		except Exception, e:
			import dbg
			dbg.TraceError("ChangeLookWindow.Load: %s" % str(e))
			return False

		self.wndItem.SetSelectEmptySlotEvent(ui.__mem_func__(self.__DropOnSlot))
		self.wndItem.SetSelectItemSlotEvent(ui.__mem_func__(self.__TakeOut))
		self.wndItem.SetUnselectItemSlotEvent(ui.__mem_func__(self.__TakeOut))
		self.wndItem.SetUseSlotEvent(ui.__mem_func__(self.__TakeOut))
		self.wndItem.SetOverInItemEvent(ui.__mem_func__(self.__OverIn))
		self.wndItem.SetOverOutItemEvent(ui.__mem_func__(self.__OverOut))
		self.wndPass.SetSelectEmptySlotEvent(ui.__mem_func__(self.__DropOnPass))
		self.wndPass.SetSelectItemSlotEvent(ui.__mem_func__(self.__TakeOutPass))
		self.wndPass.SetUnselectItemSlotEvent(ui.__mem_func__(self.__TakeOutPass))
		self.wndPass.SetUseSlotEvent(ui.__mem_func__(self.__TakeOutPass))
		self.wndPass.SetOverInItemEvent(ui.__mem_func__(self.__OverInPass))
		self.wndPass.SetOverOutItemEvent(ui.__mem_func__(self.__OverOut))
		self.isLoaded = True
		return True

	def SetItemToolTip(self, toolTip):
		self.toolTipItem = toolTip

	def Open(self, type):
		if not self.__Load():
			return
		self.type = TYPE_MOUNT if type == TYPE_MOUNT else TYPE_ITEM
		self.items = {}
		self.titleName.SetText(TITLE[self.type])
		self.helpToolTip = uiToolTip.ToolTip()
		self.helpToolTip.SetTitle(TITLE[self.type])
		self.helpToolTip.AppendSpace(5)
		for line in HELP[self.type]:
			self.helpToolTip.AutoAppendTextLine(line)
		self.helpToolTip.AlignHorizonalCenter()
		self.helpButton.SetToolTipWindow(self.helpToolTip)
		(x, y, z) = player.GetMainCharacterPosition()
		self.startPos = (x, y)
		self.Refresh()
		self.SetCenterPosition()
		self.Show()
		self.SetTop()

	def Close(self):
		if self.question:
			self.question.Close()
			self.question = None
		if self.IsShow():
			net.SendChatPacket('/transmutacja cancel')
		self.items = {}
		self.Hide()
		if self.toolTipItem:
			self.toolTipItem.HideToolTip()

	def ServerClose(self):
		self.items = {}
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def OnUpdate(self):
		(x, y, z) = player.GetMainCharacterPosition()
		if abs(x - self.startPos[0]) > LIMIT_RANGE or abs(y - self.startPos[1]) > LIMIT_RANGE:
			self.Close()

	# ---- the server -------------------------------------------------------------------------
	def SetSlot(self, slot, cell, vnum):
		self.items[slot] = (cell, vnum)
		self.Refresh()

	def DelSlot(self, slot):
		if slot in self.items:
			del self.items[slot]
		self.Refresh()

	def Refresh(self):
		if not self.isLoaded:
			return
		for slot in (SLOT_LEFT, SLOT_RIGHT):
			if slot in self.items:
				cell, vnum = self.items[slot]
				self.wndItem.SetItemSlot(slot, vnum, 0)
				MarkSlot(self.wndItem, slot, cell)
			else:
				self.wndItem.ClearSlot(slot)
		if SLOT_PASS in self.items:
			self.wndPass.SetItemSlot(0, self.items[SLOT_PASS][1], 0)
			self.cost.SetText(TEXT_COST % Money(0))
		else:
			self.wndPass.ClearSlot(0)
			self.cost.SetText(TEXT_COST % Money(PRICE[self.type]))
		self.wndItem.RefreshSlot()
		self.wndPass.RefreshSlot()

	# ---- the player -------------------------------------------------------------------------
	def __AttachedBagCell(self):
		if not mouseModule.mouseController.isAttached():
			return -1
		if mouseModule.mouseController.GetAttachedType() != player.SLOT_TYPE_INVENTORY:
			mouseModule.mouseController.DeattachObject()
			chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_NOT_BAG)
			return -1
		cell = mouseModule.mouseController.GetAttachedSlotNumber()
		mouseModule.mouseController.DeattachObject()
		if cell >= getattr(player, "EQUIPMENT_SLOT_START", 1 << 16):
			chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_NOT_BAG)
			return -1
		return cell

	def __DropOnSlot(self, slot):
		cell = self.__AttachedBagCell()
		if cell < 0:
			return
		if slot == SLOT_RIGHT and SLOT_LEFT not in self.items:
			chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_PUT_LEFT)
			return
		snd.PlaySound("sound/ui/drop.wav")
		net.SendChatPacket('/transmutacja in %d %d' % (slot, cell))

	def __DropOnPass(self, slot):
		cell = self.__AttachedBagCell()
		if cell < 0:
			return
		snd.PlaySound("sound/ui/drop.wav")
		net.SendChatPacket('/transmutacja in %d %d' % (SLOT_PASS, cell))

	def __TakeOut(self, slot):
		if mouseModule.mouseController.isAttached():
			self.__DropOnSlot(slot)
			return
		if slot in self.items:
			snd.PlaySound("sound/ui/pick.wav")
			net.SendChatPacket('/transmutacja out %d' % slot)

	def __TakeOutPass(self, slot):
		if mouseModule.mouseController.isAttached():
			self.__DropOnPass(slot)
			return
		if SLOT_PASS in self.items:
			net.SendChatPacket('/transmutacja out %d' % SLOT_PASS)

	def __OverIn(self, slot):
		if self.toolTipItem and slot in self.items:
			self.toolTipItem.SetInventoryItem(self.items[slot][0])

	def __OverInPass(self, slot):
		if self.toolTipItem and SLOT_PASS in self.items:
			self.toolTipItem.SetInventoryItem(self.items[SLOT_PASS][0])

	def __OverOut(self):
		if self.toolTipItem:
			self.toolTipItem.HideToolTip()

	def __Accept(self):
		if SLOT_LEFT not in self.items or SLOT_RIGHT not in self.items:
			chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_PUT_BOTH)
			return
		question = uiCommon.QuestionDialog()
		question.SetText(TEXT_QUESTION)
		question.SetAcceptEvent(ui.__mem_func__(self.__AcceptYes))
		question.SetCancelEvent(ui.__mem_func__(self.__AcceptNo))
		question.Open()
		self.question = question

	def __AcceptYes(self):
		if self.question:
			self.question.Close()
			self.question = None
		net.SendChatPacket('/transmutacja accept')

	def __AcceptNo(self):
		if self.question:
			self.question.Close()
			self.question = None


_window = {'wnd': None}


def GetWindow(toolTip=None):
	if not _window['wnd']:
		_window['wnd'] = ChangeLookWindow()
	if toolTip:
		_window['wnd'].SetItemToolTip(toolTip)
	return _window['wnd']


def DestroyWindow():
	wnd = _window['wnd']
	_window['wnd'] = None
	if wnd:
		try:
			wnd.Hide()
			wnd.Destroy()
		except Exception:
			pass


# ---- game.py's server commands (it binds its own methods and calls these) -------------------------
def OnOpen(toolTip, type):
	try:
		type = int(type)
	except (TypeError, ValueError):
		type = TYPE_ITEM
	GetWindow(toolTip).Open(type)


def OnSet(slot, cell, vnum):
	wnd = _window['wnd']
	if wnd:
		try:
			wnd.SetSlot(int(slot), int(cell), int(vnum))
		except (TypeError, ValueError):
			pass


def OnDel(slot):
	wnd = _window['wnd']
	if wnd:
		try:
			wnd.DelSlot(int(slot))
		except (TypeError, ValueError):
			pass


def OnClose():
	wnd = _window['wnd']
	if wnd:
		wnd.ServerClose()


def OnDone():
	wnd = _window['wnd']
	if wnd:
		wnd.Refresh()
