#author: dracaryS

import ui, localeInfo, uiToolTip, constInfo

import app, wndMgr, net, player

ROOT_PATH = "d:/ymir work/ui/game/guild_white_dragon_lair/"

class ScreenEffect(ui.Window):
	def __init__(self):
		ui.Window.__init__(self)
		self.AddFlag("float")
		self.Destroy()

		screenWidth = wndMgr.GetScreenWidth()
		screenHeight = wndMgr.GetScreenHeight()

		self.SetSize(screenWidth, screenHeight)

		image = ui.ExpandedImageBox()
		image.SetParent(self)
		image.LoadImage("d:/ymir work/ui/whitedragon_damage_01.dds")
		image.SetScale(float(screenWidth)/800.0, float(screenHeight)/600.0)
		image.Show()
		self.image = image

		keyboardBG = ui.ImageBox()
		keyboardBG.SetParent(self)
		keyboardBG.LoadImage(ROOT_PATH + "freezing_keyboard.sub")
		keyboardBG.SetWindowHorizontalAlignCenter()
		keyboardBG.SetPosition(0, screenHeight - (keyboardBG.GetHeight() + 100))
		keyboardBG.Show()
		self.keyboardBG = keyboardBG

		keyboardSpaceBtn = ui.Button()
		keyboardSpaceBtn.SetParent(keyboardBG)
		keyboardSpaceBtn.SetUpVisual(ROOT_PATH + "freezing_space_bar_default.sub")
		keyboardSpaceBtn.SetOverVisual(ROOT_PATH + "freezing_space_bar_over.sub")
		keyboardSpaceBtn.SetDownVisual(ROOT_PATH + "freezing_space_bar_down.sub")
		keyboardSpaceBtn.SetEvent(ui.__mem_func__(self.__ClickSpace))
		keyboardSpaceBtn.SetPosition(136, 185)
		keyboardSpaceBtn.Show()
		self.keyboardSpaceBtn = keyboardSpaceBtn

		keyboardSpaceBarEffect = ui.AniImageBox()
		keyboardSpaceBarEffect.SetParent(keyboardSpaceBtn)
		keyboardSpaceBarEffect.SetDelay(3)
		for i in range(1, 8 + 1):
			keyboardSpaceBarEffect.AppendImage(ROOT_PATH + "freezing_space_bar_effect_0" + str(i) + ".sub")
		keyboardSpaceBarEffect.SetPosition(keyboardSpaceBtn.GetWidth() / 2 - 256 / 2, keyboardSpaceBtn.GetHeight() / 2 - 256 / 2)
		keyboardSpaceBarEffect.OnEndFrame = ui.__mem_func__(self.__OnEndFrameEffect)
		self.keyboardSpaceBarEffect = keyboardSpaceBarEffect

	def OnKeyDown(self, key):
		if app.DIK_SPACE == key:
			self.__ClickSpace()
			return True
		return False

	def __OnEndFrameEffect(self):
		self.keyboardSpaceBarEffect.Hide()

	def __ClickSpace(self):
		self.keyboardSpaceBarEffect.ResetFrame()
		self.keyboardSpaceBarEffect.Show()

		self.clickCount -= 1
		if self.clickCount == 0:
			net.SendChatPacket("/balathor unpoly")
			self.AddWave(0)

	def Destroy(self):
		self.Clear()
		self.keyboardSpaceBarEffect = None
		self.keyboardSpaceBtn = None
		self.keyboardBG = None
		self.image = None

	def Clear(self):
		self.alphaRotation = False
		self.alphaVal = 0.0
		self.waveCount = 0
		self.waveIndex = 0
		self.sleepTime = 0.0
		self.clickCount = 0
		self.Unlock()
		self.Hide()

	def AddWave(self, waveCount):
		if waveCount == 0:
			self.Clear()
			return

		self.clickCount = app.GetRandom(4, 8)

		if self.IsShow():
			self.waveCount += waveCount
		else:
			self.MakeEffect(waveCount)

	def MakeEffect(self, waveCount):
		self.alphaRotation = True
		self.alphaVal = 0.0
		self.waveCount = waveCount
		self.waveIndex = 1
		self.sleepTime = 0.0
		self.Show()
		self.SetTop()
		self.Lock()
		self.OnUpdate()

	def OnUpdate(self):
		if not self.IsShow():
			return

		if self.sleepTime > app.GetTime():
			return

		if not self.alphaRotation:
			self.alphaVal -= 0.015

			if self.alphaVal <= (0.3 if self.waveCount != self.waveIndex else 0.05):
				self.alphaVal = 0.3
				self.alphaRotation = not self.alphaRotation

				if self.waveCount == self.waveIndex:
					if player.GetRace() == 20498:
						self.AddWave(1)
					else:
						self.AddWave(0)
		else:
			self.alphaVal += 0.015
			if self.alphaVal >= 1.0:
				self.alphaVal = 1.0
				self.alphaRotation = not self.alphaRotation

				self.sleepTime = app.GetTime() + 0.08

				self.waveIndex += 1

		self.image.SetAlpha(self.alphaVal)

class Window(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.__LoadWindow()

	def Destroy(self):
		self.ClearDictionary()
		self.Hide()

	def __LoadWindow(self):
		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "uiscript/guildwhitedragonlairwindow.py")
		except:
			import exception
			exception.Abort("uiGuildWhiteDragon.Window.__LoadWindow")

		GetChild = self.GetChild

		GetChild("boss_name").SetText(localeInfo.GUILD_WHITE_DRAGON_LAIR_UI_BOSS_NAME_TOOLTIP)
		GetChild("remain_broken_egg_text_01").SetText(localeInfo.GUILD_WHITE_DRAGON_LAIR_UI_BROKEN_EGG_INFO_1)
		GetChild("singijeon_name").SetText(localeInfo.GUILD_WHITE_DRAGON_LAIR_UI_SINGIJEON_NAME_TOOLTIP)

		boss_img = GetChild("boss_img")
		boss_img.SAFE_SetStringEvent("MOUSE_OVER_IN", self.__OverInBoss)
		boss_img.SAFE_SetStringEvent("MOUSE_OVER_OUT", self.__OverOut)

		broken_egg_img = GetChild("broken_egg_img")
		broken_egg_img.SAFE_SetStringEvent("MOUSE_OVER_IN", self.__OverInBrokenEgg)
		broken_egg_img.SAFE_SetStringEvent("MOUSE_OVER_OUT", self.__OverOut)

		singijeon_slot = GetChild("singijeon_slot")
		singijeon_slot.SetOverInItemEvent(ui.__mem_func__(self.__OverInItem))
		singijeon_slot.SetOverOutItemEvent(ui.__mem_func__(self.__OverOut))

	def __OverInItem(self, slot_index):
		interface = constInfo.GetInterfaceInstance()
		if not interface:
			return
		tooltipItem = interface.tooltipItem
		
		tooltipItem.ClearToolTip()
		tooltipItem.SetThinBoardSize(0)
		tooltipItem.AutoAppendNewTextLineResize(localeInfo.GUILD_WHITE_DRAGON_LAIR_UI_SINGIJEON_TOOLTIP % self.hwatcha_count)
		tooltipItem.ShowToolTip()

	def __OverInBoss(self):
		interface = constInfo.GetInterfaceInstance()
		if not interface:
			return
		tooltipItem = interface.tooltipItem

		tooltipItem.ClearToolTip()
		tooltipItem.SetThinBoardSize(0)
		tooltipItem.AutoAppendNewTextLineResize(localeInfo.GUILD_WHITE_DRAGON_LAIR_UI_HIDDEN_BOSS_NAME_TOOLTIP)
		tooltipItem.ShowToolTip()

	def __OverInBrokenEgg(self):
		interface = constInfo.GetInterfaceInstance()
		if not interface:
			return
		tooltipItem = interface.tooltipItem

		tooltipItem.ClearToolTip()
		tooltipItem.SetThinBoardSize(0)
		tooltipItem.AutoAppendNewTextLineResize(localeInfo.GUILD_WHITE_DRAGON_LAIR_UI_BROKEN_EGG_TOOLTIP % self.egg_fail_count)
		tooltipItem.ShowToolTip()

	def __OverOut(self):
		interface = constInfo.GetInterfaceInstance()
		if interface:
			interface.tooltipItem.HideToolTip()

	def Set(self, balathor_hp, balathor_maxhp, balathor_rage, balathor_rage_max, egg_fail_count, hwatcha_count, hwatcha_hp, hwatcha_maxhp):
		GetChild = self.GetChild

		if balathor_hp == 0 and balathor_maxhp == 0:
			self.Hide()
			return
		else:
			if not self.IsShow():
				self.Show()

		self.egg_fail_count = egg_fail_count
		self.hwatcha_count = hwatcha_count

		GetChild("remain_broken_egg_text_02").SetText(localeInfo.GUILD_WHITE_DRAGON_LAIR_UI_BROKEN_EGG_INFO_2 % egg_fail_count)

		singijeon_slot = GetChild("singijeon_slot")
		singijeon_slot.SetItemSlot(0, 30345, hwatcha_count)
		singijeon_slot.RefreshSlot()

		gauge_count = 5
		expGauge = [GetChild("gauge_" + str(i)) for i in xrange(gauge_count)]
		balathor_rage = min(balathor_rage, balathor_rage_max)
		balathor_rage = max(balathor_rage, 0)
		balathor_rage_max = max(balathor_rage_max, 0)

		quarterPoint = balathor_rage_max / gauge_count
		FullCount = 0

		if 0 != quarterPoint:
			FullCount = min(gauge_count, balathor_rage / quarterPoint)

		for i in xrange(gauge_count):
			expGauge[i].Hide()

		for i in xrange(FullCount):
			expGauge[i].SetRenderingRect(0.0, 0.0, 0.0, 0.0)
			expGauge[i].Show()

		if 0 != quarterPoint:
			if FullCount < gauge_count:
				Percentage = float(balathor_rage % quarterPoint) / quarterPoint - 1.0
				expGauge[FullCount].SetRenderingRect(0.0, Percentage, 0.0, 0.0)
				expGauge[FullCount].Show()
		
		if FullCount == gauge_count:
			for i in xrange(gauge_count):
				GetChild("shine_gauge_" + str(i)).Show()
		else:
			for i in xrange(gauge_count):
				GetChild("shine_gauge_" + str(i)).Hide()

		GetChild("boss_hp_gague").SetPercentage(balathor_hp, balathor_maxhp)
		if not hwatcha_maxhp:
			GetChild("singijeon_slot_img").Hide()
			GetChild("singijeon_thin_board").Hide()
		else:
			GetChild("singijeon_slot_img").Show()
			GetChild("singijeon_thin_board").Show()
			GetChild("singijeon_hp_gague").SetPercentage(hwatcha_hp, hwatcha_maxhp)
