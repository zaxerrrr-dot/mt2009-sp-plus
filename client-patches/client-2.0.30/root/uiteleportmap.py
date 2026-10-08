# MT2009_PLUS_TELEPORT_MAP_V1: Mapa teleportacji pod TAB. Autor: Mur4s.
# TAB (without Ctrl) opens the world map with 18 points; a click sends
# "/tabteleport <key>" and the server's quest mapa_tab warps (free, no ring;
# the server takes only the key). Hell asks for the respawn kingdom first.
# Only while the server has it on: "MAPA_TAB 1|0" (quest mapa_tab, at login
# and within seconds of the panel's switch) sets IsEnabled(); off, game.py
# leaves TAB to what it did before (Slot 6).
# Python 2.7; UI strings use CP1250 escapes.
import app
import net
import ui
import wndMgr

POINTS = (
    ('Jinno M1', 'jinno1', .192, .715),
    ('Jinno M2', 'jinno2', .283, .574),
    ('Shinsoo M1', 'shinsoo1', .462, .722),
    ('Shinsoo M2', 'shinsoo2', .503, .561),
    ('Chunjo M1', 'chunjo1', .842, .763),
    ('Chunjo M2', 'chunjo2', .694, .720),
    ('Dolina', 'valley', .099, .610),
    ('Pustynia', 'desert', .549, .634),
    ('G\xf3ra Sohan', 'snow', .396, .139),
    ('\x8cwi\xb9tynia', 'temple', .890, .390),
    ('Dolina Cyklop\xf3w', 'cyclops', .523, .338),
    ('Pustkowie Faraona', 'pharaoh', .768, .570),
    ('Las Duch\xf3w', 'forest', .151, .363),
    ('Czerwony Las', 'redforest', .183, .161),
    ('Piek\xb3o', 'hell', .850, .182),
    ('Wie\xbfa Demon\xf3w', 'tower', .347, .338),
    ('Loch Paj\xb9k\xf3w V1', 'spider', .683, .402),
    ('Kraina Gigant\xf3w', 'giants', .649, .118),
)
_window = None
_enabled = False

class TeleportMap(ui.BoardWithTitleBar):
    def __init__(self):
        ui.BoardWithTitleBar.__init__(self)
        self.AddFlag('float')
        self.SetTitleName('Mapa teleportacji - TAB')
        self.SetCloseEvent(self.Close)
        self.children = []
        self.dialog = None
        width = min(1200, wndMgr.GetScreenWidth() - 40)
        height = min(int(width * 942.0 / 1672), wndMgr.GetScreenHeight() - 100)
        width = int(height * 1672.0 / 942)
        self.SetSize(width + 20, height + 52)
        self.SetCenterPosition()
        self.image = ui.ExpandedImageBox()
        self.image.SetParent(self)
        self.image.SetPosition(10, 30)
        self.image.LoadImage('teleport_world_map_18_points.png')
        self.image.SetScale(float(width) / self.image.GetWidth(), float(height) / self.image.GetHeight())
        self.image.Show()
        for name, key, x, y in POINTS:
            button = ui.Button()
            button.SetParent(self)
            for method, state in ((button.SetUpVisual, 1), (button.SetOverVisual, 2), (button.SetDownVisual, 3)):
                method('d:/ymir work/ui/public/large_button_%02d.sub' % state)
            button.SetPosition(max(10, min(width - 80, int(x * width) - 34)), 30 + int(y * height) + 17)
            button.SetText(name)
            button.SetEvent(ui.__mem_func__(self.Select), key, name)
            button.Show()
            self.children.append(button)

    def Select(self, key, name):
        self.CloseDialog()
        if key == 'hell':
            self.dialog = ui.BoardWithTitleBar()
            self.dialog.AddFlag('float')
            self.dialog.SetSize(260, 165)
            self.dialog.SetTitleName('Piek\xb3o - wybierz respawn')
            self.dialog.SetCloseEvent(self.CloseDialog)
            self.dialog.SetCenterPosition()
            self.choices = []
            for index, kingdom in enumerate(('Shinsoo', 'Chunjo', 'Jinno')):
                b = ui.Button()
                b.SetParent(self.dialog)
                b.SetPosition(80, 40 + 34 * index)
                b.SetUpVisual('d:/ymir work/ui/public/large_button_01.sub')
                b.SetOverVisual('d:/ymir work/ui/public/large_button_02.sub')
                b.SetDownVisual('d:/ymir work/ui/public/large_button_03.sub')
                b.SetText(kingdom)
                b.SetEvent(ui.__mem_func__(self.Go), 'hell%d' % (index + 1))
                b.Show()
                self.choices.append(b)
            self.dialog.Show()
            self.dialog.SetTop()
            return
        self.Go(key)

    def Go(self, key):
        net.SendChatPacket('/tabteleport ' + key)
        self.Close()

    def CloseDialog(self):
        if self.dialog:
            self.dialog.Hide()
        self.dialog = None
        self.choices = []

    def Close(self):
        self.CloseDialog()
        self.Hide()

    def OnPressEscapeKey(self):
        self.Close()
        return True

    def OnKeyDown(self, key):
        if key == app.DIK_TAB:
            self.Close()
            return True
        return False

def ToggleWindow():
    global _window
    if _window is None:
        _window = TeleportMap()
    if _window.IsShow():
        _window.Close()
    else:
        _window.Show()
        _window.SetTop()

def DestroyWindow():
    global _window
    if _window:
        _window.Close()
    _window = None

def IsEnabled():
    return _enabled

def OnCommand(*args):
    # "MAPA_TAB 1" / "MAPA_TAB 0" from the server (quest mapa_tab).
    global _enabled
    _enabled = bool(args) and args[0] == '1'
    if not _enabled and _window:
        _window.Close()
