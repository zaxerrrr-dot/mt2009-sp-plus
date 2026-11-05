# language – gra w języku gracza (rdzeń serwera)

`MT2009_PLUS_LANGUAGE_V1` (właściciel, 5.11.2026: tłumaczenie całej gry; brief `cache/yohara/tlumaczenia-brief.md`).
Każdy gracz czyta teksty serwera w języku, który wybrał w kliencie. Polski jest źródłem i domyślnym językiem.

**Nakładana po `remotecall`** (kotwica w `questlua.cpp` to linia Enasira). Linux/VPS: `python3 apply_language.py <game/src>`;
Windows: `Apply-LanguagePatch.ps1` (`tools/port/Apply-MT2009PlusEngine.ps1`, na końcu). Edycja już nałożona jest
pomijana; edycja, której stary kod nie występuje dokładnie raz, zatrzymuje całość, zanim cokolwiek zostanie zapisane.
`gen_edits.py [<game/src>]` pisze `edits.json` (i sprawdza kotwice).

## Jak działa

| | |
|---|---|
| Język gracza | klient wysyła `/lang <kod>` po wejściu do gry i przy każdej zmianie – tylko język wybrany przez użytkownika (kody Owsapa: `pl en de tr ro es it fr pt cz hu gr ae`; aliasy `cs→cz`, `el→gr`, `ar→ae`). Zapis w `player.player.language` (VARCHAR(4) NULL, migracja `language.sql` w `apply.sh`), odczyt przy wejściu postaci na rdzeń (`Entergame`, przed questami logowania). `/lang` bez argumentu: bieżący język, domyślny serwera i dostępne; `/lang default` – z powrotem domyślny serwera (NULL); `/lang reload` (GM_IMPLEMENTOR) – słowniki od nowa. |
| Domyślny język serwera | `MT2009_PLUS_LANGUAGE_DEFAULT_V1` (właściciel, 5.11.2026): `M2_DEFAULT_LANGUAGE` w `.env` (launcher, `vps-install.sh --language`, panel zaawansowany; domyślnie `pl`). `NULL` w `player.language` = gracz nic nie wybrał → język domyślny (także bot; „nikt”/potwór – `pl`). Wybór gracza (także `pl`) zostaje po zmianie domyślnego. Pierwsza wersja kolumny miała `NOT NULL DEFAULT 'pl'` – `language.sql` raz (póki kolumna jest NOT NULL) robi ją nullable i zamienia każde `'pl'` na `NULL` (nie da się odróżnić „wybrał polski” od „nic nie wybrał”; klient z własnym wyborem wysyła go ponownie przy wejściu). Przy wejściu serwer wysyła klientowi `MT2009LANG <domyślny> <własny\|->` (komenda czatu): klient bez wyboru użytkownika przyjmuje go na swoje teksty od następnego uruchomienia (`mt2009lang.OnServerLanguage`, `mt2009_language.cfg` obok `game1.cfg`: `user <kod>` / `server <kod>`). Boty: krzyk, handel i czat gildii bez graczy w języku domyślnym (`playerbot_i18n.h`), szept – w języku czytelnika. Panele i ItemShop: `?lang` → ciasteczko `m2lang` → (sklep: język gracza z gry) → `M2_DEFAULT_LANGUAGE` → przeglądarka tylko bez ustawienia. |
| Słowniki | `share/locale/poland/lang/<kod>/*.tsv` (w repo `linux-port/docker/game/lang/`): `polski<TAB>tłumaczenie`, UTF-8 (`\t \n \\`), czytane przy pierwszym czytelniku języka i konwertowane na stronę kodową klienta (`language.cfg`: `codepage 1252`, `fallback en`; domyślnie jak GF: 1250 pl/cz/hu/ro, 1253 gr, 1254 tr, 1256 ae, reszta 1252). Pliki w kolejności nazw, późniejszy wygrywa (`zz_*.tsv` – ręczne poprawki). `item_names.tsv` / `mob_names.tsv`: `vnum<TAB>nazwa`. `*fragment*.tsv`: kawałki sklejanych tekstów. `*quest_info*.tsv` (`45_quest_info.tsv`): krótkie formy tylko dla okna misji (tytuł maks. 30 bajtów, nazwa zegara / licznika 16 – pakiet klienta). **Nowy język = nowy folder.** |
| Szukanie | dokładny tekst → format (`"Masz %d sztuk"` znajduje `"Masz 5 sztuk"` i wstawia wartości w tłumaczenie; wartość `%s`, która sama jest tekstem słownika, nazwą przedmiotu / potwora z protów albo sklejoną linią z własnym formatem, też jest tłumaczona) → to samo po angielsku (fallback) → fragmenty sklejeń → tekst bez zmian. Sklejenia questów (`"Za "..n.." sekund ..."`) `extract_server_texts.py` zamienia na formaty (`Za %s sekund ...`, `32_quest_templates.tsv`) – questy zostają bez zmian. Linie GF z `[ENTER]` także linia po linii (`notice_multiline`, `say_split`). Tłumaczenie formatu o innych konwersjach niż polski nigdy nie trafia do `vsnprintf`. |
| Czat | `CHARACTER::ChatPacket`: dla INFO / NOTICE / BIG_NOTICE / TALKING / DICE / FANCY_NOTICE / misji Zodiaku – tłumaczony format (LC_TEXT i nasze polskie formaty), a bez niego cała gotowa linia. Ogłoszenia (`notice_all`, `BroadcastNotice`, `d.notice`, P2P) docierają do każdego w jego języku, bo tłumaczy odbiorca. Nigdy COMMAND, czat graczy, szepty, gildia, drużyna. |
| Questy | `quest/mt2009_language.lua` (ładowany po `locale.lua`, ASCII): `say`, `say_title`, `say_reward`, `say_split`, `say_item`, `select` (też menu NPC), `select_table`, `makequestbutton` oddają tekst do `mt2009_tr()`; `item_name` / `get_item_name` / `mob_name` – nazwa w języku czytelnika. Questy liczą i porównują dalej po polsku; **qc i kompilacja questów bez zmian**. |
| Okno misji | `MT2009_PLUS_LANGUAGE_QUESTINFO_V1` (5.11.2026: angielski klient pokazywał tytuły i liczniki po polsku w cp1252 – „Zaklêtym”, „Pozosta³a iloœæ”). `q.set_title` / `send_letter` / `set_clock_name` / `set_counter_name` zostają w stanie questa **po polsku**; `PC::SendQuestInfoPakcet` tłumaczy przy wysyłce dla czytelnika (`Mt2009QuestInfoText`: krótka forma `*quest_info*.tsv` → słownik → bez spacji na końcu → transliteracja), przycina do pola na granicy słowa (`[ENTER]` → spacja) i wypełnia zerami. Zmiana języka (`/lang` przychodzi po questach logowania) wysyła tytuły / zegary / liczniki wszystkich listów jeszcze raz (`Mt2009ResendQuestInfo`). |
| Strona kodowa | Siatka bezpieczeństwa (`DESC::Packet`, `Mt2009LanguagePacketOut`): czat (bez `COMMAND`), szept, skrypt questa (`say`), pytanie `QUEST_CONFIRM` – czytelnik, którego klient nie ma cp1250 (en/de/es/it/fr/pt 1252, tr 1254, gr 1253, ae 1256), dostaje polskie słowa bez ogonków (ą→a, ł→l, ż→z …) zamiast bajtów cp1250. Linia jest polska, gdy któreś jej słowo ma polską literę spoza alfabetu czytelnika; zmieniane są tylko słowa z liter ASCII i polskich – przetłumaczone (francuskie ê, hiszpańskie ñ, niemieckie umlauty, greka / arabski bez liter ASCII) zostają. cz/hu/ro (cp1250) i pl – bez zmian. |
| Lua | `pc.get_language()`, `pc.set_language(kod)`, `mt2009_tr(tekst[, kod])`, `mt2009_item_name(vnum[, kod])`, `mt2009_mob_name(vnum[, kod])`, `mt2009_languages()` |
| C++ | `mt2009_language.h`: `GetPlayerLanguage(ch)`, `SetPlayerLanguage(ch, kod)`, `Mt2009Translate(kod, polski)`, `Mt2009TranslateFor(ch, polski)`, `LC_TEXT_FOR(ch, klucz)`, `Mt2009ItemNameIn`, `Mt2009MobNameIn` (boty: `GetPlayerLanguage(target)`) |

## Silnik (`edits.json`, 12 edycji) i nakładka

| Plik | Co |
|---|---|
| `char.cpp` | `#include "mt2009_language.h"`; `ChatPacket` – format / linia w języku czytelnika (długość obcięta do bufora) |
| `input_login.cpp` | `Entergame` – `player.language` przed questami logowania |
| `questlua.cpp` | funkcje Lua; `quest/mt2009_language.lua` po `locale.lua` (brak / błąd – questy po polsku, nie blokuje startu) |
| `cmd.cpp` | `/lang` (GM_PLAYER, POS_DEAD) |
| `questpc.cpp` | `SendQuestInfoPakcet` – tytuł, nazwa zegara i licznika w języku czytelnika (`QUESTINFO_V1`) |
| `desc.cpp` | `DESC::Packet` – pakiety tekstowe bez polskich ogonków dla klienta bez cp1250 (`QUESTINFO_V1 (packet)`) |

Nakładka: `linux-port/overlays/playerbot/src/game/src/mt2009_language.{h,cpp}`.

## Dane (`tools/i18n/`)

* `build_server_lang.py` – generuje `10_quest_stock.tsv` (questy paczki: `gameforge.*`, `translate.*`, `locale.*`),
  `20_server_locale.tsv` (LC_TEXT), `item_names.tsv`, `mob_names.tsv`, `language.cfg`. Źródła: oficjalne teksty GF z
  klienta Owsapa (`locale_quest.txt` / `locale_string.txt` po id, dopasowane po polskim tekście albo po angielskim),
  angielski i turecki z wydania bazowego (podpis polskiego sprawdzany), niemiecki pakietu Vegas (tylko dane), nazwy z Dump Proto
  Owsapa (tylko gdy oficjalna polska nazwa vnuma = nasza). Tylko z tymi samymi konwersjami printf; nigdy z
  „Metin2/Gameforge”.
* `extract_server_texts.py` – nasze teksty: `data/quest_custom_pl.tsv` (questy i biblioteki), `data/quest_templates_pl.tsv`
  (sklejenia jako formaty), `data/quest_fragments_pl.tsv` (kawałki sklejeń), `data/server_custom_pl.tsv` (C++ nakładki
  i łatek); `--check <kod>` – czego brakuje w `30_quest_custom.tsv` / `32_quest_templates.tsv` / `35_quest_fragments.tsv` /
  `40_server_custom.tsv`. Ręczne: także `22_server_locale_more.tsv` (LC_TEXT, których nie ma w oficjalnych źródłach).
* `lua50/` – interpreter Lua 5.0 silnika (zrzuty tabel, test składni).

## Wdrożenie

1. `language.sql` (apply.sh przy starcie migratora – samo).
2. `apply_language.py` po `remotecall` (i po `runyboty`, kolejność bez znaczenia) – lista łatek w `yohara-deploy.sh`.
3. Obraz gry: `COPY quest/mt2009_language.lua` i `COPY lang/` (game/Dockerfile).

Bez klienta z `/lang` wszyscy grają w języku domyślnym serwera (`M2_DEFAULT_LANGUAGE`, bez ustawienia `pl`).
