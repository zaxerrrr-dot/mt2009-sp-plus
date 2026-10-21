# buffi – Buffi, szamanka wsparcia z Amerii

`MT2009_PLUS_BUFFI_V1` (21.10.2026, decyzja właściciela dla Yohary 3.0: „Wyłącz system towarzysza … W zamian za towarzysza
dodaj system buffi z Amerii. Pod tym samym skrótem klawiszowym itd.”). Źródło: Ameria Project
(`/opt/metin2/ameria/ameria-prj-2025`: `srcs/server/game/buffi.{h,cpp}`, `char_state.cpp` `StateBuffi`, `char_skill.cpp`,
`questlua_pc.cpp` `pc.set_buffi_name`, quest `__buffi__`, `item_proto.txt`, `player.sql` – `skill_proto` 164–167,
`shop_item`, `ishop_data`, skrzynia 66002).

## Jak działa (mechanika i liczby Amerii)

- **Pieczęć** Buffi (7 dni) 61025 / Buffi 61026 – użycie przywołuje szamankę (mob 65000), ponowne użycie ją odwołuje
  (najwyżej raz na sekundę). Jedna Buffi na postać. Gniazdo 1 pieczęci = „przywołana”: po wejściu do gry / zmianie mapy
  Buffi wraca sama. Odłożona / sprzedana / wygasła pieczęć – Buffi znika.
- **Wzmocnienia**: co 3 s Buffi rzuca na właściciela pierwsze brakujące: Błogosławieństwo, Pomoc Smoka, a gdy ma imię
  także Szybkość i Zwiększenie Ataku. Wartości z wierszy `skill_proto` 164–167 Amerii (iq = 226, ×0,2; k = moc poziomu
  z tabeli potworów, jak u Amerii, gdzie rzuca mob): Błogosławieństwo i Pomoc Smoka `(226*0,2+5)*(2k+0,5)/(k+1,5)` %,
  Szybkość `5+35k` szybkości ruchu (3600 s) i `3+33k` szybkości czarowania (`60+100k` s), Zwiększenie Ataku `5+60,2k`
  wartości ataku; czas 3600 s. To efekty prawdziwych umiejętności (typy 94/96/110/111) – nigdy na ten sam efekt
  prawdziwego szamana (Ameria też pomija). Wymagana wybrana droga umiejętności (jak u Amerii).
- **Umiejętności** 164–167 to umiejętności właściciela (zapisane z postacią), M1 przy pierwszym przywołaniu. **Księgi**
  61035–61038 – M1 → G1 zwykłym czytaniem ksiąg silnika (te same odstępy, Zwój Egzorcyzmu, Rada Pustelnika).
  **Kamień Duchowy Buffi** 61031 – G1 → P (quest `buffi`, jak Kamień Duchowy: punkty rangi 1000 + 500 za stopień, przy
  ujemnej podwójnie, nieudana próba 1/3–1/2; następna próba po 12 h jak u nas, Zwój Egzorcyzmu od razu). Reset
  umiejętności ich nie rusza.
- **Zwój Imienia Buffi** 61030 – imię dla przywołanej Buffi (jedno na pieczęć – `player.mt2009_buffi_name`, u Amerii plik
  `share/buffi_name/<id przedmiotu>`), odblokowuje Szybkość i Zwiększenie Ataku i daje +10% silny przeciwko bossom na
  7 dni (efekt 640, Ameria `AFFECT_NAME_BUFFI`). Nowe imię dopiero, gdy ten bonus minie (Ameria też odmawia).
- **Skąd**: nowa postać (poziom ≤ 5, raz) dostaje 61025 i 61030 (skrzynia startowa 66002 Amerii); ItemShop „Koń i pomoc”:
  Buffi 61026 za 750, Zwój Imienia za 50 (ceny Amerii); Handlarka (9003) „Księgi i kamienie Buffi”: księga za
  1 000 000 Yang + 3 Zwoje Egzorcyzmu, Kamień Duchowy Buffi za 500 000 Yang + 2 Kamienie Duchowe (sklep 3 Amerii).
  Ameria dawała też Zwój Imienia z Bossa Świata (5%) i skrzyń – tu nie (Boss Świata to osobna praca).
- **Wygląd**: szamanka (rasa 3) w Czarnej Szacie+9 i z Ekstazyjnym Wachlarzem+9 (domyślne Amerii). Cztery sloty kostiumów
  Buffi z Amerii to nowe pola ekwipunku w exe – nie przeniesione.
- **Boty** Buffi nie mają.

## Bez zmiany exe

Na serwerze Buffi to NPC (pet: bez własnego AI, nie do zaatakowania), klientom pokazywany jako postać szamanki (typ PC,
rasa 3 – `BuffiInsertLook` w `EncodeInsertPacket`; części z dodatkowej informacji jak u każdego NPC). Rzucanie widać jako
ruch umiejętności (`FUNC_SKILL | ruch umiejętności`, ruch + stopień × 25 – jak `GradeData` klienta). Okno:
`root/uibuffi.py` („/buffi info|toggle|name”, odpowiedź „BUFFI state …”, „BUFFI askname”, „BUFFI off”).

## Przełącznik

`M2_BUFFI` (`docker-compose.yml`, środowisko gry i migratora; domyślnie 1). 0: nikt nie przywoła Buffi, przywołana
znika, quest milczy (`m2_buffi_off`); pieczęcie, imiona i umiejętności zostają.

## Pliki

Zmiany silnika (`edits.json`, `gen_edits.py [<game/src>]` tworzy i sprawdza kotwice): `char_item.cpp` `(use)`,
`char_skill.cpp` `(learnable)`, `(reset)`, `input_login.cpp` `(login)`, `char.cpp` `(insert)`, `(level)`, `cmd.cpp`
`(declare)`, `(table)`. Logika: `linux-port/overlays/playerbot/src/game/src/playerbot_buffi.cpp`. Quest:
`linux-port/docker/game/quest/buffi.quest`. Dane: `tools/buffi/gen_buffi.py` → `buffi.sql`, `buffi_itemshop.sql`,
`tools/buffi/buffi.json`, ikony w `client-2.0.30/root/icon/item`. Klient: `client-2.0.30/root/uibuffi.py`,
`client-2.0.30/tools/buffi` (przedmioty w `dbdata`/`gamedata`).

- Linux/VPS: `python3 apply_buffi.py <game/src>`; Windows: `Apply-BuffiPatch.ps1 -SourceDir <game/src>`
  (`tools/port/Apply-MT2009PlusEngine.ps1`, ostatni – po `monstercard` i `riposty`).
