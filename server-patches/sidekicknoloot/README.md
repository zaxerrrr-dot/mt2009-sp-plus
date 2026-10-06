# Towarzysz: „Drop: tylko dla mnie”

Poprawka silnika, znacznik `MT2009_PLUS_SIDEKICK_NO_LOOT_V1`. Nakładana przy
przygotowaniu wydania (`tools/port/Apply-MT2009PlusEngine.ps1`, po
`rankpoints` i `azcostume`); `Apply-SidekickNoLootPatch.ps1` i linuksowy
bliźniak `apply_sidekicknoloot.py <game/src>` czytają ten sam `edits.json`.
Edycja już obecna jest pomijana, więc skrypt działa na świeżym i na już
załatanym drzewie.

## Co było nie tak

Gdy z Metina lub bossa wypada kilka przedmiotów, `CHARACTER::Reward`
(`char_battle.cpp`) rozdaje własność po kolei każdemu, kto zadał co najmniej
10% obrażeń, a każdy taki udział jeszcze raz po kolei w jego grupie
(`CParty::GetNextOwnership`). Towarzysz jest w grupie gracza, więc co drugi
przedmiot leżał „na niego”, a podniesienie go przez gracza (gałąź grupowa
`CHARACTER::PickupItem`, `char_item.cpp`) wkładało go do plecaka towarzysza.
Gdy to towarzysz zadał najwięcej obrażeń, cały pojedynczy drop był jego,
a Cor Draconis i Delikatne Sukno z jego zabójstwa szły od razu do jego
plecaka (`item_manager.cpp`).

## Co robi poprawka

Wszystko przez jedną funkcję nakładki, `Mt2009PlusSidekickLootReceiver`
(`playerbot_manager.cpp` / `playerbot_sidekick.h`): gdy właściciel ustawił
w oknie Towarzysza „Drop: tylko dla mnie” (`/towarzysz podzial 0`, szeptem
„nie zbieraj dropu”) i stoi w pobliżu (ta sama mapa, zasięg zaliczenia
zabójstwa), udział towarzysza dostaje właściciel:

| Edycja | Plik | Co |
|---|---|---|
| `(single)` | `char_battle.cpp` | pojedynczy drop – właścicielem jest gracz, nie towarzysz |
| `(share)` | `char_battle.cpp` | podział kilku przedmiotów – kolej towarzysza przypada graczowi |
| `(pickup)` | `char_item.cpp` | przedmiot „na towarzysza” sprzed przełączenia, podniesiony w grupie, trafia do gracza |
| `(cloth)`, `(cor)` | `item_manager.cpp` | Sukno i Cor z zabójstwa towarzysza zostają na ziemi i są gracza |

Domyślnie (`share_loot=1` w `player.playerbot_sidekick`) wszystko działa jak
dotąd. Towarzysz z wyłączonym podziałem nic nie podnosi dla siebie przy
właścicielu; drop właściciela nadal może mu zbierać („Twój drop”), a „Pełne
EQ” działa jak wcześniej. Daleko od właściciela (np. „Wolna ręka”) jego
zabójstwa zostają jego.
