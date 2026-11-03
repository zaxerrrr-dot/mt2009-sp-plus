# MT2009_PLUS_FISH_PUZZLE_V1: Event Rybacki - Puzzle's window - GF 26.1.11's uiscript/minigamefishgamepage.py (288 x 208,
# the same places); its pictures d:/ymir work/ui/minigame/fish_event/*.sub on d:/ymir work/ui/fishingevnet001.dds travel
# in the pack "fishpuzzle" (tools/fishpuzzle). GF's "fish_event_grid_table" (an exe window type our exe lacks) is left
# out: uifishpuzzle.py lays its own grid window over GameSlotImg. No imports (the ui.py Sandbox), the texts literal
# CP1250 escapes (pl-wiki "Minigra: Wedkarskie Puzzle").
ROOT = "d:/ymir work/ui/minigame/fish_event/"

WINDOW_WIDTH	= 288
WINDOW_HEIGHT	= 208

window = {
	"name" : "FishPuzzleWindow",
	"style" : ("movable", "float",),

	"x" : SCREEN_WIDTH / 2 - WINDOW_WIDTH / 2,
	"y" : SCREEN_HEIGHT / 2 - WINDOW_HEIGHT / 2,

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
						{ "name" : "TitleName", "type" : "text", "x" : 0, "y" : 0, "text" : "W\xeadkarskie puzzle", "all_align" : "center" },
					),
				},

				## the board (6 x 4 cells of 32 px from 18, 34)
				{
					"name" : "GameSlotImg",
					"type" : "expanded_image",
					"style" : ("attach",),

					"x" : 14,
					"y" : 30,

					"image" : ROOT + "fish_grid_slot.sub",
				},
				## the deluxe box
				{
					"name" : "SpecialItemSlotBG",
					"type" : "expanded_image",
					"style" : ("attach",),
					"x" : 225,
					"y" : 54,
					"image" : ROOT + "fish_special_slot.sub",
				},
				{
					"name" : "SpecialItemSlot",
					"type" : "slot",

					"x" : 225 + 7,
					"y" : 54 + 7,
					"width" : 32,
					"height" : 32,

					"slot" : ({"index" : 0, "x" : 0, "y" : 0, "width" : 32, "height" : 32,},),
				},
				## the box
				{
					"name" : "NormalItemSlotBG",
					"type" : "expanded_image",
					"style" : ("attach",),
					"x" : 225,
					"y" : 105,
					"image" : ROOT + "fish_normal_slot.sub",
				},
				{
					"name" : "NormalItemSlot",
					"type" : "slot",

					"x" : 225 + 7,
					"y" : 105 + 7,
					"width" : 32,
					"height" : 32,

					"slot" : ({"index" : 0, "x" : 0, "y" : 0, "width" : 32, "height" : 32,},),
				},
				{
					"name" : "help_button",
					"type" : "button",

					"x" : 15,
					"y" : 177,

					"text" : "Pomoc",

					"default_image" : "d:/ymir work/ui/public/large_button_01.sub",
					"over_image" : "d:/ymir work/ui/public/large_button_02.sub",
					"down_image" : "d:/ymir work/ui/public/large_button_03.sub",
				},
				{
					"name" : "discard_button",
					"type" : "button",

					"x" : 108,
					"y" : 177,

					"text" : "Odrzu\xe6",

					"default_image" : "d:/ymir work/ui/public/middle_button_01.sub",
					"over_image" : "d:/ymir work/ui/public/middle_button_02.sub",
					"down_image" : "d:/ymir work/ui/public/middle_button_03.sub",
				},
				{
					"name" : "count_text",
					"type" : "text",

					"x" : 175,
					"y" : 182,

					"text" : "Pr\xf3by:",
				},
				{
					"name" : "use_count_area",
					"type" : "expanded_image",
					"style" : ("attach",),

					"x" : 219,
					"y" : 178,

					"image" : ROOT + "fish_use_count_area.sub",
				},
				{
					"name" : "use_count_window", "type" : "window", "x" : 219, "y" : 178, "width" : 51, "height" : 18, "style" : ("attach",),
					"children" :
					(
						{ "name" : "use_count_text", "type" : "text", "x" : 0, "y" : 0, "text" : "0", "color" : 0xFFFFFFFF, "all_align" : "center" },
					),
				},
				## the finished board (Rumi's card effects, the pack "minigames")
				{
					"name" : "score_completion_effect1",
					"type" : "ani_image",
					"x" : -5,
					"y" : 23,
					"delay" : 6,
					"images" :
					(
						"D:/Ymir Work/UI/minigame/rumi/card_completion_effect/card_completion_eff1.sub",
						"D:/Ymir Work/UI/minigame/rumi/card_completion_effect/card_completion_eff2.sub",
						"D:/Ymir Work/UI/minigame/rumi/card_completion_effect/card_completion_eff3.sub",
						"D:/Ymir Work/UI/minigame/rumi/card_completion_effect/card_completion_eff4.sub",
						"D:/Ymir Work/UI/minigame/rumi/card_completion_effect/card_completion_eff5.sub",
						"D:/Ymir Work/UI/minigame/rumi/card_completion_effect/card_completion_eff6.sub",
						"D:/Ymir Work/UI/minigame/rumi/card_completion_effect/card_completion_eff7.sub",
						"D:/Ymir Work/UI/minigame/rumi/card_completion_effect/card_completion_eff8.sub",
					),
				},
				{
					"name" : "score_completion_effect2",
					"type" : "ani_image",
					"x" : 38,
					"y" : 23,
					"delay" : 6,
					"images" :
					(
						"D:/Ymir Work/UI/minigame/rumi/card_completion_effect/card_completion_eff1.sub",
						"D:/Ymir Work/UI/minigame/rumi/card_completion_effect/card_completion_eff2.sub",
						"D:/Ymir Work/UI/minigame/rumi/card_completion_effect/card_completion_eff3.sub",
						"D:/Ymir Work/UI/minigame/rumi/card_completion_effect/card_completion_eff4.sub",
						"D:/Ymir Work/UI/minigame/rumi/card_completion_effect/card_completion_eff5.sub",
						"D:/Ymir Work/UI/minigame/rumi/card_completion_effect/card_completion_eff6.sub",
						"D:/Ymir Work/UI/minigame/rumi/card_completion_effect/card_completion_eff7.sub",
						"D:/Ymir Work/UI/minigame/rumi/card_completion_effect/card_completion_eff8.sub",
					),
				},
				{
					"name" : "score_completion_effect3",
					"type" : "ani_image",
					"x" : 81,
					"y" : 23,
					"delay" : 6,
					"images" :
					(
						"D:/Ymir Work/UI/minigame/rumi/card_completion_effect/card_completion_eff1.sub",
						"D:/Ymir Work/UI/minigame/rumi/card_completion_effect/card_completion_eff2.sub",
						"D:/Ymir Work/UI/minigame/rumi/card_completion_effect/card_completion_eff3.sub",
						"D:/Ymir Work/UI/minigame/rumi/card_completion_effect/card_completion_eff4.sub",
						"D:/Ymir Work/UI/minigame/rumi/card_completion_effect/card_completion_eff5.sub",
						"D:/Ymir Work/UI/minigame/rumi/card_completion_effect/card_completion_eff6.sub",
						"D:/Ymir Work/UI/minigame/rumi/card_completion_effect/card_completion_eff7.sub",
						"D:/Ymir Work/UI/minigame/rumi/card_completion_effect/card_completion_eff8.sub",
					),
				},
			),
		},
	),
}
