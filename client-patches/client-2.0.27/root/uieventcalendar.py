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
# its days mask names; an "activate now" one on the days it spans. The
# window shows a week (Monday to Sunday) with today lit and a banner on top.
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
	"""A week at a time (the operator, 28 September: "zeby kalendarz
	wyswietlal sie tygodniowo ... bardziej widoczne ze dzisiaj jest jakis
	event"): a banner with what runs now or what today holds, then the seven
	days, today lit, each with its events and their hours."""
	WIDTH = 500
	LEFT = 12
	ROW = 50
	EVENTS_PER_ROW = 3

	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)
		self.widgets = []
		self.rows = []
		self.weekStart = None
		self.nextRequest = 0.0
		self.AddFlag('movable')
		self.AddFlag('float')
		self.top = 34 + 44 + 28
		height = self.top + 7 * self.ROW + 14
		self.SetSize(self.WIDTH, height)
		self.SetTitleName('Kalendarz event\xf3w')
		self.SetCloseEvent(ui.__mem_func__(self.Close))
		self.__Build()
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

	def __Button(self, x, y, text, event, *args):
		button = ui.Button()
		button.SetParent(self)
		button.SetPosition(x, y)
		button.SetUpVisual('d:/ymir work/ui/public/small_button_01.sub')
		button.SetOverVisual('d:/ymir work/ui/public/small_button_02.sub')
		button.SetDownVisual('d:/ymir work/ui/public/small_button_03.sub')
		button.SetText(text)
		button.SetEvent(event, *args)
		button.Show()
		self.widgets.append(button)
		return button

	def __Build(self):
		width = self.WIDTH
		# The banner: what runs now, else what today holds.
		banner = ui.Bar()
		banner.SetParent(self)
		banner.SetPosition(self.LEFT, 34)
		banner.SetSize(width - self.LEFT * 2, 40)
		banner.SetColor(0x80202020)
		banner.Show()
		self.widgets.append(banner)
		self.bannerLine1 = self.__Text(self, width // 2, 38, '', True)
		self.bannerLine1.SetOutline()
		self.bannerLine2 = self.__Text(self, width // 2, 55, '', True)
		self.bannerLine2.SetOutline()
		navY = 34 + 44 + 2
		self.__Button(self.LEFT, navY, '<', ui.__mem_func__(self.__Week), -1)
		self.__Button(self.LEFT + 48, navY, 'Dzi\x9c', ui.__mem_func__(self.__Week), 0)
		self.__Button(width - self.LEFT - 43, navY, '>', ui.__mem_func__(self.__Week), 1)
		self.weekLine = self.__Text(self, width // 2 + 20, navY + 3, '', True)
		for i in range(7):
			y = self.top + i * self.ROW
			light = ui.Bar()
			light.SetParent(self)
			light.SetPosition(self.LEFT, y)
			light.SetSize(width - self.LEFT * 2, self.ROW - 4)
			light.SetColor(0x60305080)
			self.widgets.append(light)
			day = ui.ExpandedImageBox()
			day.SetParent(self)
			day.SetPosition(self.LEFT + 2, y + 1)
			day.LoadImage(IMG + 'black_bg.tga')
			day.SetScale(0.78, 0.78)
			day.Show()
			self.widgets.append(day)
			name = self.__Text(self, self.LEFT + 24, y + 8, WEEKDAYS[i], True)
			date = self.__Text(self, self.LEFT + 24, y + 24, '', True)
			entries = []
			for k in range(self.EVENTS_PER_ROW):
				icon = ui.ExpandedImageBox()
				icon.SetParent(self)
				icon.AddFlag('not_pick')
				icon.SetPosition(self.LEFT + 58 + k * 140, y + 4)
				self.widgets.append(icon)
				time = self.__Text(self, self.LEFT + 58 + k * 140 + 34, y + 6)
				what = self.__Text(self, self.LEFT + 58 + k * 140 + 34, y + 22)
				entries.append((icon, time, what))
			more = self.__Text(self, width - self.LEFT - 60, y + 36)
			self.rows.append({'light': light, 'day': day, 'name': name, 'date': date, 'entries': entries, 'more': more})

	def Open(self):
		self.weekStart = None
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

	def __Today(self):
		if not _data['now']:
			return None
		return DaysFromCivil(*_data['now'][1:4])

	def __Week(self, step):
		today = self.__Today()
		if today is None:
			return
		if step == 0 or self.weekStart is None:
			self.weekStart = today - Weekday(today)
		else:
			self.weekStart += step * 7
		self.Refresh()

	def Refresh(self):
		today = self.__Today()
		if today is None:
			self.bannerLine1.SetText('Wczytywanie...')
			self.bannerLine2.SetText('')
			return
		if self.weekStart is None:
			self.weekStart = today - Weekday(today)
		self.__RefreshBanner(today)
		first = CivilFromDays(self.weekStart)
		last = CivilFromDays(self.weekStart + 6)
		self.weekLine.SetText('%02d.%02d - %02d.%02d.%d' % (first[2], first[1], last[2], last[1], last[0]))
		for i, row in enumerate(self.rows):
			day = self.weekStart + i
			y, m, d = CivilFromDays(day)
			isToday = day == today
			row['date'].SetText('%02d.%02d' % (d, m))
			row['day'].LoadImage(IMG + ('today_bg.tga' if isToday else 'black_bg.tga'))
			row['day'].SetScale(0.78, 0.78)
			if isToday:
				row['light'].Show()
				row['name'].SetPackedFontColor(0xffffe060)
				row['date'].SetPackedFontColor(0xffffe060)
			else:
				row['light'].Hide()
				row['name'].SetPackedFontColor(0xffe0e0e0)
				row['date'].SetPackedFontColor(0xffa0a0a0)
			events = EventsOnDay(y, m, d)
			for k, (icon, time, what) in enumerate(row['entries']):
				if k < len(events):
					start, end, kind, value = events[k]
					icon.LoadImage(IMG + KIND_ICON.get(kind, 'bonus_event.tga'))
					icon.SetScale(0.6, 0.6)
					icon.Show()
					time.SetText('%s - %s' % (HHMM(start), HHMM(end)))
					what.SetText(KindName(kind, value))
					r, g, b = KIND_COLOR.get(kind, (1.0, 1.0, 1.0))
					what.SetFontColor(r, g, b)
					time.SetPackedFontColor(0xffffffff if isToday else 0xffc8c8c8)
				else:
					icon.Hide()
					time.SetText('')
					what.SetText('')
			if not events:
				row['entries'][0][1].SetText('brak event\xf3w')
				row['entries'][0][1].SetPackedFontColor(0xff808080)
			row['more'].SetText('+%d wi\xeacej' % (len(events) - self.EVENTS_PER_ROW) if len(events) > self.EVENTS_PER_ROW else '')

	def __RefreshBanner(self, today):
		active = ActiveNow()
		y, m, d = CivilFromDays(today)
		todays = EventsOnDay(y, m, d)
		if active:
			names = []
			for kind, value, until in active:
				names.append(KindName(kind, value))
			self.bannerLine1.SetText('TRWA TERAZ: ' + ', '.join(names))
			self.bannerLine1.SetPackedFontColor(0xff5cff5c)
		elif todays:
			self.bannerLine1.SetText('DZI\x8c S\xa5 EVENTY!')
			self.bannerLine1.SetPackedFontColor(0xffffd040)
		else:
			self.bannerLine1.SetText('Dzi\x9c nie ma event\xf3w.')
			self.bannerLine1.SetPackedFontColor(0xffa0a0a0)
		if todays:
			parts = ['%s %s' % (HHMM(start), KindName(kind, value)) for start, end, kind, value in todays[:4]]
			self.bannerLine2.SetText('Dzi\x9c: ' + ',  '.join(parts) + (' ...' if len(todays) > 4 else ''))
			self.bannerLine2.SetPackedFontColor(0xffffe8a0)
		else:
			self.bannerLine2.SetText('')


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
