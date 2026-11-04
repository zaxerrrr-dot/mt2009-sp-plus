# MT2009_PLUS_TITLES_V1: Tytuly - the title window (server-patches/tytuly/README.md; the owner's package "Official Title
# System Renewal", its window rebuilt for our client). Opened by the portrait button of the character window
# (uicharacter.py, CreateFaceButton). Left the titles of the server's catalogue (owned: the hourglass / the infinity,
# not owned: the padlock; the worn one in its own colour), under it the worn title and "Zaloz" / "Zdejmij"; right the
# preview: the title's plate with its name and its animated banner (pictures of title_<res>.sub), or its effect drawn by
# the exe into a render target (titleSystem.PreviewSelect / PreviewShow), and how the title is got / its time.
#
# Exe (Mt2009Titles.cpp, app.MT2009_TITLES_EXE): module titleSystem - the catalogue, the owned titles and the worn one
# come from the server after the client's hello; the notices (got, worn, expired ...) come here as chat lines also while
# the window is closed (the handler is installed with the portrait button). Without that exe: no button, no window.
import app
import chat
import ui
import uiToolTip
import wndMgr

try:
	import titleSystem
except ImportError:
	titleSystem = None

ROOT = "d:/ymir work/ui/game/title/window/"
FACE = "d:/ymir work/ui/game/title/"

ROWS = 9				# rows shown at once
ROW_X = 4
ROW_Y = 24
ROW_H = 23
PREVIEW_W = 224
PREVIEW_H = 346
PLATE_Y = 150			# the plate's centre in the preview
COLOR_NAME = 0xffd6e3f3
COLOR_LOCKED = 0xff8a8a8a
COLOR_EQUIPPED = 0xfff2e7c1
COLOR_INFO = 0xffc8c8c8

TEXT_WINDOW = "Tytu\xb3y"
TEXT_LIST = "Lista tytu\xb3\xf3w"
TEXT_CURRENT = "Za\xb3o\xbfony tytu\xb3"
TEXT_NONE = "brak"
TEXT_APPLY = "Za\xb3\xf3\xbf"
TEXT_CLEAR = "Zdejmij"
TEXT_BACK = "Poka\xbf za\xb3o\xbfony tytu\xb3"
TEXT_BUTTON_TIP = "Tytu\xb3y"
TEXT_PERMANENT = "Na sta\xb3e"
TEXT_LEFT = "Pozosta\xb3o: %s"
TEXT_LOCKED = "Nie posiadasz tego tytu\xb3u."
TEXT_DURATION = "Czas: %s"
TEXT_HOW = "Jak zdoby\xe6:"
TEXT_EFFECT_KIND = "Efekt nad g\xb3ow\xb9 postaci."
TEXT_WAIT = "Wczytywanie tytu\xb3\xf3w..."
TEXT_OLD_SERVER = "Serwer nie przys\xb3a\xb3 listy tytu\xb3\xf3w."

# titleSystem notices (server playerbot_titles.cpp EMessage)
MESSAGES = {
	0: "Masz ju\xbf ten tytu\xb3.",
	1: "Nie mo\xbfesz za\xb3o\xbfy\xe6 tego tytu\xb3u.",
	2: "Ten certyfikat nie nadaje \xbfadnego tytu\xb3u.",
	3: "Czas tytu\xb3u %s min\xb9\xb3.",
	4: "Otrzymujesz tytu\xb3 %s. Za\xb3\xf3\xbf go w oknie tytu\xb3\xf3w (portret w oknie postaci).",
	5: "Za\xb3o\xbfono tytu\xb3 %s.",
	6: "Zdj\xeato tytu\xb3 %s.",
	7: "Tytu\xb3 %s wyga\x9cnie za nieca\xb3\xb9 godzin\xea.",
	8: "Spr\xf3buj ponownie za chwil\xea.",
	9: "Przed\xb3u\xbfono tytu\xb3 %s.",
	10: "Utracono tytu\xb3 %s.",
}

_state = {"window": None, "notifier": None}


def IsSupported():
	return titleSystem is not None and bool(getattr(app, "MT2009_TITLES_EXE", 0))


def _Titles():
	"""{title: (title, type, name, condition, permanent, duration, resource, color)}, [titles in order]"""
	rows = titleSystem.GetTitles()
	return dict((r[0], r) for r in rows), [r[0] for r in rows]


def _Name(title):
	for r in titleSystem.GetTitles():
		if r[0] == title:
			return r[2]
	return "#%d" % title


def _Span(seconds):
	seconds = max(0, int(seconds))
	days, rest = divmod(seconds, 86400)
	hours, rest = divmod(rest, 3600)
	minutes = rest / 60
	if days:
		return "%d d %d godz." % (days, hours)
	if hours:
		return "%d godz. %d min" % (hours, minutes)
	return "%d min" % max(1, minutes)


def _Now():
	try:
		return app.GetGlobalTimeStamp()
	except Exception:
		return 0


def _Wrap(text, width=36):
	words, lines, line = text.split(), [], ""
	for w in words:
		if line and len(line) + 1 + len(w) > width:
			lines.append(line)
			line = w
		else:
			line = (line + " " + w) if line else w
	if line:
		lines.append(line)
	return lines


class _Notifier(object):
	"""titleSystem's handler for the whole game: the notices as chat lines, a refresh to the open window."""

	def OnTitleNotify(self, message, title):
		text = MESSAGES.get(message)
		if not text:
			return
		if "%s" in text:
			text = text % _Name(title)
		chat.AppendChat(chat.CHAT_TYPE_INFO, text)
		wnd = _state["window"]
		if wnd:
			wnd.Refresh()

	def OnTitleRefresh(self):
		wnd = _state["window"]
		if wnd:
			wnd.Refresh()


def InstallHandler():
	if not IsSupported():
		return
	if not _state["notifier"]:
		_state["notifier"] = _Notifier()
	titleSystem.SetHandler(_state["notifier"])


def CreateFaceButton(faceSlot):
	"""The character window's portrait as the title window's button (GF's char_face_button over the face slot, its
	pencil at the corner) - None with an older exe. faceSlot: the window's "Face_Slot" picture (the button's parent)."""
	if not IsSupported() or not faceSlot:
		return None
	InstallHandler()
	button = ui.Button()
	button.SetParent(faceSlot)
	button.SetUpVisual(FACE + "char_face_button_default.sub")
	button.SetOverVisual(FACE + "char_face_button_over.sub")
	button.SetDownVisual(FACE + "char_face_button_down.sub")
	button.SetPosition(3, 3)
	button.SetToolTipText(TEXT_BUTTON_TIP)
	button.SetEvent(ToggleWindow)
	button.Show()
	write = ui.ImageBox()
	write.SetParent(button)
	write.LoadImage(FACE + "char_face_write_default.sub")
	write.SetPosition(33, 34)
	write.AddFlag("not_pick")
	write.Show()
	button.writeImage = write
	return button


def ToggleWindow():
	if not IsSupported():
		return
	wnd = _state["window"]
	if wnd and wnd.IsShow():
		wnd.Close()
		return
	if not wnd:
		wnd = CharacterTitleWindow()
		_state["window"] = wnd
	wnd.Open()


def DestroyWindow():
	wnd = _state["window"]
	_state["window"] = None
	if wnd:
		wnd.Destroy()


class _PreviewTarget(ui.Window):
	def RegisterWindow(self, layer):
		self.hWnd = wndMgr.RegisterRenderTarget(self, layer)


class CharacterTitleWindow(ui.ScriptWindow):

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.rows = []
		self.titles = {}
		self.order = []
		self.owned = {}
		self.equipped = 0
		self.selected = 0
		self.scroll = 0
		self.tooltip = None
		self.preview = {}
		self.infoLines = []
		self.__Load()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __Load(self):
		try:
			ui.PythonScriptLoader().LoadScriptFile(self, "UIScript/CharacterTitleWindow.py")
			self.GetChild("main_title_bar").SetCloseEvent(ui.__mem_func__(self.Close))
			self.GetChild("title_name").SetText(TEXT_WINDOW)
			self.GetChild("list_text").SetText(TEXT_LIST)
			self.GetChild("current_text").SetText(TEXT_CURRENT)
			self.listBoard = self.GetChild("list_board")
			self.rightBoard = self.GetChild("right_board")
			self.scrollBar = self.GetChild("scroll_bar")
			self.equippedName = self.GetChild("equipped_name")
			self.applyButton = self.GetChild("apply_button")
			self.clearButton = self.GetChild("clear_button")
			self.backButton = self.GetChild("back_button")
		except Exception:
			import exception
			exception.Abort("CharacterTitleWindow.__Load")
			return
		self.applyButton.SetText(TEXT_APPLY)
		self.clearButton.SetText(TEXT_CLEAR)
		self.applyButton.SetEvent(ui.__mem_func__(self.__OnApply))
		self.clearButton.SetEvent(ui.__mem_func__(self.__OnClear))
		self.backButton.SetEvent(ui.__mem_func__(self.__OnBack))
		self.backButton.SetToolTipText(TEXT_BACK)
		self.scrollBar.SetScrollEvent(ui.__mem_func__(self.__OnScroll))
		if hasattr(self.scrollBar, "SAFE_SetOnWheelEvent") and hasattr(self.scrollBar, "OnMouseWheel"):
			self.scrollBar.SAFE_SetOnWheelEvent(self.listBoard)
		self.tooltip = uiToolTip.ToolTip()
		self.tooltip.HideToolTip()
		for i in xrange(ROWS):
			self.rows.append(self.__MakeRow(i))
		self.__MakePreview()
		self.SetCenterPosition()

	def __MakeRow(self, i):
		button = ui.Button()
		button.SetParent(self.listBoard)
		button.SetPosition(ROW_X, ROW_Y + i * ROW_H)
		button.SetUpVisual(ROOT + "list_button_default.sub")
		button.SetOverVisual(ROOT + "list_button_over.sub")
		button.SetDownVisual(ROOT + "list_button_down.sub")
		button.SetEvent(ui.__mem_func__(self.__OnRow), i)
		button.SAFE_SetStringEvent("MOUSE_OVER_IN", self.__OnRowIn, i)
		button.SAFE_SetStringEvent("MOUSE_OVER_OUT", self.__OnRowOut, i)
		if hasattr(self.scrollBar, "SAFE_SetOnWheelEvent") and hasattr(self.scrollBar, "OnMouseWheel"):
			self.scrollBar.SAFE_SetOnWheelEvent(button)
		name = ui.TextLine()
		name.SetParent(button)
		name.SetPosition(8, 5)
		name.AddFlag("not_pick")
		name.Show()
		state = ui.ImageBox()
		state.SetParent(button)
		state.SetPosition(181, 4)
		state.AddFlag("not_pick")
		state.Show()
		button.Hide()
		return {"button": button, "name": name, "state": state, "title": 0, "visual": None}

	def __MakePreview(self):
		p = self.preview
		target = None
		if titleSystem.RENDER_TARGET_INDEX >= 0 and hasattr(wndMgr, "RegisterRenderTarget"):
			target = _PreviewTarget()
			target.SetParent(self.rightBoard)
			target.SetPosition(1, 0)
			target.SetSize(PREVIEW_W, PREVIEW_H)
			target.AddFlag("not_pick")
			wndMgr.SetRenderTarget(target.hWnd, titleSystem.RENDER_TARGET_INDEX)
			target.Hide()
		p["target"] = target
		sprite = ui.AniImageBox()
		sprite.SetParent(self.rightBoard)
		sprite.AddFlag("not_pick")
		sprite.Hide()
		p["sprite"] = sprite
		for part in ("left", "middle", "right"):
			img = ui.ExpandedImageBox()
			img.SetParent(self.rightBoard)
			img.AddFlag("not_pick")
			img.Hide()
			p[part] = img
		name = ui.TextLine()
		name.SetParent(self.rightBoard)
		name.SetHorizontalAlignCenter()
		name.AddFlag("not_pick")
		name.SetOutline()
		name.Hide()
		p["name"] = name
		header = ui.TextLine()
		header.SetParent(self.rightBoard)
		header.SetPosition(PREVIEW_W / 2 + 1, 14)
		header.SetHorizontalAlignCenter()
		header.SetOutline()
		header.AddFlag("not_pick")
		header.Show()
		p["header"] = header
		for i in xrange(7):
			line = ui.TextLine()
			line.SetParent(self.rightBoard)
			line.SetPosition(PREVIEW_W / 2 + 1, 246 + i * 14)
			line.SetHorizontalAlignCenter()
			line.SetOutline()
			line.AddFlag("not_pick")
			line.Hide()
			self.infoLines.append(line)

	def Destroy(self):
		if IsSupported():
			titleSystem.PreviewShow(0)
		if self.tooltip:
			self.tooltip.HideToolTip()
		self.tooltip = None
		self.rows = []
		self.preview = {}
		self.infoLines = []
		self.ClearDictionary()

	def Open(self):
		InstallHandler()
		titleSystem.RequestOpen()
		self.Refresh()
		if self.equipped and not self.selected:
			self.selected = self.equipped
		self.__RefreshPreview()
		self.Show()
		self.SetTop()

	def Close(self):
		titleSystem.PreviewShow(0)
		if self.tooltip:
			self.tooltip.HideToolTip()
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	# ------------------------------------------------------------------------------------------------- data

	def Refresh(self):
		if not self.rows:
			return
		self.titles, self.order = _Titles()
		self.owned = dict(titleSystem.GetOwned())
		self.equipped = titleSystem.GetEquipped()
		if self.selected not in self.titles:
			self.selected = self.equipped if self.equipped in self.titles else (self.order[0] if self.order else 0)
		count = len(self.order)
		if count > ROWS:
			self.scrollBar.SetMiddleBarSize(float(ROWS) / float(count))
			self.scrollBar.Show()
		else:
			self.scrollBar.Hide()
		self.scroll = min(self.scroll, max(0, count - ROWS))
		self.__RefreshRows()
		self.__RefreshCurrent()
		if self.IsShow():
			self.__RefreshPreview()

	def __IsOwned(self, title):
		if title not in self.owned:
			return False
		end = self.owned[title]
		return end == 0 or end > _Now()

	def __RefreshRows(self):
		for i, row in enumerate(self.rows):
			index = self.scroll + i
			if index >= len(self.order):
				row["title"] = 0
				row["button"].Hide()
				continue
			title = self.order[index]
			t = self.titles[title]
			owned = self.__IsOwned(title)
			row["title"] = title
			if title == self.selected:
				visual = "list_button_down.sub"
			elif title == self.equipped:
				visual = "list_button_default_equipped.sub"
			elif owned:
				visual = "list_button_default.sub"
			else:
				visual = "list_button_default_disable.sub"
			if row["visual"] != visual:
				row["button"].SetUpVisual(ROOT + visual)
				row["visual"] = visual
			row["name"].SetText(t[2])
			row["name"].SetPackedFontColor(COLOR_EQUIPPED if title == self.equipped else (COLOR_NAME if owned else COLOR_LOCKED))
			if not owned:
				row["state"].LoadImage(ROOT + "state_locked.sub")
			elif self.owned.get(title, 0) == 0:
				row["state"].LoadImage(ROOT + "state_infinite.sub")
			else:
				row["state"].LoadImage(ROOT + "state_hourglass.sub")
			row["button"].Show()
		if not self.order:
			self.GetChild("list_text").SetText(TEXT_WAIT if not titleSystem.IsDataReceived() else TEXT_OLD_SERVER)
		else:
			self.GetChild("list_text").SetText(TEXT_LIST)

	def __RefreshCurrent(self):
		t = self.titles.get(self.equipped)
		self.equippedName.SetText(t[2] if t else TEXT_NONE)
		if self.selected and self.__IsOwned(self.selected) and self.selected != self.equipped:
			self.applyButton.Enable()
		else:
			self.applyButton.Disable()
		if self.equipped:
			self.clearButton.Enable()
		else:
			self.clearButton.Disable()

	# ---------------------------------------------------------------------------------------------- preview

	def __HidePreview(self):
		p = self.preview
		for key in ("sprite", "left", "middle", "right", "name"):
			p[key].Hide()
		if p["target"]:
			p["target"].Hide()
		titleSystem.PreviewShow(0)
		for line in self.infoLines:
			line.Hide()

	def __RefreshPreview(self):
		if not self.preview:
			return
		self.__HidePreview()
		p = self.preview
		t = self.titles.get(self.selected)
		if not t:
			p["header"].SetText("")
			return
		title, kind, name, condition, permanent, duration, resource, color = t
		p["header"].SetText(name)
		p["header"].SetPackedFontColor(COLOR_EQUIPPED if title == self.equipped else COLOR_NAME)
		if kind == titleSystem.TYPE_EFFECT:
			if p["target"] and titleSystem.PreviewSelect(title):
				p["target"].Show()
				titleSystem.PreviewShow(1)
		else:
			self.__ShowPlate(name, resource, color, kind == titleSystem.TYPE_NAMEPLATE)
		lines = []
		if self.__IsOwned(title):
			end = self.owned.get(title, 0)
			lines.append(TEXT_PERMANENT if end == 0 else TEXT_LEFT % _Span(end - _Now()))
		else:
			lines.append(TEXT_LOCKED)
			if not permanent and duration:
				lines.append(TEXT_DURATION % _Span(duration))
		if kind == titleSystem.TYPE_EFFECT:
			lines.append(TEXT_EFFECT_KIND)
		if condition:
			lines.append(TEXT_HOW)
			lines.extend(_Wrap(condition))
		for i, line in enumerate(self.infoLines):
			if i < len(lines):
				line.SetText(lines[i])
				line.SetPackedFontColor(COLOR_INFO)
				line.Show()

	def __ShowPlate(self, name, resource, color, plate):
		p = self.preview
		label = p["name"]
		label.SetText(name)
		label.SetPackedFontColor(color or COLOR_NAME)
		(textW, textH) = label.GetTextSize()
		label.SetPosition(PREVIEW_W / 2 + 1, PLATE_Y - textH / 2 - 1)
		label.Show()
		parts = titleSystem.GetPlate(resource) if plate else ()
		if not parts:
			return
		left, middle, right, sprites, count, spriteW, spriteH = parts
		p["left"].LoadImage(left)
		p["middle"].LoadImage(middle)
		p["right"].LoadImage(right)
		lw, h = p["left"].GetWidth(), p["left"].GetHeight()
		mw = max(1, p["middle"].GetWidth())
		top = PLATE_Y - h / 2
		x0 = PREVIEW_W / 2 + 1 - textW / 2
		p["left"].SetPosition(x0 - lw, top)
		p["middle"].SetPosition(x0, top)
		p["middle"].SetScale(float(textW) / float(mw), 1.0)
		p["right"].SetPosition(x0 + textW, top)
		if sprites and count > 0:
			sprite = ui.AniImageBox()
			sprite.SetParent(self.rightBoard)
			sprite.AddFlag("not_pick")
			for i in xrange(count):
				sprite.AppendImage("%s%02d.sub" % (sprites, i))
			sprite.SetDelay(10)
			sw = spriteW or 208
			sh = spriteH or 128
			sprite.SetPosition(PREVIEW_W / 2 + 1 - sw / 2, top + h - sh - 3)
			sprite.Show()
			p["sprite"] = sprite
		for key in ("left", "middle", "right"):
			p[key].Show()
		# the plate over the banner, the name over the plate
		for key in ("left", "middle", "right"):
			p[key].SetTop()
		label.SetTop()

	# ----------------------------------------------------------------------------------------------- events

	def __OnScroll(self):
		count = len(self.order)
		self.scroll = int(round(self.scrollBar.GetPos() * max(0, count - ROWS)))
		self.__RefreshRows()

	def __OnRow(self, i):
		title = self.rows[i]["title"]
		if not title:
			return
		self.selected = title
		self.__RefreshRows()
		self.__RefreshCurrent()
		self.__RefreshPreview()

	def __OnRowIn(self, i):
		title = self.rows[i]["title"] if i < len(self.rows) else 0
		t = self.titles.get(title)
		if not t or not self.tooltip:
			return
		tip = self.tooltip
		tip.ClearToolTip()
		tip.SetTitle(t[2])
		if t[3]:
			tip.AppendSpace(4)
			for line in _Wrap(t[3], 40):
				tip.AppendTextLine(line, COLOR_INFO)
		tip.AppendSpace(4)
		if self.__IsOwned(title):
			end = self.owned.get(title, 0)
			tip.AppendTextLine(TEXT_PERMANENT if end == 0 else TEXT_LEFT % _Span(end - _Now()), COLOR_NAME)
		else:
			tip.AppendTextLine(TEXT_LOCKED, COLOR_LOCKED)
		tip.ShowToolTip()

	def __OnRowOut(self, i):
		if self.tooltip:
			self.tooltip.HideToolTip()

	def __OnApply(self):
		if self.selected and self.__IsOwned(self.selected):
			titleSystem.RequestEquip(self.selected)

	def __OnClear(self):
		if self.equipped:
			titleSystem.RequestEquip(0)

	def __OnBack(self):
		if self.equipped:
			self.selected = self.equipped
			if self.selected in self.order:
				pos = self.order.index(self.selected)
				if pos < self.scroll or pos >= self.scroll + ROWS:
					self.scroll = max(0, min(pos, len(self.order) - ROWS))
					count = len(self.order)
					if count > ROWS:
						self.scrollBar.SetPos(float(self.scroll) / float(count - ROWS))
			self.__RefreshRows()
			self.__RefreshCurrent()
			self.__RefreshPreview()
