# Walking through one's own companion (26 September:
# "towarzysz jest dla naszej postaci nieblokujacym, zeby dalo sie przez niego
# przenikac, bo jak expi sie z nim to on strasznie przeszkadza").
#
# The collision between two characters is the client's alone:
# CInstanceBase::CheckAdvancing tests the main instance against every other
# one, and CActorInstance::TestActorCollision skips a victim whose actor type
# is NPC (ENABLE_NPC_WITHOUT_COLLISIONS in this client's GameLib). The server
# tells the owner's client which character its companion is
# (playerbot_sidekick.h, SendPlayerBotSidekickBody):
#
#   SidekickVid <vid>     - 0 once it has gone
#
# and the keeper below types that instance as an NPC - chr.SetInstanceType on
# the selected instance - whenever the client has made it anew, which it does
# every time the companion comes back into view. Nothing else of the instance
# changes. What an NPC's type also means in this client: a new hair or sash
# shows when it next comes into view, the minimap draws it as an NPC - and a
# click opens no player menu, because CPythonPlayer::OpenCharacterMenu, which
# both mouse buttons end in, returns for anything but a player. So under the
# cursor the companion is a player again (SetPicked, from game.py's picking,
# every frame): a click opens the menu - whisper, trade, guild - as it does
# for anybody else ("Na towarzysza nie dziala prawe klikniecie", Piciu713, 28
# September), and it is an NPC again, to be walked through, once the cursor
# has left it.
#
# The hair and the sash (MT2009_PLUS_SIDEKICK_HAIR_V1). CInstanceBase::SetHair
# and SetAcce return for an instance that is not a player, and the client's
# ChangeArmor makes the body anew and puts the hair back through SetHair - so
# the companion typed as an NPC lost its head in a new armour or costume, and
# kept its old hair when given a new one ("pusta glowa", 28 September). The
# server sends the two parts with the VID, again at every change of the
# armour, the hair or the sash:
#
#   SidekickVid <vid> <hair> <sash>
#
# and the keeper puts both back with the instance a player for that moment.
#
# Python 2.7 as the client has it; any exe of this line has the three chr
# calls, and one without them only loses the collision, never the game.

import chr
import clientclock
import player

CHECK_EVERY = 0.25

_state = {'vid': 0, 'next': 0.0, 'hover': False, 'look': None}


def ParseVid(value):
	try:
		vid = int(value)
	except (TypeError, ValueError):
		return 0
	return vid if vid > 0 else 0


def ParseLook(look):
	"""(hair, sash) from the command's two numbers, or None without them."""
	if len(look) < 2:
		return None
	try:
		return (max(0, int(look[0])), max(0, int(look[1])))
	except (TypeError, ValueError):
		return None


def SetVid(value, *look):
	vid = ParseVid(value)
	if vid != _state['vid']:
		_state['hover'] = False
	_state['vid'] = vid
	_state['next'] = 0.0
	_state['look'] = ParseLook(look) if vid else None


def GetVid():
	return _state['vid']


def _SetType(vid, kind):
	chr.SelectInstance(vid)
	chr.SetInstanceType(kind)
	# The selection is what every other chr.Set* call acts on; the main
	# character is where the stock scripts expect to find it.
	chr.SelectInstance(player.GetMainCharacterIndex())


def ApplyLook():
	"""Puts the hair and the sash the server named on the companion's instance,
	once; True when it did."""
	look = _state['look']
	vid = _state['vid']
	if not look or not vid:
		return False
	if vid == player.GetMainCharacterIndex() or not chr.HasInstance(vid):
		return False
	_state['look'] = None
	(hair, sash) = look
	npc = chr.GetInstanceType(vid) == chr.INSTANCE_TYPE_NPC
	chr.SelectInstance(vid)
	if npc:
		chr.SetInstanceType(chr.INSTANCE_TYPE_PLAYER)
	try:
		chr.SetHair(hair)
		chr.SetAcce(sash)
	finally:
		if npc:
			chr.SetInstanceType(chr.INSTANCE_TYPE_NPC)
		chr.SelectInstance(player.GetMainCharacterIndex())
	return True


def Apply():
	"""True when the companion's instance was typed as an NPC just now."""
	vid = _state['vid']
	if not vid or _state['hover']:
		return False
	main = player.GetMainCharacterIndex()
	if vid == main or not chr.HasInstance(vid):
		return False
	if chr.GetInstanceType(vid) == chr.INSTANCE_TYPE_NPC:
		return False
	_SetType(vid, chr.INSTANCE_TYPE_NPC)
	return True


def SetPicked(picked):
	"""The character under the cursor, from game.py every frame (-1 for none).
	True when the companion's type changed: a player under the cursor, an NPC
	once the cursor has left it."""
	vid = _state['vid']
	hover = bool(vid) and picked == vid
	if hover == _state['hover']:
		return False
	_state['hover'] = hover
	if vid == player.GetMainCharacterIndex() or not chr.HasInstance(vid):
		return False
	_SetType(vid, chr.INSTANCE_TYPE_PLAYER if hover else chr.INSTANCE_TYPE_NPC)
	return True


class Keeper(object):
	"""Registered among game.py's updateables; ends with the game window, whose
	next one hears the VID again (a warp is a new login on the server)."""

	def CanUpdate(self):
		return _state['vid'] != 0

	def OnUpdate(self):
		now = clientclock.Now()
		if now < _state['next']:
			return
		_state['next'] = now + CHECK_EVERY
		try:
			Apply()
		except Exception:
			_state['vid'] = 0
			return
		try:
			ApplyLook()
		except Exception:
			_state['look'] = None

	def Destroy(self):
		_state['vid'] = 0
		_state['next'] = 0.0
		_state['hover'] = False
		_state['look'] = None


_keeper = []


def GetKeeper():
	if not _keeper:
		_keeper.append(Keeper())
	return _keeper[0]
