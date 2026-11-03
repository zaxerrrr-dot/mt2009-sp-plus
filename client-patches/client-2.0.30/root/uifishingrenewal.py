# MT2009_PLUS_FISHING_RENEWAL_V1 - the new fishing minigame (the owner, 3 November 2026: "Nasza mini gre wedkarska
# zastap ta wersja" - github.com/amun3808/metin2-fishing-renewal, uifishinggame.py / uiscript/fishinggamewindow.py;
# the pictures GF 26.1.11's d:/ymir work/ui/game/fishing/*.sub on d:/ymir work/ui/fishing_01.dds, pack "fishren",
# tools/fishren). The game as pl-wiki "Lowienie" has it: a fish bites, the window opens, click the fish three times
# while it swims inside (or on the edge of) the circle - within 15 s; a click beside it ("Miss") costs a second.
# Three hits: the server rolls the rod's chance for the catch; the time out or the window closed: the bait is lost.
#
# No new exe (the renewal's exe parts are replaced): the server (fish_renewal.cpp, server-patches/fishren) decides
# over the chat command channel -
#   client -> server  /fishren hello                 (Start(): this client has the window - game.py's hello block)
#                     /fishren end <token> <hits>    (the game is over)
#   server -> client  FISHREN start <token> <seconds> <hits>  |  FISHREN stop          (game.py "FISHREN" -> OnCommand)
# The rod's motions are the exe's own fishing packets. A server without the patch never sends "start": the old bar
# minigame (uiFishing) goes on as before; so does it for a cast made before the hello (the first seconds in game).
# The renewal's fish turns with wndMgr.AniImageSetRotation (a new exe function); here it is four ExpandedImageBoxes,
# one a frame, turned with wndMgr.SetRotation, which our exe has. Its fishing cursor is used only if an exe has one.
#
# Python 2.7 as the client has it; the texts are CP1250 escapes.

import app
import chat
import math
import net
import ui
import wndMgr

FISHING_PATH = 'd:/ymir work/ui/game/fishing/'
FISH_PATH = FISHING_PATH + 'fish/'
WAVE_PATH = FISHING_PATH + 'wave/'

EFFECT_SIZE = 32
EFFECT_DURATION = 0.3	# "Hit", "Miss" and the wave stay this long (s)
HIT_WAIT = 1.0			# the next hit counts a second after the last one (s); the server wants >= 2 s for three
MISS_PENALTY = 1.0		# a click beside the fish takes this much off the timer (s)
FRAME_TIME = 0.12		# the fish's swimming frames (s each)
CHANGE_COURSE = 0.7		# a new course this often (s)
SPEED_MIN = 60			# the fish swims 60-120 px a second (the renewal: 1-2 px a frame)
SPEED_MAX = 120

TEXT_START = 'Ryba bierze! Kliknij j\xb9 %d razy, gdy p\xb3ywa w kole (masz %d s).'
TEXT_TIP = 'Trafienia'

_data = {'window': None}


def Send(command):
	net.SendChatPacket('/fishren ' + command)


def ToInt(value, default=0):
	try:
		return int(value)
	except (TypeError, ValueError):
		return default


def _SetCursor(fish):
	# MT2009_PLUS_FISHING_RENEWAL_V1: the renewal's fishing cursor (app.FISH) only with an exe that has it
	if not hasattr(app, 'FISH'):
		return
	want = app.FISH if fish else app.NORMAL
	if app.GetCursor() != want:
		app.SetCursor(want)


class WaterArea(ui.Window):
	"""The water's clicks and hover (a plain ImageBox has no mouse-down event in our ui.py)."""

	def __init__(self, owner):
		ui.Window.__init__(self)
		self.owner = owner

	def __del__(self):
		ui.Window.__del__(self)

	def OnMouseLeftButtonDown(self):
		if self.owner:
			self.owner.Click()
		return True

	def OnMouseOverIn(self):
		_SetCursor(True)

	def OnMouseOverOut(self):
		_SetCursor(False)


class FishingRenewalWindow(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.isLoaded = 0
		self.water = None
		self.goalCircle = None
		self.countText = None
		self.timerGauge = None
		self.navArea = None
		self.container = None
		self.clickArea = None
		self.fishFrames = []
		self.wave = None
		self.missEffect = None
		self.hitEffect = None
		self.__Reset()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __Reset(self):
		self.token = 0
		self.need = 3
		self.limit = 15
		self.endTime = 0.0
		self.clickTime = 0.0
		self.nextHit = 0.0
		self.nextCourse = 0.0
		self.nextFrame = 0.0
		self.frame = 0
		self.lastUpdate = 0.0
		self.speed = SPEED_MIN
		self.fishX = 0.0
		self.fishY = 0.0
		self.rotation = 0.0
		self.courseX = 0
		self.courseY = 0
		self.hits = 0
		self.canHit = False
		self.sent = False

	def __Load(self):
		if self.isLoaded:
			return
		self.isLoaded = 1
		ui.PythonScriptLoader().LoadScriptFile(self, 'UIScript/fishingrenewalwindow.py')
		self.GetChild('titlebar').SetCloseEvent(ui.__mem_func__(self.Close))
		self.water = self.GetChild('fishing_background_water')
		self.goalCircle = self.GetChild('fishing_goal_circle')
		self.countText = self.GetChild('fishing_goal_count_text')
		self.timerGauge = self.GetChild('fishing_timer_gauge')
		self.navArea = self.GetChild('fishing_water_navArea')
		self.navArea.Hide()

		# the renewal's trick: the effects in a container of size 0 at the circle's centre (the origin), so they never
		# take the water's mouse events; the click area over all of it
		self.container = ui.Window()
		self.container.SetParent(self.water)
		self.container.SetSize(0, 0)
		(cx, cy) = self.goalCircle.GetLocalPosition()
		self.container.SetPosition(cx + self.goalCircle.GetWidth() / 2, cy + self.goalCircle.GetHeight() / 2)
		self.container.AddFlag('not_pick')
		self.container.Show()

		self.fishFrames = []
		for i in (1, 2, 3, 4):
			image = ui.ExpandedImageBox()
			image.SetParent(self.container)
			image.AddFlag('not_pick')
			image.LoadImage(FISH_PATH + 'fishing_fish_%d.sub' % i)
			image.Hide()
			self.fishFrames.append(image)

		self.wave = ui.AniImageBox()
		self.wave.SetParent(self.container)
		self.wave.AddFlag('not_pick')
		for i in (1, 2, 3, 4):
			self.wave.AppendImage(WAVE_PATH + 'fishing_effect_wave_%d.sub' % i)
		self.wave.SetDelay(4)
		self.wave.Hide()

		self.missEffect = ui.ImageBox()
		self.missEffect.SetParent(self.container)
		self.missEffect.AddFlag('not_pick')
		self.missEffect.LoadImage(FISHING_PATH + 'fishing_effect_miss.sub')
		self.missEffect.Hide()

		self.hitEffect = ui.ImageBox()
		self.hitEffect.SetParent(self.container)
		self.hitEffect.AddFlag('not_pick')
		self.hitEffect.LoadImage(FISHING_PATH + 'fishing_effect_hit.sub')
		self.hitEffect.Hide()

		self.clickArea = WaterArea(self)
		self.clickArea.SetParent(self.water)
		self.clickArea.SetPosition(0, 0)
		self.clickArea.SetSize(self.water.GetWidth(), self.water.GetHeight())
		self.clickArea.Show()

	def Destroy(self):
		_SetCursor(False)
		if self.clickArea:
			self.clickArea.owner = None
		self.clickArea = None
		self.fishFrames = []
		self.wave = None
		self.missEffect = None
		self.hitEffect = None
		self.container = None
		self.ClearDictionary()
		self.isLoaded = 0

	# the server's "start": a fish bit
	def Start(self, token, seconds, need):
		self.__Load()
		self.__Reset()
		self.token = token
		self.limit = max(1, seconds)
		self.need = max(1, need)
		now = app.GetTime()
		self.endTime = now + self.limit
		self.lastUpdate = now
		self.__ChangeCourse(now)
		(self.fishX, self.fishY) = (float(self.courseX), float(self.courseY))
		self.__ChangeCourse(now)
		self.__RefreshCount()
		self.__PlaceFish()
		self.timerGauge.SetColor(1.0, 1.0, 1.0, 1.0)
		self.goalCircle.SetColor(1.0, 1.0, 1.0, 1.0)
		for effect in (self.wave, self.missEffect, self.hitEffect):
			effect.Hide()
		self.Show()
		self.SetTop()
		chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_START % (self.need, self.limit))

	# the server's "stop": the cast is over (result taken, time out, the rod pulled out)
	def Stop(self):
		self.sent = True
		self.__Hide()

	def __Hide(self):
		_SetCursor(False)
		self.Hide()

	def __Finish(self):
		if not self.sent and self.token:
			self.sent = True
			Send('end %d %d' % (self.token, self.hits))
		self.__Hide()

	def Close(self):
		self.__Finish()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def __RefreshCount(self):
		self.countText.SetText('%d/%d' % (self.hits, self.need))

	def __ChangeCourse(self, now):
		x = self.navArea.GetWidth() / 2 - 10
		y = self.navArea.GetHeight() / 2 - 10
		self.courseX = app.GetRandom(-x, x)
		self.courseY = app.GetRandom(-y, y)
		self.speed = app.GetRandom(SPEED_MIN, SPEED_MAX)
		self.nextCourse = now + CHANGE_COURSE

	def __PlaceFish(self):
		for i, image in enumerate(self.fishFrames):
			image.SetPosition(int(self.fishX), int(self.fishY))
			image.SetRotation(self.rotation)
			if i == self.frame:
				image.Show()
			else:
				image.Hide()

	def __FishSize(self):
		if not self.fishFrames:
			return (30, 30)
		return (self.fishFrames[0].GetWidth(), self.fishFrames[0].GetHeight())

	def Click(self):
		if self.sent or not self.token:
			return
		now = app.GetTime()
		self.clickTime = now
		(fw, fh) = self.__FishSize()
		(mx, my) = wndMgr.GetMouseLocalPosition(self.container.hWnd)
		fx, fy = int(self.fishX), int(self.fishY)
		if mx >= fx and mx <= fx + fw and my + 8 >= fy and my - 2 <= fy + fh:
			if not self.canHit or now < self.nextHit:
				return
			self.hitEffect.SetPosition(mx, my - EFFECT_SIZE)
			self.hitEffect.Show()
			self.hits += 1
			self.__RefreshCount()
			self.nextHit = now + HIT_WAIT
		else:
			self.endTime -= MISS_PENALTY
			self.timerGauge.SetColor(1.0, 0.0, 0.0, 1.0)
			self.missEffect.SetPosition(mx, my - EFFECT_SIZE)
			self.missEffect.Show()
		self.wave.SetPosition(mx - EFFECT_SIZE / 2, my - EFFECT_SIZE / 2)
		self.wave.Show()

	def OnUpdate(self):
		if self.sent or not self.token:
			return
		now = app.GetTime()
		if now >= self.endTime or self.hits >= self.need:
			self.__Finish()
			return

		if now >= self.nextCourse:
			self.__ChangeCourse(now)
		if now >= self.nextFrame:
			self.frame = (self.frame + 1) % len(self.fishFrames)
			self.nextFrame = now + FRAME_TIME

		# swim towards the course (time based, not per frame as the renewal)
		dt = min(0.1, max(0.0, now - self.lastUpdate))
		self.lastUpdate = now
		dx = self.courseX - self.fishX
		dy = self.courseY - self.fishY
		dist = math.sqrt(dx * dx + dy * dy)
		step = self.speed * dt
		if dist > 1.0 and step > 0.0:
			if step > dist:
				step = dist
			self.fishX += dx / dist * step
			self.fishY += dy / dist * step
			# +90: the picture's fish looks up
			self.rotation = math.atan2(dy, dx) * 180.0 / math.pi + 90.0
		self.__PlaceFish()

		(fw, fh) = self.__FishSize()
		radius = self.goalCircle.GetWidth() / 2
		x = self.fishX + fw / 2
		y = self.fishY + fh / 2
		self.canHit = x * x + y * y < radius * radius
		if self.canHit:
			self.goalCircle.SetColor(1.0, 0.0, 0.0, 1.0)
		else:
			self.goalCircle.SetColor(1.0, 1.0, 1.0, 1.0)

		self.timerGauge.SetPercentage(max(0.0, self.endTime - now), self.limit)
		if now > self.clickTime + EFFECT_DURATION:
			self.timerGauge.SetColor(1.0, 1.0, 1.0, 1.0)
			self.hitEffect.Hide()
			self.missEffect.Hide()
			self.wave.Hide()


def GetWindow():
	if not _data['window']:
		_data['window'] = FishingRenewalWindow()
	return _data['window']


def Start():
	"""game.py's hello block (every login and warp): this client has the new fishing window."""
	Send('hello')


def DestroyWindow():
	window = _data['window']
	if window:
		window.Hide()
		window.Destroy()
	_data['window'] = None


# game.py "FISHREN": the server's lines.
def OnCommand(sub='', *args):
	if sub == 'start':
		GetWindow().Start(ToInt(args[0] if args else 0), ToInt(args[1] if len(args) > 1 else 15, 15),
			ToInt(args[2] if len(args) > 2 else 3, 3))
	elif sub == 'stop':
		if _data['window']:
			_data['window'].Stop()
