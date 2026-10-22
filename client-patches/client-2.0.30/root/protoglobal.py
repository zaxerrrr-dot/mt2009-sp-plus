# MT2009_PLUS_GLOBAL_PROTO_V1: the fixed item bonuses of the server's M2_BONUS_MODE=global in the tooltips (the owner's
# list of 15 October 2026, item 19: Bambusowe Buty+9 - movement 15 and fire resistance 10 instead of movement 25 and
# max stamina 800). The client's item_proto carries the mt2009 values; "BonusMode 1" at login (game.py) loads
# gamedata/item_proto_global over the table (the same items with the global applies - every record the client has of the global list,
# client-patches/client-2.0.30/tools/protoglobal), "BonusMode 0" loads gamedata/item_proto_mt2009 back - only when
# the mode changes (the client starts in mt2009). A client without the files (an old pack) keeps its table.
import item

FILES = ("gamedata/item_proto_mt2009", "gamedata/item_proto_global")
current = [0]


def SetBonusMode(isGlobal):
	want = 1 if isGlobal else 0
	if want == current[0]:
		return
	try:
		item.LoadItemTable(FILES[want])
	except Exception:
		return
	current[0] = want
