# MT2009_PLUS_RELIC_V1 - Bonus Reliktu (the owner, 29 October 2026: "Add relics according to the wiki" - pl-wiki
# "Bonus Reliktu"). The window of the package "Official Passive Attr System" (Best Studio, github.com/ybeststudio;
# GF's passive_attr images - pack "relikty") on our client: no new packet and no exe change - the server
# (playerbot_relikty.cpp, server-patches/relikty) keeps the two relic pages in hidden cells of the character and
# talks over chat commands:
#   "/relikt hello"              after every load (game.py) -> "relikt_state ..."
#   "/relikt page <0|1>"         the page buttons (only the selected page's relic works)
#   "/relikt put <cell> <page>"  a relic dropped on the middle slot (a right click on a relic in the bag works too)
#   "/relikt take|add|charge|activate <page>"
#   "relikt_state <page> (<vnum> <left> <time> <flags> <type value> x4) x2", "relikt_open"
# The souls are taken from the bag and the extra inventory (one of each a bonus / a charge); their slots show how
# many there are. The tooltip of a relic (bag, window) is RelicTooltip (uitooltip.py AddItemData). Texts CP1250.
import app
import chat
import mouseModule
import net
import player
import snd
import item
import ui
import uiCommon
import uiToolTip
import relikt_data as D

FLAG_ACTIVE = 1
FLAG_USED = 2
SLOT_RELIC = 0
SOUL_SLOTS = (1, 2, 3, 4)		# up, down, left, right = D.SOULS
PAGE_NAME = ("I", "II")
HELP_LINES = (
	"Relikt Duszy (Chaegirab w Dongan wytwarza go z Od\xb3amka Reliktu)",
	"daje do 4 bonus\xf3w - ka\xbfdy w\xb3\xb9""cza si\xea sam w walce, z szans\xb9",
	"i czasem odnowienia. Dodaj: po jednej Duszy Miecza, Ochrony,",
	"Ozdoby i \x8cwiat\xb3""a - nowy losowy bonus (nie da si\xea ich zmieni\xe6).",
	"Do\xb3""aduj: te same dusze - pe\xb3ny czas reliktu (1-12 godz.).",
	"Czas p\xb3ynie tylko, gdy relikt jest aktywny. Dzia\xb3""a relikt",
	"wybranego okienka (I / II). Po pierwszej aktywacji wyj\xeacie",
	"reliktu go niszczy.",
)

_SOCKETS = getattr(player, "METIN_SOCKET_MAX_NUM", 3)
_ATTRS = getattr(player, "ATTRIBUTE_SLOT_MAX_NUM", 7)
_state = {'page': 0, 'pages': [None, None], 'at': 0.0, 'window': None}


# ---------------------------------------------------------------- data
def IsRelic(vnum):
	return D.RELIC_FIRST <= vnum <= D.RELIC_LAST


def Clock(sec):
	sec = max(0, int(sec))
	return "%d:%02d:%02d" % (sec / 3600, (sec / 60) % 60, sec % 60)


def Start():
	"""game.py, once the character is in the world (and after every warp)."""
	net.SendChatPacket("/relikt hello")


def OnServerState(*args):
	try:
		v = [int(x) for x in args]
	except ValueError:
		return
	if len(v) < 25:
		return
	_state['page'] = 1 if v[0] == 1 else 0
	pages = []
	for p in xrange(2):
		r = v[1 + p * 12:13 + p * 12]
		if not r[0]:
			pages.append(None)
			continue
		pages.append({'vnum': r[0], 'left': r[1], 'time': r[2], 'flags': r[3],
					  'attrs': [(r[4 + i * 2], r[5 + i * 2]) for i in xrange(4)]})
	_state['pages'] = pages
	_state['at'] = app.GetTime()
	w = _state['window']
	if w:
		w.Refresh()


def OnServerOpen(*args):
	OpenWindow()


def Left(page):
	d = _state['pages'][page]
	if not d:
		return 0
	left = d['left']
	if page == _state['page'] and (d['flags'] & FLAG_ACTIVE):
		left -= int(app.GetTime() - _state['at'])
	return max(0, left)


def MetinSlot(page):
	d = _state['pages'][page]
	if not d:
		return [0] * _SOCKETS
	s = [Left(page), d['time'], d['flags']]
	return s + [0] * max(0, _SOCKETS - len(s))


def AttrSlot(page):
	d = _state['pages'][page]
	a = list(d['attrs']) if d else []
	return a + [(0, 0)] * max(0, _ATTRS - len(a))


def SoulCount(vnum):
	n = player.GetItemCountByVnum(vnum)
	try:
		n += __import__("uiekwipunek").CountInStorages(vnum)
	except Exception:
		pass
	return n


def HasSouls():
	for v in D.SOULS:
		if SoulCount(v) < 1:
			return False
	return True


# ---------------------------------------------------------------- the tooltip (uitooltip.py AddItemData)
def RelicTooltip(tt, vnum, metinSlot, attrSlot):
	item.SelectItem(vnum)
	tt.SetTitle(item.GetItemName())
	tt.AppendDescription(item.GetItemDescription(), 26)
	left = total = flags = 0
	if metinSlot and metinSlot != 0:
		try:
			left, total, flags = int(metinSlot[0]), int(metinSlot[1]), int(metinSlot[2])
		except (IndexError, TypeError, ValueError):
			pass
	tt.AppendSpace(5)
	if total > 0:
		tt.AppendTextLine("Czas reliktu: %s / %s" % (Clock(left), Clock(total)), tt.CONDITION_COLOR)
	else:
		tt.AppendTextLine("Czas reliktu: 1-12 godz. (po umieszczeniu w oknie)", tt.CONDITION_COLOR)
	if flags & FLAG_ACTIVE:
		tt.AppendTextLine("Aktywny", tt.POSITIVE_COLOR)
	elif flags & FLAG_USED:
		tt.AppendTextLine("By\xb3 aktywowany - wyj\xeacie z okna go zniszczy", tt.NEGATIVE_COLOR)
	lines = []
	if attrSlot and attrSlot != 0:
		for a in attrSlot[:D.MAX_BONUS]:
			try:
				t, val = int(a[0]), int(a[1])
			except (IndexError, TypeError, ValueError):
				continue
			if t in D.BONUS:
				lines.append((t, val))
	tt.AppendSpace(5)
	tt.AppendTextLine("Bonusy reliktu: %d / %d" % (len(lines), D.MAX_BONUS), tt.TITLE_COLOR)
	for t, val in lines:
		name, text, trigger, cooldown, values = D.BONUS[t]
		if "%d" in text:
			text = text % val
		text = text.replace("%%", "%")
		tt.AppendDescription(text, 32, tt.SPECIAL_POSITIVE_COLOR)
		if cooldown > 0:
			tt.AppendDescription("%s (co %d sek.)" % (trigger, cooldown), 36, tt.NORMAL_COLOR)
		else:
			tt.AppendDescription(trigger, 36, tt.NORMAL_COLOR)


# ---------------------------------------------------------------- the window
class ReliktWindow(ui.ScriptWindow):

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.isLoaded = False
		self.question = None
		self.toolTip = None
		self.helpToolTip = None
		self.nextRefresh = 0.0
		self.__Load()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __Load(self):
		if self.isLoaded:
			return
		self.isLoaded = True
		try:
			ui.PythonScriptLoader().LoadScriptFile(self, "uiscript/reliktwindow.py")
			self.board = self.GetChild("board")
			self.soulSlot = self.GetChild("soul_slot")
			self.relicSlot = self.GetChild("relic_slot")
			self.pageButtons = (self.GetChild("page_button_1"), self.GetChild("page_button_2"))
			self.pageText = self.GetChild("page_text")
			self.timeText = self.GetChild("time_text")
			self.chargeButton = self.GetChild("ChargeButton")
			self.addButton = self.GetChild("AddButton")
			self.activateButton = self.GetChild("ActivateButton")
			self.takeButton = self.GetChild("TakeButton")
			helpButton = self.GetChild("HelpButton")
		except Exception:
			import exception
			exception.Abort("ReliktWindow.__Load")
			return
		self.board.SetCloseEvent(ui.__mem_func__(self.Close))
		self.toolTip = uiToolTip.ItemToolTip()
		self.toolTip.HideToolTip()
		self.helpToolTip = uiToolTip.ToolTip()
		self.helpToolTip.HideToolTip()

		self.soulSlot.SetSelectEmptySlotEvent(ui.__mem_func__(self.__OnSoulSlot))
		self.soulSlot.SetSelectItemSlotEvent(ui.__mem_func__(self.__OnSoulSlot))
		self.soulSlot.SetOverInItemEvent(ui.__mem_func__(self.__OverInSoul))
		self.soulSlot.SetOverOutItemEvent(ui.__mem_func__(self.__OverOut))
		self.relicSlot.SetSelectEmptySlotEvent(ui.__mem_func__(self.__OnRelicSlot))
		self.relicSlot.SetSelectItemSlotEvent(ui.__mem_func__(self.__OnRelicSlot))
		self.relicSlot.SetUnselectItemSlotEvent(ui.__mem_func__(self.__OnRelicRightClick))
		self.relicSlot.SetUseSlotEvent(ui.__mem_func__(self.__OnRelicRightClick))
		self.relicSlot.SetOverInItemEvent(ui.__mem_func__(self.__OverInRelic))
		self.relicSlot.SetOverOutItemEvent(ui.__mem_func__(self.__OverOut))
		for i in xrange(2):
			self.pageButtons[i].SetEvent(ui.__mem_func__(self.__OnPage), i)
		self.chargeButton.SetEvent(ui.__mem_func__(self.__OnCharge))
		self.addButton.SetEvent(ui.__mem_func__(self.__OnAdd))
		self.activateButton.SetEvent(ui.__mem_func__(self.__OnActivate))
		self.takeButton.SetEvent(ui.__mem_func__(self.__OnTake))
		helpButton.SetShowToolTipEvent(ui.__mem_func__(self.__OverInHelp))
		helpButton.SetHideToolTipEvent(ui.__mem_func__(self.__OverOut))

	def Destroy(self):
		self.__CloseQuestion()
		self.Hide()
		if self.toolTip:
			self.toolTip.HideToolTip()
		if self.helpToolTip:
			self.helpToolTip.HideToolTip()
		self.toolTip = None
		self.helpToolTip = None
		self.ClearDictionary()

	def Open(self):
		self.Refresh()
		self.Show()
		self.SetTop()
		net.SendChatPacket("/relikt hello")

	def Close(self):
		self.__CloseQuestion()
		self.__OverOut()
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	# -- the view
	def Refresh(self):
		page = _state['page']
		d = _state['pages'][page]
		for i in xrange(2):
			if i == page:
				self.pageButtons[i].Down()
			else:
				self.pageButtons[i].SetUp()
		if d:
			self.relicSlot.SetItemSlot(SLOT_RELIC, d['vnum'], 0)
		else:
			self.relicSlot.ClearSlot(SLOT_RELIC)
		self.relicSlot.RefreshSlot()
		for i, v in enumerate(D.SOULS):
			n = SoulCount(v)
			if n > 0:
				self.soulSlot.SetItemSlot(SOUL_SLOTS[i], v, n if n > 1 else 0)
			else:
				self.soulSlot.SetItemSlot(SOUL_SLOTS[i], v, 0, (0.4, 0.4, 0.4, 0.6))
		self.soulSlot.RefreshSlot()
		self.__RefreshTexts()

	def __RefreshTexts(self):
		page = _state['page']
		d = _state['pages'][page]
		if not d:
			self.pageText.SetText("Okienko %s - pusty (umie\x9c\xe6 tu Relikt Duszy)" % PAGE_NAME[page])
			self.timeText.SetText("")
			self.activateButton.SetText("Aktywuj")
			return
		active = (d['flags'] & FLAG_ACTIVE) != 0
		bonuses = len([a for a in d['attrs'] if a[0]])
		self.pageText.SetText("Okienko %s - %s, bonusy %d / %d" % (PAGE_NAME[page], "aktywny" if active else "nieaktywny",
																	  bonuses, D.MAX_BONUS))
		if d['time'] > 0:
			self.timeText.SetText("Czas: %s / %s" % (Clock(Left(page)), Clock(d['time'])))
		else:
			self.timeText.SetText("Czas: 1-12 godz.")
		self.activateButton.SetText("Dezaktywuj" if active else "Aktywuj")

	def OnUpdate(self):
		now = app.GetTime()
		if now < self.nextRefresh:
			return
		self.nextRefresh = now + 0.5
		self.Refresh()

	# -- the slots
	def __OnSoulSlot(self, slot):
		if mouseModule.mouseController.isAttached():
			mouseModule.mouseController.DeattachObject()
		chat.AppendChat(chat.CHAT_TYPE_INFO, "Dusze s\xb9 brane z ekwipunku same - wystarczy je mie\xe6 przy sobie.")

	def __OnRelicSlot(self, slot):
		if not mouseModule.mouseController.isAttached():
			return
		slotType = mouseModule.mouseController.GetAttachedType()
		cell = mouseModule.mouseController.GetAttachedSlotNumber()
		vnum = mouseModule.mouseController.GetAttachedItemIndex()
		mouseModule.mouseController.DeattachObject()
		if slotType != player.SLOT_TYPE_INVENTORY or not IsRelic(vnum):
			chat.AppendChat(chat.CHAT_TYPE_INFO, "Tu mo\xbfna umie\x9ci\xe6 tylko Relikt Duszy z ekwipunku.")
			return
		if _state['pages'][_state['page']]:
			chat.AppendChat(chat.CHAT_TYPE_INFO, "To okienko reliktu jest ju\xbf zaj\xeate.")
			return
		snd.PlaySound("sound/ui/drop.wav")
		net.SendChatPacket("/relikt put %d %d" % (cell, _state['page']))

	def __OnRelicRightClick(self, slot):
		self.__OnTake()

	def __OverInRelic(self, slot):
		page = _state['page']
		d = _state['pages'][page]
		if not d or mouseModule.mouseController.isAttached():
			return
		self.toolTip.ClearToolTip()
		self.toolTip.AddItemData(d['vnum'], MetinSlot(page), AttrSlot(page))
		self.toolTip.ShowToolTip()

	def __OverInSoul(self, slot):
		if mouseModule.mouseController.isAttached() or slot not in SOUL_SLOTS:
			return
		self.toolTip.ClearToolTip()
		self.toolTip.SetItemToolTip(D.SOULS[SOUL_SLOTS.index(slot)])
		self.toolTip.ShowToolTip()

	def __OverInHelp(self):
		tt = self.helpToolTip
		tt.ClearToolTip()
		tt.AutoAppendTextLine("Bonus Reliktu", tt.TITLE_COLOR)
		for line in HELP_LINES:
			tt.AutoAppendTextLine(line)
		tt.AlignHorizonalCenter()
		tt.ShowToolTip()

	def __OverOut(self):
		if self.toolTip:
			self.toolTip.HideToolTip()
		if self.helpToolTip:
			self.helpToolTip.HideToolTip()

	# -- the buttons
	def __OnPage(self, page):
		if page != _state['page']:
			net.SendChatPacket("/relikt page %d" % page)
		self.Refresh()

	def __Relic(self):
		d = _state['pages'][_state['page']]
		if not d:
			chat.AppendChat(chat.CHAT_TYPE_INFO, "Najpierw umie\x9c\xe6 Relikt Duszy w okienku (prawy klik na relikt).")
		return d

	def __OnAdd(self):
		d = self.__Relic()
		if not d:
			return
		if d['flags'] & FLAG_ACTIVE:
			chat.AppendChat(chat.CHAT_TYPE_INFO, "Nie mo\xbfna doda\xe6 bonusu do aktywnego reliktu.")
			return
		if len([a for a in d['attrs'] if a[0]]) >= D.MAX_BONUS:
			chat.AppendChat(chat.CHAT_TYPE_INFO, "Relikt Duszy ma ju\xbf 4 bonusy.")
			return
		if not HasSouls():
			chat.AppendChat(chat.CHAT_TYPE_INFO, "Potrzebujesz po jednej Duszy Miecza, Ochrony, Ozdoby i \x8cwiat\xb3""a.")
			return
		self.__Ask("Doda\xe6 nowy losowy bonus? Zu\xbfyje po jednej duszy ka\xbfdego rodzaju.",
				   "/relikt add %d" % _state['page'])

	def __OnCharge(self):
		d = self.__Relic()
		if not d:
			return
		if d['time'] > 0 and Left(_state['page']) >= d['time']:
			chat.AppendChat(chat.CHAT_TYPE_INFO, "Relikt Duszy jest w pe\xb3ni na\xb3""adowany.")
			return
		if not HasSouls():
			chat.AppendChat(chat.CHAT_TYPE_INFO, "Potrzebujesz po jednej Duszy Miecza, Ochrony, Ozdoby i \x8cwiat\xb3""a.")
			return
		self.__Ask("Do\xb3""adowa\xe6 relikt? Zu\xbfyje po jednej duszy ka\xbfdego rodzaju.", "/relikt charge %d" % _state['page'])

	def __OnActivate(self):
		d = self.__Relic()
		if not d:
			return
		if not (d['flags'] & (FLAG_ACTIVE | FLAG_USED)):
			self.__Ask("Po pierwszej aktywacji reliktu nie mo\xbfna ju\xbf wyj\xb9\xe6 bez zniszczenia. Aktywowa\xe6?",
					   "/relikt activate %d" % _state['page'])
			return
		net.SendChatPacket("/relikt activate %d" % _state['page'])

	def __OnTake(self):
		d = self.__Relic()
		if not d:
			return
		if d['flags'] & FLAG_ACTIVE:
			chat.AppendChat(chat.CHAT_TYPE_INFO, "Najpierw dezaktywuj Relikt Duszy.")
			return
		if d['flags'] & FLAG_USED:
			self.__Ask("Ten relikt by\xb3 ju\xbf aktywowany - wyj\xeacie go ZNISZCZY. Kontynuowa\xe6?",
					   "/relikt take %d" % _state['page'])
			return
		net.SendChatPacket("/relikt take %d" % _state['page'])

	def __Ask(self, text, command):
		self.__CloseQuestion()
		q = uiCommon.QuestionDialog()
		q.SetText(text)
		q.SetAcceptEvent(lambda c=command: self.__Accept(c))
		q.SetCancelEvent(ui.__mem_func__(self.__CloseQuestion))
		q.Open()
		self.question = q

	def __Accept(self, command):
		self.__CloseQuestion()
		net.SendChatPacket(command)

	def __CloseQuestion(self):
		if self.question:
			self.question.Close()
			self.question = None


def GetWindow():
	if not _state['window']:
		_state['window'] = ReliktWindow()
	return _state['window']


def OpenWindow():
	w = GetWindow()
	if not w.IsShow():
		w.Open()
	else:
		w.SetTop()


def ToggleWindow():
	w = GetWindow()
	if w.IsShow():
		w.Close()
	else:
		w.Open()


def DestroyWindow():
	w = _state['window']
	_state['window'] = None
	if w:
		w.Destroy()
