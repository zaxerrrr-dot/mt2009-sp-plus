# gmpanelbonus – bonusy 6/7 (i każdy inny) z panelu GM (F9)

Znacznik: `MT2009_PLUS_GMPANEL_POINT_BONUS_V1` (zgłoszenie #25, 8.11.2026: „z panelu gm nie można tych dziwnych bonusów
dodawać, tylko podstawowe 1-5 … atak magiczny z dodania od gm pisze nierozpoznane”).

## Przyczyna

Zakładka „Utwórz przedmiot” panelu GM (`root/interfacemodule.py`) wysyłała klasyczne numery `APPLY_*` (1–91), a
`do_gmpanel_createitem` (`cmd_gm.cpp`, `GMPanelClassicApplyToPoint`) zamieniał je na `POINT_*` – typ bonusu w tym
silniku. Tabela nie znała żadnego bonusu 6/7 (punkty 193–318), a „Wartość ataku magicznego” (55), „Magiczną wartość
obrony” (56) i „Obronę” (83) zamieniała na punkty postaci `POINT_MAGIC_ATT_GRADE` 22 / `MAGIC_DEF_GRADE` 23 /
`DEF_GRADE` 16 zamiast punktów przedmiotu `*_GRADE_BONUS` (97 / 98 / 96) – dymek nie ma dla nich nazwy
(„UNKNOWN_TYPE[22]”).

## Zmiana (4 edycje `cmd_gm.cpp`, `edits.json`)

| tag | co |
|---|---|
| `point` | liczba ≥ 1000 to `POINT_*` + 1000 (nowy panel) – brana wprost, jeśli `0 < punkt < POINT_MAX_NUM`; funkcja zwraca `WORD` (punkty do 318, `wideattr`) |
| `grade`, `def grade` | klasyczne 55 / 56 / 83 → `POINT_MAGIC_ATT_GRADE_BONUS` / `MAGIC_DEF_GRADE_BONUS` / `DEF_GRADE_BONUS` (starszy klient) |
| `type` | wywołanie trzyma typ jako `WORD` |

Kolejność: dowolna (kotwice to kod panelu GM silnika). Linux/VPS: `python3 apply_gmpanelbonus.py <game/src>`; Windows:
`Apply-GmPanelBonusPatch.ps1` (`tools/port/Apply-MT2009PlusEngine.ps1`, na końcu). `gen_edits.py [<game/src>]` pisze
`edits.json` i sprawdza kotwice. Wdrożenie Yohary: dopisać `gmpanelbonus` na końcu listy łatek `yohara-deploy.sh`.

## Klient i panele

- `root/interfacemodule.py` (`GMPanelPointItems`): lista bonusów to punkty – najpierw bonusy 1–5 (`world.item_attr`),
  potem „[6/7]” (pula `world.item_attr_rare`: Seon-Hae, 71051, 71052), potem „[inne]” (każdy punkt, który dymek umie
  nazwać); nazwy z dymka (`localeinfo_point`), wartość jako „x”; wysyłane jako 1000 + punkt. Bonus 6/7 wpisuje się w
  pola „Bonus 6” i „Bonus 7”. Stary serwer pomija takie liczby (jak dotąd nieznane).
- `root/localeinfo_point.py`: punkty 16 / 22 / 23 dostają nazwy – przedmioty zrobione wcześniej panelem pokazują linię.
- Panel Sebana (`app.py`, `apply_text`) i panel (`admin_panel.py`, `apply_key` / `APPLY_TEXTS`): punkty bez klasycznego
  `APPLY` (bonusy 6/7, Sung Ma, żywioły) i punkty, które wpadały na obcą klasyczną nazwę (49 „Silny przeciwko
  Insektom” czytany jako „Odporność na spowolnienie”, 80 „Odbicie strzał”) dostają klucz 2000 + punkt z nazwą klienta.
