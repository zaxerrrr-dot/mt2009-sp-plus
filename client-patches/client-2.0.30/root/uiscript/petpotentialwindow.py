# MT2009_PLUS_GROWTH_PET_V1 - System Zwierzat Domowych: a champion pet's potential (uipetinfo.py
# PetPotentialWindow), the official 26.1.11 uiscript/petpotentialwindow.py: two egg slots (the second opens at
# champion level 15), under each the skill the egg gave and a bar of the time it has left. An egg is dragged in,
# a right click takes it out (it is lost). Our ui has no "outline_window": a thin board instead. No text here:
# uipetinfo.py sets the title (the script sandbox imports no root module).

ROOT_PATH = "d:/ymir work/ui/pet/"

window = {
	"name" : "PetPotentialWindow",
	"style" : ("movable", "float",),

	"x" : SCREEN_WIDTH - 500 + 328 - 148,
	"y" : SCREEN_HEIGHT - 595 + 240 - 166,

	"width" : 174,
	"height" : 166,

	"children" :
	(
		{
			"name" : "potential_board",
			"type" : "board_with_titlebar",
			"style" : ("attach",),
			"x" : 0, "y" : 0,
			"width" : 174, "height" : 166,
			"title" : "",

			"children" :
			(
				{"name" : "desc_window_background", "type" : "thinboard", "x" : 10, "y" : 32, "width" : 154, "height" : 124},
				{
					"name" : "potential_pet_slot_bg_0", "type" : "image", "x" : 33, "y" : 41,
					"image" : ROOT_PATH + "conqueror/potential_pet_slot_bg.sub",
					"children" : ({"name" : "potential_pet_slot_0", "type" : "grid_table", "x" : 4, "y" : 4, "start_index" : 0, "x_count" : 1, "y_count" : 1, "x_step" : 32, "y_step" : 32},),
				},
				{
					"name" : "potential_pet_slot_bg_1", "type" : "image", "x" : 99, "y" : 41,
					"image" : ROOT_PATH + "conqueror/potential_pet_slot_bg.sub",
					"children" : ({"name" : "potential_pet_slot_1", "type" : "grid_table", "x" : 4, "y" : 4, "start_index" : 0, "x_count" : 1, "y_count" : 1, "x_step" : 32, "y_step" : 32},),
				},
				{
					"name" : "potential_skill_slot_bg_0", "type" : "image", "x" : 33, "y" : 105,
					"image" : ROOT_PATH + "conqueror/potential_slot_bg.sub",
					"children" : ({"name" : "potential_skill_slot_0", "type" : "grid_table", "x" : 4, "y" : 4, "start_index" : 0, "x_count" : 1, "y_count" : 1, "x_step" : 32, "y_step" : 32},),
				},
				{
					"name" : "potential_skill_slot_bg_1", "type" : "image", "x" : 99, "y" : 105,
					"image" : ROOT_PATH + "conqueror/potential_slot_bg.sub",
					"children" : ({"name" : "potential_skill_slot_1", "type" : "grid_table", "x" : 4, "y" : 4, "start_index" : 0, "x_count" : 1, "y_count" : 1, "x_step" : 32, "y_step" : 32},),
				},
				{"name" : "potential_gauge_bg_0", "type" : "image", "x" : 48, "y" : 81, "image" : ROOT_PATH + "conqueror/potential_slot_gauge_bg.sub"},
				{"name" : "potential_gauge_0", "type" : "expanded_image", "x" : 48, "y" : 81, "image" : ROOT_PATH + "conqueror/potential_slot_gauge.sub"},
				{"name" : "potential_gauge_bg_1", "type" : "image", "x" : 114, "y" : 81, "image" : ROOT_PATH + "conqueror/potential_slot_gauge_bg.sub"},
				{"name" : "potential_gauge_1", "type" : "expanded_image", "x" : 114, "y" : 81, "image" : ROOT_PATH + "conqueror/potential_slot_gauge.sub"},
			),
		},
	),
}
