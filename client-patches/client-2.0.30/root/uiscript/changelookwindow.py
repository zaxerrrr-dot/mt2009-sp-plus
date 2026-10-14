# MT2009_PLUS_CHANGE_LOOK_V1: Transmutacja (uichangelook.py) - Owsap's ChangeLookWindow.py with our buttons. The
# background is the client's locale/common/ui/changelook/ingame_convert.tga; the left slot takes the look, the right
# one gives it (and is destroyed), the small one under them takes a ticket instead of the Yang.
import uiScriptLocale

BUTTON_ROOT = "d:/ymir work/ui/public/"

window = {
	"name" : "ChangeLookWindow",
	"x" : 0,
	"y" : 0,
	"style" : ("movable", "float",),
	"width" : 205,
	"height" : 275,
	"children" :
	(
		{
			"name" : "board",
			"type" : "board",
			"style" : ("attach",),
			"x" : 0,
			"y" : 0,
			"width" : 205,
			"height" : 275,
			"children" :
			(
				{
					"name" : "TitleBar",
					"type" : "titlebar",
					"style" : ("attach",),
					"x" : 6,
					"y" : 6,
					"width" : 190,
					"color" : "yellow",
					"children" :
					(
						{ "name" : "TitleName", "type" : "text", "x" : 95, "y" : 3, "text" : "", "text_horizontal_align" : "center" },
					),
				},
				{
					"name" : "ChangeLook_SlotImg",
					"type" : "image",
					"x" : 9,
					"y" : 35,
					"image" : "locale/common/ui/changelook/ingame_convert.tga",
					"children" :
					(
						{
							"name" : "ChangeLookSlot",
							"type" : "slot",
							"x" : 3,
							"y" : 3,
							"width" : 190,
							"height" : 200,
							"slot" : (
								{ "index" : 0, "x" : 26, "y" : 20, "width" : 31, "height" : 96 },
								{ "index" : 1, "x" : 125, "y" : 20, "width" : 31, "height" : 96 },
							),
						},
						{
							"name" : "ChangeLookSlot_PassYangItem",
							"type" : "slot",
							"x" : 78,
							"y" : 128,
							"width" : 31,
							"height" : 31,
							"slot" : (
								{ "index" : 0, "x" : 1, "y" : 1, "width" : 31, "height" : 31 },
							),
						},
					),
				},
				{
					"name" : "Cost",
					"type" : "text",
					"text" : "",
					"text_horizontal_align" : "center",
					"x" : 102,
					"y" : 215,
				},
				{
					"name" : "AcceptButton",
					"type" : "button",
					"x" : 20,
					"y" : 238,
					"text" : "Zatwierd\xbc",
					"default_image" : BUTTON_ROOT + "middle_button_01.sub",
					"over_image" : BUTTON_ROOT + "middle_button_02.sub",
					"down_image" : BUTTON_ROOT + "middle_button_03.sub",
				},
				{
					"name" : "CancelButton",
					"type" : "button",
					"x" : 120,
					"y" : 238,
					"text" : "Anuluj",
					"default_image" : BUTTON_ROOT + "middle_button_01.sub",
					"over_image" : BUTTON_ROOT + "middle_button_02.sub",
					"down_image" : BUTTON_ROOT + "middle_button_03.sub",
				},
				{
					"name" : "ChangeLookToolTipButton",
					"type" : "button",
					"x" : 160,
					"y" : 8,
					"default_image" : "d:/ymir work/ui/pattern/q_mark_01.tga",
					"over_image" : "d:/ymir work/ui/pattern/q_mark_02.tga",
					"down_image" : "d:/ymir work/ui/pattern/q_mark_01.tga",
				},
			),
		},
	),
}
