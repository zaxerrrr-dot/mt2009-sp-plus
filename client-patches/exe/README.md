# Zmiany w źródłach exe klienta (`metin2client.exe`)

Pełne kopie zmienionych plików źródła klienta, w układzie katalogów kopii wzorcowej
`/opt/metin2/cache/client-build/Source/Source Client/` (tej kopii nie zmieniamy). Żeby zbudować
exe z tymi zmianami, skopiuj zawartość tego katalogu na drzewo źródeł (nadpisując pliki):

```
cp -a client-patches/exe/UserInterface/. "<Source Client>/UserInterface/"
```

Każda zmiana ma znacznik w komentarzu i jest za `#ifdef` z `Locale_inc.h`, więc wyłączenie
definicji przywraca stary exe.

## Menedżer eventów w grze – `MT2009_PLUS_EVENT_MANAGER_V1` (`ENABLE_INGAME_EVENT_MANAGER`)

Po Owsapie (v6.2.6, `PythonInGameEventSystemManager`), ale ogólny: exe nie zna żadnej listy typów
eventów. Serwer (`playerbot_ingame_events.h`, łatka `server-patches/eventmanager`) wysyła listę
eventów, każdy jako **klucz tekstowy** (`catchking`, `rumi`, `easter` …, najwyżej 24 znaki
`[a-z0-9_]`) z włączeniem, startem, końcem, końcem okna odbioru nagród i liczbą (procent raty,
drop). Exe tylko przechowuje tę listę i podaje ją pythonowi.

| Plik | Zmiana |
|---|---|
| `UserInterface/Locale_inc.h` | `#define ENABLE_INGAME_EVENT_MANAGER` |
| `UserInterface/Packet.h` | `HEADER_GC_INGAME_EVENT = 183`, `TPacketGCInGameEvent`, `TPacketGCInGameEventInfo`, `INGAME_EVENT_KEY_MAX_LEN`, podnagłówki `LIST`/`UPDATE` |
| `UserInterface/PythonNetworkStream.cpp` | rejestracja nagłówka 183 jako pakietu dynamicznego (`DYNAMIC_SIZE_PACKET`, rozmiar WORD) |
| `UserInterface/PythonNetworkStream.h` | `RecvInGameEventPacket()` |
| `UserInterface/PythonNetworkStreamPhaseGame.cpp` | `case HEADER_GC_INGAME_EVENT` i `RecvInGameEventPacket()` (zły rozmiar – pakiet przeczytany i pominięty, strumień zostaje zsynchronizowany) |
| `UserInterface/PythonInGameEventSystemManager.h/.cpp` | **nowe**: singleton z listą i moduł pythona `ingameEventSystem` |
| `UserInterface/PythonApplication.h` | include + instancja `m_pyInGameEventSystem` |
| `UserInterface/StdAfx.h`, `UserInterface/UserInterface.cpp` | `initInGameEventSystem()` obok `initAcce()` |
| `UserInterface/UserInterface.vcxproj`, `.vcxproj.filters` | nowe pliki w projekcie |

Nowych funkcji `wndMgr` nie ma – okno eventów (`uiingameevent.py`) używa tylko tego, co exe już ma.

### Pakiet (serwer → klient)

```
HEADER_GC_INGAME_EVENT = 183, dynamiczny:
  BYTE header; WORD size; BYTE subheader; BYTE count;            // 5 bajtów, pack(1)
  count × { char key[25]; BYTE enable; DWORD start_time; DWORD end_time;
            DWORD reward_end_time; int value; }                   // 42 bajty każdy
subheader 0 = LIST (cała lista, zastępuje poprzednią), 1 = UPDATE (tylko te eventy)
```

Czasy to epoki serwera (`app.GetGlobalTimeStamp()`); 0 = brak. Nagłówki 181, 182, 187 i 238 są
zarezerwowane dla Rumi, Yut Nori, Dzieci Kwiatów i Złap Króla (następne porty).

Serwer wysyła pakiet **tylko** klientowi, który napisał `/ingame_event hello <caps>` z bitem 1 –
stary exe zamknąłby się na nieznanym nagłówku. Python (`ingameevent.py`) wysyła bit 1 tylko wtedy,
gdy moduł `ingameEventSystem` istnieje. Bez niego serwer podaje tę samą listę liniami `IGE …`
(bit 2), więc okno eventów działa też na starym exe.

### Moduł pythona `ingameEventSystem`

| Funkcja | Wynik |
|---|---|
| `GetEventCount()` | liczba eventów na liście |
| `GetEventKey(i)` | klucz i-tego eventu (kolejność serwera) |
| `GetActiveEvents()` | krotka kluczy włączonych eventów |
| `GetActiveEventCount()` | ich liczba |
| `IsActive(key)` / `IsEventActive(key)` | 1/0 |
| `IsEvent(key)` | czy klucz jest na liście |
| `GetEventInfo(key)` | `(enable, start, end, rewardEnd, value)`, zera dla nieznanego |
| `GetEventStart(key)`, `GetEventEnd(key)` (= `GetEventEndTime`), `GetEventRewardEnd(key)`, `GetEventValue(key)` | pojedyncze pola |
| `SetEvent(key, enable, start, end, rewardEnd, value)` | wpis z pythona (linie `IGE`, polecenia Owsapa) |
| `RemoveEvent(key)`, `Clear()` | usunięcie |
| `SetInGameEventHandler(obj)` (też `SetIngameEventHandler`), `DestroyInGameEventHandler()` | obiekt, którego `RefreshInGameEvent(True)` exe woła po każdym pakiecie; bez niego woła `BINARY_RefreshInGameEvent()` okna gry |
| stałe `KEY_MAX_LEN` (24), `VERSION` (1) | |

Exe trzyma referencję do obiektu (Owsap trzymał goły wskaźnik) i zwalnia ją w
`DestroyInGameEventHandler()`.

Reszta pythona pyta nie exe, tylko `ingameevent.py` (te same nazwy, plus `GetLeftTime`, `GetFlag`,
nazwy Owsapa `GetInGameEventEnable/…Data/…EndTime/…Count` i stałe `INGAME_EVENT_TYPE_*` jako nasze
klucze) – działa z nowym i ze starym exe. **Nie wolno** dodawać do paczki pliku
`ingameeventsystem.py`: import z paczki jest przed modułami exe i przykryłby listę.

## Jak dodać nowy event bez zmiany exe

Przykład: Walentynki (`valentine`).

1. **Serwer** – rodzaj w harmonogramie: w `playerbot_event_rules.h` nowa wartość `KIND_VALENTINE`
   (przed `KIND_MAX`) i jej nazwa w `KindName` (`"valentine"`). To wystarcza, żeby event był na
   liście graczy pod kluczem `valentine` (każdy rodzaj harmonogramu jest tam automatycznie).
   Jeśli event ma własną flagę (jak `easter_drop`), NPC albo okno nagród – wiersz w `s_defs` w
   `playerbot_ingame_events.h` (klucz, rodzaj, flaga, znaczenie flagi, wartość, druga flaga,
   `*_drop`, `*_reward`, NPC, czy wysyłać polecenie Owsapa). Tekst ogłoszeń: 
   `PlayerBotMiniGameEventName` w `playerbot_events.h`.
2. **Panele** – `EVENT_KINDS` i `EVENT_FLAG_KINDS` (włącz/wyłącz) w `files/admin_panel.py`
   (skopiować też do `linux-port/docker/panel/app/admin_panel.py` – pliki muszą być identyczne),
   tłumaczenie `ev_kind_valentine`; w panelu Sebana `EVENT_KINDS`, `EVENT_FLAG_KINDS`,
   `EVENT_LABELS`, `EVENT_ICONS` (`linux-port/docker/seban-panel/app.py`).
3. **Klient (tylko paczka root)** – jeden wpis w `EVENTS` w `uiingameevent.py`: nazwa (CP1250),
   ikona 45×45, co otwiera przycisk (`'game'` + `RegisterOpener`, `'goblin'`, `'calendar'`,
   `'info'` z `desc`), opcjonalnie `rewards`; klucz w `ORDER` ustala miejsce na liście. W kalendarzu
   (F11) nazwa rodzaju: `KIND_KEYS`/`KIND_NAMES` w `uieventcalendar.py`.
   Klucz bez wpisu też się pokaże – pod swoją nazwą, z kalendarzem pod przyciskiem.

Exe zostaje ten sam: nowy klucz to tylko nowy napis w tym samym pakiecie.

## Sprawdzone

- `clang-cl` (obraz `mt2009/exebuild-clang:19`, flagi z `/opt/metin2/cache/exebuild/out/clang/build.ninja`,
  `/Zs`): `PythonInGameEventSystemManager.cpp`, `PythonNetworkStreamPhaseGame.cpp`,
  `PythonNetworkStream.cpp`, `UserInterface.cpp`, `PythonApplication.cpp` – bez błędów.
- Rozmiary struktur zgodne z serwerem (5 i 42 bajty, `static_assert` po obu stronach w teście).
- Pełnego exe jeszcze nie zbudowano (skrypt budowania w `/opt/metin2/cache/exebuild` jest w toku).
