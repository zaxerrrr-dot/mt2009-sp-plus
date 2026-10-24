# MT2009_PLUS_ITEMSHOP_V3_V1 - the second ItemShop ("V3 Itemshop Premium" web package), next to
# the old one for the owner's test (24 October 2026: "add it NEXT TO the old one, as a second one,
# under some hotkey"). Shift+F12 by default (keybind.py "itemshop_v3", rebindable in Skroty
# klawiszowe); the old shop, its taskbar coin and the Kolo Losu (F12) stay as they are.
#
# The page is the web shop of the itemshop container under /shop3/ (linux-port/docker/itemshop/
# app/shop3): the same catalogue (itemshop.ishop_items), the same Smocze Monety / Smocze Znaki and
# the same delivery (player.item_award) as the old web shop, in the look of the big servers' shop
# (1016 x 655, its own CSS and scripts).
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
# Python 2.7 as the client has it; the texts are CP1250 escapes.

import app
import net
import ui
import wndMgr

PAGE_W = 1016	# body.ingame #page of the shop's design.css
PAGE_H = 655
BORDER_X = 10
BORDER_TOP = 30
BORDER_BOTTOM = 10
PENDING_SECONDS = 15.0

TITLE = 'ItemShop (nowy)'
TEXT_WAIT = '\xa3adowanie sklepu...'
TEXT_NO_BROWSER = ('Je\x9cli sklep si\xea nie pokazuje, ten klient nie ma jeszcze', 'wbudowanej przegl\xb9darki (potrzebny nowy plik exe klienta).')

_data = {'window': None, 'pending': 0.0}


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
		pos = self.GetGlobalPosition()
		if pos == self.lastPos:
			return
		self.lastPos = pos
		try:
			app.MoveWebPage(self.__Rect())
		except:
			self.browserOpen = False


def GetWindow():
	if not _data['window']:
		_data['window'] = ItemShopV3Window()
	return _data['window']


def Open():
	# The server answers with "mall <signed url>" (game.py __InGameShop_Show -> TakeMallUrl).
	_data['pending'] = app.GetTime() + PENDING_SECONDS
	net.SendChatPacket('/in_game_mall')


def ToggleWindow():
	wnd = _data['window']
	if wnd and wnd.IsShow():
		wnd.Close()
	else:
		Open()


def TakeMallUrl(url):
	# True when the answer was this window's request (and it is open now); False leaves it to
	# the old mall window.
	if _data['pending'] <= 0.0 or app.GetTime() > _data['pending']:
		_data['pending'] = 0.0
		return False
	_data['pending'] = 0.0
	shopUrl = _ShopUrl(url)
	if not shopUrl:
		return False
	GetWindow().OpenUrl(shopUrl)
	return True


def DestroyWindow():
	wnd = _data['window']
	if wnd:
		wnd.Destroy()
	_data['window'] = None
	_data['pending'] = 0.0
