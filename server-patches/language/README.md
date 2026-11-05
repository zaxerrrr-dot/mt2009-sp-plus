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
| Język gracza | klient wysyła `/lang <kod>` po wejściu do gry i przy każdej zmianie (kody Owsapa: `pl en de tr ro es it fr pt cz hu gr ae`; aliasy `cs→cz`, `el→gr`, `ar→ae`). Zapis w `player.player.language` (VARCHAR(4), domyślnie `'pl'`, migracja `language.sql` w `apply.sh`), odczyt przy wejściu postaci na rdzeń (`Entergame`, przed questami logowania). Bot, postać bez klienta, „nikt” – `pl`. `/lang` bez argumentu: bieżący język i dostępne; `/lang reload` (GM_IMPLEMENTOR) – słowniki od nowa. |
| Słowniki | `share/locale/poland/lang/<kod>/*.tsv` (w repo `linux-port/docker/game/lang/`): `polski<TAB>tłumaczenie`, UTF-8 (`\t \n \\`), czytane przy pierwszym czytelniku języka i konwertowane na stronę kodową klienta (`language.cfg`: `codepage 1252`, `fallback en`; domyślnie jak GF: 1250 pl/cz/hu/ro, 1253 gr, 1254 tr, 1256 ae, reszta 1252). Pliki w kolejności nazw, późniejszy wygrywa (`zz_*.tsv` – ręczne poprawki). `item_names.tsv` / `mob_names.tsv`: `vnum<TAB>nazwa`. `*fragment*.tsv`: kawałki sklejanych tekstów. **Nowy język = nowy folder.** |
| Szukanie | dokładny tekst → format (`"Masz %d sztuk"` znajduje `"Masz 5 sztuk"` i wstawia wartości w tłumaczenie; wartość `%s`, która sama jest tekstem słownika, nazwą przedmiotu / potwora z protów albo sklejoną linią z własnym formatem, też jest tłumaczona) → to samo po angielsku (fallback) → fragmenty sklejeń → tekst bez zmian. Sklejenia questów (`"Za "..n.." sekund ..."`) `extract_server_texts.py` zamienia na formaty (`Za %s sekund ...`, `32_quest_templates.tsv`) – questy zostają bez zmian. Linie GF z `[ENTER]` także linia po linii (`notice_multiline`, `say_split`). Tłumaczenie formatu o innych konwersjach niż polski nigdy nie trafia do `vsnprintf`. |
| Czat | `CHARACTER::ChatPacket`: dla INFO / NOTICE / BIG_NOTICE / TALKING / DICE / FANCY_NOTICE / misji Zodiaku – tłumaczony format (LC_TEXT i nasze polskie formaty), a bez niego cała gotowa linia. Ogłoszenia (`notice_all`, `BroadcastNotice`, `d.notice`, P2P) docierają do każdego w jego języku, bo tłumaczy odbiorca. Nigdy COMMAND, czat graczy, szepty, gildia, drużyna. |
| Questy | `quest/mt2009_language.lua` (ładowany po `locale.lua`, ASCII): `say`, `say_title`, `say_reward`, `say_split`, `say_item`, `select` (też menu NPC), `select_table`, `makequestbutton`, `q.set_title` / `set_clock_name` / `set_counter_name` oddają tekst do `mt2009_tr()`; `item_name` / `get_item_name` / `mob_name` – nazwa w języku czytelnika. Questy liczą i porównują dalej po polsku; **qc i kompilacja questów bez zmian**. |
| Lua | `pc.get_language()`, `pc.set_language(kod)`, `mt2009_tr(tekst[, kod])`, `mt2009_item_name(vnum[, kod])`, `mt2009_mob_name(vnum[, kod])`, `mt2009_languages()` |
| C++ | `mt2009_language.h`: `GetPlayerLanguage(ch)`, `SetPlayerLanguage(ch, kod)`, `Mt2009Translate(kod, polski)`, `Mt2009TranslateFor(ch, polski)`, `LC_TEXT_FOR(ch, klucz)`, `Mt2009ItemNameIn`, `Mt2009MobNameIn` (boty: `GetPlayerLanguage(target)`) |

## Silnik (`edits.json`, 7 edycji) i nakładka

| Plik | Co |
|---|---|
| `char.cpp` | `#include "mt2009_language.h"`; `ChatPacket` – format / linia w języku czytelnika (długość obcięta do bufora) |
| `input_login.cpp` | `Entergame` – `player.language` przed questami logowania |
| `questlua.cpp` | funkcje Lua; `quest/mt2009_language.lua` po `locale.lua` (brak / błąd – questy po polsku, nie blokuje startu) |
| `cmd.cpp` | `/lang` (GM_PLAYER, POS_DEAD) |

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

Bez klienta z `/lang` nic się nie zmienia: wszyscy mają `pl`.
