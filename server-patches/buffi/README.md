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
- **Umiejętności** 164–167 to umiejętności właściciela (zapisane z postacią): Błogosławieństwo i Smocza Pomoc – M1 przy
  pierwszym przywołaniu, Szybkość i Zwiększenie Ataku – M1, gdy Buffi dostanie imię (jak w Amerii).
  **M1 → G1** (`MT2009_PLUS_BUFFI_V2`, właściciel 21.10.2026): zwykła **Księga Umiejętności szamana** (50300 z
  umiejętnością 94 / 96 / 110 / 111) przeciągnięta w oknie Buffi na jej umiejętność (`/buffi read`) – czytanie silnika
  (`LearnSkillByBook`: szansa, liczba ksiąg na poziom, 20 000 PD, odstęp, Zwój Egzorcyzmu, Rada Pustelnika) na
  umiejętności Buffi, nigdy na własnej umiejętności czytającego. Księgi Buffi 61035–61038 nie mają już źródła
  (wiersze zostają; posiadana dalej działa).
  **Kamień Duchowy Buffi** 61031 – G1 → P (quest `buffi`, jak Kamień Duchowy: punkty rangi 1000 + 500 za stopień, przy
  ujemnej podwójnie, nieudana próba 1/3–1/2; następna próba po 12 h jak u nas, Zwój Egzorcyzmu od razu). Wypada z Metinów
  i bossów od Zaklętego Lasu wzwyż (`tools/ymoby_arkusz/gen_buffi_stone.py`, `MT2009_PLUS_BUFFI_STONE_DROP_V1`).
  Reset umiejętności ich nie rusza.
- **Kostiumy Buffi** (`MT2009_PLUS_BUFFI_V2`, sloty Amerii): `WEAR_BUFFI_BODY/HEAD/WEAPON/SASH` = 28–31 (wolne pola pod
  `WEAR_MAX` 32 – bez zmiany układu pól, pakietów i bazy). Kostium przeciągnięty w oknie Buffi na jej slot albo użyty z
  torby przy otwartym oknie (`/buffi page 1|0`, Ameria: `/buffi_costume_page`) trafia na Buffi: strój i fryzura dla
  kobiety, broń, którą może trzymać szaman, dowolna szarfa. Kostiumy Buffi nie dają właścicielowi nic (`(points)`),
  a szamanka je nosi (strój, fryzura, broń i szarfa; przetransmutowany – z wyglądem).
- **Zwój Imienia Buffi** 61030 – imię dla przywołanej Buffi (jedno na pieczęć – `player.mt2009_buffi_name`, u Amerii plik
  `share/buffi_name/<id przedmiotu>`), odblokowuje Szybkość i Zwiększenie Ataku i daje +10% silny przeciwko bossom na
  7 dni (efekt 640, Ameria `AFFECT_NAME_BUFFI`). Nowe imię dopiero, gdy ten bonus minie (Ameria też odmawia).
- **Skąd**: nowa postać (poziom ≤ 5, raz) dostaje 61025 i 61030 (skrzynia startowa 66002 Amerii); ItemShop „Koń i pomoc”:
  Buffi 61026 za 750, Zwój Imienia za 50 (ceny Amerii). Oferta Handlarki (9003) „Księgi i kamienie Buffi” – usunięta
  w V2 (decyzja właściciela 21.10.2026).
  Ameria dawała też Zwój Imienia z Bossa Świata (5%) i skrzyń – tu nie (Boss Świata to osobna praca).
- **Wygląd**: szamanka (rasa 3) w Czarnej Szacie+9 i z Ekstazyjnym Wachlarzem+9 (domyślne Amerii) albo w kostiumach
  ze swoich slotów (V2).
- **Boty** Buffi nie mają.

## Bez zmiany exe

Na serwerze Buffi to NPC (pet: bez własnego AI, nie do zaatakowania), klientom pokazywany jako postać szamanki (typ PC,
rasa 3 – `BuffiInsertLook` w `EncodeInsertPacket`; części z dodatkowej informacji jak u każdego NPC). Rzucanie widać jako
ruch umiejętności (`FUNC_SKILL | ruch umiejętności`, ruch + stopień × 25 – jak `GradeData` klienta). Okno:
`root/uibuffi.py` + `uiscript/buffiwindow.py` (V2: strona IV ekwipunku Amerii – `companion_bg.png` ze slotami kostiumów
– i strona „Buffi” umiejętności Amerii – `buffi_skill_bg.png`, siatka stopni, zasłony bez imienia; „/buffi
info|toggle|name|page|read”, odpowiedź „BUFFI state …”, „BUFFI askname”, „BUFFI off”). Dane klienta umiejętności
164–167 (skilldesc/skilltable): `tools/buffi/gen_buffi.py` → `buffi.json` → `client-2.0.30/tools/buffi`.

## Przełącznik

`M2_BUFFI` (`docker-compose.yml`, środowisko gry i migratora; domyślnie 1). 0: nikt nie przywoła Buffi, przywołana
znika, quest milczy (`m2_buffi_off`); pieczęcie, imiona i umiejętności zostają.

## Pliki

Zmiany silnika (`edits.json`, `gen_edits.py [<game/src>]` tworzy i sprawdza kotwice): `char_item.cpp` `(use)`,
`char_skill.cpp` `(learnable)`, `(reset)`, `input_login.cpp` `(login)`, `char.cpp` `(insert)`, `(level)`, `cmd.cpp`
`(declare)`, `(table)`; `MT2009_PLUS_BUFFI_V2`: `common/length.h` `(wear)`, `item.cpp` `(cell)` (FindEquipCell),
`(points)` (ModifyPoints), `char_item.cpp` `(begin)` (EquipItem), `(swap)` (SwapItem), `(job)` (CanEquipNow), `(sex)`
(FN_check_item_sex). Exe: `client-patches/exe` (`ENABLE_MT2009_BUFFI_COSTUME`: te same numery pól, `item.BUFFI_SLOT_*`) –
stary exe też trzyma przedmioty tych pól, `root` bierze je wtedy z `player.EQUIPMENT_SLOT_START`. Logika: `linux-port/overlays/playerbot/src/game/src/playerbot_buffi.cpp`. Quest:
`linux-port/docker/game/quest/buffi.quest`. Dane: `tools/buffi/gen_buffi.py` → `buffi.sql`, `buffi_itemshop.sql`,
`tools/buffi/buffi.json`, ikony w `client-2.0.30/root/icon/item`. Klient: `client-2.0.30/root/uibuffi.py`,
`client-2.0.30/tools/buffi` (przedmioty w `dbdata`/`gamedata`).

- Linux/VPS: `python3 apply_buffi.py <game/src>`; Windows: `Apply-BuffiPatch.ps1 -SourceDir <game/src>`
  (`tools/port/Apply-MT2009PlusEngine.ps1`, ostatni – po `monstercard` i `riposty`).
