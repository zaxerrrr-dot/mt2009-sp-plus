# MT2009_PLUS_KOLEKCJONER_NAJEMNIKOW_V1: "Kolekcjoner Najemnik\xf3w" - the mercenaries' unlock (the owner, 8 November 2026,
# najemnicy-plan.md: tasks in any order, each once, items handed in as at the Biologist, 95% a hand-in, a permanent
# bonus a task and the next mercenary tier). The Arezzo "Collections System" ported in its working (categories, the
# items with their counters, hand in one, Ctrl hands in all).
#
# MT2009_PLUS_NAJEMNICY_V5 (the owner, 10 November 2026):
#   * the look of "Sesja farmienia" (uifarmsession.py - its frames, colours, flat buttons, header rows, thin scroll
#     bar are used from there, so both windows look the same): a board with a title bar, a row of flat tabs, framed
#     columns with header strips;
#   * a SECOND TAB "Najemnicy" - all of the mercenaries' management (the quest letter only opens this tab now): the
#     slots and the next slot's requirement, every mercenary (class, path, level, summoned or not, its order) with
#     Wezwij/Odwolaj, Ekwipunek, Rozkazy, Lup, Gildia, Zwolnij, the vault (balance, the cost an hour, the time left, a
#     deposit), "Wezwij wszystkich" / "Odwolaj wszystkich", a new mercenary (class, sex, path, name), the rejoin switch;
#   * the collector's tasks come from the server's tables (title, description, minimum level, order, tiers - the Seban
#     panel edits them), the built-in names stay as the fallback;
#   * live counts: while the window is shown every inventory refresh (interfacemodule.RefreshInventory - every item
#     packet, the extra inventory's storages too) recounts "Masz" here, client-side (bag + storages, "unopened" =
#     socket 0 == 0), at most every RECOUNT_SECONDS - no server poll; "Oddaj" lights up at once.
#
# The collector (playerbot_kolekcjoner_najemnikow.cpp):
#   "/kolekcja_najemnikow open" | "oddaj <task> <item> [all]"
#   KNAJ begin <done> <tasks> | tier <nr> <slots> <level> | task <task> <percent> <nr|0> <POINT:value,...|->
#   KNAJ info <task> <hexTitle|-> <minLevel> <sort> | desc <task> <hexDesc|-> | item <task> <item> <vnum> <need>
#   <given> <pack> <unopened> <have> | end <open> | res <task> <item> <code> <ok> <fail> <used> | done <task> <nr> <done>
# The mercenaries (playerbot_najemnicy.h), through one command line shared with the companion's windows
# (uisidekick._queue, COMMAND_SPACING):
#   "/najemnicy panel" (state, live pushes on) | "panel zamknij" | wezwij, odwolaj, rozkaz, wplac, stworz, zwolnij,
#   gildia, gildia_wyjdz, okno, powrot
#   NAJP begin <slots> <tasks> <level> <count> <price_h> <balance> <off> <rejoin> | tier <nr> <slots> <level> |
#   merc <slot> <race> <group> <hexName> <state> <order> <loot> <guild> <level> | end <open>
# The Esc menu's "Kolekcjoner Najemnik\xf3w", the key "kolekcjoner_najemnikow" and "NAJP end 1" (the letter) open it.
#
# Python 2.7 as the client has it; the texts are CP1250 escapes so the file stays ASCII, each a Polish and English pair
# (playerbot_lang.T).

import app
import chat
import item
import net
import player
import snd
import ui

import clientclock
import uisidekick
import uifarmsession as fs

from playerbot_lang import T

try:
	import pack
except ImportError:
	pack = None

COMMAND = '/kolekcja_najemnikow'
NAJ_PREFIX = '/najemnicy '
IMG = 'mt2009_ui/collector/'
SLOT_FALLBACK = 'd:/ymir work/ui/public/Slot_Base.sub'
FACES = {
	0: 'icon/face/warrior_m.tga', 1: 'icon/face/assassin_w.tga', 2: 'icon/face/sura_m.tga', 3: 'icon/face/shaman_w.tga',
	4: 'icon/face/warrior_w.tga', 5: 'icon/face/assassin_m.tga', 6: 'icon/face/sura_w.tga', 7: 'icon/face/shaman_m.tga',
}

# The tiers until the server names its own (playerbot_najemnicy.h): the n-th task done -> n + 1 mercenaries from
# level 75 + 5n.
DEFAULT_TIERS = [(n, n + 1, 80 + (n - 1) * 5) for n in xrange(1, 7)]
RECOUNT_SECONDS = 0.25

# ---------------------------------------------------------------- the layout

WIDTH = 760
HEIGHT = 520
TAB_X = 10
TAB_Y = 32
TAB_HEIGHT = 22
TAB_GAP = 6
PAGE_X = 10
PAGE_Y = 60
PAGE_W = WIDTH - 2 * PAGE_X
PAGE_H = HEIGHT - PAGE_Y - 10
HEAD_H = 22
COL_Y = HEAD_H + 6
COL_H = PAGE_H - COL_Y - HEAD_H - 6
BOTTOM_Y = PAGE_H - HEAD_H
CONTENT_Y = 26

LEFT_X, LEFT_W = 0, 206
MID_X, MID_W = 212, 334
RIGHT_X, RIGHT_W = 552, 188
ROW_H = 56
ROW_GAP = 4
ROWS_SHOWN = 6
ROW_W = LEFT_W - 8 - fs.SCROLL_WIDTH - 4
TILE_W = (MID_W - 18) // 2
TILE_H = 50
TILE_GAP = 6
TILE_COLS = 2
TILE_ROWS = 5
TILES = TILE_COLS * TILE_ROWS
TILES_Y = 50

NCOL_H = PAGE_H - COL_Y
NLEFT_W = 470
NRIGHT_X = 478
NRIGHT_W = PAGE_W - NRIGHT_X
MROW_H = 46
MROW_GAP = 3
MROWS = 7
MROW_W = NLEFT_W - 8
MBTN_W = 72
MBTN_H = 18

TAB_COLLECTOR = 0
TAB_MERCS = 1

# ---------------------------------------------------------------- the colours (uifarmsession's, and a few of ours)

COLOR_TEXT = fs.COLOR_TEXT
COLOR_WHITE = fs.COLOR_HEAD_TEXT
COLOR_DIM = fs.COLOR_DIM
COLOR_GOLD = fs.COLOR_GOLD
COLOR_GOOD = fs.COLOR_RUNNING
COLOR_ERROR = 0xffe08a80
COLOR_BONUS = 0xff9ce09c
COLOR_DONE_BORDER = 0xff4e7a4e
COLOR_PILL_FILL = 0xff2c261c
COLOR_PILL_DONE_FILL = 0xff1c2a1c
COLOR_PILL_OFF_FILL = 0xff201b17
COLOR_SLOT_FRAME = fs.COLOR_SECTION_BORDER
COLOR_SLOT_FILL = 0xff0c0a08
STYLE_GOLD = (0xff4a3e22, 0xffc8a060, 0xff5c4c2a, COLOR_GOLD)
STYLE_TAB = fs.STYLE_TAB
STYLE_TAB_ON = fs.STYLE_TAB_ON
STYLE_BUTTON = fs.STYLE_BUTTON
STYLE_RED = fs.STYLE_RED
STYLE_OFF = fs.STYLE_OFF
CLASS_COLORS = (0xffc86a50, 0xff6ab04a, 0xff7a6ad0, 0xff50a0c8)

# ---------------------------------------------------------------- the texts

TITLE = T('Kolekcjoner Najemnik\xf3w', 'Mercenary Collector')
TAB_LABELS = (T('Kolekcjoner', 'Collector'), T('Najemnicy', 'Mercenaries'))

# The built-in tasks: (Polish, English, a line of description Polish, English) - the fallback when the server's
# table has no title / description.
TASKS = {
	1: ('Skrzynie boss\xf3w', 'Boss chests',
		'Szkatu\xb3ki boss\xf3w, oddawane po jednej.', 'Boss caskets, handed in one at a time.'),
	2: ('Kamienie Duszy', 'Soul Stones',
		'Kamienie Duszy +4, oddawane po jednym.', 'Soul Stones +4, handed in one at a time.'),
	3: ('Cor Draconis', 'Cor Draconis',
		'Cor Draconis z misji Alchemika, paczki po 10.', "The Alchemist's Cor Draconis, packs of 10."),
	4: ('Od\xb3amki Energii', 'Energy Fragments',
		'Od\xb3amki Energii, oddawane w paczkach po 100.', 'Energy Fragments, handed in as packs of 100.'),
	5: ('Per\xb3y i ma\xb3\xbfe', 'Pearls and clams',
		'Per\xb3y po jednej, ma\xb3\xbfe w paczkach po 10.', 'Pearls one at a time, clams as packs of 10.'),
	6: ('Bossowie loch\xf3w', 'Dungeon bosses',
		'Skrzynie boss\xf3w loch\xf3w, tylko nieotwierane.', 'Dungeon boss chests, unopened only.'),
}

# The bonus names (the server's s_aKnPoints; one %d).
POINTS = {
	'MAX_HP': ('Maks. P\xaf +%d', 'Max HP +%d'),
	'MAX_SP': ('Maks. PE +%d', 'Max SP +%d'),
	'MAX_HP_PCT': ('Maks. P\xaf +%d%%', 'Max HP +%d%%'),
	'ATT_GRADE_BONUS': ('Warto\x9c\xe6 ataku +%d', 'Attack value +%d'),
	'MAGIC_ATT_GRADE_BONUS': ('Warto\x9c\xe6 ataku magicznego +%d', 'Magic attack value +%d'),
	'DEF_GRADE_BONUS': ('Obrona +%d', 'Defence +%d'),
	'MAGIC_DEF_GRADE_BONUS': ('Obrona magiczna +%d', 'Magic defence +%d'),
	'ATTBONUS_MONSTER': ('Silny przeciwko potworom +%d%%', 'Strong against monsters +%d%%'),
	'ATTBONUS_BOSS': ('Silny przeciwko bossom +%d%%', 'Strong against bosses +%d%%'),
	'ATTBONUS_STONE': ('Silny przeciwko kamieniom Metin +%d%%', 'Strong against Metin stones +%d%%'),
	'ATTBONUS_HUMAN': ('Silny przeciwko ludziom +%d%%', 'Strong against half-humans +%d%%'),
	'CRITICAL_PCT': ('Szansa na krytyczne uderzenie +%d%%', 'Critical hit chance +%d%%'),
	'PENETRATE_PCT': ('Szansa na przeszywaj\xb9ce uderzenie +%d%%', 'Piercing hit chance +%d%%'),
	'RESIST_FIRE': ('Odporno\x9c\xe6 na ogie\xf1 +%d%%', 'Fire resistance +%d%%'),
	'RESIST_ICE': ('Odporno\x9c\xe6 na l\xf3d +%d%%', 'Ice resistance +%d%%'),
	'RESIST_ELEC': ('Odporno\x9c\xe6 na b\xb3yskawice +%d%%', 'Lightning resistance +%d%%'),
	'RESIST_WIND': ('Odporno\x9c\xe6 na wiatr +%d%%', 'Wind resistance +%d%%'),
	'RESIST_EARTH': ('Odporno\x9c\xe6 na ziemi\xea +%d%%', 'Earth resistance +%d%%'),
	'RESIST_DARK': ('Odporno\x9c\xe6 na ciemno\x9c\xe6 +%d%%', 'Darkness resistance +%d%%'),
	'ATT_SPEED': ('Szybko\x9c\xe6 ataku +%d%%', 'Attack speed +%d%%'),
	'MOV_SPEED': ('Szybko\x9c\xe6 ruchu +%d%%', 'Movement speed +%d%%'),
	'CASTING_SPEED': ('Szybko\x9c\xe6 zakl\xea\xe6 +%d%%', 'Casting speed +%d%%'),
	'HP_REGEN': ('Regeneracja P\xaf +%d%%', 'HP regeneration +%d%%'),
	'SP_REGEN': ('Regeneracja PE +%d%%', 'SP regeneration +%d%%'),
	'STEAL_HP': ('Absorpcja P\xaf +%d%%', 'HP absorption +%d%%'),
	'STEAL_SP': ('Absorpcja PE +%d%%', 'SP absorption +%d%%'),
	'ATTBONUS_ANIMAL': ('Silny przeciwko zwierz\xeatom +%d%%', 'Strong against animals +%d%%'),
	'ATTBONUS_ORC': ('Silny przeciwko orkom +%d%%', 'Strong against orcs +%d%%'),
	'ATTBONUS_MILGYO': ('Silny przeciwko mistykom +%d%%', 'Strong against mystics +%d%%'),
	'ATTBONUS_UNDEAD': ('Silny przeciwko nieumar\xb3ym +%d%%', 'Strong against undead +%d%%'),
	'ATTBONUS_DEVIL': ('Silny przeciwko diab\xb3om +%d%%', 'Strong against devils +%d%%'),
	'ATTBONUS_WARRIOR': ('Silny przeciwko wojownikom +%d%%', 'Strong against warriors +%d%%'),
	'ATTBONUS_ASSASSIN': ('Silny przeciwko ninja +%d%%', 'Strong against ninjas +%d%%'),
	'ATTBONUS_SURA': ('Silny przeciwko surom +%d%%', 'Strong against suras +%d%%'),
	'ATTBONUS_SHAMAN': ('Silny przeciwko szamanom +%d%%', 'Strong against shamans +%d%%'),
	'RESIST_WARRIOR': ('Odporno\x9c\xe6 na wojownik\xf3w +%d%%', 'Resistance to warriors +%d%%'),
	'RESIST_ASSASSIN': ('Odporno\x9c\xe6 na ninja +%d%%', 'Resistance to ninjas +%d%%'),
	'RESIST_SURA': ('Odporno\x9c\xe6 na sury +%d%%', 'Resistance to suras +%d%%'),
	'RESIST_SHAMAN': ('Odporno\x9c\xe6 na szaman\xf3w +%d%%', 'Resistance to shamans +%d%%'),
	'BLOCK': ('Szansa na blok +%d%%', 'Block chance +%d%%'),
	'DODGE': ('Szansa na unik strza\xb3 +%d%%', 'Arrow dodge chance +%d%%'),
	'RESIST_SWORD': ('Odporno\x9c\xe6 na miecze +%d%%', 'Sword resistance +%d%%'),
	'RESIST_TWOHAND': ('Odporno\x9c\xe6 na bro\xf1 dwur\xeaczn\xb9 +%d%%', 'Two-handed resistance +%d%%'),
	'RESIST_DAGGER': ('Odporno\x9c\xe6 na sztylety +%d%%', 'Dagger resistance +%d%%'),
	'RESIST_BELL': ('Odporno\x9c\xe6 na dzwony +%d%%', 'Bell resistance +%d%%'),
	'RESIST_FAN': ('Odporno\x9c\xe6 na wachlarze +%d%%', 'Fan resistance +%d%%'),
	'RESIST_BOW': ('Odporno\x9c\xe6 na strza\xb3y +%d%%', 'Arrow resistance +%d%%'),
	'RESIST_MAGIC': ('Odporno\x9c\xe6 na magi\xea +%d%%', 'Magic resistance +%d%%'),
	'RESIST_CRITICAL': ('Odporno\x9c\xe6 na krytyczne uderzenia +%d%%', 'Critical hit resistance +%d%%'),
	'RESIST_PENETRATE': ('Odporno\x9c\xe6 na przeszywaj\xb9ce uderzenia +%d%%', 'Piercing hit resistance +%d%%'),
	'NORMAL_HIT_DAMAGE_BONUS': ('\x8crednie obra\xbfenia +%d%%', 'Average damage +%d%%'),
	'SKILL_DAMAGE_BONUS': ('Obra\xbfenia umiej\xeatno\x9cci +%d%%', 'Skill damage +%d%%'),
	'NORMAL_HIT_DEFEND_BONUS': ('Odporno\x9c\xe6 na \x9crednie obra\xbfenia +%d%%', 'Average damage resistance +%d%%'),
	'SKILL_DEFEND_BONUS': ('Odporno\x9c\xe6 na obra\xbfenia umiej\xeatno\x9cci +%d%%', 'Skill damage resistance +%d%%'),
	'POISON_PCT': ('Szansa na otrucie +%d%%', 'Poison chance +%d%%'),
	'STUN_PCT': ('Szansa na omdlenie +%d%%', 'Stun chance +%d%%'),
	'SLOW_PCT': ('Szansa na spowolnienie +%d%%', 'Slow chance +%d%%'),
	'EXP_DOUBLE_BONUS': ('Szansa na podw\xf3jne do\x9cwiadczenie +%d%%', 'Double experience chance +%d%%'),
	'GOLD_DOUBLE_BONUS': ('Szansa na podw\xf3jny yang +%d%%', 'Double yang chance +%d%%'),
	'ITEM_DROP_BONUS': ('Szansa na podw\xf3jny drop +%d%%', 'Double drop chance +%d%%'),
}
ELEMENTS = ('RESIST_FIRE', 'RESIST_ICE', 'RESIST_ELEC', 'RESIST_WIND', 'RESIST_EARTH', 'RESIST_DARK')
TEXT_ALL_ELEMENTS = T('+%d%% odporno\x9cci na ka\xbfdy \xbfywio\xb3', '+%d%% resistance to every element')

TEXT_LOADING = T('Wczytywanie...', 'Loading...')
TEXT_NO_TASKS = T('Kolekcjoner nie ma teraz zada\xf1.', 'The Collector has no tasks now.')
TEXT_TASKS_HEAD = T('Zadania', 'Tasks')
TEXT_ITEM_HEAD = T('Przedmiot', 'Item')
TEXT_COUNTER = '%d / %d'
TEXT_GIVEN = T('Oddane', 'Handed in')
TEXT_FROM_LEVEL = T('od %d poziomu', 'from level %d')
TEXT_DONE_HEADER = T('uko\xf1czone (%d.)', 'completed (%d.)')
TEXT_MIN_LEVEL = T('Oddawanie od %d poziomu.', 'Hand-ins from level %d.')
TEXT_CHANCE = T('Szansa: %d%%', 'Chance: %d%%')
TEXT_EVERY = T('Co ile: bez przerwy', 'How often: any time')
TEXT_HAVE = T('Masz: %d szt.', 'You have: %d')
TEXT_PACK = T('Paczka: po %d szt.', 'Pack: %d at a time')
TEXT_UNOPENED = T('Tylko nieotwierane (3/3)', 'Unopened only (3/3)')
TEXT_REWARD = T('NAGRODA', 'REWARD')
TEXT_UNLOCK = T('Odblokowuje: %s', 'Unlocks: %s')
TEXT_UNLOCKED = T('Odblokowa\xb3o: %s', 'Unlocked: %s')
TEXT_SLOT_ONE = T('%d. miejsce najemnika', 'mercenary slot %d')
TEXT_SLOT_MANY = T('%d.-%d. miejsce najemnika', 'mercenary slots %d-%d')
TEXT_SLOT_NONE = T('kolejny pr\xf3g najemnik\xf3w', 'the next mercenary tier')
TEXT_SLOT_LEVEL = T('(od %d poziomu)', '(from level %d)')
TEXT_HAND_IN = T('Oddaj', 'Hand in')
TEXT_CTRL_HINT = T('Ctrl + klik: oddaj wszystko, co masz', 'Ctrl + click: hand in all you have')
TEXT_BOTTOM = T('Za ca\xb3\xb9 kategori\xea (%d/%d): %s', 'For the whole category (%d/%d): %s')
TEXT_BOTTOM_DONE = T('Za ca\xb3\xb9 kategori\xea (%d/%d): %s - aktywny na sta\xb3e', 'For the whole category (%d/%d): %s - active for good')
TEXT_SUMMARY = T('Uko\xf1czone zadania: %d z %d     Miejsca najemnik\xf3w: %d', 'Tasks completed: %d of %d     Mercenary slots: %d')
TEXT_RESULT = T('Udane: %d, nieudane: %d (oddano %d szt.)', 'Succeeded: %d, failed: %d (%d handed in)')
TEXT_COMPLETED = T('Zadanie uko\xf1czone! Bonus dzia\xb3a na sta\xb3e.', 'Task completed! The bonus is permanent.')

STATE_CAN = T('Mo\xbfesz odda\xe6 teraz', 'You can hand in now')
STATE_NONE = T('Brak przedmiotu', 'No item')
STATE_PACK = T('Za ma\xb3o na paczk\xea', 'Not enough for a pack')
STATE_DONE = T('Oddane', 'Handed in')
STATE_TASK_DONE = T('Zadanie uko\xf1czone', 'Task completed')
STATE_LEVEL = T('Od %d poziomu', 'From level %d')

TIP_GIVEN = T('Oddane: %d / %d', 'Handed in: %d / %d')
TIP_PACK = T('Jedno oddanie: paczka %d szt. (liczy si\xea ca\xb3a przy powodzeniu)', 'One hand-in: a pack of %d (counts whole on success)')
TIP_UNOPENED = T('Tylko skrzynie nieotwierane (3/3 otwarcia)', 'Only chests never opened (3/3 openings)')
TIP_HAVE = T('W ekwipunku: %d', 'In your inventory: %d')
TIP_CLICK = T('Dwuklik / PPM: oddaj %d szt.', 'Double / right click: hand in %d')
TIP_CTRL = T('Z Ctrl: oddaj wszystko, co masz', 'With Ctrl: hand in all you have')
TIP_DONE = T('To ju\xbf oddane.', 'All handed in.')

MSG = {
	1: T('Nie masz tego przedmiotu (albo za ma\xb3o na paczk\xea).', 'You do not have this item (or not enough for a pack).'),
	2: T('Ten przedmiot jest ju\xbf ca\xb3y oddany.', 'This item is all handed in.'),
	3: T('To zadanie jest ju\xbf uko\xf1czone.', 'This task is completed already.'),
	4: T('Zamknij najpierw handel, sklep, magazyn lub inne okno.', 'Close the trade, the shop, the storage or the other window first.'),
	5: T('Nie mo\xbfesz tego zrobi\xe6 po \x9cmierci.', 'You cannot do that while dead.'),
	6: T('Kolekcjoner nie przyjmuje teraz przedmiot\xf3w.', 'The Collector takes no items now.'),
	7: T('Tego nie da si\xea odda\xe6.', 'That cannot be handed in.'),
	8: T('Za szybko - spr\xf3buj jeszcze raz.', 'Too fast - try again.'),
	9: T('Kolekcjoner nie jest teraz dost\xeapny - spr\xf3buj za chwil\xea.', 'The Collector is not available now - try again in a moment.'),
}
MSG_LEVEL = T('Za niski poziom - to zadanie od %d poziomu.', 'Level too low - this task is from level %d.')
MSG_LEVEL_PLAIN = T('Za niski poziom na to zadanie.', 'Your level is too low for this task.')

# The Najemnicy tab.
CLASS_NAMES = (T('Wojownik', 'Warrior'), T('Ninja', 'Ninja'), T('Sura', 'Sura'), T('Szaman', 'Shaman'))
PATH_NAMES = (
	(T('Cia\xb3o', 'Body'), T('Mental', 'Mental')),
	(T('Skrytob\xf3jca', 'Blade'), T('\xa3ucznik', 'Archer')),
	(T('Bro\xf1', 'Weapon'), T('Czarna Magia', 'Black Magic')),
	(T('Smok', 'Dragon'), T('Leczenie', 'Healing')),
)
MALE_RACES = (0, 5, 2, 7)
FEMALE_RACES = (4, 1, 6, 3)
SEX_NAMES = (T('M\xea\xbfczyzna', 'Male'), T('Kobieta', 'Female'))
ORDER_NAMES = (T('Za mn\xb9', 'Follow me'), T('St\xf3j tutaj', 'Stay here'), T('Bij m\xf3j cel', 'Hit my target'),
	T('Walcz sam', 'Fight nearby'))
STATE_NAMES = (T('Niewezwany', 'Not summoned'), T('W drodze', 'On its way'), T('Wezwany', 'Summoned'),
	T('Pad\xb3 (wstanie za 30 s)', 'Down (up in 30 s)'))

TEXT_MERCS_HEAD = T('Twoi najemnicy', 'Your mercenaries')
TEXT_VAULT_HEAD = T('Skarbiec', 'Vault')
TEXT_NEW_HEAD = T('Nowy najemnik', 'New mercenary')
TEXT_OPTIONS_HEAD = T('Ustawienia', 'Settings')
TEXT_USED = T('Najemnicy: %d / %d miejsc', 'Mercenaries: %d / %d slots')
TEXT_NEXT = T('Nast\xeapne miejsce (%d.): zadania Kolekcjonera %d/%d, poziom %d/%d',
	'Next slot (%d): collector tasks %d/%d, level %d/%d')
TEXT_ALL_SLOTS = T('Wszystkie miejsca odblokowane.', 'All slots unlocked.')
TEXT_OFF = T('Najemnicy s\xb9 teraz wy\xb3\xb9czeni na tym serwerze.', 'Mercenaries are switched off on this server.')
TEXT_LOCKED = (T('Najemnicy nie s\xb9 jeszcze odblokowani.', 'Mercenaries are not unlocked yet.'),
	T('Ka\xbfde zadanie Kolekcjonera daje miejsce', 'Every collector task gives a slot'),
	T('od swojego poziomu (zak\xb3adka Kolekcjoner).', 'from its level (the Collector tab).'))
TEXT_NO_MERCS = T('Nie masz jeszcze najemnika - stw\xf3rz go po prawej.', 'No mercenary yet - create one on the right.')
TEXT_WAITING = T('Czekam na serwer...', 'Waiting for the server...')
TEXT_INFO = T('%s %s, %d poz.', '%s %s, level %d')
TEXT_STATE_LINE = T('%s  -  %s%s', '%s  -  %s%s')
TEXT_NO_LOOT = T(', bez \xb3upu', ', no loot')
TEXT_IN_GUILD = T(', w gildii', ', in guild')
TEXT_SUMMON = T('Wezwij', 'Summon')
TEXT_DISMISS = T('Odwo\xb3aj', 'Dismiss')
TEXT_EQUIP = T('Ekwipunek', 'Equipment')
TEXT_ORDERS = T('Rozkazy', 'Orders')
TEXT_GUILD_JOIN = T('Do gildii', 'Join guild')
TEXT_GUILD_LEAVE = T('Z gildii', 'Leave guild')
TEXT_RETIRE = T('Zwolnij', 'Release')
TEXT_LOOT_ON = T('\xa3up: tak', 'Loot: on')
TEXT_LOOT_OFF = T('\xa3up: nie', 'Loot: off')
TEXT_SUMMON_ALL = T('Wezwij wszystkich', 'Summon all')
TEXT_DISMISS_ALL = T('Odwo\xb3aj wszystkich', 'Dismiss all')
TEXT_BALANCE = T('Stan: %s yang', 'Balance: %s yang')
TEXT_COST = T('Koszt: %s yang/h (%d wezwanych)', 'Cost: %s yang/h (%d summoned)')
TEXT_COST_NONE = T('Koszt: %s yang/h za ka\xbfdego wezwanego', 'Cost: %s yang/h for each summoned')
TEXT_LEFT = T('Wystarczy na: %d h %d min', 'Lasts: %d h %d min')
TEXT_LEFT_ONE = T('Wystarczy na: %d h %d min (przy 1)', 'Lasts: %d h %d min (for 1)')
TEXT_DEPOSIT = T('Wp\xb3a\xe6', 'Deposit')
TEXT_DEPOSIT_HINT = T('Kwota cyframi, np. 50000000 albo 50kk.', 'Amount in digits, e.g. 50000000 or 50kk.')
TEXT_NAME_HINT = T('Imi\xea: 3-16 liter i cyfr, bez polskich znak\xf3w.', 'Name: 3-16 letters and digits.')
TEXT_CREATE = T('Stw\xf3rz najemnika', 'Create mercenary')
TEXT_FREE = T('Wolne miejsca: %d', 'Free slots: %d')
TEXT_NO_FREE = T('Brak wolnych miejsc (Kolekcjoner i poziom).', 'No free slot (Collector and level).')
TEXT_REJOIN_ON = T('Powr\xf3t po zalogowaniu: tak', 'Return after login: on')
TEXT_REJOIN_OFF = T('Powr\xf3t po zalogowaniu: nie', 'Return after login: off')
TEXT_FEE_NOTE = (T('Op\xb3ata liczy si\xea co minut\xea ze skarbca,', 'The fee is taken from the vault every'),
	T('tylko za wezwanych najemnik\xf3w.', 'minute, only for the summoned ones.'))
TEXT_RETIRE_ASK = T('Zwolni\xe6 %s na dobre? Najpierw odda ci rzeczy.', 'Release %s for good? It gives your things back first.')
TEXT_NEED_NAME = T('Wpisz imi\xea najemnika.', 'Type the mercenary\'s name.')
TEXT_NEED_AMOUNT = T('Wpisz kwot\xea.', 'Type the amount.')


def _Int(value, default=0):
	try:
		return int(value)
	except (TypeError, ValueError):
		return default


def Exists(path):
	if not path:
		return False
	if path.startswith('d:/ymir work/ui/public/'):
		return True
	try:
		return bool(pack and pack.Exist(path))
	except Exception:
		return False


def Image(name):
	path = IMG + name
	return path if Exists(path) else None


def Say(text):
	if text:
		chat.AppendChat(chat.CHAT_TYPE_INFO, text)


def CtrlPressed():
	for key in (app.DIK_LCONTROL, getattr(app, 'DIK_RCONTROL', app.DIK_LCONTROL)):
		try:
			if app.IsPressed(key):
				return True
		except Exception:
			pass
	return False


def Send(text):
	"""Only in the game phase (warpsafe.py)."""
	try:
		import warpsafe
		if not warpsafe.InGame():
			return False
	except ImportError:
		pass
	net.SendChatPacket(text)
	return True


def Level():
	try:
		return player.GetStatus(player.LEVEL)
	except Exception:
		return 0


_names = {}
_icons = {}


def ItemName(vnum):
	if vnum not in _names:
		name = ''
		try:
			item.SelectItem(vnum)
			name = item.GetItemName()
		except Exception:
			name = ''
		_names[vnum] = name or ('#%d' % vnum)
	return _names[vnum]


def ItemIcon(vnum):
	if vnum not in _icons:
		path = ''
		try:
			item.SelectItem(vnum)
			path = item.GetIconImageFileName()
		except Exception:
			path = ''
		_icons[vnum] = path
	return _icons[vnum]


def Fit(text, limit):
	if len(text) <= limit:
		return text
	return text[:max(1, limit - 2)] + '..'


def RewardLines(rewards):
	"""rewards: [(name, value)] -> the bonus lines (the six elements of one value as one line)."""
	lines = []
	values = dict(rewards)
	allElements = len([n for n in ELEMENTS if n in values]) == len(ELEMENTS) and \
		len(set(values[n] for n in ELEMENTS)) == 1
	if allElements:
		lines.append(TEXT_ALL_ELEMENTS % values[ELEMENTS[0]])
	for name, value in rewards:
		if allElements and name in ELEMENTS:
			continue
		if name in POINTS:
			lines.append(T(POINTS[name][0], POINTS[name][1]) % value)
		else:
			lines.append('%s %+d' % (name, value))
	return lines or ['-']


def RewardText(rewards):
	return ', '.join(RewardLines(rewards))


# ---------------------------------------------------------------- the tiers (KNAJ tier / NAJP tier)

_tiers = {'list': list(DEFAULT_TIERS)}


def SetTiers(tiers):
	if tiers:
		_tiers['list'] = sorted(tiers)


def Tier(nr):
	"""(slots, level) of the n-th task done; past the last known: the last one."""
	tiers = _tiers['list']
	for t, slots, level in tiers:
		if t == nr:
			return slots, level
	if tiers and nr > tiers[-1][0]:
		return tiers[-1][1], tiers[-1][2]
	return nr + 1, 80 + (max(1, nr) - 1) * 5


def TierLevel(nr):
	return Tier(nr)[1]


def Slots(tasks, level):
	"""The mercenaries' slots for so many tasks at this level (playerbot_najemnicy.h GetNajemnicySlots)."""
	slots = 0
	for t, s, needLevel in _tiers['list']:
		if t <= tasks and level >= needLevel:
			slots = max(slots, s)
	return min(7, slots)


def TierSlotsText(nr):
	"""What the n-th task done unlocks: "3. miejsce najemnika" or "1.-2. miejsce najemnika"."""
	slots = Tier(nr)[0]
	before = Tier(nr - 1)[0] if nr > 1 else 0
	if slots <= before:
		return TEXT_SLOT_NONE
	if slots - before == 1:
		return TEXT_SLOT_ONE % slots
	return TEXT_SLOT_MANY % (before + 1, slots)


def NextSlot(slots, tasks, level):
	"""The tier that adds the next slot: (nr, its slots, its level), or None when every slot is open."""
	for t, s, needLevel in _tiers['list']:
		if s > slots:
			return t, s, needLevel
	return None


# ---------------------------------------------------------------- the command line (shared with the companion's windows)

_queue = {'pending': []}


def _LineFree(now):
	return now >= uisidekick._queue['next']


def _SendNow(text, now):
	uisidekick._queue['next'] = now + uisidekick.COMMAND_SPACING
	net.SendChatPacket(NAJ_PREFIX + text)


def SendNaj(text):
	"""A "/najemnicy ..." order: at once when the line is free, else after those before it (one waiting order of
	the same words waits once)."""
	_EnsurePump()
	if not uisidekick.InGame():
		return
	now = clientclock.Now()
	if not _queue['pending'] and _LineFree(now):
		_SendNow(text, now)
	elif text not in _queue['pending']:
		_queue['pending'].append(text)


def PumpNaj():
	if not _queue['pending'] or not uisidekick.InGame():
		return False
	now = clientclock.Now()
	if not _LineFree(now):
		return False
	_SendNow(_queue['pending'].pop(0), now)
	return True


class _Pump(ui.Window):
	"""A shown window with no size: its OnUpdate sends the queued orders also while the window is shut."""

	def __init__(self):
		ui.Window.__init__(self)
		self.AddFlag('not_pick')
		self.Show()

	def OnUpdate(self):
		PumpNaj()


def _EnsurePump():
	if _state['pump'] is None:
		_state['pump'] = _Pump()


# ---------------------------------------------------------------- what the server said

class Model(object):
	"""The collector: the tasks in the server's order, their items in theirs."""

	def __init__(self):
		self.Reset()

	def Reset(self):
		self.order = []
		self.tasks = {}
		self.done = 0
		self.loaded = False
		self.tiers = []

	def Begin(self, done, count):
		self.Reset()
		self.done = done

	def Task(self, index, percent, nr, rewards):
		t = self.tasks.get(index)
		if not t:
			t = {'index': index, 'items': {}, 'itemOrder': [], 'title': '', 'desc': '', 'minLevel': 0}
			self.tasks[index] = t
			if index not in self.order:
				self.order.append(index)
		t['percent'] = percent
		t['nr'] = nr
		parsed = []
		if rewards and rewards != '-':
			for part in rewards.split(','):
				if ':' in part:
					name, value = part.split(':', 1)
					parsed.append((name, _Int(value)))
		t['rewards'] = parsed

	def Info(self, index, title, minLevel):
		t = self.tasks.get(index)
		if t:
			t['title'] = uisidekick.DecodeText(title, 64)
			t['minLevel'] = max(0, minLevel)

	def Desc(self, index, desc):
		t = self.tasks.get(index)
		if t:
			t['desc'] = uisidekick.DecodeText(desc, 200)

	def Item(self, index, pos, vnum, need, given, packSize, unopened, have):
		t = self.tasks.get(index)
		if not t:
			return
		t['items'][pos] = {'pos': pos, 'vnum': vnum, 'need': max(1, need), 'given': given, 'pack': max(1, packSize),
			'unopened': unopened, 'have': have}
		if pos not in t['itemOrder']:
			t['itemOrder'].append(pos)

	def Items(self, index):
		t = self.tasks.get(index)
		if not t:
			return []
		return [t['items'][k] for k in t['itemOrder'] if k in t['items']]

	def AllItems(self):
		out = []
		for index in self.order:
			out.extend(self.Items(index))
		return out

	def Name(self, index):
		t = self.tasks.get(index)
		if t and t.get('title'):
			return t['title']
		if index in TASKS:
			return T(TASKS[index][0], TASKS[index][1])
		return T('Zadanie %d', 'Task %d') % index

	def Description(self, index):
		t = self.tasks.get(index)
		if t and t.get('desc'):
			return t['desc']
		if index in TASKS:
			return T(TASKS[index][2], TASKS[index][3])
		return ''

	def MinLevel(self, index):
		t = self.tasks.get(index)
		return t.get('minLevel', 0) if t else 0

	def Units(self, index):
		items = self.Items(index)
		return sum(min(i['given'], i['need']) for i in items), sum(i['need'] for i in items)

	def Progress(self, index):
		given, need = self.Units(index)
		if need <= 0:
			return 100
		return min(100, int(100 * given / need))

	def KindsDone(self, index):
		items = self.Items(index)
		return len([1 for i in items if i['given'] >= i['need']]), len(items)

	def DoneCount(self):
		return len([1 for t in self.tasks.values() if t.get('nr')])


class NajModel(object):
	"""The mercenaries (NAJP): the summary and one dict a mercenary by slot."""

	def __init__(self):
		self.loaded = False
		self.slots = 0
		self.tasks = 0
		self.level = 0
		self.count = 0
		self.price = 0
		self.balance = 0
		self.off = False
		self.rejoin = True
		self.mercs = {}
		self.staged = None
		self.stagedTiers = None

	def Begin(self, args):
		vals = [_Int(a) for a in args[:8]] + [0] * max(0, 8 - len(args))
		self.staged = {'slots': vals[0], 'tasks': vals[1], 'level': vals[2], 'count': vals[3], 'price': vals[4],
			'balance': vals[5], 'off': bool(vals[6]), 'rejoin': bool(vals[7]) if len(args) > 7 else True, 'mercs': {}}
		self.stagedTiers = []

	def Tier(self, args):
		if self.stagedTiers is not None and len(args) >= 3:
			self.stagedTiers.append((_Int(args[0]), _Int(args[1]), _Int(args[2])))

	def Merc(self, args):
		if self.staged is None or len(args) < 9:
			return
		slot = _Int(args[0])
		if slot <= 0:
			return
		self.staged['mercs'][slot] = {'slot': slot, 'race': _Int(args[1]) & 7, 'group': 2 if _Int(args[2]) == 2 else 1,
			'name': uisidekick.DecodeText(args[3], 24) or ('#%d' % slot), 'state': _Int(args[4]),
			'order': _Int(args[5]), 'loot': _Int(args[6], 1), 'guild': _Int(args[7], -1), 'level': _Int(args[8])}

	def End(self):
		s = self.staged
		if s is None:
			return False
		self.slots, self.tasks, self.level, self.count = s['slots'], s['tasks'], s['level'], s['count']
		self.price, self.balance, self.off, self.rejoin = s['price'], s['balance'], s['off'], s['rejoin']
		self.mercs = s['mercs']
		if self.stagedTiers:
			SetTiers(self.stagedTiers)
		self.staged = None
		self.stagedTiers = None
		self.loaded = True
		return True

	def Summoned(self):
		return len([1 for m in self.mercs.values() if m['state'] > 0])


_naj = NajModel()


def OrderOfSlot(slot):
	"""(order, loot) of a mercenary by the NAJP state, None when it is not known (uinajemnicyrozkazy.py)."""
	m = _naj.mercs.get(_Int(slot))
	if not m:
		return None
	return m['order'], m['loot']


def NameOfSlot(slot):
	m = _naj.mercs.get(_Int(slot))
	return m['name'] if m else ''


# ---------------------------------------------------------------- the client-side counts (item 3)

def _BagCells():
	try:
		return player.INVENTORY_PAGE_SIZE * player.INVENTORY_PAGE_COUNT
	except Exception:
		return 90


def CountHave(items):
	"""{(vnum, unopened): count} of these items in the bag and the extra inventory's storages (one pass each);
	"unopened" counts only pieces with socket 0 == 0 (the openings used, ShipDefense_ChestKeep)."""
	wanted = set((i['vnum'], 1 if i['unopened'] else 0) for i in items)
	if not wanted:
		return {}
	vnums = set(v for v, u in wanted)
	strict = set(v for v, u in wanted if u)
	plain = {}
	fresh = {}

	def add(window, pos, vnum):
		count = player.GetItemCount(window, pos) if window is not None else player.GetItemCount(pos)
		plain[vnum] = plain.get(vnum, 0) + count
		if vnum in strict:
			try:
				if window is None:
					socket = player.GetItemMetinSocket(pos, 0)
				else:
					socket = player.GetItemMetinSocket(window, pos, 0)
			except Exception:
				socket = 1
			if socket == 0:
				fresh[vnum] = fresh.get(vnum, 0) + count

	for pos in xrange(_BagCells()):
		vnum = player.GetItemIndex(pos)
		if vnum in vnums:
			add(None, pos, vnum)
	try:
		import uiekwipunek
		if uiekwipunek.IsSupported():
			cells = uiekwipunek.COLUMNS * uiekwipunek.ROWS * len(uiekwipunek.PAGE_NAMES)
			for win, slot, name, icon in uiekwipunek.Categories():
				for pos in xrange(cells):
					vnum = player.GetItemIndex(win, pos)
					if vnum in vnums:
						add(win, pos, vnum)
	except Exception:
		pass
	out = {}
	for vnum, unopened in wanted:
		out[(vnum, unopened)] = fresh.get(vnum, 0) if unopened else plain.get(vnum, 0)
	return out


# ---------------------------------------------------------------- small widgets

class ProgressBar(object):

	def __init__(self, parent, x, y, w, h, keep):
		self.w = w
		self.h = h
		self.back = fs._Rect(parent, x, y, w, h, fs.COLOR_TRACK)
		self.full = fs._Rect(parent, x, y, 0, h, fs.COLOR_BAR)
		self.full.Hide()
		self.width = 0
		self.shown = True
		keep.append(self.back)
		keep.append(self.full)

	def Set(self, percent, done=False):
		self.width = int(self.w * max(0, min(100, percent)) / 100)
		self.full.SetSize(self.width, self.h)
		self.full.SetColor(COLOR_GOOD if done else fs.COLOR_BAR)
		if self.width > 0 and self.shown:
			self.full.Show()
		else:
			self.full.Hide()

	def Show(self):
		self.shown = True
		self.back.Show()
		if self.width > 0:
			self.full.Show()

	def Hide(self):
		self.shown = False
		self.back.Hide()
		self.full.Hide()


class _ClickBox(fs._Frame):
	"""A framed row or tile the mouse picks: a click calls onClick(index), the wheel onWheel(direction)."""

	def __init__(self, width, height, onClick, index, onWheel=None):
		fs._Frame.__init__(self, width, height, fs.COLOR_BOX_BORDER, fs.COLOR_ROW_FILL)
		self.onClick = onClick
		self.onWheel = onWheel
		self.index = index
		self.hover = False
		self.selected = False
		self.done = False

	def SetState(self, selected, done):
		self.selected = selected
		self.done = done
		self._Paint()

	def _Paint(self):
		if self.selected:
			self.SetColors(fs.COLOR_TAB_ON_BORDER, fs.COLOR_ROW_SELECTED)
		else:
			self.SetColors(COLOR_DONE_BORDER if self.done else fs.COLOR_BOX_BORDER,
				fs.COLOR_BOX_HOVER if self.hover else fs.COLOR_ROW_FILL)

	def OnMouseOverIn(self):
		self.hover = True
		self._Paint()

	def OnMouseOverOut(self):
		self.hover = False
		self._Paint()

	def OnMouseLeftButtonUp(self):
		if self.onClick:
			self.onClick(self.index)

	def OnMouseWheel(self, nLen):
		if self.onWheel:
			self.onWheel(-1 if nLen > 0 else 1)
			return True
		return False


class TileEvent(object):
	"""A tile slot's event with the tile's number: the slot window gives back only its own slot (0), and its optional
	second argument is skipped when it is 0."""

	def __init__(self, owner, name, index):
		from _weakref import proxy
		self.owner = proxy(owner)
		self.name = name
		self.index = index

	def __call__(self, *args):
		try:
			getattr(self.owner, self.name)(self.index)
		except ReferenceError:
			pass


# ---------------------------------------------------------------- the window

class KolekcjonerWindow(ui.ScriptWindow):

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.model = Model()
		self.task = 0
		self.pos = -1			# the selected item of the task
		self.page = 0
		self.scroll = 0			# the first task row shown
		self.keep = []
		self.rows = []
		self.tiles = []
		self.mercRows = []
		self.rowTasks = [0] * ROWS_SHOWN
		self.tileItems = [None] * TILES
		self.tooltip = None
		self.statusUntil = 0.0
		self.loadingShown = False
		self.canHandIn = False
		self.tab = TAB_COLLECTOR
		self.tabButtons = []
		self.pages = []
		self.recountDirty = False
		self.nextRecount = 0.0
		self.question = None
		self.questionSlot = 0
		self.pickClass = 0
		self.pickSex = 0
		self.pickPath = 1
		self.__Load()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	# ------------------------------------------------------------ building

	def __Load(self):
		try:
			loader = ui.PythonScriptLoader()
			loader.LoadScriptFile(self, 'uiscript/najemnicykolekcjonerwindow.py')
			self.board = self.GetChild('board')
		except Exception:
			import exception
			exception.Abort('KolekcjonerWindow.LoadWindow')
		self.board.SetCloseEvent(ui.__mem_func__(self.Close))
		self.board.SetTitleName(TITLE)
		self.__Build()

	def __Keep(self, widget):
		self.keep.append(widget)
		return widget

	def __Text(self, parent, x, y, text='', color=COLOR_TEXT, align=None, bold=False):
		"""uifarmsession's line: y is its middle."""
		return self.__Keep(fs._Text(parent, x, y, text, color, align, bold))

	def __Rect(self, parent, x, y, w, h, color):
		return self.__Keep(fs._Rect(parent, x, y, w, h, color))

	def __Frame(self, parent, x, y, w, h, border=fs.COLOR_BOX_BORDER, fill=fs.COLOR_BOX_FILL):
		return self.__Keep(fs._MakeFrame(parent, x, y, w, h, border, fill))

	def __Button(self, parent, x, y, w, h, text, style, event, *args):
		button = fs._FlatButton(w, h, text, style, ui.__mem_func__(event), *args)
		button.SetParent(parent)
		button.SetPosition(x, y)
		button.Show()
		return self.__Keep(button)

	def __Area(self, parent, x, y, w, h):
		"""A pickable place for the widgets the mouse uses (uifarmsession's _Container)."""
		area = ui.Window()
		area.SetParent(parent)
		area.SetPosition(x, y)
		area.SetSize(w, h)
		area.AddFlag('attach')
		area.Show()
		return self.__Keep(area)

	def __Column(self, parent, x, y, w, h, title, titleAlign='center'):
		"""A framed column with a header strip; returns (the area, the header text)."""
		area = self.__Area(parent, x, y, w, h)
		self.__Frame(area, 0, 0, w, h, fs.COLOR_TAB_BORDER, fs.COLOR_COLUMN_FILL)
		head = self.__Head(area, 0, w, title, titleAlign)
		return area, head

	def __Head(self, area, y, w, title, align='center'):
		self.__Rect(area, 1, y + 1, w - 2, HEAD_H - 1, fs.COLOR_HEAD_FILL)
		self.__Rect(area, 1, y + HEAD_H, w - 2, 1, fs.COLOR_HEAD_LINE)
		if align == 'left':
			return self.__Text(area, 10, y + HEAD_H // 2 + 1, title, fs.COLOR_HEAD_TEXT, None, True)
		return self.__Text(area, w // 2, y + HEAD_H // 2 + 1, title, fs.COLOR_HEAD_TEXT, 'center', True)

	def __Slot(self, parent, x, y, pick=True):
		self.__Rect(parent, x - 2, y - 2, 36, 36, COLOR_SLOT_FRAME)
		self.__Rect(parent, x - 1, y - 1, 34, 34, COLOR_SLOT_FILL)
		slot = ui.SlotWindow()
		slot.SetParent(parent)
		slot.SetPosition(x, y)
		slot.SetSize(32, 32)
		slot.AppendSlot(0, 0, 0, 32, 32)
		base = Image('slot.tga') or SLOT_FALLBACK
		try:
			slot.SetSlotBaseImage(base, 1.0, 1.0, 1.0, 1.0)
		except Exception:
			slot.SetSlotBaseImage(SLOT_FALLBACK, 1.0, 1.0, 1.0, 1.0)
		if not pick:
			slot.AddFlag('not_pick')
		slot.Show()
		return self.__Keep(slot)

	def __Edit(self, parent, x, y, w, maxLength, returnEvent):
		self.__Frame(parent, x, y, w, 20, fs.COLOR_BOX_BORDER, fs.COLOR_ROW_FILL)
		edit = ui.EditLine()
		edit.SetParent(parent)
		edit.SetPosition(x + 6, y + 4)
		edit.SetSize(w - 12, 14)
		edit.SetMax(maxLength)
		edit.SetReturnEvent(ui.__mem_func__(returnEvent))
		edit.SetEscapeEvent(ui.__mem_func__(self.__OnEditEscape))
		edit.Show()
		return self.__Keep(edit)

	def __Build(self):
		board = self.board
		tabWidth = (PAGE_W - TAB_GAP) // 2
		for index in xrange(2):
			button = fs._FlatButton(tabWidth, TAB_HEIGHT, TAB_LABELS[index], STYLE_TAB, ui.__mem_func__(self.SelectTab), index)
			button.SetParent(board)
			button.SetPosition(TAB_X + index * (tabWidth + TAB_GAP), TAB_Y)
			button.Show()
			self.tabButtons.append(self.__Keep(button))
		for index in xrange(2):
			page = ui.Window()
			page.SetParent(board)
			page.SetPosition(PAGE_X, PAGE_Y)
			page.SetSize(PAGE_W, PAGE_H)
			page.AddFlag('attach')
			page.Hide()
			self.pages.append(self.__Keep(page))
		self.__BuildCollector(self.pages[TAB_COLLECTOR])
		self.__BuildMercs(self.pages[TAB_MERCS])
		self.__PaintTabs()
		self.pages[self.tab].Show()

	# ------------------------------------------------------------ the Kolekcjoner tab

	def __BuildCollector(self, page):
		head = self.__Frame(page, 0, 0, PAGE_W, HEAD_H)
		self.summaryText = self.__Text(head, PAGE_W // 2, HEAD_H // 2, '', COLOR_TEXT, 'center')
		self.__BuildLeft(page)
		self.__BuildMiddle(page)
		self.__BuildRight(page)
		bottom = self.__Frame(page, 0, BOTTOM_Y, PAGE_W, HEAD_H)
		self.bottomText = self.__Text(bottom, PAGE_W // 2, HEAD_H // 2, '', COLOR_DIM, 'center')

	def __BuildLeft(self, page):
		area, head = self.__Column(page, LEFT_X, COL_Y, LEFT_W, COL_H, TEXT_TASKS_HEAD)
		for i in xrange(ROWS_SHOWN):
			row = {}
			box = _ClickBox(ROW_W, ROW_H, ui.__mem_func__(self.OnClickRow), i, ui.__mem_func__(self.OnRowWheel))
			box.SetParent(area)
			box.SetPosition(4, CONTENT_Y + i * (ROW_H + ROW_GAP))
			box.Show()
			self.__Keep(box)
			row['box'] = box
			row['slot'] = self.__Slot(box, 10, 12, False)
			row['name'] = self.__Text(box, 52, 15, '', COLOR_WHITE)
			row['count'] = self.__Text(box, 52, 31, '', COLOR_DIM)
			row['bar'] = ProgressBar(box, 52, 44, ROW_W - 62, 3, self.keep)
			self.rows.append(row)
		scroll = fs._ThinScroll(ROWS_SHOWN * (ROW_H + ROW_GAP) - ROW_GAP, ui.__mem_func__(self.OnScroll))
		scroll.SetParent(area)
		scroll.SetPosition(LEFT_W - 4 - fs.SCROLL_WIDTH, CONTENT_Y)
		scroll.Hide()
		self.scrollBar = self.__Keep(scroll)

	def __BuildMiddle(self, page):
		area, head = self.__Column(page, MID_X, COL_Y, MID_W, COL_H, '', 'left')
		self.taskName = head
		self.taskLevel = self.__Text(area, MID_W - 10, HEAD_H // 2 + 1, '', COLOR_DIM, 'right')
		self.taskDesc = self.__Text(area, 10, 36, '', COLOR_DIM)
		for i in xrange(TILES):
			col, row = i % TILE_COLS, i // TILE_COLS
			x = 6 + col * (TILE_W + TILE_GAP)
			y = TILES_Y + row * (TILE_H + TILE_GAP)
			tile = {}
			box = _ClickBox(TILE_W, TILE_H, ui.__mem_func__(self.OnClickTile), i)
			box.SetParent(area)
			box.SetPosition(x, y)
			box.Show()
			self.__Keep(box)
			tile['box'] = box
			slot = self.__Slot(box, 8, 9)
			slot.SetSelectItemSlotEvent(TileEvent(self, 'OnTileSlotSelect', i))
			slot.SetUnselectItemSlotEvent(TileEvent(self, 'OnTileSlotUse', i))
			slot.SetUseSlotEvent(TileEvent(self, 'OnTileSlotUse', i))
			slot.SetOverInItemEvent(TileEvent(self, 'OnTileOver', i))
			slot.SetOverOutItemEvent(ui.__mem_func__(self.OnOverOutItem))
			tile['slot'] = slot
			tile['name'] = self.__Text(box, 48, 13, '', COLOR_WHITE)
			pill = self.__Frame(box, 48, 26, TILE_W - 56, 17, fs.COLOR_SECTION_BORDER, COLOR_PILL_FILL)
			tile['pill'] = pill
			tile['count'] = self.__Text(pill, (TILE_W - 56) // 2, 8, '', COLOR_GOLD, 'center')
			self.tiles.append(tile)
		y = COL_H - 24
		self.statusText = self.__Text(area, 10, y + 9, '', COLOR_GOOD)
		self.prevButton = self.__Button(area, MID_W - 82, y, 22, 18, '<', STYLE_DARK_BUTTON(), self.OnPrevPage)
		self.pageText = self.__Text(area, MID_W - 47, y + 9, '', COLOR_TEXT, 'center')
		self.nextButton = self.__Button(area, MID_W - 32, y, 22, 18, '>', STYLE_DARK_BUTTON(), self.OnNextPage)

	def __BuildRight(self, page):
		area, head = self.__Column(page, RIGHT_X, COL_Y, RIGHT_W, COL_H, TEXT_ITEM_HEAD)
		cx = RIGHT_W // 2
		self.__Frame(area, cx - 31, 30, 62, 62, fs.COLOR_TAB_ON_BORDER, COLOR_SLOT_FILL)
		icon = ui.ExpandedImageBox()
		icon.SetParent(area)
		icon.AddFlag('not_pick')
		icon.SetPosition(cx - 24, 37)
		icon.Hide()
		self.bigIcon = self.__Keep(icon)
		self.itemName = self.__Text(area, cx, 104, '', COLOR_WHITE, 'center', True)
		self.itemBar = ProgressBar(area, 16, 116, RIGHT_W - 32, 4, self.keep)
		self.itemCount = self.__Text(area, cx, 130, '', COLOR_TEXT, 'center')
		self.lineChance = self.__Text(area, 12, 150, '', COLOR_TEXT)
		self.lineEvery = self.__Text(area, 12, 166, '', COLOR_TEXT)
		self.lineHave = self.__Text(area, 12, 182, '', COLOR_TEXT)
		self.linePack = self.__Text(area, 12, 198, '', COLOR_DIM)
		self.statePill = self.__Frame(area, 10, 210, RIGHT_W - 20, 22, fs.COLOR_SECTION_BORDER, COLOR_PILL_FILL)
		self.stateText = self.__Text(self.statePill, (RIGHT_W - 20) // 2, 11, '', COLOR_GOLD, 'center')
		self.__Rect(area, 10, 242, RIGHT_W - 20, 1, fs.COLOR_ROW_LINE)
		self.__Text(area, cx, 252, TEXT_REWARD, COLOR_DIM, 'center', True)
		self.rewardLines = [self.__Text(area, cx, 268 + i * 15, '', COLOR_BONUS, 'center') for i in xrange(3)]
		self.unlockLines = [self.__Text(area, cx, 316 + i * 14, '', COLOR_GOLD, 'center') for i in xrange(2)]
		self.__Text(area, cx, COL_H - 50, TEXT_CTRL_HINT if len(TEXT_CTRL_HINT) < 32 else Fit(TEXT_CTRL_HINT, 31),
			COLOR_DIM, 'center')
		self.handButton = self.__Button(area, 10, COL_H - 40, RIGHT_W - 20, 30, TEXT_HAND_IN, STYLE_GOLD,
			self.OnHandInButton)

	# ------------------------------------------------------------ the Najemnicy tab

	def __BuildMercs(self, page):
		head = self.__Frame(page, 0, 0, PAGE_W, HEAD_H)
		self.usedText = self.__Text(head, 10, HEAD_H // 2, '', COLOR_TEXT, None, True)
		self.nextText = self.__Text(head, PAGE_W - 10, HEAD_H // 2, '', COLOR_DIM, 'right')

		area, h = self.__Column(page, 0, COL_Y, NLEFT_W, NCOL_H, TEXT_MERCS_HEAD)
		self.mercArea = area
		for i in xrange(MROWS):
			self.mercRows.append(self.__MercRow(area, 4, CONTENT_Y + i * (MROW_H + MROW_GAP), i))
		self.mercNote = [self.__Text(area, NLEFT_W // 2, 120 + i * 16, '', COLOR_DIM, 'center') for i in xrange(3)]
		y = NCOL_H - 28
		self.summonAllButton = self.__Button(area, 8, y, 150, 20, TEXT_SUMMON_ALL, STYLE_BUTTON, self.OnSummonAll)
		self.dismissAllButton = self.__Button(area, 164, y, 150, 20, TEXT_DISMISS_ALL, STYLE_RED, self.OnDismissAll)

		area, h = self.__Column(page, NRIGHT_X, COL_Y, NRIGHT_W, NCOL_H, TEXT_VAULT_HEAD)
		w = NRIGHT_W
		self.vaultBalance = self.__Text(area, 10, 34, '', COLOR_GOLD, None, True)
		self.vaultCost = self.__Text(area, 10, 50, '', COLOR_TEXT)
		self.vaultLeft = self.__Text(area, 10, 66, '', COLOR_TEXT)
		self.depositEdit = self.__Edit(area, 8, 80, w - 104, 14, self.OnDeposit)
		self.__Button(area, w - 90, 80, 82, 20, TEXT_DEPOSIT, STYLE_GOLD, self.OnDeposit)
		self.__Text(area, 10, 112, TEXT_DEPOSIT_HINT, COLOR_DIM)

		self.__Head(area, 124, w, TEXT_NEW_HEAD)
		bw = (w - 16 - 3 * 4) // 4
		self.classButtons = [self.__Button(area, 8 + i * (bw + 4), 154, bw, 20, CLASS_NAMES[i], STYLE_TAB,
			self.OnPickClass, i) for i in xrange(4)]
		bw2 = (w - 16 - 4) // 2
		self.sexButtons = [self.__Button(area, 8 + i * (bw2 + 4), 178, bw2, 20, SEX_NAMES[i], STYLE_TAB,
			self.OnPickSex, i) for i in xrange(2)]
		self.pathButtons = [self.__Button(area, 8 + i * (bw2 + 4), 202, bw2, 20, '', STYLE_TAB,
			self.OnPickPath, i + 1) for i in xrange(2)]
		self.nameEdit = self.__Edit(area, 8, 228, w - 16, 16, self.OnCreate)
		self.__Text(area, 10, 256, TEXT_NAME_HINT, COLOR_DIM)
		self.createButton = self.__Button(area, 8, 268, w - 16, 22, TEXT_CREATE, STYLE_GOLD, self.OnCreate)
		self.freeText = self.__Text(area, w // 2, 302, '', COLOR_DIM, 'center')

		self.__Head(area, 316, w, TEXT_OPTIONS_HEAD)
		self.rejoinButton = self.__Button(area, 8, 346, w - 16, 20, TEXT_REJOIN_ON, STYLE_BUTTON, self.OnToggleRejoin)
		self.__Text(area, w // 2, 380, TEXT_FEE_NOTE[0], COLOR_DIM, 'center')
		self.__Text(area, w // 2, 395, TEXT_FEE_NOTE[1], COLOR_DIM, 'center')
		self.__PaintCreate()

	def __MercRow(self, parent, x, y, index):
		row = {}
		box = fs._Frame(MROW_W, MROW_H, fs.COLOR_BOX_BORDER, fs.COLOR_ROW_FILL)
		box.SetParent(parent)
		box.SetPosition(x, y)
		box.AddFlag('attach')
		box.Show()
		self.__Keep(box)
		row['box'] = box
		self.__Rect(box, 6, 6, 34, 34, COLOR_SLOT_FRAME)
		row['badge'] = self.__Rect(box, 7, 7, 32, 32, COLOR_SLOT_FILL)
		face = ui.ExpandedImageBox()
		face.SetParent(box)
		face.AddFlag('not_pick')
		face.SetPosition(7, 7)
		face.Hide()
		row['face'] = self.__Keep(face)
		row['letter'] = self.__Text(box, 23, 23, '', COLOR_WHITE, 'center', True)
		row['name'] = self.__Text(box, 48, 9, '', COLOR_WHITE, None, True)
		row['info'] = self.__Text(box, 48, 23, '', COLOR_DIM)
		row['state'] = self.__Text(box, 48, 37, '', COLOR_DIM)
		bx = MROW_W - 6 - 3 * MBTN_W - 2 * 4
		cols = [bx + i * (MBTN_W + 4) for i in xrange(3)]
		row['summon'] = self.__Button(box, cols[0], 4, MBTN_W, MBTN_H, TEXT_SUMMON, STYLE_BUTTON, self.OnMercAction,
			'summon', index)
		row['equip'] = self.__Button(box, cols[1], 4, MBTN_W, MBTN_H, TEXT_EQUIP, STYLE_BUTTON, self.OnMercAction,
			'equip', index)
		row['orders'] = self.__Button(box, cols[2], 4, MBTN_W, MBTN_H, TEXT_ORDERS, STYLE_BUTTON, self.OnMercAction,
			'orders', index)
		row['loot'] = self.__Button(box, cols[0], 24, MBTN_W, MBTN_H, TEXT_LOOT_ON, STYLE_TAB, self.OnMercAction,
			'loot', index)
		row['guild'] = self.__Button(box, cols[1], 24, MBTN_W, MBTN_H, TEXT_GUILD_JOIN, STYLE_TAB, self.OnMercAction,
			'guild', index)
		row['retire'] = self.__Button(box, cols[2], 24, MBTN_W, MBTN_H, TEXT_RETIRE, STYLE_RED, self.OnMercAction,
			'retire', index)
		row['slot'] = 0
		box.Hide()
		return row

	def Destroy(self):
		self.Hide()
		self.OnOverOutItem()
		self.__CloseQuestion()
		self.tooltip = None
		self.rows = []
		self.tiles = []
		self.mercRows = []
		self.tabButtons = []
		self.pages = []
		self.keep = []
		self.scrollBar = None
		self.handButton = None
		self.ClearDictionary()

	# ------------------------------------------------------------ opening

	def Open(self, tab=None, request=True):
		if tab is not None:
			self.SelectTab(tab, False)
		if not self.model.loaded:
			self.__SetStatus(TEXT_LOADING)
		wasShown = self.IsShow()
		self.Show()
		self.SetTop()
		Send(COMMAND + ' open')
		if request and self.tab == TAB_MERCS and (tab is None or not wasShown):
			SendNaj('panel')
		self.recountDirty = True

	def Close(self):
		self.OnOverOutItem()
		self.__CloseQuestion()
		self.__KillFocus()
		if self.IsShow() and self.tab == TAB_MERCS:
			SendNaj('panel zamknij')
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def SelectTab(self, index, request=True):
		if index not in (TAB_COLLECTOR, TAB_MERCS):
			return
		if index == self.tab:
			return
		old = self.tab
		self.tab = index
		self.OnOverOutItem()
		self.__KillFocus()
		for i, page in enumerate(self.pages):
			if i == index:
				page.Show()
			else:
				page.Hide()
		self.__PaintTabs()
		if request and self.IsShow():
			if index == TAB_MERCS:
				SendNaj('panel')
			elif old == TAB_MERCS:
				SendNaj('panel zamknij')
		if index == TAB_MERCS:
			self.RefreshMercs()

	def __PaintTabs(self):
		for i, button in enumerate(self.tabButtons):
			button.SetStyle(STYLE_TAB_ON if i == self.tab else STYLE_TAB)

	def __KillFocus(self):
		for edit in (getattr(self, 'depositEdit', None), getattr(self, 'nameEdit', None)):
			try:
				if edit and edit.IsFocus():
					edit.KillFocus()
			except Exception:
				pass

	def __OnEditEscape(self):
		self.__KillFocus()
		return True

	# ------------------------------------------------------------ server: the collector

	def OnServer(self, word, args):
		m = self.model
		if word == 'begin':
			m.Begin(_Int(args[0] if args else 0), _Int(args[1] if len(args) > 1 else 0))
		elif word == 'tier' and len(args) >= 3:
			m.tiers.append((_Int(args[0]), _Int(args[1]), _Int(args[2])))
		elif word == 'task' and len(args) >= 4:
			m.Task(_Int(args[0]), _Int(args[1]), _Int(args[2]), args[3])
			if m.loaded:
				self.__Refresh()
		elif word == 'info' and len(args) >= 3:
			m.Info(_Int(args[0]), args[1], _Int(args[2]))
		elif word == 'desc' and len(args) >= 2:
			m.Desc(_Int(args[0]), args[1])
		elif word == 'item' and len(args) >= 8:
			m.Item(*[_Int(a) for a in args[:8]])
			if m.loaded:
				self.recountDirty = True
				self.__Refresh()
		elif word == 'end':
			m.loaded = True
			if m.tiers:
				SetTiers(m.tiers)
			if not self.task or self.task not in m.tasks:
				self.task = self.__FirstOpenTask()
				self.page = 0
				self.pos = -1
			if not m.order:
				self.__SetStatus(TEXT_NO_TASKS, True)
			elif self.loadingShown:
				self.__SetStatus('')
			self.recountDirty = True
			self.__Refresh()
			self.RefreshMercs()
			if _Int(args[0] if args else 0) and not self.IsShow():
				self.Show()
				self.SetTop()
		elif word == 'res' and len(args) >= 6:
			task, pos, code, ok, fail, used = [_Int(a) for a in args[:6]]
			if code == 0:
				self.__SetStatus(TEXT_RESULT % (ok, fail, used), ok == 0)
				try:
					snd.PlaySound('sound/ui/drop.wav')
				except Exception:
					pass
			else:
				text = ResultText(code, m.MinLevel(task))
				self.__SetStatus(text, True)
				if not self.IsShow():
					Say(text)
		elif word == 'done' and len(args) >= 3:
			task, nr, done = [_Int(a) for a in args[:3]]
			t = m.tasks.get(task)
			if t:
				t['nr'] = nr
			m.done = done
			self.__SetStatus(TEXT_COMPLETED)
			self.__Refresh()

	def __FirstOpenTask(self):
		for index in self.model.order:
			if not self.model.tasks[index].get('nr'):
				return index
		return self.model.order[0] if self.model.order else 0

	# ------------------------------------------------------------ live counts

	def MarkInventory(self):
		if self.IsShow():
			self.recountDirty = True

	def __Recount(self):
		self.recountDirty = False
		items = self.model.AllItems()
		if not items:
			return
		try:
			counts = CountHave(items)
		except Exception:
			return
		changed = False
		for it in items:
			have = counts.get((it['vnum'], 1 if it['unopened'] else 0), it['have'])
			if have != it['have']:
				it['have'] = have
				changed = True
		if changed:
			self.__Refresh()

	# ------------------------------------------------------------ drawing: the collector

	def __SetStatus(self, text, error=False):
		self.loadingShown = text == TEXT_LOADING
		self.statusText.SetText(Fit(text, 52))
		self.statusText.SetPackedFontColor(COLOR_ERROR if error else COLOR_GOOD)
		self.statusUntil = app.GetTime() + 8.0 if text else 0.0

	def __Refresh(self):
		self.__RefreshRows()
		self.__RefreshMiddle()
		self.__RefreshRight()
		m = self.model
		done = m.DoneCount()
		self.summaryText.SetText(TEXT_SUMMARY % (done, len(m.order), Slots(done, Level())))
		t = m.tasks.get(self.task)
		if t:
			kinds, total = m.KindsDone(self.task)
			template = TEXT_BOTTOM_DONE if t.get('nr') else TEXT_BOTTOM
			self.bottomText.SetText(Fit(template % (kinds, total, RewardText(t.get('rewards', []))), 120))
			self.bottomText.SetPackedFontColor(COLOR_GOOD if t.get('nr') else COLOR_DIM)
		else:
			self.bottomText.SetText('')

	def __RefreshRows(self):
		m = self.model
		order = m.order
		extra = max(0, len(order) - ROWS_SHOWN)
		self.scroll = max(0, min(self.scroll, extra))
		if extra:
			self.scrollBar.SetPage(float(ROWS_SHOWN) / len(order))
			self.scrollBar.SetPos(float(self.scroll) / extra)
			self.scrollBar.Show()
		else:
			self.scrollBar.Hide()
		for i, row in enumerate(self.rows):
			k = self.scroll + i
			index = order[k] if k < len(order) else 0
			self.rowTasks[i] = index
			if not index:
				row['box'].Hide()
				row['slot'].ClearSlot(0)
				continue
			row['box'].Show()
			t = m.tasks[index]
			items = m.Items(index)
			if items:
				row['slot'].SetItemSlot(0, items[0]['vnum'], 0)
			else:
				row['slot'].ClearSlot(0)
			row['slot'].RefreshSlot()
			row['name'].SetText(Fit(m.Name(index), 20))
			given, need = m.Units(index)
			done = bool(t.get('nr'))
			row['count'].SetText(TEXT_COUNTER % (given, need))
			row['count'].SetPackedFontColor(COLOR_GOOD if done else COLOR_DIM)
			row['name'].SetPackedFontColor(COLOR_GOOD if done else COLOR_WHITE)
			row['bar'].Set(m.Progress(index), done)
			row['box'].SetState(index == self.task, done)

	def __RefreshMiddle(self):
		m = self.model
		t = m.tasks.get(self.task)
		items = m.Items(self.task) if t else []
		if t:
			self.taskName.SetText(Fit(m.Name(self.task), 30))
			minLevel = m.MinLevel(self.task)
			desc = m.Description(self.task)
			if minLevel > 0 and not t.get('nr'):
				desc = (desc + ' ' if desc else '') + TEXT_MIN_LEVEL % minLevel
			self.taskDesc.SetText(Fit(desc, 58))
			self.taskDesc.SetPackedFontColor(COLOR_ERROR if minLevel > Level() and not t.get('nr') else COLOR_DIM)
			nr = t.get('nr', 0)
			if nr:
				self.taskLevel.SetText(TEXT_DONE_HEADER % nr)
				self.taskLevel.SetPackedFontColor(COLOR_GOOD)
			else:
				self.taskLevel.SetText(TEXT_FROM_LEVEL % TierLevel(m.DoneCount() + 1))
				self.taskLevel.SetPackedFontColor(COLOR_DIM)
		else:
			self.taskName.SetText('')
			self.taskDesc.SetText('')
			self.taskLevel.SetText('')
		pages = max(1, (len(items) + TILES - 1) // TILES)
		self.page = max(0, min(self.page, pages - 1))
		shown = items[self.page * TILES:(self.page + 1) * TILES]
		if items and self.pos not in [i['pos'] for i in items]:
			self.pos = self.__FirstOpenItem(items)
		taskDone = bool(t and t.get('nr'))
		for i, tile in enumerate(self.tiles):
			it = shown[i] if i < len(shown) else None
			self.tileItems[i] = it
			if not it:
				tile['box'].Hide()
				tile['slot'].ClearSlot(0)
				continue
			tile['box'].Show()
			complete = taskDone or it['given'] >= it['need']
			tile['slot'].SetItemSlot(0, it['vnum'], it['pack'] if it['pack'] > 1 else 0)
			tile['slot'].RefreshSlot()
			tile['name'].SetText(Fit(ItemName(it['vnum']), 16))
			if complete:
				tile['count'].SetText(TEXT_GIVEN)
				tile['count'].SetPackedFontColor(COLOR_GOOD)
				tile['pill'].SetColors(COLOR_DONE_BORDER, COLOR_PILL_DONE_FILL)
				tile['name'].SetPackedFontColor(COLOR_DIM)
			else:
				tile['count'].SetText(TEXT_COUNTER % (it['given'], it['need']))
				tile['count'].SetPackedFontColor(COLOR_GOLD)
				tile['pill'].SetColors(fs.COLOR_SECTION_BORDER, COLOR_PILL_FILL)
				tile['name'].SetPackedFontColor(COLOR_WHITE)
			tile['box'].SetState(it['pos'] == self.pos, complete)
		if pages > 1:
			self.pageText.SetText('%d/%d' % (self.page + 1, pages))
			self.prevButton.Show()
			self.nextButton.Show()
		else:
			self.pageText.SetText('')
			self.prevButton.Hide()
			self.nextButton.Hide()

	def __FirstOpenItem(self, items):
		for it in items:
			if it['given'] < it['need']:
				return it['pos']
		return items[0]['pos'] if items else -1

	def __Selected(self):
		t = self.model.tasks.get(self.task)
		if not t:
			return None, None
		return t, t['items'].get(self.pos)

	def __RefreshRight(self):
		t, it = self.__Selected()
		if not t or not it:
			for line in (self.itemName, self.itemCount, self.lineChance, self.lineEvery, self.lineHave, self.linePack,
					self.stateText):
				line.SetText('')
			self.bigIcon.Hide()
			self.itemBar.Set(0)
			self.statePill.Hide()
			for line in self.rewardLines + self.unlockLines:
				line.SetText('')
			self.__SetHandIn(False)
			return
		icon = ItemIcon(it['vnum'])
		if icon:
			try:
				self.bigIcon.LoadImage(icon)
				self.bigIcon.SetScale(1.5, 1.5)
				self.bigIcon.Show()
			except Exception:
				self.bigIcon.Hide()
		else:
			self.bigIcon.Hide()
		taskDone = bool(t.get('nr'))
		complete = taskDone or it['given'] >= it['need']
		given = min(it['given'], it['need'])
		self.itemName.SetText(Fit(ItemName(it['vnum']), 26))
		self.itemBar.Set(int(100 * given / max(1, it['need'])), complete)
		self.itemCount.SetText(TEXT_COUNTER % (given, it['need']))
		self.lineChance.SetText(TEXT_CHANCE % t.get('percent', 0))
		self.lineEvery.SetText(TEXT_EVERY)
		self.lineHave.SetText(TEXT_HAVE % it['have'])
		extra = []
		if it['pack'] > 1:
			extra.append(TEXT_PACK % it['pack'])
		if it['unopened']:
			extra.append(TEXT_UNOPENED)
		self.linePack.SetText(extra[0] if extra else '')
		self.statePill.Show()
		minLevel = t.get('minLevel', 0)
		if taskDone:
			state, color, ok = STATE_TASK_DONE, COLOR_GOOD, False
		elif complete:
			state, color, ok = STATE_DONE, COLOR_GOOD, False
		elif minLevel > Level():
			state, color, ok = STATE_LEVEL % minLevel, COLOR_ERROR, False
		elif it['have'] >= it['pack']:
			state, color, ok = STATE_CAN, COLOR_GOLD, True
		elif it['have'] > 0:
			state, color, ok = STATE_PACK, COLOR_ERROR, False
		else:
			state, color, ok = STATE_NONE, COLOR_ERROR, False
		self.stateText.SetText(state)
		self.stateText.SetPackedFontColor(color)
		if complete:
			self.statePill.SetColors(COLOR_DONE_BORDER, COLOR_PILL_DONE_FILL)
		elif ok:
			self.statePill.SetColors(fs.COLOR_TAB_ON_BORDER, COLOR_PILL_FILL)
		else:
			self.statePill.SetColors(fs.COLOR_BOX_BORDER, COLOR_PILL_OFF_FILL)
		self.__SetHandIn(ok)
		lines = RewardLines(t.get('rewards', []))
		for i, line in enumerate(self.rewardLines):
			line.SetText(Fit(lines[i], 30) if i < len(lines) else '')
		nr = t.get('nr', 0)
		tier = nr if nr else self.model.DoneCount() + 1
		template = TEXT_UNLOCKED if nr else TEXT_UNLOCK
		self.unlockLines[0].SetText(Fit(template % TierSlotsText(tier), 32))
		self.unlockLines[1].SetText(TEXT_SLOT_LEVEL % TierLevel(tier))

	def __SetHandIn(self, ok):
		self.canHandIn = ok
		if self.handButton:
			self.handButton.SetStyle(STYLE_GOLD if ok else STYLE_OFF)

	# ------------------------------------------------------------ the player: the collector

	def OnClickRow(self, i):
		index = self.rowTasks[i] if 0 <= i < ROWS_SHOWN else 0
		if not index or index == self.task:
			return
		self.task = index
		self.page = 0
		self.pos = -1
		self.OnOverOutItem()
		self.__Refresh()

	def OnRowWheel(self, direction):
		extra = max(0, len(self.model.order) - ROWS_SHOWN)
		if not extra:
			return
		self.scroll = max(0, min(extra, self.scroll + direction))
		self.__RefreshRows()

	def OnScroll(self, pos):
		extra = max(0, len(self.model.order) - ROWS_SHOWN)
		self.scroll = int(round(pos * extra))
		self.__RefreshRows()

	def OnClickTile(self, i):
		it = self.tileItems[i] if 0 <= i < TILES else None
		if not it:
			return
		self.pos = it['pos']
		self.__Refresh()

	def __Carrying(self):
		try:
			import mouseModule
			return mouseModule.mouseController.isAttached()
		except Exception:
			return False

	def OnTileSlotSelect(self, i):
		# a left click on the icon: the tile is selected, as a click beside it
		if not self.__Carrying():
			self.OnClickTile(i)

	def OnTileSlotUse(self, i):
		# a right click or a double click on the icon: one hand-in (Ctrl: all)
		if self.__Carrying():
			return
		self.OnClickTile(i)
		self.__HandIn()

	def OnPrevPage(self):
		self.page = max(0, self.page - 1)
		self.__Refresh()

	def OnNextPage(self):
		self.page += 1
		self.__Refresh()

	def OnHandInButton(self):
		self.__HandIn()

	def __HandIn(self):
		t, it = self.__Selected()
		if not t or not it or t.get('nr') or it['given'] >= it['need']:
			return
		minLevel = t.get('minLevel', 0)
		if minLevel > Level():
			self.__SetStatus(MSG_LEVEL % minLevel, True)
			return
		if it['have'] < it['pack']:
			self.__SetStatus(MSG[1], True)
			return
		Send('%s oddaj %d %d%s' % (COMMAND, self.task, it['pos'], ' all' if CtrlPressed() else ''))

	def OnTileOver(self, i):
		it = self.tileItems[i] if 0 <= i < TILES else None
		if not it:
			return
		if not self.tooltip:
			try:
				import uiToolTip
				self.tooltip = uiToolTip.ItemToolTip()
				self.tooltip.HideToolTip()
			except Exception:
				self.tooltip = None
		if not self.tooltip:
			return
		tip = self.tooltip
		tip.ClearToolTip()
		tip.SetItemToolTip(it['vnum'])
		tip.AppendSpace(5)
		tip.AppendTextLine(TIP_GIVEN % (min(it['given'], it['need']), it['need']), COLOR_GOLD)
		if it['pack'] > 1:
			tip.AppendTextLine(TIP_PACK % it['pack'], COLOR_DIM)
		if it['unopened']:
			tip.AppendTextLine(TIP_UNOPENED, COLOR_DIM)
		t = self.model.tasks.get(self.task, {})
		if t.get('nr') or it['given'] >= it['need']:
			tip.AppendTextLine(TIP_DONE, COLOR_GOOD)
		else:
			tip.AppendTextLine(TIP_HAVE % it['have'], COLOR_TEXT)
			tip.AppendTextLine(TIP_CLICK % it['pack'], COLOR_DIM)
			tip.AppendTextLine(TIP_CTRL, COLOR_DIM)
		tip.ShowToolTip()

	def OnOverOutItem(self, *args):
		if self.tooltip:
			self.tooltip.HideToolTip()

	# ------------------------------------------------------------ drawing: the mercenaries

	def RefreshMercs(self):
		if not self.mercRows:
			return
		n = _naj
		level = n.level or Level()
		if not n.loaded:
			self.usedText.SetText(TEXT_WAITING)
			self.nextText.SetText('')
		else:
			self.usedText.SetText(TEXT_USED % (n.count, n.slots))
			nxt = NextSlot(n.slots, n.tasks, level)
			if n.off:
				self.nextText.SetText(TEXT_OFF)
				self.nextText.SetPackedFontColor(COLOR_ERROR)
			elif nxt:
				nr, slots, needLevel = nxt
				self.nextText.SetText(TEXT_NEXT % (slots, min(n.tasks, nr), nr, min(level, needLevel), needLevel))
				self.nextText.SetPackedFontColor(COLOR_DIM)
			else:
				self.nextText.SetText(TEXT_ALL_SLOTS)
				self.nextText.SetPackedFontColor(COLOR_GOOD)
		mercs = [n.mercs[k] for k in sorted(n.mercs.keys())]
		for i, row in enumerate(self.mercRows):
			m = mercs[i] if i < len(mercs) else None
			if not m:
				row['slot'] = 0
				row['box'].Hide()
				continue
			row['slot'] = m['slot']
			row['box'].Show()
			self.__PaintMerc(row, m)
		notes = ('', '', '')
		if n.loaded and n.slots <= 0 and not mercs:
			notes = TEXT_LOCKED
		elif n.loaded and not mercs:
			notes = (TEXT_NO_MERCS, '', '')
		elif not n.loaded:
			notes = (TEXT_WAITING, '', '')
		for line, text in zip(self.mercNote, notes):
			line.SetText(text)
		summoned = n.Summoned()
		anyIdle = len([1 for m in mercs if m['state'] == 0 and m['slot'] <= n.slots]) > 0
		self.summonAllButton.SetStyle(STYLE_BUTTON if anyIdle and not n.off else STYLE_OFF)
		self.dismissAllButton.SetStyle(STYLE_RED if summoned else STYLE_OFF)
		# the vault
		self.vaultBalance.SetText(TEXT_BALANCE % fs.FormatNumber(n.balance))
		price = max(0, n.price)
		if summoned:
			self.vaultCost.SetText(TEXT_COST % (fs.FormatNumber(price * summoned), summoned))
		else:
			self.vaultCost.SetText(TEXT_COST_NONE % fs.FormatNumber(price))
		per = price * max(1, summoned) // 60
		minutes = n.balance // per if per > 0 else 0
		self.vaultLeft.SetText((TEXT_LEFT if summoned else TEXT_LEFT_ONE) % (minutes // 60, minutes % 60))
		self.vaultLeft.SetPackedFontColor(COLOR_ERROR if summoned and minutes <= 10 else COLOR_TEXT)
		self.rejoinButton.SetText(TEXT_REJOIN_ON if n.rejoin else TEXT_REJOIN_OFF)
		self.__PaintCreate()

	def __PaintMerc(self, row, m):
		race = m['race']
		cls = race % 4
		face = FACES.get(race)
		shown = False
		if face and Exists(face):
			try:
				row['face'].LoadImage(face)
				width = max(1, row['face'].GetWidth())
				height = max(1, row['face'].GetHeight())
				row['face'].SetScale(32.0 / width, 32.0 / height)
				row['face'].Show()
				shown = True
			except Exception:
				shown = False
		if shown:
			row['letter'].SetText('')
			row['badge'].SetColor(COLOR_SLOT_FILL)
		else:
			row['face'].Hide()
			row['badge'].SetColor(CLASS_COLORS[cls])
			row['letter'].SetText(CLASS_NAMES[cls][:1])
		state = m['state']
		here = state in (2, 3)
		locked = m['slot'] > _naj.slots
		row['name'].SetText('%d. %s' % (m['slot'], Fit(m['name'], 18)))
		row['name'].SetPackedFontColor(COLOR_GOLD if state else COLOR_WHITE)
		row['info'].SetText(Fit(TEXT_INFO % (CLASS_NAMES[cls], PATH_NAMES[cls][1 if m['group'] == 2 else 0],
			m['level'] or _naj.level), 29))
		order = ORDER_NAMES[m['order']] if 0 <= m['order'] < len(ORDER_NAMES) else ORDER_NAMES[0]
		extra = ('' if m['loot'] else TEXT_NO_LOOT) + (TEXT_IN_GUILD if m['guild'] == 1 else '')
		stateName = STATE_NAMES[state] if 0 <= state < len(STATE_NAMES) else STATE_NAMES[0]
		row['state'].SetText(Fit(TEXT_STATE_LINE % (stateName, order, extra), 30))
		row['state'].SetPackedFontColor(COLOR_GOOD if state == 2 else (COLOR_ERROR if state == 3 else COLOR_DIM))
		if state:
			row['summon'].SetText(TEXT_DISMISS)
			row['summon'].SetStyle(STYLE_RED)
		else:
			row['summon'].SetText(TEXT_SUMMON)
			row['summon'].SetStyle(STYLE_OFF if locked or _naj.off else STYLE_BUTTON)
		row['equip'].SetStyle(STYLE_BUTTON if here else STYLE_OFF)
		row['orders'].SetStyle(STYLE_BUTTON)
		row['loot'].SetText(TEXT_LOOT_ON if m['loot'] else TEXT_LOOT_OFF)
		row['loot'].SetStyle(STYLE_TAB_ON if m['loot'] else STYLE_TAB)
		if m['guild'] == 1:
			row['guild'].SetText(TEXT_GUILD_LEAVE)
			row['guild'].SetStyle(STYLE_TAB_ON)
		else:
			row['guild'].SetText(TEXT_GUILD_JOIN)
			row['guild'].SetStyle(STYLE_TAB if here else STYLE_OFF)

	def __PaintCreate(self):
		for i, button in enumerate(self.classButtons):
			button.SetStyle(STYLE_TAB_ON if i == self.pickClass else STYLE_TAB)
		for i, button in enumerate(self.sexButtons):
			button.SetStyle(STYLE_TAB_ON if i == self.pickSex else STYLE_TAB)
		for i, button in enumerate(self.pathButtons):
			button.SetText(PATH_NAMES[self.pickClass][i])
			button.SetStyle(STYLE_TAB_ON if i + 1 == self.pickPath else STYLE_TAB)
		n = _naj
		free = max(0, n.slots - n.count) if n.loaded else 0
		self.createButton.SetStyle(STYLE_GOLD if free > 0 and not n.off else STYLE_OFF)
		if not n.loaded:
			self.freeText.SetText('')
		elif free > 0:
			self.freeText.SetText(TEXT_FREE % free)
			self.freeText.SetPackedFontColor(COLOR_GOOD)
		else:
			self.freeText.SetText(TEXT_NO_FREE)
			self.freeText.SetPackedFontColor(COLOR_DIM)

	# ------------------------------------------------------------ the player: the mercenaries

	def OnMercAction(self, action, index):
		row = self.mercRows[index] if 0 <= index < len(self.mercRows) else None
		slot = row['slot'] if row else 0
		m = _naj.mercs.get(slot)
		if not m:
			return
		if action == 'summon':
			if m['state']:
				SendNaj('odwolaj %d' % slot)
			else:
				SendNaj('wezwij %d' % slot)
		elif action == 'equip':
			SendNaj('okno %d' % slot)
		elif action == 'orders':
			try:
				import uinajemnicyrozkazy
				uinajemnicyrozkazy.Open(slot, m['name'])
			except Exception:
				pass
		elif action == 'loot':
			SendNaj('rozkaz %d %s' % (slot, 'nie_podnos' if m['loot'] else 'podnos'))
		elif action == 'guild':
			SendNaj(('gildia_wyjdz %d' if m['guild'] == 1 else 'gildia %d') % slot)
		elif action == 'retire':
			self.__AskRetire(slot, m['name'])

	def __AskRetire(self, slot, name):
		import uiCommon
		self.__CloseQuestion()
		question = uiCommon.QuestionDialog()
		question.SetText(TEXT_RETIRE_ASK % name)
		question.SetAcceptEvent(ui.__mem_func__(self.__OnRetireAccept))
		question.SetCancelEvent(ui.__mem_func__(self.__CloseQuestion))
		question.Open()
		self.question = question
		self.questionSlot = slot

	def __OnRetireAccept(self):
		slot = self.questionSlot
		self.__CloseQuestion()
		if slot > 0:
			SendNaj('zwolnij %d tak' % slot)

	def __CloseQuestion(self):
		question = self.question
		self.question = None
		if question:
			question.Close()

	def OnSummonAll(self):
		SendNaj('wezwij wszyscy')

	def OnDismissAll(self):
		if _naj.Summoned():
			SendNaj('odwolaj wszyscy')

	def OnDeposit(self):
		text = self.depositEdit.GetText().strip().replace(' ', '')
		if not text:
			Say(TEXT_NEED_AMOUNT)
			return
		SendNaj('wplac %s' % text)
		self.depositEdit.SetText('')
		self.__KillFocus()

	def OnPickClass(self, index):
		self.pickClass = index
		self.__PaintCreate()

	def OnPickSex(self, index):
		self.pickSex = index
		self.__PaintCreate()

	def OnPickPath(self, group):
		self.pickPath = group
		self.__PaintCreate()

	def OnCreate(self):
		name = self.nameEdit.GetText().strip()
		if not name:
			Say(TEXT_NEED_NAME)
			return
		if ' ' in name:
			name = name.replace(' ', '')
		races = FEMALE_RACES if self.pickSex else MALE_RACES
		SendNaj('stworz %d %d %s' % (races[self.pickClass], self.pickPath, name))
		self.nameEdit.SetText('')
		self.__KillFocus()

	def OnToggleRejoin(self):
		SendNaj('powrot %d' % (0 if _naj.rejoin else 1))
		_naj.rejoin = not _naj.rejoin
		self.rejoinButton.SetText(TEXT_REJOIN_ON if _naj.rejoin else TEXT_REJOIN_OFF)

	# ------------------------------------------------------------ the clock

	def OnUpdate(self):
		if self.statusUntil and app.GetTime() > self.statusUntil:
			self.statusUntil = 0.0
			self.statusText.SetText('')
		if self.recountDirty:
			now = app.GetTime()
			if now >= self.nextRecount:
				self.nextRecount = now + RECOUNT_SECONDS
				self.__Recount()


def STYLE_DARK_BUTTON():
	return fs.STYLE_DARK


def ResultText(code, minLevel=0):
	if code == 10:
		return MSG_LEVEL % minLevel if minLevel > 0 else MSG_LEVEL_PLAIN
	return MSG.get(code, MSG[7])


_state = {'window': None, 'pump': None}


def GetWindow(create=True):
	if not _state['window'] and create:
		_state['window'] = KolekcjonerWindow()
	return _state['window']


def OpenWindow(tab=None):
	GetWindow().Open(tab)


def ToggleWindow():
	w = GetWindow()
	if w.IsShow():
		w.Close()
	else:
		w.Open()


def DestroyWindow():
	w = _state['window']
	_state['window'] = None
	if w:
		w.Destroy()
	pump = _state['pump']
	_state['pump'] = None
	if pump:
		pump.Hide()
	_queue['pending'] = []


def RefreshInventory():
	"""interfacemodule.RefreshInventory (every item packet - the bag and the extra inventory's storages): the
	counts of the shown window are recounted at its next update (at most every RECOUNT_SECONDS)."""
	w = _state['window']
	if w is not None and w.IsShow():
		w.MarkInventory()


def OnServer(word='', *args):
	"""game.py: every "KNAJ <word> ..." line."""
	if word == 'res' or word == 'done':
		w = GetWindow(False)
		if not w:
			# no window yet (a hand-in typed by hand): only the message
			if word == 'res' and len(args) >= 3 and _Int(args[2]):
				Say(ResultText(_Int(args[2])))
			return
	GetWindow().OnServer(word, list(args))


def OnNajpServer(word='', *args):
	"""game.py: every "NAJP <word> ..." line (playerbot_najemnicy.h, the mercenaries' tab)."""
	args = list(args)
	if word == 'begin':
		_naj.Begin(args)
	elif word == 'tier':
		_naj.Tier(args)
	elif word == 'merc':
		_naj.Merc(args)
	elif word == 'end':
		if not _naj.End():
			return
		w = GetWindow(False)
		if _Int(args[0] if args else 0):
			w = GetWindow()
			if not w.IsShow() or w.tab != TAB_MERCS:
				w.Open(TAB_MERCS, False)	# "panel otworz" marked the panel open already
		if w:
			w.RefreshMercs()
		try:
			__import__('uinajemnicyrozkazy').Refresh()
		except Exception:
			pass
