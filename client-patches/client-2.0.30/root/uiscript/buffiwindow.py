# MT2009_PLUS_BUFFI_V2: the Buffi window (root/uibuffi.py) - Ameria Project's two Buffi pages side by side (the
# owner, 21 October 2026: "okno 1:1 jak w Amerii: uklad, grafiki, przyciski, zakladki"):
#   left  - Ameria's inventory page IV (uiscript/inventorywindowex*.py "Equipment_Base_Tab_3", uiinventory.py
#           SetEquipmentPage(3)): companion_bg.png with the buffi's costume slots at Ameria's places - outfit (its
#           216 = our WEAR_BUFFI_BODY 28), hairstyle (217/29), weapon (218/30), sash (219/31) - and the mount's costume
#           (COSTUME_SLOT_START + 2, as Ameria shows it there); Ameria's old pet / mount skin frames stay empty;
#   right - Ameria's character window "Buffi" skill page (uiscript/characterwindow.py Skill_Page, uicharacter.py
#           PAGE_BUFFI): the skill bar with the group button "Buffi", the four skills in the active skill grid (the
#           grade columns 1/21/41 ...), buffi_skill_bg.png with the Zwoj Imienia Buffi icon and three lines, and the
#           covers over Szybkosc / Zwiekszenie Ataku while the buffi has no name (Ameria's buffi_slot_hide_1-6);
#   under - our call / send away and name buttons (Ameria does both with the items only).
# The slots of the right page take a shaman's skill book (uibuffi.py: "/buffi read").
import item
import player

BUFFI_SLOT_BODY = getattr(item, "BUFFI_SLOT_BODY", player.EQUIPMENT_SLOT_START + 28)
BUFFI_SLOT_HEAD = getattr(item, "BUFFI_SLOT_HEAD", player.EQUIPMENT_SLOT_START + 29)
BUFFI_SLOT_WEAPON = getattr(item, "BUFFI_SLOT_WEAPON", player.EQUIPMENT_SLOT_START + 30)
BUFFI_SLOT_SASH = getattr(item, "BUFFI_SLOT_SASH", player.EQUIPMENT_SLOT_START + 31)
MOUNT_SLOT = item.COSTUME_SLOT_START + 2

COSTUME_X, COSTUME_Y = 10, 32				# Ameria's page: board (10, 33)
SKILL_X, SKILL_Y = 10 + 155 + 10, 32		# Ameria's Skill_Page: the bar at (15, 9), the slots at (16, 30)
LOCK = "d:/ymir work/ui/game/costume/hideslot_01.tga"
WIDTH = SKILL_X + 223 + 12
HEIGHT = SKILL_Y + 21 + 76 + 107 + 44

window = {
	"name" : "BuffiWindow",

	"x" : (SCREEN_WIDTH - WIDTH) / 2,
	"y" : (SCREEN_HEIGHT - HEIGHT) / 2,

	"style" : ("movable", "float",),

	"width" : WIDTH,
	"height" : HEIGHT,

	"children" :
	(
		{
			"name" : "board",
			"type" : "board_with_titlebar",
			"style" : ("attach",),

			"x" : 0,
			"y" : 0,

			"width" : WIDTH,
			"height" : HEIGHT,

			"title" : "Buffi",

			"children" :
			(
				## Ameria's inventory page IV (Equipment_Base_Tab_3 / EquipmentSlot_3)
				{
					"name" : "Costume_Base",
					"type" : "image",

					"x" : COSTUME_X,
					"y" : COSTUME_Y,

					"image" : "d:/ymir work/ui/game/inventory/companion_bg.png",

					"children" :
					(
						{
							"name" : "CostumeSlot",
							"type" : "slot",

							"x" : 0,
							"y" : 0,

							"width" : 165,
							"height" : 187,

							"slot" : (
								{"index":BUFFI_SLOT_BODY, "x":62, "y":54, "width":32, "height":64},
								{"index":BUFFI_SLOT_HEAD, "x":62, "y":15, "width":32, "height":32},
								{"index":BUFFI_SLOT_WEAPON, "x":11, "y":15, "width":32, "height":96},
								{"index":BUFFI_SLOT_SASH, "x":116, "y":13, "width":32, "height":32},
								{"index":MOUNT_SLOT, "x":60, "y":141, "width":32, "height":32},
							),
						},
					),
				},

				## Ameria's skill page, group "Buffi" (Skill_Active_Title_Bar, Skill_Group_Button_3)
				{
					"name" : "Skill_Title_Bar",
					"type" : "horizontalbar",

					"x" : SKILL_X,
					"y" : SKILL_Y,

					"width" : 223,

					"children" :
					(
						{
							"name" : "Skill_Group_Button",
							"type" : "radio_button",

							"x" : 5,
							"y" : 2,

							"text" : "Buffi",
							"text_color" : 0xFFFFE3AD,

							"default_image" : "d:/ymir work/ui/game/windows/skill_tab_button_01.sub",
							"over_image" : "d:/ymir work/ui/game/windows/skill_tab_button_02.sub",
							"down_image" : "d:/ymir work/ui/game/windows/skill_tab_button_03.sub",
						},
					),
				},
				{
					"name" : "Skill_Slot",
					"type" : "slot",

					"x" : SKILL_X + 1,
					"y" : SKILL_Y + 21,

					"width" : 223,
					"height" : 76,

					"image" : "d:/ymir work/ui/public/Slot_Base.sub",

					"slot" : (
						{"index": 1, "x": 1, "y": 4, "width":32, "height":32},
						{"index":21, "x":38, "y": 4, "width":32, "height":32},
						{"index":41, "x":75, "y": 4, "width":32, "height":32},

						{"index": 2, "x":113, "y": 4, "width":32, "height":32},
						{"index":22, "x":150, "y": 4, "width":32, "height":32},
						{"index":42, "x":187, "y": 4, "width":32, "height":32},

						{"index": 3, "x": 1, "y": 40, "width":32, "height":32},
						{"index":23, "x":38, "y": 40, "width":32, "height":32},
						{"index":43, "x":75, "y": 40, "width":32, "height":32},

						{"index": 4, "x":113, "y": 40, "width":32, "height":32},
						{"index":24, "x":150, "y": 40, "width":32, "height":32},
						{"index":44, "x":187, "y": 40, "width":32, "height":32},
					),
				},
				## Ameria's buffi_skill_page
				{
					"name" : "Buffi_Skill_Page",
					"type" : "image",

					"x" : SKILL_X + 2,
					"y" : SKILL_Y + 21 + 76,

					"image" : "d:/ymir work/ui/game/buffi/buffi_skill_bg.png",

					"children" :
					(
						{ "name" : "Buffi_Info_1", "type" : "text", "all_align" : "center", "text" : "", "x" : 0, "y" : 24 - 12 },
						{ "name" : "Buffi_Info_2", "type" : "text", "all_align" : "center", "text" : "", "x" : 0, "y" : 24 },
						{ "name" : "Buffi_Info_3", "type" : "text", "all_align" : "center", "text" : "", "x" : 0, "y" : 24 + 12 },
						{ "name" : "Buffi_Icon", "type" : "image", "image" : "icon/item/61030.tga", "x" : 93, "y" : 11 },
						## Szybkosc / Zwiekszenie Ataku without a name (Ameria's buffi_slot_hide_1-6)
						{ "name" : "Buffi_Lock_1", "type" : "image", "image" : LOCK, "x" : 0, "y" : -36 },
						{ "name" : "Buffi_Lock_2", "type" : "image", "image" : LOCK, "x" : 37, "y" : -36 },
						{ "name" : "Buffi_Lock_3", "type" : "image", "image" : LOCK, "x" : 74, "y" : -36 },
						{ "name" : "Buffi_Lock_4", "type" : "image", "image" : LOCK, "x" : 112, "y" : -36 },
						{ "name" : "Buffi_Lock_5", "type" : "image", "image" : LOCK, "x" : 149, "y" : -36 },
						{ "name" : "Buffi_Lock_6", "type" : "image", "image" : LOCK, "x" : 186, "y" : -36 },
					),
				},

				## call / send away, name
				{
					"name" : "Toggle_Button",
					"type" : "button",

					"x" : COSTUME_X + 2,
					"y" : HEIGHT - 36,

					"text" : "",

					"default_image" : "d:/ymir work/ui/public/large_button_01.sub",
					"over_image" : "d:/ymir work/ui/public/large_button_02.sub",
					"down_image" : "d:/ymir work/ui/public/large_button_03.sub",
				},
				{
					"name" : "Rename_Button",
					"type" : "button",

					"x" : COSTUME_X + 2 + 98,
					"y" : HEIGHT - 36,

					"text" : "Nadaj imi\xea",

					"default_image" : "d:/ymir work/ui/public/large_button_01.sub",
					"over_image" : "d:/ymir work/ui/public/large_button_02.sub",
					"down_image" : "d:/ymir work/ui/public/large_button_03.sub",
				},
				{
					"name" : "State_Text",
					"type" : "text",

					"x" : SKILL_X + 4,
					"y" : HEIGHT - 31,

					"text" : "",
				},
			),
		},
	),
}
