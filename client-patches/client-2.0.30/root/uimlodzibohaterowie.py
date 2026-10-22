# MT2009_PLUS_MLODZI_BOHATEROWIE_V1: Bronie dla Mlodych Bohaterow - the choice window of the quest letter
# (quest mlodzi_bohaterowie, linux-port/overlays/playerbot/src/game/src/playerbot_mlodzi.cpp), laid out as the
# official window: the title "Wybierz bron:", the weapons' icons with their names in a row on top, the preview in
# the middle, one button per weapon below and "Dalej".
#
#   server -> client  "MLODZI_OPEN <tier> <level> <vnum1> <vnum2> <vnum3>"  (an unused vnum is 0; 1-3 weapons of
#                     the player's class), "MLODZI_CLOSE" (claimed, or the offer is gone)
#   client -> server  "/mlodzi_wybor <tier> <choice>"  (choice 1-3 = the vnum's place in MLODZI_OPEN; the server
#                     checks everything again and answers with a chat line and MLODZI_CLOSE)
#
# Hovering a weapon shows the normal item tooltip of the weapon as the player will get it: socket0 = now + 15 days
# (LIMIT_REAL_TIME) and attribute 0 = the tier's average damage (POINT_NORMAL_HIT_DAMAGE_BONUS - an attribute's type
# is a POINT_* number in this engine, the tooltip's localeinfo_point keys). Esc / X only close the window: the letter
# stays and the server keeps the offer.
#
# The middle preview is the race's face and the chosen weapon's icon, not a 3D model: the exe's only python model
# view (player.Mt2009Model*, Mt2009MonsterModel.cpp of the Monster Cards) builds a CInstanceBase from a race number
# alone - no armour, hair or weapon can be set on it (chr.SetWeapon works only on a character of the world) - so a
# character holding the chosen weapon cannot be drawn without an exe change.
#
# Python 2.7 as the client has it; the texts are CP1250 escapes.

import app
import item
import net
import player
import ui

TEXT_TITLE = "Wybierz bro\xf1:"
TEXT_HEAD = "Bro\xf1 dla M\xb3odych Bohater\xf3w - poziom %d"
TEXT_PICK = "Kliknij bro\xf1, aby j\xb9 wybra\xe6."
TEXT_AVG = "\x8crednie obra\xbfenia +%d%%"
TEXT_LIFE = "Znika 15 dni po otrzymaniu."
TEXT_LEVEL = "Poziom: %d"
TEXT_NEXT = "Dalej"

LIFE_SECONDS = 1296000          # 15 days, the items' LIMIT_REAL_TIME (tools/mlodzi/gen_mlodzi.py)
FIRST_VNUM = 21900
LAST_VNUM = 21975
POINT_AVERAGE = getattr(player, "POINT_NORMAL_HIT_DAMAGE_BONUS", 122)

BOARD_WIDTH = 480
COL_WIDTH = 150
ICON_TOP = 36
ICON_BOX_HEIGHT = 100           # the tallest icon is 32x96 (size 3)
NAME_Y = ICON_TOP + ICON_BOX_HEIGHT + 4
PREVIEW_Y = NAME_Y + 22
PREVIEW_HEIGHT = 108
BUTTONS_Y = PREVIEW_Y + PREVIEW_HEIGHT + 10
BUTTON_STEP = 27

COLOR_BOX = 0x90000000
COLOR_BOX_SELECTED = 0xb0c89b3c
COLOR_HEAD = 0xfff1e6c0
COLOR_NAME = 0xffffffff
COLOR_NAME_SELECTED = 0xffffd76a
COLOR_INFO = 0xffc8c8c8

FACE = {
	0: "icon/face/warrior_m.tga", 1: "icon/face/assassin_w.tga", 2: "icon/face/sura_m.tga",
	3: "icon/face/shaman_w.tga", 4: "icon/face/warrior_w.tga", 5: "icon/face/assassin_m.tga",
	6: "icon/face/sura_w.tga", 7: "icon/face/shaman_m.tga", 8: "icon/face/wolfman_m.tga",
}

_state = {
	'window': None,
	'interface': None,
}


def ToInt(value, default=0):
	try:
		return int(value)
	except (TypeError, ValueError):
		return default


def AverageDamage(tier):
	# = playerbot_mlodzi.cpp AverageDamage: +10% at tier 1, +3% a tier, at most +30%
	if tier < 1:
		return 0
	return min(30, 10 + 3 * (tier - 1))


def IsWeaponVnum(vnum):
	return FIRST_VNUM <= vnum <= LAST_VNUM and vnum % 10 <= 5


def Now():
	try:
		return int(app.GetGlobalTimeStamp())
	except Exception:
		import time
		return int(time.time())


class _WeaponIcon(ui.ImageBox):
	"""A weapon's icon: hover = the item tooltip, click = select."""

	def __init__(self, index, overIn, overOut, click):
		ui.ImageBox.__init__(self)
		self.index = index
		self.overIn = overIn
		self.overOut = overOut
		self.click = click

	def __del__(self):
		ui.ImageBox.__del__(self)

	def OnMouseOverIn(self):
		if self.overIn:
			self.overIn(self.index)

	def OnMouseOverOut(self):
		if self.overOut:
			self.overOut()

	def OnMouseLeftButtonUp(self):
		if self.click:
			self.click(self.index)
		return True

	def Release(self):
		self.overIn = None
		self.overOut = None
		self.click = None


class MlodziWindow(ui.BoardWithTitleBar):

	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)
		self.widgets = []
		self.icons = []
		self.boxes = []
		self.names = []
		self.buttons = []
		self.tier = 0
		self.level = 0
		self.vnums = []
		self.choices = []
		self.selected = -1
		self.tooltipItem = None
		self.ownTooltip = None
		self.AddFlag('movable')
		self.AddFlag('float')
		self.SetTitleName(TEXT_TITLE)
		self.SetCloseEvent(ui.__mem_func__(self.Close))
		self.SetSize(BOARD_WIDTH, 200)

	def __del__(self):
		ui.BoardWithTitleBar.__del__(self)

	def SetItemToolTip(self, tooltipItem):
		self.tooltipItem = tooltipItem

	def __ToolTip(self):
		if self.tooltipItem:
			return self.tooltipItem
		if self.ownTooltip is None:
			import uiToolTip
			self.ownTooltip = uiToolTip.ItemToolTip()
			self.ownTooltip.HideToolTip()
		return self.ownTooltip

	def __Clear(self):
		for icon in self.icons:
			icon.Release()
			icon.Hide()
		for w in self.widgets:
			w.Hide()
		self.widgets = []
		self.icons = []
		self.boxes = []
		self.names = []
		self.buttons = []
		self.next = None
		self.faceImage = None
		self.previewIcon = None
		self.previewLines = []

	def __Add(self, widget, x, y):
		widget.SetParent(self)
		widget.SetPosition(x, y)
		widget.Show()
		self.widgets.append(widget)
		return widget

	def __Label(self, x, y, text, center=False, color=None, parent=None):
		line = ui.TextLine()
		line.SetParent(parent or self)
		line.SetPosition(x, y)
		if center:
			line.SetHorizontalAlignCenter()
		line.SetText(text)
		if color is not None:
			line.SetPackedFontColor(color)
		line.Show()
		self.widgets.append(line)
		return line

	def __Build(self):
		self.__Clear()
		count = len(self.vnums)
		x0 = (BOARD_WIDTH - count * COL_WIDTH) / 2
		for i, vnum in enumerate(self.vnums):
			cx = x0 + i * COL_WIDTH + COL_WIDTH / 2
			box = ui.Bar()
			box.AddFlag('not_pick')
			box.SetSize(44, ICON_BOX_HEIGHT)
			box.SetColor(COLOR_BOX)
			self.boxes.append(self.__Add(box, cx - 22, ICON_TOP))

			item.SelectItem(vnum)
			icon = _WeaponIcon(i, ui.__mem_func__(self.OnOverIn), ui.__mem_func__(self.OnOverOut),
				ui.__mem_func__(self.Select))
			icon.LoadImage(item.GetIconImageFileName())
			h = icon.GetHeight() or 32 * max(1, item.GetItemSize()[1])
			self.__Add(icon, cx - 16, ICON_TOP + max(0, (ICON_BOX_HEIGHT - h) / 2))
			self.icons.append(icon)
			self.names.append(self.__Label(cx, NAME_Y, item.GetItemName(), True, COLOR_NAME))

		board = ui.ThinBoard()
		board.SetSize(BOARD_WIDTH - 30, PREVIEW_HEIGHT)
		self.__Add(board, 15, PREVIEW_Y)
		face = ui.ImageBox()
		face.AddFlag('not_pick')
		try:
			face.LoadImage(FACE.get(player.GetRace(), FACE[0]))
		except Exception:
			pass
		self.faceImage = self.__Add(face, 30, PREVIEW_Y + (PREVIEW_HEIGHT - 44) / 2)
		preview = ui.ImageBox()
		preview.AddFlag('not_pick')
		self.previewIcon = self.__Add(preview, 100, PREVIEW_Y + 6)
		preview.Hide()
		tx = 150
		self.previewLines = [
			self.__Label(tx, PREVIEW_Y + 14, TEXT_HEAD % self.level, False, COLOR_HEAD),
			self.__Label(tx, PREVIEW_Y + 34, TEXT_PICK, False, COLOR_NAME_SELECTED),
			self.__Label(tx, PREVIEW_Y + 52, TEXT_AVG % AverageDamage(self.tier), False, COLOR_INFO),
			self.__Label(tx, PREVIEW_Y + 70, TEXT_LIFE, False, COLOR_INFO),
		]

		for i, vnum in enumerate(self.vnums):
			item.SelectItem(vnum)
			button = ui.RadioButton()
			button.SetUpVisual('d:/ymir work/ui/public/xlarge_button_01.sub')
			button.SetOverVisual('d:/ymir work/ui/public/xlarge_button_02.sub')
			button.SetDownVisual('d:/ymir work/ui/public/xlarge_button_03.sub')
			button.SetText(item.GetItemName())
			button.SAFE_SetEvent(self.Select, i)
			self.buttons.append(self.__Add(button, (BOARD_WIDTH - 180) / 2, BUTTONS_Y + i * BUTTON_STEP))

		nextY = BUTTONS_Y + count * BUTTON_STEP + 6
		button = ui.Button()
		button.SetUpVisual('d:/ymir work/ui/public/large_button_01.sub')
		button.SetOverVisual('d:/ymir work/ui/public/large_button_02.sub')
		button.SetDownVisual('d:/ymir work/ui/public/large_button_03.sub')
		button.SetDisableVisual('d:/ymir work/ui/public/large_button_03.sub')
		button.SetText(TEXT_NEXT)
		button.SAFE_SetEvent(self.OnNext)
		self.next = self.__Add(button, (BOARD_WIDTH - 88) / 2, nextY)
		self.SetSize(BOARD_WIDTH, nextY + 25 + 14)
		self.__Refresh()

	def __Refresh(self):
		for i in xrange(len(self.vnums)):
			on = i == self.selected
			self.boxes[i].SetColor(COLOR_BOX_SELECTED if on else COLOR_BOX)
			self.names[i].SetPackedFontColor(COLOR_NAME_SELECTED if on else COLOR_NAME)
			if on:
				self.buttons[i].Down()
			else:
				self.buttons[i].SetUp()
		if self.selected < 0:
			self.next.Disable()
			self.previewIcon.Hide()
			self.previewLines[1].SetText(TEXT_PICK)
			return
		self.next.Enable()
		item.SelectItem(self.vnums[self.selected])
		self.previewIcon.LoadImage(item.GetIconImageFileName())
		self.previewIcon.Show()
		self.previewLines[1].SetText(item.GetItemName())

	def Setup(self, tier, level, offer):
		self.tier = tier
		self.level = level
		self.choices = [c for c, v in offer]
		self.vnums = [v for c, v in offer]
		self.selected = -1
		self.__Build()

	def Select(self, index):
		if 0 <= index < len(self.vnums):
			self.selected = index
			self.__Refresh()

	def OnOverIn(self, index):
		if not (0 <= index < len(self.vnums)):
			return
		tooltip = self.__ToolTip()
		sockets = [0] * player.METIN_SOCKET_MAX_NUM
		sockets[0] = Now() + LIFE_SECONDS
		attrs = [(0, 0)] * player.ATTRIBUTE_SLOT_MAX_NUM
		attrs[0] = (POINT_AVERAGE, AverageDamage(self.tier))
		tooltip.ClearToolTip()
		tooltip.AddItemData(self.vnums[index], sockets, attrs)
		tooltip.ShowToolTip()

	def OnOverOut(self):
		tooltip = self.tooltipItem or self.ownTooltip
		if tooltip:
			tooltip.HideToolTip()

	def OnNext(self):
		if not (0 <= self.selected < len(self.vnums)) or self.tier < 1:
			return
		net.SendChatPacket("/mlodzi_wybor %d %d" % (self.tier, self.choices[self.selected]))
		self.Close()

	def Open(self):
		self.SetCenterPosition()
		self.Show()
		self.SetTop()

	def Close(self):
		self.OnOverOut()
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def Destroy(self):
		self.OnOverOut()
		self.__Clear()
		self.tooltipItem = None
		if self.ownTooltip:
			self.ownTooltip.HideToolTip()
		self.ownTooltip = None
		self.Hide()


def SetInterface(interface):
	try:
		from _weakref import proxy
		_state['interface'] = proxy(interface)
	except Exception:
		_state['interface'] = None


def __Window():
	window = _state['window']
	if window is None:
		import uiminigameutil
		window = uiminigameutil.SafeCreate(MlodziWindow, TEXT_TITLE)
		if window is None:
			return None
		_state['window'] = window
	try:
		interface = _state['interface']
		window.SetItemToolTip(interface.tooltipItem if interface is not None else None)
	except Exception:
		window.SetItemToolTip(None)
	return window


def OnOpen(*args):
	"""MLODZI_OPEN <tier> <level> <vnum1> <vnum2> <vnum3>"""
	try:
		if len(args) < 3:
			return
		tier, level = ToInt(args[0]), ToInt(args[1])
		# (choice, vnum): the choice is the vnum's own place in the line (1-3), also past an unused 0
		offer = [(i + 1, ToInt(a)) for i, a in enumerate(args[2:5]) if IsWeaponVnum(ToInt(a))]
		if tier < 1 or not offer:
			return
		window = __Window()
		if window is None:
			return
		window.Setup(tier, level, offer)
		window.Open()
	except Exception:
		import dbg
		import sys
		dbg.TraceError('uimlodzibohaterowie.OnOpen %s: %s' % (str(args), str(sys.exc_info()[1])))


def OnClose(*args):
	"""MLODZI_CLOSE"""
	window = _state['window']
	if window is not None:
		window.Close()


def DestroyWindow():
	window = _state['window']
	_state['window'] = None
	_state['interface'] = None
	if window is not None:
		window.Destroy()
