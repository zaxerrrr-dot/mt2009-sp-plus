#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MT2009_PLUS_GROWTH_PET_V1 - the root pack's side of System Zwierzat Domowych: writes, from tools/pety/pety_data.py
(the feature's one data source, the server's tables come from it too) and the texts below,

  client-patches/client-2.0.30/root/petdata.py     stages, evolution materials, species (egg / seal / mobs), skills
                                                   (name, icon, kind, cooldown, unit, book), potential skills, prices
  client-patches/client-2.0.30/root/petlocale.py   every Polish text of the pet windows (uipetinfo.py, uitooltip.py,
                                                   uiinventory.py, uiscript/pet*.py)

Both are plain ASCII: the CP1250 bytes of the Polish letters are \\x escapes, so the modules need no coding cookie and
pass tools/uicheck/verify_root_encoding.py on any client. Python 2.7 (the client's) and 3 read them alike.

    python3 <repo>/client-patches/client-2.0.30/tools/pety/gen_pety_root.py [--check]

--check: exit 1 when a written file would change (pety_data.py changed without a new run) - verify_pety.py runs it.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', 'root'))
sys.path.insert(0, os.path.join(REPO, 'tools', 'pety'))
import pety_data as D  # noqa: E402

UNIT_OF = {}

# ----------------------------------------------------------------------------------------------------------------------
# The texts (Polish, as the players read them). Key -> text; a %-format where the code fills in values.
TEXTS = [
    # the main window
    ('TITLE', u'Zwierzak'),
    ('TAB_INFO', u'Informacje'),
    ('TAB_ATTR', u'Zmiana typu (Zaczaruj zwierzaka)'),
    ('TAB_REVIVE', u'Wskrzeszanie (Boska Odżywka)'),
    # MT2009_PLUS_PET_WINDOW_LAYOUT_V2: the hover lines of the skill (book) and potential (gem) icons in the bottom row
    ('SKILL_MENU_TIP_1', u'Umiejętności zwierzaka (3 sloty)'),
    ('SKILL_MENU_TIP_2', u'Księgę umiejętności przeciągnij na wolny slot.'),
    ('SKILL_MENU_TIP_3', u'Slot z krzyżykiem jest jeszcze zamknięty.'),
    ('POTENTIAL_MENU_TIP_1', u'Umiejętności potencjału (tylko czempion, 2 sloty)'),
    ('POTENTIAL_MENU_TIP_2', u'Jajo zwierzaka przeciągnij na slot albo kliknij „Potencjał”.'),
    ('CLOSE', u'Zamknij'),
    ('LEVEL', u'Poziom'),
    ('CHAMPION_LEVEL', u'Poz. czempiona'),
    ('EXP', u'Doświadczenie'),
    ('CHAMPION_EXP', u'PD czempiona'),
    ('AGE', u'Wiek'),
    ('LIFE', u'Czas trwania'),
    ('FEED_LIFE_BUTTON', u'Nakarm'),
    ('FEED_EVOL_BUTTON', u'Rozwój'),
    ('FEED_EXP_BUTTON', u'Przedmiot EXP'),
    ('ABILITIES', u'Bonusy'),
    ('CHAMPION_ABILITIES', u'Bonusy czempiona'),
    ('HP', u'PŻ'),
    ('DEF', u'Obrona'),
    ('SP', u'PE'),
    ('RES', u'Wola SungMa (ODP)'),
    ('BLOCK_PEN', u'Przebicie bloku'),
    ('PRECISION', u'Precyzja'),
    ('BTN_NORMAL', u'Zwierzak'),
    ('BTN_CHAMPION', u'Czempion'),
    ('BTN_POTENTIAL', u'Potencjał'),
    ('BTN_NORMAL_TIP', u'Poziom, doświadczenie i bonusy zwierzaka'),
    ('BTN_CHAMPION_TIP', u'Poziom czempiona, jego doświadczenie i bonusy'),
    ('BTN_POTENTIAL_TIP', u'Umiejętności potencjału (z jaj zwierzaków)'),
    ('DETERMINE_TIP', u'Sfera losu: pokazuje typ zwierzaka (zużywa Sferę Losu Zwierzaka)'),
    ('SKILLS', u'Umiejętności'),
    ('POTENTIAL_SKILLS', u'Umiejętności potencjału'),
    ('NO_PET', u'Brak przywołanego zwierzaka'),
    ('NEED_SUMMON', u'Najpierw przywołaj zwierzaka (prawy przycisk myszy na jego pieczęci).'),
    ('NOT_CHAMPION', u'Zwierzak nie jest jeszcze czempionem (stopień „Przebudzony”).'),
    ('STAGE_TYPE', u'%s - typ: %s'),
    ('LIFE_VALUE', u'%s / %s'),
    ('PERCENT', u'+%s%%'),
    ('EXP_MOB', u'PD z potworów: %s / %s'),
    ('EXP_ITEM', u'PD z przedmiotów: %s / %s'),
    ('EXP_TOTAL', u'Razem: %.2f%%'),
    ('EXP_FULL', u'Pełne doświadczenie - czas na rozwój.'),
    ('MINI_TIP', u'%s - poziom %d (kliknij: okno zwierzaka)'),
    ('MINI_TIP_CHAMPION', u'%s - poziom %d, czempion %d (kliknij: okno zwierzaka)'),
    # durations
    ('DAYS', u'%d dni'),
    # MT2009_PLUS_PET_WINDOW_LAYOUT_V3: the window's age and life as the official one shows them ("14d", "747 / 768 godz.")
    ('AGE_SHORT', u'%dd'),
    ('LIFE_HOURS', u'%d / %d godz.'),
    ('DAY_ONE', u'1 dzień'),
    ('TIME_D', u'%d d.'),
    ('TIME_H', u'%d godz.'),
    ('TIME_M', u'%d min.'),
    ('TIME_S', u'%d s'),
    ('YANG', u'%s Yang'),
    # the feed window
    ('FEED_TITLE_LIFE', u'Nakarm zwierzaka'),
    ('FEED_TITLE_EXP', u'Przedmiot EXP'),
    ('FEED_TITLE_EVOL', u'Rozwój zwierzaka'),
    ('FEED_BUTTON', u'Nakarm'),
    ('EXP_BUTTON', u'Poświęć'),
    ('EVOL_BUTTON', u'Rozwój'),
    ('FEED_HINT_LIFE', u'Jaja i pieczęcie innych zwierzaków odnawiają czas trwania.'),
    ('FEED_HINT_EXP', u'Broń, zbroja, Smakołyk i Smakołyk+ dają PD przedmiotu.'),
    ('FEED_WRONG_LIFE', u'Tu możesz dać tylko jajo albo pieczęć innego zwierzaka.'),
    ('FEED_WRONG_EXP', u'Tu możesz poświęcić tylko broń, zbroję, Smakołyk albo Smakołyk+.'),
    ('FEED_ACTIVE_PET', u'Nie możesz nakarmić zwierzaka nim samym.'),
    ('FEED_SPLIT', u'Przeciągnij cały stos przedmiotów.'),
    ('FEED_FULL', u'Okno jest pełne.'),
    ('FEED_ATTR_Q1', u'Ten przedmiot ma %d bonusy - poświęcony zniknie na zawsze.'),
    ('FEED_ATTR_Q2', u'Na pewno chcesz go poświęcić?'),
    ('FEED_EMPTY', u'Najpierw włóż przedmioty do okna (prawy przycisk myszy w ekwipunku).'),
    ('FEED_FAIL', u'Zwierzak nie przyjął tych przedmiotów.'),
    ('EVOL_TO', u'Rozwój do stopnia: %s'),
    ('EVOL_HAVE', u'Masz: %d / %d'),
    ('EVOL_MISSING', u'Brakuje materiałów do rozwoju.'),
    ('EVOL_MAX', u'Zwierzak osiągnął najwyższy stopień.'),
    ('EVOL_NEED_LEVEL', u'Rozwój wymaga poziomu %d i pełnego doświadczenia.'),
    ('EVOL_NEED_CHAMPION', u'Rozwój wymaga poziomu czempiona %d i pełnego doświadczenia.'),
    ('EVOL_NEED_EXP', u'Zwierzak musi mieć pełne doświadczenie (z potworów i z przedmiotów).'),
    ('EVOL_Q', u'Rozwinąć zwierzaka do stopnia „%s”? Materiały znikną.'),
    ('EVOL_OK', u'Zwierzak się rozwinął!'),
    # hatching / renaming
    ('HATCH_TITLE', u'Wykluwanie'),
    ('HATCH_NAME', u'Imię zwierzaka'),
    ('HATCH_BUTTON', u'Wykluj'),
    ('HATCH_MONEY', u'Koszt: %s Yang'),
    ('HATCH_Q', u'Wykluć zwierzaka o imieniu „%s”?'),
    ('HATCH_FAIL_NAME', u'Tego imienia nie można użyć - wybierz inne.'),
    ('HATCH_FAIL_TIME', u'To jajo straciło ważność.'),
    ('NAME_LEN', u'Imię musi mieć od 4 do 20 znaków.'),
    ('NAME_CHARS', u'Imię może zawierać tylko litery i cyfry.'),
    ('NOT_ENOUGH_MONEY', u'Masz za mało Yang.'),
    ('RENAME_TITLE', u'Zmiana imienia'),
    ('RENAME_BUTTON', u'Zmień imię'),
    ('RENAME_Q', u'Zmienić imię zwierzaka na „%s”?'),
    ('RENAME_FAIL', u'Tego imienia nie można użyć - wybierz inne.'),
    ('WINDOW_BUSY', u'Zamknij najpierw handel, sklep i magazyn.'),
    ('HATCH_BUSY', u'Najpierw zamknij okno wykluwania zwierzaka.'),
    # skills
    ('SKILL_LEARN_Q', u'Nauczyć zwierzaka umiejętności „%s”? Księga zniknie.'),
    ('SKILL_UPGRADE_Q1', u'Podnieść poziom umiejętności „%s” do %d?'),
    ('SKILL_UPGRADE_Q2', u'Koszt: %s Yang'),
    ('SKILL_DEL_Q1', u'Usunąć umiejętność „%s”?'),
    ('SKILL_DEL_Q2', u'Revertus Zwierza zniknie.'),
    ('SKILL_DEL_ALL_Q', u'Usunąć wszystkie umiejętności zwierzaka? Reverti Zwierza zniknie.'),
    ('SKILL_NEED_STAGE', u'Umiejętności można uczyć od stopnia „Bohaterski”.'),
    ('SKILL_SLOT_LOCKED', u'Ten slot umiejętności jest zamknięty.'),
    ('SKILL_DEL_EMPTY', u'Revertus Zwierza przeciągnij na wyuczoną umiejętność.'),
    ('SKILL_KNOWN', u'Zwierzak zna już tę umiejętność.'),
    ('SKILL_BOOK_ONLY', u'Na slot umiejętności przeciągnij księgę umiejętności zwierzaka albo Revertus Zwierza.'),
    ('NEED_WINDOW_FOR_REVERTI', u'Otwórz okno zwierzaka, aby użyć tego przedmiotu.'),
    ('SKILL_KIND_PASSIVE', u'Umiejętność pasywna'),
    ('SKILL_KIND_AUTO', u'Umiejętność automatyczna'),
    ('SKILL_LEVEL', u'Poziom umiejętności: %d / %d'),
    ('SKILL_CUR', u'Teraz: %s'),
    ('SKILL_NEXT', u'Następny poziom: %s'),
    ('SKILL_CHANCE', u'Szansa aktywacji: %d%%'),
    ('SKILL_DURATION', u'Czas działania: %s s'),
    ('SKILL_COOLDOWN', u'Odnowienie: %s'),
    ('SKILL_COOLDOWN_LEFT', u'Gotowa za: %s'),
    ('SKILL_UPGRADE_HINT', u'Kliknij +, aby podnieść poziom (%s Yang).'),
    ('SKILL_BOOK_HINT', u'Przeciągnij księgę na wolny slot umiejętności w oknie zwierzaka.'),
    ('SKILL_VALUE_RANGE', u'%d - %d obrażeń'),
    ('SKILL_VALUE_HP', u'%s PŻ'),
    ('SKILL_VALUE_M', u'+%s m'),
    ('SKILL_VALUE_S', u'%s s'),
    ('SKILL_TRIGGER_10', u'Działa sama, gdy PŻ postaci spadną poniżej 20%.'),
    ('SKILL_TRIGGER_17', u'Działa sama, gdy PŻ postaci spadną poniżej 10%.'),
    ('SKILL_TRIGGER_18', u'Działa sama, gdy postać jest otruta, krwawi albo jest spowolniona.'),
    ('SKILL_TRIGGER_23', u'Działa sama w czasie walki („Bezszelestny chód”).'),
    # the potential window
    ('POT_TITLE', u'Potencjał'),
    ('POT_EMPTY', u'Przeciągnij tu jajo zwierzaka: zwierzak dostanie losową umiejętność jego gatunku.'),
    ('POT_LOCKED', u'Ten slot otwiera się od poziomu czempiona %d.'),
    ('POT_REMOVE_Q', u'Wyjąć jajo z potencjału? Jajo i umiejętność przepadną.'),
    ('POT_REMOVE_HINT', u'Prawy przycisk myszy: wyjmij jajo (przepada).'),
    ('POT_TIME_LEFT', u'Pozostało: %s'),
    ('POT_EGG_ONLY', u'Tu możesz włożyć tylko jajo zwierzaka.'),
    ('POT_FAIL', u'Nie udało się dodać umiejętności potencjału.'),
    ('POT_OK', u'Zwierzak zyskał umiejętność potencjału.'),
    ('POT_SKILL', u'Umiejętność potencjału: %s (poz. %d)'),
    ('POT_FROM_EGG', u'Z jaja: %s'),
    # the attribute (type) change page
    ('ATTR_TITLE', u'Zaczaruj zwierzaka'),
    ('ATTR_PET', u'Zwierzak'),
    ('ATTR_ITEM', u'Zaczaruj zwierzaka'),
    ('ATTR_RESULT', u'Wynik'),
    ('ATTR_DETERMINE_TITLE', u'Typ zwierzaka'),
    ('ATTR_BUTTON', u'Zaczaruj'),
    ('ATTR_CLEAR', u'Wyczyść'),
    ('ATTR_Q', u'Zaczarować zwierzaka? Typ (1-8), czas trwania i bonusy zostaną policzone od nowa.'),
    ('ATTR_SUMMONED', u'Odwołaj zwierzaka, zanim go zaczarujesz.'),
    ('ATTR_WRONG', u'Tu pasuje tylko pieczęć zwierzaka i Zaczaruj zwierzaka.'),
    ('DETERMINE_NO_ITEM', u'Potrzebujesz Sfery Losu Zwierzaka (Handlarka Różności).'),
    ('DETERMINE_RESULT', u'Typ zwierzaka: %s'),
    ('TYPE_UNKNOWN', u'nieznany'),
    # the revive page
    ('REVIVE_TITLE', u'Wskrzeszanie zwierzaka'),
    ('REVIVE_TARGET', u'Martwy zwierzak'),
    ('REVIVE_RESULT', u'Wynik'),
    ('REVIVE_AGE', u'Wiek'),
    ('REVIVE_MATERIAL', u'Boska Odżywka'),
    ('REVIVE_COUNT', u'%d / %d'),
    ('REVIVE_BUTTON', u'Wskrześ'),
    ('REVIVE_CANCEL', u'Wyczyść'),
    ('REVIVE_Q', u'Wskrzesić zwierzaka „%s”? Zużyjesz %d x Boska Odżywka.'),
    ('REVIVE_EMPTY', u'Najpierw włóż pieczęć martwego zwierzaka.'),
    ('REVIVE_NOT_ENOUGH', u'Za mało Boskiej Odżywki.'),
    ('REVIVE_ALIVE', u'Ten zwierzak żyje - wskrzesić można tylko martwego.'),
    ('REVIVE_WRONG', u'Tu pasuje tylko pieczęć martwego zwierzaka i Boska Odżywka.'),
    ('REVIVE_OK', u'Zwierzak wrócił do życia!'),
    ('REVIVE_FAIL', u'Wskrzeszenie się nie powiodło.'),
    ('REVIVE_DESC_1', u'Boska Odżywka wskrzesza martwego zwierzaka:'),
    ('REVIVE_DESC_2', u'czas trwania wraca do 100%, bonusy i umiejętności'),
    ('REVIVE_DESC_3', u'zostają, a zwierzak zachowuje 80% swojego wieku.'),
    ('REVIVE_DESC_4', u'Potrzeba 1 Boskiej Odżywki na każde 10 dni wieku.'),
    ('REVIVE_DESC_5', u'Pieczęć martwego zwierzaka włóż w lewy slot,'),
    ('REVIVE_DESC_6', u'Boską Odżywkę w sloty poniżej (albo prawy przycisk'),
    ('REVIVE_DESC_7', u'myszy w ekwipunku przy otwartej zakładce).'),
    ('REVIVE_DESC_8', u'Odżywka przeciągnięta na pieczęć też wskrzesza,'),
    ('REVIVE_DESC_9', u'ale tylko do 50% czasu trwania i z wiekiem od nowa.'),
    # item tooltips
    ('TT_LEVEL', u'Poziom %d'),
    ('TT_LEVEL_CHAMPION', u'Poziom %d, poziom czempiona %d'),
    ('TT_STAGE', u'Stopień: %s'),
    ('TT_AGE', u'Wiek: %s'),
    ('TT_LIFE', u'Czas trwania: %s / %s'),
    ('TT_LIFE_MAX', u'Czas trwania: %s'),
    ('TT_DEAD', u'Zwierzak nie żyje - wskrześ go (Odżywka albo Boska Odżywka).'),
    ('TT_TYPE', u'Typ: %s'),
    ('TT_SLOTS', u'Sloty umiejętności: %d'),
    ('TT_SKILL', u'%s (poz. %d)'),
    ('TT_SUMMONED', u'Przywołany'),
    ('TT_EGG_HATCH', u'Wykluwa: %s'),
    ('TT_EGG_TIME', u'Jajo ważne jeszcze: %s'),
    ('TT_EGG_EXPIRED', u'Jajo straciło ważność.'),
    ('TT_EGG_POTENTIAL', u'Potencjał czempiona: %s'),
    ('TT_BAG_EMPTY', u'Klatka jest pusta.'),
    ('TT_BAG_PET', u'W klatce: %s'),
    ('TT_BAG_TIME', u'Klatka ważna jeszcze: %s'),
    ('TT_BAG_EXPIRED', u'Klatka straciła ważność - przełóż zwierzaka do nowej klatki.'),
    ('TT_NO_DATA', u'Dane zwierzaka pojawią się po chwili.'),
    ('TT_BOOK_SKILL', u'Uczy umiejętności: %s'),
    ('KEY_LABEL', u'Zwierzak domowy'),
]

# Pet types 1..8 (pl item "Sfera Losu Zwierzaka"; the descriptions of the pl table)
TYPES = {
    1: (u'Niezdarny', u'Niezbyt silny.'), 2: (u'Ciekawski', u''), 3: (u'Pełen werwy', u'Przeciętnie silny.'),
    4: (u'Odważny', u''), 5: (u'Szalenie odważny', u'Silny.'), 6: (u'Legendarny', u'Silny.'),
    7: (u'Mityczny', u'Bardzo silny.'), 8: (u'Pryzmatyczny', u'Ekstremalnie silny.'),
}


def esc(text):
    """A Python 2/3 str literal of the CP1250 bytes of text, every non-ASCII byte as \\x.."""
    out = []
    for b in text.encode('cp1250'):
        c = chr(b)
        if c in "'\\":
            out.append('\\' + c)
        elif 32 <= b < 127:
            out.append(c)
        else:
            out.append('\\x%02x' % b)
    return "'" + ''.join(out) + "'"


HEADER = ('# MT2009_PLUS_GROWTH_PET_V1 - %s\n'
          '# GENERATED by client-patches/client-2.0.30/tools/pety/gen_pety_root.py from tools/pety/pety_data.py - do not\n'
          '# edit by hand (a new run overwrites it; verify_pety.py fails while it is out of date). ASCII only: the Polish\n'
          '# letters are CP1250 \\x escapes, as the client draws them.\n')


def petdata():
    L = [HEADER % 'System Zwierzat Domowych: the data the pet windows need (uipetinfo.py).', '']
    L.append('HATCH_PRICE = %d' % D.HATCH_PRICE)
    L.append('RENAME_PRICE = %d' % D.RENAME_PRICE)
    L.append('SKILL_UPGRADE_PRICE = %d' % D.SKILL_UPGRADE_PRICE)
    L.append('EGG_LIFE_SECONDS = %d' % D.EGG_LIFE_SECONDS)
    L.append('BAG_LIFE_SECONDS = %d' % D.BAG_LIFE_SECONDS)
    L.append('MAX_LEVEL = %d' % len(D.EXP))
    L.append('CHAMPION_MAX_LEVEL = %d' % len(D.CHAMPION_EXP))
    L.append('SKILL_LEVEL_MAX = 20')
    L.append('SKILL_OPEN_STAGE = 4')
    L.append('AGE_BONUS_MAX_DAYS = %d' % D.AGE_BONUS_MAX_DAYS)
    L.append('')
    L.append('# stage -> name (1 Mlody .. 6 Mocny)')
    L.append('STAGES = {')
    for k in sorted(D.STAGES):
        L.append('\t%d: %s,' % (k, esc(D.STAGES[k])))
    L.append('}')
    L.append('')
    L.append('# to stage -> (level needed - the champion level for stage 6, age days (not checked by the window), ((vnum, count), ...))')
    L.append('# stage 5 (Przebudzony) needs level %d, stage 6 champion level %d; both with full EXP' % (
        D.EVOLUTION[5][0], D.EVOLUTION[6][0]))
    L.append('EVOLUTION = {')
    for k in sorted(D.EVOLUTION):
        lv, age, mats = D.EVOLUTION[k]
        L.append('\t%d: (%d, %d, (%s)),' % (k, lv, age, ''.join('(%d, %d), ' % (m[0], m[1]) for m in mats)))
    L.append('}')
    L.append('')
    L.append('# seal vnum -> (species, egg vnum, pet name, (young mob, heroic mob, champion mob), max skill slots, max type)')
    L.append('SEALS = {')
    for s in D.SPECIES:
        L.append('\t%d: (%d, %d, %s, (%d, %d, %d), %d, %d),' % (s[2], s[0], s[1], esc(s[3]), s[5], s[6], s[7],
                                                                s[10][1], s[11]))
    L.append('}')
    L.append('# egg vnum -> seal vnum')
    L.append('EGGS = {')
    for s in D.SPECIES:
        L.append('\t%d: %d,' % (s[1], s[2]))
    L.append('}')
    L.append('')
    L.append("# skill -> (name, icon (d:/ymir work/ui/skill/pet/<icon>.sub), kind (1 passive, 2 auto), cooldown s, unit,")
    L.append("#           book vnum, description); unit of the server's values: '%10' tenths of a per cent, 'm10' tenths")
    L.append("#           of a metre, 'hp' hit points, 's10' tenths of a second, 'dmg' the minimum damage (max 1400)")
    L.append('SKILLS = {')
    for k in sorted(D.SKILLS):
        s = D.SKILLS[k]
        L.append('\t%d: (%s, %s, %d, %d, %s, %d, %s),' % (k, esc(s[0]), esc(s[1]), s[2], s[3], esc(s[6]), s[8],
                                                          esc(s[9])))
    L.append('}')
    L.append('BOOKS = {')
    for k in sorted(D.SKILLS):
        L.append('\t%d: %d,' % (D.SKILLS[k][8], k))
    L.append('}')
    L.append('# the activation chance (%%) of the auto skills by skill level 1..20 (shown when the exe gives none)')
    L.append('ACTIVATE = {')
    for k in sorted(D.ACTIVATE):
        L.append('\t%d: (%s),' % (k, ', '.join(str(v) for v in D.ACTIVATE[k])))
    L.append('}')
    L.append('FEATHER_MAX_DAMAGE = %d' % D.FEATHER_MAX_DAMAGE)
    L.append('')
    L.append('# species -> the potential skills an egg of it can give a champion pet')
    L.append('POTENTIAL = {')
    for k in sorted(D.POTENTIAL):
        L.append('\t%d: (%s,),' % (k, ', '.join(str(v) for v in D.POTENTIAL[k])))
    L.append('}')
    L.append('# (champion level from, potential skill level), the highest first')
    L.append('POTENTIAL_LEVEL = (%s)' % ''.join('(%d, %d), ' % p for p in D.POTENTIAL_LEVEL))
    L.append('POTENTIAL_SECOND_SLOT_LEVEL = 15')
    L.append('')
    L.append('# type -> (name, description) - the Sfera Losu Zwierzaka types')
    L.append('# MT2009_PLUS_PET_EXP_GUARD_V1: level -> (mob exp, item exp) the level needs (the server\'s table) - the window')
    L.append('# falls back on it when the exe hands 0xFFFFFFFF for the need')
    L.append('EXP = (%s)' % ''.join('(%d, %d), ' % (a, b) for a, b in D.EXP))
    L.append('CHAMPION_EXP = (%s)' % ''.join('(%d, %d), ' % (a, b) for a, b in D.CHAMPION_EXP))
    L.append('')
    L.append('TYPES = {')
    for k in sorted(TYPES):
        L.append('\t%d: (%s, %s),' % (k, esc(TYPES[k][0]), esc(TYPES[k][1])))
    L.append('}')
    L.append('')
    return '\n'.join(L)


def petlocale():
    L = [HEADER % 'System Zwierzat Domowych: every Polish text of the pet windows (uipetinfo.py & co.).', '']
    keys = set()
    for k, v in TEXTS:
        assert k not in keys, k
        keys.add(k)
        L.append('%s = %s' % (k, esc(v)))
    L.append('')
    L.append('')
    L.append('def T(key, default=None):')
    L.append('\t"""The text of key; a key this module lacks gives default (or the key) - never an AttributeError."""')
    L.append('\treturn globals().get(key, key if default is None else default)')
    L.append('')
    return '\n'.join(L)


def main():
    check = '--check' in sys.argv
    bad = []
    for name, text in (('petdata.py', petdata()), ('petlocale.py', petlocale())):
        path = os.path.join(ROOT, name)
        data = text.encode('ascii')
        old = open(path, 'rb').read() if os.path.exists(path) else None
        if old == data:
            print('%s: unchanged' % name)
            continue
        if check:
            bad.append(name)
            print('%s: OUT OF DATE (run gen_pety_root.py)' % name)
            continue
        open(path, 'wb').write(data)
        print('%s: written (%d bytes)' % (name, len(data)))
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
