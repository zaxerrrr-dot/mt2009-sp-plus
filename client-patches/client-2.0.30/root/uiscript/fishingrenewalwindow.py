# MT2009_PLUS_FISHING_RENEWAL_V1: the new fishing minigame's window (uifishingrenewal.py) - the fishing renewal's
# uiscript/fishinggamewindow.py (github.com/amun3808/metin2-fishing-renewal) on GF 26.1.11's pictures
# d:/ymir work/ui/game/fishing/*.sub (fishing_01.dds, pack "fishren", tools/fishren): the water 278 x 226, the circle in
# its middle, the hit counter top right, the timer at the bottom. No imports (the ui.py Sandbox); the title a literal
# CP1250 escape; the board with our "titlebar" as fishpuzzlewindow.py.
ROOT = "d:/ymir work/ui/game/fishing/"

WINDOW_WIDTH	= 278 + 14
WINDOW_HEIGHT	= 226 + 37

window = {
	"name" : "FishingRenewalWindow",
	"style" : ("movable", "float",),

	"x" : SCREEN_WIDTH / 2 - WINDOW_WIDTH / 2,
	"y" : SCREEN_HEIGHT / 2 - WINDOW_HEIGHT / 2 - 60,

	"width" : WINDOW_WIDTH,
	"height" : WINDOW_HEIGHT,

	"children" :
	(
		{
			"name" : "board",
			"type" : "board",
			"style" : ("attach",),

			"x" : 0,
			"y" : 0,

			"width" : WINDOW_WIDTH,
			"height" : WINDOW_HEIGHT,

			"children" :
			(
				{
					"name" : "titlebar",
					"type" : "titlebar",
					"style" : ("attach",),

					"x" : 0,
					"y" : 0,

					"width" : WINDOW_WIDTH,
					"color" : "yellow",

					"children" :
					(
						{ "name" : "TitleName", "type" : "text", "x" : 0, "y" : 0, "text" : "\xa3owienie ryb", "all_align" : "center" },
					),
				},

				## the water
				{
					"name" : "fishing_background_water",
					"type" : "image",
					"style" : ("attach",),

					"x" : 7,
					"y" : 29,

					"image" : ROOT + "fishing_background_water.sub",

					"children" :
					(
						## where the fish may swim (its size only; hidden by uifishingrenewal.py)
						{
							"name" : "fishing_water_navArea",
							"type" : "box",
							"style" : ("not_pick",),

							"x" : 15,
							"y" : 15,

							"width" : 278 - 30,
							"height" : 226 - 30,

							"color" : 0xFF35302D,
						},

						## the circle the fish has to be in
						{
							"name" : "fishing_goal_circle",
							"type" : "image",
							"style" : ("not_pick",),

							"x" : 68,
							"y" : 42,

							"image" : ROOT + "fishing_goal_circle.sub",
						},
					),
				},

				## the hits (2/3)
				{
					"name" : "fishing_goal_count",
					"type" : "image",
					"style" : ("not_pick",),

					"x" : 7 + 278 - 73,
					"y" : 29 + 5,

					"image" : ROOT + "fishing_goal_count.sub",

					"children" :
					(
						{ "name" : "fishing_goal_count_text", "type" : "text", "x" : 0, "y" : 0, "text" : "0/3", "all_align" : "center" },
					),
				},

				## the timer
				{
					"name" : "fishing_timer_baseImg",
					"type" : "image",
					"style" : ("not_pick",),

					"x" : 7 + 28,
					"y" : 223,

					"image" : ROOT + "fishing_timer_base.sub",
				},
				{
					"name" : "fishing_timer_gauge",
					"type" : "expanded_image",
					"style" : ("not_pick",),

					"x" : 7 + 28,
					"y" : 223,

					"image" : ROOT + "fishing_timer_gauge.sub",
				},
			),
		},
	),
}
