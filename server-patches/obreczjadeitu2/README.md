# obreczjadeitu2 – Obręcze Jadeitu: dwa losowe bonusy i gniazda na jadeit (V2)

`MT2009_PLUS_JADE_BRACELET_V2` (14.10.2026, błąd 17 z `cache/yohara/bledy-3.0.md`: „Obręcze Jadeitu nie mają
żadnych bonusów … Precyzja i Wola SungMa … wartości wg poziomu … do 3 gniazd tworzonych Diamentem, w gniazda Jadeit –
bonusy się sumują”). Zastępuje jedną linię Woli z V1 (`server-patches/obreczjadeitu` – zostaje: jej typ obręczy i
blokady przedmiotów 6/7 bonusu działają dalej).

## Bonusy podstawowe (pl-wiki „Obręcz Jadeitu Mgły” i pozostałe)

Dwie linie w 6. i 7. bonusie przedmiotu, każda z szansą `will_tal_line_pct` (80% – „istnieje prawdopodobieństwo, że nie
będzie żadnego z nich”), wartość losowa z zakresu poziomu:

| | +0 | +1 | +2 | +3 | +4 | +5 | +6 | +7 | +8 | +9 |
|---|---|---|---|---|---|---|---|---|---|---|
| Precyzja (`POINT_HIT_PCT`) | 1–2 | 2–3 | 3–4 | 4–5 | 5–6 | 6–7 | 7–8 | 8–10 | 9–11 | 10–14 |
| Wola SungMa obręczy | 1–2 | 3–4 | 5–6 | 7–8 | 9–10 | 11–12 | 13–14 | 15–17 | 18–20 | 21–24 |

Wola: Mgły ODP, Słońca INT, Nocy WIT, Dymu SIŁA. Ulepszenie przenosi obie linie w to samo miejsce zakresu nowego
poziomu (także jedną linię Woli obręczy z V1), brakującą dodaje (jak Talizmany Woli). Przedmioty 6/7 bonusu ich nie
zmieniają (blokady V1). Precyzja działa na mapach Sung Ma (`server-patches/precyzja`).

## Gniazda i jadeit

Diament (50621, `USE_ADD_ACCESSORY_SOCKET`) robi gniazdo (do 3, silnik: szansa 50%), Jadeit obręczy (Mgły 50664,
Słońca 50661, Nocy 50662, Dymu 50663; `USE_PUT_INTO_ACCESSORY_SOCKET`) wchodzi tylko do swojej obręczy (tabela
`CItem::CanPutInto`, edycja `(jewel)`; klient: `root/constinfo.py`). Wkładanie, szanse i znikanie po 24 / 12 / 6 h
to zwykłe gniazda biżuterii silnika (`aiAccessorySocketPutPct`, `aiAccessorySocketDegradeTime` – te same czasy co
wiki). Każdy jadeit dodaje do linii, które obręcz ma (wiki, „Verb” obręczy):

| gniazdo | Precyzja | Wola |
|---|---|---|
| 1. | +1 | +1 (+2 na +9) |
| 2. | +1 (+2 na +9) | +1 (+2 od +7) |
| 3. | +1 (+2 na +9) | +1, +1, +1, +1, +1, +2, +3, +3, +4, +4 (+0…+9) |

– `Mt2009JadeBraceletSocketPoints` w `CItem::ModifyPoints`; dymek pokazuje to przy każdym gnieździe
(`root/uitooltip.py`, `yoharagear.py`).

Tworzenie obręczy (Mistrz Chi, quest `yohara_mapy4`) bez zmian.

## Naszyjniki i kolczyki z jadeitu (`MT2009_PLUS_JADE_JEWELLERY_V1`)

14.10.2026, właściciel: „Kolia Jadeitu …” (16580–16619) i „Klipsy Jadeitu …” (17570–17609) – Mgły ODP, Słońca INT,
Nocy WIT, Dymu SIŁA; te same dwie linie, gniazda Diamentu i jadeit co obręcze, wartości wg stron wiki każdego rodzaju:

| | +0 | +1 | +2 | +3 | +4 | +5 | +6 | +7 | +8 | +9 |
|---|---|---|---|---|---|---|---|---|---|---|
| Precyzja (wszystkie) | 1–2 | 2–3 | 3–4 | 4–5 | 5–6 | 6–7 | 7–8 | 8–10 | 9–11 | 10–14 |
| Wola: obręcze, kolie | 1–2 | 3–4 | 5–6 | 7–8 | 9–10 | 11–12 | 13–14 | 15–17 | 18–20 | 21–24 |
| Wola: klipsy | 1–2 | 2–4 | 3–6 | 5–8 | 7–10 | 9–12 | 13–14 | 15–17 | 18–20 | 21–24 |

(Strona „Kolia Jadeitu Dymu” jako jedyna kolia podaje zakresy klipsów – przyjęte jak u trzech pozostałych kolii i u
Owsapa, gdzie wszystkie trzy rodzaje mają jedną tabelę `ApplyRandomValue6`.)

Jadeit w gniazdach kolii / klipsów: Precyzja +1 (3. gniazdo +2 na +9); Wola jak w obręczy, tylko 1. gniazdo klipsów
zawsze +1. Silnik: przełącznik typów V1 (`item_attribute.cpp`, edycja `(types)`), tabela `CanPutInto` (`(jewel)`;
wiersz kolczyków Turmalinu 17570 – to Klipsy Jadeitu Mgły, takich kolczyków nie mamy – wyzerowany jak u Owsapa,
`(turmalin)`), tabele rodzajów w `playerbot_yohara_gear.cpp` (`JadeKindOf` – podtyp pancerza). Klient:
`root/constinfo.py`, `yoharagear.py`. Tworzenie u Mistrza Chi (quest `yohara_mapy4`) i skrzynie wiki (krok Dockerfile
`MT2009_PLUS_JADE_JEWELLERY_V1`, `linux-port/docker/game/jadejewel`).

## Silnik

`item_manager.cpp` `(new)`, `item_attribute.cpp` `(refine)`, `(types)`, `item.cpp` `(socket points)`, `(jewel)`,
`(turmalin)`, `(jewel)` naszyjników – 7 edycji, każda
ze swoim znacznikiem (`gen_edits.py [<game/src>]`); logika: `playerbot_yohara_gear.cpp` (nakładka). Po
`obreczjadeitu` (wywołania V1 są zastępowane), `precyzja` (`POINT_HIT_PCT`) i `rekawice`.

- Linux/VPS: `python3 apply_obreczjadeitu2.py <game/src>`; Windows: `Apply-ObreczJadeitu2Patch.ps1 -SourceDir <game/src>`
  (`tools/port/Apply-MT2009PlusEngine.ps1`).
