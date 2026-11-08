# MT2009_PLUS_KOLEKCJONER_NAJEMNIKOW_V1: "Kolekcjoner Najemnik\xf3w" - the mercenaries' unlock (the owner, 8 November 2026,
# najemnicy-plan.md: six tasks in any order, each once, items handed in as at the Biologist, 95% a hand-in, a permanent
# bonus a task and the next mercenary tier). The Arezzo "Collections System" (uicollections.py,
# uiscript/collectionswindow.py) ported in its working - categories, the items with their counters, hand in one, Ctrl
# hands in all - but not in its look: the layout is the owner's reference picture (8 November, "dla rozeznania"):
#   * the title "KOLEKCJONER" between two diamonds, one tab ("Kolekcjoner") over a thin line;
#   * LEFT the tasks (a list that scrolls when there are more than fit): the first item's icon in a framed slot, the
#     name, "x / N" (units handed in of all), a thin progress bar; the selected one in a gold frame;
#   * MIDDLE the selected task: its name, "od N poziomu" (the mercenary tier it brings) on the right, a line of
#     description, then two columns of item tiles - icon, name (cut with ".."), a pill "x / N" ("Oddane" when done);
#     the selected tile in a gold frame; pages when a task has more than ten;
#   * RIGHT the selected item: a big icon in a frame, its name, a progress bar, "x / N", "Szansa: 95%", "Co ile: bez
#     przerwy", "Masz: N szt." (+ the pack, "tylko nieotwierane"), a status pill ("Mo\xbfesz odda\xe6 teraz", "Brak
#     przedmiotu", "Oddane"...), "NAGRODA" - the task's permanent bonus and the mercenary slot it unlocks - and the big
#     gold "Oddaj";
#   * BOTTOM "Za ca\xb3\xb9 kategori\xea (x/N): <bonus>".
# Our rules, not the picture's: every item of a task is open at once (no item locked behind the previous one), the reward
# is the TASK's (no reward an item), the chance is the server's (95%).
# Drawn with what every client has: the board, solid bars (the auction house's card colours), the collector storage's
# slot picture (mt2009_ui/collector/slot.tga, already in the root pack), the public close button, the item icons. The
# window's frame is uiscript/najemnicykolekcjonerwindow.py.
#
# How a player hands in: select the item (a click on its tile) and press "Oddaj" - one (one pack); Ctrl + "Oddaj" all he
# has. On a tile: a double click or a right click on the icon hands in one, with Ctrl all.
#
# The server (playerbot_kolekcjoner_najemnikow.cpp, server-patches/kolekcjoner) holds everything; the window asks
#   "/kolekcja_najemnikow open"                  (opening: everything, then the window shows)
#   "/kolekcja_najemnikow oddaj <task> <item> [all]"
# and hears (game.py passes every "KNAJ ..." line here):
#   KNAJ begin <tasks done> <tasks>
#   KNAJ task <task> <percent> <nr|0> <POINT:value,...|->
#   KNAJ item <task> <item> <vnum> <need> <given> <pack> <unopened> <have>
#   KNAJ end <open 0|1>
#   KNAJ res <task> <item> <code> <successes> <failures> <units used>
#   KNAJ done <task> <nr> <tasks done>
# The Najemnicy letter's button and the Esc menu's "Kolekcjoner Najemnik\xf3w" open it, and the key of
# "kolekcjoner_najemnikow" (keybind.py, none by default).
#
# Python 2.7 as the client has it; the texts are CP1250 escapes so the file stays ASCII, each a Polish and English pair
# (playerbot_lang.T).

import app
import chat
import item
import net
import player
import snd
import ui
import wndMgr

from playerbot_lang import T

try:
	import pack
except ImportError:
	pack = None

COMMAND = '/kolekcja_najemnikow'
IMG = 'mt2009_ui/collector/'
SLOT_FALLBACK = 'd:/ymir work/ui/public/Slot_Base.sub'
CLOSE_BUTTON = ('d:/ymir work/ui/public/close_button_01.sub', 'd:/ymir work/ui/public/close_button_02.sub',
	'd:/ymir work/ui/public/close_button_03.sub')

# The mercenaries' tiers (playerbot_najemnicy.h GetNajemnicySlots): the n-th task done -> n + 1 mercenaries from level
# 75 + 5n.
TIER_FIRST_LEVEL = 80
TIER_LEVEL_STEP = 5

# The layout (uiscript/najemnicykolekcjonerwindow.py has the same size).
WIDTH = 760
HEIGHT = 500
PANEL_Y = 80
PANEL_H = 384
LEFT_X, LEFT_W = 14, 206
MID_X, MID_W = 228, 318
RIGHT_X, RIGHT_W = 554, 192
ROW_H = 60
ROW_GAP = 2
ROWS_SHOWN = 6
TILE_W = 146
TILE_H = 52
TILE_GAP = 6
TILE_COLS = 2
TILE_ROWS = 5
TILES = TILE_COLS * TILE_ROWS
TILES_Y = 52

COLOR_TEXT = 0xFFE8DCC8
COLOR_WHITE = 0xFFF2EEE6
COLOR_DIM = 0xFFA89A86
COLOR_GOLD = 0xFFFFD27F
COLOR_GOLD_DARK = 0xFFC9A04A
COLOR_GOOD = 0xFF8FDC8F
COLOR_ERROR = 0xFFFF8A80
COLOR_BONUS = 0xFF9CE09C
COLOR_PANEL_BORDER = 0xFF3E362C
COLOR_PANEL_FILL = 0xB0100E0C
COLOR_ROW_BORDER = 0xFF2E2822
COLOR_ROW_FILL = 0xC0181512
COLOR_SEL_BORDER = 0xFFC9A04A
COLOR_SEL_FILL = 0xE02A2418
COLOR_DONE_BORDER = 0xFF4E7A4E
COLOR_BAR_BACK = 0xFF2C2620
COLOR_BAR_GOLD = 0xFFC9A04A
COLOR_BAR_DONE = 0xFF5FB45F
COLOR_PILL_BORDER = 0xFF8A6D2E
COLOR_PILL_FILL = 0xFF3A2E14
COLOR_PILL_DONE_BORDER = 0xFF3F6E3F
COLOR_PILL_DONE_FILL = 0xFF1C301C
COLOR_PILL_OFF_BORDER = 0xFF4A3F36
COLOR_PILL_OFF_FILL = 0xFF201B17
COLOR_SLOT_FRAME = 0xFF5A4A30
COLOR_BUTTON_BORDER = 0xFFFFE3A0
COLOR_BUTTON_FILL = 0xFFD9A441
COLOR_BUTTON_OVER = 0xFFEBB955
COLOR_BUTTON_DOWN = 0xFFB98A30
COLOR_BUTTON_OFF = 0xFF6B5A3A
COLOR_BUTTON_TEXT = 0xFF2A1E0A
COLOR_LINE = 0xFF3A3328
COLOR_GLOW = 0x90C9A04A

TITLE = T('KOLEKCJONER', 'COLLECTOR')
TAB = T('Kolekcjoner', 'Collector')

# The six tasks: (Polish, English, a line of description Polish, English). Another index: its number.
TASKS = {
	1: ('Skrzynie boss\xf3w', 'Boss chests',
		'Szkatu\xb3ki boss\xf3w, oddawane po jednej.', 'Boss caskets, handed in one at a time.'),
	2: ('Kamienie Duszy', 'Soul Stones',
		'Kamienie Duszy +4, oddawane po jednym.', 'Soul Stones +4, handed in one at a time.'),
	3: ('Cor Draconis', 'Cor Draconis',
		'Cor Draconis z misji Alchemika, paczki po 10.', "The Alchemist's Cor Draconis, packs of 10."),
	4: ('Od\xb3amki Energii', 'Energy Fragments',
		'Od\xb3amki Energii, oddawane w paczkach po 100.', 'Energy Fragments, handed in as packs of 100.'),
	5: ('Per\xb3y i ma\xb3\xbfe', 'Pearls and clams',
		'Per\xb3y po jednej, ma\xb3\xbfe w paczkach po 10.', 'Pearls one at a time, clams as packs of 10.'),
	6: ('Bossowie loch\xf3w', 'Dungeon bosses',
		'Skrzynie boss\xf3w loch\xf3w, tylko nieotwierane.', 'Dungeon boss chests, unopened only.'),
}

# The bonus names (the server's s_aKnPoints; one %d).
POINTS = {
	'MAX_HP': ('Maks. P\xaf +%d', 'Max HP +%d'),
	'MAX_SP': ('Maks. PE +%d', 'Max SP +%d'),
	'MAX_HP_PCT': ('Maks. P\xaf +%d%%', 'Max HP +%d%%'),
	'ATT_GRADE_BONUS': ('Warto\x9c\xe6 ataku +%d', 'Attack value +%d'),
	'MAGIC_ATT_GRADE_BONUS': ('Warto\x9c\xe6 ataku magicznego +%d', 'Magic attack value +%d'),
	'DEF_GRADE_BONUS': ('Obrona +%d', 'Defence +%d'),
	'MAGIC_DEF_GRADE_BONUS': ('Obrona magiczna +%d', 'Magic defence +%d'),
	'ATTBONUS_MONSTER': ('Silny przeciwko potworom +%d%%', 'Strong against monsters +%d%%'),
	'ATTBONUS_BOSS': ('Silny przeciwko bossom +%d%%', 'Strong against bosses +%d%%'),
	'ATTBONUS_STONE': ('Silny przeciwko kamieniom Metin +%d%%', 'Strong against Metin stones +%d%%'),
	'ATTBONUS_HUMAN': ('Silny przeciwko ludziom +%d%%', 'Strong against half-humans +%d%%'),
	'CRITICAL_PCT': ('Szansa na krytyczne uderzenie +%d%%', 'Critical hit chance +%d%%'),
	'PENETRATE_PCT': ('Szansa na przeszywaj\xb9ce uderzenie +%d%%', 'Piercing hit chance +%d%%'),
	'RESIST_FIRE': ('Odporno\x9c\xe6 na ogie\xf1 +%d%%', 'Fire resistance +%d%%'),
	'RESIST_ICE': ('Odporno\x9c\xe6 na l\xf3d +%d%%', 'Ice resistance +%d%%'),
	'RESIST_ELEC': ('Odporno\x9c\xe6 na b\xb3yskawice +%d%%', 'Lightning resistance +%d%%'),
	'RESIST_WIND': ('Odporno\x9c\xe6 na wiatr +%d%%', 'Wind resistance +%d%%'),
	'RESIST_EARTH': ('Odporno\x9c\xe6 na ziemi\xea +%d%%', 'Earth resistance +%d%%'),
	'RESIST_DARK': ('Odporno\x9c\xe6 na ciemno\x9c\xe6 +%d%%', 'Darkness resistance +%d%%'),
}
ELEMENTS = ('RESIST_FIRE', 'RESIST_ICE', 'RESIST_ELEC', 'RESIST_WIND', 'RESIST_EARTH', 'RESIST_DARK')
TEXT_ALL_ELEMENTS = T('+%d%% odporno\x9cci na ka\xbfdy \xbfywio\xb3', '+%d%% resistance to every element')

TEXT_LOADING = T('Wczytywanie...', 'Loading...')
TEXT_NO_TASKS = T('Kolekcjoner nie ma teraz zada\xf1.', 'The Collector has no tasks now.')
TEXT_COUNTER = '%d / %d'
TEXT_GIVEN = T('Oddane', 'Handed in')
TEXT_FROM_LEVEL = T('od %d poziomu', 'from level %d')
TEXT_DONE_HEADER = T('uko\xf1czone (%d.)', 'completed (%d.)')
TEXT_CHANCE = T('Szansa: %d%%', 'Chance: %d%%')
TEXT_EVERY = T('Co ile: bez przerwy', 'How often: any time')
TEXT_HAVE = T('Masz: %d szt.', 'You have: %d')
TEXT_PACK = T('Paczka: po %d szt.', 'Pack: %d at a time')
TEXT_UNOPENED = T('Tylko nieotwierane (3/3)', 'Unopened only (3/3)')
TEXT_REWARD = T('NAGRODA', 'REWARD')
TEXT_UNLOCK_FIRST = (T('Odblokowuje: 1. i 2. miejsce', 'Unlocks: mercenary slots 1, 2'),
	T('najemnika (od %d poziomu)', '(from level %d)'))
TEXT_UNLOCK = (T('Odblokowuje: %d. miejsce', 'Unlocks: mercenary slot %d'), T('najemnika (od %d poziomu)', '(from level %d)'))
TEXT_UNLOCKED_FIRST = (T('Odblokowa\xb3o: 1. i 2. miejsce', 'Unlocked: mercenary slots 1, 2'),
	T('najemnika (od %d poziomu)', '(from level %d)'))
TEXT_UNLOCKED = (T('Odblokowa\xb3o: %d. miejsce', 'Unlocked: mercenary slot %d'), T('najemnika (od %d poziomu)', '(from level %d)'))
TEXT_HAND_IN = T('Oddaj', 'Hand in')
TEXT_HAND_IN_TIP = T('Klik: oddaj 1 (paczk\xea). Ctrl + klik: oddaj wszystko, co masz.',
	'Click: hand in 1 (a pack). Ctrl + click: hand in all you have.')
TEXT_BOTTOM = T('Za ca\xb3\xb9 kategori\xea (%d/%d): %s', 'For the whole category (%d/%d): %s')
TEXT_BOTTOM_DONE = T('Za ca\xb3\xb9 kategori\xea (%d/%d): %s - aktywny na sta\xb3e', 'For the whole category (%d/%d): %s - active for good')
TEXT_SUMMARY = T('Uko\xf1czone: %d z %d   Miejsca najemnik\xf3w: %d', 'Completed: %d of %d   Mercenary slots: %d')
TEXT_RESULT = T('Udane: %d, nieudane: %d (oddano %d szt.)', 'Succeeded: %d, failed: %d (%d handed in)')
TEXT_COMPLETED = T('Zadanie uko\xf1czone! Bonus dzia\xb3a na sta\xb3e.', 'Task completed! The bonus is permanent.')

STATE_CAN = T('Mo\xbfesz odda\xe6 teraz', 'You can hand in now')
STATE_NONE = T('Brak przedmiotu', 'No item')
STATE_PACK = T('Za ma\xb3o na paczk\xea', 'Not enough for a pack')
STATE_DONE = T('Oddane', 'Handed in')
STATE_TASK_DONE = T('Zadanie uko\xf1czone', 'Task completed')

TIP_GIVEN = T('Oddane: %d / %d', 'Handed in: %d / %d')
TIP_PACK = T('Jedno oddanie: paczka %d szt. (liczy si\xea ca\xb3a przy powodzeniu)', 'One hand-in: a pack of %d (counts whole on success)')
TIP_UNOPENED = T('Tylko skrzynie nieotwierane (3/3 otwarcia)', 'Only chests never opened (3/3 openings)')
TIP_HAVE = T('W ekwipunku: %d', 'In your inventory: %d')
TIP_CLICK = T('Dwuklik / PPM: oddaj %d szt.', 'Double / right click: hand in %d')
TIP_CTRL = T('Z Ctrl: oddaj wszystko, co masz', 'With Ctrl: hand in all you have')
TIP_DONE = T('To ju\xbf oddane.', 'All handed in.')

MSG = {
	1: T('Nie masz tego przedmiotu (albo za ma\xb3o na paczk\xea).', 'You do not have this item (or not enough for a pack).'),
	2: T('Ten przedmiot jest ju\xbf ca\xb3y oddany.', 'This item is all handed in.'),
	3: T('To zadanie jest ju\xbf uko\xf1czone.', 'This task is completed already.'),
	4: T('Zamknij najpierw handel, sklep, magazyn lub inne okno.', 'Close the trade, the shop, the storage or the other window first.'),
	5: T('Nie mo\xbfesz tego zrobi\xe6 po \x9cmierci.', 'You cannot do that while dead.'),
	6: T('Kolekcjoner nie przyjmuje teraz przedmiot\xf3w.', 'The Collector takes no items now.'),
	7: T('Tego nie da si\xea odda\xe6.', 'That cannot be handed in.'),
	8: T('Za szybko - spr\xf3buj jeszcze raz.', 'Too fast - try again.'),
	9: T('Kolekcjoner nie jest teraz dost\xeapny - spr\xf3buj za chwil\xea.', 'The Collector is not available now - try again in a moment.'),
}


def _Int(value, default=0):
	try:
		return int(value)
	except (TypeError, ValueError):
		return default


def Exists(path):
	if not path:
		return False
	if path.startswith('d:/ymir work/ui/public/'):
		return True
	try:
		return bool(pack and pack.Exist(path))
	except Exception:
		return False


def Image(name):
	path = IMG + name
	return path if Exists(path) else None


def Say(text):
	if text:
		chat.AppendChat(chat.CHAT_TYPE_INFO, text)


def CtrlPressed():
	for key in (app.DIK_LCONTROL, getattr(app, 'DIK_RCONTROL', app.DIK_LCONTROL)):
		try:
			if app.IsPressed(key):
				return True
		except Exception:
			pass
	return False


def Send(text):
	"""Only in the game phase (warpsafe.py)."""
	try:
		import warpsafe
		if not warpsafe.InGame():
			return False
	except ImportError:
		pass
	net.SendChatPacket(text)
	return True


def TaskName(index):
	if index in TASKS:
		return T(TASKS[index][0], TASKS[index][1])
	return T('Zadanie %d', 'Task %d') % index


def TaskDescription(index):
	if index in TASKS:
		return T(TASKS[index][2], TASKS[index][3])
	return ''


_names = {}
_icons = {}


def ItemName(vnum):
	if vnum not in _names:
		name = ''
		try:
			item.SelectItem(vnum)
			name = item.GetItemName()
		except Exception:
			name = ''
		_names[vnum] = name or ('#%d' % vnum)
	return _names[vnum]


def ItemIcon(vnum):
	if vnum not in _icons:
		path = ''
		try:
			item.SelectItem(vnum)
			path = item.GetIconImageFileName()
		except Exception:
			path = ''
		_icons[vnum] = path
	return _icons[vnum]


def Fit(text, limit):
	if len(text) <= limit:
		return text
	return text[:max(1, limit - 2)] + '..'


def RewardLines(rewards):
	"""rewards: [(name, value)] -> the bonus lines (the six elements of one value as one line)."""
	lines = []
	values = dict(rewards)
	allElements = len([n for n in ELEMENTS if n in values]) == len(ELEMENTS) and \
		len(set(values[n] for n in ELEMENTS)) == 1
	if allElements:
		lines.append(TEXT_ALL_ELEMENTS % values[ELEMENTS[0]])
	for name, value in rewards:
		if allElements and name in ELEMENTS:
			continue
		if name in POINTS:
			lines.append(T(POINTS[name][0], POINTS[name][1]) % value)
		else:
			lines.append('%s %+d' % (name, value))
	return lines or ['-']


def RewardText(rewards):
	return ', '.join(RewardLines(rewards))


def TierLevel(nr):
	return TIER_FIRST_LEVEL + (max(1, nr) - 1) * TIER_LEVEL_STEP


def Slots(tasks, level):
	"""The mercenaries' slots for so many tasks at this level (playerbot_najemnicy.h)."""
	slots = 0
	for t in xrange(1, min(tasks, 6) + 1):
		if level >= TierLevel(t):
			slots = t + 1
	return slots


class Model(object):
	"""What the server said: the tasks in its order, their items."""

	def __init__(self):
		self.Reset()

	def Reset(self):
		self.order = []
		self.tasks = {}
		self.done = 0
		self.loaded = False

	def Begin(self, done, count):
		self.Reset()
		self.done = done

	def Task(self, index, percent, nr, rewards):
		t = self.tasks.get(index)
		if not t:
			t = {'index': index, 'items': {}}
			self.tasks[index] = t
			if index not in self.order:
				self.order.append(index)
		t['percent'] = percent
		t['nr'] = nr
		parsed = []
		if rewards and rewards != '-':
			for part in rewards.split(','):
				if ':' in part:
					name, value = part.split(':', 1)
					parsed.append((name, _Int(value)))
		t['rewards'] = parsed

	def Item(self, index, pos, vnum, need, given, packSize, unopened, have):
		t = self.tasks.get(index)
		if not t:
			return
		t['items'][pos] = {'pos': pos, 'vnum': vnum, 'need': max(1, need), 'given': given, 'pack': max(1, packSize),
			'unopened': unopened, 'have': have}

	def Items(self, index):
		t = self.tasks.get(index)
		if not t:
			return []
		return [t['items'][k] for k in sorted(t['items'].keys())]

	def Units(self, index):
		items = self.Items(index)
		return sum(min(i['given'], i['need']) for i in items), sum(i['need'] for i in items)

	def Progress(self, index):
		given, need = self.Units(index)
		if need <= 0:
			return 100
		return min(100, int(100 * given / need))

	def KindsDone(self, index):
		items = self.Items(index)
		return len([1 for i in items if i['given'] >= i['need']]), len(items)

	def DoneCount(self):
		return len([1 for t in self.tasks.values() if t.get('nr')])


class Frame(object):
	"""A framed rectangle of solid bars: a border of one pixel and the fill inside."""

	def __init__(self, parent, x, y, w, h, border, fill, keep):
		self.border = ui.Bar()
		self.border.SetParent(parent)
		self.border.AddFlag('not_pick')
		self.border.SetPosition(x, y)
		self.border.SetSize(w, h)
		self.border.SetColor(border)
		self.border.Show()
		self.fill = ui.Bar()
		self.fill.SetParent(parent)
		self.fill.AddFlag('not_pick')
		self.fill.SetPosition(x + 1, y + 1)
		self.fill.SetSize(w - 2, h - 2)
		self.fill.SetColor(fill)
		self.fill.Show()
		keep.append(self.border)
		keep.append(self.fill)

	def SetColors(self, border, fill):
		self.border.SetColor(border)
		self.fill.SetColor(fill)

	def Show(self):
		self.border.Show()
		self.fill.Show()

	def Hide(self):
		self.border.Hide()
		self.fill.Hide()


class ProgressBar(object):

	def __init__(self, parent, x, y, w, h, keep):
		self.w = w
		self.h = h
		self.back = ui.Bar()
		self.back.SetParent(parent)
		self.back.AddFlag('not_pick')
		self.back.SetPosition(x, y)
		self.back.SetSize(w, h)
		self.back.SetColor(COLOR_BAR_BACK)
		self.back.Show()
		self.full = ui.Bar()
		self.full.SetParent(parent)
		self.full.AddFlag('not_pick')
		self.full.SetPosition(x, y)
		self.full.SetSize(0, h)
		self.full.SetColor(COLOR_BAR_GOLD)
		self.full.Hide()
		self.width = 0
		keep.append(self.back)
		keep.append(self.full)

	def Set(self, percent, done=False):
		self.width = int(self.w * max(0, min(100, percent)) / 100)
		self.full.SetSize(self.width, self.h)
		self.full.SetColor(COLOR_BAR_DONE if done else COLOR_BAR_GOLD)
		if self.width > 0 and self.back.IsShow():
			self.full.Show()
		else:
			self.full.Hide()

	def Show(self):
		self.back.Show()
		if self.width > 0:
			self.full.Show()

	def Hide(self):
		self.back.Hide()
		self.full.Hide()


class TileEvent(object):
	"""A tile slot's event with the tile's number: the slot window gives back only its own slot (0), and its optional
	second argument is skipped when it is 0."""

	def __init__(self, owner, name, index):
		from _weakref import proxy
		self.owner = proxy(owner)
		self.name = name
		self.index = index

	def __call__(self, *args):
		try:
			getattr(self.owner, self.name)(self.index)
		except ReferenceError:
			pass


class KolekcjonerWindow(ui.ScriptWindow):

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.model = Model()
		self.task = 0
		self.pos = -1			# the selected item of the task
		self.page = 0
		self.scroll = 0			# the first task row shown
		self.keep = []
		self.rows = []
		self.tiles = []
		self.rowTasks = [0] * ROWS_SHOWN
		self.tileItems = [None] * TILES
		self.tooltip = None
		self.statusUntil = 0.0
		self.loadingShown = False
		self.canHandIn = False
		self.buttonState = -1
		self.__Load()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	# ------------------------------------------------------------ building

	def __Load(self):
		try:
			loader = ui.PythonScriptLoader()
			loader.LoadScriptFile(self, 'uiscript/najemnicykolekcjonerwindow.py')
			self.board = self.GetChild('board')
		except Exception:
			import exception
			exception.Abort('KolekcjonerWindow.LoadWindow')
		self.__Build()

	def __Text(self, parent, x, y, text='', color=COLOR_TEXT, center=False, right=False):
		line = ui.TextLine()
		line.SetParent(parent)
		line.AddFlag('not_pick')
		line.SetPosition(x, y)
		if center:
			line.SetHorizontalAlignCenter()
		elif right:
			line.SetHorizontalAlignRight()
		line.SetText(text)
		line.SetPackedFontColor(color)
		line.Show()
		self.keep.append(line)
		return line

	def __Bar(self, parent, x, y, w, h, color):
		bar = ui.Bar()
		bar.SetParent(parent)
		bar.AddFlag('not_pick')
		bar.SetPosition(x, y)
		bar.SetSize(w, h)
		bar.SetColor(color)
		bar.Show()
		self.keep.append(bar)
		return bar

	def __Diamond(self, parent, cx, cy):
		# five rows of 1-3-5-3-1 pixels: a small gold diamond
		for dy, w in ((-2, 1), (-1, 3), (0, 5), (1, 3), (2, 1)):
			self.__Bar(parent, cx - w / 2, cy + dy, w, 1, COLOR_GOLD)

	def __Area(self, parent, x, y, w, h, event, *args):
		# a transparent button: the click of a row or a tile (the auction house's text buttons do the same)
		button = ui.Button()
		button.SetParent(parent)
		button.SetPosition(x, y)
		button.SetSize(w, h)
		button.SetEvent(event, *args)
		button.Show()
		self.keep.append(button)
		return button

	def __Slot(self, parent, x, y):
		self.__Bar(parent, x - 2, y - 2, 36, 36, COLOR_SLOT_FRAME)
		self.__Bar(parent, x - 1, y - 1, 34, 34, 0xFF0C0A08)
		slot = ui.SlotWindow()
		slot.SetParent(parent)
		slot.SetPosition(x, y)
		slot.SetSize(32, 32)
		slot.AppendSlot(0, 0, 0, 32, 32)
		base = Image('slot.tga') or SLOT_FALLBACK
		try:
			slot.SetSlotBaseImage(base, 1.0, 1.0, 1.0, 1.0)
		except Exception:
			slot.SetSlotBaseImage(SLOT_FALLBACK, 1.0, 1.0, 1.0, 1.0)
		slot.Show()
		self.keep.append(slot)
		return slot

	def __Build(self):
		board = self.board
		# the title between two diamonds, the glow line under it, the close button
		title = ' '.join(list(TITLE))
		self.__Text(board, WIDTH / 2, 12, title, COLOR_GOLD, center=True)
		half = len(title) * 3 + 22
		self.__Diamond(board, WIDTH / 2 - half, 19)
		self.__Diamond(board, WIDTH / 2 + half, 19)
		self.__Bar(board, WIDTH / 2 - 110, 33, 220, 1, COLOR_GLOW)
		close = ui.Button()
		close.SetParent(board)
		close.SetPosition(WIDTH - 32, 10)
		close.SetUpVisual(CLOSE_BUTTON[0])
		close.SetOverVisual(CLOSE_BUTTON[1])
		close.SetDownVisual(CLOSE_BUTTON[2])
		close.SetEvent(ui.__mem_func__(self.Close))
		close.Show()
		self.keep.append(close)

		# the tab, its gold underline and the line under the tabs
		self.__Text(board, LEFT_X + 70, 46, TAB, COLOR_GOLD, center=True)
		self.__Bar(board, LEFT_X + 20, 64, 100, 2, COLOR_GOLD_DARK)
		self.__Bar(board, LEFT_X, 68, WIDTH - 2 * LEFT_X, 1, COLOR_LINE)
		self.summaryText = self.__Text(board, WIDTH - LEFT_X - 4, 47, '', COLOR_DIM, right=True)

		self.__BuildLeft()
		self.__BuildMiddle()
		self.__BuildRight()

		self.bottomText = self.__Text(board, WIDTH / 2, HEIGHT - 26, '', COLOR_DIM, center=True)

	def __BuildLeft(self):
		board = self.board
		Frame(board, LEFT_X, PANEL_Y, LEFT_W, PANEL_H, COLOR_PANEL_BORDER, COLOR_PANEL_FILL, self.keep)
		rowW = LEFT_W - 8 - 16		# 16: the scroll bar's room
		for i in xrange(ROWS_SHOWN):
			x = LEFT_X + 4
			y = PANEL_Y + 5 + i * (ROW_H + ROW_GAP)
			row = {}
			row['frame'] = Frame(board, x, y, rowW, ROW_H, COLOR_ROW_BORDER, COLOR_ROW_FILL, self.keep)
			row['area'] = self.__Area(board, x, y, rowW, ROW_H, ui.__mem_func__(self.OnClickRow), i)
			row['slot'] = self.__Slot(board, x + 10, y + 14)
			row['slot'].AddFlag('not_pick')	# the row's button under it takes the click
			row['name'] = self.__Text(board, x + 52, y + 9, '', COLOR_WHITE)
			row['count'] = self.__Text(board, x + 52, y + 26, '', COLOR_DIM)
			row['bar'] = ProgressBar(board, x + 52, y + 46, rowW - 62, 3, self.keep)
			self.rows.append(row)
		scrollBar = ui.ScrollBar()
		scrollBar.SetParent(board)
		scrollBar.SetPosition(LEFT_X + LEFT_W - 18, PANEL_Y + 5)
		scrollBar.SetScrollBarSize(PANEL_H - 10)
		scrollBar.SetScrollEvent(ui.__mem_func__(self.OnScroll))
		scrollBar.Hide()
		self.scrollBar = scrollBar
		self.keep.append(scrollBar)

	def __BuildMiddle(self):
		board = self.board
		Frame(board, MID_X, PANEL_Y, MID_W, PANEL_H, COLOR_PANEL_BORDER, COLOR_PANEL_FILL, self.keep)
		self.taskName = self.__Text(board, MID_X + 12, PANEL_Y + 10, '', COLOR_WHITE)
		self.taskLevel = self.__Text(board, MID_X + MID_W - 12, PANEL_Y + 10, '', COLOR_DIM, right=True)
		self.taskDesc = self.__Text(board, MID_X + 12, PANEL_Y + 28, '', COLOR_DIM)
		for i in xrange(TILES):
			col, row = i % TILE_COLS, i / TILE_COLS
			x = MID_X + 10 + col * (TILE_W + TILE_GAP)
			y = PANEL_Y + TILES_Y + row * (TILE_H + TILE_GAP)
			tile = {}
			tile['frame'] = Frame(board, x, y, TILE_W, TILE_H, COLOR_ROW_BORDER, COLOR_ROW_FILL, self.keep)
			tile['area'] = self.__Area(board, x, y, TILE_W, TILE_H, ui.__mem_func__(self.OnClickTile), i)
			slot = self.__Slot(board, x + 8, y + 10)
			slot.SetSelectItemSlotEvent(TileEvent(self, 'OnTileSlotSelect', i))
			slot.SetUnselectItemSlotEvent(TileEvent(self, 'OnTileSlotUse', i))
			slot.SetUseSlotEvent(TileEvent(self, 'OnTileSlotUse', i))
			slot.SetOverInItemEvent(TileEvent(self, 'OnTileOver', i))
			slot.SetOverOutItemEvent(ui.__mem_func__(self.OnOverOutItem))
			tile['slot'] = slot
			tile['name'] = self.__Text(board, x + 48, y + 7, '', COLOR_WHITE)
			tile['pill'] = Frame(board, x + 48, y + 27, TILE_W - 56, 16, COLOR_PILL_BORDER, COLOR_PILL_FILL, self.keep)
			tile['count'] = self.__Text(board, x + 48 + (TILE_W - 56) / 2, y + 28, '', COLOR_GOLD, center=True)
			self.tiles.append(tile)
		y = PANEL_Y + PANEL_H - 24
		self.prevButton = self.__Area(board, MID_X + MID_W - 92, y, 20, 18, ui.__mem_func__(self.OnPrevPage))
		self.prevButton.SetText('<')
		self.nextButton = self.__Area(board, MID_X + MID_W - 32, y, 20, 18, ui.__mem_func__(self.OnNextPage))
		self.nextButton.SetText('>')
		self.pageText = self.__Text(board, MID_X + MID_W - 52, y + 2, '', COLOR_TEXT, center=True)
		self.statusText = self.__Text(board, MID_X + 12, y + 2, '', COLOR_GOOD)

	def __BuildRight(self):
		board = self.board
		x0 = RIGHT_X
		cx = RIGHT_X + RIGHT_W / 2
		Frame(board, x0, PANEL_Y, RIGHT_W, PANEL_H, COLOR_PANEL_BORDER, COLOR_PANEL_FILL, self.keep)
		# the big icon: a gold frame round the item's icon at 1.5x
		Frame(board, cx - 30, PANEL_Y + 12, 60, 60, COLOR_GOLD_DARK, 0xFF0C0A08, self.keep)
		self.__Bar(board, cx - 28, PANEL_Y + 14, 56, 56, COLOR_SLOT_FRAME)
		self.__Bar(board, cx - 27, PANEL_Y + 15, 54, 54, 0xFF0C0A08)
		icon = ui.ExpandedImageBox()
		icon.SetParent(board)
		icon.AddFlag('not_pick')
		icon.SetPosition(cx - 24, PANEL_Y + 18)
		icon.Hide()
		self.keep.append(icon)
		self.bigIcon = icon
		self.itemName = self.__Text(board, cx, PANEL_Y + 80, '', COLOR_WHITE, center=True)
		self.itemBar = ProgressBar(board, x0 + 18, PANEL_Y + 100, RIGHT_W - 36, 4, self.keep)
		self.itemCount = self.__Text(board, cx, PANEL_Y + 108, '', COLOR_TEXT, center=True)
		self.lineChance = self.__Text(board, x0 + 14, PANEL_Y + 134, '', COLOR_TEXT)
		self.lineEvery = self.__Text(board, x0 + 14, PANEL_Y + 150, '', COLOR_TEXT)
		self.lineHave = self.__Text(board, x0 + 14, PANEL_Y + 166, '', COLOR_TEXT)
		self.linePack = self.__Text(board, x0 + 14, PANEL_Y + 182, '', COLOR_DIM)
		self.statePill = Frame(board, x0 + 12, PANEL_Y + 202, RIGHT_W - 24, 22, COLOR_PILL_BORDER, COLOR_PILL_FILL, self.keep)
		self.stateText = self.__Text(board, cx, PANEL_Y + 206, '', COLOR_GOLD, center=True)
		self.__Text(board, cx, PANEL_Y + 236, TEXT_REWARD, COLOR_DIM, center=True)
		self.rewardLines = [self.__Text(board, cx, PANEL_Y + 252 + i * 15, '', COLOR_BONUS, center=True) for i in xrange(3)]
		self.unlockLines = [self.__Text(board, cx, PANEL_Y + 300 + i * 15, '', COLOR_GOLD, center=True) for i in xrange(2)]
		# the big gold "Oddaj": bars and a transparent button over them (the shades in OnUpdate)
		bx, by, bw, bh = x0 + 12, PANEL_Y + PANEL_H - 42, RIGHT_W - 24, 30
		self.handFrame = Frame(board, bx, by, bw, bh, COLOR_BUTTON_BORDER, COLOR_BUTTON_FILL, self.keep)
		self.handText = self.__Text(board, bx + bw / 2, by + 8, TEXT_HAND_IN, COLOR_BUTTON_TEXT, center=True)
		self.handButton = self.__Area(board, bx, by, bw, bh, ui.__mem_func__(self.OnHandInButton))
		self.handButton.SetToolTipText(TEXT_HAND_IN_TIP, 0, -20)

	def Destroy(self):
		self.Hide()
		self.OnOverOutItem()
		self.tooltip = None
		self.rows = []
		self.tiles = []
		self.keep = []
		self.scrollBar = None
		self.handButton = None
		self.ClearDictionary()

	# ------------------------------------------------------------ opening

	def Open(self):
		if not self.model.loaded:
			self.__SetStatus(TEXT_LOADING)
		self.Show()
		self.SetTop()
		Send(COMMAND + ' open')

	def Close(self):
		self.OnOverOutItem()
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	# ------------------------------------------------------------ server

	def OnServer(self, word, args):
		m = self.model
		if word == 'begin':
			m.Begin(_Int(args[0] if args else 0), _Int(args[1] if len(args) > 1 else 0))
		elif word == 'task' and len(args) >= 4:
			m.Task(_Int(args[0]), _Int(args[1]), _Int(args[2]), args[3])
			if m.loaded:
				self.__Refresh()
		elif word == 'item' and len(args) >= 8:
			m.Item(*[_Int(a) for a in args[:8]])
			if m.loaded:
				self.__Refresh()
		elif word == 'end':
			m.loaded = True
			if not self.task or self.task not in m.tasks:
				self.task = self.__FirstOpenTask()
				self.page = 0
				self.pos = -1
			if not m.order:
				self.__SetStatus(TEXT_NO_TASKS, True)
			elif self.loadingShown:
				self.__SetStatus('')
			self.__Refresh()
			if _Int(args[0] if args else 0) and not self.IsShow():
				self.Show()
				self.SetTop()
		elif word == 'res' and len(args) >= 6:
			task, pos, code, ok, fail, used = [_Int(a) for a in args[:6]]
			if code == 0:
				self.__SetStatus(TEXT_RESULT % (ok, fail, used), ok == 0)
				try:
					snd.PlaySound('sound/ui/drop.wav')
				except Exception:
					pass
			else:
				text = MSG.get(code, MSG[7])
				self.__SetStatus(text, True)
				if not self.IsShow():
					Say(text)
		elif word == 'done' and len(args) >= 3:
			task, nr, done = [_Int(a) for a in args[:3]]
			t = m.tasks.get(task)
			if t:
				t['nr'] = nr
			m.done = done
			self.__SetStatus(TEXT_COMPLETED)
			self.__Refresh()

	def __FirstOpenTask(self):
		for index in self.model.order:
			if not self.model.tasks[index].get('nr'):
				return index
		return self.model.order[0] if self.model.order else 0

	# ------------------------------------------------------------ drawing

	def __SetStatus(self, text, error=False):
		self.loadingShown = text == TEXT_LOADING
		self.statusText.SetText(text)
		self.statusText.SetPackedFontColor(COLOR_ERROR if error else COLOR_GOOD)
		self.statusUntil = app.GetTime() + 8.0 if text else 0.0

	def __Refresh(self):
		self.__RefreshRows()
		self.__RefreshMiddle()
		self.__RefreshRight()
		m = self.model
		done = m.DoneCount()
		self.summaryText.SetText(TEXT_SUMMARY % (done, len(m.order), Slots(done, player.GetStatus(player.LEVEL))))
		t = m.tasks.get(self.task)
		if t:
			kinds, total = m.KindsDone(self.task)
			template = TEXT_BOTTOM_DONE if t.get('nr') else TEXT_BOTTOM
			self.bottomText.SetText(template % (kinds, total, RewardText(t.get('rewards', []))))
			self.bottomText.SetPackedFontColor(COLOR_GOOD if t.get('nr') else COLOR_DIM)
		else:
			self.bottomText.SetText('')

	def __RefreshRows(self):
		m = self.model
		order = m.order
		extra = max(0, len(order) - ROWS_SHOWN)
		self.scroll = max(0, min(self.scroll, extra))
		if extra:
			self.scrollBar.SetMiddleBarSize(float(ROWS_SHOWN) / len(order))
			self.scrollBar.Show()
		else:
			self.scrollBar.Hide()
		for i, row in enumerate(self.rows):
			k = self.scroll + i
			index = order[k] if k < len(order) else 0
			self.rowTasks[i] = index
			parts = ('frame', 'area', 'slot', 'name', 'count', 'bar')
			if not index:
				for key in parts:
					row[key].Hide()
				row['slot'].ClearSlot(0)
				continue
			for key in parts:
				row[key].Show()
			t = m.tasks[index]
			items = m.Items(index)
			if items:
				row['slot'].SetItemSlot(0, items[0]['vnum'], 0)
			else:
				row['slot'].ClearSlot(0)
			row['slot'].RefreshSlot()
			row['name'].SetText(Fit(TaskName(index), 20))
			given, need = m.Units(index)
			done = bool(t.get('nr'))
			row['count'].SetText(TEXT_COUNTER % (given, need))
			row['count'].SetPackedFontColor(COLOR_GOOD if done else COLOR_DIM)
			row['name'].SetPackedFontColor(COLOR_GOOD if done else COLOR_WHITE)
			row['bar'].Set(m.Progress(index), done)
			if index == self.task:
				row['frame'].SetColors(COLOR_SEL_BORDER, COLOR_SEL_FILL)
			else:
				row['frame'].SetColors(COLOR_DONE_BORDER if done else COLOR_ROW_BORDER, COLOR_ROW_FILL)

	def __RefreshMiddle(self):
		m = self.model
		t = m.tasks.get(self.task)
		items = m.Items(self.task) if t else []
		if t:
			self.taskName.SetText(TaskName(self.task))
			self.taskDesc.SetText(TaskDescription(self.task))
			nr = t.get('nr', 0)
			if nr:
				self.taskLevel.SetText(TEXT_DONE_HEADER % nr)
				self.taskLevel.SetPackedFontColor(COLOR_GOOD)
			else:
				self.taskLevel.SetText(TEXT_FROM_LEVEL % TierLevel(m.DoneCount() + 1))
				self.taskLevel.SetPackedFontColor(COLOR_DIM)
		else:
			self.taskName.SetText('')
			self.taskDesc.SetText('')
			self.taskLevel.SetText('')
		pages = max(1, (len(items) + TILES - 1) / TILES)
		self.page = max(0, min(self.page, pages - 1))
		shown = items[self.page * TILES:(self.page + 1) * TILES]
		if items and self.pos not in [i['pos'] for i in items]:
			self.pos = self.__FirstOpenItem(items)
		taskDone = bool(t and t.get('nr'))
		for i, tile in enumerate(self.tiles):
			it = shown[i] if i < len(shown) else None
			self.tileItems[i] = it
			parts = ('frame', 'area', 'slot', 'name', 'pill', 'count')
			if not it:
				for key in parts:
					tile[key].Hide()
				tile['slot'].ClearSlot(0)
				continue
			for key in parts:
				tile[key].Show()
			complete = taskDone or it['given'] >= it['need']
			tile['slot'].SetItemSlot(0, it['vnum'], it['pack'] if it['pack'] > 1 else 0)
			tile['slot'].RefreshSlot()
			tile['name'].SetText(Fit(ItemName(it['vnum']), 15))
			if complete:
				tile['count'].SetText(TEXT_GIVEN)
				tile['count'].SetPackedFontColor(COLOR_GOOD)
				tile['pill'].SetColors(COLOR_PILL_DONE_BORDER, COLOR_PILL_DONE_FILL)
				tile['name'].SetPackedFontColor(COLOR_DIM)
			else:
				tile['count'].SetText(TEXT_COUNTER % (it['given'], it['need']))
				tile['count'].SetPackedFontColor(COLOR_GOLD)
				tile['pill'].SetColors(COLOR_PILL_BORDER, COLOR_PILL_FILL)
				tile['name'].SetPackedFontColor(COLOR_WHITE)
			if it['pos'] == self.pos:
				tile['frame'].SetColors(COLOR_SEL_BORDER, COLOR_SEL_FILL)
			else:
				tile['frame'].SetColors(COLOR_DONE_BORDER if complete else COLOR_ROW_BORDER, COLOR_ROW_FILL)
		if pages > 1:
			self.pageText.SetText('%d/%d' % (self.page + 1, pages))
			self.prevButton.Show()
			self.nextButton.Show()
		else:
			self.pageText.SetText('')
			self.prevButton.Hide()
			self.nextButton.Hide()

	def __FirstOpenItem(self, items):
		for it in items:
			if it['given'] < it['need']:
				return it['pos']
		return items[0]['pos'] if items else -1

	def __Selected(self):
		t = self.model.tasks.get(self.task)
		if not t:
			return None, None
		return t, t['items'].get(self.pos)

	def __RefreshRight(self):
		t, it = self.__Selected()
		if not t or not it:
			for line in (self.itemName, self.itemCount, self.lineChance, self.lineEvery, self.lineHave, self.linePack,
					self.stateText):
				line.SetText('')
			self.bigIcon.Hide()
			self.itemBar.Set(0)
			self.statePill.Hide()
			for line in self.rewardLines + self.unlockLines:
				line.SetText('')
			self.canHandIn = False
			return
		icon = ItemIcon(it['vnum'])
		if icon:
			try:
				self.bigIcon.LoadImage(icon)
				self.bigIcon.SetScale(1.5, 1.5)
				self.bigIcon.Show()
			except Exception:
				self.bigIcon.Hide()
		else:
			self.bigIcon.Hide()
		taskDone = bool(t.get('nr'))
		complete = taskDone or it['given'] >= it['need']
		given = min(it['given'], it['need'])
		self.itemName.SetText(Fit(ItemName(it['vnum']), 26))
		self.itemBar.Set(int(100 * given / max(1, it['need'])), complete)
		self.itemCount.SetText(TEXT_COUNTER % (given, it['need']))
		self.lineChance.SetText(TEXT_CHANCE % t.get('percent', 0))
		self.lineEvery.SetText(TEXT_EVERY)
		self.lineHave.SetText(TEXT_HAVE % it['have'])
		extra = []
		if it['pack'] > 1:
			extra.append(TEXT_PACK % it['pack'])
		if it['unopened']:
			extra.append(TEXT_UNOPENED)
		self.linePack.SetText(extra[0] if extra else '')
		self.statePill.Show()
		if taskDone:
			state, color, ok = STATE_TASK_DONE, COLOR_GOOD, False
		elif complete:
			state, color, ok = STATE_DONE, COLOR_GOOD, False
		elif it['have'] >= it['pack']:
			state, color, ok = STATE_CAN, COLOR_GOLD, True
		elif it['have'] > 0:
			state, color, ok = STATE_PACK, COLOR_ERROR, False
		else:
			state, color, ok = STATE_NONE, COLOR_ERROR, False
		self.stateText.SetText(state)
		self.stateText.SetPackedFontColor(color)
		if complete:
			self.statePill.SetColors(COLOR_PILL_DONE_BORDER, COLOR_PILL_DONE_FILL)
		elif ok:
			self.statePill.SetColors(COLOR_PILL_BORDER, COLOR_PILL_FILL)
		else:
			self.statePill.SetColors(COLOR_PILL_OFF_BORDER, COLOR_PILL_OFF_FILL)
		self.canHandIn = ok
		lines = RewardLines(t.get('rewards', []))
		for i, line in enumerate(self.rewardLines):
			line.SetText(Fit(lines[i], 32) if i < len(lines) else '')
		nr = t.get('nr', 0)
		if nr:
			tier, first, other = nr, TEXT_UNLOCKED_FIRST, TEXT_UNLOCKED
		else:
			tier, first, other = self.model.DoneCount() + 1, TEXT_UNLOCK_FIRST, TEXT_UNLOCK
		if tier <= 1:
			texts = (first[0], first[1] % TierLevel(1))
		else:
			texts = (other[0] % (tier + 1), other[1] % TierLevel(tier))
		for line, text in zip(self.unlockLines, texts):
			line.SetText(text)

	# ------------------------------------------------------------ the player

	def OnClickRow(self, i):
		index = self.rowTasks[i] if 0 <= i < ROWS_SHOWN else 0
		if not index or index == self.task:
			return
		self.task = index
		self.page = 0
		self.pos = -1
		self.OnOverOutItem()
		self.__Refresh()

	def OnScroll(self):
		extra = max(0, len(self.model.order) - ROWS_SHOWN)
		self.scroll = int(round(self.scrollBar.GetPos() * extra))
		self.__RefreshRows()

	def OnClickTile(self, i):
		it = self.tileItems[i] if 0 <= i < TILES else None
		if not it:
			return
		self.pos = it['pos']
		self.__Refresh()

	def __Carrying(self):
		try:
			import mouseModule
			return mouseModule.mouseController.isAttached()
		except Exception:
			return False

	def OnTileSlotSelect(self, i):
		# a left click on the icon: the tile is selected, as a click beside it
		if not self.__Carrying():
			self.OnClickTile(i)

	def OnTileSlotUse(self, i):
		# a right click or a double click on the icon: one hand-in (Ctrl: all)
		if self.__Carrying():
			return
		self.OnClickTile(i)
		self.__HandIn()

	def OnPrevPage(self):
		self.page = max(0, self.page - 1)
		self.__Refresh()

	def OnNextPage(self):
		self.page += 1
		self.__Refresh()

	def OnHandInButton(self):
		self.__HandIn()

	def __HandIn(self):
		t, it = self.__Selected()
		if not t or not it or t.get('nr') or it['given'] >= it['need']:
			return
		if it['have'] < it['pack']:
			self.__SetStatus(MSG[1], True)
			return
		Send('%s oddaj %d %d%s' % (COMMAND, self.task, it['pos'], ' all' if CtrlPressed() else ''))

	def OnTileOver(self, i):
		it = self.tileItems[i] if 0 <= i < TILES else None
		if not it:
			return
		if not self.tooltip:
			try:
				import uiToolTip
				self.tooltip = uiToolTip.ItemToolTip()
				self.tooltip.HideToolTip()
			except Exception:
				self.tooltip = None
		if not self.tooltip:
			return
		tip = self.tooltip
		tip.ClearToolTip()
		tip.SetItemToolTip(it['vnum'])
		tip.AppendSpace(5)
		tip.AppendTextLine(TIP_GIVEN % (min(it['given'], it['need']), it['need']), COLOR_GOLD)
		if it['pack'] > 1:
			tip.AppendTextLine(TIP_PACK % it['pack'], COLOR_DIM)
		if it['unopened']:
			tip.AppendTextLine(TIP_UNOPENED, COLOR_DIM)
		t = self.model.tasks.get(self.task, {})
		if t.get('nr') or it['given'] >= it['need']:
			tip.AppendTextLine(TIP_DONE, COLOR_GOOD)
		else:
			tip.AppendTextLine(TIP_HAVE % it['have'], COLOR_TEXT)
			tip.AppendTextLine(TIP_CLICK % it['pack'], COLOR_DIM)
			tip.AppendTextLine(TIP_CTRL, COLOR_DIM)
		tip.ShowToolTip()

	def OnOverOutItem(self, *args):
		if self.tooltip:
			self.tooltip.HideToolTip()

	def OnUpdate(self):
		if self.statusUntil and app.GetTime() > self.statusUntil:
			self.statusUntil = 0.0
			self.statusText.SetText('')
		# the gold button's shades: dark when nothing can be handed in, lighter under the mouse
		if not self.handButton:
			return
		if not self.canHandIn:
			state = 2
		elif self.handButton.IsIn():
			state = 1
		else:
			state = 0
		if state != self.buttonState:
			self.buttonState = state
			if state == 2:
				self.handFrame.SetColors(COLOR_PILL_OFF_BORDER, COLOR_BUTTON_OFF)
			else:
				self.handFrame.SetColors(COLOR_BUTTON_BORDER, COLOR_BUTTON_OVER if state == 1 else COLOR_BUTTON_FILL)


_state = {'window': None}


def GetWindow(create=True):
	if not _state['window'] and create:
		_state['window'] = KolekcjonerWindow()
	return _state['window']


def OpenWindow():
	GetWindow().Open()


def ToggleWindow():
	w = GetWindow()
	if w.IsShow():
		w.Close()
	else:
		w.Open()


def DestroyWindow():
	w = _state['window']
	_state['window'] = None
	if w:
		w.Destroy()


def OnServer(word='', *args):
	"""game.py: every "KNAJ <word> ..." line."""
	if word == 'res' or word == 'done':
		w = GetWindow(False)
		if not w:
			# no window yet (a hand-in typed by hand): only the message
			if word == 'res' and len(args) >= 3 and _Int(args[2]):
				Say(MSG.get(_Int(args[2]), MSG[7]))
			return
	GetWindow().OnServer(word, list(args))
