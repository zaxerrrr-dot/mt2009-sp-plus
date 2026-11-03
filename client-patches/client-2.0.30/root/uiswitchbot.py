# MT2009_PLUS_SWITCHBOT_V1: Bonus Switcher - Ameria Project's switchbot window
# (tools/FoxFSArchiver/source/root/uiswitchbot.py, with its d:/ymir work/ui/
# switchbot graphics), replacing our "Zmiana bonusow" (uibonusswitch.py,
# MT2009_PLUS_BONUS_SWITCH_V1 - removed). The owner, 21 October 2026: "Zamien
# bonus switcher z naszej wersji na ten z Amerii, zastosuj nowy kod po stronie
# serwera jak i klienta".
#
# Needs the 3.0 exe with ENABLE_SWITCHBOT (client-patches/exe: the module
# "switchbot", player.SWITCHBOT, player.SLOT_TYPE_SWITCHBOT, packets 170/171);
# the server's side is playerbot_switchbot.cpp (server-patches/switchbot).
# Without the module the window says so and nothing is sent - the server would
# answer an old exe with a packet it does not know.
#
# Ameria's window as it is: five item tabs at the top (drag a weapon or an
# armour from the bag onto a tab; the item stays in the bag, locked), the
# selected tab's alternatives (all five - Ameria's premium ones open for everyone,
# MT2009_PLUS_SWITCHBOT_PREMIUM_V1) and five bonus rows (search a bonus the item can get, its
# minimum - the maximum the item can roll by default), Start / Stop, the saved
# sets (a list beside the window). The server changes the bonuses every 0.2 s
# with Zaczarowanie Przedmiotu (39028, 71084, 76014, 71151) until one
# alternative is reached.
# Ours: Polish texts (CP1250); a click on a tab's item (or its right click, as in
# Ameria) takes it out - Ameria put it on the cursor first; the saved sets in
# autohunt/switchbot.cfg (Ameria: a pickle, switchbot.pkl); the bonus names of
# localeinfo_point (the tooltip's); a right click on a weapon / armour in the bag
# with the window open puts it into the selected tab, as our old window did
# (uiinventory.py); the window opens by the inventory side bar's button and the
# "bonus_switch" key (keybind.py), as the old one.
#
# MT2009_PLUS_SWITCHBOT_GLOVE_TALISMAN_V1 / MT2009_PLUS_SWITCHBOT_COSTUME_V1 (the
# owner's list of 3 November 2026): talismans and gloves too (the same
# Zaczarowanie Przedmiotu as by hand), and costumes, hairstyles and weapon skins
# with 70064 Zaczaruj kostium only (as by hand); the line under Start / Stop says
# which item the selected tab's item uses up. The exe's switchbot.GetAttributesForSet
# knows their bonus sets (client-patches/exe PythonSwitchbot.cpp, same round).
#
# Python 2.7 as the client has it.

import app
import chat
import grp
import item
import net
import player
import ui
import wndMgr
import mouseModule
import localeInfo
import localeinfo_point

try:
	import switchbot
except ImportError:
	switchbot = None

import os

COLOR_INACTIVE = grp.GenerateColor(1.0, 0.0, 0.0, 0.2)
COLOR_ACTIVE   = grp.GenerateColor(1.0, 0.6, 0.1, 0.2)
COLOR_FINISHED = grp.GenerateColor(0.0, 1.0, 0.0, 0.2)
COLOR_SELECTED = grp.GenerateColor(1.0, 1.0, 1.0, 1.0)

IMG = "d:/ymir work/ui/switchbot/"

SKILL_DAMAGE_BONUS_MAX = 20
NORMAL_HIT_DAMAGE_BONUS_MAX = 50
ADDON_TYPES = {
	getattr(player, "POINT_SKILL_DAMAGE_BONUS", 121): SKILL_DAMAGE_BONUS_MAX,
	getattr(player, "POINT_NORMAL_HIT_DAMAGE_BONUS", 122): NORMAL_HIT_DAMAGE_BONUS_MAX,
}

SLOT_COUNT = switchbot.SLOT_COUNT if switchbot else 5
ALTERNATIVE_COUNT = switchbot.ALTERNATIVE_COUNT if switchbot else 5

# MT2009_PLUS_SWITCHBOT_PREMIUM_V1 (the owner, 21 Oct 2026: "odblokuj premium dla wszystkich bez dodatkowego
# przedmiotu"): every alternative of Ameria's premium switchbot (3-5 too) for everyone - the server takes all five.
VISIBLE_ALTERNATIVES = ALTERNATIVE_COUNT

BOARD_WIDTH = 400
INPUT_HEIGHT = 27

BORDER_SPACE = 8
BORDER_SPACE_TOP = 30

ITEM_TAB_NAME_BOX_HEIGHT = 20
ITEM_TAB_SPACE = 2
ITEM_TAB_WIDTH = (BOARD_WIDTH - BORDER_SPACE * 2) / SLOT_COUNT + 1 - ITEM_TAB_SPACE

TOP_PANEL_HEIGHT = (BORDER_SPACE * 2) + (3 * 32) + ITEM_TAB_NAME_BOX_HEIGHT
TOP_PANEL_WIDTH = BOARD_WIDTH - (BORDER_SPACE * 2)

MAIN_PANEL_WIDTH = BOARD_WIDTH - BORDER_SPACE * 2
MAIN_PANEL_HEIGHT = INPUT_HEIGHT * 6 #1 AlternativeRow 5 Attribute

# MT2009_PLUS_SWITCHBOT_COSTUME_V1: 18 px more for the line of the item used up
BOT_PANEL_HEIGHT = 58
BOT_PANEL_BUTTON_Y = -8
BOT_PANEL_WIDTH = BOARD_WIDTH - BORDER_SPACE * 2

ATTR_SLOT_COUNT = 5

BOARD_HEIGHT = BORDER_SPACE_TOP + TOP_PANEL_HEIGHT + MAIN_PANEL_HEIGHT + BOT_PANEL_HEIGHT + BORDER_SPACE

# CP1250
TEXT_TITLE = "Switchbot - zmiana bonus\xf3w"
TEXT_EMPTY_ATTR = "Wybierz bonus"
TEXT_CLEAR_ATTR = "Usu\xf1"
TEXT_SAVE_BUTTON = "Zapisane zestawy"
TEXT_START = "Start"
TEXT_STOP = "Stop"
TEXT_SELECT_ATTR = "Bonusy"
TEXT_ALTERNATIVES = "Warianty:"
TEXT_CONFIGURATION_TITLE = "Zapisane bonusy"
TEXT_LOAD_CONFIGURATION = "U\xbfyj"
TEXT_CLEAR_CONFIGURATION = "Usu\xf1"
TEXT_SAVE = "Zapisz"
TEXT_ACCEPT = getattr(localeInfo, "UI_ACCEPT", "Akceptuj")
TEXT_CANCEL = getattr(localeInfo, "UI_CANCEL", "Anuluj")
TEXT_NEEDS_EXE = "Switchbot wymaga nowego klienta (exe 3.0)."
TEXT_SEARCH_TOOLTIP = "Szukaj bonusu"
TEXT_COST_COSTUME = "Zu\xbfywa: Zaczaruj kostium"
TEXT_COST_NORMAL = "Zu\xbfywa: Zaczarowanie Przedmiotu"

# MT2009_PLUS_SWITCHBOT_COSTUME_V1: what the server's switchbot takes (playerbot_switchbot.cpp
# SwitchbotHelper::IsValidItem) - a costume, a hairstyle, a weapon skin (changed with 70064)
SWITCHBOT_COSTUME_SUBTYPES = [getattr(item, name) for name in ("COSTUME_TYPE_BODY", "COSTUME_TYPE_HAIR", "COSTUME_TYPE_WEAPON") if hasattr(item, name)]


def IsCostumeItem(vnum):
	if not vnum:
		return False
	item.SelectItem(vnum)
	return item.GetItemType() == getattr(item, "ITEM_TYPE_COSTUME", 28) and item.GetItemSubType() in SWITCHBOT_COSTUME_SUBTYPES

CONFIG_FILE = os.path.join("autohunt", "switchbot.cfg")


def IsSupported():
	return switchbot is not None and hasattr(player, "SWITCHBOT") and hasattr(player, "SLOT_TYPE_SWITCHBOT")


def GetAffectString(affectType, affectValue):
	if not affectType:
		return None

	try:
		text = localeinfo_point.GetApplyString(affectType, affectValue)
		if text:
			return text
	except Exception:
		pass
	return "Bonus %d: %d" % (affectType, affectValue)


def _QuestionDialogOpen():
	try:
		import constInfo
		return constInfo.GET_ITEM_QUESTION_DIALOG_STATUS() == 1
	except Exception:
		return False


def _ListItems(listBox):
	getter = getattr(listBox, "GetItems", None)
	if getter:
		return getter()
	return getattr(listBox, "itemList", [])


class SwitchbotItemTab(ui.ThinBoardCircle):
	def __init__(self, slot_num):
		ui.ThinBoardCircle.__init__(self)

		self.slot_num = slot_num

		self.__Initialize()
		self.__LoadItemTab()
		self.__BindEvents()

	def __del__(self):
		ui.ThinBoardCircle.__del__(self)

	def __Initialize(self):
		self.tooltipItem = None
		self.onSelectEvent = None

		self.statusBar = None
		self.itemSlot = None
		self.selectButton = None
		self.selectBox = None

		self.lastSelectAlpha = 255
		self.lastSelectAlphaDir = 1

	def __LoadItemTab(self):
		self.SetSize(ITEM_TAB_WIDTH, TOP_PANEL_HEIGHT)

		self.statusBar = ui.Bar()
		self.statusBar.SetParent(self)
		self.statusBar.SetSize(ITEM_TAB_WIDTH - 4, TOP_PANEL_HEIGHT - 4)
		self.statusBar.SetPosition(2, 2)

		self.selectBox = ui.Box()
		self.selectBox.SetParent(self)
		self.selectBox.SetPosition(1, 1)
		self.selectBox.SetSize(ITEM_TAB_WIDTH - 2, TOP_PANEL_HEIGHT - 2)
		self.selectBox.SetColor(COLOR_SELECTED)

		self.selectButton = ui.RadioButton()
		self.selectButton.SetParent(self)
		self.selectButton.SetUpVisual(IMG + "btn_small_01.sub")
		self.selectButton.SetOverVisual(IMG + "btn_small_02.sub")
		self.selectButton.SetDownVisual(IMG + "btn_small_03.sub")
		self.selectButton.SetDisableVisual(IMG + "btn_small_01.sub")
		self.selectButton.SetWindowHorizontalAlignCenter()
		self.selectButton.SetPosition(0, 5)
		self.selectButton.SetText(str(self.slot_num+1))
		self.selectButton.Show()

		self.itemSlot = ui.GridSlotWindow()
		self.itemSlot.SetParent(self)
		self.itemSlot.ArrangeSlot(0, 1, 3, 32, 32, 0, 0)
		self.itemSlot.SetSlotBaseImage("d:/ymir work/ui/public/slot_base.sub", 1.0, 1.0, 1.0, 1.0)
		self.itemSlot.SetWindowHorizontalAlignCenter()
		self.itemSlot.SetPosition(0, 30)
		self.itemSlot.Show()

	def __BindEvents(self):
		self.itemSlot.SetOverInItemEvent(ui.__mem_func__(self.OverInItem))
		self.itemSlot.SetOverOutItemEvent(ui.__mem_func__(self.OverOutItem))
		self.itemSlot.SetSelectEmptySlotEvent(ui.__mem_func__(self.SelectEmptySlot))
		self.itemSlot.SetSelectItemSlotEvent(ui.__mem_func__(self.SelectItemSlot))
		self.itemSlot.SetUnselectItemSlotEvent(ui.__mem_func__(self.UseItemSlot))
		self.itemSlot.SetUseSlotEvent(ui.__mem_func__(self.UseItemSlot))

		self.selectButton.SetEvent(ui.__mem_func__(self.__OnSelectButtonClick))

	def Destroy(self):
		self.__Initialize()

	def SetItemToolTip(self, tooltipItem):
		self.tooltipItem = tooltipItem

	def OnPlacedItem(self, slot_num):
		pass

	def OverOutItem(self):
		self.itemSlot.SetUsableItem(False)
		if self.tooltipItem:
			self.tooltipItem.HideToolTip()

	def OverInItem(self, overSlotPos):
		self.itemSlot.SetUsableItem(True)

		if self.IsEmpty() or not self.tooltipItem:
			return

		self.tooltipItem.ClearToolTip()

		itemVnum = player.GetItemIndex(player.SWITCHBOT, self.slot_num)
		metinSlot = [player.GetItemMetinSocket(player.SWITCHBOT, self.slot_num, i) for i in xrange(player.METIN_SOCKET_MAX_NUM)]
		attrSlot = [player.GetItemAttribute(player.SWITCHBOT, self.slot_num, i) for i in xrange(player.ATTRIBUTE_SLOT_MAX_NUM)]

		self.tooltipItem.AddItemData(itemVnum, metinSlot, attrSlot)
		self.tooltipItem.ShowToolTip()

	def SelectEmptySlot(self, selectedSlotPos):
		if _QuestionDialogOpen():
			return

		if mouseModule.mouseController.isAttached():

			attachedSlotType = mouseModule.mouseController.GetAttachedType()
			attachedSlotPos = mouseModule.mouseController.GetAttachedSlotNumber()
			attachedItemCount = mouseModule.mouseController.GetAttachedItemCount()

			if player.SLOT_TYPE_INVENTORY == attachedSlotType:
				net.SendItemMovePacket(player.INVENTORY, attachedSlotPos, player.SWITCHBOT, self.slot_num, long(attachedItemCount))

			mouseModule.mouseController.DeattachObject()

			self.OnPlacedItem(self.slot_num)

	def SelectItemSlot(self, itemSlotIndex):
		if _QuestionDialogOpen():
			return

		if switchbot.IsActive(self.slot_num):
			return

		if mouseModule.mouseController.isAttached():
			mouseModule.mouseController.DeattachObject()
		else:
			# Ameria put the item on the cursor (dropped in the bag = taken out); here a click takes it out
			self.UseItemSlot(itemSlotIndex)

	def UseItemSlot(self, slotIndex):
		curCursorNum = app.GetCursor()
		if app.SELL == curCursorNum:
			return

		if _QuestionDialogOpen():
			return

		if switchbot.IsActive(self.slot_num):
			return

		net.SendItemUsePacket(player.SWITCHBOT, self.slot_num)
		mouseModule.mouseController.DeattachObject()
		self.OverOutItem()

	def RefreshItemSlot(self):
		if self.IsEmpty():
			switchbot.ClearSlot(self.slot_num)
			self.itemSlot.ClearSlot(0)
			self.statusBar.Hide()
		else:
			itemCount = player.GetItemCount(player.SWITCHBOT, self.slot_num)
			itemVnum = player.GetItemIndex(player.SWITCHBOT, self.slot_num)
			if itemCount == 1:
				itemCount = 0

			self.itemSlot.SetItemSlot(0, itemVnum, itemCount)

			self.statusBar.Show()
			if self.IsActive():
				self.itemSlot.ActivateSlot(0)
				self.statusBar.SetColor(COLOR_ACTIVE)
			else:
				self.itemSlot.DeactivateSlot(0)

				if self.IsFinished():
					self.statusBar.SetColor(COLOR_FINISHED)
				else:
					self.statusBar.SetColor(COLOR_INACTIVE)

		self.itemSlot.RefreshSlot()

	def IsEmpty(self):
		itemVnum = player.GetItemIndex(player.SWITCHBOT, self.slot_num)
		return not itemVnum

	def IsActive(self):
		return switchbot.IsActive(self.slot_num)

	def IsFinished(self):
		return switchbot.IsFinished(self.slot_num)

	def GetSlotNum(self):
		return self.slot_num

	def SetOnSelectEvent(self, event):
		self.onSelectEvent = event

	def __OnSelectButtonClick(self):
		if self.onSelectEvent:
			self.onSelectEvent(self.slot_num)

	def SetUp(self):
		if self.selectButton:
			self.selectButton.SetUp()
			self.selectBox.Hide()

	def Down(self):
		if self.selectButton:
			self.selectButton.Down()

			self.lastSelectAlpha = 255
			self.selectBox.Show()

	def OnUpdate(self):
		if self.selectBox and self.selectBox.IsShow():
			rate = 3

			self.lastSelectAlpha -= (rate * self.lastSelectAlphaDir)

			if self.lastSelectAlpha <= 0:
				self.lastSelectAlpha = 0
				self.lastSelectAlphaDir = -1
			elif self.lastSelectAlpha >= 255:
				self.lastSelectAlpha = 255
				self.lastSelectAlphaDir = 1

			self.selectBox.SetColor(grp.GenerateColor(1.0, 1.0, 1.0, float(self.lastSelectAlpha) / 255.0))


class SwitchbotAttribute(ui.Window):
	VALUE_WIDTH = 50

	def __init__(self):
		ui.Window.__init__(self)
		self.__Initialize()

	def __del__(self):
		ui.Window.__del__(self)

	def __Initialize(self):
		self.selectedSlot = -1
		self.alternative = 0
		self.index = -1

		self.attributeType = 0
		self.attributeValue = 0

		self.searchEvent = None
		self.attributeUpdateEvent = None
		self.escapeEvent = None
		self.attributeMaxValue = 0

		self.typeInput = None
		self.typeTextLine = None
		self.searchTypeButton = None
		self.deleteAttributeButton = None
		self.valueInput = None
		self.valueEditLine = None

	def Create(self, width, index):
		self.index = index
		self.SetSize(width, INPUT_HEIGHT)

		self.typeInput = ui.ThinBoardCircle()
		self.typeInput.SetParent(self)
		self.typeInput.SetSize(width - self.VALUE_WIDTH, INPUT_HEIGHT)
		self.typeInput.SetPosition(0, 0)
		self.typeInput.Show()

		self.typeTextLine = ui.TextLine()
		self.typeTextLine.SetParent(self.typeInput)
		self.typeTextLine.SetText(TEXT_EMPTY_ATTR)
		self.typeTextLine.SetVerticalAlignCenter()
		self.typeTextLine.SetWindowVerticalAlignCenter()
		self.typeTextLine.SetHorizontalAlignCenter()
		self.typeTextLine.SetWindowHorizontalAlignCenter()
		self.typeTextLine.SetPosition(-20, -1)
		self.typeTextLine.Show()

		self.searchTypeButton = ui.Button()
		self.searchTypeButton.SetParent(self.typeInput)
		self.searchTypeButton.SetUpVisual(IMG + "search_attr_01.sub")
		self.searchTypeButton.SetOverVisual(IMG + "search_attr_02.sub")
		self.searchTypeButton.SetDownVisual(IMG + "search_attr_03.sub")
		self.searchTypeButton.SetDisableVisual(IMG + "search_attr_03.sub")
		self.searchTypeButton.SetWindowHorizontalAlignRight()
		self.searchTypeButton.SetWindowVerticalAlignCenter()
		self.searchTypeButton.SetPosition(24 * 2 + 2, 1)
		self.searchTypeButton.SetToolTipText(TEXT_SEARCH_TOOLTIP)
		self.searchTypeButton.SetEvent(ui.__mem_func__(self.__OnClickSearchButton))
		self.searchTypeButton.Show()

		self.deleteAttributeButton = ui.Button()
		self.deleteAttributeButton.SetParent(self.typeInput)
		self.deleteAttributeButton.SetUpVisual(IMG + "delete_attr_01.sub")
		self.deleteAttributeButton.SetOverVisual(IMG + "delete_attr_02.sub")
		self.deleteAttributeButton.SetDownVisual(IMG + "delete_attr_03.sub")
		self.deleteAttributeButton.SetDisableVisual(IMG + "delete_attr_03.sub")
		self.deleteAttributeButton.SetWindowHorizontalAlignRight()
		self.deleteAttributeButton.SetWindowVerticalAlignCenter()
		self.deleteAttributeButton.SetPosition(24 + 2, 1)
		self.deleteAttributeButton.SetToolTipText(TEXT_CLEAR_ATTR)
		self.deleteAttributeButton.SetEvent(ui.__mem_func__(self.__OnClickClearButton))
		self.deleteAttributeButton.Show()

		self.valueInput = ui.ThinBoardCircle()
		self.valueInput.SetParent(self)
		self.valueInput.SetSize(self.VALUE_WIDTH, INPUT_HEIGHT)
		self.valueInput.SetPosition(width - self.VALUE_WIDTH, 0)
		self.valueInput.Show()

		self.valueEditLine = ui.EditLine()
		self.valueEditLine.SetParent(self.valueInput)
		self.valueEditLine.SetSize(self.VALUE_WIDTH, 18)
		self.valueEditLine.SetMax(4)
		self.valueEditLine.SetNumberMode()
		self.valueEditLine.SetText("0")
		self.valueEditLine.SetPosition(10, 7)
		self.valueEditLine.Show()
		self.valueEditLine.OnIMEUpdate = ui.__mem_func__(self.__OnEditLineIMEUpdate)
		self.valueEditLine.SetEscapeEvent(ui.__mem_func__(self.__OnEscapeEvent))

	def Destroy(self):
		self.__Initialize()

	def Hide(self):
		ui.Window.Hide(self)

		if self.valueEditLine:
			self.valueEditLine.KillFocus()

	def RefreshAttributeRow(self, slot_num, alternative, index):
		self.selectedSlot = slot_num
		self.alternative = alternative
		self.index = index

		if switchbot.IsActive(slot_num):
			self.searchTypeButton.Disable()
			self.deleteAttributeButton.Disable()
			self.valueEditLine.Hide()
		else:
			self.searchTypeButton.Enable()
			self.deleteAttributeButton.Enable()
			self.valueEditLine.Show()

		(type, value) = switchbot.GetAttribute(slot_num, alternative, index)
		if not type:
			self.SetAttribute(TEXT_EMPTY_ATTR, 0)
			return

		affectString = GetAffectString(type, value)
		if not affectString:
			return

		self.SetAttribute(affectString, value)

	def __OnEditLineIMEUpdate(self):
		ui.EditLine.OnIMEUpdate(self.valueEditLine)

		text = self.valueEditLine.GetText()
		if len(text) > 0 and text.isdigit():
			(curType, curValue) = switchbot.GetAttribute(self.selectedSlot, self.alternative, self.index)
			if not curType:
				return

			maxValue = 0
			if not ADDON_TYPES.has_key(curType):
				maxValue = switchbot.GetAttributeMaxValue(self.selectedSlot, curType)

			value = int(text)

			if value == curValue:
				return

			if maxValue != 0 and value > maxValue:
				value = maxValue
				self.valueEditLine.SetText(str(value))

			switchbot.SetAttribute(self.selectedSlot, self.alternative, self.index, curType, value)
			self.typeTextLine.SetText(GetAffectString(curType, value))
			self.__OnAttributeUpdate()

	def SetSearchEvent(self, event):
		self.searchEvent = event

	def __OnClickSearchButton(self):
		if self.searchEvent:
			self.searchEvent(self.index)

	def SetAttributeUpdateEvent(self, event):
		self.attributeUpdateEvent = event

	def __OnAttributeUpdate(self):
		if self.attributeUpdateEvent:
			self.attributeUpdateEvent(self.index)

	def SetEscapeEvent(self, event):
		self.escapeEvent = event

	def __OnEscapeEvent(self):
		if self.escapeEvent:
			self.escapeEvent()

	def __OnClickClearButton(self):
		self.SetAttribute(TEXT_EMPTY_ATTR, 0)
		switchbot.SetAttribute(self.selectedSlot, self.alternative, self.index, 0, 0)
		self.__OnAttributeUpdate()

	def SetAttribute(self, applyname, maxValue):
		self.typeTextLine.SetText(applyname)
		self.valueEditLine.SetText(str(maxValue))

	def GetIndex(self):
		return self.index


class SwitchbotWindow(ui.BoardWithTitleBar):
	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)

		self.__Initialize()
		self.__LoadWindow()
		self.__BindEvents()

	def __del__(self):
		ui.BoardWithTitleBar.__del__(self)

	def __Initialize(self):
		self.selectedSlot = 0
		self.alternative = 0

		self.alternativeButtons = {}
		self.itemTabs = {}
		self.attrDict = {}

		self.attributeSearchWindow = None
		self.attrSearchIdx = -1

		self.configurationSaveWindow = None

		self.topPanel = None
		self.mainPanel = None
		self.botPanel = None
		self.alternativePanel = None

		self.saveButton = None
		self.startButton = None
		self.stopButton = None
		self.costTextLine = None
		self.tooltipItem = None

	def __LoadWindow(self):
		self.AddFlag("movable")
		self.AddFlag("float")
		self.SetSize(BOARD_WIDTH, BOARD_HEIGHT)
		self.SetTitleName(TEXT_TITLE)

		self.topPanel = ui.ThinBoardCircle()
		self.topPanel.SetParent(self)
		self.topPanel.SetSize(TOP_PANEL_WIDTH, TOP_PANEL_HEIGHT)
		self.topPanel.SetPosition(BORDER_SPACE, BORDER_SPACE_TOP)
		self.topPanel.Show()

		for i in xrange(SLOT_COUNT):
			itemTab = SwitchbotItemTab(i)
			itemTab.SetParent(self.topPanel)
			itemTab.SetPosition((ITEM_TAB_WIDTH + ITEM_TAB_SPACE) * i, 0)
			itemTab.SetOnSelectEvent(ui.__mem_func__(self.SelectSlot))
			itemTab.OnPlacedItem = ui.__mem_func__(self.__OnPlacedItem)
			itemTab.Show()

			self.itemTabs[i] = itemTab

		self.mainPanel = ui.ThinBoardCircle()
		self.mainPanel.SetParent(self)
		self.mainPanel.SetSize(MAIN_PANEL_WIDTH, MAIN_PANEL_HEIGHT)
		self.mainPanel.SetPosition(BORDER_SPACE, BORDER_SPACE_TOP + TOP_PANEL_HEIGHT)
		self.mainPanel.Show()

		self.alternativePanel = ui.ThinBoardCircle()
		self.alternativePanel.SetParent(self.mainPanel)
		self.alternativePanel.SetSize(MAIN_PANEL_WIDTH, INPUT_HEIGHT)
		self.alternativePanel.SetPosition(0, 0)
		self.alternativePanel.Show()

		self.alternativeTextLine = ui.TextLine()
		self.alternativeTextLine.SetParent(self.alternativePanel)
		self.alternativeTextLine.SetPosition(5, -1)
		self.alternativeTextLine.SetVerticalAlignCenter()
		self.alternativeTextLine.SetWindowVerticalAlignCenter()
		self.alternativeTextLine.SetText(TEXT_ALTERNATIVES)
		self.alternativeTextLine.Show()

		for i in xrange(ALTERNATIVE_COUNT):
			alternativeButton = ui.RadioButton()
			alternativeButton.SetParent(self.alternativePanel)
			alternativeButton.SetUpVisual(IMG + "btn_small_01.sub")
			alternativeButton.SetOverVisual(IMG + "btn_small_02.sub")
			alternativeButton.SetDownVisual(IMG + "btn_small_03.sub")
			alternativeButton.SetDisableVisual(IMG + "btn_small_03.sub")
			alternativeButton.SetWindowVerticalAlignCenter()
			alternativeButton.SetPosition(80 + alternativeButton.GetWidth() * i, 0)
			alternativeButton.SetText(str(i+1))
			alternativeButton.SetEvent(ui.__mem_func__(self.SelectAlternative), i)

			if i >= VISIBLE_ALTERNATIVES:
				alternativeButton.Hide()
			else:
				alternativeButton.Show()

			self.alternativeButtons[i] = alternativeButton

		for i in xrange(ATTR_SLOT_COUNT):
			attr = SwitchbotAttribute()
			attr.SetParent(self.mainPanel)
			attr.Create(MAIN_PANEL_WIDTH, i)
			attr.SetPosition(0, INPUT_HEIGHT + (INPUT_HEIGHT * i))
			attr.SetSearchEvent(ui.__mem_func__(self.__OnSearchAttribute))
			attr.SetAttributeUpdateEvent(ui.__mem_func__(self.__OnAttributeUpdate))
			attr.SetEscapeEvent(ui.__mem_func__(self.Close))
			attr.Show()

			self.attrDict[i] = attr

		self.botPanel = ui.ThinBoardCircle()
		self.botPanel.SetParent(self)
		self.botPanel.SetSize(BOT_PANEL_WIDTH, BOT_PANEL_HEIGHT)
		self.botPanel.SetPosition(BORDER_SPACE, BORDER_SPACE_TOP + TOP_PANEL_HEIGHT + MAIN_PANEL_HEIGHT)
		self.botPanel.Show()

		self.saveButton = ui.Button()
		self.saveButton.SetParent(self.botPanel)
		self.saveButton.SetUpVisual(IMG + "save_attr_01.sub")
		self.saveButton.SetOverVisual(IMG + "save_attr_02.sub")
		self.saveButton.SetDownVisual(IMG + "save_attr_03.sub")
		self.saveButton.SetDisableVisual(IMG + "save_attr_03.sub")
		self.saveButton.SetWindowVerticalAlignCenter()
		self.saveButton.SetPosition(BORDER_SPACE, BOT_PANEL_BUTTON_Y)
		self.saveButton.SetToolTipText(TEXT_SAVE_BUTTON)
		self.saveButton.Show()

		self.startButton = ui.RadioButton()
		self.startButton.SetParent(self.botPanel)
		self.startButton.SetUpVisual(IMG + "btn_big_01.sub")
		self.startButton.SetOverVisual(IMG + "btn_big_02.sub")
		self.startButton.SetDownVisual(IMG + "btn_big_03.sub")
		self.startButton.SetDisableVisual(IMG + "btn_big_03.sub")
		self.startButton.SetWindowVerticalAlignCenter()
		self.startButton.SetWindowHorizontalAlignCenter()
		self.startButton.SetPosition(-self.startButton.GetWidth() / 2, BOT_PANEL_BUTTON_Y)
		self.startButton.SetText(TEXT_START)
		self.startButton.Show()

		self.stopButton = ui.RadioButton()
		self.stopButton.SetParent(self.botPanel)
		self.stopButton.SetUpVisual(IMG + "btn_big_01.sub")
		self.stopButton.SetOverVisual(IMG + "btn_big_02.sub")
		self.stopButton.SetDownVisual(IMG + "btn_big_03.sub")
		self.stopButton.SetDisableVisual(IMG + "btn_big_03.sub")
		self.stopButton.SetWindowVerticalAlignCenter()
		self.stopButton.SetWindowHorizontalAlignCenter()
		self.stopButton.SetPosition(self.stopButton.GetWidth() / 2 + 20, BOT_PANEL_BUTTON_Y)
		self.stopButton.SetText(TEXT_STOP)
		self.stopButton.Show()

		# MT2009_PLUS_SWITCHBOT_COSTUME_V1: the item the selected tab's item uses up
		self.costTextLine = ui.TextLine()
		self.costTextLine.SetParent(self.botPanel)
		self.costTextLine.SetWindowHorizontalAlignCenter()
		self.costTextLine.SetHorizontalAlignCenter()
		self.costTextLine.SetPosition(0, BOT_PANEL_HEIGHT - 19)
		self.costTextLine.SetText("")
		self.costTextLine.Show()

		try:
			import uiToolTip
			self.tooltipItem = uiToolTip.ItemToolTip()
			self.tooltipItem.HideToolTip()
		except Exception:
			self.tooltipItem = None
		self.SetItemToolTip(self.tooltipItem)

		self.SelectSlot(0)

	def __BindEvents(self):
		self.SetCloseEvent(ui.__mem_func__(self.Close))

		self.startButton.SetEvent(ui.__mem_func__(self.SetActive), True)
		self.stopButton.SetEvent(ui.__mem_func__(self.SetActive), False)
		self.saveButton.SetEvent(ui.__mem_func__(self.OpenSaveConfiguration))

	def Destroy(self):
		if self.attributeSearchWindow:
			self.attributeSearchWindow.Close()
		if self.configurationSaveWindow:
			self.configurationSaveWindow.Close()
			self.configurationSaveWindow.Destroy()
		if self.tooltipItem:
			self.tooltipItem.HideToolTip()
		self.Hide()
		self.__Initialize()

	def Open(self):
		self.Show()
		self.SetTop()
		self.SetCenterPosition()
		self.RefreshSwitchbotWindow()

	def Close(self):
		if self.attributeSearchWindow:
			self.attributeSearchWindow.Close()

		if self.configurationSaveWindow:
			self.configurationSaveWindow.Close()

		if self.tooltipItem:
			self.tooltipItem.HideToolTip()

		self.Hide()
		return True

	def __OnPlacedItem(self, slot_num):
		self.SelectSlot(slot_num)

	def SelectSlot(self, selectedSlot):
		self.itemTabs[self.selectedSlot].SetUp()
		self.selectedSlot = selectedSlot
		self.itemTabs[self.selectedSlot].Down()

		self.SelectAlternative(0)

	def GetSelectedSlot(self):
		return self.selectedSlot

	def SelectAlternative(self, alternative):
		self.alternativeButtons[self.alternative].SetUp()
		self.alternative = alternative
		self.alternativeButtons[self.alternative].Down()

		self.RefreshSwitchbotWindow()

	def SetActive(self, active):
		if self.selectedSlot >= SLOT_COUNT:
			return

		if active and self.IsActiveSlot():
			return

		if not active and not self.IsActiveSlot():
			return

		if active:
			switchbot.Start(self.selectedSlot)
		else:
			switchbot.Stop(self.selectedSlot)

	def OpenSaveConfiguration(self):
		if not self.configurationSaveWindow:
			self.configurationSaveWindow = ConfigurationWindow(self)

		if self.configurationSaveWindow.IsShow():
			self.configurationSaveWindow.Close()
		else:
			self.configurationSaveWindow.Open()

	def SetItemToolTip(self, tooltipItem):
		for i in xrange(SLOT_COUNT):
			self.itemTabs[i].SetItemToolTip(tooltipItem)

	def __AnyAttributeConfigured(self):
		for i in xrange(ALTERNATIVE_COUNT):
			for j in xrange(ATTR_SLOT_COUNT):
				(type, value) = switchbot.GetAttribute(self.selectedSlot, i, j)
				if type and value:
					return True

		return False

	def RefreshSwitchbotWindow(self):
		self.__RefreshItemSlots()
		self.__RefreshAlternatives()
		self.__RefreshAttributeRows()
		self.__RefreshButtons()

	def RefreshSwitchbotItem(self, slot):
		itemTab = self.itemTabs.get(slot, None)
		if not itemTab:
			return

		itemTab.RefreshItemSlot()

	def __RefreshItemSlots(self):
		for i in xrange(SLOT_COUNT):
			itemTab = self.itemTabs.get(i, None)
			if not itemTab:
				continue

			itemTab.RefreshItemSlot()

	def __RefreshAlternatives(self):
		if self.IsEmptySlot():
			self.alternativePanel.Hide()
		else:
			self.alternativePanel.Show()

	def __RefreshAttributeRows(self):
		for i in xrange(ATTR_SLOT_COUNT):
			row = self.attrDict.get(i, None)
			if not row:
				continue

			(applyType, applyValue) = player.GetItemAttribute(player.SWITCHBOT, self.selectedSlot, i)
			if applyType and applyValue:
				row.Show()
			else:
				row.Hide()

			row.RefreshAttributeRow(self.selectedSlot, self.alternative, i)

	def __RefreshCostText(self):
		if not self.costTextLine:
			return
		vnum = player.GetItemIndex(player.SWITCHBOT, self.selectedSlot)
		if not vnum:
			self.costTextLine.SetText("")
		elif IsCostumeItem(vnum):
			self.costTextLine.SetText(TEXT_COST_COSTUME)
		else:
			self.costTextLine.SetText(TEXT_COST_NORMAL)

	def __RefreshButtons(self):
		self.__RefreshCostText()
		if self.IsEmptySlot() or not self.__AnyAttributeConfigured():
			self.startButton.Disable()
			self.stopButton.Disable()
			return

		self.startButton.Enable()
		self.stopButton.Enable()

		if self.IsActiveSlot():
			self.stopButton.SetUp()
			self.startButton.Down()
		else:
			self.stopButton.Down()
			self.startButton.SetUp()

	def __OnAttributeUpdate(self, attrIdx):
		self.__RefreshButtons()

	def __OnSearchAttribute(self, attrIdx):
		if self.attributeSearchWindow:
			self.attributeSearchWindow.Close()
			self.attributeSearchWindow = None

		self.attrSearchIdx = attrIdx

		wnd = SearchListWindow()
		width = 260
		height = 260
		wnd.MakeWindow(width, height)
		wnd.SetTitleName(TEXT_SELECT_ATTR)
		wnd.SetAcceptArgsType("KEY_VALUE")

		(mouseX, mouseY) = wndMgr.GetMousePosition()

		if mouseX + width/2 > wndMgr.GetScreenWidth():
			xPos = wndMgr.GetScreenWidth() - width
		elif mouseX - width/2 < 0:
			xPos = 0
		else:
			xPos = mouseX - width/2

		if mouseY + height/2 > wndMgr.GetScreenHeight():
			yPos = wndMgr.GetScreenHeight() - height
		elif mouseY - height/2 < 0:
			yPos = 0
		else:
			yPos = mouseY - height/2

		wnd.SetPosition(xPos, yPos)

		firstAttrType = player.GetItemAttribute(player.SWITCHBOT, self.selectedSlot, 0)[0]
		if firstAttrType in ADDON_TYPES.keys():
			for addonType, maxValue in ADDON_TYPES.iteritems():
				affectString = GetAffectString(addonType, maxValue)
				if not affectString:
					continue

				wnd.AppendItem(addonType, affectString)

		attributes = switchbot.GetAttributesForSet(self.selectedSlot)

		# MT2009_PLUS_SWITCHBOT_ATTR_VALUES_V1: only the bonuses of the alternative's other rows are left out (a bonus is
		# wanted once) - the row being chosen keeps its own one in the list (Ameria's code hid it too, so a row set to
		# e.g. Odpornosc na Ogien looked as if the item could not roll it). The list and its maxima are the server's
		# (switchbot attribute information: item_attr of this world, in its bonus mode).
		selectedAttributes = [switchbot.GetAttribute(self.selectedSlot, self.alternative, attrIndex)[0] for attrIndex in xrange(ATTR_SLOT_COUNT) if attrIndex != attrIdx]

		for (type, value) in attributes:
			if type in selectedAttributes:
				continue

			affectString = GetAffectString(type, value)
			if not affectString:
				continue

			wnd.AppendItem(type, affectString)

		wnd.SetAcceptEvent(ui.__mem_func__(self.__OnAcceptSearch))
		wnd.SetCancelEvent(ui.__mem_func__(self.__OnCancelSearch))
		wnd.SetTop()
		wnd.Open()

		self.attributeSearchWindow = wnd

	def __OnAcceptSearch(self, key, value):
		if self.attrSearchIdx < 0 or self.attrSearchIdx >= ATTR_SLOT_COUNT:
			return

		attrRow = self.attrDict.get(self.attrSearchIdx, None)
		if not attrRow:
			return

		maxValue = ADDON_TYPES.get(key, 0)
		if not maxValue:
			maxValue = switchbot.GetAttributeMaxValue(self.selectedSlot, key)

		attrRow.SetAttribute(GetAffectString(key, maxValue), maxValue)
		switchbot.SetAttribute(self.selectedSlot, self.alternative, self.attrSearchIdx, key, maxValue)

		self.__RefreshButtons()

	def SetSavedAttribute(self, slot, alternative, attrIndex, attrType, attrValue):
		if attrIndex < 0 or attrIndex >= ATTR_SLOT_COUNT:
			return

		attrRow = self.attrDict.get(attrIndex, None)
		if not attrRow:
			return

		if slot >= SLOT_COUNT:
			return

		if switchbot.IsActive(slot):
			return

		var = switchbot.GetAttributesForSet(slot)
		attributes = [var[i][0] for i in xrange(len(var))]

		firstAttrType = player.GetItemAttribute(player.SWITCHBOT, slot, 0)[0]
		if firstAttrType in ADDON_TYPES.keys():
			for addon in ADDON_TYPES.keys():
				attributes.append(addon)

		if not attrType in attributes:
			switchbot.SetAttribute(slot, alternative, attrIndex, 0, 0)
		else:
			switchbot.SetAttribute(slot, alternative, attrIndex, attrType, attrValue)

		self.RefreshSwitchbotWindow()

	def IsEmptySlot(self):
		slot = self.itemTabs.get(self.selectedSlot, None)
		if not slot:
			return True

		return slot.IsEmpty()

	def IsActiveSlot(self):
		slot = self.itemTabs.get(self.selectedSlot, None)
		if not slot:
			return False

		return slot.IsActive()

	def TakeInventoryItem(self, pos):
		"""uiinventory's right click with the window open (ours): a weapon, an armour
		(talismans and gloves too) or a costume / hairstyle / weapon skin goes into the
		selected tab, or the first free one."""
		vnum = player.GetItemIndex(player.INVENTORY, pos)
		if not vnum:
			return False
		item.SelectItem(vnum)
		itemType = item.GetItemType()
		if itemType != item.ITEM_TYPE_WEAPON and itemType != item.ITEM_TYPE_ARMOR and not IsCostumeItem(vnum):
			return False
		target = -1
		if not self.itemTabs[self.selectedSlot].IsEmpty() or switchbot.IsActive(self.selectedSlot):
			for i in xrange(SLOT_COUNT):
				if self.itemTabs[i].IsEmpty() and not switchbot.IsActive(i):
					target = i
					break
		else:
			target = self.selectedSlot
		if target < 0:
			return True
		net.SendItemMovePacket(player.INVENTORY, pos, player.SWITCHBOT, target, 1)
		self.SelectSlot(target)
		return True

	def OnMoveWindow(self, x, y):
		if self.configurationSaveWindow:
			self.configurationSaveWindow.AdjustPosition()

	def __OnCancelSearch(self):
		pass

	def OnPressEscapeKey(self):
		self.Close()
		return True


class SearchListWindow(ui.BoardWithTitleBar):
	class SearchListItem(ui.Window):
		LIST_ITEM_HEIGHT = 12

		def __init__(self, key, value):
			ui.Window.__init__(self)

			self.key = key
			self.value = value
			self.isDown = False
			self.onClickEvent = None

			self.textLine = ui.TextLine()
			self.textLine.AddFlag("not_pick")
			self.textLine.SetParent(self)
			self.textLine.SetVerticalAlignCenter()
			self.textLine.SetWindowVerticalAlignCenter()
			self.textLine.SetPosition(10, -1)
			self.textLine.SetText(str(value))
			self.textLine.UpdateRect()
			self.textLine.Show()

		def __del__(self):
			ui.Window.__del__(self)

			self.key = None
			self.value = None

			self.onClickEvent = None

			self.textLine = 0

		def OnMouseLeftButtonUp(self):
			if not self.isDown:
				self.__OnClick()
				self.Down()

		def OnRender(self):
			if self.IsIn() or self.isDown:
				self.RenderHoverOrSelected()

		def RenderHoverOrSelected(self):
			x, y = self.GetGlobalPosition()
			grp.SetColor(grp.GenerateColor(0.0, 0.0, 0.7, 0.7))
			grp.RenderBar(x, y, self.GetWidth(), self.GetHeight())

		def SetUp(self):
			self.isDown = False

		def Down(self):
			self.isDown = True

		def IsDown(self):
			return self.isDown

		def GetKey(self):
			return self.key

		def GetValue(self):
			return self.value

		def GetText(self):
			return self.textLine.GetText()

		def MatchText(self, text):
			return text in self.GetText()

		def SetOnClickEvent(self, event):
			self.onClickEvent = ui.__mem_func__(event)

		def __OnClick(self):
			if self.onClickEvent:
				self.onClickEvent(self.key, self.value)

	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)
		self.AddFlag("attach")
		self.AddFlag("movable")
		self.AddFlag("float")

		self.__Initialize()

	def __del__(self):
		ui.BoardWithTitleBar.__del__(self)
		self.__Initialize()

	def __Initialize(self):
		self.listItems = {}
		self.acceptEvent = None
		self.acceptArgsType = "VALUE"
		self.cancelEvent = None

	def MakeWindow(self, width, height, maxInput = 50):
		self.SetSize(width, height)
		self.SetCloseEvent(ui.__mem_func__(self.Close))

		self.searchInput = ui.ThinBoardCircle()
		self.searchInput.SetParent(self)
		self.searchInput.SetSize(width - (BORDER_SPACE*2), INPUT_HEIGHT)
		self.searchInput.SetPosition(BORDER_SPACE, BORDER_SPACE_TOP)
		self.searchInput.Show()

		self.searchEditLine = ui.EditLine()
		self.searchEditLine.SetParent(self.searchInput)
		self.searchEditLine.SetPosition(10, 8)
		self.searchEditLine.SetSize(self.searchInput.GetWidth() - 20, self.searchInput.GetHeight() - 16)
		self.searchEditLine.SetMax(maxInput)
		self.searchEditLine.SetReturnEvent(ui.__mem_func__(self.__OnAccept))
		self.searchEditLine.SetEscapeEvent(ui.__mem_func__(self.Close))
		self.searchEditLine.OnIMEUpdate = ui.__mem_func__(self.__OnSearchIMEUpdate)
		self.searchEditLine.Show()

		containerHeight = height - (BORDER_SPACE_TOP + INPUT_HEIGHT + 30)

		self.scrollBar = ui.ScrollBar()
		self.scrollBar.SetParent(self)
		self.scrollBar.SetWindowHorizontalAlignRight()
		self.scrollBar.SetPosition(23, BORDER_SPACE_TOP + INPUT_HEIGHT + 2)
		self.scrollBar.SetScrollBarSize(containerHeight - 4)

		self.container = ui.ThinBoardCircle()
		self.container.SetParent(self)
		self.container.SetPosition(BORDER_SPACE, BORDER_SPACE_TOP + INPUT_HEIGHT)
		self.container.SetSize(width - (BORDER_SPACE*2), containerHeight)
		self.container.Show()

		listBoxHeight = self.container.GetHeight()
		listBoxWidth = self.container.GetWidth()

		self.listBox = ui.ListBoxEx()
		self.listBox.SetParent(self.container)
		self.listBox.SetPosition(2, 2)
		self.listBox.SetSize(listBoxWidth, listBoxHeight)
		self.listBox.SetItemStep(self.SearchListItem.LIST_ITEM_HEIGHT)
		self.listBox.SetViewItemCount(self.__GetViewItemCount())
		self.listBox.SetItemSize(listBoxWidth, self.SearchListItem.LIST_ITEM_HEIGHT)
		self.listBox.SetScrollBar(self.scrollBar)
		self.listBox.Show()

		buttonWidth = width / 2 - 20

		self.acceptButton = ui.Button()
		self.acceptButton.SetParent(self)
		self.acceptButton.SetUpVisual("d:/ymir work/ui/public/large_button_01.sub")
		self.acceptButton.SetOverVisual("d:/ymir work/ui/public/large_button_02.sub")
		self.acceptButton.SetDownVisual("d:/ymir work/ui/public/large_button_03.sub")
		self.acceptButton.SetDisableVisual("d:/ymir work/ui/public/large_button_03.sub")
		self.acceptButton.SetWindowVerticalAlignBottom()
		self.acceptButton.SetWindowHorizontalAlignCenter()
		self.acceptButton.SetPosition(-buttonWidth / 2 - 5, 29)
		self.acceptButton.SetText(TEXT_ACCEPT)
		self.acceptButton.SetEvent(ui.__mem_func__(self.__OnAccept))
		self.acceptButton.Show()

		self.cancelButton = ui.Button()
		self.cancelButton.SetParent(self)
		self.cancelButton.SetUpVisual("d:/ymir work/ui/public/large_button_01.sub")
		self.cancelButton.SetOverVisual("d:/ymir work/ui/public/large_button_02.sub")
		self.cancelButton.SetDownVisual("d:/ymir work/ui/public/large_button_03.sub")
		self.cancelButton.SetDisableVisual("d:/ymir work/ui/public/large_button_03.sub")
		self.cancelButton.SetWindowVerticalAlignBottom()
		self.cancelButton.SetWindowHorizontalAlignCenter()
		self.cancelButton.SetPosition(buttonWidth / 2 - 5, 29)
		self.cancelButton.SetText(TEXT_CANCEL)
		self.cancelButton.SetEvent(ui.__mem_func__(self.__OnCancel))
		self.cancelButton.Show()

		self.__AdjustScrollbar()

	def __OnSearchIMEUpdate(self):
		ui.EditLine.OnIMEUpdate(self.searchEditLine)
		self.__RefreshListBox()

	def __GetViewItemCount(self):
		return self.container.GetHeight() / self.SearchListItem.LIST_ITEM_HEIGHT

	def __AdjustScrollbar(self):
		if len(self.listItems) > self.__GetViewItemCount():
			listBoxWidth = self.GetWidth() - (BORDER_SPACE*2) - 20
			self.container.SetSize(listBoxWidth, self.container.GetHeight())
			self.listBox.SetSize(listBoxWidth - 4, self.listBox.GetHeight() - 4)
			self.listBox.SetItemSize(listBoxWidth - 4, self.SearchListItem.LIST_ITEM_HEIGHT)
			attachmentCount = len(self.listItems)
			scrollBarHeight = min(float(self.__GetViewItemCount()) / float(attachmentCount), 1.0)
			self.scrollBar.SetMiddleBarSize(scrollBarHeight)
			self.scrollBar.Show()
		else:
			listBoxWidth = self.GetWidth() - (BORDER_SPACE*2)
			self.container.SetSize(listBoxWidth, self.container.GetHeight())
			self.listBox.SetSize(listBoxWidth - 4, self.listBox.GetHeight() - 4)
			self.listBox.SetItemSize(listBoxWidth - 4, self.SearchListItem.LIST_ITEM_HEIGHT)
			self.scrollBar.Hide()

	def RemoveAllItems(self):
		self.listItems = {}
		self.listBox.RemoveAllItems()

	def AppendItem(self, key, value = ""):
		if self.listItems.has_key(key):
			return

		if not value:
			value = key

		self.listItems[key] = { "value" : value, "item" : None, }
		self.__RefreshListBox()

	def __RefreshListBox(self):
		self.listBox.RemoveAllItems()

		self.__AdjustScrollbar()

		search = self.searchEditLine.GetText().lower()
		for key, dict in sorted(self.listItems.items(), key = lambda kv: kv[1]["value"]):
			if not search or search in dict["value"].lower():
				listItem = self.SearchListItem(key, dict["value"])
				listItem.SetOnClickEvent(self.__OnClickListItem)
				self.listBox.AppendItem(listItem)

	def GetSelectedItem(self):
		for listItem in _ListItems(self.listBox):
			if listItem.IsDown():
				return listItem

		return None

	def SetCancelEvent(self, event):
		self.cancelEvent = event

	def SetAcceptEvent(self, event):
		self.acceptEvent = event

	def SetAcceptArgsType(self, type):
		self.acceptArgsType = type

	def __OnClickListItem(self, key, value):
		curItem = self.GetSelectedItem()
		if curItem:
			curItem.SetUp()

	def __OnCancel(self):
		if self.cancelEvent:
			self.cancelEvent()

		self.Close()

	def __OnAccept(self):
		selItem = self.GetSelectedItem()
		if not selItem:
			items = _ListItems(self.listBox)
			if len(items) == 1:
				selItem = items[0]
			else:
				return

		if self.acceptEvent:
			if self.acceptArgsType == "VALUES":
				self.acceptEvent(selItem.GetValue())
			elif self.acceptArgsType == "KEY":
				self.acceptEvent(selItem.GetKey())
			elif self.acceptArgsType == "KEY_VALUE":
				self.acceptEvent(selItem.GetKey(), selItem.GetValue())

		self.Close()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def Open(self):
		self.Show()
		self.searchEditLine.SetFocus()

	def Close(self):
		self.searchEditLine.SetText("")
		self.searchEditLine.KillFocus()
		self.Hide()


# The saved sets: autohunt/switchbot.cfg, a line a set - "<name>\t<alternative>|<alternative>|..." with an
# alternative "<type>:<value>,<type>:<value>,..." (Ameria: a pickle, switchbot.pkl).
def _LoadConfigurations():
	configs = {}
	try:
		with open(CONFIG_FILE, "r") as handle:
			key = 0
			for line in handle:
				line = line.rstrip("\r\n")
				if "\t" not in line:
					continue
				name, data = line.split("\t", 1)
				alternatives = []
				for alt in data.split("|"):
					attrs = []
					for pair in alt.split(","):
						if ":" not in pair:
							attrs.append((0, 0))
							continue
						try:
							(t, v) = pair.split(":", 1)
							attrs.append((int(t), int(v)))
						except ValueError:
							attrs.append((0, 0))
					alternatives.append(attrs)
				configs[key] = {"name": name, "alternatives": alternatives}
				key += 1
	except (IOError, OSError):
		pass
	return configs


def _SaveConfigurations(configs):
	try:
		folder = os.path.dirname(CONFIG_FILE)
		if folder and not os.path.exists(folder):
			os.makedirs(folder)
		with open(CONFIG_FILE, "w") as handle:
			for key in sorted(configs.keys()):
				config = configs[key]
				name = config["name"].replace("\t", " ").replace("\n", " ").replace("\r", " ")
				alts = []
				for alternative in config["alternatives"]:
					alts.append(",".join(["%d:%d" % (t, v) for (t, v) in alternative]))
				handle.write("%s\t%s\n" % (name, "|".join(alts)))
	except (IOError, OSError):
		pass


class ConfigurationWindow(ui.BoardWithTitleBar):
	BOARD_WIDTH = 250

	class ConfigurationLine(ui.Window):
		LIST_ITEM_HEIGHT = 26

		def __init__(self, width):
			ui.Window.__init__(self)

			self.id = 0
			self.name = ""
			self.loadEvent = None
			self.deleteEvent = None

			self.SetSize(width, 26)

			self.nameTextLine = ui.TextLine()
			self.nameTextLine.SetParent(self)
			self.nameTextLine.SetVerticalAlignCenter()
			self.nameTextLine.SetWindowVerticalAlignCenter()
			self.nameTextLine.SetPosition(5, -1)
			self.nameTextLine.Show()

			self.loadButton = ui.Button()
			self.loadButton.SetParent(self)
			self.loadButton.SetUpVisual(IMG + "load_attr_01.sub")
			self.loadButton.SetOverVisual(IMG + "load_attr_02.sub")
			self.loadButton.SetDownVisual(IMG + "load_attr_03.sub")
			self.loadButton.SetDisableVisual(IMG + "load_attr_03.sub")
			self.loadButton.SetWindowHorizontalAlignRight()
			self.loadButton.SetWindowVerticalAlignCenter()
			self.loadButton.SetPosition(24 * 2 + 2, 1)
			self.loadButton.SetToolTipText(TEXT_LOAD_CONFIGURATION)
			self.loadButton.SetEvent(ui.__mem_func__(self.__OnClickLoadButton))
			self.loadButton.Show()

			self.deleteButton = ui.Button()
			self.deleteButton.SetParent(self)
			self.deleteButton.SetUpVisual(IMG + "delete_attr_01.sub")
			self.deleteButton.SetOverVisual(IMG + "delete_attr_02.sub")
			self.deleteButton.SetDownVisual(IMG + "delete_attr_03.sub")
			self.deleteButton.SetDisableVisual(IMG + "delete_attr_03.sub")
			self.deleteButton.SetWindowHorizontalAlignRight()
			self.deleteButton.SetWindowVerticalAlignCenter()
			self.deleteButton.SetPosition(24 + 2, 1)
			self.deleteButton.SetToolTipText(TEXT_CLEAR_CONFIGURATION)
			self.deleteButton.SetEvent(ui.__mem_func__(self.__OnClickDeleteButton))
			self.deleteButton.Show()

		def __del__(self):
			ui.Window.__del__(self)

		def Load(self, id, name):
			self.id = id
			self.name = name
			self.nameTextLine.SetText(name)

		def SetLoadEvent(self, event):
			self.loadEvent = event

		def SetDeleteEvent(self, event):
			self.deleteEvent = event

		def __OnClickLoadButton(self):
			if self.loadEvent:
				self.loadEvent(self.id)

		def __OnClickDeleteButton(self):
			if self.deleteEvent:
				self.deleteEvent(self.id)

	def __init__(self, wndSwitchbot=None):
		ui.BoardWithTitleBar.__init__(self)

		from weakref import proxy
		self.wndSwitchbot = proxy(wndSwitchbot) if wndSwitchbot else None
		self.dict = {}
		self.listItems = {}
		self.nameInput = None
		self.nameEditLine = None

		self.__LoadWindow()

	def __del__(self):
		ui.BoardWithTitleBar.__del__(self)

	def Destroy(self):
		self.saveButton = None
		self.nameInput = None
		self.nameEditLine = None
		self.scrollBar = None
		self.container = None
		self.listBox = None

		self.listItems = {}

	def __LoadWindow(self):
		self.SetSize(self.BOARD_WIDTH, BOARD_HEIGHT)
		self.SetTitleName(TEXT_CONFIGURATION_TITLE)
		self.SetCloseEvent(ui.__mem_func__(self.Close))
		self.AddFlag("attach")
		self.AddFlag("float")

		self.saveButton = ui.Button()
		self.saveButton.SetParent(self)
		self.saveButton.SetUpVisual(IMG + "btn_small_01.sub")
		self.saveButton.SetOverVisual(IMG + "btn_small_02.sub")
		self.saveButton.SetDownVisual(IMG + "btn_small_03.sub")
		self.saveButton.SetDisableVisual(IMG + "btn_small_01.sub")
		self.saveButton.SetWindowHorizontalAlignRight()
		self.saveButton.SetPosition(self.saveButton.GetWidth() + BORDER_SPACE, BORDER_SPACE_TOP + 3)
		self.saveButton.SetText(TEXT_SAVE)
		self.saveButton.SetEvent(ui.__mem_func__(self.__OnSave))
		self.saveButton.Show()

		self.nameInput = ui.ThinBoardCircle()
		self.nameInput.SetParent(self)
		self.nameInput.SetSize(self.BOARD_WIDTH - (BORDER_SPACE * 2) - self.saveButton.GetWidth() - 3, INPUT_HEIGHT)
		self.nameInput.SetPosition(BORDER_SPACE, BORDER_SPACE_TOP)
		self.nameInput.Show()

		self.nameEditLine = ui.EditLine()
		self.nameEditLine.SetParent(self.nameInput)
		self.nameEditLine.SetSize(self.nameInput.GetWidth() - 20, 18)
		self.nameEditLine.SetMax(32)
		self.nameEditLine.SetPosition(10, 7)
		self.nameEditLine.Show()
		self.nameEditLine.SetEscapeEvent(ui.__mem_func__(self.__OnEscapeEvent))

		height = BOARD_HEIGHT - BORDER_SPACE_TOP - INPUT_HEIGHT - BORDER_SPACE

		self.scrollBar = ui.ScrollBar()
		self.scrollBar.SetParent(self)
		self.scrollBar.SetWindowHorizontalAlignRight()
		self.scrollBar.SetPosition(23, BORDER_SPACE_TOP + INPUT_HEIGHT + 2)
		self.scrollBar.SetScrollBarSize(height - 4)

		self.container = ui.ThinBoardCircle()
		self.container.SetParent(self)
		self.container.SetPosition(BORDER_SPACE, BORDER_SPACE_TOP + INPUT_HEIGHT)
		self.container.SetSize(self.BOARD_WIDTH - (BORDER_SPACE*2), height)
		self.container.Show()

		listBoxHeight = self.container.GetHeight()
		listBoxWidth = self.container.GetWidth()

		self.listBox = ui.ListBoxEx()
		self.listBox.SetParent(self.container)
		self.listBox.SetPosition(2, 2)
		self.listBox.SetSize(listBoxWidth, listBoxHeight)
		self.listBox.SetItemStep(self.ConfigurationLine.LIST_ITEM_HEIGHT + 1)
		self.listBox.SetViewItemCount(self.__GetViewItemCount())
		self.listBox.SetItemSize(listBoxWidth, self.ConfigurationLine.LIST_ITEM_HEIGHT)
		self.listBox.SetScrollBar(self.scrollBar)
		self.listBox.Show()

		self.__AdjustScrollbar()

	def LoadConfigurations(self):
		self.dict = _LoadConfigurations()

		self.listBox.RemoveAllItems()
		self.listItems = {}

		lineWidth = self.listBox.GetWidth()
		if len(self.dict) > self.__GetViewItemCount():
			lineWidth -= 20

		self.__AdjustScrollbar()

		for key in sorted(self.dict.iterkeys()):
			config = self.dict.get(key, None)
			if not config:
				continue

			line = self.ConfigurationLine(lineWidth)
			line.Load(key, config["name"])
			line.SetLoadEvent(ui.__mem_func__(self.__OnApplyConfiguration))
			line.SetDeleteEvent(ui.__mem_func__(self.__OnDeleteConfiguration))
			self.listBox.AppendItem(line)

			self.listItems[key] = line

	def SaveConfigurations(self):
		_SaveConfigurations(self.dict)

	def __OnApplyConfiguration(self, key):
		config = self.dict.get(key, None)
		if not config:
			return

		if not self.wndSwitchbot:
			return

		selectedSlot = self.wndSwitchbot.GetSelectedSlot()
		for alternativeIdx in xrange(min(len(config["alternatives"]), ALTERNATIVE_COUNT)):
			alternative = config["alternatives"][alternativeIdx]
			for attrIdx in xrange(min(len(alternative), ATTR_SLOT_COUNT)):
				(attrType, attrValue) = alternative[attrIdx]
				self.wndSwitchbot.SetSavedAttribute(selectedSlot, alternativeIdx, attrIdx, attrType, attrValue)

	def __OnDeleteConfiguration(self, key):
		config = self.dict.get(key, None)
		if not config:
			return

		if self.listItems.has_key(key):
			del self.listItems[key]
		del self.dict[key]
		self.SaveConfigurations()
		self.LoadConfigurations()

	def Open(self):
		self.Show()
		self.SetTop()
		self.LoadConfigurations()
		self.AdjustPosition()

	def Close(self):
		if self.nameEditLine:
			self.nameEditLine.KillFocus()
		self.Hide()

	def AdjustPosition(self):
		if not self.wndSwitchbot:
			return

		(x, y) = self.wndSwitchbot.GetGlobalPosition()
		self.SetPosition(x - self.GetWidth(), y)

	def __GetViewItemCount(self):
		return self.container.GetHeight() / (self.ConfigurationLine.LIST_ITEM_HEIGHT + 1)

	def __AdjustScrollbar(self):
		if len(self.dict) > self.__GetViewItemCount():
			listBoxWidth = self.GetWidth() - (BORDER_SPACE*2) - 20
			self.container.SetSize(listBoxWidth, self.container.GetHeight())
			self.listBox.SetSize(listBoxWidth - 4, self.listBox.GetHeight() - 4)
			self.listBox.SetItemSize(listBoxWidth - 4, self.ConfigurationLine.LIST_ITEM_HEIGHT)
			attachmentCount = len(self.dict)
			scrollBarHeight = min(float(self.__GetViewItemCount()) / float(attachmentCount), 1.0)
			self.scrollBar.SetMiddleBarSize(scrollBarHeight)
			self.scrollBar.Show()
		else:
			listBoxWidth = self.GetWidth() - (BORDER_SPACE*2)
			self.container.SetSize(listBoxWidth, self.container.GetHeight())
			self.listBox.SetSize(listBoxWidth - 4, self.listBox.GetHeight() - 4)
			self.listBox.SetItemSize(listBoxWidth - 4, self.ConfigurationLine.LIST_ITEM_HEIGHT)
			self.scrollBar.Hide()

	def __OnEscapeEvent(self):
		self.Close()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def __GetNewKey(self):
		key = 0
		while self.dict.has_key(key):
			key += 1

		return key

	def __BuildDict(self, slot, name):
		key = self.__GetNewKey()
		alternatives = []
		for alternative in xrange(ALTERNATIVE_COUNT):
			attributes = [switchbot.GetAttribute(slot, alternative, i) for i in xrange(ATTR_SLOT_COUNT)]
			alternatives.append(attributes)

		new_dict = {
			"name" : name,
			"alternatives" : alternatives,
		}

		return (key, new_dict)

	def __OnSave(self):
		if not self.wndSwitchbot:
			return

		selectedSlot = self.wndSwitchbot.GetSelectedSlot()
		name = self.nameEditLine.GetText()

		if not name:
			return

		(key, new_dict) = self.__BuildDict(selectedSlot, name)
		self.dict[key] = new_dict

		self.nameEditLine.SetText("")

		self.SaveConfigurations()
		self.LoadConfigurations()


# ---------------------------------------------------------------- the module's entry points

_state = {'window': None}


def Start():
	"""game.py, once the character is in the world (and after every warp): the hello
	that makes the server send the switchbot's packets. Nothing with an old exe."""
	if IsSupported():
		net.SendChatPacket("/switchbot hello")


def GetWindow():
	window = _state['window']
	if window is None:
		import uiminigameutil
		window = uiminigameutil.SafeCreate(SwitchbotWindow, TEXT_TITLE)
		_state['window'] = window
	return window


def IsOpen():
	window = _state['window']
	return window is not None and window.IsShow()


def ToggleWindow():
	"""The inventory side bar's button and the "bonus_switch" key (keybind.py)."""
	if not IsSupported():
		chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_NEEDS_EXE)
		return
	window = GetWindow()
	if window is None:
		return
	if window.IsShow():
		window.Close()
	else:
		window.Open()


def RefreshSwitchbotWindow():
	"""game.py, the exe's RefreshSwitchbotWindow (GC 171 UPDATE)."""
	window = _state['window']
	if window is not None and window.IsShow():
		window.RefreshSwitchbotWindow()


def RefreshSwitchbotItem(slot):
	"""game.py, the exe's RefreshSwitchbotItem (GC 171 UPDATE_ITEM)."""
	window = _state['window']
	if window is not None and window.IsShow():
		window.RefreshSwitchbotItem(slot)


def RefreshInventory():
	"""interfacemodule.RefreshInventory (every item packet - a slot's item set or taken)."""
	window = _state['window']
	if window is not None and window.IsShow():
		window.RefreshSwitchbotWindow()


def TakeInventoryItem(pos):
	"""uiinventory's right click: with the window open a weapon or an armour
	goes into a tab instead of being put on. True when taken."""
	window = _state['window']
	if window is None or not window.IsShow() or not IsSupported():
		return False
	try:
		# the equipment's own slots come here too: those still take things off
		if pos >= getattr(player, 'EQUIPMENT_SLOT_START', 180) or player.IsEquipmentSlot(pos) or player.IsCostumeSlot(pos):
			return False
		return window.TakeInventoryItem(pos)
	except Exception:
		import dbg
		import sys
		dbg.TraceError('uiswitchbot.TakeInventoryItem: %s' % str(sys.exc_info()[1]))
		return False


def DestroyWindow():
	window = _state['window']
	_state['window'] = None
	if window is not None:
		try:
			window.Destroy()
		except Exception:
			pass
