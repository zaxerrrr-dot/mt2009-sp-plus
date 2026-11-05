# MT2009_PLUS_GROWTH_PET_V1 - System Zwierzat Domowych: the 3 x 3 feed window (uipetinfo.py PetFeedWindow), the
# official 26.1.11 uiscript/petfeedwindow.py with one text line under the grid (the evolution's target stage / what
# is missing). Three modes: Nakarm (eggs, other seals), Przedmiot EXP (weapons, armour, Smakolyk / Smakolyk+) and
# Rozwoj (the stage's materials, read-only). No text here: uipetinfo.py sets it (the script sandbox imports no root
# module).
# MT2009_PLUS_PET_WINDOW_LAYOUT_V2: 176 wide (was 150) - the info line ("Rozwoj do stopnia: ..." / what is missing)
# did not fit in 140 px; the grid and the button stay centred.

FEED_WIDTH = 176

window = {
	"name" : "PetFeedWindow",
	"style" : ("movable", "float",),

	"x" : SCREEN_WIDTH - 500 + 328 - 148 - (FEED_WIDTH - 150),
	"y" : SCREEN_HEIGHT - 595 + 240,

	"width" : FEED_WIDTH,
	"height" : 190,

	"children" :
	(
		{
			"name" : "board",
			"type" : "board",
			"style" : ("attach",),
			"x" : 0, "y" : 0,
			"width" : FEED_WIDTH, "height" : 190,

			"children" :
			(
				{
					"name" : "PetFeed_TitleBar",
					"type" : "titlebar",
					"style" : ("attach",),
					"x" : 0, "y" : 0,
					"width" : FEED_WIDTH - 2,
					"children" : ({"name" : "TitleName", "type" : "text", "x" : 0, "y" : 0, "text" : "", "all_align" : "center"},),
				},
				{
					"name" : "Pet_Feed_Area",
					"type" : "window",
					"style" : ("attach",),
					"x" : 0, "y" : 26,
					"width" : FEED_WIDTH - 2, "height" : 164,
					"children" :
					(
						{
							"name" : "FeedItemSlot",
							"type" : "grid_table",
							"x" : (FEED_WIDTH - 2 - 96) // 2, "y" : 4,
							"start_index" : 0,
							"x_count" : 3, "y_count" : 3,
							"x_step" : 32, "y_step" : 32,
							"image" : "d:/ymir work/ui/public/Slot_Base.sub",
						},
						{
							"name" : "FeedInfoWindow", "type" : "window", "x" : 4, "y" : 104, "width" : FEED_WIDTH - 10, "height" : 16, "style" : ("attach",),
							"children" : ({"name" : "FeedInfo", "type" : "text", "x" : 0, "y" : 0, "text" : "", "all_align" : "center"},),
						},
						{
							"name" : "FeedButton",
							"type" : "button",
							"x" : 45 + (FEED_WIDTH - 150) // 2, "y" : 126,
							"text" : "",
							"default_image" : "d:/ymir work/ui/public/middle_button_01.sub",
							"over_image" : "d:/ymir work/ui/public/middle_button_02.sub",
							"down_image" : "d:/ymir work/ui/public/middle_button_03.sub",
						},
					),
				},
			),
		},
	),
}
