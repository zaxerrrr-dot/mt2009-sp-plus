# MT2009_PLUS_AUTOHUNT_TEST_V1 - the TEST auto hunt's window (root uiautohunt_test.py, Alt+H). The layout of the
# uploaded package's UIScript/AutoWindow.py (GF's auto hunt window; its images are in the base client's etc pack),
# the texts in Polish (CP1250 escapes) instead of uiScriptLocale's AUTO_* keys, the 24 time fields built by a loop.
import uiScriptLocale

BOARD_WIDTH = 254
BOARD_HEIGHT = 490

BAR_X = 14
BAR_WIDTH = 223
CLEAR_X = 207
SLOT_X = 15
SLOT_Y = 57
SLOT_DX = 38
SLOT_DY = 54
SLOT_GAP_Y = 29
BUTTON_X = 194
BUTTON_Y = 327
BUTTON_DY = 27

ROOT = "d:/ymir work/ui/game/windows/"
HUNT = "d:/ymir work/ui/game/auto_hunting/"
SMALL = "d:/ymir work/ui/public/Small_Button_0"


def _ClearButton(name, x, y):
	return {
		"name" : name, "type" : "button", "x" : x, "y" : y,
		"default_image" : ROOT + "auto_system_clear_button_01.sub",
		"over_image" : ROOT + "auto_system_clear_button_02.sub",
		"down_image" : ROOT + "auto_system_clear_button_03.sub",
	}


def _Bar(name, y, text, clearName):
	return {
		"name" : name, "type" : "horizontalbar", "x" : BAR_X, "y" : y, "width" : BAR_WIDTH,
		"children" : (
			{ "name" : name + "Text", "type" : "text", "x" : 9, "y" : 2, "text" : text, },
			_ClearButton(clearName, CLEAR_X, 1),
		),
	}


def _Slots():
	slots = []
	for i in range(12):
		slots.append({ "index" : i, "x" : SLOT_DX * (i % 6), "y" : SLOT_DY * (i // 6), "width" : 32, "height" : 32 })
	for i in range(12):
		slots.append({ "index" : 13 + i, "x" : SLOT_DX * (i % 6), "y" : SLOT_GAP_Y + SLOT_DY * (2 + i // 6), "width" : 32, "height" : 32 })
	return tuple(slots)


def _EditLines():
	lines = []
	for i in range(24):
		row = i // 6
		y = SLOT_Y + 32 + SLOT_DY * row + (SLOT_GAP_Y if row >= 2 else 0)	# under its slot (89, 143, 226, 280)
		lines.append({
			"name" : "cool_time_Image%d" % i, "type" : "image",
			"x" : SLOT_X + SLOT_DX * (i % 6), "y" : y,
			"image" : ROOT + "auto_system_edit_line.sub",
			"children" : (
				{
					"name" : "editline%d" % i, "type" : "editline", "x" : 3, "y" : 3,
					"input_limit" : 4, "only_number" : 1, "width" : 90, "height" : 20,
				},
			),
		})
	return tuple(lines)


def _TextBar(name, y, image, text):
	return {
		"name" : name, "type" : "image", "x" : 3, "y" : y, "image" : ROOT + image,
		"children" : (
			{ "name" : name + "Text", "type" : "text", "x" : 2, "y" : 0, "all_align" : "center", "text" : text, },
		),
	}


def _Toggle(name, row):
	return {
		"name" : name, "type" : "toggle_button", "x" : BUTTON_X, "y" : BUTTON_Y + BUTTON_DY * row,
		"text" : "Wy\xb3",
		"default_image" : SMALL + "1.sub", "over_image" : SMALL + "2.sub", "down_image" : SMALL + "3.sub",
	}


def _OpenButton(name, row):
	return {
		"name" : name, "type" : "button", "x" : BUTTON_X + 42, "y" : BUTTON_Y + BUTTON_DY * row,
		"default_image" : HUNT + "option_window_open_button_01.sub",
		"over_image" : HUNT + "option_window_open_button_02.sub",
		"down_image" : HUNT + "option_window_open_button_03.sub",
	}


def _BottomButton(name, x, text):
	return {
		"name" : name, "type" : "button", "x" : x, "y" : 459, "text" : text,
		"default_image" : ROOT + "auto_system_bottom_button_01.sub",
		"over_image" : ROOT + "auto_system_bottom_button_02.sub",
		"down_image" : ROOT + "auto_system_bottom_button_03.sub",
	}


window = {
	"name" : "AutoHuntTestWindow",
	"x" : 0,
	"y" : 0,
	"style" : ("movable", "float",),
	"width" : BOARD_WIDTH,
	"height" : BOARD_HEIGHT,
	"children" : (
		{
			"name" : "board",
			"type" : "board_with_titlebar",
			"x" : 0,
			"y" : 0,
			"width" : BOARD_WIDTH,
			"height" : BOARD_HEIGHT,
			"title" : "Auto \xa3owy (TEST)",
			"children" : (
				_Bar("SkillSettingBar", 34, "Umiej\xeatno\x9cci", "AutoSkillClearButton"),
				{
					"name" : "Auto_Active_Skill_Slot_Table",
					"type" : "slot",
					"x" : SLOT_X,
					"y" : SLOT_Y,
					"width" : 221,
					"height" : 241,
					"image" : "d:/ymir work/ui/public/Slot_Base.sub",
					"slot" : _Slots(),
				},
			) + _EditLines() + (
				_Bar("PotionSettingBar", 171, "Mikstury i przedmioty", "AutoPotionClearButton"),
				{
					"name" : "AutoSettingBar",
					"type" : "horizontalbar",
					"x" : BAR_X,
					"y" : 308,
					"width" : BAR_WIDTH,
					"children" : (
						{ "name" : "AutoSettingBarText", "type" : "text", "x" : 9, "y" : 2, "text" : "Ustawienia", },
						_TextBar("attack_text_bar", 20, "auto_system_text_bar_01.sub", "Atak (cel)"),
						_TextBar("range_text_bar", 47, "auto_system_text_bar_01.sub", "Zasi\xeag od startu"),
						_TextBar("potion_text_bar", 74, "auto_system_text_bar_02.sub", "Mikstury"),
						_TextBar("skill_text_bar", 101, "auto_system_text_bar_02.sub", "Umiej\xeatno\x9cci"),
						_TextBar("restart_text_bar", 128, "auto_system_text_bar_02.sub", "Wstawanie po \x9cmierci"),
					),
				},
				_Toggle("AutoAttackButton", 0),
				_OpenButton("AutoAttackOptionButton", 0),
				_Toggle("AutoRangeButton", 1),
				_OpenButton("AutoRangeSelectButton", 1),
				_Toggle("AutoPotionButton", 2),
				_Toggle("AutoSkillButton", 3),
				_Toggle("AutoRestartHereButton", 4),
				_BottomButton("AutoSaveOnButton", 10, "Zapisz"),
				_BottomButton("AutoStartOnButton", 88, "Start"),
				_BottomButton("AutoStartOffButton", 166, "Stop"),
				{
					"name" : "AutoToolTipButton",
					"type" : "button",
					"x" : 155,
					"y" : 8,
					"default_image" : "d:/ymir work/ui/pattern/q_mark_01.tga",
					"over_image" : "d:/ymir work/ui/pattern/q_mark_02.tga",
					"down_image" : "d:/ymir work/ui/pattern/q_mark_01.tga",
				},
				_ClearButton("AutoAllClearButton", BAR_X + CLEAR_X, 309),
			),
		},
	),
}
