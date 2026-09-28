# Ukryj kostiumy - the button under the costume window (the operator, 28
# September: "ukryj/pokaz kostiumy ... jak sa ukryte, to normalnie widac
# oryginalna zbroje i bron, ale sa zalozone i daja bonusy").
#
# The costumes stay worn and keep their bonuses; only what the body and the
# weapon look like changes, for every player around. The server does the
# looks (item.cpp, Mt2009PlusApplyCostumeParts, server-patches/playerqol):
# "/kostiumy_ukryj <0|1>", sent after every login and warp
# (CostumeHideSync, an updatable of game.py) and on every click; it answers
# "CostumeHiddenAck <0|1>". The hair costume and the sash stay as they are.
#
# The setting is the client's, for every character: autohunt/kostiumy.cfg.
#
# Python 2.7 as the client has it; the texts are CP1250 escapes.

import chat
import net
import os
import player

import uiautohunt

CONFIG_PATH = os.path.join(uiautohunt.CONFIG_BASE_DIR, 'kostiumy.cfg')

TEXT_HIDE = 'Ukryj kostiumy'
TEXT_SHOW = 'Poka\xbf kostiumy'

_state = {'loaded': False, 'hidden': 0, 'announce': False, 'buttons': []}


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
                if key == 'hidden':
                    _state['hidden'] = 1 if value.strip() == '1' else 0
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
            handle.write('hidden=%d\n' % _state['hidden'])
    except (IOError, OSError):
        pass


def IsHidden():
    Load()
    return _state['hidden'] != 0


def ButtonText():
    if IsHidden():
        return TEXT_SHOW
    return TEXT_HIDE


def Send():
    Load()
    net.SendChatPacket('/kostiumy_ukryj %d' % _state['hidden'])


def Toggle():
    Load()
    _state['hidden'] = 0 if _state['hidden'] else 1
    _state['announce'] = True
    Save()
    Send()
    RefreshButtons()


def AddButton(button):
    _state['buttons'].append(button)
    button.SetText(ButtonText())


def RemoveButton(button):
    if button in _state['buttons']:
        _state['buttons'].remove(button)


def RefreshButtons():
    text = ButtonText()
    for button in _state['buttons']:
        try:
            button.SetText(text)
        except Exception:
            pass


def OnAck(hidden='0', *rest):
    if not _state['announce']:
        return
    _state['announce'] = False
    if hidden == '1':
        chat.AppendChat(chat.CHAT_TYPE_INFO, 'Kostiumy ukryte - wida\xe6 zbroj\xea i bro\xf1, bonusy kostium\xf3w dzia\xb3aj\xb9 dalej.')
    else:
        chat.AppendChat(chat.CHAT_TYPE_INFO, 'Kostiumy znowu widoczne.')


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
