# Odnowione okno misji – `MT2009_PLUS_QUEST_RENEWAL_V1`

Na paczce **QUEST_RENEWAL 1.0.0.6** ((C) 2019 Owsap Productions). Misje w karcie postaci w 8 zwijanych kategoriach
(jak w oficjalnym kliencie), jeden list z boku ekranu zamiast kolumny listów.

Paczka dokłada kategorię do pakietu `packet_quest_info` (`c_index`, zmiana pakietu + exe). U nas **bez zmiany
pakietów i exe**: rdzeń przy wejściu do gry wysyła klientowi mapę „indeks misji → kategoria” jako komendy
`QuestCategory <część> <indeks>:<kategoria>,...` (część 0 czyści mapę). Stary klient komendę pomija, boty
(desc bota) są pomijane, przepływ misji (pakiety, `send_letter`, `button`/`info`) bez zmian.

| Plik | Zmiana |
|---|---|
| `input_login.cpp` (`edits.json`) | `QuestRenewalOnLogin(ch)` po `ChampionOnLogin` w `Entergame` |
| `linux-port/overlays/playerbot/src/game/src/playerbot_quest_renewal.cpp` | tabela kategorii i wysyłka |

Kategorie: 0 główne, 1 poboczne, 2 łowieckie, 3 wydarzenia, 4 Biolog/zioła, 5 pozostałe (domyślna, nie wysyłana),
6 zwoje misji, 7 dzienne. Opcjonalnie `<katalog misji>/questcategory.txt` (format paczki: `<kategoria><tab><nazwa
misji>`) dopisuje lub zmienia przypisania bez przebudowy – czytany przy każdym logowaniu.

Klient: root `questrenewal.py`, `uicharacter.py`, `interfacemodule.py`, `game.py`, `uiscript/characterwindow.py`;
obrazki w paczce „questren” (`client-2.0.30/tools/questren`).

- `Apply-QuestRenPatch.ps1` – Windows (wołany z `tools/port/Apply-MT2009PlusEngine.ps1`, na końcu),
- `apply_questren.py` – Linux/VPS: `python3 apply_questren.py <game/src>`; oba czytają ten sam `edits.json`.
