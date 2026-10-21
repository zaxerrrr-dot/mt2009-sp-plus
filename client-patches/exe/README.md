# Zmiany w źródłach exe klienta (`metin2client.exe`)

Pełne kopie zmienionych plików źródła klienta, w układzie katalogów kopii wzorcowej
`/opt/metin2/cache/client-build/Source/Source Client/` (tej kopii nie zmieniamy). Żeby zbudować
exe z tymi zmianami, skopiuj zawartość tego katalogu na drzewo źródeł (nadpisując pliki):

```
for d in UserInterface EterLib EterPythonLib GameLib EterGrnLib EffectLib; do
  cp -a "client-patches/exe/$d/." "<Source Client>/$d/"
done
cp -a client-patches/exe/Server/. "<Source>/Server/"   # od Zodiaku: Server/common/length.h klienta
```

Katalog `Server/` **nie** idzie do `Source Client/` (pętla po `*/` musi go pominąć), tylko do `<Source>/Server/`
(obok `Source Client`). Bez tego kroku kompilacja zatrzyma się na `CHAT_TYPE_MISSION`/`SE_SKILL_DAMAGE_ZONE`
(`static_assert` w `Mt2009Zodiak.cpp`).

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

## Wybór z nowy-system 0.28 Digi Rasty (7.10.2026)

Trzy rzeczy z exe Digi Rasty (**Autor: Digi Rasta**), napisane po naszemu w tym katalogu; jeden blok definicji na
końcu `Locale_inc.h` („Digi Rasta picks”).

### Żeńskie tytuły rang – `MT2009_PLUS_FEMALE_TITLES_V1` (`ENABLE_FEMALE_TITLES`)

Jego „Biore (Extended-Alignment): żeńskie formy tytułów rangi nad postaciami”, rozszerzone o nasze rangi Punktów Rangi.

| Plik | Zmiana |
|---|---|
| `UserInterface/InstanceBase.h`, `InstanceBaseEffect.cpp` | `g_TitleNameFemaleMap`, `g_RankTitleFemaleMap`; `RefreshTextTail`: nad kobietą (postać gracza/bota o żeńskiej rasie, `RaceToSex` = 0; przemiana – nigdy) żeńska forma rangi Punktów Rangi i tytułu za punkty, gdy zarejestrowana |
| `UserInterface/PythonCharacterManagerModule.cpp` | `chrmgr.RegisterTitleNameFemale(stopień, nazwa)`, `chrmgr.RegisterRankTitleFemale(ranga, nazwa)` |

Root: `rankpoints.py` (`TIERS_FEMALE`: Waleczna, Mocarna, Potężna, Władczyni, Arcymistrzyni – Legenda bez zmian;
`ALIGNMENT_FEMALE`: Rycerska … Okrutna; rejestracja przez `hasattr`, po angielsku bez form żeńskich),
`introloading.py` (`RegisterFemaleTitles`), `uicharacter.py` (tytuł i ranga w oknie postaci kobiety).

### Opcje dodatkowe: ukrywanie efektów i sklepów, zapis czatu – `MT2009_PLUS_DIGI_CLIENT_QOL_V1` (`ENABLE_DIGI_CLIENT_QOL`)

Funkcje exe, na które od 0.19.0 czekało okno „Opcje dodatkowe” (`root/uiopcjedodatkowe.py`, wiersze bez funkcji exe były
ukryte). Wcześniej tylko łatka `client-patches/exe-digi-client-qol/digi-client-qol.patch`, której nikt nie nakładał –
teraz w nakładce. Kod własny: jego notatki (`DOKUMENTACJA/biore.md`) mówią, że paczki z tymi pomysłami (Hide-Objects,
BL_HIDE_EFFECT) są na GPL – z nich wzięte są tylko nazwy plików efektów (dane) i miejsca haczyków.

| Plik | Zmiana |
|---|---|
| `UserInterface/Mt2009ClientQol.cpp` (**nowy**) | `app.SetHideEffects(wzmocnienia, aury)`, `app.SetChatLog(wł)`, `chrmgr.SetShopsVisible(wł)`; listy efektów (wzmocnienia szamana, aury umiejętności), zapis czatu do `logs/czat_RRRR-MM-DD.txt` bez kodów kolorów |
| `EffectLib/EffectInstance.cpp` (**nowy katalog**, z client-build) | `CEffectInstance::OnRender` pomija efekt z listy (`Mt2009DigiQol_IsEffectHidden`, bez definicji nigdy nie ukrywa) |
| `UserInterface/PythonIkarusShop.cpp` (z client-build) | ukryte sklepy offline (encje ikashop) jak „za daleko”: bez modelu, napisu i klikania |
| `UserInterface/PythonChat.cpp` (z client-build) | `AppendChat` / `AppendWhisper` → zapis czatu |
| `UserInterface/UserInterface.cpp`, `UserInterface.vcxproj(.filters)` | rejestracja funkcji, nowy plik |

### Model 3D w Kartach Potworów – `MT2009_PLUS_MONSTER_CARD_MODEL_V1` (`ENABLE_MONSTER_CARD_MODEL`)

API jego `Mt2009Window.cpp` (`player.Mt2009Model*`, którego `root/monstercard.py` szuka przez `hasattr`), zrobione na
naszym render targecie z mini gier (`CRenderTargetManager`, `UI::CRenderTarget`, `CInstanceBase` jak Yut Nori) – bez
jego render-to-texture i bez jego kodu mini gier.

| Plik | Zmiana |
|---|---|
| `UserInterface/Mt2009MonsterModel.cpp` (**nowy**) | podgląd: `player.Mt2009ModelSelect(rasa)` (0 – brak danych rasy, okno pokazuje obrazek karty), `Show`, `Rotation`, `Zoom`, `UpDown`, `Reset`, `Motion` (kolejne ruchy rasy raz, potem stanie); kadr raz z wysokości i sfery modelu; tekstura 480×612 rysowana w polu 240×306; model nieprzezroczysty w teksturze (przebieg tylko alfy) |
| `EterLib/RenderTargetManager.h` | `RENDER_TARGET_INDEX_ILLUSTRATED` (1, po Yut Nori) |
| `EterLib/Camera.h/.cpp` | własna kamera `DEFAULT_MONSTER_MODEL_CAMERA` |
| `UserInterface/PythonApplication.cpp`, `PythonApplicationModule.cpp` | update/deform/render obok Yut Nori, zniszczenie; `app.RENDER_TARGET_INDEX_ILLUSTRATED` |

## Świątynia Zodiaku – `MT2009_PLUS_ZODIAC_V1` (`ENABLE_12ZI`)

**Autor: Digi Rasta** (nowy-system 0.35.0, system po paczce WLsj24 „ZodiacTemple”). Zmiany exe z paczki
(`klient-zrodlo/zodiak-klient-exe.diff`) wpięte w nasze źródło; serwer: `server-patches/zodiak`.

| Plik | Zmiana |
|---|---|
| `Server/common/length.h` (**nowy w nakładce**, z client-build; kopiowany do `<Source>/Server/common/`) | `CHAT_TYPE_MISSION/SUB_MISSION/CLEAR_MISSION` = 13…15 przed `CHAT_TYPE_MAX_NUM`; 15 `SE_*` Zodiaku po `SE_EFFECT_ACCE_EQUIP` (pierwszy = 39) – jak w `common/length.h` serwera; **bez** `#ifdef` (wszystkie pliki muszą widzieć te same enumy) |
| `UserInterface/Locale_inc.h` | `ENABLE_12ZI` |
| `UserInterface/Mt2009Zodiak.cpp/.h` (**nowe**) | odbiór GC 220 (`RecvSpecialZodiacEffect`, efekt w punkcie x/y), `CInstanceBase::AttachSpecialZodiacEffect`, `Mt2009Zodiak_EffectFromSE`; `chrmgr.IsDead(vid)`, `chrmgr.IsPC(vid)`; stałe `app.ENABLE_12ZI`, `chat.CHAT_TYPE_*MISSION`, `chr.NEW_AFFECT_CZ_UNLIMIT_ENTER` (600), `chrmgr.EFFECT_*`; `static_assert`: numery czatu/efektów jak na serwerze, GC 220 = 15 B |
| `UserInterface/Packet.h` | `HEADER_GC_SEPCIAL_ZODIAC_EFFECT = 220`, `TPacketGCSpecialZodiacEffect` (header, type, type2, vid, x, y) |
| `UserInterface/PythonNetworkStream.cpp/.h`, `PythonNetworkStreamPhaseGame.cpp` | rejestracja i obsługa GC 220; czat `MISSION`/`SUB_MISSION`/`CLEAR_MISSION` → `game.py` `BINARY_SetMissionMessage` / `BINARY_SetSubMissionMessage` / `BINARY_CleanMissionMessage` (tablica misji, nie czat) |
| `UserInterface/PythonNetworkStreamPhaseGameItem.cpp` (z client-build) | `SE_*` Zodiaku w pakiecie efektu specjalnego (114) → efekty Zodiaku |
| `UserInterface/InstanceBase.h` | 15 `EFFECT_*` Zodiaku (po `EFFECT_FLOWER_EVENT`, w kolejności `SE_*`), `AttachSpecialZodiacEffect` |
| `UserInterface/PythonPlayerSettingsModule.cpp` (z client-build) | pliki efektów: `d:/ymir work/effect/monster2/12_shelter_in_01…08`, `12_*_drop`, `daepo_na_02_boom.mse` (paczka `nowy_system_zodiak`) |
| `UserInterface/PythonChat.cpp` | kolory trzech typów czatu misji |
| `GameLib/ActorInstanceBattle.cpp` (z client-build) | `IS_HUGE_RACE`: bossowie Zodiaku 2750–2862 nie są odpychani |
| `UserInterface/UserInterface.cpp`, `UserInterface.vcxproj(.filters)` | `Mt2009Zodiak_RegisterPython`, nowy plik |

Pominięte względem paczki: wycinek „zegarowy” obrazka (`RenderCoolTime`, `CImageBox::SetCoolTime/SetCoolTimeStart`,
`wndMgr.SetCoolTimeImageBox` / `SetStartCoolTimeImageBox`) – mamy go już z mini gier (`MT2009_PLUS_MINIGAMES_V1`,
`ENABLE_OWSAP_WNDMGR_EX`), te same nazwy w Pythonie, więc `GrpImageInstance.*`, `GrpExpandedImageInstance.*` i
`PythonWindow.*` bez zmian. Polecenia serwera Zodiaku (`ZodiacTime`, `Bead_*`, `OpenReviveDialog`…) obsługuje `game.py`.


## Exe 3.0 „Yohara” – Poziom Czempiona, Sung Ma, Hydra (`MT2009_PLUS_CHAMPION_V2`, `MT2009_PLUS_SHIP_DEFENSE_V2`)

Etap B Czempiona (`server-patches/czempion/README.md`, „Etap B”). **Zmienia protokół** (pakiet punktów, pakiety postaci) –
klient 3.0 jest wymuszony: root `constinfo.py` mówi 1.3.0 tylko z tym exe, auth odrzuca starsze („UPDATE”).

| Plik | Zmiana |
|---|---|
| `UserInterface/Locale_inc.h` | `ENABLE_CONQUEROR_LEVEL`, `ENABLE_CONQUEROR_UI` (`app.*` = 1), `ENABLE_MT2009_SHIP_DEFENSE_CLIENT` |
| `Server/common/length.h` | punkty serwera za szarfą (bez `#ifdef`): `POINT_ENCHANT_*` 178–183, `POINT_SUNGMA_*` 184–187, `POINT_CONQUEROR_*` 188–192; `POINT_MAX_NUM` 178 → **193** (= `POINT_PACKET_NUM` serwera) |
| `Server/common/item_length.h` (**nowy w nakładce**, z client-build) | `LIMIT_CONQUEROR_LEVEL` = 10 |
| `UserInterface/Packet.h` | `dwConquerorLevel` na końcu `TPacketGCCharacterAdditionalInfo` (70 B) i `TPacketGCCharacterUpdate` (52 B) |
| `UserInterface/NetworkActorManager.h/.cpp`, `PythonNetworkStreamPhaseGameActor.cpp` (**nowe w nakładce**) | poziom Czempiona z pakietów do `SNetworkActorData`/`SNetworkUpdateActorData` → `CInstanceBase::SetConquerorLevel` |
| `UserInterface/InstanceBase.h/.cpp`, `InstanceBaseEffect.cpp` | `m_dwConquerorLevel`, `Get/SetConquerorLevel`; `UpdateTextTailLevel`: gracz z Poziomem Czempiona ma nad głową „Lv N” Czempiona na niebiesko (85,185,255) |
| `UserInterface/PythonPlayer.cpp` | `SetStatus(POINT_CONQUEROR_LEVEL)` – własny niebieski poziom |
| `UserInterface/Mt2009Champion.cpp` (**nowy**) | `player.CONQUEROR_LEVEL/_LEVEL_STEP/_EXP/_NEXT_EXP/_POINT/_LEVEL_MAX`, `player.SUNGMA_STR/HP/MOVE/IMMUNE` (+ `SUNGMA_INMUNE` GF), `player.POINT_*` (15), `player.GetConquerorEXP/GetConquerorNextEXP/GetConquerorLevel`, `item.APPLY_SUNGMA_*`, `item.APPLY_ENCHANT_*`, `item.LIMIT_CONQUEROR_LEVEL`, `app.MT2009_CHAMPION_EXE`; `static_assert` numerów i rozmiarów (jak serwer) |
| `UserInterface/UserInterface.cpp`, `UserInterface.vcxproj(.filters)` | rejestracja, nowy plik |
| `GameLib/ActorInstanceBattle.cpp` | `IS_HUGE_RACE`: Hydra 3960–3962 (nie jest odpychana, efekt trafienia w miejscu ciosu, zasięg umiejętności −200) |
| `UserInterface/PythonPlayerSkill.cpp` (**nowy w nakładce**) | na `metin2_defensewave` umiejętność w olbrzymią rasę (Hydra) albo z `IGNORE_BLOCK` (`IsIgnoreTarget`) nie sprawdza „cel stoi na blokadzie” – Hydra stoi w morzu (Owsap `IsIgnoreBlock`) |

Root (klient 2.0.30 → 3.0): strona **Sung Ma** zakładki statusu w `uicharacter.py` + `uiscript/characterwindow.py`
(okno o 24 px wyższe, dwa przyciski GF `old_level_btn`/`new_level_btn` pod wierszem poziomu, ikony `char_info_sungma_*`
w miejscu STR/DEX/VIT/INT, wolne punkty i „+” → `/conqueror_stat smh_*`, wiersz poziomu pokazuje Poziom Czempiona i
jego exp na niebiesko, wartość poniżej wymagań mapy na czerwono). Klawisz „Czempion” (`keybind.py`) otwiera tę stronę;
`uichampion.py` (Etap A) usunięty; `uicharacternew.py` GF nie jest używany (brak w nim naszych części okna).
Grafiki są już w kliencie bazowym: `d:/ymir work/ui/game/windows/char_info_sungma_*.sub`, `old/new_level_btn_0*.sub`
(paczka `etc`) wskazują na `d:/ymir work/ui/windows.dds` (512×940, wersja GF – sprawdzone 13.10.2026 wycinkiem).

Zbudowane 13.10.2026 (`build.sh msvc --smoke`, MSVC 14.44; źródła: kopia client-build + cały ten katalog, jak exe 2.0.63 –
`/opt/metin2/cache/exe-yohara/Source`): `metin2client.exe` 13 700 096 B, sha256
`75d7825064b7cb42cd6e42f6117ca04300c49d88dae9acef3d5242a33ab8403a` (`/opt/metin2/cache/exe-releases/metin2client-75d78250.exe`,
`/opt/metin2/cache/yohara/exe-out/`); smoke test dochodzi do okna logowania. Drugi smoke z root 3.0 (tylko do testu: hak w
`intrologin.py` otwiera dwa okna postaci przy logowaniu) – strona zwykła i Sung Ma rysują się bez błędów
(`exe-out/smoke-character-window.png`; liczby to śmieci, bo nie ma postaci).

## Umiejętności 9. (Yohara) – `MT2009_PLUS_SKILL9_V1` (`ENABLE_NINTH_SKILL`)

Ruchy 9. umiejętności na wszystkich 8 rasach (`server-patches/skill9/README.md`). Exe 2.0.25 rejestruje ruchy umiejętności
sam (nie Python), więc bez tej zmiany klient nie zagra Trzęsienia itd. Indeks ruchu = kolumna „motion” skilldesc:
9 (pierwsza droga), 24 (druga), +25 na stopień (`SKILL_GRADEGAP`); pliki z klienta GF (paczka `yskill9`,
`client-2.0.30/tools/yskill9`). Protokół bez zmian – bramka wersji 3.0 zostaje jak jest.

| Plik | Zmiana |
|---|---|
| `UserInterface/Locale_inc.h` | `ENABLE_NINTH_SKILL` |
| `UserInterface/PythonPlayerSettingsModule.cpp` | wojownik `{9, "finish"}`; ninja `{9, "ilgangpyo"}`, `{24, "pungraepo"}`; sura `{9, "akgi"}`, `{24, "akgi_dark"}`; szaman `{9, "meteo"}`, `{24, "chunwoon"}` (+ ich `.msa` 1. stopnia na liście ręcznej) |

Zbudowane 14.10.2026 (`build.sh msvc --smoke`, MSVC 14.44; źródła: client-build + cały ten katalog = exe 3.0 + ta zmiana,
`/opt/metin2/cache/yohara/yskill9-exe/Source`): `metin2client.exe` 13 700 608 B, sha256
`f3679ead1079e00f4b02d20f68c6466d3d90d9ae2a91b335dd5a9273f273aebf` (`/opt/metin2/cache/yohara/yskill9-exe/out/`); smoke
test dochodzi do okna logowania.

## Druga runda exe Yohary – Rękawice Sung Ma, Precyzja, procent Woli, exp Czempiona (`MT2009_PLUS_YOHARA_EXE2_V1`, `ENABLE_MT2009_YOHARA_EXE2`)

Serwer: `server-patches/rekawice`, `precyzja`, `obreczjadeitu2` (+ `playerbot_yohara_gear.cpp`). **Protokół bez zmian**
– pakiet punktów dalej 193 punkty, bramka wersji 3.0 (1010300) zostaje: stary exe 3.0 pomija nowe zmiany punktu
(typ ≥ 193), nowe miejsce rękawic dostaje dopiero z tym exe (root sprawdza `app.ENABLE_GLOVE_SYSTEM`/`item.EQUIPMENT_GLOVE`).

| Plik | Zmiana |
|---|---|
| `UserInterface/Locale_inc.h` | `#define ENABLE_GLOVE_SYSTEM` (było wyłączone: `item.EQUIPMENT_GLOVE` = `c_Equipment_Start + WEAR_GLOVE` 26, `item.ARMOR_GLOVE`, `item.WEARABLE_GLOVE`, `app.ENABLE_GLOVE_SYSTEM` = 1), `#define ENABLE_MT2009_YOHARA_EXE2` |
| `Server/common/length.h` | `POINT_PACKET_NUM` (193) za punktami Czempiona, potem `POINT_SUNGMA_PER_STR/HP/MOVE/IMMUNE` 193–196 i `POINT_HIT_PCT` 197 – `POINT_MAX_NUM` 198 (serwer tak samo); `FLY_CONQUEROR_EXP = 30` |
| `Server/common/item_length.h` | `METIN_SUNGMA` (2) – Kamień (Mocy) Demonów |
| `UserInterface/Packet.h` | `TPacketGCPoints::points[POINT_PACKET_NUM]` (773 B jak dotąd) |
| `UserInterface/PythonNetworkStreamPhaseLoading.cpp` (**nowy w nakładce**, z client-build) | `__RecvPlayerPoints` czyta 193 punkty pakietu |
| `UserInterface/PythonPlayerModule.cpp` | `player.CanAttachMetin`: `METIN_SUNGMA` jak zwykły kamień (puste gniazdo; pasujące flagi `WEARABLE_GLOVE`) |
| `UserInterface/PythonPlayerSettingsModule.cpp` | `FLY_CONQUEROR_EXP` → `d:/ymir work/effect/etc/conqueror_exp/ga_piece_orange_small.msf` (GF, root `client-2.0.30/atlas/d_`) |
| `UserInterface/Mt2009Champion.cpp` | `static_assert` nowych numerów (193/196/197/198, `METIN_SUNGMA` 2, `FLY_CONQUEROR_EXP` 30, `WEAR_GLOVE` 26, `ARMOR_GLOVE` 8, `WEARABLE_GLOVE`); `player.SUNGMA_PER_STR/HP/MOVE/IMMUNE`, `player.HIT_PCT` (+ `player.POINT_*`), `item.APPLY_SUNGMA_PER_*`, `item.APPLY_HIT_PCT`, `item.METIN_SUNGMA`, `effect.FLY_CONQUEROR_EXP`, `app.MT2009_YOHARA_EXE2` |

Root (`client-2.0.30/root`): miejsce rękawic w `uiscript/inventorywindow.py` (prawa kolumna pod naszyjnikiem; przycisk
Smoczych Kamieni pomniejszony `wndMgr.SetButtonScale` między strzałą a kolczykami – tylko z tym exe), `uiinventory.py`;
`uitooltip.py` + `yoharagear.py` (kamienie w rękawicach, kamień Demonów, gniazda Obręczy Jadeitu, nazwa „Rękawice”);
`uitaskbar.py` (nowy w tym katalogu, z paczki root: exp Czempiona w tych samych czterech kulach, niebieskich –
`mt2009_conqueror_exp_point.tga` wycięty z `taskbar.tga` GF); `sungmastate.py` + `game.py` (ikony Sung Ma na pasku
afektów: buff na mapie Sung Ma, debuff każdej statystyki poniżej wymagań i za małej Precyzji – `.sub` GF z
`skill9_common.dds` paczki `yskill9`, bez niej ikony okna postaci); `uicharacter.py` (statystyki z procentem Woli);
`localeinfo_point.py` (nazwy 193–197); `constinfo.py` (jadeit → Obręcz Jadeitu).

Też w tej rundzie (błąd 1 z testów – znikająca 9. umiejętność): `UserInterface/PythonNetworkStreamPhaseGame.cpp`
`RecvSkillLevelNew` – pod `ENABLE_NINTH_SKILL` exe nie czyści już miejsca 7 okna umiejętności (`SetSkill(7, 0)`) ani nie
oddaje go umiejętnościom języków 112–115; miejsce 7 to 9. umiejętność (root). Miejsce 8 bez zmian. Obejście w pythonie
(`RestoreNinthSkillSlot`) może zostać – nic nie psuje.

Zbudowane 14.10.2026 (`build.sh msvc --smoke`, MSVC 14.44; źródła: client-build + cały ten katalog,
`/opt/metin2/cache/yohara/exe-src4/Source`): `metin2client.exe` 13 703 680 B, sha256
`eb9ed5e31d63798b3b5062ace297c5c17da22e3b42bc4f49a0615d62d59ce8e4` (`/opt/metin2/cache/yohara/exe-out4/`); smoke test
dochodzi do okna logowania. Drugi smoke z rootem tej rundy (tylko do testu: hak w `intrologin.py`, `exe-out4/smoke2`):
okno ekwipunku z miejscem rękawic (`EQUIPMENT_GLOVE` 251, `HIT_PCT` 197, `app.MT2009_YOHARA_EXE2` 1) i ikony Sung Ma
na pasku afektów rysują się bez błędów (`exe-out4/smoke-inventory-affects.png`, `smoke-equipment-zoom.png`); dymków
rękawic klient testowy nie pokazał – jego paczki nie wczytały nowych rekordów `item_proto` (`dbdata`), więc dymki
sprawdzone tylko kompilacją i testem funkcji `yoharagear.py`.

## Szata Aury – efekt szaty na postaciach (`MT2009_PLUS_AURA_V1`, `ENABLE_MT2009_AURA`)

Serwer: `server-patches/aura` (+ `playerbot_aura.cpp`). **Protokół bez zmian** – zamiast `PART_AURA` Owsapa w pakietach
postaci serwer wysyła komendę czatu `AURA view <vid> <vnum>` (gdy postać wchodzi w pole widzenia i gdy jej szata się
zmienia); root (`uiaura.py`) woła `chrmgr.SetAura`. Stary exe nie ma tej funkcji – root nic nie rysuje, reszta działa
(miejsce szaty, okna u Theowahdana, dymki to sam python). Nowych nagłówków ani pól pakietów nie ma.

| Plik | Zmiana |
|---|---|
| `UserInterface/Locale_inc.h` | `#define ENABLE_MT2009_AURA` |
| `UserInterface/Mt2009Aura.cpp` (**nowy**) | `CInstanceBase::SetAura/RegisterAuraEffect/__AttachAuraEffect` (efekt `.mse` na kości `Bip01 Spine2` jak u Owsapa; nie na polimorfii ani „zwierzęcym” stroju), `CNetworkActorManager::SetActorAura`, `chrmgr.RegisterAuraEffect(vnum, plik)`, `chrmgr.SetAura(vid, vnum)`, `chrmgr.GetAura(vid)` |
| `UserInterface/InstanceBase.h/.cpp` | `m_dwAuraVnum`, `m_dwAuraEffect` (zerowane w `__Initialize`); `ChangeArmor` przypina efekt znowu po `SetRace` (który czyści wszystkie efekty) |
| `UserInterface/NetworkActorManager.h/.cpp` | `SNetworkActorData::m_dwAura` (kopiowane, zerowane) – nowa instancja aktora (wejście w zasięg wzroku, wierzchowiec) dostaje szatę z danych; `ms_pkAuraInstance` (menedżer strumienia sieci, dla pythona) |
| `UserInterface/PythonCharacterManagerModule.cpp` | rejestracja trzech funkcji `chrmgr` |
| `UserInterface/UserInterface.vcxproj(.filters)` | `Mt2009Aura.cpp` |

Pliki efektów (GF 26.1.11, `d:/ymir work/pc/common/effect/aura/aura_01_49_001.mse` … `aura_250_006.mse` + tekstury i
skrzydełka `wing_lv06.mde`) są w paczce root (`client-2.0.30/atlas/d_`); `uiaura.EFFECTS` rejestruje je dla 49101–49106.

Sprawdzone: `clang-cl /Zs` (obraz `mt2009/exebuild-clang:19`, flagi z `out/clang/build.ninja`, źródła: client-build + cały
ten katalog, casefix) – `Mt2009Aura.cpp`, `InstanceBase.cpp`, `NetworkActorManager.cpp`, `PythonCharacterManagerModule.cpp`
bez błędów. Exe nie budowane (wspólna budowa później: `build.sh msvc --smoke`).

## Dodatkowy ekwipunek – `MT2009_PLUS_EKWIPUNEK_V1` (`ENABLE_SPECIAL_STORAGE`)

Specjalny magazyn z Amerii (`server-patches/ekwipunek/README.md`): pięć magazynów kategorii serwera jako okna
przedmiotów 11–15 (Materiały ulepszeń, Księgi, Kamienie Duszy, Zaczarowania, Skrzynie), po 4 strony 5 × 9. **Bez
zmian pakietów** – pozycja przedmiotu (`TItemPos`) i wszystkie funkcje `net.*` z oknem (`SendItemMovePacket`,
`SendItemUsePacket`, `SendItemUseToItemPacket`, `SendSafeboxCheckin/CheckoutPacket`, `SendExchangeItemAddPacket`)
już niosą okno; exe tylko przechowuje i podaje przedmioty nowych okien. Okno w pythonie: `root/uiekwipunek.py`.

| Plik | Zmiana |
|---|---|
| `UserInterface/Locale_inc.h` | `#define ENABLE_SPECIAL_STORAGE` |
| `Server/common/length.h` | `EMt2009SpecialStorage` (`SPECIAL_INVENTORY_PAGE_*`, `SPECIAL_INVENTORY_MAX_NUM` 180, `SPECIAL_INVENTORY_WINDOW_COUNT` 5), okna `UPGRADE_INVENTORY` … `CHEST_INVENTORY` po `IKASHOP_AUCTION` (11–15, numery serwera), `Mt2009IsSpecialWindow`, `TItemPos::IsValidItemPosition` |
| `UserInterface/GameType.h` | `c_Special_Inventory_Page_Size/Count`, `c_Special_ItemSlot_Count`; `SLOT_TYPE_UPGRADE_INVENTORY` … `SLOT_TYPE_CHEST_INVENTORY` przed `SLOT_TYPE_MAX` |
| `UserInterface/GameType.cpp` (nowy w tym katalogu, z client-build) | `c_aSlotTypeToInvenType`: pięć nowych typów slotów → okna (`player.SlotTypeToInvenType`, depozyt) |
| `UserInterface/PythonPlayer.h/.cpp` | `TPlayerStatus::aSpecialItem[5][180]` (zerowane jak reszta przez `memset` w `Clear`), `GetItemData`/`SetItemData` dla okien 11–15, `GetItemCountByVnum` liczy też magazyny (okno ulepszania i craftingu pokazują materiały jak w Amerii) |
| `UserInterface/PythonPlayerSkill.cpp` | `__HasItem` szuka też w magazynach (jak w Amerii) |
| `UserInterface/PythonPlayerModule.cpp` | `player.UPGRADE_INVENTORY` … `CHEST_INVENTORY`, `player.SLOT_TYPE_*_INVENTORY`, `player.SPECIAL_PAGE_SIZE` (45), `SPECIAL_PAGE_COUNT` (4), `SPECIAL_SLOT_COUNT` (180) |

Stary exe dostaje pakiety przedmiotów z oknem 11–15 i je pomija (`TItemPos::IsValidItemPosition` = false) – bez
awarii; dlatego serwer kieruje przedmioty do magazynów dopiero po `/ekwipunek hello`, które `uiekwipunek.py` wysyła
tylko, gdy `player.UPGRADE_INVENTORY` istnieje.

Sprawdzone: `clang-cl /Zs` (obraz `mt2009/exebuild-clang:19`, flagi z `out/clang/build.ninja`, drzewo
`exebuild/src` + ten katalog) – `GameType.cpp`, `PythonPlayer.cpp`, `PythonPlayerModule.cpp`, `PythonPlayerSkill.cpp`,
`PythonNetworkStreamPhaseGameItem.cpp` bez błędów. Exe nie budowane (`build.sh msvc --smoke` przy najbliższym
wydaniu exe).

## Bonus Switcher (switchbot z Amerii) – `MT2009_PLUS_SWITCHBOT_V1` (`ENABLE_SWITCHBOT`)

Switchbot z Ameria Project (`srcs/client/UserInterface/PythonSwitchbot.cpp`, `ENABLE_SWITCHBOT` + `ENABLE_SWITCHBOT_RENEWAL`)
zamiast naszej „Zmiany bonusów” (sam python). Serwer: `server-patches/switchbot` + `playerbot_switchbot.cpp` (opis zasad w
`server-patches/switchbot/README.md`). Okno w pythonie: `root/uiswitchbot.py` (Amerii).

| Plik | Zmiana |
|---|---|
| `UserInterface/Locale_inc.h` | `#define ENABLE_SWITCHBOT` |
| `Server/common/length.h` | `SwitchbotValues` (`SWITCHBOT_SLOT_COUNT` 5, `SWITCHBOT_ALTERNATIVE_COUNT` 5, `SWITCHBOT_ATTR_COUNT` 5), okno `SWITCHBOT` = 16 (po `CHEST_INVENTORY`, numer serwera), `TItemPos::IsValidItemPosition` (pole < 5) |
| `UserInterface/GameType.h`, `GameType.cpp` | `SLOT_TYPE_SWITCHBOT` przed `SLOT_TYPE_MAX` → okno `SWITCHBOT` |
| `UserInterface/PythonPlayer.h/.cpp` | `TPlayerStatus::aSwitchbotItem[5]`, `GetItemData`/`SetItemData` dla okna `SWITCHBOT` |
| `UserInterface/PythonPlayerModule.cpp` | `player.SWITCHBOT`, `player.SLOT_TYPE_SWITCHBOT` |
| `UserInterface/Packet.h` | `HEADER_CG_SWITCHBOT = 170`, `HEADER_GC_SWITCHBOT = 171` (wolne po obu stronach), `TSwitchbotAttributeAlternativeTable` (15 B), `TSwitchbotTable` (409 B), `TSwitchbotAttributeInfo` (9 B), `TPacketCGSwitchbot`/`TPacketGCSwitchbot` (5 B, `WORD size`), `TSwitchbotUpdateItem` (44 B) + `static_assert` (serwer ma te same) |
| `UserInterface/PythonNetworkStream.cpp/.h`, `PythonNetworkStreamPhaseGame.cpp` | GC 171 jako pakiet dynamiczny, `case HEADER_GC_SWITCHBOT`, deklaracje `RecvSwitchbotPacket` / `SendSwitchbotStartPacket` / `SendSwitchbotStopPacket` |
| `UserInterface/PythonSwitchbot.h/.cpp` | **nowe**: `CPythonSwitchbot` Amerii (stan pól, alternatywy, bonusy i maksima zestawów), ciała `Recv`/`Send` (zły rozmiar – pominięty, strumień zsynchronizowany), moduł `switchbot` (`IsActive`, `IsFinished`, `GetAttribute`, `SetAttribute`, `GetAttributesForSet`, `GetAttributeMaxValue`, `ClearSlot`, `Start`, `Stop`, `SLOT_COUNT`, `ALTERNATIVE_COUNT`, `ATTR_COUNT`) |
| `UserInterface/PythonApplication.h`, `StdAfx.h`, `UserInterface.cpp`, `UserInterface.vcxproj(.filters)` | instancja `m_pySwitchbot`, `initSwitchbot()`, nowe pliki |

Pakiety: GC 171 `UPDATE` (cała tabela), `UPDATE_ITEM` (nowe bonusy przedmiotu – pole switchbota i jego miejsce w torbie),
`SEND_ATTRIBUTE_INFORMATION` (dla każdego zestawu bonusów: bonus + maksimum z `item_attr`); CG 170 `START` (+ 5
alternatyw) / `STOP`, z bajtem sekwencji. Przedmioty pól to zwykłe pakiety przedmiotów (`ITEM_SET` / `ITEM_DEL`) z
oknem 16. Serwer wysyła 171 i okno 16 **tylko** po `/switchbot hello`, które `uiswitchbot.py` wysyła, gdy istnieje moduł
`switchbot` – stary exe zamknąłby się na nieznanym nagłówku.

Sprawdzone: `clang-cl /Zs` (obraz `mt2009/exebuild-clang:19`, flagi z `out/clang/build.ninja`, kopia `exebuild/src` + ten
katalog, casefix) – `PythonSwitchbot.cpp`, `PythonPlayer.cpp`, `PythonPlayerModule.cpp`, `GameType.cpp`,
`PythonNetworkStream.cpp`, `PythonNetworkStreamPhaseGame.cpp`, `PythonNetworkStreamPhaseGameItem.cpp`, `UserInterface.cpp`,
`PythonApplication.cpp` bez błędów (`static_assert` okna 16 i rozmiarów przechodzą). Exe nie budowane (wspólna budowa
później: `build.sh msvc --smoke`).
