# MT2009_PLUS_CHARDETAILS_V1 (Autor: blackdragonx61, "Character Details renewal"): the bonus window docked on the
# right of the character window (uiattributelist.py). The title comes from uiattributelist.py (DETAILS_TITLE).
MAINBOARD_WIDTH = 200
MAINBOARD_HEIGHT = 364

window = {
	"name" : "CharacterDetailsWindow",
	"style" : ("float",),

	"x" : 274,
	"y" : (SCREEN_HEIGHT - 398) / 2,

	"width" : MAINBOARD_WIDTH,
	"height" : MAINBOARD_HEIGHT,

	"children" :
	(
		{
			"name" : "MainBoard",
			"type" : "board",
			"style" : ("attach", "ltr"),

			"x" : 0,
			"y" : 0,

			"width" : MAINBOARD_WIDTH,
			"height" : MAINBOARD_HEIGHT,

			"children" :
			(
				{
					"name" : "TitleBar",
					"type" : "titlebar",
					"style" : ("attach",),

					"x" : 6,
					"y" : 7,

					"width" : MAINBOARD_WIDTH - 13,

					"children" :
					(
						{ "name" : "TitleName", "type" : "text", "x" : 0, "y" : 0, "text" : "", "all_align" : "center" },
					),
				},

				{
					"name" : "ScrollBar",
					"type" : "scrollbar",

					"x" : 24,
					"y" : 31,
					"size" : MAINBOARD_HEIGHT - 40,
					"horizontal_align" : "right",
				},

				## the clipping mask of the list (uiattributelist.py AREA_Y / AREA_HEIGHT)
				{
					"name" : "object_area_window",
					"type" : "window",
					"style" : ("attach",),

					"x" : 10 + 5,
					"y" : 32 + 5,
					"width" : 155,
					"height" : 310,
				},
			),
		},
	),
}
