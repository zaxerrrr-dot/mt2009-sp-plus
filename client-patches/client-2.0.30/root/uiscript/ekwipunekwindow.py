# MT2009_PLUS_EKWIPUNEK_LOOK_V1 - Dodatkowy ekwipunek: Ameria Project's special
# storage window (root/uiscript/inventorywindownew.py + the bar uispecialinventory.py
# makes in python) 1:1 - the same sizes, places and images (copied from Ameria's
# "ymir work/ui/game/interfaces/special_storage" and "special_inventory", the page
# tabs cut out of its ui/windows.dds: root/mt2009_ui/ekwipunek). Positions are the
# ones with the settings bar closed; uiekwipunek.py opens it at once (+25), as
# Ameria's ManageInventory() does.
#
# Ameria's eight category buttons: the first row (upgrade, stone, book, bonus) as
# there; of the second only the chests (Ameria's btn_guild icon) - Ameria's costume
# storage never fills, and its safebox / item mall buttons open the safebox from
# anywhere, which this server does not have.
#
# MT2009_PLUS_EKWIPUNEK_ROW2_V1 (the owner, 21 October 2026: "dodaj tam Kostiumy,
# Alchemie i ItemShop" - "okno kostiumow, nie magazyn kostiumow"): the second row
# as Ameria's (costume, guild = our chests, safebox, item mall), three of them
# plain buttons that open windows: Kostiumy - the costume window (the one the
# inventory's costume button opened), Alchemia - the Dragon Soul window (Ameria's
# Dragon Soul button of its taskbar, DragonSoul_Button_0x), ItemShop - the
# in-game ItemShop. uiekwipunek.py binds them.

import uiScriptLocale

ROOT = "mt2009_ui/ekwipunek/"
WINDOW_WIDTH = 184
WINDOW_HEIGHT = 328 + 32 + 60 + 20

def PageTab(index, text, tooltip):
	return {
		"name" : "Inventory_Tab_%02d" % index,
		"type" : "radio_button",
		"x" : 14 + 39 * (index - 1),
		"y" : 295 + 32,
		"default_image" : ROOT + "tab_page_1.png",
		"over_image" : ROOT + "tab_page_2.png",
		"down_image" : ROOT + "tab_page_3.png",
		"tooltip_text" : tooltip,
		"children" :
		(
			{
				"name" : "Inventory_Tab_%02d_Print" % index,
				"type" : "text",
				"x" : 0,
				"y" : 0,
				"all_align" : "center",
				"text" : text,
			},
		),
	}

def CategoryButton(name, icon, col, row, kind = "radio_button"):
	return {
		"name" : name,
		"type" : kind,
		"x" : 12 + 34 * col,
		"y" : 5 + 34 * row,
		"default_image" : ROOT + "btn_%s_1.png" % icon,
		"over_image" : ROOT + "btn_%s_2.png" % icon,
		"down_image" : ROOT + "btn_%s_3.png" % icon,
	}

window = {
	"name" : "EkwipunekWindow",

	"x" : SCREEN_WIDTH - 400,
	"y" : 10,

	"style" : ("movable", "float",),

	"width" : WINDOW_WIDTH,
	"height" : WINDOW_HEIGHT,

	"children" :
	(
		{
			"name" : "board",
			"type" : "board",
			"style" : ("attach",),

			"x" : 0,
			"y" : 0,

			"width" : WINDOW_WIDTH,
			"height" : WINDOW_HEIGHT,

			"children" :
			(
				## the settings button (Ameria's ManageInventory)
				{
					"name" : "SeparateBaseImage",
					"type" : "image",
					"style" : ("attach",),

					"x" : 8,
					"y" : 7,

					"image" : ROOT + "settings_1.png",

					"children" :
					(
						{
							"name" : "ManageInventory",
							"type" : "button",

							"x" : 0,
							"y" : 0,

							"default_image" : ROOT + "settings_1.png",
							"over_image" : ROOT + "settings_2.png",
							"down_image" : ROOT + "settings_3.png",
							"disable_image" : ROOT + "settings_3.png",
						},
					),
				},

				## Title
				{
					"name" : "TitleBar",
					"type" : "titlebar",
					"style" : ("attach",),

					"x" : 8 + 38,
					"y" : 7,

					"width" : 161 - 33,

					"color" : "yellow",

					"children" :
					(
						{
							"name" : "TitleName",
							"type" : "text",

							"x" : 77 - 20,
							"y" : 3,

							"text" : "Dodatkowy EQ",
							"text_horizontal_align" : "center"
						},
					),
				},

				## the settings bar: stack, sort, search (Ameria's wndButtonBase)
				{
					"name" : "ManageBar",
					"type" : "image",

					"x" : 12,
					"y" : 30,

					"image" : ROOT + "base_storage.png",

					"children" :
					(
						{
							"name" : "StackButton",
							"type" : "button",

							"x" : 3,
							"y" : 4,

							"default_image" : ROOT + "stack_1.png",
							"over_image" : ROOT + "stack_2.png",
							"down_image" : ROOT + "stack_3.png",
						},
						{
							"name" : "SortButton",
							"type" : "button",

							"x" : 27,
							"y" : 4,

							"default_image" : ROOT + "sort_1.png",
							"over_image" : ROOT + "sort_2.png",
							"down_image" : ROOT + "sort_3.png",
						},
						{
							"name" : "SearchSlot",
							"type" : "image",

							"x" : 52,
							"y" : 4,

							"image" : ROOT + "input.png",

							"children" :
							(
								{
									"name" : "SearchEdit",
									"type" : "editline",

									"x" : 6,
									"y" : 4,

									"width" : 100,
									"height" : 18,

									"input_limit" : 24,
									"placeholder" : "Szukaj..",
								},
							),
						},
					),
				},

				## Item Slot
				{
					"name" : "ItemSlot",
					"type" : "grid_table",

					"x" : 12,
					"y" : 35,

					"start_index" : 0,
					"x_count" : 5,
					"y_count" : 9,
					"x_step" : 32,
					"y_step" : 32,

					"image" : "d:/ymir work/ui/public/Slot_Base.sub"
				},

				PageTab(1, "I", "Strona 1"),
				PageTab(2, "II", "Strona 2"),
				PageTab(3, "III", "Strona 3"),
				PageTab(4, "IV", "Strona 4"),

				{
					"name" : "CategoryBoard",
					"type" : "expanded_image",

					"x" : 12,
					"y" : 350,

					"image" : ROOT + "frame.png",

					"children" :
					(
						CategoryButton("Category_upgrade", "upgrade", 0, 0),
						CategoryButton("Category_stone", "stone", 1, 0),
						CategoryButton("Category_book", "book", 2, 0),
						CategoryButton("Category_bonus", "bonus", 3, 0),
						# MT2009_PLUS_EKWIPUNEK_ROW2_V1: Ameria's second row (chests where its guild button is)
						CategoryButton("Window_costume", "costume", 0, 1, "button"),
						CategoryButton("Category_chest", "chest", 1, 1),
						CategoryButton("Window_alchemy", "alchemy", 2, 1, "button"),
						CategoryButton("Window_itemshop", "ishop", 3, 1, "button"),
					),
				},
			),
		},
	),
}
