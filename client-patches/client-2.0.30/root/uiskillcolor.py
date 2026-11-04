# MT2009_PLUS_SKILL_COLOR_V1: Kolor umiejetnosci - the colour window (server-patches/skillcolor/README.md; the owner's
# package "SKILL_COLOR_SYSTEM by OSWAP (FULL)", its window rebuilt for our skill window). Opened by the "Kolory" button
# of the skill tab (uicharacter.py). Left the character's skills that take a colour: both paths of its class (the
# other one while the skill hack's second tab is on, skillhack.py), the 9th skills, the horse skills 137-140 and the
# Buffi's 164-167 (uibuffi.py; they colour the Buffi's buffs and its cast) - riposty / dopalacze are passive, no effect
# to colour. Right the effect's five layers (layer n = the effect's n-th particle system, the 5th also every later
# one), the picker (skillcolorpick.py: the colour is computed from the click, the picture is painted by the client
# build's tool from the same function) and the code "#RRGGBB".
#
# The package's rules: a skill is coloured from its P (the server checks it too); "Domyslne" gives the effect its own
# colours back. Its colour presets saved in config.cfg (minIni in the exe) are left out.
#
# Exe: player.SetSkillColor(vnum, c1..c5) / player.GetSkillColor(vnum) - -1 the effect's own, else 0xRRGGBB
# (Mt2009SkillColor.cpp); without them (an older exe) the skill tab has no button.
import app
import chat
import chr
import net
import player
import skill
import wndMgr

import ui
import skillcolorpick
import skillhack

LAYERS = 5
HORSE_SKILLS = (137, 138, 139, 140)
GRADE_P = 3			# player.GetSkillGrade: 0 normal, 1 M, 2 G, 3 P
LEVEL_P = 40		# uibuffi.Level: the raw level

COLOR_OK = 0xffe8e8e8
COLOR_LOCKED = 0xff8a8a8a

TEXT_SUFFIX_P = " (od P)"
TEXT_SUFFIX_HORSE = " (nieznana)"
TEXT_SUFFIX_BUFFI = " (Buffi)"
TEXT_HINT_PICK = "Wybierz warstw\xea i kliknij kolor (lub wpisz kod)."
TEXT_HINT_P = "Kolor ustawisz od poziomu P tej umiej\xeatno\x9cci."
TEXT_HINT_HORSE = "Najpierw naucz si\xea tej umiej\xeatno\x9cci konnej."
TEXT_HINT_NONE = "Brak umiej\xeatno\x9cci, kt\xf3re mo\xbfna pokolorowa\xe6."
TEXT_SAVED = "Kolor umiej\xeatno\x9cci %s zosta\xb3 zapisany."
TEXT_RESET = "Przywr\xf3cono domy\x9clny kolor umiej\xeatno\x9cci %s."
TEXT_BAD_HEX = "Nieprawid\xb3owy kod koloru (np. #FF8800)."
TEXT_DARK = "Ten kolor jest za ciemny - efekt by\xb3by niewidoczny."
TEXT_LOCKED = "Tej umiej\xeatno\x9cci nie mo\xbfna jeszcze pokolorowa\xe6."
TEXT_BUTTON = "Kolory"
TEXT_BUTTON_TIP = "Kolor efekt\xf3w umiej\xeatno\x9cci"

_state = {"window": None}


def IsSupported():
	"""The exe can do it (an older exe: no button, no window)."""
	return bool(getattr(app, "ENABLE_SKILL_COLOR_SYSTEM", 0)) and hasattr(player, "SetSkillColor") and hasattr(player, "GetSkillColor")


def _SkillName(vnum):
	try:
		name = skill.GetSkillName(vnum)
	except Exception:
		name = ""
	return name or ("#%d" % vnum)


def _ClassLevelOk(vnum):
	slot = player.GetSkillSlotIndex(vnum)
	if not slot:
		return False
	return player.GetSkillGrade(slot) >= GRADE_P


def _HorseLearned(vnum):
	slot = player.GetSkillSlotIndex(vnum)
	if not slot:
		return False
	return player.GetSkillLevel(slot) > 0


def Entries():
	"""[(vnum, name, ok, hint)] of the character's skills that take a colour, in the skill window's order."""
	out = []
	try:
		job = chr.RaceToJob(net.GetMainActorRace())
		group = net.GetMainActorSkillGroup()
	except Exception:
		return out
	seen = set()

	def add(vnum, name, ok, hint):
		if vnum and vnum not in seen:
			seen.add(vnum)
			out.append((vnum, name, ok, hint))

	paths = skillhack.PATHS.get(job, {})
	if group in paths:
		skills, ninth = paths[group]
		for vnum in tuple(skills) + (ninth,):
			if vnum and player.GetSkillSlotIndex(vnum):
				add(vnum, _SkillName(vnum), _ClassLevelOk(vnum), TEXT_HINT_P)
		otherSkills, otherNinth = skillhack.OtherSkills()
		for vnum in tuple(otherSkills) + (otherNinth,):
			if vnum and player.GetSkillSlotIndex(vnum):
				add(vnum, _SkillName(vnum), _ClassLevelOk(vnum), TEXT_HINT_P)
	for vnum in HORSE_SKILLS:
		if player.GetSkillSlotIndex(vnum):
			add(vnum, _SkillName(vnum), _HorseLearned(vnum), TEXT_HINT_HORSE)
	try:
		import uibuffi
		for vnum, shaman, name in uibuffi.SKILLS:
			level = uibuffi.Level(vnum)
			if level > 0:
				add(vnum, name + TEXT_SUFFIX_BUFFI, level >= LEVEL_P, TEXT_HINT_P)
	except Exception:
		pass
	return out


def _GrpColor(value):
	r, g, b = skillcolorpick.ToRGB(value) if value >= 0 else skillcolorpick.DEFAULT_SHOWN
	return 0xff000000 | (r << 16) | (g << 8) | b


class SkillColorWindow(ui.ScriptWindow):

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.entries = []
		self.vnum = 0
		self.ok = False
		self.colors = [-1] * LAYERS
		self.layer = 0
		self.allLayers = False
		self.isLoaded = False

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __Load(self):
		if self.isLoaded:
			return
		self.isLoaded = True
		try:
			ui.PythonScriptLoader().LoadScriptFile(self, "UIScript/SkillColorWindow.py")
		except:
			import exception
			exception.Abort("SkillColorWindow.__Load.LoadScriptFile")
		try:
			get = self.GetChild
			get("Board").SetCloseEvent(ui.__mem_func__(self.Close))
			self.skillList = get("SkillList")
			self.skillScroll = get("SkillScroll")
			self.layerButtons = [get("Layer%d" % i) for i in xrange(LAYERS)]
			self.layerBars = [get("LayerColor%d" % i) for i in xrange(LAYERS)]
			self.allButton = get("AllLayers")
			self.offButton = get("LayerOff")
			self.picker = get("Picker")
			self.dot = get("PickerDot")
			self.hexEdit = get("HexEdit")
			self.hint = get("Hint")
			hexApply = get("HexApply")
			applyButton = get("ApplyButton")
			defaultButton = get("DefaultButton")
			closeButton = get("CloseButton")
		except:
			import exception
			exception.Abort("SkillColorWindow.__Load.BindObject")

		self.skillList.SetEvent(ui.__mem_func__(self.__OnSelectSkill))
		self.skillScroll.SetScrollEvent(ui.__mem_func__(self.__OnScroll))
		for i in xrange(LAYERS):
			self.layerButtons[i].SetEvent(ui.__mem_func__(self.__OnSelectLayer), i)
		self.allButton.SetToggleDownEvent(ui.__mem_func__(self.__OnAllLayers), True)
		self.allButton.SetToggleUpEvent(ui.__mem_func__(self.__OnAllLayers), False)
		self.offButton.SetEvent(ui.__mem_func__(self.__OnLayerOff))
		self.picker.SetEvent(ui.__mem_func__(self.__OnPick))
		self.dot.AddFlag("not_pick")
		self.dot.Hide()
		self.hexEdit.SetReturnEvent(ui.__mem_func__(self.__OnHexApply))
		self.hexEdit.SetEscapeEvent(ui.__mem_func__(self.Close))
		hexApply.SetEvent(ui.__mem_func__(self.__OnHexApply))
		applyButton.SetEvent(ui.__mem_func__(self.__OnApply))
		defaultButton.SetEvent(ui.__mem_func__(self.__OnDefault))
		closeButton.SetEvent(ui.__mem_func__(self.Close))

	def Destroy(self):
		self.ClearDictionary()
		self.entries = []
		self.skillList = None
		self.skillScroll = None
		self.layerButtons = []
		self.layerBars = []
		self.allButton = None
		self.offButton = None
		self.picker = None
		self.dot = None
		self.hexEdit = None
		self.hint = None
		self.isLoaded = False

	def Open(self):
		self.__Load()
		self.__RefreshList()
		self.SetCenterPosition()
		self.Show()
		self.SetTop()

	def Close(self):
		if self.isLoaded and self.hexEdit:
			self.hexEdit.KillFocus()
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	# ------------------------------------------------------------------ the skills
	def __RefreshList(self):
		self.entries = Entries()
		self.skillList.ClearItem()
		for i, (vnum, name, ok, hint) in enumerate(self.entries):
			text = name
			if not ok:
				text += TEXT_SUFFIX_HORSE if hint == TEXT_HINT_HORSE else TEXT_SUFFIX_P
			self.skillList.InsertItem(i, text, COLOR_OK if ok else COLOR_LOCKED)
		view = self.skillList.GetViewItemCount()
		if len(self.entries) > view:
			self.skillScroll.SetMiddleBarSize(float(view) / len(self.entries))
			self.skillScroll.Show()
		else:
			self.skillScroll.Hide()
		self.skillScroll.SetPos(0.0)
		self.skillList.SetBasePos(0)
		index = 0
		for i, entry in enumerate(self.entries):
			if entry[0] == self.vnum:
				index = i
				break
		if self.entries:
			self.skillList.ClearSelection()
			self.skillList.SelectItem(index)
		else:
			self.vnum = 0
			self.ok = False
			self.colors = [-1] * LAYERS
			self.hint.SetText(TEXT_HINT_NONE)
			self.__RefreshLayers()

	def __OnScroll(self):
		extra = len(self.entries) - self.skillList.GetViewItemCount()
		if extra > 0:
			self.skillList.SetBasePos(int(self.skillScroll.GetPos() * extra + 0.5))

	def __OnSelectSkill(self, index, text):
		if index < 0 or index >= len(self.entries):
			return
		vnum, name, ok, hint = self.entries[index]
		self.vnum = vnum
		self.ok = ok
		try:
			self.colors = [int(c) for c in player.GetSkillColor(vnum)][:LAYERS]
		except Exception:
			self.colors = [-1] * LAYERS
		while len(self.colors) < LAYERS:
			self.colors.append(-1)
		self.hint.SetText(TEXT_HINT_PICK if ok else hint)
		self.dot.Hide()
		self.__OnSelectLayer(self.layer)

	# ------------------------------------------------------------------ the layers
	def __RefreshLayers(self):
		for i in xrange(LAYERS):
			self.layerBars[i].SetColor(_GrpColor(self.colors[i]))
			if i == self.layer:
				self.layerButtons[i].Down()
			else:
				self.layerButtons[i].SetUp()
		color = self.colors[self.layer]
		self.hexEdit.SetText(skillcolorpick.ToHex(color) if color >= 0 else "")

	def __OnSelectLayer(self, layer):
		self.layer = min(max(int(layer), 0), LAYERS - 1)
		self.dot.Hide()
		self.__RefreshLayers()

	def __OnAllLayers(self, on):
		self.allLayers = bool(on)

	def __SetColor(self, value):
		if self.allLayers:
			self.colors = [value] * LAYERS
		else:
			self.colors[self.layer] = value
		self.__RefreshLayers()

	def __OnLayerOff(self):
		self.dot.Hide()
		self.__SetColor(-1)

	def __OnPick(self):
		xMouse, yMouse = wndMgr.GetMousePosition()
		xPicker, yPicker = self.picker.GetGlobalPosition()
		x = min(max(xMouse - xPicker, 0), skillcolorpick.PICKER_WIDTH - 1)
		y = min(max(yMouse - yPicker, 0), skillcolorpick.PICKER_HEIGHT - 1)
		value = skillcolorpick.FromRGB(skillcolorpick.ColorAt(x, y))
		if not skillcolorpick.IsBrightEnough(value):
			chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_DARK)
			return
		self.__SetColor(value)
		self.dot.SetPosition(x - self.dot.GetWidth() / 2, y - self.dot.GetHeight() / 2)
		self.dot.Show()

	def __OnHexApply(self):
		value = skillcolorpick.ParseHex(self.hexEdit.GetText())
		if value < 0:
			chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_BAD_HEX)
			return
		if not skillcolorpick.IsBrightEnough(value):
			chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_DARK)
			return
		self.dot.Hide()
		self.__SetColor(value)

	# ------------------------------------------------------------------ to the server
	def __Name(self):
		for vnum, name, ok, hint in self.entries:
			if vnum == self.vnum:
				return name
		return ""

	def __OnApply(self):
		if not self.vnum:
			return
		if not self.ok:
			chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_LOCKED)
			return
		player.SetSkillColor(self.vnum, *self.colors)
		if [c for c in self.colors if c >= 0]:
			chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_SAVED % self.__Name())
		else:
			chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_RESET % self.__Name())

	def __OnDefault(self):
		if not self.vnum:
			return
		self.colors = [-1] * LAYERS
		self.dot.Hide()
		self.__RefreshLayers()
		player.SetSkillColor(self.vnum, -1, -1, -1, -1, -1)
		chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_RESET % self.__Name())


def OpenWindow():
	if not IsSupported():
		return
	wnd = _state["window"]
	if wnd is None:
		wnd = SkillColorWindow()
		_state["window"] = wnd
	wnd.Open()


def ToggleWindow():
	wnd = _state["window"]
	if wnd is not None and wnd.IsShow():
		wnd.Close()
	else:
		OpenWindow()


def CloseWindow():
	wnd = _state["window"]
	if wnd is not None:
		wnd.Close()


def DestroyWindow():
	wnd = _state["window"]
	_state["window"] = None
	if wnd is not None:
		wnd.Hide()
		wnd.Destroy()


def CreateButton(parent, x, y):
	"""The skill tab's "Kolory" button (uicharacter.py) - None with an older exe."""
	if not IsSupported():
		return None
	button = ui.Button()
	button.SetParent(parent)
	button.SetUpVisual("d:/ymir work/ui/public/large_button_01.sub")
	button.SetOverVisual("d:/ymir work/ui/public/large_button_02.sub")
	button.SetDownVisual("d:/ymir work/ui/public/large_button_03.sub")
	button.SetText(TEXT_BUTTON)
	button.SetToolTipText(TEXT_BUTTON_TIP)
	button.SetPosition(x, y)
	button.SetEvent(ToggleWindow)
	button.Show()
	return button
