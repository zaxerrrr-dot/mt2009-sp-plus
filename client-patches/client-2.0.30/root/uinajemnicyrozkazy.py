# MT2009_PLUS_NAJEMNICY_V3: the orders of the player's mercenaries ("Najemnicy",
# playerbot_najemnicy.h on the server) - a small board the target board's
# "Rozkazy" button opens on one of the player's own summoned mercenaries
# (uitarget.py). Each button sends
#
#   /najemnicy rozkaz <slot|wszyscy> <za_mna|stoj|bij|sam|nie_podnos|podnos>
#
# and the server keeps the order per mercenary (also after a logout) and names
# it back in "NajemnikVids <slot>:<vid>:<hex name>:<order>:<loot>,..."
# (uisidekickinventory.py, NajemnikOrderOfSlot), which this board shows. The
# second row gives the same order to all of them ("Wszyscy"). The letter
# "Najemnicy -> Lista i rozkazy -> Rozkazy" does the same. MT2009_PLUS_NAJEMNICY_V5: the Najemnicy tab of
# the collector's window (uinajemnicykolekcjoner.py) opens it for any of the player's mercenaries, summoned or not;
# "Stoj tutaj" is the passive order now (stands, attacks nothing, no skills, no buffs - the first summon of a
# session starts in it).
#
# Python 2.7 as the client has it; no exe call beyond the stock ui module.

import ui

import uifarmsession as fs

ORDER_NAMES = ('Za mn\xb9', 'St\xf3j tutaj', 'Bij m\xf3j cel', 'Walcz sam w pobli\xbfu')
ORDER_WORDS = ('za_mna', 'stoj', 'bij', 'sam')
LOOT_OFF = 'Nie podno\x9c \xb3upu'
LOOT_ON = 'Podno\x9c \xb3up'
TITLE = 'Rozkazy: %s'
TITLE_PLAIN = 'Rozkazy najemnika'
ONE_LABEL = 'Ten najemnik'
ALL_LABEL = 'Wszyscy najemnicy'
NOW_TEXT = 'Teraz: %s, %s.'
NOW_LOOT_ON = 'podnosi \xb3up'
NOW_LOOT_OFF = 'nie podnosi \xb3upu'

# MT2009_PLUS_NAJEMNICY_V5: the look of "Sesja farmienia" (uifarmsession.py) - flat buttons, framed sections with
# header strips; the current order and the loot switch are lit (STYLE_TAB_ON). The orders go through the mercenaries'
# command line (uinajemnicykolekcjoner.SendNaj, the companion windows' queue); the order shown comes from NajemnikVids
# (a summoned one) or from the Najemnicy tab's state (NAJP - also one not summoned).
WIDTH = 320
HEIGHT = 262
PAD = 10
INNER = WIDTH - 2 * PAD
HEAD_H = 22
BUTTON_H = 20
GAP = 6
BUTTON_W = (INNER - 2 * PAD - GAP) // 2

_state = {'window': None}


def _Send(text):
	try:
		import uinajemnicykolekcjoner
		uinajemnicykolekcjoner.SendNaj(text)
	except Exception:
		import net
		net.SendChatPacket('/najemnicy ' + text)


class OrdersWindow(ui.BoardWithTitleBar):

	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)
		self.slot = 0
		self.name = ''
		self.keep = []
		self.orderButtons = []
		self.lootButtons = []
		self.AddFlag('movable')
		self.AddFlag('float')
		self.SetSize(WIDTH, HEIGHT)
		self.SetTitleName(TITLE_PLAIN)
		self.SetCloseEvent(ui.__mem_func__(self.Close))
		area = ui.Window()
		area.SetParent(self)
		area.SetPosition(PAD, 32)
		area.SetSize(INNER, HEIGHT - 42)
		area.AddFlag('attach')
		area.Show()
		self.keep.append(area)
		# one mercenary: the four orders in two columns, the loot switch, what it does now
		box = self.__Section(area, 0, 132, ONE_LABEL)
		for i in xrange(4):
			x = PAD + (i % 2) * (BUTTON_W + GAP)
			y = HEAD_H + 8 + (i // 2) * (BUTTON_H + 4)
			self.orderButtons.append(self.__Button(box, x, y, ORDER_NAMES[i], self.__OnOrder, i, False))
		y = HEAD_H + 8 + 2 * (BUTTON_H + 4)
		self.lootButtons.append(self.__Button(box, PAD, y, LOOT_OFF, self.__OnLoot, 0, False))
		self.lootButtons.append(self.__Button(box, PAD + BUTTON_W + GAP, y, LOOT_ON, self.__OnLoot, 1, False))
		self.nowText = fs._Text(box, INNER // 2, y + BUTTON_H + 13, '', fs.COLOR_DIM, 'center')
		self.keep.append(self.nowText)
		# all of them
		box = self.__Section(area, 138, 82, ALL_LABEL)
		for i in xrange(4):
			x = PAD + (i % 2) * (BUTTON_W + GAP)
			y = HEAD_H + 8 + (i // 2) * (BUTTON_H + 4)
			self.__Button(box, x, y, ORDER_NAMES[i], self.__OnOrder, i, True)
		self.SetCenterPosition()

	def __del__(self):
		ui.BoardWithTitleBar.__del__(self)

	def __Section(self, parent, y, height, title):
		box = fs._Frame(INNER, height, fs.COLOR_TAB_BORDER, fs.COLOR_COLUMN_FILL)
		box.SetParent(parent)
		box.SetPosition(0, y)
		box.AddFlag('attach')
		box.Show()
		self.keep.append(box)
		self.keep.append(fs._Rect(box, 1, 1, INNER - 2, HEAD_H - 1, fs.COLOR_HEAD_FILL))
		self.keep.append(fs._Rect(box, 1, HEAD_H, INNER - 2, 1, fs.COLOR_HEAD_LINE))
		self.keep.append(fs._Text(box, INNER // 2, HEAD_H // 2 + 1, title, fs.COLOR_HEAD_TEXT, 'center', True))
		return box

	def __Button(self, parent, x, y, text, event, arg, everybody):
		button = fs._FlatButton(BUTTON_W, BUTTON_H, text, fs.STYLE_BUTTON, ui.__mem_func__(event), arg, everybody)
		button.SetParent(parent)
		button.SetPosition(x, y)
		button.Show()
		self.keep.append(button)
		return button

	def Destroy(self):
		self.keep = []
		self.orderButtons = []
		self.lootButtons = []
		self.Hide()

	def Close(self):
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def SetTarget(self, slot, name):
		self.slot = slot
		self.name = name or ''
		self.SetTitleName(TITLE % self.name if self.name else TITLE_PLAIN)
		self.Refresh()

	def Refresh(self):
		order, loot = _OrderOf(self.slot)
		if not 0 <= order < len(ORDER_NAMES):
			order = 0
		self.nowText.SetText(NOW_TEXT % (ORDER_NAMES[order], NOW_LOOT_ON if loot else NOW_LOOT_OFF))
		for i, button in enumerate(self.orderButtons):
			button.SetStyle(fs.STYLE_TAB_ON if i == order else fs.STYLE_BUTTON)
		for i, button in enumerate(self.lootButtons):
			button.SetStyle(fs.STYLE_TAB_ON if (i == 1) == bool(loot) else fs.STYLE_BUTTON)

	def __Who(self, everybody):
		return 'wszyscy' if everybody else str(self.slot)

	def __OnOrder(self, order, everybody):
		if not everybody and self.slot <= 0:
			return
		_Send('rozkaz %s %s' % (self.__Who(everybody), ORDER_WORDS[order]))

	def __OnLoot(self, loot, everybody):
		if not everybody and self.slot <= 0:
			return
		_Send('rozkaz %s %s' % (self.__Who(everybody), 'podnos' if loot else 'nie_podnos'))


def _OrderOf(slot):
	"""The summoned one's order (NajemnikVids), else the Najemnicy tab's (NAJP), else "Za mna" with loot."""
	try:
		import uisidekickinventory
		import uinajemnicykolekcjoner
		if int(slot) in getattr(uisidekickinventory, '_najemnikOrders', {}):
			return uisidekickinventory.NajemnikOrderOfSlot(slot)
		known = uinajemnicykolekcjoner.OrderOfSlot(slot)
		if known is not None:
			return known
		return uisidekickinventory.NajemnikOrderOfSlot(slot)
	except Exception:
		return (0, 1)


def Open(slot, name=''):
	"""The board for the mercenary of a slot (the target board's "Rozkazy")."""
	try:
		slot = int(slot)
	except (TypeError, ValueError):
		return
	if slot <= 0:
		return
	window = _state['window']
	if window is None:
		window = OrdersWindow()
		_state['window'] = window
	window.SetTarget(slot, name)
	window.Show()
	window.SetTop()


def Refresh():
	"""NajemnikVids came: the order shown follows the server's."""
	window = _state['window']
	if window is not None and window.IsShow():
		window.Refresh()


def DestroyWindow():
	"""The game window's end (a warp, the character select)."""
	window = _state['window']
	if window is not None:
		window.Destroy()
	_state['window'] = None
