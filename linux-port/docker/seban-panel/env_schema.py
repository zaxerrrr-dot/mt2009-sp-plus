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

# MT2009_PLUS_UPDATER_REFRESH_V1: raise it with every key added or removed -
# the panel compares it with the updater's (env.current "schema_version") and
# says "aktualizator działa na starej wersji" instead of "nieznana zmienna".
# 2: M2_SHOP_BIG (2.34) and everything before it.
# 3: M2_DB_LOG_RETENTION_DAYS, M2_LOG_KEEP_HOURS (2.36).
# 4: M2_MLODZI_BOHATEROWIE (Yohara 3.x, MT2009_PLUS_MLODZI_BOHATEROWIE_V1).
# 5: M2_SEBAN_KEEP_* and M2_SEBAN_GEAR_PER_CHARACTER (Yohara 3.0.7,
#    MT2009_PLUS_SEBAN_SNAPSHOT_RETENTION_V1).
# 6: M2_MONSTER_ATTACK (MT2009_PLUS_MOB_ATTACK_V1) and M2_SERVER_PROFILE
#    (MT2009_PLUS_SERVER_CONFIG_V1), Yohara 3.0.7.
# 7: M2_PLAYER_ATTACK (MT2009_PLUS_PC_ATTACK_V1, the EMERALD configuration).
# 8: M2_SEBAN_SNAPSHOT_HEAVY_HOURS (MT2009_PLUS_SEBAN_SNAPSHOT_GENTLE_V1).
# 9: M2_SKILL_HACK (MT2009_PLUS_SKILL_HACK_V1, the other specialisation's skills).
# 10: M2_DEFAULT_LANGUAGE (MT2009_PLUS_LANGUAGE_DEFAULT_V1, the server's default language).
# 11: M2_WEBCLIENT_* (MT2009_PLUS_WEBCLIENT_SERVICE_V1, the webclient service).
SCHEMA_VERSION = 11

SECTIONS = [
    {"id": "boty", "label": "Boty", "icon": "🤖",
     "desc": "Ile botów gra, jak wchodzą do świata, królestwa i drugi kanał."},
    {"id": "swiat", "label": "Świat i rates", "icon": "🌍",
     "desc": "Trudność, mnożniki świeżego świata, szanse eventów i dropu, poziom maksymalny."},
    {"id": "moduly", "label": "Moduły gry", "icon": "🧩",
     "desc": "Arezzo, Seon-Hae, alchemia, szarfy, Auto Łowy, Towarzysz, Dom Towarowy, Karty Potworów, Bronie dla Młodych Bohaterów, zestawy startowe."},
    {"id": "siec", "label": "Sieć i porty", "icon": "🌐",
     "desc": "Adres serwera, porty gry, logowania, paneli i sklepu, adresy nasłuchu."},
    {"id": "panele", "label": "Panele i strona", "icon": "🖥",
     "desc": "Hasła i dostęp do paneli, nazwa serwera, rejestracja, adresy między panelami."},
    {"id": "klient", "label": "Klient gry", "icon": "💾",
     "desc": "Klient do pobrania: nazwa, adres wpisany w klienta, paczka źródłowa."},
    {"id": "webklient", "label": "Gra w przeglądarce", "icon": "🕹",
     "desc": "Gra w przeglądarce (komputer i telefon) na własnym porcie, jak panele: włączenie, port, adres, skąd pobierać jej pliki."},
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
    "webclient": "Gra w przeglądarce",
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
    # MT2009_PLUS_BOT_YOHARA_HANDOVER_V1: the bots between the game cores (playerbot_yohara_bots.h).
    _e("PLAYERBOT_HANDOVER", "Boty przechodzą między rdzeniami",
       "Włączone: boty przechodzą na rdzeń, który hostuje mapę (Zaklęty Las, Szczelina Czasu, wypady po drop na mapy 90), "
       "i wracają do swojej wioski. Zdarzenie m2_bot_handover_off 1 wyłącza to w locie i odsyła boty do domu.",
       "boty", "bool", "1", ["game"]),
    _e("PLAYERBOT_HANDOVER_CHANNELS", "Kanały z przejściami botów",
       "Na których kanałach boty przechodzą między rdzeniami (lista, np. 1 albo 1,2). Każdy kanał to osobne siatki map w pamięci.",
       "boty", "string", "1", ["game"]),
    _e("PLAYERBOT_ZAKLETY_MAX", "Boty w Zaklętym Lesie (na kanał)",
       "Ilu botów naraz expi w Zaklętym Lesie (mapa 353, rdzeń Yohary). Wchodzą przez Świątynię Ochao i portal Strażnika En-Tai. 0 = nikt.",
       "boty", "int", "100", ["game"], min=0, max=300),
    _e("PLAYERBOT_ZAKLETY_MIN_LEVEL", "Zaklęty Las od poziomu",
       "Od jakiego poziomu boty idą expić do Zaklętego Lasu (95–109; do 109, od 110 Szczelina Czasu).",
       "boty", "int", "100", ["game"], min=95, max=109),
    _e("PLAYERBOT_ZAKLETY_MIN_HP", "Zaklęty Las: minimalne PŻ bota",
       "Bot idzie do Zaklętego Lasu tylko z co najmniej tyloma maks. PŻ (słabsze giną od paczek En-Tai). 0 = bez sprawdzania.",
       "boty", "int", "20000", ["game"], min=0, max=1000000),
    _e("PLAYERBOT_ZAKLETY_STAY_MIN", "Wyprawa do Zaklętego Lasu (min)",
       "Ile minut bot zostaje w Zaklętym Lesie, zanim wróci do wioski (zapas mikstur uzupełnia na miejscu).",
       "boty", "int", "120", ["game"], min=20, max=600),
    _e("PLAYERBOT_SZC_MAX", "Boty w Szczelinie Czasu (na kanał)",
       "Ilu botów 110–119 czeka przy Statui Szczeliny Czasu na Płaskowyżu Iluzji i chodzi drużynami do Zaklętego Lasu (SZC). 0 = nikt.",
       "boty", "int", "100", ["game"], min=0, max=200),
    _e("PLAYERBOT_SZC_PARTIES", "Drużyny botów naraz w SZC",
       "Ile drużyn botów naraz w lochu Szczelina Czasu – Zaklęty Las (tylko polują: Metiny i potwory, bez misji).",
       "boty", "int", "14", ["game"], min=0, max=20),
    _e("PLAYERBOT_LOOTRUN_MAX", "Wypady botów po drop na mapy 90 (na kanał)",
       "Ilu botów (od 95 poziomu) naraz bije tylko Metiny i bossów na mapach 90. 0 = wyłączone.",
       "boty", "int", "6", ["game"], min=0, max=200),
    _e("PLAYERBOT_LOOTRUN_MAPS", "Mapy wypadów po drop",
       "Lista map: 301 Przylądek Smoczej Głowy, 302 Zbocze Gautama, 303 Nefrytowa Zatoka, 304 Gromiste Góry (301/302 to po ~125–160 MB pamięci).",
       "boty", "string", "303,304", ["game"]),
    # MT2009_PLUS_BOT_YOHARA_COHORT_V1: Wezowe Pole / Kraina Gigantow through the handover, and the cohorts.
    # MT2009_PLUS_MAPS_WZ_NOCAP_V1: -1 (the default) = no limit (the owner, 26 October 2026).
    _e("PLAYERBOT_SNAKEFIELD_MAX", "Boty na Wężowym Polu (na kanał)",
       "Ilu botów 63–78 naraz expi na Wężowym Polu (mapa 80, rdzeń game2). -1 = bez limitu (domyślnie), 0 = nikt, więcej = najwyżej tylu na kanał.",
       "boty", "int", "-1", ["game"], min=-1, max=300),
    _e("PLAYERBOT_GIANTLAND_MAX", "Boty w Krainie Gigantów (na kanał)",
       "Ilu botów 63–80 naraz expi w Krainie Gigantów (mapa 70, rdzeń game2). -1 = bez limitu (domyślnie), 0 = nikt, więcej = najwyżej tylu na kanał.",
       "boty", "int", "-1", ["game"], min=-1, max=300),
    _e("PLAYERBOT_WZ_STAY_MIN", "Wyprawa na Wężowe Pole / do Krainy (min)",
       "Ile minut bot zostaje na Wężowym Polu albo w Krainie Gigantów, zanim wróci do wioski.",
       "boty", "int", "120", ["game"], min=20, max=600),
    _e("PLAYERBOT_COHORT", "Kohorty botów",
       "Włączone: boty z tabeli kohort (Zaklęty Las, Szczelina Czasu, Wężowe Pole, Kraina Gigantów) chodzą tylko na swoją mapę. "
       "Wyłączone: kohorty odłożone, tabela zostaje. Zdarzenie m2_bot_cohort_off 1 – to samo w locie.",
       "boty", "bool", "1", ["game"]),
    _e("PLAYERBOT_COHORT_EXCLUSIVE", "Mapa kohorty tylko dla jej botów",
       "Włączone: na mapę, która ma kohortę, nie idą inne boty.",
       "boty", "bool", "1", ["game"]),
    _e("PLAYERBOT_COHORT_STAY_MIN", "Pobyt bota kohorty (min)",
       "Ile minut bot kohorty zostaje na swojej mapie, zanim zrobi przerwę.",
       "boty", "int", "720", ["game"], min=20, max=1440),
    _e("PLAYERBOT_COHORT_DISPATCH", "Boty kohorty wysyłane co 5 s",
       "Ilu botów kohorty rdzeń wiosek wysyła naraz (co 5 sekund).",
       "boty", "int", "6", ["game"], min=1, max=50),
    _e("PLAYERBOT_COHORT_REST_MIN", "Przerwa bota kohorty (min)",
       "Ile minut bot kohorty odpoczywa po wyjściu z mapy.",
       "boty", "int", "10", ["game"], min=1, max=600),
    _e("PLAYERBOT_COHORT_DEATH_REST_MIN", "Przerwa po śmierciach (min)",
       "Ile minut bot kohorty odpoczywa, gdy zginął za często (3 w 30 min albo 5 w pobycie).",
       "boty", "int", "60", ["game"], min=1, max=1440),
    # MT2009_PLUS_BOT_HYDRA_COHORT_V1: the Hydra's cohort.
    _e("PLAYERBOT_HYDRA_MAX", "Boty na Hydrę (na kanał)",
       "Ilu botów kohorty Hydry naraz czeka na pomoście Portu Nowego Kontynentu i pływa drużynami na Obronę Statku. 0 = nikt.",
       "boty", "int", "32", ["game"], min=0, max=200),
    # MT2009_PLUS_BOT_HYDRA_PAIRS_V1: sixteen pairs at once.
    _e("PLAYERBOT_HYDRA_PARTIES", "Drużyny botów naraz na Hydrze",
       "Ile drużyn botów naraz broni statku (stałe pary z kohorty Hydry: ninja + inna postać; każda para ma własny statek).",
       "boty", "int", "16", ["game"], min=0, max=32),
    # MT2009_PLUS_BOT_YOHARA_MAPS_V1: the Sung Ma maps of Yohara for the bot Champions.
    _e("PLAYERBOT_SUNGMA_MAX", "Boty na mapach Yohary (na kanał)",
       "Ilu botów-Czempionów naraz poluje na mapach Sung Ma (Twierdza, Dongan, Seoganland, Namgan, Yilad, Wąwóz, Rozpadlina, "
       "Schronienie, Zejście). 0 = nikt.",
       # MT2009_PLUS_BOT_YOHARA800_V1: up to 1000 (the 100 + the 800 new Yohara bots on one channel)
       "boty", "int", "120", ["game"], min=0, max=1000),
    _e("PLAYERBOT_SUNGMA_MAP_MAX", "Boty na jednej mapie Yohary",
       "Najwięcej botów naraz na jednej mapie Sung Ma (na kanał).",
       "boty", "int", "30", ["game"], min=0, max=300),
    _e("PLAYERBOT_SUNGMA_STAY_MIN", "Pobyt bota na Yoharze (min)",
       "Co ile minut bot-Czempion z map Yohary jedzie do domu (M1) na handel i wraca (członek kohorty: pobyt jak kohorta).",
       "boty", "int", "240", ["game"], min=20, max=1440),
    _e("PLAYERBOT_SUNGMA_MAPS", "Mapy Yohary dla botów",
       "Lista map: 374 Opuszczona Twierdza, 373 Dongan, 376 Seoganland, 377 Namgan, 385 Przełęcz Yilad, 388 Wąwóz Płn. Wiatru, "
       "389 Rozpadlina Dusz, 393 Schronienie Płn. Wiatru, 394 Zejście Płn. Wiatru (każda mapa to 18–160 MB pamięci rdzenia Yohary).",
       "boty", "string", "374,373,376,377,385,388,389,393,394", ["game"]),
    # MT2009_PLUS_BOT_YOHARA_TRADE_TRIP_V1
    _e("PLAYERBOT_SUNGMA_TRADE_MAX", "Boty z Yohary naraz na handlu w domu",
       "Ilu botów z map Yohary naraz może być w swojej pierwszej wiosce tylko na handel (sklep offline, targ) – potem wracają "
       "same na swoją mapę. 0 = bez wyjazdów (koniec pobytu = powrót do domu).",
       "boty", "int", "6", ["game"], min=0, max=100),
    # MT2009_PLUS_BOT_DGRUN_CAP_ENV_V1: the bots' dungeon runs at once per core (GetPlayerBotDgRunCap).
    _e("PLAYERBOT_DGRUN_MIN_RUNS", "Lochy botów naraz na rdzeń – minimum",
       "Ile własnych wypraw botów do lochów może iść naraz na jednym rdzeniu gry co najmniej, niezależnie od liczby botów "
       "(limit rośnie o 1 loch na każde „Botów na 1 loch” botów rdzenia, do maksimum). SZC i Hydra mają własne limity "
       "(PLAYERBOT_SZC_PARTIES, PLAYERBOT_HYDRA_PARTIES) i się tu nie liczą. 0 = bez minimum.",
       "boty", "int", "4", ["game"], min=0, max=200),
    _e("PLAYERBOT_DGRUN_MAX_RUNS", "Lochy botów naraz na rdzeń – maksimum",
       "Najwięcej wypraw botów do lochów naraz na jednym rdzeniu gry, ile by botów nie było. 0 = bez górnego limitu "
       "(wtedy tylko 1 loch na N botów). SZC i Hydra mają własne limity.",
       "boty", "int", "12", ["game"], min=0, max=200),
    _e("PLAYERBOT_DGRUN_BOTS_PER_RUN", "Botów na 1 loch",
       "Limit lochów botów naraz na rdzeń to 1 loch na tylu botów rdzenia (np. 1200 botów / 120 = 10 lochów), "
       "ale nie mniej niż minimum i nie więcej niż maksimum. 0 = bez liczenia po botach (zawsze minimum).",
       "boty", "int", "120", ["game"], min=0, max=100000),
    _e("PLAYERBOT_DGRUN_STARVED_OVER_CAP", "Lochy botów ponad limit dla zapomnianych lochów",
       "O ile lochów ponad limit rdzenia boty mogą ruszyć do lochu, do którego nikt z nich nie chodził od 40 minut "
       "(żeby rzadziej wybierane lochy też miały wyprawy). 0 = nigdy ponad limit.",
       "boty", "int", "2", ["game"], min=0, max=50),
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
    # MT2009_PLUS_MOB_ATTACK_V1 (server-patches/mobattack): the twin of the health above.
    _e("M2_MONSTER_ATTACK", "Siła ataku potworów",
       "Ile obrażeń zadają potwory i bossowie: default = jak w grze (100%), easy = 80%, albo liczba 10–300 (procent). "
       "Obrażenia graczy i botów się nie zmieniają. „Konfiguracja serwera” zmienia to od razu; ta wartość obowiązuje, gdy ją zmienisz.",
       "swiat", "string", "default", GAME, pattern=r"default|easy|[1-9]\d|[12]\d\d|300",
       hint="default, easy albo liczba od 10 do 300", suggestions=["default", "easy", "50", "150", "200"]),
    # MT2009_PLUS_PC_ATTACK_V1 (server-patches/mobattack): the other way round - how hard the
    # players hit monsters (the EMERALD configuration's "+10% obrażeń zadawanych przez gracza").
    _e("M2_PLAYER_ATTACK", "Siła ataku graczy na potwory",
       "Ile obrażeń zadają gracze (i boty) potworom, bossom i Metinom: default = jak w grze (100%), albo liczba 10–300 (procent; "
       "110 = +10% jak na serwerach EMERALD). Walka między graczami (PvP) się nie zmienia. „Konfiguracja serwera” zmienia to od razu; "
       "ta wartość obowiązuje, gdy ją zmienisz.",
       "swiat", "string", "default", GAME, pattern=r"default|[1-9]\d|[12]\d\d|300",
       hint="default albo liczba od 10 do 300", suggestions=["default", "110", "120", "150"]),
    # MT2009_PLUS_SERVER_CONFIG_V1: the profile vps-install.sh --profile chose; informational.
    _e("M2_SERVER_PROFILE", "Profil serwera (pierwszy start)",
       "Nazwa profilu z „Konfiguracji serwera” wybranego przy instalacji (instalator VPS --profile). "
       "Sam wpis niczego nie zmienia – profil stosuje się na stronie „Konfiguracja serwera”, która też pamięta, co zastosowano.",
       "swiat", "string", "", [], pattern=r"[a-z0-9_]{1,32}", hint="małe litery, cyfry i _", allow_empty=True),
    _e("M2_BONUS_MODE", "Bonusy przedmiotów i żywioły",
       "mt2009 = jak dotąd: Maks. PŻ do 1500, Maks. PE do 250, regeneracja do 12%, żywioły mają bossowie i wybrane mapy oraz lochy, "
       "odporność na żywioł odejmuje cały swój procent. global = bonusy jak na serwerze globalnym: Maks. PŻ do 2000, Maks. PE do 80 "
       "(200 na naszyjniku), regeneracja do 30%, odporność na ogień, błyskawice i wiatr (zbroja, bransoleta, hełm), szansa na bonus "
       "doświadczenia i na podwójną ilość przedmiotów, bez wytrzymałości, czasu trwania umiejętności, odbicia strzał i stałego "
       "doświadczenia; każdy potwór ma swój żywioł, a odporność działa w 30% (15% = 4,5% mniej obrażeń). "
       "Alchemia (Smocze Kamienie) w trybie global ma domyślne bonusy (np. Diament: inteligencja, odporność na lód, siła lodu). "
       "Przedmioty zachowują wszystkie bonusy, które już mają; można przełączać w obie strony.",
       "swiat", "enum", "global", GAME,
       options=[["global", "global – jak na serwerze globalnym (domyślnie)"], ["mt2009", "mt2009 – bonusy i żywioły MT2009 PLUS"]],
       note="Działa po restarcie serwera gry (migrator przełącza tabelę bonusów i żywioły potworów)."),
    _e("M2_MOONLIGHT_CHEST_PERMILLE", "Szkatułka Blasku Księżyca z potworów (‰)",
       "Szansa w promilach (10 = 1%), że zabity potwór upuści Szkatułkę Blasku Księżyca. Działa w trakcie wydarzenia ustawionego w panelu. 0 wyłącza.",
       "swiat", "int", "10", ["game"], min=0, max=1000),
    _e("M2_MOONLIGHT_CHEST_STONE_PERMILLE", "Szkatułka Blasku Księżyca z Metinów (‰)", "To samo dla kamieni Metin (300 = 30%).",
       "swiat", "int", "300", ["game"], min=0, max=1000),
    _e("M2_BLESSING_SCROLL_STONE_PERMILLE", "Zwój Błogosławieństwa z Metinów (‰)",
       "Szansa na Zwój Błogosławieństwa z Metinów poziomu 15–99, w promilach (10 = 1%). Nie wypada postaci ponad 15 poziomów wyżej od kamienia. 0 wyłącza.",
       "swiat", "int", "10", ["game"], min=0, max=1000),
    _e("M2_DRAGON_COIN_STONE_PERMILLE", "Kupon SM (100) z Metinów (‰)", "Szansa w promilach na Kupon SM (100) z kamienia Metin (3 = 0,3%).",
       "swiat", "int", "3", ["game"], min=0, max=1000),
    _e("M2_DRAGON_COIN_BOSS_PERMILLE", "Kupon SM (100) z bossów (‰)", "Szansa w promilach na Kupon SM (100) z bossa (50 = 5%).",
       "swiat", "int", "50", ["game"], min=0, max=1000),
    # MT2009_PLUS_LANGUAGE_DEFAULT_V1: the server's default language (mt2009_language.cpp, the panels, the ItemShop)
    _e("M2_DEFAULT_LANGUAGE", "Domyślny język serwera",
       "Język, w którym gra każdy gracz, dopóki sam nie wybierze innego w ustawieniach klienta (teksty serwera, questy, "
       "ogłoszenia, odpowiedzi botów), język botów na krzyku i w handlu, język, na który przełącza się klient bez "
       "własnego wyboru, oraz język paneli i ItemShopu dla odwiedzającego, który nie wybrał innego. "
       "Wybór gracza zawsze ma pierwszeństwo i zostaje po zmianie tej wartości.",
       "swiat", "enum", "pl", ["game", "panel", "itemshop"] + SEBAN,
       options=[["pl", "polski (pl)"], ["en", "English (en)"], ["de", "Deutsch (de)"], ["tr", "Türkçe (tr)"],
                ["ro", "Română (ro)"], ["es", "Español (es)"], ["it", "Italiano (it)"], ["fr", "Français (fr)"],
                ["pt", "Português (pt)"], ["cz", "Čeština (cz)"], ["hu", "Magyar (hu)"], ["gr", "Ελληνικά (gr)"],
                ["ae", "العربية (ae)"]],
       note="Działa po restarcie serwera gry; gracze widzą go przy następnym wejściu do gry, klient bez własnego wyboru "
            "– po ponownym uruchomieniu."),
    _e("M2_DEFAULT_GAME_LANGUAGE", "Język nazw w grze (świeża instalacja)",
       "Język nazw przedmiotów, potworów i questów dla świeżego świata. Później przełącza się go przyciskiem w panelu (ten wybór ma pierwszeństwo).",
       "swiat", "enum", "en", [], options=[["pl", "polski"], ["en", "angielski"]],
       note="Czytane przy instalacji (instalator/launcher) – zmiana nie restartuje kontenerów."),

    # ------------------------------------------------------------------ Moduły
    _e("M2_AREZZO", "Moduł Arezzo",
       "Mapy i lochy z Arezzo: Dolina Cyklopów, Pustkowie Faraona, Biblioteka Wiedzy, Wzgórze Wukonga, Ruiny Skorpiona, Starożytna Dżungla "
       "oraz zestawy kostiumów w ItemShopie. Panel klasyczny przełącza go od razu.",
       "moduly", "bool", "0", GAME),
    # MT2009_PLUS_PVPFAN_V1: "PVP Fan" - wojny botów z panelu Seban (Wydarzenia -> PVP Fan, /pvpfan w grze)
    _e("M2_PVPFAN", "PVP Fan (wojny botów)",
       "Wojny botów dla zabawy: kategorie, drużyny i ekwipunek w panelu Seban (Wydarzenia → PVP Fan), w grze /pvpfan start|gotowi|stop. "
       "Domyślnie włączony. Bez restartu wyłącza go przełącznik na stronie PVP Fan (flaga m2_pvpfan_off).",
       "moduly", "bool", "1", ["game"] + SEBAN),
    _e("M2_PVPFAN_MAX_CATEGORY", "PVP Fan – postaci w jednej wojnie",
       "Najwięcej postaci jednej kategorii (wszystkie drużyny razem). Panel nie wygeneruje więcej, gra nie wpuści więcej.",
       "moduly", "int", "500", ["game"] + SEBAN, min=2, max=1000),
    _e("M2_PVPFAN_MAX_TOTAL", "PVP Fan – postaci na rdzeń",
       "Najwięcej botów PVP Fan na jednym rdzeniu gry naraz (wszystkie trwające wojny).",
       "moduly", "int", "1000", ["game"], min=2, max=3000),
    _e("M2_PVPFAN_SPAWN_PER_SEC", "PVP Fan – logowania na sekundę",
       "Ile botów wojny loguje się na sekundę po /pvpfan start (500 botów przy 20/s = 25 s). Mniej = lżej dla rdzenia.",
       "moduly", "int", "20", ["game"], min=1, max=100),
    _e("M2_SEONHAE", "Seon-Hae (6/7 bonus)", "NPC Seon-Hae w pierwszych wioskach dodaje 6. i 7. bonus. Domyślnie włączony. Panel klasyczny przełącza go od razu i ustawia czas oczekiwania.",
       "moduly", "bool", "1", GAME),
    _e("M2_TELEPORT_MAP", "Mapa teleportacji (TAB) – autor: Mur4s",
       "TAB otwiera mapę świata z 18 punktami, kliknięcie teleportuje za darmo (bez pierścienia). Wymaga klienta z mapą (uiteleportmap.py). "
       "Wyłączone: TAB działa jak dawniej (Slot 6), a serwer ignoruje mapę. Przełącza się od razu, bez restartu.",
       "moduly", "bool", "0", GAME),
    # MT2009_PLUS_SHOP_QOL_V2: the players' offline shops as big as the bots'
    _e("M2_SHOP_BIG", "Większe sklepy offline graczy",
       "Włączone: okno sklepu offline gracza ma dwie strony obok siebie (160 miejsc, jak sklepy botów); druga strona bez blokad i miejsc premium. "
       "Wyłączone: tylko pierwsza strona – przedmioty, które już stoją na drugiej, zostają w sprzedaży. "
       "Wymaga klienta i serwera z wydania 2.34.0 lub nowszego. Przełącza się od razu, bez restartu; gracz widzi zmianę przy następnym otwarciu okna sklepu.",
       "moduly", "bool", "0", GAME),
    # MT2009_PLUS_SKILL_HACK_V1: the other specialisation's skills beside the main path
    _e("M2_SKILL_HACK", "Umiejętności drugiej ścieżki",
       "Włączone: postać gracza po wybraniu ścieżki (od poziomu 5) może uczyć się i używać także umiejętności drugiej ścieżki "
       "swojej klasy – np. wojownik body Aury Miecza i Duchowego Uderzenia, szaman smok Leczenia. W oknie umiejętności jest "
       "druga zakładka z nazwą tej ścieżki; ta sama pula punktów, księgi, Kamienie Duchowe i 9. umiejętność drugiej ścieżki; "
       "dopalacz i wymiana ksiąg u Seon-Hae tylko dla ścieżki głównej. Boty z tego nie korzystają. "
       "Wyłączone: umiejętności drugiej ścieżki zostają uśpione (poziomy zostają, nie da się ich używać ani rozwijać, "
       "znikają z paska szybkiego dostępu); reset umiejętności oddaje ich punkty. Wymaga klienta Yohara z drugą zakładką. "
       "Przełącza się od razu, bez restartu (także komendą GM /e m2_skill_hack 1 lub 0).",
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
    _e("M2_SIDEKICK", "Towarzysz", "Towarzysz (list „Towarzysz”) dostępny na tym świecie. System towarzysza nie jest dalej rozwijany i może niewłaściwie działać – domyślnie wyłączony; towarzysze graczy zostają w bazie.", "moduly", "bool", "0", GAME),
    _e("M2_BUFFI", "Buffi", "Buffi – szamanka wsparcia (pieczęć 61025/61026, klawisz P): rzuca na właściciela Błogosławieństwo, Pomoc Smoka, a z imieniem także Szybkość i Zwiększenie Ataku. Wyłączony: pieczęcie, imiona i umiejętności zostają.", "moduly", "bool", "1", GAME),
    # MT2009_PLUS_MLODZI_BOHATEROWIE_V1
    _e("M2_MLODZI_BOHATEROWIE", "Bronie dla Młodych Bohaterów",
       "Na poziomie 1, 10, 20, 30, 40, 50, 60 i 70 postać dostaje list i wybiera jedną broń swojej klasy z tego progu "
       "(pominięty próg przepada). Bronie nie dają się wymieniać, sprzedawać, ulepszać ani zmieniać bonusów i znikają "
       "15 dni po otrzymaniu, także założone. Boty też z nich korzystają. Wyłączone: nikt nie dostaje nowych broni, "
       "wydane zostają do końca swoich 15 dni. Działa od następnego startu serwera.",
       "moduly", "bool", "1", GAME),
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
       "siec", "host", "", ["game", "panel", "webclient"] + SEBAN, allow_empty=True, dangerous=True),
    _e("M2_HOST_BIND_ADDRESS", "Adres nasłuchu portów gry",
       "Na jakim adresie komputera wystawić porty gry. 127.0.0.1 = tylko ten komputer, 0.0.0.0 = także gracze z sieci.",
       "siec", "address", "0.0.0.0", ["game", "itemshop", "panel", "seban-panel", "webclient"], dangerous=True,
       suggestions=["0.0.0.0", "127.0.0.1"]),
    _e("M2_PANEL_BIND_ADDRESS", "Adres nasłuchu paneli",
       "To samo dla paneli. 127.0.0.1 trzyma panele przy tym komputerze (dostęp np. przez tunel SSH).",
       "siec", "address", "0.0.0.0", ["panel", "seban-panel"], dangerous=True,
       suggestions=["0.0.0.0", "127.0.0.1"]),
    # MT2009_PLUS_ITEMSHOP_PUBLIC_V1: the ItemShop follows the game's ports, not the panels'.
    _e("M2_ITEMSHOP_BIND_ADDRESS", "Adres nasłuchu ItemShopu",
       "Puste = tak jak porty gry. Gracze otwierają ItemShop z gry, więc na serwerze musi być dostępny z zewnątrz.",
       "siec", "address", "", ["itemshop"], allow_empty=True, dangerous=True,
       suggestions=["", "0.0.0.0", "127.0.0.1"]),
    _e("M2_AUTH_PORT", "Port logowania", "Port serwera logowania. Zmień tylko, gdy 11000 jest zajęty – gracze muszą wtedy dostać nowy port.",
       "siec", "port", "11000", ["game", "panel"], dangerous=True),
    _e("M2_CHANNELS", "Liczba kanałów",
       "Ile kanałów gry uruchomić (każdy ok. 2,5–3 GB RAM). Boty grają na CH2–CH4 tylko z przełącznikami „Drugi/Trzeci/Czwarty kanał”, które same podnoszą tę liczbę. Aktualizator sam poszerzy zakresy portów.",
       "siec", "int", "1", ["game"], min=1, max=4, dangerous=True,
       note="Przy zapisie aktualizator dopasuje zakresy portów gry."),
    _e("M2_GAME_PORT_RANGE", "Zakres portów gry (host)",
       "Porty kanałów otwierane na tym komputerze. 13000-13003 = jeden kanał (13003 - Yohara), 13000-13012 = dwa, 13000-13022 = trzy, 13000-13032 = cztery. Zwykle ustawiane automatycznie.",
       "siec", "portrange", "13000-13003", ["game", "panel"], dangerous=True),
    _e("M2_GAME_CONTAINER_PORT_RANGE", "Zakres portów gry (kontener)",
       "To samo po stronie kontenera – musi mieć tę samą długość co zakres hosta. Zwykle ustawiane automatycznie.",
       "siec", "portrange", "13000-13003", ["game", "webclient"], dangerous=True),
    _e("M2_GAME_PORT_BASE", "Pierwszy port kanałów w kontenerze",
       "Port, od którego rdzenie gry liczą porty kanałów wewnątrz kontenera. 13000, chyba że na tym samym komputerze stoi drugi serwer.",
       "siec", "port", "13000", ["game", "webclient"], dangerous=True),
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
    _e("M2_SEBAN_PANEL_URL", "Adres panelu klasycznego (dla przeglądarki)",
       "Adres panelu klasycznego widziany z przeglądarki – przycisk przejścia między panelami i ikony umiejętności. Puste = http://127.0.0.1:<port panelu>.",
       "panele", "url", "", SEBAN, allow_empty=True),
    # MT2009_PLUS_PANEL_URL_RENAME_V1: the older name of the same setting - a server that already has it keeps it; it
    # counts only while M2_SEBAN_PANEL_URL is empty.
    _e("M2_SEBAN_TIERU_PANEL_URL", "Adres panelu klasycznego (starsza nazwa)",
       "Starsza nazwa ustawienia wyżej, z dawnych instalacji – działa nadal, gdy nowe pole jest puste. Nowe instalacje jej nie mają.",
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

    # ------------------------------------------------------------------ Gra w przeglądarce
    # MT2009_PLUS_WEBCLIENT_SERVICE_V1: the webclient service (linux-port/docker/webclient).
    _e("M2_WEBCLIENT_ON", "Gra w przeglądarce",
       "Włączone: gracze mogą grać w przeglądarce (komputer i telefon) pod http://adres-serwera:port/ – panele pokazują link „Graj w przeglądarce”. "
       "Pierwsze uruchomienie pobiera pliki gry dla przeglądarki (ok. 2 GB, raz). Te same konta co w pobranym kliencie.",
       "webklient", "bool", "1", ["webclient", "panel"] + SEBAN, featured=True),
    _e("M2_WEBCLIENT_PORT", "Port gry w przeglądarce",
       "Port strony z grą (http://adres:7792/). Na VPS otwórz go w zaporze dostawcy, tak jak porty gry.",
       "webklient", "port", "7792", ["webclient", "panel"] + SEBAN, dangerous=True),
    _e("M2_WEBCLIENT_BIND_ADDRESS", "Adres nasłuchu gry w przeglądarce",
       "Puste = tak jak porty gry. To strona dla graczy (jak ItemShop), więc na serwerze musi być dostępna z zewnątrz.",
       "webklient", "address", "", ["webclient"], allow_empty=True, dangerous=True,
       suggestions=["", "0.0.0.0", "127.0.0.1"]),
    _e("M2_WEBCLIENT_PUBLIC_URL", "Własny adres gry w przeglądarce",
       "Tylko gdy stawiasz ją za własną domeną z HTTPS (np. https://gra.example.pl/). Puste = http://adres-serwera:port/.",
       "webklient", "url", "", ["webclient", "panel"] + SEBAN, allow_empty=True),
    _e("M2_WEBCLIENT_ORIGINS", "Dodatkowe dozwolone strony",
       "Inne strony, z których wolno łączyć się z grą (po przecinku, http(s)://host[:port]). Zwykle puste – adres serwera i domena wskazująca na serwer działają same.",
       "webklient", "string", "", ["webclient"], allow_empty=True, pattern=_URL + r"(," + _URL + r")*", hint="np. https://gra.example.pl"),
    _e("M2_WEBCLIENT_SOURCE", "Skąd pobierać pliki gry w przeglądarce",
       "Serwer aktualizacji z plikami gry w przeglądarce. Każdy plik jest sprawdzany sumą SHA-256 z wydania, więc inny serwer niczego nie podmieni. Zostaw.",
       "webklient", "string", "http://141.94.100.53/aktualizacje/webklient-yohara/", ["webclient"],
       pattern=_URL + r"( " + _URL + r")*", hint="adres http(s)://…/ (kilka po spacji)"),
    _e("M2_WEBCLIENT_SOURCE_DIR", "Folder z plikami gry w przeglądarce",
       "Folder na tym komputerze z opublikowanymi plikami zamiast pobierania (instalacja bez internetu). Puste = pobieranie.",
       "webklient", "path", "", ["webclient"], allow_empty=True, dangerous=True),

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
    # MT2009_PLUS_DB_LOG_RETENTION_V1
    _e("M2_DB_LOG_RETENTION_DAYS", "Ile dni trzymać logi w bazie",
       "Wpisy bazy logów (log.log, item_meta_log i inne rosnące tabele logów) starsze niż tyle dni są usuwane raz dziennie "
       "około 5:00, małymi porcjami. 0 = trzymaj wszystko. Domyślnie 3 dni. Statystyki „od początku serwera” "
       "w panelu się nie zmieniają: panel trzyma je w osobnych podsumowaniach. Poniżej 7 dni rankingi „ostatnie 7 dni” "
       "dalej działają (z podsumowań), ale surowa historia, np. kronika świata, będzie krótsza. "
       "To nie są logi plików serwera (te ustawia „Ile godzin trzymać logi serwera”).",
       "baza", "int", "3", SEBAN, min=0, max=365, step=1,
       note="Pierwsze czyszczenie dużej bazy trwa dłużej: tabela log.log bez indeksu po czasie jest wtedy jednorazowo "
            "podmieniana na nową (zachowane dni są przepisywane, stara tabela usuwana – miejsce na dysku wraca od razu). "
            "Stan i wynik ostatniego czyszczenia: Narzędzia → Logi bazy danych."),
    # MT2009_PLUS_SEBAN_SNAPSHOT_RETENTION_V1
    _e("M2_SEBAN_KEEP_FULL_DAYS", "Panel: ile dni pełnych migawek",
       "Panel zaawansowany co 5 minut zapisuje migawki świata (ilość każdego przedmiotu, pozycje botów, oferty na straganach, "
       "mapy, wskaźniki). Przez tyle dni zostają wszystkie, potem są przerzedzane. Zalecane 2. "
       "0 = nic nie usuwaj (tabele rosną bez końca, ok. 150 MB dziennie przy 1000 botów).",
       "baza", "int", "2", SEBAN, min=0, max=30, step=1,
       note="Sprawdzane co godzinę przez kolektor panelu, usuwane małymi porcjami. Pierwsze czyszczenie dużej bazy trwa "
            "kilkadziesiąt minut w tle. Plik bazy nie maleje sam (wolne miejsce jest używane ponownie); "
            "żeby go zmniejszyć, raz ręcznie: OPTIMIZE TABLE."),
    _e("M2_SEBAN_KEEP_HOURLY_DAYS", "Panel: do ilu dni migawki co godzinę",
       "Starsze od pełnych migawki zostają po jednej na godzinę (dla każdego przedmiotu, bota, mapy osobno – ostatnia z godziny), "
       "do tylu dni. Wykres przedmiotu w Ekonomii pokazuje 14 dni. Ilości przedmiotów i mapy są potem usuwane.",
       "baza", "int", "14", SEBAN, min=1, max=90, step=1),
    _e("M2_SEBAN_KEEP_HISTORY_DAYS", "Panel: do ilu dni migawki raz dziennie",
       "Jeszcze starsze migawki ofert na straganach, wskaźników (Yang, poziomy) i sklepów zostają po jednej na dzień "
       "(„ostatnio widziany na rynku” dalej się zgadza co do dnia), do tylu dni. Pozycje botów najwyżej 30 dni. 0 = bez limitu.",
       "baza", "int", "180", SEBAN, min=0, max=3650, step=1),
    _e("M2_SEBAN_KEEP_NEWS_DAYS", "Panel: ile dni kroniki świata",
       "Wpisy kroniki świata i paska wieści w panelu starsze niż tyle dni są usuwane. Kronika pokazuje 14 dni. 0 = trzymaj wszystko.",
       "baza", "int", "30", SEBAN, min=0, max=3650, step=1),
    _e("M2_SEBAN_GEAR_PER_CHARACTER", "Panel: historia ekwipunku na postać",
       "Ile ostatnich wpisów historii ekwipunku (karta postaci) zostaje dla każdej postaci; karta pokazuje 60. "
       "Niezależnie od tego nic starszego niż 60 dni. 0 = bez limitu na postać.",
       "baza", "int", "300", SEBAN, min=0, max=100000, step=50),
    _e("M2_SEBAN_SNAPSHOT_HEAVY_HOURS", "Panel: godziny dużego sprzątania",
       "W tych godzinach (czas serwera, od-do) panel usuwa zaległe stare migawki; w dzień tylko bieżącą, małą część, "
       "żeby nie spowalniać logowania i gry. 3-6 = od 3:00 do 6:00, 0-24 = zawsze, 0-0 = tylko ręcznie.",
       "baza", "string", "3-6", SEBAN, pattern=r"([01]?\d|2[0-4])-([01]?\d|2[0-4])"),
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
       "zaawansowane", "string", "UTC", ["game", "itemshop", "mariadb", "panel", "updater", "webclient"] + SEBAN,
       pattern=r"UTC|[A-Za-z_]+(/[A-Za-z0-9_+-]+){1,2}", hint="np. Europe/Warsaw", suggestions=["Europe/Warsaw", "UTC", "Europe/London", "Europe/Berlin"],
       note="Odtwarza wszystkie kontenery, także bazę danych (gracze zostaną rozłączeni)."),
    _e("M2_LOG_KEEP_HOURS", "Ile godzin trzymać logi serwera",
       "Ile godzin plików logów kanałów (syslog, syserr) trzymać. Gra sama usuwa starsze co godzinę; kanał zapisuje 40–120 MB na godzinę "
       "(48 godzin to 2–6 GB na kanał). To nie są logi bazy danych (te ustawia „Ile dni trzymać logi w bazie”).",
       "zaawansowane", "int", "48", ["game"], min=1, max=2160),
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
       "zaawansowane", "string", "", ALL_DB + ["updater", "webclient"], readonly=True,
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
    _e("M2_SIDEKICK_DEFAULTED", "Znacznik: towarzysz wyłączony", "Znacznik jednorazowej migracji – nie ruszaj.",
       "zaawansowane", "string", "", [], readonly=True, readonly_reason="Znacznik techniczny jednorazowej migracji aktualizacji."),
    _e("M2_SEONHAE_DEFAULTED", "Znacznik: Seon-Hae włączony", "Znacznik jednorazowej migracji – nie ruszaj.",
       "zaawansowane", "string", "", [], readonly=True, readonly_reason="Znacznik techniczny jednorazowej migracji aktualizacji."),
    _e("M2_YOHARA_UPDATES_DEFAULTED", "Znacznik: aktualizator Yohary jako edytor .env", "Znacznik jednorazowej migracji – nie ruszaj.",
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
            return "zakres portów, np. 13000-13003"
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
    "M2_SHOP_BIG": "SHOPBIG",  # MT2009_PLUS_SHOP_QOL_V2
    "M2_ALCHEMY": "RARE",
    "M2_SASHES": "RARE",
    # MT2009_PLUS_SERVER_CONFIG_V1: the monsters' health and damage, percents
    # (web_admin.quest MOB_HP / MOB_ATTACK set the flags on every core).
    "M2_MONSTER_HP": "MOB_HP",
    "M2_MONSTER_ATTACK": "MOB_ATTACK",
    # MT2009_PLUS_PC_ATTACK_V1: the players' damage to monsters (web_admin.quest PC_ATTACK).
    "M2_PLAYER_ATTACK": "PC_ATTACK",
    # MT2009_PLUS_SKILL_HACK_V1: the other specialisation's skills (web_admin.quest SKILL2).
    "M2_SKILL_HACK": "SKILL2",
}


def monster_percent(value):
    """M2_MONSTER_HP / M2_MONSTER_ATTACK / M2_PLAYER_ATTACK as the migrator reads them: default
    (or empty, 0) = 100, easy = 80, else a percent held to 10..300; None for
    anything else (MT2009_PLUS_SERVER_CONFIG_V1)."""
    text = str(value or "").strip().lower().rstrip("%")
    if text in ("", "0", "default", "normal"):
        return 100
    if text == "easy":
        return 80
    if not text.isdigit():
        return None
    return max(10, min(300, int(text)))


def public_schema():
    """What the page needs (descriptions, types, ranges) - no values."""
    return {"version": SCHEMA_VERSION, "sections": SECTIONS, "services": SERVICE_LABELS, "fields": SCHEMA,
            "live": sorted(LIVE_KEYS)}
