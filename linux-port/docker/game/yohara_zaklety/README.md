# Zaklęty Las i Erebu – linia 2.x (`MT2009_PLUS_237_ZAKLETY_LAS_V1`)

Zaklęty Las – las Jotuna Thryma za Świątynią Ochao, jak na pl-wiki („Zaklęty Las”, „Erebu”, siedem misji
strażników). Od 2.37 także na linii 2.x (właściciel, 22.10.2026: „mapa domyślna, której nie da się wyłączyć”).
Zastępuje Zaczarowany Las z Arezzo (`natural_map`, 362), który został usunięty – tak samo jak na linii Yohara
(decyzja właściciela z 14.10.2026). Reszta modułu Arezzo (360, 361, 363–366, przełącznik `M2_AREZZO`) bez zmian.

| Mapa | Nazwa | Folder | Baza | Rdzeń |
|---|---|---|---|---|
| 353 | Zaklęty Las (+ Erebu – prywatna kopia narożnika z bossami, 3530000+) | `metin2_map_dawnmist_dungeon_01` (3×4) | 768000 1408000 | game2 (zawsze) |

Pliki tego katalogu i SQL-e `yohara_zaklety*.sql`, `yohara_items_zaklety.sql` są wynikiem generatora linii Yohara
(`tools/yohara_zaklety/gen_yzaklety.py` na `claude/yohara-3`), przeniesionym skryptem `tools/las237/port_las237.py`
– bez ręcznych zmian. Skrypt pomija wiersze dropu i skrzyń z przedmiotami, których świat 2.x nie ma (płyty i barwniki
zbroi 105, Plan Zbroi, Podręczniki i Skrzynie Ksiąg ripost/dopalaczy, Kamień Duchowy+, Księga Młodego Zwierza,
Żółty Lśniący Odłamek) – lista jest w nagłówkach plików. Po zmianie na linii Yohara: uruchomić skrypt ponownie.

## Wejście

- Strażnik Świątyni (20426) stoi tylko na **Zboczu Gautama** (302, komórka 1003,700 – jak na wiki,
  `MT2009_PLUS_OCHAO_GAUTAMA_V1`) i od 95 poziomu prowadzi do Świątyni Ochao (209, game1).
- Po pokonaniu Strażnika En-Tai jego Portal przez minutę prowadzi do **Zaklętego Lasu** (albo na Zbocze Gautama) –
  quest `temple_of_the_ochao`. Od poziomu 95. Teleporter w lesie (477,984). `/goto las` dla GM.
- Kto był wylogowany w lesie dłużej niż 10 minut, wraca przed wejście do Świątyni.

## Misje, Erebu, potwory

Jak na linii Yohara – patrz quest `zaklety_las` (7 misji, Kamień Driad), `erebu` (Przywódca Straży Lasu, grupa 5–8
od 95 poziomu z Kamieniem Driad, Bagjanamu i Jotun Thrym, 30 min, ponownie po 2 h; linia `erebu` w panelu lochów).
Potwory: En-Tai 100–108 (Wiatr), Silni En-Tai 117–120 (z Metinów Lasu), Władca En-Tai 112 (Lód), Bagjanamu 120 (Lód),
Jotun Thrym 123 (Ziemia), Metin Drzewnych Stworzeń 100, Metin Lasu 120. Seon-Hae: Duży suplement i odłamki w lesie.

## Boty

Las jest na game2, boty żyją na game1 – przechodzą tam **przekazaniem między rdzeniami**
(`playerbot_yohara_bots.h`, `MT2009_PLUS_BOT_YOHARA_HANDOVER_V1`, tabela `common.playerbot_core_handover`):
od 100 poziomu i 20 000 PŻ, droga przez Świątynię Ochao (Strażnik En-Tai albo 20 min czekania), pobyt jak wyprawa
(mikstury uzupełniane w lesie), Niszczyciele En-Tai i Metiny lasu tylko w drużynie 3+, po 110 poziomie bot z lasu
wyrasta. Wyłącznik: `PLAYERBOT_HANDOVER=0` w `.env` albo zdarzenie `m2_bot_handover_off 1`.

## Klient

`client-patches/client-2.0.30/tools/zaklety237` (samodzielny teren lasu dla klienta 2.x) + nazwy w `root`.
