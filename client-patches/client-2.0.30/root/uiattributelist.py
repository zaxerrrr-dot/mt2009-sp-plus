# MT2009_PLUS_CHARDETAILS_V1 (Autor: blackdragonx61, "Character Details renewal"): the bonus window of the
# character window is the global one - a board docked on the right of the character window (it follows it, hides
# with it and comes back with it), categories under a horizontal bar, every bonus a name over a dark value box,
# its description in a tooltip, the list scrolled by the scroll bar and the wheel under a clipping mask.
# Our own: the window keeps the name and the API of the old bonus list (uiAttributeList.AttributeListWindow,
# EVENT_OPEN_ATTRIBUTE_LIST, RefreshStatus - interfacemodule.py unchanged); the "Bonusy" button of the character
# window opens and closes it (uicharacter.py sends itself with the event, so the window docks to it); the values
# are player.GetStatus(<point>) of our exe (the player module's POINT_* names, numbers for the points it has no name
# for: the element powers 178-183, Sung Ma 184-187 / 193-196, Precyzja 197); a per cent bonus shows "%";
# the package's transparent label button (details.sub) is not needed - the label is a plain window - so the
# window uses only pictures of the install (board, title bar, scroll bar, thinboardcircle, horizontalbar).
# Texts: the package's locale/pl (DETAILS_*), our lines DETAILS_MT_*; a locale_game.txt line with the same key wins.
import ui
import app
import player
import wndMgr
import localeInfo
import uiToolTip
import eventManager

EVENT_OPEN_ATTRIBUTE_LIST = "EVENT_OPEN_ATTRIBUTE_LIST" # | args: the character window (or none)
EVENT_CHARACTER_WINDOW_SHOW = "EVENT_CHARACTER_WINDOW_SHOW" # | args: the character window

# The point of the anti-magic bonus (DETAILS_77 "Antymagia"): the line is shown once the player module names it.
ANTI_MAGIC_POINT_NAME = "POINT_RESIST_MAGIC_REDUCTION"
# player.GetStatus of a point never set since the login: the exe keeps points XOR 0xe73ac1da, a zeroed slot reads as the key
NEVER_SET_POINT = -415579686

LABEL_START_X = 0 - 10
LABEL_START_Y = 39
LABEL_WIDTH = 50
LABEL_HEIGHT = 17
LABEL_GAP = LABEL_HEIGHT + 7
LABEL_NAME_POS_X = 0 - 10
LABEL_NAME_WIDTH = 155
TITLE_BAR_POS_X = 10
TITLE_BAR_WIDTH = 163
AREA_Y = 37
AREA_HEIGHT = 310
VISIBLE_HEIGHT = 350
WHEEL_PIXELS = LABEL_GAP * 4
DOCK_OFFSET_X = 253 - 3
TOOLTIP_COLOR = 0xffffff00

# the package's locale/pl/locale_game.txt (cp1250; DETAILS_22 fixed: the critical hit, not the piercing one)
# MT2009_PLUS_BONUS67_WIKI_NAMES_V1 (poprawki 3.0.10 #1): the lines of the 6th/7th bonuses carry the pl-wiki's names ("6. i 7.
# bonus", word for word, the value in its box - DETAILS_0/12/55/56, RESIST_COMBAT, BLEEDING*, LOW_RANK, FALL, SUNGMA_PER_*);
# a name wider than the label goes on more lines (Label).
PL = {
	"DETAILS_0": "Si\xb3a w walce z kamieniami Metin",
	"DETAILS_1": "Si\xb3a vs Ludziom",
	"DETAILS_10": "Si\xb3a vs Pot. Pustyni",
	"DETAILS_11": "Si\xb3a vs Insektom",
	"DETAILS_12": "Warto\x9c\xe6 Ataku",
	"DETAILS_13": "Si\xb3a Obrony",
	"DETAILS_14": "Przeci\xeatne Obra\xbfenia",
	"DETAILS_15": "Odp. na Przeci\xea.Obr.",
	"DETAILS_16": "Obra\xbf. umiej\xeatno\x9cci",
	"DETAILS_17": "Odporno\x9c\xe6 na obra\xbf. umiej.",
	"DETAILS_18": "Mag./Kr\xf3tkodyst. Atak",
	"DETAILS_19": "Magiczny Atak",
	"DETAILS_2": "Odporno\x9c\xe6 vs Ludziom",
	"DETAILS_20": "Szansa na Cios Kryt.",
	"DETAILS_21": "Przeszyw. Cios",
	"DETAILS_22": "Odp. na Cios Kryt.",
	"DETAILS_23": "Odp. na Przesz. Cios",
	"DETAILS_24": "Odp. na B\xb3yskawice",
	"DETAILS_25": "Odp. na L\xf3d",
	"DETAILS_26": "Odp. na Mrok",
	"DETAILS_27": "Odp. na Ogie\xf1",
	"DETAILS_28": "Odp. na Wiatr",
	"DETAILS_29": "Odp. na Ziemi\xea",
	"DETAILS_3": "Si\xb3a vs Orkom",
	"DETAILS_30": "Moc B\xb3yskawic",
	"DETAILS_31": "Moc Lodu",
	"DETAILS_32": "Moc Mroku",
	"DETAILS_33": "Moc Ognia",
	"DETAILS_34": "Moc Wiatru",
	"DETAILS_35": "Moc Ziemi",
	"DETAILS_36": "Si\xb3a vs Wojownikom",
	"DETAILS_37": "Si\xb3a vs Ninja",
	"DETAILS_38": "Si\xb3a vs Sura",
	"DETAILS_39": "Si\xb3a vs Szamanom",
	"DETAILS_4": "Si\xb3a vs Nieumar\xb3ym",
	"DETAILS_41": "Obrona vs Wojownikom",
	"DETAILS_42": "Obrona vs Ninja",
	"DETAILS_43": "Obrona vs Sura",
	"DETAILS_44": "Obrona vs Szamanom",
	"DETAILS_46": "Odporno\x9c\xe6 na Miecz",
	"DETAILS_47": "Odp. na Br. Dwur\xeaczn\xb9",
	"DETAILS_48": "Odporno\x9c\xe6 na Sztylet",
	"DETAILS_5": "Si\xb3a vs Potworom",
	"DETAILS_50": "Odporno\x9c\xe6 na Dzwon",
	"DETAILS_51": "Odporno\x9c\xe6 na Wachlarz",
	"DETAILS_52": "Odporno\x9c\xe6 na Strza\xb3",
	"DETAILS_53": "Szansa na Omdlenie",
	"DETAILS_54": "Szansa na Spowolnie.",
	"DETAILS_55": "Szansa na Otrucie",
	"DETAILS_56": "Odporno\x9c\xe6 na Trucizny",
	"DETAILS_59": "Kradzie\xbf \xafycia",
	"DETAILS_60": "Kradzie\xbf PE",
	"DETAILS_61": "Regeneracja P\xaf",
	"DETAILS_62": "Regeneracja PE",
	"DETAILS_63": "Blok Ataku",
	"DETAILS_64": "Unik Strza\xb3y",
	"DETAILS_65": "Odbicie Walki. Wr\xeacz",
	"DETAILS_66": "Reg. P\xaf przy Zabiciu",
	"DETAILS_67": "Reg. PE przy Zabiciu",
	"DETAILS_68": "2x PD",
	"DETAILS_69": "2x Yang",
	"DETAILS_7": "Si\xb3a vs Zwierz\xeatom",
	"DETAILS_70": "Szansa Dropu",
	"DETAILS_71": "Si\xb3a Ataku",
	"DETAILS_72": "Obrona",
	"DETAILS_73": "PD",
	"DETAILS_74": "Szansa Dropu",
	"DETAILS_75": "2x Yang",
	"DETAILS_76": "Odp. na Magi\xea",
	"DETAILS_77": "Antymagia",
	# MT2009_PLUS_BONUS67_WIKI_V1: the 6th/7th bonuses 253-255 (server-patches/bonusy67b)
	"DETAILS_MT_RESIST_COMBAT": "Je\x9cli masz powy\xbfej 90% P\xaf, doznajesz obra\xbfenia ni\xbfsze o x%.",
	"DETAILS_MT_BLEEDING": "Atak krwawienia",
	"DETAILS_MT_BLEEDING_REDUCE": "Odporno\x9c\xe6 na Atak Krwawienia",
	"DETAILS_TOOLTIP_MT_RESIST_COMBAT": "Je\x9cli masz powy\xbfej 90% P\xaf, doznajesz obra\xbfenia ni\xbfsze o podany procent.",
	"DETAILS_TOOLTIP_MT_BLEEDING": "Szansa, \xbfe zwyk\xb3y cios wywo\xb3a krwawienie: 5% P\xaf co 3 sek. (potw\xf3r wg stopnia), bez regeneracji P\xaf.",
	"DETAILS_TOOLTIP_MT_BLEEDING_REDUCE": "Zmniejsza obra\xbfenia od krwawienia o podwojon\xb9 warto\x9c\xe6 (5% = -10%).",
	"DETAILS_8": "Si\xb3a vs Mistykom",
	"DETAILS_9": "Si\xb3a vs Diab\xb3om",
	"DETAILS_CATE_1": "Obra\xbfenia/Obrona",
	"DETAILS_CATE_2": "Bonusy \xbfywio\xb3owe",
	"DETAILS_CATE_3": "Bonusy klasowe",
	"DETAILS_CATE_4": "Bonus broni",
	"DETAILS_CATE_5": "Inne bonusy",
	"DETAILS_CATE_6": "Bonusy specjalne",
	"DETAILS_HIT_PCT": "Precyzja",
	"DETAILS_TITLE": "Szczeg\xf3\xb3y",
	"DETAILS_TOOLTIP_0": "Si\xb3a w walce z kamieniami Metin: zadaje wi\xeaksze obra\xbfenia kamieniom Metin",
	"DETAILS_TOOLTIP_1": "Si\xb3a w walce z Lud\x9fmi: zadaje wi\xeacej obra\xbfe\xf1 Ludziom.",
	"DETAILS_TOOLTIP_10": "Si\xb3a w walce z potworami pustyni: zadaje wi\xeaksze obra\xbfenia potworom pustyni.",
	"DETAILS_TOOLTIP_11": "Si\xb3a w walce z insektami: zadaje wi\xeaksze obra\xbfenia insektom.",
	"DETAILS_TOOLTIP_12": "Zwi\xeaksza twoj\xb9 si\xb3\xea ataku.",
	"DETAILS_TOOLTIP_13": "Zwi\xeaksza twoj\xb9 si\xb3\xea obrony.",
	"DETAILS_TOOLTIP_14": "Zwi\xeaksza przeci\xeatne obra\xbfenia, kt\xf3re zadajesz przeciwnikom podczas ataku",
	"DETAILS_TOOLTIP_15": "Odporno\x9c\xe6 na przeci\xeatne obra\xbfenia: zmniejsza obra\xbfenia, kt\xf3re odnosisz podczas ataku.",
	"DETAILS_TOOLTIP_16": "Zwi\xeaksza obra\xbfenia zadawane przez umiej\xeatno\x9c\xe6.",
	"DETAILS_TOOLTIP_17": "Odporno\x9c\xe6 na obra\xbfenia umiej\xeatno\x9cci: zmniejsza obra\xbfenia, kt\xf3re odnosisz wskutek umiej\xeatno\x9cci.",
	"DETAILS_TOOLTIP_18": "Zwi\xeaksza zar\xf3wno fizyczn\xb9 jak i magiczn\xb9 si\xb3\xea ataku.",
	"DETAILS_TOOLTIP_19": "Zwi\xeaksza obra\xbfenia, kt\xf3re zadajesz przeciwnikom za pomoc\xb9 magicznych atak\xf3w.",
	"DETAILS_TOOLTIP_2": "Odporno\x9c\xe6 na Ludzi: zmniejsza obra\xbfenia zadawane przez Ludzi.",
	"DETAILS_TOOLTIP_20": "Zwi\xeaksza szans\xea na zadanie ciosu krytycznego.",
	"DETAILS_TOOLTIP_21": "Szansa na przeszywaj\xb9cy cios: zwi\xeaksza szans\xea na zadanie przeszywaj\xb9cego ciosu.",
	"DETAILS_TOOLTIP_22": "Odporno\x9c\xe6 na cios krytyczny: zmniejsza obra\xbfenia odnoszone wskutek ciosu krytycznego.",
	"DETAILS_TOOLTIP_23": "Odporno\x9c\xe6 na przeszywaj\xb9cy cios: zmniejsza obra\xbfenia odnoszone wskutek przeszywaj\xb9cego ciosu.",
	"DETAILS_TOOLTIP_24": "Zmniejsza obra\xbfenia zadawane przez okre\x9clone potwory.",
	"DETAILS_TOOLTIP_25": "Zmniejsza obra\xbfenia zadawane przez okre\x9clone potwory.",
	"DETAILS_TOOLTIP_26": "Odporno\x9c\xe6 na mrok: zmniejsza obra\xbfenia zadawane przez okre\x9clone potwory.",
	"DETAILS_TOOLTIP_27": "Zmniejsza obra\xbfenia zadawane przez okre\x9clone potwory.",
	"DETAILS_TOOLTIP_28": "Zmniejsza obra\xbfenia zadawane przez okre\x9clone potwory.",
	"DETAILS_TOOLTIP_29": "Zmniejsza obra\xbfenia zadawane przez okre\x9clone potwory.",
	"DETAILS_TOOLTIP_3": "Si\xb3a w walce z orkami: zadaje wi\xeaksze obra\xbfenia orkom.",
	"DETAILS_TOOLTIP_30": "Zwi\xeaksza obra\xbfenia, kt\xf3re zadajesz za pomoc\xb9 b\xb3yskawic.",
	"DETAILS_TOOLTIP_31": "Zwi\xeaksza obra\xbfenia, kt\xf3re zadajesz za pomoc\xb9 lodu.",
	"DETAILS_TOOLTIP_32": "Zwi\xeaksza obra\xbfenia, kt\xf3re zadajesz za pomoc\xb9 mroku.",
	"DETAILS_TOOLTIP_33": "Zwi\xeaksza obra\xbfenia, kt\xf3re zadajesz za pomoc\xb9 ognia.",
	"DETAILS_TOOLTIP_34": "Zwi\xeaksza obra\xbfenia, kt\xf3re zadajesz za pomoc\xb9 wiatru.",
	"DETAILS_TOOLTIP_35": "Zwi\xeaksza obra\xbfenia, kt\xf3re zadajesz za pomoc\xb9 ziemi.",
	"DETAILS_TOOLTIP_36": "Si\xb3a w walce z wojownikami: zadaje wi\xeaksze obra\xbfenia wojownikom.",
	"DETAILS_TOOLTIP_37": "Si\xb3a w walce z ninja: zadaje wi\xeaksze obra\xbfenia ninja.",
	"DETAILS_TOOLTIP_38": "Si\xb3a w walce z sura: zadaje wi\xeaksze obra\xbfenia sura.",
	"DETAILS_TOOLTIP_39": "Si\xb3a w walce z szamanami: zadaje wi\xeaksze obra\xbfenia szamanom.",
	"DETAILS_TOOLTIP_4": "Si\xb3a w walce z nieumar\xb3ymi: zadaje wi\xeaksze obra\xbfenia nieumar\xb3ym.",
	"DETAILS_TOOLTIP_41": "Odporno\x9c\xe6 na Wojownik\xf3w: zmniejsza obra\xbfenia, kt\xf3re odnosisz z r\xeaki Wojownik\xf3w.",
	"DETAILS_TOOLTIP_42": "Odporno\x9c\xe6 na Ninja: zmniejsza obra\xbfenia, kt\xf3re odnosisz z r\xeaki Ninja.",
	"DETAILS_TOOLTIP_43": "Odporno\x9c\xe6 na Sura: zmniejsza obra\xbfenia, kt\xf3re odnosisz z r\xeaki Sura.",
	"DETAILS_TOOLTIP_44": "Odporno\x9c\xe6 na Szaman\xf3w: zmniejsza obra\xbfenia, kt\xf3re odnosisz z r\xeaki Szaman\xf3w.",
	"DETAILS_TOOLTIP_46": "Zmniejsza obra\xbfenia zadawane mieczem.",
	"DETAILS_TOOLTIP_47": "Zmniejsza obra\xbfenia zadawane broni\xb9 dwur\xeaczn\xb9.",
	"DETAILS_TOOLTIP_48": "Zmniejsza obra\xbfenia zadawane sztyletem.",
	"DETAILS_TOOLTIP_5": "Si\xb3a w walce z potworami: zadaje wi\xeaksze obra\xbfenia potworom.",
	"DETAILS_TOOLTIP_50": "Zmniejsza obra\xbfenia zadawane dzwonem.",
	"DETAILS_TOOLTIP_51": "Zmniejsza obra\xbfenia zadawane wachlarzem.",
	"DETAILS_TOOLTIP_52": "Zmniejsza obra\xbfenia zadawane \xb3ukiem i strza\xb3ami.",
	"DETAILS_TOOLTIP_53": "Zwi\xeaksza szans\xea wywo\xb3ania u przeciwnika efektu omdlenia.",
	"DETAILS_TOOLTIP_54": "Zwi\xeaksza szans\xea na spowolnienie przeciwnika.",
	"DETAILS_TOOLTIP_55": "Zwi\xeaksza szans\xea na zatrucie przeciwnika.",
	"DETAILS_TOOLTIP_56": "Zmniejsza obra\xbfenia zadawane trucizn\xb9.",
	"DETAILS_TOOLTIP_59": "Przy trafieniu absorbuje P\xaf przeciwnika.",
	"DETAILS_TOOLTIP_60": "Przy trafieniu absorbuje PE przeciwnika.",
	"DETAILS_TOOLTIP_61": "Przyspiesza regeneracj\xea twoich punkt\xf3w \xbfycia.",
	"DETAILS_TOOLTIP_62": "Przyspiesza regeneracj\xea twoich punkt\xf3w energii.",
	"DETAILS_TOOLTIP_63": "Szansa na blok cios\xf3w: zwi\xeaksza szans\xea na unikni\xeacie ataku z kr\xf3tkiego dystansu.",
	"DETAILS_TOOLTIP_64": "Szansa na unikni\xeacie strza\xb3y: zwi\xeaksza szans\xea na unikni\xeacie strza\xb3y lub d\xb3ugodystansowego ataku potwora.",
	"DETAILS_TOOLTIP_65": "Szansa na odbicie ciosu: cz\xea\x9c\xe6 obra\xbfe\xf1 od ciosu jest odbijana do przeciwnika.",
	"DETAILS_TOOLTIP_66": "Regeneracja P\xaf przy zabiciu: zabicie przeciwnika podwy\xbfsza twoje punkty \xbfycia.",
	"DETAILS_TOOLTIP_67": "Regeneracja PE przy zabiciu: zabicie przeciwnika podwy\xbfsza twoje punkty energii.",
	"DETAILS_TOOLTIP_68": "Szansa na otrzymanie podw\xf3jnego do\x9cwiadczenia: zwi\xeaksza szans\xea na bonusowe PD po pokonaniu przeciwnika.",
	"DETAILS_TOOLTIP_69": "Szansa na drop podw\xf3jnej ilo\x9cci Yang: zwi\xeaksza szans\xea na otrzymanie podw\xf3jnej ilo\x9cci Yang.",
	"DETAILS_TOOLTIP_7": "Si\xb3a w walce ze zwierz\xeatami: zadaje wi\xeaksze obra\xbfenia dzikim zwierz\xeatom.",
	"DETAILS_TOOLTIP_70": "Szansa na drop przedmiot\xf3w: zwi\xeaksza szans\xea na podw\xf3jny \xb3up przedmiot\xf3w.",
	"DETAILS_TOOLTIP_71": "Zwi\xeaksza twoj\xb9 si\xb3\xea ataku.",
	"DETAILS_TOOLTIP_72": "Zwi\xeaksza twoj\xb9 si\xb3\xea obrony.",
	"DETAILS_TOOLTIP_73": "Zwi\xeaksza wzrost do\x9cwiadczenia.",
	"DETAILS_TOOLTIP_74": "Szansa na drop przedmiot\xf3w: zwi\xeaksza szans\xea na zdobycie przedmiot\xf3w.",
	"DETAILS_TOOLTIP_75": "Szansa na drop Yang: zwi\xeaksza szans\xea na zdobycie wi\xeacej Yang.",
	"DETAILS_TOOLTIP_76": "Zmniejsza obra\xbfenia odnoszone wskutek magicznych atak\xf3w.",
	"DETAILS_TOOLTIP_77": "Zmniejsza odporno\x9c\xe6 na magi\xea twojego przeciwnika.",
	"DETAILS_TOOLTIP_8": "Si\xb3a w walce z mistykami: zadaje wi\xeaksze obra\xbfenia mistykom.",
	"DETAILS_TOOLTIP_9": "Si\xb3a w walce z diab\xb3ami: zadaje wi\xeaksze obra\xbfenia diab\xb3om.",
	"DETAILS_TOOLTIP_HIT_PCT": "Zwi\xeaksza szans\xea na trafienie przeciwnika.",

	# MT2009 lines of our points the package has no line for
	"DETAILS_MT_BOSS": "Si\xb3a vs Bossom",
	"DETAILS_TOOLTIP_MT_BOSS": "Si\xb3a w walce z bossami: zadaje wi\xeaksze obra\xbfenia bossom.",
	"DETAILS_MT_REFLECT_ARROW": "Odbicie Pocisku",
	"DETAILS_TOOLTIP_MT_REFLECT_ARROW": "Szansa na odbicie pocisku: cz\xea\x9c\xe6 obra\xbfe\xf1 od strza\xb3y lub pocisku jest odbijana do przeciwnika.",
	"DETAILS_MT_MANA_BURN": "Szansa na kradzie\xbf PE",
	"DETAILS_TOOLTIP_MT_MANA_BURN": "Przy trafieniu odbiera przeciwnikowi punkty energii.",
	"DETAILS_MT_ST_REGEN": "Regeneracja ST",
	"DETAILS_TOOLTIP_MT_ST_REGEN": "Przyspiesza regeneracj\xea twojej wytrzyma\xb3o\x9cci.",
	"DETAILS_MT_SKILL_DURATION": "Czas umiej\xeatno\x9cci",
	"DETAILS_TOOLTIP_MT_SKILL_DURATION": "Wyd\xb3u\xbfa czas trwania twoich umiej\xeatno\x9cci.",
	"DETAILS_MT_CATE_SUNGMA": "Bonusy Sung Ma",
	# MT2009_PLUS_BONUS67_SKILL_V1: the 6th/7th bonuses of the wiki round 3 (server-patches/bonusy67c, 256-259) and 90
	"DETAILS_MT_CATE_B67C": "Bonusy 6/7 (dodatkowe)",
	"DETAILS_MT_LOW_RANK": "Niski ranking powoduje zwi\xeakszenie zadawanych obra\xbfe\xf1",
	"DETAILS_TOOLTIP_MT_LOW_RANK": "Niski ranking powoduje zwi\xeakszenie zadawanych obra\xbfe\xf1: Agresywny +1%, Nieuczciwy +2%, Z\xb3o\x9cliwy +3%, Okrutny +5% (bro\xf1 i he\xb3m razem: x2).",
	"DETAILS_MT_PER_HUMAN": "P\xf3\xb3-ludzie (+% \xb3\xb9cznej)",
	"DETAILS_TOOLTIP_MT_PER_HUMAN": "Silny przeciwko p\xf3\xb3-ludziom: +x% \xb3\xb9cznej warto\x9cci tego bonusu.",
	"DETAILS_MT_PER_UNDEAD": "Nieumarli (+% \xb3\xb9cznej)",
	"DETAILS_TOOLTIP_MT_PER_UNDEAD": "Silny przeciwko nieumar\xb3ym: +x% \xb3\xb9cznej warto\x9cci tego bonusu.",
	"DETAILS_MT_PER_DESERT": "Pustynia (+% \xb3\xb9cznej)",
	"DETAILS_TOOLTIP_MT_PER_DESERT": "Silny przeciwko potworom pustyni: +x% \xb3\xb9cznej warto\x9cci tego bonusu.",
	"DETAILS_MT_FALL": "Odporno\x9c\xe6 na Upadek",
	"DETAILS_TOOLTIP_MT_FALL": "Odporno\x9c\xe6 na Upadek: szansa, \xbfe cios lub umiej\xeatno\x9c\xe6 nie przewr\xf3ci ani nie odrzuci postaci.",
	"DETAILS_MT_SUNGMA_STR": "Si\xb3a Sung Ma",
	"DETAILS_MT_SUNGMA_HP": "Witalno\x9c\xe6 Sung Ma",
	"DETAILS_MT_SUNGMA_MOVE": "Odporno\x9c\xe6 Sung Ma",
	"DETAILS_MT_SUNGMA_IMMUNE": "Inteligencja Sung Ma",
	"DETAILS_MT_SUNGMA_PER_STR": "Wola SungMa (SI\xa3A)",
	"DETAILS_MT_SUNGMA_PER_HP": "Wola SungMa (WIT)",
	"DETAILS_MT_SUNGMA_PER_MOVE": "Wola SungMa (ODP)",
	"DETAILS_MT_SUNGMA_PER_IMMUNE": "Wola SungMa (INT)",
	"DETAILS_TOOLTIP_MT_SUNGMA": "Statystyka Sung Ma z przedmiot\xf3w Yohary: mapy Yohary wymagaj\xb9 jej odpowiedniej warto\x9cci.",
	"DETAILS_TOOLTIP_MT_SUNGMA_PER": "Zwi\xeaksza statystyk\xea Sung Ma o podany procent.",
}

def Text(key):
	return getattr(localeInfo, key, PL.get(key, key))

def Point(name, number):
	return getattr(player, name, number)

def AntiMagicPoint():
	return getattr(player, ANTI_MAGIC_POINT_NAME, None)

# MT2009_PLUS_BONUS67_WIKI_V1: the points 253-255 (server-patches/bonusy67b) come as point changes, but only an exe whose
# POINT_MAX_NUM is 256 keeps them (an older one drops a type >= 253) - so their lines show only with it (player.MAX_NUM).
def Bonus67bPoint(name, number):
	if getattr(player, "MAX_NUM", 0) <= number:
		return None
	return getattr(player, name, number)

# MT2009_PLUS_BONUS67_SKILL_V1: the points 256 and up (server-patches/bonusy67c) - an exe with two-byte bonus types
# (POINT_MAX_NUM 512, app.MT2009_WIDE_ATTR_EXE) keeps them; the skill lines (260-318) are in the item's tooltip only.
def Bonus67cPoint(number):
	if getattr(player, "MAX_NUM", 0) <= number:
		return None
	return number

# (title key, [(name key, tooltip key, point), ...]) - the package's order; a point None is left out
def BuildCategories():
	return [
		("DETAILS_CATE_1", [
			("DETAILS_1", "DETAILS_TOOLTIP_1", player.POINT_ATTBONUS_HUMAN),
			("DETAILS_2", "DETAILS_TOOLTIP_2", Point("POINT_RESIST_HUMAN", 160)),
			("DETAILS_3", "DETAILS_TOOLTIP_3", player.POINT_ATTBONUS_ORC),
			("DETAILS_4", "DETAILS_TOOLTIP_4", player.POINT_ATTBONUS_UNDEAD),
			("DETAILS_5", "DETAILS_TOOLTIP_5", player.POINT_ATTBONUS_MONSTER),
			("DETAILS_0", "DETAILS_TOOLTIP_0", Point("POINT_ATTBONUS_STONE", 149)),
			("DETAILS_MT_BOSS", "DETAILS_TOOLTIP_MT_BOSS", Point("POINT_ATTBONUS_BOSS", 150)),
			("DETAILS_7", "DETAILS_TOOLTIP_7", player.POINT_ATTBONUS_ANIMAL),
			("DETAILS_8", "DETAILS_TOOLTIP_8", player.POINT_ATTBONUS_MILGYO),
			("DETAILS_9", "DETAILS_TOOLTIP_9", player.POINT_ATTBONUS_DEVIL),
			("DETAILS_10", "DETAILS_TOOLTIP_10", Point("POINT_ATTBONUS_DESERT", 52)),
			("DETAILS_11", "DETAILS_TOOLTIP_11", Point("POINT_ATTBONUS_INSECT", 49)),
			("DETAILS_12", "DETAILS_TOOLTIP_12", player.POINT_ATT_GRADE_BONUS),
			("DETAILS_13", "DETAILS_TOOLTIP_13", player.POINT_DEF_GRADE_BONUS),
			("DETAILS_14", "DETAILS_TOOLTIP_14", player.POINT_NORMAL_HIT_DAMAGE_BONUS),
			("DETAILS_15", "DETAILS_TOOLTIP_15", player.POINT_NORMAL_HIT_DEFEND_BONUS),
			("DETAILS_16", "DETAILS_TOOLTIP_16", player.POINT_SKILL_DAMAGE_BONUS),
			("DETAILS_17", "DETAILS_TOOLTIP_17", player.POINT_SKILL_DEFEND_BONUS),
			("DETAILS_MT_RESIST_COMBAT", "DETAILS_TOOLTIP_MT_RESIST_COMBAT", Bonus67bPoint("POINT_RESIST_COMBAT", 253)),
			("DETAILS_18", "DETAILS_TOOLTIP_18", player.POINT_MELEE_MAGIC_ATT_BONUS_PER),
			("DETAILS_19", "DETAILS_TOOLTIP_19", player.POINT_MAGIC_ATT_BONUS_PER),
			("DETAILS_20", "DETAILS_TOOLTIP_20", player.POINT_CRITICAL_PCT),
			("DETAILS_21", "DETAILS_TOOLTIP_21", player.POINT_PENETRATE_PCT),
			("DETAILS_22", "DETAILS_TOOLTIP_22", player.POINT_RESIST_CRITICAL),
			("DETAILS_23", "DETAILS_TOOLTIP_23", player.POINT_RESIST_PENETRATE),
			("DETAILS_HIT_PCT", "DETAILS_TOOLTIP_HIT_PCT", Point("POINT_HIT_PCT", 197)),
		]),
		("DETAILS_CATE_2", [
			("DETAILS_76", "DETAILS_TOOLTIP_76", player.POINT_RESIST_MAGIC),
			("DETAILS_77", "DETAILS_TOOLTIP_77", AntiMagicPoint()),
			("DETAILS_24", "DETAILS_TOOLTIP_24", player.POINT_RESIST_ELEC),
			("DETAILS_25", "DETAILS_TOOLTIP_25", player.POINT_RESIST_ICE),
			("DETAILS_26", "DETAILS_TOOLTIP_26", player.POINT_RESIST_DARK),
			("DETAILS_27", "DETAILS_TOOLTIP_27", player.POINT_RESIST_FIRE),
			("DETAILS_28", "DETAILS_TOOLTIP_28", player.POINT_RESIST_WIND),
			("DETAILS_29", "DETAILS_TOOLTIP_29", player.POINT_RESIST_EARTH),
			# the talismans' element powers (MT2009_PLUS_ELEMENTS_V1, points 178-183)
			("DETAILS_30", "DETAILS_TOOLTIP_30", Point("POINT_ENCHANT_ELECT", 178)),
			("DETAILS_31", "DETAILS_TOOLTIP_31", Point("POINT_ENCHANT_ICE", 180)),
			("DETAILS_32", "DETAILS_TOOLTIP_32", Point("POINT_ENCHANT_DARK", 183)),
			("DETAILS_33", "DETAILS_TOOLTIP_33", Point("POINT_ENCHANT_FIRE", 179)),
			("DETAILS_34", "DETAILS_TOOLTIP_34", Point("POINT_ENCHANT_WIND", 181)),
			("DETAILS_35", "DETAILS_TOOLTIP_35", Point("POINT_ENCHANT_EARTH", 182)),
		]),
		("DETAILS_CATE_3", [
			("DETAILS_36", "DETAILS_TOOLTIP_36", player.POINT_ATTBONUS_WARRIOR),
			("DETAILS_37", "DETAILS_TOOLTIP_37", player.POINT_ATTBONUS_ASSASSIN),
			("DETAILS_38", "DETAILS_TOOLTIP_38", player.POINT_ATTBONUS_SURA),
			("DETAILS_39", "DETAILS_TOOLTIP_39", player.POINT_ATTBONUS_SHAMAN),
			("DETAILS_41", "DETAILS_TOOLTIP_41", player.POINT_RESIST_WARRIOR),
			("DETAILS_42", "DETAILS_TOOLTIP_42", player.POINT_RESIST_ASSASSIN),
			("DETAILS_43", "DETAILS_TOOLTIP_43", player.POINT_RESIST_SURA),
			("DETAILS_44", "DETAILS_TOOLTIP_44", player.POINT_RESIST_SHAMAN),
		]),
		("DETAILS_CATE_4", [
			("DETAILS_46", "DETAILS_TOOLTIP_46", player.POINT_RESIST_SWORD),
			("DETAILS_47", "DETAILS_TOOLTIP_47", player.POINT_RESIST_TWOHAND),
			("DETAILS_48", "DETAILS_TOOLTIP_48", player.POINT_RESIST_DAGGER),
			("DETAILS_50", "DETAILS_TOOLTIP_50", player.POINT_RESIST_BELL),
			("DETAILS_51", "DETAILS_TOOLTIP_51", player.POINT_RESIST_FAN),
			("DETAILS_52", "DETAILS_TOOLTIP_52", player.POINT_RESIST_BOW),
		]),
		("DETAILS_CATE_5", [
			("DETAILS_53", "DETAILS_TOOLTIP_53", player.POINT_STUN_PCT),
			("DETAILS_54", "DETAILS_TOOLTIP_54", player.POINT_SLOW_PCT),
			("DETAILS_55", "DETAILS_TOOLTIP_55", player.POINT_POISON_PCT),
			("DETAILS_56", "DETAILS_TOOLTIP_56", player.POINT_POISON_REDUCE),
			("DETAILS_MT_BLEEDING", "DETAILS_TOOLTIP_MT_BLEEDING", Bonus67bPoint("POINT_BLEEDING_PCT", 254)),
			("DETAILS_MT_BLEEDING_REDUCE", "DETAILS_TOOLTIP_MT_BLEEDING_REDUCE", Bonus67bPoint("POINT_BLEEDING_REDUCE", 255)),
			("DETAILS_59", "DETAILS_TOOLTIP_59", player.POINT_STEAL_HP),
			("DETAILS_60", "DETAILS_TOOLTIP_60", player.POINT_STEAL_SP),
			("DETAILS_MT_MANA_BURN", "DETAILS_TOOLTIP_MT_MANA_BURN", player.POINT_MANA_BURN_PCT),
			("DETAILS_61", "DETAILS_TOOLTIP_61", player.POINT_HP_REGEN),
			("DETAILS_62", "DETAILS_TOOLTIP_62", player.POINT_SP_REGEN),
			("DETAILS_MT_ST_REGEN", "DETAILS_TOOLTIP_MT_ST_REGEN", Point("POINT_ST_REGEN", 139)),
			("DETAILS_63", "DETAILS_TOOLTIP_63", player.POINT_BLOCK),
			("DETAILS_64", "DETAILS_TOOLTIP_64", player.POINT_DODGE),
			("DETAILS_65", "DETAILS_TOOLTIP_65", player.POINT_REFLECT_MELEE),
			("DETAILS_MT_REFLECT_ARROW", "DETAILS_TOOLTIP_MT_REFLECT_ARROW", player.POINT_REFLECT_ARROW),
			("DETAILS_MT_SKILL_DURATION", "DETAILS_TOOLTIP_MT_SKILL_DURATION", Point("POINT_SKILL_DURATION", 147)),
			("DETAILS_66", "DETAILS_TOOLTIP_66", player.POINT_KILL_HP_RECOVERY),
			("DETAILS_67", "DETAILS_TOOLTIP_67", player.POINT_KILL_SP_RECOVER),
			("DETAILS_68", "DETAILS_TOOLTIP_68", player.POINT_EXP_DOUBLE_BONUS),
			("DETAILS_69", "DETAILS_TOOLTIP_69", player.POINT_GOLD_DOUBLE_BONUS),
			("DETAILS_70", "DETAILS_TOOLTIP_70", player.POINT_ITEM_DROP_BONUS),
		]),
		("DETAILS_CATE_6", [
			("DETAILS_71", "DETAILS_TOOLTIP_71", player.POINT_MALL_ATTBONUS),
			("DETAILS_72", "DETAILS_TOOLTIP_72", player.POINT_MALL_DEFBONUS),
			# MT2009_PLUS_PD_BONUS_V1 (PD line): every experience bonus of the person, as the server's GiveExp adds them to
			# the rate - the potions and mounts (POINT_MALL_EXPBONUS) and the items: rings, lollipops, amulets, costume
			# sets (POINT_RAMADAN_CANDY_BONUS_EXP 127, server-patches/pdbonus). It showed only the first: PD 0% with a ring.
			("DETAILS_73", "DETAILS_TOOLTIP_73", (player.POINT_MALL_EXPBONUS, Point("POINT_RAMADAN_CANDY_BONUS_EXP", 127))),
			("DETAILS_74", "DETAILS_TOOLTIP_74", player.POINT_MALL_ITEMBONUS),
			("DETAILS_75", "DETAILS_TOOLTIP_75", player.POINT_MALL_GOLDBONUS),
		]),
		# Yohara (MT2009_PLUS_CHAMPION_V2 184-187, MT2009_PLUS_YOHARA_EXE2_V1 193-196)
		("DETAILS_MT_CATE_SUNGMA", [
			("DETAILS_MT_SUNGMA_STR", "DETAILS_TOOLTIP_MT_SUNGMA", Point("POINT_SUNGMA_STR", 184)),
			("DETAILS_MT_SUNGMA_HP", "DETAILS_TOOLTIP_MT_SUNGMA", Point("POINT_SUNGMA_HP", 185)),
			("DETAILS_MT_SUNGMA_MOVE", "DETAILS_TOOLTIP_MT_SUNGMA", Point("POINT_SUNGMA_MOVE", 186)),
			("DETAILS_MT_SUNGMA_IMMUNE", "DETAILS_TOOLTIP_MT_SUNGMA", Point("POINT_SUNGMA_IMMUNE", 187)),
			("DETAILS_MT_SUNGMA_PER_STR", "DETAILS_TOOLTIP_MT_SUNGMA_PER", Point("POINT_SUNGMA_PER_STR", 193)),
			("DETAILS_MT_SUNGMA_PER_HP", "DETAILS_TOOLTIP_MT_SUNGMA_PER", Point("POINT_SUNGMA_PER_HP", 194)),
			("DETAILS_MT_SUNGMA_PER_MOVE", "DETAILS_TOOLTIP_MT_SUNGMA_PER", Point("POINT_SUNGMA_PER_MOVE", 195)),
			("DETAILS_MT_SUNGMA_PER_IMMUNE", "DETAILS_TOOLTIP_MT_SUNGMA_PER", Point("POINT_SUNGMA_PER_IMMUNE", 196)),
		]),
		# MT2009_PLUS_BONUS67_SKILL_V1: the round 3's lines that are no skill's (256-259) and "Odpornosc na Upadek" (90)
		("DETAILS_MT_CATE_B67C", [
			("DETAILS_MT_LOW_RANK", "DETAILS_TOOLTIP_MT_LOW_RANK", Bonus67cPoint(256)),
			("DETAILS_MT_PER_HUMAN", "DETAILS_TOOLTIP_MT_PER_HUMAN", Bonus67cPoint(257)),
			("DETAILS_MT_PER_UNDEAD", "DETAILS_TOOLTIP_MT_PER_UNDEAD", Bonus67cPoint(258)),
			("DETAILS_MT_PER_DESERT", "DETAILS_TOOLTIP_MT_PER_DESERT", Bonus67cPoint(259)),
			("DETAILS_MT_FALL", "DETAILS_TOOLTIP_MT_FALL", Point("POINT_IMMUNE_FALL", 90)),
		]),
	]

# MT2009_PLUS_PD_BONUS_V1 (per cent lines): the drop and Yang bonuses are +x% (their item line reads "x1.5")
PERCENT_POINTS = (player.POINT_MALL_ITEMBONUS, player.POINT_MALL_GOLDBONUS)

def IsPercentPoint(point):
	if isinstance(point, tuple):
		point = point[0]
	if point in PERCENT_POINTS:
		return True
	try:
		import localeinfo_point
		text = localeinfo_point.GetApplyString(point, 1)
		return bool(text) and text.find("%") >= 0
	except Exception:
		return False

class Title(object):
	def __init__(self, parent, mask, text):
		bar = ui.HorizontalBar()
		bar.SetParent(parent)
		bar.Create(TITLE_BAR_WIDTH)
		bar.AddFlag("not_pick")
		bar.Show()

		name = ui.TextLine()
		name.SetParent(bar)
		name.SetPosition(0, 0)
		name.SetHorizontalAlignCenter()
		name.SetVerticalAlignCenter()
		name.SetWindowHorizontalAlignCenter()
		name.SetWindowVerticalAlignCenter()
		name.SetText(text)
		name.Show()

		bar.SetClippingMaskWindow(mask)
		name.SetClippingMaskWindow(mask)
		self.bar = bar
		self.name = name

	def Destroy(self):
		self.bar = None
		self.name = None

	def SetY(self, y, visible):
		self.bar.SetPosition(TITLE_BAR_POS_X, y)
		if visible:
			self.bar.Show()
		else:
			self.bar.Hide()

	def GetGap(self):
		return LABEL_GAP

# MT2009_PLUS_BONUS67_WIKI_NAMES_V1: the words of a name on as many lines as its width needs (the wiki's long 6th/7th
# lines); a word wider than a line stays whole on its own line.
def TextWidth(text):
	line = ui.TextLine()
	line.SetText(text)
	try:
		return int(line.GetTextSize()[0])
	except Exception:
		return len(text) * 6

def SplitName(text, width = LABEL_NAME_WIDTH - 6):
	if TextWidth(text) <= width:
		return [text]
	lines = []
	current = ""
	for word in text.split(" "):
		trial = (current + " " + word) if current else word
		if current and TextWidth(trial) > width:
			lines.append(current)
			current = word
		else:
			current = trial
	if current:
		lines.append(current)
	return lines or [text]

class Label(object):
	def __init__(self, parent, mask, text, tooltip_text, point):
		self.point = point
		self.isPercent = IsPercentPoint(point)

		# the name: a plain window the mouse goes over (the package's transparent details.sub button)
		nameWindow = ui.Window()
		nameWindow.SetParent(parent)
		nameWindow.SetSize(LABEL_NAME_WIDTH, LABEL_HEIGHT)
		nameWindow.SetWindowHorizontalAlignCenter()
		nameWindow.SetStringEvent("MOUSE_OVER_IN", ui.__mem_func__(parent.ButtonOverIn), text, tooltip_text)
		nameWindow.SetStringEvent("MOUSE_OVER_OUT", ui.__mem_func__(parent.ButtonOverOut))
		nameWindow.Show()

		# MT2009_PLUS_BONUS67_WIKI_NAMES_V1: one text line per line of the name (SplitName); the box goes down with them
		names = []
		lines = SplitName(text)
		for (row, lineText) in enumerate(lines):
			name = ui.TextLine()
			name.SetParent(nameWindow)
			name.AddFlag("not_pick")
			name.SetPosition(0, row * LABEL_HEIGHT + LABEL_HEIGHT / 2)
			name.SetHorizontalAlignCenter()
			name.SetVerticalAlignCenter()
			name.SetWindowHorizontalAlignCenter()
			name.SetText(lineText)
			name.Show()
			names.append(name)
		self.extraHeight = (len(lines) - 1) * LABEL_HEIGHT
		nameWindow.SetSize(LABEL_NAME_WIDTH, LABEL_HEIGHT + self.extraHeight)

		box = ui.ThinBoardCircle()
		box.SetParent(parent)
		box.AddFlag("not_pick")
		box.SetSize(LABEL_WIDTH, LABEL_HEIGHT)
		box.SetWindowHorizontalAlignCenter()
		box.Show()

		value = ui.TextLine()
		value.SetParent(box)
		value.AddFlag("not_pick")
		value.SetPosition(0, 0)
		value.SetHorizontalAlignCenter()
		value.SetVerticalAlignCenter()
		value.SetWindowHorizontalAlignCenter()
		value.SetWindowVerticalAlignCenter()
		value.Show()

		for wnd in [nameWindow, box, value] + names:
			wnd.SetClippingMaskWindow(mask)

		self.nameWindow = nameWindow
		self.names = names
		self.box = box
		self.value = value
		self.Refresh()

	def Destroy(self):
		self.nameWindow = None
		self.names = []
		self.box = None
		self.value = None

	def SetY(self, y, visible):
		self.nameWindow.SetPosition(LABEL_NAME_POS_X, y)
		self.box.SetPosition(LABEL_START_X, y + LABEL_GAP + self.extraHeight)
		for wnd in (self.nameWindow, self.box):
			if visible:
				wnd.Show()
			else:
				wnd.Hide()

	def GetGap(self):
		return LABEL_GAP * 2 + self.extraHeight

	def Refresh(self):
		# MT2009_PLUS_PD_BONUS_V1 (PD line): a line of several points shows their sum
		val = 0
		for point in (self.point if isinstance(self.point, tuple) else (self.point,)):
			one = player.GetStatus(point)
			# MT2009_PLUS_ANTI_RESIST_MAGIC_V1 (poprawki 3.0.8 #2): a point the server never sent (its slot still zeroed) reads
			# as the exe's XOR key 0xe73ac1da = -415579686 ("Antymagia -415579686%") - that is 0
			if one in (NEVER_SET_POINT, NEVER_SET_POINT & 0xffffffff):
				one = 0
			val += one
		if self.isPercent:
			self.value.SetText("%d%%" % val)
		else:
			self.value.SetText(str(val))

class AttributeListWindow(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.__Initialize()
		self.LoadDialog()

		eventManager.EventManager().add_observer(EVENT_OPEN_ATTRIBUTE_LIST, self.Open)
		eventManager.EventManager().add_observer(EVENT_CHARACTER_WINDOW_SHOW, self.OnCharacterWindowShow)

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __Initialize(self):
		self.objectList = []
		self.toolTip = None
		self.scrollBar = None
		self.mask = None
		self.totalGap = LABEL_START_Y
		self.characterWindow = None
		self.isWanted = False
		self.dockPos = None

	@ui.WindowDestroy
	def Destroy(self):
		eventManager.EventManager().remove_observer(EVENT_OPEN_ATTRIBUTE_LIST, self.Open)
		eventManager.EventManager().remove_observer(EVENT_CHARACTER_WINDOW_SHOW, self.OnCharacterWindowShow)
		for obj in self.objectList:
			obj.Destroy()
		if self.toolTip:
			self.toolTip.HideToolTip()
		self.ClearDictionary()
		self.__Initialize()

	def LoadDialog(self):
		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "UIScript/characterdetailswindow.py")

			self.GetChild("TitleName").SetText(Text("DETAILS_TITLE"))
			self.GetChild("TitleBar").SetCloseEvent(ui.__mem_func__(self.Close))
			self.scrollBar = self.GetChild("ScrollBar")
			self.scrollBar.SetScrollEvent(ui.__mem_func__(self.ArrangePosition))
			self.mask = self.GetChild("object_area_window")
		except:
			import exception
			exception.Abort("AttributeListWindow.LoadDialog.BindObject")

		self.toolTip = uiToolTip.ToolTip(220)
		self.toolTip.HideToolTip()

		for (titleKey, lines) in BuildCategories():
			lines = [l for l in lines if l[2] is not None]
			if not lines:
				continue
			self.objectList.append(Title(self, self.mask, Text(titleKey)))
			for (nameKey, tipKey, point) in lines:
				self.objectList.append(Label(self, self.mask, Text(nameKey), Text(tipKey), point))

		self.totalGap = LABEL_START_Y
		for obj in self.objectList:
			self.totalGap += obj.GetGap()

		self.scrollBar.SetMiddleBarSize(max(0.08, min(1.0, float(AREA_HEIGHT) / max(1, self.totalGap))))
		self.scrollBar.SetScrollStep(min(1.0, float(WHEEL_PIXELS) / max(1, self.totalGap - VISIBLE_HEIGHT)))
		self.ArrangePosition()

	def ArrangePosition(self):
		y = LABEL_START_Y - int(self.scrollBar.GetPos() * (self.totalGap - VISIBLE_HEIGHT))
		top = AREA_Y - LABEL_GAP * 2
		bottom = AREA_Y + AREA_HEIGHT
		for obj in self.objectList:
			obj.SetY(y, y + obj.GetGap() > top and y < bottom)
			y += obj.GetGap()

	def RefreshStatus(self): # binary call (interfacemodule.RefreshStatus)
		if not self.IsShow():
			return
		for obj in self.objectList:
			if isinstance(obj, Label):
				obj.Refresh()

	# the character window's "Bonusy" button (uicharacter.py sends the character window)
	def Open(self, characterWindow=None):
		if characterWindow is not None:
			self.characterWindow = characterWindow
		if self.IsShow():
			self.Close()
		else:
			self.isWanted = True
			self.__Show()

	# the character window was opened again: so is this one, when it was open
	def OnCharacterWindowShow(self, characterWindow=None):
		if characterWindow is not None:
			self.characterWindow = characterWindow
		if self.isWanted and not self.IsShow():
			self.__Show()

	def __Show(self):
		self.dockPos = None
		self.__Dock()
		self.Show()
		self.SetTop()
		self.RefreshStatus()

	def __Dock(self):
		wnd = self.characterWindow
		if not wnd:
			return
		try:
			(x, y) = wnd.GetGlobalPosition()
		except Exception:
			return
		if self.dockPos == (x, y):
			return
		self.dockPos = (x, y)
		px = x + DOCK_OFFSET_X
		if px + self.GetWidth() > wndMgr.GetScreenWidth():
			px = max(0, x - self.GetWidth() + 3)
		self.SetPosition(px, y)

	def OnUpdate(self):
		wnd = self.characterWindow
		if wnd:
			try:
				shown = wnd.IsShow()
			except Exception:
				shown = False
			if not shown:
				# hidden with the character window; it comes back with it (OnCharacterWindowShow)
				self.Hide()
				if self.toolTip:
					self.toolTip.HideToolTip()
				return
			self.__Dock()

	def OnMouseWheel(self, nLen):
		if not self.scrollBar:
			return False
		if nLen > 0:
			self.scrollBar.OnUp()
		elif nLen < 0:
			self.scrollBar.OnDown()
		return True

	def ButtonOverIn(self, name, tooltip_text):
		if not self.toolTip:
			return
		self.toolTip.ClearToolTip()
		self.toolTip.SetTitle(name)
		self.toolTip.AppendDescription(tooltip_text, 26, TOOLTIP_COLOR)
		self.toolTip.ShowToolTip()

	def ButtonOverOut(self):
		if self.toolTip:
			self.toolTip.HideToolTip()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def Close(self):
		self.isWanted = False
		if self.toolTip:
			self.toolTip.HideToolTip()
		self.Hide()
