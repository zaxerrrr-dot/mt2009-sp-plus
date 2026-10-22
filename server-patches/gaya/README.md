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
i pokazać, co trzeba dać” – jak na serwerach globalnych). Dwanaście edycji (`cube.h`, `cube.cpp`, `cmd_general.cpp`):

- lista materiałów okna (`cube m_info`) ma w każdym wierszu po Yang także szansę i Gaya:
  `materiały/Yang/szansa[/Gaya]` – szansa `30` albo `5-50` (wiersz scalony z receptur +5…+9 – najniższa i najwyższa),
  Gaya tylko gdy receptura ją bierze; wiersz kowala zestawów: `.../Yang/szansa` (Gaya jest tam materiałem). Stary
  klient czyta tylko Yang (drugie pole) i resztę pomija;
- `cube pick <vnum nagrody>` (klient wysyła przed `cube make` – wiersz, który gracz kliknął): `Cube_make` i podgląd
  Yang biorą najpierw recepturę z tą nagrodą, do której pasują materiały w oknie, inaczej – jak dotąd – pierwszą
  pasującą. Bez tego receptury o tych samych materiałach (obręcz / kolia / klipsy jednego jadeitu u Mistrza Chi, Pył
  i Jedwab Wężowy u Statui Węży) dawały zawsze pierwszą z `cube.txt`. Wybór znika przy otwarciu i zamknięciu okna;
  stary klient go nie wysyła (zachowanie jak dotąd).

Klient: `client-patches/client-2.0.30/root/game.py`, `uicube.py` (ten sam znacznik) – dymek wiersza: Yang, Gaya,
szansa; kliknięcie wiersza go wybiera (komunikat na czacie, Yang w polu okna). Receptury: `game/cube.npc_okno.txt`.

Linux/VPS: `python3 apply_gaya.py <game/src>`; Windows: `Apply-GayaPatch.ps1 -SourceDir <game/src>` (wołane przez
`tools/port/Apply-MT2009PlusEngine.ps1`). Pliki silnika: `cube.h`, `cube.cpp`, `cmd_general.cpp`.
