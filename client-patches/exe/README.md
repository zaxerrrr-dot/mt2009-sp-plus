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

## Poświata przedmiotów (zestawy Arezzo) – `MT2009_PLUS_AREZZO_COSTUME_SETS_V1` (`ENABLE_ITEM_SHINING_TABLE`)

Kostiumy i nakładki na broń z Arezzo mają własne efekty (świecenie, iskry, dym). Arezzo trzyma je w
tabeli „shining” (vnum → plik `.mse`), a nasz exe jej nie miał. Teraz exe czyta opcjonalny plik
`gamedata/shiningtable.txt` (`vnum<TAB>"efekt.mse"[<TAB>"efekt.mse"...]`, `#` – komentarz; format Arezzo)
i dokłada efekty, gdy postać nosi przedmiot o tym vnumie: broń / nakładka na broń – na kość broni (sztylety
na obie ręce), zbroja / kostium – na `Bip01`. Bez pakietów i bez Pythona; bez pliku nic się nie zmienia.
Dane: `client-patches/client-2.0.30/tools/azcostume` (112 wierszy dla 22 zestawów Arezzo).

| Plik | Zmiana |
|---|---|
| `UserInterface/Locale_inc.h` | `#define ENABLE_ITEM_SHINING_TABLE` |
| `GameLib/ItemManager.h/.cpp` | **nowe w tym katalogu** (kopia z `client-build`): `LoadShiningTable`, `GetShiningFiles`, mapa `m_ShiningTable` |
| `UserInterface/PythonApplication.cpp` | `LoadLocaleData`: po `item_scale.txt` wczytuje `gamedata/shiningtable.txt` (brak pliku = tylko wpis w logu) |
| `UserInterface/InstanceBase.h/.cpp` | `__AttachShiningEffect` / `__ClearShiningEffect`, wektory efektów; wołane w `SetArmor` i `SetWeapon` (zmiana zbroi/kostiumu/broni odpina stare efekty), zerowane w `__Initialize` |

Sprawdzone: `clang-cl /Zs` (obraz `mt2009/exebuild-clang:19`, flagi z `out/clang/build.ninja`) dla
`InstanceBase.cpp`, `PythonApplication.cpp`, `GameLib/ItemManager.cpp` na `exebuild/src` + ten katalog –
bez błędów. Exe nie był budowany.

## Exe klienta 2.0.57 (6.10.2026)

Zbudowane `build.sh msvc --smoke` (MSVC 14.44) ze źródeł client-build + cały ten katalog (mini gry, menedżer
eventów, poprawki walki, `ENABLE_RANK_TITLE`, `ENABLE_ITEM_SHINING_TABLE`): `metin2client.exe` 13 669 888 B,
sha256 `a8a53aae116fa91a05a59f87fa9e9aa83f3a67ea6383066f61ae4c4c7204608f` (kopia:
`/opt/metin2/cache/exe-releases/metin2client-a8a53aae.exe`); smoke test dochodzi do okna logowania.

## Nakładki na szarfy z położeniem w modelu – `MT2009_PLUS_ACCE_INITIAL_PLACEMENT_V1` (`ENABLE_ACCE_INITIAL_PLACEMENT`)

Modele skrzydeł Arezzo z katalogu `me_w` (85213, 85219, 85220, 85221) mają szkielet z kością główną w punkcie 0,
a miejsce na plecach w `InitialPlacement` modelu – exe go nie czytał, więc stały obrócone. `EterGrnLib/ThingInstance.cpp`
(nowy w tym katalogu, z client-build): dla części szarfy z kością główną = identyczność i niepustym `InitialPlacement`
macierz położenia idzie przed macierzą szarfy (`GrannyGetModelInitialPlacement4x4`); inne modele bez zmian.
Kopiując ten katalog na źródła, kopiuj też `EterGrnLib`.

Exe 2.0.57 (druga budowa, 6.10.2026): sha256 `1ea7ce73e19eef73b96bb8e92d6762815edec946a47a1a58c36e33d28d6c95a1`,
13 670 400 B (`/opt/metin2/cache/exe-releases/metin2client-1ea7ce73.exe`); smoke test do okna logowania.

**Wyłączone (7.10.2026, `MT2009_PLUS_AREZZO_COSTUME_SETS_V4`):** `#define ENABLE_ACCE_INITIAL_PLACEMENT` w
`UserInterface/Locale_inc.h` jest zakomentowany. Żadna poprawka obrotu (V1–V3, także `acce_fix.txt` na żywo) nie
ustawiła skrzydeł `me_w` poprawnie, a animacja wyglądała kanciasto – właściciel usunął te cztery nakładki (85213,
85219, 85220, 85221) z gry, więc obejście nie jest już potrzebne. Kod w `EterGrnLib/ThingInstance.cpp` zostaje za
flagą (gałąź `#else` = zwykła macierz szarfy); bez flagi exe nie sprawdza już co 2 s pliku `acce_fix.txt`.

## Ekwipunek pasa – `MT2009_PLUS_BELTS_V1` (`ENABLE_NEW_EQUIPMENT_SYSTEM`)

System pasów (**Autor: Digi Rasta**, nowy-system v0.27.0; jego exe ma z tej flagi tylko jej włączenie). Kod pasa jest
w źródle od zawsze, za flagą: `item.EQUIPMENT_BELT`, `item.BELT_INVENTORY_SLOT_START/COUNT/END`,
`player.IsBeltInventorySlot`, `player.IsEquippingBelt`, `player.IsAvailableBeltInventoryCell` (tabela pól jak
`belt_inventory_helper.h` serwera), `app.ENABLE_NEW_EQUIPMENT_SYSTEM` = 1 (root: `BeltInventoryWindow` w
`uiinventory.py`, `uiscript/beltinventorywindow.py`).

| Plik | Zmiana |
|---|---|
| `UserInterface/Locale_inc.h` | `#define ENABLE_NEW_EQUIPMENT_SYSTEM` |

Układ pól bez zmian w pakietach: `c_Inventory_Count` rośnie o 16 pól pasa za zarezerwowanymi polami smoczych kamieni
(`c_Belt_Inventory_Slot_Start` = 225 + 32 + 12 + 18 = 287, `BELT_INVENTORY_SLOT_START` serwera – ta sama suma
z `common/length.h`); pole pasa w wyposażeniu = `c_Equipment_Start + WEAR_BELT` (248), tak jak dotychczasowe
`EQUIPMENT_SLOT_START + 23` z `MT2009_PLUS_BELT_SLOT_V1`.

Sprawdzone 7.10.2026: `build.sh msvc --smoke` (źródła client-build + cały ten katalog z flagą) bez błędów, smoke test
dochodzi do okna logowania; exe testowe 13 672 448 B, sha256 `441d16ab104d86372cb9256b5d6db9718298f1c9750eaf932d1eb95989dcd2ed`
(`/opt/metin2/cache/exe-releases/metin2client-pasy-test.exe`; nie do wydania – exe budować raz na rundę).

## Limity Yang – `MT2009_PLUS_YANG_LIMITS_V1` (`ENABLE_MT2009_YANG_LIMITS`)

**Autor: Digi Rasta** (nowy-system v0.26.0, `SYSTEMY/limity.md`; serwer: `server-patches/yanglimits`). 100 mld przy sobie,
10 mld w jednym handlu, 50 mld cena jednej pozycji sklepu. Pakiety bez zmian (handel, złoto i ceny były już 64-bitowe).

| Plik | Zmiana |
|---|---|
| `UserInterface/Locale_inc.h` | `ENABLE_MT2009_YANG_LIMITS`, `MT2009_YANG_GOLD_MAX` / `_EXCHANGE_GOLD_MAX` / `_SHOP_PRICE_MAX` (jak `common/length.h` serwera; `Server/common/length.h` exe bez zmian) |
| `UserInterface/PythonExchange.h/.cpp`, `PythonExchangeModule.cpp` (nowe w tym katalogu, z client-build) | `GetElkFromSelf/Target` zwracają `YANG`, do pythona jako long |
| `UserInterface/PythonNetworkStream.h`, `PythonNetworkStreamPhaseGame.cpp`, `PythonNetworkStreamModule.cpp` | `SendExchangeElkAddPacket(YANG)`, `net.SendExchangeElkAddPacket` czyta 64 bity |
| `UserInterface/PythonPlayerModule.cpp` | `player.GOLD_MAX` 100 mld (long), nowe `player.EXCHANGE_GOLD_MAX`, `player.SHOP_PRICE_MAX` |

Root (`client-2.0.30/root`: `uiexchange.py`, `shopautoprice.py`, `offlineshopbuilder.py`, `offlineshopmanage.py`) czyta
nowe stałe przez `getattr`, więc ze starym exe zostają dawne limity (8 cyfr w handlu, cena < 2 mld).
## Talizmany i znak żywiołu celu – `MT2009_PLUS_ELEMENTS_V1` (`ENABLE_PENDANT_SYSTEM`, `ENABLE_ELEMENTAL_TARGET`)

Żywioły i talizmany (**Autor: Digi Rasta**, nowy-system 0.28.0; jego exe: te dwie flagi i dwie poprawki niżej). Serwer:
`server-patches/zywioly`. Pakiety bez zmian – siła żywiołów (punkty 178–183) jest tylko na serwerze, pakiet punktów
dalej ma 178 pozycji.

| Plik | Zmiana |
|---|---|
| `UserInterface/Locale_inc.h` | `#define ENABLE_PENDANT_SYSTEM` (`item.EQUIPMENT_PENDANT` = `c_Equipment_Start + WEAR_PENDANT` 25, `item.WEARABLE_PENDANT`, `item.ARMOR_PENDANT`, `app.ENABLE_PENDANT_SYSTEM`), `#define ENABLE_ELEMENTAL_TARGET` (`nonplayer.GetMonsterRaceFlag`, `nonplayer.RACE_FLAG_ATT_*`, `app.ENABLE_ELEMENTAL_TARGET` – ikona żywiołu w `root/uitarget.py`) |
| `UserInterface/PythonNonPlayer.h` (nowy w tym katalogu, z client-build) | `EAIFlags` / `EImmuneFlags` + `ERaceFlags` także pod `ENABLE_ELEMENTAL_TARGET` (moduł ich używa) |
| `UserInterface/PythonNonPlayerModule.cpp` (nowy w tym katalogu, z client-build) | `GetMonsterRaceFlag` zwraca 0 dla vnumu bez rekordu (był dereferencją NULL) |

Sprawdzone 7.10.2026: `build.sh msvc --smoke` (client-build + cały ten katalog) bez błędów, smoke test do okna logowania;
exe testowe 13 679 104 B, sha256 `b43b786b2af48911ac35522b74ffb16d22511792d8a4a6f1d0b40bbac8330bf7`
(`/opt/metin2/cache/exe-releases/metin2client-zywioly-test.exe`; nie do wydania – exe budować raz na rundę).
