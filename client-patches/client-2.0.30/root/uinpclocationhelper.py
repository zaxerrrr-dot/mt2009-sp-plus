# MT2009_PLUS_NPC_LOCATION_HELPER_V1 - Lokalizator NPC, the improved world map (Autor: Best Studio; ported to MT2009 Plus).
#
# The package's window file with our changes (search "MT2009" below):
#  - texts: Polish, put into localeInfo / uiScriptLocale here when the locale packs do not have them (_PL_*_TEXTS);
#  - app flags our exe may not have (ENABLE_CLIP_MASK, ENABLE_ELEMENT_ADD, ENABLE_EVENT_BANNER, ...) are read with
#    getattr; the current map's index comes from _CurMapIndex() (net.GetMapIndex when the exe has it, otherwise the
#    current map's folder name looked up in npc_location_helper.txt);
#  - the teleport question shows the real cost (1 stone on the same map, 2 in the same region, 3 elsewhere - the
#    server's rule, npc_location_helper.cpp);
#  - map names: localeInfo.MINIMAP_ZONE_NAME_DICT matched without regard to case (our folders keep their case);
#  - at the end: MiniMapBridge (what the package added to uiminimap.py's MiniMap: the switch between the small atlas
#    and this window) and the hooks game.py calls (OnGameOpen, OnServerStatus, OnServerWarpResult, OnServerGuildLand).
# Needs an exe with the module npcLocationHelper (ENABLE_NPC_LOCATION_HELPER); without it importing this file fails
# and uiminimap.py / game.py simply do without it.
import ui
import uiCommon
import uiToolTip
import app
import wndMgr
import miniMap
import player
import item
import nonplayer
import net
import localeInfo
import uiScriptLocale
import chat
import background # MT2009: _CurMapIndex

import npcLocationHelper

# MT2009: the Polish texts, only where the locale packs do not have the key
_PL_LOCALE_TEXTS = (
	("NPC_LOCATION_HELPER_ATLAS_DONT_SHOW_MAP", "Ta mapa nie jest dost\xeapna."),
	("NPC_LOCATION_HELPER_ATLAS_UNLOCKED_MAP_1", "Nie widzisz jeszcze ca\xb3ej mapy."),
	("NPC_LOCATION_HELPER_ATLAS_UNLOCKED_MAP_2", "Najpierw odblokuj: %s."),
	("NPC_LOCATION_HELPER_CANNOT_WARP_TO_NPC_NOW", "Nie mo\xbfesz si\xea teraz teleportowa\xe6."),
	("NPC_LOCATION_HELPER_CAN_WARP_TO_NPC_STATE_FALSE_COOLTIME", "Kolejna teleportacja mo\xbfliwa za %d min."),
	("NPC_LOCATION_HELPER_CAN_WARP_TO_NPC_STATE_FALSE_COOLTIME_LESS_THAN_1M", "Kolejna teleportacja mo\xbfliwa za nieca\xb3\xb9 minut\xea."),
	("NPC_LOCATION_HELPER_CAN_WARP_TO_NPC_STATE_FALSE_DIFFERENT_EMPIRE", "Nie mo\xbfesz si\xea teleportowa\xe6 do NPC wrogiego kr\xf3lestwa."),
	("NPC_LOCATION_HELPER_CAN_WARP_TO_NPC_STATE_FALSE_GOLD", "Masz za ma\xb3o Yang."),
	("NPC_LOCATION_HELPER_CAN_WARP_TO_NPC_STATE_FALSE_LEVEL_LIMIT", "Tw\xf3j poziom (lub Poziom Czempiona) jest za niski na t\xea map\xea."),
	("NPC_LOCATION_HELPER_MAP_CATEGORY_EMPIRE_DUNGEON", "Lochy"),
	("NPC_LOCATION_HELPER_MAP_CATEGORY_EMPIRE_FIELD", "Kr\xf3lestwa"),
	("NPC_LOCATION_HELPER_MAP_CATEGORY_EVIL_DRAGON_TERRITORY", "Ziemie Mrocznego Smoka"),
	("NPC_LOCATION_HELPER_MAP_CATEGORY_HIDDEN", "Inne"),
	("NPC_LOCATION_HELPER_MAP_CATEGORY_LABYRINTH", "P\xb3askowy\xbf Iluzji"),
	("NPC_LOCATION_HELPER_MAP_CATEGORY_NEUTRAL", "Ziemie neutralne"),
	("NPC_LOCATION_HELPER_MAP_CATEGORY_NEW_WORLD_DUNGEON", "Lochy Yohary"),
	("NPC_LOCATION_HELPER_MAP_CATEGORY_NEW_WORLD_FIELD", "Yohara"),
	("NPC_LOCATION_HELPER_MESSAGE_CANNOT_TOGGLE_ATLAS_DISABLED", "Najpierw w\xb3\xb9cz Lokalizator NPC (u\xbfyj przedmiotu Lokalizator NPC)."),
	("NPC_LOCATION_HELPER_MESSAGE_CANNOT_TOGGLE_TO_SMALL_ATLAS", "Tutaj nie mo\xbfna zmieni\xe6 widoku mapy."),
	("NPC_LOCATION_HELPER_MESSAGE_CANNOT_USE_STONE_OF_WARP_DISABLED", "Najpierw w\xb3\xb9cz Lokalizator NPC (u\xbfyj przedmiotu Lokalizator NPC)."),
	("NPC_LOCATION_HELPER_MESSAGE_CANNOT_WARP_TO_NPC_NOW", "Nie mo\xbfesz si\xea teraz teleportowa\xe6."),
	("NPC_LOCATION_HELPER_MESSAGE_GUILD_LAND_UPDATE_COOLTIME", "Spr\xf3buj ponownie za chwil\xea."),
	("NPC_LOCATION_HELPER_MESSAGE_NOT_ENOUGH_STONE_OF_WARP", "Masz za ma\xb3o Kamieni Teleportacji."),
	("NPC_LOCATION_HELPER_MESSAGE_SELECTED_NPC_IS_NEAR", "Wybrany NPC jest tu\xbf obok."),
	("NPC_LOCATION_HELPER_NPC_ROLE_TOOLTIP_ALCHEMY_DS", "Alchemia smoczych kamieni"),
	("NPC_LOCATION_HELPER_NPC_ROLE_TOOLTIP_COMBINE", "\xa3\xb9czenie"),
	("NPC_LOCATION_HELPER_NPC_ROLE_TOOLTIP_CUBE", "Wytwarzanie"),
	("NPC_LOCATION_HELPER_NPC_ROLE_TOOLTIP_DUNGEON", "Wej\x9ccie do lochu"),
	("NPC_LOCATION_HELPER_NPC_ROLE_TOOLTIP_EQUIPMENT_SHOP", "Sklep z ekwipunkiem"),
	("NPC_LOCATION_HELPER_NPC_ROLE_TOOLTIP_EVENT", "Wydarzenie"),
	("NPC_LOCATION_HELPER_NPC_ROLE_TOOLTIP_FISHING", "Rybo\xb3\xf3wstwo"),
	("NPC_LOCATION_HELPER_NPC_ROLE_TOOLTIP_GEM", "Gaya"),
	("NPC_LOCATION_HELPER_NPC_ROLE_TOOLTIP_GENERAL_SHOP", "Sklep og\xf3lny"),
	("NPC_LOCATION_HELPER_NPC_ROLE_TOOLTIP_GUILD_LAND", "Ziemie gildii"),
	("NPC_LOCATION_HELPER_NPC_ROLE_TOOLTIP_JOB", "Nauczyciel"),
	("NPC_LOCATION_HELPER_NPC_ROLE_TOOLTIP_MAIL", "Poczta"),
	("NPC_LOCATION_HELPER_NPC_ROLE_TOOLTIP_MINING", "G\xf3rnictwo"),
	("NPC_LOCATION_HELPER_NPC_ROLE_TOOLTIP_MOUNT", "Wierzchowce"),
	("NPC_LOCATION_HELPER_NPC_ROLE_TOOLTIP_NPC", "Pozostali NPC"),
	("NPC_LOCATION_HELPER_NPC_ROLE_TOOLTIP_PORTAL", "Portale"),
	("NPC_LOCATION_HELPER_NPC_ROLE_TOOLTIP_REFINE", "Ulepszanie"),
	("NPC_LOCATION_HELPER_NPC_ROLE_TOOLTIP_TELEPORT", "Teleportacja"),
	("NPC_LOCATION_HELPER_NPC_ROLE_TOOLTIP_WAREHOUSE", "Magazyn"),
	("NPC_LOCATION_HELPER_QUESTION_USE_TICKET", "Lokalizator NPC nie jest w\xb3\xb9czony. W\xb3\xb9cz go przedmiotem Lokalizator NPC."),
	("NPC_LOCATION_HELPER_QUEST_PROGRESS_STATE_ACCEPT", "Przyj\xeate"),
	("NPC_LOCATION_HELPER_QUEST_PROGRESS_STATE_COMPLETE", "Uko\xf1czone"),
	("NPC_LOCATION_HELPER_QUEST_PROGRESS_STATE_PROGRESS", "W toku"),
	("NPC_LOCATION_HELPER_WARP_TO_NPC_QUESTION_1", "Kamienie Teleportacji: %d. Teleportowa\xe6 do: %s?"),
	("TOOLTIP_NPC_LOCATION_HELPER_ELEMENT_ENCHANT", "\xafywio\xb3y: %s"),
	("TOOLTIP_NPC_LOCATION_HELPER_ELEMENT_ENCHANT_DARK", "Ciemno\x9c\xe6"),
	("TOOLTIP_NPC_LOCATION_HELPER_ELEMENT_ENCHANT_EARTH", "Ziemia"),
	("TOOLTIP_NPC_LOCATION_HELPER_ELEMENT_ENCHANT_ELECT", "B\xb3yskawica"),
	("TOOLTIP_NPC_LOCATION_HELPER_ELEMENT_ENCHANT_FIRE", "Ogie\xf1"),
	("TOOLTIP_NPC_LOCATION_HELPER_ELEMENT_ENCHANT_ICE", "L\xf3d"),
	("TOOLTIP_NPC_LOCATION_HELPER_ELEMENT_ENCHANT_NONE", "brak"),
	("TOOLTIP_NPC_LOCATION_HELPER_ELEMENT_ENCHANT_WIND", "Wiatr"),
	("TOOLTIP_NPC_LOCATION_HELPER_LEVEL", "Poziom potwora: %d"),
	("TOOLTIP_NPC_LOCATION_HELPER_MOB_GRADE", "Ranga potwora: %s"),
	("TARGET_LEVEL_PAWN", "Zwyk\xb3y"),
	("TARGET_LEVEL_S_PAWN", "Silny"),
	("TARGET_LEVEL_KNIGHT", "Elitarny"),
	("TARGET_LEVEL_S_KNIGHT", "Silny elitarny"),
	("TARGET_LEVEL_BOSS", "Boss"),
	("TARGET_LEVEL_KING", "Kr\xf3l"),
)

_PL_SCRIPT_TEXTS = (
	("NPC_HELPER_ATLAS_EXPAND_BUTTON_TOOLTIP", "Poka\xbf list\xea NPC"),
	("NPC_HELPER_ATLAS_SHRINK_BUTTON_TOOLTIP", "Ukryj list\xea NPC"),
	("NPC_HELPER_ATLAS_SWITCH_TO_NPC_LOCATION_HELPER_BUTTON_TOOLTIP", "Prze\xb3\xb9cz na Lokalizator NPC"),
	("NPC_HELPER_ATLAS_SWITCH_TO_SMALL_BUTTON_TOOLTIP", "Wr\xf3\xe6 do zwyk\xb3ej mapy"),
	("NPC_HELPER_ATLAS_TITLE", "Mapa \x9cwiata"),
	("NPC_HELPER_NPC_INFO_CONQUEROR_LEVEL", "Czemp. "),
	("NPC_HELPER_NPC_INFO_LEVEL", "Poz. "),
	("NPC_HELPER_NPC_INFO_MENU_NPC_LIST", "NPC"),
	("NPC_HELPER_NPC_INFO_MENU_SELECT_CATEGORY", "Wybierz region"),
	("NPC_HELPER_NPC_INFO_MENU_SELECT_MAP", "Wybierz map\xea"),
	("NPC_HELPER_NPC_INFO_TITLE", "Lokalizator NPC"),
	("NPC_LOCATION_HELPER_MOB_INFO_DROP_ITEM_INFO", "Mo\xbfliwy \xb3up"),
	("NPC_LOCATION_HELPER_MOB_INFO_MOB_INFO", "Potwory"),
	("NPC_LOCATION_HELPER_MOB_INFO_TITLE", "Przewodnik po potworach"),
	("NPC_LOCATION_HELPER_TOOLTIP_DROP_ITEM_INFO", "Przewodnik po potworach: co mog\xb9 upu\x9cci\xe6 potwory tej mapy."),
	("NPC_LOCATION_HELPER_TOOLTIP_GUILD_LAND", "Ziemie gildii: od\x9cwie\xbfa informacje (raz na minut\xea)."),
	("NPC_LOCATION_HELPER_TOOLTIP_MY_LOCATION", "Twoja pozycja: pokazuje map\xea, na kt\xf3rej jeste\x9c, i ustawia na niej widok."),
	("NPC_LOCATION_HELPER_TOOLTIP_SCALE_DOWN", "Oddal"),
	("NPC_LOCATION_HELPER_TOOLTIP_SCALE_UP", "Przybli\xbf"),
)

for (_k, _v) in _PL_LOCALE_TEXTS:
	if not hasattr(localeInfo, _k):
		setattr(localeInfo, _k, _v)
for (_k, _v) in _PL_SCRIPT_TEXTS:
	if not hasattr(uiScriptLocale, _k):
		setattr(uiScriptLocale, _k, _v)

if getattr(app, "ENABLE_EVENT_BANNER", 0):
	import ingameEventSystem

	_EVENT_FLAG_INGAME_TYPE = {
		"new_xmas_event": ingameEventSystem.INGAME_EVENT_TYPE_NEW_XMAS_EVENT,
		"easter_drop": ingameEventSystem.INGAME_EVENT_TYPE_EASTER_EVENT,
		"e_summer_event": ingameEventSystem.INGAME_EVENT_TYPE_ICECREAM_EVENT,
		"ramadan_drop": ingameEventSystem.INGAME_EVENT_TYPE_RAMADAN_EVENT,
		"halloween_box": ingameEventSystem.INGAME_EVENT_TYPE_HALLOWEEN_EVENT,
		"football_drop": ingameEventSystem.INGAME_EVENT_TYPE_FOOTBALL_EVENT,
		"medal_part_drop": ingameEventSystem.INGAME_EVENT_TYPE_OLYMPIC_EVENT,
		"valentine_drop": ingameEventSystem.INGAME_EVENT_TYPE_VALENTINE_DAY_EVENT,
		"e_late_summer": ingameEventSystem.INGAME_EVENT_TYPE_ROULETTE,
	}

	if getattr(app, "ENABLE_MINI_GAME_RUMI", 0):
		_EVENT_FLAG_INGAME_TYPE["mini_game_okey"] = ingameEventSystem.INGAME_EVENT_TYPE_OKEY
		_EVENT_FLAG_INGAME_TYPE["mini_game_okey_normal"] = ingameEventSystem.INGAME_EVENT_TYPE_OKEY_NORMAL

	if getattr(app, "ENABLE_MINI_GAME_YUTNORI", 0):
		_EVENT_FLAG_INGAME_TYPE["mini_game_yutnori"] = ingameEventSystem.INGAME_EVENT_TYPE_YUTNORI

	if getattr(app, "ENABLE_FLOWER_EVENT", 0):
		_EVENT_FLAG_INGAME_TYPE["e_flower_drop"] = ingameEventSystem.INGAME_EVENT_TYPE_FLOWER_EVENT

	if getattr(app, "ENABLE_MINI_GAME_CATCH_KING", 0):
		_EVENT_FLAG_INGAME_TYPE["mini_game_catchking"] = ingameEventSystem.INGAME_EVENT_TYPE_CATCHKING

	if getattr(app, "ENABLE_SNOWFLAKE_STICK_EVENT", 0):
		_EVENT_FLAG_INGAME_TYPE["snowflake_stick_event"] = ingameEventSystem.INGAME_EVENT_TYPE_SNOWFLAKE_STICK_EVENT
else:
	ingameEventSystem = None
	_EVENT_FLAG_INGAME_TYPE = {}

COMMON_MAP_PATH = "locale/common/map/"
HELPER_PATH = COMMON_MAP_PATH + "npc_location_helper/"
ROOT_PATH = "d:/ymir work/ui/game/npc_location_helper/"
PATTERN_BTN_CHANGE_PATH = "d:/ymir work/ui/pattern/btn_change_"
PATTERN_BTN_SHOW_PATH = "d:/ymir work/ui/pattern/btn_show01_"
NPC_LOCATION_DIRECTION_EFFECT = "d:/ymir work/effect/etc/npc_location/npc_location_direction.mse"

SHOW_NPC_LIST_POSITION = False

HELPER_ATLAS_W = 378
HELPER_ATLAS_H = 434
HELPER_NPC_W = 286
HELPER_LAYOUT_GAP = -5
# Reference 26.0.6: uiscript atlas_window + miniMap.SQUARED_ATLAS_SIZE = 352 (fixed).
# npcLocationHelper.ATLAS_SCALE_MIN/MAX = 1..3; uniform SetAtlasScale() only.
HELPER_ATLAS_VIEW_W = 352
HELPER_ATLAS_VIEW_H = 352
# Auto-fit may go below 1.0 so the whole map fits in 352x352 (no crop). User +/- stays 1..3.
HELPER_ATLAS_FIT_MIN_SCALE = 0.25


def _RefAtlasScaleLimits():
	return float(npcLocationHelper.ATLAS_SCALE_MIN), float(npcLocationHelper.ATLAS_SCALE_MAX)


def _ClampUserAtlasScale(scaleVal):

	sMin, sMax = _RefAtlasScaleLimits()

	s = float(scaleVal)

	if s < sMin:

		s = sMin

	if s > sMax:

		s = sMax

	return s


def _RefAtlasScaleLevels():

	# 5 levels => 4x zoom-in from 1.0 to 3.0 (matches C++ HELPER_ATLAS_SCALE_LEVELS)
	return (1.0, 1.5, 2.0, 2.5, 3.0)


def _NpLocMouseInRect(window):
	if not window:
		return False
	try:
		if not window.IsShow():
			return False
	except Exception:
		return False
	try:
		mx, my = wndMgr.GetMousePosition()
		wx, wy = window.GetGlobalPosition()
		ww = window.GetWidth()
		wh = window.GetHeight()
	except Exception:
		return False
	return wx <= mx <= wx + ww and wy <= my <= wy + wh


def _ClampFitAtlasScale(scaleVal):

	sMax = _RefAtlasScaleLimits()[1]

	s = float(scaleVal)

	if s < HELPER_ATLAS_FIT_MIN_SCALE:

		s = HELPER_ATLAS_FIT_MIN_SCALE

	if s > sMax:

		s = sMax

	return s

NPC_LIST_HIDE_MAP_INDICES = (375, 413, 414, 360)

NEAR_NPC_RADIUS_SQ = 150 * 150

ROLE_ICON_FILE = {
	1: "npc_role_icon_1_portal.sub",
	2: "npc_role_icon_2_equipment_shop.sub",
	3: "npc_role_icon_3_general_shop.sub",
	4: "npc_role_icon_4_warehouse.sub",
	5: "npc_role_icon_5_mail.sub",
	6: "npc_role_icon_6_teleport.sub",
	7: "npc_role_icon_7_refine.sub",
	8: "npc_role_icon_8_fishing.sub",
	9: "npc_role_icon_9_mining.sub",
	10: "npc_role_icon_10_alchemy_ds.sub",
	11: "npc_role_icon_11_cube.sub",
	12: "npc_role_icon_12_gem.sub",
	13: "npc_role_icon_13_combine.sub",
	14: "npc_role_icon_14_mount.sub",
	15: "npc_role_icon_15_dungeon.sub",
	16: "npc_role_icon_16_event.sub",
	17: "npc_role_icon_17_guild_land.sub",
	18: "npc_role_icon_18_job.sub",
	19: "npc_role_icon_19_npc.sub",
}

ROLE_LOC_KEY = {
	1: "NPC_LOCATION_HELPER_NPC_ROLE_TOOLTIP_PORTAL",
	2: "NPC_LOCATION_HELPER_NPC_ROLE_TOOLTIP_EQUIPMENT_SHOP",
	3: "NPC_LOCATION_HELPER_NPC_ROLE_TOOLTIP_GENERAL_SHOP",
	4: "NPC_LOCATION_HELPER_NPC_ROLE_TOOLTIP_WAREHOUSE",
	5: "NPC_LOCATION_HELPER_NPC_ROLE_TOOLTIP_MAIL",
	6: "NPC_LOCATION_HELPER_NPC_ROLE_TOOLTIP_TELEPORT",
	7: "NPC_LOCATION_HELPER_NPC_ROLE_TOOLTIP_REFINE",
	8: "NPC_LOCATION_HELPER_NPC_ROLE_TOOLTIP_FISHING",
	9: "NPC_LOCATION_HELPER_NPC_ROLE_TOOLTIP_MINING",
	10: "NPC_LOCATION_HELPER_NPC_ROLE_TOOLTIP_ALCHEMY_DS",
	11: "NPC_LOCATION_HELPER_NPC_ROLE_TOOLTIP_CUBE",
	12: "NPC_LOCATION_HELPER_NPC_ROLE_TOOLTIP_GEM",
	13: "NPC_LOCATION_HELPER_NPC_ROLE_TOOLTIP_COMBINE",
	14: "NPC_LOCATION_HELPER_NPC_ROLE_TOOLTIP_MOUNT",
	15: "NPC_LOCATION_HELPER_NPC_ROLE_TOOLTIP_DUNGEON",
	16: "NPC_LOCATION_HELPER_NPC_ROLE_TOOLTIP_EVENT",
	17: "NPC_LOCATION_HELPER_NPC_ROLE_TOOLTIP_GUILD_LAND",
	18: "NPC_LOCATION_HELPER_NPC_ROLE_TOOLTIP_JOB",
	19: "NPC_LOCATION_HELPER_NPC_ROLE_TOOLTIP_NPC",
}

CAT_LOCALE_KEY = (
	"NPC_LOCATION_HELPER_MAP_CATEGORY_HIDDEN",
	"NPC_LOCATION_HELPER_MAP_CATEGORY_EMPIRE_FIELD",
	"NPC_LOCATION_HELPER_MAP_CATEGORY_NEUTRAL",
	"NPC_LOCATION_HELPER_MAP_CATEGORY_EVIL_DRAGON_TERRITORY",
	"NPC_LOCATION_HELPER_MAP_CATEGORY_LABYRINTH",
	"NPC_LOCATION_HELPER_MAP_CATEGORY_EMPIRE_DUNGEON",
	"NPC_LOCATION_HELPER_MAP_CATEGORY_NEW_WORLD_FIELD",
	"NPC_LOCATION_HELPER_MAP_CATEGORY_NEW_WORLD_DUNGEON",
)


def _Lc(key, fb):
	try:
		return getattr(localeInfo, key)
	except Exception:
		return fb


def _UiScr(key, fb):

	try:

		return getattr(uiScriptLocale, key)

	except Exception:

		return fb


def _AtlasInterfaceTip(key, fb=""):
	# NPC helper atlas title/tooltips live in locale_interface.txt (uiScriptLocale).
	tip = _UiScr(key, "")
	if tip:
		return tip
	try:
		return getattr(localeInfo, key)
	except Exception:
		return fb


def LcTry(locKey, fbText):

	try:

		return getattr(localeInfo, locKey)

	except Exception:

		return fbText


class MapTextTip(ui.Window):

	def __init__(self):
		self.textLine = None
		ui.Window.__init__(self)
		self.AddFlag("float")
		tx = ui.TextLine()
		tx.SetParent(self)
		tx.SetOutline()
		tx.SetHorizontalAlignRight()
		tx.Show()
		self.textLine = tx

	def __del__(self):
		ui.Window.__del__(self)

	def SetText(self, txt):
		textLine = getattr(self, "textLine", None)
		if textLine:
			textLine.SetText(txt)

	def Show(self):
		ui.Window.Show(self)
		textLine = getattr(self, "textLine", None)
		if textLine:
			textLine.Show()

	def Hide(self):
		textLine = getattr(self, "textLine", None)
		if textLine:
			textLine.Hide()
		ui.Window.Hide(self)

	def SetTooltipPosition(self, px, py):
		textLine = getattr(self, "textLine", None)
		if not textLine:
			return
		try:
			if localeInfo.IsARABIC():
				sw, uh = textLine.GetTextSize()
				textLine.SetPosition(px - sw - 5, py)
			else:
				textLine.SetPosition(px - 5, py)
		except Exception:
			textLine.SetPosition(px - 5, py)

	def SetTextColor(self, clr):
		textLine = getattr(self, "textLine", None)
		if not textLine:
			return
		try:
			textLine.SetPackedFontColor(clr)
		except Exception:
			pass

	def GetTextSize(self):
		textLine = getattr(self, "textLine", None)
		if not textLine:
			return (0, 0)
		return textLine.GetTextSize()


class NPCLocationHelperUtil(object):

	_mapInfos = None
	_npcByMap = None
	_mobByMap = None
	_mobDrops = None
	_eventNpcPool = None
	_eventFlagCache = None
	_eventFlagNames = None
	_locDone = False

	_EVENT_FLAG_ALIASES = {
		"easter_egg": "easter_drop",
		"e_summer_spawn": "e_summer_event",
	}

	@classmethod
	def ReadPackedLines(cls, relPath):

		fp = COMMON_MAP_PATH + relPath.replace("\\", "/")
		arr = []

		try:
			pack = npcLocationHelper.ReadTextFile(fp)
		except Exception:
			pack = None

		if pack:
			for rawChunk in pack:
				txt = ""

				try:
					if isinstance(rawChunk, unicode):
						txt = rawChunk.strip()
					else:
						txt = str(rawChunk).strip()
				except Exception:
					txt = ""

				txt = txt.rstrip("\r\n")

				arr.append(txt)

			return arr

		try:

			fl = open(fp, "r")

			try:
				for ln in fl:
					arr.append(ln.strip().rstrip("\r\n"))
			finally:

				fl.close()

		except IOError:
			pass

		return arr

	@classmethod
	def _ResolveEventFlagName(cls, flagName):
		try:
			name = str(flagName).strip()
		except Exception:
			return ""
		if not name:
			return ""
		seen = set()
		while name in cls._EVENT_FLAG_ALIASES and name not in seen:
			seen.add(name)
			name = cls._EVENT_FLAG_ALIASES[name]
		return name

	@classmethod
	def _ParseEventFlagSpec(cls, flagSpec):
		if flagSpec is None:
			return ("", None)
		try:
			text = str(flagSpec).strip()
		except Exception:
			return ("", None)
		if not text:
			return ("", None)
		if "," in text:
			parts = text.split(",", 1)
			try:
				return (cls._ResolveEventFlagName(parts[0]), int(parts[1].strip()))
			except Exception:
				return (cls._ResolveEventFlagName(parts[0]), None)
		return (cls._ResolveEventFlagName(text), None)

	@classmethod
	def _RegisterEventFlagName(cls, flagSpec):
		name, _unused = cls._ParseEventFlagSpec(flagSpec)
		if not name:
			return
		if cls._eventFlagNames is None:
			cls._eventFlagNames = set()
		cls._eventFlagNames.add(name)

	@classmethod
	def GetEventFlagValue(cls, flagName):
		cls.Load()
		name = cls._ResolveEventFlagName(flagName)
		if not name:
			return 0

		val = 0
		try:
			if cls._eventFlagCache and name in cls._eventFlagCache:
				val = int(cls._eventFlagCache[name])
		except Exception:
			val = 0

		evType = _EVENT_FLAG_INGAME_TYPE.get(name)
		if evType is not None and ingameEventSystem:
			try:
				if ingameEventSystem.GetInGameEventEnable(evType):
					igVal = int(ingameEventSystem.GetInGameEventEndTime(evType))
					if igVal <= 0:
						igVal = 1
					if igVal > val:
						val = igVal
			except Exception:
				pass
		return val

	@classmethod
	def IsEventNpcVisible(cls, startFlagSpec, endFlagSpec=None):
		startName, startExpected = cls._ParseEventFlagSpec(startFlagSpec)
		if not startName:
			return False

		startVal = cls.GetEventFlagValue(startName)
		if startExpected is not None:
			if startVal != startExpected:
				return False
		elif startVal <= 0:
			return False

		if endFlagSpec:
			endName, endExpected = cls._ParseEventFlagSpec(endFlagSpec)
			if endName:
				endVal = cls.GetEventFlagValue(endName)
				if endExpected is not None:
					if endVal == endExpected:
						return False
				elif endVal > 0:
					return False
		return True

	@classmethod
	def _IsTrackedEventFlag(cls, flagName):
		if cls._eventFlagNames is None:
			return False
		try:
			name = str(flagName).strip()
		except Exception:
			return False
		if not name:
			return False
		if name in cls._eventFlagNames:
			return True
		resolved = cls._ResolveEventFlagName(name)
		if resolved in cls._eventFlagNames:
			return True
		for alias, target in cls._EVENT_FLAG_ALIASES.items():
			if target == name and alias in cls._eventFlagNames:
				return True
		return False

	@classmethod
	def SetEventFlag(cls, flagName, flagValue):
		cls.Load()
		if not cls._IsTrackedEventFlag(flagName):
			return False
		if cls._eventFlagCache is None:
			cls._eventFlagCache = {}
		try:
			newVal = int(flagValue)
		except Exception:
			newVal = 0
		storeKeys = set()
		try:
			raw = str(flagName).strip()
			if raw:
				storeKeys.add(raw)
		except Exception:
			pass
		resolved = cls._ResolveEventFlagName(flagName)
		if resolved:
			storeKeys.add(resolved)
		oldVal = 0
		for key in storeKeys:
			oldVal = cls._eventFlagCache.get(key, oldVal)
		changed = False
		for key in storeKeys:
			if cls._eventFlagCache.get(key, 0) != newVal:
				changed = True
			cls._eventFlagCache[key] = newVal
		if changed:
			cls.RefreshOpenNpcLists()
		return True

	@classmethod
	def TrySetEventFlagFromCommand(cls, commandName, flagValue):
		if not commandName:
			return False
		cls.Load()
		if not cls._IsTrackedEventFlag(commandName):
			return False
		return cls.SetEventFlag(commandName, flagValue)

	@classmethod
	def RefreshOpenNpcLists(cls):
		try:
			if cls._npLocAtlasRef and cls._npLocAtlasRef.IsShow():
				cls._npLocAtlasRef.RefreshHelperStatus()
		except Exception:
			pass

	@classmethod
	def BindAtlasWindow(cls, atlasWnd):
		cls._npLocAtlasRef = atlasWnd

	@classmethod
	def _LoadEventNpcList(cls):
		cls._eventNpcPool = []
		cls._eventFlagNames = set()
		cls._eventFlagCache = {}

		for ln in cls.ReadPackedLines("npc_location_helper/event_npc_list.txt"):
			if not ln or ln.startswith("#"):
				continue

			if "\t" in ln:
				parts = [col.strip() for col in ln.split("\t")]
			else:
				parts = ln.split()

			if len(parts) < 5:
				continue

			try:
				mIx = int(parts[0])
				gx = int(parts[1])
				gy = int(parts[2])
				vnum = int(parts[3])
			except Exception:
				continue

			startFlag = parts[4]
			endFlag = parts[5] if len(parts) >= 6 else None
			cls._RegisterEventFlagName(startFlag)
			if endFlag:
				cls._RegisterEventFlagName(endFlag)

			nm = ""
			try:
				nm = nonplayer.GetMonsterName(vnum)
			except Exception:
				nm = ""
			if not nm:
				nm = "%d" % vnum

			cls._eventNpcPool.append(
				{
					"map_index": mIx,
					"start_flag": startFlag,
					"end_flag": endFlag,
					"npc": {
						"map_index": mIx,
						"vnum": vnum,
						"x": gx,
						"y": gy,
						"icon": 16,
						"name": nm,
						"land_id": 0,
						"quest_state": -1,
						"is_event_npc": 1,
					},
				}
			)

	@classmethod
	def _AppendActiveEventNpcs(cls, mapIx, pool):
		if not cls._eventNpcPool:
			return pool

		try:
			targetMap = int(mapIx)
		except Exception:
			return pool

		eventRows = []
		seen = set()

		for ev in cls._eventNpcPool:
			try:
				if int(ev.get("map_index", -1)) != targetMap:
					continue
			except Exception:
				continue
			if not cls.IsEventNpcVisible(ev.get("start_flag"), ev.get("end_flag")):
				continue
			npc = ev.get("npc")
			if not npc:
				continue
			key = (int(npc.get("vnum", 0)), int(npc.get("x", 0)), int(npc.get("y", 0)))
			if key in seen:
				continue
			seen.add(key)
			eventRows.append(npc)

		if not eventRows:
			return pool

		out = list(eventRows)
		for row in pool:
			try:
				key = (int(row.get("vnum", 0)), int(row.get("x", 0)), int(row.get("y", 0)))
			except Exception:
				out.append(row)
				continue
			if key in seen:
				continue
			seen.add(key)
			out.append(row)
		return out

	_npLocAtlasRef = None

	@classmethod
	def Load(cls):

		if cls._mapInfos is not None:
			return

		cls.InitializeLoca()

		cls._mapInfos = []

		cls._npcByMap = {}

		cls._mobByMap = {}

		cls._mobDrops = {}

		inGrp = False

		for ln in cls.ReadPackedLines("npc_location_helper/npc_location_helper.txt"):

			if not ln or ln.startswith("#"):

				continue

			if ln.startswith("Group") and ("MapInfo" in ln):
				inGrp = True

				continue

			if inGrp and ln.startswith("}"):
				break

			if not inGrp or ln.startswith("{"):

				continue

			if "\t" in ln:

				p = [col.strip() for col in ln.split("\t")]

			else:

				p = ln.split()

			if len(p) < 13:
				continue

			mIx = int(p[0])

			row = {}

			row["map_index"] = mIx

			row["map_name"] = p[1]

			row["map_dir"] = p[2]

			row["category"] = int(p[3])

			row["min_level"] = int(p[4])

			row["min_c_level"] = int(p[5])

			row["recommended_min"] = int(p[6])

			row["recommended_max"] = int(p[7])

			row["empire"] = int(p[8])

			row["show_atlas"] = int(p[9])

			row["show_npc_list"] = int(p[10])

			row["warp_need_yang"] = int(p[11])

			row["warp_need_item"] = p[12]

			cls._mapInfos.append(row)

			if row["show_npc_list"] and (mIx not in NPC_LIST_HIDE_MAP_INDICES):
				ptPathRel = "%s_point.txt" % row["map_dir"]

				pool = []

				for pl in cls.ReadPackedLines(ptPathRel):

					if not pl or pl.startswith("#"):
						continue

					toks = pl.split()

					if len(toks) < 6:

						continue

					try:

						if int(toks[4]) == 0:

							continue

						gx = int(toks[1]) // 100

						gy = int(toks[2]) // 100

						vnum = int(toks[3])

						role = int(toks[5])
						qst = -1
						if len(toks) >= 7:
							try:
								qst = int(toks[6])
							except Exception:
								qst = -1

					except Exception:

						continue

					nm = ""

					try:

						nm = nonplayer.GetMonsterName(vnum)

					except Exception:

						nm = ""

					if not nm:

						nm = "%d" % vnum
					elif int(role) == 1:
						# Portal names often include extra coords; keep only the map slug token.
						try:
							nm = nm.split()[0]
						except Exception:
							pass

					pool.append(
						{
							"map_index": mIx,
							"vnum": vnum,
							"x": gx,

							"y": gy,

							"icon": role,

							"name": nm,

							"land_id": 0,
							"quest_state": qst,

						}
					)

				cls._npcByMap[mIx] = pool

		for ln2 in cls.ReadPackedLines("npc_location_helper/map_mob_list.txt"):

			if not ln2 or ln2.startswith("#"):

				continue

			tp = ln2.split("\t")

			if len(tp) < 2:

				tp = ln2.split()

				if len(tp) < 2:

					continue

			try:

				mm = int(tp[0])

				mv = int(tp[1])

			except Exception:

				continue

			posArr = []

			for pairTxt in tp[2:]:

				k = pairTxt.find(",")

				if k < 0:

					continue

				try:

					ax = int(pairTxt[:k].strip())

					ay = int(pairTxt[k + 1 :].strip())

				except Exception:

					continue

				posArr.append((ax, ay))

			if mm not in cls._mobByMap:

				cls._mobByMap[mm] = []

			cls._mobByMap[mm].append({"mob_vnum": mv, "positions": tuple(posArr)})

		curMobDrop = None

		for ln3 in cls.ReadPackedLines("npc_location_helper/mob_drop_item.txt"):

			if not ln3 or ln3.startswith("#"):
				continue

			toks3 = ln3.split()

			if not toks3:
				continue

			h = toks3[0]

			if h == "Group" or h == "{":
				continue

			if h == "}":
				curMobDrop = None

				continue

			if h == "Mob" and len(toks3) >= 2:

				try:

					curMobDrop = int(toks3[1])

				except Exception:

					curMobDrop = None

				if curMobDrop is not None:

					if curMobDrop not in cls._mobDrops:

						cls._mobDrops[curMobDrop] = []

				continue

			if curMobDrop is None:

				continue

			for tail in toks3[1:]:

				try:

					cls._mobDrops[curMobDrop].append(int(tail))

				except Exception:

					pass

		cls._LoadEventNpcList()

	@classmethod

	def InitializeLoca(cls):

		if cls._locDone:

			return

		cls._locDone = True

	@classmethod

	def AppendChat(cls, msg):

		try:
			chat.AppendChat(chat.CHAT_TYPE_INFO, msg)
		except Exception:
			pass

	@classmethod

	def MapInfos(cls):

		cls.Load()

		return cls._mapInfos

	@classmethod

	def VisibleNpcMapsFiltered(cls):

		out = []

		for m in cls.MapInfos():

			if m["show_npc_list"] and (m["map_index"] not in NPC_LIST_HIDE_MAP_INDICES):

				out.append(m)

		return out

	@classmethod

	def ByCategoryBuckets(cls):

		cls.Load()

		buckets = [[] for _unused in xrange(8)]

		for mx in cls.VisibleNpcMapsFiltered():

			cat = mx["category"]

			if cat < 0 or cat >= 8:

				continue

			buckets[cat].append(mx)

		return buckets

	@classmethod

	def NpcsOnMap(cls, mapIx):

		cls.Load()

		pool = cls._npcByMap.get(mapIx, [])
		return cls._AppendActiveEventNpcs(mapIx, pool)

	@classmethod

	def MobsOnMap(cls, mapIx):

		cls.Load()

		return cls._mobByMap.get(mapIx, [])

	@classmethod

	def DropsForMob(cls, mobV):

		cls.Load()

		seq = cls._mobDrops.get(int(mobV), [])

		seen = set()

		uniq = []

		for vv in seq:

			if vv in seen:

				continue

			seen.add(vv)

			uniq.append(vv)

		return uniq

	@classmethod
	def GetItemNameByVnumSafe(cls, itemVnum):
		try:
			vv = int(itemVnum)
		except Exception:
			return ""
		try:
			api = getattr(item, "GetItemNameByVnum", None)
			if callable(api):
				nm = api(vv)
				if nm:
					return str(nm)
		except Exception:
			pass
		try:
			item.SelectItem(vv)
			nm = item.GetItemName()
			if nm:
				return str(nm)
		except Exception:
			pass
		return "%d" % vv

	@classmethod
	def __SelectMobSafe(cls, mobVnum):
		try:
			vv = int(mobVnum)
		except Exception:
			return False
		try:
			selectApi = getattr(nonplayer, "SelectMob", None)
			if callable(selectApi):
				selectApi(vv)
				return True
		except Exception:
			pass
		return False

	@classmethod
	def GetMobLevelTooltipLine(cls, mobVnum):
		if not cls.__SelectMobSafe(mobVnum):
			return ""
		try:
			lvl = int(nonplayer.GetLevel())
		except Exception:
			return ""
		shell = _Lc("TOOLTIP_NPC_LOCATION_HELPER_LEVEL", "Lv%d")
		try:
			return shell % lvl
		except Exception:
			return shell

	@classmethod
	def GetMobGradeTooltipLine(cls, mobVnum):
		api = getattr(nonplayer, "GetMonsterRank", None)
		if api is None:
			api = getattr(nonplayer, "GetRankOnVnum", None)
		if not callable(api):
			return ""
		try:
			rnk = int(api(int(mobVnum)))
		except Exception:
			return ""
		rankLocaleMap = {
			int(getattr(nonplayer, "PAWN", 0)): "TARGET_LEVEL_PAWN",
			int(getattr(nonplayer, "S_PAWN", 1)): "TARGET_LEVEL_S_PAWN",
			int(getattr(nonplayer, "KNIGHT", 2)): "TARGET_LEVEL_KNIGHT",
			int(getattr(nonplayer, "S_KNIGHT", 3)): "TARGET_LEVEL_S_KNIGHT",
			int(getattr(nonplayer, "BOSS", 4)): "TARGET_LEVEL_BOSS",
			int(getattr(nonplayer, "KING", 5)): "TARGET_LEVEL_KING",
		}
		gradeKey = rankLocaleMap.get(rnk, "")
		if not gradeKey:
			return ""
		gradeText = _Lc(gradeKey, "")
		if not gradeText:
			return ""
		shell = _Lc("TOOLTIP_NPC_LOCATION_HELPER_MOB_GRADE", "%s")
		try:
			return shell % gradeText
		except Exception:
			return gradeText

	@classmethod
	def GetMobElementTooltipLine(cls, mobVnum):
		if getattr(app, "ENABLE_ELEMENT_ADD", 0):
			try:
				txt = cls.GetElementEnchantText(int(mobVnum))
			except Exception:
				txt = ""
			if txt:
				return txt
		noneLbl = _Lc("TOOLTIP_NPC_LOCATION_HELPER_ELEMENT_ENCHANT_NONE", "none")
		shell = _Lc("TOOLTIP_NPC_LOCATION_HELPER_ELEMENT_ENCHANT", "%s")
		try:
			return shell % noneLbl
		except Exception:
			return shell

	@classmethod
	def ShowMobGuideMobTooltip(cls, tip, mobVnum):
		if not tip:
			return
		lines = []
		line = cls.GetMobLevelTooltipLine(mobVnum)
		if line:
			lines.append(line)
		line = cls.GetMobGradeTooltipLine(mobVnum)
		if line:
			lines.append(line)
		line = cls.GetMobElementTooltipLine(mobVnum)
		if line:
			lines.append(line)
		if not lines:
			return
		try:
			tip.ClearToolTip()
			for ln in lines:
				tip.AppendTextLine(ln, uiToolTip.ToolTip.FONT_COLOR, True)
			tip.ResizeToolTip()
			tip.ShowToolTip()
		except Exception:
			try:
				tip.Show()
			except Exception:
				pass

	@classmethod
	def ShowMobGuideItemTooltip(cls, itemTip, itemVnum):
		if not itemTip or not itemVnum:
			return
		try:
			vv = int(itemVnum)
		except Exception:
			return
		oldPrivateSearch = None
		try:
			if hasattr(itemTip, "ClearToolTip"):
				itemTip.ClearToolTip()
			if hasattr(itemTip, "isPrivateSearchItem"):
				oldPrivateSearch = bool(itemTip.isPrivateSearchItem)
				itemTip.isPrivateSearchItem = True
			metinSlot = []
			for i in xrange(player.METIN_SOCKET_MAX_NUM):
				metinSlot.append(0)
			attrSlot = []
			for i in xrange(player.ATTRIBUTE_SLOT_MAX_NUM):
				attrSlot.append((0, 0))
			if hasattr(itemTip, "AddItemData"):
				itemTip.AddItemData(vv, metinSlot, attrSlot)
			elif hasattr(itemTip, "SetItemToolTip"):
				itemTip.SetItemToolTip(vv)
			itemTip.ShowToolTip()
		except Exception:
			pass
		finally:
			try:
				if oldPrivateSearch is not None:
					itemTip.isPrivateSearchItem = oldPrivateSearch
			except Exception:
				pass

	@classmethod

	def GetMapCategoryText(cls, catIx):

		if catIx < 0 or catIx >= len(CAT_LOCALE_KEY):

			return ""

		k = CAT_LOCALE_KEY[catIx]

		# Prefer localeInfo, then uiScriptLocale; avoid raw key suffix fallback.
		return _Lc(k, _UiScr(k, ""))

	@classmethod

	def GetMapNameLoca(cls, mx):

		if not isinstance(mx, dict):

			try:

				return localeInfo.MINIMAP_ZONE_NAME_DICT.get(mx, mx)

			except Exception:

				return mx

		mapDir = mx.get("map_dir", "")

		mapIx = mx.get("map_index")

		try:

			if mapDir and mapDir in localeInfo.MINIMAP_ZONE_NAME_DICT:

				return localeInfo.MINIMAP_ZONE_NAME_DICT[mapDir]
			# MT2009: our folders keep their case (Metin2_map_CapeDragonHead)
			for (zk, zv) in localeInfo.MINIMAP_ZONE_NAME_DICT.items():
				if mapDir and str(zk).lower() == mapDir.lower():
					return zv

		except Exception:

			pass

		try:

			if mapIx is not None and hasattr(localeInfo, "MINIMAP_ZONE_NAME_DICT_BY_IDX"):

				if mapIx in localeInfo.MINIMAP_ZONE_NAME_DICT_BY_IDX:

					return localeInfo.MINIMAP_ZONE_NAME_DICT_BY_IDX[mapIx]

		except Exception:

			pass

		return mapDir or mx.get("map_name", "")

	@classmethod

	def GetMapRecommendedLevelText(cls, mx):

		mi = mx.get("recommended_min", 0)

		ma = mx.get("recommended_max", 0)

		mcl = mx.get("min_c_level", 0)

		# Data rule: recommended_level_min == 0 means do not show a level band (e.g. market map).
		if mi == 0:

			return ""

		if ma == 0:

			return ""

		if mcl > 0:

			lvPrefix = _UiScr("NPC_HELPER_NPC_INFO_CONQUEROR_LEVEL", "")

			if not lvPrefix:

				lvPrefix = _Lc("NPC_HELPER_NPC_INFO_CONQUEROR_LEVEL", "C-Lvl")

		else:

			lvPrefix = _UiScr("NPC_HELPER_NPC_INFO_LEVEL", "")

			if not lvPrefix:

				lvPrefix = _Lc("NPC_HELPER_NPC_INFO_LEVEL", "Lv")

		shell = _UiScr("NPC_HELPER_ATLAS_SCALETEXT_SHELL", "")

		if shell:

			try:

				return shell % (lvPrefix, mi, ma)

			except Exception:

				try:

					return shell % (mi, ma)

				except Exception:

					pass

		if mi == ma:

			return "%s%d" % (lvPrefix, mi)

		return "%s%d~%d" % (lvPrefix, mi, ma)

	@classmethod

	def GetMapDropDownListTitle(cls, mx):

		name = cls.GetMapNameLoca(mx)

		lvl = cls.GetMapRecommendedLevelText(mx)

		if lvl:

			return "%s(%s)" % (name, lvl)

		return name

	@classmethod

	def GetNPCRoleIconFilePath(cls, roleIx):

		fname = ROLE_ICON_FILE.get(int(roleIx), ROLE_ICON_FILE[19])

		return ROOT_PATH + fname

	@classmethod

	def GetNPCRoleTooltipText(cls, roleIx):

		k = ROLE_LOC_KEY.get(int(roleIx), ROLE_LOC_KEY[19])

		return getattr(localeInfo, k, "")

	@classmethod

	def GetCanWarpToNPCStateText(cls, resultIdx):

		if int(resultIdx) == int(npcLocationHelper.RESULT_OK):
			return ""

		if int(resultIdx) == int(npcLocationHelper.RESULT_COOLDOWN):

			sec = max(0, int(npcLocationHelper.GetCooldownRemain()))

			if sec < 60:

				txt = _Lc(
					"NPC_LOCATION_HELPER_CAN_WARP_TO_NPC_STATE_FALSE_COOLTIME_LESS_THAN_1M",
					"Wait before warp",
				)

				return txt

			mins = max(1, sec // 60)

			txt = _Lc(
				"NPC_LOCATION_HELPER_CAN_WARP_TO_NPC_STATE_FALSE_COOLTIME",
				"No warp %d min",
			)

			try:
				return txt % mins

			except Exception:

				return txt

		resultLocale = {
			npcLocationHelper.RESULT_NOT_ACTIVE: "NPC_LOCATION_HELPER_MESSAGE_CANNOT_USE_STONE_OF_WARP_DISABLED",
			npcLocationHelper.RESULT_CANNOT_USE: "NPC_LOCATION_HELPER_MESSAGE_CANNOT_WARP_TO_NPC_NOW",
			npcLocationHelper.RESULT_INVALID_TARGET: "NPC_LOCATION_HELPER_MESSAGE_CANNOT_WARP_TO_NPC_NOW",
			npcLocationHelper.RESULT_LEVEL_LIMIT: "NPC_LOCATION_HELPER_CAN_WARP_TO_NPC_STATE_FALSE_LEVEL_LIMIT",
			npcLocationHelper.RESULT_EMPIRE_LIMIT: "NPC_LOCATION_HELPER_CAN_WARP_TO_NPC_STATE_FALSE_DIFFERENT_EMPIRE",
			npcLocationHelper.RESULT_NEED_ITEM: "NPC_LOCATION_HELPER_MESSAGE_NOT_ENOUGH_STONE_OF_WARP",
			npcLocationHelper.RESULT_NEED_YANG: "NPC_LOCATION_HELPER_CAN_WARP_TO_NPC_STATE_FALSE_GOLD",
		}

		locKey = resultLocale.get(int(resultIdx), "")

		if locKey:

			try:

				return getattr(localeInfo, locKey, "")

			except Exception:

				pass

		fallbackMsg = ""

		try:

			fallbackMsg = getattr(localeInfo, "NPC_LOCATION_HELPER_CANNOT_WARP_TO_NPC_NOW", "")

		except Exception:

			pass

		if fallbackMsg:

			return fallbackMsg

		return ""

	@classmethod

	def GetQuestProgressStateText(cls, st):

		for pair in ((0, "NPC_LOCATION_HELPER_QUEST_PROGRESS_STATE_ACCEPT"),
			(1, "NPC_LOCATION_HELPER_QUEST_PROGRESS_STATE_PROGRESS"),
			(2, "NPC_LOCATION_HELPER_QUEST_PROGRESS_STATE_COMPLETE"),

		):

			if st == pair[0]:
				try:

					return getattr(localeInfo, pair[1], "")

				except Exception:

					return ""

		return ""

	@classmethod

	def GetMobGradeText(cls, mobVnum):

		api = getattr(nonplayer, "GetMonsterRank", None)

		if api is None:

			api = getattr(nonplayer, "GetRankOnVnum", None)


		if callable(api):

			try:

				rnk = int(api(int(mobVnum)))

				txtMap = {
					int(getattr(nonplayer, "PAWN", 0)): "PAWN",
					int(getattr(nonplayer, "S_PAWN", 1)): "S_PAWN",
					int(getattr(nonplayer, "KNIGHT", 2)): "KNIGHT",
					int(getattr(nonplayer, "S_KNIGHT", 3)): "S_KNIGHT",
					int(getattr(nonplayer, "BOSS", 4)): "BOSS",
					int(getattr(nonplayer, "KING", 5)): "KING",
				}

				ll = txtMap.get(rnk, "")

				if ll:

					shell = _Lc(
						"TOOLTIP_NPC_LOCATION_HELPER_MOB_GRADE",
						"%s",

					)

					try:

						return shell % ll

					except Exception:

						return ll

			except Exception:

				pass

		try:

			okSel = cls.__SelectMobSafe(int(mobVnum))

			if okSel:

				lvtxt = ""

				try:

					lvtxt = getattr(localeInfo, "TOOLTIP_NPC_LOCATION_HELPER_LEVEL", "Lv%d") % (
						int(nonplayer.GetLevel()))

				except Exception:

					lvtxt = ""

				if lvtxt:

					return lvtxt

		except Exception:

			pass

		return ""

	@classmethod

	def GetElementEnchantText(cls, mv):

		if not getattr(app, "ENABLE_ELEMENT_ADD", 0):

			return ""

		try:

			if not cls.__SelectMobSafe(int(mv)):
				return ""
		except Exception:

			return ""

		partsOut = []

		keySeq = ()

		keySeq += (
			(getattr(nonplayer, "MOB_ENCHANT_ELECT", 0)),
			(getattr(nonplayer, "MOB_ENCHANT_FIRE", 0)),
			(getattr(nonplayer, "MOB_ENCHANT_ICE", 0)),
			(getattr(nonplayer, "MOB_ENCHANT_WIND", 0)),
			(getattr(nonplayer, "MOB_ENCHANT_EARTH", 0)),
			(getattr(nonplayer, "MOB_ENCHANT_DARK", 0)),
		)

		txtKeys = ()

		txtKeys += (
			"TOOLTIP_NPC_LOCATION_HELPER_ELEMENT_ENCHANT_ELECT",
			"TOOLTIP_NPC_LOCATION_HELPER_ELEMENT_ENCHANT_FIRE",

			"TOOLTIP_NPC_LOCATION_HELPER_ELEMENT_ENCHANT_ICE",
			"TOOLTIP_NPC_LOCATION_HELPER_ELEMENT_ENCHANT_WIND",
			"TOOLTIP_NPC_LOCATION_HELPER_ELEMENT_ENCHANT_EARTH",
			"TOOLTIP_NPC_LOCATION_HELPER_ELEMENT_ENCHANT_DARK",
		)

		for kk in xrange(len(keySeq)):
			el = keySeq[kk]

			labelKey = ""

			try:

				labelKey = txtKeys[kk]

			except Exception:

				labelKey = ""

			try:

				val = int(nonplayer.GetElement(el))

			except Exception:

				val = 0

			if val:

				part = ""

				try:

					part = getattr(localeInfo, labelKey, "")

				except Exception:

					part = ""

				if part:

					partsOut.append(part)

		if not partsOut:

			noneLbl = ""

			try:

				noneLbl = _Lc(
					"TOOLTIP_NPC_LOCATION_HELPER_ELEMENT_ENCHANT_NONE",
					"none",

				)

			except Exception:

				noneLbl = "none"

			partsJoined = noneLbl

		else:

			partsJoined = ", ".join(partsOut)

		shell = ""

		try:

			shell = getattr(localeInfo, "TOOLTIP_NPC_LOCATION_HELPER_ELEMENT_ENCHANT", "%s")

			return shell % partsJoined

		except Exception:

			return partsJoined


	@classmethod

	def GetMapInfos(cls):

		return cls.MapInfos()

	@classmethod

	def GetNPCInfos(cls, mapIx):

		return cls.NpcsOnMap(mapIx)

	@classmethod
	def FindMapInfoByIndex(cls, mapIx):
		try:
			mx = int(mapIx)
		except Exception:
			return None
		for row in cls.MapInfos():
			try:
				if int(row.get("map_index", -1)) == mx:
					return row
			except Exception:
				pass
		return None

	@classmethod
	def FindMapInfoBySlug(cls, slugText):
		try:
			s = str(slugText)
		except Exception:
			s = ""
		if not s:
			return None
		for row in cls.MapInfos():
			try:
				if row.get("map_dir") == s or row.get("map_name") == s:
					return row
				if str(row.get("map_dir", "")).lower() == s.lower(): # MT2009: case of the folder names
					return row
			except Exception:
				pass
		return None

	@classmethod
	def ReadNpcPointFileByMapDir(cls, mapDirSlug, mapIndexFallback=0):
		try:
			mapDir = str(mapDirSlug)
		except Exception:
			mapDir = ""
		if not mapDir:
			return []

		pool = []
		ptPathRel = "%s_point.txt" % mapDir
		for pl in cls.ReadPackedLines(ptPathRel):
			if not pl or pl.startswith("#"):
				continue
			toks = pl.split()
			if len(toks) < 6:
				continue
			try:
				if int(toks[4]) == 0:
					continue
				gx = int(toks[1]) // 100
				gy = int(toks[2]) // 100
				vnum = int(toks[3])
				role = int(toks[5])
			except Exception:
				continue

			nm = ""
			try:
				nm = nonplayer.GetMonsterName(vnum)
			except Exception:
				nm = ""
			if not nm:
				nm = "%d" % vnum
			elif int(role) == 1:
				try:
					nm = nm.split()[0]
				except Exception:
					pass

			try:
				mi = int(mapIndexFallback)
			except Exception:
				mi = 0

			pool.append(
				{
					"map_index": mi,
					"vnum": vnum,
					"x": gx,
					"y": gy,
					"icon": role,
					"name": nm,
					"land_id": 0,
				}
			)
		return cls._AppendActiveEventNpcs(mapIndexFallback, pool)


class ListView(ui.Window):

	def __init__(self):
		ui.Window.__init__(self)
		self._w = 0
		self._vh = 0
		self._ih = 20
		self._nodes = []
		self._sel = -1
		self.scroll = None
		self.body = None
		self.clipWindow = None
		self.cbScroll = lambda: None

	def __del__(self):
		ui.Window.__del__(self)

	def MakeListView(self, w, viewH, itemH):
		self._w = max(40, int(w))

		self._vh = max(20, int(viewH))

		self._ih = max(8, int(itemH))

		sbWide = getattr(ui.ScrollBar, "SCROLLBAR_WIDTH", 17)

		bw = max(10, self._w - sbWide - 2)

		if getattr(app, "ENABLE_CLIP_MASK", 0):
			cw = ui.Window()
			cw.SetParent(self)
			cw.SetPosition(0, 0)
			cw.SetSize(bw, self._vh)
			cw.Show()
			self.clipWindow = cw

		bd = ui.Window()

		if self.clipWindow:
			bd.SetParent(self.clipWindow)
		else:
			bd.SetParent(self)

		bd.SetPosition(0, 0)

		bd.SetSize(bw, self._vh)

		bd.Show()

		self.body = bd

		sbObj = ui.ScrollBar()

		sbObj.SetParent(self)

		sbObj.SetPosition(bw + 2, 0)

		# This list prefers a smaller thumb than default.
		scale = float(self._vh) / float(max(1, len(self._nodes)) * max(1, self._ih))
		scale *= 0.60

		try:

			sbObj.SetMiddleBarSize(min(1.0, max(scale, 0.0)))

		except Exception:

			pass

		try:

			sbObj.SetScrollBarSize(self._vh)

		except Exception:

			pass

		try:

			sbObj.SetScrollEvent(ui.__mem_func__(self.__OnSb))

		except Exception:

			pass

		sbObj.Show()

		self.scroll = sbObj

		self.SetSize(self._w, self._vh)

		self.__BindWheelForward(self)
		self.__BindWheelForward(self.clipWindow)
		self.__BindWheelForward(self.body)
		self.__BindWheelForward(self.scroll)

		self.__RefreshSb()

	def __BindWheelForward(self, targetWin):
		if not targetWin:
			return
		owner = self

		def OnMouseWheelButtonUp():
			return owner.OnMouseWheelButtonUp()

		def OnMouseWheelButtonDown():
			return owner.OnMouseWheelButtonDown()

		targetWin.OnMouseWheelButtonUp = OnMouseWheelButtonUp
		targetWin.OnMouseWheelButtonDown = OnMouseWheelButtonDown

	def __OnSb(self):

		self.Refresh()

		try:

			self.cbScroll()

		except Exception:

			pass

	def SetScrollCb(self, fn):

		self.cbScroll = fn

	def ClearNodes(self):

		for ww in tuple(self._nodes):

			try:

				ww.Hide()

			except Exception:

				pass

			self._nodes.remove(ww)

			try:

				ww.SetParent(None)

			except Exception:

				pass

		self._nodes = []

		self._sel = -1

		try:
			if self.scroll and hasattr(self.scroll, "SetPos"):
				self.scroll.SetPos(0.0, True)
		except Exception:
			pass

		self.__RefreshSb()
		self.Refresh()

	def AddNode(self, nodeWin):

		if self.body:

			nodeWin.SetParent(self.body)
			if self.clipWindow and hasattr(nodeWin, "SetClippingMaskWindow"):
				try:
					nodeWin.SetClippingMaskWindow(self.clipWindow)
				except Exception:
					pass

			nodeWin.Show()

		self._nodes.append(nodeWin)

		self.__RefreshSb()
		self.Refresh()

	def __RefreshSb(self):

		if not self.scroll or not self.body:
			return

		self.__ApplyScrollBarLayout()

		# Use real node heights for stable scroll/thumb sizing.
		total = 0
		for nd in self._nodes:
			try:
				hh = nd.GetHeight()
			except Exception:
				hh = 0
			if hh <= 0:
				hh = self._ih
			total += max(self._ih, hh)
		total = max(1, total)

		visibleCap = max(1, self._vh // max(1, self._ih))
		needScroll = len(self._nodes) > visibleCap
		if not needScroll:
			try:
				self.scroll.SetPos(0.0, True)
			except Exception:
				pass
			return

		# This list prefers a smaller thumb than default.
		ratio = float(self.body.GetHeight()) / float(max(self.body.GetHeight(), total))
		ratio *= 0.30

		try:

			self.scroll.SetMiddleBarSize(min(1.0, max(0.0, ratio)))

		except Exception:

			pass

		try:
			bodyH = self.body.GetHeight()
			scrollRange = max(1, total - bodyH)
			rowStep = float(max(self._ih, 1)) / float(scrollRange)
			self.scroll.SetScrollStep(min(0.2, max(0.01, rowStep)))
		except Exception:
			pass

	def __ApplyScrollBarLayout(self):
		if not self.scroll or not self.body:
			return

		sbWide = getattr(ui.ScrollBar, "SCROLLBAR_WIDTH", 17)
		visibleCap = max(1, self._vh // max(1, self._ih))
		needScroll = len(self._nodes) > visibleCap

		if needScroll:
			bw = max(10, self._w - sbWide - 2)
			try:
				self.scroll.Show()
				self.scroll.SetPosition(bw + 2, 0)
			except Exception:
				pass
		else:
			bw = max(10, self._w - 2)
			try:
				self.scroll.Hide()
				self.scroll.SetPos(0.0, True)
			except Exception:
				pass

		try:
			if self.clipWindow:
				self.clipWindow.SetSize(bw, self._vh)
			self.body.SetSize(bw, self._vh)
		except Exception:
			pass

	def __ScrollPx(self):

		total = 0
		try:
			bodyH = self.body.GetHeight()
		except Exception:
			bodyH = 0

		for nd in self._nodes:
			try:
				hh = nd.GetHeight()
			except Exception:
				hh = 0
			if hh <= 0:
				hh = self._ih
			total += max(self._ih, hh)

		total = max(0, total - bodyH)

		try:

			return int(total * float(self.scroll.GetPos()))

		except Exception:

			return 0

	def Refresh(self):

		if not self.body:

			return

		off = self.__ScrollPx()

		acu = -off

		for nd in self._nodes:

			hh = nd.GetHeight()

			if hh <= 0:

				hh = self._ih

			nd.SetPosition(4, acu)

			# MT2009: our exe has no clip mask - a row outside the list's visible band is hidden
			if not self.clipWindow:
				try:
					if acu < 0 or acu + max(self._ih, hh) > self.body.GetHeight():
						nd.Hide()
					else:
						nd.Show()
				except Exception:
					pass

			acu += max(self._ih, hh)

	def ClickNodeWindow(self, wobj):

		if wobj not in self._nodes:

			return False

		self._sel = self._nodes.index(wobj)

		return True

	def SelectItemIndex(self, ix):

		self._sel = int(ix)

	def GetSelectedIndex(self):

		return self._sel

	def __GetScrollRangePx(self):
		if not self.body:
			return 0, 0
		try:
			bodyH = self.body.GetHeight()
		except Exception:
			bodyH = 0
		total = 0
		for nd in self._nodes:
			try:
				hh = nd.GetHeight()
			except Exception:
				hh = 0
			if hh <= 0:
				hh = self._ih
			total += max(self._ih, hh)
		return max(0, total - bodyH), max(self._ih, 8)

	def OnMouseWheelScrollLines(self, lineDelta):
		if not self.scroll:
			return False
		try:
			if not self.scroll.IsShow():
				return False
		except Exception:
			pass
		scrollRange, stepPx = self.__GetScrollRangePx()
		if scrollRange <= 0:
			return False
		curPx = self.__ScrollPx()
		newPx = curPx + int(lineDelta) * int(stepPx)
		if newPx < 0:
			newPx = 0
		elif newPx > scrollRange:
			newPx = scrollRange
		if newPx == curPx:
			return False
		try:
			self.scroll.SetPos(float(newPx) / float(scrollRange), False)
		except Exception:
			return False
		self.Refresh()
		try:
			self.cbScroll()
		except Exception:
			pass
		return True

	def OnMouseWheelButtonUp(self):
		return self.OnMouseWheelScrollLines(-1)

	def OnMouseWheelButtonDown(self):
		return self.OnMouseWheelScrollLines(1)


def _NpcLocHelperDropRowBg(dataIx, totalCount):

	if totalCount == 1:

		return ROOT_PATH + "button_drop_down_bg_main.sub"

	if dataIx == totalCount - 1:

		return ROOT_PATH + "button_drop_down_bg_bottom.sub"

	return ROOT_PATH + "button_drop_down_bg_middle.sub"


class _NpcListHoverPollWnd(ui.Window):

	def __init__(self, owner):

		ui.Window.__init__(self)

		self.owner = owner

	def OnUpdate(self):

		if self.owner:

			self.owner._UpdateNpcRowHover()


class _DropDownListWnd(ui.Window):

	def __init__(self, owner):

		ui.Window.__init__(self, "TOP_MOST")

		self.owner = owner

	def OnUpdate(self):

		if self.owner:

			self.owner._UpdateListHover()

	def OnMouseLeftButtonUp(self):

		if not self.owner:

			return

		if self.owner._listScrollDragging:

			self.owner._listScrollDragging = False

	def OnMouseWheelButtonUp(self):

		if self.owner and self.owner.OnListMouseWheel(1):

			return True

		return False

	def OnMouseWheelButtonDown(self):

		if self.owner and self.owner.OnListMouseWheel(-1):

			return True

		return False


class _DropDownListRowWnd(ui.Window):

	def __init__(self, owner):

		ui.Window.__init__(self)

		self.owner = owner

	def OnMouseLeftButtonUp(self):

		if not self.owner:

			return

		if self.owner._listScrollDragging or self.owner._IsMouseOnListScrollColumn():

			self.owner._listScrollDragging = False

			return

		if not self.owner._IsMouseInOpenListBody():

			return

		self.owner._OnListMouseClick()


class _DropDownScrollWnd(ui.Window):

	def __init__(self, owner):

		ui.Window.__init__(self)

		self.owner = owner

	def OnMouseLeftButtonDown(self):

		if self.owner:

			self.owner._listScrollDragging = True

	def OnMouseLeftButtonUp(self):

		if self.owner:

			self.owner._listScrollDragging = False

	def OnMouseWheelButtonUp(self):

		if self.owner and self.owner.OnListMouseWheel(1):

			return True

		return False

	def OnMouseWheelButtonDown(self):

		if self.owner and self.owner.OnListMouseWheel(-1):

			return True

		return False


class DropDownList(ui.Window):

	DROP_DOWN_BUTTON_WIDTH = 244
	DROP_DOWN_BUTTON_HEIGHT = 16
	ITEM_ROW_HEIGHT = 16
	# Gap between chrome bar and list (reference ~1-2px; bar slot is 16px, art is 18px).
	LIST_OPEN_OFFSET_Y = 3
	ROW_TEXT_Y = 4

	# Map dropdown: fixed viewport height on reference client (~10 rows).
	MAP_DROP_LIST_VISIBLE_ROWS = 10

	def __init__(self, show_item_count=10, fixed_list_rows=0):

		ui.Window.__init__(self)

		self.items = []

		self.itemCatIx = []

		self.selIx = -1

		self.fixedListRows = max(0, int(fixed_list_rows))

		self.maxVis = max(2, int(show_item_count))

		if self.fixedListRows > 0:

			self.maxVis = self.fixedListRows

		self.openFlag = False

		self.shellWnd = None

		self.cbPick = lambda a, b: None

		self.listWnd = None

		self.listRowWnd = None

		self.popRows = []

		self._hoverIdx = -1

		self.hoverBar = None

		self.rowOverImgs = []

		self._listVisMap = []

		self._scrollStart = 0

		self.listScrollBar = None

		self.listScrollWnd = None

		self._listScrollDragging = False

		self._listPopW = 0

		self._listScrollW = 0

		self._chromeBuilt = False

		self._boxW = 241

		self.bgImg = None

		self.selText = None

		self.arrowBtn = None

		self._hostWnd = None

		self._peerDropDown = None

	def __del__(self):

		self.CloseDropDownWindow()

		ui.Window.__del__(self)

	def SetParent(self, parent):

		ui.Window.SetParent(self, parent)

		self._hostWnd = parent

	def SetPopupParent(self, wnd):

		self.shellWnd = wnd

	def __GetHostWnd(self):

		if self._hostWnd:

			return self._hostWnd

		try:

			p = self.GetParentProxy()

			if p:

				return p

		except Exception:

			pass

		return None

	def __GetListParent(self):

		if self.shellWnd:

			try:

				brd = self.shellWnd.board

				if brd:

					return brd

			except Exception:

				pass

			try:

				bw = self.shellWnd.bgWindow

				if bw:

					return bw

			except Exception:

				pass

		hostWnd = self.__GetHostWnd()

		if hostWnd:

			return hostWnd

		return self

	def __CalcListOpenPos(self, parentWnd):

		bh = self.DROP_DOWN_BUTTON_HEIGHT

		try:

			wh = self.GetHeight()

			if wh > 0:

				bh = wh

		except Exception:

			pass

		try:

			gx, gy = self.GetGlobalPosition()

			px, py = parentWnd.GetGlobalPosition()

		except Exception:

			return 0, int(bh) + self.LIST_OPEN_OFFSET_Y

		return int(gx - px), int(gy - py) + int(bh) + self.LIST_OPEN_OFFSET_Y

	def _IsMouseInOpenListBody(self):

		if not self.openFlag or not self.listWnd:

			return False

		try:

			mx, my = wndMgr.GetMousePosition()

			gx, gy = self.listWnd.GetGlobalPosition()

			lw = self.listWnd.GetWidth()

			lh = self.listWnd.GetHeight()

			if lw <= 0:

				lw = self._listPopW

			if lh <= 0:

				lh = self.__GetListViewportRows() * self.ITEM_ROW_HEIGHT

			return (gx <= mx < gx + lw) and (gy <= my < gy + lh)

		except Exception:

			return False

	def __BuildVisibleItemMap(self):

		vis = []

		for jj in xrange(len(self.items)):

			try:

				lbl = self.items[jj]

				if lbl and str(lbl).strip():

					vis.append(jj)

			except Exception:

				pass

		return vis

	def __ResolveListParent(self):

		if self.shellWnd:

			try:

				bw = self.shellWnd.bgWindow

				if bw:

					return bw

			except Exception:

				pass

		hostWnd = self.__GetHostWnd()

		if hostWnd:

			try:

				p = hostWnd

				while p:

					try:

						if p.GetWindowName() == "bg_window":

							return p

					except Exception:

						pass

					try:

						p = p.GetParentProxy()

					except Exception:

						break

					if not p:

						break

			except Exception:

				pass

			return hostWnd

		return self

	def __RaiseListLayer(self):

		try:

			if self.listWnd:

				self.listWnd.SetTop()

		except Exception:

			pass

		try:

			self.SetTop()

		except Exception:

			pass

		try:

			if self.shellWnd:

				self.shellWnd.SetTop()

		except Exception:

			pass

		try:

			if self.shellWnd and getattr(self.shellWnd, "board", None):

				self.shellWnd.board.SetTop()

		except Exception:

			pass

	def __DestroyListWnd(self):

		self._hoverIdx = -1

		self.popRows = []

		self.hoverBar = None

		self.rowOverImgs = []

		self._listVisMap = []

		self._scrollStart = 0

		self._listScrollDragging = False

		self._listScrollW = 0

		if self.listScrollBar:

			try:

				self.listScrollBar.Hide()

			except Exception:

				pass

			self.listScrollBar = None

		if self.listScrollWnd:

			try:

				self.listScrollWnd.Hide()

			except Exception:

				pass

			self.listScrollWnd = None

		if self.listWnd:

			try:

				self.listWnd.Hide()

			except Exception:

				pass

			self.listWnd = None

		self.listRowWnd = None

	def __GetListViewportRows(self):

		if self.fixedListRows > 0:

			return self.fixedListRows

		try:

			return min(len(self._listVisMap), self.maxVis)

		except Exception:

			return self.maxVis

	def __GetListVisibleRowCount(self):

		try:

			return min(len(self._listVisMap), self.__GetListViewportRows())

		except Exception:

			return 0

	def __NeedsListScroll(self):

		try:

			return len(self._listVisMap) > self.__GetListViewportRows()

		except Exception:

			return False

	def __ClipRowButtonPickWidth(self, rowBtn, pickW):

		try:

			imgW = self.DROP_DOWN_BUTTON_WIDTH

			try:

				w = rowBtn.GetWidth()

				if w > 0:

					imgW = w

			except Exception:

				pass

			if imgW > pickW:

				rowBtn.SetButtonScale(float(pickW) / float(imgW), 1.0)

		except Exception:

			pass

	def _IsMouseOnListScrollColumn(self):

		if not self.openFlag or not self.listWnd:

			return False

		if self._listScrollW <= 0:

			return False

		try:

			if self.listScrollWnd and self.listScrollWnd.IsShow() and self.listScrollWnd.IsIn():

				return True

		except Exception:

			pass

		if self.listScrollBar:

			try:

				if self.listScrollBar.IsShow() and self.listScrollBar.IsIn():

					return True

			except Exception:

				pass

		try:

			mx, my = wndMgr.GetMousePosition()

			gx, gy = self.listWnd.GetGlobalPosition()

			lw = self.listWnd.GetWidth()

			if lw <= 0:

				lw = self._listPopW

			if int(mx - gx) >= int(lw) - int(self._listScrollW):

				return True

		except Exception:

			pass

		return False

	def _IsMouseOnListScrollBar(self):

		return self._IsMouseOnListScrollColumn()

	def OnListMouseWheel(self, direction):

		if not self.openFlag or not self.listWnd:

			return False

		visTotal = len(self._listVisMap)

		viewportRows = self.__GetListViewportRows()

		if visTotal <= viewportRows:

			return False

		maxStart = visTotal - viewportRows

		self._scrollStart = max(0, min(self._scrollStart - int(direction), maxStart))

		if self.listScrollBar:

			try:

				self.listScrollBar.SetPos(float(self._scrollStart) / float(max(1, maxStart)))

			except Exception:

				pass

		self.__RelayoutListRows()

		return True

	def __OnListScroll(self):

		if not self.openFlag or not self.listScrollBar:

			return

		self._listScrollDragging = True

		visTotal = len(self._listVisMap)

		viewportRows = self.__GetListViewportRows()

		maxStart = max(0, visTotal - viewportRows)

		try:

			pos = self.listScrollBar.GetPos()

		except Exception:

			pos = 0.0

		newStart = int(pos * maxStart + 0.5)

		if newStart == self._scrollStart:

			return

		self._scrollStart = newStart

		self.__RelayoutListRows()

	def __RelayoutListRows(self):

		if not self.listWnd or not self.openFlag:

			return

		visTotal = len(self._listVisMap)

		visRows = self.__GetListVisibleRowCount()

		popW = self._listPopW

		if popW <= 0:

			popW = self.DROP_DOWN_BUTTON_WIDTH

		for rowVis in xrange(len(self.popRows)):

			if rowVis >= visRows:

				try:

					self.popRows[rowVis].Hide()

					self.rowOverImgs[rowVis].Hide()

				except Exception:

					pass

				continue

			jj = self._listVisMap[self._scrollStart + rowVis]

			visPath = _NpcLocHelperDropRowBg(jj, visTotal)

			rowBtn = self.popRows[rowVis]

			rowBtn.SetPosition(0, rowVis * self.ITEM_ROW_HEIGHT)

			rowBtn.SetUpVisual(visPath)

			rowBtn.SetOverVisual(visPath)

			rowBtn.SetDownVisual(visPath)

			rowBtn.SetText(self.items[jj], self.ROW_TEXT_Y)

			rowBtn.Show()

			self.rowOverImgs[rowVis].Hide()

		self._hoverIdx = -1

	def CloseDropDownWindow(self):

		wasOpen = self.openFlag

		self.openFlag = False

		if wasOpen:

			self.__SetNpcListPickBlocked(False)

		self.__DestroyListWnd()

	def OpenDropDownWindow(self):

		peerDropDown = getattr(self, "_peerDropDown", None)

		if peerDropDown and peerDropDown is not self and peerDropDown.openFlag:

			try:

				peerDropDown.CloseDropDownWindow()

			except Exception:

				pass

		self.__ToggleDropDown()

	def _UpdateListHover(self):

		if not self.openFlag or not self.listWnd:

			return

		try:

			if self._IsMouseOnListScrollColumn():

				self._hoverIdx = -1

				for rowOver in self.rowOverImgs:

					try:

						rowOver.Hide()

					except Exception:

						pass

				return

			if not self._IsMouseInOpenListBody():

				self._hoverIdx = -1

				for rowOver in self.rowOverImgs:

					try:

						rowOver.Hide()

					except Exception:

						pass

				return

			mx, my = wndMgr.GetMousePosition()

			gx, gy = self.listWnd.GetGlobalPosition()

			relY = int(my - gy)

			rowVis = relY / self.ITEM_ROW_HEIGHT

			visRows = self.__GetListVisibleRowCount()

			if rowVis < 0 or rowVis >= visRows:

				self._hoverIdx = -1

			else:

				self._hoverIdx = rowVis

			for ii, rowOver in enumerate(self.rowOverImgs):

				try:

					if ii == self._hoverIdx:

						rowOver.Show()

					else:

						rowOver.Hide()

				except Exception:

					pass

		except Exception:

			self._hoverIdx = -1

			for rowOver in self.rowOverImgs:

				try:

					rowOver.Hide()

				except Exception:

					pass

	def __ToggleDropDown(self):

		if self.openFlag:

			self.CloseDropDownWindow()

			return

		if not self.items:

			return

		peerDropDown = getattr(self, "_peerDropDown", None)

		if peerDropDown:

			try:

				peerDropDown.CloseDropDownWindow()

			except Exception:

				pass

		self.__BuildChrome()

		self.__DestroyListWnd()

		self._scrollStart = 0

		parentWnd = self.__GetListParent()

		popW = self._boxW

		if popW <= 0:

			popW = self.DROP_DOWN_BUTTON_WIDTH

		self._listPopW = popW

		listX, listY = self.__CalcListOpenPos(parentWnd)

		self._listVisMap = self.__BuildVisibleItemMap()

		visTotal = len(self._listVisMap)

		if visTotal <= 0:

			return

		viewportRows = self.__GetListViewportRows()

		visRows = min(visTotal, viewportRows)

		popH = viewportRows * self.ITEM_ROW_HEIGHT

		needScroll = visTotal > viewportRows

		sbW = getattr(ui.ScrollBar, "SCROLLBAR_WIDTH", 17)

		self._listScrollW = sbW if needScroll else 0

		listWnd = _DropDownListWnd(self)

		listWnd.SetParent(parentWnd)

		listWnd.SetPosition(listX, listY)

		listWnd.SetSize(popW, popH)

		listWnd.AddFlag("float")

		listBg = ui.Bar()

		listBg.SetParent(listWnd)

		listBg.SetPosition(0, 0)

		listBg.SetSize(popW, popH)

		listBg.SetColor(0xFF000000)

		try:

			listBg.AddFlag("not_pick")

		except Exception:

			pass

		listBg.Show()

		listRowWnd = _DropDownListRowWnd(self)

		listRowWnd.SetParent(listWnd)

		listRowWnd.SetPosition(0, 0)

		listRowWnd.SetSize(popW, popH)

		listRowWnd.Show()

		self.hoverBar = None

		self.listWnd = listWnd

		self.listRowWnd = listRowWnd

		self.popRows = []

		self.rowOverImgs = []

		self.listScrollBar = None

		self._hoverIdx = -1

		for rowVis in xrange(visRows):

			jj = self._listVisMap[self._scrollStart + rowVis]

			visPath = _NpcLocHelperDropRowBg(jj, visTotal)

			rowBtn = ui.Button()

			rowBtn.SetParent(listRowWnd)

			rowBtn.SetPosition(0, rowVis * self.ITEM_ROW_HEIGHT)

			rowBtn.SetUpVisual(visPath)

			rowBtn.SetOverVisual(visPath)

			rowBtn.SetDownVisual(visPath)

			self.__BindDropRowPick(rowBtn, jj)

			rowBtn.Show()

			rowBtn.SetText(self.items[jj], self.ROW_TEXT_Y)

			rowOver = ui.ImageBox()

			rowOver.SetParent(rowBtn)

			rowOver.SetPosition(0, 0)

			rowOver.LoadImage(ROOT_PATH + "button_drop_down_bg_over.sub")

			try:

				rowOver.AddFlag("not_pick")

			except Exception:

				pass

			rowOver.Hide()

			self.rowOverImgs.append(rowOver)

			self.popRows.append(rowBtn)

		if needScroll:

			try:

				scrollWnd = _DropDownScrollWnd(self)

				scrollWnd.SetParent(listWnd)

				scrollWnd.SetPosition(max(0, popW - sbW), 0)

				scrollWnd.SetSize(sbW, popH)

				sb = ui.ScrollBar()

				sb.SetParent(scrollWnd)

				sb.SetPosition(0, 0)

				scale = float(popH) / float(max(1, visTotal * self.ITEM_ROW_HEIGHT))

				sb.SetMiddleBarSize(min(1.0, max(scale, 0.08)))

				sb.SetScrollBarSize(popH)

				maxStart = visTotal - viewportRows

				sb.SetScrollStep(1.0 / float(max(1, maxStart)))

				sb.SetScrollEvent(ui.__mem_func__(self.__OnListScroll))

				sb.SetPos(0.0)

				sb.Show()

				scrollWnd.Show()

				scrollWnd.SetTop()

				sb.SetTop()

				self.listScrollWnd = scrollWnd

				self.listScrollBar = sb

			except Exception:

				self.listScrollBar = None

				self.listScrollWnd = None

		listWnd.Show()

		self.__RaiseListLayer()

		try:

			if self.shellWnd and getattr(self.shellWnd, "lvNpc", None):

				if self.listWnd:

					self.listWnd.SetTop()

		except Exception:

			pass

		if self.listScrollWnd:

			try:

				self.listScrollWnd.SetTop()

			except Exception:

				pass

			if self.listScrollBar:

				try:

					self.listScrollBar.SetTop()

				except Exception:

					pass

		self.openFlag = True

		self.__SetNpcListPickBlocked(True)

	def _OnListMouseClick(self):

		if not self.listWnd or not self.openFlag:

			return

		if self._listScrollDragging or self._IsMouseOnListScrollColumn():

			return

		try:

			rowWnd = self.listRowWnd if self.listRowWnd else self.listWnd

			mx, my = wndMgr.GetMousePosition()

			gx, gy = rowWnd.GetGlobalPosition()

			rowVis = int(my - gy) / self.ITEM_ROW_HEIGHT

		except Exception:

			return

		visRows = self.__GetListVisibleRowCount()

		if rowVis < 0 or rowVis >= visRows:

			return

		self.__OnPickItem(self._listVisMap[self._scrollStart + rowVis])

	def __OnPickItem(self, idx):

		self.SelectItemIndex(idx)

		self.CloseDropDownWindow()

	def __BuildChrome(self):

		if self._chromeBuilt:

			self.__LayoutChrome()

			return

		self._chromeBuilt = True

		bg = ui.Button()

		bg.SetParent(self)

		bg.SetPosition(0, 0)

		bg.SetUpVisual(ROOT_PATH + "button_drop_down_bg_main.sub")

		bg.SetOverVisual(ROOT_PATH + "button_drop_down_bg_main.sub")

		bg.SetDownVisual(ROOT_PATH + "button_drop_down_bg_main.sub")

		try:

			bg.SAFE_SetEvent(ui.__mem_func__(self.OpenDropDownWindow))

		except Exception:

			bg.SetEvent(ui.__mem_func__(self.OpenDropDownWindow))

		bg.Show()

		self.bgImg = bg

		tx = ui.TextLine()

		tx.SetParent(self)

		tx.SetVerticalAlignCenter()

		tx.SetHorizontalAlignCenter()

		try:

			tx.AddFlag("not_pick")

		except Exception:

			pass

		tx.Show()

		self.selText = tx

		ab = ui.Button()

		ab.SetParent(self)

		ab.SetUpVisual(ROOT_PATH + "button_drop_down_arrow_default.sub")

		ab.SetOverVisual(ROOT_PATH + "button_drop_down_arrow_over.sub")

		ab.SetDownVisual(ROOT_PATH + "button_drop_down_arrow_down.sub")

		try:

			ab.SAFE_SetEvent(ui.__mem_func__(self.OpenDropDownWindow))

		except Exception:

			ab.SetEvent(ui.__mem_func__(self.OpenDropDownWindow))

		ab.Show()

		self.arrowBtn = ab

		self.__LayoutChrome()

	def __LayoutChrome(self):

		bh = self.DROP_DOWN_BUTTON_HEIGHT

		self.SetSize(self._boxW, bh)

		if self.selText:

			self.selText.SetPosition(self._boxW / 2, bh / 2)

		if self.arrowBtn:

			try:

				aw = self.arrowBtn.GetWidth()

			except Exception:

				aw = 0

			if aw <= 0:

				aw = 16

			self.arrowBtn.SetPosition(max(0, self._boxW - aw + 2), 0)

	def SetBox(self, widthPx):

		try:

			w = int(widthPx)

		except Exception:

			w = 0

		if w > 0:

			self._boxW = w

		else:

			self._boxW = self.DROP_DOWN_BUTTON_WIDTH

		if self._chromeBuilt:

			self.__LayoutChrome()

		else:

			self.SetSize(self._boxW, self.DROP_DOWN_BUTTON_HEIGHT)

	def InsertItem(self, labelTxt, catIx=-1):

		self.__BuildChrome()

		try:

			if not labelTxt or not str(labelTxt).strip():

				return

		except Exception:

			return

		self.items.append(labelTxt)

		self.itemCatIx.append(int(catIx))

	def SetSelectedText(self, text):

		self.__BuildChrome()

		try:

			if self.selText:

				self.selText.SetText(text)

		except Exception:

			pass

	def SelectItemIndex(self, kk, bNotify=True):

		if kk < 0 or kk >= len(self.items):

			return

		self.selIx = kk

		self.__BuildChrome()

		txt = self.items[kk]

		if self.selText:

			self.selText.SetText(txt)

		if not bNotify:

			return

		pickKey = kk

		try:

			if kk < len(self.itemCatIx) and self.itemCatIx[kk] >= 0:

				pickKey = self.itemCatIx[kk]

		except Exception:

			pass

		try:

			self.cbPick(pickKey, txt)

		except Exception:

			pass

	def SelectCategoryIndex(self, catIx):

		try:

			catIx = int(catIx)

		except Exception:

			return

		for ii in xrange(len(self.itemCatIx)):

			try:

				if self.itemCatIx[ii] == catIx:

					self.SelectItemIndex(ii)

					return

			except Exception:

				pass

	def SetPickEvent(self, fn):

		self.cbPick = fn

	def SetPeerDropDown(self, other):

		self._peerDropDown = other

	def __SetNpcListPickBlocked(self, block):

		try:

			if self.shellWnd and getattr(self.shellWnd, "lvNpc", None):

				self.shellWnd.lvNpc.SetNpcRowPickBlocked(block)

		except Exception:

			pass

	def __BindDropRowPick(self, rowBtn, itemIdx):

		def _OnRowPick():

			self.__OnPickItem(itemIdx)

		try:

			rowBtn.SAFE_SetEvent(_OnRowPick)

		except Exception:

			try:

				rowBtn.SetEvent(_OnRowPick)

			except Exception:

				pass


class NPCListNode(ui.ImageBox):

	NPC_ROW_W = 244
	NPC_ROW_H = 28
	NPC_ICON_X = 2
	NPC_ICON_Y = 2
	# Reference layout: move button sits left of the row edge (~2 grid steps from flush-right).
	NPC_BTN_X = 205
	NPC_BTN_Y = 1
	QUEST_ICON_W = 16
	QUEST_ICON_H = 16
	QUEST_ICON_GAP = 1
	QUEST_ICON_BASE_X = NPC_BTN_X - QUEST_ICON_W - 2
	QUEST_ICON_BASE_Y = 1
	QUEST_ICON_ACCEPT = "d:/ymir work/ui/game/npc_location_helper/quest_state_icon_accept.sub"
	QUEST_ICON_PROGRESS = "d:/ymir work/ui/game/npc_location_helper/quest_state_icon_progress.sub"
	QUEST_ICON_COMPLETE = "d:/ymir work/ui/game/npc_location_helper/quest_state_icon_complete.sub"
	NPC_NAME_WIN_X = 28
	NPC_NAME_WIN_W = NPC_BTN_X - NPC_NAME_WIN_X - 2

	NPC_ROW_BG_DEFAULT = ROOT_PATH + "npc_list_node_default.sub"
	NPC_ROW_BG_OVER = ROOT_PATH + "npc_list_node_over.sub"
	NPC_ROW_BG_DOWN = ROOT_PATH + "npc_list_node_down.sub"
	NPC_ROW_BG_SELECTED = ROOT_PATH + "npc_list_node_down.sub"
	NPC_ROW_BG_SELECTED_OVER = ROOT_PATH + "npc_list_node_down_over.sub"

	NPC_MOVE_BTN_DEFAULT = ROOT_PATH + "npc_list_move_button_default.sub"
	NPC_MOVE_BTN_OVER = ROOT_PATH + "npc_list_move_button_over.sub"
	NPC_MOVE_BTN_DOWN = ROOT_PATH + "npc_list_move_button_down.sub"

	def __init__(self):
		ui.ImageBox.__init__(self)

		self.data = None

		self.ic = None

		self.nameWin = None

		self.labName = None

		self.labPos = None

		self.btGo = None

		self.questAccept = None

		self.questProg = None

		self.questDone = None

		self.warpDlg = None

		self.roleTooltip = None

		self._rowHovered = False

		self._isSelected = False

		self._lvNpc = None

		self.namePick = None

		self._pickBlocked = False

		self.onRowInfo = lambda d: None

		self.NotifyBarCb = lambda w: None

	def __del__(self):
		ui.ImageBox.__del__(self)

	def BindListViewNpc(self, lvNpc):
		self._lvNpc = lvNpc

	def BindRoleTooltip(self, tipRef):
		self.roleTooltip = tipRef

	def __HandleSelectClick(self):
		try:
			if self._lvNpc:
				try:
					blockCb = getattr(self._lvNpc, "_dropDownBlockCb", None)
					if blockCb and blockCb():
						return
				except Exception:
					pass
				cb = getattr(self._lvNpc, "_nodeClickCb", None)
				if cb:
					cb(self)
					return
		except Exception:
			pass
		try:
			self.NotifyBarCb(self)
		except Exception:
			pass

	def __ApplyRowBackground(self, bgPath):
		try:
			self.LoadImage(bgPath)
		except Exception:
			pass

	def __RefreshRowBackground(self):
		if self._isSelected:
			if self._rowHovered:
				self.__ApplyRowBackground(self.NPC_ROW_BG_SELECTED_OVER)
			else:
				self.__ApplyRowBackground(self.NPC_ROW_BG_SELECTED)
		elif self._rowHovered:
			self.__ApplyRowBackground(self.NPC_ROW_BG_OVER)
		else:
			self.__ApplyRowBackground(self.NPC_ROW_BG_DEFAULT)

	def __OnRowHoverIn(self):
		if self._rowHovered:
			return
		self._rowHovered = True
		self.__RefreshRowBackground()

	def __OnRowHoverOut(self):
		if not self._rowHovered:
			return
		self._rowHovered = False
		self.__RefreshRowBackground()

	def OnSelectNode(self):
		self._isSelected = True
		self.__RefreshRowBackground()

	def OnUnselectNode(self):
		self._isSelected = False
		self.__RefreshRowBackground()

	def SetRowPickBlocked(self, block):

		self._pickBlocked = bool(block)

		try:

			if self.namePick:

				if block:

					self.namePick.Hide()

				else:

					self.namePick.Show()

		except Exception:

			pass

	def OnMouseOverIn(self):
		self.__OnRowHoverIn()

	def OnMouseOverOut(self):
		self.__OnRowHoverOut()

	def OnMouseLeftButtonDown(self):
		if self._isSelected:
			self.__ApplyRowBackground(self.NPC_ROW_BG_SELECTED_OVER)
		else:
			self.__ApplyRowBackground(self.NPC_ROW_BG_DOWN)

	def OnMouseLeftButtonUp(self):
		try:
			if self.btGo and self.btGo.IsShow() and self.btGo.IsIn():
				try:
					ui.ImageBox.OnMouseLeftButtonUp(self)
				except Exception:
					pass
				return
		except Exception:
			pass
		self.__RefreshRowBackground()
		self.__HandleSelectClick()
		try:
			ui.ImageBox.OnMouseLeftButtonUp(self)
		except Exception:
			pass

	def __OnRowClickSelect(self):
		self.__HandleSelectClick()

	def __GetListViewOwner(self):
		p = self
		while p:
			if isinstance(p, ListView):
				return p
			try:
				p = p.GetParent()
			except Exception:
				p = None
		return None

	def OnMouseWheelScrollLines(self, lineDelta):
		owner = self.__GetListViewOwner()
		if owner:
			return owner.OnMouseWheelScrollLines(lineDelta)
		return False

	def OnMouseWheelButtonUp(self):
		return self.OnMouseWheelScrollLines(-1)

	def OnMouseWheelButtonDown(self):
		return self.OnMouseWheelScrollLines(1)

	def SetNPCData(self, vnum, name, gx, gy, roleIcon, landId):

		self.data = {
			"vnum": int(vnum),
			"name": name,
			"x": int(gx),
			"y": int(gy),
			"icon": int(roleIcon),
			"land_id": int(landId),
			"map_index": 0,
			"quest_state": -1,
		}

		self.RefreshLayout()

	def SetQuestState(self, st):
		try:
			if self.data is None:
				self.data = {}
			self.data["quest_state"] = int(st)
		except Exception:
			if self.data is None:
				self.data = {}
			self.data["quest_state"] = -1
		self.__RefreshQuestIcons()

	def BindMapIx(self, mxi):

		if self.data is None:

			self.data = {}

		self.data["map_index"] = int(mxi)

	def BuildRow(self):

		if self.labName:

			return

		self.SetSize(self.NPC_ROW_W, self.NPC_ROW_H)

		self.__ApplyRowBackground(self.NPC_ROW_BG_DEFAULT)

		self.ic = ui.ExpandedImageBox()

		self.ic.SetParent(self)

		self.ic.SetPosition(self.NPC_ICON_X, self.NPC_ICON_Y)

		self.ic.SetEvent(ui.__mem_func__(self.__OnIconMouseOverIn), "mouse_over_in")

		self.ic.SetEvent(ui.__mem_func__(self.__OnIconMouseOverOut), "mouse_over_out")

		self.ic.SetEvent(ui.__mem_func__(self.__OnRowClickSelect), "mouse_click")

		self.ic.Show()

		self.namePick = ui.Bar()

		self.namePick.SetParent(self)

		self.namePick.SetPosition(self.NPC_NAME_WIN_X, 0)

		self.namePick.SetSize(self.NPC_NAME_WIN_W, self.NPC_ROW_H)

		try:

			self.namePick.SetColor(0x00000000)

		except Exception:

			pass

		self.namePick.Show()

		try:

			self.namePick.SetPickAlways()

		except Exception:

			pass

		rowRef = self

		def _NamePickMouseUp():
			rowRef.__HandleSelectClick()
			return True

		self.namePick.OnMouseLeftButtonUp = _NamePickMouseUp

		def _NamePickMouseOverIn():
			rowRef.__OnRowHoverIn()

		def _NamePickMouseOverOut():
			rowRef.__OnRowHoverOut()

		self.namePick.OnMouseOverIn = _NamePickMouseOverIn
		self.namePick.OnMouseOverOut = _NamePickMouseOverOut

		self.nameWin = ui.Window()

		self.nameWin.SetParent(self)

		self.nameWin.SetPosition(self.NPC_NAME_WIN_X, 0)

		self.nameWin.SetSize(self.NPC_NAME_WIN_W, self.NPC_ROW_H)

		try:

			self.nameWin.AddFlag("not_pick")

		except Exception:

			pass

		self.nameWin.Show()

		self.labName = ui.TextLine()

		self.labName.SetParent(self.nameWin)

		self.labName.SetPosition(0, 8)

		self.labName.SetWindowHorizontalAlignCenter()

		self.labName.SetHorizontalAlignCenter()

		try:

			self.labName.AddFlag("not_pick")

		except Exception:

			pass

		self.labName.Show()

		self.labPos = ui.TextLine()

		self.labPos.SetParent(self.nameWin)

		self.labPos.SetPosition(0, 16)

		self.labPos.SetWindowHorizontalAlignCenter()

		self.labPos.SetHorizontalAlignCenter()

		try:

			self.labPos.AddFlag("not_pick")

		except Exception:

			pass

		if SHOW_NPC_LIST_POSITION:
			self.labPos.Show()
		else:
			self.labPos.Hide()

		bt = ui.Button()

		bt.SetParent(self)

		bt.SetPosition(self.NPC_BTN_X, self.NPC_BTN_Y)

		bt.SetUpVisual(self.NPC_MOVE_BTN_DEFAULT)
		bt.SetOverVisual(self.NPC_MOVE_BTN_OVER)
		bt.SetDownVisual(self.NPC_MOVE_BTN_DOWN)

		bt.SAFE_SetEvent(self.__OnClickMoveButton)

		try:
			bt.SetPickAlways()
		except Exception:
			pass

		bt.Show()

		try:
			bt.SetTop()
		except Exception:
			pass

		self.btGo = bt

		self.questAccept = ui.ImageBox()
		self.questAccept.SetParent(self)
		self.questAccept.SetPosition(self.QUEST_ICON_BASE_X, self.QUEST_ICON_BASE_Y)
		self.questAccept.LoadImage(self.QUEST_ICON_ACCEPT)
		try:
			self.questAccept.AddFlag("not_pick")
		except Exception:
			pass
		self.questAccept.Hide()

		self.questProg = ui.ImageBox()
		self.questProg.SetParent(self)
		self.questProg.SetPosition(self.QUEST_ICON_BASE_X, self.QUEST_ICON_BASE_Y + self.QUEST_ICON_H + self.QUEST_ICON_GAP)
		self.questProg.LoadImage(self.QUEST_ICON_PROGRESS)
		try:
			self.questProg.AddFlag("not_pick")
		except Exception:
			pass
		self.questProg.Hide()

		self.questDone = ui.ImageBox()
		self.questDone.SetParent(self)
		self.questDone.SetPosition(self.QUEST_ICON_BASE_X, self.QUEST_ICON_BASE_Y + (self.QUEST_ICON_H + self.QUEST_ICON_GAP) * 2)
		self.questDone.LoadImage(self.QUEST_ICON_COMPLETE)
		try:
			self.questDone.AddFlag("not_pick")
		except Exception:
			pass
		self.questDone.Hide()

		self.__RefreshQuestIcons()

	def __OnIconMouseOverIn(self):
		self.__OnRowHoverIn()
		self.__OnRoleIconOverIn()

	def __OnIconMouseOverOut(self):
		self.__OnRowHoverOut()
		self.__OnRoleIconOverOut()

	def __OnRoleIconOverIn(self):

		if not self.data or not self.ic or not self.ic.IsShow():

			return

		tip = self.roleTooltip

		if tip is None:

			try:

				tip = uiToolTip.ToolTip()

				self.roleTooltip = tip

			except Exception:

				return

		try:

			tipText = NPCLocationHelperUtil.GetNPCRoleTooltipText(int(self.data.get("icon", 19)))

		except Exception:

			tipText = ""

		if not tipText:

			return

		try:

			tip.ClearToolTip()

			tip.AppendTextLine(tipText, uiToolTip.ToolTip.FONT_COLOR, True)

			tip.ResizeToolTip()

			tip.Show()

		except Exception:

			pass

	def __OnRoleIconOverOut(self):

		tip = self.roleTooltip

		if not tip:

			return

		try:

			tip.HideToolTip()

		except Exception:

			try:

				tip.Hide()

			except Exception:

				pass

	def RefreshLayout(self):

		if self.data is None:

			return

		self.BuildRow()

		imgPath = NPCLocationHelperUtil.GetNPCRoleIconFilePath(int(self.data["icon"]))

		try:

			self.ic.LoadImage(imgPath)

		except Exception:

			pass

		self.labName.SetText(self.data.get("name", ""))

		if SHOW_NPC_LIST_POSITION:
			self.labPos.SetText("[%d,%d]" % (int(self.data["x"]), int(self.data["y"])))
			self.labPos.Show()
		else:
			self.labPos.SetText("")
			self.labPos.Hide()

		self.__RefreshQuestIcons()

	def __RefreshQuestIcons(self):
		st = -1
		try:
			if self.data:
				st = int(self.data.get("quest_state", -1))
		except Exception:
			st = -1

		for w in (self.questAccept, self.questProg, self.questDone):
			if w:
				try:
					w.Hide()
				except Exception:
					pass

		if st == 0 and self.questAccept:
			try:
				self.questAccept.Show()
			except Exception:
				pass
		elif st == 1 and self.questProg:
			try:
				self.questProg.Show()
			except Exception:
				pass
		elif st == 2 and self.questDone:
			try:
				self.questDone.Show()
			except Exception:
				pass

	def __OnClickMoveButton(self):
		try:
			if self._pickBlocked:
				return
			if self._lvNpc:
				blockCb = getattr(self._lvNpc, "_dropDownBlockCb", None)
				if blockCb and blockCb():
					return
		except Exception:
			pass
		try:
			self.DoWarpPrompt()
		except Exception:
			pass

	def RefreshNPCTeleportButton(self):

		showBtn = False

		try:

			if _HelperIsActive(): # MT2009_PLUS_NPC_LOCATION_HELPER_V2

				showBtn = True

		except Exception:

			showBtn = False

		try:

			if self.btGo:

				if showBtn:

					self.btGo.Show()

				else:

					self.btGo.Hide()

		except Exception:

			pass

	def DoWarpPrompt(self):

		if self.data is None:

			return

		# MT2009: the server's target rules (npc_location_helper.cpp) said before the question, not after it
		blockMsg = _WarpBlockedReason(self.data)
		if blockMsg:
			NPCLocationHelperUtil.AppendChat(blockMsg)
			return

		try:

			if player.IsDead():

				return

		except Exception:

			pass

		try:

			if player.IsMountingHorse():

				return

		except Exception:

			pass

		try:

			if not _HelperIsActive(): # MT2009_PLUS_NPC_LOCATION_HELPER_V2

				self.__TicketDlg()

				return

		except Exception:

			pass

		self.__WarpDlg()

	def __TicketDlg(self):

		qtxt = ""

		try:

			qtxt = getattr(localeInfo, "NPC_LOCATION_HELPER_QUESTION_USE_TICKET", "")

		except Exception:

			pass

		if not qtxt:

			return

		self.__EnsureWarpDialog()

		self.warpDlg.SetText(qtxt)

		self.__FitWarpDialogWidth()

		self.warpDlg.SetAcceptEvent(ui.__mem_func__(self.__TicketAccept))

		self.warpDlg.SetCancelEvent(ui.__mem_func__(self.__DlgHide))

		self.__ShowWarpDialog()

	def __DlgHide(self):

		try:

			if self.warpDlg:

				self.warpDlg.Unlock()

				self.warpDlg.Hide()

		except Exception:

			pass

		self.__NotifyAtlasModal(False)

	def __EnsureWarpDialog(self):
		if self.warpDlg is not None:
			return
		try:
			if hasattr(uiCommon, "ExQuestionDialog"):
				self.warpDlg = uiCommon.ExQuestionDialog("TOP_MOST")
			else:
				self.warpDlg = uiCommon.QuestionDialog()
		except Exception:
			self.warpDlg = uiCommon.QuestionDialog()

	def __ShowWarpDialog(self):
		if not self.warpDlg:
			return
		self.__NotifyAtlasModal(True)
		try:
			self.warpDlg.Open()
		except Exception:
			try:
				self.warpDlg.SetCenterPosition()
				self.warpDlg.SetTop()
				self.warpDlg.Show()
			except Exception:
				pass
		try:
			self.warpDlg.Lock()
		except Exception:
			pass

	def __NotifyAtlasModal(self, block):
		try:
			if self._lvNpc:
				cb = getattr(self._lvNpc, "_atlasModalCb", None)
				if cb:
					cb(bool(block))
		except Exception:
			pass

	def __FitWarpDialogWidth(self):
		try:
			if not self.warpDlg:
				return
			tw, th = self.warpDlg.GetTextSize()
			w = max(340, int(tw) + 80)
			self.warpDlg.SetWidth(w)
		except Exception:
			pass

	def __TicketAccept(self):

		try:

			msg = getattr(localeInfo, "NPC_LOCATION_HELPER_MESSAGE_CANNOT_USE_STONE_OF_WARP_DISABLED", "")

			if msg:

				NPCLocationHelperUtil.AppendChat(msg)

		except Exception:

			pass

		self.__DlgHide()

	def __WarpDlg(self):

		self.__EnsureWarpDialog()

		q1 = ""

		try:

			q1 = getattr(localeInfo, "NPC_LOCATION_HELPER_WARP_TO_NPC_QUESTION_1", "%s %s")

		except Exception:

			q1 = "%s"

		txt = ""

		try:

			txt = q1 % (_StoneCost(self.data.get("map_index", 0)), self.data.get("name", "")) # MT2009: the server's cost

		except Exception:

			txt = ""

		try:

			self.warpDlg.SetText(txt)

		except Exception:

			pass

		self.__FitWarpDialogWidth()

		self.warpDlg.SetAcceptEvent(ui.__mem_func__(self.__DoWarpPkt))

		self.warpDlg.SetCancelEvent(ui.__mem_func__(self.__DlgHide))

		self.__ShowWarpDialog()

	def __DoWarpPkt(self):

		if self.data:

			try:

				npcLocationHelper.WarpToNPC(
					int(self.data["map_index"]),
					int(self.data["vnum"]),
					int(self.data["x"]),
					int(self.data["y"]),

				)

			except Exception:

				pass

		self.__DlgHide()


class ListViewNPCList(ListView):

	def __init__(self):
		ListView.__init__(self)

		self.ttItemRef = None

		self.roleTooltip = None

		self._nodeClickCb = None

		self.pickCbNpc = lambda r: None

		self._hoverPollWnd = None

		self._hoverNode = None

		self._dropDownBlockCb = lambda: False

		self._atlasModalCb = lambda block: None

	def SetDropDownBlockCb(self, fn):

		self._dropDownBlockCb = fn

	def SetAtlasModalBlockCb(self, fn):

		self._atlasModalCb = fn

	def SetNpcRowPickBlocked(self, block):

		for nd in self._nodes:

			try:

				nd.SetRowPickBlocked(block)

			except Exception:

				pass

	def ClearNodes(self):

		self._hoverNode = None

		ListView.ClearNodes(self)

	def SetNodeClickCb(self, fn):

		self._nodeClickCb = fn

	def SetPickCallback(self, fn):

		self.pickCbNpc = fn

	def AddNode(self, nodeWin):

		ListView.AddNode(self, nodeWin)

		try:

			nodeWin.BindListViewNpc(self)

		except Exception:

			pass

	def GetRoleTooltip(self):

		if self.roleTooltip is None:

			try:

				self.roleTooltip = uiToolTip.ToolTip()

			except Exception:

				pass

		return self.roleTooltip

	def SetItemToolTip(self, tt):

		self.ttItemRef = tt

		tip = self.GetRoleTooltip()

		if not tip:

			return

		for nd in self._nodes:

			try:

				nd.BindRoleTooltip(tip)

			except Exception:

				pass

	def RefreshNPCTeleportButton(self):

		for z in self._nodes:

			try:

				z.RefreshNPCTeleportButton()

			except Exception:

				pass

	def MakeListViewNpc(self, w, h):

		self.MakeListView(w, h, 28)

		try:
			if self._hoverPollWnd:
				self._hoverPollWnd.Hide()
				self._hoverPollWnd = None
		except Exception:
			self._hoverPollWnd = None

		self._hoverNode = None

		try:
			pollWnd = _NpcListHoverPollWnd(self)
			pollWnd.SetParent(self)
			pollWnd.SetPosition(0, 0)
			pollWnd.SetSize(max(1, self._w), max(1, self._vh))
			try:
				pollWnd.AddFlag("not_pick")
			except Exception:
				pass
			pollWnd.Show()
			self._hoverPollWnd = pollWnd
		except Exception:
			self._hoverPollWnd = None

	def _UpdateNpcRowHover(self):
		try:
			if self._dropDownBlockCb and self._dropDownBlockCb():
				try:
					if self._hoverNode:
						self._hoverNode.__OnRowHoverOut()
				except Exception:
					pass
				self._hoverNode = None
				return
		except Exception:
			pass

		hoverNode = None

		try:
			if not self.IsShow():
				return

			mx, my = wndMgr.GetMousePosition()
			gx, gy = self.GetGlobalPosition()
			gw = self.GetWidth()
			gh = self.GetHeight()

			if gx <= mx < gx + gw and gy <= my < gy + gh:
				for nd in self._nodes:
					try:
						if nd.IsShow() and nd.IsIn():
							hoverNode = nd
							break
					except Exception:
						pass
		except Exception:
			hoverNode = None

		if hoverNode is self._hoverNode:
			return

		try:
			if self._hoverNode and self._hoverNode is not hoverNode:
				self._hoverNode.__OnRowHoverOut()
		except Exception:
			pass

		self._hoverNode = hoverNode

		try:
			if hoverNode:
				hoverNode.__OnRowHoverIn()
		except Exception:
			pass

	def ClickNodeWindow(self, wobj):

		try:

			if self._dropDownBlockCb and self._dropDownBlockCb():

				return False

		except Exception:

			pass

		if wobj not in self._nodes:

			return False

		idx = self._nodes.index(wobj)

		if self._sel == idx:

			for nd in self._nodes:

				try:

					nd.OnUnselectNode()

				except Exception:

					pass

			self._sel = -1

			return False

		for nd in self._nodes:

			try:

				if nd is wobj:

					nd.OnSelectNode()

				else:

					nd.OnUnselectNode()

			except Exception:

				pass

		self._sel = idx

		return True


class MobDropItemListNode(ui.ImageBox):

	ROW_W = 186
	ROW_H = 18
	BG_DEFAULT = ROOT_PATH + "mob_drop_item_list_node_default.sub"
	BG_OVER = ROOT_PATH + "mob_drop_item_list_node_over.sub"
	BG_DOWN = ROOT_PATH + "mob_drop_item_list_node_down.sub"

	def __init__(self):
		ui.ImageBox.__init__(self)
		self._vnum = 0
		self._tooltip = None
		self._mobTooltip = None
		self._listView = None
		self._selectable = False
		self._rowHovered = False
		self._isSelected = False
		self._nameText = None

	def __del__(self):
		ui.ImageBox.__del__(self)

	def BindListView(self, lv):
		self._listView = lv

	def SetSelectable(self, flag):
		self._selectable = bool(flag)

	def SetItemToolTip(self, tooltip):
		self._tooltip = tooltip

	def SetMobToolTip(self, tooltip):
		self._mobTooltip = tooltip

	def __HideActiveTooltip(self):
		if self._selectable and self._mobTooltip:
			try:
				self._mobTooltip.HideToolTip()
			except Exception:
				try:
					self._mobTooltip.Hide()
				except Exception:
					pass
			return
		if self._tooltip:
			try:
				self._tooltip.HideToolTip()
			except Exception:
				try:
					self._tooltip.Hide()
				except Exception:
					pass

	def __ShowActiveTooltip(self):
		if self._selectable:
			NPCLocationHelperUtil.ShowMobGuideMobTooltip(self._mobTooltip, self._vnum)
			return
		NPCLocationHelperUtil.ShowMobGuideItemTooltip(self._tooltip, self._vnum)

	def __ApplyRowBackground(self, bgPath):
		try:
			self.LoadImage(bgPath)
		except Exception:
			pass
		try:
			wImg = self.GetWidth()
			if wImg > 0:
				self.SetSize(wImg, self.ROW_H)
			else:
				self.SetSize(self.ROW_W, self.ROW_H)
		except Exception:
			self.SetSize(self.ROW_W, self.ROW_H)

	def __RefreshRowBackground(self):
		if self._isSelected:
			self.__ApplyRowBackground(self.BG_DOWN)
		elif self._rowHovered:
			self.__ApplyRowBackground(self.BG_OVER)
		else:
			self.__ApplyRowBackground(self.BG_DEFAULT)

	def __EnsureNameText(self):
		if self._nameText:
			return
		self._nameText = ui.TextLine()
		self._nameText.SetParent(self)
		self._nameText.SetPosition(0, 1)
		try:
			self._nameText.SetWindowHorizontalAlignCenter()
			self._nameText.SetHorizontalAlignCenter()
		except Exception:
			pass
		self._nameText.Show()

	def SetData(self, vnum, name):
		self._vnum = int(vnum)
		self.__ApplyRowBackground(self.BG_DEFAULT)
		self.__EnsureNameText()
		try:
			self._nameText.SetText(str(name))
		except Exception:
			pass

	def GetVnum(self):
		return self._vnum

	def OnSelectNode(self):
		self._isSelected = True
		self.__RefreshRowBackground()

	def OnUnselectNode(self):
		self._isSelected = False
		self.__RefreshRowBackground()

	def OnMouseOverInNode(self):
		if self._rowHovered:
			return
		self._rowHovered = True
		self.__RefreshRowBackground()
		self.__ShowActiveTooltip()

	def OnMouseOverOutNode(self):
		if not self._rowHovered:
			return
		self._rowHovered = False
		self.__RefreshRowBackground()
		self.__HideActiveTooltip()

	def OnMouseOverIn(self):
		self.OnMouseOverInNode()

	def OnMouseOverOut(self):
		self.OnMouseOverOutNode()

	def OnMouseLeftButtonDown(self):
		if self._isSelected:
			self.__ApplyRowBackground(self.BG_DOWN)
		else:
			self.__ApplyRowBackground(self.BG_OVER)

	def OnMouseLeftButtonUp(self):
		self.__RefreshRowBackground()
		if not self._selectable or not self._listView:
			try:
				ui.ImageBox.OnMouseLeftButtonUp(self)
			except Exception:
				pass
			return
		try:
			self._listView.ClickNodeWindow(self)
		except Exception:
			pass
		try:
			ui.ImageBox.OnMouseLeftButtonUp(self)
		except Exception:
			pass


class ListViewMobList(ListView):

	def __init__(self):
		ListView.__init__(self)
		self._nodeClickCb = None

	def SetNodeClickCb(self, fn):
		self._nodeClickCb = fn

	def AddNode(self, nodeWin):
		ListView.AddNode(self, nodeWin)
		try:
			if hasattr(nodeWin, "BindListView"):
				nodeWin.BindListView(self)
			if hasattr(nodeWin, "SetSelectable"):
				nodeWin.SetSelectable(True)
		except Exception:
			pass

	def MakeListViewMob(self, w, h):
		self.MakeListView(max(40, int(w)), max(self.ROW_H, int(h)), 18)

	ROW_H = 18

	def ClickNodeWindow(self, wobj):
		if wobj not in self._nodes:
			return False
		idx = self._nodes.index(wobj)
		if self._sel == idx:
			for nd in self._nodes:
				try:
					nd.OnUnselectNode()
				except Exception:
					pass
			self._sel = -1
			if self._nodeClickCb:
				try:
					self._nodeClickCb(wobj)
				except Exception:
					pass
			return False
		for nd in self._nodes:
			try:
				if nd is wobj:
					nd.OnSelectNode()
				else:
					nd.OnUnselectNode()
			except Exception:
				pass
		self._sel = idx
		if self._nodeClickCb:
			try:
				self._nodeClickCb(wobj)
			except Exception:
				pass
		return True

	def GetSelectedVnum(self):
		i = self.GetSelectedIndex()
		if i < 0 or i >= len(self._nodes):
			return 0
		nd = self._nodes[i]
		try:
			return int(nd.GetVnum())
		except Exception:
			return 0


class NPCInfoWindow(ui.ScriptWindow):

	def __init__(self):
		ui.ScriptWindow.__init__(self)

		self.board = None

		self.bgWindow = None

		self.ddCat = None

		self.ddMap = None

		self.lvNpc = ListViewNPCList()

		self.mapObj = None

		self.pickAtlasCb = lambda drow: None

		self.mapPickCb = lambda mx: None

		self.mobRefreshCb = lambda mx: None

		self.killCbOuter = lambda: None

		self.preferMapSlug = ""

		self.npcListHost = None

		self.atlasModalCb = lambda block: None

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def LoadWindow(self):

		pyx = ui.PythonScriptLoader()

		okPath = ""

		okPath = "UIScript/npclocationhelper_npcinfowindow.py"

		try:

			pyx.LoadScriptFile(self, okPath)

		except Exception:

			import exception as exc

			exc.Abort("NPCInfoWindow.Load")

		try:

			self.board = self.GetChild("board")

			self.board.SetCloseEvent(ui.__mem_func__(self.Close))

			self.bgWindow = self.GetChild("bg_window")

			wNpc = self.GetChild("npc_list_window")

			self.npcListHost = wNpc

			wCat = self.GetChild("select_category_window")

			wMap = self.GetChild("select_map_window")

			self.ddCat = DropDownList(12)

			self.ddMap = DropDownList(12, DropDownList.MAP_DROP_LIST_VISIBLE_ROWS)

			self.ddCat.SetParent(wCat)

			self.ddCat.SetPosition(0, 0)

			try:

				self.ddCat.SetBox(wCat.GetWidth())

			except Exception:

				self.ddCat.SetBox(226)

			self.ddCat.Show()

			try:

				self.ddCat.SetPopupParent(self)

			except Exception:

				pass

			self.ddMap.SetParent(wMap)

			self.ddMap.SetPosition(0, 0)

			try:

				self.ddMap.SetBox(wMap.GetWidth())

			except Exception:

				self.ddMap.SetBox(226)

			self.ddMap.Show()
			try:
				self.ddMap.SetPopupParent(self)
			except Exception:
				pass

			self.lvNpc.SetParent(wNpc)

			self.lvNpc.MakeListViewNpc(max(220, wNpc.GetWidth() - 10), max(240, wNpc.GetHeight()) - 4)

			self.lvNpc.SetPosition(4, 0)

			self.lvNpc.Show()

			self.lvNpc.SetNodeClickCb(ui.__mem_func__(self.BarPickBridge))

			self.lvNpc.SetAtlasModalBlockCb(self.atlasModalCb)

		except Exception:

			pass

		for cc in xrange(8):

			if cc == 0:

				continue

			txt = NPCLocationHelperUtil.GetMapCategoryText(cc)

			if txt:

				self.ddCat.InsertItem(txt, cc)

		self.ddCat.SelectCategoryIndex(1)

		self.ddCat.SetPickEvent(ui.__mem_func__(self.OnCategoryGlue))

		self.ddMap.SetPickEvent(ui.__mem_func__(self.OnMapGlue))

		self.__WireDropDownPeers()

		self.lvNpc.SetDropDownBlockCb(ui.__mem_func__(self.__IsAnyDropDownOpen))

		self.RefreshMapDropForCat(1)

		self.__AutoSelectCurrentMap()

	def __IsAnyDropDownOpen(self):

		try:

			if self.ddCat and self.ddCat.openFlag:

				return True

		except Exception:

			pass

		try:

			if self.ddMap and self.ddMap.openFlag:

				return True

		except Exception:

			pass

		return False

	def __WireDropDownPeers(self):

		try:

			if self.ddCat and self.ddMap:

				self.ddCat.SetPeerDropDown(self.ddMap)

				self.ddMap.SetPeerDropDown(self.ddCat)

		except Exception:

			pass

	def SetPreferredMapSlug(self, slugText):
		try:
			self.preferMapSlug = str(slugText)
		except Exception:
			self.preferMapSlug = ""

	def _SetCategoryDropdownIndexSilent(self, catIx):

		try:

			catIx = int(catIx)

		except Exception:

			return False

		try:

			for ii in xrange(len(self.ddCat.itemCatIx)):

				try:

					if int(self.ddCat.itemCatIx[ii]) == catIx:

						self.ddCat.selIx = ii

						if self.ddCat.selText:

							self.ddCat.selText.SetText(self.ddCat.items[ii])

						self.ddCat.__BuildChrome()

						return True

				except Exception:

					pass

		except Exception:

			pass

		return False

	def SyncToMapRow(self, mx, bNotifyAtlas=False):

		if not mx:

			return False

		try:

			cat = int(mx.get("category", 1))

		except Exception:

			cat = 1

		self._SetCategoryDropdownIndexSilent(cat)

		self.RefreshMapDropForCat(cat)

		title = NPCLocationHelperUtil.GetMapDropDownListTitle(mx)

		iPick = -1

		for i in xrange(len(self.ddMap.items)):

			try:

				if self.ddMap.items[i] == title:

					iPick = i

					break

			except Exception:

				pass

		if iPick < 0:

			try:

				targetIx = int(mx.get("map_index", -1))

				bk = NPCLocationHelperUtil.ByCategoryBuckets()

				mapsArr = bk[int(cat)]

				for i in xrange(len(mapsArr)):

					try:

						if int(mapsArr[i].get("map_index", -2)) == targetIx:

							iPick = i

							break

					except Exception:

						pass

			except Exception:

				pass

		if iPick >= 0:

			self.ddMap.SelectItemIndex(iPick, False)

		else:

			try:

				self.ddMap.SetSelectedText(title)

				self.ddMap.selIx = -1

			except Exception:

				pass

		self.SetMapInfo(mx)

		if bNotifyAtlas:

			try:

				if self.mapPickCb:

					self.mapPickCb(mx)

			except Exception:

				pass

		return True

	def __AutoSelectCurrentMap(self):
		# Prefer map_index (player position), then explicit slug from atlas/minimap.
		slug = getattr(self, "preferMapSlug", "")
		mx = None
		try:
			mx = NPCLocationHelperUtil.FindMapInfoByIndex(int(_CurMapIndex()))
		except Exception:
			mx = None
		if mx is None:
			if slug:
				mx = NPCLocationHelperUtil.FindMapInfoBySlug(slug)

		if mx is not None:
			self.SyncToMapRow(mx, False)
			return

		# Fallback: current map not in helper map list - still show NPC/portal list via point file.
		if not slug:
			return
		try:
			fbIx = int(_CurMapIndex())
		except Exception:
			fbIx = 0
		try:
			self.mapObj = {"map_index": fbIx, "map_dir": slug, "map_name": slug, "category": 1}
		except Exception:
			self.mapObj = None
			return
		self.OnNPCListChanged(NPCLocationHelperUtil.ReadNpcPointFileByMapDir(slug, fbIx))

	def SetCloseEvent(self, fnKill):

		self.killCbOuter = fnKill

	def SetAtlasPickCb(self, fn):

		self.pickAtlasCb = fn

	def SetMapPickCb(self, fn):

		self.mapPickCb = fn

	def SetMobRefreshCb(self, fn):

		self.mobRefreshCb = fn

	def SetAtlasModalBlockCb(self, fn):

		self.atlasModalCb = fn

		try:

			self.lvNpc.SetAtlasModalBlockCb(fn)

		except Exception:

			pass

	def SetItemToolTip(self, tt):

		self.lvNpc.SetItemToolTip(tt)

	def __GetMapSelectPlaceholderText(self):

		return _UiScr("NPC_HELPER_NPC_INFO_MENU_SELECT_MAP", _Lc("NPC_HELPER_NPC_INFO_MENU_SELECT_MAP", ""))

	def __ResetMapDropToPlaceholder(self):

		try:

			self.ddMap.selIx = -1

			self.ddMap.SetSelectedText(self.__GetMapSelectPlaceholderText())

		except Exception:

			pass

		self.mapObj = None

		self.OnNPCListChanged([])

		try:

			if self.mobRefreshCb:

				self.mobRefreshCb(None)

		except Exception:

			pass

	def RefreshMapDropForCat(self, catIx):

		bk = NPCLocationHelperUtil.ByCategoryBuckets()

		try:

			mapsArr = bk[int(catIx)]

		except Exception:

			mapsArr = []

		self.ddMap.CloseDropDownWindow()

		oldItemsRef = ()

		oldItemsRef = tuple(self.ddMap.items)

		for kk in xrange(len(oldItemsRef)):

			pass

		self.ddMap = DropDownList(12, DropDownList.MAP_DROP_LIST_VISIBLE_ROWS)

		try:

			wMap = self.GetChild("select_map_window")

			self.ddMap.SetParent(wMap)

			self.ddMap.SetPosition(0, 0)

			self.ddMap.SetBox(wMap.GetWidth())

			self.ddMap.Show()

			self.ddMap.SetPickEvent(ui.__mem_func__(self.OnMapGlue))

			try:

				self.ddMap.SetPopupParent(self)

			except Exception:

				pass

			self.__WireDropDownPeers()

		except Exception:

			pass

		for mobj in mapsArr:

			title = NPCLocationHelperUtil.GetMapDropDownListTitle(mobj)

			self.ddMap.InsertItem(title)

			mobj["_title_cache"] = title

		self.__ResetMapDropToPlaceholder()

	def OnCategoryGlue(self, kk, lbl):

		self.RefreshMapDropForCat(kk)

		self.OnCategoryChanged([])

	def OnMapGlue(self, unusedIx, lblCap):

		try:

			if lblCap == self.__GetMapSelectPlaceholderText():

				return

		except Exception:

			pass

		for mx in NPCLocationHelperUtil.VisibleNpcMapsFiltered():

			cap = NPCLocationHelperUtil.GetMapDropDownListTitle(mx)

			if cap == lblCap:

				self.SetMapInfo(mx)

				self.mapObj = mx

				try:

					if self.mapPickCb:

						self.mapPickCb(mx)

				except Exception:

					pass

				return

	def SetMapInfo(self, mx):

		self.mapObj = mx

		self.OnNPCListChanged(NPCLocationHelperUtil.GetNPCInfos(mx["map_index"]))

		try:

			if self.mobRefreshCb:

				self.mobRefreshCb(mx)

		except Exception:

			pass

	def OnCategoryChanged(self, mapsArr):

		pass

	def Close(self):

		self.Hide()

		try:

			self.killCbOuter()

		except Exception:

			pass

	def __IsMouseOverNpcListArea(self):
		if _NpLocMouseInRect(self.npcListHost):
			return True
		if not self.lvNpc:
			return False
		try:
			if self.lvNpc.IsIn():
				return True
		except Exception:
			pass
		for ww in (
			self.lvNpc,
			self.lvNpc.clipWindow,
			self.lvNpc.body,
			self.lvNpc.scroll,
		):
			if _NpLocMouseInRect(ww):
				return True
		return False

	def OnMouseWheelScrollLines(self, lineDelta):
		wheelDir = 1 if lineDelta < 0 else -1
		try:
			if self.ddMap and self.ddMap.openFlag:
				if self.ddMap.OnListMouseWheel(wheelDir):
					return True
		except Exception:
			pass
		try:
			if self.ddCat and self.ddCat.openFlag:
				if self.ddCat.OnListMouseWheel(wheelDir):
					return True
		except Exception:
			pass
		try:
			if self.__IsMouseOverNpcListArea() and self.lvNpc:
				return self.lvNpc.OnMouseWheelScrollLines(lineDelta)
		except Exception:
			pass
		return False

	def OnMouseWheelButtonUp(self):
		return self.OnMouseWheelScrollLines(-1)

	def OnMouseWheelButtonDown(self):
		return self.OnMouseWheelScrollLines(1)

	def OnNPCListChanged(self, infos):

		self.lvNpc.ClearNodes()

		if self.mapObj is None:

			return

		for pack in infos:

			rowNpc = NPCListNode()

			rowNpc.onRowInfo = self.pickAtlasCb

			rowNpc.NotifyBarCb = ui.__mem_func__(self.BarPickBridge)

			rowNpc.BindRoleTooltip(self.lvNpc.GetRoleTooltip())

			try:

				rowNpc.SetNPCData(
					pack["vnum"], pack["name"], pack["x"], pack["y"], pack["icon"], pack.get("land_id", 0)

				)

			except Exception:

				pass
			try:
				if "quest_state" in pack:
					rowNpc.SetQuestState(pack.get("quest_state", -1))
			except Exception:
				pass

			try:
				rowNpc.BindMapIx(int(pack.get("map_index", self.mapObj["map_index"])))
			except Exception:
				try:
					rowNpc.BindMapIx(self.mapObj["map_index"])
				except Exception:
					pass

			self.lvNpc.AddNode(rowNpc)

		try:
			self.lvNpc.Refresh()

			# After rebuild, force list to top so first row is visible.
			try:
				if self.lvNpc.scroll and hasattr(self.lvNpc.scroll, "SetPos"):
					self.lvNpc.scroll.SetPos(0.0, False)
					self.lvNpc.Refresh()
			except Exception:
				pass
		except Exception:
			pass

	def BarPickBridge(self, wLeaf):

		if self.__IsAnyDropDownOpen():

			return

		if self.lvNpc.ClickNodeWindow(wLeaf):

			self.__AfterNpcIx()

		else:

			self.ClearNPCSelection()

	def ClearNPCSelection(self):

		try:

			if self.lvNpc.GetSelectedIndex() >= 0:

				for nd in self.lvNpc._nodes:

					try:

						nd.OnUnselectNode()

					except Exception:

						pass

				self.lvNpc._sel = -1

		except Exception:

			pass

		try:

			miniMap.UnselectNPC()

		except Exception:

			pass

	def __AfterNpcIx(self):

		i = self.lvNpc.GetSelectedIndex()

		if i < 0 or i >= len(self.lvNpc._nodes):

			return

		d = getattr(self.lvNpc._nodes[i], "data", None)

		if not d:

			return

		try:

			_SelectNPC(
				int(d["map_index"]),
				int(d["vnum"]),
				int(d["x"]) * 100,
				int(d["y"]) * 100,
			)

		except Exception:

			pass

		try:

			self.pickAtlasCb(d)

		except Exception:

			pass

	def RefreshNPCTeleportButton(self):

		try:

			self.lvNpc.RefreshNPCTeleportButton()

		except Exception:

			pass

	def UnlockMapMessage(self, mapDirSlug):

		try:

			tplMsg = ""

			tplMsg = getattr(localeInfo, "NPC_LOCATION_HELPER_ATLAS_UNLOCKED_MAP_2", "%s")

			NPCLocationHelperUtil.AppendChat(tplMsg % str(mapDirSlug))

		except Exception:

			pass

	def SelectedNPCIsNear(self, notify=True):

		if self.mapObj is None:

			return False

		try:

			if _CurMapIndex() != int(self.mapObj["map_index"]):

				return False

		except Exception:

			return False

		iSel = self.lvNpc.GetSelectedIndex()

		if iSel < 0 or iSel >= len(self.lvNpc._nodes):

			return False

		dLeaf = getattr(self.lvNpc._nodes[iSel], "data", None)

		if dLeaf is None:

			return False

		px, py, uz = player.GetMainCharacterPosition()

		dSq = float(px - float(dLeaf["x"]) * 100.0) ** 2 + float(py - float(dLeaf["y"]) * 100.0) ** 2

		if dSq <= float(NEAR_NPC_RADIUS_SQ):

			if notify:

				try:

					NPCLocationHelperUtil.AppendChat(
						getattr(localeInfo, "NPC_LOCATION_HELPER_MESSAGE_SELECTED_NPC_IS_NEAR", "")
					)

				except Exception:

					pass

			return True

		return False


class MobInfoWindow(ui.ScriptWindow):

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.board = None
		self.ttMob = None
		self.ttMobInfo = None
		self._mapIndex = 0
		self.mvListUi = ListViewMobList()
		self.dropLv = ListView()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def LoadWindow(self):
		ldx = ui.PythonScriptLoader()
		try:
			ldx.LoadScriptFile(self, "UIScript/npclocationhelper_mobinfowindow.py")
		except Exception:
			import exception as excTwo
			excTwo.Abort("MobInfoWindow.Load")
		self.board = self.GetChild("board")
		self.board.SetCloseEvent(ui.__mem_func__(self.Close))
		wMb = None
		wDropWrap = None
		try:
			wMb = self.GetChild("mob_info_window")
		except Exception:
			wMb = None
		try:
			wDropWrap = self.GetChild("drop_item_info_window")
		except Exception:
			wDropWrap = None
		if wMb:
			self.mvListUi.SetParent(wMb)
			self.mvListUi.MakeListViewMob(wMb.GetWidth(), wMb.GetHeight())
			self.mvListUi.SetPosition(0, 0)
			self.mvListUi.SetNodeClickCb(ui.__mem_func__(self.__OnMobRowSelected))
			self.mvListUi.Show()
		if wDropWrap:
			self.dropLv.SetParent(wDropWrap)
			self.dropLv.MakeListView(wDropWrap.GetWidth(), wDropWrap.GetHeight(), 18)
			self.dropLv.SetPosition(0, 0)
			self.dropLv.Show()

	def SetItemToolTip(self, tt):
		self.ttMob = tt

	def __GetMobInfoTooltip(self):
		if self.ttMobInfo is None:
			try:
				self.ttMobInfo = uiToolTip.ToolTip()
				self.ttMobInfo.Hide()
			except Exception:
				self.ttMobInfo = None
		return self.ttMobInfo

	def SetMapIndex(self, mapIdx):
		try:
			self._mapIndex = int(mapIdx)
		except Exception:
			self._mapIndex = 0

	def SetMapFromInfo(self, mx):
		if mx:
			try:
				self.SetMapIndex(mx.get("map_index", 0))
			except Exception:
				self.SetMapIndex(0)
		else:
			self.SetMapIndex(0)
		if self.IsShow():
			self.RefreshMobGuide()

	def RefreshMobGuide(self):
		self.OnMobListChanged()
		self.OnDropItemListChanged()

	def _ResolveMobListForMap(self):
		if self._mapIndex > 0:
			return NPCLocationHelperUtil.MobsOnMap(self._mapIndex)
		try:
			return NPCLocationHelperUtil.MobsOnMap(int(_CurMapIndex()))
		except Exception:
			return []

	def OnMobListChanged(self, mob_list=None):
		self.mvListUi.ClearNodes()
		if mob_list is None:
			mob_list = self._ResolveMobListForMap()
		seenVnums = set()
		for block in mob_list:
			try:
				mobVnum = int(block["mob_vnum"])
			except Exception:
				continue
			if mobVnum in seenVnums:
				continue
			seenVnums.add(mobVnum)
			nTitle = ""
			try:
				nTitle = nonplayer.GetMonsterName(mobVnum)
			except Exception:
				nTitle = ""
			if not nTitle:
				nTitle = "%d" % mobVnum
			row = MobDropItemListNode()
			row.SetMobToolTip(self.__GetMobInfoTooltip())
			row.SetData(mobVnum, nTitle)
			self.mvListUi.AddNode(row)
		self.mvListUi.Refresh()
		if self.mvListUi._nodes:
			try:
				self.mvListUi._nodes[0].OnSelectNode()
			except Exception:
				pass
			self.mvListUi._sel = 0
		else:
			self.mvListUi._sel = -1

	def __OnMobRowSelected(self, wmob):
		self.OnDropItemListChanged()

	def OnDropItemListChanged(self, drop_item_list=None):
		self.dropLv.ClearNodes()
		if drop_item_list is None:
			vv = self.mvListUi.GetSelectedVnum()
			if vv <= 0:
				return
			drop_item_list = NPCLocationHelperUtil.DropsForMob(vv)
		for itemVnum in drop_item_list:
			try:
				itemVnum = int(itemVnum)
			except Exception:
				continue
			itemName = NPCLocationHelperUtil.GetItemNameByVnumSafe(itemVnum)
			row = MobDropItemListNode()
			row.SetItemToolTip(self.ttMob)
			row.SetData(itemVnum, itemName)
			self.dropLv.AddNode(row)
		self.dropLv.Refresh()

	def __IsMouseOverMobList(self):
		if not self.mvListUi:
			return False
		try:
			if self.mvListUi.IsIn():
				return True
		except Exception:
			pass
		for ww in (self.mvListUi, self.mvListUi.clipWindow, self.mvListUi.body, self.mvListUi.scroll):
			if _NpLocMouseInRect(ww):
				return True
		return False

	def __IsMouseOverDropList(self):
		if not self.dropLv:
			return False
		try:
			if self.dropLv.IsIn():
				return True
		except Exception:
			pass
		for ww in (self.dropLv, self.dropLv.clipWindow, self.dropLv.body, self.dropLv.scroll):
			if _NpLocMouseInRect(ww):
				return True
		return False

	def OnMouseWheelScrollLines(self, lineDelta):
		try:
			if self.__IsMouseOverDropList():
				return self.dropLv.OnMouseWheelScrollLines(lineDelta)
		except Exception:
			pass
		try:
			if self.__IsMouseOverMobList():
				return self.mvListUi.OnMouseWheelScrollLines(lineDelta)
		except Exception:
			pass
		return False

	def OnMouseWheelButtonUp(self):
		return self.OnMouseWheelScrollLines(-1)

	def OnMouseWheelButtonDown(self):
		return self.OnMouseWheelScrollLines(1)

	def Close(self):
		try:
			self.Hide()
		except Exception:
			pass


class NPCLocationHelper_Atlas(ui.ScriptWindow):

	class AtlasRenderer(ui.Window):

		def __init__(self, outerWin):

			ui.Window.__init__(self)

			self._atlRoot = outerWin

			self._grab = False

			self._lastMx = None

			self._lastMy = None

		def __del__(self):

			try:

				ui.Window.__del__(self)

			except Exception:

				pass

		def HideAtlas(self):
			try:
				miniMap.HideAtlas()
			except Exception:
				pass

		def ShowAtlas(self):
			try:

				miniMap.ShowAtlas()
			except Exception:

				pass

		def OnUpdate(self):

			miniMap.UpdateAtlas()

			if self._atlRoot:

				try:

					self._atlRoot._TryDeferredAtlasFit()

				except Exception:

					pass

			if self._grab and self._lastMx is not None:

				mmX, mmY = wndMgr.GetMousePosition()

				dMx = mmX - self._lastMx

				dMy = mmY - self._lastMy

				self._lastMx, self._lastMy = mmX, mmY

				try:

					self._atlRoot._AtlasDragPixels(-float(dMx), -float(dMy))

				except Exception:

					pass

		def OnRender(self):

			pgX, pgY = self.GetGlobalPosition()

			try:

				floatX = float(pgX)

				floatY = float(pgY)

				if hasattr(miniMap, "SetAtlasNpcHelperView"):

					miniMap.SetAtlasNpcHelperView(1)

				miniMap.RenderAtlas(floatX, floatY)

			except Exception:

				pass

		def OnMouseLeftButtonDown(self):

			self._grab = True

			mmXb, mmYb = wndMgr.GetMousePosition()

			self._lastMx = mmXb

			self._lastMy = mmYb

			return True

		def OnMouseLeftButtonUp(self):

			self._grab = False

			self._lastMx = None

			self._lastMy = None

			try:

				return ui.Window.OnMouseLeftButtonUp(self)

			except Exception:

				pass

	def __init__(self):
		ui.ScriptWindow.__init__(self)

		self.tooltipItemRefExt = None

		self.tooltipInfo = MapTextTip()

		try:
			self.tooltipInfo.Hide()
		except Exception:
			pass

		self._atlasMarkTooltip = None
		self._atlasMarkTooltipVisible = False

		try:
			self.infoGuildMark = ui.MarkBox()

			try:
				self.infoGuildMark.Hide()
			except Exception:
				pass
		except Exception:
			self.infoGuildMark = None

		self.AtlasMainWindow = None

		self.boardOuter = None

		self.tabTitleTextHandle = None

		self.rawMapKey = ""

		self.IsShowWindowValue = False

		self.lastBoardPos = [0, 74]

		self._npcdlg = None
		self._npcSidebarVisible = False

		self._mobdlg = None

		self.cbNpcSelExt = lambda d: None

		self.faceIfOuter = None

		self.guildLandShown = False

		self.curMapRow = None

		self.txAtlas1Win = None

		self.txAtlas2Win = None

		self.rxAtlas = None
		self.shellAtlas = None

		self._atlRxTrack = 0.0

		self._atlRyTrack = 0.0

		self.miniMapOwner = None

		self.titleBarSwitchSmallBtn = None
		self.titleBarExpandBtn = None
		self._titleBarExpandBtnTip = None
		self._titleBarExpandBtnTipText = ""

		self._atlasBarButtonTooltip = None
		self._atlasBarButtonTooltipVisible = False

		self._inBoardAtlasW = HELPER_ATLAS_VIEW_W

		self._inBoardAtlasH = HELPER_ATLAS_VIEW_H

		self.__InitAtlasRuntimeMembers()

	def __InitAtlasRuntimeMembers(self):
		if not getattr(self, "tooltipInfo", None):
			self.tooltipInfo = MapTextTip()
			try:
				self.tooltipInfo.Hide()
			except Exception:
				pass

		if not hasattr(self, "infoGuildMark"):
			try:
				self.infoGuildMark = ui.MarkBox()
				try:
					self.infoGuildMark.Hide()
				except Exception:
					pass
			except Exception:
				self.infoGuildMark = None

		self._atlasMarkTooltip = None
		self._atlasMarkTooltipVisible = False
		if not hasattr(self, "_atlasBarButtonTooltip"):
			self._atlasBarButtonTooltip = None
		if not hasattr(self, "_atlasBarButtonTooltipVisible"):
			self._atlasBarButtonTooltipVisible = False

	def SetMiniMapOwner(self, owner):
		self.miniMapOwner = owner

	def SetNPCSelectedCallback(self, evHandler):

		try:

			if evHandler:

				self.cbNpcSelExt = evHandler

			else:

				self.cbNpcSelExt = lambda d: None

		except Exception:

			pass

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def LoadWindow(self):

		ldxAtlas = ui.PythonScriptLoader()

		try:

			ldxAtlas.LoadScriptFile(self, "UIScript/npclocationhelper_atlaswindow.py")

		except Exception:

			import dbg

			dbg.TraceError("NPCLocationHelper_Atlas.LoadWindow: uiscript load failed")
			_LogTrace("NPCLocationHelper_Atlas.LoadWindow (uiscript/npclocationhelper_atlaswindow.py)")

			return False

		self.__InitAtlasRuntimeMembers()

		try:

			self.boardOuter = self.GetChild("board")

			self.boardOuter.SetCloseEvent(ui.__mem_func__(self.Close))

			tooltipInfo = getattr(self, "tooltipInfo", None)
			if tooltipInfo:
				tooltipInfo.SetParent(self.boardOuter)

			infoGuildMark = getattr(self, "infoGuildMark", None)
			if infoGuildMark:
				infoGuildMark.SetParent(self.boardOuter)

			if not self.boardOuter:

				import dbg

				dbg.TraceError("NPCLocationHelper_Atlas.LoadWindow: board missing")

				return False

			shellAtlas = None

			shellAtlas = self.GetChild("atlas_window")
			self.shellAtlas = shellAtlas

			self.txAtlas1Win = self.GetChild("atlas_text_1")

			self.txAtlas2Win = self.GetChild("atlas_text_2")

			self.rxAtlas = self.AtlasRenderer(self)

			self.rxAtlas.SetParent(shellAtlas)

			try:

				self.rxAtlas.SetSize(shellAtlas.GetWidth(), shellAtlas.GetHeight())

				self.rxAtlas.SetPosition(0, 0)

				self.rxAtlas.SetPickAlways()

			except Exception:

				pass

			if getattr(app, "ENABLE_CLIP_MASK", 0) and shellAtlas and hasattr(self.rxAtlas, "SetClippingMaskWindow"):

				try:

					self.rxAtlas.SetClippingMaskWindow(shellAtlas)

				except Exception:

					pass

			self.rxAtlas.HideAtlas()

			self.rxAtlas.Hide()

			self.AtlasMainWindow = self.rxAtlas

			guildBtnSelf = None

			dropMobBtnSelf = None

			try:

				guildBtnSelf = self.GetChild("show_guild_land_button")

			except Exception:

				guildBtnSelf = None

			try:

				dropMobBtnSelf = self.GetChild("drop_item_info_button")

			except Exception:

				dropMobBtnSelf = None

			btUpPx = None

			btDwPx = None

			btMyGPS = None

			try:

				btUpPx = self.GetChild("scale_up_button")

				btDwPx = self.GetChild("scale_down_button")

				btMyGPS = self.GetChild("my_location_button")

			except Exception:

				pass

			if guildBtnSelf:

				self.__BindAtlasBarButtonThinTooltip(guildBtnSelf, "NPC_LOCATION_HELPER_TOOLTIP_GUILD_LAND")

				try:

					guildBtnSelf.SAFE_SetEvent(ui.__mem_func__(self.ToggleGuildLand))

				except Exception:

					try:

						guildBtnSelf.SetEvent(ui.__mem_func__(self.ToggleGuildLand))

					except Exception:

						pass

			if dropMobBtnSelf:

				self.__BindAtlasBarButtonThinTooltip(dropMobBtnSelf, "NPC_LOCATION_HELPER_TOOLTIP_DROP_ITEM_INFO")

				try:

					dropMobBtnSelf.SAFE_SetEvent(ui.__mem_func__(self.ToggleMobInfoWindow))

				except Exception:

					try:

						dropMobBtnSelf.SetEvent(ui.__mem_func__(self.ToggleMobInfoWindow))

					except Exception:

						pass

			if btUpPx:

				self.__BindAtlasBarButtonThinTooltip(btUpPx, "NPC_LOCATION_HELPER_TOOLTIP_SCALE_UP")

				btUpPx.SetEvent(ui.__mem_func__(self.OnAtlasScaleGrow))

			if btDwPx:

				self.__BindAtlasBarButtonThinTooltip(btDwPx, "NPC_LOCATION_HELPER_TOOLTIP_SCALE_DOWN")

				btDwPx.SetEvent(ui.__mem_func__(self.OnAtlasScaleShrink))

			if btMyGPS:

				self.__BindAtlasBarButtonThinTooltip(btMyGPS, "NPC_LOCATION_HELPER_TOOLTIP_MY_LOCATION")

				try:

					btMyGPS.SAFE_SetEvent(ui.__mem_func__(self.__AtlasMyPosition))

				except Exception:

					try:

						btMyGPS.SetEvent(ui.__mem_func__(self.__AtlasMyPosition))

					except Exception:

						pass

		except Exception:

			import dbg

			dbg.TraceError("NPCLocationHelper_Atlas.LoadWindow: bind children failed")
			_LogTrace("NPCLocationHelper_Atlas.LoadWindow (bind children)")

			return False

		self.SetPosition(int(self.lastBoardPos[0]), int(self.lastBoardPos[1]))

		self._SyncRefAtlasViewport()

		return True

	def _ResolveHelperAtlasViewport(self):

		mapW = HELPER_ATLAS_VIEW_W

		mapH = HELPER_ATLAS_VIEW_H

		try:

			bgWin = self.GetChild("bg_window")

			shellAtlas = self.GetChild("atlas_window")

			ax, ay = shellAtlas.GetLocalPosition()

			innerW = int(bgWin.GetWidth()) - int(ax) * 2

			if innerW > mapW:

				mapW = innerW

			mapH = max(mapH, int(shellAtlas.GetHeight()))

		except Exception:

			pass

		return mapW, mapH

	def _SyncRefAtlasViewport(self):

		mapW, mapH = self._ResolveHelperAtlasViewport()

		self._inBoardAtlasW = mapW

		self._inBoardAtlasH = mapH

		try:

			if self.rxAtlas:

				self.rxAtlas.SetSize(mapW, mapH)

		except Exception:

			pass

		try:

			if hasattr(miniMap, "SetAtlasHelperViewportSize"):

				miniMap.SetAtlasHelperViewportSize(float(mapW), float(mapH))

		except Exception:

			pass

	def __SetAtlasRenderPosWithinMinMax(self, posX, posY):

		try:

			atlasX, atlasY = self.__GetAtlasRenderPos(posX, posY)

			miniMap.ChangeAtlasRenderPos(atlasX, atlasY)

			self._atlRxTrack = atlasX

			self._atlRyTrack = atlasY

		except Exception:

			pass

	def __GetAtlasRenderPos(self, posX, posY):

		# uiNPCLocationHelper.__GetAtlasRenderPos (26.0.6 dump): atlas_scale, max_pos_x/y, width_ratio, height_ratio.
		try:

			atlasScale = float(miniMap.GetAtlasScale())

		except Exception:

			atlasScale = 1.0

		try:

			maxPosX, maxPosY = miniMap.GetAtlasMaxPos()

		except Exception:

			maxPosX = 0.0

			maxPosY = 0.0

		try:

			widthRatio = float(miniMap.GetAtlasWidthHeightRatio())

		except Exception:

			widthRatio = 1.0

		if widthRatio <= 0.0:

			widthRatio = 1.0

		heightRatio = 1.0 / widthRatio

		atlasRenderPosX = float(posX)

		atlasRenderPosY = float(posY)

		if atlasRenderPosX < 0.0:

			atlasRenderPosX = 0.0

		if atlasRenderPosY < 0.0:

			atlasRenderPosY = 0.0

		if atlasRenderPosX > float(maxPosX):

			atlasRenderPosX = float(maxPosX)

		if atlasRenderPosY > float(maxPosY):

			atlasRenderPosY = float(maxPosY)

		return atlasRenderPosX, atlasRenderPosY

	def __AtlasCenterPosition(self):

		try:

			maxXpane, maxYpane = miniMap.GetAtlasMaxPos()

		except Exception:

			maxXpane = 0.0

			maxYpane = 0.0

		self.__SetAtlasRenderPosWithinMinMax(0.5 * float(maxXpane), 0.5 * float(maxYpane))

	def _TryDeferredAtlasFit(self):

		if getattr(self, "_atlFitDone", False):

			return

		try:

			bGet, imgW, imgH = miniMap.GetAtlasSize()

		except Exception:

			bGet = 0

			imgW = 0

			imgH = 0

		if not bGet or imgW <= 0 or imgH <= 0:

			return

		self._FitAtlasScaleToBoard()

		self._atlFitDone = True

	def _FitAtlasScaleToBoard(self):

		# One rule: full map visible (no crop). Widen only when height still fits at that scale.
		mapW = float(getattr(self, "_inBoardAtlasW", HELPER_ATLAS_VIEW_W))

		mapH = float(getattr(self, "_inBoardAtlasH", HELPER_ATLAS_VIEW_H))

		try:

			bGet, imgW, imgH = miniMap.GetAtlasSize()

		except Exception:

			bGet = 0

			imgW = 0

			imgH = 0

		if not bGet or imgW <= 0 or imgH <= 0:

			try:

				miniMap.SetAtlasScale(1.0)

			except Exception:

				pass

			return

		try:

			scaleW = mapW / float(imgW)

			scaleH = mapH / float(imgH)

			scaleContain = min(scaleW, scaleH)

			if float(imgH) * scaleW <= mapH + 0.5:

				useScale = scaleW

			else:

				useScale = scaleContain

		except Exception:

			useScale = 1.0

		useScale = _ClampFitAtlasScale(useScale)

		try:

			miniMap.SetAtlasScale(useScale)

		except Exception:

			pass

		try:

			if hasattr(miniMap, "CenterAtlasRenderPos"):

				miniMap.CenterAtlasRenderPos()

				if hasattr(miniMap, "GetAtlasPanExtents"):

					minX, maxX, minY, maxY = miniMap.GetAtlasPanExtents()

					self._atlRxTrack = 0.5 * (float(minX) + float(maxX))

					self._atlRyTrack = 0.5 * (float(minY) + float(maxY))

			else:

				self.__AtlasCenterPosition()

		except Exception:

			self.__AtlasCenterPosition()

	def _SyncAtlasRenderPosTrack(self):

		try:

			if hasattr(miniMap, "GetAtlasRenderPos"):

				rx, ry = miniMap.GetAtlasRenderPos()

				self._atlRxTrack = float(rx)

				self._atlRyTrack = float(ry)

		except Exception:

			pass

	def __ResolvePlayerMapRow(self):

		try:

			mx = NPCLocationHelperUtil.FindMapInfoByIndex(int(_CurMapIndex()))

			if mx:

				return mx

		except Exception:

			pass

		mapDir = ""

		try:

			if self.miniMapOwner and getattr(self.miniMapOwner, "mapName", ""):

				mapDir = str(self.miniMapOwner.mapName)

		except Exception:

			pass

		if mapDir:

			rawKey = ""
			try:
				rawKey = str(getattr(self, "rawMapKey", ""))
			except Exception:
				rawKey = ""

			bMapAlreadyActive = (rawKey and rawKey == mapDir)

			try:

				return NPCLocationHelperUtil.FindMapInfoBySlug(mapDir)

			except Exception:

				pass

		return None

	def __ResolvePlayerMapDir(self):

		mx = self.__ResolvePlayerMapRow()

		if mx:

			try:

				return mx.get("map_dir", "")

			except Exception:

				pass

		return ""

	def __SyncNpcSidebarToMapRow(self, mx):

		if not mx:

			return

		try:

			if self._npcSidebarVisible and self._npcdlg is None:

				self.OpenNPCInfoWindow()

			if self._npcdlg:

				slug = mx.get("map_dir", "")

				if slug:

					self._npcdlg.SetPreferredMapSlug(slug)

				self._npcdlg.SyncToMapRow(mx, False)

		except Exception:

			pass

	def __SyncNpcSidebarToMapDir(self, mapDir):

		mx = self.__ResolvePlayerMapRow()

		if mx is None and mapDir:

			try:

				mx = NPCLocationHelperUtil.FindMapInfoBySlug(mapDir)

			except Exception:

				mx = None

		self.__SyncNpcSidebarToMapRow(mx)

	def __AtlasMyPosition(self):

		mx = self.__ResolvePlayerMapRow()

		mapDir = ""

		if mx:

			try:

				mapDir = mx.get("map_dir", "")

			except Exception:

				mapDir = ""

		if not mapDir:

			mapDir = self.__ResolvePlayerMapDir()

		if mapDir:
			rawKey = ""
			try:
				rawKey = str(getattr(self, "rawMapKey", ""))
			except Exception:
				rawKey = ""

			bMapAlreadyActive = (rawKey and rawKey == mapDir)

			try:

				miniMap.UnselectNPC()

			except Exception:

				pass

			try:

				if hasattr(miniMap, "SetAtlasNpcHelperView"):

					miniMap.SetAtlasNpcHelperView(1)

			except Exception:

				pass

			if not bMapAlreadyActive:

				try:

					if hasattr(miniMap, "LoadAtlas"):

						miniMap.LoadAtlas()

				except Exception:

					pass

				self._atlFitDone = False

				self.SetMapName(mapDir)

			self.__SyncNpcSidebarToMapRow(mx)

		try:

			ppx, ppy, pzSkip = player.GetMainCharacterPosition()

			sxScr, syScr = miniMap.ConvertGlobalPosToAtlasPos(float(ppx), float(ppy))

			vpW = float(HELPER_ATLAS_VIEW_W)

			vpH = float(HELPER_ATLAS_VIEW_H)

			if hasattr(miniMap, "GetAtlasHelperViewportSize"):

				vpW, vpH = miniMap.GetAtlasHelperViewportSize()

			rtx = float(getattr(self, "_atlRxTrack", 0.0))

			rty = float(getattr(self, "_atlRyTrack", 0.0))

			atlasX, atlasY = self.__GetAtlasRenderPos(

				float(sxScr) + rtx - vpW * 0.5,

				float(syScr) + rty - vpH * 0.5,

			)

			self.__SetAtlasRenderPosWithinMinMax(atlasX, atlasY)

		except Exception:

			pass

	def __IsMouseOverNpcSidebar(self):
		if not self._npcSidebarVisible or not self._npcdlg:
			return False
		try:
			if not self._npcdlg.IsShow():
				return False
		except Exception:
			return False
		return _NpLocMouseInRect(self._npcdlg)

	def __IsMouseOverMobGuide(self):
		if not self._mobdlg:
			return False
		try:
			if not self._mobdlg.IsShow():
				return False
		except Exception:
			return False
		return _NpLocMouseInRect(self._mobdlg)

	def __NpcSidebarWheelScroll(self, lineDelta):
		if not self.__IsMouseOverNpcSidebar() or not self._npcdlg:
			return False
		try:
			return self._npcdlg.OnMouseWheelScrollLines(lineDelta)
		except Exception:
			pass
		return False

	def __MobGuideWheelScroll(self, lineDelta):
		if not self.__IsMouseOverMobGuide() or not self._mobdlg:
			return False
		try:
			return self._mobdlg.OnMouseWheelScrollLines(lineDelta)
		except Exception:
			pass
		return False

	def OnMouseWheelScrollLines(self, lineDelta):
		if self.__MobGuideWheelScroll(lineDelta):
			return True
		if self.__NpcSidebarWheelScroll(lineDelta):
			return True
		if self.__IsMouseOverMobGuide():
			return True
		if self.__IsMouseOverNpcSidebar():
			return True
		return False

	def OnMouseWheelButtonUp(self):
		if self.__MobGuideWheelScroll(-1):
			return True
		if self.__IsMouseOverMobGuide():
			return True
		if self.__NpcSidebarWheelScroll(-1):
			return True
		if self.__IsMouseOverNpcSidebar():
			return True
		self.__AtlasScaleUp()
		return True

	def OnMouseWheelButtonDown(self):
		if self.__MobGuideWheelScroll(1):
			return True
		if self.__IsMouseOverMobGuide():
			return True
		if self.__NpcSidebarWheelScroll(1):
			return True
		if self.__IsMouseOverNpcSidebar():
			return True
		self.__AtlasScaleDown()
		return True

	def __ClaimWheelTopWindow(self):
		if not getattr(app, "ENABLE_MOUSE_WHEEL_TOP_WINDOW", 0):
			return
		try:
			wndMgr.SetWheelTopWindow(self.hWnd)
		except Exception:
			pass

	def __ReleaseWheelTopWindow(self):
		if not getattr(app, "ENABLE_MOUSE_WHEEL_TOP_WINDOW", 0):
			return
		try:
			wndMgr.ClearWheelTopWindow()
		except Exception:
			pass

	def __SetAtlasModalBlocked(self, block):
		if block:
			self.__ReleaseWheelTopWindow()
		elif self.IsShowWindowValue:
			self.__ClaimWheelTopWindow()

	def LayoutHelperWindows(self):
		sw = wndMgr.GetScreenWidth()
		sh = wndMgr.GetScreenHeight()
		totalW = HELPER_ATLAS_W + HELPER_NPC_W + HELPER_LAYOUT_GAP
		x0 = max(0, int((sw - totalW) / 2))
		y0 = max(0, int((sh - HELPER_ATLAS_H) / 2))
		self.SetPosition(x0, y0)
		self.lastBoardPos = [x0, y0]
		return x0, y0

	def __RaiseAtlasChrome(self):

		if self.boardOuter:

			try:

				self.boardOuter.Show()

				self.boardOuter.SetTop()

			except Exception:

				pass

		for childName in (
			"bg_window",
			"tab_menu_1_atlas",
			"show_guild_land_button",
			"drop_item_info_button",
			"scale_up_button",
			"scale_down_button",
			"my_location_button",
		):

			try:

				w = self.GetChild(childName)

				w.Show()

				w.SetTop()

			except Exception:

				pass

		self.__RaiseTitleBarButtons()

	def __EnsureAtlasBarButtonTooltip(self):
		if self._atlasBarButtonTooltip is not None:
			return
		try:
			self._atlasBarButtonTooltip = uiToolTip.ToolTip()
			self._atlasBarButtonTooltip.Hide()
		except Exception:
			self._atlasBarButtonTooltip = None

	def __BindAtlasBarButtonThinTooltip(self, button, localeKey):
		if not button:
			return
		if not _AtlasInterfaceTip(localeKey):
			return
		self.__EnsureAtlasBarButtonTooltip()
		try:
			if getattr(app, "ENABLE_MONSTER_CARD", 0):
				button.SetAlwaysToolTip(True)
		except Exception:
			pass
		try:
			button.SetShowToolTipEvent(ui.__mem_func__(self.__OnAtlasBarButtonTooltipOverIn), button, localeKey)
			button.SetHideToolTipEvent(ui.__mem_func__(self.__OnAtlasBarButtonTooltipOverOut))
		except Exception:
			pass

	def __ClearThinToolTipLines(self, tip):
		if not tip:
			return
		for child in tip.childrenList:
			try:
				child.Hide()
			except Exception:
				pass
		tip.ClearToolTip()

	def __PositionAtlasBarButtonTooltip(self, tip):
		# Reference style: show a couple of text lines under mouse (not under the button).
		try:
			mx, my = wndMgr.GetMousePosition()
		except Exception:
			return

		try:
			# ToolTip.OnUpdate places top at (yPos - height). To show below cursor,
			# pass yPos as (cursorY + offset + height).
			offsetY = 34
			height = getattr(tip, "toolTipHeight", tip.GetHeight())
			if height <= 0:
				height = 24
			tip.SetFollow(True)
			tip.SetToolTipPosition(mx, my + offsetY + height)
			tip.OnUpdate()
		except Exception:
			pass

	def __OnAtlasBarButtonTooltipOverIn(self, btn, localeKey):
		if not self._atlasBarButtonTooltip:
			return
		text = _AtlasInterfaceTip(localeKey)
		if not text:
			return
		try:
			tip = self._atlasBarButtonTooltip
			self.__ClearThinToolTipLines(tip)
			probe = ui.TextLine()
			try:
				probe.SetFontName(tip.defFontName)
			except Exception:
				pass
			probe.SetText(text)
			tw, th = probe.GetTextSize()
			if tw < 1:
				tw = len(text) * 6
			boardW = max(60, tw + 20)
			tip.SetThinBoardSize(boardW, 12)
			tip.AppendTextLine(text, uiToolTip.ToolTip.FONT_COLOR, True)
			tip.ResizeToolTip()
			self.__PositionAtlasBarButtonTooltip(tip)
			tip.Show()
			tip.SetTop()
			self._atlasBarButtonTooltipVisible = True
		except Exception:
			pass

	def __OnAtlasBarButtonTooltipOverOut(self):
		if self._atlasBarButtonTooltip:
			try:
				self._atlasBarButtonTooltip.HideToolTip()
			except Exception:
				try:
					self._atlasBarButtonTooltip.Hide()
				except Exception:
					pass
		self._atlasBarButtonTooltipVisible = False

	def __AssignPatternBtnChangeImages(self, button):
		pathUp = PATTERN_BTN_CHANGE_PATH + "01.tga"
		if not app.IsExistFile(pathUp):
			return False
		try:
			button.SetUpVisual(pathUp)
			button.SetOverVisual(PATTERN_BTN_CHANGE_PATH + "02.tga")
			button.SetDownVisual(PATTERN_BTN_CHANGE_PATH + "03.tga")
			return True
		except Exception:
			return False

	def __LoadTitleBarExpandBtnImage(self, state):
		if not self.titleBarExpandBtn:
			return False

		stateMap = {
			"default": "default.tga",
			"over": "over.tga",
			"down": "down.tga",
		}
		fileName = stateMap.get(state, "default.tga")
		path = PATTERN_BTN_SHOW_PATH + fileName
		if not app.IsExistFile(path):
			return False

		try:
			self.titleBarExpandBtn.LoadImage(path)
			self.__ApplyTitleBarExpandButtonFlip(self._npcSidebarVisible)
			return True
		except Exception:
			return False

	def __ApplyTitleBarExpandButtonFlip(self, is_expanded):
		if not self.titleBarExpandBtn:
			return
		try:
			if is_expanded:
				self.titleBarExpandBtn.SetRotation(180.0)
			else:
				self.titleBarExpandBtn.SetRotation(0.0)
		except Exception:
			pass

	def __EnsureTitleBarExpandBtnTooltip(self, text):
		btn = self.titleBarExpandBtn
		if not btn:
			return

		self._titleBarExpandBtnTipText = text or ""
		if not self._titleBarExpandBtnTipText:
			if self._titleBarExpandBtnTip:
				self._titleBarExpandBtnTip.Hide()
			return

		if self._titleBarExpandBtnTip is None:
			tip = ui.TextLine()
			tip.SetParent(btn)
			tip.SetOutline()
			tip.SetHorizontalAlignCenter()
			tip.Hide()
			self._titleBarExpandBtnTip = tip

		self._titleBarExpandBtnTip.SetText(self._titleBarExpandBtnTipText)
		bw = btn.GetWidth()
		if bw <= 0:
			bw = 16
		self._titleBarExpandBtnTip.SetPosition(bw // 2, -19)

	def __OnTitleBarExpandBtnOverIn(self):
		self.__LoadTitleBarExpandBtnImage("over")
		if self._titleBarExpandBtnTip and self._titleBarExpandBtnTipText:
			self._titleBarExpandBtnTip.Show()

	def __OnTitleBarExpandBtnOverOut(self):
		self.__LoadTitleBarExpandBtnImage("default")
		if self._titleBarExpandBtnTip:
			self._titleBarExpandBtnTip.Hide()

	def __AssignButtonImages(self, button, namePrefixes):
		for prefix in namePrefixes:
			defaultPath = prefix + "default.sub"
			if not app.IsExistFile(defaultPath):
				continue
			try:
				button.SetUpVisual(defaultPath)
				button.SetOverVisual(prefix + "over.sub")
				button.SetDownVisual(prefix + "down.sub")
				return True
			except Exception:
				pass
		return False

	def __EnsureTitleBarButtons(self):
		if not self.boardOuter or not getattr(self.boardOuter, "titleBar", None):
			return

		if self.titleBarSwitchSmallBtn is None:
			btnSwitch = ui.Button()
			if self.__AssignPatternBtnChangeImages(btnSwitch):
				btnSwitch.SetEvent(ui.__mem_func__(self.OnClickSwitchToSmallAtlas))
				tipSwitch = _AtlasInterfaceTip("NPC_HELPER_ATLAS_SWITCH_TO_SMALL_BUTTON_TOOLTIP")
				if tipSwitch:
					btnSwitch.SetToolTipText(tipSwitch)
				self.titleBarSwitchSmallBtn = btnSwitch

		if self.titleBarExpandBtn is None:
			btnExpand = ui.ExpandedImageBox()
			btnExpand.SetEvent(ui.__mem_func__(self.__ToggleNPCInfoWindow), "mouse_click")
			btnExpand.SetEvent(ui.__mem_func__(self.__OnTitleBarExpandBtnOverIn), "mouse_over_in")
			btnExpand.SetEvent(ui.__mem_func__(self.__OnTitleBarExpandBtnOverOut), "mouse_over_out")
			self.titleBarExpandBtn = btnExpand

		self.__SetTitleBarExpandButtonVisual(self._npcSidebarVisible)
		self.__LayoutTitleBarButtons()

	def __LayoutTitleBarButtons(self):
		if not self.boardOuter or not getattr(self.boardOuter, "titleBar", None):
			return

		titleBar = self.boardOuter.titleBar
		tw = titleBar.GetWidth()
		if tw < 64:
			tw = max(64, int(self.boardOuter.GetWidth()) - 15)

		cw = titleBar.btnClose.GetWidth()
		if cw <= 0:
			cw = 16

		gap = 4
		barX = 8
		barY = 7
		yBtn = barY + 0

		titleBar.btnClose.SetPosition(tw - cw - 3, 3)
		try:
			titleBar.btnClose.SetTop()
		except Exception:
			pass

		xRight = barX + tw - cw - 3

		if self.titleBarExpandBtn:
			self.titleBarExpandBtn.SetParent(self.boardOuter)
			bw = self.titleBarExpandBtn.GetWidth()
			if bw <= 0:
				bw = 16
			xRight -= gap + bw
			self.titleBarExpandBtn.SetPosition(xRight - 1, yBtn)	# Karakter bulucu butonu sola cektim. 1 pixel sola cektik.
			self.titleBarExpandBtn.Show()
			try:
				self.titleBarExpandBtn.SetTop()
			except Exception:
				pass

		if self.titleBarSwitchSmallBtn:
			self.titleBarSwitchSmallBtn.SetParent(self.boardOuter)
			bw = self.titleBarSwitchSmallBtn.GetWidth()
			if bw <= 0:
				bw = 16
			xRight -= gap + bw
			self.titleBarSwitchSmallBtn.SetPosition(xRight + 2, yBtn)	# Degistirme butonu saga cektim. 1 pixel saga cektik.
			self.titleBarSwitchSmallBtn.Show()
			try:
				self.titleBarSwitchSmallBtn.SetTop()
			except Exception:
				pass

	def __RaiseTitleBarButtons(self):
		self.__EnsureTitleBarButtons()
		self.__LayoutTitleBarButtons()

	def __SetTitleBarExpandButtonVisual(self, is_expanded):
		if not self.titleBarExpandBtn:
			return

		if not self.__LoadTitleBarExpandBtnImage("default"):
			return

		self.__ApplyTitleBarExpandButtonFlip(is_expanded)

		if is_expanded:
			tip = _AtlasInterfaceTip("NPC_HELPER_ATLAS_SHRINK_BUTTON_TOOLTIP")
		else:
			tip = _AtlasInterfaceTip("NPC_HELPER_ATLAS_EXPAND_BUTTON_TOOLTIP")

		self.__EnsureTitleBarExpandBtnTooltip(tip)

	def __ToggleNPCInfoWindow(self):
		if self._npcSidebarVisible:
			self._npcSidebarVisible = False
			self._HideNpcSidebar()
		else:
			self._npcSidebarVisible = True
			self.OpenNPCInfoWindow()

		self.__SetTitleBarExpandButtonVisual(self._npcSidebarVisible)
		self.__LayoutTitleBarButtons()

	def OnClickSwitchToSmallAtlas(self):
		if self.miniMapOwner:
			self.miniMapOwner.SetAtlasWindow(miniMap.ATLAS_TYPE_SMALL)
		else:
			self.CannotChangeToSmallAtlasMessage()

	def Destroy(self):

		try:

			miniMap.UnregisterAtlasWindow()

		except Exception:

			pass

		try:

			if self.rxAtlas:

				self.rxAtlas.HideAtlas()

		except Exception:

			pass

		try:

			tooltipInfo = getattr(self, "tooltipInfo", None)
			if tooltipInfo:
				tooltipInfo.Hide()

		except Exception:

			pass

		try:

			self.ClearDictionary()

		except Exception:

			pass

		self.AtlasMainWindow = None

		self.titleBarSwitchSmallBtn = None
		self.titleBarExpandBtn = None
		self._titleBarExpandBtnTip = None
		self._titleBarExpandBtnTipText = ""

		self._atlasBarButtonTooltip = None
		self._atlasBarButtonTooltipVisible = False

		self._atlasMarkTooltip = None
		self._atlasMarkTooltipVisible = False

		self.miniMapOwner = None

		self.__ReleaseWheelTopWindow()

	def BindInterface(self, ifaceOuter):

		self.faceIfOuter = ifaceOuter

	def SetItemToolTip(self, tooltipObjOuter):

		self.tooltipItemRefExt = tooltipObjOuter

		try:

			if self._npcdlg:

				self._npcdlg.SetItemToolTip(tooltipObjOuter)

		except Exception:

			pass

		try:

			if self._mobdlg:

				self._mobdlg.SetItemToolTip(tooltipObjOuter)

		except Exception:

			pass

	def OpenNPCInfoWindow(self):

		if self._npcdlg is None:

			self._npcdlg = NPCInfoWindow()

			try:

				self._npcdlg.LoadWindow()

			except Exception:

				self._npcdlg = None

				return

			self._npcdlg.SetAtlasPickCb(ui.__mem_func__(self.OnNPCRowFromSidebar))

			self._npcdlg.SetMapPickCb(ui.__mem_func__(self.OnMapRowFromSidebar))

			self._npcdlg.SetMobRefreshCb(ui.__mem_func__(self.OnMobGuideMapChanged))

			self._npcdlg.SetCloseEvent(ui.__mem_func__(self._HideNpcSidebar))

			self._npcdlg.SetAtlasModalBlockCb(ui.__mem_func__(self.__SetAtlasModalBlocked))

			if self.tooltipItemRefExt:

				self._npcdlg.SetItemToolTip(self.tooltipItemRefExt)

			try:
				if self.rawMapKey:
					self._npcdlg.SetPreferredMapSlug(self.rawMapKey)
				elif self.miniMapOwner and getattr(self.miniMapOwner, "mapName", ""):
					self._npcdlg.SetPreferredMapSlug(self.miniMapOwner.mapName)
			except Exception:
				pass

		self._npcdlg.RefreshNPCTeleportButton()

		self._npcSidebarVisible = True
		self.__SetTitleBarExpandButtonVisual(True)

		try:

			ax, ay = self.GetGlobalPosition()

			aw = self.GetWidth()

			self._npcdlg.SetPosition(int(ax) + int(aw) + HELPER_LAYOUT_GAP, int(ay))

		except Exception:

			pass

		self._npcdlg.Show()

		self.__ClaimWheelTopWindow()

		try:

			self._npcdlg.SetTop()

		except Exception:

			pass

	def _HideNpcSidebar(self):

		self._npcSidebarVisible = False

		try:

			if self._npcdlg:

				self._npcdlg.Hide()

		except Exception:

			pass

		self.__SetTitleBarExpandButtonVisual(False)

	def __PositionMobInfoWindow(self):
		if not self._mobdlg:
			return
		try:
			ax, ay = self.GetGlobalPosition()
			aw = self.GetWidth()
		except Exception:
			return

		try:
			mw = self._mobdlg.GetWidth()
			mh = self._mobdlg.GetHeight()
			if mw <= 0:
				mw = 210
			if mh <= 0:
				mh = 430
		except Exception:
			mw = 210
			mh = 430

		gap = HELPER_LAYOUT_GAP

		# Prefer right side. If it doesn't fit, fall back to left.
		px = int(ax) + int(aw) + int(gap)
		py = int(ay)

		try:
			sw = wndMgr.GetScreenWidth()
			sh = wndMgr.GetScreenHeight()
			if px + int(mw) > sw:
				px = int(ax) - int(mw) - int(gap)
			if px < 0:
				px = 0
			if px + int(mw) > sw:
				px = max(0, sw - int(mw))
			if py + int(mh) > sh:
				py = max(0, sh - int(mh))
		except Exception:
			pass

		try:
			self._mobdlg.SetPosition(int(px), int(py))
		except Exception:
			pass

	def __GetSidebarMapObj(self):

		try:

			if self._npcdlg and self._npcdlg.mapObj:

				return self._npcdlg.mapObj

		except Exception:

			pass

		return None

	def OnMobGuideMapChanged(self, mx):

		if not self._mobdlg:

			return

		try:

			self._mobdlg.SetMapFromInfo(mx)

		except Exception:

			pass

	def OpenMobInfoWindow(self):

		if self._mobdlg is None:

			self._mobdlg = MobInfoWindow()

			self._mobdlg.LoadWindow()

			if self.tooltipItemRefExt:

				self._mobdlg.SetItemToolTip(self.tooltipItemRefExt)

		mx = self.__GetSidebarMapObj()

		try:

			self._mobdlg.SetMapFromInfo(mx)

		except Exception:

			pass

		self.__PositionMobInfoWindow()
		self._mobdlg.Show()

		self.__ClaimWheelTopWindow()

		try:

			self._mobdlg.RefreshMobGuide()

		except Exception:

			pass

		try:

			self._mobdlg.SetTop()

		except Exception:

			pass

	def ToggleMobInfoWindow(self):
		try:
			if self._mobdlg and self._mobdlg.IsShow():
				self._mobdlg.Hide()
				return
		except Exception:
			pass
		self.OpenMobInfoWindow()

	def OnMapRowFromSidebar(self, mx):

		if not mx:

			return

		mapDir = mx.get("map_dir", "")

		if not mapDir:

			return

		try:

			if hasattr(miniMap, "SetAtlasNpcHelperView") and not miniMap.IsAtlasNpcHelperView():

				miniMap.SetAtlasNpcHelperView(1)

		except Exception:

			pass

		try:

			if hasattr(miniMap, "LoadAtlasForMapName"):

				miniMap.LoadAtlasForMapName(mapDir)

		except Exception:

			pass

		try:

			miniMap.UnselectNPC()

		except Exception:

			pass

		self._atlFitDone = False

		self.SetMapName(mapDir)

		try:

			if self._mobdlg and self._mobdlg.IsShow():

				self._mobdlg.SetMapFromInfo(mx)

		except Exception:

			pass

	def OnNPCRowFromSidebar(self, dataDict):

		if not dataDict:

			try:

				miniMap.UnselectNPC()

			except Exception:

				pass

			return

		try:

			_SelectNPC(
				int(dataDict["map_index"]),
				int(dataDict["vnum"]),
				int(dataDict["x"]) * 100,
				int(dataDict["y"]) * 100,
			)

		except Exception:

			pass

		try:

			if hasattr(miniMap, "CenterAtlasOnMapPos"):

				miniMap.CenterAtlasOnMapPos(
					float(int(dataDict["x"]) * 100),
					float(int(dataDict["y"]) * 100),
				)

				self._SyncAtlasRenderPosTrack()

		except Exception:

			pass

		try:

			self.cbNpcSelExt(dataDict)

		except Exception:

			pass

	def OnNPCSelected(self, *argsOuter):

		try:

			if argsOuter:

				self.OnNPCRowFromSidebar(argsOuter[0])

		except Exception:

			pass

	def ToggleGuildLand(self):

		try:

			npcLocationHelper.RequestGuildLand(int(_CurMapIndex()))

		except Exception:

			pass

	def OnAtlasScaleGrow(self):

		self.__AtlasScaleUp()

	def OnAtlasScaleShrink(self):

		self.__AtlasScaleDown()

	def __AtlasScaleUp(self):

		try:

			miniMap.AtlasScaleUp()

			self._SyncAtlasRenderPosTrack()

		except Exception:

			pass

	def __AtlasScaleDown(self):

		try:

			miniMap.AtlasScaleDown()

			self._SyncAtlasRenderPosTrack()

		except Exception:

			pass

	def _GetAtlasPanLimits(self):

		if hasattr(miniMap, "GetAtlasPanExtents"):

			return miniMap.GetAtlasPanExtents()

		maxXpane, maxYpane = miniMap.GetAtlasMaxPos()

		return 0.0, float(maxXpane), 0.0, float(maxYpane)

	def _AtlasDragPixels(self, ddXflt, ddYflt):

		try:

			minXpane, maxXpane, minYpane, maxYpane = self._GetAtlasPanLimits()

			nextXflt = float(self._atlRxTrack) + float(ddXflt)

			nextYflt = float(self._atlRyTrack) + float(ddYflt)

			if nextXflt < float(minXpane):

				nextXflt = float(minXpane)

			if nextYflt < float(minYpane):

				nextYflt = float(minYpane)

			if nextXflt > float(maxXpane):

				nextXflt = float(maxXpane)

			if nextYflt > float(maxYpane):

				nextYflt = float(maxYpane)

			atlasX, atlasY = self.__GetAtlasRenderPos(nextXflt, nextYflt)

			self.__SetAtlasRenderPosWithinMinMax(atlasX, atlasY)

		except Exception:

			pass

	def RecenterMyPos(self):

		self.__AtlasMyPosition()

	def Show(self):

		try:
			NPCLocationHelperUtil.BindAtlasWindow(self)
		except Exception:
			pass

		if not self.boardOuter:

			import dbg

			dbg.TraceError("NPCLocationHelper_Atlas.Show: boardOuter is None")

			return

		self.LayoutHelperWindows()
		self.__RaiseTitleBarButtons()

		try:

			if self._npcSidebarVisible:

				self.OpenNPCInfoWindow()

			else:

				self.__SetTitleBarExpandButtonVisual(False)

		except Exception:

			pass

		try:

			if hasattr(miniMap, "SetAtlasNpcHelperView"):

				miniMap.SetAtlasNpcHelperView(1)

			if hasattr(miniMap, "ChangeAtlasRenderPos"):

				miniMap.ChangeAtlasRenderPos(0.0, 0.0)

				self._atlRxTrack = 0.0

				self._atlRyTrack = 0.0

		except Exception:

			pass

		self._atlFitDone = False

		try:

			if self.rxAtlas:

				self.rxAtlas.ShowAtlas()

				self.rxAtlas.Show()

		except Exception:

			pass

		self.IsShowWindowValue = True

		ui.ScriptWindow.Show(self)

		self.__ClaimWheelTopWindow()

		self.__RaiseAtlasChrome()

		try:

			if self.shellAtlas:

				self.shellAtlas.Show()

				self.shellAtlas.SetTop()

		except Exception:

			pass

		try:

			if self.rxAtlas:

				self.rxAtlas.Show()

				self.rxAtlas.SetTop()

		except Exception:

			pass

		self._SyncRefAtlasViewport()

		self._FitAtlasScaleToBoard()

		self._TryDeferredAtlasFit()

		try:

			if self.rawMapKey:

				self.SetMapName(self.rawMapKey)

			elif self.miniMapOwner and getattr(self.miniMapOwner, "mapName", ""):

				self.SetMapName(self.miniMapOwner.mapName)

		except Exception:

			pass

		# Reference: sidebar opens only via the titlebar button (user action).

		try:

			npcLocationHelper.RequestStatus()

		except Exception:

			pass

	def Hide(self):

		try:

			if self._npcdlg and self._npcdlg.IsShow():

				self._npcdlg.Hide()

		except Exception:

			pass

		try:

			if self._mobdlg:

				self._mobdlg.Hide()

		except Exception:

			pass

		try:

			if self.rxAtlas:

				self.rxAtlas.HideAtlas()

				self.rxAtlas.Hide()

		except Exception:

			pass

		self.__HideAtlasMarkTooltip()

		self.__ReleaseWheelTopWindow()

		ui.ScriptWindow.Hide(self)

		self.IsShowWindowValue = False

	def Close(self):

		self.IsShowWindowValue = False

		self.__ReleaseWheelTopWindow()

		self.Hide()

	def OnMoveWindow(self, x, y):
		self.lastBoardPos = [x, y]

	def SetMapName(self, mapSlugText):

		self.rawMapKey = mapSlugText

		showTitle = ""

		try:

			showTitle = localeInfo.MINIMAP_ZONE_NAME_DICT.get(mapSlugText, mapSlugText)

			# Title bar: reference large atlas uses NPC_HELPER_ATLAS_TITLE, not zone name.
			atlasBoardTitle = getattr(localeInfo, "NPC_HELPER_ATLAS_TITLE", None)
			if not atlasBoardTitle:
				atlasBoardTitle = getattr(uiScriptLocale, "NPC_HELPER_ATLAS_TITLE", "")
			self.boardOuter.SetTitleName(atlasBoardTitle)

		except Exception:

			pass

		self.curMapRow = None

		try:

			for rowScan in NPCLocationHelperUtil.GetMapInfos():

				if rowScan.get("map_dir") == mapSlugText or rowScan.get("map_name") == mapSlugText:

					self.curMapRow = rowScan

					break

			if self.curMapRow:

				showTitle = NPCLocationHelperUtil.GetMapNameLoca(self.curMapRow)

			subLine = ""

			if self.curMapRow:

				subLine = NPCLocationHelperUtil.GetMapRecommendedLevelText(self.curMapRow)

			try:

				tabTxt = self.GetChild("tab_menu_1_atlas_text")

				if subLine:

					mergeCap = "%s(%s)" % (showTitle, subLine)

				else:

					mergeCap = showTitle

				tabTxt.SetText(mergeCap)

			except Exception:

				pass

			if self.curMapRow:

				showAtlasMode = int(self.curMapRow.get("show_atlas", 1))

				if self.IsShowWindowValue:

					if showAtlasMode == 0:

						self.OnShowDontShowMap(mapSlugText)

					elif showAtlasMode == 2:

						self.OnShowUnlockedMap(mapSlugText)

					else:

						self.OnShowMap(mapSlugText)

		except Exception:

			pass

		try:

			px, py = self.GetGlobalPosition()

			self.lastBoardPos[0] = int(px)

			self.lastBoardPos[1] = int(py)

		except Exception:

			pass

	def IsShowWindow(self):

		return self.IsShowWindowValue

	def OnPressEscapeKey(self):

		self.Close()

		return True

	def RefreshHelperStatus(self):

		try:

			if self._npcdlg:

				self._npcdlg.RefreshNPCTeleportButton()

		except Exception:

			pass

		try:

			if self._npcdlg and self._npcdlg.mapObj:

				self._npcdlg.SetMapInfo(self._npcdlg.mapObj)

		except Exception:

			pass

	def OnHelperWarpResult(self, resultIdx):

		try:

			if self._npcdlg:

				self._npcdlg.RefreshNPCTeleportButton()

		except Exception:

			pass

		msg = NPCLocationHelperUtil.GetCanWarpToNPCStateText(resultIdx)

		if not msg:

			try:

				resOk = npcLocationHelper.RESULT_OK

				if int(resultIdx) == int(resOk):

					return

			except Exception:

				pass

			try:

				msg = getattr(localeInfo, "NPC_LOCATION_HELPER_MESSAGE_CANNOT_WARP_TO_NPC_NOW", "")

			except Exception:

				msg = ""

		if msg:

			NPCLocationHelperUtil.AppendChat(msg)

	def RefreshHelperGuildLand(self, mapIndex, resultIdx):

		try:

			resOk = npcLocationHelper.RESULT_OK

			if int(resultIdx) != int(resOk):

				msg = LcTry("NPC_LOCATION_HELPER_MESSAGE_GUILD_LAND_UPDATE_COOLTIME", "")

				if msg:

					NPCLocationHelperUtil.AppendChat(msg)

				return

		except Exception:

			pass

		try:

			miniMap.UpdateAtlas()

		except Exception:

			pass

	def OnShowMap(self, slugText):

		self.SetAtlasText("", "")

		try:

			if self.rxAtlas:

				self.rxAtlas.ShowAtlas()

		except Exception:

			pass

		self._atlFitDone = False

		self._SyncRefAtlasViewport()

		self._FitAtlasScaleToBoard()

		self._TryDeferredAtlasFit()

	def OnShowUnlockedMap(self, slugTextTry):

		try:

			l1Try = LcTry("NPC_LOCATION_HELPER_ATLAS_UNLOCKED_MAP_1", "")

			l2Fmt = LcTry("NPC_LOCATION_HELPER_ATLAS_UNLOCKED_MAP_2", "%s")

			capNam = NPCLocationHelperUtil.GetMapNameLoca(slugTextTry) # MT2009: without regard to case

			self.SetAtlasText(l1Try, l2Fmt % capNam)

		except Exception:

			pass

	def OnShowDontShowMap(self, slugUnusedTry):

		try:

			tNo = LcTry("NPC_LOCATION_HELPER_ATLAS_DONT_SHOW_MAP", "")

			self.SetAtlasText("", tNo)

		except Exception:

			pass

	def SetAtlasText(self, lineOne, lineTwo):

		try:

			if self.txAtlas1Win:

				self.txAtlas1Win.SetText(lineOne)

			if self.txAtlas2Win:

				self.txAtlas2Win.SetText(lineTwo)

		except Exception:

			pass

	def CannotWarpToNPCNowMessage(self):

		try:

			msg = getattr(localeInfo, "NPC_LOCATION_HELPER_MESSAGE_CANNOT_WARP_TO_NPC_NOW", "")

			if msg:

				NPCLocationHelperUtil.AppendChat(msg)

		except Exception:

			pass

	def CannotToggleAtlasTypeMessage(self):

		try:

			msg = getattr(localeInfo, "NPC_LOCATION_HELPER_MESSAGE_CANNOT_TOGGLE_ATLAS_DISABLED", "")

			if msg:

				NPCLocationHelperUtil.AppendChat(msg)

		except Exception:

			pass

	def CannotChangeToSmallAtlasMessage(self):

		try:

			msg = getattr(localeInfo, "NPC_LOCATION_HELPER_MESSAGE_CANNOT_TOGGLE_TO_SMALL_ATLAS", "")

			if msg:

				NPCLocationHelperUtil.AppendChat(msg)

		except Exception:

			pass

	def __IsMouseOverAtlasMap(self):
		for w in (self.rxAtlas, self.shellAtlas):
			if not w:
				continue
			try:
				gx, gy = w.GetGlobalPosition()
				mw = w.GetWidth()
				mh = w.GetHeight()
				if mw <= 0 or mh <= 0:
					continue
				mx, my = wndMgr.GetMousePosition()
				if (gx <= mx < gx + mw) and (gy <= my < gy + mh):
					return True
			except Exception:
				pass
		return False

	def __EnsureAtlasMarkTooltip(self):
		if getattr(self, "_atlasMarkTooltip", None) is not None:
			return
		try:
			self._atlasMarkTooltip = uiToolTip.ToolTip()
			self._atlasMarkTooltip.Hide()
		except Exception:
			self._atlasMarkTooltip = None

	def __HideAtlasMarkTooltip(self):
		self._atlasMarkTooltipVisible = False
		tooltipInfo = getattr(self, "tooltipInfo", None)
		if tooltipInfo:
			try:
				tooltipInfo.SetText("")
				tooltipInfo.Hide()
			except Exception:
				pass
		infoGuildMark = getattr(self, "infoGuildMark", None)
		if infoGuildMark:
			try:
				infoGuildMark.Hide()
			except Exception:
				pass

	def __FormatAtlasMarkCaption(self, sName, iPosX, iPosY):
		if sName == "empty_guild_area":
			sName = localeInfo.GUILD_EMPTY_AREA

		if getattr(app, "WJ_SHOW_PARTY_ON_MINIMAP", 0):
			splitsName = sName.split("|")
			isQuest = (len(splitsName) == 2)
			if localeInfo.IsARABIC() and len(sName) > 0 and sName[-1].isalnum():
				if isQuest and len(splitsName[0]) == 0:
					return "(%s)%d, %d" % (uiScriptLocale.GUILD_BUILDING_POSITION, iPosX, iPosY)
				return "(%s)%d, %d" % (splitsName[0], iPosX, iPosY)
			if isQuest and len(splitsName[0]) == 0:
				return "%s(%d, %d)" % (uiScriptLocale.GUILD_BUILDING_POSITION, iPosX, iPosY)
			return "%s(%d, %d)" % (splitsName[0], iPosX, iPosY)

		if localeInfo.IsARABIC() and len(sName) > 0 and sName[-1].isalnum():
			return "(%s)%d, %d" % (sName, iPosX, iPosY)
		return "%s(%d, %d)" % (sName, iPosX, iPosY)

	def __PrepareAtlasPickContext(self):
		if not self.rxAtlas:
			return False
		try:
			pgX, pgY = self.rxAtlas.GetGlobalPosition()
			if hasattr(miniMap, "SetAtlasNpcHelperView"):
				miniMap.SetAtlasNpcHelperView(1)
			if hasattr(miniMap, "SetAtlasScreenOrigin"):
				miniMap.SetAtlasScreenOrigin(float(pgX), float(pgY))
			return True
		except Exception:
			return False

	def __PickHelperAtlasMarkAtMouse(self, mouseX, mouseY):
		if not self.__PrepareAtlasPickContext():
			return (False, "", 0, 0, 0, 0)

		try:
			bFind, sName, iPosX, iPosY, dwTextColor, dwGuildID = miniMap.GetAtlasInfo(mouseX, mouseY)
			if bFind and sName:
				return (bFind, sName, iPosX, iPosY, dwTextColor, dwGuildID)
		except Exception:
			pass

		return (False, "", 0, 0, 0, 0)

	def __UpdateAtlasMarkHoverTooltip(self):
		if not self.boardOuter:
			return

		self._atlasMarkTooltipVisible = False
		infoGuildMark = getattr(self, "infoGuildMark", None)
		if infoGuildMark:
			try:
				infoGuildMark.Hide()
			except Exception:
				pass
		tooltipInfo = getattr(self, "tooltipInfo", None)
		if tooltipInfo:
			try:
				tooltipInfo.SetText("")
				tooltipInfo.Hide()
			except Exception:
				pass

		mouseX, mouseY = wndMgr.GetMousePosition()

		if not self.__IsMouseOverAtlasMap():
			return

		bFind, sName, iPosX, iPosY, dwTextColor, dwGuildID = self.__PickHelperAtlasMarkAtMouse(mouseX, mouseY)

		if not bFind or not sName or not tooltipInfo:
			return

		caption = self.__FormatAtlasMarkCaption(sName, iPosX, iPosY)

		try:
			tooltipInfo.SetText(caption)
			bx, by = self.boardOuter.GetGlobalPosition()
			tooltipInfo.SetTooltipPosition(mouseX - bx, mouseY - by)
			tooltipInfo.SetTextColor(dwTextColor)
			tooltipInfo.Show()
			tooltipInfo.SetTop()
			self._atlasMarkTooltipVisible = True
		except Exception:
			return

		if dwGuildID != 0 and infoGuildMark:
			try:
				textWidth, textHeight = tooltipInfo.GetTextSize()
				bx, by = self.boardOuter.GetGlobalPosition()
				infoGuildMark.SetIndex(dwGuildID)
				infoGuildMark.SetPosition(mouseX - bx - textWidth - 18 - 5, mouseY - by)
				infoGuildMark.Show()
				infoGuildMark.SetTop()
			except Exception:
				pass

	def OnUpdate(self):
		if self._atlasBarButtonTooltipVisible and self._atlasBarButtonTooltip:
			try:
				self.__PositionAtlasBarButtonTooltip(self._atlasBarButtonTooltip)
			except Exception:
				pass

		if not self.IsShowWindowValue:
			return

		if not getattr(self, "tooltipInfo", None):
			return

		try:
			self.__UpdateAtlasMarkHoverTooltip()
		except Exception:
			pass


# ---------------------------------------------------------------------------------------------------------------------
# MT2009_PLUS_NPC_LOCATION_HELPER_V1 (MT2009 Plus): the bridge between our uiminimap.MiniMap and this window - what the
# package's uiminimap.py hunks did inside its own MiniMap (the switch button on the small atlas' title bar, the
# active atlas type, which window the exe's atlas talks to). uiminimap.py keeps only a few calls into it.
# ---------------------------------------------------------------------------------------------------------------------
# MT2009_PLUS_NPC_LOCATION_HELPER_V3 (the owner, 29 October 2026): every character has the improved map, so it is the
# atlas the M key / the minimap's button / the exe open from the start; the classic one is a click away (the window's
# "Wroc do zwyklej mapy" button) and the choice is kept until the client closes. V1/V2 started on the classic atlas
# here, and with _HelperIsActive() always true nothing ever switched - the improved map never showed by itself.
_LAST_ATLAS_TYPE = [miniMap.ATLAS_TYPE_NPC_LOCATION_HELPER]
_BRIDGES = []


def _LogTrace(where):
	# MT2009_PLUS_NPC_LOCATION_HELPER_V3: a failure on the way to the improved map goes to syserr with its traceback
	# (it used to be swallowed and the classic atlas opened without a word)
	try:
		import dbg
		import traceback
		dbg.TraceError("MT2009 NPC location helper: %s\n%s" % (where, traceback.format_exc()))
	except Exception:
		pass

BTN_CHANGE_UP = "d:/ymir work/ui/pattern/btn_change_01.tga"
BTN_CHANGE_OVER = "d:/ymir work/ui/pattern/btn_change_02.tga"
BTN_CHANGE_DOWN = "d:/ymir work/ui/pattern/btn_change_03.tga"


def _HelperIsActive():
	# MT2009_PLUS_NPC_LOCATION_HELPER_V2 (the owner, 28 October 2026): every character has the improved map - no
	# Lokalizator NPC item, no wait for the server's STATUS (the server checks every teleport itself)
	return True


def _CurMapIndex():
	# the index the server's STATUS packet carries (npcLocationHelper.GetCurrentMapIndex), net.GetMapIndex when an exe
	# has it, otherwise the current map's folder in npc_location_helper.txt
	try:
		ix = int(npcLocationHelper.GetCurrentMapIndex())
		if ix > 0:
			return ix
	except Exception:
		pass
	try:
		fn = getattr(net, "GetMapIndex", None)
		if callable(fn):
			ix = int(fn())
			if ix > 0:
				return ix
	except Exception:
		pass
	try:
		mx = NPCLocationHelperUtil.FindMapInfoBySlug(str(background.GetCurrentMapName()))
		if mx:
			return int(mx.get("map_index", 0))
	except Exception:
		pass
	return 0


def _SelectNPC(mapIndex, vnum, x, y):
	# our exe takes the map's folder as a 5th argument: the arrow under the character shows only on that map
	mapDir = ""
	try:
		mx = NPCLocationHelperUtil.FindMapInfoByIndex(int(mapIndex))
		if mx:
			mapDir = str(mx.get("map_dir", ""))
	except Exception:
		mapDir = ""
	try:
		miniMap.SelectNPC(int(mapIndex), int(vnum), int(x), int(y), mapDir)
	except TypeError:
		miniMap.SelectNPC(int(mapIndex), int(vnum), int(x), int(y))


# the server's rule (CNpcLocationHelperManager::IsOpenTargetMap / ROLE_PORTAL) - change both together
_OPEN_TARGET_CATEGORIES = (1, 2)	# no Yohara from another map (the owner, 28 Oct 2026)
_OPEN_TARGET_MAPS = (104, 209, 301, 302, 303, 304, 368)
_TXT_PORTAL = "Do portalu nie mo\xbfna si\xea teleportowa\xe6 - wybierz NPC obok niego."
# MT2009_PLUS_NPC_LOCATION_HELPER_V2 (the wiki): the target map's level, the Champion level for Yohara, no NPC of
# an enemy kingdom - the server's checks (npc_location_helper.cpp), said before the question
_TXT_LEVEL = "Na t\xea map\xea mo\xbfna si\xea teleportowa\xe6 od %d poziomu."
_TXT_CHAMPION = "Na ziemie Yohary mo\xbfna si\xea teleportowa\xe6 od 1. Poziomu Czempiona."
_TXT_EMPIRE = "Nie mo\xbfesz si\xea teleportowa\xe6 do NPC wrogiego kr\xf3lestwa."
_TXT_CLOSED_MAP = "Na t\xea map\xea nie mo\xbfna si\xea teleportowa\xe6 z innej mapy - wejd\x9f tam zwyk\xb3\xb9 drog\xb9 (wej\x9ccie, bilet, op\xb3ata)."


def _WarpBlockedReason(npcData):
	try:
		if int(npcData.get("icon", 0)) == 1:
			return _TXT_PORTAL
		target = int(npcData.get("map_index", 0))
	except Exception:
		return ""
	cur = _CurMapIndex()
	if target <= 0:
		return ""
	mx = NPCLocationHelperUtil.FindMapInfoByIndex(target)
	if not mx:
		return ""
	if cur > 0 and target != cur and not (int(mx.get("category", 0)) in _OPEN_TARGET_CATEGORIES or target in _OPEN_TARGET_MAPS):
		return _TXT_CLOSED_MAP
	return _WikiBlockedReason(mx)


def _WikiBlockedReason(mx):
	# MT2009_PLUS_NPC_LOCATION_HELPER_V2: as the server - the level, the Champion level (Yohara: categories 6 / 7)
	try:
		minLevel = int(mx.get("min_level", 0))
		if minLevel > 0 and player.GetStatus(player.LEVEL) < minLevel:
			return _TXT_LEVEL % minLevel
	except Exception:
		pass
	try:
		minC = int(mx.get("min_c_level", 0))
		if int(mx.get("category", 0)) in (6, 7):
			minC = max(1, minC)
		if minC > 0 and hasattr(player, "CONQUEROR_LEVEL") and player.GetStatus(player.CONQUEROR_LEVEL) < minC:
			return _TXT_CHAMPION
	except Exception:
		pass
	try:
		empire = int(mx.get("empire", 0))
		if empire != 0 and empire != int(net.GetMainActorEmpire()):
			return _TXT_EMPIRE
	except Exception:
		pass
	return ""


def _StoneCost(targetMapIndex):
	# the server's rule (CNpcLocationHelperManager::GetStoneCost)
	try:
		cur = _CurMapIndex()
		tgt = int(targetMapIndex)
	except Exception:
		return 1
	if cur <= 0 or tgt <= 0 or cur == tgt:
		return 1
	if cur // 10 == tgt // 10:
		return 2
	return 3


class MiniMapBridge(object):

	def __init__(self, miniMapWnd):
		self.owner = miniMapWnd
		self.helperWnd = None
		self.switchBtn = None
		self.interface = None
		self.tooltipItem = None
		lastType = _LAST_ATLAS_TYPE[0]
		if lastType not in (miniMap.ATLAS_TYPE_SMALL, miniMap.ATLAS_TYPE_NPC_LOCATION_HELPER):
			lastType = miniMap.ATLAS_TYPE_NPC_LOCATION_HELPER # MT2009_PLUS_NPC_LOCATION_HELPER_V3
		self._activeAtlasType = lastType
		try:
			self.owner.AtlasWindow.npcLocBridge = self
		except Exception:
			pass
		_BRIDGES.append(self)

	# the window's owner API (NPCLocationHelper_Atlas.miniMapOwner)
	def __GetMapName(self):
		try:
			return self.owner.mapName
		except Exception:
			return ""
	mapName = property(__GetMapName)

	def Destroy(self):
		try:
			if self.helperWnd:
				self.helperWnd.Hide()
				self.helperWnd.Destroy()
		except Exception:
			pass
		self.helperWnd = None
		try:
			if self.switchBtn:
				self.switchBtn.Hide()
		except Exception:
			pass
		self.switchBtn = None
		try:
			if self.owner and self.owner.AtlasWindow:
				self.owner.AtlasWindow.npcLocBridge = None
		except Exception:
			pass
		self.owner = None
		self.interface = None
		self.tooltipItem = None
		try:
			_BRIDGES.remove(self)
		except ValueError:
			pass

	def BindInterface(self, interface):
		self.interface = interface
		try:
			self.tooltipItem = interface.tooltipItem
		except Exception:
			self.tooltipItem = None
		if self.helperWnd:
			try:
				self.helperWnd.BindInterface(interface)
				if self.tooltipItem:
					self.helperWnd.SetItemToolTip(self.tooltipItem)
			except Exception:
				pass

	def __EnsureHelperWindow(self):
		if self.helperWnd:
			return self.helperWnd
		try:
			wnd = NPCLocationHelper_Atlas()
			loaded = wnd.LoadWindow()
		except Exception:
			_LogTrace("the window did not load (exception) - the classic atlas opens instead")
			return None
		if not loaded:
			import dbg
			dbg.TraceError("MT2009 NPC location helper: the window did not load - the classic atlas opens instead")
			return None
		try:
			wnd.Hide()
		except Exception:
			pass
		wnd.SetMiniMapOwner(self)
		self.helperWnd = wnd
		try:
			if self.interface:
				wnd.BindInterface(self.interface)
			if self.tooltipItem:
				wnd.SetItemToolTip(self.tooltipItem)
		except Exception:
			pass
		return wnd

	def __SmallAtlas(self):
		try:
			return self.owner.AtlasWindow
		except Exception:
			return None

	def __IsAnyAtlasVisible(self):
		small = self.__SmallAtlas()
		try:
			if small and small.IsShow():
				return True
		except Exception:
			pass
		try:
			if self.helperWnd and self.helperWnd.IsShowWindow():
				return True
		except Exception:
			pass
		return False

	def __HideAll(self):
		small = self.__SmallAtlas()
		try:
			if small and small.IsShow():
				small.Hide()
		except Exception:
			pass
		try:
			if self.helperWnd and self.helperWnd.IsShowWindow():
				self.helperWnd.Close()
		except Exception:
			pass

	def __Register(self, target):
		try:
			miniMap.UnregisterAtlasWindow()
		except Exception:
			_LogTrace("miniMap.UnregisterAtlasWindow")
		try:
			miniMap.RegisterAtlasWindow(target)
		except Exception:
			_LogTrace("miniMap.RegisterAtlasWindow(%s)" % target.__class__.__name__)

	def __UseHelper(self):
		return self._activeAtlasType == miniMap.ATLAS_TYPE_NPC_LOCATION_HELPER and _HelperIsActive()

	def SetMapName(self, mapName):
		if self.helperWnd:
			try:
				self.helperWnd.SetMapName(mapName)
			except Exception:
				pass
		# a new map: the exe loaded the small atlas of it - the helper's view is set again when its window opens
		try:
			if self.__UseHelper() and self.helperWnd and self.helperWnd.IsShowWindow():
				miniMap.SetAtlasNpcHelperView(1)
			else:
				miniMap.SetAtlasNpcHelperView(0)
		except Exception:
			pass

	def SetAtlasWindow(self, atlasType):
		if atlasType not in (miniMap.ATLAS_TYPE_SMALL, miniMap.ATLAS_TYPE_NPC_LOCATION_HELPER):
			return
		if atlasType == miniMap.ATLAS_TYPE_NPC_LOCATION_HELPER:
			if not _HelperIsActive():
				msg = getattr(localeInfo, "NPC_LOCATION_HELPER_MESSAGE_CANNOT_TOGGLE_ATLAS_DISABLED", "")
				if msg:
					NPCLocationHelperUtil.AppendChat(msg)
				return
			if not self.__EnsureHelperWindow():
				return
		wasShown = self.__IsAnyAtlasVisible()
		small = self.__SmallAtlas()
		pos = None
		try:
			if atlasType == miniMap.ATLAS_TYPE_SMALL and self.helperWnd and self.helperWnd.IsShowWindow():
				pos = self.helperWnd.GetGlobalPosition()
			elif atlasType == miniMap.ATLAS_TYPE_NPC_LOCATION_HELPER and small and small.IsShow():
				pos = small.GetGlobalPosition()
		except Exception:
			pos = None
		self.__HideAll()
		self._activeAtlasType = atlasType
		_LAST_ATLAS_TYPE[0] = atlasType
		if atlasType == miniMap.ATLAS_TYPE_NPC_LOCATION_HELPER:
			target = self.helperWnd
			self.__Register(target)
			try:
				miniMap.SetAtlasNpcHelperView(1)
			except Exception:
				_LogTrace("miniMap.SetAtlasNpcHelperView(1)")
			if pos:
				try:
					target.SetPosition(int(pos[0]), int(pos[1]))
				except Exception:
					pass
			if self.mapName:
				try:
					target.SetMapName(self.mapName)
				except Exception:
					pass
			try:
				target.Show()
			except Exception:
				# MT2009_PLUS_NPC_LOCATION_HELPER_V3: said in syserr, and the classic atlas opens instead of nothing
				_LogTrace("the window's Show - back to the classic atlas")
				try:
					target.Hide()
				except Exception:
					pass
				self.SetAtlasWindow(miniMap.ATLAS_TYPE_SMALL)
				if small and not small.IsShow():
					small.Show()
				return
			try:
				target.SetTop()
			except Exception:
				pass
		else:
			try:
				miniMap.SetAtlasNpcHelperView(0)
				miniMap.ChangeAtlasRenderPos(0.0, 0.0)
			except Exception:
				_LogTrace("miniMap.SetAtlasNpcHelperView(0)")
			if small:
				self.__Register(small)
				if pos:
					try:
						small.SetPosition(int(pos[0]), int(pos[1]))
					except Exception:
						pass
				if wasShown:
					small.Show()

	def SwitchToNPCHelperAtlas(self):
		self.SetAtlasWindow(miniMap.ATLAS_TYPE_NPC_LOCATION_HELPER)

	# uiminimap.MiniMap.ShowAtlas / ToggleAtlasWindow: True = done here (the helper's window is the active atlas)
	def ShowAtlas(self):
		if not self.__UseHelper():
			return False
		wnd = self.__EnsureHelperWindow()
		if not wnd:
			return False
		if not wnd.IsShowWindow():
			self.SetAtlasWindow(miniMap.ATLAS_TYPE_NPC_LOCATION_HELPER)
		return True

	def ToggleAtlas(self):
		if not self.__UseHelper():
			return False
		wnd = self.__EnsureHelperWindow()
		if not wnd:
			return False
		if wnd.IsShowWindow():
			wnd.Close()
		else:
			self.SetAtlasWindow(miniMap.ATLAS_TYPE_NPC_LOCATION_HELPER)
		return True

	# the switch button on the small atlas' title bar (the package's AtlasWindow hunk)
	def __EnsureSwitchButton(self):
		if self.switchBtn:
			return self.switchBtn
		small = self.__SmallAtlas()
		board = getattr(small, "board", None) if small else None
		titleBar = getattr(board, "titleBar", None) if board else None
		if not titleBar:
			return None
		try:
			if not app.IsExistFile(BTN_CHANGE_UP):
				return None
		except Exception:
			pass
		btn = ui.Button()
		btn.SetParent(titleBar)
		try:
			btn.SetUpVisual(BTN_CHANGE_UP)
			btn.SetOverVisual(BTN_CHANGE_OVER)
			btn.SetDownVisual(BTN_CHANGE_DOWN)
		except Exception:
			return None
		tip = _UiScr("NPC_HELPER_ATLAS_SWITCH_TO_NPC_LOCATION_HELPER_BUTTON_TOOLTIP", "")
		if tip:
			try:
				btn.SetToolTipText(tip)
			except Exception:
				pass
		btn.SetEvent(ui.__mem_func__(self.SwitchToNPCHelperAtlas))
		btn.Hide()
		self.switchBtn = btn
		return btn

	def RefreshSwitchButton(self):
		small = self.__SmallAtlas()
		btn = self.__EnsureSwitchButton()
		if not btn:
			return
		try:
			if not small or not small.IsShow() or not _HelperIsActive():
				btn.Hide()
				return
			titleBar = small.board.titleBar
			closeW = 0
			try:
				closeW = titleBar.btnClose.GetWidth()
			except Exception:
				closeW = 16
			bx = titleBar.GetWidth() - closeW - btn.GetWidth() - 8
			# our atlas has its shrink / stretch button at the right of the title bar: go left of it
			scaleBtn = getattr(small, "scaleButton", None)
			if scaleBtn:
				try:
					(sx, sy) = scaleBtn.GetGlobalPosition()
					(tx, ty) = titleBar.GetGlobalPosition()
					bx = min(bx, sx - tx - btn.GetWidth() - 4)
				except Exception:
					pass
			btn.SetPosition(max(0, bx), 0)
			btn.Show()
		except Exception:
			_LogTrace("the classic atlas' switch button")
			try:
				btn.Hide()
			except Exception:
				pass

	# the server's answers (game.py -> the module functions below)
	def OnStatus(self):
		self.RefreshSwitchButton()
		if self.helperWnd:
			try:
				self.helperWnd.RefreshHelperStatus()
			except Exception:
				pass
		# switched off (another character) while the helper was the active atlas: back to the small one
		if self._activeAtlasType == miniMap.ATLAS_TYPE_NPC_LOCATION_HELPER and not _HelperIsActive():
			try:
				if self.helperWnd and self.helperWnd.IsShowWindow():
					self.SetAtlasWindow(miniMap.ATLAS_TYPE_SMALL)
				else:
					self._activeAtlasType = miniMap.ATLAS_TYPE_SMALL
					small = self.__SmallAtlas()
					if small:
						self.__Register(small)
			except Exception:
				pass

	def OnWarpResult(self, result):
		if self.helperWnd:
			try:
				self.helperWnd.OnHelperWarpResult(result)
				return
			except Exception:
				pass
		msg = NPCLocationHelperUtil.GetCanWarpToNPCStateText(result)
		if msg:
			NPCLocationHelperUtil.AppendChat(msg)

	def OnGuildLand(self, mapIndex, result):
		if self.helperWnd:
			try:
				self.helperWnd.RefreshHelperGuildLand(mapIndex, result)
			except Exception:
				pass


def _BridgeOf(interface):
	try:
		wnd = interface.wndMiniMap
		return getattr(wnd, "npcLocBridge", None) if wnd else None
	except Exception:
		return None


def OnGameOpen(interface):
	# game.py GameWindow.Open: the item tooltip and the interface for the window, the server's state
	bridge = _BridgeOf(interface)
	if bridge:
		bridge.BindInterface(interface)
	else:
		import dbg
		dbg.TraceError("MT2009 NPC location helper: the minimap has no bridge - only the classic atlas (see the errors above)")
	try:
		npcLocationHelper.RequestStatus() # CG 196 REQUEST_STATUS; the server answers GC 196 STATUS
	except Exception:
		_LogTrace("npcLocationHelper.RequestStatus")


def OnServerStatus(interface):
	bridge = _BridgeOf(interface)
	if bridge:
		bridge.OnStatus()


def OnServerWarpResult(interface, result):
	bridge = _BridgeOf(interface)
	if bridge:
		bridge.OnWarpResult(result)
	else:
		msg = NPCLocationHelperUtil.GetCanWarpToNPCStateText(result)
		if msg:
			NPCLocationHelperUtil.AppendChat(msg)


def OnServerGuildLand(interface, mapIndex, result):
	bridge = _BridgeOf(interface)
	if bridge:
		bridge.OnGuildLand(mapIndex, result)
