# MT2009_PLUS_IRREMOVABLE_DELETE_V1 - a worn item that cannot be taken off (ITEM_FLAG_IRREMOVABLE, the timed unique
# items) asks whether to destroy it when the player tries to take it off (a right click on it, or dragging it out of
# the equipment). The server decides when to ask and checks the yes again (irremovable_delete.cpp, server-patches/irrem):
#   server -> client  "IRREM ask <token> <vnum>"     open the question
#   client -> server  "/irrem usun <token>"          "Tak" - destroy it
#                     "/irrem anuluj"                "Nie", Esc, or the window closed
# The texts are cp1250 bytes (the client's Polish), the file itself ascii.
import net
import item
import uiCommon

_data = {'dialog': None, 'token': 0, 'answered': False}


def _ToInt(value):
	try:
		return int(value)
	except (TypeError, ValueError):
		return 0


def DestroyWindow():
	dialog = _data['dialog']
	_data['dialog'] = None
	_data['answered'] = True	# a warp / logout: no "anuluj" from here (the server's question dies with the connection)
	if dialog:
		dialog.closeEvent = None
		dialog.Close()
		dialog.Destroy()


def _OnAccept():
	if not _data['answered'] and _data['token']:
		_data['answered'] = True
		net.SendChatPacket("/irrem usun %d" % _data['token'])
	if _data['dialog']:
		_data['dialog'].Close()


def _OnCancel():
	if _data['dialog']:
		_data['dialog'].Close()


def _OnClosed():
	if not _data['answered']:
		_data['answered'] = True
		net.SendChatPacket("/irrem anuluj")


def OnCommand(sub='', *args):
	if sub != 'ask' or len(args) < 2:
		return
	token = _ToInt(args[0])
	vnum = _ToInt(args[1])
	if token <= 0 or vnum <= 0:
		return

	name = ""
	try:
		item.SelectItem(vnum)
		name = item.GetItemName()
	except Exception:
		name = ""

	dialog = _data['dialog']
	if not dialog:
		dialog = uiCommon.QuestionDialog2()
		_data['dialog'] = dialog
	# a new question replaces an open one (the server keeps one per player, the newest)
	_data['token'] = token
	_data['answered'] = False
	dialog.SetText1("Tego przedmiotu nie mo\xbfna zdj\xb9\xe6.")
	if name:
		dialog.SetText2("Czy chcesz go zniszczy\xe6? (%s)" % name)
	else:
		dialog.SetText2("Czy chcesz go zniszczy\xe6?")
	dialog.SetAcceptText("Zniszcz")
	dialog.SetCancelText("Nie")
	dialog.SetAcceptEvent(_OnAccept)
	dialog.SetCancelEvent(_OnCancel)
	dialog.closeEvent = _OnClosed
	dialog.Open()
