# MT2009_PLUS_NPC_LOCATION_HELPER_V1 (Autor: Best Studio): the package's layout; "outline_window" -> "thinboard_circle" (our ui.py).
import uiScriptLocale

ROOT_PATH = "d:/ymir work/ui/game/npc_location_helper/"

WINDOW_WIDTH		= 210
WINDOW_HEIGHT		= 430

window = {
	"name" : "NPCLocationHelper_MobInfo",
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

			"title" : uiScriptLocale.NPC_LOCATION_HELPER_MOB_INFO_TITLE,

			"children" :
			(
				{
					"name"		: "bg_window",
					"type"		: "thinboard_circle",
					"x"			: 10,
					"y"			: 32,
					"width"		: 190,
					"height"	: 386,

					"children"	:
					(

						{
							"name"	: "tab_menu_1_monster_infos",
							"type"	: "image",
							"x"		: 3,
							"y"		: 2,
							"image"	: ROOT_PATH + "tab_menu_3_mob_info.sub",

							"children"	:
							(
								{
									"name"		: "tab_menu_1_monster_text",
									"type"		: "text",
									"x"			: 0,
									"y"			: 0,
									"all_align"	: "center",
									"text"		: uiScriptLocale.NPC_LOCATION_HELPER_MOB_INFO_MOB_INFO,
								},
							),
						},


						{
							"name"	: "mob_info_window",
							"type"	: "window",

							"x"		: 0,
							"y"		: 26,

							"width"		: 190,
							"height"	: 18 * 9,
						},


						{
							"name"	: "tab_menu_2_drop_item_info",
							"type"	: "image",
							"x"		: 3,
							"y"		: 192,
							"image"	: ROOT_PATH + "tab_menu_4_drop_item_info.sub",

							"children"	:
							(
								{
									"name"		: "tab_menu_2_drop_item_info_text",
									"type"		: "text",
									"x"			: 0,
									"y"			: 0,
									"all_align"	: "center",
									"text"		: uiScriptLocale.NPC_LOCATION_HELPER_MOB_INFO_DROP_ITEM_INFO,
								},
							),
						},


						{
							"name"	: "drop_item_info_window",
							"type"	: "window",

							"x"		: 3,
							"y"		: 217,

							"width"		: 190,
							"height"	: 18 * 9,
						},
					),
				},
			),
		},
	),
}
