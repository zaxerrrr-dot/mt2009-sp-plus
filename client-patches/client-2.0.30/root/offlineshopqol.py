# MT2009_PLUS_SHOP_QOL_V2 - the offline shop's second round (2026-10-13, Autor: Vekirion), client side:
#   * the lines' clocks from the server ("IkaShopMeta <item> <since> <pct> <hours> <min>",
#     game.py) - how long a line has stood unsold, and its automatic price drop
#   * the owner's "stale" frame: a line unsold for Y hours lit up in the owner's
#     window; Y is this client's (shop_stale_glow.cfg, 0 = off)
#   * the auto price drop window (one of the price window's options)
#   * the shop's pages ("IkaShopPages <n>": 2 = the bigger shop the panel switched on)
# Python 2.7 as the client has it; texts without Polish letters or as CP1250 escapes.
import app
import ui
import chat
import localeInfo
import playerbot_lang

STALE_GLOW_FILE = "shop_stale_glow.cfg"
STALE_GLOW_COLOR = (1.0, 0.55, 0.1, 1.0)
AUTO_PRICE_PCT_MAX = 50
AUTO_PRICE_HOURS_MAX = 720

T = playerbot_lang.T

# item id -> {"since": unix time, "pct": int, "hours": int, "min": long}
g_itemMeta = {}
g_shopPages = 1
g_manageWindow = None
_staleGlowHours = None


def SetManageWindow(window):
	global g_manageWindow
	g_manageWindow = window


def _Open(name, mode):
	try:
		return old_open(name, mode)  # the real file open (system.py); open() reads packs
	except NameError:
		return open(name, mode)


def GetStaleGlowHours():
	global _staleGlowHours
	if _staleGlowHours is None:
		_staleGlowHours = 0
		try:
			f = _Open(STALE_GLOW_FILE, "r")
			try:
				_staleGlowHours = max(0, min(24 * 90, int(f.read().strip() or "0")))
			finally:
				f.close()
		except (IOError, ValueError):
			_staleGlowHours = 0
	return _staleGlowHours


def SetStaleGlowHours(hours):
	global _staleGlowHours
	_staleGlowHours = max(0, min(24 * 90, int(hours)))
	try:
		f = _Open(STALE_GLOW_FILE, "w")
		try:
			f.write("%d\n" % _staleGlowHours)
		finally:
			f.close()
	except IOError:
		pass


def GetMeta(itemId):
	return g_itemMeta.get(itemId)


def GetAgeSeconds(itemId):
	meta = g_itemMeta.get(itemId)
	if not meta or meta["since"] <= 0:
		return -1
	return max(0, app.GetGlobalTimeStamp() - meta["since"])


def IsStale(itemId):
	hours = GetStaleGlowHours()
	if hours <= 0:
		return False
	age = GetAgeSeconds(itemId)
	return age >= 0 and age >= hours * 3600


def FormatAge(seconds):
	if seconds < 0:
		return "?"
	days = seconds / 86400
	hours = (seconds % 86400) / 3600
	minutes = (seconds % 3600) / 60
	if days > 0:
		return "%dd %dh" % (days, hours)
	if hours > 0:
		return "%dh %dmin" % (hours, minutes)
	return "%dmin" % minutes


def AutoPriceText(meta):
	if not meta or meta.get("pct", 0) <= 0:
		return T("Auto-obnizka: wylaczona", "Auto price drop: off")
	return T("Auto-obnizka: -%d%% co %dh, min. %s", "Auto price drop: -%d%% every %dh, min. %s") % (
		meta["pct"], meta["hours"], localeInfo.NumberToMoneyString(meta["min"]))


def TooltipLines(itemId):
	lines = []
	age = GetAgeSeconds(itemId)
	if age >= 0:
		lines.append(T("Bez sprzedazy od: %s", "Unsold for: %s") % FormatAge(age))
	meta = g_itemMeta.get(itemId)
	if meta and meta.get("pct", 0) > 0:
		lines.append(AutoPriceText(meta))
	return lines


# Sent a few a second (Pump, from the owner's window every frame): the server
# takes ten chat commands in half a second, and a mass edit sends one a line.
AUTO_PRICE_SEND_GAP = 0.12
_autoPriceQueue = []
_autoPriceNext = [0.0]


def SendAutoPrice(itemId, pct, hours, minYang):
	_autoPriceQueue.append("/ikashop_autoprice %d %d %d %d" % (int(itemId), int(pct), int(hours), long(minYang)))


def Pump():
	if not _autoPriceQueue:
		return
	import clientclock
	now = clientclock.Now()
	if now < _autoPriceNext[0]:
		return
	import net
	net.SendChatPacket(_autoPriceQueue.pop(0))
	_autoPriceNext[0] = now + AUTO_PRICE_SEND_GAP


#### server commands (game.py) ####
def OnMeta(itemId, since, pct, hours, minYang):
	try:
		itemId = int(itemId)
		g_itemMeta[itemId] = {"since": long(since), "pct": int(pct), "hours": int(hours), "min": long(minYang)}
	except ValueError:
		return
	if g_manageWindow:
		try:
			g_manageWindow.OnShopMetaUpdate()
		except Exception:
			pass


def OnPages(pages):
	global g_shopPages
	try:
		g_shopPages = max(1, min(2, int(pages)))
	except ValueError:
		g_shopPages = 1
	if g_manageWindow:
		try:
			g_manageWindow.SetShopPages(g_shopPages)
		except Exception:
			import dbg
			dbg.TraceError("offlineshopqol: pages")


def OnAutoPrice(itemId, newPrice):
	try:
		item = __import__("item")
		import constInfo
		for data in constInfo.myshop_data.get("items", {}).values():
			if data.get("id") == int(itemId):
				item.SelectItem(data["vnum"])
				chat.AppendChat(chat.CHAT_TYPE_INFO, T("Auto-obnizka: %s - nowa cena %s", "Auto price drop: %s - new price %s") % (
					item.GetItemName(), localeInfo.NumberToMoneyString(long(newPrice))))
				return
	except Exception:
		pass


#### the window ####
def _MakeText(parent, x, y, text, color=0xFFE5E0D4):
	line = ui.TextLine()
	line.SetParent(parent)
	line.SetPosition(x, y)
	line.SetPackedFontColor(color)
	line.SetText(text)
	line.AddFlag("not_pick")
	line.Show()
	return line


def _MakeEdit(parent, x, y, w, maxLen, number=True):
	bar = ui.SlotBar()
	bar.SetParent(parent)
	bar.SetPosition(x, y)
	bar.SetSize(w, 18)
	bar.Show()
	edit = ui.EditLine()
	edit.SetParent(bar)
	edit.SetPosition(4, 2)
	edit.SetSize(w - 6, 16)
	edit.SetMax(maxLen)
	if number:
		edit.SetNumberMode()
	edit.Show()
	return bar, edit


def _MakeButton(parent, x, y, text, event):
	button = ui.Button()
	button.SetParent(parent)
	button.SetPosition(x, y)
	button.SetUpVisual("d:/ymir work/ui/public/middle_button_01.sub")
	button.SetOverVisual("d:/ymir work/ui/public/middle_button_02.sub")
	button.SetDownVisual("d:/ymir work/ui/public/middle_button_03.sub")
	button.SetText(text)
	button.SetEvent(event)
	button.Show()
	return button


def _Number(edit, default):
	try:
		return long(edit.GetText().strip() or str(default))
	except ValueError:
		return default


class AutoPriceWindow(ui.BoardWithTitleBar):
	"""The price window's "Auto-obnizka": X% less every Y hours nobody bought,
	never under a minimum - and, apart from it, this client's stale frame."""
	WIDTH = 300
	HEIGHT = 256

	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)
		self.AddFlag("movable")
		self.AddFlag("float")
		self.SetSize(self.WIDTH, self.HEIGHT)
		self.SetTitleName(T("Auto-obnizka ceny", "Auto price drop"))
		self.SetCloseEvent(ui.__mem_func__(self.Close))
		self.acceptEvent = None
		self.children = []

		y = 36
		self.children.append(_MakeText(self, 18, y, T("Gdy nikt nie kupi przedmiotu:", "When nobody buys the item:")))
		y += 22
		self.children.append(_MakeText(self, 18, y + 2, T("obnizaj cene o", "lower the price by")))
		self.pctBar, self.pctEdit = _MakeEdit(self, 150, y, 40, 2)
		self.children.append(_MakeText(self, 196, y + 2, "%"))
		y += 24
		self.children.append(_MakeText(self, 18, y + 2, T("co (godzin)", "every (hours)")))
		self.hoursBar, self.hoursEdit = _MakeEdit(self, 150, y, 40, 3)
		y += 24
		self.children.append(_MakeText(self, 18, y + 2, T("nie ponizej (Yang)", "not below (Yang)")))
		# "k" / "kk" too, as in the price window (localeInfo.MoneyStringToNumber)
		self.minBar, self.minEdit = _MakeEdit(self, 150, y, 130, 14, False)
		y += 20
		self.minPreview = _MakeText(self, 154, y, "", 0xFFFFD56A)
		self.lastMinText = None
		y += 28
		self.children.append(_MakeText(self, 18, y, T("Ramka zalegajacych (wszystkie przedmioty):", "Stale frame (all items):"), 0xFFFFD56A))
		y += 22
		self.children.append(_MakeText(self, 18, y + 2, T("podswietl po (godzin, 0 = wyl.)", "light up after (hours, 0 = off)")))
		self.glowBar, self.glowEdit = _MakeEdit(self, 230, y, 50, 4)
		y += 34
		self.okButton = _MakeButton(self, 18, y, T("Zapisz", "Save"), ui.__mem_func__(self.__OnAccept))
		self.offButton = _MakeButton(self, 18 + 92, y, T("Wylacz", "Off"), ui.__mem_func__(self.__OnOff))
		self.cancelButton = _MakeButton(self, 18 + 184, y, T("Anuluj", "Cancel"), ui.__mem_func__(self.Close))

		self.pctEdit.SetTabEvent(ui.__mem_func__(self.hoursEdit.SetFocus))
		self.hoursEdit.SetTabEvent(ui.__mem_func__(self.minEdit.SetFocus))
		self.minEdit.SetTabEvent(ui.__mem_func__(self.glowEdit.SetFocus))
		self.glowEdit.SetTabEvent(ui.__mem_func__(self.pctEdit.SetFocus))
		for edit in (self.pctEdit, self.hoursEdit, self.minEdit, self.glowEdit):
			edit.SetReturnEvent(ui.__mem_func__(self.__OnAccept))
			edit.SetEscapeEvent(ui.__mem_func__(self.Close))

	def __del__(self):
		ui.BoardWithTitleBar.__del__(self)

	def Destroy(self):
		self.acceptEvent = None
		self.children = []
		self.Hide()

	def Open(self, current, price, acceptEvent):
		"""current: (pct, hours, min) or None; price: the line's price (a hint for the minimum)."""
		self.acceptEvent = acceptEvent
		if current and current[0] > 0:
			(pct, hours, minYang) = current
		else:
			(pct, hours, minYang) = (5, 12, max(1, long(price) / 2) if price > 0 else 0)
		self.pctEdit.SetText(str(pct))
		self.hoursEdit.SetText(str(hours))
		self.minEdit.SetText(str(minYang))
		self.glowEdit.SetText(str(GetStaleGlowHours()))
		self.SetCenterPosition()
		self.SetTop()
		self.Show()
		self.pctEdit.SetFocus()

	def __MinYang(self):
		try:
			return long(localeInfo.MoneyStringToNumber(self.minEdit.GetText().strip()))
		except Exception:
			return 0

	# the minimum as a price under its input: 150000 -> 150.000, 3kk -> 3.000.000
	def OnUpdate(self):
		text = self.minEdit.GetText()
		if text == self.lastMinText:
			return
		self.lastMinText = text
		value = self.__MinYang()
		if value > 0:
			self.minPreview.SetText(localeInfo.NumberToMoneyString(value))
		else:
			self.minPreview.SetText("")

	def __SaveGlow(self):
		SetStaleGlowHours(_Number(self.glowEdit, 0))
		if g_manageWindow:
			try:
				g_manageWindow.OnShopMetaUpdate()
			except Exception:
				pass

	def __OnAccept(self):
		pct = int(_Number(self.pctEdit, 0))
		hours = int(_Number(self.hoursEdit, 0))
		minYang = self.__MinYang()
		if pct < 1 or pct > AUTO_PRICE_PCT_MAX or hours < 1 or hours > AUTO_PRICE_HOURS_MAX or minYang < 1:
			chat.AppendChat(chat.CHAT_TYPE_INFO, T(
				"Auto-obnizka: 1-%d%%, co 1-%d godzin, cena minimalna co najmniej 1 Yang.",
				"Auto price drop: 1-%d%%, every 1-%d hours, a minimum of at least 1 Yang.") % (AUTO_PRICE_PCT_MAX, AUTO_PRICE_HOURS_MAX))
			return True
		self.__SaveGlow()
		if self.acceptEvent:
			self.acceptEvent((pct, hours, minYang))
		self.Close()
		return True

	def __OnOff(self):
		self.__SaveGlow()
		if self.acceptEvent:
			self.acceptEvent((0, 0, 0))
		self.Close()

	def Close(self):
		for edit in (self.pctEdit, self.hoursEdit, self.minEdit, self.glowEdit):
			edit.KillFocus()
		self.Hide()
		return True

	def OnPressEscapeKey(self):
		return self.Close()
