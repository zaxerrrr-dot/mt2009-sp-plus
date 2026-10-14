# MT2009_PLUS_HIDE_COSTUME_V1 (the owner, 14 October): Owsap's costume hiding
# (__HIDE_COSTUME_SYSTEM__) in place of our three buttons of
# MT2009_PLUS_COSTUME_HIDE_V1/V2 - an eye over each slot of the costume window
# (the costume, the hairstyle, the weapon skin and now the sash), each part on
# its own, saved on the server for each character (Owsap's quest flags
# costume_option.hide_*; server-patches/ukryjkostium):
#   "/hide_costume_part <subtype> <0|1>"  ->  "SetHiddenCostumePart <subtype> <0|1>"
# (also after every login). The costume stays worn and keeps its bonuses.
#
# The old setting (autohunt/kostiumy.cfg "mask=N", the same for every
# character of this computer) is sent once after each login as the old command
# "/kostiumy_ukryj m <mask>": a character that never chose with the eyes takes
# it (costume_option.migrated) - nothing is lost by the update.
#
# MT2009_PLUS_COSTUME_VIEW_OTHERS_V1 (the owner, 7 October) stays: the button
# "Ukryj cudze" under the costume window - the OTHER characters without their
# looks, for this player only ("/kostiumy_innych <0|1>", answered
# "CostumeOthersAck <0|1>"; server-patches/playerqol), sent after every login
# and warp; saved as "others=1" in kostiumy.cfg.
#
# Python 2.7 as the client has it; the texts are CP1250 escapes.

import chat
import net
import os
import player

import uiautohunt

CONFIG_PATH = os.path.join(uiautohunt.CONFIG_BASE_DIR, 'kostiumy.cfg')

# the costume subtypes (server common/item_length.h ECostumeSubTypes)
COSTUME_BODY = 0
COSTUME_HAIR = 1
COSTUME_ACCE = 3
COSTUME_WEAPON = 4
PARTS = (COSTUME_BODY, COSTUME_HAIR, COSTUME_ACCE, COSTUME_WEAPON)

# the old kostiumy.cfg mask (MT2009_PLUS_COSTUME_HIDE_V2)
BODY = 1
HAIR = 2
WEAPON = 4
ALL = BODY | HAIR | WEAPON

TOOLTIP_HIDE = {
	COSTUME_BODY: 'Ukryj kostium',
	COSTUME_HAIR: 'Ukryj fryzur\xea',
	COSTUME_ACCE: 'Ukryj szarf\xea',
	COSTUME_WEAPON: 'Ukryj wizerunek broni',
}
TOOLTIP_SHOW = {
	COSTUME_BODY: 'Poka\xbf kostium',
	COSTUME_HAIR: 'Poka\xbf fryzur\xea',
	COSTUME_ACCE: 'Poka\xbf szarf\xea',
	COSTUME_WEAPON: 'Poka\xbf wizerunek broni',
}
TEXTS_OTHERS = ('Ukryj cudze', 'Poka\xbf cudze',
	'Kostiumy innych postaci ukryte (widzisz ich zbroje, bronie, fryzury i zwyk\xb3e szarfy)',
	'Kostiumy innych postaci znowu widoczne.')
TOOLTIP_OTHERS = 'Kostiumy innych postaci - ukryte tylko u Ciebie'

_state = {'loaded': False, 'mask': 0, 'others': False, 'othersUsed': False, 'announce': False,
	'hidden': {}, 'windows': [], 'buttons': []}


def Load():
	if _state['loaded']:
		return
	_state['loaded'] = True
	try:
		with open(CONFIG_PATH, 'r') as handle:
			for line in handle:
				if '=' not in line:
					continue
				key, value = line.strip().split('=', 1)
				value = value.strip()
				if key == 'mask' and value.isdigit():
					_state['mask'] = int(value) & ALL
				elif key == 'others' and value == '1':
					_state['others'] = True
				elif key == 'hidden' and value == '1':
					_state['mask'] = ALL
	except (IOError, OSError):
		pass


def Save():
	if not os.path.exists(uiautohunt.CONFIG_BASE_DIR):
		try:
			os.makedirs(uiautohunt.CONFIG_BASE_DIR)
		except (IOError, OSError):
			pass
	try:
		with open(CONFIG_PATH, 'w') as handle:
			handle.write('mask=%d\n' % _state['mask'])
			handle.write('others=%d\n' % (1 if _state['others'] else 0))
	except (IOError, OSError):
		pass


def IsHidden(part):
	return _state['hidden'].get(part, 0) != 0


def Send():
	"""After the login and every warp: the old setting (the server takes it only for a character that
	never chose) and "Ukryj cudze"."""
	Load()
	if _state['mask']:
		net.SendChatPacket('/kostiumy_ukryj m %d' % _state['mask'])
	if _state['others'] or _state['othersUsed']:
		net.SendChatPacket('/kostiumy_innych %d' % (1 if _state['others'] else 0))


def TogglePart(part):
	net.SendChatPacket('/hide_costume_part %d %d' % (part, 0 if IsHidden(part) else 1))


def OnSetHidden(part, hidden):
	"""SetHiddenCostumePart <subtype> <0|1> (game.py)."""
	try:
		part = int(part)
		hidden = int(hidden)
	except (TypeError, ValueError):
		return
	_state['hidden'][part] = hidden
	for window in list(_state['windows']):
		try:
			window.SetHiddenCostumePart(part, hidden)
		except Exception:
			pass


def AddWindow(window):
	if window not in _state['windows']:
		_state['windows'].append(window)
	for part in PARTS:
		window.SetHiddenCostumePart(part, 1 if IsHidden(part) else 0)


def RemoveWindow(window):
	_state['windows'] = [entry for entry in _state['windows'] if entry is not window]


# ---- "Ukryj cudze" (MT2009_PLUS_COSTUME_VIEW_OTHERS_V1) ----------------------------------------
def OthersText():
	Load()
	return TEXTS_OTHERS[1] if _state['others'] else TEXTS_OTHERS[0]


def ToggleOthers():
	Load()
	_state['others'] = not _state['others']
	_state['othersUsed'] = True
	_state['announce'] = True
	Save()
	net.SendChatPacket('/kostiumy_innych %d' % (1 if _state['others'] else 0))
	RefreshButtons()


def AddButton(button):
	_state['buttons'].append(button)
	button.SetText(OthersText())


def RemoveButton(button):
	_state['buttons'] = [entry for entry in _state['buttons'] if entry is not button]


def RefreshButtons():
	for button in _state['buttons']:
		try:
			button.SetText(OthersText())
		except Exception:
			pass


def OnAck(*rest):
	"""CostumeHiddenAck - the old command's answer (a server without ukryjkostium); nothing to say."""
	pass


def OnOthersAck(*rest):
	"""CostumeOthersAck <0|1> - only after a click (not after the login's sync)."""
	if not _state['announce']:
		return
	_state['announce'] = False
	if rest and rest[0] == '1':
		chat.AppendChat(chat.CHAT_TYPE_INFO, TEXTS_OTHERS[2] + '.')
	else:
		chat.AppendChat(chat.CHAT_TYPE_INFO, TEXTS_OTHERS[3])


class CostumeHideSync(object):
	"""An updatable: the settings to the server once a game phase has a named
	character - after the login and after every warp, when the core may be
	another one."""

	def __init__(self):
		self.sent = False

	def CanUpdate(self):
		return not self.sent

	def OnUpdate(self):
		if player.GetMainCharacterName():
			self.sent = True
			Send()

	def Destroy(self):
		pass
