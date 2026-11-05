# MT2009_PLUS_LANG_V1 - the language choice: the "Jezyk" tab of the Esc menu's "Opcje Gry" (uioptionstabs.py,
# uisystem.GetOptionPage("lang")) and the "Language" button of the login screen (intrologin.py). One window for both:
# a button per language of mt2009lang.Languages() (its own name), the chosen one marked.
#   - a click saves the choice (game1.cfg LANGUAGE); in the game it also tells the server ("/lang <code>", the server's
#     texts, bots and quests follow at once);
#   - the client's own texts, names and descriptions change at the next start: "Uruchom ponownie" starts the client
#     again on an exe with app.Mt2009Restart (exe-src21), else the window asks the player to restart it.
# Python 2.7 as the client has it; the texts are CP1250 escapes (mt2009lang translates them like any other).

import ui
import mt2009lang

TEXT_TITLE = "J\xeazyk / Language"
TEXT_CURRENT = "J\xeazyk klienta: %s"
TEXT_CHOSEN = "Po ponownym uruchomieniu: %s"
TEXT_NOTE1 = "Nazwy, opisy i okna zmieni\xb9 j\xeazyk po ponownym"
TEXT_NOTE2 = "uruchomieniu klienta (Language: after a restart)."
TEXT_NOTE_EXE = "Ten klient pokazuje tylko j\xeazyki z alfabetem \xb3aci\xf1skim (Latin only)."
TEXT_RESTART = "Uruchom ponownie"
TEXT_CLOSE = "Zamknij"
TEXT_RESTART_FAILED = "Uruchom klienta ponownie (Restart the client)."

COLOR_INFO = 0xffc8c8c8
COLOR_NOTE = 0xff9be27c
COLOR_MARK = 0xfff1e6c0

WIDTH = 240
COLS = 2
BUTTON_W = 88
ROW_H = 26

_window = {"page": None}


def GetWindow():
	"""the options tab's page (one for the client's run)"""
	if _window["page"] is None:
		_window["page"] = LanguageWindow(inGame=True)
	return _window["page"]


def _InGame():
	try:
		return __import__("warpsafe").InGame()
	except Exception:
		return False


class LanguageWindow(ui.BoardWithTitleBar):

	def __init__(self, inGame=False):
		ui.BoardWithTitleBar.__init__(self)
		self.inGame = inGame
		self.widgets = []
		self.buttons = {}
		self.AddFlag("movable")
		self.AddFlag("float")
		self.SetTitleName(TEXT_TITLE)
		self.SetCloseEvent(ui.__mem_func__(self.Close))
		self.__Build()
		self.SetCenterPosition()

	def __del__(self):
		ui.BoardWithTitleBar.__del__(self)

	def Destroy(self):
		self.Hide()
		for w in self.widgets:
			try:
				w.Hide()
			except Exception:
				pass
		self.widgets = []
		self.buttons = {}

	def __Label(self, x, y, text, color=None):
		line = ui.TextLine()
		line.SetParent(self)
		line.SetPosition(x, y)
		line.SetText(text)
		if color is not None:
			line.SetPackedFontColor(color)
		line.Show()
		self.widgets.append(line)
		return line

	def __Button(self, x, y, text, event, arg=None, large=True):
		button = ui.Button()
		button.SetParent(self)
		button.SetPosition(x, y)
		size = "large" if large else "middle"
		button.SetUpVisual("d:/ymir work/ui/public/%s_button_01.sub" % size)
		button.SetOverVisual("d:/ymir work/ui/public/%s_button_02.sub" % size)
		button.SetDownVisual("d:/ymir work/ui/public/%s_button_03.sub" % size)
		button.SetText(text)
		if arg is None:
			button.SAFE_SetEvent(event)
		else:
			button.SAFE_SetEvent(event, arg)
		button.Show()
		self.widgets.append(button)
		return button

	def __Build(self):
		y = 34
		self.currentLine = self.__Label(16, y, "", COLOR_INFO)
		self.chosenLine = self.__Label(16, y + 15, "", COLOR_MARK)
		y += 38
		langs = mt2009lang.Languages()
		gap = (WIDTH - COLS * BUTTON_W) / (COLS + 1)
		for i, (code, name, cp) in enumerate(langs):
			col = i % COLS
			row = i / COLS
			x = gap + col * (BUTTON_W + gap)
			self.buttons[code] = (self.__Button(x, y + row * ROW_H, name, self.OnChoose, code), name)
		y += ((len(langs) + COLS - 1) / COLS) * ROW_H + 6
		self.__Label(16, y, TEXT_NOTE1, COLOR_NOTE)
		self.__Label(16, y + 15, TEXT_NOTE2, COLOR_NOTE)
		y += 32
		if not mt2009lang.ExeSwitchesCodePage():
			self.__Label(16, y, TEXT_NOTE_EXE, COLOR_INFO)
			y += 18
		self.restartButton = None
		if mt2009lang.CanRestart():
			self.restartButton = self.__Button(gap, y, TEXT_RESTART, self.OnRestart)
		self.__Button(WIDTH - gap - BUTTON_W, y, TEXT_CLOSE, self.Close)
		self.SetSize(WIDTH, y + 40)
		self.Refresh()

	def Refresh(self):
		current = mt2009lang.Language()
		chosen = mt2009lang.ChosenLanguage()
		self.currentLine.SetText(TEXT_CURRENT % mt2009lang.LanguageName(current))
		if chosen != current:
			self.chosenLine.SetText(TEXT_CHOSEN % mt2009lang.LanguageName(chosen))
		else:
			self.chosenLine.SetText("")
		for code, (button, name) in self.buttons.items():
			if code == chosen:
				button.SetText("> %s <" % name)
				button.Down()
			else:
				button.SetText(name)
				button.SetUp()
		if self.restartButton:
			if chosen != current:
				self.restartButton.Enable()
			else:
				self.restartButton.Disable()

	def OnChoose(self, code):
		inGame = self.inGame and _InGame()
		mt2009lang.SetLanguage(code, inGame=inGame)
		self.Refresh()

	def OnRestart(self):
		if mt2009lang.ChosenLanguage() == mt2009lang.Language():
			return
		if not mt2009lang.Restart():
			self.chosenLine.SetText(TEXT_RESTART_FAILED)

	def Open(self):
		self.Refresh()
		self.Show()
		self.SetTop()

	def Close(self):
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True
