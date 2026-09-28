# Kalendarz eventow - F11 or the button on the task bar (the operator, 28
# September: "kalendarz eventow ... tylko okno kalendarza pod F11 i przycisk
# gdzies w gui, z eventami ustawionymi w panelu").
#
# The events are the ones the web panels schedule (the weekly windows and
# "activate now"): the server keeps them in /opt/m2spool/playerbot_events.tsv
# and "/kalendarz" asks the player's core for them (playerbot_manager.cpp,
# SendEventCalendar):
#   EventCalBegin <epoch> <year> <month> <mday> <weekday 0=Mon> <minute> <utc offset min>
#   EventCal <kind> <days, bit 0 = Mon> <start min> <end min> <value> <now> <since> <until> <map>
#   EventCalEnd <lines>
# The dates are the server's. A weekly window shows on every day of the month
# its days mask names; an "activate now" one on the days it spans.
#
# Python 2.7 as the client has it; the texts are CP1250 escapes.

import app
import net
import ui

IMG = 'mt2009_ui/calendar/'

KIND_CHEST, KIND_EXP, KIND_DROP, KIND_YANG, KIND_TANAKA, KIND_ZUO = range(6)
KIND_ICON = {
	KIND_CHEST: 'moonlight_event.tga',
	KIND_EXP: 'exp_event.tga',
	KIND_DROP: 'item_drop_event.tga',
	KIND_YANG: 'money_drop_event.tga',
	KIND_TANAKA: 'double_boss_loot_event.tga',
	KIND_ZUO: 'double_metin_loot_event.tga',
}
KIND_COLOR = {
	KIND_CHEST: (0.75, 0.65, 1.0),
	KIND_EXP: (0.55, 0.85, 1.0),
	KIND_DROP: (0.6, 1.0, 0.6),
	KIND_YANG: (1.0, 0.85, 0.35),
	KIND_TANAKA: (1.0, 0.55, 0.45),
	KIND_ZUO: (1.0, 0.7, 0.35),
}

MONTHS = ('Stycze\xf1', 'Luty', 'Marzec', 'Kwiecie\xf1', 'Maj', 'Czerwiec', 'Lipiec',
		'Sierpie\xf1', 'Wrzesie\xf1', 'Pa\x9fdziernik', 'Listopad', 'Grudzie\xf1')
WEEKDAYS = ('Pn', 'Wt', '\x8cr', 'Cz', 'Pt', 'So', 'Nd')


def KindName(kind, value):
	if kind == KIND_CHEST:
		return 'Szkatu\xb3ka Blasku Ksi\xea\xbfyca'
	if kind == KIND_EXP:
		return 'Do\x9cwiadczenie +%d%%' % value
	if kind == KIND_DROP:
		return 'Drop +%d%%' % value
	if kind == KIND_YANG:
		return 'Yang +%d%%' % value
	if kind == KIND_TANAKA:
		return 'Pirat Tanaka'
	if kind == KIND_ZUO:
		return 'Deszcz metin\xf3w Zuo'
	return 'Event %d' % kind


def HHMM(minutes):
	minutes = minutes % (24 * 60)
	return '%02d:%02d' % (minutes // 60, minutes % 60)


# Calendar arithmetic without the datetime module: days since 1970-01-01.
def DaysFromCivil(y, m, d):
	y -= m <= 2
	era = (y if y >= 0 else y - 399) // 400
	yoe = y - era * 400
	doy = (153 * (m + (-3 if m > 2 else 9)) + 2) // 5 + d - 1
	doe = yoe * 365 + yoe // 4 - yoe // 100 + doy
	return era * 146097 + doe - 719468


def CivilFromDays(z):
	z += 719468
	era = (z if z >= 0 else z - 146096) // 146097
	doe = z - era * 146097
	yoe = (doe - doe // 1460 + doe // 36524 - doe // 146096) // 365
	y = yoe + era * 400
	doy = doe - (365 * yoe + yoe // 4 - yoe // 100)
	mp = (5 * doy + 2) // 153
	d = doy - (153 * mp + 2) // 5 + 1
	m = mp + (3 if mp < 10 else -9)
	return (y + (m <= 2), m, d)


def DaysInMonth(y, m):
	if m == 12:
		return DaysFromCivil(y + 1, 1, 1) - DaysFromCivil(y, 12, 1)
	return DaysFromCivil(y, m + 1, 1) - DaysFromCivil(y, m, 1)


def Weekday(days):
	# 1970-01-01 was a Thursday; 0 = Monday.
	return (days + 3) % 7


_data = {'now': None, 'lines': [], 'pending': [], 'window': None}


def OnBegin(epoch='0', year='1970', month='1', mday='1', weekday='0', minute='0', offset='0', *rest):
	try:
		_data['pending'] = []
		_data['begin'] = (int(epoch), int(year), int(month), int(mday), int(weekday), int(minute), int(offset))
		_data['receivedAt'] = app.GetTime()
	except ValueError:
		_data['begin'] = None


def OnLine(*args):
	try:
		kind, days, start, end, value, now, since, until, mapIndex = [int(a) for a in args[:9]]
	except (ValueError, TypeError):
		return
	_data['pending'].append({'kind': kind, 'days': days, 'start': start, 'end': end, 'value': value,
			'now': now, 'since': since, 'until': until, 'map': mapIndex})


def OnEnd(*rest):
	if not _data.get('begin'):
		return
	_data['now'] = _data['begin']
	_data['lines'] = _data['pending']
	_data['pending'] = []
	wnd = _data['window']
	if wnd and wnd.IsShow():
		wnd.Refresh()


def Request():
	net.SendChatPacket('/kalendarz')


def EventsOnDay(y, m, d):
	"""(start minute, end minute, kind, value) of the events that begin on
	the server's day y-m-d."""
	result = []
	if not _data['now']:
		return result
	offset = _data['now'][6] * 60
	day = DaysFromCivil(y, m, d)
	wd = Weekday(day)
	for line in _data['lines']:
		if line['now']:
			since = line['since'] or _data['now'][0]
			first = (since + offset) // 86400
			last = (max(line['until'], since) + offset - 1) // 86400
			if first <= day <= last:
				start = (since + offset) % 86400 // 60 if day == first else 0
				end = (line['until'] + offset) % 86400 // 60 if day == last else 24 * 60
				result.append((start, end, line['kind'], line['value']))
		elif line['days'] & (1 << wd):
			result.append((line['start'], line['end'], line['kind'], line['value']))
	result.sort()
	return result


def ActiveNow():
	"""The kinds and values running at the server's minute of the snapshot,
	moved on by the time since it came."""
	result = []
	if not _data['now']:
		return result
	epoch, y, m, d, wd, minute, offsetMin = _data['now']
	passed = int(app.GetTime() - _data.get('receivedAt', app.GetTime()))
	now = epoch + passed
	local = now + offsetMin * 60
	day = local // 86400
	minute = local % 86400 // 60
	wd = Weekday(day)
	for line in _data['lines']:
		if line['now']:
			since = line['since'] or epoch
			if since <= now < line['until']:
				result.append((line['kind'], line['value'], line['until']))
			continue
		start, end = line['start'], line['end']
		if end > start:
			if line['days'] & (1 << wd) and start <= minute < end:
				result.append((line['kind'], line['value'], None))
		else:
			yesterday = (wd + 6) % 7
			if (line['days'] & (1 << wd) and minute >= start) or (line['days'] & (1 << yesterday) and minute < end):
				result.append((line['kind'], line['value'], None))
	return result


class EventCalendarWindow(ui.BoardWithTitleBar):
	CELL = 57
	LEFT = 14
	TOP = 58
	ROWS = 6
	LIST_ROWS = 8

	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)
		self.widgets = []
		self.cells = []
		self.listLines = []
		self.year = self.month = 0
		self.selected = None
		self.nextRequest = 0.0
		self.AddFlag('movable')
		self.AddFlag('float')
		width = self.LEFT * 2 + self.CELL * 7
		height = self.TOP + 18 + self.CELL * self.ROWS + 32 + self.LIST_ROWS * 16 + 14
		self.SetSize(width, height)
		self.SetTitleName('Kalendarz event\xf3w')
		self.SetCloseEvent(ui.__mem_func__(self.Close))
		self.__Build(width)
		self.SetCenterPosition()

	def __Text(self, parent, x, y, text='', center=False):
		line = ui.TextLine()
		line.SetParent(parent)
		line.SetPosition(x, y)
		if center:
			line.SetHorizontalAlignCenter()
		line.SetText(text)
		line.Show()
		self.widgets.append(line)
		return line

	def __Build(self, width):
		prev = ui.Button()
		prev.SetParent(self)
		prev.SetPosition(self.LEFT, 34)
		prev.SetUpVisual('d:/ymir work/ui/public/small_button_01.sub')
		prev.SetOverVisual('d:/ymir work/ui/public/small_button_02.sub')
		prev.SetDownVisual('d:/ymir work/ui/public/small_button_03.sub')
		prev.SetText('<')
		prev.SetEvent(ui.__mem_func__(self.__Month), -1)
		prev.Show()
		nxt = ui.Button()
		nxt.SetParent(self)
		nxt.SetPosition(width - self.LEFT - 43, 34)
		nxt.SetUpVisual('d:/ymir work/ui/public/small_button_01.sub')
		nxt.SetOverVisual('d:/ymir work/ui/public/small_button_02.sub')
		nxt.SetDownVisual('d:/ymir work/ui/public/small_button_03.sub')
		nxt.SetText('>')
		nxt.SetEvent(ui.__mem_func__(self.__Month), 1)
		nxt.Show()
		self.widgets.extend([prev, nxt])
		self.monthLine = self.__Text(self, width // 2, 37, '', True)
		for i, name in enumerate(WEEKDAYS):
			self.__Text(self, self.LEFT + i * self.CELL + self.CELL // 2, self.TOP, name, True)
		for row in range(self.ROWS):
			for col in range(7):
				cell = ui.Button()
				cell.SetParent(self)
				cell.SetPosition(self.LEFT + col * self.CELL, self.TOP + 18 + row * self.CELL)
				cell.SetUpVisual(IMG + 'black_bg.tga')
				cell.SetOverVisual(IMG + 'blue_bg.tga')
				cell.SetDownVisual(IMG + 'blue_bg.tga')
				cell.SetEvent(ui.__mem_func__(self.__SelectCell), len(self.cells))
				cell.Show()
				number = ui.TextLine()
				number.SetParent(cell)
				number.SetPosition(5, 3)
				number.Show()
				icons = []
				for k in range(3):
					icon = ui.ExpandedImageBox()
					icon.SetParent(cell)
					icon.AddFlag('not_pick')
					icon.SetPosition(3 + k * 17, 35)
					icons.append(icon)
				self.cells.append({'button': cell, 'number': number, 'icons': icons, 'date': None})
		listTop = self.TOP + 18 + self.CELL * self.ROWS + 8
		self.nowLine = self.__Text(self, self.LEFT, listTop)
		self.dayLine = self.__Text(self, self.LEFT, listTop + 16)
		for i in range(self.LIST_ROWS):
			self.listLines.append(self.__Text(self, self.LEFT + 8, listTop + 34 + i * 16))

	def Open(self):
		if _data['now'] and not self.year:
			self.year, self.month = _data['now'][1], _data['now'][2]
		self.Refresh()
		self.Show()
		self.SetTop()
		Request()
		self.nextRequest = app.GetTime() + 60.0

	def Close(self):
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def OnUpdate(self):
		if app.GetTime() >= self.nextRequest:
			self.nextRequest = app.GetTime() + 60.0
			Request()

	def __Month(self, step):
		if not self.year:
			return
		self.month += step
		if self.month < 1:
			self.month, self.year = 12, self.year - 1
		elif self.month > 12:
			self.month, self.year = 1, self.year + 1
		self.selected = None
		self.Refresh()

	def __SelectCell(self, index):
		date = self.cells[index]['date']
		if date:
			self.selected = date
			self.__RefreshList()

	def Refresh(self):
		if not _data['now']:
			self.monthLine.SetText('Wczytywanie...')
			return
		if not self.year:
			self.year, self.month = _data['now'][1], _data['now'][2]
		today = _data['now'][1:4]
		if self.selected is None and (self.year, self.month) == today[:2]:
			self.selected = today
		self.monthLine.SetText('%s %d' % (MONTHS[self.month - 1], self.year))
		first = DaysFromCivil(self.year, self.month, 1)
		lead = Weekday(first)
		count = DaysInMonth(self.year, self.month)
		for i, cell in enumerate(self.cells):
			d = i - lead + 1
			for icon in cell['icons']:
				icon.Hide()
			if d < 1 or d > count:
				cell['date'] = None
				cell['number'].SetText('')
				cell['button'].SetUpVisual(IMG + 'black_bg.tga')
				cell['button'].Disable()
				continue
			cell['button'].Enable()
			date = (self.year, self.month, d)
			cell['date'] = date
			cell['number'].SetText(str(d))
			cell['button'].SetUpVisual(IMG + ('today_bg.tga' if date == today else 'black_bg.tga'))
			kinds = []
			for start, end, kind, value in EventsOnDay(*date):
				if kind not in kinds:
					kinds.append(kind)
			for k, kind in enumerate(kinds[:3]):
				icon = cell['icons'][k]
				icon.LoadImage(IMG + KIND_ICON.get(kind, 'bonus_event.tga'))
				icon.SetScale(0.36, 0.36)
				icon.Show()
		self.__RefreshList()

	def __RefreshList(self):
		active = ActiveNow()
		if active:
			names = []
			for kind, value, until in active:
				names.append(KindName(kind, value))
			self.nowLine.SetText('Teraz trwa: ' + ', '.join(names))
			self.nowLine.SetPackedFontColor(0xff7cff7c)
		else:
			self.nowLine.SetText('Teraz nie trwa \xbfaden event.')
			self.nowLine.SetPackedFontColor(0xffc8c8c8)
		for line in self.listLines:
			line.SetText('')
		if not self.selected:
			self.dayLine.SetText('')
			return
		y, m, d = self.selected
		self.dayLine.SetText('%02d.%02d.%d:' % (d, m, y))
		events = EventsOnDay(y, m, d)
		if not events:
			self.listLines[0].SetText('Brak event\xf3w tego dnia.')
			self.listLines[0].SetPackedFontColor(0xffc8c8c8)
			return
		for i, (start, end, kind, value) in enumerate(events[:self.LIST_ROWS]):
			line = self.listLines[i]
			line.SetText('%s - %s   %s' % (HHMM(start), HHMM(end), KindName(kind, value)))
			r, g, b = KIND_COLOR.get(kind, (1.0, 1.0, 1.0))
			line.SetFontColor(r, g, b)
		if len(events) > self.LIST_ROWS:
			self.listLines[-1].SetText('... i %d wi\xeacej' % (len(events) - self.LIST_ROWS + 1))


def GetWindow():
	if not _data['window']:
		_data['window'] = EventCalendarWindow()
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
