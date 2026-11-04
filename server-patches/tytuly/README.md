# tytuly – Tytuły postaci

`MT2009_PLUS_TITLES_V1` (właściciel, 4.11.2026: „dodaj”). Na podstawie paczki właściciela „Official Title System Renewal”
– przepisanej, nie skopiowanej: ten sam pomysł (gracz zdobywa tytuły na stałe albo na czas, zakłada jeden z nich, a każdy
w pobliżu widzi go przy jego imieniu – tabliczka z nazwą, animowany baner albo efekt nad głową; okno tytułów z podglądem;
certyfikaty 57000–57002), inne wnętrze tam, gdzie paczka nie pasowała do naszego silnika albo miała błędy.

**Nakładana jako OSTATNIA** z listy łatek (po `skillcolor`; kotwice: linie pakietów, logowania, `EncodeInsertPacket` i
`Destroy` koloru umiejętności). Linux/VPS: `python3 apply_tytuly.py <game/src>`; Windows: `Apply-TytulyPatch.ps1`
(`tools/port/Apply-MT2009PlusEngine.ps1`, na końcu). Edycja już nałożona jest pomijana; edycja, której stary kod nie
występuje dokładnie raz, zatrzymuje całość, zanim cokolwiek zostanie zapisane. `gen_edits.py [<game/src>]` pisze
`edits.json` (i sprawdza kotwice).

## Co robi

- **Katalog** jest w nakładce (`playerbot_titles.cpp`, `TITLES`): numer, wygląd (tabliczka z nazwą / efekt nad głową),
  polska nazwa i sposób zdobycia, na stałe albo domyślny czas, zasób klienta
  (`d:/ymir work/ui/game/title/titles/title_<zasób>.sub`) i plik efektu. Serwer wysyła go klientowi (pakiet TABLE) –
  nowy tytuł to linia tutaj i ewentualnie obrazki w kliencie, bez zmian w danych klienta.
- **Wygląd**: tabliczka (lewa/środek/prawa część + nazwa w kolorze tytułu; 1005, 1006, 1011 dodatkowo z animowanym
  banerem nad nią) albo efekt nad głową (bez nazwy) – jak w paczce.
- **Posiadanie**: `player.player_title` (wiersz na tytuł: `pid`, `title_index`, `end_time` – 0 = na stałe, `equipped`).
  Czytane przy logowaniu, pisane przy zmianie; tytuł, któremu minął czas, znika (wiersz, lista, założony) – sprawdzane co
  60 s, godzinę przed końcem gracz dostaje komunikat.
- **Zakładanie**: okno tytułów (portret w oknie postaci), 1 zmiana na sekundę (jak w paczce).
- **Kto co nosi**: `GC VISUAL` (VID, tytuł) do każdego widza, którego klient się przywitał – po jego pakietach dodania
  postaci (`EncodeInsertPacket`) i przy zmianie.

### Lista tytułów (nazwy z polskich plików paczki; źródła – do decyzji właściciela)

| Nr | Nazwa | Wygląd | Czas | Jak zdobyć teraz |
|---|---|---|---|---|
| 1000 | Szczęściarz | niebieska tabliczka | na stałe | Niebieski Certyfikat Tytułu 57001, GM, quest |
| 1002 | Heroiczny | złota tabliczka | 30 dni (kolejny certyfikat dokłada 30) | Czerwony Certyfikat Tytułu 57000, GM, quest |
| 1003 | Legendarny | złota tabliczka | 30 dni | GM, quest |
| 1004 | Mistyczny | złota tabliczka | 30 dni | GM, quest |
| 1005 | Czciciel Słońca | złoty baner (animowany) | na stałe | Zielony Certyfikat Tytułu 57002, GM, quest |
| 1006 | Gwiazda Polarna | niebieski baner (animowany) | na stałe | GM, quest |
| 1011 | Wielki Mistrz Okey | czerwony baner (animowany) | na stałe | GM, quest |
| 1012 | Łowca Monet | czerwona tabliczka | na stałe | GM, quest |
| 1 | Ostatni Ocalały | korona nad głową | 3 h | GM, quest |
| 2 | Niepokonany | puchar nad głową | 7 dni | GM, quest |
| 3 | Zwiastun Wojny | medal nad głową | 7 dni | GM, quest |
| 4 | Rzeźnik | pięść nad głową | 7 dni | GM, quest |
| 6 | Płomienny Pogromca | czerwony smok | 7 dni | GM, quest |
| 7 | Bezlitosny Sędzia | biało-zielony smok | 7 dni | GM, quest |

Zasady, kiedy dawać te tytuły (np. automatycznie dla 1.–3. miejsca rankingu zabójców), są do decyzji właściciela.
Opisy warunków w oknie (kolumna „warunek” katalogu) mówią, do czego tytuł jest pomyślany (ranking zabójców, Schronienie
Meley, Krypta Balathora, Okey, eventy) – samo przyznawanie z tych źródeł nie jest podłączone (decyzja właściciela).
Wypadły tytuły serwera oficjalnego bez odpowiednika u nas (członkostwo premium, transfery z innych serwerów).

## Silnik (`edits.json`, 12 edycji) i nakładka

| Plik | Miejsce | Co |
|---|---|---|
| `packet.h` | nagłówki | `HEADER_CG_TITLE = 185`, `HEADER_GC_TITLE = 189` (numery paczki) – wolne u nas i w exe (sprawdzone: wszystkie CG/GC naszego `packet.h`, `npc_location_helper.h`, `input_udp.cpp`, `Packet.h` exe i gałęzi y-lowienie / y-mikstury2 / y-grupy) i poza zakresami zarezerwowanymi dla zwierzaków (CG 122–133, GC 200–215) |
| `packet.h` | struktury | `TPacketCGTitle` (6 B), `TPacketGCTitle` (6 B, dynamiczny), wiersze `TPacketGCTitleRow` (309 B), `TPacketGCTitleOwned` (8 B), `TPacketGCTitleNotify` (5 B), `TPacketGCTitleVisual` (8 B), `static_assert` (exe to samo) |
| `packet_info.cpp` | rozmiary | CG 185, stały, z bajtem sekwencji |
| `input_main.cpp` | pakiety | `TitleSystemPacket` (powitanie/odświeżenie, załóż, zdejmij) |
| `input_login.cpp` | po kolorze umiejętności | wiersze postaci z bazy, założony tytuł do wszystkich wokół (`TitleSystemOnLogin`) |
| `char.cpp` | `EncodeInsertPacket`, `Destroy` | założony tytuł temu, kto widzi postać; stan VID-u znika |
| `char_item.cpp` | `UseItemEx` | certyfikaty 57000–57002 przed limitami i typem przedmiotu (`TitleSystemUseItem`) |
| `cmd.cpp` | polecenia | `/tytul` i nazwa paczki `/title_system` (GM_LOW_WIZARD, jak w paczce) |
| `questlua.cpp` | moduły questów | `title.give(nr [, sekundy])`, `title.has(nr)`, `title.remove(nr)`, `title.equipped()` |

Nakładka: `linux-port/overlays/playerbot/src/game/src/playerbot_titles.cpp` (cała logika).

GM: `/tytul lista`, `/tytul <nr|nazwa>` (sobie), `/tytul daj <gracz> <nr> [dni]`, `/tytul zabierz <gracz> <nr>`,
`/tytul pokaz <gracz>` (gracz na tym samym kanale).

**Różnice względem paczki** (świadome):
- Klient **wita się** (CG 185 OPEN po wejściu do gry) i tylko taki klient dostaje GC 189 – starszy exe nigdy nie zobaczy
  nieznanego pakietu (bez podnoszenia wersji klienta), boty nie kosztują nic (nie mają wiersza ani zapytania).
- Kto nosi który tytuł – własny podpakiet `VISUAL` tylko do widzów, nie `SpecificEffectPacket` z „ścieżka|numer” do
  wszystkich wokół przy każdym pojawieniu się postaci.
- Posiadanie i założony tytuł tylko w `player.player_title` (paczka: tabela + flagi questów `title_system.*`); tytuł „na
  stałe” jest na stałe (paczka: 365 dni).
- Certyfikat = jeden tytuł (value0) i jego czas (value1, 0 = domyślny); certyfikat tytułu czasowego, który gracz już ma,
  przedłuża go (paczka: odmawiała). Bez nowego podtypu `USE_TITLE` – `ITEM_QUEST` jak pudła puzzli, więc bez zmian w
  `item_length.h`, `ProtoReader.cpp`, DumpProto i `ItemData.h` exe.
- Bez wpisu do syserr przy każdym otwarciu okna (paczka zostawiła `TITLE_SYSTEM DEBUG`).

## Baza

`linux-port/docker/mariadb/playerbot/tytuly.sql` (w `apply.sh` po puzzlach rybackich): `player.player_title` (`CREATE
TABLE IF NOT EXISTS`, `ADD COLUMN IF NOT EXISTS equipped`) i certyfikaty 57000–57002 w `world.item_proto` (`INSERT
IGNORE`, ITEM_QUEST, 1 w slocie, antyflagi paczki: bez wyrzucania, dawania, upuszczenia przy PK, łączenia i sklepu
prywatnego = 123008). Sprawdzone na jednorazowym MariaDB 11.8 (dwa przebiegi).

## Klient

- Exe (`client-patches/exe`, `ENABLE_MT2009_TITLES`, `Mt2009Titles.cpp`) – README exe.
- Root: `uicharactertitle.py` (okno: lista tytułów z katalogu serwera – kłódka / klepsydra / nieskończoność, założony
  tytuł, „Załóż” / „Zdejmij”, podgląd tabliczki z banerem albo efektu, opis zdobycia i czas; komunikaty na czacie także
  przy zamkniętym oknie), `uiscript/charactertitlewindow.py` (układ paczki), portret w oknie postaci otwiera okno
  (`uicharacter.py`, przycisk GF nad ramką twarzy), „Ukryj tytuły innych graczy” w Opcjach dodatkowych
  (`uiopcjedodatkowe.py`). Bez exe z `titleSystem` nic z tego się nie pokazuje.
- Dane: paczka `tytuly` + certyfikaty w `gamedata`/`dbdata` (`client-2.0.30/tools/tytuly`).
