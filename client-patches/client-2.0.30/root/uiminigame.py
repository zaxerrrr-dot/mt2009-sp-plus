# MT2009_PLUS_FISH_PUZZLE_V2 - the event banner of the owner's package "Mini Game Fish Event (17.3)" (uiMiniGame.py,
# uiscript minigamewindow.py / minigamedialog.py): the banner beside the minimap while a banner mini game runs (the
# fish puzzle: the server's GC 223 ENABLE), a click opens the list of its games, a game's button opens its window.
# Owned by uifishpuzzle.py (module-level, as our other mini games - interfacemodule only hides / shows the banner).
# The banner stands left of the event hub's "E" button (uiscript minigamewindow.py; the package's x was under it).
#
# Python 2.7 as the client has it.

import ui
import uiScriptLocale
import wndMgr
import app
import uiminigameutil

if getattr(app, "ENABLE_FISH_EVENT", 0):
	import uiminigamefishevent


class MiniGameDialog(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.isLoaded = 0

		self.board = None
		self.closeButton = None
		self.buttonDict = {}

		self.__LoadWindow()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def Destroy(self):
		self.isLoaded = 0

		self.board = None
		self.closeButton = None

		self.buttonDict = {}
		self.ClearDictionary()

	def Show(self):
		self.__LoadWindow()
		ui.ScriptWindow.Show(self)

	def Close(self):
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def __LoadWindow(self):
		if self.isLoaded == 1:
			return

		self.isLoaded = 1

		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "uiscript/minigamedialog.py")
		except:
			uiminigameutil.LoadError("MiniGameDialog.LoadWindow.LoadObject")

		try:
			self.board = self.GetChild("board")
			self.closeButton = self.GetChild("close_button")
			self.closeButton.SetEvent(ui.__mem_func__(self.Close))
		except:
			uiminigameutil.LoadError("MiniGameDialog.LoadWindow.BindObject")

		self.Hide()

	def AppendButton(self, name, func):
		if self.buttonDict.has_key(name):
			return

		button = ui.Button()
		button.SetParent(self.board)
		button.SetPosition(10, (10 * (len(self.buttonDict) + 1)) + len(self.buttonDict) * 25)
		button.SetUpVisual("d:/ymir work/ui/public/XLarge_Button_01.sub")
		button.SetOverVisual("d:/ymir work/ui/public/XLarge_Button_02.sub")
		button.SetDownVisual("d:/ymir work/ui/public/XLarge_Button_03.sub")

		if name:
			button.SetText(name)

		if func:
			button.SetEvent(ui.__mem_func__(func))

		button.Show()
		self.buttonDict[name] = button

	def DeleteButton(self, name):
		if not self.buttonDict.has_key(name):
			return

		self.buttonDict[name].Hide()
		del self.buttonDict[name]

	def DeleteAllButton(self):
		for button in self.buttonDict.values():
			button.Hide()
			del button

		self.buttonDict.clear()

	def RefreshDialog(self):
		self.board.SetSize(200, (25 * (len(self.buttonDict) + 1)) + (10 * ((len(self.buttonDict) + 1) + 1)))
		self.SetSize(200, (25 * (len(self.buttonDict) + 1)) + (10 * ((len(self.buttonDict) + 1) + 1)))
		self.closeButton.SetPosition(10, (10 * (len(self.buttonDict) + 1)) + len(self.buttonDict) * 25)


class MiniGameWindow(ui.ScriptWindow):
	def __init__(self):
		self.isLoaded = 0

		self.miniGameDialog = None
		self.eventBannerButton = None
		self.bannerEnabled = False
		self.bannerHidden = False

		self.fishGame = None
		self.tooltipItem = None
		self.wndInterface = None
		self.wndInventory = None

		ui.ScriptWindow.__init__(self)

		self.__LoadWindow()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def Show(self):
		self.__LoadWindow()
		ui.ScriptWindow.Show(self)

	def Close(self):
		self.Hide()

	def Hide(self):
		if self.miniGameDialog:
			self.miniGameDialog.Hide()

		wndMgr.Hide(self.hWnd)

	def Destroy(self):
		self.isLoaded = 0

		if self.miniGameDialog:
			self.miniGameDialog.Destroy()
			self.miniGameDialog = None

		if self.fishGame:
			self.fishGame.Destroy()
			self.fishGame = None

		self.eventBannerButton = None
		self.tooltipItem = None
		self.wndInterface = None
		self.wndInventory = None
		self.ClearDictionary()

	def __LoadWindow(self):
		if self.isLoaded == 1:
			return

		self.isLoaded = 1

		try:
			self.__LoadScript("uiscript/minigamewindow.py")
		except:
			uiminigameutil.LoadError("MiniGameWindow.LoadWindow.LoadObject")

		try:
			self.eventBannerButton = ui.Button()
			self.eventBannerButton.SetParent(self.GetChild("mini_game_window"))
			self.eventBannerButton.SetPosition(0, 0)
			self.eventBannerButton.SetUpVisual("d:/ymir work/ui/minigame/banner.sub")
			self.eventBannerButton.SetOverVisual("d:/ymir work/ui/minigame/banner.sub")
			self.eventBannerButton.SetDownVisual("d:/ymir work/ui/minigame/banner.sub")
			self.eventBannerButton.SetEvent(ui.__mem_func__(self.__ClickIntegrationEventBannerButton))
			self.eventBannerButton.Hide()
		except:
			uiminigameutil.LoadError("MiniGameWindow.LoadWindow.EventBannerButton.BindObject")

		self.miniGameDialog = MiniGameDialog()
		self.miniGameDialog.Hide()

		self.Show()

	def __LoadScript(self, fileName):
		pyScrLoader = ui.PythonScriptLoader()
		pyScrLoader.LoadScriptFile(self, fileName)

	def __ClickIntegrationEventBannerButton(self):
		if not self.miniGameDialog:
			return

		if self.miniGameDialog.IsShow():
			self.miniGameDialog.Close()
		else:
			self.miniGameDialog.Show()
			self.miniGameDialog.SetTop()

	def IntegrationMiniGame(self, enable):
		self.bannerEnabled = enable
		if enable and not self.bannerHidden:
			self.eventBannerButton.Show()
		else:
			self.eventBannerButton.Hide()

		if self.fishGame:
			self.fishGame.Destroy()
			self.fishGame = None

		# the game window always (the board's pieces follow ENABLE; the hub opens it after the event too),
		# the banner's button only while the event is shown
		if getattr(app, "ENABLE_FISH_EVENT", 0):
			self.__CreateFishGame()

		if self.miniGameDialog:
			self.miniGameDialog.DeleteAllButton()

			if False == enable:
				self.miniGameDialog.Hide()
			else:
				if getattr(app, "ENABLE_FISH_EVENT", 0):
					self.miniGameDialog.AppendButton(uiScriptLocale.BANNER_FISH_BUTTON, self.__ClickFishEventButton)

			self.miniGameDialog.RefreshDialog()

	def __CreateFishGame(self):
		if self.fishGame:
			return
		self.fishGame = uiminigameutil.SafeCreate(uiminigamefishevent.MiniGameFish, uiScriptLocale.BANNER_FISH_BUTTON)
		if not self.fishGame:
			return

		if self.tooltipItem:
			self.fishGame.SetItemToolTip(self.tooltipItem)

		if self.wndInterface:
			self.fishGame.BindInterface(self.wndInterface)

		if self.wndInventory:
			self.fishGame.BindInventory(self.wndInventory)

	# the event hub's button and "FP open" while the banner is off (the board can be finished after the event)
	def GetFishGame(self):
		if getattr(app, "ENABLE_FISH_EVENT", 0):
			self.__CreateFishGame()
		return self.fishGame

	def MiniGameFishUse(self, shape, useCount):
		if self.fishGame:
			self.fishGame.MiniGameFishUse(shape, useCount)

	def MiniGameFishAdd(self, pos, shape):
		if self.fishGame:
			self.fishGame.MiniGameFishAdd(pos, shape)

	def MiniGameFishReward(self, vnum):
		if self.fishGame:
			self.fishGame.MiniGameFishReward(vnum)

	def MiniGameFishCount(self, count):
		if self.fishGame:
			self.fishGame.MiniGameFishCount(count)

	def __ClickFishEventButton(self):
		if self.miniGameDialog:
			self.miniGameDialog.Close()

		if self.fishGame:
			self.fishGame.Open()

	def SetItemToolTip(self, tooltip):
		self.tooltipItem = tooltip

	def BindInterface(self, interface):
		self.wndInterface = interface

	def BindInventory(self, inventory):
		self.wndInventory = inventory

	# interfacemodule's HideAllWindows / ShowDefaultWindows
	def HideMiniGameDialog(self):
		self.bannerHidden = True
		if self.eventBannerButton:
			if self.eventBannerButton.IsShow():
				self.eventBannerButton.Hide()

		if self.miniGameDialog:
			if self.miniGameDialog.IsShow():
				self.miniGameDialog.Hide()

	def ShowMiniGameDialog(self):
		self.bannerHidden = False
		if self.eventBannerButton and self.bannerEnabled:
			self.eventBannerButton.Show()
