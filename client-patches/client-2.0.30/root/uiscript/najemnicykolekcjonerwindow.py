# MT2009_PLUS_KOLEKCJONER_NAJEMNIKOW_V1 / MT2009_PLUS_NAJEMNICY_V5: Kolekcjoner Najemnikow's window frame - a board with
# a title bar, as "Sesja farmienia" (uifarmsession.py); root/uinajemnicykolekcjoner.py draws the rest on it: the row of
# flat tabs ("Kolekcjoner", "Najemnicy") and their pages of framed columns. The close button of the title bar closes it
# (the module sets its event). The size is the module's WIDTH / HEIGHT.
WINDOW_WIDTH = 760
WINDOW_HEIGHT = 520

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
			"type" : "board_with_titlebar",
			"style" : ("attach",),

			"x" : 0,
			"y" : 0,

			"width" : WINDOW_WIDTH,
			"height" : WINDOW_HEIGHT,

			"title" : "Kolekcjoner Najemnik\xf3w",
		},
	),
}
