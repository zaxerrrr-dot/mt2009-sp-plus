# Obrona Statku (Hydra, map 367): the mast's HP bar (MT2009_PLUS_SHIP_DEFENSE_V1).
# Owsap v6.2.6's AllianceTargetBoard (root/uitarget.py, ENABLE_DEFENSE_WAVE) on our
# chat-command protocol: no packet, no change to the exe. The core
# (playerbot_ship_defense.cpp, CShipDefense::SendMastHP) sends everyone on the
# ship one command, at most once a second and only when the HP changed:
#   ShipMastHP <hp> <max hp>      the bar shows (or moves)
#   ShipMastHP 0 0                the bar goes (not started, won, lost, closed)
# and once more to whoever enters the ship. game.py passes the command here
# (serverCommandList["ShipMastHP"]); the game window's Close() destroys the bar
# at every warp, so leaving the ship hides it as well.
#
# The bar is a small board at the top of the screen, under the target window:
# "Maszt statku", a red gauge and "<hp> / <max> (<pct>%)"; the mouse goes
# through it. Python 2.7 as the client has it; the texts are CP1250 escapes.
import background
import ui
import wndMgr

MAP_NAME = "metin2_map_defensewave"
WIDTH = 220
HEIGHT = 46
TOP = 58
TEXT_TITLE = "Maszt statku"
TEXT_HP = "%s / %s  (%d%%)"
COLOR_TITLE = 0xffe6d0a0
COLOR_LOW = 0xffff6060

_wnd = [None]


def Thousands(n):
	s = str(abs(int(n)))
	parts = []
	while len(s) > 3:
		parts.insert(0, s[-3:])
		s = s[:-3]
	parts.insert(0, s)
	return ("-" if n < 0 else "") + " ".join(parts)


class MastBar(ui.ThinBoard):
	def __init__(self):
		ui.ThinBoard.__init__(self)
		self.AddFlag("not_pick")
		self.AddFlag("float")
		self.SetSize(WIDTH, HEIGHT)

		title = ui.TextLine()
		title.SetParent(self)
		title.AddFlag("not_pick")
		title.SetWindowHorizontalAlignCenter()
		title.SetHorizontalAlignCenter()
		title.SetPosition(0, 6)
		title.SetPackedFontColor(COLOR_TITLE)
		title.SetOutline()
		title.SetText(TEXT_TITLE)
		title.Show()

		gauge = ui.Gauge()
		gauge.SetParent(self)
		gauge.AddFlag("not_pick")
		gauge.MakeGauge(WIDTH - 20, "red")
		gauge.SetPosition(10, 22)
		gauge.Show()

		value = ui.TextLine()
		value.SetParent(self)
		value.AddFlag("not_pick")
		value.SetWindowHorizontalAlignCenter()
		value.SetHorizontalAlignCenter()
		value.SetPosition(0, 30)
		value.SetOutline()
		value.Show()

		self.title = title
		self.gauge = gauge
		self.value = value
		self.UpdatePosition()

	def __del__(self):
		ui.ThinBoard.__del__(self)

	def Destroy(self):
		self.Hide()
		self.title = None
		self.gauge = None
		self.value = None

	def UpdatePosition(self):
		self.SetPosition((wndMgr.GetScreenWidth() - WIDTH) / 2, TOP)

	def SetHP(self, hp, hpMax):
		hp = max(0, min(hp, hpMax))
		pct = int(hp * 100 / hpMax) if hpMax > 0 else 0
		if hp > 0 and pct == 0:
			pct = 1
		self.gauge.SetPercentage(hp, hpMax)
		self.value.SetText(TEXT_HP % (Thousands(hp), Thousands(hpMax), pct))
		if pct <= 30:
			self.value.SetPackedFontColor(COLOR_LOW)
		else:
			self.value.SetPackedFontColor(0xffffffff)

	def OnUpdate(self):
		# a stale bar never outlives the ship (the game window closes at every warp anyway)
		if str(background.GetCurrentMapName()) != MAP_NAME:
			self.Hide()


def ToInt(value):
	try:
		return int(value)
	except (TypeError, ValueError):
		return 0


def OnCommand(hp="0", hpMax="0", *rest):
	hp, hpMax = ToInt(hp), ToInt(hpMax)
	if hpMax <= 0:
		if _wnd[0]:
			_wnd[0].Hide()
		return
	if not _wnd[0]:
		_wnd[0] = MastBar()
	_wnd[0].UpdatePosition()
	_wnd[0].SetHP(hp, hpMax)
	_wnd[0].Show()


def DestroyWindow():
	if _wnd[0]:
		_wnd[0].Destroy()
		_wnd[0] = None
