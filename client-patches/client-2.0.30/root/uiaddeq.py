# MT2009_PLUS_ADDEQ_V1 - Druga strona ekwipunku: the "Official Additional Equipment Page"
# package on our client (the owner, 28 October 2026: "Add this too to the client.").
#
# The server keeps the inactive page (server-patches/addeq, playerbot_addeq.cpp) and swaps
# it with the worn items of the paged slots - armour, helmet, shoes, bracelet, weapon,
# necklace, earrings, arrows, shield, talisman, gloves (rings, costumes and the belt are
# shared). The equipment window always shows the worn page, as before; here are only the
# page tabs I / II (the inventory's hidden Equipment_Tab_01/02, moved into the title bar)
# shown once the page is unlocked (item "Strona ekwipunku II", 38306 / 76055). The support
# skill 200 "Zmiana strony ekwipunku" (playersettingmodule.py, uicharacter.py) switches as
# well - with the exe that sends it (app.ENABLE_MT2009_ADDEQ).
#
#   "/addeq hello"   after every load (game.py) -> "addeq_page <unlocked> <page>"
#   "/addeq <0|1>"   a tab
# Texts CP1250.
import net
import app

TEXT_TAB = ("Strona ekwipunku I", "Strona ekwipunku II")
TITLE_X_TABS = 92		# the title's centre with the tabs at its left (uiscript/inventorywindow.py: 71)
TAB_X = (2, 34)
TAB_Y = 1

_state = {'unlocked': 0, 'page': 0, 'inv': None, 'title_x': None}


def IsSkillSupported():
	"""the exe sends the skill 200 (PythonPlayerSkill.cpp); an older exe gets no skill slot"""
	return getattr(app, "ENABLE_MT2009_ADDEQ", 0) != 0


def Start():
	"""game.py, once the character is in the world (and after every warp)."""
	net.SendChatPacket("/addeq hello")


def OnServerPage(*args):
	try:
		_state['unlocked'] = int(args[0])
		_state['page'] = int(args[1])
	except (IndexError, ValueError):
		return
	Refresh()


def GetPage():
	return _state['page']


def IsUnlocked():
	return _state['unlocked'] != 0


def _OnTab(page):
	if page != _state['page']:
		net.SendChatPacket("/addeq %d" % page)
	Refresh()	# the radio button stays as the server says


def BindInventory(wnd):
	"""uiinventory.py __LoadWindow: the two hidden equipment tabs become the page tabs."""
	from _weakref import proxy
	try:
		tabs = wnd.equipmentTab
		titleBar = wnd.GetChild("TitleBar")
		titleName = wnd.GetChild("TitleName")
	except Exception:
		return
	if len(tabs) < 2:
		return
	# MT2009_PLUS_INVENTORY_V2_V1: the v2 inventory's equipment window has the tabs in their own row (inventoryv2.py)
	v2 = getattr(wnd, "wndEquipWindow", None) is not None
	for i in xrange(2):
		tab = tabs[i]
		if not v2:
			tab.SetParent(titleBar)
			tab.SetPosition(TAB_X[i], TAB_Y)
		tab.SetEvent(_OnTab, i)
		tab.SetToolTipText(TEXT_TAB[i])
	if _state['title_x'] is None:
		_state['title_x'] = titleName.GetLocalPosition()[0]
	_state['inv'] = proxy(wnd)
	Refresh()


def Refresh():
	wnd = _state['inv']
	if wnd is None:
		return
	try:
		if getattr(wnd, "wndEquipWindow", None) is not None:	# MT2009_PLUS_INVENTORY_V2_V1
			__import__("inventoryv2").RefreshPageTabs(wnd, IsUnlocked(), _state['page'])
			return
		tabs = wnd.equipmentTab
		titleName = wnd.GetChild("TitleName")
		y = titleName.GetLocalPosition()[1]
		if not IsUnlocked():
			for tab in tabs:
				tab.Hide()
			if _state['title_x'] is not None:
				titleName.SetPosition(_state['title_x'], y)
			return
		titleName.SetPosition(TITLE_X_TABS, y)
		for i in xrange(2):
			if i == _state['page']:
				tabs[i].Down()
			else:
				tabs[i].SetUp()
			tabs[i].Show()
	except ReferenceError:
		_state['inv'] = None
