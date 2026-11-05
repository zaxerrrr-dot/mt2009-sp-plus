# MT2009_PLUS_REMOTE_CALL_V1: Enasir - Dozorca / Handlarz (server-patches/remotecall/README.md; the idea of the "Official
# Remote Call" package by Khaled / LungSam, rebuilt for our client; the texts are the official Polish client's, from the
# pl-wiki "System Enasira" screenshots).
#   * the button: the side bar by the inventory (uiinventory.py SidebarWindow, "enasir") - over it the tooltip with the
#     services and their time left, Enasir summoned / when he can come again; a click asks "Czy chcesz przywolac
#     Enasira?" (or to send him away while he is here) and sends CG 190;
#   * the items 72368-72371: uiinventory __UseItem asks first (UseBagItem) and refuses one that would pass 1000 days;
#   * the storeroom opened at Enasir is "Magazyn Enasira" (interfacemodule AskSafeboxPassword / uisafebox ShowWindow,
#     TakeSafeboxRemote);
#   * the exe (Mt2009RemoteCall.cpp, app.MT2009_REMOTE_CALL_EXE) keeps the state the server sends (GC 190) and calls
#     game.py BINARY_RemoteCall_Event, which comes here (OnEvent). The server writes every notice to the chat itself.
# Module-level state only (no window holds another; nothing takes a weak proxy).
import app
import chat
import net
import player
import ui

try:
	import remoteCall
except ImportError:
	remoteCall = None

ITEM_VNUMS = {
	72368: 0,	# Dozorca Enasir - storeroom
	72369: 1,	# Handlarz Enasir - shop
	72370: 0,	# Dozorca Enasir (h)
	72371: 1,	# Handlarz Enasir (h)
}
ITEM_DEFAULT_SEC = 604800
MAX_BUFF_SEC = 86400000
REQUEST_TIMEOUT = 5.0

TEXT_NAME = "Enasir"
TEXT_SERVICES = "Us\xb3ugi, z kt\xf3rych mo\xbfesz korzysta\xe6, s\xb9 uzale\xbfnione od posiadanych przez ciebie buff\xf3w."
TEXT_BUFF_COUNT = "Twoje buffy: %d"
TEXT_BUFF_LEFT = "%s (Pozosta\xb3y czas: %s)"
TEXT_BUFF_NAME = ("Magazyn", "Sklep")
TEXT_CAN_SUMMON = "Mo\xbfna przywo\xb3a\xe6 Enasira."
TEXT_SUMMONED = "Enasir jest przy tobie (pozosta\xb3y czas: %s)."
TEXT_COOLTIME = "Enasira mo\xbfna przywo\xb3a\xe6 ponownie za %d s."
TEXT_NOT_HERE = "Enasira nie mo\xbfna przywo\xb3a\xe6 w tym miejscu."
TEXT_NO_BUFF_1 = "Przywo\xb3any Enasir otworzy ci magazyn albo sklep."
TEXT_NO_BUFF_2 = "Najpierw u\xbfyj przedmiotu Dozorca Enasir albo Handlarz Enasir."
TEXT_ASK_SUMMON = "Czy chcesz przywo\xb3a\xe6 Enasira?"
TEXT_ASK_UNSUMMON = "Czy chcesz odes\xb3a\xe6 Enasira?"
TEXT_ASK_USE = "Czy chcesz skorzysta\xe6 z us\xb3ug %s?"
TEXT_MAX = "Tej us\xb3ugi Enasira nie mo\xbfna ju\xbf przed\xb3u\xbfy\xe6 - najwy\xbfej do 1000 dni."
TEXT_SAFEBOX_TITLE = "Magazyn Enasira"
TEXT_WAIT = "Poczekaj chwil\xea."

_tooltip = None
_tooltipShown = False
_dialog = None
_requestTime = 0.0


def IsAvailable():
	return remoteCall is not None and bool(getattr(app, "MT2009_REMOTE_CALL_EXE", 0))


def _Duration(sec):
	sec = max(0, int(sec))
	days, hours, minutes = sec / 86400, sec % 86400 / 3600, sec % 3600 / 60
	if days:
		return "%dd %dh %dm" % (days, hours, minutes)
	if hours:
		return "%dh %dm" % (hours, minutes)
	if minutes:
		return "%dm" % minutes
	return "%ds" % sec


def _BuffLeft(kind):
	try:
		return max(0, remoteCall.GetBuffLeft(kind))
	except Exception:
		return 0


def _GetToolTip():
	global _tooltip
	if _tooltip is None:
		import uiToolTip
		_tooltip = uiToolTip.ToolTip()
		_tooltip.HideToolTip()
	return _tooltip


def _FillToolTip(tip):
	tip.ClearToolTip()
	tip.SetTitle(TEXT_NAME)
	if not IsAvailable():
		return
	buffs = [(kind, _BuffLeft(kind)) for kind in (0, 1)]
	buffs = [(kind, left) for kind, left in buffs if left > 0]
	if not remoteCall.IsAllowedHere():
		tip.AutoAppendTextLine(TEXT_NOT_HERE)
	if not buffs:
		tip.AutoAppendTextLine(TEXT_NO_BUFF_1)
		tip.AutoAppendTextLine(TEXT_NO_BUFF_2)
		return
	tip.AutoAppendTextLine(TEXT_SERVICES)
	tip.AutoAppendTextLine(TEXT_BUFF_COUNT % len(buffs))
	for kind, left in buffs:
		tip.AutoAppendTextLine(TEXT_BUFF_LEFT % (TEXT_BUFF_NAME[kind], _Duration(left)))
	summonLeft = remoteCall.GetSummonLeft()
	coolLeft = remoteCall.GetCoolLeft()
	if summonLeft > 0:
		tip.AutoAppendTextLine(TEXT_SUMMONED % _Duration(summonLeft))
	elif coolLeft > 0:
		tip.AutoAppendTextLine(TEXT_COOLTIME % coolLeft)
	elif remoteCall.IsAllowedHere():
		tip.AutoAppendTextLine(TEXT_CAN_SUMMON)


# the side bar's button: SetShowToolTipEvent / SetHideToolTipEvent
def ShowToolTip():
	global _tooltipShown
	tip = _GetToolTip()
	_FillToolTip(tip)
	tip.ResizeToolTip()
	tip.ShowToolTip()
	_tooltipShown = True


def HideToolTip():
	global _tooltipShown
	_tooltipShown = False
	if _tooltip is not None:
		_tooltip.HideToolTip()


def _CloseDialog():
	if _dialog is not None:
		_dialog.Close()


def _Ask(text, onAccept):
	global _dialog
	if _dialog is None:
		import uiCommon
		_dialog = uiCommon.QuestionDialog()
	_dialog.SetText(text)
	try:
		_dialog.SetWidth(max(_dialog.GetWidth(), _dialog.textLine.GetTextSize()[0] + 40))
	except Exception:
		pass

	def accept():
		_CloseDialog()
		onAccept()

	_dialog.SetAcceptEvent(accept)
	_dialog.SetCancelEvent(_CloseDialog)
	_dialog.Open()


def _Send(sub):
	global _requestTime
	now = app.GetTime()
	if _requestTime and now - _requestTime < REQUEST_TIMEOUT:
		chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_WAIT)
		return
	_requestTime = now
	remoteCall.SendPacket(sub)


# the side bar's button
def OnClick():
	if not IsAvailable():
		return
	HideToolTip()
	if remoteCall.GetSummonLeft() > 0:
		_Ask(TEXT_ASK_UNSUMMON, lambda: _Send(remoteCall.CG_UNSUMMON))
		return
	# the server says why it cannot (chat): no service, the place, the cool-down, death
	if not remoteCall.IsAllowedHere():
		chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_NOT_HERE)
		return
	if not _BuffLeft(0) and not _BuffLeft(1):
		chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_NO_BUFF_2)
		return
	coolLeft = remoteCall.GetCoolLeft()
	if coolLeft > 0:
		chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_COOLTIME % coolLeft)
		return
	_Ask(TEXT_ASK_SUMMON, lambda: _Send(remoteCall.CG_SUMMON))


# game.py BINARY_RemoteCall_Event (the exe, after every GC 190)
def OnEvent(sub, value):
	global _requestTime
	if not IsAvailable():
		return
	if sub in (remoteCall.GC_SUMMONED, remoteCall.GC_GONE, remoteCall.GC_MESSAGE):
		_requestTime = 0.0
	if _tooltipShown and _tooltip is not None:
		_FillToolTip(_tooltip)
		_tooltip.ResizeToolTip()


# uiinventory __UseItem: True when the use was handled here (asked first; the item use packet after "Tak")
def UseBagItem(cell, vnum):
	if vnum not in ITEM_VNUMS or not IsAvailable():
		return False
	import item
	item.SelectItem(vnum)
	sec = player.GetItemMetinSocket(cell, 0)
	if sec <= 0:
		sec = item.GetValue(1)
	if sec <= 0:
		sec = ITEM_DEFAULT_SEC
	if _BuffLeft(ITEM_VNUMS[vnum]) + sec > MAX_BUFF_SEC:
		chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_MAX)
		return True

	def use():
		import uiPrivateShopBuilder
		if uiPrivateShopBuilder.IsBuildingPrivateShop():
			return
		if player.GetItemIndex(cell) == vnum:
			net.SendItemUsePacket(cell)

	_Ask(TEXT_ASK_USE % item.GetItemName(), use)
	return True


# interfacemodule AskSafeboxPassword: is the storeroom asked for now Enasir's? (read once - the flag is cleared)
def TakeSafeboxRemote():
	if not IsAvailable():
		return False
	try:
		remote = bool(remoteCall.IsSafeboxRemote())
		remoteCall.SetSafeboxRemote(0)
		return remote
	except Exception:
		return False


def Destroy():
	global _tooltip, _dialog, _tooltipShown, _requestTime
	if _dialog is not None:
		_dialog.Close()
	if _tooltip is not None:
		_tooltip.HideToolTip()
	_tooltip = None
	_dialog = None
	_tooltipShown = False
	_requestTime = 0.0
