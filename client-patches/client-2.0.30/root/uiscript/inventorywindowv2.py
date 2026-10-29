import uiScriptLocale
import app
import item
import flamewindPath
from utils import ReplaceElement, AppendChildren

# MT2009_PLUS_INVENTORY_V2_V1 - the bag of the official v2 inventory (the package "offical_inventory_v2", Autor:
# dracaryS; root/inventoryv2.py, uiinventory.py): the worn items left for their own window (uiscript/
# inventoryequipwindow.py, docked over this one); here the title bar (Scal i uporzadkuj), the four page tabs as the
# package draws them, the 5 x 9 grid and the money rows - the Yang (+ the Won with ENABLE_CHEQUE_SYSTEM) and the Gaya row
# of MT2009_PLUS_GAYA_CURRENCY_V1, both as in uiscript/inventorywindow.py (the old one-window inventory, kept for
# inventoryv2.ENABLED = 0 and as the fallback when this layout does not load).
BOARD_WIDTH = 176
GRID_Y = 55
BOARD_HEIGHT = GRID_Y + 9 * 32 + 31	# 374: the money row 28 px over the bottom, as in the old window


def InventoryTab(i, text, tooltip):
	return {
		"name" : "Inventory_Tab_%02d" % (i + 1),
		"type" : "radio_button",

		"x" : 7 + 40 * i,
		"y" : 33,

		"default_image" : "d:/ymir work/ui/game/windows/tab_button_large_half_01.sub",
		"over_image" : "d:/ymir work/ui/game/windows/tab_button_large_half_02.sub",
		"down_image" : "d:/ymir work/ui/game/windows/tab_button_large_half_03.sub",
		"tooltip_text" : tooltip,

		"children" :
		(
			{
				"name" : "Inventory_Tab_%02d_Print" % (i + 1),
				"type" : "text",

				"x" : 0,
				"y" : 0,

				"all_align" : "center",

				"text" : text,
			},
		),
	}


window = {
	"name" : "InventoryWindow",

	"x" : SCREEN_WIDTH - BOARD_WIDTH,
	"y" : SCREEN_HEIGHT - 37 - BOARD_HEIGHT,

	"style" : ("movable", "float",),

	"width" : BOARD_WIDTH,
	"height" : BOARD_HEIGHT,

	"children" :
	(
		{
			"name" : "board",
			"type" : "board",
			"style" : ("attach",),

			"x" : 0,
			"y" : 0,

			"width" : BOARD_WIDTH,
			"height" : BOARD_HEIGHT,

			"children" :
			(
				## Title
				{
					"name" : "TitleBar",
					"type" : "titlebar",
					"style" : ("attach",),

					"x" : 8,
					"y" : 7,

					"width" : 161,
					"color" : "yellow",

					"children" :
					(
						{ "name":"TitleName", "type":"text", "x":71, "y":3, "text":uiScriptLocale.INVENTORY_TITLE, "text_horizontal_align":"center" },

						{
							"name" : "AutoStackButton",
							"type" : "button",
							"x" : 42,
							"y" : -1,
							"horizontal_align": "right",
							"vertical_align": "center",
							"default_image" : flamewindPath.GetInventory("autostack_01"),
							"over_image" : flamewindPath.GetInventory("autostack_02"),
							"down_image" : flamewindPath.GetInventory("autostack_03"),
							"tooltip_text" : uiScriptLocale.INVENTORY_AUTOSTACK,
							"tooltip_y": -19,
							"tooltip_x": -30,
						},
					),
				},

				InventoryTab(0, "I", uiScriptLocale.INVENTORY_PAGE_BUTTON_TOOLTIP_1),
				InventoryTab(1, "II", uiScriptLocale.INVENTORY_PAGE_BUTTON_TOOLTIP_2),
				InventoryTab(2, "III", "3. Ekwipunek"),
				InventoryTab(3, "IV", "4. Ekwipunek"),

				## Item Slot
				{
					"name" : "ItemSlot",
					"type" : "grid_table",

					"x" : 8,
					"y" : GRID_Y,

					"start_index" : 0,
					"x_count" : 5,
					"y_count" : 9,
					"x_step" : 32,
					"y_step" : 32,

					"image" : "d:/ymir work/ui/public/Slot_Base.sub"
				},

				## Print
				{
					"name":"Money_Slot",
					"type":"button",

					"x":8,
					"y":28,

					"horizontal_align":"center",
					"vertical_align":"bottom",

					"default_image" : "d:/ymir work/ui/public/parameter_slot_05.sub",
					"over_image" : "d:/ymir work/ui/public/parameter_slot_05.sub",
					"down_image" : "d:/ymir work/ui/public/parameter_slot_05.sub",

					"children" :
					(
						{
							"name":"Money_Icon",
							"type":"image",

							"x":-18,
							"y":2,

							"image":"d:/ymir work/ui/game/windows/money_icon.sub",
						},

						{
							"name" : "Money",
							"type" : "text",

							"x" : 3,
							"y" : 3,

							"horizontal_align" : "right",
							"text_horizontal_align" : "right",

							"text" : "123456789",
						},
					),
				},
			),
		},
	),
}

if app.ENABLE_CHEQUE_SYSTEM:
	slot = {
		"name":"Money_Slot",
		"type":"button",

		"x":75,
		"y":28,

		#"horizontal_align":"center",
		"vertical_align":"bottom",

		"default_image" : "d:/ymir work/ui/public/gold_slot.sub",
		"over_image" : "d:/ymir work/ui/public/gold_slot.sub",
		"down_image" : "d:/ymir work/ui/public/gold_slot.sub",

		"children" :
		(
			{
				"name" : "Money",
				"type" : "text",

				"x" : 3,
				"y" : 3,

				"horizontal_align" : "right",
				"text_horizontal_align" : "right",

				"text" : "123456789",
			},
		),
	}

	children = (
		{
			"name":"Money_Icon",
			"type":"image",
			"vertical_align":"bottom",

			"x":57,
			"y":26,

			"image":"d:/ymir work/ui/game/windows/money_icon.sub",
		},

		{
			"name":"Cheque_Icon",
			"type":"image",
			"vertical_align":"bottom",

			"x":10,
			"y":26,

			"image":"d:/ymir work/ui/game/windows/cheque_icon.sub",
		},
		{
			"name":"Cheque_Slot",
			"type":"button",

			"x":28,
			"y":28,

			#"horizontal_align":"center",
			"vertical_align":"bottom",

			"default_image" : "d:/ymir work/ui/public/cheque_slot.sub",
			"over_image" : "d:/ymir work/ui/public/cheque_slot.sub",
			"down_image" : "d:/ymir work/ui/public/cheque_slot.sub",

			"children" :
			(
				{
					"name" : "Cheque",
					"type" : "text",

					"x" : 3,
					"y" : 3,

					"horizontal_align" : "right",
					"text_horizontal_align" : "right",

					"text" : "99",
				},
			),
		},
	)

	ReplaceElement("Money_Slot", slot, window)
	AppendChildren("board", children, window)

# MT2009_PLUS_GAYA_CURRENCY_V1: the Gaya counter right over the Yang (the owner, 28 October 2026: "no icon / counter next
# to the Yang, the Gaya piles up as slots" - Gaya is a currency now, server-patches/gaya2; gayacurrency.py fills it): one
# more 22-px row at the board's bottom, the window as much taller (the item grid and everything above stay). With
# constInfo.ENABLE_WON (no Won on the server yet - off) the row is Won + Gaya. A uiscript may not import constInfo (the
# loader's sandbox) - utils, which may, holds it.
import utils
_gayaConst = getattr(utils, "constInfo", None)
if getattr(_gayaConst, "ENABLE_GAYA_CURRENCY", 0) and not app.ENABLE_CHEQUE_SYSTEM:
	GAYA_ROW = 22
	window["height"] += GAYA_ROW
	window["y"] = max(0, window["y"] - GAYA_ROW)
	window["children"][0]["height"] += GAYA_ROW
	_gayaText = {"name" : "Gaya", "type" : "text", "x" : 3, "y" : 3, "horizontal_align" : "right",
		"text_horizontal_align" : "right", "text" : "0"}
	if getattr(_gayaConst, "ENABLE_WON", 0):
		gayaRow = (
			{"name" : "Won_Icon", "type" : "image", "x" : 10, "y" : 48, "vertical_align" : "bottom",
				"image" : "d:/ymir work/ui/game/windows/cheque_icon.sub"},
			{"name" : "Won_Slot", "type" : "image", "x" : 28, "y" : 50, "vertical_align" : "bottom",
				"image" : "d:/ymir work/ui/gaya2/cheque_slot.sub",
				"children" : ({"name" : "Won", "type" : "text", "x" : 3, "y" : 3, "horizontal_align" : "right",
					"text_horizontal_align" : "right", "text" : "0"},)},
			{"name" : "Gaya_Icon", "type" : "image", "x" : 58, "y" : 47, "vertical_align" : "bottom",
				"image" : "d:/ymir work/ui/gaya2/gaya_icon.tga"},
			{"name" : "Gaya_Slot", "type" : "image", "x" : 74, "y" : 50, "vertical_align" : "bottom",
				"image" : "d:/ymir work/ui/public/parameter_slot_03.sub", "children" : (_gayaText,)},
		)
	else:
		gayaRow = (
			{"name" : "Gaya_Slot", "type" : "image", "x" : 8, "y" : 50, "horizontal_align" : "center",
				"vertical_align" : "bottom", "image" : "d:/ymir work/ui/public/parameter_slot_05.sub",
				"children" : (
					{"name" : "Gaya_Icon", "type" : "image", "x" : -16, "y" : 4, "image" : "d:/ymir work/ui/gaya2/gaya_icon.tga"},
					_gayaText,
				)},
		)
	AppendChildren("board", gayaRow, window)
