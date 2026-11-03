import uiScriptLocale
import app
import item
import flamewindPath
from utils import ReplaceElement, AppendChildren

EQUIPMENT_START_INDEX = 90

# MT2009_PLUS_BELT_SLOT_V1: the belt slot (WEAR_BELT = 23). The exe is built
# without ENABLE_NEW_EQUIPMENT_SYSTEM, so item.EQUIPMENT_BELT may be missing:
# the slot is the inventory's equipment start + 23, as the server's
# INVENTORY_MAX_NUM + WEAR_BELT. Placed where GF puts it, under the armour.
import player
EQUIPMENT_BELT_SLOT = getattr(item, "EQUIPMENT_BELT", player.EQUIPMENT_SLOT_START + 23)
BELT_SLOT_X = 39
BELT_SLOT_Y = 106

# MT2009_PLUS_ELEMENTS_V1: the talisman slot (WEAR_PENDANT = 25; Autor: Digi Rasta, Zywioly
# i talizmany). item.EQUIPMENT_PENDANT comes with an exe built with ENABLE_PENDANT_SYSTEM;
# without it the slot is the equipment start + 25, as the server's INVENTORY_MAX_NUM +
# WEAR_PENDANT. Bottom of the left column, under the left ring (V2: under the necklace it lay
# beneath the Dragon Soul button at 114,120 - the owner, 7 October).
EQUIPMENT_PENDANT_SLOT = getattr(item, "EQUIPMENT_PENDANT", player.EQUIPMENT_SLOT_START + 25)
PENDANT_SLOT_X = 2
PENDANT_SLOT_Y = 147

# MT2009_PLUS_GLOVES_V1: the Sung Ma glove slot (WEAR_GLOVE = 26; server-patches/rekawice) - only with the exe of
# the second Yohara round (ENABLE_GLOVE_SYSTEM: item.EQUIPMENT_GLOVE). Right column, under the necklace (the
# arrow, the earrings, the necklace, the gloves); the Dragon Soul button, which stood there, went small into the gap
# between the arrow and the earrings - now (MT2009_PLUS_INVENTORY_DSS_V1, below) full size in the costume button's place.
EQUIPMENT_GLOVE_SLOT = getattr(item, "EQUIPMENT_GLOVE", 0) if getattr(app, "ENABLE_GLOVE_SYSTEM", 0) else 0
GLOVE_SLOT_X = 114
GLOVE_SLOT_Y = 117
if EQUIPMENT_GLOVE_SLOT:
	GLOVE_SLOT_TUPLE = ({"index":EQUIPMENT_GLOVE_SLOT, "x":GLOVE_SLOT_X, "y":GLOVE_SLOT_Y, "width":32, "height":32},)
	GLOVE_BASE_TUPLE = ({
		"name" : "GloveSlotBase",
		"type" : "image",
		"x" : 3 + GLOVE_SLOT_X,
		"y" : 3 + GLOVE_SLOT_Y,
		"image" : "d:/ymir work/ui/public/slot_base.sub",
	},)
else:
	GLOVE_SLOT_TUPLE = ()
	GLOVE_BASE_TUPLE = ()

# MT2009_PLUS_INVENTORY_DSS_V1 (the owner, 21 October 2026: "usunac przycisk kostiumow, w jego miejsce przycisk
# Alchemii normalnej wielkosci"): the costume button is gone (the costume window opens from the extra inventory's
# "Kostiumy" button, uiekwipunek.py MT2009_PLUS_EKWIPUNEK_ROW2_V1); the Dragon Soul button, at its own size (38 x 34),
# takes its place between the helmet and the arrow - over the shield, clear of all three slots.
DSS_BUTTON_X, DSS_BUTTON_Y = 77, 3

window = {
	"name" : "InventoryWindow",

	"x" : SCREEN_WIDTH - 176 ,
	"y" : SCREEN_HEIGHT - 37 - 565,

	"style" : ("movable", "float",),

	"width" : 176,
	"height" : 565,

	"children" :
	(
		{
			"name" : "board",
			"type" : "board",
			"style" : ("attach",),

			"x" : 0,
			"y" : 0,

			"width" : 176,
			"height" : 565,

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

				## Equipment Slot
				{
					"name" : "Equipment_Base",
					"type" : "image",

					"x" : 10,
					"y" : 33,

					"image" : "d:/ymir work/ui/game/windows/equipment_base.sub",

					"children" :
					(

						## MT2009_PLUS_BELT_SLOT_V1: the empty belt slot's frame (under the slot window)
						{
							"name" : "BeltSlotBase",
							"type" : "image",

							"x" : 3 + BELT_SLOT_X,
							"y" : 3 + BELT_SLOT_Y,

							"image" : "d:/ymir work/ui/public/slot_base.sub",
						},

						## MT2009_PLUS_ELEMENTS_V1: the empty talisman slot's frame
						{
							"name" : "PendantSlotBase",
							"type" : "image",

							"x" : 3 + PENDANT_SLOT_X,
							"y" : 3 + PENDANT_SLOT_Y,

							"image" : "d:/ymir work/ui/public/slot_base.sub",
						},
					) + GLOVE_BASE_TUPLE + (

						{
							"name" : "EquipmentSlot",
							"type" : "slot",

							"x" : 3,
							"y" : 3,

							"width" : 150,
							"height" : 182,

							"slot" : (
										{"index":item.EQUIPMENT_BODY, "x":39, "y":37, "width":32, "height":64},
										{"index":item.EQUIPMENT_HEAD, "x":39, "y":2, "width":32, "height":32},
										{"index":item.EQUIPMENT_SHOES, "x":39, "y":145, "width":32, "height":32},
										{"index":item.EQUIPMENT_WRIST, "x":75, "y":67, "width":32, "height":32},
										{"index":item.EQUIPMENT_WEAPON, "x":3, "y":3, "width":32, "height":96},
										{"index":item.EQUIPMENT_NECK, "x":114, "y":84, "width":32, "height":32},
										{"index":item.EQUIPMENT_EAR, "x":114, "y":52, "width":32, "height":32},
										{"index":item.EQUIPMENT_UNIQUE1, "x":2, "y":113, "width":32, "height":32},
										{"index":item.EQUIPMENT_UNIQUE2, "x":75, "y":113, "width":32, "height":32},
										{"index":item.EQUIPMENT_ARROW, "x":114, "y":1, "width":32, "height":32},
										{"index":item.EQUIPMENT_SHIELD, "x":75, "y":35, "width":32, "height":32},
										## MT2009_PLUS_BELT_SLOT_V1
										{"index":EQUIPMENT_BELT_SLOT, "x":BELT_SLOT_X, "y":BELT_SLOT_Y, "width":32, "height":32},
										## MT2009_PLUS_ELEMENTS_V1
										{"index":EQUIPMENT_PENDANT_SLOT, "x":PENDANT_SLOT_X, "y":PENDANT_SLOT_Y, "width":32, "height":32},
									) + GLOVE_SLOT_TUPLE,
						},

						{
							"name" : "InventoryAdditionalButtons",
							"type" : "image",

							"x" : 55,
							"y" : 23,

							"horizontal_align" : "right",
							"vertical_align" : "bottom",

							"image" : flamewindPath.GetInventory("inventory_buttons_slot"),
							"children" : (
								# MT2009_PLUS_INVENTORY_V2_V2: the horse bag button is gone (no horse bags on Yohara)
								{
									"name" : "DepositButton",
									"type" : "button",

									"x" : 17,"y" : 2,

									"tooltip_text" : "Magazyn ItemShop",	# MT2009_PLUS_INVENTORY_WIKI_V1

									"default_image" : flamewindPath.GetInventory("deposit_btn1"),
									"over_image" : flamewindPath.GetInventory("deposit_btn2"),
									"down_image" : flamewindPath.GetInventory("deposit_btn3"),
								},
								{
									"name": "MyShopButton",
									"type": "button",

									"x": 32, "y": 2,

									"tooltip_text" : "Osobisty Sklepik Premium",	# MT2009_PLUS_INVENTORY_WIKI_V1: the offline shop

									"default_image": flamewindPath.GetInventory("myshop_btn1"),
									"over_image": flamewindPath.GetInventory("myshop_btn2"),
									"down_image": flamewindPath.GetInventory("myshop_btn3"),
								},
							),
						},

						## Dragon Soul Button
						{
							"name" : "DSSButton",
							"type" : "button",
							"x" : DSS_BUTTON_X, # MT2009_PLUS_INVENTORY_DSS_V1: the costume button's place
							"y" : DSS_BUTTON_Y,
							"tooltip_text" : uiScriptLocale.TASKBAR_DRAGON_SOUL,
							"default_image" : "d:/ymir work/ui/dragonsoul/dss_inventory_button_01.tga",
							"over_image" : "d:/ymir work/ui/dragonsoul/dss_inventory_button_02.tga",
							"down_image" : "d:/ymir work/ui/dragonsoul/dss_inventory_button_03.tga",
						},

						## Costume Button - MT2009_PLUS_INVENTORY_DSS_V1: removed (Kostiumy in the extra inventory)

						{
							"name" : "ChestPreviewButton",
							"type" : "button",

							"x" : 70,
							"y" : 21,

							"horizontal_align" : "right",
							"vertical_align" : "bottom",

							"tooltip_text" : "Podgl\xb9d skrzynki",

							"default_image" : "playerbot_ui/chest_button.tga",
							"over_image" : "playerbot_ui/chest_button.tga",
							"down_image" : "playerbot_ui/chest_button.tga",
						},

						{
							"name" : "Equipment_Tab_01",
							"type" : "radio_button",

							"x" : 86,
							"y" : 161,

							"default_image" : "d:/ymir work/ui/game/windows/tab_button_small_01.sub",
							"over_image" : "d:/ymir work/ui/game/windows/tab_button_small_02.sub",
							"down_image" : "d:/ymir work/ui/game/windows/tab_button_small_03.sub",

							"children" :
							(
								{
									"name" : "Equipment_Tab_01_Print",
									"type" : "text",

									"x" : 0,
									"y" : 0,

									"all_align" : "center",

									"text" : "I",
								},
							),
						},
						{
							"name" : "Equipment_Tab_02",
							"type" : "radio_button",

							"x" : 86 + 32,
							"y" : 161,

							"default_image" : "d:/ymir work/ui/game/windows/tab_button_small_01.sub",
							"over_image" : "d:/ymir work/ui/game/windows/tab_button_small_02.sub",
							"down_image" : "d:/ymir work/ui/game/windows/tab_button_small_03.sub",

							"children" :
							(
								{
									"name" : "Equipment_Tab_02_Print",
									"type" : "text",

									"x" : 0,
									"y" : 0,

									"all_align" : "center",

									"text" : "II",
								},
							),
						},

					),
				},

				{
					"name" : "Inventory_Tab_01",
					"type" : "radio_button",

					"x" : 12,
					"y" : 33 + 191,

					"default_image" : "d:/ymir work/ui/game/windows/tab_button_small_01.sub",
					"over_image" : "d:/ymir work/ui/game/windows/tab_button_small_02.sub",
					"down_image" : "d:/ymir work/ui/game/windows/tab_button_small_03.sub",
					"tooltip_text" : uiScriptLocale.INVENTORY_PAGE_BUTTON_TOOLTIP_1,

					"children" :
					(
						{
							"name" : "Inventory_Tab_01_Print",
							"type" : "text",

							"x" : 0,
							"y" : 0,

							"all_align" : "center",

							"text" : "I",
						},
					),
				},
				{
					"name" : "Inventory_Tab_02",
					"type" : "radio_button",

					"x" : 52,
					"y" : 33 + 191,

					"default_image" : "d:/ymir work/ui/game/windows/tab_button_small_01.sub",
					"over_image" : "d:/ymir work/ui/game/windows/tab_button_small_02.sub",
					"down_image" : "d:/ymir work/ui/game/windows/tab_button_small_03.sub",
					"tooltip_text" : uiScriptLocale.INVENTORY_PAGE_BUTTON_TOOLTIP_2,

					"children" :
					(
						{
							"name" : "Inventory_Tab_02_Print",
							"type" : "text",

							"x" : 0,
							"y" : 0,

							"all_align" : "center",

							"text" : "II",
						},
					),
				},
				{
					"name" : "Inventory_Tab_03",
					"type" : "radio_button",

					"x" : 92,
					"y" : 33 + 191,

					"default_image" : "d:/ymir work/ui/game/windows/tab_button_small_01.sub",
					"over_image" : "d:/ymir work/ui/game/windows/tab_button_small_02.sub",
					"down_image" : "d:/ymir work/ui/game/windows/tab_button_small_03.sub",
					"tooltip_text" : "3. Ekwipunek",

					"children" :
					(
						{
							"name" : "Inventory_Tab_03_Print",
							"type" : "text",

							"x" : 0,
							"y" : 0,

							"all_align" : "center",

							"text" : "III",
						},
					),
				},
				{
					"name" : "Inventory_Tab_04",
					"type" : "radio_button",

					"x" : 132,
					"y" : 33 + 191,

					"default_image" : "d:/ymir work/ui/game/windows/tab_button_small_01.sub",
					"over_image" : "d:/ymir work/ui/game/windows/tab_button_small_02.sub",
					"down_image" : "d:/ymir work/ui/game/windows/tab_button_small_03.sub",
					"tooltip_text" : "4. Ekwipunek",

					"children" :
					(
						{
							"name" : "Inventory_Tab_04_Print",
							"type" : "text",

							"x" : 0,
							"y" : 0,

							"all_align" : "center",

							"text" : "IV",
						},
					),
				},

				# {
				# 	"name" : "Inventory_Tab_03",
				# 	"type" : "radio_button",
				#
				# 	"x" : 10 + 78,
				# 	"y" : 33 + 171,
				#
				# 	"default_image" : "d:/ymir work/ui/game/windows/tab_button_large_01.sub",
				# 	"over_image" : "d:/ymir work/ui/game/windows/tab_button_large_02.sub",
				# 	"down_image" : "d:/ymir work/ui/game/windows/tab_button_large_03.sub",
				# 	"tooltip_text" : uiScriptLocale.INVENTORY_PAGE_BUTTON_TOOLTIP_2,
				#
				# 	"children" :
				# 	(
				# 		{
				# 			"name" : "Inventory_Tab_03_Print",
				# 			"type" : "text",
				#
				# 			"x" : 0,
				# 			"y" : 0,
				#
				# 			"all_align" : "center",
				#
				# 			"text" : "III",
				# 		},
				# 	),
				# },

				## Item Slot
				{
					"name" : "ItemSlot",
					"type" : "grid_table",

					"x" : 8,
					"y" : 246,

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
