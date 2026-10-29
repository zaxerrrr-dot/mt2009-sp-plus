# MT2009_PLUS_AUTOHUNT_TEST_V1 - the TEST auto hunt (Alt+H, keybind.py "autohunt_test"), next to our own Auto Lowy
# (uiautohunt.py, K / Shift+K), which stay as they are. The owner, 28 October 2026: "I'm uploading an auto-hunt too -
# add it as a TEST auto-hunt, e.g. under Alt+H, so I can test it."
#
# The uploaded "Oto Av" package is the other way round from ours: the exe hunts by itself (client-patches/exe,
# ENABLE_MT2009_AUTOHUNT_TEST, UserInterface/Mt2009AutoHuntTest.cpp) - it picks the nearest monster the client sees
# (rank and level filter, a free line, nobody else's), lets the client's own auto attack walk there and swing, casts the
# skills of the 12 slots on their clocks and drinks the potions of the 12 slots under their %. This window only gives
# it the settings (player.AutoHuntTest*), keeps them per character (autohunt/test/<name>.cfg) and stands the character
# up after a death ("Wstawanie po smierci", /restart_here like Auto Lowy). It picks nothing up - Z / ~ as always.
#
# Our Auto Lowy ask the server for every target (/autohunt_target); this one asks the server only whether it may run:
# "/autohunt_test b" -> "AutoHuntTest on" (the hunt starts) or "AutoHuntTest off [reason]" (server-patches/autohunttest:
# the event flag autohunt_test_off switches it off for everybody). A server without that patch never answers - the
# window then says so after 5 s and nothing starts. While it runs the question goes again every minute; "/autohunt_test d"
# says it stopped.
#
# Never both at once: Start here stops Auto Lowy (uiautohunt.QuickToggle), uiautohunt's Start calls StopIfRunning.
# An exe without the hunt (no player.AutoHuntTestStart) gets a chat line instead of a window.
#
# Python 2.7 as the client has it; the texts are CP1250 escapes.

import app
import chat
import guild
import mouseModule
import net
import os
import player
import skill
import ui
import uiToolTip
import wndMgr

SKILL_SLOTS = 12
ITEM_SLOTS = 12
ITEM_SLOT_BASE = 13			# the slot window's indexes of the items (12 is the package's gap)
RANGE_MIN = 2000
RANGE_MAX = 8000
RANGE_DEFAULT = 4000
LEVEL_MIN = 1
LEVEL_MAX = 255
ANSWER_WAIT = 5.0			# seconds for the server's "AutoHuntTest on/off"
HEARTBEAT = 60.0			# the question again while it runs
REVIVE_AFTER = 10.0			# Auto Lowy's REVIVE_MIN_SECONDS
REVIVE_RETRY = 5.0
REFRESH = 0.5				# the open window's slots
CONFIG_DIR = os.path.join('autohunt', 'test')

RANK_LABELS = (
	'Zwyk\xb3e potwory',
	'Silne potwory',
	'Elitarne',
	'Silne elitarne',
	'Bossy',
	'Kr\xf3lowie',
)
STONE_LABEL = 'Kamienie'

TOOLTIP_LINES = (
	'Umiej\xeatno\x9cci: przeci\xb9gnij je z okna postaci do p\xf3l.',
	'Pod umiej\xeatno\x9cci\xb9 wpisz, co ile sekund ma jej u\xbfy\xe6.',
	'Mikstury: przeci\xb9gnij je i inne przedmioty z ekwipunku.',
	'Pod mikstur\xb9 HP / PE wpisz %, poni\xbfej kt\xf3rego j\xb9 pije,',
	'pod innym przedmiotem - co ile sekund go u\xbfywa.',
	'Prawy klik na polu je opr\xf3\xbfnia.',
	'Zasi\xeag od startu: poluje tylko wok\xf3\xb3 miejsca startu.',
	'Nie podnosi przedmiot\xf3w (Z / ~ jak zawsze).',
	'Wersja TESTOWA: zwyk\xb3e Auto \xa3owy (K) staj\xb9, gdy ta rusza.',
)

PREFIX = 'Auto \xa3owy (TEST): '


def Chat(text):
	chat.AppendChat(chat.CHAT_TYPE_INFO, PREFIX + text)


_LOAD_FAILED = {}


def LoadFailed(what):
	"""MT2009_PLUS_AUTOHUNT_TEST_UI_SAFE_V1: a window whose pictures the player's packs lack (3.0.4 shipped none)
	raised on every Alt+H. Now: the error once to syserr, a chat line on each try, the window stays closed."""
	if not _LOAD_FAILED.get(what):
		_LOAD_FAILED[what] = True
		try:
			import dbg
			import sys
			import traceback
			dbg.TraceError('uiautohunt_test %s: %s' % (what, ''.join(traceback.format_exception(*sys.exc_info())).strip()))
		except Exception:
			pass
	Chat('nie uda\xb3o si\xea wczyta\xe6 okna (brak plik\xf3w klienta) - zaktualizuj klienta.')


def HasExe():
	return hasattr(player, 'AutoHuntTestStart')


def Now():
	try:
		import clientclock
		return clientclock.Now()
	except Exception:
		return app.GetTime()


def InGame():
	try:
		import warpsafe
		return warpsafe.InGame()
	except ImportError:
		return True


def Send(command):
	if InGame():
		net.SendChatPacket(command)


def ToInt(text, default=0):
	try:
		return int(text)
	except (TypeError, ValueError):
		return default


def DefaultConfig():
	return {
		'attack': 1, 'skills': 0, 'items': 0, 'anchor': 0, 'restart': 0,
		'range': RANGE_DEFAULT, 'ranks': 0x3f, 'stones': 0, 'min_level': LEVEL_MIN, 'max_level': LEVEL_MAX,
		'skill_slots': [(0, 0)] * SKILL_SLOTS,		# (skill slot, seconds)
		'item_slots': [(-1, 0)] * ITEM_SLOTS,		# (inventory cell, % or seconds)
	}


def ConfigPath():
	name = player.GetMainCharacterName()
	name = ''.join(c for c in str(name) if c.isalnum() or c in '_-')
	if not name:
		return None
	return os.path.join(CONFIG_DIR, name + '.cfg')


def LoadConfig():
	config = DefaultConfig()
	path = ConfigPath()
	if not path or not os.path.exists(path):
		return config
	try:
		lines = open(path, 'r').read().splitlines()
	except (IOError, OSError):
		return config
	skills = list(config['skill_slots'])
	items = list(config['item_slots'])
	for line in lines:
		if '=' not in line:
			continue
		key, value = line.split('=', 1)
		key = key.strip()
		value = value.strip()
		if key.startswith('skill') and key[5:].isdigit():
			i = int(key[5:])
			parts = value.split(',')
			if 0 <= i < SKILL_SLOTS and len(parts) == 2:
				skills[i] = (ToInt(parts[0]), ToInt(parts[1]))
		elif key.startswith('item') and key[4:].isdigit():
			i = int(key[4:])
			parts = value.split(',')
			if 0 <= i < ITEM_SLOTS and len(parts) == 2:
				items[i] = (ToInt(parts[0], -1), ToInt(parts[1]))
		elif key in config and not isinstance(config[key], list):
			config[key] = ToInt(value, config[key])
	config['skill_slots'] = skills
	config['item_slots'] = items
	config['range'] = max(RANGE_MIN, min(RANGE_MAX, config['range']))
	return config


def SaveConfig(config):
	path = ConfigPath()
	if not path:
		return False
	try:
		if not os.path.isdir(CONFIG_DIR):
			os.makedirs(CONFIG_DIR)
		lines = []
		for key in ('attack', 'skills', 'items', 'anchor', 'restart', 'range', 'ranks', 'stones', 'min_level', 'max_level'):
			lines.append('%s=%d' % (key, int(config[key])))
		for i, (pos, value) in enumerate(config['skill_slots']):
			lines.append('skill%d=%d,%d' % (i, pos, value))
		for i, (pos, value) in enumerate(config['item_slots']):
			lines.append('item%d=%d,%d' % (i, pos, value))
		f = open(path, 'w')
		f.write('\n'.join(lines) + '\n')
		f.close()
		return True
	except (IOError, OSError):
		return False


class Hunt(object):
	"""The hunt's state outside the window: the server's answer, the heartbeat, standing up after a death."""

	def __init__(self):
		self.config = None
		self.configPath = None
		self.running = False
		self.waitingSince = 0.0
		self.nextHeartbeat = 0.0
		self.deadSince = 0.0
		self.nextRevive = 0.0

	def Config(self):
		path = ConfigPath()
		if self.config is None or path != self.configPath:
			self.config = LoadConfig()
			self.configPath = path
		return self.config

	def PushSettings(self):
		"""The settings to the exe; the slots come back with the exe's values (a skill never under its cooldown)."""
		if not HasExe():
			return
		c = self.Config()
		player.AutoHuntTestSetOptions(c['attack'], c['skills'], c['items'], c['anchor'])
		player.AutoHuntTestSetFilter(c['ranks'], c['stones'], c['min_level'], c['max_level'])
		player.AutoHuntTestSetRange(float(c['range']))
		for i in xrange(SKILL_SLOTS):
			pos, value = c['skill_slots'][i]
			if pos > 0 and player.AutoHuntTestSetSkillSlot(i, pos):
				if value > 0:
					player.AutoHuntTestSetSlotValue(i, value)
			else:
				player.AutoHuntTestSetSkillSlot(i, 0)
		for i in xrange(ITEM_SLOTS):
			pos, value = c['item_slots'][i]
			if pos >= 0 and player.AutoHuntTestSetItemSlot(i, pos):
				if value > 0:
					player.AutoHuntTestSetSlotValue(SKILL_SLOTS + i, value)
			else:
				player.AutoHuntTestSetItemSlot(i, -1)
		self.ReadSlotsBack()

	def ReadSlotsBack(self):
		c = self.Config()
		c['skill_slots'] = [self.SlotOf(i, 0) for i in xrange(SKILL_SLOTS)]
		c['item_slots'] = [self.SlotOf(SKILL_SLOTS + i, -1) for i in xrange(ITEM_SLOTS)]

	def SlotOf(self, index, empty):
		(pos, value) = player.AutoHuntTestGetSlot(index)
		if pos < 0:
			return (empty, 0)
		return (pos, value)

	def IsBusy(self):
		return self.running or self.waitingSince > 0.0

	def RequestStart(self):
		if self.IsBusy():
			return
		if not HasExe():
			Chat('ten test wymaga nowego klienta (exe).')
			return
		if not InGame():
			return
		# never together with our Auto Lowy
		try:
			import uiautohunt
			if uiautohunt.IsRunning():
				uiautohunt.QuickToggle()
				Chat('zwyk\xb3e Auto \xa3owy zatrzymane.')
		except Exception:
			pass
		self.PushSettings()
		self.waitingSince = Now()
		Send('/autohunt_test b')
		RefreshWindow()

	def Begin(self):
		self.waitingSince = 0.0
		if self.running:
			return
		try:
			import uiautohunt
			if uiautohunt.IsRunning():
				uiautohunt.QuickToggle()
		except Exception:
			pass
		self.PushSettings()
		if not player.AutoHuntTestStart(1):
			Chat('nie mo\xbfna wystartowa\xe6.')
			RefreshWindow()
			return
		self.running = True
		self.deadSince = 0.0
		self.nextHeartbeat = Now() + HEARTBEAT
		c = self.Config()
		Chat('start, zasi\xeag %d m.' % (c['range'] // 100))
		RefreshWindow()

	def Stop(self, quiet=False, send=True):
		wasBusy = self.IsBusy()
		self.waitingSince = 0.0
		if HasExe():
			player.AutoHuntTestStart(0)
		if not self.running:
			if wasBusy:
				RefreshWindow()
			return
		self.running = False
		if send:
			Send('/autohunt_test d')
		if not quiet:
			Chat('stop.')
		RefreshWindow()

	def OnServer(self, answer='', *rest):
		if answer == 'on':
			if self.waitingSince > 0.0:
				self.Begin()
		elif answer == 'off':
			reason = ' '.join(rest)
			wasBusy = self.IsBusy()
			self.Stop(quiet=True, send=False)
			if wasBusy:
				if reason == 'flag':
					Chat('wy\xb3\xb9czone na tym serwerze.')
				elif reason == 'item':
					Chat('potrzebny bilet Auto \xa3ow\xf3w (jak dla zwyk\xb3ych Auto \xa3ow\xf3w).')
				else:
					Chat('serwer nie pozwala teraz polowa\xe6.')

	def OnUpdate(self):
		now = Now()
		if self.waitingSince > 0.0 and now - self.waitingSince > ANSWER_WAIT:
			self.waitingSince = 0.0
			Chat('serwer nie odpowiada (brak poprawki autohunttest) - nie wystartowano.')
			RefreshWindow()
		if not self.running:
			return
		if not HasExe() or not player.AutoHuntTestIsRunning():
			# the exe stopped it (no character - a warp, a logout)
			self.running = False
			RefreshWindow()
			return
		if now >= self.nextHeartbeat:
			self.nextHeartbeat = now + HEARTBEAT
			Send('/autohunt_test b')
		if player.GetStatus(player.HP) <= 0:
			if not self.deadSince:
				self.deadSince = now
				self.nextRevive = now + REVIVE_AFTER
			if self.Config()['restart'] and now >= self.nextRevive and InGame():
				self.nextRevive = now + REVIVE_RETRY
				net.SendChatPacket('/restart_here')
		else:
			self.deadSince = 0.0

	def Destroy(self):
		# the game window closes: nothing goes out any more
		self.Stop(quiet=True, send=False)
		if HasExe():
			player.AutoHuntTestShowRange(0.0)


class CheckBox(ui.Window):
	"""The package's AutoHuntCheckBox: GF's check images and a label."""

	def __init__(self, text, checked):
		ui.Window.__init__(self)
		self.checked = bool(checked)
		self.back = ui.ImageBox()
		self.back.SetParent(self)
		self.back.AddFlag('not_pick')
		self.back.LoadImage('d:/ymir work/ui/game/auto_hunting/auto_attack_check_back_img.sub')
		self.back.SetPosition(0, 0)
		self.back.Show()
		self.mark = ui.ImageBox()
		self.mark.SetParent(self)
		self.mark.AddFlag('not_pick')
		self.mark.LoadImage('d:/ymir work/ui/game/auto_hunting/auto_attack_check_box.sub')
		self.mark.SetPosition(2, 1)
		self.text = ui.TextLine()
		self.text.SetParent(self)
		self.text.SetPosition(20, 0)
		self.text.SetText(text)
		self.text.Show()
		self.SetSize(self.back.GetWidth() + 20 + self.text.GetTextSize()[0], max(16, self.back.GetHeight()))
		self.SetStatus(self.checked)

	def __del__(self):
		ui.Window.__del__(self)

	def OnMouseLeftButtonUp(self):
		self.SetStatus(not self.checked)
		return True

	def SetStatus(self, checked):
		self.checked = bool(checked)
		if self.checked:
			self.mark.Show()
		else:
			self.mark.Hide()

	def GetStatus(self):
		return self.checked


class OptionWindow(ui.ScriptWindow):
	"""What to attack: the six ranks, the stones, the level range."""

	def __init__(self, owner):
		ui.ScriptWindow.__init__(self)
		self.owner = owner
		self.boxes = []
		ui.PythonScriptLoader().LoadScriptFile(self, 'UIScript/autohunttestoptionwindow.py')
		board = self.GetChild('board')
		self.editMin = self.GetChild('auto_attack_level_min')
		self.editMax = self.GetChild('auto_attack_level_max')
		self.GetChild('ClearButton').SetEvent(ui.__mem_func__(self.OnDefaults))
		self.GetChild('AcceptButton').SetEvent(ui.__mem_func__(self.OnAccept))
		for i, label in enumerate(RANK_LABELS + (STONE_LABEL,)):
			box = CheckBox(label, False)
			box.SetParent(board)
			box.SetPosition(17, 17 + 16 * i)
			box.Show()
			self.boxes.append(box)
		self.editMin.SetEscapeEvent(ui.__mem_func__(self.Close))
		self.editMax.SetEscapeEvent(ui.__mem_func__(self.Close))

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def Load(self, config):
		for i in xrange(len(RANK_LABELS)):
			self.boxes[i].SetStatus(config['ranks'] & (1 << i))
		self.boxes[len(RANK_LABELS)].SetStatus(config['stones'])
		self.editMin.SetText(str(config['min_level']))
		self.editMax.SetText(str(config['max_level']))

	def OnDefaults(self):
		self.Load(DefaultConfig())

	def OnAccept(self):
		config = GetHunt().Config()
		ranks = 0
		for i in xrange(len(RANK_LABELS)):
			if self.boxes[i].GetStatus():
				ranks |= 1 << i
		config['ranks'] = ranks
		config['stones'] = 1 if self.boxes[len(RANK_LABELS)].GetStatus() else 0
		low = max(LEVEL_MIN, min(LEVEL_MAX, ToInt(self.editMin.GetText(), LEVEL_MIN)))
		high = max(LEVEL_MIN, min(LEVEL_MAX, ToInt(self.editMax.GetText(), LEVEL_MAX)))
		config['min_level'], config['max_level'] = min(low, high), max(low, high)
		if HasExe():
			player.AutoHuntTestSetFilter(config['ranks'], config['stones'], config['min_level'], config['max_level'])
		self.Close()

	def Close(self):
		self.editMin.KillFocus()
		self.editMax.KillFocus()
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True


class RangeWindow(ui.ScriptWindow):
	"""The range slider; the circle is on the ground while the window is open."""

	def __init__(self, owner):
		ui.ScriptWindow.__init__(self)
		self.owner = owner
		self.range = RANGE_DEFAULT
		ui.PythonScriptLoader().LoadScriptFile(self, 'UIScript/autohunttestrangewindow.py')
		self.slider = self.GetChild('hunting_range_sliderbar')
		self.text = self.GetChild('range_text')
		self.slider.SetEvent(ui.__mem_func__(self.OnSlide))
		self.GetChild('AcceptButton').SetEvent(ui.__mem_func__(self.OnAccept))

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def Open(self, value):
		self.range = max(RANGE_MIN, min(RANGE_MAX, value))
		self.slider.SetSliderPos(float(self.range - RANGE_MIN) / float(RANGE_MAX - RANGE_MIN))
		self.UpdateText()
		self.Show()
		self.SetTop()
		self.ShowCircle()

	def ShowCircle(self):
		if HasExe():
			player.AutoHuntTestShowRange(float(self.range))

	def UpdateText(self):
		self.text.SetText('%d m' % (self.range // 100))

	def OnSlide(self):
		ratio = max(0.0, min(1.0, self.slider.GetSliderPos()))
		self.range = int(RANGE_MIN + (RANGE_MAX - RANGE_MIN) * ratio)
		self.UpdateText()
		self.ShowCircle()

	def OnAccept(self):
		config = GetHunt().Config()
		config['range'] = self.range
		if HasExe():
			player.AutoHuntTestSetRange(float(self.range))
		self.Close()

	def Close(self):
		if HasExe():
			player.AutoHuntTestShowRange(0.0)
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True


class AutoHuntTestWindow(ui.ScriptWindow):
	TOGGLES = (
		('AutoAttackButton', 'attack'),
		('AutoRangeButton', 'anchor'),
		('AutoPotionButton', 'items'),
		('AutoSkillButton', 'skills'),
		('AutoRestartHereButton', 'restart'),
	)

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.toggles = {}
		self.edits = []
		self.optionWindow = None
		self.rangeWindow = None
		self.nextRefresh = 0.0
		self.tooltipSkill = uiToolTip.SkillToolTip()
		self.tooltipSkill.HideToolTip()
		self.tooltipItem = uiToolTip.ItemToolTip()
		self.tooltipItem.HideToolTip()
		self.helpToolTip = None
		self.__Load()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __Load(self):
		ui.PythonScriptLoader().LoadScriptFile(self, 'UIScript/autohunttestwindow.py')
		self.GetChild('board').SetCloseEvent(ui.__mem_func__(self.Close))
		self.GetChild('AutoSaveOnButton').SetEvent(ui.__mem_func__(self.OnSave))
		self.startButton = self.GetChild('AutoStartOnButton')
		self.stopButton = self.GetChild('AutoStartOffButton')
		self.startButton.SetEvent(ui.__mem_func__(self.OnStart))
		self.stopButton.SetEvent(ui.__mem_func__(self.OnStop))
		for name, key in self.TOGGLES:
			button = self.GetChild(name)
			button.SetToggleDownEvent(ui.__mem_func__(self.OnToggle), key, 1)
			button.SetToggleUpEvent(ui.__mem_func__(self.OnToggle), key, 0)
			self.toggles[key] = button
		self.GetChild('AutoSkillClearButton').SetEvent(ui.__mem_func__(self.OnClear), 1)
		self.GetChild('AutoPotionClearButton').SetEvent(ui.__mem_func__(self.OnClear), 2)
		self.GetChild('AutoAllClearButton').SetEvent(ui.__mem_func__(self.OnClear), 0)
		self.GetChild('AutoAttackOptionButton').SetEvent(ui.__mem_func__(self.OnOpenOptions))
		self.GetChild('AutoRangeSelectButton').SetEvent(ui.__mem_func__(self.OnOpenRange))
		for i in xrange(SKILL_SLOTS + ITEM_SLOTS):
			edit = self.GetChild('editline%d' % i)
			edit.SetEscapeEvent(ui.__mem_func__(self.Close))
			self.edits.append(edit)
		self.slots = self.GetChild('Auto_Active_Skill_Slot_Table')
		self.slots.SetSlotStyle(wndMgr.SLOT_STYLE_NONE)
		self.slots.SetSelectEmptySlotEvent(ui.__mem_func__(self.OnSelectEmpty))
		self.slots.SetSelectItemSlotEvent(ui.__mem_func__(self.OnSelectEmpty))
		self.slots.SetUnselectItemSlotEvent(ui.__mem_func__(self.OnClearSlot))
		self.slots.SetOverInItemEvent(ui.__mem_func__(self.OnOverIn))
		self.slots.SetOverOutItemEvent(ui.__mem_func__(self.OnOverOut))
		self.helpToolTip = uiToolTip.ToolTip()
		self.helpToolTip.SetTitle('Auto \xa3owy (TEST)')
		self.helpToolTip.AppendSpace(5)
		for line in TOOLTIP_LINES:
			self.helpToolTip.AutoAppendTextLine(line)
		self.helpToolTip.AlignHorizonalCenter()
		self.GetChild('AutoToolTipButton').SetToolTipWindow(self.helpToolTip)
		self.SetCenterPosition()

	# slot index helpers: skills 0-11 = slot window 0-11 = edit 0-11; items 0-11 = slot window 13-24 = edit 12-23
	def __IsSkillSlot(self, slotIndex):
		return 0 <= slotIndex < SKILL_SLOTS

	def __IsItemSlot(self, slotIndex):
		return ITEM_SLOT_BASE <= slotIndex < ITEM_SLOT_BASE + ITEM_SLOTS

	def __ExeIndex(self, slotIndex):
		if self.__IsSkillSlot(slotIndex):
			return slotIndex
		return SKILL_SLOTS + slotIndex - ITEM_SLOT_BASE

	def Open(self):
		hunt = GetHunt()
		hunt.Config()
		if HasExe():
			hunt.PushSettings()
		self.Refresh()
		self.Show()
		self.SetTop()

	def Close(self):
		for edit in self.edits:
			edit.KillFocus()
		self.OnOverOut()
		if self.optionWindow:
			self.optionWindow.Close()
		if self.rangeWindow:
			self.rangeWindow.Close()
		self.Hide()

	def Destroy(self):
		self.Close()
		for child in (self.optionWindow, self.rangeWindow):
			if child:
				child.Hide()
		self.optionWindow = None
		self.rangeWindow = None
		self.helpToolTip = None
		self.ClearDictionary()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def OnMoveWindow(self, x, y):
		self.__PlaceChildren()

	def __PlaceChildren(self):
		(x, y) = self.GetGlobalPosition()
		width = self.GetWidth()
		if self.optionWindow and self.optionWindow.IsShow():
			self.optionWindow.SetPosition(x + width - 5, y + 300)
		if self.rangeWindow and self.rangeWindow.IsShow():
			self.rangeWindow.SetPosition(x + width - 5, y + 380)

	def Refresh(self):
		hunt = GetHunt()
		config = hunt.Config()
		for key, button in self.toggles.items():
			if config[key]:
				button.Down()
				button.SetText('W\xb3')
			else:
				button.SetUp()
				button.SetText('Wy\xb3')
		if hunt.IsBusy():
			self.startButton.Down()
			self.startButton.Disable()
			self.stopButton.SetUp()
			self.stopButton.Enable()
		else:
			self.startButton.SetUp()
			self.startButton.Enable()
			self.stopButton.Down()
			self.stopButton.Disable()
		self.RefreshSlots(True)

	def RefreshSlots(self, texts=False):
		if not HasExe():
			return
		config = GetHunt().Config()
		for i in xrange(SKILL_SLOTS):
			(pos, value) = config['skill_slots'][i]
			skillIndex = player.GetSkillIndex(pos) if pos > 0 else 0
			if not skillIndex:
				self.slots.ClearSlot(i)
				if texts:
					self.edits[i].SetText('')
				continue
			if skill.GetSkillType(skillIndex) == skill.SKILL_TYPE_GUILD:
				grade, level = 0, guild.GetSkillLevel(pos)
			else:
				grade, level = player.GetSkillGrade(pos), player.GetSkillLevel(pos)
			self.slots.SetSkillSlotNew(i, skillIndex, grade, level)
			self.slots.SetSlotCountNew(i, grade, level)
			if player.IsSkillCoolTime(pos):
				(coolTime, elapsed) = player.GetSkillCoolTime(pos)
				self.slots.SetSlotCoolTime(i, coolTime, elapsed)
			if player.IsSkillActive(pos):
				self.slots.ActivateSlot(i)
			else:
				self.slots.DeactivateSlot(i)
			if texts:
				self.edits[i].SetText(str(value))
		for i in xrange(ITEM_SLOTS):
			(cell, value) = config['item_slots'][i]
			slotIndex = ITEM_SLOT_BASE + i
			vnum = player.GetItemIndex(cell) if cell >= 0 else 0
			if not vnum:
				self.slots.ClearSlot(slotIndex)
				if texts:
					self.edits[SKILL_SLOTS + i].SetText('' if cell < 0 else str(value))
				continue
			count = player.GetItemCount(cell)
			self.slots.SetItemSlot(slotIndex, vnum, count if count > 1 else 0)
			if texts:
				self.edits[SKILL_SLOTS + i].SetText(str(value))
		self.slots.RefreshSlot()

	def __ReadEdits(self):
		"""The fields to the exe (it keeps a skill at least at its cooldown, a potion at 100 % at most) and back."""
		hunt = GetHunt()
		for i in xrange(SKILL_SLOTS + ITEM_SLOTS):
			text = self.edits[i].GetText()
			if text and HasExe():
				player.AutoHuntTestSetSlotValue(i, ToInt(text))
		if HasExe():
			hunt.ReadSlotsBack()
		self.RefreshSlots(True)

	def OnToggle(self, key, value):
		config = GetHunt().Config()
		config[key] = value
		self.toggles[key].SetText('W\xb3' if value else 'Wy\xb3')
		if HasExe():
			player.AutoHuntTestSetOptions(config['attack'], config['skills'], config['items'], config['anchor'])

	def OnStart(self):
		self.__ReadEdits()
		GetHunt().RequestStart()
		self.Refresh()

	def OnStop(self):
		GetHunt().Stop()
		self.Refresh()

	def OnSave(self):
		self.__ReadEdits()
		if SaveConfig(GetHunt().Config()):
			Chat('ustawienia zapisane.')
		else:
			Chat('nie uda\xb3o si\xea zapisa\xe6 ustawie\xf1.')

	def OnClear(self, which):
		if GetHunt().running:
			Chat('najpierw zatrzymaj polowanie.')
			return
		config = GetHunt().Config()
		if which in (0, 1):
			config['skill_slots'] = [(0, 0)] * SKILL_SLOTS
		if which in (0, 2):
			config['item_slots'] = [(-1, 0)] * ITEM_SLOTS
		if HasExe():
			player.AutoHuntTestClearSlots(which)
		self.RefreshSlots(True)

	def OnClearSlot(self, slotIndex):
		if not HasExe() or not (self.__IsSkillSlot(slotIndex) or self.__IsItemSlot(slotIndex)):
			return
		config = GetHunt().Config()
		if self.__IsSkillSlot(slotIndex):
			player.AutoHuntTestSetSkillSlot(slotIndex, 0)
			config['skill_slots'][slotIndex] = (0, 0)
		else:
			player.AutoHuntTestSetItemSlot(slotIndex - ITEM_SLOT_BASE, -1)
			config['item_slots'][slotIndex - ITEM_SLOT_BASE] = (-1, 0)
		self.OnOverOut()
		self.RefreshSlots(True)

	def OnSelectEmpty(self, slotIndex):
		if not mouseModule.mouseController.isAttached() or not HasExe():
			return
		attachedType = mouseModule.mouseController.GetAttachedType()
		attachedSlot = mouseModule.mouseController.GetAttachedSlotNumber()
		if self.__IsSkillSlot(slotIndex) and attachedType == player.SLOT_TYPE_SKILL:
			if player.AutoHuntTestSetSkillSlot(slotIndex, attachedSlot):
				GetHunt().ReadSlotsBack()
			else:
				Chat('tej umiej\xeatno\x9cci nie da si\xea tu u\xbfy\xe6.')
		elif self.__IsItemSlot(slotIndex) and attachedType == player.SLOT_TYPE_INVENTORY:
			if player.AutoHuntTestSetItemSlot(slotIndex - ITEM_SLOT_BASE, attachedSlot):
				GetHunt().ReadSlotsBack()
			else:
				Chat('tego przedmiotu nie da si\xea tu u\xbfy\xe6 (mikstura, wzmocnienie albo rosa).')
		else:
			return
		mouseModule.mouseController.DeattachObject()
		self.RefreshSlots(True)

	def OnOverIn(self, slotIndex):
		if mouseModule.mouseController.isAttached():
			return
		config = GetHunt().Config()
		if self.__IsSkillSlot(slotIndex):
			pos = config['skill_slots'][slotIndex][0]
			skillIndex = player.GetSkillIndex(pos) if pos > 0 else 0
			if skillIndex:
				self.tooltipSkill.SetSkillNew(pos, skillIndex, player.GetSkillGrade(pos), player.GetSkillLevel(pos))
		elif self.__IsItemSlot(slotIndex):
			cell = config['item_slots'][slotIndex - ITEM_SLOT_BASE][0]
			if cell >= 0 and player.GetItemIndex(cell):
				self.tooltipItem.SetInventoryItem(cell)

	def OnOverOut(self):
		if self.tooltipSkill:
			self.tooltipSkill.HideToolTip()
		if self.tooltipItem:
			self.tooltipItem.HideToolTip()

	def OnOpenOptions(self):
		if self.rangeWindow and self.rangeWindow.IsShow():
			self.rangeWindow.Close()
		if self.optionWindow is None:
			try:
				self.optionWindow = OptionWindow(self)
			except Exception:
				LoadFailed('OptionWindow')
				return
		if self.optionWindow.IsShow():
			self.optionWindow.Close()
			return
		self.optionWindow.Load(GetHunt().Config())
		self.optionWindow.Show()
		self.optionWindow.SetTop()
		self.__PlaceChildren()

	def OnOpenRange(self):
		if self.optionWindow and self.optionWindow.IsShow():
			self.optionWindow.Close()
		if self.rangeWindow is None:
			try:
				self.rangeWindow = RangeWindow(self)
			except Exception:
				LoadFailed('RangeWindow')
				return
		if self.rangeWindow.IsShow():
			self.rangeWindow.Close()
			return
		self.rangeWindow.Open(GetHunt().Config()['range'])
		self.__PlaceChildren()

	def OnUpdate(self):
		now = Now()
		if now >= self.nextRefresh:
			self.nextRefresh = now + REFRESH
			self.RefreshSlots(False)


class Keeper(object):
	"""One of the game window's updateables (game.py RegisterUpdatable): the hunt's clock, and the end of the hunt and
	the window with the game window (a warp, a logout)."""

	def CanUpdate(self):
		return True

	def OnUpdate(self):
		GetHunt().OnUpdate()

	def Destroy(self):
		DestroyAll()


_data = {'hunt': None, 'window': None, 'keeper': None}


def GetHunt():
	if _data['hunt'] is None:
		_data['hunt'] = Hunt()
	return _data['hunt']


def _EnsureKeeper(game):
	keeper = _data['keeper']
	if keeper is not None or game is None:
		return
	try:
		keeper = Keeper()
		game.RegisterUpdatable(keeper)
		_data['keeper'] = keeper
	except Exception:
		pass


def RefreshWindow():
	window = _data['window']
	if window and window.IsShow():
		window.Refresh()


def ToggleWindow(game=None):
	"""game.py's "autohunt_test" action (Alt+H)."""
	if not HasExe():
		Chat('ten test wymaga nowego klienta (exe) - na tym kliencie dzia\xb3aj\xb9 zwyk\xb3e Auto \xa3owy (K).')
		return
	_EnsureKeeper(game)
	window = _data['window']
	if window is None:
		if _LOAD_FAILED.get('AutoHuntTestWindow'):
			LoadFailed('AutoHuntTestWindow')
			return
		try:
			window = AutoHuntTestWindow()
		except Exception:
			LoadFailed('AutoHuntTestWindow')
			return
		_data['window'] = window
	if window.IsShow():
		window.Close()
	else:
		window.Open()


def IsRunning():
	hunt = _data['hunt']
	return hunt is not None and hunt.IsBusy()


def StopIfRunning():
	"""uiautohunt.py's Start: our Auto Lowy start, the test stops."""
	if IsRunning():
		_data['hunt'].Stop(quiet=True)
		Chat('zatrzymane - ruszy\xb3y zwyk\xb3e Auto \xa3owy.')


def OnServerCommand(*args):
	"""game.py "AutoHuntTest on|off [reason]" (server-patches/autohunttest)."""
	if not args:
		return
	GetHunt().OnServer(*args)


def DestroyAll():
	hunt = _data['hunt']
	if hunt:
		hunt.Destroy()
	window = _data['window']
	_data['window'] = None
	_data['keeper'] = None
	if window:
		window.Destroy()
