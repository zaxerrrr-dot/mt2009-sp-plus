# Wygody klienta Digi Rasty – `MT2009_PLUS_DIGI_CLIENT_QOL_V1`

**Autor: Digi Rasta** (paczka „nowy-system” v0.23.0, wpis 0.19.0 „Biore: małe systemy klienta”).
Przeniesione do MT2009 PLUS jako nasz kod: moduły w paczce `root` (bez jego osobnej paczki
`nowy_system` i bez `constInfo.NowySystemImport`), funkcje exe jako łatka do źródła exe.

## Co jest w grze

| Co | Gdzie | Exe |
|---|---|---|
| Okno **„Opcje dodatkowe”** (przycisk w menu pod ESC, nad „Wyjście”): ukryj efekty wzmocnień szamana, ukryj aury umiejętności (BL_HIDE_EFFECT), ukryj sklepy graczy (Hide-Objects), ukryj drzewa / budynki i obiekty / chmury / wodę (Graphic-Mask-Control), zapis czatu i szeptów do `logs/czat_RRRR-MM-DD.txt` (Chat-Log-Viewer). Ustawienia w `opcje_dodatkowe.cfg` (klucz=0/1), stosowane co sekundę (nowa mapa, przejście, nowe sklepy). | `uiopcjedodatkowe.py`, `uisystem.py`, `uiscript/systemdialog.py`, `game.py` (`Apply()` w `OnUpdate`) | efekty, sklepy, czat – nowe exe; drzewa/obiekty/chmury/woda – każde exe (`background.SetVisiblePart`). Wiersz, którego exe nie umie, jest ukryty. |
| **Porównanie pod ALT** (Compare-Item-Tooltip): przy opisie broni/zbroi trzymany ALT pokazuje obok opis założonego przedmiotu z dopiskiem „[ Założony ]” | `uitooltip.py` (`ItemToolTip`: `OnUpdate`, `HideToolTip`, pole źródła w `SetInventoryItem`), `digiqol.py` | każde |
| **Licznik Yang** (Refresh-Money-With-Sleep) dochodzi do nowej kwoty w ~0,4 s | `uiinventory.py` (`RefreshGold`), `digiqol.py` | każde |
| **Sklep NPC**: towar tańszy niż 500 Yang podświetlony (Shop-Low-Price-Icon – podświetlenie pola zamiast ikony z C++) | `uishop.py` (`Refresh`) | każde |
| **Dźwięk podnoszenia** (Pick-Up-Sound-Effect): `PickupSound <vnum>` od serwera, dźwięk według rodzaju, najwyżej raz na 0,15 s | `game.py` (komenda), `digiqol.py`; serwer: `server-patches/digirasta-client` | każde |

Grafiki: pole wyboru z paczki (jego `ui/game/refine/checkbox.tga` / `checked.tga`) jako
`mt2009_ui/checkbox/checkbox.tga` i `checked.tga` w paczce `root` – `d:/ymir work/ui/game/quest/quest_check*.tga`
nie ma w paczkach graczy (2.0.46: „Failed to load image”, okno się nie otwierało); gdy obrazka brak,
okno pokazuje `[x]` / `[ ]`. Dźwięki z `sound/ui/` klienta (`money.wav`, `equip_metal_weapon.wav`,
`equip_bow.wav`, `equip_metal_armor.wav`, `equip_ring_amulet.wav`, `pick.wav` – zamiast `itemget.wav`
z paczki, którego nasz klient nie używa).

Nowe pliki `root`: `digiqol.py`, `uiopcjedodatkowe.py`; zmienione: `game.py`, `uiinventory.py`,
`uitooltip.py`, oraz (do tej pory nie w repozytorium, wzięte z paczki `root` 2.0.43) `uishop.py`,
`uisystem.py`, `uiscript/systemdialog.py`.

## Exe

Od 7.10.2026 w nakładce exe (`client-patches/exe`, `ENABLE_DIGI_CLIENT_QOL`, `UserInterface/Mt2009ClientQol.cpp`,
`EffectLib/EffectInstance.cpp`, `PythonIkarusShop.cpp`, `PythonChat.cpp`, `UserInterface.cpp`) – opis w
`client-patches/exe/README.md`, „Wybór z nowy-system 0.28”. Dawna łatka `digi-client-qol.patch` (nigdy nie nakładana
przez `build.sh`) usunięta.

Paczka ukrywała tylko postacie-sklepy (`IsShop()`); u nas sklepy to encje ikashop, więc
`SetShopsVisible` robi oba.
