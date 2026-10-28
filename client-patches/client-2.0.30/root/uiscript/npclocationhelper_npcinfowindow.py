# MT2009_PLUS_NPC_LOCATION_HELPER_V1 (Autor: Best Studio): the package's layout; "outline_window" -> "thinboard_circle" (our ui.py).
import uiScriptLocale

ROOT_PATH = "d:/ymir work/ui/game/npc_location_helper/"

WINDOW_WIDTH		= 286
WINDOW_HEIGHT		= 434

window = {
	"name" : "NPCHelper_NPCInfo",
	"style" : ("movable", "float",),

	"x" : SCREEN_WIDTH / 2 - WINDOW_WIDTH / 2,
	"y" : SCREEN_HEIGHT / 2 - WINDOW_HEIGHT / 2,

	"width" : WINDOW_WIDTH,
	"height" : WINDOW_HEIGHT,

	"children" :
	(
		{
			"name" : "board",
			"type" : "board_with_titlebar",

			"x" : 0,
			"y" : 0,

			"width"		: WINDOW_WIDTH,
			"height"	: WINDOW_HEIGHT,

			"title" : uiScriptLocale.NPC_HELPER_NPC_INFO_TITLE,

			"children" :
			(
				{
					"name"		: "bg_window",
					"type"		: "thinboard_circle",
					"x"			: 10,
					"y"			: 32,
					"width"		: 266,
					"height"	: 390,

					"children"	:
					(

						{
							"name"	: "tab_menu_2_npc_list",
							"type"	: "image",
							"x"		: 3,
							"y"		: 109 - 32 - 14,
							"image"	: ROOT_PATH + "tab_menu_2_npc_info.sub",

							"children"	:
							(
								{
									"name"		: "tab_menu_2_npc_list",
									"type"		: "text",
									"x"			: 0,
									"y"			: 0,
									"all_align"	: "center",
									"text"		: uiScriptLocale.NPC_HELPER_NPC_INFO_MENU_NPC_LIST,
								},
							),
						},


						{
							"name" : "npc_list_window",
							"type" : "window",

							"x"		: 0,
							"y"		: 100 - 14,
							"color"	: 0xFFFFFFFF,

							"width"		: 266,
							"height"	: 304,
						},


						{
							"name" : "select_map_window",
							"type" : "window",

							"x"		: 21 - 10,
							"y"		: 84 - 32 - 17,

							"width"		: 225 + 16,
							"height"	: 16,
						},


						{
							"name" : "select_category_window",
							"type" : "window",

							"x"		: 21 - 10,
							"y"		: 61 - 32 - 17,

							"width"		: 225 + 16,
							"height"	: 16,
						},
					),
				},
			),
		},
	),
}
