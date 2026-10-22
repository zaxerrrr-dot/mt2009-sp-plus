# seonpyeong – przepisy Seon-Pyeonga (przeciąganie +9 → następny przedmiot)

`MT2009_PLUS_SEONPYEONG_ELITE_V1` (właściciel, 22.10.2026; paczka p-gf-po-3.0.1, pkt 2 – „jak na wiki, co z czym
i u kogo”). Seon-Pyeong (20091, `BLACKSMITH2_MOB`) przyjmuje tylko przedmioty z „elitarnym” przepisem
(`IsEliteRefine`): broń / zbroję / buty +9 przeciągnięte na niego zamienia w następny przedmiot (100%, kamienie
i bonusy zostają). Zwykły Kowal i zwoje ulepszeń takich przepisów nie przyjmują.

Od `MT2009_PLUS_REFINE_GLOBAL_V1` (arkusz właściciela) te przejścia miały numery nadawane po kolei przez
`tools/refineglobal/gen_refineglobal.py` (40027 / 40232 / 40037 / 40095) – nie elitarne, więc robił je zwykły Kowal,
a Seon-Pyeong nic nie przyjmował. Teraz generator daje im STAŁE numery 39900–39903 (lista `ELITE` w generatorze:
które przejścia arkusza są Seon-Pyeonga, plus dwa spoza arkusza – Partyzana+9 → Pogromca Nieb. Smoka i zbroje
105 +9 → cyjanitowe), więc ponowne wczytanie arkusza ich nie przesunie:

| id | przejście |
|----|-----------|
| 39900 | broń 65/66 +9 → 80 (2× Zwój Błogosławieństwa, Broszura Szermierki, 100 000) + Partyzana+9 → Pogromca |
| 39901 | zbroje 66 +9 i buty 47–59 +9 → 80 (3× Smocza Łuska, 4× Smoczy Szpon, 200 000) |
| 39902 | broń 80 +9 → 87–105 (3× Broszura, 100× Odłamek Energii, 2× Zwój, 5 000 000) |
| 39903 | broń 87–105 +9 i zbroje 105–115 +9 → cyjanitowe (3× Księga Prawdy, 2× Zwój, 2× Dusza Prawdy, 2 000 000) |

Silnik (ta łatka, cztery edycje z własnymi znacznikami):

- `constants.cpp` – `IsEliteRefine`: 501, 530 (z paczki) i zakres 39900–39999 (trzymać w zgodzie z `ELITE`);
- `char_item.cpp` – `CanReceiveItem`: kowale budynków gildii (20044–20046) i Wieży Demonów (20074–20076) nie
  przyjmują przepisów Seon-Pyeonga (wcześniej przyjmowali).

Reszta: `quest/seon_pyeong.quest` (rozmowa – co na niego przeciągnąć; okna wytwarzania już nie ma),
`cube.buty.txt` bez 4 receptur Seon-Pyeonga (buty idą przeciągnięciem), `cube.seon_pyeong.txt` usunięty.

Linux/VPS: `python3 apply_seonpyeong.py <game/src>`; Windows: `Apply-SeonPyeongPatch.ps1 -SourceDir <game/src>`
(wołane przez `tools/port/Apply-MT2009PlusEngine.ps1`, na końcu).

`MT2009_PLUS_SEONPYEONG_FIX_V1` (właściciel, 22.10.2026: „po OK nic się nie dzieje”): jak na globalu przedmiot idzie
przez okno ulepszania (to samo, co po przeciągnięciu na niego). Rozmowa nie jest już ślepym zaułkiem: „Przekuj
przedmiot +9” pokazuje przedmioty z plecaka z jego przepisem i otwiera dla wybranego okno ulepszania; „Przepisy” –
lista. Silnik (`questlua_pc.cpp`, trzy edycje): `pc.seonpyeong_cells()` (komórki plecaka z przepisem elitarnym) i
`pc.seonpyeong_refine(komórka)` (tylko przy Seon-Pyeongu, w zasięgu – `CanReceiveItem`; `SetRefineNPC` +
`RefineInformation(REFINE_TYPE_NORMAL)`, dalej zwykłe `CInputMain::Refine`). Obie funkcje są na liście
`quest_functions` w Dockerfile.
