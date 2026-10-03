# Wygody Digi Rasty (3 października) – serwer i jego część w kliencie

**Autor: Digi Rasta** (paczka „nowy-system” v0.23.0, systemy z jego listy „Biore”: `nowy_system.cpp`,
`nowy_system_biore.h`, haki `zastosuj.py`, poprawki `klient.py`, moduły `uikillbar.py`, `uiksiegi.py`,
quest `ksiegi_seonhae`). Przeniesione do MT2009 PLUS jako nasz kod – bez skryptu haków: zmiany silnika są
tutaj (`edits.json`), kod w nakładce botów (`playerbot_digi_qol.h`), klient w zwykłych plikach roota.
Znacznik: `MT2009_PLUS_DIGI_SERVER_QOL_V1`.

## Co robi

| System | Jak |
|---|---|
| Powód nieudanego ulepszenia | po „RefineFailed” serwer dosyła `RefineFailedType <0 obniżony / 1 zniszczony albo jedna sztuka ze stosu / 2 bez zmian>`, okienko pokazuje właściwy tekst |
| Blokada z komunikatora | lista zablokowanych zatrzymuje też handel, zaproszenie do grupy i do gildii, emocje we dwoje i pojedynek – w obie strony (ja zablokowałem / on mnie); GM nie jest zatrzymywany cudzą blokadą (jak przy szeptach) |
| Awans | gratulacje na czacie przy każdym poziomie, co 10 poziomów ogłoszenie dla wszystkich „[Awans] X zdobywa N. poziom!” (kilka poziomów naraz – ogłoszona ostatnia przekroczona dziesiątka); **boty pominięte** |
| Prezent dzienny | przy wejściu raz na 24 h od 10. poziomu: Yang = poziom × 500 i po 20 Czerwonych + Niebieskich Mikstur (D) (27003, 27006); tylko gracze; flaga `digi_qol.daily_gift` czytana dopiero po wczytaniu flag questów (krótkie zdarzenie czeka do 30 s), więc wolne wczytanie nie da drugiego prezentu |
| Pasek zabójstw | zabicie postaci przez postać: `KillBar <rasa> <broń> <rasa ofiary> <zabójca> <ofiara>` do graczy na tej mapie (prawy górny róg, `uikillbar.py`) |
| Seria zabójstw | zabicie postaci albo bossa przez gracza: `KillSound <1..13>`; seria rośnie, gdy kolejne zabicie przyjdzie w 10 s |
| Umiejętności gotowe po śmierci | serwer zeruje odnowienia gracza i wysyła `SkillCoolTimeReset`; boty zostają przy swoich |
| Okno śmierci z odliczaniem | `DeadTime <tu> <miasto>` (10 i 7 s jak w `do_restart`, limit portalu po walce), przyciski pokazują sekundy i są nieaktywne do zera |
| Wymiana ksiąg u Seon-Hae | quest `ksiegi_seonhae` (20095, „Wymiana ksiąg umiejętności”) otwiera okno; `/nowy_ksiegi <10 pól>`: 10 dowolnych ksiąg + 1 000 000 Yang = losowa księga „Instr.” (50400 + umiejętność) własnej klasy i drogi, tylko te, które są w naszym `item_proto` (Wojownik ma po 5 na drogę, reszta po 6); serwer sprawdza wszystko od nowa (NPC po vid z questa, ta sama mapa, 25 m, rozmowa w ostatnich 10 min, żadnych innych okien, 10 różnych pól z księgami, nie zablokowane, Yang); z każdego pola jedna sztuka; Yang przez `PlayerBotChangeGold` (mt2009 odrzuca `PointChange(POINT_GOLD)`) |

## Decyzja: pasek zabójstw a boty

Boty królestw walczą ze sobą cały dzień (2000 botów) – pasek pokazuje **tylko zabójstwa z prawdziwym graczem
po jednej ze stron** (zabójca albo ofiara), wysyłane tylko do prawdziwych graczy na tej mapie. Bot kontra bot
nie idzie nigdzie. Seria zabójstw liczy się tylko prawdziwemu graczowi. Bez dodatkowego limitu – pasek ma
5 wierszy po 6 s.

## Zmiany silnika (`edits.json`)

| Znacznik `MT2009_PLUS_DIGI_SERVER_QOL_V1 (…)` | Plik | Wywołuje |
|---|---|---|
| `(refine note)` | `char_item.cpp` (`NotifyRefineFail`) | `Mt2009DigiRefineFailNoted` |
| `(refine report)` | `input_main.cpp` (`CInputMain::Refine`) | `Mt2009DigiRefineFailReport` |
| `(trade block)` | `exchange.cpp` | `Mt2009DigiBlocked` |
| `(party block)` | `char.cpp` (`PartyInvite`) | `Mt2009DigiBlocked` |
| `(guild block)` | `guild.cpp` (`CGuild::Invite`) | `Mt2009DigiBlocked` |
| `(duel block)` | `cmd_general.cpp` (`do_pvp`) | `Mt2009DigiBlocked` |
| `(emote block)` | `cmd_emotion.cpp` | `Mt2009DigiBlocked` |
| `(level up)` | `char.cpp` (`POINT_LEVEL`) | `Mt2009DigiLevelUp` |
| `(daily gift)` | `input_login.cpp` (`EnterGame`) | `Mt2009DigiDailyGift` |
| `(skills ready)` | `char_battle.cpp` (`Dead`) | zeruje `m_SkillUseInfo[*].dwNextSkillUsableTime` |
| `(kill sound)` | `char_battle.cpp` (`Dead`) | `Mt2009DigiKillSound` |
| `(kill bar)` | `char_battle.cpp` (`Dead`) | `Mt2009DigiKillBar` |
| `(dead time)` | `char_battle.cpp` (`Dead`) | `Mt2009DigiDeadTime` |
| `(declare)`, `(table)` | `cmd.cpp` | `/nowy_ksiegi` (za Seon-Hae, na jego liniach) |

Funkcje są w nakładce botów, `linux-port/overlays/playerbot/src/game/src/playerbot_digi_qol.h`
(dołączonej w `playerbot_manager.cpp`), deklarowane w miejscu wywołania.

- `Apply-DigiRastaQolPatch.ps1` – Windows (`tools/port/Apply-MT2009PlusEngine.ps1`, ostatni krok przed skrzydłami);
- `apply_digirasta_qol.py <game/src>` – Linux/VPS; oba czytają ten sam `edits.json`.

Zmiana już nałożona (jest jej znacznik) jest pomijana; zmiana, której kodu nie ma dokładnie raz, przerywa
całość, zanim cokolwiek zostanie zapisane. `exchange.cpp`, `guild.cpp` i `cmd_emotion.cpp` mają mieszane
końce linii (CRLF i LF) – zmiana jest szukana jak w pliku (najpierw LF, potem CRLF) i reszta pliku zostaje
bajt w bajt.

Quest: `linux-port/docker/game/quest/ksiegi_seonhae.quest` (lista questów w `Dockerfile`).
`cmd_emotion.cpp` dopisany do `launcher/server-update-files.mod.txt`, znaczniki do `$engineMarks`
w `tools/New-M2UpdatePackage.ps1`.

## Klient (`client-patches/client-2.0.30/root`)

| Plik | Co |
|---|---|
| `digiserverqol.py` (nowy) | komendy serwera: `RefineFailedType`, `KillBar`, `KillSound`, `SkillCoolTimeReset`, `DeadTime`, `NOWY_KSIEGI` – wpisywane prosto do `serverCommander` okna gry |
| `uikillbar.py` (nowy) | pasek zabójstw |
| `uiskillbookexchange.py` (nowy) | okno wymiany ksiąg |
| `game.py` | 2 linie: `digiserverqol.Register(self)` po komendach i `digiserverqol.DestroyWindows()` przy zamknięciu okna gry |
| `uichat.py` (nowy w repo, z paczki) | „@nick tekst” w zwykłym czacie = szept (jak z okna szeptu); czat handlowy zostaje: w trybie handlu (TAB) i dla „@ tekst” linia idzie na czat handlowy jak dotąd |
| `uirestart.py` (nowy w repo, z paczki) | odliczanie na przyciskach okna śmierci |
| `uichestpreview.py` | „Otwórz” / „Otwórz 10” w podglądzie skrzynki: jedna co 0,25 s (`net.SendItemUsePacket`), stop: drugie kliknięcie, brak skrzynek w polu, serwer nie otworzył (liczba w polu bez zmian), zamknięcie okna / inna skrzynka; tylko w fazie gry (`warpsafe.InGame()`) |
| `mt2009_ui/killbar/*.png` (16) | ikony ras i broni z jego paczki (`d:/ymir work/ui/nowy_system/kill_bar/`) |
| `mt2009_ui/killstreak/1..13.wav` | dźwięki serii z jego paczki (`d:/ymir work/nowy_system/kill_effect/`), razem 5,3 MB |

Reset odnowień w kliencie wymaga exe z `player.ResetSkillCoolTimes()` (łatka exe `server-patches/digirasta-qol/digi-server-qol-exe.patch`,
`ENABLE_SKILL_COOLTIME_RESET`); na exe bez niej serwer i tak zeruje odnowienia, a klient odlicza swoje jak
dotąd (skrypt sprawdza `hasattr`). Czysto skryptowej drogi nie ma: czasy odnowień (`fLastUsedTime`,
`fCoolTime`) zmienia tylko użycie umiejętności, a `player.ToggleCoolTime()` to przełącznik GM, który wyłącza
sprawdzanie wszystkich odnowień naraz.
