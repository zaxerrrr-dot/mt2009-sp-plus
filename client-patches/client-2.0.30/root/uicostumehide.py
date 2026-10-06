# Ukryj kostiumy - the buttons under the costume window (the operator, 28
# September: "ukryj/pokaz kostiumy ... jak sa ukryte, to normalnie widac
# oryginalna zbroje i bron, ale sa zalozone i daja bonusy").
#
# MT2009_PLUS_COSTUME_HIDE_V2 (the owner, 6 October: "nakladka na bron
# wlaczona, a fryzura i kostium wylaczone"): three buttons, each look hidden on
# its own - the costume (1), the hair (2), the weapon skin (4).
#
# The costumes stay worn and keep their bonuses; only what the body, the
# weapon and the hair look like changes, for every player around. The server does the
# looks (item.cpp, Mt2009PlusApplyCostumeParts, server-patches/playerqol):
# "/kostiumy_ukryj m <mask>", sent after every login and warp
# (CostumeHideSync, an updatable of game.py) and on every click; it answers
# "CostumeHiddenAck m <mask>". A hidden hair costume shows the character's own
# default hair; the sash stays as it is.
#
# The setting is the client's, for every character: autohunt/kostiumy.cfg
# ("mask=N"; the old "hidden=1" of V1 reads as everything hidden).
#
# Python 2.7 as the client has it; the texts are CP1250 escapes.

import chat
import net
import os
import player

import uiautohunt

CONFIG_PATH = os.path.join(uiautohunt.CONFIG_BASE_DIR, 'kostiumy.cfg')

BODY = 1
HAIR = 2
WEAPON = 4
ALL = BODY | HAIR | WEAPON

# bit -> (hide text, show text, hidden message, shown message)
TEXTS = {
    BODY: ('Ukryj kostium', 'Poka\xbf kostium', 'Kostium ukryty', 'Kostium znowu widoczny.'),
    HAIR: ('Ukryj fryzur\xea', 'Poka\xbf fryzur\xea', 'Fryzura ukryta', 'Fryzura znowu widoczna.'),
    WEAPON: ('Ukryj bro\xf1', 'Poka\xbf bro\xf1', 'Sk\xf3rka broni ukryta', 'Sk\xf3rka broni znowu widoczna.'),
}

_state = {'loaded': False, 'mask': 0, 'announce': 0, 'buttons': []}


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
    except (IOError, OSError):
        pass


def IsHidden(bit=ALL):
    Load()
    return (_state['mask'] & bit) != 0


def ButtonText(bit):
    if IsHidden(bit):
        return TEXTS[bit][1]
    return TEXTS[bit][0]


def Send():
    Load()
    net.SendChatPacket('/kostiumy_ukryj m %d' % _state['mask'])


def Toggle(bit):
    Load()
    _state['mask'] ^= bit
    _state['announce'] = bit
    Save()
    Send()
    RefreshButtons()


def AddButton(button, bit):
    _state['buttons'].append((button, bit))
    button.SetText(ButtonText(bit))


def RemoveButton(button):
    _state['buttons'] = [entry for entry in _state['buttons'] if entry[0] is not button]


def RefreshButtons():
    for button, bit in _state['buttons']:
        try:
            button.SetText(ButtonText(bit))
        except Exception:
            pass


def OnAck(*rest):
    bit = _state['announce']
    if not bit:
        return
    _state['announce'] = 0
    if rest and rest[0] == 'm' and len(rest) > 1 and rest[1].isdigit():
        mask = int(rest[1])
    elif rest and rest[0] == '1':
        mask = ALL  # a server without V2
    else:
        mask = 0
    if mask & bit:
        chat.AppendChat(chat.CHAT_TYPE_INFO, '%s - bonusy dzia\xb3aj\xb9 dalej.' % TEXTS[bit][2])
    else:
        chat.AppendChat(chat.CHAT_TYPE_INFO, TEXTS[bit][3])


class CostumeHideSync(object):
    """An updatable: the setting to the server once a game phase has a named
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
