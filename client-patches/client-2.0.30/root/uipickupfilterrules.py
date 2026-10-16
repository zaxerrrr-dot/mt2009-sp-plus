# Filtr podnoszenia - the windows (MT2009_PLUS_PICKUP_RULES_V1, Autor: Vekirion; the owner,
# 13 October: "a complex pickup filter ... based on the amount of bonuses,
# what those bonuses are and of what value", and the same day: replace the
# Ctrl+Z window - a left click takes a kind or not, a right click opens the
# kind's detailed filter: its bonuses, chosen items and levels).
#
#  - PickupFilterWindow (Ctrl+Z, "/filtr", the inventory's button): the
#    switch, the presets and the thirteen kinds. LEFT click: Tak / Nie.
#    RIGHT click: KindFilterWindow for that kind. A kind with rules says
#    "Filtr (N)".
#  - KindFilterWindow: the kind's rules (uipickupfilter.py keeps them and
#    sends them; the server decides, char_item.cpp). A rule asks for chosen
#    items (empty: any), refine +from..+to, wear level from..to and, for the
#    eight equipment kinds, bonuses: at least N of 1-5, N of 6/7 and up to
#    six "bonus X at least V" conditions (all / any / at least K). An item of
#    the kind is picked up when ANY switched-on rule matches; a kind with no
#    rules is picked up whole.
#  - ItemPicker: the item search - the server finds the kind's items by name
#    ("/pickup_items", PickupItemsList); refinable items come as a line
#    (every +N of it; the refine range narrows it).
#  - BonusPicker: the bonus list, with search.
# The look is the Dom Aukcyjny's (the owner, 13 October: "UI bardziej w stylu
# Domu aukcyjnego"): its bold fonts and colours, its big scaled buttons, framed
# buttons, list rows, check boxes, red X and hints are used as they are
# (uiauctionhouse.py), so both systems change together.
# Both windows edit a working copy; "Zapisz i wyslij" stores it, "Cofnij
# zmiany" drops it. "Sprawdz ekwipunek" runs the same test on the bag here in
# the client and writes the verdicts to the chat.
#
# Python 2.7 as the client has it; the texts are CP1250 escapes.

import app
import chat
import item
import player
import ui
import wndMgr

import localeinfo_point
import uiauctionhouse as ah	# the Dom Aukcyjny's look: fonts, colours, buttons, cards
import uiautohunt
import uipickupfilter as pf

# ---- colours (the Dom Aukcyjny's) ----------------------------------------------
COLOR_DIM = ah.COLOR_DIM
COLOR_GOLD = ah.COLOR_GOLD
COLOR_GOOD = ah.COLOR_GREEN
COLOR_BAD = 0xFFE07070
COLOR_BONUS = ah.COLOR_BONUS
COLOR_CARD_BORDER = ah.COLOR_CARD_BORDER
COLOR_CARD_FILL = ah.COLOR_CARD_FILL
ROW_IMAGE = ah.BONUS_ROW_IMAGE
LINE = ah.TEXT_LINE_LARGE

# ---- the bonuses offered ----------------------------------------------------
# (POINT_* name without "POINT_", the values lv1..lv5 of item_attr - offered as
# quick choices like the Dom Aukcyjny's bonus window; () where the table has
# none). The bonus numbers of this server's items are the POINT_* ones
# (uitooltip.py, MT2009_PLUS_RARE_NAMES_V1).
_V_STAT = (2, 4, 6, 8, 12)
_V_PCT = (1, 2, 3, 5, 8)
_V_PCT10 = (1, 2, 3, 5, 10)
_V_MOB = (2, 4, 6, 10, 20)
_V_RES = (2, 4, 6, 10, 15)
BONUS_CATALOG = (
    ('MAX_HP', (300, 500, 800, 1000, 1500)), ('MAX_SP', (20, 50, 90, 140, 250)),
    ('HT', _V_STAT), ('IQ', _V_STAT), ('ST', _V_STAT), ('DX', _V_STAT),
    ('ATT_SPEED', _V_PCT), ('MOV_SPEED', _V_MOB), ('CASTING_SPEED', _V_MOB),
    ('HP_REGEN', _V_STAT), ('SP_REGEN', _V_STAT), ('POISON_PCT', _V_PCT), ('STUN_PCT', _V_PCT),
    ('SLOW_PCT', _V_PCT), ('CRITICAL_PCT', _V_PCT10), ('PENETRATE_PCT', _V_PCT10),
    ('ATTBONUS_HUMAN', _V_PCT10), ('ATTBONUS_ANIMAL', _V_MOB), ('ATTBONUS_ORC', _V_MOB),
    ('ATTBONUS_MILGYO', _V_MOB), ('ATTBONUS_UNDEAD', _V_MOB), ('ATTBONUS_DEVIL', _V_MOB),
    ('STEAL_HP', _V_PCT10), ('STEAL_SP', _V_PCT10), ('MANA_BURN_PCT', _V_PCT10),
    ('BLOCK', _V_RES), ('DODGE', _V_RES), ('RESIST_SWORD', _V_RES), ('RESIST_TWOHAND', _V_RES),
    ('RESIST_DAGGER', _V_RES), ('RESIST_BELL', _V_RES), ('RESIST_FAN', _V_RES), ('RESIST_BOW', _V_RES),
    ('ST_REGEN', (2, 4, 6, 8, 10)), ('SKILL_DURATION', _V_STAT), ('RESIST_MAGIC', _V_RES),
    ('MAX_STAMINA', (50, 100, 150, 200, 400)), ('REFLECT_MELEE', (1, 2, 3, 6, 10)),
    ('POISON_REDUCE', (1, 2, 3, 4, 5)), ('MALL_EXPBONUS', (1, 2, 3, 4, 5)),
    ('GOLD_DOUBLE_BONUS', (2, 4, 6, 8, 20)), ('REFLECT_ARROW', (2, 4, 6, 8, 10)),
    ('IMMUNE_STUN', (1,)), ('IMMUNE_SLOW', (1,)), ('ATT_GRADE_BONUS', (5, 10, 15, 30, 50)),
    # rare (6th/7th), awards and the like
    ('ATTBONUS_MONSTER', ()), ('ATTBONUS_WARRIOR', ()), ('ATTBONUS_ASSASSIN', ()),
    ('ATTBONUS_SURA', ()), ('ATTBONUS_SHAMAN', ()), ('RESIST_WARRIOR', ()),
    ('RESIST_ASSASSIN', ()), ('RESIST_SURA', ()), ('RESIST_SHAMAN', ()),
    ('SKILL_DAMAGE_BONUS', ()), ('NORMAL_HIT_DAMAGE_BONUS', ()), ('SKILL_DEFEND_BONUS', ()),
    ('NORMAL_HIT_DEFEND_BONUS', ()), ('MAX_HP_PCT', ()), ('MAX_SP_PCT', ()),
    ('DEF_GRADE_BONUS', ()), ('MAGIC_ATT_GRADE_BONUS', ()), ('MAGIC_DEF_GRADE_BONUS', ()),
    ('EXP_DOUBLE_BONUS', ()), ('ITEM_DROP_BONUS', ()), ('KILL_HP_RECOVERY', ()),
    ('KILL_SP_RECOVER', ()), ('RESIST_FIRE', ()), ('RESIST_ELEC', ()), ('RESIST_WIND', ()),
    ('RESIST_ICE', ()), ('RESIST_EARTH', ()), ('RESIST_DARK', ()), ('RESIST_CRITICAL', ()),
    ('RESIST_PENETRATE', ()), ('ATTBONUS_BOSS', ()), ('ATTBONUS_STONE', ()),
    ('ATT_BONUS', ()), ('DEF_BONUS', ()),
)

MODE_TEXTS = ('Wszystkie', 'Dowolny', 'Co najmniej K')
SLOT_TEXTS = ('Ka\xbfdy', '1-5', '6-7')
# MT2009_PLUS_PICKUP_COND_ABSENT_V1: the condition's kind (pf.COND_*)
OP_TEXTS = ('Min.', 'Brak / >')
OP_HINT = ('Min.: przedmiot musi mie\xe6 ten bonus, co najmniej X. Klik: Brak / >.\n'
    'Brak / >: podnosi przedmiot bez tego bonusu, a z nim tylko powy\xbfej X. Klik: Min.')
COND_KEYS = ('bonus', 'ge', 'bar', 'slots', 'remove')
ITEM_SHOWN = 12		# the item chips of a rule (pf.ITEM_MAX is the server's limit)

_catalog = []
_values = {}


def _FormatlessLabel(text):
    out = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == '%':
            # a printf field: %d, %+d, %.1f, %%
            j = i + 1
            while j < len(text) and text[j] in '+- #0123456789.':
                j += 1
            i = j + 1
            continue
        out.append(ch)
        i += 1
    return ' '.join(''.join(out).split()).strip(' :+-.')


def BonusLabel(kind):
    """A bonus's name from its tooltip text ("Maks. PZ +%d" -> "Maks. PZ")."""
    text = localeinfo_point.AFFECT_DICT.get(kind)
    if callable(text):
        try:
            text = text.func_closure[0].cell_contents
        except Exception:
            text = None
    if not isinstance(text, str):
        return 'Bonus nr %d' % kind
    return _FormatlessLabel(text) or 'Bonus nr %d' % kind


def Catalog(everything=False):
    """[(type, label)]: the usual equipment bonuses; with everything, every
    other bonus the tooltip knows after them."""
    if not _catalog:
        seen = set()
        for name, values in BONUS_CATALOG:
            kind = getattr(player, 'POINT_' + name, None)
            if kind is None or kind in seen:
                continue
            seen.add(kind)
            _catalog.append((kind, BonusLabel(kind)))
            if values:
                _values[kind] = values
    if not everything:
        return list(_catalog)
    known = set(kind for kind, label in _catalog)
    rest = [(kind, BonusLabel(kind)) for kind in localeinfo_point.AFFECT_DICT.keys()
        if isinstance(kind, int) and 0 < kind < 256 and kind not in known]
    rest.sort(key=lambda entry: entry[1].lower())
    return list(_catalog) + rest


def BonusValues(kind):
    """item_attr's lv1..lv5 values of a bonus, () when unknown."""
    Catalog()
    return _values.get(kind, ())


def MaxValueHint(kind):
    values = BonusValues(kind)
    return values[-1] if values else 0


def Short(text, limit):
    return text if len(text) <= limit else text[:max(1, limit - 2)] + '..'


# ---- items ------------------------------------------------------------------------
# item.SelectItem of a vnum the client does not know selects another item (the
# Dom Aukcyjny found it: uiauctionhouse.ItemNameOf); a name the same as that of
# a vnum surely missing is "unknown".
MISSING_ITEM_VNUM = 2147483000
SENTINEL_ITEM_VNUM = 1
_fallbackName = []
_nameCache = {}


def _Type(name):
    return getattr(item, name, None)


def _SelectedName(vnum):
    item.SelectItem(SENTINEL_ITEM_VNUM)
    item.SelectItem(vnum)
    return item.GetItemName() or ''


def ItemNameOf(vnum):
    """The item's name, or '' when the client does not know it."""
    if vnum in _nameCache:
        return _nameCache[vnum]
    try:
        if not _fallbackName:
            _fallbackName.append(_SelectedName(MISSING_ITEM_VNUM))
        name = _SelectedName(vnum)
    except Exception:
        return ''
    if vnum != SENTINEL_ITEM_VNUM and name == _fallbackName[0]:
        name = ''
    _nameCache[vnum] = name
    return name


def StripPlus(name):
    plus = name.rfind('+')
    if plus > 0 and name[plus + 1:].strip().isdigit():
        return name[:plus].rstrip()
    return name


def LineName(vnum):
    """A line's name without its "+N" (its +0, or the first +N the client knows)."""
    for offset in xrange(10):
        name = ItemNameOf(vnum + offset)
        if name:
            return StripPlus(name)
        if offset == 0 and vnum % 10:
            break
    return 'Przedmiot %d' % vnum


def IsRefinableType(itemType):
    return itemType in (_Type('ITEM_TYPE_WEAPON'), _Type('ITEM_TYPE_ARMOR'), _Type('ITEM_TYPE_BELT'))


def KindOfSelected():
    """The filter's kind bit of the selected item (char_item.cpp,
    Mt2009PlusPickupKindOf); 0 for yang."""
    itemType = item.GetItemType()
    subType = item.GetItemSubType()
    if itemType == _Type('ITEM_TYPE_ELK'):
        return 0
    if itemType == _Type('ITEM_TYPE_WEAPON'):
        return 1 << 6 if subType == _Type('WEAPON_ARROW') else 1 << 0
    if itemType == _Type('ITEM_TYPE_ARMOR'):
        for name, bit in (('ARMOR_BODY', 1), ('ARMOR_HEAD', 7), ('ARMOR_SHIELD', 8), ('ARMOR_WRIST', 9),
                ('ARMOR_FOOTS', 10), ('ARMOR_NECK', 11), ('ARMOR_EAR', 12)):
            if subType == _Type(name):
                return 1 << bit
        return 1 << 2
    if itemType in (_Type('ITEM_TYPE_RING'), _Type('ITEM_TYPE_BELT')):
        return 1 << 2
    if itemType == _Type('ITEM_TYPE_USE'):
        if subType in (_Type('USE_POTION'), _Type('USE_POTION_NODELAY'), _Type('USE_ABILITY_UP')):
            return 1 << 3
        return 1 << 6
    if itemType in (_Type('ITEM_TYPE_SKILLBOOK'), _Type('ITEM_TYPE_SKILLFORGET')):
        return 1 << 4
    if itemType == _Type('ITEM_TYPE_METIN'):
        return 1 << 5
    return 1 << 6


def LevelOfSelected():
    limitLevel = _Type('LIMIT_LEVEL')
    try:
        for i in xrange(getattr(item, 'LIMIT_MAX_NUM', 2)):
            limitType, value = item.GetLimit(i)
            if limitType == limitLevel:
                return value
    except Exception:
        pass
    return 0


def RefineOf(name):
    """+N from the name, as CItem::GetRefineLevel reads it."""
    plus = name.rfind('+')
    if plus < 0:
        return 0
    try:
        return int(name[plus + 1:].strip())
    except ValueError:
        return 0


def CountHint(number, slots):
    """MT2009_PLUS_PICKUP_COUNT_HINT_V1: the hint of a bonus count button -
    how many bonuses (any, in slots 1-5 or 6/7) the item must have, whatever
    they are; the conditions below are separate."""
    if not number:
        return 'Liczba bonus\xf3w %s na przedmiocie: dowolna (tak\xbfe 0)' % slots
    return 'Liczba bonus\xf3w %s na przedmiocie: co najmniej %d (dowolne bonusy)' % (slots, number)


def OtherHint(number):
    """MT2009_PLUS_PICKUP_OTHER_BONUSES_V1: the hint of an "other bonuses" button."""
    if not number:
        return 'Wy\xb3\xb9czone - decyduj\xb9 tylko warunki poni\xbfej'
    return ('Podnie\x9c te\xbf przedmiot z co najmniej %d bonusami (1-5) innymi ni\xbf te z warunk\xf3w, '
        'nawet gdy warunki nie s\xb9 spe\xb3nione' % number)


def CondFields(cond):
    """(type, value, slots, op) of a condition saved with or without its op
    (MT2009_PLUS_PICKUP_COND_ABSENT_V1)."""
    return (tuple(cond) + (pf.COND_AT_LEAST,))[:4]


def RuleMatches(rule, info):
    """The server's Mt2009PlusPickupRuleMatches. info: 'line', 'refinable',
    'refine', 'level', 'attrs' (seven (type, value), five normal, two rare)."""
    if rule['items'] and info['line'] not in rule['items']:
        return False
    if info['refinable'] and (rule['refine_min'] > 0 or rule['refine_max'] < pf.REFINE_MAX):
        if not rule['refine_min'] <= info['refine'] <= rule['refine_max']:
            return False
    if rule['level_min'] or rule['level_max']:
        if info['level'] < rule['level_min'] or (rule['level_max'] and info['level'] > rule['level_max']):
            return False
    attrs = info['attrs']
    normal = 0
    for kind, value in attrs[:5]:
        if not kind:
            break
        normal += 1
    rare = len([1 for kind, value in attrs[5:7] if kind])
    if normal < rule['min_normal'] or rare < rule['min_rare']:
        return False
    conds = rule['conds']
    if not conds:
        return True
    # MT2009_PLUS_PICKUP_OTHER_BONUSES_V1: or at least N bonuses (slots 1-5) of
    # kinds none of the conditions names
    otherMin = rule.get('other_min', 0)
    if otherMin > 0:
        named = [CondFields(cond)[0] for cond in conds]
        if len([1 for kind, value in attrs[:5] if kind and kind not in named]) >= otherMin:
            return True
    met = 0
    for cond in conds:
        kind, minValue, slots, op = CondFields(cond)
        if slots == pf.SLOTS_RARE:
            part = attrs[5:7]
        elif slots == pf.SLOTS_NORMAL:
            part = attrs[:5]
        else:
            part = attrs[:7]
        if op == pf.COND_ABSENT_OR_ABOVE:
            # MT2009_PLUS_PICKUP_COND_ABSENT_V1: no such bonus, or it above the value
            found = [attrValue for attrKind, attrValue in part if attrKind == kind]
            if not found or max(found) > minValue:
                met += 1
            continue
        for attrKind, attrValue in part:
            if attrKind == kind and attrValue >= minValue:
                met += 1
                break
    if rule['mode'] == pf.MODE_ANY:
        return met >= 1
    if rule['mode'] == pf.MODE_AT_LEAST:
        return met >= min(rule['need'], len(conds))
    return met == len(conds)


def TestInventory(rules, kinds, onlyKind=0):
    """What the filter (kinds, rules) would do with the bag's items -
    written to the chat. onlyKind: one kind's items only."""
    rules = [rule for rule in rules if rule['on']]
    cells = getattr(player, 'INVENTORY_MAX_NUM', 0) or \
        player.INVENTORY_PAGE_SIZE * getattr(player, 'INVENTORY_PAGE_COUNT', 4)
    lines = []
    taken = left = 0
    seen = set()
    for cell in xrange(cells):
        vnum = player.GetItemIndex(cell)
        if not vnum:
            continue
        item.SelectItem(vnum)
        bit = KindOfSelected()
        if not bit or (onlyKind and not bit & onlyKind):
            continue
        name = item.GetItemName()
        refinable = IsRefinableType(item.GetItemType())
        level = LevelOfSelected()
        try:
            attrs = [tuple(player.GetItemAttribute(cell, i)) for i in xrange(7)]
        except Exception:
            attrs = [(0, 0)] * 7
        key = (vnum, tuple(attrs))
        if key in seen:
            continue
        seen.add(key)
        info = {'line': vnum - vnum % 10 if refinable else vnum, 'refinable': refinable,
            'refine': RefineOf(name) if refinable else 0, 'level': level, 'attrs': attrs}
        if not kinds & bit:
            verdict, why = False, 'rodzaj wy\xb3\xb9czony'
        else:
            forKind = [rule for rule in rules if rule['kinds'] & bit]
            if not forKind:
                verdict, why = True, 'rodzaj bez filtra'
            else:
                hit = None
                for rule in forKind:
                    if RuleMatches(rule, info):
                        hit = rule
                        break
                verdict = hit is not None
                why = ('regu\xb3a "%s"' % hit['name']) if hit else 'nie pasuje \xbfadna regu\xb3a'
        if verdict:
            taken += 1
        else:
            left += 1
        lines.append('%s %s - %s' % ('[TAK]' if verdict else '[NIE]', name, why))
    chat.AppendChat(chat.CHAT_TYPE_INFO, '--- Test filtra na ekwipunku (ustawienia z okna, tak\xbfe niezapisane) ---')
    for line in lines[:20]:
        chat.AppendChat(chat.CHAT_TYPE_INFO, line)
    if len(lines) > 20:
        chat.AppendChat(chat.CHAT_TYPE_INFO, '... i %d wi\xeacej.' % (len(lines) - 20))
    if not lines:
        chat.AppendChat(chat.CHAT_TYPE_INFO, 'Brak takich przedmiot\xf3w w ekwipunku.')
    chat.AppendChat(chat.CHAT_TYPE_INFO, 'Podni\xf3s\xb3bym: %d, zostawi\xb3bym: %d.%s' % (taken, left,
        '' if pf.IsActive() else ' (filtr jest wy\xb3\xb9czony - teraz podnosisz wszystko)'))


# ---- controls: the Dom Aukcyjny's, put in place -----------------------------------
class _Call(object):
    """An event with its argument fixed - for the Dom Aukcyjny's buttons, which
    call their events without one."""

    def __init__(self, func, *args):
        self.func = func
        self.args = args

    def __call__(self):
        if self.func:
            self.func(*self.args)


def Place(widget, parent, x, y, hint=None):
    widget.SetParent(parent)
    widget.SetPosition(x, y)
    if hint:
        ah.SetHint(widget, hint)
    widget.Show()
    return widget


def Text(parent, x, y, text='', color=None, large=True):
    return ah.MakeText(parent, x, y, text, color, large)


def Card(parent, x, y, w, h):
    """A panel like the Dom Aukcyjny's category panel: a thin frame, dark fill."""
    return (ah.MakeBar(parent, x, y, w, h, COLOR_CARD_BORDER),
        ah.MakeBar(parent, x + 1, y + 1, w - 2, h - 2, COLOR_CARD_FILL))


def Edit(parent, x, y, w, maxLen, numeric, placeholder='', height=22):
    slot, edit = ah.MakeEdit(parent, x, y, w, maxLen, numeric, ah.SearchEditLine, height)
    if placeholder:
        try:
            edit.SetPlaceholder(placeholder, ah.FontName())
        except Exception:
            pass
    return slot, edit


def EditNumber(edit, low, high, default):
    try:
        value = int(edit.GetText().strip() or str(default))
    except ValueError:
        return default
    return max(low, min(high, value))


def ClampToScreen(window, x, y, w, h):
    try:
        x = max(0, min(x, wndMgr.GetScreenWidth() - w))
        y = max(0, min(y, wndMgr.GetScreenHeight() - h))
    except Exception:
        pass
    window.SetPosition(x, y)


def ItemIcon(vnum):
    try:
        item.SelectItem(vnum)
        return item.GetIconImageFileName()
    except Exception:
        return ''


class ItemCard(ui.Window):
    """A chosen item: a card like a Dom Aukcyjny offer - its icon in the
    offer's icon frame, the name, a red X that takes it off the rule."""
    ICON = 32

    def __init__(self, width, height, removeEvent, index):
        ui.Window.__init__(self)
        self.SetSize(width, height)
        self.board = ui.ThinBoard()
        self.board.SetParent(self)
        self.board.SetPosition(0, 0)
        self.board.SetSize(width, height)
        self.board.AddFlag('not_pick')
        self.board.Show()
        top = (height - self.ICON) // 2
        self.iconBack = ah.MakeBar(self, 6 + 3, top + 3, self.ICON - 6, self.ICON - 6, ah.COLOR_ICON_BACK)
        self.iconSlot = ah.MakeScaledImage(self, 6, top, ah.ICON_SLOT_IMAGE, self.ICON, self.ICON)
        self.icon = ui.ExpandedImageBox()
        self.icon.SetParent(self)
        self.icon.SetPosition(6, top)
        self.icon.AddFlag('not_pick')
        self.icon.Show()
        self.nameWidth = width - self.ICON - 14 - ah.REMOVE_SIZE - 8
        self.name = Text(self, self.ICON + 12, (height - LINE) // 2, '', None, False)
        self.remove = Place(ah.IconButton(ah.REMOVE_IMAGE, ah.REMOVE_HOVER_IMAGE, 'Usu\xf1', 16,
            removeEvent, index), self, width - 16 - 6, (height - 16) // 2)

    def __del__(self):
        ui.Window.__del__(self)

    def SetItem(self, vnum):
        ah.FitText(self.name, LineName(vnum), self.nameWidth)
        fileName = ItemIcon(vnum)
        try:
            self.icon.LoadImage(fileName)
            w, h = self.icon.GetWidth(), self.icon.GetHeight()
            if w > 0 and h > 0:
                scale = min(float(self.ICON) / w, float(self.ICON) / h, 1.0)
                self.icon.SetScale(scale, scale)
                self.icon.SetPosition(6 + (self.ICON - int(w * scale)) // 2,
                    (self.GetHeight() - int(h * scale)) // 2)
            self.icon.Show()
        except Exception:
            self.icon.Hide()


# ---- pickers: a searchable list, as the Dom Aukcyjny's bonus list -------------------
class ListPicker(ui.BoardWithTitleBar):
    """A list with a search line and a scroll bar; a click on a row calls the
    event with that row's key and closes the list."""
    WIDTH = 340
    ROWS = 14
    LINE = 22
    TOP = 70
    LIST_W = 286
    HEIGHT = TOP + ROWS * LINE + 40

    def __init__(self, title):
        ui.BoardWithTitleBar.__init__(self)
        self.event = None
        self.entries = []		# [(key, label)]
        self.shown = []
        self.offset = 0
        self.scrolling = False
        self.lastFilter = None
        self.keep = []
        self.AddFlag('movable')
        self.AddFlag('float')
        self.SetSize(self.WIDTH, self.HEIGHT)
        self.SetTitleName(title)
        self.SetCloseEvent(ui.__mem_func__(self.Close))
        self.searchSlot, self.searchEdit = Edit(self, 14, 36, 210, 30, False, 'Szukaj...', 26)
        self.extraButton = Place(ah.FrameButton(86, 26, '', ui.__mem_func__(self.OnExtra)), self, 232, 36)
        self.extraButton.Hide()
        self.keep += list(Card(self, 12, self.TOP - 3, self.LIST_W + 17 + 6, self.ROWS * self.LINE + 6))
        self.rows = []
        for index in xrange(self.ROWS):
            row = Place(ah.ImageListButton(self.LIST_W, self.LINE - 1, ROW_IMAGE,
                ui.__mem_func__(self.OnPick), index), self, 15, self.TOP + index * self.LINE)
            self.rows.append(row)
        self.scrollBar = ui.ScrollBar()
        self.scrollBar.SetParent(self)
        self.scrollBar.SetPosition(15 + self.LIST_W + 1, self.TOP)
        self.scrollBar.SetScrollBarSize(self.ROWS * self.LINE)
        self.scrollBar.SetScrollEvent(ui.__mem_func__(self.OnScroll))
        self.hint = Text(self, 14, self.TOP + self.ROWS * self.LINE + 12, '', COLOR_DIM)
        self.Hide()

    def __del__(self):
        ui.BoardWithTitleBar.__del__(self)

    def Open(self, event, x, y):
        self.event = event
        self.searchEdit.SetText('')
        self.lastFilter = None
        self.OnOpen()
        ClampToScreen(self, x, y, self.WIDTH, self.HEIGHT)
        self.Show()
        self.SetTop()
        self.searchEdit.SetFocus()

    def OnOpen(self):
        pass

    def OnExtra(self):
        pass

    def SetEntries(self, entries, hint):
        self.entries = entries
        self.hint.SetText(hint)
        self.ApplyFilter(False)

    def ApplyFilter(self, filtering=True):
        text = ah.PolishLower(self.searchEdit.GetText().strip())
        self.lastFilter = text
        if text and filtering:
            self.shown = [entry for entry in self.entries if text in ah.PolishLower(entry[1])]
        else:
            self.shown = list(self.entries)
        self.offset = 0
        limit = self.MaxOffset()
        if limit > 0:
            self.scrolling = True
            self.scrollBar.SetMiddleBarSize(float(self.ROWS) / len(self.shown))
            self.scrollBar.SetPos(0.0)
            self.scrolling = False
            self.scrollBar.Show()
        else:
            self.scrollBar.Hide()
        self.RefreshRows()

    def MaxOffset(self):
        return max(0, len(self.shown) - self.ROWS)

    def RowText(self, entry):
        return Short(entry[1], 36)

    def RefreshRows(self):
        for index, row in enumerate(self.rows):
            at = self.offset + index
            if at < len(self.shown):
                row.SetLabel(self.RowText(self.shown[at]))
                row.SetSelected(False)
                row.Show()
            else:
                row.Hide()

    def OnSearchChanged(self, text):
        self.ApplyFilter()

    def OnUpdate(self):
        text = ah.PolishLower(self.searchEdit.GetText().strip())
        if text != self.lastFilter:
            self.lastFilter = text
            self.OnSearchChanged(text)

    def OnScroll(self):
        if self.scrolling:
            return
        self.offset = int(self.scrollBar.GetPos() * self.MaxOffset() + 0.5)
        self.RefreshRows()

    def OnMouseWheel(self, length):
        limit = self.MaxOffset()
        if limit > 0:
            self.offset = max(0, min(limit, self.offset + (-2 if length > 0 else 2)))
            self.scrolling = True
            self.scrollBar.SetPos(float(self.offset) / limit)
            self.scrolling = False
            self.RefreshRows()
        return True

    def OnPick(self, index):
        at = self.offset + index
        if at < len(self.shown) and self.event:
            event = self.event
            key = self.shown[at][0]
            self.Close()
            event(key)

    def Close(self):
        self.event = None
        self.searchEdit.KillFocus()
        ah.HideHint()
        self.Hide()

    def OnPressEscapeKey(self):
        self.Close()
        return True

    def Destroy(self):
        self.Hide()
        self.event = None
        self.rows = []
        self.keep = []


class BonusPicker(ListPicker):
    def __init__(self):
        ListPicker.__init__(self, 'Wybierz bonus')
        self.everything = False
        ah.SetHint(self.extraButton, 'Typowe bonusy ekwipunku albo wszystkie znane klientowi')
        self.extraButton.Show()

    def OnOpen(self):
        self.Reload()

    def Reload(self):
        self.extraButton.SetText('Typowe' if self.everything else 'Wszystkie')
        entries = Catalog(self.everything)
        self.SetEntries(entries, 'Bonus\xf3w: %d' % len(entries))

    def RowText(self, entry):
        top = MaxValueHint(entry[0])
        return Short(entry[1], 30) + ('  (max %d)' % top if top else '')

    def OnExtra(self):
        self.everything = not self.everything
        self.Reload()


class ItemPicker(ListPicker):
    """The server finds the kind's items by name (uipickupfilter.RequestItems);
    a refinable item comes as its line, every +N of it."""
    SEARCH_DELAY = ah.NAMES_DELAY + 0.15

    def __init__(self):
        ListPicker.__init__(self, 'Wybierz przedmiot')
        self.kind = 0
        self.askAt = 0.0
        self.asked = ''

    def Open(self, event, x, y, kind):
        self.kind = kind
        ListPicker.Open(self, event, x, y)

    def OnOpen(self):
        self.askAt = 0.0
        self.asked = ''
        self.SetTitleName('Wybierz przedmiot: %s' % pf.KindLabel(self.kind))
        self.SetEntries([], 'Wpisz co najmniej 2 litery nazwy.')

    def OnSearchChanged(self, text):
        # the server is asked once the typing stops for a moment
        import clientclock  # MT2009_PLUS_PICKUP_SYNC_CLOCK_V1: never runs backwards at a warp
        self.askAt = clientclock.Now() + self.SEARCH_DELAY

    def OnUpdate(self):
        ListPicker.OnUpdate(self)
        import clientclock
        if self.askAt and clientclock.Now() >= self.askAt:
            self.askAt = 0.0
            text = self.searchEdit.GetText().strip()
            if text == self.asked:
                return
            self.asked = text
            if pf.RequestItems(self.kind, text, ui.__mem_func__(self.OnFound)):
                self.hint.SetText('Szukam...')
            else:
                self.SetEntries([], 'Wpisz co najmniej 2 litery nazwy.')

    def OnFound(self, vnums):
        entries = []
        for vnum in vnums:
            name = LineName(vnum)
            if name:
                entries.append((vnum, name))
        hint = 'Znaleziono: %d' % len(entries) if entries else 'Nic nie znaleziono.'
        if len(vnums) >= 36:
            hint += ' - doprecyzuj nazw\xea'
        self.SetEntries(entries, hint)


class Panelled(ui.BoardWithTitleBar):
    """The shared bits of the two filter windows."""

    def __init__(self):
        ui.BoardWithTitleBar.__init__(self)
        self.keep = []

    def __del__(self):
        ui.BoardWithTitleBar.__del__(self)

    def K(self, widget):
        self.keep.append(widget)
        return widget

    def Label(self, x, y, text, color=None, large=True):
        return self.K(Text(self, x, y, text, color, large))

    def Card(self, x, y, w, h):
        self.keep.extend(Card(self, x, y, w, h))

    def Big(self, x, y, w, h, text, event, rightEvent=None, hint=None):
        """The Dom Aukcyjny's big button (Szukaj, Poziom, Bonus) in any size."""
        return self.K(Place(ah.ScaledButton(w, h, text, event, rightEvent), self, x, y, hint))

    def Frame(self, x, y, w, h, text, event, gold=False, hint=None, *args):
        if gold:
            button = ah.FrameButton(w, h, text, event, ah.COLOR_BUY_BORDER, ah.COLOR_BUY_TEXT, *args)
        else:
            button = ah.FrameButton(w, h, text, event, ah.COLOR_OPTION_BORDER, ah.MainColor(), *args)
        return self.K(Place(button, self, x, y, hint))

    def Option(self, x, y, w, h, text, event, hint=None, *args):
        return self.K(Place(ah.OptionButton(w, h, text, event, *args), self, x, y, hint))

    def DestroyControls(self):
        ah.HideHint()
        self.keep = []


# ---- the main window (Ctrl+Z) ------------------------------------------------------
class PickupFilterWindow(Panelled):
    WIDTH = 540
    PAD = 14
    COLS = 3
    KIND_H = 30
    KIND_GAP = 4
    TOOL_H = 30

    def __init__(self):
        Panelled.__init__(self)
        self.kindButtons = {}
        self.presets = []
        self.presetPopup = None
        self.kindW = (self.WIDTH - 2 * self.PAD - 2 * 6 - (self.COLS - 1) * self.KIND_GAP) // self.COLS
        rows = (len(uiautohunt.LOOT_KINDS) + self.COLS - 1) // self.COLS
        self.kindsY = 36 + self.TOOL_H + 10 + 26 + 12
        self.kindsH = 6 + 22 + rows * (self.KIND_H + self.KIND_GAP) - self.KIND_GAP + 8
        self.footY = self.kindsY + self.kindsH + 10
        self.AddFlag('movable')
        self.AddFlag('float')
        self.SetSize(self.WIDTH, self.footY + 70)
        self.SetTitleName('Filtr podnoszenia')
        self.SetCloseEvent(ui.__mem_func__(self.Close))
        self.Build()
        self.SetCenterPosition()
        self.Hide()

    def Build(self):
        W, P = self.WIDTH, self.PAD
        # toolbar: the switch and the presets, as the Dom Aukcyjny's top bar
        y = 36
        third = (W - 2 * P - 2 * 8) // 3
        self.onButton = self.Big(P, y, third, self.TOOL_H, '', ui.__mem_func__(self.OnToggleFilter),
            hint='W\xb3\xb9cz / wy\xb3\xb9cz filtr (wy\xb3\xb9czony: podnosisz wszystko)')
        self.presetButton = self.Big(P + third + 8, y, third, self.TOOL_H, 'Presety', ui.__mem_func__(self.OpenPresets),
            hint='Wczytaj zapisany preset (ca\xb3y filtr)')
        self.testButton = self.Big(P + 2 * (third + 8), y, third, self.TOOL_H, 'Sprawd\x9f ekwipunek',
            ui.__mem_func__(self.OnTest), hint='Co filtr zrobi\xb3by z przedmiotami z ekwipunku (na czacie)')
        y += self.TOOL_H + 10
        slot, self.presetEdit = Edit(self, P, y, W - 2 * P - 2 * (96 + 8), pf.NAME_MAX, False, 'Nazwa presetu', 26)
        self.K(slot)
        self.Frame(W - P - 2 * 96 - 8, y, 96, 26, 'Zapisz', ui.__mem_func__(self.OnPresetSave), True,
            'Zapisz obecny filtr jako preset o tej nazwie')
        self.Frame(W - P - 96, y, 96, 26, 'Usu\xf1', ui.__mem_func__(self.OnPresetDelete), False,
            'Usu\xf1 preset o tej nazwie')
        # kinds: a card of big buttons
        y = self.kindsY
        self.Card(P, y, W - 2 * P, self.kindsH)
        self.Label(P + 8, y + 6, 'Rodzaje')
        self.mouseHint = self.Label(P + 90, y + 7, '', COLOR_DIM, False)
        top = y + 6 + 22
        for index, (key, label, bit) in enumerate(uiautohunt.LOOT_KINDS):
            x = P + 6 + (index % self.COLS) * (self.kindW + self.KIND_GAP)
            button = self.Big(x, top + (index // self.COLS) * (self.KIND_H + self.KIND_GAP), self.kindW, self.KIND_H,
                label, _Call(ui.__mem_func__(self.OnToggleKind), bit), _Call(ui.__mem_func__(self.OnOpenKind), bit))
            self.kindButtons[bit] = (button, label)
        # footer
        y = self.footY
        self.statusText = self.Label(P, y, '', COLOR_DIM)
        self.Label(P, y + 18, 'Dzia\xb3a dla Z, `, peta, Auto \xa3ow\xf3w i Towarzysza. Yang zawsze.', COLOR_DIM, False)
        self.Frame(W - P - 110, y + 4, 110, 26, 'Zamknij', ui.__mem_func__(self.Close))

    # -- opening
    def Open(self):
        self.Refresh()
        self.Show()
        self.SetTop()

    def Close(self):
        self.presetEdit.KillFocus()
        if self.presetPopup is not None:
            self.presetPopup.Close()
        ah.HideHint()
        self.Hide()

    def OnPressEscapeKey(self):
        self.Close()
        return True

    def Destroy(self):
        self.Hide()
        if self.presetPopup is not None:
            self.presetPopup.Destroy()
            self.presetPopup = None
        self.DestroyControls()
        self.kindButtons = {}

    def Refresh(self):
        active = pf.IsActive()
        self.onButton.SetText('Filtr: %s' % pf.OnStateText())
        self.onButton.text.SetPackedFontColor(COLOR_GOOD if active else COLOR_BAD)
        kinds = pf.GetKinds()
        for bit, (button, label) in self.kindButtons.items():
            count = pf.KindRuleCount(bit)
            if not kinds & bit:
                text, color, hint = 'Nie', COLOR_BAD, 'Nie podnosz\xea'
            elif count:
                text, color, hint = 'Filtr %d' % count, COLOR_GOLD, 'Tylko to, co pasuje do regu\xb3 (%d)' % count
            else:
                text, color, hint = 'Tak', COLOR_GOOD, 'Podnosz\xea wszystko'
            button.SetText('%s: %s' % (label, text))
            button.text.SetPackedFontColor(color)
            ah.SetHint(button, '%s - %s. LPM: tak / nie%s' % (label, hint,
                ', PPM: dok\xb3adny filtr' if pf.AdvancedEnabled() else ''))
        if not active:
            self.statusText.SetText('Filtr wy\xb3\xb9czony - podnosisz wszystko.')
        elif not pf.AdvancedEnabled():
            self.statusText.SetText('Prosty filtr (zaawansowany: Opcje Gry -> Dodatkowe).')
        else:
            self.statusText.SetText(pf.RulesAckText())
        if pf.AdvancedEnabled():
            self.mouseHint.SetText('LPM: podnosz\xea tak / nie     PPM: dok\xb3adny filtr')
        else:
            self.mouseHint.SetText('LPM: podnosz\xea tak / nie')

    # -- the switch and the kinds
    def OnToggleFilter(self):
        pf.ToggleOn()

    def OnToggleKind(self, bit):
        pf.ToggleKind(bit)

    def OnOpenKind(self, bit):
        pf.OpenKindWindow(bit)

    def OnTest(self):
        TestInventory(pf.GetRules() if pf.AdvancedEnabled() else [], pf.GetKinds())

    # -- presets
    def OpenPresets(self):
        presets = pf.LoadPresets()
        if not presets:
            chat.AppendChat(chat.CHAT_TYPE_INFO, 'Brak preset\xf3w - wpisz nazw\xea i kliknij "Zapisz".')
            return
        if self.presetPopup is not None:
            self.presetPopup.Destroy()
        width = self.presetButton.GetWidth()
        choices = [(Short(preset['name'], 22), index) for index, preset in enumerate(presets)]
        self.presetPopup = ah.ChoicePopup(choices, width, ui.__mem_func__(self.OnPresetPicked))
        x, y = self.presetButton.GetGlobalPosition()
        self.presetPopup.Open(x, y + self.presetButton.GetHeight(), -1)

    def OnPresetPicked(self, index):
        presets = pf.LoadPresets()
        if 0 <= index < len(presets) and pf.ApplyPreset(index):
            self.presetEdit.SetText(presets[index]['name'])
            kindWindow = pf._state['kind_window']
            if kindWindow is not None and kindWindow.IsShow():
                kindWindow.OpenKind(kindWindow.kind, True)

    def OnPresetDelete(self):
        name = pf.CleanName(self.presetEdit.GetText())
        presets = pf.LoadPresets()
        for index, preset in enumerate(presets):
            if preset['name'].lower() == name.lower():
                if pf.DeletePreset(index):
                    chat.AppendChat(chat.CHAT_TYPE_INFO, 'Usuni\xeato preset "%s".' % preset['name'])
                return
        chat.AppendChat(chat.CHAT_TYPE_INFO, 'Nie ma presetu o tej nazwie - wybierz go z "Presety".')

    def OnPresetSave(self):
        name = pf.CleanName(self.presetEdit.GetText())
        if not name:
            chat.AppendChat(chat.CHAT_TYPE_INFO, 'Wpisz nazw\xea presetu.')
            return
        kindWindow = pf._state['kind_window']
        if kindWindow is not None and kindWindow.dirty:
            chat.AppendChat(chat.CHAT_TYPE_INFO, 'Okno filtra rodzaju ma niezapisane zmiany - preset ma zapisany stan.')
        if pf.SavePreset(name) < 0:
            chat.AppendChat(chat.CHAT_TYPE_INFO, 'Nie uda\xb3o si\xea zapisa\xe6 presetu (najwy\xbfej %d).' % pf.PRESET_MAX)
            return
        chat.AppendChat(chat.CHAT_TYPE_INFO, 'Zapisano preset "%s".' % name)


class CondCard(ui.Window):
    """A bonus condition, as an entry of the Dom Aukcyjny's bonus window: a
    card with the bonus's name, its item_attr values to click, a field for
    any other value, the slots it is looked for in and a red X."""
    VALUE_W = 36

    def __init__(self, owner, width, height, index):
        ui.Window.__init__(self)
        self.SetSize(width, height)
        self.index = index
        self.board = ui.ThinBoard()
        self.board.SetParent(self)
        self.board.SetPosition(0, 0)
        self.board.SetSize(width, height)
        self.board.AddFlag('not_pick')
        self.board.Show()
        self.nameWidth = width - 10 - 84 - 30 - 72
        self.name = Text(self, 10, 6, '', COLOR_BONUS)
        # MT2009_PLUS_PICKUP_COND_ABSENT_V1: Min. / Brak / >
        self.op = Place(ah.FrameButton(68, 20, '', _Call(ui.__mem_func__(owner.OnCycleOp), index)), self, width - 26 - 80 - 72, 5,
            OP_HINT)
        self.slots = Place(ah.FrameButton(76, 20, '', _Call(ui.__mem_func__(owner.OnCycleSlots), index)), self, width - 26 - 80, 5,
            'Gdzie szuka\xe6: dowolny slot, bonusy 1-5 albo 6/7')
        self.remove = Place(ah.IconButton(ah.REMOVE_IMAGE, ah.REMOVE_HOVER_IMAGE, 'Usu\xf1', 18,
            ui.__mem_func__(owner.OnRemoveCond), index), self, width - 22, 6)
        self.values = []
        for slot in xrange(5):
            button = Place(ah.OptionButton(self.VALUE_W - 2, 20, '', ui.__mem_func__(owner.OnPickValue), index, slot), self,
                10 + slot * self.VALUE_W, height - 26)
            self.values.append(button)
        self.editSlot, self.edit = Edit(self, 10 + 5 * self.VALUE_W + 4, height - 27, 56, 5, True, 'min.', 22)

    def __del__(self):
        ui.Window.__del__(self)

    def SetCond(self, kind, value, slots, op=0):
        ah.FitText(self.name, BonusLabel(kind), self.nameWidth)
        self.slots.SetText(SLOT_TEXTS[slots])
        self.op.SetText(OP_TEXTS[op if 0 <= op < len(OP_TEXTS) else 0])
        values = BonusValues(kind)
        x = 10
        for index, button in enumerate(self.values):
            if index < len(values):
                button.SetText('%d' % values[index])
                button.SetSelected(values[index] == value)
                button.SetPosition(x, self.GetHeight() - 26)
                ah.SetHint(button, ('Brak bonusu albo powy\xbfej %d' if op == pf.COND_ABSENT_OR_ABOVE else 'Co najmniej %d') % values[index])
                button.Show()
                x += self.VALUE_W
            else:
                button.Hide()
        self.editSlot.SetPosition(x + 4, self.GetHeight() - 27)
        self.edit.SetText(str(value))


# ---- the detailed filter of a kind (right click) -------------------------------------
class KindFilterWindow(Panelled):
    WIDTH = 840
    PAD = 14
    SIDE_W = 210
    ROW_H = 26
    EX = PAD + SIDE_W + 10
    EW = WIDTH - EX - PAD
    BODY_Y = 76
    ITEMS_Y = BODY_Y + 48
    ITEM_COLS = 4
    ITEM_H = 40
    LIMITS_Y = ITEMS_Y + 30 + 3 * (ITEM_H + 4) + 8
    BONUS_Y = LIMITS_Y + 48
    COND_COLS = 2
    COND_H = 54
    OTHER_ROW = 30  # MT2009_PLUS_PICKUP_OTHER_BONUSES_V1: the "Albo inne bonusy" row
    FOOT_Y = BONUS_Y + 76 + OTHER_ROW + 3 * (COND_H + 6) + 4
    HEIGHT = FOOT_Y + 50

    def __init__(self):
        Panelled.__init__(self)
        self.kind = 0
        self.rules = []			# every rule (the working copy)
        self.view = []			# indices of this kind's rules in self.rules
        self.sel = -1			# position in self.view
        self.dirty = False
        self.editor = []
        self.bonusWidgets = []
        self.refineWidgets = []
        self.itemPicker = None
        self.bonusPicker = None
        self.pickFor = -1
        self.AddFlag('movable')
        self.AddFlag('float')
        self.SetSize(self.WIDTH, self.HEIGHT)
        self.SetTitleName('Filtr rodzaju')
        self.SetCloseEvent(ui.__mem_func__(self.Close))
        self.Build()
        self.SetCenterPosition()
        self.Hide()

    def Ed(self, widget, group=None):
        self.editor.append(widget)
        if group is not None:
            group.append(widget)
        return widget

    def Build(self):
        W, P, EX, EW = self.WIDTH, self.PAD, self.EX, self.EW
        # toolbar: the kind taken or not
        self.takeButton = self.Big(P, 36, self.SIDE_W, 30, '', ui.__mem_func__(self.OnToggleTake),
            hint='Czy ten rodzaj jest w og\xf3le podnoszony (to samo co LPM w oknie filtra)')
        self.kindHint = self.Label(EX, 43, '', COLOR_DIM)

        # the rule list: a card like the Dom Aukcyjny's categories
        y = self.BODY_Y
        self.Card(P, y, self.SIDE_W, self.FOOT_Y - y - 8)
        self.Label(P + 8, y + 6, 'Regu\xb3y')
        self.Label(P + 70, y + 7, '(max %d)' % pf.KIND_RULE_MAX, COLOR_DIM, False)
        self.ruleRows = []
        rowW = self.SIDE_W - 12 - 24
        for index in xrange(pf.KIND_RULE_MAX):
            ry = y + 30 + index * self.ROW_H
            row = self.K(Place(ah.ImageListButton(rowW, self.ROW_H - 2, ROW_IMAGE,
                ui.__mem_func__(self.OnSelectRule), index), self, P + 6, ry))
            check = self.K(Place(ah.CheckBox(ui.__mem_func__(self.OnToggleRuleOn), index), self,
                P + 6 + rowW + 6, ry + (self.ROW_H - 2 - ah.CHECK_SIZE) // 2, 'Regu\xb3a w\xb3\xb9czona / wy\xb3\xb9czona'))
            self.ruleRows.append((row, check))
        by = y + 30 + pf.KIND_RULE_MAX * self.ROW_H + 6
        third = (self.SIDE_W - 12 - 8) // 3
        self.Frame(P + 6, by, third, 24, 'Dodaj', ui.__mem_func__(self.OnAddRule), True, 'Nowa regu\xb3a tego rodzaju')
        self.Frame(P + 6 + third + 4, by, third, 24, 'Kopiuj', ui.__mem_func__(self.OnCopyRule), False, 'Kopia wybranej regu\xb3y')
        self.Frame(P + 6 + 2 * (third + 4), by, third, 24, 'Usu\xf1', ui.__mem_func__(self.OnDeleteRule), False, 'Usu\xf1 wybran\xb9 regu\xb3\xea')
        half = (self.SIDE_W - 12 - 4) // 2
        self.Frame(P + 6, by + 28, half, 24, 'W g\xf3r\xea', ui.__mem_func__(self.OnMoveRule), False, None, -1)
        self.Frame(P + 6 + half + 4, by + 28, half, 24, 'W d\xf3\xb3', ui.__mem_func__(self.OnMoveRule), False, None, 1)
        self.Label(P + 8, by + 62, 'Podnosz\xea, gdy pasuje', COLOR_DIM, False)
        self.Label(P + 8, by + 76, 'DOWOLNA zaznaczona regu\xb3a.', COLOR_DIM, False)

        # the rule: its name
        self.Card(EX, y, EW, 40)
        self.editorHint = self.Label(EX + 12, y + 11, '', COLOR_DIM)
        self.Ed(self.Label(EX + 10, y + 11, 'Nazwa'))
        slot, self.nameEdit = Edit(self, EX + 70, y + 8, 260, pf.NAME_MAX, False, 'Nazwa regu\xb3y', 24)
        self.Ed(self.K(slot))

        # items: offer-like cards
        iy = self.ITEMS_Y
        self.Card(EX, iy, EW, 30 + 3 * (self.ITEM_H + 4) + 2)
        self.Ed(self.Label(EX + 10, iy + 7, 'Przedmioty'))
        self.Ed(self.Label(EX + 100, iy + 8, 'puste = dowolny przedmiot', COLOR_DIM, False))
        self.addItemButton = self.Ed(self.Frame(EX + EW - 160 - 8, iy + 4, 160, 22, '+ Dodaj przedmiot',
            ui.__mem_func__(self.OnAddItem), True, 'Szukaj przedmiotu po nazwie'))
        cw = (EW - 16 - (self.ITEM_COLS - 1) * 6) // self.ITEM_COLS
        self.itemCards = []
        for index in xrange(ITEM_SHOWN):
            card = self.K(Place(ItemCard(cw, self.ITEM_H, ui.__mem_func__(self.OnRemoveItem), index), self,
                EX + 8 + (index % self.ITEM_COLS) * (cw + 6), iy + 30 + (index // self.ITEM_COLS) * (self.ITEM_H + 4)))
            self.itemCards.append(card)
        self.itemsEmpty = self.Ed(self.Label(EX + 14, iy + 40, 'Dowolny przedmiot tego rodzaju.', COLOR_DIM))

        # refine and level
        ly = self.LIMITS_Y
        self.Card(EX, ly, EW, 40)
        self.Ed(self.Label(EX + 10, ly + 11, 'Ulepszenie  od +'), self.refineWidgets)
        slot, self.refineMinEdit = Edit(self, EX + 118, ly + 8, 40, 2, True, '', 24)
        self.Ed(self.K(slot), self.refineWidgets)
        self.Ed(self.Label(EX + 166, ly + 11, 'do +'), self.refineWidgets)
        slot, self.refineMaxEdit = Edit(self, EX + 200, ly + 8, 40, 2, True, '', 24)
        self.Ed(self.K(slot), self.refineWidgets)
        self.Ed(self.Label(EX + 270, ly + 11, 'Poziom  od'))
        slot, self.levelMinEdit = Edit(self, EX + 350, ly + 8, 48, 3, True, '', 24)
        self.Ed(self.K(slot))
        self.Ed(self.Label(EX + 406, ly + 11, 'do'))
        slot, self.levelMaxEdit = Edit(self, EX + 430, ly + 8, 48, 3, True, '', 24)
        self.Ed(self.K(slot))
        self.Ed(self.Label(EX + 486, ly + 12, '0 = bez granicy', COLOR_DIM, False))

        # bonuses
        sy = self.BONUS_Y
        self.Card(EX, sy, EW, self.FOOT_Y - sy - 8)
        self.noBonusText = self.Label(EX + 12, sy + 12, '', COLOR_DIM)
        B = self.bonusWidgets
        self.Ed(self.Label(EX + 10, sy + 10, 'Bonus\xf3w 1-5'), B)
        self.normalButtons = []
        for number in xrange(6):
            self.normalButtons.append(self.Ed(self.Option(EX + 110 + number * 30, sy + 8, 28, 22,
                str(number) if number else '-', _Call(ui.__mem_func__(self.OnSetCount), 'min_normal', number),
                CountHint(number, '1-5')), B))
        self.Ed(self.Label(EX + 310, sy + 10, 'Bonus\xf3w 6/7'), B)
        self.rareButtons = []
        for number in xrange(3):
            self.rareButtons.append(self.Ed(self.Option(EX + 410 + number * 30, sy + 8, 28, 22,
                str(number) if number else '-', _Call(ui.__mem_func__(self.OnSetCount), 'min_rare', number),
                CountHint(number, '6/7')), B))
        self.Ed(self.Label(EX + 10, sy + 44, 'Warunki'), B)
        self.modeChecks = []
        mx = EX + 110
        for mode, label, hint in ((pf.MODE_ALL, 'Wszystkie', 'Przedmiot spe\xb3nia wszystkie warunki'),
                (pf.MODE_ANY, 'Dowolny', 'Wystarczy jeden warunek'),
                (pf.MODE_AT_LEAST, 'Co najmniej', 'Co najmniej K warunk\xf3w')):
            check = self.Ed(self.K(Place(ah.LabeledSelect(label, 20, ui.__mem_func__(self.OnSetMode), mode),
                self, mx, sy + 38, hint)), B)
            self.modeChecks.append(check)
            mx += check.GetWidth() + 10
        self.needButtons = []
        for number in xrange(1, pf.COND_MAX + 1):
            self.needButtons.append(self.Ed(self.Option(mx + (number - 1) * 24, sy + 38, 22, 22, str(number),
                _Call(ui.__mem_func__(self.OnSetCount), 'need', number), 'K = %d' % number), B))
        # MT2009_PLUS_PICKUP_OTHER_BONUSES_V1: or N bonuses of other kinds
        self.Ed(self.Label(EX + 10, sy + 72, 'Albo inne'), B)
        self.otherButtons = []
        for number in xrange(pf.OTHER_MAX + 1):
            self.otherButtons.append(self.Ed(self.Option(EX + 110 + number * 30, sy + 70, 28, 22,
                str(number) if number else '-', _Call(ui.__mem_func__(self.OnSetCount), 'other_min', number),
                OtherHint(number)), B))
        self.Ed(self.Label(EX + 110 + (pf.OTHER_MAX + 1) * 30 + 6, sy + 73,
            'bonus\xf3w 1-5 spoza warunk\xf3w', COLOR_DIM, False), B)
        sy += self.OTHER_ROW
        cw = (EW - 16 - (self.COND_COLS - 1) * 8) // self.COND_COLS
        self.condCards = []
        self.condPos = []
        for index in xrange(pf.COND_MAX):
            pos = (EX + 8 + (index % self.COND_COLS) * (cw + 8), sy + 72 + (index // self.COND_COLS) * (self.COND_H + 6))
            card = self.K(Place(CondCard(self, cw, self.COND_H, index), self, pos[0], pos[1]))
            self.condCards.append(card)
            self.condPos.append(pos)
        self.addCondButton = self.Frame(EX + 8, sy + 72, 160, 24, '+ Dodaj bonus', ui.__mem_func__(self.OnAddCond), True,
            'Warunek: bonus o co najmniej podanej warto\x9cci')
        self.condHint = self.Label(EX + 178, sy + 76, '', COLOR_DIM, False)

        # footer
        fy = self.FOOT_Y
        self.statusText = self.Label(P, fy + 2, '', COLOR_DIM)
        self.dirtyText = self.Label(P, fy + 20, '')
        self.Frame(W - P - 150, fy + 6, 150, 28, 'Zapisz i wy\x9clij', ui.__mem_func__(self.OnApply), True,
            'Zapisz regu\xb3y i wy\x9clij je na serwer')
        self.Frame(W - P - 150 - 8 - 130, fy + 6, 130, 28, 'Cofnij zmiany', ui.__mem_func__(self.OnRevert), False,
            'Wr\xf3\xe6 do zapisanych regu\xb3')
        self.Frame(W - P - 150 - 8 - 130 - 8 - 160, fy + 6, 160, 28, 'Sprawd\x9f ekwipunek', ui.__mem_func__(self.OnTest), False,
            'Co te regu\xb3y (tak\xbfe niezapisane) zrobi\xb3yby z ekwipunkiem')

    # -- opening and closing
    def OpenKind(self, kind, reload=False):
        if self.IsShow() and kind != self.kind:
            self.PullEdits()
            if self.dirty:
                chat.AppendChat(chat.CHAT_TYPE_INFO, 'Niezapisane zmiany rodzaju "%s" porzucone.' % pf.KindLabel(self.kind))
        if reload or kind != self.kind or not self.dirty:
            self.kind = kind
            self.LoadFromFilter()
        self.SetTitleName('Filtr podnoszenia: %s' % pf.KindLabel(kind))
        self.RefreshAll()
        self.Show()
        self.SetTop()

    def LoadFromFilter(self, keepSel=False):
        sel = self.sel
        self.rules = pf.GetRules()
        self.MakeView()
        self.sel = sel if keepSel and 0 <= sel < len(self.view) else (0 if self.view else -1)
        self.dirty = False

    def MakeView(self):
        self.view = [index for index, rule in enumerate(self.rules) if rule['kinds'] & self.kind]

    def Close(self):
        self.PullEdits()
        self.KillEditFocus()
        for picker in (self.itemPicker, self.bonusPicker):
            if picker is not None:
                picker.Close()
        ah.HideHint()
        self.Hide()

    def Edits(self):
        edits = [self.nameEdit, self.refineMinEdit, self.refineMaxEdit, self.levelMinEdit, self.levelMaxEdit]
        return edits + [card.edit for card in self.condCards]

    def KillEditFocus(self):
        for edit in self.Edits():
            try:
                edit.KillFocus()
            except Exception:
                pass

    def OnPressEscapeKey(self):
        self.Close()
        return True

    def Destroy(self):
        self.Hide()
        for picker in (self.itemPicker, self.bonusPicker):
            if picker is not None:
                picker.Destroy()
        self.itemPicker = None
        self.bonusPicker = None
        self.DestroyControls()
        self.editor = []
        self.bonusWidgets = []
        self.refineWidgets = []
        self.ruleRows = []
        self.condCards = []
        self.itemCards = []
        self.normalButtons = []
        self.rareButtons = []
        self.needButtons = []
        self.otherButtons = []
        self.modeChecks = []

    def Refresh(self):
        """uipickupfilter.RefreshWindows: the stored state changed."""
        self.RefreshKind()
        self.RefreshStatus()

    # -- the working copy
    def Rule(self):
        if 0 <= self.sel < len(self.view):
            return self.rules[self.view[self.sel]]
        return None

    def HasBonuses(self):
        return bool(self.kind & pf.BONUS_KINDS)

    def HasRefine(self):
        return bool(self.kind & pf.REFINE_KINDS)

    def Touch(self):
        self.dirty = True
        self.RefreshAll()

    def ReadEdits(self, rule):
        """The edit lines as the rule's fields, without changing the rule."""
        fields = {'name': pf.CleanName(self.nameEdit.GetText(), rule['name'])}
        fields['refine_min'] = EditNumber(self.refineMinEdit, 0, pf.REFINE_MAX, 0)
        fields['refine_max'] = EditNumber(self.refineMaxEdit, 0, pf.REFINE_MAX, pf.REFINE_MAX)
        if fields['refine_max'] < fields['refine_min']:
            fields['refine_min'], fields['refine_max'] = fields['refine_max'], fields['refine_min']
        fields['level_min'] = EditNumber(self.levelMinEdit, 0, pf.LEVEL_MAX, 0)
        fields['level_max'] = EditNumber(self.levelMaxEdit, 0, pf.LEVEL_MAX, 0)
        if fields['level_max'] and fields['level_max'] < fields['level_min']:
            fields['level_min'], fields['level_max'] = fields['level_max'], fields['level_min']
        conds = []
        for index, cond in enumerate(rule['conds']):
            kind, value, slots, op = CondFields(cond)
            conds.append((kind, EditNumber(self.condCards[index].edit, 0, 32767, value), slots, op))
        fields['conds'] = conds
        return fields

    def PullEdits(self):
        rule = self.Rule()
        if rule is None:
            return
        for key, value in self.ReadEdits(rule).items():
            if rule[key] != value:
                rule[key] = value
                self.dirty = True

    def OnUpdate(self):
        # typing into a field marks the copy changed (the status line)
        rule = self.Rule()
        if rule is None or self.dirty or not self.IsShow():
            return
        texts = [(self.nameEdit, rule['name']), (self.refineMinEdit, str(rule['refine_min'])),
            (self.refineMaxEdit, str(rule['refine_max'])), (self.levelMinEdit, str(rule['level_min'])),
            (self.levelMaxEdit, str(rule['level_max']))]
        texts += [(self.condCards[i].edit, str(cond[1])) for i, cond in enumerate(rule['conds'])]
        for edit, text in texts:
            if edit.GetText() != text:
                self.dirty = True
                self.RefreshStatus()
                return

    # -- refreshing
    def RefreshAll(self):
        self.RefreshKind()
        self.RefreshList()
        self.RefreshEditor()
        self.RefreshStatus()

    def RefreshKind(self):
        if pf.HasKind(self.kind):
            self.takeButton.SetText('Podnosz\xea: Tak')
            self.takeButton.text.SetPackedFontColor(COLOR_GOOD)
            self.kindHint.SetText('Bez regu\xb3 podnosz\xea ka\xbfdy przedmiot tego rodzaju.' if not self.view
                else 'Podnosz\xea tylko to, co pasuje do regu\xb3.')
        else:
            self.takeButton.SetText('Podnosz\xea: Nie')
            self.takeButton.text.SetPackedFontColor(COLOR_BAD)
            self.kindHint.SetText('Rodzaj zostaje na ziemi - regu\xb3y nie dzia\xb3aj\xb9.')

    def RefreshList(self):
        for index, (row, check) in enumerate(self.ruleRows):
            if index < len(self.view):
                rule = self.rules[self.view[index]]
                row.SetLabel(Short(rule['name'], 18))
                row.SetSelected(index == self.sel)
                check.SetChecked(rule['on'])
                row.Show()
                check.Show()
            else:
                row.Hide()
                check.Hide()

    def ShowGroup(self, widgets, show):
        for widget in widgets:
            if show:
                widget.Show()
            else:
                widget.Hide()

    def RefreshEditor(self):
        rule = self.Rule()
        self.ShowGroup(self.editor, rule is not None)
        if rule is None:
            self.editorHint.SetText('Brak regu\xb3 - "Dodaj" tworzy pierwsz\xb9.')
            self.editorHint.Show()
            self.noBonusText.Hide()
            self.addCondButton.Hide()
            self.condHint.SetText('')
            self.ShowGroup(self.itemCards, False)
            self.ShowGroup(self.condCards, False)
            return
        self.editorHint.Hide()
        self.nameEdit.SetText(rule['name'])
        # items
        for index, card in enumerate(self.itemCards):
            if index < len(rule['items']):
                card.SetItem(rule['items'][index])
                card.Show()
            else:
                card.Hide()
        if rule['items']:
            self.itemsEmpty.Hide()
        if len(rule['items']) >= ITEM_SHOWN:
            self.addItemButton.Hide()
        # refine and level
        self.refineMinEdit.SetText(str(rule['refine_min']))
        self.refineMaxEdit.SetText(str(rule['refine_max']))
        self.levelMinEdit.SetText(str(rule['level_min']))
        self.levelMaxEdit.SetText(str(rule['level_max']))
        if not self.HasRefine():
            self.ShowGroup(self.refineWidgets, False)
        # bonuses
        if not self.HasBonuses():
            self.ShowGroup(self.bonusWidgets, False)
            self.ShowGroup(self.condCards, False)
            self.noBonusText.SetText('Ten rodzaj nie ma bonus\xf3w - licz\xb9 si\xea przedmioty, ulepszenie i poziom.')
            self.noBonusText.Show()
            self.addCondButton.Hide()
            self.condHint.SetText('')
            return
        self.noBonusText.Hide()
        for number, button in enumerate(self.normalButtons):
            button.SetSelected(number == rule['min_normal'])
        for number, button in enumerate(self.rareButtons):
            button.SetSelected(number == rule['min_rare'])
        for number, button in enumerate(self.otherButtons):
            button.SetSelected(number == rule.get('other_min', 0))
        for mode, check in enumerate(self.modeChecks):
            check.SetChecked(mode == rule['mode'])
        conds = rule['conds']
        need = max(1, min(rule['need'], len(conds) or 1))
        for number, button in enumerate(self.needButtons):
            if rule['mode'] == pf.MODE_AT_LEAST and number < max(1, len(conds)):
                button.SetSelected(number + 1 == need)
                button.Show()
            else:
                button.Hide()
        for index, card in enumerate(self.condCards):
            if index < len(conds):
                card.SetCond(*CondFields(conds[index]))
                card.Show()
            else:
                card.Hide()
        count = len(conds)
        if count < pf.COND_MAX:
            cardX, cardY = self.condPos[count]
            self.addCondButton.SetPosition(cardX, cardY + (self.COND_H - 24) // 2)
            self.addCondButton.Show()
            self.condHint.SetPosition(cardX, cardY + (self.COND_H - 24) // 2 + 30)
            self.condHint.SetText('' if count else 'Bez warunk\xf3w liczy si\xea tylko liczba bonus\xf3w.')
        else:
            self.addCondButton.Hide()
            self.condHint.SetText('')

    def RefreshStatus(self):
        state = pf.RulesAckText()
        if not pf.IsActive():
            state = 'Filtr podnoszenia jest WY\xa3\xa5CZONY (Ctrl+Z) - teraz podnosisz wszystko.'
        self.statusText.SetText(state)
        if self.dirty:
            self.dirtyText.SetText('Niezapisane zmiany - "Zapisz i wy\x9clij".')
            self.dirtyText.SetPackedFontColor(COLOR_GOLD)
        else:
            self.dirtyText.SetText('Wszystko zapisane.')
            self.dirtyText.SetPackedFontColor(COLOR_DIM)

    # -- the kind
    def OnToggleTake(self):
        pf.ToggleKind(self.kind)
        self.RefreshKind()

    # -- the rule list
    def OnSelectRule(self, index):
        self.PullEdits()
        if index < len(self.view):
            self.sel = index
        self.RefreshAll()

    def OnToggleRuleOn(self, index):
        self.PullEdits()
        if index < len(self.view):
            rule = self.rules[self.view[index]]
            rule['on'] = 0 if rule['on'] else 1
            self.Touch()

    def OnAddRule(self):
        self.PullEdits()
        if len(self.view) >= pf.KIND_RULE_MAX or len(self.rules) >= pf.RULE_MAX:
            chat.AppendChat(chat.CHAT_TYPE_INFO, 'Najwy\xbfej %d regu\xb3 na rodzaj (%d razem).' % (pf.KIND_RULE_MAX, pf.RULE_MAX))
            return
        self.rules.append(pf.NewRule(self.kind, 'Regu\xb3a %d' % (len(self.view) + 1)))
        self.MakeView()
        self.sel = len(self.view) - 1
        self.Touch()

    def OnCopyRule(self):
        self.PullEdits()
        rule = self.Rule()
        if rule is None or len(self.view) >= pf.KIND_RULE_MAX or len(self.rules) >= pf.RULE_MAX:
            return
        copy = pf.CopyRule(rule)
        copy['name'] = pf.CleanName(rule['name'][:pf.NAME_MAX - 4] + ' (2)', 'Regu\xb3a')
        self.rules.insert(self.view[self.sel] + 1, copy)
        self.MakeView()
        self.sel += 1
        self.Touch()

    def OnDeleteRule(self):
        if self.Rule() is None:
            return
        del self.rules[self.view[self.sel]]
        self.MakeView()
        self.sel = min(self.sel, len(self.view) - 1)
        self.Touch()

    def OnMoveRule(self, step):
        self.PullEdits()
        to = self.sel + step
        if self.Rule() is None or not 0 <= to < len(self.view):
            return
        a, b = self.view[self.sel], self.view[to]
        self.rules[a], self.rules[b] = self.rules[b], self.rules[a]
        self.sel = to
        self.Touch()

    # -- counts and the mode
    def OnSetCount(self, field, number):
        self.PullEdits()
        rule = self.Rule()
        if rule is not None and rule.get(field) != number:
            rule[field] = number
            self.Touch()

    def OnSetMode(self, mode):
        self.PullEdits()
        rule = self.Rule()
        if rule is not None and rule['mode'] != mode:
            rule['mode'] = mode
            self.Touch()

    # -- items
    def OnAddItem(self):
        self.PullEdits()
        rule = self.Rule()
        if rule is None or len(rule['items']) >= ITEM_SHOWN:
            return
        if self.itemPicker is None:
            self.itemPicker = ItemPicker()
        x, y = self.GetGlobalPosition()
        self.itemPicker.Open(ui.__mem_func__(self.OnItemPicked), x + self.WIDTH + 4, y, self.kind)

    def OnItemPicked(self, vnum):
        rule = self.Rule()
        if rule is None or vnum in rule['items'] or len(rule['items']) >= ITEM_SHOWN:
            return
        rule['items'].append(vnum)
        self.Touch()

    def OnRemoveItem(self, index):
        self.PullEdits()
        rule = self.Rule()
        if rule is not None and index < len(rule['items']):
            del rule['items'][index]
            self.Touch()

    # -- bonus conditions
    def OnAddCond(self):
        self.PullEdits()
        rule = self.Rule()
        if rule is None or len(rule['conds']) >= pf.COND_MAX:
            return
        if self.bonusPicker is None:
            self.bonusPicker = BonusPicker()
        self.pickFor = len(rule['conds'])
        x, y = self.GetGlobalPosition()
        self.bonusPicker.Open(ui.__mem_func__(self.OnBonusPicked), x + self.WIDTH + 4, y)

    def OnBonusPicked(self, kind):
        rule = self.Rule()
        if rule is None or len(rule['conds']) >= pf.COND_MAX:
            return
        values = BonusValues(kind)
        # a first value: the middle roll of item_attr, as a start to change
        rule['conds'].append((kind, values[len(values) // 2] if values else 1, pf.SLOTS_ANY, pf.COND_AT_LEAST))
        self.Touch()

    def OnPickValue(self, index, slot):
        self.PullEdits()
        rule = self.Rule()
        if rule is None or index >= len(rule['conds']):
            return
        kind, value, slots, op = CondFields(rule['conds'][index])
        values = BonusValues(kind)
        if slot < len(values):
            rule['conds'][index] = (kind, values[slot], slots, op)
            self.Touch()

    def OnCycleSlots(self, index):
        self.PullEdits()
        rule = self.Rule()
        if rule is not None and index < len(rule['conds']):
            kind, value, slots, op = CondFields(rule['conds'][index])
            rule['conds'][index] = (kind, value, (slots + 1) % len(SLOT_TEXTS), op)
            self.Touch()

    def OnCycleOp(self, index):
        """MT2009_PLUS_PICKUP_COND_ABSENT_V1: Min. <-> Brak / >."""
        self.PullEdits()
        rule = self.Rule()
        if rule is not None and index < len(rule['conds']):
            kind, value, slots, op = CondFields(rule['conds'][index])
            rule['conds'][index] = (kind, value, slots, (op + 1) % len(OP_TEXTS))
            self.Touch()

    def OnRemoveCond(self, index):
        self.PullEdits()
        rule = self.Rule()
        if rule is not None and index < len(rule['conds']):
            del rule['conds'][index]
            rule['need'] = max(1, min(rule['need'], len(rule['conds']) or 1))
            self.Touch()

    # -- saving
    def OnApply(self):
        self.PullEdits()
        self.KillEditFocus()
        pf.SetRules(self.rules)
        self.LoadFromFilter(True)
        self.RefreshAll()
        chat.AppendChat(chat.CHAT_TYPE_INFO, 'Filtr podnoszenia: zapisano regu\xb3y rodzaju "%s" (%d).' % (
            pf.KindLabel(self.kind), len(self.view)))

    def OnRevert(self):
        self.KillEditFocus()
        self.LoadFromFilter(True)
        self.RefreshAll()

    def OnTest(self):
        self.PullEdits()
        TestInventory(self.rules, pf.GetKinds(), self.kind)
