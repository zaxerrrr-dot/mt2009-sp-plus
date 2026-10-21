# Buffi - the support shaman of Ameria Project (MT2009_PLUS_BUFFI_V1; the
# owner, 21 October 2026: "W zamian za towarzysza dodaj system buffi z Amerii.
# Pod tym samym skrotem klawiszowym itd."). The P key (keybind "companion")
# and the inventory side bar's first button open it, where the companion's
# window was; the companion (uisidekick.py) is off unless the server's .env
# says M2_SIDEKICK=1 and then opens from its letter or the "sidekick" key.
#
# MT2009_PLUS_BUFFI_V2 (the owner, 21 October 2026: "okno i rozwoj buffi
# dokladnie jak w Amerii", "do G1 zwykle ksiegi szamana przez okno buffi"):
# the window is Ameria's two Buffi pages side by side (uiscript/buffiwindow.py):
#   - the buffi's costume slots (Ameria's inventory page IV, companion_bg.png):
#     an outfit, a hairstyle, a weapon and a sash costume dragged onto them (or
#     used from the bag while this window is open - "/buffi page 1|0", Ameria's
#     /buffi_costume_page) dress the shaman; they give their owner nothing;
#   - its skills (Ameria's character window "Buffi" page, buffi_skill_bg.png):
#     the four skills by grade; a shaman's skill book (50300 of Blogoslawienstwo,
#     Pomoc Smoka, Szybkosc, Zwiekszenie Ataku) dropped onto its buffi skill
#     trains it to G1 ("/buffi read <skill> <window> <cell>"); from G1 the
#     Kamien Duchowy Buffi (61031) - used from the bag (quest buffi).
#
# MT2009_PLUS_BUFFI_V3 (the owner's list of 22 October 2026, poprawki 1-5):
#   - three costume slots: outfit, hairstyle, weapon - no sash, and the player's own mount costume is not shown
#     here any more (it was: Ameria's page showed it, the owner took it for a buffi slot);
#   - the skills show their grade as the skill window does: the grade's icon column and M1-M10 / G1-G10 / P
#     (player.GetSkillGrade + the level within it - player.GetSkillLevel is that, not the raw 20-40), the tooltip
#     likewise (uicharacter.py OverInItem); the tooltip's values are the weaker ones (gen_buffi.py CLIENT_FACTOR);
#   - Buffi from level 55: below it the window does not open ("Buffi dostepna od 55 poziomu.").
#
# The server half is playerbot_buffi.cpp (server-patches/buffi/README.md):
#   window -> "/buffi info"          the state
#             "/buffi toggle"        call / send away (the seal in the bag)
#             "/buffi name <name>"   Zwoj Imienia Buffi (61030)
#             "/buffi page 1|0"      the window open / closed
#             "/buffi read <skill> <window> <cell>"   a shaman's skill book
#   server -> "BUFFI state <on> <called> <seal vnum> <named> <name|-> <lv164>
#                <lv165> <lv166> <lv167> <boss bonus seconds> <name scrolls>
#                [<skill group>]"
#             "BUFFI askname"       a name scroll was used: the name dialog
#             "BUFFI off"           M2_BUFFI=0 on the server
#             "BUFFI low <level>"   MT2009_PLUS_BUFFI_V3: under the level Buffi needs (the window closes)
# (game.py passes the "BUFFI" lines here.)
#
# The costume slots are the server's wear cells 28-31 (WEAR_BUFFI_*); the 3.0
# exe names them item.BUFFI_SLOT_* (client-patches/exe), an older one gets the
# same cells from player.EQUIPMENT_SLOT_START. The skills' slots are their
# vnums (RegisterSlots, as riposty.py) so the skill tooltip reads them.
#
# Python 2.7 as the client has it; the texts are CP1250.

import chat
import item
import mouseModule
import net
import player
import skill
import ui
import uiCommon
import uiToolTip

import warpsafe

NAME_MAX = 16

# the buffi's costume cells (the server's WEAR_BUFFI_BODY/HEAD/WEAPON = 28-30; MT2009_PLUS_BUFFI_V3: no sash 31,
# no mount)
BUFFI_CELLS = (
	getattr(item, "BUFFI_SLOT_BODY", player.EQUIPMENT_SLOT_START + 28),
	getattr(item, "BUFFI_SLOT_HEAD", player.EQUIPMENT_SLOT_START + 29),
	getattr(item, "BUFFI_SLOT_WEAPON", player.EQUIPMENT_SLOT_START + 30),
)
MIN_LEVEL = 55		# MT2009_PLUS_BUFFI_V3: the server's MIN_LEVEL

TEXT_TITLE = "Buffi"
TEXT_OFF = "Buffi jest wy\xb3\xb9czony na tym serwerze."
TEXT_LOW_LEVEL = "Buffi dost\xeapna od %d poziomu."
TEXT_INFO_PAGE = "Ta strona jest tylko dla Buffi."
TEXT_NO_SEAL = "Potrzebujesz piecz\xeaci Buffi."
TEXT_CALLED = "%s - przywo\xb3ana."
TEXT_NOT_CALLED = "%s - odwo\xb3ana."
TEXT_NO_NAME = "Bez imienia (Zw\xf3j Imienia Buffi)."
TEXT_NAME = "Imi\xea: %s"
TEXT_NO_GROUP = "Wybierz drog\xea umiej\xeatno\x9cci."
TEXT_BOSS = "+10%% w bossy: %s"
TEXT_CALL = "Przywo\xb3aj"
TEXT_SEND_AWAY = "Odwo\xb3aj"
TEXT_ASK_NAME = "Imi\xea Buffi (2-%d liter lub cyfr)"
TEXT_NO_SCROLL = "Nie masz Zwoju Imienia Buffi (ItemShop)."
TEXT_COSTUMES_FREE = "Kostiumy Buffi nie daj\xb9 bonus\xf3w."
TEXT_BOOK_TIP = "Do G1: Ksi\xeaga Umiej\xeatno\x9cci - %s (szaman)."
TEXT_BOOK_TIP2 = "Przeci\xb9gnij j\xb9 tutaj (szansa, PD i odst\xeap jak zwykle)."
TEXT_STONE_TIP = "Od G1 do P: Kamie\xf1 Duchowy Buffi (u\xbfyj go)."
TEXT_NEEDS_NAME = "Wymaga imienia Buffi (Zw\xf3j Imienia Buffi)."
TEXT_LEVEL_NOW = "Aktualny poziom: %s"
TEXT_LEVEL_NEXT = "Nast\xeapny poziom: %s (maks. P)"
TEXT_DURATION = "Czas trwania: 60 min (Buffi odnawia je sama)"
TEXT_CASTING_TIME = "Czas \xb3adowania kr\xf3tszy przez %d s"
TEXT_WRONG_BOOK = "[Buffi] T\xea umiej\xeatno\x9c\xe6 trenuje Ksi\xeaga Umiej\xeatno\x9cci: %s (szaman)."
TEXT_NOT_BOOK = "[Buffi] Na umiej\xeatno\x9c\xe6 Buffi przeci\xb9gnij Ksi\xeag\xea Umiej\xeatno\x9cci szamana."
SEALS = {61025: "Buffi (7 dni)", 61026: "Buffi"}

# the buffi skill, the shaman skill whose book trains it, its Polish name
SKILLS = (
	(164, 94, "B\xb3ogos\xb3awie\xf1stwo"),
	(165, 96, "Pomoc Smoka"),
	(166, 110, "Szybko\x9c\xe6"),
	(167, 111, "Zwi\xeakszenie Ataku"),
)
NAMED_ONLY = (166, 167)
SKILL_BOOK = 50300
GRADE_STEP = 20		# Ameria's grid: the grade columns 1/21/41 (skill.SKILL_GRADE_STEP_COUNT)
GRADE_COLUMNS = 3	# skill.SKILL_GRADE_COUNT: the normal, master and grand master columns, P in the last
GRADE_BASE = {0: 0, 1: 19, 2: 29, 3: 39}	# MT2009_PLUS_BUFFI_V3: the raw level of a grade's first step - 1

COLOR_GOOD = 0xff9be27c
COLOR_WARN = 0xffe0b060

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
		return 3
	if level >= 30:
		return 2
	if level >= 20:
		return 1
	return 0


def Duration(seconds):
	days, rest = divmod(max(0, seconds), 86400)
	hours, rest = divmod(rest, 3600)
	if days:
		return "%d d. %d godz." % (days, hours)
	return "%d godz. %d min." % (hours, rest // 60)


def CleanName(text):
	text = (text or "").strip()
	return "".join([c for c in text if c.isalnum()])[:NAME_MAX]


def RegisterSlots():
	"""playersettingmodule.RegisterSkill: each buffi skill's slot is its vnum (the skill tooltip and its level)."""
	for vnum, book, name in SKILLS:
		try:
			player.SetSkill(vnum, vnum)
		except Exception:
			pass


def GradeLevel(vnum):
	"""MT2009_PLUS_BUFFI_V3: (grade, level within it, raw level 0-40) of a buffi skill - the client's own skill
	data (player.GetSkillGrade / GetSkillLevel of its slot = its vnum, the level within the grade as the skill window
	shows it), else the server's raw level of "BUFFI state"."""
	raw = 0
	try:
		grade = player.GetSkillGrade(vnum)
		level = player.GetSkillLevel(vnum)
		if level > 0 and grade in GRADE_BASE:
			raw = min(40, level + GRADE_BASE[grade])
	except Exception:
		pass
	if raw <= 0:
		data = _state['data']
		raw = min(40, data['levels'].get(vnum, 0)) if data else 0
	if raw <= 0:
		return 0, 0, 0
	grade = Grade(raw)		# from the raw level, whatever grade the packet said
	return grade, raw - GRADE_BASE[grade], raw


def GradeText(raw):
	"""MT2009_PLUS_BUFFI_V3: a raw level as the skill window names it - M1-M10, G1-G10, P."""
	if raw >= 40:
		return "P"
	if raw >= 30:
		return "G%d" % (raw - 29)
	if raw >= 20:
		return "M%d" % (raw - 19)
	return "%d" % raw


# the client's skill power of a level (Locale.cpp INTERNATIONAL_SKILL_POWERS = the server's table): k = power / 100
SKILL_POWER = (0, 5, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 50, 52, 54, 56, 58, 60,
	63, 66, 69, 72, 82, 85, 88, 91, 94, 98, 102, 106, 110, 115, 125)


def Level(vnum):
	"""The raw level 0-40 (M1 = 20, G1 = 30, P = 40)."""
	return GradeLevel(vnum)[2]


def LevelOk(say=True):
	"""MT2009_PLUS_BUFFI_V3: Buffi from the character's level 55."""
	try:
		if player.GetStatus(player.LEVEL) >= MIN_LEVEL:
			return True
	except Exception:
		return True		# the server checks it anyway
	if say:
		chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_LOW_LEVEL % MIN_LEVEL)
	return False


def AttachedWindow(slotType):
	"""The item window of an attached item: the bag or a storage of the extra inventory (uiekwipunek.py)."""
	if slotType == player.SLOT_TYPE_INVENTORY:
		return player.INVENTORY
	try:
		return __import__("uiekwipunek").WindowOfSlotType(slotType)
	except Exception:
		return -1


class BuffiWindow(ui.ScriptWindow):

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.dialog = None
		self.itemToolTip = None
		self.skillToolTip = None
		self.__Load()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __Load(self):
		ui.PythonScriptLoader().LoadScriptFile(self, "UIScript/BuffiWindow.py")
		self.GetChild("board").SetCloseEvent(ui.__mem_func__(self.Close))
		self.costumeSlot = self.GetChild("CostumeSlot")
		self.skillSlot = self.GetChild("Skill_Slot")
		self.groupButton = self.GetChild("Skill_Group_Button")
		self.groupButton.Down()
		self.groupButton.SAFE_SetEvent(self.groupButton.Down)
		self.infoLines = [self.GetChild("Buffi_Info_%d" % i) for i in (1, 2, 3)]
		self.locks = [self.GetChild("Buffi_Lock_%d" % i) for i in xrange(1, 7)]
		self.toggleButton = self.GetChild("Toggle_Button")
		self.renameButton = self.GetChild("Rename_Button")
		self.stateText = self.GetChild("State_Text")
		self.toggleButton.SetText(TEXT_CALL)
		self.toggleButton.SAFE_SetEvent(self.OnToggle)
		self.renameButton.SAFE_SetEvent(self.OnRename)
		for lock in self.locks:
			lock.AddFlag("not_pick")
			lock.Hide()

		slot = self.costumeSlot
		slot.SetSelectEmptySlotEvent(ui.__mem_func__(self.OnSelectEmptyCostume))
		slot.SetSelectItemSlotEvent(ui.__mem_func__(self.OnSelectCostume))
		slot.SetUnselectItemSlotEvent(ui.__mem_func__(self.OnUseCostume))
		slot.SetUseSlotEvent(ui.__mem_func__(self.OnUseCostume))
		slot.SetOverInItemEvent(ui.__mem_func__(self.OnOverInCostume))
		slot.SetOverOutItemEvent(ui.__mem_func__(self.OnOverOut))

		slot = self.skillSlot
		slot.SetSelectEmptySlotEvent(ui.__mem_func__(self.OnDropOnSkill))
		slot.SetSelectItemSlotEvent(ui.__mem_func__(self.OnDropOnSkill))
		slot.SetOverInItemEvent(ui.__mem_func__(self.OnOverInSkill))
		slot.SetOverOutItemEvent(ui.__mem_func__(self.OnOverOut))

		self.itemToolTip = uiToolTip.ItemToolTip()
		self.itemToolTip.HideToolTip()
		self.skillToolTip = uiToolTip.SkillToolTip()
		self.skillToolTip.HideToolTip()

	# ------------------------------------------------------------------ the costume slots

	def OnSelectEmptyCostume(self, cell):
		if not mouseModule.mouseController.isAttached():
			return
		attachedType = mouseModule.mouseController.GetAttachedType()
		attachedPos = mouseModule.mouseController.GetAttachedSlotNumber()
		mouseModule.mouseController.DeattachObject()
		if attachedType != player.SLOT_TYPE_INVENTORY or attachedPos == cell:
			return
		# the server puts it onto this buffi slot, or refuses (another kind of costume)
		net.SendItemMovePacket(attachedPos, cell, 0)

	def OnSelectCostume(self, cell):
		if mouseModule.mouseController.isAttached():
			attachedType = mouseModule.mouseController.GetAttachedType()
			attachedPos = mouseModule.mouseController.GetAttachedSlotNumber()
			mouseModule.mouseController.DeattachObject()
			# onto a dressed slot: the costume is used - with this window open it goes onto the buffi and
			# the old one back into the bag
			if attachedType == player.SLOT_TYPE_INVENTORY and attachedPos != cell:
				net.SendItemUsePacket(attachedPos)
			return
		vnum = player.GetItemIndex(cell)
		if vnum:
			mouseModule.mouseController.AttachObject(self, player.SLOT_TYPE_INVENTORY, cell, vnum)

	def OnUseCostume(self, cell):
		if player.GetItemIndex(cell):
			net.SendItemUsePacket(cell)

	def OnOverInCostume(self, cell):
		if not self.itemToolTip or not player.GetItemIndex(cell):
			return
		self.itemToolTip.ClearToolTip()
		self.itemToolTip.SetInventoryItem(cell)
		if cell in BUFFI_CELLS:
			self.itemToolTip.AppendSpace(5)
			self.itemToolTip.AppendTextLine(TEXT_COSTUMES_FREE, COLOR_WARN)
		self.itemToolTip.ShowToolTip()

	def OnOverOut(self):
		if self.itemToolTip:
			self.itemToolTip.HideToolTip()
		if self.skillToolTip:
			self.skillToolTip.HideToolTip()

	# ------------------------------------------------------------------ the skills

	def SkillOfSlot(self, slot):
		index = slot % GRADE_STEP
		if 1 <= index <= len(SKILLS):
			return SKILLS[index - 1]
		return None

	def OnDropOnSkill(self, slot):
		if not mouseModule.mouseController.isAttached():
			return
		entry = self.SkillOfSlot(slot)
		attachedType = mouseModule.mouseController.GetAttachedType()
		attachedPos = mouseModule.mouseController.GetAttachedSlotNumber()
		attachedVnum = mouseModule.mouseController.GetAttachedItemIndex()
		mouseModule.mouseController.DeattachObject()
		if not entry:
			return
		vnum, book, name = entry
		window = AttachedWindow(attachedType)
		if window < 0 or attachedVnum != SKILL_BOOK:
			chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_NOT_BOOK)
			return
		try:
			bookSkill = player.GetItemMetinSocket(window, attachedPos, 0)
		except Exception:
			bookSkill = book	# the server checks it anyway
		if bookSkill != book:
			chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_WRONG_BOOK % name)
			return
		Send("read %d %d %d" % (vnum, window, attachedPos))

	def OnOverInSkill(self, slot):
		entry = self.SkillOfSlot(slot)
		if not entry or not self.skillToolTip:
			return
		vnum, book, name = entry
		grade, inGrade, level = GradeLevel(vnum)
		column = min(GRADE_COLUMNS - 1, slot // GRADE_STEP)
		tip = self.skillToolTip
		tip.ClearToolTip()
		# MT2009_PLUS_BUFFI_V3: as the skill window's tooltip (uicharacter.py OverInItem) on the column of its grade
		# (P on the last) - the grade's name (Mistrz / Arcymistrz / Perfekcyjny Mistrz), the level as M1-M10 /
		# G1-G10 / P now and next, the (weaker) values of both; only the name on another column
		try:
			if level > 0 and (column == grade or (grade == GRADE_COLUMNS and column == GRADE_COLUMNS - 1)):
				self.__SkillToolTip(tip, vnum, grade, level)
			else:
				tip.SetSkillOnlyName(vnum, vnum, column)
		except Exception:
			tip.SetTitle(name)
		tip.AppendSpace(5)
		data = _state['data']
		if vnum in NAMED_ONLY and not (data and data['named']):
			tip.AppendTextLine(TEXT_NEEDS_NAME, COLOR_WARN)
		if level < 30:
			tip.AppendTextLine(TEXT_BOOK_TIP % name, COLOR_GOOD)
			tip.AppendTextLine(TEXT_BOOK_TIP2, COLOR_GOOD)
		if level < 40:
			tip.AppendTextLine(TEXT_STONE_TIP, COLOR_GOOD)
		tip.ShowToolTip()

	def __SkillToolTip(self, tip, vnum, grade, level):
		"""MT2009_PLUS_BUFFI_V3: a buffi skill's tooltip - the values its owner gets from the buffi at this level and
		the next (skilldesc's polys with the grade's cut, gen_buffi.py CLIENT_FACTOR; "sl" = the raw level)."""
		tip.toolTipWidth = tip.SKILL_TOOL_TIP_WIDTH
		tip.ResizeToolTip()
		tip.ClearToolTip()
		tip.SetTitle(skill.GetSkillName(vnum, grade))
		gradeName = tip.SKILL_GRADE_NAME.get(grade)
		if gradeName:
			tip.AppendSpace(5)
			tip.AppendTextLine(gradeName % skill.GetSkillName(vnum, 0), tip.CAN_LEVEL_UP_COLOR)
		tip.AppendDescription(skill.GetSkillDescription(vnum), 25)
		tip.AppendSkillConditionData(vnum)
		steps = [(level, TEXT_LEVEL_NOW % GradeText(level), tip.NORMAL_COLOR, tip.ENABLE_COLOR)]
		if level < 40:
			steps.append((level + 1, TEXT_LEVEL_NEXT % GradeText(level + 1), tip.NEGATIVE_COLOR, tip.DISABLE_COLOR))
		for raw, title, titleColor, color in steps:
			k = SKILL_POWER[min(raw, len(SKILL_POWER) - 1)] / 100.0
			tip.AppendSpace(5)
			tip.AppendTextLine(title, titleColor)
			for i in xrange(skill.GetSkillAffectDescriptionCount(vnum)):
				tip.AppendTextLine(skill.GetSkillAffectDescription(vnum, i, raw, k), color)
			tip.AppendTextLine(TEXT_DURATION, color)
			if vnum == 166:		# Szybkosc's casting speed lasts 60 + 100 * k seconds (playerbot_buffi.cpp Cast)
				tip.AppendTextLine(TEXT_CASTING_TIME % int(60 + 100 * k), color)

	# ------------------------------------------------------------------ the state

	def Refresh(self):
		for cell in BUFFI_CELLS:
			self.costumeSlot.SetItemSlot(cell, player.GetItemIndex(cell), 0)
		self.costumeSlot.RefreshSlot()

		data = _state['data']
		named = bool(data and data['named'])
		# Ameria's grid: a skill's three grade columns, the one of its grade lit and counted - MT2009_PLUS_BUFFI_V3:
		# as uicharacter.py's active skills, the grade and the level within it (M4 = "m4", G2 = "g2", P = "p"),
		# not the raw level
		for k, (vnum, book, name) in enumerate(SKILLS):
			grade, inGrade, level = GradeLevel(vnum)
			for j in xrange(GRADE_COLUMNS):
				real = k + 1 + j * GRADE_STEP
				if level <= 0:
					self.skillSlot.ClearSlot(real)
					continue
				self.skillSlot.SetSkillSlotNew(real, vnum, j, inGrade)
				if grade == GRADE_COLUMNS and j == GRADE_COLUMNS - 1:
					self.skillSlot.SetSlotCountNew(real, grade, inGrade)
				elif grade != j:
					self.skillSlot.SetSlotCount(real, 0)
					self.skillSlot.DeactivateSlot(real)
				else:
					self.skillSlot.SetSlotCountNew(real, grade, inGrade)
		self.skillSlot.RefreshSlot()
		# Ameria's buffi_slot_hide: Szybkosc (1-3) and Zwiekszenie Ataku (4-6) until they are learned
		for i, lock in enumerate(self.locks):
			if Level(166 if i < 3 else 167) < 1:
				lock.Show()
			else:
				lock.Hide()

		if _state['off']:
			self.__Info(TEXT_OFF, "", "")
			self.toggleButton.Hide()
			self.renameButton.Hide()
			self.stateText.SetText("")
			return
		if data is None:
			self.__Info(TEXT_INFO_PAGE, "", "")
			return
		self.toggleButton.Show()
		self.toggleButton.SetText(TEXT_SEND_AWAY if data['called'] else TEXT_CALL)
		if not data['seal']:
			line1 = TEXT_NO_SEAL
		else:
			line1 = (TEXT_CALLED if data['called'] else TEXT_NOT_CALLED) % SEALS.get(data['seal'], "Buffi")
		line2 = TEXT_NAME % data['name'] if named else TEXT_NO_NAME
		line3 = TEXT_NO_GROUP if data.get('group', 1) == 0 else TEXT_INFO_PAGE
		self.__Info(line1, line2, line3)
		if data['scrolls'] > 0 and data['called']:
			self.renameButton.Show()
		else:
			self.renameButton.Hide()
		self.stateText.SetText(TEXT_BOSS % Duration(data['boss']) if data['boss'] > 0 else "")

	def __Info(self, line1, line2, line3):
		for line, text in zip(self.infoLines, (line1, line2, line3)):
			line.SetText(text)

	# ------------------------------------------------------------------ the buttons

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

	# ------------------------------------------------------------------ open / close

	def Open(self):
		if not LevelOk():	# MT2009_PLUS_BUFFI_V3
			return
		self.Refresh()
		self.Show()
		self.SetTop()
		Send("page 1")

	def Close(self):
		self.__CloseDialog()
		self.OnOverOut()
		if self.IsShow():
			Send("page 0")
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def Destroy(self):
		self.__CloseDialog()
		self.OnOverOut()
		self.Hide()
		self.itemToolTip = None
		self.skillToolTip = None
		self.ClearDictionary()


def GetWindow():
	window = _state['window']
	if window is None:
		import uiminigameutil
		window = uiminigameutil.SafeCreate(BuffiWindow, TEXT_TITLE)
		_state['window'] = window
	return window


def OpenWindow():
	if not LevelOk():	# MT2009_PLUS_BUFFI_V3: Buffi from level 55
		return
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


def Refresh():
	"""interfacemodule.RefreshInventory / RefreshSkill: the slots of an open window."""
	window = _state['window']
	if window is not None and window.IsShow():
		try:
			window.Refresh()
		except Exception:
			import dbg
			import sys
			dbg.TraceError('uibuffi.Refresh: %s' % str(sys.exc_info()[1]))


def OnCommand(sub='', *args):
	try:
		if sub == 'off':
			_state['off'] = True
		elif sub == 'low':
			# MT2009_PLUS_BUFFI_V3: under level 55 (the server said so in the chat) - the window closes
			window = _state['window']
			if window is not None and window.IsShow():
				window.Close()
			return
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
				'group': ToInt(args[11], 1) if len(args) >= 12 else 1,
			}
		elif sub == 'askname':
			window = GetWindow()
			if window is not None and LevelOk(False):
				window.Open()
				window.AskName()
			return
		else:
			return
		Refresh()
	except Exception:
		import dbg
		import sys
		dbg.TraceError('uibuffi.OnCommand %s: %s' % (str((sub,) + args), str(sys.exc_info()[1])))
