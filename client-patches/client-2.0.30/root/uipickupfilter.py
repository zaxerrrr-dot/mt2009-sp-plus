# Filtr podnoszenia - what the Z key and a loot pet pick up (the operator,
# 28 September: "okno dla autopeta i do recznego dzialania ... mozliwosc
# filtrowania zbieranego dropu, jak w auto lowach").
#
# One filter for everything (the operator, 30 September: "filtr dzialal na
# wszystko: czyli na nas, na autolowy i na towarzysza jednoczesnie. Tak aby
# mozna bylo ustawic tylko filtr pod ctrl + z lub tylko w autolowach"): this
# module owns it - a switch and the thirteen kinds of the auto-hunt's
# pick-up (uiautohunt.LOOT_KINDS, the server's AutoHuntLootKind bits). Two
# windows show and edit the same settings: this one (Ctrl+Z, "/filtr", the
# inventory's button) and the "Podnoszenie" board of Auto Lowy's settings
# window (uiautohunt.AutoHuntLootWindow). Every change is saved at once,
# sent to the server and shown in both.
#
# With the filter on it holds for:
#  - the Z and ` keys and a loot pet - the server picks up
#    (CHARACTER::PickupNearbyItems, server-patches/playerqol);
#  - Auto Lowy - uiautohunt.LootMask asks the server for these kinds only,
#    and the server checks the same filter (FAutoHuntLoot, "(auto hunt)");
#    Auto Lowy's own "Podnies" still says whether the hunt picks up at all;
#  - the companion (Towarzysz) - its own drops and the owner's drops it
#    lifts (playerbot_loot.h / playerbot_sidekick.h, the owner's filter).
# Off, everything is picked up as before the filter. Yang is always taken.
#
# "/pickup_filter <on> <kinds>" is sent after every login and warp
# (PickupFilterSync, an updatable of game.py) and every change.
# MT2009_PLUS_PICKUP_FILTER_PER_CHAR_V1 (the owner, 3 October): the settings
# are each character's own - autohunt/postacie/filtr_<nick>.cfg. A character
# with no file of its own starts from the old client-wide autohunt/filtr.cfg
# (left in place for the other characters), or, with none either, from the
# kinds its Auto Lowy file left out (AdoptAutoHuntKinds).
#
# MT2009_PLUS_PICKUP_BONUS_FILTER_V1 (the owner, 3 October: "podnos tylko z
# bonusem dla kategorii eq"): an equipment kind (BONUS_KINDS) has a third
# choice, "Bonus" - its items are picked up only with at least bonus_min of
# their five bonuses (1 by default, "Min. bonusow" in both windows). A click
# goes Tak -> Bonus -> Nie -> Tak; the other kinds stay Tak / Nie. The
# server decides, it knows the bonuses of an item on the ground: the command
# is "/pickup_filter <on> <kinds> <bonus kinds> <min bonuses>" (playerqol,
# Mt2009PlusPickupFilterAllows) - a server before it reads the first two and
# picks such items up whatever their bonuses. filtr.cfg keeps bonus= and
# bonus_min=, which an older client skips.
#
# MT2009_PLUS_PICKUP_RULES_V1 (Autor: Vekirion; the owner, 13 October): the Ctrl+Z window is
# replaced (uipickupfilterrules.PickupFilterWindow). A LEFT click on a kind
# takes it or not (Tak / Nie); a RIGHT click opens the kind's detailed filter
# (uipickupfilterrules.KindFilterWindow): up to KIND_RULE_MAX rules, each with
#  - chosen items (empty = any item of the kind) - a refinable item (weapon,
#    armour, belt) by its line, the +0's vnum, so "Zbroja X" is every +N of
#    it; the item search asks the server ("/pickup_items", PickupItemsList);
#  - refine from +N to +M (weapon, armour, belt) and wear level from..to;
#  - for the eight equipment kinds: a minimum count of normal (1-5) and rare
#    (6-7) bonuses and up to COND_MAX conditions "bonus X at least V" (slots
#    1-5, 6-7 or any), needed all / any one / at least K.
# A kind the filter takes is decided by its switched-on rules when it has
# any - ANY rule matching takes the item - and taken whole when it has none.
# The "Bonus" state of MT2009_PLUS_PICKUP_BONUS_FILTER_V1 is gone: a file
# that still has bonus kinds becomes one "Min. N bonusow" rule for each.
# The rules are each character's own (autohunt/postacie/filtr_reguly_<nick>.cfg)
# and go to the server after the filter: "/pickup_rules begin", one
# "/pickup_rules add ..." each (char_item.cpp), "/pickup_rules end" - the
# server swaps the set in whole. The engine takes 10 commands a half second
# and 256 characters a command, so everything goes through a queue
# (SEND_BATCH commands every SEND_GAP seconds, flushed by PickupFilterSync;
# MT2009_PLUS_PICKUP_SYNC_FAST_V1: the server no longer limits them).
# The detailed filter is an option of "Opcje Gry" -> "Dodatkowe" -> "Filtr
# podnoszenia" (uiopcjedodatkowe.py, pickup_advanced, on by default). Off, the
# filter is the simple one: no rules go to the server ("/pickup_rules clear"),
# a right click does not open a kind's window, and the rules stay saved.
# Presets: named snapshots of the whole filter (switch, kinds and rules),
# shared by every character of this client (autohunt/filtr_presety.cfg).
#
# Python 2.7 as the client has it; the texts are CP1250 escapes.

import app
import chat
import clientclock  # MT2009_PLUS_PICKUP_SYNC_CLOCK_V1
import net
import os
import player
import ui

import uiautohunt

# The client-wide file of the clients before MT2009_PLUS_PICKUP_FILTER_PER_CHAR_V1.
CONFIG_PATH = os.path.join(uiautohunt.CONFIG_BASE_DIR, 'filtr.cfg')


def CharacterName():
    try:
        return player.GetMainCharacterName() or ''
    except Exception:
        return ''


def CharConfigPath(name):
    safe = ''.join(c if c.isalnum() else '_' for c in (name or 'postac'))
    return os.path.join(uiautohunt.CONFIG_CHAR_DIR, 'filtr_%s.cfg' % safe)
ALL_KINDS = 0
for _key, _label, _bit in uiautohunt.LOOT_KINDS:
    ALL_KINDS |= _bit

# The equipment kinds - the ones with bonuses (the server's
# MT2009_PLUS_PICKUP_BONUS_KINDS).
BONUS_KEYS = ('loot_weapon', 'loot_armour', 'loot_helmet', 'loot_shield',
    'loot_bracelet', 'loot_shoes', 'loot_necklace', 'loot_earrings')
BONUS_KINDS = 0
for _key, _label, _bit in uiautohunt.LOOT_KINDS:
    if _key in BONUS_KEYS:
        BONUS_KINDS |= _bit
# MT2009_PLUS_PICKUP_RULES_V1: the kinds with refine (+N) - equipment and
# trinkets (belts).
REFINE_KINDS = BONUS_KINDS | (1 << 2)
BONUS_MIN_MAX = 5

# MT2009_PLUS_PICKUP_RULES_V1: limits - the same as the server's.
RULE_MAX = 40
KIND_RULE_MAX = 10
COND_MAX = 6
ITEM_MAX = 16
REFINE_MAX = 15
LEVEL_MAX = 250
PRESET_MAX = 20
NAME_MAX = 20
MODE_ALL = 0
MODE_ANY = 1
MODE_AT_LEAST = 2
SLOTS_ANY = 0
SLOTS_NORMAL = 1
SLOTS_RARE = 2
# MT2009_PLUS_PICKUP_COND_ABSENT_V1 (the owner, 14 October): a condition is
# "bonus X of at least V" (COND_AT_LEAST, as before) or "no bonus X, or it
# above V" (COND_ABSENT_OR_ABOVE) - the item is picked up when it does not
# have the bonus at all, and with it only when its value is greater than V.
# Saved and sent as a 4th field "type:value:slots:1" (none for the first).
COND_AT_LEAST = 0
COND_ABSENT_OR_ABOVE = 1
# MT2009_PLUS_PICKUP_OTHER_BONUSES_V1 (the owner, 15 October): a rule also takes an
# item with at least N bonuses (slots 1-5) of kinds none of its conditions names,
# whatever its conditions say ("o:N" in the saved line, "o<N>" to the server).
OTHER_MAX = 5


def CondToken(cond):
    kind, value, slots, op = (tuple(cond) + (COND_AT_LEAST,))[:4]
    if op == COND_ABSENT_OR_ABOVE:
        return '%d:%d:%d:%d' % (kind, value, slots, op)
    return '%d:%d:%d' % (kind, value, slots)
# MT2009_PLUS_PICKUP_SYNC_V1 (the owner, 15 October: the companion picked up what
# the filter's test said it would leave; the window stuck on "Wysylanie do
# serwera..."): the server's command limit (cmd.cpp, ENABLE_ANTI_CMD_FLOOD - 10
# commands a half second for everything the client sends) dropped some of the
# filter's commands, often "/pickup_rules end" - the rules never swapped in and
# no "PickupRulesAck" came. Now: slower (3 commands every 0.5 s), and with no
# answer ACK_WAIT seconds after the last command the whole filter goes again,
# up to ACK_RETRIES times. The server lets these commands through its limit and,
# until a kind's rules are there, leaves its items on the ground.
# MT2009_PLUS_PICKUP_SYNC_FAST_V1 (the owner, 16 October: "a channel change with a
# few filters set makes the login much longer"): the server lets these commands
# through its limit (cmd.cpp, s_apszUnthrottled), so the slow pace only made the
# filter wait - 40 rules with item lists took 10+ seconds after every login and
# channel change, and the kinds with rules were left on the ground meanwhile.
# Now 20 commands every 0.05 s (the whole filter in a frame or two), and no
# answer in 1.5 s sends it again.
SEND_GAP = 0.05
SEND_BATCH = 20
ACK_WAIT = 1.5
# MT2009_PLUS_PICKUP_SYNC_V2 (the owner, 16 October: "a long time after the login
# before the rules reach the server - on mine they never do"): a server whose
# command limit still counts these commands (10 a half second for everything the
# client sends - the login's other windows send too) dropped some of a fast send,
# often "/pickup_rules begin": the adds went nowhere and "end" answered 0, which
# was taken as the answer. Now the answer is checked - the number of rules the
# server keeps must be the number sent, and the filter's own command must have
# been answered (PickupFilterAck) - and a wrong or missing answer sends the whole
# filter again, the retries at the slow pace (SLOW_BATCH commands every
# SLOW_GAP seconds) that such a limit lets through.
SLOW_GAP = 0.5
SLOW_BATCH = 4
SLOW_ACK_WAIT = 3.0
ACK_RETRIES = 4
COMMAND_MAX = 250
PRESETS_PATH = os.path.join(uiautohunt.CONFIG_BASE_DIR, 'filtr_presety.cfg')

_state = {'loaded': False, 'file': False, 'on': 0, 'kinds': ALL_KINDS,
    'bonus': 0, 'bonus_min': 1, 'window': None, 'name': None,
    'rules': [], 'rules_ack': None, 'kind_window': None,
    'items_req': 0, 'items_event': None, 'ack_wait': 0.0, 'retries': 0,
    'expected': 0, 'filter_ack': False}  # MT2009_PLUS_PICKUP_SYNC_V2

# Commands waiting for their turn (Send, Flush).
_queue = []
_sendTime = [0.0]


def KindLabel(bit):
    for key, label, kindBit in uiautohunt.LOOT_KINDS:
        if kindBit == bit:
            return label
    return '?'


def KindBits():
    return [bit for key, label, bit in uiautohunt.LOOT_KINDS]


def RulesConfigPath(name):
    if not name:
        return os.path.join(uiautohunt.CONFIG_BASE_DIR, 'filtr_reguly.cfg')
    safe = ''.join(c if c.isalnum() else '_' for c in name)
    return os.path.join(uiautohunt.CONFIG_CHAR_DIR, 'filtr_reguly_%s.cfg' % safe)


def CleanName(text, default=''):
    text = ''.join(c for c in (text or '') if c >= ' ' and c not in '|\r\n[]=')
    text = text.strip()[:NAME_MAX]
    return text or default


def _Int(text, low, high, default=0):
    try:
        value = int(text)
    except (TypeError, ValueError):
        return default
    return max(low, min(high, value))


# ---- rules -------------------------------------------------------------------
def NewRule(kind, name='Regu\xb3a'):
    return {'name': name, 'on': 1, 'kinds': kind, 'items': [],
        'refine_min': 0, 'refine_max': REFINE_MAX, 'level_min': 0, 'level_max': 0,
        'min_normal': 0, 'min_rare': 0, 'mode': MODE_ALL, 'need': 1, 'conds': [], 'other_min': 0}


def CopyRule(rule):
    copy = dict(rule)
    copy['conds'] = [tuple(cond) for cond in rule['conds']]
    copy['items'] = list(rule['items'])
    return copy


def RuleToLine(rule):
    """on|kinds|normal|rare|+min|+max|lvmin|lvmax|mode|need|t:v:s,..|vnum,..|name"""
    return '%d|%d|%d|%d|%d|%d|%d|%d|%d|%d|%s|%s|%s' % (1 if rule['on'] else 0,
        rule['kinds'], rule['min_normal'], rule['min_rare'], rule['refine_min'],
        rule['refine_max'], rule['level_min'], rule['level_max'], rule['mode'],
        rule['need'], ','.join([CondToken(cond) for cond in rule['conds']] + OtherTokens(rule, 'o:%d')),
        ','.join(str(vnum) for vnum in rule['items']), CleanName(rule['name'], 'Regu\xb3a'))


def OtherTokens(rule, form):
    """MT2009_PLUS_PICKUP_OTHER_BONUSES_V1: the rule's "other bonuses" as a token."""
    number = rule.get('other_min', 0)
    return [form % number] if number > 0 else []


def _Other(text):
    for token in text.split(','):
        if token.startswith('o:'):
            return _Int(token[2:], 0, OTHER_MAX)
    return 0


def _Conds(text):
    conds = []
    for token in text.split(','):
        fields = token.split(':')
        if len(fields) not in (3, 4) or len(conds) >= COND_MAX:
            continue
        kind = _Int(fields[0], 0, 255)
        op = _Int(fields[3], COND_AT_LEAST, COND_ABSENT_OR_ABOVE) if len(fields) == 4 else COND_AT_LEAST
        if kind > 0:
            conds.append((kind, _Int(fields[1], 0, 32767), _Int(fields[2], SLOTS_ANY, SLOTS_RARE), op))
    return conds


def RulesFromLine(text, version):
    """A saved line as rules: version 2 is one rule; version 1 (the first
    rules of 13 October, several kinds a rule) one rule for each kind."""
    if version == 1:
        parts = text.split('|', 8)
        if len(parts) < 9:
            return []
        rules = []
        for bit in KindBits():
            if not _Int(parts[1], 0, ALL_KINDS) & bit & BONUS_KINDS:
                continue
            rule = NewRule(bit, CleanName(parts[8], 'Regu\xb3a'))
            rule['on'] = _Int(parts[0], 0, 1, 1)
            rule['min_normal'] = _Int(parts[2], 0, BONUS_MIN_MAX)
            rule['min_rare'] = _Int(parts[3], 0, 2)
            rule['refine_min'] = _Int(parts[4], 0, REFINE_MAX)
            rule['mode'] = _Int(parts[5], MODE_ALL, MODE_AT_LEAST)
            rule['need'] = _Int(parts[6], 1, COND_MAX, 1)
            rule['conds'] = _Conds(parts[7])
            rules.append(rule)
        return rules
    parts = text.split('|', 12)
    if len(parts) < 13:
        return []
    kinds = _Int(parts[1], 0, ALL_KINDS)
    if not kinds:
        return []
    rule = NewRule(kinds, CleanName(parts[12], 'Regu\xb3a'))
    rule['on'] = _Int(parts[0], 0, 1, 1)
    rule['min_normal'] = _Int(parts[2], 0, BONUS_MIN_MAX)
    rule['min_rare'] = _Int(parts[3], 0, 2)
    rule['refine_min'] = _Int(parts[4], 0, REFINE_MAX)
    rule['refine_max'] = _Int(parts[5], 0, REFINE_MAX, REFINE_MAX)
    rule['level_min'] = _Int(parts[6], 0, LEVEL_MAX)
    rule['level_max'] = _Int(parts[7], 0, LEVEL_MAX)
    rule['mode'] = _Int(parts[8], MODE_ALL, MODE_AT_LEAST)
    rule['need'] = _Int(parts[9], 1, COND_MAX, 1)
    rule['conds'] = _Conds(parts[10])
    rule['other_min'] = _Other(parts[10])
    for token in parts[11].split(','):
        vnum = _Int(token, 0, 0x7FFFFFFF)
        if vnum and vnum not in rule['items'] and len(rule['items']) < ITEM_MAX:
            rule['items'].append(vnum)
    return [rule]


def ParseRuleLine(line):
    if line.startswith('rule2='):
        return RulesFromLine(line[6:], 2)
    if line.startswith('rule='):
        return RulesFromLine(line[5:], 1)
    return []


def _LoadRules(name):
    _state['rules'] = []
    try:
        with open(RulesConfigPath(name), 'r') as handle:
            for line in handle:
                for rule in ParseRuleLine(line.rstrip('\r\n')):
                    if len(_state['rules']) < RULE_MAX:
                        _state['rules'].append(rule)
    except (IOError, OSError):
        pass


def _SaveRules(name):
    try:
        with open(RulesConfigPath(name), 'w') as handle:
            for rule in _state['rules']:
                handle.write('rule2=%s\n' % RuleToLine(rule))
    except (IOError, OSError):
        pass


def _MigrateBonus():
    """MT2009_PLUS_PICKUP_BONUS_FILTER_V1's "Bonus" kinds as rules: each one
    a "Min. N bonusow" rule of its own, unless the kind has rules already."""
    bonus = _state['bonus'] & _state['kinds'] & BONUS_KINDS
    if not bonus:
        _state['bonus'] = 0
        return False
    for bit in KindBits():
        if not bonus & bit or RulesForKind(bit):
            continue
        rule = NewRule(bit, 'Min. %d bonus\xf3w' % _state['bonus_min'])
        rule['min_normal'] = _state['bonus_min']
        if len(_state['rules']) < RULE_MAX:
            _state['rules'].append(rule)
    _state['bonus'] = 0
    return True


def RulesForKind(bit, rules=None):
    if rules is None:
        rules = _state['rules']
    return [rule for rule in rules if rule['kinds'] & bit]


def Load():
    # MT2009_PLUS_PICKUP_FILTER_PER_CHAR_V1: read again for another character.
    name = CharacterName()
    if _state['loaded'] and _state['name'] == name:
        return
    _state['loaded'] = True
    _state['name'] = name
    _state['file'] = False
    _state['on'] = 0
    _state['kinds'] = ALL_KINDS
    _state['bonus'] = 0
    _state['bonus_min'] = 1
    path = CharConfigPath(name) if name else CONFIG_PATH
    if name and not os.path.exists(path):
        path = CONFIG_PATH	# the old client-wide settings as a start
    try:
        with open(path, 'r') as handle:
            _state['file'] = path != CONFIG_PATH or not name
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
                elif key == 'bonus':
                    _state['bonus'] = value & BONUS_KINDS
                elif key == 'bonus_min':
                    _state['bonus_min'] = max(1, min(BONUS_MIN_MAX, value))
    except (IOError, OSError):
        pass
    # MT2009_PLUS_PICKUP_RULES_V1: the character's rules; "Bonus" kinds of
    # an older file become rules (saved at the next change).
    _LoadRules(name)
    _MigrateBonus()


def Save():
    Load()
    name = _state['name']
    folder = uiautohunt.CONFIG_CHAR_DIR if name else uiautohunt.CONFIG_BASE_DIR
    if not os.path.exists(folder):
        try:
            os.makedirs(folder)
        except (IOError, OSError):
            pass
    try:
        with open(CharConfigPath(name) if name else CONFIG_PATH, 'w') as handle:
            handle.write('on=%d\nkinds=%d\nbonus=0\nbonus_min=%d\n' % (
                _state['on'], _state['kinds'], _state['bonus_min']))
        _state['file'] = True
    except (IOError, OSError):
        pass
    _SaveRules(name)


# ---- to the server -----------------------------------------------------------
def AdvancedEnabled():
    """The detailed filter switched on in the game options (uiopcjedodatkowe)."""
    try:
        import uiopcjedodatkowe
        return uiopcjedodatkowe.PickupAdvanced()
    except Exception:
        return True


def OnAdvancedChanged():
    """The option changed: the rules to the server or off it, the windows
    redrawn, the kind window closed when the detailed filter went off."""
    if not AdvancedEnabled():
        window = _state['kind_window']
        if window is not None:
            try:
                window.Close()
            except RuntimeError:
                pass
    Send()
    RefreshWindows()


def SendableRules():
    """The switched-on rules of the kinds the filter takes (none with the
    detailed filter off in the game options)."""
    Load()
    if not AdvancedEnabled():
        return []
    return [rule for rule in _state['rules'] if rule['on'] and rule['kinds'] & _state['kinds']]


def RuleCommands(rule):
    """The rule as "/pickup_rules add ..." - and "items ..." for the items
    that do not fit in it."""
    command = '/pickup_rules add %d %d %d %d %d %d %d %d %d' % (rule['kinds'] & ALL_KINDS,
        rule['min_normal'], rule['min_rare'], rule['refine_min'], rule['refine_max'],
        rule['level_min'], rule['level_max'], rule['mode'], rule['need'])
    for cond in rule['conds'][:COND_MAX]:
        command += ' ' + CondToken(cond)
    for token in OtherTokens(rule, ' o%d'):
        command += token
    commands = []
    for vnum in rule['items'][:ITEM_MAX]:
        token = ' v%d' % vnum
        if len(command) + len(token) > COMMAND_MAX:
            commands.append(command)
            command = '/pickup_rules items'
        command += token
    commands.append(command)
    return commands


def Send(retry=False):
    """The whole filter to the server, through the queue: a newer state
    replaces whatever of an older one has not gone yet."""
    Load()
    del _queue[:]
    if not retry:
        _state['retries'] = 0
    rules = SendableRules()[:RULE_MAX]
    # MT2009_PLUS_PICKUP_SYNC_V1: the kinds with rules, as a 5th field - the server
    # leaves their items until the rules are in (an older server ignores it).
    ruleKinds = 0
    for rule in rules:
        ruleKinds |= rule['kinds']
    _state['expected'] = len(rules)  # MT2009_PLUS_PICKUP_SYNC_V2: what "PickupRulesAck" must say
    _state['filter_ack'] = False
    _queue.append('/pickup_filter %d %d 0 %d %d' % (_state['on'], _state['kinds'], _state['bonus_min'],
        ruleKinds & _state['kinds'] & ALL_KINDS))
    if rules:
        _queue.append('/pickup_rules begin')
        for rule in rules:
            _queue.extend(RuleCommands(rule))
        _queue.append('/pickup_rules end')
    else:
        _queue.append('/pickup_rules clear')
    _state['rules_ack'] = None
    _state['ack_wait'] = 0.0
    Flush()


def Flush():
    """SEND_BATCH queued commands every SEND_GAP seconds."""
    if not _queue:
        return
    # MT2009_PLUS_PICKUP_SYNC_CLOCK_V1: app.GetTime() starts again from zero at every
    # connection (a channel change, a teleport) - a deadline taken on the map before
    # held the filter back for as long as the character had played there.
    # clientclock.Now() never runs backwards.
    now = clientclock.Now()
    if now < _sendTime[0]:
        return
    # MT2009_PLUS_PICKUP_SYNC_V2: the first send fast, every retry at the slow pace
    slow = _state['retries'] > 0
    _sendTime[0] = now + (SLOW_GAP if slow else SEND_GAP)
    for i in xrange(min(SLOW_BATCH if slow else SEND_BATCH, len(_queue))):
        net.SendChatPacket(_queue.pop(0))
    if not _queue:
        # MT2009_PLUS_PICKUP_SYNC_V1: all gone - now the answer is awaited
        _state['ack_wait'] = now + (SLOW_ACK_WAIT if slow else ACK_WAIT)
        RefreshWindows()


def WaitingAck():
    """MT2009_PLUS_PICKUP_SYNC_V1: sent, not answered, a retry still possible."""
    return not _queue and _state['rules_ack'] is None and _state['ack_wait'] > 0.0 \
        and _state['retries'] < ACK_RETRIES


def CheckAck():
    """MT2009_PLUS_PICKUP_SYNC_V1: no answer in time - the whole filter again."""
    if not WaitingAck() or clientclock.Now() < _state['ack_wait']:  # MT2009_PLUS_PICKUP_SYNC_CLOCK_V1
        return
    _state['retries'] += 1
    Send(True)
    RefreshWindows()


def HasQueued():
    return len(_queue) > 0


def GetRules():
    Load()
    return [CopyRule(rule) for rule in _state['rules']]


def SetRules(rules):
    Load()
    _state['rules'] = [CopyRule(rule) for rule in rules[:RULE_MAX]]
    Changed()


def RulesAckText():
    ack = _state['rules_ack']
    if HasQueued():
        return 'Wysy\xb3anie do serwera...'
    if ack is None:
        if _state['ack_wait'] > 0.0 and _state['retries'] >= ACK_RETRIES:
            return 'Serwer nie potwierdzi\xb3 regu\xb3 - kliknij "Zapisz i wy\x9clij"'
        if _state['retries']:
            return 'Serwer: brak potwierdzenia, ponawiam (%d/%d)...' % (_state['retries'], ACK_RETRIES)
        return 'Serwer: czekam na potwierdzenie'
    return 'Serwer: aktywnych regu\xb3 %d' % ack


def OnRulesAck(count='0', *rest):
    try:
        count = int(count)
    except ValueError:
        count = 0
    # MT2009_PLUS_PICKUP_SYNC_V2: an answer while the filter is still being sent
    # belongs to an older send; a wrong one (a command of the send was dropped)
    # sends it all again, at the slow pace.
    if _queue:
        return
    if (count != _state['expected'] or not _state['filter_ack']) and _state['retries'] < ACK_RETRIES:
        _state['retries'] += 1
        Send(True)
        RefreshWindows()
        return
    _state['rules_ack'] = count
    _state['retries'] = 0
    RefreshWindows()


# ---- the item search ("/pickup_items", char_item.cpp) -------------------------
def RequestItems(kind, text, event):
    """Asks the server for the items of a kind whose name holds the text;
    event(vnums) gets the answer. Returns False for a too short text."""
    text = ' '.join(text.split())
    if len(text) < 2:
        return False
    _state['items_req'] += 1
    _state['items_event'] = event
    net.SendChatPacket('/pickup_items %d %d %s' % (_state['items_req'], kind, text[:40]))
    return True


def OnItemsList(req='0', vnums='-', *rest):
    try:
        if int(req) != _state['items_req']:
            return
    except ValueError:
        return
    event = _state['items_event']
    _state['items_event'] = None
    found = []
    if vnums != '-':
        for token in vnums.split(','):
            vnum = _Int(token, 0, 0x7FFFFFFF)
            if vnum:
                found.append(vnum)
    if event:
        try:
            event(found)
        except Exception:
            pass


# ---- presets: the whole filter under a name ---------------------------------
def LoadPresets():
    presets = []
    current = None
    try:
        with open(PRESETS_PATH, 'r') as handle:
            for line in handle:
                line = line.rstrip('\r\n')
                if line == '[preset]':
                    current = {'name': 'Preset', 'on': 1, 'kinds': ALL_KINDS, 'rules': []}
                    presets.append(current)
                    continue
                if current is None or '=' not in line:
                    continue
                key, value = line.split('=', 1)
                if key == 'name':
                    current['name'] = CleanName(value, 'Preset')
                elif key == 'on':
                    current['on'] = _Int(value, 0, 1)
                elif key == 'kinds':
                    current['kinds'] = _Int(value, 0, ALL_KINDS, ALL_KINDS)
                else:
                    for rule in ParseRuleLine(line):
                        if len(current['rules']) < RULE_MAX:
                            current['rules'].append(rule)
    except (IOError, OSError):
        pass
    return presets[:PRESET_MAX]


def SavePresets(presets):
    if not os.path.exists(uiautohunt.CONFIG_BASE_DIR):
        try:
            os.makedirs(uiautohunt.CONFIG_BASE_DIR)
        except (IOError, OSError):
            pass
    try:
        with open(PRESETS_PATH, 'w') as handle:
            for preset in presets[:PRESET_MAX]:
                handle.write('[preset]\nname=%s\non=%d\nkinds=%d\n' % (
                    CleanName(preset['name'], 'Preset'), preset['on'], preset['kinds']))
                for rule in preset['rules']:
                    handle.write('rule2=%s\n' % RuleToLine(rule))
        return True
    except (IOError, OSError):
        return False


def SavePreset(name):
    """The current filter as a preset; one of the same name is replaced.
    Returns the preset's index, or -1."""
    Load()
    name = CleanName(name)
    if not name:
        return -1
    presets = LoadPresets()
    preset = {'name': name, 'on': _state['on'], 'kinds': _state['kinds'],
        'rules': [CopyRule(rule) for rule in _state['rules']]}
    for index, old in enumerate(presets):
        if old['name'].lower() == name.lower():
            presets[index] = preset
            break
    else:
        if len(presets) >= PRESET_MAX:
            return -1
        presets.append(preset)
        index = len(presets) - 1
    if not SavePresets(presets):
        return -1
    return index


def ApplyPreset(index):
    presets = LoadPresets()
    if not 0 <= index < len(presets):
        return False
    Load()
    preset = presets[index]
    _state['on'] = preset['on']
    _state['kinds'] = preset['kinds'] & ALL_KINDS
    _state['bonus'] = 0
    _state['rules'] = [CopyRule(rule) for rule in preset['rules']]
    chat.AppendChat(chat.CHAT_TYPE_INFO, 'Filtr podnoszenia: wczytano preset "%s".' % preset['name'])
    Changed()
    return True


def DeletePreset(index):
    presets = LoadPresets()
    if not 0 <= index < len(presets):
        return False
    del presets[index]
    return SavePresets(presets)


# ---- the switch and the kinds ------------------------------------------------
def IsActive():
    Load()
    return _state['on'] != 0


def GetKinds():
    """The kinds the filter takes, whether it is on or not."""
    Load()
    return _state['kinds']


def HasKind(bit):
    return (GetKinds() & bit) != 0


def BonusKinds():
    """MT2009_PLUS_PICKUP_RULES_V1: no "Bonus" kinds any more (rules)."""
    return 0


def KindRuleCount(bit):
    Load()
    if not AdvancedEnabled():
        return 0
    return len([rule for rule in _state['rules'] if rule['on'] and rule['kinds'] & bit])


def KindText(bit, yes='Tak', no='Nie', bonus='filtr'):
    """A kind's state as its button says it: no, yes, or yes with a filter."""
    Load()
    if not _state['kinds'] & bit:
        return no
    count = KindRuleCount(bit)
    if count:
        return 'Filtr (%d)' % count
    return yes


def BonusMinText():
    """Auto Lowy's old "Min. bonusow" button now opens the filter window."""
    return 'Dok\xb3adny filtr...'


def CycleBonusMin():
    OpenWindow()


def EffectiveKinds():
    """What may be picked up: the kinds with the filter on, all of them off."""
    Load()
    return _state['kinds'] if _state['on'] else ALL_KINDS


def OnStateText():
    return 'W\xb3\xb9czony' if IsActive() else 'Wy\xb3\xb9czony'


def ToggleOn():
    Load()
    _state['on'] = 0 if _state['on'] else 1
    Changed()


def ToggleKind(bit):
    """A kind taken or not (a left click in either window). With the filter
    off it is turned on too - whoever leaves a kind out means it to stay on
    the ground."""
    Load()
    _state['kinds'] ^= bit
    if not _state['on']:
        _state['on'] = 1
        chat.AppendChat(chat.CHAT_TYPE_INFO, 'Filtr podnoszenia w\xb3\xb9czony (Z, Auto \xa3owy i Towarzysz).')
    Changed()


def Changed():
    Save()
    Send()
    RefreshWindows()


def AdoptAutoHuntKinds(mask):
    """The per-character kinds of Auto Lowy's older files (uiautohunt,
    Hunter.LoadConfig), taken once by a character with no filter file: a file
    that left some kinds out becomes the filter, switched on. A file with
    every kind, or with none (the pick-up in all but name switched off),
    changes nothing. With filtr.cfg the filter's own settings win."""
    Load()
    name = _state['name']
    if _state['file'] or os.path.exists(CONFIG_PATH) or (name and os.path.exists(CharConfigPath(name))):
        return
    mask &= ALL_KINDS
    if mask == 0 or mask == ALL_KINDS:
        return
    _state['on'] = 1
    _state['kinds'] = mask
    chat.AppendChat(chat.CHAT_TYPE_INFO, 'Filtr podnoszenia: rodzaje z Auto \xa3ow\xf3w tej postaci dzia\xb3aj\xb9 teraz dla Z, Auto \xa3ow\xf3w i Towarzysza (Ctrl+Z).')
    Changed()


def RefreshWindows():
    for key in ('window', 'kind_window'):
        window = _state[key]
        if window is not None:
            try:
                if window.IsShow():
                    window.Refresh()
            except RuntimeError:
                pass
    hunter = uiautohunt._hunter
    if hunter is not None and hunter.lootWindow is not None:
        try:
            if hunter.lootWindow.IsShow():
                hunter.lootWindow.Refresh()
        except RuntimeError:
            pass


def OnAck(on='0', kinds='0', *rest):
    # MT2009_PLUS_PICKUP_SYNC_V2: the filter's own command reached the server
    try:
        _state['filter_ack'] = int(on) == (1 if _state['on'] else 0) and int(kinds) == _state['kinds']
    except ValueError:
        _state['filter_ack'] = False


class PickupFilterSync(object):
    """An updatable: the filter to the server once a game phase has a named
    character - after the login and after every warp, when the core may be
    another one - and the queue's commands in their turn."""

    def __init__(self):
        self.sent = False
        # MT2009_PLUS_PICKUP_SYNC_CLOCK_V1: a new game window is a new connection -
        # nothing of the last one's queue or pace is left to wait for.
        del _queue[:]
        _sendTime[0] = 0.0

    def CanUpdate(self):
        return not self.sent or HasQueued() or WaitingAck()

    def OnUpdate(self):
        # MT2009_PLUS_SIDEKICK_WARP_SAFE_V1: only in the game phase (warpsafe.py).
        import warpsafe
        if not warpsafe.InGame():
            return
        if not self.sent and player.GetMainCharacterName():
            self.sent = True
            Send()
        Flush()
        CheckAck()  # MT2009_PLUS_PICKUP_SYNC_V1

    def Destroy(self):
        DestroyWindow()


# ---- the windows (uipickupfilterrules.py) -------------------------------------
def ToggleWindow():
    window = _state['window']
    if window is None:
        import uipickupfilterrules
        window = uipickupfilterrules.PickupFilterWindow()
        _state['window'] = window
    if window.IsShow():
        window.Close()
    else:
        window.Open()


def OpenWindow():
    window = _state['window']
    if window is None or not window.IsShow():
        ToggleWindow()


def OpenKindWindow(bit):
    """The detailed filter of one kind (a right click on it)."""
    if not AdvancedEnabled():
        chat.AppendChat(chat.CHAT_TYPE_INFO, 'Zaawansowany filtr jest wy\xb3\xb9czony: Opcje Gry -> Dodatkowe -> Filtr podnoszenia.')
        return
    window = _state['kind_window']
    if window is None:
        import uipickupfilterrules
        window = uipickupfilterrules.KindFilterWindow()
        _state['kind_window'] = window
    window.OpenKind(bit)


def DestroyWindow():
    for key in ('window', 'kind_window'):
        window = _state[key]
        _state[key] = None
        if window is not None:
            window.Destroy()
