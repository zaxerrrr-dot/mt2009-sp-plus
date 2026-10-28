# MT2009_PLUS_SMH_TOWER_V3: GF 26.1.11 uiscript/sungmaheetowerinformationboard.py (the floor board in place of the
# minimap inside the tower - uiwiezasm.py), the exit tooltip as a Polish CP1250 literal; below GF's board our line of
# the stage's blessing / curse (GF's buff_debuff.sub and GF's affect icons
# sungmahee_tower_buff / _debuff.sub as wieza_buff.sub / wieza_debuff.sub, tools/wieza).

PATTERN_PATH		= "d:/ymir work/ui/pattern/"
ROOT_PATH			= "d:/ymir work/ui/game/sungmahee_tower/"

WINDOW_WIDTH		= 136
WINDOW_HEIGHT		= 135 + 30

window = {
	"name" : "SungmaheeTowerInformationBoard",
	"style" : ("float","ltr", ),
	
	"x" : SCREEN_WIDTH - WINDOW_WIDTH,
	"y" : 2,
	
	"width" : WINDOW_WIDTH,
	"height" : WINDOW_HEIGHT,
	
	"children" :
	(
		{
			"name"	: "information_bg",
			"type"	: "image",
			"x"		: 0,
			"y"		: 0,
			"image"	: ROOT_PATH + "information_bg.sub",
		},
		
		## floor text window
		{
			"name" : "floor_text_window", "type" : "window", "style" : ("attach",), "x" : 55, "y" : 37, "width" : 26, "height" : 11,
			"children" :
			(
				{ "name" : "floor_text", "type" : "text", "x" : 0, "y" : 0, "all_align" : "center", "text" : "", "outline" : 1, "color" : 0xFFFFAE00, "fontsize":"LARGE", },
			),
		},
		## stage 1 clear icon
		{
			"name"	: "1stage_clear_icon",
			"style" : ("attach",),
			"type"	: "image",
			"x"		: 16,
			"y"		: 18,
			"image"	: ROOT_PATH + "1stage_clear_icon.sub",
		},
		## stage 2 clear icon
		{
			"name"	: "2stage_clear_icon",
			"style" : ("attach",),
			"type"	: "image",
			"x"		: 47,
			"y"		: 12,
			"image"	: ROOT_PATH + "2stage_clear_icon.sub",
		},
		## stage 3 clear icon
		{
			"name"	: "3stage_clear_icon",
			"style" : ("attach",),
			"type"	: "image",
			"x"		: 88,
			"y"		: 18,
			"image"	: ROOT_PATH + "3stage_clear_icon.sub",
		},
		## alarm text window
		{
			"name" : "alarm_text_window", "type" : "window", "style" : ("attach",), "x" : 21, "y" : 59, "width" : 93, "height" : 11,
			"children" :
			(
				{ "name" : "alarm_text", "type" : "text", "x" : 0, "y" : 0, "all_align" : "center", "text" : "", },
			),
		},
		
		## gauge
		{
			"name"	: "time_gauge",
			"style" : ("attach",),
			"type"	: "expanded_image",
			"x"		: 16,
			"y"		: 78,
			"image"	: ROOT_PATH + "information_gauge.sub",
		},
		
		## time text window
		{
			"name" : "time_text_window", "type" : "window", "style" : ("attach",), "x" : 45, "y" : 80, "width" : 46, "height" : 11,
			"children" :
			(
				{ "name" : "time_text", "type" : "text", "x" : 0, "y" : 0, "all_align" : "center", "text" : "", },
			),
		},
		## exit button
		{
			"name" : "exit_button",
			"type" : "button",
			
			"x" : 54,
			"y" : 99,
			
			"tooltip_text" : "Opu\x9c\xe6 wie\xbf\xea",
			"tooltip_x" : 0,
			"tooltip_y" : 32,
			
			"default_image"	: ROOT_PATH + "exit_button_default.sub",
			"over_image"	: ROOT_PATH + "exit_button_over.sub",
			"down_image"	: ROOT_PATH + "exit_button_down.sub",
		},
		## MT2009_PLUS_SMH_TOWER_V3: the stage's blessing / curse
		{
			"name" : "effect_window", "type" : "window", "x" : 0, "y" : 137, "width" : 136, "height" : 26,
			"children" :
			(
				{ "name" : "effect_bg", "type" : "image", "x" : 15, "y" : 1, "image" : ROOT_PATH + "buff_debuff.sub", },
				{ "name" : "effect_icon", "type" : "expanded_image", "x" : 0, "y" : 2, "image" : ROOT_PATH + "wieza_buff.sub", },
				{ "name" : "effect_text_window", "type" : "window", "style" : ("attach",), "x" : 24, "y" : 6, "width" : 106, "height" : 13,
					"children" :
					(
						{ "name" : "effect_text", "type" : "text", "x" : 0, "y" : 0, "all_align" : "center", "text" : "", },
					),
				},
			),
		},
	),
}
