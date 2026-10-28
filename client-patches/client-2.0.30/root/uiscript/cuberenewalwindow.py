# MT2009_PLUS_CUBE_RENEWAL_V1: the crafting window as on the global servers - GF 26.1.11's uiscript/cuberenewalwindow.py
# (the list of recipes by category, the result and its materials on cube_slot_bg, the quantity, the chance-raising
# slot, Gaya and Yang, OK / Cancel) with three changes of ours: a search line over the list (everything below it 26
# lower), a sixth material column (some of our recipes take six: mt2009_cube_slot_col.sub / mt2009_cube_slot_end.sub,
# crops of cube_slot_bg, the window 46 wider) and no uiScriptLocale - uicuberenewal.py writes the Polish texts.
# The graphics (d:/ymir work/ui/making_001.dds, d:/ymir work/ui/game/cube/*.sub, GF's) travel in the root pack
# (client-2.0.30/atlas); gemshop_001.dds (the Gaya icon) is already there for the Gaya shop.
ROOT_PATH = "d:/ymir work/ui/game/cube/"
PUBLIC_PATH = "d:/ymir work/ui/public/"
PATTERN_PATH = "d:/ymir work/ui/pattern/"

WINDOW_WIDTH = 382
WINDOW_HEIGHT = 514
D = 26	# the search line

LIST_WINDOW_WIDTH = 362
SEARCH_WIDTH = 196
LIST_WINDOW_HEIGHT = 252
LIST_WINDOW_PATTERN_X_COUNT = (LIST_WINDOW_WIDTH - 32) / 16.0
LIST_WINDOW_PATTERN_Y_COUNT = (LIST_WINDOW_HEIGHT - 32) / 16.0

def _QtyText(index, x):
	return {
		"name" : "material_qty_window_%d" % index,
		"type" : "window",
		"x" : x,
		"y" : 115,
		"width" : 45,
		"height" : 16,
		"children" :
		(
			{
				"name" : "material_qty_text_%d" % index,
				"type" : "text",
				"x" : 0, "y" : 0,
				"horizontal_align" : "center",
				"text_horizontal_align" : "center",
				"vertical_align" : "center",
				"text_vertical_align" : "center",
				"text" : "",
			},
		),
	}

window = {
	"name" : "CubeRenewalWindow",
	"style" : ("movable", "float", ),

	"x" : 0,
	"y" : 0,

	"width" : WINDOW_WIDTH,
	"height" : WINDOW_HEIGHT,

	"children" :
	(
		{
			"name" : "board",
			"type" : "board_with_titlebar",
			"style" : ("attach", ),

			"x" : 0,
			"y" : 0,

			"width" : WINDOW_WIDTH,
			"height" : WINDOW_HEIGHT,
			"title" : "",

			"children" :
			(
				## Search
				{
					"name" : "search_bar",
					"type" : "slotbar",
					"x" : 10,
					"y" : 34,
					"width" : SEARCH_WIDTH,
					"height" : 18,
					"children" :
					(
						{
							"name" : "search_edit",
							"type" : "editline",
							"x" : 4,
							"y" : 3,
							"width" : SEARCH_WIDTH - 8,
							"height" : 15,
							"input_limit" : 24,
						},
					),
				},

				## the chosen recipe's chance and the last attempt's result, right of the search line
				{
					"name" : "info_text",
					"type" : "text",
					"x" : 10,
					"y" : 36,
					"horizontal_align" : "right",
					"text_horizontal_align" : "right",
					"text" : "",
				},

				## ItemList
				{
					"name" : "item_list_board",
					"type" : "window",
					"style" : ("ltr", "attach", ),

					"x" : 10,
					"y" : 32 + D,

					"width" : LIST_WINDOW_WIDTH,
					"height" : LIST_WINDOW_HEIGHT,

					"children" :
					(
						{ "name" : "ListWindowLeftTop", "type" : "image", "style" : ("ltr",), "x" : 0, "y" : 0, "image" : PATTERN_PATH + "border_A_left_top.tga", },
						{ "name" : "ListWindowRightTop", "type" : "image", "style" : ("ltr",), "x" : LIST_WINDOW_WIDTH - 16, "y" : 0, "image" : PATTERN_PATH + "border_A_right_top.tga", },
						{ "name" : "ListWindowLeftBottom", "type" : "image", "style" : ("ltr",), "x" : 0, "y" : LIST_WINDOW_HEIGHT - 16, "image" : PATTERN_PATH + "border_A_left_bottom.tga", },
						{ "name" : "ListWindowRightBottom", "type" : "image", "style" : ("ltr",), "x" : LIST_WINDOW_WIDTH - 16, "y" : LIST_WINDOW_HEIGHT - 16, "image" : PATTERN_PATH + "border_A_right_bottom.tga", },
						{ "name" : "ListWindowTopCenterImg", "type" : "expanded_image", "style" : ("ltr",), "x" : 16, "y" : 0, "image" : PATTERN_PATH + "border_A_top.tga", "rect" : (0.0, 0.0, LIST_WINDOW_PATTERN_X_COUNT, 0), },
						{ "name" : "ListWindowLeftCenterImg", "type" : "expanded_image", "style" : ("ltr",), "x" : 0, "y" : 16, "image" : PATTERN_PATH + "border_A_left.tga", "rect" : (0.0, 0.0, 0, LIST_WINDOW_PATTERN_Y_COUNT), },
						{ "name" : "ListWindowRightCenterImg", "type" : "expanded_image", "style" : ("ltr",), "x" : LIST_WINDOW_WIDTH - 16, "y" : 16, "image" : PATTERN_PATH + "border_A_right.tga", "rect" : (0.0, 0.0, 0, LIST_WINDOW_PATTERN_Y_COUNT), },
						{ "name" : "ListWindowBottomCenterImg", "type" : "expanded_image", "style" : ("ltr",), "x" : 16, "y" : LIST_WINDOW_HEIGHT - 16, "image" : PATTERN_PATH + "border_A_bottom.tga", "rect" : (0.0, 0.0, LIST_WINDOW_PATTERN_X_COUNT, 0), },
						{ "name" : "ListWindowCenterImg", "type" : "expanded_image", "style" : ("ltr",), "x" : 16, "y" : 16, "image" : PATTERN_PATH + "border_A_center.tga", "rect" : (0.0, 0.0, LIST_WINDOW_PATTERN_X_COUNT, LIST_WINDOW_PATTERN_Y_COUNT), },
						{
							"name" : "item_list_window",
							"type" : "window",
							"style" : ("ltr",),
							"x" : 3,
							"y" : 3,
							"width" : LIST_WINDOW_WIDTH - 6,
							"height" : LIST_WINDOW_HEIGHT - 10,
						},
					),
				},
				{
					"name" : "cube_list_scroll_bar",
					"type" : "scrollbar",
					"x" : 26,
					"y" : 34 + D,
					"size" : 248,
					"horizontal_align" : "right",
				},

				## the sixth material column and the right edge, beside cube_slot_bg
				{
					"name" : "item_slot_col",
					"type" : "image",
					"style" : ("ltr", ),
					"x" : 10 + 309,
					"y" : 283 + D,
					"image" : ROOT_PATH + "mt2009_cube_slot_col.sub",
				},
				{
					"name" : "item_slot_end",
					"type" : "image",
					"style" : ("ltr", ),
					"x" : 10 + 355,
					"y" : 283 + D,
					"image" : ROOT_PATH + "mt2009_cube_slot_end.sub",
				},

				## ItemSlot
				{
					"name" : "item_slot",
					"type" : "image",
					"style" : ("ltr", "attach"),
					"x" : 10,
					"y" : 283 + D,
					"image" : ROOT_PATH + "cube_slot_bg.sub",
					"children" :
					(
						{
							"name" : "result_qty_window",
							"type" : "window",
							"x" : 24,
							"y" : 115,
							"width" : 36,
							"height" : 16,
							"children" :
							(
								{
									"name" : "result_qty",
									"type" : "editline",
									"x" : 3, "y" : 3,
									"width" : 36,
									"height" : 16,
									"input_limit" : 3,
									"only_number" : 1,
									"text" : "",
								},
							)
						},
						{
							"name" : "qty_sub_button",
							"type" : "button",
							"x" : 7,
							"y" : 117,
							"default_image" : ROOT_PATH + "cube_qty_sub_default.sub",
							"over_image" : ROOT_PATH + "cube_qty_sub_over.sub",
							"down_image" : ROOT_PATH + "cube_qty_sub_down.sub",
						},
						{
							"name" : "qty_add_button",
							"type" : "button",
							"x" : 62,
							"y" : 117,
							"default_image" : ROOT_PATH + "cube_qty_add_default.sub",
							"over_image" : ROOT_PATH + "cube_qty_add_over.sub",
							"down_image" : ROOT_PATH + "cube_qty_add_down.sub",
						},
						_QtyText(1, 80),
						_QtyText(2, 126),
						_QtyText(3, 172),
						_QtyText(4, 218),
						_QtyText(5, 264),
						_QtyText(6, 310),
					),
				},

				## Gaya
				{
					"name" : "gem_icon",
					"type" : "image",
					"style" : ("ltr", ),
					"x" : 152,
					"y" : 430 + D,
					"image" : ROOT_PATH + "cube_gem_icon.sub",
				},
				{
					"name" : "gem_textbg",
					"type" : "image",
					"style" : ("ltr", ),
					"x" : 169,
					"y" : 427 + D,
					"image" : ROOT_PATH + "cube_yang_textbg.sub",
					"children" :
					(
						{
							"name" : "gem_text",
							"type" : "text",
							"x" : 7,
							"y" : 3,
							"horizontal_align" : "right",
							"text_horizontal_align" : "right",
							"text" : "",
						},
					),
				},

				## Yang
				{
					"name" : "yang_icon",
					"type" : "image",
					"style" : ("ltr", ),
					"x" : 262,
					"y" : 430 + D,
					"image" : ROOT_PATH + "cube_yang_icon.sub",
				},
				{
					"name" : "yang_textbg",
					"type" : "image",
					"style" : ("ltr", ),
					"x" : 279,
					"y" : 427 + D,
					"image" : ROOT_PATH + "cube_yang_textbg.sub",
					"children" :
					(
						{
							"name" : "yang_text",
							"type" : "text",
							"x" : 7,
							"y" : 3,
							"horizontal_align" : "right",
							"text_horizontal_align" : "right",
							"text" : "",
						},
					),
				},

				## the chance-raising slot
				{
					"name" : "imporve_slot",
					"type" : "image",
					"style" : ("ltr", ),
					"x" : 29,
					"y" : 421 + D,
					"image" : ROOT_PATH + "cube_improve_slot.sub",
				},
				{
					"name" : "impove_text_window",
					"type" : "window",
					"style" : ("ltr", ),
					"x" : 27,
					"y" : 465 + D,
					"width" : 47,
					"height" : 13,
					"children" :
					(
						{
							"name" : "improve_text",
							"type" : "text",
							"x" : 0,
							"y" : 0,
							"horizontal_align" : "center",
							"text_horizontal_align" : "center",
							"vertical_align" : "center",
							"text_vertical_align" : "center",
							"text" : "",
						},
					),
				},

				{
					"name" : "button_ok",
					"type" : "button",
					"x" : 187,
					"y" : 453 + D,
					"text" : "",
					"default_image" : PUBLIC_PATH + "large_button_01.sub",
					"over_image" : PUBLIC_PATH + "large_button_02.sub",
					"down_image" : PUBLIC_PATH + "large_button_03.sub",
				},
				{
					"name" : "button_cancel",
					"type" : "button",
					"x" : 275,
					"y" : 453 + D,
					"text" : "",
					"default_image" : PUBLIC_PATH + "large_button_01.sub",
					"over_image" : PUBLIC_PATH + "large_button_02.sub",
					"down_image" : PUBLIC_PATH + "large_button_03.sub",
				},
			),
		},
	),
}
