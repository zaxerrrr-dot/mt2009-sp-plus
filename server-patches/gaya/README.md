# gaya – koszt Gaya w oknie wytwarzania (Yohara)

`MT2009_PLUS_GAYA_V1` (14.10.2026, decyzja właściciela: „Kamienie Gaya – dodać”, `cache/yohara/decyzje.md`
„14.10 ok. 8:10”).

Gaya to u nas przedmiot-waluta **95927 „Gaya”** (nie do wymiany, nie do sprzedania, stos do 999 999 – wiki „Gaya”:
maks. 999.999, nie można nią handlować). Zdobywa się ją szlifując Kamyki (95926) u Statuy Wojownika w porcie
(quest `ygaya`, 70%), płaci w Portowym Sklepie Gaya, u Tajemniczego Ołtarza, u Mistrza Chi (questy) oraz w oknie
wytwarzania (cube) – i tylko to ostatnie wymaga silnika:

- `cube.h` – `CUBE_DATA::gaya` (domyślnie 0),
- `cube.cpp` – linia receptury `gaya N` (`cube.txt`); przed zabraniem czegokolwiek sprawdzane jest, czy gracz ma
  w ekwipunku N Gaya (komunikat „Masz za mało Gaya (potrzeba N).”), a Gaya znika razem z materiałami i Yang – także
  przy nieudanej próbie (jak Yang). Dotyczy zwykłych receptur i receptur kowali zestawów (`ysets`,
  `Mt2009YSetsCubeMake`).

Receptury z Gaya (wiki / Owsap `cube.txt` „gem”): kowale zestawów 20475–20479 – 500, Statua Węży 20807 (wężowe bronie
i zbroje) – 100 (`tools/ysets/gen_ysets.py`). Skrzynek Żywiołaków u Statui Wojownika nie ma (decyzja właściciela
14.10.2026 – pet tylko w ItemShopie). Okno wytwarzania klienta pokazuje Gaya tylko u kowali zestawów (niżej, V2);
u innych NPC (Statua Węży ma już 5 materiałów – więcej okno nie mieści) koszt podają rozmowy z NPC.

`MT2009_PLUS_GAYA_V2` (runda 15.10 nr 10): wiersz kowala zestawów (`ysets` V4) pokazuje Gaya jako materiał
(95927 × N), a `Cube_add_item` nie przyjmuje Gaya do okna (komunikat) – zabierana jest z ekwipunku, a stos opróżniony
tam, gdy leżał w oknie, zostawiłby w oknie wskaźnik na usunięty przedmiot.

Siedem edycji, każda ze swoim znacznikiem. Po `ysets` (edycja „cube set” stoi w jego funkcji `Mt2009YSetsCubeMake`).

`MT2009_PLUS_NPC_CRAFT_WINDOW_V1` (22.10.2026, właściciel: „u każdego NPC z wytwarzaniem ma się otworzyć okno
i pokazać, co trzeba dać” – jak na serwerach globalnych). Siedemnaście edycji (`cube.h`, `cube.cpp`, `cmd_general.cpp`):

- lista materiałów okna (`cube m_info`): każdy wiersz `materiały/Yang/szansa/Gaya/kategoria` – szansa `30` albo `5-50`
  (wiersz scalony z receptur +5…+9), Gaya 0 gdy nie trzeba; wiersz kowala zestawów `…/Yang/szansa/0/kategoria`
  (jego Gaya jest materiałem). Stary klient czyta tylko Yang (drugie pole);
- `cube pick <vnum nagrody>` (klient przed `cube make`): najpierw receptura z tą nagrodą, do której pasują materiały
  w oknie, inaczej – jak dotąd – pierwsza pasująca. Receptury o tych samych materiałach (obręcz / kolia / klipsy
  jednego jadeitu, Pył i Jedwab Wężowy) dawały zawsze pierwszą z `cube.txt`;
- `cube improve <komórka ekwipunku>` (−1: brak) – przedmiot „Podwyższ szansę”: tabela `locale/cube_improve.txt`
  (`vnum premia kategoria [npc,npc…]`, czytana przy pierwszym otwarciu okna i `/reload c`); działa na recepturę swojej
  kategorii (u wskazanych NPC), dodaje premię (do 100%), przy każdej próbie znika jedna sztuka (`Cube_make_window`,
  `cube make`). Odpowiedź do klienta: `CubeImprove vnum premia kategoria`. Runy Wykuwania (79605–79659) – ich
  przedmiotów jeszcze nie ma, linie w tabeli są zakomentowane;
- kategoria receptury: linia `category N` (0 zbroje … 13 alchemia, jak globalne okno) albo z przedmiotu-wyniku;
- `copy_attr 1` (receptura): wynik dostaje kamienie i bonusy pierwszego przedmiotu receptury (`CopyAllAttrTo`, jak
  ulepszenie) – Admirał Angmur (`game/cube.npc_okno.txt`); Seon-Pyeong (20091): jego wiersze rdzeń robi sam z zestawów
  ulepszeń elitarnych (`IsEliteRefine`: przedmiot +9, materiały, Yang i szansa receptury, przedmiot po ulepszeniu),
  przy pierwszym otwarciu okna (i po `/reload c`) – te same kroki, co przeciągnięcie przedmiotu na niego.

Klient: `client-patches/client-2.0.30/root/game.py`, `uicube.py`, `uicubeokno.py` (ten sam znacznik).

Linux/VPS: `python3 apply_gaya.py <game/src>`; Windows: `Apply-GayaPatch.ps1 -SourceDir <game/src>` (wołane przez
`tools/port/Apply-MT2009PlusEngine.ps1`). Pliki silnika: `cube.h`, `cube.cpp`, `cmd_general.cpp`.
