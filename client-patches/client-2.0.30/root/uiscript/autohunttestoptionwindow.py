# MT2009_PLUS_AUTOHUNT_TEST_V1 - the TEST auto hunt's "what to attack" window (root uiautohunt_test.py): the package's
# UIScript/AutoAttackOptionWindow.py, Polish texts. The seven check boxes are made by uiautohunt_test.py.
import uiScriptLocale

BOARD_WIDTH = 192
BOARD_HEIGHT = 190

PATTERN = "d:/ymir work/ui/pattern/"
HUNT = "d:/ymir work/ui/game/auto_hunting/"
ROOT = "d:/ymir work/ui/game/windows/"


def _Button(name, x, text):
	return {
		"name" : name, "type" : "button", "x" : x, "y" : BOARD_HEIGHT - 31, "text" : text,
		"default_image" : ROOT + "auto_system_bottom_button_01.sub",
		"over_image" : ROOT + "auto_system_bottom_button_02.sub",
		"down_image" : ROOT + "auto_system_bottom_button_03.sub",
	}


def _LevelEdit(name, x):
	return {
		"name" : name + "_img", "type" : "image", "x" : x, "y" : 16 * 8 + 4,
		"image" : HUNT + "auto_attack_level_range_edit_img.sub",
		"children" : (
			{
				"name" : name, "type" : "editline", "x" : 3, "y" : 2,
				"input_limit" : 3, "only_number" : 1, "width" : 70, "height" : 16,
			},
		),
	}


window = {
	"name" : "AutoHuntTestOptionWindow",
	"x" : 0,
	"y" : 0,
	"style" : ("float",),
	"width" : BOARD_WIDTH,
	"height" : BOARD_HEIGHT,
	"children" : (
		{
			"name" : "board",
			"type" : "board",
			"x" : 0,
			"y" : 0,
			"width" : BOARD_WIDTH,
			"height" : BOARD_HEIGHT,
			"children" : (
				{ "name" : "leftTop", "type" : "image", "x" : 10, "y" : 10, "image" : PATTERN + "border_A_left_top.tga", },
				{ "name" : "rightTop", "type" : "image", "x" : 165, "y" : 10, "image" : PATTERN + "border_A_right_top.tga", },
				{ "name" : "leftBottom", "type" : "image", "x" : 10, "y" : 138, "image" : PATTERN + "border_A_left_bottom.tga", },
				{ "name" : "rightBottom", "type" : "image", "x" : 165, "y" : 138, "image" : PATTERN + "border_A_right_bottom.tga", },
				{ "name" : "topCenter", "type" : "expanded_image", "x" : 26, "y" : 10, "image" : PATTERN + "border_A_top.tga", "rect" : (0.0, 0.0, 8, 0), },
				{ "name" : "leftCenter", "type" : "expanded_image", "x" : 10, "y" : 26, "image" : PATTERN + "border_A_left.tga", "rect" : (0.0, 0.0, 0, 6), },
				{ "name" : "rightCenter", "type" : "expanded_image", "x" : 165, "y" : 26, "image" : PATTERN + "border_A_right.tga", "rect" : (0.0, 0.0, 0, 6), },
				{ "name" : "bottomCenter", "type" : "expanded_image", "x" : 26, "y" : 138, "image" : PATTERN + "border_A_bottom.tga", "rect" : (0.0, 0.0, 8, 0), },
				{ "name" : "center", "type" : "expanded_image", "x" : 26, "y" : 26, "image" : PATTERN + "border_A_center.tga", "rect" : (0.0, 0.0, 7, 6), },
				{
					"name" : "level_range",
					"type" : "image",
					"x" : 16,
					"y" : 16 * 8 + 5,
					"image" : HUNT + "auto_attack_level_range_back_img.sub",
					"children" : (
						{ "name" : "level_range_text", "type" : "text", "x" : 16, "y" : 0, "text" : "Poziom", },
					),
				},
				{ "name" : "level_range_min_img", "type" : "image", "x" : 89, "y" : 16 * 8 + 12, "image" : HUNT + "auto_attack_level_range_min_img.sub", },
				_LevelEdit("auto_attack_level_min", 98),
				{ "name" : "level_range_sign", "type" : "text", "x" : 126, "y" : 16 * 8 + 5, "text" : "~", },
				{ "name" : "level_range_max_img", "type" : "image", "x" : 140, "y" : 16 * 8 + 10, "image" : HUNT + "auto_attack_level_range_max_img.sub", },
				_LevelEdit("auto_attack_level_max", 148),
				_Button("ClearButton", 19, "Domy\x9clne"),
				_Button("AcceptButton", 97, "Zatwierd\x9f"),
			),
		},
	),
}
