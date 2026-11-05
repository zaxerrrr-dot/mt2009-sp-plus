# MT2009_PLUS_GROWTH_PET_V1 - System Zwierzat Domowych: the pet window (uipetinfo.py PetInformationWindow), the
# official 26.1.11 uiscript/petinformationwindow.py (the champion version: normal / champion / potential buttons) on
# our client: no text here - uipetinfo.py sets every one from petlocale.py (the script sandbox imports no root
# module), the life gauge an expanded image (our exe's ani_image cannot be
# scaled), the tab buttons with tooltips (the official tab pictures are icons only). Three pages: Informacje,
# Zmiana typu (Zaczaruj zwierzaka), Wskrzeszanie (Boska Odzywka).
# MT2009_PLUS_PET_WINDOW_LAYOUT_V2: the mode buttons and the tab plates are our mt2009_ui/pet/ copies of the official
# pictures (tools/pety/make_pet_ui_art.py) - the emblem moved left / taken off so their text is not drawn over it; the
# life gauge fits the background's frame (36..188); the potential slots sit in the background's octagons like the
# skill slots (no square slot picture over them).

PET_UI_ROOT = "d:/ymir work/ui/pet/"
OUR_UI_ROOT = "mt2009_ui/pet/"
BASE_SLOT_FILE = "d:/ymir work/ui/public/Slot_Base.sub"
PET_UI_BG_IMAGE = "d:/ymir work/ui/pet/res/pet_ui_bg.tga"
PET_PRIMIUM_FEEFSTUFF_UI_BG_IMAGE = "d:/ymir work/ui/pet/res/pet_ui_bg3.tga"
PET_ATTR_CHANGE_UI_BG_IMAGE = "d:/ymir work/ui/pet/res/pet_ui_bg2.tga"

PET_UI_ITEM_SLOT_Y = 49 - 9
PET_UI_BG_WIDTH = 352
PET_UI_BG_HEIGHT = 456	# 408 + the tab bar (48)
PET_PAGE_UI_BG_WIDTH = 352
PET_PAGE_UI_BG_HEIGHT = 408

LONG_LABEL_WIDTH = 266
LONG_LABEL_HEIGHT = 19
SHORT_LABLE_WIDTH = 90
SHORT_LABLE_HEIGHT = 20
MIDDLE_LABLE_WIDTH = 168
MIDDLE_LABLE_HEIGHT = 20

EXP_GAGUE_INTERVAL = 2
EXP_IMG_WIDTH = 16
EXP_IMG_HEIGHT = 16

LIFE_GAUGE_IMAGE = "d:/ymir work/ui/pattern/hpgauge/01.tga"	# 95 x 11
LIFE_GAUGE_WIDTH = 153	# the frame in pet_ui_bg.tga: x 35..189, y 226..238
LIFE_GAUGE_SCALE_X = float(LIFE_GAUGE_WIDTH) / 95.0

GOLD_COLOR = 0xFFFEE3AE
WHITE_COLOR = 0xFFFFFFFF

PET_UI_TAB_X = 13
PET_UI_TAB_Y = 8
PET_UI_TAB_WIDTH = 77
PET_UI_TAB_HEIGHT = 30


def label(name, x, y, width, height, text, color=WHITE_COLOR):
	return {
		"name" : name + "Window", "type" : "window", "x" : x, "y" : y, "width" : width, "height" : height, "style" : ("attach",),
		"children" : (
			{"name" : name, "type" : "text", "x" : 0, "y" : 0, "text" : text, "color" : color, "all_align" : "center"},
		),
	}


def exp_ball(name, index, image):
	return {
		"name" : name, "type" : "expanded_image",
		"x" : (EXP_IMG_WIDTH + EXP_GAGUE_INTERVAL) * index, "y" : 0,
		"image" : image,
	}


def one_slot_grid(name, x, y):
	return {
		"name" : name, "type" : "grid_table",
		"x" : x, "y" : y, "start_index" : 0, "x_count" : 1, "y_count" : 1, "x_step" : 32, "y_step" : 32,
	}


def feed_button(name, y, text):
	return {
		"name" : name, "type" : "toggle_button",
		"x" : 207, "y" : y,
		"default_image" : PET_UI_ROOT + "feed_button/feed_button_default.sub",
		"over_image" : PET_UI_ROOT + "feed_button/feed_button_over.sub",
		"down_image" : PET_UI_ROOT + "feed_button/feed_button_down.sub",
		"text" : text, "text_color" : GOLD_COLOR,
	}


def page_button(name, x, image, text):
	return {
		"name" : name, "type" : "button",
		"x" : x, "y" : 109,
		"default_image" : OUR_UI_ROOT + image + "_bt_default.tga",
		"over_image" : OUR_UI_ROOT + image + "_bt_over.tga",
		"down_image" : OUR_UI_ROOT + image + "_bt_down.tga",
		"text" : text, "text_color" : GOLD_COLOR,
	}


window = {
	"name" : "PetInformationWindow",
	"style" : ("movable", "float",),

	"x" : SCREEN_WIDTH - 176 - 200 - 146 - 145,
	"y" : SCREEN_HEIGHT - 37 - 565,

	"width" : PET_UI_BG_WIDTH,
	"height" : PET_UI_BG_HEIGHT,

	"children" :
	[
		{
			"name" : "board",
			"type" : "window",
			"style" : ("attach",),
			"x" : 0, "y" : 0,
			"width" : PET_UI_BG_WIDTH, "height" : PET_UI_BG_HEIGHT,

			"children" :
			[
				## the information page
				{
					"name" : "PetInfo_Page",
					"type" : "window",
					"style" : ("attach",),
					"x" : 0, "y" : 0,
					"width" : PET_PAGE_UI_BG_WIDTH, "height" : PET_PAGE_UI_BG_HEIGHT,

					"children" :
					[
						{"name" : "PetInfoUIBG", "type" : "expanded_image", "style" : ("attach",), "x" : 0, "y" : 0, "image" : PET_UI_BG_IMAGE},

						## the summoned pet's seal
						{
							"name" : "UpBringing_Pet_Slot", "type" : "slot",
							"x" : 25, "y" : PET_UI_ITEM_SLOT_Y, "width" : 32, "height" : 32,
							"slot" : ({"index" : 0, "x" : 0, "y" : 0, "width" : 32, "height" : 32},),
						},

						## stage (and type), name
						{
							"name" : "EvolNameWindow", "type" : "window", "x" : 65, "y" : 47, "width" : LONG_LABEL_WIDTH, "height" : LONG_LABEL_HEIGHT, "style" : ("attach",),
							"children" : ({"name" : "EvolName", "type" : "text", "x" : 0, "y" : 0, "text" : "", "r" : 1.0, "g" : 0.85, "b" : 0.3, "a" : 1.0, "all_align" : "center"},),
						},
						{
							"name" : "NameWindow", "type" : "window", "x" : 65, "y" : 72, "width" : LONG_LABEL_WIDTH, "height" : LONG_LABEL_HEIGHT, "style" : ("attach",),
							"children" : ({"name" : "PetName", "type" : "text", "x" : 0, "y" : 0, "text" : "", "r" : 0.83, "g" : 0.77, "b" : 0.73, "a" : 1.0, "all_align" : "center"},),
						},

						## normal / champion / potential
						page_button("NormalInfoButton", 14, "normal", ""),
						page_button("ConquerorInfoButton", 122, "conqueror", ""),
						page_button("PotentialButton", 230, "potential", ""),

						label("LevelTitle", 28, 135, SHORT_LABLE_WIDTH, SHORT_LABLE_HEIGHT, "", GOLD_COLOR),
						label("LevelValue", 28, 158, SHORT_LABLE_WIDTH, SHORT_LABLE_HEIGHT, ""),
						label("ExpTitle", 131, 135, SHORT_LABLE_WIDTH, SHORT_LABLE_HEIGHT, "", GOLD_COLOR),
						{
							"name" : "UpBringing_Pet_EXP_Gauge_Board",
							"type" : "window",
							"style" : ("ltr",),
							"x" : 131, "y" : 160,
							"width" : EXP_IMG_WIDTH * 5 + EXP_GAGUE_INTERVAL * 4, "height" : EXP_IMG_HEIGHT,
							"children" : (
								exp_ball("UpBringing_Pet_EXPGauge_01", 0, "d:/ymir work/ui/pet/exp_gauge/exp_on.sub"),
								exp_ball("UpBringing_Pet_EXPGauge_02", 1, "d:/ymir work/ui/pet/exp_gauge/exp_on.sub"),
								exp_ball("UpBringing_Pet_EXPGauge_03", 2, "d:/ymir work/ui/pet/exp_gauge/exp_on.sub"),
								exp_ball("UpBringing_Pet_EXPGauge_04", 3, "d:/ymir work/ui/pet/exp_gauge/exp_on.sub"),
								exp_ball("UpBringing_Pet_EXPGauge_05", 4, "d:/ymir work/ui/pet/exp_gauge/item_exp_on.sub"),
							),
						},
						label("AgeTitle", 232, 135, SHORT_LABLE_WIDTH, SHORT_LABLE_HEIGHT, "", GOLD_COLOR),
						label("AgeValue", 232, 158, SHORT_LABLE_WIDTH, SHORT_LABLE_HEIGHT, ""),

						label("LifeTitle", 28, 180, 168, SHORT_LABLE_HEIGHT, "", GOLD_COLOR),
						{
							"name" : "LifeValueWindow", "type" : "window", "x" : 28, "y" : 203, "width" : 168, "height" : 20, "style" : ("attach",),
							"children" : ({"name" : "LifeTextValue", "type" : "text", "x" : 0, "y" : 2, "text" : "", "color" : WHITE_COLOR, "all_align" : "center"},),
						},
						{
							"name" : "LifeGaugeWindow", "type" : "window", "x" : 36, "y" : 227, "width" : LIFE_GAUGE_WIDTH, "height" : 11, "style" : ("attach",),
							"children" : (
								{"name" : "LifeGauge", "type" : "expanded_image", "x" : 0, "y" : 0, "x_scale" : LIFE_GAUGE_SCALE_X, "y_scale" : 1.0, "image" : LIFE_GAUGE_IMAGE},
							),
						},

						feed_button("FeedLifeTimeButton", 184, ""),
						feed_button("FeedEvolButton", 205, ""),
						feed_button("FeedExpButton", 226, ""),

						{
							"name" : "AbilitiesWindow", "type" : "window", "x" : 43, "y" : 261, "width" : LONG_LABEL_WIDTH, "height" : LONG_LABEL_HEIGHT, "style" : ("attach",),
							"children" : ({"name" : "AbilitiesName", "type" : "text", "x" : 0, "y" : 0, "text" : "", "r" : 1.0, "g" : 0.85, "b" : 0.3, "a" : 1.0, "all_align" : "center"},),
						},
						label("HpTitle", 20, 284, MIDDLE_LABLE_WIDTH, MIDDLE_LABLE_HEIGHT, "", GOLD_COLOR),
						label("HpValue", 20 + MIDDLE_LABLE_WIDTH, 284, MIDDLE_LABLE_WIDTH, MIDDLE_LABLE_HEIGHT, ""),
						label("DefTitle", 20, 306, MIDDLE_LABLE_WIDTH, MIDDLE_LABLE_HEIGHT, "", GOLD_COLOR),
						label("DefValue", 20 + MIDDLE_LABLE_WIDTH, 306, MIDDLE_LABLE_WIDTH, MIDDLE_LABLE_HEIGHT, ""),
						label("SpTitle", 20, 328, MIDDLE_LABLE_WIDTH, MIDDLE_LABLE_HEIGHT, "", GOLD_COLOR),
						label("SpValue", 20 + MIDDLE_LABLE_WIDTH, 328, MIDDLE_LABLE_WIDTH, MIDDLE_LABLE_HEIGHT, ""),

						## skills: three slots, then the two potential skills
						{"name" : "PetSkillMenuIcon", "type" : "image", "x" : 20, "y" : 362, "image" : PET_UI_ROOT + "conqueror/skill_menu_icon_bg.sub"},
						one_slot_grid("PetSkillSlot0", 65, 365),
						one_slot_grid("PetSkillSlot1", 101, 365),
						one_slot_grid("PetSkillSlot2", 137, 365),
						{"name" : "PetPotentialMenuIcon", "type" : "image", "x" : 180, "y" : 362, "image" : PET_UI_ROOT + "conqueror/potential_menu_icon_bg.sub"},
						one_slot_grid("potential_pet_slot_0", 225, 365),
						one_slot_grid("potential_pet_slot_1", 261, 365),
					],
				},
			],
		},
	],
}

## the tab bar under the pages
window["children"] = window["children"] + [
	{
		"name" : "TabControl",
		"type" : "window",
		"x" : 0, "y" : PET_UI_BG_HEIGHT - 40 - 8,
		"width" : PET_UI_BG_WIDTH, "height" : 48,
		"children" :
		[
			{"name" : "Tab_01", "type" : "image", "x" : 0, "y" : 0, "image" : OUR_UI_ROOT + "tab_1.tga"},
			{"name" : "Tab_02", "type" : "image", "x" : 0, "y" : 0, "image" : OUR_UI_ROOT + "tab_2.tga"},
			{"name" : "Tab_03", "type" : "image", "x" : 0, "y" : 0, "image" : OUR_UI_ROOT + "tab_3.tga"},
			{"name" : "Tab_Button_01", "type" : "button", "x" : PET_UI_TAB_X, "y" : PET_UI_TAB_Y, "width" : PET_UI_TAB_WIDTH, "height" : PET_UI_TAB_HEIGHT, "tooltip_text" : ""},
			{"name" : "Tab_Button_02", "type" : "button", "x" : PET_UI_TAB_X + 94, "y" : PET_UI_TAB_Y, "width" : PET_UI_TAB_WIDTH, "height" : PET_UI_TAB_HEIGHT, "tooltip_text" : ""},
			{"name" : "Tab_Button_03", "type" : "button", "x" : PET_UI_TAB_X + 94 * 2, "y" : PET_UI_TAB_Y, "width" : PET_UI_TAB_WIDTH, "height" : PET_UI_TAB_HEIGHT, "tooltip_text" : ""},
		],
	},
]

## "Sfera losu": shows the pet's type (uses a Sfera Losu Zwierzaka)
window["children"] = window["children"] + [
	{
		"name" : "DetermineButton",
		"type" : "button",
		"x" : 21, "y" : 79,
		"width" : 38, "height" : 26,
		"default_image" : PET_UI_ROOT + "determine_button/determine_button_default.sub",
		"over_image" : PET_UI_ROOT + "determine_button/determine_button_over.sub",
		"down_image" : PET_UI_ROOT + "determine_button/determine_button_down.sub",
		"tooltip_text" : "",
	},
]

## the type change page (Zaczaruj zwierzaka)
window["children"] = window["children"] + [
	{
		"name" : "PetAttrChange_Page",
		"type" : "window",
		"style" : ("attach",),
		"x" : 0, "y" : 0,
		"width" : PET_PAGE_UI_BG_WIDTH, "height" : PET_PAGE_UI_BG_HEIGHT,
		"children" :
		[
			{"name" : "PetAttrChangeUIBG", "type" : "expanded_image", "style" : ("attach",), "x" : 0, "y" : 0, "image" : PET_ATTR_CHANGE_UI_BG_IMAGE},
			label("PetAttrChangeTitle", 102, 41, 150, 11, "", 0xFFD9D9D9),
			{
				"name" : "Change_Pet_Slot", "type" : "slot",
				"x" : 160, "y" : 67, "width" : 32, "height" : 173,
				"slot" : (
					{"index" : 0, "x" : 0, "y" : 0, "width" : 32, "height" : 32},		# the seal
					{"index" : 1, "x" : 0, "y" : 69, "width" : 32, "height" : 32},		# Zaczaruj zwierzaka
					{"index" : 2, "x" : 0, "y" : 140, "width" : 32, "height" : 32},	# the result
				),
			},
			label("ChangePetText", 121, 112, 113, 11, ""),
			label("AttrChangeItemText", 103, 181, 150, 11, ""),
			label("AttrChangeResultText", 136, 254, 83, 11, ""),
			label("PetDetermineInfoTitle", 102, 292, 150, 11, "", GOLD_COLOR),
			label("PetDetermineInfoText", 20, 333, 312, 11, " "),
			{
				"name" : "Pet_Change_Button", "type" : "button",
				"x" : 25, "y" : 379,
				"default_image" : PET_UI_ROOT + "feed_button/feed_button_default.sub",
				"over_image" : PET_UI_ROOT + "feed_button/feed_button_over.sub",
				"down_image" : PET_UI_ROOT + "feed_button/feed_button_down.sub",
				"text" : "", "text_color" : GOLD_COLOR,
			},
			{
				"name" : "Pet_OK_Button", "type" : "button",
				"x" : 205, "y" : 379,
				"default_image" : PET_UI_ROOT + "feed_button/feed_button_default.sub",
				"over_image" : PET_UI_ROOT + "feed_button/feed_button_over.sub",
				"down_image" : PET_UI_ROOT + "feed_button/feed_button_down.sub",
				"text" : "", "text_color" : GOLD_COLOR,
			},
		],
	},
]

## the revive page (Boska Odzywka)
window["children"] = window["children"] + [
	{
		"name" : "PetPrimiumFeefstuff_Page",
		"type" : "window",
		"style" : ("attach",),
		"x" : 0, "y" : 0,
		"width" : PET_PAGE_UI_BG_WIDTH, "height" : PET_PAGE_UI_BG_HEIGHT,
		"children" :
		[
			{"name" : "PetPrimiumFeefstuffUIBG", "type" : "expanded_image", "style" : ("attach",), "x" : 0, "y" : 0, "image" : PET_PRIMIUM_FEEFSTUFF_UI_BG_IMAGE},
			label("PetReviveTitleText", 17, 36, 317, 21, ""),
			label("PetReviveText", 35, 59, 135, 21, "", 0xFFCCC2B3),
			label("PetReviveAgeText", 53, 132, 100, 18, ""),
			label("PetReviveAgeNumberText", 53, 148, 100, 18, ""),
			label("PetReviveResultText", 181, 59, 135, 21, "", 0xFFCCC2B3),
			label("PetReviveResultAgeText", 199, 132, 100, 18, ""),
			label("PetReviveResultAgeNumerText", 199, 148, 100, 18, ""),
			label("PetReviveMaterialText", 35, 175, 135, 21, "", 0xFFCCC2B3),
			label("PetReviveMaterialCountText", 219, 177, 57, 17, ""),
			{
				"name" : "PetReviveSlot", "type" : "slot",
				"x" : 87, "y" : 91, "width" : 32, "height" : 32, "image" : BASE_SLOT_FILE,
				"slot" : ({"index" : 0, "x" : 0, "y" : 0, "width" : 32, "height" : 32},),
			},
			{
				"name" : "PetReviveResultSlot", "type" : "slot",
				"x" : 233, "y" : 91, "width" : 32, "height" : 32, "image" : BASE_SLOT_FILE,
				"slot" : ({"index" : 0, "x" : 0, "y" : 0, "width" : 32, "height" : 32},),
			},
			{
				"name" : "PetReviveMaterialSlot", "type" : "slot",
				"x" : 56, "y" : 206, "width" : 32 * 5 + 20 * 4, "height" : 32 * 2, "image" : BASE_SLOT_FILE,
				"slot" : (
					{"index" : 0, "x" : 0, "y" : 0, "width" : 32, "height" : 32},
					{"index" : 1, "x" : 52, "y" : 0, "width" : 32, "height" : 32},
					{"index" : 2, "x" : 104, "y" : 0, "width" : 32, "height" : 32},
					{"index" : 3, "x" : 156, "y" : 0, "width" : 32, "height" : 32},
					{"index" : 4, "x" : 208, "y" : 0, "width" : 32, "height" : 32},
					{"index" : 5, "x" : 0, "y" : 32, "width" : 32, "height" : 32},
					{"index" : 6, "x" : 52, "y" : 32, "width" : 32, "height" : 32},
					{"index" : 7, "x" : 104, "y" : 32, "width" : 32, "height" : 32},
					{"index" : 8, "x" : 156, "y" : 32, "width" : 32, "height" : 32},
					{"index" : 9, "x" : 208, "y" : 32, "width" : 32, "height" : 32},
				),
			},
			## the rules, 4 lines a page (uipetinfo.py fills it)
			{"name" : "desc_window", "type" : "window", "x" : 17, "y" : 282, "width" : 317, "height" : 75},
			{
				"name" : "PetReviveDescPrevButton", "type" : "button", "x" : 277, "y" : 359,
				"default_image" : "d:/ymir work/ui/public/public_intro_btn/prev_btn_01.sub",
				"over_image" : "d:/ymir work/ui/public/public_intro_btn/prev_btn_02.sub",
				"down_image" : "d:/ymir work/ui/public/public_intro_btn/prev_btn_01.sub",
			},
			{
				"name" : "PetReviveDescNextButton", "type" : "button", "x" : 308, "y" : 359,
				"default_image" : "d:/ymir work/ui/public/public_intro_btn/next_btn_01.sub",
				"over_image" : "d:/ymir work/ui/public/public_intro_btn/next_btn_02.sub",
				"down_image" : "d:/ymir work/ui/public/public_intro_btn/next_btn_01.sub",
			},
			{
				"name" : "PetReviveButton", "type" : "button",
				"x" : 56, "y" : 383,
				"text" : "",
				"default_image" : "d:/ymir work/ui/public/large_button_01.sub",
				"over_image" : "d:/ymir work/ui/public/large_button_02.sub",
				"down_image" : "d:/ymir work/ui/public/large_button_03.sub",
			},
			{
				"name" : "PetReviveCancelButton", "type" : "button",
				"x" : 205, "y" : 383,
				"text" : "",
				"default_image" : "d:/ymir work/ui/public/large_button_01.sub",
				"over_image" : "d:/ymir work/ui/public/large_button_02.sub",
				"down_image" : "d:/ymir work/ui/public/large_button_03.sub",
			},
		],
	},
]

## the title and the close button over every page
window["children"] = window["children"] + [
	{
		"name" : "PetWindowTitle", "type" : "window", "x" : 10, "y" : 10, "width" : PET_UI_BG_WIDTH - 10 - 15, "height" : 15, "style" : ("attach",),
		"children" : ({"name" : "TitleName", "type" : "text", "x" : 0, "y" : 0, "text" : "", "all_align" : "center"},),
	},
	{
		"name" : "PetWindowCloseButton",
		"type" : "button",
		"x" : PET_UI_BG_WIDTH - 10 - 15, "y" : 10,
		"tooltip_text" : "",
		"default_image" : "d:/ymir work/ui/public/close_button_01.sub",
		"over_image" : "d:/ymir work/ui/public/close_button_02.sub",
		"down_image" : "d:/ymir work/ui/public/close_button_03.sub",
	},
]
