# Dźwięk podnoszenia (Digi Rasta, wygody klienta) – strona serwera

**Autor: Digi Rasta** (paczka „nowy-system” v0.23.0, wpis 0.19.0 „Biore: małe systemy klienta”,
Pick-Up-Sound-Effect). Przeniesione do MT2009 PLUS jako nasz kod, bez haków `zastosuj.py`.
Znacznik: `MT2009_PLUS_DIGI_CLIENT_QOL_V1`.

## Co robi

Gdy prawdziwy gracz podnosi przedmiot (Z, `~`, zwierzak zbierający do właściciela) albo Yang,
serwer wysyła jego klientowi komendę czatu `PickupSound <vnum>` (`1` = Yang). Klient
(`game.py` → `digiqol.py`) gra dźwięk według rodzaju: Yang `money.wav`, broń
`equip_metal_weapon.wav` (łuk, strzały `equip_bow.wav`), zbroja `equip_metal_armor.wav`,
naszyjnik/kolczyki/bransoleta `equip_ring_amulet.wav`, reszta `pick.wav` – najwyżej jeden
dźwięk na 0,15 s (Z podnosi wiele naraz). Wszystkie dźwięki są w kliencie (`sound/ui/`).

Boty nie dostają tej linii (sprawdzane `GetDesc()->IsBot()`), a przedmiot podniesiony przez
członka grupy dla kogoś innego nie daje dźwięku nikomu. Bez nowego pakietu: stary klient nie zna
komendy `PickupSound` i ją pomija.

## Zmiany silnika (`edits.json`, `char_item.cpp`)

| Znacznik | Co robi |
|---|---|
| `MT2009_PLUS_DIGI_CLIENT_QOL_V1 (pickup sound)` | przed `ChatPacketRecieveItem`: licznik „trwa podnoszenie”, `Mt2009DigiPickupSound` (tylko gracz z prawdziwym połączeniem); `ChatPacketRecieveItem` wysyła `PickupSound <vnum>`, gdy jest wołane z `PickupItem` |
| `MT2009_PLUS_DIGI_CLIENT_QOL_V1 (pickup scope)` | `CHARACTER::PickupItem`: zakres podnoszenia (przedmiot ze stosu, na wolne pole, z podziału w grupie dla siebie) |
| `MT2009_PLUS_DIGI_CLIENT_QOL_V1 (pickup yang)` | `PickupItem`: po `GiveGold` – `PickupSound 1` |

`AutoGiveItem` (nagrody z questów, kupno) też woła `ChatPacketRecieveItem`, ale poza
podnoszeniem dźwięku nie ma.

- `Apply-DigiRastaClientPatch.ps1` – Windows (`tools/port/Apply-MT2009PlusEngine.ps1`, zaraz po
  `server-patches/digirasta`);
- `apply_digirasta_client.py <game/src>` – Linux/VPS; oba czytają ten sam `edits.json`.

Zmiana już nałożona (jest jej znacznik) jest pomijana; zmiana, której kodu nie ma dokładnie raz,
przerywa całość, zanim cokolwiek zostanie zapisane.

## Reszta (klient)

Okno „Opcje dodatkowe”, porównanie pod ALT, licznik Yang, tani towar w sklepie NPC i odbiór
`PickupSound`: `client-patches/client-2.0.30/root/` (`digiqol.py`, `uiopcjedodatkowe.py`); funkcje
exe i opis całości: `client-patches/exe-digi-client-qol/README.md` (exe: `client-patches/exe`, `ENABLE_DIGI_CLIENT_QOL`).
