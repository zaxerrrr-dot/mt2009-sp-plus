# MT2009_PLUS_GAYA_CURRENCY_V1: the money bar of the owner's package "Expanded Money Taskbar" (cache/gaya2/emt,
# uiscript/expandedmoneytaskbar.py) - Won (only with constInfo.ENABLE_WON), Gaya and Yang side by side, over the
# taskbar's right end; opened by the taskbar button of gayacurrency.py. The package's layout counted on the exe's
# ENABLE_CHEQUE_SYSTEM / ENABLE_GEM_SYSTEM; here the row is laid out from the left for whichever currencies are on.
# Images: the client pack "gaya2" (d:/ymir work/ui/gaya2/, client-2.0.30/tools/gaya2) and the base money icon.
import utils

GAYA2_UI = "d:/ymir work/ui/gaya2/"
# a uiscript may not import constInfo (ui.PythonScriptLoader's sandbox) - utils, which may, holds it
WON = getattr(getattr(utils, "constInfo", None), "ENABLE_WON", 0)

children = []
cursor = 12

if WON:
	children += [
		{"name" : "Won_Icon", "type" : "image", "x" : cursor, "y" : 12, "image" : "d:/ymir work/ui/game/windows/cheque_icon.sub"},
		{"name" : "Won_Slot", "type" : "image", "x" : cursor + 19, "y" : 11, "image" : GAYA2_UI + "cheque_slot.sub",
			"children" : ({"name" : "Won", "type" : "text", "x" : 3, "y" : 3, "horizontal_align" : "right",
				"text_horizontal_align" : "right", "text" : "0"},)},
	]
	cursor += 19 + 24 + 8

children += [
	{"name" : "Gaya_Icon", "type" : "image", "x" : cursor, "y" : 14, "image" : GAYA2_UI + "gaya_icon.tga"},
	{"name" : "Gaya_Slot", "type" : "image", "x" : cursor + 16, "y" : 11, "image" : GAYA2_UI + "gaya_slot.sub",
		"children" : ({"name" : "Gaya", "type" : "text", "x" : 3, "y" : 3, "horizontal_align" : "right",
			"text_horizontal_align" : "right", "text" : "0"},)},
]
cursor += 16 + 52 + 8

children += [
	{"name" : "Money_Icon", "type" : "image", "x" : cursor, "y" : 12, "image" : "d:/ymir work/ui/game/windows/money_icon.sub"},
	{"name" : "Money_Slot", "type" : "image", "x" : cursor + 19, "y" : 11, "image" : GAYA2_UI + "gold_slot.sub",
		"children" : ({"name" : "Money", "type" : "text", "x" : 3, "y" : 3, "horizontal_align" : "right",
			"text_horizontal_align" : "right", "text" : "0"},)},
]
cursor += 19 + 90 + 12

BOARD_WIDTH = cursor
BOARD_HEIGHT = 40

window = {
	"name" : "ExpandedMoneyTaskbar",
	"x" : SCREEN_WIDTH - BOARD_WIDTH - 4,
	"y" : SCREEN_HEIGHT - 37 - BOARD_HEIGHT - 2,
	"width" : BOARD_WIDTH,
	"height" : BOARD_HEIGHT,
	"style" : ("movable", "float",),
	"children" :
	(
		{
			"name" : "ExpandedMoneyTaskBar_Board",
			"type" : "board",
			"style" : ("attach",),
			"x" : 0,
			"y" : 0,
			"width" : BOARD_WIDTH,
			"height" : BOARD_HEIGHT,
			"children" : tuple(children),
		},
	),
}
