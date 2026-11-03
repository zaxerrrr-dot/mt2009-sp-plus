#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_bot_catalogue.py

MT2009_PLUS_BOT_ISHOP_CATALOGUE_V1 (the owner, 31 October 2026: "Daj mu pelen dostep do bazy, niech kupuja wszystko co
potrzebuja, niech znaja wszystkie przedmioty" - and, earlier the same day, "kupuja rozne przedmioty, tylko gdy ich
potrzebuja - nie na zapas"): every line of the ItemShop V3 catalogue classified for the bots - which of their needs
uses the item, how many a bot may hold and buy a day, or why it is never a bot's.

  python3 tools/itemshop3/gen_bot_catalogue.py --docker mt2009plustest-db
      reads the catalogue from the test world's database (read only: one SELECT over the view itemshop3.shop, the
      categories and world.item_proto) into tools/itemshop3/bot_catalogue_dump.tsv, then generates
  python3 tools/itemshop3/gen_bot_catalogue.py
      generates from the dump already there (the committed snapshot)
  ... --report
      also prints every row with its class and reason

Writes (GENERATED - do not edit, run this again after the catalogue changes):
  linux-port/overlays/playerbot/src/game/src/playerbot_ishop3_catalogue_data.h

The prices are not in the table: the bots read them from itemshop3.shop at runtime (RefreshPlayerBotIshop3Catalogue,
playerbot_itemshop.h) - the table only says what an item is FOR. A vnum the table does not know (a line added after
the last run) is bought by no new rule; the hold/day defaults of playerbot_itemshop.h apply to it. Run with --report
after a catalogue change: UNKNOWN rows (an item type no rule here names) are listed for a decision.

The classes (the C++ side: playerbot_ishop3_goals.h, CollectPlayerBotIshop3CatalogueGoals):
  NEVER    no bot ever buys it (the reason in the row's comment)
  OWNED    a pass of its own already buys it for a use (the goals of playerbot_ishop3_goals.h, the shop aids, the wishes,
           the Sung Ma guides, the element passes, the looks) - the table gives its hold/day caps and the census
  USE      the catalogue pass buys it when the bot lacks it for a use its passes make now (a quiver for a bow, the pet's
           food, a cape for a cape build, the rank fruit for the next Kamien Duchowy) - never from tomorrow's coins
  COMFORT  the catalogue pass buys it when the bot would use it and has coins to spare: half of what today's allowance
           still holds after the open goals (Smocze Monety), or Smocze Znaki over a reserve
"""
import argparse
import collections
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
DUMP = os.path.join(HERE, 'bot_catalogue_dump.tsv')
OUT = os.path.join(REPO, 'linux-port', 'overlays', 'playerbot', 'src', 'game', 'src', 'playerbot_ishop3_catalogue_data.h')

QUERY = (
    "SELECT s.id, s.category, COALESCE(c.kind, ''), s.pay_type, COALESCE(s.coins, 0), s.discount, s.count, s.vnum, "
    "s.time, s.min_level, COALESCE(s.vip, 0), COALESCE(s.auction, 0), s.arezzo_locked, s.chest, COALESCE(s.available, 0), "
    "s.stackable, COALESCE(p.type, -1), COALESCE(p.subtype, -1), COALESCE(p.stack, 0), COALESCE(p.value0, 0), "
    "COALESCE(p.value1, 0), COALESCE(p.locale_name, s.name, '') "
    "FROM itemshop3.shop s LEFT JOIN itemshop3.categories c ON c.id = s.category "
    "LEFT JOIN world.item_proto p ON p.vnum = s.vnum ORDER BY s.vnum, s.id")
COLS = ['id', 'category', 'kind', 'pay_type', 'coins', 'discount', 'count', 'vnum', 'time', 'min_level', 'vip', 'auction',
        'arezzo_locked', 'chest', 'available', 'stackable', 'type', 'subtype', 'stack', 'value0', 'value1', 'name']

# item_proto types / subtypes (common/item_length.h)
ITEM_WEAPON, ITEM_USE, ITEM_UNIQUE, ITEM_GIFTBOX, ITEM_COSTUME, ITEM_PET = 1, 3, 16, 23, 28, 37
COSTUME_BODY, COSTUME_HAIR, COSTUME_MOUNT, COSTUME_ACCE, COSTUME_WEAPON = 0, 1, 2, 3, 4
USE_AFFECT, USE_SPECIAL, USE_POTION_NODELAY = 8, 10, 11
PET_PAY = 12
TIMED_BUFF = 510	# PLAYERBOT_USE_AFFECT_TIMED_BUFF (playerbot_types.h): what UsePlayerBotBoosters drinks in a fight

NEEDS = [
    # name, class, what it means (the header's comment)
    ('NEVER', 'NEVER', 'no bot buys it'),
    ('LOOK_HAIR', 'OWNED', 'the look pass: a costume set\'s hairstyle (PickPlayerBotLook)'),
    ('LOOK_COSTUME', 'OWNED', 'the look pass: a costume'),
    ('LOOK_WEAPON_SKIN', 'OWNED', 'the look pass: a weapon skin over its own kind of weapon'),
    ('LOOK_PET', 'OWNED', 'the look pass: a pet seal'),
    ('LOOK_MOUNT', 'OWNED', 'the look pass: a mount seal'),
    ('LOOK_SET_CHEST', 'OWNED', 'the set chest of a dressed bot, once a week (ManagePlayerBotIshop3Chest)'),
    ('BONUS_STONE', 'OWNED', 'the bonus passes\' goals (bonus_add / bonus_change / bonus_marble)'),
    ('COR', 'OWNED', 'the Alchemist\'s goal (cor)'),
    ('BEAN', 'OWNED', 'the Alchemist\'s goal (bean)'),
    ('SASH', 'OWNED', 'the sash keeper\'s goal (sash)'),
    ('REFINE_SCROLL', 'OWNED', 'the scroll work\'s goal and wish (refine / blessing_scroll)'),
    ('SMITH', 'OWNED', 'the Blacksmith\'s better scrolls (smith_scroll, playerbot_shop_aids.h)'),
    ('SEONHAE', 'OWNED', 'the 6th/7th lines (bonus_67add / bonus_67change, playerbot_shop_aids.h)'),
    ('STONE_BOOK', 'OWNED', 'a cracked stone\'s socket cleaned (bonus_socket_clean, playerbot_shop_aids.h)'),
    ('RELIC_SOUL', 'OWNED', 'the relic\'s next bonus or charge (relic_soul, playerbot_relikty.cpp)'),
    ('ELEMENT_STONE', 'OWNED', 'the element stones\' renewal (playerbot_element_stones.h)'),
    ('ELEMENT_PET', 'OWNED', 'the hunt element\'s pet (playerbot_element_pet.h)'),
    ('SUNGMA', 'OWNED', 'the Sung Ma guides: the premium buff, the elixirs, the boosters (playerbot_yohara_guides.h)'),
    ('BOOSTER', 'OWNED', 'the raid / tower / war booster wish and the Sung Ma boosters'),
    ('LOCH_TICKET', 'OWNED', 'the Loch\'s ticket (loch_ticket, playerbot_yohara_guides.h)'),
    ('WISH', 'OWNED', 'a wish of playerbot_itemshop.h (detector, teleport ring, exorcism, Rada Pustelnika)'),
    ('TIMED_BUFF', 'COMFORT', 'a fight potion the booster pass drinks (UsePlayerBotBoosters), when the bot holds none of its line'),
    ('POTION_RED', 'COMFORT', 'a red potion of the potion pass, when the bag runs low far from the general store'),
    ('POTION_BLUE', 'COMFORT', 'a blue potion of the potion pass, when the bag runs low'),
    ('AUTO_POTION_HP', 'COMFORT', 'an auto HP potion (ManagePlayerBotAutoPotions) when none is running or held'),
    ('AUTO_POTION_SP', 'COMFORT', 'an auto SP potion when none is running or held'),
    ('CAPE', 'USE', 'Peleryna Mestwa for a cape build short of PLAYERBOT_CAPE_WANT'),
    ('NEWPET', 'USE', 'the New Pet\'s want (GetPlayerBotNewPetWant): the food for its life energy'),
    ('HORSE_FEED', 'COMFORT', 'the horse\'s feed for its next try (Mt2009KonieBotFeedWanted) beyond the daily gift'),
    ('LIFE_FRUIT', 'USE', 'Owoc Zycia for the rank of the next Kamien Duchowy when no counter has one'),
    ('QUIVER', 'USE', 'Kolczan for an archer\'s bow (its arrows never run out)'),
]
NEED_INDEX = dict((n[0], i) for i, n in enumerate(NEEDS))
CLASS_OF = dict((n[0], n[1]) for n in NEEDS)
CLASSES = ['NEVER', 'OWNED', 'USE', 'COMFORT']

# The per-vnum decisions: need, hold, day, reason. hold / day 0 = no cap (a piece that does not stack - its own rule
# buys one), None = the runtime default for a stackable (playerbot_itemshop.h: 10 held, 20 a day).
# The hold/day of the OWNED stones are MT2009_PLUS_BOT_ISHOP_NEED_V1's (350730d3) - moved here unchanged.
EXPLICIT = {
    # --- the bonus stones and the refine (owned by the goals)
    71084: ('BONUS_STONE', 60, 60, 'Zaczarowanie: the Yohara plan\'s reserve (40) and a batch'),
    71085: ('BONUS_STONE', 24, 32, 'Wzmocnienie: the open lines of the bot\'s pieces'),
    70024: ('BONUS_STONE', 2, 4, 'the marble for a piece of four lines'),
    51501: ('COR', 60, 60, 'raw Cor for a dragon stone kind under its target'),
    100300: ('BEAN', 24, 40, 'a strength refine waits, V3\'s bean cheaper than the Alchemist\'s'),
    85001: ('SASH', 3, 4, 'the keeper\'s three'),
    25041: ('REFINE_SCROLL', 6, 6, 'a worn piece under scroll work, no safe scroll held'),
    71025: ('SMITH', 10, 10, 'Podrecznik Kowala (+ a Blessing Scroll at Kowal 20016)'),
    71026: ('SMITH', 10, 10, 'Zwoj Boga Smokow (+ a Blessing Scroll at Kowal 20016)'),
    71052: ('SEONHAE', 5, 10, 'a worn piece\'s 6th/7th lines rolled again'),
    72065: ('SEONHAE', 10, 15, 'a Seon-Hae recipe\'s additive'),
    72066: ('SEONHAE', 10, 15, 'a Seon-Hae recipe\'s additive'),
    72067: ('SEONHAE', 10, 15, 'a Seon-Hae recipe\'s additive'),
    71083: ('STONE_BOOK', None, None, 'a cracked stone blocks a stone that waits'),
    30255: ('RELIC_SOUL', 2, 4, 'the relic\'s next step'),
    30256: ('RELIC_SOUL', 2, 4, 'the relic\'s next step'),
    30257: ('RELIC_SOUL', 2, 4, 'the relic\'s next step'),
    30258: ('RELIC_SOUL', 2, 4, 'the relic\'s next step'),
    39119: ('ELEMENT_STONE', 0, 0, 'bought only when missing'),
    39120: ('ELEMENT_STONE', 0, 0, 'bought only when missing'),
    39048: ('NEVER', None, None, 'a class chest (MT2009_PLUS_CLASS_CHESTS_V1, 999 SM) - the bots read their books from the market and the drops'),
    39050: ('NEVER', None, None, 'a class chest (MT2009_PLUS_CLASS_CHESTS_V1, 999 SM) - the bots read their books from the market and the drops'),
    39052: ('NEVER', None, None, 'a class chest (MT2009_PLUS_CLASS_CHESTS_V1, 999 SM) - the bots read their books from the market and the drops'),
    39054: ('NEVER', None, None, 'a class chest (MT2009_PLUS_CLASS_CHESTS_V1, 999 SM) - the bots read their books from the market and the drops'),
    39056: ('NEVER', None, None, 'a class chest (MT2009_PLUS_CLASS_CHESTS_V1, 999 SM) - the bots read their books from the market and the drops'),
    39058: ('NEVER', None, None, 'a class chest (MT2009_PLUS_CLASS_CHESTS_V1, 999 SM) - the bots read their books from the market and the drops'),
    39060: ('NEVER', None, None, 'a class chest (MT2009_PLUS_CLASS_CHESTS_V1, 999 SM) - the bots read their books from the market and the drops'),
    39062: ('NEVER', None, None, 'a class chest (MT2009_PLUS_CLASS_CHESTS_V1, 999 SM) - the bots read their books from the market and the drops'),
    72803: ('SUNGMA', 0, 0, 'the Will alone between the bot and its next map'),
    72804: ('SUNGMA', None, None, 'the Sung Ma Will elixir of its stat'),
    72805: ('SUNGMA', None, None, 'the Sung Ma Will elixir of its stat'),
    72806: ('SUNGMA', None, None, 'the Sung Ma Will elixir of its stat'),
    72807: ('SUNGMA', None, None, 'the Sung Ma Will elixir of its stat'),
    71027: ('BOOSTER', 1, 8, 'one held, the next when it is drunk'),
    71028: ('BOOSTER', 1, 8, 'one held, the next when it is drunk'),
    71029: ('BOOSTER', 1, 8, 'one held, the next when it is drunk'),
    71030: ('BOOSTER', 1, 8, 'one held, the next when it is drunk'),
    71044: ('BOOSTER', 1, 8, 'one held, the next when it is drunk'),
    71045: ('BOOSTER', 1, 8, 'one held, the next when it is drunk'),
    70408: ('LOCH_TICKET', 2, 4, 'a ticket a run (the single line)'),
    27989: ('WISH', 0, 0, 'a stone hunter without a detector'),
    70058: ('WISH', 0, 0, 'the frontier without a ring'),
    71001: ('WISH', None, None, 'a class book waiting to be read'),
    71094: ('WISH', None, None, 'a book waiting, no book bonus running'),
    # --- the catalogue pass's own (MT2009_PLUS_BOT_ISHOP_CATALOGUE_V1)
    71014: ('TIMED_BUFF', 2, 6, 'Mikstura Ataku +10 (its attack line)'),
    71034: ('TIMED_BUFF', 2, 6, 'Mikstura Ataku +15 (the same line, the stronger)'),
    71050: ('TIMED_BUFF', 2, 6, 'Mikstura Szybkosci (movement)'),
    71101: ('TIMED_BUFF', 2, 6, 'Mikstura Pospiechu'),
    71018: ('POTION_RED', 20, 20, 'Blogoslawienstwo Zycia - the red list of the potion pass (gear.h)'),
    71020: ('POTION_BLUE', 20, 20, 'Blogoslawienstwo Smoka - the blue list of the potion pass (gear.h)'),
    72724: ('AUTO_POTION_HP', 1, 2, 'Eliksir Slonca (S) - an auto HP potion'),
    72728: ('AUTO_POTION_SP', 1, 2, 'Eliksir Ksiezyca (S) - an auto SP potion'),
    70138: ('CAPE', 10, 10, 'PLAYERBOT_CAPE_KEEP; never the 50-pack over it'),
    55001: ('NEWPET', 4, 8, 'PLAYERBOT_NEWPET_PROTEIN_KEEP'),
    50048: ('HORSE_FEED', 80, 100, 'the bar and the try (50) of a horse of level 21+'),
    71107: ('LIFE_FRUIT', 2, 2, 'PLAYERBOT_LIFE_FRUIT_BUY_KEEP'),
    8010: ('QUIVER', 1, 1, 'one, worn; 14 days'),
    # --- never, with the reason
    71019: ('NEVER', None, None, 'Blogoslawienstwo Magii - no potion list of the bots drinks it'),
    70020: ('NEVER', None, None, 'the wine - no potion list of the bots drinks it'),
    22000: ('NEVER', None, None, 'return scrolls - a bot travels by its own warps'),
    22010: ('NEVER', None, None, 'return scrolls - a bot travels by its own warps'),
    79668: ('NEVER', None, None, 'teleport stones - a bot travels by its own warps'),
    79669: ('NEVER', None, None, 'teleport stones - a bot travels by its own warps'),
    71005: ('NEVER', None, None, 'a language ring - the bots read every kingdom\'s chat anyway'),
    71006: ('NEVER', None, None, 'a language ring - the bots read every kingdom\'s chat anyway'),
    71007: ('NEVER', None, None, 'a language ring - the bots read every kingdom\'s chat anyway'),
    71011: ('NEVER', None, None, 'an emotion mask - no bot logic'),
    71033: ('NEVER', None, None, 'an emotion mask - no bot logic'),
    71012: ('NEVER', None, None, 'Ksiazka Lidera - the bots\' parties take no leader bonus'),
    40002: ('NEVER', None, None, 'the anti-exp ring - a bot always takes its experience'),
    71099: ('NEVER', None, None, 'Pierscien Zastepstwa - no bot logic'),
    72701: ('NEVER', None, None, 'wind boots - the unique slots are the element stones\''),
    72702: ('NEVER', None, None, 'wind boots - the unique slots are the element stones\''),
    71049: ('NEVER', None, None, 'Szpula Jedwabiu - the counter pass refuses a permanent bundle (playerbot_town.h)'),
    76055: ('NEVER', None, None, 'Strona ekwipunku II - addeq refuses a bot (the second set swaps through the bag)'),
    71009: ('NEVER', None, None, 'Powiekszony Sklad - the bots\' storage passes use the safebox they have'),
    72199: ('NEVER', None, None, 'Przepustka Triumfu - every bot holds the premium subscription'),
    71069: ('NEVER', None, None, 'a marriage item - the bots do not marry'),
    71070: ('NEVER', None, None, 'a marriage item - the bots do not marry'),
    71071: ('NEVER', None, None, 'a marriage item - the bots do not marry'),
    71072: ('NEVER', None, None, 'a marriage item - the bots do not marry'),
    71073: ('NEVER', None, None, 'a marriage item - the bots do not marry'),
    71074: ('NEVER', None, None, 'a marriage item - the bots do not marry'),
    30190: ('NEVER', None, None, 'Krwisty Kamien - a bot enters the Grota Wygnancow without a pass'),
    71095: ('NEVER', None, None, 'Przepustka - a bot enters Loch Pajakow V2 without a pass'),
    70430: ('NEVER', None, None, 'the Serpent Temple\'s entry - no bot run takes it'),
    30319: ('NEVER', None, None, 'Zasuszona Glowa - the Demon Tower\'s drop, goods for the counter'),
    31146: ('NEVER', None, None, 'Ksiazka Przebudzenia - no bot logic'),
    39063: ('NEVER', None, None, 'Gaya shop reset - the bots do not trade at the Gaya shop'),
    39064: ('NEVER', None, None, 'Gaya shop extension - the bots do not trade at the Gaya shop'),
    50347: ('NEVER', None, None, 'a guild skill reset - the bots\' guilds keep their skills'),
    70401: ('NEVER', None, None, 'Sztandar Czaszki - no bot logic'),
    71000: ('NEVER', None, None, 'Zwoj Zmiany Treningu - the bots keep their ripostes'),
    71002: ('NEVER', None, None, 'a status reset - the bots never redistribute'),
    71003: ('NEVER', None, None, 'a skill reset - the bots never relearn (a companion\'s is its player\'s)'),
    71103: ('NEVER', None, None, 'a status redistribution - the bots never redistribute'),
    71104: ('NEVER', None, None, 'a status redistribution - the bots never redistribute'),
    71105: ('NEVER', None, None, 'a status redistribution - the bots never redistribute'),
    71106: ('NEVER', None, None, 'a status redistribution - the bots never redistribute'),
    71109: ('NEVER', None, None, 'Zwoj Korekcji - the bots never redistribute'),
    72068: ('NEVER', None, None, 'Nowa Wola - the bots\' Sung Ma points follow their own plan, never reset'),
    72069: ('NEVER', None, None, 'Nowa Wola - the bots\' Sung Ma points follow their own plan, never reset'),
    72070: ('NEVER', None, None, 'Nowa Wola - the bots\' Sung Ma points follow their own plan, never reset'),
    72071: ('NEVER', None, None, 'Nowa Wola - the bots\' Sung Ma points follow their own plan, never reset'),
    71048: ('NEVER', None, None, 'a name change - never'),
    71054: ('NEVER', None, None, 'a kingdom change - never'),
    71004: ('NEVER', None, None, 'Medal Smoka (death\'s exp loss) - no bot logic'),
    72322: ('NEVER', None, None, 'a Monster Card reset - bots have no cards (playerbot_monster_card.h)'),
    72323: ('NEVER', None, None, 'a Monster Card shuffle - bots have no cards'),
    83036: ('NEVER', None, None, 'a Monster Card box - bots have no cards'),
    83037: ('NEVER', None, None, 'a Monster Card box - bots have no cards'),
    83073: ('NEVER', None, None, 'a Monster Card box - bots have no cards'),
    83074: ('NEVER', None, None, 'a Monster Card box - bots have no cards'),
    72325: ('NEVER', None, None, 'Transmutacja - the bots never transmute'),
    72326: ('NEVER', None, None, 'Transmutacja - the bots never transmute'),
    72344: ('NEVER', None, None, 'a mount polymorph - the bots never transmute'),
    72328: ('NEVER', None, None, 'Znak Straznika - the Zodiac runs are the operator\'s (their spheres too)'),
    72329: ('NEVER', None, None, 'Pergamin Sfer - the Zodiac runs are the operator\'s (their spheres too)'),
    49101: ('NEVER', None, None, 'Szata Aury - the bots have no aura logic'),
    49991: ('NEVER', None, None, 'an aura rune - the bots have no aura logic'),
    49992: ('NEVER', None, None, 'an aura rune - the bots have no aura logic'),
    49993: ('NEVER', None, None, 'an aura rune - the bots have no aura logic'),
    49994: ('NEVER', None, None, 'an aura rune - the bots have no aura logic'),
    49995: ('NEVER', None, None, 'an aura rune - the bots have no aura logic'),
    89999: ('NEVER', None, None, 'Swiadectwo Aury+ - the bots have no aura logic'),
    30177: ('NEVER', None, None, 'Olejek Pizmowy - no bot logic'),
    70035: ('NEVER', None, None, 'Magiczna Ruda Miedzi - the Blacksmith\'s Zwoj Wojny is no scroll the bots craft'),
    39068: ('NEVER', None, None, 'Zdobna Skrz. z Odlamkiem - the shards come from the bots\' own hunts'),
    30263: ('NEVER', None, None, 'Pakiet Dusz - the relic goal buys the one soul it waits for, four at once is stock'),
    55002: ('NEVER', None, None, 'the pet transporter - trading pets is the players\''),
    55008: ('NEVER', None, None, 'a pet rename - never'),
    55009: ('NEVER', None, None, 'Skrzynia Ksiag Peta - the bots take the exact books off the counters'),
    55033: ('NEVER', None, None, 'Reverti - the bots keep their pets\' skills'),
    55034: ('NEVER', None, None, 'Revertus - the bots keep their pets\' skills'),
    55036: ('NEVER', None, None, 'the heroic pet\'s slot key - no bot logic opens it'),
    83050: ('NEVER', None, None, 'Zestaw Opieki nad Koniem - the feed is bought by its own line (50048)'),
    72800: ('NEVER', None, None, 'Auto Lowy - the bots hunt by their own AI (IsPlayerBotIshop3ExcludedVnum)'),
    72801: ('NEVER', None, None, 'Auto Lowy - the bots hunt by their own AI (IsPlayerBotIshop3ExcludedVnum)'),
    72802: ('NEVER', None, None, 'Szklo Handlu - excluded (IsPlayerBotIshop3ExcludedVnum)'),
    70115: ('NEVER', None, None, 'Kolekcjoner - the collector\'s storage no bot uses'),
    50513: ('NEVER', None, None, 'Kamien Duchowy - hidden in V3 (line 907, category 0)'),
}
ELEMENT_PETS = range(53290, 53296)


def price(r):
    """Shop::getItemPrice - the discount's whole per cent off."""
    return int(r['coins']) - int(float(r['discount']) / 100.0 * float(r['coins']))


def eligible(r):
    """A line RefreshPlayerBotIshop3Catalogue keeps (the runtime decides again: the Arezzo module, the proto)."""
    p = price(r)
    return (int(r['category']) > 0 and not int(r['vip']) and not int(r['auction']) and int(r['available']) == 1
            and 0 < p and int(r['count']) > 0 and int(r['pay_type']) in (1, 2))


def classify(vnum, rows):
    """(need, hold, day, reason) of a vnum's lines."""
    r = rows[0]
    t, st, v0 = int(r['type']), int(r['subtype']), int(r['value0'])
    if not any(eligible(x) for x in rows):
        if any(int(x['vip']) for x in rows):
            return 'NEVER', None, None, 'VIP - every bot holds the premium subscription'
        if all(int(x['category']) <= 0 for x in rows):
            return 'NEVER', None, None, 'not on sale (category 0)'
        return 'NEVER', None, None, 'no line a bot may buy (unavailable / auction)'
    if 80014 <= vnum <= 80019:
        return 'NEVER', None, None, 'a Kupon SM is cashed, never bought'
    if vnum in EXPLICIT:
        return EXPLICIT[vnum]
    if vnum in ELEMENT_PETS:
        return 'ELEMENT_PET', 0, 0, 'its element\'s pet, bought only when missing'
    if t == ITEM_COSTUME and st == COSTUME_HAIR:
        return 'LOOK_HAIR', 0, 0, 'a hairstyle'
    if t == ITEM_COSTUME and st == COSTUME_BODY:
        return 'LOOK_COSTUME', 0, 0, 'a costume'
    if t == ITEM_COSTUME and st == COSTUME_WEAPON:
        return 'LOOK_WEAPON_SKIN', 0, 0, 'a weapon skin'
    if t == ITEM_COSTUME and st == COSTUME_MOUNT:
        return 'LOOK_MOUNT', 0, 0, 'a mount'
    if t == ITEM_PET and st == PET_PAY:
        return 'LOOK_PET', 0, 0, 'a pet seal'
    if t == ITEM_USE and st == USE_SPECIAL and 85200 <= vnum <= 85299:
        return 'NEVER', None, None, 'a sash skin - the bots have no sash-skin logic'
    if t == ITEM_USE and st == USE_AFFECT and v0 == TIMED_BUFF:
        return 'TIMED_BUFF', 2, 6, 'a fight potion (a new one: the generic rule)'
    return 'UNKNOWN', None, None, 'type %d/%d - no rule; decide in EXPLICIT' % (t, st)


def read_dump(path):
    rows = []
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            if not line:
                continue
            p = line.split('\t')
            if len(p) != len(COLS):
                sys.exit('bad dump line (%d columns): %r' % (len(p), line[:120]))
            rows.append(dict(zip(COLS, p)))
    return rows


def dump_from_docker(container):
    cmd = ['docker', 'exec', container, 'sh', '-c',
           'mariadb -uroot -p"$MARIADB_ROOT_PASSWORD" -N -B -e "%s"' % QUERY.replace('"', '\\"')]
    out = subprocess.run(cmd, check=True, stdout=subprocess.PIPE).stdout.decode('utf-8')
    with open(DUMP, 'w', encoding='utf-8') as f:
        f.write(out)


def ascii_name(s):
    tr = str.maketrans('ąćęłńóśźżĄĆĘŁŃÓŚŹŻ', 'acelnoszzACELNOSZZ')
    return s.translate(tr).encode('ascii', 'replace').decode('ascii').replace('*/', '* /')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--docker', help='read the catalogue from this database container first')
    ap.add_argument('--report', action='store_true')
    a = ap.parse_args()
    if a.docker:
        dump_from_docker(a.docker)
    rows = read_dump(DUMP)
    by_vnum = collections.OrderedDict()
    chests = []
    for r in rows:
        if int(r['chest']):
            chests.append(r)
        elif int(r['vnum']):
            by_vnum.setdefault(int(r['vnum']), []).append(r)
    out_rows = []
    unknown = []
    for vnum in sorted(by_vnum):
        lines = by_vnum[vnum]
        need, hold, day, reason = classify(vnum, lines)
        if need == 'UNKNOWN':
            unknown.append((vnum, lines[0]['name'], reason))
            need = 'NEVER'
        el = [x for x in lines if eligible(x)]
        cur = 0
        for x in el:
            cur |= 1 if int(x['pay_type']) == 1 else 2
        stack = int(lines[0]['stackable']) and int(lines[0]['stack']) > 1
        if hold is None:
            hold, day = (10, 20) if stack else (0, 0)
        minlv = min([int(x['min_level']) for x in el] or [0])
        out_rows.append((vnum, need, hold, day, min(255, minlv), len(el), len(lines), cur, lines[0]['name'], reason,
                         [(int(x['id']), int(x['count']), price(x), int(x['pay_type'])) for x in el]))
    chest_rows = []
    for r in chests:
        ok = eligible(r)
        if r['kind'] == 'sets':
            need, reason = ('LOOK_SET_CHEST', 'a costume set chest') if int(r['pay_type']) == 1 else \
                ('NEVER', 'a set chest for Smocze Znaki - the look buys for Smocze Monety')
        else:
            need, reason = 'NEVER', 'a chest of timed unique rings - the unique slots are the element stones\''
        if not ok:
            need, reason = 'NEVER', 'not on sale to a bot'
        chest_rows.append((int(r['id']), int(r['chest']), need, price(r), int(r['count']), r['name'] or '', reason))

    cnt = collections.Counter()
    lines_by_class = collections.Counter()
    for row in out_rows:
        cnt[CLASS_OF[row[1]]] += 1
        lines_by_class[CLASS_OF[row[1]]] += row[5]
    for c in chest_rows:
        cnt[CLASS_OF[c[2]]] += 1
        lines_by_class[CLASS_OF[c[2]]] += 1
    need_cnt = collections.Counter(r[1] for r in out_rows)
    need_cnt.update(c[2] for c in chest_rows)

    L = []
    L.append('// playerbot_ishop3_catalogue_data.h - GENERATED by tools/itemshop3/gen_bot_catalogue.py from the ItemShop V3')
    L.append('// catalogue (itemshop3.shop + world.item_proto, the dump tools/itemshop3/bot_catalogue_dump.tsv) - do not edit,')
    L.append('// run the generator. MT2009_PLUS_BOT_ISHOP_CATALOGUE_V1: every item of the catalogue with the bots\' need that')
    L.append('// uses it (or NEVER and why), the hold / day caps (MT2009_PLUS_BOT_ISHOP_NEED_V1) and the lines it has.')
    L.append('// The prices are read at runtime (RefreshPlayerBotIshop3Catalogue); this table says what an item is FOR.')
    L.append('//')
    L.append('// The catalogue: %d lines (%d items, %d chest lines); classes by item: %s.' % (
        len(rows), len(out_rows), len(chest_rows),
        ', '.join('%s %d' % (c, cnt[c]) for c in CLASSES)))
    L.append('// Lines a bot may buy, by class: %s.' % ', '.join('%s %d' % (c, lines_by_class[c]) for c in CLASSES))
    L.append('#ifndef __INC_METIN2_PLAYERBOT_ISHOP3_CATALOGUE_DATA_H__')
    L.append('#define __INC_METIN2_PLAYERBOT_ISHOP3_CATALOGUE_DATA_H__')
    L.append('')
    L.append('namespace')
    L.append('{')
    L.append('\tenum EPlayerBotIshop3Need')
    L.append('\t{')
    for name, cls, what in NEEDS:
        L.append('\t\tPLAYERBOT_ISHOP3_NEED_%s,\t// %s: %s' % (name, cls, what))
    L.append('\t\tPLAYERBOT_ISHOP3_NEED_COUNT,')
    L.append('\t};')
    L.append('')
    L.append('\tenum EPlayerBotIshop3NeedClass')
    L.append('\t{')
    for c in CLASSES:
        L.append('\t\tPLAYERBOT_ISHOP3_CLASS_%s,' % c)
    L.append('\t};')
    L.append('')
    L.append('\tconst char* const PLAYERBOT_ISHOP3_NEED_NAMES[PLAYERBOT_ISHOP3_NEED_COUNT] = {')
    for i in range(0, len(NEEDS), 6):
        L.append('\t\t' + ' '.join('"%s",' % n[0].lower() for n in NEEDS[i:i + 6]))
    L.append('\t};')
    L.append('\tconst BYTE PLAYERBOT_ISHOP3_NEED_CLASS[PLAYERBOT_ISHOP3_NEED_COUNT] = {')
    for i in range(0, len(NEEDS), 6):
        L.append('\t\t' + ' '.join('PLAYERBOT_ISHOP3_CLASS_%s,' % n[1] for n in NEEDS[i:i + 6]))
    L.append('\t};')
    L.append('')
    L.append('\t// One item of the catalogue (sorted by vnum): its need, the hold / day caps (0: none), the lowest level of its')
    L.append('\t// lines, the lines a bot may buy and all its lines, the currencies (1 Smocze Monety, 2 Smocze Znaki).')
    L.append('\tstruct TPlayerBotIshop3CatalogueRow')
    L.append('\t{')
    L.append('\t\tDWORD dwVnum;')
    L.append('\t\tBYTE bNeed;')
    L.append('\t\tshort sHold;')
    L.append('\t\tshort sDay;')
    L.append('\t\tBYTE bMinLevel;')
    L.append('\t\tBYTE bLines;')
    L.append('\t\tBYTE bAllLines;')
    L.append('\t\tBYTE bCurrencies;')
    L.append('\t};')
    L.append('')
    L.append('\tconst TPlayerBotIshop3CatalogueRow PLAYERBOT_ISHOP3_CATALOGUE[] = {')
    for (vnum, need, hold, day, minlv, nel, nall, cur, name, reason, el) in out_rows:
        L.append('\t\t{ %6d, PLAYERBOT_ISHOP3_NEED_%s, %d, %d, %d, %d, %d, %d },\t// %s - %s' % (
            vnum, need, hold, day, minlv, min(nel, 255), min(nall, 255), cur, ascii_name(name), ascii_name(reason)))
    L.append('\t};')
    L.append('\tconst size_t PLAYERBOT_ISHOP3_CATALOGUE_SIZE = sizeof(PLAYERBOT_ISHOP3_CATALOGUE) / sizeof(PLAYERBOT_ISHOP3_CATALOGUE[0]);')
    L.append('')
    L.append('\t// The chest lines (vnum 0 in the view): the line, the chest, its need.')
    L.append('\tstruct TPlayerBotIshop3CatalogueChest')
    L.append('\t{')
    L.append('\t\tDWORD dwLine;')
    L.append('\t\tDWORD dwChest;')
    L.append('\t\tBYTE bNeed;')
    L.append('\t};')
    L.append('\tconst TPlayerBotIshop3CatalogueChest PLAYERBOT_ISHOP3_CATALOGUE_CHESTS[] = {')
    for (line, chest, need, pr, count, name, reason) in chest_rows:
        L.append('\t\t{ %6d, %3d, PLAYERBOT_ISHOP3_NEED_%s },\t// %s x%d, %d - %s' % (
            line, chest, need, ascii_name(name) or 'chest %d' % chest, count, pr, ascii_name(reason)))
    L.append('\t};')
    L.append('\tconst size_t PLAYERBOT_ISHOP3_CATALOGUE_CHEST_COUNT = sizeof(PLAYERBOT_ISHOP3_CATALOGUE_CHESTS) / '
             'sizeof(PLAYERBOT_ISHOP3_CATALOGUE_CHESTS[0]);')
    L.append('\tconst unsigned int PLAYERBOT_ISHOP3_CATALOGUE_ALL_LINES = %d;\t// every line of the view at the dump' % len(rows))
    L.append('}')
    L.append('')
    L.append('#endif')
    with open(OUT, 'w', encoding='ascii') as f:
        f.write('\n'.join(L) + '\n')

    print('catalogue: %d lines, %d items, %d chest lines -> %s' % (len(rows), len(out_rows), len(chest_rows),
                                                                   os.path.relpath(OUT, REPO)))
    print('by class (items+chests): ' + ', '.join('%s %d' % (c, cnt[c]) for c in CLASSES))
    print('bot lines by class:      ' + ', '.join('%s %d' % (c, lines_by_class[c]) for c in CLASSES))
    print('by need: ' + ', '.join('%s %d' % (n, need_cnt[n]) for n, _, _ in NEEDS if need_cnt[n]))
    if unknown:
        print('UNKNOWN (classified NEVER until decided - add them to EXPLICIT):')
        for vnum, name, reason in unknown:
            print('  %6d %s - %s' % (vnum, name, reason))
    if a.report:
        for (vnum, need, hold, day, minlv, nel, nall, cur, name, reason, el) in out_rows:
            print('%6d %-16s %-8s hold=%-3d day=%-3d lv=%-3d lines=%d/%d %-36s %s' % (
                vnum, need, CLASS_OF[need], hold, day, minlv, nel, nall, name[:36], reason))
        for c in chest_rows:
            print('chest line %d chest %d %s %s - %s' % (c[0], c[1], c[2], c[5], c[6]))
    return 1 if unknown else 0


if __name__ == '__main__':
    sys.exit(main())
