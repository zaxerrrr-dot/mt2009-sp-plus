# MT2009_PLUS_AURA_V1 (the owner, 15 October): Szata Aury - the aura outfit system of the pl-wiki ("System Szat Aury")
# with Owsap's windows (uiaura.py, uiscript/aura_absorbwindow.py, aura_levelupwindow.py, Autor: Owsap) on chat commands
# instead of his packets (server-patches/aura; the server checks everything again at "accept"):
#   window 0  przenies parametry  the outfit (left) + a bracelet / necklace / earrings / shield (right, destroyed);
#             the small slot shows the outfit with the bonuses it will get
#   window 1  rozwoj              the outfit + Lodowa / Ognista Runa Aury (only the runes needed are taken)
#             MT2009_PLUS_AURA_RUNE_STACK_V1 (the owner, 10 November 2026): one accept spends the whole stack (Lodowa
#             Runa Aury stacks to 9999) as far as the grade's top - every level-up at once, the rest stays; asks first
#             with the numbers. A right click on an item of the bag or of the Dodatkowy ekwipunek's storages puts it
#             into the open window (TakeItem: an outfit -> the left slot, anything else -> the right one).
#   window 2  ewolucja            the outfit at the top of its grade, full + the grade's material and Yang
# server -> "AURA open <type>", "AURA set <slot> <cell> <vnum> <count> [<window>]", "AURA del <slot>", "AURA close",
#           "AURA done", "AURA view <vid> <vnum>" (the outfit another character wears: the 3.0 exe's chrmgr.SetAura)
# client -> /aura in <slot> <cell> [<window>] | out <slot> | accept | cancel
# Also here: the outfit's tooltip lines (AppendToolTip, uitooltip.py), its costume slot (SLOT, uiinventory.py).
# The outfit's sockets (Owsap's): socket 0 the absorbed item's vnum, socket 1 (1000 + level) * 100000 + exp - a new
# outfit (0) is its grade's first level. The numbers are the server's (playerbot_aura.cpp).
#
# Python 2.7 as the client has it; the texts are CP1250 escapes.

import app
import chat
import item
import mouseModule
import net
import player
import snd
import ui
import uiCommon
import localeInfo

VNUM_FIRST = 49101			# Zwyczajna Szata Aury .. 49106 Promienista (grade = vnum - 49100)
VNUM_LAST = 49106
WEAR_COSTUME_AURA = 27		# the server's WEAR_COSTUME_AURA
COSTUME_AURA = 5			# the server's COSTUME_AURA (uicostumehide.py: the eye)
SOCKET_DRAIN = 0
SOCKET_LEVEL = 1
MAX_LEVEL = 250

TYPE_ABSORB = 0
TYPE_GROWTH = 1
TYPE_EVOLVE = 2
SLOT_MAIN = 0
SLOT_SUB = 1
SLOT_RESULT = 2
LIMIT_RANGE = 1000

# min level, max level, exp of one level, evolution material, its count, Yang (Owsap = the pl-wiki)
GRADES = (
	(1, 49, 1000, 30617, 10, 5000000),
	(50, 99, 2000, 31136, 10, 5000000),
	(100, 149, 4000, 31137, 10, 5000000),
	(150, 199, 8000, 31138, 10, 8000000),
	(200, 249, 16000, 31138, 20, 10000000),
	(250, 250, 0, 0, 0, 0),
)
GRADE_NAMES = ('Zwyczajna', 'Prosta', 'Szlachetna', 'B\xb3yszcz\xb9ca', 'Wytworna', 'Promienista')
RUNE_EXP = {49990: 1, 49991: 10, 49992: 50, 49993: 100, 49994: 250, 49995: 500}
EFFECTS = {
	49101: 'd:/ymir work/pc/common/effect/aura/aura_01_49_001.mse',
	49102: 'd:/ymir work/pc/common/effect/aura/aura_50_99_002.mse',
	49103: 'd:/ymir work/pc/common/effect/aura/aura_100_149_003.mse',
	49104: 'd:/ymir work/pc/common/effect/aura/aura_150_199_004.mse',
	49105: 'd:/ymir work/pc/common/effect/aura/aura_200_249_005.mse',
	49106: 'd:/ymir work/pc/common/effect/aura/aura_250_006.mse',
}

# MT2009_PLUS_AURA_NAMES_V1: the owner's names - the runes are "rozwoj", the next grade "ewolucja" (the quest's too)
TITLE = {TYPE_ABSORB: 'Szata aury: przenie\x9c parametry', TYPE_GROWTH: 'Szata aury: rozw\xf3j', TYPE_EVOLVE: 'Szata aury: ewolucja'}
SCRIPT = {TYPE_ABSORB: 'UIScript/Aura_AbsorbWindow.py', TYPE_GROWTH: 'UIScript/Aura_LevelUpWindow.py',
	TYPE_EVOLVE: 'UIScript/Aura_LevelUpWindow.py'}
TEXT_NOT_BAG = 'Przeci\xb9gnij przedmiot z ekwipunku (nie za\xb3o\xbfony).'
TEXT_PUT_MAIN = 'Najpierw w\xb3\xf3\xbf szat\xea aury.'
TEXT_PUT_BOTH = 'W\xb3\xf3\xbf oba przedmioty.'
TEXT_QUESTION_ABSORB = 'Przedmiot z prawego pola zniknie. Przenie\x9c\xe6 parametry?'
TEXT_QUESTION_EVOLVE = 'Ewoluowa\xe6 szat\xea za %s Yang i materia\xb3?'
TEXT_QUESTION_GROWTH = 'Zu\xbfy\xe6 %d z %d run? Poziom %d -> %d.'			# MT2009_PLUS_AURA_RUNE_STACK_V1
TEXT_QUESTION_GROWTH_TOP = 'Zu\xbfy\xe6 %d z %d run? Poziom %d -> %d (szczyt rodzaju, reszta zostaje).'
TEXT_GROWTH_NOTHING = 'Ta szata nie przyjmie ju\xbf run - czas na ewolucj\xea.'
TEXT_SLOT_TAKEN = 'Najpierw wyjmij przedmiot z prawego pola.'
TEXT_QUICK_AURA = 'PPM: w\xb3\xf3\xbf do okna szaty aury'
TEXT_NOW = 'Teraz:'
TEXT_AFTER = 'Po rozwoju (%d z %d szt.):'
TEXT_EVOLVED = 'Po ewolucji:'
TEXT_LEVEL = 'Poziom %d (%s), absorpcja %.1f%%'
TEXT_EXP = 'Do\x9cwiadczenie: %d%%'
TEXT_READY = 'Szczyt rodzaju - czas na ewolucj\xea'
TEXT_CHANCE = 'Szansa powodzenia: 100%'
TEXT_NEED = 'Potrzeba:'
TEXT_MATERIAL = '%s x%d (masz %d)'
TEXT_COST = 'Koszt: %s'

TOOLTIP_LEVEL = 'Poziom: %d (%s Szata Aury)'
TOOLTIP_EXP = 'Do\x9cwiadczenie: %d%% (%d / %d)'
TOOLTIP_READY = 'Gotowa do ewolucji u Theowahdana'
TOOLTIP_ABSORB = 'Stopie\xf1 absorpcji: %.1f%%'
TOOLTIP_FROM = 'Przeniesione z: %s'
TOOLTIP_NONE = 'Brak przeniesionych parametr\xf3w'
TOOLTIP_WHERE = 'Przenie\x9c je u Theowahdana.'
TOOLTIP_COLOR = 0xffb4d5ff


def SLOT():
	"""The outfit's slot of the costume window (the server's WEAR_COSTUME_AURA)."""
	return player.EQUIPMENT_SLOT_START + WEAR_COSTUME_AURA


def IsAuraVnum(vnum):
	return VNUM_FIRST <= vnum <= VNUM_LAST


def Grade(vnum):
	if not IsAuraVnum(vnum):
		return 0
	return vnum - VNUM_FIRST


def Decode(vnum, socket):
	"""(level, exp) of an outfit from its socket 1."""
	(lo, hi, need) = GRADES[Grade(vnum)][:3]
	try:
		socket = int(socket)
	except (TypeError, ValueError):
		socket = 0
	if socket < 100000000:
		return (lo, 0)
	return (max(lo, min(hi, socket / 100000 - 1000)), max(0, min(need, socket % 100000)))


def IsFull(vnum, level, exp):
	(lo, hi, need) = GRADES[Grade(vnum)][:3]
	return level >= hi and exp >= need


def Grow(vnum, level, exp, count, value):
	"""The runes used of `count` worth `value` each and the state after them (the server's aura::Grow)."""
	(lo, hi, need) = GRADES[Grade(vnum)][:3]
	used = 0
	while used < count and need > 0 and not IsFull(vnum, level, exp):
		used += 1
		exp += value
		while exp >= need and level < hi:
			exp -= need
			level += 1
		if level >= hi and exp >= need:
			exp = need
	return (used, level, exp)


def Drain(value, level):
	"""The outfit's part of a bonus line (Owsap: under 1 -> 1, else cut)."""
	if value <= 0 or level <= 0:
		return 0
	v = float(value) * level / 1000.0
	if v < 1.0:
		return 1
	return int(v)


def ExpPct(vnum, level, exp):
	need = GRADES[Grade(vnum)][2]
	if need <= 0:
		return 100
	return exp * 100 / need


def Money(n):
	try:
		return localeInfo.NumberToMoneyString(n)
	except Exception:
		return '%d Yang' % n


def ItemName(vnum):
	item.SelectItem(vnum)
	return item.GetItemName()


# ---- the tooltip (uitooltip.py) --------------------------------------------------------------------------------------
def _MoveSpeed():
	return getattr(item, 'APPLY_MOV_SPEED', -1)


def AppendToolTip(toolTip, itemVnum, metinSlot, attrSlot):
	"""The outfit's level, absorption and the absorbed bonuses at its rate; item.SelectItem(itemVnum) again at the end."""
	if not IsAuraVnum(itemVnum):
		return
	socket0 = 0
	socket1 = 0
	try:
		if metinSlot:
			socket0 = int(metinSlot[SOCKET_DRAIN])
			socket1 = int(metinSlot[SOCKET_LEVEL])
	except (TypeError, ValueError, IndexError):
		pass
	grade = Grade(itemVnum)
	(level, exp) = Decode(itemVnum, socket1)
	need = GRADES[grade][2]
	toolTip.AppendSpace(5)
	toolTip.AppendTextLine(TOOLTIP_LEVEL % (level, GRADE_NAMES[grade]), toolTip.CONDITION_COLOR)
	if need > 0:
		toolTip.AppendTextLine(TOOLTIP_EXP % (ExpPct(itemVnum, level, exp), exp, need), toolTip.CONDITION_COLOR)
		if IsFull(itemVnum, level, exp):
			toolTip.AppendTextLine(TOOLTIP_READY, toolTip.SPECIAL_TITLE_COLOR)
	toolTip.AppendTextLine(TOOLTIP_ABSORB % (level / 10.0), toolTip.CONDITION_COLOR)

	if socket0:
		item.SelectItem(socket0)
		toolTip.AppendSpace(5)
		toolTip.AppendTextLine(TOOLTIP_FROM % item.GetItemName(), TOOLTIP_COLOR)
		lines = []
		for i in xrange(item.ITEM_APPLY_MAX_NUM):
			(affectType, affectValue) = item.GetAffect(i)
			if affectType and affectType != _MoveSpeed():
				lines.append((affectType, affectValue))
		try:
			lines += [line for line in __import__('uitooltip').GetItemExtraApplies(socket0) if line[0] != _MoveSpeed()]
		except Exception:
			pass
		if item.GetItemType() == item.ITEM_TYPE_ARMOR and item.GetItemSubType() == item.ARMOR_SHIELD:
			defGrade = Drain(item.GetValue(1) + item.GetValue(5) * 2, level)
			if defGrade > 0:
				toolTip.AppendTextLine(localeInfo.TOOLTIP_ITEM_DEF_GRADE % defGrade, toolTip.POSITIVE_COLOR)
		for (affectType, affectValue) in lines:
			value = Drain(affectValue, level)
			text = localeInfo.GetApplyString(affectType, value)
			if text and value > 0:
				toolTip.AppendTextLine(text, toolTip.POSITIVE_COLOR)
		for attr in (attrSlot or []):
			try:
				(attrType, attrValue) = attr
			except (TypeError, ValueError):
				continue
			value = Drain(attrValue, level)
			text = attrType and localeInfo.GetApplyString(attrType, value)
			if text and value > 0:
				toolTip.AppendTextLine(text, toolTip.SPECIAL_POSITIVE_COLOR)
	else:
		toolTip.AppendSpace(5)
		toolTip.AppendTextLine(TOOLTIP_NONE, TOOLTIP_COLOR)
		toolTip.AppendTextLine(TOOLTIP_WHERE, TOOLTIP_COLOR)
	item.SelectItem(itemVnum)


# ---- what the others wear ("AURA view") ------------------------------------------------------------------------------
_effects = {'registered': False}


def _RegisterEffects():
	if _effects['registered']:
		return True
	try:
		import chrmgr
		if not hasattr(chrmgr, 'SetAura'):
			return False
		for (vnum, path) in EFFECTS.items():
			chrmgr.RegisterAuraEffect(vnum, path)
	except Exception:
		return False
	_effects['registered'] = True
	return True


def OnView(vid, vnum):
	"""An outfit worn by a character in view (0: none); with "Ukryj cudze" on, the others' are not drawn."""
	try:
		vid = int(vid)
		vnum = int(vnum)
	except (TypeError, ValueError):
		return
	if not _RegisterEffects():
		return
	try:
		import uicostumehide
		if vnum and vid != player.GetMainCharacterIndex() and uicostumehide._state.get('others'):
			vnum = 0
	except Exception:
		pass
	try:
		import chrmgr
		chrmgr.SetAura(vid, vnum)
	except Exception:
		pass


# ---- the window -------------------------------------------------------------------------------------------------------
class AuraWindow(ui.ScriptWindow):

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.loadedType = -1
		self.type = TYPE_ABSORB
		self.items = {}  # slot -> (cell, vnum, count)
		self.toolTipItem = None
		self.question = None
		self.startPos = (0, 0)
		self.texts = []

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def Destroy(self):
		self.question = None
		self.toolTipItem = None
		self.texts = []
		self.ClearDictionary()
		self.loadedType = -1

	def __Load(self, type):
		if self.loadedType >= 0:
			return SCRIPT[self.loadedType] == SCRIPT[type]	# another layout: OnCommand makes a new window
		try:
			ui.PythonScriptLoader().LoadScriptFile(self, SCRIPT[type])
			self.wndItem = self.GetChild('AuraSlot')
			self.titleName = self.GetChild('TitleName')
			self.GetChild('TitleBar').SetCloseEvent(ui.__mem_func__(self.Close))
			self.GetChild('AcceptButton').SetEvent(ui.__mem_func__(self.__Accept))
			self.GetChild('CancelButton').SetEvent(ui.__mem_func__(self.Close))
		except Exception, e:
			import dbg
			dbg.TraceError('AuraWindow.Load: %s' % str(e))
			self.ClearDictionary()	# MT2009_PLUS_AURA_UI_PATH_V1: no half-loaded children kept for the next try
			return False

		self.wndItem.SetSelectEmptySlotEvent(ui.__mem_func__(self.__DropOnSlot))
		self.wndItem.SetSelectItemSlotEvent(ui.__mem_func__(self.__TakeOut))
		self.wndItem.SetUnselectItemSlotEvent(ui.__mem_func__(self.__TakeOut))
		self.wndItem.SetUseSlotEvent(ui.__mem_func__(self.__TakeOut))
		self.wndItem.SetOverInItemEvent(ui.__mem_func__(self.__OverIn))
		self.wndItem.SetOverOutItemEvent(ui.__mem_func__(self.__OverOut))
		self.loadedType = type
		return True

	def SetItemToolTip(self, toolTip):
		self.toolTipItem = toolTip

	def Open(self, type):
		if type not in SCRIPT:
			type = TYPE_ABSORB
		if self.IsShow():
			self.Hide()
		if not self.__Load(type):
			return
		self.type = type
		self.texts = []
		if type != TYPE_ABSORB:
			self.texts = [self.GetChild('AuraToolTip%d' % i) for i in xrange(1, 7)]
		self.items = {}
		self.titleName.SetText(TITLE[type])
		(x, y, z) = player.GetMainCharacterPosition()
		self.startPos = (x, y)
		self.Refresh()
		self.SetCenterPosition()
		self.Show()
		self.SetTop()

	def Close(self):
		if self.question:
			self.question.Close()
			self.question = None
		if self.IsShow():
			net.SendChatPacket('/aura cancel')
		self.items = {}
		self.Hide()
		if self.toolTipItem:
			self.toolTipItem.HideToolTip()

	def ServerClose(self):
		self.items = {}
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def OnUpdate(self):
		(x, y, z) = player.GetMainCharacterPosition()
		if abs(x - self.startPos[0]) > LIMIT_RANGE or abs(y - self.startPos[1]) > LIMIT_RANGE:
			self.Close()

	# ---- the server -------------------------------------------------------------------------------------------------
	def SetSlot(self, slot, cell, vnum, count, window=None):
		if window is None:
			window = player.INVENTORY
		self.items[slot] = (cell, vnum, count, window)
		self.Refresh()

	def __Count(self, slot):
		"""MT2009_PLUS_AURA_RUNE_STACK_V1: the stack's count now (a pickup may have joined it), the server's otherwise."""
		(cell, vnum, count, window) = self.items[slot]
		try:
			if player.GetItemIndex(window, cell) == vnum:
				return max(1, int(player.GetItemCount(window, cell)))
		except Exception:
			pass
		return count

	def DelSlot(self, slot):
		if slot in self.items:
			del self.items[slot]
		self.Refresh()

	def __MainState(self):
		(cell, vnum, count, window) = self.items[SLOT_MAIN]
		return (vnum,) + Decode(vnum, player.GetItemMetinSocket(cell, SOCKET_LEVEL))

	def Refresh(self):
		if self.loadedType < 0:
			return
		for slot in (SLOT_MAIN, SLOT_SUB, SLOT_RESULT):
			self.wndItem.ClearSlot(slot)
		for slot in self.items.keys():
			count = self.__Count(slot)
			self.wndItem.SetItemSlot(slot, self.items[slot][1], count if count > 1 else 0)
		if self.type == TYPE_ABSORB and SLOT_MAIN in self.items and SLOT_SUB in self.items:
			self.wndItem.SetItemSlot(SLOT_RESULT, self.items[SLOT_MAIN][1], 0)
		for text in self.texts:
			text.SetText('')
		if self.texts and SLOT_MAIN in self.items:
			if self.type == TYPE_GROWTH:
				self.__RefreshGrowth()
			else:
				self.__RefreshEvolve()
		self.wndItem.RefreshSlot()

	def __Lines(self, lines):
		for (text, line) in zip(self.texts, lines):
			text.SetText(line)

	def __RefreshGrowth(self):
		(vnum, level, exp) = self.__MainState()
		grade = Grade(vnum)
		lines = [TEXT_NOW, TEXT_LEVEL % (level, GRADE_NAMES[grade], level / 10.0), TEXT_EXP % ExpPct(vnum, level, exp)]
		if SLOT_SUB in self.items:
			rune = self.items[SLOT_SUB][1]
			count = self.__Count(SLOT_SUB)
			(used, level2, exp2) = Grow(vnum, level, exp, count, RUNE_EXP.get(rune, 0))
			lines += [TEXT_AFTER % (used, count), TEXT_LEVEL % (level2, GRADE_NAMES[grade], level2 / 10.0),
				TEXT_READY if IsFull(vnum, level2, exp2) and grade < 5 else TEXT_EXP % ExpPct(vnum, level2, exp2)]
		self.__Lines(lines)

	def __RefreshEvolve(self):
		(vnum, level, exp) = self.__MainState()
		grade = Grade(vnum)
		if grade >= 5:
			return
		(lo, hi, need, material, materialCount, gold) = GRADES[grade]
		self.__Lines([TEXT_EVOLVED, TEXT_LEVEL % (level + 1, GRADE_NAMES[grade + 1], (level + 1) / 10.0), TEXT_CHANCE,
			TEXT_NEED, TEXT_MATERIAL % (ItemName(material), materialCount, player.GetItemCountByVnum(material)),
			TEXT_COST % Money(gold)])

	# ---- the player -------------------------------------------------------------------------------------------------
	def __AttachedBagCell(self):
		"""(window, cell) of the item on the cursor - the bag or (MT2009_PLUS_AURA_RUNE_STACK_V1) a Dodatkowy
		ekwipunek storage; (-1, -1) otherwise."""
		if not mouseModule.mouseController.isAttached():
			return (-1, -1)
		attachedType = mouseModule.mouseController.GetAttachedType()
		cell = mouseModule.mouseController.GetAttachedSlotNumber()
		window = _StorageWindowOfSlotType(attachedType)
		mouseModule.mouseController.DeattachObject()
		if attachedType == player.SLOT_TYPE_INVENTORY:
			if cell >= getattr(player, 'EQUIPMENT_SLOT_START', 1 << 16):
				chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_NOT_BAG)
				return (-1, -1)
			return (player.INVENTORY, cell)
		if window >= 0:
			return (window, cell)
		chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_NOT_BAG)
		return (-1, -1)

	def __DropOnSlot(self, slot):
		if slot == SLOT_RESULT:
			mouseModule.mouseController.DeattachObject()
			return
		(window, cell) = self.__AttachedBagCell()
		if cell < 0:
			return
		self.PutItem(slot, window, cell)

	def PutItem(self, slot, window, cell):
		"""Ask the server to put the item of (window, cell) into `slot` (a drop or a right click)."""
		if slot == SLOT_SUB and SLOT_MAIN not in self.items:
			chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_PUT_MAIN)
			return
		snd.PlaySound('sound/ui/drop.wav')
		if window == player.INVENTORY:
			net.SendChatPacket('/aura in %d %d' % (slot, cell))
		else:
			net.SendChatPacket('/aura in %d %d %d' % (slot, cell, window))

	def TakeItem(self, window, cell):
		"""MT2009_PLUS_AURA_RUNE_STACK_V1 (the owner, 10 November 2026): a right click on an item of the bag or of a
		storage with this window open - an outfit goes into the left slot, anything else (the jewel, the runes - the
		whole stack -, the material) into the right one; the server checks it as a drop. True: the click is taken."""
		if not self.IsShow() or self.loadedType < 0:
			return False
		vnum = player.GetItemIndex(window, cell)
		if not vnum:
			return True
		slot = SLOT_MAIN if IsAuraVnum(vnum) else SLOT_SUB
		if slot in self.items:
			(oldCell, oldVnum, x, oldWindow) = self.items[slot]
			if (oldCell, oldWindow) == (cell, window):
				return True
			if slot == SLOT_SUB or SLOT_SUB not in self.items:
				net.SendChatPacket('/aura out %d' % slot)	# a swap: the old item out first (an outfit only with the right slot empty)
			else:
				chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_SLOT_TAKEN)
				return True
		self.PutItem(slot, window, cell)
		return True

	def __TakeOut(self, slot):
		if mouseModule.mouseController.isAttached():
			self.__DropOnSlot(slot)
			return
		if slot in self.items and slot != SLOT_RESULT:
			snd.PlaySound('sound/ui/pick.wav')
			net.SendChatPacket('/aura out %d' % slot)

	def __OverIn(self, slot):
		if not self.toolTipItem:
			return
		if slot == SLOT_RESULT:
			self.__ResultToolTip()
		elif slot in self.items:
			(cell, vnum, count, window) = self.items[slot]
			self.toolTipItem.SetInventoryItem(cell, window)

	def __ResultToolTip(self):
		"""The outfit as it will be: the right item's vnum and bonuses on it."""
		if SLOT_MAIN not in self.items or SLOT_SUB not in self.items:
			return
		(mainCell, mainVnum, x, y) = self.items[SLOT_MAIN]
		(subCell, subVnum, x, y) = self.items[SLOT_SUB]
		toolTip = self.toolTipItem
		toolTip.ClearToolTip()
		item.SelectItem(mainVnum)
		toolTip.SetTitle(item.GetItemName())
		metinSlot = [subVnum, player.GetItemMetinSocket(mainCell, SOCKET_LEVEL), 0]
		attrSlot = [player.GetItemAttribute(subCell, i) for i in xrange(player.ATTRIBUTE_SLOT_MAX_NUM)]
		AppendToolTip(toolTip, mainVnum, metinSlot, attrSlot)
		toolTip.ShowToolTip()

	def __OverOut(self):
		if self.toolTipItem:
			self.toolTipItem.HideToolTip()

	def __Accept(self):
		if SLOT_MAIN not in self.items or SLOT_SUB not in self.items:
			chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_PUT_BOTH)
			return
		text = None
		if self.type == TYPE_ABSORB:
			text = TEXT_QUESTION_ABSORB
		elif self.type == TYPE_EVOLVE:
			grade = Grade(self.items[SLOT_MAIN][1])
			text = TEXT_QUESTION_EVOLVE % Money(GRADES[grade][5])
		elif self.type == TYPE_GROWTH:
			# MT2009_PLUS_AURA_RUNE_STACK_V1: the whole stack in one go - say how many runes and which level
			(vnum, level, exp) = self.__MainState()
			count = self.__Count(SLOT_SUB)
			(used, level2, exp2) = Grow(vnum, level, exp, count, RUNE_EXP.get(self.items[SLOT_SUB][1], 0))
			if used <= 0:
				chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_GROWTH_NOTHING)
				return
			if used < count and IsFull(vnum, level2, exp2):
				text = TEXT_QUESTION_GROWTH_TOP % (used, count, level, level2)
			else:
				text = TEXT_QUESTION_GROWTH % (used, count, level, level2)
		if not text:
			net.SendChatPacket('/aura accept')
			return
		question = uiCommon.QuestionDialog()
		question.SetText(text)
		question.SetAcceptEvent(ui.__mem_func__(self.__AcceptYes))
		question.SetCancelEvent(ui.__mem_func__(self.__AcceptNo))
		question.Open()
		self.question = question

	def __AcceptYes(self):
		if self.question:
			self.question.Close()
			self.question = None
		net.SendChatPacket('/aura accept')

	def __AcceptNo(self):
		if self.question:
			self.question.Close()
			self.question = None


_window = {'wnd': None}


def _StorageWindowOfSlotType(slotType):
	"""The Dodatkowy ekwipunek storage window of a slot type (uiekwipunek.py), -1 for none."""
	try:
		return __import__('uiekwipunek').WindowOfSlotType(slotType)
	except Exception:
		return -1


def IsOpen():
	wnd = _window['wnd']
	try:
		return bool(wnd and wnd.loadedType >= 0 and wnd.IsShow())
	except Exception:
		return False


def TakeItem(window, cell):
	"""MT2009_PLUS_AURA_RUNE_STACK_V1: uiinventory.py UseItemSlot / uiekwipunek.py QuickAdd (a right click) - with
	the aura window open the item goes into it. True when taken (only while the window is open)."""
	if not IsOpen():
		return False
	try:
		return bool(_window['wnd'].TakeItem(window, cell))
	except Exception:
		import dbg
		import sys
		dbg.TraceError('uiaura.TakeItem: %s %s' % (sys.exc_info()[0], sys.exc_info()[1]))
		return False


def TakeInventoryItem(cell):
	"""uiinventory.py UseItemSlot: a right click on a bag item."""
	return TakeItem(player.INVENTORY, cell)


def QuickHint():
	"""The tooltip's hint line of a storage item while a right click puts it into the aura window."""
	return TEXT_QUICK_AURA if IsOpen() else ''


def GetWindow(toolTip=None):
	if not _window['wnd']:
		_window['wnd'] = AuraWindow()
	if toolTip:
		_window['wnd'].SetItemToolTip(toolTip)
	return _window['wnd']


def DestroyWindow():
	wnd = _window['wnd']
	_window['wnd'] = None
	if wnd:
		try:
			wnd.Hide()
			wnd.Destroy()
		except Exception:
			pass


def _Int(value, default=0):
	try:
		return int(value)
	except (TypeError, ValueError):
		return default


def OnCommand(toolTip, *args):
	"""game.py: "AURA <what> ..." from the server."""
	if not args:
		return
	what = args[0]
	rest = args[1:]
	if what == 'view' and len(rest) >= 2:
		OnView(rest[0], rest[1])
	elif what == 'open':
		type = _Int(rest[0] if rest else 0)
		if type not in SCRIPT:
			type = TYPE_ABSORB
		wnd = _window['wnd']
		if wnd and wnd.loadedType >= 0 and SCRIPT[wnd.loadedType] != SCRIPT[type]:
			DestroyWindow()	# the absorb and the level-up windows are two layouts
		GetWindow(toolTip).Open(type)
	elif what == 'set' and len(rest) >= 3:
		wnd = _window['wnd']
		if wnd:
			window = _Int(rest[4], player.INVENTORY) if len(rest) > 4 else player.INVENTORY
			wnd.SetSlot(_Int(rest[0]), _Int(rest[1]), _Int(rest[2]), _Int(rest[3] if len(rest) > 3 else 1, 1), window)
	elif what == 'del' and rest:
		wnd = _window['wnd']
		if wnd:
			wnd.DelSlot(_Int(rest[0]))
	elif what == 'close':
		wnd = _window['wnd']
		if wnd:
			wnd.ServerClose()
	elif what == 'done':
		wnd = _window['wnd']
		if wnd:
			wnd.Refresh()
