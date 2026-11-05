# MT2009_PLUS_FARM_SESSION_V1 - Sesja farmienia (server-patches/sesja/README.md): the farming session window
# (the Y key, the keybind row "player_stat"; dr_farm_session.cpp on the server). Port of Digi Rasta's
# p-sesja-farmienia (marker DR_FARM_SESSION_V1: the protocol, the queue, the parsing, the tables), drawn anew after
# the owner's screenshots (5 November 2026): a large dark board, three tabs, framed sections with header rows.
#
#   Sesja       the running session and its drops (FarmInfo, FarmItems, FarmSpark, FarmDone)
#   Historia    the finished sessions (FarmHist, FarmHistEnd)
#   Statystyki  the totals (FarmStatSum ... FarmStatAll, FarmStatEnd)
#
# The package's fourth tab "Ogolne" (the 22 stat_* counters of the old Y window) is not here: the old window
# (uiPlayerStat.PlayerStatsWindow) stays as it was, on the keybind row "player_stat_general" (no key by default).
#
# The server's lines (protocol 1, CHAT_TYPE_COMMAND through game.py); every answer begins with FarmInfo and the
# lines of one answer never mix with another's, so a FarmInfo also means "a new answer begins":
#
#   FarmInfo 1 <state> <id> <start> <active> <limit> <now> <exp> <ym> <ys> <yb> <im> <is> <ib> <km> <ks> <kb>
#            [<ylast>]                 state 0 none, 1 running, 2 paused; m/s/b monsters/metins/bosses;
#                                      ylast the time of the last yang (ours); a new <id> drops the items
#   FarmResult <code>                  0 ok, 1 already running, 2 no session, 3 wrong state, 4 wrong limit,
#                                      5 database, 6 ended at the limit
#   FarmItems <src> <n> <vnum>:<cnt>:<last> ...   up to 14 a line; <cnt> is the whole count
#   FarmSpark <minute> <n> <c1> ... <cn>          (ours) the items of the active minutes minute-n+1 .. minute
#   FarmDone                           ends a "pelne" and a "stan" that sent rows
#   FarmHist <id> <start> <active> <yang> <items> <kills> <exp> <reason>, FarmHistEnd
#   FarmStatSum / Per / Rec / Cat / Top / Mob / Map / All (ours: <vnum>:<cat>:<cnt>), FarmStatEnd
#
# The orders (net.SendChatPacket '/sesja ...'): start <sec>, pauza, wznow, koniec, stan, pelne, historia, stat - on
# the one line of the companion's windows (uisidekick._queue['next']), never sooner than COMMAND_SPACING after the
# last. While the window is shown: "stan" every POLL_STAN, "pelne" every POLL_PELNE and when it opens.
#
# Ours beyond the package (the screenshots): the Yang row's tooltip ("Ostatni drop") and hiding, the item line
# chart ("Przedmioty (maks. N)", FarmSpark), rows as tall as their icons, the sources' share bars, the categories
# of one's own ("Nowa kategoria" / "Usun zaznaczona": a name and words of item names, cache/farm_categories_<name>.json;
# their items leave the six of the server), dotted numbers everywhere. The look is drawn in code (bars and texts on
# the client's board), no new images.
#
# Python 2.7 as the client has it; the Polish letters are CP1250 escapes.

from weakref import proxy


def _proxy(obj):
	"""A weak proxy of obj - obj itself when it is one already (events called through ui.__mem_func__ hand the
	window in as a proxy, and a proxy of a proxy raises TypeError) - MT2009_PLUS_WEAKPROXY_FIX_V1."""
	try:
		return proxy(obj)
	except TypeError:
		return obj

import clientclock
import file_utils
import net
import player
import simplejson as json
import ui
import uiToolTip
import uisidekick

PROTOCOL = 1
PREFIX = '/sesja '
POLL_STAN = 5.0
POLL_PELNE = 60.0
CLOCK_INTERVAL = 1.0
COMMAND_SPACING = uisidekick.COMMAND_SPACING

STATE_NONE = 0
STATE_RUNNING = 1
STATE_PAUSED = 2

SOURCE_MONSTERS = 0
SOURCE_METINS = 1
SOURCE_BOSSES = 2

# ---------------------------------------------------------------- the window

WINDOW_WIDTH = 560
WINDOW_HEIGHT = 462
TITLE = 'Sesja farmienia'

TAB_SESSION = 0
TAB_HISTORY = 1
TAB_STATS = 2
TAB_LABELS = ('Sesja', 'Historia', 'Statystyki')
TAB_COUNT = len(TAB_LABELS)
TAB_X = 10
TAB_Y = 32
TAB_HEIGHT = 22
TAB_GAP = 6

PAGE_X = 10
PAGE_Y = 60
PAGE_WIDTH = WINDOW_WIDTH - 2 * PAGE_X
PAGE_HEIGHT = WINDOW_HEIGHT - PAGE_Y - 10

INFO_FIELDS = ('state', 'id', 'start', 'active', 'limit', 'now', 'exp',
	'ym', 'ys', 'yb', 'im', 'is', 'ib', 'km', 'ks', 'kb')
HIST_FIELDS = ('id', 'start', 'active', 'yang', 'items', 'kills', 'exp', 'reason')
STAT_RECORDS = {
	'Sum': ('sum', ('sessions', 'active', 'exp', 'ym', 'ys', 'yb', 'im', 'is', 'ib', 'km', 'ks', 'kb')),
	'Per': ('per', ('today_sessions', 'today_yang', 'week_sessions', 'week_yang')),
	'Rec': ('rec', ('yang', 'yang_at', 'yph', 'yph_at', 'longest', 'longest_at', 'kills', 'kills_at')),
}
STAT_LISTS = {
	'Top': ('top', 2),
	'Mob': ('mob', 2),
	'Map': ('map', 4),
	'All': ('all', 3),
}
STAT_CATEGORIES = 6

# ---------------------------------------------------------------- the colours (the screenshots)

COLOR_BOX_FILL = 0xff1a1815
COLOR_BOX_BORDER = 0xff4a4234
COLOR_BOX_HOVER = 0xff26221c
COLOR_SECTION_BORDER = 0xff6a583a
COLOR_HEAD_FILL = 0xff3a3123
COLOR_HEAD_LINE = 0xff7a6644
COLOR_TOTAL_FILL = 0xff2c261c
COLOR_ROW_FILL = 0xff181613
COLOR_ROW_SELECTED = 0xff302a1f
COLOR_ROW_LINE = 0xff2c2822
COLOR_COLUMN_LINE = 0xff38322a
COLOR_TAB_FILL = 0xff1c1a17
COLOR_TAB_BORDER = 0xff3e3a32
COLOR_TAB_HOVER = 0xff2a2620
COLOR_TAB_ON_FILL = 0xff4a4030
COLOR_TAB_ON_BORDER = 0xff9a8458
COLOR_BUTTON_FILL = 0xff3a3226
COLOR_BUTTON_BORDER = 0xff6a5a42
COLOR_BUTTON_HOVER = 0xff4a4030
COLOR_RED_FILL = 0xff3a2321
COLOR_RED_BORDER = 0xff7a4a3c
COLOR_RED_HOVER = 0xff4a2c28
COLOR_OFF_FILL = 0xff2e1c1c
COLOR_OFF_BORDER = 0xff5a2e2c
COLOR_COLUMN_FILL = 0xff141210
COLOR_TEXT = 0xffe8e0d0
COLOR_HEAD_TEXT = 0xfff2e8d2
COLOR_GOLD = 0xfff0c840
COLOR_DIM = 0xff9a948a
COLOR_OFF_TEXT = 0xff9a7272
COLOR_HIDDEN = 0xff6e6a64
COLOR_RUNNING = 0xffa8e08a
COLOR_BAR = 0xffc8a060
COLOR_TRACK = 0xff2a2620
COLOR_RESULT = 0xffffb050
COLOR_SPARK = 0xffc8a060
COLOR_SCROLL_TRACK = 0xff1e1b17
COLOR_SCROLL_THUMB = 0xff8a7550

# Flat buttons: (fill, border, hover fill, text).
STYLE_TAB = (COLOR_TAB_FILL, COLOR_TAB_BORDER, COLOR_TAB_HOVER, COLOR_TEXT)
STYLE_TAB_ON = (COLOR_TAB_ON_FILL, COLOR_TAB_ON_BORDER, COLOR_TAB_ON_FILL, COLOR_HEAD_TEXT)
STYLE_BUTTON = (COLOR_BUTTON_FILL, COLOR_BUTTON_BORDER, COLOR_BUTTON_HOVER, COLOR_TEXT)
STYLE_RED = (COLOR_RED_FILL, COLOR_RED_BORDER, COLOR_RED_HOVER, COLOR_TEXT)
STYLE_DARK = (COLOR_TAB_FILL, COLOR_TAB_BORDER, COLOR_TAB_HOVER, COLOR_TEXT)
STYLE_OFF = (COLOR_OFF_FILL, COLOR_OFF_BORDER, COLOR_OFF_FILL, COLOR_OFF_TEXT)

# ---------------------------------------------------------------- the Sesja tab

TEXT_NONE = 'Brak aktywnej sesji'
TEXT_LOADING = 'Wczytywanie...'
TEXT_SOURCES = '\x8fr\xf3d\xb3a'
TEXT_YANG = 'Yang'
TEXT_RUNNING = 'Aktywna'
TEXT_PAUSED = 'Wstrzymana'
TEXT_PAUSE = 'Wstrzymaj'
TEXT_RESUME = 'Wzn\xf3w'
TEXT_END = 'Zako\xf1cz'
TEXT_HIDDEN = 'Ukryte'
TEXT_SPARK = 'Przedmioty (maks. %d):'
TEXT_LAST_DROP = 'Ostatni drop: %s'
TEXT_CLICK_HIDE = 'Kliknij, aby ukry\xe6.'
TEXT_CLICK_SHOW = 'Kliknij, aby pokaza\xe6.'
TEXT_END_ASK = 'Zako\xf1czy\xe6 sesj\xea farmienia?'
START_BUTTONS = (('1 godz.', 3600), ('2 godz.', 7200), ('4 godz.', 14400), ('8 godz.', 28800), ('Bez limitu', 0))
FILTER_ALL = 0
TEXT_FILTERS = ('Wszystkie', 'Potwory', 'Metiny', 'Bossy')
FILTER_COUNT = len(TEXT_FILTERS)
SOURCE_WORDS = (('im', 'ym'), ('is', 'ys'), ('ib', 'yb'))
RESULT_TEXTS = {
	1: 'Sesja ju\xbf trwa.',
	2: 'Brak aktywnej sesji.',
	3: 'Nie mo\xbfna tego teraz zrobi\xe6.',
	4: 'Nieprawid\xb3owy limit czasu.',
	5: 'B\xb3\xb9d serwera - spr\xf3buj ponownie.',
	6: 'Sesja zako\xf1czona: osi\xb9gni\xeato limit czasu.',
}
TEXT_RESULT_OTHER = RESULT_TEXTS[5]
STATUS_SECONDS = 6.0

HIDDEN_FILE = 'cache/farm_hidden_%s.json'
MONEY_ICON = 'd:/ymir work/ui/game/windows/money_icon.sub'
YANG_VNUM = 1

BAR_HEIGHT = 22
BUTTON_HEIGHT = 20
START_Y = 28
START_GAP = 6
LEFT_WIDTH = 128
RIGHT_X = 136
RIGHT_WIDTH = PAGE_WIDTH - RIGHT_X
SOURCE_HEAD_HEIGHT = 20
SOURCE_Y = 24
SOURCE_HEIGHT = 21
SOURCE_STEP = 24
ACTION_Y = 28
ACTION_WIDTH = 78
ACTION_GAP = 6
SPARK_Y = 54
SPARK_HEIGHT = 24
SPARK_LABEL_WIDTH = 120
SPARK_MINUTES = 40
SPARK_STEP = 2
LIST_Y = 84
LIST_HEIGHT = PAGE_HEIGHT - LIST_Y
LIST_GAP = 3
SCROLL_WIDTH = 5
SCROLL_GAP = 4
ROW_WIDTH = RIGHT_WIDTH - SCROLL_WIDTH - SCROLL_GAP
ICON_BOX = 40
ROW_TEXT_X = ICON_BOX + 6
ROW_RIGHT_MARGIN = 10
COUNT_WIDTH = 80
ROW_POOL = 14
WHEEL_ROWS = 2
YANG_ROW = 0

# ---------------------------------------------------------------- the Historia and Statystyki tabs

RESULT_DATABASE = 5
DASH = '-'
SUBHEAD_HEIGHT = 22
TABLE_Y = SUBHEAD_HEIGHT + 4
TABLE_VIEW_HEIGHT = PAGE_HEIGHT - TABLE_Y
TABLE_WIDTH = PAGE_WIDTH - SCROLL_WIDTH - SCROLL_GAP
TABLE_WHEEL_LINES = 3
TABLE_CELLS = 6
CELL_PAD = 10
BAR_PAD = 14
BAR_THICKNESS = 5
ICON_PAD = 6
ICON_COLUMN = 32

# (kind, columns, cells, extra, frame): columns = ((width, align), ...) adding up to TABLE_WIDTH, align 'left' /
# 'right' / 'center' or 'bar'; extra: TOTAL the grey texts under the cells, BAR (share, key, selected), ITEM the vnum,
# BUTTONS whether "Usun zaznaczona" works; frame FRAME_TOP / FRAME_BOTTOM: the section's first / last line.
KIND_GAP = 0
KIND_TITLE = 1
KIND_HEAD = 2
KIND_ROW = 3
KIND_TOTAL = 4
KIND_BAR = 5
KIND_ITEM = 6
KIND_NOTE = 7
KIND_BUTTONS = 8
FRAME_TOP = 1
FRAME_BOTTOM = 2
LINE_HEIGHTS = {
	KIND_GAP: 6, KIND_TITLE: 23, KIND_HEAD: 23, KIND_ROW: 21,
	KIND_TOTAL: 34, KIND_BAR: 21, KIND_ITEM: 36, KIND_NOTE: 21, KIND_BUTTONS: 30,
}
LINE_GAP = (KIND_GAP, (), (), None, 0)
TOTAL_MIDDLE = 11
TOTAL_SUB_MIDDLE = 24
BUTTON_WIDE = 116

TEXT_HISTORY = 'Historia'
TEXT_STATS = 'Statystyki'
HISTORY_COLUMNS = ((122, 'left'), (82, 'right'), (104, 'right'), (82, 'right'), (72, 'right'), (68, 'center'))
TEXT_HISTORY_TITLES = ('Data', 'Czas', 'Yang', 'Przedmioty', 'Zabici', 'Koniec')
TEXT_HISTORY_EMPTY = 'Brak zako\xf1czonych sesji.'
TEXT_REASONS = {0: 'r\xeacznie', 1: 'limit', 2: 'porzucona'}

WIDE_COLUMNS = ((TABLE_WIDTH, 'center'),)
SUMMARY_COLUMNS = ((265, 'left'), (265, 'right'))
SOURCE_COLUMNS = ((128, 'left'), (134, 'right'), (134, 'right'), (134, 'right'))
PERIOD_COLUMNS = ((200, 'left'), (165, 'right'), (165, 'right'))
RECORD_COLUMNS = ((210, 'left'), (160, 'right'), (160, 'right'))
CATEGORY_COLUMNS = ((130, 'left'), (180, 'bar'), (110, 'right'), (110, 'right'))
RANK_COLUMNS = ((136, 'left'), (252, 'left'), (142, 'right'))
MAP_COLUMNS = ((175, 'left'), (125, 'right'), (125, 'right'), (105, 'right'))
SOURCE_KEYS = (('ym', 'im', 'km'), ('ys', 'is', 'ks'), ('yb', 'ib', 'kb'))
TEXT_SUMMARY = 'Podsumowanie'
TEXT_SUMMARY_ROWS = ('Sesje (z bie\xbf\xb9c\xb9)', '\xa3\xb9czny czas', '\x8cr. czas sesji', '\x8cr. yang na sesj\xea',
	'Do\x9cwiadczenie \xb3\xb9cznie', 'Yang na zab\xf3jstwo', 'Przedmioty na 100 zab\xf3jstw')
TEXT_SOURCE_TITLES = (TEXT_SOURCES, TEXT_YANG, 'Przedmioty', 'Zabici')
TEXT_SOURCE_ROWS = TEXT_FILTERS[1:]
TEXT_TOTAL = 'Razem'
TEXT_PERIOD_TITLES = ('Okres', 'Sesje', TEXT_YANG)
TEXT_PERIOD_ROWS = ('Dzi\x9c', 'Ostatnie 7 dni')
TEXT_RECORD_TITLES = ('Rekordy', 'Wynik', 'Kiedy')
TEXT_RECORD_ROWS = ('Najlepsza sesja (yang)', 'Rekord yang/h', 'Najd\xb3u\xbfsza sesja', 'Najwi\xeacej zab\xf3jstw')
TEXT_CATEGORY_TITLES = ('Kategorie', 'Udzia\xb3', 'Ilo\x9c\xe6', '%')
TEXT_CATEGORIES = ('Materia\xb3y', 'U\xbfytkowe', 'Bronie', 'Zbroje', 'Bi\xbfuteria', 'Inne')
TEXT_TOP_TITLES = ('#', 'Top przedmiot\xf3w', 'Ilo\x9c\xe6')
TEXT_MOB_TITLES = ('#', 'Najcz\xea\x9cciej zabijani', 'Zabici')
TEXT_MAP_TITLES = ('Mapy', TEXT_YANG, 'Przedmioty', 'Zabici')
TEXT_NO_DATA = 'Brak danych.'
TEXT_NEW_CATEGORY = 'Nowa kategoria'
TEXT_DELETE_CATEGORY = 'Usu\xf1 zaznaczon\xb9'
TEXT_CATEGORY_NAME = 'Nowa kategoria - nazwa'
TEXT_CATEGORY_WORDS = 'S\xb3owa z nazw przedmiot\xf3w (po przecinku)'
TEXT_CATEGORY_FULL = 'Mo\xbfesz mie\xe6 najwy\xbfej %d w\xb3asnych kategorii.'
TEXT_CATEGORY_TWICE = 'Taka kategoria ju\xbf jest.'

CATEGORY_FILE = 'cache/farm_categories_%s.json'
CATEGORY_MAX = 6
CATEGORY_NAME_LEN = 16
CATEGORY_WORDS_LEN = 48
# The base categories' keys in a BAR line: 0..5; one's own: 'c<index>'.

# CP1250's capital Polish letters and their small ones (str.lower() knows only ASCII).
_PL_UPPER = '\xa5\xc6\xca\xa3\xd1\xd3\x8c\x8f\xaf'
_PL_LOWER = '\xb9\xe6\xea\xb3\xf1\xf3\x9c\x9f\xbf'


def LowerPl(text):
	text = text.lower()
	for upper, lower in zip(_PL_UPPER, _PL_LOWER):
		text = text.replace(upper, lower)
	return text


def ParseInt(value, default=0):
	return uisidekick.ParseInt(value, default)


def _Numbers(words, names):
	"""The words as a dict of non-negative numbers by the names; None when short."""
	if len(words) < len(names):
		return None
	row = {}
	for name, word in zip(names, words):
		row[name] = max(0, ParseInt(word))
	return row


def _Tuples(words, size):
	"""The words 'a:b:c' as tuples of size numbers; a malformed word is skipped."""
	rows = []
	for word in words:
		parts = word.split(':')
		if len(parts) != size:
			continue
		numbers = [ParseInt(part, -1) for part in parts]
		if min(numbers) >= 0:
			rows.append(tuple(numbers))
	return rows


def ParseInfo(args):
	"""FarmInfo's words after the command as a dict (INFO_FIELDS and 'ylast'); None when the protocol is another
	one or the line is short."""
	if len(args) < 1 + len(INFO_FIELDS) or ParseInt(args[0], -1) != PROTOCOL:
		return None
	info = _Numbers(args[1:], INFO_FIELDS)
	info['ylast'] = max(0, ParseInt(args[1 + len(INFO_FIELDS)])) if len(args) > 1 + len(INFO_FIELDS) else 0
	return info


def ParseItems(args):
	"""FarmItems' words as (src, [(vnum, cnt, last), ...]); None when malformed."""
	if len(args) < 2:
		return None
	src = ParseInt(args[0], -1)
	if src not in (SOURCE_MONSTERS, SOURCE_METINS, SOURCE_BOSSES):
		return None
	return src, _Tuples(args[2:], 3)


def ParseSpark(args):
	"""FarmSpark's words as (minute, [counts]); None when malformed."""
	if len(args) < 2:
		return None
	minute = ParseInt(args[0], -1)
	if minute < 0:
		return None
	return minute, [max(0, ParseInt(word)) for word in args[2:2 + SPARK_MINUTES]]


def ParseHist(args):
	return _Numbers(args, HIST_FIELDS)


def FormatClock(seconds):
	"""hh:mm:ss; the hours go past 24."""
	seconds = max(0, int(seconds))
	return '%02d:%02d:%02d' % (seconds // 3600, seconds // 60 % 60, seconds % 60)


def FormatNumber(value):
	"""1234567 -> '1.234.567'."""
	digits = str(max(0, int(value)))
	parts = []
	while len(digits) > 3:
		parts.insert(0, digits[-3:])
		digits = digits[:-3]
	parts.insert(0, digits)
	return '.'.join(parts)


def _FormatTime(pattern, unix):
	if unix <= 0:
		return DASH
	try:
		import time
		return time.strftime(pattern, time.localtime(unix))
	except Exception:
		return DASH


def FormatDate(unix):
	"""dd/mm/yyyy hh:mm:ss (the tooltip's "Ostatni drop")."""
	return _FormatTime('%d/%m/%Y %H:%M:%S', unix)


def FormatShortDate(unix):
	"""dd/mm hh:mm (the records' "Kiedy")."""
	return _FormatTime('%d/%m %H:%M', unix)


def FormatHistoryDate(unix):
	"""dd/mm/yyyy hh:mm (Historia's "Data")."""
	return _FormatTime('%d/%m/%Y %H:%M', unix)


def FormatPerHour(value, seconds):
	"""'1.234/h' of a total over the active seconds; a dash when there are none."""
	if seconds <= 0:
		return DASH
	return '%s/h' % FormatNumber(value * 3600 // seconds)


def ItemName(vnum):
	try:
		import uidropwiki
		return uidropwiki.ItemName(vnum)
	except Exception:
		return str(vnum)


def ItemIcon(vnum):
	try:
		import uidropwiki
		return uidropwiki.ItemIcon(vnum)
	except Exception:
		return ''


def MobName(vnum):
	try:
		import uidropwiki
		return uidropwiki.MobName(vnum)
	except Exception:
		return str(vnum)


def MapName(index):
	try:
		import uidropwiki
		return uidropwiki.MapName(index, '')
	except Exception:
		return 'Mapa %d' % index


def FilterTotals(info, index):
	"""(items, yang) of a filter from FarmInfo's dict: FILTER_ALL adds the three sources."""
	if index == FILTER_ALL:
		words = SOURCE_WORDS
	elif 1 <= index <= len(SOURCE_WORDS):
		words = (SOURCE_WORDS[index - 1],)
	else:
		words = ()
	count = 0
	yang = 0
	for countWord, yangWord in words:
		count += info[countWord]
		yang += info[yangWord]
	return count, yang


def BuildList(items, index, hidden, showHidden):
	"""The item rows of a filter: ([(vnum, count, last), ...], total), the most dropped first; the hidden vnums
	are left out unless showHidden, the total counts every item of the filter."""
	source = None
	if index != FILTER_ALL:
		source = index - 1
	sums = {}
	for (vnum, src), (count, last) in items.items():
		if count <= 0 or (source is not None and src != source):
			continue
		old = sums.get(vnum)
		if old is None:
			sums[vnum] = (count, last)
		else:
			sums[vnum] = (old[0] + count, max(old[1], last))
	rows = []
	total = 0
	for vnum, (count, last) in sums.items():
		total += count
		if showHidden or vnum not in hidden:
			rows.append((vnum, count, last))
	rows.sort(key=lambda row: (-row[1], row[0]))
	return rows, total


def _CharacterName():
	try:
		return player.GetName()
	except Exception:
		return ''


def _LoadJson(path):
	text = file_utils.GetFileContent(path)
	if not text:
		return None
	try:
		return json.loads(text)
	except Exception:
		return None


def _SaveJson(path, value):
	try:
		file_utils.WriteFile(path, json.dumps(value))
	except Exception:
		pass


def LoadHidden(name):
	"""The vnums this character has hidden (0 = the Yang row), [] when there is no file."""
	values = _LoadJson(HIDDEN_FILE % name)
	vnums = []
	if isinstance(values, list):
		for value in values:
			try:
				vnums.append(int(value))
			except (TypeError, ValueError):
				pass
	return vnums


def SaveHidden(name, hidden):
	_SaveJson(HIDDEN_FILE % name, sorted(hidden))


def _Plain(text):
	"""A saved text as the client's CP1250 str: SaveCategories stores the bytes as latin-1 text and simplejson gives
	unicode back."""
	if isinstance(text, unicode):
		return text.encode('latin-1', 'replace')
	return str(text)


def LoadCategories(name):
	"""This character's own categories: [{'name': str, 'words': [str, ...]}, ...]."""
	values = _LoadJson(CATEGORY_FILE % name)
	categories = []
	if isinstance(values, list):
		for value in values[:CATEGORY_MAX]:
			if not isinstance(value, dict):
				continue
			title = _Plain(value.get('name', '')).strip()
			words = [LowerPl(_Plain(word).strip()) for word in value.get('words', []) if _Plain(word).strip()]
			if title and words:
				categories.append({'name': title, 'words': words})
	return categories


def SaveCategories(name, categories):
	# Stored as latin-1 text of the CP1250 bytes, read back the same way (_Plain).
	_SaveJson(CATEGORY_FILE % name, [{'name': c['name'].decode('latin-1'),
		'words': [word.decode('latin-1') for word in c['words']]} for c in categories])


def CategoryOf(categories, itemName):
	"""The index of the first own category whose word is in the item's name, None when none is."""
	text = LowerPl(itemName)
	for index, category in enumerate(categories):
		for word in category['words']:
			if word and word in text:
				return index
	return None


# ---------------------------------------------------------------- the queue (the package's)

_queue = {'pending': []}


def InGame():
	return uisidekick.InGame()


def _LineFree(now):
	return now >= uisidekick._queue['next']


def _Send(text, now):
	uisidekick._queue['next'] = now + COMMAND_SPACING
	net.SendChatPacket(PREFIX + text)


def SendCommand(text):
	"""An order: at once when the line is free, else after those before it (an order already waiting waits once)."""
	now = clientclock.Now()
	if not _queue['pending'] and _LineFree(now) and InGame():
		_Send(text, now)
	elif text not in _queue['pending']:
		_queue['pending'].append(text)


def PumpCommands():
	if not _queue['pending'] or not InGame():
		return False
	now = clientclock.Now()
	if not _LineFree(now):
		return False
	_Send(_queue['pending'].pop(0), now)
	return True


def TryPoll(text):
	"""A poll, only when no order of this window or of the companion's waits and the line is free."""
	if _queue['pending'] or uisidekick.HasPendingCommands() or not InGame():
		return False
	now = clientclock.Now()
	if not _LineFree(now):
		return False
	_Send(text, now)
	return True


def ResetCommands():
	_queue['pending'] = []


def Destroy():
	"""The game window's Close (game.py) drops the orders still waiting."""
	ResetCommands()


class _Pump(ui.Window):
	"""A shown window with no size: its OnUpdate sends the queued orders also while the farming window is shut."""

	def __init__(self):
		ui.Window.__init__(self)
		self.AddFlag('not_pick')
		self.Show()

	def OnUpdate(self):
		PumpCommands()


# ---------------------------------------------------------------- drawing

def _Rect(parent, x, y, width, height, color):
	"""A filled rectangle the mouse goes through."""
	bar = ui.Bar()
	bar.SetParent(parent)
	bar.SetPosition(x, y)
	bar.SetSize(max(0, width), max(0, height))
	bar.SetColor(color)
	bar.AddFlag('not_pick')
	bar.Show()
	return bar


def _Text(parent, x, y, text='', color=COLOR_TEXT, align=None, bold=False):
	"""A line of text the mouse goes through; y is its middle; align None (x the left edge), 'center' or 'right'."""
	line = ui.TextLine()
	line.SetParent(parent)
	line.AddFlag('not_pick')
	if bold:
		line.SetBold()
	line.SetPackedFontColor(color)
	if align == 'center':
		line.SetHorizontalAlignCenter()
	elif align == 'right':
		line.SetHorizontalAlignRight()
	line.SetVerticalAlignCenter()
	line.SetPosition(x, y)
	line.SetText(text)
	line.Show()
	return line


class _Frame(ui.Window):
	"""A box with a one pixel border and cut corners (the screenshots' rounded boxes)."""

	def __init__(self, width, height, border=COLOR_BOX_BORDER, fill=COLOR_BOX_FILL):
		ui.Window.__init__(self)
		self.fills = [_Rect(self, 0, 0, 0, 0, fill) for number in range(3)]
		self.edges = [_Rect(self, 0, 0, 0, 0, border) for number in range(8)]
		self.border = border
		self.fill = fill
		self.Resize(width, height)

	def Resize(self, width, height):
		self.SetSize(width, height)
		w, h = width, height
		places = ((1, 2, w - 2, h - 4), (2, 1, w - 4, 1), (2, h - 2, w - 4, 1))
		for bar, (x, y, bw, bh) in zip(self.fills, places):
			bar.SetPosition(x, y)
			bar.SetSize(max(0, bw), max(0, bh))
		places = ((2, 0, w - 4, 1), (2, h - 1, w - 4, 1), (0, 2, 1, h - 4), (w - 1, 2, 1, h - 4),
			(1, 1, 1, 1), (w - 2, 1, 1, 1), (1, h - 2, 1, 1), (w - 2, h - 2, 1, 1))
		for bar, (x, y, bw, bh) in zip(self.edges, places):
			bar.SetPosition(x, y)
			bar.SetSize(max(0, bw), max(0, bh))

	def SetColors(self, border, fill):
		if border != self.border:
			self.border = border
			for bar in self.edges:
				bar.SetColor(border)
		if fill != self.fill:
			self.fill = fill
			for bar in self.fills:
				bar.SetColor(fill)


def _MakeFrame(parent, x, y, width, height, border=COLOR_BOX_BORDER, fill=COLOR_BOX_FILL, pick=False):
	frame = _Frame(width, height, border, fill)
	frame.SetParent(parent)
	frame.SetPosition(x, y)
	frame.AddFlag('attach' if pick else 'not_pick')
	frame.Show()
	return frame


class _FlatButton(_Frame):
	"""A drawn button: a box, its text in the middle; the style is (fill, border, hover fill, text colour). event
	is a ui.__mem_func__ (a weak proxy: no cycle keeps a window alive), called with args."""

	def __init__(self, width, height, text, style, event=None, *args):
		_Frame.__init__(self, width, height, style[1], style[0])
		self.style = style
		self.event = event
		self.args = args
		self.hover = False
		self.enabled = True
		self.text = _Text(self, width // 2, height // 2, text, style[3], 'center')

	def SetEvent(self, event, *args):
		self.event = event
		self.args = args

	def SetText(self, text):
		self.text.SetText(text)

	def SetStyle(self, style):
		self.style = style
		self._Paint()

	def SetTextColor(self, color):
		self.text.SetPackedFontColor(color)

	def Enable(self, enabled):
		self.enabled = enabled
		self._Paint()

	def _Paint(self):
		fill, border, hover, color = self.style
		self.SetColors(border, hover if self.hover and self.enabled else fill)
		self.text.SetPackedFontColor(color)

	def OnMouseOverIn(self):
		self.hover = True
		self._Paint()

	def OnMouseOverOut(self):
		self.hover = False
		self._Paint()

	def OnMouseLeftButtonUp(self):
		if self.enabled and self.event:
			self.event(*self.args)


class _ThumbButton(ui.DragButton):
	"""The thin scroll bar's thumb: a drag button with a bar inside."""

	def __init__(self):
		ui.DragButton.__init__(self)
		self.bar = _Rect(self, 0, 0, SCROLL_WIDTH, 1, COLOR_SCROLL_THUMB)

	def SetThumbHeight(self, height):
		ui.DragButton.SetSize(self, SCROLL_WIDTH, height)
		self.bar.SetSize(SCROLL_WIDTH, height)


class _ThinScroll(ui.Window):
	"""The screenshots' thin scroll bar: a dark track and a light thumb; onScroll(pos 0..1) when the mouse moves it."""

	def __init__(self, height, onScroll):
		ui.Window.__init__(self)
		self.SetSize(SCROLL_WIDTH, height)
		self.height = height
		self.onScroll = onScroll
		self.thumbHeight = height
		self.track = _Rect(self, 0, 0, SCROLL_WIDTH, height, COLOR_SCROLL_TRACK)
		thumb = _ThumbButton()
		thumb.SetParent(self)
		thumb.SetPosition(0, 0)
		thumb.SetMoveEvent(ui.__mem_func__(self._OnMove))
		thumb.Show()
		self.thumb = thumb
		self.SetPage(1.0)

	def SetPage(self, fraction):
		self.thumbHeight = max(16, min(self.height, int(self.height * fraction)))
		self.thumb.SetThumbHeight(self.thumbHeight)
		self.thumb.SetRestrictMovementArea(0, 0, SCROLL_WIDTH, self.height)

	def SetPos(self, pos):
		room = self.height - self.thumbHeight
		self.thumb.SetPosition(0, int(round(max(0.0, min(1.0, pos)) * room)))

	def _OnMove(self):
		room = self.height - self.thumbHeight
		if room <= 0:
			return
		x, y = self.thumb.GetLocalPosition()
		self.thumb.SetPosition(0, max(0, min(room, y)))
		self.onScroll(float(max(0, min(room, y))) / room)

	def OnMouseLeftButtonDown(self):
		room = self.height - self.thumbHeight
		if room <= 0:
			return True
		x, y = self.GetMouseLocalPosition()
		pos = float(max(0, min(room, y - self.thumbHeight // 2))) / room
		self.SetPos(pos)
		self.onScroll(pos)
		return True


# ---------------------------------------------------------------- the Sesja tab's parts

class _FilterRow(_Frame):
	"""A source filter: the name on the left, the item count on the right, the share bar under them."""

	def __init__(self, index, width, text, onClick):
		_Frame.__init__(self, width, SOURCE_HEIGHT)
		self.index = index
		self.width = width
		self.onClick = onClick
		self.selected = False
		self.hover = False
		self.nameText = _Text(self, 10, SOURCE_HEIGHT // 2 - 1, text)
		self.countText = _Text(self, width - 9, SOURCE_HEIGHT // 2 - 1, '', COLOR_DIM, 'right')
		self.fillBar = _Rect(self, 10, SOURCE_HEIGHT - 4, 1, 2, COLOR_BAR)
		self.fillBar.Hide()

	def SetCount(self, count, share):
		# The screenshots write these counts without dots.
		self.countText.SetText(str(max(0, int(count))))
		if share > 0 and self.index != FILTER_ALL:
			self.fillBar.SetSize(max(2, int((self.width - 19) * min(1.0, share))), 2)
			self.fillBar.Show()
		else:
			self.fillBar.Hide()

	def SetSelected(self, selected):
		self.selected = selected
		self._Paint()

	def _Paint(self):
		if self.selected:
			self.SetColors(COLOR_TAB_ON_BORDER, COLOR_TAB_ON_FILL)
			self.countText.SetPackedFontColor(COLOR_TEXT)
		else:
			self.SetColors(COLOR_BOX_BORDER, COLOR_BOX_HOVER if self.hover else COLOR_BOX_FILL)
			self.countText.SetPackedFontColor(COLOR_DIM)

	def OnMouseOverIn(self):
		self.hover = True
		self._Paint()

	def OnMouseOverOut(self):
		self.hover = False
		self._Paint()

	def OnMouseLeftButtonUp(self):
		self.onClick(self.index)


class _WheelWindow(ui.Window):
	"""The list's area: the wheel over it (and over its empty places) scrolls."""

	def __init__(self, onWheel):
		ui.Window.__init__(self)
		self.onWheel = onWheel

	def OnMouseWheel(self, nLen):
		self.onWheel(-1 if nLen > 0 else 1)
		return True


def _IconSize(path, cache):
	"""(width, height) of an icon, read once by loading it into a hidden image."""
	size = cache.get(path)
	if size is None:
		size = (32, 32)
		try:
			probe = ui.ImageBox()
			probe.LoadImage(path)
			size = (max(1, probe.GetWidth()), max(1, probe.GetHeight()))
		except Exception:
			pass
		cache[path] = size
	return size


def RowHeight(iconHeight):
	"""A list row as tall as its icon (the screenshots' bow is a tall row): 32 -> 34, 64 -> 50, 96 -> 64."""
	if iconHeight > 64:
		return 64
	if iconHeight > 32:
		return 50
	return 34


def _PlaceIcon(row, path, size, dim, height, left=0, box=ICON_BOX):
	"""Shows an item's icon in row.icon: shrunk to fit a box wide and height high at x = left, in its middle."""
	if not path:
		row.icon.Hide()
		row.iconPath = ''
		return
	try:
		if path != row.iconPath:
			row.icon.LoadImage(path)
			row.iconPath = path
		width, iconHeight = size
		scale = min(1.0, float(height - 4) / iconHeight, float(box - 4) / width)
		row.icon.SetScale(scale, scale)
		row.icon.SetPosition(left + int((box - width * scale) // 2), int((height - iconHeight * scale) // 2))
		row.icon.SetAlpha(0.4 if dim else 1.0)
		row.icon.Show()
	except Exception:
		row.icon.Hide()
		row.iconPath = ''


class _FarmRow(_Frame):
	"""One line of the list: the icon, the name, the count and, under the name, a bar of the item's share."""

	def __init__(self, index, width, onOver, onOut, onClick, onWheel):
		_Frame.__init__(self, width, 34)
		self.index = index
		self.width = width
		self.onOver = onOver
		self.onOut = onOut
		self.onClick = onClick
		self.onWheel = onWheel
		self.iconPath = ''
		self.hover = False
		self.highlight = False
		self.trackWidth = width - ROW_TEXT_X - ROW_RIGHT_MARGIN
		self.icon = ui.ExpandedImageBox()
		self.icon.SetParent(self)
		self.icon.AddFlag('not_pick')
		self.icon.Hide()
		self.nameText = _Text(self, ROW_TEXT_X, 12)
		self.countText = _Text(self, width - ROW_RIGHT_MARGIN, 12, '', COLOR_GOLD, 'right')
		self.track = _Rect(self, ROW_TEXT_X, 26, self.trackWidth, 3, COLOR_TRACK)
		self.fillBar = _Rect(self, ROW_TEXT_X, 26, 2, 3, COLOR_BAR)

	def SetYang(self, amount, hidden, path, size):
		height = 34
		self.Resize(self.width, height)
		self.highlight = True
		self._Paint()
		_PlaceIcon(self, path, size, hidden, height)
		self._SetTexts(TEXT_YANG, amount, hidden, height // 2)
		self.track.Hide()
		self.fillBar.Hide()

	def SetItem(self, vnum, count, share, hidden, path, size):
		height = RowHeight(size[1])
		self.Resize(self.width, height)
		self.highlight = False
		self._Paint()
		_PlaceIcon(self, path, size, hidden, height)
		middle = height // 2 - 4
		self._SetTexts(ItemName(vnum), count, hidden, middle)
		barY = middle + 11
		self.track.SetPosition(ROW_TEXT_X, barY)
		self.fillBar.SetPosition(ROW_TEXT_X, barY)
		self.fillBar.SetSize(max(2, min(self.trackWidth, int(self.trackWidth * share))), 3)
		self.fillBar.SetColor(COLOR_HIDDEN if hidden else COLOR_BAR)
		self.track.Show()
		self.fillBar.Show()

	def _SetTexts(self, name, count, hidden, middle):
		self.countText.SetText(FormatNumber(count))
		self.countText.SetPosition(self.width - ROW_RIGHT_MARGIN, middle)
		self.nameText.SetPosition(ROW_TEXT_X, middle)
		uisidekick.FitText(self.nameText, name, self.width - ROW_TEXT_X - ROW_RIGHT_MARGIN - COUNT_WIDTH)
		self.countText.SetPackedFontColor(COLOR_HIDDEN if hidden else COLOR_GOLD)
		self.nameText.SetPackedFontColor(COLOR_HIDDEN if hidden else COLOR_TEXT)

	def _Paint(self):
		if self.hover or self.highlight:
			self.SetColors(COLOR_BOX_BORDER, COLOR_BOX_HOVER)
		else:
			self.SetColors(COLOR_BOX_BORDER, COLOR_BOX_FILL)

	def OnMouseOverIn(self):
		self.hover = True
		self._Paint()
		self.onOver(self.index)

	def OnMouseOverOut(self):
		self.hover = False
		self._Paint()
		self.onOut(self.index)

	def OnMouseLeftButtonUp(self):
		self.onClick(self.index)

	def OnMouseWheel(self, nLen):
		self.onWheel(-1 if nLen > 0 else 1)
		return True


class _Spark(ui.Window):
	"""The item line chart of the last minutes: one thin column per SPARK_STEP pixels from the last point's
	height to this one's (a line drawn with bars)."""

	def __init__(self, width, height):
		ui.Window.__init__(self)
		self.AddFlag('not_pick')
		self.SetSize(width, height)
		self.width = width
		self.height = height
		self.columns = [_Rect(self, x, 0, SPARK_STEP, 1, COLOR_SPARK) for x in range(0, width, SPARK_STEP)]

	def SetValues(self, values):
		"""values: the counts, oldest first; the line runs from the left edge to the right one."""
		top = max(values) if values else 0
		count = len(values)
		usable = self.height - 3

		def Height(position):
			if count < 2 or top <= 0:
				return float(self.height - 2)
			at = position * (count - 1)
			low = int(at)
			high = min(count - 1, low + 1)
			value = values[low] + (values[high] - values[low]) * (at - low)
			return self.height - 2 - usable * float(value) / top

		last = None
		for number, bar in enumerate(self.columns):
			x = number * SPARK_STEP
			y = Height(float(x) / max(1, self.width - SPARK_STEP))
			if last is None:
				last = y
			upper = int(min(last, y))
			lower = int(max(last, y))
			bar.SetPosition(x, upper)
			bar.SetSize(SPARK_STEP, max(1, lower - upper + 1))
			last = y


# ---------------------------------------------------------------- the tables

class _TableRow(ui.Window):
	"""One line of a table (Historia, Statystyki) inside a framed section: SetData(line) refills it for any kind
	of line. The windows are made once; a line only moves, shows and hides them."""

	def __init__(self, width, view):
		ui.Window.__init__(self)
		self.AddFlag('attach')
		self.width = width
		self.view = _proxy(view)	# the view holds its rows: a weak one back
		self.iconPath = ''
		self.key = None
		self.SetSize(width, LINE_HEIGHTS[KIND_ROW])
		self.fill = _Rect(self, 0, 0, width, 1, COLOR_ROW_FILL)
		self.rowLine = _Rect(self, 1, 0, width - 2, 1, COLOR_ROW_LINE)
		self.columnLines = [_Rect(self, 0, 0, 1, 1, COLOR_COLUMN_LINE) for number in range(TABLE_CELLS)]
		self.headLine = _Rect(self, 1, 0, width - 2, 1, COLOR_HEAD_LINE)
		self.left = _Rect(self, 0, 0, 1, 1, COLOR_SECTION_BORDER)
		self.right = _Rect(self, width - 1, 0, 1, 1, COLOR_SECTION_BORDER)
		self.top = _Rect(self, 2, 0, width - 4, 1, COLOR_SECTION_BORDER)
		self.bottom = _Rect(self, 2, 0, width - 4, 1, COLOR_SECTION_BORDER)
		self.corners = [_Rect(self, 0, 0, 1, 1, COLOR_SECTION_BORDER) for number in range(4)]
		self.icon = ui.ExpandedImageBox()
		self.icon.SetParent(self)
		self.icon.AddFlag('not_pick')
		self.icon.Hide()
		self.track = _Rect(self, 0, 0, 1, BAR_THICKNESS, COLOR_TRACK)
		self.fillBar = _Rect(self, 0, 0, 1, BAR_THICKNESS, COLOR_BAR)
		self.cells = [_Text(self, 0, 0) for number in range(TABLE_CELLS)]
		self.bolds = [_Text(self, 0, 0, '', COLOR_HEAD_TEXT, None, True) for number in range(TABLE_CELLS)]
		self.subs = [_Text(self, 0, 0, '', COLOR_DIM, None, True) for number in range(TABLE_CELLS)]
		self.buttons = []

	def _Buttons(self):
		if not self.buttons:
			view = self.view
			for text, style, name in ((TEXT_NEW_CATEGORY, STYLE_DARK, 'new'), (TEXT_DELETE_CATEGORY, STYLE_RED, 'delete')):
				button = _FlatButton(BUTTON_WIDE, BUTTON_HEIGHT, text, style, ui.__mem_func__(view.OnButton), name)
				button.SetParent(self)
				button.Hide()
				self.buttons.append(button)
		return self.buttons

	def SetData(self, line):
		kind, columns, cells, extra, frame = line
		w = self.width
		height = LINE_HEIGHTS[kind]
		self.SetSize(w, height)
		self.key = None
		for text in self.cells + self.bolds + self.subs:
			text.Hide()
		for bar in self.columnLines + self.corners:
			bar.Hide()
		for bar in (self.track, self.fillBar, self.rowLine, self.headLine, self.top, self.bottom):
			bar.Hide()
		for button in self.buttons:
			button.Hide()
		if kind != KIND_ITEM:
			self.icon.Hide()
		if kind == KIND_GAP:
			for bar in (self.fill, self.left, self.right):
				bar.Hide()
			return
		header = kind in (KIND_TITLE, KIND_HEAD)
		strong = header or kind == KIND_TOTAL
		fill = COLOR_ROW_FILL
		if header or kind == KIND_BUTTONS:
			fill = COLOR_HEAD_FILL
		elif kind == KIND_TOTAL:
			fill = COLOR_TOTAL_FILL
		elif kind == KIND_BAR and extra and extra[2]:
			fill = COLOR_ROW_SELECTED
		first = frame & FRAME_TOP
		last = frame & FRAME_BOTTOM
		self.fill.SetPosition(1, 1 if first else 0)
		self.fill.SetSize(w - 2, height - (1 if first else 0) - (1 if last else 0))
		self.fill.SetColor(fill)
		self.fill.Show()
		sideTop = 2 if first else 0
		sideHeight = height - sideTop - (2 if last else 0)
		for bar, x in ((self.left, 0), (self.right, w - 1)):
			bar.SetPosition(x, sideTop)
			bar.SetSize(1, max(0, sideHeight))
			bar.Show()
		if first:
			self.top.SetPosition(2, 0)
			self.top.Show()
			self.corners[0].SetPosition(1, 1)
			self.corners[1].SetPosition(w - 2, 1)
			self.corners[0].Show()
			self.corners[1].Show()
		if last:
			self.bottom.SetPosition(2, height - 1)
			self.bottom.Show()
			self.corners[2].SetPosition(1, height - 2)
			self.corners[3].SetPosition(w - 2, height - 2)
			self.corners[2].Show()
			self.corners[3].Show()
		if header:
			self.headLine.SetPosition(1, height - 1)
			self.headLine.Show()
		elif not first:
			self.rowLine.SetPosition(1, 0)
			self.rowLine.Show()
		if kind == KIND_BUTTONS:
			self._ShowButtons(height, extra)
			return
		if not header and kind != KIND_NOTE and len(columns) > 1:
			x = 0
			for number in range(min(len(columns), TABLE_CELLS) - 1):
				x += columns[number][0]
				bar = self.columnLines[number]
				bar.SetPosition(x, 1 if first else 0)
				bar.SetSize(1, height - (1 if first else 0) - (1 if last else 0))
				bar.Show()
		texts = self.bolds if strong else self.cells
		color = COLOR_HEAD_TEXT if strong else COLOR_TEXT
		if kind == KIND_NOTE:
			color = COLOR_DIM
		elif kind == KIND_BAR and extra and extra[2]:
			color = COLOR_GOLD
		middle = TOTAL_MIDDLE if kind == KIND_TOTAL else height // 2
		x = 0
		for number in range(min(len(columns), TABLE_CELLS)):
			width, align = columns[number]
			if align == 'bar' and kind == KIND_BAR:
				self._ShowBar(x, width, middle, extra[0])
			elif number < len(cells):
				pad = CELL_PAD
				if kind == KIND_ITEM and number == 1:
					pad += ICON_PAD + ICON_COLUMN
				self._Put(texts[number], x, width, 'center' if align == 'bar' else align, middle, cells[number], color, pad)
			x += width
		if kind == KIND_TOTAL and extra:
			x = 0
			for number in range(min(len(columns), len(extra), TABLE_CELLS)):
				width, align = columns[number]
				self._Put(self.subs[number], x, width, align, TOTAL_SUB_MIDDLE, extra[number], COLOR_DIM, CELL_PAD)
				x += width
		if kind == KIND_ITEM:
			path = ItemIcon(extra)
			_PlaceIcon(self, path, _IconSize(path, self.view.iconSizes) if path else (32, 32), False, height,
				columns[0][0] + ICON_PAD, ICON_COLUMN)
		if kind == KIND_BAR and extra:
			self.key = extra[1]

	def _ShowButtons(self, height, canDelete):
		buttons = self._Buttons()
		left = (self.width - 2 * BUTTON_WIDE - 8) // 2
		for number, button in enumerate(buttons):
			button.SetPosition(left + number * (BUTTON_WIDE + 8), (height - BUTTON_HEIGHT) // 2)
			button.Show()
		buttons[1].SetStyle(STYLE_RED if canDelete else STYLE_OFF)
		buttons[1].Enable(bool(canDelete))

	def _Put(self, cell, x, width, align, middle, text, color, pad):
		if align == 'right':
			cell.SetHorizontalAlignRight()
			cell.SetPosition(x + width - pad, middle)
		elif align == 'center':
			cell.SetHorizontalAlignCenter()
			cell.SetPosition(x + width // 2, middle)
		else:
			cell.SetHorizontalAlignLeft()
			cell.SetPosition(x + pad, middle)
		cell.SetPackedFontColor(color)
		cell.SetText(text)
		cell.Show()

	def _ShowBar(self, x, width, middle, share):
		trackWidth = max(1, width - 2 * BAR_PAD)
		top = middle - BAR_THICKNESS // 2
		self.track.SetPosition(x + BAR_PAD, top)
		self.track.SetSize(trackWidth, BAR_THICKNESS)
		self.track.Show()
		fillWidth = max(BAR_THICKNESS, min(trackWidth, int(trackWidth * share)))
		self.fillBar.SetPosition(x + BAR_PAD, top)
		self.fillBar.SetSize(fillWidth, BAR_THICKNESS)
		self.fillBar.Show()

	def OnMouseLeftButtonUp(self):
		if self.key is not None:
			self.view.OnAction('select', self.key)

	def OnMouseWheel(self, nLen):
		self.view.OnWheel(-1 if nLen > 0 else 1)
		return True


class _TableView(ui.Window):
	"""A column of table lines of different heights: a pool of _TableRow windows shows the lines from self.offset
	on (the ones that fit whole), the thin scroll bar and the wheel move the offset by lines. onAction(name, *args):
	the category buttons and a click on a category."""

	def __init__(self, width, height, onAction=None):
		ui.Window.__init__(self)
		self.AddFlag('attach')
		self.SetSize(width, height)
		self.viewHeight = height
		self.onAction = onAction
		self.lines = []
		self.heights = []
		self.pool = []
		self.offset = 0
		self.iconSizes = {}
		self.scroll = _ThinScroll(height, ui.__mem_func__(self._OnScroll))
		self.scroll.SetParent(self)
		self.scroll.SetPosition(width - SCROLL_WIDTH, 0)
		self.scroll.Hide()

	def OnAction(self, name, *args):
		if self.onAction:
			self.onAction(name, *args)

	def OnButton(self, name):
		self.OnAction(name)

	def SetLines(self, lines):
		self.lines = lines
		self.heights = [LINE_HEIGHTS[line[0]] for line in lines]
		self._FixOffset()
		self._Draw()

	def _MaxOffset(self):
		start = len(self.lines)
		total = 0
		while start > 0 and total + self.heights[start - 1] <= self.viewHeight:
			start -= 1
			total += self.heights[start]
		return start

	def _FixOffset(self):
		maxOffset = self._MaxOffset()
		self.offset = max(0, min(maxOffset, self.offset))
		if maxOffset <= 0:
			self.scroll.Hide()
			return
		self.scroll.SetPage(float(self.viewHeight) / max(1, sum(self.heights)))
		self.scroll.SetPos(float(self.offset) / maxOffset)
		self.scroll.Show()

	def _Draw(self):
		y = 0
		number = self.offset
		slot = 0
		while number < len(self.lines) and y + self.heights[number] <= self.viewHeight:
			if slot >= len(self.pool):
				row = _TableRow(TABLE_WIDTH, self)
				row.SetParent(self)
				self.pool.append(row)
			row = self.pool[slot]
			row.SetData(self.lines[number])
			row.SetPosition(0, y)
			row.Show()
			y += self.heights[number]
			number += 1
			slot += 1
		for row in self.pool[slot:]:
			row.Hide()

	def _SetOffset(self, offset):
		maxOffset = self._MaxOffset()
		offset = max(0, min(maxOffset, offset))
		if offset == self.offset:
			return
		self.offset = offset
		if maxOffset > 0:
			self.scroll.SetPos(float(offset) / maxOffset)
		self._Draw()

	def _OnScroll(self, pos):
		maxOffset = self._MaxOffset()
		if maxOffset <= 0:
			return
		offset = max(0, min(maxOffset, int(round(pos * maxOffset))))
		if offset != self.offset:
			self.offset = offset
			self._Draw()

	def OnWheel(self, direction):
		self._SetOffset(self.offset + direction * TABLE_WHEEL_LINES)

	def OnMouseWheel(self, nLen):
		self.OnWheel(-1 if nLen > 0 else 1)
		return True


def _Section(lines):
	"""The lines of one framed section: the first gets FRAME_TOP, the last FRAME_BOTTOM; a gap after it."""
	out = []
	for number, (kind, columns, cells, extra) in enumerate(lines):
		frame = 0
		if number == 0:
			frame |= FRAME_TOP
		if number == len(lines) - 1:
			frame |= FRAME_BOTTOM
		out.append((kind, columns, cells, extra, frame))
	out.append(LINE_GAP)
	return out


def BuildHistoryLines(hist):
	"""Historia's section, the newest on top; [] when there is none."""
	if not hist:
		return []
	lines = [(KIND_HEAD, HISTORY_COLUMNS, TEXT_HISTORY_TITLES, None)]
	for row in sorted(hist, key=lambda item: (item['start'], item['id']), reverse=True):
		lines.append((KIND_ROW, HISTORY_COLUMNS, (
			FormatHistoryDate(row['start']), FormatClock(row['active']), FormatNumber(row['yang']),
			FormatNumber(row['items']), FormatNumber(row['kills']), TEXT_REASONS.get(row['reason'], DASH)), None))
	return _Section(lines)


def _Zeros(names):
	return dict((name, 0) for name in names)


def CategoryRows(stats, categories, selected):
	"""The Kategorie rows: [(label, count, key)], the server's six less the items of one's own categories, then
	one's own; the most first."""
	base = list(stats.get('cat') or [0] * STAT_CATEGORIES)
	own = [0] * len(categories)
	if categories:
		for vnum, cat, count in stats.get('all') or []:
			index = CategoryOf(categories, ItemName(vnum))
			if index is None:
				continue
			own[index] += count
			if 0 <= cat < STAT_CATEGORIES:
				base[cat] = max(0, base[cat] - count)
	rows = [(TEXT_CATEGORIES[number], base[number], number) for number in range(STAT_CATEGORIES)]
	rows += [(category['name'], own[number], 'c%d' % number) for number, category in enumerate(categories)]
	rows.sort(key=lambda row: -row[1])
	return rows


def BuildStatsLines(stats, categories, selected):
	"""Statystyki's sections from FarmSessionWindow.stats (a missing part is zeros); the averages, the "/h" and
	one's own categories are worked out here."""
	total = stats.get('sum') or _Zeros(STAT_RECORDS['Sum'][1])
	period = stats.get('per') or _Zeros(STAT_RECORDS['Per'][1])
	record = stats.get('rec') or _Zeros(STAT_RECORDS['Rec'][1])
	seconds = total['active']
	sessions = total['sessions']
	yang = total['ym'] + total['ys'] + total['yb']
	items = total['im'] + total['is'] + total['ib']
	kills = total['km'] + total['ks'] + total['kb']

	values = (
		FormatNumber(sessions),
		FormatClock(seconds),
		FormatClock(seconds // sessions) if sessions > 0 else DASH,
		FormatNumber(yang // sessions) if sessions > 0 else DASH,
		'%s  (%s)' % (FormatNumber(total['exp']), FormatPerHour(total['exp'], seconds)),
		FormatNumber(yang // kills) if kills > 0 else DASH,
		FormatNumber(items * 100 // kills) if kills > 0 else DASH,
	)
	out = []
	section = [(KIND_TITLE, WIDE_COLUMNS, (TEXT_SUMMARY,), None)]
	for label, value in zip(TEXT_SUMMARY_ROWS, values):
		section.append((KIND_ROW, SUMMARY_COLUMNS, (label, value), None))
	out += _Section(section)

	section = [(KIND_HEAD, SOURCE_COLUMNS, TEXT_SOURCE_TITLES, None)]
	for label, (yangKey, itemsKey, killsKey) in zip(TEXT_SOURCE_ROWS, SOURCE_KEYS):
		section.append((KIND_ROW, SOURCE_COLUMNS, (label, FormatNumber(total[yangKey]),
			FormatNumber(total[itemsKey]), FormatNumber(total[killsKey])), None))
	section.append((KIND_TOTAL, SOURCE_COLUMNS, (TEXT_TOTAL, FormatNumber(yang), FormatNumber(items), FormatNumber(kills)),
		('', FormatPerHour(yang, seconds), FormatPerHour(items, seconds), FormatPerHour(kills, seconds))))
	out += _Section(section)

	out += _Section([
		(KIND_HEAD, PERIOD_COLUMNS, TEXT_PERIOD_TITLES, None),
		(KIND_ROW, PERIOD_COLUMNS, (TEXT_PERIOD_ROWS[0], FormatNumber(period['today_sessions']), FormatNumber(period['today_yang'])), None),
		(KIND_ROW, PERIOD_COLUMNS, (TEXT_PERIOD_ROWS[1], FormatNumber(period['week_sessions']), FormatNumber(period['week_yang'])), None),
	])

	section = [(KIND_HEAD, RECORD_COLUMNS, TEXT_RECORD_TITLES, None)]
	records = (
		(FormatNumber(record['yang']), record['yang_at']),
		(FormatNumber(record['yph']), record['yph_at']),
		(FormatClock(record['longest']), record['longest_at']),
		(FormatNumber(record['kills']), record['kills_at']),
	)
	for label, (value, at) in zip(TEXT_RECORD_ROWS, records):
		section.append((KIND_ROW, RECORD_COLUMNS, (label, value if at > 0 else DASH, FormatShortDate(at)), None))
	out += _Section(section)

	section = [(KIND_HEAD, CATEGORY_COLUMNS, TEXT_CATEGORY_TITLES, None)]
	rows = CategoryRows(stats, categories, selected)
	categorySum = sum(count for label, count, key in rows)
	biggest = max([count for label, count, key in rows] + [0])
	for label, count, key in rows:
		percent = '%.2f%%' % (count * 100.0 / categorySum) if categorySum > 0 else '0.00%'
		share = float(count) / biggest if biggest > 0 else 0.0
		section.append((KIND_BAR, CATEGORY_COLUMNS, (label, '', FormatNumber(count), percent),
			(share, key, key == selected)))
	section.append((KIND_BUTTONS, (), (), selected is not None))
	out += _Section(section)

	section = [(KIND_HEAD, RANK_COLUMNS, TEXT_TOP_TITLES, None)]
	top = stats.get('top') or []
	for rank, (vnum, count) in enumerate(top, 1):
		section.append((KIND_ITEM, RANK_COLUMNS, ('%d.' % rank, ItemName(vnum), FormatNumber(count)), vnum))
	if not top:
		section.append((KIND_NOTE, WIDE_COLUMNS, (TEXT_NO_DATA,), None))
	out += _Section(section)

	section = [(KIND_HEAD, RANK_COLUMNS, TEXT_MOB_TITLES, None)]
	mobs = stats.get('mob') or []
	for rank, (vnum, count) in enumerate(mobs, 1):
		section.append((KIND_ROW, RANK_COLUMNS, ('%d.' % rank, MobName(vnum), FormatNumber(count)), None))
	if not mobs:
		section.append((KIND_NOTE, WIDE_COLUMNS, (TEXT_NO_DATA,), None))
	out += _Section(section)

	section = [(KIND_HEAD, MAP_COLUMNS, TEXT_MAP_TITLES, None)]
	maps = stats.get('map') or []
	for index, mapYang, mapItems, mapKills in maps:
		section.append((KIND_ROW, MAP_COLUMNS, (MapName(index), FormatNumber(mapYang), FormatNumber(mapItems), FormatNumber(mapKills)), None))
	if not maps:
		section.append((KIND_NOTE, WIDE_COLUMNS, (TEXT_NO_DATA,), None))
	out += _Section(section)
	return out


# ---------------------------------------------------------------- the window

class FarmSessionWindow(ui.ScriptWindow):
	"""The farming session window. The parsed answers are kept on the window for the tabs:

	info         FarmInfo as a dict (INFO_FIELDS, 'ylast') plus 'received' (clientclock.Now when it came)
	items        {(vnum, src): (cnt, last_unix)}; cleared when FarmInfo brings another session id
	spark        (minute, [counts]) of FarmSpark, None before the first
	hist         [dict (HIST_FIELDS), ...], replaced by FarmHistEnd
	stats        {'sum', 'per', 'rec', 'cat', 'top', 'mob', 'map', 'all'}, replaced by FarmStatEnd
	categories   this character's own categories (cache/farm_categories_<name>.json)
	"""

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self._Initialize()
		self._Build()
		self.SelectTab(TAB_SESSION)
		self.Hide()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def _Initialize(self):
		self.board = None
		self.pump = None
		self.tabButtons = []
		self.pages = []
		self.widgets = []
		self.tab = TAB_SESSION
		self.nextStan = 0.0
		self.nextPelne = 0.0
		self.nextSecond = 0.0
		self.info = None
		self.items = {}
		self.itemsDirty = False
		self.itemsDone = False
		self.spark = None
		self.sparkShown = None
		self.hist = []
		self.histStaged = []
		self.histDone = False
		self.stats = {}
		self.statsStaged = {}
		self.statsDone = False
		self.lastResult = None
		self.sessionReady = False
		self.filter = FILTER_ALL
		self.showHidden = False
		self.hidden = set()
		self.characterName = ''
		self.listData = []
		self.listDirty = True
		self.shareTotal = 1
		self.offset = 0
		self.hoverRow = None
		self.statusUntil = 0.0
		self.question = None
		self.inputDialog = None
		self.newCategoryName = ''
		self.iconSizes = {}
		self.histReady = False
		self.histPending = False
		self.histError = ''
		self.statsReady = False
		self.statsPending = False
		self.statsError = ''
		self.categories = []
		self.selectedCategory = None

	@ui.WindowDestroy
	def Destroy(self):
		self.Hide()
		if self.pump:
			self.pump.Hide()
		ResetCommands()
		self.ClearDictionary()
		self._Initialize()

	def Hide(self):
		self._CloseQuestion()
		self._CloseInput()
		self._HideTip()
		ui.ScriptWindow.Hide(self)

	# -------------------------------------------------------------- building

	def _Build(self):
		self.SetSize(WINDOW_WIDTH, WINDOW_HEIGHT)
		self.SetCenterPosition()
		self.AddFlag('movable')
		self.AddFlag('float')

		board = ui.BoardWithTitleBar()
		board.SetParent(self)
		board.AddFlag('attach')
		board.SetPosition(0, 0)
		board.SetSize(WINDOW_WIDTH, WINDOW_HEIGHT)
		board.SetTitleName(TITLE)
		board.SetCloseEvent(ui.__mem_func__(self.Close))
		board.Show()
		self.board = board

		tabWidth = (PAGE_WIDTH - (TAB_COUNT - 1) * TAB_GAP) // TAB_COUNT
		for index in range(TAB_COUNT):
			button = _FlatButton(tabWidth, TAB_HEIGHT, TAB_LABELS[index], STYLE_TAB, ui.__mem_func__(self.SelectTab), index)
			button.SetParent(board)
			button.SetPosition(TAB_X + index * (tabWidth + TAB_GAP), TAB_Y)
			button.Show()
			self.tabButtons.append(button)

		for index in range(TAB_COUNT):
			page = ui.Window()
			page.SetParent(board)
			page.SetPosition(PAGE_X, PAGE_Y)
			page.SetSize(PAGE_WIDTH, PAGE_HEIGHT)
			page.AddFlag('attach')
			page.Hide()
			self.pages.append(page)

		self._BuildSessionTab(self.pages[TAB_SESSION])
		self._BuildHistoryTab(self.pages[TAB_HISTORY])
		self._BuildStatsTab(self.pages[TAB_STATS])
		self.pump = _Pump()

	def _Subheader(self, page, text):
		bar = _MakeFrame(page, 0, 0, PAGE_WIDTH, SUBHEAD_HEIGHT)
		self.widgets.append(bar)
		label = _Text(bar, PAGE_WIDTH // 2, SUBHEAD_HEIGHT // 2, text, COLOR_TEXT, 'center')
		self.widgets.append(label)
		return label

	def _BuildHistoryTab(self, page):
		self._Subheader(page, TEXT_HISTORY)
		view = _TableView(PAGE_WIDTH, TABLE_VIEW_HEIGHT)
		view.SetParent(page)
		view.SetPosition(0, TABLE_Y)
		view.Show()
		self.histView = view
		self.histNote = _Text(page, PAGE_WIDTH // 2, TABLE_Y + 60, '', COLOR_DIM, 'center')
		self.histReady = True

	def _BuildStatsTab(self, page):
		self._Subheader(page, TEXT_STATS)
		view = _TableView(PAGE_WIDTH, TABLE_VIEW_HEIGHT, ui.__mem_func__(self._OnStatsAction))
		view.SetParent(page)
		view.SetPosition(0, TABLE_Y)
		view.Show()
		self.statsView = view
		self.statsNote = _Text(page, PAGE_WIDTH // 2, TABLE_Y + 60, '', COLOR_DIM, 'center')
		self.statsReady = True

	# -------------------------------------------------------------- the Sesja tab

	def _Button(self, parent, x, y, width, text, style, event, *args):
		button = _FlatButton(width, BUTTON_HEIGHT, text, style, ui.__mem_func__(event), *args)
		button.SetParent(parent)
		button.SetPosition(x, y)
		button.Show()
		self.widgets.append(button)
		return button

	def _BuildSessionTab(self, page):
		self.tooltip = uiToolTip.ToolTip()
		self.tooltip.HideToolTip()
		self._BuildNoneView(page)
		self._BuildRunView(page)
		self.runView.Hide()
		self.sessionReady = True

	def _Container(self, page):
		window = ui.Window()
		window.SetParent(page)
		window.SetPosition(0, 0)
		window.SetSize(PAGE_WIDTH, PAGE_HEIGHT)
		window.AddFlag('attach')
		window.Show()
		self.widgets.append(window)
		return window

	def _BuildNoneView(self, page):
		"""No session: the bar and one button for each limit."""
		view = self._Container(page)
		self.noneView = view
		bar = _MakeFrame(view, 0, 0, PAGE_WIDTH, BAR_HEIGHT)
		self.widgets.append(bar)
		self.noneText = _Text(bar, PAGE_WIDTH // 2, BAR_HEIGHT // 2, TEXT_NONE, COLOR_TEXT, 'center')
		self.noneResult = _Text(view, PAGE_WIDTH // 2, START_Y + BUTTON_HEIGHT + 16, '', COLOR_RESULT, 'center')
		self.startButtons = []
		count = len(START_BUTTONS)
		width = (PAGE_WIDTH - (count - 1) * START_GAP) // count
		for number, (text, seconds) in enumerate(START_BUTTONS):
			self.startButtons.append(self._Button(view, number * (width + START_GAP), START_Y, width, text,
				STYLE_BUTTON, self._OnStart, seconds))

	def _BuildRunView(self, page):
		"""A session: the sources on the left; the clock, the buttons, the chart and the list on the right."""
		view = self._Container(page)
		self.runView = view

		column = _MakeFrame(view, 0, SOURCE_HEAD_HEIGHT + 1, LEFT_WIDTH, PAGE_HEIGHT - SOURCE_HEAD_HEIGHT - 1,
			COLOR_TAB_BORDER, COLOR_COLUMN_FILL)
		self.widgets.append(column)
		head = _MakeFrame(view, 0, 0, LEFT_WIDTH, SOURCE_HEAD_HEIGHT, COLOR_SECTION_BORDER, COLOR_HEAD_FILL)
		self.widgets.append(head)
		self.widgets.append(_Text(head, LEFT_WIDTH // 2, SOURCE_HEAD_HEIGHT // 2, TEXT_SOURCES, COLOR_HEAD_TEXT, 'center', True))
		self.sourceRows = []
		for index in range(FILTER_COUNT):
			row = _FilterRow(index, LEFT_WIDTH - 8, TEXT_FILTERS[index], ui.__mem_func__(self._OnFilter))
			row.SetParent(view)
			row.SetPosition(4, SOURCE_Y + index * SOURCE_STEP)
			row.Show()
			self.sourceRows.append(row)

		bar = _MakeFrame(view, RIGHT_X, 0, RIGHT_WIDTH, BAR_HEIGHT, COLOR_TAB_ON_BORDER, COLOR_BOX_FILL)
		self.widgets.append(bar)
		coin = ui.ImageBox()
		coin.SetParent(bar)
		coin.AddFlag('not_pick')
		coin.LoadImage(MONEY_ICON)
		coin.SetPosition(8, max(0, (BAR_HEIGHT - coin.GetHeight()) // 2))
		coin.Show()
		self.widgets.append(coin)
		self.clockText = _Text(bar, 12 + max(16, coin.GetWidth()), BAR_HEIGHT // 2, '', COLOR_TEXT, None, True)
		self.stateText = _Text(bar, RIGHT_WIDTH - 10, BAR_HEIGHT // 2, '', COLOR_DIM, 'right')

		self.pauseButton = self._Button(view, RIGHT_X, ACTION_Y, ACTION_WIDTH, TEXT_PAUSE, STYLE_RED, self._OnPause)
		self.endButton = self._Button(view, RIGHT_X + ACTION_WIDTH + ACTION_GAP, ACTION_Y, ACTION_WIDTH, TEXT_END,
			STYLE_RED, self._OnEnd)
		self.hiddenButton = self._Button(view, RIGHT_X + RIGHT_WIDTH - ACTION_WIDTH, ACTION_Y, ACTION_WIDTH, TEXT_HIDDEN,
			STYLE_BUTTON, self._OnToggleHidden)

		sparkBox = _MakeFrame(view, RIGHT_X, SPARK_Y, RIGHT_WIDTH, SPARK_HEIGHT)
		self.widgets.append(sparkBox)
		self.sparkText = _Text(sparkBox, 10, SPARK_HEIGHT // 2, TEXT_SPARK % 0, COLOR_DIM)
		spark = _Spark(RIGHT_WIDTH - SPARK_LABEL_WIDTH - 10, SPARK_HEIGHT - 8)
		spark.SetParent(sparkBox)
		spark.SetPosition(SPARK_LABEL_WIDTH, 4)
		spark.Show()
		self.sparkChart = spark
		# A FarmResult other than 0 stands in the chart's place for a few seconds.
		self.resultLine = _Text(sparkBox, RIGHT_WIDTH // 2, SPARK_HEIGHT // 2, '', COLOR_RESULT, 'center')

		area = _WheelWindow(ui.__mem_func__(self._OnListWheel))
		area.SetParent(view)
		area.SetPosition(RIGHT_X, LIST_Y)
		area.SetSize(RIGHT_WIDTH, LIST_HEIGHT)
		area.Show()
		self.listArea = area
		scroll = _ThinScroll(LIST_HEIGHT, ui.__mem_func__(self._OnListScroll))
		scroll.SetParent(area)
		scroll.SetPosition(RIGHT_WIDTH - SCROLL_WIDTH, 0)
		scroll.Hide()
		self.scroll = scroll
		self.rows = []
		for index in range(ROW_POOL):
			row = _FarmRow(index, ROW_WIDTH, ui.__mem_func__(self._OnRowOver), ui.__mem_func__(self._OnRowOut),
				ui.__mem_func__(self._OnRowClick), ui.__mem_func__(self._OnListWheel))
			row.SetParent(area)
			row.Hide()
			self.rows.append(row)
		self.rowLines = [None] * ROW_POOL

	def _ShowView(self, mode):
		"""mode: 'run' (a session), 'none' (no session) or 'load' (no answer yet)."""
		if mode == 'run':
			self.noneView.Hide()
			self.runView.Show()
			return
		self.runView.Hide()
		self._HideTip()
		self.noneText.SetText(TEXT_LOADING if mode == 'load' else TEXT_NONE)
		for button in self.startButtons:
			if mode == 'none':
				button.Show()
			else:
				button.Hide()
		self.noneView.Show()

	def _LoadCharacter(self):
		"""This character's hidden rows and own categories, once for each name."""
		name = _CharacterName()
		if not name or name == self.characterName:
			return
		self.characterName = name
		self.hidden = set(LoadHidden(name))
		self.categories = LoadCategories(name)
		self.selectedCategory = None
		self.listDirty = True

	def _RefreshSessionTab(self):
		if not self.sessionReady or self.tab != TAB_SESSION or not self.IsShow():
			return
		info = self.info
		if info is None:
			self._ShowView('load')
			return
		if info['state'] == STATE_NONE:
			self._ShowView('none')
			return
		self._ShowView('run')
		allCount = max(1, FilterTotals(info, FILTER_ALL)[0])
		for index in range(FILTER_COUNT):
			row = self.sourceRows[index]
			count = FilterTotals(info, index)[0]
			row.SetCount(count, float(count) / allCount)
			row.SetSelected(index == self.filter)
		self.pauseButton.SetText(TEXT_RESUME if info['state'] == STATE_PAUSED else TEXT_PAUSE)
		self.hiddenButton.SetStyle(STYLE_TAB_ON if self.showHidden else STYLE_BUTTON)
		self._UpdateClock()
		self._UpdateSpark(True)
		yang = FilterTotals(info, self.filter)[1]
		if self.itemsDirty or self.listDirty or not self.listData or self.listData[0][1] != yang:
			self._RebuildList(yang)

	def _UpdateClock(self):
		info = self.info
		if not self.sessionReady or info is None or info['state'] == STATE_NONE:
			return
		text = FormatClock(self.GetActiveSeconds())
		if info['limit'] > 0:
			text += ' / ' + FormatClock(info['limit'])
		self.clockText.SetText(text)
		if info['state'] == STATE_RUNNING:
			self.stateText.SetPackedFontColor(COLOR_RUNNING)
			self.stateText.SetText(TEXT_RUNNING)
		else:
			self.stateText.SetPackedFontColor(COLOR_DIM)
			self.stateText.SetText(TEXT_PAUSED)

	def _UpdateSpark(self, force=False):
		"""The chart of the last SPARK_MINUTES active minutes (FarmSpark, moved on by the client's clock)."""
		if not self.sessionReady or self.info is None:
			return
		current = self.GetActiveSeconds() // 60
		key = (current, self.spark)
		if not force and key == self.sparkShown:
			return
		self.sparkShown = key
		values = [0] * SPARK_MINUTES
		if self.spark:
			minute, counts = self.spark
			first = minute - len(counts) + 1
			for number in range(SPARK_MINUTES):
				at = current - SPARK_MINUTES + 1 + number - first
				if 0 <= at < len(counts):
					values[number] = counts[at]
		self.sparkText.SetText(TEXT_SPARK % max(values))
		self.sparkChart.SetValues(values)

	def _RebuildList(self, yang):
		rows, total = BuildList(self.items, self.filter, self.hidden, self.showHidden)
		yangRows = []
		if self.showHidden or YANG_ROW not in self.hidden:
			yangRows = [(YANG_ROW, yang, self.info['ylast'] if self.info else 0)]
		self.listData = yangRows + rows
		self.shareTotal = max(1, max([row[1] for row in rows] + [0]))
		self.itemsDirty = False
		self.listDirty = False
		self._FixOffset()
		self._DrawRows()

	def _RowIcon(self, vnum):
		if vnum == YANG_ROW:
			path = ItemIcon(YANG_VNUM) or MONEY_ICON
		else:
			path = ItemIcon(vnum)
		return path, (_IconSize(path, self.iconSizes) if path else (32, 32))

	def _DrawRows(self):
		y = 0
		slot = 0
		number = self.offset
		while number < len(self.listData) and slot < ROW_POOL:
			vnum, count, last = self.listData[number]
			path, size = self._RowIcon(vnum)
			height = 34 if vnum == YANG_ROW else RowHeight(size[1])
			if y + height > LIST_HEIGHT:
				break
			row = self.rows[slot]
			if vnum == YANG_ROW:
				row.SetYang(count, vnum in self.hidden, path, size)
			else:
				row.SetItem(vnum, count, float(count) / self.shareTotal, vnum in self.hidden, path, size)
			row.SetPosition(0, y)
			row.Show()
			self.rowLines[slot] = number
			y += height + LIST_GAP
			number += 1
			slot += 1
		for index in range(slot, ROW_POOL):
			self.rows[index].Hide()
			self.rowLines[index] = None
		if self.hoverRow is not None:
			self._ShowRowTip(self.hoverRow)

	def _MaxOffset(self):
		"""The first line from which all the rest fits in the list."""
		start = len(self.listData)
		total = 0
		while start > 0:
			vnum = self.listData[start - 1][0]
			height = 34 if vnum == YANG_ROW else RowHeight(self._RowIcon(vnum)[1][1])
			if total + height > LIST_HEIGHT:
				break
			total += height + LIST_GAP
			start -= 1
		return start

	def _FixOffset(self):
		maxOffset = self._MaxOffset()
		self.offset = max(0, min(maxOffset, self.offset))
		if maxOffset <= 0:
			self.scroll.Hide()
			return
		self.scroll.SetPage(float(len(self.listData) - maxOffset) / max(1, len(self.listData)))
		self.scroll.SetPos(float(self.offset) / maxOffset)
		self.scroll.Show()

	def _SetOffset(self, offset):
		maxOffset = self._MaxOffset()
		offset = max(0, min(maxOffset, offset))
		if offset == self.offset:
			return
		self.offset = offset
		if maxOffset > 0:
			self.scroll.SetPos(float(offset) / maxOffset)
		self._DrawRows()

	def _OnListScroll(self, pos):
		maxOffset = self._MaxOffset()
		if not self.sessionReady or maxOffset <= 0:
			return
		offset = max(0, min(maxOffset, int(round(pos * maxOffset))))
		if offset != self.offset:
			self.offset = offset
			self._DrawRows()

	def _OnListWheel(self, direction):
		if self.sessionReady:
			self._SetOffset(self.offset + direction * WHEEL_ROWS)

	# -- the buttons

	def _OnStart(self, seconds):
		SendCommand('start %d' % seconds)

	def _OnPause(self):
		info = self.info
		if info is None:
			return
		if info['state'] == STATE_PAUSED:
			SendCommand('wznow')
		elif info['state'] == STATE_RUNNING:
			SendCommand('pauza')

	def _OnEnd(self):
		import uiCommon
		self._CloseQuestion()
		question = uiCommon.QuestionDialog()
		question.SetText(TEXT_END_ASK)
		question.SetAcceptEvent(ui.__mem_func__(self._OnEndAccept))
		question.SetCancelEvent(ui.__mem_func__(self._CloseQuestion))
		question.Open()
		self.question = question

	def _OnEndAccept(self):
		self._CloseQuestion()
		SendCommand('koniec')

	def _CloseQuestion(self):
		question = self.question
		self.question = None
		if question:
			question.Close()

	def _OnToggleHidden(self):
		self.showHidden = not self.showHidden
		self.listDirty = True
		self._RefreshSessionTab()

	def _OnFilter(self, index):
		if index == self.filter:
			return
		self.filter = index
		self.offset = 0
		self.listDirty = True
		self._RefreshSessionTab()

	# -- the rows

	def _LineOf(self, index):
		if index < 0 or index >= ROW_POOL:
			return None
		number = self.rowLines[index]
		if number is None or number >= len(self.listData):
			return None
		return self.listData[number]

	def _OnRowOver(self, index):
		if not self.sessionReady:
			return
		self.hoverRow = index
		self._ShowRowTip(index)

	def _OnRowOut(self, index):
		if self.hoverRow == index:
			self.hoverRow = None
			self._HideTip()

	def _OnRowClick(self, index):
		"""A click on a row (the Yang one too) hides it, or shows it again."""
		line = self._LineOf(index)
		if not self.sessionReady or line is None:
			return
		vnum = line[0]
		if vnum in self.hidden:
			self.hidden.discard(vnum)
		else:
			self.hidden.add(vnum)
		if self.characterName:
			SaveHidden(self.characterName, self.hidden)
		self.listDirty = True
		self._RefreshSessionTab()

	def _ShowRowTip(self, index):
		line = self._LineOf(index)
		tip = self.tooltip
		if line is None or not tip:
			self._HideTip(False)
			return
		vnum, count, last = line
		tip.ClearToolTip()
		tip.AppendTextLine(TEXT_YANG if vnum == YANG_ROW else ItemName(vnum), tip.TITLE_COLOR)
		if last:
			tip.AppendTextLine(TEXT_LAST_DROP % FormatDate(last), tip.SPECIAL_TITLE_COLOR)
		tip.AppendTextLine(TEXT_CLICK_SHOW if vnum in self.hidden else TEXT_CLICK_HIDE)
		tip.ShowToolTip()

	def _HideTip(self, forget=True):
		if not self.sessionReady:
			return
		if forget:
			self.hoverRow = None
		tip = self.tooltip
		if tip:
			tip.HideToolTip()

	# -- the answer in the chart's place (or under the start buttons)

	def _ShowStatus(self, text):
		self.resultLine.SetText(text)
		self.noneResult.SetText(text)
		self.sparkText.Hide()
		self.sparkChart.Hide()
		self.statusUntil = clientclock.Now() + STATUS_SECONDS

	def _ExpireStatus(self):
		if self.statusUntil and clientclock.Now() >= self.statusUntil:
			self.statusUntil = 0.0
			self.resultLine.SetText('')
			self.noneResult.SetText('')
			self.sparkText.Show()
			self.sparkChart.Show()

	# -------------------------------------------------------------- the categories (Statystyki)

	def _OnStatsAction(self, name, *args):
		if name == 'select':
			key = args[0] if args else None
			if not (isinstance(key, str) and key.startswith('c')):
				key = None
			self.selectedCategory = None if key == self.selectedCategory else key
			self._RefreshStatsTab()
		elif name == 'new':
			self._AskCategoryName()
		elif name == 'delete':
			self._DeleteCategory()

	def _AskInput(self, title, length, accept):
		import uiCommon
		self._CloseInput()
		dialog = uiCommon.InputDialog()
		dialog.SetTitle(title)
		dialog.SetMaxLength(length)
		dialog.SetAcceptEvent(ui.__mem_func__(accept))
		dialog.SetCancelEvent(ui.__mem_func__(self._CloseInput))
		dialog.Open()
		self.inputDialog = dialog

	def _CloseInput(self):
		dialog = self.inputDialog
		self.inputDialog = None
		if dialog:
			dialog.Close()

	def _AskCategoryName(self):
		self._LoadCharacter()
		if len(self.categories) >= CATEGORY_MAX:
			self._StatsMessage(TEXT_CATEGORY_FULL % CATEGORY_MAX)
			return
		self._AskInput(TEXT_CATEGORY_NAME, CATEGORY_NAME_LEN, self._OnCategoryName)

	def _OnCategoryName(self):
		text = self.inputDialog.GetText().strip() if self.inputDialog else ''
		self._CloseInput()
		if not text:
			return
		if LowerPl(text) in [LowerPl(c['name']) for c in self.categories] or LowerPl(text) in [LowerPl(t) for t in TEXT_CATEGORIES]:
			self._StatsMessage(TEXT_CATEGORY_TWICE)
			return
		self.newCategoryName = text
		self._AskInput(TEXT_CATEGORY_WORDS, CATEGORY_WORDS_LEN, self._OnCategoryWords)

	def _OnCategoryWords(self):
		text = self.inputDialog.GetText() if self.inputDialog else ''
		self._CloseInput()
		words = [LowerPl(word.strip()) for word in text.split(',') if word.strip()]
		if not words:
			words = [LowerPl(self.newCategoryName)]
		self.categories.append({'name': self.newCategoryName, 'words': words})
		self.selectedCategory = 'c%d' % (len(self.categories) - 1)
		if self.characterName:
			SaveCategories(self.characterName, self.categories)
		self._RefreshStatsTab()

	def _DeleteCategory(self):
		key = self.selectedCategory
		if not key:
			return
		index = ParseInt(key[1:], -1)
		if 0 <= index < len(self.categories):
			del self.categories[index]
			if self.characterName:
				SaveCategories(self.characterName, self.categories)
		self.selectedCategory = None
		self._RefreshStatsTab()

	def _StatsMessage(self, text):
		import chat
		chat.AppendChat(chat.CHAT_TYPE_INFO, text)

	# -------------------------------------------------------------- the tabs

	def SelectTab(self, index):
		if index < 0 or index >= TAB_COUNT or not self.pages:
			return
		self.tab = index
		for number in range(TAB_COUNT):
			if number == index:
				self.pages[number].Show()
				self.tabButtons[number].SetStyle(STYLE_TAB_ON)
			else:
				self.pages[number].Hide()
				self.tabButtons[number].SetStyle(STYLE_TAB)
		self._OnTabEnter(index)

	def _OnTabEnter(self, index):
		if index != TAB_SESSION:
			self._HideTip()
		if self.IsShow():
			try:
				self._LoadCharacter()
			except Exception:
				pass
		if index == TAB_HISTORY and self.histReady and self.IsShow():
			self.histError = ''
			self.RequestHistory()
		elif index == TAB_STATS and self.statsReady and self.IsShow():
			self.statsError = ''
			self.RequestStats()
		self._RefreshTab(index)

	def _RefreshTab(self, index):
		if index == TAB_SESSION:
			self._RefreshSessionTab()
		elif index == TAB_HISTORY:
			self._RefreshHistoryTab()
		elif index == TAB_STATS:
			self._RefreshStatsTab()

	def _SetNote(self, note, hasLines, done, error, empty):
		if error:
			text = error
		elif not done:
			text = TEXT_LOADING
		elif not hasLines:
			text = empty
		else:
			text = ''
		note.SetText(text)
		note.SetPackedFontColor(COLOR_RESULT if error else COLOR_DIM)
		if text:
			note.Show()
		else:
			note.Hide()

	def _RefreshHistoryTab(self):
		if not self.histReady or self.tab != TAB_HISTORY or not self.IsShow():
			return
		lines = BuildHistoryLines(self.hist)
		self.histView.SetLines(lines)
		self._SetNote(self.histNote, bool(lines), self.histDone, self.histError, TEXT_HISTORY_EMPTY)

	def _RefreshStatsTab(self):
		if not self.statsReady or self.tab != TAB_STATS or not self.IsShow():
			return
		lines = BuildStatsLines(self.stats, self.categories, self.selectedCategory) if self.statsDone else []
		self.statsView.SetLines(lines)
		self._SetNote(self.statsNote, bool(lines), self.statsDone, self.statsError, TEXT_NO_DATA)

	def _OnResult(self, code):
		if code == 0:
			return
		text = RESULT_TEXTS.get(code, TEXT_RESULT_OTHER)
		failed = code == RESULT_DATABASE or code not in RESULT_TEXTS
		if failed and self.histReady and self.tab == TAB_HISTORY and self.histPending and self.IsShow():
			self.histPending = False
			self.histError = text
			self._RefreshHistoryTab()
		elif failed and self.statsReady and self.tab == TAB_STATS and self.statsPending and self.IsShow():
			self.statsPending = False
			self.statsError = text
			self._RefreshStatsTab()
		elif self.sessionReady and self.tab == TAB_SESSION and self.IsShow():
			self._ShowStatus(text)
		else:
			import chat
			chat.AppendChat(chat.CHAT_TYPE_INFO, text)

	def _OnSecond(self):
		if self.sessionReady:
			self._ExpireStatus()
		if self.tab == TAB_SESSION:
			self._UpdateClock()
			self._UpdateSpark()

	# -------------------------------------------------------------- open, close

	def Open(self):
		"""The Y key: shuts the window when shown, else opens it and asks for the whole snapshot."""
		if self.IsShow():
			self.Close()
			return
		self.Show()
		self.SetTop()
		now = clientclock.Now()
		self.nextStan = now + POLL_STAN
		self.nextPelne = now + POLL_PELNE
		self.nextSecond = 0.0
		SendCommand('pelne')
		self._OnTabEnter(self.tab)

	def Close(self):
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def OnUpdate(self):
		if not InGame():
			return
		now = clientclock.Now()
		if now >= self.nextSecond:
			self.nextSecond = now + CLOCK_INTERVAL
			self._OnSecond()
		if now >= self.nextPelne:
			if TryPoll('pelne'):
				self.nextPelne = now + POLL_PELNE
				self.nextStan = now + POLL_STAN
		elif now >= self.nextStan:
			if TryPoll('stan'):
				self.nextStan = now + POLL_STAN

	# -------------------------------------------------------------- orders

	def RequestHistory(self):
		self.histPending = True
		SendCommand('historia')

	def RequestStats(self):
		self.statsPending = True
		SendCommand('stat')

	def GetActiveSeconds(self):
		info = self.info
		if info is None:
			return 0
		active = info['active']
		if info['state'] == STATE_RUNNING:
			active += int(clientclock.Now() - info['received'])
		if info['limit'] > 0 and active > info['limit']:
			active = info['limit']
		return active

	# -------------------------------------------------------------- the server's lines

	def OnFarmInfo(self, *a):
		info = ParseInfo(a)
		if info is None:
			return
		info['received'] = clientclock.Now()
		if self.info is None or self.info['id'] != info['id']:
			self.items = {}
			self.spark = None
			self.itemsDirty = True
		self.info = info
		self.histStaged = []
		self.statsStaged = {}
		self._RefreshSessionTab()

	def OnFarmItems(self, *a):
		parsed = ParseItems(a)
		if parsed is None:
			return
		src, rows = parsed
		for vnum, cnt, last in rows:
			self.items[(vnum, src)] = (cnt, last)
		self.itemsDirty = True

	def OnFarmSpark(self, *a):
		parsed = ParseSpark(a)
		if parsed is not None:
			self.spark = parsed

	def OnFarmDone(self):
		self.itemsDone = True
		self._RefreshSessionTab()

	def OnFarmResult(self, code='-1', *rest):
		self.lastResult = ParseInt(code, -1)
		self._OnResult(self.lastResult)

	def OnFarmHist(self, *a):
		row = ParseHist(a)
		if row is not None:
			self.histStaged.append(row)

	def OnFarmHistEnd(self):
		self.hist = self.histStaged
		self.histStaged = []
		self.histDone = True
		self.histPending = False
		self.histError = ''
		self._RefreshHistoryTab()

	def OnFarmStat(self, kind, *a):
		if kind == 'End':
			self.stats = self.statsStaged
			self.statsStaged = {}
			self.statsDone = True
			self.statsPending = False
			self.statsError = ''
			self._RefreshStatsTab()
		elif kind in STAT_RECORDS:
			key, names = STAT_RECORDS[kind]
			row = _Numbers(a, names)
			if row is not None:
				self.statsStaged[key] = row
		elif kind == 'Cat':
			if len(a) >= STAT_CATEGORIES:
				self.statsStaged['cat'] = [max(0, ParseInt(word)) for word in a[:STAT_CATEGORIES]]
		elif kind in STAT_LISTS:
			key, size = STAT_LISTS[kind]
			self.statsStaged.setdefault(key, []).extend(_Tuples(a[1:], size))
