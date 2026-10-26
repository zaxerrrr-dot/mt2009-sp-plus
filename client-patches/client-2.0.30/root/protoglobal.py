# MT2009_PLUS_GLOBAL_PROTO_V1: the fixed item bonuses of the server's M2_BONUS_MODE=global in the tooltips (the owner's
# list of 15 October 2026, item 19: Bambusowe Buty+9 - movement 15 and fire resistance 10 instead of movement 25 and
# max stamina 800). The client's item_proto carries the mt2009 values; "BonusMode 1" at login (game.py) loads
# gamedata/item_proto_global over the table (the same items with the global applies - every record the client has of the global list,
# client-patches/client-2.0.30/tools/protoglobal), "BonusMode 0" loads gamedata/item_proto_mt2009 back.
# A client without the files (an old pack) keeps its table.
#
# MT2009_PLUS_GLOBAL_PROTO_V2: the global values were lost after a relog. Every character select
# (networkModule.SetSelectCharacterPhase -> localeInfo.LoadLocaleData -> app.LoadLocaleData) destroys the item
# table and reads the base gamedata/item_proto again, while V1 still remembered "global is loaded" and skipped the
# next "BonusMode 1". Now:
#   * localeInfo.LoadLocaleData calls BaseTableReloaded() - the table is the base (mt2009) one again;
#   * "BonusMode 1" loads the global records every time (the quest sends it once per enter-game: login, relog,
#     warp, channel change - a small file, never per frame), so nothing can leave the base values in place;
#   * "BonusMode 0" loads the mt2009 records back only when the global ones may be over the table.
import item

FILES = ("gamedata/item_proto_mt2009", "gamedata/item_proto_global")
current = [0]


def BaseTableReloaded():
	current[0] = 0


def SetBonusMode(isGlobal):
	want = 1 if isGlobal else 0
	if want == 0 and current[0] == 0:
		return
	try:
		item.LoadItemTable(FILES[want])
	except Exception:
		return
	current[0] = want
