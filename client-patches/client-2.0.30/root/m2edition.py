# MT2009_CLASSIC_EDITION_V1: the edition this client is. MT2009 PLUS ships
# "plus"; the MT2009 Classic client's root pack has "classic" here, and its
# windows then show no button, key or window of a system Classic leaves out
# (costumes, pets, mounts, alchemy, sashes, Battle Pass, the Wheel, the event
# calendar, the weekly ranking, the companion, the saved positions, "Usun
# misje", the collector's storage).
EDITION = "plus"
CLASSIC = (EDITION == "classic")

# The keybind actions and inventory sidebar buttons Classic has none of.
CLASSIC_ACTIONS = ("dragon_soul", "companion", "event_calendar", "wheel", "new_pet",
	"battle_pass", "tp_bookmarks", "weekly_rank", "unmount")
CLASSIC_SIDEBAR = ("companion", "battlepass", "calendar", "wheel", "teleport",
	"missions", "ranking")
