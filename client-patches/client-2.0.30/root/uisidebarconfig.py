# MT2009_PLUS_SIDEBAR_CONFIG_V1 - the inventory's side bar, set up by each player (the owner, 10 November 2026: "today
# every button is added automatically - let each player choose which buttons appear and their order, e.g. without
# 'Usun misje'").
#
# The side bar (uiinventory.SidebarWindow) lists its buttons in SidebarWindow.BUTTONS - that tuple stays the catalogue
# and the default: every button, in its order, for a new player and for a button a later client adds. This module keeps
# the player's own choice and shows the window that changes it:
#   - opened by the gear under the bar's buttons, and from Esc > Opcje Gry > Dodatkowe ("Pasek boczny ekwipunku");
#   - a row per button: the tick shows or hides it, the arrows move it up or down, and a row dragged with the mouse
#     (held on its name) is put where it is let go; "Domyslne" gives back the default list;
#   - every change is applied to the bar at once and saved at once.
# Kept per character, as the window places (uiwindowpos.py) and the bar's fold: autohunt/okna/pasek/<nick>.cfg,
#   kolejnosc=name,name,...   (the order of the buttons it knows)
#   ukryte=name,...           (the ones hidden)
# A name the client no longer has is dropped; a button the file does not know yet is shown, at its default place.
#
# Python 2.7 as the client has it; the texts are CP1250 escapes.

import os
from weakref import proxy

import player
import ui
import wndMgr

try:
	import __builtin__ as _builtins
except ImportError:		# Python 3 (the tests)
	import builtins as _builtins

CONFIG_DIR = os.path.join('autohunt', 'okna', 'pasek')

TITLE = 'Pasek boczny'
HINT = 'Zaznacz przyciski paska. Kolejno\x9c\xe6: strza\xb3ki lub przeci\xb9gnij wiersz.'
BUTTON_DEFAULTS = 'Domy\x9clne'
BUTTON_CLOSE = 'Zamknij'
TOOLTIP_GEAR = 'Ustawienia paska'
TOOLTIP_UP = 'Wy\xbfej'
TOOLTIP_DOWN = 'Ni\xbfej'

SIDEBAR_IMAGE = "mt2009_ui/sidebar/%s_%02d.tga"
CHECKBOX_IMAGE = "mt2009_ui/checkbox/checkbox.tga"
CHECKED_IMAGE = "mt2009_ui/checkbox/checked.tga"

_state = {'name': None, 'order': [], 'hidden': set(), 'saved': False, 'version': 0}
_window = [None]


def _Open(path, mode):
	return getattr(_builtins, 'old_open', open)(path, mode)		# open() of system.py reads the packs


def _FileFor(name):
	if not name.isalnum():
		try:
			name = name.encode('hex')
		except (AttributeError, LookupError):
			name = ''.join('%02x' % ord(c) for c in name)
	return os.path.join(CONFIG_DIR, name + '.cfg')


def _Names(text):
	return [part.strip() for part in text.split(',') if part.strip()]


def _Load():
	"""The character's choice read once a character; False while there is none (before the game)."""
	try:
		name = player.GetName()
	except Exception:
		name = None
	if not name:
		return False
	if _state['name'] == name:
		return True
	_state['name'] = name
	_state['order'] = []
	_state['hidden'] = set()
	_state['saved'] = False
	_state['version'] += 1
	try:
		handle = _Open(_FileFor(name), 'r')
		try:
			for line in handle:
				if '=' not in line:
					continue
				key, value = line.strip().split('=', 1)
				if key == 'kolejnosc':
					_state['order'] = _Names(value)
					_state['saved'] = True
				elif key == 'ukryte':
					_state['hidden'] = set(_Names(value))
		finally:
			handle.close()
	except (IOError, OSError):
		pass
	return True


def _Save():
	if not _state['name']:
		return
	try:
		if not os.path.exists(CONFIG_DIR):
			os.makedirs(CONFIG_DIR)
		handle = _Open(_FileFor(_state['name']), 'w')
		try:
			handle.write('kolejnosc=%s\n' % ','.join(_state['order']))
			handle.write('ukryte=%s\n' % ','.join(sorted(_state['hidden'])))
		finally:
			handle.close()
	except (IOError, OSError):
		pass


def GetVersion():
	"""Changes whenever the arrangement may have changed (a new character, a change in the window)."""
	_Load()
	return _state['version']


def Arrange(catalogue):
	"""[(entry, shown)] - every entry of the catalogue (tuples whose [0] is the name) in the player's order."""
	_Load()
	known = dict((entry[0], entry) for entry in catalogue)
	names = [name for name in _state['order'] if name in known]
	names = [name for i, name in enumerate(names) if name not in names[:i]]
	if _state['saved']:
		# a button the saved order does not know (a newer client): after the one before it in the default list
		for index, entry in enumerate(catalogue):
			if entry[0] in names:
				continue
			at = 0
			for previous in reversed([e[0] for e in catalogue[:index]]):
				if previous in names:
					at = names.index(previous) + 1
					break
			names.insert(at, entry[0])
	else:
		names = [entry[0] for entry in catalogue]
	return [(known[name], name not in _state['hidden']) for name in names]


def Visible(catalogue):
	return [entry for entry, shown in Arrange(catalogue) if shown]


def SetArrangement(order, hidden):
	if not _Load():
		return
	_state['order'] = list(order)
	_state['hidden'] = set(hidden)
	_state['saved'] = True
	_state['version'] += 1
	_Save()


def ResetArrangement():
	if not _Load():
		return
	_state['order'] = []
	_state['hidden'] = set()
	_state['saved'] = False
	_state['version'] += 1
	try:
		path = _FileFor(_state['name'])
		if os.path.exists(path):
			os.remove(path)
	except (IOError, OSError):
		pass


def Catalogue():
	"""The side bar's buttons this client can show (uiinventory.SidebarWindow.BUTTONS)."""
	import uiinventory
	return uiinventory.SidebarCatalogue()


# ---------------------------------------------------------------------------------------------------------------------
# The window


class _Row(ui.Window):
	"""One button of the bar: tick, icon, name, up, down. Held on its name and let go: the drag (RunMouseLeftButtonUp
	gives the release to the row that took the press)."""

	def __init__(self, owner, name, text):
		ui.Window.__init__(self)
		self.owner = proxy(owner)
		self.name = name
		self.SetSize(SidebarSettingsWindow.ROW_WIDTH, SidebarSettingsWindow.ROW_HEIGHT)

		self.highlight = ui.Bar()
		self.highlight.SetParent(self)
		self.highlight.AddFlag("not_pick")
		self.highlight.SetSize(SidebarSettingsWindow.ROW_WIDTH, SidebarSettingsWindow.ROW_HEIGHT)
		self.highlight.SetColor(0x40ffd56a)
		self.highlight.Hide()

		self.check = ui.Window()
		self.check.SetParent(self)
		self.check.SetSize(16, 16)
		self.check.SetPosition(2, 5)
		self.check.Show()
		self.box = self.mark = self.textMark = None
		try:
			box = ui.ImageBox()
			box.SetParent(self.check)
			box.AddFlag("not_pick")
			box.LoadImage(CHECKBOX_IMAGE)
			box.SetPosition(0, 2)
			box.Show()
			mark = ui.ImageBox()
			mark.SetParent(self.check)
			mark.AddFlag("not_pick")
			mark.LoadImage(CHECKED_IMAGE)
			mark.SetPosition(0, -2)
			self.box, self.mark = box, mark
		except Exception:
			textMark = ui.TextLine()
			textMark.SetParent(self.check)
			textMark.AddFlag("not_pick")
			textMark.SetText("[ ]")
			textMark.SetOutline()
			textMark.Show()
			self.textMark = textMark
		self.check.SAFE_SetEvent("MOUSE_LEFT_BUTTON_UP", self.__OnClickCheck)

		self.icon = None
		try:
			icon = ui.ExpandedImageBox()
			icon.SetParent(self)
			icon.AddFlag("not_pick")
			icon.LoadImage(SIDEBAR_IMAGE % (name, 1))
			icon.SetScale(0.625, 0.625)		# 32 -> 20
			icon.SetPosition(22, 2)
			icon.Show()
			self.icon = icon
		except Exception:
			pass

		self.label = ui.TextLine()
		self.label.SetParent(self)
		self.label.AddFlag("not_pick")
		self.label.SetPosition(48, 5)
		self.label.SetText(text)
		self.label.SetOutline()
		self.label.Show()

		x = SidebarSettingsWindow.ROW_WIDTH - 2 * 17 - 4
		self.upButton = self.__Arrow(x, "up", TOOLTIP_UP, self.__OnClickUp)
		self.downButton = self.__Arrow(x + 19, "down", TOOLTIP_DOWN, self.__OnClickDown)

	def __del__(self):
		ui.Window.__del__(self)

	def __Arrow(self, x, kind, tooltip, event):
		button = ui.Button()
		button.SetParent(self)
		button.SetUpVisual("d:/ymir work/ui/public/scrollbar_%s_button_01.sub" % kind)
		button.SetOverVisual("d:/ymir work/ui/public/scrollbar_%s_button_02.sub" % kind)
		button.SetDownVisual("d:/ymir work/ui/public/scrollbar_%s_button_03.sub" % kind)
		button.SetPosition(x, 3)
		button.SetToolTipText(tooltip)
		button.SAFE_SetEvent(event)
		button.Show()
		return button

	def Destroy(self):
		self.owner = None
		self.check.ClearEvents()
		self.upButton.ClearEvent()
		self.downButton.ClearEvent()
		self.Hide()

	def SetShown(self, shown):
		if self.textMark:
			self.textMark.SetText("[x]" if shown else "[ ]")
		elif shown:
			self.mark.Show()
		else:
			self.mark.Hide()
		color = 0xffffffff if shown else 0xff8c8c8c
		self.label.SetPackedFontColor(color)

	def SetDragged(self, dragged):
		if dragged:
			self.highlight.Show()
		else:
			self.highlight.Hide()

	def __Call(self, method, *args):
		try:
			if self.owner is not None:
				getattr(self.owner, method)(*args)
		except ReferenceError:
			self.owner = None

	def __OnClickCheck(self):
		self.__Call("Toggle", self.name)

	def __OnClickUp(self):
		self.__Call("Move", self.name, -1)

	def __OnClickDown(self):
		self.__Call("Move", self.name, 1)

	def OnMouseLeftButtonDown(self):
		self.__Call("BeginDrag", self.name)
		return True

	def OnMouseLeftButtonUp(self):
		self.__Call("EndDrag")
		return True


class SidebarSettingsWindow(ui.BoardWithTitleBar):
	WIDTH = 290
	ROW_WIDTH = 256
	ROW_HEIGHT = 24
	LIST_X = 17
	LIST_Y = 52

	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)
		self.AddFlag("movable")
		self.AddFlag("float")
		self.SetTitleName(TITLE)
		self.SetCloseEvent(ui.__mem_func__(self.Close))
		self.rows = {}
		self.order = []
		self.hidden = set()
		self.dragName = None
		self.loadedVersion = -1

		hint = ui.TextLine()
		hint.SetParent(self)
		hint.SetPosition(self.LIST_X, 32)
		hint.SetText(HINT)
		hint.SetPackedFontColor(0xffc8c8c8)
		hint.Show()
		self.hint = hint

		marker = ui.Bar()
		marker.SetParent(self)
		marker.AddFlag("not_pick")
		marker.SetSize(self.ROW_WIDTH, 2)
		marker.SetColor(0xffffd56a)
		marker.Hide()
		self.marker = marker

		self.defaultsButton = self.__TextButton(BUTTON_DEFAULTS, self.ResetDefaults)
		self.closeButton = self.__TextButton(BUTTON_CLOSE, self.Close)
		self.SetSize(self.WIDTH, 120)

	def __del__(self):
		ui.BoardWithTitleBar.__del__(self)

	def __TextButton(self, text, event):
		button = ui.Button()
		button.SetParent(self)
		button.SetUpVisual("d:/ymir work/ui/public/middle_button_01.sub")
		button.SetOverVisual("d:/ymir work/ui/public/middle_button_02.sub")
		button.SetDownVisual("d:/ymir work/ui/public/middle_button_03.sub")
		button.SetText(text)
		button.SAFE_SetEvent(event)
		button.Show()
		return button

	def Destroy(self):
		for row in self.rows.values():
			row.Destroy()
		self.rows = {}
		self.defaultsButton.ClearEvent()
		self.closeButton.ClearEvent()
		self.Hide()

	def __Load(self):
		arranged = Arrange(Catalogue())
		self.order = [entry[0] for entry, shown in arranged]
		self.hidden = set(entry[0] for entry, shown in arranged if not shown)
		texts = dict((entry[0], entry[1]) for entry, shown in arranged)
		for name in list(self.rows.keys()):
			if name not in texts:
				self.rows.pop(name).Destroy()
		for name in self.order:
			if name not in self.rows:
				row = _Row(self, name, texts[name])
				row.SetParent(self)
				self.rows[name] = row
		self.loadedVersion = GetVersion()
		self.__Layout()

	def __Layout(self):
		y = self.LIST_Y
		for name in self.order:
			row = self.rows[name]
			row.SetPosition(self.LIST_X, y)
			row.SetShown(name not in self.hidden)
			row.SetDragged(name == self.dragName)
			row.Show()
			y += self.ROW_HEIGHT
		y += 8
		self.defaultsButton.SetPosition(self.WIDTH // 2 - 61 - 4, y)
		self.closeButton.SetPosition(self.WIDTH // 2 + 4, y)
		self.SetSize(self.WIDTH, y + 21 + 14)

	def __Apply(self):
		SetArrangement(self.order, self.hidden)
		self.loadedVersion = GetVersion()
		self.__Layout()

	def Toggle(self, name):
		if name in self.hidden:
			self.hidden.discard(name)
		else:
			self.hidden.add(name)
		self.__Apply()

	def Move(self, name, step):
		if name not in self.order:
			return
		index = self.order.index(name)
		target = max(0, min(len(self.order) - 1, index + step))
		if target == index:
			return
		self.order.pop(index)
		self.order.insert(target, name)
		self.__Apply()

	def ResetDefaults(self):
		ResetArrangement()
		self.dragName = None
		self.__Load()

	def BeginDrag(self, name):
		self.dragName = name
		if name in self.rows:
			self.rows[name].SetDragged(True)

	def __DropIndex(self):
		"""Where the dragged row goes: the gap between rows nearest the mouse."""
		x, y = self.GetGlobalPosition()
		mouseX, mouseY = wndMgr.GetMousePosition()
		slot = (mouseY - (y + self.LIST_Y) + self.ROW_HEIGHT // 2) // self.ROW_HEIGHT
		return int(max(0, min(len(self.order), slot)))

	def EndDrag(self):
		name = self.dragName
		self.dragName = None
		self.marker.Hide()
		if name is None or name not in self.order:
			self.__Layout()
			return
		gap = self.__DropIndex()
		index = self.order.index(name)
		if gap in (index, index + 1):
			self.__Layout()		# let go where it was (a plain click on the name)
			return
		self.order.pop(index)
		if gap > index:
			gap -= 1
		self.order.insert(gap, name)
		self.__Apply()

	def OnUpdate(self):
		if self.dragName is not None:
			gap = self.__DropIndex()
			self.marker.SetPosition(self.LIST_X, self.LIST_Y + gap * self.ROW_HEIGHT - 1)
			self.marker.Show()
		elif GetVersion() != self.loadedVersion:
			self.__Load()		# another character

	def Open(self):
		self.dragName = None
		self.__Load()
		if not self.IsShow():
			self.SetCenterPosition()
		self.SetTop()
		self.Show()

	def Close(self):
		self.dragName = None
		self.marker.Hide()
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True


def GetWindow():
	if _window[0] is None:
		_window[0] = SidebarSettingsWindow()
	return _window[0]


def OpenWindow():
	GetWindow().Open()


def ToggleWindow():
	window = GetWindow()
	if window.IsShow():
		window.Close()
	else:
		window.Open()


def DestroyWindow():
	window = _window[0]
	_window[0] = None
	if window is not None:
		window.Destroy()
