# MT2009_PLUS_FISH_PUZZLE_V2 - Event Rybacki - Puzzle (Wedkarskie Puzzle): the glue between game.py, the event hub
# and the owner's package "Mini Game Fish Event (17.3)" (uiminigame.py: the banner, uiminigamefishevent.py: the game).
#
# The game needs the exe with ENABLE_FISH_EVENT (client-patches/exe; packets CG 219 / GC 223, server fish_puzzle.cpp).
# With it, Register() (game.py, once the game window runs - again after every warp) says "/fishpuzzle hello": from
# then on the server sends this client the event's packets (an older exe would stop at their unknown header, so the
# server sends nothing without the hello). The exe calls the game window's MiniGameFishEvent / MiniGameFishUse /
# MiniGameFishAdd / MiniGameFishReward, game.py hands them here. The server's "FP open" (a box used from the
# inventory) opens the board; the event hub's "Event Rybacki - Puzzle" button opens the game too.
# An older exe: no hello, no opener - the hub says the game comes with a client update, the server says the same
# when a box is used.
#
# V1 (the chat-command puzzle window, uiscript/fishpuzzlewindow.py) is gone.
#
# Python 2.7 as the client has it.

import app
import net

EVENT_KEY = 'fishpuzzle'

_data = {'window': None, 'interface': None, 'banner_hidden': False}


def HasExe():
	return getattr(app, 'ENABLE_FISH_EVENT', 0) and hasattr(net, 'SendUseFishBox')


def _Bind(window, interface):
	if not window or not interface:
		return
	tooltip = getattr(interface, 'tooltipItem', None)
	if tooltip:
		window.SetItemToolTip(tooltip)
	window.BindInterface(interface)
	inventory = getattr(interface, 'wndInventory', None)
	if inventory:
		window.BindInventory(inventory)


def GetWindow():
	if not HasExe():
		return None
	if not _data['window']:
		import uiminigame
		import uiminigameutil
		_data['window'] = uiminigameutil.SafeCreate(uiminigame.MiniGameWindow, 'W\xeadkarskie Puzzle')
		if _data['window']:
			_Bind(_data['window'], _data['interface'])
			if _data['banner_hidden']:
				_data['window'].HideMiniGameDialog()
	return _data['window']


def BindInterface(interface):
	if interface is _data['interface']:
		return
	_data['interface'] = interface
	_Bind(_data['window'], interface)


def OpenWindow():
	window = GetWindow()
	if not window:
		return
	game = window.GetFishGame()
	if game:
		game.Open()


def OpenGame():
	window = GetWindow()
	if not window:
		return
	game = window.GetFishGame()
	if game:
		game.OpenGame()


def Register():
	"""game.py, with the event hub: the hub's button opens the game; the server is told this exe has it."""
	if not HasExe():
		return
	try:
		import uiingameevent
		uiingameevent.RegisterOpener(EVENT_KEY, OpenWindow)
	except ImportError:
		pass
	net.SendChatPacket('/fishpuzzle hello')


def DestroyWindow():
	window = _data['window']
	if window:
		window.Hide()
		window.Destroy()
	_data['window'] = None
	_data['interface'] = None


def SetBannerHidden(hidden):
	"""interfacemodule's HideAllWindows / ShowDefaultWindows."""
	_data['banner_hidden'] = hidden
	window = _data['window']
	if not window:
		return
	if hidden:
		window.HideMiniGameDialog()
	else:
		window.ShowMiniGameDialog()


# --------------------------------------------------------------- the exe (game.py relays)

def OnEvent(interface, isEnable, useCount):
	BindInterface(interface)
	window = GetWindow()
	if not window:
		return
	window.IntegrationMiniGame(True if isEnable else False)
	window.MiniGameFishCount(useCount)


def OnUse(shape, useCount):
	window = GetWindow()
	if window:
		window.MiniGameFishUse(shape, useCount)


def OnAdd(pos, shape):
	window = GetWindow()
	if window:
		window.MiniGameFishAdd(pos, shape)


def OnReward(vnum):
	window = GetWindow()
	if window:
		window.MiniGameFishReward(vnum)


# game.py "FP": the server's lines ("FP open": a box used from the inventory).
def OnCommand(sub='', *args):
	if sub == 'open':
		OpenGame()
