"""MT2009_PLUS_ENV_EDITOR_V1: every setting of linux-port/docker/.env, described.

One list read by two programs:

* the advanced panel (app.py, page "Ustawienia serwera (.env)") draws the form
  from it and checks what the owner typed before it queues anything;
* the updater (linux-port/tools/env_apply.py, run by update.sh in its watch
  loop, the only part of the stack that holds the Docker socket) checks the
  same request again - it never trusts the panel - writes .env and recreates
  exactly the services named here.

Pure standard library on purpose: the updater image has python3 and nothing
else. test_env_schema.py fails when .env.example or docker-compose.yml gains
a variable this file does not describe, or when the services listed here
stop matching the ones docker-compose.yml passes the variable to.

Entry fields
------------
key, label, desc      the variable, a Polish name and a Polish description
section               one of SECTIONS (the page's cards)
type                  int | number | bool | enum | string | port | portrange |
                      address | host | url | path
default               the value .env.example ships (or compose's default)
services              compose services that must be recreated on a change
min / max / step      int and number
options               enum: [[value, label], ...]
pattern / hint        string: a regular expression the value must match
allow_empty           an empty value is valid (means "the default / auto")
secret                never shown: the page only says set / not set and
                      offers "ustaw nowe"
readonly              the panel shows it but cannot change it (readonly_reason)
dangerous             ports, addresses, things that can lock you out: the
                      page asks for an extra typed confirmation
build                 read only when the game image is built: written to
                      .env, applied by the next rebuild (update), no restart
note                  what a change does, when the services alone don't say
"""
import re

SCHEMA_VERSION = 1

SECTIONS = [
    {"id": "boty", "label": "Boty", "icon": "🤖",
     "desc": "Ile botów gra, jak wchodzą do świata, królestwa i drugi kanał."},
    {"id": "swiat", "label": "Świat i rates", "icon": "🌍",
     "desc": "Trudność, mnożniki świeżego świata, szanse eventów i dropu, poziom maksymalny."},
    {"id": "moduly", "label": "Moduły gry", "icon": "🧩",
     "desc": "Arezzo, Seon-Hae, alchemia, szarfy, Auto Łowy, Towarzysz, Dom Towarowy, Karty Potworów, zestawy startowe."},
    {"id": "siec", "label": "Sieć i porty", "icon": "🌐",
     "desc": "Adres serwera, porty gry, logowania, paneli i sklepu, adresy nasłuchu."},
    {"id": "panele", "label": "Panele i strona", "icon": "🖥",
     "desc": "Hasła i dostęp do paneli, nazwa serwera, rejestracja, adresy między panelami."},
    {"id": "klient", "label": "Klient gry", "icon": "💾",
     "desc": "Klient do pobrania: nazwa, adres wpisany w klienta, paczka źródłowa."},
    # Hidden from the page (the owner, 6 October: "Całą sekcję gra w przeglądarce usuń"); its keys
    # stay described for the schema test and are never written from the panel.
    {"id": "przegladarka", "label": "Gra w przeglądarce", "icon": "🕸", "hidden": True,
     "desc": "Eksperymentalny mostek WebSocket do gry przez przeglądarkę."},
    {"id": "baza", "label": "Baza danych", "icon": "🗄",
     "desc": "Hasła i użytkownik bazy, port dla narzędzi typu HeidiSQL, zabezpieczenia startu."},
    {"id": "aktualizacje", "label": "Aktualizacje", "icon": "⬆",
     "desc": "Sprawdzanie i instalowanie aktualizacji, katalogi aktualizatora."},
    {"id": "zaawansowane", "label": "Zaawansowane", "icon": "🛠",
     "desc": "Budowanie obrazu, tryb testowy, logi, znaczniki techniczne. Zwykle nie trzeba tu niczego zmieniać."},
]

SERVICE_LABELS = {
    "game": "Serwer gry",
    "playerbot-migrate": "Migrator botów",
    "mariadb": "Baza danych",
    "panel": "Panel klasyczny",
    "seban-panel": "Panel zaawansowany",
    "seban-collector": "Kolektor statystyk",
    "seban-item-grants": "Nadawanie przedmiotów",
    "itemshop": "ItemShop",
    "updater": "Aktualizator",
}

GAME = ["game", "playerbot-migrate"]
SEBAN = ["seban-collector", "seban-item-grants", "seban-panel"]
ALL_DB = ["game", "itemshop", "mariadb", "panel", "playerbot-migrate"] + SEBAN

_IPV4 = r"(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)"
_HOST = r"(?:" + _IPV4 + r"|[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)*)"
_URL = r"https?://[A-Za-z0-9._~:/?&=%+,;@!*()\[\]-]+"
_SECRET = r"[A-Za-z0-9._-]{1,120}"

BOOL = [["1", "włączone"], ["0", "wyłączone"]]


def _e(key, label, desc, section, type="string", default="", services=(), **kw):
    entry = {"key": key, "label": label, "desc": desc, "section": section, "type": type,
             "default": default, "services": list(services)}
    entry.update(kw)
    return entry


SCHEMA = [
    # ------------------------------------------------------------------ Boty
    _e("PLAYERBOT_AUTOSPAWN_COUNT", "Liczba botów",
       "Ilu botów gra na serwerze, dzielonych po równo na trzy królestwa. Najczęściej zmieniana wartość. "
       "350 to spokojny świat, 1000 i więcej wymaga mocniejszej maszyny (więcej botów = większe obciążenie procesora). "
       "Maksimum 2500. Przy włączonych indywidualnych liczbach dla królestw ta wartość jest pomijana.",
       "boty", "int", "350", ["game"], min=0, max=2500, step=10, featured=True),
    _e("PLAYERBOT_AUTOSPAWN_PER_KINGDOM", "Osobna liczba botów dla każdego królestwa",
       "Włączone: każde królestwo dostaje tyle botów, ile podasz w trzech polach poniżej (najwyżej 1500 na królestwo), "
       "a „Liczba botów” jest pomijana. Wyłączone: jedna liczba dzielona po równo.",
       "boty", "bool", "0", ["game"]),
    _e("PLAYERBOT_AUTOSPAWN_SHINSOO", "Boty w Shinsoo", "Liczba botów w Shinsoo (działa tylko przy osobnej liczbie dla królestw).",
       "boty", "int", "0", ["game"], min=0, max=1500),
    _e("PLAYERBOT_AUTOSPAWN_CHUNJO", "Boty w Chunjo", "Liczba botów w Chunjo (działa tylko przy osobnej liczbie dla królestw).",
       "boty", "int", "0", ["game"], min=0, max=1500),
    _e("PLAYERBOT_AUTOSPAWN_JINNO", "Boty w Jinno", "Liczba botów w Jinno (działa tylko przy osobnej liczbie dla królestw).",
       "boty", "int", "0", ["game"], min=0, max=1500),
    _e("M2_PLAYERBOT_KINGDOMS", "Boty we wszystkich królestwach",
       "Włączone: boty grają w Shinsoo, Chunjo i Jinno. Wyłączone: tylko Chunjo (boty pozostałych królestw zostają w bazie, ale nie wchodzą do gry).",
       "boty", "bool", "1", GAME),
    _e("PLAYERBOT_SPAWN_WINDOW_MINUTES", "Czas wpuszczania botów po starcie (min)",
       "Przez ile minut od startu serwera boty mają się logować. 1 = wszystkie naraz (tłok na placu), 10–15 = wchodzą stopniowo.",
       "boty", "int", "1", ["game"], min=1, max=180),
    _e("PLAYERBOT_LATE_JOINERS", "Dodatkowe boty dołączające później",
       "Ilu dodatkowych botów ma dołączać pojedynczo już w trakcie gry, ponad „Liczbę botów”. 0 = nikt.",
       "boty", "int", "0", ["game"], min=0, max=2500),
    _e("PLAYERBOT_LATE_JOIN_HOURS", "Czas dołączania późniejszych botów (godz.)",
       "W ciągu ilu godzin rozłożyć dołączanie dodatkowych botów (1–168).",
       "boty", "int", "24", ["game"], min=1, max=168),
    _e("M2_PLAYERBOT_START_HELD", "Boty czekają przy drzwiach po starcie",
       "Włączone: po starcie serwera w świecie nie ma ani jednego bota, dopóki nie wpuścisz ich przyciskiem w panelu (strona AI) albo w launcherze. "
       "Daje czas na ustawienie rates i respawnów.",
       "boty", "bool", "0", GAME),
    _e("PLAYERBOT_MEDAL_DROPPERS", "Boty-„dropki medali” (na królestwo)",
       "Ilu botów na każde królestwo, ponad liczbę botów, siedzi w Lochu Małp i farmi medale konne na sprzedaż. 0 = wyłączone.",
       "boty", "int", "0", ["game"], min=0, max=200),
    _e("PLAYERBOT_MEDAL_DROPPER_LEVEL", "Poziom „dropków medali”",
       "Na jakim poziomie zatrzymać dropki medali (18–120). Niższy poziom = lepszy drop medalu.",
       "boty", "int", "25", ["game"], min=18, max=120),
    _e("M2_PLAYERBOT_CH2", "Drugi kanał (CH2)",
       "Włączone: serwer uruchamia drugi kanał (~1 GB RAM więcej), część botów gra na CH2, a porty 13010–13012 są otwierane automatycznie. "
       "Sklepy stoją tylko na CH1.",
       "boty", "bool", "0", ["game", "panel"],
       note="Przy zapisie aktualizator sam dopasuje M2_CHANNELS i zakresy portów gry oraz zapisze moment zmiany."),
    _e("PLAYERBOT_CH2_SHARE", "Odsetek botów poza CH1 (%)",
       "Jaki procent botów gra poza CH1 (10–90): na CH2, a z włączonym CH3/CH4 – po równo na CH2–CH4. Boty ze straganami i tak zostają na CH1.",
       "boty", "int", "40", ["game"], min=10, max=90, step=5),
    # MT2009_PLUS_CH34_V1: the third and fourth channel, same principle as CH2.
    _e("M2_PLAYERBOT_CH3", "Trzeci kanał (CH3)",
       "Włączone: serwer uruchamia trzeci kanał – trzy kolejne rdzenie gry na własnych procesach (ok. 2,5–3 GB RAM więcej i od pół do jednego rdzenia CPU pod obciążeniem), "
       "część botów gra na CH3, a porty 13020–13022 są otwierane automatycznie. Sklepy i stragany stoją tylko na CH1 – boty, które mają coś do "
       "zrobienia przy straganach, przelogowują się na CH1. Działa tylko z włączonym CH2. Domyślnie wyłączone.",
       "boty", "bool", "0", ["game", "panel"],
       note="Uwaga: każdy kanał to osobne rdzenie (RAM/CPU). Przy zapisie aktualizator sam dopasuje M2_CHANNELS i zakresy portów gry."),
    _e("M2_PLAYERBOT_CH4", "Czwarty kanał (CH4)",
       "Włączone: serwer uruchamia czwarty kanał – kolejne trzy rdzenie gry (ok. 2,5–3 GB RAM więcej i od pół do jednego rdzenia CPU pod obciążeniem), "
       "porty 13030–13032. Zasady jak na CH2/CH3: sklepy tylko na CH1. Działa tylko z włączonymi CH2 i CH3. Domyślnie wyłączone.",
       "boty", "bool", "0", ["game", "panel"],
       note="Uwaga: każdy kanał to osobne rdzenie (RAM/CPU). CH1–CH4 razem to ok. 11 GB RAM na same rdzenie gry."),
    _e("M2_PLAYERBOT_HUMAN_NAMES", "Ludzkie nicki botów",
       "Włączone: boty dostają nicki przypominające graczy zamiast technicznych nazw.",
       "boty", "bool", "1", GAME),
    _e("M2_PLAYERBOT_WORLD_LAYOUT", "Układ świata na rdzeniach",
       "unified = wszystkie królestwa i cały front na jednym rdzeniu, więc boty Shinsoo i Jinno mogą rosnąć dalej niż 36 poziom (zalecane do ~1500 botów). "
       "split = trzy rdzenie, szybsze przy bardzo dużej liczbie botów, ale dwa królestwa nie mają gdzie rosnąć.",
       "boty", "enum", "unified", ["game"],
       options=[["unified", "unified – jeden rdzeń dla całego świata"], ["split", "split – każde królestwo na swoim rdzeniu"]]),
    _e("M2_PLAYERBOT_DISABLE_STUDENT_CHEST", "Boty bez Skrzyni Ucznia",
       "Włączone: nowe boty nie dostają Skrzyni Ucznia (integracja panelu Seban). Ogólny przełącznik skrzyni to „Skrzynia Ucznia” w Modułach.",
       "boty", "bool", "0", GAME),

    # ------------------------------------------------------------------ Świat
    _e("M2_DIFFICULTY", "Poziom trudności",
       "Czasy oczekiwania u Biologa, u Stajennego i na kolejną księgę oraz szanse wymian u NPC. "
       "easy = bez czekania, medium = 1/3 oryginału, hard = jak w oryginale, custom = wartości z pól poniżej. "
       "Panel klasyczny zmienia trudność od razu; ta wartość obowiązuje od startu.",
       "swiat", "enum", "easy", GAME,
       options=[["easy", "easy – bez czekania"], ["medium", "medium – 1/3 oryginalnych czasów"], ["hard", "hard – jak w oryginale"], ["custom", "custom – własne wartości poniżej"]]),
    _e("M2_BIOLOGIST_WAIT_HOURS", "Biolog: czekanie (godz.)", "Ile godzin czekać między oddaniami u Biologa. Działa przy trudności custom. Ułamki dozwolone (0.5 = pół godziny).",
       "swiat", "number", "0", GAME, min=0, max=168, step=0.5),
    _e("M2_HORSE_WAIT_HOURS", "Stajenny: czekanie (godz.)", "Ile godzin czekać u Stajennego (kucyk, księgi konia, treningi). Działa przy trudności custom.",
       "swiat", "number", "0", GAME, min=0, max=168, step=0.5),
    _e("M2_BOOK_WAIT_HOURS", "Księgi graczy: czekanie (godz.)",
       "Ile godzin gracz czeka między dwiema księgami tej samej umiejętności i między Kamieniami Duchowymi (te najwyżej 12 h). 0 = od razu. Działa przy trudności custom.",
       "swiat", "number", "0", GAME, min=0, max=168, step=0.5),
    _e("M2_BOT_BOOK_WAIT_HOURS", "Księgi botów: czekanie (godz.)", "To samo dla botów. 0 = boty czytają od razu. Działa przy trudności custom.",
       "swiat", "number", "0", GAME, min=0, max=168, step=0.5),
    _e("M2_EXCHANGE_DUST_CHANCE", "Szansa wymiany na Magiczny Pył (%)", "Szansa wymiany kamienia duszy na Magiczny Pył u Alchemika. 0 = jak w pakiecie (100%). Działa przy trudności custom.",
       "swiat", "int", "0", GAME, min=0, max=100),
    _e("M2_EXCHANGE_PARCHMENT_CHANCE", "Szansa wymiany na Pergamin (%)", "Szansa wymiany księgi umiejętności na Pergamin. 0 = jak w pakiecie (100%). Działa przy trudności custom.",
       "swiat", "int", "0", GAME, min=0, max=100),
    _e("M2_EXCHANGE_MATERIAL_CHANCE", "Szansa wymiany na Materiały Rzemieślnicze (%)", "Szansa wymiany ulepszacza na Materiały Rzemieślnicze u Dozorcy. 0 = jak w pakiecie (55%). Działa przy trudności custom.",
       "swiat", "int", "0", GAME, min=0, max=100),
    _e("M2_RATE_EXP", "Rate doświadczenia świeżego świata (%)",
       "Mnożnik doświadczenia w procentach (100 = jak w oryginale). Używany TYLKO przy pierwszym starcie nowego świata i po resecie świata; "
       "w działającym świecie rates zmienia się w „Gra i serwer → Raty”.",
       "swiat", "int", "100", GAME, min=1, max=10000, step=10),
    _e("M2_RATE_DROP", "Rate dropu świeżego świata (%)", "Mnożnik dropu przedmiotów, jak wyżej – tylko dla świeżego świata.",
       "swiat", "int", "100", GAME, min=1, max=10000, step=10),
    _e("M2_RATE_YANG", "Rate yang świeżego świata (%)",
       "Mnożnik yang, jak wyżej. UWAGA: ceny i boty są dopasowane do 100% – więcej oznacza inflację i przesadzone ceny.",
       "swiat", "int", "100", GAME, min=1, max=1000, step=10),
    _e("M2_MAX_LEVEL", "Maksymalny poziom postaci", "Najwyższy poziom postaci na serwerze (do 120). Panel klasyczny używa tej samej wartości przy ustawianiu poziomu.",
       "swiat", "int", "120", ["game", "panel"], min=1, max=120),
    _e("M2_MONSTER_HP", "Życie potworów",
       "Ile życia mają potwory, bossowie i Metiny: default = jak w grze (100%), easy = 80%, albo liczba 10–300 (procent). "
       "Panel klasyczny zmienia to od razu; ta wartość obowiązuje, gdy ją zmienisz.",
       "swiat", "string", "default", GAME, pattern=r"default|easy|[1-9]\d|[12]\d\d|300",
       hint="default, easy albo liczba od 10 do 300", suggestions=["default", "easy", "50", "150", "200"]),
    _e("M2_MOONLIGHT_CHEST_PERMILLE", "Szkatułka Blasku Księżyca z potworów (‰)",
       "Szansa w promilach (10 = 1%), że zabity potwór upuści Szkatułkę Blasku Księżyca. Działa w trakcie wydarzenia ustawionego w panelu. 0 wyłącza.",
       "swiat", "int", "10", ["game"], min=0, max=1000),
    _e("M2_MOONLIGHT_CHEST_STONE_PERMILLE", "Szkatułka Blasku Księżyca z Metinów (‰)", "To samo dla kamieni Metin (300 = 30%).",
       "swiat", "int", "300", ["game"], min=0, max=1000),
    _e("M2_BLESSING_SCROLL_STONE_PERMILLE", "Zwój Błogosławieństwa z Metinów (‰)",
       "Szansa na Zwój Błogosławieństwa z Metinów poziomu 15–99, w promilach (10 = 1%). Nie wypada postaci ponad 15 poziomów wyżej od kamienia. 0 wyłącza.",
       "swiat", "int", "10", ["game"], min=0, max=1000),
    _e("M2_DRAGON_COIN_STONE_PERMILLE", "Smocze Monety z Metinów (‰)", "Szansa w promilach na Smoczą Monetę z kamienia Metin (3 = 0,3%).",
       "swiat", "int", "3", ["game"], min=0, max=1000),
    _e("M2_DRAGON_COIN_BOSS_PERMILLE", "Smocze Monety z bossów (‰)", "Szansa w promilach na Smoczą Monetę z bossa (50 = 5%).",
       "swiat", "int", "50", ["game"], min=0, max=1000),
    _e("M2_DEFAULT_GAME_LANGUAGE", "Język nazw w grze (świeża instalacja)",
       "Język nazw przedmiotów, potworów i questów dla świeżego świata. Później przełącza się go przyciskiem w panelu (ten wybór ma pierwszeństwo).",
       "swiat", "enum", "en", [], options=[["pl", "polski"], ["en", "angielski"]],
       note="Czytane przy instalacji (instalator/launcher) – zmiana nie restartuje kontenerów."),

    # ------------------------------------------------------------------ Moduły
    _e("M2_AREZZO", "Moduł Arezzo",
       "Mapy i lochy z Arezzo: Dolina Cyklopów, Pustkowie Faraona, Zaczarowany Las, Biblioteka Wiedzy, Wzgórze Wukonga, Ruiny Skorpiona, Starożytna Dżungla "
       "oraz zestawy kostiumów w ItemShopie. Panel klasyczny przełącza go od razu.",
       "moduly", "bool", "0", GAME),
    _e("M2_SEONHAE", "Seon-Hae (6/7 bonus)", "NPC Seon-Hae w pierwszych wioskach dodaje 6. i 7. bonus. Panel klasyczny przełącza go od razu i ustawia czas oczekiwania.",
       "moduly", "bool", "0", GAME),
    _e("M2_TELEPORT_MAP", "Mapa teleportacji (TAB) – autor: Mur4s",
       "TAB otwiera mapę świata z 18 punktami, kliknięcie teleportuje za darmo (bez pierścienia). Wymaga klienta z mapą (uiteleportmap.py). "
       "Wyłączone: TAB działa jak dawniej (Slot 6), a serwer ignoruje mapę. Przełącza się od razu, bez restartu.",
       "moduly", "bool", "0", GAME),
    _e("M2_ALCHEMY", "Alchemia (Cor Draconis)",
       "Wyłączone: nie powstają nowe Cor Draconis (Metiny, bossowie, odłamki i wymiana u Alchemika). To, co gracze mają, zostaje. "
       "Panel przełącza to od razu; ta wartość działa przy starcie, gdy się zmieniła.",
       "moduly", "bool", "1", GAME),
    _e("M2_SASHES", "Szarfy", "Wyłączone: nie wypadają nowe szarfy (bossowie i ich skrzynie). To, co gracze mają, zostaje.",
       "moduly", "bool", "1", GAME),
    _e("M2_AUTOHUNT", "Auto Łowy", "Auto Łowy (klawisz K) dostępne na tym świecie.", "moduly", "bool", "1", GAME),
    _e("M2_AUTOHUNT_ITEM", "Auto Łowy tylko z przedmiotem",
       "Wyłączone: Auto Łowy dla każdego. Włączone: tylko po kupnie „Auto Łowy (8h)” w ItemShopie (czas liczy się tylko w grze).",
       "moduly", "bool", "0", GAME),
    _e("M2_SIDEKICK", "Towarzysz", "Towarzysz (list i okno P) dostępny na tym świecie.", "moduly", "bool", "1", GAME),
    _e("M2_FLEA_MARKET", "Dom Towarowy", "Dom Towarowy u Handlarki Rozmaitości w M1: oferty wszystkich sklepów offline w jednym oknie, zakup zdalny.",
       "moduly", "bool", "1", GAME),
    _e("M2_MONSTER_CARDS", "Karty Potworów", "System Kart Potworów (misje, karty, gwiazdki, bonusy zestawów). Wyłączone: karty nic nie robią, postęp zostaje w bazie.",
       "moduly", "bool", "1", GAME),
    _e("M2_STARTER_CHEST", "Skrzynia Ucznia",
       "Włączone: nowe postacie graczy i boty dostają Skrzynię Ucznia. Wyłączone: nikt jej nie dostaje, a boty tracą nieotwarte skrzynie z łańcucha (graczy nic nie rusza).",
       "moduly", "bool", "1", GAME),
    _e("M2_STARTER_KIT", "Zestaw startowy",
       "Co zakłada nowa postać gracza i nowy bot: default = nic ponad grę, medium = broń i zbroja poziomu 1 na +5, easy = cały zestaw poziomu 1 na +9.",
       "moduly", "enum", "default", GAME,
       options=[["default", "default – jak w grze"], ["medium", "medium – broń i zbroja +5"], ["easy", "easy – cały zestaw +9"]]),

    # ------------------------------------------------------------------ Sieć
    _e("M2_PUBLIC_ADDRESS", "Publiczny adres serwera",
       "Adres, który gracze wpisują w kliencie: publiczne IP VPS albo domena. Na własnym komputerze puste (127.0.0.1). "
       "Zły adres = gracze zawisają na „łączenie z serwerem”.",
       "siec", "host", "", ["game", "panel"], allow_empty=True, dangerous=True),
    _e("M2_HOST_BIND_ADDRESS", "Adres nasłuchu portów gry",
       "Na jakim adresie komputera wystawić porty gry. 127.0.0.1 = tylko ten komputer, 0.0.0.0 = także gracze z sieci.",
       "siec", "address", "0.0.0.0", ["game", "itemshop", "panel", "seban-panel"], dangerous=True,
       suggestions=["0.0.0.0", "127.0.0.1"]),
    _e("M2_PANEL_BIND_ADDRESS", "Adres nasłuchu paneli",
       "To samo dla paneli i ItemShopu. 127.0.0.1 trzyma panele przy tym komputerze (dostęp np. przez tunel SSH).",
       "siec", "address", "0.0.0.0", ["itemshop", "panel", "seban-panel"], dangerous=True,
       suggestions=["0.0.0.0", "127.0.0.1"]),
    _e("M2_AUTH_PORT", "Port logowania", "Port serwera logowania. Zmień tylko, gdy 11000 jest zajęty – gracze muszą wtedy dostać nowy port.",
       "siec", "port", "11000", ["game", "panel"], dangerous=True),
    _e("M2_CHANNELS", "Liczba kanałów",
       "Ile kanałów gry uruchomić (każdy ok. 2,5–3 GB RAM). Boty grają na CH2–CH4 tylko z przełącznikami „Drugi/Trzeci/Czwarty kanał”, które same podnoszą tę liczbę. Aktualizator sam poszerzy zakresy portów.",
       "siec", "int", "1", ["game"], min=1, max=4, dangerous=True,
       note="Przy zapisie aktualizator dopasuje zakresy portów gry."),
    _e("M2_GAME_PORT_RANGE", "Zakres portów gry (host)",
       "Porty kanałów otwierane na tym komputerze. 13000-13002 = jeden kanał, 13000-13012 = dwa, 13000-13022 = trzy, 13000-13032 = cztery. Zwykle ustawiane automatycznie.",
       "siec", "portrange", "13000-13002", ["game", "panel"], dangerous=True),
    _e("M2_GAME_CONTAINER_PORT_RANGE", "Zakres portów gry (kontener)",
       "To samo po stronie kontenera – musi mieć tę samą długość co zakres hosta. Zwykle ustawiane automatycznie.",
       "siec", "portrange", "13000-13002", ["game"], dangerous=True),
    _e("M2_GAME_PORT_BASE", "Pierwszy port kanałów w kontenerze",
       "Port, od którego rdzenie gry liczą porty kanałów wewnątrz kontenera. 13000, chyba że na tym samym komputerze stoi drugi serwer.",
       "siec", "port", "13000", ["game"], dangerous=True),
    _e("M2_PANEL_PUBLIC_PORT", "Port panelu klasycznego", "Port panelu klasycznego (http://adres:7788). Tylko cyfry.",
       "siec", "port", "7788", ["game", "panel"] + SEBAN, dangerous=True),
    _e("M2_SEBAN_PANEL_PORT", "Port panelu zaawansowanego",
       "Port tego panelu (http://adres:7790). Po zmianie panel będzie dostępny pod nowym portem – zapamiętaj go.",
       "siec", "port", "7790", ["seban-panel"], dangerous=True),
    _e("M2_ITEMSHOP_PUBLIC_PORT", "Port ItemShopu", "Port sklepu z przedmiotami (ItemShop).",
       "siec", "port", "7791", ["game", "itemshop"], dangerous=True),
    _e("M2_MALL_URL", "Adres ItemShopu dla klienta",
       "Adres (host:port, bez http://), który gra podaje klientowi po otwarciu sklepu. Puste = publiczny adres i port ItemShopu.",
       "siec", "string", "", ["game"], allow_empty=True, pattern=_HOST + r":\d{1,5}", hint="np. 1.2.3.4:7791"),
    _e("M2_DB_PUBLISH_PORT", "Port bazy dla narzędzi (HeidiSQL)",
       "Port na 127.0.0.1, pod którym baza jest widoczna dla HeidiSQL/Navicata. Zmień, jeśli 3306 jest zajęty.",
       "siec", "port", "3306", ["mariadb", "game"], dangerous=True,
       note="Odtwarza bazę danych, a po niej serwer gry (gracze zostaną rozłączeni)."),
    _e("M2_PANEL_STATUS_PORTS", "Porty sprawdzane przez panel", "Porty, które panel klasyczny odpytuje, sprawdzając, czy serwer żyje (po przecinku).",
       "siec", "string", "11000,13000", ["panel"], pattern=r"\d{1,5}(,\d{1,5})*", hint="np. 11000,13000"),
    _e("M2_BIND_IP", "Adres nasłuchu rdzeni (w kontenerze)", "Adres, na którym rdzenie gry nasłuchują wewnątrz kontenera. Zostaw 0.0.0.0.",
       "siec", "address", "0.0.0.0", ["game"], dangerous=True),
    _e("M2_LOCAL_ONLY", "Serwer tylko dla tego komputera",
       "Włączone: panel mówi wprost, że nikt z sieci nie dołączy (instalacja lokalna). Na prawdziwym serwerze (także za nginx) zostaw wyłączone.",
       "siec", "bool", "0", ["panel"]),
    _e("M2_TRUST_PROXY", "Panel za nginx (zaufaj X-Forwarded)",
       "Włącz tylko, gdy panel klasyczny stoi za nginx i jest wystawiony wyłącznie na 127.0.0.1 (ustawia to instalator przy domenie).",
       "siec", "bool", "0", ["panel"], dangerous=True),

    # ------------------------------------------------------------------ Panele
    _e("M2_PANEL_LOCAL_ONLY", "Panel klasyczny bez hasła",
       "Puste (domyślnie na linii 2.x) = panel nie pyta o hasło na żadnym adresie. 0 = wymagaj hasła (ustaw je w M2_PANEL_PASSWORD) – zalecane na VPS. 1 = zawsze bez hasła.",
       "panele", "enum", "", ["panel"], options=[["", "domyślnie (bez hasła)"], ["0", "0 – wymagaj hasła"], ["1", "1 – zawsze bez hasła"]],
       dangerous=True),
    _e("M2_PANEL_PASSWORD", "Hasło panelu klasycznego",
       "Hasło do panelu klasycznego.", "panele", "string", "", ["panel"], secret=True, readonly=True,
       readonly_reason="Panel klasyczny trzyma hasło we własnym pliku konfiguracyjnym utworzonym przy pierwszym starcie – sama zmiana w .env nic nie daje. "
                       "Zmiana: wpisz nowe hasło w .env, potem `docker compose exec panel rm /usr/local/etc/m2panel.conf` i `docker compose up -d --force-recreate panel`."),
    _e("M2_ADMINPAGE_PASSWORD", "Hasło strony admina silnika",
       "Hasło wbudowanej strony administracyjnej silnika gry (niezwiązane z panelami). Gdy klucz sesji panelu zaawansowanego jest pusty, służy też jako ten klucz – "
       "zmiana wtedy wyloguje wszystkich z panelu zaawansowanego.",
       "panele", "string", "", ["game"] + SEBAN, secret=True, pattern=_SECRET, hint="litery, cyfry, . _ -"),
    _e("M2_SEBAN_SESSION_SECRET", "Klucz sesji panelu zaawansowanego",
       "Klucz podpisujący sesje tego panelu. Puste = używane jest hasło strony admina. Zmiana wyloguje wszystkich zalogowanych.",
       "panele", "string", "", SEBAN, secret=True, allow_empty=True, pattern=_SECRET, hint="litery, cyfry, . _ -"),
    _e("M2_REGISTER_ACCESS_CODE", "Hasło rejestracji (dla wspierających)",
       "Hasło, bez którego strona /register nie założy konta. Można je używać wiele razy. Puste = zwykła rejestracja bez hasła.",
       "panele", "string", "", ["panel"], secret=True, allow_empty=True, pattern=r"[A-Za-z0-9_-]{1,64}", hint="litery, cyfry, - i _ (najlepiej 10+ znaków)"),
    _e("M2_REGISTER_GAME_ADDRESS", "Adres serwera na stronie rejestracji",
       "Adres pokazywany graczom na stronie rejestracji dla wspierających. Puste = adres, pod którym gracz otworzył stronę.",
       "panele", "host", "", ["panel"], allow_empty=True),
    _e("M2_BRAND", "Nazwa serwera", "Nazwa serwera pokazywana w panelu klasycznym i na stronie. Puste = nazwa domyślna.",
       "panele", "string", "", ["panel"], allow_empty=True, pattern=r"[^$\"'`\\#]{1,60}", hint="do 60 znaków, bez $ \" ' ` \\ #"),
    _e("M2_CONTACT_EMAIL", "E-mail kontaktowy", "Adres, na który gracze piszą w sprawach serwera (strona główna panelu). Puste = linia ukryta.",
       "panele", "string", "", ["panel"], allow_empty=True, pattern=r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", hint="np. admin@example.org"),
    _e("M2_SEBAN_TIERU_PANEL_URL", "Adres panelu klasycznego (dla przeglądarki)",
       "Adres panelu klasycznego widziany z przeglądarki – przycisk przejścia między panelami i ikony umiejętności. Puste = http://127.0.0.1:<port panelu>.",
       "panele", "url", "", SEBAN, allow_empty=True),
    _e("M2_GM_PANEL_URL", "Adres karty postaci dla GM",
       "Gdzie otwiera się „Podgląd” postaci z okna gracza w grze (karta postaci w panelu klasycznym). Puste = http://127.0.0.1:<port panelu>/.",
       "panele", "url", "", ["game"], allow_empty=True),
    _e("M2_SEBAN_COLLECTOR_INTERVAL", "Częstotliwość zbierania statystyk (s)", "Co ile sekund kolektor panelu zaawansowanego zapisuje statystyki świata.",
       "panele", "int", "300", SEBAN, min=30, max=3600, step=30),
    _e("M2_PLAYERBOTS_VERSION", "Wersja pokazywana w panelu (zapas)",
       "Wersja serwera pokazywana, gdy panel nie zna jej z pliku VERSION. Zwykle zbędne – panel czyta wersję sam.",
       "panele", "string", "", SEBAN, allow_empty=True, pattern=r"\d+(\.\d+){1,3}", hint="np. 2.2.38"),
    _e("M2_INVENTORY_SLOTS", "Komórki ekwipunku (panel)", "Ile komórek plecaka przeszukuje panel klasyczny przy nadawaniu (180 = cztery strony).",
       "panele", "int", "180", ["panel"], min=45, max=180, step=45),
    _e("M2_MAX_ITEM_COUNT", "Największy stos przedmiotów (panel)", "Największy stos, jaki panel klasyczny zapisze (kolumna w bazie mieści najwyżej 255).",
       "panele", "int", "255", ["panel"], min=1, max=255),

    # ------------------------------------------------------------------ Klient
    _e("M2_CLIENT_URL", "Adres pobierania klienta", "Adres, spod którego panel proponuje pobranie klienta. Puste = klient serwowany przez panel.",
       "klient", "url", "", ["panel"], allow_empty=True),
    _e("M2_CLIENT_NAME", "Nazwa pliku klienta", "Nazwa pliku klienta pokazywana graczom przy pobieraniu.",
       "klient", "string", "", ["panel"], allow_empty=True, pattern=r"[A-Za-z0-9._ ()-]{1,80}", hint="np. Metin2-MT2009.zip"),
    _e("M2_CLIENT_ADDRESS", "Adres wpisany w klienta", "Adres zapisywany klientowi w serverinfo. Puste = publiczny adres serwera.",
       "klient", "host", "", ["panel"], allow_empty=True),
    _e("M2_CLIENT_AUTH_PORT", "Port logowania wpisany w klienta", "Port logowania zapisywany klientowi. Puste = port logowania serwera.",
       "klient", "port", "", ["panel"], allow_empty=True),
    _e("M2_CLIENT_SERVER_NAME", "Nazwa serwera w kliencie", "Nazwa serwera na liście w kliencie. Puste = nazwa z plików serwera.",
       "klient", "string", "", [], allow_empty=True, pattern=r"[^$\"'`\\#]{1,60}", hint="do 60 znaków",
       note="Czyta to budowanie klienta (client-builder) – zmiana nie restartuje kontenerów."),
    _e("M2_CLIENT_CHANNELS", "Liczba kanałów w kliencie", "Ile kanałów klient ma pokazać. Puste = tyle, ile naprawdę działa (zalecane).",
       "klient", "int", "", [], allow_empty=True, min=1, max=4,
       note="Czyta to budowanie klienta (client-builder) – zmiana nie restartuje kontenerów."),
    _e("M2_CLIENT_ARCHIVE_URL", "Adres paczki klienta", "Skąd budowanie klienta ściąga paczkę. Puste = adres z manifestu wydania.",
       "klient", "url", "", [], allow_empty=True, note="Czyta to launcher/budowanie klienta – zmiana nie restartuje kontenerów."),
    _e("M2_CLIENT_ARCHIVE_URL_FALLBACK", "Zapasowy adres paczki klienta", "Adres zapasowy, gdy główny nie odpowiada (np. MEGA „509 over quota”).",
       "klient", "url", "", [], allow_empty=True, note="Czyta to launcher/budowanie klienta – zmiana nie restartuje kontenerów."),
    _e("M2_CLIENT_ARCHIVE_URL_FALLBACK2", "Drugi zapasowy adres paczki klienta", "Drugi adres zapasowy paczki klienta.",
       "klient", "url", "", [], allow_empty=True, note="Czyta to launcher/budowanie klienta – zmiana nie restartuje kontenerów."),
    _e("M2_CLIENT_ARCHIVE_SHA256", "Suma SHA-256 paczki klienta", "Suma kontrolna paczki klienta. Puste = sprawdzana z manifestu.",
       "klient", "string", "", [], allow_empty=True, pattern=r"[A-Fa-f0-9]{64}", hint="64 znaki szesnastkowe",
       note="Czyta to launcher/budowanie klienta – zmiana nie restartuje kontenerów."),
    _e("M2_CLIENT_KEEP_ARCHIVE", "Zachowaj pobrany zip klienta", "Włączone: zip klienta zostaje po zbudowaniu (~1,4 GB, szybsza naprawa). Wyłączone: odzyskaj miejsce.",
       "klient", "bool", "1", [], note="Czyta to launcher/budowanie klienta – zmiana nie restartuje kontenerów."),
    _e("M2_CLIENT_MIN_FREE_MB", "Wymagane wolne miejsce (MB)", "Ile MB wolnego miejsca musi być, żeby zacząć pobieranie i budowanie klienta.",
       "klient", "int", "7000", [], min=500, max=100000, step=500, note="Czyta to launcher/budowanie klienta – zmiana nie restartuje kontenerów."),

    # ------------------------------------------------------------------ Przeglądarka
    _e("M2_BROWSER_PLAY", "Gra przez przeglądarkę (eksperyment)",
       "Włącza przycisk gry w przeglądarce w panelu klasycznym. Wymaga też mostka (wsbridge) i klienta WebAssembly – bez nich przycisk się nie pokaże.",
       "przegladarka", "bool", "0", ["panel"]),
    _e("M2_BRIDGE_PORT", "Port mostka", "Port mostka WebSocket do gry przez przeglądarkę.",
       "przegladarka", "port", "7789", ["panel"], dangerous=True),
    _e("M2_BRIDGE_BIND_ADDRESS", "Adres nasłuchu mostka", "Adres nasłuchu mostka. 127.0.0.1 = tylko ten komputer (np. za nginx).",
       "przegladarka", "address", "127.0.0.1", [], dangerous=True, note="Czyta to usługa wsbridge (profil browser) – uruchom ją ponownie ręcznie."),
    _e("M2_BRIDGE_HOST_ALIASES", "Dodatkowe nazwy hosta mostka", "Nazwy, pod którymi mostek odpowiada (po przecinku). Puste = każda nazwa (zalecane).",
       "przegladarka", "string", "", [], allow_empty=True, pattern=_HOST + r"(," + _HOST + r")*", hint="np. gra.example.org",
       note="Czyta to usługa wsbridge (profil browser) – uruchom ją ponownie ręcznie."),
    _e("M2_BRIDGE_TRUST_PROXY", "Mostek za nginx/Cloudflare", "Włącz tylko, gdy do mostka dochodzi wyłącznie nginx (adres nasłuchu 127.0.0.1).",
       "przegladarka", "bool", "0", [], note="Czyta to usługa wsbridge (profil browser) – uruchom ją ponownie ręcznie."),
    _e("M2_BRIDGE_MAX_CONNECTIONS", "Mostek: połączeń łącznie", "Ile połączeń naraz mostek przyjmie.",
       "przegladarka", "int", "200", [], min=1, max=10000, note="Czyta to usługa wsbridge (profil browser) – uruchom ją ponownie ręcznie."),
    _e("M2_BRIDGE_MAX_PER_IP", "Mostek: połączeń z jednego IP", "Ile połączeń z jednego adresu IP.",
       "przegladarka", "int", "8", [], min=1, max=100, note="Czyta to usługa wsbridge (profil browser) – uruchom ją ponownie ręcznie."),
    _e("M2_BRIDGE_ORIGINS", "Dozwolone strony dla mostka", "Z jakich stron wolno łączyć się z mostkiem (adresy po przecinku). Puste = bez ograniczeń.",
       "przegladarka", "string", "", [], allow_empty=True, pattern=_URL + r"(," + _URL + r")*", hint="np. https://example.org",
       note="Czyta to usługa wsbridge (profil browser) – uruchom ją ponownie ręcznie."),
    _e("M2_BROWSER_CACHE_MB", "Pamięć gry w przeglądarce (MB)", "Ile MB danych gry strona trzyma w pamięci. Decyduje o płynności; 0 = domyślne strony (96).",
       "przegladarka", "int", "768", ["panel"], min=0, max=4096, step=64),

    # ------------------------------------------------------------------ Baza
    _e("M2_DB_ROOT_PASSWORD", "Hasło administratora bazy",
       "Hasło konta root bazy danych.", "baza", "string", "", ["game", "mariadb", "playerbot-migrate"], secret=True, readonly=True,
       readonly_reason="Baza zapamiętuje hasło przy pierwszym starcie (w danych na wolumenie). Zmiana tylko w .env odcięłaby serwer od jego własnej bazy – "
                       "hasło trzeba najpierw zmienić w samej bazie (ALTER USER), a dopiero potem w .env."),
    _e("M2_DB_PASSWORD", "Hasło użytkownika bazy",
       "Hasło użytkownika bazy, którego używają serwer gry i panele.", "baza", "string", "", ALL_DB, secret=True, readonly=True,
       readonly_reason="Jak wyżej: użytkownik bazy ma hasło zapisane w danych bazy. Zmiana tylko w .env zatrzyma grę i panele."),
    _e("M2_DB_USER", "Użytkownik bazy", "Nazwa użytkownika bazy, którego używa serwer.", "baza", "string", "metin2", ALL_DB, readonly=True,
       readonly_reason="Użytkownik jest tworzony przy pierwszym starcie bazy – zmiana nazwy po instalacji odcina serwer od danych."),
    _e("M2_KEEP_DEMO_ACCOUNTS", "Konta demonstracyjne (admin/admin)", "Czy przy tworzeniu świeżej bazy zostawić konta testowe z paczki.",
       "baza", "bool", "1", ["mariadb", "game"], note="Działa tylko przy tworzeniu nowej bazy (świeża instalacja / reset). Odtwarza bazę i serwer gry."),
    _e("PLAYERBOT_SEED_STRICT", "Ścisłe sprawdzanie botów przy starcie", "Dla testów: przerwij start, jeśli boty w bazie nie zgadzają się z oczekiwanymi. Zostaw wyłączone.",
       "baza", "bool", "0", GAME),
    _e("PLAYERBOT_EXPECT_MIN_EXISTING_BOTS", "Minimalna liczba botów w bazie", "Ochrona świata: ilu botów musi już być w bazie, żeby start był uznany za dobry. 0 = bez sprawdzania.",
       "baza", "int", "0", GAME, min=0, max=10000),
    _e("M2_TABLE_POSTFIX", "Przyrostek nazw tabel", "Przyrostek nazw tabel gry. Zostaw puste.", "baza", "string", "", ["game"], readonly=True,
       readonly_reason="Zmiana przyrostka sprawia, że serwer szuka innych tabel – świat wyglądałby na pusty."),

    # ------------------------------------------------------------------ Aktualizacje
    _e("M2_UPDATE_CHECK", "Sprawdzaj nowe wersje", "Raz dziennie panel sprawdza na GitHubie, czy jest nowsza wersja. Nic o serwerze nie jest wysyłane.",
       "aktualizacje", "bool", "1", ["panel"]),
    _e("M2_UPDATE_APPLY", "Instalacja aktualizacji z panelu",
       "Czy panel klasyczny może zainstalować aktualizację przyciskiem (tylko Linux, wymaga uruchomionego aktualizatora). Na serwerze dostępnym dla innych zostaw wyłączone.",
       "aktualizacje", "bool", "0", ["panel", "updater"], dangerous=True),
    _e("M2_UPDATE_COMMAND", "Polecenie aktualizacji (podpowiedź)", "Polecenie, które panel klasyczny pokazuje jako sposób aktualizacji. Puste = opis ręcznej aktualizacji.",
       "aktualizacje", "string", "", ["panel"], allow_empty=True, pattern=r"[^$`\"\\]{1,200}", hint="tekst do 200 znaków, bez $ ` \" \\"),
    _e("M2_UPDATE_BRANCH", "Gałąź aktualizacji", "Gałąź, z której brać aktualizacje. Zostaw main.",
       "aktualizacje", "string", "main", ["updater"], pattern=r"[A-Za-z0-9._/-]{1,60}", dangerous=True),
    _e("M2_UPDATE_WATCH_UPDATES", "Aktualizator instaluje aktualizacje",
       "Wyłączone: aktualizator służy tylko temu edytorowi (zapis .env i restart usług), a przycisk aktualizacji nic nie robi – np. na serwerze testowym.",
       "aktualizacje", "bool", "0", ["updater"], allow_empty=True,
       note="Puste = jak „Instalacja aktualizacji z panelu”. Aktualizator uruchamiany automatycznie zawsze dostaje tę wartość z M2_UPDATE_APPLY."),
    _e("M2_UPDATE_AUTOSTART", "Aktualizator startuje sam",
       "Włączone: aktualizator (potrzebny do zapisu tej strony) uruchamia się sam po instalacji i aktualizacji (VPS) oraz przy starcie serwera z launchera (Windows). "
       "Domyślnie nie instaluje aktualizacji. Wyłączone: trzeba go uruchamiać ręcznie.",
       "aktualizacje", "bool", "1", [], note="Czytane przez update.sh i launcher – zmiana nie restartuje kontenerów."),
    _e("M2_UPDATE_STACK_DIR", "Katalog serwera (aktualizator)", "Ścieżka katalogu serwera na hoście, montowana do aktualizatora.",
       "aktualizacje", "path", "/opt/metin2", ["updater"], readonly=True,
       readonly_reason="Ścieżki na hoście zmienia się tylko ręcznie w .env: panel nie może wskazywać aktualizatorowi (który ma dostęp do Dockera) dowolnych katalogów."),
    _e("M2_UPDATE_CACHE_DIR", "Katalog podręczny aktualizacji", "Katalog podręczny aktualizacji na hoście.",
       "aktualizacje", "path", "/var/cache/m2src", ["updater"], readonly=True,
       readonly_reason="Ścieżki na hoście zmienia się tylko ręcznie w .env (bezpieczeństwo)."),
    _e("M2_UPDATE_REPO_DIR", "Katalog repozytorium aktualizacji", "Katalog z pobranym repozytorium aktualizacji.",
       "aktualizacje", "path", "/var/cache/m2src/repo", ["updater"], readonly=True,
       readonly_reason="Ścieżki na hoście zmienia się tylko ręcznie w .env (bezpieczeństwo)."),

    # ------------------------------------------------------------------ Zaawansowane
    _e("M2_TZ", "Strefa czasowa", "Strefa czasowa kontenerów, np. Europe/Warsaw. Ustawia godziny w logach, w panelach i porę nocy botów.",
       "zaawansowane", "string", "UTC", ["game", "itemshop", "mariadb", "panel", "updater"] + SEBAN,
       pattern=r"UTC|[A-Za-z_]+(/[A-Za-z0-9_+-]+){1,2}", hint="np. Europe/Warsaw", suggestions=["Europe/Warsaw", "UTC", "Europe/London", "Europe/Berlin"],
       note="Odtwarza wszystkie kontenery, także bazę danych (gracze zostaną rozłączeni)."),
    _e("M2_LOG_KEEP_DAYS", "Ile dni trzymać logi", "Ile dni logów serwera trzymać. Kanał zapisuje 40–120 MB na godzinę – na małym dysku zmniejsz.",
       "zaawansowane", "int", "7", ["game"], min=1, max=90),
    _e("M2_TEST_SERVER", "Tryb testowy silnika", "Włącza tryb testowy silnika (komendy GM dla wszystkich, więcej logów). Na serwerze, na którym ktoś gra, zostaw wyłączone.",
       "zaawansowane", "bool", "0", ["game"], dangerous=True),
    _e("M2_CORE_DUMPS", "Zrzuty pamięci po awarii", "Zapisuj zrzut pamięci po awarii rdzenia (do zgłaszania błędów). Zajmuje dużo miejsca – włączaj tylko na czas badania awarii.",
       "zaawansowane", "bool", "0", ["game"]),
    _e("M2_BACKUP_HOST_DIR", "Katalog kopii przed resetem", "Katalog na hoście, do którego reset świata zapisuje kopię bazy.",
       "zaawansowane", "path", "../../backups", ["game"], readonly=True,
       readonly_reason="Ścieżki na hoście zmienia się tylko ręcznie w .env: panel nie może montować kontenerom dowolnych katalogów hosta."),
    _e("M2_MALL_SAS_KEY", "Klucz podpisu linku ItemShopu", "Klucz, którym rdzeń podpisuje link do ItemShopu (GF9001).", "zaawansowane", "string", "", ["itemshop"],
       secret=True, readonly=True, readonly_reason="Musi być taki sam jak w skompilowanym rdzeniu gry – zmiana tylko tutaj zepsuje otwieranie ItemShopu."),
    _e("M2_MAKE_JOBS", "Wątki kompilacji", "Ile rdzeni procesora użyć przy budowaniu serwera. Puste = dobierz do pamięci maszyny.",
       "zaawansowane", "int", "", ["game"], allow_empty=True, min=1, max=64, build=True),
    _e("M2_STRIP_BINARIES", "Mniejsze pliki wykonywalne", "Włączone: binaria bez symboli (mniejszy obraz). Wyłączone: symbole do czytania awarii (gdb).",
       "zaawansowane", "bool", "1", ["game"], build=True),
    _e("M2_APT_MIRROR", "Serwer pakietów przy budowaniu", "Lustro pakietów Ubuntu używane przy budowaniu obrazu gry. Puste = polskie lustro (szybkie z Polski).",
       "zaawansowane", "url", "", ["game"], allow_empty=True, build=True, dangerous=True),
    _e("M2_BASE_IMAGE", "Obraz bazowy serwera", "Obraz systemu, na którym budowany jest serwer.", "zaawansowane", "string", "ubuntu:24.04", ["game"],
       build=True, readonly=True, readonly_reason="Serwer jest kompilowany i testowany na ubuntu:24.04 – inny obraz to pewny błąd budowania."),
    _e("M2_COMPOSE_PROJECT_NAME", "Nazwa projektu Dockera", "Nazwa projektu Dockera tej instalacji (ustawia ją launcher/instalator).",
       "zaawansowane", "string", "", [], readonly=True,
       readonly_reason="Zmiana nazwy projektu odcina serwer od jego wolumenów, czyli od całego świata i bazy."),
    _e("M2_CONTAINER_PREFIX", "Przedrostek nazw kontenerów", "Przedrostek nazw kontenerów (ustawia launcher/instalator).",
       "zaawansowane", "string", "", ALL_DB + ["updater"], readonly=True,
       readonly_reason="Zmiana tworzy kontenery o nowych nazwach obok starych – dwa serwery walczyłyby o te same porty."),
    _e("PLAYERBOT_RETIRE_COUNT", "Emerytury z .env: liczba botów", "Starszy sposób uruchamiania emerytur botów z .env. Zamiast tego użyj strony „Emerytury botów”.",
       "zaawansowane", "int", "0", ["game"], min=0, max=2500),
    _e("PLAYERBOT_RETIRE_WINDOW_MINUTES", "Emerytury z .env: okno wyboru (min)", "Jak wyżej: w ciągu ilu minut boty są wybierane do partii.",
       "zaawansowane", "int", "1440", ["game"], min=1, max=10080),
    _e("PLAYERBOT_RETIRE_SHOP_MINUTES", "Emerytury z .env: czas sklepu (min)", "Jak wyżej: jak długo bot trzyma sklep przed zakończeniem gry.",
       "zaawansowane", "int", "60", ["game"], min=1, max=10080),
    _e("PLAYERBOT_RETIRE_BATCH_ID", "Emerytury z .env: numer partii", "Numer partii emerytur – nadaje go system.", "zaawansowane", "int", "0", ["game"],
       readonly=True, readonly_reason="Numer partii jest techniczny – zmienia go system emerytur."),
    _e("M2_PLAYERBOT_CH2_SET_AT", "Znacznik zmiany kanałów CH2–CH4", "Moment ostatniej zmiany kanałów CH2/CH3/CH4 (porównywany z ustawieniem z panelu).",
       "zaawansowane", "int", "0", ["game"], readonly=True, readonly_reason="Ustawiany automatycznie przy zmianie kanałów CH2/CH3/CH4."),
    _e("M2_PLAYERBOT_KINGDOMS_DEFAULTED", "Znacznik: królestwa przestawione", "Znacznik jednorazowej migracji – nie ruszaj.",
       "zaawansowane", "string", "1", [], readonly=True, readonly_reason="Znacznik techniczny jednorazowej migracji aktualizacji."),
    _e("M2_PLAYERBOT_WORLD_LAYOUT_DEFAULTED", "Znacznik: układ świata przestawiony", "Znacznik jednorazowej migracji – nie ruszaj.",
       "zaawansowane", "string", "", [], readonly=True, readonly_reason="Znacznik techniczny jednorazowej migracji aktualizacji."),
    _e("M2_BLESSING_SCROLL_STONE_PERMILLE_DEFAULTED", "Znacznik: szansa zwoju przestawiona", "Znacznik jednorazowej migracji – nie ruszaj.",
       "zaawansowane", "string", "", [], readonly=True, readonly_reason="Znacznik techniczny jednorazowej migracji aktualizacji."),
    _e("M2_LOG_KEEP_DAYS_DEFAULTED", "Znacznik: dni logów przestawione", "Znacznik jednorazowej migracji – nie ruszaj.",
       "zaawansowane", "string", "", [], readonly=True, readonly_reason="Znacznik techniczny jednorazowej migracji aktualizacji."),
    _e("M2_TZ_DEFAULTED", "Znacznik: strefa czasowa ustawiona", "Znacznik jednorazowej migracji – nie ruszaj.",
       "zaawansowane", "string", "", [], readonly=True, readonly_reason="Znacznik techniczny jednorazowej migracji aktualizacji."),
]

BY_KEY = {entry["key"]: entry for entry in SCHEMA}

# Keys whose change makes the updater adjust M2_CHANNELS / the port ranges
# (update.sh's sync_channel_ports) right after writing .env.
CHANNEL_KEYS = ("M2_PLAYERBOT_CH2", "M2_PLAYERBOT_CH3", "M2_PLAYERBOT_CH4", "M2_CHANNELS", "M2_GAME_PORT_BASE")

_FORBIDDEN = re.compile(r"[\x00-\x1f\x7f$`\"'\\]")


def _int_ok(value, entry):
    if not re.fullmatch(r"-?\d{1,9}", value):
        return "musi być liczbą całkowitą"
    number = int(value)
    if "min" in entry and number < entry["min"]:
        return "najmniej %s" % entry["min"]
    if "max" in entry and number > entry["max"]:
        return "najwyżej %s" % entry["max"]
    return None


def validate(key, value):
    """None when value may be written for key, else a Polish reason.

    Run by the panel before it queues a change and again by the updater
    before it writes .env (the updater never trusts the panel)."""
    entry = BY_KEY.get(key)
    if entry is None:
        return "nieznana zmienna"
    if entry.get("readonly"):
        return "tej wartości nie można zmieniać z panelu"
    if not isinstance(value, str):
        return "nieprawidłowa wartość"
    if value != value.strip():
        return "bez spacji na początku i końcu"
    if len(value) > 300:
        return "za długa wartość"
    if _FORBIDDEN.search(value) or "#" in value:
        return "niedozwolone znaki ($ ` \" ' \\ # lub znaki sterujące)"
    if value == "":
        if entry.get("allow_empty") or entry["type"] == "enum" and "" in [o[0] for o in entry.get("options", [])]:
            return None
        return "wartość nie może być pusta"
    kind = entry["type"]
    if kind == "int":
        return _int_ok(value, entry)
    if kind == "number":
        if not re.fullmatch(r"\d{1,6}(\.\d{1,3})?", value):
            return "musi być liczbą (np. 0 albo 1.5)"
        number = float(value)
        if number < entry.get("min", 0) or number > entry.get("max", 1e9):
            return "zakres %s–%s" % (entry.get("min", 0), entry.get("max"))
        return None
    if kind == "bool":
        return None if value in ("0", "1") else "tylko 0 albo 1"
    if kind == "enum":
        return None if value in [o[0] for o in entry["options"]] else "dozwolone: " + ", ".join(o[0] or "(puste)" for o in entry["options"])
    if kind == "port":
        if not re.fullmatch(r"\d{1,5}", value) or not 1 <= int(value) <= 65535:
            return "port 1–65535"
        return None
    if kind == "portrange":
        match = re.fullmatch(r"(\d{1,5})-(\d{1,5})", value)
        if not match or not 1 <= int(match.group(1)) <= int(match.group(2)) <= 65535:
            return "zakres portów, np. 13000-13002"
        return None
    if kind == "address":
        return None if re.fullmatch(_IPV4, value) else "adres IPv4, np. 0.0.0.0 albo 127.0.0.1"
    if kind == "host":
        return None if re.fullmatch(_HOST, value) and len(value) <= 253 else "adres IP albo nazwa domeny (bez http:// i portu)"
    if kind == "url":
        return None if re.fullmatch(_URL, value) else "adres zaczynający się od http:// albo https://"
    if kind == "path":
        return None if re.fullmatch(r"[A-Za-z0-9._/-]{1,200}", value) else "ścieżka"
    pattern = entry.get("pattern")
    if pattern and not re.fullmatch(pattern, value):
        return "nieprawidłowy format" + (" (" + entry["hint"] + ")" if entry.get("hint") else "")
    if entry.get("secret") and not pattern and not re.fullmatch(_SECRET, value):
        return "tylko litery, cyfry, . _ -"
    return None


def services_for(keys):
    """Compose services to recreate for these keys (build-only keys: none)."""
    found = []
    for key in keys:
        entry = BY_KEY.get(key)
        if not entry or entry.get("build"):
            continue
        for service in entry["services"]:
            if service not in found:
                found.append(service)
    order = list(SERVICE_LABELS)
    return sorted(found, key=lambda s: order.index(s) if s in order else len(order))


# MT2009_PLUS_ENV_LIVE_V1: the switches the classic panel already turns LIVE
# (an event flag in player.quest plus a web_admin_queue row the in-game
# helper, web_admin.quest, applies within seconds). The .env page switches
# these itself even without the updater; the updater writes the .env line
# later (env.pending), without restarting anything.
LIVE_KEYS = {
    "M2_AREZZO": "AREZZO",
    "M2_SEONHAE": "SEONHAE",
    "M2_TELEPORT_MAP": "TPMAP",
    "M2_ALCHEMY": "RARE",
    "M2_SASHES": "RARE",
}


def public_schema():
    """What the page needs (descriptions, types, ranges) - no values."""
    return {"version": SCHEMA_VERSION, "sections": SECTIONS, "services": SERVICE_LABELS, "fields": SCHEMA,
            "live": sorted(LIVE_KEYS)}
