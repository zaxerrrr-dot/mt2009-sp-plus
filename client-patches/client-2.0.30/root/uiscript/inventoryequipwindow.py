import uiScriptLocale
import app
import item
import player
import flamewindPath

# MT2009_PLUS_INVENTORY_V2_V1 - the equipment window of the official v2 inventory (the package "offical_inventory_v2",
# Autor: dracaryS; root/inventoryv2.py, uiinventory.py): the worn items in their own window, docked over the bag
# (uiscript/inventorywindowv2.py) - the page tabs of Druga strona ekwipunku (uiaddeq.py, MT2009_PLUS_ADDEQ_V1) at the
# top, the package's equipment picture (new_inventory/equip_bg_mt2009.png - its pet frame wiped: no pet slot here, the
# frame holds the horse bag and chest preview buttons) and under it the two rings and three round buttons
# (Alchemia, Magazyn przedmiotow, Sklep). No costume button (the owner, 21 October 2026 - MT2009_PLUS_INVENTORY_DSS_V1:
# Kostiumy opens from the extra inventory, uiekwipunek.py): its icon is painted out of the sub picture
# (equip_bg_sub_mt2009.png). Pictures: the pack inv2_ui (tools/inv2).
#
# ONE slot window ("EquipmentSlot", as the old inventory had) covers both pictures, so uiinventory.py fills and reads
# it as before (RefreshEquipSlotWindow, the rings included). Slot places = the package's (EquipmentSlot0); the rings
# sit on the sub picture's two frames.
ROOT = "d:/ymir work/ui/new_inventory/"

BOARD_WIDTH = 176
BOARD_HEIGHT = 286

EQUIP_BG_X, EQUIP_BG_Y = 10, 56		# equip_bg_mt2009.png 157 x 138
SUB_BG_X, SUB_BG_Y = 10, 196		# equip_bg_sub_mt2009.png 157 x 82
SLOT_X, SLOT_Y = EQUIP_BG_X + 3, EQUIP_BG_Y + 3
RING_Y = SUB_BG_Y + 6 - SLOT_Y		# the ring frames of the sub picture, in the slot window

# the exe without these systems has no item.EQUIPMENT_*: the server's INVENTORY_MAX_NUM + WEAR_* (uiscript/inventorywindow.py)
EQUIPMENT_BELT_SLOT = getattr(item, "EQUIPMENT_BELT", player.EQUIPMENT_SLOT_START + 23)
EQUIPMENT_PENDANT_SLOT = getattr(item, "EQUIPMENT_PENDANT", player.EQUIPMENT_SLOT_START + 25)
EQUIPMENT_GLOVE_SLOT = getattr(item, "EQUIPMENT_GLOVE", 0) if getattr(app, "ENABLE_GLOVE_SYSTEM", 0) else 0

SLOTS = (
	{"index":item.EQUIPMENT_BODY, "x":39, "y":37, "width":32, "height":64},
	{"index":item.EQUIPMENT_HEAD, "x":39, "y":2, "width":32, "height":32},
	{"index":item.EQUIPMENT_SHOES, "x":2, "y":98, "width":32, "height":32},
	{"index":item.EQUIPMENT_WRIST, "x":75, "y":67, "width":32, "height":32},
	{"index":item.EQUIPMENT_WEAPON, "x":3, "y":3, "width":32, "height":96},
	{"index":item.EQUIPMENT_NECK, "x":114, "y":67, "width":32, "height":32},
	{"index":item.EQUIPMENT_EAR, "x":114, "y":35, "width":32, "height":32},
	{"index":item.EQUIPMENT_ARROW, "x":114, "y":2, "width":32, "height":32},
	{"index":item.EQUIPMENT_SHIELD, "x":75, "y":35, "width":32, "height":32},
	{"index":EQUIPMENT_BELT_SLOT, "x":39, "y":98, "width":32, "height":32},
	{"index":EQUIPMENT_PENDANT_SLOT, "x":75, "y":2, "width":32, "height":32},
	{"index":item.EQUIPMENT_UNIQUE1, "x":2, "y":RING_Y, "width":32, "height":32},
	{"index":item.EQUIPMENT_UNIQUE2, "x":38, "y":RING_Y, "width":32, "height":32},
)
if EQUIPMENT_GLOVE_SLOT:
	SLOTS = SLOTS + ({"index":EQUIPMENT_GLOVE_SLOT, "x":75, "y":98, "width":32, "height":32},)

# the wiped bottom right frame of the equipment picture (its inside: 119..146 x 103..131 of the picture)
SMALL_BUTTON_X = EQUIP_BG_X + 126
SMALL_BUTTON_Y = EQUIP_BG_Y + 104


def PageTab(i, text):
	return {
		"name" : "Equipment_PageBg_%d" % i,
		"type" : "image",
		"x" : 5 + 40 * i,
		"y" : 33,
		"image" : ROOT + "equip_pagebtn_bg.png",
		"children" :
		(
			{
				"name" : "Equipment_Tab_%02d" % (i + 1),
				"type" : "radio_button",
				"x" : 1,
				"y" : 4,
				"default_image" : "d:/ymir work/ui/game/windows/tab_button_large_half_01.sub",
				"over_image" : "d:/ymir work/ui/game/windows/tab_button_large_half_02.sub",
				"down_image" : "d:/ymir work/ui/game/windows/tab_button_large_half_03.sub",
				"children" :
				(
					{
						"name" : "Equipment_Tab_%02d_Print" % (i + 1),
						"type" : "text",
						"x" : 0,
						"y" : 0,
						"all_align" : "center",
						"text" : text,
					},
				),
			},
		),
	}


def RoundButton(name, x, number, tooltip):
	return {
		"name" : name,
		"type" : "button",
		"x" : x,
		"y" : 45,
		"tooltip_text" : tooltip,
		"default_image" : ROOT + "btn_%d_0.png" % number,
		"over_image" : ROOT + "btn_%d_1.png" % number,
		"down_image" : ROOT + "btn_%d_2.png" % number,
	}


window = {
	"name" : "InventoryEquipWindow",

	"x" : SCREEN_WIDTH - BOARD_WIDTH,
	"y" : max(0, SCREEN_HEIGHT - 37 - 374 - BOARD_HEIGHT),

	"style" : ("movable", "float",),

	"width" : BOARD_WIDTH,
	"height" : BOARD_HEIGHT,

	"children" :
	(
		{
			"name" : "board",
			"type" : "board_with_titlebar",
			"style" : ("attach",),

			"x" : 0,
			"y" : 0,

			"width" : BOARD_WIDTH,
			"height" : BOARD_HEIGHT,

			"title" : uiScriptLocale.INVENTORY_TITLE,

			"children" :
			(
				# the page tabs: I / II = Druga strona ekwipunku (uiaddeq.py); III / IV stay hidden (two pages on the server)
				PageTab(0, "I"),
				PageTab(1, "II"),
				PageTab(2, "III"),
				PageTab(3, "IV"),

				{
					"name" : "Equipment_Base",
					"type" : "image",
					"x" : EQUIP_BG_X,
					"y" : EQUIP_BG_Y,
					"image" : ROOT + "equip_bg_mt2009.png",
				},
				{
					"name" : "Equipment_Sub_Base",
					"type" : "image",
					"x" : SUB_BG_X,
					"y" : SUB_BG_Y,
					"image" : ROOT + "equip_bg_sub_mt2009.png",
					"children" :
					(
						RoundButton("DSSButton", 6, 0, uiScriptLocale.TASKBAR_DRAGON_SOUL),
						RoundButton("DepositButton", 41, 1, uiScriptLocale.POCKET_DEPOSIT),
						RoundButton("MyShopButton", 79, 2, uiScriptLocale.SHOP_MANAGE),
					),
				},

				# over both pictures (a later child is drawn and picked over the earlier ones)
				{
					"name" : "EquipmentSlot",
					"type" : "slot",

					"x" : SLOT_X,
					"y" : SLOT_Y,

					"width" : 151,
					"height" : RING_Y + 33,

					"slot" : SLOTS,
				},

				{
					"name" : "HorseInventoryWindow",
					"type" : "button",
					"x" : SMALL_BUTTON_X,
					"y" : SMALL_BUTTON_Y,
					"tooltip_text" : uiScriptLocale.HORSE_INVENTORY,
					"default_image" : flamewindPath.GetInventory("horse_inv_btn1"),
					"over_image" : flamewindPath.GetInventory("horse_inv_btn2"),
					"down_image" : flamewindPath.GetInventory("horse_inv_btn3"),
				},
				{
					"name" : "ChestPreviewButton",
					"type" : "button",
					"x" : SMALL_BUTTON_X,
					"y" : SMALL_BUTTON_Y + 14,
					"tooltip_text" : "Podgl\xb9d skrzynki",
					"default_image" : "playerbot_ui/chest_button.tga",
					"over_image" : "playerbot_ui/chest_button.tga",
					"down_image" : "playerbot_ui/chest_button.tga",
				},
			),
		},
	),
}
