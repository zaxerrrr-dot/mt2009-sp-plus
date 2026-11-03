# MT2009_PLUS_FISH_PUZZLE_V2 - Wedkarskie Puzzle (Event Rybacki - Puzzle): the owner's package "Mini Game Fish Event
# (17.3)" (uiMiniGameFishEvent.py, uiscript minigamefishgamepage.py / minigamefisheventwaitingpage.py) with its fixes
# from the owner (MiniGameFishAdd: the laid piece is its cover button only). Needs the exe with ENABLE_FISH_EVENT
# (client-patches/exe): net.SendUseFishBox / SendAddFishBox, player.SLOT_TYPE_FISH_EVENT, app.FISH_EVENT_SHAPE_1..7,
# wndMgr.SetDisableDeattach / SetPickedAreaRender / DeleteCoverButton. The server: fish_puzzle.cpp (CG 219 / GC 223).
#
# The waiting page (the rules, Start) and the game page: the 6 x 4 board, the deluxe and the normal box slot (a box
# dragged from the inventory, or the first one found when the page opens), the attempts. A left click on a box slot
# asks and opens the box (one attempt); the piece follows the mouse; a left click on the board asks and lays it, a
# right click asks and throws it away. A full board: the effects, then the reward's name.
#
# Ours against the package: the texts are Polish (CP1250 escapes, on uiScriptLocale / localeInfo under the package's
# names when the locale has none), a window that does not load is logged (uiminigameutil.LoadError) instead of
# exception.Abort, the rules are TextLines (uiminigameutil.DescriptionText - our exe lays out the quest text renderer
# itself, the package's event set page shift moved it out of the box), the mouse's "no deattach" ends with every piece
# laid or thrown (the package left it on after a laid piece), WJ_ENABLE_TRADABLE_ICON is not in our exe.
#
# Python 2.7 as the client has it.

import app
import net
import player
import localeInfo
import uiScriptLocale
import uiCommon
import grpImage
import wndMgr
import item
import ui
import mouseModule
import uiminigameutil

SPECIAL_TYPE = 1
NORMAL_TYPE = 2
FISH_EVENT_TYPE_MAX = 3

ITEM_FISH_EVENT_BOX = 25106
ITEM_FISH_EVENT_BOX_SPECIAL = 25107

DESC_FILE_NAME = 'fish_event_desc.txt'
DESC_LINE_COUNT = 8

TRADABLE_ICON = getattr(app, 'WJ_ENABLE_TRADABLE_ICON', 0)

# --------------------------------------------------------------- the texts (the package's keys)

_TEXTS_INTERFACE = (
	('MINI_GAME_FISH_TITLE', 'W\xeadkarskie Puzzle'),
	('BANNER_FISH_BUTTON', 'W\xeadkarskie Puzzle'),
	('MINI_GAME_FISH_START_TEXT', 'Start'),
	('MINI_GAME_FISH_HELP_TEXT', 'Pomoc'),
	('MINIGAME_FISH_EVENT_USE_COUNT', 'Pr\xf3by'),
)
_TEXTS_GAME = (
	('MINIGAME_FISH_EVENT_ADD_ACCEPT', 'Czy chcesz po\xb3o\xbfy\xe6 tutaj ten element?'),
	('MINIGAME_FISH_EVENT_DROP_ACCEPT', 'Czy na pewno chcesz wyrzuci\xe6 ten element?'),
	('MINIGAME_FISH_EVENT_REWARD_MSG', 'Otrzymujesz: %s.'),
	('MINIGAME_FISH_EVENT_USE_ACCEPT', 'Czy chcesz otworzy\xe6 to pud\xb3o?'),
)
# the uiscripts may import only uiScriptLocale (the ui.py sandbox): their texts go there before a page loads
for _key, _val in _TEXTS_INTERFACE:
	if _key not in uiScriptLocale.__dict__:
		setattr(uiScriptLocale, _key, _val)
for _key, _val in _TEXTS_GAME:
	if _key not in localeInfo.__dict__:
		setattr(localeInfo, _key, _val)


def LoadScript(self, fileName):
	try:
		pyScrLoader = ui.PythonScriptLoader()
		pyScrLoader.LoadScriptFile(self, fileName)
	except:
		uiminigameutil.LoadError("MiniGameFish.LoadScript %s" % fileName)


class FishEventGameWaitingPage(ui.ScriptWindow):
	def __init__(self, wndMiniGameFish):
		if not wndMiniGameFish:
			uiminigameutil.LoadError("wndMiniGameFish parameter must be set to MiniGameFish")

		ui.ScriptWindow.__init__(self)
		self.isLoaded = 0
		self.SetWindowName("FishEventGameWaitingPage")
		self.wndMiniGameFish = wndMiniGameFish
		self.descriptionBox = None

		self.__LoadWindow()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __LoadWindow(self):
		if self.isLoaded == 1:
			return
		self.isLoaded = 1

		LoadScript(self, "uiscript/minigamefisheventwaitingpage.py")

		try:
			self.titleBar = self.GetChild("titlebar")
			self.gameStartButton = self.GetChild("game_start_button")
			self.descBoard = self.GetChild("desc_board")
			self.prevButton = self.GetChild("prev_button")
			self.nextButton = self.GetChild("next_button")
		except:
			uiminigameutil.LoadError("FishEventGameWaitingPage.__LoadWindow.BindObject")

		self.titleBar.SetCloseEvent(ui.__mem_func__(self.Close))
		self.gameStartButton.SetEvent(ui.__mem_func__(self.__ClickStartButton))

		self.descriptionBox = uiminigameutil.DescriptionText(self.descBoard, 7, 7,
			self.descBoard.GetWidth() - 14, self.descBoard.GetHeight() - 14, DESC_LINE_COUNT, 16)
		self.descriptionBox.Show()

		self.prevButton.SetEvent(ui.__mem_func__(self.PrevDescriptionPage))
		self.nextButton.SetEvent(ui.__mem_func__(self.NextDescriptionPage))

	def Show(self):
		if self.descriptionBox:
			self.descriptionBox.LoadLocaleFile(DESC_FILE_NAME)
			self.descriptionBox.Show()

		ui.ScriptWindow.Show(self)
		self.SetTop()

	def Close(self):
		ui.ScriptWindow.Hide(self)

	def Destroy(self):
		self.isLoaded = 0
		if self.descriptionBox:
			self.descriptionBox.Destroy()
		self.descriptionBox = None
		self.wndMiniGameFish = None
		self.titleBar = None
		self.ClearDictionary()

	def __ClickStartButton(self):
		if self.wndMiniGameFish:
			if self.wndMiniGameFish.wndGamePage:
				self.wndMiniGameFish.wndGamePage.Show()
				self.Close()

	def PrevDescriptionPage(self):
		if self.descriptionBox:
			self.descriptionBox.PrevPage()

	def NextDescriptionPage(self):
		if self.descriptionBox:
			self.descriptionBox.NextPage()

	def OnPressEscapeKey(self):
		self.Close()
		return True


class FishEventGamePage(ui.ScriptWindow):
	def __init__(self, wndMiniGameFish):
		if not wndMiniGameFish:
			uiminigameutil.LoadError("wndMiniGameFish parameter must be set to MiniGameFish")

		ui.ScriptWindow.__init__(self)
		self.isLoaded = 0
		self.SetWindowName("FishEventGamePageWindow")
		self.wndMiniGameFish = wndMiniGameFish

		self.wndInterface = None
		self.wndInventory = None

		self.tooltipItem = None

		self.fishBoxSlot = [0 for col in range(0, FISH_EVENT_TYPE_MAX)]
		self.fishBoxSlotPos = [-1 for col in range(0, FISH_EVENT_TYPE_MAX)]

		self.gridSlot = None
		self.currentShape = 0

		self.questionDialog = None

		self.useCountText = None
		self.useCount = 0

		self.scoreTextEffect = None
		self.scoreEffects = [None for effect in xrange(3)]

		self.popupReward = None
		self.rewardVnum = 0

		self.fishPieceDict = {
			app.FISH_EVENT_SHAPE_1	: ["D:/Ymir Work/UI/minigame/fish_event/fish_1.sub", (0, 0), (1, 3)],
			app.FISH_EVENT_SHAPE_2	: ["D:/Ymir Work/UI/minigame/fish_event/fish_2.sub", (0, 0), (1, 1)],
			app.FISH_EVENT_SHAPE_3	: ["D:/Ymir Work/UI/minigame/fish_event/fish_3.sub", (-16, -16), (2, 2)],
			app.FISH_EVENT_SHAPE_4	: ["D:/Ymir Work/UI/minigame/fish_event/fish_4.sub", (-16, -16), (2, 2)],
			app.FISH_EVENT_SHAPE_5	: ["D:/Ymir Work/UI/minigame/fish_event/fish_5.sub", (-16, -16), (2, 2)],
			app.FISH_EVENT_SHAPE_6	: ["D:/Ymir Work/UI/minigame/fish_event/fish_6.sub", (-8, -16), (3, 2)],
			app.FISH_EVENT_SHAPE_7	: ["D:/Ymir Work/UI/minigame/fish_event/fish_7.sub", (-8, -16), (3, 2)],
		}

		self.__LoadWindow()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def BindInterface(self, interface):
		self.wndInterface = interface

	def BindInventory(self, inventory):
		self.wndInventory = inventory

	def SetItemToolTip(self, tooltip):
		self.tooltipItem = tooltip

	def __LoadWindow(self):
		if self.isLoaded == 1:
			return
		self.isLoaded = 1

		LoadScript(self, "uiscript/minigamefishgamepage.py")

		try:
			self.GetChild("titlebar").SetCloseEvent(ui.__mem_func__(self.Close))
			self.GetChild("help_button").SetEvent(ui.__mem_func__(self.__ClickHelpButton))

			self.gridSlot = self.GetChild("GameSlot")
			self.gridSlot.SetSelectEmptySlotEvent(ui.__mem_func__(self.__SelectEmptyGameSlot))
			self.gridSlot.SetUnselectEmptySlotEvent(ui.__mem_func__(self.__UnselectEmptyGameSlot))
			self.gridSlot.SetUnselectItemSlotEvent(ui.__mem_func__(self.__UnselectItemGameSlotEvent))

			self.useCountText = self.GetChild("use_count_text")
			self.useCountText.SetText(str(self.useCount))

			for i in xrange(len(self.scoreEffects)):
				self.scoreEffects[i] = self.GetChild("score_completion_effect%d" % int(i + 1))
				self.scoreEffects[i].SetScale(1.2, 1.2)
				self.scoreEffects[i].Hide()
				self.scoreEffects[i].SetEndFrameEvent(lambda arg = i : ui.__mem_func__(self.__ScoreEffectEndFrameEvent)(arg))

			self.scoreTextEffect = self.GetChild("score_completion_text_effect")
			self.scoreTextEffect.SetEndFrameEvent(ui.__mem_func__(self.__ScoreTextEffectEndFrameEvent))
			self.scoreTextEffect.Hide()

			specialItemSlot = self.GetChild("SpecialItemSlot")
			specialItemSlot.SetSelectEmptySlotEvent(ui.__mem_func__(self.__SelectEmptySlot), SPECIAL_TYPE)
			specialItemSlot.SetOverInItemEvent(ui.__mem_func__(self.OverInItem), SPECIAL_TYPE)
			specialItemSlot.SetOverOutItemEvent(ui.__mem_func__(self.OverOutItem))
			specialItemSlot.SetSelectItemSlotEvent(ui.__mem_func__(self.SelectItemSlot), SPECIAL_TYPE)
			specialItemSlot.SetUnselectItemSlotEvent(ui.__mem_func__(self.__UnselectItemSlot), SPECIAL_TYPE)
			self.fishBoxSlot[SPECIAL_TYPE] = specialItemSlot

			normalItemSlot = self.GetChild("NormalItemSlot")
			normalItemSlot.SetSelectEmptySlotEvent(ui.__mem_func__(self.__SelectEmptySlot), NORMAL_TYPE)
			normalItemSlot.SetOverInItemEvent(ui.__mem_func__(self.OverInItem), NORMAL_TYPE)
			normalItemSlot.SetOverOutItemEvent(ui.__mem_func__(self.OverOutItem))
			normalItemSlot.SetSelectItemSlotEvent(ui.__mem_func__(self.SelectItemSlot), NORMAL_TYPE)
			normalItemSlot.SetUnselectItemSlotEvent(ui.__mem_func__(self.__UnselectItemSlot), NORMAL_TYPE)
			self.fishBoxSlot[NORMAL_TYPE] = normalItemSlot
		except:
			uiminigameutil.LoadError("FishEventGamePage.__LoadWindow.BindObject")

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def Show(self):
		ui.ScriptWindow.Show(self)
		self.SetTop()
		mouseModule.mouseController.DeattachObjectPostProcess()

		for i in xrange(player.INVENTORY_PAGE_SIZE * player.INVENTORY_PAGE_COUNT):
			if player.GetItemIndex(i) == ITEM_FISH_EVENT_BOX_SPECIAL:
				self.__AddFishEventSlot(SPECIAL_TYPE, i)
				break

		for i in xrange(player.INVENTORY_PAGE_SIZE * player.INVENTORY_PAGE_COUNT):
			if player.GetItemIndex(i) == ITEM_FISH_EVENT_BOX:
				self.__AddFishEventSlot(NORMAL_TYPE, i)
				break

	def Close(self):
		if player.SLOT_TYPE_FISH_EVENT == mouseModule.mouseController.GetAttachedType():
			return

		if TRADABLE_ICON:
			if self.wndInterface:
				self.wndInterface.SetOnTopWindow(player.ON_TOP_WND_NONE)
				self.wndInterface.RefreshMarkInventoryBag()

		self.ClearFishBoxSlot()

		app.ShowCursor()

		if self.tooltipItem:
			self.tooltipItem.HideToolTip()

		if self.popupReward:
			self.popupReward.Close()

		ui.ScriptWindow.Hide(self)

	def Destroy(self):
		self.ClearFishBoxSlot()

		if player.SLOT_TYPE_FISH_EVENT == mouseModule.mouseController.GetAttachedType():
			self.__DropAccept()

		if self.questionDialog:
			self.questionDialog.Close()
			self.questionDialog = None

		self.isLoaded = 0
		self.wndMiniGameFish = None

		if self.fishBoxSlot:
			del self.fishBoxSlot[:]

		if self.fishBoxSlotPos:
			del self.fishBoxSlotPos[:]

		if self.scoreEffects:
			del self.scoreEffects[:]

		self.wndInterface = None
		self.wndInventory = None

		self.tooltipItem = None

		self.gridSlot = None
		self.currentShape = 0
		self.popupReward = None
		self.useCountText = None
		self.scoreTextEffect = None
		self.rewardVnum = 0

		self.ClearDictionary()

	def __ClickHelpButton(self):
		if player.SLOT_TYPE_FISH_EVENT == mouseModule.mouseController.GetAttachedType():
			return

		if self.wndMiniGameFish:
			if self.wndMiniGameFish.wndWaitingPage:
				self.wndMiniGameFish.wndWaitingPage.Show()
				self.Close()

	if TRADABLE_ICON:
		def OnTop(self):
			if not self.wndInterface:
				return

			self.wndInterface.SetOnTopWindow(player.ON_TOP_WND_FISH_EVENT)
			self.wndInterface.RefreshMarkInventoryBag()

	def OverInItem(self, slotIndex, type):
		if self.tooltipItem and self.fishBoxSlotPos[type] != -1:
			self.tooltipItem.SetInventoryItem(self.fishBoxSlotPos[type])

	def OverOutItem(self):
		if self.tooltipItem:
			self.tooltipItem.HideToolTip()

	def __UnselectItemSlot(self, slotIndex, type):
		if mouseModule.mouseController.isAttached():
			return

		if self.questionDialog:
			if self.questionDialog.IsShow():
				return

		self.ClearFishBoxSlot(type)

	def __UnselectEmptyGameSlot(self, slotIndex):
		if not mouseModule.mouseController.isAttached():
			return

		self.DropQuestionDialog()

	def __UnselectItemGameSlotEvent(self, slotIndex):
		if not mouseModule.mouseController.isAttached():
			return

		self.DropQuestionDialog()

	def __AddFishEventSlot(self, type, pos):
		if -1 != self.fishBoxSlotPos[type]:
			return

		self.fishBoxSlotPos[type] = pos
		self.fishBoxSlot[type].SetItemSlot(0, player.GetItemIndex(player.INVENTORY, pos), player.GetItemCount(player.INVENTORY, pos))
		self.fishBoxSlot[type].ActivateSlot(0)
		self.fishBoxSlot[type].RefreshSlot()

	def __SelectEmptySlot(self, slotIndex, type):
		if not mouseModule.mouseController.isAttached():
			return

		attachedSlotType = mouseModule.mouseController.GetAttachedType()
		attachedSlotPos = mouseModule.mouseController.GetAttachedSlotNumber()
		attachedItemIndex = mouseModule.mouseController.GetAttachedItemIndex()

		if player.SLOT_TYPE_INVENTORY != attachedSlotType:
			return

		mouseModule.mouseController.DeattachObject()
		if attachedSlotPos >= player.INVENTORY_PAGE_SIZE * player.INVENTORY_PAGE_COUNT:
			return

		if NORMAL_TYPE == type:
			if ITEM_FISH_EVENT_BOX != attachedItemIndex:
				return
		elif SPECIAL_TYPE == type:
			if ITEM_FISH_EVENT_BOX_SPECIAL != attachedItemIndex:
				return
		else:
			return

		self.fishBoxSlotPos[type] = attachedSlotPos
		self.fishBoxSlot[type].SetItemSlot(0, attachedItemIndex, player.GetItemCount(player.INVENTORY, attachedSlotPos))
		self.fishBoxSlot[type].ActivateSlot(0)
		self.fishBoxSlot[type].RefreshSlot()

	def __SelectEmptyGameSlot(self, slotIndex):
		if not mouseModule.mouseController.isAttached():
			return

		if 0 == self.currentShape:
			return

		attachedSlotType = mouseModule.mouseController.GetAttachedType()
		if player.SLOT_TYPE_FISH_EVENT != attachedSlotType:
			return

		if self.questionDialog:
			self.questionDialog.Close()
			self.questionDialog = None

		self.questionDialog = uiCommon.QuestionDialog()
		self.questionDialog.SetAcceptEvent(lambda arg = slotIndex : ui.__mem_func__(self.__AddAccept)(arg))
		self.questionDialog.SetCancelEvent(ui.__mem_func__(self.__QuestionCancel))
		self.questionDialog.SetText(localeInfo.MINIGAME_FISH_EVENT_ADD_ACCEPT)
		self.questionDialog.Open()
		mouseModule.mouseController.SetAttachedIconRender(False)

		app.ShowCursor()

		if self.gridSlot:
			self.gridSlot.SetPickedAreaRender(False)

	def __AddAccept(self, slotIndex):
		self.__QuestionCancel()
		net.SendAddFishBox(slotIndex)
		self.currentShape = 0
		self.DeattachObject()

	# the owner's working version (3 November 2026): the laid piece is its cover button only
	def MiniGameFishAdd(self, pos, shape):
		shapeImage = self.fishPieceDict[shape][0]
		positionInfo = {
			app.FISH_EVENT_SHAPE_1 : [0, 6, 12],
			app.FISH_EVENT_SHAPE_2 : [0],
			app.FISH_EVENT_SHAPE_3 : [0, 6, 7],
			app.FISH_EVENT_SHAPE_4 : [0, 1, 7],
			app.FISH_EVENT_SHAPE_5 : [0, 1, 6, 7],
			app.FISH_EVENT_SHAPE_6 : [0, 1, 7, 8],
			app.FISH_EVENT_SHAPE_7 : [0, 1, 2, 6, 7, 8],
		}
		if shape in positionInfo:
			self.gridSlot.SetCoverButton(pos, shapeImage, shapeImage, shapeImage, shapeImage, False, False)
			self.gridSlot.SetAlwaysRenderCoverButton(pos)
			# for i in xrange(len(positionInfo[shape])):
				# self.gridSlot.SetSlot(pos + positionInfo[shape][i], 1, 1, 1, 0)
			self.gridSlot.RefreshSlot()

	def MiniGameFishReward(self, vnum):
		self.rewardVnum = vnum
		self.__ClearCompletionEffect()

		for scoreEffect in self.scoreEffects:
			if scoreEffect:
				scoreEffect.Show()

		if self.scoreTextEffect:
			self.scoreTextEffect.Show()

	def ClearFishBoxSlot(self, type = FISH_EVENT_TYPE_MAX):
		if TRADABLE_ICON:
			if not self.wndInventory:
				return

		if FISH_EVENT_TYPE_MAX == type:
			for index in range(1, FISH_EVENT_TYPE_MAX):
				if not self.fishBoxSlot[index]:
					continue

				if self.fishBoxSlotPos[index] == -1:
					continue

				self.fishBoxSlot[index].SetItemSlot(0, 0)
				self.fishBoxSlot[index].DeactivateSlot(0)
				self.fishBoxSlot[index].RefreshSlot()
				self.fishBoxSlotPos[index] = -1

		else:
			if not self.fishBoxSlot[type]:
				return

			if self.fishBoxSlotPos[type] == -1:
				return

			self.fishBoxSlot[type].SetItemSlot(0, 0)
			self.fishBoxSlot[type].DeactivateSlot(0)
			self.fishBoxSlot[type].RefreshSlot()
			self.fishBoxSlotPos[type] = -1

	def SelectItemSlot(self, slotIndex, type):
		if 0 != self.currentShape:
			return

		mouseModule.mouseController.DeattachObject()

		if self.questionDialog:
			self.questionDialog.Close()
			self.questionDialog = None

		self.questionDialog = uiCommon.QuestionDialog()
		self.questionDialog.SetAcceptEvent(lambda arg = type : ui.__mem_func__(self.__UseAccept)(arg))
		self.questionDialog.SetCancelEvent(ui.__mem_func__(self.__UseAcceptCancel))
		self.questionDialog.SetText(localeInfo.MINIGAME_FISH_EVENT_USE_ACCEPT)
		self.questionDialog.Open()

	def __UseAccept(self, type):
		self.__QuestionCancel()
		if self.fishBoxSlotPos[type] != -1:
			net.SendUseFishBox(player.INVENTORY, self.fishBoxSlotPos[type])

	def __UseAcceptCancel(self):
		if self.questionDialog:
			self.questionDialog.Close()
			self.questionDialog = None

	def __QuestionCancel(self):
		if self.questionDialog:
			self.questionDialog.Close()
			self.questionDialog = None

		if self.gridSlot:
			self.gridSlot.SetPickedAreaRender(True)

		mouseModule.mouseController.SetAttachedIconRender(True)
		app.HideCursor()

	def DropQuestionDialog(self):
		if self.questionDialog:
			self.questionDialog.Close()
			self.questionDialog = None

		self.questionDialog = uiCommon.QuestionDialog()
		self.questionDialog.SetAcceptEvent(ui.__mem_func__(self.__DropAccept))
		self.questionDialog.SetCancelEvent(ui.__mem_func__(self.__QuestionCancel))
		self.questionDialog.SetText(localeInfo.MINIGAME_FISH_EVENT_DROP_ACCEPT)
		self.questionDialog.Open()
		self.questionDialog.SetTop()

		mouseModule.mouseController.SetAttachedIconRender(False)
		app.ShowCursor()

		if self.gridSlot:
			self.gridSlot.SetPickedAreaRender(False)

	def __DropAccept(self):
		self.__QuestionCancel()
		self.currentShape = 0
		app.ShowCursor()
		wndMgr.SetDisableDeattach(False)
		self.DeattachObject()

	def MiniGameFishCount(self, useCount):
		self.useCount = useCount
		if self.useCountText:
			self.useCountText.SetText(str(self.useCount))

	def MiniGameFishUse(self, shape, useCount):
		if shape not in self.fishPieceDict:
			return

		self.currentShape = shape

		for index in range(1, FISH_EVENT_TYPE_MAX):
			if self.fishBoxSlotPos[index] == -1:
				continue

			item_count = player.GetItemCount(player.INVENTORY, self.fishBoxSlotPos[index])
			item_vnum = player.GetItemIndex(player.INVENTORY, self.fishBoxSlotPos[index])

			if 0 == item_count:
				self.ClearFishBoxSlot(index)
			else:
				self.fishBoxSlot[index].SetItemSlot(0, item_vnum, item_count)
				self.fishBoxSlot[index].RefreshSlot()

		app.HideCursor()

		(adjust_x, adjust_y) = self.fishPieceDict[shape][1]
		(width, height) = self.fishPieceDict[shape][2]

		if shape == app.FISH_EVENT_SHAPE_1:
			mouseModule.mouseController.AttachFishPiece(self, 3000, grpImage.Generate(self.fishPieceDict[shape][0]), adjust_x, adjust_y, width, height)
		elif shape == app.FISH_EVENT_SHAPE_2:
			mouseModule.mouseController.AttachFishPiece(self, 71084, grpImage.Generate(self.fishPieceDict[shape][0]), adjust_x, adjust_y, width, height)
		else:
			mouseModule.mouseController.AttachFishPiece(self, shape, grpImage.Generate(self.fishPieceDict[shape][0]), adjust_x, adjust_y, width, height)

		for type in range(1, FISH_EVENT_TYPE_MAX):
			self.fishBoxSlot[type].DeactivateSlot(0)

		wndMgr.SetDisableDeattach(True)

		self.useCount = useCount
		if self.useCountText:
			self.useCountText.SetText(str(self.useCount))

	def DeattachObject(self):
		mouseModule.mouseController.DeattachObjectPostProcess()
		# the exe's own deattach again (the package left it off after a laid piece)
		wndMgr.SetDisableDeattach(False)

		for type in range(1, FISH_EVENT_TYPE_MAX):
			if self.fishBoxSlotPos[type] == -1:
				self.fishBoxSlot[type].DeactivateSlot(0)
				continue
			item_count = player.GetItemCount(player.INVENTORY, self.fishBoxSlotPos[type])
			if item_count:
				self.fishBoxSlot[type].ActivateSlot(0)
			else:
				self.fishBoxSlot[type].DeactivateSlot(0)

	def __ScoreEffectEndFrameEvent(self, type):
		if self.scoreEffects and self.scoreEffects[type]:
			self.scoreEffects[type].Hide()

	def __ScoreTextEffectEndFrameEvent(self):
		if self.scoreTextEffect:
			self.scoreTextEffect.Hide()

		self.useCount = 0
		if self.useCountText:
			self.useCountText.SetText(str(self.useCount))

		if self.gridSlot:
			for slotPos in xrange(self.gridSlot.GetSlotCount()):
				self.gridSlot.DeleteCoverButton(slotPos)
				self.gridSlot.ClearSlot(slotPos)
			self.gridSlot.RefreshSlot()

		if not self.rewardVnum:
			return

		if not self.popupReward:
			self.popupReward = uiCommon.PopupDialog()

		item.SelectItem(self.rewardVnum)
		self.popupReward.SetText(localeInfo.MINIGAME_FISH_EVENT_REWARD_MSG % item.GetItemName())
		self.popupReward.Open()

		self.rewardVnum = 0

	def __ClearCompletionEffect(self):
		if self.scoreTextEffect:
			self.scoreTextEffect.Hide()
			self.scoreTextEffect.ResetFrame()
			self.scoreTextEffect.SetDelay(6)

		for scoreEffect in self.scoreEffects:
			if scoreEffect:
				scoreEffect.Hide()
				scoreEffect.ResetFrame()
				scoreEffect.SetDelay(6)


class MiniGameFish(ui.Window):
	wndWaitingPage = None
	wndGamePage = None

	def __init__(self):
		ui.Window.__init__(self)
		self.SetWindowName("MiniGameFishWindow")
		self.wndWaitingPage = FishEventGameWaitingPage(self)
		self.wndGamePage = FishEventGamePage(self)

	def __del__(self):
		ui.Window.__del__(self)

	def Destroy(self):
		self.isLoaded = 0

		if self.wndWaitingPage:
			self.wndWaitingPage.Destroy()
			self.wndWaitingPage = None

		if self.wndGamePage:
			self.wndGamePage.Destroy()
			self.wndGamePage = None

	def Open(self):
		if self.wndGamePage:
			if self.wndGamePage.IsShow():
				self.wndGamePage.SetTop()
				return

		if self.wndWaitingPage:
			self.wndWaitingPage.Show()

	# "FP open" (a box used from the inventory): straight to the board
	def OpenGame(self):
		if self.wndGamePage:
			if self.wndGamePage.IsShow():
				self.wndGamePage.SetTop()
				return
			if self.wndWaitingPage and self.wndWaitingPage.IsShow():
				self.wndWaitingPage.Close()
			self.wndGamePage.Show()

	def Close(self):
		if self.wndWaitingPage:
			if self.wndWaitingPage.IsShow():
				self.wndWaitingPage.Close()

		if self.wndGamePage:
			if self.wndGamePage.IsShow():
				self.wndGamePage.Close()

	def MiniGameFishUse(self, shape, useCount):
		if self.wndGamePage:
			self.wndGamePage.MiniGameFishUse(shape, useCount)

	def MiniGameFishAdd(self, pos, shape):
		if self.wndGamePage:
			self.wndGamePage.MiniGameFishAdd(pos, shape)

	def MiniGameFishReward(self, vnum):
		if self.wndGamePage:
			self.wndGamePage.MiniGameFishReward(vnum)

	def MiniGameFishCount(self, count):
		if self.wndGamePage:
			self.wndGamePage.MiniGameFishCount(count)

	def CantFishEventSlot(self, InvenSlot):
		ItemVnum = player.GetItemIndex(InvenSlot)
		if ItemVnum in [ITEM_FISH_EVENT_BOX, ITEM_FISH_EVENT_BOX_SPECIAL]:
			return False

		return True

	def SetItemToolTip(self, tooltip):
		if self.wndGamePage:
			self.wndGamePage.SetItemToolTip(tooltip)

	def BindInterface(self, interface):
		if self.wndGamePage:
			self.wndGamePage.BindInterface(interface)

	def BindInventory(self, inventory):
		if self.wndGamePage:
			self.wndGamePage.BindInventory(inventory)
