# Buffi - the support shaman of Ameria Project (MT2009_PLUS_BUFFI_V1; the
# owner, 21 October 2026: "W zamian za towarzysza dodaj system buffi z Amerii.
# Pod tym samym skrotem klawiszowym itd."). The P key (keybind "companion")
# and the inventory side bar's first button open it, where the companion's
# window was; the companion (uisidekick.py) is off unless the server's .env
# says M2_SIDEKICK=1 and then opens from its letter or the "sidekick" key.
#
# The server half is playerbot_buffi.cpp (server-patches/buffi/README.md):
#   window -> "/buffi info"          the state
#             "/buffi toggle"        call / send away (the seal in the bag)
#             "/buffi name <name>"   Zwoj Imienia Buffi (61030)
#   server -> "BUFFI state <on> <called> <seal vnum> <named> <name|-> <lv164>
#                <lv165> <lv166> <lv167> <boss bonus seconds> <name scrolls>"
#             "BUFFI askname"       a name scroll was used: the name dialog
#             "BUFFI off"           M2_BUFFI=0 on the server
# (game.py passes the "BUFFI" lines here.)
#
# What the window shows: the seal, called or not, the name, the four buffs
# with their grade (M1..P) - Szybkosc and Zwiekszenie Ataku only with a name -
# and where the books and soul stones are sold. It sends only on a click and
# when it opens, only in the game phase (warpsafe.InGame).
#
# Python 2.7 as the client has it; the texts are CP1250.

import chat
import net
import ui
import uiCommon

import warpsafe

NAME_MAX = 16

TEXT_TITLE = "Buffi"
TEXT_OFF = "Buffi jest wy\xb3\xb9czony na tym serwerze."
TEXT_SEAL = "Piecz\xea\xe6: %s"
TEXT_NO_SEAL = "Piecz\xea\xe6: brak (ItemShop, nowa posta\xe6 dostaje Buffi na 7 dni)"
TEXT_CALLED = "Stan: przywo\xb3ana - chodzi za tob\xb9 i rzuca wzmocnienia"
TEXT_NOT_CALLED = "Stan: odwo\xb3ana"
TEXT_NAME = "Imi\xea: %s"
TEXT_NO_NAME = "Imi\xea: brak - Zw\xf3j Imienia Buffi odblokowuje dwa wzmocnienia"
TEXT_BOSS = "+10%% silny przeciwko bossom jeszcze: %s"
TEXT_SKILLS = "Wzmocnienia (co 3 sekundy, gdy ich brakuje):"
TEXT_NEEDS_NAME = "wymaga imienia"
TEXT_NOT_YET = "M1 przy pierwszym przywo\xb3aniu"
TEXT_HELP1 = "Ksi\xeagi Buffi (M1 - G1) i Kamie\xf1 Duchowy Buffi (G1 - P):"
TEXT_HELP2 = "Handlarka - \"Ksi\xeagi i kamienie Buffi\". Wymagana droga umiej\xeatno\x9cci."
TEXT_CALL = "Przywo\xb3aj"
TEXT_SEND_AWAY = "Odwo\xb3aj"
TEXT_RENAME = "Nadaj imi\xea"
TEXT_CLOSE = "Zamknij"
TEXT_ASK_NAME = "Imi\xea Buffi (2-%d liter lub cyfr)"
TEXT_NO_SCROLL = "Nie masz Zwoju Imienia Buffi (ItemShop)."
SEALS = {61025: "Buffi (7 dni)", 61026: "Buffi"}

# the skill, its Polish name, the shaman skill's icon
SKILLS = (
	(164, "B\xb3ogos\xb3awie\xf1stwo", "hosin"),
	(165, "Pomoc Smoka", "gicheon"),
	(166, "Szybko\x9c\xe6", "kwaesok"),
	(167, "Zwi\xeakszenie Ataku", "jeungryeok"),
)
NAMED_ONLY = (166, 167)

COLOR_INFO = 0xffc8c8c8
COLOR_GOOD = 0xff9be27c
COLOR_WARN = 0xffe0b060
COLOR_OFF = 0xff909090

_state = {
	'window': None,
	'data': None,
	'off': False,
}


def ToInt(value, default=0):
	try:
		return int(value)
	except (TypeError, ValueError):
		return default


def Send(command):
	if not warpsafe.InGame():
		return False
	net.SendChatPacket("/buffi " + command)
	return True


def Grade(level):
	if level >= 40:
		return "P"
	if level >= 30:
		return "G%d" % (level - 29)
	if level >= 20:
		return "M%d" % (level - 19)
	return ""


def Duration(seconds):
	days, rest = divmod(max(0, seconds), 86400)
	hours, rest = divmod(rest, 3600)
	if days:
		return "%d d. %d godz." % (days, hours)
	return "%d godz. %d min." % (hours, rest // 60)


def CleanName(text):
	text = (text or "").strip()
	return "".join([c for c in text if c.isalnum()])[:NAME_MAX]


class BuffiWindow(ui.BoardWithTitleBar):
	WIDTH = 330
	TOP = 34
	ROW_H = 38

	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)
		self.widgets = []
		self.rows = []
		self.dialog = None
		self.AddFlag('movable')
		self.AddFlag('float')
		self.SetTitleName(TEXT_TITLE)
		self.SetCloseEvent(ui.__mem_func__(self.Close))
		self.__Build()
		self.SetCenterPosition()

	def __del__(self):
		ui.BoardWithTitleBar.__del__(self)

	def __Label(self, x, y, text="", color=None):
		line = ui.TextLine()
		line.SetParent(self)
		line.SetPosition(x, y)
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
		y = self.TOP
		self.sealLine = self.__Label(16, y)
		self.stateLine = self.__Label(16, y + 16)
		self.nameLine = self.__Label(16, y + 32)
		self.bossLine = self.__Label(16, y + 48, "", COLOR_GOOD)
		y += 70
		self.__Label(16, y, TEXT_SKILLS, COLOR_INFO)
		y += 18
		board = ui.ThinBoard()
		board.SetParent(self)
		board.SetPosition(10, y)
		board.SetSize(self.WIDTH - 20, len(SKILLS) * self.ROW_H + 10)
		board.Show()
		self.widgets.append(board)
		for i, (vnum, name, icon) in enumerate(SKILLS):
			ry = y + 6 + i * self.ROW_H
			image = ui.ImageBox()
			image.SetParent(self)
			image.SetPosition(20, ry)
			image.Show()
			self.widgets.append(image)
			title = self.__Label(60, ry + 2, name)
			grade = self.__Label(60, ry + 17, "", COLOR_INFO)
			self.rows.append((vnum, icon, image, title, grade))
		y += len(SKILLS) * self.ROW_H + 18
		self.__Label(16, y, TEXT_HELP1, COLOR_INFO)
		self.__Label(16, y + 15, TEXT_HELP2, COLOR_INFO)
		y += 38
		self.toggleButton = self.__Button(16, y, TEXT_CALL, self.OnToggle)
		self.renameButton = self.__Button(16 + 98, y, TEXT_RENAME, self.OnRename)
		self.__Button(self.WIDTH - 16 - 88, y, TEXT_CLOSE, self.Close)
		self.SetSize(self.WIDTH, y + 40)

	def __Icon(self, image, icon, level):
		grade = 1 if level < 20 else 2 if level < 30 else 3
		try:
			image.LoadImage("d:/ymir work/ui/skill/shaman/%s_%02d.sub" % (icon, grade))
		except Exception:
			pass

	def Refresh(self):
		if _state['off']:
			self.sealLine.SetText(TEXT_OFF)
			self.sealLine.SetPackedFontColor(COLOR_WARN)
			for line in (self.stateLine, self.nameLine, self.bossLine):
				line.SetText("")
			for vnum, icon, image, title, grade in self.rows:
				grade.SetText("")
			self.toggleButton.Hide()
			self.renameButton.Hide()
			return
		data = _state['data']
		if data is None:
			return
		self.toggleButton.Show()
		if data['seal']:
			self.sealLine.SetText(TEXT_SEAL % SEALS.get(data['seal'], "Buffi"))
			self.sealLine.SetPackedFontColor(COLOR_INFO)
		else:
			self.sealLine.SetText(TEXT_NO_SEAL)
			self.sealLine.SetPackedFontColor(COLOR_WARN)
		if data['called']:
			self.stateLine.SetText(TEXT_CALLED)
			self.stateLine.SetPackedFontColor(COLOR_GOOD)
			self.toggleButton.SetText(TEXT_SEND_AWAY)
		else:
			self.stateLine.SetText(TEXT_NOT_CALLED)
			self.stateLine.SetPackedFontColor(COLOR_INFO)
			self.toggleButton.SetText(TEXT_CALL)
		if data['named']:
			self.nameLine.SetText(TEXT_NAME % data['name'])
			self.nameLine.SetPackedFontColor(COLOR_GOOD)
		else:
			self.nameLine.SetText(TEXT_NO_NAME)
			self.nameLine.SetPackedFontColor(COLOR_WARN)
		self.bossLine.SetText(TEXT_BOSS % Duration(data['boss']) if data['boss'] > 0 else "")
		if data['scrolls'] > 0 and data['called']:
			self.renameButton.Show()
		else:
			self.renameButton.Hide()
		for vnum, icon, image, title, grade in self.rows:
			level = data['levels'].get(vnum, 0)
			self.__Icon(image, icon, level)
			if vnum in NAMED_ONLY and not data['named']:
				text, color = "%s - %s" % (Grade(level) or "-", TEXT_NEEDS_NAME), COLOR_OFF
			elif level <= 0:
				text, color = TEXT_NOT_YET, COLOR_INFO
			else:
				text, color = Grade(level), COLOR_GOOD
			grade.SetText(text)
			grade.SetPackedFontColor(color)

	def OnToggle(self):
		Send("toggle")

	def OnRename(self):
		data = _state['data']
		if not data or data['scrolls'] <= 0:
			chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_NO_SCROLL)
			return
		self.AskName()

	def AskName(self):
		self.__CloseDialog()
		dialog = uiCommon.InputDialog()
		dialog.SetTitle(TEXT_ASK_NAME % NAME_MAX)
		dialog.SetMaxLength(NAME_MAX)
		dialog.SetAcceptEvent(ui.__mem_func__(self.OnAcceptName))
		dialog.SetCancelEvent(ui.__mem_func__(self.OnCancelDialog))
		dialog.Open()
		self.dialog = dialog

	def OnAcceptName(self):
		name = ""
		if self.dialog:
			try:
				name = CleanName(self.dialog.GetText())
			except Exception:
				name = ""
		self.__CloseDialog()
		if len(name) >= 2:
			Send("name " + name)
		return True

	def OnCancelDialog(self):
		self.__CloseDialog()
		return True

	def __CloseDialog(self):
		dialog = self.dialog
		self.dialog = None
		if dialog:
			try:
				dialog.Close()
			except Exception:
				pass

	def Open(self):
		self.Refresh()
		self.Show()
		self.SetTop()

	def Close(self):
		self.__CloseDialog()
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def Destroy(self):
		self.__CloseDialog()
		self.Hide()
		self.rows = []
		self.widgets = []


def GetWindow():
	window = _state['window']
	if window is None:
		import uiminigameutil
		window = uiminigameutil.SafeCreate(BuffiWindow, TEXT_TITLE)
		_state['window'] = window
	return window


def OpenWindow():
	window = GetWindow()
	if window is None:
		return
	window.Open()
	Send("info")


def ToggleWindow():
	window = _state['window']
	if window is not None and window.IsShow():
		window.Close()
		return
	OpenWindow()


def DestroyWindow():
	window = _state['window']
	_state['window'] = None
	if window is not None:
		window.Destroy()


def OnCommand(sub='', *args):
	try:
		if sub == 'off':
			_state['off'] = True
		elif sub == 'state' and len(args) >= 11:
			_state['off'] = ToInt(args[0]) == 0
			_state['data'] = {
				'called': ToInt(args[1]) != 0,
				'seal': ToInt(args[2]),
				'named': ToInt(args[3]) != 0,
				'name': args[4] if args[4] != "-" else "",
				'levels': {164: ToInt(args[5]), 165: ToInt(args[6]), 166: ToInt(args[7]), 167: ToInt(args[8])},
				'boss': ToInt(args[9]),
				'scrolls': ToInt(args[10]),
			}
		elif sub == 'askname':
			window = GetWindow()
			if window is not None:
				window.Open()
				window.AskName()
			return
		else:
			return
		window = _state['window']
		if window is not None and window.IsShow():
			window.Refresh()
	except Exception:
		import dbg
		import sys
		dbg.TraceError('uibuffi.OnCommand %s: %s' % (str((sub,) + args), str(sys.exc_info()[1])))
