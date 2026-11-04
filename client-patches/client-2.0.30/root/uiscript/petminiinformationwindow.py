# MT2009_PLUS_GROWTH_PET_V1 - System Zwierzat Domowych: the small window bottom left while a pet is summoned
# (uipetinfo.py PetMiniInformationWindow), the official 26.1.11 uiscript/petminiinformationwindow.py (the champion
# version, 128 wide): the seal (a click opens the pet window; it flashes when the pet can evolve, is hungry or waits
# for item EXP), the 4 red + 1 blue EXP balls, the life bar and the 3 skills + 2 potential skills as small icons.
# Our exe scales neither a slot nor an ani_image: the small icons and the life bar are expanded images (scaled).

PET_UI_ROOT = "d:/ymir work/ui/pet/"
MINI_WINDOW_WIDTH = 128
MINI_WINDOW_HEIGHT = 44
BASE_SLOT_FILE = "d:/ymir work/ui/public/slot_base.sub"
PET_MINI_INFO_SLOT_FILE = PET_UI_ROOT + "mini_window/pet_slot_corver.sub"

EXP_GAGUE_INTERVAL = 6
EXP_GAGUE_SCALE = 0.8
EXP_IMG_WIDTH = 16 * EXP_GAGUE_SCALE

LIFE_TIME_SCALE_X = 0.736
LIFE_TIME_SCALE_Y = 0.636
SMALL = 0.5


def exp_ball(index, image):
	return {
		"name" : "pet_mini_EXPGauge_0%d" % (index + 1), "type" : "expanded_image", "style" : ("attach",),
		"x" : int(EXP_IMG_WIDTH * index + EXP_GAGUE_INTERVAL * index), "y" : 0,
		"x_scale" : EXP_GAGUE_SCALE, "y_scale" : EXP_GAGUE_SCALE,
		"image" : image,
	}


def small_slot(name, x):
	return {
		"name" : name + "_bg", "type" : "expanded_image", "style" : ("attach",),
		"x" : x, "y" : 25, "x_scale" : SMALL, "y_scale" : SMALL,
		"image" : BASE_SLOT_FILE,
		"children" : (
			{"name" : name, "type" : "expanded_image", "style" : ("attach",), "x" : 0, "y" : 0, "x_scale" : SMALL, "y_scale" : SMALL, "image" : BASE_SLOT_FILE},
		),
	}


window = {
	"name" : "PetMiniInformationWindow",
	"style" : ("movable", "float",),

	"x" : 10,
	"y" : SCREEN_HEIGHT - 150,

	"width" : MINI_WINDOW_WIDTH,
	"height" : MINI_WINDOW_HEIGHT,

	"children" :
	(
		{"name" : "main_bg", "type" : "expanded_image", "style" : ("attach",), "x" : 0, "y" : 0, "image" : PET_UI_ROOT + "mini_window/pet_mini_info_back.sub"},
		{
			"name" : "icon_base",
			"type" : "window",
			"style" : ("attach",),
			"x" : 0, "y" : 0,
			"width" : 35, "height" : MINI_WINDOW_HEIGHT,
			"children" :
			(
				{"name" : "main_slot_img", "type" : "expanded_image", "style" : ("attach",), "x" : 3, "y" : 3, "image" : PET_MINI_INFO_SLOT_FILE},
				{
					"name" : "pet_icon_slot",
					"type" : "slot",
					"x" : 3, "y" : 6,
					"width" : 35, "height" : MINI_WINDOW_HEIGHT,
					"slot" : ({"index" : 0, "x" : 0, "y" : 0, "width" : 32, "height" : 32},),
				},
				{
					"name" : "pet_icon_slot_ani_img",
					"type" : "ani_image",
					"style" : ("attach",),
					"x" : 3, "y" : 3,
					"delay" : 6,
					"images" :
					(
						PET_UI_ROOT + "mini_window/main_slot_effect/main_slot_effect1.sub",
						PET_UI_ROOT + "mini_window/main_slot_effect/main_slot_effect2.sub",
						PET_UI_ROOT + "mini_window/main_slot_effect/main_slot_effect3.sub",
						PET_UI_ROOT + "mini_window/main_slot_effect/main_slot_effect4.sub",
						PET_UI_ROOT + "mini_window/main_slot_effect/main_slot_effect5.sub",
						PET_UI_ROOT + "mini_window/main_slot_effect/main_slot_effect6.sub",
						PET_UI_ROOT + "mini_window/main_slot_effect/main_slot_effect6.sub",
						PET_UI_ROOT + "mini_window/main_slot_effect/main_slot_effect6.sub",
						PET_UI_ROOT + "mini_window/main_slot_effect/main_slot_effect5.sub",
						PET_UI_ROOT + "mini_window/main_slot_effect/main_slot_effect4.sub",
						PET_UI_ROOT + "mini_window/main_slot_effect/main_slot_effect3.sub",
						PET_UI_ROOT + "mini_window/main_slot_effect/main_slot_effect2.sub",
						PET_UI_ROOT + "mini_window/main_slot_effect/main_slot_effect1.sub",
					),
				},
			),
		},
		## the life bar
		{
			"name" : "LifeGaugeWindow", "type" : "window", "x" : 36, "y" : 17, "width" : 88, "height" : 8, "style" : ("attach",),
			"children" :
			(
				{"name" : "gauge_left", "type" : "expanded_image", "style" : ("attach",), "x" : 0, "y" : 0, "image" : "d:/ymir work/ui/pattern/gauge_slot_left.tga"},
				{"name" : "gauge_right", "type" : "expanded_image", "style" : ("attach",), "x" : 72, "y" : 0, "image" : "d:/ymir work/ui/pattern/gauge_slot_right.tga"},
				{"name" : "gauge_center", "type" : "expanded_image", "style" : ("attach",), "x" : 10, "y" : 0, "x_scale" : 4.1875, "y_scale" : 1.0, "image" : "d:/ymir work/ui/pattern/gauge_slot_center.tga"},
				{"name" : "LifeGauge", "type" : "expanded_image", "style" : ("attach",), "x" : 10, "y" : 0, "x_scale" : LIFE_TIME_SCALE_X, "y_scale" : LIFE_TIME_SCALE_Y, "image" : "d:/ymir work/ui/pattern/hpgauge/01.tga"},
			),
		},
		## the skills (3) and the potential skills (2), 16 x 16
		small_slot("mini_skill_slot0", 36),
		small_slot("mini_skill_slot1", 54),
		small_slot("mini_skill_slot2", 72),
		small_slot("mini_potential_skill_slot_0", 90),
		small_slot("mini_potential_skill_slot_1", 108),
		## the EXP balls: 4 red (mob EXP, 90 %) + 1 blue (item EXP, 10 %)
		{
			"name" : "pet_mini_info_exp_gauge_board",
			"type" : "window",
			"style" : ("ltr",),
			"x" : 36, "y" : 3,
			"width" : 89, "height" : 13,
			"children" :
			(
				exp_ball(0, "d:/ymir work/ui/pet/exp_gauge/exp_on.sub"),
				exp_ball(1, "d:/ymir work/ui/pet/exp_gauge/exp_on.sub"),
				exp_ball(2, "d:/ymir work/ui/pet/exp_gauge/exp_on.sub"),
				exp_ball(3, "d:/ymir work/ui/pet/exp_gauge/exp_on.sub"),
				exp_ball(4, "d:/ymir work/ui/pet/exp_gauge/item_exp_on.sub"),
			),
		},
	),
}
