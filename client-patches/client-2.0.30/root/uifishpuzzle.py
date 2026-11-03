# MT2009_PLUS_FISH_PUZZLE_V1 - Event Rybacki - Puzzle (Wedkarskie Puzzle): the puzzle window (GF 26.1.11's layout
# uiscript/fishpuzzlewindow.py, the pictures in the pack "fishpuzzle"; the root logic ours).
#
# No new exe: the server (fish_puzzle.cpp, "/fishpuzzle") decides everything over the chat command channel.
# Client -> server:  /fishpuzzle open  |  /fishpuzzle box <1 normal, 2 deluxe>  |  /fishpuzzle place <cell 0-23>  |
#                    /fishpuzzle discard
# Server -> client (game.py "FP" -> OnCommand):
#   FP state <event 0/1> <attempts> <piece in hand 0-7> <boxes> <deluxe boxes> <pieces|->
#        pieces: two characters a piece - its shape '1'-'7' and its top-left cell 'a' + 0..23 (6 x 4, row by row)
#   FP open                          - a box used from the inventory: open the window
#   FP piece <shape> <attempts>      - a box was opened, the piece is in hand
#   FP done <attempts> <reward vnum> - the board was full: the reward came, the board is empty again
#
# Playing (pl-wiki "Minigra: Wedkarskie Puzzle"): a left click on a box opens it (one attempt); the piece then follows
# the mouse, snapped to the board's cells - green where it fits; a left click on the board lays it, a right click (or
# "Odrzuc") throws it away. The fewer attempts, the better the Zl. Skrzynia na Ryby.
# Opened from the event hub's button (uiingameevent.RegisterOpener('fishpuzzle')) or by using a box from the inventory.
#
# Python 2.7 as the client has it; the texts are CP1250 escapes.

import app
import chat
import net
import ui
import wndMgr

EVENT_KEY = 'fishpuzzle'
COLS = 6
ROWS = 4
CELL = 32
GRID_X = 18
GRID_Y = 34
BOX_NORMAL = 25106
BOX_DELUXE = 25107
SHAPE_DELUXE = 7
ROOT_PATH = 'd:/ymir work/ui/minigame/fish_event/'

# the seven pieces (fish_1..fish_7.sub): their cells (dx, dy) from the top-left corner - as fish_puzzle.cpp
SHAPES = {
	1: ((0, 0), (0, 1), (0, 2)),
	2: ((0, 0),),
	3: ((0, 0), (0, 1), (1, 1)),
	4: ((0, 0), (1, 0), (1, 1)),
	5: ((0, 0), (1, 0), (0, 1), (1, 1)),
	6: ((0, 0), (1, 0), (1, 1), (2, 1)),
	7: ((0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1)),
}

TITLE_OFF = 'W\xeadkarskie puzzle (event nie trwa - pud\xb3a mo\xbfesz otwiera\xe6 dalej)'
NO_BOX = 'Nie masz takiego pud\xb3a. Pud\xb3a wy\xb3awiasz w\xeadk\xb9 podczas Eventu Rybackiego.'
HAVE_PIECE = 'Najpierw po\xb3\xf3\xbf albo odrzu\xe6 element, kt\xf3ry trzymasz.'
DONE = 'Puzzle u\xb3o\xbfone w %d pr\xf3bach!'
BOX_TIP = 'Lewy klik: otw\xf3rz pud\xb3o (1 pr\xf3ba)'
HELP = [
	'W\xcaDKARSKIE PUZZLE',
	'Podczas Eventu Rybackiego \xb3owi\xb9c ryby znajdziesz',
	'Pud\xb3a w\xeadkarskich puzzli - ka\xbfde to losowy element.',
	'Z Rybimi Wn\xeatrzno\x9cciami pud\xb3o jest przy ka\xbfdej rybie,',
	'a czasem luksusowe - z du\xbfym elementem 3 x 2.',
	'',
	'Lewy klik na pud\xb3o otwiera je (to jedna pr\xf3ba).',
	'Element idzie za kursorem - lewy klik na planszy',
	'k\xb3adzie go tam, gdzie pasuje (zielony), prawy klik',
	'albo "Odrzu\xe6" go wyrzuca.',
	'',
	'Wype\xb3nij ca\xb3\xb9 plansz\xea w jak najmniej pr\xf3bach:',
	'  10 lub mniej - Z\xb3. Skrzynia na Ryby (D)',
	'  11 do 24 - Z\xb3. Skrzynia na Ryby (\x8c)',
	'  25 lub wi\xeacej - Z\xb3. Skrzynia na Ryby (M)',
	'i zawsze +30 000 PD.',
]

_data = {'window': None}


def Send(command):
	net.SendChatPacket('/fishpuzzle ' + command)


def ToInt(value, default=0):
	try:
		return int(value)
	except (TypeError, ValueError):
		return default


def DecodePieces(text):
	pieces = []
	if not text or text == '-':
		return pieces
	for i in xrange(0, len(text) - 1, 2):
		shape = ord(text[i]) - ord('0')
		pos = ord(text[i + 1]) - ord('a')
		if shape in SHAPES and 0 <= pos < COLS * ROWS:
			pieces.append((shape, pos))
	return pieces


def Occupied(pieces):
	used = set()
	for shape, pos in pieces:
		for dx, dy in SHAPES[shape]:
			used.add((pos / COLS + dy) * COLS + pos % COLS + dx)
	return used


def Fits(pieces, shape, pos):
	if shape not in SHAPES or not 0 <= pos < COLS * ROWS:
		return False
	used = Occupied(pieces)
	for dx, dy in SHAPES[shape]:
		x = pos % COLS + dx
		y = pos / COLS + dy
		if x >= COLS or y >= ROWS or y * COLS + x in used:
			return False
	return True


def PieceImage(parent, shape):
	image = ui.ExpandedImageBox()
	image.SetParent(parent)
	image.AddFlag('not_pick')
	image.LoadImage(ROOT_PATH + 'fish_%d.sub' % shape)
	image.Show()
	return image


class GridArea(ui.Window):
	"""The 6 x 4 board's clicks: left lays the piece in hand on the cell under its top-left corner, right throws it."""

	def __init__(self, owner):
		ui.Window.__init__(self)
		self.owner = owner
		self.SetSize(COLS * CELL, ROWS * CELL)

	def __del__(self):
		ui.Window.__del__(self)

	def OnMouseLeftButtonDown(self):
		if self.owner:
			self.owner.ClickGrid()
		return True

	def OnMouseRightButtonDown(self):
		if self.owner:
			self.owner.Discard()
		return True


class FishPuzzleWindow(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.eventOn = 0
		self.uses = 0
		self.pending = 0
		self.boxes = 0
		self.deluxe = 0
		self.pieces = []
		self.pieceImages = []
		self.hand = None
		self.handShape = 0
		self.tooltip = None
		self.helpTip = None
		self.effectEnd = 0.0
		self.__LoadWindow()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __LoadWindow(self):
		ui.PythonScriptLoader().LoadScriptFile(self, 'UIScript/fishpuzzlewindow.py')
		self.board = self.GetChild('board')
		self.titleName = self.GetChild('TitleName')
		self.gridImage = self.GetChild('GameSlotImg')
		self.normalSlot = self.GetChild('NormalItemSlot')
		self.specialSlot = self.GetChild('SpecialItemSlot')
		self.useCountText = self.GetChild('use_count_text')
		self.helpButton = self.GetChild('help_button')
		self.discardButton = self.GetChild('discard_button')
		self.effects = [self.GetChild('score_completion_effect%d' % i) for i in (1, 2, 3)]
		for effect in self.effects:
			effect.Hide()

		self.GetChild('titlebar').SetCloseEvent(ui.__mem_func__(self.Close))
		self.discardButton.SetEvent(ui.__mem_func__(self.Discard))
		self.helpButton.SetEvent(ui.__mem_func__(self.__ToggleHelp))

		self.normalSlot.SetSelectItemSlotEvent(ui.__mem_func__(self.__ClickNormal))
		self.normalSlot.SetSelectEmptySlotEvent(ui.__mem_func__(self.__ClickNormal))
		self.normalSlot.SetOverInItemEvent(ui.__mem_func__(self.__OverInNormal))
		self.normalSlot.SetOverOutItemEvent(ui.__mem_func__(self.__OverOut))
		self.specialSlot.SetSelectItemSlotEvent(ui.__mem_func__(self.__ClickDeluxe))
		self.specialSlot.SetSelectEmptySlotEvent(ui.__mem_func__(self.__ClickDeluxe))
		self.specialSlot.SetOverInItemEvent(ui.__mem_func__(self.__OverInDeluxe))
		self.specialSlot.SetOverOutItemEvent(ui.__mem_func__(self.__OverOut))

		self.grid = GridArea(self)
		self.grid.SetParent(self.board)
		self.grid.SetPosition(GRID_X, GRID_Y)
		self.grid.Show()

		import uiToolTip
		self.tooltip = uiToolTip.ItemToolTip()
		self.tooltip.HideToolTip()
		self.helpTip = uiToolTip.ToolTip()
		for line in HELP:
			self.helpTip.AppendTextLine(line)
		self.helpTip.HideToolTip()
		self.Refresh()

	def Destroy(self):
		if self.tooltip:
			self.tooltip.HideToolTip()
		if self.helpTip:
			self.helpTip.HideToolTip()
		self.tooltip = None
		self.helpTip = None
		self.grid.owner = None
		self.grid = None
		self.pieceImages = []
		self.hand = None
		self.effects = []
		self.ClearDictionary()

	def Open(self):
		self.Show()
		self.SetTop()
		Send('open')
		self.Refresh()

	def Close(self):
		if self.tooltip:
			self.tooltip.HideToolTip()
		if self.helpTip:
			self.helpTip.HideToolTip()
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	# ------------------------------------------------------------ the server's lines

	def SetState(self, eventOn, uses, pending, boxes, deluxe, pieces):
		self.eventOn = eventOn
		self.uses = uses
		self.pending = pending if pending in SHAPES else 0
		self.boxes = boxes
		self.deluxe = deluxe
		self.pieces = DecodePieces(pieces)
		self.Refresh()

	def SetPiece(self, shape, uses):
		self.pending = shape if shape in SHAPES else 0
		self.uses = uses
		self.Refresh()

	def Done(self, uses):
		chat.AppendChat(chat.CHAT_TYPE_INFO, DONE % uses)
		for effect in self.effects:
			effect.ResetFrame()
			effect.Show()
		self.effectEnd = app.GetTime() + 1.5

	# ------------------------------------------------------------ drawing

	def Refresh(self):
		self.titleName.SetText('W\xeadkarskie puzzle' if self.eventOn else TITLE_OFF)
		self.useCountText.SetText(str(self.uses))
		self.normalSlot.SetItemSlot(0, BOX_NORMAL, self.boxes)
		self.specialSlot.SetItemSlot(0, BOX_DELUXE, self.deluxe)
		self.normalSlot.RefreshSlot()
		self.specialSlot.RefreshSlot()
		self.pieceImages = []
		for shape, pos in self.pieces:
			image = PieceImage(self.board, shape)
			image.SetPosition(GRID_X + pos % COLS * CELL, GRID_Y + pos / COLS * CELL)
			self.pieceImages.append(image)
		if self.handShape != self.pending:
			self.hand = None
			self.handShape = 0
			if self.pending:
				self.hand = PieceImage(self.board, self.pending)
				self.handShape = self.pending
		if self.hand:
			self.hand.SetTop()
		self.__PlaceHand()

	def __HoverCell(self):
		"""The board's cell under the mouse, or -1."""
		(mx, my) = wndMgr.GetMousePosition()
		(gx, gy) = self.grid.GetGlobalPosition()
		x = mx - gx
		y = my - gy
		if x < 0 or y < 0 or x >= COLS * CELL or y >= ROWS * CELL:
			return -1
		return (y / CELL) * COLS + x / CELL

	def __PlaceHand(self):
		if not self.hand:
			return
		cell = self.__HoverCell()
		if cell >= 0:
			self.hand.SetPosition(GRID_X + cell % COLS * CELL, GRID_Y + cell / COLS * CELL)
			if Fits(self.pieces, self.pending, cell):
				self.hand.SetColor(0.6, 1.0, 0.6, 0.85)
			else:
				self.hand.SetColor(1.0, 0.4, 0.4, 0.6)
		else:
			(mx, my) = wndMgr.GetMousePosition()
			(bx, by) = self.board.GetGlobalPosition()
			self.hand.SetPosition(mx - bx - CELL / 2, my - by - CELL / 2)
			self.hand.SetColor(1.0, 1.0, 1.0, 0.85)

	def OnUpdate(self):
		self.__PlaceHand()
		if self.effectEnd and app.GetTime() > self.effectEnd:
			self.effectEnd = 0.0
			for effect in self.effects:
				effect.Hide()

	# ------------------------------------------------------------ the player's clicks

	def __Box(self, kind):
		if self.pending:
			chat.AppendChat(chat.CHAT_TYPE_INFO, HAVE_PIECE)
			return
		if (self.deluxe if kind == 2 else self.boxes) <= 0:
			chat.AppendChat(chat.CHAT_TYPE_INFO, NO_BOX)
			return
		Send('box %d' % kind)

	def __ClickNormal(self, slot=0):
		self.__Box(1)

	def __ClickDeluxe(self, slot=0):
		self.__Box(2)

	def __OverIn(self, vnum):
		if self.tooltip:
			self.tooltip.ClearToolTip()
			self.tooltip.SetItemToolTip(vnum)
			self.tooltip.AppendTextLine(BOX_TIP)
			self.tooltip.ShowToolTip()

	def __OverInNormal(self, slot=0):
		self.__OverIn(BOX_NORMAL)

	def __OverInDeluxe(self, slot=0):
		self.__OverIn(BOX_DELUXE)

	def __OverOut(self, slot=0):
		if self.tooltip:
			self.tooltip.HideToolTip()

	def __ToggleHelp(self):
		if not self.helpTip:
			return
		if self.helpTip.IsShow():
			self.helpTip.HideToolTip()
		else:
			self.helpTip.ShowToolTip()

	def ClickGrid(self):
		if not self.pending:
			return
		cell = self.__HoverCell()
		if cell < 0:
			return
		if not Fits(self.pieces, self.pending, cell):
			return
		Send('place %d' % cell)

	def Discard(self):
		if self.pending:
			Send('discard')


def GetWindow():
	if not _data['window']:
		_data['window'] = FishPuzzleWindow()
	return _data['window']


def OpenWindow():
	window = GetWindow()
	if not window.IsShow():
		window.Open()
	else:
		window.SetTop()


def ToggleWindow():
	window = GetWindow()
	if window.IsShow():
		window.Close()
	else:
		window.Open()


def Register():
	"""game.py, with the event hub: the hub's "Event Rybacki - Puzzle" button opens the window."""
	try:
		import uiingameevent
		uiingameevent.RegisterOpener(EVENT_KEY, OpenWindow)
	except ImportError:
		pass


def DestroyWindow():
	window = _data['window']
	if window:
		window.Hide()
		window.Destroy()
	_data['window'] = None


# game.py "FP": the server's lines.
def OnCommand(sub='', *args):
	if sub == 'state':
		values = [ToInt(a) for a in args[:5]]
		while len(values) < 5:
			values.append(0)
		pieces = args[5] if len(args) > 5 else '-'
		GetWindow().SetState(values[0], values[1], values[2], values[3], values[4], pieces)
	elif sub == 'open':
		OpenWindow()
	elif sub == 'piece':
		if _data['window']:
			_data['window'].SetPiece(ToInt(args[0] if args else 0), ToInt(args[1] if len(args) > 1 else 0))
	elif sub == 'done':
		if _data['window']:
			_data['window'].Done(ToInt(args[0] if args else 0))
