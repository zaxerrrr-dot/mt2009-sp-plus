# MT2009_PLUS_KOLEKCJONER_NAJEMNIKOW_V1: Kolekcjoner Najemnikow's window frame - our dark board only; root/uinajemnicykolekcjoner.py
# draws the rest on it in the layout of the owner's reference picture (8 November 2026): the title "KOLEKCJONER"
# between two diamonds and the close button, the tab, the tasks on the left, the selected task's item tiles in the
# middle, the selected item's panel with the gold "Oddaj" on the right, the category's bonus at the bottom.
# The size is the module's WIDTH / HEIGHT.
WINDOW_WIDTH = 760
WINDOW_HEIGHT = 500

window = {
	"name" : "KolekcjonerNajemnikowWindow",
	"style" : ("movable", "float",),

	"x" : SCREEN_WIDTH / 2 - WINDOW_WIDTH / 2,
	"y" : SCREEN_HEIGHT / 2 - WINDOW_HEIGHT / 2,

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
		},
	),
}
