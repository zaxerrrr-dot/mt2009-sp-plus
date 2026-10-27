# MT2009_PLUS_ITEMSHOP_V3_V1 - the second ItemShop ("V3 Itemshop Premium" web package), next to
# the old one for the owner's test (24 October 2026: "add it NEXT TO the old one, as a second one,
# under some hotkey"). Shift+F12 by default (keybind.py "itemshop_v3", rebindable in Skroty
# klawiszowe); the old shop, its taskbar coin and the Kolo Losu (F12) stay as they are.
#
# The page is the web shop of the itemshop container under /shop3/ (linux-port/docker/itemshop/
# app/shop3): since MT2009_PLUS_ITEMSHOP_V3_V3 the in-game shop's catalogue (common.itemshop_items, its
# categories, promotions, flash offers, vouchers and premium page), the same Smocze Monety / Smocze Znaki
# and the ItemShop storage (player.item_award), in the look of the big servers' shop (1016 x 655, its own
# CSS and scripts; the wheel over the page scrolls it - exe CWebBrowser WebBrowser_ForwardMouseWheel).
#
# The link has to be signed by the server for the account (sas = md5(pid . account id . key)), and
# only the server knows the account id: Open() asks it with /in_game_mall, the same command the old
# web shop used, and game.py hands the "mall <url>" answer here while the request is fresh. The
# answer names /ishop (the old shop's entry, cmd_general.cpp ACMD(do_in_game_mall)); this window
# opens /shop3/ with the same pid and sas, which the new shop checks the same way.
#
# The page is drawn by the client's embedded browser (app.ShowWebPage - one at a time, so the old
# mall window and the bots' chat page are closed first). The exe of 3.x starts that browser and
# puts it in IE11 mode (client-patches/exe, MT2009_PLUS_ITEMSHOP_V3_V1); an older exe draws
# nothing, and the board then says so.
#
# MT2009_PLUS_ITEMSHOP_V3_MAIN_V1 (Yohara line, the owner 27 Oct 2026: "Na yohara ustaw nowy itemshop look like
# global, jako glowny itemshop"): this is THE ItemShop now. Every way into the old in-game window (the taskbar coin,
# the system menu's ItemShop button, the minimap's ItemShop button, the Dodatkowy ekwipunek's ItemShop button - all
# send uiItemShop.EVENT_OPEN_ITEMSHOP), the server's "itemshop_open" and an unasked "mall <url>" open this window
# (uiitemshop.py, game.py) when IsMain() - the exe can draw the page (app.TakeWebPageCommand, exe of
# MT2009_PLUS_ITEMSHOP_V3_V4). An older exe keeps the old in-game window, which would otherwise be no shop at all.
# Shift+F12 (keybind "itemshop_v3") still opens it.
#
# Python 2.7 as the client has it; the texts are CP1250 escapes.

import app
import chat
import net
import ui
import wndMgr

PAGE_W = 1016	# body.ingame #page of the shop's design.css
PAGE_H = 655
BORDER_X = 10
BORDER_TOP = 30
BORDER_BOTTOM = 10
PENDING_SECONDS = 15.0

TITLE = 'ItemShop'	# MT2009_PLUS_ITEMSHOP_V3_MAIN_V1: the main shop, no longer "(nowy)"
TEXT_WAIT = '\xa3adowanie sklepu...'
TEXT_NO_BROWSER = ('Je\x9cli sklep si\xea nie pokazuje, ten klient nie ma jeszcze', 'wbudowanej przegl\xb9darki (potrzebny nowy plik exe klienta).')
# MT2009_PLUS_ITEMSHOP_V3_ONLY_V1: what an exe without the shop's browser (no app.TakeWebPageCommand) gets instead of a shop.
TEXT_NEED_EXE = 'Potrzebny jest nowy plik exe klienta \x96 zaktualizuj klienta.'

_data = {'window': None, 'pending': 0.0}

# MT2009_PLUS_ITEMSHOP_V3_V4: the game windows the page may ask for (game/<name>/): name -> (module, function)
GAME_WINDOWS = {'wheel': ('uiwheel', 'OpenWindow')}
_TakeWebPageCommand = getattr(app, 'TakeWebPageCommand', None)


def _ShopUrl(url):
	# "http://host:port/ishop?pid=..&c=..&sid=..&sas=.." -> "http://host:port/shop3/?pid=..&sas=.."
	base, sep, query = url.partition('?')
	if not sep:
		return None
	i = base.rfind('/ishop')
	if i < 0:
		return None
	return base[:i] + '/shop3/?' + query


class ItemShopV3Window(ui.BoardWithTitleBar):
	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)
		self.AddFlag('movable')
		self.AddFlag('float')
		self.SetTitleName(TITLE)
		self.SetCloseEvent(ui.__mem_func__(self.Close))

		self.pageW = PAGE_W
		self.pageH = PAGE_H
		self.browserOpen = False
		self.lastPos = None

		self.lines = []
		for n in xrange(3):
			line = ui.TextLine()
			line.SetParent(self)
			line.SetHorizontalAlignCenter()
			line.Show()
			self.lines.append(line)
		self.__Layout()

	def __del__(self):
		ui.BoardWithTitleBar.__del__(self)

	def Destroy(self):
		self.__CloseBrowser()
		self.lines = []
		self.Hide()

	def __Layout(self):
		# Smaller screens get a smaller page (the shop scrolls), never a window off the screen.
		sw = wndMgr.GetScreenWidth()
		sh = wndMgr.GetScreenHeight()
		self.pageW = max(320, min(PAGE_W, sw - 2 * BORDER_X - 10))
		self.pageH = max(240, min(PAGE_H, sh - BORDER_TOP - BORDER_BOTTOM - 40))
		w = self.pageW + 2 * BORDER_X
		h = self.pageH + BORDER_TOP + BORDER_BOTTOM
		self.SetSize(w, h)
		y = BORDER_TOP + self.pageH / 2 - 24
		for n in xrange(len(self.lines)):
			self.lines[n].SetPosition(w / 2, y + n * 18)

	def __Rect(self):
		x, y = self.GetGlobalPosition()
		sx, sy = x + BORDER_X, y + BORDER_TOP
		return (sx, sy, sx + self.pageW, sy + self.pageH)

	def __CloseBrowser(self):
		if not self.browserOpen:
			return
		self.browserOpen = False
		try:
			app.HideWebPage()
		except:
			pass

	def OpenUrl(self, url):
		self.__Layout()
		self.lines[0].SetText(TEXT_WAIT)
		self.lines[1].SetText(TEXT_NO_BROWSER[0])
		self.lines[2].SetText(TEXT_NO_BROWSER[1])
		if not self.IsShow():
			self.SetCenterPosition()
			self.Show()
			self.SetTop()
		# One embedded browser at a time: the old mall window (uiweb) and the bots' chat page
		# use the same one.
		try:
			app.HideWebPage()
		except:
			pass
		self.browserOpen = False
		self.lastPos = self.GetGlobalPosition()
		if _TakeWebPageCommand:	# MT2009_PLUS_ITEMSHOP_V3_V4: no request left over from a page closed before it was taken
			try:
				_TakeWebPageCommand()
			except:
				pass
		try:
			app.ShowWebPage(url, self.__Rect())
			self.browserOpen = True
		except:
			self.browserOpen = False

	def Close(self):
		self.__CloseBrowser()
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def OnUpdate(self):
		if not self.browserOpen:
			return
		# MT2009_PLUS_ITEMSHOP_V3_V4: the page's "Kolo Losu" tab (a link to the shop's game/wheel/) - the exe keeps the
		# name instead of loading it (CWebBrowser.c, app.TakeWebPageCommand); the shop closes (the browser would lie over
		# any game window) and the wheel's window opens. An older exe has no such function and loads the shop's page
		# for the link, which names the window's key.
		if _TakeWebPageCommand:
			try:
				command = _TakeWebPageCommand()
			except:
				command = ''
			if command in GAME_WINDOWS:
				self.Close()
				try:
					getattr(__import__(GAME_WINDOWS[command][0]), GAME_WINDOWS[command][1])()
				except:
					pass
				return
		pos = self.GetGlobalPosition()
		if pos == self.lastPos:
			return
		self.lastPos = pos
		try:
			app.MoveWebPage(self.__Rect())
		except:
			self.browserOpen = False


def IsMain():
	# MT2009_PLUS_ITEMSHOP_V3_MAIN_V1: this window replaces the old in-game ItemShop.
	# MT2009_PLUS_ITEMSHOP_V3_ONLY_V1 (the owner, 27 Oct 2026): always - the old shop is closed on the Yohara line. An exe
	# that cannot draw the page (no app.TakeWebPageCommand, MT2009_PLUS_ITEMSHOP_V3_V4) gets TEXT_NEED_EXE instead of
	# the old shop (CanShow, Open, TakeMallUrl).
	return True


def CanShow():
	# MT2009_PLUS_ITEMSHOP_V3_ONLY_V1: whether this exe draws the shop's page (the exe with app.TakeWebPageCommand has
	# the working embedded browser too); otherwise the player is told to update the client.
	if _TakeWebPageCommand:
		return True
	chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_NEED_EXE)
	return False


def TakesKeys():
	# MT2009_PLUS_ITEMSHOP_V3_V4: while the page is open the keys are the page's - game.py OnKeyDown / OnKeyUp and
	# updateable.py act on no hotkey then (the game reads the keyboard by DirectInput, so a letter typed in the
	# shop's search box also reached the game). Esc and the shop's own key still close it.
	wnd = _data['window']
	return bool(wnd and wnd.browserOpen and wnd.IsShow())


def GetWindow():
	if not _data['window']:
		_data['window'] = ItemShopV3Window()
	return _data['window']


def Open():
	# The server answers with "mall <signed url>" (game.py __InGameShop_Show -> TakeMallUrl).
	if not CanShow():	# MT2009_PLUS_ITEMSHOP_V3_ONLY_V1: an old exe asks the server for nothing
		_data['pending'] = 0.0
		return
	_data['pending'] = app.GetTime() + PENDING_SECONDS
	net.SendChatPacket('/in_game_mall')


def ToggleWindow():
	wnd = _data['window']
	if wnd and wnd.IsShow():
		wnd.Close()
	else:
		Open()


def TakeMallUrl(url, unasked=False):
	# True when the answer was this window's request (and it is open now); False leaves it to
	# the old mall window. MT2009_PLUS_ITEMSHOP_V3_MAIN_V1: unasked=True takes any "mall" answer (a typed
	# /in_game_mall, a quest's game.web_mall) - the old web shop is no player's way in on the Yohara line.
	if not unasked and (_data['pending'] <= 0.0 or app.GetTime() > _data['pending']):
		_data['pending'] = 0.0
		return False
	_data['pending'] = 0.0
	shopUrl = _ShopUrl(url)
	if not shopUrl:
		return False
	# MT2009_PLUS_ITEMSHOP_V3_ONLY_V1: with an exe that cannot draw the page the answer is taken (no old web window)
	# and the player is told to update the client.
	if not CanShow():
		return True
	GetWindow().OpenUrl(shopUrl)
	return True


def DestroyWindow():
	wnd = _data['window']
	if wnd:
		wnd.Destroy()
	_data['window'] = None
	_data['pending'] = 0.0
