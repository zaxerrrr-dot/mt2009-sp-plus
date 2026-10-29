# -*- coding: utf-8 -*-
"""MT2009_PLUS_AUTOHUNT_NAVGRID_V1 - Auto Lowy's walk on the client's grid (client-2.0.30/root/uiautohunt.py) against a
fake exe: a wall, an island, the target moving away, a way held still, a way too long round, a drop out of reach, and
an exe without the functions (today's walk). Python 3 (and 2.7):

    python3 tests/uiautohunt_nav_test.py
"""
import math
import os
import sys
import types
import unittest
from collections import deque

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'client-patches', 'client-2.0.30', 'root')


class Dummy(object):
    def __init__(self, *a, **k):
        pass

    def __call__(self, *a, **k):
        return Dummy()

    def __getattr__(self, name):
        return Dummy()


class StubModule(types.ModuleType):
    def __getattr__(self, name):
        if name.startswith('__'):
            raise AttributeError(name)
        if name[:1].isupper() and name.isupper():
            return 0
        return Dummy


class Grid(object):
    """A fake background: cells of 100 units, '#' blocked. FindPath is a BFS (8 ways, no corner cutting)."""

    def __init__(self, rows):
        self.rows = rows
        self.h = len(rows)
        self.w = len(rows[0])
        self.temp = set()
        self.calls = []

    def open(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h and self.rows[y][x] != '#' and (x, y) not in self.temp

    def static(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h and self.rows[y][x] != '#'

    def comp(self, x, y):
        """the exe's components: the static grid only (NavBlock does not change them)"""
        if not self.static(x, y):
            return 0
        seen = {(x, y)}
        q = deque([(x, y)])
        while q:
            cx, cy = q.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (cx + dx, cy + dy)
                if n not in seen and self.static(*n):
                    seen.add(n)
                    q.append(n)
        return min(seen)

    # the exe's API (pixels)
    def GetCurrentMapName(self):
        return 'test_map'

    def IsNavReady(self):
        return 1

    def IsNavWalkable(self, x, y):
        return 1 if self.open(x // 100, y // 100) else 0

    def NavReach(self, sx, sy, dx, dy):
        a, b = self.comp(sx // 100, sy // 100), self.comp(dx // 100, dy // 100)
        if not a or not b:
            return -1
        return 1 if a == b else 0

    def NavBlock(self, x, y, r):
        cx, cy, rc = x // 100, y // 100, max(0, (r + 50) // 100)
        for yy in range(cy - rc, cy + rc + 1):
            for xx in range(cx - rc, cx + rc + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= rc * rc:
                    self.temp.add((xx, yy))
        self.calls.append(('block', x, y, r))

    def NavBlockClear(self):
        self.temp = set()
        self.calls.append(('clear',))

    def FindPath(self, sx, sy, dx, dy, nodes=0):
        self.calls.append(('find', sx, sy, dx, dy))
        s, t = (sx // 100, sy // 100), (dx // 100, dy // 100)
        if not self.open(*s) or not self.open(*t):
            return []
        prev = {s: None}
        q = deque([s])
        while q:
            c = q.popleft()
            if c == t:
                break
            for ddx in (-1, 0, 1):
                for ddy in (-1, 0, 1):
                    if not ddx and not ddy:
                        continue
                    n = (c[0] + ddx, c[1] + ddy)
                    if n in prev or not self.open(*n):
                        continue
                    if ddx and ddy and not (self.open(c[0] + ddx, c[1]) and self.open(c[0], c[1] + ddy)):
                        continue
                    prev[n] = c
                    q.append(n)
        if t not in prev:
            return []
        out = []
        c = t
        while c is not None:
            out.append((c[0] * 100 + 50, c[1] * 100 + 50))
            c = prev[c]
        return out[::-1]


class World(object):
    def __init__(self):
        self.now = 100.0
        self.me = [250.0, 250.0]
        self.mobs = {}
        self.walks = []
        self.target = 0


def install(world, grid):
    names = ['app', 'autologin', 'chat', 'chr', 'clientclock', 'item', 'mouseModule', 'net', 'player', 'skill', 'ui',
             'wndMgr', 'playerbot_lang', 'background', 'chrmgr', 'warpsafe', 'uipickupfilter']
    for n in names:
        sys.modules[n] = StubModule(n) if n != 'background' else types.ModuleType(n)
    sys.modules['playerbot_lang'].T = lambda pl, en=None: pl
    sys.modules['clientclock'].Now = lambda: world.now
    p = sys.modules['player']
    p.GetMainCharacterPosition = lambda: (world.me[0], world.me[1], 0.0)
    p.GetCharacterDistance = lambda vid: (math.hypot(world.mobs[vid][0] - world.me[0], world.mobs[vid][1] - world.me[1])
                                          if vid in world.mobs else -1)
    p.GetMainCharacterIndex = lambda: 1
    p.GetTargetVID = lambda: world.target
    p.ClearTarget = lambda: None
    p.SetAttackKeyState = lambda on: None
    p.IsBowEquipped = lambda: False
    p.IsTargetDead = lambda vid: False
    c = sys.modules['chr']
    c.GetPixelPosition = lambda vid: (world.mobs[vid][0], world.mobs[vid][1], 0.0)
    c.MoveToDestPosition = lambda index, x, y: world.walks.append((x, y))
    sys.modules['net'].SendChatPacket = lambda text: None
    b = sys.modules['background']
    if grid is not None:
        for name in ('GetCurrentMapName', 'IsNavReady', 'IsNavWalkable', 'NavReach', 'NavBlock', 'NavBlockClear',
                     'FindPath'):
            setattr(b, name, getattr(grid, name))
    else:
        b.GetCurrentMapName = lambda: 'test_map'
    sys.modules.pop('uiautohunt', None)
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    import uiautohunt
    h = uiautohunt.Hunter.__new__(uiautohunt.Hunter)
    h.config = uiautohunt.DefaultConfig()
    h.config['return'] = 0
    h.config_global = dict(uiautohunt.GLOBAL_DEFAULTS)
    h.configName = 'x'
    h.running = True
    h.mainWindow = h.lootWindow = None
    h.isLoaded = True
    h.pendingSession = None
    h.riderBuffStamp = {}
    h.riderBroken = False
    h.lastCommandAt = -1000.0
    h.pathKind = uiautohunt.PATH_KIND_NONE
    h.pathSeq = 0
    h.navMapName = None
    h.navOk = False
    h.navBlocks = False
    h.ResetState()
    h.Command = lambda text, now=None: None
    return uiautohunt, h


# 12 x 10 cells; a wall at x=6 with a gap at the bottom (y=8); an island (x=10..11, y=0..1) cut off by '#'
MAP = [
    '......#...#.',
    '......#...##',
    '......#.....',
    '......#.....',
    '......#.....',
    '......#.....',
    '......#.....',
    '......#.....',
    '............',
    '......#.....',
]


class NavTest(unittest.TestCase):
    def setUp(self):
        self.world = World()
        self.grid = Grid(MAP)
        self.mod, self.h = install(self.world, self.grid)

    def target(self, vid, x, y):
        self.world.mobs[vid] = [x, y]
        self.h.OnServerTarget(str(vid))

    def test_wall_walks_round(self):
        self.target(7, 950, 250)
        self.assertEqual(self.h.targetVid, 7)
        self.h.Chase(self.world.now)
        self.assertTrue(self.h.pathNav)
        self.assertEqual(self.h.pathPurpose, 'target')
        # the first step goes down along the wall, not straight at the target through it
        x, y = self.world.walks[-1]
        self.assertLess(x, 650)
        self.assertGreater(y, 250)
        # every waypoint stands on open ground
        for (px, py) in self.h.pathPoints:
            self.assertTrue(self.grid.IsNavWalkable(int(px), int(py)))

    def test_island_refused(self):
        self.target(9, 1150, 50)
        self.assertEqual(self.h.targetVid, 0)
        self.assertIn(9, self.h.blockedTargets)

    def test_replan_when_target_moves(self):
        self.target(7, 950, 250)
        self.h.Chase(self.world.now)
        finds = len([c for c in self.grid.calls if c[0] == 'find'])
        self.world.now += 0.6
        self.world.mobs[7] = [950, 750]       # 500 units away from the way's end
        self.h.Chase(self.world.now)
        self.assertEqual(len([c for c in self.grid.calls if c[0] == 'find']), finds + 1)
        self.assertEqual(self.h.pathEnd, (950, 750))

    def test_held_way_blocks_and_replans_then_gives_up(self):
        self.target(7, 950, 250)
        self.h.Chase(self.world.now)
        blocks = 0
        for step in range(12):
            self.world.now += 0.5                # the character never moves
            self.h.Chase(self.world.now)
            blocks = len([c for c in self.grid.calls if c[0] == 'block'])
        self.assertEqual(blocks, self.mod.NAV_STUCK_REPLANS)
        self.assertEqual(self.h.navGaveUp, ('target', 7))

    def test_too_long_round_is_skipped(self):
        # the gap moves far: a target right across the wall needs a long walk round
        self.grid.rows = ['......#.....'] * 9 + ['............']
        self.world.me = [450.0, 50.0]
        self.target(7, 850, 50)
        self.h.Chase(self.world.now)
        self.assertEqual(self.h.targetVid, 0)
        self.assertIn(7, self.h.blockedTargets)

    def test_loot_out_of_reach(self):
        self.h.lootVid = 55
        self.h.lootPos = (1150, 50)
        self.assertFalse(self.h.GoForLoot(self.world.now))
        self.assertIn(55, self.h.lootSkippedVids)
        self.assertEqual(self.h.lootVid, 0)

    def test_return_uses_the_grid(self):
        self.h.config['return'] = 1
        self.h.anchor = (950, 250)
        self.h.ReturnToAnchor(self.world.now)
        self.assertTrue(self.h.pathNav)
        self.assertEqual(self.h.pathPurpose, 'return')
        self.assertEqual(self.h.pathPoints[-1], (950, 250))


class OldExeTest(unittest.TestCase):
    def test_old_exe_walks_straight(self):
        world = World()
        mod, h = install(world, None)
        self.assertFalse(mod.NAV_EXE)
        world.mobs[7] = [950, 250]
        h.OnServerTarget('7')
        self.assertEqual(h.targetVid, 7)
        h.Chase(world.now)
        self.assertFalse(h.pathNav)
        x, y = world.walks[-1]
        self.assertGreater(x, 650)              # straight at it, as before


if __name__ == '__main__':
    unittest.main()
