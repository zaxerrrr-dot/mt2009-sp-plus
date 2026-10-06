# Zmiany w źródłach exe klienta (`metin2client.exe`)

Pełne kopie zmienionych plików źródła klienta, w układzie katalogów kopii wzorcowej
`/opt/metin2/cache/client-build/Source/Source Client/` (tej kopii nie zmieniamy). Żeby zbudować
exe z tymi zmianami, skopiuj zawartość tego katalogu na drzewo źródeł (nadpisując pliki):

```
for d in UserInterface EterLib EterPythonLib GameLib; do
  cp -a "client-patches/exe/$d/." "<Source Client>/$d/"
done
```

Każda zmiana ma znacznik w komentarzu i jest za `#ifdef` z `Locale_inc.h`, więc wyłączenie
definicji przywraca stary exe.

## Mini gry Owsapa – `MT2009_PLUS_MINIGAMES_V1`

Rumi (Okey), Yut Nori (3D w render target), Złap Króla i Dzieci Kwiatów + widżety `wndMgr` z `ui.py`
Owsapa. Pakiety, nazwy funkcji pythona i różnice względem Owsapa: **[MINIGAMES.md](MINIGAMES.md)**.

| Plik | Zmiana |
|---|---|
| `UserInterface/Locale_inc.h` | `ENABLE_MINI_GAME_RUMI/YUTNORI/CATCH_KING`, `ENABLE_*_EVENT_FLAG_RENEWAL`, `ENABLE_FLOWER_EVENT`, `ENABLE_OWSAP_WNDMGR_EX`, `RENDER_TARGET`, `ENABLE_MOUSE_WHEEL_TOP_WINDOW` |
| `UserInterface/Packet.h` | nagłówki CG 181/182/187/226, GC 181/182/187/238, struktury i podnagłówki (+ `static_assert` rozmiarów) |
| `UserInterface/PythonNetworkStream.cpp/.h`, `PythonNetworkStreamPhaseGame.cpp` | rejestracja GC, `Recv*`/`Send*` (ciała sprawdzane co do rozmiaru) |
| `UserInterface/PythonNetworkStreamModule.cpp` | `net.SendMiniGame*`, `net.SendFlowerEvent*`, stałe |
| `UserInterface/PythonPlayer.cpp/.h`, `PythonPlayerModule.cpp` | stany gier, `YutnoriNotifyMotionDone`, `player.*` Owsapa, `player.GetLevel` |
| `UserInterface/PythonItemModule.cpp`, `PythonApplicationModule.cpp`, `PythonCharacterModule.cpp`, `PythonCharacterManagerModule.cpp` | stałe `item/app/chr/chrmgr`, `app.YutnoriCreate` |
| `UserInterface/PythonYutnoriManager.cpp/.h` | **nowe**: model 20505 w render targecie |
| `UserInterface/PythonApplication.cpp/.h`, `PythonApplicationCamera.cpp` | menedżery render target / Yut Nori, update/deform/render, reset urządzenia, kamera |
| `UserInterface/InstanceBase.cpp/.h` | `SetLODLimits`, `SetAlwaysRender`, `EFFECT_FLOWER_EVENT` |
| `UserInterface/UserInterface.vcxproj(.filters)` | nowe pliki |
| `EterLib/RenderTargetManager.*`, `EterLib/GrpRenderTargetTexture.*` | **nowe**: render target (D3D9) |
| `EterLib/GrpImageInstance.*`, `GrpExpandedImageInstance.*` | odbicie w poziomie, cooltime obrazka, `SetRenderingRectWithScale`, skala wokół środka |
| `EterLib/GrpTextInstance.*` | odstęp linii (`wndMgr.SetLineHeight`) |
| `EterLib/GrpObjectInstance.*`, `GrpBase.h`, `Camera.*`, `eterlib.vcxproj` | „zawsze rysuj”, gettery perspektywy, kamera Yut Nori, nowe pliki |
| `EterPythonLib/PythonWindow.*` | `CMoveTextLine`, `CMoveImageBox`, `CMoveScaleImageBox`, `CCircle`, `CRenderTarget`, rozszerzenia TextLine/ImageBox/AniImageBox (`OnKeyFrame`)/Button (flash, skala, …) |
| `EterPythonLib/PythonWindowManager.*`, `PythonWindowManagerModule.cpp` | rejestracja nowych okien, okno kółka myszy, 57 funkcji `wndMgr` |
| `EterPythonLib/PythonSlotWindow.*` | obrazy przykrywające/podświetlenia slotów, skala, zapamiętanie cooltime’ów, pozycje slotów |
| `EterPythonLib/PythonGraphicImageModule.cpp` | `grpImage.GetGraphicImagePointer` |
| `GameLib/ActorInstance.h`, `ActorInstanceMotion.cpp` | `IsMotionDone` |

Zbudowane (`build.sh msvc --smoke`, MSVC 14.44): `/opt/metin2/cache/exebuild/out/msvc-minigames/metin2client.exe`,
sha256 `f719eb1da1ca8beb0a1370fcfed23a91720a86bbb534515348219c8faafdf65a`; smoke test dochodzi do okna logowania.

## Rangi Punktów Rangi nad głową – `MT2009_PLUS_RANK_POINTS_V1` (`ENABLE_RANK_TITLE`)

Ranga z Punktów Rangi (serwer: `playerbot_rank_points.h`, `server-patches/rankpoints`) w miejscu tytułu rangi za
punkty (alignment), w kolorze rangi; ranga 0 – zwykły tytuł. Pakiety bez zmian: serwer wysyła `RANGA tail <vid>
<ranga>` (komenda czatu), `root/rankpoints.py` woła `chrmgr.SetRankTitle`.

| Plik | Zmiana |
|---|---|
| `UserInterface/Locale_inc.h` | `ENABLE_RANK_TITLE` |
| `UserInterface/InstanceBase.h/.cpp` | `RANK_TITLE_NUM` (16), `m_byRankTitle` (0 przy tworzeniu), `RegisterRankTitle`, `SetRankTitle`, `GetRankTitle` |
| `UserInterface/InstanceBaseEffect.cpp` (nowy w tym katalogu, z client-build) | `g_RankTitleMap`; `RefreshTextTail`: ranga > 0 z zarejestrowaną nazwą – `AttachTitle(nazwa, kolor rangi)` zamiast tytułu rangi za punkty; `SetRankTitle` odświeża ogon |
| `UserInterface/PythonCharacterManagerModule.cpp` | `chrmgr.RegisterRankTitle(ranga, nazwa, r, g, b)`, `chrmgr.SetRankTitle(vid, ranga)` |

Sprawdzone: `clang-cl /Zs` (obraz `mt2009/exebuild-clang:19`, flagi z `out/clang/build.ninja`) –
`InstanceBase.cpp`, `InstanceBaseEffect.cpp`, `PythonCharacterManagerModule.cpp` bez błędów. Exe nie budowane
(`build.sh msvc --smoke` przy najbliższym wydaniu exe).

## Poprawki walki – `MT2009_PLUS_DAMAGE_INFO_GUARD_V1`, `MT2009_PLUS_RECV_TIME_BUDGET_V1`

| Plik | Zmiana |
|---|---|
| `UserInterface/Locale_inc.h` | `ENABLE_DAMAGE_INFO_NULL_GUARD`, `ENABLE_RECV_TIME_BUDGET` |
| `UserInterface/PythonNetworkStreamPhaseGame.cpp` | `RecvDamageInfoPacket`: pakiet obrażeń dla postaci, której klient już nie ma (zniknęła z widoku, trup usunięty), przy zaznaczonym innym celu wołał `pInstTarget->IsPC()` na NULL – losowe zamknięcie klienta w walce. Teraz pakiet jest pomijany. |
| `UserInterface/PythonNetworkStreamPhaseGame.cpp` | `GamePhase`: po pierwszych 8 pakietach w klatce (stary limit) klient czyta dalej, dopóki nie minie 5 ms. W tłumie botów pakiety (ruchy, obrażenia, cele dodatkowych strzał łucznika) nie czekają już kilka klatek, więc dodatkowe strzały lecą razem ze strzałem. |

Zbudowane (`build.sh msvc --smoke`, MSVC 14.44, źródła: client-build + ten katalog): 
`/opt/metin2/cache/exebuild/out/msvc-client-port/metin2client.exe`, sha256
`402d525af2c4ce812b29e9b08f0ffe22a0ebe73ec93730876b40699e5b080aea`; smoke test dochodzi do okna logowania.

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
