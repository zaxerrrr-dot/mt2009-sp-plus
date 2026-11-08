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
# "Najemnicy -> Lista i rozkazy -> Rozkazy" does the same.
#
# Python 2.7 as the client has it; no exe call beyond the stock ui module.

import net
import ui

ORDER_NAMES = ('Za mn\xb9', 'St\xf3j tutaj', 'Bij m\xf3j cel', 'Walcz sam w pobli\xbfu')
ORDER_WORDS = ('za_mna', 'stoj', 'bij', 'sam')
LOOT_OFF = 'Nie podno\x9c \xb3upu'
LOOT_ON = 'Podno\x9c \xb3up'
TITLE = 'Rozkazy: %s'
TITLE_PLAIN = 'Rozkazy najemnika'
ALL_LABEL = 'Wszyscy najemnicy:'
NOW_TEXT = 'Teraz: %s, %s.'
NOW_LOOT_ON = 'podnosi \xb3up'
NOW_LOOT_OFF = 'nie podnosi \xb3upu'

BUTTON = ('d:/ymir work/ui/public/middle_button_01.sub', 'd:/ymir work/ui/public/middle_button_02.sub',
		'd:/ymir work/ui/public/middle_button_03.sub')
WIDTH = 300
HEIGHT = 222
BUTTON_W = 130
COLOR_ACTIVE = 0xFFFFD27F
COLOR_TEXT = 0xFFE8DCC8

_state = {'window': None}


class OrdersWindow(ui.BoardWithTitleBar):

	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)
		self.slot = 0
		self.name = ''
		self.keep = []
		self.orderButtons = []
		self.AddFlag('movable')
		self.AddFlag('float')
		self.SetSize(WIDTH, HEIGHT)
		self.SetTitleName(TITLE_PLAIN)
		self.SetCloseEvent(ui.__mem_func__(self.Close))
		self.nowText = self.__Text(WIDTH / 2, 34, '', True)
		# one mercenary: the four orders in two columns, the loot switch
		for i in xrange(4):
			x = 16 + (i % 2) * (BUTTON_W + 12)
			y = 52 + (i / 2) * 26
			self.orderButtons.append(self.__Button(x, y, ORDER_NAMES[i], self.__OnOrder, i, False))
		self.__Button(16, 104, LOOT_OFF, self.__OnLoot, 0, False)
		self.__Button(16 + BUTTON_W + 12, 104, LOOT_ON, self.__OnLoot, 1, False)
		# all of them
		self.__Text(16, 136, ALL_LABEL, False)
		for i in xrange(4):
			x = 16 + (i % 2) * (BUTTON_W + 12)
			y = 154 + (i / 2) * 26
			self.__Button(x, y, ORDER_NAMES[i], self.__OnOrder, i, True)
		self.SetCenterPosition()

	def __del__(self):
		ui.BoardWithTitleBar.__del__(self)

	def __Text(self, x, y, text, center):
		line = ui.TextLine()
		line.SetParent(self)
		line.AddFlag('not_pick')
		line.SetPosition(x, y)
		if center:
			line.SetHorizontalAlignCenter()
		line.SetText(text)
		line.SetPackedFontColor(COLOR_TEXT)
		line.Show()
		self.keep.append(line)
		return line

	def __Button(self, x, y, text, event, arg, everybody):
		button = ui.Button()
		button.SetParent(self)
		button.SetPosition(x, y)
		button.SetUpVisual(BUTTON[0])
		button.SetOverVisual(BUTTON[1])
		button.SetDownVisual(BUTTON[2])
		button.SetText(text)
		button.SetEvent(ui.__mem_func__(event), arg, everybody)
		button.Show()
		self.keep.append(button)
		return button

	def Destroy(self):
		self.keep = []
		self.orderButtons = []
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
		self.nowText.SetText(NOW_TEXT % (ORDER_NAMES[order] if 0 <= order < len(ORDER_NAMES) else ORDER_NAMES[0],
				NOW_LOOT_ON if loot else NOW_LOOT_OFF))
		for i, button in enumerate(self.orderButtons):
			try:
				button.SetTextColor(COLOR_ACTIVE if i == order else COLOR_TEXT)
			except Exception:
				pass

	def __Who(self, everybody):
		return 'wszyscy' if everybody else str(self.slot)

	def __OnOrder(self, order, everybody):
		if not everybody and self.slot <= 0:
			return
		net.SendChatPacket('/najemnicy rozkaz %s %s' % (self.__Who(everybody), ORDER_WORDS[order]))

	def __OnLoot(self, loot, everybody):
		if not everybody and self.slot <= 0:
			return
		net.SendChatPacket('/najemnicy rozkaz %s %s' % (self.__Who(everybody), 'podnos' if loot else 'nie_podnos'))


def _OrderOf(slot):
	try:
		import uisidekickinventory
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
