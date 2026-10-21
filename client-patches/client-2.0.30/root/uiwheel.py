# MT2009_PLUS_KOLA_V1: "Kolo Losu" - the wheel of the ItemShop, in the game (F12).
#
# The same wheel as the ItemShop's page (itemshop/pages/wheel.php): one
# server-side system, the same per-account state (wheel, tier, keys, timer),
# the same pools and chances, the price of a spin in Smocze Monety and the
# prize into the ItemShop's storage. The game server does every spin
# (playerbot_wheel.h, "/kolo"); this window only shows it, the original's look
# and animation rebuilt with the client's images (root/mt2009_ui/kola/, made
# with tools/kola/make_kola_ui.py, which also writes koladata.py).
#
# Client -> server:  /kolo  |  /kolo krec  |  /kolo opusc
# Server -> client (game.py "WOF" -> OnCommand):
#   WOF kstate <enabled> <wheel> <tier> <maxTier> <keys> <keysNeeded> <secondsLeft> <cost> <balance>
#   WOF kcosts <c1> <c2> <c3>
#   WOF kpool <tier> <special 0/1> <vnum>|<count>|<weight x100>|<srcIcon>#...   (appended)
#   WOF kpoolend
#   WOF klayout <vnum>|<count>|<srcIcon>#...   (16 fields)
#   WOF kspin <position 1-16> <keyHit 0/1> <special 0/1>
#   WOF kfail
# F12 or uiwheel.ToggleWindow() opens it.
#
# Python 2.7 as the client has it; the texts are CP1250 escapes.

import math

import app
import chat
import grp
import item
import net
import ui
import uiToolTip

import koladata

UI = koladata.UI
# MT2009_PLUS_KOLA_UI_V2: the window is the page's game area (.crk-game,
# 900x489) with no title bar - the whole background art, the wheel in the
# middle, the ladder left, the small welcome box bottom right (bottom 35,
# right 10, 192 wide, as high as its rows), "Mozliwe nagrody" bottom left and
# a small close button; dragged by any free spot of the art.
CONTENT_W = 900
CONTENT_H = 489
WHEEL_X = 232	# the 436x436 wheel, centred: (900 - 436) / 2
WHEEL_Y = 26	# (489 - 436) / 2
LADDER_X = 15	# .crk-stages left:15, centred in height
BOX_W = 192	# .crk-welcome
BOX_RIGHT = 10
BOX_BOTTOM = 35
BOX_PAD = 10
BOX_INNER = BOX_W - 2 * BOX_PAD
BOX_MAX_H = 320	# box.jpg's height
BOX_X = CONTENT_W - BOX_RIGHT - BOX_W
CLOSE_SIZE = 24
CLOSE_X = CONTENT_W - CLOSE_SIZE - 6
CLOSE_Y = 6
NAME_X = LADDER_X	# the wheel's name, small, top left
NAME_Y = 9
PRICES_Y = CONTENT_H - 32	# .crk-prices: bottom 0, left 0
EXIT_W = 144	# exit.png
TIMER_W = 172	# timer.jpg
TIMER_H = 50
ICON = 45	# a field's icon box

TITLE = 'Ko\xb3o Losu'
TEXT_SPIN = ('ZAKR\xca\xc6', 'TERAZ!')
TEXT_SPINNING = 'KR\xcaCI SI\xca...'
TEXT_WELCOME = 'Witaj na poziomie %d'
TEXT_COST_1 = 'Zakr\xea\xe6 ko\xb3em za jedyne'
TEXT_COST_2 = '%d!'	# MT2009_PLUS_KOLA_UI_V2: "... za jedyne [coin] 16!" like the page
TEXT_BALANCE = 'Twoje Smocze Monety: %d'
TEXT_BACK = 'Powr\xf3t na poziom 1'
TEXT_EXIT = 'Opu\x9c\xe6 ten poziom'
TEXT_LAST = 'Ostatnia nagroda:'
TEXT_LAST_NONE = 'Zakr\xea\xe6 ko\xb3em.'
TEXT_PRICES = 'Mo\xbfliwe nagrody'
TEXT_OFF = 'Ko\xb3o Losu jest teraz wy\xb3\xb9czone.'
TEXT_WON = 'Ko\xb3o Losu: wygrywasz %s. Nagroda czeka w magazynie ItemShopu.'
TEXT_TIER = 'poziom %d'
TEXT_SPECIAL = 'G\xb3\xf3wne nagrody'
TEXT_STANDARD = 'Nagrody standardowe'
TEXT_MAIN_CHANCE = 'Szansa na g\xb3\xf3wn\xb9 nagrod\xea: %s'
TEXT_HOW = 'Ko\xb3o ma 16 p\xf3l, ka\xbfde z szans\xb9 1/16. Przed ka\xbfdym obrotem pola s\xb9 losowane od nowa.'
TEXT_HOW_2 = 'Procent przy nagrodzie to szansa, \xbfe trafi na pole swojego rodzaju.'
TEXT_PAGE = 'Strona %d/%d'
TEXT_KEY = 'Ko\xb3o Losu: zdobywasz klucz (%d/%d).'
TEXT_GATE = 'Ko\xb3o Losu: brama otwarta - poziom %d!'

BROWN = grp.GenerateColor(0.4, 0.1765, 0.0706, 1.0)	# #662d12
DARK = grp.GenerateColor(0.2353, 0.1176, 0.0863, 1.0)	# #3c1e16
GOLD = grp.GenerateColor(0.949, 0.902, 0.624, 1.0)	# #f2e69f
LIGHT = grp.GenerateColor(0.9490, 0.9058, 0.7568, 1.0)
SPECIAL_COLOR = grp.GenerateColor(1.0, 0.7843, 0.0, 1.0)


def BoldFontName():
	try:
		import gamefont
		return gamefont.GetCurrentFontLarge() + 'b'
	except Exception:
		return ''


def ItemName(vnum):
	try:
		item.SelectItem(vnum)
		return item.GetItemName()
	except Exception:
		return str(vnum)


def PrizeName(vnum, count):
	name = ItemName(vnum)
	if count > 1:
		name = '%dx %s' % (count, name)
	return name


def IconPath(vnum, src):
	if src > 0:
		return UI + 'i/%d.png' % src
	try:
		item.SelectItem(vnum)
		return item.GetIconImageFileName()
	except Exception:
		return ''


def Percent(weight100):
	whole = weight100 / 100
	frac = weight100 % 100
	if frac == 0:
		return '%d%%' % whole
	if frac % 10 == 0:
		return '%d,%d%%' % (whole, frac / 10)
	return '%d,%02d%%' % (whole, frac)


def MainChance(tier):
	n = len(koladata.SPECIAL_FIELDS.get(tier, (1,)))
	return Percent(n * 10000 / 16)


def Clock(seconds):
	seconds = max(0, int(seconds))
	return '%02d:%02d:%02d' % (seconds / 3600, (seconds % 3600) / 60, seconds % 60)


# the original's easings
def EaseP(t):
	return 0.5 - math.cos(t * math.pi) / 2.0


def EaseM(t):
	return math.sqrt(max(0.0, 1.0 - (t - 1.0) ** 2))


def EaseH(t):
	return t


def BoxRows(costLines, last, timer, message):
	"""MT2009_PLUS_KOLA_UI_V2: the welcome box's rows from its top,
	[(name, y, height)], and the box's height (the box grows upwards)."""
	rows = [('welcome', 19), ('cost1', 17)]
	if costLines > 1:
		rows.append(('cost2', 17))
	rows.append(('balance', 17))
	if last:
		rows.append(('last', 36))
	if timer:
		rows.append(('timer', TIMER_H + 6))
		rows.append(('exit', 32))
	if message:
		rows.append(('message', 17))
	out = []
	y = BOX_PAD - 2
	for name, h in rows:
		out.append((name, y, h))
		y += h
	return out, min(BOX_MAX_H, y + BOX_PAD - 2)


def _Int(value, default=0):
	try:
		return int(value)
	except (ValueError, TypeError):
		return default


def ParseEntries(text, fields):
	out = []
	for part in text.split('#'):
		values = part.split('|')
		if len(values) < fields:
			continue
		out.append(tuple([_Int(v) for v in values[:fields]]))
	return out


_data = {
	'window': None,
	'state': None,	# (enabled, wheel, tier, maxTier, keys, need, secondsLeft, cost, balance)
	'costs': (0, 0, 0),
	'poolIn': {},
	'pool': {},	# tier -> {1: [...special], 0: [...standard]}, entries (vnum, count, weight100, src)
	'layout': [],
}


class Sprite(object):
	"""An ExpandedImageBox with a box (x, y, w, h) and an alpha the
	tweens animate; the image keeps its proportions inside the box."""

	def __init__(self, parent, path=''):
		img = ui.ExpandedImageBox()
		img.SetParent(parent)
		self.img = img
		self.bw = 1
		self.bh = 1
		self.x = 0.0
		self.y = 0.0
		self.w = 0.0
		self.h = 0.0
		self.alpha = 1.0
		self.path = ''
		self.home = (0, 0)
		if path:
			self.Load(path)

	def Load(self, path):
		if path == self.path or not path:
			return
		self.path = path
		self.img.SetScale(1.0, 1.0)
		self.img.LoadImage(path)
		self.bw = max(1, self.img.GetWidth())
		self.bh = max(1, self.img.GetHeight())

	def Box(self, x, y, w, h):
		self.x, self.y, self.w, self.h = float(x), float(y), float(w), float(h)
		self.Apply()

	def Apply(self):
		if not self.path:
			return
		s = max(0.0, min(self.w / self.bw, self.h / self.bh))
		dw = self.bw * s
		dh = self.bh * s
		self.img.SetScale(s, s)
		self.img.SetPosition(int(round(self.x + (self.w - dw) / 2.0)), int(round(self.y + (self.h - dh) / 2.0)))
		self.img.SetAlpha(self.alpha)

	def Show(self):
		self.img.Show()

	def Hide(self):
		self.img.Hide()


class PrizeWindow(ui.BoardWithTitleBar):
	"""Mozliwe nagrody: the pools of each tier with their chances."""

	WIDTH = 540
	HEIGHT = 470
	ROWS = 10
	COLS = 2
	ROW_H = 30
	TOP = 104

	def __init__(self, owner):
		ui.BoardWithTitleBar.__init__(self)
		self.owner = owner
		self.children = []
		self.tabs = []
		self.tabTiers = []
		self.cells = []
		self.rows = []
		self.tier = 1
		self.page = 0
		self.SetSize(self.WIDTH, self.HEIGHT)
		self.SetTitleName(TEXT_PRICES)
		self.SetCloseEvent(ui.__mem_func__(self.Close))
		self.AddFlag('movable')
		self.AddFlag('float')
		self.SetCenterPosition()

		for i, text in enumerate((TEXT_HOW, TEXT_HOW_2)):
			line = ui.TextLine()
			line.SetParent(self)
			line.SetPosition(16, 62 + i * 14)
			line.SetText(text)
			line.Show()
			self.children.append(line)
		chance = ui.TextLine()
		chance.SetParent(self)
		chance.SetPosition(self.WIDTH - 16, 38)
		chance.SetHorizontalAlignRight()
		chance.SetPackedFontColor(SPECIAL_COLOR)
		chance.Show()
		self.chance = chance

		for r in xrange(self.ROWS):
			for c in xrange(self.COLS):
				x = 16 + c * 258
				y = self.TOP + r * self.ROW_H
				icon = Sprite(self)
				icon.img.SAFE_SetStringEvent('MOUSE_OVER_IN', self.__OverIn, len(self.cells))
				icon.img.SAFE_SetStringEvent('MOUSE_OVER_OUT', self.__OverOut)
				name = ui.TextLine()
				name.SetParent(self)
				name.SetPosition(x + 34, y + 8)
				pct = ui.TextLine()
				pct.SetParent(self)
				pct.SetPosition(x + 246, y + 8)
				pct.SetHorizontalAlignRight()
				pct.SetPackedFontColor(SPECIAL_COLOR)
				self.cells.append((x, y, icon, name, pct))

		bottom = self.TOP + self.ROWS * self.ROW_H + 8
		page = ui.TextLine()
		page.SetParent(self)
		page.SetPosition(self.WIDTH / 2, bottom + 4)
		page.SetHorizontalAlignCenter()
		page.SetPackedFontColor(LIGHT)
		self.pageText = page
		self.prevButton = self.__Button('small', '<', ui.__mem_func__(self.__Prev))
		self.prevButton.SetPosition(self.WIDTH / 2 - 80, bottom)
		self.nextButton = self.__Button('small', '>', ui.__mem_func__(self.__Next))
		self.nextButton.SetPosition(self.WIDTH / 2 + 80 - self.nextButton.GetWidth(), bottom)

	def __del__(self):
		ui.BoardWithTitleBar.__del__(self)

	def Open(self, tier):
		for tab in self.tabs:
			tab.Hide()
		self.tabs = []
		self.tabTiers = sorted(_data['pool'].keys()) or [1]
		for i, t in enumerate(self.tabTiers):
			tab = self.__Button('middle', TEXT_TIER % t, ui.__mem_func__(self.SelectTier), t)
			tab.SetPosition(16 + i * 92, 34)
			tab.Show()
			self.tabs.append(tab)
		self.SelectTier(tier if tier in self.tabTiers else self.tabTiers[0])
		self.Show()
		self.SetTop()

	def __Button(self, image, text, event, *args):
		button = ui.Button()
		button.SetParent(self)
		button.SetUpVisual('d:/ymir work/ui/public/%s_button_01.sub' % image)
		button.SetOverVisual('d:/ymir work/ui/public/%s_button_02.sub' % image)
		button.SetDownVisual('d:/ymir work/ui/public/%s_button_03.sub' % image)
		button.SetText(text)
		button.SetEvent(event, *args)
		self.children.append(button)
		return button

	def SelectTier(self, tier):
		self.tier = tier
		self.page = 0
		pools = _data['pool'].get(tier, {})
		rows = []
		for special, title in ((1, TEXT_SPECIAL), (0, TEXT_STANDARD)):
			entries = pools.get(special, [])
			if not entries:
				continue
			rows.append((title, special))
			while len(rows) % self.COLS:
				rows.append(None)
			for e in entries:
				rows.append((e, special))
			while len(rows) % self.COLS:
				rows.append(None)
		self.rows = rows
		self.chance.SetText(TEXT_MAIN_CHANCE % MainChance(tier))
		for i, tab in enumerate(self.tabs):
			if self.tabTiers[i] == tier:
				tab.Down()
			else:
				tab.SetUp()
		self.__Refresh()

	def __Pages(self):
		per = self.ROWS * self.COLS
		return max(1, (len(self.rows) + per - 1) / per)

	def __Refresh(self):
		per = self.ROWS * self.COLS
		start = self.page * per
		for i, (x, y, icon, name, pct) in enumerate(self.cells):
			row = self.rows[start + i] if start + i < len(self.rows) else None
			if row is None:
				icon.Hide()
				name.Hide()
				pct.Hide()
				continue
			what, special = row
			if isinstance(what, str):
				icon.Hide()
				name.SetText(what)
				name.SetPackedFontColor(SPECIAL_COLOR if special else GOLD)
				name.SetPosition(x, y + 8)
				name.Show()
				pct.Hide()
				continue
			vnum, count, weight, src = what
			icon.Load(IconPath(vnum, src))
			icon.Box(x, y, 28, 28)
			icon.Show()
			text = PrizeName(vnum, count)
			if len(text) > 30:
				text = text[:28] + '...'
			name.SetText(text)
			name.SetPackedFontColor(LIGHT)
			name.SetPosition(x + 34, y + 8)
			name.Show()
			pct.SetText(Percent(weight))
			pct.Show()
		pages = self.__Pages()
		if pages > 1:
			self.pageText.SetText(TEXT_PAGE % (self.page + 1, pages))
			self.pageText.Show()
			self.prevButton.Show()
			self.nextButton.Show()
		else:
			self.pageText.Hide()
			self.prevButton.Hide()
			self.nextButton.Hide()

	def __Prev(self):
		if self.page > 0:
			self.page -= 1
			self.__Refresh()

	def __Next(self):
		if self.page + 1 < self.__Pages():
			self.page += 1
			self.__Refresh()

	def __OverIn(self, index):
		per = self.ROWS * self.COLS
		i = self.page * per + index
		if i < len(self.rows) and self.rows[i] and not isinstance(self.rows[i][0], str):
			self.owner.ShowItemToolTip(self.rows[i][0][0], self.rows[i][1])

	def __OverOut(self):
		self.owner.HideItemToolTip()

	def Close(self):
		self.owner.HideItemToolTip()
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True


class WheelWindow(ui.Window):	# MT2009_PLUS_KOLA_UI_V2: no board, no title bar
	def __init__(self):
		ui.Window.__init__(self)
		self.tooltipItem = uiToolTip.ItemToolTip()
		self.tooltipItem.HideToolTip()
		self.prizeWindow = None
		self.wheelId = 0
		self.tier = 1
		self.maxTier = 3
		self.keys = 0
		self.need = 4
		self.cost = 0
		self.balance = 0
		self.enabled = 1
		self.deadline = 0.0
		self.resyncSent = False
		self.waiting = False	# a spin asked for, no answer yet
		self.animating = False	# the spin runs until the prize is told (the button locked)
		self.playing = False	# the field icons are shown (until 3 s after the prize)
		self.pendingState = None
		self.layout = []
		self.spinGen = 0
		self.idleGen = 0
		self.spinClicked = 0.0
		self.spinInfo = (1, 0, 0, 1, 0)
		self.timers = []	# [time, function]
		self.queues = {}	# id(sprite) -> [sprite, [steps]]: each step starts when the one before ends
		self.running = {}	# id(sprite) -> [sprite, start, duration, {prop: (from, to)}, ease, done]
		self.ladder = []
		self.slotImages = {}	# (tier, k) -> ImageBox
		self.lastPrize = None
		self.idle = {}	# (tier, pos) -> Sprite
		self.__Build()

	def __del__(self):
		ui.Window.__del__(self)

	# ------------------------------------------------------------------ build

	def __Text(self, parent, x, y, color=BROWN, bold=False, center=False):
		line = ui.TextLine()
		line.SetParent(parent)
		if bold:
			font = BoldFontName()
			if font:
				try:
					line.SetFontName(font)
				except Exception:
					pass
		line.SetPosition(x, y)
		if center:
			line.SetHorizontalAlignCenter()
		line.SetPackedFontColor(color)
		line.Show()
		return line

	def __Image(self, parent, path, x, y):
		img = ui.ImageBox()
		img.SetParent(parent)
		img.LoadImage(path)
		img.SetPosition(x, y)
		img.Show()
		return img

	def __Build(self):
		# MT2009_PLUS_KOLA_UI_V2: the art is the window; the pictures let the
		# clicks through (not_pick), so a click on the art drags the window
		self.SetSize(CONTENT_W, CONTENT_H)
		self.AddFlag('movable')
		self.AddFlag('float')
		self.SetCenterPosition()

		bg = ui.ExpandedImageBox()
		bg.SetParent(self)
		bg.SetPosition(0, 0)
		bg.SetSize(CONTENT_W, CONTENT_H)
		bg.AddFlag('not_pick')
		bg.Show()
		self.bg = bg
		self.bgPath = ''

		# the ladder (left)
		ladder = ui.ExpandedImageBox()
		ladder.SetParent(bg)
		ladder.LoadImage(UI + 'ladder.jpg')
		ladder.AddFlag('not_pick')
		ladder.Show()
		self.ladderBg = ladder

		# the wheel: slices, pointer, ring, keys, spinner, button, the fields
		wheel = ui.Window()
		wheel.SetParent(bg)
		wheel.SetPosition(WHEEL_X, WHEEL_Y)
		wheel.SetSize(436, 436)
		wheel.AddFlag('not_pick')	# MT2009_PLUS_KOLA_UI_V2
		wheel.Show()
		self.wheel = wheel
		self.slices = self.__Image(wheel, UI + 'slices_1.png', 0, 0)
		self.slices.AddFlag('not_pick')
		self.pointer = self.__Image(wheel, UI + 'pointer_00.png', 0, 0)
		self.pointer.AddFlag('not_pick')
		self.pointer.Hide()
		self.ring = self.__Image(wheel, UI + 'ring_1.png', 0, 0)
		self.ring.AddFlag('not_pick')
		self.keySprites = {}
		for f in koladata.KEY_FIELDS:
			x, y = koladata.KEY_POS[f - 1]
			key = Sprite(wheel, UI + 'key_1.png')
			key.img.AddFlag('not_pick')
			key.home = (x, y)
			key.Box(x, y, 56, 56)
			key.Show()
			self.keySprites[f] = key
		self.spinner = self.__Image(wheel, UI + 'spinner_00.png', 0, 0)
		self.spinner.AddFlag('not_pick')
		button = ui.ImageBox()
		button.SetParent(wheel)
		button.LoadImage(UI + 'btn.png')
		button.SetPosition(155, 156)
		button.SetEvent(ui.__mem_func__(self.__OnSpin), 'mouse_click')
		button.Show()
		self.button = button
		self.buttonLines = []
		for i in xrange(3):
			line = self.__Text(button, 62, 34 + i * 20, BROWN, True, True)
			line.AddFlag('not_pick')
			self.buttonLines.append(line)
		# MT2009_PLUS_KOLA_UI_V2: "(16 [coin])" like the page
		self.buttonCost = self.__Text(button, 0, 74, BROWN, True)
		self.buttonCost.AddFlag('not_pick')
		self.buttonCoin = self.__Image(button, UI + 'coin.png', 0, 73)
		self.buttonCoin.AddFlag('not_pick')
		self.buttonParen = self.__Text(button, 0, 74, BROWN, True)
		self.buttonParen.AddFlag('not_pick')
		self.buttonParen.SetText(')')
		self.rewards = []
		for i in xrange(16):
			x, y = koladata.FIELD_POS[i]
			sprite = Sprite(wheel)
			sprite.img.SAFE_SetStringEvent('MOUSE_OVER_IN', self.__OverField, i)
			sprite.img.SAFE_SetStringEvent('MOUSE_OVER_OUT', self.__OverOut)
			sprite.home = (x, y)
			sprite.Box(x, y, ICON, ICON)
			sprite.Hide()
			self.rewards.append(sprite)

		# MT2009_PLUS_KOLA_UI_V2: the wheel's name, small, top left (the page has none;
		# the title bar that showed it is gone)
		self.title = self.__Text(self, NAME_X, NAME_Y, GOLD, True)
		self.title.SetOutline()
		self.title.AddFlag('not_pick')

		# MT2009_PLUS_KOLA_UI_V2: the welcome box (.crk-welcome), bottom right; its
		# rows (BoxRows) and height follow the state, the art above stays free
		box = ui.ExpandedImageBox()
		box.SetParent(self)
		box.LoadImage(UI + 'box.jpg')
		box.AddFlag('not_pick')
		box.Show()
		self.box = box
		self.welcome = self.__Text(box, BOX_PAD, 0, BROWN, True)
		self.costLine1 = self.__Text(box, BOX_PAD, 0, BROWN)
		self.costLine1.SetText(TEXT_COST_1)
		self.coin = self.__Image(box, UI + 'coin.png', 0, 0)
		self.coin.AddFlag('not_pick')
		self.costLine2 = self.__Text(box, 0, 0, BROWN, True)
		self.balanceLine = self.__Text(box, BOX_PAD, 0, DARK)
		lastIcon = Sprite(box)
		lastIcon.img.SAFE_SetStringEvent('MOUSE_OVER_IN', self.__OverLast)
		lastIcon.img.SAFE_SetStringEvent('MOUSE_OVER_OUT', self.__OverOut)
		self.lastIcon = lastIcon
		self.lastTitle = self.__Text(box, BOX_PAD + 36, 0, BROWN)
		self.lastTitle.SetText(TEXT_LAST)
		self.lastName1 = self.__Text(box, BOX_PAD + 36, 0, DARK, True)
		timer = self.__Image(box, UI + 'timer.jpg', BOX_PAD, 0)
		timer.AddFlag('not_pick')
		self.timerBox = timer
		self.backLine = self.__Text(timer, TIMER_W / 2, 9, DARK, False, True)
		self.backLine.SetText(TEXT_BACK)
		self.clockLine = self.__Text(timer, TIMER_W / 2, 27, DARK, True, True)
		exitButton = ui.Button()
		exitButton.SetParent(box)
		exitButton.SetUpVisual(UI + 'exit.png')
		exitButton.SetOverVisual(UI + 'exit_h.png')
		exitButton.SetDownVisual(UI + 'exit_h.png')
		exitButton.SetText(TEXT_EXIT)
		exitButton.SetEvent(ui.__mem_func__(self.__OnExit))
		self.exitButton = exitButton
		self.message = self.__Text(box, BOX_PAD, 0, DARK)

		prices = ui.Button()
		prices.SetParent(self)
		prices.SetUpVisual(UI + 'prices.png')
		prices.SetOverVisual(UI + 'prices_h.png')
		prices.SetDownVisual(UI + 'prices_h.png')
		prices.SetPosition(0, PRICES_Y)
		prices.SetEvent(ui.__mem_func__(self.__OnPrices))
		prices.Show()
		self.pricesButton = prices
		# MT2009_PLUS_KOLA_UI_V2: the label left (padding 8) in #f2e69f, like the page
		self.pricesText = self.__Text(prices, 8, 9, GOLD)
		self.pricesText.SetText(TEXT_PRICES)
		self.pricesText.AddFlag('not_pick')

		# MT2009_PLUS_KOLA_UI_V2: close, in the red of the page's exit button
		close = ui.Button()
		close.SetParent(self)
		close.SetUpVisual(UI + 'close.png')
		close.SetOverVisual(UI + 'close_h.png')
		close.SetDownVisual(UI + 'close_h.png')
		close.SetPosition(CLOSE_X, CLOSE_Y)
		close.SetEvent(ui.__mem_func__(self.Close))
		close.Show()
		self.closeButton = close

		self.__ApplyState()

	# --------------------------------------------------------------- helpers

	def After(self, ms, func):
		self.timers.append([app.GetTime() + ms / 1000.0, func])

	def Queue(self, sprite, step):
		"""step: (targets(sprite) -> {prop: (from, to)}, ms, ease, done or None),
		started after the steps already queued on the sprite (the original's H())."""
		key = id(sprite)
		entry = self.queues.get(key)
		if entry is None:
			entry = [sprite, []]
			self.queues[key] = entry
		entry[1].append(step)
		if key not in self.running:
			self.__NextStep(key)

	def Stop(self, sprite):
		key = id(sprite)
		self.queues.pop(key, None)
		self.running.pop(key, None)

	def __NextStep(self, key):
		entry = self.queues.get(key)
		if not entry or not entry[1]:
			self.queues.pop(key, None)
			self.running.pop(key, None)
			return
		sprite = entry[0]
		targets, ms, ease, done = entry[1].pop(0)
		self.running[key] = [sprite, app.GetTime(), max(0.001, ms / 1000.0), targets(sprite), ease, done]

	def __Tick(self):
		now = app.GetTime()
		for key in self.running.keys():
			run = self.running.get(key)
			if not run:
				continue
			sprite, start, dur, props, ease, done = run
			t = min(1.0, (now - start) / dur)
			e = ease(t)
			for prop, (a, b) in props.items():
				setattr(sprite, prop, a + (b - a) * e)
			sprite.Apply()
			if t >= 1.0 and self.running.get(key) is run:
				self.running.pop(key, None)
				if done:
					done()
				if key not in self.running:
					self.__NextStep(key)
		if self.timers:
			due = [t for t in self.timers if t[0] <= now]
			if due:
				self.timers = [t for t in self.timers if t[0] > now]
				for t in due:
					t[1]()

	# ------------------------------------------------------------------- open

	def Open(self):
		self.Show()
		self.SetTop()
		if not self.animating and not self.playing:
			self.__StartIdle()
		net.SendChatPacket('/kolo')

	def Close(self):
		if self.animating or self.playing:
			self.__Finish(True)
		self.__StopIdle()
		self.HideItemToolTip()
		if self.prizeWindow:
			self.prizeWindow.Close()
		self.Hide()

	def Destroy(self):
		self.HideItemToolTip()
		self.timers = []
		self.queues = {}
		self.running = {}
		if self.prizeWindow:
			self.prizeWindow.Hide()
			self.prizeWindow = None
		self.tooltipItem = None
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def ShowItemToolTip(self, vnum, special):
		if not self.tooltipItem or not vnum:
			return
		self.tooltipItem.SetItemToolTip(vnum)
		if special:
			self.tooltipItem.AppendTextLine(TEXT_SPECIAL, SPECIAL_COLOR)
		self.tooltipItem.ShowToolTip()

	def HideItemToolTip(self):
		if self.tooltipItem:
			self.tooltipItem.HideToolTip()

	def __OverField(self, index):
		if self.playing and index < len(self.layout):
			special = (index + 1) in koladata.SPECIAL_FIELDS.get(self.spinInfo[3], ())
			self.ShowItemToolTip(self.layout[index][0], special)

	def __OverLast(self):
		if self.lastPrize:
			self.ShowItemToolTip(self.lastPrize[0], self.lastPrize[3])

	def __OverOut(self):
		self.HideItemToolTip()

	# ------------------------------------------------------------------ state

	def OnState(self, values):
		if self.animating:
			# told after the prize, like the original (the key/tier change shows then)
			self.pendingState = values
			return
		self.__TakeState(values)
		self.__ApplyState()

	def __TakeState(self, values):
		(enabled, wheel, tier, maxTier, keys, need, seconds, cost, balance) = values
		self.enabled = enabled
		if wheel != self.wheelId and wheel in koladata.WHEELS:
			self.__StopIdle()
			for sprite in self.idle.values():
				sprite.Hide()
			self.idle = {}
			self.wheelId = wheel
			if self.IsShow() and not self.playing:
				self.__StartIdle()
		self.tier = max(1, tier)
		self.maxTier = max(1, maxTier)
		self.keys = max(0, keys)
		self.need = max(1, need)
		self.cost = cost
		self.balance = balance
		self.deadline = app.GetTime() + seconds if (tier > 1 and seconds > 0) else 0.0
		self.resyncSent = False

	def __ApplyState(self):
		info = koladata.WHEELS.get(self.wheelId)
		if info:
			self.title.SetText(info['name'])
			if self.bgPath != info['bg']:
				self.bgPath = info['bg']
				self.bg.LoadImage(info['bg'])
		else:
			self.title.SetText(TITLE)
		lvl = min(3, self.tier)
		self.slices.LoadImage(UI + 'slices_%d.png' % lvl)
		self.ring.LoadImage(UI + 'ring_%d.png' % lvl)
		for f, key in self.keySprites.items():
			self.Stop(key)
			if self.tier >= self.maxTier:
				key.Hide()
			else:
				key.Load(UI + 'key_%d.png' % min(2, self.tier))
				key.alpha = 1.0
				key.Box(key.home[0], key.home[1], 56, 56)
				key.Show()
		self.__BuildLadder()
		self.__SetButton(self.animating or self.waiting)
		self.__RefreshPanel()

	def __RefreshPanel(self):
		"""MT2009_PLUS_KOLA_UI_V2: fills the welcome box and lays its rows out."""
		if not self.enabled:
			self.message.SetText(TEXT_OFF)
		elif self.message.GetText() == TEXT_OFF:
			self.message.SetText('')
		self.welcome.SetText(TEXT_WELCOME % self.tier)
		self.costLine2.SetText(TEXT_COST_2 % self.cost)
		(w1, h1) = self.costLine1.GetTextSize()
		(w2, h2) = self.costLine2.GetTextSize()
		costLines = 1 if w1 + 4 + 16 + 4 + w2 <= BOX_INNER else 2
		self.balanceLine.SetText(TEXT_BALANCE % self.balance)
		timer = self.tier > 1
		message = self.message.GetText() != ''
		rows, height = BoxRows(costLines, self.lastPrize is not None, timer, message)
		at = dict([(name, y) for (name, y, h) in rows])
		self.box.SetPosition(BOX_X, CONTENT_H - BOX_BOTTOM - height)
		self.box.SetRenderingRect(0.0, 0.0, 0.0, -1.0 + float(height) / float(BOX_MAX_H))
		self.welcome.SetPosition(BOX_PAD, at['welcome'])
		self.costLine1.SetPosition(BOX_PAD, at['cost1'])
		if costLines == 1:
			cx, cy = BOX_PAD + w1 + 4, at['cost1']
		else:
			cx, cy = BOX_PAD, at['cost2']
		self.coin.SetPosition(cx, cy)
		self.costLine2.SetPosition(cx + 20, cy)
		self.balanceLine.SetPosition(BOX_PAD, at['balance'])
		if 'last' in at:
			y = at['last']
			self.lastIcon.Box(BOX_PAD, y + 2, 30, 30)
			self.lastIcon.Show()
			self.lastTitle.SetPosition(BOX_PAD + 36, y + 2)
			self.lastTitle.Show()
			self.lastName1.SetPosition(BOX_PAD + 36, y + 17)
			self.lastName1.Show()
		else:
			self.lastIcon.Hide()
			self.lastTitle.Hide()
			self.lastName1.Hide()
		if timer:
			self.timerBox.SetPosition(BOX_PAD, at['timer'] + 3)
			self.timerBox.Show()
			self.exitButton.SetPosition((BOX_W - EXIT_W) / 2, at['exit'])
			self.exitButton.Show()
			self.__RefreshClock()
		else:
			self.timerBox.Hide()
			self.exitButton.Hide()
		if message:
			self.message.SetPosition(BOX_PAD, at['message'])
			self.message.Show()
		else:
			self.message.Hide()

	def __RefreshClock(self):
		left = self.deadline - app.GetTime() if self.deadline else 0
		self.clockLine.SetText(Clock(math.ceil(max(0, left))))
		if self.tier > 1 and left <= 0 and not self.resyncSent and not self.animating and not self.waiting:
			# the server takes the player back to tier 1; ask for the state
			self.resyncSent = True
			net.SendChatPacket('/kolo')

	def __SetButton(self, running):
		self.buttonLines[2].SetText('')
		if running:
			self.button.LoadImage(UI + 'btn_run.png')
			self.buttonLines[0].SetText('')
			self.buttonLines[1].SetText(TEXT_SPINNING)
		else:
			self.button.LoadImage(UI + 'btn.png')
			self.buttonLines[0].SetText(TEXT_SPIN[0])
			self.buttonLines[1].SetText(TEXT_SPIN[1])
		# MT2009_PLUS_KOLA_UI_V2: "(16 [coin])", centred under TERAZ!
		if running or not self.cost:
			self.buttonCost.Hide()
			self.buttonCoin.Hide()
			self.buttonParen.Hide()
			return
		self.buttonCost.SetText('(%d' % self.cost)
		(w1, h1) = self.buttonCost.GetTextSize()
		(w2, h2) = self.buttonParen.GetTextSize()
		x = 62 - (w1 + 3 + 16 + 2 + w2) / 2
		self.buttonCost.SetPosition(x, 74)
		self.buttonCoin.SetPosition(x + w1 + 3, 73)
		self.buttonParen.SetPosition(x + w1 + 3 + 16 + 2, 74)
		self.buttonCost.Show()
		self.buttonCoin.Show()
		self.buttonParen.Show()

	# ----------------------------------------------------------------- ladder

	def __BuildLadder(self):
		for part in self.ladder:
			part.Hide()
		self.ladder = []
		self.slotImages = {}
		items = []	# (kind, value, height): from the top tier down, 4 key slots between two tiers
		for e in xrange(self.maxTier, 0, -1):
			items.append(('lvl', e, 12 + (58 if e == self.tier else 39) + 5))
			if e > 1:
				for k in xrange(4, 0, -1):
					items.append(('stg', (e - 1, k), 18))
		height = 30 + sum([i[2] for i in items]) + 11	# the lowest slot image overhangs its 18 px
		ly = max(0, (CONTENT_H - height) / 2)
		x0 = LADDER_X	# MT2009_PLUS_KOLA_UI_V2
		self.ladderBg.SetPosition(x0, ly)
		self.ladderBg.SetRenderingRect(0.0, 0.0, 0.0, -1.0 + min(1.0, float(height) / 420.0))
		y = ly + 15
		for kind, value, h in items:
			if kind == 'lvl':
				e = value
				current = e == self.tier
				size = 58 if current else 39
				img = self.__Image(self.bg, UI + 'lvl_%d%s.png' % (min(3, e), 'c' if current else ''), x0 + 50 - size / 2, y + 12)
				img.AddFlag('not_pick')
				self.ladder.append(img)
				num = self.__Text(img, size / 2, size / 2 - 8, DARK, True, True)
				num.SetText(str(e))
				self.ladder.append(num)
				if current:
					for path, ax in (('arrow_l.png', 0), ('arrow_r.png', 80)):
						arrow = self.__Image(self.bg, UI + path, x0 + ax, y + int(h * 0.4))
						arrow.AddFlag('not_pick')
						self.ladder.append(arrow)
				if e > self.tier:
					lock = self.__Image(self.bg, UI + 'lock.png', x0 + 75, y + int(h * 0.42))
					lock.AddFlag('not_pick')
					self.ladder.append(lock)
			else:
				r, k = value
				filled = self.tier > r or (self.tier == r and k <= self.keys)
				path = 'stg.png'
				if filled:
					path = 'stg_f1.png' if r == 1 else 'stg_f2.png'
				img = self.__Image(self.bg, UI + path, x0 + 31, y)
				img.AddFlag('not_pick')
				self.ladder.append(img)
				self.slotImages[value] = img
			y += h

	# ------------------------------------------------------------------- idle

	def __IdleSprite(self, layer, pos):
		key = (layer, pos)
		sprite = self.idle.get(key)
		if sprite is None:
			info = koladata.WHEELS.get(self.wheelId)
			if not info:
				return None
			paths = info['fields'].get(layer)
			if not paths or pos > len(paths):
				return None
			sprite = Sprite(self.wheel, paths[pos - 1])
			sprite.img.AddFlag('not_pick')
			sprite.Hide()
			self.idle[key] = sprite
		return sprite

	def __StopIdle(self):
		self.idleGen += 1
		for sprite in self.idle.values():
			self.Stop(sprite)
			sprite.Hide()

	def __StartIdle(self):
		self.__StopIdle()
		self.__IdleStep(1, 1, self.idleGen)

	def __IdleStep(self, layer, pos, gen):
		"""The original's idle show: every 200 ms the next field's icon pops in
		(400 ms), stays 800 ms and goes (400 ms), tier after tier."""
		if gen != self.idleGen or not self.IsShow():
			return
		if pos > 16:
			layer += 1
			pos = 1
		info = koladata.WHEELS.get(self.wheelId)
		top = min(max(info['fields'].keys()), self.maxTier) if info else 1
		if layer > top:
			layer = 1
		sprite = self.__IdleSprite(layer, pos)
		if sprite:
			x, y = koladata.FIELD_POS[pos - 1]
			self.Stop(sprite)
			sprite.alpha = 1.0
			sprite.Box(x + 20, y + 20, 0, 0)
			sprite.Show()
			grow = lambda s, x=x, y=y: {'w': (0.0, ICON), 'h': (0.0, ICON), 'x': (x + 20.0, x), 'y': (y + 20.0, y)}
			hold = lambda s: {}
			shrink = lambda s, x=x, y=y: {'w': (ICON, 0.0), 'h': (ICON, 0.0), 'x': (x, x + 20.0), 'y': (y, y + 20.0)}
			def hide(sprite=sprite, gen=gen):
				if gen == self.idleGen:
					sprite.Hide()
			self.Queue(sprite, (grow, 400, EaseP, None))
			self.Queue(sprite, (hold, 800, EaseH, None))
			self.Queue(sprite, (shrink, 400, EaseP, hide))
		self.After(200, lambda: self.__IdleStep(layer, pos + 1, gen))

	# ------------------------------------------------------------------- spin

	def __OnSpin(self, *args):
		if self.waiting or self.animating or not self.enabled:
			return
		self.waiting = True
		self.message.SetText('')
		self.__SetButton(True)
		self.spinClicked = app.GetTime()
		net.SendChatPacket('/kolo krec')

	def OnFail(self):
		self.waiting = False
		if not self.animating:
			self.__SetButton(False)

	def OnLayout(self, entries):
		if not self.animating:
			self.layout = list(entries)

	def OnSpin(self, position, keyHit, special):
		if position < 1 or position > 16 or len(self.layout) < 16 or self.animating:
			self.OnFail()
			return
		if self.playing:
			# the 3 s after the last prize: straight to the new spin
			self.spinGen += 1
		self.waiting = False
		self.animating = True
		self.playing = True
		self.spinGen += 1
		gen = self.spinGen
		self.spinInfo = (position, keyHit, special, self.tier, self.keys)
		self.__StopIdle()
		self.__SetButton(True)
		self.pointer.Show()
		for i, sprite in enumerate(self.rewards):
			vnum, count, src = self.layout[i]
			self.Stop(sprite)
			sprite.Load(IconPath(vnum, src))
			sprite.alpha = 1.0
			sprite.Box(sprite.home[0], sprite.home[1], ICON, ICON)
			sprite.Show()
		# the steps: field 1 .. 32 + position, a second after the click
		last = 32 + position
		delay = max(0.0, 1.0 - (app.GetTime() - self.spinClicked)) * 1000.0
		self.After(delay, lambda: self.__Step(1, last, gen))

	def __Frame(self, field):
		name = '%02d.png' % (field - 1)
		self.spinner.LoadImage(UI + 'spinner_' + name)
		self.pointer.LoadImage(UI + 'pointer_' + name)

	def __Step(self, step, last, gen):
		if gen != self.spinGen:
			return
		field = step % 16
		if field == 0:
			field = 16
		self.__Frame(field)
		left = last - step
		if step == last:
			self.__Stopped(field, gen)
			return
		# the passed field's icon jumps 10 px
		sprite = self.rewards[field - 1]
		up = lambda s: {'y': (s.y, s.y - 10)}
		down = lambda s: {'y': (s.y, s.y + 10)}
		self.Queue(sprite, (up, 100, EaseP, None))
		self.Queue(sprite, (down, 400, EaseP, None))
		ms = 100
		if left <= 10:
			ms += 900 - left * 90
		self.After(ms, lambda: self.__Step(step + 1, last, gen))

	def __Stopped(self, field, gen):
		(position, keyHit, special, tier, keys) = self.spinInfo
		sprite = self.rewards[field - 1]
		sprite.img.SetTop()
		for (d, t, ms) in ((60, -30, 200), (-40, 20, 300), (30, -15, 300), (-20, 10, 400), (10, -5, 400)):
			grow = lambda s, d=d, t=t: {'w': (s.w, s.w + d), 'h': (s.h, s.h + d), 'x': (s.x, s.x + t), 'y': (s.y, s.y + t)}
			self.Queue(sprite, (grow, ms, EaseP, None))
		wait = 1500
		if keyHit and field in self.keySprites and tier < self.maxTier:
			self.__FlyKey(field, tier, keys + 1)
			wait += 1700
		self.After(wait, lambda: self.__Reveal(gen))

	def __FlyKey(self, field, tier, slot):
		key = self.keySprites[field]
		target = self.slotImages.get((tier, slot))
		if target:
			# the slot's middle, in the wheel's coordinates
			(tx, ty) = target.GetLocalPosition()
			tx = tx + 19 - WHEEL_X - 28
			ty = ty + 14 - WHEEL_Y - 28
		else:
			tx, ty = key.x, key.y
		self.Stop(key)
		key.img.SetTop()
		up = lambda s: {'x': (s.x, s.x - 28), 'y': (s.y, s.y - 28)}
		fly = lambda s, tx=tx, ty=ty: {'x': (s.x, tx), 'y': (s.y, ty)}
		fade = lambda s: {'alpha': (1.0, 0.0), 'w': (56.0, 19.0), 'h': (56.0, 14.5)}
		def landed(key=key, target=target, tier=tier):
			key.Hide()
			if target:
				target.LoadImage(UI + ('stg_f1.png' if tier == 1 else 'stg_f2.png'))
		self.Queue(key, (up, 800, EaseM, None))
		self.Queue(key, (fly, 400, EaseM, None))
		self.Queue(key, (fade, 300, EaseH, landed))

	def __Reveal(self, gen):
		if gen != self.spinGen:
			return
		self.__Finish(False)
		self.After(3000, lambda: self.__BackToIdle(gen))

	def __Finish(self, instant):
		"""The prize told, the new state taken; instant: the window closes mid-spin."""
		if not self.animating:
			if instant:
				self.__BackToIdle(self.spinGen)
			return
		(position, keyHit, special, tier, keys) = self.spinInfo
		vnum, count, src = self.layout[position - 1]
		self.lastPrize = (vnum, count, src, special)
		self.lastIcon.Load(IconPath(vnum, src))
		# MT2009_PLUS_KOLA_UI_V2: one short line in the welcome box (the tooltip has the rest)
		name = PrizeName(vnum, count)
		if len(name) > 22:
			name = name[:20] + '...'
		self.lastName1.SetText(name)
		chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_WON % PrizeName(vnum, count))
		self.animating = False
		state = self.pendingState
		self.pendingState = None
		if state:
			if keyHit and tier < self.maxTier:
				if state[2] > tier:
					chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_GATE % state[2])
				else:
					chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_KEY % (state[4], state[5]))
			self.__TakeState(state)
		self.__ApplyState()
		if instant:
			self.spinGen += 1
			self.__BackToIdle(self.spinGen)

	def __BackToIdle(self, gen):
		if gen != self.spinGen or self.animating:
			return
		self.playing = False
		for sprite in self.rewards:
			self.Stop(sprite)
			sprite.Hide()
		self.spinner.LoadImage(UI + 'spinner_00.png')
		self.pointer.LoadImage(UI + 'pointer_00.png')
		self.pointer.Hide()
		self.__ApplyState()
		if self.IsShow():
			self.__StartIdle()

	def __OnExit(self):
		if self.animating or self.waiting or self.tier <= 1:
			return
		net.SendChatPacket('/kolo opusc')

	def __OnPrices(self):
		if not self.prizeWindow:
			self.prizeWindow = PrizeWindow(self)
		self.prizeWindow.Open(self.tier)

	def RefreshPool(self):
		if self.prizeWindow and self.prizeWindow.IsShow():
			self.prizeWindow.Open(self.prizeWindow.tier)

	def OnUpdate(self):
		self.__Tick()
		if self.tier > 1 and not self.animating:
			self.__RefreshClock()


def GetWindow():
	if not _data['window']:
		_data['window'] = WheelWindow()
	return _data['window']


def ToggleWindow():
	wnd = GetWindow()
	if wnd.IsShow():
		wnd.Close()
	else:
		wnd.Open()


def OpenWindow():
	wnd = GetWindow()
	if not wnd.IsShow():
		wnd.Open()


def DestroyWindow():
	wnd = _data['window']
	if wnd:
		wnd.Destroy()
	_data['window'] = None


# game.py "WOF": the server's answers.
def OnCommand(sub='', *args):
	if sub == 'kstate':
		values = [_Int(a) for a in args[:9]]
		while len(values) < 9:
			values.append(0)
		_data['state'] = tuple(values)
		GetWindow().OnState(tuple(values))
	elif sub == 'kcosts':
		_data['costs'] = tuple([_Int(a) for a in args[:3]])
	elif sub == 'kpool':
		if len(args) >= 3:
			tier = _Int(args[0])
			special = 1 if _Int(args[1]) else 0
			pools = _data['poolIn'].setdefault(tier, {})
			pools.setdefault(special, []).extend(ParseEntries(args[2], 4))
	elif sub == 'kpoolend':
		_data['pool'] = _data['poolIn']
		_data['poolIn'] = {}
		if _data['window']:
			_data['window'].RefreshPool()
	elif sub == 'klayout':
		entries = ParseEntries(args[0], 3) if args else []
		_data['layout'] = entries
		GetWindow().OnLayout(entries)
	elif sub == 'kspin':
		if len(args) >= 1:
			GetWindow().OnSpin(_Int(args[0]), _Int(args[1]) if len(args) > 1 else 0, _Int(args[2]) if len(args) > 2 else 0)
	elif sub == 'kfail':
		if _data['window']:
			_data['window'].OnFail()
