# Filtr podnoszenia - what the Z key and a loot pet pick up (the operator,
# 28 September: "okno dla autopeta i do recznego dzialania ... mozliwosc
# filtrowania zbieranego dropu, jak w auto lowach").
#
# The same thirteen kinds as the auto-hunt's pick-up (uiautohunt.LOOT_KINDS);
# the server keeps them per character and applies them where the Z key and
# a loot pet pick up (CHARACTER::PickupNearbyItems,
# server-patches/playerqol): "/pickup_filter <on> <kinds>", sent after every
# login (PickupFilterSync, an updatable of game.py) and every change. Yang
# is always taken. With the filter on, holding Z or ` asks the server for
# the filtered pick-up instead of the client's own PickCloseItem, which
# takes whatever lies nearest.
#
# Ctrl+Z or "/filtr" opens the window. The settings are the client's, for
# every character: autohunt/filtr.cfg.
#
# Python 2.7 as the client has it; the texts are CP1250 escapes.

import chat
import net
import os
import player
import ui

import uiautohunt

CONFIG_PATH = os.path.join(uiautohunt.CONFIG_BASE_DIR, 'filtr.cfg')
ALL_KINDS = 0
for _key, _label, _bit in uiautohunt.LOOT_KINDS:
    ALL_KINDS |= _bit

_state = {'loaded': False, 'on': 0, 'kinds': ALL_KINDS, 'window': None}


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
                try:
                    value = int(value)
                except ValueError:
                    continue
                if key == 'on':
                    _state['on'] = 1 if value else 0
                elif key == 'kinds':
                    _state['kinds'] = value & ALL_KINDS
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
            handle.write('on=%d\nkinds=%d\n' % (_state['on'], _state['kinds']))
    except (IOError, OSError):
        pass


def Send():
    Load()
    net.SendChatPacket('/pickup_filter %d %d' % (_state['on'], _state['kinds']))


def IsActive():
    Load()
    return _state['on'] != 0


def OnAck(on='0', kinds='0', *rest):
    pass


class PickupFilterSync(object):
    """An updatable: the filter to the server once a game phase has a named
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
        DestroyWindow()


class PickupFilterWindow(ui.BoardWithTitleBar):
    WIDTH = 300
    ROWS = (len(uiautohunt.LOOT_KINDS) + 2) // 3

    def __init__(self):
        ui.BoardWithTitleBar.__init__(self)
        self.widgets = []
        self.toggles = {}
        self.height = 32 + 30 + 28 + self.ROWS * 22 + 12 + 40
        self.AddFlag('movable')
        self.AddFlag('float')
        self.SetSize(self.WIDTH, self.height)
        self.SetTitleName('Filtr podnoszenia (Z i pet)')
        self.SetCloseEvent(ui.__mem_func__(self.Close))
        self.Build()
        self.SetCenterPosition()

    def Build(self):
        BL = 10
        BW = self.WIDTH - 2 * BL
        y = 32
        self.onButton = self._Btn(self, 'xlarge', 0, y, '', self.OnToggleFilter)
        self.onButton.SetWindowHorizontalAlignCenter()
        y += 30

        board = ui.ThinBoard()
        board.SetParent(self)
        board.SetPosition(BL, y)
        board.SetSize(BW, 24 + self.ROWS * 22 + 8)
        board.Show()
        self.widgets.append(board)
        self._Label(board, 14, 4, 'Podnosz\xea:')
        for idx, (key, label, bit) in enumerate(uiautohunt.LOOT_KINDS):
            btn = self._Btn(board, 'large', 4 + (idx % 3) * 92, 24 + (idx // 3) * 22, '', self.OnToggleKind, bit)
            self.toggles[bit] = (btn, label)
        y += 24 + self.ROWS * 22 + 8 + 6

        self._Label(self, BL + 4, y, 'Klawisz Z i pet zbieraj\xb9cy drop. Yang zawsze.')
        self._Label(self, BL + 4, y + 14, 'Wy\xb3\xb9czony filtr: podnosz\xea wszystko.')

    def _Label(self, parent, x, y, text):
        line = ui.TextLine()
        line.SetParent(parent)
        line.SetPosition(x, y)
        line.SetText(text)
        line.Show()
        self.widgets.append(line)
        return line

    def _Btn(self, parent, size, x, y, text, event, *args):
        button = ui.Button()
        button.SetParent(parent)
        button.SetPosition(x, y)
        button.SetUpVisual('d:/ymir work/ui/public/%s_button_01.sub' % size)
        button.SetOverVisual('d:/ymir work/ui/public/%s_button_02.sub' % size)
        button.SetDownVisual('d:/ymir work/ui/public/%s_button_03.sub' % size)
        button.SetText(text)
        button.SAFE_SetEvent(event, *args)
        button.Show()
        self.widgets.append(button)
        return button

    def Refresh(self):
        Load()
        self.onButton.SetText('Filtr: %s' % ('W\xb3\xb9czony' if _state['on'] else 'Wy\xb3\xb9czony'))
        for bit, (btn, label) in self.toggles.items():
            btn.SetText('%s: %s' % (label, 'Tak' if _state['kinds'] & bit else 'Nie'))

    def OnToggleFilter(self):
        _state['on'] = 0 if _state['on'] else 1
        self.Changed()

    def OnToggleKind(self, bit):
        _state['kinds'] ^= bit
        self.Changed()

    def Changed(self):
        Save()
        Send()
        self.Refresh()

    def Open(self):
        self.Refresh()
        self.Show()
        self.SetTop()

    def Close(self):
        self.Hide()

    def OnPressEscapeKey(self):
        self.Close()
        return True

    def Destroy(self):
        self.Hide()
        self.widgets = []
        self.toggles = {}


def ToggleWindow():
    window = _state['window']
    if window is None:
        window = PickupFilterWindow()
        _state['window'] = window
    if window.IsShow():
        window.Close()
    else:
        window.Open()


def OpenWindow():
    window = _state['window']
    if window is None or not window.IsShow():
        ToggleWindow()


def DestroyWindow():
    window = _state['window']
    _state['window'] = None
    if window is not None:
        window.Destroy()
