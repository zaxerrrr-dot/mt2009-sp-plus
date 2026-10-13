# Poziom Czempiona - the Champion level and the Sung Ma stats, Stage A (MT2009_PLUS_CHAMPION_V1,
# MT2009_PLUS_SUNGMA_V1; server-patches/czempion/README.md).
#
# The exe 2.0.25 has no Champion points (app.ENABLE_CONQUEROR_LEVEL = 0, GF's uicharacternew.py sleeps), so
# the server sends the numbers as chat commands (playerbot_champion.cpp) and this window draws them:
#
#   server -> "champion_info <level> <exp> <next exp> <free points> <str> <hp> <move> <immune> <step>"
#             (at login, after every gain, point and reset; the stats with what items add)
#             "sungma_map <str> <hp> <move> <immune>" (the map's requirements at login, all 0 off a Sung Ma map)
#   window -> "/conqueror_stat smh_str|smh_hp|smh_move|smh_inmune" (a point; GF's command names)
#             "/conqueror_stat info" (the numbers again, when the window opens)
#
# Opened by the key "Czempion" (keybind.py, no key by default). Stage B (a new exe) replaces this with
# GF's character window page (uicharacternew.py) and the points packet.
#
# Python 2.7 as the client has it; the texts are CP1250 escapes.

import app
import net
import ui
import warpsafe

TEXT_TITLE = "Poziom Czempiona"
TEXT_NONE_1 = "Nie jeste\x9c jeszcze Czempionem."
TEXT_NONE_2 = "Pos\xb9g Wojownika nada Ci ten poziom: najwy\xbfszy"
TEXT_NONE_3 = "poziom, obrona statku przed Hydr\xb9 i pe\xb3na kula"
TEXT_NONE_4 = "do\x9cwiadczenia na najwy\xbfszym poziomie."
TEXT_LEVEL = "Poziom Czempiona: %d"
TEXT_LEVEL_MAX = "Poziom Czempiona: %d (najwy\xbfszy)"
TEXT_EXP = "Do\x9cwiadczenie: %s / %s (%.1f%%)"
TEXT_POINTS = "Wolne punkty Sung Ma: %d"
TEXT_HEAD_STAT = "Statystyka Sung Ma"
TEXT_HEAD_VALUE = "Masz"
TEXT_HEAD_MAP = "Mapa"
TEXT_MAP_NONE = "Ta mapa nie jest ziemi\xb9 Sung Ma."
TEXT_MAP_OK = "Spe\xb3niasz wymagania tej mapy."
TEXT_MAP_SHORT = "Za ma\xb3o (czerwone): ta cecha s\xb3abnie o po\xb3ow\xea."

STATS = (
	# (name, command, what a shortage costs on a Sung Ma map)
	("Si\xb3a", "smh_str", "obra\xbfenia zadawane potworom /2"),
	("Witalno\x9c\xe6", "smh_hp", "maksymalne P\xaf /2"),
	("Odporno\x9c\xe6", "smh_move", "pr\xeadko\x9c\xe6 ruchu /2"),
	("Inteligencja", "smh_inmune", "trucizna, ogie\xf1, krwawienie rzadziej"),
)

COLOR_TEXT = 0xffd8d8d8
COLOR_GOLD = 0xfff2d17a
COLOR_OK = 0xff7fd37f
COLOR_SHORT = 0xffff6a5a
COLOR_DIM = 0xff9a9a9a

_state = {
	'window': None,
	'info': (0, 0, 0, 0, 0, 0, 0, 0, 0),	# level, exp, next, points, str, hp, move, immune, step
	'map': (0, 0, 0, 0),
}


def ToInt(value, default=0):
	try:
		return int(value)
	except (TypeError, ValueError):
		try:
			return int(float(value))
		except (TypeError, ValueError):
			return default


def Number(value):
	text = str(value)
	parts = []
	while len(text) > 3:
		parts.insert(0, text[-3:])
		text = text[:-3]
	parts.insert(0, text)
	return " ".join(parts)


def Send(command):
	# MT2009_PLUS_SIDEKICK_WARP_SAFE_V1: only in the game phase (warpsafe.py).
	if not warpsafe.InGame():
		return False
	net.SendChatPacket("/conqueror_stat " + command)
	return True


def IsSungmaMap():
	return any(_state['map'])


class ChampionWindow(ui.BoardWithTitleBar):
	WIDTH = 320
	HEIGHT = 312
	ROW_Y = 132
	ROW_STEP = 22

	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)
		self.widgets = []
		self.plusButtons = []
		self.statValues = []
		self.statNeeds = []
		self.statCosts = []
		self.lastAsk = -100.0
		self.AddFlag('movable')
		self.AddFlag('float')
		self.SetSize(self.WIDTH, self.HEIGHT)
		self.SetTitleName(TEXT_TITLE)
		self.SetCloseEvent(ui.__mem_func__(self.Close))
		self.__Build()
		self.SetCenterPosition()

	def __Label(self, x, y, text="", color=COLOR_TEXT):
		line = ui.TextLine()
		line.SetParent(self)
		line.SetPosition(x, y)
		line.SetText(text)
		line.SetPackedFontColor(color)
		line.Show()
		self.widgets.append(line)
		return line

	def __Bar(self, x, y, width, height, color):
		bar = ui.Bar()
		bar.SetParent(self)
		bar.SetPosition(x, y)
		bar.SetSize(width, height)
		bar.SetColor(color)
		bar.Show()
		self.widgets.append(bar)
		return bar

	def __PlusButton(self, x, y, command):
		button = ui.Button()
		button.SetParent(self)
		button.SetPosition(x, y)
		root = "d:/ymir work/ui/game/windows/"
		button.SetUpVisual(root + "btn_plus_up.sub")
		button.SetOverVisual(root + "btn_plus_over.sub")
		button.SetDownVisual(root + "btn_plus_down.sub")
		button.SetEvent(lambda c=command: Send(c))
		button.Hide()
		self.widgets.append(button)
		return button

	def __Build(self):
		self.lineLevel = self.__Label(16, 36, "", COLOR_GOLD)
		self.lineExp = self.__Label(16, 56)
		self.__Bar(16, 76, self.WIDTH - 32, 8, 0xff202020)
		self.expFill = self.__Bar(17, 77, 1, 6, 0xff3f8fe0)
		self.linePoints = self.__Label(16, 92)
		self.__Label(16, 112, TEXT_HEAD_STAT, COLOR_DIM)
		self.__Label(150, 112, TEXT_HEAD_VALUE, COLOR_DIM)
		self.__Label(200, 112, TEXT_HEAD_MAP, COLOR_DIM)
		for i, (name, command, cost) in enumerate(STATS):
			y = self.ROW_Y + i * self.ROW_STEP
			self.__Label(16, y, name)
			self.statValues.append(self.__Label(150, y))
			self.statNeeds.append(self.__Label(200, y))
			self.plusButtons.append(self.__PlusButton(260, y, command))
		self.lineMap = self.__Label(16, self.ROW_Y + 4 * self.ROW_STEP + 6)
		for i, (name, command, cost) in enumerate(STATS):
			self.statCosts.append(self.__Label(24, self.ROW_Y + 4 * self.ROW_STEP + 24 + i * 14, "", COLOR_DIM))
		self.noneLines = [self.__Label(16, 150 + i * 18, text) for i, text in
				enumerate((TEXT_NONE_1, TEXT_NONE_2, TEXT_NONE_3, TEXT_NONE_4))]

	def Refresh(self):
		level, exp, nextExp, points, sStr, sHp, sMove, sImm, step = _state['info']
		values = (sStr, sHp, sMove, sImm)
		needs = _state['map']
		champion = level > 0
		for line in self.noneLines:
			if champion:
				line.Hide()
			else:
				line.Show()
		rows = self.statValues + self.statNeeds + self.statCosts + [self.lineExp, self.linePoints, self.lineMap]
		for line in rows:
			if champion:
				line.Show()
			else:
				line.Hide()
		if not champion:
			self.lineLevel.SetText(TEXT_TITLE)
			self.expFill.SetSize(1, 6)
			for button in self.plusButtons:
				button.Hide()
			return
		if nextExp > 0:
			self.lineLevel.SetText(TEXT_LEVEL % level)
			pct = min(100.0, 100.0 * exp / nextExp)
			self.lineExp.SetText(TEXT_EXP % (Number(exp), Number(nextExp), pct))
		else:
			self.lineLevel.SetText(TEXT_LEVEL_MAX % level)
			pct = 100.0
			self.lineExp.SetText("")
		self.expFill.SetSize(max(1, int((self.WIDTH - 34) * pct / 100.0)), 6)
		self.linePoints.SetText(TEXT_POINTS % points)
		short = False
		for i in xrange(4):
			self.statValues[i].SetText(str(values[i]))
			if IsSungmaMap():
				self.statNeeds[i].SetText(str(needs[i]))
				lacking = values[i] < needs[i]
				short = short or lacking
				self.statValues[i].SetPackedFontColor(COLOR_SHORT if lacking else COLOR_OK)
				self.statNeeds[i].SetPackedFontColor(COLOR_SHORT if lacking else COLOR_DIM)
			else:
				self.statNeeds[i].SetText("-")
				self.statValues[i].SetPackedFontColor(COLOR_TEXT)
				self.statNeeds[i].SetPackedFontColor(COLOR_DIM)
			self.statCosts[i].SetText("%s: %s" % (STATS[i][0], STATS[i][2]))
			if points > 0:
				self.plusButtons[i].Show()
			else:
				self.plusButtons[i].Hide()
		if not IsSungmaMap():
			self.lineMap.SetText(TEXT_MAP_NONE)
			self.lineMap.SetPackedFontColor(COLOR_DIM)
		elif short:
			self.lineMap.SetText(TEXT_MAP_SHORT)
			self.lineMap.SetPackedFontColor(COLOR_SHORT)
		else:
			self.lineMap.SetText(TEXT_MAP_OK)
			self.lineMap.SetPackedFontColor(COLOR_OK)

	def Open(self):
		self.Refresh()
		self.Show()
		self.SetTop()
		now = app.GetTime()
		if now - self.lastAsk > 2.0:
			self.lastAsk = now
			Send("info")

	def Close(self):
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def Destroy(self):
		self.Hide()
		for widget in self.widgets:
			widget.Hide()
		self.widgets = []
		self.plusButtons = []
		self.statValues = []
		self.statNeeds = []
		self.statCosts = []
		self.noneLines = []


# ---------------------------------------------------------------- commands (game.py)

def _RefreshWindow():
	window = _state['window']
	if window is not None and window.IsShow():
		try:
			window.Refresh()
		except Exception:
			import dbg
			import sys
			dbg.TraceError("uichampion.Refresh: %s" % str(sys.exc_info()[1]))


def OnInfo(*args):
	values = [ToInt(a) for a in args[:9]]
	while len(values) < 9:
		values.append(0)
	_state['info'] = tuple(values)
	_RefreshWindow()


def OnMap(*args):
	values = [ToInt(a) for a in args[:4]]
	while len(values) < 4:
		values.append(0)
	_state['map'] = tuple(values)
	_RefreshWindow()


def ToggleWindow():
	window = _state['window']
	if window is None:
		import uiminigameutil
		window = uiminigameutil.SafeCreate(ChampionWindow, TEXT_TITLE)
		if window is None:
			return
		_state['window'] = window
	if window.IsShow():
		window.Close()
	else:
		window.Open()


def DestroyWindow():
	window = _state['window']
	_state['window'] = None
	if window is not None:
		window.Destroy()
