# MT2009_PLUS_TOOLTIP_MODEL_PREVIEW_V1 - the item tooltip's 3D preview (the owner, 10 November 2026, with his "Render
# Target 2.0 edit by Volvox" package: "when hovering an item ... for wearable items - armour, weapons, costumes, sashes,
# mounts, pets - the tooltip shows a preview window with a character of the PLAYER'S OWN race and sex wearing that
# item"). A small board next to the tooltip (right of it; left when there is no room - ALT's compare tooltip stands on
# the left) with the model in it, turning slowly:
#   weapon / weapon skin      the player's race holding it, in the armour (or costume) it wears now
#   armour / body costume     the player's race in it, with the weapon it holds now (when the race can hold it)
#   hair costume, sash, aura  the player's race with it, in its armour and with its weapon
#   mount / pet               the mount's / pet's own model
# An item the player's class or sex cannot wear: the same sex of a class that can, else any race that can (the race
# Volvox's __ItemGetRace picks the same way). Refine glow and the shining table come with the model (the exe draws the
# attached effects - Mt2009WikiModel.cpp, module renderTarget).
# Off with Esc > Opcje Gry > Dodatkowe "Wylacz podglad modelu w opisie przedmiotu" (the package's DISABLE_MODEL_PREVIEW,
# uiopcjedodatkowe.py "modelpreview_off"); an exe without renderTarget shows nothing.
# One-line hooks in uitooltip.py ItemToolTip (OnUpdate / HideToolTip / ClearToolTip), as digiqol's compare tooltip.
# Python 2.7 as the client has it; texts CP1250 as escapes.
import app
import chr
import item
import player
import ui
import wndMgr
from _weakref import proxy

try:
	import renderTarget
except ImportError:
	renderTarget = None
try:
	import wikipedia
except ImportError:
	wikipedia = None

PREVIEW_W = 190
PREVIEW_H = 230
BOARD_PAD = 6
TITLE_H = 18
BACKGROUND = "d:/ymir work/ui/game/wiki/preview_back.tga"
TITLE = "Podgl\xb9d"

# wikipedia's costume categories (gen_wiki_data.py CO lines)
CO_WEAPON, CO_BODY, CO_HAIR, CO_SASH, CO_SASH_COSTUME, CO_MOUNT, CO_PET, CO_AURA = range(8)

# races: job = race % 4; sex as chr.RaceToSex (1 male)
_JOB_FLAGS = None


def Available():
	return renderTarget is not None and hasattr(wndMgr, "RegisterRenderTarget")


def _Disabled():
	try:
		return bool(__import__("uiopcjedodatkowe").Settings().get("modelpreview_off"))
	except Exception:
		return False


def _JobFlag(job):
	global _JOB_FLAGS
	if _JOB_FLAGS is None:
		_JOB_FLAGS = {0: item.ITEM_ANTIFLAG_WARRIOR, 1: item.ITEM_ANTIFLAG_ASSASSIN, 2: item.ITEM_ANTIFLAG_SURA,
			3: item.ITEM_ANTIFLAG_SHAMAN}
	return _JOB_FLAGS.get(job, 0)


def _CanWear(race):
	"""the selected item (item.SelectItem) on a race"""
	flag = _JobFlag(chr.RaceToJob(race))
	if flag and item.IsAntiFlag(flag):
		return False
	sex = chr.RaceToSex(race)
	if item.IsAntiFlag(item.ITEM_ANTIFLAG_MALE) and sex == 1:
		return False
	if item.IsAntiFlag(item.ITEM_ANTIFLAG_FEMALE) and sex == 0:
		return False
	return True


def PickRace(vnum, own=None):
	"""the player's own race when it can wear the item, else the same sex of a class that can, else any"""
	if own is None:
		try:
			own = player.GetRace()
		except Exception:
			own = 0
	item.SelectItem(vnum)
	if _CanWear(own):
		return own
	sex = chr.RaceToSex(own)
	others = [race for race in xrange(8) if race != own]
	for race in others:
		if chr.RaceToSex(race) == sex and _CanWear(race):
			return race
	for race in others:
		if _CanWear(race):
			return race
	return own


def _Worn(slot):
	try:
		return player.GetItemIndex(slot)
	except Exception:
		return 0


def _WornArmor():
	vnum = 0
	for slot in (getattr(item, "COSTUME_SLOT_BODY", -1), getattr(item, "EQUIPMENT_BODY", -1)):
		if slot >= 0:
			vnum = _Worn(slot)
			if vnum:
				return vnum
	return 0


def _WornWeapon():
	for slot in (getattr(item, "COSTUME_SLOT_WEAPON", -1), getattr(item, "EQUIPMENT_WEAPON", -1)):
		if slot >= 0:
			vnum = _Worn(slot)
			if vnum:
				return vnum
	return 0


def _CostumeInfo(vnum):
	if not wikipedia:
		return None
	try:
		return wikipedia.GetCostumeInfo(vnum)
	except Exception:
		return None


def ModelOf(vnum):
	"""(race, armour, weapon, hairItem, sash, aura) of the preview of an item, or None (nothing to show)"""
	if not vnum:
		return None
	if wikipedia and hasattr(wikipedia, "ItemExists") and not wikipedia.ItemExists(vnum):
		return None
	try:
		item.SelectItem(vnum)
		itemType = item.GetItemType()
		subType = item.GetItemSubType()
	except Exception:
		return None
	info = _CostumeInfo(vnum)
	if info:
		cat, preview = info
		if cat in (CO_MOUNT, CO_PET):
			return (preview, 0, 0, 0, 0, 0) if preview else None
		kind = {CO_WEAPON: "weapon", CO_BODY: "armor", CO_HAIR: "hair", CO_SASH: "sash", CO_SASH_COSTUME: "sash",
			CO_AURA: "aura"}.get(cat)
	elif itemType == item.ITEM_TYPE_WEAPON and subType not in (getattr(item, "WEAPON_ARROW", -1), getattr(item, "WEAPON_QUIVER", -1)):
		kind = "weapon"
	elif itemType == item.ITEM_TYPE_ARMOR and subType == item.ARMOR_BODY:
		kind = "armor"
	elif itemType == getattr(item, "ITEM_TYPE_COSTUME", -1):
		kind = {getattr(item, "COSTUME_TYPE_BODY", -1): "armor", getattr(item, "COSTUME_TYPE_HAIR", -1): "hair",
			getattr(item, "COSTUME_TYPE_WEAPON", -1): "weapon", getattr(item, "COSTUME_TYPE_ACCE", -1): "sash"}.get(subType)
	else:
		kind = None
	if not kind:
		return None
	race = PickRace(vnum)
	own = race == player.GetRace()
	armor = _WornArmor() if own else 0
	weapon = _WornWeapon() if own else 0
	if weapon:
		item.SelectItem(weapon)
		if not _CanWear(race):
			weapon = 0
	if kind == "weapon":
		return (race, armor, vnum, 0, 0, 0)
	if kind == "armor":
		return (race, vnum, weapon, 0, 0, 0)
	if kind == "hair":
		return (race, armor, weapon, vnum, 0, 0)
	if kind == "sash":
		return (race, armor, weapon, 0, vnum, 0)
	if kind == "aura":
		return (race, armor, weapon, 0, 0, vnum)
	return None


class _RenderTarget(ui.Window):
	def RegisterWindow(self, layer):
		self.hWnd = wndMgr.RegisterRenderTarget(self, layer)

	def SetRenderTarget(self, index):
		wndMgr.SetRenderTarget(self.hWnd, index)


class PreviewBoard(ui.Window):
	def __init__(self):
		ui.Window.__init__(self, "TOP_MOST")
		self.AddFlag("not_pick")
		self.AddFlag("float")
		self.board = ui.ThinBoard()
		self.board.SetParent(self)
		self.board.AddFlag("not_pick")
		self.board.SetSize(PREVIEW_W + BOARD_PAD * 2, PREVIEW_H + TITLE_H + BOARD_PAD * 2)
		self.board.SetPosition(0, 0)
		self.board.Show()
		self.title = ui.TextLine()
		self.title.SetParent(self.board)
		self.title.AddFlag("not_pick")
		self.title.SetOutline()
		self.title.SetPackedFontColor(0xffc8aa80)
		self.title.SetHorizontalAlignCenter()
		self.title.SetPosition((PREVIEW_W + BOARD_PAD * 2) // 2, BOARD_PAD)
		self.title.SetText(TITLE)
		self.title.Show()
		self.index = renderTarget.GetFreeIndex(9000, 9100)
		renderTarget.SetBackground(self.index, BACKGROUND)
		renderTarget.SetRotation(self.index, 1)
		self.view = _RenderTarget()
		self.view.SetParent(self.board)
		self.view.AddFlag("not_pick")
		self.view.SetPosition(BOARD_PAD, BOARD_PAD + TITLE_H)
		self.view.SetSize(PREVIEW_W, PREVIEW_H)
		self.view.SetRenderTarget(self.index)
		self.view.Show()
		self.SetSize(PREVIEW_W + BOARD_PAD * 2, PREVIEW_H + TITLE_H + BOARD_PAD * 2)
		self.model = None
		self.owner = None

	def SetOwner(self, tooltip):
		try:
			self.owner = proxy(tooltip)
		except TypeError:
			self.owner = tooltip

	# a tooltip hidden with Hide() (not HideToolTip) takes its preview along
	def OnUpdate(self):
		try:
			if self.owner is None or not self.owner.IsShow():
				self.Hide()
		except ReferenceError:
			self.owner = None
			self.Hide()

	def __del__(self):
		ui.Window.__del__(self)

	def Destroy(self):
		if self.index >= 0:
			renderTarget.Destroy(self.index)
			self.index = -1

	def SetModel(self, model):
		if model == self.model:
			return True
		self.model = model
		ok = renderTarget.SetModel(self.index, *model)
		if ok:
			renderTarget.SetVisibility(self.index, 1)
		return ok


_board = [None]
_shown = {"vnum": 0, "ok": False, "model": None}
# MT2009_PLUS_WIKI_V1: the item of the last item tooltip drawn (Shift+H opens it in the wiki, uiwiki.py)
_last = {"vnum": 0, "time": 0.0}


def OpenWikiForTooltip():
	"""keybind "wiki_item" (Shift+H): the item whose tooltip is up opens in the wiki; with none, the wiki opens"""
	wiki = __import__("uiwiki")
	if _last["vnum"] and app.GetTime() - _last["time"] < 0.3:
		wiki.OpenItem(_last["vnum"])
	else:
		wiki.Toggle()


def _Board():
	if _board[0] is None:
		_board[0] = PreviewBoard()
	return _board[0]


def Hide(tooltip=None):
	board = _board[0]
	if board and board.IsShow():
		board.Hide()


def Clear(tooltip=None):
	_shown["vnum"] = 0
	Hide()


def Update(tooltip):
	"""every frame of a shown item tooltip (uitooltip.py ItemToolTip.OnUpdate)"""
	if getattr(tooltip, "compareOwner", None) is not None:
		return
	vnum = getattr(tooltip, "itemVnum", 0)
	if vnum and tooltip.IsShow():
		_last["vnum"] = vnum
		_last["time"] = app.GetTime()
	if not Available():
		return
	if not vnum or not tooltip.IsShow() or _Disabled():
		Hide()
		return
	if vnum != _shown["vnum"]:
		_shown["vnum"] = vnum
		_shown["model"] = ModelOf(vnum)
		_shown["ok"] = False
		if _shown["model"]:
			try:
				_shown["ok"] = bool(_Board().SetModel(_shown["model"]))
			except Exception:
				_shown["ok"] = False
	if not _shown["ok"]:
		Hide()
		return
	board = _Board()
	board.SetOwner(tooltip)
	(x, y) = tooltip.GetGlobalPosition()
	width = board.GetWidth()
	screenW = wndMgr.GetScreenWidth()
	if x + tooltip.GetWidth() + 2 + width <= screenW:
		x = x + tooltip.GetWidth() + 2
	else:
		x = max(0, x - width - 2)
	y = max(0, min(y, wndMgr.GetScreenHeight() - board.GetHeight()))
	board.SetPosition(x, y)
	if not board.IsShow():
		board.Show()
	board.SetTop()


def Destroy():
	board = _board[0]
	if board:
		board.Hide()
		board.Destroy()
	_board[0] = None
	_shown["vnum"] = 0
