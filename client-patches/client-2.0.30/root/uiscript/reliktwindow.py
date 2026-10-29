# MT2009_PLUS_RELIC_V1: the window of Bonus Reliktu (root/uirelikt.py) - the layout of GF 26.1.11 uiscript/passiveattr.py
# (the package "Official Passive Attr System", Best Studio): the relic in the middle, the four souls round it (up: Dusza
# Miecza, down: Dusza Swiatla, left: Dusza Ochrony, right: Dusza Ozdoby), the page buttons I / II; under it the page,
# the time and the buttons Doladuj / Dodaj / Aktywuj / Wyjmij. Images: the pack "relikty" (passive_attr/*.sub,
# passive_01.dds); texts CP1250.

ROOT = "d:/ymir work/ui/game/passive_attr/"
PUBLIC_PATH = "d:/ymir work/ui/public/"

WINDOW_WIDTH = 200
WINDOW_HEIGHT = 308

BG_X = 14
BG_Y = 35
BG_SIZE = 172

SLOT_RELIC = 0
SLOT_UP, SLOT_DOWN, SLOT_LEFT, SLOT_RIGHT = 1, 2, 3, 4

window = {
	"name" : "ReliktWindow",
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

			"width" : WINDOW_WIDTH,
			"height" : WINDOW_HEIGHT,

			"title" : "Bonus Reliktu",

			"children" :
			(
				{
					"name" : "bg",
					"type" : "image",

					"x" : BG_X,
					"y" : BG_Y,
					"image" : ROOT + "bg.sub",

					"children" :
					(
						{
							"name" : "soul_slot",
							"type" : "slot",

							"x" : 0,
							"y" : 0,
							"width" : BG_SIZE,
							"height" : BG_SIZE,

							"slot" : (
								{"index" : SLOT_UP,		"x" : 70,	"y" : 13,	"width" : 32, "height" : 32},
								{"index" : SLOT_DOWN,	"x" : 70,	"y" : 127,	"width" : 32, "height" : 32},
								{"index" : SLOT_LEFT,	"x" : 13,	"y" : 70,	"width" : 32, "height" : 32},
								{"index" : SLOT_RIGHT,	"x" : 127,	"y" : 70,	"width" : 32, "height" : 32},
							),
						},
						{
							"name" : "relic_slot",
							"type" : "slot",

							"x" : 70,
							"y" : 70,
							"width" : 32,
							"height" : 32,

							"slot" : (
								{"index" : SLOT_RELIC, "x" : 0, "y" : 0, "width" : 32, "height" : 32},
							),
						},
						{
							"name" : "page_button_1",
							"type" : "radio_button",

							"x" : 6,
							"y" : 134,

							"default_image" : ROOT + "up_button_default.sub",
							"over_image" : ROOT + "up_button_over.sub",
							"down_image" : ROOT + "up_button_down.sub",
						},
						{
							"name" : "page_button_2",
							"type" : "radio_button",

							"x" : 134,
							"y" : 134,

							"default_image" : ROOT + "down_button_default.sub",
							"over_image" : ROOT + "down_button_over.sub",
							"down_image" : ROOT + "down_button_down.sub",
						},
					),
				},
				{
					"name" : "page_text",
					"type" : "text",

					"x" : 0,
					"y" : BG_Y + BG_SIZE + 6,
					"horizontal_align" : "center",
					"text_horizontal_align" : "center",
					"text" : "",
				},
				{
					"name" : "time_text",
					"type" : "text",

					"x" : 0,
					"y" : BG_Y + BG_SIZE + 22,
					"horizontal_align" : "center",
					"text_horizontal_align" : "center",
					"text" : "",
				},
				{
					"name" : "ChargeButton",
					"type" : "button",

					"x" : 12,
					"y" : 248,

					"default_image" : PUBLIC_PATH + "large_button_01.sub",
					"over_image" : PUBLIC_PATH + "large_button_02.sub",
					"down_image" : PUBLIC_PATH + "large_button_03.sub",

					"text" : "Do\xb3aduj",
				},
				{
					"name" : "AddButton",
					"type" : "button",

					"x" : 100,
					"y" : 248,

					"default_image" : PUBLIC_PATH + "large_button_01.sub",
					"over_image" : PUBLIC_PATH + "large_button_02.sub",
					"down_image" : PUBLIC_PATH + "large_button_03.sub",

					"text" : "Dodaj",
				},
				{
					"name" : "ActivateButton",
					"type" : "button",

					"x" : 12,
					"y" : 274,

					"default_image" : PUBLIC_PATH + "large_button_01.sub",
					"over_image" : PUBLIC_PATH + "large_button_02.sub",
					"down_image" : PUBLIC_PATH + "large_button_03.sub",

					"text" : "Aktywuj",
				},
				{
					"name" : "TakeButton",
					"type" : "button",

					"x" : 100,
					"y" : 274,

					"default_image" : PUBLIC_PATH + "large_button_01.sub",
					"over_image" : PUBLIC_PATH + "large_button_02.sub",
					"down_image" : PUBLIC_PATH + "large_button_03.sub",

					"text" : "Wyjmij",
				},
				{
					"name" : "HelpButton",
					"type" : "button",

					"x" : WINDOW_WIDTH - 46,
					"y" : 9,

					"default_image" : "d:/ymir work/ui/pattern/q_mark_01.tga",
					"over_image" : "d:/ymir work/ui/pattern/q_mark_02.tga",
					"down_image" : "d:/ymir work/ui/pattern/q_mark_01.tga",
				},
			),
		},
	),
}
