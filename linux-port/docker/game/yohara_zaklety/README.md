# Zaklęty Las i Erebu (`MT2009_PLUS_YOHARA_ZAKLETY_V1`)

Zaklęty Las – las Jotuna Thryma za Świątynią Ochao, jak na pl-wiki („Zaklęty Las”, „Erebu”, siedem misji
strażników). Zastępuje Zaczarowany Las z Arezzo (`natural_map`, 362), który został usunięty (właściciel,
14.10.2026).

| Mapa | Nazwa | Folder | Baza | Rdzeń |
|---|---|---|---|---|
| 353 | Zaklęty Las (+ Erebu – prywatna kopia narożnika z bossami, 3530000+) | `metin2_map_dawnmist_dungeon_01` (3×4) | 768000 1408000 | Yohara (game3) |

Teren to ten sam las co Zaklęty Las (PB) (371) i (SZC) (404): `server_attr` = komórka w komórkę `attr.atr`
klienta (sprawdzone), w kliencie kopiowany folder z `ParentMapName` = `metin2_map_boss_awaken_dawnmist`
(`client-patches/client-2.0.30/tools/yzaklety`). Baza nie nachodzi na żadną mapę z `atlasinfo.txt`.

## Wejście

- Świątynia Ochao (209): po pokonaniu Strażnika En-Tai jego Portal przez minutę prowadzi do **Zaklętego Lasu**
  (albo na Zbocze Gautama) – quest `temple_of_the_ochao`. Od poziomu 95.
- Kto był wylogowany w lesie dłużej niż 10 minut, wraca przed wejście do Świątyni (Strażnik Świątyni na Zboczu
  Gautama). Teleporter w lesie (477,984). `/goto las` dla GM.
- To nie jest mapa Yohary ani Sung Ma, ale stoi na rdzeniu Yohary obok lasów PB/SZC – boty tam nie wchodzą.

## Misje (quest `zaklety_las`, każdy gracz osobno, od 95 poziomu)

1. **Chaos w Zaklętym Lesie** – Strażnik Świątyni (Zbocze Gautama) daje Ducha Ziemi dla Strażnika Lasu:
   5 825 000 PD i 5 Róż Alpejskich.
2. **Pierwszy rekonesans** – 50 Wojowników En-Tai: 776 600 PD.
3. **Znajdź apteczkę** – Apteczka od Druidów En-Tai (1 na 25): 776 600 PD.
4. **Dostarcz apteczkę** – do Zwiadowcy Lasu: 5 582 500 PD i 10 Korzeni Gango.
5. **Drugi rekonesans** – 5 Metinów Drzewnych Stworzeń: 7 766 000 PD.
6. **Zdobądź Rosy En-Tai** – 5 Ros od Niszczycieli En-Tai (1 na 10): 7 766 000 PD i 10 Wód Young.
7. **Zabij władcę En-Tai** – Badacz Lasu: Szlachetne Drewno z Władcy En-Tai (11 650 000 PD), potem Drzewny
   Szmaragd (11 650 000 PD i **Kamień Driad**). Potem od misji 2 po kolejny Kamień Driad.

## Erebu (quest `erebu`)

Przywódca Straży Lasu (615,108): tylko grupa, otwiera przywódca, co najmniej 5 osób (do 8), każdy od 95 poziomu
z Kamieniem Driad (znika przy wejściu), cała grupa przy nim. Najpierw Bagjanamu, minutę po nim Jotun Thrym
(przywołuje Uzdrowicieli Ochao). 30 minut; po zwycięstwie 3 minuty i powrót do Przywódcy. Ponownie 2 godziny
po zakończeniu (flaga `erebu.end` – też w panelu lochów, linia `erebu`). „Wróć do Erebu” – do trwającej wyprawy.

## Potwory (wiki: poziomy, PD, żywioły)

Wojownik / Bojownik / Druid / Uzdrowiciel / Niszczyciel En-Tai (100–108, Wiatr), Silni En-Tai (117–120, Wiatr –
wychodzą z Metinów Lasu), Władca En-Tai (112, boss, Lód), Bagjanamu (120, boss, Lód), Jotun Thrym (123, boss,
Ziemia, 10–27 mln Yang), Uzdrowiciel Ochao (110, Wiatr), Metin Drzewnych Stworzeń (100), Metin Lasu (120).
Dropy z list wiki (nasze szanse); Bagjanamu 10 Skrzyń Bagjanamu, Jotun Thrym 9 Skrzyń Jotuna Thryma (zawartość
z wiki, jedna rzecz na otwarcie). Event dropu serwera testowego nie jest kompensowany.

## Pliki

- `tools/yohara_zaklety/gen_yzaklety.py` (+ `yzaklety_data.py`) generuje: `map/metin2_map_dawnmist_dungeon_01/`,
  `data/monster/` (ruchy trent_*, thunder_boss), `group.yohara_zaklety.txt` (6311–6318, 6330–6333),
  `mob_drop_item.yohara_zaklety.txt`, `special_item_group.yohara_zaklety.txt`, `spawned.txt`,
  `mariadb/playerbot/yohara_zaklety.sql`, `yohara_items_zaklety.sql`, `yohara_zaklety_zywioly.sql` i dane klienta.
- Dockerfile: krok „share: Zaklety Las (353) and Erebu”; `bin/m2-render-config`: 353 na rdzeniu Yohary;
  `apply.sh`: SQL i jednorazowe przeniesienie postaci z mapy 362 do Świątyni Ochao.
- Strażnicy lasu: 20160–20162 (nasze numery – 20409–20411 to łucznicy w Dolinie Orków), Przywódca 20412.

## Usunięte z Zaczarowanym Lasem (362)

Mapa, indeks, rdzeń game1, nazwa, `/goto las` (teraz 353), grupy lemurów 36201–36203, wiersz `atlasinfo`
klienta; boty: wyprawy do Lasu (zapas 600/400 mikstur, pobyt 2 h, droga przez Świątynię), rajdy na Lemura Hrabiego
i Straż Przyboczną w Lesie, pożyczanie botów z lochów Arezzo. Strażnik Starożytnej Dżungli stoi w Świątyni
Ochao (przy wejściu), wyjście z Dżungli też tam. Seon-Hae: Duży suplement i odłamki – w Zaklętym Lesie (353).
Przedmioty i potwory z Lasu zostają w bazie.
