# -*- coding: utf-8 -*-
# MT2009_PLUS_ALCHEMY_WIKI_NAMES_V1 (the owner, 4 November 2026: "Nazwy bonusow alchemii maja byc dokladnie takie same
# jak na polskiej wiki. Bonusy ogolnie sa dobre, tylko nazwy sa do poprawy.") - the Dragon Stone (Smocze Kamienie)
# bonus lines in the pl-wiki's words. Only the names (and the wiki's "value first" form: "6% Odpornosc na Mrok",
# "+240 Obrona", "+2.400 Max. PZ") - the values are the server's dragon_soul_table, unchanged.
#
# Source: the pl-wiki stone pages (Smoczy Diament / Rubin / Jadeit / Szafir / Granat / Onyks / Ametyst, action=raw,
# 4 Nov 2026): the bonus lists at the top of each page and the bonus tables of every class (Smoczy Kamien/Layout:
# Bonus1/Bonus2/Bonus3 + the "dodatkowe bonusy" column). The 1st (basic) bonus: the page "Alchemia Smoczych Kamieni"
# names it in full ("+16 Witalnosc", "+800 PE", "+2.400 PZ" - the stone tables abbreviate it to WIT/INT/SIL/ZRE).
# The wiki's own alchemy names differ from its item bonus names ("Szansa na Unik Strzaly" here, "Szansa na uniknięcie
# Strzaly" on the item pages "Bonusy"), so these names are the dragon stone tooltip's own: every other item keeps the
# shared names (locale_game.txt TOOLTIP_*, localeinfo_point.AFFECT_DICT).
#
# The client: locale/pl/locale_game.txt (locale pack) gets one line per bonus, DS_APPLY_<POINT> (DS_APPLY_BASIC_<POINT>:
# the stone's 1st bonus where the wiki names it otherwise - Jadeit's "PE" / Granat's "PZ" are MAX_SP / MAX_HP like
# Granat's / Jadeit's additional "Max. PE" / "Max. PZ"). root localeinfo_point.GetDragonSoulApplyString maps
# <POINT> to player.POINT_<POINT> (DS_FALLBACK_POINTS there for the points the player module has no name for) and
# formats "%d" with the value, "%s" with the value grouped by dots (the wiki's "2.400"). A bonus without a line here
# (the mt2009 bonus mode's race bonuses - the wiki's alchemy has none) keeps its shared name.
# Order of the list = the wiki's order per stone. The wiki's Likan lines ("Silny przeciwko Likanom", "Odpornosc na
# Atak Likanow") are left out: no Likan class here, no dragon_soul_table line and no player.POINT_ for them.
NAMES = [
    # Smoczy Diament: Inteligencja (INT); Odpornosc na Lod (od Antycznego); Sila Lodu (od Mitycznego)
    ('IQ', u'+%d Inteligencja'),
    ('RESIST_ICE', u'%d%% Odporność na Lód'),
    ('ENCHANT_ICE', u'%d%% Siła Lodu'),
    ('SKILL_DAMAGE_BONUS', u'%d%% Obrażenia Umiejętności'),
    ('SKILL_DEFEND_BONUS', u'%d%% Odporność na Obrażenia Umiejętności'),
    ('MAGIC_DEF_GRADE_BONUS', u'+%s Magiczna Obrona'),
    ('MAGIC_ATT_GRADE_BONUS', u'+%s Wartość Magicznego Ataku'),
    # Smoczy Rubin: Sila (SIL); Odpornosc na Ogien; Sila Ognia
    ('ST', u'+%d Siła'),
    ('RESIST_FIRE', u'%d%% Odporność na Ogień'),
    ('ENCHANT_FIRE', u'%d%% Siła Ognia'),
    ('NORMAL_HIT_DAMAGE_BONUS', u'%d%% Średnie Obrażenia'),
    ('NORMAL_HIT_DEFEND_BONUS', u'%d%% Odporność na Obrażenia'),
    ('DEF_GRADE_BONUS', u'+%s Obrona'),
    ('ATT_GRADE_BONUS', u'+%s Wartość Ataku'),
    # Smoczy Jadeit: Punkty Energii (PE); Odpornosc na Wiatr; Sila Wiatru
    ('BASIC_MAX_SP', u'+%s PE'),
    ('RESIST_WIND', u'%d%% Odporność na Wiatr'),
    ('ENCHANT_WIND', u'%d%% Siła Wiatru'),
    ('MAX_HP', u'+%s Max. PŻ'),
    ('MAX_HP_PCT', u'%d%% Max. PŻ'),
    ('STEAL_HP', u'%d%% Obrażenia dodane do PŻ'),
    ('HP_REGEN', u'%d%% Regeneracja PŻ'),
    ('KILL_HP_RECOVERY', u'%d%% Szansa na odzyskanie PŻ'),
    # Smoczy Szafir: Zrecznosc (ZRE); Odpornosc na Ziemie; Sila Ziemi
    ('DX', u'+%d Zręczność'),
    ('RESIST_EARTH', u'%d%% Odporność na Ziemię'),
    ('ENCHANT_EARTH', u'%d%% Siła Ziemi'),
    ('ATTBONUS_WARRIOR', u'%d%% Silny przeciwko Wojownikom'),
    ('ATTBONUS_ASSASSIN', u'%d%% Silny przeciwko Ninja'),
    ('ATTBONUS_SURA', u'%d%% Silny przeciwko Sura'),
    ('ATTBONUS_SHAMAN', u'%d%% Silny przeciwko Szamanom'),
    ('RESIST_WARRIOR', u'%d%% Odporność na Wojowników'),
    ('RESIST_ASSASSIN', u'%d%% Odporność na Ninja'),
    ('RESIST_SURA', u'%d%% Odporność na Sura'),
    ('RESIST_SHAMAN', u'%d%% Odporność na Szamanów'),
    # Smoczy Granat: Punkty Zycia (PZ); Odpornosc na Blyskawice; Sila Blyskawic
    ('BASIC_MAX_HP', u'+%s PŻ'),
    ('RESIST_ELEC', u'%d%% Odporność na Błyskawice'),
    ('ENCHANT_ELECT', u'%d%% Siła Błyskawic'),
    ('MAX_SP', u'+%s Max. PE'),
    ('MAX_SP_PCT', u'%d%% Max. PE'),
    ('SP_REGEN', u'%d%% Regeneracja PE'),
    ('STEAL_SP', u'%d%% Obrażenia dodane do PE'),
    ('KILL_SP_RECOVER', u'%d%% Szansa na odzyskanie PE'),
    # Smoczy Onyks: Witalnosc (WIT); Odpornosc na Mrok; Sila Mroku
    ('HT', u'+%d Witalność'),
    ('RESIST_DARK', u'%d%% Odporność na Mrok'),
    ('ENCHANT_DARK', u'%d%% Siła Mroku'),
    ('DODGE', u'%d%% Szansa na Unik Strzały'),
    ('RESIST_CRITICAL', u'%d%% Odporność na Cios Krytyczny'),
    ('RESIST_PENETRATE', u'%d%% Odporność na Przeszywający Cios'),
    ('REFLECT_MELEE', u'%d%% Szansa na Odbicie Ciosu'),
    ('BLOCK', u'%d%% Szansa na Blok Ciosu'),
    # Smoczy Ametyst: Sila w walce z diablami; Precyzja (od Antycznego); Wola SungMa (WIT) (od Mitycznego)
    ('ATTBONUS_DEVIL', u'%d%% Siła w walce z diabłami'),
    ('HIT_PCT', u'+%d Precyzja'),
    ('SUNGMA_HP', u'+%d Wola SungMa (WIT)'),
    ('SUNGMA_STR', u'+%d Wola SungMa (SIŁA)'),
    ('SUNGMA_MOVE', u'+%d Wola SungMa (ODP)'),
    ('SUNGMA_IMMUNE', u'+%d Wola SungMa (INT)'),
    ('ATTBONUS_STONE', u'%d%% Siła w walce z kamieniami Metin'),
]

PREFIX = 'DS_APPLY_'
FORBIDDEN = ('metin2', 'gameforge', 'oficjaln')


def lines():
    """the locale_game.txt lines (cp1250 bytes, CRLF like the file; the 3rd, empty column keeps the CR out of the text)"""
    out = []
    for key, text in NAMES:
        assert not any(w in text.lower() for w in FORBIDDEN), text
        out.append((PREFIX + key + u'\t' + text + u'\t\r\n').encode('cp1250'))
    return out


def patch_locale_game(data):
    """locale/pl/locale_game.txt with this step's lines at its end - any DS_APPLY_ line of an earlier run replaced
    (idempotent); every other line byte for byte"""
    keys = set(k for k, t in NAMES)
    assert len(keys) == len(NAMES)
    body = data
    kept = []
    for l in body.splitlines(True):
        if l.startswith(PREFIX.encode('ascii')):
            continue
        kept.append(l)
    body = b''.join(kept)
    if body and not body.endswith((b'\n', b'\r')):
        body += b'\r\n'
    return body + b''.join(lines())


def parse(data):
    """{key: text} of the DS_APPLY_ lines of a locale_game.txt (as the client's LoadLocaleFile reads them)"""
    out = {}
    for l in data.split(b'\n'):
        if l.startswith(PREFIX.encode('ascii')):
            t = l.split(b'\t')
            out[t[0].decode('ascii')[len(PREFIX):]] = t[1].rstrip(b'\r').decode('cp1250') if len(t) > 1 else u''
    return out
