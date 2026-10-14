# MT2009_PLUS_GAYA_SHOP_WINDOW_V1: Portowy Sklep Gaya (Statua Wojownika, Port Nowego Kontynentu) in its own window,
# as in the official game (GF uiscript/gemshopwindow.py: 3 rows of 3 slots on gemshop_backimg.sub, a Gaya price under
# every slot, the time left to the next offer, the refresh button) plus our Gaya balance and the Rozszerzenie / Reset
# buttons. The images d:/ymir work/ui/gemshop/*.sub and d:/ymir work/ui/gemshop_001.dds are GF's, shipped in the root
# pack (client-2.0.30/atlas); the buttons and the slot base are the ones every window uses.
#
# The server half is the quest ygaya (linux-port/docker/game/quest/ygaya.quest), which keeps all the shop's rules:
#   server -> client  "YGAYA open <quest index> <gaya> <seconds to the new offer> <unlocked> <extensions> <resets>",
#                     "YGAYA slot <1-9> <state 0 open / 1 bought / 2 locked> <vnum> <count> <price> <extensions needed>",
#                     "YGAYA show" (open / refresh the window), "YGAYA close"
#   client -> server  the quest's "button" event (event.QuestButtonClick(<quest index>)) and its input() answered
#                     with a number: 1-9 buy the slot, 11-19 unlock the slot, 20 reset the offer, 21 send the state
#                     again. The quest window of that input is not shown (game.OpenQuestWindow asks ConsumeQuestWindow).
#
# Python 2.7 as the client has it; the texts are CP1250 escapes.

import app
import chat
import event
import item
import net
import ui
import uiCommon

TEXT_TITLE = "Sklep Gaya"
TEXT_TIME = "Nowa oferta:"
TEXT_BALANCE = "Twoja Gaya: %s"
TEXT_EXPAND = "Rozszerzenie"
TEXT_RESET = "Reset oferty"
TEXT_BOUGHT = "kupione"
TEXT_LOCKED = "zablok."
TEXT_ASK_BUY = "Kupi\xe6 %s za %s Gaya?"
TEXT_ASK_BUY2 = "Z ka\xbfdego slotu kupisz jedn\xb9 rzecz na ofert\xea."
TEXT_ASK_UNLOCK = "Odblokowa\xe6 slot %d na sta\xb3e?"
TEXT_ASK_UNLOCK2 = "Koszt: Rozszerzenie Sklepu Gaya x%d (masz %d)."
TEXT_ASK_RESET = "Wylosowa\xe6 now\xb9 ofert\xea od razu?"
TEXT_ASK_RESET2 = "Koszt: Reset Sklepu Gaya x1 (masz %d)."
TEXT_NO_GAYA = "Masz za ma\xb3o Gaya (potrzeba %s)."
TEXT_NO_EXT = "Masz za ma\xb3o Rozszerze\xf1 Sklepu Gaya (potrzeba %d)."
TEXT_NO_RESET = "Potrzebujesz Resetu Sklepu Gaya."
TEXT_ALL_OPEN = "Wszystkie sloty sklepu s\xb9 ju\xbf odblokowane."
TEXT_IS_BOUGHT = "Ten slot ju\xbf kupiono - poczekaj na now\xb9 ofert\xea."
TEXT_TIP_LOCKED = "Slot zablokowany: odblokuje go Rozszerzenie Sklepu Gaya x%d."
TEXT_TIP_BOUGHT = "Kupione - nowa oferta za %s."
TEXT_TIP_PRICE = "Cena: %s Gaya"
TEXT_TIP_RESET = "Reset oferty (Reset Sklepu Gaya)"

GEM_PATH = "d:/ymir work/ui/gemshop/"
GEM_ICON = GEM_PATH + "gemshop_gemicon.sub"
SLOT_BASE = "d:/ymir work/ui/public/slot_base.sub"

EXT_VNUM = 39064
RESET_VNUM = 39063

BOARD_WIDTH = 200
BOARD_HEIGHT = 292
DX = 16                       # GF's 168 wide board, centred in ours
SLOT_X = (22, 67, 112)
SLOT_Y = (0, 58, 116)
SLOTS_Y = 60

COLOR_PRICE = 0xffffffff
COLOR_BOUGHT = 0xff9a9a9a
COLOR_LOCKED = 0xffd07070
COLOR_BALANCE = 0xfff1e6c0

QUEST_WINDOW_WAIT = 5.0       # seconds the input window of a click is waited for

_state = {
	'window': None,
	'qid': -1,
	'interface': None,
	'pending': None,      # the number to answer the quest's input() with
	'pendingTime': 0.0,
}


def ToInt(value, default=0):
	try:
		return int(value)
	except (TypeError, ValueError):
		return default


def FormatNumber(n):
	s = str(abs(n))
	parts = []
	while len(s) > 3:
		parts.insert(0, s[-3:])
		s = s[:-3]
	parts.insert(0, s)
	return ("-" if n < 0 else "") + " ".join(parts)


def FormatTime(sec):
	sec = max(0, int(sec))
	return "%d:%02d:%02d" % (sec / 3600, (sec / 60) % 60, sec % 60)


def SetInterface(interface):
	try:
		from _weakref import proxy
		_state['interface'] = proxy(interface)
	except Exception:
		_state['interface'] = None


def Send(action):
	# the quest's "button" event, then its input() gets the number (ConsumeQuestWindow)
	if _state['qid'] < 0:
		return
	_state['pending'] = str(action)
	_state['pendingTime'] = app.GetTime()
	event.QuestButtonClick(_state['qid'])


def ConsumeQuestWindow(skin, idx):
	"""game.OpenQuestWindow: True when this is the input window of a shop click - answered here, never shown."""
	pending = _state['pending']
	if pending is None:
		return False
	_state['pending'] = None
	if app.GetTime() - _state['pendingTime'] > QUEST_WINDOW_WAIT:
		return False
	try:
		event.ClearEventSet(idx)
	except Exception:
		pass
	net.SendQuestInputStringPacket(pending)
	return True


class GayaShopWindow(ui.BoardWithTitleBar):

	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)
		self.widgets = []
		self.priceLines = []
		self.priceIcons = []
		self.slots = {}
		self.gaya = 0
		self.unlocked = 0
		self.extensions = 0
		self.resets = 0
		self.endTime = 0.0
		self.askedRefresh = False
		self.dialog = None
		self.tooltipItem = None
		self.AddFlag('movable')
		self.AddFlag('float')
		self.SetSize(BOARD_WIDTH, BOARD_HEIGHT)
		self.SetTitleName(TEXT_TITLE)
		self.SetCloseEvent(ui.__mem_func__(self.Close))
		self.__Build()
		self.SetCenterPosition()

	def __del__(self):
		ui.BoardWithTitleBar.__del__(self)

	def __Image(self, x, y, path):
		image = ui.ImageBox()
		image.SetParent(self)
		image.SetPosition(x, y)
		image.LoadImage(path)
		image.Show()
		self.widgets.append(image)
		return image

	def __Label(self, x, y, text, center=False, color=None):
		line = ui.TextLine()
		line.SetParent(self)
		line.SetPosition(x, y)
		if center:
			line.SetHorizontalAlignCenter()
		line.SetText(text)
		if color is not None:
			line.SetPackedFontColor(color)
		line.Show()
		self.widgets.append(line)
		return line

	def __Button(self, x, y, text, event):
		button = ui.Button()
		button.SetParent(self)
		button.SetPosition(x, y)
		button.SetUpVisual('d:/ymir work/ui/public/large_button_01.sub')
		button.SetOverVisual('d:/ymir work/ui/public/large_button_02.sub')
		button.SetDownVisual('d:/ymir work/ui/public/large_button_03.sub')
		button.SetText(text)
		button.SAFE_SetEvent(event)
		button.Show()
		self.widgets.append(button)
		return button

	def __Build(self):
		# GF uiscript/gemshopwindow.py, moved DX to the right
		self.__Image(14 + DX, 31, GEM_PATH + "gemshop_backimg.sub")
		self.__Label(74 + DX, 35, TEXT_TIME, True)
		self.timeLine = self.__Label(132 + DX, 35, "", True)

		slot = ui.SlotWindow()
		slot.SetParent(self)
		slot.SetPosition(DX, SLOTS_Y)
		slot.SetSize(160, 150)
		for i in xrange(9):
			slot.AppendSlot(i, SLOT_X[i % 3], SLOT_Y[i / 3], 32, 32)
		slot.SetSlotBaseImage(SLOT_BASE, 1.0, 1.0, 1.0, 1.0)
		slot.SetSelectItemSlotEvent(ui.__mem_func__(self.OnSelectSlot))
		slot.SetSelectEmptySlotEvent(ui.__mem_func__(self.OnSelectSlot))
		slot.SetOverInItemEvent(ui.__mem_func__(self.OnOverInSlot))
		slot.SetOverOutItemEvent(ui.__mem_func__(self.OnOverOutSlot))
		slot.Show()
		self.slotWindow = slot

		for i in xrange(9):
			x = SLOT_X[i % 3] - 3 + DX
			y = 100 + 58 * (i / 3)
			self.priceIcons.append(self.__Image(x, y, GEM_ICON))
			self.priceLines.append(self.__Label(x + 28, y, "", True))

		refresh = ui.Button()
		refresh.SetParent(self)
		refresh.SetPosition(13 + DX, 30)
		refresh.SetUpVisual(GEM_PATH + "gemshop_refreshbutton_up.sub")
		refresh.SetOverVisual(GEM_PATH + "gemshop_refreshbutton_over.sub")
		refresh.SetDownVisual(GEM_PATH + "gemshop_refreshbutton_down.sub")
		refresh.SetToolTipText(TEXT_TIP_RESET, 0, -20)
		refresh.SAFE_SetEvent(self.OnReset)
		refresh.Show()
		self.widgets.append(refresh)

		self.__Image(14 + DX, 240, GEM_ICON)
		self.balanceLine = self.__Label(32 + DX, 238, "", False, COLOR_BALANCE)
		self.__Button(8, 258, TEXT_EXPAND, self.OnExpand)
		self.__Button(BOARD_WIDTH - 8 - 88, 258, TEXT_RESET, self.OnReset)

	def SetItemToolTip(self, tooltipItem):
		self.tooltipItem = tooltipItem

	def SetHeader(self, gaya, left, unlocked, extensions, resets):
		self.gaya = gaya
		self.unlocked = unlocked
		self.extensions = extensions
		self.resets = resets
		self.endTime = app.GetTime() + max(0, left)
		self.askedRefresh = False
		self.balanceLine.SetText(TEXT_BALANCE % FormatNumber(gaya))

	def SetSlot(self, slot, state, vnum, count, price, need):
		self.slots[slot] = (state, vnum, count, price, need)

	def Refresh(self):
		for i in xrange(9):
			state, vnum, count, price, need = self.slots.get(i + 1, (2, 0, 0, 0, 0))
			line = self.priceLines[i]
			if state == 2:
				self.slotWindow.SetItemSlot(i, EXT_VNUM, need, (0.5, 0.5, 0.5, 1.0))
				self.priceIcons[i].Hide()
				line.SetText(TEXT_LOCKED)
				line.SetPackedFontColor(COLOR_LOCKED)
			elif state == 1:
				self.slotWindow.SetItemSlot(i, vnum, count, (0.4, 0.4, 0.4, 1.0))
				self.priceIcons[i].Hide()
				line.SetText(TEXT_BOUGHT)
				line.SetPackedFontColor(COLOR_BOUGHT)
			else:
				self.slotWindow.SetItemSlot(i, vnum, count)
				self.priceIcons[i].Show()
				line.SetText(FormatNumber(price))
				line.SetPackedFontColor(COLOR_PRICE)
		self.slotWindow.RefreshSlot()

	def OnUpdate(self):
		left = self.endTime - app.GetTime()
		self.timeLine.SetText(FormatTime(left))
		if left <= 0 and not self.askedRefresh and self.IsShow():
			self.askedRefresh = True
			Send(21)

	def __CloseDialog(self):
		dialog = self.dialog
		self.dialog = None
		if dialog:
			try:
				dialog.Close()
			except Exception:
				pass

	def __Ask(self, text1, text2, accept):
		self.__CloseDialog()
		dialog = uiCommon.QuestionDialog2()
		dialog.SetText1(text1)
		dialog.SetText2(text2)
		dialog.SetAcceptEvent(accept)
		dialog.SetCancelEvent(ui.__mem_func__(self.__CloseDialog))
		dialog.Open()
		self.dialog = dialog

	def __AskUnlock(self, slot, need):
		if self.extensions < need:
			chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_NO_EXT % need)
			return
		self.__Ask(TEXT_ASK_UNLOCK % slot, TEXT_ASK_UNLOCK2 % (need, self.extensions),
			lambda arg=10 + slot: self.__Accept(arg))

	def __Accept(self, action):
		self.__CloseDialog()
		Send(action)

	def OnSelectSlot(self, i):
		slot = i + 1
		state, vnum, count, price, need = self.slots.get(slot, (2, 0, 0, 0, 0))
		if state == 2:
			self.__AskUnlock(slot, need)
			return
		if state == 1:
			chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_IS_BOUGHT)
			return
		if not vnum:
			return
		if self.gaya < price:
			chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_NO_GAYA % FormatNumber(price))
			return
		item.SelectItem(vnum)
		name = item.GetItemName()
		if count > 1:
			name = "%s x%d" % (name, count)
		self.__Ask(TEXT_ASK_BUY % (name, FormatNumber(price)), TEXT_ASK_BUY2, lambda arg=slot: self.__Accept(arg))

	def OnOverInSlot(self, i):
		tooltip = self.tooltipItem
		if not tooltip:
			return
		state, vnum, count, price, need = self.slots.get(i + 1, (2, 0, 0, 0, 0))
		if state == 2:
			tooltip.SetItemToolTip(EXT_VNUM)
			tooltip.AppendSpace(5)
			tooltip.AppendTextLine(TEXT_TIP_LOCKED % need, COLOR_LOCKED)
		elif vnum:
			tooltip.SetItemToolTip(vnum)
			tooltip.AppendSpace(5)
			if state == 1:
				tooltip.AppendTextLine(TEXT_TIP_BOUGHT % FormatTime(self.endTime - app.GetTime()), COLOR_BOUGHT)
			else:
				tooltip.AppendTextLine(TEXT_TIP_PRICE % FormatNumber(price), COLOR_BALANCE)
		else:
			return
		tooltip.ResizeToolTip()
		tooltip.ShowToolTip()

	def OnOverOutSlot(self):
		if self.tooltipItem:
			self.tooltipItem.HideToolTip()

	def OnExpand(self):
		for slot in xrange(1, 10):
			state, vnum, count, price, need = self.slots.get(slot, (0, 0, 0, 0, 0))
			if state == 2:
				self.__AskUnlock(slot, need)
				return
		chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_ALL_OPEN)

	def OnReset(self):
		if self.resets < 1:
			chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_NO_RESET)
			return
		self.__Ask(TEXT_ASK_RESET, TEXT_ASK_RESET2 % self.resets, lambda arg=20: self.__Accept(arg))

	def Open(self):
		self.Show()
		self.SetTop()

	def Close(self):
		self.__CloseDialog()
		self.OnOverOutSlot()
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def Destroy(self):
		self.__CloseDialog()
		self.tooltipItem = None
		self.slotWindow = None
		self.widgets = []
		self.priceLines = []
		self.priceIcons = []
		self.Hide()


def __Window():
	window = _state['window']
	if window is None:
		import uiminigameutil
		window = uiminigameutil.SafeCreate(GayaShopWindow, TEXT_TITLE)
		if window is None:
			return None
		interface = _state['interface']
		try:
			if interface is not None:
				window.SetItemToolTip(interface.tooltipItem)
		except Exception:
			pass
		_state['window'] = window
	return window


def OnCommand(*args):
	if not args:
		return
	sub, rest = args[0], args[1:]
	try:
		if sub == 'open' and len(rest) >= 6:
			_state['qid'] = ToInt(rest[0], -1)
			window = __Window()
			if window is not None:
				window.SetHeader(ToInt(rest[1]), ToInt(rest[2]), ToInt(rest[3]), ToInt(rest[4]), ToInt(rest[5]))
		elif sub == 'slot' and len(rest) >= 6:
			window = __Window()
			if window is not None:
				window.SetSlot(ToInt(rest[0]), ToInt(rest[1]), ToInt(rest[2]), ToInt(rest[3]), ToInt(rest[4]), ToInt(rest[5]))
		elif sub == 'show':
			window = __Window()
			if window is not None:
				window.Refresh()
				if not window.IsShow():
					window.Open()
		elif sub == 'close':
			window = _state['window']
			if window is not None:
				window.Close()
	except Exception:
		import dbg
		import sys
		dbg.TraceError('uiygaya.OnCommand %s: %s' % (str(args), str(sys.exc_info()[1])))


def DestroyWindow():
	window = _state['window']
	_state['window'] = None
	_state['pending'] = None
	_state['qid'] = -1
	if window is not None:
		window.Destroy()
