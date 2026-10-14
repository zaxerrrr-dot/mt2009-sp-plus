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
14.10.2026 – pet tylko w ItemShopie). Okno wytwarzania klienta nie pokazuje
Gaya (exe bez zmian) – koszt podają rozmowy z NPC.

Pięć edycji, każda ze swoim znacznikiem. Po `ysets` (edycja „cube set” stoi w jego funkcji `Mt2009YSetsCubeMake`).

Linux/VPS: `python3 apply_gaya.py <game/src>`; Windows: `Apply-GayaPatch.ps1 -SourceDir <game/src>` (wołane przez
`tools/port/Apply-MT2009PlusEngine.ps1`). Pliki silnika: `cube.h`, `cube.cpp`.
