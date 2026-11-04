# fishglobal – łowienie jak na globalu (Yohara 3.x)

Znacznik: `MT2009_PLUS_FISHING_GLOBAL_V1` (właściciel, 4.11.2026: `cache/yohara/decyzje-lowienie-mikstury.md`,
sekcja „Łowienie” 1–13 i Wędka Węglowa; analiza `cache/yohara/lowienie-analiza.md`). Logika silnika:
`linux-port/overlays/playerbot/src/game/src/fish_global.cpp`, tu tylko haki (`gen_edits.py` → `edits.json`,
`apply_fishglobal.py` / `Apply-FishGlobalPatch.ps1`). Kolejność: po `chestsash`, `konie`, `fishpuzzle` i `fishren` –
np. na końcu listy.

## Haki (7)
- `fishing.cpp` **decl / chance** – szansa brania +10 % z Rybimi Wnętrznościami: premium ItemShopu **albo założony
  przedmiot** 71008 / 72013–72015 (grupa unikatowa 10009 – wcześniej założone Wnętrzności nic nie dawały) **albo bonus
  Złotego Tuńczyka** (efekt 742; quest `zloty_tunczyk`). Do tego jak dotąd Kula Rybaka +2 % i wędka `value5`
  (poziom / 2: +20 = 10 %, Wędka Węglowa 12 %).
- `fishing.cpp` **refinable** – ulepszyć można tylko wędkę z następnym stopniem (nie +20, nie Wędkę Węglową, której
  socket 0 to czas końca).
- `fishing.cpp` **rod fail** – nieudane ulepszenie: wędka zostaje, traci 10 % punktów (pl-wiki „Wędka”, od 15.7;
  Owsap `__REFINE_FISHINGROD_RENEWAL__`). Wcześniej: nowa wędka z `value4` bez punktów. Szansa to `value3` wędki
  (+1 → 100 %, potem 39 %), bez materiałów i Yang.
- `char_item.cpp` **fisher take** – Rybak (9009) nie otwiera już okna ulepszania (refine_proto 411–419, ryby + Yang);
  każda wędka idzie do jego rozmowy (quest `rybak_wedki` → `__fish_real_refine_rod` → `fishing::RealRefineRod`).
- `char_item.cpp` **chest sash** – Skrzynia Nimfy Wodnej (27625) nie losuje szarfy jak skrzynie bossów (jak Złota /
  Srebrna Szkatułka).
- `item_manager.cpp` **nimfa drop** – Skrzynia Nimfy Wodnej wypada z każdego potwora od 70 poz. (nie z Metinów), jak
  wiersz „Type drop” potwora: flaga eventu `nimfa_chest_drop` = wartość wiersza × 100 (0 → domyślnie 200, czyli
  wiersz „2” = 0,5 % na zabicie przed różnicą poziomów i bonusami dropu; ujemna – wyłączone).

## Reszta systemu (poza tą łatką)
- przedmioty: `mariadb/playerbot/yohara_lowienie.sql` (`tools/yohara_lowienie/gen_ylowienie.py`, apply.sh);
- połów: `linux-port/docker/game/lowienie/fishing_drop.lua`, `fishing.lua` (quest/libs/fishing, Dockerfile);
- questy: `quest/rybak_wedki.quest` (ulepszanie, Wędka Węglowa), `quest/zloty_tunczyk.quest` (wypuść / pokrój /
  przynęta);
- skrzynia: `lowienie/special_item_group.lowienie.txt`, przepis: `lowienie/cube.lowienie.txt` (Rybak 9009);
- boty: `playerbot_activities.h` (ulepszanie przez `RealRefineRod`, Rybie Wnętrzności na czas łowienia).

Linux/VPS: `python3 apply_fishglobal.py <game/src>`; Windows: `Apply-FishGlobalPatch.ps1 -SourceDir <game/src>`
(wołane przez `tools/port/Apply-MT2009PlusEngine.ps1`).
