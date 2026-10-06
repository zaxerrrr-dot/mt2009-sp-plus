# Magazyn kolekcjonera (natychmiastowy)

Znacznik `MT2009_PLUS_COLLECTOR_STORAGE_V1`. Na podstawie systemu z projektu
upstream (based on the upstream Metin2 Playerbots project) – te same funkcje,
ale przepisane tak, żeby wkładanie i wyjmowanie było natychmiastowe, jak
przerzucanie między Towarzyszem a naszym ekwipunkiem.

Poprawka silnika dotyka tylko `game/src/cmd.cpp` (trzy wstawki z
`edits.json`, nakładane przez `Apply-CollectorPatch.ps1` przy wydaniu albo
linuksowy bliźniak `apply_collector.py`); całą pracę robi
`linux-port/overlays/playerbot/src/game/src/playerbot_collector.{h,cpp}`,
okno – `client-patches/client-2.0.30/root/uicollector.py`. Zmiana już
nałożona (jest jej znacznik) jest pomijana; zmiana, której kodu nie ma
dokładnie raz, przerywa całość, zanim cokolwiek zostanie zapisane.

## Co robi

- **Jeden magazyn na całe konto**, obok zwykłego magazynu (zwykły zostaje bez
  zmian, boty nadal używają tylko zwykłego). Otwiera się przyciskiem
  **„Kolekcjoner”** w oknie zwykłego magazynu – czyli u magazyniera, po haśle
  magazynu. Zamyka się, gdy odejdziesz (ok. 15 m od miejsca otwarcia).
- **Pojemność w wpisach**: 500 na start; „Rozbuduj” za Yang: 1000 (od 20 poz.,
  100 tys.), 2000 (35, 500 tys.), 3500 (50, 2 kk), 5000 (65, 5 kk),
  7500 (80, 10 kk), 10 000 (90, 20 kk) – tabela z upstream.
- **Stosy bez limitu**: przedmiot stakowalny bez bonusów to jeden wpis na
  rodzaj (ten sam vnum i te same sockety), niezależnie od liczby sztuk.
  Przedmioty z bonusami / niestakowalne – wpis na sztukę.
- **13 widoków**: Wszystko + 12 kategorii (Wyposażenie, Ulepszacze, Zwoje i
  bonusy, Księgi, Kamienie dusz, Zioła, Zużywalne, Skrzynie i klucze,
  Łowienie i kopanie, Zadania i eventy, Wygląd postaci, Inne) z licznikami,
  **wyszukiwarka po nazwie** (polskie litery), siatka 10 × 10 z przedmiotami
  w ich rozmiarze, strony `<< < X / Y > >>`, podpowiedź przedmiotu
  (z bonusami i liczbą sztuk), podświetlenie pola pod myszką, pasek
  zajętości „Zajęte X / Y” i suma sztuk.
- **Wkładanie**: prawy przycisk na przedmiocie w ekwipunku albo
  przeciągnięcie na siatkę; Shift + PPM pyta o ilość; **Ctrl + PPM chowa
  wszystkie stosy tego rodzaju** jednym poleceniem (pola zablokowane gwiazdką
  sortowania zostają).
- **Wyjmowanie**: PPM albo dwuklik – jeden stos (najpierw dopełnia stosy tego
  rodzaju w ekwipunku); Ctrl + PPM – wszystko, co się zmieści; Shift – ilość;
  przeciągnięcie do ekwipunku – na wskazane pole.
- Czego nie wolno włożyć – to samo co do zwykłego magazynu: `ANTI_SAFEBOX`,
  zablokowany przedmiot, rozszerzenie magazynu, pas z rzeczami w swoich
  polach, pola konia bez konia, kamienie smoka; ręce wolne (bez handlu,
  sklepu, questa), postać żywa.
- Nagród za kolekcję upstream nie miał – nie ma ich też tu.

## Dlaczego upstream się „zacinał”

W oknie upstream każdy ruch był: komenda → serwer sprawdza i **zatwierdza
zapis w bazie** → odpowiedź → okno **prosi o całą stronę od nowa**, a serwer
układa ją i odsyła wiersz po wierszu. Do tego okno pozwalało na **jeden ruch
naraz** (blokada „poprzedni ruch jeszcze trwa” do 10 s) i wysyłało komendy
**nie częściej niż co 0,2 s**, bo silnikowy limit (`ENABLE_ANTI_CMD_FLOOD`)
wyrzucał bez słowa szóstą komendę w pół sekundy. Dziesięć przedmiotów to
były sekundy czekania.

## Jak jest tu

- Okno dostaje **cały magazyn raz**, przy otwarciu (`COLL begin/e/end`), i
  samo układa strony, filtruje kategorie i szuka – zmiana kategorii, strony
  czy wpisanie litery nie pyta serwera o nic.
- Ruch to **jedna krótka komenda wysłana od razu** (bez kolejki i przerw),
  a okno **pokazuje skutek natychmiast** (nakładka na to, co serwer ostatnio
  powiedział). Serwer odpowiada **małą zmianą**: `COLL set <wpis>` albo
  `COLL del <id>` dla dotkniętego wpisu i `COLL res <op> <kod> <sztuki>`;
  odmowa sama cofa obraz. Żadnego odświeżania całości po ruchu.
- `/kolekcjoner` jest **poza silnikowym limitem komend** (`cmd.cpp`), ma
  własny, hojny limit (60 ruchów na sekundę), więc seria kliknięć nie ginie.
- „Schowaj wszystkie takie” (Ctrl + PPM) to **jedna komenda na całą partię**.
- **Zero czytania z bazy po otwarciu**; zapisy idą w kolejce rdzenia bazy,
  serwer nie czeka na nie z odpowiedzią.

## Zapis i bezpieczeństwo przedmiotów

- Wpis magazynu **to wiersz samego przedmiotu w `player.item`**: `window =
  'SAFEBOX'`, `owner_id = 2000000000 + id konta`. Żaden id postaci ani konta
  nie jest tak duży, więc ani wczytanie postaci, ani zwykły magazyn
  (`owner_id = id konta`) nigdy tych wierszy nie czytają; schemat bazy się
  nie zmienia.
- Rdzeń bazy zapisuje wiersz okna SAFEBOX **od razu** (`QUERY_ITEM_SAVE`, bez
  pamięci podręcznej), a wiersz w ekwipunku po wyjęciu jest zapisywany
  natychmiast (`HEADER_GD_ITEM_FLUSH`, jak przy wyjmowaniu ze zwykłego
  magazynu).
- Ruch całego stosu **zmienia jeden wiersz** (ten sam id przedmiotu) – nie ma
  chwili, w której istnieją dwie kopie, cokolwiek i kiedykolwiek przerwie
  serwer. Dzielenie i łączenie stosów zapisuje najpierw stronę przybywającą,
  potem ubywającą (w najgorszym razie podwojone sztuki, nigdy zgubione).
- Każdy ruch jest sprawdzany na serwerze (sesja tego połączenia, odległość,
  ręce, flagi, pojemność); wpis, którego id żyje już jako przedmiot (wiersz
  przeczytany przed zapisem wyjęcia na innym rdzeniu), znika z obrazu i
  nigdy nie trafia do ekwipunku drugi raz.
- Magazyn jest czytany od nowa przy każdym otwarciu, więc zmiany z innego
  rdzenia (teleport, zmiana kanału) zawsze są widoczne.
- Boty: komenda wymaga prawdziwego połączenia w fazie gry – boty jej nie
  wysyłają i nie mają tego magazynu.
- Tabela `player.collector_storage` (konto → poziom rozbudowy) –
  `linux-port/docker/mariadb/playerbot/apply.sh`, idempotentnie. Bez niej
  magazyn działa z 500 wpisami, a „Rozbuduj” odmawia (pieniądze nie są
  pobierane).

## Protokół

Klient → serwer: `/kolekcjoner open | close | put <op> <pole> <ilość> |
putall <op> <pole> [keep=<hex>] | take <op> <id> <ilość> <pole> | expand <op>`
(ilość 0 = cały stos / jeden stos, pole -1 = dowolne).

Serwer → klient (`COLL ...`): `begin <poziom> <pojemność> <wpisy> <rozbudowa
dostępna>`, `e <wpis> ...`, `end <wpisy>`, `set <wpis>`, `del <id>`,
`res <op> <kod> <sztuki>`, `tier <poziom> <pojemność>`, `close <powód>`,
`err <kod>`; wpis = `id,vnum,ilość,s0,s1,s2[,typ:wartość;...×7]`. Kody:
`playerbot_collector.h`.

## Klient

`uicollector.py` (nowy), `uiinventory.py` (PPM i upuszczanie do ekwipunku),
`uisafebox.py` (przycisk „Kolekcjoner”), `game.py` (`COLL`). Grafiki w paczce
`root` pod `mt2009_ui/collector/` (ikony kategorii, przyciski kategorii,
pole, lupa, pasek, nagłówek, pole wyszukiwania); każda brakująca grafika ma
zastępstwo z paczek klienta albo jest pomijana – okno nigdy nie wywraca się
na braku pliku. Bez zmian w `metin2client.exe`.

## Przedmiot „Kolekcjoner” (MT2009_PLUS_COLLECTOR_ITEM_V1)

- **70115 „Kolekcjoner”** – w ItemShopie (strona „Wyposażenie”, indeks 16,
  1000 SM, bez progu poziomu; `apply.sh`, `ishop_once collector_item_16`,
  edytowalny w edytorze bazy danych). `ITEM_QUEST`, **nie zużywa się**,
  stos 1, antyflagi 106880 (bez wyrzucania, sprzedaży, handlu, sklepu
  prywatnego/offline, łączenia) – zostaje u kupującego; magazyn konta może
  go przenieść między postaciami.
- Użycie (`game/quest/kolekcjoner_item.quest`) wysyła `/kolekcjoner
  przedmiot`: serwer sprawdza, czy przedmiot jest w ekwipunku i postać żyje,
  i otwiera magazyn kolekcjonera **tam, gdzie stoi postać** – bez
  magazyniera i bez otwartego zwykłego magazynu (czyli też bez jego hasła).
  Reszta zasad jak u magazyniera: ruchy z wolnymi rękami, zamknięcie po
  odejściu 15 m od miejsca otwarcia. Okno otwiera się samo na pierwszy
  wiersz `COLL begin` (jak przy przycisku w oknie magazynu).
- Boty go nie kupują (`playerbot_itemshop.h` pomija jego wiersze w katalogu
  botów) i nie otwierają magazynu (`RealPlayer`).
- Klient: rekord `item_proto`, wiersz `item_list.txt` (ikona Biletu Do
  Magazynu, `icon/item/70010.tga`) i `itemdesc.txt` –
  `client-patches/client-2.0.30/tools/collectoritem/patch_collector_item_client.py`;
  w `uicollector.py` komunikat dla braku przedmiotu (`COLL err 6`).
