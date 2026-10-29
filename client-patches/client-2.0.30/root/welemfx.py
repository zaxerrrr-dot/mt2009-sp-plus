# MT2009_PLUS_WEAPON_ELEMENT_V1: Zaczarowanie Zywiolu Broni - the element's effect on the weapons of the characters in
# view (server-patches/zywiolbroni; the exe's side: client-patches/exe/UserInterface/Mt2009WeaponElement.cpp).
# The server says "WELEMFX <vid> <type>" (game.py -> OnServer) when a character with an enchant +3 on a weapon with its
# refine "stars" comes into view or changes (type 0 none, 1 Blyskawica, 2 Ogien, 3 Lod, 4 Wiatr, 5 Ziemia, 6 Mrok).
# The 3.x exe with chrmgr.SetWeaponElement draws it (only while the weapon shows its refine effect); an older exe has
# no such function and nothing happens.
import chrmgr

# our element number -> the GF effect file's stem (d:/ymir work/pc/common/effect/sword/)
ELEMENT_FILES = {
	1: "element01_electric",
	2: "element02_fire",
	3: "element03_ice",
	4: "element04_wind",
	5: "element05_daeji",
	6: "element06_dark",
}
# the exe's weapon kinds -> the file's suffix (as the refine effects sword_7*.mse): 0 sword / two-handed,
# 1 fan, 2 bow (left hand), 3 dagger (both hands) / bell, 4 claw (both hands)
KIND_SUFFIX = {0: "", 1: "_f", 2: "_b", 3: "_s", 4: "_w"}
EFFECT_PATH = "d:/ymir work/pc/common/effect/sword/%s%s.mse"

_state = {"registered": False}


def Available():
	return hasattr(chrmgr, "SetWeaponElement") and hasattr(chrmgr, "RegisterWeaponElementEffect")


def Register():
	"""the 30 effect files, once (the exe keeps them)"""
	if _state["registered"]:
		return True
	if not Available():
		return False
	try:
		for (elem, stem) in ELEMENT_FILES.items():
			for (kind, suffix) in KIND_SUFFIX.items():
				chrmgr.RegisterWeaponElementEffect(elem, kind, EFFECT_PATH % (stem, suffix))
	except Exception:
		return False
	_state["registered"] = True
	return True


def OnServer(vid="0", elem="0", *rest):
	"""WELEMFX <vid> <type>: the element shown on that character's weapon (0: none)"""
	try:
		vid = int(vid)
		elem = int(elem)
	except (TypeError, ValueError):
		return
	if elem < 0 or elem > 6:
		elem = 0
	if not Register():
		return
	try:
		chrmgr.SetWeaponElement(vid, elem)
	except Exception:
		pass
