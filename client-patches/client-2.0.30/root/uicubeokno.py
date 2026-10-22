# MT2009_PLUS_NPC_CRAFT_WINDOW_V1 (the owner, 22 October 2026: "at every NPC with crafting a window must open and show
# what you need to give", as on the global servers): the crafting window of the NPCs - a list of the NPC's recipes and,
# for the chosen one, its result, its materials with "have / need", the Gaya and the Yang it takes, its chance and the
# chance-raising slot ("Podwyzsz szanse"). "Wytworz" puts the materials from the bag (and the extra inventory) into the
# server's crafting window itself ("/cube add", "/ekwipunek kostka"), names the chosen recipe ("/cube pick") and makes it
# ("/cube make"); the server side is the usual cube (server-patches/gaya). The set blacksmiths (20475-20479) keep the
# old window (uicube.py) - their rows are the player's own pieces. Built in code from the public UI images only.
import ui
import net
import player
import item
import grp
import app
import chat
import mouseModule
import localeInfo
import uiCube

GAYA_VNUM = 95927
MAX_MATERIALS = 6
CUBE_SLOT_MAX = 24
USE_LIMIT_RANGE = 1000
SLOT_BASE = "d:/ymir work/ui/public/Slot_Base.sub"
BUTTON = ("d:/ymir work/ui/public/middle_button_01.sub", "d:/ymir work/ui/public/middle_button_02.sub", "d:/ymir work/ui/public/middle_button_03.sub")

COLOR_OK = grp.GenerateColor(0.5411, 0.7254, 0.5568, 1.0)
COLOR_BAD = grp.GenerateColor(0.9, 0.4745, 0.4627, 1.0)
COLOR_GOLD = grp.GenerateColor(1.0, 0.85, 0.4, 1.0)
COLOR_GAYA = grp.GenerateColor(0.6, 0.85, 1.0, 1.0)

TEXT_TITLE = "Wytwarzanie"
TEXT_MAKE = "Wytw\xf3rz"
TEXT_CLOSE = "Zamknij"
TEXT_IMPROVE = "Podwy\xbfsz szans\xea"
TEXT_PICK = "Wybierz przepis z listy."
TEXT_COST = "Koszt: %s"
TEXT_GAYA = "Gaya: %d (masz %d)"
TEXT_CHANCE = "Szansa: %s%%"
TEXT_CHANCE_BONUS = "Szansa: %s%% (+%d%%)"
TEXT_MISSING = "Brakuje: %s"
TEXT_NO_GOLD = "Masz za ma\xb3o Yang."
TEXT_NO_GAYA = "Masz za ma\xb3o Gaya."
TEXT_TOO_MANY = "Za du\xbfo stos\xf3w materia\xb3\xf3w - po\xb3\xb9cz je w ekwipunku."
TEXT_SUCCESS = "Uda\xb3o si\xea: %s"
TEXT_FAIL = "Nie uda\xb3o si\xea."
TEXT_OR = "albo"
TEXT_IMPROVE_WRONG = "Ten przedmiot nie dzia\xb3a na ten przepis."
TEXT_IMPROVE_HINT = "Po\xb3\xf3\xbf tu przedmiot zwi\xeakszaj\xb9cy szans\xea."
TEXT_CLICK_REMOVE = "Kliknij, aby go wyj\xb9\xe6."
TEXT_COUNT = "Przepis\xf3w: %d"


def _HaveCount(vnum):
	n = 0
	for pos in uiCube._CubePositions():
		if uiCube._ItemIndex(pos) == vnum:
			n += uiCube._ItemCount(pos)
	return n


def _ChanceMin(chance):
	try:
		return int(str(chance).split("-")[0])
	except ValueError:
		return 0


class RecipeRow(ui.ListBoxEx.Item):
	def __init__(self, text, chance):
		ui.ListBoxEx.Item.__init__(self)
		self.textLine = ui.TextLine()
		self.textLine.SetParent(self)
		self.textLine.SetPosition(4, 2)
		self.textLine.SetText(text)
		self.textLine.Show()
		self.chanceLine = ui.TextLine()
		self.chanceLine.SetParent(self)
		self.chanceLine.SetPosition(4, 2)
		self.chanceLine.SetWindowHorizontalAlignRight()
		self.chanceLine.SetHorizontalAlignRight()
		self.chanceLine.SetText(chance)
		self.chanceLine.Show()

	def __del__(self):
		ui.ListBoxEx.Item.__del__(self)

	def SetChance(self, chance):
		self.chanceLine.SetText(chance)

	def SetSize(self, width, height):
		ui.ListBoxEx.Item.SetSize(self, width, height)
		self.chanceLine.SetPosition(8, 2)
		self.chanceLine.UpdateRect()


class CubeOknoWindow(ui.BoardWithTitleBar):
	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)
		self.tooltipItem = None
		self.npcVnum = 0
		self.isUsable = False
		self.xStart = 0
		self.yStart = 0
		self.cubeResultInfos = []
		self.cubeMaterialInfos = {}
		self.cubeResultExtra = {}
		self.selected = -1
		self.placed = []
		self.improvePos = -1
		self.improveVnum = 0
		self.improveBonus = 0
		self.improveCategory = -1
		self.nextRefresh = 0.0
		self.listDirty = False
		self.shownMaterials = []

	def __del__(self):
		ui.BoardWithTitleBar.__del__(self)

	def LoadWindow(self):
		self.AddFlag("movable")
		self.AddFlag("float")
		self.SetSize(362, 470)
		self.SetTitleName(TEXT_TITLE)
		self.SetCloseEvent(ui.__mem_func__(self.__OnCloseButtonClick))
		self.SetCenterPosition()

		self.listBox = ui.ListBoxEx()
		self.listBox.SetParent(self)
		self.listBox.SetPosition(14, 34)
		self.listBox.SetViewItemCount(9)
		self.listBox.SetItemSize(310, 18)
		self.listBox.SetItemStep(21)
		self.listBox.SetSelectEvent(ui.__mem_func__(self.__OnSelectRow))
		self.listBox.Show()

		self.scrollBar = ui.ScrollBar()
		self.scrollBar.SetParent(self)
		self.scrollBar.SetPosition(330, 34)
		self.scrollBar.SetScrollBarSize(21 * 9)
		self.scrollBar.Show()
		self.listBox.SetScrollBar(self.scrollBar)

		self.countLine = self.__Text(14, 228, "")

		self.line = ui.Line()
		self.line.SetParent(self)
		self.line.SetPosition(14, 246)
		self.line.SetSize(334, 0)
		self.line.SetColor(grp.GenerateColor(0.5, 0.45, 0.35, 1.0))
		self.line.Show()

		self.nameLine = self.__Text(14, 252, TEXT_PICK)

		# the result and the materials: a dark box of 32 x 96 each, the icon in its middle
		self.boxes = []
		self.resultSlot = self.__MakeSlot(14, 272)
		self.resultSlot.SetOverInItemEvent(ui.__mem_func__(self.__OverInResult))
		self.resultSlot.SetOverOutItemEvent(ui.__mem_func__(self.__OverOut))
		self.arrowLine = self.__Text(52, 310, ">")
		self.materialSlots = []
		self.materialTexts = []
		for i in xrange(MAX_MATERIALS):
			x = 66 + i * 40
			slot = self.__MakeSlot(x, 272)
			slot.SetOverInItemEvent(lambda trash = 0, col = i: self.__OverInMaterial(col))
			slot.SetOverOutItemEvent(ui.__mem_func__(self.__OverOut))
			self.materialSlots.append(slot)
			text = ui.TextLine()
			text.SetParent(self)
			text.SetPosition(x + 16, 371)
			text.SetHorizontalAlignCenter()
			text.Show()
			self.materialTexts.append(text)

		# the chance-raising slot
		self.improveSlot = ui.SlotWindow()
		self.improveSlot.SetParent(self)
		self.improveSlot.SetPosition(312, 304)
		self.improveSlot.SetSize(32, 32)
		self.improveSlot.AppendSlot(0, 0, 0, 32, 32)
		self.improveSlot.SetSlotBaseImage(SLOT_BASE, 1.0, 1.0, 1.0, 1.0)
		self.improveSlot.SetSelectEmptySlotEvent(ui.__mem_func__(self.__OnImproveDrop))
		self.improveSlot.SetSelectItemSlotEvent(ui.__mem_func__(self.__OnImproveClick))
		self.improveSlot.SetOverInItemEvent(ui.__mem_func__(self.__OverInImprove))
		self.improveSlot.SetOverOutItemEvent(ui.__mem_func__(self.__OverOut))
		self.improveSlot.Show()
		self.improveLabel = ui.TextLine()
		self.improveLabel.SetParent(self)
		self.improveLabel.SetPosition(328, 340)
		self.improveLabel.SetHorizontalAlignCenter()
		self.improveLabel.SetText(TEXT_IMPROVE)
		self.improveLabel.Show()

		self.costLine = self.__Text(14, 392, "")
		self.gayaLine = self.__Text(190, 392, "")
		self.chanceLine = self.__Text(14, 410, "")
		self.resultLine = self.__Text(190, 410, "")

		self.makeButton = self.__Button(95, 434, TEXT_MAKE, self.__OnMake)
		self.closeButton = self.__Button(195, 434, TEXT_CLOSE, self.__OnCloseButtonClick)
		self.__ShowRecipe()

	def __Text(self, x, y, text):
		t = ui.TextLine()
		t.SetParent(self)
		t.SetPosition(x, y)
		t.SetText(text)
		t.Show()
		return t

	def __Button(self, x, y, text, event):
		b = ui.Button()
		b.SetParent(self)
		b.SetPosition(x, y)
		b.SetUpVisual(BUTTON[0])
		b.SetOverVisual(BUTTON[1])
		b.SetDownVisual(BUTTON[2])
		b.SetText(text)
		b.SetEvent(ui.__mem_func__(event))
		b.Show()
		return b

	def __MakeSlot(self, x, y):
		box = ui.Bar()
		box.SetParent(self)
		box.SetPosition(x, y)
		box.SetSize(32, 96)
		box.SetColor(grp.GenerateColor(0.0, 0.0, 0.0, 0.45))
		box.Show()
		self.boxes.append(box)
		slot = ui.SlotWindow()
		slot.SetParent(self)
		slot.SetPosition(x, y)
		slot.SetSize(32, 96)
		slot.AppendSlot(0, 0, 0, 32, 96)
		slot.Show()
		slot.baseY = y
		return slot

	def __PlaceItem(self, slot, vnum, count):
		if not vnum:
			slot.ClearSlot(0)
			slot.RefreshSlot()
			return
		item.SelectItem(vnum)
		sizeY = max(1, min(3, item.GetItemSize()[1]))
		x, y = slot.GetLocalPosition()
		slot.SetSize(32, 32 * sizeY)
		slot.SetPosition(x, slot.baseY + (96 - 32 * sizeY) / 2)
		slot.SetItemSlot(0, vnum, count)
		slot.RefreshSlot()

	# ------------------------------------------------------------------ the interface of uicube.CubeWindow
	def SetItemToolTip(self, tooltipItem):
		self.tooltipItem = tooltipItem

	@ui.WindowDestroy
	def Destroy(self):
		self.tooltipItem = None
		self.listBox = None
		self.scrollBar = None

	def Open(self, npcVnum = 0):
		self.npcVnum = npcVnum
		self.cubeResultInfos = []
		self.cubeMaterialInfos = {}
		self.cubeResultExtra = {}
		self.selected = -1
		self.placed = []
		self.__ClearImprove()
		self.listBox.RemoveAllItems()
		self.resultLine.SetText("")
		title = TEXT_TITLE
		try:
			import nonplayer
			name = nonplayer.GetMonsterName(npcVnum)
			if name:
				title = "%s - %s" % (TEXT_TITLE, name)
		except Exception:
			pass
		self.SetTitleName(title)
		self.__ShowRecipe()
		self.Show()
		self.SetTop()
		self.isUsable = True
		(self.xStart, self.yStart, z) = player.GetMainCharacterPosition()

	def Close(self):
		if self.tooltipItem:
			self.tooltipItem.HideToolTip()
		self.isUsable = False
		self.Hide()
		self.cubeResultInfos = []
		self.cubeMaterialInfos = {}
		self.cubeResultExtra = {}
		self.selected = -1
		self.placed = []
		self.__ClearImprove()

	def AddCubeResultItem(self, itemVnum, count):
		self.cubeResultInfos.append((itemVnum, count))
		self.listDirty = True

	def AddMaterialInfo(self, itemIndex, orderIndex, itemVnum, itemCount):
		columns = self.cubeMaterialInfos.setdefault(itemIndex, [])
		while len(columns) <= orderIndex:
			columns.append([])
		columns[orderIndex].append((itemVnum, itemCount))

	def SetResultExtra(self, itemIndex, gold, chance, gaya, category = -1):
		self.cubeResultExtra[itemIndex] = (gold, chance, gaya, category)
		self.listDirty = True

	def SetImproveInfo(self, vnum, bonus, category):
		self.improveVnum = vnum
		self.improveBonus = bonus
		self.improveCategory = category
		if not vnum:
			self.improvePos = -1
		self.__ShowImprove()
		self.__ShowRecipe()

	def ClearCubeResultItem(self):
		self.cubeResultInfos = []
		self.Refresh()

	def UpdateInfo(self, gold, itemVnum, count):
		pass	# the server's "cube info": the window shows the chosen recipe's own Yang

	def Clear(self):
		self.Refresh()

	def Refresh(self):
		if self.listDirty:
			self.__RebuildList()
		self.__ShowRecipe()

	def OnCubeResult(self, success, itemVnum = 0, count = 0):
		# what the attempt left in the server's window (a kept helmet, the rest of a stack) is taken out before the next
		if success:
			item.SelectItem(itemVnum)
			self.resultLine.SetText(TEXT_SUCCESS % item.GetItemName())
			self.resultLine.SetPackedFontColor(COLOR_OK)
		else:
			self.resultLine.SetText(TEXT_FAIL)
			self.resultLine.SetPackedFontColor(COLOR_BAD)
		self.__ShowImprove()
		self.__ShowRecipe()

	def OnPressEscapeKey(self):
		self.__OnCloseButtonClick()
		return True

	def OnUpdate(self):
		(x, y, z) = player.GetMainCharacterPosition()
		if abs(x - self.xStart) > USE_LIMIT_RANGE or abs(y - self.yStart) > USE_LIMIT_RANGE:
			self.__OnCloseButtonClick()
			return
		if self.listDirty:
			self.__RebuildList()
			self.__ShowRecipe()
		if app.GetTime() >= self.nextRefresh:	# the bag changes - "have / need" every half second
			self.nextRefresh = app.GetTime() + 0.5
			self.__ShowRecipe()
			self.__ShowImprove()

	# ------------------------------------------------------------------ the list
	def __RebuildList(self):
		self.listDirty = False
		keep = self.selected
		self.listBox.RemoveAllItems()
		for i in xrange(len(self.cubeResultInfos)):
			(vnum, count) = self.cubeResultInfos[i]
			item.SelectItem(vnum)
			name = item.GetItemName()
			if count > 1:
				name = "%s x%d" % (name, count)
			extra = self.cubeResultExtra.get(i)
			chance = (extra and extra[1]) and ("%s%%" % extra[1]) or ""
			row = RecipeRow(name, chance)
			self.listBox.AppendItem(row)
		self.countLine.SetText(TEXT_COUNT % len(self.cubeResultInfos))
		if 0 <= keep < len(self.cubeResultInfos):
			self.listBox.SelectIndex(keep)

	def __OnSelectRow(self, row):
		try:
			index = self.listBox.GetItemIndex(row)
		except ValueError:
			return
		if index != self.selected:
			self.selected = index
			self.resultLine.SetText("")
			if 0 <= index < len(self.cubeResultInfos):
				net.SendChatPacket("/cube pick %d" % self.cubeResultInfos[index][0])
		self.__ShowRecipe()

	# ------------------------------------------------------------------ the chosen recipe
	def __Columns(self):
		return self.cubeMaterialInfos.get(self.selected, [])

	def __Extra(self):
		return self.cubeResultExtra.get(self.selected, (0, "", 0, -1))

	def __BestAlternative(self, alternatives):
		# the first alternative the bag has enough of; with none, the one it has most of
		best = None
		for (vnum, count) in alternatives:
			have = _HaveCount(vnum)
			if best is None:
				best = (vnum, count, have)
				continue
			bestOk = best[2] >= best[1]
			if have >= count and not bestOk:
				best = (vnum, count, have)
			elif not bestOk and have > best[2]:
				best = (vnum, count, have)
		return best

	def __ShowRecipe(self):
		self.shownMaterials = []
		if not (0 <= self.selected < len(self.cubeResultInfos)):
			self.nameLine.SetText(TEXT_PICK)
			self.__PlaceItem(self.resultSlot, 0, 0)
			for i in xrange(MAX_MATERIALS):
				self.__PlaceItem(self.materialSlots[i], 0, 0)
				self.materialTexts[i].SetText("")
			for t in (self.costLine, self.gayaLine, self.chanceLine):
				t.SetText("")
			return
		(vnum, count) = self.cubeResultInfos[self.selected]
		item.SelectItem(vnum)
		self.nameLine.SetText(item.GetItemName())
		self.__PlaceItem(self.resultSlot, vnum, count)
		columns = self.__Columns()
		for i in xrange(MAX_MATERIALS):
			if i < len(columns) and columns[i]:
				best = self.__BestAlternative(columns[i])
				self.shownMaterials.append(best)
				self.__PlaceItem(self.materialSlots[i], best[0], best[1])
				self.materialTexts[i].SetText("%d/%d" % (min(best[2], 999999), best[1]))
				self.materialTexts[i].SetPackedFontColor(best[2] >= best[1] and COLOR_OK or COLOR_BAD)
			else:
				self.__PlaceItem(self.materialSlots[i], 0, 0)
				self.materialTexts[i].SetText("")
		(gold, chance, gaya, category) = self.__Extra()
		self.costLine.SetText(TEXT_COST % localeInfo.NumberToMoneyString(gold))
		self.costLine.SetPackedFontColor(player.GetElk() >= gold and COLOR_GOLD or COLOR_BAD)
		if gaya > 0:
			haveGaya = player.GetItemCountByVnum(GAYA_VNUM)
			self.gayaLine.SetText(TEXT_GAYA % (gaya, haveGaya))
			self.gayaLine.SetPackedFontColor(haveGaya >= gaya and COLOR_GAYA or COLOR_BAD)
		else:
			self.gayaLine.SetText("")
		bonus = self.__ImproveBonusFor(category)
		if chance and bonus > 0:
			self.chanceLine.SetText(TEXT_CHANCE_BONUS % (chance, bonus))
		elif chance:
			self.chanceLine.SetText(TEXT_CHANCE % chance)
		else:
			self.chanceLine.SetText("")
		self.chanceLine.SetPackedFontColor(COLOR_OK)

	def __ImproveBonusFor(self, category):
		if self.improveVnum and self.improveBonus > 0 and self.improveCategory == category and category >= 0:
			return self.improveBonus
		return 0

	# ------------------------------------------------------------------ tooltips
	def __OverOut(self):
		if self.tooltipItem:
			self.tooltipItem.HideToolTip()

	def __ShowItemTip(self, vnum):
		if not self.tooltipItem or not vnum:
			return
		self.tooltipItem.ClearToolTip()
		metinSlot = [0 for i in xrange(player.METIN_SOCKET_MAX_NUM)]
		attrSlot = [(0, 0) for i in xrange(player.ATTRIBUTE_SLOT_MAX_NUM)]
		self.tooltipItem.AddItemData(vnum, metinSlot, attrSlot)

	def __OverInResult(self, slotIndex = 0):
		if not (0 <= self.selected < len(self.cubeResultInfos)):
			return
		self.__ShowItemTip(self.cubeResultInfos[self.selected][0])
		(gold, chance, gaya, category) = self.__Extra()
		if self.tooltipItem:
			self.tooltipItem.AppendSpace(5)
			if gold > 0:
				self.tooltipItem.AppendTextLine(TEXT_COST % localeInfo.NumberToMoneyString(gold), COLOR_GOLD)
			if gaya > 0:
				self.tooltipItem.AppendTextLine("Gaya: %d" % gaya, COLOR_GAYA)
			if chance:
				self.tooltipItem.AppendTextLine(TEXT_CHANCE % chance, COLOR_OK)
			self.tooltipItem.ResizeToolTip()

	def __OverInMaterial(self, col):
		columns = self.__Columns()
		if col >= len(columns) or not columns[col] or col >= len(self.shownMaterials):
			return
		self.__ShowItemTip(self.shownMaterials[col][0])
		if self.tooltipItem and len(columns[col]) > 1:	# the +5..+9 of a merged row: any of them
			self.tooltipItem.AppendSpace(5)
			first = True
			for (vnum, count) in columns[col]:
				if not first:
					self.tooltipItem.AppendTextLine(TEXT_OR)
				first = False
				item.SelectItem(vnum)
				self.tooltipItem.AppendTextLine(item.GetItemName(), _HaveCount(vnum) >= count and COLOR_OK or COLOR_BAD)
			self.tooltipItem.ResizeToolTip()

	def __OverInImprove(self, slotIndex = 0):
		if self.improveVnum:
			self.__ShowItemTip(self.improveVnum)
			if self.tooltipItem:
				self.tooltipItem.AppendTextLine(TEXT_CLICK_REMOVE)
				self.tooltipItem.ResizeToolTip()
		elif self.tooltipItem:
			self.tooltipItem.ClearToolTip()
			self.tooltipItem.AppendTextLine(TEXT_IMPROVE)
			self.tooltipItem.AppendTextLine(TEXT_IMPROVE_HINT)
			self.tooltipItem.ResizeToolTip()
			self.tooltipItem.ShowToolTip()

	# ------------------------------------------------------------------ the chance-raising slot
	def __ClearImprove(self):
		self.improvePos = -1
		self.improveVnum = 0
		self.improveBonus = 0
		self.improveCategory = -1
		if hasattr(self, "improveSlot"):
			self.__ShowImprove()

	def __ShowImprove(self):
		if self.improvePos >= 0 and self.improveVnum and player.GetItemIndex(self.improvePos) == self.improveVnum:
			self.improveSlot.SetItemSlot(0, self.improveVnum, player.GetItemCount(self.improvePos))
		else:
			if self.improveVnum and self.improvePos >= 0:	# used up or moved
				self.improvePos = -1
				self.improveVnum = 0
				self.improveBonus = 0
			self.improveSlot.ClearSlot(0)
		self.improveSlot.RefreshSlot()

	def __OnImproveDrop(self, slotIndex = 0):
		if not mouseModule.mouseController.isAttached():
			return
		attachedType = mouseModule.mouseController.GetAttachedType()
		attachedPos = mouseModule.mouseController.GetAttachedSlotNumber()
		mouseModule.mouseController.DeattachObject()
		if player.SLOT_TYPE_INVENTORY != attachedType:
			return
		self.improvePos = attachedPos
		self.improveVnum = 0
		net.SendChatPacket("/cube improve %d" % attachedPos)

	def __OnImproveClick(self, slotIndex = 0):
		if mouseModule.mouseController.isAttached():
			self.__OnImproveDrop(slotIndex)
			return
		self.__ClearImprove()
		net.SendChatPacket("/cube improve -1")
		self.__ShowRecipe()

	# ------------------------------------------------------------------ making
	def __OnMake(self):
		if not (0 <= self.selected < len(self.cubeResultInfos)):
			chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_PICK)
			return
		(gold, chance, gaya, category) = self.__Extra()
		if player.GetElk() < gold:
			chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_NO_GOLD)
			return
		if gaya > 0 and player.GetItemCountByVnum(GAYA_VNUM) < gaya:
			chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_NO_GAYA)
			return
		plan = []
		used = {}
		for alternatives in self.__Columns():
			if not alternatives:
				continue
			best = self.__BestAlternative(alternatives)
			if best[2] < best[1]:
				item.SelectItem(best[0])
				chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_MISSING % item.GetItemName())
				return
			need = best[1]
			for pos in uiCube._CubePositions():
				if need <= 0:
					break
				if pos in used or uiCube._ItemIndex(pos) != best[0]:
					continue
				used[pos] = True
				plan.append(pos)
				need -= uiCube._ItemCount(pos)
		if len(plan) > CUBE_SLOT_MAX:
			chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_TOO_MANY)
			return
		for slot in self.placed:	# what an earlier attempt left in the server's window
			net.SendChatPacket("/cube del %d" % slot)
		self.placed = []
		for slot in xrange(len(plan)):
			uiCube._CubeAdd(slot, plan[slot])
			self.placed.append(slot)
		self.resultLine.SetText("")
		net.SendChatPacket("/cube pick %d" % self.cubeResultInfos[self.selected][0])
		net.SendChatPacket("/cube make")

	def __OnCloseButtonClick(self):
		if self.isUsable:
			self.isUsable = False
			net.SendChatPacket("/cube close")
		self.Close()
