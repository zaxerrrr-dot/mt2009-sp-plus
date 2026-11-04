# MT2009_PLUS_TITLES_V1: Tytuly - the title window (root uicharactertitle.py; the owner's package "Official Title System
# Renewal", its layout). Left: the title list (rows made by uicharactertitle.py), under it the worn title, "Zaloz" /
# "Zdejmij"; right: the preview (the background, the plate / banner / the effect in a render target made in code).
# No import: every text is set by uicharactertitle.py; pictures pack "tytuly" (client-2.0.30/tools/tytuly, GF's
# d:/ymir work/ui/titlesystem_001.dds).

ROOT_PATH = "d:/ymir work/ui/game/title/window/"

LEFTBOARD_WIDTH = 224
LEFTBOARD_HEIGHT = 260
LEFTBOARD_X = 12
LEFTBOARD_Y = 32

RIGHTBOARD_WIDTH = 226
RIGHTBOARD_HEIGHT = 346
RIGHTBOARD_X = 240
RIGHTBOARD_Y = 32

LEFT_BOTTOM_BOARD_HEIGHT = RIGHTBOARD_HEIGHT - LEFTBOARD_HEIGHT
LEFT_BOTTOM_BOARD_Y = LEFTBOARD_HEIGHT + LEFTBOARD_Y - 1
BUTTON_Y = LEFT_BOTTOM_BOARD_HEIGHT - (21 + 8)

MAINBOARD_WIDTH = RIGHTBOARD_X + RIGHTBOARD_WIDTH + LEFTBOARD_X
MAINBOARD_HEIGHT = RIGHTBOARD_HEIGHT + 46

window = {
	"name" : "CharacterTitleWindow",
	"style" : ("movable", "float",),
	"x" : 24 + 253 - 3,
	"y" : (SCREEN_HEIGHT - 37 - 361) / 2,
	"width" : MAINBOARD_WIDTH,
	"height" : MAINBOARD_HEIGHT,
	"children" :
	(
		{
			"name" : "main_board", "type" : "board", "style" : ("attach", "ltr"),
			"x" : 0, "y" : 0, "width" : MAINBOARD_WIDTH, "height" : MAINBOARD_HEIGHT,
			"children" :
			(
				{
					"name" : "main_title_bar", "type" : "titlebar", "style" : ("attach",),
					"x" : 6, "y" : 7, "width" : MAINBOARD_WIDTH - 13,
					"children" :
					(
						{ "name" : "title_name", "type" : "text", "x" : 0, "y" : 0, "text" : "", "all_align" : "center" },
					),
				},
				# the list
				{
					"name" : "list_board", "type" : "thinboard_circle",
					"x" : LEFTBOARD_X, "y" : LEFTBOARD_Y, "width" : LEFTBOARD_WIDTH, "height" : LEFTBOARD_HEIGHT,
					"children" :
					(
						{
							"name" : "list_bar", "type" : "image", "x" : 1, "y" : 0, "image" : ROOT_PATH + "title_list_bar.sub",
							"children" :
							(
								{ "name" : "list_text", "type" : "text", "x" : 0, "y" : 0, "text" : "", "all_align" : "center" },
							),
						},
						{
							"name" : "scroll_bar", "type" : "scrollbar",
							"x" : 17, "y" : 24, "size" : LEFTBOARD_HEIGHT - 25, "horizontal_align" : "right",
						},
					),
				},
				# the worn title, "Zaloz" / "Zdejmij"
				{
					"name" : "current_board", "type" : "thinboard_circle",
					"x" : LEFTBOARD_X, "y" : LEFT_BOTTOM_BOARD_Y, "width" : LEFTBOARD_WIDTH, "height" : LEFT_BOTTOM_BOARD_HEIGHT,
					"children" :
					(
						{
							"name" : "current_bar", "type" : "image", "x" : 1, "y" : 0, "image" : ROOT_PATH + "title_list_bar.sub",
							"children" :
							(
								{ "name" : "current_text", "type" : "text", "x" : 0, "y" : 0, "text" : "", "all_align" : "center" },
							),
						},
						{
							"name" : "equipped_title", "type" : "image", "x" : 12, "y" : 28, "image" : ROOT_PATH + "current_title.sub",
							"children" :
							(
								{ "name" : "equipped_name", "type" : "text", "x" : 0, "y" : 0, "text" : "", "all_align" : "center" },
							),
						},
						{
							"name" : "back_button", "type" : "button", "x" : 195, "y" : 28,
							"default_image" : ROOT_PATH + "back_button_default.sub",
							"over_image" : ROOT_PATH + "back_button_over.sub",
							"down_image" : ROOT_PATH + "back_button_down.sub",
						},
						{
							"name" : "apply_button", "type" : "button", "x" : 12, "y" : BUTTON_Y, "text" : "",
							"default_image" : ROOT_PATH + "button_default.sub",
							"over_image" : ROOT_PATH + "button_over.sub",
							"down_image" : ROOT_PATH + "button_down.sub",
							"disable_image" : ROOT_PATH + "button_default.sub",
						},
						{
							"name" : "clear_button", "type" : "button", "x" : 115, "y" : BUTTON_Y, "text" : "",
							"default_image" : ROOT_PATH + "button_default.sub",
							"over_image" : ROOT_PATH + "button_over.sub",
							"down_image" : ROOT_PATH + "button_down.sub",
							"disable_image" : ROOT_PATH + "button_default.sub",
						},
					),
				},
				# the preview (its pictures and the render target: uicharactertitle.py)
				{
					"name" : "right_board", "type" : "thinboard_circle",
					"x" : RIGHTBOARD_X, "y" : RIGHTBOARD_Y, "width" : RIGHTBOARD_WIDTH, "height" : RIGHTBOARD_HEIGHT,
					"children" :
					(
						{ "name" : "preview_background", "type" : "image", "x" : 1, "y" : 0, "image" : ROOT_PATH + "model_view_background.sub" },
					),
				},
			),
		},
	),
}
