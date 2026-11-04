# MT2009_PLUS_GROWTH_PET_V1 - System Zwierzat Domowych: renaming a pet with Pergamin Nazwy Zwierzaka (uipetinfo.py
# PetNameChangeWindow), the official 26.1.11 uiscript/petnamechangewindow.py. No text here: uipetinfo.py sets it
# (the script sandbox imports no root module).

WINDOW_WIDTH = 176
WINDOW_HEIGHT = 184
BUTTON_ROOT = "mt2009_ui/newpet/"	# the official pattern/largeb_button_0x.tga (in the base root pack)

window = {
	"name" : "PetNameChangeWindow",
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
			"x" : 0, "y" : 0,
			"width" : WINDOW_WIDTH, "height" : WINDOW_HEIGHT,

			"children" :
			(
				{
					"name" : "PetNameChangeTitleBar",
					"type" : "titlebar",
					"style" : ("attach",),
					"x" : 0, "y" : 0,
					"width" : WINDOW_WIDTH - 2,
					"children" : ({"name" : "TitleName", "type" : "text", "x" : 0, "y" : 0, "text" : "", "all_align" : "center"},),
				},
				{"name" : "SlotBG", "type" : "expanded_image", "style" : ("attach",), "x" : 68, "y" : 34, "image" : "d:/ymir work/ui/pet/pet_incu_slot_001.tga"},
				{
					"name" : "PetItemSlot",
					"type" : "slot",
					"x" : 72, "y" : 38, "width" : 32, "height" : 32,
					"slot" : ({"index" : 0, "x" : 0, "y" : 0, "width" : 32, "height" : 32},),
				},
				{
					"name" : "NameChangeMoneyWindow", "type" : "window", "x" : 13, "y" : 132, "width" : 150, "height" : 14, "style" : ("attach",),
					"children" : ({"name" : "NameChangeMoney", "type" : "text", "x" : 0, "y" : 0, "text" : "", "r" : 1.0, "g" : 1.0, "b" : 1.0, "a" : 1.0, "all_align" : "center"},),
				},
				{
					"name" : "NameChangeButton",
					"type" : "button",
					"x" : 39, "y" : 151,
					"text" : "",
					"default_image" : BUTTON_ROOT + "largeb_button_01.tga",
					"over_image" : BUTTON_ROOT + "largeb_button_02.tga",
					"down_image" : BUTTON_ROOT + "largeb_button_03.tga",
				},
				{
					"name" : "PetNamingBG",
					"type" : "expanded_image",
					"style" : ("attach",),
					"x" : 12, "y" : 78,
					"image" : "d:/ymir work/ui/pet/pet_incu_001.tga",
					"children" :
					(
						{
							"name" : "pet_name",
							"type" : "editline",
							"x" : 11, "y" : 28,
							"width" : 129, "height" : 16,
							"input_limit" : 20,
						},
					),
				},
				{
					"name" : "PetNamingTitleWindow", "type" : "window", "x" : 22, "y" : 86, "width" : 130, "height" : 14, "style" : ("attach",),
					"children" : ({"name" : "PetNamingTitle", "type" : "text", "x" : 0, "y" : 0, "text" : "", "all_align" : "center"},),
				},
			),
		},
	),
}
