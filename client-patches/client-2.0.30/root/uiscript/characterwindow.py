import uiScriptLocale
import quest

QUEST_ICON_BACKGROUND = 'd:/ymir work/ui/game/quest/slot_base.sub'

SMALL_VALUE_FILE = "d:/ymir work/ui/public/Parameter_Slot_00.sub"
MIDDLE_VALUE_FILE = "d:/ymir work/ui/public/Parameter_Slot_01.sub"
LARGE_VALUE_FILE = "d:/ymir work/ui/public/Parameter_Slot_03.sub"
ICON_SLOT_FILE = "d:/ymir work/ui/public/Slot_Base.sub"
FACE_SLOT_FILE = "d:/ymir work/ui/game/windows/box_face.sub"
ROOT_PATH = "d:/ymir work/ui/game/windows/"

LOCALE_PATH = uiScriptLocale.WINDOWS_PATH

# MT2009_PLUS_CHAMPION_WINDOW_V1: the status tab in the layout of the 3.0 character window of the global client
# (GF 26.1.11 uiscript/characterwindow.py): the Lv / EXP box (a Champion's level and experience in it), the page
# buttons ordinary stats / Poziom Czempiona with "Bonusy" beside them, the bar with the free points ("+" and the
# number), the stat rows with their icons (the Sung Ma rows in their place on the champion page), HP / PE / atak /
# obrona on the right, the lower block with icons and the tab strip with icons. The pictures are GF's, on
# windows_yohara.dds / tabchar_yohara.tga under our own names (client-2.0.30/atlas/d_: mt2009_*.sub). The window is
# GF's size, 253 x 405. The companion's window keeps the old layout (uiscript/sidekickwindow.py).
WINDOW_HEIGHT = 405
TAB_Y = 368		# GF 371; the strip's picture (37, its last rows its shadow) ends 2 px above the window's bottom, as before
PAGE_HEIGHT = 371
STAT_ROW_Y = 26		# base_info / sungma_info in Status_Standard
STAT_ROW_STEP = 31
PLUS_IMAGES = { "default_image" : ROOT_PATH+"btn_plus_up.sub", "over_image" : ROOT_PATH+"btn_plus_over.sub", "down_image" : ROOT_PATH+"btn_plus_down.sub", }
MINUS_IMAGES = { "default_image" : ROOT_PATH+"btn_minus_up.sub", "over_image" : ROOT_PATH+"btn_minus_over.sub", "down_image" : ROOT_PATH+"btn_minus_down.sub", }

def _Plus(name, x, y):
	element = { "name" : name, "type" : "button", "x" : x, "y" : y, }
	element.update(PLUS_IMAGES)
	return element

def _Minus(name, x, y):
	element = { "name" : name, "type" : "button", "x" : x, "y" : y, }
	element.update(MINUS_IMAGES)
	return element

def _StatRow(slotName, valueName, plusName, imageName, image, row):
	y = row * STAT_ROW_STEP
	return (
		{ "name" : imageName, "type" : "image", "x" : 20, "y" : y - 2, "image" : ROOT_PATH + image },
		{ "name" : slotName, "type" : "image", "x" : 50, "y" : y, "image" : SMALL_VALUE_FILE },
		{ "name" : valueName, "type" : "text", "x" : 70, "y" : y + 3, "text" : "0", "r" : 1.0, "g" : 1.0, "b" : 1.0, "a" : 1.0, "text_horizontal_align" : "center" },
		_Plus(plusName, 91, y + 3),
	)

def _ValueBox(labelName, slotName, valueName, x, y, slotFile, textX):
	return {
		"name" : labelName, "type" : "window", "x" : x, "y" : y, "width" : textX * 2, "height" : 20,
		"children" :
		(
			{ "name" : slotName, "type" : "image", "x" : 0, "y" : 0, "image" : slotFile },
			{ "name" : valueName, "type" : "text", "x" : textX, "y" : 3, "text" : "0", "r" : 1.0, "g" : 1.0, "b" : 1.0, "a" : 1.0, "text_horizontal_align" : "center" },
		),
	}

window = {
	"name" : "CharacterWindow",
	"style" : ("movable", "float",),

	"x" : 24,
	"y" : (SCREEN_HEIGHT - 37 - WINDOW_HEIGHT) / 2,

	"width" : 253,
	"height" : WINDOW_HEIGHT,

	"children" :
	(
		{
			"name" : "board",
			"type" : "board",
			"style" : ("attach",),

			"x" : 0,
			"y" : 0,

			"width" : 253,
			"height" : WINDOW_HEIGHT,

			"children" :
			(
				{
					"name" : "Skill_TitleBar",
					"type" : "titlebar",
					"style" : ("attach",),

					"x" : 8,
					"y" : 7,

					"width" : 238,
					"color" : "red",

					"children" :
					(
						{ "name":"TitleName", "type":"text", "x":0, "y":-1, "text":uiScriptLocale.CHARACTER_SKILL, "all_align":"center" },
					),
				},
				{
					"name" : "Emoticon_TitleBar",
					"type" : "titlebar",
					"style" : ("attach",),

					"x" : 8,
					"y" : 7,

					"width" : 238,
					"color" : "red",

					"children" :
					(
						{ "name":"TitleName", "type":"text", "x":0, "y":-1, "text":uiScriptLocale.CHARACTER_ACTION, "all_align":"center" },
					),
				},
				{
					"name" : "Quest_TitleBar",
					"type" : "titlebar",
					"style" : ("attach",),

					"x" : 8,
					"y" : 7,

					"width" : 238,
					"color" : "red",

					"children" :
					(
						{ "name":"TitleName", "type":"text", "x":0, "y":-1, "text":uiScriptLocale.CHARACTER_QUEST, "all_align":"center" },
					),
				},

				## Tab Area - MT2009_PLUS_CHAMPION_WINDOW_V1: GF's tab strip with icons (karta postaci, miecz, popiersie, zwoj)
				{
					"name" : "TabControl",
					"type" : "window",

					"x" : 0,
					"y" : TAB_Y,

					"width" : 253,
					"height" : 31,

					"children" :
					(
						## Tab
						{ "name" : "Tab_01", "type" : "image", "x" : 0, "y" : 0, "width" : 253, "height" : 31, "image" : ROOT_PATH+"mt2009_char_tab_01.sub", },
						{ "name" : "Tab_02", "type" : "image", "x" : 0, "y" : 0, "width" : 253, "height" : 31, "image" : ROOT_PATH+"mt2009_char_tab_02.sub", },
						{ "name" : "Tab_03", "type" : "image", "x" : 0, "y" : 0, "width" : 253, "height" : 31, "image" : ROOT_PATH+"mt2009_char_tab_03.sub", },
						{ "name" : "Tab_04", "type" : "image", "x" : 0, "y" : 0, "width" : 253, "height" : 31, "image" : ROOT_PATH+"mt2009_char_tab_04.sub", },
						## RadioButton
						{ "name" : "Tab_Button_01", "type" : "radio_button", "x" : 6, "y" : 5, "width" : 53, "height" : 27, },
						{ "name" : "Tab_Button_02", "type" : "radio_button", "x" : 61, "y" : 5, "width" : 67, "height" : 27, },
						{ "name" : "Tab_Button_03", "type" : "radio_button", "x" : 130, "y" : 5, "width" : 61, "height" : 27, },
						{ "name" : "Tab_Button_04", "type" : "radio_button", "x" : 192, "y" : 5, "width" : 55, "height" : 27, },
					),
				},

				## Page Area
				{
					"name" : "Character_Page",
					"type" : "window",
					"style" : ("attach",),

					"x" : 0,
					"y" : 0,

					"width" : 253,
					"height" : PAGE_HEIGHT,

					"children" :
					(

						## Title Area
						{
							"name" : "Character_TitleBar", "type" : "titlebar", "style" : ("attach",), "x" : 61, "y" : 7, "width" : 185, "color" : "red",
							"children" :
							(
								{ "name" : "TitleName", "type":"text", "x":0, "y":-1, "text":uiScriptLocale.CHARACTER_MAIN, "all_align":"center" },
							),
						},

						## Guild Name Slot
						{
							"name" : "Guild_Name_Slot",
							"type" : "image",
							"x" : 63,
							"y" :27+7,
							"image" : LARGE_VALUE_FILE,

							"children" :
							(
								{ "name" : "Guild_Name", "type":"text", "text":"", "x":0, "y":0, "r":1.0, "g":1.0, "b":1.0, "a":1.0, "all_align" : "center", },
							),
						},

						## Character Name Slot
						{
							"name" : "Character_Name_Slot",
							"type" : "image",
							"x" : 153,
							"y" :27+7,
							"image" : LARGE_VALUE_FILE,

							"children" :
							(
								{ "name" : "Character_Name", "type":"text", "text":"", "x":0, "y":0, "r":1.0, "g":1.0, "b":1.0, "a":1.0, "all_align" : "center", },
							),
						},

						## Lv / EXP (GF level_exp_info: the "Lv" and "EXP" coins over the values)
						{ "name":"Lv_Exp_BackImg", "type":"image", "x":9, "y":60, "image":ROOT_PATH+"mt2009_level_exp_info.sub" },
						{ "name":"Lv_ToolTip", "type":"button", "x":9, "y":60, "width":52, "height":44, },
						{ "name":"Exp_ToolTip", "type":"button", "x":61, "y":60, "width":182, "height":44, },

						{ "name":"Level_Value", "type":"text", "x":35, "y":84, "fontsize":"LARGE", "text":"1", "r":1.0, "g":1.0, "b":1.0, "a":1.0, "text_horizontal_align":"center" },
						{
							"name":"Status_CurExp", "type":"window", "x":61, "y":84, "width":92, "height":20,
							"children" :
							(
								{ "name":"Exp_Value", "type":"text", "x":46, "y":0, "fontsize":"LARGE", "text":"0", "r":1.0, "g":1.0, "b":1.0, "a":1.0, "text_horizontal_align":"center" },
							),
						},
						{ "name":"Exp_Slash", "type":"text", "text":"/", "x":153, "y":86, "text_horizontal_align":"center", },
						{
							"name":"Status_RestExp", "type":"window", "x":153, "y":84, "width":92, "height":20,
							"children" :
							(
								{ "name":"RestExp_Value", "type":"text", "x":46, "y":0, "fontsize":"LARGE", "text":"0", "r":1.0, "g":1.0, "b":1.0, "a":1.0, "text_horizontal_align":"center" },
							),
						},

						## Face Slot
						{ "name" : "Face_Image", "type" : "image", "x" : 11, "y" : 11, "image" : "d:/ymir work/ui/game/windows/face_warrior.sub" },
						{ "name" : "Face_Slot", "type" : "image", "x" : 7, "y" : 7, "image" : FACE_SLOT_FILE, },

						## The page buttons - ordinary stats / Poziom Czempiona (GF: 03 the bright one while the page is not open,
						## 01 the pressed one of the open page) - and "Bonusy" (the attribute list) in the place of GF's third button
						{
							"name":"change_base_button", "type":"radio_button", "x":8, "y":107,
							"default_image" : ROOT_PATH+"old_level_btn_03.sub", "over_image" : ROOT_PATH+"old_level_btn_03.sub", "down_image" : ROOT_PATH+"old_level_btn_01.sub",
						},
						{
							"name":"change_conqueror_button", "type":"radio_button", "x":87, "y":107,
							"default_image" : ROOT_PATH+"new_level_btn_03.sub", "over_image" : ROOT_PATH+"new_level_btn_03.sub", "down_image" : ROOT_PATH+"new_level_btn_01.sub",
						},
						{
							"name":"AttributeListButton", "type":"button", "x":166, "y":107,
							"default_image" : ROOT_PATH+"mt2009_passive_expanded_button_01.sub", "over_image" : ROOT_PATH+"mt2009_passive_expanded_button_02.sub", "down_image" : ROOT_PATH+"mt2009_passive_expanded_button_03.sub",
						},

						## The stats
						{
							"name":"Status_Standard", "type":"window", "x":3, "y":125, "width":250, "height":145,
							"children" :
							(
								## the bar: the stats' sign and the free points ("+" and the number)
								{ "name":"Base_Info_bar", "type":"image", "x":6, "y":5, "image":ROOT_PATH+"mt2009_base_info_bar.sub" },
								{ "name":"Char_Info_Status_img", "type":"image", "x":12, "y":7, "image":ROOT_PATH+"mt2009_char_info_status_img.sub" },
								{
									"name":"Status_Plus_Label", "type":"image", "x":191, "y":8, "image":ROOT_PATH+"mt2009_char_info_status_plus_img.sub",
									"children" :
									(
										{ "name":"Status_Plus_Btn_Img", "type":"image", "x":19, "y":0, "image":ROOT_PATH+"mt2009_char_info_status_value_img.sub", },
										{ "name":"Status_Plus_Value", "type":"text", "x":31, "y":-1, "text":"0", "r":1.0, "g":1.0, "b":1.0, "a":1.0, "text_horizontal_align":"center" },
									),
								},

								## the four stats (Witalnosc, Inteligencja, Sila, Zrecznosc)
								{
									"name":"base_info", "type":"window", "x":0, "y":STAT_ROW_Y, "width":115, "height":120,
									"children" :
									_StatRow("HTH_Slot", "HTH_Value", "HTH_Plus", "HTH_IMG", "mt2009_char_info_con.sub", 0) +
									_StatRow("INT_Slot", "INT_Value", "INT_Plus", "INT_IMG", "mt2009_char_info_int.sub", 1) +
									_StatRow("STR_Slot", "STR_Value", "STR_Plus", "STR_IMG", "mt2009_char_info_str.sub", 2) +
									_StatRow("DEX_Slot", "DEX_Value", "DEX_Plus", "DEX_IMG", "mt2009_char_info_dex.sub", 3),
								},

								## the four Sung Ma stats (the champion page)
								{
									"name":"sungma_info", "type":"window", "x":0, "y":STAT_ROW_Y, "width":115, "height":120,
									"children" :
									_StatRow("sungma_str_slot", "sungma_str_value", "sungma_str_plus", "SUNGMA_STR_IMG", "char_info_sungma_str.sub", 0) +
									_StatRow("sungma_hp_slot", "sungma_hp_value", "sungma_hp_plus", "SUNGMA_HP_IMG", "char_info_sungma_hp.sub", 1) +
									_StatRow("sungma_move_slot", "sungma_move_value", "sungma_move_plus", "SUNGMA_MOVE_IMG", "char_info_sungma_move.sub", 2) +
									_StatRow("sungma_immune_slot", "sungma_immune_value", "sungma_immune_plus", "SUNGMA_IMMUNE_IMG", "char_info_sungma_immune.sub", 3),
								},

								## the minus buttons (a stat reset item), left of the icons
								_Minus("HTH_Minus", 5, STAT_ROW_Y + 3),
								_Minus("INT_Minus", 5, STAT_ROW_Y + 3 + STAT_ROW_STEP),
								_Minus("STR_Minus", 5, STAT_ROW_Y + 3 + STAT_ROW_STEP * 2),
								_Minus("DEX_Minus", 5, STAT_ROW_Y + 3 + STAT_ROW_STEP * 3),

								## P.Z., P.E., atak, obrona
								{ "name":"HEL_IMG", "type":"image", "x":118, "y":STAT_ROW_Y - 2, "image":ROOT_PATH+"mt2009_char_info_hp.sub" },
								{ "name":"SP_IMG", "type":"image", "x":118, "y":STAT_ROW_Y - 2 + STAT_ROW_STEP, "image":ROOT_PATH+"mt2009_char_info_sp.sub" },
								{ "name":"ATT_IMG", "type":"image", "x":118, "y":STAT_ROW_Y - 2 + STAT_ROW_STEP * 2, "image":ROOT_PATH+"mt2009_char_info_att.sub" },
								{ "name":"DEF_IMG", "type":"image", "x":118, "y":STAT_ROW_Y - 2 + STAT_ROW_STEP * 3, "image":ROOT_PATH+"mt2009_char_info_def.sub" },
								_ValueBox("HEL_Label", "HP_Slot", "HP_Value", 145, STAT_ROW_Y, LARGE_VALUE_FILE, 45),
								_ValueBox("SP_Label", "SP_Slot", "SP_Value", 145, STAT_ROW_Y + STAT_ROW_STEP, LARGE_VALUE_FILE, 45),
								_ValueBox("ATT_Label", "ATT_Slot", "ATT_Value", 145, STAT_ROW_Y + STAT_ROW_STEP * 2, LARGE_VALUE_FILE, 45),
								_ValueBox("DEF_Label", "DEF_Slot", "DEF_Value", 145, STAT_ROW_Y + STAT_ROW_STEP * 3, LARGE_VALUE_FILE, 45),
							),
						},

						## The lower block: ruch, atak, czarowanie (speeds) | atak magiczny, obrona magiczna, precyzja
						{
							"name":"Status_Extent", "type":"window", "x":3, "y":270, "width":250, "height":100,
							"children" :
							(
								{ "name":"Status_Extent_Label", "type":"image", "x":13, "y":0, "image":ROOT_PATH+"mt2009_status_extent_bar.sub", },

								{ "name":"MSPD_IMG", "type":"image", "x":20, "y":6, "image":ROOT_PATH+"mt2009_char_info_movespeed.sub" },
								{ "name":"ASPD_IMG", "type":"image", "x":20, "y":6 + STAT_ROW_STEP, "image":ROOT_PATH+"mt2009_char_info_attspeed.sub" },
								{ "name":"CSPD_IMG", "type":"image", "x":20, "y":6 + STAT_ROW_STEP * 2, "image":ROOT_PATH+"mt2009_char_info_magspeed.sub" },
								{ "name":"MATT_IMG", "type":"image", "x":118, "y":6, "image":ROOT_PATH+"mt2009_char_info_magatt.sub" },
								{ "name":"MDEF_IMG", "type":"image", "x":118, "y":6 + STAT_ROW_STEP, "image":ROOT_PATH+"mt2009_char_info_magdef.sub" },
								{ "name":"ER_IMG", "type":"image", "x":118, "y":6 + STAT_ROW_STEP * 2, "image":ROOT_PATH+"mt2009_char_info_hitpct.sub" },

								_ValueBox("MOV_Label", "MSPD_Slot", "MSPD_Value", 50, 8, MIDDLE_VALUE_FILE, 26),
								_ValueBox("ASPD_Label", "ASPD_Slot", "ASPD_Value", 50, 8 + STAT_ROW_STEP, MIDDLE_VALUE_FILE, 26),
								_ValueBox("CSPD_Label", "CSPD_Slot", "CSPD_Value", 50, 8 + STAT_ROW_STEP * 2, MIDDLE_VALUE_FILE, 26),
								_ValueBox("MATT_Label", "MATT_Slot", "MATT_Value", 148, 8, MIDDLE_VALUE_FILE, 26),
								_ValueBox("MDEF_Label", "MDEF_Slot", "MDEF_Value", 148, 8 + STAT_ROW_STEP, MIDDLE_VALUE_FILE, 26),
								_ValueBox("ER_Label", "ER_Slot", "ER_Value", 148, 8 + STAT_ROW_STEP * 2, MIDDLE_VALUE_FILE, 26),
							),
						},
					),
				},
				{
					"name" : "Skill_Page",
					"type" : "window",
					"style" : ("attach",),

					"x" : 0,
					"y" : 24,

					"width" : 250,
					"height" : 304,

					"children" :
					(

						{
							"name":"Skill_Active_Title_Bar", "type":"horizontalbar", "x":15, "y":17, "width":223,

							"children" :
							(
								{
									"name":"Active_Skill_Point_Label", "type":"image", "x":145, "y":3, "image":LOCALE_PATH+"label_uppt.sub",
									"children" :
									(
										{ "name":"Active_Skill_Point_Value", "type":"text", "x":62, "y":0, "text":"99", "r":1.0, "g":1.0, "b":1.0, "a":1.0, "text_horizontal_align":"center" },
									),
								},

								## Group Button
								{
									"name" : "Skill_Group_Button_1",
									"type" : "radio_button",

									"x" : 5,
									"y" : 2,

									"text" : "Group1",
									"text_color" : 0xFFFFE3AD,

									"default_image" : "d:/ymir work/ui/game/windows/skill_tab_button_01.sub",
									"over_image" : "d:/ymir work/ui/game/windows/skill_tab_button_02.sub",
									"down_image" : "d:/ymir work/ui/game/windows/skill_tab_button_03.sub",
								},

								{
									"name" : "Skill_Group_Button_2",
									"type" : "radio_button",

									"x" : 50,
									"y" : 2,

									"text" : "Group2",
									"text_color" : 0xFFFFE3AD,

									"default_image" : "d:/ymir work/ui/game/windows/skill_tab_button_01.sub",
									"over_image" : "d:/ymir work/ui/game/windows/skill_tab_button_02.sub",
									"down_image" : "d:/ymir work/ui/game/windows/skill_tab_button_03.sub",
								},

								{
									"name" : "Active_Skill_Group_Name",
									"type" : "text",

									"x" : 7,
									"y" : 1,
									"text" : "Active",

									"vertical_align" : "center",
									"text_vertical_align" : "center",
									"color" : 0xFFFFE3AD,
								},

							),
						},

						{
							"name":"Skill_ETC_Title_Bar", "type":"horizontalbar", "x":15, "y":200, "width":223,

							"children" :
							(
								{
									"name" : "Support_Skill_Group_Name",
									"type" : "text",

									"x" : 7,
									"y" : 1,
									"text" : uiScriptLocale.SKILL_SUPPORT_TITLE,

									"vertical_align" : "center",
									"text_vertical_align" : "center",
									"color" : 0xFFFFE3AD,
								},

								{
									"name":"Support_Skill_Point_Label", "type":"image", "x":145, "y":3, "image":LOCALE_PATH+"label_uppt.sub",
									"children" :
									(
										{ "name":"Support_Skill_Point_Value", "type":"text", "x":62, "y":0, "text":"99", "r":1.0, "g":1.0, "b":1.0, "a":1.0, "text_horizontal_align":"center" },
									),
								},
							),
						},
						{ "name":"Skill_Board", "type":"image", "x":13, "y":38, "image":"d:/ymir work/ui/game/windows/skill_board.sub", },

						## Active Slot
						{
							"name" : "Skill_Active_Slot",
							"type" : "slot",

							"x" : 0 + 16,
							"y" : 0 + 15 + 23,

							"width" : 223,
							"height" : 223,
							"image" : ICON_SLOT_FILE,

							"slot" :	(
											{"index": 1, "x": 1, "y":  4, "width":32, "height":32},
											{"index":21, "x":38, "y":  4, "width":32, "height":32},
											{"index":41, "x":75, "y":  4, "width":32, "height":32},

											{"index": 3, "x": 1, "y": 40, "width":32, "height":32},
											{"index":23, "x":38, "y": 40, "width":32, "height":32},
											{"index":43, "x":75, "y": 40, "width":32, "height":32},

											{"index": 5, "x": 1, "y": 76, "width":32, "height":32},
											{"index":25, "x":38, "y": 76, "width":32, "height":32},
											{"index":45, "x":75, "y": 76, "width":32, "height":32},

											{"index": 7, "x": 1, "y":112, "width":32, "height":32},
											{"index":27, "x":38, "y":112, "width":32, "height":32},
											{"index":47, "x":75, "y":112, "width":32, "height":32},

											####

											{"index": 2, "x":113, "y":  4, "width":32, "height":32},
											{"index":22, "x":150, "y":  4, "width":32, "height":32},
											{"index":42, "x":187, "y":  4, "width":32, "height":32},

											{"index": 4, "x":113, "y": 40, "width":32, "height":32},
											{"index":24, "x":150, "y": 40, "width":32, "height":32},
											{"index":44, "x":187, "y": 40, "width":32, "height":32},

											{"index": 6, "x":113, "y": 76, "width":32, "height":32},
											{"index":26, "x":150, "y": 76, "width":32, "height":32},
											{"index":46, "x":187, "y": 76, "width":32, "height":32},

											{"index": 8, "x":113, "y":112, "width":32, "height":32},
											{"index":28, "x":150, "y":112, "width":32, "height":32},
											{"index":48, "x":187, "y":112, "width":32, "height":32},
										),
						},

						## ETC Slot
						{
							"name" : "Skill_ETC_Slot",
							"type" : "grid_table",
							"x" : 18,
							"y" : 221,
							"start_index" : 101,
							"x_count" : 6,
							"y_count" : 2,
							"x_step" : 32,
							"y_step" : 32,
							"x_blank" : 5,
							"y_blank" : 4,
							"image" : ICON_SLOT_FILE,
						},

						{
							"name": "SprintOnboardingTint",
							"type": "bar",
							"x": 0, "y": 0,
							"horizontal_align": "center",
							"width": 253 - 15, "height": 361 - 26,
							"color": 0x94000000,
							"children": (
								{
									"type": "text",
									"x": 0, "y": 0,
									"all_align": "center",
									"fontsize": "LARGE",
									"bold": True,
									"text": uiScriptLocale.SPRINT_ONBOARDING,
								},
								{
									"name": "SprintOnboardingIcon",
									"type": "image",
									"x": 18 + 4 * 32 + 3 * 5 - 1, "y": 221,
									"image": "d:/ymir work/ui/skill/common/support/sprint.sub",
								},
							)
						},

					),
				},
				{
					"name" : "Emoticon_Page",
					"type" : "window",
					"style" : ("attach",),

					"x" : 0,
					"y" : 24,

					"width" : 250,
					"height" : 304,

					"children" :
					(
						{ "name":"Action_Bar", "type":"horizontalbar", "x":12, "y":11, "width":223, },
						{ "name":"Action_Bar_Text", "type":"text", "x":15, "y":13, "text":uiScriptLocale.CHARACTER_NORMAL_ACTION },

						## Basis Action Slot
						{
							"name" : "SoloEmotionSlot",
							"type" : "grid_table",
							"x" : 30,
							"y" : 33,
							"horizontal_align" : "center",
							"start_index" : 1,
							"x_count" : 6,
							"y_count" : 3,
							"x_step" : 32,
							"y_step" : 32,
							"x_blank" : 0,
							"y_blank" : 0,
							"image" : ICON_SLOT_FILE,
						},

						{ "name":"Reaction_Bar", "type":"horizontalbar", "x":12, "y":8+150, "width":223, },
						{ "name":"Reaction_Bar_Text", "type":"text", "x":15, "y":10+150, "text":uiScriptLocale.CHARACTER_MUTUAL_ACTION },

						## Reaction Slot
						{
							"name" : "DualEmotionSlot",
							"type" : "grid_table",
							"x" : 30,
							"y" : 180,
							"start_index" : 51,
							"x_count" : 6,
							"y_count" : 3,
							"x_step" : 32,
							"y_step" : 32,
							"x_blank" : 0,
							"y_blank" : 0,
							"image" : ICON_SLOT_FILE,
						},
					),
				},
				{
					"name" : "Quest_Page",
					"type" : "window",
					"style" : ("attach",),

					"x" : 0,
					"y" : 24,

					"width" : 282,
					"height" : 304,

					"children" :
					(
						{
							"name" : "Quest_BG",
							"type" : "window",
							"x": 0,
							"y": 0,
							"width" : 0,
							"height" : 0,
						},

						{
							"name" : "Quest_Slot",
							"type" : "grid_table",
							"x" : 18,
							"y" : 17,
							"start_index" : 0,
							"x_count" : 1,
							"y_count" : quest.QUEST_MAX_NUM,
							"x_step" : 32,
							"y_step" : 32,
							"y_blank" : 9,
							"image" : QUEST_ICON_BACKGROUND,
						},

						{
							"name" : "Quest_ScrollBar",
							"type" : "scrollbar",

							"x" : 57,
							"y" : 12,
							"size" : 290,
							"horizontal_align" : "right",
						},
					),
				},
			),
		},
	),
}
