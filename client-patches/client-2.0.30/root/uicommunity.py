# MT2009_PLUS_COMMUNITY_V1 - the Community window ("Spolecznosc"): one window for the friends (friends /
# blocked / requests), the guild and the settings, with a status message, the state the player shows
# (online / AFK / appear offline; Auto Lowy by itself) and each friend's level and location.
# The idea, the look and the graphics come from "Community System (Messenger Renewal)" (Autor: Best Studio,
# github.com/ybeststudio; its .sub files are the GF client's d:/ymir work/ui/game/windows/community_*); the
# package's uicommunity.py was written for another root (its own ui.py widgets, an exe module "community"),
# so this is our own window on our ui.py, with the package's layout and sizes.
#
# Works with every exe: the lists come from the exe's messenger handler (this window takes the handler and
# passes every call on to the old uimessenger window, which stays as it was), the rest are chat commands
# (server-patches/community, playerbot_community.cpp):
#   "/community hello | state <0|1|4> | auto <0|1> | status [text] | privacy <flags> | guild | party <name>"
#   "community_my", "community_friend", "community_guild", "community_request" (game.py -> OnServerCommand).
# A server without the patch never answers "hello": the window still works as a messenger (no states,
# levels or messages).
# Settings of this client (spolecznosc.cfg): the login notices, favourites first, the message under the
# name and the favourites of each character. The privacy settings are the server's (community_flags).
# Python 2.7 as the client has it; texts CP1250 as escapes.
import app
import ui
import net
import grp
import chat
import guild
import player
import messenger
import wndMgr
import uiToolTip
import uiCommon
from _weakref import proxy

ROOT = "d:/ymir work/ui/game/windows/"
CHECKBOX_IMAGE = "mt2009_ui/checkbox/checkbox.tga"
CHECKED_IMAGE = "mt2009_ui/checkbox/checked.tga"
CONFIG_FILE = "spolecznosc.cfg"

GROUP_FRIEND = getattr(messenger, "GROUP_INDEX_FRIEND", 0)
GROUP_GUILD = getattr(messenger, "GROUP_INDEX_GUILD", 1)
GROUP_BLOCK = getattr(messenger, "GROUP_INDEX_BLOCK", 2)

STATE_CONNECT = 0
STATE_LEFT_SEAT = 1
STATE_AUTO_HUNT = 2
STATE_SHOP_OPEN = 3
STATE_DISCONNECT = 4

PRIVACY_HIDE_LEVEL = 8
PRIVACY_HIDE_LOCATION = 16

STATUS_MAX_LEN = 50

WINDOW_WIDTH = 302
WINDOW_HEIGHT = 424

VIEW_MESSENGER = 0
VIEW_GUILD = 1
VIEW_CONFIG = 2

LIST_FRIEND = 0
LIST_BLOCK = 1
LIST_REQUEST = 2

ROW_WIDTH = 258
ROW_HEIGHT = 34
ROW_STEP = 36
FRIEND_LIST_Y = 139
FRIEND_LIST_ROWS = 7
GUILD_LIST_Y = 107
GUILD_LIST_ROWS = 7

LEVEL_COLOR = grp.GenerateColor(0.54, 0.72, 0.55, 1.0)
STATUS_COLOR = grp.GenerateColor(0.65, 0.65, 0.65, 1.0)
OFFLINE_COLOR = grp.GenerateColor(0.55, 0.55, 0.55, 1.0)
NAME_COLOR = grp.GenerateColor(0.9, 0.9, 0.9, 1.0)

T = {
	"TITLE": "Spo\xb3eczno\x9c\xe6",
	"TAB_FRIEND": "Znajomi",
	"TAB_GUILD": "Gildia",
	"TAB_CONFIG": "Ustawienia",
	"SUB_FRIEND": "Lista znajomych",
	"SUB_BLOCK": "Zablokowani",
	"SUB_REQUEST": "Zaproszenia do znajomych",
	"SUB_GUILD": "Cz\xb3onkowie gildii",
	"ADD_FRIEND": "Dodaj znajomego",
	"BLOCK": "Zablokuj gracza",
	"WHISPER": "Szept",
	"DELETE": "Usu\xf1",
	"UNBLOCK": "Odblokuj",
	"ACCEPT": "Przyjmij",
	"REFUSE": "Odrzu\xe6",
	"KICK": "Wyrzu\xe6 z gildii",
	"PARTY_INVITE": "Zapro\x9c do grupy",
	"FAVORITE_ADD": "Dodaj do ulubionych",
	"FAVORITE_DEL": "Usu\xf1 z ulubionych",
	"LOCATION": "Po\xb3o\xbfenie",
	"NO_GUILD": "Brak gildii",
	"HAS_NO_GUILD": "Nie nale\xbfysz do \xbfadnej gildii.",
	"GUILD_INFO": "Okno gildii",
	"CONNECT": "Online",
	"LEFT_SEAT": "Zaraz wracam (AFK)",
	"AUTO_HUNT": "Auto \xa3owy",
	"SHOP_OPEN": "Sklep otwarty",
	"DISCONNECT": "Offline",
	"APPEAR_OFFLINE": "Niewidoczny",
	"LEFT_SEAT_TIP": "Znajomi zobacz\xb9, \xbfe jeste\x9c AFK.",
	"DISCONNECT_TIP": "Znajomi zobacz\xb9 Ci\xea jako offline.",
	"MY_STATUS": "Tw\xf3j opis",
	"MY_STATUS_EMPTY": "Kliknij o\xb3\xf3wek, aby ustawi\xe6 opis.",
	"STATUS_BUTTON": "Opis widoczny dla znajomych",
	"STATUS_DIALOG": "Opis (do 50 znak\xf3w, puste - usu\xf1)",
	"CHANNEL": "Kana\xb3 %d",
	"MAP": "Mapa: %s",
	"LEVEL": "Lv. %d",
	"CHAMPION": "Poziom Czempiona %d",
	"LOCATION_UNKNOWN": "Po\xb3o\xbfenie nieznane",
	"OFFLINE": "Offline",
	"LOVER": "Ma\xb3\xbfonek",
	"LOVE_POINT": "Punkty mi\xb3o\x9cci: %d%%",
	"ADD_FRIEND_DIALOG": "Dodaj znajomego",
	"BLOCK_DIALOG": "Zablokuj gracza",
	"DELETE_QUESTION": "Usun\xb9\xe6 %s z listy znajomych?",
	"UNBLOCK_QUESTION": "Odblokowa\xe6 %s?",
	"KICK_QUESTION": "Wyrzuci\xe6 %s z gildii?",
	"REQUEST_CHAT": "%s chce doda\xe6 Ci\xea do znajomych - odpowiedz w okienku albo w Spo\xb3eczno\x9cci (zak\xb3adka Zaproszenia).",
	"FRIEND_LOGIN": "Tw\xf3j znajomy %s jest teraz w grze.",
	"GUILD_LOGIN": "Cz\xb3onek gildii %s jest teraz w grze.",
	"SELECT_FIRST": "Najpierw zaznacz gracza na li\x9ccie.",
	"OFFLINE_PARTY": "Ten gracz jest offline.",
	"CONFIG_NOTICE": "Powiadomienia",
	"CONFIG_PRIVACY": "Prywatno\x9c\xe6",
	"CONFIG_LIST": "Lista",
	"OPT_FRIEND_LOGIN": "Znajomy wchodzi do gry - wiadomo\x9c\xe6 na czacie",
	"OPT_GUILD_LOGIN": "Cz\xb3onek gildii wchodzi do gry - wiadomo\x9c\xe6",
	"OPT_HIDE_LEVEL": "Nie pokazuj znajomym mojego poziomu",
	"OPT_HIDE_LOCATION": "Nie pokazuj innym, gdzie jestem",
	"OPT_FAVORITE_FIRST": "Ulubieni na g\xf3rze listy",
	"OPT_SHOW_STATUS": "Opis znajomego pod jego nickiem",
	"SAVE": "Zapisz",
	"DEFAULT": "Domy\x9clne",
	"SAVED": "Ustawienia Spo\xb3eczno\x9cci zapisane.",
	"EMPTY_LIST": "Lista jest pusta.",
}

# client settings (spolecznosc.cfg): key=0/1, fav=<my name>:<friend>
OPTIONS = (
	("friend_login", "OPT_FRIEND_LOGIN", True),
	("guild_login", "OPT_GUILD_LOGIN", False),
	("favorite_first", "OPT_FAVORITE_FIRST", True),
	("show_status", "OPT_SHOW_STATUS", True),
)
PRIVACY_OPTIONS = (
	("hide_level", "OPT_HIDE_LEVEL", PRIVACY_HIDE_LEVEL),
	("hide_location", "OPT_HIDE_LOCATION", PRIVACY_HIDE_LOCATION),
)

STATE_IMAGE = {
	STATE_CONNECT: ROOT + "community_state_green.sub",
	STATE_LEFT_SEAT: ROOT + "community_state_deep_red.sub",
	STATE_AUTO_HUNT: ROOT + "community_state_blue.sub",
	STATE_SHOP_OPEN: ROOT + "community_state_yellow.sub",
	STATE_DISCONNECT: ROOT + "community_state_red.sub",
}
STATE_TEXT = {
	STATE_CONNECT: "CONNECT",
	STATE_LEFT_SEAT: "LEFT_SEAT",
	STATE_AUTO_HUNT: "AUTO_HUNT",
	STATE_SHOP_OPEN: "SHOP_OPEN",
	STATE_DISCONNECT: "DISCONNECT",
}
# what the drop list offers (Auto Lowy is set by the hunt itself)
STATE_CHOICES = (
	(STATE_CONNECT, "CONNECT", None),
	(STATE_LEFT_SEAT, "LEFT_SEAT", "LEFT_SEAT_TIP"),
	(STATE_DISCONNECT, "APPEAR_OFFLINE", "DISCONNECT_TIP"),
)

_state = {"window": None, "settings": None, "hello": False, "auto": None, "next": 0.0, "since": 0.0}


def _T(key):
	return T.get(key, key)


def _Int(value, default=0):
	try:
		return int(value)
	except (TypeError, ValueError):
		return default


def _Open(name, mode):
	try:
		return old_open(name, mode)  # the real file open (system.py); open() reads packs
	except NameError:
		return open(name, mode)


def _MyName():
	try:
		return player.GetName()
	except Exception:
		return ""


def Settings():
	if _state["settings"] is None:
		settings = {"options": dict((key, default) for key, text, default in OPTIONS), "fav": set()}
		try:
			f = _Open(CONFIG_FILE, "r")
			try:
				for line in f.read().split("\n"):
					key, sep, value = line.strip().partition("=")
					if not sep:
						continue
					if key == "fav":
						owner, sep2, name = value.partition(":")
						if sep2 and owner and name:
							settings["fav"].add((owner, name))
					elif key in settings["options"]:
						settings["options"][key] = value.strip() == "1"
			finally:
				f.close()
		except IOError:
			pass
		_state["settings"] = settings
	return _state["settings"]


def SaveSettings():
	settings = Settings()
	try:
		f = _Open(CONFIG_FILE, "w")
		try:
			for key, value in sorted(settings["options"].items()):
				f.write("%s=%d\n" % (key, 1 if value else 0))
			for owner, name in sorted(settings["fav"]):
				f.write("fav=%s:%s\n" % (owner, name))
		finally:
			f.close()
	except IOError:
		pass


def Option(key):
	return bool(Settings()["options"].get(key, False))


def IsFavorite(name):
	return (_MyName(), name) in Settings()["fav"]


def SetFavorite(name, on):
	key = (_MyName(), name)
	if on:
		Settings()["fav"].add(key)
	else:
		Settings()["fav"].discard(key)
	SaveSettings()


def _GuildID():
	for module, name in ((guild, "GetGuildID"), (player, "GetGuildID")):
		function = getattr(module, name, None)
		if function is not None:
			try:
				return function()
			except Exception:
				pass
	return 0


def MapName(mapIndex):
	if mapIndex <= 0:
		return ""
	base = mapIndex / 10000 if mapIndex >= 10000 else mapIndex
	try:
		import uitpbookmarks
		name = uitpbookmarks.MAP_NAMES.get(base)
		if name:
			return name
	except Exception:
		pass
	try:
		import localeInfo
		name = getattr(localeInfo, "MINIMAP_ZONE_NAME_DICT_BY_IDX", {}).get(base)
		if name:
			return name
	except Exception:
		pass
	return "%d" % base


def LocationLines(channel, mapIndex):
	if channel <= 0 and mapIndex <= 0:
		return [_T("LOCATION_UNKNOWN")]
	lines = []
	if channel > 0:
		lines.append(_T("CHANNEL") % channel)
	if mapIndex > 0:
		lines.append(_T("MAP") % MapName(mapIndex))
	return lines


def _Send(command):
	try:
		import warpsafe
		if not warpsafe.InGame():
			return False
	except Exception:
		pass
	net.SendChatPacket(command)
	return True


def _Chat(text):
	chat.AppendChat(chat.CHAT_TYPE_INFO, text)


def _MakeButton(parent, x, y, name, tooltip=None):
	button = ui.Button()
	button.SetParent(parent)
	button.SetPosition(x, y)
	button.SetUpVisual(ROOT + name + "_default.sub")
	button.SetOverVisual(ROOT + name + "_mouse_over.sub")
	button.SetDownVisual(ROOT + name + "_click.sub")
	if tooltip:
		button.SetToolTipText(tooltip)
	button.Show()
	return button


def _MakeImage(parent, x, y, image, pick=False):
	box = ui.ImageBox()
	box.SetParent(parent)
	if not pick:
		box.AddFlag("not_pick")
	box.LoadImage(image)
	box.SetPosition(x, y)
	box.Show()
	return box


def _MakeText(parent, x, y, text="", align=None, color=None, outline=True):
	line = ui.TextLine()
	line.SetParent(parent)
	line.AddFlag("not_pick")
	line.SetPosition(x, y)
	if align == "center":
		line.SetHorizontalAlignCenter()
	elif align == "right":
		line.SetHorizontalAlignRight()
	if color is not None:
		line.SetPackedFontColor(color)
	if outline:
		line.SetOutline()
	line.SetText(text)
	line.Show()
	return line


def _Fit(text, width):
	"""Cuts text to about width pixels (6 px a letter) with '...'."""
	limit = max(4, width / 6)
	if len(text) <= limit:
		return text
	return text[:limit - 3] + "..."


class FriendInfo(object):
	def __init__(self, name):
		self.name = name
		self.online = False
		self.state = STATE_DISCONNECT
		self.level = 0
		self.conqueror = 0
		self.channel = 0
		self.mapIndex = 0
		self.status = ""


class ClickArea(ui.Window):
	"""An invisible tab area of the window's pictures: click, hover picture, tooltip."""

	def __init__(self, parent, x, y, width, height, event, tooltip=None, overImage=None, getToolTip=None):
		ui.Window.__init__(self)
		self.SetParent(parent)
		self.SetPosition(x, y)
		self.SetSize(width, height)
		self.event = event
		self.tooltipText = tooltip
		self.getToolTip = getToolTip
		self.over = None
		if overImage:
			self.over = _MakeImage(self, 0, 0, overImage)
			self.over.Hide()
		self.Show()

	def __del__(self):
		ui.Window.__del__(self)

	def OnMouseLeftButtonUp(self):
		if self.event:
			self.event()
		return True

	def OnMouseOverIn(self):
		if self.over:
			self.over.Show()
		if self.tooltipText and self.getToolTip:
			self.getToolTip().ShowToolTip([self.tooltipText])

	def OnMouseOverOut(self):
		if self.over:
			self.over.Hide()
		if self.getToolTip:
			self.getToolTip().HideToolTip()


class TextToolTip(object):
	def __init__(self):
		self.toolTip = uiToolTip.ToolTip(150)
		self.toolTip.HideToolTip()

	def ShowText(self, lines, colors=None):
		toolTip = self.toolTip
		toolTip.ClearToolTip()
		width = 60
		for line in lines:
			width = max(width, len(line) * 6 + 20)
		toolTip.SetThinBoardSize(min(320, width))
		for i, line in enumerate(lines):
			color = colors[i] if colors and i < len(colors) and colors[i] is not None else uiToolTip.ToolTip.FONT_COLOR
			toolTip.AppendTextLine(line, color)
		toolTip.ShowToolTip()

	def Hide(self):
		self.toolTip.HideToolTip()

	def Destroy(self):
		self.toolTip.HideToolTip()
		self.toolTip = None


class MemberRow(ui.Window):
	"""One line of a list: picture, state, name (+ message), level and the line's buttons."""

	def __init__(self, owner, kind, name):
		ui.Window.__init__(self)
		self.owner = proxy(owner)
		self.kind = kind
		self.name = name
		self.selected = False
		self.over = False
		self.SetSize(ROW_WIDTH, ROW_HEIGHT)
		self.AddFlag("float")

		self.bg = _MakeImage(self, 0, 0, ROOT + "community_info_bar_default.sub")
		self.stateIcon = _MakeImage(self, 7, 12, STATE_IMAGE[STATE_DISCONNECT])
		self.nameText = _MakeText(self, 25, 10, name, color=NAME_COLOR)
		self.statusText = _MakeText(self, 25, 18, "", color=STATUS_COLOR)
		self.statusText.Hide()
		self.levelText = _MakeText(self, 0, 10, "", align="right", color=LEVEL_COLOR)
		self.buttons = []
		self.SetMouseWheelEvent(self.__OnWheel)

		if kind == "friend":
			self.locationButton = self.__Button(170, "community_icon_position", self.__OnLocation, self.__OverLocation, imageOnly=True)
			self.favoriteButton = self.__Button(200, "community_icon_wishlist", self.__OnFavorite, self.__OverFavorite)
			self.partyButton = self.__Button(230, "community_icon_party_invite", self.__OnParty, self.__OverParty)
			self.levelText.SetPosition(165, 10)
		elif kind == "guild":
			self.locationButton = self.__Button(230, "community_icon_position", self.__OnLocation, self.__OverLocation, imageOnly=True)
			self.levelText.SetPosition(225, 10)
		elif kind == "block":
			self.__Button(230, "community_icon_x", self.__OnUnblock, self.__OverUnblock)
		elif kind == "request":
			self.locationButton = self.__Button(170, "community_icon_position", self.__OnLocation, self.__OverLocation, imageOnly=True)
			self.__Button(200, "community_icon_request_accept", self.__OnAccept, self.__OverAccept)
			self.__Button(230, "community_icon_x", self.__OnRefuse, self.__OverRefuse)
			self.levelText.SetPosition(165, 10)
		self.Show()

	def __del__(self):
		ui.Window.__del__(self)

	def Destroy(self):
		self.owner = None
		self.buttons = []
		self.Hide()

	def __Button(self, x, name, event, overEvent, imageOnly=False):
		button = ui.Button()
		button.SetParent(self)
		button.SetPosition(x, 5)
		if imageOnly:
			image = ROOT + name + "_default.sub"
			button.SetUpVisual(image)
			button.SetOverVisual(ROOT + name + "_mouse_over.sub")
			button.SetDownVisual(ROOT + name + "_mouse_over.sub")
		else:
			button.SetUpVisual(ROOT + name + "_default.sub")
			button.SetOverVisual(ROOT + name + "_mouse_over.sub")
			button.SetDownVisual(ROOT + name + "_click.sub")
		button.SetEvent(ui.__mem_func__(event))
		button.SetShowToolTipEvent(ui.__mem_func__(overEvent))
		button.SetHideToolTipEvent(ui.__mem_func__(self.__OverOut))
		button.SetMouseWheelEvent(self.__OnWheel)
		button.Show()
		self.buttons.append(button)
		return button

	def __OnWheel(self, delta):
		if self.owner:
			self.owner.OnListWheel(delta)

	def __Info(self):
		return self.owner.GetInfo(self.kind, self.name) if self.owner else None

	def __OverOut(self):
		if self.owner:
			self.owner.HideToolTip()

	def __OverLocation(self):
		info = self.__Info()
		if info and self.owner:
			if self.kind == "friend" and not info.online:
				self.owner.ShowToolTip([_T("OFFLINE")])
			else:
				self.owner.ShowToolTip([_T("LOCATION")] + LocationLines(info.channel, info.mapIndex))

	def __OnLocation(self):
		info = self.__Info()
		if info and (info.online or self.kind != "friend") and (info.channel or info.mapIndex):
			_Chat("%s: %s" % (self.name, ", ".join(LocationLines(info.channel, info.mapIndex))))

	def __OverFavorite(self):
		if self.owner:
			self.owner.ShowToolTip([_T("FAVORITE_DEL") if IsFavorite(self.name) else _T("FAVORITE_ADD")])

	def __OnFavorite(self):
		SetFavorite(self.name, not IsFavorite(self.name))
		if self.owner:
			self.owner.HideToolTip()
			self.owner.RefreshList()

	def __OverParty(self):
		if self.owner:
			self.owner.ShowToolTip([_T("PARTY_INVITE")])

	def __OnParty(self):
		info = self.__Info()
		if not info or not info.online:
			_Chat(_T("OFFLINE_PARTY"))
			return
		_Send("/community party %s" % self.name)

	def __OverUnblock(self):
		if self.owner:
			self.owner.ShowToolTip([_T("UNBLOCK")])

	def __OnUnblock(self):
		if self.owner:
			self.owner.AskUnblock(self.name)

	def __OverAccept(self):
		if self.owner:
			self.owner.ShowToolTip([_T("ACCEPT")])

	def __OnAccept(self):
		if self.owner:
			self.owner.AnswerRequest(self.name, True)

	def __OverRefuse(self):
		if self.owner:
			self.owner.ShowToolTip([_T("REFUSE")])

	def __OnRefuse(self):
		if self.owner:
			self.owner.AnswerRequest(self.name, False)

	def Refresh(self, info, showStatus):
		online = info.online
		state = info.state if online else STATE_DISCONNECT
		self.stateIcon.LoadImage(STATE_IMAGE.get(state, STATE_IMAGE[STATE_CONNECT]))
		if self.kind == "block":
			self.stateIcon.Hide()
			self.nameText.SetPosition(12, 10)
		else:
			self.stateIcon.Show()
		self.nameText.SetPackedFontColor(NAME_COLOR if online or self.kind == "block" else OFFLINE_COLOR)

		levelText = ""
		if self.kind in ("friend", "guild", "request") and info.level > 0 and (online or self.kind != "friend"):
			levelText = _T("LEVEL") % info.level
		self.levelText.SetText(levelText)

		status = info.status if self.kind == "friend" else ""
		if status and showStatus:
			self.nameText.SetPosition(25, 3)
			self.statusText.SetText(_Fit(status, 140))
			self.statusText.Show()
		else:
			if self.kind != "block":
				self.nameText.SetPosition(25, 10)
			self.statusText.Hide()

		if self.kind == "friend":
			if IsFavorite(self.name):
				self.favoriteButton.SetUpVisual(ROOT + "community_icon_wishlist_click.sub")
			else:
				self.favoriteButton.SetUpVisual(ROOT + "community_icon_wishlist_default.sub")

	def SetSelected(self, selected):
		self.selected = selected
		self.__RefreshBg()

	def __RefreshBg(self):
		if self.selected or self.over:
			self.bg.LoadImage(ROOT + "community_info_bar_mouse_over.sub")
		else:
			self.bg.LoadImage(ROOT + "community_info_bar_default.sub")

	def OnMouseOverIn(self):
		self.over = True
		self.__RefreshBg()
		if self.owner:
			self.owner.ShowRowToolTip(self.kind, self.name)

	def OnMouseOverOut(self):
		self.over = False
		self.__RefreshBg()
		if self.owner:
			self.owner.HideToolTip()

	def OnMouseLeftButtonDown(self):
		if self.owner:
			self.owner.OnSelectRow(self)
		return True

	def OnMouseLeftButtonDoubleClick(self):
		if self.owner:
			self.owner.OnDoubleClickRow(self)
		return True


class CheckRow(ui.Window):
	def __init__(self, owner, key, text):
		ui.Window.__init__(self)
		self.owner = proxy(owner)
		self.key = key
		self.textMark = None
		box = mark = None
		try:
			box = _MakeImage(self, 0, 3, CHECKBOX_IMAGE)
			mark = _MakeImage(self, 0, -1, CHECKED_IMAGE)
			mark.Hide()
		except Exception:
			for image in (box, mark):
				if image:
					image.Hide()
			box = mark = None
			self.textMark = _MakeText(self, 0, 1, "[ ]")
		self.box = box
		self.mark = mark
		self.label = _MakeText(self, 18, 1, text)
		self.SetSize(240, 18)
		self.Show()

	def __del__(self):
		ui.Window.__del__(self)

	def SetChecked(self, checked):
		if self.textMark:
			self.textMark.SetText("[x]" if checked else "[ ]")
		elif checked:
			self.mark.Show()
		else:
			self.mark.Hide()

	def OnMouseLeftButtonUp(self):
		if self.owner:
			self.owner.ToggleOption(self.key)
		return True


class StateDropList(ui.Window):
	def __init__(self, owner):
		ui.Window.__init__(self)
		self.owner = proxy(owner)
		self.AddFlag("float")
		self.rows = []
		count = len(STATE_CHOICES)
		self.SetSize(170, 16 * count)
		for i, (state, textKey, tipKey) in enumerate(STATE_CHOICES):
			if i == 0:
				image = ROOT + "community_drop_list_top.sub"
			elif i == count - 1:
				image = ROOT + "community_drop_list_bottom.sub"
			else:
				image = ROOT + "community_drop_list_middle.sub"
			bg = _MakeImage(self, 0, i * 16, image)
			over = _MakeImage(self, 2, i * 16 + 1, ROOT + "community_drop_mouse_over.sub")
			over.Hide()
			icon = _MakeImage(self, 8, i * 16 + 3, STATE_IMAGE[state])
			text = _MakeText(self, 24, i * 16 + 1, _T(textKey))
			self.rows.append((state, tipKey, bg, over, icon, text))
		self.overIndex = -1
		self.Hide()

	def __del__(self):
		ui.Window.__del__(self)

	def __Index(self):
		x, y = self.GetMouseLocalPosition()
		if x < 0 or x >= self.GetWidth() or y < 0:
			return -1
		index = y / 16
		if index >= len(self.rows):
			return -1
		return index

	def OnUpdate(self):
		index = self.__Index()
		if index == self.overIndex:
			return
		self.overIndex = index
		for i, row in enumerate(self.rows):
			if i == index:
				row[3].Show()
			else:
				row[3].Hide()
		if self.owner:
			if index >= 0 and self.rows[index][1]:
				self.owner.ShowToolTip([_T(self.rows[index][1])])
			else:
				self.owner.HideToolTip()

	def OnMouseLeftButtonUp(self):
		index = self.__Index()
		self.Hide()
		if self.owner:
			self.owner.HideToolTip()
			if index >= 0:
				self.owner.OnSelectState(self.rows[index][0])
		return True

	def OnMouseOverOut(self):
		self.overIndex = -1
		for row in self.rows:
			row[3].Hide()
		if self.owner:
			self.owner.HideToolTip()


class CommunityWindow(ui.BoardWithTitleBar):

	def __init__(self, interface):
		ui.BoardWithTitleBar.__init__(self)
		self.interface = proxy(interface)
		self.oldMessenger = None
		try:
			if interface.wndMessenger:
				self.oldMessenger = proxy(interface.wndMessenger)
		except Exception:
			self.oldMessenger = None

		self.friends = {}
		self.blocks = set()
		self.requests = _state.setdefault("requests", {})	# kept over a warp: the server still waits for the answer
		self.guildMembers = {}
		self.guildLocation = {}
		self.lover = None
		self.myState = STATE_CONNECT
		self.myStatus = ""
		self.myPrivacy = 0
		self.hasServer = False
		self.view = VIEW_MESSENGER
		self.listKind = LIST_FRIEND
		self.rows = {}
		self.shownRows = []
		self.selected = None
		self.startLine = 0
		self.guildStartLine = 0
		self.dialog = None
		self.question = None
		self.nextGuildAsk = 0.0
		self.twinkle = 0.0
		self.toolTip = TextToolTip()
		self.pendingOptions = None

		self.SetSize(WINDOW_WIDTH, WINDOW_HEIGHT)
		self.AddFlag("movable")
		self.AddFlag("float")
		self.SetTitleName(_T("TITLE"))
		self.SetCloseEvent(ui.__mem_func__(self.Close))
		self.__BuildHeader()
		self.__BuildMessengerView()
		self.__BuildGuildView()
		self.__BuildConfigView()
		self.__BuildMainTabs()
		self.SetCenterPosition()
		self.Hide()

		messenger.SetMessengerHandler(self)
		try:
			messenger.RefreshGuildMember()
		except Exception:
			pass
		self.__SelectView(VIEW_MESSENGER)

	def __del__(self):
		ui.BoardWithTitleBar.__del__(self)

	def Destroy(self):
		try:
			if self.oldMessenger:
				messenger.SetMessengerHandler(self.oldMessenger)
			else:
				messenger.SetMessengerHandler(None)
		except Exception:
			pass
		self.__CloseDialogs()
		if self.toolTip:
			self.toolTip.Destroy()
			self.toolTip = None
		for row in self.rows.values():
			row.Destroy()
		self.rows = {}
		self.shownRows = []
		self.selected = None
		self.stateDrop = None
		self.oldMessenger = None
		self.interface = None
		self.Hide()

	# ------------------------------------------------------------------ building
	def __BuildHeader(self):
		self.myInfo = _MakeImage(self, 11, 35, ROOT + "community_info_bar_player.sub", pick=True)
		self.myStateIcon = _MakeImage(self.myInfo, 10, 12, STATE_IMAGE[STATE_CONNECT])
		self.dropButton = _MakeButton(self.myInfo, 26, 9, "community_drop_button")
		self.dropButton.SetEvent(ui.__mem_func__(self.__OnDropButton))
		self.myStateArea = ClickArea(self.myInfo, 4, 6, 20, 22, None, getToolTip=self.__GetToolTip)
		self.myStateArea.OnMouseOverIn = ui.__mem_func__(self.__OverMyState)
		self.guildNameText = _MakeText(self.myInfo, 95, 10, _T("NO_GUILD"), align="center")
		self.myNameText = _MakeText(self.myInfo, 205, 10, "", align="center")
		self.statusButton = _MakeButton(self.myInfo, 259, 8, "community_icon_my_message", _T("STATUS_BUTTON"))
		self.statusButton.SetEvent(ui.__mem_func__(self.__OnStatusButton))

		self.familyBar = _MakeImage(self, 15, 72, ROOT + "community_info_bar_family_default.sub", pick=True)
		self.familyIcon = _MakeImage(self.familyBar, 6, 5, ROOT + "community_icon_family_default.sub")
		self.familyText = _MakeText(self.familyBar, 34, 10, "", color=STATUS_COLOR)
		self.loverState = _MakeImage(self.familyBar, 34, 12, STATE_IMAGE[STATE_DISCONNECT])
		self.loverState.Hide()

		self.stateDrop = StateDropList(self)
		self.stateDrop.SetParent(self)
		self.stateDrop.SetPosition(19, 63)

	def __BuildMessengerView(self):
		self.messengerView = ui.Window()
		self.messengerView.SetParent(self)
		self.messengerView.SetPosition(0, 0)
		self.messengerView.SetSize(WINDOW_WIDTH, WINDOW_HEIGHT)
		self.messengerView.AddFlag("not_pick")
		self.messengerView.Show()
		parent = self.messengerView

		self.subTabImages = [
			_MakeImage(parent, 10, 112, ROOT + "community_friend_member.sub"),
			_MakeImage(parent, 10, 112, ROOT + "community_friend_block.sub"),
			_MakeImage(parent, 10, 112, ROOT + "community_friend_request.sub"),
		]
		self.subTabAreas = [
			ClickArea(parent, 13, 117, 46, 20, lambda: self.__SelectList(LIST_FRIEND), _T("SUB_FRIEND"), ROOT + "community_tab_mouse_over_member.sub", self.__GetToolTip),
			ClickArea(parent, 58, 117, 46, 20, lambda: self.__SelectList(LIST_BLOCK), _T("SUB_BLOCK"), ROOT + "community_tab_mouse_over_block.sub", self.__GetToolTip),
			ClickArea(parent, 103, 117, 46, 20, lambda: self.__SelectList(LIST_REQUEST), _T("SUB_REQUEST"), ROOT + "community_tab_mouse_over_request.sub", self.__GetToolTip),
		]
		self.requestTwinkle = _MakeImage(parent, 104, 118, ROOT + "community_request_button_twinkle.sub")
		self.requestTwinkle.Hide()

		self.friendInvite = _MakeButton(parent, 160, 112, "community_icon_friend_invite", _T("ADD_FRIEND"))
		self.friendInvite.SetEvent(ui.__mem_func__(self.__OnAddFriend))
		self.friendBlock = _MakeButton(parent, 190, 112, "community_icon_block", _T("BLOCK"))
		self.friendBlock.SetEvent(ui.__mem_func__(self.__OnBlock))
		self.friendWhisper = _MakeButton(parent, 220, 112, "community_icon_whisper", _T("WHISPER"))
		self.friendWhisper.SetEvent(ui.__mem_func__(self.__OnWhisper))
		self.friendDelete = _MakeButton(parent, 250, 112, "community_icon_delete", _T("DELETE"))
		self.friendDelete.SetEvent(ui.__mem_func__(self.__OnDelete))

		self.friendListBg = ui.BoxedBoard()
		self.friendListBg.SetParent(parent)
		self.friendListBg.SetPosition(11, FRIEND_LIST_Y)
		self.friendListBg.SetSize(266, 255)
		self.friendListBg.SetMouseWheelEvent(self.OnListWheel)
		self.friendListBg.Show()
		self.emptyText = _MakeText(parent, 144, FRIEND_LIST_Y + 120, _T("EMPTY_LIST"), align="center", color=OFFLINE_COLOR)

		self.friendScroll = ui.ScrollBar()
		self.friendScroll.SetParent(parent)
		self.friendScroll.SetPosition(278, FRIEND_LIST_Y)
		self.friendScroll.SetScrollBarSize(253)
		self.friendScroll.SetScrollEvent(ui.__mem_func__(self.__OnScroll))
		self.friendScroll.Show()

	def __BuildGuildView(self):
		self.guildView = ui.Window()
		self.guildView.SetParent(self)
		self.guildView.SetPosition(0, 0)
		self.guildView.SetSize(WINDOW_WIDTH, WINDOW_HEIGHT)
		self.guildView.AddFlag("not_pick")
		parent = self.guildView

		self.guildHas = ui.Window()
		self.guildHas.SetParent(parent)
		self.guildHas.SetPosition(0, 0)
		self.guildHas.SetSize(WINDOW_WIDTH, WINDOW_HEIGHT)
		self.guildHas.AddFlag("not_pick")
		self.guildHas.Show()
		g = self.guildHas
		_MakeImage(g, 10, 75, ROOT + "community_guild_member.sub")
		ClickArea(g, 13, 80, 46, 20, None, _T("SUB_GUILD"), None, self.__GetToolTip)
		self.guildInvite = _MakeButton(g, 160, 75, "community_icon_friend_invite", _T("ADD_FRIEND"))
		self.guildInvite.SetEvent(ui.__mem_func__(self.__OnGuildAddFriend))
		self.guildBlock = _MakeButton(g, 190, 75, "community_icon_block", _T("BLOCK"))
		self.guildBlock.SetEvent(ui.__mem_func__(self.__OnGuildBlock))
		self.guildWhisper = _MakeButton(g, 220, 75, "community_icon_whisper", _T("WHISPER"))
		self.guildWhisper.SetEvent(ui.__mem_func__(self.__OnWhisper))
		self.guildKick = _MakeButton(g, 250, 75, "community_icon_delete", _T("KICK"))
		self.guildKick.SetEvent(ui.__mem_func__(self.__OnGuildKick))

		self.guildListBg = ui.BoxedBoard()
		self.guildListBg.SetParent(g)
		self.guildListBg.SetPosition(11, GUILD_LIST_Y)
		self.guildListBg.SetSize(266, 252)
		self.guildListBg.SetMouseWheelEvent(self.OnListWheel)
		self.guildListBg.Show()

		self.guildScroll = ui.ScrollBar()
		self.guildScroll.SetParent(g)
		self.guildScroll.SetPosition(278, GUILD_LIST_Y)
		self.guildScroll.SetScrollBarSize(250)
		self.guildScroll.SetScrollEvent(ui.__mem_func__(self.__OnGuildScroll))
		self.guildScroll.Show()

		self.guildInfoButton = ui.Button()
		self.guildInfoButton.SetParent(g)
		self.guildInfoButton.SetPosition(175, 364)
		self.guildInfoButton.SetUpVisual(ROOT + "community_button_default.sub")
		self.guildInfoButton.SetOverVisual(ROOT + "community_button_mouse_over.sub")
		self.guildInfoButton.SetDownVisual(ROOT + "community_button_click.sub")
		self.guildInfoButton.SetText(_T("GUILD_INFO"))
		self.guildInfoButton.SetEvent(ui.__mem_func__(self.__OnGuildInfo))
		self.guildInfoButton.Show()

		self.guildNone = ui.Window()
		self.guildNone.SetParent(parent)
		self.guildNone.SetPosition(0, 0)
		self.guildNone.SetSize(WINDOW_WIDTH, WINDOW_HEIGHT)
		self.guildNone.AddFlag("not_pick")
		noneBg = ui.BoxedBoard()
		noneBg.SetParent(self.guildNone)
		noneBg.SetPosition(11, 75)
		noneBg.SetSize(281, 284)
		noneBg.Show()
		self.guildNoneBg = noneBg
		self.guildNoneText = _MakeText(self.guildNone, 151, 200, _T("HAS_NO_GUILD"), align="center")

	def __BuildConfigView(self):
		self.configView = ui.Window()
		self.configView.SetParent(self)
		self.configView.SetPosition(0, 0)
		self.configView.SetSize(WINDOW_WIDTH, WINDOW_HEIGHT)
		self.configView.AddFlag("not_pick")
		parent = self.configView

		bg = ui.BoxedBoard()
		bg.SetParent(parent)
		bg.SetPosition(11, 35)
		bg.SetSize(281, 322)
		bg.Show()
		self.configBg = bg

		self.optionRows = {}
		self.configTitles = []
		y = 42
		for titleKey, rows in (
				("CONFIG_NOTICE", [(key, textKey) for key, textKey, default in OPTIONS[:2]]),
				("CONFIG_PRIVACY", [(key, textKey) for key, textKey, flag in PRIVACY_OPTIONS]),
				("CONFIG_LIST", [(key, textKey) for key, textKey, default in OPTIONS[2:]])):
			title = _MakeImage(parent, 22, y, ROOT + "community_config_main_title.sub")
			_MakeText(title, 129, 6, _T(titleKey), align="center")
			self.configTitles.append(title)
			y += 32
			for key, textKey in rows:
				row = CheckRow(self, key, _T(textKey))
				row.SetParent(parent)
				row.SetPosition(30, y)
				self.optionRows[key] = row
				y += 22
			y += 8

		self.saveButton = ui.Button()
		self.saveButton.SetParent(parent)
		self.saveButton.SetPosition(175, 364)
		self.saveButton.SetUpVisual(ROOT + "community_button_default.sub")
		self.saveButton.SetOverVisual(ROOT + "community_button_mouse_over.sub")
		self.saveButton.SetDownVisual(ROOT + "community_button_click.sub")
		self.saveButton.SetText(_T("SAVE"))
		self.saveButton.SetEvent(ui.__mem_func__(self.__OnSaveConfig))
		self.saveButton.Show()

		self.defaultButton = ui.Button()
		self.defaultButton.SetParent(parent)
		self.defaultButton.SetPosition(17, 364)
		self.defaultButton.SetUpVisual(ROOT + "community_button_default.sub")
		self.defaultButton.SetOverVisual(ROOT + "community_button_mouse_over.sub")
		self.defaultButton.SetDownVisual(ROOT + "community_button_click.sub")
		self.defaultButton.SetText(_T("DEFAULT"))
		self.defaultButton.SetEvent(ui.__mem_func__(self.__OnDefaultConfig))
		self.defaultButton.Show()

	def __BuildMainTabs(self):
		self.mainTabImages = [
			_MakeImage(self, 0, 396, ROOT + "community_lower_tab_friend.sub"),
			_MakeImage(self, 0, 396, ROOT + "community_lower_tab_guild.sub"),
			_MakeImage(self, 0, 396, ROOT + "community_lower_tab_config.sub"),
		]
		self.mainTabAreas = [
			ClickArea(self, 10, 398, 95, 28, lambda: self.__SelectView(VIEW_MESSENGER), _T("TAB_FRIEND"), None, self.__GetToolTip),
			ClickArea(self, 105, 398, 95, 28, lambda: self.__SelectView(VIEW_GUILD), _T("TAB_GUILD"), None, self.__GetToolTip),
			ClickArea(self, 200, 398, 95, 28, lambda: self.__SelectView(VIEW_CONFIG), _T("TAB_CONFIG"), None, self.__GetToolTip),
		]

	# ------------------------------------------------------------------ tool tips
	def __GetToolTip(self):
		return self

	def Hide(self):
		ui.BoardWithTitleBar.Hide(self)
		self.HideToolTip()

	def ShowToolTip(self, lines, colors=None):
		toolTip = getattr(self, "toolTip", None)
		if toolTip:
			toolTip.ShowText(lines, colors)

	def HideToolTip(self):
		toolTip = getattr(self, "toolTip", None)
		if toolTip:
			toolTip.Hide()

	def ShowRowToolTip(self, kind, name):
		info = self.GetInfo(kind, name)
		if not info or kind == "block":
			return
		lines = [name]
		colors = [None]
		if kind == "friend":
			state = info.state if info.online else STATE_DISCONNECT
			lines.append(_T(STATE_TEXT.get(state, "CONNECT")))
			colors.append(LEVEL_COLOR if info.online else OFFLINE_COLOR)
		if info.level > 0 and (info.online or kind != "friend"):
			lines.append(_T("LEVEL") % info.level)
			colors.append(None)
		if info.conqueror > 0 and (info.online or kind != "friend"):
			lines.append(_T("CHAMPION") % info.conqueror)
			colors.append(None)
		if (info.online or kind != "friend") and (info.channel or info.mapIndex):
			for line in LocationLines(info.channel, info.mapIndex):
				lines.append(line)
				colors.append(None)
		if kind == "friend" and info.status:
			lines.append('"%s"' % info.status)
			colors.append(STATUS_COLOR)
		self.ShowToolTip(lines, colors)

	def __OverMyState(self):
		self.ShowToolTip([_T(STATE_TEXT.get(self.myState, "CONNECT"))])

	# ------------------------------------------------------------------ views
	def __SelectView(self, view):
		self.view = view
		self.__CloseStateDrop()
		for i, image in enumerate(self.mainTabImages):
			if i == view:
				image.Show()
			else:
				image.Hide()
		self.messengerView.Hide()
		self.guildView.Hide()
		self.configView.Hide()
		self.selected = None
		if view == VIEW_MESSENGER:
			self.myInfo.Show()
			self.familyBar.Show()
			self.messengerView.Show()
			self.__SelectList(self.listKind)
		elif view == VIEW_GUILD:
			self.myInfo.Show()
			self.familyBar.Hide()
			self.guildView.Show()
			self.__RefreshGuildView()
			self.__AskGuildLocations()
		else:
			self.myInfo.Hide()
			self.familyBar.Hide()
			self.configView.Show()
			self.__LoadConfig()
		self.RefreshList()

	def __SelectList(self, kind):
		self.listKind = kind
		for i, image in enumerate(self.subTabImages):
			if i == kind:
				image.Show()
			else:
				image.Hide()
		self.startLine = 0
		self.friendScroll.SetPos(0.0)
		self.selected = None
		self.RefreshList()

	# ------------------------------------------------------------------ data
	def GetInfo(self, kind, name):
		if kind == "friend":
			return self.friends.get(name)
		if kind == "guild":
			return self.guildMembers.get(name)
		if kind == "request":
			return self.requests.get(name)
		if kind == "block":
			info = FriendInfo(name)
			return info
		return None

	def __Friend(self, name):
		info = self.friends.get(name)
		if not info:
			info = FriendInfo(name)
			self.friends[name] = info
		return info

	def __SortedNames(self, kind):
		if kind == "friend":
			favoriteFirst = Option("favorite_first")
			def key(name):
				info = self.friends[name]
				return (0 if favoriteFirst and IsFavorite(name) else 1, 0 if info.online else 1, name.lower())
			return sorted(self.friends.keys(), key=key)
		if kind == "block":
			return sorted(self.blocks, key=lambda n: n.lower())
		if kind == "request":
			return sorted(self.requests.keys(), key=lambda n: n.lower())
		if kind == "guild":
			myName = _MyName()
			def gkey(name):
				info = self.guildMembers[name]
				return (0 if info.online else 1, name.lower())
			return sorted([n for n in self.guildMembers.keys() if n != myName], key=gkey)
		return []

	def __Row(self, kind, name):
		key = (kind, name)
		row = self.rows.get(key)
		if not row:
			row = MemberRow(self, kind, name)
			if kind == "guild":
				row.SetParent(self.guildHas)
			else:
				row.SetParent(self.messengerView)
			row.SetMouseWheelEvent(self.OnListWheel)
			self.rows[key] = row
		return row

	def __DropRows(self, kind, keepNames):
		for key in self.rows.keys():
			if key[0] == kind and key[1] not in keepNames:
				row = self.rows.pop(key)
				if self.selected is row:
					self.selected = None
				row.Destroy()

	def RefreshList(self):
		if not self.interface:
			return
		for row in self.shownRows:
			row.Hide()
		self.shownRows = []
		if self.view == VIEW_MESSENGER:
			kind = ("friend", "block", "request")[self.listKind]
			names = self.__SortedNames(kind)
			self.__DropRows(kind, set(names))
			self.__Place(kind, names, self.startLine, FRIEND_LIST_Y, FRIEND_LIST_ROWS, self.friendScroll)
			if names:
				self.emptyText.Hide()
			else:
				self.emptyText.Show()
		elif self.view == VIEW_GUILD:
			names = self.__SortedNames("guild")
			self.__DropRows("guild", set(names))
			self.__Place("guild", names, self.guildStartLine, GUILD_LIST_Y, GUILD_LIST_ROWS, self.guildScroll)
		self.__RefreshHeader()
		self.__RefreshTwinkle()

	def __Place(self, kind, names, startLine, top, rowsShown, scrollBar):
		showStatus = Option("show_status")
		if len(names) > rowsShown:
			scrollBar.SetMiddleBarSize(float(rowsShown) / float(len(names)))
			scrollBar.SetScrollStep(1.0 / float(len(names) - rowsShown))
			scrollBar.Show()
		else:
			scrollBar.Hide()
		startLine = max(0, min(startLine, max(0, len(names) - rowsShown)))
		for i, name in enumerate(names[startLine:startLine + rowsShown]):
			row = self.__Row(kind, name)
			row.SetPosition(14, top + 3 + i * ROW_STEP)
			row.Refresh(self.GetInfo(kind, name), showStatus)
			row.SetSelected(row is self.selected)
			row.Show()
			self.shownRows.append(row)

	def __OnScroll(self):
		names = self.__SortedNames(("friend", "block", "request")[self.listKind])
		lines = max(0, len(names) - FRIEND_LIST_ROWS)
		startLine = int(round(lines * max(0.0, min(1.0, self.friendScroll.GetPos()))))
		if startLine != self.startLine:
			self.startLine = startLine
			self.RefreshList()

	def __OnGuildScroll(self):
		names = self.__SortedNames("guild")
		lines = max(0, len(names) - GUILD_LIST_ROWS)
		startLine = int(round(lines * max(0.0, min(1.0, self.guildScroll.GetPos()))))
		if startLine != self.guildStartLine:
			self.guildStartLine = startLine
			self.RefreshList()

	def OnListWheel(self, delta):
		if self.view == VIEW_MESSENGER:
			scrollBar, kind, rowsShown = self.friendScroll, ("friend", "block", "request")[self.listKind], FRIEND_LIST_ROWS
		elif self.view == VIEW_GUILD:
			scrollBar, kind, rowsShown = self.guildScroll, "guild", GUILD_LIST_ROWS
		else:
			return
		count = len(self.__SortedNames(kind))
		if count <= rowsShown:
			return
		step = 1.0 / float(count - rowsShown)
		scrollBar.SetPos(scrollBar.GetPos() - step * (1 if delta > 0 else -1))

	def __RefreshHeader(self):
		self.myNameText.SetText(_MyName())
		guildName = ""
		if _GuildID():
			try:
				guildName = guild.GetGuildName()
			except Exception:
				guildName = ""
		self.guildNameText.SetText(_Fit(guildName, 100) if guildName else _T("NO_GUILD"))
		self.myStateIcon.LoadImage(STATE_IMAGE.get(self.myState, STATE_IMAGE[STATE_CONNECT]))
		if self.lover:
			name, lovePoint, online = self.lover
			self.familyText.SetPosition(48, 10)
			self.familyText.SetPackedFontColor(NAME_COLOR if online else OFFLINE_COLOR)
			self.familyText.SetText("%s: %s" % (_T("LOVER"), name))
			self.loverState.LoadImage(STATE_IMAGE[STATE_CONNECT if online else STATE_DISCONNECT])
			self.loverState.Show()
		else:
			self.loverState.Hide()
			self.familyText.SetPosition(34, 10)
			self.familyText.SetPackedFontColor(STATUS_COLOR)
			if self.myStatus:
				self.familyText.SetText(_Fit("%s: %s" % (_T("MY_STATUS"), self.myStatus), 225))
			else:
				self.familyText.SetText(_T("MY_STATUS_EMPTY"))

	def __RefreshTwinkle(self):
		if self.requests and not (self.view == VIEW_MESSENGER and self.listKind == LIST_REQUEST) and self.view == VIEW_MESSENGER:
			if int(app.GetTime() * 2) % 2 == 0:
				self.requestTwinkle.Show()
			else:
				self.requestTwinkle.Hide()
		else:
			self.requestTwinkle.Hide()

	def __RefreshGuildView(self):
		if _GuildID():
			self.guildNone.Hide()
			self.guildHas.Show()
			self.__SyncGuildData()
		else:
			self.guildHas.Hide()
			self.guildNone.Show()

	def __SyncGuildData(self):
		try:
			count = guild.GetMemberCount()
		except Exception:
			return
		for i in xrange(count):
			try:
				pid, name, grade, job, level, offer, general = guild.GetMemberData(i)
			except Exception:
				continue
			if pid < 0 or not name:
				continue
			info = self.guildMembers.get(name)
			if not info:
				info = FriendInfo(name)
				self.guildMembers[name] = info
			info.pid = pid
			info.level = level
			location = self.guildLocation.get(pid)
			if location and info.online:
				info.channel, info.mapIndex = location
			elif not info.online:
				info.channel, info.mapIndex = 0, 0

	def __AskGuildLocations(self):
		if not self.hasServer:
			return
		now = app.GetTime()
		if now < self.nextGuildAsk:
			return
		self.nextGuildAsk = now + 10.0
		if not _GuildID():
			return
		self.guildLocation = {}
		_Send("/community guild")

	# ------------------------------------------------------------------ messenger handler (the exe)
	def __Forward(self, name, *args):
		if self.oldMessenger:
			try:
				getattr(self.oldMessenger, name)(*args)
			except (ReferenceError, AttributeError):
				self.oldMessenger = None

	def OnLogin(self, groupIndex, key, name=None):
		self.__Forward("OnLogin", groupIndex, key, name)
		name = name or key
		if groupIndex == GROUP_FRIEND:
			info = self.__Friend(name)
			wasOnline = info.online
			info.online = True
			if info.state == STATE_DISCONNECT:
				info.state = STATE_CONNECT
			if not wasOnline and Option("friend_login") and self.__NoticesOn():
				_Chat(_T("FRIEND_LOGIN") % name)
		elif groupIndex == GROUP_GUILD:
			info = self.guildMembers.get(name)
			if not info:
				info = FriendInfo(name)
				self.guildMembers[name] = info
			wasOnline = info.online
			info.online = True
			info.state = STATE_CONNECT
			if not wasOnline and Option("guild_login") and self.__NoticesOn() and name != _MyName():
				_Chat(_T("GUILD_LOGIN") % name)
		self.RefreshList()

	def OnLogout(self, groupIndex, key, name=None):
		self.__Forward("OnLogout", groupIndex, key, name)
		name = name or key
		if groupIndex == GROUP_FRIEND:
			info = self.__Friend(name)
			info.online = False
			info.state = STATE_DISCONNECT
			info.channel = info.mapIndex = 0
		elif groupIndex == GROUP_GUILD:
			info = self.guildMembers.get(name)
			if not info:
				info = FriendInfo(name)
				self.guildMembers[name] = info
			info.online = False
			info.state = STATE_DISCONNECT
			info.channel = info.mapIndex = 0
		elif groupIndex == GROUP_BLOCK:
			self.blocks.add(name)
		self.RefreshList()

	def OnRemoveList(self, groupIndex, key):
		self.__Forward("OnRemoveList", groupIndex, key)
		if groupIndex == GROUP_FRIEND:
			self.friends.pop(key, None)
		elif groupIndex == GROUP_GUILD:
			self.guildMembers.pop(key, None)
		elif groupIndex == GROUP_BLOCK:
			self.blocks.discard(key)
		self.RefreshList()

	def OnRemoveAllList(self, groupIndex):
		self.__Forward("OnRemoveAllList", groupIndex)
		if groupIndex == GROUP_FRIEND:
			self.friends = {}
		elif groupIndex == GROUP_GUILD:
			self.guildMembers = {}
		elif groupIndex == GROUP_BLOCK:
			self.blocks = set()
		self.RefreshList()

	def __NoticesOn(self):
		return _state["since"] and app.GetTime() - _state["since"] > 10.0

	# the lover (game.py passes the marriage calls on too)
	def OnLover(self, action, name="", lovePoint=0):
		if action == "add":
			self.lover = (name, lovePoint, False)
		elif action == "point" and self.lover:
			self.lover = (self.lover[0], lovePoint, self.lover[2])
		elif action == "login" and self.lover:
			self.lover = (self.lover[0], self.lover[1], True)
		elif action == "logout" and self.lover:
			self.lover = (self.lover[0], self.lover[1], False)
		elif action == "clear":
			self.lover = None
		self.__RefreshHeader()

	def ClearGuildMember(self):
		self.guildMembers = {}
		self.guildLocation = {}
		self.RefreshList()

	def RefreshMessenger(self):
		self.RefreshList()

	# ------------------------------------------------------------------ server lines
	def OnServerCommand(self, command, args):
		self.hasServer = True
		if command == "community_my":
			self.myState = _Int(args[0] if len(args) > 0 else 0)
			self.myPrivacy = _Int(args[1] if len(args) > 1 else 0)
			self.myStatus = " ".join(args[2:])
			if self.view == VIEW_CONFIG:
				self.__LoadConfig()
		elif command == "community_friend":
			if len(args) < 6:
				return
			info = self.__Friend(args[0])
			info.state = _Int(args[1], STATE_DISCONNECT)
			info.level = _Int(args[2])
			info.conqueror = _Int(args[3])
			info.channel = _Int(args[4])
			info.mapIndex = _Int(args[5])
			info.status = " ".join(args[6:])
			info.online = info.state != STATE_DISCONNECT
		elif command == "community_guild":
			for item in args:
				parts = item.split(":")
				if len(parts) == 3:
					self.guildLocation[_Int(parts[0])] = (_Int(parts[1]), _Int(parts[2]))
			self.__SyncGuildData()
		elif command == "community_request":
			if len(args) < 5:
				return
			info = self.requests.get(args[0])
			if not info:
				info = FriendInfo(args[0])
				self.requests[args[0]] = info
			info.online = True
			info.state = STATE_CONNECT
			info.level = _Int(args[1])
			info.conqueror = _Int(args[2])
			info.channel = _Int(args[3])
			info.mapIndex = _Int(args[4])
		self.RefreshList()

	def AddFriendRequest(self, name):
		if name not in self.requests:
			info = FriendInfo(name)
			info.online = True
			info.state = STATE_CONNECT
			self.requests[name] = info
		_Chat(_T("REQUEST_CHAT") % name)
		self.RefreshList()

	def HasRequest(self, name):
		return name in self.requests

	def AnswerRequest(self, name, accept):
		if name not in self.requests:
			return
		del self.requests[name]
		_Send("/messenger_auth %s %s" % ("y" if accept else "n", name))
		# MT2009_PLUS_COMMUNITY_V1 (dialog): answered in the tab - game.py's question dialog of this name closes too
		_CloseRequestDialog(name)
		self.HideToolTip()
		self.RefreshList()

	# ------------------------------------------------------------------ my state / message
	def __OnDropButton(self):
		if self.stateDrop.IsShow():
			self.__CloseStateDrop()
		else:
			self.stateDrop.Show()
			self.stateDrop.SetTop()

	def __CloseStateDrop(self):
		if self.stateDrop:
			self.stateDrop.Hide()

	def OnSelectState(self, state):
		if not self.hasServer:
			return
		_Send("/community state %d" % state)

	def __OnStatusButton(self):
		self.__CloseDialogs()
		dialog = uiCommon.InputDialog()
		dialog.SetTitle(_T("STATUS_DIALOG"))
		dialog.SetMaxLength(STATUS_MAX_LEN)
		dialog.SetAcceptEvent(ui.__mem_func__(self.__OnStatusAccept))
		dialog.SetCancelEvent(ui.__mem_func__(self.__CloseDialogs))
		try:
			dialog.inputValue.SetText(self.myStatus)
		except Exception:
			pass
		dialog.Open()
		self.dialog = dialog

	def __OnStatusAccept(self):
		if not self.dialog:
			return True
		text = self.dialog.GetText().strip()
		self.__CloseDialogs()
		if self.hasServer:
			_Send(("/community status %s" % text).rstrip())
		return True

	# ------------------------------------------------------------------ list actions
	def OnSelectRow(self, row):
		if self.selected and self.selected is not row:
			try:
				self.selected.SetSelected(False)
			except ReferenceError:
				pass
		self.selected = row
		row.SetSelected(True)

	def OnDoubleClickRow(self, row):
		self.OnSelectRow(row)
		if row.kind in ("friend", "guild"):
			info = self.GetInfo(row.kind, row.name)
			if info and info.online:
				self.__Whisper(row.name)

	def __SelectedName(self, kinds):
		if self.selected and self.selected.kind in kinds:
			return self.selected.name
		return None

	def __Whisper(self, name):
		try:
			self.interface.OpenWhisperDialog(name)
		except Exception:
			pass

	def __OnWhisper(self):
		name = self.__SelectedName(("friend", "guild", "request"))
		if not name:
			_Chat(_T("SELECT_FIRST"))
			return
		self.__Whisper(name)

	def __OnAddFriend(self):
		self.__InputDialog(_T("ADD_FRIEND_DIALOG"), self.__OnAddFriendAccept)

	def __OnAddFriendAccept(self):
		text = self.dialog.GetText().strip() if self.dialog else ""
		self.__CloseDialogs()
		if text:
			net.SendMessengerAddByNamePacket(text)
		return True

	def __OnBlock(self):
		name = self.__SelectedName(("friend", "request"))
		self.__InputDialog(_T("BLOCK_DIALOG"), self.__OnBlockAccept, name)

	def __OnBlockAccept(self):
		text = self.dialog.GetText().strip() if self.dialog else ""
		self.__CloseDialogs()
		if text:
			net.SendMessengerBlockPacket(text)
		return True

	def __OnDelete(self):
		if self.listKind == LIST_FRIEND:
			name = self.__SelectedName(("friend",))
			if not name:
				_Chat(_T("SELECT_FIRST"))
				return
			self.__Question(_T("DELETE_QUESTION") % name, lambda n=name: self.__DeleteFriend(n))
		elif self.listKind == LIST_BLOCK:
			name = self.__SelectedName(("block",))
			if not name:
				_Chat(_T("SELECT_FIRST"))
				return
			self.AskUnblock(name)
		else:
			name = self.__SelectedName(("request",))
			if not name:
				_Chat(_T("SELECT_FIRST"))
				return
			self.AnswerRequest(name, False)

	def __DeleteFriend(self, name):
		self.__CloseDialogs()
		messenger.RemoveFriend(name)
		net.SendMessengerRemovePacket(name, name)
		self.friends.pop(name, None)
		self.selected = None
		self.RefreshList()

	def AskUnblock(self, name):
		self.__Question(_T("UNBLOCK_QUESTION") % name, lambda n=name: self.__Unblock(n))

	def __Unblock(self, name):
		self.__CloseDialogs()
		net.SendMessengerUnblockPacket(name)

	def __OnGuildAddFriend(self):
		name = self.__SelectedName(("guild",))
		if name:
			net.SendMessengerAddByNamePacket(name)
		else:
			self.__OnAddFriend()

	def __OnGuildBlock(self):
		name = self.__SelectedName(("guild",))
		self.__InputDialog(_T("BLOCK_DIALOG"), self.__OnBlockAccept, name)

	def __CanKick(self, name):
		try:
			for i in xrange(guild.ENEMY_GUILD_SLOT_MAX_COUNT):
				if guild.GetEnemyGuildName(i) != "":
					return False
			return bool(guild.MainPlayerHasAuthority(guild.AUTH_REMOVE_MEMBER)) and bool(guild.IsMemberByName(name))
		except Exception:
			return False

	def __OnGuildKick(self):
		name = self.__SelectedName(("guild",))
		if not name:
			_Chat(_T("SELECT_FIRST"))
			return
		if not self.__CanKick(name):
			return
		self.__Question(_T("KICK_QUESTION") % name, lambda n=name: self.__Kick(n))

	def __Kick(self, name):
		self.__CloseDialogs()
		net.SendGuildRemoveMemberPacket(name)

	def __OnGuildInfo(self):
		try:
			self.interface.ToggleGuildWindow()
		except Exception:
			pass

	def __InputDialog(self, title, event, text=None):
		self.__CloseDialogs()
		dialog = uiCommon.InputDialog()
		dialog.SetTitle(title)
		dialog.SetMaxLength(24)
		dialog.SetAcceptEvent(ui.__mem_func__(event))
		dialog.SetCancelEvent(ui.__mem_func__(self.__CloseDialogs))
		if text:
			try:
				dialog.inputValue.SetText(text)
			except Exception:
				pass
		dialog.Open()
		self.dialog = dialog

	def __Question(self, text, event):
		self.__CloseDialogs()
		question = uiCommon.QuestionDialog()
		question.SetText(text)
		question.SetAcceptEvent(event)
		question.SetCancelEvent(ui.__mem_func__(self.__CloseDialogs))
		question.Open()
		self.question = question

	def __CloseDialogs(self):
		if self.dialog:
			dialog, self.dialog = self.dialog, None
			dialog.Close()
		if self.question:
			question, self.question = self.question, None
			question.Close()
		return True

	# ------------------------------------------------------------------ settings
	def __LoadConfig(self):
		options = Settings()["options"]
		self.pendingOptions = dict(options)
		for key, textKey, flag in PRIVACY_OPTIONS:
			self.pendingOptions[key] = bool(self.myPrivacy & flag)
		self.__ShowConfig()

	def __ShowConfig(self):
		for key, row in self.optionRows.items():
			row.SetChecked(bool(self.pendingOptions.get(key, False)))

	def ToggleOption(self, key):
		if self.pendingOptions is None:
			self.__LoadConfig()
		self.pendingOptions[key] = not self.pendingOptions.get(key, False)
		self.__ShowConfig()

	def __OnSaveConfig(self):
		if self.pendingOptions is None:
			return
		settings = Settings()["options"]
		for key, textKey, default in OPTIONS:
			settings[key] = bool(self.pendingOptions.get(key, default))
		SaveSettings()
		privacy = 0
		for key, textKey, flag in PRIVACY_OPTIONS:
			if self.pendingOptions.get(key):
				privacy |= flag
		if self.hasServer and privacy != self.myPrivacy:
			_Send("/community privacy %d" % privacy)
		_Chat(_T("SAVED"))
		self.RefreshList()

	def __OnDefaultConfig(self):
		self.pendingOptions = dict((key, default) for key, textKey, default in OPTIONS)
		for key, textKey, flag in PRIVACY_OPTIONS:
			self.pendingOptions[key] = False
		self.__ShowConfig()

	# ------------------------------------------------------------------ window
	def Open(self):
		self.RefreshList()
		self.SetTop()
		self.Show()
		if self.view == VIEW_GUILD:
			self.__RefreshGuildView()
			self.__AskGuildLocations()

	def Close(self):
		self.__CloseStateDrop()
		self.__CloseDialogs()
		self.Hide()

	def Toggle(self):
		if self.IsShow():
			self.Close()
		else:
			self.Open()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def OnUpdate(self):
		self.__RefreshTwinkle()
		if self.view == VIEW_GUILD and self.hasServer and app.GetTime() >= self.nextGuildAsk:
			self.__AskGuildLocations()


# ---------------------------------------------------------------------- module
def Create(interface):
	window = CommunityWindow(interface)
	_state["window"] = window
	_state["hello"] = False
	_state["auto"] = None
	return window


def GetWindow():
	window = _state["window"]
	if window is None:
		return None
	try:
		window.IsShow()
	except ReferenceError:
		_state["window"] = None
		return None
	return window


def Destroy():
	window = _state["window"]
	_state["window"] = None
	_state["hello"] = False
	if window:
		try:
			window.Destroy()
		except ReferenceError:
			pass


def OnServerCommand(command, *args):
	window = GetWindow()
	if window:
		window.OnServerCommand(command, args)


def OnFriendRequest(name):
	"""game.py OnMessengerAddFriendQuestion: True when the window took the request."""
	window = GetWindow()
	if not window:
		return False
	window.AddFriendRequest(name)
	return True


# MT2009_PLUS_COMMUNITY_V1 (dialog): a friend request also opens the classic question dialog (game.py
# OnMessengerAddFriendQuestion, as the old messenger did); an answer in either place removes the other.
def SetRequestDialogCloser(closer):
	"""game.py: closer(name) closes its question dialog when it is open for that name."""
	_state["dialog_closer"] = closer


def _CloseRequestDialog(name):
	closer = _state.get("dialog_closer")
	if not closer:
		return
	try:
		closer(name)
	except Exception:
		_state["dialog_closer"] = None


def AnswerFromDialog(name, accept):
	"""game.py's question dialog answered: the request tab loses the entry; the server gets the answer once."""
	window = GetWindow()
	if window and window.HasRequest(name):
		window.AnswerRequest(name, accept)
		return
	_Send("/messenger_auth %s %s" % ("y" if accept else "n", name))


def OnLover(action, name="", lovePoint=0):
	window = GetWindow()
	if window:
		window.OnLover(action, name, lovePoint)


def _AutoHuntOn():
	try:
		import uiautohunt
		hunter = getattr(uiautohunt, "_hunter", None)
		return bool(hunter and getattr(hunter, "running", False))
	except Exception:
		return False


class Keeper(object):
	"""game.py's updatable: "/community hello" once the character is in the game, Auto \xa3owy on / off."""

	def CanUpdate(self):
		return True

	def OnUpdate(self):
		now = app.GetTime()
		if now < _state["next"]:
			return
		_state["next"] = now + 1.0
		if not GetWindow():
			return
		if not _state["hello"]:
			if _Send("/community hello"):
				_state["hello"] = True
				_state["since"] = now
			return
		auto = _AutoHuntOn()
		if auto != _state["auto"]:
			_state["auto"] = auto
			_Send("/community auto %d" % (1 if auto else 0))

	def Destroy(self):
		_state["hello"] = False
		_state["auto"] = None
		_state["next"] = 0.0


def GetKeeper():
	return Keeper()
