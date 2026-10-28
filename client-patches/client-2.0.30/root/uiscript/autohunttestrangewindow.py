# MT2009_PLUS_AUTOHUNT_TEST_V1 - the TEST auto hunt's range window (root uiautohunt_test.py): the package's
# UIScript/AutoHuntingRangeWindow.py, Polish texts. While it is open the range is drawn on the ground (the exe's
# player.AutoHuntTestShowRange, d:/ymir work/effect/etc/auto_hunt/auto_hunt_range_01.mse).
import uiScriptLocale

BOARD_WIDTH = 230
BOARD_HEIGHT = 110

PATTERN = "d:/ymir work/ui/pattern/"
ROOT = "d:/ymir work/ui/game/windows/"

window = {
	"name" : "AutoHuntTestRangeWindow",
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
				{ "name" : "rightTop", "type" : "image", "x" : 200, "y" : 10, "image" : PATTERN + "border_A_right_top.tga", },
				{ "name" : "leftBottom", "type" : "image", "x" : 10, "y" : 55, "image" : PATTERN + "border_A_left_bottom.tga", },
				{ "name" : "rightBottom", "type" : "image", "x" : 200, "y" : 55, "image" : PATTERN + "border_A_right_bottom.tga", },
				{ "name" : "topCenter", "type" : "expanded_image", "x" : 26, "y" : 10, "image" : PATTERN + "border_A_top.tga", "rect" : (0.0, 0.0, 10, 0), },
				{ "name" : "leftCenter", "type" : "expanded_image", "x" : 10, "y" : 26, "image" : PATTERN + "border_A_left.tga", "rect" : (0.0, 0.0, 0, 1), },
				{ "name" : "rightCenter", "type" : "expanded_image", "x" : 200, "y" : 26, "image" : PATTERN + "border_A_right.tga", "rect" : (0.0, 0.0, 0, 1), },
				{ "name" : "bottomCenter", "type" : "expanded_image", "x" : 26, "y" : 55, "image" : PATTERN + "border_A_bottom.tga", "rect" : (0.0, 0.0, 10, 0), },
				{ "name" : "center", "type" : "expanded_image", "x" : 26, "y" : 26, "image" : PATTERN + "border_A_center.tga", "rect" : (0.0, 0.0, 10, 1), },
				{
					"name" : "hunting_range_sliderbar",
					"type" : "sliderbar",
					"x" : 0,
					"y" : BOARD_HEIGHT - 85,
					"horizontal_align" : "center",
				},
				{
					"name" : "range_back_ui",
					"type" : "image",
					"x" : 0,
					"y" : BOARD_HEIGHT - 65,
					"horizontal_align" : "center",
					"image" : ROOT + "auto_system_edit_line.sub",
					"children" : (
						{ "name" : "range_text", "type" : "text", "x" : 0, "y" : 0, "all_align" : "center", "text" : "", },
					),
				},
				{
					"name" : "AcceptButton",
					"type" : "button",
					"x" : 0,
					"y" : BOARD_HEIGHT - 31,
					"horizontal_align" : "center",
					"text" : "Zatwierd\x9f",
					"default_image" : ROOT + "auto_system_bottom_button_01.sub",
					"over_image" : ROOT + "auto_system_bottom_button_02.sub",
					"down_image" : ROOT + "auto_system_bottom_button_03.sub",
				},
			),
		},
	),
}
