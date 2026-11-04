# MT2009_PLUS_SKILL_COLOR_V1: Kolor umiejetnosci - the colour window (root uiskillcolor.py; the owner's package
# "SKILL_COLOR_SYSTEM by OSWAP (FULL)", its window rebuilt). Left: the character's skills that take a colour; right: the
# effect's five layers (their colours under the buttons), the picker (client-2.0.30/tools/skillcolor paints it from
# root skillcolorpick.py), the code "#RRGGBB". No import: every text is set here or by uiskillcolor.py.

WIDTH = 420
HEIGHT = 306
PICK = "d:/ymir work/ui/skillcolor/"
PUB = "d:/ymir work/ui/public/"
RX = 190	# the right column


def _Layer(i):
	return {
		"name" : "Layer%d" % i, "type" : "radio_button", "x" : RX + i * 43, "y" : 54,
		"text" : "%d" % (i + 1),
		"default_image" : PUB + "small_button_01.sub",
		"over_image" : PUB + "small_button_02.sub",
		"down_image" : PUB + "small_button_03.sub",
	}


def _LayerBar(i):
	return {
		"name" : "LayerColor%d" % i, "type" : "bar", "x" : RX + i * 43 + 2, "y" : 76, "width" : 39, "height" : 7,
		"color" : 0xff5a5a5a,
	}


window = {
	"name" : "SkillColorWindow",
	"style" : ("movable", "float",),

	"x" : 0,
	"y" : 0,

	"width" : WIDTH,
	"height" : HEIGHT,

	"children" :
	(
		{
			"name" : "Board",
			"type" : "board_with_titlebar",
			"style" : ("attach",),

			"x" : 0,
			"y" : 0,

			"width" : WIDTH,
			"height" : HEIGHT,

			"title" : "Kolor umiej\xeatno\x9cci",

			"children" :
			(
				## the skills
				{ "name" : "SkillTitle", "type" : "text", "x" : 16, "y" : 36, "text" : "Umiej\xeatno\x9cci", },
				{
					"name" : "SkillListBase", "type" : "bar", "x" : 14, "y" : 54, "width" : 152, "height" : 196,
					"color" : 0xa0000000,
					"children" :
					(
						{ "name" : "SkillList", "type" : "listbox", "x" : 2, "y" : 2, "width" : 148, "height" : 192,
						  "item_align" : 0, },
					),
				},
				{ "name" : "SkillScroll", "type" : "scrollbar", "x" : 166, "y" : 54, "size" : 196, },

				## the layers
				{ "name" : "LayerTitle", "type" : "text", "x" : RX, "y" : 36, "text" : "Warstwy efektu", },
				_Layer(0), _Layer(1), _Layer(2), _Layer(3), _Layer(4),
				_LayerBar(0), _LayerBar(1), _LayerBar(2), _LayerBar(3), _LayerBar(4),
				{
					"name" : "AllLayers", "type" : "toggle_button", "x" : RX, "y" : 88,
					"text" : "Wszystkie warstwy",
					"default_image" : PUB + "large_button_01.sub",
					"over_image" : PUB + "large_button_02.sub",
					"down_image" : PUB + "large_button_03.sub",
				},
				{
					"name" : "LayerOff", "type" : "button", "x" : RX + 94, "y" : 88,
					"text" : "Bez koloru",
					"default_image" : PUB + "middle_button_01.sub",
					"over_image" : PUB + "middle_button_02.sub",
					"down_image" : PUB + "middle_button_03.sub",
				},

				## the picker (180 x 120, skillcolorpick.ColorAt) and its mark
				{
					"name" : "Picker", "type" : "button", "x" : RX, "y" : 114,
					"default_image" : PICK + "color_picker.tga",
					"over_image" : PICK + "color_picker.tga",
					"down_image" : PICK + "color_picker.tga",
					"children" :
					(
						{ "name" : "PickerDot", "type" : "image", "x" : 0, "y" : 0, "image" : PICK + "color_picker_dot.tga", },
					),
				},

				## the code
				{ "name" : "HexTitle", "type" : "text", "x" : RX, "y" : 242, "text" : "Kod:", },
				{
					"name" : "HexSlot", "type" : "image", "x" : RX + 28, "y" : 240, "image" : PUB + "Parameter_Slot_03.sub",
					"children" :
					(
						{ "name" : "HexEdit", "type" : "editline", "x" : 4, "y" : 2, "width" : 82, "height" : 16,
						  "input_limit" : 7, },
					),
				},
				{
					"name" : "HexApply", "type" : "button", "x" : RX + 124, "y" : 238,
					"text" : "Ustaw",
					"default_image" : PUB + "middle_button_01.sub",
					"over_image" : PUB + "middle_button_02.sub",
					"down_image" : PUB + "middle_button_03.sub",
				},

				## the hint and the buttons
				{ "name" : "Hint", "type" : "text", "x" : 16, "y" : 256, "text" : "", },
				{
					"name" : "ApplyButton", "type" : "button", "x" : 14, "y" : 274,
					"text" : "Zastosuj",
					"default_image" : PUB + "large_button_01.sub",
					"over_image" : PUB + "large_button_02.sub",
					"down_image" : PUB + "large_button_03.sub",
				},
				{
					"name" : "DefaultButton", "type" : "button", "x" : 110, "y" : 274,
					"text" : "Domy\x9clne",
					"default_image" : PUB + "large_button_01.sub",
					"over_image" : PUB + "large_button_02.sub",
					"down_image" : PUB + "large_button_03.sub",
				},
				{
					"name" : "CloseButton", "type" : "button", "x" : WIDTH - 102, "y" : 274,
					"text" : "Zamknij",
					"default_image" : PUB + "large_button_01.sub",
					"over_image" : PUB + "large_button_02.sub",
					"down_image" : PUB + "large_button_03.sub",
				},
			),
		},
	),
}
