# Battle Pass - the window and the task bar's button (the operator, 28
# September). The server keeps the season, the missions and every player's
# progress (playerbot_battlepass.h, "/battlepass"):
#   BPBegin <season YYYYMM> <days left> <final vnum> <final count> <final claimed> <missions>
#   BPMission <id> <type> <target> <count> <progress> <claimed> <reward vnum> <reward count> <name hex or ->
#   BPEnd <all done>
#   BPUpdate                       - something changed; the open window asks again
# The window words a mission from its type and target, unless the operator
# gave it a name. "Odbierz" sends "/battlepass odbierz <id>", the final
# reward "/battlepass nagroda".
#
# Python 2.7 as the client has it; the texts are CP1250 escapes.

import item
import net
import nonplayer
import ui

MONTHS = ('Stycze\xf1', 'Luty', 'Marzec', 'Kwiecie\xf1', 'Maj', 'Czerwiec', 'Lipiec',
		'Sierpie\xf1', 'Wrzesie\xf1', 'Pa\x9fdziernik', 'Listopad', 'Grudzie\xf1')

# (any target, one target) - %(n)s the count, %(what)s the target's name.
MISSION_TEXT = {
	1: ('Zabij %(n)s potwor\xf3w', 'Zabij %(n)s x %(what)s'),
	2: ('Zniszcz %(n)s kamieni Metin', 'Zniszcz %(n)s x %(what)s'),
	3: ('Pokonaj %(n)s boss\xf3w', 'Pokonaj %(n)s x %(what)s'),
	4: ('Z\xb3\xf3w %(n)s ryb', 'Z\xb3\xf3w %(n)s ryb'),
	5: ('Ulepsz %(n)s przedmiot\xf3w', 'Ulepsz %(n)s przedmiot\xf3w'),
	6: ('Zbierz %(n)s yang', 'Zbierz %(n)s yang'),
	7: ('Otw\xf3rz %(n)s skrzy\xf1', 'Otw\xf3rz %(n)s skrzy\xf1'),
	8: ('Zbierz %(n)s zi\xf3\xb3', 'Zbierz %(n)s zi\xf3\xb3'),
	9: ('Wydob\xb9d\x9f %(n)s rudy', 'Wydob\xb9d\x9f %(n)s rudy'),
	10: ('Uko\xf1cz %(n)s loch\xf3w', 'Uko\xf1cz %(n)s loch\xf3w'),
	11: ('Wykonaj %(n)s Ksi\xb9g Misji', 'Wykonaj %(n)s Ksi\xb9g Misji'),
	12: ('Graj przez %(n)s min', 'Graj przez %(n)s min'),
	13: ('U\xbfyj %(n)s przedmiot\xf3w', 'U\xbfyj %(n)s x %(what)s'),
}

_data = {'begin': None, 'missions': [], 'pending': [], 'allDone': False, 'window': None}


def Money(n):
	text = str(n)
	parts = []
	while len(text) > 3:
		parts.insert(0, text[-3:])
		text = text[:-3]
	parts.insert(0, text)
	return '.'.join(parts)


def ItemName(vnum):
	try:
		item.SelectItem(vnum)
		return item.GetItemName()
	except Exception:
		return str(vnum)


def MissionText(m):
	if m['name']:
		return m['name']
	anyText, oneText = MISSION_TEXT.get(m['type'], ('Misja %(n)s', 'Misja %(n)s'))
	n = Money(m['count']) if m['type'] == 6 else str(m['count'])
	if not m['target']:
		return anyText % {'n': n}
	if m['type'] in (1, 2, 3):
		try:
			what = nonplayer.GetMonsterName(m['target'])
		except Exception:
			what = str(m['target'])
	else:
		what = ItemName(m['target'])
	return oneText % {'n': n, 'what': what}


def Request():
	net.SendChatPacket('/battlepass')


def OnBegin(season='0', days='0', finalVnum='0', finalCount='0', finalClaimed='0', count='0', *rest):
	try:
		_data['pending_begin'] = (int(season), int(days), int(finalVnum), int(finalCount), int(finalClaimed) != 0)
	except ValueError:
		_data['pending_begin'] = None
	_data['pending'] = []


def OnMission(*args):
	try:
		mid, mtype, target, count, progress, claimed, rewardVnum, rewardCount = [int(a) for a in args[:8]]
	except (ValueError, TypeError):
		return
	name = ''
	if len(args) > 8 and args[8] != '-':
		try:
			name = args[8].decode('hex')
		except Exception:
			name = ''
	_data['pending'].append({'id': mid, 'type': mtype, 'target': target, 'count': count,
			'progress': progress, 'claimed': claimed != 0, 'rewardVnum': rewardVnum,
			'rewardCount': rewardCount, 'name': name})


def OnEnd(allDone='0', *rest):
	if not _data.get('pending_begin'):
		return
	_data['begin'] = _data['pending_begin']
	_data['missions'] = _data['pending']
	_data['pending'] = []
	_data['allDone'] = allDone == '1'
	# The window asks only while it is open; an answer to a closed one is
	# "/battlepass" typed in the chat, which opens it.
	wnd = GetWindow()
	if wnd.IsShow():
		wnd.Refresh()
	else:
		wnd.Refresh()
		wnd.Show()
		wnd.SetTop()


def OnUpdate(*rest):
	wnd = _data['window']
	if wnd and wnd.IsShow():
		Request()


class BattlePassWindow(ui.BoardWithTitleBar):
	WIDTH = 400
	ROWS = 7
	ROW_HEIGHT = 44

	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)
		self.widgets = []
		self.rows = []
		self.page = 0
		self.AddFlag('movable')
		self.AddFlag('float')
		height = 34 + 36 + self.ROWS * self.ROW_HEIGHT + 30 + 58
		self.SetSize(self.WIDTH, height)
		self.SetTitleName('Battle Pass')
		self.SetCloseEvent(ui.__mem_func__(self.Close))
		self.__Build(height)
		self.SetCenterPosition()

	def __Text(self, parent, x, y, text=''):
		line = ui.TextLine()
		line.SetParent(parent)
		line.SetPosition(x, y)
		line.SetText(text)
		line.Show()
		self.widgets.append(line)
		return line

	def __Button(self, parent, size, x, y, text, event, *args):
		button = ui.Button()
		button.SetParent(parent)
		button.SetPosition(x, y)
		button.SetUpVisual('d:/ymir work/ui/public/%s_button_01.sub' % size)
		button.SetOverVisual('d:/ymir work/ui/public/%s_button_02.sub' % size)
		button.SetDownVisual('d:/ymir work/ui/public/%s_button_03.sub' % size)
		button.SetText(text)
		button.SetEvent(event, *args)
		button.Show()
		self.widgets.append(button)
		return button

	def __Build(self, height):
		self.seasonLine = self.__Text(self, 16, 34)
		self.summaryLine = self.__Text(self, 16, 50)
		top = 70
		for i in range(self.ROWS):
			y = top + i * self.ROW_HEIGHT
			name = self.__Text(self, 16, y)
			gauge = ui.Gauge()
			gauge.SetParent(self)
			gauge.SetPosition(16, y + 18)
			gauge.MakeGauge(220, 'blue')
			gauge.Show()
			self.widgets.append(gauge)
			progress = self.__Text(self, 244, y + 15)
			reward = self.__Text(self, 16, y + 28)
			claim = self.__Button(self, 'middle', self.WIDTH - 16 - 61, y + 8, 'Odbierz',
					ui.__mem_func__(self.__Claim), i)
			self.rows.append({'name': name, 'gauge': gauge, 'progress': progress, 'reward': reward,
					'claim': claim, 'mission': None})
		pagerY = top + self.ROWS * self.ROW_HEIGHT + 2
		self.prevButton = self.__Button(self, 'small', 16, pagerY, '<', ui.__mem_func__(self.__Page), -1)
		self.pageLine = self.__Text(self, 66, pagerY + 3)
		self.nextButton = self.__Button(self, 'small', 120, pagerY, '>', ui.__mem_func__(self.__Page), 1)
		self.finalLine = self.__Text(self, 16, height - 50)
		self.finalState = self.__Text(self, 16, height - 34)
		self.finalButton = self.__Button(self, 'large', self.WIDTH - 16 - 88, height - 44, 'Odbierz nagrod\xea',
				ui.__mem_func__(self.__ClaimFinal))

	def Open(self):
		self.Refresh()
		self.Show()
		self.SetTop()
		Request()

	def Close(self):
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def __Page(self, step):
		pages = max(1, (len(_data['missions']) + self.ROWS - 1) // self.ROWS)
		self.page = max(0, min(pages - 1, self.page + step))
		self.Refresh()

	def __Claim(self, index):
		m = self.rows[index]['mission']
		if m:
			net.SendChatPacket('/battlepass odbierz %d' % m['id'])

	def __ClaimFinal(self):
		net.SendChatPacket('/battlepass nagroda')

	def Refresh(self):
		begin = _data['begin']
		missions = _data['missions']
		if not begin:
			self.seasonLine.SetText('Wczytywanie...')
			self.summaryLine.SetText('')
			for row in self.rows:
				for key in ('name', 'gauge', 'progress', 'reward', 'claim'):
					row[key].Hide()
			self.finalButton.Hide()
			return
		season, days, finalVnum, finalCount, finalClaimed = begin
		year, month = season // 100, season % 100
		monthName = MONTHS[month - 1] if 1 <= month <= 12 else str(month)
		self.seasonLine.SetText('Sezon: %s %d   (do ko\xf1ca: %d dni)' % (monthName, year, days))
		done = len([m for m in missions if m['progress'] >= m['count']])
		self.summaryLine.SetText('Uko\xf1czone misje: %d / %d' % (done, len(missions)))
		pages = max(1, (len(missions) + self.ROWS - 1) // self.ROWS)
		self.page = min(self.page, pages - 1)
		self.pageLine.SetText('%d / %d' % (self.page + 1, pages))
		for i, row in enumerate(self.rows):
			index = self.page * self.ROWS + i
			m = missions[index] if index < len(missions) else None
			row['mission'] = m
			if not m:
				for key in ('name', 'gauge', 'progress', 'reward', 'claim'):
					row[key].Hide()
				continue
			complete = m['progress'] >= m['count']
			row['name'].SetText(MissionText(m))
			row['name'].SetPackedFontColor(0xff7cff7c if complete else 0xfff0f0f0)
			row['name'].Show()
			row['gauge'].SetPercentage(m['progress'], m['count'])
			row['gauge'].Show()
			row['progress'].SetText('%s / %s' % (Money(m['progress']), Money(m['count'])))
			row['progress'].Show()
			if m['rewardVnum']:
				row['reward'].SetText('Nagroda: %s x%d' % (ItemName(m['rewardVnum']), max(1, m['rewardCount'])))
				row['reward'].SetPackedFontColor(0xffbeb47d)
			else:
				row['reward'].SetText('')
			row['reward'].Show()
			if complete and m['rewardVnum'] and not m['claimed']:
				row['claim'].Show()
			else:
				row['claim'].Hide()
		self.finalLine.SetText('Nagroda za wszystkie misje: %s x%d' % (ItemName(finalVnum), max(1, finalCount)))
		self.finalLine.SetPackedFontColor(0xffffc800)
		if finalClaimed:
			self.finalState.SetText('Odebrana w tym sezonie.')
			self.finalButton.Hide()
		elif _data['allDone']:
			self.finalState.SetText('Wszystkie misje uko\xf1czone!')
			self.finalButton.Show()
		else:
			self.finalState.SetText('Uko\xf1cz wszystkie misje sezonu, \xbfeby j\xb9 odebra\xe6.')
			self.finalButton.Hide()


def GetWindow():
	if not _data['window']:
		_data['window'] = BattlePassWindow()
	return _data['window']


def ToggleWindow():
	wnd = GetWindow()
	if wnd.IsShow():
		wnd.Close()
	else:
		wnd.Open()


def DestroyWindow():
	wnd = _data['window']
	if wnd:
		wnd.Hide()
	_data['window'] = None
