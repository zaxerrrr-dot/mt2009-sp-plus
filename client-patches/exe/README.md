# Zmiany w źródłach exe klienta (`metin2client.exe`)

Pełne kopie zmienionych plików źródła klienta, w układzie katalogów kopii wzorcowej
`/opt/metin2/cache/client-build/Source/Source Client/` (tej kopii nie zmieniamy). Żeby zbudować
exe z tymi zmianami, skopiuj zawartość tego katalogu na drzewo źródeł (nadpisując pliki):

```
for d in UserInterface EterLib EterPythonLib GameLib EterGrnLib EffectLib CWebBrowser; do
  cp -a "client-patches/exe/$d/." "<Source Client>/$d/"
done
cp -a client-patches/exe/Server/. "<Source>/Server/"   # od Zodiaku: Server/common/length.h klienta
```

Katalog `Server/` **nie** idzie do `Source Client/` (pętla po `*/` musi go pominąć), tylko do `<Source>/Server/`
(obok `Source Client`). Bez tego kroku kompilacja zatrzyma się na `CHAT_TYPE_MISSION`/`SE_SKILL_DAMAGE_ZONE`
(`static_assert` w `Mt2009Zodiak.cpp`).

Każda zmiana ma znacznik w komentarzu i jest za `#ifdef` z `Locale_inc.h`, więc wyłączenie
definicji przywraca stary exe.

## Błyszczenie i żywioł na +10…+15 – `MT2009_PLUS_REFINE_EFFECT_15_V1` (`ENABLE_MT2009_REFINE_EFFECT_15`)

Wężowa broń i zbroje (+0…+15) od +10 nie miały błyszczenia ani efektu żywiołu. `CItemData::GetRefine()` to `vnum % 10`,
więc +10…+15 (vnumy …0–…5, np. 370–375, 21320–21325) liczyły się jak +0…+5 i `__GetRefinedEffect` (`< 7`) nic nie
dołączał. Efekt żywiołu (`Mt2009WeaponElement.cpp`) rysuje się tylko obok efektu ulepszenia, więc znikał razem z nim.
Plików efektów +10…+15 nie ma (GF ma tylko `sword_7/8/9`, `armor_7/8/9`), więc +10…+15 dostają efekt +9.

| Plik | Zmiana |
|---|---|
| `UserInterface/Locale_inc.h` | `ENABLE_MT2009_REFINE_EFFECT_15` |
| `UserInterface/InstanceBase.cpp` | `Mt2009PlusAboveNine`: przedmiot jest +10 lub więcej, gdy przedmiot +9 tuż pod jego „+0” (`vnum - vnum%10 - 1`, np. 369) jest tego samego typu/podtypu i ulepsza się w `vnum - vnum%10` (369 → 370), albo gdy nazwa kończy się na „+N”, N ≥ 10 (jak `RefineOf` serwera). Wtedy `__GetRefinedEffect` liczy go jak +9 (z gniazdami jak dotąd); wynik zawsze ≤ 9 (`EFFECT_*_REFINED7 + refine - 7` nie wchodzi na efekty innej broni). Broń i zbroja (`ARMOR_BODY`) idą tą samą funkcją; żywioł wraca sam |

Bez zmian paczek i Pythona. Sprawdzone: kompilacja `InstanceBase.cpp` clang-cl z całą nakładką (10.11.2026).

## Auto Łowy: podejście do celu jak w testowych – `MT2009_PLUS_AUTOHUNT_DIRECT_V1` (`ENABLE_MT2009_AUTOHUNT_TEST`)

Nasze Auto Łowy (root `uiautohunt.py`) krążyły wokół celu: „w zasięgu” liczyły od środka do środka (200), a szły do
punktu 120 od środka potwora – szerszy potwór (i każdy dla jeźdźca, koń ma szerokie ciało) zatrzymywał postać na swoim
brzegu, kolizja aktorów zsuwała ją bokiem po ciele, kolejny krok znowu do środka – bieg w kółko bez ciosu. Testowe Auto
Łowy (Alt+H) oddają podejście i walkę exe (`__Update_AutoAttack`: co klatkę do żywej pozycji celu, stop na brzegu ciała
+150 – `IsClickableDistanceDestInstance` – obrót i cios) i przechodzą przez potwory. Teraz nasze też – ostatni prosty
odcinek i walkę; omijanie ścian (siatka `NavGrid`, `/autohunt_path`, „box”, krok od ściany) zostaje w Pythonie.

| Plik | Zmiana |
|---|---|
| `UserInterface/PythonPlayer.h` | `AutoHuntDirect_Attack`, `AutoHuntDirect_InReach`, `AutoHuntDirect_PassMonsters` |
| `UserInterface/Mt2009AutoHuntTest.cpp` | `player.AutoHuntDirectAttack(vid)` (cel + `__SetAutoAttackTargetActorID` + `__ReserveClickActor`; 0 oddaje chód Pythonowi; 0 = nie wzięte: martwy, nieatakowalny, koń bez poziomu do walki), `player.AutoHuntInReach(vid)` (`NEW_IsClickableDistanceDestInstance`: 1/0/-1), `player.AutoHuntPassMonsters(on)` (chód przez potwory i kamienie, jak w teście; nie rusza go, gdy test działa) |

Stary exe: root sprawdza `hasattr` i ma własne obejście (kontakt z ciałem, częstszy krok, natychmiastowy obrót). Bez nowych
pakietów. Sprawdzone: kompilacja `Mt2009AutoHuntTest.cpp`, `PythonPlayer.cpp` clang-cl z całą nakładką (10.11.2026).

## Wierzchowce stojące (deska, chmury, drakkary) – `MT2009_PLUS_STANDING_MOUNT_V1` (`ENABLE_MT2009_STANDING_MOUNT_FIX`), efekty w ruchu – `MT2009_PLUS_FIX_EFFECT_MOVEMENT_V1` (`ENABLE_FIX_EFFECT_MOVEMENT`)

Wierzchowce stojące to rasy `MT2009_STANDING_MOUNT_FIRST..LAST` = 40003–40007 (pieczęcie 52202, 52204–52207).
Jeździec zostaje w swoich naziemnych trybach animacji (`IsStandingMountRace` w `InstanceBase.cpp`), więc w ruchu
grał naziemny chód/bieg. Teraz stoi (WAIT), a deska/chmura/łódź gra własny walk/run i to ona przesuwa postać.

| Plik | Zmiana |
|---|---|
| `UserInterface/Locale_inc.h` | `ENABLE_MT2009_STANDING_MOUNT_FIX`, `MT2009_STANDING_MOUNT_FIRST/LAST`, `ENABLE_FIX_EFFECT_MOVEMENT` |
| `GameLib/ActorInstance.h/.cpp` | `__IsMountingStandingMount()`; `__GetCurrentComboType` daje na nim typ kombinacji jak na ziemi; `UpdateAttachingInstances` przeniesione z `OnUpdate` do `INSTANCEBASE_Transform` po `Transform()` (efekty nie zostają w tyle w ruchu) |
| `GameLib/ActorInstanceMotion.cpp` | `__SetMotion`: przy WALK/RUN na wierzchowcu stojącym tylko **model** jeźdźca gra WAIT jego trybu (z losowymi wariantami); węzeł ruchu i związane dane ruchu zostają WALK/RUN (`TYPE_MOVE`), więc `IsWalking()`/zatrzymanie/skręt działają jak na koniu. `__MotionEventProcess` pomija wtedy zdarzenia/dźwięki chodu (bez kroków). `MT2009_PLUS_STANDING_MOUNT_V2` (3.0.19): w 3.0.18 wiązane były dane WAIT, więc `IsWalking()` = false – po puszczeniu W postać sunęła bez końca i nie dało się zmienić kierunku |
| `GameLib/ActorInstanceBattle.cpp` | `__OnEndCombo`: kombinacja naziemna zaczyna się od początku (nie od 1 jak na koniu) |
| `GameLib/ActorInstanceAttach.cpp` | wachlarz zostaje w prawej ręce (poza naziemna), nie w lewej jak na koniu |
| `GameLib/ActorInstanceCollisionDetection.cpp` | `BlockMovement`: zatrzymuje też ruch samego jeźdźca (nie przechodzi przez ściany) |
| `UserInterface/InstanceBase.cpp` | kilof / sierp / wędka na wierzchowcu stojącym: `MODE_GENERAL` (stoi), nie `MODE_HORSE` (siedział na desce) |

Bez zmian paczek: modele i animacje desek są w paczkach (import GF, `npc_mount/summer_2023_hoverboard` itd.).
Sprawdzone `clang-cl /Zs` zmienionych plików na kopii źródeł z całą nakładką (6.11.2026).

## Wbudowana przeglądarka (drugi ItemShop) – `MT2009_PLUS_ITEMSHOP_V3_V1` (`ENABLE_MT2009_INGAME_BROWSER`)

`app.ShowWebPage` (okno Item Mall, czat botów, drugi ItemShop pod Shift+F12 – root `uiitemshopv3.py`) nie
działało w żadnym exe z tych źródeł: `WebBrowser_Startup` był zakomentowany w `UserInterface.cpp`, więc klasa
okna „WEBBROWSER” nie istniała i każde otwarcie kończyło się `CREATE_WEBBROWSER_ERROR:1407`.

| Plik | Zmiana |
|---|---|
| `UserInterface/Locale_inc.h` | `ENABLE_MT2009_INGAME_BROWSER` |
| `UserInterface/UserInterface.cpp` | `WebBrowser_Startup`/`WebBrowser_Cleanup` znowu wołane; przed startem `FEATURE_BROWSER_EMULATION` = 11001 (IE11) dla nazwy pliku exe w `HKCU` (bez uprawnień administratora) – kontrolka domyślnie rysuje jak IE7 |
| `CWebBrowser/CWebBrowser.c` | **nowy w nakładce** (katalog `CWebBrowser` w pętli kopiowania wyżej): `put_Silent` przed każdą nawigacją (bez okienek błędów skryptu nad grą), `OleInitialize` zwracające `S_FALSE` też uznane za sukces |

Sprawdzone: `clang-cl /Zs` obu plików na kopii źródeł z tą nakładką (24.10.2026); pełny build `build.sh msvc --smoke`
robi lead.

### Poprawka 24.10.2026 – `MT2009_PLUS_ITEMSHOP_V3_V2` (zawieszenie gry i crash przy zamykaniu)

Przyczyna: `CGraphicDevice::EnableWebBrowserMode` robił `Reset` urządzenia D3D na łańcuch `D3DSWAPEFFECT_COPY`, nie
zwalniając zasobów `D3DPOOL_DEFAULT` gry (tekstury cieni i render targetów, bufory wierzchołków, render targety mini
gier). Taki `Reset` zawsze się nie udaje, urządzenie zostaje „utracone” – nic się już nie rysuje (zawieszona gra, w
syserr „texture not found”, „cannot create the render target”), a drugi `Reset` przy zamykaniu kończył się crashem.

| Plik | Zmiana |
|---|---|
| `EterLib/GrpDevice.cpp` (**nowy w nakładce**) | `Enable/DisableWebBrowserMode` bez `Reset` – tylko prostokąt przeglądarki |
| `EterLib/GrpScreen.cpp` (**nowy w nakładce**) | częściowe `Present` wokół przeglądarki tylko przy łańcuchu COPY; normalnie cała klatka jak zawsze |
| `CWebBrowser/CWebBrowser.c` | okno gry dostaje `WS_CLIPCHILDREN` (Present nie zamalowuje przeglądarki); zamykanie w bezpiecznej kolejności (Stop → InPlaceDeactivate → Close → `SetClientSite(NULL)` → Release, dopiero potem `DestroyWindow`; blok strony zwalniany przy następnym otwarciu); `put_Silent` od pierwszej strony; zdarzenia `DWebBrowserEvents2`: link na inny serwer (np. „Doładuj SM” → buycoffee.to) i `target=_blank`/`window.open` otwierają się w domyślnej przeglądarce systemu (`ShellExecute`, tylko http/https/mailto), nie w grze |

Klawiatura gry działa przez DirectInput (nie przez okno), więc Esc i skróty (Shift+F12) zamykają sklep także wtedy,
gdy kursor jest w przeglądarce. Sprawdzone `clang-cl /Zs` trzech plików na kopii źródeł z całą nakładką.

### Poprawka 24.10.2026 – `MT2009_PLUS_ITEMSHOP_V3_V4` (zakładka „Koło Losu” w sklepie)

Strona sklepu prosi grę o okno gry: link na własny host sklepu `…/shop3/game/<nazwa>/` (zakładka „Koło Losu” →
`game/wheel/`) nie jest ładowany – `BeforeNavigate2` go anuluje i zapamiętuje nazwę (a–z, 0–9, `_`), a gra ją odbiera.

| Plik | Zmiana |
|---|---|
| `CWebBrowser/CWebBrowser.c` | `Mt2009TakeGameUrl` w `BeforeNavigate2` strony głównej, `WebBrowser_TakeGameCommand(out, len)` (nazwa raz, potem pusto) |
| `CWebBrowser/CWebBrowser.h` | deklaracja `WebBrowser_TakeGameCommand` |
| `UserInterface/PythonApplicationModule.cpp` | `app.TakeWebPageCommand()` → `'wheel'` / `''` (za `ENABLE_MT2009_INGAME_BROWSER`) |

Root `uiitemshopv3.py` pyta co klatkę, gdy sklep jest otwarty: `wheel` → zamyka sklep i otwiera `uiwheel.OpenWindow()`.
Stary exe (bez funkcji) ładuje link – sklep pokazuje wtedy stronę z informacją o klawiszu F12. Sprawdzone `clang-cl /Zs`
obu plików na kopii źródeł z całą nakładką.

## System gildii – `MT2009_PLUS_GUILDSYS_V1` (`ENABLE_MT2009_GUILDSYS`)

Na paczce Guild Systems (skompilował Nazox), serwer: `server-patches/guildsys`. Bez zmian pakietów.

| Plik | Zmiana |
|---|---|
| `UserInterface/Locale_inc.h` | `ENABLE_MT2009_GUILDSYS` |
| `UserInterface/Locale.cpp` | **nowy w nakładce**: `LocaleService_GetLastExp` – tabela doświadczenia gildii do poziomu 40 (ta sama co `guild_exp_table` serwera) |
| `UserInterface/PythonGuild.cpp` | **nowy w nakładce**: `guild.GetGuildExperience` – ostatni poziom 40 |
| `UserInterface/PythonPlayerSkill.cpp` | `UseGuildSkill`: umiejętności gildii `ONLY_FOR_GUILD_WAR` działają też w Krypcie Balathora (`metin2_map_guild_whitedragon_boss`) |

Sprawdzone `clang-cl /Zs` trzech plików `.cpp` na kopii `exe-src7` z całą nakładką (29.10.2026).

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

## Pomocnicze przedmioty Smoczych Kamieni z danych klienta – `MT2009_PLUS_DS_UTILITY_FROM_PROTO_V1` (`ENABLE_DRAGON_SOUL_SYSTEM`)

`GameLib/ItemManager.cpp` (`LoadItemTable`, tablica `aDragonSoulUtilityItems`): 12 przedmiotów (30270, 50255, 50260,
76029, 100100, 100101, 100200, 100300, 100400, 100500, 100700, 100701) exe tworzy już **tylko wtedy, gdy item_proto
klienta (dbdata) nie ma ich rekordu** (wpis z samego item_list.txt ma pustą tabelę – liczy się tabela z tym vnumem).
Wcześniej nadpisywał wszystkie 12 nazwami w UTF-8 (krzaki w oknach, np. „PĹ‚omieĹ„ Smoka+”) i ikoną
`icon/item/<vnum>.tga` (100701.tga nie istnieje – brak ikony). Teraz nazwa, opis, flagi i ikona idą z danych (item_list:
100701 → 100700.tga, 76029 → 100300.tga). Zapasowe nazwy w cp1250 (jak w danych); przy wpisie z item_list zostaje jego ikona.
W danych 3.0 rekordu nie mają tylko 76029 i 100101 – te dalej tworzy exe (antyflagi jak world.item_proto).

Sprawdzone: `clang-cl /Zs` (obraz `mt2009/exebuild-clang:19`, flagi z `out/clang/build.ninja`, drzewo `exebuild/src`
+ ten katalog) – `ItemManager.cpp` bez błędów. Exe nie budowane.
## Kostiumy Buffi – `MT2009_PLUS_BUFFI_V2` (`ENABLE_MT2009_BUFFI_COSTUME`)

Cztery sloty kostiumów Buffi z Amerii (strój, fryzura, broń, szarfa; serwer: `server-patches/buffi`,
`playerbot_buffi.cpp`). Pola to **wolne pola wyposażenia 28–31 pod `WEAR_MAX` 32** – bez zmiany układu pól, pakietów
i bazy; stary exe też trzyma przedmioty tych pól (`c_Wear_Max` 32), a `root/uibuffi.py` bierze je wtedy z
`player.EQUIPMENT_SLOT_START + 28…31`.

| Plik | Zmiana |
|---|---|
| `UserInterface/Locale_inc.h` | `#define ENABLE_MT2009_BUFFI_COSTUME` |
| `Server/common/length.h` | `WEAR_BUFFI_BODY = 28`, `WEAR_BUFFI_HEAD = 29`, `WEAR_BUFFI_WEAPON = 30`, `WEAR_BUFFI_SASH = 31` (stałe numery serwera) |
| `UserInterface/GameType.h` | `c_Buffi_Slot_Start/Body/Head/Weapon/Sash/Count` + `static_assert` (wewnątrz pól wyposażenia, po rękawicach) |
| `UserInterface/PythonItemModule.cpp` | `item.BUFFI_SLOT_START`, `BUFFI_SLOT_BODY`, `BUFFI_SLOT_HEAD`, `BUFFI_SLOT_WEAPON`, `BUFFI_SLOT_SASH`, `BUFFI_SLOT_COUNT` |
| `UserInterface/PythonApplicationModule.cpp` | `app.ENABLE_MT2009_BUFFI_COSTUME` |

Sprawdzone: `clang-cl /Zs` (obraz `mt2009/exebuild-clang:19`, flagi z `out/clang/build.ninja`, kopia `exebuild/src` +
ten katalog, casefix) – `PythonItemModule.cpp`, `PythonApplicationModule.cpp`, `GameType.cpp`, `PythonPlayerModule.cpp`
bez błędów; `/E` potwierdza stałe `BUFFI_SLOT_*` w module. Exe nie budowane (wspólna budowa rundy).
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

## Ognisty Duch – efekty modelu bez duplikatów – `MT2009_PLUS_FIRE_GHOST_V1` (`ENABLE_MT2009_FIRE_GHOST_FIX`)

`CActorInstance::SetShape` przyczepiał efekty z `AttachingData` modelu (`.msm`, `AttachingDataType 2`) przy każdym
wywołaniu, nie zdejmując tych z poprzedniego (czyścił je tylko `SetRace`). Gdy `SetShape` wraca na żywym aktorze, każda
kopia zostaje – a efekt zapętlony (`fire_ghost_body.mse` w `fire_ghost.msm` Ognistego Ducha 2202/2232, ten sam wzorzec w
`2009_recycle_monster` 2281) nigdy nie gaśnie: mob rośnie w kulę ognia, klient zjada cały rdzeń.

| Plik | Zmiana |
|---|---|
| `UserInterface/Locale_inc.h` | `#define ENABLE_MT2009_FIRE_GHOST_FIX` |
| `GameLib/ActorInstance.h` | `std::vector<DWORD> m_kVct_dwShapeEffectID` – id efektów, które przyczepił `SetShape` |
| `GameLib/ActorInstanceData.cpp` (**nowy w nakładce**) | `SetShape` najpierw `DettachEffect` na swoich poprzednich id, potem przyczepia i zapamiętuje nowe; `SetRace` czyści listę razem z `__ClearAttachingEffect` |

Zdejmowane są tylko efekty z `AttachingData` – efekty affectów i przedmiotów (też w `m_AttachingEffectList`) zostają.
Id, którego lista już nie ma (wyczyścił je `Destroy`), `DettachEffect` pomija; `CEffectManager::GetEmptyIndex` tylko rośnie,
więc stare id nie trafi w cudzy efekt. Strona danych (paczka `fireghost`, `client-2.0.30/tools/fireghost`) działa też ze
starym exe.

Sprawdzone: `clang-cl /Zs` (obraz `mt2009/exebuild-clang:19`, flagi z `out/clang/build.ninja`, kopia `exebuild/src` + ten
katalog) – `ActorInstanceData.cpp`, `ActorInstance.cpp`, `ActorInstanceAttach.cpp`, `ActorInstanceMotion.cpp`,
`InstanceBase.cpp`, `InstanceBaseEffect.cpp` bez błędów, `/E` potwierdza, że kod jest za włączoną definicją (27.10.2026).
Exe nie budowane.

## Auto Łowy biegną pod strzałami – `MT2009_PLUS_AUTOHUNT_RUN_ON_HIT_V1` (`ENABLE_MT2009_RUN_THROUGH_ARROWS`)

Strzała (lub pocisk czaru) potwora, która trafia biegnącą postać, odgrywała „drgnięcie” (`CActorInstance::OnShootDamage`:
`InterceptOnceMotion(DAMAGE)`, potem `WAIT`). To kasowało animację biegu, od której zależy ruch postaci, więc Auto Łowy
stawały do następnego rozkazu kroku (do 0,35 s), a marsz kliknięciem myszy zatrzymywał się całkiem.

| Plik | Zmiana |
|---|---|
| `UserInterface/Locale_inc.h` | `#define ENABLE_MT2009_RUN_THROUGH_ARROWS` |
| `GameLib/ActorInstanceBattle.cpp` | `OnShootDamage`: postać gracza (`m_isMain` albo `TYPE_PC`) w ruchu (`__IsMoveMotion`) tylko się trzęsie (`__Shake`), bez animacji obrażeń; stojąca postać i potwory jak dotąd |

Serwer animacji nie widzi, więc nic poza wyglądem się nie zmienia. Ciosy wręcz bez zmian. Root (`uiautohunt.py`,
`WALK_KEEP_*`) i tak od razu wznawia zatrzymany marsz, także na starym exe.

Sprawdzone: `clang-cl /Zs` pliku `ActorInstanceBattle.cpp` (obraz `mt2009/exebuild-clang:19`, flagi z `out/clang/build.ninja`)
z definicją i bez, `/E` potwierdza kod za definicją (28.10.2026). Exe nie budowane.

## Testowe Auto Łowy (Alt+H) – `MT2009_PLUS_AUTOHUNT_TEST_V1` (`ENABLE_MT2009_AUTOHUNT_TEST`)

Auto łowy z paczki „Oto Av” właściciela (28.10.2026) jako **test** obok naszych Auto Łowów (K / Shift+K, bez zmian). Tu
poluje exe: co klatkę (`CPythonPlayer::Update`, po `__Update_AutoAttack`) wybiera najbliższego potwora, którego klient
widzi (ranga i poziom z okna, kamienie osobno, zasięg wokół postaci albo – „Zasięg od startu” – wokół miejsca startu,
wolna linia bez ściany mapy, nie cudzy: poruszający się gracz bliżej niego w 15 m go zabiera), daje go własnemu
auto-atakowi klienta (podejście i ciosy), rzuca umiejętności z 12 pól co ich czas (ataku tylko w zasięgu celu), pije
mikstury HP/PE z 12 pól poniżej ich % (do pełna co 0,4 s) i używa wzmocnień / ros co N sekund. Utknięcie (3 s bez ruchu i
ciosu) albo 15 s bez ciosu – cel porzucony na 10 s. Nazwa celu jest zielona, postać przechodzi przez potwory i kamienie.
Okno, zapis ustawień, wstawanie po śmierci i zgoda serwera to root `uiautohunt_test.py` (+ `server-patches/autohunttest`).
**Bez nowych pakietów** – zwykłe pakiety ataku, umiejętności, celu i użycia przedmiotu.

| Plik | Zmiana |
|---|---|
| `UserInterface/Locale_inc.h` | `#define ENABLE_MT2009_AUTOHUNT_TEST` |
| `UserInterface/Mt2009AutoHuntTest.cpp` (**nowy**) | cała logika polowania, efekt zasięgu (`d:/ymir work/effect/etc/auto_hunt/auto_hunt_range_01.mse`, skala zasięg/10000), `player.AutoHuntTest*` (13 funkcji) i `player.AUTOHUNT_TEST_SKILL_SLOTS` / `ITEM_SLOTS` |
| `UserInterface/PythonPlayer.h/.cpp` | stan `m_kAutoHuntTest` (ustawienia, 24 pola, cel, utknięcie), `AutoHuntTest_Update()` w `Update`, `AutoHuntTest_Reset()` w `Clear` |
| `UserInterface/InstanceBase.h/.cpp`, `InstanceBaseEffect.cpp` | `SetAutoHuntTestTarget` (zielona nazwa w `GetNameColor`), `SetAutoHuntTestPass` |
| `GameLib/ActorInstance.h`, `ActorInstance.cpp` (**nowy w nakładce**) | `m_bAutoHuntTestPass` (zerowane w inicjalizacji aktora) |
| `GameLib/ActorInstanceCollisionDetection.cpp` (**nowy w nakładce**) | `TestActorCollision`: z polowaniem testowym bez kolizji z potworami i kamieniami |
| `UserInterface/UserInterface.cpp`, `UserInterface.vcxproj(.filters)` | `Mt2009AutoHuntTest_RegisterPython()` po module `player`, nowy plik |

Różnice względem paczki: zasięg naprawdę ogranicza (w paczce i tak było maks. 50 m), przełącznik zasięgu („Odak” paczki) kotwiczy
obszar przy starcie (w paczce nic nie robił), pole 0 ekwipunku może trzymać przedmiot, utknięty cel jest naprawdę pomijany,
każda mikstura HP/PE (wartość 0 / 1 przedmiotu) się liczy, nie tylko 27001–27008 / 70390–70391; bez afektu premium 814 i
przedmiotów 20170–20173 (zgoda serwera zamiast nich); bez gwiazdki startu na minimapie i bez przycisku na pasku.
Nie zmienia `ActorInstanceBattle.cpp` (`ENABLE_MT2009_RUN_THROUGH_ARROWS` bez zmian – działa też dla tego polowania).

Sprawdzone: `clang-cl /Zs` (obraz `mt2009/exebuild-clang:19`, flagi z `out/clang/build.ninja`, kopia `exebuild/src` + ten
katalog) – `Mt2009AutoHuntTest.cpp`, `PythonPlayer.cpp`, `PythonPlayerSkill.cpp`, `PythonPlayerModule.cpp`, `InstanceBase.cpp`,
`InstanceBaseEffect.cpp`, `InstanceBaseBattle.cpp`, `UserInterface.cpp`, `PythonCharacterManager.cpp`,
`PythonNetworkStreamPhaseGame.cpp`, `GameLib/ActorInstance.cpp`, `ActorInstanceCollisionDetection.cpp`,
`ActorInstanceBattle.cpp`, `ActorInstanceData.cpp` bez błędów, z definicją i bez; `/E` potwierdza kod za definicją
(28.10.2026). Exe nie budowane.
## Lokalizator NPC – `MT2009_PLUS_NPC_LOCATION_HELPER_V1` (`ENABLE_NPC_LOCATION_HELPER`)

Ulepszona mapa świata z paczki „NPC Location Helper” (Autor: Best Studio), przeniesiona na nasz exe: lista NPC każdej
mapy, powiększanie (1–3) i przesuwanie atlasu w oknie, atlas innej mapy, znacznik wybranego NPC, strzałka pod postacią
i teleport do NPC (serwer: `server-patches/npcloc`). Pakiety: **CG 196 / GC 196** (`HEADER_CG/GC_NPC_LOCATION_HELPER`),
CG 18 bajtów (+ bajt sekwencji), GC 24 bajty, pola `int`/`DWORD` (bez `long`), `static_assert` rozmiarów.

| Plik | Zmiana |
|---|---|
| `UserInterface/Locale_inc.h` | `#define ENABLE_NPC_LOCATION_HELPER` |
| `UserInterface/Packet.h` | nagłówki 196/196, podnagłówki CG (`REQUEST_STATUS`, `WARP_TO_NPC`, `USE_TICKET`, `REQUEST_GUILD_LAND`) i GC (`STATUS`, `WARP_RESULT`, `GUILD_LAND`), `TPacketCG/GCNPCLocationHelper` |
| `UserInterface/PythonNPCLocationHelper.h/.cpp` | **nowe**: `CPythonNPCLocationHelper` (aktywny, cooldown odliczany między pakietami, ostatni wynik, numer mapy postaci z pakietu `STATUS`), ciała `SendNPCLocationHelperPacket`/`RecvNPCLocationHelperPacket` (woła w oknie gry `RefreshNPCLocationHelperStatus()`, `OnNPCLocationHelperWarpResult(wynik)`, `RefreshNPCLocationHelperGuildLand(mapa, wynik)`), moduł `npcLocationHelper` |
| `UserInterface/PythonMiniMapNPCLocationHelper.cpp` | **nowe**: widok atlasu pomocnika – to samo `atlas.sub` (bez tekstur „atlas_resize”, zwykłe przeliczenie pozycji jak na małym atlasie), skala własną macierzą, przycinanie do okna prostokątem nożyc D3D9 (exe nie ma clip mask), atlas innej mapy (miejsce z `atlasinfo.txt`, znaczniki z `locale/pl/map/<mapa>_point.txt`, obszary gildii mapy postaci zachowane), znaczniki pod myszą, wybrany NPC (punkt drogi + pomarańczowy kwadrat), strzałka `d:/ymir work/effect/etc/npc_location/npc_location_direction.mse` aż grot dojdzie do NPC (3 m) |
| `UserInterface/PythonMiniMap.h/.cpp` | deklaracje i pola pomocnika; `__LoadAtlasMarkInfo` dzieli się na `__LoadAtlasMarkInfoForMap(nazwa)`; `LoadAtlas` zeruje nazwę pokazanej mapy; `RenderAtlas` i `GetAtlasInfo` przy widoku pomocnika idą do jego kodu; kółko pozycji `my_position_01..07.sub` (tylko gdy są w paczkach). Wyłączony widok pomocnika rysuje mały atlas dokładnie jak dotąd |
| `UserInterface/PythonMiniMapModule.cpp` | 22 funkcje `miniMap` pomocnika, stałe `SQUARED_ATLAS_SIZE`, `ATLAS_TYPE_*`; `SetAtlasScale(s)` z jednym argumentem = skala pomocnika, `SetAtlasScale(x, y)` jak dotąd (pomijane, gdy widok pomocnika jest włączony) |
| `UserInterface/PythonBackground.h` | `GetMapInfoByName` (miejsce i rozmiar innej mapy z `atlasinfo.txt`) |
| `UserInterface/PythonPlayer.cpp` | strzałka aktualizowana co klatkę (także przy schowanej minimapie) |
| `UserInterface/PythonNetworkStream.cpp/.h`, `PythonNetworkStreamPhaseGame.cpp` | rejestracja GC 196 (stały rozmiar), deklaracje, `case` |
| `UserInterface/PythonApplicationModule.cpp` | `app.ENABLE_NPC_LOCATION_HELPER`; 0 dla `ENABLE_CLIP_MASK`, `ENABLE_ELEMENT_ADD`, `ENABLE_EVENT_BANNER`, `WJ_SHOW_PARTY_ON_MINIMAP` (python paczki o nie pyta) |
| `UserInterface/PythonNonPlayerModule.cpp` | `nonplayer.GetMonsterRank(vnum)` / `GetRankOnVnum(vnum)`, `GetMonsterLevel(vnum)` |
| `UserInterface/UserInterface.cpp` | `initNPCLocationHelper()` |
| `UserInterface/UserInterface.vcxproj(.filters)` | nowe pliki |

Ta sama mapa (strzałka): `miniMap.SelectNPC(mapa, vnum, x, y, nazwa_mapy)` – x/y w pikselach mapy (wartość z pliku
punktów), `nazwa_mapy` = folder mapy; bez nazwy numer mapy porównywany z `npcLocationHelper.GetCurrentMapIndex()`
(serwer podaje go w pakiecie `STATUS`), 0 = mapa postaci.

Sprawdzone: `clang-cl /Zs` (obraz `mt2009/exebuild-clang:19`, flagi z `out/clang/build.ninja`, kopia `exebuild/src` + cały
ten katalog) – `PythonNPCLocationHelper.cpp`, `PythonMiniMap.cpp`, `PythonMiniMapNPCLocationHelper.cpp`,
`PythonMiniMapModule.cpp`, `PythonNetworkStream.cpp`, `PythonNetworkStreamPhaseGame.cpp`, `UserInterface.cpp`,
`PythonApplicationModule.cpp`, `PythonNonPlayerModule.cpp`, `PythonPlayer.cpp` bez błędów; próbny błąd potwierdza kod za
włączoną definicją (28.10.2026). Exe nie budowane.

## Większe liczby w slotach pod Ctrl – `MT2009_PLUS_SLOT_TEXT_SIZE_V1` (`ENABLE_SLOT_TEXT_SIZE`, Autor: EREMIT STUDIO)

Trzymany Ctrl rysuje liczby `CNumberLine` (ilości przedmiotów w slotach) dwa razy większe; puszczony – zwykłe. Paczka
SLOT_TEXT_SIZE (EREMIT STUDIO) przeniesiona z poprawkami: cyfry są instancjami `CGraphicExpandedImageInstance` (skala 2×),
szerokość do wyrównania liczona ×2, przy powiększeniu przesunięcie −4 px w górę i +4 px w prawo.

| Plik | Zmiana |
|---|---|
| `UserInterface/Locale_inc.h` | `#define ENABLE_SLOT_TEXT_SIZE` |
| `EterPythonLib/PythonWindow.h` | `CNumberLine`: wektor `CGraphicExpandedImageInstance*` (bez definicji jak dotąd `CGraphicImageInstance*`), `m_bIsZoomed`, statyczny włącznik `ms_bZoomEnabled` (domyślnie włączony) |
| `EterPythonLib/PythonWindow.cpp` | `SetNumber` tworzy instancje rozszerzone ze skalą; `OnRender` sprawdza Ctrl (`GetAsyncKeyState`) i przy zmianie skaluje + `OnChangePosition`; `OnChangePosition` z szerokością ×2; `ClearNumber` oddaje instancje do puli `CGraphicExpandedImageInstance::Delete` (paczka i stary kod tylko czyściły wektor – wyciek przy każdej zmianie liczby) |
| `EterPythonLib/PythonWindowManagerModule.cpp` | `wndMgr.SetSlotTextZoom(0/1)`, `wndMgr.IsSlotTextZoom()` |

Root (`client-patches/client-2.0.30/root`): w opcjach gry wiersz „Liczby” – „Ctrl” / „Wyłączone” (`uiscript/gameoptiondialog.py`,
okno +25 px; `uigameoption.py`). Wybór w `slottext.cfg` obok klienta, ustawiany przy imporcie `uiGameOption` (start gry).
Stary exe bez `wndMgr.SetSlotTextZoom` – wiersz ukryty, nic się nie zmienia.

Sprawdzone: `clang-cl /Zs` (obraz `mt2009/exebuild-clang:19`, flagi z `out/clang/build.ninja`, kopia `yohara/exe-src7` +
cały ten katalog) – `PythonWindow.cpp`, `PythonWindowManagerModule.cpp`, `PythonSlotWindow.cpp`,
`PythonGridSlotWindow.cpp`, `PythonWindowManager.cpp` bez błędów z definicją i bez niej (28.10.2026); pliki root
sprawdzone parserem Pythona 2.7. Exe nie budowane.
## Krypta Balathora – `MT2009_PLUS_BALATHOR_V1` (`__BALATHOR__`, autor: dracaryS)

Strona klienta gildyjnego lochu Balathora (serwer: `server-patches/balathor`, mapa 420). Bez nowych pakietów: efekty
przychodzą komendami czatu `BalathorEffectAdd <id> <vid> <efekt> <x> <y> <z> <obrót> <główny>` i
`BalathorEffectRemove <id>` (obsługa w exe), ruchy bossa `ETC1..3` w zwykłym `HEADER_GC_MOTION` (na `victim_vid`).
Komendy `SetBalathor` / `SetBalathorEffect` obsługuje root (`game.py` → `uiguildwhitedragon.py`).

| Plik | Zmiana |
|---|---|
| `UserInterface/Locale_inc.h` | `#define __BALATHOR__` |
| `UserInterface/PythonApplicationModule.cpp` | `app.__BALATHOR__` (1/0) |
| `UserInterface/GameType.h` | `BALATHOR_EFF_*` (0–8), `TBalathorEffect` |
| `UserInterface/PythonPlayer.h/.cpp` | lista efektów (`AddBalathorEffect`, `RemoveBalathorEffect`, `CheckBalathorEffect`, `UpdateBalathorEffect` – strzałka do pozycji co klatkę), czyszczona w `NEW_ClearSkillData` |
| `UserInterface/InstanceBase.h/.cpp` | efekty przypięte do VID (kość `Bip01`), Balathor 6896/6897 zawsze rysowany (`SetForceShow`) |
| `UserInterface/PythonNetworkStreamCommand.cpp` (**nowy w nakładce**) | komendy `BalathorEffectAdd/Remove` |
| `UserInterface/PythonNetworkStreamPhaseGame.cpp` | `RecvMotionPacket` gra ruch na `victim_vid` |
| `UserInterface/PythonEventManager.h/.cpp` (**nowe w nakładce**) | zdarzenia kamer cutscenek `SET_KEYBOARD_MOUSE_LOCK`, `RESTORE_CAMERA_EXCEPT_POSITION`, `CLOSE_CINEMA` (zdejmuje też blokadę) |
| `UserInterface/PythonApplicationEvent.cpp` (**nowy w nakładce**) | przy blokadzie: bez klawiatury i bez obracania kamery myszą |
| `UserInterface/PythonTextTail.cpp` (**nowy w nakładce**) | przy blokadzie bez nazw nad postaciami |
| `EterPythonLib/PythonWindowManager.h/.cpp` | `SetLockMouseAndKeyboard` / `IsMouseAndKeyboardLocked` |
| `EterLib/GrpObjectInstance.h`, `EterLib/CullingManager.cpp` (**nowy w nakładce**) | `SetForceShow` – obiekt nie znika poza widokiem |
| `EterLib/parser.cpp` (**nowy w nakładce**) | wartości argumentów skryptu zdarzeń do 128 znaków (foldery kamer) |
| `GameLib/RaceMotionData.h/.cpp`, `RaceManager.cpp` (**nowe w nakładce**), `ActorInstanceMotion.cpp` | `NAME_ETC_1..3` = 39–41 (`static_assert`), `motlist` `ETC1..3` |
| `GameLib/ActorInstance.h/.cpp`, `ActorInstanceBattle.cpp` | Lodowa Ściana 20494 jak drzwi, Ogniste Jajo 20497 da się pchać (siła 20) i nie blokuje ruchu |

Pominięte z paczki: `wndMgr.ResetFrame` – nasz exe już go ma (`ENABLE_OWSAP_WNDMGR_EX`).
Efekty, których exe szuka: `d:/ymir work/effect/monster2/guild_whitedragon_*.mse`, `whitedragon_ground_ice.mse`,
`d:/ymir work/effect/etc/direction/direction_land.mse`, `d:/ymir work/effect/etc/npc_location/npc_location_direction.mse`.

Sprawdzone: `clang-cl /Zs` (obraz `mt2009/exebuild-clang:19`, flagi z `out/clang/build.ninja`, kopia `exebuild/src` + cały ten
katalog) – wszystkie 15 zmienionych `.cpp` bez błędów; `/E` potwierdza kod za definicją (28.10.2026). Exe nie budowane.

## Błyskawice rękawic 6/7 – `MT2009_PLUS_ELEC_GLOVE_V1` (`ENABLE_GLOVE_ELEC_ATTACK_BONUS`)

Bonus rękawic „Atakuj potwory w pobliżu błyskawicami” (`POINT_GLOVE_LIGHTNING` 242, serwer: `server-patches/bonusy67`)
dostaje globalny efekt trafienia: serwer (`server-patches/elecglove`) wysyła `SE_ELEC_ATTACK_HIT` (**54**) do każdego
potwora, w którego uderza błyskawica.

| Plik | Zmiana |
|---|---|
| `UserInterface/Locale_inc.h` | `ENABLE_GLOVE_ELEC_ATTACK_BONUS` |
| `Server/common/length.h` | `SE_ELEC_ATTACK_HIT` po `SE_SKILL_SAFE_ZONE_SMALL` (54 jak na serwerze) |
| `UserInterface/InstanceBase.h` | `EFFECT_ELEC_ATTACK_HIT` przed `EFFECT_NUM` |
| `UserInterface/PythonPlayerSettingsModule.cpp` | rejestracja `d:/ymir work/effect/hit/blow_electric/6th7th_attributes_blow.mse` (paczka `elecglove`, `client-2.0.30/tools/elecglove`) |
| `UserInterface/PythonNetworkStreamPhaseGameItem.cpp` | `case SE_ELEC_ATTACK_HIT` → `EFFECT_ELEC_ATTACK_HIT` (`static_assert` 54) |
| `UserInterface/PythonCharacterManagerModule.cpp` | `chrmgr.EFFECT_ELEC_ATTACK_HIT` |

Stary exe: efekt 54 to tylko wpis w syserr. Sprawdzone `clang-cl /Zs` czterech plików (`InstanceBase.cpp` też) na kopii
źródeł z całą nakładką.
## „Pełny ekran” jako okno bez ramek – `MT2009_PLUS_BORDERLESS_FULLSCREEN_V1` (`ENABLE_MT2009_BORDERLESS_FULLSCREEN`)

Runda 27.10, poz. 1: ItemShop V3 (przeglądarka – okno-dziecko gry) był niewidoczny w trybie „Pełny ekran”: ekskluzywny
pełny ekran D3D9 (`Windowed=FALSE`) omija kompozycję pulpitu, więc obraz gry przykrywał przeglądarkę. Teraz ta opcja
(`WINDOWED 0` w `metin2.cfg`, `CPythonSystem::IsFullscreen`) to okno bez ramek na cały monitor. „Okno” (`WINDOWED 1`) i
„Pełny ekran w oknie” (`WINDOWED 2`) bez zmian.

| Plik | Zmiana |
|---|---|
| `UserInterface/Locale_inc.h` | `#define ENABLE_MT2009_BORDERLESS_FULLSCREEN` |
| `UserInterface/PythonApplication.cpp` | `CreateDevice`: urządzenie zawsze `Windowed=TRUE` (`FullScreen_RefreshRateInHz` 0, `DISCARD`, 2 bufory, `PresentationInterval` jak dotąd – synchronizacja przez kompozycję pulpitu); `Create`: tylko w „Pełnym ekranie” `SetProcessDPIAware` przed utworzeniem okna (bez tego pulpit ze skalą 125/150% rozmywałby grę i zmniejszał prostokąt monitora); tryb ekranu i okno w rozmiarze bufora (`m_dwWidth`×`m_dwHeight` = `GetWidth`×`GetHeight`, też przy skali interfejsu); po utworzeniu urządzenia okno `HWND_TOPMOST` na monitorze; `Destroy`: przywrócenie rozdzielczości pulpitu |
| `UserInterface/PythonApplicationProcedure.cpp` | `__SetFullScreenWindow`: monitor okna (`MonitorFromWindow` przy starcie – główny; zapamiętana nazwa urządzenia `\\.\DISPLAYn`), `ChangeDisplaySettingsEx(CDS_FULLSCREEN)` **tylko** gdy wybrana rozdzielczość ≠ rozdzielczość pulpitu (`ENUM_REGISTRY_SETTINGS`), z częstotliwością z `metin2.cfg` (gdy monitor jej nie przyjmie – bez niej); drugi raz nie zmienia trybu, który już jest; potem okno na prostokąt tego monitora (`EnumDisplayMonitors` + `GetMonitorInfo`, także monitor z ujemnymi współrzędnymi). `__MinimizeFullScreenWindow` (Alt+Tab): pulpit z powrotem, zdjęte `TOPMOST`, minimalizacja – jak dotąd. Aktywacja: `SW_RESTORE` z paska zadań, tryb, okno. `WM_SIZE`/`WM_EXITSIZEMOVE`: w tym trybie bez `ResizeBackBuffer` (bufor ma rozmiar okna; `Reset` z żywymi zasobami `D3DPOOL_DEFAULT` zamrażał grę) |
| `UserInterface/PythonApplication.h` | `__PlaceFullScreenWindow`, `__RestoreFullScreenDisplayMode` |

`GrpDevice.cpp` bez zmian: przy `Windowed=TRUE` jego `SetWindowPos(HWND_TOPMOST)` się nie wykonuje, okno ustawia
`__PlaceFullScreenWindow`. Utrata urządzenia przy zmianie trybu (Alt+Tab, powrót, blokada ekranu) idzie jak dotąd przez
`CheckDeviceState` → `DEVICESTATE_NEEDS_RESET` (zwolnienie cieni i render targetów, `Reset`, odtworzenie). Gra nie
zamyka kursora w oknie (`ClipCursor` nigdzie) – tak zostaje. Gdy zmiana trybu się nie uda, gra ma okno w rozmiarze
bufora na środku monitora (myszka dalej trafia), w syserr „FullScreen: ChangeDisplaySettingsEx … failed”.

Różnica względem ekskluzywnego trybu: gamma z opcji (`SetGammaRamp`) działa tylko w ekskluzywnym pełnym ekranie, więc
teraz – jak w „Oknie” – nie zmienia jasności.

Sprawdzone (29.10.2026): `clang-cl /Zs` (obraz `mt2009/exebuild-clang:19`, flagi z `out/clang/build.ninja`) –
`PythonApplication.cpp`, `PythonApplicationProcedure.cpp` na `exe-src7` + ten katalog, z definicją i bez – bez błędów
i bez ostrzeżeń w nowym kodzie. Exe nie budowane (budowa na koniec rundy).

Do sprawdzenia w grze („Pełny ekran”): rozdzielczość = pulpit (bez mrugnięcia przy starcie i Alt+Tab) i ≠ pulpit
(zmiana trybu, powrót pulpitu przy Alt+Tab / minimalizacji / wyjściu); ItemShop V3 (Shift+F12) widoczny i klikalny;
Alt+Tab tam i z powrotem przy otwartym sklepie i na mapie ze śniegiem; pulpit ze skalą 125/150%; dwa monitory; Win+D;
„Okno” i „Pełny ekran w oknie” jak dotąd.
## Kamienie Antymagii – `MT2009_PLUS_ANTI_RESIST_MAGIC_V1` (`ENABLE_MT2009_ANTI_RESIST_MAGIC`)

Paczka „Anti Magic penetrate stone” (serwer: `server-patches/antimagic`). Bonus kamieni to punkt serwera **252**
(`POINT_ANTI_RESIST_MAGIC`, w tym silniku apply = punkt) – przychodzi jako zmiana punktu, więc exe musi go znać.

| Plik | Zmiana |
|---|---|
| `Server/common/length.h` | `POINT_ANTI_RESIST_MAGIC = 252` po `POINT_HIT_PCT`, `POINT_MAX_NUM` 253 – **bez `#ifdef`** (rozmiar `m_alPoint` i tablicy efektów punktów musi być ten sam w każdym pliku); 198–251 serwera nigdy nie przychodzą, nie mają tu nazw; pakiet punktów bez zmian (`POINT_PACKET_NUM` 193) |
| `UserInterface/Mt2009Champion.cpp` | `static_assert` 252 / 253 zamiast `POINT_MAX_NUM == 198` |
| `UserInterface/Locale_inc.h` | `#define ENABLE_MT2009_ANTI_RESIST_MAGIC` |
| `UserInterface/PythonItemModule.cpp` | `item.APPLY_ANTI_RESIST_MAGIC` (252) |
| `UserInterface/PythonPlayerModule.cpp` | `player.POINT_ANTI_RESIST_MAGIC` i `player.POINT_RESIST_MAGIC_REDUCTION` (252 – pod tą nazwą okno postaci, `uiattributelist.py`, pokazuje linię „Antymagia”) |
| `UserInterface/PythonApplicationModule.cpp` | `app.ANTI_RESIST_MAGIC_BONUS` (1 / 0) |

`GameLib/ItemData.h` paczki (`CItemData::APPLY_*`) nie ma odpowiednika – nasz exe nie ma tam listy APPLY, nazwy
bonusów to `POINT_*`. Stary exe pomija zmianę punktu 252 (`SetStatus`: typ ≥ 198), dymek kamienia i tak nazywa 252
(`root/localeinfo_point.py`).

Sprawdzone: `clang-cl /Zs` (kopia `exebuild/src` + cały ten katalog) – `PythonItemModule.cpp`,
`PythonApplicationModule.cpp`, `PythonPlayerModule.cpp`, `Mt2009Champion.cpp`, `PythonPlayer.cpp`,
`PythonCharacterManager.cpp`, `PythonNetworkStreamPhaseGame.cpp`, `GameLib/ItemData.cpp`, `GameLib/ItemManager.cpp` bez
błędów; preprocesor potwierdza kod za definicją (28.10.2026). Exe nie budowane.
## Druga strona ekwipunku – `MT2009_PLUS_ADDEQ_V1` (`ENABLE_MT2009_ADDEQ`)

Paczka „Official Additional Equipment Page” na naszej bazie (serwer: `server-patches/addeq`, root `uiaddeq.py`). Stronę
trzyma serwer (ukryty magazyn nieaktywnej strony, zamiana przy przełączeniu) – bez nowych pakietów, okien przedmiotów,
pól ekwipunku i stałych `WEAR_*`; paczkowe `WEAR_SECOND_*`, `SetSlotChange`, `net.ChangeEquipment` (CG 208) i
przenumerowany `EWearPositions` **nie** są przeniesione.

| Plik | Zmiana |
|---|---|
| `UserInterface/Locale_inc.h` | `#define ENABLE_MT2009_ADDEQ` |
| `UserInterface/PythonPlayerSkill.cpp` | `__CheckSpecialSkill`: umiejętność 200 „Zmiana strony ekwipunku” idzie od razu do serwera (`SendUseSkillPacket`, bez animacji i celu – jak Kombo 122); poziom 0 → „NOT_YET_LEARN” |
| `UserInterface/PythonApplicationModule.cpp` | `app.ENABLE_MT2009_ADDEQ` (1/0) – root pokazuje umiejętność w pomocniczych tylko z tym exe |

Bez nowego exe: zakładki I / II w oknie ekwipunku działają (komenda `/addeq`), umiejętności 200 w oknie postaci nie ma.
Sprawdzone `clang-cl /Zs` obu plików `.cpp` na kopii źródeł z całą nakładką (29.10.2026).

## Damage Print Improve – `MT2009_PLUS_DAMAGE_PRINT_V1` (`ENABLE_DAMAGE_PRINT_IMPROVE`)

Paczka „Damage Print Improve v26.0.5” (serwer: `server-patches/dmgprint`, paczka klienta `dmgprint` –
`client-2.0.30/tools/dmgprint`). Liczby obrażeń niżej na postaci, nad całym światem (bez testu głębokości), do 11 cyfr,
ikona krytyka / przebicia / obu przy potworze, znaki unik / blok / pudło na graczu, efekty z nowego folderu
`d:/ymir work/effect/affect/damagevalue2/` (stary exe czyta dalej `damagevalue/`). **Bez zmiany pakietu** (paczka
dokładała `dwAttackerVID`): „czy bił gracz” i „pudło” to bity 6/7 we fladze `TPacketGCDamageInfo`.

| Plik | Zmiana |
|---|---|
| `UserInterface/Locale_inc.h` | `#define ENABLE_DAMAGE_PRINT_IMPROVE` |
| `EffectLib/EffectManager.cpp/.h` (**nowe w nakładce**) | `CreateDamageEffect` / `SetSingleParticleTexture` / `UpdateDamageEffect` / `RenderDamageEffect` – osobny `std::set` instancji (Z wyłączone przy rysowaniu); w odróżnieniu od paczki nowa instancja nie zostaje „wybraną” (wisiałby wskaźnik po jej usunięciu), zbiór czyszczony przed danymi efektów (`Destroy`) i w `DeleteAllInstances` |
| `EffectLib/ParticleProperty.cpp/.h`, `ParticleSystemData.cpp`, `ParticleSystemInstance.h` (**nowe w nakładce**) | token `EnableFrustum` w .mse; **brak tokenu = TRUE** (stary test frustum dla wszystkich innych efektów – paczka go wyłączała wszystkim); `EnableFrustum 0` mają znaki unik/blok/pudło/krytyk |
| `UserInterface/InstanceBase.h` | `DAMAGE_ATTACKER_PC` (1<<6), `DAMAGE_MISS` (1<<7); `EFFECT_DAMAGE_DODGE/BLOCK/PENETRATE/MIX_CRITICAL_PENETRATE` na końcu enum (przed `EFFECT_NUM` – żaden numer się nie przesuwa); `SEffectDamage::bTargetIsPC` |
| `UserInterface/InstanceBaseEffect.cpp` | nowe `ProcessDamage` (paczki) z naszą opcją „Pokazuj obrażenia” (brak / tylko cel / wszystkie) i limitem kolejki; `AddDamageEffect` zapisuje `IsPC()` celu |
| `UserInterface/PythonApplication.cpp/.h` | `RenderDamageEffect()` na końcu `RenderGame` (paczka wołała `app.RenderDamageEffect` z `game.py` po nazwach – tu root bez zmian, `PythonTextTail.cpp` bez zmian) |
| `UserInterface/PythonPlayerSettingsModule.cpp` | efekty obrażeń z `damagevalue2/` (+ krytyk, unik, blok, przebicie, krytyk+przebicie) |
| `UserInterface/PythonCharacterManagerModule.cpp` | `chrmgr.EFFECT_DAMAGE_DODGE/BLOCK/PENETRATE/MIX_CRITICAL_PENETRATE` |
| `UserInterface/PythonApplicationModule.cpp` | `app.ENABLE_DAMAGE_PRINT_IMPROVE` (1/0) |

`PythonNetworkStreamPhaseGame.cpp` i `Packet.h` bez zmian. Sprawdzone `clang-cl /Zs` (EffectLib: EffectManager,
ParticleProperty, ParticleSystemData, ParticleSystemInstance, EffectInstance; UserInterface: InstanceBaseEffect,
InstanceBase, PythonApplication, PythonApplicationModule, PythonCharacterManagerModule, PythonPlayerSettingsModule,
PythonNetworkStreamPhaseGame) na kopii `exe-src8` z całą nakładką (29.10.2026).

## Rozszerzony pasek szybkich slotów – `MT2009_PLUS_QUICKSLOT_IMPROVE_V1` (`ENABLE_QUICKSLOT_IMPROVE`)

Paczka „ENABLE_QUICKSLOT_IMPROVE”: przycisk obok slotów rozwija nad paskiem pozostałe 3 strony (4 x 8). Root:
`uitaskbar.py`, `quickslotstate.py` (nowy), `uiscript/expandedquickslot.py` (nowy), `game.py`, `interfacemodule.py`;
obrazki są już w paczce `etc` (`client-2.0.30/tools/quickslot2/verify_quickslot2.py`). Serwer / db bez zmian
(40 slotów = 4 strony x 10 po obu stronach; globalny indeks = strona * 10 + slot, paczka liczyła * 8).

| Plik | Zmiana |
|---|---|
| `UserInterface/Locale_inc.h` | `#define ENABLE_QUICKSLOT_IMPROVE` |
| `UserInterface/PythonPlayer.cpp/.h` | `RequestAddGlobalQuickSlot` / `RequestMoveGlobalQuickSlot` / `RequestUseGlobalQuickSlot` (te same pakiety co lokalne; pozycja przedmiotu jako WORD, bez limitu 255 z paczki) |
| `UserInterface/PythonPlayerModule.cpp` | `player.RequestAddGlobalQuickSlot/RequestMoveGlobalQuickSlot/RequestUseGlobalQuickSlot`, `player.QUICKSLOT_COUNT_PER_LINE` (10), `player.QUICKSLOT_PAGE_COUNT` (4) |
| `UserInterface/PythonApplicationModule.cpp` | `app.ENABLE_QUICKSLOT_IMPROVE` (1/0) |

Z paczki **nie** przeniesione: `player.IsQuickSlotExpanded/SetQuickSlotExpanded` (stan trzyma `quickslotstate.py`) i
`app.AtomicWriteFile` (zwykły zapis pliku `quickslot/<postać>.cfg`). Stary exe: root nie pokazuje przycisku.
Sprawdzone `clang-cl /Zs` `PythonPlayer.cpp`, `PythonPlayerModule.cpp`, `PythonApplicationModule.cpp` (29.10.2026).
## Nawigacja Auto Łowów – `MT2009_PLUS_NAVGRID_V1` (`ENABLE_MT2009_NAVGRID`)

Na bazie Path-Finder V1.0 – autor: @coanitoa97, poradnik: Kolen (analiza: `cache/yohara/pathfinder-analiza.md`).
Siatka mapy `maps/<mapa>/navgrid.bin` z paczki `navgrid` (generator `client-2.0.30/tools/navgrid`), komórka 1 m =
100 jednostek (rozdzielczość attr klienta). Bez paczki/siatki dla mapy: Auto Łowy chodzą jak dotąd.

| Plik | Zmiana |
|---|---|
| `UserInterface/Locale_inc.h` | `ENABLE_MT2009_NAVGRID` |
| `UserInterface/NavGrid.cpp/.h` | **nowe**: wczytanie siatki raz na mapę (brak = zapamiętany, bez ponownych prób i bez wpisów w syserr), A* w oknie wokół startu i celu (+48 komórek, potem +160, bok ≤ 400), pamięć robocza wielokrotnego użytku (znacznik pokolenia zamiast memset), limit węzłów 60000, składowe 4-spójne = ta sama reguła narożników co A* (odpowiedź „nieosiągalny” w O(1)), kara przy ścianie liczona raz przy wczytaniu, blokady tymczasowe jako warstwa bitowa, wygładzanie tylko do przodu (O(n)), punkty w środkach komórek |
| `UserInterface/PythonBackgroundModule.cpp` | **nowy w nakładce**: `background.IsNavReady()`, `FindPath(sx,sy,dx,dy[,maxNodes])` → `[(x,y),...]`, `NavReach(sx,sy,dx,dy)` → 1/0/-1, `IsNavWalkable(x,y)`, `NavBlock(x,y,r)`, `NavBlockClear()` – wszystko w lokalnych pikselach mapy (jak `player.GetMainCharacterPosition`) |
| `UserInterface/UserInterface.vcxproj(.filters)` | `NavGrid.cpp`, `NavGrid.h` |

Format pliku: nagłówek „PXNV” wersja 4 (40 bajtów: pola wersji 3 pakietu + CRC32 plików mapy + wersja generatora),
bity przejścia (1 bit/komórkę), opcjonalnie klasy terenu (2 bity/komórkę). Wersja 3 pakietu też jest czytana.
Root: `uiautohunt.py` (`MT2009_PLUS_AUTOHUNT_NAVGRID_V1`) sprawdza `hasattr(background, 'FindPath')` – stary exe = stare
zachowanie. Sprawdzone `clang-cl /Zs` (`NavGrid.cpp`, `PythonBackgroundModule.cpp`) na kopii `exe-src8` z całą nakładką
(29.10.2026).
## Zaczarowanie Żywiołu Broni – efekt na broni – `MT2009_PLUS_WEAPON_ELEMENT_V1` (`ENABLE_MT2009_WEAPON_ELEMENT`)

Na bazie paczki „[System] Elemental Spell” (WorldArd), przepisane na wzór Szaty Aury: bez nowych pakietów i bez zmian
w strukturach przedmiotów. Serwer (`server-patches/zywiolbroni`) wysyła komendę czatu `WELEMFX <vid> <typ>` (0 brak,
1 Błyskawica, 2 Ogień, 3 Lód, 4 Wiatr, 5 Ziemia, 6 Mrok) przy wejściu postaci w widok i przy zmianie broni/żywiołu – tylko
dla zaczarowania +3 na broni z „gwiazdkami” (reguły wiki i transmutacji liczy serwer). Root `welemfx.py` rejestruje
efekty i woła `chrmgr.SetWeaponElement`; stare exe nie ma tej funkcji – nic się nie dzieje.

| Plik | Zmiana |
|---|---|
| `UserInterface/Locale_inc.h` | `ENABLE_MT2009_WEAPON_ELEMENT` (wymaga `ENABLE_MT2009_AURA`) |
| `UserInterface/Mt2009WeaponElement.cpp` (**nowy**) | `chrmgr.RegisterWeaponElementEffect(typ, rodzaj, plik)`, `chrmgr.SetWeaponElement(vid, typ)`, `chrmgr.GetWeaponElement(vid)`; rodzaje: 0 miecz/dwuręczna, 1 wachlarz (`_f`), 2 łuk (`_b`, lewa ręka), 3 sztylety (obie ręce)/dzwon (`_s`), 4 szpony (obie ręce, `_w`) – jak efekty ulepszenia `sword_7*.mse`; strzała/kołczan nigdy (błąd paczki: strzała dostawała efekt sztyletu) |
| `UserInterface/InstanceBase.h/.cpp` | `m_dwWeaponElement`, `m_dwWeaponElementEffect[2]`; `SetWeapon` po `__GetRefinedEffect` dokłada efekt żywiołu tylko, gdy broń ma właśnie efekt ulepszenia (kostium broni, polimorfia, strój zwierzęcy, niewidzialność – brak); `ChangeArmor` zeruje uchwyty po `SetRace` (SetWeapon dokłada je znowu); `__Initialize` |
| `UserInterface/NetworkActorManager.h/.cpp` | `SNetworkActorData::m_dwWeaponElement` + `SetActorWeaponElement` – nowa instancja aktora (wejście w widok, koń, zmiana kształtu) dostaje żywioł z powrotem |
| `UserInterface/PythonCharacterManagerModule.cpp` | trzy funkcje `chrmgr` |
| `UserInterface/UserInterface.vcxproj(.filters)` | `Mt2009WeaponElement.cpp` |

Pliki efektów (GF 26.1.11, pakuje `client-2.0.30/tools/zywiolbroni`): `d:/ymir work/pc/common/effect/sword/element0{1..6}_{electric,fire,ice,wind,daeji,dark}{,_f,_b,_s,_w}.mse`.
Sprawdzone `clang-cl /Zs` (exe-src8 + cała nakładka + `clang-cl-compat.patch`): `Mt2009WeaponElement.cpp`, `InstanceBase.cpp`,
`NetworkActorManager.cpp`, `PythonCharacterManagerModule.cpp`, `Mt2009Aura.cpp` (29.10.2026).

## Efekty zakładania pierścieni / amuletów / lizaków – `MT2009_PLUS_RING_EFFECTS_V1` (`ENABLE_MT2009_RING_EFFECTS`)

Serwer (`server-patches/ringfx`) przy założeniu 71148 / 71149 / 71158 / 71180 / 71181 / 71188 / 71199 / 71202 / 72054
wysyła `SE_EQUIP_WILL_RING` … `SE_EQUIP_GUARD_PENDANT` = **55–63** (za `SE_ELEC_ATTACK_HIT` 54, ta sama kolejność co
serwer; `static_assert` po obu stronach).

| Plik | Zmiana |
|---|---|
| `UserInterface/Locale_inc.h` | `ENABLE_MT2009_RING_EFFECTS` |
| `Server/common/length.h` | 9 × `SE_EQUIP_*` na końcu `SPECIAL_EFFECT` (zawsze – numery protokołu) |
| `UserInterface/InstanceBase.h` | `EFFECT_WILL_RING_EQUIP` … `EFFECT_GUARD_PENDANT_EQUIP` za efektami Damage Print, `EFFECT_NUM` dalej ostatni |
| `UserInterface/PythonNetworkStreamPhaseGameItem.cpp` | `case SE_EQUIP_*` → `EFFECT_*_EQUIP` |
| `UserInterface/PythonPlayerSettingsModule.cpp` | rejestracja (cache): `d:/ymir work/effect/etc/buff/` `buff_item5`, `deadly_ring`, `buff_symbol1`, `buff_item16`, `green_candy`, `buff_item8`, `buff_item10`, `buff_item13`, `buff_item14` `.mse` |
| `UserInterface/PythonCharacterManagerModule.cpp` | `chrmgr.EFFECT_*_EQUIP` |

Siedem plików to oryginały GF 26.1.11 z paczki `etc` instalacji; `deadly_ring.mse` / `green_candy.mse` (+ tekstury) –
nowa paczka `ringfx` (`client-2.0.30/tools/ringfx`, `verify_ringfx.py` sprawdza też numery SE serwer ↔ exe). Sprawdzone
`clang-cl /Zs` (exe-src8 + cała nakładka + `clang-cl-compat.patch`): `PythonNetworkStreamPhaseGameItem.cpp`,
`PythonCharacterManagerModule.cpp`, `PythonPlayerSettingsModule.cpp`, `InstanceBase.cpp` (30.10.2026).

## Wędkarskie Puzzle (Event Rybacki - Puzzle) – `MT2009_PLUS_FISH_PUZZLE_V2` (`ENABLE_MINI_GAME`, `ENABLE_FISH_EVENT`)

Zmiany źródła exe z paczki właściciela „Mini Game Fish Event (17.3)” („Jigsaw FULL + Fix Scale”, 3.11.2026) z jego
poprawkami. Serwer: `server-patches/fishpuzzle` + `fish_puzzle.cpp`; root: `uifishpuzzle.py`, `uiminigame.py`,
`uiminigamefishevent.py`, `uiscript/minigame*.py`; obrazki: paczka `fishpuzzle` (`client-2.0.30/tools/fishpuzzle`).

| Plik | Zmiana |
|---|---|
| `UserInterface/Locale_inc.h` | `ENABLE_MINI_GAME`, `ENABLE_FISH_EVENT`, `MT2009_SLOT_TYPE_FISH_EVENT 18` |
| `UserInterface/GameType.h` | `SLOT_TYPE_FISH_EVENT` (po `SLOT_TYPE_SWITCHBOT`; `static_assert` == 18), `EFishEventInfo` (`FISH_EVENT_SHAPE_1..7`) |
| `UserInterface/Packet.h` | CG **219** `HEADER_CG_FISH_EVENT_SEND`, GC **223** `HEADER_GC_FISH_EVENT_INFO` (numery paczki, wolne u nas i w serwerze), podnagłówki, `TPacketCGFishEvent` (2 B), `TPacketGCFishEventInfo` (10 B) |
| `UserInterface/PythonNetworkStream*.cpp/.h` | GC 223 stały 10 B → `MiniGameFishUse/Add/Reward/Event` okna gry; `SendFishBoxUse(okno, pole)`, `SendFishShapeAdd(pole)` |
| `UserInterface/PythonNetworkStreamModule.cpp` | `net.SendUseFishBox`, `net.SendAddFishBox` |
| `UserInterface/PythonApplicationModule.cpp` | `app.ENABLE_MINI_GAME`, `app.ENABLE_FISH_EVENT`, `app.FISH_EVENT_SHAPE_1..7`, `app.WJ_ENABLE_TRADABLE_ICON` = 0 |
| `UserInterface/PythonPlayerModule.cpp` | `player.SLOT_TYPE_FISH_EVENT` |
| `EterPythonLib/PythonGridSlotWindow.cpp/.h` (**nowe w nakładce**) | `SetPickedAreaRender`; szerokość 3 w `GetPickedSlotList` (było 2); kształty L/Z (3, 4, 6 – poprawka właściciela „5 → 4”) sprawdzane i rysowane tylko na swoich polach; typ porównywany z `MT2009_SLOT_TYPE_FISH_EVENT` (poprawka skali paczki: „`dwAttachedType == 14/17/19`” – u nas 18) |
| `EterPythonLib/PythonSlotWindow.cpp/.h` | `DeleteCoverButton` (zdejmuje też znak „zawsze rysuj osłonę”); render osłony bez przycisku nie wywołuje NULL |
| `EterPythonLib/PythonWindowManager.cpp/.h` | `SetDisableDeattach` / `IsDisableDeattach` (element zostaje na myszy), pole zainicjowane w konstruktorze |
| `EterPythonLib/PythonWindowManagerModule.cpp` | `wndMgr.SetPickedAreaRender`, `DeleteCoverButton`, `SetDisableDeattach` (zły typ okna = nic). `wndMgr.ResetFrame` / `SetAniImgScale` (poprawka D właściciela) już są – `MT2009_PLUS_MINIGAMES_V1`, z kontrolą typu |

Pętle paczki „erase w for z ++it” (UB na końcu listy) zastąpione `__MT2009_FishPieceRemoveFreeCells` – te same pola (lista
kolumnami: L3 bez 3. pola, L4 bez 2., Z6 bez 2. i 5.). Zbudowane `build.sh msvc --smoke` (exe-src10 = exe-src8 + ta
nakładka, osobny `EXEBUILD_WORK`): `cache/yohara/exe-out10/metin2client.exe`, sha256 `34e2a053…12911d` (z `PythonSwitchbot.cpp` z claude/y-switch), smoke do ekranu
logowania (3.11.2026).

## Bonusy 6/7 z wiki, runda 2 – `MT2009_PLUS_BONUS67_WIKI_V1` (bez `#ifdef`)

Serwer (`server-patches/bonusy67b`) dodał ostatnie trzy numery jednobajtowego typu bonusu: `POINT_RESIST_COMBAT` 253
(„Jeśli masz powyżej 90% PŻ, doznajesz obrażenia niższe o x%”), `POINT_BLEEDING_PCT` 254 („Atak krwawienia”),
`POINT_BLEEDING_REDUCE` 255 („Odporność na atak krwawienia”) i wysyła je jako zmianę punktu (także przy logowaniu).
Bez zmian pakietów (pakiet punktów dalej ma `POINT_PACKET_NUM` 193; typ w zmianie punktu to bajt).

| Plik | Zmiana |
|---|---|
| `Server/common/length.h` | `POINT_RESIST_COMBAT = 253`, `POINT_BLEEDING_PCT = 254`, `POINT_BLEEDING_REDUCE = 255`, `POINT_MAX_NUM` 256 (rozmiar `m_alPoint`, `m_adwPointEffect`) |
| `UserInterface/Mt2009Champion.cpp` | `static_assert` numerów 253–255 i `POINT_MAX_NUM` 256 |
| `UserInterface/PythonPlayerModule.cpp` | `player.POINT_RESIST_COMBAT`, `player.POINT_BLEEDING_PCT`, `player.POINT_BLEEDING_REDUCE` |

Root (`uiattributelist.py`) pokazuje trzy linie okna bonusów tylko, gdy `player.MAX_NUM` > ich numer, więc stary exe
(`POINT_MAX_NUM` 253 – odrzuca typ ≥ 253 w `CPythonPlayer::SetStatus`) ich nie pokazuje i nic się nie psuje; dymek
przedmiotu działa na każdym exe (`localeinfo_point.py`, nazwy po numerze). Sprawdzone: `g++ -fsyntax-only` wyliczenia
`length.h` z `static_assert` 252 / 253–255 / 256.

## Dwubajtowy typ bonusu – `MT2009_PLUS_WIDE_ATTR_V1` (bez `#ifdef`; `server-patches/wideattr`)

Serwer trzyma typ bonusu przedmiotu, punkt efektu i typ zmiany punktu w 2 bajtach (`WORD`, do `POINT_MAX_NUM` 512), więc
każdy pakiet z przedmiotem urósł o 7 B (7 linii × 1 B). Ten exe czyta nowy układ; starszy (1.3.0) jest odrzucany przy
logowaniu (root `constinfo.py` mówi 1.3.1 tylko z `app.MT2009_WIDE_ATTR_EXE`, auth `M2_CLIENT_MIN_VERSION` 1010301).

| Plik | Zmiana |
|---|---|
| `UserInterface/GameType.h` | `TPlayerItemAttribute::bType` `WORD` (linia bonusu 4 B) – zestaw/aktualizacja przedmiotu, sklep, wymiana, przechowalnia, Ikarus, switchbot, podgląd ekwipunku |
| `UserInterface/Packet.h` | `TPacketGCPointChange::Type`, `TPacketAffectElement::bPointIdxApplyOn`, `TPacketGCAffectRemove::bApplyOn` `WORD`; `static_assert` rozmiarów jak na serwerze (linia 4 B, efekt 26 B, usunięcie efektu 7 B, zmiana punktu 18 B, przedmiot sklepu 57 B, podgląd ekwipunku 48 B, filtr Ikarus 86 B, switchbot 20/534/51 B, wyszukiwarka sklepów 103 B) |
| `UserInterface/Mt2009ChangeLook.cpp` | `static_assert`: item set 65 B, item update 52 B, wymiana 65 B, `ikashop::TPlayerItem` 63 B |
| `Server/common/length.h` | `POINT_MAX_NUM = 512` – nowe punkty serwera (256+) trafiają do `m_alPoint` / `player.GetStatus(n)` bez nowego exe |
| `UserInterface/Mt2009Champion.cpp` | `static_assert` `POINT_MAX_NUM` 512; `app.MT2009_WIDE_ATTR_EXE` = 1 |
| `UserInterface/PythonPlayer.h/.cpp`, `AbstractPlayer.h` (**nowy w nakładce**), `PythonPlayerModule.cpp` | `Get/SetItemAttribute` z typem `WORD` |
| `UserInterface/PythonExchange.h/.cpp`, `PythonExchangeModule.cpp` | atrybuty wymiany `WORD` |
| `UserInterface/PythonSwitchbot.h/.cpp` | `SetAttribute`, mapa maksimów i `GetAttributeMaxValue` z typem `WORD`; `switchbot.SetAttribute` / `GetAttributeMaxValue` czytają typ jako liczbę (`PyTuple_GetInteger`), nie bajt |

Rekord `item_proto` klienta (184 B, `TItemApply` z 1-bajtowym typem) **bez zmian**: applies protu zostają 0–255 (panel
waliduje), nowe bonusy 6/7 to linie przedmiotu, nie applies. Sprawdzone: `clang-cl -fsyntax-only -Wconversion` całego
UserInterface/GameLib/EterPythonLib – zero zwężeń `WORD` → `BYTE` w kodzie bonusów; build MSVC (`build.sh msvc --smoke`,
osobny `EXEBUILD_WORK=cache/yohara/exebuild-wide`, źródła `cache/yohara/exe-src11` = exe-src10 + ta nakładka):
`cache/yohara/exe-out11/metin2client.exe` (sha256 `9f72aee7…988aff`), smoke do ekranu logowania (4.11.2026).

## Kolor umiejętności – `MT2009_PLUS_SKILL_COLOR_V1` (`ENABLE_MT2009_SKILL_COLOR`; `server-patches/skillcolor`)

Z paczki właściciela „SKILL_COLOR_SYSTEM by OSWAP (FULL)” – przepisane (opis i różnice: README łatki). Kolor umiejętności
ma pięć warstw (n-ty system cząsteczek efektu, 5. także każdy następny; 0 = własny kolor, inaczej `0xFFrrggbb`).
Cząsteczka zachowuje przezroczystość i jasność (najmocniejszy z r/g/b) i bierze barwę koloru – **kolor instancji**,
wczytane `.mse` nigdy nie są zmieniane (paczka zmieniała współdzielone dane i dlatego robiła kopię każdego efektu na imię
gracza – `GetCaseCRC32(name + file)`, `RegisterEffect(..., name)` – tego tu nie ma). Bez `#define` exe jak dotąd.

| Plik | Zmiana |
|---|---|
| `UserInterface/Locale_inc.h` | `ENABLE_MT2009_SKILL_COLOR` |
| `UserInterface/Packet.h` | CG **56** `HEADER_CG_SKILL_COLOR`, GC **59** `HEADER_GC_SKILL_COLOR` (wolne u nas i na serwerze), `TPacketCGSkillColor` 23 B, `TPacketGCSkillColor` 28 B, `SKILL_COLOR_LAYERS`/`_TYPE_OWN`/`_TYPE_BUFF`, `static_assert` |
| `UserInterface/Mt2009SkillColor.cpp` (**nowy**, + `UserInterface.vcxproj(.filters)`) | `CInstanceBase::Mt2009SetSkillColor/GetSkillColor/GetSkillColorOfFly`, mapa ruch → kolor z `CPythonSkill` (każdy stopień `GradeData`, `wMotionIndex`, `wMotionIndexForMe`; bez 164–167), efekty wzmocnień (własne: 3, 4 – poświata broni, 19, 34, 49, 63, 64, 65, 78, 79; szamańskie 94/95/96/110/111 – kolor rzucającego) zakładane od nowa przy zmianie; `CNetworkActorManager::Mt2009SetSkillColor` (kolory per VID – nowa instancja: widok, koń – dostaje je z powrotem); `RecvSkillColorPacket` / `SendSkillColorPacket`; `player.SetSkillColor(vnum, c1..c5)` / `player.GetSkillColor(vnum)` (−1 = własny, inaczej `0xRRGGBB`), `app.ENABLE_SKILL_COLOR_SYSTEM`, `app.MT2009_SKILL_COLOR_EXE` |
| `UserInterface/UserInterface.cpp` | `Mt2009SkillColor_RegisterPython()` po `Mt2009Champion_RegisterPython()` |
| `UserInterface/PythonNetworkStream.cpp/.h`, `PythonNetworkStreamPhaseGame.cpp` | GC 59 stały 28 B → `RecvSkillColorPacket`; pakiet „fly” serwera (Burzowy Szpon, Ognisty Duch) w kolorze rzucającego |
| `UserInterface/NetworkActorManager.cpp/.h` | kolory per VID: zapisywane tylko dla znanego aktora, nakładane na nową instancję (`__AppendCharacterManagerActor`), usuwane z aktorem / przy czyszczeniu |
| `UserInterface/InstanceBase.cpp/.h`, `InstanceBaseEffect.cpp` | mapa kolorów instancji (czyszczona w `__Initialize`), `__AttachEffect` – kolor efektu wzmocnienia / Aury Miecza |
| `GameLib/ActorInstance.cpp/.h` | `SMt2009SkillColor`, mapa indeks ruchu (− `NAME_SKILL`) → kolor (`Mt2009SetSkillColorOfMotion`, `Mt2009GetSkillColorOfMotion(klucz ruchu)` – każdy tryb: pieszo, konno, broń), `AttachEffectByID(..., c_pdwSkillColor = NULL)` |
| `GameLib/ActorInstanceMotionEvent.cpp`, `ActorInstanceAttach.cpp` | zdarzenia ruchu: efekt, efekt na celu, pocisk – w kolorach bieżącego ruchu |
| `GameLib/FlyingInstance.cpp/.h`, `FlyingObjectManager.cpp/.h` | pocisk pamięta kolory (przed `Create`): jego efekty i trafienie; `CreateFlyingInstanceFlyTarget` / `CreateIndexedFly` z kolorem (domyślnie `NULL`) |
| `EffectLib/EffectManager.cpp/.h`, `EffectInstance.cpp/.h` | `CreateEffect` / `CreateEffectInstance` z kolorem (domyślnie `NULL`), `CEffectInstance::SetMt2009SkillColor` – warstwy na systemy cząsteczek instancji |
| `EffectLib/ParticleSystemInstance.cpp/.h`, `ParticleInstance.cpp/.h` | kolor warstwy w systemie i w każdej cząsteczce (pule czyszczone), `Mt2009SkillColorTint` w `Transform` (`D3DRS_TEXTUREFACTOR`) |

Root: `uiskillcolor.py` (okno), `skillcolorpick.py` (kolor z kliknięcia liczony, nie zrzut ekranu – paczka czytała piksel
ekranu `wndMgr.GetColorAtPosition`, tego nie ma), `uiscript/skillcolorwindow.py`, przycisk w `uicharacter.py`; obrazki –
paczka `skillcolor` (`client-2.0.30/tools/skillcolor`). Bez `player.SetSkillColor` (starszy exe) przycisku nie ma.
Wersja: root `constinfo.py` 1.3.2 tylko z `app.MT2009_SKILL_COLOR_EXE`; auth `M2_CLIENT_MIN_VERSION` 1010302.

**Kolory po relogu** (`MT2009_PLUS_SKILL_COLOR_RELOG_V1`, 4.11.2026): `InstanceBase.h` (deklaracje + 3 pola),
`InstanceBase.cpp` (`__Initialize`: zerowanie; koniec `Update`: sprawdzenie co 0,5 s), `InstanceBaseEffect.cpp`
(`__AttachEffect`: zapis koloru założenia), `Mt2009SkillColor.cpp` (`__Mt2009NoteAttachedSkillColor`,
`Mt2009RefreshAffectSkillColors`, wywołanie na końcu `Mt2009SetSkillColor`) – efekt trwającego wzmocnienia założony
w innym kolorze niż obecny kolor umiejętności zakładany od nowa (README łatki `skillcolor`). exe-src17 = exe-src16 + to;
`cache/yohara/exe-out17/metin2client.exe` (sha256 `c1c31b96…ed305ac`, MSVC 14.44, smoke do ekranu logowania, 5.11.2026).

Zbudowane `build.sh msvc --smoke` (MSVC 14.44; osobny `EXEBUILD_WORK=cache/yohara/exebuild-color`, źródła
`cache/yohara/exe-src14` = exe-src12 + ta nakładka – po scaleniu poprawek 3.0.10 nakładka exe bez innych zmian):
`cache/yohara/exe-out14/metin2client.exe` (sha256 `a7765317…3032e6`), bez ostrzeżeń w zmienionych plikach, smoke do
ekranu logowania (4.11.2026).

## Tytuły – `MT2009_PLUS_TITLES_V1` (`ENABLE_MT2009_TITLES`)

Z paczki właściciela „Official Title System Renewal” – przepisane (opis i różnice: `server-patches/tytuly/README.md`).
Założony tytuł postaci jest rysowany przy jej imieniu: tabliczka z nazwą (lewa/środek/prawa część z
`d:/ymir work/ui/game/title/titles/title_<zasób>.sub`, środek rozciągnięty na nazwę) i – gdy `.sub` ma `sprites` –
animowany baner za nią, albo efekt nad głową (plik efektu z katalogu serwera; zakładany od nowa na nowej instancji: w
zasięgu wzroku, koń, przemiana). Katalog (nazwy, wygląd, zasoby, efekty, kolory) przychodzi z serwera – bez plików
locale. Podgląd w oknie tytułów: efekt wybranego tytułu rysowany do render targetu (indeks 40, `titleSystem.RENDER_TARGET_INDEX`)
na tle okna, przez hook `UI::CRenderTarget` (łańcuch z hookiem Kart Potworów), własną kamerą (cząsteczki zwrócone do
niej) – instancja efektu poza mapą menedżera efektów, więc świat jej nie rysuje (paczka zmieniała w tym celu EffectLib).
Bez `#define` exe jak dotąd; bez zmian w EffectLib/GameLib (paczka: skalowanie efektu z odległością kamery,
`SetAttachingEffectTranslation`, wymuszanie rysowania poza frustum – niepotrzebne).

| Plik | Zmiana |
|---|---|
| `UserInterface/Locale_inc.h` | `ENABLE_MT2009_TITLES` |
| `UserInterface/Packet.h` | CG **185** `HEADER_CG_TITLE`, GC **189** `HEADER_GC_TITLE` (numery paczki; wolne u nas, na serwerze i poza zakresami zwierzaków CG 122–134 / GC 224–236 – `MT2009_PLUS_GROWTH_PET_V1`), struktury jak w `packet.h` serwera (`static_assert` rozmiarów w `Mt2009Titles.cpp`: 6 / 6 / 309 / 8 / 5 / 8 B) |
| `UserInterface/Mt2009Titles.cpp` (**nowy**, + `UserInterface.vcxproj(.filters)`) | dane tytułów, `RecvTitlePacket` / `SendTitlePacket`, efekty nad głową (synchronizacja co klatkę), obrazki przy imieniu, podgląd, moduł `titleSystem`, `app.MT2009_TITLES_EXE` |
| `UserInterface/PythonNetworkStream.cpp/.h`, `PythonNetworkStreamPhaseGame.cpp` | GC 189 dynamiczny → `RecvTitlePacket`; w `SetGamePhase` powitanie (CG 185 OPEN) – serwer wysyła GC 189 tylko klientowi, który się przywitał, więc starszy exe go nie zobaczy |
| `UserInterface/PythonTextTail.cpp` | `ArrangeTextTail` / `Render` / `DeleteCharacterTextTail` / `Clear`: obrazki i nazwa tytułu nad najwyższą linią (imię, gildia, osobowość) |
| `UserInterface/PythonApplication.cpp` | `Mt2009Titles_Update()` w `UpdateGame` (efekty, klatki banerów, efekt podglądu), `Mt2009Titles_Destroy()` |
| `UserInterface/UserInterface.cpp` | `Mt2009Titles_RegisterPython()` po kolorze umiejętności (po hooku Kart Potworów) |
| `EterPythonLib/PythonWindow.h` | `UI::CRenderTarget::GetRenderHook()` – łańcuch hooków |

Python (`titleSystem`): `SetHandler`, `RequestOpen`, `RequestEquip`, `GetTitles`, `GetOwned`, `GetEquipped`,
`IsDataReceived`, `GetPlate`, `SetShowOthers` / `GetShowOthers` („Ukryj tytuły innych graczy” w Opcjach dodatkowych),
`PreviewSelect`, `PreviewShow`, `RENDER_TARGET_INDEX`, `TYPE_TEXT/EFFECT/NAMEPLATE`. Root: `uicharactertitle.py`,
`uiscript/charactertitlewindow.py`, portret w `uicharacter.py`, opcja w `uiopcjedodatkowe.py`; obrazki i efekty – paczka
`tytuly` (`client-2.0.30/tools/tytuly`).

Zbudowane `build.sh msvc --smoke` (MSVC 14.44, `EXEBUILD_WORK=cache/exebuild`, źródła `cache/yohara/exe-src15` =
exe-src14 + ta nakładka): `cache/yohara/exe-out15/metin2client.exe` (sha256 `dac9ca96…61fc0cfd`), bez ostrzeżeń w
zmienionych plikach, smoke do ekranu logowania (4.11.2026).

## System zwierząt domowych – `MT2009_PLUS_GROWTH_PET_V1` (`ENABLE_GROWTH_PET_SYSTEM`)

Oficjalny system zwierzaków (pieczęć, wyklucie z jaja, poziomy, ewolucje 1–6, umiejętności, karmienie, odnawianie życia,
klatka transportowa, zmiana imienia, Sfera Losu, poziom czempiona i sloty potencjału) – przeniesiony ze źródeł Anka2
(`ENABLE_GROWTH_PET_SYSTEM` + `ENABLE_UPBRINGING_PET_CONQUEROR_LEVEL`) według kontraktu wspólnego z serwerem
(`server-patches/pety`) i rootem (`SPEC.md`). Cały kod w jednym nowym pliku `Mt2009GrowthPet.cpp` (jak `Mt2009SkillColor.cpp`),
w pozostałych plikach tylko krótkie bloki za `#ifdef`. Bez `#define` exe jak dotąd.

Różnice względem Anka2: numery GC **224–236** (Anka2 173–184 są u nas zajęte), pozycje karmienia i odnawiania to `TItemPos`
(każde okno ekwipunku, także magazyny specjalne) z liczbą sztuk, `bLocked` jako `BYTE`, punkty czempiona (11–19), nowe GC 235
(wygląd) / GC 236 + CG 134 (sloty potencjału). Nie przeniesione: wzór skali z poziomu (`SetPetLevel`: poziom × 0,2 – błędny),
typ postaci `IsGrowthPet` (serwer tworzy zwierzaka jako zwykłego NPC-zwierzaka), link czatu `petitem:` i pasek szybkich
slotów dla pieczęci. Pakiety dodania postaci bez zmian.

| Plik | Zmiana |
|---|---|
| `UserInterface/Locale_inc.h` | `ENABLE_GROWTH_PET_SYSTEM`, w nim `ENABLE_UPBRINGING_PET_CONQUEROR_LEVEL` |
| `UserInterface/Packet.h` | CG **122–134**, GC **224–236** (wolne w exe-src15), stałe `GROWTH_PET_*`, `EGrowthPetPoints` (`POINT_UPBRINGING_*`, 20 punktów), `EGrowthPetSubheader` (0–15), `PET_WINDOW_*`, `FEED_*`, `PET_POTENTIAL_INSERT/REMOVE`, struktury z `SPEC.md`, `static_assert` każdego rozmiaru (oraz `TItemPos` = 3 B, `ITEM_PET` = 37) |
| `UserInterface/Mt2009GrowthPet.cpp` (**nowy**, + `UserInterface.vcxproj(.filters)`) | odbiór GC 224–236, wysyłanie CG 122–134, dane zwierzaków w `CPythonPlayer`, wczytanie `pet_skill.txt`, skala z GC 235 w `CNetworkActorManager`, funkcje i stałe Pythona (niżej) |
| `UserInterface/PythonNetworkStream.cpp/.h` | GC 224–236 zarejestrowane jako pakiety stałej długości (`STATIC_SIZE_PACKET`), deklaracje `RecvGrowthPet*` / `SendPet*` |
| `UserInterface/PythonNetworkStreamPhaseGame.cpp` | `case` GC 224–236; koniec wymiany (`EXCHANGE_SUBHEADER_GC_END`) usuwa zwierzaki partnera (GC 226) |
| `UserInterface/PythonPlayer.h/.cpp` | `SGrowthPet` / `SGrowthPetSkill` / `SGrowthPetPotential`, mapy po id zwierzaka (= gniazdo 2 pieczęci / klatki), aktywny zwierzak, flagi okien; `Clear()` czyści (serwer wysyła je znowu po wejściu) |
| `UserInterface/NetworkActorManager.cpp/.h` | GC 235: skala per VID (także zanim instancja powstanie), nakładana na każdą nową instancję (`__AppendCharacterManagerActor`), usuwana z aktorem / przy teleportacji / czyszczeniu |
| `UserInterface/PythonApplication.cpp` | `LoadLocaleData`: `locale/<język>/pet_skill.txt` (jak `SkillDesc.txt`), zapasowo `locale/pl/pet_skill.txt`; brak pliku to tylko wpis w logu |
| `UserInterface/UserInterface.cpp` | `Mt2009GrowthPet_RegisterPython()` po wymianie wyglądu (po modułach app/player/item/net/skill) |

Pakiety (wszystkie stałej długości; rozmiary w B): GC 224 `PET` 2 (podnagłówek), 225 `PET_SET` 131, 226 `PET_SET_EXCHANGE` 131,
227 `PET_DEL` 5, 228 `PET_SUMMON` 5, 229 `PET_POINT_CHANGE` 10, 230 `PET_NAME_CHANGE_RESULT` 27, 231 `PET_DETERMINE_RESULT` 2,
232 `PET_ATTR_CHANGE_RESULT` 5, 233 `PET_SKILL_UPDATE` 266, 234 `PET_SKILL_COOLTIME` 10, 235 `PET_LOOK` 9, 236 `PET_POTENTIAL` 26;
CG 122 `PET_HATCH` 25, 123 `PET_WINDOW_TYPE` 2, 124 `PET_WINDOW` 3, 125 `PET_NAME_CHANGE` 28, 126 `PET_FEED` 47,
127 `PET_DETERMINE` 4, 128 `PET_ATTR_CHANGE` 7, 129 `PET_REVIVE` 54, 130 `PET_LEARN_SKILL` 5, 131 `PET_SKILL_UPGRADE` 2,
132 `PET_DELETE_SKILL` 5, 133 `PET_DELETE_ALL_SKILL` 4, 134 `PET_POTENTIAL` 6.

GC 235: skala modelu = skala rasy NPC (tabela skal) × `wScalePct / 100` (100 = bez zmian, 0 traktowane jak 100, najwyżej
1000), tylko dla instancji nie-gracza. Serwer musi wysłać GC 235 po każdym dodaniu zwierzaka u widza (wyjście z zasięgu
usuwa zapamiętaną skalę). `bEvolution` / `bType78` na razie nieużywane.

Python:
- `net`: `SendPetHatchingPacket(name, window, cell)`, `SendPetHatchingWindowPacket(state)`, `SendPetNameChangeWindowPacket(state)`
  (okno `PET_WINDOW_NAME_CHANGE` – Anka2 wysyłała tu omyłkowo `PET_WINDOW_HATCH`), `SendPetWindowType(type)`,
  `SendPetFeedPacket(index, [(window, cell, count), ...])` (do 9; `FEED_EVOL_EVENT` z pustą listą), `SendPetAttrDetermine(window, cell)`,
  `SendPetAttrChange(sealWindow, sealCell, itemWindow, itemCell)`, `SendPetRevive(sealWindow, sealCell, [(window, cell, count), ...])`
  (do 10), `SendPetLearnSkill(slot, window, cell)`, `SendPetSkillUpgradeRequest(slot)`, `SendPetDeleteSkill(slot, window, cell)`,
  `SendPetDeleteAllSkill(window, cell)`, `SendPetNameChangePacket(name, scrollWindow, scrollCell, sealWindow, sealCell)`,
  `SendPetPotential(action, slot, window, cell)`, `CheckUsePetItem()` (zawsze `PET_EGG_USE_TRUE`). Listy przyjmują też stary
  zapis Anka2 (`[cell, ...]`, `[count, ...]` – główny ekwipunek).
- `player`: `GetPetItem(petId)` → `(vnum, level, evolution, hp, def, sp, lifeEnd, maxLife, birthday, exp, itemExp, nextExp,
  championLevel, championExp, championItemExp, championNextExp, res, blockPen, precision, type, skillSlots, name)` (hp/def/sp/
  res/blockPen/precision w 0,001 %; nieznany zwierzak: zera i `""`), `GetPetSkill(petId, slot)` → `(skill, level, cooltime)`
  (z jednym argumentem krotka Anka2 z 10 wartości), `GetPetSkillByIndex(petId, slot, skillLevel 1..20)` → `(activatePct,
  valueTenths, durationTenths)` (z dwoma argumentami krotka Anka2 z 9 wartości), `GetPetPotential(petId, slot)` → `(eggVnum,
  skill, level, endTime)`, `GetPetPotentialSlots(petId)`, `GetPetLifeTime(petId)` → `(lifeEnd, maxLife)`, `GetPetExpPoints(petId)`
  → `(exp, mobExpNeeded, itemExp, itemExpNeeded)` (podział `NEXT_EXP * 9 / 10` / reszta), `GetPetChampionExpPoints(petId)`
  (to samo dla czempiona), `IsPetExchange(petId)`, `GetActivePetItemId()`, `GetActivePetItemVNum()`, `GetPetItemVNumInBag(petId)`,
  `SetOpenPetHatchingWindow/NameChangeWindow/FeedWindow(bool)`, `IsOpenPetHatchingWindow/FeedWindow/NameChangeWindow()`; stałe
  `PET_FEED_SLOT_MAX`, `PET_REVIVE_MATERIAL_SLOT_MAX`, `PET_SKILL_COUNT_MAX`, `PET_GROWTH_SKILL_LEVEL_MAX`, `PET_GROWTH_EVOL_MAX` (6),
  `PET_GROWTH_SKILL_OPEN_EVOL_LEVEL` (4), `PET_POTENTIAL_SLOT_MAX`, `PET_MAX_LEVEL`, `PET_CHAMPION_MAX_LEVEL`, `PET_HATCHING_MONEY`,
  `PET_SKILL_UPGRADE_PRICE`, `PET_NAME_MIN/MAX_SIZE`, `LIFE_TIME_FLASH_MIN_TIME`, `SPECIAL_EVOL_MIN_AGE`, `PET_ATTR_DETERMINE_ITEM`,
  `PET_ATTR_CHANGE_ITEM`, `FEED_*`, `PET_WINDOW_*`, `PET_POTENTIAL_INSERT/REMOVE`, `POINT_UPBRINGING_*`.
- `skill`: `GetPetSkillInfo(id)` → `(name, description, type, cooldown)`, `GetPetSkillIconImage(id)` (obrazek przy pierwszym
  użyciu), `GetPetSkillIconPath(id)` (`d:/ymir work/ui/skill/pet/<ikona>.sub`), `PET_SKILL_USE_TYPE_NONE/PASSIVE/AUTO/MAX`.
- `item`: `ITEM_TYPE_GROWTH_PET` (= `ITEM_PET` 37), podtypy `PET_EGG` … `PET_PRIMIUM_FEEDSTUFF` (0–13), `ITEM_ANTIFLAG_PETFEED` (0),
  `EGG_USE_*`, `PET_EGG_USE_*`, `NAME_CHANGE_USE_*`, `PET_NAME_MIN/MAX_SIZE`, `PET_HATCHING_MONEY`, `PET_ATTR_CHANGE_ITEMVNUM`.
- `app`: `ENABLE_GROWTH_PET_SYSTEM`, `ENABLE_UPBRINGING_PET_CONQUEROR_LEVEL`, `MT2009_GROWTH_PET_EXE` (bramka wersji w root `constinfo.py`).
- Okno gry: `PetHatchingWindowCommand(i)`, `PetFeedReuslt(i)` [sic], `PetReviveResult(i)`, `PetWindowTypeResult(i)`,
  `PetNameChangeWindowCommand(i)` (0 sukces, 1 złe imię – także z GC 224 podnagłówki 8/9), `PetAffectShowerRefresh()` (GC 233,
  przywołanie / odwołanie / usunięcie aktywnego), `PetAttrDetermineResult(type)`, `PetAttrChangeResult(cell, type)`,
  `PetEvolveResult(1)`, `PetPotentialResult(0/1)`, `PetPotentialRefresh(petId)` (GC 236), `PetInfoRefresh(petId)` (po GC 225/226,
  227, 228, 229, 230 sukces, 233, 236 i odwołaniu), `RefreshInventory` przy przywołaniu / odwołaniu.

Zbudowane `build.sh msvc --smoke` (MSVC 14.44, osobny `EXEBUILD_WORK=cache/yohara/exebuild-pety`, źródła
`cache/yohara/exe-src16` = exe-src15 (z tytułami) + ta nakładka): `cache/yohara/exe-out16/metin2client.exe` (sha256
`b23d3c15…b40e4fc7`), bez ostrzeżeń w zmienionych plikach, smoke do ekranu logowania (4.11.2026).

## Enasir (przywoływalny dozorca / handlarz) – `MT2009_PLUS_REMOTE_CALL_V1` (`ENABLE_MT2009_REMOTE_CALL`)

Z paczki „Official Remote Call” (Khaled / LungSam) – przepisane, nie skopiowane (opis, przedmioty i różnice:
`server-patches/remotecall/README.md`). Serwer decyduje o wszystkim (buffy Dozorca / Handlarz Enasir, gdzie wolno
przywołać, odstęp 10 s); exe tylko pamięta, co serwer ostatnio przysłał, i podaje to pythonowi. Bez listy nazw map w
kliencie (paczka miała ją w exe) i bez `SetHandler` z mocną referencją – zdarzenia idą do okna gry. Rozmiar pakietu
skrzyni (`TPacketGCSafeboxSize`) bez zmian – „magazyn Enasira” to osobny podpakiet, więc starszy exe działa jak dotąd.

| Plik | Zmiana |
|---|---|
| `UserInterface/Locale_inc.h` | `ENABLE_MT2009_REMOTE_CALL` |
| `UserInterface/Packet.h` | CG **190** `HEADER_CG_REMOTE_CALL` (2 B + bajt sekwencji: `HELLO` 0, `SUMMON` 1, `UNSUMMON` 2), GC **190** `HEADER_GC_REMOTE_CALL` (14 B, stały: `STATE` 0, `SUMMONED` 1, `GONE` 2, `MESSAGE` 3, `SAFEBOX` 4), `static_assert` rozmiarów; wolne w exe i na serwerze (paczka: GC 235 – u nas skala zwierzaka) |
| `UserInterface/Mt2009RemoteCall.cpp` (**nowy**, + `UserInterface.vcxproj(.filters)`) | stan (końce buffów, przywołania i odstępu jako czas zegarowy), `SendRemoteCallPacket` / `RecvRemoteCallPacket`, ruch `SPAWN` Enasira po `SUMMONED`, moduł `remoteCall`, `app.MT2009_REMOTE_CALL_EXE` |
| `UserInterface/PythonNetworkStream.cpp/.h`, `PythonNetworkStreamPhaseGame.cpp` | GC 190 stały → `RecvRemoteCallPacket`; w `SetGamePhase` stan czyszczony i powitanie (CG 190 HELLO) – serwer odpowiada tylko na pakiety tego exe |
| `UserInterface/UserInterface.cpp` | `Mt2009RemoteCall_RegisterPython()` po tytułach |

GC 190: `STATE` v0 = sekundy buffa magazynu, v1 = sekundy buffa sklepu (0 brak), v2 bit0 = przywołanie dozwolone na tej
mapie; `SUMMONED` v0 = ile sekund Enasir zostaje (180), v1 = jego VID; `GONE` v0 = sekundy odstępu (10); `MESSAGE` v0 =
kod komunikatu (teksty w root); `SAFEBOX` = następne okno magazynu jest magazynem Enasira. Po każdym podpakiecie okno gry
dostaje `BINARY_RemoteCall_Event(sub, v0)`.

Python (`remoteCall`): `SendPacket(sub)`, `GetBuffLeft(BUFF_SAFEBOX|BUFF_SHOP)` (sekundy, 0 brak), `GetSummonLeft()`,
`GetCoolLeft()`, `GetNpcVID()`, `IsAllowedHere()`, `IsSafeboxRemote()` / `SetSafeboxRemote(i)`, `Clear()`; stałe
`CG_HELLO/SUMMON/UNSUMMON`, `GC_STATE/SUMMONED/GONE/MESSAGE/SAFEBOX`, `BUFF_SAFEBOX` 0, `BUFF_SHOP` 1, `MOB_VNUM` 20874,
`SUMMON_SEC` 180, `COOLTIME_SEC` 10, `MAX_BUFF_SEC` 86400000 (1000 dni).

Zbudowane `build.sh msvc --smoke` (MSVC 14.44, `EXEBUILD_WORK=cache/exebuild`, źródła `cache/yohara/exe-src19` =
exe-src18 (tytuły, zwierzaki, kolory po relogu, ruch podnoszenia) + ta nakładka, kopia na twardych linkach):
`cache/yohara/exe-out19/metin2client.exe` (sha256 `eceb7ee6…2b561a6e9f`), bez ostrzeżeń w zmienionych plikach, smoke do
ekranu logowania (5.11.2026).

## Języki klienta – `MT2009_PLUS_LANG_V1` (`ENABLE_MT2009_LANG_CODEPAGE`; `client-patches/lang`, `tools/lang`)

Stary system języków (nakładka `locale/<język>/` na polski, `LANGUAGE` w `game1.cfg`) działał tylko dla angielskiego:
strona kodowa była na sztywno 1250, a język bez własnego `skilldesc.txt` zatrzymywał klienta (`RegisterSkillDesc`).

| Plik | Zmiana |
|---|---|
| `UserInterface/Locale_inc.h` | `ENABLE_MT2009_LANG_CODEPAGE` |
| `UserInterface/UserInterface.cpp` | `Mt2009Lang_ApplyCodePage()` zaraz po `new CPythonApplication` (game1.cfg wczytany, paczki otwarte): `CODEPAGE` z `locale/<język>/language.cfg` w paczkach (paczka `lang` z buildu), inaczej wbudowana tabela (pl/cz/hu/ro 1250, en/de/es/fr/it/pt 1252, gr 1253, tr 1254, ae 1256), inaczej 1250 → `MULTI_LOCALE_CODE` + `SetDefaultCodePage`; język bez `locale/<język>/skilldesc.txt` w paczkach wraca na `pl` |
| `UserInterface/PythonApplication.cpp` | `LoadLocaleData`: brak `skilldesc.txt` języka → `locale/pl/skilldesc.txt` zamiast błędu |
| `UserInterface/PythonApplicationModule.cpp` | `app.MT2009_LANG_CODEPAGE` (root `mt2009lang.py`: ten exe pokazuje każdy język) i `app.Mt2009Restart()` (ten sam exe, ta sama linia poleceń i katalog, potem `Exit`) |

Zmiana języka działa od następnego startu klienta (exe czyta nazwy, opisy i stronę kodową przy starcie). Bez tego exe
(exe-src20 i starsze) root oferuje tylko języki czytelne w 1250 (pl, en, de, ro, cz, hu – lista `works_on_1250_exe` w
`locale/common/mt2009_languages.txt`). Sprawdzone `clang-cl /Zs` trzech plików na kopii źródeł exe-src20 z tą nakładką
(5.11.2026, z wymuszonym `ENABLE_MT2009_LANG_CODEPAGE`). Kopia źródeł do budowy: `cache/yohara/exe-src21` (= exe-src20 na
twardych linkach + te cztery pliki + `UserInterface/PythonSkill.cpp`, patrz niżej).

`UserInterface/PythonSkill.cpp` (`MT2009_PLUS_PY_NONE_FIX_V1`): `skill.GetSkillConditionDescription` dla indeksu poza
listą zwracało `Py_BuildValue("None")` – format `N` bierze `PyObject*`, którego nikt nie podał (śmieć ze stosu, potem
zwolniony przez Pythona → uszkodzenie sterty); teraz `Py_BuildNone()`. Innych takich wywołań w źródłach nie ma.

Zbudowane `build.sh msvc --smoke` (MSVC 14.44) do `cache/yohara/exe-out21` (exe, map, pdb, zrzut smoke) dla łatki
klienta testowego 3.0.16.
