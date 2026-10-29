# MT2009_PLUS_HORSE40_V1: the horse past level 21 - the Stajenny's window (server-patches/konie/README.md).
# The pl-wiki's "Kon" (levels 22-40 with Pasza dla Konia, the failed try's Gaya, the horse skills) in the shape of the
# uploaded package "system_rozwoju_konia" (Best Studio's export of the official Mount Upgrade System - its
# uimountupgradesystem.py / mountupgradesystemwindow.py: the level boxes, the experience bar, the feed and level-up
# buttons, the Yang and Gaya costs) and its horse skill icons, built in code like uiygaya.py. No new packet: the
# package's exe module "mount" is replaced by chat commands -
#   server -> client  "konie_rozwoj_info <open> <horse level> <exp> <exp needed> <yang> <failed> <retry gaya>
#                      <requirement> <skill 1> <level 1> <skill 2> <level 2> <slots> <golden book>"
#                     "konie_rozwoj_msg <code> <a> <b>"            (konie_rozwoj.cpp KonieSendInfo / KonieMsg)
#   client -> server  "/konie_rozwoj info|karm|awans|umiej <1|2>"   (ACMD do_konie_rozwoj)
# The Stajenny opens it (quest konie_rozwoj, "Rozwoj konia (21-40)"); the images are the pack "konie"
# (client-2.0.30/tools/konie). Python 2.7 as the client has it; the texts are CP1250 escapes.

import chat
import net
import player
import ui
import uiCommon
import uiToolTip
import wndMgr

PATH = "d:/ymir work/ui/konie/"
FEED_VNUM = 50048
FEED_LEVEL_UP = 50
SKILL_GAYA = 1000
SKILL_YANG = 20000000
MAX_LEVEL = 40

BOARD_WIDTH = 332
BOARD_HEIGHT = 312

COLOR_OK = 0xff9ff59f
COLOR_BAD = 0xffff7070
COLOR_GOLD = 0xfff2e7c1
COLOR_DIM = 0xffb0b0b0

TEXT_TITLE = "Rozw\xf3j konia"
TEXT_LEVEL = "Poziom konia"
TEXT_FEED_BUTTON = "Nakarm konia"
TEXT_LEVEL_BUTTON = "Spr\xf3buj awansu"
TEXT_SKILL_BUTTON = "Ulepsz"
TEXT_FEED_HAVE = "Pasza dla Konia w ekwipunku: %d"
TEXT_FULL = "Pasek pe\xb3ny - spr\xf3buj awansu (%d paszy i Yang)."
TEXT_FEED_MORE = "Karm konia Pasz\xb9 dla Konia, a\xbf pasek si\xea wype\xb3ni."
TEXT_RETRY = "Poprzednia pr\xf3ba nieudana - ta kosztuje te\xbf Gaya i si\xea uda."
TEXT_REQ = {
	1: "Wymagany poziom postaci: 75",
	2: "Od 30 poziomu konia: wymagany Poziom Czempiona 1",
	3: "Tw\xf3j ko\xf1 osi\xb9gn\xb9\xb3 najwy\xbfszy, 40 poziom.",
	4: "Ten rozw\xf3j jest dla konia od 21 poziomu.",
}
TEXT_SKILLS = "Umiej\xeatno\x9cci konia (miejsca: %d z 2)"
TEXT_SKILL_EMPTY = "- wolne miejsce: przeczytaj ksi\xeag\xea umiej\xeatno\x9cci konnej"
TEXT_SKILL_LOCKED = "- drugie miejsce od 31 poziomu konia"
TEXT_SKILL_LEVEL = "Poziom %d / 20"
TEXT_HINT = "Zapomnienie umiej\xeatno\x9cci: Stajenny (za darmo)."
TEXT_ASK_FEED = "Nakarmi\xe6 konia Pasz\xb9 dla Konia?"
TEXT_ASK_FEED2 = "Zjedzona zostanie pasza potrzebna do pe\xb3nego paska."
TEXT_ASK_LEVEL = "Spr\xf3bowa\xe6 awansu konia na %d poziom?"
TEXT_ASK_LEVEL2 = "Koszt: %d Paszy dla Konia, %s Yang%s."
TEXT_ASK_LEVEL_GAYA = " i %d Gaya"
TEXT_ASK_SKILL = "Ulepszy\xe6 %s do poziomu %d?"
TEXT_ASK_SKILL2 = "Koszt: %d Gaya i %s Yang."
TEXT_TIP_YANG = "Yang za pr\xf3b\xea awansu"
TEXT_TIP_GAYA = "Gaya za ponown\xb9 pr\xf3b\xea"
TEXT_TIP_NEXT = "Nast\xeapny poziom:"
TEXT_TIP_COST = "Ulepszenie: 1000 Gaya i 20 000 000 Yang"
TEXT_TIP_RIDING = "Dzia\xb3a na ka\xbfdym wierzchowcu."

MSG = {
	1: "Rozw\xf3j konia: porozmawiaj ze Stajennym, aby otworzy\xe6 okno.",
	2: "Rozw\xf3j konia: brakuje Paszy dla Konia (potrzeba %(a)d).",
	3: "Rozw\xf3j konia: najpierw wype\xb3nij pasek do\x9cwiadczenia konia.",
	4: "Rozw\xf3j konia: masz za ma\xb3o Yang (potrzeba %(a)s).",
	5: "Rozw\xf3j konia: masz za ma\xb3o Gaya (potrzeba %(a)d).",
	6: "Tw\xf3j ko\xf1 osi\xb9gn\xb9\xb3 %(a)d poziom!",
	7: "Awans konia si\xea nie uda\xb3. Nast\xeapna pr\xf3ba kosztuje dodatkowo %(b)d Gaya i si\xea uda.",
	8: "Pasek do\x9cwiadczenia konia jest pe\xb3ny - spr\xf3buj awansu.",
	9: "Zsi\xb9d\x9f z konia, aby go rozwija\xe6.",
	11: "Rozw\xf3j konia: wymagany %(a)d poziom postaci.",
	12: "Rozw\xf3j konia: od 30 poziomu konia wymagany jest Poziom Czempiona 1.",
	13: "Tw\xf3j ko\xf1 osi\xb9gn\xb9\xb3 najwy\xbfszy poziom.",
	14: "Rozw\xf3j konia: potrzebny ko\xf1 od 21 poziomu.",
	20: "Ta umiej\xeatno\x9c\xe6 konia ma ju\xbf 20 poziom.",
	21: "%(name)s: poziom %(b)d.",
	22: "Ko\xf1 zjad\xb3 %(a)d Paszy dla Konia (do\x9cwiadczenie %(b)d).",
}

# vnum -> (name, icon, what it does - %(v)s the value, %(d)d the seconds)
SKILLS = {
	285: ("Jazda (Zwinne Kopyta)", "mount_upgrade_skill_nimble", "Pr\xeadko\x9c\xe6 ruchu +%(v)s%% na %(d)d s po ataku z grzbietu wierzchowca (co 180 s)"),
	286: ("Jazda Konna (PD)", "mount_upgrade_skill_exp", "Do\x9cwiadczenie +%(v)s%% podczas jazdy"),
	287: ("Jazda (Gwa\xb3t. Wichura)", "mount_upgrade_skill_speed", "Pr\xeadko\x9c\xe6 ataku +%(v)s%% na %(d)d s po ataku z grzbietu wierzchowca (co 180 s)"),
	288: ("Jazda (Bezszelest. Ch\xf3d)", "mount_upgrade_skill_gyeonggong", "Lekki Krok (pr\xeadko\x9c\xe6 ruchu +%(v)s) na %(d)d s po ataku pieszo (co 300 s)"),
	289: ("Jazda (Nie\x9cmiertelno\x9c\xe6)", "mount_upgrade_skill_invisibility", "Niewra\xbfliwo\x9c\xe6 na obra\xbfenia przez %(d)d s, gdy P\xaf je\x9fd\x9fca spadn\xb9 poni\xbfej 30%% (co 600 s)"),
	290: ("Jazda (Brak Odrzutu)", "mount_upgrade_skill_knockback", "Szansa 1%% przy ataku z wierzchowca: brak odrzutu przez %(d)d s (co 180 s)"),
	291: ("Jazda Konna (p\xf3\xb3ludzie)", "mount_upgrade_skill_random_strong", "Silny przeciwko p\xf3\xb3ludziom +%(v)s%% podczas jazdy"),
	292: ("Jazda Konna (zwierz\xeata)", "mount_upgrade_skill_random_strong", "Silny przeciwko zwierz\xeatom +%(v)s%% podczas jazdy"),
	293: ("Jazda Konna (orki)", "mount_upgrade_skill_random_strong", "Silny przeciwko orkom +%(v)s%% podczas jazdy"),
	294: ("Jazda Konna (mistycy)", "mount_upgrade_skill_random_strong", "Silny przeciwko mistykom +%(v)s%% podczas jazdy"),
	295: ("Jazda Konna (nieumarli)", "mount_upgrade_skill_random_strong", "Silny przeciwko nieumar\xb3ym +%(v)s%% podczas jazdy"),
	296: ("Jazda Konna (diab\xb3y)", "mount_upgrade_skill_random_strong", "Silny przeciwko diab\xb3om +%(v)s%% podczas jazdy"),
	298: ("Jazda Konna (pustynia)", "mount_upgrade_skill_random_strong", "Silny przeciwko potworom pustyni +%(v)s%% podczas jazdy"),
	299: ("Jazda Konna (insekty)", "mount_upgrade_skill_random_strong", "Silny przeciwko insektom +%(v)s%% podczas jazdy"),
	300: ("Jazda Konna (potwory)", "mount_upgrade_skill_random_strong", "Silny przeciwko potworom +%(v)s%% podczas jazdy"),
	301: ("Jazda (umiej. konne)", "mount_upgrade_skill_effect_up", "Obra\xbfenia umiej\xeatno\x9cci konnych +%(v)s%%"),
	302: ("Jazda Konna (Wojownik)", "mount_upgrade_skill_random_strong", "Silny przeciwko wojownikom +%(v)s%% podczas jazdy"),
	303: ("Jazda Konna (Ninja)", "mount_upgrade_skill_random_strong", "Silny przeciwko ninja +%(v)s%% podczas jazdy"),
	304: ("Jazda Konna (Sura)", "mount_upgrade_skill_random_strong", "Silny przeciwko surom +%(v)s%% podczas jazdy"),
	305: ("Jazda Konna (Szaman)", "mount_upgrade_skill_random_strong", "Silny przeciwko szamanom +%(v)s%% podczas jazdy"),
	307: ("Jazda (W. SungMa. SI\xa3A)", "mount_upgrade_skill_sungma_str", "Wola SungMa (SI\xa3A) +%(v)s na %(d)d s po ataku z grzbietu wierzchowca (co 180 s)"),
	308: ("Jazda (W. SungMa. WIT)", "mount_upgrade_skill_sungma_hp", "Wola SungMa (WIT) +%(v)s na %(d)d s po ataku z grzbietu wierzchowca (co 180 s)"),
	309: ("Jazda (W. SungMa. ODP)", "mount_upgrade_skill_sungma_move", "Wola SungMa (ODP) +%(v)s na %(d)d s po ataku z grzbietu wierzchowca (co 180 s)"),
	310: ("Jazda (W. SungMa. INT)", "mount_upgrade_skill_sungma_immune", "Wola SungMa (INT) +%(v)s na %(d)d s po ataku z grzbietu wierzchowca (co 180 s)"),
	311: ("Jazda Konna (Precyzja)", "mount_upgrade_skill_hit_pct", "Precyzja +%(v)s podczas jazdy"),
}


# konie_rozwoj.cpp KonieValue / KonieDuration (the package's polynomials) - s the skill's level, h the horse's
def Value(v, s, h):
	s = float(s)
	h = float(h)
	if v == 285:
		return (4.0 + h * s / 100.0) * (s / 3.0)
	if v == 286:
		return (h * s / 100.0) + 1.5 + (s / 8.0)
	if v == 287:
		return (5.0 + h * s / 600.0) * (s / 5.0)
	if v == 288:
		return 60.0 * min(1.0, s * h / 800.0)
	if v == 301:
		return s * s / (140.0 - h)
	if v in (307, 308, 309, 310):
		return 3.0 + (h * s) * (s / 500.0)
	return 1.0 + s * h / 100.0


def Duration(v, s, h):
	s = float(s)
	h = float(h)
	d = 0.0
	if v in (285, 287, 307, 308, 309, 310):
		d = 3.0 + (s * h * 0.4) / 20.0
	elif v == 288:
		d = 1.0 + (s * h * 0.3) / 20.0
	elif v == 289:
		d = (h * s * 0.3) / 60.0
	elif v == 290:
		d = 3.0 + (s * h * 0.5) / 20.0
	return max(1, int(d))


def ValueText(v, s, h):
	value = Value(v, s, h)
	if v == 301:
		return "%.2f" % value
	return "%d" % max(1, int(value))


def EffectText(v, s, h):
	data = SKILLS.get(v)
	if not data:
		return ""
	return data[2] % {"v": ValueText(v, s, h), "d": Duration(v, s, h)}


def ToInt(value, default=0):
	try:
		return int(value)
	except Exception:
		return default


def FormatNumber(n):
	s = str(int(n))
	out = ""
	while len(s) > 3:
		out = " " + s[-3:] + out
		s = s[:-3]
	return s + out


_state = {"window": None, "interface": None, "info": None}


class HorseUpgradeWindow(ui.BoardWithTitleBar):

	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)
		self.widgets = []
		self.dialog = None
		self.popup = None
		self.toolTip = uiToolTip.ToolTip()
		self.toolTip.HideToolTip()
		self.info = None
		self.skillRows = []
		self.AddFlag("movable")
		self.AddFlag("float")
		self.SetSize(BOARD_WIDTH, BOARD_HEIGHT)
		self.SetTitleName(TEXT_TITLE)
		self.SetCloseEvent(ui.__mem_func__(self.Close))
		self.__Build()
		self.SetCenterPosition()

	def __del__(self):
		ui.BoardWithTitleBar.__del__(self)

	def __Image(self, x, y, path, expanded=False):
		image = ui.ExpandedImageBox() if expanded else ui.ImageBox()
		image.SetParent(self)
		image.SetPosition(x, y)
		image.LoadImage(path)
		image.Show()
		self.widgets.append(image)
		return image

	def __Label(self, x, y, text="", center=False, color=None, parent=None):
		line = ui.TextLine()
		line.SetParent(parent or self)
		line.SetPosition(x, y)
		if center:
			line.SetHorizontalAlignCenter()
		line.SetText(text)
		if color is not None:
			line.SetPackedFontColor(color)
		line.Show()
		self.widgets.append(line)
		return line

	def __Button(self, x, y, text, event, size="large", arg=None):
		button = ui.Button()
		button.SetParent(self)
		button.SetPosition(x, y)
		button.SetUpVisual("d:/ymir work/ui/public/%s_button_01.sub" % size)
		button.SetOverVisual("d:/ymir work/ui/public/%s_button_02.sub" % size)
		button.SetDownVisual("d:/ymir work/ui/public/%s_button_03.sub" % size)
		button.SetText(text)
		if arg is None:
			button.SAFE_SetEvent(event)
		else:
			button.SAFE_SetEvent(event, arg)
		button.Show()
		self.widgets.append(button)
		return button

	def __Build(self):
		self.__Label(BOARD_WIDTH / 2, 34, TEXT_LEVEL, True, COLOR_GOLD)
		# the package's row: current level, the experience bar, the next level
		self.__Image(14, 54, PATH + "level_cur_bg.sub")
		self.curLevel = self.__Label(42, 57, "", True)
		self.__Image(76, 52, PATH + "exp_gage_bg.sub")
		self.gauge = self.__Image(82, 54, PATH + "exp_gage_bar.sub", True)
		self.gaugeText = self.__Label(163, 57, "", True)
		self.__Image(260, 54, PATH + "level_next_bg.sub")
		self.arrow = self.__Image(264, 56, PATH + "levelup_arrow.sub")
		self.nextLevel = self.__Label(292, 57, "", True)

		self.statusLine = self.__Label(BOARD_WIDTH / 2, 84, "", True)
		self.feedLine = self.__Label(BOARD_WIDTH / 2, 102, "", True, COLOR_DIM)

		# the costs: Yang always, Gaya after a failed try
		self.yangIcon = self.__Image(70, 125, PATH + "yang_icon.sub")
		self.yangIcon.SetEvent(ui.__mem_func__(self.__TipText), "mouse_over_in", TEXT_TIP_YANG)
		self.yangIcon.SetEvent(ui.__mem_func__(self.__TipHide), "mouse_over_out")
		self.__Image(86, 123, PATH + "yang_text_bg.sub")
		self.yangText = self.__Label(166, 125, "")
		self.yangText.SetHorizontalAlignRight()
		self.gemIcon = self.__Image(186, 124, PATH + "gem_icon.sub")
		self.gemIcon.SetEvent(ui.__mem_func__(self.__TipText), "mouse_over_in", TEXT_TIP_GAYA)
		self.gemIcon.SetEvent(ui.__mem_func__(self.__TipHide), "mouse_over_out")
		self.gemBg = self.__Image(206, 123, PATH + "gem_text_bg.sub")
		self.gemText = self.__Label(252, 125, "")
		self.gemText.SetHorizontalAlignRight()

		self.feedButton = self.__Button(60, 150, TEXT_FEED_BUTTON, self.OnFeed)
		self.levelButton = self.__Button(BOARD_WIDTH - 60 - 88, 150, TEXT_LEVEL_BUTTON, self.OnLevel)

		self.skillTitle = self.__Label(BOARD_WIDTH / 2, 186, "", True, COLOR_GOLD)
		for i in xrange(2):
			y = 206 + 42 * i
			icon = self.__Image(16, y, PATH + "mount_upgrade_skill_random_strong.sub")
			icon.SetEvent(ui.__mem_func__(self.__TipSkill), "mouse_over_in", i)
			icon.SetEvent(ui.__mem_func__(self.__TipHide), "mouse_over_out")
			name = self.__Label(56, y + 1, "")
			level = self.__Label(56, y + 17, "", False, COLOR_DIM)
			button = self.__Button(BOARD_WIDTH - 16 - 44, y + 6, TEXT_SKILL_BUTTON, self.OnSkill, "small", i + 1)
			self.skillRows.append((icon, name, level, button))
		self.__Label(BOARD_WIDTH / 2, 290, TEXT_HINT, True, COLOR_DIM)

	# ---------------------------------------------------------------- the server's state
	def SetInfo(self, info):
		self.info = info
		self.Refresh()

	def Refresh(self):
		info = self.info
		if not info:
			return
		level = info["level"]
		need = info["need"]
		exp = min(info["exp"], need) if need else 0
		full = need > 0 and info["exp"] >= need
		self.curLevel.SetText(str(level))
		if level >= MAX_LEVEL or info["req"] in (3, 4):
			self.nextLevel.SetText("")
			self.arrow.Hide()
		else:
			self.nextLevel.SetText(str(level + 1))
			if full:
				self.arrow.Show()
			else:
				self.arrow.Hide()
		self.gauge.SetPercentage(exp if need else 1, need if need else 1)
		if level >= MAX_LEVEL:
			self.gaugeText.SetText("MAX")
		else:
			self.gaugeText.SetText("%s / %s" % (FormatNumber(exp), FormatNumber(need)))

		req = info["req"]
		if req:
			self.statusLine.SetText(TEXT_REQ.get(req, ""))
			self.statusLine.SetPackedFontColor(COLOR_BAD if req in (1, 2, 4) else COLOR_OK)
		elif info["fail"] and full:
			self.statusLine.SetText(TEXT_RETRY)
			self.statusLine.SetPackedFontColor(COLOR_GOLD)
		elif full:
			self.statusLine.SetText(TEXT_FULL % FEED_LEVEL_UP)
			self.statusLine.SetPackedFontColor(COLOR_OK)
		else:
			self.statusLine.SetText(TEXT_FEED_MORE)
			self.statusLine.SetPackedFontColor(COLOR_GOLD)
		self.feedLine.SetText(TEXT_FEED_HAVE % player.GetItemCountByVnum(FEED_VNUM))

		self.yangText.SetText(FormatNumber(info["yang"]) if not req else "-")
		if info["fail"] and not req:
			self.gemText.SetText(str(info["gaya"]))
			self.gemIcon.Show()
			self.gemBg.Show()
			self.gemText.Show()
		else:
			self.gemIcon.Hide()
			self.gemBg.Hide()
			self.gemText.Hide()
		if full:
			self.feedButton.Hide()
			self.levelButton.Show()
		else:
			self.feedButton.Show()
			self.levelButton.Hide()
		if req:
			self.feedButton.Disable()
			self.levelButton.Disable()
		else:
			self.feedButton.Enable()
			self.levelButton.Enable()

		self.skillTitle.SetText(TEXT_SKILLS % info["slots"])
		for i in xrange(2):
			icon, name, lvl, button = self.skillRows[i]
			v, s = info["skills"][i]
			if v in SKILLS and s > 0:
				icon.LoadImage(PATH + SKILLS[v][1] + ".sub")
				icon.SetAlpha(1.0)
				name.SetText(SKILLS[v][0])
				lvl.SetText(TEXT_SKILL_LEVEL % s)
				if s < 20:
					button.Show()
				else:
					button.Hide()
			else:
				icon.LoadImage(PATH + "mount_upgrade_skill_random_strong.sub")
				icon.SetAlpha(0.3)
				name.SetText(TEXT_SKILL_EMPTY if i < info["slots"] else TEXT_SKILL_LOCKED)
				lvl.SetText("")
				button.Hide()

	# ---------------------------------------------------------------- the tooltips
	def __TipText(self, event, text):
		self.toolTip.ClearToolTip()
		self.toolTip.AppendTextLine(text, COLOR_GOLD)
		self.toolTip.ShowToolTip()

	def __TipHide(self, *args):
		self.toolTip.HideToolTip()

	def __TipSkill(self, event, i):
		info = self.info
		if not info:
			return
		v, s = info["skills"][i]
		self.toolTip.ClearToolTip()
		if v not in SKILLS or s <= 0:
			self.toolTip.AppendTextLine(TEXT_SKILL_EMPTY if i < info["slots"] else TEXT_SKILL_LOCKED, COLOR_DIM)
			self.toolTip.ShowToolTip()
			return
		h = max(21, info["level"])
		self.toolTip.AppendTextLine(SKILLS[v][0], COLOR_GOLD)
		self.toolTip.AppendTextLine(TEXT_SKILL_LEVEL % s)
		self.toolTip.AppendTextLine(EffectText(v, s, h))
		if s < 20:
			self.toolTip.AppendTextLine(TEXT_TIP_NEXT, COLOR_DIM)
			self.toolTip.AppendTextLine(EffectText(v, s + 1, h), COLOR_DIM)
			self.toolTip.AppendTextLine(TEXT_TIP_COST, COLOR_DIM)
		self.toolTip.AppendTextLine(TEXT_TIP_RIDING, COLOR_DIM)
		self.toolTip.ShowToolTip()

	# ---------------------------------------------------------------- the buttons
	def __Ask(self, line1, line2, action):
		self.__CloseDialog()
		dialog = uiCommon.QuestionDialog2()
		dialog.SetText1(line1)
		dialog.SetText2(line2)
		dialog.SetAcceptEvent(lambda: self.__Answer(action))
		dialog.SetCancelEvent(ui.__mem_func__(self.__CloseDialog))
		dialog.Open()
		self.dialog = dialog

	def __Answer(self, action):
		self.__CloseDialog()
		net.SendChatPacket("/konie_rozwoj " + action)

	def __CloseDialog(self):
		if self.dialog:
			self.dialog.Close()
			self.dialog = None

	def OnFeed(self):
		if not self.info:
			return
		if player.GetItemCountByVnum(FEED_VNUM) < 1:
			ShowMessage(2, FEED_LEVEL_UP, 0)
			return
		self.__Ask(TEXT_ASK_FEED, TEXT_ASK_FEED2, "karm")

	def OnLevel(self):
		info = self.info
		if not info:
			return
		gaya = TEXT_ASK_LEVEL_GAYA % info["gaya"] if info["fail"] else ""
		self.__Ask(TEXT_ASK_LEVEL % (info["level"] + 1),
				   TEXT_ASK_LEVEL2 % (FEED_LEVEL_UP, FormatNumber(info["yang"]), gaya), "awans")

	def OnSkill(self, slot):
		info = self.info
		if not info:
			return
		v, s = info["skills"][slot - 1]
		if v not in SKILLS or s <= 0 or s >= 20:
			return
		self.__Ask(TEXT_ASK_SKILL % (SKILLS[v][0], s + 1), TEXT_ASK_SKILL2 % (SKILL_GAYA, FormatNumber(SKILL_YANG)),
				   "umiej %d" % slot)

	def Popup(self, text):
		if self.popup:
			self.popup.Close()
		popup = uiCommon.PopupDialog()
		popup.SetText(text)
		popup.Open()
		self.popup = popup

	def Open(self):
		self.Refresh()
		self.SetTop()
		self.Show()

	def Close(self):
		self.__CloseDialog()
		self.toolTip.HideToolTip()
		if self.popup:
			self.popup.Close()
			self.popup = None
		self.Hide()

	def Destroy(self):
		self.Close()
		self.widgets = []
		self.skillRows = []

	def OnPressEscapeKey(self):
		self.Close()
		return True


def __Window():
	window = _state["window"]
	if window is None:
		import uiminigameutil
		window = uiminigameutil.SafeCreate(HorseUpgradeWindow, TEXT_TITLE)
		if window is None:
			return None
		_state["window"] = window
	return window


def SetInterface(interface):
	_state["interface"] = interface


def ShowMessage(code, a, b):
	text = MSG.get(code)
	if not text:
		return
	name = SKILLS.get(a, ("", "", ""))[0]
	try:
		text = text % {"a": FormatNumber(a) if code == 4 else a, "b": b, "name": name}
	except Exception:
		pass
	chat.AppendChat(chat.CHAT_TYPE_INFO, text)
	window = _state["window"]
	if window is not None and window.IsShow() and code in (6, 7):
		window.Popup(text)


# "konie_rozwoj_info ..." (game.py)
def OnInfo(*args):
	try:
		v = [ToInt(x) for x in args]
		if len(v) < 14:
			return
		info = {"level": v[1], "exp": v[2], "need": v[3], "yang": v[4], "fail": v[5], "gaya": v[6], "req": v[7],
				"skills": ((v[8], v[9]), (v[10], v[11])), "slots": v[12], "golden": v[13]}
		_state["info"] = info
		window = _state["window"]
		if v[0] == 1:
			window = __Window()
			if window is None:
				return
			window.SetInfo(info)
			window.Open()
		elif window is not None:
			window.SetInfo(info)
	except Exception:
		import dbg
		import sys
		dbg.TraceError("uikonierozwoj.OnInfo %s: %s" % (str(args), str(sys.exc_info()[1])))


# "konie_rozwoj_msg <code> <a> <b>" (game.py)
def OnMessage(*args):
	try:
		v = [ToInt(x) for x in args] + [0, 0, 0]
		ShowMessage(v[0], v[1], v[2])
	except Exception:
		import dbg
		import sys
		dbg.TraceError("uikonierozwoj.OnMessage %s: %s" % (str(args), str(sys.exc_info()[1])))


def DestroyWindow():
	window = _state["window"]
	_state["window"] = None
	_state["info"] = None
	if window is not None:
		window.Destroy()
