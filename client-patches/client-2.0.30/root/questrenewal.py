# -*- coding: latin-1 -*-
# MT2009_PLUS_QUEST_RENEWAL_V1: the renewed quest window - QUEST_RENEWAL 1.0.0.6 ((C) 2019 Owsap Productions), the
# official client's quest page: the quests under eight folding categories (one open at a time) with a coloured mark on
# the ones that hold quests, each quest with its counter, its clock and a dot while its letter is still unread, and one
# letter on the screen's side in place of the column of letters (its tooltip tells how many wait).
#
# Adapted for our client and server:
#  - no exe change: the package sends a quest's category in the quest-info packet (a changed packet and exe); here the
#    server sends its quest index -> category map at the login as "QuestCategory <part> <index>:<category>,..." command
#    lines (server-patches/questren, playerbot_quest_renewal.cpp) and this module keeps it. A quest the map does not
#    name is in DEFAULT_CATEGORY. quest.GetQuestData keeps the exe's 4-tuple.
#  - the package's widgets (ui.py SubTitleBar / ListBar, Window.SetProperty, Button.SetTextAlignLeft) live here, so
#    ui.py is not touched; the layout (uiscript/characterwindow.py "Quest_Renewal_Board") is for our 253 x 405 window.
#  - the letters: a click on the side letter opens the quest page at that quest (the package's flow); a click on a
#    quest whose letter is still unread sends the letter's own "button" event, as a click on the letter always did
#    (the quests' "when button" code runs as before), later clicks the "info" event. A letter without an entry in the
#    list (makequestbutton without a title, e.g. the guild war's request) works as a plain letter.
import app
import ui
import quest
import event
import localeInfo
import systemSetting

ENABLED = True

CATEGORY_COUNT = 8
DEFAULT_CATEGORY = 5	# not named by the server's map (playerbot_quest_renewal.cpp QR_SYSTEM)

IMG = "d:/ymir work/ui/quest_re/"
TAB_IMAGE = IMG + "quest_tab_01.tga"
ARROW_CLOSED = IMG + "quest_down.tga"
ARROW_OPEN = IMG + "quest_up.tga"
NEW_DOT = IMG + "quest_new.tga"
SEPARATOR = IMG + "quest_list_line_01.tga"
CATEGORY_MARK = (
	IMG + "tabcolor_1_main.tga",
	IMG + "tabcolor_2_sub.tga",
	IMG + "tabcolor_3_levelup.tga",
	IMG + "tabcolor_4_event.tga",
	IMG + "tabcolor_5_collection.tga",
	IMG + "tabcolor_6_system.tga",
	IMG + "tabcolor_7_scroll.tga",
	IMG + "tabcolor_8_daily.tga",
)

LABELS_PL = (
	"Misje g\xb3\xf3wne",
	"Misje poboczne",
	"Misje \xb3owieckie",
	"Wydarzenia",
	"Misje Biologa",
	"Pozosta\xb3e misje",
	"Zwoje misji",
	"Misje dzienne",
)
LABELS_EN = (
	"Main Quests",
	"Side Quests",
	"Hunting Missions",
	"Event Missions",
	"Biologist Quests",
	"Other Missions",
	"Mission Book Quests",
	"Daily Quests",
)

COLOR_CATEGORY = 0xFFCEC6B5
COLOR_TITLE = 0xFFF2E7C1
COLOR_INFO = 0xFFB0A898
TITLE_COLORS = { "*" : 0xFF45678D, "&" : 0xFF83C055, "~" : 0xFFCAB62F }	# the package's "blue", "green", "golden"

HEADER_STEP = 20
HEADER_WIDTH = 210
HEADER_HEIGHT = 17
ROW_BASE_HEIGHT = 35	# title 20 + clock 15
ROW_COUNTER_HEIGHT = 15


def Label(category):
	try:
		lang = systemSetting.GetLanguage()
	except:
		lang = "pl"
	labels = LABELS_PL if lang == "pl" else LABELS_EN
	key = "QUEST_CATEGORY_%02d" % category
	return getattr(localeInfo, key, labels[category])


# --- the server's map --------------------------------------------------------------------------------------------
_categoryOf = {}


def OnServerCommand(part, data = "-"):
	"""'QuestCategory <part> <index>:<category>,...' - part 0 starts a new map"""
	global _categoryOf
	try:
		if int(part) == 0:
			_categoryOf = {}
	except ValueError:
		return
	if not data or data == "-":
		return
	for pair in data.split(","):
		try:
			(idx, cat) = pair.split(":")
			idx, cat = int(idx), int(cat)
		except ValueError:
			continue
		if 0 <= cat < CATEGORY_COUNT:
			_categoryOf[idx] = cat


def GetCategory(questIndex):
	return _categoryOf.get(questIndex, DEFAULT_CATEGORY)


# --- the letters (interfacemodule.py registers itself) -------------------------------------------------------------
_letterOwner = None
_letterOwnerRef = None


def SetLetterOwner(hasLetter, takeLetter):
	"""hasLetter(questIndex) -> bool, takeLetter(questIndex) -> bool (sent the letter's button event) - two methods of
	the interface (Interface.MakeInterface)"""
	global _letterOwner, _letterOwnerRef
	import weakref
	_letterOwner = (ui.__mem_func__(hasLetter), ui.__mem_func__(takeLetter))
	_letterOwnerRef = weakref.ref(hasLetter.im_self)


def ClearLetterOwner(owner):
	"""Interface.Close: off, unless a newer interface has taken over already"""
	global _letterOwner, _letterOwnerRef
	if _letterOwnerRef is None or _letterOwnerRef() is None or _letterOwnerRef() is owner:
		_letterOwner = None
		_letterOwnerRef = None


def HasLetter(questIndex):
	if not _letterOwner:
		return False
	try:
		return bool(_letterOwner[0](questIndex))
	except:
		return False


def TakeLetter(questIndex):
	if not _letterOwner:
		return False
	try:
		return bool(_letterOwner[1](questIndex))
	except:
		return False


def FindQuest(questIndex):
	"""True: the quest is in the client's quest list with a title (the window can show it)"""
	for i in xrange(quest.GetQuestCount()):
		if not quest.IsExist(i):
			continue
		if quest.GetQuestIndex(i) == questIndex:
			return len(quest.GetQuestData(i)[0]) > 0
	return False


def SelectQuest(questIndex):
	"""a click on a quest of the list: its unread letter's button event, else its info event"""
	if TakeLetter(questIndex):
		return
	event.QuestButtonClick(-2147483648 + questIndex)


def _Text(text, token):
	try:
		import utils
		return utils.process_string(text, token)[0]
	except:
		return text


def ClockText(lastName, lastTime):
	if len(lastName) <= 0:
		return localeInfo.QUEST_UNLIMITED_TIME
	if lastTime <= 0:
		return localeInfo.QUEST_TIMEOVER
	return lastName + ": " + localeInfo.SecondToDHMS(lastTime, True)


# --- the widgets (the package's ui.SubTitleBar / ui.ListBar) -------------------------------------------------------
class CategoryBar(ui.Button):
	def __init__(self, category):
		ui.Button.__init__(self)
		self.category = category
		self.SetUpVisual(TAB_IMAGE)
		self.SetOverVisual(TAB_IMAGE)
		self.SetDownVisual(TAB_IMAGE)
		self.SetSize(HEADER_WIDTH, HEADER_HEIGHT)

		arrow = ui.ImageBox()
		arrow.SetParent(self)
		arrow.AddFlag("not_pick")
		arrow.LoadImage(ARROW_CLOSED)
		arrow.SetPosition(5, 2)
		arrow.Show()
		self.arrow = arrow

		mark = ui.ImageBox()
		mark.SetParent(self)
		mark.AddFlag("not_pick")
		mark.LoadImage(CATEGORY_MARK[category])
		mark.SetPosition(188, 6)
		mark.Hide()
		self.mark = mark

		text = ui.TextLine()
		text.SetParent(self)
		text.SetPosition(27, HEADER_HEIGHT / 2)
		text.SetVerticalAlignCenter()
		text.SetHorizontalAlignLeft()
		text.SetPackedFontColor(COLOR_CATEGORY)
		text.Show()
		self.text = text

	def __del__(self):
		ui.Button.__del__(self)

	def SetCount(self, count):
		self.text.SetText("%s (%d)" % (Label(self.category), count))
		if count > 0:
			self.mark.Show()
		else:
			self.mark.Hide()

	def SetOpen(self, isOpen):
		self.arrow.LoadImage(ARROW_OPEN if isOpen else ARROW_CLOSED)


class QuestRow(ui.Button):
	def __init__(self, width):
		ui.Button.__init__(self)
		self.questIndex = 0
		self.SetSize(width, ROW_BASE_HEIGHT)

		dot = ui.ImageBox()
		dot.SetParent(self)
		dot.AddFlag("not_pick")
		dot.LoadImage(NEW_DOT)
		dot.SetPosition(10, 7)
		dot.Hide()
		self.dot = dot

		title = ui.TextLine()
		title.SetParent(self)
		title.SetPosition(23, 2)
		title.Show()
		self.title = title

		counter = ui.TextLine()
		counter.SetParent(self)
		counter.SetPosition(20, 18)
		counter.SetPackedFontColor(COLOR_INFO)
		counter.Hide()
		self.counter = counter

		clock = ui.TextLine()
		clock.SetParent(self)
		clock.SetPosition(20, 18)
		clock.SetPackedFontColor(COLOR_INFO)
		clock.Show()
		self.clock = clock

		line = ui.ImageBox()
		line.SetParent(self)
		line.AddFlag("not_pick")
		line.LoadImage(SEPARATOR)
		line.SetPosition(4, ROW_BASE_HEIGHT - 3)
		line.Hide()
		self.line = line

	def __del__(self):
		ui.Button.__del__(self)

	def SetQuest(self, questIndex, name, counterName, counterValue, isLast):
		self.questIndex = questIndex
		color = COLOR_TITLE
		if name and name[0] in TITLE_COLORS:
			color = TITLE_COLORS[name[0]]
			name = name[1:]
		self.title.SetText(_Text(name, "m"))
		self.title.SetPackedFontColor(color)

		hasCounter = len(counterName) > 0
		height = ROW_BASE_HEIGHT
		if hasCounter:
			self.counter.SetText("%s: %d" % (_Text(counterName, "m"), counterValue))
			self.counter.Show()
			self.clock.SetPosition(20, 18 + ROW_COUNTER_HEIGHT)
			height += ROW_COUNTER_HEIGHT
		else:
			self.counter.Hide()
			self.clock.SetPosition(20, 18)
		self.SetSize(self.GetWidth(), height)
		self.line.SetPosition(4, height - 3)
		if isLast:
			self.line.Hide()
		else:
			self.line.Show()
		self.SetUnread(HasLetter(questIndex))
		return height

	def SetUnread(self, unread):
		if unread:
			self.dot.Show()
		else:
			self.dot.Hide()

	def SetClock(self, text):
		self.clock.SetText(text)


class QuestList(object):
	"""the quest page: board = the window the rows live in (its size is the visible part), scrollBar = ui.ScrollBar"""

	def __init__(self, board, scrollBar):
		self.board = board
		self.scrollBar = scrollBar
		self.width = board.GetWidth()
		self.height = board.GetHeight()
		self.openCategory = -1
		self.totalHeight = 0
		self.categoryQuests = [[] for i in xrange(CATEGORY_COUNT)]
		self.rows = {}
		self.visibleRows = []

		self.bars = []
		for i in xrange(CATEGORY_COUNT):
			bar = CategoryBar(i)
			bar.SetParent(board)
			bar.SetEvent(ui.__mem_func__(self.__OnClickCategory), i)
			bar.SetCount(0)
			bar.Hide()
			self.bars.append(bar)

		self.scrollBar.SetScrollEvent(ui.__mem_func__(self.__OnScroll))
		self.__Wheel(board)
		for bar in self.bars:
			self.__Wheel(bar)
		self.scrollBar.Hide()

	def __Wheel(self, window):
		# the wheel over the board, a category or a quest scrolls the list
		try:
			self.scrollBar.SAFE_SetOnWheelEvent(window)
		except:
			pass

	def Destroy(self):
		for row in self.rows.itervalues():
			row.ClearEvent()
			row.Hide()
		for bar in self.bars:
			bar.ClearEvent()
			bar.Hide()
		self.rows = {}
		self.bars = []
		self.visibleRows = []
		self.board = None
		self.scrollBar = None

	# the client's quest list -> the categories
	def __Collect(self):
		lists = [[] for i in xrange(CATEGORY_COUNT)]
		for i in xrange(quest.GetQuestCount()):
			if not quest.IsExist(i):
				continue
			(name, icon, counterName, counterValue) = quest.GetQuestData(i)
			questIndex = quest.GetQuestIndex(i)
			lists[GetCategory(questIndex)].append((i, questIndex, name, counterName, counterValue))
		self.categoryQuests = lists

	def Refresh(self):
		if not self.board:
			return
		self.__Collect()
		for i in xrange(CATEGORY_COUNT):
			self.bars[i].SetCount(len(self.categoryQuests[i]))
		if self.openCategory >= 0 and not self.categoryQuests[self.openCategory]:
			self.openCategory = -1
		self.__Layout()

	def Open(self, category):
		if category < 0 or category >= CATEGORY_COUNT or not self.categoryQuests[category]:
			return
		self.openCategory = category
		self.scrollBar.SetPos(0)
		self.__Layout()

	def Focus(self, questIndex):
		"""open the category of a quest and scroll to it"""
		self.Refresh()
		category = GetCategory(questIndex)
		if not self.categoryQuests[category]:
			return
		if self.openCategory != category:
			self.openCategory = category
		self.scrollBar.SetPos(0)
		self.__Layout()
		y = (category + 1) * HEADER_STEP
		for (i, idx, name, counterName, counterValue) in self.categoryQuests[category]:
			if idx == questIndex:
				break
			y += ROW_BASE_HEIGHT + (ROW_COUNTER_HEIGHT if counterName else 0)
		overflow = self.totalHeight - self.height
		if overflow > 0:
			self.scrollBar.SetPos(min(1.0, max(0.0, float(y - HEADER_STEP) / overflow)))
			self.__Layout()

	def __OnClickCategory(self, category):
		if self.openCategory == category:
			self.openCategory = -1
			self.scrollBar.SetPos(0)
			self.__Layout()
		else:
			self.Open(category)

	def __OnScroll(self):
		self.__Layout()

	def __OnClickQuest(self, questIndex):
		SelectQuest(questIndex)
		row = self.rows.get(questIndex)
		if row:
			row.SetUnread(HasLetter(questIndex))

	def __Row(self, questIndex):
		row = self.rows.get(questIndex)
		if not row:
			row = QuestRow(HEADER_WIDTH)
			row.SetParent(self.board)
			row.SetEvent(ui.__mem_func__(self.__OnClickQuest), questIndex)
			self.__Wheel(row)
			self.rows[questIndex] = row
		return row

	def __Layout(self):
		if not self.board:
			return

		# the total height first (the scroll offset depends on it)
		total = CATEGORY_COUNT * HEADER_STEP
		if self.openCategory >= 0:
			for q in self.categoryQuests[self.openCategory]:
				total += ROW_BASE_HEIGHT + (ROW_COUNTER_HEIGHT if q[3] else 0)
		self.totalHeight = total
		overflow = total - self.height
		if overflow > 0:
			self.scrollBar.Show()
			try:
				self.scrollBar.SetMiddleBarSize(float(self.height) / total)
				self.scrollBar.SetScrollStep(min(1.0, float(HEADER_STEP * 2) / overflow))
			except:
				pass
			offset = int(overflow * self.scrollBar.GetPos())
		else:
			self.scrollBar.Hide()
			offset = 0

		used = {}
		self.visibleRows = []
		y = -offset
		for category in xrange(CATEGORY_COUNT):
			bar = self.bars[category]
			bar.SetOpen(category == self.openCategory)
			if 0 <= y and y + HEADER_HEIGHT <= self.height:
				bar.SetPosition(2, y + 1)
				bar.Show()
			else:
				bar.Hide()
			y += HEADER_STEP

			if category != self.openCategory:
				continue
			quests = self.categoryQuests[category]
			for n in xrange(len(quests)):
				(i, questIndex, name, counterName, counterValue) = quests[n]
				row = self.__Row(questIndex)
				height = row.SetQuest(questIndex, name, counterName, counterValue, n == len(quests) - 1)
				used[questIndex] = True
				if 0 <= y and y + height - 4 <= self.height:
					row.SetPosition(2, y)
					row.Show()
					self.visibleRows.append((row, i))
				else:
					row.Hide()
				y += height

		for (questIndex, row) in self.rows.items():
			if questIndex not in used:
				row.ClearEvent()
				row.Hide()
				del self.rows[questIndex]
		self.UpdateClocks()

	def UpdateClocks(self):
		for (row, i) in self.visibleRows:
			if not quest.IsExist(i):
				continue
			(lastName, lastTime) = quest.GetQuestLastTime(i)
			row.SetClock(ClockText(lastName, lastTime))
