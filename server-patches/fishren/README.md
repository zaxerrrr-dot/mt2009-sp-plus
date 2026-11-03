# fishren – nowa minigra wędkarska (fishing renewal)

Znacznik: `MT2009_PLUS_FISHING_RENEWAL_V1` (właściciel, 3.11.2026: „Naszą mini grę wędkarską zastąp tą wersją” –
github.com/amun3808/metin2-fishing-renewal). Logika: `linux-port/overlays/playerbot/src/game/src/fish_renewal.cpp`,
tu tylko haki (`gen_edits.py` → `edits.json`, `apply_fishren.py` / `Apply-FishRenPatch.ps1`). Kolejność: po
`enginefixes` (MT2009_PLUS_FISHING_FREE_V1 w `CHARACTER::fishing`) i po `fishpuzzle` – np. na końcu listy.

## Licencja źródła
Repozytorium nie ma pliku LICENSE (Readme bez warunków użycia, tylko „no support”). Grafiki są GF 26.1.11
(`d:/ymir work/ui/fishing_01.dds`, `ui/game/fishing/**.sub`) – bierzemy je z naszej rozpakowanej kopii klienta GF,
bajt w bajt te same co w repozytorium (różnią się tylko końcami linii w `.sub`). Okno klienta jest przeróbką
`uifishinggame.py` / `uiscript/fishinggamewindow.py` z repozytorium (te same stałe, układ i zasady trafień; ruch ryby
liczony w czasie, bez funkcji nowego exe); serwer napisany od nowa (łatka repozytorium jest na inny silnik).

## Rozgrywka (pl-wiki „Łowienie”)
1. Zarzucasz wędkę (spacja) – „po chwili” ryba bierze (domyślnie 5–10 s; stara minigra: 17 s), wędka drga z „!”.
2. Otwiera się okno: ryba pływa po wodzie, trzeba ją kliknąć **3 razy**, gdy jest w kole pośrodku (koło czerwienieje),
   w **15 s**. Trafienie liczy się co najmniej sekundę po poprzednim; kliknięcie obok („Miss”) zabiera 1 s z zegara.
3. 3 trafienia → „spróbujesz złapać rybę (nadal możesz jej uniknąć)”: rzut szansy wędki jak dotąd
   (`fishing::GetFishingChance` – Rybie Wnętrzności, premium Złotego Tuńczyka, wartość wędki – plus „litość”
   `m_iFishingChanceBonus` +2 za każdą nieudaną). Sukces = to samo co wygrana starej minigry
   (`fishing::ProcessFishingGameSuccess`: quest `fishing_manage.success` daje rybę, animacja połowu, **hak Eventu
   Rybackiego – Puzzle** `Mt2009FishPuzzleOnCatch` działa bez zmian), punkty wędki (`FishingPractice`), przynęta zużyta.
   Porażka rzutu: „Ryba się zerwała z haczyka.”, przynęta zużyta, punkty wędki jak przy przegranej starej minigry.
4. Za mało trafień / koniec czasu / zamknięcie okna (X, Esc) → przynęta stracona. Spacja albo ruch postacią w trakcie
   (exe wysyła wtedy pakiet łowienia) = wyciągnięcie wędki – też bez ryby (jak w renewalu: `fishing(0)`).

Flagi eventu (0 = domyślnie): `fishren_bite_min` / `fishren_bite_max` (s do brania, 5 / 10), `fishren_time` (15),
`fishren_hits` (3).

## Exe – bez zmian
Renewal wymaga nowego exe (3. bajt w CG 82 FISHING z wynikiem, `wndMgr.AniImageSetRotation`, kursor wędki
`app.FISH`, emotka porażki, wywołania pythona z `RecvFishing`). U nas wszystko idzie kanałem komend czatu, jak
fishpuzzle/worldboss:

- klient → serwer: `/fishren hello` (po każdym wejściu i teleporcie, blok hello w `game.py`),
  `/fishren end <token> <trafienia>`
- serwer → klient (`game.py` „FISHREN” → `uifishingrenewal.py`): `FISHREN start <token> <sekundy> <trafienia>`,
  `FISHREN stop`

Animacje wędki to istniejące pakiety GC 89 (START / REACT / SUCCESS / FAIL / STOP). Rybę obracamy przez
`wndMgr.SetRotation` (ExpandedImageBox, jest w naszym exe; 4 klatki jako 4 obrazki). Kursor `app.FISH` – tylko jeśli
kiedyś exe go dostanie (`hasattr`). Nowych nagłówków pakietów nie ma – nic nie koliduje.

## Zgodność
- Stary klient (stary root) nie mówi `hello` → dostaje starą minigrę z paskiem (fishing.cpp, GC 155) bez zmian.
  Nowy root na serwerze bez łatki: `start` nigdy nie przychodzi, działa stara minigra.
- Zarzucenie w pierwszych sekundach po wejściu (przed `hello`) → stara minigra (nowy root ją nadal ma).
- `hello` jest pamiętane na pid + uchwyt połączenia (`DESC::GetHandle`) – relog starym klientem nie dostaje okna.
- Boty nie wysyłają `hello` → łowią dokładnie jak dotąd (`playerbot_activities.h`, reakcja 1,9–3,3 s + pasek).
- Zarzucenie żyje w `m_pkPreFishingEvent` (własny `EVENTINFO`), więc wszystkie testy „czy łowi” (koń, zmiana
  ekwipunku, addeq, boty) działają; `CHARACTER::fishing()` oddaje takie zarzucenie `Mt2009FishRenPull` przed starym
  `fishing_take`.

## Walidacja (renewal nie ma żadnej)
Losowy token na każde branie; wynik tylko w trakcie tej gry; 3 trafienia nie wcześniej niż 2 s od otwarcia okna (okno
pozwala na trafienie co sekundę) i nie później niż limit + 3 s; połów i tak rozstrzyga rzut szansy serwera – fałszywe
„3 trafienia” daje tyle, co dobra gra. Odrzucony wynik → `sys_log` „FISHREN: … result refused”.

## Klient
- root: `uifishingrenewal.py`, `uiscript/fishingrenewalwindow.py` (bez importów – Sandbox), `game.py`
  (komenda „FISHREN”, `Start()` w bloku hello, `DestroyWindow()`).
- grafiki: `client-patches/client-2.0.30/tools/fishren` – paczka „fishren” (fishing_01.dds + 15 `.sub`) + linia w
  `Index`; `build_fishren_pack.py` + `verify_fishren.py`. clientY.sh:
  `S_fishren() { docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/fishren/build_fishren_pack.py $C/azbase $C/out/pack; }; step fishren $C/fishren.json S_fishren`
  i `fishren/verify_fishren.py` w pętli weryfikatorów.
