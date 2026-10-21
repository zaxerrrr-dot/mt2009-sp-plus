# MT2009_PLUS_WORLDBOSS_V1 - Boss Swiata (World Boss): the event's window and its ranking (the pl-wiki's "Boss
# Swiata"; GF 26.1.11's layouts uiscript/worldbosswindow.py and worldbossrankingwindow.py, the root logic ours).
#
# The server (playerbot_worldboss.h, "/worldboss") decides everything; this only shows it.
# Client -> server:  /worldboss info  |  /worldboss ranking  |  /worldboss sezon <kingdom 1-3>  |  /worldboss odbierz
# Server -> client (game.py "WB" -> OnCommand):
#   WB info <state> <boss vnum> <map> <fight left s> <next left s> <my damage> <min damage> <claims> <my tier>
#           <my place> <season points> <enabled> <channel>
#        state 0 waiting, 1 standing, 2 defeated, 3 escaped
#   WB where <map> <area words...>
#   WB rbegin <serial> <boss vnum> <count> / WB r <pos> <tier> <empire> <damage> <name> <guild|-> /
#   WB rme <pos> <tier> <empire> <damage> <name> <guild|-> / WB rend          - the last defeated boss's ranking
#   WB sbegin <season> <seconds left> <empire> / WB s <pos> <points> <name> <guild|-> / WB sg <pos> <points> <guild> /
#   WB sme <pos> <points> / WB send                                            - a kingdom's season ranking
#   WB claimok
#   WB mark <x> <y> <local x> <local y> <boss vnum> / WB unmark   - MT2009_PLUS_WORLDBOSS_ICON_V1: the standing boss's
#        place (every 3 s to the players on his map) - his icon on the atlas (M) and the minimap (uiminimap.py hooks
#        UpdateAtlasIcon / UpdateMiniMapIcon), the boss's name on hover
# Opened from the event hub's "Boss Swiata" button (uiingameevent.RegisterOpener('worldboss')) or the "world_boss"
# key (keybind.py, none by default). Receiving "WB info" never opens it.
#
# Python 2.7 as the client has it; the texts are CP1250 escapes.

import app
import chat
import net
import ui

try:
	import background
except ImportError:
	background = None

try:
	import nonplayer
except ImportError:
	nonplayer = None

EVENT_KEY = 'worldboss'
POLL_SECONDS = 5.0
ROWS_PER_PAGE = 10
ROW_STEP = 24
PAGE_BUTTONS = 5
ROOT_PATH = 'd:/ymir work/ui/minigame/world_boss/'
PUBLIC_PATH = 'd:/ymir work/ui/public/'
INTRO_PATH = 'd:/ymir work/ui/public/public_intro_btn/'

TIER_NAME = {1: 'I', 2: 'II', 3: 'III', 4: 'IV'}
EMPIRE_NAME = {1: 'Shinsoo', 2: 'Chunjo', 3: 'Jinno'}
EMPIRE_COLOR = {1: (1.0, 0.40, 0.40), 2: (1.0, 0.85, 0.30), 3: (0.45, 0.65, 1.0)}
TEXT_COLOR = (0.812, 0.749, 0.651)
ME_COLOR = (1.0, 0.92, 0.55)

STATE_SHORT = {
	0: 'Boss \x8cwiata jeszcze si\xea nie pojawi\xb3',
	1: 'Boss \x8cwiata terroryzuje okolic\xea!',
	2: 'Boss \x8cwiata pokonany',
	3: 'Boss \x8cwiata uciek\xb3',
}
STATE_LONG = {
	0: 'czekamy na kolejnego bossa',
	1: 'stoi - pokonajcie go, zanim ucieknie!',
	2: 'pokonany',
	3: 'uciek\xb3 - nikt nie dosta\xb3 nagrody',
}

# The rules - the wiki's window (Boss \x8cwiata info 1-3), split into pages by the window.
RULES = [
	'Pokonaj Bossa \x8cwiata w neutralnej strefie i zdob\xb9d\x9f nagrody!',
	'',
	'ZASADY',
	'Boss \x8cwiata pojawia si\xea w dowolnym czasie podczas trwania',
	'eventu na jednej z map: Dolina Seungryong, Pustynia Yongbi,',
	'Doyyumhwan albo G\xf3ra Sohan (komunikat powie, gdzie).',
	'Musisz go pokona\xe6, by otrzyma\xe6 nagrod\xea.',
	'Podczas walki liczone s\xb9 zadane przez Ciebie obra\xbfenia.',
	'Je\x9cli jednak Bossowi \x8cwiata uda si\xea uciec, licznik obra\xbfe\xf1',
	'zostanie zresetowany.',
	'',
	'WSKAZ\xd3WKA: otrzymasz tylko wtedy nagrod\xea, je\x9cli znajdujesz',
	'si\xea na tej samej mapie, co Boss \x8cwiata, i zadasz minimaln\xb9',
	'ilo\x9c\xe6 wymaganych obra\xbfe\xf1. Opuszczenie mapy lub wylogowanie',
	'zeruje Twoje obra\xbfenia.',
	'Pami\xeataj jednak, \xbfe Boss \x8cwiata nie mo\xbfe Ci umkn\xb9\xe6.',
	'Odbierz swoj\xb9 nagrod\xea koniecznie przed pojawieniem si\xea',
	'nowego bossa! W przeciwnym razie nagroda przepadnie.',
	'',
	'NAGRODY',
	'Im wi\xeacej obra\xbfe\xf1 zadasz Bossowi \x8cwiata, tym wy\xbfsz\xb9 pozycj\xea',
	'zajmiesz w rankingu.',
	'Osi\xb9gnij wy\xbfsz\xb9 pozycj\xea, by otrzyma\xe6 lepszy \xb3up!',
	'',
	'Miejsce 1-10: poziom \xb3upu I',
	'   100 Kamyk\xf3w, Skrzynka Tajemnic, Zagadkowa Szkatu\xb3ka,',
	'   Kupon SM (50), +100% szansy na drop przez 2 godziny',
	'Miejsce 11-25: poziom \xb3upu II',
	'   50 Kamyk\xf3w, Zagadkowa Szkatu\xb3ka, Kupon SM (20),',
	'   +50% szansy na drop przez 2 godziny',
	'Miejsce 26-100: poziom \xb3upu III',
	'   50 Kamyk\xf3w, Zagadkowa Szkatu\xb3ka, Kupon SM (10),',
	'   +25% szansy na drop przez 2 godziny',
	'Miejsce 100+, ale uda\xb3o Ci si\xea zada\xe6 minimalne obra\xbfenia:',
	'poziom \xb3upu IV - 25 Kamyk\xf3w',
	'',
	'POKONAJ BOSSA \x8cWIATA (raz dziennie)',
	'Zadaj pokonanemu bossowi co najmniej 100 000 obra\xbfe\xf1:',
	'warto\x9c\xe6 ataku +20% przez 3 godziny (do odebrania razem',
	'z nagrod\xb9, przed pojawieniem si\xea kolejnego bossa).',
	'',
	'RANKING SEZONU (8 tygodni)',
	'Punkty rangi: poziom \xb3upu I - 10, II - 5, III - 2, IV - 1.',
	'Tyle samo punkt\xf3w dostaje Twoja gildia. Ka\xbfde kr\xf3lestwo',
	'ma sw\xf3j ranking postaci i gildii. Na koniec sezonu',
	'nagrody dostaje 25 najlepszych postaci i 3 najlepsze',
	'gildie ka\xbfdego kr\xf3lestwa (odbi\xf3r w tym oknie).',
]
LINES_PER_PAGE = 12
LINE_STEP = 15

_data = {
	'window': None,
	'ranking': None,
	# the last "WB info": (state, vnum, map, fightLeft, nextLeft, damage, minDamage, claims, tier, pos, points,
	# enabled, channel) and app.GetTime() when it came
	'info': None,
	'infoAt': 0.0,
	'where': '',
	'rank': [],		# (pos, tier, empire, damage, name, guild)
	'rankIn': [],
	'rankMe': None,
	'rankBoss': 0,
	'season': {},	# empire -> dict(season, left, at, rows, guilds, me)
	'seasonIn': None,
	# MT2009_PLUS_WORLDBOSS_ICON_V1: the last "WB mark": (x, y, local x, local y, vnum, map name, app.GetTime())
	'mark': None,
}

# MT2009_PLUS_WORLDBOSS_ICON_V1: "Dodaj ikonk\xea bossa na mapie" - the event's icon (the pl-wiki's "Boss \x8cwiata
# Ikona", 32x32, already the buffs' icon) where the boss stands: on the atlas and on the minimap (on its rim when he
# is farther away, pointing the way). No line for MARK_TIMEOUT seconds (he is gone, the player left his map) hides it.
MARK_ICON = 'mt2009_ui/affect/worldboss.tga'
MARK_ICON_SIZE = 32
MARK_ATLAS_SIZE = 20
MARK_MINIMAP_SIZE = 16
MARK_TIMEOUT = 10.0
MARK_TOOLTIP_COLOR = 0xFFFF6040 - 0x100000000	# the atlas tooltip's ARGB, signed as GetAtlasInfo gives it
MINIMAP_CENTER = (4 + 64, 5 + 64)	# uiscript/minimap.py "MiniMapWindow" (4, 5, 128 x 128) in "OpenWindow"
MINIMAP_RIM = 56.0


def Send(command):
	net.SendChatPacket('/worldboss ' + command)


def ToInt(value, default=0):
	try:
		return int(value)
	except (TypeError, ValueError):
		return default


def MobName(vnum):
	if vnum and nonplayer:
		try:
			name = nonplayer.GetMonsterName(vnum)
			if name:
				return name
		except Exception:
			pass
	return 'Boss \x8cwiata'


def Number(n):
	s = str(abs(int(n)))
	out = ''
	while len(s) > 3:
		out = '.' + s[-3:] + out
		s = s[:-3]
	return ('-' if n < 0 else '') + s + out


def Clock(seconds):
	seconds = max(0, int(seconds))
	h, rest = divmod(seconds, 3600)
	m, s = divmod(rest, 60)
	if h:
		return '%d:%02d:%02d' % (h, m, s)
	return '%02d:%02d' % (m, s)


def GuildText(guild):
	if not guild or guild == '-':
		return ''
	return guild


def InfoNow():
	"""The last info with the two counters run down to now."""
	info = _data['info']
	if not info:
		return None
	passed = int(app.GetTime() - _data['infoAt'])
	values = list(info)
	if values[3] > 0:
		values[3] = max(0, values[3] - passed)
	if values[4] > 0:
		values[4] = max(0, values[4] - passed)
	return values


class WorldBossWindow(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.page = 0
		self.lines = []
		self.nextPoll = 0.0
		self.rewardEnabled = None	# MT2009_PLUS_WORLDBOSS_CLAIM_V1
		self.__LoadWindow()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __LoadWindow(self):
		ui.PythonScriptLoader().LoadScriptFile(self, 'UIScript/worldbosswindow.py')
		self.board = self.GetChild('board')
		self.descBoard = self.GetChild('desc_board')
		self.stateText = self.GetChild('current_state_text')
		self.prevButton = self.GetChild('prev_button')
		self.nextButton = self.GetChild('next_button')
		self.runTimeText = self.GetChild('run_time_text')
		self.breakTimeText = self.GetChild('break_time_text')
		self.totalDamageText = self.GetChild('total_damage_text')
		self.minDamageText = self.GetChild('min_damage_text')
		self.rankingButton = self.GetChild('ranking_button')
		self.rewardButton = self.GetChild('reward_button')

		self.board.SetCloseEvent(ui.__mem_func__(self.Close))
		self.prevButton.SetEvent(ui.__mem_func__(self.__Page), -1)
		self.nextButton.SetEvent(ui.__mem_func__(self.__Page), 1)
		self.rankingButton.SetEvent(ui.__mem_func__(self.__ClickRanking))
		self.rewardButton.SetEvent(ui.__mem_func__(self.__ClickReward))

		for i in xrange(LINES_PER_PAGE):
			line = ui.TextLine()
			line.SetParent(self.descBoard)
			line.SetPosition(8, 6 + i * LINE_STEP)
			line.SetFontColor(*TEXT_COLOR)
			line.Show()
			self.lines.append(line)
		self.__ShowPage()
		self.Refresh()

	def Destroy(self):
		self.ClearDictionary()
		self.lines = []

	def Open(self):
		self.Show()
		self.SetTop()
		self.nextPoll = app.GetTime() + POLL_SECONDS
		Send('info')
		self.Refresh()

	def Close(self):
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def __PageCount(self):
		return 1 + (len(RULES) + LINES_PER_PAGE - 1) / LINES_PER_PAGE

	def __Page(self, step):
		self.page = (self.page + step) % self.__PageCount()
		self.__ShowPage()

	def __StateLines(self):
		info = InfoNow()
		if not info:
			return ['Wczytywanie...']
		state, vnum, mapIndex, fightLeft, nextLeft, damage, minDamage, claims, tier, pos, points, enabled, channel = info
		out = []
		if not enabled:
			out.append('Event Boss \x8cwiata jest teraz wy\xb3\xb9czony.')
			if state != 1:
				out.append('')
		if vnum and state in (1, 2, 3):
			out.append('Boss: %s' % MobName(vnum))
			if _data['where']:
				out.append('Gdzie: %s, kana\xb3 %d' % (_data['where'], channel))
			out.append('Stan: %s' % STATE_LONG.get(state, ''))
		else:
			out.append('Stan: %s' % STATE_LONG.get(0))
		if enabled and nextLeft > 0 and state != 1:
			out.append('Kolejny boss za: %s' % Clock(nextLeft))
		out.append('')
		if state == 1:
			out.append('Twoje obra\xbfenia: %s' % Number(damage))
		if pos > 0:
			out.append('Twoje miejsce na ostatnim bossie: %d (poziom \xb3upu %s)' % (pos, TIER_NAME.get(tier, '-')))
		elif state in (2, 3):
			out.append('Na ostatnim bossie nie zdoby\xb3e\x9c miejsca w rankingu.')
		out.append('Nagrody do odebrania: %d' % claims)
		out.append('Twoje punkty rangi w tym sezonie: %d' % points)
		return out

	def __ShowPage(self):
		if self.page == 0:
			rows = self.__StateLines()
		else:
			start = (self.page - 1) * LINES_PER_PAGE
			rows = RULES[start:start + LINES_PER_PAGE]
		for i, line in enumerate(self.lines):
			line.SetText(rows[i] if i < len(rows) else '')

	def Refresh(self):
		info = InfoNow()
		if not info:
			self.stateText.SetText('')
			self.runTimeText.SetText('--:--')
			self.breakTimeText.SetText('--:--')
			self.totalDamageText.SetText('0')
			self.minDamageText.SetText('-')
			self.__SetRewardEnabled(False)
			return
		state, vnum, mapIndex, fightLeft, nextLeft, damage, minDamage, claims = info[:8]
		enabled = info[11]
		self.stateText.SetText(STATE_SHORT.get(state, '') if enabled or state == 1 else 'Event wy\xb3\xb9czony')
		self.runTimeText.SetText(Clock(fightLeft) if state == 1 else '--:--')
		self.breakTimeText.SetText(Clock(nextLeft) if (nextLeft > 0 and state != 1) else '--:--')
		self.totalDamageText.SetText(Number(damage))
		self.minDamageText.SetText(Number(minDamage))
		self.__SetRewardEnabled(claims > 0)
		if self.page == 0:
			self.__ShowPage()

	# MT2009_PLUS_WORLDBOSS_CLAIM_V1: "Odbierz nagrod\xea" did nothing - Refresh runs every frame (OnUpdate) and
	# Button.Enable() is CButton::Enable -> SetUp(), which drops the pressed state, so a press never became a
	# click. The button is switched only when its state changes.
	def __SetRewardEnabled(self, enabled):
		if self.rewardEnabled == enabled:
			return
		self.rewardEnabled = enabled
		if enabled:
			self.rewardButton.Enable()
		else:
			self.rewardButton.Disable()

	def __ClickRanking(self):
		OpenRanking()

	def __ClickReward(self):
		info = _data['info']
		if not info or info[7] <= 0:
			chat.AppendChat(chat.CHAT_TYPE_INFO, 'Boss \x8cwiata: nie masz nagr\xf3d do odebrania.')
			return
		Send('odbierz')
		self.nextPoll = app.GetTime() + POLL_SECONDS	# MT2009_PLUS_WORLDBOSS_CLAIM_V1: the answer brings the info

	def OnUpdate(self):
		now = app.GetTime()
		if now >= self.nextPoll:
			self.nextPoll = now + POLL_SECONDS
			Send('info')
		self.Refresh()


class RankRow(ui.ExpandedImageBox):
	COLUMNS = ((6, 42, 'right'), (55, 113, 'right'), (175, 88, 'right'), (266, 50, 'center'), (318, 39, 'center'))

	def __init__(self, parent, y):
		ui.ExpandedImageBox.__init__(self)
		self.SetParent(parent)
		self.LoadImage(ROOT_PATH + 'ranking_rank_list_item.sub')
		self.SetPosition(0, y)
		self.texts = []
		for x, width, align in self.COLUMNS:
			box = ui.Window()
			box.SetParent(self)
			box.SetPosition(x, 4)
			box.SetSize(width, 11)
			box.Show()
			text = ui.TextLine()
			text.SetParent(box)
			if align == 'right':
				text.SetPosition(2, 0)
				text.SetWindowHorizontalAlignRight()
				text.SetHorizontalAlignRight()
			else:
				text.SetPosition(0, 0)
				text.SetWindowHorizontalAlignCenter()
				text.SetHorizontalAlignCenter()
			text.Show()
			self.texts.append((box, text))
		self.Hide()

	def Set(self, values, empire=0, color=TEXT_COLOR):
		for i, (box, text) in enumerate(self.texts):
			text.SetText(values[i] if i < len(values) else '')
			if i == 3 and empire in EMPIRE_COLOR:
				text.SetFontColor(*EMPIRE_COLOR[empire])
			else:
				text.SetFontColor(*color)
		self.Show()


class WorldBossRankingWindow(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.mode = 0		# 0 the last boss, 1-3 the season of that kingdom
		self.page = 0
		self.rows = []
		self.pageButtons = []
		self.__LoadWindow()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __LoadWindow(self):
		ui.PythonScriptLoader().LoadScriptFile(self, 'UIScript/worldbossrankingwindow.py')
		self.board = self.GetChild('board')
		self.board.SetCloseEvent(ui.__mem_func__(self.Close))
		self.itemWindow = self.GetChild('rank_item_window')
		self.pageWindow = self.GetChild('page_window')
		self.tierColumn = self.GetChild('rank_column_tier')
		self.myTexts = [self.GetChild('my_rank_rank_text'), self.GetChild('my_rank_name_text'),
						self.GetChild('my_rank_guild_name_text'), self.GetChild('my_rank_empire_text'),
						self.GetChild('my_rank_tier_text')]
		self.GetChild('mode_boss_button').SetEvent(ui.__mem_func__(self.SetMode), 0)
		for empire in (1, 2, 3):
			self.GetChild('mode_season%d_button' % empire).SetEvent(ui.__mem_func__(self.SetMode), empire)
		for i in xrange(ROWS_PER_PAGE):
			self.rows.append(RankRow(self.itemWindow, i * ROW_STEP))

		self.prevButton = self.__MakeButton(INTRO_PATH + 'prev_btn_01.sub', INTRO_PATH + 'prev_btn_02.sub',
											INTRO_PATH + 'prev_btn_01.sub', 70, 2)
		self.prevButton.SetEvent(ui.__mem_func__(self.__Step), -1)
		for i in xrange(PAGE_BUTTONS):
			button = self.__MakeButton(PUBLIC_PATH + 'xsmall_button_01.sub', PUBLIC_PATH + 'xsmall_button_02.sub',
									   PUBLIC_PATH + 'xsmall_button_03.sub', 100 + i * 35, 0)
			button.SetEvent(ui.__mem_func__(self.__ClickPage), i)
			self.pageButtons.append(button)
		self.nextButton = self.__MakeButton(INTRO_PATH + 'next_btn_01.sub', INTRO_PATH + 'next_btn_02.sub',
											INTRO_PATH + 'next_btn_01.sub', 100 + PAGE_BUTTONS * 35 + 5, 2)
		self.nextButton.SetEvent(ui.__mem_func__(self.__Step), 1)

	def __MakeButton(self, up, over, down, x, y):
		button = ui.Button()
		button.SetParent(self.pageWindow)
		button.SetUpVisual(up)
		button.SetOverVisual(over)
		button.SetDownVisual(down)
		button.SetPosition(x, y)
		button.Show()
		return button

	def Destroy(self):
		self.ClearDictionary()
		self.rows = []
		self.pageButtons = []
		self.prevButton = None
		self.nextButton = None

	def Open(self):
		self.Show()
		self.SetTop()
		self.SetMode(self.mode)

	def Close(self):
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def SetMode(self, mode):
		self.mode = mode
		self.page = 0
		if mode == 0:
			Send('ranking')
		else:
			Send('sezon %d' % mode)
		self.Refresh()

	def __Entries(self):
		"""(values, empire, color) of every row of the mode."""
		out = []
		if self.mode == 0:
			for pos, tier, empire, damage, name, guild in _data['rank']:
				out.append(((str(pos), name, GuildText(guild), EMPIRE_NAME.get(empire, ''), TIER_NAME.get(tier, '-')),
							 empire, TEXT_COLOR))
			return out
		season = _data['season'].get(self.mode)
		if not season:
			return out
		for pos, points, name, guild in season['rows']:
			out.append(((str(pos), name, GuildText(guild), EMPIRE_NAME.get(self.mode, ''), str(points)),
						self.mode, TEXT_COLOR))
		if season['guilds']:
			out.append((('', 'Gildie:', '', '', ''), 0, ME_COLOR))
			for pos, points, guild in season['guilds']:
				out.append(((str(pos), '', GuildText(guild), EMPIRE_NAME.get(self.mode, ''), str(points)),
							self.mode, TEXT_COLOR))
		return out

	def __PageCount(self, entries):
		return max(1, (len(entries) + ROWS_PER_PAGE - 1) / ROWS_PER_PAGE)

	def __Step(self, step):
		count = self.__PageCount(self.__Entries())
		self.page = max(0, min(count - 1, self.page + step))
		self.Refresh()

	def __ClickPage(self, index):
		first = self.__FirstPageButton(self.__PageCount(self.__Entries()))
		self.page = first + index
		self.Refresh()

	def __FirstPageButton(self, count):
		return max(0, min(self.page - PAGE_BUTTONS / 2, count - PAGE_BUTTONS))

	def Refresh(self):
		entries = self.__Entries()
		count = self.__PageCount(entries)
		self.page = max(0, min(count - 1, self.page))
		start = self.page * ROWS_PER_PAGE
		for i, row in enumerate(self.rows):
			if start + i < len(entries):
				values, empire, color = entries[start + i]
				row.Set(values, empire, color)
			else:
				row.Hide()
		first = self.__FirstPageButton(count)
		for i, button in enumerate(self.pageButtons):
			number = first + i
			if number < count:
				button.SetText(str(number + 1))
				button.Show()
				if number == self.page:
					button.Down()
				else:
					button.SetUp()
			else:
				button.Hide()

		if self.mode == 0:
			self.tierColumn.SetText('Poziom \xb3upu')
			vnum = _data['rankBoss']
			self.board.SetTitleName('Ranking Bossa \x8cwiata' + (' - %s' % MobName(vnum) if vnum else ''))
			me = _data['rankMe']
			if me:
				pos, tier, empire, damage, name, guild = me
				self.__SetMe((str(pos) if pos else '-', name, GuildText(guild), EMPIRE_NAME.get(empire, ''),
							  TIER_NAME.get(tier, '-') if pos else '-'), empire)
			else:
				self.__SetMe(('', '', '', '', ''), 0)
		else:
			self.tierColumn.SetText('Punkty')
			season = _data['season'].get(self.mode)
			if season:
				left = max(0, season['left'] - int(app.GetTime() - season['at']))
				days = left / 86400
				self.board.SetTitleName('Sezon %d - %s (do ko\xf1ca: %d dni %s)' % (
					season['season'], EMPIRE_NAME.get(self.mode, ''), days, Clock(left % 86400)))
				pos, points = season['me'] or (0, 0)
				self.__SetMe((str(pos) if pos else '-', 'Ty', '', '', str(points)), 0)
			else:
				self.board.SetTitleName('Ranking Bossa \x8cwiata')
				self.__SetMe(('', '', '', '', ''), 0)

	def __SetMe(self, values, empire):
		for i, text in enumerate(self.myTexts):
			text.SetText(values[i])
			if i == 3 and empire in EMPIRE_COLOR:
				text.SetFontColor(*EMPIRE_COLOR[empire])


def GetWindow():
	if not _data['window']:
		_data['window'] = WorldBossWindow()
	return _data['window']


def ToggleWindow():
	window = GetWindow()
	if window.IsShow():
		window.Close()
	else:
		window.Open()


def OpenWindow():
	window = GetWindow()
	if not window.IsShow():
		window.Open()


def OpenRanking():
	if not _data['ranking']:
		_data['ranking'] = WorldBossRankingWindow()
	_data['ranking'].Open()


def Register():
	"""game.py, with the event hub: the hub's "Boss Swiata" button opens the window."""
	try:
		import uiingameevent
		uiingameevent.RegisterOpener(EVENT_KEY, OpenWindow)
	except ImportError:
		pass


def DestroyWindow():
	_data['mark'] = None	# MT2009_PLUS_WORLDBOSS_ICON_V1: a new map, a new icon (or none)
	for key in ('window', 'ranking'):
		window = _data[key]
		if window:
			window.Hide()
			window.Destroy()
		_data[key] = None


def _RefreshRanking():
	if _data['ranking'] and _data['ranking'].IsShow():
		_data['ranking'].Refresh()


def _Name(args, i):
	return args[i] if len(args) > i else ''


# game.py "WB": the server's lines.
def OnCommand(sub='', *args):
	if sub == 'info':
		values = [ToInt(a) for a in args[:13]]
		while len(values) < 13:
			values.append(0)
		_data['info'] = tuple(values)
		_data['infoAt'] = app.GetTime()
		if values[0] != 1:
			_data['mark'] = None	# MT2009_PLUS_WORLDBOSS_ICON_V1: no boss standing
		if _data['window']:
			_data['window'].Refresh()
	elif sub == 'where':
		_data['where'] = ' '.join(args[1:])
	elif sub == 'rbegin':
		_data['rankIn'] = []
		_data['rankMe'] = None
		_data['rankBoss'] = ToInt(_Name(args, 1))
	elif sub in ('r', 'rme'):
		row = (ToInt(_Name(args, 0)), ToInt(_Name(args, 1)), ToInt(_Name(args, 2)), ToInt(_Name(args, 3)),
			   _Name(args, 4), _Name(args, 5))
		if sub == 'r':
			_data['rankIn'].append(row)
		else:
			_data['rankMe'] = row
	elif sub == 'rend':
		_data['rank'] = _data['rankIn']
		_data['rankIn'] = []
		_RefreshRanking()
	elif sub == 'sbegin':
		_data['seasonIn'] = dict(season=ToInt(_Name(args, 0)), left=ToInt(_Name(args, 1)), at=app.GetTime(),
								 empire=ToInt(_Name(args, 2)), rows=[], guilds=[], me=None)
	elif sub in ('s', 'sg', 'sme'):
		season = _data['seasonIn']
		if season is None:
			return
		if sub == 's':
			season['rows'].append((ToInt(_Name(args, 0)), ToInt(_Name(args, 1)), _Name(args, 2), _Name(args, 3)))
		elif sub == 'sg':
			season['guilds'].append((ToInt(_Name(args, 0)), ToInt(_Name(args, 1)), ' '.join(args[2:])))
		else:
			season['me'] = (ToInt(_Name(args, 0)), ToInt(_Name(args, 1)))
	elif sub == 'send':
		season = _data['seasonIn']
		if season is not None:
			_data['season'][season['empire']] = season
		_data['seasonIn'] = None
		_RefreshRanking()
	elif sub == 'claimok':
		Send('info')
	elif sub == 'mark':	# MT2009_PLUS_WORLDBOSS_ICON_V1
		values = [ToInt(_Name(args, i)) for i in range(5)]
		_data['mark'] = (values[0], values[1], values[2], values[3], values[4], _MapName(), app.GetTime())
	elif sub == 'unmark':
		_data['mark'] = None


# ---------------------------------------------------------------- MT2009_PLUS_WORLDBOSS_ICON_V1: the map icon

def _MapName():
	if background:
		try:
			return background.GetCurrentMapName()
		except Exception:
			pass
	return ''


def MarkNow():
	"""The standing boss's last place on this map, or None."""
	mark = _data['mark']
	if not mark:
		return None
	if app.GetTime() - mark[6] > MARK_TIMEOUT:
		_data['mark'] = None
		return None
	if mark[5] and mark[5] != _MapName():
		return None
	return mark


def _Icon(owner, attr, parent, size):
	icon = getattr(owner, attr, None)
	if icon is None:
		icon = ui.ExpandedImageBox()
		icon.SetParent(parent)
		icon.AddFlag('not_pick')
		icon.LoadImage(MARK_ICON)
		scale = float(size) / MARK_ICON_SIZE
		icon.SetScale(scale, scale)
		icon.SetSize(size, size)
		icon.Hide()
		setattr(owner, attr, icon)
	return icon


def _MouseOver(icon, size):
	import wndMgr
	(mx, my) = wndMgr.GetMousePosition()
	(ix, iy) = icon.GetGlobalPosition()
	return ix <= mx < ix + size and iy <= my < iy + size


def _Tooltip(mark):
	return 'Boss \x8cwiata: %s' % MobName(mark[4])


def UpdateAtlasIcon(atlas):
	"""uiminimap.AtlasWindow.OnUpdate: places the icon on the atlas; (text, x, y, color) when the mouse is on it."""
	board = getattr(atlas, 'board', None)
	if not board:
		return None
	icon = _Icon(atlas, 'mt2009WorldBossIcon', board, MARK_ATLAS_SIZE)
	mark = MarkNow()
	if not mark or not atlas.IsShow():
		icon.Hide()
		return None
	import miniMap
	(ok, sizeX, sizeY) = miniMap.GetAtlasSize()
	(ok2, maxX, maxY) = miniMap.GetAtlasMaxSize()
	if not ok or not ok2 or maxX <= 0 or maxY <= 0:
		icon.Hide()
		return None
	# the atlas is drawn at (7, 30) of the board (AtlasWindow.LoadWindow), the map-local units scaled to its size
	x = 7 + int(float(mark[2]) / maxX * sizeX) - MARK_ATLAS_SIZE / 2
	y = 30 + int(float(mark[3]) / maxY * sizeY) - MARK_ATLAS_SIZE / 2
	icon.SetPosition(x, y)
	icon.Show()
	icon.SetTop()
	if _MouseOver(icon, MARK_ATLAS_SIZE):
		return (_Tooltip(mark), mark[2] / 100, mark[3] / 100, MARK_TOOLTIP_COLOR)
	return None


def UpdateMiniMapIcon(minimap, playerX, playerY, scale):
	"""uiminimap.MiniMap.OnUpdate: places the icon on the minimap; the tooltip's text when the mouse is on it."""
	parent = getattr(minimap, 'OpenWindow', None)
	if not parent:
		return None
	icon = _Icon(minimap, 'mt2009WorldBossIcon', parent, MARK_MINIMAP_SIZE)
	mark = MarkNow()
	if not mark:
		icon.Hide()
		return None
	# PythonMiniMap.cpp: a mark is (its pixel position - the player's) / CELLSCALE (200) * the minimap's scale
	dx = (float(mark[0]) - playerX) / 200.0 * scale
	dy = (float(mark[1]) - playerY) / 200.0 * scale
	dist = (dx * dx + dy * dy) ** 0.5
	if dist > MINIMAP_RIM:
		dx = dx * MINIMAP_RIM / dist
		dy = dy * MINIMAP_RIM / dist
	icon.SetPosition(MINIMAP_CENTER[0] + int(dx) - MARK_MINIMAP_SIZE / 2, MINIMAP_CENTER[1] + int(dy) - MARK_MINIMAP_SIZE / 2)
	icon.Show()
	icon.SetTop()
	if _MouseOver(icon, MARK_MINIMAP_SIZE):
		return _Tooltip(mark)
	return None
