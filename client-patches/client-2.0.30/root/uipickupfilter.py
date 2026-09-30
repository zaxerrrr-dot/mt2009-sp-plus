# Filtr podnoszenia - what the Z and ` keys and a loot pet pick up.
#
# MT2009_PLUS_PICKUP_FILTER_V1: since client 2.0.31 the filter is Auto Lowy's
# own pick-up panel (uiautohunt.py): the switch "Filtr dla Z i `" under its
# kinds, with "Bez bonusu", per character - no longer a window and a file of
# its own (autohunt/filtr.cfg is not read any more). The same switch is in
# ESC -> Opcje gry, row "Podnoszenie" ([Wszystko] [Filtr] [Ustaw]).
#
# The server keeps the filter per character and applies it where Z, ` and a
# loot pet pick up (CHARACTER::PickupNearbyItems, server-patches/playerqol):
# "/pickup_filter <on> <kinds>", sent after every login and warp
# (PickupFilterSync, an updatable of game.py) and at every change of the
# panel (uiautohunt.NotifyPickupKinds). Yang is always taken, and a click on
# an item with the mouse still picks up anything. With the filter on, a held
# Z or ` asks the server for the filtered pick-up instead of the client's own
# PickCloseItem, which takes whatever lies nearest (game.py, updateable.py).
# The kinds are sent with the switch off too: the server keeps them for the
# companion's "Filtr" (uisidekick.py, playerbot_sidekick.h).
#
# Ctrl+Z, "/filtr" and the inventory's button open Auto Lowy's settings
# window, whose first panel this is.
#
# Python 2.7 as the client has it.

import net
import player


def _Hunt():
	import uiautohunt
	return uiautohunt


def Send():
	"""The switch and the kinds to the server; nothing before this
	character's settings are read (PickupFilterSync sends them then). The
	kinds go with the switch off too: a companion's "Filtr" takes them
	(playerbot_sidekick.h), at once when they change."""
	hunt = _Hunt()
	if not hunt.IsLoaded():
		return False
	on = 0 if hunt.ManualPickupMask() is None else 1
	net.SendChatPacket('/pickup_filter %d %d' % (on, hunt.PickupKindsMask()))
	return True


def IsActive():
	return _Hunt().IsManualFilterOn()


def OnAck(on='0', kinds='0', *rest):
	pass


class PickupFilterSync(object):
	"""An updatable: the filter to the server once a game phase has a named
	character and Auto Lowy has read its settings - after the login and after
	every warp, when the core may be another one."""

	def __init__(self):
		self.sent = False

	def CanUpdate(self):
		return not self.sent

	def OnUpdate(self):
		if player.GetMainCharacterName() and Send():
			self.sent = True

	def Destroy(self):
		pass


def ToggleWindow():
	_Hunt().ShowLootWindow(True)


def OpenWindow():
	_Hunt().ShowLootWindow()


def DestroyWindow():
	# The window is Auto Lowy's, which the game's updatables destroy.
	pass
