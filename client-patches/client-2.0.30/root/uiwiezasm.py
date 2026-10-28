# MT2009_PLUS_SMH_TOWER_V3: Piekielna Wieza Sunga Mahi in the client (the owner, 28 October 2026) - the tower window at
# the hall portal, the floor board in place of the minimap inside the tower and the defeat popup in place of the
# restart window. Ported from the tower package's client root (uiSungMahi.py, the minimap's SungMahiCover, uirestart's
# defeat box; their texts were Romanian - Polish here) on GF 26.1.11's uiscripts uiscript/sungmaheetowerenter.py and
# uiscript/sungmaheetowerinformationboard.py (root/uiscript) and GF's images d:/ymir work/ui/game/sungmahee_tower/*.sub,
# d:/ymir work/ui/smhtower_01.dds and the affect icons as wieza_buff.sub / wieza_debuff.sub (the pack "wieza",
# tools/wieza/build_wieza_packs.py). No exe
# change and no new packet: the package's exe text measuring (GetCharSize) is not used - long lines scroll by a
# python-only marquee (a moving window of characters).
#
# The server half is the quest wieza_sung_mahi (linux-port/docker/game/quest/wieza_sung_mahi.quest):
#   server -> client  "WSM clear"
#                     "WSM f <floor> <cleared 0/1> <my best time s> <my place> <element 0-6> [<vnum> <count>] x5"
#                     "WSM open <quest index> <cleared floors> <highest open floor> <Sztandary Czaszki>"
#                     "WSM board <floor> <stage 1-3> <cleared stages mask> <seconds left> <seconds of the stage>"
#                     "WSM goal <text>", "WSM fx <0 none / 1 blessing / 2 curse> <text>", "WSM defeat"
#   client -> server  the quest's "button" event (event.QuestButtonClick(<quest index>)) and its input() answered with
#                     a number: 1-50 enter that floor, 100 leave the tower, 101 the board again, 102 the window again.
#                     The quest window of that input is not shown (game.OpenQuestWindow asks ConsumeQuestWindow).
# game.py: Register(self) with the server commands, DestroyWindow() when the game window closes, ConsumeQuestWindow()
# in OpenQuestWindow and OnGameOver() before the restart window.
#
# Python 2.7 as the client has it; the texts are CP1250 escapes.

import app
import background
import chat
import event
import net
import ui
import uiCommon
import wndMgr

TOWER_MAP = "metin2_map_smhdungeon_02"
ROOT_PATH = "d:/ymir work/ui/game/sungmahee_tower/"
MAX_FLOOR = 50
REWARD_SLOTS = 5
LIST_ROWS = 5
LIST_X, LIST_Y, LIST_STEP = 15, 38, 31

BTN_EXIT = 100
BTN_BOARD = 101

TEXT_FLOOR = "Pi\xeatro %d"
TEXT_RANK = "%d. miejsce"
TEXT_NO_RANK = "-"
TEXT_TIME = "Najlepszy czas: %s"
TEXT_ELEMENT_TIP = "\xafywio\xb3 potwor\xf3w na tym pi\xeatrze"
TEXT_ELEMENTS = ("Wszystkie \xbfywio\xb3y", "Ogie\xf1", "L\xf3d", "B\xb3yskawica", "Wiatr", "Ziemia", "Mrok")
TEXT_ASK_ENTER = "Wej\x9c\xe6 na %d. pi\xeatro Wie\xbfy Sung Mahi?"
TEXT_ASK_ENTER2 = "Wspinaczka zabiera 1 Sztandar Czaszki (masz: %d)."
TEXT_LOCKED = "Najpierw uko\xf1cz %d. pi\xeatro w tym sezonie."
TEXT_ASK_EXIT = "Opu\x9cci\xe6 Wie\xbf\xea Sung Mahi?"
TEXT_ASK_EXIT2 = "Wspinaczka si\xea sko\xf1czy - wr\xf3cisz do hali."
TEXT_STAGE = "Etap %d: %s"
TEXT_DEFEAT = "Gorzka pora\xbfka! Twoja wspinaczka ko\xf1czy si\xea tutaj."
TEXT_DEFEAT2 = "Za chwil\xea wr\xf3cisz do hali wie\xbfy."
TEXT_OK = "OK"

COLOR_BLESS = 0xff9be37c
COLOR_CURSE = 0xffff7a6b
COLOR_CLEARED = 0xffffd76b

QUEST_WINDOW_WAIT = 5.0       # seconds the input window of a click is waited for
MARQUEE_STEP = 0.18           # seconds per character of a scrolling line
DEFEAT_FALLBACK = 10.0        # the server's warp did not come: the usual restart window after this many seconds

_state = {
	'game': None,
	'qid': -1,
	'pending': None,
	'pendingTime': 0.0,
	'enter': None,
	'board': None,
	'defeat': None,
	'floors': {},
	'inside': False,
}


def ToInt(value, default=0):
	try:
		return int(value)
	except (TypeError, ValueError):
		return default


def FormatTime(sec):
	sec = max(0, int(sec))
	return "%d:%02d" % (sec / 60, sec % 60)


def InTower():
	if _state['inside']:
		return True
	try:
		return str(background.GetCurrentMapName()) == TOWER_MAP
	except Exception:
		return False


def Send(action):
	# the quest's "button" event, then its input() gets the number (ConsumeQuestWindow)
	if _state['qid'] < 0:
		return
	_state['pending'] = str(action)
	_state['pendingTime'] = app.GetTime()
	event.QuestButtonClick(_state['qid'])


def ConsumeQuestWindow(skin, idx):
	"""game.OpenQuestWindow: True when this is the input window of a tower click - answered here, never shown."""
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


def _Interface():
	game = _state['game']
	if game is None:
		return None
	try:
		return game.interface
	except Exception:
		return None


class Marquee(ui.TextLine):
	"""A line that scrolls when it is longer than its width (a moving window of characters, python only)."""

	def __init__(self, chars):
		ui.TextLine.__init__(self)
		self.chars = chars
		self.fullText = ""
		self.offset = 0
		self.nextTime = 0.0

	def __del__(self):
		ui.TextLine.__del__(self)

	def SetMarqueeText(self, text):
		if text == self.fullText:
			return
		self.fullText = text
		self.offset = 0
		self.nextTime = app.GetTime() + 1.0
		if len(text) <= self.chars:
			self.SetText(text)
		else:
			self.SetText(text[:self.chars])

	def Tick(self):
		text = self.fullText
		if len(text) <= self.chars or app.GetTime() < self.nextTime:
			return
		loop = text + "     "
		self.offset = (self.offset + 1) % len(loop)
		self.nextTime = app.GetTime() + MARQUEE_STEP
		if self.offset == 0:
			self.nextTime += 1.0
		double = loop + loop
		self.SetText(double[self.offset:self.offset + self.chars])


class FloorButton(ui.RadioButton):

	def __init__(self):
		ui.RadioButton.__init__(self)
		self.floor = 0
		self.clearIcon = None
		self.SetUpVisual(ROOT_PATH + "floor_button_default.sub")
		self.SetOverVisual(ROOT_PATH + "floor_button_over.sub")
		self.SetDownVisual(ROOT_PATH + "floor_button_down.sub")
		icon = ui.ImageBox()
		icon.SetParent(self)
		icon.LoadImage(ROOT_PATH + "clear_icon.sub")
		icon.SetPosition(107, 7)
		icon.AddFlag("not_pick")
		icon.Hide()
		self.clearIcon = icon

	def __del__(self):
		ui.RadioButton.__del__(self)

	def SetFloor(self, floor, cleared):
		self.floor = floor
		self.SetText(TEXT_FLOOR % floor)
		if cleared:
			self.clearIcon.Show()
		else:
			self.clearIcon.Hide()

	def Destroy(self):
		self.clearIcon = None


class TowerEnterWindow(ui.ScriptWindow):
	"""GF's sungmaheetowerenter: 50 floors (5 rows and a scrollbar), the floor's rewards, element, my place and time."""

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.tooltipItem = None
		self.dialog = None
		self.buttons = []
		self.first = 1
		self.selected = 1
		self.cleared = 0
		self.top = 1
		self.banners = 0
		self.rewards = []
		ui.PythonScriptLoader().LoadScriptFile(self, "uiscript/sungmaheetowerenter.py")
		get = self.GetChild
		self.board = get("board")
		self.scrollbar = get("floor_scrollbar")
		self.rewardSlot = get("reward_slot")
		self.rankText = get("my_rank_text")
		self.timeText = get("my_rank_time_text")
		self.elementText = get("element_text")
		self.elementWindow = get("element_text_window")
		self.board.SetCloseEvent(ui.__mem_func__(self.Close))
		get("enter_button").SetEvent(ui.__mem_func__(self.OnEnter))
		self.scrollbar.SetScrollEvent(ui.__mem_func__(self.OnScroll))
		self.scrollbar.SetMiddleBarSize(float(LIST_ROWS) / MAX_FLOOR)
		self.rewardSlot.SetOverInItemEvent(ui.__mem_func__(self.OnOverInSlot))
		self.rewardSlot.SetOverOutItemEvent(ui.__mem_func__(self.OnOverOut))
		self.elementWindow.SAFE_SetEvent("MOUSE_OVER_IN", self.OnOverInElement)
		self.elementWindow.SAFE_SetEvent("MOUSE_OVER_OUT", self.OnOverOut)
		for i in xrange(LIST_ROWS):
			button = FloorButton()
			button.SetParent(self.board)
			button.SetPosition(LIST_X, LIST_Y + i * LIST_STEP)
			button.SetEvent(lambda arg=i: self.OnClickRow(arg))
			button.Show()
			self.buttons.append(button)
		self.SetCenterPosition()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def SetItemToolTip(self, tooltipItem):
		self.tooltipItem = tooltipItem

	def SetHeader(self, cleared, top, banners):
		self.cleared = max(0, min(MAX_FLOOR, cleared))
		self.top = max(1, min(MAX_FLOOR, top))
		self.banners = banners
		self.selected = self.top
		# the open floor in the list's view, as GF's window scrolls to it
		self.first = max(1, min(MAX_FLOOR - LIST_ROWS + 1, self.top - LIST_ROWS / 2))
		self.scrollbar.SetPos(float(self.first - 1) / float(MAX_FLOOR - LIST_ROWS))

	def OnScroll(self):
		first = int(self.scrollbar.GetPos() * (MAX_FLOOR - LIST_ROWS) + 0.5) + 1
		if first != self.first:
			self.first = first
			self.RefreshList()

	def OnClickRow(self, row):
		self.selected = self.first + row
		self.Refresh()

	def RefreshList(self):
		floors = _state['floors']
		for i in xrange(LIST_ROWS):
			floor = self.first + i
			info = floors.get(floor)
			button = self.buttons[i]
			button.SetFloor(floor, info is not None and info[0])
			if floor == self.selected:
				button.Down()
			else:
				button.SetUp()

	def Refresh(self):
		self.RefreshList()
		info = _state['floors'].get(self.selected, (0, 0, 0, 0, []))
		cleared, seconds, place, element, rewards = info
		if place > 0:
			self.rankText.SetText(TEXT_RANK % place)
		else:
			self.rankText.SetText(TEXT_NO_RANK)
		if seconds > 0:
			self.timeText.SetText(TEXT_TIME % FormatTime(seconds))
		else:
			self.timeText.SetText(TEXT_NO_RANK)
		if 0 <= element < len(TEXT_ELEMENTS):
			self.elementText.SetText(TEXT_ELEMENTS[element])
		else:
			self.elementText.SetText("")
		self.rewards = rewards[:REWARD_SLOTS]
		for slot in xrange(REWARD_SLOTS):
			self.rewardSlot.ClearSlot(slot)
		for slot, (vnum, count) in enumerate(self.rewards):
			self.rewardSlot.SetItemSlot(slot, vnum, count)
		self.rewardSlot.RefreshSlot()

	def OnOverInSlot(self, slot):
		if not self.tooltipItem or slot >= len(self.rewards):
			return
		self.tooltipItem.SetItemToolTip(self.rewards[slot][0])
		self.tooltipItem.ShowToolTip()

	def OnOverInElement(self):
		if not self.tooltipItem:
			return
		self.tooltipItem.ClearToolTip()
		self.tooltipItem.AppendTextLine(TEXT_ELEMENT_TIP)
		self.tooltipItem.ResizeToolTip()
		self.tooltipItem.ShowToolTip()

	def OnOverOut(self):
		if self.tooltipItem:
			self.tooltipItem.HideToolTip()

	def __CloseDialog(self):
		dialog = self.dialog
		self.dialog = None
		if dialog:
			try:
				dialog.Close()
			except Exception:
				pass

	def OnEnter(self):
		floor = self.selected
		if floor > self.top:
			chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_LOCKED % (floor - 1))
			return
		self.__CloseDialog()
		dialog = uiCommon.QuestionDialog2()
		dialog.SetText1(TEXT_ASK_ENTER % floor)
		dialog.SetText2(TEXT_ASK_ENTER2 % self.banners)
		dialog.SetAcceptEvent(lambda arg=floor: self.__Accept(arg))
		dialog.SetCancelEvent(ui.__mem_func__(self.__CloseDialog))
		dialog.Open()
		self.dialog = dialog

	def __Accept(self, floor):
		self.__CloseDialog()
		Send(floor)
		self.Close()

	def Open(self):
		self.Refresh()
		self.Show()
		self.SetTop()

	def Close(self):
		self.__CloseDialog()
		self.OnOverOut()
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def Destroy(self):
		self.__CloseDialog()
		for button in self.buttons:
			button.Destroy()
		self.buttons = []
		self.tooltipItem = None
		self.ClearDictionary()
		self.Hide()


class FloorBoard(ui.ScriptWindow):
	"""GF's sungmaheetowerinformationboard in place of the minimap: floor, cleared stages, the stage's goal, its time,
	the exit X and the stage's blessing or curse."""

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.dialog = None
		self.endTime = 0.0
		self.total = 0
		self.stage = 1
		self.goal = ""
		self.nextCheck = 0.0
		ui.PythonScriptLoader().LoadScriptFile(self, "uiscript/sungmaheetowerinformationboard.py")
		get = self.GetChild
		self.floorText = get("floor_text")
		self.stageIcons = [get("1stage_clear_icon"), get("2stage_clear_icon"), get("3stage_clear_icon")]
		self.timeGauge = get("time_gauge")
		self.timeText = get("time_text")
		self.effectWindow = get("effect_window")
		self.effectIcon = get("effect_icon")
		self.effectIcon.SetScale(0.7, 0.7)
		get("exit_button").SetEvent(ui.__mem_func__(self.OnExit))
		# the goal and the blessing / curse: GF's text windows, our marquee lines in them
		alarm = get("alarm_text")
		alarm.Hide()
		self.goalLine = Marquee(16)
		self.goalLine.SetParent(get("alarm_text_window"))
		self.goalLine.SetPosition(0, 0)
		self.goalLine.SetWindowHorizontalAlignCenter()
		self.goalLine.SetHorizontalAlignCenter()
		self.goalLine.Show()
		effect = get("effect_text")
		effect.Hide()
		self.effectLine = Marquee(17)
		self.effectLine.SetParent(get("effect_text_window"))
		self.effectLine.SetPosition(0, 0)
		self.effectLine.SetWindowHorizontalAlignCenter()
		self.effectLine.SetHorizontalAlignCenter()
		self.effectLine.Show()
		self.effectWindow.Hide()
		for icon in self.stageIcons:
			icon.Hide()
		self.SetPosition(wndMgr.GetScreenWidth() - self.GetWidth(), 2)

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def SetBoard(self, floor, stage, mask, left, total):
		self.floorText.SetText(str(floor))
		self.stage = max(1, min(3, stage))
		for i in xrange(3):
			if mask & (1 << i):
				self.stageIcons[i].Show()
			else:
				self.stageIcons[i].Hide()
		self.total = max(0, total)
		self.endTime = app.GetTime() + max(0, left)
		self.__ShowGoal()
		self.__UpdateTime()

	def SetGoal(self, text):
		self.goal = text
		self.__ShowGoal()

	def __ShowGoal(self):
		if self.goal:
			self.goalLine.SetMarqueeText(TEXT_STAGE % (self.stage, self.goal))
		else:
			self.goalLine.SetMarqueeText("")

	def SetEffect(self, kind, text):
		if kind <= 0 or not text:
			self.effectWindow.Hide()
			return
		if kind == 2:
			self.effectIcon.LoadImage(ROOT_PATH + "wieza_debuff.sub")
			self.effectLine.SetPackedFontColor(COLOR_CURSE)
		else:
			self.effectIcon.LoadImage(ROOT_PATH + "wieza_buff.sub")
			self.effectLine.SetPackedFontColor(COLOR_BLESS)
		self.effectIcon.SetScale(0.7, 0.7)
		self.effectLine.SetMarqueeText(text)
		self.effectWindow.Show()

	def __UpdateTime(self):
		if self.total <= 0:
			self.timeGauge.SetPercentage(0, 1)
			self.timeText.SetText("")
			return
		left = max(0, int(self.endTime - app.GetTime() + 0.5))
		self.timeGauge.SetPercentage(left, self.total)
		self.timeText.SetText(FormatTime(left))

	def OnUpdate(self):
		self.goalLine.Tick()
		self.effectLine.Tick()
		now = app.GetTime()
		if now >= self.nextCheck:
			self.nextCheck = now + 0.5
			self.__UpdateTime()
			# the board stands where the minimap is: the minimap stays hidden inside the tower
			interface = _Interface()
			try:
				miniMap = interface.wndMiniMap
				if miniMap and miniMap.IsShow():
					miniMap.Hide()
			except Exception:
				pass

	def __CloseDialog(self):
		dialog = self.dialog
		self.dialog = None
		if dialog:
			try:
				dialog.Close()
			except Exception:
				pass

	def OnExit(self):
		self.__CloseDialog()
		dialog = uiCommon.QuestionDialog2()
		dialog.SetText1(TEXT_ASK_EXIT)
		dialog.SetText2(TEXT_ASK_EXIT2)
		dialog.SetAcceptEvent(ui.__mem_func__(self.__AcceptExit))
		dialog.SetCancelEvent(ui.__mem_func__(self.__CloseDialog))
		dialog.Open()
		self.dialog = dialog

	def __AcceptExit(self):
		self.__CloseDialog()
		Send(BTN_EXIT)

	def Destroy(self):
		self.__CloseDialog()
		self.goalLine = None
		self.effectLine = None
		self.stageIcons = []
		self.ClearDictionary()
		self.Hide()


class DefeatPopup(ui.Board):
	"""The package's defeat box in place of the restart window inside the tower; the server takes the player to the
	hall. Should that not come, the usual restart window opens after DEFEAT_FALLBACK seconds."""

	def __init__(self):
		ui.Board.__init__(self)
		self.shownAt = 0.0
		self.fallbackDone = False
		self.widgets = []
		self.SetSize(320, 104)
		self.AddFlag("float")
		for y, text in ((24, TEXT_DEFEAT), (44, TEXT_DEFEAT2)):
			line = ui.TextLine()
			line.SetParent(self)
			line.SetPosition(160, y)
			line.SetHorizontalAlignCenter()
			line.SetText(text)
			line.Show()
			self.widgets.append(line)
		button = ui.Button()
		button.SetParent(self)
		button.SetUpVisual("d:/ymir work/ui/public/middle_button_01.sub")
		button.SetOverVisual("d:/ymir work/ui/public/middle_button_02.sub")
		button.SetDownVisual("d:/ymir work/ui/public/middle_button_03.sub")
		button.SetPosition(160 - 30, 68)
		button.SetText(TEXT_OK)
		button.SetEvent(ui.__mem_func__(self.Hide))
		button.Show()
		self.widgets.append(button)
		self.SetPosition(wndMgr.GetScreenWidth() / 2 - 160, wndMgr.GetScreenHeight() / 2 - 100)

	def __del__(self):
		ui.Board.__del__(self)

	def Open(self):
		if not self.IsShow():
			self.shownAt = app.GetTime()
			self.fallbackDone = False
		self.Show()
		self.SetTop()

	def OnUpdate(self):
		if self.fallbackDone or app.GetTime() - self.shownAt < DEFEAT_FALLBACK:
			return
		self.fallbackDone = True
		self.Hide()
		interface = _Interface()
		try:
			interface.OpenRestartDialog()
		except Exception:
			pass

	def OnPressEscapeKey(self):
		self.Hide()
		return True

	def Destroy(self):
		self.widgets = []
		self.Hide()


def __Create(key, factory, name):
	window = _state[key]
	if window is None:
		import uiminigameutil
		window = uiminigameutil.SafeCreate(factory, name)
		_state[key] = window
	return window


def __EnterWindow():
	window = __Create('enter', TowerEnterWindow, "Wie\xbfa Sung Mahi")
	if window is not None and window.tooltipItem is None:
		interface = _Interface()
		try:
			window.SetItemToolTip(interface.tooltipItem)
		except Exception:
			pass
	return window


def __ShowDefeat():
	interface = _Interface()
	try:
		interface.CloseRestartDialog()
	except Exception:
		pass
	popup = __Create('defeat', DefeatPopup, "Wie\xbfa Sung Mahi")
	if popup is not None:
		popup.Open()


def OnCommand(game, *args):
	if not args:
		return
	sub, rest = args[0], args[1:]
	try:
		if sub == 'clear':
			_state['floors'] = {}
		elif sub == 'f' and len(rest) >= 5:
			floor = ToInt(rest[0])
			rewards = []
			pairs = rest[5:]
			for i in xrange(0, len(pairs) - 1, 2):
				vnum, count = ToInt(pairs[i]), ToInt(pairs[i + 1])
				if vnum > 0:
					rewards.append((vnum, count))
			if 1 <= floor <= MAX_FLOOR:
				_state['floors'][floor] = (ToInt(rest[1]) != 0, ToInt(rest[2]), ToInt(rest[3]), ToInt(rest[4]), rewards)
		elif sub == 'open' and len(rest) >= 3:
			_state['qid'] = ToInt(rest[0], -1)
			window = __EnterWindow()
			if window is not None:
				banners = 0
				if len(rest) >= 4:
					banners = ToInt(rest[3])
				window.SetHeader(ToInt(rest[1]), ToInt(rest[2]), banners)
				window.Open()
		elif sub == 'board' and len(rest) >= 5:
			_state['inside'] = True
			board = __Create('board', FloorBoard, "Wie\xbfa Sung Mahi")
			if board is not None:
				board.SetBoard(ToInt(rest[0]), ToInt(rest[1]), ToInt(rest[2]), ToInt(rest[3]), ToInt(rest[4]))
				if not board.IsShow():
					board.Show()
				board.SetTop()
		elif sub == 'goal':
			board = _state['board']
			if board is not None:
				board.SetGoal(" ".join(rest))
		elif sub == 'fx':
			board = _state['board']
			if board is not None:
				kind = 0
				if rest:
					kind = ToInt(rest[0])
				board.SetEffect(kind, " ".join(rest[1:]))
		elif sub == 'qid' and rest:
			_state['qid'] = ToInt(rest[0], -1)
		elif sub == 'defeat':
			_state['inside'] = True
			__ShowDefeat()
	except Exception:
		import dbg
		import sys
		dbg.TraceError('uiwiezasm.OnCommand %s: %s' % (str(args), str(sys.exc_info()[1])))


def OnGameOver(game):
	"""game.OnGameOver: True when the death was inside the tower - the defeat popup instead of the restart window."""
	if not InTower():
		return False
	try:
		__ShowDefeat()
	except Exception:
		return False
	return _state['defeat'] is not None


class _Command:
	def __init__(self, func):
		self.func = func

	def __call__(self, *args):
		game = _state['game']
		if game is None:
			return None
		try:
			return self.func(game, *args)
		except ReferenceError:
			return None

	def GetArgumentCount(self):
		# stringCommander.Analyzer asks it only without variadic commands
		# (constInfo.ENABLE_CMDCHAT_VARIADIC_ARGS is on in this client).
		return 1


def Register(game):
	"""game.py, once its own commands are in: the "WSM" lines go straight into its serverCommander."""
	try:
		from _weakref import proxy
		_state['game'] = proxy(game)
	except Exception:
		_state['game'] = None
	commander = getattr(game, "serverCommander", None)
	if commander is None or not hasattr(commander, "cmdDict"):
		return
	if "WSM" not in commander.cmdDict:
		commander.cmdDict["WSM"] = _Command(OnCommand)


def DestroyWindow():
	"""The game window closes (a warp, a channel change, the logout)."""
	for key in ('enter', 'board', 'defeat'):
		window = _state[key]
		_state[key] = None
		if window is not None:
			try:
				window.Destroy()
			except Exception:
				pass
	_state['pending'] = None
	_state['inside'] = False
	_state['game'] = None
