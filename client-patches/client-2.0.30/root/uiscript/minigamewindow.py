# MT2009_PLUS_FISH_PUZZLE_V2: the event banner window (the package "Mini Game Fish Event (17.3)"); left of the event hub's "E" button
# beside the minimap (the package's x put the banner under it).
import uiScriptLocale

window = {
	"name" : "MiniGameWindow",
	"style" : ("not_pick",),	# only the banner takes clicks (an empty corner does not block the map)
	
	"x" : SCREEN_WIDTH - 136 - 100 - 44,
	"y" : 15,
	
	"width" : 100,
	"height" : 58,
	
	"children" :
	(
		{
			"name" : "mini_game_window",
			"type" : "window",
			"style" : ("not_pick",),
			
			"x" : 0,
			"y" : 0,
			
			"width" : 100,
			"height" : 58,
		},		
	),	
}
